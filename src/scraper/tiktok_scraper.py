"""
TikTok scraper for TikTok Research System
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..utils.logger import get_logger, PerformanceLogger
from ..utils.config import config
from ..utils.helpers import retry_on_exception
# from ..parser.tiktok_parser import TikTokParser  # 循環インポート回避
from ..parser.video_data import VideoData, VideoCollection
from .scraperapi_client import ScraperAPIClient
from .exceptions import ScraperError, APIError, RateLimitError


class TikTokScraper:
    """TikTok動画スクレイパー"""
    
    def __init__(self, api_client: Optional[ScraperAPIClient] = None):
        """
        TikTokスクレイパーを初期化
        
        Args:
            api_client: ScraperAPIクライアント（省略時は設定から作成）
        """
        self.logger = get_logger(self.__class__.__name__)
        self.performance_logger = PerformanceLogger(self.logger)
        
        # APIクライアントの初期化
        if api_client:
            self.api_client = api_client
        else:
            scraper_config = config.get_scraper_config()
            self.api_client = ScraperAPIClient(
                api_key=scraper_config.get('api_key'),
                base_url=scraper_config.get('base_url'),
                timeout=scraper_config.get('timeout', 60),
                max_retries=scraper_config.get('max_retries', 3),
            )
        
        # パーサーの遅延初期化（循環インポート回避）
        self._parser = None
        
        # 統計情報
        self.stats = {
            'requests_made': 0,
            'videos_found': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    @property
    def parser(self):
        """パーサーの遅延初期化"""
        if self._parser is None:
            from ..parser.tiktok_parser import TikTokParser
            self._parser = TikTokParser()
        return self._parser
    
    @retry_on_exception(max_retries=3, delay=2.0)
    def scrape_explore_page(
        self,
        country_code: str = None,
        render_js: bool = True,
        device_type: str = "desktop"
    ) -> VideoCollection:
        """
        TikTok /exploreページをスクレイピング
        
        Args:
            country_code: 国コード（デフォルト: 設定値）
            render_js: JavaScript実行を有効にするか
            device_type: デバイスタイプ
            
        Returns:
            動画データコレクション
            
        Raises:
            ScraperError: スクレイピングエラー
        """
        self.performance_logger.start("explore_page_scraping")
        
        try:
            # パラメータの設定
            country_code = country_code or self.tiktok_config.get('country_code', 'JP')
            
            self.logger.info(f"TikTok /exploreページのスクレイピングを開始 (国: {country_code})")
            
            # スクレイピング実行
            result = self.api_client.scrape_tiktok_explore(
                country_code=country_code,
                render_js=render_js,
                device_type=device_type
            )
            
            if not result.get('success'):
                raise ScraperError("スクレイピングが失敗しました")
            
            # HTMLコンテンツを取得
            html_content = result.get('content', '')
            if not html_content:
                raise ScraperError("HTMLコンテンツが空です")
            
            self.logger.info(f"HTMLコンテンツを取得 (サイズ: {len(html_content)} 文字)")
            
            # HTMLを解析
            video_collection = self.parser.parse_explore_page(html_content)
            
            self.performance_logger.end("explore_page_scraping")
            
            self.logger.info(f"動画データ {len(video_collection)} 件を取得完了")
            return video_collection
            
        except (APIError, RateLimitError) as e:
            self.logger.error(f"API エラー: {e}")
            raise
        except Exception as e:
            self.logger.error(f"スクレイピングエラー: {e}")
            raise ScraperError(f"スクレイピングに失敗: {e}")
    
    def scrape_video_details(self, video_urls: List[str]) -> List[VideoData]:
        """
        個別動画の詳細情報をスクレイピング
        
        Args:
            video_urls: 動画URLのリスト
            
        Returns:
            詳細動画データのリスト
        """
        self.performance_logger.start("video_details_scraping")
        
        detailed_videos = []
        
        for i, url in enumerate(video_urls):
            try:
                self.logger.info(f"動画詳細取得中 ({i+1}/{len(video_urls)}): {url}")
                
                # レート制限対応
                if i > 0:
                    time.sleep(self.api_client.rate_limit_delay)
                
                # 個別動画ページをスクレイピング
                result = self.api_client.scrape(
                    url=url,
                    render_js=True,
                    country_code=self.tiktok_config.get('country_code', 'JP'),
                    premium=True
                )
                
                if result.get('success'):
                    html_content = result.get('content', '')
                    video_data = self.parser.parse_video_page(html_content, url)
                    
                    if video_data:
                        detailed_videos.append(video_data)
                        self.logger.debug(f"動画詳細取得成功: {url}")
                    else:
                        self.logger.warning(f"動画詳細解析失敗: {url}")
                else:
                    self.logger.warning(f"動画詳細スクレイピング失敗: {url}")
                    
            except Exception as e:
                self.logger.error(f"動画詳細取得エラー ({url}): {e}")
                continue
        
        self.performance_logger.end("video_details_scraping")
        
        self.logger.info(f"動画詳細 {len(detailed_videos)}/{len(video_urls)} 件を取得完了")
        return detailed_videos
    
    def filter_videos(self, video_collection: VideoCollection) -> VideoCollection:
        """
        動画データをフィルタリング
        
        Args:
            video_collection: 動画データコレクション
            
        Returns:
            フィルタリング済み動画データコレクション
        """
        self.logger.info("動画データのフィルタリングを開始")
        
        # 設定値を取得
        min_views = self.filter_config.get('min_views', 500000)
        time_range_hours = self.filter_config.get('time_range_hours', 24)
        
        # 再生数でフィルタリング
        filtered_by_views = video_collection.filter_by_views(min_views)
        self.logger.info(f"再生数フィルタリング: {len(video_collection)} → {len(filtered_by_views)} 件")
        
        # 投稿日時でフィルタリング
        filtered_by_date = filtered_by_views.filter_by_date(time_range_hours)
        self.logger.info(f"日時フィルタリング: {len(filtered_by_views)} → {len(filtered_by_date)} 件")
        
        # 重複除去
        if self.filter_config.get('exclude_duplicates', True):
            unique_videos = self._remove_duplicates(filtered_by_date.videos)
            filtered_by_date.videos = unique_videos
            filtered_by_date.total_count = len(unique_videos)
            self.logger.info(f"重複除去後: {len(unique_videos)} 件")
        
        return filtered_by_date
    
    def _remove_duplicates(self, videos: List[VideoData]) -> List[VideoData]:
        """重複する動画を除去"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            if video.video_id not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video.video_id)
        
        return unique_videos
    
    def collect_trending_videos(
        self,
        target_count: int = 100,
        max_attempts: int = 5
    ) -> VideoCollection:
        """
        トレンド動画を収集
        
        Args:
            target_count: 目標収集数
            max_attempts: 最大試行回数
            
        Returns:
            収集された動画データコレクション
        """
        self.performance_logger.start("trending_videos_collection")
        
        all_videos = []
        attempt = 0
        
        while len(all_videos) < target_count and attempt < max_attempts:
            attempt += 1
            
            try:
                self.logger.info(f"トレンド動画収集 (試行 {attempt}/{max_attempts})")
                
                # /exploreページをスクレイピング
                video_collection = self.scrape_explore_page()
                
                # フィルタリング
                filtered_collection = self.filter_videos(video_collection)
                
                # 新しい動画のみを追加
                new_videos = []
                existing_ids = {v.video_id for v in all_videos}
                
                for video in filtered_collection.videos:
                    if video.video_id not in existing_ids:
                        new_videos.append(video)
                        existing_ids.add(video.video_id)
                
                all_videos.extend(new_videos)
                
                self.logger.info(f"新規動画 {len(new_videos)} 件を追加 (合計: {len(all_videos)} 件)")
                
                # 目標達成チェック
                if len(all_videos) >= target_count:
                    break
                
                # 次の試行まで待機
                if attempt < max_attempts:
                    wait_time = 30  # 30秒待機
                    self.logger.info(f"次の試行まで {wait_time} 秒待機")
                    time.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"トレンド動画収集エラー (試行 {attempt}): {e}")
                
                if attempt < max_attempts:
                    wait_time = 60  # エラー時は60秒待機
                    self.logger.info(f"エラー後の待機: {wait_time} 秒")
                    time.sleep(wait_time)
        
        # 最終結果
        result_collection = VideoCollection(
            videos=all_videos[:target_count],  # 目標数まで切り詰め
            source="trending_collection",
            total_count=len(all_videos[:target_count])
        )
        
        self.performance_logger.end("trending_videos_collection")
        
        self.logger.info(f"トレンド動画収集完了: {len(result_collection)} 件")
        return result_collection
    
    def test_connection(self) -> bool:
        """
        接続テスト
        
        Returns:
            接続成功かどうか
        """
        try:
            self.logger.info("接続テストを実行")
            success = self.api_client.test_connection()
            
            if success:
                self.logger.info("接続テスト成功")
            else:
                self.logger.error("接続テスト失敗")
            
            return success
            
        except Exception as e:
            self.logger.error(f"接続テストエラー: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        システム状態を取得
        
        Returns:
            システム状態情報
        """
        try:
            # アカウント情報を取得
            account_info = self.api_client.get_account_info()
            
            # 設定情報
            config_info = {
                'country_code': self.tiktok_config.get('country_code'),
                'min_views': self.filter_config.get('min_views'),
                'time_range_hours': self.filter_config.get('time_range_hours')
            }
            
            # パフォーマンス情報
            performance_info = {
                'metrics': self.performance_logger.metrics
            }
            
            return {
                'status': 'active',
                'account': account_info,
                'config': config_info,
                'performance': performance_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"システム状態取得エラー: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close(self):
        """リソースを解放"""
        if self.api_client:
            self.api_client.close()
        
        # パフォーマンスメトリクスをログ出力
        self.performance_logger.log_metrics()
        
        self.logger.info("TikTokスクレイパーを終了しました")

