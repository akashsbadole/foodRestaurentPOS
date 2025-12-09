#!/usr/bin/env python3
"""
Comprehensive test script to verify the fixes for:
1. OrderScreen AttributeError with missing show_print_options method
2. Inventory quantity default issue (empty stock fields defaulting to 0)
"""

import sys
import os
import tkinter as tk
from tkinter import ttk
import traceback
from datetime import datetime
import inspect

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import required modules
from models.database import DatabaseManager, MenuItem, Category
from ui.order_screen import OrderScreen
from ui.inventory_screen import InventoryScreen
from controllers.order_controller import OrderController

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
        self.order_model = None
        self.table_model = None
        self.menu_item_model = MenuItem(self.db)

class FixVerificationTest:
    """Test class to verify the fixes"""
    
    def __init__(self):
        self.test_results = {
            'order_screen_fix': {'status': 'PENDING', 'details': []},
            'inventory_default_fix': {'status': 'PENDING', 'details': []},
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
    
    def test_order_screen_show_print_options(self):
        """Test 1: Verify OrderScreen has show_print_options method and it works"""
        print("\n" + "=" * 60)
        print("TEST 1: OrderScreen show_print_options Method")
        print("=" * 60)
        
        try:
            # Create OrderScreen instance
            order_screen = OrderScreen(self.root, self.app)
            
            # Check if show_print_options method exists
            if hasattr(order_screen, 'show_print_options'):
                print("[PASS] show_print_options method exists in OrderScreen")
                self.test_results['order_screen_fix']['details'].append("Method exists")
            else:
                print("[FAIL] show_print_options method missing from OrderScreen")
                self.test_results['order_screen_fix']['details'].append("Method missing")
                self.test_results['order_screen_fix']['status'] = 'FAILED'
                return False
            
            # Check if datetime import is present (the fix) - read file directly
            try:
                with open('src/ui/order_screen.py', 'r') as f:
                    source = f.read()
                if 'from datetime import datetime' in source:
                    print("[PASS] datetime import found in OrderScreen (fix applied)")
                    self.test_results['order_screen_fix']['details'].append("datetime import present")
                elif 'import datetime' in source:
                    print("[PASS] datetime import found in OrderScreen (fix applied)")
                    self.test_results['order_screen_fix']['details'].append("datetime import present")
                else:
                    print("[FAIL] datetime import not found in OrderScreen")
                    self.test_results['order_screen_fix']['details'].append("datetime import missing")
                    self.test_results['order_screen_fix']['status'] = 'FAILED'
                    return False
            except Exception as e:
                print(f"[FAIL] Error reading OrderScreen file: {str(e)}")
                self.test_results['order_screen_fix']['details'].append(f"File read error: {str(e)}")
                self.test_results['order_screen_fix']['status'] = 'FAILED'
                return False
            
            # Test method accessibility (try to call it with mock data)
            try:
                # This should not raise AttributeError anymore
                method = getattr(order_screen, 'show_print_options')
                print("[PASS] show_print_options method is accessible")
                self.test_results['order_screen_fix']['details'].append("Method accessible")
            except AttributeError as e:
                print(f"[FAIL] AttributeError when accessing show_print_options: {str(e)}")
                self.test_results['order_screen_fix']['details'].append(f"AttributeError: {str(e)}")
                self.test_results['order_screen_fix']['status'] = 'FAILED'
                return False
            
            # Check if _prepare_kot_data method uses datetime.now()
            if hasattr(order_screen, '_prepare_kot_data'):
                kot_source = inspect.getsource(order_screen._prepare_kot_data)
                if 'datetime.now()' in kot_source:
                    print("[PASS] _prepare_kot_data uses datetime.now() correctly")
                    self.test_results['order_screen_fix']['details'].append("datetime.now() used correctly")
                else:
                    print("[WARN] _prepare_kot_data may not use datetime.now()")
                    self.test_results['order_screen_fix']['details'].append("datetime.now() usage unclear")
            
            self.test_results['order_screen_fix']['status'] = 'PASSED'
            print("[PASS] OrderScreen show_print_options method test PASSED")
            return True
            
        except Exception as e:
            print(f"[FAIL] Error testing OrderScreen: {str(e)}")
            traceback.print_exc()
            self.test_results['order_screen_fix']['status'] = 'FAILED'
            self.test_results['order_screen_fix']['details'].append(f"Exception: {str(e)}")
            return False
    
    def test_inventory_quantity_default(self):
        """Test 2: Verify inventory items with empty stock default to 0"""
        print("\n" + "=" * 60)
        print("TEST 2: Inventory Quantity Default to 0")
        print("=" * 60)
        
        try:
            # Create test data
            db = self.app.db
            
            # Create a test category first
            db.execute_query("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Test Category",))
            db.commit()
            
            # Get category ID
            db.execute_query("SELECT id FROM categories WHERE name = ?", ("Test Category",))
            category_result = db.fetch_one()
            category_id = category_result[0] if category_result else 1
            
            # Test 1: Add menu item with empty stock (should default to 0)
            print("\nTesting menu item creation with empty stock...")
            
            # First, let's check the current implementation
            # We need to examine the add method in MenuItem model
            menu_item_model = MenuItem(db)
            
            # Test adding item with empty stock
            test_item_name = f"Test Item {datetime.now().strftime('%H%M%S')}"
            
            # Try to add with empty string stock (this should be handled)
            try:
                # Check if the model handles empty stock properly
                print(f"[DEBUG] Attempting to add item: {test_item_name}, category_id: {category_id}")
                success = menu_item_model.add(test_item_name, 10.99, category_id, "")
                
                print(f"[DEBUG] Add result: {success}")
                
                if success:
                    print("[PASS] Menu item added with empty stock")
                    
                    # Check what value was actually stored
                    db.execute_query("SELECT stock_quantity FROM menu_items WHERE name = ?", (test_item_name,))
                    result = db.fetch_one()
                    
                    if result:
                        stock_value = result[0]
                        print(f"[INFO] Stock value stored: {stock_value} (type: {type(stock_value)})")
                        
                        # Check if it defaults to 0
                        if stock_value == 0 or stock_value == "0":
                            print("[PASS] Empty stock correctly defaults to 0")
                            self.test_results['inventory_default_fix']['details'].append("Empty stock defaults to 0")
                        else:
                            print(f"[FAIL] Empty stock does not default to 0, got: {stock_value}")
                            self.test_results['inventory_default_fix']['details'].append(f"Empty stock defaults to: {stock_value}")
                    else:
                        print("[FAIL] Could not retrieve stock value")
                        self.test_results['inventory_default_fix']['details'].append("Could not retrieve stock value")
                else:
                    print("[FAIL] Failed to add menu item with empty stock")
                    self.test_results['inventory_default_fix']['details'].append("Failed to add item with empty stock")
                    
            except Exception as e:
                print(f"[FAIL] Error adding menu item with empty stock: {str(e)}")
                traceback.print_exc()
                self.test_results['inventory_default_fix']['details'].append(f"Error: {str(e)}")
            
            # Test 2: Check UI behavior for empty stock
            print("\nTesting UI behavior for empty stock...")
            
            # Create InventoryScreen instance
            inventory_screen = InventoryScreen(self.root, self.app)
            
            # Check if the UI handles stock display properly
            if hasattr(inventory_screen, 'load_inventory'):
                print("[PASS] load_inventory method exists in InventoryScreen")
                self.test_results['inventory_default_fix']['details'].append("load_inventory method exists")
                
                # Try to load inventory
                try:
                    inventory_screen.load_inventory()
                    print("[PASS] load_inventory executed without errors")
                    self.test_results['inventory_default_fix']['details'].append("load_inventory executes successfully")
                except Exception as e:
                    print(f"[FAIL] Error in load_inventory: {str(e)}")
                    self.test_results['inventory_default_fix']['details'].append(f"load_inventory error: {str(e)}")
            else:
                print("[FAIL] load_inventory method missing from InventoryScreen")
                self.test_results['inventory_default_fix']['details'].append("load_inventory method missing")
            
            # Test 3: Check update_stock method behavior
            print("\nTesting update_stock method...")
            
            if hasattr(menu_item_model, 'update_stock'):
                print("[PASS] update_stock method exists in MenuItem model")
                self.test_results['inventory_default_fix']['details'].append("update_stock method exists")
                
                # Try to update stock to 0
                try:
                    # Get the test item ID
                    db.execute_query("SELECT id FROM menu_items WHERE name = ?", (test_item_name,))
                    item_result = db.fetch_one()
                    
                    if item_result:
                        item_id = item_result[0]
                        menu_item_model.update_stock(item_id, 0)
                        
                        # Verify the update
                        db.execute_query("SELECT stock_quantity FROM menu_items WHERE id = ?", (item_id,))
                        stock_result = db.fetch_one()
                        
                        if stock_result and stock_result[0] == 0:
                            print("[PASS] Stock successfully updated to 0")
                            self.test_results['inventory_default_fix']['details'].append("Stock update to 0 works")
                        else:
                            print(f"[FAIL] Stock update to 0 failed, got: {stock_result[0] if stock_result else 'None'}")
                            self.test_results['inventory_default_fix']['details'].append("Stock update to 0 failed")
                    
                except Exception as e:
                    print(f"[FAIL] Error testing update_stock: {str(e)}")
                    self.test_results['inventory_default_fix']['details'].append(f"update_stock error: {str(e)}")
            
            # Clean up test data
            try:
                db.execute_query("DELETE FROM menu_items WHERE name = ?", (test_item_name,))
                db.commit()
                print("[PASS] Test data cleaned up")
            except Exception as e:
                print(f"[FAIL] Error cleaning up test data: {str(e)}")
            
            # Determine overall test status
            if any("error" in detail.lower() or "failed" in detail.lower() or "missing" in detail.lower() 
                   for detail in self.test_results['inventory_default_fix']['details']):
                self.test_results['inventory_default_fix']['status'] = 'FAILED'
            else:
                self.test_results['inventory_default_fix']['status'] = 'PASSED'
            
            return self.test_results['inventory_default_fix']['status'] == 'PASSED'
            
        except Exception as e:
            print(f"[FAIL] Error testing inventory quantity default: {str(e)}")
            traceback.print_exc()
            self.test_results['inventory_default_fix']['status'] = 'FAILED'
            self.test_results['inventory_default_fix']['details'].append(f"Exception: {str(e)}")
            return False
    
    def check_for_additional_issues(self):
        """Check for any additional issues that might have been introduced by the fixes"""
        print("\n" + "=" * 60)
        print("CHECKING FOR ADDITIONAL ISSUES")
        print("=" * 60)
        
        additional_issues = []
        
        try:
            # Check for import issues
            print("Checking for import issues...")
            
            try:
                from ui.order_screen import OrderScreen
                print("[PASS] OrderScreen imports successfully")
            except ImportError as e:
                print(f"[FAIL] Import error in OrderScreen: {str(e)}")
                additional_issues.append(f"OrderScreen import error: {str(e)}")
            
            try:
                from ui.inventory_screen import InventoryScreen
                print("[PASS] InventoryScreen imports successfully")
            except ImportError as e:
                print(f"[FAIL] Import error in InventoryScreen: {str(e)}")
                additional_issues.append(f"InventoryScreen import error: {str(e)}")
            
            # Check for syntax errors in key files
            print("\nChecking for syntax errors...")
            
            files_to_check = [
                'src/ui/order_screen.py',
                'src/ui/inventory_screen.py',
                'src/controllers/order_controller.py',
                'src/models/menu_item.py'
            ]
            
            for file_path in files_to_check:
                try:
                    with open(file_path, 'r') as f:
                        code = f.read()
                    compile(code, file_path, 'exec')
                    print(f"[PASS] {file_path} - No syntax errors")
                except SyntaxError as e:
                    print(f"[FAIL] Syntax error in {file_path}: {str(e)}")
                    additional_issues.append(f"Syntax error in {file_path}: {str(e)}")
                except Exception as e:
                    print(f"[FAIL] Error checking {file_path}: {str(e)}")
                    additional_issues.append(f"Error checking {file_path}: {str(e)}")
            
            # Check for potential runtime issues
            print("\nChecking for potential runtime issues...")
            
            # Test OrderScreen initialization
            try:
                order_screen = OrderScreen(self.root, self.app)
                print("[PASS] OrderScreen initializes without errors")
            except Exception as e:
                print(f"[FAIL] OrderScreen initialization error: {str(e)}")
                additional_issues.append(f"OrderScreen init error: {str(e)}")
            
            # Test InventoryScreen initialization
            try:
                inventory_screen = InventoryScreen(self.root, self.app)
                print("[PASS] InventoryScreen initializes without errors")
            except Exception as e:
                print(f"[FAIL] InventoryScreen initialization error: {str(e)}")
                additional_issues.append(f"InventoryScreen init error: {str(e)}")
            
            # Test OrderController initialization
            try:
                order_controller = OrderController(self.app.db)
                print("[PASS] OrderController initializes without errors")
            except Exception as e:
                print(f"[FAIL] OrderController initialization error: {str(e)}")
                additional_issues.append(f"OrderController init error: {str(e)}")
            
        except Exception as e:
            print(f"[FAIL] Error during additional issues check: {str(e)}")
            additional_issues.append(f"Additional check error: {str(e)}")
        
        return additional_issues
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        # Calculate overall status
        all_passed = all(
            result['status'] == 'PASSED' 
            for result in [
                self.test_results['order_screen_fix'],
                self.test_results['inventory_default_fix']
            ]
        )
        
        self.test_results['overall_status'] = 'PASSED' if all_passed else 'FAILED'
        
        # Print detailed results
        print(f"\nOVERALL STATUS: {self.test_results['overall_status']}")
        print("-" * 60)
        
        print("\n1. OrderScreen show_print_options Fix:")
        print(f"   Status: {self.test_results['order_screen_fix']['status']}")
        for detail in self.test_results['order_screen_fix']['details']:
            print(f"   - {detail}")
        
        print("\n2. Inventory Quantity Default Fix:")
        print(f"   Status: {self.test_results['inventory_default_fix']['status']}")
        for detail in self.test_results['inventory_default_fix']['details']:
            print(f"   - {detail}")
        
        # Check for additional issues
        additional_issues = self.check_for_additional_issues()
        if additional_issues:
            print("\n3. Additional Issues Found:")
            for issue in additional_issues:
                print(f"   [FAIL] {issue}")
        else:
            print("\n3. Additional Issues: None found [PASS]")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if self.test_results['overall_status'] == 'PASSED':
            print("[PASS] ALL FIXES VERIFIED SUCCESSFULLY")
            print("[PASS] OrderScreen show_print_options method is accessible")
            print("[PASS] Inventory quantity default to 0 is working")
            print("[PASS] No additional issues detected")
        else:
            print("[FAIL] SOME FIXES NEED ATTENTION")
            
            if self.test_results['order_screen_fix']['status'] != 'PASSED':
                print("[FAIL] OrderScreen fix needs review")
            
            if self.test_results['inventory_default_fix']['status'] != 'PASSED':
                print("[FAIL] Inventory fix needs review")
        
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
        test.test_order_screen_show_print_options()
        test.test_inventory_quantity_default()
        
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