"""
TikTok Research System

ScraperAPI TikTok Scraperを使用したTikTok動画自動収集システム
"""

__version__ = "1.0.0"
__author__ = "Manus AI Agent"
__description__ = "TikTok automatic research system using ScraperAPI"

# パッケージレベルのインポート
from .utils.logger import get_logger
from .utils.config import Config

# デフォルトロガーの設定
logger = get_logger(__name__)

# バージョン情報
def get_version():
    """バージョン情報を取得"""
    return __version__

def get_info():
    """システム情報を取得"""
    return {
        "name": "TikTok Research System",
        "version": __version__,
        "author": __author__,
        "description": __description__
    }

