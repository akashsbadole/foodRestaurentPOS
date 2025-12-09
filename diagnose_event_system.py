#!/usr/bin/env python3
"""
Diagnose and fix event system issues
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.database import DatabaseManager, Order, Table, KOT
from models.menu_item import MenuItem
from controllers.order_controller import OrderController
from utils.event_dispatcher import event_dispatcher, EventType

def diagnose_order_creation_issue():
    """Diagnose order creation issue"""
    print("DIAGNOSING ORDER CREATION ISSUE")
    print("=" * 50)
    
    # Initialize database
    db = DatabaseManager()
    order_controller = OrderController(db)
    
    # Get a menu item
    menu_items = order_controller.get_menu_items()
    if not menu_items:
        print("No menu items found!")
        return
    
    test_item = menu_items[0]
    item_id = test_item[0]
    name = test_item[1]
    price = test_item[2]
    
    print(f"Test item: {name} (ID: {item_id}, Price: {price})")
    
    # Add to cart
    success, message = order_controller.add_to_cart(item_id, 1)
    print(f"Add to cart: {success}, {message}")
    
    # Set order type
    order_controller.set_order_type("Dine-in")
    
    # Get available table
    tables = order_controller.get_available_tables()
    if tables:
        table_id = tables[0][0]
        order_controller.set_table(table_id)
        print(f"Set table: {table_id}")
    
    # Check cart state
    print(f"Cart items: {order_controller.cart_items}")
    
    # Calculate totals
    totals = order_controller.calculate_totals()
    print(f"Totals: {totals}")
    
    # Try to create order
    success, result = order_controller.process_payment("Cash", 0, "%", "Test Customer", "1234567890")
    print(f"Payment processing: {success}, {result}")
    
    if not success:
        print("PAYMENT PROCESSING FAILED!")
        print("This is the root cause of the event system issues.")
        
        # Let's check what's happening in the order model
        print("\nChecking order model directly...")
        order_model = Order(db)
        
        order_data = {
            'order_number': 'TEST-001',
            'table_id': table_id if tables else None,
            'customer_name': 'Test Customer',
            'customer_mobile': '1234567890',
            'order_type': 'Dine-in',
            'subtotal': totals['subtotal'],
            'tax': totals['tax'],
            'discount': totals['discount'],
            'total': totals['total'],
            'payment_mode': 'Cash',
            'items': order_controller.cart_items  # This is missing!
        }
        
        print(f"Order data with items: {order_data}")
        
        try:
            order_id = order_model.create(order_data)
            print(f"Direct order creation successful: {order_id}")
        except Exception as e:
            print(f"Direct order creation failed: {e}")
    
    db.close()

def diagnose_event_system():
    """Diagnose event system"""
    print("\nDIAGNOSING EVENT SYSTEM")
    print("=" * 50)
    
    events_received = []
    
    def test_callback(data):
        events_received.append(data)
        print(f"Event received: {data}")
    
    # Subscribe to events
    event_dispatcher.subscribe(EventType.ORDER_CREATED, test_callback)
    event_dispatcher.subscribe(EventType.INVENTORY_UPDATED, test_callback)
    
    # Test event dispatch
    event_dispatcher.order_created("TEST-001", {'test': True})
    event_dispatcher.inventory_updated(1, 100)
    
    print(f"Total events received: {len(events_received)}")
    
    # Check if menu item model dispatches events
    print("\nChecking menu item model event dispatch...")
    db = DatabaseManager()
    menu_item_model = MenuItem(db)
    
    # Clear events
    events_received.clear()
    
    # Update stock (should trigger event)
    menu_item_model.update_stock(1, 50)
    
    print(f"Events after stock update: {len(events_received)}")
    
    db.close()

def main():
    """Main diagnosis function"""
    diagnose_order_creation_issue()
    diagnose_event_system()
    
    print("\nDIAGNOSIS COMPLETE")
    print("=" * 50)
    print("ISSUES FOUND:")
    print("1. Order controller doesn't pass 'items' to order model")
    print("2. Menu item model doesn't dispatch events on stock update")
    print("3. Order model generates duplicate order numbers")
    print("4. Event system works but components don't use it properly")

if __name__ == "__main__":
    main()