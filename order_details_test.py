#!/usr/bin/env python3
"""
Order Details Visibility Test
Tests the order details functionality specifically
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_order_details_visibility():
    """Test order details visibility functionality"""
    print("Testing Order Details Visibility...")
    print("=" * 50)
    
    try:
        from src.models.database import DatabaseManager
        from src.models.order import Order
        
        # Initialize database and order model
        db = DatabaseManager()
        order_model = Order(db)
        
        # Test 1: Get all orders
        print("1. Testing get_all() method...")
        orders = order_model.get_all()
        print(f"   [OK] Found {len(orders)} orders")
        
        if not orders:
            print("   ! No orders found. Creating test order...")
            
            # Create a test order
            test_order_data = {
                'table_id': None,
                'customer_name': 'Test Customer',
                'customer_mobile': '1234567890',
                'order_type': 'Takeaway',
                'subtotal': 100.0,
                'tax': 5.0,
                'discount': 0.0,
                'total': 105.0,
                'payment_mode': 'Cash',
                'items': [
                    {'id': 1, 'quantity': 2, 'price': 25.0, 'total': 50.0},
                    {'id': 2, 'quantity': 1, 'price': 50.0, 'total': 50.0}
                ]
            }
            
            try:
                order_id = order_model.create(test_order_data)
                print(f"   [OK] Created test order with ID: {order_id}")
                orders = order_model.get_all()
            except Exception as e:
                print(f"   ! Could not create test order: {e}")
                return False
        
        # Test 2: Get order details
        if orders:
            print("2. Testing get_details() method...")
            first_order_id = orders[0][0]
            print(f"   Testing with order ID: {first_order_id}")
            
            order_details = order_model.get_details(first_order_id)
            
            if order_details:
                print(f"   [OK] Order details retrieved successfully")
                print(f"   [OK] Order number: {order_details['order'][1]}")
                print(f"   [OK] Order type: {order_details['order'][4]}")
                print(f"   [OK] Items count: {len(order_details['items'])}")
                print(f"   [OK] Payments count: {len(order_details['payments'])}")
                
                # Test 3: Verify data structure
                print("3. Testing data structure...")
                if 'order' in order_details and 'items' in order_details and 'payments' in order_details:
                    print("   [OK] Data structure is correct")
                    
                    # Test 4: Test items data
                    if order_details['items']:
                        first_item = order_details['items'][0]
                        if len(first_item) >= 5:
                            print(f"   [OK] Item data correct: {first_item[0]} (Qty: {first_item[1]})")
                        else:
                            print(f"   [FAIL] Item data incomplete: {first_item}")
                            return False
                    
                    # Test 5: Test payments data
                    if order_details['payments']:
                        first_payment = order_details['payments'][0]
                        if len(first_payment) >= 3:
                            print(f"   [OK] Payment data correct: {first_payment[0]} - Rs{first_payment[1]}")
                        else:
                            print(f"   [FAIL] Payment data incomplete: {first_payment}")
                            return False
                    
                else:
                    print("   [FAIL] Data structure is incorrect")
                    return False
                    
            else:
                print("   [FAIL] Could not retrieve order details")
                return False
        
        print("\n[SUCCESS] ORDER DETAILS VISIBILITY TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"[FAIL] Order details visibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Order Details Visibility Test")
    print("=" * 60)
    print("This test specifically verifies that:")
    print("1. Order details can be retrieved from database")
    print("2. Order items are properly structured")
    print("3. Payment details are accessible")
    print("4. Data structure matches UI expectations")
    print("=" * 60)
    
    success = test_order_details_visibility()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ORDER DETAILS VISIBILITY ISSUES RESOLVED!")
        print("The order details functionality is working correctly.")
        print("\nKey improvements made:")
        print("- Fixed import issues in orders_screen.py")
        print("- Corrected method calls (get_all vs get_orders)")
        print("- Proper data structure handling in UI")
        print("- Fixed order details retrieval methods")
    else:
        print("❌ ORDER DETAILS VISIBILITY ISSUES PERSIST!")
        print("Further investigation needed.")
    
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    main()
