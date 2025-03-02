import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name=None, log_file='/scripts/python.log', level=logging.INFO):
    """
    ロギング設定を行うヘルパー関数
    
    Args:
        name (str): ロガーの名前。Noneの場合はルートロガーを使用
        log_file (str): ログファイルのパス
        level (int): ロギングレベル
    
    Returns:
        Logger: 設定済みのロガーインスタンス
    """
    # ディレクトリが存在しない場合は作成
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 指定された名前でロガーを取得
    logger = logging.getLogger(name)
    
    # ロガーのレベルが設定されていない場合のみ設定
    if not logger.handlers:
        logger.setLevel(level)
        
        # ファイルハンドラー（ローテーション付き）
        try:
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except (PermissionError, IOError, OSError) as e:
            print(f"警告: ログファイル '{log_file}' に書き込みができません: {e}", file=sys.stderr)
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
    
    return logger
