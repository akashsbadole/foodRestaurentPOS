"""
Offline Support and Synchronization Manager for Flask POS Application
Provides offline functionality with automatic synchronization when online
"""

import os
import json
import sqlite3
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app, g, jsonify
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OfflineManager:
    """Manages offline operations and synchronization"""
    
    def __init__(self, app=None):
        self.app = app
        self.offline_db_path = 'offline_data.db'
        self.sync_queue = queue.Queue()
        self.is_online = True
        self.sync_thread = None
        self.sync_interval = 30  # seconds
        self.max_retry_attempts = 3
        self.logger = logging.getLogger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize offline manager with Flask app"""
        self.app = app
        self.offline_db_path = os.path.join(app.instance_path, 'offline_data.db')
        
        # Initialize offline database
        self._init_offline_database()
        
        # Start sync thread
        self._start_sync_thread()
        
        # Check online status
        self._check_online_status()
        
        self.logger.info("Offline manager initialized")
    
    def _init_offline_database(self):
        """Initialize offline SQLite database"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            # Create tables for offline data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_id TEXT UNIQUE NOT NULL,
                    order_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    sync_attempts INTEGER DEFAULT 0,
                    last_sync_attempt TEXT,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    local_id TEXT UNIQUE NOT NULL,
                    payment_data TEXT NOT NULL,
                    order_local_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    sync_attempts INTEGER DEFAULT 0,
                    last_sync_attempt TEXT,
                    error_message TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_menu_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER UNIQUE NOT NULL,
                    item_data TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'synced'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER UNIQUE NOT NULL,
                    category_data TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'synced'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS offline_tables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_id INTEGER UNIQUE NOT NULL,
                    table_data TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'synced'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Offline database initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing offline database: {e}")
    
    def _start_sync_thread(self):
        """Start background synchronization thread"""
        if self.sync_thread is None or not self.sync_thread.is_alive():
            self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
            self.sync_thread.start()
            self.logger.info("Sync thread started")
    
    def _sync_worker(self):
        """Background worker for synchronization"""
        while True:
            try:
                if self.is_online:
                    self._process_sync_queue()
                    self._sync_pending_data()
                
                threading.Event().wait(self.sync_interval)
                
            except Exception as e:
                self.logger.error(f"Error in sync worker: {e}")
                threading.Event().wait(60)  # Wait longer on error
    
    def _check_online_status(self):
        """Check if application is online"""
        try:
            # Try to connect to a reliable endpoint
            response = requests.get('https://httpbin.org/get', timeout=5)
            self.is_online = response.status_code == 200
        except Exception:
            self.is_online = False
    
    def _process_sync_queue(self):
        """Process items in sync queue"""
        while not self.sync_queue.empty():
            try:
                item = self.sync_queue.get_nowait()
                self._sync_item(item)
                self.sync_queue.task_done()
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Error processing sync queue item: {e}")
    
    def _sync_item(self, item: Dict[str, Any]):
        """Sync individual item to server"""
        try:
            data_type = item.get('data_type')
            data = item.get('data')
            local_id = item.get('local_id')
            
            if data_type == 'order':
                self._sync_order(data, local_id)
            elif data_type == 'payment':
                self._sync_payment(data, local_id)
            
        except Exception as e:
            self.logger.error(f"Error syncing item {item.get('local_id')}: {e}")
    
    def _sync_order(self, order_data: Dict[str, Any], local_id: str):
        """Sync order to server with conflict resolution"""
        try:
            # Check for conflicts first
            conflict_check = self._check_order_conflicts(order_data)
            
            if conflict_check['has_conflict']:
                # Handle conflict resolution
                resolution = self._resolve_order_conflict(order_data, conflict_check['conflicts'])
                if not resolution['resolved']:
                    self._update_sync_status('offline_orders', local_id, 'conflict',
                                         f"Conflict: {resolution['message']}")
                    self._log_sync_operation('order_sync', 'order', local_id, 'conflict',
                                         resolution['message'])
                    return
                order_data = resolution['resolved_data']
            
            # Make API call to sync order
            response = self._make_api_request('/api/orders/sync', 'POST', order_data)
            
            if response and response.get('success'):
                self._update_sync_status('offline_orders', local_id, 'synced')
                self._log_sync_operation('order_sync', 'order', local_id, 'success')
                self._notify_sync_status_update('order', local_id, 'synced')
            else:
                self._update_sync_status('offline_orders', local_id, 'failed',
                                     response.get('message', 'Unknown error'))
                self._log_sync_operation('order_sync', 'order', local_id, 'failed',
                                     response.get('message', 'Unknown error'))
                self._notify_sync_status_update('order', local_id, 'failed',
                                             response.get('message', 'Unknown error'))
        
        except Exception as e:
            self._update_sync_status('offline_orders', local_id, 'failed', str(e))
            self._log_sync_operation('order_sync', 'order', local_id, 'failed', str(e))
            self._notify_sync_status_update('order', local_id, 'failed', str(e))
    
    def _sync_payment(self, payment_data: Dict[str, Any], local_id: str):
        """Sync payment to server"""
        try:
            # Make API call to sync payment
            response = self._make_api_request('/api/payments/sync', 'POST', payment_data)
            
            if response and response.get('success'):
                self._update_sync_status('offline_payments', local_id, 'synced')
                self._log_sync_operation('payment_sync', 'payment', local_id, 'success')
            else:
                self._update_sync_status('offline_payments', local_id, 'failed', 
                                     response.get('message', 'Unknown error'))
                self._log_sync_operation('payment_sync', 'payment', local_id, 'failed', 
                                     response.get('message', 'Unknown error'))
        
        except Exception as e:
            self._update_sync_status('offline_payments', local_id, 'failed', str(e))
            self._log_sync_operation('payment_sync', 'payment', local_id, 'failed', str(e))
    
    def _make_api_request(self, endpoint: str, method: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make API request with retry logic"""
        try:
            # Setup session with retry strategy
            session = requests.Session()
            retry_strategy = Retry(
                total=self.max_retry_attempts,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # Make request
            base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
            url = f"{base_url}{endpoint}"
            
            if method == 'POST':
                response = session.post(url, json=data, timeout=10)
            else:
                response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"API request failed: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None
    
    def _sync_pending_data(self):
        """Sync all pending offline data"""
        try:
            # Sync pending orders
            self._sync_pending_orders()
            
            # Sync pending payments
            self._sync_pending_payments()
            
            # Update cached data
            self._update_cached_data()
            
        except Exception as e:
            self.logger.error(f"Error syncing pending data: {e}")
    
    def _sync_pending_orders(self):
        """Sync all pending orders"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT local_id, order_data, sync_attempts 
                FROM offline_orders 
                WHERE sync_status = 'pending' AND sync_attempts < ?
            ''', (self.max_retry_attempts,))
            
            pending_orders = cursor.fetchall()
            
            for local_id, order_data, sync_attempts in pending_orders:
                order_dict = json.loads(order_data)
                
                # Check if order should be retried
                if sync_attempts >= self.max_retry_attempts:
                    self._update_sync_status('offline_orders', local_id, 'failed', 'Max retry attempts reached')
                    continue
                
                # Increment sync attempts
                cursor.execute('''
                    UPDATE offline_orders 
                    SET sync_attempts = sync_attempts + 1, last_sync_attempt = ?
                    WHERE local_id = ?
                ''', (datetime.utcnow().isoformat(), local_id))
                
                # Add to sync queue
                self.sync_queue.put({
                    'data_type': 'order',
                    'data': order_dict,
                    'local_id': local_id
                })
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error syncing pending orders: {e}")
    
    def _sync_pending_payments(self):
        """Sync all pending payments"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT local_id, payment_data, sync_attempts 
                FROM offline_payments 
                WHERE sync_status = 'pending' AND sync_attempts < ?
            ''', (self.max_retry_attempts,))
            
            pending_payments = cursor.fetchall()
            
            for local_id, payment_data, sync_attempts in pending_payments:
                payment_dict = json.loads(payment_data)
                
                # Check if payment should be retried
                if sync_attempts >= self.max_retry_attempts:
                    self._update_sync_status('offline_payments', local_id, 'failed', 'Max retry attempts reached')
                    continue
                
                # Increment sync attempts
                cursor.execute('''
                    UPDATE offline_payments 
                    SET sync_attempts = sync_attempts + 1, last_sync_attempt = ?
                    WHERE local_id = ?
                ''', (datetime.utcnow().isoformat(), local_id))
                
                # Add to sync queue
                self.sync_queue.put({
                    'data_type': 'payment',
                    'data': payment_dict,
                    'local_id': local_id
                })
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error syncing pending payments: {e}")
    
    def _update_cached_data(self):
        """Update cached menu items, categories, and tables"""
        try:
            # Get latest data from server
            menu_items = self._make_api_request('/api/menu/items', 'GET', {})
            categories = self._make_api_request('/api/categories', 'GET', {})
            tables = self._make_api_request('/api/tables', 'GET', {})
            
            # Update offline cache
            if menu_items and menu_items.get('success'):
                self._cache_menu_items(menu_items['data'])
            
            if categories and categories.get('success'):
                self._cache_categories(categories['data'])
            
            if tables and tables.get('success'):
                self._cache_tables(tables['data'])
            
        except Exception as e:
            self.logger.error(f"Error updating cached data: {e}")
    
    def _cache_menu_items(self, items: List[Dict[str, Any]]):
        """Cache menu items locally"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            for item in items:
                cursor.execute('''
                    INSERT OR REPLACE INTO offline_menu_items 
                    (item_id, item_data, last_updated, sync_status)
                    VALUES (?, ?, ?, ?)
                ''', (item['id'], json.dumps(item), datetime.utcnow().isoformat(), 'synced'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching menu items: {e}")
    
    def _cache_categories(self, categories: List[Dict[str, Any]]):
        """Cache categories locally"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            for category in categories:
                cursor.execute('''
                    INSERT OR REPLACE INTO offline_categories 
                    (category_id, category_data, last_updated, sync_status)
                    VALUES (?, ?, ?, ?)
                ''', (category['id'], json.dumps(category), datetime.utcnow().isoformat(), 'synced'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching categories: {e}")
    
    def _cache_tables(self, tables: List[Dict[str, Any]]):
        """Cache tables locally"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            for table in tables:
                cursor.execute('''
                    INSERT OR REPLACE INTO offline_tables 
                    (table_id, table_data, last_updated, sync_status)
                    VALUES (?, ?, ?, ?)
                ''', (table['id'], json.dumps(table), datetime.utcnow().isoformat(), 'synced'))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error caching tables: {e}")
    
    def _update_sync_status(self, table: str, local_id: str, status: str, error_message: str = None):
        """Update sync status of an item"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute(f'''
                UPDATE {table} 
                SET sync_status = ?, last_sync_attempt = ?, error_message = ?
                WHERE local_id = ?
            ''', (status, datetime.utcnow().isoformat(), error_message, local_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating sync status: {e}")
    
    def _log_sync_operation(self, operation: str, data_type: str, data_id: str, 
                           status: str, error_message: str = None):
        """Log synchronization operation"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_log 
                (operation, data_type, data_id, status, timestamp, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (operation, data_type, data_id, status, datetime.utcnow().isoformat(), error_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error logging sync operation: {e}")
    
    # Public API methods
    
    def store_order_offline(self, order_data: Dict[str, Any]) -> str:
        """Store order for offline synchronization"""
        try:
            local_id = f"order_{datetime.utcnow().timestamp()}_{hash(json.dumps(order_data))}"
            
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO offline_orders 
                (local_id, order_data, created_at, sync_status)
                VALUES (?, ?, ?, ?)
            ''', (local_id, json.dumps(order_data), datetime.utcnow().isoformat(), 'pending'))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Order stored offline with local_id: {local_id}")
            return local_id
            
        except Exception as e:
            self.logger.error(f"Error storing order offline: {e}")
            raise
    
    def store_payment_offline(self, payment_data: Dict[str, Any], order_local_id: str) -> str:
        """Store payment for offline synchronization"""
        try:
            local_id = f"payment_{datetime.utcnow().timestamp()}_{hash(json.dumps(payment_data))}"
            
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO offline_payments 
                (local_id, payment_data, order_local_id, created_at, sync_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (local_id, json.dumps(payment_data), order_local_id, datetime.utcnow().isoformat(), 'pending'))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Payment stored offline with local_id: {local_id}")
            return local_id
            
        except Exception as e:
            self.logger.error(f"Error storing payment offline: {e}")
            raise
    
    def get_cached_menu_items(self) -> List[Dict[str, Any]]:
        """Get cached menu items"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT item_data FROM offline_menu_items WHERE sync_status = "synced"')
            items = [json.loads(row[0]) for row in cursor.fetchall()]
            
            conn.close()
            return items
            
        except Exception as e:
            self.logger.error(f"Error getting cached menu items: {e}")
            return []
    
    def get_cached_categories(self) -> List[Dict[str, Any]]:
        """Get cached categories"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT category_data FROM offline_categories WHERE sync_status = "synced"')
            categories = [json.loads(row[0]) for row in cursor.fetchall()]
            
            conn.close()
            return categories
            
        except Exception as e:
            self.logger.error(f"Error getting cached categories: {e}")
            return []
    
    def get_cached_tables(self) -> List[Dict[str, Any]]:
        """Get cached tables"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT table_data FROM offline_tables WHERE sync_status = "synced"')
            tables = [json.loads(row[0]) for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            self.logger.error(f"Error getting cached tables: {e}")
            return []
    
    def get_offline_orders(self) -> List[Dict[str, Any]]:
        """Get all offline orders"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT local_id, order_data, created_at, sync_status FROM offline_orders ORDER BY created_at DESC')
            orders = []
            
            for row in cursor.fetchall():
                order_data = json.loads(row[1])
                order_data['local_id'] = row[0]
                order_data['created_at'] = row[2]
                order_data['sync_status'] = row[3]
                orders.append(order_data)
            
            conn.close()
            return orders
            
        except Exception as e:
            self.logger.error(f"Error getting offline orders: {e}")
            return []
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            # Get counts
            cursor.execute('SELECT COUNT(*) FROM offline_orders WHERE sync_status = "pending"')
            pending_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM offline_payments WHERE sync_status = "pending"')
            pending_payments = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM offline_orders WHERE sync_status = "failed"')
            failed_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM offline_payments WHERE sync_status = "failed"')
            failed_payments = cursor.fetchone()[0]
            
            # Get last sync time
            cursor.execute('SELECT MAX(timestamp) FROM sync_log WHERE status = "success"')
            last_sync = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'is_online': self.is_online,
                'pending_orders': pending_orders,
                'pending_payments': pending_payments,
                'failed_orders': failed_orders,
                'failed_payments': failed_payments,
                'last_sync': last_sync,
                'sync_queue_size': self.sync_queue.qsize()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return {
                'is_online': self.is_online,
                'error': str(e)
            }
    
    def force_sync(self) -> bool:
        """Force immediate synchronization"""
        try:
            self._check_online_status()
            if self.is_online:
                self._sync_pending_data()
                self._process_sync_queue()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error forcing sync: {e}")
            return False
    
    def clear_failed_items(self) -> bool:
        """Clear failed synchronization items"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM offline_orders WHERE sync_status = "failed"')
            cursor.execute('DELETE FROM offline_payments WHERE sync_status = "failed"')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Failed synchronization items cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing failed items: {e}")
            return False
    
    def _check_order_conflicts(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for order conflicts with server data"""
        try:
            # Check if order already exists on server
            order_id = order_data.get('order_id')
            if not order_id:
                return {'has_conflict': False}
            
            # Get server order data
            response = self._make_api_request(f'/api/orders/{order_id}', 'GET', {})
            
            if response and response.get('success'):
                server_order = response.get('data')
                conflicts = []
                
                # Check for conflicts in key fields
                if server_order.get('status') != order_data.get('status'):
                    conflicts.append({
                        'field': 'status',
                        'server_value': server_order.get('status'),
                        'local_value': order_data.get('status')
                    })
                
                if server_order.get('total_amount') != order_data.get('total_amount'):
                    conflicts.append({
                        'field': 'total_amount',
                        'server_value': server_order.get('total_amount'),
                        'local_value': order_data.get('total_amount')
                    })
                
                # Check payment status conflicts
                server_payments = server_order.get('payments', [])
                local_payments = order_data.get('payments', [])
                
                if len(server_payments) != len(local_payments):
                    conflicts.append({
                        'field': 'payments',
                        'server_value': f"{len(server_payments)} payments",
                        'local_value': f"{len(local_payments)} payments"
                    })
                
                return {
                    'has_conflict': len(conflicts) > 0,
                    'conflicts': conflicts,
                    'server_data': server_order
                }
            
            return {'has_conflict': False}
            
        except Exception as e:
            self.logger.error(f"Error checking order conflicts: {e}")
            return {'has_conflict': False}
    
    def _resolve_order_conflict(self, local_order: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve order conflicts using intelligent strategies"""
        try:
            resolution_strategy = current_app.config.get('CONFLICT_RESOLUTION_STRATEGY', 'server_wins')
            
            if resolution_strategy == 'server_wins':
                # Server data takes precedence
                return {
                    'resolved': True,
                    'resolved_data': local_order,  # Keep local for now, server will update
                    'message': 'Server data will be used'
                }
            
            elif resolution_strategy == 'local_wins':
                # Local data takes precedence
                return {
                    'resolved': True,
                    'resolved_data': local_order,
                    'message': 'Local data will be used'
                }
            
            elif resolution_strategy == 'merge':
                # Intelligent merge
                resolved_data = local_order.copy()
                
                # For each conflict, apply intelligent resolution
                for conflict in conflicts:
                    field = conflict['field']
                    
                    if field == 'status':
                        # Use the most recent status
                        server_status = conflict['server_value']
                        local_status = conflict['local_value']
                        
                        # Priority order: completed > cancelled > pending > preparing
                        status_priority = {
                            'completed': 4,
                            'cancelled': 3,
                            'pending': 2,
                            'preparing': 1
                        }
                        
                        if status_priority.get(server_status, 0) > status_priority.get(local_status, 0):
                            resolved_data[field] = server_status
                        else:
                            resolved_data[field] = local_status
                    
                    elif field == 'total_amount':
                        # Use the higher amount (for safety)
                        server_amount = float(conflict['server_value'])
                        local_amount = float(conflict['local_value'])
                        resolved_data[field] = max(server_amount, local_amount)
                    
                    elif field == 'payments':
                        # Merge payment data
                        # This would require more complex logic in a real implementation
                        pass
                
                return {
                    'resolved': True,
                    'resolved_data': resolved_data,
                    'message': 'Conflicts resolved with intelligent merge'
                }
            
            else:
                return {
                    'resolved': False,
                    'message': f'Unknown conflict resolution strategy: {resolution_strategy}'
                }
                
        except Exception as e:
            self.logger.error(f"Error resolving order conflict: {e}")
            return {
                'resolved': False,
                'message': f'Error resolving conflict: {str(e)}'
            }
    
    def _notify_sync_status_update(self, data_type: str, local_id: str, status: str, error_message: str = None):
        """Notify clients of sync status updates via WebSocket or Server-Sent Events"""
        try:
            # This would integrate with WebSocket or SSE implementation
            # For now, we'll just log the notification
            notification = {
                'type': 'sync_status_update',
                'data_type': data_type,
                'local_id': local_id,
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
                'error_message': error_message
            }
            
            # Store notification for real-time updates
            self._store_realtime_notification(notification)
            
            self.logger.info(f"Sync status notification: {notification}")
            
        except Exception as e:
            self.logger.error(f"Error sending sync status notification: {e}")
    
    def _store_realtime_notification(self, notification: Dict[str, Any]):
        """Store notification for real-time client updates"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            # Create notifications table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS realtime_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    delivered BOOLEAN DEFAULT FALSE
                )
            ''')
            
            # Store notification
            cursor.execute('''
                INSERT INTO realtime_notifications
                (notification_data, created_at, delivered)
                VALUES (?, ?, ?)
            ''', (json.dumps(notification), datetime.utcnow().isoformat(), False))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error storing realtime notification: {e}")
    
    def get_realtime_notifications(self, since: str = None) -> List[Dict[str, Any]]:
        """Get realtime notifications for client updates"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            if since:
                cursor.execute('''
                    SELECT notification_data, created_at
                    FROM realtime_notifications
                    WHERE created_at > ? AND delivered = FALSE
                    ORDER BY created_at ASC
                ''', (since,))
            else:
                cursor.execute('''
                    SELECT notification_data, created_at
                    FROM realtime_notifications
                    WHERE delivered = FALSE
                    ORDER BY created_at ASC
                ''')
            
            notifications = []
            for row in cursor.fetchall():
                notification = json.loads(row[0])
                notification['created_at'] = row[1]
                notifications.append(notification)
            
            # Mark notifications as delivered
            if notifications:
                cursor.execute('''
                    UPDATE realtime_notifications
                    SET delivered = TRUE
                    WHERE delivered = FALSE
                ''')
                conn.commit()
            
            conn.close()
            return notifications
            
        except Exception as e:
            self.logger.error(f"Error getting realtime notifications: {e}")
            return []
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get detailed synchronization statistics"""
        try:
            conn = sqlite3.connect(self.offline_db_path)
            cursor = conn.cursor()
            
            # Get detailed sync statistics
            stats = {}
            
            # Order statistics
            cursor.execute('''
                SELECT sync_status, COUNT(*)
                FROM offline_orders
                GROUP BY sync_status
            ''')
            order_stats = dict(cursor.fetchall())
            stats['orders'] = order_stats
            
            # Payment statistics
            cursor.execute('''
                SELECT sync_status, COUNT(*)
                FROM offline_payments
                GROUP BY sync_status
            ''')
            payment_stats = dict(cursor.fetchall())
            stats['payments'] = payment_stats
            
            # Recent sync activity
            cursor.execute('''
                SELECT operation, COUNT(*)
                FROM sync_log
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY operation
            ''')
            recent_activity = dict(cursor.fetchall())
            stats['recent_activity'] = recent_activity
            
            # Average sync time
            cursor.execute('''
                SELECT AVG(
                    (julianday(timestamp) - julianday(
                        (SELECT timestamp FROM sync_log s2
                         WHERE s2.data_id = sync_log.data_id
                         AND s2.operation = 'sync_started'
                         AND s2.timestamp < sync_log.timestamp
                         ORDER BY s2.timestamp DESC LIMIT 1)
                    )) * 24 * 60 * 60
                ) as avg_sync_time
                FROM sync_log
                WHERE operation = 'sync_completed'
                AND timestamp > datetime('now', '-24 hours')
            ''')
            avg_sync_time = cursor.fetchone()[0]
            stats['average_sync_time_seconds'] = avg_sync_time if avg_sync_time else 0
            
            conn.close()
            
            # Add current status
            stats.update({
                'is_online': self.is_online,
                'sync_queue_size': self.sync_queue.qsize(),
                'last_updated': datetime.utcnow().isoformat()
            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting sync statistics: {e}")
            return {'error': str(e)}

# Global offline manager instance
offline_manager = OfflineManager()

# Decorators for offline functionality
def offline_capable(f):
    """Decorator to make function work offline"""
    def decorated_function(*args, **kwargs):
        g.offline_mode = not offline_manager.is_online
        return f(*args, **kwargs)
    return decorated_function

def require_online(f):
    """Decorator to require online connection"""
    def decorated_function(*args, **kwargs):
        if not offline_manager.is_online:
            return jsonify({
                'success': False,
                'message': 'This feature requires an internet connection',
                'offline_mode': True
            }), 503
        return f(*args, **kwargs)
    return decorated_function

# Utility functions
def is_online() -> bool:
    """Check if application is online"""
    return offline_manager.is_online

def store_offline_order(order_data: Dict[str, Any]) -> str:
    """Store order for offline synchronization"""
    return offline_manager.store_order_offline(order_data)

def store_offline_payment(payment_data: Dict[str, Any], order_local_id: str) -> str:
    """Store payment for offline synchronization"""
    return offline_manager.store_payment_offline(payment_data, order_local_id)

def get_cached_data() -> Dict[str, List[Dict[str, Any]]]:
    """Get all cached data"""
    return {
        'menu_items': offline_manager.get_cached_menu_items(),
        'categories': offline_manager.get_cached_categories(),
        'tables': offline_manager.get_cached_tables()
    }

def get_sync_status() -> Dict[str, Any]:
    """Get synchronization status"""
    return offline_manager.get_sync_status()

def force_sync() -> bool:
    """Force immediate synchronization"""
    return offline_manager.force_sync()

def get_realtime_notifications(since: str = None) -> List[Dict[str, Any]]:
    """Get realtime notifications for client updates"""
    return offline_manager.get_realtime_notifications(since)

def get_sync_statistics() -> Dict[str, Any]:
    """Get detailed synchronization statistics"""
    return offline_manager.get_sync_statistics()

def check_conflicts(data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Check for conflicts with server data"""
    if data_type == 'order':
        return offline_manager._check_order_conflicts(data)
    return {'has_conflict': False}

def resolve_conflicts(data_type: str, local_data: Dict[str, Any], conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resolve conflicts using intelligent strategies"""
    if data_type == 'order':
        return offline_manager._resolve_order_conflict(local_data, conflicts)
    return {'resolved': False, 'message': 'Conflict resolution not supported for this data type'}