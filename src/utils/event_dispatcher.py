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
    
    # Support system events
    SUPPORT_TICKET_CREATED = "support_ticket_created"
    SUPPORT_TICKET_UPDATED = "support_ticket_updated"
    SUPPORT_TICKET_ASSIGNED = "support_ticket_assigned"
    SUPPORT_TICKET_CLOSED = "support_ticket_closed"
    BUG_REPORT_CREATED = "bug_report_created"
    BUG_REPORT_UPDATED = "bug_report_updated"
    CONTACT_SUBMISSION_CREATED = "contact_submission_created"
    SUPPORT_CONVERSATION_ADDED = "support_conversation_added"

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
    
    # License system convenience methods
    def license_activated(self, license_key: str, license_type: str, expiry_date: str = None):
        """Convenience method for license activation"""
        self.dispatch(EventType.LICENSE_ACTIVATED, {
            'license_key': license_key,
            'license_type': license_type,
            'expiry_date': expiry_date
        })
    
    def license_deactivated(self, license_key: str, reason: str = None):
        """Convenience method for license deactivation"""
        self.dispatch(EventType.LICENSE_DEACTIVATED, {
            'license_key': license_key,
            'reason': reason
        })
    
    def license_expired(self, license_key: str, license_type: str):
        """Convenience method for license expiration"""
        self.dispatch(EventType.LICENSE_EXPIRED, {
            'license_key': license_key,
            'license_type': license_type
        })
    
    def license_validation_failed(self, license_key: str, error_message: str):
        """Convenience method for license validation failure"""
        self.dispatch(EventType.LICENSE_VALIDATION_FAILED, {
            'license_key': license_key,
            'error_message': error_message
        })
    
    def license_transferred(self, old_key: str, new_key: str, new_hardware_id: str):
        """Convenience method for license transfer"""
        self.dispatch(EventType.LICENSE_TRANSFERRED, {
            'old_key': old_key,
            'new_key': new_key,
            'new_hardware_id': new_hardware_id
        })
    
    def license_upgraded(self, license_key: str, old_type: str, new_type: str):
        """Convenience method for license upgrade"""
        self.dispatch(EventType.LICENSE_UPGRADED, {
            'license_key': license_key,
            'old_type': old_type,
            'new_type': new_type
        })
    
    def trial_started(self, trial_days: int, expiry_date: str):
        """Convenience method for trial start"""
        self.dispatch(EventType.TRIAL_STARTED, {
            'trial_days': trial_days,
            'expiry_date': expiry_date
        })
    
    def trial_expired(self, license_key: str):
        """Convenience method for trial expiration"""
        self.dispatch(EventType.TRIAL_EXPIRED, {
            'license_key': license_key
        })
    
    def feature_access_denied(self, feature: str, license_type: str, required_license: str):
        """Convenience method for feature access denial"""
        self.dispatch(EventType.FEATURE_ACCESS_DENIED, {
            'feature': feature,
            'current_license': license_type,
            'required_license': required_license
        })
    
    # Support system convenience methods
    def support_ticket_created(self, ticket_id: int, ticket_data: dict = None):
        """Convenience method for support ticket creation"""
        self.dispatch(EventType.SUPPORT_TICKET_CREATED, {
            'ticket_id': ticket_id,
            'ticket_data': ticket_data
        })
    
    def support_ticket_updated(self, ticket_id: int, updated_data: dict = None):
        """Convenience method for support ticket updates"""
        self.dispatch(EventType.SUPPORT_TICKET_UPDATED, {
            'ticket_id': ticket_id,
            'updated_data': updated_data
        })
    
    def support_ticket_assigned(self, ticket_id: int, assigned_to: str):
        """Convenience method for support ticket assignment"""
        self.dispatch(EventType.SUPPORT_TICKET_ASSIGNED, {
            'ticket_id': ticket_id,
            'assigned_to': assigned_to
        })
    
    def support_ticket_closed(self, ticket_id: int, resolution: str = None):
        """Convenience method for support ticket closure"""
        self.dispatch(EventType.SUPPORT_TICKET_CLOSED, {
            'ticket_id': ticket_id,
            'resolution': resolution
        })
    
    def bug_report_created(self, bug_id: int, bug_data: dict = None):
        """Convenience method for bug report creation"""
        self.dispatch(EventType.BUG_REPORT_CREATED, {
            'bug_id': bug_id,
            'bug_data': bug_data
        })
    
    def bug_report_updated(self, bug_id: int, updated_data: dict = None):
        """Convenience method for bug report updates"""
        self.dispatch(EventType.BUG_REPORT_UPDATED, {
            'bug_id': bug_id,
            'updated_data': updated_data
        })
    
    def contact_submission_created(self, submission_id: int, contact_data: dict = None):
        """Convenience method for contact submission creation"""
        self.dispatch(EventType.CONTACT_SUBMISSION_CREATED, {
            'submission_id': submission_id,
            'contact_data': contact_data
        })
    
    def support_conversation_added(self, ticket_id: int, conversation_id: int, message_data: dict = None):
        """Convenience method for support conversation messages"""
        self.dispatch(EventType.SUPPORT_CONVERSATION_ADDED, {
            'ticket_id': ticket_id,
            'conversation_id': conversation_id,
            'message_data': message_data
        })

# Global event dispatcher instance
event_dispatcher = EventDispatcher()
