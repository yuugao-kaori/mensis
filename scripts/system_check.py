import os
import shutil
import psutil
from custom_logging import setup_logger
def get_disk_usage(path='/'):
    """
    指定されたパスのディスク使用率を取得します。
    
    Args:
        path (str): ディスク使用率を調べるパスまたはマウントポイント。デフォルトは'/'（ルートディレクトリ）。
        
    Returns:
        dict: 以下の情報を含む辞書:
            - total: 合計容量（バイト）
            - used: 使用済み容量（バイト）
            - free: 空き容量（バイト）
            - percent: 使用率（パーセント）
    """
    logger = setup_logger(name='get_disk_usage')
    try:
        # shutil.disk_usageを使用した方法
        # total, used, free = shutil.disk_usage(path)
        
        # psutilを使用した方法（より詳細な情報が取得可能）
        disk_info = psutil.disk_usage(path)
        logger.info(f"Disk usage: {disk_info}")
        return {
            'total': disk_info.total,
            'used': disk_info.used,
            'free': disk_info.free,
            'percent': disk_info.percent
        }

    except Exception as e:
        logger.error(f"Failed to get disk usage: {e}")
        return {
            'error': str(e),
            'total': 0,
            'used': 0,
            'free': 0,
            'percent': 0
        }

def format_bytes(bytes_value):
    """
    バイト数を人間が読みやすい形式に変換します。
    
    Args:
        bytes_value (int): 変換するバイト数
        
    Returns:
        str: 変換された文字列（例：'1.23 GB'）
    """
    logger = setup_logger(name='format_bytes')
    logger.info(f"Formatting bytes: {bytes_value}")
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0 or unit == 'TB':
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
