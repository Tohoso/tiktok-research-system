"""
TikTok Research System - Main Application
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from .utils.config import config
from .utils.logger import get_logger, setup_logging
from .scraper.tiktok_scraper import TikTokScraper
from .storage.database import DatabaseManager
from .filter.video_filter import VideoFilter
from .monitor.system_monitor import SystemMonitor


class TikTokResearchApp:
    """TikTok自動リサーチアプリケーション"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        アプリケーションを初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        # 設定を読み込み
        if config_path:
            config.load_config(config_path)
        
        # ログを設定
        setup_logging()
        self.logger = get_logger(self.__class__.__name__)
        
        # コンポーネントを初期化
        self.scraper = TikTokScraper()
        self.database = DatabaseManager()
        self.filter = VideoFilter()
        self.monitor = SystemMonitor()
        
        self.logger.info("TikTok自動リサーチシステムを初期化しました")
    
    def collect_trending_videos(
        self,
        target_count: int = 100,
        min_views: int = 500000,
        hours_ago: int = 24
    ) -> dict:
        """
        トレンド動画を収集
        
        Args:
            target_count: 目標収集数
            min_views: 最小再生数
            hours_ago: 何時間前から
            
        Returns:
            収集結果
        """
        self.logger.info(f"トレンド動画収集を開始 (目標: {target_count}件, 最小再生数: {min_views:,})")
        
        start_time = datetime.now()
        
        try:
            # システム監視を開始
            self.monitor.start_monitoring()
            
            # 動画を収集
            collection = self.scraper.collect_trending_videos(
                target_count=target_count,
                max_attempts=5
            )
            
            # フィルタリング
            filtered_videos = self.filter.apply_trending_filter(
                collection.videos,
                min_views=min_views,
                hours_ago=hours_ago
            )
            
            # データベースに保存
            collection.videos = filtered_videos
            collection.total_count = len(filtered_videos)
            collection_id = self.database.save_collection(collection)
            
            # 実行時間を記録
            duration = (datetime.now() - start_time).total_seconds()
            self.monitor.record_performance_metric(
                operation="collect_trending_videos",
                duration=duration,
                success=True
            )
            
            result = {
                'success': True,
                'collection_id': collection_id,
                'collected_count': len(filtered_videos),
                'target_count': target_count,
                'duration_seconds': duration,
                'videos': [
                    {
                        'video_id': v.video_id,
                        'url': v.url,
                        'title': v.title,
                        'author_username': v.author_username,
                        'view_count': v.view_count,
                        'upload_date': v.upload_date.isoformat() if v.upload_date else None
                    }
                    for v in filtered_videos[:10]  # 最初の10件のみ
                ]
            }
            
            self.logger.info(f"トレンド動画収集完了: {len(filtered_videos)}件 ({duration:.2f}秒)")
            return result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            self.monitor.record_performance_metric(
                operation="collect_trending_videos",
                duration=duration,
                success=False,
                error_message=str(e)
            )
            
            self.logger.error(f"トレンド動画収集エラー: {e}")
            return {
                'success': False,
                'error': str(e),
                'duration_seconds': duration
            }
        
        finally:
            self.monitor.stop_monitoring()
    
    def search_videos(
        self,
        min_views: Optional[int] = None,
        hours_ago: Optional[int] = None,
        author_username: Optional[str] = None,
        limit: int = 100
    ) -> dict:
        """
        動画を検索
        
        Args:
            min_views: 最小再生数
            hours_ago: 何時間前から
            author_username: 作成者ユーザー名
            limit: 取得件数制限
            
        Returns:
            検索結果
        """
        try:
            start_date = None
            if hours_ago:
                start_date = datetime.now() - timedelta(hours=hours_ago)
            
            videos = self.database.search_videos(
                min_views=min_views,
                start_date=start_date,
                author_username=author_username,
                limit=limit
            )
            
            result = {
                'success': True,
                'count': len(videos),
                'videos': [
                    {
                        'video_id': v.video_id,
                        'url': v.url,
                        'title': v.title,
                        'author_username': v.author_username,
                        'view_count': v.view_count,
                        'upload_date': v.upload_date.isoformat() if v.upload_date else None,
                        'hashtags': v.hashtags
                    }
                    for v in videos
                ]
            }
            
            self.logger.info(f"動画検索完了: {len(videos)}件")
            return result
            
        except Exception as e:
            self.logger.error(f"動画検索エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> dict:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        try:
            db_stats = self.database.get_statistics()
            system_status = self.monitor.get_system_status()
            health_score = self.monitor.get_health_score()
            
            return {
                'success': True,
                'database_statistics': db_stats,
                'system_status': system_status,
                'health_score': health_score,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"統計取得エラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def test_connection(self) -> dict:
        """
        接続テスト
        
        Returns:
            テスト結果
        """
        try:
            # ScraperAPI接続テスト
            scraper_test = self.scraper.test_connection()
            
            # データベース接続テスト
            db_test = True
            try:
                self.database.get_statistics()
            except Exception:
                db_test = False
            
            result = {
                'success': scraper_test and db_test,
                'scraper_api': scraper_test,
                'database': db_test,
                'timestamp': datetime.now().isoformat()
            }
            
            if result['success']:
                self.logger.info("接続テスト成功")
            else:
                self.logger.error("接続テスト失敗")
            
            return result
            
        except Exception as e:
            self.logger.error(f"接続テストエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_old_data(self, days: int = 30) -> dict:
        """
        古いデータを削除
        
        Args:
            days: 保持日数
            
        Returns:
            削除結果
        """
        try:
            deleted_count = self.database.cleanup_old_data(days)
            
            result = {
                'success': True,
                'deleted_count': deleted_count,
                'retention_days': days
            }
            
            self.logger.info(f"データクリーンアップ完了: {deleted_count}件削除")
            return result
            
        except Exception as e:
            self.logger.error(f"データクリーンアップエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def backup_database(self, backup_path: str) -> dict:
        """
        データベースをバックアップ
        
        Args:
            backup_path: バックアップファイルパス
            
        Returns:
            バックアップ結果
        """
        try:
            success = self.database.backup_database(backup_path)
            
            result = {
                'success': success,
                'backup_path': backup_path
            }
            
            if success:
                self.logger.info(f"データベースバックアップ完了: {backup_path}")
            else:
                self.logger.error("データベースバックアップ失敗")
            
            return result
            
        except Exception as e:
            self.logger.error(f"データベースバックアップエラー: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def close(self):
        """リソースを解放"""
        if self.scraper:
            self.scraper.close()
        
        self.logger.info("TikTok自動リサーチシステムを終了しました")


def create_cli_parser():
    """CLIパーサーを作成"""
    parser = argparse.ArgumentParser(
        description="TikTok自動リサーチシステム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # トレンド動画を100件収集
  python -m src.main collect --count 100
  
  # 50万再生以上の動画を検索
  python -m src.main search --min-views 500000
  
  # 統計情報を表示
  python -m src.main stats
  
  # 接続テスト
  python -m src.main test
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='設定ファイルパス'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='実行コマンド')
    
    # collect コマンド
    collect_parser = subparsers.add_parser('collect', help='トレンド動画を収集')
    collect_parser.add_argument('--count', type=int, default=100, help='目標収集数')
    collect_parser.add_argument('--min-views', type=int, default=500000, help='最小再生数')
    collect_parser.add_argument('--hours', type=int, default=24, help='何時間前から')
    
    # search コマンド
    search_parser = subparsers.add_parser('search', help='動画を検索')
    search_parser.add_argument('--min-views', type=int, help='最小再生数')
    search_parser.add_argument('--hours', type=int, help='何時間前から')
    search_parser.add_argument('--author', type=str, help='作成者ユーザー名')
    search_parser.add_argument('--limit', type=int, default=100, help='取得件数制限')
    
    # stats コマンド
    subparsers.add_parser('stats', help='統計情報を表示')
    
    # test コマンド
    subparsers.add_parser('test', help='接続テスト')
    
    # cleanup コマンド
    cleanup_parser = subparsers.add_parser('cleanup', help='古いデータを削除')
    cleanup_parser.add_argument('--days', type=int, default=30, help='保持日数')
    
    # backup コマンド
    backup_parser = subparsers.add_parser('backup', help='データベースをバックアップ')
    backup_parser.add_argument('path', help='バックアップファイルパス')
    
    return parser


def main():
    """メイン関数"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # アプリケーションを初期化
    app = TikTokResearchApp(config_path=args.config)
    
    try:
        if args.command == 'collect':
            result = app.collect_trending_videos(
                target_count=args.count,
                min_views=args.min_views,
                hours_ago=args.hours
            )
        
        elif args.command == 'search':
            result = app.search_videos(
                min_views=args.min_views,
                hours_ago=args.hours,
                author_username=args.author,
                limit=args.limit
            )
        
        elif args.command == 'stats':
            result = app.get_statistics()
        
        elif args.command == 'test':
            result = app.test_connection()
        
        elif args.command == 'cleanup':
            result = app.cleanup_old_data(days=args.days)
        
        elif args.command == 'backup':
            result = app.backup_database(backup_path=args.path)
        
        else:
            print(f"不明なコマンド: {args.command}")
            return
        
        # 結果を出力
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 終了コード
        sys.exit(0 if result.get('success', False) else 1)
        
    except KeyboardInterrupt:
        print("\n処理を中断しました")
        sys.exit(1)
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)
    
    finally:
        app.close()


if __name__ == '__main__':
    main()

