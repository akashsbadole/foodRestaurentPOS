"""
Performance Utilities for Desktop POS Application
Handles database optimization, caching, and memory management
"""

import threading
import time
import psutil
import gc
import weakref
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import json
import os
from collections import OrderedDict
import sqlite3
from contextlib import contextmanager

class PerformanceConfig:
    """Performance configuration manager for desktop application"""
    
    def __init__(self, config_path: str = "src/config/performance_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.current_profile = self.config.get('current_profile', 'balanced')
        self.auto_optimization = self.config.get('auto_optimization', {})
        
    def _load_config(self) -> Dict[str, Any]:
        """Load performance configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_config()
        except json.JSONDecodeError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default performance configuration"""
        return {
            "performance_settings": {
                "database_optimization": {
                    "connection_pooling": {
                        "enabled": True,
                        "pool_size": 10,
                        "max_overflow": 20,
                        "pool_timeout": 30
                    },
                    "query_optimization": {
                        "use_indexes": True,
                        "selective_loading": True,
                        "batch_operations": True
                    },
                    "caching": {
                        "enabled": True,
                        "type": "memory",
                        "default_ttl": 300,
                        "max_size": 1000
                    }
                },
                "ui_optimization": {
                    "lazy_loading": {
                        "images": True,
                        "menu_items": True,
                        "data_lists": True
                    },
                    "rendering": {
                        "virtual_scrolling": True,
                        "widget_reuse": True,
                        "progressive_loading": True
                    },
                    "memory_management": {
                        "enabled": True,
                        "garbage_collection": True,
                        "object_pooling": True,
                        "streaming_data": True
                    }
                }
            },
            "current_profile": "balanced",
            "auto_optimization": {
                "enabled": True,
                "detect_resources": True,
                "adjust_settings": True,
                "profile_switching": True
            }
        }
    
    def get_setting(self, path: str, default: Any = None) -> Any:
        """Get configuration setting by path"""
        keys = path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def get_profile_settings(self, profile: str = None) -> Dict[str, Any]:
        """Get settings for specific performance profile"""
        if profile is None:
            profile = self.current_profile
        
        profiles = self.config.get('performance_settings', {}).get('profiles', {})
        return profiles.get(profile, {})
    
    def update_setting(self, path: str, value: Any):
        """Update configuration setting"""
        keys = path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
    
    def switch_profile(self, profile: str):
        """Switch performance profile"""
        if profile in self.config.get('performance_settings', {}).get('profiles', {}):
            self.current_profile = profile
            self.update_setting('current_profile', profile)
            self._save_config()
            return True
        return False
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving performance config: {e}")

class DatabaseOptimizer:
    """Database optimization utilities for desktop application"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.connection_pool = {}
        self.query_cache = OrderedDict()
        self.cache_lock = threading.RLock()
        self.logger = self._get_logger()
        
    def _get_logger(self):
        """Get logger instance"""
        import logging
        return logging.getLogger(__name__)
    
    def get_connection(self, db_path: str) -> sqlite3.Connection:
        """Get optimized database connection from pool"""
        pool_key = f"{db_path}_{threading.current_thread().ident}"
        
        if pool_key not in self.connection_pool:
            try:
                conn = sqlite3.connect(db_path)
                # Apply optimizations
                self._optimize_connection(conn)
                self.connection_pool[pool_key] = conn
            except Exception as e:
                self.logger.error(f"Failed to create connection: {e}")
                raise
        
        return self.connection_pool[pool_key]
    
    def _optimize_connection(self, conn: sqlite3.Connection):
        """Optimize SQLite connection settings"""
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
        conn.commit()
        cursor.close()
    
    @contextmanager
    def get_optimized_cursor(self, db_path: str):
        """Context manager for optimized database cursor"""
        conn = self.get_connection(db_path)
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_cached_query(self, db_path: str, query: str, params: tuple = None, 
                           ttl: int = None) -> List[tuple]:
        """Execute query with caching"""
        cache_key = f"{query}_{str(params)}"
        current_time = time.time()
        
        # Check cache first
        with self.cache_lock:
            if cache_key in self.query_cache:
                cached_result, cached_time = self.query_cache[cache_key]
                if ttl is None:
                    ttl = self.config.get_setting('performance_settings.database_optimization.caching.default_ttl', 300)
                
                if current_time - cached_time < ttl:
                    # Move to end to show recent use
                    self.query_cache.move_to_end(cache_key)
                    return cached_result
        
        # Execute query
        try:
            with self.get_optimized_cursor(db_path) as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchall()
                
                # Cache result
                with self.cache_lock:
                    # Limit cache size
                    if len(self.query_cache) >= self.config.get_setting('performance_settings.database_optimization.caching.max_size', 1000):
                        self.query_cache.popitem(last=False)
                    
                    self.query_cache[cache_key] = (result, current_time)
                    self.query_cache.move_to_end(cache_key)
                
                return result
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
    
    def clear_cache(self):
        """Clear query cache"""
        with self.cache_lock:
            self.query_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            return {
                'cache_size': len(self.query_cache),
                'cache_keys': list(self.query_cache.keys()),
                'memory_usage': len(str(self.query_cache)) / 1024  # KB
            }

class MemoryManager:
    """Memory management utilities"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.memory_thresholds = {
            'warning': config.get_setting('monitoring.alerts.memory_threshold_warning', 80),
            'critical': config.get_setting('monitoring.alerts.memory_threshold_critical', 90)
        }
        self.object_pool = weakref.WeakValueDictionary()
        self.gc_callbacks = []
        self.logger = self._get_logger()
        
    def _get_logger(self):
        """Get logger instance"""
        import logging
        return logging.getLogger(__name__)
    
    def monitor_memory_usage(self) -> Dict[str, Any]:
        """Monitor system memory usage"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'memory_percent': memory.percent,
            'memory_available': memory.available,
            'memory_total': memory.total,
            'disk_percent': disk.percent,
            'disk_free': disk.free,
            'disk_total': disk.total
        }
    
    def check_memory_status(self) -> str:
        """Check memory status based on thresholds"""
        memory_info = self.monitor_memory_usage()
        percent = memory_info['memory_percent']
        
        if percent >= self.memory_thresholds['critical']:
            return 'critical'
        elif percent >= self.memory_thresholds['warning']:
            return 'warning'
        else:
            return 'normal'
    
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        # Trigger garbage collection
        if self.config.get_setting('ui_optimization.memory_management.garbage_collection', True):
            gc.collect()
        
        # Clear unused objects from pool
        self.object_pool.clear()
        
        # Clear database cache if memory is low
        if self.check_memory_status() == 'critical':
            self._trigger_cache_cleanup()
    
    def add_to_object_pool(self, key: str, obj: Any):
        """Add object to object pool for reuse"""
        self.object_pool[key] = obj
    
    def get_from_object_pool(self, key: str) -> Optional[Any]:
        """Get object from pool if available"""
        return self.object_pool.get(key)
    
    def register_gc_callback(self, callback: Callable):
        """Register garbage collection callback"""
        self.gc_callbacks.append(callback)
    
    def _trigger_cache_cleanup(self):
        """Trigger cache cleanup in other modules"""
        for callback in self.gc_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Cache cleanup callback failed: {e}")

class UIOptimizer:
    """UI optimization utilities"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.widget_cache = {}
        self.lazy_loading_enabled = config.get_setting('ui_optimization.lazy_loading', {})
        self.rendering_enabled = config.get_setting('ui_optimization.rendering', {})
        self.debounce_timers = {}
        self.logger = self._get_logger()
        
    def _get_logger(self):
        """Get logger instance"""
        import logging
        return logging.getLogger(__name__)
    
    def debounce(self, func: Callable, delay: int = 300):
        """Debounce function calls"""
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            
            if key in self.debounce_timers:
                self.debounce_timers[key].cancel()
            
            timer = threading.Timer(delay, lambda: func(*args, **kwargs))
            self.debounce_timers[key] = timer
            timer.start()
        
        return wrapper
    
    def create_virtual_scrollable_frame(self, parent, item_height: int = 50):
        """Create virtual scrollable frame for large lists"""
        from tkinter import ttk, Canvas, Frame
        
        # Create main container
        container = Frame(parent)
        
        # Create canvas and scrollbar
        canvas = Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Configure scrollable frame
        scrollable_frame = Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack components
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        container.canvas = canvas
        container.scrollable_frame = scrollable_frame
        container.item_height = item_height
        
        return container
    
    def add_virtual_items(self, scrollable_frame, items: List[Dict], render_func: Callable):
        """Add items to virtual scrollable frame"""
        canvas = scrollable_frame.canvas
        item_height = scrollable_frame.item_height
        
        # Clear existing items
        for widget in scrollable_frame.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create visible items only
        canvas_height = canvas.winfo_height()
        visible_items = int(canvas_height / item_height) + 2
        
        for i in range(min(len(items), visible_items)):
            item_frame = Frame(scrollable_frame.scrollable_frame, height=item_height, relief="solid", borderwidth=1)
            item_frame.pack(fill="x", pady=2)
            item_frame.pack_propagate(False)
            
            render_func(item_frame, items[i], i)
        
        # Update scroll region
        scrollable_frame.scrollable_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def cache_widget(self, key: str, widget: Any):
        """Cache widget for reuse"""
        self.widget_cache[key] = widget
    
    def get_cached_widget(self, key: str) -> Optional[Any]:
        """Get cached widget"""
        return self.widget_cache.get(key)
    
    def clear_widget_cache(self):
        """Clear widget cache"""
        self.widget_cache.clear()

class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.metrics_history = []
        self.monitoring_enabled = config.get_setting('monitoring.performance_metrics.enabled', True)
        self.collection_interval = config.get_setting('monitoring.performance_metrics.collection_interval', 60)
        self.logger = self._get_logger()
        
    def _get_logger(self):
        """Get logger instance"""
        import logging
        return logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.monitoring_enabled:
            return
        
        def monitor_loop():
            while self.monitoring_enabled:
                try:
                    metrics = self.collect_metrics()
                    self.metrics_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'metrics': metrics
                    })
                    
                    # Keep only last 1000 entries
                    if len(self.metrics_history) > 1000:
                        self.metrics_history.pop(0)
                    
                    time.sleep(self.collection_interval)
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(30)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        metrics = {
            'memory': psutil.virtual_memory()._asdict(),
            'cpu': psutil.cpu_percent(interval=1),
            'disk': psutil.disk_usage('/')._asdict(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add application-specific metrics
        if hasattr(self, 'db_optimizer'):
            metrics['database'] = self.db_optimizer.get_cache_stats()
        
        return metrics
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report"""
        if not self.metrics_history:
            return {'error': 'No metrics available'}
        
        latest_metrics = self.metrics_history[-1]['metrics']
        
        # Calculate trends
        if len(self.metrics_history) > 10:
            memory_trend = self._calculate_trend([m['metrics']['memory']['percent'] for m in self.metrics_history[-10:]])
            cpu_trend = self._calculate_trend([m['metrics']['cpu'] for m in self.metrics_history[-10:]])
        else:
            memory_trend = cpu_trend = 'stable'
        
        return {
            'current_metrics': latest_metrics,
            'memory_trend': memory_trend,
            'cpu_trend': cpu_trend,
            'recommendations': self._get_recommendations(latest_metrics),
            'monitoring_status': 'active' if self.monitoring_enabled else 'inactive'
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return 'stable'
        
        first, last = values[0], values[-1]
        change = ((last - first) / first) * 100
        
        if change > 5:
            return 'increasing'
        elif change < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _get_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get performance recommendations"""
        recommendations = []
        
        # Memory recommendations
        if metrics['memory']['percent'] > 80:
            recommendations.append("High memory usage detected. Consider closing unused applications.")
        
        # CPU recommendations
        if metrics['cpu'] > 80:
            recommendations.append("High CPU usage detected. Consider optimizing application performance.")
        
        # Disk recommendations
        if metrics['disk']['percent'] > 90:
            recommendations.append("Low disk space detected. Consider cleaning up disk space.")
        
        return recommendations

class PerformanceManager:
    """Main performance manager for desktop application"""
    
    def __init__(self, config_path: str = "src/config/performance_config.json"):
        self.config = PerformanceConfig(config_path)
        self.db_optimizer = DatabaseOptimizer(self.config)
        self.memory_manager = MemoryManager(self.config)
        self.ui_optimizer = UIOptimizer(self.config)
        self.monitor = PerformanceMonitor(self.config)
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Auto-optimization
        if self.config.auto_optimization.get('enabled', True):
            self.start_auto_optimization()
    
    def start_auto_optimization(self):
        """Start automatic optimization based on system resources"""
        def auto_optimize_loop():
            while True:
                try:
                    memory_status = self.memory_manager.check_memory_status()
                    
                    if memory_status == 'critical':
                        self.memory_manager.optimize_memory_usage()
                        self.config.switch_profile('low_resource')
                    elif memory_status == 'warning':
                        if self.config.current_profile != 'medium_resource':
                            self.config.switch_profile('medium_resource')
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    print(f"Auto-optimization error: {e}")
                    time.sleep(30)
        
        optimize_thread = threading.Thread(target=auto_optimize_loop, daemon=True)
        optimize_thread.start()
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        return {
            'configuration': {
                'current_profile': self.config.current_profile,
                'auto_optimization': self.config.auto_optimization
            },
            'database': self.db_optimizer.get_cache_stats(),
            'memory': self.memory_manager.monitor_memory_usage(),
            'monitoring': self.monitor.get_performance_report(),
            'recommendations': self.monitor.get_performance_report().get('recommendations', [])
        }
    
    def optimize_ui_performance(self, parent):
        """Optimize UI performance"""
        return self.ui_optimizer.create_virtual_scrollable_frame(parent)
    
    def optimize_database_query(self, db_path: str, query: str, params: tuple = None):
        """Optimize database query execution"""
        return self.db_optimizer.execute_cached_query(db_path, query, params)
    
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        self.memory_manager.optimize_memory_usage()

# Global performance manager instance
_performance_manager = None

def get_performance_manager(config_path: str = None) -> PerformanceManager:
    """Get global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager(config_path)
    return _performance_manager