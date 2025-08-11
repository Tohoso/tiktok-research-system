"""
Enhanced TikTok parser with successful extraction logic
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from ..utils.logger import get_logger
from .video_data import VideoData


class EnhancedTikTokParser:
    """成功した抽出ロジックを統合した改良版TikTokパーサー"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def parse_videos(self, html_content: str) -> List[VideoData]:
        """
        HTMLコンテンツから動画データを解析（成功した抽出ロジック使用）
        
        Args:
            html_content: 解析対象のHTMLコンテンツ
            
        Returns:
            動画データのリスト
        """
        self.logger.info("動画データの解析を開始")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            videos = []
            
            # 方法1: 動画リンクから抽出（最も成功率が高い）
            video_links = soup.find_all('a', href=re.compile(r'/video/\d+'))
            self.logger.info(f"動画リンク: {len(video_links)}件")
            
            for link in video_links:
                video_data = self._extract_from_video_link(link)
                if video_data:
                    videos.append(video_data)
            
            # 方法2: data-e2e属性を持つ要素から抽出
            recommend_items = soup.find_all(attrs={'data-e2e': 'recommend-list-item'})
            self.logger.info(f"recommend-list-item要素: {len(recommend_items)}件")
            
            for element in recommend_items:
                video_data = self._extract_from_recommend_item(element)
                if video_data:
                    videos.append(video_data)
            
            # 方法3: JavaScriptデータから抽出
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('{' in script.string or '[' in script.string):
                    try:
                        # window.__INITIAL_STATE__ パターン
                        if 'window.__INITIAL_STATE__' in script.string:
                            json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script.string, re.DOTALL)
                            if json_match:
                                try:
                                    data = json.loads(json_match.group(1))
                                    script_videos = self._extract_from_initial_state(data)
                                    videos.extend(script_videos)
                                except json.JSONDecodeError:
                                    pass
                        
                        # その他のJSONパターン
                        elif script.string.strip().startswith('{') or script.string.strip().startswith('['):
                            try:
                                data = json.loads(script.string)
                                script_videos = self._extract_from_script_data(data)
                                videos.extend(script_videos)
                            except json.JSONDecodeError:
                                pass
                                
                    except Exception:
                        continue
            
            # 重複除去
            unique_videos = self._remove_duplicate_videos(videos)
            
            # VideoDataオブジェクトに変換
            video_data_objects = []
            for video in unique_videos:
                try:
                    video_obj = VideoData(
                        video_id=video.get('video_id', ''),
                        url=video.get('url', ''),
                        title=video.get('description', ''),
                        description=video.get('description', ''),
                        author_username=video.get('author_username', ''),
                        author_display_name=video.get('author_display_name', ''),
                        view_count=self._parse_view_count(video.get('view_count')),
                        like_count=self._parse_count(video.get('like_count')),
                        comment_count=self._parse_count(video.get('comment_count')),
                        share_count=self._parse_count(video.get('share_count')),
                        hashtags=video.get('hashtags', []),
                        music_title=video.get('music_title', ''),
                        duration=video.get('duration')
                    )
                    video_data_objects.append(video_obj)
                except Exception as e:
                    self.logger.warning(f"VideoDataオブジェクト作成エラー: {e}")
                    continue
            
            self.logger.info(f"解析完了: {len(video_data_objects)}件の動画データを抽出")
            return video_data_objects
            
        except Exception as e:
            self.logger.error(f"動画データ解析エラー: {e}")
            return []
    
    def _extract_from_video_link(self, link) -> Optional[Dict[str, Any]]:
        """動画リンクから動画データを抽出"""
        try:
            href = link.get('href', '')
            
            # 動画IDを抽出
            video_id_match = re.search(r'/video/(\d+)', href)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            
            # 作者情報を抽出
            author_username = ''
            if '/@' in href:
                author_match = re.search(r'/@([\w.-]+)', href)
                if author_match:
                    author_username = author_match.group(1)
            
            # 親要素から追加情報を抽出
            parent = link.parent
            text_content = parent.get_text(strip=True) if parent else ''
            
            # 再生数を抽出（テキストから）
            view_count = self._extract_view_count_from_text(text_content)
            
            return {
                'video_id': video_id,
                'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
                'author_username': author_username,
                'description': text_content,
                'view_count': view_count,
                'extraction_method': 'video_link'
            }
            
        except Exception as e:
            self.logger.warning(f"動画リンク解析エラー: {e}")
            return None
    
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
            
            # 統計情報を抽出
            view_count = self._extract_view_count_from_text(text_content)
            like_count = self._extract_like_count_from_text(text_content)
            
            return {
                'video_id': video_id,
                'url': f"https://www.tiktok.com{href}" if href.startswith('/') else href,
                'author_username': author_username,
                'description': text_content,
                'view_count': view_count,
                'like_count': like_count,
                'extraction_method': 'recommend_item'
            }
            
        except Exception as e:
            self.logger.warning(f"recommend-list-item要素解析エラー: {e}")
            return None
    
    def _extract_from_initial_state(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """INITIAL_STATEデータから動画データを抽出"""
        videos = []
        
        try:
            def search_video_data(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['itemList', 'items', 'videoList', 'videos', 'data', 'list']:
                            if isinstance(value, list):
                                for item in value:
                                    if self._is_video_item(item):
                                        video_data = self._extract_video_from_item(item)
                                        if video_data:
                                            videos.append(video_data)
                            else:
                                search_video_data(value, f"{path}.{key}")
                        elif key in ['aweme_id', 'video_id', 'id'] and isinstance(value, (str, int)):
                            if str(value).isdigit():
                                videos.append({
                                    'video_id': str(value),
                                    'url': f"https://www.tiktok.com/video/{value}",
                                    'extraction_method': 'initial_state'
                                })
                        else:
                            search_video_data(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_video_data(item, f"{path}[{i}]")
            
            search_video_data(data)
            
        except Exception as e:
            self.logger.warning(f"INITIAL_STATEデータ解析エラー: {e}")
        
        return videos
    
    def _extract_from_script_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """スクリプトデータから動画データを抽出"""
        videos = []
        
        try:
            def search_video_data(obj, path=""):
                if isinstance(obj, dict):
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
                        else:
                            search_video_data(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_video_data(item, f"{path}[{i}]")
            
            search_video_data(data)
            
        except Exception as e:
            self.logger.warning(f"スクリプトデータ解析エラー: {e}")
        
        return videos
    
    def _is_video_item(self, item: Any) -> bool:
        """アイテムが動画データかどうかを判定"""
        if not isinstance(item, dict):
            return False
        
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
    
    def _extract_view_count_from_text(self, text: str) -> Optional[int]:
        """テキストから再生数を抽出"""
        try:
            # 数値パターンを検索（M, K, B サフィックス対応）
            patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生|回再生)',
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:M|K|B)',
                r'(\d+(?:\.\d+)?[KMB])',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._parse_count_string(match.group(1))
            
            return None
            
        except Exception:
            return None
    
    def _extract_like_count_from_text(self, text: str) -> Optional[int]:
        """テキストからいいね数を抽出"""
        try:
            patterns = [
                r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね)',
                r'♥\s*(\d+(?:\.\d+)?[KMB]?)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return self._parse_count_string(match.group(1))
            
            return None
            
        except Exception:
            return None
    
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
    
    def _parse_view_count(self, view_count) -> Optional[int]:
        """再生数を解析"""
        if isinstance(view_count, int):
            return view_count
        elif isinstance(view_count, str):
            return self._parse_count_string(view_count)
        return None
    
    def _parse_count(self, count) -> Optional[int]:
        """カウントを解析"""
        if isinstance(count, int):
            return count
        elif isinstance(count, str):
            return self._parse_count_string(count)
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

