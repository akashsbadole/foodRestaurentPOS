"""
Pytest configuration and fixtures for the multi-retail POS testing framework.
Provides shared test data, database setup, and utility functions.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

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


@pytest.fixture(scope='session')
def test_config():
    """Test configuration for pytest"""
    return {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 300
    }


@pytest.fixture(scope='function')
def app(test_config):
    """Create application for testing"""
    app = create_app('testing')
    app.config.update(test_config)
    
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def database(app):
    """Create database for testing"""
    db.create_all()
    yield db
    db.drop_all()


@pytest.fixture(scope='function')
def sample_tenant(database):
    """Create sample tenant for testing"""
    tenant = Tenant(
        name='Test Tenant',
        subdomain='test',
        database_name='test_db',
        retail_type='general',
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    return tenant


@pytest.fixture(scope='function')
def restaurant_tenant(database):
    """Create restaurant tenant for testing"""
    tenant = Tenant(
        name='Restaurant Test Tenant',
        subdomain='restaurant-test',
        database_name='restaurant_test_db',
        retail_type='restaurant',
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    
    # Enable restaurant features
    feature_manager.enable_feature('FEATURE_TABLE_MANAGEMENT', str(tenant.id))
    feature_manager.enable_feature('FEATURE_RESERVATIONS', str(tenant.id))
    feature_manager.enable_feature('FEATURE_KOT_PRINTING', str(tenant.id))
    feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', str(tenant.id))
    
    return tenant


@pytest.fixture(scope='function')
def apparel_tenant(database):
    """Create apparel tenant for testing"""
    tenant = Tenant(
        name='Apparel Test Tenant',
        subdomain='apparel-test',
        database_name='apparel_test_db',
        retail_type='apparel',
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    
    # Enable apparel features
    feature_manager.enable_feature('FEATURE_SIZE_VARIANTS', str(tenant.id))
    feature_manager.enable_feature('FEATURE_COLOR_VARIANTS', str(tenant.id))
    feature_manager.enable_feature('FEATURE_EXCHANGE_MANAGEMENT', str(tenant.id))
    
    return tenant


@pytest.fixture(scope='function')
def books_tenant(database):
    """Create books tenant for testing"""
    tenant = Tenant(
        name='Books Test Tenant',
        subdomain='books-test',
        database_name='books_test_db',
        retail_type='books',
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    
    # Enable books features
    feature_manager.enable_feature('FEATURE_ISBN_TRACKING', str(tenant.id))
    feature_manager.enable_feature('FEATURE_SPECIAL_ORDERS', str(tenant.id))
    
    return tenant


@pytest.fixture(scope='function')
def admin_user(database, sample_tenant):
    """Create admin user for testing"""
    user = User(
        username='admin',
        email='admin@test.com',
        password_hash='hashed_password',
        role='admin',
        tenant_id=str(sample_tenant.id),
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def manager_user(database, sample_tenant):
    """Create manager user for testing"""
    user = User(
        username='manager',
        email='manager@test.com',
        password_hash='hashed_password',
        role='manager',
        tenant_id=str(sample_tenant.id),
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def staff_user(database, sample_tenant):
    """Create staff user for testing"""
    user = User(
        username='staff',
        email='staff@test.com',
        password_hash='hashed_password',
        role='staff',
        tenant_id=str(sample_tenant.id),
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope='function')
def auth_headers(client, admin_user):
    """Create authentication headers for testing"""
    login_data = {
        'username': 'admin',
        'password': 'test_password',
        'tenant_id': str(admin_user.tenant_id)
    }
    
    response = client.post('/api/auth/login',
                         data=json.dumps(login_data),
                         content_type='application/json')
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def staff_headers(client, staff_user):
    """Create staff authentication headers for testing"""
    login_data = {
        'username': 'staff',
        'password': 'test_password',
        'tenant_id': str(staff_user.tenant_id)
    }
    
    response = client.post('/api/auth/login',
                         data=json.dumps(login_data),
                         content_type='application/json')
    
    token = json.loads(response.data)['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def sample_products(database, sample_tenant):
    """Create sample products for testing"""
    products = []
    for i in range(5):
        product = Product(
            sku=f'SAMPLE{i+1:03d}',
            name=f'Sample Product {i+1}',
            description=f'Description for sample product {i+1}',
            price=Decimal(str(100 + i * 50)),
            tenant_id=str(sample_tenant.id),
            status='active'
        )
        products.append(product)
        db.session.add(product)
    
    db.session.commit()
    return products


@pytest.fixture(scope='function')
def restaurant_tables(database, restaurant_tenant):
    """Create restaurant tables for testing"""
    tables = []
    for i in range(5):
        table = RestaurantTable(
            table_number=f'T{i+1}',
            capacity=4 + i,
            location=f'Area {chr(65+i)}',
            description=f'Test table {i+1}',
            tenant_id=str(restaurant_tenant.id),
            status='available'
        )
        tables.append(table)
        db.session.add(table)
    
    db.session.commit()
    return tables


@pytest.fixture(scope='function')
def apparel_products(database, apparel_tenant):
    """Create apparel products for testing"""
    products = []
    for i in range(3):
        product = ApparelProduct(
            sku=f'APP{i+1:001}',
            name=f'Apparel Product {i+1}',
            description=f'Description for apparel product {i+1}',
            category='Clothing',
            brand='Test Brand',
            base_price=Decimal(str(500 + i * 100)),
            tenant_id=str(apparel_tenant.id),
            status='active'
        )
        products.append(product)
        db.session.add(product)
    
    db.session.commit()
    
    # Create variants
    variants = []
    colors = ['Red', 'Blue', 'Black']
    sizes = ['S', 'M', 'L']
    
    for product in products:
        for color in colors:
            for size in sizes:
                variant = ApparelVariant(
                    product_id=product.id,
                    sku=f'{product.sku}-{color[0]}{size}',
                    color=color,
                    size=size,
                    price=product.base_price + Decimal('50'),
                    stock_quantity=10,
                    tenant_id=str(apparel_tenant.id),
                    status='active'
                )
                variants.append(variant)
                db.session.add(variant)
    
    db.session.commit()
    return products, variants


@pytest.fixture(scope='function')
def book_authors(database, books_tenant):
    """Create book authors for testing"""
    authors = []
    author_names = [
        ('John Doe', 'Fiction author'),
        ('Jane Smith', 'Non-fiction author'),
        ('Robert Johnson', 'Technical author')
    ]
    
    for name, description in author_names:
        author = BookAuthor(
            name=name,
            description=description,
            tenant_id=str(books_tenant.id)
        )
        authors.append(author)
        db.session.add(author)
    
    db.session.commit()
    return authors


@pytest.fixture(scope='function')
def sample_orders(database, sample_tenant, sample_products):
    """Create sample orders for testing"""
    orders = []
    for i in range(3):
        order = Order(
            order_number=f'ORD{i+1:03d}',
            customer_name=f'Customer {i+1}',
            order_type='Sale',
            total_amount=Decimal(str(200 + i * 100)),
            tenant_id=str(sample_tenant.id),
            status='Completed'
        )
        orders.append(order)
        db.session.add(order)
    
    db.session.commit()
    
    # Create order items
    for i, order in enumerate(orders):
        for j in range(2):
            item = OrderItem(
                order_id=order.id,
                product_id=sample_products[j].id,
                quantity=1 + j,
                unit_price=sample_products[j].price,
                total_price=sample_products[j].price * (1 + j),
                tenant_id=str(sample_tenant.id)
            )
            db.session.add(item)
    
    db.session.commit()
    return orders


@pytest.fixture(scope='function')
def mock_payment_gateway():
    """Mock payment gateway for testing"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'transaction_id': 'txn_test123456',
            'status': 'success',
            'amount': 999.00,
            'currency': 'USD'
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture(scope='function')
def mock_email_service():
    """Mock email service for testing"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value = mock_server
        yield mock_smtp


@pytest.fixture(scope='function')
def mock_sms_service():
    """Mock SMS service for testing"""
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message_id': 'msg_test123456',
            'status': 'sent',
            'to': '+1234567890'
        }
        mock_post.return_value = mock_response
        yield mock_post


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_tenant(**kwargs):
        """Create a tenant with custom attributes"""
        defaults = {
            'name': 'Test Tenant',
            'subdomain': 'test',
            'database_name': 'test_db',
            'retail_type': 'general',
            'status': 'active'
        }
        defaults.update(kwargs)
        
        tenant = Tenant(**defaults)
        db.session.add(tenant)
        db.session.commit()
        return tenant
    
    @staticmethod
    def create_user(tenant_id, **kwargs):
        """Create a user with custom attributes"""
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': 'hashed_password',
            'role': 'staff',
            'tenant_id': str(tenant_id),
            'is_active': True
        }
        defaults.update(kwargs)
        
        user = User(**defaults)
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_product(tenant_id, **kwargs):
        """Create a product with custom attributes"""
        defaults = {
            'sku': 'TEST001',
            'name': 'Test Product',
            'description': 'Test description',
            'price': Decimal('99.99'),
            'tenant_id': str(tenant_id),
            'status': 'active'
        }
        defaults.update(kwargs)
        
        product = Product(**defaults)
        db.session.add(product)
        db.session.commit()
        return product
    
    @staticmethod
    def create_order(tenant_id, **kwargs):
        """Create an order with custom attributes"""
        defaults = {
            'order_number': 'ORD001',
            'customer_name': 'Test Customer',
            'order_type': 'Sale',
            'total_amount': Decimal('99.99'),
            'tenant_id': str(tenant_id),
            'status': 'Pending'
        }
        defaults.update(kwargs)
        
        order = Order(**defaults)
        db.session.add(order)
        db.session.commit()
        return order


@pytest.fixture(scope='function')
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "restaurant: mark test as restaurant-specific"
    )
    config.addinivalue_line(
        "markers", "apparel: mark test as apparel-specific"
    )
    config.addinivalue_line(
        "markers", "books: mark test as books-specific"
    )
    config.addinivalue_line(
        "markers", "grocery: mark test as grocery-specific"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location"""
    for item in items:
        # Add markers based on file location
        if 'test_feature_flags' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif 'test_multi_retail_modules' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif 'test_database_schema' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif 'test_api_comprehensive' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif 'test_ui_ux' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif 'test_performance' in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        elif 'test_security_comprehensive' in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif 'test_integration_workflows' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        
        # Add retail type markers based on test name
        test_name = item.name.lower()
        if 'restaurant' in test_name:
            item.add_marker(pytest.mark.restaurant)
        elif 'apparel' in test_name:
            item.add_marker(pytest.mark.apparel)
        elif 'books' in test_name:
            item.add_marker(pytest.mark.books)
        elif 'grocery' in test_name:
            item.add_marker(pytest.mark.grocery)