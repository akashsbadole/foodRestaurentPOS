"""
Comprehensive API Testing Framework
Tests all API endpoints with different feature combinations,
access control, error handling, and validation.
"""

import unittest
import json
import tempfile
import os
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


class TestAPIAuthentication(unittest.TestCase):
    """Test API authentication and authorization"""
    
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
            name='API Test Tenant',
            subdomain='api-test',
            database_name='api_test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test users
        cls.admin_user = User(
            username='admin',
            email='admin@test.com',
            password_hash='hashed_password',
            role='admin',
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
        db.session.add(cls.staff_user)
        db.session.add(cls.inactive_user)
        db.session.commit()
    
    def test_login_endpoint(self):
        """Test API login endpoint"""
        print("\n=== Testing API Login Endpoint ===")
        
        with self.app.test_client() as client:
            # Test successful login
            login_data = {
                'username': 'admin',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login', 
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 200, "Login should succeed")
            response_data = json.loads(response.data)
            self.assertIn('access_token', response_data, "Should return access token")
            self.assertIn('user', response_data, "Should return user data")
            
            # Test invalid credentials
            invalid_login = {
                'username': 'admin',
                'password': 'wrong_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(invalid_login),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 401, "Invalid login should return 401")
            
            # Test inactive user login
            inactive_login = {
                'username': 'inactive',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(inactive_login),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 403, "Inactive user login should return 403")
            
            # Test missing tenant
            no_tenant_login = {
                'username': 'admin',
                'password': 'test_password'
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(no_tenant_login),
                                 content_type='application/json')
            
            self.assertEqual(response.status_code, 400, "Missing tenant should return 400")
        
        print("✅ API login endpoint tests passed")
    
    def test_token_validation(self):
        """Test API token validation"""
        print("\n=== Testing API Token Validation ===")
        
        with self.app.test_client() as client:
            # Login to get token
            login_data = {
                'username': 'admin',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            
            # Test valid token
            headers = {'Authorization': f'Bearer {token}'}
            response = client.get('/api/auth/validate', headers=headers)
            
            self.assertEqual(response.status_code, 200, "Valid token should pass validation")
            
            # Test invalid token
            invalid_headers = {'Authorization': 'Bearer invalid_token'}
            response = client.get('/api/auth/validate', headers=invalid_headers)
            
            self.assertEqual(response.status_code, 401, "Invalid token should return 401")
            
            # Test missing token
            response = client.get('/api/auth/validate')
            
            self.assertEqual(response.status_code, 401, "Missing token should return 401")
        
        print("✅ API token validation tests passed")
    
    def test_role_based_access(self):
        """Test role-based access control"""
        print("\n=== Testing Role-Based Access Control ===")
        
        with self.app.test_client() as client:
            # Admin login
            admin_login = {
                'username': 'admin',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(admin_login),
                                 content_type='application/json')
            
            admin_token = json.loads(response.data)['access_token']
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            
            # Staff login
            staff_login = {
                'username': 'staff',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(staff_login),
                                 content_type='application/json')
            
            staff_token = json.loads(response.data)['access_token']
            staff_headers = {'Authorization': f'Bearer {staff_token}'}
            
            # Test admin-only endpoint
            response = client.get('/api/admin/users', headers=admin_headers)
            self.assertEqual(response.status_code, 200, "Admin should access admin endpoints")
            
            response = client.get('/api/admin/users', headers=staff_headers)
            self.assertEqual(response.status_code, 403, "Staff should not access admin endpoints")
            
            # Test staff endpoint
            response = client.get('/api/orders', headers=staff_headers)
            self.assertEqual(response.status_code, 200, "Staff should access staff endpoints")
        
        print("✅ Role-based access control tests passed")


class TestFeatureProtectedAPIs(unittest.TestCase):
    """Test APIs protected by feature flags"""
    
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
            name='Feature API Test Tenant',
            subdomain='feature-api-test',
            database_name='feature_api_test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_restaurant_feature_apis(self):
        """Test restaurant feature-protected APIs"""
        print("\n=== Testing Restaurant Feature APIs ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'testuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test API without feature enabled
            response = client.get('/api/restaurant/tables', headers=headers)
            self.assertEqual(response.status_code, 403, "API should be disabled without feature")
            
            # Enable restaurant features
            feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_RESERVATIONS', str(self.test_tenant.id))
            
            # Test API with feature enabled
            response = client.get('/api/restaurant/tables', headers=headers)
            self.assertEqual(response.status_code, 200, "API should work with feature enabled")
            
            # Test table creation
            table_data = {
                'table_number': 'T1',
                'capacity': 4,
                'location': 'Main Area'
            }
            
            response = client.post('/api/restaurant/tables',
                                 data=json.dumps(table_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Table creation should succeed")
            
            # Test reservation API
            reservation_data = {
                'table_number': 'T1',
                'customer_name': 'Test Customer',
                'customer_phone': '+1234567890',
                'reservation_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'party_size': 4
            }
            
            response = client.post('/api/restaurant/reservations',
                                 data=json.dumps(reservation_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Reservation creation should succeed")
        
        print("✅ Restaurant feature API tests passed")
    
    def test_apparel_feature_apis(self):
        """Test apparel feature-protected APIs"""
        print("\n=== Testing Apparel Feature APIs ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'testuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test API without feature enabled
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 403, "API should be disabled without feature")
            
            # Enable apparel features
            feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(self.test_tenant.id))
            
            # Test API with feature enabled
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 200, "API should work with feature enabled")
            
            # Test product creation
            product_data = {
                'sku': 'APP001',
                'name': 'Test Apparel Product',
                'category': 'Clothing',
                'base_price': '999.00',
                'description': 'Test apparel product'
            }
            
            response = client.post('/api/apparel/products',
                                 data=json.dumps(product_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Product creation should succeed")
            
            # Test variant creation
            variant_data = {
                'sku': 'APP001-M-RED',
                'size': 'M',
                'color': 'Red',
                'price': '1049.00',
                'stock_quantity': 10
            }
            
            response = client.post('/api/apparel/variants',
                                 data=json.dumps(variant_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Variant creation should succeed")
        
        print("✅ Apparel feature API tests passed")
    
    def test_books_feature_apis(self):
        """Test books feature-protected APIs"""
        print("\n=== Testing Books Feature APIs ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'testuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test API without feature enabled
            response = client.get('/api/books/products', headers=headers)
            self.assertEqual(response.status_code, 403, "API should be disabled without feature")
            
            # Enable books features
            feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_SPECIAL_ORDERS', str(self.test_tenant.id))
            
            # Test API with feature enabled
            response = client.get('/api/books/products', headers=headers)
            self.assertEqual(response.status_code, 200, "API should work with feature enabled")
            
            # Test author creation
            author_data = {
                'name': 'Test Author',
                'description': 'Test author description'
            }
            
            response = client.post('/api/books/authors',
                                 data=json.dumps(author_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Author creation should succeed")
            
            # Test book creation
            book_data = {
                'isbn': '978-3-16-148410-0',
                'title': 'Test Book',
                'price': '299.00',
                'description': 'Test book description'
            }
            
            response = client.post('/api/books/products',
                                 data=json.dumps(book_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Book creation should succeed")
        
        print("✅ Books feature API tests passed")


class TestAPIErrorHandling(unittest.TestCase):
    """Test API error handling and validation"""
    
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
            name='Error Test Tenant',
            subdomain='error-test',
            database_name='error_test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='erroruser',
            email='error@example.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_validation_errors(self):
        """Test API validation error handling"""
        print("\n=== Testing API Validation Errors ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'erroruser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test missing required fields
            invalid_data = {
                'name': 'Test Product'
                # Missing required fields
            }
            
            response = client.post('/api/products',
                                 data=json.dumps(invalid_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 400, "Should return 400 for missing fields")
            response_data = json.loads(response.data)
            self.assertIn('error', response_data, "Should return error message")
            
            # Test invalid data types
            invalid_type_data = {
                'sku': 'TEST001',
                'name': 'Test Product',
                'price': 'invalid_price',  # Should be numeric
                'category': 'Test Category'
            }
            
            response = client.post('/api/products',
                                 data=json.dumps(invalid_type_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 400, "Should return 400 for invalid data types")
            
            # Test duplicate data
            # First create a product
            valid_data = {
                'sku': 'DUPLICATE001',
                'name': 'Test Product 1',
                'price': '999.00',
                'category': 'Test Category'
            }
            
            response = client.post('/api/products',
                                 data=json.dumps(valid_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "First product should be created")
            
            # Try to create duplicate
            duplicate_data = {
                'sku': 'DUPLICATE001',  # Same SKU
                'name': 'Test Product 2',
                'price': '1099.00',
                'category': 'Test Category'
            }
            
            response = client.post('/api/products',
                                 data=json.dumps(duplicate_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 409, "Should return 409 for duplicate data")
        
        print("✅ API validation error tests passed")
    
    def test_not_found_errors(self):
        """Test API not found error handling"""
        print("\n=== Testing API Not Found Errors ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'erroruser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test non-existent resource
            response = client.get('/api/products/999999', headers=headers)
            self.assertEqual(response.status_code, 404, "Should return 404 for non-existent resource")
            
            # Test invalid endpoint
            response = client.get('/api/invalid/endpoint', headers=headers)
            self.assertEqual(response.status_code, 404, "Should return 404 for invalid endpoint")
            
            # Test non-existent order
            response = client.get('/api/orders/999999', headers=headers)
            self.assertEqual(response.status_code, 404, "Should return 404 for non-existent order")
        
        print("✅ API not found error tests passed")
    
    def test_server_error_handling(self):
        """Test API server error handling"""
        print("\n=== Testing API Server Error Handling ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'erroruser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test malformed JSON
            response = client.post('/api/products',
                                 data='invalid json',
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 400, "Should return 400 for malformed JSON")
            
            # Test missing content type
            response = client.post('/api/products',
                                 data=json.dumps({'test': 'data'}),
                                 headers=headers)
            
            self.assertEqual(response.status_code, 400, "Should return 400 for missing content type")
        
        print("✅ API server error handling tests passed")


class TestAPIPerformance(unittest.TestCase):
    """Test API performance and response times"""
    
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
            name='Performance Test Tenant',
            subdomain='performance-test',
            database_name='performance_test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='perfuser',
            email='perf@example.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_response_time_performance(self):
        """Test API response time performance"""
        print("\n=== Testing API Response Time Performance ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'perfuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test simple API response time
            import time
            start_time = time.time()
            
            response = client.get('/api/products', headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200, "API should succeed")
            self.assertLess(response_time, 1.0, "Response time should be less than 1 second")
            
            # Test pagination performance
            start_time = time.time()
            
            response = client.get('/api/products?page=1&per_page=50', headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200, "Paginated API should succeed")
            self.assertLess(response_time, 1.5, "Paginated response time should be less than 1.5 seconds")
        
        print("✅ API response time performance tests passed")
    
    def test_concurrent_requests(self):
        """Test API concurrent request handling"""
        print("\n=== Testing API Concurrent Request Handling ===")
        
        import threading
        import time
        
        results = []
        
        def make_request():
            with self.app.test_client() as client:
                # Login
                login_data = {
                    'username': 'perfuser',
                    'password': 'test_password',
                    'tenant_id': str(self.test_tenant.id)
                }
                
                response = client.post('/api/auth/login',
                                     data=json.dumps(login_data),
                                     content_type='application/json')
                
                token = json.loads(response.data)['access_token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # Make request
                start_time = time.time()
                response = client.get('/api/products', headers=headers)
                end_time = time.time()
                
                results.append({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify results
        self.assertEqual(len(results), 5, "Should have 5 results")
        
        for result in results:
            self.assertEqual(result['status_code'], 200, "All requests should succeed")
            self.assertLess(result['response_time'], 2.0, "Each request should complete within 2 seconds")
        
        self.assertLess(total_time, 5.0, "All requests should complete within 5 seconds")
        
        print("✅ API concurrent request handling tests passed")


def run_api_comprehensive_tests():
    """Run all API tests"""
    print("=" * 80)
    print("COMPREHENSIVE API TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing all API endpoints with authentication, authorization,\n"
          "feature protection, error handling, and performance\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAPIAuthentication,
        TestFeatureProtectedAPIs,
        TestAPIErrorHandling,
        TestAPIPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
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
        print("API endpoints are working correctly")
        exit(0)
    else:
        print("\n❌ SOME API TESTS FAILED!")
        print("Review and fix API issues")
        exit(1)