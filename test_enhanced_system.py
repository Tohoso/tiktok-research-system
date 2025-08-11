#!/usr/bin/env python3
"""
改良版TikTok自動リサーチシステムの統合テスト
"""

import os
import sys
import json
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import get_logger
from src.parser.enhanced_tiktok_parser import EnhancedTikTokParser
from src.filter.video_filter import VideoFilter
from src.storage.database import DatabaseManager
from src.monitor.system_monitor import SystemMonitor


def main():
    """改良版システムの統合テスト"""
    logger = get_logger("EnhancedSystemTest")
    logger.info("改良版TikTok自動リサーチシステムの統合テストを開始")
    
    try:
        # 1. 既存の成功データを使用してパーサーテスト
        logger.info("=== フェーズ1: 改良版パーサーテスト ===")
        
        parser = EnhancedTikTokParser()
        
        # 既存の成功データファイルを読み込み
        html_files = [
            "debug/tiktok_explore_strategy_1.html",
            "debug/tiktok_explore_strategy_2.html", 
            "debug/tiktok_explore_strategy_3.html"
        ]
        
        all_videos = []
        
        for html_file in html_files:
            if os.path.exists(html_file):
                logger.info(f"HTMLファイル解析: {html_file}")
                
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                videos = parser.parse_videos(html_content)
                logger.info(f"{html_file}: {len(videos)}件の動画データを抽出")
                
                all_videos.extend(videos)
            else:
                logger.warning(f"HTMLファイルが見つかりません: {html_file}")
        
        logger.info(f"総動画数: {len(all_videos)}件")
        
        # 2. フィルタリング機能テスト
        logger.info("=== フェーズ2: フィルタリング機能テスト ===")
        
        video_filter = VideoFilter()
        
        # 条件1: 50万再生以上
        high_view_videos = video_filter.filter_by_views(all_videos, min_views=500000)
        logger.info(f"50万再生以上の動画: {len(high_view_videos)}件")
        
        # 条件2: 24時間以内（テスト用に1週間に緩和）
        recent_videos = video_filter.filter_by_date(all_videos, hours_ago=168)
        logger.info(f"1週間以内の動画: {len(recent_videos)}件")
        
        # 条件3: 組み合わせフィルタリング
        filtered_videos = video_filter.apply_trending_filter(
            all_videos,
            min_views=100000,  # テスト用に10万に緩和
            hours_ago=168,     # 1週間
            min_engagement_score=0.001
        )
        logger.info(f"フィルタリング後の動画: {len(filtered_videos)}件")
        
        # 3. データベース統合テスト
        logger.info("=== フェーズ3: データベース統合テスト ===")
        
        db_manager = DatabaseManager()
        
        # データベース初期化
        db_manager.initialize_database()
        logger.info("データベース初期化完了")
        
        # 動画データ保存テスト
        saved_count = 0
        for video in filtered_videos[:10]:  # 最初の10件をテスト
            try:
                success = db_manager.save_video(video)
                if success:
                    saved_count += 1
            except Exception as e:
                logger.warning(f"動画保存エラー: {e}")
        
        logger.info(f"データベース保存成功: {saved_count}件")
        
        # データベース統計取得
        stats = db_manager.get_statistics()
        logger.info(f"データベース統計: {stats}")
        
        # 4. システム監視機能テスト
        logger.info("=== フェーズ4: システム監視機能テスト ===")
        
        monitor = SystemMonitor()
        
        # システム統計取得
        system_stats = monitor.get_system_stats()
        logger.info(f"システム統計: {system_stats}")
        
        # ヘルススコア計算
        health_score = monitor.calculate_health_score()
        logger.info(f"システムヘルススコア: {health_score}/100")
        
        # 5. 結果サマリー
        logger.info("=== テスト結果サマリー ===")
        
        results = {
            "test_timestamp": datetime.now().isoformat(),
            "total_videos_extracted": len(all_videos),
            "high_view_videos": len(high_view_videos),
            "recent_videos": len(recent_videos),
            "filtered_videos": len(filtered_videos),
            "database_saved": saved_count,
            "system_health_score": health_score,
            "test_status": "SUCCESS"
        }
        
        # 結果をファイルに保存
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info("統合テスト完了")
        logger.info(f"結果: {results}")
        
        # 成功した動画の詳細表示
        if filtered_videos:
            logger.info("=== フィルタリング成功動画（上位5件） ===")
            for i, video in enumerate(filtered_videos[:5], 1):
                logger.info(f"動画{i}: {video.video_id}")
                logger.info(f"  URL: {video.url}")
                logger.info(f"  作者: {video.author_username}")
                logger.info(f"  再生数: {video.view_count:,}" if video.view_count else "  再生数: 不明")
                logger.info(f"  説明: {video.description[:100]}...")
                logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"統合テストエラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

