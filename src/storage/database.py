"""
Database management for TikTok Research System
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

from ..utils.logger import get_logger
from ..utils.config import config
from ..parser.video_data import VideoData, VideoCollection


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "data/tiktok_videos.db"):
        """
        データベースマネージャーを初期化
        
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.logger = get_logger(self.__class__.__name__)
        
        # データベースディレクトリを作成
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # データベースを初期化
        self._initialize_database()
        
        self.logger.info(f"データベースを初期化: {self.db_path}")
    
    def _initialize_database(self):
        """データベーステーブルを初期化"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 動画テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    
                    -- 作成者情報
                    author_username TEXT,
                    author_display_name TEXT,
                    author_follower_count INTEGER,
                    author_verified BOOLEAN,
                    
                    -- 統計情報
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    share_count INTEGER,
                    
                    -- 時間情報
                    upload_date TIMESTAMP,
                    duration INTEGER,
                    
                    -- メディア情報
                    thumbnail_url TEXT,
                    video_url TEXT,
                    music_title TEXT,
                    music_author TEXT,
                    
                    -- 地域・言語情報
                    region TEXT,
                    language TEXT,
                    
                    -- メタデータ
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_page TEXT,
                    raw_data TEXT,
                    
                    -- インデックス用
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ハッシュタグテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hashtags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    hashtag TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id),
                    UNIQUE(video_id, hashtag)
                )
            ''')
            
            # メンションテーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    mention TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id),
                    UNIQUE(video_id, mention)
                )
            ''')
            
            # 収集履歴テーブル
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collection_id TEXT NOT NULL,
                    source TEXT,
                    total_count INTEGER,
                    filtered_count INTEGER,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # インデックスを作成
            self._create_indexes(cursor)
            
            conn.commit()
    
    def _create_indexes(self, cursor):
        """インデックスを作成"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_videos_video_id ON videos(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_videos_upload_date ON videos(upload_date)",
            "CREATE INDEX IF NOT EXISTS idx_videos_view_count ON videos(view_count)",
            "CREATE INDEX IF NOT EXISTS idx_videos_collected_at ON videos(collected_at)",
            "CREATE INDEX IF NOT EXISTS idx_videos_author_username ON videos(author_username)",
            "CREATE INDEX IF NOT EXISTS idx_hashtags_video_id ON hashtags(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_hashtags_hashtag ON hashtags(hashtag)",
            "CREATE INDEX IF NOT EXISTS idx_mentions_video_id ON mentions(video_id)",
            "CREATE INDEX IF NOT EXISTS idx_collection_history_collected_at ON collection_history(collected_at)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    @contextmanager
    def _get_connection(self):
        """データベース接続のコンテキストマネージャー"""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_video(self, video: VideoData) -> bool:
        """
        動画データを保存
        
        Args:
            video: 動画データ
            
        Returns:
            保存成功かどうか
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 動画データを挿入または更新
                cursor.execute('''
                    INSERT OR REPLACE INTO videos (
                        video_id, url, title, description,
                        author_username, author_display_name, author_follower_count, author_verified,
                        view_count, like_count, comment_count, share_count,
                        upload_date, duration,
                        thumbnail_url, video_url, music_title, music_author,
                        region, language,
                        collected_at, source_page, raw_data,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video.video_id, video.url, video.title, video.description,
                    video.author_username, video.author_display_name, video.author_follower_count, video.author_verified,
                    video.view_count, video.like_count, video.comment_count, video.share_count,
                    video.upload_date, video.duration,
                    video.thumbnail_url, video.video_url, video.music_title, video.music_author,
                    video.region, video.language,
                    video.collected_at, video.source_page, json.dumps(video.raw_data),
                    datetime.now()
                ))
                
                # ハッシュタグを保存
                self._save_hashtags(cursor, video.video_id, video.hashtags)
                
                # メンションを保存
                self._save_mentions(cursor, video.video_id, video.mentions)
                
                conn.commit()
                
                self.logger.debug(f"動画データを保存: {video.video_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"動画データ保存エラー ({video.video_id}): {e}")
            return False
    
    def _save_hashtags(self, cursor, video_id: str, hashtags: List[str]):
        """ハッシュタグを保存"""
        # 既存のハッシュタグを削除
        cursor.execute("DELETE FROM hashtags WHERE video_id = ?", (video_id,))
        
        # 新しいハッシュタグを挿入
        for hashtag in hashtags:
            cursor.execute(
                "INSERT OR IGNORE INTO hashtags (video_id, hashtag) VALUES (?, ?)",
                (video_id, hashtag)
            )
    
    def _save_mentions(self, cursor, video_id: str, mentions: List[str]):
        """メンションを保存"""
        # 既存のメンションを削除
        cursor.execute("DELETE FROM mentions WHERE video_id = ?", (video_id,))
        
        # 新しいメンションを挿入
        for mention in mentions:
            cursor.execute(
                "INSERT OR IGNORE INTO mentions (video_id, mention) VALUES (?, ?)",
                (video_id, mention)
            )
    
    def save_collection(self, collection: VideoCollection) -> str:
        """
        動画コレクションを保存
        
        Args:
            collection: 動画コレクション
            
        Returns:
            コレクションID
        """
        collection_id = f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 各動画を保存
            saved_count = 0
            for video in collection.videos:
                if self.save_video(video):
                    saved_count += 1
            
            # 収集履歴を保存
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO collection_history (
                        collection_id, source, total_count, filtered_count, metadata
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    collection_id,
                    collection.source,
                    collection.total_count,
                    saved_count,
                    json.dumps({
                        'collected_at': collection.collected_at.isoformat(),
                        'source': collection.source
                    })
                ))
                conn.commit()
            
            self.logger.info(f"コレクションを保存: {collection_id} ({saved_count}/{collection.total_count} 件)")
            return collection_id
            
        except Exception as e:
            self.logger.error(f"コレクション保存エラー: {e}")
            return ""
    
    def get_video(self, video_id: str) -> Optional[VideoData]:
        """
        動画データを取得
        
        Args:
            video_id: 動画ID
            
        Returns:
            動画データ
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 動画データを取得
                cursor.execute("SELECT * FROM videos WHERE video_id = ?", (video_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # ハッシュタグを取得
                cursor.execute("SELECT hashtag FROM hashtags WHERE video_id = ?", (video_id,))
                hashtags = [r[0] for r in cursor.fetchall()]
                
                # メンションを取得
                cursor.execute("SELECT mention FROM mentions WHERE video_id = ?", (video_id,))
                mentions = [r[0] for r in cursor.fetchall()]
                
                # VideoDataオブジェクトを作成
                video = self._row_to_video_data(row, hashtags, mentions)
                return video
                
        except Exception as e:
            self.logger.error(f"動画データ取得エラー ({video_id}): {e}")
            return None
    
    def search_videos(
        self,
        min_views: Optional[int] = None,
        max_views: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        author_username: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[VideoData]:
        """
        動画データを検索
        
        Args:
            min_views: 最小再生数
            max_views: 最大再生数
            start_date: 開始日時
            end_date: 終了日時
            author_username: 作成者ユーザー名
            hashtags: ハッシュタグリスト
            limit: 取得件数制限
            offset: オフセット
            
        Returns:
            動画データリスト
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # クエリを構築
                query = "SELECT DISTINCT v.* FROM videos v"
                conditions = []
                params = []
                
                # ハッシュタグ検索の場合はJOIN
                if hashtags:
                    query += " JOIN hashtags h ON v.video_id = h.video_id"
                    hashtag_conditions = " OR ".join(["h.hashtag = ?"] * len(hashtags))
                    conditions.append(f"({hashtag_conditions})")
                    params.extend(hashtags)
                
                # 条件を追加
                if min_views is not None:
                    conditions.append("v.view_count >= ?")
                    params.append(min_views)
                
                if max_views is not None:
                    conditions.append("v.view_count <= ?")
                    params.append(max_views)
                
                if start_date:
                    conditions.append("v.upload_date >= ?")
                    params.append(start_date)
                
                if end_date:
                    conditions.append("v.upload_date <= ?")
                    params.append(end_date)
                
                if author_username:
                    conditions.append("v.author_username = ?")
                    params.append(author_username)
                
                # WHERE句を追加
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                # ORDER BY と LIMIT を追加
                query += " ORDER BY v.view_count DESC, v.upload_date DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # VideoDataオブジェクトに変換
                videos = []
                for row in rows:
                    video_id = row['video_id']
                    
                    # ハッシュタグとメンションを取得
                    cursor.execute("SELECT hashtag FROM hashtags WHERE video_id = ?", (video_id,))
                    video_hashtags = [r[0] for r in cursor.fetchall()]
                    
                    cursor.execute("SELECT mention FROM mentions WHERE video_id = ?", (video_id,))
                    video_mentions = [r[0] for r in cursor.fetchall()]
                    
                    video = self._row_to_video_data(row, video_hashtags, video_mentions)
                    videos.append(video)
                
                self.logger.info(f"動画検索結果: {len(videos)} 件")
                return videos
                
        except Exception as e:
            self.logger.error(f"動画検索エラー: {e}")
            return []
    
    def _row_to_video_data(self, row, hashtags: List[str], mentions: List[str]) -> VideoData:
        """データベース行をVideoDataオブジェクトに変換"""
        raw_data = {}
        if row['raw_data']:
            try:
                raw_data = json.loads(row['raw_data'])
            except json.JSONDecodeError:
                pass
        
        return VideoData(
            video_id=row['video_id'],
            url=row['url'],
            title=row['title'] or '',
            description=row['description'] or '',
            
            author_username=row['author_username'] or '',
            author_display_name=row['author_display_name'] or '',
            author_follower_count=row['author_follower_count'],
            author_verified=bool(row['author_verified']),
            
            view_count=row['view_count'],
            like_count=row['like_count'],
            comment_count=row['comment_count'],
            share_count=row['share_count'],
            
            upload_date=row['upload_date'],
            duration=row['duration'],
            
            thumbnail_url=row['thumbnail_url'] or '',
            video_url=row['video_url'] or '',
            music_title=row['music_title'] or '',
            music_author=row['music_author'] or '',
            
            hashtags=hashtags,
            mentions=mentions,
            
            region=row['region'] or '',
            language=row['language'] or '',
            
            collected_at=row['collected_at'] or datetime.now(),
            source_page=row['source_page'] or '',
            raw_data=raw_data
        )
    
    def get_trending_videos(
        self,
        min_views: int = 500000,
        hours: int = 24,
        limit: int = 100
    ) -> List[VideoData]:
        """
        トレンド動画を取得
        
        Args:
            min_views: 最小再生数
            hours: 時間範囲
            limit: 取得件数制限
            
        Returns:
            トレンド動画リスト
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        
        return self.search_videos(
            min_views=min_views,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        データベース統計を取得
        
        Returns:
            統計情報
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 総動画数
                cursor.execute("SELECT COUNT(*) FROM videos")
                stats['total_videos'] = cursor.fetchone()[0]
                
                # 今日収集された動画数
                today = datetime.now().date()
                cursor.execute(
                    "SELECT COUNT(*) FROM videos WHERE DATE(collected_at) = ?",
                    (today,)
                )
                stats['today_videos'] = cursor.fetchone()[0]
                
                # 高再生数動画数（50万以上）
                cursor.execute("SELECT COUNT(*) FROM videos WHERE view_count >= 500000")
                stats['high_view_videos'] = cursor.fetchone()[0]
                
                # 最新収集日時
                cursor.execute("SELECT MAX(collected_at) FROM videos")
                latest_collection = cursor.fetchone()[0]
                stats['latest_collection'] = latest_collection
                
                # 人気ハッシュタグ（上位10）
                cursor.execute('''
                    SELECT hashtag, COUNT(*) as count 
                    FROM hashtags 
                    GROUP BY hashtag 
                    ORDER BY count DESC 
                    LIMIT 10
                ''')
                stats['popular_hashtags'] = [
                    {'hashtag': row[0], 'count': row[1]} 
                    for row in cursor.fetchall()
                ]
                
                # 人気作成者（上位10）
                cursor.execute('''
                    SELECT author_username, COUNT(*) as count, AVG(view_count) as avg_views
                    FROM videos 
                    WHERE author_username IS NOT NULL AND author_username != ''
                    GROUP BY author_username 
                    ORDER BY count DESC 
                    LIMIT 10
                ''')
                stats['popular_authors'] = [
                    {
                        'username': row[0], 
                        'video_count': row[1], 
                        'avg_views': int(row[2]) if row[2] else 0
                    } 
                    for row in cursor.fetchall()
                ]
                
                return stats
                
        except Exception as e:
            self.logger.error(f"統計取得エラー: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30) -> int:
        """
        古いデータを削除
        
        Args:
            days: 保持日数
            
        Returns:
            削除された動画数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # 削除対象の動画IDを取得
                cursor.execute(
                    "SELECT video_id FROM videos WHERE collected_at < ?",
                    (cutoff_date,)
                )
                video_ids = [row[0] for row in cursor.fetchall()]
                
                if not video_ids:
                    return 0
                
                # 関連データを削除
                placeholders = ','.join(['?'] * len(video_ids))
                
                cursor.execute(f"DELETE FROM hashtags WHERE video_id IN ({placeholders})", video_ids)
                cursor.execute(f"DELETE FROM mentions WHERE video_id IN ({placeholders})", video_ids)
                cursor.execute(f"DELETE FROM videos WHERE video_id IN ({placeholders})", video_ids)
                
                # 古い収集履歴も削除
                cursor.execute("DELETE FROM collection_history WHERE collected_at < ?", (cutoff_date,))
                
                conn.commit()
                
                self.logger.info(f"古いデータを削除: {len(video_ids)} 件 ({days}日以前)")
                return len(video_ids)
                
        except Exception as e:
            self.logger.error(f"データクリーンアップエラー: {e}")
            return 0
    
    def backup_database(self, backup_path: str) -> bool:
        """
        データベースをバックアップ
        
        Args:
            backup_path: バックアップファイルパス
            
        Returns:
            バックアップ成功かどうか
        """
        try:
            import shutil
            
            backup_file = Path(backup_path)
            backup_file.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(self.db_path, backup_file)
            
            self.logger.info(f"データベースをバックアップ: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"データベースバックアップエラー: {e}")
            return False

