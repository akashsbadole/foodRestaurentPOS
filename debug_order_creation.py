#!/usr/bin/env python3
"""
Debug order creation issue step by step
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.database import DatabaseManager, Order, Table
from models.menu_item import MenuItem
from controllers.order_controller import OrderController
from utils.event_dispatcher import event_dispatcher, EventType

def debug_order_creation():
    """Debug order creation step by step"""
    print("DEBUGGING ORDER CREATION STEP BY STEP")
    print("=" * 60)
    
    # Initialize database
    db = DatabaseManager()
    print(f"Database initialized: {db}")
    
    # Test basic database connection
    try:
        result = db.fetch_one("SELECT 1")
        print(f"Database connection test: {result}")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return
    
    # Initialize models
    order_model = Order(db)
    menu_item_model = MenuItem(db)
    table_model = Table(db)
    print("Models initialized")
    
    # Get menu items
    try:
        menu_items = menu_item_model.get_all()
        print(f"Menu items count: {len(menu_items)}")
        if menu_items:
            print(f"First menu item: {menu_items[0]}")
    except Exception as e:
        print(f"Failed to get menu items: {e}")
        return
    
    # Get tables
    try:
        tables = table_model.get_available()
        print(f"Available tables count: {len(tables)}")
        if tables:
            print(f"First table: {tables[0]}")
    except Exception as e:
        print(f"Failed to get tables: {e}")
        return
    
    # Test order creation with minimal data
    try:
        order_data = {
            'table_id': 1,
            'customer_name': 'Test Customer',
            'customer_mobile': '1234567890',
            'order_type': 'Dine-in',
            'subtotal': 40.0,
            'tax': 2.0,
            'discount': 0.0,
            'total': 42.0,
            'payment_mode': 'Cash',
            'items': [{'id': 1, 'name': 'Test Item', 'price': 40.0, 'quantity': 1, 'total': 40.0}]
        }
        
        print(f"Creating order with data: {order_data}")
        order_id = order_model.create(order_data)
        print(f"Order created with ID: {order_id}")
        
        if order_id:
            # Check if order was actually created
            orders = order_model.get_all()
            print(f"Total orders in database: {len(orders)}")
            
            # Get order details
            order_details = order_model.get_details(order_id)
            print(f"Order details: {order_details}")
        
    except Exception as e:
        print(f"Order creation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test event dispatcher
    try:
        events_received = []
        def test_callback(data):
            events_received.append(data)
            print(f"Event received: {data}")
        
        event_dispatcher.subscribe(EventType.ORDER_CREATED, test_callback)
        event_dispatcher.order_created("TEST-ORDER", {'test': True})
        
        print(f"Events received: {len(events_received)}")
        
    except Exception as e:
        print(f"Event dispatcher test failed: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()

if __name__ == "__main__":
    debug_order_creation()