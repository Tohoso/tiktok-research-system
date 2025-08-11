#!/usr/bin/env python3
"""
Explore Page Video Batch Processor
/exploreページから取得した動画URLの詳細情報を一括取得
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
from meta_tag_video_scraper import MetaTagVideoScraper


class ExploreBatchProcessor:
    """Exploreページ動画のバッチ処理クラス"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # APIキーを取得
        self.api_key = os.getenv('SCRAPERAPI_KEY')
        if not self.api_key:
            raise ValueError("SCRAPERAPI_KEY環境変数が設定されていません")
        
        # メタタグスクレイパーを初期化
        self.meta_scraper = MetaTagVideoScraper(self.api_key)
        
        # 処理結果
        self.results = {
            'start_time': datetime.now().isoformat(),
            'source': 'tiktok_explore_page',
            'processed_videos': [],
            'failed_videos': [],
            'summary': {}
        }
    
    def load_video_urls(self, filename: str = 'explore_video_urls.txt') -> List[str]:
        """動画URLファイルを読み込み"""
        urls = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('https://www.tiktok.com/') and '/video/' in line:
                        urls.append(line)
            
            self.logger.info(f"動画URL読み込み完了: {len(urls)}件")
            return urls
            
        except Exception as e:
            self.logger.error(f"動画URL読み込みエラー: {e}")
            return []
    
    def process_videos_batch(self, urls: List[str], max_videos: int = 30) -> Dict[str, Any]:
        """動画の一括処理"""
        self.logger.info(f"バッチ処理開始: {len(urls)}件の動画")
        
        try:
            print(f"🚀 /exploreページ動画の詳細情報取得開始")
            print(f"対象動画数: {min(len(urls), max_videos)}件")
            print("=" * 60)
            
            processed_count = 0
            failed_count = 0
            
            for i, url in enumerate(urls[:max_videos], 1):
                try:
                    print(f"\n📹 動画 {i}/{min(len(urls), max_videos)}: {url}")
                    print(f"   ⏳ 詳細情報を取得中...")
                    
                    start_time = time.time()
                    details = self.meta_scraper.get_video_details(url)
                    end_time = time.time()
                    
                    processing_time = end_time - start_time
                    
                    if details:
                        # 成功した場合
                        video_data = {
                            'url': url,
                            'video_id': details.get('video_id'),
                            'author_username': details.get('author_username'),
                            'like_count': details.get('like_count'),
                            'comment_count': details.get('comment_count'),
                            'title': details.get('og_title', ''),
                            'description': details.get('description', ''),
                            'keywords': details.get('keywords', ''),
                            'processing_time': processing_time,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.results['processed_videos'].append(video_data)
                        processed_count += 1
                        
                        print(f"   ✅ 成功 ({processing_time:.1f}秒)")
                        print(f"   動画ID: {details.get('video_id')}")
                        print(f"   作者: @{details.get('author_username')}")
                        if details.get('like_count'):
                            print(f"   いいね数: {details.get('like_count'):,}")
                        if details.get('comment_count'):
                            print(f"   コメント数: {details.get('comment_count'):,}")
                        
                    else:
                        # 失敗した場合
                        failed_data = {
                            'url': url,
                            'error': '詳細情報の取得に失敗',
                            'processing_time': processing_time,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        self.results['failed_videos'].append(failed_data)
                        failed_count += 1
                        
                        print(f"   ❌ 失敗: 詳細情報の取得に失敗")
                    
                    # 進捗表示
                    success_rate = processed_count / i * 100
                    print(f"   進捗: {i}/{min(len(urls), max_videos)} ({success_rate:.1f}%成功)")
                    
                    # API制限を考慮した待機
                    if i < min(len(urls), max_videos):
                        print(f"   ⏳ 次の動画まで待機中...")
                        time.sleep(2)  # 2秒待機
                    
                except Exception as e:
                    # エラーが発生した場合
                    failed_data = {
                        'url': url,
                        'error': str(e),
                        'processing_time': 0,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    self.results['failed_videos'].append(failed_data)
                    failed_count += 1
                    
                    print(f"   ❌ エラー: {e}")
                    self.logger.error(f"動画処理エラー {url}: {e}")
            
            # サマリーを生成
            self._generate_summary()
            
            # 結果を表示
            self._display_results()
            
            self.results['end_time'] = datetime.now().isoformat()
            self.logger.info(f"バッチ処理完了: 成功{processed_count}件、失敗{failed_count}件")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"バッチ処理エラー: {e}")
            self.results['error'] = str(e)
            return self.results
    
    def _generate_summary(self):
        """処理結果のサマリーを生成"""
        total_processed = len(self.results['processed_videos'])
        total_failed = len(self.results['failed_videos'])
        total_attempts = total_processed + total_failed
        
        self.results['summary'] = {
            'total_attempts': total_attempts,
            'successful_extractions': total_processed,
            'failed_extractions': total_failed,
            'success_rate': total_processed / total_attempts if total_attempts > 0 else 0,
            'average_processing_time': self._calculate_average_processing_time(),
            'unique_authors': len(set(video.get('author_username') for video in self.results['processed_videos'] if video.get('author_username'))),
            'total_likes': sum(video.get('like_count', 0) for video in self.results['processed_videos']),
            'total_comments': sum(video.get('comment_count', 0) for video in self.results['processed_videos'] if video.get('comment_count'))
        }
    
    def _calculate_average_processing_time(self) -> float:
        """平均処理時間を計算"""
        processing_times = [video.get('processing_time', 0) for video in self.results['processed_videos']]
        return sum(processing_times) / len(processing_times) if processing_times else 0
    
    def _display_results(self):
        """結果を表示"""
        print("\n" + "=" * 60)
        print("📊 /exploreページ動画バッチ処理結果")
        print("=" * 60)
        
        summary = self.results['summary']
        
        print(f"総処理数: {summary['total_attempts']}")
        print(f"成功: {summary['successful_extractions']}件")
        print(f"失敗: {summary['failed_extractions']}件")
        print(f"成功率: {summary['success_rate']:.2%}")
        print(f"平均処理時間: {summary['average_processing_time']:.1f}秒")
        print(f"ユニーク作者数: {summary['unique_authors']}")
        print(f"総いいね数: {summary['total_likes']:,}")
        print(f"総コメント数: {summary['total_comments']:,}")
        
        if self.results['processed_videos']:
            print("\n🏆 トップパフォーマー:")
            sorted_videos = sorted(
                self.results['processed_videos'], 
                key=lambda x: x.get('like_count', 0), 
                reverse=True
            )
            for i, video in enumerate(sorted_videos[:5], 1):
                author = video.get('author_username', 'Unknown')
                likes = video.get('like_count', 0)
                print(f"{i}. @{author}: {likes:,}いいね")
    
    def save_results(self, filename: str = None) -> str:
        """結果をJSONファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"explore_batch_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 詳細結果を保存: {filename}")
            self.logger.info(f"結果保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 結果保存エラー: {e}")
            self.logger.error(f"結果保存エラー: {e}")
            return ""
    
    def save_csv(self, filename: str = None) -> str:
        """結果をCSVファイルに保存"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"explore_videos_{timestamp}.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'video_id', 'author_username', 'like_count', 'comment_count', 
                    'title', 'description', 'keywords', 'url', 'processing_time'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for video in self.results['processed_videos']:
                    writer.writerow({
                        'video_id': video.get('video_id', ''),
                        'author_username': video.get('author_username', ''),
                        'like_count': video.get('like_count', 0),
                        'comment_count': video.get('comment_count', 0),
                        'title': video.get('title', ''),
                        'description': video.get('description', ''),
                        'keywords': video.get('keywords', ''),
                        'url': video.get('url', ''),
                        'processing_time': video.get('processing_time', 0)
                    })
            
            print(f"📊 CSV出力完了: {filename}")
            self.logger.info(f"CSV保存: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ CSV保存エラー: {e}")
            self.logger.error(f"CSV保存エラー: {e}")
            return ""


def main():
    """メイン関数"""
    print("🚀 TikTok /exploreページ動画バッチ処理")
    print("取得した動画URLから詳細情報を一括取得します")
    print("=" * 60)
    
    try:
        # バッチプロセッサーを初期化
        processor = ExploreBatchProcessor()
        
        # 動画URLを読み込み
        urls = processor.load_video_urls()
        if not urls:
            print("❌ 動画URLが見つかりません")
            return False
        
        print(f"📋 読み込み完了: {len(urls)}件の動画URL")
        
        # バッチ処理を実行
        results = processor.process_videos_batch(urls, max_videos=30)
        
        # 結果を保存
        json_file = processor.save_results()
        csv_file = processor.save_csv()
        
        # 最終評価
        summary = results['summary']
        success_rate = summary['success_rate']
        
        print(f"\n🎯 最終評価:")
        if success_rate >= 0.8:
            print("🟢 優秀 - 高い成功率で処理完了")
        elif success_rate >= 0.6:
            print("🟡 良好 - 概ね成功")
        else:
            print("🟠 要改善 - 成功率が低い")
        
        print(f"成功率: {success_rate:.2%}")
        print(f"処理完了: {summary['successful_extractions']}/{summary['total_attempts']}件")
        
        if json_file:
            print(f"詳細結果: {json_file}")
        if csv_file:
            print(f"CSV出力: {csv_file}")
        
        return success_rate >= 0.5
        
    except Exception as e:
        print(f"❌ バッチ処理実行エラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

