"""
プロキシローテーション管理モジュール
異なるIPアドレスを使用してアクセスを分散
"""

import random
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from ..utils.logger import get_logger


@dataclass
class ProxyConfig:
    """プロキシ設定"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"
    country: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    
    @property
    def url(self) -> str:
        """プロキシURL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    def record_success(self):
        """成功を記録"""
        self.success_count += 1
        self.last_used = time.time()
    
    def record_failure(self):
        """失敗を記録"""
        self.failure_count += 1
        self.last_used = time.time()


class ProxyManager:
    """プロキシローテーション管理クラス"""
    
    def __init__(self, enable_rotation: bool = True):
        """
        プロキシマネージャーを初期化
        
        Args:
            enable_rotation: プロキシローテーションを有効にするか
        """
        self.enable_rotation = enable_rotation
        self.proxies: List[ProxyConfig] = []
        self.current_proxy_index = 0
        self.logger = get_logger(self.__class__.__name__)
        
        # デフォルトプロキシリストを設定（ScraperAPI内蔵プロキシ）
        self._setup_default_proxies()
    
    def _setup_default_proxies(self):
        """デフォルトプロキシリストを設定"""
        # ScraperAPIの地域別プロキシ設定
        default_proxies = [
            # 日本のプロキシ（優先）
            {"country": "JP", "priority": 1},
            # アジア太平洋地域
            {"country": "SG", "priority": 2},  # シンガポール
            {"country": "KR", "priority": 2},  # 韓国
            {"country": "HK", "priority": 2},  # 香港
            # その他の地域
            {"country": "US", "priority": 3},  # アメリカ
            {"country": "CA", "priority": 3},  # カナダ
            {"country": "AU", "priority": 3},  # オーストラリア
        ]
        
        for proxy_info in default_proxies:
            proxy = ProxyConfig(
                host="scraperapi",  # ScraperAPI内部で処理
                port=0,
                country=proxy_info["country"]
            )
            self.proxies.append(proxy)
        
        self.logger.info(f"デフォルトプロキシを設定: {len(self.proxies)}件")
    
    def add_proxy(
        self,
        host: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        protocol: str = "http",
        country: Optional[str] = None
    ):
        """
        プロキシを追加
        
        Args:
            host: プロキシホスト
            port: プロキシポート
            username: ユーザー名
            password: パスワード
            protocol: プロトコル
            country: 国コード
        """
        proxy = ProxyConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            protocol=protocol,
            country=country
        )
        self.proxies.append(proxy)
        self.logger.info(f"プロキシを追加: {host}:{port} ({country})")
    
    def get_next_proxy(self) -> Optional[ProxyConfig]:
        """
        次のプロキシを取得（ローテーション）
        
        Returns:
            プロキシ設定またはNone
        """
        if not self.enable_rotation or not self.proxies:
            return None
        
        # 成功率でソートして選択
        available_proxies = [p for p in self.proxies if p.success_rate >= 0.3 or p.success_count + p.failure_count < 5]
        
        if not available_proxies:
            # 全て失敗している場合は、最も最近使用されていないものを選択
            available_proxies = sorted(self.proxies, key=lambda x: x.last_used or 0)
        
        # 重み付きランダム選択（成功率が高いほど選ばれやすい）
        if available_proxies:
            weights = [max(p.success_rate, 0.1) for p in available_proxies]
            proxy = random.choices(available_proxies, weights=weights)[0]
            return proxy
        
        return None
    
    def get_proxy_for_country(self, country_code: str) -> Optional[ProxyConfig]:
        """
        特定の国のプロキシを取得
        
        Args:
            country_code: 国コード（例: "JP", "US"）
            
        Returns:
            プロキシ設定またはNone
        """
        country_proxies = [p for p in self.proxies if p.country == country_code]
        
        if country_proxies:
            # 成功率でソート
            country_proxies.sort(key=lambda x: x.success_rate, reverse=True)
            return country_proxies[0]
        
        return None
    
    def get_scraperapi_params(self, proxy: Optional[ProxyConfig] = None) -> Dict[str, Any]:
        """
        ScraperAPI用のプロキシパラメータを取得
        
        Args:
            proxy: プロキシ設定
            
        Returns:
            ScraperAPIパラメータ
        """
        params = {}
        
        if proxy and proxy.country:
            params['country_code'] = proxy.country
            
        # 追加のプロキシ設定
        params.update({
            'premium': True,  # プレミアムプロキシを使用
            'session_number': random.randint(1, 1000),  # セッション番号をランダム化
            'keep_headers': True,  # ヘッダーを保持
        })
        
        return params
    
    def record_proxy_result(self, proxy: ProxyConfig, success: bool):
        """
        プロキシの使用結果を記録
        
        Args:
            proxy: プロキシ設定
            success: 成功したかどうか
        """
        if success:
            proxy.record_success()
            self.logger.debug(f"プロキシ成功: {proxy.country} (成功率: {proxy.success_rate:.2f})")
        else:
            proxy.record_failure()
            self.logger.debug(f"プロキシ失敗: {proxy.country} (成功率: {proxy.success_rate:.2f})")
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """
        プロキシ統計情報を取得
        
        Returns:
            統計情報
        """
        if not self.proxies:
            return {"total_proxies": 0}
        
        total_success = sum(p.success_count for p in self.proxies)
        total_failure = sum(p.failure_count for p in self.proxies)
        total_requests = total_success + total_failure
        
        stats = {
            "total_proxies": len(self.proxies),
            "total_requests": total_requests,
            "total_success": total_success,
            "total_failure": total_failure,
            "overall_success_rate": total_success / total_requests if total_requests > 0 else 0.0,
            "proxy_details": []
        }
        
        for proxy in self.proxies:
            proxy_stats = {
                "country": proxy.country,
                "success_count": proxy.success_count,
                "failure_count": proxy.failure_count,
                "success_rate": proxy.success_rate,
                "last_used": proxy.last_used
            }
            stats["proxy_details"].append(proxy_stats)
        
        return stats
    
    def reset_proxy_stats(self):
        """プロキシ統計をリセット"""
        for proxy in self.proxies:
            proxy.success_count = 0
            proxy.failure_count = 0
            proxy.last_used = None
        
        self.logger.info("プロキシ統計をリセットしました")

