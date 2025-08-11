#!/usr/bin/env python3
"""
Simplified Integration Test for TikTok Research System
メタタグスクレイパーに焦点を当てた簡略化統合テスト
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import get_logger
from meta_tag_video_scraper import MetaTagVideoScraper


class SimplifiedIntegrationTest:
    """簡略化統合テストクラス"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # APIキーを取得
        self.api_key = os.getenv('SCRAPERAPI_KEY')
        if not self.api_key:
            raise ValueError("SCRAPERAPI_KEY環境変数が設定されていません")
        
        # メタタグスクレイパーを初期化
        self.meta_scraper = MetaTagVideoScraper(self.api_key)
        
        # テスト結果
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """包括的テストを実行"""
        self.logger.info("簡略化統合テストを開始")
        
        try:
            # テスト1: 単一動画詳細取得
            self.logger.info("テスト1: 単一動画詳細取得")
            single_result = self._test_single_video_detail()
            self.test_results['tests'].append(single_result)
            
            # テスト2: 複数動画詳細取得
            self.logger.info("テスト2: 複数動画詳細取得")
            multiple_result = self._test_multiple_video_details()
            self.test_results['tests'].append(multiple_result)
            
            # テスト3: エラーハンドリング
            self.logger.info("テスト3: エラーハンドリング")
            error_result = self._test_error_handling()
            self.test_results['tests'].append(error_result)
            
            # テスト4: パフォーマンス測定
            self.logger.info("テスト4: パフォーマンス測定")
            performance_result = self._test_performance_metrics()
            self.test_results['tests'].append(performance_result)
            
            # テスト5: データ品質検証
            self.logger.info("テスト5: データ品質検証")
            quality_result = self._test_data_quality()
            self.test_results['tests'].append(quality_result)
            
            # サマリーを生成
            self._generate_summary()
            
            self.test_results['end_time'] = datetime.now().isoformat()
            self.logger.info("簡略化統合テスト完了")
            
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"統合テスト実行エラー: {e}")
            self.test_results['error'] = str(e)
            return self.test_results
    
    def _test_single_video_detail(self) -> Dict[str, Any]:
        """単一動画詳細取得テスト"""
        test_result = {
            'test_name': 'single_video_detail',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'video_details': None,
            'error': None
        }
        
        try:
            test_url = "https://www.tiktok.com/@_quietlydope/video/7535094688726945079"
            
            start_time = time.time()
            details = self.meta_scraper.get_video_details(test_url)
            end_time = time.time()
            
            if details:
                test_result['success'] = True
                test_result['video_details'] = details
                test_result['processing_time'] = end_time - start_time
                
                # 必須フィールドの確認
                required_fields = ['video_id', 'like_count', 'comment_count', 'author_username']
                missing_fields = [field for field in required_fields if not details.get(field)]
                
                test_result['required_fields_present'] = len(missing_fields) == 0
                test_result['missing_fields'] = missing_fields
                
                self.logger.info(f"単一動画詳細取得成功: {details.get('video_id')}")
            else:
                test_result['error'] = "動画詳細の取得に失敗"
                
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"単一動画詳細取得テストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_multiple_video_details(self) -> Dict[str, Any]:
        """複数動画詳細取得テスト"""
        test_result = {
            'test_name': 'multiple_video_details',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'video_details': [],
            'success_count': 0,
            'failure_count': 0,
            'error': None
        }
        
        try:
            test_urls = [
                "https://www.tiktok.com/@_quietlydope/video/7535094688726945079",
                "https://www.tiktok.com/@ohnoitsrolo/video/7534370912854985997",
            ]
            
            start_time = time.time()
            video_details = self.meta_scraper.get_multiple_video_details(
                test_urls, 
                delay_between_requests=2.0
            )
            end_time = time.time()
            
            success_count = len(video_details)
            failure_count = len(test_urls) - success_count
            
            test_result['success'] = success_count > 0
            test_result['video_details'] = video_details
            test_result['success_count'] = success_count
            test_result['failure_count'] = failure_count
            test_result['success_rate'] = success_count / len(test_urls)
            test_result['total_processing_time'] = end_time - start_time
            test_result['average_processing_time'] = (end_time - start_time) / len(test_urls)
            
            self.logger.info(f"複数動画詳細取得: {success_count}/{len(test_urls)}件成功")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"複数動画詳細取得テストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """エラーハンドリングテスト"""
        test_result = {
            'test_name': 'error_handling',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'error_cases': [],
            'error': None
        }
        
        try:
            error_cases = []
            
            # 無効なURL
            invalid_url = "https://www.tiktok.com/invalid/url"
            try:
                details = self.meta_scraper.get_video_details(invalid_url)
                error_cases.append({
                    'case': 'invalid_url',
                    'handled_gracefully': details is None,
                    'result': 'success' if details is None else 'unexpected_success'
                })
            except Exception as e:
                error_cases.append({
                    'case': 'invalid_url',
                    'handled_gracefully': True,
                    'result': 'exception_caught',
                    'exception': str(e)
                })
            
            # 存在しない動画ID
            nonexistent_url = "https://www.tiktok.com/@test/video/9999999999999999999"
            try:
                details = self.meta_scraper.get_video_details(nonexistent_url)
                error_cases.append({
                    'case': 'nonexistent_video',
                    'handled_gracefully': details is None,
                    'result': 'success' if details is None else 'unexpected_success'
                })
            except Exception as e:
                error_cases.append({
                    'case': 'nonexistent_video',
                    'handled_gracefully': True,
                    'result': 'exception_caught',
                    'exception': str(e)
                })
            
            test_result['success'] = all(case['handled_gracefully'] for case in error_cases)
            test_result['error_cases'] = error_cases
            
            self.logger.info(f"エラーハンドリングテスト: {len(error_cases)}ケース実行")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"エラーハンドリングテストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_performance_metrics(self) -> Dict[str, Any]:
        """パフォーマンス測定テスト"""
        test_result = {
            'test_name': 'performance_metrics',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'metrics': {},
            'error': None
        }
        
        try:
            test_url = "https://www.tiktok.com/@_quietlydope/video/7535094688726945079"
            
            # 複数回実行して平均を取る
            execution_times = []
            success_count = 0
            
            for i in range(3):
                start_time = time.time()
                details = self.meta_scraper.get_video_details(test_url)
                end_time = time.time()
                
                execution_time = end_time - start_time
                execution_times.append(execution_time)
                
                if details:
                    success_count += 1
                
                # 次のリクエストまで待機
                if i < 2:
                    time.sleep(2)
            
            test_result['success'] = success_count > 0
            test_result['metrics'] = {
                'total_executions': len(execution_times),
                'successful_executions': success_count,
                'success_rate': success_count / len(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'average_execution_time': sum(execution_times) / len(execution_times),
                'execution_times': execution_times
            }
            
            self.logger.info(f"パフォーマンステスト: 平均{test_result['metrics']['average_execution_time']:.2f}秒")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"パフォーマンステストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
    def _test_data_quality(self) -> Dict[str, Any]:
        """データ品質検証テスト"""
        test_result = {
            'test_name': 'data_quality',
            'start_time': datetime.now().isoformat(),
            'success': False,
            'quality_metrics': {},
            'error': None
        }
        
        try:
            test_urls = [
                "https://www.tiktok.com/@_quietlydope/video/7535094688726945079",
                "https://www.tiktok.com/@ohnoitsrolo/video/7534370912854985997",
            ]
            
            quality_metrics = {
                'total_videos': 0,
                'videos_with_like_count': 0,
                'videos_with_comment_count': 0,
                'videos_with_author': 0,
                'videos_with_title': 0,
                'videos_with_keywords': 0,
                'like_count_range': {'min': float('inf'), 'max': 0},
                'comment_count_range': {'min': float('inf'), 'max': 0}
            }
            
            for url in test_urls:
                details = self.meta_scraper.get_video_details(url)
                
                if details:
                    quality_metrics['total_videos'] += 1
                    
                    if details.get('like_count'):
                        quality_metrics['videos_with_like_count'] += 1
                        like_count = details['like_count']
                        quality_metrics['like_count_range']['min'] = min(quality_metrics['like_count_range']['min'], like_count)
                        quality_metrics['like_count_range']['max'] = max(quality_metrics['like_count_range']['max'], like_count)
                    
                    if details.get('comment_count'):
                        quality_metrics['videos_with_comment_count'] += 1
                        comment_count = details['comment_count']
                        quality_metrics['comment_count_range']['min'] = min(quality_metrics['comment_count_range']['min'], comment_count)
                        quality_metrics['comment_count_range']['max'] = max(quality_metrics['comment_count_range']['max'], comment_count)
                    
                    if details.get('author_username'):
                        quality_metrics['videos_with_author'] += 1
                    
                    if details.get('video_title') or details.get('og_title'):
                        quality_metrics['videos_with_title'] += 1
                    
                    if details.get('keywords'):
                        quality_metrics['videos_with_keywords'] += 1
                
                time.sleep(2)  # リクエスト間隔
            
            # 品質スコアを計算
            total = quality_metrics['total_videos']
            if total > 0:
                quality_score = (
                    quality_metrics['videos_with_like_count'] +
                    quality_metrics['videos_with_comment_count'] +
                    quality_metrics['videos_with_author'] +
                    quality_metrics['videos_with_title']
                ) / (total * 4)  # 4つの主要フィールド
                
                quality_metrics['overall_quality_score'] = quality_score
                
                test_result['success'] = quality_score > 0.5  # 50%以上の品質
            
            test_result['quality_metrics'] = quality_metrics
            
            self.logger.info(f"データ品質テスト: 品質スコア{quality_metrics.get('overall_quality_score', 0):.2%}")
            
        except Exception as e:
            test_result['error'] = str(e)
            self.logger.error(f"データ品質テストエラー: {e}")
        
        test_result['end_time'] = datetime.now().isoformat()
        return test_result
    
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
        
        # スクレイパー統計を追加
        scraper_stats = self.meta_scraper.get_stats()
        self.test_results['scraper_stats'] = scraper_stats
    
    def save_test_results(self, filename: str = None):
        """テスト結果をファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simplified_integration_test_results_{timestamp}.json"
        
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
    print("🔧 TikTokリサーチシステム簡略化統合テスト開始")
    
    try:
        # 統合テストを実行
        test_runner = SimplifiedIntegrationTest()
        results = test_runner.run_comprehensive_test()
        
        # 結果を保存
        result_file = test_runner.save_test_results()
        
        # 結果を表示
        print("\n📊 統合テスト結果:")
        print(f"総テスト数: {results['summary']['total_tests']}")
        print(f"成功テスト数: {results['summary']['successful_tests']}")
        print(f"失敗テスト数: {results['summary']['failed_tests']}")
        print(f"成功率: {results['summary']['success_rate']:.2%}")
        print(f"総合ステータス: {results['summary']['overall_status']}")
        
        # スクレイパー統計
        if 'scraper_stats' in results:
            stats = results['scraper_stats']
            print(f"\n📈 スクレイパー統計:")
            print(f"総リクエスト数: {stats['total_requests']}")
            print(f"成功率: {stats['success_rate']:.2%}")
            print(f"いいね数抽出率: {stats['like_count_extraction_rate']:.2%}")
            print(f"コメント数抽出率: {stats['comment_count_extraction_rate']:.2%}")
        
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

