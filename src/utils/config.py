"""
Configuration management for TikTok Research System
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        設定を初期化
        
        Args:
            config_file: 設定ファイルのパス（デフォルト: config/config.yaml）
        """
        self.config_file = config_file or "config/config.yaml"
        self.config_data = {}
        self._load_config()
    
    def _load_config(self):
        """設定ファイルを読み込み"""
        # .env ファイルを読み込み
        env_file = Path("config/.env")
        if env_file.exists():
            load_dotenv(env_file)
        
        # YAML設定ファイルを読み込み
        config_path = Path(self.config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_data = yaml.safe_load(f)
                
            # 環境変数の置換
            self._substitute_env_vars(self.config_data)
        else:
            # デフォルト設定
            self.config_data = self._get_default_config()
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """環境変数を置換"""
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str) and data.startswith('${') and data.endswith('}'):
            env_var = data[2:-1]
            return os.getenv(env_var, data)
        else:
            return data
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を取得"""
        return {
            'scraper': {
                'api_key': os.getenv('SCRAPERAPI_KEY', ''),
                'base_url': os.getenv('SCRAPERAPI_BASE_URL', 'http://api.scraperapi.com'),
                'timeout': 60,
                'max_retries': 3,
                'rate_limit_delay': 2
            },
            'tiktok': {
                'explore_url': os.getenv('TIKTOK_EXPLORE_URL', 'https://www.tiktok.com/explore'),
                'country_code': os.getenv('TARGET_COUNTRY', 'JP'),
                'render_js': True,
                'device_type': 'desktop'
            },
            'filters': {
                'min_views': int(os.getenv('MIN_VIEWS', 500000)),
                'time_range_hours': int(os.getenv('TIME_RANGE_HOURS', 24)),
                'exclude_duplicates': True
            },
            'storage': {
                'database_file': os.getenv('DATABASE_FILE', 'data/tiktok_videos.db'),
                'data_dir': os.getenv('DATA_DIR', 'data'),
                'backup_enabled': True
            },
            'monitoring': {
                'enabled': os.getenv('ENABLE_MONITORING', 'true').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                'log_dir': os.getenv('LOG_DIR', 'logs'),
                'alert_on_errors': True
            },
            'scheduler': {
                'enabled': False,
                'interval_minutes': 60,
                'max_concurrent_jobs': 1
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            key: 設定キー（ドット記法対応: 'scraper.api_key'）
            default: デフォルト値
            
        Returns:
            設定値
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        設定値を設定
        
        Args:
            key: 設定キー（ドット記法対応）
            value: 設定値
        """
        keys = key.split('.')
        data = self.config_data
        
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        data[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        設定の妥当性をチェック
        
        Returns:
            妥当性チェック結果
        """
        required_keys = [
            'scraper.api_key',
            'tiktok.explore_url',
            'tiktok.country_code',
            'filters.min_views',
            'filters.time_range_hours'
        ]
        
        for key in required_keys:
            value = self.get(key)
            if not value:
                return False
        
        # API キーの形式チェック
        api_key = self.get('scraper.api_key')
        if api_key == 'your_scraperapi_key_here' or len(api_key) < 10:
            return False
        
        return True
    
    def get_scraper_config(self) -> Dict[str, Any]:
        """スクレイパー設定を取得"""
        return self.get('scraper', {})
    
    def get_tiktok_config(self) -> Dict[str, Any]:
        """TikTok設定を取得"""
        return self.get('tiktok', {})
    
    def get_filter_config(self) -> Dict[str, Any]:
        """フィルター設定を取得"""
        return self.get('filters', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """ストレージ設定を取得"""
        return self.get('storage', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """監視設定を取得"""
        return self.get('monitoring', {})


# グローバル設定インスタンス
config = Config()

