import logging
import sys
from pathlib import Path

def setup_logger(name=None, log_file=None, level=logging.INFO):
    """
    ロガーを設定してインスタンスを返す
    
    Args:
        name (str, optional): ロガーの名前
        log_file (str, optional): ログファイルのパス
        level (int, optional): ログレベル
        
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    # ロガーの名前が指定されていない場合はメインのロガーを使用
    logger = logging.getLogger(name or __name__)
    logger.setLevel(level)
    
    # 既存のハンドラーをクリア
    logger.handlers = []
    
    # フォーマッターの作成
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 標準出力へのハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ログファイルが指定されている場合、ファイルハンドラーを追加
    if log_file:
        # ログディレクトリの作成
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
