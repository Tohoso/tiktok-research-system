"""
Individual video detail scraper for TikTok Research System
"""

import re
import json
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup

from ..utils.logger import get_logger
from ..utils.user_agents import UserAgentManager
from ..utils.proxy_manager import ProxyManager
from ..utils.request_throttle import RequestThrottle
from .scraperapi_client import ScraperAPIClient
from ..parser.video_data import VideoData


class VideoDetailScraper:
    """個別動画ページからの詳細情報取得クラス"""
    
    def __init__(self, api_key: str):
        self.logger = get_logger(self.__class__.__name__)
        self.api_client = ScraperAPIClient(api_key)
        self.proxy_manager = ProxyManager()
        self.throttle = RequestThrottle()
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'videos_with_details': 0,
            'videos_without_details': 0
        }
    
    def get_video_details(self, video_url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        個別動画ページから詳細情報を取得
        
        Args:
            video_url: 動画URL
            max_retries: 最大リトライ回数
            
        Returns:
            動画詳細情報の辞書、失敗時はNone
        """
        self.logger.info(f"動画詳細情報を取得: {video_url}")
        
        for attempt in range(max_retries):
            try:
                # リクエスト制御
                self.throttle.wait_if_needed()
                
                # User-Agentとプロキシを選択
                user_agent = UserAgentManager.get_random_tiktok_agent()
                proxy = self.proxy_manager.get_next_proxy()
                
                # ScraperAPIでページを取得
                custom_params = {}
                
                if proxy:
                    # ProxyConfigオブジェクトから適切にパラメータを取得
                    if hasattr(proxy, 'country') and proxy.country:
                        custom_params['country_code'] = proxy.country
                    
                    # ScraperAPI用の追加パラメータ
                    custom_params.update({
                        'premium': True,
                        'session_number': random.randint(1, 1000),
                        'keep_headers': True
                    })
                
                self.stats['total_requests'] += 1
                
                response = self.api_client.scrape(
                    url=video_url,
                    render_js=True,
                    **custom_params
                )
                
                if response and response.get('status_code') == 200:
                    html_content = response.get('content', '')
                    
                    if html_content and len(html_content) > 1000:  # 最小サイズチェック
                        details = self._extract_video_details(html_content, video_url)
                        
                        if details:
                            self.stats['successful_requests'] += 1
                            self.stats['videos_with_details'] += 1
                            self.logger.info(f"詳細情報取得成功: {video_url}")
                            return details
                        else:
                            self.stats['videos_without_details'] += 1
                            self.logger.warning(f"詳細情報の抽出に失敗: {video_url}")
                    else:
                        self.logger.warning(f"コンテンツが不十分: {video_url} (サイズ: {len(html_content)})")
                else:
                    self.logger.warning(f"HTTP エラー: {response.get('status_code')} - {video_url}")
                
                # リトライ前の待機
                if attempt < max_retries - 1:
                    wait_time = random.uniform(5, 15)
                    self.logger.info(f"リトライ前待機: {wait_time:.1f}秒")
                    time.sleep(wait_time)
                
            except Exception as e:
                self.logger.error(f"動画詳細取得エラー (試行 {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = random.uniform(10, 20)
                    time.sleep(wait_time)
        
        self.stats['failed_requests'] += 1
        self.logger.error(f"動画詳細取得失敗: {video_url}")
        return None
    
    def _extract_video_details(self, html_content: str, video_url: str) -> Optional[Dict[str, Any]]:
        """
        HTMLコンテンツから動画詳細情報を抽出
        
        Args:
            html_content: HTMLコンテンツ
            video_url: 動画URL
            
        Returns:
            動画詳細情報の辞書
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            details = {}
            
            # 動画IDを抽出
            video_id_match = re.search(r'/video/(\d+)', video_url)
            if video_id_match:
                details['video_id'] = video_id_match.group(1)
            
            # 方法1: JSON-LD構造化データから抽出
            json_ld_data = self._extract_from_json_ld(soup)
            if json_ld_data:
                details.update(json_ld_data)
            
            # 方法2: SIGI_STATE（TikTokの内部状態）から抽出
            sigi_data = self._extract_from_sigi_state(html_content)
            if sigi_data:
                details.update(sigi_data)
            
            # 方法3: メタタグから抽出
            meta_data = self._extract_from_meta_tags(soup)
            if meta_data:
                details.update(meta_data)
            
            # 方法4: HTMLテキストから統計情報を抽出
            text_data = self._extract_from_text_content(soup)
            if text_data:
                details.update(text_data)
            
            # 方法5: data-e2e属性から抽出
            e2e_data = self._extract_from_e2e_attributes(soup)
            if e2e_data:
                details.update(e2e_data)
            
            # 基本情報の補完
            details['url'] = video_url
            details['scraped_at'] = datetime.now().isoformat()
            
            # 詳細情報が取得できたかチェック
            has_details = any([
                details.get('view_count'),
                details.get('like_count'),
                details.get('create_time'),
                details.get('author_username')
            ])
            
            if has_details:
                self.logger.debug(f"抽出された詳細情報: {details}")
                return details
            else:
                self.logger.warning("有効な詳細情報が見つかりませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"詳細情報抽出エラー: {e}")
            return None
    
    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """JSON-LD構造化データから情報を抽出"""
        details = {}
        
        try:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        
                        if isinstance(data, dict):
                            # VideoObjectタイプをチェック
                            if data.get('@type') == 'VideoObject':
                                details.update(self._parse_video_object(data))
                            
                            # その他の構造化データ
                            if 'interactionStatistic' in data:
                                details.update(self._parse_interaction_stats(data['interactionStatistic']))
                        
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.logger.warning(f"JSON-LD抽出エラー: {e}")
        
        return details
    
    def _extract_from_sigi_state(self, html_content: str) -> Dict[str, Any]:
        """SIGI_STATE（TikTokの内部状態）から情報を抽出"""
        details = {}
        
        try:
            # SIGI_STATEパターンを検索
            sigi_pattern = r'window\[\'SIGI_STATE\'\]\s*=\s*({.+?});'
            sigi_match = re.search(sigi_pattern, html_content, re.DOTALL)
            
            if sigi_match:
                try:
                    sigi_data = json.loads(sigi_match.group(1))
                    
                    # ItemModuleから動画情報を抽出
                    if 'ItemModule' in sigi_data:
                        item_module = sigi_data['ItemModule']
                        for video_id, video_data in item_module.items():
                            if isinstance(video_data, dict):
                                details.update(self._parse_item_module_data(video_data))
                                break  # 最初の動画データを使用
                    
                    # UserModuleから作者情報を抽出
                    if 'UserModule' in sigi_data:
                        user_module = sigi_data['UserModule']
                        if 'users' in user_module:
                            for user_id, user_data in user_module['users'].items():
                                if isinstance(user_data, dict):
                                    details.update(self._parse_user_module_data(user_data))
                                    break  # 最初のユーザーデータを使用
                
                except json.JSONDecodeError as e:
                    self.logger.warning(f"SIGI_STATE JSON解析エラー: {e}")
        
        except Exception as e:
            self.logger.warning(f"SIGI_STATE抽出エラー: {e}")
        
        return details
    
    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """メタタグから情報を抽出"""
        details = {}
        
        try:
            # Open Graphメタタグ
            og_tags = {
                'og:title': 'title',
                'og:description': 'description',
                'og:image': 'thumbnail_url',
                'og:video': 'video_url'
            }
            
            for og_property, detail_key in og_tags.items():
                meta_tag = soup.find('meta', property=og_property)
                if meta_tag and meta_tag.get('content'):
                    details[detail_key] = meta_tag['content']
            
            # Twitterカードメタタグ
            twitter_tags = {
                'twitter:title': 'title',
                'twitter:description': 'description',
                'twitter:image': 'thumbnail_url'
            }
            
            for twitter_name, detail_key in twitter_tags.items():
                meta_tag = soup.find('meta', attrs={'name': twitter_name})
                if meta_tag and meta_tag.get('content'):
                    if detail_key not in details:  # OGタグを優先
                        details[detail_key] = meta_tag['content']
        
        except Exception as e:
            self.logger.warning(f"メタタグ抽出エラー: {e}")
        
        return details
    
    def _extract_from_text_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """HTMLテキストコンテンツから統計情報を抽出"""
        details = {}
        
        try:
            text_content = soup.get_text()
            
            # 再生数パターン
            view_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生|回再生)',
                r'(\d+(?:,\d+)*)\s*(?:views?|再生)',
            ]
            
            for pattern in view_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    details['view_count'] = self._parse_count_string(match.group(1))
                    break
            
            # いいね数パターン
            like_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね)',
                r'♥\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    details['like_count'] = self._parse_count_string(match.group(1))
                    break
            
            # コメント数パターン
            comment_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:comments?|コメント)',
            ]
            
            for pattern in comment_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    details['comment_count'] = self._parse_count_string(match.group(1))
                    break
            
            # シェア数パターン
            share_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:shares?|シェア)',
            ]
            
            for pattern in share_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    details['share_count'] = self._parse_count_string(match.group(1))
                    break
        
        except Exception as e:
            self.logger.warning(f"テキストコンテンツ抽出エラー: {e}")
        
        return details
    
    def _extract_from_e2e_attributes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """data-e2e属性から情報を抽出"""
        details = {}
        
        try:
            # 統計情報のdata-e2e属性
            e2e_mappings = {
                'like-count': 'like_count',
                'comment-count': 'comment_count',
                'share-count': 'share_count',
                'video-views': 'view_count'
            }
            
            for e2e_value, detail_key in e2e_mappings.items():
                element = soup.find(attrs={'data-e2e': e2e_value})
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        count = self._parse_count_string(text)
                        if count is not None:
                            details[detail_key] = count
        
        except Exception as e:
            self.logger.warning(f"data-e2e属性抽出エラー: {e}")
        
        return details
    
    def _parse_video_object(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """VideoObjectデータを解析"""
        details = {}
        
        try:
            if 'name' in data:
                details['title'] = data['name']
            if 'description' in data:
                details['description'] = data['description']
            if 'uploadDate' in data:
                details['create_time'] = data['uploadDate']
            if 'thumbnailUrl' in data:
                details['thumbnail_url'] = data['thumbnailUrl']
            if 'contentUrl' in data:
                details['video_url'] = data['contentUrl']
        
        except Exception as e:
            self.logger.warning(f"VideoObject解析エラー: {e}")
        
        return details
    
    def _parse_interaction_stats(self, stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """インタラクション統計を解析"""
        details = {}
        
        try:
            for stat in stats:
                interaction_type = stat.get('interactionType', {}).get('@type', '')
                user_interaction_count = stat.get('userInteractionCount')
                
                if interaction_type == 'LikeAction' and user_interaction_count:
                    details['like_count'] = int(user_interaction_count)
                elif interaction_type == 'CommentAction' and user_interaction_count:
                    details['comment_count'] = int(user_interaction_count)
                elif interaction_type == 'ShareAction' and user_interaction_count:
                    details['share_count'] = int(user_interaction_count)
        
        except Exception as e:
            self.logger.warning(f"インタラクション統計解析エラー: {e}")
        
        return details
    
    def _parse_item_module_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ItemModuleデータを解析"""
        details = {}
        
        try:
            if 'desc' in data:
                details['description'] = data['desc']
            if 'createTime' in data:
                details['create_time'] = data['createTime']
            
            # 統計情報
            if 'stats' in data:
                stats = data['stats']
                if 'playCount' in stats:
                    details['view_count'] = stats['playCount']
                if 'diggCount' in stats:
                    details['like_count'] = stats['diggCount']
                if 'commentCount' in stats:
                    details['comment_count'] = stats['commentCount']
                if 'shareCount' in stats:
                    details['share_count'] = stats['shareCount']
            
            # 作者情報
            if 'author' in data:
                author = data['author']
                if 'uniqueId' in author:
                    details['author_username'] = author['uniqueId']
                if 'nickname' in author:
                    details['author_display_name'] = author['nickname']
                if 'verified' in author:
                    details['author_verified'] = author['verified']
        
        except Exception as e:
            self.logger.warning(f"ItemModule解析エラー: {e}")
        
        return details
    
    def _parse_user_module_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """UserModuleデータを解析"""
        details = {}
        
        try:
            if 'uniqueId' in data:
                details['author_username'] = data['uniqueId']
            if 'nickname' in data:
                details['author_display_name'] = data['nickname']
            if 'verified' in data:
                details['author_verified'] = data['verified']
            if 'followerCount' in data:
                details['author_follower_count'] = data['followerCount']
        
        except Exception as e:
            self.logger.warning(f"UserModule解析エラー: {e}")
        
        return details
    
    def _parse_count_string(self, count_str: str) -> Optional[int]:
        """カウント文字列を数値に変換"""
        try:
            count_str = count_str.upper().strip().replace(',', '')
            
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
    
    def get_multiple_video_details(
        self,
        video_urls: List[str],
        max_concurrent: int = 3,
        delay_between_requests: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        複数の動画の詳細情報を取得
        
        Args:
            video_urls: 動画URLのリスト
            max_concurrent: 最大同時実行数
            delay_between_requests: リクエスト間の遅延（秒）
            
        Returns:
            動画詳細情報のリスト
        """
        self.logger.info(f"複数動画の詳細情報取得開始: {len(video_urls)}件")
        
        results = []
        
        for i, url in enumerate(video_urls):
            self.logger.info(f"進捗: {i + 1}/{len(video_urls)} - {url}")
            
            details = self.get_video_details(url)
            if details:
                results.append(details)
            
            # リクエスト間の遅延
            if i < len(video_urls) - 1:
                time.sleep(delay_between_requests)
        
        self.logger.info(f"複数動画詳細取得完了: {len(results)}/{len(video_urls)}件成功")
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        success_rate = 0.0
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'proxy_stats': self.proxy_manager.get_statistics(),
            'throttle_stats': self.throttle.get_statistics()
        }

