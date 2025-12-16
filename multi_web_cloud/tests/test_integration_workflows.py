"""
Comprehensive Integration Testing Framework
Tests end-to-end workflows for each retail type, multi-tenant scenarios,
third-party integrations, and offline synchronization.
"""

import unittest
import json
import time
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


class TestRestaurantWorkflows(unittest.TestCase):
    """Test end-to-end restaurant workflows"""
    
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
            name='Restaurant Integration Test',
            subdomain='restaurant-integration',
            database_name='restaurant_integration_db',
            retail_type='restaurant',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test users
        cls.manager_user = User(
            username='restaurant_manager',
            email='manager@restaurant.com',
            password_hash='hashed_password',
            role='manager',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        
        cls.waiter_user = User(
            username='restaurant_waiter',
            email='waiter@restaurant.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        
        db.session.add(cls.manager_user)
        db.session.add(cls.waiter_user)
        db.session.commit()
        
        # Enable restaurant features
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_RESERVATIONS', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_KOT_PRINTING', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', str(cls.test_tenant.id))
        
        # Create restaurant tables
        cls.test_tables = []
        for i in range(5):
            table = RestaurantTable(
                table_number=f'T{i+1}',
                capacity=4,
                location=f'Area {chr(65+i)}',
                tenant_id=str(cls.test_tenant.id),
                status='available'
            )
            cls.test_tables.append(table)
            db.session.add(table)
        
        # Create kitchen stations
        cls.test_stations = []
        stations = ['Main Kitchen', 'Bar']
        for station_name in stations:
            station = KitchenStation(
                name=station_name,
                description=f'{station_name} station',
                tenant_id=str(cls.test_tenant.id),
                status='active'
            )
            cls.test_stations.append(station)
            db.session.add(station)
        
        # Create menu items
        cls.test_menu_items = []
        menu_items = [
            ('Burger', 'Main Course', 299.00, 'Main Kitchen'),
            ('Pizza', 'Main Course', 399.00, 'Main Kitchen'),
            ('Coke', 'Beverage', 49.00, 'Bar'),
            ('Beer', 'Beverage', 99.00, 'Bar')
        ]
        
        for name, category, price, station_name in menu_items:
            menu_item = MenuItem(
                name=name,
                category=category,
                price=Decimal(str(price)),
                tenant_id=str(cls.test_tenant.id),
                status='active'
            )
            cls.test_menu_items.append(menu_item)
            db.session.add(menu_item)
        
        db.session.commit()
    
    def test_complete_restaurant_workflow(self):
        """Test complete restaurant workflow from reservation to payment"""
        print("\n=== Testing Complete Restaurant Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'restaurant_manager',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            manager_headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Create reservation
            reservation_data = {
                'table_number': 'T1',
                'customer_name': 'John Doe',
                'customer_phone': '+1234567890',
                'reservation_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'party_size': 4,
                'special_requests': 'Window seat preferred'
            }
            
            response = client.post('/api/restaurant/reservations',
                                 data=json.dumps(reservation_data),
                                 content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 201, "Reservation should be created")
            reservation_id = json.loads(response.data)['id']
            
            # Step 2: Check in customer
            checkin_data = {
                'status': 'arrived',
                'arrived_at': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/restaurant/reservations/{reservation_id}',
                                data=json.dumps(checkin_data),
                                content_type='application/json',
                                headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "Customer should be checked in")
            
            # Step 3: Create order
            order_data = {
                'customer_name': 'John Doe',
                'order_type': 'Dine-in',
                'table_number': 'T1',
                'items': [
                    {'menu_item_id': self.test_menu_items[0].id, 'quantity': 2, 'notes': 'No onions'},
                    {'menu_item_id': self.test_menu_items[2].id, 'quantity': 2, 'notes': 'Extra ice'}
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 201, "Order should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 4: Send KOT to kitchen
            response = client.post(f'/api/orders/{order_id}/kot',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "KOT should be sent to kitchen")
            
            # Step 5: Update order status
            status_data = {'status': 'Preparing'}
            response = client.put(f'/api/orders/{order_id}/status',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "Order status should be updated")
            
            # Step 6: Mark order as ready
            status_data = {'status': 'Ready'}
            response = client.put(f'/api/orders/{order_id}/status',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "Order should be marked as ready")
            
            # Step 7: Process payment
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': '696.00',  # 2*299 + 2*49
                'card_last_four': '1234'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 201, "Payment should be processed")
            payment_id = json.loads(response.data)['id']
            
            # Step 8: Complete order
            status_data = {'status': 'Completed'}
            response = client.put(f'/api/orders/{order_id}/status',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "Order should be completed")
            
            # Step 9: Update table status
            response = client.put(f'/api/restaurant/tables/{self.test_tables[0].id}',
                                data=json.dumps({'status': 'available'}),
                                content_type='application/json',
                                 headers=manager_headers)
            
            self.assertEqual(response.status_code, 200, "Table should be marked as available")
            
            # Verify complete workflow
            response = client.get(f'/api/orders/{order_id}', headers=manager_headers)
            order_data = json.loads(response.data)
            
            self.assertEqual(order_data['status'], 'Completed', "Order should be completed")
            self.assertEqual(len(order_data['items']), 2, "Order should have 2 items")
            
            response = client.get(f'/api/payments/{payment_id}', headers=manager_headers)
            payment_data = json.loads(response.data)
            
            self.assertEqual(payment_data['status'], 'Completed', "Payment should be completed")
            self.assertEqual(str(payment_data['amount']), '696.00', "Payment amount should be correct")
        
        print("✅ Complete restaurant workflow tests passed")
    
    def test_kitchen_operations_workflow(self):
        """Test kitchen operations workflow"""
        print("\n=== Testing Kitchen Operations Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'restaurant_manager',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            manager_headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Create multiple orders
            order_ids = []
            for i in range(3):
                order_data = {
                    'customer_name': f'Customer {i+1}',
                    'order_type': 'Dine-in',
                    'table_number': f'T{i+1}',
                    'items': [
                        {'menu_item_id': self.test_menu_items[0].id, 'quantity': 1}
                    ]
                }
                
                response = client.post('/api/orders',
                                     data=json.dumps(order_data),
                                     content_type='application/json',
                                     headers=manager_headers)
                
                order_ids.append(json.loads(response.data)['id'])
                
                # Send to kitchen
                client.post(f'/api/orders/{order_ids[-1]}/kot', headers=manager_headers)
            
            # Check kitchen display
            response = client.get('/api/restaurant/kitchen/display', headers=manager_headers)
            self.assertEqual(response.status_code, 200, "Kitchen display should work")
            
            kitchen_orders = json.loads(response.data)
            self.assertEqual(len(kitchen_orders), 3, "Should show 3 orders in kitchen")
            
            # Update order statuses
            for order_id in order_ids:
                # Mark as preparing
                status_data = {'status': 'Preparing'}
                client.put(f'/api/orders/{order_id}/status',
                          data=json.dumps(status_data),
                          content_type='application/json',
                          headers=manager_headers)
                
                # Mark as ready
                status_data = {'status': 'Ready'}
                client.put(f'/api/orders/{order_id}/status',
                          data=json.dumps(status_data),
                          content_type='application/json',
                          headers=manager_headers)
            
            # Verify kitchen display updated
            response = client.get('/api/restaurant/kitchen/display', headers=manager_headers)
            kitchen_orders = json.loads(response.data)
            
            ready_orders = [o for o in kitchen_orders if o['status'] == 'Ready']
            self.assertEqual(len(ready_orders), 3, "All orders should be ready")
        
        print("✅ Kitchen operations workflow tests passed")


class TestApparelWorkflows(unittest.TestCase):
    """Test end-to-end apparel workflows"""
    
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
            name='Apparel Integration Test',
            subdomain='apparel-integration',
            database_name='apparel_integration_db',
            retail_type='apparel',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='apparel_staff',
            email='staff@apparel.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
        
        # Enable apparel features
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(cls.test_tenant.id))
        
        # Create apparel products
        cls.test_products = []
        for i in range(3):
            product = ApparelProduct(
                sku=f'APP{i+1:001}',
                name=f'Apparel Product {i+1}',
                description=f'Description for apparel product {i+1}',
                category='Clothing',
                base_price=Decimal(str(999 + i * 100)),
                tenant_id=str(cls.test_tenant.id),
                status='active'
            )
            cls.test_products.append(product)
            db.session.add(product)
        
        # Create variants
        cls.test_variants = []
        colors = ['Red', 'Blue', 'Black']
        sizes = ['S', 'M', 'L']
        
        for product in cls.test_products:
            for color in colors:
                for size in sizes:
                    variant = ApparelVariant(
                        product_id=product.id,
                        sku=f'{product.sku}-{color[0]}{size}',
                        color=color,
                        size=size,
                        price=product.base_price + Decimal('50'),
                        stock_quantity=10,
                        tenant_id=str(cls.test_tenant.id),
                        status='active'
                    )
                    cls.test_variants.append(variant)
                    db.session.add(variant)
        
        db.session.commit()
    
    def test_apparel_sales_workflow(self):
        """Test complete apparel sales workflow"""
        print("\n=== Testing Apparel Sales Workflow ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'apparel_staff',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Step 1: Browse products with variants
            response = client.get('/api/apparel/products', headers=headers)
            self.assertEqual(response.status_code, 200, "Should browse apparel products")
            
            products = json.loads(response.data)
            self.assertGreater(len(products), 0, "Should have apparel products")
            
            # Step 2: Select specific variant
            selected_variant = self.test_variants[0]
            response = client.get(f'/api/apparel/variants/{selected_variant.id}', headers=headers)
            self.assertEqual(response.status_code, 200, "Should get variant details")
            
            variant_data = json.loads(response.data)
            self.assertEqual(variant_data['sku'], selected_variant.sku, "Should return correct variant")
            
            # Step 3: Create order with variant
            order_data = {
                'customer_name': 'Jane Smith',
                'customer_email': 'jane@example.com',
                'order_type': 'Sale',
                'items': [
                    {
                        'variant_id': selected_variant.id,
                        'quantity': 2,
                        'price': str(selected_variant.price)
                    }
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 4: Process payment
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': str(selected_variant.price * 2),
                'card_last_four': '5678'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Payment should be processed")
            
            # Step 5: Update inventory
            response = client.put(f'/api/apparel/variants/{selected_variant.id}/inventory',
                                data=json.dumps({'stock_change': -2}),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Inventory should be updated")
            
            # Step 6: Complete order
            status_data = {'status': 'Completed'}
            response = client.put(f'/api/orders/{order_id}/status',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Order should be completed")
            
            # Verify inventory updated
            response = client.get(f'/api/apparel/variants/{selected_variant.id}', headers=headers)
            variant_data = json.loads(response.data)
            self.assertEqual(variant_data['stock_quantity'], 8, "Stock should be reduced")
        
        print("✅ Apparel sales workflow tests passed")
    
    def test_exchange_workflow(self):
        """Test apparel exchange workflow"""
        print("\n=== Testing Apparel Exchange Workflow ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'apparel_staff',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create initial order
            original_variant = self.test_variants[0]
            order_data = {
                'customer_name': 'Exchange Customer',
                'customer_email': 'exchange@example.com',
                'order_type': 'Sale',
                'items': [
                    {
                        'variant_id': original_variant.id,
                        'quantity': 1,
                        'price': str(original_variant.price)
                    }
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            order_id = json.loads(response.data)['id']
            
            # Process payment
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': str(original_variant.price),
                'card_last_four': '9012'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            # Complete order
            status_data = {'status': 'Completed'}
            client.put(f'/api/orders/{order_id}/status',
                       data=json.dumps(status_data),
                       content_type='application/json',
                       headers=headers)
            
            # Step 1: Create exchange request
            new_variant = self.test_variants[1]
            exchange_data = {
                'order_id': order_id,
                'customer_name': 'Exchange Customer',
                'customer_phone': '+1234567890',
                'exchange_reason': 'Size too small',
                'exchange_type': 'size_exchange',
                'original_item_sku': original_variant.sku,
                'original_item_size': original_variant.size,
                'original_item_color': original_variant.color,
                'new_item_sku': new_variant.sku,
                'new_item_size': new_variant.size,
                'new_item_color': new_variant.color
            }
            
            response = client.post('/api/apparel/exchanges',
                                 data=json.dumps(exchange_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Exchange should be created")
            exchange_id = json.loads(response.data)['id']
            
            # Step 2: Approve exchange
            approval_data = {
                'status': 'approved',
                'approved_by': 'store_manager',
                'approved_at': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/apparel/exchanges/{exchange_id}',
                                data=json.dumps(approval_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Exchange should be approved")
            
            # Step 3: Process exchange
            process_data = {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/apparel/exchanges/{exchange_id}',
                                data=json.dumps(process_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Exchange should be completed")
            
            # Step 4: Update inventory
            # Return original item
            response = client.put(f'/api/apparel/variants/{original_variant.id}/inventory',
                                data=json.dumps({'stock_change': 1}),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Original item inventory should be updated")
            
            # Give new item
            response = client.put(f'/api/apparel/variants/{new_variant.id}/inventory',
                                data=json.dumps({'stock_change': -1}),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "New item inventory should be updated")
            
            # Verify exchange completed
            response = client.get(f'/api/apparel/exchanges/{exchange_id}', headers=headers)
            exchange_data = json.loads(response.data)
            self.assertEqual(exchange_data['status'], 'completed', "Exchange should be completed")
        
        print("✅ Exchange workflow tests passed")


class TestMultiTenantScenarios(unittest.TestCase):
    """Test multi-tenant scenarios and data isolation"""
    
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
        # Create multiple tenants
        cls.tenant1 = Tenant(
            name='Multi-Tenant 1',
            subdomain='tenant1',
            database_name='tenant1_db',
            retail_type='restaurant',
            status='active'
        )
        
        cls.tenant2 = Tenant(
            name='Multi-Tenant 2',
            subdomain='tenant2',
            database_name='tenant2_db',
            retail_type='apparel',
            status='active'
        )
        
        cls.tenant3 = Tenant(
            name='Multi-Tenant 3',
            subdomain='tenant3',
            database_name='tenant3_db',
            retail_type='books',
            status='active'
        )
        
        db.session.add(cls.tenant1)
        db.session.add(cls.tenant2)
        db.session.add(cls.tenant3)
        
        # Create users for each tenant
        cls.user1 = User(
            username='user1',
            email='user1@tenant1.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.tenant1.id),
            is_active=True
        )
        
        cls.user2 = User(
            username='user2',
            email='user2@tenant2.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.tenant2.id),
            is_active=True
        )
        
        cls.user3 = User(
            username='user3',
            email='user3@tenant3.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.tenant3.id),
            is_active=True
        )
        
        db.session.add(cls.user1)
        db.session.add(cls.user2)
        db.session.add(cls.user3)
        db.session.commit()
        
        # Enable features for each tenant
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(cls.tenant1.id))
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(cls.tenant2.id))
        feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(cls.tenant3.id))
    
    def test_tenant_isolation_workflow(self):
        """Test tenant isolation in workflows"""
        print("\n=== Testing Tenant Isolation Workflow ===")
        
        with self.app.test_client() as client:
            # Login as tenant 1 user
            login_data1 = {
                'username': 'user1',
                'password': 'test_password',
                'tenant_id': str(self.tenant1.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data1),
                                 content_type='application/json')
            
            token1 = json.loads(response.data)['access_token']
            headers1 = {'Authorization': f'Bearer {token1}'}
            
            # Create restaurant table for tenant 1
            table_data = {
                'table_number': 'T1',
                'capacity': 4,
                'location': 'Main Area'
            }
            
            response = client.post('/api/restaurant/tables',
                                 data=json.dumps(table_data),
                                 content_type='application/json',
                                 headers=headers1)
            
            self.assertEqual(response.status_code, 201, "Tenant 1 should create restaurant table")
            
            # Login as tenant 2 user
            login_data2 = {
                'username': 'user2',
                'password': 'test_password',
                'tenant_id': str(self.tenant2.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data2),
                                 content_type='application/json')
            
            token2 = json.loads(response.data)['access_token']
            headers2 = {'Authorization': f'Bearer {token2}'}
            
            # Create apparel product for tenant 2
            product_data = {
                'sku': 'APP001',
                'name': 'Apparel Product',
                'category': 'Clothing',
                'base_price': '999.00'
            }
            
            response = client.post('/api/apparel/products',
                                 data=json.dumps(product_data),
                                 content_type='application/json',
                                 headers=headers2)
            
            self.assertEqual(response.status_code, 201, "Tenant 2 should create apparel product")
            
            # Verify tenant isolation
            # Tenant 1 should not access tenant 2 data
            response = client.get('/api/apparel/products', headers=headers1)
            self.assertEqual(response.status_code, 403, "Tenant 1 should not access apparel features")
            
            # Tenant 2 should not access tenant 1 data
            response = client.get('/api/restaurant/tables', headers=headers2)
            self.assertEqual(response.status_code, 403, "Tenant 2 should not access restaurant features")
            
            # Verify data separation
            response = client.get('/api/users', headers=headers1)
            users1 = json.loads(response.data)
            
            response = client.get('/api/users', headers=headers2)
            users2 = json.loads(response.data)
            
            # Each tenant should only see their own users
            user1_ids = [user['id'] for user in users1]
            user2_ids = [user['id'] for user in users2]
            
            self.assertIn(str(self.user1.id), user1_ids, "Tenant 1 should see their user")
            self.assertNotIn(str(self.user2.id), user1_ids, "Tenant 1 should not see tenant 2 users")
            
            self.assertIn(str(self.user2.id), user2_ids, "Tenant 2 should see their user")
            self.assertNotIn(str(self.user1.id), user2_ids, "Tenant 2 should not see tenant 1 users")
        
        print("✅ Tenant isolation workflow tests passed")
    
    def test_cross_tenant_feature_isolation(self):
        """Test feature isolation across tenants"""
        print("\n=== Testing Cross-Tenant Feature Isolation ===")
        
        with self.app.test_client() as client:
            # Test tenant 1 features
            login_data1 = {
                'username': 'user1',
                'password': 'test_password',
                'tenant_id': str(self.tenant1.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data1),
                                 content_type='application/json')
            
            token1 = json.loads(response.data)['access_token']
            headers1 = {'Authorization': f'Bearer {token1}'}
            
            # Tenant 1 should access restaurant features
            response = client.get('/api/restaurant/tables', headers=headers1)
            self.assertEqual(response.status_code, 200, "Tenant 1 should access restaurant features")
            
            # Tenant 1 should not access apparel features
            response = client.get('/api/apparel/products', headers=headers1)
            self.assertEqual(response.status_code, 403, "Tenant 1 should not access apparel features")
            
            # Test tenant 2 features
            login_data2 = {
                'username': 'user2',
                'password': 'test_password',
                'tenant_id': str(self.tenant2.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data2),
                                 content_type='application/json')
            
            token2 = json.loads(response.data)['access_token']
            headers2 = {'Authorization': f'Bearer {token2}'}
            
            # Tenant 2 should access apparel features
            response = client.get('/api/apparel/products', headers=headers2)
            self.assertEqual(response.status_code, 200, "Tenant 2 should access apparel features")
            
            # Tenant 2 should not access restaurant features
            response = client.get('/api/restaurant/tables', headers=headers2)
            self.assertEqual(response.status_code, 403, "Tenant 2 should not access restaurant features")
            
            # Test tenant 3 features
            login_data3 = {
                'username': 'user3',
                'password': 'test_password',
                'tenant_id': str(self.tenant3.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data3),
                                 content_type='application/json')
            
            token3 = json.loads(response.data)['access_token']
            headers3 = {'Authorization': f'Bearer {token3}'}
            
            # Tenant 3 should access books features
            response = client.get('/api/books/products', headers=headers3)
            self.assertEqual(response.status_code, 200, "Tenant 3 should access books features")
            
            # Tenant 3 should not access other features
            response = client.get('/api/restaurant/tables', headers=headers3)
            self.assertEqual(response.status_code, 403, "Tenant 3 should not access restaurant features")
            
            response = client.get('/api/apparel/products', headers=headers3)
            self.assertEqual(response.status_code, 403, "Tenant 3 should not access apparel features")
        
        print("✅ Cross-tenant feature isolation tests passed")


class TestThirdPartyIntegrations(unittest.TestCase):
    """Test third-party integrations"""
    
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
            name='Integration Test Tenant',
            subdomain='integration',
            database_name='integration_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='integration_user',
            email='integration@test.com',
            password_hash='hashed_password',
            role='admin',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
        
        # Enable integration features
        feature_manager.enable_feature('FEATURE_PAYMENT_GATEWAY', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_EMAIL_NOTIFICATIONS', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_SMS_NOTIFICATIONS', str(cls.test_tenant.id))
    
    @patch('requests.post')
    def test_payment_gateway_integration(self, mock_post):
        """Test payment gateway integration"""
        print("\n=== Testing Payment Gateway Integration ===")
        
        # Mock payment gateway response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'transaction_id': 'txn_123456789',
            'status': 'success',
            'amount': 999.00,
            'currency': 'USD'
        }
        mock_post.return_value = mock_response
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'integration_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create order
            order_data = {
                'customer_name': 'Payment Test Customer',
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 1, 'price': '999.00'}
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            order_id = json.loads(response.data)['id']
            
            # Process payment with gateway
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': '999.00',
                'gateway': 'stripe',
                'card_token': 'tok_test123'
            }
            
            response = client.post('/api/payments/gateway',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Gateway payment should succeed")
            
            # Verify payment gateway was called
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check correct endpoint was called
            self.assertIn('stripe.com', call_args[0][0], "Should call Stripe API")
            
            # Check payment data was sent
            sent_data = json.loads(call_args[1]['data'])
            self.assertEqual(sent_data['amount'], 99900, "Amount should be in cents")
            self.assertEqual(sent_data['currency'], 'usd', "Currency should be USD")
        
        print("✅ Payment gateway integration tests passed")
    
    @patch('smtplib.SMTP')
    def test_email_integration(self, mock_smtp):
        """Test email notification integration"""
        print("\n=== Testing Email Integration ===")
        
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'integration_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create order that should trigger email
            order_data = {
                'customer_name': 'Email Test Customer',
                'customer_email': 'customer@example.com',
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 1, 'price': '999.00'}
                ],
                'send_email_confirmation': True
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order should be created")
            
            # Verify email was sent
            mock_smtp.assert_called_once()
            mock_server.send_message.assert_called_once()
            
            # Check email content
            call_args = mock_server.send_message.call_args
            message = call_args[0][0]
            
            self.assertIn('customer@example.com', message['To'], "Should send to customer email")
            self.assertIn('order confirmation', message['Subject'].lower(), "Should have confirmation subject")
        
        print("✅ Email integration tests passed")
    
    @patch('requests.post')
    def test_sms_integration(self, mock_post):
        """Test SMS notification integration"""
        print("\n=== Testing SMS Integration ===")
        
        # Mock SMS API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message_id': 'msg_123456789',
            'status': 'sent',
            'to': '+1234567890'
        }
        mock_post.return_value = mock_response
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'integration_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create order with SMS notification
            order_data = {
                'customer_name': 'SMS Test Customer',
                'customer_phone': '+1234567890',
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 1, 'price': '999.00'}
                ],
                'send_sms_confirmation': True
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order should be created")
            
            # Verify SMS was sent
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check correct SMS API was called
            self.assertIn('twilio.com', call_args[0][0], "Should call Twilio API")
            
            # Check SMS data was sent
            sent_data = call_args[1]['data']
            self.assertEqual(sent_data['To'], '+1234567890', "Should send to customer phone")
            self.assertIn('order', sent_data['Body'].lower(), "Should mention order")
        
        print("✅ SMS integration tests passed")


class TestOfflineSynchronization(unittest.TestCase):
    """Test offline synchronization and data recovery"""
    
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
            name='Offline Test Tenant',
            subdomain='offline',
            database_name='offline_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        
        # Create test user
        cls.test_user = User(
            username='offline_user',
            email='offline@test.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.test_tenant.id),
            is_active=True
        )
        db.session.add(cls.test_user)
        db.session.commit()
        
        # Enable offline features
        feature_manager.enable_feature('FEATURE_OFFLINE_MODE', str(cls.test_tenant.id))
        feature_manager.enable_feature('FEATURE_DATA_SYNC', str(cls.test_tenant.id))
    
    def test_offline_order_creation(self):
        """Test creating orders in offline mode"""
        print("\n=== Testing Offline Order Creation ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'offline_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Enable offline mode
            response = client.post('/api/offline/enable',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Offline mode should be enabled")
            
            # Create order in offline mode
            order_data = {
                'customer_name': 'Offline Customer',
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 2, 'price': '499.00'}
                ],
                'offline_mode': True
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Offline order should be created")
            order_id = json.loads(response.data)['id']
            
            # Verify order is marked as pending sync
            response = client.get(f'/api/orders/{order_id}', headers=headers)
            order_data = json.loads(response.data)
            self.assertEqual(order_data['sync_status'], 'pending', "Order should be pending sync")
            
            # Create multiple offline orders
            offline_orders = []
            for i in range(3):
                order_data = {
                    'customer_name': f'Offline Customer {i+1}',
                    'order_type': 'Sale',
                    'items': [
                        {'product_id': 1, 'quantity': 1, 'price': '299.00'}
                    ],
                    'offline_mode': True
                }
                
                response = client.post('/api/orders',
                                     data=json.dumps(order_data),
                                     content_type='application/json',
                                     headers=headers)
                
                offline_orders.append(json.loads(response.data)['id'])
            
            # Verify all orders are pending sync
            pending_orders = 0
            for order_id in offline_orders:
                response = client.get(f'/api/orders/{order_id}', headers=headers)
                order_data = json.loads(response.data)
                if order_data['sync_status'] == 'pending':
                    pending_orders += 1
            
            self.assertEqual(pending_orders, 3, "All offline orders should be pending sync")
        
        print("✅ Offline order creation tests passed")
    
    def test_data_synchronization(self):
        """Test data synchronization when back online"""
        print("\n=== Testing Data Synchronization ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'offline_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Enable offline mode and create orders
            client.post('/api/offline/enable', headers=headers)
            
            offline_orders = []
            for i in range(2):
                order_data = {
                    'customer_name': f'Sync Customer {i+1}',
                    'order_type': 'Sale',
                    'items': [
                        {'product_id': 1, 'quantity': 1, 'price': '399.00'}
                    ],
                    'offline_mode': True
                }
                
                response = client.post('/api/orders',
                                     data=json.dumps(order_data),
                                     content_type='application/json',
                                     headers=headers)
                
                offline_orders.append(json.loads(response.data)['id'])
            
            # Disable offline mode (go back online)
            response = client.post('/api/offline/disable',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should disable offline mode")
            
            # Trigger synchronization
            response = client.post('/api/sync/start',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Synchronization should start")
            
            # Check sync status
            response = client.get('/api/sync/status',
                                headers=headers)
            
            sync_data = json.loads(response.data)
            self.assertIn('pending_orders', sync_data, "Should show pending orders")
            self.assertEqual(sync_data['pending_orders'], 2, "Should have 2 pending orders")
            
            # Complete synchronization
            response = client.post('/api/sync/complete',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Synchronization should complete")
            
            # Verify orders are synced
            synced_orders = 0
            for order_id in offline_orders:
                response = client.get(f'/api/orders/{order_id}', headers=headers)
                order_data = json.loads(response.data)
                if order_data['sync_status'] == 'synced':
                    synced_orders += 1
            
            self.assertEqual(synced_orders, 2, "All orders should be synced")
        
        print("✅ Data synchronization tests passed")
    
    def test_conflict_resolution(self):
        """Test conflict resolution during synchronization"""
        print("\n=== Testing Conflict Resolution ===")
        
        with self.app.test_client() as client:
            # Login
            login_data = {
                'username': 'offline_user',
                'password': 'test_password',
                'tenant_id': str(self.test_tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Create order online first
            online_order_data = {
                'customer_name': 'Online Customer',
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 1, 'price': '599.00'}
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(online_order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            online_order_id = json.loads(response.data)['id']
            
            # Enable offline mode and create conflicting order
            client.post('/api/offline/enable', headers=headers)
            
            offline_order_data = {
                'customer_name': 'Online Customer',  # Same customer
                'order_type': 'Sale',
                'items': [
                    {'product_id': 1, 'quantity': 2, 'price': '599.00'}  # Different quantity
                ],
                'offline_mode': True
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(offline_order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            offline_order_id = json.loads(response.data)['id']
            
            # Disable offline mode and sync
            client.post('/api/offline/disable', headers=headers)
            client.post('/api/sync/start', headers=headers)
            
            # Check for conflicts
            response = client.get('/api/sync/conflicts',
                                headers=headers)
            
            conflicts = json.loads(response.data)
            self.assertGreater(len(conflicts), 0, "Should detect conflicts")
            
            # Resolve conflict (keep offline version)
            conflict_resolution = {
                'conflict_id': conflicts[0]['id'],
                'resolution': 'keep_offline',
                'reason': 'Offline version has more items'
            }
            
            response = client.post('/api/sync/resolve',
                                 data=json.dumps(conflict_resolution),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Conflict should be resolved")
            
            # Complete sync
            client.post('/api/sync/complete', headers=headers)
            
            # Verify resolution
            response = client.get(f'/api/orders/{online_order_id}', headers=headers)
            online_order = json.loads(response.data)
            
            response = client.get(f'/api/orders/{offline_order_id}', headers=headers)
            offline_order = json.loads(response.data)
            
            # One should be merged, the other marked as duplicate
            self.assertIn(
                online_order['sync_status'],
                ['synced', 'duplicate'],
                "Online order should be synced or marked as duplicate"
            )
            self.assertEqual(
                offline_order['sync_status'],
                'synced',
                "Offline order should be synced"
            )
        
        print("✅ Conflict resolution tests passed")


def run_integration_workflow_tests():
    """Run all integration workflow tests"""
    print("=" * 80)
    print("COMPREHENSIVE INTEGRATION WORKFLOW TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing end-to-end workflows, multi-tenant scenarios,\n"
          "third-party integrations, and offline synchronization\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestRestaurantWorkflows,
        TestApparelWorkflows,
        TestMultiTenantScenarios,
        TestThirdPartyIntegrations,
        TestOfflineSynchronization
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("COMPREHENSIVE INTEGRATION WORKFLOW TEST RESULTS")
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
    success = run_integration_workflow_tests()
    
    if success:
        print("\n✅ ALL INTEGRATION WORKFLOW TESTS PASSED!")
        print("Integration workflows are working correctly")
        exit(0)
    else:
        print("\n❌ SOME INTEGRATION WORKFLOW TESTS FAILED!")
        print("Review and fix integration issues")
        exit(1)