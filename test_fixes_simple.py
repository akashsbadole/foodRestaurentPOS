#!/usr/bin/env python3
"""
Simple test script to verify the fixes for:
1. Order creation workflow (tuple object has no attribute get error)
2. Keyboard shortcuts modifications
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import traceback
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from models.database import DatabaseManager
from models.order import Order
from models.menu_item import MenuItem
from controllers.order_controller import OrderController
from utils.keyboard_handler import KeyboardHandler

class TestApp:
    """Mock app class for testing"""
    def __init__(self):
        self.db = DatabaseManager()
        self.settings = {
            'restaurant_name': 'Test Restaurant',
            'restaurant_address': 'Test Address',
            'tax_rate': '5.0',
            'auto_print_bill': 'False',
            'default_bill_printer_type': 'standard',
            'standard_printer_name': '',
            'thermal_printer_name': ''
        }
        self.content_frame = None
        self.order_model = Order(self.db)
        self.table_model = None
        self.menu_item_model = MenuItem(self.db)
        self.status_bar = None

class FixVerificationTest:
    """Test class to verify the fixes"""
    
    def __init__(self):
        self.test_results = {
            'order_creation_fix': {'status': 'PENDING', 'details': []},
            'keyboard_shortcuts_fix': {'status': 'PENDING', 'details': []},
            'overall_status': 'PENDING'
        }
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up test environment with database and UI components"""
        print("=" * 60)
        print("SETTING UP TEST ENVIRONMENT")
        print("=" * 60)
        
        try:
            # Create root window (hidden)
            self.root = tk.Tk()
            self.root.withdraw()  # Hide the window during testing
            
            # Create mock app
            self.app = TestApp()
            
            # Create content frame for testing
            self.app.content_frame = ttk.Frame(self.root)
            
            print("[PASS] Test environment initialized successfully")
            return True
            
        except Exception as e:
            print(f"[FAIL] Failed to setup test environment: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_order_creation_workflow(self):
        """Test 1: Verify order creation works without 'tuple object has no attribute get' error"""
        print("\n" + "=" * 60)
        print("TEST 1: Order Creation Workflow")
        print("=" * 60)
        
        try:
            # Create OrderController instance
            order_controller = OrderController(self.app.db)
            
            # Test 1: Check if OrderController can process payment with dictionary format
            print("\nTesting order creation with dictionary format...")
            
            # Add a test item to cart
            success, message = order_controller.add_to_cart(1, 2)  # Add 2 of item ID 1
            
            if success:
                print(f"[PASS] Item added to cart: {message}")
                self.test_results['order_creation_fix']['details'].append("Item added to cart successfully")
            else:
                print(f"[FAIL] Failed to add item to cart: {message}")
                self.test_results['order_creation_fix']['details'].append(f"Failed to add item to cart: {message}")
                self.test_results['order_creation_fix']['status'] = 'FAILED'
                return False
            
            # Test 2: Process payment with dictionary format
            print("\nTesting payment processing...")
            
            # Set table for dine-in
            order_controller.set_table(1)
            
            # Process payment
            success, result = order_controller.process_payment(
                payment_mode="Cash",
                discount_value=0,
                discount_type="%",
                customer_name="Test Customer",
                customer_mobile="1234567890"
            )
            
            if success:
                print(f"[PASS] Order created successfully: {result}")
                self.test_results['order_creation_fix']['details'].append(f"Order created successfully: {result}")
            else:
                print(f"[FAIL] Failed to create order: {result}")
                self.test_results['order_creation_fix']['details'].append(f"Failed to create order: {result}")
                self.test_results['order_creation_fix']['status'] = 'FAILED'
                return False
            
            # Test 3: Check Order model directly with dictionary input
            print("\nTesting Order model with dictionary input...")
            
            order_data = {
                'order_number': 'TEST-001',
                'table_id': 1,
                'customer_name': 'Test Customer',
                'customer_mobile': '1234567890',
                'order_type': 'Dine-in',
                'subtotal': 100.0,
                'tax': 5.0,
                'discount': 0.0,
                'total': 105.0,
                'items': [
                    {'id': 1, 'quantity': 2, 'price': 50.0, 'total': 100.0}
                ],
                'payment_mode': 'Cash'
            }
            
            order_id = self.app.order_model.create(order_data)
            
            if order_id:
                print(f"[PASS] Order model created order successfully: {order_id}")
                self.test_results['order_creation_fix']['details'].append("Order model handles dictionary input correctly")
            else:
                print("[FAIL] Order model failed to create order")
                self.test_results['order_creation_fix']['details'].append("Order model failed to create order")
                self.test_results['order_creation_fix']['status'] = 'FAILED'
                return False
            
            self.test_results['order_creation_fix']['status'] = 'PASSED'
            print("[PASS] Order creation workflow test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error testing order creation: {str(e)}")
            traceback.print_exc()
            self.test_results['order_creation_fix']['status'] = 'FAILED'
            self.test_results['order_creation_fix']['details'].append(f"Exception: {str(e)}")
            return False
    
    def test_keyboard_shortcuts(self):
        """Test 2: Verify keyboard shortcuts have been properly modified"""
        print("\n" + "=" * 60)
        print("TEST 2: Keyboard Shortcuts Modifications")
        print("=" * 60)
        
        try:
            # Create KeyboardHandler instance
            keyboard_handler = KeyboardHandler(self.root, self.app)
            
            # Test 1: Check if setup_global_keyboard_shortcuts method exists
            if hasattr(keyboard_handler, 'setup_global_keyboard_shortcuts'):
                print("[PASS] setup_global_keyboard_shortcuts method exists")
                self.test_results['keyboard_shortcuts_fix']['details'].append("setup_global_keyboard_shortcuts method exists")
            else:
                print("[FAIL] setup_global_keyboard_shortcuts method missing")
                self.test_results['keyboard_shortcuts_fix']['details'].append("setup_global_keyboard_shortcuts method missing")
                self.test_results['keyboard_shortcuts_fix']['status'] = 'FAILED'
                return False
            
            # Test 2: Check keyboard handler source code for modifications
            try:
                with open('src/utils/keyboard_handler.py', 'r') as f:
                    source = f.read()
                
                # Check for essential shortcuts (Alt+N, Alt+O, F1)
                if '<Alt-n>' in source and '<Alt-o>' in source and '<F1>' in source:
                    print("[PASS] Essential shortcuts (Alt+N, Alt+O, F1) are present")
                    self.test_results['keyboard_shortcuts_fix']['details'].append("Essential shortcuts preserved")
                else:
                    print("[FAIL] Essential shortcuts missing")
                    self.test_results['keyboard_shortcuts_fix']['details'].append("Essential shortcuts missing")
                    self.test_results['keyboard_shortcuts_fix']['status'] = 'FAILED'
                    return False
                
                # Check for removal of other shortcuts
                removed_shortcuts = ['<Alt-d>', '<Alt-m>', '<Alt-t>', '<Alt-i>', '<Alt-k>', '<Alt-r>', '<Alt-s>', '<Alt-l>']
                removed_count = 0
                for shortcut in removed_shortcuts:
                    if shortcut not in source:
                        removed_count += 1
                
                if removed_count >= len(removed_shortcuts) * 0.8:  # At least 80% removed
                    print(f"[PASS] Most non-essential shortcuts have been removed ({removed_count}/{len(removed_shortcuts)})")
                    self.test_results['keyboard_shortcuts_fix']['details'].append("Non-essential shortcuts removed")
                else:
                    print(f"[WARN] Only {removed_count}/{len(removed_shortcuts)} non-essential shortcuts removed")
                    self.test_results['keyboard_shortcuts_fix']['details'].append(f"Only {removed_count} non-essential shortcuts removed")
                
                # Check for Enter key functionality
                if 'event.keysym == \'Return\'' in source:
                    print("[PASS] Enter key functionality preserved")
                    self.test_results['keyboard_shortcuts_fix']['details'].append("Enter key functionality preserved")
                else:
                    print("[WARN] Enter key functionality may not be preserved")
                    self.test_results['keyboard_shortcuts_fix']['details'].append("Enter key functionality unclear")
                
            except Exception as e:
                print(f"[FAIL] Error reading keyboard handler file: {str(e)}")
                self.test_results['keyboard_shortcuts_fix']['details'].append(f"File read error: {str(e)}")
                self.test_results['keyboard_shortcuts_fix']['status'] = 'FAILED'
                return False
            
            # Test 3: Try to setup keyboard shortcuts
            try:
                keyboard_handler.setup_global_keyboard_shortcuts()
                print("[PASS] setup_global_keyboard_shortcuts executes without errors")
                self.test_results['keyboard_shortcuts_fix']['details'].append("setup_global_keyboard_shortcuts executes successfully")
            except Exception as e:
                print(f"[FAIL] Error in setup_global_keyboard_shortcuts: {str(e)}")
                self.test_results['keyboard_shortcuts_fix']['details'].append(f"setup_global_keyboard_shortcuts error: {str(e)}")
                self.test_results['keyboard_shortcuts_fix']['status'] = 'FAILED'
                return False
            
            self.test_results['keyboard_shortcuts_fix']['status'] = 'PASSED'
            print("[PASS] Keyboard shortcuts modifications test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error testing keyboard shortcuts: {str(e)}")
            traceback.print_exc()
            self.test_results['keyboard_shortcuts_fix']['status'] = 'FAILED'
            self.test_results['keyboard_shortcuts_fix']['details'].append(f"Exception: {str(e)}")
            return False
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Calculate overall status
        all_passed = all(
            result['status'] == 'PASSED' 
            for result in [
                self.test_results['order_creation_fix'],
                self.test_results['keyboard_shortcuts_fix']
            ]
        )
        
        self.test_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        # Print detailed results
        print(f"\nOVERALL STATUS: {self.test_results['overall_status']}")
        print("-" * 60)
        
        print("\n1. Order Creation Workflow Fix:")
        print(f"   Status: {self.test_results['order_creation_fix']['status']}")
        for detail in self.test_results['order_creation_fix']['details']:
            print(f"   - {detail}")
        
        print("\n2. Keyboard Shortcuts Modifications Fix:")
        print(f"   Status: {self.test_results['keyboard_shortcuts_fix']['status']}")
        for detail in self.test_results['keyboard_shortcuts_fix']['details']:
            print(f"   - {detail}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if self.test_results['overall_status'] == 'PASSED':
            print("[PASS] ALL FIXES VERIFIED SUCCESSFULLY")
            print("[PASS] Order creation workflow works without 'tuple object has no attribute get' error")
            print("[PASS] Keyboard shortcuts have been properly modified")
        else:
            print("[FAIL] SOME FIXES NEED ATTENTION")
            
            if self.test_results['order_creation_fix']['status'] != 'PASSED':
                print("[FAIL] Order creation fix needs review")
            
            if self.test_results['keyboard_shortcuts_fix']['status'] != 'PASSED':
                print("[FAIL] Keyboard shortcuts fix needs review")
        
        return self.test_results
    
    def cleanup(self):
        """Clean up test environment"""
        try:
            if hasattr(self, 'root'):
                self.root.destroy()
            print("\n[PASS] Test environment cleaned up")
        except Exception as e:
            print(f"\n[FAIL] Error during cleanup: {str(e)}")

def main():
    """Main test execution"""
    print("Starting Fix Verification Tests...")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create test instance
    test = FixVerificationTest()
    
    try:
        # Run tests
        test.test_order_creation_workflow()
        test.test_keyboard_shortcuts()
        
        # Generate report
        results = test.generate_test_report()
        
        # Return appropriate exit code
        return 0 if results['overall_status'] == 'PASSED' else 1
        
    except Exception as e:
        print(f"\n[FAIL] Test execution failed: {str(e)}")
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        test.cleanup()

if __name__ == "__main__":
    exit_code = main()
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Exit code: {exit_code}")
    sys.exit(exit_code)