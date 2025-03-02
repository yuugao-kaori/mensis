import schedule
import time
import argparse
from datetime import datetime
from custom_logging import setup_logger
from postgres import check_postgres_connection as check_pg_conn, manual_backup_postgres as manual_backup_pg, pgroonga_reindex as pgroonga_kensaku_reindex, auto_backup_postgres, pg_repack_all_db as pg_repack_db
from load_env import load_env
from notice import sendDM_misskey_notification

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
        sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築が完了しました。処理時間: {time_str}")
        logger.info(f"テーブルの再構築完了 - 処理時間: {time_str}")
    else:
        sendDM_misskey_notification(f"PostgreSQLのテーブルの再構築に失敗しました。処理時間: {time_str}")
        logger.error(f"テーブルの再構築失敗 - 処理時間: {time_str}")


def pgroonga_reindex():
    logger = setup_logger(name='pgroonga_reindex')
    connection_info = load_env()
    pgroonga_kensaku_reindex(connection_info, logger)

def manual_backup_postgres():
    logger = setup_logger(name='manual_backup_postgres')
    connection_info = load_env()
    manual_backup_pg(connection_info, logger)


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
    'pg_repack_all_db': pg_repack_all_db

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
    schedule.every().day.at("03:00").do(test)
    schedule.every().day.at("05:00").do(auto_backup_postgres)
    schedule.every().day.at("06:00").do(pgroonga_reindex)
    schedule.every().day.at("07:00").do(pg_repack_all_db)


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
