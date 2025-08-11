#!/usr/bin/env python3
"""
Integrated System Test for TikTok Research System
既存システムとメタタグスクレイパーの統合テスト
"""

import os
import sys
import json
import time
import csv
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import get_logger
from src.utils.config import Config
from src.scraper.tiktok_scraper import TikTokScraper
from src.parser.tiktok_parser import TikTokParser
from src.storage.database import DatabaseManager
from src.filter.video_filter import VideoFilter
from meta_tag_video_scraper import MetaTagVideoScraper


class IntegratedSystemTest:
    """統合システムテストクラス"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.config = Config()
        
        # APIキーを取得
        self.api_key = os.getenv('SCRAPERAPI_KEY')
        if not self.api_key:
            raise ValueError("SCRAPERAPI_KEY環境変数が設定されていません")
        
        # コンポーネントを初期化
        self.tiktok_scraper = TikTokScraper(self.api_key)
        self.parser = TikTokParser()
        self.database = DatabaseManager()
        self.filter = VideoFilter()
        self.meta_scraper = MetaTagVideoScraper(self.api_key)
        
        # テスト結果
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
    
    def run_full_integration_test(self) -> Dict[str, Any]:
        """完全統合テストを実行"""
        self.logger.info("統合システムテストを開始")
        
        try:
            # テスト1: 探索ページからの動画URL収集
            self.logger.info("テスト1: 探索ページからの動画URL収集")
            explore_result = self._test_explore_scraping()
            self.test_results['tests'].append(explore_result)
            
            # テスト2: 個別動画詳細情報取得
            if explore_result['success'] and explore_result['video_urls']:
                self.logger.info("テスト2: 個別動画詳細情報取得")
                detail_result = self._test_video_detail_scraping(explore_result['video_urls'][:5])
                self.test_results['tests'].append(detail_result)
                
                # テスト3: データベース保存とフィルタリング
                if detail_result['success'] and detail_result['video_details']:
                    self.logger.info("テスト3: データベース保存とフィルタリング")
                    db_result = self._test_database_operations(detail_result['video_details'])
                    self.test_results['tests'].append(db_result)
                    
                    # テスト4: フィルタリング機能
                    self.logger.info("テスト4: フィルタリング機能")
                    filter_result = self._test_filtering(detail_result['video_details'])
                    self.test_results['tests'].append(filter_result)
            
            # テスト5: パフォーマンステスト
            self.logger.info("テスト5: パフォーマンステスト")
            performance_result = self._test_performance()
            self.test_results['tests'].append(performance_result)
            
            # サマリーを生成
            self._generate_summary()
            
            self.test_results['end_time'] = datetime.now().isoformat()
            self.logger.info("統合システムテスト完了")
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"統合テスト実行エラー: {e}")
            self.test_results['error'] = str(e)
            return self.test_results
    
    def _test_explore_scraping(self) -> Dict[str, Any]:
        """探索ページからの動画URL収集テスト"""
        test_result = {
            'test_name': 'explore_scraping',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'video_urls': [],
            'error': None
        }
        
        try:
            # 探索ページをスクレイピング
            explore_url = "https://www.tiktok.com/explore"
            video_collection = self.tiktok_scraper.scrape_explore_page()
            
            if video_collection and video_collection.videos:
                # 動画URLを抽出
                video_urls = [video.url for video in video_collection.videos if video.url]
                
                test_result['success'] = len(video_urls) > 0
                test_result['video_urls'] = video_urls[:20]  # 最大20個
                test_result['total_urls_found'] = len(video_urls)
                
                self.logger.info(f"探索ページから{len(video_urls)}個の動画URLを取得")
            else:
                test_result['error'] = "探索ページのスクレイピングに失敗"
                
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"探索スクレイピングテストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_video_detail_scraping(self, video_urls: List[str]) -> Dict[str, Any]:
        """個別動画詳細情報取得テスト"""
        test_result = {
            'test_name': 'video_detail_scraping',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'video_details': [],
            'success_count': 0,
            'failure_count': 0,
            'error': None
        }
        
        try:
            video_details = []
            success_count = 0
            failure_count = 0
            
            for i, url in enumerate(video_urls[:5]):  # 最大5個をテスト
                self.logger.info(f"動画詳細取得 {i+1}/{min(len(video_urls), 5)}: {url}")
                
                try:
                    details = self.meta_scraper.get_video_details(url)
                    
                    if details:
                        video_details.append(details)
                        success_count += 1
                        self.logger.info(f"詳細取得成功: {details.get('video_id', 'N/A')}")
                    else:
                        failure_count += 1
                        self.logger.warning(f"詳細取得失敗: {url}")
                    
                    # リクエスト間隔を空ける
                    if i < len(video_urls) - 1:
                        time.sleep(3)
                        
                except Exception as e:
                    failure_count += 1
                    self.logger.error(f"動画詳細取得エラー: {e}")
            
            test_result['success'] = success_count > 0
            test_result['video_details'] = video_details
            test_result['success_count'] = success_count
            test_result['failure_count'] = failure_count
            test_result['success_rate'] = success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"動画詳細スクレイピングテストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_database_operations(self, video_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データベース操作テスト"""
        test_result = {
            'test_name': 'database_operations',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'saved_count': 0,
            'retrieved_count': 0,
            'error': None
        }
        
        try:
            # データベースは既に初期化済み
            
            saved_count = 0
            
            # 動画データを保存
            for details in video_details:
                try:
                    video_data = self._convert_to_video_data(details)
                    self.database.save_video(video_data)
                    saved_count += 1
                except Exception as e:
                    self.logger.warning(f"動画保存エラー: {e}")
            
            # データベースから取得
            retrieved_videos = self.database.get_recent_videos(limit=100)
            retrieved_count = len(retrieved_videos)
            
            test_result['success'] = saved_count > 0 and retrieved_count > 0
            test_result['saved_count'] = saved_count
            test_result['retrieved_count'] = retrieved_count
            
            self.logger.info(f"データベーステスト: {saved_count}件保存, {retrieved_count}件取得")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"データベース操作テストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_filtering(self, video_details: List[Dict[str, Any]]) -> Dict[str, Any]:
        """フィルタリング機能テスト"""
        test_result = {
            'test_name': 'filtering',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'original_count': 0,
            'filtered_count': 0,
            'error': None
        }
        
        try:
            original_count = len(video_details)
            
            # フィルタリング条件を設定
            filter_criteria = {
                'min_views': 100000,  # 最小再生数10万
                'min_likes': 1000,    # 最小いいね数1000
                'time_range_hours': 24  # 24時間以内
            }
            
            filtered_videos = []
            
            for details in video_details:
                video_data = self._convert_to_video_data(details)
                
                if self.filter.should_include_video(video_data, filter_criteria):
                    filtered_videos.append(details)
            
            filtered_count = len(filtered_videos)
            
            test_result['success'] = True  # フィルタリング自体は成功
            test_result['original_count'] = original_count
            test_result['filtered_count'] = filtered_count
            test_result['filter_rate'] = filtered_count / original_count if original_count > 0 else 0
            
            self.logger.info(f"フィルタリングテスト: {original_count}件 -> {filtered_count}件")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"フィルタリングテストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_performance(self) -> Dict[str, Any]:
        """パフォーマンステスト"""
        test_result = {
            'test_name': 'performance',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'metrics': {},
            'error': None
        }
        
        try:
            # テスト用動画URL
            test_url = "https://www.tiktok.com/@_quietlydope/video/7535094688726945079"
            
            # 処理時間を測定
            start_time = time.time()
            details = self.meta_scraper.get_video_details(test_url)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            test_result['success'] = details is not None
            test_result['metrics'] = {
                'processing_time_seconds': processing_time,
                'data_extracted': bool(details),
                'like_count_extracted': bool(details and details.get('like_count')),
                'comment_count_extracted': bool(details and details.get('comment_count')),
                'author_extracted': bool(details and details.get('author_username'))
            }
            
            self.logger.info(f"パフォーマンステスト: {processing_time:.2f}秒で処理完了")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"パフォーマンステストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _convert_to_video_data(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """詳細情報をVideoDataフォーマットに変換"""
        return {
            'video_id': details.get('video_id'),
            'url': details.get('url'),
            'title': details.get('video_title', details.get('og_title', '')),
            'description': details.get('meta_description', ''),
            'author_username': details.get('author_username'),
            'author_display_name': details.get('author_display_name'),
            'view_count': details.get('view_count', 0),
            'like_count': details.get('like_count', 0),
            'comment_count': details.get('comment_count', 0),
            'share_count': details.get('share_count', 0),
            'create_time': details.get('create_time'),
            'scraped_at': details.get('scraped_at'),
            'keywords': details.get('keywords', []),
            'hashtags': details.get('hashtags', ''),
            'extraction_method': details.get('extraction_method', 'meta_tag_based')
        }
    
    def _generate_summary(self):
        """テスト結果のサマリーを生成"""
        total_tests = len(self.test_results['tests'])
        successful_tests = sum(1 for test in self.test_results['tests'] if test['success'])
        
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
            'overall_status': 'PASS' if successful_tests == total_tests else 'PARTIAL' if successful_tests > 0 else 'FAIL'
        }
    
    def save_test_results(self, filename: str = None):
        """テスト結果をファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"テスト結果を保存: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"テスト結果保存エラー: {e}")
            return None


def main():
    """メイン関数"""
    print("🔧 TikTokリサーチシステム統合テスト開始")
    
    try:
        # 統合テストを実行
        test_runner = IntegratedSystemTest()
        results = test_runner.run_full_integration_test()
        
        # 結果を保存
        result_file = test_runner.save_test_results()
        
        # 結果を表示
        print("\n📊 統合テスト結果:")
        print(f"総テスト数: {results['summary']['total_tests']}")
        print(f"成功テスト数: {results['summary']['successful_tests']}")
        print(f"失敗テスト数: {results['summary']['failed_tests']}")
        print(f"成功率: {results['summary']['success_rate']:.2%}")
        print(f"総合ステータス: {results['summary']['overall_status']}")
        
        if result_file:
            print(f"\n詳細結果ファイル: {result_file}")
        
        # 個別テスト結果
        print("\n📋 個別テスト結果:")
        for test in results['tests']:
            status = "✅ PASS" if test['success'] else "❌ FAIL"
            print(f"{status} {test['test_name']}")
            if test.get('error'):
                print(f"   エラー: {test['error']}")
        
        return results['summary']['overall_status'] == 'PASS'
        
    except Exception as e:
        print(f"❌ 統合テスト実行エラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

