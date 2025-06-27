from pathlib import Path  # このインポートが正しく機能しているか確認
import dotenv
import os

from custom_logging import setup_logger


def load_env():
    logger = setup_logger(name='load_env')
    
    # 複数の可能性のあるパスをチェック
    possible_paths = [
        Path('/scripts/.env'),              # Dockerコンテナのルート
        Path('/home/web/mensis/.env'),      # プロジェクトのルート
        Path(__file__).parent.parent / '.env'  # スクリプトからの相対パス
    ]
    
    env_path = None
    for path in possible_paths:
        if path.exists():
            env_path = path
            logger.info(f"Found .env file at: {env_path}")
            break
    
    if (env_path is None):
        error_msg = (
            "Could not find .env file. Searched in:\n" + 
            "\n".join(f"- {p}" for p in possible_paths)
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # .envファイルをロード
    dotenv.load_dotenv(env_path)
    
    # 必須の環境変数（PostgreSQL）
    required_postgres_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 
                             'POSTGRES_HOST', 'POSTGRES_PORT']
    
    # 環境変数の値を取得し、未設定のものがないかチェック
    config = {}
    missing_vars = []
    
    for var in required_postgres_vars:
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        config[var.lower().replace('postgres_', '')] = value
    
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # レプリカ設定（オプション）
    config.update({
        'replica_enabled': os.getenv('POSTGRES_REPLICA', 'false').lower() == 'true',
        'replica_user': os.getenv('POSTGRES_REPLICA_USER'),
        'replica_password': os.getenv('POSTGRES_REPLICA_PASSWORD'),
        'replica_db': os.getenv('POSTGRES_REPLICA_DB'),
        'replica_host': os.getenv('POSTGRES_REPLICA_HOST'),
        'replica_port': os.getenv('POSTGRES_REPLICA_PORT')
    })
    
    # MinIO設定を追加
    config.update({
        'minio_access_key': os.getenv('MINIO_ACCESS_KEY'),
        'minio_secret_key': os.getenv('MINIO_SECRET_KEY'),
        'minio_host': os.getenv('MINIO_HOST'),
        'minio_port': os.getenv('MINIO_PORT'),
        'minio_bucket': os.getenv('MINIO_BUCKET'),
        'minio_backup': os.getenv('MINIO_BACKUP', 'False').lower() == 'true',
        'minio_backup_frequency': os.getenv('MINIO_BACKUP_FREQUENCY', 'everyday'),
        'minio_backup_time': os.getenv('MINIO_BACKUP_TIME', '07:00'),
        'minio_backup_generation': os.getenv('MINIO_BACKUP_GENERATION', '12')
    })
    
    # バックアップディレクトリ設定
    config.update({
        'backup_dir': os.getenv('BACKUP_DIR', '/backup')
    })
    
    # その他のシステム設定
    config.update({
        'pg_repack': os.getenv('PG_REPACK', 'False').lower() == 'true',
        'pg_repack_frequency': os.getenv('PG_REPACK_FREQUENCY', 'everyday'),
        'pg_repack_time': os.getenv('PG_REPACK_TIME', '02:00'),
        'pg_pgroonga_reindex': os.getenv('PG_PGROONGA_REINDEX', 'False').lower() == 'true',
        'pg_pgroonga_reindex_frequency': os.getenv('PG_PGROONGA_REINDEX_FREQUENCY', 'everyday'),
        'pg_pgroonga_reindex_time': os.getenv('PG_PGROONGA_REINDEX_TIME', '03:00'),
        'pg_backup_daily': os.getenv('PG_BACKUP_DAILY', 'False').lower() == 'true',
        'pg_backup_daily_frequency': os.getenv('PG_BACKUP_DAILY_FREQUENCY', 'every'),
        'pg_backup_daily_time': os.getenv('PG_BACKUP_DAILY_TIME', '04:00'),
        'pg_backup_daily_generation': os.getenv('PG_BACKUP_DAILY_GENERATION', '7'),
        'pg_backup_weekly': os.getenv('PG_BACKUP_WEEKLY', 'False').lower() == 'true',
        'pg_backup_weekly_frequency': os.getenv('PG_BACKUP_WEEKLY_FREQUENCY', 'every'),
        'pg_backup_weekly_time': os.getenv('PG_BACKUP_WEEKLY_TIME', '05:00'),
        'pg_backup_weekly_generation': os.getenv('PG_BACKUP_WEEKLY_GENERATION', '4'),
        'pg_backup_monthly': os.getenv('PG_BACKUP_MONTHLY', 'False').lower() == 'true',
        'pg_backup_monthly_frequency': os.getenv('PG_BACKUP_MONTHLY_FREQUENCY', 'every'),
        'pg_backup_monthly_time': os.getenv('PG_BACKUP_MONTHLY_TIME', '06:00'),
        'pg_backup_monthly_generation': os.getenv('PG_BACKUP_MONTHLY_GENERATION', '12')
    })
    
    # Misskey設定
    config.update({
        'misskey_host': os.getenv('MISSKEY_HOST'),
        'misskey_notice_user_id': os.getenv('MISSKEY_NOTICE_USER_ID'),
        'misskey_notice_user_token': os.getenv('MISSKEY_NOTICE_USER_TOKEN'),
        'misskey_tearget_user_id': os.getenv('MISSKEY_TEARGET_USER_ID')
    })
    
    # Redis設定
    config.update({
        'redis_host': os.getenv('REDIS_HOST'),
        'redis_port': os.getenv('REDIS_PORT')
    })
    
    logger.info("Environment variables loaded successfully")
    return config