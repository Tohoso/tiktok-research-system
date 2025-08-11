#!/usr/bin/env python3
"""
Meta Tag Based Video Detail Scraper for TikTok Research System
メタタグから統計情報を抽出する改良版スクレイパー
"""

import os
import sys
import re
import json
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.scraper.scraperapi_client import ScraperAPIClient
from src.utils.logger import get_logger
from src.parser.video_data import VideoData


class MetaTagVideoScraper:
    """メタタグベースの動画詳細スクレイパー"""
    
    def __init__(self, api_key: str):
        self.logger = get_logger(self.__class__.__name__)
        self.api_client = ScraperAPIClient(api_key)
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'videos_with_details': 0,
            'meta_tag_extractions': 0,
            'view_count_extracted': 0,
            'like_count_extracted': 0,
            'comment_count_extracted': 0,
            'author_extracted': 0
        }
    
    def get_video_details(self, video_url: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        個別動画ページから詳細情報を取得（メタタグベース）
        
        Args:
            video_url: 動画URL
            max_retries: 最大リトライ回数
            
        Returns:
            動画詳細情報の辞書、失敗時はNone
        """
        self.logger.info(f"動画詳細情報を取得: {video_url}")
        
        for attempt in range(max_retries):
            try:
                self.stats['total_requests'] += 1
                
                # JavaScript実行ありでスクレイピング
                response = self.api_client.scrape(
                    url=video_url,
                    render_js=True,
                    country_code='JP',
                    premium=True
                )
                
                if response and response.get('status_code') == 200:
                    html_content = response.get('content', '')
                    
                    if html_content and len(html_content) > 1000:
                        details = self._extract_video_details_from_meta(html_content, video_url)
                        
                        if details:
                            self.stats['successful_requests'] += 1
                            self.stats['videos_with_details'] += 1
                            self.logger.info(f"詳細情報取得成功: {video_url}")
                            return details
                        else:
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
    
    def _extract_video_details_from_meta(self, html_content: str, video_url: str) -> Optional[Dict[str, Any]]:
        """
        HTMLコンテンツのメタタグから動画詳細情報を抽出
        
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
            
            # メタタグから基本情報を抽出
            meta_info = self._extract_meta_tags(soup)
            details.update(meta_info)
            
            # descriptionメタタグから統計情報を抽出
            stats_info = self._extract_stats_from_description(soup)
            details.update(stats_info)
            
            # keywordsメタタグから追加情報を抽出
            keywords_info = self._extract_keywords(soup)
            details.update(keywords_info)
            
            # JSON-LDから補完情報を抽出
            json_ld_info = self._extract_json_ld(soup)
            details.update(json_ld_info)
            
            # 基本情報の補完
            details['url'] = video_url
            details['scraped_at'] = datetime.now().isoformat()
            details['extraction_method'] = 'meta_tag_based'
            
            # 統計更新
            if details.get('like_count'):
                self.stats['like_count_extracted'] += 1
            if details.get('comment_count'):
                self.stats['comment_count_extracted'] += 1
            if details.get('view_count'):
                self.stats['view_count_extracted'] += 1
            if details.get('author_username'):
                self.stats['author_extracted'] += 1
            
            self.stats['meta_tag_extractions'] += 1
            
            # 詳細情報が取得できたかチェック
            has_details = any([
                details.get('like_count'),
                details.get('comment_count'),
                details.get('title'),
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
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """メタタグから基本情報を抽出"""
        details = {}
        
        try:
            # Open Graphメタタグ
            og_tags = {
                'og:title': 'og_title',
                'og:description': 'og_description',
                'og:image': 'thumbnail_url',
                'og:url': 'canonical_url'
            }
            
            for og_property, detail_key in og_tags.items():
                meta_tag = soup.find('meta', property=og_property)
                if meta_tag and meta_tag.get('content'):
                    details[detail_key] = meta_tag['content']
            
            # Twitterカードメタタグ
            twitter_tags = {
                'twitter:title': 'twitter_title',
                'twitter:description': 'twitter_description',
                'twitter:image': 'twitter_image'
            }
            
            for twitter_name, detail_key in twitter_tags.items():
                meta_tag = soup.find('meta', attrs={'name': twitter_name})
                if meta_tag and meta_tag.get('content'):
                    details[detail_key] = meta_tag['content']
            
            # 基本メタタグ
            basic_tags = {
                'description': 'meta_description',
                'keywords': 'meta_keywords'
            }
            
            for meta_name, detail_key in basic_tags.items():
                meta_tag = soup.find('meta', attrs={'name': meta_name})
                if meta_tag and meta_tag.get('content'):
                    details[detail_key] = meta_tag['content']
            
            # タイトルタグ
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                details['page_title'] = title_tag.string.strip()
        
        except Exception as e:
            self.logger.warning(f"メタタグ抽出エラー: {e}")
        
        return details
    
    def _extract_stats_from_description(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """descriptionメタタグから統計情報を抽出"""
        details = {}
        
        try:
            # descriptionメタタグを取得
            desc_tag = soup.find('meta', attrs={'name': 'description'})
            if not desc_tag or not desc_tag.get('content'):
                return details
            
            description = desc_tag['content']
            self.logger.debug(f"Description内容: {description}")
            
            # 日本語の統計情報パターン
            patterns = {
                'like_count': [
                    r'いいねの数[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'いいね[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'♥\s*(\d+(?:\.\d+)?[KMB]?)'
                ],
                'comment_count': [
                    r'コメントの数[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'コメント[：:]\s*(\d+(?:\.\d+)?[KMB]?)'
                ],
                'view_count': [
                    r'再生回数[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'再生[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'(\d+(?:\.\d+)?[KMB]?)\s*回再生'
                ],
                'share_count': [
                    r'シェア[：:]\s*(\d+(?:\.\d+)?[KMB]?)',
                    r'共有[：:]\s*(\d+(?:\.\d+)?[KMB]?)'
                ]
            }
            
            # 各統計情報を抽出
            for stat_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        count_str = match.group(1)
                        count = self._parse_count_string(count_str)
                        if count is not None and count > 0:
                            details[stat_type] = count
                            self.logger.debug(f"{stat_type}を抽出: {count_str} -> {count}")
                            break
            
            # 作者情報を抽出
            author_patterns = [
                r'([^(]+)\s*\(@([^)]+)\)',  # "Destined Destiné (@_quietlydope)"
                r'@([a-zA-Z0-9_]+)',       # "@_quietlydope"
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, description)
                if match:
                    if len(match.groups()) == 2:
                        details['author_display_name'] = match.group(1).strip()
                        details['author_username'] = match.group(2).strip()
                    else:
                        details['author_username'] = match.group(1).strip()
                    break
            
            # 動画タイトル/説明を抽出
            title_patterns = [
                r'動画[：:]「([^」]+)」',
                r'TikTok[^：:]*[：:]「([^」]+)」',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, description)
                if match:
                    details['video_title'] = match.group(1).strip()
                    break
            
            # ハッシュタグやキーワードを抽出
            hashtag_match = re.search(r'。([^。]+)。', description)
            if hashtag_match:
                details['hashtags'] = hashtag_match.group(1).strip()
        
        except Exception as e:
            self.logger.warning(f"統計情報抽出エラー: {e}")
        
        return details
    
    def _extract_keywords(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """keywordsメタタグから情報を抽出"""
        details = {}
        
        try:
            keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_tag and keywords_tag.get('content'):
                keywords = keywords_tag['content']
                details['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
                self.logger.debug(f"キーワード抽出: {details['keywords']}")
        
        except Exception as e:
            self.logger.warning(f"キーワード抽出エラー: {e}")
        
        return details
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """JSON-LD構造化データから補完情報を抽出"""
        details = {}
        
        try:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        
                        if isinstance(data, dict) and data.get('@type') == 'VideoObject':
                            if 'name' in data:
                                details['json_ld_title'] = data['name']
                            if 'description' in data:
                                details['json_ld_description'] = data['description']
                            if 'uploadDate' in data:
                                details['upload_date'] = data['uploadDate']
                            if 'duration' in data:
                                details['duration'] = data['duration']
                            
                            # インタラクション統計
                            if 'interactionStatistic' in data:
                                for stat in data['interactionStatistic']:
                                    interaction_type = stat.get('interactionType', {}).get('@type', '')
                                    count = stat.get('userInteractionCount')
                                    
                                    if interaction_type == 'LikeAction' and count:
                                        details['json_ld_like_count'] = int(count)
                                    elif interaction_type == 'CommentAction' and count:
                                        details['json_ld_comment_count'] = int(count)
                                    elif interaction_type == 'ShareAction' and count:
                                        details['json_ld_share_count'] = int(count)
                                    elif interaction_type == 'WatchAction' and count:
                                        details['json_ld_view_count'] = int(count)
                        
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.logger.warning(f"JSON-LD抽出エラー: {e}")
        
        return details
    
    def _parse_count_string(self, count_str: str) -> Optional[int]:
        """カウント文字列を数値に変換"""
        try:
            count_str = count_str.upper().strip().replace(',', '').replace(' ', '')
            
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
        delay_between_requests: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        複数の動画の詳細情報を取得
        
        Args:
            video_urls: 動画URLのリスト
            delay_between_requests: リクエスト間の待機時間
            
        Returns:
            動画詳細情報のリスト
        """
        results = []
        
        for i, url in enumerate(video_urls):
            self.logger.info(f"動画 {i+1}/{len(video_urls)} を処理中: {url}")
            
            details = self.get_video_details(url)
            if details:
                results.append(details)
            
            # 最後以外は待機
            if i < len(video_urls) - 1:
                time.sleep(delay_between_requests)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            'success_rate': self.stats['successful_requests'] / max(self.stats['total_requests'], 1),
            'like_count_extraction_rate': self.stats['like_count_extracted'] / max(self.stats['videos_with_details'], 1),
            'comment_count_extraction_rate': self.stats['comment_count_extracted'] / max(self.stats['videos_with_details'], 1),
            'author_extraction_rate': self.stats['author_extracted'] / max(self.stats['videos_with_details'], 1)
        }


def test_meta_tag_scraper():
    """メタタグスクレイパーのテスト"""
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
    
    scraper = MetaTagVideoScraper(api_key)
    
    print("🔍 メタタグベース動画詳細スクレイパーのテスト開始")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n=== テスト {i}: {url} ===")
        
        details = scraper.get_video_details(url)
        
        if details:
            print("✅ 詳細情報取得成功")
            print(f"動画ID: {details.get('video_id', 'N/A')}")
            print(f"作者: {details.get('author_username', 'N/A')} ({details.get('author_display_name', 'N/A')})")
            print(f"いいね数: {details.get('like_count', 'N/A')}")
            print(f"コメント数: {details.get('comment_count', 'N/A')}")
            print(f"再生数: {details.get('view_count', 'N/A')}")
            print(f"タイトル: {details.get('video_title', details.get('og_title', 'N/A'))}")
            print(f"キーワード: {details.get('keywords', 'N/A')}")
            
            # 詳細情報をファイルに保存
            os.makedirs('debug', exist_ok=True)
            with open(f'debug/meta_tag_video_details_{details.get("video_id", i)}.json', 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
            print(f"詳細情報を保存: debug/meta_tag_video_details_{details.get('video_id', i)}.json")
        else:
            print("❌ 詳細情報取得失敗")
    
    # 統計情報を表示
    stats = scraper.get_stats()
    print(f"\n📊 統計情報:")
    print(f"総リクエスト数: {stats['total_requests']}")
    print(f"成功率: {stats['success_rate']:.2%}")
    print(f"いいね数抽出率: {stats['like_count_extraction_rate']:.2%}")
    print(f"コメント数抽出率: {stats['comment_count_extraction_rate']:.2%}")
    print(f"作者情報抽出率: {stats['author_extraction_rate']:.2%}")


if __name__ == "__main__":
    test_meta_tag_scraper()

