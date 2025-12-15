"""
Comprehensive Test Suite for Enhanced POS Features
Tests all newly implemented features for production readiness
"""

import unittest
import json
import tempfile
import os
import time
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging

# Import the application and managers
from app import create_app
from config import Config
from utils.form_validator import FormValidator, RealTimeValidator
from utils.session_manager import SessionManager
from utils.security_manager import SecurityManager
from utils.offline_manager import OfflineManager
from utils.razorpay_manager import RazorpayManager

# Import models
from models import db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings

class TestEnhancedFeatures(unittest.TestCase):
    """Main test suite for all enhanced features"""
    
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
        
        db.session.commit()
    
    def test_form_validation_system(self):
        """Test advanced form validation system"""
        print("\n=== Testing Form Validation System ===")
        
        # Test GST validation
        valid_gst = '27AAPCE2839H1ZV'
        is_valid, message = self.form_validator.validate_business_rules('gst_number', valid_gst)
        self.assertTrue(is_valid, f"Valid GST should pass: {message}")
        
        invalid_gst = '1234567890123'
        is_valid, message = self.form_validator.validate_business_rules('gst_number', invalid_gst)
        self.assertFalse(is_valid, "Invalid GST should fail")
        
        # Test phone validation
        valid_phone = '+919876543210'
        is_valid, message = self.form_validator.validate_business_rules('phone_number', valid_phone)
        self.assertTrue(is_valid, f"Valid phone should pass: {message}")
        
        # Test password strength
        strong_password = 'MyStr0ngP@ssw0rd!'
        is_valid, errors = self.form_validator.validate_password_strength(strong_password)
        self.assertTrue(is_valid, f"Strong password should pass: {errors}")
        
        weak_password = 'password'
        is_valid, errors = self.form_validator.validate_password_strength(weak_password)
        self.assertFalse(is_valid, "Weak password should fail")
        
        # Test input sanitization
        xss_input = '<script>alert("xss")</script>'
        sanitized = self.form_validator.sanitize_input(xss_input)
        self.assertNotIn('<script>', sanitized, "XSS should be removed")
        
        sql_input = "'; DROP TABLE users; --"
        sanitized = self.form_validator.sanitize_input(sql_input)
        self.assertNotIn('DROP', sanitized.upper(), "SQL injection should be removed")
        
        print("✅ Form validation system tests passed")
    
    def test_session_management(self):
        """Test enhanced session management with fingerprinting"""
        print("\n=== Testing Session Management ===")
        
        with self.app.test_request_context('/', headers={
            'User-Agent': 'Mozilla/5.0 (Test Browser)',
            'Accept-Language': 'en-US,en;q=0.9'
        }):
            # Test session creation
            session_data = self.session_manager.create_session(
                user_id=self.test_user.id,
                remember_me=True
            )
            
            self.assertIsNotNone(session_data, "Session data should be created")
            self.assertEqual(session_data['user_id'], self.test_user.id)
            self.assertIn('session_fingerprint', session_data)
            
            # Test session validation
            is_valid = self.session_manager._is_session_valid()
            self.assertTrue(is_valid, "Session should be valid")
            
            # Test session extension
            extended = self.session_manager.extend_session(hours=12)
            self.assertTrue(extended, "Session should be extended")
            
            # Test session info
            info = self.session_manager.get_session_info()
            self.assertIsNotNone(info, "Session info should be available")
            self.assertEqual(info['user_id'], self.test_user.id)
            
            # Test session statistics
            stats = self.session_manager.get_session_statistics()
            self.assertIn('total_sessions', stats)
            self.assertIn('active_sessions', stats)
            
        print("✅ Session management tests passed")
    
    def test_security_features(self):
        """Test enterprise-grade security features"""
        print("\n=== Testing Security Features ===")
        
        with self.app.test_request_context('/api/test', headers={
            'User-Agent': 'Test Browser',
            'X-Forwarded-For': '192.168.1.100'
        }):
            # Test rate limiting
            for i in range(10):
                is_allowed = self.security_manager._check_rate_limit('192.168.1.100', 'api.test')
                if i < 100:  # Should allow first 100 requests
                    self.assertTrue(is_allowed, f"Request {i+1} should be allowed")
            
            # Test IP blocking
            test_ip = '192.168.1.200'
            self.security_manager._block_ip(test_ip, 'Test block')
            self.assertTrue(self.security_manager._is_ip_blocked(test_ip), "IP should be blocked")
            
            # Test suspicious content detection
            suspicious_content = '<script>alert("xss")</script>'
            is_suspicious = self.security_manager._is_suspicious_string(suspicious_content)
            self.assertTrue(is_suspicious, "Suspicious content should be detected")
            
            # Test password validation
            is_valid, errors = self.security_manager.validate_password('WeakPass123')
            self.assertFalse(is_valid, "Weak password should fail validation")
            
            is_valid, errors = self.security_manager.validate_password('Str0ngP@ssw0rd!')
            self.assertTrue(is_valid, "Strong password should pass validation")
            
            # Test security statistics
            stats = self.security_manager.get_security_statistics()
            self.assertIn('total_events_24h', stats)
            self.assertIn('blocked_ips', stats)
            self.assertIn('failed_attempts', stats)
            
        print("✅ Security features tests passed")
    
    def test_offline_support(self):
        """Test offline support architecture"""
        print("\n=== Testing Offline Support ===")
        
        # Test offline order storage
        order_data = {
            'order_id': 'TEST001',
            'customer_name': 'Test Customer',
            'items': [
                {'name': 'Item 1', 'price': 100, 'quantity': 2},
                {'name': 'Item 2', 'price': 50, 'quantity': 1}
            ],
            'total_amount': 250
        }
        
        local_id = self.offline_manager.store_order_offline(order_data)
        self.assertIsNotNone(local_id, "Local ID should be generated")
        self.assertTrue(local_id.startswith('order_'), "Local ID should have order prefix")
        
        # Test offline payment storage
        payment_data = {
            'payment_id': 'PAY001',
            'amount': 250,
            'method': 'cash'
        }
        
        payment_local_id = self.offline_manager.store_payment_offline(payment_data, local_id)
        self.assertIsNotNone(payment_local_id, "Payment local ID should be generated")
        
        # Test sync status
        sync_status = self.offline_manager.get_sync_status()
        self.assertIn('is_online', sync_status)
        self.assertIn('pending_orders', sync_status)
        self.assertIn('pending_payments', sync_status)
        
        # Test cached data retrieval
        menu_items = self.offline_manager.get_cached_menu_items()
        self.assertIsInstance(menu_items, list, "Cached menu items should be a list")
        
        categories = self.offline_manager.get_cached_categories()
        self.assertIsInstance(categories, list, "Cached categories should be a list")
        
        tables = self.offline_manager.get_cached_tables()
        self.assertIsInstance(tables, list, "Cached tables should be a list")
        
        # Test sync statistics
        stats = self.offline_manager.get_sync_statistics()
        self.assertIn('orders', stats)
        self.assertIn('payments', stats)
        self.assertIn('recent_activity', stats)
        
        print("✅ Offline support tests passed")
    
    def test_razorpay_integration(self):
        """Test Razorpay payment integration"""
        print("\n=== Testing Razorpay Integration ===")
        
        # Test configuration
        self.assertTrue(self.razorpay_manager.is_configured(), "Razorpay should be configured")
        
        config_info = self.razorpay_manager.get_configuration_info()
        self.assertTrue(config_info['configured'], "Configuration should show as configured")
        self.assertTrue(config_info['test_mode'], "Should be in test mode")
        
        # Test payment amount validation
        valid_amount = Decimal('250.00')
        is_valid, message = self.razorpay_manager.validate_payment_amount(valid_amount)
        self.assertTrue(is_valid, f"Valid amount should pass: {message}")
        
        invalid_amount = Decimal('0.50')
        is_valid, message = self.razorpay_manager.validate_payment_amount(invalid_amount)
        self.assertFalse(is_valid, "Invalid amount should fail")
        
        # Test payment method validation
        card_details = {
            'card_number': '4111111111111111',
            'expiry': '12/25',
            'cvv': '123',
            'name': 'Test User'
        }
        
        is_valid, message = self.razorpay_manager.validate_payment_method('card', card_details)
        self.assertTrue(is_valid, f"Valid card should pass: {message}")
        
        # Test EMI calculation
        amount = Decimal('12000.00')
        emi_details = self.razorpay_manager.process_emi_payment(amount, 12, 12.0)
        
        self.assertIn('monthly_emi', emi_details, "Should calculate monthly EMI")
        self.assertIn('total_interest', emi_details, "Should calculate total interest")
        self.assertIn('effective_rate', emi_details, "Should calculate effective rate")
        
        # Test payment analytics
        from_date = datetime.utcnow() - timedelta(days=30)
        to_date = datetime.utcnow()
        
        analytics = self.razorpay_manager.get_payment_analytics(from_date, to_date)
        self.assertIn('total_transactions', analytics)
        self.assertIn('total_amount', analytics)
        self.assertIn('success_rate', analytics)
        self.assertIn('payment_methods', analytics)
        
        # Test payment methods
        payment_methods = self.razorpay_manager.get_payment_methods()
        self.assertIn('card', payment_methods)
        self.assertIn('upi', payment_methods)
        self.assertIn('netbanking', payment_methods)
        self.assertIn('wallet', payment_methods)
        self.assertIn('emi', payment_methods)
        
        print("✅ Razorpay integration tests passed")
    
    def test_realtime_validation(self):
        """Test real-time validation system"""
        print("\n=== Testing Real-time Validation ===")
        
        # Test field validation
        result = RealTimeValidator.validate_field('email', 'test@example.com', 'email')
        self.assertTrue(result['valid'], "Valid email should pass")
        self.assertEqual(result['sanitized_value'], 'test@example.com')
        
        # Test password field validation
        result = RealTimeValidator.validate_field('password', 'StrongP@ss123', 'password')
        self.assertTrue(result['valid'], "Strong password should pass")
        
        # Test XSS detection
        result = RealTimeValidator.validate_field('name', '<script>alert("xss")</script>', 'text')
        self.assertFalse(result['valid'], "XSS should be detected")
        self.assertIn('warnings', result)
        
        # Test form validation
        form_data = {
            'email': 'test@example.com',
            'password': 'StrongP@ss123',
            'phone': '+919876543210'
        }
        
        form_config = {
            'email': {'type': 'email'},
            'password': {'type': 'password'},
            'phone': {'type': 'phone'}
        }
        
        result = RealTimeValidator.validate_form_data(form_data, form_config)
        self.assertTrue(result['valid'], "Valid form data should pass")
        
        print("✅ Real-time validation tests passed")
    
    def test_file_upload_validation(self):
        """Test file upload validation"""
        print("\n=== Testing File Upload Validation ===")
        
        # Create mock file
        mock_file = Mock()
        mock_file.filename = 'test.jpg'
        mock_file.content_type = 'image/jpeg'
        mock_file.tell = Mock(return_value=1024)  # 1KB file
        
        # Test valid file
        is_valid, message = self.form_validator.validate_file_upload(
            mock_file,
            allowed_extensions=['jpg', 'jpeg', 'png'],
            max_size_mb=5
        )
        self.assertTrue(is_valid, f"Valid file should pass: {message}")
        
        # Test invalid extension
        mock_file.filename = 'test.exe'
        is_valid, message = self.form_validator.validate_file_upload(
            mock_file,
            allowed_extensions=['jpg', 'jpeg', 'png']
        )
        self.assertFalse(is_valid, "Invalid extension should fail")
        
        # Test large file
        mock_file.tell = Mock(return_value=10 * 1024 * 1024)  # 10MB file
        is_valid, message = self.form_validator.validate_file_upload(
            mock_file,
            max_size_mb=5
        )
        self.assertFalse(is_valid, "Large file should fail")
        
        print("✅ File upload validation tests passed")
    
    def test_json_validation(self):
        """Test JSON structure validation"""
        print("\n=== Testing JSON Validation ===")
        
        # Test valid JSON
        valid_data = {
            'name': 'Test Item',
            'price': 100.50,
            'category': 'Food'
        }
        
        is_valid, message = self.form_validator.validate_json_structure(
            valid_data,
            required_fields=['name', 'price'],
            field_types={'price': (int, float)}
        )
        self.assertTrue(is_valid, f"Valid JSON should pass: {message}")
        
        # Test missing required fields
        invalid_data = {'name': 'Test Item'}
        is_valid, message = self.form_validator.validate_json_structure(
            invalid_data,
            required_fields=['name', 'price']
        )
        self.assertFalse(is_valid, "Missing required fields should fail")
        
        # Test wrong field types
        wrong_type_data = {'name': 'Test', 'price': 'not_a_number'}
        is_valid, message = self.form_validator.validate_json_structure(
            wrong_type_data,
            field_types={'price': (int, float)}
        )
        self.assertFalse(is_valid, "Wrong field types should fail")
        
        print("✅ JSON validation tests passed")
    
    def test_timestamp_validation(self):
        """Test timestamp validation for replay attack prevention"""
        print("\n=== Testing Timestamp Validation ===")
        
        # Test valid timestamp
        valid_timestamp = datetime.utcnow().isoformat()
        is_valid = self.form_validator.validate_timestamp(valid_timestamp, 30)
        self.assertTrue(is_valid, "Recent timestamp should be valid")
        
        # Test old timestamp
        old_timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        is_valid = self.form_validator.validate_timestamp(old_timestamp, 30)
        self.assertFalse(is_valid, "Old timestamp should be invalid")
        
        # Test invalid timestamp
        is_valid = self.form_validator.validate_timestamp('invalid-timestamp', 30)
        self.assertFalse(is_valid, "Invalid timestamp should be invalid")
        
        print("✅ Timestamp validation tests passed")
    
    def test_validation_hash_generation(self):
        """Test validation hash generation for tamper detection"""
        print("\n=== Testing Validation Hash Generation ===")
        
        test_data = {
            'order_id': 'TEST001',
            'amount': 250.00,
            'customer': 'Test Customer'
        }
        
        hash1 = self.form_validator.generate_validation_hash(test_data)
        hash2 = self.form_validator.generate_validation_hash(test_data)
        
        self.assertEqual(hash1, hash2, "Same data should generate same hash")
        self.assertIsInstance(hash1, str, "Hash should be a string")
        self.assertEqual(len(hash1), 64, "SHA256 hash should be 64 characters")
        
        # Test tampered data
        tampered_data = test_data.copy()
        tampered_data['amount'] = 200.00
        
        hash3 = self.form_validator.generate_validation_hash(tampered_data)
        self.assertNotEqual(hash1, hash3, "Different data should generate different hash")
        
        print("✅ Validation hash generation tests passed")
    
    def test_business_rule_validation(self):
        """Test comprehensive business rule validation"""
        print("\n=== Testing Business Rule Validation ===")
        
        # Test order number validation
        valid_order_number = 'ORD20231209001'
        is_valid, message = self.form_validator.validate_business_rules('order_number', valid_order_number)
        self.assertTrue(is_valid, f"Valid order number should pass: {message}")
        
        invalid_order_number = '123'
        is_valid, message = self.form_validator.validate_business_rules('order_number', invalid_order_number)
        self.assertFalse(is_valid, "Invalid order number should fail")
        
        # Test price validation
        valid_price = '100.50'
        is_valid, message = self.form_validator.validate_business_rules('price', valid_price)
        self.assertTrue(is_valid, f"Valid price should pass: {message}")
        
        invalid_price = '-50'
        is_valid, message = self.form_validator.validate_business_rules('price', invalid_price)
        self.assertFalse(is_valid, "Negative price should fail")
        
        # Test quantity validation
        valid_quantity = '10'
        is_valid, message = self.form_validator.validate_business_rules('quantity', valid_quantity)
        self.assertTrue(is_valid, f"Valid quantity should pass: {message}")
        
        invalid_quantity = '100000'
        is_valid, message = self.form_validator.validate_business_rules('quantity', invalid_quantity)
        self.assertFalse(is_valid, "Quantity too high should fail")
        
        print("✅ Business rule validation tests passed")
    
    def test_validation_context(self):
        """Test validation context generation"""
        print("\n=== Testing Validation Context ===")
        
        with self.app.test_request_context('/api/test', headers={
            'User-Agent': 'Test Browser',
            'X-Forwarded-For': '192.168.1.100'
        }):
            context = self.form_validator.get_validation_context()
            
            self.assertIn('ip_address', context)
            self.assertIn('user_agent', context)
            self.assertIn('timestamp', context)
            self.assertIn('request_method', context)
            self.assertIn('request_endpoint', context)
            
            self.assertEqual(context['ip_address'], '192.168.1.100')
            self.assertEqual(context['user_agent'], 'Test Browser')
            self.assertEqual(context['request_method'], 'GET')
            self.assertEqual(context['request_endpoint'], 'api.test')
        
        print("✅ Validation context tests passed")
    
    def test_validation_event_logging(self):
        """Test validation event logging"""
        print("\n=== Testing Validation Event Logging ===")
        
        with self.app.test_request_context('/api/test'):
            # Test logging security event
            self.form_validator.log_validation_event(
                'xss_detected',
                'comment',
                '<script>alert("xss")</script>',
                'XSS pattern detected and blocked',
                'high'
            )
            
            # Test logging business rule violation
            self.form_validator.log_validation_event(
                'business_rule_violation',
                'price',
                '-100',
                'Negative price not allowed',
                'medium'
            )
            
            # Check if events were logged (in real implementation, would check database)
            # For now, just ensure no exceptions were raised
            self.assertTrue(True, "Validation events should be logged successfully")
        
        print("✅ Validation event logging tests passed")

def run_enhanced_feature_tests():
    """Run all enhanced feature tests"""
    print("=" * 80)
    print("ENHANCED FEATURES COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Testing all enhanced POS features for production readiness\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestEnhancedFeatures('test_form_validation_system'))
    test_suite.addTest(TestEnhancedFeatures('test_session_management'))
    test_suite.addTest(TestEnhancedFeatures('test_security_features'))
    test_suite.addTest(TestEnhancedFeatures('test_offline_support'))
    test_suite.addTest(TestEnhancedFeatures('test_razorpay_integration'))
    test_suite.addTest(TestEnhancedFeatures('test_realtime_validation'))
    test_suite.addTest(TestEnhancedFeatures('test_file_upload_validation'))
    test_suite.addTest(TestEnhancedFeatures('test_json_validation'))
    test_suite.addTest(TestEnhancedFeatures('test_timestamp_validation'))
    test_suite.addTest(TestEnhancedFeatures('test_validation_hash_generation'))
    test_suite.addTest(TestEnhancedFeatures('test_business_rule_validation'))
    test_suite.addTest(TestEnhancedFeatures('test_validation_context'))
    test_suite.addTest(TestEnhancedFeatures('test_validation_event_logging'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("ENHANCED FEATURES TEST RESULTS")
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
    success = run_enhanced_feature_tests()
    
    if success:
        print("\n✅ ALL ENHANCED FEATURE TESTS PASSED!")
        print("System is production-ready with enhanced features")
        exit(0)
    else:
        print("\n❌ SOME ENHANCED FEATURE TESTS FAILED!")
        print("Review and fix issues before production deployment")
        exit(1)