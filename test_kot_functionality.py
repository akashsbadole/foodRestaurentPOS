#!/usr/bin/env python3
"""
Simple test to verify KOT functionality is working
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_kot_functionality():
    """Test KOT functionality specifically"""
    print("Testing KOT Functionality...")
    print("=" * 50)
    
    try:
        from src.models.database import DatabaseManager, KOT
        
        # Initialize database
        db = DatabaseManager()
        kot_model = KOT(db)
        
        # Test 1: Get pending items
        print("\n1. Testing get_items with 'Pending' status...")
        pending_items = kot_model.get_items("Pending")
        print(f"Found {len(pending_items)} pending items")
        
        if pending_items:
            print("[PASS] KOT get_items works for Pending status")
            
            # Test 2: Update status of first item
            print("\n2. Testing update_status...")
            first_item = pending_items[0]
            item_id = first_item[0]
            current_status = first_item[5]
            
            print(f"Updating item {item_id} from '{current_status}' to 'Preparing'")
            
            # Update status
            kot_model.update_status(item_id, "Preparing")
            
            # Verify update
            preparing_items = kot_model.get_items("Preparing")
            if preparing_items:
                print("[PASS] KOT update_status works")
                
                # Test 3: Get KOT details
                print("\n3. Testing get_kot_details...")
                kot_details = kot_model.get_kot_details(item_id)
                if kot_details:
                    order_number, name, quantity, created_at = kot_details
                    print(f"[PASS] KOT details retrieved: Order {order_number}, Item: {name}")
                else:
                    print("[FAIL] KOT details retrieval failed")
                    return False
            else:
                print("[FAIL] KOT update_status failed")
                return False
        else:
            print("[INFO] No pending items found (might be normal if no orders)")
        
        # Test 4: Get completed items
        print("\n4. Testing get_items with 'Completed' status...")
        completed_items = kot_model.get_items("Completed")
        print(f"Found {len(completed_items)} completed items")
        
        print("\n[PASS] KOT functionality test completed successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Error testing KOT functionality: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_kot_functionality()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)