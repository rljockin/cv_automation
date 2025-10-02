#!/usr/bin/env python3
"""
Monitoring System - Real-time system monitoring
Generic monitoring system with metrics collection, alerting, and performance tracking
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict

from src.core import CVFile


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class SystemHealth:
    """System health status"""
    status: str  # "healthy", "degraded", "unhealthy"
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_processes: int
    uptime_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)


class MonitoringSystem:
    """
    Generic monitoring system with comprehensive metrics and alerting
    
    Features:
    - Real-time metrics collection
    - System health monitoring
    - Custom metric tracking
    - Alert management
    - Performance analysis
    - Historical data storage
    - Dashboard data generation
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize monitoring system"""
        self.config = config or {}
        
        # Monitoring configuration
        self.collection_interval = self.config.get('collection_interval', 5)  # seconds
        self.retention_hours = self.config.get('retention_hours', 24)
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        # Alerts
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # System monitoring
        self.start_time = datetime.now()
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.alert_callbacks: List[Callable[[Alert], Any]] = []
        self.metric_callbacks: List[Callable[[Metric], Any]] = []
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self._log("Started system monitoring")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self._log("Stopped system monitoring")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Check alerts
                self._check_alerts()
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep until next collection
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self._log(f"Monitoring loop error: {str(e)}", "ERROR")
                time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system.cpu.usage", cpu_percent, unit="percent")
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory.usage", memory.percent, unit="percent")
            self.record_gauge("system.memory.available", memory.available / (1024**3), unit="GB")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_gauge("system.disk.usage", disk_percent, unit="percent")
            self.record_gauge("system.disk.free", disk.free / (1024**3), unit="GB")
            
            # Process count
            process_count = len(psutil.pids())
            self.record_gauge("system.processes.count", process_count)
            
            # Uptime
            uptime = (datetime.now() - self.start_time).total_seconds()
            self.record_gauge("system.uptime", uptime, unit="seconds")
            
        except Exception as e:
            self._log(f"Failed to collect system metrics: {str(e)}", "ERROR")
    
    def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record counter metric"""
        self.counters[name] += value
        metric = Metric(
            name=name,
            value=self.counters[name],
            metric_type=MetricType.COUNTER,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def record_gauge(self, name: str, value: float, unit: str = "", labels: Dict[str, str] = None):
        """Record gauge metric"""
        self.gauges[name] = value
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,
            unit=unit,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram metric"""
        self.histograms[name].append(value)
        metric = Metric(
            name=name,
            value=value,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def record_timer(self, name: str, duration_seconds: float, labels: Dict[str, str] = None):
        """Record timer metric"""
        self.timers[name].append(duration_seconds)
        metric = Metric(
            name=name,
            value=duration_seconds,
            metric_type=MetricType.TIMER,
            unit="seconds",
            labels=labels or {}
        )
        self._store_metric(metric)
    
    def time_operation(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations"""
        return TimerContext(self, name, labels)
    
    def _store_metric(self, metric: Metric):
        """Store metric in time series"""
        self.metrics[metric.name].append(metric)
        
        # Call metric callbacks
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self._log(f"Metric callback error: {str(e)}", "ERROR")
    
    def _check_alerts(self):
        """Check for alert conditions"""
        for metric_name, threshold_config in self.alert_thresholds.items():
            try:
                current_value = self.gauges.get(metric_name, 0)
                
                # Check each threshold
                for level, threshold_value in threshold_config.items():
                    if self._should_trigger_alert(level, current_value, threshold_value):
                        self._trigger_alert(metric_name, level, current_value, threshold_value)
                
            except Exception as e:
                self._log(f"Alert check error for {metric_name}: {str(e)}", "ERROR")
    
    def _should_trigger_alert(self, level: str, current_value: float, threshold_value: float) -> bool:
        """Check if alert should be triggered"""
        alert_id = f"{level}_{threshold_value}"
        
        # Check if alert already exists
        if alert_id in self.active_alerts:
            return False
        
        # Check threshold conditions
        if level == "warning" and current_value > threshold_value:
            return True
        elif level == "error" and current_value > threshold_value:
            return True
        elif level == "critical" and current_value > threshold_value:
            return True
        
        return False
    
    def _trigger_alert(self, metric_name: str, level: str, current_value: float, threshold_value: float):
        """Trigger an alert"""
        alert_id = f"{metric_name}_{level}_{threshold_value}"
        
        alert = Alert(
            id=alert_id,
            level=AlertLevel(level),
            message=f"{metric_name} is {current_value:.2f}, exceeds threshold {threshold_value:.2f}",
            metric_name=metric_name,
            threshold_value=threshold_value,
            current_value=current_value
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self._log(f"Alert callback error: {str(e)}", "ERROR")
        
        self._log(f"Alert triggered: {alert.message}", level.upper())
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            
            self._log(f"Alert resolved: {alert_id}")
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health status"""
        cpu_usage = self.gauges.get("system.cpu.usage", 0)
        memory_usage = self.gauges.get("system.memory.usage", 0)
        disk_usage = self.gauges.get("system.disk.usage", 0)
        process_count = self.gauges.get("system.processes.count", 0)
        uptime = self.gauges.get("system.uptime", 0)
        
        # Determine overall health status
        status = "healthy"
        if cpu_usage > 90 or memory_usage > 90 or disk_usage > 95:
            status = "unhealthy"
        elif cpu_usage > 80 or memory_usage > 80 or disk_usage > 85:
            status = "degraded"
        
        return SystemHealth(
            status=status,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            active_processes=process_count,
            uptime_seconds=uptime
        )
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        summary = {
            'time_period_hours': hours,
            'metrics': {},
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'active_alerts': len(self.active_alerts),
            'system_health': self.get_system_health()
        }
        
        # Process time series metrics
        for metric_name, metric_series in self.metrics.items():
            # Filter by time period
            recent_metrics = [m for m in metric_series if m.timestamp >= cutoff_time]
            
            if recent_metrics:
                values = [m.value for m in recent_metrics]
                summary['metrics'][metric_name] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'avg': sum(values) / len(values),
                    'latest': values[-1] if values else 0,
                    'unit': recent_metrics[0].unit
                }
        
        return summary
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate throughput metrics
        total_files_processed = self.counters.get("files.processed", 0)
        throughput_per_hour = (total_files_processed / uptime) * 3600 if uptime > 0 else 0
        
        # Calculate average processing times
        processing_times = self.timers.get("file.processing_time", [])
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Calculate success rate
        successful_files = self.counters.get("files.processed.success", 0)
        failed_files = self.counters.get("files.processed.failed", 0)
        success_rate = successful_files / (successful_files + failed_files) if (successful_files + failed_files) > 0 else 0
        
        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'total_files_processed': total_files_processed,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': success_rate,
            'throughput_per_hour': throughput_per_hour,
            'average_processing_time_seconds': avg_processing_time,
            'system_health': self.get_system_health(),
            'active_alerts': len(self.active_alerts),
            'total_alerts_triggered': len(self.alert_history),
            'metrics_collected': len(self.metrics),
            'memory_usage_mb': self.gauges.get("system.memory.usage", 0) * psutil.virtual_memory().total / (1024**2) / 100
        }
    
    def track_file_processing(self, cv_file: CVFile, success: bool, processing_time: float):
        """Track file processing metrics"""
        # Record counters
        self.record_counter("files.processed")
        if success:
            self.record_counter("files.processed.success")
        else:
            self.record_counter("files.processed.failed")
        
        # Record processing time
        self.record_timer("file.processing_time", processing_time)
        
        # Record file size metrics
        self.record_histogram("file.size", cv_file.file_size)
        
        # Record by file format
        self.record_counter(f"files.processed.{cv_file.file_format.value}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        # Clean up metrics
        for metric_name, metric_series in self.metrics.items():
            # Remove old metrics
            while metric_series and metric_series[0].timestamp < cutoff_time:
                metric_series.popleft()
        
        # Clean up old alerts
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert.timestamp >= cutoff_time
        ]
    
    def _initialize_default_thresholds(self):
        """Initialize default alert thresholds"""
        if not self.alert_thresholds:
            self.alert_thresholds = {
                "system.cpu.usage": {
                    "warning": 80.0,
                    "error": 90.0,
                    "critical": 95.0
                },
                "system.memory.usage": {
                    "warning": 80.0,
                    "error": 90.0,
                    "critical": 95.0
                },
                "system.disk.usage": {
                    "warning": 85.0,
                    "error": 90.0,
                    "critical": 95.0
                },
                "file.processing_time": {
                    "warning": 300.0,  # 5 minutes
                    "error": 600.0,    # 10 minutes
                    "critical": 1200.0  # 20 minutes
                }
            }
    
    def add_alert_callback(self, callback: Callable[[Alert], Any]):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def add_metric_callback(self, callback: Callable[[Metric], Any]):
        """Add metric callback"""
        self.metric_callbacks.append(callback)
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] [MonitoringSystem] {message}")


class TimerContext:
    """Context manager for timing operations"""
    
    def __init__(self, monitoring_system: MonitoringSystem, name: str, labels: Dict[str, str] = None):
        self.monitoring_system = monitoring_system
        self.name = name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.monitoring_system.record_timer(self.name, duration, self.labels)
