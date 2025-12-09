#!/usr/bin/env python3
"""
Test script to verify all UI fixes have been properly implemented
"""

import unittest
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import sqlite3
import os
import sys

# Add src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import RestaurantPOSApp
from src.models.database import Database
from src.models.order import Order
from src.models.kot import KOT
from src.models.menu_item import MenuItem
from src.models.category import Category
from src.models.table import Table
from src.models.settings import Settings
from src.ui.dashboard_screen import DashboardScreen
from src.ui.order_screen import OrderScreen
from src.ui.orders_screen import OrdersScreen
from src.ui.kot_screen import KOTScreen
from src.ui.menu_screen import MenuScreen
from src.utils.constants import *

class TestUIFixes(unittest.TestCase):
    """Test class for verifying UI fixes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Create test database
        cls.db_path = "test_restaurant_pos.db"
        cls.db = Database(cls.db_path)
        
        # Initialize test data
        cls._setup_test_data()
        
        # Create app instance
        root = tk.Tk()
        root.withdraw()  # Hide the main window for testing
        cls.app = RestaurantPOSApp(root, cls.db)
        
        # Initialize models
        cls.order_model = Order(cls.db)
        cls.kot_model = KOT(cls.db)
        cls.menu_item_model = MenuItem(cls.db)
        cls.category_model = Category(cls.db)
        cls.table_model = Table(cls.db)
        cls.settings_model = Settings(cls.db)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.db.close()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        if hasattr(cls, 'app'):
            cls.app.root.destroy()
    
    @classmethod
    def _setup_test_data(cls):
        """Set up test data for database"""
        # Create tables if they don't exist
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_number TEXT UNIQUE,
            table_id INTEGER,
            customer_name TEXT,
            customer_mobile TEXT,
            order_type TEXT,
            subtotal REAL,
            tax REAL,
            discount REAL,
            total REAL,
            created_at TEXT,
            status TEXT
        )
        """)
        
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            menu_item_id INTEGER,
            quantity INTEGER,
            price REAL,
            total REAL,
            status TEXT,
            created_at TEXT
        )
        """)
        
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            category_id INTEGER,
            price REAL,
            stock_quantity INTEGER,
            image_path TEXT,
            created_at TEXT
        )
        """)
        
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            created_at TEXT
        )
        """)
        
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY,
            table_number INTEGER UNIQUE,
            status TEXT,
            created_at TEXT
        )
        """)
        
        cls.db.execute_query("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            key TEXT UNIQUE,
            value TEXT,
            created_at TEXT
        )
        """)
        
        # Insert test data
        cls.db.execute_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                          ("restaurant_name", "Test Restaurant"))
        cls.db.execute_query("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                          ("tax_rate", "5"))
        
        # Add test categories
        cls.db.execute_query("INSERT OR IGNORE INTO categories (name) VALUES (?)", ("Test Category",))
        
        # Add test menu items
        cls.db.execute_query("INSERT OR IGNORE INTO menu_items (name, category_id, price, stock_quantity) VALUES (?, ?, ?, ?)", 
                          ("Test Item", 1, 100.0, 10))
        
        # Add test tables
        cls.db.execute_query("INSERT OR IGNORE INTO tables (table_number, status) VALUES (?, ?)", 
                          (1, "Available"))
        
        cls.db.commit()
    
    def test_dashboard_statistics(self):
        """Test dashboard statistics display"""
        # Create dashboard screen
        dashboard = DashboardScreen(cls.app.root, cls.app)
        
        # Check if dashboard has date/time display
        self.assertIsNotNone(dashboard)
        
        # Test statistics loading
        stats = cls.db.get_dashboard_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_orders', stats)
        self.assertIn('today_sales', stats)
        self.assertIn('items_sold', stats)
        self.assertIn('occupied_tables', stats)
        
    def test_order_screen_cart_functionality(self):
        """Test order screen cart functionality"""
        # Create order screen
        order_screen = OrderScreen(cls.app.root, cls.app)
        
        # Check if order screen has database reference
        self.assertIsNotNone(order_screen.db)
        self.assertEqual(order_screen.db, cls.app.db)
        
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
        orders_screen = OrdersScreen(cls.app.root, cls.app)
        
        # Check if orders screen has necessary components
        self.assertIsNotNone(orders_screen.orders_tree)
        self.assertIsNotNone(orders_screen.order_filter_var)
        self.assertIsNotNone(orders_screen.order_search_entry)
        
        # Test order loading
        orders = cls.order_model.get_all()
        self.assertIsInstance(orders, list)
        
    def test_kot_screen_display(self):
        """Test KOT screen display functionality"""
        # Create KOT screen
        kot_screen = KOTScreen(cls.app.root, cls.app)
        
        # Check if KOT screen has necessary components
        self.assertIsNotNone(kot_screen.kot_canvas)
        self.assertIsNotNone(kot_screen.kot_scrollable_frame)
        self.assertIsNotNone(kot_screen.kot_filter_var)
        
        # Test KOT item loading
        kot_items = cls.kot_model.get_items()
        self.assertIsInstance(kot_items, list)
        
    def test_menu_screen_design(self):
        """Test menu screen design and functionality"""
        # Create menu screen
        menu_screen = MenuScreen(cls.app.root, cls.app)
        
        # Check if menu screen has necessary components
        self.assertIsNotNone(menu_screen.menu_items_tree)
        self.assertIsNotNone(menu_screen.categories_tree)
        self.assertIsNotNone(menu_screen.search_entry)
        self.assertIsNotNone(menu_screen.category_combo)
        
        # Test menu item loading
        menu_items = cls.menu_item_model.get_all()
        self.assertIsInstance(menu_items, list)
        
        # Test category loading
        categories = cls.category_model.get_all()
        self.assertIsInstance(categories, list)

if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)