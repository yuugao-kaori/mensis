
import os
import time
import datetime
import subprocess
import shutil
from pathlib import Path
from custom_logging import setup_logger
from system_check import get_disk_usage, format_bytes

def check_minio_connection(connection_info, logger):
    """
    MinIOへの接続をテストする
    
    Args:
        connection_info (dict): Minioの接続情報
        logger (logging.Logger): ロガーオブジェクト
        
    Returns:
        bool: 接続成功時はTrue、失敗時はFalse
    """
    try:
        # 環境変数を設定して、mc configコマンドを実行
        env = os.environ.copy()
        env["MC_HOST_mensis"] = f"http://{connection_info['MINIO_ACCESS_KEY']}:{connection_info['MINIO_SECRET_KEY']}@{connection_info['MINIO_HOST']}:{connection_info['MINIO_PORT']}"

        # mcコマンドが利用可能か確認
        try:
            result = subprocess.run(["mc", "--version"], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  env=env,
                                  check=True,
                                  text=True)
            logger.info(f"MinIO Client (mc)が利用可能です: {result.stdout.strip()}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"MinIO Client (mc)が利用できません。インストールしてください。エラー: {str(e)}")
            return False
            
        # mcコマンドでMinIOへの接続を確認
        result = subprocess.run(["mc", "ls", f"mensis/{connection_info['MINIO_BUCKET']}"], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE,
                              env=env,
                              check=True,
                              text=True)
        
        if result.returncode == 0:
            logger.info("MinIOへの接続に成功しました")
            return True
        else:
            logger.error(f"MinIOへの接続に失敗しました: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"MinIOへの接続テスト中にエラーが発生しました: {str(e)}")
        return False

def auto_backup_minio(connection_info, logger, backup_dir="/backup/minio"):
    """
    MinIOバケットの自動バックアップを実行する
    
    Args:
        connection_info (dict): Minioの接続情報
        logger (logging.Logger): ロガーオブジェクト
        backup_dir (str): バックアップの保存先ディレクトリ
        
    Returns:
        tuple: (成功したかどうかのbool, バックアップサイズ(bytes))
    """
    try:
        # バックアップを開始する前にディスク容量を確認
        disk = get_disk_usage()
        if disk['percent'] > 90:
            logger.error(f"ディスク使用率が{disk['percent']}%であるため、バックアップを中止します")
            return False, 0

        # mcコマンドが利用可能か確認
        try:
            subprocess.run(["mc", "--version"], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE,
                          check=True)
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"MinIO Client (mc)が利用できません。インストールしてください。エラー: {str(e)}")
            return False, 0
            
        # 現在の日時をフォーマット
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"minio_backup_{timestamp}")
        
        # バックアップディレクトリの作成
        os.makedirs(backup_path, exist_ok=True)
        logger.info(f"バックアップディレクトリを作成しました: {backup_path}")
        
        # 環境変数を設定
        env = os.environ.copy()
        env["MC_HOST_mensis"] = f"http://{connection_info['MINIO_ACCESS_KEY']}:{connection_info['MINIO_SECRET_KEY']}@{connection_info['MINIO_HOST']}:{connection_info['MINIO_PORT']}"
        
        # バケットのバックアップを実行
        logger.info(f"MinIOバケット {connection_info['MINIO_BUCKET']} のバックアップを開始します")
        result = subprocess.run(
            ["mc", "mirror", f"mensis/{connection_info['MINIO_BUCKET']}", backup_path, "--overwrite"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"MinIOバックアップ実行中にエラーが発生しました: {result.stderr}")
            return False, 0
            
        logger.info(f"MinIOバケット {connection_info['MINIO_BUCKET']} のバックアップが完了しました")
        
        # バックアップサイズの計算
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(backup_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
                    
        logger.info(f"バックアップサイズ: {format_bytes(total_size)}")
        
        # 古いバックアップの削除処理
        cleanup_old_backups(backup_dir, int(connection_info.get('MINIO_BACKUP_GENERATION', 12)), logger)
        
        return True, total_size
        
    except Exception as e:
        logger.error(f"MinIOバックアップ中にエラーが発生しました: {str(e)}")
        return False, 0

def manual_backup_minio(connection_info, logger, backup_dir="/backup/minio"):
    """
    MinIOバケットの手動バックアップを実行する
    
    Args:
        connection_info (dict): Minioの接続情報
        logger (logging.Logger): ロガーオブジェクト
        backup_dir (str): バックアップの保存先ディレクトリ
        
    Returns:
        tuple: (成功したかどうかのbool, バックアップサイズ(bytes))
    """
    # 手動バックアップは自動バックアップと同じロジックを使用
    return auto_backup_minio(connection_info, logger, backup_dir)

def cleanup_old_backups(backup_dir, keep_count=12, logger=None):
    """
    古いバックアップを削除する
    
    Args:
        backup_dir (str): バックアップディレクトリのパス
        keep_count (int): 保持するバックアップの数
        logger (logging.Logger): ロガーオブジェクト
    """
    if logger is None:
        logger = setup_logger(name='minio_cleanup')
        
    try:
        # バックアップディレクトリが存在するか確認
        if not os.path.exists(backup_dir):
            logger.warning(f"バックアップディレクトリが存在しません: {backup_dir}")
            return
            
        # minio_backup_で始まるディレクトリを取得し、日時でソート
        backup_dirs = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d)) and d.startswith('minio_backup_')]
        backup_dirs.sort(reverse=True)  # 新しい順にソート
        
        # 保持数を超える古いバックアップを削除
        if len(backup_dirs) > keep_count:
            for old_dir in backup_dirs[keep_count:]:
                old_path = os.path.join(backup_dir, old_dir)
                logger.info(f"古いバックアップを削除します: {old_path}")
                shutil.rmtree(old_path)
                
            logger.info(f"バックアップのクリーンアップ完了: {len(backup_dirs) - keep_count} 個のバックアップを削除しました")
    except Exception as e:
        logger.error(f"バックアップのクリーンアップ中にエラーが発生しました: {str(e)}")

def minio_backup_frequency_check(logger=None):
    """
    設定されたバックアップ頻度に基づいて、本日バックアップを実行すべきかチェックする
    
    Args:
        logger (logging.Logger): ロガーオブジェクト
        
    Returns:
        bool: 今日バックアップすべき場合はTrue、そうでない場合はFalse
    """
    if logger is None:
        logger = setup_logger(name='minio_frequency_check')
        
    frequency = os.environ.get('MINIO_BACKUP_FREQUENCY', 'everyday')
    
    if frequency == 'everyday':
        return True
    elif frequency == 'every_second':  # 隔日
        return datetime.datetime.now().day % 2 != 0  # 奇数日に実行
    elif frequency == 'every_third':  # 3日に1回
        return datetime.datetime.now().day % 3 == 1  # 1, 4, 7, 10, ...日に実行
    else:
        logger.warning(f"不明なバックアップ頻度: {frequency}。毎日のバックアップを実行します。")
        return True
