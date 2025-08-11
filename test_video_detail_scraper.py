"""
Test script for VideoDetailScraper
"""

import os
import sys
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper.video_detail_scraper import VideoDetailScraper
from src.utils.logger import get_logger
from src.utils.config import config


def test_video_detail_scraper():
    """VideoDetailScraperのテスト"""
    logger = get_logger("VideoDetailScraperTest")
    logger.info("VideoDetailScraperのテストを開始")
    
    try:
        # 設定読み込み
        api_key = config.get('scraper.api_key')
        
        # VideoDetailScraperを初期化
        detail_scraper = VideoDetailScraper(api_key)
        
        # テスト用動画URL（以前に取得した23件から一部を使用）
        test_video_urls = [
            "https://www.tiktok.com/@_quietlydope/video/7535094688726945079",
            "https://www.tiktok.com/@ohnoitsrolo/video/7534370912854985997",
            "https://www.tiktok.com/@sc0ttydog81/video/7532629994703539486",
            "https://www.tiktok.com/@ig..ig17/video/7533384463401684246",
            "https://www.tiktok.com/@cdukes33/video/7534379272505462071"
        ]
        
        logger.info(f"テスト対象動画: {len(test_video_urls)}件")
        
        # 個別テスト
        logger.info("=== 個別動画詳細取得テスト ===")
        for i, url in enumerate(test_video_urls[:2]):  # 最初の2件でテスト
            logger.info(f"\\nテスト {i + 1}: {url}")
            
            details = detail_scraper.get_video_details(url)
            
            if details:
                logger.info("✅ 詳細情報取得成功")
                logger.info(f"動画ID: {details.get('video_id', 'N/A')}")
                logger.info(f"タイトル: {details.get('title', 'N/A')}")
                logger.info(f"作者: {details.get('author_username', 'N/A')}")
                logger.info(f"再生数: {details.get('view_count', 'N/A')}")
                logger.info(f"いいね数: {details.get('like_count', 'N/A')}")
                logger.info(f"投稿日時: {details.get('create_time', 'N/A')}")
                
                # 詳細情報をファイルに保存
                output_file = f"debug/video_details_{details.get('video_id', i)}.json"
                os.makedirs("debug", exist_ok=True)
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(details, f, ensure_ascii=False, indent=2)
                
                logger.info(f"詳細情報を保存: {output_file}")
            else:
                logger.error("❌ 詳細情報取得失敗")
        
        # 複数動画一括テスト
        logger.info("\\n=== 複数動画一括取得テスト ===")
        all_details = detail_scraper.get_multiple_video_details(
            test_video_urls,
            max_concurrent=2,
            delay_between_requests=5.0
        )
        
        logger.info(f"一括取得結果: {len(all_details)}/{len(test_video_urls)}件成功")
        
        # 結果の分析
        logger.info("\\n=== 取得結果分析 ===")
        
        videos_with_views = [d for d in all_details if d.get('view_count')]
        videos_with_likes = [d for d in all_details if d.get('like_count')]
        videos_with_dates = [d for d in all_details if d.get('create_time')]
        videos_with_authors = [d for d in all_details if d.get('author_username')]
        
        logger.info(f"再生数データあり: {len(videos_with_views)}/{len(all_details)}件")
        logger.info(f"いいね数データあり: {len(videos_with_likes)}/{len(all_details)}件")
        logger.info(f"投稿日時データあり: {len(videos_with_dates)}/{len(all_details)}件")
        logger.info(f"作者データあり: {len(videos_with_authors)}/{len(all_details)}件")
        
        # 高再生数動画の特定
        high_view_videos = [
            d for d in videos_with_views 
            if isinstance(d.get('view_count'), int) and d['view_count'] >= 500000
        ]
        
        logger.info(f"50万再生以上の動画: {len(high_view_videos)}件")
        
        for video in high_view_videos:
            logger.info(f"  - {video.get('author_username', 'Unknown')}: {video.get('view_count', 0):,}再生")
        
        # 統計情報
        logger.info("\\n=== 統計情報 ===")
        stats = detail_scraper.get_statistics()
        
        logger.info(f"総リクエスト数: {stats['total_requests']}")
        logger.info(f"成功リクエスト数: {stats['successful_requests']}")
        logger.info(f"失敗リクエスト数: {stats['failed_requests']}")
        logger.info(f"成功率: {stats['success_rate']:.1f}%")
        logger.info(f"詳細情報取得成功: {stats['videos_with_details']}件")
        logger.info(f"詳細情報取得失敗: {stats['videos_without_details']}件")
        
        # 全結果をファイルに保存
        output_file = "debug/all_video_details.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_videos': len(test_video_urls),
                'successful_extractions': len(all_details),
                'statistics': stats,
                'video_details': all_details
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"全結果を保存: {output_file}")
        
        # テスト結果の評価
        logger.info("\\n=== テスト結果評価 ===")
        
        if len(all_details) > 0:
            logger.info("✅ VideoDetailScraperは基本的に動作しています")
            
            if len(videos_with_views) > 0:
                logger.info("✅ 再生数データの取得に成功しています")
            else:
                logger.warning("⚠️ 再生数データの取得に課題があります")
            
            if len(high_view_videos) > 0:
                logger.info("✅ 高再生数動画の特定に成功しています")
            else:
                logger.warning("⚠️ 高再生数動画が見つかりませんでした")
        else:
            logger.error("❌ VideoDetailScraperに重大な問題があります")
        
        logger.info("VideoDetailScraperのテスト完了")
        return all_details
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        return []


if __name__ == "__main__":
    test_video_detail_scraper()

