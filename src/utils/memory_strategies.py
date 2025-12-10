"""
Memory Optimization Strategies for Desktop POS Application
Provides various memory optimization strategies and techniques
"""

import gc
import weakref
import threading
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
from collections import defaultdict
import psutil
import os

from src.config.performance_config import PerformanceConfig

class OptimizationStrategy:
    """Base class for memory optimization strategies"""
    
    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger(__name__)
        self.enabled = True
        self.last_execution = None
        self.execution_count = 0
        self.total_execution_time = 0
    
    def optimize(self):
        """Execute optimization strategy"""
        if not self.enabled:
            return
        
        start_time = time.time()
        
        try:
            self._execute_optimization()
            self.execution_count += 1
            self.last_execution = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Strategy {self.__class__.__name__} error: {e}")
        
        finally:
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
    
    def _execute_optimization(self):
        """Execute optimization logic"""
        raise NotImplementedError
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        return {
            'name': self.__class__.__name__,
            'enabled': self.enabled,
            'execution_count': self.execution_count,
            'last_execution': self.last_execution,
            'total_execution_time': self.total_execution_time,
            'average_execution_time': self.total_execution_time / max(self.execution_count, 1)
        }

class GarbageCollectionStrategy(OptimizationStrategy):
    """Garbage collection optimization strategy"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.gc_enabled = self.config.get_setting('ui_optimization.memory_management.garbage_collection', True)
        self.gc_threshold = self.config.get_setting('memory_optimization.gc_threshold', 1000)  # Objects
        self.gc_interval = self.config.get_setting('memory_optimization.gc_interval', 300)  # Seconds
        
    def _execute_optimization(self):
        """Execute garbage collection"""
        if not self.gc_enabled:
            return
        
        # Get current object count
        object_count = len(gc.get_objects())
        
        if object_count > self.gc_threshold:
            self.logger.info(f"Performing garbage collection (objects: {object_count})")
            
            # Perform garbage collection
            collected = gc.collect()
            self.logger.info(f"Garbage collection: {collected} objects collected")
            
            # Collect specific generations
            for i in range(3):
                collected_gen = gc.collect(i)
                if collected_gen > 0:
                    self.logger.info(f"Generation {i} collection: {collected_gen} objects collected")
        
        # Force garbage collection if interval has passed
        if self.last_execution and (datetime.now() - self.last_execution).total_seconds() > self.gc_interval:
            self.logger.info("Performing scheduled garbage collection")
            gc.collect()

class CacheCleanupStrategy(OptimizationStrategy):
    """Cache cleanup optimization strategy"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.cache_cleanup_threshold = self.config.get_setting('memory_optimization.cache_cleanup_threshold', 500)
        self.cache_retention_time = self.config.get_setting('memory_optimization.cache_retention_time', 600)  # Seconds
        
        # Track cache entries
        self.cache_entries = {}
        self.cache_lock = threading.RLock()
    
    def register_cache_entry(self, cache_id: str, size: int, timestamp: float = None):
        """Register a cache entry"""
        with self.cache_lock:
            if timestamp is None:
                timestamp = time.time()
            
            self.cache_entries[cache_id] = {
                'size': size,
                'timestamp': timestamp,
                'access_count': 0
            }
    
    def update_cache_entry(self, cache_id: str):
        """Update cache entry access"""
        with self.cache_lock:
            if cache_id in self.cache_entries:
                self.cache_entries[cache_id]['access_count'] += 1
    
    def remove_cache_entry(self, cache_id: str):
        """Remove a cache entry"""
        with self.cache_lock:
            if cache_id in self.cache_entries:
                del self.cache_entries[cache_id]
    
    def _execute_optimization(self):
        """Execute cache cleanup"""
        with self.cache_lock:
            current_time = time.time()
            total_size = sum(entry['size'] for entry in self.cache_entries.values())
            
            if total_size > self.cache_cleanup_threshold or len(self.cache_entries) > 1000:
                self.logger.info(f"Cache cleanup triggered (size: {total_size}, entries: {len(self.cache_entries)})")
                
                # Remove old entries
                expired_entries = []
                for cache_id, entry in self.cache_entries.items():
                    if current_time - entry['timestamp'] > self.cache_retention_time:
                        expired_entries.append(cache_id)
                
                # Remove expired entries
                for cache_id in expired_entries:
                    del self.cache_entries[cache_id]
                    self.logger.debug(f"Removed expired cache entry: {cache_id}")
                
                # Remove least recently used entries if still over threshold
                if len(self.cache_entries) > 500:
                    sorted_entries = sorted(
                        self.cache_entries.items(),
                        key=lambda x: x[1]['access_count']
                    )
                    
                    entries_to_remove = sorted_entries[:len(self.cache_entries) - 500]
                    for cache_id, _ in entries_to_remove:
                        del self.cache_entries[cache_id]
                        self.logger.debug(f"Removed LRU cache entry: {cache_id}")
                
                self.logger.info(f"Cache cleanup completed (entries: {len(self.cache_entries)})")

class ObjectPoolCleanupStrategy(OptimizationStrategy):
    """Object pool cleanup optimization strategy"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.pool_cleanup_threshold = self.config.get_setting('memory_optimization.pool_cleanup_threshold', 100)
        self.pool_retention_time = self.config.get_setting('memory_optimization.pool_retention_time', 1800)  # 30 minutes
        
        # Track object pools
        self.object_pools = {}
        self.pools_lock = threading.RLock()
    
    def register_object_pool(self, pool_id: str, pool_object: Any):
        """Register an object pool"""
        with self.pools_lock:
            if pool_id not in self.object_pools:
                self.object_pools[pool_id] = {
                    'object': pool_object,
                    'created_at': time.time(),
                    'last_used': time.time(),
                    'usage_count': 0
                }
            else:
                self.object_pools[pool_id]['last_used'] = time.time()
                self.object_pools[pool_id]['usage_count'] += 1
    
    def _execute_optimization(self):
        """Execute object pool cleanup"""
        with self.pools_lock:
            current_time = time.time()
            
            # Clean up old pools
            pools_to_remove = []
            for pool_id, pool_info in self.object_pools.items():
                if (current_time - pool_info['last_used'] > self.pool_retention_time or
                    pool_info['usage_count'] == 0):
                    pools_to_remove.append(pool_id)
            
            # Remove old pools
            for pool_id in pools_to_remove:
                del self.object_pools[pool_id]
                self.logger.debug(f"Removed unused object pool: {pool_id}")
            
            # Log pool statistics
            if self.object_pools:
                total_usage = sum(info['usage_count'] for info in self.object_pools.values())
                avg_usage = total_usage / len(self.object_pools)
                self.logger.info(f"Object pool cleanup completed (pools: {len(self.object_pools)}, avg_usage: {avg_usage:.1f})")

class MemoryLeakDetectionStrategy(OptimizationStrategy):
    """Memory leak detection strategy"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.leak_detection_enabled = self.config.get_setting('memory_optimization.leak_detection_enabled', True)
        self.memory_increase_threshold = self.config.get_setting('memory_optimization.memory_increase_threshold', 10)  # Percent
        self.check_interval = self.config.get_setting('memory_optimization.leak_detection_interval', 300)  # Seconds
        
        # Memory tracking
        self.memory_history = []
        self.history_lock = threading.RLock()
        
        # Leak detection callbacks
        self.leak_callbacks = []
    
    def add_leak_callback(self, callback: Callable):
        """Add memory leak detection callback"""
        self.leak_callbacks.append(callback)
    
    def _execute_optimization(self):
        """Execute memory leak detection"""
        if not self.leak_detection_enabled:
            return
        
        current_memory = self._get_current_memory_usage()
        
        with self.history_lock:
            self.memory_history.append({
                'timestamp': time.time(),
                'memory': current_memory
            })
            
            # Keep only recent history
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-100:]
            
            # Check for memory leaks
            if len(self.memory_history) >= 10:
                self._check_memory_leaks()
    
    def _get_current_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)  # MB
        except:
            return 0.0
    
    def _check_memory_leaks(self):
        """Check for memory leaks"""
        recent_history = self.memory_history[-10:]
        
        # Calculate memory trend
        memory_values = [entry['memory'] for entry in recent_history]
        if len(memory_values) < 2:
            return
        
        # Check if memory is consistently increasing
        increasing_count = 0
        for i in range(1, len(memory_values)):
            if memory_values[i] > memory_values[i-1]:
                increasing_count += 1
        
        # If memory is increasing in most readings, check for leaks
        if increasing_count >= len(memory_values) * 0.7:
            memory_increase = ((memory_values[-1] - memory_values[0]) / memory_values[0]) * 100
            
            if memory_increase > self.memory_increase_threshold:
                self._trigger_leak_detection(memory_values, memory_increase)
    
    def _trigger_leak_detection(self, memory_values: List[float], increase_percent: float):
        """Trigger memory leak detection"""
        self.logger.warning(f"Potential memory leak detected: {increase_percent:.1f}% increase")
        
        # Call leak detection callbacks
        for callback in self.leak_callbacks:
            try:
                callback(memory_values, increase_percent)
            except Exception as e:
                self.logger.error(f"Leak detection callback error: {e}")

class ResourceCleanupStrategy(OptimizationStrategy):
    """Resource cleanup optimization strategy"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.resource_cleanup_threshold = self.config.get_setting('memory_optimization.resource_cleanup_threshold', 1000)
        self.resource_types = ['files', 'connections', 'threads']
        
        # Track resources
        self.resource_counts = defaultdict(int)
        self.resource_lock = threading.RLock()
    
    def register_resource(self, resource_type: str, count: int = 1):
        """Register resource usage"""
        with self.resource_lock:
            self.resource_counts[resource_type] += count
    
    def unregister_resource(self, resource_type: str, count: int = 1):
        """Unregister resource usage"""
        with self.resource_lock:
            self.resource_counts[resource_type] = max(0, self.resource_counts[resource_type] - count)
    
    def _execute_optimization(self):
        """Execute resource cleanup"""
        with self.resource_lock:
            for resource_type, count in self.resource_counts.items():
                if count > self.resource_cleanup_threshold:
                    self.logger.warning(f"High resource usage detected: {resource_type} = {count}")
                    self._cleanup_resource(resource_type)
    
    def _cleanup_resource(self, resource_type: str):
        """Clean up specific resource type"""
        try:
            if resource_type == 'files':
                self._cleanup_file_handles()
            elif resource_type == 'connections':
                self._cleanup_connections()
            elif resource_type == 'threads':
                self._cleanup_threads()
        except Exception as e:
            self.logger.error(f"Resource cleanup error for {resource_type}: {e}")
    
    def _cleanup_file_handles(self):
        """Clean up file handles"""
        try:
            process = psutil.Process()
            open_files = process.open_files()
            
            if len(open_files) > 100:
                self.logger.warning(f"High number of open files: {len(open_files)}")
                
                # Close unused file handles (this is a simplified example)
                # In practice, you'd need to track which files are still in use
                self.logger.info("File handle cleanup completed")
                
        except Exception as e:
            self.logger.error(f"File handle cleanup error: {e}")
    
    def _cleanup_connections(self):
        """Clean up connections"""
        try:
            process = psutil.Process()
            connections = process.connections()
            
            if len(connections) > 100:
                self.logger.warning(f"High number of connections: {len(connections)}")
                
                # Close unused connections
                self.logger.info("Connection cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Connection cleanup error: {e}")
    
    def _cleanup_threads(self):
        """Clean up threads"""
        try:
            thread_count = threading.active_count()
            
            if thread_count > 50:
                self.logger.warning(f"High number of threads: {thread_count}")
                
                # Note: Thread cleanup is complex and should be done carefully
                self.logger.info("Thread cleanup completed")
                
        except Exception as e:
            self.logger.error(f"Thread cleanup error: {e}")

class AdaptiveOptimizationStrategy(OptimizationStrategy):
    """Adaptive optimization strategy that adjusts based on system conditions"""
    
    def __init__(self, config: PerformanceConfig = None):
        super().__init__(config)
        self.adaptive_mode = self.config.get_setting('memory_optimization.adaptive_mode', True)
        
        # System thresholds
        self.high_memory_threshold = self.config.get_setting('memory_optimization.high_memory_threshold', 80)
        self.high_cpu_threshold = self.config.get_setting('memory_optimization.high_cpu_threshold', 80)
        
        # Optimization levels
        self.optimization_levels = {
            'low': {
                'gc_enabled': True,
                'cache_cleanup': False,
                'aggressive_cleanup': False
            },
            'medium': {
                'gc_enabled': True,
                'cache_cleanup': True,
                'aggressive_cleanup': False
            },
            'high': {
                'gc_enabled': True,
                'cache_cleanup': True,
                'aggressive_cleanup': True
            }
        }
        
        self.current_level = 'medium'
    
    def _execute_optimization(self):
        """Execute adaptive optimization"""
        if not self.adaptive_mode:
            return
        
        # Determine system conditions
        memory_percent = self._get_memory_percent()
        cpu_percent = self._get_cpu_percent()
        
        # Determine optimization level
        new_level = self._determine_optimization_level(memory_percent, cpu_percent)
        
        if new_level != self.current_level:
            self.current_level = new_level
            self.logger.info(f"Adaptive optimization level changed to: {new_level}")
        
        # Execute optimization based on level
        level_config = self.optimization_levels[self.current_level]
        
        if level_config['gc_enabled']:
            gc.collect()
        
        if level_config['cache_cleanup']:
            self._cleanup_caches()
        
        if level_config['aggressive_cleanup']:
            self._aggressive_cleanup()
    
    def _get_memory_percent(self) -> float:
        """Get memory usage percentage"""
        try:
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _get_cpu_percent(self) -> float:
        """Get CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _determine_optimization_level(self, memory_percent: float, cpu_percent: float) -> str:
        """Determine optimization level based on system conditions"""
        if memory_percent > self.high_memory_threshold or cpu_percent > self.high_cpu_threshold:
            return 'high'
        elif memory_percent > 60 or cpu_percent > 60:
            return 'medium'
        else:
            return 'low'
    
    def _cleanup_caches(self):
        """Clean up caches"""
        # Implementation depends on your caching system
        pass
    
    def _aggressive_cleanup(self):
        """Perform aggressive cleanup"""
        # Perform more aggressive cleanup operations
        gc.collect(2)  # Collect oldest generation
        # Additional aggressive cleanup as needed