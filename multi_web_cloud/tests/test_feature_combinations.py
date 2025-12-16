"""
Feature Combination Testing Framework
Tests all possible feature combinations, feature enable/disable scenarios,
feature conflicts and resolution, and performance with all features enabled.
"""

import unittest
import json
import itertools
import time
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


class TestFeatureCombinations(unittest.TestCase):
    """Test all possible feature combinations"""
    
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
        
        # Define all available features
        cls.all_features = [
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_RESERVATIONS',
            'FEATURE_KOT_PRINTING',
            'FEATURE_KITCHEN_DISPLAY',
            'FEATURE_WAITER_MANAGEMENT',
            'FEATURE_SHIFT_MANAGEMENT',
            'FEATURE_SIZE_VARIANTS',
            'FEATURE_COLOR_VARIANTS',
            'FEATURE_STYLE_VARIANTS',
            'FEATURE_EXCHANGE_MANAGEMENT',
            'FEATURE_ALTERATION_TRACKING',
            'FEATURE_ISBN_TRACKING',
            'FEATURE_SPECIAL_ORDERS',
            'FEATURE_PUBLISHER_MANAGEMENT',
            'FEATURE_AUTHOR_MANAGEMENT',
            'FEATURE_CATEGORY_MANAGEMENT',
            'FEATURE_WEIGHING_SCALE',
            'FEATURE_EXPIRY_TRACKING',
            'FEATURE_BATCH_TRACKING',
            'FEATURE_PRICE_BY_WEIGHT',
            'FEATURE_COMBO_OFFERS',
            'FEATURE_FRESH_PRODUCE',
            'FEATURE_SALES_PROCESSING',
            'FEATURE_PRODUCT_CATALOG',
            'FEATURE_CUSTOMER_MANAGEMENT',
            'FEATURE_INVENTORY',
            'FEATURE_REPORTING',
            'FEATURE_ANALYTICS',
            'FEATURE_MULTI_STORE',
            'FEATURE_FRANCHISE_MANAGEMENT',
            'FEATURE_LOYALTY_PROGRAM',
            'FEATURE_CRM',
            'FEATURE_PROMOTIONS',
            'FEATURE_DISCOUNTS',
            'FEATURE_GIFT_CARDS',
            'FEATURE_STORE_CREDIT',
            'FEATURE_ONLINE_ORDERING',
            'FEATURE_DELIVERY',
            'FEATURE_PICKUP',
            'FEATURE_MOBILE_APP',
            'FEATURE_API_ACCESS',
            'FEATURE_WEBHOOKS',
            'FEATURE_INTEGRATIONS',
            'FEATURE_EMAIL_NOTIFICATIONS',
            'FEATURE_SMS_NOTIFICATIONS',
            'FEATURE_PUSH_NOTIFICATIONS',
            'FEATURE_OFFLINE_MODE',
            'FEATURE_DATA_SYNC',
            'FEATURE_BACKUP_RESTORE',
            'FEATURE_AUDIT_LOG',
            'FEATURE_MULTI_CURRENCY',
            'FEATURE_MULTI_LANGUAGE',
            'FEATURE_TAX_MANAGEMENT',
            'FEATURE_PAYMENT_GATEWAY',
            'FEATURE_CASH_MANAGEMENT',
            'FEATURE_BANK_DEPOSIT',
            'FEATURE_EXPENSE_TRACKING'
        ]
        
        # Define feature groups for testing
        cls.feature_groups = {
            'restaurant': [
                'FEATURE_TABLE_MANAGEMENT',
                'FEATURE_RESERVATIONS',
                'FEATURE_KOT_PRINTING',
                'FEATURE_KITCHEN_DISPLAY',
                'FEATURE_WAITER_MANAGEMENT',
                'FEATURE_SHIFT_MANAGEMENT'
            ],
            'apparel': [
                'FEATURE_SIZE_VARIANTS',
                'FEATURE_COLOR_VARIANTS',
                'FEATURE_STYLE_VARIANTS',
                'FEATURE_EXCHANGE_MANAGEMENT',
                'FEATURE_ALTERATION_TRACKING'
            ],
            'books': [
                'FEATURE_ISBN_TRACKING',
                'FEATURE_SPECIAL_ORDERS',
                'FEATURE_PUBLISHER_MANAGEMENT',
                'FEATURE_AUTHOR_MANAGEMENT',
                'FEATURE_CATEGORY_MANAGEMENT'
            ],
            'grocery': [
                'FEATURE_WEIGHING_SCALE',
                'FEATURE_EXPIRY_TRACKING',
                'FEATURE_BATCH_TRACKING',
                'FEATURE_PRICE_BY_WEIGHT',
                'FEATURE_COMBO_OFFERS',
                'FEATURE_FRESH_PRODUCE'
            ],
            'core': [
                'FEATURE_SALES_PROCESSING',
                'FEATURE_PRODUCT_CATALOG',
                'FEATURE_CUSTOMER_MANAGEMENT',
                'FEATURE_INVENTORY',
                'FEATURE_REPORTING'
            ],
            'advanced': [
                'FEATURE_ANALYTICS',
                'FEATURE_MULTI_STORE',
                'FEATURE_FRANCHISE_MANAGEMENT',
                'FEATURE_LOYALTY_PROGRAM',
                'FEATURE_CRM',
                'FEATURE_PROMOTIONS',
                'FEATURE_DISCOUNTS'
            ],
            'payments': [
                'FEATURE_GIFT_CARDS',
                'FEATURE_STORE_CREDIT',
                'FEATURE_PAYMENT_GATEWAY',
                'FEATURE_CASH_MANAGEMENT',
                'FEATURE_BANK_DEPOSIT'
            ],
            'digital': [
                'FEATURE_ONLINE_ORDERING',
                'FEATURE_DELIVERY',
                'FEATURE_PICKUP',
                'FEATURE_MOBILE_APP',
                'FEATURE_API_ACCESS',
                'FEATURE_WEBHOOKS',
                'FEATURE_INTEGRATIONS'
            ],
            'notifications': [
                'FEATURE_EMAIL_NOTIFICATIONS',
                'FEATURE_SMS_NOTIFICATIONS',
                'FEATURE_PUSH_NOTIFICATIONS'
            ],
            'operations': [
                'FEATURE_OFFLINE_MODE',
                'FEATURE_DATA_SYNC',
                'FEATURE_BACKUP_RESTORE',
                'FEATURE_AUDIT_LOG'
            ],
            'global': [
                'FEATURE_MULTI_CURRENCY',
                'FEATURE_MULTI_LANGUAGE',
                'FEATURE_TAX_MANAGEMENT',
                'FEATURE_EXPENSE_TRACKING'
            ]
        }
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for feature combination testing"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Feature Combination Test',
            subdomain='feature-combo',
            database_name='feature_combo_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='featureuser',
            email='feature@example.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_all_feature_combinations_small(self):
        """Test a subset of all possible feature combinations"""
        print("\n=== Testing All Feature Combinations (Subset) ===")
        
        # Test combinations within each feature group
        for group_name, features in self.feature_groups.items():
            print(f"\n--- Testing {group_name.upper()} Feature Group ---")
            
            # Test all combinations of up to 3 features from this group
            if len(features) <= 3:
                # Test all combinations if group is small
                combinations_to_test = list(itertools.combinations(features, len(features)))
            else:
                # Test combinations of 2-3 features if group is large
                combinations_to_test = (
                    list(itertools.combinations(features, 2))[:5] +  # First 5 combinations of 2
                    list(itertools.combinations(features, 3))[:3]    # First 3 combinations of 3
                )
            
            for i, feature_combo in enumerate(combinations_to_test):
                print(f"  Testing combination {i+1}: {', '.join(feature_combo)}")
                
                with self.app.test_client() as client:
                    # Clear all features first
                    for feature in self.all_features:
                        feature_manager.disable_feature(feature, str(self.test_tenant.id))
                    
                    # Enable current combination
                    for feature in feature_combo:
                        feature_manager.enable_feature(feature, str(self.test_tenant.id))
                    
                    # Login
                    login_data = {
                        'username': 'featureuser',
                        'password': 'test_password',
                        'tenant_id': str(self.test_tenant.id)
                    }
                    
                    response = client.post('/api/auth/login',
                                         data=json.dumps(login_data),
                                         content_type='application/json')
                    
                    if response.status_code == 200:
                        token = json.loads(response.data)['access_token']
                        headers = {'Authorization': f'Bearer {token}'}
                        
                        # Test basic functionality with this combination
                        response = client.get('/api/products', headers=headers)
                        
                        # Should either work (200) or be properly restricted (403)
                        self.assertIn(response.status_code, [200, 403], 
                                     f"Should handle combination {', '.join(feature_combo)}")
                        
                        # Test feature-specific endpoints
                        for feature in feature_combo:
                            endpoint = self._get_feature_endpoint(feature)
                            if endpoint:
                                response = client.get(endpoint, headers=headers)
                                
                                # Should either work (200) or be properly restricted (403/404)
                                self.assertIn(response.status_code, [200, 403, 404], 
                                             f"Should handle feature {feature}")
                    else:
                        # Login should work regardless of feature combination
                        self.fail(f"Login failed with feature combination {', '.join(feature_combo)}")
        
        print("✅ All feature combinations (subset) tests passed")
    
    def test_cross_group_combinations(self):
        """Test combinations across different feature groups"""
        print("\n=== Testing Cross-Group Feature Combinations ===")
        
        # Define cross-group combinations to test
        cross_combinations = [
            # Restaurant + Core
            ['FEATURE_TABLE_MANAGEMENT', 'FEATURE_SALES_PROCESSING', 'FEATURE_PRODUCT_CATALOG'],
            
            # Apparel + Payments
            ['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS', 'FEATURE_PAYMENT_GATEWAY'],
            
            # Books + Digital
            ['FEATURE_ISBN_TRACKING', 'FEATURE_SPECIAL_ORDERS', 'FEATURE_ONLINE_ORDERING'],
            
            # Grocery + Operations
            ['FEATURE_WEIGHING_SCALE', 'FEATURE_EXPIRY_TRACKING', 'FEATURE_OFFLINE_MODE'],
            
            # Advanced + Notifications
            ['FEATURE_ANALYTICS', 'FEATURE_LOYALTY_PROGRAM', 'FEATURE_EMAIL_NOTIFICATIONS'],
            
            # Multi-retail combination
            ['FEATURE_TABLE_MANAGEMENT', 'FEATURE_SIZE_VARIANTS', 'FEATURE_ISBN_TRACKING', 
             'FEATURE_WEIGHING_SCALE', 'FEATURE_SALES_PROCESSING'],
            
            # Full-featured combination
            ['FEATURE_TABLE_MANAGEMENT', 'FEATURE_SIZE_VARIANTS', 'FEATURE_ISBN_TRACKING',
             'FEATURE_WEIGHING_SCALE', 'FEATURE_ANALYTICS', 'FEATURE_PAYMENT_GATEWAY',
             'FEATURE_ONLINE_ORDERING', 'FEATURE_EMAIL_NOTIFICATIONS', 'FEATURE_OFFLINE_MODE']
        ]
        
        for i, feature_combo in enumerate(cross_combinations):
            print(f"  Testing cross-group combination {i+1}: {', '.join(feature_combo)}")
            
            with self.app.test_client() as client:
                # Clear all features first
                for feature in self.all_features:
                    feature_manager.disable_feature(feature, str(self.test_tenant.id))
                
                # Enable current combination
                for feature in feature_combo:
                    feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                # Login
                login_data = {
                    'username': 'featureuser',
                    'password': 'test_password',
                    'tenant_id': str(self.test_tenant.id)
                }
                
                response = client.post('/api/auth/login',
                                     data=json.dumps(login_data),
                                     content_type='application/json')
                
                self.assertEqual(response.status_code, 200, 
                               f"Login should succeed with combination {i+1}")
                
                token = json.loads(response.data)['access_token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test that all features are accessible
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                
                for feature in feature_combo:
                    self.assertIn(feature, enabled_features, 
                                 f"Feature {feature} should be enabled")
                    
                    # Test feature-specific endpoint
                    endpoint = self._get_feature_endpoint(feature)
                    if endpoint:
                        response = client.get(endpoint, headers=headers)
                        
                        # Should work since feature is enabled
                        self.assertEqual(response.status_code, 200, 
                                       f"Feature {feature} endpoint should work")
                
                # Test that disabled features are not accessible
                for feature in self.all_features[:10]:  # Test first 10 features
                    if feature not in feature_combo:
                        endpoint = self._get_feature_endpoint(feature)
                        if endpoint:
                            response = client.get(endpoint, headers=headers)
                            
                            # Should be restricted
                            self.assertEqual(response.status_code, 403, 
                                           f"Disabled feature {feature} should be restricted")
        
        print("✅ Cross-group feature combinations tests passed")
    
    def test_feature_enable_disable_scenarios(self):
        """Test feature enable and disable scenarios"""
        print("\n=== Testing Feature Enable/Disable Scenarios ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'featureuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test 1: Enable features one by one
            print("  Testing enabling features one by one")
            for i, feature in enumerate(self.all_features[:10]):  # Test first 10 features
                # Enable feature
                feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                # Verify it's enabled
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                self.assertIn(feature, enabled_features, f"Feature {feature} should be enabled")
                
                # Test endpoint
                endpoint = self._get_feature_endpoint(feature)
                if endpoint:
                    response = client.get(endpoint, headers=headers)
                    self.assertEqual(response.status_code, 200, f"Feature {feature} should work")
            
            # Test 2: Disable features one by one
            print("  Testing disabling features one by one")
            for i, feature in enumerate(self.all_features[:10]):  # Test first 10 features
                # Disable feature
                feature_manager.disable_feature(feature, str(self.test_tenant.id))
                
                # Verify it's disabled
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                self.assertNotIn(feature, enabled_features, f"Feature {feature} should be disabled")
                
                # Test endpoint
                endpoint = self._get_feature_endpoint(feature)
                if endpoint:
                    response = client.get(endpoint, headers=headers)
                    self.assertEqual(response.status_code, 403, f"Feature {feature} should be restricted")
            
            # Test 3: Enable multiple features at once
            print("  Testing enabling multiple features at once")
            features_to_enable = self.all_features[:5]  # Enable first 5 features
            
            for feature in features_to_enable:
                feature_manager.enable_feature(feature, str(self.test_tenant.id))
            
            # Verify all are enabled
            enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
            for feature in features_to_enable:
                self.assertIn(feature, enabled_features, f"Feature {feature} should be enabled")
                
                # Test endpoint
                endpoint = self._get_feature_endpoint(feature)
                if endpoint:
                    response = client.get(endpoint, headers=headers)
                    self.assertEqual(response.status_code, 200, f"Feature {feature} should work")
            
            # Test 4: Disable multiple features at once
            print("  Testing disabling multiple features at once")
            for feature in features_to_enable:
                feature_manager.disable_feature(feature, str(self.test_tenant.id))
            
            # Verify all are disabled
            enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
            for feature in features_to_enable:
                self.assertNotIn(feature, enabled_features, f"Feature {feature} should be disabled")
                
                # Test endpoint
                endpoint = self._get_feature_endpoint(feature)
                if endpoint:
                    response = client.get(endpoint, headers=headers)
                    self.assertEqual(response.status_code, 403, f"Feature {feature} should be restricted")
            
            # Test 5: Toggle features rapidly
            print("  Testing rapid feature toggling")
            test_features = self.all_features[:3]  # Test first 3 features
            
            for cycle in range(3):  # 3 toggle cycles
                # Enable all
                for feature in test_features:
                    feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                # Verify and test
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                for feature in test_features:
                    self.assertIn(feature, enabled_features, f"Feature {feature} should be enabled in cycle {cycle+1}")
                
                # Disable all
                for feature in test_features:
                    feature_manager.disable_feature(feature, str(self.test_tenant.id))
                
                # Verify and test
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                for feature in test_features:
                    self.assertNotIn(feature, enabled_features, f"Feature {feature} should be disabled in cycle {cycle+1}")
        
        print("✅ Feature enable/disable scenarios tests passed")
    
    def test_feature_conflicts_resolution(self):
        """Test feature conflict detection and resolution"""
        print("\n=== Testing Feature Conflicts and Resolution ===")
        
        # Define conflicting feature combinations
        conflict_scenarios = [
            {
                'name': 'Offline vs Online Features',
                'conflicts': [
                    ('FEATURE_OFFLINE_MODE', 'FEATURE_ONLINE_ORDERING'),
                    ('FEATURE_OFFLINE_MODE', 'FEATURE_DELIVERY'),
                    ('FEATURE_OFFLINE_MODE', 'FEATURE_API_ACCESS')
                ],
                'resolution': 'disable_offline_when_online'
            },
            {
                'name': 'Payment Method Conflicts',
                'conflicts': [
                    ('FEATURE_CASH_MANAGEMENT', 'FEATURE_PAYMENT_GATEWAY'),
                    ('FEATURE_BANK_DEPOSIT', 'FEATURE_STORE_CREDIT')
                ],
                'resolution': 'allow_multiple_payment_methods'
            },
            {
                'name': 'Scale vs Weight-Based Pricing',
                'conflicts': [
                    ('FEATURE_WEIGHING_SCALE', 'FEATURE_PRICE_BY_WEIGHT')
                ],
                'resolution': 'require_both_for_grocery'
            }
        ]
        
        for scenario in conflict_scenarios:
            print(f"  Testing conflict scenario: {scenario['name']}")
            
            with self.app.test_client() as client:
                # Login
                login_data = {
                    'username': 'featureuser',
                    'password': 'test_password',
                    'tenant_id': str(self.test_tenant.id)
                }
                
                response = client.post('/api/auth/login',
                                     data=json.dumps(login_data),
                                     content_type='application/json')
                
                token = json.loads(response.data)['access_token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # Test each conflict pair
                for feature1, feature2 in scenario['conflicts']:
                    print(f"    Testing conflict: {feature1} vs {feature2}")
                    
                    # Enable first feature
                    feature_manager.enable_feature(feature1, str(self.test_tenant.id))
                    
                    # Try to enable conflicting feature
                    try:
                        feature_manager.enable_feature(feature2, str(self.test_tenant.id))
                        
                        # Check if conflict was detected
                        enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                        
                        # System should either:
                        # 1. Prevent the conflict by not enabling both
                        # 2. Allow both but warn about conflict
                        # 3. Automatically resolve based on rules
                        
                        if feature1 in enabled_features and feature2 in enabled_features:
                            print(f"      Both features enabled - checking resolution")
                            
                            # Test resolution behavior
                            resolution_response = client.get('/api/features/conflicts', headers=headers)
                            self.assertEqual(resolution_response.status_code, 200, "Should get conflict information")
                            
                            conflicts = json.loads(resolution_response.data)
                            self.assertGreater(len(conflicts), 0, "Should detect conflicts")
                            
                            # Test resolution endpoint
                            if scenario['resolution']:
                                resolution_data = {
                                    'conflict_features': [feature1, feature2],
                                    'resolution_strategy': scenario['resolution']
                                }
                                
                                response = client.post('/api/features/resolve-conflict',
                                                     data=json.dumps(resolution_data),
                                                     content_type='application/json',
                                                     headers=headers)
                                
                                self.assertEqual(response.status_code, 200, "Should resolve conflict")
                    
                    finally:
                        # Clean up - disable both features
                        feature_manager.disable_feature(feature1, str(self.test_tenant.id))
                        feature_manager.disable_feature(feature2, str(self.test_tenant.id))
        
        print("✅ Feature conflicts and resolution tests passed")
    
    def test_performance_with_all_features(self):
        """Test performance with all features enabled"""
        print("\n=== Testing Performance with All Features Enabled ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'featureuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Measure performance with no features
            print("  Measuring performance with no features")
            start_time = time.time()
            response = client.get('/api/products', headers=headers)
            no_features_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200, "Should work with no features")
            
            # Enable all features
            print("  Enabling all features")
            for feature in self.all_features:
                feature_manager.enable_feature(feature, str(self.test_tenant.id))
            
            # Verify all features are enabled
            enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
            self.assertEqual(len(enabled_features), len(self.all_features), "All features should be enabled")
            
            # Measure performance with all features
            print("  Measuring performance with all features")
            start_time = time.time()
            response = client.get('/api/products', headers=headers)
            all_features_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 200, "Should work with all features")
            
            # Performance should not degrade significantly
            performance_ratio = all_features_time / no_features_time
            self.assertLess(performance_ratio, 3.0, "Performance with all features should be reasonable")
            
            print(f"    No features time: {no_features_time:.3f}s")
            print(f"    All features time: {all_features_time:.3f}s")
            print(f"    Performance ratio: {performance_ratio:.2f}x")
            
            # Test feature-specific endpoints with all features enabled
            print("  Testing feature-specific endpoints with all features enabled")
            feature_endpoints = [
                ('/api/restaurant/tables', 'FEATURE_TABLE_MANAGEMENT'),
                ('/api/apparel/products', 'FEATURE_SIZE_VARIANTS'),
                ('/api/books/products', 'FEATURE_ISBN_TRACKING'),
                ('/api/grocery/produce', 'FEATURE_WEIGHING_SCALE'),
                ('/api/analytics/dashboard', 'FEATURE_ANALYTICS'),
                ('/api/payments/gateway', 'FEATURE_PAYMENT_GATEWAY'),
                ('/api/notifications/email', 'FEATURE_EMAIL_NOTIFICATIONS')
            ]
            
            for endpoint, feature in feature_endpoints:
                start_time = time.time()
                response = client.get(endpoint, headers=headers)
                endpoint_time = time.time() - start_time
                
                self.assertEqual(response.status_code, 200, f"Endpoint {endpoint} should work with all features")
                self.assertLess(endpoint_time, 2.0, f"Endpoint {endpoint} should respond quickly")
                
                print(f"    {endpoint}: {endpoint_time:.3f}s")
            
            # Test complex operations with all features enabled
            print("  Testing complex operations with all features enabled")
            
            # Create complex order
            order_data = {
                'customer_name': 'Complex Order Customer',
                'order_type': 'Sale',
                'items': [
                    {
                        'product_id': 1,
                        'quantity': 2,
                        'price': '299.00',
                        'variant_id': 1,
                        'special_instructions': 'Test with all features'
                    }
                ],
                'payment_method': 'credit_card',
                'delivery_required': True,
                'notification_preferences': ['email', 'sms'],
                'loyalty_points_applied': True
            }
            
            start_time = time.time()
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            complex_order_time = time.time() - start_time
            
            self.assertEqual(response.status_code, 201, "Complex order should be created")
            self.assertLess(complex_order_time, 3.0, "Complex order should be processed quickly")
            
            print(f"    Complex order creation: {complex_order_time:.3f}s")
        
        print("✅ Performance with all features tests passed")
    
    def test_memory_usage_with_features(self):
        """Test memory usage with different feature combinations"""
        print("\n=== Testing Memory Usage with Feature Combinations ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'featureuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Measure baseline memory usage
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"  Baseline memory usage: {baseline_memory:.1f} MB")
            
            # Test memory usage with different feature loads
            feature_loads = [
                ('Minimal', self.all_features[:5]),
                ('Moderate', self.all_features[:15]),
                ('Heavy', self.all_features[:35]),
                ('Maximum', self.all_features)
            ]
            
            for load_name, features in feature_loads:
                print(f"  Testing {load_name} feature load ({len(features)} features)")
                
                # Clear all features
                for feature in self.all_features:
                    feature_manager.disable_feature(feature, str(self.test_tenant.id))
                
                # Enable feature set
                for feature in features:
                    feature_manager.enable_feature(feature, str(self.test_tenant.id))
                
                # Make multiple requests to stabilize memory
                for _ in range(10):
                    response = client.get('/api/products', headers=headers)
                    self.assertEqual(response.status_code, 200)
                
                # Measure memory usage
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = memory_usage - baseline_memory
                
                print(f"    Memory usage: {memory_usage:.1f} MB (+{memory_increase:.1f} MB)")
                
                # Memory increase should be reasonable
                self.assertLess(memory_increase, 100, f"Memory increase should be reasonable for {load_name} load")
                
                # Memory should not grow excessively
                self.assertLess(memory_usage, 500, f"Total memory usage should be reasonable for {load_name} load")
        
        print("✅ Memory usage with features tests passed")
    
    def _get_feature_endpoint(self, feature):
        """Get the API endpoint for a specific feature"""
        feature_endpoints = {
            'FEATURE_TABLE_MANAGEMENT': '/api/restaurant/tables',
            'FEATURE_RESERVATIONS': '/api/restaurant/reservations',
            'FEATURE_KOT_PRINTING': '/api/restaurant/kot',
            'FEATURE_KITCHEN_DISPLAY': '/api/restaurant/kitchen/display',
            'FEATURE_WAITER_MANAGEMENT': '/api/restaurant/waiters',
            'FEATURE_SHIFT_MANAGEMENT': '/api/restaurant/shifts',
            'FEATURE_SIZE_VARIANTS': '/api/apparel/variants',
            'FEATURE_COLOR_VARIANTS': '/api/apparel/colors',
            'FEATURE_STYLE_VARIANTS': '/api/apparel/styles',
            'FEATURE_EXCHANGE_MANAGEMENT': '/api/apparel/exchanges',
            'FEATURE_ALTERATION_TRACKING': '/api/apparel/alterations',
            'FEATURE_ISBN_TRACKING': '/api/books/isbn',
            'FEATURE_SPECIAL_ORDERS': '/api/books/special-orders',
            'FEATURE_PUBLISHER_MANAGEMENT': '/api/books/publishers',
            'FEATURE_AUTHOR_MANAGEMENT': '/api/books/authors',
            'FEATURE_CATEGORY_MANAGEMENT': '/api/books/categories',
            'FEATURE_WEIGHING_SCALE': '/api/grocery/scales',
            'FEATURE_EXPIRY_TRACKING': '/api/grocery/expiry',
            'FEATURE_BATCH_TRACKING': '/api/grocery/batches',
            'FEATURE_PRICE_BY_WEIGHT': '/api/grocery/price-by-weight',
            'FEATURE_COMBO_OFFERS': '/api/grocery/combos',
            'FEATURE_FRESH_PRODUCE': '/api/grocery/produce',
            'FEATURE_SALES_PROCESSING': '/api/sales',
            'FEATURE_PRODUCT_CATALOG': '/api/products',
            'FEATURE_CUSTOMER_MANAGEMENT': '/api/customers',
            'FEATURE_INVENTORY': '/api/inventory',
            'FEATURE_REPORTING': '/api/reports',
            'FEATURE_ANALYTICS': '/api/analytics',
            'FEATURE_MULTI_STORE': '/api/stores',
            'FEATURE_FRANCHISE_MANAGEMENT': '/api/franchise',
            'FEATURE_LOYALTY_PROGRAM': '/api/loyalty',
            'FEATURE_CRM': '/api/crm',
            'FEATURE_PROMOTIONS': '/api/promotions',
            'FEATURE_DISCOUNTS': '/api/discounts',
            'FEATURE_GIFT_CARDS': '/api/gift-cards',
            'FEATURE_STORE_CREDIT': '/api/store-credit',
            'FEATURE_PAYMENT_GATEWAY': '/api/payments/gateway',
            'FEATURE_CASH_MANAGEMENT': '/api/cash-management',
            'FEATURE_BANK_DEPOSIT': '/api/bank-deposit',
            'FEATURE_EXPENSE_TRACKING': '/api/expenses',
            'FEATURE_ONLINE_ORDERING': '/api/online-orders',
            'FEATURE_DELIVERY': '/api/delivery',
            'FEATURE_PICKUP': '/api/pickup',
            'FEATURE_MOBILE_APP': '/api/mobile',
            'FEATURE_API_ACCESS': '/api/api-access',
            'FEATURE_WEBHOOKS': '/api/webhooks',
            'FEATURE_INTEGRATIONS': '/api/integrations',
            'FEATURE_EMAIL_NOTIFICATIONS': '/api/notifications/email',
            'FEATURE_SMS_NOTIFICATIONS': '/api/notifications/sms',
            'FEATURE_PUSH_NOTIFICATIONS': '/api/notifications/push',
            'FEATURE_OFFLINE_MODE': '/api/offline',
            'FEATURE_DATA_SYNC': '/api/sync',
            'FEATURE_BACKUP_RESTORE': '/api/backup',
            'FEATURE_AUDIT_LOG': '/api/audit',
            'FEATURE_MULTI_CURRENCY': '/api/currency',
            'FEATURE_MULTI_LANGUAGE': '/api/language',
            'FEATURE_TAX_MANAGEMENT': '/api/tax'
        }
        
        return feature_endpoints.get(feature, None)


class TestFeatureDependencyResolution(unittest.TestCase):
    """Test feature dependency resolution"""
    
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
        """Create test data for dependency testing"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Dependency Test',
            subdomain='dependency',
            database_name='dependency_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='dependencyuser',
            email='dependency@example.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
    
    def test_feature_dependencies(self):
        """Test feature dependency resolution"""
        print("\n=== Testing Feature Dependencies ===")
        
        # Define feature dependencies
        dependencies = {
            'FEATURE_KITCHEN_DISPLAY': ['FEATURE_TABLE_MANAGEMENT'],
            'FEATURE_RESERVATIONS': ['FEATURE_TABLE_MANAGEMENT'],
            'FEATURE_EXCHANGE_MANAGEMENT': ['FEATURE_SIZE_VARIANTS', 'FEATURE_SALES_PROCESSING'],
            'FEATURE_SPECIAL_ORDERS': ['FEATURE_ISBN_TRACKING', 'FEATURE_CUSTOMER_MANAGEMENT'],
            'FEATURE_DELIVERY': ['FEATURE_ONLINE_ORDERING', 'FEATURE_CUSTOMER_MANAGEMENT'],
            'FEATURE_WEIGHING_SCALE': ['FEATURE_PRICE_BY_WEIGHT'],
            'FEATURE_BATCH_TRACKING': ['FEATURE_INVENTORY'],
            'FEATURE_LOYALTY_PROGRAM': ['FEATURE_CUSTOMER_MANAGEMENT'],
            'FEATURE_ANALYTICS': ['FEATURE_SALES_PROCESSING'],
            'FEATURE_FRANCHISE_MANAGEMENT': ['FEATURE_MULTI_STORE'],
            'FEATURE_PUSH_NOTIFICATIONS': ['FEATURE_MOBILE_APP'],
            'FEATURE_DATA_SYNC': ['FEATURE_OFFLINE_MODE']
        }
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'dependencyuser',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test each dependency
            for feature, deps in dependencies.items():
                print(f"  Testing dependencies for {feature}")
                
                # Clear all features
                for f in dependencies.keys():
                    feature_manager.disable_feature(f, str(self.test_tenant.id))
                
                # Try to enable feature without dependencies
                response = client.post(f'/api/features/{feature}/enable',
                                     headers=headers)
                
                # Should fail or warn about missing dependencies
                self.assertIn(response.status_code, [400, 409, 200], 
                             f"Should handle missing dependencies for {feature}")
                
                if response.status_code in [400, 409]:
                    # Properly rejected
                    error_data = json.loads(response.data)
                    self.assertIn('dependencies', error_data, "Should list missing dependencies")
                    
                    for dep in deps:
                        self.assertIn(dep, error_data['dependencies'], 
                                      f"Should list {dep} as dependency")
                
                # Enable dependencies first
                for dep in deps:
                    feature_manager.enable_feature(dep, str(self.test_tenant.id))
                    
                    # Verify dependency is enabled
                    enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                    self.assertIn(dep, enabled_features, f"Dependency {dep} should be enabled")
                
                # Now enable the main feature
                response = client.post(f'/api/features/{feature}/enable',
                                     headers=headers)
                
                self.assertEqual(response.status_code, 200, f"Should enable {feature} with dependencies")
                
                # Verify feature is enabled
                enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
                self.assertIn(feature, enabled_features, f"Feature {feature} should be enabled")
                
                # Test that feature works
                endpoint = self._get_feature_endpoint(feature)
                if endpoint:
                    response = client.get(endpoint, headers=headers)
                    self.assertEqual(response.status_code, 200, f"Feature {feature} should work")
                
                # Test dependency removal
                for dep in deps:
                    # Try to disable dependency
                    response = client.post(f'/api/features/{dep}/disable',
                                         headers=headers)
                    
                    # Should either prevent removal or warn about dependent features
                    self.assertIn(response.status_code, [200, 409], 
                                 f"Should handle dependency removal for {dep}")
                    
                    if response.status_code == 409:
                        # Properly rejected
                        error_data = json.loads(response.data)
                        self.assertIn('dependent_features', error_data, "Should list dependent features")
                        self.assertIn(feature, error_data['dependent_features'], 
                                      f"Should list {feature} as dependent")
        
        print("✅ Feature dependencies tests passed")
    
    def _get_feature_endpoint(self, feature):
        """Get the API endpoint for a specific feature"""
        feature_endpoints = {
            'FEATURE_TABLE_MANAGEMENT': '/api/restaurant/tables',
            'FEATURE_RESERVATIONS': '/api/restaurant/reservations',
            'FEATURE_KITCHEN_DISPLAY': '/api/restaurant/kitchen/display',
            'FEATURE_EXCHANGE_MANAGEMENT': '/api/apparel/exchanges',
            'FEATURE_SPECIAL_ORDERS': '/api/books/special-orders',
            'FEATURE_DELIVERY': '/api/delivery',
            'FEATURE_WEIGHING_SCALE': '/api/grocery/scales',
            'FEATURE_BATCH_TRACKING': '/api/grocery/batches',
            'FEATURE_LOYALTY_PROGRAM': '/api/loyalty',
            'FEATURE_ANALYTICS': '/api/analytics',
            'FEATURE_FRANCHISE_MANAGEMENT': '/api/franchise',
            'FEATURE_PUSH_NOTIFICATIONS': '/api/notifications/push',
            'FEATURE_DATA_SYNC': '/api/sync'
        }
        
        return feature_endpoints.get(feature, None)


def run_feature_combination_tests():
    """Run all feature combination tests"""
    print("=" * 80)
    print("FEATURE COMBINATION TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing all possible feature combinations, conflicts, and performance\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFeatureCombinations,
        TestFeatureDependencyResolution
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("FEATURE COMBINATION TEST RESULTS")
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
    success = run_feature_combination_tests()
    
    if success:
        print("\n✅ ALL FEATURE COMBINATION TESTS PASSED!")
        print("Feature combinations are working correctly")
        exit(0)
    else:
        print("\n❌ SOME FEATURE COMBINATION TESTS FAILED!")
        print("Review and fix feature combination issues")
        exit(1)