import os
import sys
import requests
import json
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
        
        # リクエスト送信
        logger.info(f"Sending notification to Misskey: {url}")
        print(f"Sending notification to Misskey: {url}")
        response = requests.post(url, headers=headers, json=payload)
        
        # レスポンスの確認
        response.raise_for_status()
        logger.info(f"Notification sent successfully: {response.status_code}")
        print(f"Notification sent successfully: {response.status_code}")
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to send notification to Misskey: {e}")
        return



def post_misskey_notification(text, visibility="home", visible_user_ids=None, cw=None, local_only=False):
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
        
        # リクエスト送信
        logger.info(f"Sending notification to Misskey: {url}")
        print(f"Sending notification to Misskey: {url}")
        response = requests.post(url, headers=headers, json=payload)
        
        # レスポンスの確認
        response.raise_for_status()
        logger.info(f"Notification sent successfully: {response.status_code}")
        print(f"Notification sent successfully: {response.status_code}")
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to send notification to Misskey: {e}")
        return