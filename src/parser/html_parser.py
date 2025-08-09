"""
HTML parser for TikTok Research System
"""

import re
import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse

from ..utils.logger import get_logger
from ..utils.helpers import clean_text, parse_view_count, parse_upload_date
from ..scraper.exceptions import ParseError


class HTMLParser:
    """HTML解析クラス"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def parse_html(self, html_content: str, base_url: str = "") -> BeautifulSoup:
        """
        HTMLをパース
        
        Args:
            html_content: HTML文字列
            base_url: ベースURL
            
        Returns:
            BeautifulSoupオブジェクト
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            return soup
        except Exception as e:
            self.logger.error(f"HTMLパースエラー: {e}")
            raise ParseError(f"HTMLパースに失敗: {e}", raw_data=html_content[:1000])
    
    def extract_json_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        HTML内のJSONデータを抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            抽出されたJSONデータのリスト
        """
        json_data_list = []
        
        # script タグ内のJSONを検索
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    json_data_list.append(data)
            except json.JSONDecodeError:
                continue
        
        # script タグ内のJavaScript変数を検索
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string:
                # window.__INITIAL_STATE__ などの変数を検索
                patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                    r'window\.__NEXT_DATA__\s*=\s*({.+?});',
                    r'window\.SIGI_STATE\s*=\s*({.+?});',
                    r'__INITIAL_PROPS__\s*=\s*({.+?});'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, script.string, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match)
                            json_data_list.append(data)
                        except json.JSONDecodeError:
                            continue
        
        self.logger.info(f"JSONデータ {len(json_data_list)} 件を抽出")
        return json_data_list
    
    def extract_video_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """
        動画要素を抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            動画要素のリスト
        """
        video_elements = []
        
        # 一般的な動画コンテナのセレクタ
        selectors = [
            '[data-e2e="recommend-list-item"]',
            '[data-e2e="video-feed-item"]',
            '.video-feed-item',
            '.video-card',
            '.tiktok-video',
            '[class*="video"]',
            '[class*="item"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                video_elements.extend(elements)
                self.logger.debug(f"セレクタ '{selector}' で {len(elements)} 件の要素を発見")
        
        # 重複を除去
        unique_elements = []
        seen_elements = set()
        
        for element in video_elements:
            element_id = id(element)
            if element_id not in seen_elements:
                unique_elements.append(element)
                seen_elements.add(element_id)
        
        self.logger.info(f"動画要素 {len(unique_elements)} 件を抽出")
        return unique_elements
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = "") -> List[str]:
        """
        TikTok動画リンクを抽出
        
        Args:
            soup: BeautifulSoupオブジェクト
            base_url: ベースURL
            
        Returns:
            動画URLのリスト
        """
        links = []
        
        # TikTok動画URLのパターン
        tiktok_patterns = [
            r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/\d+',
            r'https?://(?:vm\.)?tiktok\.com/\w+',
            r'https?://(?:www\.)?tiktok\.com/t/\w+'
        ]
        
        # href属性から抽出
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # 相対URLを絶対URLに変換
            if base_url and not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # TikTok動画URLかチェック
            for pattern in tiktok_patterns:
                if re.match(pattern, href):
                    links.append(href)
                    break
        
        # テキスト内からURL抽出
        text_content = soup.get_text()
        for pattern in tiktok_patterns:
            matches = re.findall(pattern, text_content)
            links.extend(matches)
        
        # 重複を除去
        unique_links = list(set(links))
        
        self.logger.info(f"TikTok動画リンク {len(unique_links)} 件を抽出")
        return unique_links
    
    def extract_metadata_from_element(self, element: Tag) -> Dict[str, Any]:
        """
        要素からメタデータを抽出
        
        Args:
            element: HTML要素
            
        Returns:
            抽出されたメタデータ
        """
        metadata = {}
        
        # data属性から抽出
        for attr_name, attr_value in element.attrs.items():
            if attr_name.startswith('data-'):
                metadata[attr_name] = attr_value
        
        # テキストコンテンツから抽出
        text_content = clean_text(element.get_text())
        if text_content:
            metadata['text_content'] = text_content
        
        # 画像URL抽出
        img_tags = element.find_all('img')
        if img_tags:
            metadata['images'] = [img.get('src') or img.get('data-src') for img in img_tags if img.get('src') or img.get('data-src')]
        
        # リンク抽出
        link_tags = element.find_all('a', href=True)
        if link_tags:
            metadata['links'] = [link['href'] for link in link_tags]
        
        return metadata
    
    def extract_video_stats(self, element: Tag) -> Dict[str, Optional[int]]:
        """
        動画統計情報を抽出
        
        Args:
            element: HTML要素
            
        Returns:
            統計情報
        """
        stats = {
            'view_count': None,
            'like_count': None,
            'comment_count': None,
            'share_count': None
        }
        
        # data属性から抽出
        for stat_name in stats.keys():
            data_attr = f'data-{stat_name.replace("_", "-")}'
            if element.get(data_attr):
                try:
                    stats[stat_name] = int(element[data_attr])
                except (ValueError, TypeError):
                    pass
        
        # テキストから数値を抽出
        text_content = element.get_text()
        
        # 再生数のパターン
        view_patterns = [
            r'(\d+(?:\.\d+)?[KMB]?)\s*(?:views?|再生)',
            r'(\d+(?:,\d+)*)\s*(?:views?|再生)'
        ]
        
        for pattern in view_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                stats['view_count'] = parse_view_count(match.group(1))
                break
        
        # いいね数のパターン
        like_patterns = [
            r'(\d+(?:\.\d+)?[KMB]?)\s*(?:likes?|いいね)',
            r'(\d+(?:,\d+)*)\s*(?:likes?|いいね)'
        ]
        
        for pattern in like_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                stats['like_count'] = parse_view_count(match.group(1))
                break
        
        return stats
    
    def extract_author_info(self, element: Tag) -> Dict[str, Any]:
        """
        作成者情報を抽出
        
        Args:
            element: HTML要素
            
        Returns:
            作成者情報
        """
        author_info = {
            'username': '',
            'display_name': '',
            'verified': False,
            'follower_count': None
        }
        
        # ユーザー名の抽出
        username_selectors = [
            '[data-e2e="video-author-uniqueid"]',
            '.author-username',
            '.username',
            '[class*="username"]'
        ]
        
        for selector in username_selectors:
            username_element = element.select_one(selector)
            if username_element:
                author_info['username'] = clean_text(username_element.get_text())
                break
        
        # 表示名の抽出
        display_name_selectors = [
            '[data-e2e="video-author-nickname"]',
            '.author-name',
            '.display-name',
            '[class*="display-name"]'
        ]
        
        for selector in display_name_selectors:
            name_element = element.select_one(selector)
            if name_element:
                author_info['display_name'] = clean_text(name_element.get_text())
                break
        
        # 認証バッジの確認
        verified_selectors = [
            '.verified',
            '[data-e2e="video-author-verified"]',
            '[class*="verified"]'
        ]
        
        for selector in verified_selectors:
            if element.select_one(selector):
                author_info['verified'] = True
                break
        
        return author_info
    
    def extract_hashtags(self, text: str) -> List[str]:
        """
        テキストからハッシュタグを抽出
        
        Args:
            text: テキスト
            
        Returns:
            ハッシュタグのリスト
        """
        if not text:
            return []
        
        # ハッシュタグのパターン
        hashtag_pattern = r'#[\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+'
        hashtags = re.findall(hashtag_pattern, text)
        
        # # を除去して正規化
        normalized_hashtags = [tag[1:] for tag in hashtags if len(tag) > 1]
        
        return list(set(normalized_hashtags))  # 重複除去
    
    def extract_mentions(self, text: str) -> List[str]:
        """
        テキストからメンションを抽出
        
        Args:
            text: テキスト
            
        Returns:
            メンションのリスト
        """
        if not text:
            return []
        
        # メンションのパターン
        mention_pattern = r'@[\w.-]+'
        mentions = re.findall(mention_pattern, text)
        
        # @ を除去して正規化
        normalized_mentions = [mention[1:] for mention in mentions if len(mention) > 1]
        
        return list(set(normalized_mentions))  # 重複除去

