"""
Comprehensive Multi-Tenancy Implementation Test Suite
Tests all aspects of the multi-tenant architecture including:
- Database schema and models
- Tenant identification middleware
- Tenant-aware queries
- Security isolation
- Feature management
- Subscription management
"""

import unittest
import tempfile
import os
import json
from datetime import datetime, timedelta
from flask import Flask, g
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import models and utilities
from models import db, create_app
from models.tenant import Tenant, TenantSettings, SubscriptionPlan, TenantSubscription, TenantFeatureFlag, TenantUsage
from models.user import User
from models.order import Order, OrderItem
from models.menu_item import MenuItem
from models.settings import Settings
from middleware.tenant_middleware import TenantMiddleware, TenantContext
from utils.tenant_query_manager import TenantQueryManager, tenant_scoped


class MultiTenancyTestCase(unittest.TestCase):
    """Test case for multi-tenancy implementation"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test data
        self.create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_data(self):
        """Create test data for multi-tenancy tests"""
        # Create subscription plans
        self.basic_plan = SubscriptionPlan(
            name='Basic',
            identifier='basic',
            description='Basic plan for small restaurants',
            price=29.99,
            billing_cycle='monthly',
            features=json.dumps({
                'max_users': 5,
                'max_orders_per_month': 1000,
                'api_calls_per_day': 10000,
                'features': ['basic_reporting', 'menu_management', 'order_management']
            }),
            is_active=True
        )
        
        self.premium_plan = SubscriptionPlan(
            name='Premium',
            identifier='premium',
            description='Premium plan for growing restaurants',
            price=99.99,
            billing_cycle='monthly',
            features=json.dumps({
                'max_users': 20,
                'max_orders_per_month': 10000,
                'api_calls_per_day': 100000,
                'features': ['advanced_reporting', 'crm', 'loyalty', 'inventory_management', 'multi_store']
            }),
            is_active=True
        )
        
        db.session.add(self.basic_plan)
        db.session.add(self.premium_plan)
        
        # Create test tenants
        self.tenant1 = Tenant(
            name='Restaurant One',
            identifier='restaurant1',
            subdomain='restaurant1',
            contact_email='admin@restaurant1.com',
            is_active=True
        )
        
        self.tenant2 = Tenant(
            name='Restaurant Two',
            identifier='restaurant2',
            subdomain='restaurant2',
            contact_email='admin@restaurant2.com',
            is_active=True
        )
        
        db.session.add(self.tenant1)
        db.session.add(self.tenant2)
        db.session.flush()
        
        # Create tenant settings
        self.tenant1_settings = TenantSettings(
            tenant_id=self.tenant1.id,
            timezone='America/New_York',
            currency='USD',
            theme='default'
        )
        
        self.tenant2_settings = TenantSettings(
            tenant_id=self.tenant2.id,
            timezone='Europe/London',
            currency='EUR',
            theme='dark'
        )
        
        db.session.add(self.tenant1_settings)
        db.session.add(self.tenant2_settings)
        
        # Create subscriptions
        self.tenant1_subscription = TenantSubscription(
            tenant_id=self.tenant1.id,
            plan_id=self.basic_plan.id,
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        self.tenant2_subscription = TenantSubscription(
            tenant_id=self.tenant2.id,
            plan_id=self.premium_plan.id,
            status='active',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30)
        )
        
        db.session.add(self.tenant1_subscription)
        db.session.add(self.tenant2_subscription)
        
        # Create users for each tenant
        self.tenant1_admin = User(
            username='tenant1_admin',
            email='admin@restaurant1.com',
            first_name='Admin',
            last_name='User',
            tenant_id=self.tenant1.id,
            is_tenant_admin=True,
            is_active=True
        )
        self.tenant1_admin.set_password('password123')
        
        self.tenant1_user = User(
            username='tenant1_user',
            email='user@restaurant1.com',
            first_name='Regular',
            last_name='User',
            tenant_id=self.tenant1.id,
            is_tenant_admin=False,
            is_active=True
        )
        self.tenant1_user.set_password('password123')
        
        self.tenant2_admin = User(
            username='tenant2_admin',
            email='admin@restaurant2.com',
            first_name='Admin',
            last_name='User',
            tenant_id=self.tenant2.id,
            is_tenant_admin=True,
            is_active=True
        )
        self.tenant2_admin.set_password('password123')
        
        db.session.add(self.tenant1_admin)
        db.session.add(self.tenant1_user)
        db.session.add(self.tenant2_admin)
        
        # Create menu items for each tenant
        self.tenant1_item = MenuItem(
            name='Burger',
            description='Delicious burger',
            price=9.99,
            category_id=1,
            tenant_id=self.tenant1.id
        )
        
        self.tenant2_item = MenuItem(
            name='Pizza',
            description='Delicious pizza',
            price=12.99,
            category_id=1,
            tenant_id=self.tenant2.id
        )
        
        db.session.add(self.tenant1_item)
        db.session.add(self.tenant2_item)
        
        # Create orders for each tenant
        self.tenant1_order = Order(
            order_number='ORD001',
            table_id=1,
            subtotal=19.98,
            tax=1.60,
            total=21.58,
            status='completed',
            tenant_id=self.tenant1.id
        )
        
        self.tenant2_order = Order(
            order_number='ORD002',
            table_id=1,
            subtotal=25.98,
            tax=2.08,
            total=28.06,
            status='completed',
            tenant_id=self.tenant2.id
        )
        
        db.session.add(self.tenant1_order)
        db.session.add(self.tenant2_order)
        
        db.session.commit()


class TenantModelTests(MultiTenancyTestCase):
    """Test tenant model functionality"""
    
    def test_tenant_creation(self):
        """Test tenant creation and basic properties"""
        tenant = Tenant.query.filter_by(identifier='restaurant1').first()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.name, 'Restaurant One')
        self.assertEqual(tenant.subdomain, 'restaurant1')
        self.assertTrue(tenant.is_active)
    
    def test_tenant_settings_relationship(self):
        """Test tenant settings relationship"""
        tenant = Tenant.query.filter_by(identifier='restaurant1').first()
        settings = tenant.settings.first()
        self.assertIsNotNone(settings)
        self.assertEqual(settings.timezone, 'America/New_York')
        self.assertEqual(settings.currency, 'USD')
    
    def test_tenant_subscription_relationship(self):
        """Test tenant subscription relationship"""
        tenant = Tenant.query.filter_by(identifier='restaurant1').first()
        subscription = tenant.active_subscription()
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.plan.name, 'Basic')
        self.assertEqual(subscription.status, 'active')
    
    def test_tenant_has_feature_method(self):
        """Test tenant feature checking method"""
        tenant1 = Tenant.query.filter_by(identifier='restaurant1').first()
        tenant2 = Tenant.query.filter_by(identifier='restaurant2').first()
        
        # Basic plan should have basic features
        self.assertTrue(tenant1.has_feature('basic_reporting'))
        self.assertTrue(tenant1.has_feature('menu_management'))
        self.assertFalse(tenant1.has_feature('crm'))
        
        # Premium plan should have advanced features
        self.assertTrue(tenant2.has_feature('advanced_reporting'))
        self.assertTrue(tenant2.has_feature('crm'))
        self.assertTrue(tenant2.has_feature('loyalty'))
    
    def test_tenant_has_plan_method(self):
        """Test tenant plan checking method"""
        tenant1 = Tenant.query.filter_by(identifier='restaurant1').first()
        tenant2 = Tenant.query.filter_by(identifier='restaurant2').first()
        
        self.assertTrue(tenant1.has_plan('basic'))
        self.assertFalse(tenant1.has_plan('premium'))
        
        self.assertTrue(tenant2.has_plan('premium'))
        self.assertFalse(tenant2.has_plan('basic'))
    
    def test_tenant_user_isolation(self):
        """Test that users are properly isolated by tenant"""
        tenant1_users = User.query.filter_by(tenant_id=self.tenant1.id).all()
        tenant2_users = User.query.filter_by(tenant_id=self.tenant2.id).all()
        
        self.assertEqual(len(tenant1_users), 2)
        self.assertEqual(len(tenant2_users), 1)
        
        # Verify no cross-tenant access
        for user in tenant1_users:
            self.assertEqual(user.tenant_id, self.tenant1.id)
        
        for user in tenant2_users:
            self.assertEqual(user.tenant_id, self.tenant2.id)


class TenantQueryManagerTests(MultiTenancyTestCase):
    """Test tenant query manager functionality"""
    
    def test_get_tenant_query(self):
        """Test tenant-aware query filtering"""
        with self.app.test_request_context():
            # Set tenant context
            g.tenant_id = self.tenant1.id
            
            # Test tenant-scoped query
            query = TenantQueryManager.get_tenant_query(User)
            users = query.all()
            
            self.assertEqual(len(users), 2)
            for user in users:
                self.assertEqual(user.tenant_id, self.tenant1.id)
    
    def test_check_tenant_access(self):
        """Test tenant access validation"""
        with self.app.test_request_context():
            # Set tenant context
            g.tenant_id = self.tenant1.id
            
            # Test access to tenant's own resource
            self.assertTrue(TenantQueryManager.check_tenant_access(
                self.tenant1_admin.id, User
            ))
            
            # Test access to other tenant's resource
            self.assertFalse(TenantQueryManager.check_tenant_access(
                self.tenant2_admin.id, User
            ))
    
    def test_create_tenant_resource(self):
        """Test creating resources with tenant context"""
        with self.app.test_request_context():
            # Set tenant context
            g.tenant_id = self.tenant1.id
            
            # Create resource with tenant context
            data = {
                'name': 'New Item',
                'description': 'Test item',
                'price': 15.99,
                'category_id': 1
            }
            
            item = TenantQueryManager.create_tenant_resource(data, MenuItem)
            db.session.add(item)
            db.session.commit()
            
            self.assertEqual(item.tenant_id, self.tenant1.id)
    
    def test_tenant_scoped_query_helper(self):
        """Test tenant-scoped query helper"""
        with self.app.test_request_context():
            # Set tenant context
            g.tenant_id = self.tenant1.id
            
            # Test scoped query
            query = tenant_scoped(User)
            users = query.all()
            
            self.assertEqual(len(users), 2)
            for user in users:
                self.assertEqual(user.tenant_id, self.tenant1.id)
            
            # Test additional filtering
            admin_users = query.filter_by(is_tenant_admin=True).all()
            self.assertEqual(len(admin_users), 1)
            self.assertTrue(admin_users[0].is_tenant_admin)


class TenantMiddlewareTests(MultiTenancyTestCase):
    """Test tenant identification middleware"""
    
    def test_subdomain_identification(self):
        """Test tenant identification from subdomain"""
        with self.app.test_request_context(headers={'Host': 'restaurant1.localhost'}):
            middleware = TenantMiddleware(self.app)
            tenant_id = middleware._identify_tenant_from_subdomain()
            self.assertEqual(tenant_id, self.tenant1.id)
    
    def test_header_identification(self):
        """Test tenant identification from header"""
        with self.app.test_request_context(headers={'X-Tenant-ID': str(self.tenant1.id)}):
            middleware = TenantMiddleware(self.app)
            tenant_id = middleware._identify_tenant_from_header()
            self.assertEqual(tenant_id, self.tenant1.id)
    
    def test_path_identification(self):
        """Test tenant identification from path"""
        with self.app.test_request_context('/t/restaurant1/dashboard'):
            middleware = TenantMiddleware(self.app)
            tenant_id = middleware._identify_tenant_from_path()
            self.assertEqual(tenant_id, self.tenant1.id)
    
    def test_tenant_context_management(self):
        """Test tenant context management"""
        with self.app.test_request_context():
            # Test setting context
            TenantContext.set_tenant_context(self.tenant1.id)
            self.assertEqual(TenantContext.get_current_tenant_id(), self.tenant1.id)
            self.assertEqual(TenantContext.get_current_tenant().id, self.tenant1.id)
            
            # Test clearing context
            TenantContext.clear_tenant_context()
            self.assertIsNone(TenantContext.get_current_tenant_id())
            self.assertIsNone(TenantContext.get_current_tenant())


class TenantIsolationTests(MultiTenancyTestCase):
    """Test tenant data isolation"""
    
    def test_menu_item_isolation(self):
        """Test menu item isolation between tenants"""
        with self.app.test_request_context():
            # Tenant 1 context
            g.tenant_id = self.tenant1.id
            tenant1_items = MenuItem.query.filter_by(tenant_id=self.tenant1.id).all()
            self.assertEqual(len(tenant1_items), 1)
            self.assertEqual(tenant1_items[0].name, 'Burger')
            
            # Tenant 2 context
            g.tenant_id = self.tenant2.id
            tenant2_items = MenuItem.query.filter_by(tenant_id=self.tenant2.id).all()
            self.assertEqual(len(tenant2_items), 1)
            self.assertEqual(tenant2_items[0].name, 'Pizza')
    
    def test_order_isolation(self):
        """Test order isolation between tenants"""
        with self.app.test_request_context():
            # Tenant 1 context
            g.tenant_id = self.tenant1.id
            tenant1_orders = Order.query.filter_by(tenant_id=self.tenant1.id).all()
            self.assertEqual(len(tenant1_orders), 1)
            self.assertEqual(tenant1_orders[0].order_number, 'ORD001')
            
            # Tenant 2 context
            g.tenant_id = self.tenant2.id
            tenant2_orders = Order.query.filter_by(tenant_id=self.tenant2.id).all()
            self.assertEqual(len(tenant2_orders), 1)
            self.assertEqual(tenant2_orders[0].order_number, 'ORD002')
    
    def test_cross_tenant_access_prevention(self):
        """Test prevention of cross-tenant data access"""
        with self.app.test_request_context():
            # Set tenant 1 context
            g.tenant_id = self.tenant1.id
            
            # Try to access tenant 2 data
            tenant2_item = MenuItem.query.filter_by(
                id=self.tenant2_item.id,
                tenant_id=self.tenant2.id
            ).first()
            
            # Should not find the item when in tenant 1 context
            self.assertIsNone(tenant2_item)
            
            # But should find it when explicitly querying for tenant 2
            tenant2_item_explicit = MenuItem.query.filter_by(
                id=self.tenant2_item.id,
                tenant_id=self.tenant2.id
            ).first()
            self.assertIsNotNone(tenant2_item_explicit)


class TenantFeatureTests(MultiTenancyTestCase):
    """Test tenant feature management"""
    
    def test_feature_flag_creation(self):
        """Test feature flag creation and management"""
        feature = TenantFeatureFlag(
            tenant_id=self.tenant1.id,
            feature_name='custom_theme',
            is_enabled=True,
            settings=json.dumps({'theme_color': '#ff0000'})
        )
        
        db.session.add(feature)
        db.session.commit()
        
        retrieved_feature = TenantFeatureFlag.query.filter_by(
            tenant_id=self.tenant1.id,
            feature_name='custom_theme'
        ).first()
        
        self.assertIsNotNone(retrieved_feature)
        self.assertTrue(retrieved_feature.is_enabled)
        self.assertEqual(json.loads(retrieved_feature.settings)['theme_color'], '#ff0000')
    
    def test_subscription_feature_access(self):
        """Test feature access based on subscription"""
        # Test basic plan features
        self.assertTrue(self.tenant1.has_feature('basic_reporting'))
        self.assertFalse(self.tenant1.has_feature('crm'))
        
        # Test premium plan features
        self.assertTrue(self.tenant2.has_feature('advanced_reporting'))
        self.assertTrue(self.tenant2.has_feature('crm'))
        self.assertTrue(self.tenant2.has_feature('loyalty'))


class TenantUsageTests(MultiTenancyTestCase):
    """Test tenant usage tracking"""
    
    def test_usage_tracking(self):
        """Test usage tracking functionality"""
        usage = TenantUsage(
            tenant_id=self.tenant1.id,
            usage_date=datetime.utcnow().date(),
            api_calls=100,
            orders_count=5,
            active_users=3
        )
        
        db.session.add(usage)
        db.session.commit()
        
        retrieved_usage = TenantUsage.query.filter_by(
            tenant_id=self.tenant1.id
        ).first()
        
        self.assertIsNotNone(retrieved_usage)
        self.assertEqual(retrieved_usage.api_calls, 100)
        self.assertEqual(retrieved_usage.orders_count, 5)
        self.assertEqual(retrieved_usage.active_users, 3)


class TenantAPITests(MultiTenancyTestCase):
    """Test tenant API endpoints"""
    
    def test_tenant_list_api(self):
        """Test tenant list API endpoint"""
        # Login as super admin (create one first)
        super_admin = User(
            username='superadmin',
            email='super@admin.com',
            first_name='Super',
            last_name='Admin',
            is_super_admin=True,
            is_active=True
        )
        super_admin.set_password('password123')
        db.session.add(super_admin)
        db.session.commit()
        
        # Test API endpoint
        response = self.client.get('/tenant/api/tenants')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and test again
        self.client.post('/auth/login', data={
            'username': 'superadmin',
            'password': 'password123'
        })
        
        response = self.client.get('/tenant/api/tenants')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['tenants']), 2)
    
    def test_current_tenant_api(self):
        """Test current tenant API endpoint"""
        with self.app.test_request_context(headers={'X-Tenant-ID': str(self.tenant1.id)}):
            # Set tenant context
            g.tenant_id = self.tenant1.id
            g.tenant = self.tenant1
            
            response = self.client.get('/tenant/api/current')
            self.assertEqual(response.status_code, 302)  # Redirect to login


class MigrationTests(MultiTenancyTestCase):
    """Test migration functionality"""
    
    def test_default_tenant_creation(self):
        """Test default tenant creation during migration"""
        # This would be tested during actual migration process
        # For now, just verify the structure exists
        self.assertIsNotNone(self.tenant1)
        self.assertIsNotNone(self.tenant1_settings)
        self.assertIsNotNone(self.tenant1_subscription)
    
    def test_data_integrity_after_migration(self):
        """Test data integrity after migration to multi-tenant"""
        # Verify all data has proper tenant_id
        users = User.query.all()
        for user in users:
            self.assertIsNotNone(user.tenant_id)
        
        menu_items = MenuItem.query.all()
        for item in menu_items:
            self.assertIsNotNone(item.tenant_id)
        
        orders = Order.query.all()
        for order in orders:
            self.assertIsNotNone(order.tenant_id)


if __name__ == '__main__':
    # Run the test suite
    unittest.main(verbosity=2)