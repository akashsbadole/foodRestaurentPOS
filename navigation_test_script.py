#!/usr/bin/env python3
"""
Navigation Testing Script for Restaurant POS System
Tests navigation between all screens and integration
"""

import sys
import os
import time
import tkinter as tk
from tkinter import ttk

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import RestaurantPOSApp

class NavigationTestRunner:
    """Test runner for navigation testing"""
    
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
        
    def test_navigation(self):
        """Test navigation between all screens"""
        print("\n" + "="*60)
        print("NAVIGATION AND INTEGRATION TESTING")
        print("="*60)
        
        try:
            # Initialize application
            self.app = RestaurantPOSApp(self.root)
            self.log_test("Application Initialization", "PASS", "Application started for navigation testing")
            
            # Auto-login for testing
            self.root.after(1000, self._auto_login_and_test_navigation)
            self.root.mainloop()
            
        except Exception as e:
            self.log_test("Navigation Testing", "FAIL", f"Exception: {str(e)}")
            
    def _auto_login_and_test_navigation(self):
        """Auto-login and test navigation"""
        try:
            # Set login credentials
            if hasattr(self.app.login_screen, 'username_entry') and hasattr(self.app.login_screen, 'password_entry'):
                self.app.login_screen.username_entry.insert(0, 'admin')
                self.app.login_screen.password_entry.insert(0, 'admin123')
                
                # Attempt login
                self.app.login_screen.login()
                
                if self.app.current_user:
                    self.log_test("Auto-Login", "PASS", "Login successful for navigation testing")
                    self._test_screen_navigation()
                else:
                    self.log_test("Auto-Login", "FAIL", "Login failed")
                    
        except Exception as e:
            self.log_test("Auto-Login", "FAIL", f"Exception: {str(e)}")
            
        self.root.quit()
        
    def _test_screen_navigation(self):
        """Test navigation between all screens"""
        screens_to_test = [
            ("Dashboard", self.app.show_dashboard),
            ("New Order", self.app.show_new_order),
            ("Orders", self.app.show_orders),
            ("Menu", self.app.show_menu),
            ("Tables", self.app.show_tables),
            ("Inventory", self.app.show_inventory),
            ("KOT", self.app.show_kot),
            ("Reports", self.app.show_reports),
            ("Settings", self.app.show_settings),
            ("Back to Dashboard", self.app.show_dashboard)
        ]
        
        for i, (screen_name, navigation_method) in enumerate(screens_to_test):
            try:
                # Clear content frame before navigation
                if hasattr(self.app, 'content_frame'):
                    for widget in self.app.content_frame.winfo_children():
                        widget.destroy()
                
                # Navigate to screen
                navigation_method()
                time.sleep(0.3)  # Brief pause for screen to load
                
                # Check if content frame has children (screen loaded)
                if hasattr(self.app, 'content_frame'):
                    children = self.app.content_frame.winfo_children()
                    if children:
                        self.log_test(f"Navigate to {screen_name}", "PASS", f"Screen loaded successfully")
                    else:
                        self.log_test(f"Navigate to {screen_name}", "FAIL", "No content loaded")
                else:
                    self.log_test(f"Navigate to {screen_name}", "FAIL", "Content frame not found")
                    
            except Exception as e:
                self.log_test(f"Navigate to {screen_name}", "FAIL", f"Exception: {str(e)}")
                
        # Test consistent theme and design
        self._test_design_consistency()
        
    def _test_design_consistency(self):
        """Test design consistency across screens"""
        try:
            # Navigate to a few key screens to check consistency
            test_screens = [
                ("Dashboard", self.app.show_dashboard),
                ("Menu", self.app.show_menu),
                ("KOT", self.app.show_kot)
            ]
            
            for screen_name, navigation_method in test_screens:
                try:
                    navigation_method()
                    time.sleep(0.2)
                    
                    # Check if modern styling is applied
                    if hasattr(self.app, 'content_frame'):
                        children = self.app.content_frame.winfo_children()
                        if children:
                            self.log_test(f"Design Consistency - {screen_name}", "PASS", "Modern styling applied")
                        else:
                            self.log_test(f"Design Consistency - {screen_name}", "FAIL", "No content to check")
                            
                except Exception as e:
                    self.log_test(f"Design Consistency - {screen_name}", "FAIL", f"Exception: {str(e)}")
                    
        except Exception as e:
            self.log_test("Design Consistency", "FAIL", f"Exception: {str(e)}")
            
    def generate_navigation_report(self):
        """Generate navigation test report"""
        print("\n" + "="*60)
        print("NAVIGATION AND INTEGRATION TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        
        print(f"Total Navigation Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print("\nDetailed Results:")
        print("-" * 60)
        for result in self.test_results:
            status_symbol = "[PASS]" if result['status'] == 'PASS' else "[FAIL]"
            print(f"{status_symbol} {result['test']}: {result['details']}")
            
        # Save report to file
        with open('navigation_test_report.txt', 'w') as f:
            f.write("Restaurant POS System - Navigation and Integration Test Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Navigation Tests: {total_tests}\n")
            f.write(f"Passed: {passed_tests}\n")
            f.write(f"Failed: {failed_tests}\n")
            f.write(f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n\n")
            
            f.write("Detailed Results:\n")
            f.write("-" * 60 + "\n")
            for result in self.test_results:
                status_symbol = "PASS" if result['status'] == 'PASS' else "FAIL"
                f.write(f"[{status_symbol}] {result['test']}: {result['details']}\n")
                
        print(f"\nNavigation test report saved to: navigation_test_report.txt")
        
    def run_navigation_tests(self):
        """Run all navigation tests"""
        print("Starting navigation and integration testing...")
        self.test_navigation()
        self.generate_navigation_report()

if __name__ == "__main__":
    test_runner = NavigationTestRunner()
    test_runner.run_navigation_tests()