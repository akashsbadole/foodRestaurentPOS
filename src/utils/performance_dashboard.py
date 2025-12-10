"""
Performance Monitoring Dashboard for Desktop POS Application
Real-time performance monitoring and reporting for Tkinter UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from collections import deque
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import os
import queue

from src.config.performance_config import PerformanceConfig
from src.models.optimized_database import DatabasePerformanceManager
from src.utils.memory_monitor import MemoryMonitor

class MetricType(Enum):
    """Performance metric types"""
    CPU = "cpu"
    MEMORY = "memory"
    DATABASE = "database"
    CACHE = "cache"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"

@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: float
    metric_type: MetricType
    value: float
    unit: str
    tags: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'unit': self.unit,
            'tags': self.tags
        }

@dataclass
class SystemResource:
    """System resource information"""
    cpu_percent: float
    memory_percent: float
    memory_used: float
    memory_total: float
    disk_percent: float
    disk_used: float
    disk_total: float
    network_sent: float
    network_received: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'disk_percent': self.disk_percent,
            'disk_used': self.disk_used,
            'disk_total': self.disk_total,
            'network_sent': self.network_sent,
            'network_received': self.network_received,
            'timestamp': self.timestamp
        }

class DesktopPerformanceMonitor:
    """Desktop performance monitoring system"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage
        self.metrics = {
            MetricType.CPU: deque(maxlen=1000),
            MetricType.MEMORY: deque(maxlen=1000),
            MetricType.DATABASE: deque(maxlen=1000),
            MetricType.CACHE: deque(maxlen=1000),
            MetricType.RESPONSE_TIME: deque(maxlen=1000),
            MetricType.THROUGHPUT: deque(maxlen=1000),
            MetricType.ERROR_RATE: deque(maxlen=1000)
        }
        
        # System resources
        self.system_resources = deque(maxlen=100)
        
        # Performance thresholds
        self.thresholds = {
            MetricType.CPU: 80.0,
            MetricType.MEMORY: 85.0,
            MetricType.DATABASE: 100.0,  # ms
            MetricType.RESPONSE_TIME: 500.0,  # ms
            MetricType.ERROR_RATE: 5.0  # percentage
        }
        
        # Alert callbacks
        self.alert_callbacks = []
        
        # Monitoring state
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_lock = threading.RLock()
        
        # Database performance manager
        self.db_perf_manager = DatabasePerformanceManager()
        
        # Memory monitor
        self.memory_monitor = MemoryMonitor(config)
        
        # Cache performance tracker
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Response time tracker
        self.response_times = deque(maxlen=100)
        
        # Error tracking
        self.error_count = 0
        self.total_requests = 0
        
        # UI update queue
        self.ui_update_queue = queue.Queue()
        
        # Initialize monitoring
        self._initialize_monitoring()
    
    def _initialize_monitoring(self):
        """Initialize monitoring system"""
        # Start monitoring thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Desktop performance monitoring initialized")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Collect database metrics
                self._collect_database_metrics()
                
                # Collect cache metrics
                self._collect_cache_metrics()
                
                # Collect memory metrics
                self._collect_memory_metrics()
                
                # Check thresholds
                self._check_thresholds()
                
                # Queue UI update
                self.ui_update_queue.put('update')
                
                # Sleep for configured interval
                time.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(5)
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Create system resource record
            resource = SystemResource(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_percent=disk.percent,
                disk_used=disk.used,
                disk_total=disk.total,
                network_sent=network.bytes_sent,
                network_received=network.bytes_recv,
                timestamp=time.time()
            )
            
            # Add to resources
            self.system_resources.append(resource)
            
            # Add individual metrics
            self.add_metric(MetricType.CPU, cpu_percent, "%", {"source": "system"})
            self.add_metric(MetricType.MEMORY, memory.percent, "%", {"source": "system"})
            
            # Calculate network throughput
            if len(self.system_resources) > 1:
                prev_resource = self.system_resources[-2]
                current_time = resource.timestamp
                prev_time = prev_resource.timestamp
                
                if current_time > prev_time:
                    time_diff = current_time - prev_time
                    network_sent = (resource.network_sent - prev_resource.network_sent) / time_diff
                    network_received = (resource.network_received - prev_resource.network_received) / time_diff
                    
                    self.add_metric(MetricType.THROUGHPUT, network_sent, "bytes/s", {"type": "network_sent"})
                    self.add_metric(MetricType.THROUGHPUT, network_received, "bytes/s", {"type": "network_received"})
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            # Get database metrics from performance manager
            db_stats = self.db_perf_manager.get_performance_stats()
            
            # Add database metrics
            self.add_metric(MetricType.DATABASE, db_stats.get('avg_query_time', 0), "ms", {"source": "database"})
            self.add_metric(MetricType.DATABASE, db_stats.get('connection_pool_size', 0), "connections", {"type": "pool_size"})
            self.add_metric(MetricType.DATABASE, db_stats.get('active_connections', 0), "connections", {"type": "active"})
            
        except Exception as e:
            self.logger.error(f"Error collecting database metrics: {e}")
    
    def _collect_cache_metrics(self):
        """Collect cache performance metrics"""
        try:
            # Calculate cache hit rate
            total_requests = self.cache_hits + self.cache_misses
            if total_requests > 0:
                hit_rate = (self.cache_hits / total_requests) * 100
                self.add_metric(MetricType.CACHE, hit_rate, "%", {"type": "hit_rate"})
            
            # Add cache size metrics
            # This would be implemented based on your cache system
            
        except Exception as e:
            self.logger.error(f"Error collecting cache metrics: {e}")
    
    def _collect_memory_metrics(self):
        """Collect memory metrics"""
        try:
            # Get memory metrics from memory monitor
            memory_stats = self.memory_monitor.get_memory_stats()
            
            # Add memory metrics
            self.add_metric(MetricType.MEMORY, memory_stats.get('memory_percent', 0), "%", {"source": "detailed"})
            self.add_metric(MetricType.MEMORY, memory_stats.get('objects_count', 0), "objects", {"type": "objects"})
            
        except Exception as e:
            self.logger.error(f"Error collecting memory metrics: {e}")
    
    def _check_thresholds(self):
        """Check performance thresholds and trigger alerts"""
        for metric_type, threshold in self.thresholds.items():
            if metric_type in self.metrics:
                recent_metrics = list(self.metrics[metric_type])[-10:]  # Last 10 measurements
                
                for metric in recent_metrics:
                    if metric.value > threshold:
                        self._trigger_alert(metric_type, metric.value, threshold)
    
    def _trigger_alert(self, metric_type: MetricType, value: float, threshold: float):
        """Trigger performance alert"""
        alert = {
            'metric_type': metric_type.value,
            'value': value,
            'threshold': threshold,
            'timestamp': time.time(),
            'message': f"{metric_type.value} performance threshold exceeded: {value} > {threshold}"
        }
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
        
        self.logger.warning(f"Performance alert: {alert['message']}")
    
    def add_metric(self, metric_type: MetricType, value: float, unit: str, tags: Dict[str, str] = None):
        """Add performance metric"""
        if tags is None:
            tags = {}
        
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_type=metric_type,
            value=value,
            unit=unit,
            tags=tags
        )
        
        self.metrics[metric_type].append(metric)
    
    def record_response_time(self, response_time: float):
        """Record response time"""
        self.response_times.append(response_time)
        self.add_metric(MetricType.RESPONSE_TIME, response_time, "ms")
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1
    
    def record_error(self):
        """Record error"""
        self.error_count += 1
        self.total_requests += 1
        
        # Calculate error rate
        error_rate = (self.error_count / self.total_requests) * 100
        self.add_metric(MetricType.ERROR_RATE, error_rate, "%")
    
    def record_request(self):
        """Record successful request"""
        self.total_requests += 1
    
    def get_metrics_summary(self, metric_type: MetricType, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        
        metrics = [m for m in self.metrics[metric_type] if m.timestamp >= cutoff_time]
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            'metric_type': metric_type.value,
            'count': len(metrics),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1],
            'timestamp': time.time()
        }
    
    def get_system_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get system resource summary"""
        cutoff_time = time.time() - (hours * 3600)
        
        resources = [r for r in self.system_resources if r.timestamp >= cutoff_time]
        
        if not resources:
            return {}
        
        return {
            'cpu': {
                'avg': sum(r.cpu_percent for r in resources) / len(resources),
                'max': max(r.cpu_percent for r in resources),
                'min': min(r.cpu_percent for r in resources)
            },
            'memory': {
                'avg': sum(r.memory_percent for r in resources) / len(resources),
                'max': max(r.memory_percent for r in resources),
                'min': min(r.memory_percent for r in resources)
            },
            'disk': {
                'avg': sum(r.disk_percent for r in resources) / len(resources),
                'max': max(r.disk_percent for r in resources),
                'min': min(r.disk_percent for r in resources)
            },
            'timestamp': time.time()
        }
    
    def get_database_summary(self) -> Dict[str, Any]:
        """Get database performance summary"""
        return self.db_perf_manager.get_performance_stats()
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get cache performance summary"""
        total_requests = self.cache_hits + self.cache_misses
        
        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'hit_rate': (self.cache_hits / total_requests * 100) if total_requests > 0 else 0,
            'total_requests': total_requests,
            'timestamp': time.time()
        }
    
    def get_response_time_summary(self) -> Dict[str, Any]:
        """Get response time summary"""
        if not self.response_times:
            return {}
        
        return {
            'count': len(self.response_times),
            'min': min(self.response_times),
            'max': max(self.response_times),
            'avg': sum(self.response_times) / len(self.response_times),
            'latest': self.response_times[-1],
            'timestamp': time.time()
        }
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        if self.total_requests == 0:
            return {}
        
        return {
            'total_errors': self.error_count,
            'total_requests': self.total_requests,
            'error_rate': (self.error_count / self.total_requests) * 100,
            'timestamp': time.time()
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        return {
            'timestamp': time.time(),
            'system': self.get_system_summary(),
            'database': self.get_database_summary(),
            'cache': self.get_cache_summary(),
            'response_time': self.get_response_time_summary(),
            'errors': self.get_error_summary(),
            'memory': self.memory_monitor.get_memory_stats(),
            'metrics': {
                'cpu': self.get_metrics_summary(MetricType.CPU),
                'memory': self.get_metrics_summary(MetricType.MEMORY),
                'database': self.get_metrics_summary(MetricType.DATABASE),
                'cache': self.get_metrics_summary(MetricType.CACHE),
                'response_time': self.get_metrics_summary(MetricType.RESPONSE_TIME),
                'throughput': self.get_metrics_summary(MetricType.THROUGHPUT),
                'error_rate': self.get_metrics_summary(MetricType.ERROR_RATE)
            }
        }
    
    def add_alert_callback(self, callback: Callable):
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def export_metrics(self, filename: str, hours: int = 24):
        """Export metrics to file"""
        try:
            data = {
                'export_timestamp': time.time(),
                'time_range_hours': hours,
                'metrics': {},
                'system_resources': []
            }
            
            # Export metrics
            for metric_type in MetricType:
                data['metrics'][metric_type.value] = [
                    metric.to_dict() for metric in self.metrics[metric_type]
                    if metric.timestamp >= (time.time() - (hours * 3600))
                ]
            
            # Export system resources
            data['system_resources'] = [
                resource.to_dict() for resource in self.system_resources
                if resource.timestamp >= (time.time() - (hours * 3600))
            ]
            
            # Write to file
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Metrics exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting metrics: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Desktop performance monitoring stopped")

class PerformanceDashboardUI:
    """Performance dashboard UI for Tkinter"""
    
    def __init__(self, parent, monitor: DesktopPerformanceMonitor):
        self.parent = parent
        self.monitor = monitor
        self.logger = logging.getLogger(__name__)
        
        # Dashboard data
        self.dashboard_data = {}
        self.last_update = 0
        self.update_interval = 5  # seconds
        
        # UI components
        self.widgets = {}
        self.frames = {}
        
        # Create UI
        self.create_ui()
        
        # Start UI updates
        self.update_ui()
    
    def create_ui(self):
        """Create dashboard UI"""
        # Main frame
        self.frames['main'] = ttk.Frame(self.parent)
        self.frames['main'].pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for different sections
        self.widgets['notebook'] = ttk.Notebook(self.frames['main'])
        self.widgets['notebook'].pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_overview_tab()
        self.create_metrics_tab()
        self.create_database_tab()
        self.create_memory_tab()
        self.create_settings_tab()
        
        # Status bar
        self.create_status_bar()
    
    def create_overview_tab(self):
        """Create overview tab"""
        frame = ttk.Frame(self.widgets['notebook'])
        self.widgets['notebook'].add(frame, text="Overview")
        
        # Create grid for overview
        grid_frame = ttk.Frame(frame)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System resources
        self.create_system_resources_grid(grid_frame)
        
        # Performance metrics
        self.create_performance_metrics_grid(grid_frame)
    
    def create_system_resources_grid(self, parent):
        """Create system resources grid"""
        frame = ttk.LabelFrame(parent, text="System Resources", padding=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Configure grid weights
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # CPU Usage
        self.create_metric_display(frame, "CPU Usage", "cpu_percent", "%", row=0, column=0)
        
        # Memory Usage
        self.create_metric_display(frame, "Memory Usage", "memory_percent", "%", row=0, column=1)
        
        # Disk Usage
        self.create_metric_display(frame, "Disk Usage", "disk_percent", "%", row=0, column=2)
        
        # Network
        self.create_metric_display(frame, "Network Sent", "network_sent", "MB/s", row=1, column=0)
        self.create_metric_display(frame, "Network Received", "network_received", "MB/s", row=1, column=1)
    
    def create_performance_metrics_grid(self, parent):
        """Create performance metrics grid"""
        frame = ttk.LabelFrame(parent, text="Performance Metrics", padding=10)
        frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Database Performance
        self.create_metric_display(frame, "Database Query Time", "avg_query_time", "ms", row=0, column=0)
        self.create_metric_display(frame, "Active Connections", "active_connections", "count", row=0, column=1)
        
        # Cache Performance
        self.create_metric_display(frame, "Cache Hit Rate", "cache_hit_rate", "%", row=1, column=0)
        self.create_metric_display(frame, "Response Time", "avg_response_time", "ms", row=1, column=1)
    
    def create_metric_display(self, parent, label, key, unit, row=0, column=0):
        """Create metric display widget"""
        # Label
        label_widget = ttk.Label(parent, text=f"{label}:")
        label_widget.grid(row=row, column=column*2, sticky="w", padx=5, pady=2)
        
        # Value
        value_widget = ttk.Label(parent, text="0.0", font=("Arial", 12, "bold"))
        value_widget.grid(row=row, column=column*2+1, sticky="w", padx=5, pady=2)
        
        # Unit
        unit_widget = ttk.Label(parent, text=unit)
        unit_widget.grid(row=row, column=column*2+2, sticky="w", padx=5, pady=2)
        
        # Store widget reference
        widget_key = f"{key}_value"
        self.widgets[widget_key] = value_widget
    
    def create_metrics_tab(self):
        """Create detailed metrics tab"""
        frame = ttk.Frame(self.widgets['notebook'])
        self.widgets['notebook'].add(frame, text="Metrics")
        
        # Create treeview for metrics
        columns = ('Metric', 'Value', 'Unit', 'Timestamp')
        self.widgets['metrics_tree'] = ttk.Treeview(frame, columns=columns, show='headings')
        
        for col in columns:
            self.widgets['metrics_tree'].heading(col, text=col)
            self.widgets['metrics_tree'].column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.widgets['metrics_tree'].yview)
        self.widgets['metrics_tree'].configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.widgets['metrics_tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_database_tab(self):
        """Create database performance tab"""
        frame = ttk.Frame(self.widgets['notebook'])
        self.widgets['notebook'].add(frame, text="Database")
        
        # Database info
        db_frame = ttk.LabelFrame(frame, text="Database Performance", padding=10)
        db_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection pool info
        self.create_metric_display(db_frame, "Pool Size", "pool_size", "connections", row=0, column=0)
        self.create_metric_display(db_frame, "Active Connections", "active_connections", "connections", row=0, column=1)
        self.create_metric_display(db_frame, "Available Connections", "available_connections", "connections", row=1, column=0)
        self.create_metric_display(db_frame, "Avg Query Time", "avg_query_time", "ms", row=1, column=1)
        self.create_metric_display(db_frame, "Total Queries", "total_queries", "count", row=2, column=0)
        self.create_metric_display(db_frame, "Cache Hits", "cache_hits", "count", row=2, column=1)
    
    def create_memory_tab(self):
        """Create memory monitoring tab"""
        frame = ttk.Frame(self.widgets['notebook'])
        self.widgets['notebook'].add(frame, text="Memory")
        
        # Memory info
        memory_frame = ttk.LabelFrame(frame, text="Memory Usage", padding=10)
        memory_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Memory metrics
        self.create_metric_display(memory_frame, "Memory Usage", "memory_percent", "%", row=0, column=0)
        self.create_metric_display(memory_frame, "Memory Used", "memory_used", "MB", row=0, column=1)
        self.create_metric_display(memory_frame, "Objects Count", "objects_count", "count", row=1, column=0)
        self.create_metric_display(memory_frame, "Garbage Collections", "gc_count", "count", row=1, column=1)
    
    def create_settings_tab(self):
        """Create settings tab"""
        frame = ttk.Frame(self.widgets['notebook'])
        self.widgets['notebook'].add(frame, text="Settings")
        
        # Settings frame
        settings_frame = ttk.LabelFrame(frame, text="Performance Settings", padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Monitoring interval
        ttk.Label(settings_frame, text="Monitoring Interval (seconds):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        interval_var = tk.StringVar(value=str(self.monitor.config.monitoring_interval))
        interval_entry = ttk.Entry(settings_frame, textvariable=interval_var, width=10)
        interval_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Cache size
        ttk.Label(settings_frame, text="Cache Size:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        cache_var = tk.StringVar(value=str(self.monitor.config.cache_size))
        cache_entry = ttk.Entry(settings_frame, textvariable=cache_var, width=10)
        cache_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Apply Settings", command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Export Metrics", command=self.export_metrics).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Metrics", command=self.reset_metrics).pack(side=tk.LEFT, padx=5)
    
    def create_status_bar(self):
        """Create status bar"""
        self.frames['status'] = ttk.Frame(self.parent)
        self.frames['status'].pack(fill=tk.X, side=tk.BOTTOM)
        
        # Status label
        self.widgets['status_label'] = ttk.Label(self.frames['status'], text="Performance monitoring active")
        self.widgets['status_label'].pack(side=tk.LEFT, padx=5)
        
        # Last update label
        self.widgets['update_label'] = ttk.Label(self.frames['status'], text="Last update: Never")
        self.widgets['update_label'].pack(side=tk.RIGHT, padx=5)
    
    def update_ui(self):
        """Update UI with latest data"""
        try:
            # Check for UI updates
            try:
                while True:
                    self.ui_update_queue.get_nowait()
                    self.dashboard_data = self.monitor.get_dashboard_data()
                    self.last_update = time.time()
            except queue.Empty:
                pass
            
            # Update overview metrics
            self.update_overview_metrics()
            
            # Update metrics tree
            self.update_metrics_tree()
            
            # Update status bar
            self.update_status_bar()
            
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
        
        # Schedule next update
        self.parent.after(1000, self.update_ui)
    
    def update_overview_metrics(self):
        """Update overview metrics"""
        if not self.dashboard_data:
            return
        
        # Update system metrics
        system_data = self.dashboard_data.get('system', {})
        if system_data:
            self.update_metric_widget('cpu_percent_value', system_data.get('cpu', {}).get('latest', 0))
            self.update_metric_widget('memory_percent_value', system_data.get('memory', {}).get('latest', 0))
            self.update_metric_widget('disk_percent_value', system_data.get('disk', {}).get('latest', 0))
        
        # Update performance metrics
        database_data = self.dashboard_data.get('database', {})
        if database_data:
            self.update_metric_widget('avg_query_time_value', database_data.get('avg_query_time', 0))
            self.update_metric_widget('active_connections_value', database_data.get('active_connections', 0))
        
        cache_data = self.dashboard_data.get('cache', {})
        if cache_data:
            self.update_metric_widget('cache_hit_rate_value', cache_data.get('hit_rate', 0))
        
        response_data = self.dashboard_data.get('response_time', {})
        if response_data:
            self.update_metric_widget('avg_response_time_value', response_data.get('avg', 0))
    
    def update_metric_widget(self, widget_key, value):
        """Update metric widget value"""
        if widget_key in self.widgets:
            widget = self.widgets[widget_key]
            widget.config(text=f"{value:.2f}")
    
    def update_metrics_tree(self):
        """Update metrics tree"""
        if not self.dashboard_data:
            return
        
        # Clear existing items
        for item in self.widgets['metrics_tree'].get_children():
            self.widgets['metrics_tree'].delete(item)
        
        # Add metrics
        for metric_type, summary in self.dashboard_data.get('metrics', {}).items():
            if summary:
                self.widgets['metrics_tree'].insert('', 'end', values=(
                    metric_type,
                    f"{summary.get('latest', 0):.2f}",
                    summary.get('unit', ''),
                    datetime.fromtimestamp(summary.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')
                ))
    
    def update_status_bar(self):
        """Update status bar"""
        if self.last_update > 0:
            update_time = datetime.fromtimestamp(self.last_update).strftime('%Y-%m-%d %H:%M:%S')
            self.widgets['update_label'].config(text=f"Last update: {update_time}")
    
    def apply_settings(self):
        """Apply settings"""
        try:
            # Get new values
            new_interval = float(self.widgets['interval_entry'].get())
            new_cache_size = int(self.widgets['cache_entry'].get())
            
            # Update monitor configuration
            self.monitor.config.monitoring_interval = new_interval
            self.monitor.config.cache_size = new_cache_size
            
            # Show success message
            messagebox.showinfo("Settings", "Settings applied successfully")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {e}")
    
    def export_metrics(self):
        """Export metrics"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                self.monitor.export_metrics(filename)
                messagebox.showinfo("Export", f"Metrics exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export metrics: {e}")
    
    def reset_metrics(self):
        """Reset all metrics"""
        try:
            if messagebox.askyesno("Reset Metrics", "Are you sure you want to reset all metrics?"):
                # Clear all metrics
                for metric_queue in self.monitor.metrics.values():
                    metric_queue.clear()
                
                # Clear system resources
                self.monitor.system_resources.clear()
                
                # Reset counters
                self.monitor.cache_hits = 0
                self.monitor.cache_misses = 0
                self.monitor.error_count = 0
                self.monitor.total_requests = 0
                self.monitor.response_times.clear()
                
                messagebox.showinfo("Reset", "Metrics reset successfully")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset metrics: {e}")

# Global desktop performance monitor instance
_desktop_performance_monitor = None

def get_desktop_performance_monitor() -> DesktopPerformanceMonitor:
    """Get global desktop performance monitor instance"""
    global _desktop_performance_monitor
    if _desktop_performance_monitor is None:
        config = PerformanceConfig()
        _desktop_performance_monitor = DesktopPerformanceMonitor(config)
    return _desktop_performance_monitor