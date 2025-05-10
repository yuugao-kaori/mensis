import os
import sys
import requests
import json
import time
from pathlib import Path
import dotenv
from load_env import load_env
from custom_logging import setup_logger


# 以下、残りのコードは変更なし


def sendDM_misskey_notification(text, visibility="specified", visible_user_ids=None, cw=None, local_only=False):
    """
    Misskeyに投稿を送信する関数
    
    Args:
        text (str): 投稿するテキスト内容
        visibility (str): 投稿の公開範囲 ("public", "home", "followers", "specified")
        visible_user_ids (list): visibilityが"specified"の場合、表示を許可するユーザーIDのリスト
        cw (str): コンテンツ警告（任意）
        local_only (bool): ローカルのみに投稿するかどうか
        
    Returns:
        dict: API応答のJSON、または失敗時にはNone
    """
    logger = setup_logger(name='sendDM_misskey_notification')
    try:
        # 環境変数の読み込み
        env_config = load_env()
        
        # Misskey関連の設定を取得
        misskey_host = os.getenv('MISSKEY_HOST')
        token = os.getenv('MISSKEY_NOTICE_USER_TOKEN')
        
        if not misskey_host or not token:
            logger.error("MISSKEY_HOST or MISSKEY_NOTICE_USER_TOKEN not found in environment variables")
            return None
        
        # APIエンドポイントの構築
        url = f"https://{misskey_host}/api/notes/create"
        
        # ヘッダーの設定
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 可視性設定
        if visible_user_ids is None and visibility == "specified":
            target_user_id = os.getenv('MISSKEY_TEARGET_USER_ID')
            visible_user_ids = [target_user_id] if target_user_id else []
        
        # ペイロードの構築
        payload = {
            "visibility": visibility,
            "visibleUserIds": visible_user_ids or [],
            "cw": cw,
            "localOnly": local_only,
            "reactionAcceptance": None,
            "noExtractMentions": False,
            "noExtractHashtags": False,
            "noExtractEmojis": False,
            "channelId": None,
            "text": text
        }
        
        # 不要なNoneの値を削除
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # リクエスト送信 - 最大6回、20秒間隔で再試行
        logger.info(f"Sending notification to Misskey: {url}")
        print(f"Sending notification to Misskey: {url}")
        
        max_retries = 6
        retry_count = 0
        retry_delay = 20  # 秒
        
        while retry_count < max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Notification sent successfully: {response.status_code}")
                print(f"Notification sent successfully: {response.status_code}")
                return response.json()
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to send notification to Misskey after {max_retries} attempts: {e}")
                    return None
                
                logger.warning(f"Error sending notification (attempt {retry_count}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                print(f"Error sending notification (attempt {retry_count}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
    except Exception as e:
        logger.error(f"Unexpected error in sendDM_misskey_notification: {e}")
        return None



def post_misskey_notification(text, visibility="public", visible_user_ids=None, cw=None, local_only=False):
    """
    Misskeyに投稿を送信する関数
    
    Args:
        text (str): 投稿するテキスト内容
        visibility (str): 投稿の公開範囲 ("public", "home", "followers", "specified")
        visible_user_ids (list): visibilityが"specified"の場合、表示を許可するユーザーIDのリスト
        cw (str): コンテンツ警告（任意）
        local_only (bool): ローカルのみに投稿するかどうか
        
    Returns:
        dict: API応答のJSON、または失敗時にはNone
    """
    logger = setup_logger(name='post_misskey_notification')
    try:
        # 環境変数の読み込み
        env_config = load_env()
        
        # Misskey関連の設定を取得
        misskey_host = os.getenv('MISSKEY_HOST')
        token = os.getenv('MISSKEY_NOTICE_USER_TOKEN')
        
        if not misskey_host or not token:
            logger.error("MISSKEY_HOST or MISSKEY_NOTICE_USER_TOKEN not found in environment variables")
            return None
        
        # APIエンドポイントの構築
        url = f"https://{misskey_host}/api/notes/create"
        
        # ヘッダーの設定
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
       
        # ペイロードの構築
        payload = {
            "visibility": visibility,
            "visibleUserIds": visible_user_ids or [],
            "cw": cw,
            "localOnly": local_only,
            "reactionAcceptance": None,
            "noExtractMentions": False,
            "noExtractHashtags": False,
            "noExtractEmojis": False,
            "channelId": None,
            "text": text
        }
        
        # 不要なNoneの値を削除
        payload = {k: v for k, v in payload.items() if v is not None}
        
        # リクエスト送信 - 最大6回、20秒間隔で再試行
        logger.info(f"Sending notification to Misskey: {url}")
        print(f"Sending notification to Misskey: {url}")
        
        max_retries = 6
        retry_count = 0
        retry_delay = 20  # 秒
        
        while retry_count < max_retries:
            try:
                response = requests.post(url, headers=headers, json=payload)
                response.raise_for_status()
                logger.info(f"Notification sent successfully: {response.status_code}")
                print(f"Notification sent successfully: {response.status_code}")
                return response.json()
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Failed to send notification to Misskey after {max_retries} attempts: {e}")
                    return None
                
                logger.warning(f"Error sending notification (attempt {retry_count}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                print(f"Error sending notification (attempt {retry_count}/{max_retries}): {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
    except Exception as e:
        logger.error(f"Unexpected error in post_misskey_notification: {e}")
        return None