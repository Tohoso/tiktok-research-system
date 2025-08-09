"""
System monitoring for TikTok Research System
"""

import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..utils.logger import get_logger


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent: int
    network_recv: int
    process_count: int


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    timestamp: datetime
    operation: str
    duration: float
    success: bool
    error_message: Optional[str] = None


class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self, monitoring_interval: int = 60):
        """
        システムモニターを初期化
        
        Args:
            monitoring_interval: 監視間隔（秒）
        """
        self.logger = get_logger(self.__class__.__name__)
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        
        # メトリクス履歴
        self.system_metrics_history: List[SystemMetrics] = []
        self.performance_metrics_history: List[PerformanceMetrics] = []
        
        # アラート閾値
        self.alert_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate': 0.1,  # 10%
            'response_time': 30.0  # 30秒
        }
        
        # 初期ネットワーク統計を取得
        self._initial_network_stats = psutil.net_io_counters()
        
        self.logger.info("システムモニターを初期化しました")
    
    def start_monitoring(self):
        """監視を開始"""
        self.is_monitoring = True
        self.logger.info("システム監視を開始しました")
    
    def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
        self.logger.info("システム監視を停止しました")
    
    def collect_system_metrics(self) -> SystemMetrics:
        """
        システムメトリクスを収集
        
        Returns:
            システムメトリクス
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # ネットワーク統計
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent - self._initial_network_stats.bytes_sent
            network_recv = network.bytes_recv - self._initial_network_stats.bytes_recv
            
            # プロセス数
            process_count = len(psutil.pids())
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_sent=network_sent,
                network_recv=network_recv,
                process_count=process_count
            )
            
            # 履歴に追加
            self.system_metrics_history.append(metrics)
            
            # 古いデータを削除（24時間分のみ保持）
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.system_metrics_history = [
                m for m in self.system_metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"システムメトリクス収集エラー: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_sent=0,
                network_recv=0,
                process_count=0
            )
    
    def record_performance_metric(
        self,
        operation: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        パフォーマンスメトリクスを記録
        
        Args:
            operation: 操作名
            duration: 実行時間（秒）
            success: 成功フラグ
            error_message: エラーメッセージ
        """
        metric = PerformanceMetrics(
            timestamp=datetime.now(),
            operation=operation,
            duration=duration,
            success=success,
            error_message=error_message
        )
        
        self.performance_metrics_history.append(metric)
        
        # 古いデータを削除（24時間分のみ保持）
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.performance_metrics_history = [
            m for m in self.performance_metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # アラートチェック
        self._check_performance_alerts(metric)
    
    def _check_performance_alerts(self, metric: PerformanceMetrics):
        """パフォーマンスアラートをチェック"""
        # 応答時間アラート
        if metric.duration > self.alert_thresholds['response_time']:
            self.logger.warning(
                f"応答時間アラート: {metric.operation} が {metric.duration:.2f}秒かかりました"
            )
        
        # エラーアラート
        if not metric.success:
            self.logger.error(
                f"操作エラー: {metric.operation} - {metric.error_message}"
            )
    
    def check_system_alerts(self, metrics: SystemMetrics) -> List[str]:
        """
        システムアラートをチェック
        
        Args:
            metrics: システムメトリクス
            
        Returns:
            アラートメッセージのリスト
        """
        alerts = []
        
        # CPU使用率アラート
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append(f"CPU使用率が高いです: {metrics.cpu_percent:.1f}%")
        
        # メモリ使用率アラート
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append(f"メモリ使用率が高いです: {metrics.memory_percent:.1f}%")
        
        # ディスク使用率アラート
        if metrics.disk_percent > self.alert_thresholds['disk_percent']:
            alerts.append(f"ディスク使用率が高いです: {metrics.disk_percent:.1f}%")
        
        # アラートをログ出力
        for alert in alerts:
            self.logger.warning(alert)
        
        return alerts
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        システム状態を取得
        
        Returns:
            システム状態情報
        """
        current_metrics = self.collect_system_metrics()
        alerts = self.check_system_alerts(current_metrics)
        
        # 最近のパフォーマンス統計
        recent_performance = self._get_recent_performance_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': {
                'cpu_percent': current_metrics.cpu_percent,
                'memory_percent': current_metrics.memory_percent,
                'disk_percent': current_metrics.disk_percent,
                'network_sent_mb': current_metrics.network_sent / (1024 * 1024),
                'network_recv_mb': current_metrics.network_recv / (1024 * 1024),
                'process_count': current_metrics.process_count
            },
            'performance_metrics': recent_performance,
            'alerts': alerts,
            'monitoring_status': 'active' if self.is_monitoring else 'inactive'
        }
    
    def _get_recent_performance_stats(self, hours: int = 1) -> Dict[str, Any]:
        """最近のパフォーマンス統計を取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.performance_metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # 操作別統計
        operations = {}
        for metric in recent_metrics:
            if metric.operation not in operations:
                operations[metric.operation] = {
                    'count': 0,
                    'success_count': 0,
                    'total_duration': 0.0,
                    'max_duration': 0.0,
                    'errors': []
                }
            
            op_stats = operations[metric.operation]
            op_stats['count'] += 1
            op_stats['total_duration'] += metric.duration
            op_stats['max_duration'] = max(op_stats['max_duration'], metric.duration)
            
            if metric.success:
                op_stats['success_count'] += 1
            else:
                op_stats['errors'].append(metric.error_message)
        
        # 統計を計算
        for op_name, op_stats in operations.items():
            op_stats['success_rate'] = op_stats['success_count'] / op_stats['count']
            op_stats['avg_duration'] = op_stats['total_duration'] / op_stats['count']
            op_stats['error_count'] = len(op_stats['errors'])
        
        return {
            'total_operations': len(recent_metrics),
            'operations': operations,
            'time_range_hours': hours
        }
    
    def get_historical_metrics(
        self,
        hours: int = 24,
        metric_type: str = "system"
    ) -> List[Dict[str, Any]]:
        """
        履歴メトリクスを取得
        
        Args:
            hours: 取得時間範囲
            metric_type: メトリクスタイプ（"system" または "performance"）
            
        Returns:
            履歴メトリクスのリスト
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if metric_type == "system":
            metrics = [
                m for m in self.system_metrics_history 
                if m.timestamp > cutoff_time
            ]
            return [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_percent': m.cpu_percent,
                    'memory_percent': m.memory_percent,
                    'disk_percent': m.disk_percent,
                    'network_sent': m.network_sent,
                    'network_recv': m.network_recv,
                    'process_count': m.process_count
                }
                for m in metrics
            ]
        
        elif metric_type == "performance":
            metrics = [
                m for m in self.performance_metrics_history 
                if m.timestamp > cutoff_time
            ]
            return [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'operation': m.operation,
                    'duration': m.duration,
                    'success': m.success,
                    'error_message': m.error_message
                }
                for m in metrics
            ]
        
        return []
    
    def set_alert_threshold(self, metric: str, threshold: float):
        """
        アラート閾値を設定
        
        Args:
            metric: メトリクス名
            threshold: 閾値
        """
        if metric in self.alert_thresholds:
            old_threshold = self.alert_thresholds[metric]
            self.alert_thresholds[metric] = threshold
            self.logger.info(f"アラート閾値を更新: {metric} {old_threshold} → {threshold}")
        else:
            self.logger.warning(f"不明なメトリクス: {metric}")
    
    def get_health_score(self) -> float:
        """
        システムヘルススコアを計算
        
        Returns:
            ヘルススコア（0-100）
        """
        try:
            current_metrics = self.collect_system_metrics()
            
            # 各メトリクスのスコアを計算（100点満点）
            cpu_score = max(0, 100 - current_metrics.cpu_percent)
            memory_score = max(0, 100 - current_metrics.memory_percent)
            disk_score = max(0, 100 - current_metrics.disk_percent)
            
            # パフォーマンススコア
            recent_performance = self._get_recent_performance_stats(hours=1)
            performance_score = 100
            
            if recent_performance and 'operations' in recent_performance:
                success_rates = [
                    op['success_rate'] for op in recent_performance['operations'].values()
                ]
                if success_rates:
                    avg_success_rate = sum(success_rates) / len(success_rates)
                    performance_score = avg_success_rate * 100
            
            # 重み付き平均
            weights = {
                'cpu': 0.25,
                'memory': 0.25,
                'disk': 0.25,
                'performance': 0.25
            }
            
            health_score = (
                cpu_score * weights['cpu'] +
                memory_score * weights['memory'] +
                disk_score * weights['disk'] +
                performance_score * weights['performance']
            )
            
            return round(health_score, 2)
            
        except Exception as e:
            self.logger.error(f"ヘルススコア計算エラー: {e}")
            return 0.0
    
    def generate_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        監視レポートを生成
        
        Args:
            hours: レポート対象時間範囲
            
        Returns:
            監視レポート
        """
        try:
            current_status = self.get_system_status()
            historical_system = self.get_historical_metrics(hours, "system")
            historical_performance = self.get_historical_metrics(hours, "performance")
            health_score = self.get_health_score()
            
            # 統計計算
            if historical_system:
                avg_cpu = sum(m['cpu_percent'] for m in historical_system) / len(historical_system)
                avg_memory = sum(m['memory_percent'] for m in historical_system) / len(historical_system)
                max_cpu = max(m['cpu_percent'] for m in historical_system)
                max_memory = max(m['memory_percent'] for m in historical_system)
            else:
                avg_cpu = avg_memory = max_cpu = max_memory = 0
            
            return {
                'report_generated_at': datetime.now().isoformat(),
                'time_range_hours': hours,
                'health_score': health_score,
                'current_status': current_status,
                'summary_statistics': {
                    'avg_cpu_percent': round(avg_cpu, 2),
                    'avg_memory_percent': round(avg_memory, 2),
                    'max_cpu_percent': round(max_cpu, 2),
                    'max_memory_percent': round(max_memory, 2),
                    'total_system_samples': len(historical_system),
                    'total_performance_samples': len(historical_performance)
                },
                'historical_data': {
                    'system_metrics': historical_system[-100:],  # 最新100件
                    'performance_metrics': historical_performance[-100:]  # 最新100件
                }
            }
            
        except Exception as e:
            self.logger.error(f"監視レポート生成エラー: {e}")
            return {
                'error': str(e),
                'report_generated_at': datetime.now().isoformat()
            }

