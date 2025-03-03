import schedule
import time
import argparse
import dotenv
from datetime import datetime, timedelta
from custom_logging import setup_logger
from postgres import check_postgres_connection as check_pg_conn, manual_backup_postgres as manual_backup_pg, pgroonga_reindex as pgroonga_kensaku_reindex, auto_backup_postgres as auto_backup_pg, pg_repack_all_db as pg_repack_db
from load_env import load_env
from notice import sendDM_misskey_notification, post_misskey_notification
from system_check import get_disk_usage, format_bytes
import os

TASK_RESULTS = {
    'pg_repack_all_db': {'last_run': None, 'success': None, 'details': None},
    'auto_backup_daily': {'last_run': None, 'success': None, 'details': None},
    'auto_backup_weekly': {'last_run': None, 'success': None, 'details': None},
    'auto_backup_monthly': {'last_run': None, 'success': None, 'details': None},
    'pgroonga_reindex': {'last_run': None, 'success': None, 'details': None}
}


# タスク結果を記録する関数
def record_task_result(task_name, success, details=None):
    """タスクの実行結果を記録する"""
    if task_name in TASK_RESULTS:
        TASK_RESULTS[task_name]['last_run'] = datetime.now()
        TASK_RESULTS[task_name]['success'] = success
        TASK_RESULTS[task_name]['details'] = details

def system_check():
    logger = setup_logger(name='system_check')
    disk = get_disk_usage()
    system_check_msg = f"ディスク使用状況:\n合計容量: {format_bytes(disk['total'])}\n使用済み: {format_bytes(disk['used'])}\n空き容量: {format_bytes(disk['free'])}\n使用率: {disk['percent']}%"
    logger.info(system_check_msg)

    if disk['percent'] > 80:
        sendDM_misskey_notification(f"######################\n\nディスク使用率が90%を超えています。\n\n######################\n{system_check_msg}")
        logger.warning(f"ディスク使用率が80%を超えています。")
    else:
        sendDM_misskey_notification(system_check_msg)
        logger.info(f"ディスク使用率が80%未満です。")

def pg_repack_all_db():
    dotenv.load_dotenv()
    logger = setup_logger(name='pg_repack_all_db')
    task_name = 'pg_repack_all_db'

    PG_REPACK = os.environ.get('PG_REPACK')
    
    PG_REPACK_FREQUENCY = os.environ.get('PG_REPACK_FREQUENCY')

    if not PG_REPACK_FREQUENCY or PG_REPACK_FREQUENCY == "everyday":
        logger.warning("PG_REPACK_FREQUENCY environment variable is not set, using default configuration")
        PG_REPACK_FREQUENCY = "daily"  # デフォルト値を設定
    # Check if repack should run based on frequency setting
    if PG_REPACK_FREQUENCY == "everyweek":
        # Only run on Sunday (weekday 6)
        if datetime.now().weekday() != 6:
            logger.info("PG_REPACK_FREQUENCY is set to everyweek, but today is not Sunday. Skipping.")
            ## 意図した挙動である（失敗ではない）ため、record_task_resultは呼び出さない
            return False
    if PG_REPACK_FREQUENCY == "everymonth":
        # Only run on the 1st day of the month
        if datetime.now().day != 1:
            logger.info("PG_REPACK_FREQUENCY is set to everymonth, but today is not the first day of the month. Skipping.")
            ## 意図した挙動である（失敗ではない）ため、record_task_resultは呼び出さない
            return False
    if not PG_REPACK:
        logger.error("PG_REPACK environment variable is not set")
        sendDM_misskey_notification("環境変数PG_REPACKが設定されていません。")
        record_task_result(task_name, False, "環境変数PG_REPACKが設定されていません。")
        return False
    elif PG_REPACK == "True":
        system_check() # メンテナンス前にディスク使用量をログに残しておく

        connection_info = load_env()
        
        start_time = time.time()  # 開始時間を記録
        
        response = pg_repack_db(connection_info, logger)
        
        end_time = time.time()  # 終了時間を記録
        elapsed_time = end_time - start_time  # 経過時間を計算
        
        # 時間を見やすいフォーマットに変換（時:分:秒）
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        # 現在の時間を取得してフォーマット
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response:
            sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築が完了しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
            record_task_result(task_name, True, f"処理時間: {time_str}")
            logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
        else:
            sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築に失敗しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
            record_task_result(task_name, False, f"処理時間: {time_str}")
            logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")
    else:
        logger.info("PG_REPACK is set to false. Skipping pg_repack_all_db")
        record_task_result(task_name, False, "PG_REPACKがFalseのため実行しない")
        return False


def pgroonga_reindex():
    logger = setup_logger(name='pgroonga_reindex')
    task_name = 'pgroonga_reindex'

    PG_PGROONGA_REINDEX = os.environ.get('PG_PGROONGA_REINDEX')
    PG_PGROONGA_REINDEX_FREQUENCY = os.environ.get('PG_PGROONGA_REINDEX_FREQUENCY')

    # Check if repack should run based on frequency setting
    if PG_PGROONGA_REINDEX_FREQUENCY == "everyweek":
        # Only run on Sunday (weekday 6)
        if datetime.now().weekday() != 6:
            logger.info("PG_PGROONGA_REINDEX_FREQUENCY is set to everyweek, but today is not Sunday. Skipping.")
            ## 意図した挙動である（失敗ではない）ため、record_task_resultは呼び出さない
            return False
    if PG_PGROONGA_REINDEX_FREQUENCY == "everymonth":
        # Only run on the 1st day of the month
        if datetime.now().day != 1:
            logger.info("PG_PGROONGA_REINDEX_FREQUENCY is set to everymonth, but today is not the first day of the month. Skipping.")
            ## 意図した挙動である（失敗ではない）ため、record_task_resultは呼び出さない
            return False

    if not PG_PGROONGA_REINDEX:
        logger.error("PG_PGROONGA_REINDEX environment variable is not set")
        sendDM_misskey_notification("環境変数PG_PGROONGA_REINDEXが設定されていません。")
        record_task_result(task_name, False, f"環境変数PG_PGROONGA_REINDEXが設定されていません。")

        return False

    elif PG_PGROONGA_REINDEX == "True":
        connection_info = load_env()
        
        start_time = time.time()  # 開始時間を記録
        
        response = pgroonga_kensaku_reindex(connection_info, logger)
        
        end_time = time.time()  # 終了時間を記録
        elapsed_time = end_time - start_time  # 経過時間を計算
        
        # 時間を見やすいフォーマットに変換（時:分:秒）
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        # 現在の時間を取得してフォーマット
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response:
            sendDM_misskey_notification(f"PGroongaのインデックス再構築が完了しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
            record_task_result(task_name, True, f"処理時間: {time_str}")
            logger.info(f"PGroongaインデックスの再構築完了 - 処理時間: {time_str}")
        else:
            sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築に失敗しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
            record_task_result(task_name, False, f"処理時間: {time_str}")

            logger.error(f"PGroongaインデックスの再構築に失敗 - 処理時間: {time_str}")
    
    else:
        logger.info("PG_PGROONGA_REINDEX is set to false. Skipping pgroonga_reindex")
        record_task_result(task_name, False, f"PG_PGROONGA_REINDEXがFalseのため実行しない")
        return False

def manual_backup_postgres():
    logger = setup_logger(name='manual_backup_postgres')
    connection_info = load_env()
    
    start_time = time.time()  # 開始時間を記録
    
    response,backup_size = manual_backup_pg(connection_info, logger)

    end_time = time.time()  # 終了時間を記録
    elapsed_time = end_time - start_time  # 経過時間を計算
    
    # 時間を見やすいフォーマットに変換（時:分:秒）
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    disk = get_disk_usage()
    system_check_msg = f"ディスク使用状況:\n合計容量: {format_bytes(disk['total'])}\n使用済み: {format_bytes(disk['used'])}\n空き容量: {format_bytes(disk['free'])}\n使用率: {disk['percent']}%"

    # 現在の時間を取得してフォーマット
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if response:

        backup_size_formatted = format_bytes(backup_size) if backup_size else "不明"


        sendDM_misskey_notification(f"Postgresの手動バックアップが完了しました。\n\n現在時間：{current_time}\n処理時間: {time_str}\n出力サイズ：{backup_size_formatted}\nディスク使用率: {disk['percent']}%\n空き容量: {format_bytes(disk['free'])}")
        logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
    else:
        sendDM_misskey_notification(f"Postgresの手動バックアップに失敗しました。\n\n現在時間：{current_time}\n処理時間: {time_str}\nディスク使用率: {disk['percent']}%\n空き容量: {format_bytes(disk['free'])}")
        logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")

def auto_backup_postgres(backup_type="daily"):

    logger = setup_logger(name='auto_backup_postgres')

    backup_type_upperd = backup_type.upper()



    GET_ENV = f'PG_BACKUP_{backup_type_upperd}'
    GET_ENV_FREQUENCY = f'PG_BACKUP_{backup_type_upperd}_FREQUENCY'
    PG_BACKUP_TYPE = os.environ.get(GET_ENV)


    if not PG_BACKUP_TYPE:
        logger.error(f"{GET_ENV} environment variable is not set")
        sendDM_misskey_notification(f"環境変数{GET_ENV}が設定されていません。")
        record_task_result(task_name, False, f"環境変数{GET_ENV}が設定されていません")
        return False
    elif PG_BACKUP_TYPE == "True":

        if backup_type == "daily" and GET_ENV_FREQUENCY == "every_second":
            # Only run on Sunday (weekday 6)
            if datetime.now().day % 2 == 0:  # day % 2 == 0 is even days, so skip them
                logger.info(f"{GET_ENV_FREQUENCY} is set to every_second, but today is not an odd day. Skipping.")
                ## 意図した挙動である（失敗ではない）ため、record_task_resultは呼び出さない
                return False
        if backup_type == "weekly" and os.environ.get(GET_ENV_FREQUENCY) == "every_second":
            # Get the week number in the year (1-53)
            current_week = datetime.now().isocalendar()[1]
            if current_week % 2 == 0:  # Even weeks
                logger.info(f"{GET_ENV_FREQUENCY} is set to every_second, but this is an even week. Skipping.")
                # Not a failure, just intentionally skipping
                return False
        if backup_type == "monthly" and os.environ.get(GET_ENV_FREQUENCY) == "every_second":
            # Only run on the 1st day of the month
            current_month = datetime.now().month
            if current_month % 2 == 0:  # Even months (February, April, etc.)
                logger.info(f"{GET_ENV_FREQUENCY} is set to every_second, but today is not an odd day. Skipping.")
                # Not a failure, just intentionally skipping
                return False

        connection_info = load_env()
        
        disk = get_disk_usage()
        if disk['percent'] > 90:
            sendDM_misskey_notification(f"ディスク使用率が{disk['percent']}％です。\nバックアップは行われません。")
            record_task_result(task_name, False, f"ディスク使用率が{disk['percent']}％のためバックアップ中止")
            logger.warning(f"ディスク使用率が90％を超過しているため、バックアップは実行されなかった")
            return

        start_time = time.time()  # 開始時間を記録
        
        response, backup_size  = auto_backup_pg(connection_info, logger, backup_type)

        end_time = time.time()  # 終了時間を記録
        elapsed_time = end_time - start_time  # 経過時間を計算
        
        # 時間を見やすいフォーマットに変換（時:分:秒）
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

        disk = get_disk_usage()
        system_check_msg = f"ディスク使用状況:\n合計容量: {format_bytes(disk['total'])}\n使用済み: {format_bytes(disk['used'])}\n空き容量: {format_bytes(disk['free'])}\n使用率: {disk['percent']}%"

        # 現在の時間を取得してフォーマット
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if response:

            backup_size_formatted = format_bytes(backup_size) if backup_size else "不明"

            sendDM_misskey_notification(f"Postgresの自動バックアップが完了しました。\n\nモード：{backup_type}\n現在時間：{current_time}\n処理時間: {time_str}\n出力サイズ：{backup_size_formatted}\nディスク使用率: {disk['percent']}%\n空き容量: {format_bytes(disk['free'])}")
            record_task_result(task_name, True, f"処理時間: {time_str}, サイズ: {backup_size_formatted}")
            logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
        else:
            sendDM_misskey_notification(f"Postgresの自動バックアップに失敗しました。\n\nモード：{backup_type}\n現在時間：{current_time}\n処理時間: {time_str}\nディスク使用率: {disk['percent']}%\n空き容量: {format_bytes(disk['free'])}")
            record_task_result(task_name, False, f"処理時間: {time_str}")
            logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")
    else:
        logger.info(f"{GET_ENV} is set to false. Skipping auto_backup_postgres")
        record_task_result(task_name, False, f"{GET_ENV}がFalseのため実行しない")
        return False

def daily_maintenance_report():
    """毎朝のメンテナンス結果レポートを生成して通知する"""
    logger = setup_logger(name='daily_maintenance_report')

    MAINTENANCE_REPORT = os.environ.get('MAINTENANCE_REPORT')
    if not MAINTENANCE_REPORT:
        logger.error("MAINTENANCE_REPORT environment variable is not set")
        sendDM_misskey_notification("環境変数MAINTENANCE_REPORTが設定されていません。")
        return False
    elif MAINTENANCE_REPORT == "True":
        # 現在の時間を取得してフォーマット
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        
        # ディスク使用状況の確認
        disk = get_disk_usage()
        disk_status = f"ディスク使用状況:\n合計容量: {format_bytes(disk['total'])}\n使用済み: {format_bytes(disk['used'])}\n空き容量: {format_bytes(disk['free'])}\n使用率: {disk['percent']}%"
        
        # タスク実行結果のレポート
        task_status = ""
        
        # テーブル再構築
        repack_status = TASK_RESULTS['pg_repack_all_db']
        if repack_status['last_run'] and repack_status['last_run'].date() == (datetime.now() - timedelta(days=1)).date():
            result = "✅ 成功" if repack_status['success'] else "❌ 失敗"
            details = f" ({repack_status['details']})" if repack_status['details'] else ""
            task_status += f"- テーブル再構築: {result}{details}\n"
        else:
            task_status += f"- テーブル再構築: ⚠️ 実行なし\n"
        
        # 日次バックアップ
        daily_backup = TASK_RESULTS['auto_backup_daily']
        if daily_backup['last_run'] and daily_backup['last_run'].date() == (datetime.now() - timedelta(days=1)).date():
            result = "✅ 成功" if daily_backup['success'] else "❌ 失敗"
            details = f" ({daily_backup['details']})" if daily_backup['details'] else ""
            task_status += f"- 日次バックアップ: {result}{details}\n"
        else:
            task_status += f"- 日次バックアップ: ⚠️ 実行なし\n"
        
        # PGroongaインデックス再構築
        pgroonga_status = TASK_RESULTS['pgroonga_reindex']
        if pgroonga_status['last_run'] and pgroonga_status['last_run'].date() == (datetime.now() - timedelta(days=1)).date():
            result = "✅ 成功" if pgroonga_status['success'] else "❌ 失敗"
            details = f" ({pgroonga_status['details']})" if pgroonga_status['details'] else ""
            task_status += f"- PGroonga再構築: {result}{details}\n"
        else:
            task_status += f"- PGroonga再構築: ⚠️ 実行なし\n"
        
        # 週次バックアップ（日曜日のみ）
        if (datetime.now() - timedelta(days=1)).weekday() == 6:
            weekly_backup = TASK_RESULTS['auto_backup_weekly']
            if weekly_backup['last_run'] and weekly_backup['last_run'].date() == (datetime.now() - timedelta(days=1)).date():
                result = "✅ 成功" if weekly_backup['success'] else "❌ 失敗"
                details = f" ({weekly_backup['details']})" if weekly_backup['details'] else ""
                task_status += f"- 週次バックアップ: {result}{details}\n"
            else:
                task_status += f"- 週次バックアップ: ⚠️ 実行なし\n"
        
        # 月次バックアップ（1日のみ）
        if (datetime.now() - timedelta(days=1)).day == 1:
            monthly_backup = TASK_RESULTS['auto_backup_monthly']
            if monthly_backup['last_run'] and monthly_backup['last_run'].date() == (datetime.now() - timedelta(days=1)).date():
                result = "✅ 成功" if monthly_backup['success'] else "❌ 失敗"
                details = f" ({monthly_backup['details']})" if monthly_backup['details'] else ""
                task_status += f"- 月次バックアップ: {result}{details}\n"
            else:
                task_status += f"- 月次バックアップ: ⚠️ 実行なし\n"
        
        # レポートメッセージの作成
        report_message = f"""
メンテナンス実行レポート ({yesterday})

## タスク実行結果
{task_status}
## システム状況
{disk_status}
## 現在時間
{current_time}

報告者：【Mensis】 ｰ 星海天測団Misskey支部 メンテナンスシステム
    """
        
        # ログに記録して通知
        logger.info(f"日次メンテナンスレポートを生成しました")
        post_misskey_notification(report_message)
        return True
    else:
        logger.info("MAINTENANCE_REPORT is set to false. Skipping daily_maintenance_report")
        return False

def check_postgres_connection():
    logger = setup_logger(name='check_postgres_connection')
    connection_info = load_env()
    check_pg_conn(connection_info, logger)

def morning_print():
    print(f"Morning print at {datetime.now()}")

def test():
    print(f"test ok at {datetime.now()}")
    # バックアップ処理をここに実装

def announcement_maintenance_start():
    MAINTENANCE_ANNOUNCEMENT = os.environ.get('MAINTENANCE_ANNOUNCEMENT')
    if not MAINTENANCE_ANNOUNCEMENT:
        logger.error("MAINTENANCE_ANNOUNCEMENT environment variable is not set")
        sendDM_misskey_notification("環境変数MAINTENANCE_ANNOUNCEMENTが設定されていません。")
        return False
    elif MAINTENANCE_ANNOUNCEMENT == "True":
        logger = setup_logger(name='announcement_maintenance_start')
        post_misskey_notification(f"まもなく、本日2時よりメンテナンス作業を開始します。\n作業中もサーバはご利用頂けますが、応答速度の低下などが生じる可能性があります。\nご了承の程、よろしくお願いいたします。")
        logger.info("メンテナンス作業開始のアナウンスを実行")
    else:
        logger.info("MAINTENANCE_ANNOUNCEMENT is set to false. Skipping announcement")
        return False

# 利用可能なタスクの辞書
TASKS = {
    'morning_print': morning_print,
    'test': test,  # ここにカンマを追加
    'check_postgres_connection': check_postgres_connection,
    'manual_backup_postgres': manual_backup_postgres,
    'pgroonga_reindex': pgroonga_reindex,
    'pg_repack_all_db': pg_repack_all_db,
    'system_check': system_check,
    'daily_maintenance_report': daily_maintenance_report,
    'announcement_maintenance_start': announcement_maintenance_start

}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', choices=TASKS.keys(), help='実行するタスクを指定')
    args = parser.parse_args()

    if args.run:
        # 指定されたタスクを即時実行
        TASKS[args.run]()
        return

    # スケジュール設定
    schedule.every().day.at("01:50").do(announcement_maintenance_start)
    schedule.every().day.at("02:00").do(pg_repack_all_db)
    schedule.every().day.at("03:00").do(auto_backup_postgres, backup_type="daily")
    schedule.every().day.at("04:00").do(pgroonga_reindex)
    schedule.every().day.at("05:00").do(auto_backup_postgres, backup_type="weekly") if datetime.now().weekday() == 6 else None
    schedule.every().day.at("06:00").do(lambda: auto_backup_postgres(backup_type="monthly") if datetime.now().day == 1 else None)
    # 毎朝8時にメンテナンスレポートを送信
    schedule.every().day.at("08:00").do(daily_maintenance_report)

    # スケジューラー起動をログに記録
    # 現在の時間を取得してフォーマット
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger = setup_logger(name='load_env')
    logger.info("Mensis 星海天測団Misskeyメンテナンスシステムが起動しました")
    sendDM_misskey_notification(f"Mensis 星海天測団Misskeyメンテナンスシステムが起動しました\n\n現在の日時:{current_time}")
    # スケジュール実行ループ
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
