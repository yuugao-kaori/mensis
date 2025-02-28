import schedule
import time
import argparse
from datetime import datetime
from custom_logging import setup_logger
from postgres import check_postgres_connection as check_pg_conn, load_env, manual_backup_postgres as manual_backup_pg


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
    schedule.every().day.at("03:00").do(morning_print)

    # スケジュール実行ループ
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
