"""
Multi-Order Management System for POS
Handles multiple active orders with switching, management, and isolation
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from src.utils.helpers import generate_order_number


class OrderManager:
    """Manages multiple active orders in the POS system"""
    
    def __init__(self):
        self.active_orders: Dict[str, Dict] = {}  # {order_id: order_data}
        self.current_order_id: Optional[str] = None
        self.order_counter = 0
        # Add order status tracking
        self.order_statuses = {
            'new': 'New',
            'in_progress': 'In Progress',
            'ready': 'Ready for Payment',
            'completed': 'Completed'
        }
        
    def create_new_order(self, order_type: str = "Dine-in") -> str:
        """Create a new order and return its ID"""
        # Generate unique order ID
        order_id = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter}"
        self.order_counter += 1
        
        # Initialize order data
        self.active_orders[order_id] = {
            'order_id': order_id,
            'order_number': generate_order_number(),
            'order_type': order_type,
            'items': [],
            'customer_name': '',
            'customer_mobile': '',
            'table_id': None,
            'subtotal': 0.0,
            'tax': 0.0,
            'discount': 0.0,
            'total': 0.0,
            # GST fields
            'cgst_amount': 0.0,
            'sgst_amount': 0.0,
            'total_tax': 0.0,
            'gst_rate': 5.0,
            'created_at': datetime.now(),
            'last_modified': datetime.now(),
            'status': 'new',  # Use new status system
            'status_display': self.order_statuses['new']
        }
        
        # Set as current order if it's the first one
        if self.current_order_id is None:
            self.current_order_id = order_id
            
        return order_id
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order data by ID"""
        return self.active_orders.get(order_id)
    
    def get_current_order(self) -> Optional[Dict]:
        """Get current active order"""
        if self.current_order_id:
            return self.active_orders.get(self.current_order_id)
        return None
    
    def switch_to_order(self, order_id: str) -> bool:
        """Switch to a different order"""
        if order_id in self.active_orders:
            self.current_order_id = order_id
            self.update_order_timestamp(order_id)
            return True
        return False
    
    def delete_order(self, order_id: str) -> bool:
        """Delete an order"""
        if order_id in self.active_orders:
            del self.active_orders[order_id]
            
            # If deleting current order, switch to another one
            if order_id == self.current_order_id:
                if self.active_orders:
                    self.current_order_id = list(self.active_orders.keys())[0]
                else:
                    self.current_order_id = None
                    
            return True
        return False
    
    def get_all_orders(self) -> List[Dict]:
        """Get all active orders"""
        return list(self.active_orders.values())
    
    def get_order_ids(self) -> List[str]:
        """Get all order IDs"""
        return list(self.active_orders.keys())
    
    def get_orders_summary(self) -> List[Dict]:
        """Get summary of all orders for display"""
        summaries = []
        for order_id, order_data in self.active_orders.items():
            summaries.append({
                'order_id': order_id,
                'order_number': order_data['order_number'],
                'order_type': order_data['order_type'],
                'total': order_data['total'],
                'items_count': len(order_data['items']),
                'customer_name': order_data['customer_name'],
                'created_at': order_data['created_at'],
                'is_current': order_id == self.current_order_id,
                'status': order_data['status'],
                'status_display': order_data.get('status_display', self.order_statuses.get(order_data['status'], 'Unknown'))
            })
        # Sort by creation time, current order first
        summaries.sort(key=lambda x: (not x['is_current'], x['created_at']), reverse=True)
        return summaries
    
    def add_item_to_order(self, order_id: str, item_data: Dict) -> bool:
        """Add item to specific order"""
        
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        
        # Check if item already exists in order
        for existing_item in order['items']:
            if existing_item['menu_item_id'] == item_data['menu_item_id']:
                # Update quantity
                existing_item['quantity'] += item_data['quantity']
                existing_item['total'] = existing_item['price'] * existing_item['quantity']
                self.recalculate_order_totals(order_id)
                self.update_order_timestamp(order_id)
                self.update_order_status(order_id, 'in_progress')
                return True
        
        # Add new item
        order['items'].append(item_data)
        self.recalculate_order_totals(order_id)
        self.update_order_timestamp(order_id)
        self.update_order_status(order_id, 'in_progress')
        return True
    
    def remove_item_from_order(self, order_id: str, item_index: int) -> bool:
        """Remove item from specific order"""
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        if 0 <= item_index < len(order['items']):
            del order['items'][item_index]
            self.recalculate_order_totals(order_id)
            self.update_order_timestamp(order_id)
            return True
        return False
    
    def update_item_quantity(self, order_id: str, item_index: int, new_quantity: int) -> bool:
        """Update item quantity in specific order"""
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        if 0 <= item_index < len(order['items']) and new_quantity > 0:
            order['items'][item_index]['quantity'] = new_quantity
            order['items'][item_index]['total'] = (
                order['items'][item_index]['price'] * new_quantity
            )
            self.recalculate_order_totals(order_id)
            self.update_order_timestamp(order_id)
            return True
        return False
    
    def update_order_info(self, order_id: str, **kwargs) -> bool:
        """Update order information"""
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        allowed_fields = [
            'customer_name', 'customer_mobile', 'table_id',
            'order_type', 'discount'
        ]
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                order[field] = value
                
        self.recalculate_order_totals(order_id)
        self.update_order_timestamp(order_id)
        # Update status based on order completeness
        self._update_order_status_automatically(order_id)
        return True
    
    def recalculate_order_totals(self, order_id: str) -> bool:
        """Recalculate order totals with GST calculations"""
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        order['subtotal'] = sum(item['total'] for item in order['items'])
        
        # GST calculation (5% total: 2.5% CGST + 2.5% SGST)
        gst_rate = 0.05  # 5% total GST
        cgst_rate = 0.025  # 2.5% CGST
        sgst_rate = 0.025  # 2.5% SGST
        
        order['gst_rate'] = gst_rate * 100  # Store as percentage
        order['cgst_amount'] = order['subtotal'] * cgst_rate
        order['sgst_amount'] = order['subtotal'] * sgst_rate
        order['total_tax'] = order['cgst_amount'] + order['sgst_amount']
        order['tax'] = order['total_tax']  # For backward compatibility
        order['total'] = order['subtotal'] + order['total_tax'] - order['discount']
        
        return True
    
    def update_order_timestamp(self, order_id: str) -> bool:
        """Update order last modified timestamp"""
        if order_id in self.active_orders:
            self.active_orders[order_id]['last_modified'] = datetime.now()
            return True
        return False
    
    def clear_order(self, order_id: str) -> bool:
        """Clear all items from order"""
        if order_id not in self.active_orders:
            return False
            
        order = self.active_orders[order_id]
        order['items'] = []
        order['discount'] = 0.0
        self.recalculate_order_totals(order_id)
        self.update_order_timestamp(order_id)
        return True
    
    def get_order_count(self) -> int:
        """Get number of active orders"""
        return len(self.active_orders)
    
    def has_items(self, order_id: str) -> bool:
        """Check if order has items"""
        if order_id in self.active_orders:
            return len(self.active_orders[order_id]['items']) > 0
        return False
    
    def get_total_value_all_orders(self) -> float:
        """Get total value of all active orders"""
        return sum(order['total'] for order in self.active_orders.values())
    
    def complete_order(self, order_id: str) -> Optional[Dict]:
        """Mark order as completed and return order data for saving"""
        if order_id not in self.active_orders:
            return None
            
        order_data = self.active_orders[order_id].copy()
        order_data['status'] = 'completed'
        order_data['completed_at'] = datetime.now()
        
        # Remove from active orders
        del self.active_orders[order_id]
        
        # Switch to another order if this was current
        if order_id == self.current_order_id:
            if self.active_orders:
                self.current_order_id = list(self.active_orders.keys())[0]
            else:
                self.current_order_id = None
                
        return order_data
    
    def validate_order(self, order_id: str) -> Tuple[bool, str]:
        """Validate order for processing"""
        
        if order_id not in self.active_orders:
            return False, "Order not found"
            
        order = self.active_orders[order_id]
        
        if not order['items']:
            return False, "Order has no items"
            
        if order['order_type'] == 'Dine-in' and not order['table_id']:
            return False, "Table selection required for dine-in orders"
            
        if order['order_type'] == 'Takeaway' and not order['customer_name']:
            return False, "Customer name required for takeaway orders"
            
        return True, "Order is valid"
    
    def get_order_for_export(self, order_id: str) -> Optional[Dict]:
        """Get order data formatted for export"""
        if order_id not in self.active_orders:
            return None
            
        order = self.active_orders[order_id]
        
        return {
            'order_number': order['order_number'],
            'order_type': order['order_type'],
            'customer_name': order['customer_name'],
            'customer_mobile': order['customer_mobile'],
            'table_id': order['table_id'],
            'items': order['items'],
            'subtotal': order['subtotal'],
            'tax': order['tax'],
            'cgst_amount': order['cgst_amount'],
            'sgst_amount': order['sgst_amount'],
            'total_tax': order['total_tax'],
            'gst_rate': order['gst_rate'],
            'discount': order['discount'],
            'total': order['total'],
            'created_at': order['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
            'status': order['status'],
            'status_display': order.get('status_display', self.order_statuses.get(order['status'], 'Unknown'))
        }
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        if order_id not in self.active_orders:
            return False
        
        if status in self.order_statuses:
            self.active_orders[order_id]['status'] = status
            self.active_orders[order_id]['status_display'] = self.order_statuses[status]
            self.update_order_timestamp(order_id)
            return True
        return False
    
    def _update_order_status_automatically(self, order_id: str) -> None:
        """Automatically update order status based on order state"""
        if order_id not in self.active_orders:
            return
        
        order = self.active_orders[order_id]
        current_status = order['status']
        
        # Don't downgrade from completed status
        if current_status == 'completed':
            return
        
        # Determine new status based on order content
        if not order['items']:
            new_status = 'new'
        elif order['customer_name'] or order['table_id']:
            new_status = 'ready'  # Ready for payment
        else:
            new_status = 'in_progress'
        
        # Update status if it changed
        if new_status != current_status:
            self.update_order_status(order_id, new_status)
    
    def get_status_color(self, status: str) -> str:
        """Get color for order status"""
        status_colors = {
            'new': '#808080',      # Gray
            'in_progress': '#FFA500',  # Orange
            'ready': '#008000',     # Green
            'completed': '#0000FF'  # Blue
        }
        return status_colors.get(status, '#000000')  # Default black
    
    def backup_order_data(self) -> Dict:
        """Create a backup of all order data"""
        return {
            'active_orders': self.active_orders.copy(),
            'current_order_id': self.current_order_id,
            'order_counter': self.order_counter,
            'timestamp': datetime.now().isoformat()
        }
    
    def restore_order_data(self, backup_data: Dict) -> bool:
        """Restore order data from backup"""
        try:
            self.active_orders = backup_data.get('active_orders', {})
            self.current_order_id = backup_data.get('current_order_id')
            self.order_counter = backup_data.get('order_counter', 0)
            return True
        except Exception:
            return False