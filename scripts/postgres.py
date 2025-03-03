import os
import subprocess
import dotenv
import gzip
import shutil
from pathlib import Path
from datetime import datetime
from custom_logging import setup_logger  # logging.py から custom_logging.py に変更
from load_env import load_env

def check_postgres_connection(connection_info, logger):
    """
    PostgreSQLへの接続をチェックする
    """
    try:
        # psqlコマンドの構築
        cmd = [
            'psql',
            f'--host={connection_info["host"]}',
            f'--port={connection_info["port"]}',
            f'--username={connection_info["user"]}',
            f'--dbname={connection_info["db"]}',
            '--no-password',  # パスワードはPGPASSWORD環境変数で渡す
            '-c', 'SELECT 1'  # 簡単な接続テストクエリ
        ]

        # 環境変数にパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = connection_info['password']

        # psqlコマンドを実行
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"Successfully connected to PostgreSQL at {connection_info['host']}:{connection_info['port']}")
            return True
        else:
            logger.error(f"Failed to connect to PostgreSQL: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error checking PostgreSQL connection: {str(e)}")
        return False


def manual_backup_postgres(connection_info, logger):
    """
    PostgreSQLデータベースのバックアップを作成する
    pg_dumpallを使用して全データベースをバックアップし、gzipで圧縮する
    
    Args:
        connection_info (dict): PostgreSQL接続情報
        logger: ロガーインスタンス
        
    Returns:
        tuple: (成功したかどうかのブール値, 出力ファイルパスまたはエラーメッセージ)
    """
    try:
        # バックアップディレクトリの設定
        backup_dir = Path('/backup/postgres/manual/')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # バックアップファイル名の生成 (YYYYMMDD形式)
        current_date = datetime.now().strftime('%Y%m%d')
        backup_filename = f"pg_dump_{current_date}"
        sql_file = backup_dir / f"{backup_filename}.sql"
        gz_file = backup_dir / f"{backup_filename}.sql.gz"
        
        logger.info(f"Starting PostgreSQL backup to {sql_file}")
        
        # pg_dumpallコマンドの構築
        cmd = [
            'pg_dumpall',
            f'--host={connection_info["host"]}',
            f'--port={connection_info["port"]}',
            f'--username={connection_info["user"]}',
            '--clean',  # データベース再作成用のDROPコマンドを含める
            '--if-exists',  # DROP時にIF EXISTSを使用
            f'--file={sql_file}'
        ]
        
        # 環境変数にパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = connection_info['password']
        
        # pg_dumpallを実行
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Database backup failed: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg
        
        logger.info(f"Database dump completed successfully. Compressing the file...")
        
        # gzipで圧縮
        with open(sql_file, 'rb') as f_in:
            with gzip.open(gz_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 圧縮後、元のSQLファイルを削除
        os.remove(sql_file)
        logger.info(f"Compression complete. Backup saved to: {gz_file}")

        # 圧縮ファイルのサイズを取得
        file_size = gz_file.stat().st_size
        file_size_mb = round(file_size / (1024 * 1024), 2)
        logger.info(f"Compression complete. Backup saved to: {gz_file} (サイズ: {file_size_mb} MB)")
        
        
        return True, file_size
        
    except Exception as e:
        error_msg = f"Error during database backup: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def auto_backup_postgres(connection_info, logger, backup_type):
    """
    PostgreSQLデータベースの自動バックアップを作成する
    pg_dumpallを使用して全データベースをバックアップし、gzipで圧縮する
    古いバックアップは設定に応じて自動的に削除される
    
    Args:
        connection_info (dict): PostgreSQL接続情報
        logger: ロガーインスタンス
        backup_type (str): バックアップタイプ ('dairy', 'weekly', 'monthly')
        
    Returns:
        bool: バックアップが成功したかどうか
    """
    try:
        # バックアップタイプの検証
        if backup_type not in ['dairy', 'weekly', 'monthly']:
            logger.error(f"Invalid backup type: {backup_type}. Must be one of: dairy, weekly, monthly")
            return False
            
        # 各タイプごとの保持世代数を設定
        retention_config = {
            'dairy': 7,
            'weekly': 5,
            'monthly': 12
        }
        
        # バックアップディレクトリの設定
        backup_dir = Path(f'/backup/postgres/auto/{backup_type}/')
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # バックアップファイル名の生成
        current_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"pg_dump_{backup_type}_{current_date}"
        sql_file = backup_dir / f"{backup_filename}.sql"
        gz_file = backup_dir / f"{backup_filename}.sql.gz"
        
        logger.info(f"Starting PostgreSQL {backup_type} backup to {sql_file}")
        
        # pg_dumpallコマンドの構築
        cmd = [
            'pg_dumpall',
            f'--host={connection_info["host"]}',
            f'--port={connection_info["port"]}',
            f'--username={connection_info["user"]}',
            '--clean',  # データベース再作成用のDROPコマンドを含める
            '--if-exists',  # DROP時にIF EXISTSを使用
            f'--file={sql_file}'
        ]
        
        # 環境変数にパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = connection_info['password']
        
        # pg_dumpallを実行
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"Database backup failed: {result.stderr}"
            logger.error(error_msg)
            return False
        
        logger.info(f"Database dump completed successfully. Compressing the file...")
        
        # gzipで圧縮
        with open(sql_file, 'rb') as f_in:
            with gzip.open(gz_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 圧縮後、元のSQLファイルを削除
        os.remove(sql_file)
        logger.info(f"Compression complete. Backup saved to: {gz_file}")
        
        # 圧縮ファイルのサイズを取得
        file_size = gz_file.stat().st_size
        file_size_mb = round(file_size / (1024 * 1024), 2)
        logger.info(f"Compression complete. Backup saved to: {gz_file} (サイズ: {file_size_mb} MB)")
        

        # 古いバックアップを削除して世代管理を行う
        # 保持する世代数
        retention_count = retention_config[backup_type]
        
        # 対象ディレクトリのバックアップファイル一覧を取得し、古い順にソート
        backup_files = list(backup_dir.glob("*.sql.gz"))
        backup_files.sort(key=lambda x: x.stat().st_mtime)
        
        # 保持数を超える古いバックアップを削除
        if len(backup_files) > retention_count:
            files_to_delete = backup_files[:-retention_count]
            for file in files_to_delete:
                logger.info(f"Removing old backup: {file}")
                file.unlink()
                
            logger.info(f"Removed {len(files_to_delete)} old backup(s). Keeping {retention_count} most recent backups.")
        
        return True, file_size
        
    except Exception as e:
        error_msg = f"Error during {backup_type} database backup: {str(e)}"
        logger.error(error_msg)

        file_size = None
        return False, file_size

def pg_repack_all_db(connection_info, logger):
    """
    PostgreSQLデータベース内の全テーブルに対してpg_repackを実行し、物理的な再編成を行う
    
    Args:
        connection_info (dict): PostgreSQL接続情報
        logger: ロガーインスタンス
        
    Returns:
        bool: pg_repackが成功したかどうか
    """
    try:
        logger.info(f"Starting pg_repack for all tables in database: {connection_info['db']}")
        
        # pg_repackコマンドの構築
        cmd = [
            'pg_repack',
            f"--host={connection_info['host']}",
            f"--port={connection_info['port']}",
            f"--username={connection_info['user']}",
            f"--dbname={connection_info['db']}",
            '--jobs=2',           # 並列処理数
            '--wait-timeout=30000', # タイムアウト（秒）
            '-a'                  # 全テーブルを対象にする
        ]
        
        # 環境変数にパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = connection_info['password']
        
        # pg_repackを実行
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = f"pg_repack failed: {result.stderr}"
            logger.error(error_msg)
            return False
        
        logger.info("pg_repack completed successfully")
        logger.debug(f"pg_repack output: {result.stdout}")
        
        return True
        
    except Exception as e:
        error_msg = f"Error during pg_repack operation: {str(e)}"
        logger.error(error_msg)
        return False

def pgroonga_reindex(connection_info, logger):
    """
    CREATE INDEX idx_note_text_with_pgroonga ON note USING pgroonga (text);
    でインデックスを作成/再作成する。
    
    Args:
        connection_info (dict): PostgreSQL接続情報
        logger: ロガーインスタンス
        
    Returns:
        bool: インデックスの作成/再作成が成功したかどうか
    """
    try:
        logger.info("Starting PGroonga index creation/recreation process")
        
        # 環境変数にパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = connection_info['password']
        
        # 1. まず既存のPGroongaインデックスを確認
        check_cmd = [
            'psql',
            f'--host={connection_info["host"]}',
            f'--port={connection_info["port"]}',
            f'--username={connection_info["user"]}',
            f'--dbname={connection_info["db"]}',
            '--no-password',
            '--tuples-only',
            '-c', "SELECT indexname FROM pg_indexes WHERE indexname = 'idx_note_text_with_pgroonga'"
        ]
        
        logger.info("Checking for existing idx_note_text_with_pgroonga index...")
        check_result = subprocess.run(
            check_cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        if check_result.returncode != 0:
            error_msg = f"Failed to check existing PGroonga index: {check_result.stderr}"
            logger.error(error_msg)
            return False
        
        # 2. 既存のインデックスがあれば削除
        if check_result.stdout.strip():
            logger.info("Found existing idx_note_text_with_pgroonga index, dropping it first")
            drop_cmd = [
                'psql',
                f'--host={connection_info["host"]}',
                f'--port={connection_info["port"]}',
                f'--username={connection_info["user"]}',
                f'--dbname={connection_info["db"]}',
                '--no-password',
                '-c', "DROP INDEX IF EXISTS idx_note_text_with_pgroonga"
            ]
            
            drop_result = subprocess.run(
                drop_cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if drop_result.returncode != 0:
                error_msg = f"Failed to drop existing PGroonga index: {drop_result.stderr}"
                logger.error(error_msg)
                return False
                
            logger.info("Successfully dropped existing PGroonga index")
        
        # 3. インデックスを作成
        logger.info("Creating PGroonga index on note.text column...")
        create_cmd = [
            'psql',
            f'--host={connection_info["host"]}',
            f'--port={connection_info["port"]}',
            f'--username={connection_info["user"]}',
            f'--dbname={connection_info["db"]}',
            '--no-password',
            '-c', "CREATE INDEX idx_note_text_with_pgroonga ON note USING pgroonga (text)"
        ]
        
        try:
            create_result = subprocess.run(
                create_cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=7200  # 2時間のタイムアウト
            )
            
            if create_result.returncode != 0:
                error_msg = f"Failed to create PGroonga index: {create_result.stderr}"
                logger.error(error_msg)
                return False
                
            logger.info("Successfully created PGroonga index on note.text column")
            return True
                
        except subprocess.TimeoutExpired:
            logger.error("Timeout occurred while creating PGroonga index")
            return False
        
    except Exception as e:
        error_msg = f"Error during PGroonga index creation: {str(e)}"
        logger.error(error_msg)
        return False