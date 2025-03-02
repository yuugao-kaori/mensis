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
    
    # 必須の環境変数
    required_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 
                    'POSTGRES_HOST', 'POSTGRES_PORT']
    
    # 環境変数の値を取得し、未設定のものがないかチェック
    config = {}
    missing_vars = []
    
    for var in required_vars:
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
    
    logger.info("Environment variables loaded successfully")
    return config