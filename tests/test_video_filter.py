"""
Tests for video filter module
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.filter.video_filter import VideoFilter
from src.parser.video_data import VideoData


class TestVideoFilter(unittest.TestCase):
    """動画フィルターのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        self.filter = VideoFilter()
        
        # テスト用動画データを作成
        self.test_videos = [
            VideoData(
                video_id="test1",
                url="https://tiktok.com/test1",
                title="Test Video 1",
                view_count=1000000,
                like_count=50000,  # エンゲージメント情報を追加
                comment_count=1000,
                upload_date=datetime.now() - timedelta(hours=12),
                author_username="user1",
                author_verified=True
            ),
            VideoData(
                video_id="test2",
                url="https://tiktok.com/test2",
                title="Test Video 2",
                view_count=300000,
                like_count=15000,  # エンゲージメント情報を追加
                comment_count=500,
                upload_date=datetime.now() - timedelta(hours=36),
                author_username="user2",
                author_verified=False
            ),
            VideoData(
                video_id="test3",
                url="https://tiktok.com/test3",
                title="Test Video 3",
                view_count=800000,
                like_count=40000,  # エンゲージメント情報を追加
                comment_count=800,
                upload_date=datetime.now() - timedelta(hours=6),
                author_username="user1",
                author_verified=True
            )
        ]
    
    def test_filter_by_views(self):
        """再生数フィルタリングのテスト"""
        # 50万再生以上でフィルタリング
        filtered = self.filter.filter_by_views(self.test_videos, min_views=500000)
        
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.test_videos[0], filtered)  # 100万再生
        self.assertIn(self.test_videos[2], filtered)  # 80万再生
        self.assertNotIn(self.test_videos[1], filtered)  # 30万再生
    
    def test_filter_by_date(self):
        """日時フィルタリングのテスト"""
        # 24時間以内でフィルタリング
        filtered = self.filter.filter_by_date(self.test_videos, hours_ago=24)
        
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.test_videos[0], filtered)  # 12時間前
        self.assertIn(self.test_videos[2], filtered)  # 6時間前
        self.assertNotIn(self.test_videos[1], filtered)  # 36時間前
    
    def test_filter_by_author(self):
        """作成者フィルタリングのテスト"""
        # 認証済みアカウントのみ
        filtered = self.filter.filter_by_author(self.test_videos, verified_only=True)
        
        self.assertEqual(len(filtered), 2)
        self.assertIn(self.test_videos[0], filtered)
        self.assertIn(self.test_videos[2], filtered)
        self.assertNotIn(self.test_videos[1], filtered)
    
    def test_remove_duplicates(self):
        """重複除去のテスト"""
        # 重複データを追加
        duplicate_videos = self.test_videos + [self.test_videos[0]]
        
        unique = self.filter.remove_duplicates(duplicate_videos)
        
        self.assertEqual(len(unique), 3)
        self.assertEqual(len(duplicate_videos), 4)
    
    def test_apply_trending_filter(self):
        """トレンドフィルターのテスト"""
        filtered = self.filter.apply_trending_filter(
            self.test_videos,
            min_views=500000,
            hours_ago=24
        )
        
        # 50万再生以上かつ24時間以内の動画
        self.assertEqual(len(filtered), 2)
        
        # 再生数順にソートされているかチェック
        if len(filtered) > 1:
            self.assertGreaterEqual(filtered[0].view_count, filtered[1].view_count)
    
    def test_get_filter_statistics(self):
        """フィルター統計のテスト"""
        filtered = self.filter.filter_by_views(self.test_videos, min_views=500000)
        stats = self.filter.get_filter_statistics(self.test_videos, filtered)
        
        self.assertEqual(stats['original_count'], 3)
        self.assertEqual(stats['filtered_count'], 2)
        self.assertEqual(stats['removed_count'], 1)
        self.assertAlmostEqual(stats['filter_rate'], 2/3, places=2)


if __name__ == '__main__':
    unittest.main()

