#!/usr/bin/env python3
"""
JavaScript実行機能付きスクレイパーのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper.javascript_scraper import JavaScriptScraper
from src.utils.logger import get_logger

def test_javascript_scraper():
    """JavaScript実行機能付きスクレイパーをテスト"""
    logger = get_logger("TestJavaScriptScraper")
    
    logger.info("="*60)
    logger.info("JavaScript実行機能付きスクレイパーテスト開始")
    logger.info("="*60)
    
    try:
        # スクレイパーを初期化
        scraper = JavaScriptScraper()
        
        # TikTok /exploreページをJavaScript実行機能付きでスクレイピング
        logger.info("TikTok /exploreページのJavaScript実行機能付きスクレイピング開始...")
        
        result = scraper.scrape_tiktok_explore_with_js()
        
        if result.get('success'):
            logger.info(f"JavaScript実行成功!")
            logger.info(f"取得コンテンツサイズ: {len(result.get('content', ''))} 文字")
            logger.info(f"ステータスコード: {result.get('status_code')}")
            logger.info(f"レスポンス時間: {result.get('response_time')} 秒")
            
            # HTMLコンテンツから動画データを抽出
            html_content = result.get('content', '')
            if html_content:
                logger.info("\n動画データ抽出開始...")
                
                videos = scraper.extract_video_data_from_js_content(html_content)
                
                logger.info(f"抽出された動画数: {len(videos)}")
                
                # 動画データの詳細を表示
                for i, video in enumerate(videos[:10]):  # 最初の10件のみ表示
                    logger.info(f"\n--- 動画 {i+1} ---")
                    logger.info(f"ID: {video.get('video_id', 'N/A')}")
                    logger.info(f"URL: {video.get('url', 'N/A')}")
                    logger.info(f"作者: {video.get('author_username', 'N/A')}")
                    logger.info(f"説明: {video.get('description', video.get('text_content', 'N/A'))[:100]}...")
                    logger.info(f"再生数: {video.get('view_count', 'N/A')}")
                    logger.info(f"いいね数: {video.get('like_count', 'N/A')}")
                    logger.info(f"抽出方法: {video.get('extraction_method', 'N/A')}")
                
                if len(videos) > 10:
                    logger.info(f"\n... 他 {len(videos) - 10} 件")
                
                # 結果をファイルに保存
                import json
                output_file = "debug/javascript_scraper_result.json"
                os.makedirs("debug", exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'scraping_result': result,
                        'extracted_videos': videos,
                        'total_videos': len(videos),
                        'timestamp': str(datetime.now())
                    }, f, ensure_ascii=False, indent=2)
                
                logger.info(f"\n結果を保存: {output_file}")
                
                # HTMLコンテンツも保存
                html_file = "debug/javascript_scraper_content.html"
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                logger.info(f"HTMLコンテンツを保存: {html_file}")
                
            else:
                logger.warning("HTMLコンテンツが空です")
        else:
            logger.error(f"JavaScript実行失敗: {result}")
            
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n" + "="*60)
    logger.info("JavaScript実行機能付きスクレイパーテスト完了")
    logger.info("="*60)

if __name__ == "__main__":
    from datetime import datetime
    test_javascript_scraper()

