#!/usr/bin/env python3
"""
Enhanced Video Detail Scraper for TikTok Research System
再生数、投稿日時、作者情報の抽出を強化
"""

import re
import json
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import get_logger
from src.utils.user_agents import UserAgentManager
from src.utils.proxy_manager import ProxyManager
from src.utils.request_throttle import RequestThrottle
from src.scraper.scraperapi_client import ScraperAPIClient
from src.parser.video_data import VideoData


class EnhancedVideoDetailScraper:
    """改良版個別動画詳細情報取得クラス"""
    
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
            'videos_without_details': 0,
            'view_count_extracted': 0,
            'create_time_extracted': 0,
            'author_extracted': 0
        }
    
    def get_video_details(self, video_url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        個別動画ページから詳細情報を取得（改良版）
        
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
                custom_params = {
                    'premium': True,
                    'session_number': random.randint(1, 1000),
                    'keep_headers': True,
                    'render_js': True  # JavaScript実行を有効化
                }
                
                if proxy and hasattr(proxy, 'country') and proxy.country:
                    custom_params['country_code'] = proxy.country
                
                self.stats['total_requests'] += 1
                
                response = self.api_client.scrape(
                    url=video_url,
                    **custom_params
                )
                
                if response and response.get('status_code') == 200:
                    html_content = response.get('content', '')
                    
                    if html_content and len(html_content) > 1000:  # 最小サイズチェック
                        details = self._extract_video_details_enhanced(html_content, video_url)
                        
                        if details:
                            self.stats['successful_requests'] += 1
                            self.stats['videos_with_details'] += 1
                            
                            # 抽出成功統計
                            if details.get('view_count'):
                                self.stats['view_count_extracted'] += 1
                            if details.get('create_time'):
                                self.stats['create_time_extracted'] += 1
                            if details.get('author_username'):
                                self.stats['author_extracted'] += 1
                            
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
    
    def _extract_video_details_enhanced(self, html_content: str, video_url: str) -> Optional[Dict[str, Any]]:
        """
        HTMLコンテンツから動画詳細情報を抽出（改良版）
        
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
            
            # 方法1: SIGI_STATE（最優先）
            sigi_data = self._extract_from_sigi_state_enhanced(html_content)
            if sigi_data:
                details.update(sigi_data)
                self.logger.debug(f"SIGI_STATE抽出成功: {len(sigi_data)}項目")
            
            # 方法2: __UNIVERSAL_DATA_FOR_REHYDRATION__
            universal_data = self._extract_from_universal_data(html_content)
            if universal_data:
                details.update(universal_data)
                self.logger.debug(f"Universal Data抽出成功: {len(universal_data)}項目")
            
            # 方法3: JSON-LD構造化データ
            json_ld_data = self._extract_from_json_ld_enhanced(soup)
            if json_ld_data:
                details.update(json_ld_data)
                self.logger.debug(f"JSON-LD抽出成功: {len(json_ld_data)}項目")
            
            # 方法4: メタタグ（改良版）
            meta_data = self._extract_from_meta_tags_enhanced(soup)
            if meta_data:
                details.update(meta_data)
                self.logger.debug(f"メタタグ抽出成功: {len(meta_data)}項目")
            
            # 方法5: HTMLテキストから統計情報を抽出（改良版）
            text_data = self._extract_from_text_content_enhanced(soup)
            if text_data:
                details.update(text_data)
                self.logger.debug(f"テキスト抽出成功: {len(text_data)}項目")
            
            # 方法6: data-e2e属性（改良版）
            e2e_data = self._extract_from_e2e_attributes_enhanced(soup)
            if e2e_data:
                details.update(e2e_data)
                self.logger.debug(f"data-e2e抽出成功: {len(e2e_data)}項目")
            
            # 方法7: CSS セレクターによる直接抽出
            css_data = self._extract_from_css_selectors(soup)
            if css_data:
                details.update(css_data)
                self.logger.debug(f"CSS セレクター抽出成功: {len(css_data)}項目")
            
            # 方法8: 正規表現による高度な抽出
            regex_data = self._extract_from_regex_patterns(html_content)
            if regex_data:
                details.update(regex_data)
                self.logger.debug(f"正規表現抽出成功: {len(regex_data)}項目")
            
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
    
    def _extract_from_sigi_state_enhanced(self, html_content: str) -> Dict[str, Any]:
        """SIGI_STATE（TikTokの内部状態）から情報を抽出（改良版）"""
        details = {}
        
        try:
            # 複数のSIGI_STATEパターンを試行
            sigi_patterns = [
                r'window\[\'SIGI_STATE\'\]\s*=\s*({.+?});',
                r'window\.SIGI_STATE\s*=\s*({.+?});',
                r'SIGI_STATE\s*=\s*({.+?});',
                r'"SIGI_STATE":\s*({.+?})',
            ]
            
            for pattern in sigi_patterns:
                sigi_match = re.search(pattern, html_content, re.DOTALL)
                
                if sigi_match:
                    try:
                        sigi_data = json.loads(sigi_match.group(1))
                        
                        # ItemModuleから動画情報を抽出
                        if 'ItemModule' in sigi_data:
                            item_module = sigi_data['ItemModule']
                            for video_id, video_data in item_module.items():
                                if isinstance(video_data, dict):
                                    extracted = self._parse_item_module_data_enhanced(video_data)
                                    details.update(extracted)
                                    if extracted:  # データが見つかったら最初のものを使用
                                        break
                        
                        # UserModuleから作者情報を抽出
                        if 'UserModule' in sigi_data:
                            user_module = sigi_data['UserModule']
                            if 'users' in user_module:
                                for user_id, user_data in user_module['users'].items():
                                    if isinstance(user_data, dict):
                                        extracted = self._parse_user_module_data_enhanced(user_data)
                                        details.update(extracted)
                                        if extracted:  # データが見つかったら最初のものを使用
                                            break
                        
                        # VideoDetailから詳細情報を抽出
                        if 'VideoDetail' in sigi_data:
                            video_detail = sigi_data['VideoDetail']
                            extracted = self._parse_video_detail_data(video_detail)
                            details.update(extracted)
                        
                        if details:  # データが見つかったらループを終了
                            break
                    
                    except json.JSONDecodeError as e:
                        self.logger.debug(f"SIGI_STATE JSON解析エラー (パターン {pattern}): {e}")
                        continue
        
        except Exception as e:
            self.logger.warning(f"SIGI_STATE抽出エラー: {e}")
        
        return details
    
    def _extract_from_universal_data(self, html_content: str) -> Dict[str, Any]:
        """__UNIVERSAL_DATA_FOR_REHYDRATION__から情報を抽出"""
        details = {}
        
        try:
            # Universal Dataパターンを検索
            universal_patterns = [
                r'window\[\'__UNIVERSAL_DATA_FOR_REHYDRATION__\'\]\s*=\s*({.+?});',
                r'__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.+?});',
            ]
            
            for pattern in universal_patterns:
                universal_match = re.search(pattern, html_content, re.DOTALL)
                
                if universal_match:
                    try:
                        universal_data = json.loads(universal_match.group(1))
                        
                        # __DEFAULT_SCOPE__から動画情報を抽出
                        if '__DEFAULT_SCOPE__' in universal_data:
                            default_scope = universal_data['__DEFAULT_SCOPE__']
                            
                            # webapp.video-detailから詳細情報を抽出
                            if 'webapp.video-detail' in default_scope:
                                video_detail = default_scope['webapp.video-detail']
                                extracted = self._parse_webapp_video_detail(video_detail)
                                details.update(extracted)
                        
                        if details:  # データが見つかったらループを終了
                            break
                    
                    except json.JSONDecodeError as e:
                        self.logger.debug(f"Universal Data JSON解析エラー: {e}")
                        continue
        
        except Exception as e:
            self.logger.warning(f"Universal Data抽出エラー: {e}")
        
        return details
    
    def _extract_from_json_ld_enhanced(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """JSON-LD構造化データから情報を抽出（改良版）"""
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
                                extracted = self._parse_video_object_enhanced(data)
                                details.update(extracted)
                            
                            # その他の構造化データ
                            if 'interactionStatistic' in data:
                                extracted = self._parse_interaction_stats_enhanced(data['interactionStatistic'])
                                details.update(extracted)
                        
                        elif isinstance(data, list):
                            # 配列の場合は各要素をチェック
                            for item in data:
                                if isinstance(item, dict) and item.get('@type') == 'VideoObject':
                                    extracted = self._parse_video_object_enhanced(item)
                                    details.update(extracted)
                        
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.logger.warning(f"JSON-LD抽出エラー: {e}")
        
        return details
    
    def _extract_from_meta_tags_enhanced(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """メタタグから情報を抽出（改良版）"""
        details = {}
        
        try:
            # Open Graphメタタグ
            og_tags = {
                'og:title': 'title',
                'og:description': 'description',
                'og:image': 'thumbnail_url',
                'og:video': 'video_url',
                'og:video:duration': 'duration',
                'og:video:width': 'width',
                'og:video:height': 'height'
            }
            
            for og_property, detail_key in og_tags.items():
                meta_tag = soup.find('meta', property=og_property)
                if meta_tag and meta_tag.get('content'):
                    content = meta_tag['content']
                    if detail_key in ['duration', 'width', 'height']:
                        try:
                            details[detail_key] = int(content)
                        except ValueError:
                            pass
                    else:
                        details[detail_key] = content
            
            # Twitterカードメタタグ
            twitter_tags = {
                'twitter:title': 'title',
                'twitter:description': 'description',
                'twitter:image': 'thumbnail_url',
                'twitter:player:width': 'width',
                'twitter:player:height': 'height'
            }
            
            for twitter_name, detail_key in twitter_tags.items():
                meta_tag = soup.find('meta', attrs={'name': twitter_name})
                if meta_tag and meta_tag.get('content'):
                    if detail_key not in details:  # OGタグを優先
                        content = meta_tag['content']
                        if detail_key in ['width', 'height']:
                            try:
                                details[detail_key] = int(content)
                            except ValueError:
                                pass
                        else:
                            details[detail_key] = content
            
            # TikTok特有のメタタグ
            tiktok_meta_tags = {
                'tiktok:video:id': 'video_id',
                'tiktok:author': 'author_username',
                'tiktok:upload_date': 'create_time'
            }
            
            for meta_name, detail_key in tiktok_meta_tags.items():
                meta_tag = soup.find('meta', attrs={'name': meta_name})
                if meta_tag and meta_tag.get('content'):
                    details[detail_key] = meta_tag['content']
        
        except Exception as e:
            self.logger.warning(f"メタタグ抽出エラー: {e}")
        
        return details
    
    def _extract_from_text_content_enhanced(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """HTMLテキストコンテンツから統計情報を抽出（改良版）"""
        details = {}
        
        try:
            text_content = soup.get_text()
            
            # 再生数パターン（改良版）
            view_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生|回再生|次再生)',
                r'(\d+(?:,\d+)*)\s*(?:views?|再生)',
                r'再生回数[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                r'view[s]?\s*[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in view_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    view_count = self._parse_count_string(match.group(1))
                    if view_count and view_count > 0:
                        details['view_count'] = view_count
                        break
            
            # いいね数パターン（改良版）
            like_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね|♥)',
                r'♥\s*(\d+(?:\.\d+)?[KMB]?)',
                r'いいね[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                r'like[s]?\s*[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    like_count = self._parse_count_string(match.group(1))
                    if like_count and like_count > 0:
                        details['like_count'] = like_count
                        break
            
            # コメント数パターン（改良版）
            comment_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:comments?|コメント)',
                r'コメント[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                r'comment[s]?\s*[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in comment_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    comment_count = self._parse_count_string(match.group(1))
                    if comment_count and comment_count > 0:
                        details['comment_count'] = comment_count
                        break
            
            # シェア数パターン（改良版）
            share_patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:shares?|シェア)',
                r'シェア[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                r'share[s]?\s*[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in share_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    share_count = self._parse_count_string(match.group(1))
                    if share_count and share_count > 0:
                        details['share_count'] = share_count
                        break
            
            # 投稿日時パターン（改良版）
            date_patterns = [
                r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
                r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
                r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
                r'(\d+)\s*(?:hours?|時間)\s*ago',  # X hours ago
                r'(\d+)\s*(?:days?|日)\s*ago',  # X days ago
                r'(\d+)\s*(?:weeks?|週間)\s*ago',  # X weeks ago
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    details['create_time_raw'] = match.group(1)
                    break
        
        except Exception as e:
            self.logger.warning(f"テキストコンテンツ抽出エラー: {e}")
        
        return details
    
    def _extract_from_e2e_attributes_enhanced(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """data-e2e属性から情報を抽出（改良版）"""
        details = {}
        
        try:
            # 統計情報のdata-e2e属性（改良版）
            e2e_mappings = {
                'like-count': 'like_count',
                'comment-count': 'comment_count',
                'share-count': 'share_count',
                'video-views': 'view_count',
                'video-view-count': 'view_count',
                'browse-video-desc': 'description',
                'browse-username': 'author_username',
                'browse-nickname': 'author_display_name'
            }
            
            for e2e_value, detail_key in e2e_mappings.items():
                elements = soup.find_all(attrs={'data-e2e': e2e_value})
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        if detail_key in ['like_count', 'comment_count', 'share_count', 'view_count']:
                            count = self._parse_count_string(text)
                            if count is not None and count > 0:
                                details[detail_key] = count
                                break
                        else:
                            details[detail_key] = text
                            break
        
        except Exception as e:
            self.logger.warning(f"data-e2e属性抽出エラー: {e}")
        
        return details
    
    def _extract_from_css_selectors(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """CSS セレクターによる直接抽出"""
        details = {}
        
        try:
            # TikTokの一般的なCSSセレクター
            css_selectors = {
                # 統計情報
                '[data-e2e="like-count"]': 'like_count',
                '[data-e2e="comment-count"]': 'comment_count',
                '[data-e2e="share-count"]': 'share_count',
                '[data-e2e="video-views"]': 'view_count',
                
                # 作者情報
                '[data-e2e="browse-username"]': 'author_username',
                '[data-e2e="browse-nickname"]': 'author_display_name',
                
                # 動画情報
                '[data-e2e="browse-video-desc"]': 'description',
                
                # その他のセレクター
                '.video-meta-caption': 'description',
                '.author-uniqueId': 'author_username',
                '.author-nickname': 'author_display_name',
            }
            
            for selector, detail_key in css_selectors.items():
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text:
                            if detail_key in ['like_count', 'comment_count', 'share_count', 'view_count']:
                                count = self._parse_count_string(text)
                                if count is not None and count > 0:
                                    details[detail_key] = count
                                    break
                            else:
                                details[detail_key] = text
                                break
                except Exception:
                    continue
        
        except Exception as e:
            self.logger.warning(f"CSS セレクター抽出エラー: {e}")
        
        return details
    
    def _extract_from_regex_patterns(self, html_content: str) -> Dict[str, Any]:
        """正規表現による高度な抽出"""
        details = {}
        
        try:
            # 再生数の高度なパターン
            view_patterns = [
                r'"playCount":\s*(\d+)',
                r'"viewCount":\s*(\d+)',
                r'"play_count":\s*(\d+)',
                r'"view_count":\s*(\d+)',
                r'playCount["\']:\s*["\']?(\d+)',
                r'viewCount["\']:\s*["\']?(\d+)',
            ]
            
            for pattern in view_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    try:
                        view_count = int(match.group(1))
                        if view_count > 0:
                            details['view_count'] = view_count
                            break
                    except ValueError:
                        continue
            
            # いいね数の高度なパターン
            like_patterns = [
                r'"diggCount":\s*(\d+)',
                r'"likeCount":\s*(\d+)',
                r'"like_count":\s*(\d+)',
                r'diggCount["\']:\s*["\']?(\d+)',
                r'likeCount["\']:\s*["\']?(\d+)',
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    try:
                        like_count = int(match.group(1))
                        if like_count > 0:
                            details['like_count'] = like_count
                            break
                    except ValueError:
                        continue
            
            # 投稿日時の高度なパターン
            time_patterns = [
                r'"createTime":\s*(\d+)',
                r'"create_time":\s*(\d+)',
                r'"uploadDate":\s*["\']([^"\']+)["\']',
                r'"published_at":\s*["\']([^"\']+)["\']',
                r'createTime["\']:\s*["\']?(\d+)',
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    time_value = match.group(1)
                    try:
                        # Unix timestampの場合
                        if time_value.isdigit():
                            timestamp = int(time_value)
                            # TikTokのタイムスタンプは通常秒単位
                            if timestamp > 1000000000:  # 2001年以降
                                details['create_time'] = timestamp
                                break
                        else:
                            # ISO形式の場合
                            details['create_time_iso'] = time_value
                            break
                    except ValueError:
                        continue
            
            # 作者情報の高度なパターン
            author_patterns = [
                r'"uniqueId":\s*["\']([^"\']+)["\']',
                r'"author":\s*["\']([^"\']+)["\']',
                r'"username":\s*["\']([^"\']+)["\']',
                r'uniqueId["\']:\s*["\']([^"\']+)["\']',
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    author = match.group(1)
                    if author and len(author) > 0:
                        details['author_username'] = author
                        break
        
        except Exception as e:
            self.logger.warning(f"正規表現抽出エラー: {e}")
        
        return details
    
    def _parse_item_module_data_enhanced(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ItemModuleデータを解析（改良版）"""
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
            
            # 動画情報
            if 'video' in data:
                video = data['video']
                if 'duration' in video:
                    details['duration'] = video['duration']
                if 'width' in video:
                    details['width'] = video['width']
                if 'height' in video:
                    details['height'] = video['height']
        
        except Exception as e:
            self.logger.warning(f"ItemModule解析エラー: {e}")
        
        return details
    
    def _parse_user_module_data_enhanced(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """UserModuleデータを解析（改良版）"""
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
            if 'followingCount' in data:
                details['author_following_count'] = data['followingCount']
            if 'videoCount' in data:
                details['author_video_count'] = data['videoCount']
        
        except Exception as e:
            self.logger.warning(f"UserModule解析エラー: {e}")
        
        return details
    
    def _parse_video_detail_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """VideoDetailデータを解析"""
        details = {}
        
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        # 再帰的に解析
                        sub_details = self._parse_video_detail_data(value)
                        details.update(sub_details)
        
        except Exception as e:
            self.logger.warning(f"VideoDetail解析エラー: {e}")
        
        return details
    
    def _parse_webapp_video_detail(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """webapp.video-detailデータを解析"""
        details = {}
        
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        # 再帰的に解析
                        sub_details = self._parse_webapp_video_detail(value)
                        details.update(sub_details)
        
        except Exception as e:
            self.logger.warning(f"webapp.video-detail解析エラー: {e}")
        
        return details
    
    def _parse_video_object_enhanced(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """VideoObjectデータを解析（改良版）"""
        details = {}
        
        try:
            if 'name' in data:
                details['title'] = data['name']
            if 'description' in data:
                details['description'] = data['description']
            if 'uploadDate' in data:
                details['create_time_iso'] = data['uploadDate']
            if 'thumbnailUrl' in data:
                details['thumbnail_url'] = data['thumbnailUrl']
            if 'contentUrl' in data:
                details['video_url'] = data['contentUrl']
            if 'duration' in data:
                details['duration'] = data['duration']
            if 'width' in data:
                details['width'] = data['width']
            if 'height' in data:
                details['height'] = data['height']
        
        except Exception as e:
            self.logger.warning(f"VideoObject解析エラー: {e}")
        
        return details
    
    def _parse_interaction_stats_enhanced(self, stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """インタラクション統計を解析（改良版）"""
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
                elif interaction_type == 'WatchAction' and user_interaction_count:
                    details['view_count'] = int(user_interaction_count)
        
        except Exception as e:
            self.logger.warning(f"インタラクション統計解析エラー: {e}")
        
        return details
    
    def _parse_count_string(self, count_str: str) -> Optional[int]:
        """カウント文字列を数値に変換（改良版）"""
        try:
            count_str = count_str.upper().strip().replace(',', '').replace(' ', '')
            
            if count_str.endswith('K'):
                return int(float(count_str[:-1]) * 1000)
            elif count_str.endswith('M'):
                return int(float(count_str[:-1]) * 1000000)
            elif count_str.endswith('B'):
                return int(float(count_str[:-1]) * 1000000000)
            else:
                # 数値のみの場合
                return int(float(count_str))
                
        except (ValueError, TypeError):
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            'success_rate': self.stats['successful_requests'] / max(self.stats['total_requests'], 1),
            'view_count_extraction_rate': self.stats['view_count_extracted'] / max(self.stats['videos_with_details'], 1),
            'create_time_extraction_rate': self.stats['create_time_extracted'] / max(self.stats['videos_with_details'], 1),
            'author_extraction_rate': self.stats['author_extracted'] / max(self.stats['videos_with_details'], 1)
        }


def test_enhanced_scraper():
    """改良版スクレイパーのテスト"""
    import os
    
    # APIキーを取得
    api_key = os.getenv('SCRAPERAPI_KEY')
    if not api_key:
        print("❌ SCRAPERAPI_KEY環境変数が設定されていません")
        return
    
    # テスト用動画URL
    test_urls = [
        "https://www.tiktok.com/@_quietlydope/video/7535094688726945079",
        "https://www.tiktok.com/@ohnoitsrolo/video/7534370912854985997",
    ]
    
    scraper = EnhancedVideoDetailScraper(api_key)
    
    print("🔍 改良版動画詳細スクレイパーのテスト開始")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n=== テスト {i}: {url} ===")
        
        details = scraper.get_video_details(url)
        
        if details:
            print("✅ 詳細情報取得成功")
            print(f"動画ID: {details.get('video_id', 'N/A')}")
            print(f"タイトル: {details.get('title', 'N/A')}")
            print(f"作者: {details.get('author_username', 'N/A')}")
            print(f"再生数: {details.get('view_count', 'N/A')}")
            print(f"いいね数: {details.get('like_count', 'N/A')}")
            print(f"投稿日時: {details.get('create_time', 'N/A')}")
            
            # 詳細情報をファイルに保存
            import json
            os.makedirs('debug', exist_ok=True)
            with open(f'debug/enhanced_video_details_{details.get("video_id", i)}.json', 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
            print(f"詳細情報を保存: debug/enhanced_video_details_{details.get('video_id', i)}.json")
        else:
            print("❌ 詳細情報取得失敗")
    
    # 統計情報を表示
    stats = scraper.get_stats()
    print(f"\n📊 統計情報:")
    print(f"総リクエスト数: {stats['total_requests']}")
    print(f"成功率: {stats['success_rate']:.2%}")
    print(f"再生数抽出率: {stats['view_count_extraction_rate']:.2%}")
    print(f"投稿日時抽出率: {stats['create_time_extraction_rate']:.2%}")
    print(f"作者情報抽出率: {stats['author_extraction_rate']:.2%}")


if __name__ == "__main__":
    test_enhanced_scraper()

