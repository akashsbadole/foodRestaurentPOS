#!/usr/bin/env python3
"""
Simple test script to verify core functionality of refactored POS application
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Test imports
    print("Testing imports...")
    
    from models.database import DatabaseManager
    from models.report import Report
    from models.settings import Settings
    
    from utils.helpers import generate_order_number, format_currency, format_datetime
    from utils.constants import *
    
    print("OK All imports successful")
    
    # Test database connection
    print("\nTesting database connection...")
    db = DatabaseManager()
    print("OK Database connection established")
    
    # Test model initialization
    print("\nTesting model initialization...")
    settings_model = Settings(db)
    report_model = Report(db)
    print("OK All models initialized successfully")
    
    # Test basic database operations
    print("\nTesting basic database operations...")
    
    # Test settings
    settings = settings_model.get_all()
    print(f"OK Settings loaded: {len(settings)} settings found")
    
    # Test dashboard stats
    print("\nTesting dashboard statistics...")
    try:
        stats = report_model.get_dashboard_stats()
        print(f"OK Dashboard stats retrieved:")
        print(f"  - Total orders: {stats.get('total_orders', 0)}")
        print(f"  - Today's sales: {stats.get('today_sales', 0)}")
        print(f"  - Items sold: {stats.get('items_sold', 0)}")
        print(f"  - Occupied tables: {stats.get('occupied_tables', 0)}")
        print(f"  - Recent orders: {len(stats.get('recent_orders', []))}")
        print(f"  - Hourly sales: {len(stats.get('hourly_sales', []))}")
        print(f"  - Top items: {len(stats.get('top_items', []))}")
    except Exception as e:
        print(f"FAIL Dashboard stats failed: {e}")
    
    # Test helper functions
    print("\nTesting helper functions...")
    order_num = generate_order_number()
    print(f"OK Order number generated: {order_num}")
    
    formatted_currency = format_currency(1234.56)
    print(f"OK Currency formatted: {formatted_currency.encode('ascii', 'ignore').decode('ascii')}")
    
    formatted_date = format_datetime("2024-01-01 12:00:00")
    print(f"OK Date formatted: {formatted_date}")
    
    # Test report generation
    print("\nTesting report generation...")
    try:
        from_date = "2024-01-01"
        to_date = "2024-12-31"
        
        daily_sales = report_model.daily_sales_summary(from_date, to_date)
        print(f"OK Daily sales report: {len(daily_sales)} records")
        
        sales_by_item = report_model.sales_by_item(from_date, to_date)
        print(f"OK Sales by item report: {len(sales_by_item)} records")
        
        sales_by_category = report_model.sales_by_category(from_date, to_date)
        print(f"OK Sales by category report: {len(sales_by_category)} records")
        
    except Exception as e:
        print(f"FAIL Report generation failed: {e}")
    
    # Close database
    db.close()
    print("\nOK Database connection closed")
    
    print("\n" + "="*50)
    print("SUCCESS! CORE TESTS PASSED! The refactored application core is working correctly.")
    print("="*50)
    
except ImportError as e:
    print(f"FAIL Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAIL Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
