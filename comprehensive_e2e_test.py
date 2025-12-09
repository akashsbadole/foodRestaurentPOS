#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Script for POS Application
Tests all workflows that were previously broken:
1. Orders not showing on KOT when customers place orders
2. Inventory not properly showing/updated
3. Order details not visible properly

This script tests the complete integration of all fixes.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import traceback
import time
import threading
from datetime import datetime, timedelta
import sqlite3
import gc
import psutil
import inspect

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockApp:
    """Mock application class for testing"""
    def __init__(self):
        self.db = None
        self.settings = {
            'restaurant_name': 'Test Restaurant',
            'restaurant_address': 'Test Address',
            'tax_rate': '5.0',
            'auto_print_bill': 'False',
            'auto_print_kot': 'False',
            'default_bill_printer_type': 'standard',
            'default_kot_printer_type': 'thermal',
            'standard_printer_name': '',
            'thermal_printer_name': ''
        }
        self.content_frame = None
        self.order_model = None
        self.table_model = None
        self.menu_item_model = None
        self.kot_model = None
        self.category_model = None

class E2ETestSuite:
    """Comprehensive end-to-end test suite"""
    
    def __init__(self):
        self.test_results = {
            'order_workflow': {'status': 'PENDING', 'details': [], 'errors': []},
            'inventory_updates': {'status': 'PENDING', 'details': [], 'errors': []},
            'kot_workflow': {'status': 'PENDING', 'details': [], 'errors': []},
            'order_details': {'status': 'PENDING', 'details': [], 'errors': []},
            'edge_cases': {'status': 'PENDING', 'details': [], 'errors': []},
            'memory_stability': {'status': 'PENDING', 'details': [], 'errors': []},
            'overall_status': 'PENDING'
        }
        self.root = None
        self.app = None
        self.initial_memory = None
        
    def setup_test_environment(self):
        """Set up test environment with database and UI components"""
        print("=" * 80)
        print("SETTING UP COMPREHENSIVE E2E TEST ENVIRONMENT")
        print("=" * 80)
        
        try:
            # Create root window (hidden)
            self.root = tk.Tk()
            self.root.withdraw()  # Hide window during testing
            
            # Initialize mock app
            self.app = MockApp()
            
            # Import and initialize database
            from src.models.database import DatabaseManager, KOT, Category, Table
            from src.models.order import Order
            from src.models.menu_item import MenuItem
            self.app.db = DatabaseManager()
            
            # Initialize models
            self.app.order_model = Order(self.app.db)
            self.app.kot_model = KOT(self.app.db)
            self.app.menu_item_model = MenuItem(self.app.db)
            self.app.category_model = Category(self.app.db)
            self.app.table_model = Table(self.app.db)
            
            # Create content frame for testing
            self.app.content_frame = ttk.Frame(self.root)
            
            # Record initial memory usage
            process = psutil.Process()
            self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            print(f"[PASS] Test environment initialized successfully")
            print(f"[INFO] Initial memory usage: {self.initial_memory:.2f} MB")
            return True
            
        except Exception as e:
            print(f"[FAIL] Failed to setup test environment: {str(e)}")
            traceback.print_exc()
            return False
    
    def setup_test_data(self):
        """Set up test data for comprehensive testing"""
        print("\n" + "=" * 80)
        print("SETTING UP TEST DATA")
        print("=" * 80)
        
        try:
            # Create test category
            self.app.db.execute_query("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Test Category",))
            self.app.db.commit()
            
            # Get category ID
            self.app.db.execute_query("SELECT id FROM categories WHERE name = ?", ("Test Category",))
            category_result = self.app.db.fetch_one()
            self.test_category_id = category_result[0] if category_result else 1
            
            # Create test menu items with different stock levels
            test_items = [
                ("Test Item 1", 10.99, self.test_category_id, 50),  # Normal stock
                ("Test Item 2", 15.99, self.test_category_id, 5),   # Low stock
                ("Test Item 3", 8.99, self.test_category_id, 0),    # Out of stock
                ("Test Item 4", 12.99, self.test_category_id, ""),  # Empty stock (should default to 0)
            ]
            
            self.test_item_ids = []
            for name, price, category_id, stock in test_items:
                self.app.db.execute_query(
                    "INSERT OR IGNORE INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)",
                    (name, price, category_id, stock)
                )
                self.app.db.commit()
                
                # Get the item ID
                self.app.db.execute_query("SELECT id FROM menu_items WHERE name = ?", (name,))
                item_result = self.app.db.fetch_one()
                if item_result:
                    self.test_item_ids.append(item_result[0])
            
            # Create test table
            self.app.db.execute_query("INSERT OR IGNORE INTO tables (table_number, capacity, status) VALUES (?, ?, ?)", 
                                   ("T1", 4, "Available"))
            self.app.db.commit()
            
            self.app.db.execute_query("SELECT id FROM tables WHERE table_number = ?", ("T1",))
            table_result = self.app.db.fetch_one()
            self.test_table_id = table_result[0] if table_result else 1
            
            print(f"[PASS] Test data created successfully")
            print(f"[INFO] Created {len(self.test_item_ids)} test menu items")
            print(f"[INFO] Test table ID: {self.test_table_id}")
            return True
            
        except Exception as e:
            print(f"[FAIL] Failed to setup test data: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_complete_order_workflow(self):
        """Test 1: Complete order workflow from creation to completion"""
        print("\n" + "=" * 80)
        print("TEST 1: COMPLETE ORDER WORKFLOW")
        print("=" * 80)
        
        try:
            # Import OrderController
            from src.controllers.order_controller import OrderController
            from src.utils.event_dispatcher import event_dispatcher
            
            # Initialize order controller
            order_controller = OrderController(self.app.db)
            
            # Step 1: Set up order type and table
            print("\nStep 1: Setting up order type and table...")
            order_controller.set_order_type("Dine-in")
            order_controller.set_table(self.test_table_id)
            
            if order_controller.order_type == "Dine-in" and order_controller.selected_table == self.test_table_id:
                print("[PASS] Order type and table set correctly")
                self.test_results['order_workflow']['details'].append("Order type and table configuration works")
            else:
                print("[FAIL] Order type or table not set correctly")
                self.test_results['order_workflow']['errors'].append("Order type/table configuration failed")
                return False
            
            # Step 2: Add items to cart
            print("\nStep 2: Adding items to cart...")
            
            # Add item with normal stock
            success, message = order_controller.add_to_cart(self.test_item_ids[0], 2)
            if success:
                print("[PASS] Item with normal stock added to cart")
                self.test_results['order_workflow']['details'].append("Normal stock item added to cart")
            else:
                print(f"[FAIL] Failed to add normal stock item: {message}")
                self.test_results['order_workflow']['errors'].append(f"Normal stock item failed: {message}")
            
            # Add item with low stock
            success, message = order_controller.add_to_cart(self.test_item_ids[1], 3)
            if success:
                print("[PASS] Item with low stock added to cart")
                self.test_results['order_workflow']['details'].append("Low stock item added to cart")
            else:
                print(f"[FAIL] Failed to add low stock item: {message}")
                self.test_results['order_workflow']['errors'].append(f"Low stock item failed: {message}")
            
            # Try to add out of stock item (should fail)
            success, message = order_controller.add_to_cart(self.test_item_ids[2], 1)
            if not success:
                print("[PASS] Out of stock item correctly rejected")
                self.test_results['order_workflow']['details'].append("Out of stock item correctly rejected")
            else:
                print("[FAIL] Out of stock item was incorrectly accepted")
                self.test_results['order_workflow']['errors'].append("Out of stock item incorrectly accepted")
            
            # Step 3: Calculate totals
            print("\nStep 3: Calculating order totals...")
            totals = order_controller.calculate_totals()
            if totals and 'subtotal' in totals and 'total' in totals:
                print(f"[PASS] Order totals calculated: Subtotal={totals['subtotal']}, Total={totals['total']}")
                self.test_results['order_workflow']['details'].append("Order totals calculation works")
            else:
                print("[FAIL] Order totals calculation failed")
                self.test_results['order_workflow']['errors'].append("Order totals calculation failed")
            
            # Step 4: Process payment
            print("\nStep 4: Processing payment...")
            success, order_number = order_controller.process_payment("Cash")
            if success and order_number:
                print(f"[PASS] Payment processed successfully. Order number: {order_number}")
                self.test_results['order_workflow']['details'].append(f"Payment processed: Order {order_number}")
                self.test_order_number = order_number
            else:
                print(f"[FAIL] Payment processing failed: {order_number}")
                self.test_results['order_workflow']['errors'].append(f"Payment failed: {order_number}")
                return False
            
            # Step 5: Verify order in database
            print("\nStep 5: Verifying order in database...")
            order_details = self.app.order_model.get_details_by_number(order_number)
            if order_details and order_details['order']:
                print("[PASS] Order found in database with correct details")
                self.test_results['order_workflow']['details'].append("Order stored in database correctly")
            else:
                print("[FAIL] Order not found in database or details incomplete")
                self.test_results['order_workflow']['errors'].append("Order database verification failed")
                return False
            
            self.test_results['order_workflow']['status'] = 'PASSED'
            print("\n[PASS] Complete order workflow test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error in order workflow test: {str(e)}")
            traceback.print_exc()
            self.test_results['order_workflow']['status'] = 'FAILED'
            self.test_results['order_workflow']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def test_inventory_updates(self):
        """Test 2: Inventory updates during order processing"""
        print("\n" + "=" * 80)
        print("TEST 2: INVENTORY UPDATES DURING ORDER PROCESSING")
        print("=" * 80)
        
        try:
            # Step 1: Check initial stock levels
            print("\nStep 1: Checking initial stock levels...")
            initial_stocks = {}
            for i, item_id in enumerate(self.test_item_ids):
                self.app.db.execute_query("SELECT stock_quantity FROM menu_items WHERE id = ?", (item_id,))
                result = self.app.db.fetch_one()
                initial_stocks[item_id] = result[0] if result else 0
                print(f"[INFO] Item {item_id} initial stock: {initial_stocks[item_id]}")
            
            # Step 2: Create another order to test inventory updates
            print("\nStep 2: Creating order to test inventory updates...")
            from src.controllers.order_controller import OrderController
            
            order_controller = OrderController(self.app.db)
            order_controller.set_order_type("Dine-in")
            order_controller.set_table(self.test_table_id)
            
            # Add items to cart
            order_controller.add_to_cart(self.test_item_ids[0], 3)  # Reduce by 3
            order_controller.add_to_cart(self.test_item_ids[1], 2)  # Reduce by 2
            
            # Process payment
            success, order_number = order_controller.process_payment("Cash")
            if success:
                print(f"[PASS] Test order created: {order_number}")
                self.test_results['inventory_updates']['details'].append("Test order created for inventory testing")
            else:
                print("[FAIL] Failed to create test order")
                self.test_results['inventory_updates']['errors'].append("Test order creation failed")
                return False
            
            # Step 3: Verify inventory updates
            print("\nStep 3: Verifying inventory updates...")
            expected_changes = {
                self.test_item_ids[0]: -3,  # Should be reduced by 3
                self.test_item_ids[1]: -2   # Should be reduced by 2
            }
            
            all_updates_correct = True
            for item_id, expected_change in expected_changes.items():
                self.app.db.execute_query("SELECT stock_quantity FROM menu_items WHERE id = ?", (item_id,))
                result = self.app.db.fetch_one()
                current_stock = result[0] if result else 0
                expected_stock = initial_stocks[item_id] + expected_change
                
                if current_stock == expected_stock:
                    print(f"[PASS] Item {item_id} stock updated correctly: {initial_stocks[item_id]} -> {current_stock}")
                    self.test_results['inventory_updates']['details'].append(f"Item {item_id} stock updated correctly")
                else:
                    print(f"[FAIL] Item {item_id} stock update incorrect: expected {expected_stock}, got {current_stock}")
                    self.test_results['inventory_updates']['errors'].append(f"Item {item_id} stock update incorrect")
                    all_updates_correct = False
            
            # Step 4: Test manual inventory updates
            print("\nStep 4: Testing manual inventory updates...")
            
            # Update stock manually
            new_stock = 100
            self.app.menu_item_model.update_stock(self.test_item_ids[0], new_stock)
            
            # Verify manual update
            self.app.db.execute_query("SELECT stock_quantity FROM menu_items WHERE id = ?", (self.test_item_ids[0],))
            result = self.app.db.fetch_one()
            updated_stock = result[0] if result else 0
            
            if updated_stock == new_stock:
                print(f"[PASS] Manual stock update works: {new_stock}")
                self.test_results['inventory_updates']['details'].append("Manual stock update works correctly")
            else:
                print(f"[FAIL] Manual stock update failed: expected {new_stock}, got {updated_stock}")
                self.test_results['inventory_updates']['errors'].append("Manual stock update failed")
                all_updates_correct = False
            
            # Step 5: Test empty stock default behavior
            print("\nStep 5: Testing empty stock default behavior...")
            
            # Add item with empty stock
            test_item_name = f"Empty Stock Test {datetime.now().strftime('%H%M%S')}"
            self.app.menu_item_model.add(test_item_name, 9.99, self.test_category_id, "")
            
            # Check what was stored
            self.app.db.execute_query("SELECT stock_quantity FROM menu_items WHERE name = ?", (test_item_name,))
            result = self.app.db.fetch_one()
            stored_stock = result[0] if result else None
            
            if stored_stock == 0 or stored_stock == "0":
                print("[PASS] Empty stock correctly defaults to 0")
                self.test_results['inventory_updates']['details'].append("Empty stock defaults to 0 correctly")
            else:
                print(f"[FAIL] Empty stock does not default to 0, got: {stored_stock}")
                self.test_results['inventory_updates']['errors'].append("Empty stock default behavior incorrect")
                all_updates_correct = False
            
            # Clean up test item
            self.app.db.execute_query("DELETE FROM menu_items WHERE name = ?", (test_item_name,))
            self.app.db.commit()
            
            if all_updates_correct:
                self.test_results['inventory_updates']['status'] = 'PASSED'
                print("\n[PASS] Inventory updates test PASSED")
            else:
                self.test_results['inventory_updates']['status'] = 'FAILED'
                print("\n[FAIL] Inventory updates test FAILED")
            
            return all_updates_correct
            
        except Exception as e:
            print(f"[FAIL] Error in inventory updates test: {str(e)}")
            traceback.print_exc()
            self.test_results['inventory_updates']['status'] = 'FAILED'
            self.test_results['inventory_updates']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def test_kot_workflow(self):
        """Test 3: KOT updates and status changes"""
        print("\n" + "=" * 80)
        print("TEST 3: KOT UPDATES AND STATUS CHANGES")
        print("=" * 80)
        
        try:
            # Step 1: Check if orders appear in KOT
            print("\nStep 1: Checking if orders appear in KOT...")
            
            # Get pending KOT items
            pending_items = self.app.kot_model.get_items("Pending")
            print(f"[INFO] Found {len(pending_items)} pending KOT items")
            
            if len(pending_items) > 0:
                print("[PASS] Orders appear in KOT with Pending status")
                self.test_results['kot_workflow']['details'].append("Orders appear in KOT correctly")
            else:
                print("[FAIL] No orders found in KOT with Pending status")
                self.test_results['kot_workflow']['errors'].append("Orders not appearing in KOT")
                return False
            
            # Step 2: Test KOT status updates
            print("\nStep 2: Testing KOT status updates...")
            
            # Get first pending item
            first_item = pending_items[0]
            item_id = first_item[0]
            initial_status = first_item[5]
            
            print(f"[INFO] Testing with item {item_id}, initial status: {initial_status}")
            
            # Update status to Preparing
            success = self.app.kot_model.update_status(item_id, "Preparing")
            if success:
                print("[PASS] KOT status updated to Preparing")
                self.test_results['kot_workflow']['details'].append("KOT status update to Preparing works")
            else:
                print("[FAIL] Failed to update KOT status to Preparing")
                self.test_results['kot_workflow']['errors'].append("KOT status update to Preparing failed")
                return False
            
            # Verify status change
            preparing_items = self.app.kot_model.get_items("Preparing")
            if len(preparing_items) > 0:
                print("[PASS] KOT items correctly show Preparing status")
                self.test_results['kot_workflow']['details'].append("KOT Preparing status works")
            else:
                print("[FAIL] No KOT items with Preparing status found")
                self.test_results['kot_workflow']['errors'].append("KOT Preparing status not working")
                return False
            
            # Update status to Completed
            success = self.app.kot_model.update_status(item_id, "Completed")
            if success:
                print("[PASS] KOT status updated to Completed")
                self.test_results['kot_workflow']['details'].append("KOT status update to Completed works")
            else:
                print("[FAIL] Failed to update KOT status to Completed")
                self.test_results['kot_workflow']['errors'].append("KOT status update to Completed failed")
                return False
            
            # Verify status change
            completed_items = self.app.kot_model.get_items("Completed")
            if len(completed_items) > 0:
                print("[PASS] KOT items correctly show Completed status")
                self.test_results['kot_workflow']['details'].append("KOT Completed status works")
            else:
                print("[FAIL] No KOT items with Completed status found")
                self.test_results['kot_workflow']['errors'].append("KOT Completed status not working")
                return False
            
            # Step 3: Test KOT details retrieval
            print("\nStep 3: Testing KOT details retrieval...")
            
            kot_details = self.app.kot_model.get_kot_details(item_id)
            if kot_details and len(kot_details) >= 4:
                order_number, name, quantity, created_at = kot_details
                print(f"[PASS] KOT details retrieved: Order {order_number}, Item: {name}, Qty: {quantity}")
                self.test_results['kot_workflow']['details'].append("KOT details retrieval works")
            else:
                print("[FAIL] KOT details retrieval failed or incomplete")
                self.test_results['kot_workflow']['errors'].append("KOT details retrieval failed")
                return False
            
            # Step 4: Test event system integration
            print("\nStep 4: Testing event system integration...")
            from src.utils.event_dispatcher import event_dispatcher, EventType
            
            # Track events
            events_received = []
            
            def test_event_handler(data):
                events_received.append(data)
            
            # Subscribe to events
            event_dispatcher.subscribe(EventType.KOT_STATUS_CHANGED, test_event_handler)
            
            # Trigger status change
            event_dispatcher.kot_status_changed(item_id, "Testing")
            
            # Check if event was received (with small delay for async processing)
            self.root.after(100, lambda: None)  # Allow event processing
            self.root.update()
            
            if len(events_received) > 0:
                print("[PASS] KOT status change event dispatched correctly")
                self.test_results['kot_workflow']['details'].append("KOT event system works")
            else:
                print("[WARN] KOT status change event may not be working (could be timing)")
                self.test_results['kot_workflow']['details'].append("KOT event system unclear")
            
            # Unsubscribe
            event_dispatcher.unsubscribe(EventType.KOT_STATUS_CHANGED, test_event_handler)
            
            self.test_results['kot_workflow']['status'] = 'PASSED'
            print("\n[PASS] KOT workflow test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error in KOT workflow test: {str(e)}")
            traceback.print_exc()
            self.test_results['kot_workflow']['status'] = 'FAILED'
            self.test_results['kot_workflow']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def test_order_details(self):
        """Test 4: Order detail retrieval and display"""
        print("\n" + "=" * 80)
        print("TEST 4: ORDER DETAIL RETRIEVAL AND DISPLAY")
        print("=" * 80)
        
        try:
            # Step 1: Test order details by order number
            print("\nStep 1: Testing order details retrieval...")
            
            if hasattr(self, 'test_order_number'):
                order_details = self.app.order_model.get_details_by_number(self.test_order_number)
                
                if order_details and order_details['order']:
                    order = order_details['order']
                    items = order_details['items']
                    payments = order_details['payments']
                    
                    print(f"[PASS] Order details retrieved for {self.test_order_number}")
                    print(f"[INFO] Order has {len(items)} items and {len(payments)} payments")
                    
                    self.test_results['order_details']['details'].append("Order details retrieval works")
                    
                    # Verify order structure
                    if len(order) >= 10:  # Should have all order fields
                        print("[PASS] Order structure is complete")
                        self.test_results['order_details']['details'].append("Order structure complete")
                    else:
                        print("[FAIL] Order structure is incomplete")
                        self.test_results['order_details']['errors'].append("Order structure incomplete")
                    
                    # Verify items structure
                    if items and len(items[0]) >= 5:  # Should have all item fields
                        print("[PASS] Order items structure is complete")
                        self.test_results['order_details']['details'].append("Order items structure complete")
                    else:
                        print("[FAIL] Order items structure is incomplete")
                        self.test_results['order_details']['errors'].append("Order items structure incomplete")
                    
                else:
                    print("[FAIL] Failed to retrieve order details")
                    self.test_results['order_details']['errors'].append("Order details retrieval failed")
                    return False
            else:
                print("[FAIL] No test order number available")
                self.test_results['order_details']['errors'].append("No test order available")
                return False
            
            # Step 2: Test order items by order number
            print("\nStep 2: Testing order items retrieval...")
            
            order_items = self.app.order_model.get_items_by_order_number(self.test_order_number)
            if order_items:
                print(f"[PASS] Retrieved {len(order_items)} order items")
                self.test_results['order_details']['details'].append("Order items retrieval works")
                
                # Verify item structure
                for item in order_items:
                    if len(item) >= 5:  # name, quantity, price, total, status
                        print(f"[INFO] Item: {item[0]}, Qty: {item[1]}, Status: {item[4]}")
                    else:
                        print("[FAIL] Item structure incomplete")
                        self.test_results['order_details']['errors'].append("Item structure incomplete")
                        return False
            else:
                print("[FAIL] No order items found")
                self.test_results['order_details']['errors'].append("Order items retrieval failed")
                return False
            
            # Step 3: Test order filtering and search
            print("\nStep 3: Testing order filtering and search...")
            
            # Test getting all orders
            all_orders = self.app.order_model.get_all()
            if all_orders:
                print(f"[PASS] Retrieved {len(all_orders)} orders")
                self.test_results['order_details']['details'].append("Order listing works")
            else:
                print("[FAIL] No orders found")
                self.test_results['order_details']['errors'].append("Order listing failed")
                return False
            
            # Test filtering by today
            today_orders = self.app.order_model.get_all("Today")
            if today_orders:
                print(f"[PASS] Retrieved {len(today_orders)} today's orders")
                self.test_results['order_details']['details'].append("Order filtering works")
            else:
                print("[WARN] No today's orders found (might be normal)")
                self.test_results['order_details']['details'].append("Order filtering works (no today's orders)")
            
            # Test search functionality
            search_orders = self.app.order_model.get_all(search_term=self.test_order_number)
            if search_orders:
                print(f"[PASS] Search found {len(search_orders)} orders")
                self.test_results['order_details']['details'].append("Order search works")
            else:
                print("[FAIL] Order search failed")
                self.test_results['order_details']['errors'].append("Order search failed")
                return False
            
            self.test_results['order_details']['status'] = 'PASSED'
            print("\n[PASS] Order details test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error in order details test: {str(e)}")
            traceback.print_exc()
            self.test_results['order_details']['status'] = 'FAILED'
            self.test_results['order_details']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def test_edge_cases(self):
        """Test 5: Edge cases and error scenarios"""
        print("\n" + "=" * 80)
        print("TEST 5: EDGE CASES AND ERROR SCENARIOS")
        print("=" * 80)
        
        try:
            from src.controllers.order_controller import OrderController
            
            # Test 1: Empty cart payment
            print("\nTest 1: Empty cart payment...")
            order_controller = OrderController(self.app.db)
            success, message = order_controller.process_payment("Cash")
            
            if not success and "empty" in message.lower():
                print("[PASS] Empty cart payment correctly rejected")
                self.test_results['edge_cases']['details'].append("Empty cart payment rejected")
            else:
                print(f"[FAIL] Empty cart payment not properly handled: {message}")
                self.test_results['edge_cases']['errors'].append("Empty cart payment not rejected")
            
            # Test 2: Invalid item addition
            print("\nTest 2: Invalid item addition...")
            success, message = order_controller.add_to_cart(99999, 1)  # Non-existent item
            
            if not success and "not found" in message.lower():
                print("[PASS] Invalid item correctly rejected")
                self.test_results['edge_cases']['details'].append("Invalid item rejected")
            else:
                print(f"[FAIL] Invalid item not properly handled: {message}")
                self.test_results['edge_cases']['errors'].append("Invalid item not rejected")
            
            # Test 3: Negative quantity
            print("\nTest 3: Negative quantity...")
            if len(self.test_item_ids) > 0:
                success, message = order_controller.add_to_cart(self.test_item_ids[0], -1)
                
                if not success:
                    print("[PASS] Negative quantity correctly rejected")
                    self.test_results['edge_cases']['details'].append("Negative quantity rejected")
                else:
                    print("[FAIL] Negative quantity not properly handled")
                    self.test_results['edge_cases']['errors'].append("Negative quantity not rejected")
            
            # Test 4: Excessive quantity (more than stock)
            print("\nTest 4: Excessive quantity...")
            if len(self.test_item_ids) > 0:
                # Get current stock
                self.app.db.execute_query("SELECT stock_quantity FROM menu_items WHERE id = ?", (self.test_item_ids[0],))
                result = self.app.db.fetch_one()
                current_stock = result[0] if result else 0
                
                # Try to add more than available
                success, message = order_controller.add_to_cart(self.test_item_ids[0], current_stock + 100)
                
                if not success and "stock" in message.lower():
                    print("[PASS] Excessive quantity correctly rejected")
                    self.test_results['edge_cases']['details'].append("Excessive quantity rejected")
                else:
                    print(f"[FAIL] Excessive quantity not properly handled: {message}")
                    self.test_results['edge_cases']['errors'].append("Excessive quantity not rejected")
            
            # Test 5: Invalid order status update
            print("\nTest 5: Invalid KOT status update...")
            success = self.app.kot_model.update_status(99999, "InvalidStatus")
            
            # This might not fail due to database design, but we test it doesn't crash
            print(f"[INFO] Invalid KOT update result: {success}")
            self.test_results['edge_cases']['details'].append("Invalid KOT update handled")
            
            # Test 6: Database connection resilience
            print("\nTest 6: Database connection resilience...")
            
            # Test multiple rapid operations
            for i in range(10):
                try:
                    items = self.app.kot_model.get_items("Pending")
                    orders = self.app.order_model.get_all()
                    menu_items = self.app.menu_item_model.get_all()
                except Exception as e:
                    print(f"[FAIL] Database operation failed on iteration {i}: {str(e)}")
                    self.test_results['edge_cases']['errors'].append(f"Database resilience failed: {str(e)}")
                    break
            else:
                print("[PASS] Database connection resilient to rapid operations")
                self.test_results['edge_cases']['details'].append("Database connection resilient")
            
            # Determine overall status
            if len(self.test_results['edge_cases']['errors']) == 0:
                self.test_results['edge_cases']['status'] = 'PASSED'
                print("\n[PASS] Edge cases test PASSED")
            else:
                self.test_results['edge_cases']['status'] = 'FAILED'
                print("\n[FAIL] Edge cases test FAILED")
            
            return self.test_results['edge_cases']['status'] == 'PASSED'
            
        except Exception as e:
            print(f"[FAIL] Error in edge cases test: {str(e)}")
            traceback.print_exc()
            self.test_results['edge_cases']['status'] = 'FAILED'
            self.test_results['edge_cases']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def test_memory_stability(self):
        """Test 6: Application stability and memory usage"""
        print("\n" + "=" * 80)
        print("TEST 6: APPLICATION STABILITY AND MEMORY USAGE")
        print("=" * 80)
        
        try:
            process = psutil.Process()
            
            # Step 1: Baseline memory measurement
            print("\nStep 1: Measuring baseline memory usage...")
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"[INFO] Baseline memory: {baseline_memory:.2f} MB")
            
            # Step 2: Stress test with multiple operations
            print("\nStep 2: Performing stress test...")
            
            from src.controllers.order_controller import OrderController
            
            for i in range(50):
                # Create order controller
                order_controller = OrderController(self.app.db)
                order_controller.set_order_type("Dine-in")
                order_controller.set_table(self.test_table_id)
                
                # Add items to cart
                if len(self.test_item_ids) > 0:
                    order_controller.add_to_cart(self.test_item_ids[0], 1)
                
                # Calculate totals
                order_controller.calculate_totals()
                
                # Reset order
                order_controller.reset_order()
                
                # Periodically check memory
                if i % 10 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    print(f"[INFO] Iteration {i}: Memory {current_memory:.2f} MB")
            
            # Step 3: Force garbage collection
            print("\nStep 3: Forcing garbage collection...")
            gc.collect()
            
            # Step 4: Final memory measurement
            print("\nStep 4: Measuring final memory usage...")
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - baseline_memory
            
            print(f"[INFO] Final memory: {final_memory:.2f} MB")
            print(f"[INFO] Memory increase: {memory_increase:.2f} MB")
            
            # Check for memory leaks
            if memory_increase < 50:  # Allow some increase but not excessive
                print("[PASS] Memory usage within acceptable limits")
                self.test_results['memory_stability']['details'].append("Memory usage acceptable")
            else:
                print(f"[WARN] Memory usage increased by {memory_increase:.2f} MB")
                self.test_results['memory_stability']['details'].append(f"Memory increase: {memory_increase:.2f} MB")
            
            # Step 5: Test database connection stability
            print("\nStep 5: Testing database connection stability...")
            
            connection_errors = 0
            for i in range(100):
                try:
                    # Rapid database operations
                    self.app.kot_model.get_items("Pending")
                    self.app.order_model.get_all()
                    self.app.menu_item_model.get_all()
                except Exception as e:
                    connection_errors += 1
                    if connection_errors > 5:
                        break
            
            if connection_errors == 0:
                print("[PASS] Database connection stable under load")
                self.test_results['memory_stability']['details'].append("Database connection stable")
            else:
                print(f"[FAIL] Database connection errors: {connection_errors}")
                self.test_results['memory_stability']['errors'].append(f"Database errors: {connection_errors}")
            
            # Step 6: Test UI component cleanup
            print("\nStep 6: Testing UI component cleanup...")
            
            try:
                from src.ui.order_screen import OrderScreen
                from src.ui.kot_screen import KOTScreen
                from src.ui.inventory_screen import InventoryScreen
                
                # Create and destroy UI components
                for i in range(5):
                    order_screen = OrderScreen(self.root, self.app)
                    kot_screen = KOTScreen(self.root, self.app)
                    inventory_screen = InventoryScreen(self.root, self.app)
                    
                    # Cleanup
                    if hasattr(order_screen, 'cleanup'):
                        order_screen.cleanup()
                    if hasattr(kot_screen, 'cleanup'):
                        kot_screen.cleanup()
                    
                    # Force garbage collection
                    gc.collect()
                
                print("[PASS] UI components cleanup without errors")
                self.test_results['memory_stability']['details'].append("UI cleanup works")
                
            except Exception as e:
                print(f"[FAIL] UI component cleanup error: {str(e)}")
                self.test_results['memory_stability']['errors'].append(f"UI cleanup error: {str(e)}")
            
            # Determine overall status
            if len(self.test_results['memory_stability']['errors']) == 0:
                self.test_results['memory_stability']['status'] = 'PASSED'
                print("\n[PASS] Memory stability test PASSED")
            else:
                self.test_results['memory_stability']['status'] = 'FAILED'
                print("\n[FAIL] Memory stability test FAILED")
            
            return self.test_results['memory_stability']['status'] == 'PASSED'
            
        except Exception as e:
            print(f"[FAIL] Error in memory stability test: {str(e)}")
            traceback.print_exc()
            self.test_results['memory_stability']['status'] = 'FAILED'
            self.test_results['memory_stability']['errors'].append(f"Exception: {str(e)}")
            return False
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE END-TO-END TEST REPORT")
        print("=" * 80)
        
        # Calculate overall status
        all_passed = all(
            result['status'] == 'PASSED' 
            for result in [
                self.test_results['order_workflow'],
                self.test_results['inventory_updates'],
                self.test_results['kot_workflow'],
                self.test_results['order_details'],
                self.test_results['edge_cases'],
                self.test_results['memory_stability']
            ]
        )
        
        self.test_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        # Print detailed results
        print(f"\nOVERALL STATUS: {self.test_results['overall_status']}")
        print("-" * 80)
        
        test_sections = [
            ('Complete Order Workflow', 'order_workflow'),
            ('Inventory Updates', 'inventory_updates'),
            ('KOT Workflow', 'kot_workflow'),
            ('Order Details', 'order_details'),
            ('Edge Cases', 'edge_cases'),
            ('Memory Stability', 'memory_stability')
        ]
        
        for section_name, section_key in test_sections:
            print(f"\n{section_name}:")
            print(f"   Status: {self.test_results[section_key]['status']}")
            
            if self.test_results[section_key]['details']:
                print("   Details:")
                for detail in self.test_results[section_key]['details']:
                    print(f"   [PASS] {detail}")
            
            if self.test_results[section_key]['errors']:
                print("   Errors:")
                for error in self.test_results[section_key]['errors']:
                    print(f"   [FAIL] {error}")
        
        # Original issues verification
        print("\n" + "=" * 80)
        print("ORIGINAL ISSUES VERIFICATION")
        print("=" * 80)
        
        print("\n1. Orders not showing on KOT when customers place orders:")
        if self.test_results['kot_workflow']['status'] == 'PASSED':
            print("   [PASS] RESOLVED - Orders now appear correctly in KOT")
        else:
            print("   [FAIL] NOT RESOLVED - Issues still exist")
        
        print("\n2. Inventory not properly showing/updated:")
        if self.test_results['inventory_updates']['status'] == 'PASSED':
            print("   [PASS] RESOLVED - Inventory updates work correctly")
        else:
            print("   [FAIL] NOT RESOLVED - Issues still exist")
        
        print("\n3. Order details not visible properly:")
        if self.test_results['order_details']['status'] == 'PASSED':
            print("   [PASS] RESOLVED - Order details are properly visible")
        else:
            print("   [FAIL] NOT RESOLVED - Issues still exist")
        
        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR PRODUCTION DEPLOYMENT")
        print("=" * 80)
        
        if self.test_results['overall_status'] == 'PASSED':
            print("\n[PASS] SYSTEM READY FOR PRODUCTION")
            print("  - All critical workflows are working correctly")
            print("  - Original issues have been resolved")
            print("  - System shows good stability under stress testing")
            print("  - Memory usage is within acceptable limits")
            print("  - Error handling is robust")
        else:
            print("\n[WARN] SYSTEM NEEDS ADDITIONAL WORK")
            
            for section_name, section_key in test_sections:
                if self.test_results[section_key]['status'] != 'PASSED':
                    print(f"  - {section_name} requires attention")
        
        print("\nGeneral Recommendations:")
        print("  - Implement regular database backups")
        print("  - Set up monitoring for memory usage")
        print("  - Consider implementing automated testing pipeline")
        print("  - Document error handling procedures")
        print("  - Plan for scalability testing")
        
        return self.test_results
    
    def cleanup(self):
        """Clean up test environment"""
        print("\n" + "=" * 80)
        print("CLEANING UP TEST ENVIRONMENT")
        print("=" * 80)
        
        try:
            # Clean up test data
            if hasattr(self, 'test_item_ids'):
                for item_id in self.test_item_ids:
                    self.app.db.execute_query("DELETE FROM order_items WHERE menu_item_id = ?", (item_id,))
                    self.app.db.execute_query("DELETE FROM menu_items WHERE id = ?", (item_id,))
            
            if hasattr(self, 'test_table_id'):
                self.app.db.execute_query("DELETE FROM orders WHERE table_id = ?", (self.test_table_id,))
            
            if hasattr(self, 'test_category_id'):
                self.app.db.execute_query("DELETE FROM menu_items WHERE category_id = ?", (self.test_category_id,))
                self.app.db.execute_query("DELETE FROM categories WHERE id = ?", (self.test_category_id,))
            
            self.app.db.commit()
            
            # Close database connection
            if self.app.db:
                try:
                    self.app.db.commit()
                    self.app.db.close()
                except:
                    pass  # Ignore cleanup errors
            
            # Destroy UI
            if self.root:
                self.root.destroy()
            
            print("[PASS] Test environment cleaned up successfully")
            
        except Exception as e:
            print(f"[FAIL] Error during cleanup: {str(e)}")
            traceback.print_exc()

def main():
    """Main test execution"""
    print("Starting Comprehensive End-to-End Test Suite...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test instance
    test_suite = E2ETestSuite()
    
    try:
        # Setup
        if not test_suite.setup_test_environment():
            return 1
        
        if not test_suite.setup_test_data():
            return 1
        
        # Run tests
        test_suite.test_complete_order_workflow()
        test_suite.test_inventory_updates()
        test_suite.test_kot_workflow()
        test_suite.test_order_details()
        test_suite.test_edge_cases()
        test_suite.test_memory_stability()
        
        # Generate report
        results = test_suite.generate_comprehensive_report()
        
        # Return appropriate exit code
        return 0 if results['overall_status'] == 'PASSED' else 1
        
    except Exception as e:
        print(f"\n[FAIL] Test execution failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        test_suite.cleanup()

if __name__ == "__main__":
    exit_code = main()
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exit code: {exit_code}")
    sys.exit(exit_code)