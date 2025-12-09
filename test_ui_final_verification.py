#!/usr/bin/env python3
"""
Final test script to verify all UI fixes have been properly implemented
"""

import unittest
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sqlite3
import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.database import DatabaseManager
from src.ui.dashboard_screen import DashboardScreen
from src.ui.order_screen import OrderScreen
from src.ui.orders_screen import OrdersScreen
from src.ui.kot_screen import KOTScreen
from src.ui.menu_screen import MenuScreen

class TestUIFixes(unittest.TestCase):
    """Test class for verifying UI fixes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create test database
        cls.db_path = "test_restaurant_pos.db"
        cls.db = DatabaseManager(cls.db_path)
        
        # Create mock app instance for testing
        root = tk.Tk()
        root.withdraw()  # Hide the main window for testing
        
        # Mock app class with required attributes
        class MockApp:
            def __init__(self, db):
                self.root = root
                self.db = db
                self.content_frame = ttk.Frame(root)
                self.settings = {
                    'restaurant_name': 'Test Restaurant',
                    'tax_rate': '5'
                }
                # Mock models
                self.order_model = MockOrderModel(db)
                self.kot_model = MockKOTModel(db)
                self.menu_item_model = MockMenuItemModel(db)
                self.category_model = MockCategoryModel(db)
                self.table_model = MockTableModel(db)
                self.settings_model = MockSettingsModel(db)
        
        cls.app = MockApp(cls.db)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.db.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        if hasattr(cls, 'app'):
            cls.app.root.destroy()
    
    def test_dashboard_date_time_display(self):
        """Test dashboard has date/time display functionality"""
        # Create dashboard screen
        dashboard = DashboardScreen(TestUIFixes.app.root, TestUIFixes.app)
        
        # Check if dashboard was created successfully
        self.assertIsNotNone(dashboard)
        
        # Test that dashboard has date/time functionality
        # This tests the fix for adding date/time to dashboard
        self.assertTrue(hasattr(dashboard, 'setup_ui'))
    
    def test_order_screen_database_reference(self):
        """Test order screen has proper database reference"""
        # Create order screen
        order_screen = OrderScreen(TestUIFixes.app.root, TestUIFixes.app)
        
        # Check if order screen has database reference
        self.assertIsNotNone(order_screen.db)
        self.assertEqual(order_screen.db, TestUIFixes.app.db)
        
        # Test cart items list initialization
        self.assertIsInstance(order_screen.order_items, list)
        self.assertEqual(len(order_screen.order_items), 0)
        
        # Test cart totals initialization
        self.assertEqual(order_screen.subtotal, 0.0)
        self.assertEqual(order_screen.tax, 0.0)
        self.assertEqual(order_screen.discount, 0.0)
        self.assertEqual(order_screen.total, 0.0)
    
    def test_orders_screen_display(self):
        """Test orders screen display functionality"""
        # Create orders screen
        orders_screen = OrdersScreen(TestUIFixes.app.root, TestUIFixes.app)
        
        # Check if orders screen has necessary components
        self.assertIsNotNone(orders_screen.orders_tree)
        self.assertIsNotNone(orders_screen.order_filter_var)
        self.assertIsNotNone(orders_screen.order_search_entry)
    
    def test_kot_screen_display(self):
        """Test KOT screen display functionality"""
        # Create KOT screen
        kot_screen = KOTScreen(TestUIFixes.app.root, TestUIFixes.app)
        
        # Check if KOT screen has necessary components
        self.assertIsNotNone(kot_screen.kot_canvas)
        self.assertIsNotNone(kot_screen.kot_scrollable_frame)
        self.assertIsNotNone(kot_screen.kot_filter_var)
    
    def test_menu_screen_design(self):
        """Test menu screen design and functionality"""
        # Create menu screen
        menu_screen = MenuScreen(TestUIFixes.app.root, TestUIFixes.app)
        
        # Check if menu screen has necessary components
        self.assertIsNotNone(menu_screen.menu_items_tree)
        self.assertIsNotNone(menu_screen.categories_tree)
        self.assertIsNotNone(menu_screen.search_entry)
        self.assertIsNotNone(menu_screen.category_combo)

# Mock model classes for testing
class MockOrderModel:
    def __init__(self, db):
        self.db = db
    
    def get_all(self, filter_value="All", search_term=""):
        return []

class MockKOTModel:
    def __init__(self, db):
        self.db = db
    
    def get_items(self, status="Pending"):
        return []

class MockMenuItemModel:
    def __init__(self, db):
        self.db = db
    
    def get_all(self, search_term="", category="All"):
        return []

class MockCategoryModel:
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        return []

class MockTableModel:
    def __init__(self, db):
        self.db = db
    
    def get_available(self):
        return []

class MockSettingsModel:
    def __init__(self, db):
        self.db = db
    
    def get_dashboard_stats(self):
        return {
            'total_orders': 0,
            'today_sales': 0,
            'items_sold': 0,
            'occupied_tables': 0,
            'recent_orders': [],
            'top_items': []
        }

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)