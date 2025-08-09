"""
Exception classes for TikTok Research System scraper
"""


class ScraperError(Exception):
    """スクレイパーの基底例外クラス"""
    pass


class APIError(ScraperError):
    """API関連のエラー"""
    
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class RateLimitError(APIError):
    """レート制限エラー"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(APIError):
    """認証エラー"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class ParseError(ScraperError):
    """データパースエラー"""
    
    def __init__(self, message: str, raw_data: str = None):
        super().__init__(message)
        self.raw_data = raw_data


class NetworkError(ScraperError):
    """ネットワークエラー"""
    
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message)
        self.original_exception = original_exception


class ConfigurationError(ScraperError):
    """設定エラー"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.config_key = config_key


class ValidationError(ScraperError):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message)
        self.field = field
        self.value = value

