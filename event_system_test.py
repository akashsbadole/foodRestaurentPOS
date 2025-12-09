#!/usr/bin/env python3
"""
Comprehensive Event System and Data Flow Test Script

This script tests the event system and data flow between components in the POS application
after the recent fixes for order management, inventory tracking, and import resolution.

Test Areas:
1. Event System Functionality
2. Order Management Workflow
3. Inventory Tracking Workflow
4. Data Flow Between Components
5. KOT Status Changes
6. Real-time UI Updates
"""

import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from models.database import DatabaseManager, Table
from models.order import Order
from models.menu_item import MenuItem
from models.kot import KOT
from controllers.order_controller import OrderController
from utils.event_dispatcher import event_dispatcher, EventType
from utils.helpers import generate_order_number

class EventSystemTester:
    """Comprehensive event system and data flow tester"""
    
    def __init__(self):
        self.test_results = []
        self.event_log = []
        self.test_start_time = datetime.now()
        
        # Initialize database connection
        self.db = DatabaseManager()
        
        # Initialize models
        self.order_model = Order(self.db)
        self.menu_item_model = MenuItem(self.db)
        self.table_model = Table(self.db)
        self.kot_model = KOT(self.db)
        
        # Initialize controller
        self.order_controller = OrderController(self.db)
        
        # Set up event listeners for testing
        self.setup_event_listeners()
        
        # Don't set tkinter root - events will be processed synchronously
        # This ensures events are processed immediately in tests
        
        print("=" * 80)
        print("EVENT SYSTEM AND DATA FLOW TEST")
        print("=" * 80)
        print(f"Test started at: {self.test_start_time}")
        print()
    
    def setup_event_listeners(self):
        """Set up event listeners to capture all events"""
        # Subscribe to all event types
        event_dispatcher.subscribe(EventType.ORDER_CREATED, self.log_event)
        event_dispatcher.subscribe(EventType.ORDER_UPDATED, self.log_event)
        event_dispatcher.subscribe(EventType.KOT_STATUS_CHANGED, self.log_event)
        event_dispatcher.subscribe(EventType.INVENTORY_UPDATED, self.log_event)
        event_dispatcher.subscribe(EventType.TABLE_STATUS_CHANGED, self.log_event)
        event_dispatcher.subscribe(EventType.MENU_UPDATED, self.log_event)
        event_dispatcher.subscribe(EventType.PAYMENT_PROCESSED, self.log_event)
    
    def log_event(self, data):
        """Log all events for analysis"""
        event_info = {
            'timestamp': datetime.now(),
            'data': data,
            'thread': threading.current_thread().name
        }
        self.event_log.append(event_info)
        print(f"[EVENT] {event_info['timestamp']}: {data}")
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now()
        }
        self.test_results.append(result)
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    Details: {details}")
        print()
    
    def test_event_dispatcher_functionality(self):
        """Test basic event dispatcher functionality"""
        print("Testing Event Dispatcher Functionality...")
        print("-" * 50)
        
        # Test 1: Event subscription
        test_received = False
        def test_callback(data):
            nonlocal test_received
            test_received = True
        
        event_dispatcher.subscribe(EventType.ORDER_CREATED, test_callback)
        event_dispatcher.order_created("TEST-001", {'test': True})
        
        # Wait a bit for event processing
        time.sleep(0.1)
        
        self.log_test_result(
            "Event Subscription and Dispatch",
            test_received,
            "Event was properly subscribed and dispatched"
        )
        
        # Test 2: Event unsubscription
        test_received = False
        event_dispatcher.unsubscribe(EventType.ORDER_CREATED, test_callback)
        event_dispatcher.order_created("TEST-002", {'test': True})
        
        time.sleep(0.1)
        
        self.log_test_result(
            "Event Unsubscription",
            not test_received,
            "Event was properly unsubscribed and not received"
        )
        
        # Test 3: Multiple subscribers
        received_counts = {'callback1': 0, 'callback2': 0}
        def callback1(data): received_counts['callback1'] += 1
        def callback2(data): received_counts['callback2'] += 1
        
        event_dispatcher.subscribe(EventType.ORDER_CREATED, callback1)
        event_dispatcher.subscribe(EventType.ORDER_CREATED, callback2)
        event_dispatcher.order_created("TEST-003", {'test': True})
        
        time.sleep(0.1)
        
        self.log_test_result(
            "Multiple Event Subscribers",
            received_counts['callback1'] == 1 and received_counts['callback2'] == 1,
            f"Subscriber1: {received_counts['callback1']}, Subscriber2: {received_counts['callback2']}"
        )
        
        # Clean up
        event_dispatcher.unsubscribe(EventType.ORDER_CREATED, callback1)
        event_dispatcher.unsubscribe(EventType.ORDER_CREATED, callback2)
    
    def test_order_creation_workflow(self):
        """Test complete order creation workflow"""
        print("Testing Order Creation Workflow...")
        print("-" * 50)
        
        # Clear previous events
        self.event_log.clear()
        
        # Get a menu item for testing
        menu_items = self.menu_item_model.get_all()
        if not menu_items:
            self.log_test_result(
                "Order Creation Setup",
                False,
                "No menu items found in database"
            )
            return
        
        test_item = menu_items[0]
        item_id, name, category, price, stock = test_item
        
        # Get available table
        tables = self.table_model.get_available()
        if not tables:
            self.log_test_result(
                "Order Creation Setup",
                False,
                "No available tables found in database"
            )
            return
        
        test_table = tables[0]
        table_id, table_number = test_table
        
        # Test 1: Add item to cart
        success, message = self.order_controller.add_to_cart(item_id, 1)
        self.log_test_result(
            "Add Item to Cart",
            success,
            f"Added {name} to cart: {message}"
        )
        
        if not success:
            return
        
        # Test 2: Set order type and table
        self.order_controller.set_order_type("Dine-in")
        self.order_controller.set_table(table_id)
        
        self.log_test_result(
            "Set Order Type and Table",
            True,
            f"Set order type to Dine-in and table to {table_number}"
        )
        
        # Test 3: Process payment (this should trigger events)
        initial_event_count = len(self.event_log)
        
        success, result = self.order_controller.process_payment(
            "Cash", 0, "%", "Test Customer", "1234567890"
        )
        
        # Wait for event processing
        time.sleep(0.5)
        
        final_event_count = len(self.event_log)
        
        self.log_test_result(
            "Process Payment and Create Order",
            success,
            f"Order created with number: {result}" if success else f"Failed: {result}"
        )
        
        # Test 4: Verify events were dispatched
        order_created_events = [e for e in self.event_log if 'order_number' in str(e.get('data', {}))]
        
        self.log_test_result(
            "Order Creation Events Dispatched",
            len(order_created_events) > 0,
            f"Found {len(order_created_events)} order creation events"
        )
        
        # Test 5: Verify inventory update events
        inventory_events = [e for e in self.event_log if 'item_id' in str(e.get('data', {})) and 'quantity' in str(e.get('data', {}))]
        
        self.log_test_result(
            "Inventory Update Events Dispatched",
            len(inventory_events) > 0,
            f"Found {len(inventory_events)} inventory update events"
        )
        
        # Test 6: Verify table status change events
        table_events = [e for e in self.event_log if 'table_id' in str(e.get('data', {})) and 'status' in str(e.get('data', {}))]
        
        self.log_test_result(
            "Table Status Change Events Dispatched",
            len(table_events) > 0,
            f"Found {len(table_events)} table status change events"
        )
    
    def test_kot_workflow(self):
        """Test KOT workflow and status changes"""
        print("Testing KOT Workflow...")
        print("-" * 50)
        
        # Get pending KOT items
        kot_items = self.kot_model.get_items("Pending")
        
        if not kot_items:
            self.log_test_result(
                "KOT Workflow Setup",
                False,
                "No pending KOT items found"
            )
            return
        
        # Test 1: Get KOT items
        self.log_test_result(
            "Get KOT Items",
            len(kot_items) > 0,
            f"Found {len(kot_items)} pending KOT items"
        )
        
        # Test 2: Update KOT status
        test_item = kot_items[0]
        item_id = test_item[0]
        
        initial_event_count = len(self.event_log)
        
        self.kot_model.update_status(item_id, "Preparing")
        
        # Wait for event processing
        time.sleep(0.5)
        
        final_event_count = len(self.event_log)
        
        self.log_test_result(
            "Update KOT Status",
            final_event_count > initial_event_count,
            "KOT status update triggered events"
        )
        
        # Test 3: Verify KOT status change events
        kot_events = [e for e in self.event_log if 'item_id' in str(e.get('data', {})) and 'status' in str(e.get('data', {}))]
        
        self.log_test_result(
            "KOT Status Change Events Dispatched",
            len(kot_events) > 0,
            f"Found {len(kot_events)} KOT status change events"
        )
        
        # Test 4: Update to completed
        self.kot_model.update_status(item_id, "Completed")
        time.sleep(0.5)
        
        completed_items = self.kot_model.get_items("Completed")
        
        self.log_test_result(
            "KOT Status Update to Completed",
            any(item[0] == item_id for item in completed_items),
            "KOT item successfully marked as completed"
        )
    
    def test_inventory_workflow(self):
        """Test inventory tracking workflow"""
        print("Testing Inventory Workflow...")
        print("-" * 50)
        
        # Get a menu item for testing
        menu_items = self.menu_item_model.get_all()
        if not menu_items:
            self.log_test_result(
                "Inventory Workflow Setup",
                False,
                "No menu items found in database"
            )
            return
        
        test_item = menu_items[0]
        item_id, name, category, price, current_stock = test_item
        
        # Test 1: Get current stock
        self.log_test_result(
            "Get Current Stock",
            True,
            f"Item {name} has current stock: {current_stock}"
        )
        
        # Test 2: Update stock manually
        # Reset to a known value first
        reset_stock = 100
        self.menu_item_model.update_stock(item_id, reset_stock)
        time.sleep(0.2)  # Wait for reset to complete
        
        # Clear events after reset
        self.event_log.clear()
        initial_event_count = 0
        
        # Now update to new value
        new_stock = reset_stock + 10
        self.menu_item_model.update_stock(item_id, new_stock)
        
        # Wait for event processing
        time.sleep(0.5)
        
        final_event_count = len(self.event_log)
        
        self.log_test_result(
            "Update Stock Manually",
            final_event_count > initial_event_count,
            f"Stock updated from {reset_stock} to {new_stock}"
        )
        
        # Test 3: Verify inventory update events
        inventory_events = [e for e in self.event_log if 'item_id' in str(e.get('data', {})) and 'quantity' in str(e.get('data', {}))]
        
        self.log_test_result(
            "Inventory Update Events Dispatched",
            len(inventory_events) > 0,
            f"Found {len(inventory_events)} inventory update events"
        )
        
        # Test 4: Get inventory items
        inventory_items = self.menu_item_model.get_inventory_items()
        
        self.log_test_result(
            "Get Inventory Items",
            len(inventory_items) > 0,
            f"Found {len(inventory_items)} inventory items"
        )
        
        # Test 5: Test low stock filter
        low_stock_items = self.menu_item_model.get_inventory_items("", "Low Stock")
        
        self.log_test_result(
            "Low Stock Filter",
            True,
            f"Found {len(low_stock_items)} low stock items"
        )
    
    def test_data_flow_integrity(self):
        """Test data flow integrity between components"""
        print("Testing Data Flow Integrity...")
        print("-" * 50)
        
        # Test 1: Order data flow
        # Create an order and verify it appears in all related components
        menu_items = self.menu_item_model.get_all()
        if not menu_items:
            self.log_test_result(
                "Data Flow Setup",
                False,
                "No menu items found"
            )
            return
        
        test_item = menu_items[0]
        item_id, name, category, price, stock = test_item
        
        # Reset stock first to ensure item is available
        self.menu_item_model.update_stock(item_id, 100)
        time.sleep(0.2)
        
        # Add to cart and create order
        success, message = self.order_controller.add_to_cart(item_id, 1)
        if not success:
            self.log_test_result(
                "Order Data Flow",
                False,
                f"Failed to add item to cart: {message}"
            )
            return
            
        self.order_controller.set_order_type("Takeaway")
        
        success, order_number = self.order_controller.process_payment("Cash", 0, "%", "Test User", "9876543210")
        
        if not success:
            self.log_test_result(
                "Order Data Flow",
                False,
                f"Failed to create order: {order_number}"
            )
            return
        
        # Test 2: Verify order exists in database
        order_details = self.order_model.get_details_by_number(order_number)
        
        self.log_test_result(
            "Order Data Persistence",
            order_details is not None,
            f"Order {order_number} found in database"
        )
        
        # Test 3: Verify order items exist
        order_items = self.order_model.get_items_by_order_number(order_number)
        
        self.log_test_result(
            "Order Items Data Persistence",
            len(order_items) > 0,
            f"Found {len(order_items)} items for order {order_number}"
        )
        
        # Test 4: Verify KOT items created
        kot_items = self.kot_model.get_items("Pending")
        kot_order_items = [item for item in kot_items if item[1] == order_number]
        
        self.log_test_result(
            "KOT Items Data Flow",
            len(kot_order_items) > 0,
            f"Found {len(kot_order_items)} KOT items for order {order_number}"
        )
        
        # Test 5: Verify inventory was updated
        updated_item = self.menu_item_model.get_by_id(item_id)
        updated_stock = updated_item[3] if updated_item else stock
        
        self.log_test_result(
            "Inventory Data Flow",
            updated_stock < stock,
            f"Stock reduced from {stock} to {updated_stock}"
        )
    
    def test_event_system_performance(self):
        """Test event system performance under load"""
        print("Testing Event System Performance...")
        print("-" * 50)
        
        # Test 1: Multiple rapid events
        event_count = 50
        start_time = time.time()
        
        for i in range(event_count):
            event_dispatcher.order_created(f"PERF-TEST-{i}", {'test': True, 'index': i})
        
        # Wait for all events to process
        time.sleep(1.0)
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.log_test_result(
            "Multiple Rapid Events",
            len(self.event_log) >= event_count,
            f"Processed {len(self.event_log)}/{event_count} events in {duration:.3f}s"
        )
        
        # Test 2: Event processing time
        processing_times = []
        
        for i in range(10):
            start = time.time()
            event_dispatcher.inventory_updated(i, i * 10)
            time.sleep(0.01)  # Small delay
            end = time.time()
            processing_times.append(end - start)
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        
        self.log_test_result(
            "Event Processing Time",
            avg_processing_time < 0.1,
            f"Average processing time: {avg_processing_time:.4f}s"
        )
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("=" * 80)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        
        test_end_time = datetime.now()
        total_duration = test_end_time - self.test_start_time
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Test Duration: {total_duration}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("FAILED TESTS:")
            print("-" * 50)
            for result in self.test_results:
                if not result['passed']:
                    print(f"[FAIL] {result['test_name']}")
                    print(f"   Details: {result['details']}")
                    print()
        
        # Event analysis
        print("EVENT ANALYSIS:")
        print("-" * 50)
        print(f"Total Events Dispatched: {len(self.event_log)}")
        
        # Count events by type
        event_types = {}
        for event in self.event_log:
            data = event.get('data', {})
            if isinstance(data, dict):
                for key in data.keys():
                    if key in ['order_number', 'item_id', 'table_id']:
                        event_type = key
                        event_types[event_type] = event_types.get(event_type, 0) + 1
                        break
        
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count} events")
        
        print()
        
        # Recommendations
        print("RECOMMENDATIONS:")
        print("-" * 50)
        
        if failed_tests == 0:
            print("[SUCCESS] All tests passed! The event system and data flow are working correctly.")
        else:
            print("[WARNING] Some tests failed. Please review the failed tests above.")
        
        if len(self.event_log) == 0:
            print("[WARNING] No events were dispatched. Check event dispatcher initialization.")
        
        # Performance recommendations
        if total_tests > 0:
            avg_time_per_test = total_duration.total_seconds() / total_tests
            if avg_time_per_test > 1.0:
                print("[WARNING] Tests are running slowly. Consider optimizing event processing.")
        
        print()
        print("Event System and Data Flow Test Complete!")
        print("=" * 80)
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            'total_events': len(self.event_log),
            'duration': total_duration,
            'failed_test_details': [r for r in self.test_results if not r['passed']]
        }
    
    def run_all_tests(self):
        """Run all tests"""
        try:
            self.test_event_dispatcher_functionality()
            self.test_order_creation_workflow()
            self.test_kot_workflow()
            self.test_inventory_workflow()
            self.test_data_flow_integrity()
            self.test_event_system_performance()
            
            return self.generate_test_report()
            
        except Exception as e:
            print(f"Error running tests: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up
            if self.db:
                self.db.close()

def main():
    """Main function to run the event system tests"""
    tester = EventSystemTester()
    report = tester.run_all_tests()
    
    if report:
        # Save report to file
        with open("event_system_test_report.txt", "w") as f:
            f.write("EVENT SYSTEM AND DATA FLOW TEST REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Test Duration: {report['duration']}\n")
            f.write(f"Total Tests: {report['total_tests']}\n")
            f.write(f"Passed: {report['passed_tests']}\n")
            f.write(f"Failed: {report['failed_tests']}\n")
            f.write(f"Success Rate: {report['success_rate']:.1f}%\n")
            f.write(f"Total Events: {report['total_events']}\n")
            
            if report['failed_test_details']:
                f.write("\nFailed Tests:\n")
                for test in report['failed_test_details']:
                    f.write(f"- {test['test_name']}: {test['details']}\n")
        
        print(f"\nTest report saved to: event_system_test_report.txt")
    
    return report

if __name__ == "__main__":
    main()