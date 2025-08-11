"""
JavaScript実行機能付きTikTokスクレイパー
"""

import time
import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.config import config
from .scraperapi_client import ScraperAPIClient
from .exceptions import ScraperError, APIError


class JavaScriptScraper:
    """JavaScript実行機能付きスクレイパー"""
    
    def __init__(self, api_client: Optional[ScraperAPIClient] = None):
        """
        JavaScript実行機能付きスクレイパーを初期化
        
        Args:
            api_client: ScraperAPIクライアント
        """
        self.logger = get_logger(self.__class__.__name__)
        
        # APIクライアントの初期化
        if api_client:
            self.api_client = api_client
        else:
            scraper_config = config.get_scraper_config()
            self.api_client = ScraperAPIClient(
                api_key=scraper_config.get('api_key'),
                base_url=scraper_config.get('base_url'),
                timeout=scraper_config.get('timeout', 120),  # JavaScript実行のため長めに設定
                max_retries=scraper_config.get('max_retries', 3),
            )
    
    def scrape_with_javascript(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        wait_time: int = 10,
        execute_script: Optional[str] = None,
        country_code: str = "JP"
    ) -> Dict[str, Any]:
        """
        JavaScript実行機能付きでページをスクレイピング
        
        Args:
            url: スクレイピング対象URL
            wait_for_selector: 待機するCSSセレクター
            wait_time: 待機時間（秒）
            execute_script: 実行するJavaScriptコード
            country_code: 国コード
            
        Returns:
            スクレイピング結果
        """
        self.logger.info(f"JavaScript実行機能付きスクレイピング開始: {url}")
        
        try:
            # ScraperAPIのJavaScript実行機能を使用
            params = {
                'render': 'true',  # JavaScript実行を有効化
                'wait_for': wait_for_selector or 'body',  # 待機するセレクター
                'wait': wait_time,  # 待機時間
                'country_code': country_code,
                'premium': 'true',  # プレミアム機能を使用
                'session_number': 1,  # セッション番号
            }
            
            # カスタムJavaScriptの実行
            if execute_script:
                params['execute'] = execute_script
            
            # リクエスト実行
            response = self.api_client.scrape(url, params)
            
            if response.get('success'):
                self.logger.info(f"JavaScript実行完了: {len(response.get('content', ''))} 文字")
                return {
                    'success': True,
                    'content': response.get('content', ''),
                    'status_code': response.get('status_code', 200),
                    'response_time': response.get('response_time', 0),
                    'javascript_executed': True
                }
            else:
                error_msg = response.get('error', 'Unknown error')
                self.logger.error(f"JavaScript実行エラー: {error_msg}")
                raise APIError(f"JavaScript実行失敗: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"JavaScript実行機能付きスクレイピングエラー: {e}")
            raise ScraperError(f"JavaScript実行機能付きスクレイピング失敗: {e}")
    
    def scrape_tiktok_explore_with_js(self) -> Dict[str, Any]:
        """
        TikTok /exploreページをJavaScript実行機能付きでスクレイピング
        
        Returns:
            スクレイピング結果
        """
        self.logger.info("TikTok /exploreページのJavaScript実行機能付きスクレイピング開始")
        
        # TikTok用のJavaScriptコード
        tiktok_script = """
        // TikTokの動的コンテンツを待機
        function waitForTikTokContent() {
            return new Promise((resolve) => {
                let attempts = 0;
                const maxAttempts = 30;
                
                function checkContent() {
                    attempts++;
                    
                    // 動画要素を検索
                    const videoElements = document.querySelectorAll('[data-e2e="recommend-list-item"]');
                    const videoLinks = document.querySelectorAll('a[href*="/video/"]');
                    
                    if (videoElements.length > 0 || videoLinks.length > 0 || attempts >= maxAttempts) {
                        resolve({
                            videoElements: videoElements.length,
                            videoLinks: videoLinks.length,
                            totalAttempts: attempts
                        });
                    } else {
                        setTimeout(checkContent, 1000);
                    }
                }
                
                checkContent();
            });
        }
        
        // スクロールして追加コンテンツを読み込み
        function scrollAndLoad() {
            return new Promise((resolve) => {
                let scrollCount = 0;
                const maxScrolls = 5;
                
                function scroll() {
                    if (scrollCount < maxScrolls) {
                        window.scrollTo(0, document.body.scrollHeight);
                        scrollCount++;
                        setTimeout(scroll, 2000);
                    } else {
                        resolve(scrollCount);
                    }
                }
                
                scroll();
            });
        }
        
        // メイン処理
        async function main() {
            console.log('TikTok JavaScript処理開始');
            
            // コンテンツの待機
            const contentResult = await waitForTikTokContent();
            console.log('コンテンツ検出:', contentResult);
            
            // スクロールして追加読み込み
            const scrollResult = await scrollAndLoad();
            console.log('スクロール完了:', scrollResult);
            
            // 最終的な動画データを収集
            const finalVideoElements = document.querySelectorAll('[data-e2e="recommend-list-item"]');
            const finalVideoLinks = document.querySelectorAll('a[href*="/video/"]');
            
            return {
                success: true,
                videoElements: finalVideoElements.length,
                videoLinks: finalVideoLinks.length,
                contentWaitResult: contentResult,
                scrollResult: scrollResult
            };
        }
        
        return main();
        """
        
        try:
            result = self.scrape_with_javascript(
                url="https://www.tiktok.com/explore",
                wait_for_selector='[data-e2e="recommend-list-item"], a[href*="/video/"]',
                wait_time=15,
                execute_script=tiktok_script,
                country_code="JP"
            )
            
            self.logger.info("TikTok /exploreページのJavaScript実行完了")
            return result
            
        except Exception as e:
            self.logger.error(f"TikTok /exploreページJavaScript実行エラー: {e}")
            raise
    
    def extract_video_data_from_js_content(self, html_content: str) -> List[Dict[str, Any]]:
        """
        JavaScript実行後のHTMLコンテンツから動画データを抽出
        
        Args:
            html_content: JavaScript実行後のHTMLコンテンツ
            
        Returns:
            動画データリスト
        """
        self.logger.info("JavaScript実行後のコンテンツから動画データを抽出開始")
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            videos = []
            
            # 方法1: data-e2e属性を持つ要素から抽出
            video_elements = soup.find_all(attrs={'data-e2e': 'recommend-list-item'})
            self.logger.info(f"recommend-list-item要素: {len(video_elements)}件")
            
            for element in video_elements:
                video_data = self._extract_from_recommend_item(element)
                if video_data:
                    videos.append(video_data)
            
            # 方法2: 動画リンクから抽出
            video_links = soup.find_all('a', href=re.compile(r'/video/\d+'))
            self.logger.info(f"動画リンク: {len(video_links)}件")
            
            for link in video_links:
                video_data = self._extract_from_video_link(link)
                if video_data:
                    videos.append(video_data)
            
            # 方法3: JavaScriptデータから抽出
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    data = json.loads(script.string or '{}')
                    script_videos = self._extract_from_script_data(data)
                    videos.extend(script_videos)
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # 重複除去
            unique_videos = self._remove_duplicate_videos(videos)
            
            self.logger.info(f"JavaScript実行後のコンテンツから {len(unique_videos)} 件の動画データを抽出")
            return unique_videos
            
        except Exception as e:
            self.logger.error(f"JavaScript実行後のコンテンツ解析エラー: {e}")
            return []
    
    def _extract_from_recommend_item(self, element) -> Optional[Dict[str, Any]]:
        """recommend-list-item要素から動画データを抽出"""
        try:
            # 動画リンクを検索
            link = element.find('a', href=True)
            if not link:
                return None
            
            href = link['href']
            
            # 動画IDを抽出
            video_id_match = re.search(r'/video/(\d+)', href)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            
            # 作者情報を抽出
            author_link = element.find('a', href=re.compile(r'/@[\w.-]+'))
            author_username = ''
            if author_link:
                author_match = re.search(r'/@([\w.-]+)', author_link['href'])
                if author_match:
                    author_username = author_match.group(1)
            
            # テキストコンテンツを抽出
            text_content = element.get_text(strip=True)
            
            # 統計情報を抽出（可能であれば）
            stats = self._extract_stats_from_element(element)
            
            return {
                'video_id': video_id,
                'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
                'author_username': author_username,
                'text_content': text_content,
                'stats': stats,
                'extraction_method': 'recommend_item'
            }
            
        except Exception as e:
            self.logger.warning(f"recommend-list-item要素解析エラー: {e}")
            return None
    
    def _extract_from_video_link(self, link) -> Optional[Dict[str, Any]]:
        """動画リンクから動画データを抽出"""
        try:
            href = link['href']
            
            # 動画IDを抽出
            video_id_match = re.search(r'/video/(\d+)', href)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            
            # 親要素から追加情報を抽出
            parent = link.parent
            text_content = parent.get_text(strip=True) if parent else ''
            
            return {
                'video_id': video_id,
                'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
                'text_content': text_content,
                'extraction_method': 'video_link'
            }
            
        except Exception as e:
            self.logger.warning(f"動画リンク解析エラー: {e}")
            return None
    
    def _extract_from_script_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """JavaScriptデータから動画データを抽出"""
        videos = []
        
        try:
            # TikTokの一般的なデータ構造を検索
            def search_video_data(obj, path=""):
                if isinstance(obj, dict):
                    # 動画データの可能性があるキーを検索
                    for key, value in obj.items():
                        if key in ['itemList', 'items', 'videoList', 'videos', 'data']:
                            if isinstance(value, list):
                                for item in value:
                                    if self._is_video_item(item):
                                        video_data = self._extract_video_from_item(item)
                                        if video_data:
                                            videos.append(video_data)
                        else:
                            search_video_data(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_video_data(item, f"{path}[{i}]")
            
            search_video_data(data)
            
        except Exception as e:
            self.logger.warning(f"JavaScriptデータ解析エラー: {e}")
        
        return videos
    
    def _is_video_item(self, item: Any) -> bool:
        """アイテムが動画データかどうかを判定"""
        if not isinstance(item, dict):
            return False
        
        # 動画データの特徴的なキーをチェック
        video_keys = ['id', 'aweme_id', 'video_id', 'desc', 'author', 'stats']
        return any(key in item for key in video_keys)
    
    def _extract_video_from_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """動画アイテムから動画データを抽出"""
        try:
            video_id = item.get('id') or item.get('aweme_id') or item.get('video_id')
            if not video_id:
                return None
            
            author = item.get('author', {})
            stats = item.get('stats', {})
            
            return {
                'video_id': str(video_id),
                'url': f"https://www.tiktok.com/@{author.get('unique_id', 'unknown')}/video/{video_id}",
                'description': item.get('desc', ''),
                'author_username': author.get('unique_id', ''),
                'author_display_name': author.get('nickname', ''),
                'view_count': stats.get('play_count'),
                'like_count': stats.get('digg_count'),
                'comment_count': stats.get('comment_count'),
                'share_count': stats.get('share_count'),
                'create_time': item.get('create_time'),
                'extraction_method': 'script_data'
            }
            
        except Exception as e:
            self.logger.warning(f"動画アイテム解析エラー: {e}")
            return None
    
    def _extract_stats_from_element(self, element) -> Dict[str, Any]:
        """要素から統計情報を抽出"""
        stats = {}
        
        try:
            # 数値パターンを検索
            text = element.get_text()
            
            # いいね数のパターン
            like_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね)',
                r'♥\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    stats['like_count'] = self._parse_count_string(match.group(1))
                    break
            
            # 再生数のパターン
            view_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生)',
                r'👁\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in view_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    stats['view_count'] = self._parse_count_string(match.group(1))
                    break
            
        except Exception as e:
            self.logger.warning(f"統計情報抽出エラー: {e}")
        
        return stats
    
    def _parse_count_string(self, count_str: str) -> Optional[int]:
        """カウント文字列を数値に変換"""
        try:
            count_str = count_str.upper().strip()
            
            if count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith('B'):
                return int(float(count_str[:-1]) * 1000000000)
            else:
                return int(float(count_str))
                
        except (ValueError, TypeError):
            return None
    
    def _remove_duplicate_videos(self, videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """重複する動画を除去"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            video_id = video.get('video_id')
            if video_id and video_id not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video_id)
        
        return unique_videos

