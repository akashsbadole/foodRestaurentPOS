"""
Memory Monitoring and Optimization Utilities for Desktop POS Application
Provides real-time memory monitoring, garbage collection, and memory optimization
"""

import threading
import time
import psutil
import gc
import weakref
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from collections import deque, OrderedDict
import tracemalloc
import os

from src.utils.performance_utils import PerformanceConfig

class MemoryMonitor:
    """Real-time memory monitoring and optimization"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Memory thresholds
        self.warning_threshold = self.config.get_setting('monitoring.alerts.memory_threshold_warning', 80)
        self.critical_threshold = self.config.get_setting('monitoring.alerts.memory_threshold_critical', 90)
        
        # Monitoring settings
        self.monitoring_enabled = self.config.get_setting('monitoring.performance_metrics.enabled', True)
        self.collection_interval = self.config.get_setting('monitoring.performance_metrics.collection_interval', 60)
        
        # Memory tracking
        self.memory_history = deque(maxlen=1000)  # Store last 1000 readings
        self.peak_memory_usage = 0
        self.total_allocations = 0
        self.total_frees = 0
        
        # Callbacks
        self.warning_callbacks = []
        self.critical_callbacks = []
        self.memory_optimization_callbacks = []
        
        # Monitoring thread
        self.monitoring_thread = None
        self.running = False
        
        # Memory optimization
        self.gc_enabled = self.config.get_setting('ui_optimization.memory_management.garbage_collection', True)
        self.object_pool = weakref.WeakValueDictionary()
        
        # Initialize monitoring
        if self.monitoring_enabled:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if self.running:
            return
        
        self.running = True
        tracemalloc.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        tracemalloc.stop()
        self.logger.info("Memory monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Collect memory metrics
                metrics = self._collect_memory_metrics()
                
                # Store in history
                self.memory_history.append({
                    'timestamp': datetime.now(),
                    'metrics': metrics
                })
                
                # Update peak memory
                if metrics['memory_percent'] > self.peak_memory_usage:
                    self.peak_memory_usage = metrics['memory_percent']
                
                # Check thresholds
                self._check_memory_thresholds(metrics)
                
                # Sleep for collection interval
                time.sleep(self.collection_interval)
                
            except Exception as e:
                self.logger.error(f"Memory monitoring error: {e}")
                time.sleep(30)  # Wait less on error
    
    def _collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics"""
        # System memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Process memory metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # Application-specific metrics
        app_metrics = self._get_application_metrics()
        
        return {
            'timestamp': datetime.now(),
            'system_memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'used': memory.used,
                'free': memory.free
            },
            'swap_memory': {
                'total': swap.total,
                'used': swap.used,
                'percent': swap.percent,
                'free': swap.free
            },
            'process_memory': {
                'rss': process_memory.rss,
                'vms': process_memory.vms,
                'percent': memory.percent  # Process memory as % of system memory
            },
            'application_metrics': app_metrics,
            'gc_stats': self._get_gc_stats(),
            'thread_count': threading.active_count(),
            'open_files': len(process.open_files()),
            'open_connections': len(process.connections())
        }
    
    def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-specific memory metrics"""
        metrics = {
            'object_pool_size': len(self.object_pool),
            'total_allocations': self.total_allocations,
            'total_frees': self.total_frees,
            'net_allocations': self.total_allocations - self.total_frees
        }
        
        # Add custom metrics
        metrics.update(self._get_custom_metrics())
        
        return metrics
    
    def _get_custom_metrics(self) -> Dict[str, Any]:
        """Get custom application metrics"""
        # Override this method in subclasses to add custom metrics
        return {}
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Get garbage collection statistics"""
        stats = {}
        
        # Get GC counters
        for i in range(gc.get_count()):
            stats[f'gc_{i}_count'] = gc.get_count()[i]
        
        # Get GC generations
        for i in range(3):
            generation = gc.get_stats()[i]
            stats[f'generation_{i}_collected'] = generation['collected']
            stats[f'generation_{i}_uncollectable'] = generation['uncollectable']
            stats[f'generation_{i}_collections'] = generation['collections']
        
        return stats
    
    def _check_memory_thresholds(self, metrics: Dict[str, Any]):
        """Check memory thresholds and trigger callbacks"""
        memory_percent = metrics['system_memory']['percent']
        
        if memory_percent >= self.critical_threshold:
            self._trigger_critical_callbacks(metrics)
        elif memory_percent >= self.warning_threshold:
            self._trigger_warning_callbacks(metrics)
    
    def _trigger_warning_callbacks(self, metrics: Dict[str, Any]):
        """Trigger warning callbacks"""
        self.logger.warning(f"Memory usage warning: {metrics['system_memory']['percent']:.1f}%")
        
        for callback in self.warning_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                self.logger.error(f"Warning callback error: {e}")
    
    def _trigger_critical_callbacks(self, metrics: Dict[str, Any]):
        """Trigger critical callbacks"""
        self.logger.critical(f"Memory usage critical: {metrics['system_memory']['percent']:.1f}%")
        
        for callback in self.critical_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                self.logger.error(f"Critical callback error: {e}")
    
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        self.logger.info("Starting memory optimization")
        
        # Trigger optimization callbacks
        for callback in self.memory_optimization_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Memory optimization callback error: {e}")
        
        # Perform garbage collection
        if self.gc_enabled:
            self._perform_garbage_collection()
        
        # Clean up object pool
        self._cleanup_object_pool()
        
        # Perform additional optimizations
        self._perform_additional_optimizations()
        
        self.logger.info("Memory optimization completed")
    
    def _perform_garbage_collection(self):
        """Perform garbage collection"""
        try:
            # Collect garbage
            collected = gc.collect()
            self.logger.info(f"Garbage collection: {collected} objects collected")
            
            # Collect specific generations
            for i in range(3):
                collected_gen = gc.collect(i)
                if collected_gen > 0:
                    self.logger.info(f"Generation {i} collection: {collected_gen} objects collected")
            
        except Exception as e:
            self.logger.error(f"Garbage collection error: {e}")
    
    def _cleanup_object_pool(self):
        """Clean up object pool"""
        # Weak references are automatically cleaned up
        # Just log the current size
        pool_size = len(self.object_pool)
        if pool_size > 0:
            self.logger.info(f"Object pool size: {pool_size}")
    
    def _perform_additional_optimizations(self):
        """Perform additional memory optimizations"""
        # Clear memory history if it's getting large
        if len(self.memory_history) > 500:
            # Keep only recent history
            self.memory_history = deque(list(self.memory_history)[-500:], maxlen=1000)
        
        # Clear any cached data
        self._clear_cached_data()
    
    def _clear_cached_data(self):
        """Clear cached data"""
        # Override this method in subclasses to implement custom cache clearing
        pass
    
    def get_memory_report(self) -> Dict[str, Any]:
        """Get comprehensive memory report"""
        if not self.memory_history:
            return {'error': 'No memory data available'}
        
        latest_metrics = self.memory_history[-1]['metrics']
        
        # Calculate trends
        if len(self.memory_history) > 10:
            memory_trend = self._calculate_trend([
                m['metrics']['system_memory']['percent'] 
                for m in list(self.memory_history)[-10:]
            ])
        else:
            memory_trend = 'stable'
        
        return {
            'current_metrics': latest_metrics,
            'peak_memory_usage': self.peak_memory_usage,
            'memory_trend': memory_trend,
            'history_summary': self._get_history_summary(),
            'recommendations': self._get_memory_recommendations(latest_metrics),
            'monitoring_status': 'active' if self.running else 'inactive'
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
    
    def _get_history_summary(self) -> Dict[str, Any]:
        """Get memory history summary"""
        if not self.memory_history:
            return {}
        
        memory_values = [m['metrics']['system_memory']['percent'] for m in self.memory_history]
        
        return {
            'min_memory': min(memory_values),
            'max_memory': max(memory_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'readings_count': len(self.memory_history)
        }
    
    def _get_memory_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """Get memory optimization recommendations"""
        recommendations = []
        
        # Memory usage recommendations
        memory_percent = metrics['system_memory']['percent']
        if memory_percent > 90:
            recommendations.append("Critical memory usage detected. Close unnecessary applications.")
        elif memory_percent > 80:
            recommendations.append("High memory usage detected. Consider optimizing application memory usage.")
        
        # Process recommendations
        process_memory = metrics['process_memory']['rss'] / (1024 * 1024)  # MB
        if process_memory > 500:
            recommendations.append(f"High process memory usage: {process_memory:.1f}MB. Consider restarting application.")
        
        # GC recommendations
        gc_stats = metrics['gc_stats']
        total_collections = sum(gc_stats.get(f'generation_{i}_collections', 0) for i in range(3))
        if total_collections > 100:
            recommendations.append("Frequent garbage collection detected. Check for memory leaks.")
        
        # Thread recommendations
        thread_count = metrics['thread_count']
        if thread_count > 50:
            recommendations.append(f"High thread count: {thread_count}. Check for excessive thread creation.")
        
        return recommendations
    
    def add_warning_callback(self, callback: Callable):
        """Add warning callback"""
        self.warning_callbacks.append(callback)
    
    def add_critical_callback(self, callback: Callable):
        """Add critical callback"""
        self.critical_callbacks.append(callback)
    
    def add_memory_optimization_callback(self, callback: Callable):
        """Add memory optimization callback"""
        self.memory_optimization_callbacks.append(callback)
    
    def get_snapshot(self) -> Dict[str, Any]:
        """Get current memory snapshot"""
        if not tracemalloc.is_tracing():
            return {'error': 'Tracing not enabled'}
        
        # Get current snapshot
        snapshot = tracemalloc.take_snapshot()
        
        # Analyze snapshot
        top_stats = snapshot.statistics('lineno')
        
        return {
            'top_allocations': [
                {
                    'file': stat.traceback.format()[0] if stat.traceback else 'unknown',
                    'line': stat.traceback.format()[1].strip() if stat.traceback and len(stat.traceback.format()) > 1 else 'unknown',
                    'size': stat.size,
                    'count': stat.count
                }
                for stat in top_stats[:10]
            ],
            'total_allocated': sum(stat.size for stat in top_stats),
            'total_objects': sum(stat.count for stat in top_stats)
        }

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Memory optimization settings
        self.auto_optimization = self.config.get_setting('auto_optimization.enabled', True)
        self.optimization_interval = self.config.get_setting('auto_optimization.optimization_interval', 300)  # 5 minutes
        
        # Optimization strategies
        self.optimization_strategies = []
        
        # Initialize strategies
        self._initialize_strategies()
        
        # Start auto-optimization
        if self.auto_optimization:
            self.start_auto_optimization()
    
    def _initialize_strategies(self):
        """Initialize optimization strategies"""
        from .memory_strategies import (
            GarbageCollectionStrategy,
            CacheCleanupStrategy,
            ObjectPoolCleanupStrategy,
            MemoryLeakDetectionStrategy
        )
        
        self.optimization_strategies = [
            GarbageCollectionStrategy(),
            CacheCleanupStrategy(),
            ObjectPoolCleanupStrategy(),
            MemoryLeakDetectionStrategy()
        ]
    
    def start_auto_optimization(self):
        """Start automatic memory optimization"""
        def optimization_loop():
            while self.auto_optimization:
                try:
                    time.sleep(self.optimization_interval)
                    self.optimize_memory()
                except Exception as e:
                    self.logger.error(f"Auto-optimization error: {e}")
                    time.sleep(60)  # Wait less on error
        
        optimization_thread = threading.Thread(target=optimization_loop, daemon=True)
        optimization_thread.start()
    
    def optimize_memory(self):
        """Optimize memory usage"""
        self.logger.info("Starting memory optimization")
        
        for strategy in self.optimization_strategies:
            try:
                strategy.optimize()
            except Exception as e:
                self.logger.error(f"Strategy {strategy.__class__.__name__} error: {e}")
        
        self.logger.info("Memory optimization completed")
    
    def add_optimization_strategy(self, strategy):
        """Add custom optimization strategy"""
        self.optimization_strategies.append(strategy)
    
    def stop_auto_optimization(self):
        """Stop automatic memory optimization"""
        self.auto_optimization = False

# Global memory monitor instance
_memory_monitor = None

def get_memory_monitor(config: PerformanceConfig = None) -> MemoryMonitor:
    """Get global memory monitor instance"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor(config)
    return _memory_monitor

def get_memory_optimizer(config: PerformanceConfig = None) -> MemoryOptimizer:
    """Get global memory optimizer instance"""
    return MemoryOptimizer(config)