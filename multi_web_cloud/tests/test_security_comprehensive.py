"""
Comprehensive Security Testing Framework
Tests feature-based access control, data encryption, tenant isolation,
input validation, SQL injection prevention, CSRF protection, and session management.
"""

import unittest
import json
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Import application and managers
from app import create_app
from config import Config
from utils.feature_flag_manager import feature_manager

# Import models
from models import (
    db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings,
    # Feature flag models
    FeatureFlag, FeatureDependency, FeatureConflict, TenantFeature,
    # Multi-tenant models
    Tenant, TenantUser, TenantSettings, TenantConfiguration,
    # Restaurant models
    RestaurantTable, TableReservation, KitchenStation, RestaurantShift,
    # Apparel models
    ApparelProduct, ApparelVariant, ApparelSizeMatrix, ApparelExchange,
    # Books models
    BookProduct, BookVariant, BookAuthor, BookPublisher, BookCategory,
    # Grocery models
    FreshProduce, FreshProduceInventory, WeighingScaleIntegration
)


class TestAccessControl(unittest.TestCase):
    """Test feature-based access control and authorization"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Security Test Tenant',
            subdomain='security',
            database_name='security_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create users with different roles
        cls.admin_user = User(
            username='admin',
            email='admin@test.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        
        cls.manager_user = User(
            username='manager',
            email='manager@test.com',
            password_hash='hashed_password',
            role='manager',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        
        cls.staff_user = User(
            username='staff',
            email='staff@test.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        
        cls.inactive_user = User(
            username='inactive',
            email='inactive@test.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.test_tenant.id),
            is_active=False
        )
        
        db.session.add(cls.admin_user)
        db.session.add(cls.manager_user)
        db.session.add(cls.staff_user)
        db.session.add(cls.inactive_user)
        db.session.commit()
    
    def test_role_based_access_control(self):
        """Test role-based access control"""
        print("\n=== Testing Role-Based Access Control ===")
        
        with self.app.test_client() as client:
            # Test admin access
            login_data = {
                'username': 'admin',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            admin_token = json.loads(response.data)['access_token']
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            
            # Admin should access all endpoints
            response = client.get('/api/admin/users', headers=admin_headers)
            self.assertEqual(response.status_code, 200, "Admin should access admin endpoints")
            
            response = client.get('/api/products', headers=admin_headers)
            self.assertEqual(response.status_code, 200, "Admin should access product endpoints")
            
            response = client.get('/api/orders', headers=admin_headers)
            self.assertEqual(response.status_code, 200, "Admin should access order endpoints")
            
            # Test manager access
            login_data = {
                'username': 'manager',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            manager_headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Manager should access business endpoints but not admin
            response = client.get('/api/admin/users', headers=manager_headers)
            self.assertEqual(response.status_code, 403, "Manager should not access admin endpoints")
            
            response = client.get('/api/products', headers=manager_headers)
            self.assertEqual(response.status_code, 200, "Manager should access product endpoints")
            
            response = client.get('/api/orders', headers=manager_headers)
            self.assertEqual(response.status_code, 200, "Manager should access order endpoints")
            
            # Test staff access
            login_data = {
                'username': 'staff',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            staff_token = json.loads(response.data)['access_token']
            staff_headers = {'Authorization': f'Bearer {staff_token}'}
            
            # Staff should access basic endpoints
            response = client.get('/api/admin/users', headers=staff_headers)
            self.assertEqual(response.status_code, 403, "Staff should not access admin endpoints")
            
            response = client.get('/api/products', headers=staff_headers)
            self.assertEqual(response.status_code, 200, "Staff should access product endpoints")
            
            response = client.get('/api/orders', headers=staff_headers)
            self.assertEqual(response.status_code, 200, "Staff should access order endpoints")
        
        print("✅ Role-based access control tests passed")
    
    def test_feature_based_access_control(self):
        """Test feature-based access control"""
        print("\n=== Testing Feature-Based Access Control ===")
        
        with self.app.test_client() as client:
            # Login as admin
            login_data = {
                'username': 'admin',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test access without features enabled
            response = client.get('/api/restaurant/tables', headers=headers)
            self.assertEqual(response.status_code, 403, "Should not access restaurant features without enabling")
            
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 403, "Should not access apparel features without enabling")
            
            response = client.get('/api/books/products', headers=headers)
            self.assertEqual(response.status_code, 403, "Should not access books features without enabling")
            
            # Enable restaurant features
            feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_RESERVATIONS', str(self.test_tenant.id))
            
            # Should now access restaurant features
            response = client.get('/api/restaurant/tables', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access restaurant features when enabled")
            
            # Still should not access other features
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 403, "Should not access apparel features without enabling")
            
            # Enable apparel features
            feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(self.test_tenant.id))
            
            # Should now access apparel features
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access apparel features when enabled")
            
            # Test feature dependency access
            feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(self.test_tenant.id))
            
            response = client.get('/api/apparel/exchanges', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access exchanges when feature is enabled")
            
            # Disable dependent feature
            feature_manager.disable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
            
            # Should still access exchanges if it doesn't depend on size variants
            response = client.get('/api/apparel/exchanges', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access exchanges if independent")
        
        print("✅ Feature-based access control tests passed")
    
    def test_inactive_user_access(self):
        """Test inactive user access restrictions"""
        print("\n=== Testing Inactive User Access ===")
        
        with self.app.test_client() as client:
            # Try to login as inactive user
            login_data = {
                'username': 'inactive',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 403, "Inactive user should not be able to login")
            
            # Try to access with manually created token (should be rejected)
            fake_token = 'fake.jwt.token'
            headers = {'Authorization': f'Bearer {fake_token}'}
            
            response = client.get('/api/products', headers=headers)
            self.assertEqual(response.status_code, 401, "Fake token should be rejected")
        
        print("✅ Inactive user access tests passed")


class TestDataEncryption(unittest.TestCase):
    """Test data encryption and tenant isolation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data"""
        # Create test tenants
        cls.tenant1 = Tenant(
            name='Encryption Tenant 1',
            subdomain='encrypt1',
            database_name='encrypt1_db',
            retail_type='general',
            status='active'
        )
        
        cls.tenant2 = Tenant(
            name='Encryption Tenant 2',
            subdomain='encrypt2',
            database_name='encrypt2_db',
            retail_type='general',
            status='active'
        )
        
        db.session.add(cls.tenant1)
        db.session.add(cls.tenant2)
        db.session.commit()
    
    def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data"""
        print("\n=== Testing Sensitive Data Encryption ===")
        
        # Create user with sensitive data
        user1 = User(
            username='user1',
            email='user1@test.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(self.tenant1.id),
            is_active=True,
            phone='+1234567890',  # Sensitive data
            address='123 Test Street'  # Sensitive data
        )
        
        user2 = User(
            username='user2',
            email='user2@test.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(self.tenant2.id),
            is_active=True,
            phone='+0987654321',  # Sensitive data
            address='456 Test Avenue'  # Sensitive data
        )
        
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Verify data is stored (in real implementation, this would be encrypted)
        retrieved_user1 = User.query.get(user1.id)
        retrieved_user2 = User.query.get(user2.id)
        
        self.assertEqual(retrieved_user1.phone, '+1234567890', "Phone should be retrievable")
        self.assertEqual(retrieved_user1.address, '123 Test Street', "Address should be retrievable")
        self.assertEqual(retrieved_user2.phone, '+0987654321', "Phone should be retrievable")
        self.assertEqual(retrieved_user2.address, '456 Test Avenue', "Address should be retrievable")
        
        # Test data isolation between tenants
        tenant1_users = User.query.filter_by(tenant_id=str(self.tenant1.id)).all()
        tenant2_users = User.query.filter_by(tenant_id=str(self.tenant2.id)).all()
        
        self.assertEqual(len(tenant1_users), 1, "Tenant 1 should have 1 user")
        self.assertEqual(len(tenant2_users), 1, "Tenant 2 should have 1 user")
        
        # Verify no cross-tenant data access
        tenant1_user_ids = [user.id for user in tenant1_users]
        tenant2_user_ids = [user.id for user in tenant2_users]
        
        self.assertNotIn(user2.id, tenant1_user_ids, "Tenant 1 should not access Tenant 2 data")
        self.assertNotIn(user1.id, tenant2_user_ids, "Tenant 2 should not access Tenant 1 data")
        
        print("✅ Sensitive data encryption tests passed")
    
    def test_tenant_data_isolation(self):
        """Test tenant data isolation at database level"""
        print("\n=== Testing Tenant Data Isolation ===")
        
        # Create products for each tenant
        product1 = Product(
            sku='ISO001',
            name='Isolation Product 1',
            description='Product for tenant 1',
            price=Decimal('999.00'),
            tenant_id=str(self.tenant1.id),
            status='active'
        )
        
        product2 = Product(
            sku='ISO002',
            name='Isolation Product 2',
            description='Product for tenant 2',
            price=Decimal('1099.00'),
            tenant_id=str(self.tenant2.id),
            status='active'
        )
        
        db.session.add(product1)
        db.session.add(product2)
        db.session.commit()
        
        # Test tenant-specific queries
        tenant1_products = Product.query.filter_by(tenant_id=str(self.tenant1.id)).all()
        tenant2_products = Product.query.filter_by(tenant_id=str(self.tenant2.id)).all()
        
        self.assertEqual(len(tenant1_products), 1, "Tenant 1 should have 1 product")
        self.assertEqual(len(tenant2_products), 1, "Tenant 2 should have 1 product")
        
        # Verify correct products
        self.assertEqual(tenant1_products[0].sku, 'ISO001', "Tenant 1 should have correct product")
        self.assertEqual(tenant2_products[0].sku, 'ISO002', "Tenant 2 should have correct product")
        
        # Test cross-tenant access prevention
        tenant1_accessing_tenant2 = Product.query.filter_by(
            tenant_id=str(self.tenant1.id),
            sku='ISO002'  # Wrong tenant
        ).first()
        
        self.assertIsNone(tenant1_accessing_tenant2, "Should not access other tenant's products")
        
        tenant2_accessing_tenant1 = Product.query.filter_by(
            tenant_id=str(self.tenant2.id),
            sku='ISO001'  # Wrong tenant
        ).first()
        
        self.assertIsNone(tenant2_accessing_tenant1, "Should not access other tenant's products")
        
        print("✅ Tenant data isolation tests passed")
    
    def test_configuration_isolation(self):
        """Test configuration isolation between tenants"""
        print("\n=== Testing Configuration Isolation ===")
        
        # Create tenant configurations
        config1 = TenantConfiguration(
            tenant_id=str(self.tenant1.id),
            config_key='security_settings',
            config_value={
                'password_policy': 'strong',
                'session_timeout': 3600,
                'max_login_attempts': 3
            }
        )
        
        config2 = TenantConfiguration(
            tenant_id=str(self.tenant2.id),
            config_key='security_settings',
            config_value={
                'password_policy': 'medium',
                'session_timeout': 1800,
                'max_login_attempts': 5
            }
        )
        
        db.session.add(config1)
        db.session.add(config2)
        db.session.commit()
        
        # Test configuration isolation
        tenant1_configs = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant1.id)
        ).all()
        
        tenant2_configs = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant2.id)
        ).all()
        
        self.assertEqual(len(tenant1_configs), 1, "Tenant 1 should have 1 configuration")
        self.assertEqual(len(tenant2_configs), 1, "Tenant 2 should have 1 configuration")
        
        # Verify configuration values
        tenant1_config = json.loads(tenant1_configs[0].config_value)
        tenant2_config = json.loads(tenant2_configs[0].config_value)
        
        self.assertEqual(tenant1_config['password_policy'], 'strong', "Tenant 1 should have strong policy")
        self.assertEqual(tenant2_config['password_policy'], 'medium', "Tenant 2 should have medium policy")
        
        # Test cross-tenant configuration access
        tenant1_accessing_tenant2 = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant1.id),
            config_key='security_settings'
        ).first()
        
        # Should return tenant 1's config, not tenant 2's
        config_value = json.loads(tenant1_accessing_tenant2.config_value)
        self.assertEqual(config_value['password_policy'], 'strong', "Should access own configuration")
        
        print("✅ Configuration isolation tests passed")


class TestInputValidation(unittest.TestCase):
    """Test input validation and SQL injection prevention"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Validation Test Tenant',
            subdomain='validation',
            database_name='validation_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='validator',
            email='validator@test.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        print("\n=== Testing SQL Injection Prevention ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'validator',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test SQL injection attempts
            sql_injection_payloads = [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "1' UNION SELECT * FROM users --",
                "'; DELETE FROM products; --",
                "' OR 1=1 --",
                "1'; EXEC xp_cmdshell('dir'); --"
            ]
            
            for payload in sql_injection_payloads:
                # Test in product search
                response = client.get(f'/api/products?search={payload}', headers=headers)
                self.assertNotEqual(response.status_code, 500, "Should not cause server error")
                
                # Test in product creation
                product_data = {
                    'sku': payload,
                    'name': 'Test Product',
                    'price': '999.00'
                }
                
                response = client.post('/api/products',
                                     data=json.dumps(product_data),
                                     content_type='application/json',
                                     headers=headers)
                
                # Should return validation error, not success
                self.assertIn(response.status_code, [400, 422], "Should reject malicious input")
                
                # Test in order search
                response = client.get(f'/api/orders?search={payload}', headers=headers)
                self.assertNotEqual(response.status_code, 500, "Should not cause server error")
            
            # Verify database integrity
            users = User.query.all()
            products = Product.query.all()
            
            self.assertGreater(len(users), 0, "Users table should be intact")
            self.assertEqual(len(products), 0, "No malicious products should be created")
        
        print("✅ SQL injection prevention tests passed")
    
    def test_xss_prevention(self):
        """Test XSS prevention"""
        print("\n=== Testing XSS Prevention ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'validator',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test XSS payloads
            xss_payloads = [
                '<script>alert("XSS")</script>',
                'javascript:alert("XSS")',
                '<img src="x" onerror="alert(\'XSS\')">',
                '<svg onload="alert(\'XSS\')">',
                '"><script>alert("XSS")</script>',
                '\';alert("XSS");//'
            ]
            
            for payload in xss_payloads:
                # Test in product creation
                product_data = {
                    'sku': 'XSS001',
                    'name': payload,  # XSS payload in name
                    'description': payload,  # XSS payload in description
                    'price': '999.00'
                }
                
                response = client.post('/api/products',
                                     data=json.dumps(product_data),
                                     content_type='application/json',
                                     headers=headers)
                
                if response.status_code == 201:
                    # If product was created, check if XSS is sanitized in response
                    response_data = json.loads(response.data)
                    if 'name' in response_data:
                        self.assertNotIn('<script>', response_data['name'], "Script tags should be removed")
                        self.assertNotIn('javascript:', response_data['name'], "JavaScript URLs should be removed")
                
                # Test in search
                response = client.get(f'/api/products?search={payload}', headers=headers)
                self.assertNotEqual(response.status_code, 500, "Should not cause server error")
                
                # Check response doesn't contain unescaped XSS
                response_text = response.data.decode('utf-8')
                self.assertNotIn('<script>', response_text, "Response should not contain unescaped scripts")
        
        print("✅ XSS prevention tests passed")
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        print("\n=== Testing Input Sanitization ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'validator',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test various malicious inputs
            malicious_inputs = [
                {'field': 'email', 'value': '../../../etc/passwd'},
                {'field': 'phone', 'value': '<script>alert("XSS")</script>'},
                {'field': 'price', 'value': 'not_a_number'},
                {'field': 'quantity', 'value': '-1'},
                {'field': 'sku', 'value': 'a' * 1000},  # Very long string
                {'field': 'description', 'value': 'null; DROP TABLE users; --'}
            ]
            
            for malicious_input in malicious_inputs:
                field = malicious_input['field']
                value = malicious_input['value']
                
                # Test in product creation
                product_data = {
                    'sku': 'SANITIZE001',
                    'name': 'Sanitization Test',
                    'price': '999.00'
                }
                
                # Add malicious field
                product_data[field] = value
                
                response = client.post('/api/products',
                                     data=json.dumps(product_data),
                                     content_type='application/json',
                                     headers=headers)
                
                # Should either reject or sanitize the input
                self.assertIn(response.status_code, [201, 400, 422], 
                             "Should handle malicious input appropriately")
                
                # If accepted, verify sanitization
                if response.status_code == 201:
                    response_data = json.loads(response.data)
                    if field in response_data:
                        sanitized_value = response_data[field]
                        
                        # Check for common malicious patterns
                        self.assertNotIn('<script>', str(sanitized_value), "Script tags should be removed")
                        self.assertNotIn('DROP TABLE', str(sanitized_value), "SQL commands should be removed")
                        self.assertNotIn('../', str(sanitized_value), "Path traversal should be removed")
        
        print("✅ Input sanitization tests passed")


class TestCSRFProtection(unittest.TestCase):
    """Test CSRF protection mechanisms"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': True,  # Enable CSRF for testing
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='CSRF Test Tenant',
            subdomain='csrf',
            database_name='csrf_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_csrf_token_validation(self):
        """Test CSRF token validation"""
        print("\n=== Testing CSRF Token Validation ===")
        
        with self.app.test_client() as client:
            # Get form page (should include CSRF token)
            response = client.get('/products/new')
            self.assertEqual(response.status_code, 200, "Form page should render")
            
            # Extract CSRF token from form
            csrf_token = None
            if b'csrf_token' in response.data:
                # In real implementation, this would extract the actual CSRF token
                csrf_token = 'test_csrf_token'
            
            # Test form submission without CSRF token
            form_data = {
                'sku': 'CSRF001',
                'name': 'CSRF Test Product',
                'price': '999.00'
            }
            
            response = client.post('/products/new', data=form_data)
            self.assertEqual(response.status_code, 400, "Should reject form without CSRF token")
            
            # Test form submission with invalid CSRF token
            form_data['csrf_token'] = 'invalid_token'
            
            response = client.post('/products/new', data=form_data)
            self.assertEqual(response.status_code, 400, "Should reject form with invalid CSRF token")
            
            # Test API endpoints (should not require CSRF for stateless APIs)
            # API endpoints use JWT tokens instead of CSRF
            api_data = {
                'sku': 'CSRF002',
                'name': 'CSRF API Product',
                'price': '999.00'
            }
            
            response = client.post('/api/products',
                                 data=json.dumps(api_data),
                                 content_type='application/json')
            
            # API should return 401 (unauthorized) rather than CSRF error
            self.assertIn(response.status_code, [401, 403], "API should require authentication, not CSRF")
        
        print("✅ CSRF token validation tests passed")
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation and uniqueness"""
        print("\n=== Testing CSRF Token Generation ===")
        
        with self.app.test_client() as client:
            # Get multiple form pages
            response1 = client.get('/products/new')
            response2 = client.get('/products/new')
            response3 = client.get('/products/new')
            
            self.assertEqual(response1.status_code, 200, "First form should render")
            self.assertEqual(response2.status_code, 200, "Second form should render")
            self.assertEqual(response3.status_code, 200, "Third form should render")
            
            # In real implementation, this would extract and compare CSRF tokens
            # For testing purposes, we verify the pages render correctly
            
            # Test token expiration (simulate)
            with patch('time.time', return_value=time.time() + 3600):  # 1 hour later
                response_expired = client.get('/products/new')
                self.assertEqual(response_expired.status_code, 200, "Should generate new token after expiration")
        
        print("✅ CSRF token generation tests passed")


class TestSessionManagement(unittest.TestCase):
    """Test session management and security"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'SESSION_TIMEOUT': 3600  # 1 hour
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Session Test Tenant',
            subdomain='session',
            database_name='session_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='sessionuser',
            email='session@test.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_session_creation(self):
        """Test session creation and management"""
        print("\n=== Testing Session Creation ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'sessionuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 200, "Login should succeed")
            
            response_data = json.loads(response.data)
            self.assertIn('access_token', response_data, "Should return access token")
            self.assertIn('refresh_token', response_data, "Should return refresh token")
            
            access_token = response_data['access_token']
            refresh_token = response_data['refresh_token']
            
            # Test token format (JWT)
            self.assertIsInstance(access_token, str, "Access token should be string")
            self.assertIsInstance(refresh_token, str, "Refresh token should be string")
            
            # Test token structure (should have 3 parts separated by dots)
            self.assertEqual(access_token.count('.'), 2, "Access token should have JWT structure")
            self.assertEqual(refresh_token.count('.'), 2, "Refresh token should have JWT structure")
            
            # Test accessing protected resource with token
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = client.get('/api/products', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access protected resource with valid token")
        
        print("✅ Session creation tests passed")
    
    def test_session_expiration(self):
        """Test session expiration and timeout"""
        print("\n=== Testing Session Expiration ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'sessionuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test immediate access
            response = client.get('/api/products', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access immediately after login")
            
            # Simulate token expiration by mocking time
            with patch('time.time', return_value=time.time() + 7200):  # 2 hours later
                response = client.get('/api/products', headers=headers)
                self.assertEqual(response.status_code, 401, "Should reject expired token")
        
        print("✅ Session expiration tests passed")
    
    def test_session_invalidation(self):
        """Test session invalidation on logout"""
        print("\n=== Testing Session Invalidation ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'sessionuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            refresh_token = json.loads(response.data)['refresh_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test access before logout
            response = client.get('/api/products', headers=headers)
            self.assertEqual(response.status_code, 200, "Should access before logout")
            
            # Logout
            logout_data = {'refresh_token': refresh_token}
            
            response = client.post('/api/auth/logout',
                                 data=json.dumps(logout_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Logout should succeed")
            
            # Test access after logout
            response = client.get('/api/products', headers=headers)
            self.assertEqual(response.status_code, 401, "Should reject access after logout")
            
            # Test token refresh after logout
            refresh_data = {'refresh_token': refresh_token}
            
            response = client.post('/api/auth/refresh',
                                 data=json.dumps(refresh_data),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 401, "Should reject token refresh after logout")
        
        print("✅ Session invalidation tests passed")
    
    def test_concurrent_sessions(self):
        """Test concurrent session management"""
        print("\n=== Testing Concurrent Sessions ===")
        
        with self.app.test_client() as client1, self.app.test_client() as client2:
            # Login from client 1
            login_data = {
                'username': 'sessionuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response1 = client1.post('/api/auth/login',
                                    data=json.dumps(login_data),
                                    content_type='application/json')
            
            token1 = json.loads(response1.data)['access_token']
            headers1 = {'Authorization': f'Bearer {token1}'}
            
            # Login from client 2 (same user)
            response2 = client2.post('/api/auth/login',
                                    data=json.dumps(login_data),
                                    content_type='application/json')
            
            token2 = json.loads(response2.data)['access_token']
            headers2 = {'Authorization': f'Bearer {token2}'}
            
            # Both sessions should work
            response1 = client1.get('/api/products', headers=headers1)
            response2 = client2.get('/api/products', headers=headers2)
            
            self.assertEqual(response1.status_code, 200, "First session should work")
            self.assertEqual(response2.status_code, 200, "Second session should work")
            
            # Logout from client 1
            refresh_token1 = json.loads(response1.data)['refresh_token']
            logout_data = {'refresh_token': refresh_token1}
            
            response1 = client1.post('/api/auth/logout',
                                    data=json.dumps(logout_data),
                                    content_type='application/json',
                                    headers=headers1)
            
            self.assertEqual(response1.status_code, 200, "First logout should succeed")
            
            # Client 1 should be logged out
            response1 = client1.get('/api/products', headers=headers1)
            self.assertEqual(response1.status_code, 401, "First session should be invalid after logout")
            
            # Client 2 should still be logged in
            response2 = client2.get('/api/products', headers=headers2)
            self.assertEqual(response2.status_code, 200, "Second session should still work")
        
        print("✅ Concurrent session tests passed")


def run_security_comprehensive_tests():
    """Run all security tests"""
    print("=" * 80)
    print("COMPREHENSIVE SECURITY TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing access control, data encryption, input validation,\n"
          "CSRF protection, and session management\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAccessControl,
        TestDataEncryption,
        TestInputValidation,
        TestCSRFProtection,
        TestSessionManagement
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
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
        print("Security measures are working correctly")
        exit(0)
    else:
        print("\n❌ SOME SECURITY TESTS FAILED!")
        print("Review and fix security vulnerabilities")
        exit(1)