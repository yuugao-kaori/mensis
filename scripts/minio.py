import os
import time
import datetime
import subprocess
import shutil
import tarfile
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
        env["MC_HOST_mensis"] = f"http://{connection_info['minio_access_key']}:{connection_info['minio_secret_key']}@{connection_info['minio_host']}:{connection_info['minio_port']}"

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
        ls_command = ["mc", "ls", f"mensis/{connection_info['minio_bucket']}"]
        logger.info(f"MinIO接続確認コマンドを実行: {' '.join(ls_command)}")
        
        result = subprocess.run(ls_command, 
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
    MinIOバケットの自動バックアップを実行する（圧縮付き）
    
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
        temp_backup_path = os.path.join(backup_dir, f"minio_backup_{timestamp}_temp")
        compressed_backup_path = os.path.join(backup_dir, f"minio_backup_{timestamp}.tar.gz")
        
        # バックアップディレクトリの作成
        os.makedirs(temp_backup_path, exist_ok=True)
        logger.info(f"一時バックアップディレクトリを作成しました: {temp_backup_path}")
        
        # 環境変数を設定
        env = os.environ.copy()
        env["MC_HOST_mensis"] = f"http://{connection_info['minio_access_key']}:{connection_info['minio_secret_key']}@{connection_info['minio_host']}:{connection_info['minio_port']}"
        
        # バケットのバックアップを実行
        logger.info(f"MinIOバケット {connection_info['minio_bucket']} のバックアップを開始します")

        mirror_command = ["mc", "mirror", f"mensis/{connection_info['minio_bucket']}", temp_backup_path, "--overwrite"]
        logger.info(f"バックアップコマンドを実行: {' '.join(mirror_command)}")
        
        result = subprocess.run(
            mirror_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"MinIOバックアップ実行中にエラーが発生しました: {result.stderr}")
            # 一時ディレクトリをクリーンアップ
            if os.path.exists(temp_backup_path):
                shutil.rmtree(temp_backup_path)
            return False, 0
        else:
            logger.info(f"バックアップコマンドが正常に完了しました")
        
        # バックアップを圧縮
        logger.info(f"バックアップを圧縮しています: {compressed_backup_path}")
        try:
            with tarfile.open(compressed_backup_path, "w:gz") as tar:
                tar.add(temp_backup_path, arcname=f"minio_backup_{timestamp}")
            logger.info(f"バックアップの圧縮が完了しました")
        except Exception as e:
            logger.error(f"バックアップの圧縮中にエラーが発生しました: {str(e)}")
            # 一時ディレクトリをクリーンアップ
            if os.path.exists(temp_backup_path):
                shutil.rmtree(temp_backup_path)
            return False, 0
        
        # 一時ディレクトリを削除
        shutil.rmtree(temp_backup_path)
        logger.info(f"一時ディレクトリを削除しました: {temp_backup_path}")
        
        logger.info(f"MinIOバケット {connection_info['minio_bucket']} のバックアップが完了しました")

        # 圧縮ファイルのサイズを取得
        total_size = os.path.getsize(compressed_backup_path)
        logger.info(f"圧縮後のバックアップサイズ: {format_bytes(total_size)}")
        
        # 古いバックアップの削除処理
        cleanup_old_backups(backup_dir, int(connection_info.get('minio_backup_generation', 12)), logger)
        
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
    古いバックアップを削除する（圧縮ファイル対応）
    
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
            
        # minio_backup_で始まる圧縮ファイルと非圧縮ディレクトリを取得し、日時でソート
        backup_items = []
        
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            # 圧縮ファイル（.tar.gz）または非圧縮ディレクトリを対象とする
            if item.startswith('minio_backup_'):
                if item.endswith('.tar.gz') and os.path.isfile(item_path):
                    backup_items.append(item)
                elif os.path.isdir(item_path) and not item.endswith('_temp'):
                    backup_items.append(item)
        
        backup_items.sort(reverse=True)  # 新しい順にソート
        
        # 保持数を超える古いバックアップを削除
        if len(backup_items) > keep_count:
            for old_item in backup_items[keep_count:]:
                old_path = os.path.join(backup_dir, old_item)
                logger.info(f"古いバックアップを削除します: {old_path}")
                
                if os.path.isfile(old_path):
                    os.remove(old_path)
                elif os.path.isdir(old_path):
                    shutil.rmtree(old_path)
                
            logger.info(f"バックアップのクリーンアップ完了: {len(backup_items) - keep_count} 個のバックアップを削除しました")
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
