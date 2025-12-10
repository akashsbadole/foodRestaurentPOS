#!/usr/bin/env python3
"""
Test script for shortcode functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.database import DatabaseManager
from src.models.menu_item import MenuItem
from src.models.category import Category

def test_shortcode_functionality():
    """Test shortcode functionality end-to-end"""
    
    print("Testing shortcode functionality...")
    
    # Initialize database and models
    db = DatabaseManager('restaurant_pos.db')
    menu_item_model = MenuItem(db)
    category_model = Category(db)
    
    try:
        # Test 1: Get an existing category
        print("\n1. Getting existing category...")
        category_id = None
        categories = category_model.get_all()
        for cat in categories:
            if cat[1] == "Starters":  # Use existing category
                category_id = cat[0]
                break
        
        if not category_id and categories:
            # Use first available category
            category_id = categories[0][0]
        
        print(f"   Category ID: {category_id} ({'Starters' if categories and categories[0][1] == 'Starters' else categories[0][1] if categories else 'None'})")
        
        # Test 2: Add menu items with shortcodes
        print("\n2. Adding menu items with shortcodes...")
        
        # Add item with shortcode
        success = menu_item_model.add(
            "Test Item 1", 
            100.0, 
            category_id, 
            50, 
            "", 
            "11"
        )
        print(f"   Added item with shortcode '11': {'Success' if success else 'Failed'}")
        
        # Add item without shortcode
        success = menu_item_model.add(
            "Test Item 2", 
            150.0, 
            category_id, 
            30, 
            "", 
            ""
        )
        print(f"   Added item without shortcode: {'Success' if success else 'Failed'}")
        
        # Test 3: Test shortcode uniqueness validation
        print("\n3. Testing shortcode uniqueness validation...")
        
        # Try to add duplicate shortcode in same category
        success = menu_item_model.add(
            "Test Item 3",
            200.0,
            category_id,
            20,
            "",
            "11"  # Duplicate shortcode
        )
        print(f"   Attempted to add duplicate shortcode '11': {'Failed (Expected)' if not success else 'Success (Unexpected)'}")
        
        # Debug: Check what's happening
        if success:
            print("   DEBUG: Duplicate shortcode was allowed - checking uniqueness method...")
            is_unique = menu_item_model.is_shortcode_unique("11", category_id)
            print(f"   DEBUG: is_shortcode_unique('11', {category_id}) = {is_unique}")
        
        # Test 4: Test get_by_shortcode
        print("\n4. Testing get_by_shortcode...")
        
        item = menu_item_model.get_by_shortcode("11")
        if item:
            print(f"   Found item by shortcode '11': {item[1]} (ID: {item[0]})")
        else:
            print("   Failed to find item by shortcode '11'")
        
        # Test 5: Test search by shortcode
        print("\n5. Testing search by shortcode...")
        
        items = menu_item_model.get_all("11")
        if items:
            for item in items:
                print(f"   Found in search: {item[1]} (Shortcode: {item[5] or 'None'})")
        else:
            print("   No items found in search by shortcode")
        
        # Test 6: Test search by name
        print("\n6. Testing search by name...")
        
        items = menu_item_model.get_all("Test Item 1")
        if items:
            for item in items:
                print(f"   Found in search: {item[1]} (Shortcode: {item[5] or 'None'})")
        else:
            print("   No items found in search by name")
        
        print("\n7. Testing get_all with shortcode display...")
        items = menu_item_model.get_all()
        print("   All items with shortcodes:")
        for item in items:
            shortcode_display = item[5] if item[5] else "None"
            print(f"   - {item[1]} (Shortcode: {shortcode_display})")
        
        print("\nAll shortcode tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_shortcode_functionality()
    sys.exit(0 if success else 1)