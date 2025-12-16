"""
Retail-Type Specific Test Scenarios
Tests specific workflows and business logic for each retail type:
- Restaurant: Table management, KOT, order workflows
- Apparel: Size/color variants, exchanges, inventory
- Books: ISBN tracking, special orders, publisher management
- Grocery: Weight-based pricing, expiry tracking, fresh produce
- And other retail types with their specific workflows
"""

import unittest
import json
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


class TestRestaurantScenarios(unittest.TestCase):
    """Test restaurant-specific scenarios and workflows"""
    
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
        """Create test data for restaurant scenarios"""
        # Create restaurant tenant
        cls.tenant = Tenant(
            name='Restaurant Scenario Test',
            subdomain='restaurant-scenario',
            database_name='restaurant_scenario_db',
            retail_type='restaurant',
            status='active'
        )
        db.session.add(cls.tenant)
        
        # Create restaurant staff
        cls.manager = User(
            username='restaurant_manager',
            email='manager@restaurant.com',
            password_hash='hashed_password',
            role='manager',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        cls.waiter = User(
            username='restaurant_waiter',
            email='waiter@restaurant.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        cls.chef = User(
            username='restaurant_chef',
            email='chef@restaurant.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        db.session.add(cls.manager)
        db.session.add(cls.waiter)
        db.session.add(cls.chef)
        
        # Enable restaurant features
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_RESERVATIONS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_KOT_PRINTING', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_WAITER_MANAGEMENT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_SHIFT_MANAGEMENT', str(cls.tenant.id))
        
        # Create restaurant tables
        cls.tables = []
        for i in range(10):
            table = RestaurantTable(
                table_number=f'T{i+1:02d}',
                capacity=2 + (i % 4),  # 2-6 capacity
                location=f'Area {chr(65 + (i % 3))}',  # Areas A, B, C
                description=f'Table {i+1} - {2 + (i % 4)} seats',
                tenant_id=str(cls.tenant.id),
                status='available'
            )
            cls.tables.append(table)
            db.session.add(table)
        
        # Create kitchen stations
        cls.stations = []
        stations = [
            ('Main Kitchen', 'Main cooking station'),
            ('Grill Station', 'Grilling and BBQ'),
            ('Bar', 'Beverages and cocktails'),
            ('Dessert Station', 'Desserts and sweets')
        ]
        
        for name, description in stations:
            station = KitchenStation(
                name=name,
                description=description,
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.stations.append(station)
            db.session.add(station)
        
        # Create restaurant shifts
        cls.shifts = []
        shifts = [
            ('Breakfast', '06:00', '14:00'),
            ('Lunch', '14:00', '22:00'),
            ('Dinner', '22:00', '06:00')
        ]
        
        for name, start_time, end_time in shifts:
            shift = RestaurantShift(
                name=name,
                start_time=start_time,
                end_time=end_time,
                description=f'{name} shift',
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.shifts.append(shift)
            db.session.add(shift)
        
        # Create menu items
        cls.menu_items = []
        menu_data = [
            ('Classic Burger', 'Main Course', Decimal('299.00'), 'Main Kitchen'),
            ('Grilled Chicken', 'Main Course', Decimal('399.00'), 'Grill Station'),
            ('Caesar Salad', 'Starter', Decimal('199.00'), 'Main Kitchen'),
            ('French Fries', 'Side Dish', Decimal('99.00'), 'Main Kitchen'),
            ('Cocktail', 'Beverage', Decimal('249.00'), 'Bar'),
            ('Soft Drink', 'Beverage', Decimal('49.00'), 'Bar'),
            ('Ice Cream', 'Dessert', Decimal('149.00'), 'Dessert Station'),
            ('Coffee', 'Beverage', Decimal('79.00'), 'Bar')
        ]
        
        for name, category, price, station in menu_data:
            menu_item = MenuItem(
                name=name,
                category=category,
                price=price,
                station=station,
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.menu_items.append(menu_item)
            db.session.add(menu_item)
        
        db.session.commit()
    
    def test_table_management_workflow(self):
        """Test complete table management workflow"""
        print("\n=== Testing Table Management Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'restaurant_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Check table availability
            response = client.get('/api/restaurant/tables/available', headers=headers)
            self.assertEqual(response.status_code, 200, "Should get available tables")
            
            available_tables = json.loads(response.data)
            self.assertEqual(len(available_tables), 10, "All tables should be available")
            
            # Step 2: Reserve a table
            reservation_data = {
                'table_number': 'T01',
                'customer_name': 'John Doe',
                'customer_phone': '+1234567890',
                'reservation_time': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                'party_size': 4,
                'special_requests': 'Window seat preferred'
            }
            
            response = client.post('/api/restaurant/reservations',
                                 data=json.dumps(reservation_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Reservation should be created")
            reservation_id = json.loads(response.data)['id']
            
            # Step 3: Check table status after reservation
            response = client.get('/api/restaurant/tables/T01', headers=headers)
            table_data = json.loads(response.data)
            self.assertEqual(table_data['status'], 'reserved', "Table should be reserved")
            
            # Step 4: Customer arrives - check in
            checkin_data = {
                'status': 'arrived',
                'arrived_at': datetime.utcnow().isoformat(),
                'actual_party_size': 4
            }
            
            response = client.put(f'/api/restaurant/reservations/{reservation_id}',
                                data=json.dumps(checkin_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Check-in should succeed")
            
            # Step 5: Update table status to occupied
            response = client.put(f'/api/restaurant/tables/T01',
                                data=json.dumps({'status': 'occupied'}),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Table should be marked occupied")
            
            # Step 6: Create order for the table
            order_data = {
                'customer_name': 'John Doe',
                'order_type': 'Dine-in',
                'table_number': 'T01',
                'items': [
                    {'menu_item_id': self.menu_items[0].id, 'quantity': 2, 'notes': 'No onions'},
                    {'menu_item_id': self.menu_items[3].id, 'quantity': 1, 'notes': 'Extra crispy'},
                    {'menu_item_id': self.menu_items[4].id, 'quantity': 2, 'notes': 'Less ice'}
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 7: Send KOT to kitchen
            response = client.post(f'/api/orders/{order_id}/kot',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "KOT should be sent to kitchen")
            
            # Step 8: Update order status through kitchen workflow
            statuses = ['Preparing', 'Ready', 'Served']
            for status in statuses:
                status_data = {'status': status}
                response = client.put(f'/api/orders/{order_id}/status',
                                    data=json.dumps(status_data),
                                    content_type='application/json',
                                    headers=headers)
                
                self.assertEqual(response.status_code, 200, f"Order status should be updated to {status}")
            
            # Step 9: Process payment
            order_total = (2 * 299) + 99 + (2 * 249)  # Calculate total
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': str(order_total),
                'card_last_four': '1234'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Payment should be processed")
            
            # Step 10: Complete order and free table
            status_data = {'status': 'Completed'}
            response = client.put(f'/api/orders/{order_id}/status',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Order should be completed")
            
            # Step 11: Clean table and make available
            response = client.put(f'/api/restaurant/tables/T01',
                                data=json.dumps({'status': 'available'}),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Table should be available again")
        
        print("✅ Table management workflow tests passed")
    
    def test_kitchen_operations_workflow(self):
        """Test kitchen operations and KOT workflow"""
        print("\n=== Testing Kitchen Operations Workflow ===")
        
        with self.app.test_client() as client:
            # Login as chef
            login_data = {
                'username': 'restaurant_chef',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            chef_token = json.loads(response.data)['access_token']
            chef_headers = {'Authorization': f'Bearer {chef_token}'}
            
            # Step 1: Check kitchen display
            response = client.get('/api/restaurant/kitchen/display', headers=chef_headers)
            self.assertEqual(response.status_code, 200, "Should access kitchen display")
            
            # Step 2: Create multiple orders
            order_ids = []
            for i in range(3):
                order_data = {
                    'customer_name': f'Kitchen Customer {i+1}',
                    'order_type': 'Dine-in',
                    'table_number': f'T{i+2:02d}',
                    'items': [
                        {'menu_item_id': self.menu_items[i].id, 'quantity': 1, 'notes': f'Order {i+1} notes'}
                    ]
                }
                
                response = client.post('/api/orders',
                                     data=json.dumps(order_data),
                                     content_type='application/json',
                                     headers=chef_headers)
                
                order_ids.append(json.loads(response.data)['id'])
                
                # Send to kitchen
                client.post(f'/api/orders/{order_ids[-1]}/kot', headers=chef_headers)
            
            # Step 3: Check kitchen queue
            response = client.get('/api/restaurant/kitchen/queue', headers=chef_headers)
            self.assertEqual(response.status_code, 200, "Should get kitchen queue")
            
            kitchen_queue = json.loads(response.data)
            self.assertEqual(len(kitchen_queue), 3, "Should have 3 orders in queue")
            
            # Step 4: Process orders in kitchen
            for i, order_id in enumerate(order_ids):
                # Start preparing
                status_data = {'status': 'Preparing', 'chef_id': self.chef.id}
                response = client.put(f'/api/orders/{order_id}/status',
                                    data=json.dumps(status_data),
                                    content_type='application/json',
                                    headers=chef_headers)
                
                self.assertEqual(response.status_code, 200, f"Order {i+1} preparation should start")
                
                # Mark as ready
                status_data = {'status': 'Ready'}
                response = client.put(f'/api/orders/{order_id}/status',
                                    data=json.dumps(status_data),
                                    content_type='application/json',
                                    headers=chef_headers)
                
                self.assertEqual(response.status_code, 200, f"Order {i+1} should be ready")
            
            # Step 5: Check station-specific orders
            for station in self.stations:
                response = client.get(f'/api/restaurant/kitchen/station/{station.name}',
                                    headers=chef_headers)
                
                self.assertEqual(response.status_code, 200, f"Should get {station.name} orders")
            
            # Step 6: Update station status
            for station in self.stations:
                response = client.put(f'/api/restaurant/kitchen/station/{station.id}',
                                    data=json.dumps({'status': 'busy', 'current_orders': 2}),
                                    content_type='application/json',
                                    headers=chef_headers)
                
                self.assertEqual(response.status_code, 200, f"Station {station.name} status should update")
        
        print("✅ Kitchen operations workflow tests passed")
    
    def test_shift_management_workflow(self):
        """Test shift management and handover"""
        print("\n=== Testing Shift Management Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'restaurant_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Start breakfast shift
            shift_data = {
                'shift_id': self.shifts[0].id,  # Breakfast shift
                'staff_assigned': [self.waiter.id, self.chef.id],
                'started_at': datetime.utcnow().isoformat(),
                'notes': 'Normal breakfast shift'
            }
            
            response = client.post('/api/restaurant/shifts/start',
                                 data=json.dumps(shift_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Breakfast shift should start")
            
            # Step 2: Create orders during shift
            for i in range(2):
                order_data = {
                    'customer_name': f'Shift Customer {i+1}',
                    'order_type': 'Dine-in',
                    'table_number': f'T{i+3:02d}',
                    'items': [
                        {'menu_item_id': self.menu_items[0].id, 'quantity': 1}
                    ]
                }
                
                response = client.post('/api/orders',
                                     data=json.dumps(order_data),
                                     content_type='application/json',
                                     headers=headers)
                
                # Process order
                order_id = json.loads(response.data)['id']
                client.post(f'/api/orders/{order_id}/kot', headers=headers)
            
            # Step 3: Get shift summary
            response = client.get('/api/restaurant/shifts/current/summary',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get current shift summary")
            shift_summary = json.loads(response.data)
            self.assertGreater(shift_summary['orders_count'], 0, "Should have orders in shift")
            
            # Step 4: End breakfast shift
            end_shift_data = {
                'ended_at': datetime.utcnow().isoformat(),
                'total_orders': shift_summary['orders_count'],
                'total_revenue': shift_summary['total_revenue'],
                'notes': 'Shift completed successfully'
            }
            
            response = client.put(f'/api/restaurant/shifts/{self.shifts[0].id}/end',
                                data=json.dumps(end_shift_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Breakfast shift should end")
            
            # Step 5: Start lunch shift (handover)
            lunch_shift_data = {
                'shift_id': self.shifts[1].id,  # Lunch shift
                'staff_assigned': [self.waiter.id, self.chef.id],
                'started_at': datetime.utcnow().isoformat(),
                'handover_notes': 'All tables cleaned, kitchen ready'
            }
            
            response = client.post('/api/restaurant/shifts/start',
                                 data=json.dumps(lunch_shift_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Lunch shift should start")
            
            # Step 6: Verify handover information
            response = client.get('/api/restaurant/shifts/handover',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get handover information")
            handover_data = json.loads(response.data)
            self.assertIn('previous_shift', handover_data, "Should include previous shift info")
        
        print("✅ Shift management workflow tests passed")


class TestApparelScenarios(unittest.TestCase):
    """Test apparel-specific scenarios and workflows"""
    
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
        """Create test data for apparel scenarios"""
        # Create apparel tenant
        cls.tenant = Tenant(
            name='Apparel Scenario Test',
            subdomain='apparel-scenario',
            database_name='apparel_scenario_db',
            retail_type='apparel',
            status='active'
        )
        db.session.add(cls.tenant)
        
        # Create apparel staff
        cls.manager = User(
            username='apparel_manager',
            email='manager@apparel.com',
            password_hash='hashed_password',
            role='manager',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        cls.sales_associate = User(
            username='apparel_sales',
            email='sales@apparel.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        db.session.add(cls.manager)
        db.session.add(cls.sales_associate)
        
        # Enable apparel features
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_STYLE_VARIANTS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_ALTERATION_TRACKING', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_INVENTORY_TRACKING', str(cls.tenant.id))
        
        # Create apparel products
        cls.products = []
        product_data = [
            ('Classic T-Shirt', 'Basic cotton t-shirt', 'Tops', Decimal('599.00')),
            ('Denim Jeans', 'Classic blue denim jeans', 'Bottoms', Decimal('1299.00')),
            ('Leather Jacket', 'Genuine leather jacket', 'Outerwear', Decimal('2999.00')),
            ('Running Shoes', 'Athletic running shoes', 'Footwear', Decimal('1999.00')),
            ('Wool Sweater', 'Warm wool sweater', 'Knitwear', Decimal('899.00'))
        ]
        
        for name, description, category, base_price in product_data:
            product = ApparelProduct(
                sku=f'APP{len(cls.products)+1:03d}',
                name=name,
                description=description,
                category=category,
                brand='Test Brand',
                base_price=base_price,
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.products.append(product)
            db.session.add(product)
        
        db.session.commit()
        
        # Create size matrix for each product
        cls.size_matrices = []
        for product in cls.products:
            size_matrix = ApparelSizeMatrix(
                product_id=product.id,
                size_chart='Standard',
                sizes=['XS', 'S', 'M', 'L', 'XL', 'XXL'],
                size_mappings={
                    'XS': {'chest': 34, 'waist': 28, 'length': 26},
                    'S': {'chest': 36, 'waist': 30, 'length': 27},
                    'M': {'chest': 38, 'waist': 32, 'length': 28},
                    'L': {'chest': 40, 'waist': 34, 'length': 29},
                    'XL': {'chest': 42, 'waist': 36, 'length': 30},
                    'XXL': {'chest': 44, 'waist': 38, 'length': 31}
                },
                tenant_id=str(cls.tenant.id)
            )
            cls.size_matrices.append(size_matrix)
            db.session.add(size_matrix)
        
        # Create variants for each product
        cls.variants = []
        colors = ['Red', 'Blue', 'Black', 'White', 'Gray']
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        
        for product in cls.products:
            for color in colors:
                for size in sizes:
                    variant = ApparelVariant(
                        product_id=product.id,
                        sku=f'{product.sku}-{color[0]}{size}',
                        color=color,
                        size=size,
                        price=product.base_price + Decimal('50'),  # Color/size premium
                        stock_quantity=10 + (hash(color + size) % 20),  # Random stock
                        tenant_id=str(cls.tenant.id),
                        status='active'
                    )
                    cls.variants.append(variant)
                    db.session.add(variant)
        
        db.session.commit()
    
    def test_variant_management_workflow(self):
        """Test complete variant management workflow"""
        print("\n=== Testing Variant Management Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'apparel_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Create new product with variants
            product_data = {
                'sku': 'APP006',
                'name': 'Test Product',
                'description': 'Test product for variant workflow',
                'category': 'Tops',
                'brand': 'Test Brand',
                'base_price': '799.00',
                'has_variants': True,
                'colors': ['Green', 'Purple'],
                'sizes': ['S', 'M', 'L'],
                'size_chart': 'Standard'
            }
            
            response = client.post('/api/apparel/products',
                                 data=json.dumps(product_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Product with variants should be created")
            product_id = json.loads(response.data)['id']
            
            # Step 2: Check generated variants
            response = client.get(f'/api/apparel/products/{product_id}/variants',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get product variants")
            variants = json.loads(response.data)
            self.assertEqual(len(variants), 6, "Should have 6 variants (2 colors x 3 sizes)")
            
            # Step 3: Update variant stock
            for variant in variants[:3]:  # Update first 3 variants
                stock_data = {'stock_quantity': 25}
                response = client.put(f'/api/apparel/variants/{variant["id"]}/stock',
                                    data=json.dumps(stock_data),
                                    content_type='application/json',
                                    headers=headers)
                
                self.assertEqual(response.status_code, 200, "Variant stock should update")
            
            # Step 4: Create order with specific variants
            order_data = {
                'customer_name': 'Variant Customer',
                'order_type': 'Sale',
                'items': [
                    {
                        'variant_id': variants[0]['id'],
                        'quantity': 2,
                        'price': variants[0]['price']
                    },
                    {
                        'variant_id': variants[1]['id'],
                        'quantity': 1,
                        'price': variants[1]['price']
                    }
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order with variants should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 5: Process payment
            payment_data = {
                'order_id': order_id,
                'payment_method': 'credit_card',
                'amount': str(2 * Decimal(variants[0]['price']) + Decimal(variants[1]['price'])),
                'card_last_four': '5678'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Payment should be processed")
            
            # Step 6: Update inventory after sale
            for item in json.loads(response.data)['items']:
                stock_data = {'stock_change': -item['quantity']}
                response = client.put(f'/api/apparel/variants/{item["variant_id"]}/inventory',
                                    data=json.dumps(stock_data),
                                    content_type='application/json',
                                    headers=headers)
                
                self.assertEqual(response.status_code, 200, "Inventory should update after sale")
            
            # Step 7: Check variant availability
            response = client.get(f'/api/apparel/products/{product_id}/availability',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should check availability")
            availability = json.loads(response.data)
            
            for variant_info in availability:
                if variant_info['variant_id'] == variants[0]['id']:
                    self.assertEqual(variant_info['available_quantity'], 23, "Stock should be reduced")
        
        print("✅ Variant management workflow tests passed")
    
    def test_exchange_management_workflow(self):
        """Test complete exchange management workflow"""
        print("\n=== Testing Exchange Management Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'apparel_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Create original sale
            original_variant = self.variants[0]
            order_data = {
                'customer_name': 'Exchange Customer',
                'customer_email': 'exchange@example.com',
                'customer_phone': '+1234567890',
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
            
            self.assertEqual(response.status_code, 201, "Original order should be created")
            original_order_id = json.loads(response.data)['id']
            
            # Process payment
            payment_data = {
                'order_id': original_order_id,
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
            client.put(f'/api/orders/{original_order_id}/status',
                       data=json.dumps(status_data),
                       content_type='application/json',
                       headers=headers)
            
            # Step 2: Customer requests exchange
            new_variant = self.variants[1]  # Different size/color
            exchange_data = {
                'order_id': original_order_id,
                'customer_name': 'Exchange Customer',
                'customer_phone': '+1234567890',
                'customer_email': 'exchange@example.com',
                'exchange_reason': 'Size too small',
                'exchange_type': 'size_exchange',
                'original_item_sku': original_variant.sku,
                'original_item_size': original_variant.size,
                'original_item_color': original_variant.color,
                'new_item_sku': new_variant.sku,
                'new_item_size': new_variant.size,
                'new_item_color': new_variant.color,
                'exchange_date': datetime.utcnow().isoformat(),
                'notes': 'Customer wants larger size'
            }
            
            response = client.post('/api/apparel/exchanges',
                                 data=json.dumps(exchange_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Exchange request should be created")
            exchange_id = json.loads(response.data)['id']
            
            # Step 3: Process exchange approval
            approval_data = {
                'status': 'approved',
                'approved_by': 'store_manager',
                'approved_at': datetime.utcnow().isoformat(),
                'approval_notes': 'Exchange approved - size difference confirmed',
                'price_adjustment': '0.00'  # No price difference
            }
            
            response = client.put(f'/api/apparel/exchanges/{exchange_id}',
                                data=json.dumps(approval_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Exchange should be approved")
            
            # Step 4: Process exchange (give new item, receive old item)
            process_data = {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'processed_by': 'store_associate',
                'new_item_given': True,
                'original_item_received': True,
                'original_item_condition': 'Good',
                'notes': 'Exchange completed successfully'
            }
            
            response = client.put(f'/api/apparel/exchanges/{exchange_id}',
                                data=json.dumps(process_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Exchange should be completed")
            
            # Step 5: Update inventory
            # Return original item to inventory
            return_data = {'stock_change': 1}
            response = client.put(f'/api/apparel/variants/{original_variant.id}/inventory',
                                data=json.dumps(return_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Original item should be returned to inventory")
            
            # Remove new item from inventory
            give_data = {'stock_change': -1}
            response = client.put(f'/api/apparel/variants/{new_variant.id}/inventory',
                                data=json.dumps(give_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "New item should be removed from inventory")
            
            # Step 6: Verify exchange record
            response = client.get(f'/api/apparel/exchanges/{exchange_id}',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get exchange details")
            exchange_details = json.loads(response.data)
            self.assertEqual(exchange_details['status'], 'completed', "Exchange should be completed")
            self.assertEqual(exchange_details['original_item_sku'], original_variant.sku, "Original SKU should match")
            self.assertEqual(exchange_details['new_item_sku'], new_variant.sku, "New SKU should match")
            
            # Step 7: Check exchange history
            response = client.get('/api/apparel/exchanges/history',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get exchange history")
            exchange_history = json.loads(response.data)
            self.assertGreater(len(exchange_history), 0, "Should have exchange history")
        
        print("✅ Exchange management workflow tests passed")
    
    def test_inventory_tracking_workflow(self):
        """Test inventory tracking and low stock alerts"""
        print("\n=== Testing Inventory Tracking Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'apparel_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Check current inventory levels
            response = client.get('/api/apparel/inventory/summary',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get inventory summary")
            inventory_summary = json.loads(response.data)
            
            total_variants = inventory_summary['total_variants']
            total_stock = inventory_summary['total_stock']
            low_stock_items = inventory_summary['low_stock_items']
            
            self.assertGreater(total_variants, 0, "Should have variants")
            self.assertGreater(total_stock, 0, "Should have stock")
            
            # Step 2: Create sales to reduce stock
            for i in range(3):
                variant = self.variants[i]
                order_data = {
                    'customer_name': f'Inventory Customer {i+1}',
                    'order_type': 'Sale',
                    'items': [
                        {
                            'variant_id': variant.id,
                            'quantity': 5,  # Sell 5 units
                            'price': str(variant.price)
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
                    'payment_method': 'cash',
                    'amount': str(5 * variant.price)
                }
                
                client.post('/api/payments',
                          data=json.dumps(payment_data),
                          content_type='application/json',
                          headers=headers)
                
                # Update inventory
                stock_data = {'stock_change': -5}
                client.put(f'/api/apparel/variants/{variant.id}/inventory',
                          data=json.dumps(stock_data),
                          content_type='application/json',
                          headers=headers)
            
            # Step 3: Check for low stock alerts
            response = client.get('/api/apparel/inventory/low-stock',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should check low stock")
            low_stock = json.loads(response.data)
            
            # Should have items with low stock
            self.assertGreater(len(low_stock), 0, "Should have low stock items")
            
            for item in low_stock:
                self.assertLessEqual(item['stock_quantity'], 10, "Low stock threshold should be 10")
            
            # Step 4: Create stock adjustment
            adjustment_data = {
                'variant_id': self.variants[0].id,
                'adjustment_type': 'restock',
                'quantity': 50,
                'reason': 'New stock received',
                'adjusted_by': 'inventory_manager',
                'adjusted_at': datetime.utcnow().isoformat()
            }
            
            response = client.post('/api/apparel/inventory/adjust',
                                 data=json.dumps(adjustment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Stock adjustment should be created")
            
            # Step 5: Verify updated inventory
            response = client.get(f'/api/apparel/variants/{self.variants[0].id}',
                                headers=headers)
            
            variant_data = json.loads(response.data)
            expected_stock = self.variants[0].stock_quantity - 5 + 50  # Original - sold + restocked
            self.assertEqual(variant_data['stock_quantity'], expected_stock, "Stock should be updated correctly")
            
            # Step 6: Generate inventory report
            response = client.get('/api/apparel/inventory/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate inventory report")
            inventory_report = json.loads(response.data)
            
            self.assertIn('total_value', inventory_report, "Report should include total value")
            self.assertIn('categories', inventory_report, "Report should include categories")
            self.assertIn('movements', inventory_report, "Report should include movements")
        
        print("✅ Inventory tracking workflow tests passed")


class TestBooksScenarios(unittest.TestCase):
    """Test books-specific scenarios and workflows"""
    
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
        """Create test data for books scenarios"""
        # Create books tenant
        cls.tenant = Tenant(
            name='Books Scenario Test',
            subdomain='books-scenario',
            database_name='books_scenario_db',
            retail_type='books',
            status='active'
        )
        db.session.add(cls.tenant)
        
        # Create books staff
        cls.manager = User(
            username='books_manager',
            email='manager@books.com',
            password_hash='hashed_password',
            role='manager',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        cls.librarian = User(
            username='books_librarian',
            email='librarian@books.com',
            password_hash='hashed_password',
            role='staff',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        db.session.add(cls.manager)
        db.session.add(cls.librarian)
        
        # Enable books features
        feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_SPECIAL_ORDERS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_PUBLISHER_MANAGEMENT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_AUTHOR_MANAGEMENT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_CATEGORY_MANAGEMENT', str(cls.tenant.id))
        
        # Create authors
        cls.authors = []
        author_data = [
            ('John Author', 'Fiction writer with 10+ years experience', 'Fiction'),
            ('Jane Writer', 'Non-fiction specialist', 'Non-Fiction'),
            ('Robert Scholar', 'Technical book author', 'Technical'),
            ('Mary Poet', 'Poetry and literature', 'Poetry')
        ]
        
        for name, description, specialty in author_data:
            author = BookAuthor(
                name=name,
                description=description,
                specialty=specialty,
                tenant_id=str(cls.tenant.id)
            )
            cls.authors.append(author)
            db.session.add(author)
        
        # Create publishers
        cls.publishers = []
        publisher_data = [
            ('Fiction Press', 'Leading fiction publisher', 'Fiction'),
            ('Tech Books Inc', 'Technical publications', 'Technical'),
            ('Academic Publishing', 'Scholarly works', 'Academic'),
            ('Children Books Co', 'Children literature', "Children's")
        ]
        
        for name, description, focus in publisher_data:
            publisher = BookPublisher(
                name=name,
                description=description,
                focus=focus,
                tenant_id=str(cls.tenant.id)
            )
            cls.publishers.append(publisher)
            db.session.add(publisher)
        
        # Create categories
        cls.categories = []
        category_data = [
            ('Fiction', 'Fictional literature'),
            ('Non-Fiction', 'Non-fictional works'),
            ('Technical', 'Technical and reference books'),
            ('Academic', 'Scholarly publications'),
            ('Children', "Children's books"),
            ('Poetry', 'Poetry collections')
        ]
        
        for name, description in category_data:
            category = BookCategory(
                name=name,
                description=description,
                tenant_id=str(cls.tenant.id)
            )
            cls.categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        
        # Create books
        cls.books = []
        book_data = [
            ('The Great Novel', '978-3-16-148410-0', cls.authors[0].id, cls.publishers[0].id, cls.categories[0].id, Decimal('499.00'), 350, '2023', 'Fiction'),
            ('Technical Guide', '978-1-234-56789-0', cls.authors[2].id, cls.publishers[1].id, cls.categories[2].id, Decimal('899.00'), 500, '2023', 'Technical'),
            ('Learning Python', '978-0-123-45678-9', cls.authors[2].id, cls.publishers[1].id, cls.categories[2].id, Decimal('799.00'), 450, '2022', 'Programming'),
            ('History Book', '978-9-876-54321-1', cls.authors[1].id, cls.publishers[2].id, cls.categories[1].id, Decimal('699.00'), 300, '2023', 'History'),
            ('Children Story', '978-5-555-12345-6', cls.authors[3].id, cls.publishers[3].id, cls.categories[4].id, Decimal('199.00'), 100, '2023', "Children's")
        ]
        
        for title, isbn, author_id, publisher_id, category_id, price, pages, year, genre in book_data:
            book = BookProduct(
                isbn=isbn,
                title=title,
                author_id=author_id,
                publisher_id=publisher_id,
                category_id=category_id,
                price=price,
                pages=pages,
                publication_year=int(year),
                language='English',
                genre=genre,
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.books.append(book)
            db.session.add(book)
        
        db.session.commit()
    
    def test_isbn_tracking_workflow(self):
        """Test ISBN tracking and validation workflow"""
        print("\n=== Testing ISBN Tracking Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'books_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Validate ISBN format
            valid_isbns = [
                '978-3-16-148410-0',
                '978-1-234-56789-0',
                '978-0-123-45678-9'
            ]
            
            for isbn in valid_isbns:
                response = client.get(f'/api/books/isbn/validate/{isbn}',
                                    headers=headers)
                
                self.assertEqual(response.status_code, 200, f"ISBN {isbn} should be valid")
                validation_result = json.loads(response.data)
                self.assertTrue(validation_result['is_valid'], "ISBN should be valid")
            
            # Step 2: Test invalid ISBNs
            invalid_isbns = [
                '978-3-16-148410',  # Missing check digit
                '978-1-234-567890',  # Too many digits
                '978-0-123-4567-89',  # Wrong format
                '1234567890123'  # Not ISBN format
            ]
            
            for isbn in invalid_isbns:
                response = client.get(f'/api/books/isbn/validate/{isbn}',
                                    headers=headers)
                
                self.assertEqual(response.status_code, 200, f"Should validate ISBN {isbn}")
                validation_result = json.loads(response.data)
                self.assertFalse(validation_result['is_valid'], "ISBN should be invalid")
            
            # Step 3: Create book with ISBN
            book_data = {
                'isbn': '978-2-345-67890-1',
                'title': 'Test Book with ISBN',
                'author_id': self.authors[0].id,
                'publisher_id': self.publishers[0].id,
                'category_id': self.categories[0].id,
                'price': '599.00',
                'pages': 400,
                'publication_year': 2023,
                'language': 'English',
                'genre': 'Fiction'
            }
            
            response = client.post('/api/books/products',
                                 data=json.dumps(book_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Book with ISBN should be created")
            book_id = json.loads(response.data)['id']
            
            # Step 4: Search by ISBN
            response = client.get(f'/api/books/isbn/978-2-345-67890-1',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should find book by ISBN")
            book_result = json.loads(response.data)
            self.assertEqual(book_result['id'], book_id, "Should find correct book")
            
            # Step 5: Check for duplicate ISBN
            duplicate_data = {
                'isbn': '978-2-345-67890-1',  # Same ISBN
                'title': 'Duplicate Book',
                'author_id': self.authors[1].id,
                'publisher_id': self.publishers[1].id,
                'category_id': self.categories[1].id,
                'price': '699.00',
                'pages': 350,
                'publication_year': 2023,
                'language': 'English',
                'genre': 'Non-Fiction'
            }
            
            response = client.post('/api/books/products',
                                 data=json.dumps(duplicate_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 409, "Should reject duplicate ISBN")
            
            # Step 6: Generate ISBN report
            response = client.get('/api/books/isbn/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate ISBN report")
            isbn_report = json.loads(response.data)
            
            self.assertIn('total_books', isbn_report, "Report should include total books")
            self.assertIn('valid_isbns', isbn_report, "Report should include valid ISBNs")
            self.assertIn('invalid_isbns', isbn_report, "Report should include invalid ISBNs")
            self.assertIn('duplicate_isbns', isbn_report, "Report should include duplicates")
        
        print("✅ ISBN tracking workflow tests passed")
    
    def test_special_order_workflow(self):
        """Test special order management workflow"""
        print("\n=== Testing Special Order Workflow ===")
        
        with self.app.test_client() as client:
            # Login as librarian
            login_data = {
                'username': 'books_librarian',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            librarian_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {librarian_token}'}
            
            # Step 1: Customer requests special order
            special_order_data = {
                'customer_name': 'Special Order Customer',
                'customer_email': 'special@example.com',
                'customer_phone': '+1234567890',
                'book_title': 'Rare Programming Book',
                'author_name': 'Famous Programmer',
                'isbn': '978-9-876-54321-2',
                'publisher': 'Tech Publishing House',
                'special_requests': 'Signed copy with dedication',
                'quantity': 1,
                'expected_price': '1299.00',
                'expected_delivery_date': (datetime.utcnow() + timedelta(days=14)).isoformat(),
                'deposit_amount': '299.00',
                'order_date': datetime.utcnow().isoformat(),
                'status': 'ordered'
            }
            
            response = client.post('/api/books/special-orders',
                                 data=json.dumps(special_order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Special order should be created")
            special_order_id = json.loads(response.data)['id']
            
            # Step 2: Process deposit
            deposit_data = {
                'special_order_id': special_order_id,
                'payment_method': 'credit_card',
                'amount': '299.00',
                'card_last_four': '3456',
                'payment_type': 'deposit'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(deposit_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Deposit should be processed")
            deposit_id = json.loads(response.data)['id']
            
            # Step 3: Update special order status
            status_data = {'status': 'ordered_from_publisher'}
            response = client.put(f'/api/books/special-orders/{special_order_id}',
                                data=json.dumps(status_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Status should update to ordered from publisher")
            
            # Step 4: Book received from publisher
            receive_data = {
                'status': 'received',
                'received_date': datetime.utcnow().isoformat(),
                'actual_price': '1199.00',  # Lower than expected
                'condition': 'new',
                'notes': 'Book received in good condition'
            }
            
            response = client.put(f'/api/books/special-orders/{special_order_id}',
                                data=json.dumps(receive_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should update as received")
            
            # Step 5: Notify customer
            notification_data = {
                'special_order_id': special_order_id,
                'notification_type': 'ready_for_pickup',
                'message': 'Your special order is ready for pickup',
                'sent_date': datetime.utcnow().isoformat(),
                'sent_via': 'email'
            }
            
            response = client.post('/api/books/special-orders/notify',
                                 data=json.dumps(notification_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Notification should be sent")
            
            # Step 6: Customer picks up order
            pickup_data = {
                'status': 'completed',
                'pickup_date': datetime.utcnow().isoformat(),
                'picked_up_by': 'Special Order Customer',
                'final_payment_method': 'cash',
                'final_amount': '900.00',  # Remaining balance
                'notes': 'Customer satisfied with order'
            }
            
            response = client.put(f'/api/books/special-orders/{special_order_id}',
                                data=json.dumps(pickup_data),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Order should be completed")
            
            # Step 7: Process final payment
            final_payment_data = {
                'special_order_id': special_order_id,
                'payment_method': 'cash',
                'amount': '900.00',
                'payment_type': 'final_payment'
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(final_payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Final payment should be processed")
            
            # Step 8: Check special order history
            response = client.get('/api/books/special-orders/history',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get special order history")
            order_history = json.loads(response.data)
            self.assertGreater(len(order_history), 0, "Should have order history")
            
            # Find our order in history
            our_order = next((o for o in order_history if o['id'] == special_order_id), None)
            self.assertIsNotNone(our_order, "Should find our order in history")
            self.assertEqual(our_order['status'], 'completed', "Order should be completed")
        
        print("✅ Special order workflow tests passed")
    
    def test_author_publisher_workflow(self):
        """Test author and publisher management workflow"""
        print("\n=== Testing Author Publisher Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'books_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Add new author
            author_data = {
                'name': 'New Famous Author',
                'description': 'Bestselling author with multiple awards',
                'specialty': 'Mystery Fiction',
                'biography': 'Born in 1980, started writing in 2005',
                'awards': ['Best Novel 2020', 'Reader Choice 2021'],
                'website': 'https://newauthor.com',
                'email': 'contact@newauthor.com'
            }
            
            response = client.post('/api/books/authors',
                                 data=json.dumps(author_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "New author should be created")
            new_author_id = json.loads(response.data)['id']
            
            # Step 2: Add new publisher
            publisher_data = {
                'name': 'New Publishing House',
                'description': 'Independent publisher focused on quality literature',
                'focus': 'Literary Fiction',
                'founded_year': 2010,
                'address': '123 Publishing St, Book City',
                'website': 'https://newpublisher.com',
                'email': 'info@newpublisher.com',
                'phone': '+1234567890'
            }
            
            response = client.post('/api/books/publishers',
                                 data=json.dumps(publisher_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "New publisher should be created")
            new_publisher_id = json.loads(response.data)['id']
            
            # Step 3: Create book with new author and publisher
            book_data = {
                'isbn': '978-7-888-99999-9',
                'title': 'Book by New Author',
                'author_id': new_author_id,
                'publisher_id': new_publisher_id,
                'category_id': self.categories[0].id,
                'price': '799.00',
                'pages': 350,
                'publication_year': 2023,
                'language': 'English',
                'genre': 'Mystery'
            }
            
            response = client.post('/api/books/products',
                                 data=json.dumps(book_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Book should be created")
            new_book_id = json.loads(response.data)['id']
            
            # Step 4: Update author statistics
            author_stats = {
                'total_books': 1,
                'total_sales': 0,
                'average_rating': 0.0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/books/authors/{new_author_id}/stats',
                                data=json.dumps(author_stats),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Author stats should update")
            
            # Step 5: Update publisher statistics
            publisher_stats = {
                'total_books': 1,
                'total_authors': 1,
                'total_sales': 0,
                'revenue': 0.0,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/books/publishers/{new_publisher_id}/stats',
                                data=json.dumps(publisher_stats),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Publisher stats should update")
            
            # Step 6: Generate author report
            response = client.get('/api/books/authors/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate author report")
            author_report = json.loads(response.data)
            
            self.assertIn('total_authors', author_report, "Report should include total authors")
            self.assertIn('top_authors', author_report, "Report should include top authors")
            self.assertIn('new_authors', author_report, "Report should include new authors")
            
            # Step 7: Generate publisher report
            response = client.get('/api/books/publishers/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate publisher report")
            publisher_report = json.loads(response.data)
            
            self.assertIn('total_publishers', publisher_report, "Report should include total publishers")
            self.assertIn('top_publishers', publisher_report, "Report should include top publishers")
            self.assertIn('new_releases', publisher_report, "Report should include new releases")
            
            # Step 8: Check author-publisher relationships
            response = client.get(f'/api/books/products/{new_book_id}/details',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get book details")
            book_details = json.loads(response.data)
            
            self.assertEqual(book_details['author']['id'], new_author_id, "Should link to correct author")
            self.assertEqual(book_details['publisher']['id'], new_publisher_id, "Should link to correct publisher")
        
        print("✅ Author publisher workflow tests passed")


class TestGroceryScenarios(unittest.TestCase):
    """Test grocery-specific scenarios and workflows"""
    
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
        """Create test data for grocery scenarios"""
        # Create grocery tenant
        cls.tenant = Tenant(
            name='Grocery Scenario Test',
            subdomain='grocery-scenario',
            database_name='grocery_scenario_db',
            retail_type='grocery',
            status='active'
        )
        db.session.add(cls.tenant)
        
        # Create grocery staff
        cls.manager = User(
            username='grocery_manager',
            email='manager@grocery.com',
            password_hash='hashed_password',
            'role': 'manager',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        cls.cashier = User(
            username='grocery_cashier',
            email='cashier@grocery.com',
            password_hash='hashed_password',
            'role': 'staff',
            tenant_id=str(cls.tenant.id),
            is_active=True
        )
        
        db.session.add(cls.manager)
        db.session.add(cls.cashier)
        
        # Enable grocery features
        feature_manager.enable_feature('FEATURE_WEIGHING_SCALE', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_EXPIRY_TRACKING', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_BATCH_TRACKING', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_PRICE_BY_WEIGHT', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_COMBO_OFFERS', str(cls.tenant.id))
        feature_manager.enable_feature('FEATURE_FRESH_PRODUCE', str(cls.tenant.id))
        
        # Create fresh produce items
        cls.produce_items = []
        produce_data = [
            ('Apples', 'Fresh red apples', 'Fruits', 'kg', Decimal('89.99'), 'A', 7),
            ('Bananas', 'Ripe yellow bananas', 'Fruits', 'kg', Decimal('59.99'), 'B', 5),
            ('Tomatoes', 'Fresh vine tomatoes', 'Vegetables', 'kg', Decimal('79.99'), 'A', 4),
            ('Potatoes', 'White potatoes', 'Vegetables', 'kg', Decimal('39.99'), 'B', 10),
            ('Carrots', 'Orange carrots', 'Vegetables', 'kg', Decimal('49.99'), 'A', 6),
            ('Lettuce', 'Fresh green lettuce', 'Vegetables', 'kg', Decimal('29.99'), 'A', 3),
            ('Oranges', 'Fresh oranges', 'Fruits', 'kg', Decimal('69.99'), 'B', 8),
            ('Onions', 'Yellow onions', 'Vegetables', 'kg', Decimal('35.99'), 'B', 12)
        ]
        
        for name, description, category, unit, price_per_unit, grade, shelf_life in produce_data:
            produce = FreshProduce(
                name=name,
                description=description,
                category=category,
                unit=unit,
                price_per_unit=price_per_unit,
                grade=grade,
                shelf_life_days=shelf_life,
                tenant_id=str(cls.tenant.id),
                status='active'
            )
            cls.produce_items.append(produce)
            db.session.add(produce)
        
        db.session.commit()
        
        # Create inventory records
        cls.inventory_records = []
        for produce in cls.produce_items:
            inventory = FreshProduceInventory(
                produce_id=produce.id,
                current_stock=Decimal('100.5'),
                unit=produce.unit,
                batch_number=f'BATCH{produce.id:03d}',
                expiry_date=datetime.utcnow() + timedelta(days=produce.shelf_life_days),
                received_date=datetime.utcnow() - timedelta(days=1),
                supplier=f'{produce.category} Supplier Inc',
                quality_grade=produce.grade,
                temperature_zone='cool',
                storage_location=f'Section {chr(65 + (produce.id % 4))}',
                tenant_id=str(cls.tenant.id)
            )
            cls.inventory_records.append(inventory)
            db.session.add(inventory)
        
        # Create weighing scale integration
        cls.weighing_scales = []
        scale_data = [
            ('SCALE001', 'Main Produce Scale', 'WS-2000', 'Produce Section'),
            ('SCALE002', 'Bulk Items Scale', 'WS-3000', 'Bulk Section'),
            ('SCALE003', 'Delicatessen Scale', 'WS-1500', 'Deli Section')
        ]
        
        for scale_id, name, model, location in scale_data:
            scale = WeighingScaleIntegration(
                scale_id=scale_id,
                scale_name=name,
                model=model,
                location=location,
                calibration_date=datetime.utcnow() - timedelta(days=7),
                next_calibration_date=datetime.utcnow() + timedelta(days=30),
                status='active',
                tenant_id=str(cls.tenant.id)
            )
            cls.weighing_scales.append(scale)
            db.session.add(scale)
        
        db.session.commit()
    
    def test_weighing_scale_workflow(self):
        """Test weighing scale integration workflow"""
        print("\n=== Testing Weighing Scale Workflow ===")
        
        with self.app.test_client() as client:
            # Login as cashier
            login_data = {
                'username': 'grocery_cashier',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            cashier_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {cashier_token}'}
            
            # Step 1: Check scale status
            response = client.get('/api/grocery/scales/status',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get scale status")
            scale_status = json.loads(response.data)
            
            self.assertEqual(len(scale_status), 3, "Should have 3 scales")
            for scale in scale_status:
                self.assertEqual(scale['status'], 'active', "All scales should be active")
            
            # Step 2: Simulate weighing produce
            weighing_data = {
                'scale_id': 'SCALE001',
                'produce_id': self.produce_items[0].id,  # Apples
                'measured_weight': Decimal('1.234'),
                'unit': 'kg',
                'measurement_time': datetime.utcnow().isoformat(),
                'operator_id': self.cashier.id,
                'tare_weight': Decimal('0.100'),
                'net_weight': Decimal('1.134')
            }
            
            response = client.post('/api/grocery/scales/weigh',
                                 data=json.dumps(weighing_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Weighing should be recorded")
            weighing_result = json.loads(response.data)
            
            # Calculate expected price
            expected_price = weighing_data['net_weight'] * self.produce_items[0].price_per_unit
            self.assertEqual(Decimal(str(weighing_result['calculated_price'])), expected_price, "Price should be calculated correctly")
            
            # Step 3: Create order with weighed item
            order_data = {
                'customer_name': 'Weighing Customer',
                'order_type': 'Sale',
                'items': [
                    {
                        'produce_id': self.produce_items[0].id,
                        'measured_weight': str(weighing_data['net_weight']),
                        'unit': 'kg',
                        'price_per_unit': str(self.produce_items[0].price_per_unit),
                        'total_price': str(weighing_result['calculated_price'])
                    }
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order with weighed item should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 4: Process payment
            payment_data = {
                'order_id': order_id,
                'payment_method': 'cash',
                'amount': str(weighing_result['calculated_price'])
            }
            
            response = client.post('/api/payments',
                                 data=json.dumps(payment_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Payment should be processed")
            
            # Step 5: Update inventory
            inventory_update = {
                'produce_id': self.produce_items[0].id,
                'weight_change': -weighing_data['net_weight'],
                'reason': 'Sale',
                'order_id': order_id,
                'updated_by': self.cashier.id
            }
            
            response = client.post('/api/grocery/inventory/update',
                                 data=json.dumps(inventory_update),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Inventory should be updated")
            
            # Step 6: Verify scale calibration
            calibration_data = {
                'scale_id': 'SCALE001',
                'calibration_date': datetime.utcnow().isoformat(),
                'calibrated_by': 'scale_technician',
                'calibration_results': 'passed',
                'next_calibration_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'notes': 'Scale calibrated successfully'
            }
            
            response = client.post('/api/grocery/scales/calibrate',
                                 data=json.dumps(calibration_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Scale calibration should be recorded")
            
            # Step 7: Generate weighing report
            response = client.get('/api/grocery/scales/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate weighing report")
            weighing_report = json.loads(response.data)
            
            self.assertIn('total_weighings', weighing_report, "Report should include total weighings")
            self.assertIn('scale_utilization', weighing_report, "Report should include scale utilization")
            self.assertIn('weight_discrepancies', weighing_report, "Report should include discrepancies")
        
        print("✅ Weighing scale workflow tests passed")
    
    def test_expiry_tracking_workflow(self):
        """Test expiry tracking and management workflow"""
        print("\n=== Testing Expiry Tracking Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'grocery_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Check current expiry status
            response = client.get('/api/grocery/expiry/status',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get expiry status")
            expiry_status = json.loads(response.data)
            
            self.assertIn('total_items', expiry_status, "Should include total items")
            self.assertIn('expiring_soon', expiry_status, "Should include items expiring soon")
            self.assertIn('expired', expiry_status, "Should include expired items")
            
            # Step 2: Create items with different expiry dates
            # Item expiring in 2 days
            expiring_soon = FreshProduceInventory(
                produce_id=self.produce_items[1].id,
                current_stock=Decimal('50.0'),
                unit='kg',
                batch_number='EXPIRE001',
                expiry_date=datetime.utcnow() + timedelta(days=2),
                received_date=datetime.utcnow(),
                supplier='Test Supplier',
                quality_grade='A',
                tenant_id=str(cls.tenant.id)
            )
            db.session.add(expiring_soon)
            
            # Item already expired
            expired_item = FreshProduceInventory(
                produce_id=self.produce_items[2].id,
                current_stock=Decimal('25.0'),
                unit='kg',
                batch_number='EXPIRE002',
                expiry_date=datetime.utcnow() - timedelta(days=1),
                received_date=datetime.utcnow() - timedelta(days=5),
                supplier='Test Supplier',
                quality_grade='B',
                tenant_id=str(cls.tenant.id)
            )
            db.session.add(expired_item)
            
            db.session.commit()
            
            # Step 3: Check expiry alerts
            response = client.get('/api/grocery/expiry/alerts',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should get expiry alerts")
            expiry_alerts = json.loads(response.data)
            
            self.assertGreater(len(expiry_alerts), 0, "Should have expiry alerts")
            
            # Check for specific alert types
            expiring_soon_alerts = [a for a in expiry_alerts if a['alert_type'] == 'expiring_soon']
            expired_alerts = [a for a in expiry_alerts if a['alert_type'] == 'expired']
            
            self.assertGreater(len(expiring_soon_alerts), 0, "Should have expiring soon alerts")
            self.assertGreater(len(expired_alerts), 0, "Should have expired alerts")
            
            # Step 4: Process expired items
            process_expired_data = {
                'inventory_id': expired_item.id,
                'action': 'dispose',
                'disposal_reason': 'Expired',
                'disposal_method': 'waste',
                'quantity_disposed': Decimal('25.0'),
                'processed_by': self.manager.id,
                'processed_date': datetime.utcnow().isoformat(),
                'notes': 'Item expired, disposed according to policy'
            }
            
            response = client.post('/api/grocery/expiry/process',
                                 data=json.dumps(process_expired_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 200, "Expired item should be processed")
            
            # Step 5: Create discount for expiring items
            discount_data = {
                'inventory_id': expiring_soon.id,
                'discount_type': 'percentage',
                'discount_value': '30',
                'discount_reason': 'Expiring soon',
                'start_date': datetime.utcnow().isoformat(),
                'end_date': (datetime.utcnow() + timedelta(days=2)).isoformat(),
                'created_by': self.manager.id
            }
            
            response = client.post('/api/grocery/expiry/discount',
                                 data=json.dumps(discount_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Discount should be created for expiring item")
            
            # Step 6: Update expired item status
            status_update = {
                'status': 'disposed',
                'current_stock': Decimal('0.0')
            }
            
            response = client.put(f'/api/grocery/inventory/{expired_item.id}',
                                data=json.dumps(status_update),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Expired item status should be updated")
            
            # Step 7: Generate expiry report
            response = client.get('/api/grocery/expiry/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate expiry report")
            expiry_report = json.loads(response.data)
            
            self.assertIn('total_expired', expiry_report, "Report should include total expired")
            self.assertIn('total_waste', expiry_report, "Report should include total waste")
            self.assertIn('waste_value', expiry_report, "Report should include waste value")
            self.assertIn('expiry_trends', expiry_report, "Report should include expiry trends")
        
        print("✅ Expiry tracking workflow tests passed")
    
    def test_batch_tracking_workflow(self):
        """Test batch tracking and traceability workflow"""
        print("\n=== Testing Batch Tracking Workflow ===")
        
        with self.app.test_client() as client:
            # Login as manager
            login_data = {
                'username': 'grocery_manager',
                'password': 'test_password',
                'tenant_id': str(self.tenant.id)
            }
            
            response = client.post('/api/auth/login',
                                 data=json.dumps(login_data),
                                 content_type='application/json')
            
            manager_token = json.loads(response.data)['access_token']
            headers = {'Authorization': f'Bearer {manager_token}'}
            
            # Step 1: Create new batch
            batch_data = {
                'produce_id': self.produce_items[0].id,
                'batch_number': 'BATCH2024001',
                'current_stock': Decimal('200.0'),
                'unit': 'kg',
                'supplier': 'Fresh Farm Supplier',
                'supplier_invoice': 'INV2024001',
                'received_date': datetime.utcnow().isoformat(),
                'expiry_date': (datetime.utcnow() + timedelta(days=7)).isoformat(),
                'quality_grade': 'A',
                'temperature_zone': 'cool',
                'storage_location': 'Section A',
                'certifications': ['organic', 'gap'],
                'notes': 'Premium quality batch'
            }
            
            response = client.post('/api/grocery/batches',
                                 data=json.dumps(batch_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "New batch should be created")
            batch_id = json.loads(response.data)['id']
            
            # Step 2: Track batch movements
            movement_data = {
                'batch_id': batch_id,
                'movement_type': 'received',
                'quantity': Decimal('200.0'),
                'movement_date': datetime.utcnow().isoformat(),
                'reference': 'PO2024001',
                'moved_by': self.manager.id,
                'from_location': 'Supplier',
                'to_location': 'Section A',
                'notes': 'Received from supplier'
            }
            
            response = client.post('/api/grocery/batches/movement',
                                 data=json.dumps(movement_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Batch movement should be tracked")
            
            # Step 3: Create sale from batch
            order_data = {
                'customer_name': 'Batch Customer',
                'order_type': 'Sale',
                'items': [
                    {
                        'produce_id': self.produce_items[0].id,
                        'batch_number': 'BATCH2024001',
                        'quantity': Decimal('5.5'),
                        'unit': 'kg',
                        'price_per_unit': str(self.produce_items[0].price_per_unit)
                    }
                ]
            }
            
            response = client.post('/api/orders',
                                 data=json.dumps(order_data),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Order from batch should be created")
            order_id = json.loads(response.data)['id']
            
            # Step 4: Track batch sale movement
            sale_movement = {
                'batch_id': batch_id,
                'movement_type': 'sold',
                'quantity': Decimal('5.5'),
                'movement_date': datetime.utcnow().isoformat(),
                'reference': f'ORDER{order_id}',
                'moved_by': self.cashier.id,
                'from_location': 'Section A',
                'to_location': 'Customer',
                'notes': 'Sold to customer'
            }
            
            response = client.post('/api/grocery/batches/movement',
                                 data=json.dumps(sale_movement),
                                 content_type='application/json',
                                 headers=headers)
            
            self.assertEqual(response.status_code, 201, "Sale movement should be tracked")
            
            # Step 5: Update batch stock
            stock_update = {
                'current_stock': Decimal('194.5'),  # 200 - 5.5
                'last_updated': datetime.utcnow().isoformat()
            }
            
            response = client.put(f'/api/grocery/batches/{batch_id}',
                                data=json.dumps(stock_update),
                                content_type='application/json',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Batch stock should be updated")
            
            # Step 6: Trace batch history
            response = client.get(f'/api/grocery/batches/{batch_id}/trace',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should trace batch history")
            batch_trace = json.loads(response.data)
            
            self.assertIn('batch_info', batch_trace, "Should include batch info")
            self.assertIn('movements', batch_trace, "Should include movements")
            self.assertIn('current_stock', batch_trace, "Should include current stock")
            
            # Verify movements
            movements = batch_trace['movements']
            self.assertEqual(len(movements), 2, "Should have 2 movements")
            
            # Step 7: Generate batch report
            response = client.get('/api/grocery/batches/report',
                                headers=headers)
            
            self.assertEqual(response.status_code, 200, "Should generate batch report")
            batch_report = json.loads(response.data)
            
            self.assertIn('total_batches', batch_report, "Report should include total batches")
            self.assertIn('active_batches', batch_report, "Report should include active batches")
            self.assertIn('batch_movements', batch_report, "Report should include movements")
            self.assertIn('stock_by_batch', batch_report, "Report should include stock by batch")
        
        print("✅ Batch tracking workflow tests passed")


def run_retail_specific_tests():
    """Run all retail-type specific tests"""
    print("=" * 80)
    print("RETAIL-TYPE SPECIFIC TEST SCENARIOS")
    print("=" * 80)
    print("Testing specific workflows and business logic for each retail type\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestRestaurantScenarios,
        TestApparelScenarios,
        TestBooksScenarios,
        TestGroceryScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("RETAIL-TYPE SPECIFIC TEST RESULTS")
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
    success = run_retail_specific_tests()
    
    if success:
        print("\n✅ ALL RETAIL-TYPE SPECIFIC TESTS PASSED!")
        print("All retail-type specific workflows are working correctly")
        exit(0)
    else:
        print("\n❌ SOME RETAIL-TYPE SPECIFIC TESTS FAILED!")
        print("Review and fix retail-type specific issues")
        exit(1)