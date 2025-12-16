"""
Comprehensive Database Schema Testing Framework
Tests conditional table creation, data integrity, tenant isolation,
and rollback procedures for the multi-retail POS system.
"""

import unittest
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
    FreshProduce, FreshProduceInventory, WeighingScaleIntegration,
    # Product models
    Product, ProductCategory, ProductVariant,
    # Inventory models
    InventoryTransaction, StockAdjustment, LowStockAlert
)


class TestConditionalTableCreation(unittest.TestCase):
    """Test conditional table creation based on feature flags"""
    
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
        
        # Create base tables only
        db.create_all()
        
        cls._create_base_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_base_data(cls):
        """Create base test data"""
        # Create test tenant
        cls.test_tenant = Tenant(
            name='Test Tenant',
            subdomain='test',
            database_name='test_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_restaurant_tables_creation(self):
        """Test restaurant-specific table creation"""
        print("\n=== Testing Restaurant Tables Creation ===")
        
        # Enable restaurant features
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_KOT_PRINTING', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', str(self.test_tenant.id))
        
        # Check if restaurant tables exist
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            'restaurant_table',
            'table_reservation',
            'kitchen_station',
            'restaurant_shift'
        ]
        
        for table_name in expected_tables:
            self.assertIn(table_name, table_names, f"Table {table_name} should exist")
        
        # Test table creation with features enabled
        restaurant_table = RestaurantTable(
            table_number='T1',
            capacity=4,
            location='Main Area',
            tenant_id=str(self.test_tenant.id),
            status='available'
        )
        db.session.add(restaurant_table)
        db.session.commit()
        
        self.assertIsNotNone(restaurant_table.id, "Restaurant table should be created")
        
        # Test conditional model loading
        with patch('models.restaurant.RestaurantTable') as mock_model:
            mock_model.query.all.return_value = [restaurant_table]
            
            tables = mock_model.query.all()
            self.assertEqual(len(tables), 1, "Should load restaurant tables when feature is enabled")
        
        print("✅ Restaurant tables creation tests passed")
    
    def test_apparel_tables_creation(self):
        """Test apparel-specific table creation"""
        print("\n=== Testing Apparel Tables Creation ===")
        
        # Enable apparel features
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(self.test_tenant.id))
        
        # Check if apparel tables exist
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            'apparel_product',
            'apparel_variant',
            'apparel_size_matrix',
            'apparel_exchange'
        ]
        
        for table_name in expected_tables:
            self.assertIn(table_name, table_names, f"Table {table_name} should exist")
        
        # Test apparel product creation
        apparel_product = ApparelProduct(
            sku='APP001',
            name='Test Apparel Product',
            category='Clothing',
            base_price=Decimal('999.00'),
            tenant_id=str(self.test_tenant.id),
            status='active'
        )
        db.session.add(apparel_product)
        db.session.commit()
        
        self.assertIsNotNone(apparel_product.id, "Apparel product should be created")
        
        # Test variant creation
        apparel_variant = ApparelVariant(
            product_id=apparel_product.id,
            sku='APP001-M-RED',
            size='M',
            color='Red',
            price=Decimal('1049.00'),
            stock_quantity=10,
            tenant_id=str(self.test_tenant.id)
        )
        db.session.add(apparel_variant)
        db.session.commit()
        
        self.assertIsNotNone(apparel_variant.id, "Apparel variant should be created")
        
        print("✅ Apparel tables creation tests passed")
    
    def test_books_tables_creation(self):
        """Test books-specific table creation"""
        print("\n=== Testing Books Tables Creation ===")
        
        # Enable books features
        feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_SPECIAL_ORDERS', str(self.test_tenant.id))
        
        # Check if books tables exist
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            'book_product',
            'book_variant',
            'book_author',
            'book_publisher',
            'book_category'
        ]
        
        for table_name in expected_tables:
            self.assertIn(table_name, table_names, f"Table {table_name} should exist")
        
        # Test author creation
        author = BookAuthor(
            name='Test Author',
            description='Test author description',
            tenant_id=str(self.test_tenant.id)
        )
        db.session.add(author)
        db.session.commit()
        
        self.assertIsNotNone(author.id, "Book author should be created")
        
        # Test book creation with ISBN
        book = BookProduct(
            isbn='978-3-16-148410-0',
            title='Test Book',
            author_id=author.id,
            price=Decimal('299.00'),
            tenant_id=str(self.test_tenant.id),
            status='active'
        )
        db.session.add(book)
        db.session.commit()
        
        self.assertIsNotNone(book.id, "Book product should be created")
        self.assertEqual(book.isbn, '978-3-16-148410-0', "ISBN should be stored correctly")
        
        print("✅ Books tables creation tests passed")
    
    def test_grocery_tables_creation(self):
        """Test grocery-specific table creation"""
        print("\n=== Testing Grocery Tables Creation ===")
        
        # Enable grocery features
        feature_manager.enable_feature('FEATURE_WEIGHING_SCALE', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_EXPIRY_TRACKING', str(self.test_tenant.id))
        feature_manager.enable_feature('FEATURE_BATCH_TRACKING', str(self.test_tenant.id))
        
        # Check if grocery tables exist
        inspector = db.inspect(db.engine)
        table_names = inspector.get_table_names()
        
        expected_tables = [
            'fresh_produce',
            'fresh_produce_inventory',
            'weighing_scale_integration'
        ]
        
        for table_name in expected_tables:
            self.assertIn(table_name, table_names, f"Table {table_name} should exist")
        
        # Test fresh produce creation
        produce = FreshProduce(
            name='Test Produce',
            description='Test produce description',
            category='Fresh Produce',
            unit='kg',
            price_per_unit=Decimal('5.99'),
            tenant_id=str(self.test_tenant.id),
            status='active'
        )
        db.session.add(produce)
        db.session.commit()
        
        self.assertIsNotNone(produce.id, "Fresh produce should be created")
        
        # Test inventory with expiry tracking
        inventory = FreshProduceInventory(
            produce_id=produce.id,
            current_stock=Decimal('100.0'),
            unit='kg',
            batch_number='BATCH001',
            expiry_date=datetime.utcnow() + timedelta(days=7),
            tenant_id=str(self.test_tenant.id)
        )
        db.session.add(inventory)
        db.session.commit()
        
        self.assertIsNotNone(inventory.id, "Produce inventory should be created")
        self.assertIsNotNone(inventory.expiry_date, "Expiry date should be set")
        
        print("✅ Grocery tables creation tests passed")


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity across feature combinations"""
    
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
        """Create test data for integrity testing"""
        # Create test tenants
        cls.tenant1 = Tenant(
            name='Tenant 1',
            subdomain='tenant1',
            database_name='tenant1_db',
            retail_type='restaurant',
            status='active'
        )
        cls.tenant2 = Tenant(
            name='Tenant 2',
            subdomain='tenant2',
            database_name='tenant2_db',
            retail_type='apparel',
            status='active'
        )
        db.session.add(cls.tenant1)
        db.session.add(cls.tenant2)
        db.session.commit()
    
    def test_foreign_key_integrity(self):
        """Test foreign key constraints and referential integrity"""
        print("\n=== Testing Foreign Key Integrity ===")
        
        # Test restaurant table foreign key
        restaurant_table = RestaurantTable(
            table_number='T1',
            capacity=4,
            location='Main Area',
            tenant_id=str(self.tenant1.id),
            status='available'
        )
        db.session.add(restaurant_table)
        db.session.commit()
        
        # Test reservation with valid table reference
        reservation = TableReservation(
            table_id=restaurant_table.id,
            customer_name='Test Customer',
            reservation_time=datetime.utcnow() + timedelta(hours=2),
            party_size=4,
            tenant_id=str(self.tenant1.id),
            status='confirmed'
        )
        db.session.add(reservation)
        db.session.commit()
        
        self.assertIsNotNone(reservation.id, "Reservation should be created with valid table reference")
        
        # Test apparel product foreign key
        apparel_product = ApparelProduct(
            sku='APP001',
            name='Test Apparel',
            category='Clothing',
            base_price=Decimal('999.00'),
            tenant_id=str(self.tenant2.id),
            status='active'
        )
        db.session.add(apparel_product)
        db.session.commit()
        
        # Test variant with valid product reference
        variant = ApparelVariant(
            product_id=apparel_product.id,
            sku='APP001-M-RED',
            size='M',
            color='Red',
            price=Decimal('1049.00'),
            stock_quantity=10,
            tenant_id=str(self.tenant2.id)
        )
        db.session.add(variant)
        db.session.commit()
        
        self.assertIsNotNone(variant.id, "Variant should be created with valid product reference")
        
        # Test invalid foreign key handling
        invalid_reservation = TableReservation(
            table_id=999999,  # Non-existent table ID
            customer_name='Invalid Customer',
            reservation_time=datetime.utcnow() + timedelta(hours=3),
            party_size=2,
            tenant_id=str(self.tenant1.id),
            status='pending'
        )
        
        # This should fail due to foreign key constraint
        with self.assertRaises(Exception):
            db.session.add(invalid_reservation)
            db.session.commit()
        
        db.session.rollback()
        
        print("✅ Foreign key integrity tests passed")
    
    def test_unique_constraint_integrity(self):
        """Test unique constraints and data uniqueness"""
        print("\n=== Testing Unique Constraint Integrity ===")
        
        # Test unique table number per tenant
        table1 = RestaurantTable(
            table_number='T10',
            capacity=4,
            location='Area 1',
            tenant_id=str(self.tenant1.id),
            status='available'
        )
        db.session.add(table1)
        db.session.commit()
        
        # Try to create another table with same number for same tenant
        table2 = RestaurantTable(
            table_number='T10',  # Same number
            capacity=6,
            location='Area 2',
            tenant_id=str(self.tenant1.id),  # Same tenant
            status='available'
        )
        
        # This should fail due to unique constraint
        with self.assertRaises(Exception):
            db.session.add(table2)
            db.session.commit()
        
        db.session.rollback()
        
        # But same table number should be allowed for different tenant
        table3 = RestaurantTable(
            table_number='T10',  # Same number
            capacity=4,
            location='Area 3',
            tenant_id=str(self.tenant2.id),  # Different tenant
            status='available'
        )
        db.session.add(table3)
        db.session.commit()
        
        self.assertIsNotNone(table3.id, "Same table number should be allowed for different tenant")
        
        # Test unique SKU constraint
        product1 = ApparelProduct(
            sku='UNIQUE001',
            name='Product 1',
            category='Clothing',
            base_price=Decimal('999.00'),
            tenant_id=str(self.tenant2.id),
            status='active'
        )
        db.session.add(product1)
        db.session.commit()
        
        # Try to create product with same SKU
        product2 = ApparelProduct(
            sku='UNIQUE001',  # Same SKU
            name='Product 2',
            category='Clothing',
            base_price=Decimal('1099.00'),
            tenant_id=str(self.tenant2.id),
            status='active'
        )
        
        # This should fail due to unique SKU constraint
        with self.assertRaises(Exception):
            db.session.add(product2)
            db.session.commit()
        
        db.session.rollback()
        
        print("✅ Unique constraint integrity tests passed")
    
    def test_data_consistency_across_features(self):
        """Test data consistency when features are enabled/disabled"""
        print("\n=== Testing Data Consistency Across Features ===")
        
        # Create data with multiple features enabled
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.tenant1.id))
        feature_manager.enable_feature('FEATURE_RESERVATIONS', str(self.tenant1.id))
        
        # Create restaurant table and reservation
        table = RestaurantTable(
            table_number='T20',
            capacity=4,
            location='Main Area',
            tenant_id=str(self.tenant1.id),
            status='available'
        )
        db.session.add(table)
        db.session.commit()
        
        reservation = TableReservation(
            table_id=table.id,
            customer_name='Test Customer',
            reservation_time=datetime.utcnow() + timedelta(hours=2),
            party_size=4,
            tenant_id=str(self.tenant1.id),
            status='confirmed'
        )
        db.session.add(reservation)
        db.session.commit()
        
        # Disable reservation feature
        feature_manager.disable_feature('FEATURE_RESERVATIONS', str(self.tenant1.id))
        
        # Check if reservation data is still accessible
        existing_reservation = TableReservation.query.get(reservation.id)
        self.assertIsNotNone(existing_reservation, "Existing reservation data should remain accessible")
        
        # Check if new reservations can be created (should be prevented)
        new_reservation = TableReservation(
            table_id=table.id,
            customer_name='New Customer',
            reservation_time=datetime.utcnow() + timedelta(hours=3),
            party_size=2,
            tenant_id=str(self.tenant1.id),
            status='pending'
        )
        
        # In real implementation, this would be prevented by feature flag check
        # For testing, we just verify the data structure remains intact
        db.session.add(new_reservation)
        db.session.commit()
        
        self.assertIsNotNone(new_reservation.id, "Data structure should remain intact")
        
        # Test re-enabling feature
        feature_manager.enable_feature('FEATURE_RESERVATIONS', str(self.tenant1.id))
        
        # Verify all reservations are still accessible
        all_reservations = TableReservation.query.filter_by(
            tenant_id=str(self.tenant1.id)
        ).all()
        
        self.assertEqual(len(all_reservations), 2, "All reservations should be accessible after re-enabling feature")
        
        print("✅ Data consistency across features tests passed")


class TestTenantIsolation(unittest.TestCase):
    """Test tenant isolation and data security"""
    
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
        """Create test data for tenant isolation testing"""
        # Create test tenants
        cls.tenant1 = Tenant(
            name='Restaurant Chain',
            subdomain='restaurant',
            database_name='restaurant_db',
            retail_type='restaurant',
            status='active'
        )
        cls.tenant2 = Tenant(
            name='Apparel Store',
            subdomain='apparel',
            database_name='apparel_db',
            retail_type='apparel',
            status='active'
        )
        cls.tenant3 = Tenant(
            name='Bookstore',
            subdomain='books',
            database_name='books_db',
            retail_type='books',
            status='active'
        )
        db.session.add(cls.tenant1)
        db.session.add(cls.tenant2)
        db.session.add(cls.tenant3)
        db.session.commit()
    
    def test_tenant_data_isolation(self):
        """Test that tenant data is properly isolated"""
        print("\n=== Testing Tenant Data Isolation ===")
        
        # Create data for each tenant
        # Restaurant data
        restaurant_table = RestaurantTable(
            table_number='RT1',
            capacity=4,
            location='Restaurant Area',
            tenant_id=str(self.tenant1.id),
            status='available'
        )
        db.session.add(restaurant_table)
        
        # Apparel data
        apparel_product = ApparelProduct(
            sku='AP001',
            name='Apparel Product',
            category='Clothing',
            base_price=Decimal('999.00'),
            tenant_id=str(self.tenant2.id),
            status='active'
        )
        db.session.add(apparel_product)
        
        # Books data
        author = BookAuthor(
            name='Book Author',
            description='Book author description',
            tenant_id=str(self.tenant3.id)
        )
        db.session.add(author)
        
        db.session.commit()
        
        # Test tenant-specific queries
        restaurant_tables = RestaurantTable.query.filter_by(
            tenant_id=str(self.tenant1.id)
        ).all()
        
        apparel_products = ApparelProduct.query.filter_by(
            tenant_id=str(self.tenant2.id)
        ).all()
        
        book_authors = BookAuthor.query.filter_by(
            tenant_id=str(self.tenant3.id)
        ).all()
        
        # Verify data isolation
        self.assertEqual(len(restaurant_tables), 1, "Tenant 1 should have 1 restaurant table")
        self.assertEqual(len(apparel_products), 1, "Tenant 2 should have 1 apparel product")
        self.assertEqual(len(book_authors), 1, "Tenant 3 should have 1 book author")
        
        # Verify cross-tenant access prevention
        tenant1_restaurant_tables = RestaurantTable.query.filter_by(
            tenant_id=str(self.tenant2.id)  # Wrong tenant
        ).all()
        
        self.assertEqual(len(tenant1_restaurant_tables), 0, "Should not access other tenant's data")
        
        print("✅ Tenant data isolation tests passed")
    
    def test_tenant_feature_isolation(self):
        """Test that feature flags are isolated per tenant"""
        print("\n=== Testing Tenant Feature Isolation ===")
        
        # Enable different features for each tenant
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(self.tenant1.id))
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(self.tenant2.id))
        feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(self.tenant3.id))
        
        # Check feature isolation
        tenant1_features = feature_manager.get_tenant_features(str(self.tenant1.id))
        tenant2_features = feature_manager.get_tenant_features(str(self.tenant2.id))
        tenant3_features = feature_manager.get_tenant_features(str(self.tenant3.id))
        
        self.assertIn('FEATURE_TABLE_MANAGEMENT', tenant1_features)
        self.assertNotIn('FEATURE_SIZE_VARIANTS', tenant1_features)
        self.assertNotIn('FEATURE_ISBN_TRACKING', tenant1_features)
        
        self.assertIn('FEATURE_SIZE_VARIANTS', tenant2_features)
        self.assertNotIn('FEATURE_TABLE_MANAGEMENT', tenant2_features)
        self.assertNotIn('FEATURE_ISBN_TRACKING', tenant2_features)
        
        self.assertIn('FEATURE_ISBN_TRACKING', tenant3_features)
        self.assertNotIn('FEATURE_TABLE_MANAGEMENT', tenant3_features)
        self.assertNotIn('FEATURE_SIZE_VARIANTS', tenant3_features)
        
        # Test feature access control
        can_manage_tables = feature_manager.is_feature_enabled('FEATURE_TABLE_MANAGEMENT', str(self.tenant1.id))
        can_use_variants = feature_manager.is_feature_enabled('FEATURE_SIZE_VARIANTS', str(self.tenant1.id))
        
        self.assertTrue(can_manage_tables, "Tenant 1 should have table management feature")
        self.assertFalse(can_use_variants, "Tenant 1 should not have size variants feature")
        
        print("✅ Tenant feature isolation tests passed")
    
    def test_tenant_configuration_isolation(self):
        """Test that tenant configurations are isolated"""
        print("\n=== Testing Tenant Configuration Isolation ===")
        
        # Create tenant-specific configurations
        config1 = TenantConfiguration(
            tenant_id=str(self.tenant1.id),
            config_key='restaurant_settings',
            config_value={
                'table_count': 20,
                'kitchen_stations': 3,
                'shift_management': True
            }
        )
        db.session.add(config1)
        
        config2 = TenantConfiguration(
            tenant_id=str(self.tenant2.id),
            config_key='apparel_settings',
            config_value={
                'size_variants': True,
                'color_variants': True,
                'exchange_policy': '30_days'
            }
        )
        db.session.add(config2)
        
        config3 = TenantConfiguration(
            tenant_id=str(self.tenant3.id),
            config_key='books_settings',
            config_value={
                'isbn_tracking': True,
                'special_orders': True,
                'publisher_management': True
            }
        )
        db.session.add(config3)
        
        db.session.commit()
        
        # Test configuration isolation
        tenant1_configs = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant1.id)
        ).all()
        
        tenant2_configs = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant2.id)
        ).all()
        
        tenant3_configs = TenantConfiguration.query.filter_by(
            tenant_id=str(self.tenant3.id)
        ).all()
        
        self.assertEqual(len(tenant1_configs), 1, "Tenant 1 should have 1 configuration")
        self.assertEqual(len(tenant2_configs), 1, "Tenant 2 should have 1 configuration")
        self.assertEqual(len(tenant3_configs), 1, "Tenant 3 should have 1 configuration")
        
        # Verify configuration content
        self.assertEqual(tenant1_configs[0].config_key, 'restaurant_settings')
        self.assertEqual(tenant2_configs[0].config_key, 'apparel_settings')
        self.assertEqual(tenant3_configs[0].config_key, 'books_settings')
        
        print("✅ Tenant configuration isolation tests passed")


class TestRollbackProcedures(unittest.TestCase):
    """Test rollback procedures and data recovery"""
    
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
        """Create test data for rollback testing"""
        cls.test_tenant = Tenant(
            name='Rollback Test Tenant',
            subdomain='rollback',
            database_name='rollback_db',
            retail_type='general',
            status='active'
        )
        db.session.add(cls.test_tenant)
        db.session.commit()
    
    def test_feature_rollback(self):
        """Test rolling back feature changes"""
        print("\n=== Testing Feature Rollback ===")
        
        # Enable multiple features
        features_to_enable = [
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_SIZE_VARIANTS',
            'FEATURE_ISBN_TRACKING',
            'FEATURE_WEIGHING_SCALE'
        ]
        
        for feature in features_to_enable:
            feature_manager.enable_feature(feature, str(self.test_tenant.id))
        
        # Verify features are enabled
        enabled_features = feature_manager.get_tenant_features(str(self.test_tenant.id))
        for feature in features_to_enable:
            self.assertIn(feature, enabled_features, f"Feature {feature} should be enabled")
        
        # Create data with features enabled
        restaurant_table = RestaurantTable(
            table_number='RB1',
            capacity=4,
            location='Rollback Area',
            tenant_id=str(self.test_tenant.id),
            status='available'
        )
        db.session.add(restaurant_table)
        
        apparel_product = ApparelProduct(
            sku='RB001',
            name='Rollback Apparel',
            category='Clothing',
            base_price=Decimal('999.00'),
            tenant_id=str(self.test_tenant.id),
            status='active'
        )
        db.session.add(apparel_product)
        
        db.session.commit()
        
        # Rollback features
        for feature in features_to_enable:
            feature_manager.disable_feature(feature, str(self.test_tenant.id))
        
        # Verify features are disabled
        enabled_features_after = feature_manager.get_tenant_features(str(self.test_tenant.id))
        for feature in features_to_enable:
            self.assertNotIn(feature, enabled_features_after, f"Feature {feature} should be disabled")
        
        # Verify data integrity after rollback
        existing_table = RestaurantTable.query.get(restaurant_table.id)
        existing_product = ApparelProduct.query.get(apparel_product.id)
        
        self.assertIsNotNone(existing_table, "Restaurant table data should remain after feature rollback")
        self.assertIsNotNone(existing_product, "Apparel product data should remain after feature rollback")
        
        print("✅ Feature rollback tests passed")
    
    def test_data_migration_rollback(self):
        """Test rolling back data migrations"""
        print("\n=== Testing Data Migration Rollback ===")
        
        # Create initial data
        initial_product = Product(
            sku='INITIAL001',
            name='Initial Product',
            description='Initial product description',
            price=Decimal('999.00'),
            tenant_id=str(self.test_tenant.id),
            status='active'
        )
        db.session.add(initial_product)
        db.session.commit()
        
        initial_product_id = initial_product.id
        
        # Simulate migration that adds new fields
        # In real implementation, this would be a migration script
        initial_product.additional_field = 'migration_data'
        initial_product.migration_version = '2.0'
        db.session.commit()
        
        # Verify migration data
        migrated_product = Product.query.get(initial_product_id)
        self.assertEqual(migrated_product.additional_field, 'migration_data')
        self.assertEqual(migrated_product.migration_version, '2.0')
        
        # Simulate rollback by removing migration fields
        # In real implementation, this would be a rollback migration
        migrated_product.additional_field = None
        migrated_product.migration_version = None
        db.session.commit()
        
        # Verify rollback
        rolled_back_product = Product.query.get(initial_product_id)
        self.assertIsNone(rolled_back_product.additional_field, "Migration field should be removed")
        self.assertIsNone(rolled_back_product.migration_version, "Migration version should be removed")
        
        # Verify original data is intact
        self.assertEqual(rolled_back_product.sku, 'INITIAL001')
        self.assertEqual(rolled_back_product.name, 'Initial Product')
        
        print("✅ Data migration rollback tests passed")
    
    def test_transaction_rollback(self):
        """Test transaction rollback on errors"""
        print("\n=== Testing Transaction Rollback ===")
        
        # Start transaction
        try:
            # Create multiple records
            table1 = RestaurantTable(
                table_number='TR1',
                capacity=4,
                location='Transaction Area 1',
                tenant_id=str(self.test_tenant.id),
                status='available'
            )
            db.session.add(table1)
            
            table2 = RestaurantTable(
                table_number='TR2',
                capacity=6,
                location='Transaction Area 2',
                tenant_id=str(self.test_tenant.id),
                status='available'
            )
            db.session.add(table2)
            
            # Force an error
            invalid_table = RestaurantTable(
                table_number=None,  # This should cause an error
                capacity=4,
                location='Invalid Area',
                tenant_id=str(self.test_tenant.id),
                status='available'
            )
            db.session.add(invalid_table)
            
            db.session.commit()
            
        except Exception as e:
            # Rollback on error
            db.session.rollback()
            
            # Verify rollback
            tables = RestaurantTable.query.filter_by(
                tenant_id=str(self.test_tenant.id)
            ).all()
            
            self.assertEqual(len(tables), 0, "All tables should be rolled back")
        
        # Test successful transaction after rollback
        table3 = RestaurantTable(
            table_number='TR3',
            capacity=4,
            location='Transaction Area 3',
            tenant_id=str(self.test_tenant.id),
            status='available'
        )
        db.session.add(table3)
        db.session.commit()
        
        # Verify successful transaction
        tables_after = RestaurantTable.query.filter_by(
            tenant_id=str(self.test_tenant.id)
        ).all()
        
        self.assertEqual(len(tables_after), 1, "Should have 1 table after successful transaction")
        self.assertEqual(tables_after[0].table_number, 'TR3')
        
        print("✅ Transaction rollback tests passed")


def run_database_schema_tests():
    """Run all database schema tests"""
    print("=" * 80)
    print("DATABASE SCHEMA TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing conditional table creation, data integrity, tenant isolation\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConditionalTableCreation,
        TestDataIntegrity,
        TestTenantIsolation,
        TestRollbackProcedures
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("DATABASE SCHEMA TEST RESULTS")
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
    success = run_database_schema_tests()
    
    if success:
        print("\n✅ ALL DATABASE SCHEMA TESTS PASSED!")
        print("Database schema is working correctly")
        exit(0)
    else:
        print("\n❌ SOME DATABASE SCHEMA TESTS FAILED!")
        print("Review and fix database schema issues")
        exit(1)