"""
Helper utilities for TikTok Research System
"""

import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Union, Any
import pytz


def parse_view_count(view_text: str) -> Optional[int]:
    """
    再生数テキストを数値に変換
    
    Args:
        view_text: 再生数テキスト（例: "1.2M", "500K", "1,234"）
        
    Returns:
        再生数（数値）、パースできない場合はNone
    """
    if not view_text or not isinstance(view_text, str):
        return None
    
    # テキストをクリーンアップ
    text = view_text.strip().upper().replace(',', '').replace(' ', '')
    
    # 数値部分を抽出
    match = re.search(r'([\d.]+)([KMB]?)', text)
    if not match:
        return None
    
    number_str, unit = match.groups()
    
    try:
        number = float(number_str)
        
        # 単位に応じて変換
        multipliers = {
            'K': 1_000,
            'M': 1_000_000,
            'B': 1_000_000_000
        }
        
        if unit in multipliers:
            number *= multipliers[unit]
        
        return int(number)
        
    except (ValueError, TypeError):
        return None


def parse_upload_date(date_text: str, timezone: str = 'Asia/Tokyo') -> Optional[datetime]:
    """
    投稿日時テキストをdatetimeに変換
    
    Args:
        date_text: 日時テキスト
        timezone: タイムゾーン
        
    Returns:
        datetime オブジェクト、パースできない場合はNone
    """
    if not date_text or not isinstance(date_text, str):
        return None
    
    text = date_text.strip().lower()
    now = datetime.now(pytz.timezone(timezone))
    
    # 相対時間のパターン
    relative_patterns = [
        (r'(\d+)\s*分前', 'minutes'),
        (r'(\d+)\s*時間前', 'hours'),
        (r'(\d+)\s*日前', 'days'),
        (r'(\d+)\s*週間前', 'weeks'),
        (r'(\d+)\s*ヶ月前', 'months'),
        (r'(\d+)\s*年前', 'years'),
        (r'(\d+)m\s*ago', 'minutes'),
        (r'(\d+)h\s*ago', 'hours'),
        (r'(\d+)d\s*ago', 'days'),
        (r'(\d+)w\s*ago', 'weeks'),
    ]
    
    for pattern, unit in relative_patterns:
        match = re.search(pattern, text)
        if match:
            value = int(match.group(1))
            
            if unit == 'minutes':
                return now - timedelta(minutes=value)
            elif unit == 'hours':
                return now - timedelta(hours=value)
            elif unit == 'days':
                return now - timedelta(days=value)
            elif unit == 'weeks':
                return now - timedelta(weeks=value)
            elif unit == 'months':
                return now - timedelta(days=value * 30)  # 概算
            elif unit == 'years':
                return now - timedelta(days=value * 365)  # 概算
    
    # 絶対時間のパターン
    absolute_patterns = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%m/%d/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
    ]
    
    for pattern in absolute_patterns:
        try:
            dt = datetime.strptime(text, pattern)
            # タイムゾーンを設定
            if dt.tzinfo is None:
                dt = pytz.timezone(timezone).localize(dt)
            return dt
        except ValueError:
            continue
    
    return None


def is_within_time_range(upload_date: datetime, hours: int = 24) -> bool:
    """
    指定時間範囲内かチェック
    
    Args:
        upload_date: 投稿日時
        hours: 時間範囲
        
    Returns:
        範囲内かどうか
    """
    if not upload_date:
        return False
    
    now = datetime.now(upload_date.tzinfo or pytz.UTC)
    time_diff = now - upload_date
    
    return time_diff <= timedelta(hours=hours)


def clean_text(text: str) -> str:
    """
    テキストをクリーンアップ
    
    Args:
        text: 元のテキスト
        
    Returns:
        クリーンアップされたテキスト
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 改行・タブを空白に変換
    text = re.sub(r'[\n\r\t]+', ' ', text)
    
    # 連続する空白を単一空白に変換
    text = re.sub(r'\s+', ' ', text)
    
    # 前後の空白を削除
    text = text.strip()
    
    return text


def validate_url(url: str) -> bool:
    """
    URLの妥当性をチェック
    
    Args:
        url: チェックするURL
        
    Returns:
        妥当性
    """
    if not url or not isinstance(url, str):
        return False
    
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def extract_video_id(url: str) -> Optional[str]:
    """
    TikTok URLから動画IDを抽出
    
    Args:
        url: TikTok URL
        
    Returns:
        動画ID、抽出できない場合はNone
    """
    if not url or not isinstance(url, str):
        return None
    
    # TikTok動画URLのパターン
    patterns = [
        r'tiktok\.com/@[\w.-]+/video/(\d+)',
        r'tiktok\.com/v/(\d+)',
        r'vm\.tiktok\.com/(\w+)',
        r'tiktok\.com/t/(\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def format_number(number: Union[int, float], precision: int = 1) -> str:
    """
    数値を読みやすい形式にフォーマット
    
    Args:
        number: 数値
        precision: 小数点以下の桁数
        
    Returns:
        フォーマットされた文字列
    """
    if not isinstance(number, (int, float)):
        return str(number)
    
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.{precision}f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.{precision}f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.{precision}f}K"
    else:
        return str(int(number))


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    辞書から安全に値を取得（ドット記法対応）
    
    Args:
        data: 辞書
        key: キー（ドット記法対応）
        default: デフォルト値
        
    Returns:
        値
    """
    if not isinstance(data, dict):
        return default
    
    keys = key.split('.')
    value = data
    
    try:
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default


def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """
    例外発生時のリトライデコレータ
    
    Args:
        max_retries: 最大リトライ回数
        delay: リトライ間隔（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # 指数バックオフ
            
        return wrapper
    return decorator

