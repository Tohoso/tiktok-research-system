"""
ScraperAPI client for TikTok Research System
"""

import time
import random
import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode

from ..utils.logger import get_logger
from ..utils.helpers import retry_on_exception, validate_url
from ..utils.user_agents import UserAgentManager
from ..utils.proxy_manager import ProxyManager
from ..utils.request_throttle import RequestThrottle, RequestPattern
from .exceptions import (
    APIError,
    RateLimitError,
    AuthenticationError,
    NetworkError,
    ConfigurationError
)


class ScraperAPIClient:
    """ScraperAPI クライアント"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://api.scraperapi.com",
        timeout: int = 60,
        max_retries: int = 3,
        rate_limit_delay: float = 2.0,
        enable_proxy_rotation: bool = True,
        enable_request_throttling: bool = True,
        device_type: str = "desktop"
    ):
        """
        ScraperAPI クライアントを初期化
        
        Args:
            api_key: ScraperAPI キー
            base_url: ベースURL
            timeout: タイムアウト（秒）
            max_retries: 最大リトライ回数
            rate_limit_delay: レート制限時の待機時間（秒）
            enable_proxy_rotation: プロキシローテーションを有効にするか
            enable_request_throttling: リクエスト制御を有効にするか
            device_type: デバイスタイプ（"desktop", "mobile", "tiktok"）
        """
        if not api_key or api_key == "your_scraperapi_key_here":
            raise ConfigurationError("有効なScraperAPI キーが設定されていません")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        self.device_type = device_type
        
        self.logger = get_logger(self.__class__.__name__)
        self.session = requests.Session()
        
        # 新機能の初期化
        self.user_agent_manager = UserAgentManager()
        self.proxy_manager = ProxyManager(enable_rotation=enable_proxy_rotation)
        
        # リクエスト制御の設定
        if enable_request_throttling:
            throttle_pattern = RequestPattern(
                min_delay=3.0,  # TikTok用に少し長めに設定
                max_delay=10.0,
                burst_requests=2,  # バースト数を減らす
                burst_cooldown=45.0,  # クールダウンを長めに
                hourly_limit=50,  # 時間制限を厳しく
                daily_limit=500   # 日制限を厳しく
            )
            self.request_throttle = RequestThrottle(throttle_pattern)
        else:
            self.request_throttle = None
        
        # 現在のUser-Agentを設定
        self.current_user_agent = self.user_agent_manager.get_random_agent(device_type)
        
        # セッションのデフォルト設定
        self._update_session_headers()
        
        self.logger.info("ScraperAPI クライアントを初期化しました")
        self.logger.info(f"プロキシローテーション: {'有効' if enable_proxy_rotation else '無効'}")
        self.logger.info(f"リクエスト制御: {'有効' if enable_request_throttling else '無効'}")
        self.logger.info(f"デバイスタイプ: {device_type}")
    
    def _update_session_headers(self):
        """セッションヘッダーを更新"""
        headers = self.user_agent_manager.get_browser_headers(self.current_user_agent)
        self.session.headers.update(headers)
        
        # TikTok特有のヘッダーを追加
        if self.device_type == "tiktok":
            self.session.headers.update({
                'Referer': 'https://www.tiktok.com/',
                'Origin': 'https://www.tiktok.com',
                'X-Requested-With': 'XMLHttpRequest',
            })
    
    def _rotate_user_agent(self):
        """User-Agentをローテーション"""
        self.current_user_agent = self.user_agent_manager.get_random_agent(self.device_type)
        self._update_session_headers()
        self.logger.debug(f"User-Agentを変更: {self.current_user_agent[:50]}...")
    
    def _build_url(self, target_url: str, params: Dict[str, Any]) -> str:
        """
        リクエストURLを構築
        
        Args:
            target_url: スクレイピング対象URL
            params: パラメータ
            
        Returns:
            構築されたURL
        """
        # 必須パラメータを追加
        all_params = {
            'api_key': self.api_key,
            'url': target_url,
            **params
        }
        
        # パラメータをエンコード
        query_string = urlencode(all_params)
        return f"{self.base_url}?{query_string}"
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        レスポンスを処理
        
        Args:
            response: HTTPレスポンス
            
        Returns:
            処理されたレスポンスデータ
            
        Raises:
            APIError: API関連エラー
            RateLimitError: レート制限エラー
            AuthenticationError: 認証エラー
        """
        status_code = response.status_code
        
        # 成功
        if status_code == 200:
            return {
                'success': True,
                'status_code': status_code,
                'content': response.text,
                'headers': dict(response.headers)
            }
        
        # エラーハンドリング
        error_message = f"HTTP {status_code}"
        
        if status_code == 401:
            raise AuthenticationError("API キーが無効です")
        elif status_code == 403:
            raise AuthenticationError("アクセスが拒否されました")
        elif status_code == 429:
            retry_after = int(response.headers.get('Retry-After', self.rate_limit_delay))
            raise RateLimitError(
                "レート制限に達しました",
                retry_after=retry_after
            )
        elif status_code >= 500:
            raise APIError(
                f"サーバーエラー: {error_message}",
                status_code=status_code,
                response_text=response.text
            )
        else:
            raise APIError(
                f"APIエラー: {error_message}",
                status_code=status_code,
                response_text=response.text
            )
    
    @retry_on_exception(max_retries=3, delay=1.0)
    def scrape(
        self,
        url: str,
        render_js: bool = True,
        country_code: str = "JP",
        device_type: str = "desktop",
        premium: bool = True,
        session_number: Optional[int] = None,
        keep_headers: bool = True,
        output_format: str = "text",
        custom_params: Optional[Dict[str, Any]] = None,
        rotate_user_agent: bool = True,
        use_proxy_rotation: bool = True
    ) -> Dict[str, Any]:
        """
        URLをスクレイピング（改良版）
        
        Args:
            url: スクレイピング対象URL
            render_js: JavaScript実行を有効にするか
            country_code: 国コード
            device_type: デバイスタイプ
            premium: プレミアム機能を使用するか
            session_number: セッション番号
            keep_headers: ヘッダーを保持するか
            output_format: 出力形式
            custom_params: カスタムパラメータ
            rotate_user_agent: User-Agentをローテーションするか
            use_proxy_rotation: プロキシローテーションを使用するか
            
        Returns:
            スクレイピング結果
            
        Raises:
            APIError: API関連エラー
            NetworkError: ネットワークエラー
        """
        # URL検証
        if not validate_url(url):
            raise ValueError(f"無効なURL: {url}")
        
        # リクエスト制御
        if self.request_throttle:
            wait_time = self.request_throttle.wait_if_needed()
            if wait_time > 0:
                self.logger.info(f"リクエスト制御: {wait_time:.2f}秒待機しました")
        
        # User-Agentローテーション
        if rotate_user_agent:
            self._rotate_user_agent()
        
        # プロキシ選択
        proxy = None
        if use_proxy_rotation:
            proxy = self.proxy_manager.get_proxy_for_country(country_code)
            if not proxy:
                proxy = self.proxy_manager.get_next_proxy()
        
        # パラメータ構築
        params = {
            'render': 'true' if render_js else 'false',
            'country_code': country_code,
            'device_type': device_type,
            'premium': 'true' if premium else 'false',
            'keep_headers': 'true' if keep_headers else 'false',
            'format': output_format,
            'wait': 5000,  # JavaScript読み込み待機時間を増加
            'timeout': self.timeout * 1000,  # ミリ秒に変換
        }
        
        # セッション番号設定
        if session_number is None:
            session_number = random.randint(1, 10000)
        params['session_number'] = session_number
        
        # プロキシパラメータを追加
        if proxy:
            proxy_params = self.proxy_manager.get_scraperapi_params(proxy)
            params.update(proxy_params)
        
        # カスタムパラメータを追加
        if custom_params:
            params.update(custom_params)
        
        # リクエストURL構築
        request_url = self._build_url(url, params)
        
        self.logger.info(f"スクレイピング開始: {url}")
        if proxy:
            self.logger.debug(f"使用プロキシ: {proxy.country}")
        
        try:
            # HTTPリクエスト実行
            response = self.session.get(
                request_url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # レスポンス処理
            result = self._handle_response(response)
            
            # プロキシ成功を記録
            if proxy:
                self.proxy_manager.record_proxy_result(proxy, True)
            
            # 人間らしい読み取り時間をシミュレート
            if self.request_throttle:
                content_length = len(result.get('content', ''))
                reading_time = self.request_throttle.simulate_reading_time(content_length)
                if reading_time > 1.0:  # 1秒以上の場合のみ実行
                    self.logger.debug(f"読み取り時間シミュレート: {reading_time:.2f}秒")
                    time.sleep(reading_time)
            
            self.logger.info(f"スクレイピング成功: {url}")
            return result
            
        except (RateLimitError, AuthenticationError) as e:
            # プロキシ失敗を記録
            if proxy:
                self.proxy_manager.record_proxy_result(proxy, False)
            raise e
            
        except requests.exceptions.RequestException as e:
            # プロキシ失敗を記録
            if proxy:
                self.proxy_manager.record_proxy_result(proxy, False)
            
            self.logger.error(f"ネットワークエラー: {e}")
            raise NetworkError(f"リクエストに失敗しました: {e}")
        
        except Exception as e:
            # プロキシ失敗を記録
            if proxy:
                self.proxy_manager.record_proxy_result(proxy, False)
            
            self.logger.error(f"予期しないエラー: {e}")
            raise APIError(f"スクレイピングに失敗しました: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        stats = {
            "current_user_agent": self.current_user_agent,
            "device_type": self.device_type,
        }
        
        # プロキシ統計
        if self.proxy_manager:
            stats["proxy_stats"] = self.proxy_manager.get_proxy_stats()
        
        # リクエスト制御統計
        if self.request_throttle:
            stats["throttle_stats"] = self.request_throttle.get_stats()
        
        return stats
    
    def close(self):
        """セッションを閉じる"""
        if self.session:
            self.session.close()
            self.logger.info("ScraperAPI セッションを閉じました")

