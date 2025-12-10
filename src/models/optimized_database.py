"""
Optimized Database Module for Desktop POS Application
Implements connection pooling, query optimization, and caching
"""

import threading
import time
import weakref
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Tuple, Callable
import sqlite3
import logging
import json
import os
from datetime import datetime, timedelta
from collections import OrderedDict
import psutil
import gc

from src.config.performance_config import PerformanceConfig

class DatabaseConnectionPool:
    """Database connection pool for better performance"""
    
    def __init__(self, db_path: str, pool_size: int = 10, max_overflow: int = 20):
        self.db_path = db_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool = OrderedDict()
        self.overflow_pool = OrderedDict()
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self.pool[conn] = {'created_at': time.time(), 'in_use': False}
            except Exception as e:
                self.logger.error(f"Failed to create connection: {e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create optimized database connection"""
        conn = sqlite3.connect(self.db_path)
        
        # Apply SQLite optimizations
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.execute("PRAGMA cache_size = 10000")
        cursor.execute("PRAGMA temp_store = MEMORY")
        cursor.execute("PRAGMA mmap_size = 268435456")  # 256MB
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
        cursor.execute("PRAGMA read_uncommitted = True")
        conn.commit()
        cursor.close()
        
        return conn
    
    def get_connection(self) -> sqlite3.Connection:
        """Get connection from pool"""
        with self.lock:
            # Try to get connection from main pool
            for conn, info in self.pool.items():
                if not info['in_use']:
                    info['in_use'] = True
                    info['last_used'] = time.time()
                    return conn
            
            # Try to get connection from overflow pool
            if len(self.overflow_pool) < self.max_overflow:
                conn = self._create_connection()
                self.overflow_pool[conn] = {'created_at': time.time(), 'in_use': True}
                return conn
            
            # Wait for available connection (simplified)
            self.logger.warning("Connection pool exhausted, waiting for available connection")
            time.sleep(0.1)
            return self.get_connection()
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool"""
        with self.lock:
            if conn in self.pool:
                self.pool[conn]['in_use'] = False
                self.pool[conn]['last_used'] = time.time()
            elif conn in self.overflow_pool:
                # Close overflow connections to prevent leaks
                try:
                    conn.close()
                except:
                    pass
                del self.overflow_pool[conn]
    
    def cleanup_expired(self, max_age: int = 3600):
        """Clean up old connections"""
        with self.lock:
            current_time = time.time()
            
            # Clean overflow pool
            expired_overflow = [
                conn for conn, info in self.overflow_pool.items()
                if current_time - info['created_at'] > max_age
            ]
            for conn in expired_overflow:
                try:
                    conn.close()
                except:
                    pass
                del self.overflow_pool[conn]
            
            # Clean main pool (keep minimum connections)
            active_connections = [conn for conn, info in self.pool.items() if info['in_use']]
            inactive_connections = [conn for conn, info in self.pool.items() if not info['in_use']]
            
            # Remove some inactive connections if we have too many
            if len(inactive_connections) > self.pool_size // 2:
                for conn in inactive_connections[:len(inactive_connections) - self.pool_size // 2]:
                    try:
                        conn.close()
                    except:
                        pass
                    del self.pool[conn]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self.lock:
            return {
                'pool_size': len(self.pool),
                'active_connections': sum(1 for info in self.pool.values() if info['in_use']),
                'overflow_connections': len(self.overflow_pool),
                'total_connections': len(self.pool) + len(self.overflow_pool)
            }

class QueryOptimizer:
    """Query optimization utilities"""
    
    def __init__(self, connection_pool: DatabaseConnectionPool):
        self.connection_pool = connection_pool
        self.logger = logging.getLogger(__name__)
        self.query_cache = OrderedDict()
        self.query_stats = {}
        self.cache_lock = threading.RLock()
        
    def execute_query(self, query: str, params: tuple = None, use_cache: bool = True, 
                    ttl: int = None) -> List[Tuple]:
        """Execute optimized query with caching"""
        cache_key = self._get_cache_key(query, params)
        
        # Check cache first
        if use_cache:
            cached_result = self._get_from_cache(cache_key, ttl)
            if cached_result is not None:
                self._update_query_stats(query, cached=True)
                return cached_result
        
        # Execute query
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchall()
                
                # Cache result
                if use_cache:
                    self._set_cache(cache_key, result, ttl)
                
                self._update_query_stats(query, cached=False)
                return result
                
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if 'conn' in locals():
                self.connection_pool.return_connection(conn)
    
    def execute_query_one(self, query: str, params: tuple = None, use_cache: bool = True) -> Optional[Tuple]:
        """Execute query and return first result"""
        results = self.execute_query(query, params, use_cache)
        return results[0] if results else None
    
    def execute_query_many(self, query: str, params_list: List[tuple]) -> List[List[Tuple]]:
        """Execute query with multiple parameter sets"""
        results = []
        for params in params_list:
            result = self.execute_query(query, params)
            results.append(result)
        return results
    
    def _get_cache_key(self, query: str, params: tuple = None) -> str:
        """Generate cache key for query"""
        import hashlib
        key_data = f"{query}_{str(params)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str, ttl: int = None) -> Optional[List[Tuple]]:
        """Get result from cache"""
        with self.cache_lock:
            if cache_key not in self.query_cache:
                return None
            
            result, cached_time = self.query_cache[cache_key]
            
            # Check if expired
            if ttl is not None and time.time() - cached_time > ttl:
                del self.query_cache[cache_key]
                return None
            
            # Move to end for LRU
            self.query_cache.move_to_end(cache_key)
            return result
    
    def _set_cache(self, cache_key: str, result: List[Tuple], ttl: int = None):
        """Set result in cache"""
        with self.cache_lock:
            # Limit cache size
            if len(self.query_cache) >= 1000:  # Max 1000 cached queries
                self.query_cache.popitem(last=False)
            
            self.query_cache[cache_key] = (result, time.time())
            self.query_cache.move_to_end(cache_key)
    
    def _update_query_stats(self, query: str, cached: bool = False):
        """Update query execution statistics"""
        if query not in self.query_stats:
            self.query_stats[query] = {'executions': 0, 'cached': 0, 'total_time': 0}
        
        self.query_stats[query]['executions'] += 1
        if cached:
            self.query_stats[query]['cached'] += 1
    
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
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        return self.query_stats.copy()
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.connection_pool.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Transaction failed: {e}")
            raise
        finally:
            self.connection_pool.return_connection(conn)

class DatabaseOptimizer:
    """Main database optimizer for desktop application"""
    
    def __init__(self, db_path: str, config: PerformanceConfig = None):
        self.db_path = db_path
        self.config = config or PerformanceConfig()
        self.connection_pool = DatabaseConnectionPool(
            db_path,
            pool_size=self.config.get_setting('performance_settings.database_optimization.connection_pooling.pool_size', 10),
            max_overflow=self.config.get_setting('performance_settings.database_optimization.connection_pooling.max_overflow', 20)
        )
        self.query_optimizer = QueryOptimizer(self.connection_pool)
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Clean every 5 minutes
                    self.connection_pool.cleanup_expired()
                    self.logger.debug("Database connection pool cleanup completed")
                except Exception as e:
                    self.logger.error(f"Cleanup thread error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection from pool"""
        return self.connection_pool.get_connection()
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return database connection to pool"""
        self.connection_pool.return_connection(conn)
    
    def execute_query(self, query: str, params: tuple = None, use_cache: bool = True, 
                    ttl: int = None) -> List[Tuple]:
        """Execute optimized query"""
        return self.query_optimizer.execute_query(query, params, use_cache, ttl)
    
    def execute_query_one(self, query: str, params: tuple = None, use_cache: bool = True) -> Optional[Tuple]:
        """Execute query and return first result"""
        return self.query_optimizer.execute_query_one(query, params, use_cache)
    
    def execute_query_many(self, query: str, params_list: List[tuple]) -> List[List[Tuple]]:
        """Execute query with multiple parameter sets"""
        return self.query_optimizer.execute_query_many(query, params_list)
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.query_optimizer.transaction() as cursor:
            yield cursor
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            'connection_pool': self.connection_pool.get_stats(),
            'cache': self.query_optimizer.get_cache_stats(),
            'queries': self.query_optimizer.get_query_stats()
        }
    
    def optimize_database(self):
        """Optimize database performance"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Run vacuum if database is large
                cursor.execute("SELECT COUNT(*) FROM sqlite_master")
                table_count = cursor.fetchone()[0]
                
                if table_count > 10:  # If we have many tables
                    cursor.execute("VACUUM")
                    conn.commit()
                
                # Analyze database statistics
                cursor.execute("ANALYZE")
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
    
    def clear_all_caches(self):
        """Clear all caches"""
        self.query_optimizer.clear_cache()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.connection_pool.cleanup_expired(max_age=0)
        except:
            pass

# Global database optimizer instance
_db_optimizer = None

def get_db_optimizer(db_path: str = None, config: PerformanceConfig = None) -> DatabaseOptimizer:
    """Get global database optimizer instance"""
    global _db_optimizer
    if _db_optimizer is None:
        db_path = db_path or 'restaurant_pos.db'
        _db_optimizer = DatabaseOptimizer(db_path, config)
    return _db_optimizer

def optimize_database_query(query: str, params: tuple = None, use_cache: bool = True, 
                          ttl: int = None) -> List[Tuple]:
    """Execute optimized database query"""
    optimizer = get_db_optimizer()
    return optimizer.execute_query(query, params, use_cache, ttl)