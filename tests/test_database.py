"""
Tests for database module
"""

import unittest
import tempfile
import os
from datetime import datetime, timedelta

from src.storage.database import DatabaseManager
from src.parser.video_data import VideoData, VideoCollection


class TestDatabaseManager(unittest.TestCase):
    """データベースマネージャーのテストクラス"""
    
    def setUp(self):
        """テストセットアップ"""
        # 一時データベースファイルを作成
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db = DatabaseManager(db_path=self.temp_db.name)
        
        # テスト用動画データを作成
        self.test_video = VideoData(
            video_id="test123",
            url="https://tiktok.com/test123",
            title="Test Video",
            description="Test Description",
            author_username="testuser",
            author_display_name="Test User",
            author_verified=True,
            view_count=1000000,
            like_count=50000,
            comment_count=1000,
            upload_date=datetime.now() - timedelta(hours=12),
            hashtags=["test", "video"],
            mentions=["user1", "user2"]
        )
    
    def tearDown(self):
        """テストクリーンアップ"""
        # 一時ファイルを削除
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_save_and_get_video(self):
        """動画保存・取得のテスト"""
        # 動画を保存
        success = self.db.save_video(self.test_video)
        self.assertTrue(success)
        
        # 動画を取得
        retrieved_video = self.db.get_video("test123")
        self.assertIsNotNone(retrieved_video)
        self.assertEqual(retrieved_video.video_id, "test123")
        self.assertEqual(retrieved_video.title, "Test Video")
        self.assertEqual(retrieved_video.view_count, 1000000)
        self.assertEqual(len(retrieved_video.hashtags), 2)
        self.assertIn("test", retrieved_video.hashtags)
    
    def test_search_videos(self):
        """動画検索のテスト"""
        # 複数の動画を保存
        videos = [
            self.test_video,
            VideoData(
                video_id="test456",
                url="https://tiktok.com/test456",
                title="Another Video",
                view_count=300000,
                upload_date=datetime.now() - timedelta(hours=36)
            )
        ]
        
        for video in videos:
            self.db.save_video(video)
        
        # 再生数でフィルタリング
        results = self.db.search_videos(min_views=500000)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].video_id, "test123")
        
        # 日時でフィルタリング
        start_date = datetime.now() - timedelta(hours=24)
        results = self.db.search_videos(start_date=start_date)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].video_id, "test123")
    
    def test_save_collection(self):
        """コレクション保存のテスト"""
        collection = VideoCollection(
            videos=[self.test_video],
            source="test_collection",
            total_count=1
        )
        
        collection_id = self.db.save_collection(collection)
        self.assertIsNotNone(collection_id)
        self.assertTrue(collection_id.startswith("collection_"))
    
    def test_get_statistics(self):
        """統計取得のテスト"""
        # 動画を保存
        self.db.save_video(self.test_video)
        
        stats = self.db.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['total_videos'], 1)
        self.assertIn('today_videos', stats)
        self.assertIn('popular_hashtags', stats)
    
    def test_cleanup_old_data(self):
        """古いデータ削除のテスト"""
        # 古い動画データを作成
        old_video = VideoData(
            video_id="old123",
            url="https://tiktok.com/old123",
            title="Old Video",
            collected_at=datetime.now() - timedelta(days=35)
        )
        
        # 動画を保存
        self.db.save_video(self.test_video)  # 新しい動画
        self.db.save_video(old_video)  # 古い動画
        
        # 30日以前のデータを削除
        deleted_count = self.db.cleanup_old_data(days=30)
        self.assertEqual(deleted_count, 1)
        
        # 新しい動画は残っているかチェック
        remaining_video = self.db.get_video("test123")
        self.assertIsNotNone(remaining_video)
        
        # 古い動画は削除されているかチェック
        deleted_video = self.db.get_video("old123")
        self.assertIsNone(deleted_video)


if __name__ == '__main__':
    unittest.main()

