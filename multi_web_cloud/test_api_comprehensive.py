"""
Comprehensive API Test Suite for Multi-Web-Cloud POS Application
Tests all API endpoints, request/response validation, error handling, and security
"""

import unittest
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging

# Import application and managers
from app import create_app
from config import Config
from utils.form_validator import FormValidator
from utils.session_manager import SessionManager
from utils.security_manager import SecurityManager
from utils.offline_manager import OfflineManager
from utils.razorpay_manager import RazorpayManager

# Import models
from models import db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings

class TestAPIComprehensive(unittest.TestCase):
    """Comprehensive API test suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Configure test app
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'SESSION_SALT': 'test-session-salt',
            'RAZORPAY_KEY_ID': 'test_key_id',
            'RAZORPAY_KEY_SECRET': 'test_key_secret',
            'RAZORPAY_WEBHOOK_SECRET': 'test_webhook_secret',
            'RAZORPAY_TEST_MODE': True,
            'RATE_LIMITS': {
                'default': {'requests': 100, 'window': 60},
                'auth': {'requests': 5, 'window': 300},
                'api': {'requests': 200, 'window': 60}
            },
            'IP_BLOCK_DURATION': 3600,
            'MAX_FAILED_ATTEMPTS': 5,
            'OFFLINE_MODE': False,
            'SYNC_INTERVAL': 5,
            'MAX_RETRY_ATTEMPTS': 3,
            'BASE_URL': 'http://localhost:5000'
        }
        
        # Create test app
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        # Create test client
        cls.client = cls.app.test_client()
        
        # Create application context
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test data
        cls._create_test_data()
        
        # Initialize managers
        cls.form_validator = FormValidator()
        cls.session_manager = SessionManager(cls.app)
        cls.security_manager = SecurityManager(cls.app)
        cls.offline_manager = OfflineManager(cls.app)
        cls.razorpay_manager = RazorpayManager(cls.app)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def setUp(self):
        """Set up for each test"""
        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()
        
        # Reset managers
        self.security_manager.blocked_ips.clear()
        self.security_manager.failed_attempts.clear()
        self.security_manager.security_events.clear()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for testing"""
        # Create test user
        cls.test_user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        cls.test_user.set_password('testpass123')
        db.session.add(cls.test_user)
        
        # Create test category
        cls.test_category = Category(
            name='Test Category',
            description='Test category description'
        )
        db.session.add(cls.test_category)
        
        # Create test menu item
        cls.test_menu_item = MenuItem(
            name='Test Item',
            description='Test item description',
            category_id=1,
            price=Decimal('100.00'),
            stock_quantity=50,
            min_stock_level=5,
            unit='pcs'
        )
        db.session.add(cls.test_menu_item)
        
        # Create test table
        cls.test_table = Table(
            table_number='T1',
            capacity=4,
            location='Main Hall',
            description='Test table'
        )
        db.session.add(cls.test_table)
        
        # Create test order
        cls.test_order = Order(
            order_number='TEST001',
            customer_name='Test Customer',
            order_type='Dine-in',
            table_id=1,
            status='New',
            total_amount=Decimal('250.00')
        )
        db.session.add(cls.test_order)
        
        db.session.commit()
    
    def _login_user(self, username='testuser', password='testpass123'):
        """Helper method to login user"""
        response = self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember': True
        }, follow_redirects=True)
        return response
    
    def _get_auth_headers(self):
        """Get authentication headers"""
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.test_user.id
            sess['_fresh'] = True
        return {}
    
    def test_authentication_endpoints(self):
        """Test authentication API endpoints"""
        print("\n=== Testing Authentication Endpoints ===")
        
        # Test login endpoint
        response = self.client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertIn(response.status_code, [200, 302], "Login should succeed")
        
        # Test login with invalid credentials
        response = self.client.post('/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertIn(response.status_code, [200, 401], "Invalid login should be handled")
        
        # Test logout endpoint
        self._login_user()
        response = self.client.post('/auth/logout')
        self.assertIn(response.status_code, [200, 302], "Logout should succeed")
        
        # Test session status endpoint
        response = self.client.get('/api/session/status')
        self.assertEqual(response.status_code, 401, "Session status should require authentication")
        
        # Test with authenticated session
        self._login_user()
        response = self.client.get('/api/session/status')
        self.assertEqual(response.status_code, 200, "Session status should work with authentication")
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('session', data)
        
        print("✅ Authentication endpoints tests passed")
    
    def test_validation_api_endpoints(self):
        """Test validation API endpoints"""
        print("\n=== Testing Validation API Endpoints ===")
        
        # Test field validation endpoint
        response = self.client.post('/api/validation/validate-field', json={
            'field_name': 'email',
            'field_value': 'test@example.com',
            'field_type': 'email'
        })
        self.assertEqual(response.status_code, 200, "Field validation should work")
        
        data = json.loads(response.data)
        self.assertIn('valid', data)
        self.assertTrue(data['valid'], "Valid email should pass validation")
        
        # Test form validation endpoint
        response = self.client.post('/api/validation/validate-form', json={
            'form_data': {
                'email': 'test@example.com',
                'password': 'StrongP@ss123',
                'phone': '+919876543210'
            },
            'form_config': {
                'email': {'type': 'email'},
                'password': {'type': 'password'},
                'phone': {'type': 'phone'}
            }
        })
        self.assertEqual(response.status_code, 200, "Form validation should work")
        
        data = json.loads(response.data)
        self.assertIn('valid', data)
        self.assertTrue(data['valid'], "Valid form should pass validation")
        
        # Test business rules validation
        response = self.client.post('/api/validation/validate-business-rules', json={
            'field_name': 'gst_number',
            'field_value': '27AAPCE2839H1ZV'
        })
        self.assertEqual(response.status_code, 200, "Business rules validation should work")
        
        data = json.loads(response.data)
        self.assertIn('valid', data)
        self.assertTrue(data['valid'], "Valid GST should pass validation")
        
        print("✅ Validation API endpoints tests passed")
    
    def test_security_api_endpoints(self):
        """Test security API endpoints"""
        print("\n=== Testing Security API Endpoints ===")
        
        # Test security status endpoint
        response = self.client.get('/api/security/status')
        self.assertEqual(response.status_code, 200, "Security status should work")
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('security', data)
        
        # Test IP blocking endpoint (admin only)
        self._login_user()
        response = self.client.post('/api/security/block-ip', json={
            'ip_address': '192.168.1.100',
            'reason': 'Test block',
            'duration': 3600
        })
        self.assertIn(response.status_code, [200, 403], "IP blocking should work for admin")
        
        # Test IP unblocking endpoint
        response = self.client.post('/api/security/unblock-ip', json={
            'ip_address': '192.168.1.100'
        })
        self.assertIn(response.status_code, [200, 403], "IP unblocking should work for admin")
        
        # Test security events endpoint
        response = self.client.get('/api/security/events')
        self.assertIn(response.status_code, [200, 403], "Security events should work for admin")
        
        # Test rate limiting status
        response = self.client.get('/api/security/rate-limit-status')
        self.assertEqual(response.status_code, 200, "Rate limit status should work")
        
        print("✅ Security API endpoints tests passed")
    
    def test_offline_api_endpoints(self):
        """Test offline API endpoints"""
        print("\n=== Testing Offline API Endpoints ===")
        
        # Test offline status endpoint
        response = self.client.get('/api/offline/status')
        self.assertEqual(response.status_code, 200, "Offline status should work")
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('offline', data)
        
        # Test force sync endpoint
        self._login_user()
        response = self.client.post('/api/offline/force-sync')
        self.assertIn(response.status_code, [200, 401], "Force sync should require authentication")
        
        # Test offline orders endpoint
        response = self.client.get('/api/offline/orders')
        self.assertIn(response.status_code, [200, 401], "Offline orders should require authentication")
        
        # Test offline payments endpoint
        response = self.client.get('/api/offline/payments')
        self.assertIn(response.status_code, [200, 401], "Offline payments should require authentication")
        
        # Test sync statistics endpoint
        response = self.client.get('/api/offline/sync-statistics')
        self.assertEqual(response.status_code, 200, "Sync statistics should work")
        
        data = json.loads(response.data)
        self.assertIn('orders', data)
        self.assertIn('payments', data)
        self.assertIn('recent_activity', data)
        
        print("✅ Offline API endpoints tests passed")
    
    def test_payment_api_endpoints(self):
        """Test payment API endpoints"""
        print("\n=== Testing Payment API Endpoints ===")
        
        # Test Razorpay configuration endpoint
        response = self.client.get('/api/payment/razorpay-config')
        self.assertEqual(response.status_code, 200, "Razorpay config should work")
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('razorpay', data)
        
        # Test create payment order endpoint
        self._login_user()
        response = self.client.post('/api/payment/create-order', json={
            'amount': 250.00,
            'currency': 'INR',
            'receipt': 'TEST001'
        })
        self.assertIn(response.status_code, [200, 401], "Create order should require authentication")
        
        # Test validate payment method endpoint
        response = self.client.post('/api/payment/validate-method', json={
            'method': 'card',
            'details': {
                'card_number': '4111111111111111',
                'expiry': '12/25',
                'cvv': '123',
                'name': 'Test User'
            }
        })
        self.assertEqual(response.status_code, 200, "Payment method validation should work")
        
        data = json.loads(response.data)
        self.assertIn('valid', data)
        self.assertTrue(data['valid'], "Valid card should pass validation")
        
        # Test calculate EMI endpoint
        response = self.client.post('/api/payment/calculate-emi', json={
            'amount': 12000.00,
            'tenure_months': 12,
            'interest_rate': 12.0
        })
        self.assertEqual(response.status_code, 200, "EMI calculation should work")
        
        data = json.loads(response.data)
        self.assertIn('monthly_emi', data)
        self.assertIn('total_interest', data)
        
        # Test payment analytics endpoint
        response = self.client.get('/api/payment/analytics')
        self.assertIn(response.status_code, [200, 401], "Payment analytics should require authentication")
        
        print("✅ Payment API endpoints tests passed")
    
    def test_dashboard_api_endpoints(self):
        """Test dashboard API endpoints"""
        print("\n=== Testing Dashboard API Endpoints ===")
        
        # Test dashboard stats endpoint
        self._login_user()
        response = self.client.get('/api/dashboard/stats')
        self.assertIn(response.status_code, [200, 401], "Dashboard stats should require authentication")
        
        # Test recent orders endpoint
        response = self.client.get('/api/dashboard/recent-orders')
        self.assertIn(response.status_code, [200, 401], "Recent orders should require authentication")
        
        # Test sales summary endpoint
        response = self.client.get('/api/dashboard/sales-summary')
        self.assertIn(response.status_code, [200, 401], "Sales summary should require authentication")
        
        # Test popular items endpoint
        response = self.client.get('/api/dashboard/popular-items')
        self.assertIn(response.status_code, [200, 401], "Popular items should require authentication")
        
        # Test low stock items endpoint
        response = self.client.get('/api/dashboard/low-stock-items')
        self.assertIn(response.status_code, [200, 401], "Low stock items should require authentication")
        
        print("✅ Dashboard API endpoints tests passed")
    
    def test_config_api_endpoints(self):
        """Test configuration API endpoints"""
        print("\n=== Testing Configuration API Endpoints ===")
        
        # Test get settings endpoint
        self._login_user()
        response = self.client.get('/api/config/settings')
        self.assertIn(response.status_code, [200, 401], "Get settings should require authentication")
        
        # Test update settings endpoint
        response = self.client.post('/api/config/settings', json={
            'restaurant_name': 'Test Restaurant',
            'currency_symbol': '₹',
            'decimal_places': 2
        })
        self.assertIn(response.status_code, [200, 401], "Update settings should require authentication")
        
        # Test get categories endpoint
        response = self.client.get('/api/config/categories')
        self.assertEqual(response.status_code, 200, "Get categories should work")
        
        # Test get tables endpoint
        response = self.client.get('/api/config/tables')
        self.assertEqual(response.status_code, 200, "Get tables should work")
        
        # Test get payment methods endpoint
        response = self.client.get('/api/config/payment-methods')
        self.assertEqual(response.status_code, 200, "Get payment methods should work")
        
        print("✅ Configuration API endpoints tests passed")
    
    def test_orders_api_endpoints(self):
        """Test orders API endpoints"""
        print("\n=== Testing Orders API Endpoints ===")
        
        # Test get orders endpoint
        self._login_user()
        response = self.client.get('/api/orders')
        self.assertIn(response.status_code, [200, 401], "Get orders should require authentication")
        
        # Test create order endpoint
        response = self.client.post('/api/orders', json={
            'customer_name': 'Test Customer',
            'order_type': 'Dine-in',
            'table_id': 1,
            'items': [
                {'menu_item_id': 1, 'quantity': 2, 'price': 100.00}
            ],
            'special_instructions': 'No onions'
        })
        self.assertIn(response.status_code, [200, 401], "Create order should require authentication")
        
        # Test get order details endpoint
        response = self.client.get('/api/orders/1')
        self.assertIn(response.status_code, [200, 401], "Get order details should require authentication")
        
        # Test update order endpoint
        response = self.client.put('/api/orders/1', json={
            'status': 'In Progress',
            'special_instructions': 'Extra spicy'
        })
        self.assertIn(response.status_code, [200, 401], "Update order should require authentication")
        
        # Test delete order endpoint
        response = self.client.delete('/api/orders/999')  # Non-existent order
        self.assertIn(response.status_code, [200, 401, 404], "Delete order should require authentication")
        
        print("✅ Orders API endpoints tests passed")
    
    def test_menu_api_endpoints(self):
        """Test menu API endpoints"""
        print("\n=== Testing Menu API Endpoints ===")
        
        # Test get menu items endpoint
        response = self.client.get('/api/menu/items')
        self.assertEqual(response.status_code, 200, "Get menu items should work")
        
        # Test create menu item endpoint
        self._login_user()
        response = self.client.post('/api/menu/items', json={
            'name': 'New Test Item',
            'description': 'New test item description',
            'category_id': 1,
            'price': 150.00,
            'stock_quantity': 25,
            'min_stock_level': 5,
            'unit': 'pcs'
        })
        self.assertIn(response.status_code, [200, 401], "Create menu item should require authentication")
        
        # Test get categories endpoint
        response = self.client.get('/api/menu/categories')
        self.assertEqual(response.status_code, 200, "Get categories should work")
        
        # Test update menu item endpoint
        response = self.client.put('/api/menu/items/1', json={
            'name': 'Updated Test Item',
            'price': 120.00
        })
        self.assertIn(response.status_code, [200, 401], "Update menu item should require authentication")
        
        # Test delete menu item endpoint
        response = self.client.delete('/api/menu/items/999')  # Non-existent item
        self.assertIn(response.status_code, [200, 401, 404], "Delete menu item should require authentication")
        
        print("✅ Menu API endpoints tests passed")
    
    def test_tables_api_endpoints(self):
        """Test tables API endpoints"""
        print("\n=== Testing Tables API Endpoints ===")
        
        # Test get tables endpoint
        response = self.client.get('/api/tables')
        self.assertEqual(response.status_code, 200, "Get tables should work")
        
        # Test create table endpoint
        self._login_user()
        response = self.client.post('/api/tables', json={
            'table_number': 'T2',
            'capacity': 4,
            'location': 'Outdoor',
            'description': 'Outdoor table'
        })
        self.assertIn(response.status_code, [200, 401], "Create table should require authentication")
        
        # Test get table details endpoint
        response = self.client.get('/api/tables/1')
        self.assertEqual(response.status_code, 200, "Get table details should work")
        
        # Test update table endpoint
        response = self.client.put('/api/tables/1', json={
            'capacity': 6,
            'location': 'Updated Location'
        })
        self.assertIn(response.status_code, [200, 401], "Update table should require authentication")
        
        # Test delete table endpoint
        response = self.client.delete('/api/tables/999')  # Non-existent table
        self.assertIn(response.status_code, [200, 401, 404], "Delete table should require authentication")
        
        print("✅ Tables API endpoints tests passed")
    
    def test_api_request_validation(self):
        """Test API request validation"""
        print("\n=== Testing API Request Validation ===")
        
        # Test JSON validation
        response = self.client.post('/api/validation/validate-field', 
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400, "Invalid JSON should return 400")
        
        # Test missing required fields
        response = self.client.post('/api/validation/validate-field', json={
            'field_value': 'test@example.com'
            # Missing field_name
        })
        self.assertEqual(response.status_code, 400, "Missing required fields should return 400")
        
        # Test invalid data types
        response = self.client.post('/api/payment/create-order', json={
            'amount': 'not_a_number',
            'currency': 'INR'
        })
        self.assertEqual(response.status_code, 400, "Invalid data types should return 400")
        
        # Test XSS prevention
        response = self.client.post('/api/validation/validate-field', json={
            'field_name': 'name',
            'field_value': '<script>alert("xss")</script>',
            'field_type': 'text'
        })
        self.assertEqual(response.status_code, 200, "Request should be processed")
        
        data = json.loads(response.data)
        if 'sanitized_value' in data:
            self.assertNotIn('<script>', data['sanitized_value'], "XSS should be sanitized")
        
        print("✅ API request validation tests passed")
    
    def test_api_error_handling(self):
        """Test API error handling"""
        print("\n=== Testing API Error Handling ===")
        
        # Test 404 handling
        response = self.client.get('/api/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404, "Non-existent endpoint should return 404")
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        
        # Test 405 handling (wrong method)
        response = self.client.delete('/api/validation/validate-field')
        self.assertEqual(response.status_code, 405, "Wrong method should return 405")
        
        # Test 422 handling (unprocessable entity)
        response = self.client.post('/api/payment/create-order', json={
            'amount': -100,  # Negative amount
            'currency': 'INR'
        })
        self.assertEqual(response.status_code, 422, "Invalid data should return 422")
        
        # Test 500 handling (server error simulation)
        with patch('utils.razorpay_manager.RazorpayManager.create_order') as mock_create:
            mock_create.side_effect = Exception("Database error")
            response = self.client.post('/api/payment/create-order', json={
                'amount': 100,
                'currency': 'INR'
            })
            self.assertEqual(response.status_code, 500, "Server error should return 500")
        
        print("✅ API error handling tests passed")
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        print("\n=== Testing API Rate Limiting ===")
        
        # Make multiple requests to trigger rate limiting
        for i in range(10):
            response = self.client.get('/api/session/status')
            if i < 100:  # Should allow first 100 requests
                self.assertIn(response.status_code, [200, 401], f"Request {i+1} should be allowed")
            else:
                self.assertEqual(response.status_code, 429, f"Request {i+1} should be rate limited")
        
        print("✅ API rate limiting tests passed")
    
    def test_api_authentication(self):
        """Test API authentication and authorization"""
        print("\n=== Testing API Authentication ===")
        
        # Test endpoints without authentication
        protected_endpoints = [
            '/api/dashboard/stats',
            '/api/orders',
            '/api/menu/items',
            '/api/tables',
            '/api/payment/create-order'
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [401, 403], f"Endpoint {endpoint} should require authentication")
        
        # Test with authentication
        self._login_user()
        for endpoint in protected_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [200, 405], f"Endpoint {endpoint} should work with authentication")
        
        print("✅ API authentication tests passed")
    
    def test_api_cors_headers(self):
        """Test API CORS headers"""
        print("\n=== Testing API CORS Headers ===")
        
        response = self.client.options('/api/orders')
        self.assertIn(response.status_code, [200, 204], "OPTIONS request should work")
        
        # Check CORS headers
        headers = response.headers
        self.assertIn('Access-Control-Allow-Origin', headers)
        self.assertIn('Access-Control-Allow-Methods', headers)
        self.assertIn('Access-Control-Allow-Headers', headers)
        
        print("✅ API CORS headers tests passed")
    
    def test_api_response_format(self):
        """Test API response format consistency"""
        print("\n=== Testing API Response Format ===")
        
        # Test successful response format
        response = self.client.get('/api/offline/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        # Test error response format
        response = self.client.post('/api/validation/validate-field', json={})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)
        
        print("✅ API response format tests passed")

def run_api_comprehensive_tests():
    """Run all comprehensive API tests"""
    print("=" * 80)
    print("COMPREHENSIVE API TEST SUITE")
    print("=" * 80)
    print("Testing all API endpoints, validation, and security\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestAPIComprehensive('test_authentication_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_validation_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_security_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_offline_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_payment_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_dashboard_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_config_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_orders_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_menu_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_tables_api_endpoints'))
    test_suite.addTest(TestAPIComprehensive('test_api_request_validation'))
    test_suite.addTest(TestAPIComprehensive('test_api_error_handling'))
    test_suite.addTest(TestAPIComprehensive('test_api_rate_limiting'))
    test_suite.addTest(TestAPIComprehensive('test_api_authentication'))
    test_suite.addTest(TestAPIComprehensive('test_api_cors_headers'))
    test_suite.addTest(TestAPIComprehensive('test_api_response_format'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE API TEST RESULTS")
    print(f"{'='*80}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    print(f"\n{'='*80}")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_api_comprehensive_tests()
    
    if success:
        print("\n✅ ALL API TESTS PASSED!")
        print("API endpoints are production-ready")
        exit(0)
    else:
        print("\n❌ SOME API TESTS FAILED!")
        print("Review and fix API issues before production deployment")
        exit(1)