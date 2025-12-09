"""
Event Dispatcher System for Real-time UI Updates
Provides centralized event handling for POS application
"""

import tkinter as tk
from typing import Dict, List, Callable, Any
from enum import Enum

class EventType(Enum):
    """Event types for the POS system"""
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    KOT_STATUS_CHANGED = "kot_status_changed"
    INVENTORY_UPDATED = "inventory_updated"
    TABLE_STATUS_CHANGED = "table_status_changed"
    MENU_UPDATED = "menu_updated"
    PAYMENT_PROCESSED = "payment_processed"

class EventDispatcher:
    """Centralized event dispatcher for real-time updates"""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._root = None
    
    def set_tk_root(self, root):
        """Set the tkinter root for thread-safe operations"""
        self._root = root
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        event_name = event_type.value
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        event_name = event_type.value
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    def dispatch(self, event_type: EventType, data: Any = None):
        """Dispatch an event to all subscribers"""
        event_name = event_type.value
        if event_name in self._listeners:
            # Thread-safe execution using tkinter's after method
            if self._root:
                self._root.after(0, lambda: self._execute_callbacks(event_name, data))
            else:
                self._execute_callbacks(event_name, data)
    
    def _execute_callbacks(self, event_name: str, data: Any):
        """Execute all callbacks for an event"""
        try:
            for callback in self._listeners[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Error in event callback: {e}")
        except KeyError:
            pass  # No listeners for this event
    
    def order_created(self, order_number: str, order_data: dict = None):
        """Convenience method for order creation events"""
        self.dispatch(EventType.ORDER_CREATED, {
            'order_number': order_number,
            'order_data': order_data
        })
    
    def kot_status_changed(self, item_id: int, new_status: str):
        """Convenience method for KOT status changes"""
        self.dispatch(EventType.KOT_STATUS_CHANGED, {
            'item_id': item_id,
            'status': new_status
        })
    
    def inventory_updated(self, item_id: int, new_quantity: int):
        """Convenience method for inventory updates"""
        self.dispatch(EventType.INVENTORY_UPDATED, {
            'item_id': item_id,
            'quantity': new_quantity
        })
    
    def table_status_changed(self, table_id: int, new_status: str):
        """Convenience method for table status changes"""
        self.dispatch(EventType.TABLE_STATUS_CHANGED, {
            'table_id': table_id,
            'status': new_status
        })
    
    def payment_processed(self, order_number: str, payment_data: dict = None):
        """Convenience method for payment processing"""
        self.dispatch(EventType.PAYMENT_PROCESSED, {
            'order_number': order_number,
            'payment_data': payment_data
        })

# Global event dispatcher instance
event_dispatcher = EventDispatcher()
