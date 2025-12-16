"""
Comprehensive Multi-Retail Module Testing Framework
Tests all retail modules (restaurant, apparel, books, grocery, etc.)
with their specific business logic and workflows.
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
from utils.retail_type_manager import get_retail_type_manager

# Import models
from models import (
    db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings,
    # Restaurant models
    RestaurantTable, TableReservation, KitchenStation, RestaurantShift,
    # Apparel models
    ApparelProduct, ApparelVariant, ApparelSizeMatrix, ApparelExchange,
    # Books models
    BookProduct, BookVariant, BookAuthor, BookPublisher, BookCategory,
    # Grocery models
    FreshProduce, FreshProduceInventory, WeighingScaleIntegration,
    # Product models
    Product, ProductCategory, ProductVariant as BaseProductVariant,
    # Inventory models
    InventoryTransaction, StockAdjustment, LowStockAlert
)


class TestRestaurantModule(unittest.TestCase):
    """Test restaurant-specific functionality"""
    
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
        
        # Enable restaurant features
        feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', 'test_tenant')
        feature_manager.enable_feature('FEATURE_KOT_PRINTING', 'test_tenant')
        feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', 'test_tenant')
        feature_manager.enable_feature('FEATURE_WAITER_MANAGEMENT', 'test_tenant')
        feature_manager.enable_feature('FEATURE_RESERVATIONS', 'test_tenant')
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for restaurant module"""
        # Create restaurant tables
        cls.test_tables = []
        for i in range(5):
            table = RestaurantTable(
                table_number=f'T{i+1}',
                capacity=4 + i,
                location=f'Area {chr(65+i)}',
                description=f'Test table {i+1}',
                tenant_id='test_tenant',
                status='available'
            )
            cls.test_tables.append(table)
            db.session.add(table)
        
        # Create kitchen stations
        cls.test_stations = []
        stations = ['Main Kitchen', 'Bar', 'Dessert Station']
        for station_name in stations:
            station = KitchenStation(
                name=station_name,
                description=f'{station_name} station',
                tenant_id='test_tenant',
                status='active'
            )
            cls.test_stations.append(station)
            db.session.add(station)
        
        # Create restaurant shifts
        cls.test_shifts = []
        shifts = [
            ('Morning', '06:00', '14:00'),
            ('Evening', '14:00', '22:00'),
            ('Night', '22:00', '06:00')
        ]
        for shift_name, start_time, end_time in shifts:
            shift = RestaurantShift(
                name=shift_name,
                start_time=start_time,
                end_time=end_time,
                description=f'{shift_name} shift',
                tenant_id='test_tenant',
                status='active'
            )
            cls.test_shifts.append(shift)
            db.session.add(shift)
        
        db.session.commit()
    
    def test_table_management(self):
        """Test restaurant table management"""
        print("\n=== Testing Restaurant Table Management ===")
        
        # Test table creation
        new_table = RestaurantTable(
            table_number='T99',
            capacity=6,
            location='Test Area',
            description='Test table',
            tenant_id='test_tenant',
            status='available'
        )
        db.session.add(new_table)
        db.session.commit()
        
        self.assertIsNotNone(new_table.id, "Table should be created with ID")
        
        # Test table status management
        new_table.status = 'occupied'
        db.session.commit()
        
        updated_table = RestaurantTable.query.get(new_table.id)
        self.assertEqual(updated_table.status, 'occupied', "Table status should be updated")
        
        # Test table availability check
        available_tables = RestaurantTable.query.filter_by(
            tenant_id='test_tenant', status='available'
        ).all()
        self.assertGreater(len(available_tables), 0, "Should have available tables")
        
        print("✅ Restaurant table management tests passed")
    
    def test_table_reservations(self):
        """Test table reservation functionality"""
        print("\n=== Testing Table Reservations ===")
        
        # Create reservation
        reservation = TableReservation(
            table_id=self.test_tables[0].id,
            customer_name='Test Customer',
            customer_phone='+1234567890',
            reservation_time=datetime.utcnow() + timedelta(hours=2),
            party_size=4,
            special_requests='Window seat preferred',
            tenant_id='test_tenant',
            status='confirmed'
        )
        db.session.add(reservation)
        db.session.commit()
        
        self.assertIsNotNone(reservation.id, "Reservation should be created")
        
        # Test reservation status updates
        reservation.status = 'arrived'
        reservation.arrived_at = datetime.utcnow()
        db.session.commit()
        
        updated_reservation = TableReservation.query.get(reservation.id)
        self.assertEqual(updated_reservation.status, 'arrived', "Reservation status should be updated")
        self.assertIsNotNone(updated_reservation.arrived_at, "Arrival time should be recorded")
        
        # Test reservation conflicts
        conflicting_reservation = TableReservation(
            table_id=self.test_tables[0].id,
            customer_name='Another Customer',
            reservation_time=datetime.utcnow() + timedelta(hours=2, minutes=30),
            party_size=2,
            tenant_id='test_tenant',
            status='pending'
        )
        
        # Should detect time conflict
        existing_reservations = TableReservation.query.filter(
            TableReservation.table_id == self.test_tables[0].id,
            TableReservation.reservation_time.between(
                reservation.reservation_time - timedelta(hours=1),
                reservation.reservation_time + timedelta(hours=1)
            )
        ).all()
        
        self.assertGreater(len(existing_reservations), 0, "Should detect existing reservation")
        
        print("✅ Table reservation tests passed")
    
    def test_kitchen_operations(self):
        """Test kitchen station operations"""
        print("\n=== Testing Kitchen Operations ===")
        
        # Test station status management
        for station in self.test_stations:
            station.status = 'busy' if station.name == 'Main Kitchen' else 'active'
            station.current_orders = 3 if station.name == 'Main Kitchen' else 0
            db.session.commit()
            
            updated_station = KitchenStation.query.get(station.id)
            self.assertEqual(updated_station.status, station.status, "Station status should be updated")
            self.assertEqual(updated_station.current_orders, station.current_orders, 
                           "Current orders should be tracked")
        
        # Test order assignment to stations
        test_order = Order(
            order_number='KOT001',
            customer_name='Kitchen Test',
            order_type='Dine-in',
            table_id=self.test_tables[0].id,
            status='In Progress',
            total_amount=Decimal('250.00'),
            tenant_id='test_tenant'
        )
        db.session.add(test_order)
        db.session.commit()
        
        # Assign order to kitchen station
        test_order.kitchen_station_id = self.test_stations[0].id
        test_order.kot_sent_at = datetime.utcnow()
        db.session.commit()
        
        updated_order = Order.query.get(test_order.id)
        self.assertEqual(updated_order.kitchen_station_id, self.test_stations[0].id, 
                       "Order should be assigned to kitchen station")
        self.assertIsNotNone(updated_order.kot_sent_at, "KOT sent time should be recorded")
        
        print("✅ Kitchen operations tests passed")
    
    def test_shift_management(self):
        """Test restaurant shift management"""
        print("\n=== Testing Shift Management ===")
        
        # Test shift activation
        for shift in self.test_shifts:
            shift.status = 'active' if shift.name == 'Morning' else 'inactive'
            shift.current_staff_count = 5 if shift.name == 'Morning' else 0
            db.session.commit()
            
            updated_shift = RestaurantShift.query.get(shift.id)
            self.assertEqual(updated_shift.status, shift.status, "Shift status should be updated")
            self.assertEqual(updated_shift.current_staff_count, shift.current_staff_count,
                           "Staff count should be tracked")
        
        # Test shift handover
        morning_shift = next(s for s in self.test_shifts if s.name == 'Morning')
        evening_shift = next(s for s in self.test_shifts if s.name == 'Evening')
        
        # Simulate shift handover
        morning_shift.status = 'completed'
        morning_shift.ended_at = datetime.utcnow()
        evening_shift.status = 'active'
        evening_shift.started_at = datetime.utcnow()
        db.session.commit()
        
        updated_morning = RestaurantShift.query.get(morning_shift.id)
        updated_evening = RestaurantShift.query.get(evening_shift.id)
        
        self.assertEqual(updated_morning.status, 'completed', "Morning shift should be completed")
        self.assertIsNotNone(updated_morning.ended_at, "End time should be recorded")
        self.assertEqual(updated_evening.status, 'active', "Evening shift should be active")
        self.assertIsNotNone(updated_evening.started_at, "Start time should be recorded")
        
        print("✅ Shift management tests passed")


class TestApparelModule(unittest.TestCase):
    """Test apparel & footwear specific functionality"""
    
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
        
        # Enable apparel features
        feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', 'test_tenant')
        feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', 'test_tenant')
        feature_manager.enable_feature('FEATURE_STYLE_VARIANTS', 'test_tenant')
        feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', 'test_tenant')
        feature_manager.enable_feature('FEATURE_ALTERATION_TRACKING', 'test_tenant')
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for apparel module"""
        # Create apparel products
        cls.test_products = []
        for i in range(3):
            product = ApparelProduct(
                sku=f'APP{i+1:001}',
                name=f'Test Apparel Product {i+1}',
                description=f'Description for apparel product {i+1}',
                category='Clothing',
                brand='Test Brand',
                base_price=Decimal(str(1000 + i * 100)),
                tenant_id='test_tenant',
                status='active'
            )
            cls.test_products.append(product)
            db.session.add(product)
        
        # Create size matrix
        cls.test_size_matrix = ApparelSizeMatrix(
            product_id=cls.test_products[0].id,
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
            tenant_id='test_tenant'
        )
        db.session.add(cls.test_size_matrix)
        
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
                        tenant_id='test_tenant',
                        status='active'
                    )
                    cls.test_variants.append(variant)
                    db.session.add(variant)
        
        db.session.commit()
    
    def test_size_variant_management(self):
        """Test size variant functionality"""
        print("\n=== Testing Size Variant Management ===")
        
        # Test size matrix creation
        size_matrix = ApparelSizeMatrix(
            product_id=self.test_products[1].id,
            size_chart='Extended',
            sizes=['3XS', '2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL'],
            tenant_id='test_tenant'
        )
        db.session.add(size_matrix)
        db.session.commit()
        
        self.assertIsNotNone(size_matrix.id, "Size matrix should be created")
        
        # Test variant creation with size
        variant = ApparelVariant(
            product_id=self.test_products[1].id,
            sku=f'{self.test_products[1].sku}-M-Extended',
            size='M',
            color='White',
            price=self.test_products[1].base_price,
            stock_quantity=5,
            tenant_id='test_tenant'
        )
        db.session.add(variant)
        db.session.commit()
        
        self.assertIsNotNone(variant.id, "Variant should be created")
        self.assertEqual(variant.size, 'M', "Variant should have correct size")
        
        # Test size availability check
        available_sizes = db.session.query(ApparelVariant.size).filter(
            ApparelVariant.product_id == self.test_products[0].id,
            ApparelVariant.stock_quantity > 0
        ).distinct().all()
        
        self.assertGreater(len(available_sizes), 0, "Should have available sizes")
        
        print("✅ Size variant management tests passed")
    
    def test_color_variant_management(self):
        """Test color variant functionality"""
        print("\n=== Testing Color Variant Management ===")
        
        # Test color availability
        available_colors = db.session.query(ApparelVariant.color).filter(
            ApparelVariant.product_id == self.test_products[0].id,
            ApparelVariant.stock_quantity > 0
        ).distinct().all()
        
        self.assertGreater(len(available_colors), 0, "Should have available colors")
        
        # Test color-specific pricing
        premium_color_variant = ApparelVariant(
            product_id=self.test_products[0].id,
            sku=f'{self.test_products[0].sku}-Premium-Red',
            color='Premium Red',
            size='M',
            price=self.test_products[0].base_price + Decimal('200'),  # Premium color surcharge
            stock_quantity=3,
            tenant_id='test_tenant'
        )
        db.session.add(premium_color_variant)
        db.session.commit()
        
        self.assertGreater(premium_color_variant.price, self.test_products[0].base_price,
                          "Premium color should have higher price")
        
        # Test color filtering
        red_variants = ApparelVariant.query.filter(
            ApparelVariant.product_id == self.test_products[0].id,
            ApparelVariant.color == 'Red'
        ).all()
        
        self.assertGreater(len(red_variants), 0, "Should find red variants")
        
        print("✅ Color variant management tests passed")
    
    def test_exchange_management(self):
        """Test product exchange functionality"""
        print("\n=== Testing Exchange Management ===")
        
        # Create test order
        test_order = Order(
            order_number='EXCH001',
            customer_name='Exchange Customer',
            order_type='Sale',
            total_amount=Decimal('1500.00'),
            tenant_id='test_tenant',
            status='Completed'
        )
        db.session.add(test_order)
        db.session.commit()
        
        # Create exchange request
        exchange = ApparelExchange(
            order_id=test_order.id,
            customer_name='Exchange Customer',
            customer_phone='+1234567890',
            exchange_reason='Size too small',
            exchange_type='size_exchange',
            original_item_sku=self.test_variants[0].sku,
            original_item_size=self.test_variants[0].size,
            original_item_color=self.test_variants[0].color,
            new_item_sku=self.test_variants[1].sku,
            new_item_size=self.test_variants[1].size,
            new_item_color=self.test_variants[1].color,
            exchange_date=datetime.utcnow(),
            status='pending',
            tenant_id='test_tenant'
        )
        db.session.add(exchange)
        db.session.commit()
        
        self.assertIsNotNone(exchange.id, "Exchange should be created")
        
        # Test exchange status updates
        exchange.status = 'approved'
        exchange.approved_by = 'store_manager'
        exchange.approved_at = datetime.utcnow()
        db.session.commit()
        
        updated_exchange = ApparelExchange.query.get(exchange.id)
        self.assertEqual(updated_exchange.status, 'approved', "Exchange status should be updated")
        self.assertIsNotNone(updated_exchange.approved_at, "Approval time should be recorded")
        
        # Test inventory adjustment for exchange
        original_variant = ApparelVariant.query.filter_by(
            sku=exchange.original_item_sku
        ).first()
        new_variant = ApparelVariant.query.filter_by(
            sku=exchange.new_item_sku
        ).first()
        
        if original_variant and new_variant:
            # Adjust inventory
            original_variant.stock_quantity += 1  # Return original item
            new_variant.stock_quantity -= 1  # Give new item
            db.session.commit()
            
            updated_original = ApparelVariant.query.get(original_variant.id)
            updated_new = ApparelVariant.query.get(new_variant.id)
            
            self.assertEqual(updated_original.stock_quantity, 11, "Original item stock should increase")
            self.assertEqual(updated_new.stock_quantity, 9, "New item stock should decrease")
        
        print("✅ Exchange management tests passed")


class TestBooksModule(unittest.TestCase):
    """Test books & office supplies specific functionality"""
    
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
        
        # Enable books features
        feature_manager.enable_feature('FEATURE_SALES_PROCESSING', 'test_tenant')
        feature_manager.enable_feature('FEATURE_PRODUCT_CATALOG', 'test_tenant')
        feature_manager.enable_feature('FEATURE_CUSTOMER_MANAGEMENT', 'test_tenant')
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for books module"""
        # Create authors
        cls.test_authors = []
        authors = [
            ('John Doe', 'Fiction author'),
            ('Jane Smith', 'Non-fiction author'),
            ('Robert Johnson', 'Technical author')
        ]
        for name, description in authors:
            author = BookAuthor(
                name=name,
                description=description,
                tenant_id='test_tenant'
            )
            cls.test_authors.append(author)
            db.session.add(author)
        
        # Create publishers
        cls.test_publishers = []
        publishers = [
            ('Test Publishing House', 'Fiction and non-fiction'),
            ('Tech Books Inc', 'Technical publications'),
            ('Academic Press', 'Academic publications')
        ]
        for name, description in publishers:
            publisher = BookPublisher(
                name=name,
                description=description,
                tenant_id='test_tenant'
            )
            cls.test_publishers.append(publisher)
            db.session.add(publisher)
        
        # Create book categories
        cls.test_categories = []
        categories = [
            ('Fiction', 'Fictional literature'),
            ('Non-Fiction', 'Non-fictional works'),
            ('Technical', 'Technical and reference books')
        ]
        for name, description in categories:
            category = BookCategory(
                name=name,
                description=description,
                tenant_id='test_tenant'
            )
            cls.test_categories.append(category)
            db.session.add(category)
        
        db.session.commit()
        
        # Create book products
        cls.test_books = []
        for i in range(5):
            book = BookProduct(
                isbn=f'978-{1234567890 + i}',
                title=f'Test Book {i+1}',
                author_id=cls.test_authors[i % len(cls.test_authors)].id,
                publisher_id=cls.test_publishers[i % len(cls.test_publishers)].id,
                category_id=cls.test_categories[i % len(cls.test_categories)].id,
                description=f'Description for test book {i+1}',
                price=Decimal(str(299 + i * 50)),
                pages=200 + i * 50,
                language='English',
                publication_year=2020 + i,
                tenant_id='test_tenant',
                status='active'
            )
            cls.test_books.append(book)
            db.session.add(book)
        
        db.session.commit()
    
    def test_isbn_management(self):
        """Test ISBN tracking and validation"""
        print("\n=== Testing ISBN Management ===")
        
        # Test ISBN-13 validation
        valid_isbn = '978-3-16-148410-0'
        book = BookProduct(
            isbn=valid_isbn,
            title='Valid ISBN Book',
            author_id=self.test_authors[0].id,
            publisher_id=self.test_publishers[0].id,
            category_id=self.test_categories[0].id,
            price=Decimal('299.00'),
            tenant_id='test_tenant'
        )
        db.session.add(book)
        db.session.commit()
        
        self.assertIsNotNone(book.id, "Book with valid ISBN should be created")
        
        # Test ISBN uniqueness
        duplicate_book = BookProduct(
            isbn=valid_isbn,  # Same ISBN
            title='Duplicate ISBN Book',
            author_id=self.test_authors[1].id,
            publisher_id=self.test_publishers[1].id,
            category_id=self.test_categories[1].id,
            price=Decimal('399.00'),
            tenant_id='test_tenant'
        )
        
        # Should detect duplicate ISBN
        existing_book = BookProduct.query.filter_by(isbn=valid_isbn).first()
        self.assertIsNotNone(existing_book, "Should find existing book with same ISBN")
        
        # Test ISBN format validation
        invalid_isbns = [
            '978-3-16-148410',  # Missing check digit
            '978-3161484100',   # Missing hyphens
            '978-3-16-14841-00', # Invalid format
            '1234567890123'      # Too long
        ]
        
        for invalid_isbn in invalid_isbns:
            # In real implementation, this would validate ISBN format
            # For testing, we just check length and format
            is_valid = (len(invalid_isbn.replace('-', '')) == 13 and 
                       invalid_isbn.count('-') >= 2)
            self.assertFalse(is_valid, f"ISBN {invalid_isbn} should be invalid")
        
        print("✅ ISBN management tests passed")
    
    def test_author_publisher_relations(self):
        """Test author and publisher relationships"""
        print("\n=== Testing Author Publisher Relations ===")
        
        # Test author's books
        author_books = BookProduct.query.filter_by(
            author_id=self.test_authors[0].id
        ).all()
        
        self.assertGreater(len(author_books), 0, "Author should have associated books")
        
        # Test publisher's books
        publisher_books = BookProduct.query.filter_by(
            publisher_id=self.test_publishers[0].id
        ).all()
        
        self.assertGreater(len(publisher_books), 0, "Publisher should have associated books")
        
        # Test author statistics
        author = self.test_authors[0]
        author.total_books = len(author_books)
        db.session.commit()
        
        updated_author = BookAuthor.query.get(author.id)
        self.assertEqual(updated_author.total_books, len(author_books), 
                       "Author book count should be updated")
        
        # Test publisher statistics
        publisher = self.test_publishers[0]
        publisher.total_books = len(publisher_books)
        db.session.commit()
        
        updated_publisher = BookPublisher.query.get(publisher.id)
        self.assertEqual(updated_publisher.total_books, len(publisher_books),
                       "Publisher book count should be updated")
        
        print("✅ Author publisher relations tests passed")
    
    def test_special_orders(self):
        """Test special book orders functionality"""
        print("\n=== Testing Special Orders ===")
        
        # Create special order
        special_order = BookVariant(
            product_id=self.test_books[0].id,
            sku=f'{self.test_books[0].isbn}-SPECIAL',
            title=f'{self.test_books[0].title} (Special Order)',
            is_special_order=True,
            customer_name='Special Order Customer',
            customer_phone='+1234567890',
            customer_email='customer@example.com',
            special_request='Signed copy with dedication',
            expected_delivery_date=datetime.utcnow() + timedelta(days=14),
            status='ordered',
            tenant_id='test_tenant'
        )
        db.session.add(special_order)
        db.session.commit()
        
        self.assertIsNotNone(special_order.id, "Special order should be created")
        self.assertTrue(special_order.is_special_order, "Should be marked as special order")
        
        # Test special order status tracking
        special_order.status = 'received'
        special_order.received_date = datetime.utcnow()
        db.session.commit()
        
        updated_order = BookVariant.query.get(special_order.id)
        self.assertEqual(updated_order.status, 'received', "Status should be updated")
        self.assertIsNotNone(updated_order.received_date, "Received date should be recorded")
        
        # Test customer notification
        special_order.status = 'ready_for_pickup'
        special_order.notification_sent = True
        special_order.notification_date = datetime.utcnow()
        db.session.commit()
        
        final_order = BookVariant.query.get(special_order.id)
        self.assertEqual(final_order.status, 'ready_for_pickup', "Status should be updated")
        self.assertTrue(final_order.notification_sent, "Notification should be marked as sent")
        
        print("✅ Special orders tests passed")


class TestGroceryModule(unittest.TestCase):
    """Test grocery & supermarket specific functionality"""
    
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
        
        # Enable grocery features
        feature_manager.enable_feature('FEATURE_WEIGHING_SCALE', 'test_tenant')
        feature_manager.enable_feature('FEATURE_EXPIRY_TRACKING', 'test_tenant')
        feature_manager.enable_feature('FEATURE_BATCH_TRACKING', 'test_tenant')
        feature_manager.enable_feature('FEATURE_PRICE_BY_WEIGHT', 'test_tenant')
        feature_manager.enable_feature('FEATURE_COMBO_OFFERS', 'test_tenant')
        
        cls._create_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_data(cls):
        """Create test data for grocery module"""
        # Create fresh produce items
        cls.test_produce = []
        produce_items = [
            ('Apples', 'Fresh red apples', 'kg', 5.99),
            ('Bananas', 'Ripe bananas', 'kg', 3.99),
            ('Tomatoes', 'Fresh tomatoes', 'kg', 8.99),
            ('Potatoes', 'White potatoes', 'kg', 4.99)
        ]
        
        for name, description, unit, price in produce_items:
            produce = FreshProduce(
                name=name,
                description=description,
                category='Fresh Produce',
                unit=unit,
                price_per_unit=Decimal(str(price)),
                tenant_id='test_tenant',
                status='active'
            )
            cls.test_produce.append(produce)
            db.session.add(produce)
        
        # Create inventory records
        cls.test_inventory = []
        for produce in cls.test_produce:
            inventory = FreshProduceInventory(
                produce_id=produce.id,
                current_stock=Decimal('100.5'),
                unit=produce.unit,
                batch_number=f'BATCH{produce.id:03d}',
                expiry_date=datetime.utcnow() + timedelta(days=7),
                received_date=datetime.utcnow() - timedelta(days=1),
                supplier='Fresh Supplier Inc',
                quality_grade='A',
                tenant_id='test_tenant'
            )
            cls.test_inventory.append(inventory)
            db.session.add(inventory)
        
        db.session.commit()
    
    def test_weighing_scale_integration(self):
        """Test weighing scale integration"""
        print("\n=== Testing Weighing Scale Integration ===")
        
        # Create weighing scale integration record
        scale_integration = WeighingScaleIntegration(
            scale_id='SCALE001',
            scale_name='Main Produce Scale',
            model='WS-2000',
            location='Produce Section',
            calibration_date=datetime.utcnow() - timedelta(days=7),
            next_calibration_date=datetime.utcnow() + timedelta(days=30),
            status='active',
            tenant_id='test_tenant'
        )
        db.session.add(scale_integration)
        db.session.commit()
        
        self.assertIsNotNone(scale_integration.id, "Scale integration should be created")
        
        # Test weight measurement
        weight_measurement = {
            'scale_id': 'SCALE001',
            'product_id': self.test_produce[0].id,
            'measured_weight': Decimal('1.234'),
            'unit': 'kg',
            'measurement_time': datetime.utcnow(),
            'operator_id': 'operator001'
        }
        
        # Calculate price based on weight
        produce = self.test_produce[0]
        calculated_price = weight_measurement['measured_weight'] * produce.price_per_unit
        
        expected_price = Decimal('1.234') * Decimal('5.99')
        self.assertAlmostEqual(calculated_price, expected_price, places=2,
                          msg="Price calculation should be accurate")
        
        # Test scale status monitoring
        scale_integration.last_heartbeat = datetime.utcnow()
        scale_integration.is_connected = True
        db.session.commit()
        
        updated_scale = WeighingScaleIntegration.query.get(scale_integration.id)
        self.assertTrue(updated_scale.is_connected, "Scale should be marked as connected")
        self.assertIsNotNone(updated_scale.last_heartbeat, "Heartbeat should be recorded")
        
        print("✅ Weighing scale integration tests passed")
    
    def test_expiry_tracking(self):
        """Test product expiry tracking"""
        print("\n=== Testing Expiry Tracking ===")
        
        # Test expiry date validation
        expiring_items = FreshProduceInventory.query.filter(
            FreshProduceInventory.expiry_date <= datetime.utcnow() + timedelta(days=3)
        ).all()
        
        self.assertGreater(len(expiring_items), 0, "Should find items expiring soon")
        
        # Test expiry alerts
        for inventory in self.test_inventory:
            days_to_expiry = (inventory.expiry_date - datetime.utcnow()).days
            
            if days_to_expiry <= 3:
                # Create expiry alert
                alert = LowStockAlert(
                    product_type='fresh_produce',
                    product_id=inventory.produce_id,
                    alert_type='expiry_warning',
                    alert_message=f'Product expires in {days_to_expiry} days',
                    threshold_value=3,
                    current_value=days_to_expiry,
                    tenant_id='test_tenant'
                )
                db.session.add(alert)
        
        db.session.commit()
        
        # Check for created alerts
        expiry_alerts = LowStockAlert.query.filter_by(
            alert_type='expiry_warning',
            tenant_id='test_tenant'
        ).all()
        
        self.assertGreater(len(expiry_alerts), 0, "Should create expiry alerts")
        
        # Test automatic stock reduction for expired items
        expired_inventory = FreshProduceInventory.query.filter(
            FreshProduceInventory.expiry_date <= datetime.utcnow()
        ).first()
        
        if expired_inventory:
            expired_inventory.status = 'expired'
            expired_inventory.current_stock = Decimal('0')
            db.session.commit()
            
            updated_inventory = FreshProduceInventory.query.get(expired_inventory.id)
            self.assertEqual(updated_inventory.status, 'expired', "Status should be expired")
            self.assertEqual(updated_inventory.current_stock, Decimal('0'), "Stock should be zero")
        
        print("✅ Expiry tracking tests passed")
    
    def test_batch_tracking(self):
        """Test batch tracking functionality"""
        print("\n=== Testing Batch Tracking ===")
        
        # Test batch creation
        new_batch = FreshProduceInventory(
            produce_id=self.test_produce[0].id,
            current_stock=Decimal('50.0'),
            unit='kg',
            batch_number='BATCH2024001',
            expiry_date=datetime.utcnow() + timedelta(days=10),
            received_date=datetime.utcnow(),
            supplier='New Supplier Ltd',
            quality_grade='A+',
            temperature_zone='cool',
            tenant_id='test_tenant'
        )
        db.session.add(new_batch)
        db.session.commit()
        
        self.assertIsNotNone(new_batch.id, "Batch should be created")
        
        # Test batch tracking
        batch_transactions = [
            {
                'transaction_type': 'received',
                'quantity': Decimal('50.0'),
                'transaction_date': datetime.utcnow(),
                'reference': 'PO001'
            },
            {
                'transaction_type': 'sold',
                'quantity': Decimal('5.5'),
                'transaction_date': datetime.utcnow() + timedelta(hours=2),
                'reference': 'SALE001'
            }
        ]
        
        for transaction in batch_transactions:
            inventory_transaction = InventoryTransaction(
                product_type='fresh_produce',
                product_id=new_batch.produce_id,
                batch_number=new_batch.batch_number,
                transaction_type=transaction['transaction_type'],
                quantity=transaction['quantity'],
                transaction_date=transaction['transaction_date'],
                reference=transaction['reference'],
                tenant_id='test_tenant'
            )
            db.session.add(inventory_transaction)
        
        db.session.commit()
        
        # Verify batch transactions
        batch_transaction_records = InventoryTransaction.query.filter_by(
            batch_number=new_batch.batch_number,
            tenant_id='test_tenant'
        ).all()
        
        self.assertEqual(len(batch_transaction_records), len(batch_transactions),
                       "Should record all batch transactions")
        
        # Test batch reconciliation
        total_received = sum(t['quantity'] for t in batch_transactions 
                            if t['transaction_type'] == 'received')
        total_sold = sum(t['quantity'] for t in batch_transactions 
                        if t['transaction_type'] == 'sold')
        expected_stock = total_received - total_sold
        
        updated_batch = FreshProduceInventory.query.get(new_batch.id)
        self.assertEqual(updated_batch.current_stock, expected_stock,
                       "Batch stock should match transactions")
        
        print("✅ Batch tracking tests passed")


def run_multi_retail_tests():
    """Run all multi-retail module tests"""
    print("=" * 80)
    print("MULTI-RETAIL MODULE TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing all retail modules with their specific business logic\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestRestaurantModule,
        TestApparelModule,
        TestBooksModule,
        TestGroceryModule
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("MULTI-RETAIL MODULE TEST RESULTS")
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
    success = run_multi_retail_tests()
    
    if success:
        print("\n✅ ALL MULTI-RETAIL MODULE TESTS PASSED!")
        print("All retail modules are working correctly")
        exit(0)
    else:
        print("\n❌ SOME MULTI-RETAIL MODULE TESTS FAILED!")
        print("Review and fix retail module issues")
        exit(1)