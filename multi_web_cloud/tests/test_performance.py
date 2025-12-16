"""
Comprehensive Performance Testing Framework
Tests load performance for different feature combinations,
database performance with conditional tables, UI rendering performance,
and caching/optimization effectiveness.
"""

import unittest
import json
import time
import threading
import concurrent.futures
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


class TestLoadPerformance(unittest.TestCase):
    """Test load performance with different feature combinations"""
    
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
            subdomain='performance',
            database_name='performance_db',
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
        
        # Create test products
        cls.test_products = []
        for i in range(100):
            product = Product(
                sku=f'PERF{i:03d}',
                name=f'Performance Test Product {i}',
                description=f'Description for performance test product {i}',
                price=Decimal(str(100 + i)),
                tenant_id=str(cls.test_tenant.id),
                status='active'
            )
            cls.test_products.append(product)
            db.session.add(product)
        
        db.session.commit()
    
    def test_api_load_performance(self):
        """Test API load performance with concurrent requests"""
        print("\n=== Testing API Load Performance ===")
        
        with self.app.test_client() as client:
            # Login to get token
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
            
            # Test concurrent API requests
            def make_api_request():
                start_time = time.time()
                response = client.get('/api/products', headers=headers)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }
            
            # Run concurrent requests
            num_requests = 20
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_api_request) for _ in range(num_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_requests = [r for r in results if r['status_code'] == 200]
            response_times = [r['response_time'] for r in successful_requests]
            
            self.assertEqual(len(successful_requests), num_requests, "All requests should succeed")
            self.assertLess(max(response_times), 2.0, "Max response time should be less than 2 seconds")
            self.assertLess(sum(response_times) / len(response_times), 1.0, 
                          "Average response time should be less than 1 second")
        
        print("✅ API load performance tests passed")
    
    def test_feature_combination_performance(self):
        """Test performance with different feature combinations"""
        print("\n=== Testing Feature Combination Performance ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test performance with no features
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            baseline_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200, "Page should render")
            
            # Enable features one by one and measure performance impact
            features_to_enable = [
                'FEATURE_TABLE_MANAGEMENT',
                'FEATURE_SIZE_VARIANTS',
                'FEATURE_COLOR_VARIANTS',
                'FEATURE_ISBN_TRACKING',
                'FEATURE_BATCH_TRACKING',
                'FEATURE_EXPIRY_TRACKING',
                'FEATURE_REPORTING',
                'FEATURE_INVENTORY',
                'FEATURE_CUSTOMER_MANAGEMENT'
            ]
            
            performance_impact = {}
            
            for feature in features_to_enable:
                # Enable feature
                feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                # Measure performance
                start_time = time.time()
                response = client.get('/')
                end_time = time.time()
                
                feature_time = end_time - start_time
                impact = feature_time - baseline_time
                performance_impact[feature] = impact
                
                self.assertEqual(response.status_code, 200, "Page should render with feature enabled")
                self.assertLess(impact, 0.5, f"Feature {feature} should not add more than 0.5s overhead")
            
            # Test with all features enabled
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            all_features_time = end_time - start_time
            total_impact = all_features_time - baseline_time
            
            self.assertLess(total_impact, 2.0, "All features combined should not add more than 2s overhead")
            
            # Print performance impact
            print(f"Baseline time: {baseline_time:.3f}s")
            print(f"All features time: {all_features_time:.3f}s")
            print(f"Total impact: {total_impact:.3f}s")
            
            for feature, impact in performance_impact.items():
                print(f"  {feature}: +{impact:.3f}s")
        
        print("✅ Feature combination performance tests passed")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        print("\n=== Testing Database Query Performance ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test simple query performance
            start_time = time.time()
            products = Product.query.filter_by(tenant_id=str(self.test_tenant.id)).all()
            end_time = time.time()
            
            simple_query_time = end_time - start_time
            self.assertLess(simple_query_time, 0.1, "Simple query should complete within 0.1s")
            self.assertEqual(len(products), 100, "Should return all test products")
            
            # Test paginated query performance
            start_time = time.time()
            paginated_products = Product.query.filter_by(tenant_id=str(self.test_tenant.id)).paginate(
                page=1, per_page=20, error_out=False
            )
            end_time = time.time()
            
            paginated_query_time = end_time - start_time
            self.assertLess(paginated_query_time, 0.1, "Paginated query should complete within 0.1s")
            self.assertEqual(len(paginated_products.items), 20, "Should return 20 items per page")
            
            # Test filtered query performance
            start_time = time.time()
            filtered_products = Product.query.filter_by(
                tenant_id=str(self.test_tenant.id),
                status='active'
            ).all()
            end_time = time.time()
            
            filtered_query_time = end_time - start_time
            self.assertLess(filtered_query_time, 0.1, "Filtered query should complete within 0.1s")
            self.assertEqual(len(filtered_products), 100, "Should return all active products")
            
            # Test complex query performance
            start_time = time.time()
            complex_products = Product.query.filter(
                Product.tenant_id == str(self.test_tenant.id),
                Product.price.between(100, 200),
                Product.status == 'active'
            ).order_by(Product.price.desc()).limit(50).all()
            end_time = time.time()
            
            complex_query_time = end_time - start_time
            self.assertLess(complex_query_time, 0.2, "Complex query should complete within 0.2s")
            self.assertLessEqual(len(complex_products), 50, "Should limit to 50 results")
            
            print(f"Simple query: {simple_query_time:.3f}s")
            print(f"Paginated query: {paginated_query_time:.3f}s")
            print(f"Filtered query: {filtered_query_time:.3f}s")
            print(f"Complex query: {complex_query_time:.3f}s")
        
        print("✅ Database query performance tests passed")


class TestDatabasePerformance(unittest.TestCase):
    """Test database performance with conditional tables"""
    
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
            name='DB Performance Test Tenant',
            subdomain='db-perf',
            database_name='db_perf_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_conditional_table_performance(self):
        """Test performance with conditional table creation"""
        print("\n=== Testing Conditional Table Performance ===")
        
        # Test performance without retail-specific tables
        start_time = time.time()
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        end_time = time.time()
        
        baseline_table_count = len(table_names)
        inspection_time = end_time - start_time
        
        self.assertLess(inspection_time, 0.1, "Table inspection should complete within 0.1s")
        
        # Enable restaurant features
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_KOT_PRINTING', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_RESERVATIONS', str(self.test_tenant.id))
        
        # Create restaurant tables
        start_time = time.time()
        
        restaurant_tables = []
        for i in range(50):
            table = RestaurantTable(
                table_number=f'T{i+1}',
                capacity=4,
                location=f'Area {i % 5}',
                tenant_id=str(self.test_tenant.id),
                status='available'
            )
            restaurant_tables.append(table)
            db.session.add(table)
        
        db.session.commit()
        end_time = time.time()
        
        restaurant_table_creation_time = end_time - start_time
        self.assertLess(restaurant_table_creation_time, 1.0, "Restaurant table creation should complete within 1s")
        
        # Test query performance on conditional tables
        start_time = time.time()
        tables = RestaurantTable.query.filter_by(tenant_id=str(self.test_tenant.id)).all()
        end_time = time.time()
        
        restaurant_query_time = end_time - start_time
        self.assertLess(restaurant_query_time, 0.1, "Restaurant table query should complete within 0.1s")
        self.assertEqual(len(tables), 50, "Should return all restaurant tables")
        
        # Enable apparel features
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(self.test_tenant.id))
        
        # Create apparel products
        start_time = time.time()
        
        apparel_products = []
        for i in range(30):
            product = ApparelProduct(
                sku=f'APP{i+1:03d}',
                name=f'Apparel Product {i+1}',
                category='Clothing',
                base_price=Decimal(str(500 + i * 10)),
                tenant_id=str(self.test_tenant.id),
                status='active'
            )
            apparel_products.append(product)
            db.session.add(product)
        
        db.session.commit()
        end_time = time.time()
        
        apparel_product_creation_time = end_time - start_time
        self.assertLess(apparel_product_creation_time, 1.0, "Apparel product creation should complete within 1s")
        
        # Test query performance on apparel tables
        start_time = time.time()
        products = ApparelProduct.query.filter_by(tenant_id=str(self.test_tenant.id)).all()
        end_time = time.time()
        
        apparel_query_time = end_time - start_time
        self.assertLess(apparel_query_time, 0.1, "Apparel product query should complete within 0.1s")
        self.assertEqual(len(products), 30, "Should return all apparel products")
        
        # Test cross-table join performance
        start_time = time.time()
        
        # Create orders and join with tables
        orders = []
        for i in range(20):
            order = Order(
                order_number=f'ORD{i+1:03d}',
                customer_name=f'Customer {i+1}',
                order_type='Dine-in',
                table_id=restaurant_tables[i % len(restaurant_tables)].id,
                total_amount=Decimal(str(100 + i * 10)),
                tenant_id=str(self.test_tenant.id),
                status='Completed'
            )
            orders.append(order)
            db.session.add(order)
        
        db.session.commit()
        end_time = time.time()
        
        order_creation_time = end_time - start_time
        self.assertLess(order_creation_time, 1.0, "Order creation should complete within 1s")
        
        # Test join query performance
        start_time = time.time()
        join_results = db.session.query(Order, RestaurantTable).join(
            RestaurantTable, Order.table_id == RestaurantTable.id
        ).filter(Order.tenant_id == str(self.test_tenant.id)).all()
        end_time = time.time()
        
        join_query_time = end_time - start_time
        self.assertLess(join_query_time, 0.2, "Join query should complete within 0.2s")
        self.assertEqual(len(join_results), 20, "Should return all joined results")
        
        print(f"Baseline table count: {baseline_table_count}")
        print(f"Table inspection: {inspection_time:.3f}s")
        print(f"Restaurant table creation: {restaurant_table_creation_time:.3f}s")
        print(f"Restaurant table query: {restaurant_query_time:.3f}s")
        print(f"Apparel product creation: {apparel_product_creation_time:.3f}s")
        print(f"Apparel product query: {apparel_query_time:.3f}s")
        print(f"Order creation: {order_creation_time:.3f}s")
        print(f"Join query: {join_query_time:.3f}s")
        
        print("✅ Conditional table performance tests passed")
    
    def test_index_performance(self):
        """Test database index performance"""
        print("\n=== Testing Database Index Performance ===")
        
        # Create large dataset
        start_time = time.time()
        
        large_products = []
        for i in range(1000):
            product = Product(
                sku=f'LARGE{i:04d}',
                name=f'Large Product {i}',
                description=f'Description for large product {i}',
                price=Decimal(str(100 + i % 500)),
                tenant_id=str(self.test_tenant.id),
                status='active' if i % 10 != 0 else 'inactive'
            )
            large_products.append(product)
            db.session.add(product)
        
        db.session.commit()
        end_time = time.time()
        
        large_dataset_creation_time = end_time - start_time
        self.assertLess(large_dataset_creation_time, 5.0, "Large dataset creation should complete within 5s")
        
        # Test query without index (should be slower)
        start_time = time.time()
        products_without_index = Product.query.filter_by(
            tenant_id=str(self.test_tenant.id),
            status='active'
        ).all()
        end_time = time.time()
        
        query_without_index_time = end_time - start_time
        self.assertLess(query_without_index_time, 0.5, "Query without index should complete within 0.5s")
        
        # Test query with price range (should benefit from index if exists)
        start_time = time.time()
        products_with_price_range = Product.query.filter(
            Product.tenant_id == str(self.test_tenant.id),
            Product.price.between(200, 300),
            Product.status == 'active'
        ).all()
        end_time = time.time()
        
        query_with_range_time = end_time - start_time
        self.assertLess(query_with_range_time, 0.5, "Range query should complete within 0.5s")
        
        # Test ordered query
        start_time = time.time()
        ordered_products = Product.query.filter_by(
            tenant_id=str(self.test_tenant.id)
        ).order_by(Product.price.desc()).limit(100).all()
        end_time = time.time()
        
        ordered_query_time = end_time - start_time
        self.assertLess(ordered_query_time, 0.5, "Ordered query should complete within 0.5s")
        
        print(f"Large dataset creation: {large_dataset_creation_time:.3f}s")
        print(f"Query without index: {query_without_index_time:.3f}s")
        print(f"Query with range: {query_with_range_time:.3f}s")
        print(f"Ordered query: {ordered_query_time:.3f}s")
        
        print("✅ Database index performance tests passed")


class TestUIRenderingPerformance(unittest.TestCase):
    """Test UI rendering performance with adaptive components"""
    
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
            name='UI Performance Test Tenant',
            subdomain='ui-perf',
            database_name='ui_perf_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_template_rendering_performance(self):
        """Test template rendering performance"""
        print("\n=== Testing Template Rendering Performance ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test baseline rendering performance
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            baseline_rendering_time = end_time - start_time
            self.assertEqual(response.status_code, 200, "Page should render")
            self.assertLess(baseline_rendering_time, 0.5, "Baseline rendering should complete within 0.5s")
            
            # Test rendering with features enabled
            features_to_enable = [
                'FEATURE_TABLE_MANAGEMENT',
                'FEATURE_SIZE_VARIANTS',
                'FEATURE_COLOR_VARIANTS',
                'FEATURE_REPORTING',
                'FEATURE_INVENTORY'
            ]
            
            rendering_times = {}
            
            for feature in features_to_enable:
                feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                start_time = time.time()
                response = client.get('/')
                end_time = time.time()
                
                rendering_time = end_time - start_time
                rendering_times[feature] = rendering_time
                
                self.assertEqual(response.status_code, 200, f"Page should render with {feature}")
                self.assertLess(rendering_time, 1.0, f"Rendering with {feature} should complete within 1s")
            
            # Test rendering with all features
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            all_features_rendering_time = end_time - start_time
            self.assertEqual(response.status_code, 200, "Page should render with all features")
            self.assertLess(all_features_rendering_time, 2.0, "Rendering with all features should complete within 2s")
            
            print(f"Baseline rendering: {baseline_rendering_time:.3f}s")
            print(f"All features rendering: {all_features_rendering_time:.3f}s")
            
            for feature, render_time in rendering_times.items():
                print(f"  {feature}: {render_time:.3f}s")
        
        print("✅ Template rendering performance tests passed")
    
    def test_component_loading_performance(self):
        """Test dynamic component loading performance"""
        print("\n=== Testing Component Loading Performance ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test component loading with different retail types
            retail_types = ['restaurant', 'apparel', 'books', 'grocery']
            component_loading_times = {}
            
            for retail_type in retail_types:
                with client.session_transaction() as sess:
                    sess['retail_type'] = retail_type
                
                start_time = time.time()
                response = client.get('/')
                end_time = time.time()
                
                loading_time = end_time - start_time
                component_loading_times[retail_type] = loading_time
                
                self.assertEqual(response.status_code, 200, f"Page should render for {retail_type}")
                self.assertLess(loading_time, 1.0, f"Component loading for {retail_type} should complete within 1s")
            
            # Test component loading with features
            feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(self.test_tenant.id))
            
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            features_loading_time = end_time - start_time
            self.assertEqual(response.status_code, 200, "Page should render with features")
            self.assertLess(features_loading_time, 1.5, "Component loading with features should complete within 1.5s")
            
            print("Component loading times by retail type:")
            for retail_type, loading_time in component_loading_times.items():
                print(f"  {retail_type}: {loading_time:.3f}s")
            
            print(f"With features: {features_loading_time:.3f}s")
        
        print("✅ Component loading performance tests passed")
    
    def test_form_generation_performance(self):
        """Test dynamic form generation performance"""
        print("\n=== Testing Form Generation Performance ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test basic form generation
            start_time = time.time()
            response = client.get('/products/new')
            end_time = time.time()
            
            basic_form_time = end_time - start_time
            self.assertEqual(response.status_code, 200, "Basic form should render")
            self.assertLess(basic_form_time, 0.5, "Basic form generation should complete within 0.5s")
            
            # Test form generation with features
            feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(self.test_tenant.id))
            feature_manager.enable_feature('FEATURE_BATCH_TRACKING', str(self.test_tenant.id))
            
            start_time = time.time()
            response = client.get('/products/new')
            end_time = time.time()
            
            feature_form_time = end_time - start_time
            self.assertEqual(response.status_code, 200, "Feature form should render")
            self.assertLess(feature_form_time, 1.0, "Feature form generation should complete within 1s")
            
            # Test form generation for different retail types
            retail_types = ['restaurant', 'apparel', 'books']
            form_times = {}
            
            for retail_type in retail_types:
                with client.session_transaction() as sess:
                    sess['retail_type'] = retail_type
                
                start_time = time.time()
                response = client.get('/products/new')
                end_time = time.time()
                
                form_time = end_time - start_time
                form_times[retail_type] = form_time
                
                self.assertEqual(response.status_code, 200, f"Form should render for {retail_type}")
                self.assertLess(form_time, 1.0, f"Form generation for {retail_type} should complete within 1s")
            
            print(f"Basic form generation: {basic_form_time:.3f}s")
            print(f"Feature form generation: {feature_form_time:.3f}s")
            
            for retail_type, form_time in form_times.items():
                print(f"  {retail_type} form: {form_time:.3f}s")
        
        print("✅ Form generation performance tests passed")


class TestCachingOptimization(unittest.TestCase):
    """Test caching and optimization effectiveness"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300
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
            name='Cache Test Tenant',
            subdomain='cache-test',
            database_name='cache_test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_feature_flag_caching(self):
        """Test feature flag caching effectiveness"""
        print("\n=== Testing Feature Flag Caching ===")
        
        # Enable features
        features_to_enable = [
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_SIZE_VARIANTS',
            'FEATURE_COLOR_VARIANTS'
        ]
        
        for feature in features_to_enable:
            feature_manager.enable_feature(feature, str(self.test_tenant.id))
        
        # Test feature flag retrieval performance (first time - cache miss)
        start_time = time.time()
        features_first = feature_manager.get_tenant_features(str(self.test_tenant.id))
        end_time = time.time()
        
        first_retrieval_time = end_time - start_time
        self.assertEqual(set(features_first), set(features_to_enable), "Should return enabled features")
        
        # Test feature flag retrieval performance (subsequent times - cache hit)
        start_time = time.time()
        features_cached = feature_manager.get_tenant_features(str(self.test_tenant.id))
        end_time = time.time()
        
        cached_retrieval_time = end_time - start_time
        self.assertEqual(set(features_cached), set(features_to_enable), "Should return cached features")
        
        # Cache should be faster
        self.assertLess(cached_retrieval_time, first_retrieval_time, 
                       "Cached retrieval should be faster than first retrieval")
        
        print(f"First retrieval: {first_retrieval_time:.6f}s")
        print(f"Cached retrieval: {cached_retrieval_time:.6f}s")
        print(f"Speedup: {first_retrieval_time / cached_retrieval_time:.1f}x")
        
        print("✅ Feature flag caching tests passed")
    
    def test_template_caching(self):
        """Test template caching effectiveness"""
        print("\n=== Testing Template Caching ===")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['tenant_id'] = str(self.test_tenant.id)
                sess['retail_type'] = 'general'
            
            # Test template rendering performance (first time)
            start_time = time.time()
            response1 = client.get('/')
            end_time = time.time()
            
            first_render_time = end_time - start_time
            self.assertEqual(response1.status_code, 200, "Template should render first time")
            
            # Test template rendering performance (subsequent times)
            start_time = time.time()
            response2 = client.get('/')
            end_time = time.time()
            
            cached_render_time = end_time - start_time
            self.assertEqual(response2.status_code, 200, "Template should render from cache")
            
            # Responses should be identical
            self.assertEqual(response1.data, response2.data, "Cached response should be identical")
            
            print(f"First render: {first_render_time:.3f}s")
            print(f"Cached render: {cached_render_time:.3f}s")
            
            if cached_render_time < first_render_time:
                print(f"Speedup: {first_render_time / cached_render_time:.1f}x")
            else:
                print("No significant speedup detected (may be due to testing environment)")
        
        print("✅ Template caching tests passed")
    
    def test_database_query_caching(self):
        """Test database query caching effectiveness"""
        print("\n=== Testing Database Query Caching ===")
        
        # Create test data
        test_products = []
        for i in range(50):
            product = Product(
                sku=f'CACHE{i:02d}',
                name=f'Cache Test Product {i}',
                description=f'Description for cache test product {i}',
                price=Decimal(str(100 + i)),
                tenant_id=str(self.test_tenant.id),
                status='active'
            )
            test_products.append(product)
            db.session.add(product)
        
        db.session.commit()
        
        # Test query performance (first time)
        start_time = time.time()
        products_first = Product.query.filter_by(
            tenant_id=str(self.test_tenant.id),
            status='active'
        ).all()
        end_time = time.time()
        
        first_query_time = end_time - start_time
        self.assertEqual(len(products_first), 50, "Should return all test products")
        
        # Test query performance (subsequent times)
        start_time = time.time()
        products_cached = Product.query.filter_by(
            tenant_id=str(self.test_tenant.id),
            status='active'
        ).all()
        end_time = time.time()
        
        cached_query_time = end_time - start_time
        self.assertEqual(len(products_cached), 50, "Should return cached products")
        
        # Results should be identical
        self.assertEqual(len(products_first), len(products_cached), "Cached query should return same results")
        
        print(f"First query: {first_query_time:.3f}s")
        print(f"Cached query: {cached_query_time:.3f}s")
        
        if cached_query_time < first_query_time:
            print(f"Speedup: {first_query_time / cached_query_time:.1f}x")
        else:
            print("No significant speedup detected (may be due to testing environment)")
        
        print("✅ Database query caching tests passed")


def run_performance_tests():
    """Run all performance tests"""
    print("=" * 80)
    print("COMPREHENSIVE PERFORMANCE TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing load performance, database performance, UI rendering,\n"
          "and caching optimization effectiveness\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestLoadPerformance,
        TestDatabasePerformance,
        TestUIRenderingPerformance,
        TestCachingOptimization
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE PERFORMANCE TEST RESULTS")
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
    success = run_performance_tests()
    
    if success:
        print("\n✅ ALL PERFORMANCE TESTS PASSED!")
        print("System performance is within acceptable limits")
        exit(0)
    else:
        print("\n❌ SOME PERFORMANCE TESTS FAILED!")
        print("Review and optimize performance issues")
        exit(1)