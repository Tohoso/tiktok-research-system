"""
Video filtering for TikTok Research System
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import re

from ..utils.logger import get_logger
from ..parser.video_data import VideoData, VideoCollection


class VideoFilter:
    """動画フィルタリングクラス"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def filter_by_views(
        self,
        videos: List[VideoData],
        min_views: Optional[int] = None,
        max_views: Optional[int] = None
    ) -> List[VideoData]:
        """
        再生数でフィルタリング
        
        Args:
            videos: 動画データリスト
            min_views: 最小再生数
            max_views: 最大再生数
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            if video.view_count is None:
                continue
            
            # 最小再生数チェック
            if min_views is not None and video.view_count < min_views:
                continue
            
            # 最大再生数チェック
            if max_views is not None and video.view_count > max_views:
                continue
            
            filtered.append(video)
        
        self.logger.info(f"再生数フィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def filter_by_date(
        self,
        videos: List[VideoData],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        hours_ago: Optional[int] = None
    ) -> List[VideoData]:
        """
        投稿日時でフィルタリング
        
        Args:
            videos: 動画データリスト
            start_date: 開始日時
            end_date: 終了日時
            hours_ago: 何時間前から（現在時刻基準）
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        # hours_ago が指定されている場合は start_date を設定
        if hours_ago is not None:
            start_date = datetime.now() - timedelta(hours=hours_ago)
        
        for video in videos:
            if video.upload_date is None:
                continue
            
            # 開始日時チェック
            if start_date is not None and video.upload_date < start_date:
                continue
            
            # 終了日時チェック
            if end_date is not None and video.upload_date > end_date:
                continue
            
            filtered.append(video)
        
        self.logger.info(f"日時フィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def filter_by_author(
        self,
        videos: List[VideoData],
        usernames: Optional[List[str]] = None,
        verified_only: bool = False,
        min_followers: Optional[int] = None
    ) -> List[VideoData]:
        """
        作成者でフィルタリング
        
        Args:
            videos: 動画データリスト
            usernames: 対象ユーザー名リスト
            verified_only: 認証済みアカウントのみ
            min_followers: 最小フォロワー数
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            # ユーザー名チェック
            if usernames is not None:
                if video.author_username not in usernames:
                    continue
            
            # 認証済みチェック
            if verified_only and not video.author_verified:
                continue
            
            # フォロワー数チェック
            if min_followers is not None:
                if video.author_follower_count is None or video.author_follower_count < min_followers:
                    continue
            
            filtered.append(video)
        
        self.logger.info(f"作成者フィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def filter_by_hashtags(
        self,
        videos: List[VideoData],
        required_hashtags: Optional[List[str]] = None,
        excluded_hashtags: Optional[List[str]] = None,
        min_hashtag_count: Optional[int] = None
    ) -> List[VideoData]:
        """
        ハッシュタグでフィルタリング
        
        Args:
            videos: 動画データリスト
            required_hashtags: 必須ハッシュタグ
            excluded_hashtags: 除外ハッシュタグ
            min_hashtag_count: 最小ハッシュタグ数
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            video_hashtags = [tag.lower() for tag in video.hashtags]
            
            # 必須ハッシュタグチェック
            if required_hashtags:
                required_lower = [tag.lower() for tag in required_hashtags]
                if not any(tag in video_hashtags for tag in required_lower):
                    continue
            
            # 除外ハッシュタグチェック
            if excluded_hashtags:
                excluded_lower = [tag.lower() for tag in excluded_hashtags]
                if any(tag in video_hashtags for tag in excluded_lower):
                    continue
            
            # 最小ハッシュタグ数チェック
            if min_hashtag_count is not None and len(video.hashtags) < min_hashtag_count:
                continue
            
            filtered.append(video)
        
        self.logger.info(f"ハッシュタグフィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def filter_by_content(
        self,
        videos: List[VideoData],
        keywords: Optional[List[str]] = None,
        excluded_keywords: Optional[List[str]] = None,
        min_title_length: Optional[int] = None,
        max_title_length: Optional[int] = None
    ) -> List[VideoData]:
        """
        コンテンツでフィルタリング
        
        Args:
            videos: 動画データリスト
            keywords: 必須キーワード
            excluded_keywords: 除外キーワード
            min_title_length: 最小タイトル長
            max_title_length: 最大タイトル長
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            content_text = f"{video.title} {video.description}".lower()
            
            # 必須キーワードチェック
            if keywords:
                keywords_lower = [kw.lower() for kw in keywords]
                if not any(kw in content_text for kw in keywords_lower):
                    continue
            
            # 除外キーワードチェック
            if excluded_keywords:
                excluded_lower = [kw.lower() for kw in excluded_keywords]
                if any(kw in content_text for kw in excluded_lower):
                    continue
            
            # タイトル長チェック
            title_length = len(video.title)
            if min_title_length is not None and title_length < min_title_length:
                continue
            if max_title_length is not None and title_length > max_title_length:
                continue
            
            filtered.append(video)
        
        self.logger.info(f"コンテンツフィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def filter_by_engagement(
        self,
        videos: List[VideoData],
        min_like_rate: Optional[float] = None,
        min_comment_rate: Optional[float] = None,
        min_engagement_score: Optional[float] = None
    ) -> List[VideoData]:
        """
        エンゲージメントでフィルタリング
        
        Args:
            videos: 動画データリスト
            min_like_rate: 最小いいね率（いいね数/再生数）
            min_comment_rate: 最小コメント率（コメント数/再生数）
            min_engagement_score: 最小エンゲージメントスコア
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            if video.view_count is None or video.view_count == 0:
                continue
            
            # いいね率チェック
            if min_like_rate is not None:
                like_rate = (video.like_count or 0) / video.view_count
                if like_rate < min_like_rate:
                    continue
            
            # コメント率チェック
            if min_comment_rate is not None:
                comment_rate = (video.comment_count or 0) / video.view_count
                if comment_rate < min_comment_rate:
                    continue
            
            # エンゲージメントスコアチェック
            if min_engagement_score is not None:
                engagement_score = self._calculate_engagement_score(video)
                if engagement_score < min_engagement_score:
                    continue
            
            filtered.append(video)
        
        self.logger.info(f"エンゲージメントフィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def _calculate_engagement_score(self, video: VideoData) -> float:
        """
        エンゲージメントスコアを計算
        
        Args:
            video: 動画データ
            
        Returns:
            エンゲージメントスコア（0-1）
        """
        if video.view_count is None or video.view_count == 0:
            return 0.0
        
        # 重み付きエンゲージメントスコア
        like_weight = 1.0
        comment_weight = 3.0  # コメントはより価値が高い
        share_weight = 5.0    # シェアは最も価値が高い
        
        like_score = (video.like_count or 0) * like_weight
        comment_score = (video.comment_count or 0) * comment_weight
        share_score = (video.share_count or 0) * share_weight
        
        total_engagement = like_score + comment_score + share_score
        engagement_rate = total_engagement / video.view_count
        
        # 0-1の範囲に正規化（最大値を0.1と仮定）
        return min(engagement_rate / 0.1, 1.0)
    
    def filter_by_duration(
        self,
        videos: List[VideoData],
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[VideoData]:
        """
        動画長でフィルタリング
        
        Args:
            videos: 動画データリスト
            min_duration: 最小動画長（秒）
            max_duration: 最大動画長（秒）
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = []
        
        for video in videos:
            if video.duration is None:
                continue
            
            # 最小動画長チェック
            if min_duration is not None and video.duration < min_duration:
                continue
            
            # 最大動画長チェック
            if max_duration is not None and video.duration > max_duration:
                continue
            
            filtered.append(video)
        
        self.logger.info(f"動画長フィルタリング: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def remove_duplicates(
        self,
        videos: List[VideoData],
        by_field: str = "video_id"
    ) -> List[VideoData]:
        """
        重複を除去
        
        Args:
            videos: 動画データリスト
            by_field: 重複判定フィールド
            
        Returns:
            重複除去済み動画リスト
        """
        seen = set()
        unique_videos = []
        
        for video in videos:
            field_value = getattr(video, by_field, None)
            if field_value is not None and field_value not in seen:
                seen.add(field_value)
                unique_videos.append(video)
        
        self.logger.info(f"重複除去: {len(videos)} → {len(unique_videos)} 件")
        return unique_videos
    
    def apply_trending_filter(
        self,
        videos: List[VideoData],
        min_views: int = 500000,
        hours_ago: int = 24,
        min_engagement_score: float = 0.01
    ) -> List[VideoData]:
        """
        トレンド動画フィルターを適用
        
        Args:
            videos: 動画データリスト
            min_views: 最小再生数
            hours_ago: 何時間前から
            min_engagement_score: 最小エンゲージメントスコア
            
        Returns:
            トレンド動画リスト
        """
        self.logger.info("トレンド動画フィルターを適用")
        
        # 段階的にフィルタリング
        filtered = videos
        
        # 1. 日時フィルタリング
        filtered = self.filter_by_date(filtered, hours_ago=hours_ago)
        
        # 2. 再生数フィルタリング
        filtered = self.filter_by_views(filtered, min_views=min_views)
        
        # 3. エンゲージメントフィルタリング
        filtered = self.filter_by_engagement(filtered, min_engagement_score=min_engagement_score)
        
        # 4. 重複除去
        filtered = self.remove_duplicates(filtered)
        
        # 5. 再生数でソート
        filtered.sort(key=lambda v: v.view_count or 0, reverse=True)
        
        self.logger.info(f"トレンド動画フィルター完了: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def apply_custom_filter(
        self,
        videos: List[VideoData],
        filter_func: Callable[[VideoData], bool]
    ) -> List[VideoData]:
        """
        カスタムフィルターを適用
        
        Args:
            videos: 動画データリスト
            filter_func: フィルター関数
            
        Returns:
            フィルタリング済み動画リスト
        """
        filtered = [video for video in videos if filter_func(video)]
        
        self.logger.info(f"カスタムフィルター: {len(videos)} → {len(filtered)} 件")
        return filtered
    
    def get_filter_statistics(
        self,
        original_videos: List[VideoData],
        filtered_videos: List[VideoData]
    ) -> Dict[str, Any]:
        """
        フィルタリング統計を取得
        
        Args:
            original_videos: 元の動画リスト
            filtered_videos: フィルタリング後の動画リスト
            
        Returns:
            統計情報
        """
        if not original_videos:
            return {}
        
        stats = {
            'original_count': len(original_videos),
            'filtered_count': len(filtered_videos),
            'filter_rate': len(filtered_videos) / len(original_videos),
            'removed_count': len(original_videos) - len(filtered_videos)
        }
        
        if filtered_videos:
            # 再生数統計
            view_counts = [v.view_count for v in filtered_videos if v.view_count is not None]
            if view_counts:
                stats['avg_views'] = sum(view_counts) / len(view_counts)
                stats['max_views'] = max(view_counts)
                stats['min_views'] = min(view_counts)
            
            # エンゲージメント統計
            engagement_scores = [self._calculate_engagement_score(v) for v in filtered_videos]
            if engagement_scores:
                stats['avg_engagement'] = sum(engagement_scores) / len(engagement_scores)
                stats['max_engagement'] = max(engagement_scores)
        
        return stats

