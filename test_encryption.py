#!/usr/bin/env python3
"""
Test script for encryption implementation in POS system
"""

import os
import sys
import sqlite3
from src.utils.encryption import EncryptionManager, get_encryption_manager, encrypt_data, decrypt_data
from src.models.user import User
from src.models.payment import Payment

# Mock database class for testing
class MockDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.cursor = self.conn.cursor()
    
    def execute_query(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
    
    def fetch_one(self):
        return self.cursor.fetchone()
    
    def fetch_all(self):
        return self.cursor.fetchall()
    
    def lastrowid(self):
        return self.cursor.lastrowid
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()

def test_encryption_manager():
    """Test basic encryption manager functionality"""
    print("=" * 50)
    print("Testing Encryption Manager")
    print("=" * 50)
    
    try:
        # Initialize encryption manager
        encryption_manager = get_encryption_manager()
        
        # Test data
        test_data = [
            "Hello World",
            "Password123!",
            "4111111111111111",  # Test card number
            "user@upi.example.com",  # Test UPI ID
            "9876543210",  # Test mobile number
            "",  # Test empty string
            None  # Test None
        ]
        
        print("Testing encryption/decryption:")
        for data in test_data:
            try:
                if data is None:
                    print(f"  Testing None: SKIPPED (None values not encrypted)")
                    continue
                
                encrypted = encryption_manager.encrypt(data)
                decrypted = encryption_manager.decrypt(encrypted)
                
                success = data == decrypted
                status = "✓ PASS" if success else "✗ FAIL"
                
                print(f"  {status}: '{data}' -> '{encrypted[:20]}...' -> '{decrypted}'")
                
                if not success:
                    print(f"    ERROR: Original '{data}' != Decrypted '{decrypted}'")
                    
            except Exception as e:
                print(f"  ✗ FAIL: '{data}' -> ERROR: {e}")
        
        # Test key info
        print("\nEncryption key info:")
        key_info = encryption_manager.get_key_info()
        for key, value in key_info.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"Encryption manager test failed: {e}")
        return False

def test_user_encryption():
    """Test user password encryption"""
    print("\n" + "=" * 50)
    print("Testing User Password Encryption")
    print("=" * 50)
    
    try:
        # Create a test database
        test_db = MockDatabase()
        test_db.execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        """)
        
        # Create user model with test database
        user_model = User(test_db)
        
        # Test adding user with encrypted password
        test_username = "testuser"
        test_password = "TestPassword123!"
        test_role = "Admin"
        
        print(f"Adding user: {test_username}")
        success = user_model.add(test_username, test_password, test_role)
        
        if not success:
            print("✗ FAIL: Failed to add user")
            return False
        
        # Verify password is encrypted in database
        test_db.execute("SELECT password FROM users WHERE username = ?", (test_username,))
        result = test_db.fetchone()
        
        if not result:
            print("✗ FAIL: User not found in database")
            return False
        
        stored_password = result[0]
        
        # Check if password is encrypted (should not equal original)
        if stored_password == test_password:
            print("✗ FAIL: Password not encrypted in database")
            return False
        
        print(f"✓ PASS: Password encrypted (stored as: {stored_password[:20]}...)")
        
        # Test authentication
        print(f"Testing authentication for {test_username}")
        auth_result = user_model.authenticate(test_username, test_password)
        
        if not auth_result:
            print("✗ FAIL: Authentication failed")
            return False
        
        print(f"✓ PASS: Authentication successful (User ID: {auth_result[0]}, Role: {auth_result[2]})")
        
        # Test wrong password
        print("Testing authentication with wrong password")
        wrong_auth = user_model.authenticate(test_username, "WrongPassword")
        
        if wrong_auth:
            print("✗ FAIL: Authentication should have failed with wrong password")
            return False
        
        print("✓ PASS: Authentication correctly failed with wrong password")
        
        test_db.close()
        return True
        
    except Exception as e:
        print(f"User encryption test failed: {e}")
        return False

def test_payment_encryption():
    """Test payment details encryption"""
    print("\n" + "=" * 50)
    print("Testing Payment Details Encryption")
    print("=" * 50)
    
    try:
        # Create a test database
        test_db = MockDatabase()
        test_db.execute_query("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            payment_mode TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create payment model with test database
        payment_model = Payment(test_db)
        
        # Test adding payment with encrypted details
        test_order_id = 1
        test_payment_mode = "Card"
        test_amount = 100.50
        test_payment_details = {
            "card_number": "4111111111111111",
            "expiry": "12/25",
            "card_holder": "Test User"
        }
        
        print(f"Adding payment: {test_payment_mode} - Rs.{test_amount}")
        payment_id = payment_model.add_payment(
            test_order_id, 
            test_payment_mode, 
            test_amount, 
            test_payment_details
        )
        
        if not payment_id:
            print("✗ FAIL: Failed to add payment")
            return False
        
        print(f"✓ PASS: Payment added (ID: {payment_id})")
        
        # Verify payment details are encrypted in database
        test_db.execute("SELECT payment_details FROM payments WHERE id = ?", (payment_id,))
        result = test_db.fetchone()
        
        if not result:
            print("✗ FAIL: Payment not found in database")
            return False
        
        stored_details = result[0]
        
        # Check if details are encrypted (should be JSON with encrypted values)
        import json
        try:
            details_dict = json.loads(stored_details)
            
            # Card number should be encrypted
            if 'card_number' in details_dict:
                encrypted_card = details_dict['card_number']
                if encrypted_card == test_payment_details['card_number']:
                    print("✗ FAIL: Card number not encrypted in database")
                    return False
                
                print(f"✓ PASS: Card number encrypted (stored as: {encrypted_card[:20]}...)")
            
        except json.JSONDecodeError:
            print("✗ FAIL: Payment details not stored as valid JSON")
            return False
        
        # Test retrieving and decrypting payment details
        print("Testing payment details retrieval and decryption")
        retrieved_payment = payment_model.get_payment_details(payment_id)
        
        if not retrieved_payment:
            print("✗ FAIL: Failed to retrieve payment details")
            return False
        
        retrieved_details = retrieved_payment['payment_details']
        
        # Check if decrypted details match original
        if (retrieved_details.get('card_number') != test_payment_details['card_number'] or
            retrieved_details.get('expiry') != test_payment_details['expiry'] or
            retrieved_details.get('card_holder') != test_payment_details['card_holder']):
            print("✗ FAIL: Decrypted payment details don't match original")
            print(f"  Original: {test_payment_details}")
            print(f"  Retrieved: {retrieved_details}")
            return False
        
        print("✓ PASS: Payment details correctly decrypted")
        
        # Test UPI payment
        print("\nTesting UPI payment encryption")
        upi_details = {
            "upi_id": "user@upi.example.com"
        }
        
        upi_payment_id = payment_model.add_payment(
            test_order_id + 1,
            "UPI",
            50.0,
            upi_details
        )
        
        if not upi_payment_id:
            print("✗ FAIL: Failed to add UPI payment")
            return False
        
        upi_payment = payment_model.get_payment_details(upi_payment_id)
        upi_retrieved = upi_payment['payment_details']
        
        if upi_retrieved.get('upi_id') != upi_details['upi_id']:
            print("✗ FAIL: UPI ID encryption/decryption failed")
            return False
        
        print("✓ PASS: UPI ID correctly encrypted and decrypted")
        
        test_db.close()
        return True
        
    except Exception as e:
        print(f"Payment encryption test failed: {e}")
        return False

def main():
    """Run all encryption tests"""
    print("POS System Encryption Tests")
    print("=" * 50)
    
    # Run tests
    test_results = []
    
    test_results.append(("Encryption Manager", test_encryption_manager()))
    test_results.append(("User Password Encryption", test_user_encryption()))
    test_results.append(("Payment Details Encryption", test_payment_encryption()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All encryption tests passed!")
        return 0
    else:
        print("❌ Some encryption tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())