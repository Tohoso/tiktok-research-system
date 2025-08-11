"""
リクエスト制御モジュール
人間らしいアクセスパターンを実現
"""

import time
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ..utils.logger import get_logger


@dataclass
class RequestPattern:
    """リクエストパターン設定"""
    min_delay: float = 2.0  # 最小待機時間（秒）
    max_delay: float = 8.0  # 最大待機時間（秒）
    burst_requests: int = 3  # バースト時の最大リクエスト数
    burst_cooldown: float = 30.0  # バースト後のクールダウン時間（秒）
    daily_limit: int = 1000  # 1日の最大リクエスト数
    hourly_limit: int = 100  # 1時間の最大リクエスト数


class RequestThrottle:
    """リクエスト制御クラス"""
    
    def __init__(self, pattern: Optional[RequestPattern] = None):
        """
        リクエスト制御を初期化
        
        Args:
            pattern: リクエストパターン設定
        """
        self.pattern = pattern or RequestPattern()
        self.logger = get_logger(self.__class__.__name__)
        
        # リクエスト履歴
        self.request_history = []
        self.last_request_time = 0.0
        self.burst_count = 0
        self.last_burst_time = 0.0
        
        # 統計情報
        self.total_requests = 0
        self.total_wait_time = 0.0
        
        self.logger.info("リクエスト制御を初期化しました")
    
    def wait_if_needed(self) -> float:
        """
        必要に応じて待機
        
        Returns:
            実際の待機時間（秒）
        """
        current_time = time.time()
        
        # 前回のリクエストからの経過時間
        time_since_last = current_time - self.last_request_time
        
        # 基本的な待機時間を計算
        base_delay = self._calculate_base_delay()
        
        # バースト制御
        burst_delay = self._calculate_burst_delay(current_time)
        
        # レート制限チェック
        rate_delay = self._calculate_rate_limit_delay(current_time)
        
        # 最大の待機時間を適用
        required_delay = max(base_delay, burst_delay, rate_delay)
        
        # 既に十分時間が経過している場合は待機不要
        if time_since_last >= required_delay:
            wait_time = 0.0
        else:
            wait_time = required_delay - time_since_last
        
        if wait_time > 0:
            self.logger.debug(f"リクエスト制御: {wait_time:.2f}秒待機")
            time.sleep(wait_time)
            self.total_wait_time += wait_time
        
        # リクエスト履歴を更新
        self.last_request_time = time.time()
        self.total_requests += 1
        self._update_request_history()
        
        return wait_time
    
    def _calculate_base_delay(self) -> float:
        """
        基本的な待機時間を計算（人間らしいランダム性）
        
        Returns:
            待機時間（秒）
        """
        # 基本的なランダム待機時間
        base_delay = random.uniform(self.pattern.min_delay, self.pattern.max_delay)
        
        # 時間帯による調整（深夜は少し長め）
        current_hour = time.localtime().tm_hour
        if 0 <= current_hour <= 6:  # 深夜
            base_delay *= 1.5
        elif 12 <= current_hour <= 14:  # 昼休み
            base_delay *= 0.8
        elif 18 <= current_hour <= 22:  # 夕方〜夜
            base_delay *= 0.9
        
        # 曜日による調整
        weekday = time.localtime().tm_wday
        if weekday >= 5:  # 週末
            base_delay *= 1.2
        
        # ランダムな変動を追加（±20%）
        variation = random.uniform(0.8, 1.2)
        base_delay *= variation
        
        return base_delay
    
    def _calculate_burst_delay(self, current_time: float) -> float:
        """
        バースト制御の待機時間を計算
        
        Args:
            current_time: 現在時刻
            
        Returns:
            待機時間（秒）
        """
        # バーストカウントをリセット（クールダウン期間経過後）
        if current_time - self.last_burst_time > self.pattern.burst_cooldown:
            self.burst_count = 0
        
        # バースト制限に達している場合
        if self.burst_count >= self.pattern.burst_requests:
            remaining_cooldown = self.pattern.burst_cooldown - (current_time - self.last_burst_time)
            if remaining_cooldown > 0:
                return remaining_cooldown
            else:
                self.burst_count = 0  # リセット
        
        return 0.0
    
    def _calculate_rate_limit_delay(self, current_time: float) -> float:
        """
        レート制限の待機時間を計算
        
        Args:
            current_time: 現在時刻
            
        Returns:
            待機時間（秒）
        """
        # 過去1時間のリクエスト数をカウント
        hour_ago = current_time - 3600
        hourly_requests = len([t for t in self.request_history if t > hour_ago])
        
        # 時間制限チェック
        if hourly_requests >= self.pattern.hourly_limit:
            # 最も古いリクエストから1時間経過するまで待機
            oldest_request = min([t for t in self.request_history if t > hour_ago])
            return 3600 - (current_time - oldest_request)
        
        # 過去24時間のリクエスト数をカウント
        day_ago = current_time - 86400
        daily_requests = len([t for t in self.request_history if t > day_ago])
        
        # 日制限チェック
        if daily_requests >= self.pattern.daily_limit:
            # 最も古いリクエストから24時間経過するまで待機
            oldest_request = min([t for t in self.request_history if t > day_ago])
            return 86400 - (current_time - oldest_request)
        
        return 0.0
    
    def _update_request_history(self):
        """リクエスト履歴を更新"""
        current_time = time.time()
        self.request_history.append(current_time)
        
        # バーストカウントを更新
        if current_time - self.last_request_time < self.pattern.burst_cooldown:
            self.burst_count += 1
            if self.burst_count == 1:
                self.last_burst_time = current_time
        else:
            self.burst_count = 1
            self.last_burst_time = current_time
        
        # 古い履歴を削除（24時間以上前）
        day_ago = current_time - 86400
        self.request_history = [t for t in self.request_history if t > day_ago]
    
    def get_human_like_delay(self) -> float:
        """
        人間らしい追加の待機時間を取得
        
        Returns:
            追加待機時間（秒）
        """
        # ランダムな「考える時間」
        thinking_time = random.uniform(0.5, 3.0)
        
        # 稀に長い休憩を取る（5%の確率）
        if random.random() < 0.05:
            break_time = random.uniform(30.0, 120.0)  # 30秒〜2分
            self.logger.info(f"人間らしい休憩: {break_time:.1f}秒")
            return thinking_time + break_time
        
        # 稀に短い休憩を取る（15%の確率）
        elif random.random() < 0.15:
            short_break = random.uniform(5.0, 15.0)  # 5〜15秒
            return thinking_time + short_break
        
        return thinking_time
    
    def simulate_reading_time(self, content_length: int) -> float:
        """
        コンテンツの読み取り時間をシミュレート
        
        Args:
            content_length: コンテンツの長さ（文字数）
            
        Returns:
            読み取り時間（秒）
        """
        # 平均的な読み取り速度: 200-300文字/分
        reading_speed = random.uniform(200, 300)  # 文字/分
        base_reading_time = (content_length / reading_speed) * 60  # 秒
        
        # 最小・最大時間を設定
        min_time = 2.0  # 最低2秒
        max_time = 30.0  # 最大30秒
        
        reading_time = max(min_time, min(base_reading_time, max_time))
        
        # ランダムな変動を追加
        variation = random.uniform(0.7, 1.3)
        reading_time *= variation
        
        return reading_time
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        current_time = time.time()
        
        # 過去1時間と24時間のリクエスト数
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        hourly_requests = len([t for t in self.request_history if t > hour_ago])
        daily_requests = len([t for t in self.request_history if t > day_ago])
        
        avg_wait_time = self.total_wait_time / self.total_requests if self.total_requests > 0 else 0.0
        
        return {
            "total_requests": self.total_requests,
            "hourly_requests": hourly_requests,
            "daily_requests": daily_requests,
            "hourly_limit": self.pattern.hourly_limit,
            "daily_limit": self.pattern.daily_limit,
            "total_wait_time": self.total_wait_time,
            "average_wait_time": avg_wait_time,
            "burst_count": self.burst_count,
            "last_request_time": self.last_request_time
        }
    
    def reset_stats(self):
        """統計情報をリセット"""
        self.request_history.clear()
        self.total_requests = 0
        self.total_wait_time = 0.0
        self.burst_count = 0
        self.last_request_time = 0.0
        self.last_burst_time = 0.0
        
        self.logger.info("リクエスト制御統計をリセットしました")

