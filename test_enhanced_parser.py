#!/usr/bin/env python3
"""
改良版TikTokパーサーのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.parser.tiktok_parser import TikTokParser
from src.utils.logger import get_logger

def test_enhanced_parser():
    """改良版パーサーをテスト"""
    logger = get_logger("TestEnhancedParser")
    
    # パーサーを初期化
    parser = TikTokParser()
    
    # 取得したHTMLファイルを読み込み
    html_files = [
        "debug/tiktok_explore_strategy_1.html",
        "debug/tiktok_explore_strategy_2.html", 
        "debug/tiktok_explore_strategy_3.html"
    ]
    
    total_videos = 0
    
    for html_file in html_files:
        if not os.path.exists(html_file):
            logger.warning(f"ファイルが見つかりません: {html_file}")
            continue
            
        logger.info(f"\n{'='*60}")
        logger.info(f"テスト開始: {html_file}")
        logger.info(f"{'='*60}")
        
        try:
            # HTMLファイルを読み込み
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            logger.info(f"HTMLサイズ: {len(html_content):,} 文字")
            
            # パーサーでテスト
            video_collection = parser.parse_explore_page(html_content)
            
            logger.info(f"抽出された動画数: {len(video_collection.videos)}")
            total_videos += len(video_collection.videos)
            
            # 動画データの詳細を表示
            for i, video in enumerate(video_collection.videos[:5]):  # 最初の5件のみ表示
                logger.info(f"\n--- 動画 {i+1} ---")
                logger.info(f"ID: {video.video_id}")
                logger.info(f"URL: {video.url}")
                logger.info(f"タイトル: {video.title}")
                logger.info(f"作者: {video.author_username} ({video.author_display_name})")
                logger.info(f"再生数: {video.view_count:,}" if video.view_count else "再生数: 不明")
                logger.info(f"いいね数: {video.like_count:,}" if video.like_count else "いいね数: 不明")
                logger.info(f"投稿日時: {video.upload_date}" if video.upload_date else "投稿日時: 不明")
                logger.info(f"ハッシュタグ: {', '.join(video.hashtags)}" if video.hashtags else "ハッシュタグ: なし")
            
            if len(video_collection.videos) > 5:
                logger.info(f"\n... 他 {len(video_collection.videos) - 5} 件")
                
        except Exception as e:
            logger.error(f"テストエラー ({html_file}): {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"テスト完了")
    logger.info(f"総動画数: {total_videos}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    test_enhanced_parser()

