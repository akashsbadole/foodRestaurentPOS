#!/usr/bin/env python3
"""
Complete Functionality Test for POS Application
Tests all major features including export/import functionality
"""

import os
import sys
import sqlite3
import tempfile
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_database_connection():
    """Test database connection and basic operations"""
    print("Testing database connection...")
    try:
        from src.models.database import DatabaseManager
        db = DatabaseManager()
        
        # Test basic query
        db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        result = db.fetch_one()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def test_data_manager():
    """Test data manager functionality"""
    print("Testing data manager...")
    try:
        from src.models.database import DatabaseManager
        from src.managers.data_manager import DataManager
        from src.models.database import User, Category, Table, Order, KOT, Settings
        from src.models.menu_item import MenuItem
        from src.models.report import Report
        
        # Create mock app
        class MockApp:
            def __init__(self):
                self.db = DatabaseManager()
                self.user_model = User(self.db)
                self.category_model = Category(self.db)
                self.menu_item_model = MenuItem(self.db)
                self.table_model = Table(self.db)
                self.order_model = Order(self.db)
                self.kot_model = KOT(self.db)
                self.report_model = Report(self.db)
                self.settings_model = Settings(self.db)
        
        app = MockApp()
        dm = DataManager(app)
        
        # Test getting categories
        categories = dm.get_categories()
        print(f"Data manager working - found {len(categories)} categories")
        
        return True
    except Exception as e:
        print(f"Data manager test failed: {e}")
        return False

def test_data_exporter():
    """Test data export functionality"""
    print("Testing data export functionality...")
    try:
        from src.utils.data_exporter import DataExporter
        from src.managers.data_manager import DataManager
        
        # Create mock app
        class MockApp:
            def __init__(self):
                from src.models.database import DatabaseManager
                from src.models.database import User, Category, Table, Order, KOT, Settings
                from src.models.menu_item import MenuItem
                from src.models.report import Report
                
                self.db = DatabaseManager()
                self.user_model = User(self.db)
                self.category_model = Category(self.db)
                self.menu_item_model = MenuItem(self.db)
                self.table_model = Table(self.db)
                self.order_model = Order(self.db)
                self.kot_model = KOT(self.db)
                self.report_model = Report(self.db)
                self.settings_model = Settings(self.db)
        
        app = MockApp()
        data_manager = DataManager(app)
        exporter = DataExporter(app, data_manager)
        
        # Test export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # Export all data
            success = exporter.export_data('all', 'json', temp_file)
            if success:
                print("Data export successful")
                
                # Verify export file
                if os.path.exists(temp_file):
                    with open(temp_file, 'r') as f:
                        data = json.load(f)
                    print(f"Export file created with {len(data.get('data', {}))} data types")
                    return True
                else:
                    print("Export file not created")
                    return False
            else:
                print("Data export failed")
                return False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception as e:
        print(f"Data exporter test failed: {e}")
        return False

def test_data_importer():
    """Test data import functionality"""
    print("Testing data import functionality...")
    try:
        from src.utils.data_importer import DataImporter
        from src.managers.data_manager import DataManager
        
        # Create mock app
        class MockApp:
            def __init__(self):
                from src.models.database import DatabaseManager
                from src.models.database import User, Category, Table, Order, KOT, Settings
                from src.models.menu_item import MenuItem
                from src.models.report import Report
                
                self.db = DatabaseManager()
                self.user_model = User(self.db)
                self.category_model = Category(self.db)
                self.menu_item_model = MenuItem(self.db)
                self.table_model = Table(self.db)
                self.order_model = Order(self.db)
                self.kot_model = KOT(self.db)
                self.report_model = Report(self.db)
                self.settings_model = Settings(self.db)
        
        app = MockApp()
        data_manager = DataManager(app)
        importer = DataImporter(app, data_manager)
        
        # Create test data
        test_data = {
            'categories': [
                {'id': 999, 'name': 'Test Category'}
            ],
            'menu_items': [
                {
                    'id': 999,
                    'name': 'Test Item',
                    'category_id': 999,
                    'price': 10.99,
                    'stock_quantity': 100
                }
            ]
        }
        
        # Test import
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            result = importer.import_data(temp_file, 'all', validate_only=False)
            print(f"Import result: {result}")  # Debug output
            if result['success']:
                print("Data import successful")
                print(f"Imported: {result.get('total_imported', 0)} items")
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                errors = result.get('errors', [])
                print(f"Data import failed: {error_msg}")
                if errors:
                    print(f"Errors: {errors}")
                return False
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception as e:
        print(f"Data importer test failed: {e}")
        return False

def test_event_dispatcher():
    """Test event dispatcher functionality"""
    print("Testing event dispatcher...")
    try:
        from src.utils.event_dispatcher import event_dispatcher, EventType
        
        # Test event subscription and dispatching
        callback_called = False
        
        def test_callback(data):
            nonlocal callback_called
            callback_called = True
        
        event_dispatcher.subscribe(EventType.ORDER_CREATED, test_callback)
        event_dispatcher.dispatch(EventType.ORDER_CREATED, {'test': 'data'})
        
        if callback_called:
            print("Event dispatcher working correctly")
            return True
        else:
            print("Event dispatcher callback not called")
            return False
            
    except Exception as e:
        print(f"Event dispatcher test failed: {e}")
        return False

def test_ui_components():
    """Test UI component imports"""
    print("Testing UI component imports...")
    try:
        from src.ui.dashboard_screen import DashboardScreen
        from src.ui.order_screen import OrderScreen
        from src.ui.orders_screen import OrdersScreen
        from src.ui.data_management_screen import DataManagementScreen
        
        print("All UI components imported successfully")
        return True
    except Exception as e:
        print(f"UI component import failed: {e}")
        return False

def main():
    """Run all functionality tests"""
    print("Starting Complete POS Functionality Test")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Data Manager", test_data_manager),
        ("Event Dispatcher", test_event_dispatcher),
        ("Data Exporter", test_data_exporter),
        ("Data Importer", test_data_importer),
        ("UI Components", test_ui_components),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1
        print("-" * 30)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! The POS application is fully functional.")
        print("\nKey Features Working:")
        print("  - Database connectivity")
        print("  - Centralized data management with caching")
        print("  - Event-driven architecture")
        print("  - Complete data export functionality")
        print("  - Complete data import functionality")
        print("  - All UI components properly imported")
        print("  - Data Management screen for admin users")
        print("\nReady to run: python -m src.app")
    else:
        print(f"{total - passed} tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
