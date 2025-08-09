"""
Logging utilities for TikTok Research System
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
import colorlog


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "tiktok_research.log",
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    ログシステムをセットアップ
    
    Args:
        log_level: ログレベル
        log_dir: ログディレクトリ
        log_file: ログファイル名
        enable_console: コンソール出力を有効にするか
        enable_file: ファイル出力を有効にするか
        
    Returns:
        設定されたロガー
    """
    # ログディレクトリの作成
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # ルートロガーの設定
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマッターの設定
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # コンソールハンドラー
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # ファイルハンドラー（ローテーション対応）
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # エラー専用ログファイル
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "error.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    名前付きロガーを取得
    
    Args:
        name: ロガー名
        log_level: ログレベル（オプション）
        
    Returns:
        ロガーインスタンス
    """
    logger = logging.getLogger(name)
    
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger


class LoggerMixin:
    """ログ機能を提供するMixin"""
    
    @property
    def logger(self) -> logging.Logger:
        """ロガーを取得"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


class PerformanceLogger:
    """パフォーマンス測定用ロガー"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_time = None
        self.metrics = {}
    
    def start(self, operation: str):
        """測定開始"""
        import time
        self.start_time = time.time()
        self.logger.info(f"開始: {operation}")
    
    def end(self, operation: str):
        """測定終了"""
        if self.start_time:
            import time
            elapsed = time.time() - self.start_time
            self.metrics[operation] = elapsed
            self.logger.info(f"完了: {operation} (実行時間: {elapsed:.2f}秒)")
            self.start_time = None
    
    def log_metrics(self):
        """メトリクスをログ出力"""
        if self.metrics:
            self.logger.info("パフォーマンスメトリクス:")
            for operation, elapsed in self.metrics.items():
                self.logger.info(f"  {operation}: {elapsed:.2f}秒")


# デフォルトロガーの初期化
def init_default_logger():
    """デフォルトロガーを初期化"""
    try:
        from .config import config
        monitoring_config = config.get_monitoring_config()
        
        return setup_logging(
            log_level=monitoring_config.get('log_level', 'INFO'),
            log_dir=monitoring_config.get('log_dir', 'logs'),
            enable_console=True,
            enable_file=monitoring_config.get('enabled', True)
        )
    except ImportError:
        # config モジュールが利用できない場合のフォールバック
        return setup_logging()


# モジュール読み込み時にデフォルトロガーを初期化
try:
    default_logger = init_default_logger()
except Exception:
    # 初期化に失敗した場合の基本ロガー
    default_logger = setup_logging()

