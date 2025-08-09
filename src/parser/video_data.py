"""
Video data model for TikTok Research System
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
import json


@dataclass
class VideoData:
    """TikTok動画データモデル"""
    
    # 基本情報
    video_id: str
    url: str
    title: str = ""
    description: str = ""
    
    # 作成者情報
    author_username: str = ""
    author_display_name: str = ""
    author_follower_count: Optional[int] = None
    author_verified: bool = False
    
    # 統計情報
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    
    # 時間情報
    upload_date: Optional[datetime] = None
    duration: Optional[int] = None  # 秒
    
    # メディア情報
    thumbnail_url: str = ""
    video_url: str = ""
    music_title: str = ""
    music_author: str = ""
    
    # ハッシュタグ・メンション
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    
    # 地域・言語情報
    region: str = ""
    language: str = ""
    
    # メタデータ
    collected_at: datetime = field(default_factory=datetime.now)
    source_page: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初期化後の処理"""
        # video_idが空の場合、URLから抽出を試行
        if not self.video_id and self.url:
            from ..utils.helpers import extract_video_id
            extracted_id = extract_video_id(self.url)
            if extracted_id:
                self.video_id = extracted_id
    
    @property
    def is_valid(self) -> bool:
        """データの妥当性をチェック"""
        return bool(self.video_id and self.url)
    
    @property
    def meets_view_threshold(self) -> bool:
        """再生数閾値を満たすかチェック（デフォルト50万）"""
        return self.view_count is not None and self.view_count >= 500000
    
    @property
    def is_recent(self) -> bool:
        """24時間以内の投稿かチェック"""
        if not self.upload_date:
            return False
        
        from ..utils.helpers import is_within_time_range
        return is_within_time_range(self.upload_date, hours=24)
    
    @property
    def engagement_rate(self) -> Optional[float]:
        """エンゲージメント率を計算"""
        if not self.view_count or self.view_count == 0:
            return None
        
        total_engagement = (self.like_count or 0) + (self.comment_count or 0) + (self.share_count or 0)
        return (total_engagement / self.view_count) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = {}
        
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat() if value else None
            elif isinstance(value, list):
                data[key] = value.copy()
            elif isinstance(value, dict):
                data[key] = value.copy()
            else:
                data[key] = value
        
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VideoData':
        """辞書からインスタンスを作成"""
        # datetime フィールドの変換
        datetime_fields = ['upload_date', 'collected_at']
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    data[field_name] = datetime.fromisoformat(data[field_name])
                except ValueError:
                    data[field_name] = None
        
        # 不要なフィールドを除去
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VideoData':
        """JSON文字列からインスタンスを作成"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_stats(self, view_count: int = None, like_count: int = None, 
                    comment_count: int = None, share_count: int = None):
        """統計情報を更新"""
        if view_count is not None:
            self.view_count = view_count
        if like_count is not None:
            self.like_count = like_count
        if comment_count is not None:
            self.comment_count = comment_count
        if share_count is not None:
            self.share_count = share_count
    
    def add_hashtag(self, hashtag: str):
        """ハッシュタグを追加"""
        if hashtag and hashtag not in self.hashtags:
            self.hashtags.append(hashtag)
    
    def add_mention(self, mention: str):
        """メンションを追加"""
        if mention and mention not in self.mentions:
            self.mentions.append(mention)
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"VideoData(id={self.video_id}, title='{self.title[:50]}...', views={self.view_count})"
    
    def __repr__(self) -> str:
        """詳細文字列表現"""
        return (f"VideoData(video_id='{self.video_id}', url='{self.url}', "
                f"title='{self.title}', view_count={self.view_count}, "
                f"upload_date={self.upload_date})")


@dataclass
class VideoCollection:
    """動画データのコレクション"""
    
    videos: List[VideoData] = field(default_factory=list)
    collected_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    total_count: int = 0
    
    def add_video(self, video: VideoData):
        """動画を追加"""
        if video.is_valid and video not in self.videos:
            self.videos.append(video)
            self.total_count = len(self.videos)
    
    def filter_by_views(self, min_views: int = 500000) -> 'VideoCollection':
        """再生数でフィルタリング"""
        filtered_videos = [v for v in self.videos if v.view_count and v.view_count >= min_views]
        
        return VideoCollection(
            videos=filtered_videos,
            collected_at=self.collected_at,
            source=f"{self.source}_filtered_views_{min_views}",
            total_count=len(filtered_videos)
        )
    
    def filter_by_date(self, hours: int = 24) -> 'VideoCollection':
        """投稿日時でフィルタリング"""
        filtered_videos = [v for v in self.videos if v.is_recent]
        
        return VideoCollection(
            videos=filtered_videos,
            collected_at=self.collected_at,
            source=f"{self.source}_filtered_recent_{hours}h",
            total_count=len(filtered_videos)
        )
    
    def get_top_videos(self, limit: int = 10, sort_by: str = "view_count") -> List[VideoData]:
        """上位動画を取得"""
        if sort_by == "view_count":
            return sorted(
                [v for v in self.videos if v.view_count],
                key=lambda x: x.view_count,
                reverse=True
            )[:limit]
        elif sort_by == "engagement_rate":
            return sorted(
                [v for v in self.videos if v.engagement_rate],
                key=lambda x: x.engagement_rate,
                reverse=True
            )[:limit]
        else:
            return self.videos[:limit]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'videos': [video.to_dict() for video in self.videos],
            'collected_at': self.collected_at.isoformat(),
            'source': self.source,
            'total_count': self.total_count
        }
    
    def to_json(self, indent: int = 2) -> str:
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
    
    def __len__(self) -> int:
        """コレクションのサイズ"""
        return len(self.videos)
    
    def __iter__(self):
        """イテレータ"""
        return iter(self.videos)
    
    def __getitem__(self, index):
        """インデックスアクセス"""
        return self.videos[index]

