"""
TikTok parser for TikTok Research System
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.logger import get_logger
from ..utils.helpers import (
    clean_text, 
    parse_view_count, 
    parse_upload_date, 
    extract_video_id,
    safe_get
)
from ..scraper.exceptions import ParseError
from .html_parser import HTMLParser
from .video_data import VideoData, VideoCollection


class TikTokParser:
    """TikTok専用パーサー"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.html_parser = HTMLParser()
    
    def parse_explore_page(self, html_content: str) -> VideoCollection:
        """
        TikTok /exploreページを解析
        
        Args:
            html_content: HTML文字列
            
        Returns:
            動画データコレクション
        """
        self.logger.info("TikTok /exploreページの解析を開始")
        
        try:
            # HTMLをパース
            soup = self.html_parser.parse_html(html_content)
            
            # 動画データを抽出
            videos = []
            
            # 方法1: JSONデータから抽出
            json_videos = self._extract_from_json_data(soup)
            videos.extend(json_videos)
            
            # 方法2: HTML要素から抽出
            html_videos = self._extract_from_html_elements(soup)
            videos.extend(html_videos)
            
            # 方法3: リンクから抽出
            link_videos = self._extract_from_links(soup)
            videos.extend(link_videos)
            
            # 重複を除去
            unique_videos = self._remove_duplicates(videos)
            
            # コレクションを作成
            collection = VideoCollection(
                videos=unique_videos,
                source="tiktok_explore",
                total_count=len(unique_videos)
            )
            
            self.logger.info(f"動画データ {len(unique_videos)} 件を抽出完了")
            return collection
            
        except Exception as e:
            self.logger.error(f"TikTok /exploreページ解析エラー: {e}")
            raise ParseError(f"ページ解析に失敗: {e}")
    
    def _extract_from_json_data(self, soup) -> List[VideoData]:
        """JSONデータから動画情報を抽出"""
        videos = []
        
        try:
            json_data_list = self.html_parser.extract_json_data(soup)
            
            for json_data in json_data_list:
                # TikTokの一般的なJSONデータ構造を解析
                video_list = self._find_video_data_in_json(json_data)
                
                for video_info in video_list:
                    video = self._create_video_from_json(video_info)
                    if video and video.is_valid:
                        videos.append(video)
            
            self.logger.info(f"JSONから {len(videos)} 件の動画データを抽出")
            
        except Exception as e:
            self.logger.warning(f"JSON解析エラー: {e}")
        
        return videos
    
    def _find_video_data_in_json(self, data: Any, path: str = "") -> List[Dict[str, Any]]:
        """JSON内の動画データを再帰的に検索"""
        video_list = []
        
        if isinstance(data, dict):
            # 動画データの可能性があるキーを検索
            video_keys = [
                'itemList', 'items', 'videoList', 'videos', 'data',
                'recommendList', 'feedList', 'exploreList'
            ]
            
            for key, value in data.items():
                if key in video_keys and isinstance(value, list):
                    # 動画リストの可能性
                    for item in value:
                        if self._is_video_data(item):
                            video_list.append(item)
                else:
                    # 再帰的に検索
                    video_list.extend(self._find_video_data_in_json(value, f"{path}.{key}"))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if self._is_video_data(item):
                    video_list.append(item)
                else:
                    video_list.extend(self._find_video_data_in_json(item, f"{path}[{i}]"))
        
        return video_list
    
    def _is_video_data(self, data: Any) -> bool:
        """データが動画情報かどうかを判定"""
        if not isinstance(data, dict):
            return False
        
        # 動画データの特徴的なキーをチェック
        video_indicators = [
            'id', 'video', 'aweme_id', 'item_id',
            'desc', 'description', 'title',
            'author', 'user', 'creator',
            'stats', 'statistics', 'digg_count', 'play_count'
        ]
        
        return any(key in data for key in video_indicators)
    
    def _create_video_from_json(self, video_info: Dict[str, Any]) -> Optional[VideoData]:
        """JSON情報から動画データを作成"""
        try:
            # 基本情報の抽出
            video_id = self._extract_video_id_from_json(video_info)
            if not video_id:
                return None
            
            # URL構築
            author_username = safe_get(video_info, 'author.unique_id') or safe_get(video_info, 'author.uniqueId')
            if author_username:
                url = f"https://www.tiktok.com/@{author_username}/video/{video_id}"
            else:
                url = f"https://www.tiktok.com/video/{video_id}"
            
            # 動画データを作成
            video = VideoData(
                video_id=video_id,
                url=url,
                title=clean_text(safe_get(video_info, 'desc') or safe_get(video_info, 'description') or ''),
                description=clean_text(safe_get(video_info, 'desc') or safe_get(video_info, 'description') or ''),
                
                # 作成者情報
                author_username=author_username or '',
                author_display_name=clean_text(safe_get(video_info, 'author.nickname') or safe_get(video_info, 'author.display_name') or ''),
                author_verified=safe_get(video_info, 'author.verified') or False,
                
                # 統計情報
                view_count=safe_get(video_info, 'stats.play_count') or safe_get(video_info, 'statistics.play_count'),
                like_count=safe_get(video_info, 'stats.digg_count') or safe_get(video_info, 'statistics.digg_count'),
                comment_count=safe_get(video_info, 'stats.comment_count') or safe_get(video_info, 'statistics.comment_count'),
                share_count=safe_get(video_info, 'stats.share_count') or safe_get(video_info, 'statistics.share_count'),
                
                # 時間情報
                upload_date=self._extract_upload_date_from_json(video_info),
                duration=safe_get(video_info, 'video.duration') or safe_get(video_info, 'duration'),
                
                # メディア情報
                thumbnail_url=self._extract_thumbnail_url(video_info),
                music_title=clean_text(safe_get(video_info, 'music.title') or ''),
                music_author=clean_text(safe_get(video_info, 'music.author') or ''),
                
                # メタデータ
                source_page="explore",
                raw_data=video_info
            )
            
            # ハッシュタグとメンションを抽出
            description = video.description
            if description:
                video.hashtags = self.html_parser.extract_hashtags(description)
                video.mentions = self.html_parser.extract_mentions(description)
            
            return video
            
        except Exception as e:
            self.logger.warning(f"JSON動画データ作成エラー: {e}")
            return None
    
    def _extract_video_id_from_json(self, video_info: Dict[str, Any]) -> Optional[str]:
        """JSONから動画IDを抽出"""
        id_keys = ['id', 'aweme_id', 'item_id', 'video_id']
        
        for key in id_keys:
            video_id = safe_get(video_info, key)
            if video_id:
                return str(video_id)
        
        return None
    
    def _extract_upload_date_from_json(self, video_info: Dict[str, Any]) -> Optional[datetime]:
        """JSONから投稿日時を抽出"""
        date_keys = ['create_time', 'createTime', 'upload_date', 'published_at']
        
        for key in date_keys:
            date_value = safe_get(video_info, key)
            if date_value:
                try:
                    # Unix timestamp の場合
                    if isinstance(date_value, (int, float)):
                        return datetime.fromtimestamp(date_value)
                    # 文字列の場合
                    elif isinstance(date_value, str):
                        return parse_upload_date(date_value)
                except Exception:
                    continue
        
        return None
    
    def _extract_thumbnail_url(self, video_info: Dict[str, Any]) -> str:
        """JSONからサムネイルURLを抽出"""
        thumbnail_paths = [
            'video.cover.url_list.0',
            'video.dynamic_cover.url_list.0',
            'video.origin_cover.url_list.0',
            'cover.url_list.0',
            'thumbnail_url',
            'cover_url'
        ]
        
        for path in thumbnail_paths:
            url = safe_get(video_info, path)
            if url:
                return str(url)
        
        return ""
    
    def _extract_from_html_elements(self, soup) -> List[VideoData]:
        """HTML要素から動画情報を抽出"""
        videos = []
        
        try:
            video_elements = self.html_parser.extract_video_elements(soup)
            
            for element in video_elements:
                video = self._create_video_from_element(element)
                if video and video.is_valid:
                    videos.append(video)
            
            self.logger.info(f"HTML要素から {len(videos)} 件の動画データを抽出")
            
        except Exception as e:
            self.logger.warning(f"HTML要素解析エラー: {e}")
        
        return videos
    
    def _create_video_from_element(self, element) -> Optional[VideoData]:
        """HTML要素から動画データを作成"""
        try:
            # メタデータを抽出
            metadata = self.html_parser.extract_metadata_from_element(element)
            
            # 動画URLを抽出
            video_url = self._extract_video_url_from_element(element)
            if not video_url:
                return None
            
            # 動画IDを抽出
            video_id = extract_video_id(video_url)
            if not video_id:
                return None
            
            # 統計情報を抽出
            stats = self.html_parser.extract_video_stats(element)
            
            # 作成者情報を抽出
            author_info = self.html_parser.extract_author_info(element)
            
            # 動画データを作成
            video = VideoData(
                video_id=video_id,
                url=video_url,
                title=clean_text(metadata.get('text_content', '')[:100]),
                description=clean_text(metadata.get('text_content', '')),
                
                # 作成者情報
                author_username=author_info.get('username', ''),
                author_display_name=author_info.get('display_name', ''),
                author_verified=author_info.get('verified', False),
                
                # 統計情報
                view_count=stats.get('view_count'),
                like_count=stats.get('like_count'),
                comment_count=stats.get('comment_count'),
                share_count=stats.get('share_count'),
                
                # メディア情報
                thumbnail_url=metadata.get('images', [''])[0] if metadata.get('images') else '',
                
                # メタデータ
                source_page="explore",
                raw_data=metadata
            )
            
            # ハッシュタグとメンションを抽出
            if video.description:
                video.hashtags = self.html_parser.extract_hashtags(video.description)
                video.mentions = self.html_parser.extract_mentions(video.description)
            
            return video
            
        except Exception as e:
            self.logger.warning(f"HTML要素動画データ作成エラー: {e}")
            return None
    
    def _extract_video_url_from_element(self, element) -> Optional[str]:
        """HTML要素から動画URLを抽出"""
        # リンクを検索
        links = element.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            if self._is_tiktok_video_url(href):
                return href
        
        # data属性を検索
        for attr_name, attr_value in element.attrs.items():
            if isinstance(attr_value, str) and self._is_tiktok_video_url(attr_value):
                return attr_value
        
        return None
    
    def _is_tiktok_video_url(self, url: str) -> bool:
        """TikTok動画URLかどうかを判定"""
        if not url or not isinstance(url, str):
            return False
        
        patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm\.)?tiktok\.com/\w+',
            r'https?://(?:www\.)?tiktok\.com/t/\w+'
        ]
        
        return any(re.match(pattern, url) for pattern in patterns)
    
    def _extract_from_links(self, soup) -> List[VideoData]:
        """リンクから動画情報を抽出"""
        videos = []
        
        try:
            links = self.html_parser.extract_links(soup, "https://www.tiktok.com")
            
            for link in links:
                video_id = extract_video_id(link)
                if video_id:
                    video = VideoData(
                        video_id=video_id,
                        url=link,
                        source_page="explore"
                    )
                    videos.append(video)
            
            self.logger.info(f"リンクから {len(videos)} 件の動画データを抽出")
            
        except Exception as e:
            self.logger.warning(f"リンク解析エラー: {e}")
        
        return videos
    
    def _remove_duplicates(self, videos: List[VideoData]) -> List[VideoData]:
        """重複する動画データを除去"""
        seen_ids = set()
        unique_videos = []
        
        for video in videos:
            if video.video_id not in seen_ids:
                unique_videos.append(video)
                seen_ids.add(video.video_id)
        
        self.logger.info(f"重複除去: {len(videos)} → {len(unique_videos)} 件")
        return unique_videos
    
    def parse_video_page(self, html_content: str, video_url: str) -> Optional[VideoData]:
        """
        個別動画ページを解析
        
        Args:
            html_content: HTML文字列
            video_url: 動画URL
            
        Returns:
            動画データ
        """
        try:
            soup = self.html_parser.parse_html(html_content)
            
            # JSONデータから詳細情報を抽出
            json_data_list = self.html_parser.extract_json_data(soup)
            
            for json_data in json_data_list:
                video_list = self._find_video_data_in_json(json_data)
                
                for video_info in video_list:
                    video = self._create_video_from_json(video_info)
                    if video and video.url == video_url:
                        return video
            
            # JSONで見つからない場合、HTML要素から抽出
            video_id = extract_video_id(video_url)
            if video_id:
                return VideoData(
                    video_id=video_id,
                    url=video_url,
                    source_page="video_detail"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"動画ページ解析エラー: {e}")
            return None

