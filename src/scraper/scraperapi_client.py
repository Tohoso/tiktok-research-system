"""
ScraperAPI client for TikTok Research System
"""

import time
import requests
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode

from ..utils.logger import get_logger
from ..utils.helpers import retry_on_exception, validate_url
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
        rate_limit_delay: float = 2.0
    ):
        """
        ScraperAPI クライアントを初期化
        
        Args:
            api_key: ScraperAPI キー
            base_url: ベースURL
            timeout: タイムアウト（秒）
            max_retries: 最大リトライ回数
            rate_limit_delay: レート制限時の待機時間（秒）
        """
        if not api_key or api_key == "your_scraperapi_key_here":
            raise ConfigurationError("有効なScraperAPI キーが設定されていません")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay
        
        self.logger = get_logger(self.__class__.__name__)
        self.session = requests.Session()
        
        # セッションのデフォルト設定
        self.session.headers.update({
            'User-Agent': 'TikTok-Research-System/1.0'
        })
        
        self.logger.info("ScraperAPI クライアントを初期化しました")
    
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
        premium: bool = False,
        session_number: Optional[int] = None,
        keep_headers: bool = True,
        output_format: str = "text",
        custom_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        URLをスクレイピング
        
        Args:
            url: スクレイピング対象URL
            render_js: JavaScript実行を有効にするか
            country_code: 国コード
            device_type: デバイスタイプ
            premium: プレミアムプロキシを使用するか
            session_number: セッション番号
            keep_headers: ヘッダーを保持するか
            output_format: 出力形式
            custom_params: カスタムパラメータ
            
        Returns:
            スクレイピング結果
            
        Raises:
            ValidationError: URLが無効
            NetworkError: ネットワークエラー
            APIError: API関連エラー
        """
        # URLバリデーション
        if not validate_url(url):
            raise ValidationError(f"無効なURL: {url}")
        
        # パラメータ構築
        params = {
            'render': 'true' if render_js else 'false',
            'country_code': country_code,
            'device_type': device_type,
            'output_format': output_format
        }
        
        if premium:
            params['premium'] = 'true'
        
        if session_number is not None:
            params['session_number'] = session_number
        
        if keep_headers:
            params['keep_headers'] = 'true'
        
        # カスタムパラメータを追加
        if custom_params:
            params.update(custom_params)
        
        # リクエストURL構築
        request_url = self._build_url(url, params)
        
        self.logger.info(f"スクレイピング開始: {url}")
        self.logger.debug(f"パラメータ: {params}")
        
        try:
            # レート制限対応
            time.sleep(self.rate_limit_delay)
            
            # リクエスト実行
            response = self.session.get(
                request_url,
                timeout=self.timeout
            )
            
            # レスポンス処理
            result = self._handle_response(response)
            
            self.logger.info(f"スクレイピング成功: {url}")
            return result
            
        except requests.exceptions.Timeout:
            error_msg = f"タイムアウト: {url}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg)
            
        except requests.exceptions.ConnectionError as e:
            error_msg = f"接続エラー: {url}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg, original_exception=e)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"リクエストエラー: {url}"
            self.logger.error(error_msg)
            raise NetworkError(error_msg, original_exception=e)
        
        except RateLimitError as e:
            self.logger.warning(f"レート制限: {url}, {e.retry_after}秒後にリトライ")
            time.sleep(e.retry_after)
            raise
    
    def scrape_tiktok_explore(
        self,
        country_code: str = "JP",
        render_js: bool = True,
        device_type: str = "desktop"
    ) -> Dict[str, Any]:
        """
        TikTok /exploreページをスクレイピング
        
        Args:
            country_code: 国コード
            render_js: JavaScript実行を有効にするか
            device_type: デバイスタイプ
            
        Returns:
            スクレイピング結果
        """
        explore_url = "https://www.tiktok.com/explore"
        
        return self.scrape(
            url=explore_url,
            render_js=render_js,
            country_code=country_code,
            device_type=device_type,
            premium=True,  # TikTokは高度な対策があるためプレミアム使用
            output_format="text"
        )
    
    def test_connection(self) -> bool:
        """
        接続テスト
        
        Returns:
            接続成功かどうか
        """
        try:
            # 簡単なテストページでテスト
            test_url = "https://httpbin.org/html"
            result = self.scrape(
                url=test_url,
                render_js=False,
                country_code="US"
            )
            
            success = result.get('success', False)
            self.logger.info(f"接続テスト結果: {'成功' if success else '失敗'}")
            return success
            
        except Exception as e:
            self.logger.error(f"接続テスト失敗: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        アカウント情報を取得
        
        Returns:
            アカウント情報
        """
        try:
            # ScraperAPIのアカウント情報エンドポイント
            account_url = f"{self.base_url}/account"
            params = {'api_key': self.api_key}
            
            response = self.session.get(
                account_url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"アカウント情報取得失敗: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"アカウント情報取得エラー: {e}")
            return {}
    
    def close(self):
        """セッションを閉じる"""
        if self.session:
            self.session.close()
            self.logger.info("ScraperAPI セッションを閉じました")

