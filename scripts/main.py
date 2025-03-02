import schedule
import time
import argparse
from datetime import datetime
from custom_logging import setup_logger
from postgres import check_postgres_connection as check_pg_conn, manual_backup_postgres as manual_backup_pg, pgroonga_reindex as pgroonga_kensaku_reindex, auto_backup_postgres as auto_backup_pg, pg_repack_all_db as pg_repack_db
from load_env import load_env
from notice import sendDM_misskey_notification
from system_check import get_disk_usage, format_bytes

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
    logger = setup_logger(name='pg_repack_all_db')
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
        logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
    else:
        sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築に失敗しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
        logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")


def pgroonga_reindex():
    logger = setup_logger(name='pgroonga_reindex')
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
        logger.info(f"PGroongaインデックスの再構築完了 - 処理時間: {time_str}")
    else:
        sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築に失敗しました。\n\n現在時間：{current_time}\n処理時間: {time_str}")
        logger.error(f"PGroongaインデックスの再構築に失敗 - 処理時間: {time_str}")

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
    connection_info = load_env()
    
    disk = get_disk_usage()
    if disk['percent'] > 90:
        sendDM_misskey_notification(f"ディスク使用率が{disk['percent']}％です。\nバックアップは行われません。")
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
        logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
    else:
        sendDM_misskey_notification(f"Postgresの自動バックアップに失敗しました。\n\nモード：{backup_type}\n現在時間：{current_time}\n処理時間: {time_str}\nディスク使用率: {disk['percent']}%\n空き容量: {format_bytes(disk['free'])}")
        logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")



def check_postgres_connection():
    logger = setup_logger(name='check_postgres_connection')
    connection_info = load_env()
    check_pg_conn(connection_info, logger)

def morning_print():
    print(f"Morning print at {datetime.now()}")

def test():
    print(f"test ok at {datetime.now()}")
    # バックアップ処理をここに実装

# 利用可能なタスクの辞書
TASKS = {
    'morning_print': morning_print,
    'test': test,  # ここにカンマを追加
    'check_postgres_connection': check_postgres_connection,
    'manual_backup_postgres': manual_backup_postgres,
    'pgroonga_reindex': pgroonga_reindex,
    'pg_repack_all_db': pg_repack_all_db,
    'system_check': system_check

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
    schedule.every().day.at("02:00").do(pg_repack_all_db)
    schedule.every().day.at("03:00").do(auto_backup_postgres, backup_type="daily")
    schedule.every().day.at("04:00").do(pgroonga_reindex)
    schedule.every().day.at("05:00").do(auto_backup_postgres, backup_type="weekly") if datetime.now().weekday() == 6 else None
    schedule.every().day.at("06:00").do(lambda: auto_backup_postgres(backup_type="monthly") if datetime.now().day == 1 else None)


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
