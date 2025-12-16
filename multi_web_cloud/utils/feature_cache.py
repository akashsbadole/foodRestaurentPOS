"""
High-performance caching for feature flag evaluations
"""

import time
import threading
from typing import Any, Optional, Dict, Set
from collections import OrderedDict
from flask import current_app


class FeatureCache:
    """
    High-performance caching for feature flag evaluations
    """
    
    def __init__(self, cache_size=1000, ttl=300):
        self.cache_size = cache_size
        self.ttl = ttl
        self.cache = OrderedDict()
        self.access_times = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get cached feature value"""
        with self.lock:
            full_key = self._make_key(key, tenant_id)
            
            if full_key not in self.cache:
                self.misses += 1
                return None
            
            # Check if entry has expired
            entry = self.cache[full_key]
            if self._is_expired(entry):
                del self.cache[full_key]
                if full_key in self.access_times:
                    del self.access_times[full_key]
                self.misses += 1
                return None
            
            # Update access time and move to end (LRU)
            self.access_times[full_key] = time.time()
            self.cache.move_to_end(full_key)
            self.hits += 1
            
            return entry['value']
    
    def set(self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None):
        """Cache feature value"""
        with self.lock:
            full_key = self._make_key(key, tenant_id)
            current_time = time.time()
            
            # Set TTL
            if ttl is None:
                ttl = self.ttl
            
            # Create cache entry
            entry = {
                'value': value,
                'created_at': current_time,
                'expires_at': current_time + ttl,
                'ttl': ttl
            }
            
            # Add to cache
            self.cache[full_key] = entry
            self.access_times[full_key] = current_time
            
            # Move to end
            self.cache.move_to_end(full_key)
            
            # Evict if necessary
            self._evict_if_needed()
    
    def invalidate_tenant_cache(self, tenant_id: str):
        """Invalidate cache for specific tenant"""
        with self.lock:
            keys_to_remove = []
            
            for key in self.cache.keys():
                if f":{tenant_id}:" in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
    
    def invalidate_feature_cache(self, feature_name: str):
        """Invalidate cache for specific feature"""
        with self.lock:
            keys_to_remove = []
            
            for key in self.cache.keys():
                if key.startswith(f"{feature_name}:"):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        with self.lock:
            import re
            regex = re.compile(pattern)
            keys_to_remove = []
            
            for key in self.cache.keys():
                if regex.search(key):
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.hits = 0
            self.misses = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.cache_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'ttl': self.ttl
            }
    
    def get_expired_entries(self) -> Set[str]:
        """Get set of expired cache entries"""
        with self.lock:
            current_time = time.time()
            expired = set()
            
            for key, entry in self.cache.items():
                if self._is_expired(entry, current_time):
                    expired.add(key)
            
            return expired
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        with self.lock:
            expired = self.get_expired_entries()
            count = len(expired)
            
            for key in expired:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
            
            return count
    
    def _make_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Create full cache key"""
        if tenant_id:
            return f"{key}:{tenant_id}:{time.time() // 60}"  # Add minute bucket for cache invalidation
        return f"{key}:global:{time.time() // 60}"
    
    def _is_expired(self, entry: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """Check if cache entry has expired"""
        if current_time is None:
            current_time = time.time()
        return current_time > entry['expires_at']
    
    def _evict_if_needed(self):
        """Evict least recently used entries if cache is full"""
        while len(self.cache) > self.cache_size:
            # Remove oldest entry (first in OrderedDict)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.access_times:
                del self.access_times[oldest_key]


class MultiLevelFeatureCache:
    """
    Multi-level caching strategy for optimal performance
    """
    
    def __init__(self, l1_size=100, l2_size=1000, ttl=300):
        # L1 Cache (in-memory, fastest)
        self.l1_cache = FeatureCache(l1_size, ttl)
        
        # L2 Cache (larger, slightly slower)
        self.l2_cache = FeatureCache(l2_size, ttl)
        
        self.ttl = ttl
    
    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try L1 first
        value = self.l1_cache.get(key, tenant_id)
        if value is not None:
            return value
        
        # Try L2
        value = self.l2_cache.get(key, tenant_id)
        if value is not None:
            # Promote to L1
            self.l1_cache.set(key, value, tenant_id)
            return value
        
        return None
    
    def set(self, key: str, value: Any, tenant_id: Optional[str] = None, ttl: Optional[int] = None):
        """Set value in both cache levels"""
        self.l1_cache.set(key, value, tenant_id, ttl)
        self.l2_cache.set(key, value, tenant_id, ttl)
    
    def invalidate_tenant_cache(self, tenant_id: str):
        """Invalidate cache for specific tenant in both levels"""
        self.l1_cache.invalidate_tenant_cache(tenant_id)
        self.l2_cache.invalidate_tenant_cache(tenant_id)
    
    def invalidate_feature_cache(self, feature_name: str):
        """Invalidate cache for specific feature in both levels"""
        self.l1_cache.invalidate_feature_cache(feature_name)
        self.l2_cache.invalidate_feature_cache(feature_name)
    
    def clear(self):
        """Clear both cache levels"""
        self.l1_cache.clear()
        self.l2_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics"""
        l1_stats = self.l1_cache.get_cache_stats()
        l2_stats = self.l2_cache.get_cache_stats()
        
        total_hits = l1_stats['hits'] + l2_stats['hits']
        total_misses = l1_stats['misses'] + l2_stats['misses']
        total_requests = total_hits + total_misses
        overall_hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'l1_cache': l1_stats,
            'l2_cache': l2_stats,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'overall_hit_rate': overall_hit_rate,
            'total_size': l1_stats['size'] + l2_stats['size']
        }
    
    def cleanup_expired(self) -> int:
        """Clean up expired entries in both levels"""
        l1_cleaned = self.l1_cache.cleanup_expired()
        l2_cleaned = self.l2_cache.cleanup_expired()
        return l1_cleaned + l2_cleaned


# Global cache instance
feature_cache = MultiLevelFeatureCache()