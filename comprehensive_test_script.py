#!/usr/bin/env python3
"""
Comprehensive Testing Script for Restaurant POS System
Tests all modernized screens and functionality systematically
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import RestaurantPOSApp

class POSTestRunner:
    """Test runner for comprehensive POS system testing"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially
        self.app = None
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {details}")
        
    def test_application_startup(self):
        """Test 1: Application Startup and Login Screen"""
        print("\n" + "="*60)
        print("TEST 1: Application Startup and Login Screen")
        print("="*60)
        
        try:
            # Initialize application
            self.app = RestaurantPOSApp(self.root)
            self.log_test("Application Initialization", "PASS", "Application started without errors")
            
            # Test login screen visibility
            if hasattr(self.app, 'login_screen') and self.app.login_screen:
                self.log_test("Login Screen Display", "PASS", "Login screen created successfully")
            else:
                self.log_test("Login Screen Display", "FAIL", "Login screen not found")
                
            # Test login functionality with default credentials
            self.root.after(1000, self._test_login)
            self.root.mainloop()
            
        except Exception as e:
            self.log_test("Application Startup", "FAIL", f"Exception: {str(e)}")
            
    def _test_login(self):
        """Test login functionality"""
        try:
            # Set login credentials
            if hasattr(self.app.login_screen, 'username_entry') and hasattr(self.app.login_screen, 'password_entry'):
                self.app.login_screen.username_entry.insert(0, 'admin')
                self.app.login_screen.password_entry.insert(0, 'admin123')
                
                # Attempt login
                self.app.login_screen.login()
                
                # Check if login was successful
                if self.app.current_user and self.app.current_user['username'] == 'admin':
                    self.log_test("Login Authentication", "PASS", "Login successful with admin/admin123")
                    self._test_main_app_screens()
                else:
                    self.log_test("Login Authentication", "FAIL", "Login failed with valid credentials")
            else:
                self.log_test("Login Form Elements", "FAIL", "Username or password entry not found")
                
        except Exception as e:
            self.log_test("Login Functionality", "FAIL", f"Exception: {str(e)}")
            
        self.root.quit()
        
    def _test_main_app_screens(self):
        """Test all main application screens"""
        print("\n" + "="*60)
        print("TEST 2: Main Application Screens")
        print("="*60)
        
        # Test Dashboard Screen
        self._test_dashboard_screen()
        
        # Test Order Screen
        self._test_order_screen()
        
        # Test Menu Screen
        self._test_menu_screen()
        
        # Test Tables Screen
        self._test_tables_screen()
        
        # Test Inventory Screen
        self._test_inventory_screen()
        
        # Test KOT Screen
        self._test_kot_screen()
        
        # Test Reports Screen
        self._test_reports_screen()
        
        # Test Settings Screen
        self._test_settings_screen()
        
    def _test_dashboard_screen(self):
        """Test Dashboard Screen"""
        try:
            self.app.show_dashboard()
            self.log_test("Dashboard Screen", "PASS", "Dashboard loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Dashboard Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_order_screen(self):
        """Test Order Screen"""
        try:
            self.app.show_new_order()
            self.log_test("Order Screen", "PASS", "Order screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Order Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_menu_screen(self):
        """Test Menu Screen"""
        try:
            self.app.show_menu()
            self.log_test("Menu Screen", "PASS", "Menu screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Menu Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_tables_screen(self):
        """Test Tables Screen"""
        try:
            self.app.show_tables()
            self.log_test("Tables Screen", "PASS", "Tables screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Tables Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_inventory_screen(self):
        """Test Inventory Screen"""
        try:
            self.app.show_inventory()
            self.log_test("Inventory Screen", "PASS", "Inventory screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Inventory Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_kot_screen(self):
        """Test KOT Screen"""
        try:
            self.app.show_kot()
            self.log_test("KOT Screen", "PASS", "KOT screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("KOT Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_reports_screen(self):
        """Test Reports Screen"""
        try:
            self.app.show_reports()
            self.log_test("Reports Screen", "PASS", "Reports screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Reports Screen", "FAIL", f"Exception: {str(e)}")
            
    def _test_settings_screen(self):
        """Test Settings Screen"""
        try:
            self.app.show_settings()
            self.log_test("Settings Screen", "PASS", "Settings screen loaded without errors")
            time.sleep(0.5)
        except Exception as e:
            self.log_test("Settings Screen", "FAIL", f"Exception: {str(e)}")
            
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        for result in self.test_results:
            status_symbol = "[PASS]" if result['status'] == 'PASS' else "[FAIL]"
            print(f"{status_symbol} {result['test']}: {result['details']}")
            
        # Save report to file
        with open('test_report.txt', 'w') as f:
            f.write("Restaurant POS System - Comprehensive Test Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n\n")
            
            f.write("Detailed Results:\n")
            f.write("-" * 60 + "\n")
            for result in self.test_results:
                status_symbol = "PASS" if result['status'] == 'PASS' else "FAIL"
                f.write(f"[{status_symbol}] {result['test']}: {result['details']}\n")
                
        print(f"\nTest report saved to: test_report.txt")
        
    def run_tests(self):
        """Run all tests"""
        print("Starting comprehensive POS system testing...")
        self.test_application_startup()
        self.generate_test_report()

if __name__ == "__main__":
    test_runner = POSTestRunner()
    test_runner.run_tests()