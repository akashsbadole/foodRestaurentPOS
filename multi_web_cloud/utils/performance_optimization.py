"""
Performance Optimization with Lazy Loading
Provides performance optimization and lazy loading for UI components
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import current_app, request
import json
from datetime import datetime, timedelta
from utils.feature_flag_manager import feature_manager


class PerformanceRule:
    """
    Represents a performance optimization rule
    """
    
    def __init__(self, rule_id: str, **kwargs):
        self.rule_id = rule_id
        self.name = kwargs.get('name', rule_id.title())
        self.description = kwargs.get('description', '')
        self.category = kwargs.get('category', 'general')  # loading, caching, rendering, network
        self.condition = kwargs.get('condition', None)  # Function to check if rule applies
        self.action = kwargs.get('action', None)  # Function to apply optimization
        self.priority = kwargs.get('priority', 'medium')  # low, medium, high, critical
        self.impact = kwargs.get('impact', 'moderate')  # minimal, moderate, significant, major
        self.metrics = kwargs.get('metrics', {})  # Expected performance improvements
        self.auto_apply = kwargs.get('auto_apply', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary"""
        return {
            'id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'impact': self.impact,
            'metrics': self.metrics,
            'auto_apply': self.auto_apply
        }


class LazyLoadComponent:
    """
    Represents a lazy-loadable component
    """
    
    def __init__(self, component_id: str, **kwargs):
        self.component_id = component_id
        self.name = kwargs.get('name', component_id.title())
        self.component_type = kwargs.get('component_type', 'view')
        self.load_trigger = kwargs.get('load_trigger', 'viewport')  # viewport, click, scroll, manual
        self.load_strategy = kwargs.get('load_strategy', 'async')  # async, defer, prefetch
        self.placeholder = kwargs.get('placeholder', None)
        self.fallback = kwargs.get('fallback', None)
        self.dependencies = kwargs.get('dependencies', [])
        self.required_features = kwargs.get('required_features', [])
        self.priority = kwargs.get('priority', 100)
        self.cache_duration = kwargs.get('cache_duration', 3600)  # seconds
        self.preload_conditions = kwargs.get('preload_conditions', [])
        self.load_timeout = kwargs.get('load_timeout', 10000)  # milliseconds
        self.retry_attempts = kwargs.get('retry_attempts', 3)
        self.css_classes = kwargs.get('css_classes', [])
        self.attributes = kwargs.get('attributes', {})
        self.config = kwargs.get('config', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            'id': self.component_id,
            'name': self.name,
            'type': self.component_type,
            'load_trigger': self.load_trigger,
            'load_strategy': self.load_strategy,
            'placeholder': self.placeholder,
            'fallback': self.fallback,
            'dependencies': self.dependencies,
            'required_features': self.required_features,
            'priority': self.priority,
            'cache_duration': self.cache_duration,
            'preload_conditions': self.preload_conditions,
            'load_timeout': self.load_timeout,
            'retry_attempts': self.retry_attempts,
            'css_classes': self.css_classes,
            'attributes': self.attributes,
            'config': self.config
        }


class AssetBundle:
    """
    Represents an asset bundle for optimization
    """
    
    def __init__(self, bundle_id: str, **kwargs):
        self.bundle_id = bundle_id
        self.name = kwargs.get('name', bundle_id.title())
        self.bundle_type = kwargs.get('bundle_type', 'js')  # js, css, images
        self.assets = kwargs.get('assets', [])  # List of asset files
        self.dependencies = kwargs.get('dependencies', [])
        self.required_features = kwargs.get('required_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.minify = kwargs.get('minify', True)
        self.compress = kwargs.get('compress', True)
        self.cache_headers = kwargs.get('cache_headers', {
            'Cache-Control': 'public, max-age=31536000',
            'ETag': True
        })
        self.load_strategy = kwargs.get('load_strategy', 'async')  # async, defer, preload
        self.priority = kwargs.get('priority', 100)
        self.version = kwargs.get('version', '1.0.0')
        self.integrity = kwargs.get('integrity', None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bundle to dictionary"""
        return {
            'id': self.bundle_id,
            'name': self.name,
            'type': self.bundle_type,
            'assets': self.assets,
            'dependencies': self.dependencies,
            'required_features': self.required_features,
            'retail_types': self.retail_types,
            'minify': self.minify,
            'compress': self.compress,
            'cache_headers': self.cache_headers,
            'load_strategy': self.load_strategy,
            'priority': self.priority,
            'version': self.version,
            'integrity': self.integrity
        }


class CacheManager:
    """
    Manages caching for performance optimization
    """
    
    def __init__(self):
        self.cache_store = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'size': 0,
            'evictions': 0
        }
        self.cache_config = {
            'max_size': 100,  # MB
            'max_entries': 1000,
            'default_ttl': 3600,  # seconds
            'cleanup_interval': 300  # seconds
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached item"""
        if key in self.cache_store:
            item = self.cache_store[key]
            if item['expires_at'] > datetime.utcnow():
                self.cache_stats['hits'] += 1
                return item['data']
            else:
                del self.cache_store[key]
                self.cache_stats['evictions'] += 1
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set cached item"""
        if ttl is None:
            ttl = self.cache_config['default_ttl']
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self.cache_store[key] = {
            'data': data,
            'expires_at': expires_at,
            'created_at': datetime.utcnow(),
            'size': len(str(data))
        }
        
        self._update_cache_size()
        self._evict_if_needed()
    
    def delete(self, key: str) -> None:
        """Delete cached item"""
        if key in self.cache_store:
            del self.cache_store[key]
            self._update_cache_size()
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache_store.clear()
        self.cache_stats['size'] = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'size': self.cache_stats['size'],
            'entries': len(self.cache_store),
            'evictions': self.cache_stats['evictions']
        }
    
    def _update_cache_size(self):
        """Update cache size statistics"""
        total_size = sum(item['size'] for item in self.cache_store.values())
        self.cache_stats['size'] = total_size
    
    def _evict_if_needed(self):
        """Evict cache entries if needed"""
        # Evict by size
        while (self.cache_stats['size'] > self.cache_config['max_size'] * 1024 * 1024 or
               len(self.cache_store) > self.cache_config['max_entries']):
            # Find oldest item
            oldest_key = min(self.cache_store.keys(), 
                           key=lambda k: self.cache_store[k]['created_at'])
            del self.cache_store[oldest_key]
            self.cache_stats['evictions'] += 1
        
        self._update_cache_size()


class PerformanceOptimizer:
    """
    Main performance optimization manager
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.rules = {}
        self.lazy_components = {}
        self.asset_bundles = {}
        self.cache_manager = CacheManager()
        self.performance_metrics = {}
        self.optimization_strategies = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize performance optimizer"""
        if self._initialized:
            return
        
        self._load_performance_rules()
        self._load_lazy_components()
        self._load_asset_bundles()
        self._load_optimization_strategies()
        self._initialized = True
    
    def _load_performance_rules(self):
        """Load performance optimization rules"""
        rules = [
            # Loading optimization rules
            PerformanceRule(
                'lazy_load_images',
                name='Lazy Load Images',
                description='Load images only when they enter viewport',
                category='loading',
                priority='high',
                impact='significant',
                metrics={'load_time_reduction': '30-50%', 'bandwidth_saving': '20-40%'},
                auto_apply=True
            ),
            PerformanceRule(
                'preload_critical_css',
                name='Preload Critical CSS',
                description='Preload critical CSS for faster rendering',
                category='loading',
                priority='high',
                impact='significant',
                metrics={'render_time_reduction': '20-30%', 'fcp_improvement': '15-25%'},
                auto_apply=True
            ),
            PerformanceRule(
                'defer_non_critical_js',
                name='Defer Non-Critical JavaScript',
                description='Defer loading of non-critical JavaScript',
                category='loading',
                priority='high',
                impact='significant',
                metrics={'load_time_reduction': '25-40%', 'fcp_improvement': '20-35%'},
                auto_apply=True
            ),
            # Caching optimization rules
            PerformanceRule(
                'browser_caching',
                name='Browser Caching',
                description='Set appropriate caching headers',
                category='caching',
                priority='medium',
                impact='moderate',
                metrics={'repeat_load_reduction': '80-95%'},
                auto_apply=True
            ),
            PerformanceRule(
                'component_caching',
                name='Component Caching',
                description='Cache rendered components',
                category='caching',
                priority='medium',
                impact='moderate',
                metrics={'render_time_reduction': '40-60%'},
                auto_apply=True
            ),
            # Rendering optimization rules
            PerformanceRule(
                'virtual_scrolling',
                name='Virtual Scrolling',
                description='Use virtual scrolling for large lists',
                category='rendering',
                priority='high',
                impact='major',
                metrics={'memory_reduction': '70-90%', 'scroll_performance': '200-300%'},
                auto_apply=True
            ),
            PerformanceRule(
                'debounce_events',
                name='Debounce Events',
                description='Debounce frequently triggered events',
                category='rendering',
                priority='medium',
                impact='moderate',
                metrics={'event_handler_reduction': '60-80%'},
                auto_apply=True
            ),
            # Network optimization rules
            PerformanceRule(
                'compress_responses',
                name='Compress Responses',
                description='Compress HTTP responses',
                category='network',
                priority='high',
                impact='significant',
                metrics={'bandwidth_saving': '60-80%'},
                auto_apply=True
            ),
            PerformanceRule(
                'bundle_assets',
                name='Bundle Assets',
                description='Bundle CSS and JavaScript files',
                category='network',
                priority='high',
                impact='significant',
                metrics={'request_reduction': '70-90%', 'bandwidth_saving': '10-20%'},
                auto_apply=True
            )
        ]
        
        for rule in rules:
            self.rules[rule.rule_id] = rule
    
    def _load_lazy_components(self):
        """Load lazy-loadable components"""
        components = [
            # Image components
            LazyLoadComponent(
                'product_image',
                name='Product Image',
                component_type='image',
                load_trigger='viewport',
                load_strategy='async',
                placeholder='loading-spinner',
                fallback='no-image-placeholder',
                required_features=['FEATURE_PRODUCT_CATALOG'],
                priority=10,
                cache_duration=86400,  # 24 hours
                preload_conditions=['user_scroll_nearby']
            ),
            LazyLoadComponent(
                'customer_avatar',
                name='Customer Avatar',
                component_type='image',
                load_trigger='viewport',
                load_strategy='async',
                placeholder='avatar-placeholder',
                fallback='default-avatar',
                required_features=['FEATURE_CUSTOMER_MANAGEMENT'],
                priority=20,
                cache_duration=3600  # 1 hour
            ),
            # Data components
            LazyLoadComponent(
                'order_history',
                name='Order History',
                component_type='data',
                load_trigger='scroll',
                load_strategy='async',
                placeholder='loading-indicator',
                required_features=['FEATURE_SALES_PROCESSING'],
                priority=30,
                cache_duration=300,  # 5 minutes
                preload_conditions=['user_near_bottom']
            ),
            LazyLoadComponent(
                'product_list',
                name='Product List',
                component_type='data',
                load_trigger='scroll',
                load_strategy='async',
                placeholder='skeleton-loader',
                required_features=['FEATURE_PRODUCT_CATALOG'],
                priority=25,
                cache_duration=1800,  # 30 minutes
                preload_conditions=['user_scroll_nearby']
            ),
            # Chart components
            LazyLoadComponent(
                'sales_chart',
                name='Sales Chart',
                component_type='chart',
                load_trigger='viewport',
                load_strategy='defer',
                placeholder='chart-placeholder',
                required_features=['FEATURE_SALES_PROCESSING'],
                priority=40,
                cache_duration=600  # 10 minutes
            ),
            LazyLoadComponent(
                'analytics_dashboard',
                name='Analytics Dashboard',
                component_type='dashboard',
                load_trigger='manual',
                load_strategy='async',
                placeholder='dashboard-placeholder',
                required_features=['FEATURE_ANALYTICS'],
                priority=50,
                cache_duration=1800  # 30 minutes
            ),
            # Modal components
            LazyLoadComponent(
                'product_modal',
                name='Product Modal',
                component_type='modal',
                load_trigger='click',
                load_strategy='async',
                placeholder=None,
                required_features=['FEATURE_PRODUCT_CATALOG'],
                priority=60,
                cache_duration=3600  # 1 hour
            ),
            LazyLoadComponent(
                'customer_modal',
                name='Customer Modal',
                component_type='modal',
                load_trigger='click',
                load_strategy='async',
                placeholder=None,
                required_features=['FEATURE_CUSTOMER_MANAGEMENT'],
                priority=65,
                cache_duration=1800  # 30 minutes
            )
        ]
        
        for component in components:
            self.lazy_components[component.component_id] = component
    
    def _load_asset_bundles(self):
        """Load asset bundles for optimization"""
        bundles = [
            # Core bundles
            AssetBundle(
                'core_css',
                name='Core CSS',
                bundle_type='css',
                assets=[
                    'css/modern-pos.css',
                    'css/common.css',
                    'css/components.css'
                ],
                minify=True,
                compress=True,
                load_strategy='preload',
                priority=1
            ),
            AssetBundle(
                'core_js',
                name='Core JavaScript',
                bundle_type='js',
                assets=[
                    'js/utils.js',
                    'js/pos-core.js',
                    'js/validation.js'
                ],
                minify=True,
                compress=True,
                load_strategy='defer',
                priority=1
            ),
            # Retail-type specific bundles
            AssetBundle(
                'restaurant_css',
                name='Restaurant CSS',
                bundle_type='css',
                assets=[
                    'css/restaurant.css',
                    'css/tables.css',
                    'css/kitchen.css'
                ],
                retail_types=['restaurant'],
                required_features=['FEATURE_TABLE_MANAGEMENT', 'FEATURE_KITCHEN_DISPLAY'],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=10
            ),
            AssetBundle(
                'retail_css',
                name='Retail CSS',
                bundle_type='css',
                assets=[
                    'css/retail.css',
                    'css/barcode.css',
                    'css/inventory.css'
                ],
                retail_types=['retail'],
                required_features=['FEATURE_BARCODE_SCANNING', 'FEATURE_INVENTORY_BASIC'],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=10
            ),
            AssetBundle(
                'apparel_css',
                name='Apparel CSS',
                bundle_type='css',
                assets=[
                    'css/apparel.css',
                    'css/variants.css',
                    'css/exchanges.css'
                ],
                retail_types=['apparel'],
                required_features=['FEATURE_SIZE_VARIANTS', 'FEATURE_EXCHANGE_MANAGEMENT'],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=10
            ),
            AssetBundle(
                'grocery_css',
                name='Grocery CSS',
                bundle_type='css',
                assets=[
                    'css/grocery.css',
                    'css/weighing.css',
                    'css/expiry.css'
                ],
                retail_types=['grocery'],
                required_features=['FEATURE_WEIGHING_SCALE', 'FEATURE_EXPIRY_TRACKING'],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=10
            ),
            # Feature-specific bundles
            AssetBundle(
                'dashboard_js',
                name='Dashboard JavaScript',
                bundle_type='js',
                assets=[
                    'js/dashboard.js',
                    'js/charts.js',
                    'js/widgets.js'
                ],
                required_features=['FEATURE_DASHBOARD'],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=20
            ),
            AssetBundle(
                'mobile_js',
                name='Mobile JavaScript',
                bundle_type='js',
                assets=[
                    'js/mobile.js',
                    'js/touch.js',
                    'js/gestures.js'
                ],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=30
            ),
            AssetBundle(
                'accessibility_js',
                name='Accessibility JavaScript',
                bundle_type='js',
                assets=[
                    'js/accessibility.js',
                    'js/screen-reader.js',
                    'js/keyboard.js'
                ],
                minify=True,
                compress=True,
                load_strategy='async',
                priority=40
            )
        ]
        
        for bundle in bundles:
            self.asset_bundles[bundle.bundle_id] = bundle
    
    def _load_optimization_strategies(self):
        """Load optimization strategies"""
        strategies = {
            'image_optimization': {
                'name': 'Image Optimization',
                'description': 'Optimize images for faster loading',
                'techniques': [
                    'webp_conversion',
                    'responsive_images',
                    'lazy_loading',
                    'compression',
                    'cdn_delivery'
                ],
                'expected_improvement': '40-60% bandwidth reduction'
            },
            'code_splitting': {
                'name': 'Code Splitting',
                'description': 'Split code into smaller chunks',
                'techniques': [
                    'route_based_splitting',
                    'feature_based_splitting',
                    'vendor_separation',
                    'dynamic_imports'
                ],
                'expected_improvement': '30-50% initial load reduction'
            },
            'caching_strategy': {
                'name': 'Caching Strategy',
                'description': 'Implement multi-level caching',
                'techniques': [
                    'browser_cache',
                    'cdn_cache',
                    'application_cache',
                    'database_cache',
                    'memory_cache'
                ],
                'expected_improvement': '70-90% cache hit rate'
            },
            'rendering_optimization': {
                'name': 'Rendering Optimization',
                'description': 'Optimize rendering performance',
                'techniques': [
                    'virtual_scrolling',
                    'debouncing',
                    'throttling',
                    'request_animation_frame',
                    'web_workers'
                ],
                'expected_improvement': '200-400% rendering performance'
            }
        }
        
        self.optimization_strategies = strategies
    
    def get_optimization_config(self, tenant_id: Optional[str] = None, 
                             user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Get optimization configuration for tenant
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Detect device capabilities
        device_info = self._detect_device_capabilities(user_agent or request.headers.get('User-Agent', ''))
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(enabled_features, retail_type, device_info)
        
        # Get lazy components
        lazy_components = self._get_lazy_components(enabled_features, retail_type)
        
        # Get asset bundles
        asset_bundles = self._get_asset_bundles(enabled_features, retail_type)
        
        # Get cache stats
        cache_stats = self.cache_manager.get_stats()
        
        return {
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'device_info': device_info,
            'applicable_rules': [rule.to_dict() for rule in applicable_rules],
            'lazy_components': [comp.to_dict() for comp in lazy_components],
            'asset_bundles': [bundle.to_dict() for bundle in asset_bundles],
            'cache_stats': cache_stats,
            'optimization_strategies': self.optimization_strategies,
            'performance_metrics': self.performance_metrics
        }
    
    def _detect_device_capabilities(self, user_agent: str) -> Dict[str, Any]:
        """Detect device capabilities for optimization"""
        user_agent = user_agent.lower()
        
        capabilities = {
            'connection_speed': 'unknown',
            'memory': 'unknown',
            'cpu_cores': 'unknown',
            'webp_support': False,
            'service_worker_support': False,
            'intersection_observer_support': False,
            'resize_observer_support': False,
            'web_worker_support': False,
            'touch_support': False,
            'screen_size': 'unknown',
            'pixel_ratio': 1.0
        }
        
        # Detect browser features
        capabilities['webp_support'] = 'chrome' in user_agent or 'firefox' in user_agent
        capabilities['service_worker_support'] = 'chrome' in user_agent or 'firefox' in user_agent
        capabilities['intersection_observer_support'] = 'chrome' in user_agent or 'firefox' in user_agent
        capabilities['resize_observer_support'] = 'chrome' in user_agent or 'firefox' in user_agent
        capabilities['web_worker_support'] = 'chrome' in user_agent or 'firefox' in user_agent
        capabilities['touch_support'] = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent
        
        # Estimate connection speed based on device type
        if 'mobile' in user_agent:
            capabilities['connection_speed'] = '3g'  # Conservative estimate
        elif 'tablet' in user_agent:
            capabilities['connection_speed'] = '4g'
        else:
            capabilities['connection_speed'] = 'broadband'
        
        # Estimate memory and CPU based on device
        if 'iphone' in user_agent:
            capabilities['memory'] = 'medium'
            capabilities['cpu_cores'] = 6  # Modern iPhones
        elif 'android' in user_agent:
            capabilities['memory'] = 'medium'
            capabilities['cpu_cores'] = 8  # Typical Android
        else:
            capabilities['memory'] = 'high'
            capabilities['cpu_cores'] = 4  # Conservative desktop estimate
        
        return capabilities
    
    def _get_applicable_rules(self, enabled_features: Set[str], retail_type: str, 
                            device_info: Dict[str, Any]) -> List[PerformanceRule]:
        """Get applicable performance rules"""
        applicable_rules = []
        
        for rule in self.rules.values():
            # Check if rule applies to current context
            if rule.condition and not rule.condition(enabled_features, retail_type, device_info):
                continue
            
            # Check if rule should be auto-applied
            if rule.auto_apply:
                applicable_rules.append(rule)
        
        # Sort by priority
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        applicable_rules.sort(key=lambda r: priority_order.get(r.priority, 0), reverse=True)
        
        return applicable_rules
    
    def _get_lazy_components(self, enabled_features: Set[str], retail_type: str) -> List[LazyLoadComponent]:
        """Get lazy-loadable components"""
        lazy_components = []
        
        for component in self.lazy_components.values():
            # Check required features
            if component.required_features:
                if not all(feature in enabled_features for feature in component.required_features):
                    continue
            
            # Check retail type compatibility
            if hasattr(component, 'retail_types') and component.retail_types:
                if retail_type not in component.retail_types:
                    continue
            
            lazy_components.append(component)
        
        # Sort by priority
        lazy_components.sort(key=lambda c: c.priority)
        
        return lazy_components
    
    def _get_asset_bundles(self, enabled_features: Set[str], retail_type: str) -> List[AssetBundle]:
        """Get asset bundles for current context"""
        bundles = []
        
        for bundle in self.asset_bundles.values():
            # Check required features
            if bundle.required_features:
                if not all(feature in enabled_features for feature in bundle.required_features):
                    continue
            
            # Check retail type compatibility
            if bundle.retail_types and retail_type not in bundle.retail_types:
                continue
            
            bundles.append(bundle)
        
        # Sort by priority
        bundles.sort(key=lambda b: b.priority)
        
        return bundles
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def register_rule(self, rule: PerformanceRule):
        """Register a performance rule"""
        self.rules[rule.rule_id] = rule
    
    def register_lazy_component(self, component: LazyLoadComponent):
        """Register a lazy-loadable component"""
        self.lazy_components[component.component_id] = component
    
    def register_asset_bundle(self, bundle: AssetBundle):
        """Register an asset bundle"""
        self.asset_bundles[bundle.bundle_id] = bundle
    
    def cache_component(self, component_id: str, data: Any, ttl: Optional[int] = None):
        """Cache component data"""
        cache_key = f"component_{component_id}"
        self.cache_manager.set(cache_key, data, ttl)
    
    def get_cached_component(self, component_id: str) -> Optional[Any]:
        """Get cached component data"""
        cache_key = f"component_{component_id}"
        return self.cache_manager.get(cache_key)
    
    def clear_cache(self, pattern: Optional[str] = None):
        """Clear cache with optional pattern"""
        if pattern:
            keys_to_delete = [key for key in self.cache_manager.cache_store.keys() if pattern in key]
            for key in keys_to_delete:
                self.cache_manager.delete(key)
        else:
            self.cache_manager.clear()
    
    def record_performance_metric(self, metric_name: str, value: float, 
                              tags: Optional[Dict[str, str]] = None):
        """Record performance metric"""
        if metric_name not in self.performance_metrics:
            self.performance_metrics[metric_name] = []
        
        self.performance_metrics[metric_name].append({
            'value': value,
            'timestamp': datetime.utcnow(),
            'tags': tags or {}
        })
        
        # Keep only last 100 entries per metric
        if len(self.performance_metrics[metric_name]) > 100:
            self.performance_metrics[metric_name] = self.performance_metrics[metric_name][-100:]


# Global performance optimizer instance
performance_optimizer = None


def get_performance_optimizer(feature_manager=None) -> PerformanceOptimizer:
    """Get or create global performance optimizer instance"""
    global performance_optimizer
    if performance_optimizer is None:
        performance_optimizer = PerformanceOptimizer(feature_manager)
    return performance_optimizer