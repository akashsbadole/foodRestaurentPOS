"""
Centralized Data Manager for POS Application
Handles data caching, synchronization, and event-driven updates
"""

import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from src.utils.event_dispatcher import event_dispatcher, EventType

class DataCache:
    """Simple thread-safe data cache"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.RLock()
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Any:
        """Get cached data if valid"""
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check if cache is expired
            if key in self._timestamps:
                if time.time() - self._timestamps[key] > self.ttl:
                    self.invalidate(key)
                    return None
            
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set cached data"""
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached data"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._timestamps:
                del self._timestamps[key]
    
    def invalidate_all(self) -> None:
        """Invalidate all cached data"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

class DataManager:
    """Centralized data management with caching and synchronization"""
    
    def __init__(self, app):
        self.app = app
        self.cache = DataCache(ttl_seconds=300)  # 5 minutes cache
        self._lock = threading.RLock()
        
        # Register event listeners
        self._setup_event_listeners()
        
        # Cache keys
        self.CACHE_KEYS = {
            'ORDERS': 'orders',
            'MENU_ITEMS': 'menu_items',
            'CATEGORIES': 'categories',
            'TABLES': 'tables',
            'USERS': 'users',
            'INVENTORY': 'inventory',
            'KOT_ITEMS': 'kot_items',
            'REPORTS': 'reports',
            'SETTINGS': 'settings'
        }
    
    def _setup_event_listeners(self):
        """Setup event listeners for data changes"""
        # Listen to all relevant events
        event_dispatcher.subscribe(EventType.ORDER_CREATED, self._on_order_changed)
        event_dispatcher.subscribe(EventType.ORDER_UPDATED, self._on_order_changed)
        event_dispatcher.subscribe(EventType.KOT_STATUS_CHANGED, self._on_kot_changed)
        event_dispatcher.subscribe(EventType.INVENTORY_UPDATED, self._on_inventory_changed)
        event_dispatcher.subscribe(EventType.TABLE_STATUS_CHANGED, self._on_table_changed)
        event_dispatcher.subscribe(EventType.MENU_UPDATED, self._on_menu_item_changed)
        event_dispatcher.subscribe(EventType.PAYMENT_PROCESSED, self._on_order_changed)
    
    def _on_order_changed(self, data):
        """Handle order changes"""
        self.cache.invalidate(self.CACHE_KEYS['ORDERS'])
        self.cache.invalidate(self.CACHE_KEYS['REPORTS'])
    
    def _on_menu_item_changed(self, data):
        """Handle menu item changes"""
        self.cache.invalidate(self.CACHE_KEYS['MENU_ITEMS'])
        self.cache.invalidate(self.CACHE_KEYS['INVENTORY'])
    
    def _on_category_changed(self, data):
        """Handle category changes"""
        self.cache.invalidate(self.CACHE_KEYS['CATEGORIES'])
        self.cache.invalidate(self.CACHE_KEYS['MENU_ITEMS'])
    
    def _on_table_changed(self, data):
        """Handle table changes"""
        self.cache.invalidate(self.CACHE_KEYS['TABLES'])
    
    def _on_inventory_changed(self, data):
        """Handle inventory changes"""
        self.cache.invalidate(self.CACHE_KEYS['INVENTORY'])
    
    def _on_kot_changed(self, data):
        """Handle KOT changes"""
        self.cache.invalidate(self.CACHE_KEYS['KOT_ITEMS'])
    
    def _on_settings_changed(self, data):
        """Handle settings changes"""
        self.cache.invalidate(self.CACHE_KEYS['SETTINGS'])
    
    # Orders Data Management
    def get_orders(self, filter_value: str = "All", search_term: str = "", force_refresh: bool = False) -> List[Dict]:
        """Get orders with caching"""
        cache_key = f"{self.CACHE_KEYS['ORDERS']}_{filter_value}_{search_term}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            orders = self.app.order_model.get_orders(filter_value, search_term)
            formatted_orders = []
            
            for order in orders:
                order_id, order_number, created_at, order_type, table_number, total, status, customer_name = order
                
                formatted_orders.append({
                    'id': order_id,
                    'order_number': order_number,
                    'created_at': created_at,
                    'order_type': order_type,
                    'table_number': table_number,
                    'total': total,
                    'status': status,
                    'customer_name': customer_name
                })
            
            self.cache.set(cache_key, formatted_orders)
            return formatted_orders
            
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []
    
    def get_order_details(self, order_id: int, force_refresh: bool = False) -> Optional[Dict]:
        """Get order details with caching"""
        cache_key = f"{self.CACHE_KEYS['ORDERS']}_details_{order_id}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            details = self.app.order_model.get_details(order_id)
            if details:
                items = self.app.order_model.get_items(order_id)
                payments = self.app.order_model.get_payments(order_id)
                
                order_dict = {
                    'id': order_id,
                    'order_number': details[0],
                    'table_id': details[1],
                    'customer_name': details[2],
                    'customer_mobile': details[3],
                    'order_type': details[4],
                    'subtotal': details[5],
                    'tax': details[6],
                    'discount': details[7],
                    'total': details[8],
                    'created_at': details[9],
                    'status': details[10],
                    'items': items,
                    'payments': payments
                }
                
                self.cache.set(cache_key, order_dict)
                return order_dict
            
            return None
            
        except Exception as e:
            print(f"Error getting order details: {e}")
            return None
    
    # Menu Items Data Management
    def get_menu_items(self, search_term: str = "", category: str = "All", force_refresh: bool = False) -> List[Dict]:
        """Get menu items with caching"""
        cache_key = f"{self.CACHE_KEYS['MENU_ITEMS']}_{search_term}_{category}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            items = self.app.menu_item_model.get_all(search_term, category)
            formatted_items = []
            
            for item in items:
                item_id, name, category_name, price, stock_quantity = item
                
                formatted_items.append({
                    'id': item_id,
                    'name': name,
                    'category_name': category_name,
                    'price': price,
                    'stock_quantity': stock_quantity
                })
            
            self.cache.set(cache_key, formatted_items)
            return formatted_items
            
        except Exception as e:
            print(f"Error getting menu items: {e}")
            return []
    
    def get_categories(self, force_refresh: bool = False) -> List[Dict]:
        """Get categories with caching"""
        if not force_refresh:
            cached_data = self.cache.get(self.CACHE_KEYS['CATEGORIES'])
            if cached_data is not None:
                return cached_data
        
        try:
            categories = self.app.category_model.get_all()
            formatted_categories = []
            
            for category in categories:
                category_id, name = category
                
                formatted_categories.append({
                    'id': category_id,
                    'name': name
                })
            
            self.cache.set(self.CACHE_KEYS['CATEGORIES'], formatted_categories)
            return formatted_categories
            
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
    
    # Tables Data Management
    def get_tables(self, force_refresh: bool = False) -> List[Dict]:
        """Get tables with caching"""
        if not force_refresh:
            cached_data = self.cache.get(self.CACHE_KEYS['TABLES'])
            if cached_data is not None:
                return cached_data
        
        try:
            tables = self.app.table_model.get_all()
            formatted_tables = []
            
            for table in tables:
                table_id, table_number, capacity, status = table
                
                formatted_tables.append({
                    'id': table_id,
                    'table_number': table_number,
                    'capacity': capacity,
                    'status': status
                })
            
            self.cache.set(self.CACHE_KEYS['TABLES'], formatted_tables)
            return formatted_tables
            
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    def get_available_tables(self, force_refresh: bool = False) -> List[Dict]:
        """Get available tables with caching"""
        cache_key = f"{self.CACHE_KEYS['TABLES']}_available"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            tables = self.app.table_model.get_available()
            formatted_tables = []
            
            for table in tables:
                table_id, table_number = table
                
                formatted_tables.append({
                    'id': table_id,
                    'table_number': table_number
                })
            
            self.cache.set(cache_key, formatted_tables)
            return formatted_tables
            
        except Exception as e:
            print(f"Error getting available tables: {e}")
            return []
    
    # Inventory Data Management
    def get_inventory_items(self, search_term: str = "", filter_type: str = "All", force_refresh: bool = False) -> List[Dict]:
        """Get inventory items with caching"""
        cache_key = f"{self.CACHE_KEYS['INVENTORY']}_{search_term}_{filter_type}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            items = self.app.menu_item_model.get_inventory_items(search_term, filter_type)
            formatted_items = []
            
            for item in items:
                item_id, name, category_name, stock_quantity = item
                
                formatted_items.append({
                    'id': item_id,
                    'name': name,
                    'category_name': category_name,
                    'stock_quantity': stock_quantity
                })
            
            self.cache.set(cache_key, formatted_items)
            return formatted_items
            
        except Exception as e:
            print(f"Error getting inventory items: {e}")
            return []
    
    # KOT Data Management
    def get_kot_items(self, status: str = "Pending", force_refresh: bool = False) -> List[Dict]:
        """Get KOT items with caching"""
        cache_key = f"{self.CACHE_KEYS['KOT_ITEMS']}_{status}"
        
        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        try:
            items = self.app.kot_model.get_items(status)
            formatted_items = []
            
            for item in items:
                item_id, order_number, name, quantity, created_at, item_status = item
                
                formatted_items.append({
                    'id': item_id,
                    'order_number': order_number,
                    'name': name,
                    'quantity': quantity,
                    'created_at': created_at,
                    'status': item_status
                })
            
            self.cache.set(cache_key, formatted_items)
            return formatted_items
            
        except Exception as e:
            print(f"Error getting KOT items: {e}")
            return []
    
    # Settings Data Management
    def get_settings(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get settings with caching"""
        if not force_refresh:
            cached_data = self.cache.get(self.CACHE_KEYS['SETTINGS'])
            if cached_data is not None:
                return cached_data
        
        try:
            settings = self.app.settings_model.get_all()
            self.cache.set(self.CACHE_KEYS['SETTINGS'], settings)
            return settings
            
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {}
    
    # Cache Management
    def invalidate_cache(self, data_type: str = None):
        """Invalidate cache for specific data type or all"""
        if data_type:
            self.cache.invalidate(data_type)
        else:
            self.cache.invalidate_all()
    
    def refresh_all_data(self):
        """Refresh all cached data"""
        self.cache.invalidate_all()

# Global data manager instance
_data_manager = None

def get_data_manager(app) -> DataManager:
    """Get or create data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager(app)
    return _data_manager

def init_data_manager(app):
    """Initialize data manager"""
    global _data_manager
    _data_manager = DataManager(app)
    return _data_manager
