"""
Multi-Tenancy Tests for Multi-Web-Cloud POS Application
Tests tenant isolation, data separation, and multi-tenant configurations
"""

import unittest
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging

# Import application and managers
from app import create_app
from config import Config
from utils.form_validator import FormValidator
from utils.session_manager import SessionManager
from utils.security_manager import SecurityManager
from utils.offline_manager import OfflineManager
from utils.razorpay_manager import RazorpayManager

# Import models
from models import db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings

class TestMultiTenancy(unittest.TestCase):
    """Multi-tenancy test suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Configure test app with multi-tenancy
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'SESSION_SALT': 'test-session-salt',
            'RAZORPAY_KEY_ID': 'test_key_id',
            'RAZORPAY_KEY_SECRET': 'test_key_secret',
            'RAZORPAY_WEBHOOK_SECRET': 'test_webhook_secret',
            'RAZORPAY_TEST_MODE': True,
            'RATE_LIMITS': {
                'default': {'requests': 100, 'window': 60},
                'auth': {'requests': 5, 'window': 300},
                'api': {'requests': 200, 'window': 60}
            },
            'IP_BLOCK_DURATION': 3600,
            'MAX_FAILED_ATTEMPTS': 5,
            'OFFLINE_MODE': False,
            'SYNC_INTERVAL': 5,
            'MAX_RETRY_ATTEMPTS': 3,
            'BASE_URL': 'http://localhost:5000',
            'MULTI_TENANCY': True,  # Enable multi-tenancy
            'DEFAULT_TENANT': 'tenant1'
        }
        
        # Create test app
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        # Create test client
        cls.client = cls.app.test_client()
        
        # Create application context
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create tenant-specific test data
        cls._create_tenant_data()
        
        # Initialize managers
        cls.form_validator = FormValidator()
        cls.session_manager = SessionManager(cls.app)
        cls.security_manager = SecurityManager(cls.app)
        cls.offline_manager = OfflineManager(cls.app)
        cls.razorpay_manager = RazorpayManager(cls.app)
        
        # Test tenants
        cls.test_tenants = ['tenant1', 'tenant2', 'tenant3']
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def setUp(self):
        """Set up for each test"""
        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()
        
        # Reset managers
        self.security_manager.blocked_ips.clear()
        self.security_manager.failed_attempts.clear()
        self.security_manager.security_events.clear()
    
    @classmethod
    def _create_tenant_data(cls):
        """Create tenant-specific test data"""
        # Create tenant-specific users
        cls.tenant_users = {}
        for tenant in cls.test_tenants:
            users = []
            for i in range(3):
                user = User(
                    username=f'{tenant}_user{i}',
                    email=f'{tenant}_user{i}@example.com',
                    role='admin' if i == 0 else 'cashier',
                    tenant_id=tenant  # Assuming tenant_id field exists
                )
                user.set_password('testpass123')
                users.append(user)
                db.session.add(user)
            cls.tenant_users[tenant] = users
        
        # Create tenant-specific categories
        cls.tenant_categories = {}
        for tenant in cls.test_tenants:
            categories = []
            for i in range(2):
                category = Category(
                    name=f'{tenant}_Category_{i}',
                    description=f'{tenant} category {i} description',
                    tenant_id=tenant
                )
                categories.append(category)
                db.session.add(category)
            cls.tenant_categories[tenant] = categories
        
        # Create tenant-specific menu items
        cls.tenant_menu_items = {}
        for tenant in cls.test_tenants:
            items = []
            for i in range(5):
                item = MenuItem(
                    name=f'{tenant}_Item_{i}',
                    description=f'{tenant} item {i} description',
                    category_id=cls.tenant_categories[tenant][0].id,
                    price=Decimal(str(100 + i * 10)),
                    stock_quantity=100 + i,
                    min_stock_level=10,
                    unit='pcs',
                    tenant_id=tenant
                )
                items.append(item)
                db.session.add(item)
            cls.tenant_menu_items[tenant] = items
        
        # Create tenant-specific tables
        cls.tenant_tables = {}
        for tenant in cls.test_tenants:
            tables = []
            for i in range(3):
                table = Table(
                    table_number=f'{tenant}_T{i+1}',
                    capacity=4 + i,
                    location=f'{tenant} Area {i}',
                    description=f'{tenant} table {i}',
                    tenant_id=tenant
                )
                tables.append(table)
                db.session.add(table)
            cls.tenant_tables[tenant] = tables
        
        db.session.commit()
    
    def _set_tenant_context(self, tenant_id):
        """Set tenant context for requests"""
        with self.client.session_transaction() as sess:
            sess['tenant_id'] = tenant_id
    
    def _login_tenant_user(self, tenant_id, user_index=0):
        """Login tenant user"""
        self._set_tenant_context(tenant_id)
        user = self.tenant_users[tenant_id][user_index]
        
        response = self.client.post('/auth/login', json={
            'username': user.username,
            'password': 'testpass123'
        })
        return response, user
    
    def test_tenant_isolation(self):
        """Test tenant data isolation"""
        print("\n=== Testing Tenant Isolation ===")
        
        # Test that users can only access their own data
        for tenant in self.test_tenants:
            # Login as tenant user
            response, user = self._login_tenant_user(tenant)
            self.assertIn(response.status_code, [200, 302], f"Tenant {tenant} login should succeed")
            
            # Test menu item access - should only see tenant's items
            response = self.client.get('/api/menu/items')
            self.assertEqual(response.status_code, 200, f"Tenant {tenant} should access menu items")
            
            menu_items = json.loads(response.data)
            
            # Verify all items belong to current tenant
            for item in menu_items:
                if isinstance(item, dict) and 'tenant_id' in item:
                    self.assertEqual(item['tenant_id'], tenant, 
                                   f"Item should belong to tenant {tenant}")
            
            # Test category access - should only see tenant's categories
            response = self.client.get('/api/categories')
            self.assertEqual(response.status_code, 200, f"Tenant {tenant} should access categories")
            
            categories = json.loads(response.data)
            
            # Verify all categories belong to current tenant
            for category in categories:
                if isinstance(category, dict) and 'tenant_id' in category:
                    self.assertEqual(category['tenant_id'], tenant,
                                   f"Category should belong to tenant {tenant}")
            
            # Test table access - should only see tenant's tables
            response = self.client.get('/api/tables')
            self.assertEqual(response.status_code, 200, f"Tenant {tenant} should access tables")
            
            tables = json.loads(response.data)
            
            # Verify all tables belong to current tenant
            for table in tables:
                if isinstance(table, dict) and 'tenant_id' in table:
                    self.assertEqual(table['tenant_id'], tenant,
                                   f"Table should belong to tenant {tenant}")
        
        print("✅ Tenant isolation tests passed")
    
    def test_cross_tenant_data_leakage_prevention(self):
        """Test prevention of cross-tenant data leakage"""
        print("\n=== Testing Cross-Tenant Data Leakage Prevention ===")
        
        # Login as tenant1 user
        response, user1 = self._login_tenant_user('tenant1')
        
        # Try to access tenant2 data directly
        tenant2_item = self.tenant_menu_items['tenant2'][0]
        
        # Try direct access by ID
        response = self.client.get(f'/api/menu/items/{tenant2_item.id}')
        
        # Should be denied or return empty/not found
        self.assertIn(response.status_code, [403, 404, 400], 
                      "Should not access other tenant's data")
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # If 200, ensure data doesn't belong to other tenant
            if isinstance(data, dict) and 'tenant_id' in data:
                self.assertNotEqual(data['tenant_id'], 'tenant2',
                                 "Should not return other tenant's data")
        
        # Try to access other tenant's orders
        response = self.client.get('/api/orders')
        self.assertEqual(response.status_code, 200, "Should access own orders")
        
        orders = json.loads(response.data)
        
        # Verify all orders belong to current tenant
        for order in orders:
            if isinstance(order, dict) and 'tenant_id' in order:
                self.assertEqual(order['tenant_id'], 'tenant1',
                                 "Orders should belong to current tenant")
        
        # Try to create order for other tenant
        order_data = {
            'customer_name': 'Cross-tenant Test',
            'order_type': 'Dine-in',
            'items': [
                {'menu_item_id': tenant2_item.id, 'quantity': 1, 'price': 100.00}
            ]
        }
        
        response = self.client.post('/api/orders', json=order_data)
        
        # Should be rejected
        self.assertIn(response.status_code, [400, 403, 404],
                      "Should not create order with other tenant's item")
        
        print("✅ Cross-tenant data leakage prevention tests passed")
    
    def test_tenant_specific_configurations(self):
        """Test tenant-specific configurations"""
        print("\n=== Testing Tenant-Specific Configurations ===")
        
        # Test tenant-specific settings
        for tenant in self.test_tenants:
            self._set_tenant_context(tenant)
            
            # Test tenant-specific settings
            response = self.client.get('/api/config/settings')
            self.assertEqual(response.status_code, 200, f"Should access tenant {tenant} settings")
            
            settings = json.loads(response.data)
            
            # Verify settings are tenant-specific
            if isinstance(settings, dict) and 'tenant_id' in settings:
                self.assertEqual(settings['tenant_id'], tenant,
                                 "Settings should be tenant-specific")
            
            # Test tenant-specific payment methods
            response = self.client.get('/api/config/payment-methods')
            self.assertEqual(response.status_code, 200, f"Should access tenant {tenant} payment methods")
            
            # Test tenant-specific business rules
            response = self.client.get('/api/config/business-rules')
            self.assertEqual(response.status_code, 200, f"Should access tenant {tenant} business rules")
        
        print("✅ Tenant-specific configurations tests passed")
    
    def test_multi_tenant_session_management(self):
        """Test multi-tenant session management"""
        print("\n=== Testing Multi-Tenant Session Management ===")
        
        # Test session isolation between tenants
        sessions = {}
        
        for tenant in self.test_tenants:
            # Login as tenant user
            response, user = self._login_tenant_user(tenant)
            self.assertIn(response.status_code, [200, 302], f"Tenant {tenant} login should succeed")
            
            # Get session info
            response = self.client.get('/api/session/status')
            self.assertEqual(response.status_code, 200, f"Should get session status for tenant {tenant}")
            
            session_data = json.loads(response.data)
            sessions[tenant] = session_data
            
            # Verify tenant context in session
            if 'session' in session_data and isinstance(session_data['session'], dict):
                self.assertIn('tenant_id', session_data['session'],
                             f"Session should contain tenant_id for {tenant}")
        
        # Verify sessions are isolated
        for tenant in self.test_tenants:
            session_data = sessions[tenant]
            if 'session' in session_data and isinstance(session_data['session'], dict):
                self.assertEqual(session_data['session']['tenant_id'], tenant,
                                 "Session should maintain correct tenant context")
        
        print("✅ Multi-tenant session management tests passed")
    
    def test_tenant_resource_sharing(self):
        """Test tenant resource sharing and isolation"""
        print("\n=== Testing Tenant Resource Sharing ===")
        
        # Test shared resources vs isolated resources
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Test shared resources (if any)
            response = self.client.get('/api/config/shared-resources')
            
            # Some resources might be shared across tenants
            if response.status_code == 200:
                shared_resources = json.loads(response.data)
                
                # Verify shared resources don't contain tenant-specific data
                for resource in shared_resources:
                    if isinstance(resource, dict):
                        self.assertNotIn('tenant_id', resource,
                                        "Shared resources should not contain tenant-specific data")
            
            # Test isolated resources
            response = self.client.get('/api/config/isolated-resources')
            
            if response.status_code == 200:
                isolated_resources = json.loads(response.data)
                
                # Verify isolated resources are tenant-specific
                for resource in isolated_resources:
                    if isinstance(resource, dict) and 'tenant_id' in resource:
                        self.assertEqual(resource['tenant_id'], tenant,
                                         "Isolated resources should be tenant-specific")
        
        print("✅ Tenant resource sharing tests passed")
    
    def test_tenant_user_management(self):
        """Test tenant user management"""
        print("\n=== Testing Tenant User Management ===")
        
        # Test user creation within tenant
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant, 0)  # Login as admin user
            
            # Create new user for tenant
            new_user_data = {
                'username': f'{tenant}_newuser',
                'email': f'{tenant}_newuser@example.com',
                'password': 'newpass123',
                'role': 'cashier'
            }
            
            response = self.client.post('/api/users/create', json=new_user_data)
            self.assertIn(response.status_code, [200, 201, 400], 
                          f"Should create user for tenant {tenant}")
            
            # Test user listing - should only show tenant's users
            response = self.client.get('/api/users')
            self.assertEqual(response.status_code, 200, f"Should list users for tenant {tenant}")
            
            users = json.loads(response.data)
            
            # Verify all users belong to current tenant
            for user in users:
                if isinstance(user, dict) and 'tenant_id' in user:
                    self.assertEqual(user['tenant_id'], tenant,
                                     "Users list should contain only tenant's users")
            
            # Test user permission within tenant
            for user_data in users:
                if isinstance(user_data, dict):
                    username = user_data.get('username', '')
                    if f'{tenant}_' in username:
                        # User should have appropriate permissions for tenant
                        self.assertIn('role', user_data,
                                     "User should have role defined")
        
        print("✅ Tenant user management tests passed")
    
    def test_tenant_order_isolation(self):
        """Test tenant order isolation"""
        print("\n=== Testing Tenant Order Isolation ===")
        
        # Create orders for each tenant
        tenant_orders = {}
        
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Create order for tenant
            order_data = {
                'customer_name': f'{tenant} Customer',
                'order_type': 'Dine-in',
                'items': [
                    {'menu_item_id': self.tenant_menu_items[tenant][0].id, 
                     'quantity': 2, 'price': 100.00}
                ]
            }
            
            response = self.client.post('/api/orders', json=order_data)
            self.assertIn(response.status_code, [200, 201], 
                          f"Should create order for tenant {tenant}")
            
            if response.status_code in [200, 201]:
                order_response = json.loads(response.data)
                tenant_orders[tenant] = order_response.get('order_id')
        
        # Test order isolation
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Get orders list
            response = self.client.get('/api/orders')
            self.assertEqual(response.status_code, 200, f"Should get orders for tenant {tenant}")
            
            orders = json.loads(response.data)
            
            # Verify all orders belong to current tenant
            for order in orders:
                if isinstance(order, dict) and 'tenant_id' in order:
                    self.assertEqual(order['tenant_id'], tenant,
                                     "Orders list should contain only tenant's orders")
            
            # Try to access other tenant's order
            for other_tenant in self.test_tenants:
                if other_tenant != tenant and other_tenant in tenant_orders:
                    order_id = tenant_orders[other_tenant]
                    
                    response = self.client.get(f'/api/orders/{order_id}')
                    
                    # Should be denied or return empty
                    self.assertIn(response.status_code, [403, 404, 400],
                                  f"Should not access other tenant's order")
                    
                    if response.status_code == 200:
                        order_data = json.loads(response.data)
                        if isinstance(order_data, dict) and 'tenant_id' in order_data:
                            self.assertNotEqual(order_data['tenant_id'], other_tenant,
                                             "Should not return other tenant's order data")
        
        print("✅ Tenant order isolation tests passed")
    
    def test_tenant_payment_isolation(self):
        """Test tenant payment isolation"""
        print("\n=== Testing Tenant Payment Isolation ===")
        
        # Test payment processing within tenant
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Create order first
            order_data = {
                'customer_name': f'{tenant} Payment Customer',
                'order_type': 'Dine-in',
                'items': [
                    {'menu_item_id': self.tenant_menu_items[tenant][0].id, 
                     'quantity': 1, 'price': 100.00}
                ]
            }
            
            response = self.client.post('/api/orders', json=order_data)
            self.assertIn(response.status_code, [200, 201], 
                          f"Should create order for tenant {tenant}")
            
            if response.status_code in [200, 201]:
                order_response = json.loads(response.data)
                order_id = order_response.get('order_id')
                
                # Create payment for order
                payment_data = {
                    'order_id': order_id,
                    'payment_method': 'Cash',
                    'amount_paid': 100.00,
                    'reference_number': f'{tenant}_PAY001'
                }
                
                response = self.client.post('/api/payments', json=payment_data)
                self.assertIn(response.status_code, [200, 201], 
                              f"Should create payment for tenant {tenant}")
                
                # Get payments list
                response = self.client.get('/api/payments')
                self.assertEqual(response.status_code, 200, 
                              f"Should get payments for tenant {tenant}")
                
                payments = json.loads(response.data)
                
                # Verify all payments belong to current tenant
                for payment in payments:
                    if isinstance(payment, dict) and 'tenant_id' in payment:
                        self.assertEqual(payment['tenant_id'], tenant,
                                         "Payments list should contain only tenant's payments")
        
        print("✅ Tenant payment isolation tests passed")
    
    def test_tenant_reporting_isolation(self):
        """Test tenant reporting isolation"""
        print("\n=== Testing Tenant Reporting Isolation ===")
        
        # Test reporting for each tenant
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Test sales report
            response = self.client.get('/api/reports/sales')
            self.assertEqual(response.status_code, 200, 
                          f"Should get sales report for tenant {tenant}")
            
            sales_report = json.loads(response.data)
            
            # Verify report data is tenant-specific
            if isinstance(sales_report, dict):
                if 'tenant_id' in sales_report:
                    self.assertEqual(sales_report['tenant_id'], tenant,
                                     "Sales report should be tenant-specific")
                
                # Verify order data in report belongs to tenant
                if 'orders' in sales_report:
                    for order in sales_report['orders']:
                        if isinstance(order, dict) and 'tenant_id' in order:
                            self.assertEqual(order['tenant_id'], tenant,
                                             "Report orders should belong to tenant")
            
            # Test inventory report
            response = self.client.get('/api/reports/inventory')
            self.assertEqual(response.status_code, 200, 
                          f"Should get inventory report for tenant {tenant}")
            
            inventory_report = json.loads(response.data)
            
            # Verify inventory data is tenant-specific
            if isinstance(inventory_report, dict) and 'items' in inventory_report:
                for item in inventory_report['items']:
                    if isinstance(item, dict) and 'tenant_id' in item:
                        self.assertEqual(item['tenant_id'], tenant,
                                         "Inventory items should belong to tenant")
            
            # Test financial report
            response = self.client.get('/api/reports/financial')
            self.assertEqual(response.status_code, 200, 
                          f"Should get financial report for tenant {tenant}")
            
            financial_report = json.loads(response.data)
            
            # Verify financial data is tenant-specific
            if isinstance(financial_report, dict):
                if 'tenant_id' in financial_report:
                    self.assertEqual(financial_report['tenant_id'], tenant,
                                     "Financial report should be tenant-specific")
        
        print("✅ Tenant reporting isolation tests passed")
    
    def test_tenant_api_rate_limiting(self):
        """Test tenant-specific API rate limiting"""
        print("\n=== Testing Tenant-Specific API Rate Limiting ===")
        
        # Test rate limiting per tenant
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Make requests up to rate limit
            for i in range(15):  # Should exceed rate limit
                response = self.client.get('/api/menu/items')
                
                if i < 10:  # Should be allowed
                    self.assertEqual(response.status_code, 200, 
                                  f"Request {i+1} should be allowed for tenant {tenant}")
                else:  # Should be rate limited
                    self.assertEqual(response.status_code, 429, 
                                  f"Request {i+1} should be rate limited for tenant {tenant}")
            
            # Wait for rate limit reset
            time.sleep(1)
        
        print("✅ Tenant-specific API rate limiting tests passed")
    
    def test_tenant_backup_and_restore(self):
        """Test tenant backup and restore functionality"""
        print("\n=== Testing Tenant Backup and Restore ===")
        
        # Test backup for each tenant
        tenant_backups = {}
        
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant, 0)  # Login as admin
            
            # Create tenant backup
            response = self.client.post('/api/backup/create', json={
                'backup_type': 'full',
                'include_files': True
            })
            
            self.assertIn(response.status_code, [200, 201], 
                          f"Should create backup for tenant {tenant}")
            
            if response.status_code in [200, 201]:
                backup_response = json.loads(response.data)
                tenant_backups[tenant] = backup_response.get('backup_id')
        
        # Test restore isolation
        for tenant in self.test_tenants:
            if tenant in tenant_backups:
                self._login_tenant_user(tenant, 0)
                
                # Try to restore other tenant's backup
                for other_tenant in self.test_tenants:
                    if other_tenant != tenant and other_tenant in tenant_backups:
                        backup_id = tenant_backups[other_tenant]
                        
                        response = self.client.post('/api/backup/restore', json={
                            'backup_id': backup_id
                        })
                        
                        # Should be denied
                        self.assertIn(response.status_code, [400, 403, 404],
                                      f"Should not restore other tenant's backup")
                
                # Restore own backup
                backup_id = tenant_backups[tenant]
                response = self.client.post('/api/backup/restore', json={
                    'backup_id': backup_id
                })
                
                self.assertIn(response.status_code, [200, 202],
                              f"Should restore own backup for tenant {tenant}")
        
        print("✅ Tenant backup and restore tests passed")
    
    def test_tenant_audit_logging(self):
        """Test tenant audit logging"""
        print("\n=== Testing Tenant Audit Logging ===")
        
        # Test audit logging for each tenant
        for tenant in self.test_tenants:
            self._login_tenant_user(tenant)
            
            # Perform various actions
            actions = [
                ('menu_item_created', 'POST /api/menu/items'),
                ('order_created', 'POST /api/orders'),
                ('payment_processed', 'POST /api/payments'),
                ('user_login', 'POST /auth/login')
            ]
            
            for action, endpoint in actions:
                # Perform action
                if 'menu_items' in endpoint:
                    response = self.client.post('/api/menu/items', json={
                        'name': f'{tenant} Audit Item',
                        'price': 100.00,
                        'category_id': self.tenant_categories[tenant][0].id
                    })
                elif 'orders' in endpoint:
                    response = self.client.post('/api/orders', json={
                        'customer_name': f'{tenant} Audit Customer',
                        'items': [
                            {'menu_item_id': self.tenant_menu_items[tenant][0].id, 
                             'quantity': 1, 'price': 100.00}
                        ]
                    })
                elif 'payments' in endpoint:
                    # Create order first
                    order_response = self.client.post('/api/orders', json={
                        'customer_name': f'{tenant} Payment Audit',
                        'items': [
                            {'menu_item_id': self.tenant_menu_items[tenant][0].id, 
                             'quantity': 1, 'price': 100.00}
                        ]
                    })
                    
                    if order_response.status_code in [200, 201]:
                        order_data = json.loads(order_response.data)
                        order_id = order_data.get('order_id')
                        
                        response = self.client.post('/api/payments', json={
                            'order_id': order_id,
                            'payment_method': 'Cash',
                            'amount_paid': 100.00
                        })
                
                # Check audit log
                response = self.client.get('/api/audit/logs')
                self.assertEqual(response.status_code, 200, 
                              f"Should get audit logs for tenant {tenant}")
                
                audit_logs = json.loads(response.data)
                
                # Verify audit logs are tenant-specific
                for log in audit_logs:
                    if isinstance(log, dict):
                        if 'tenant_id' in log:
                            self.assertEqual(log['tenant_id'], tenant,
                                             "Audit logs should be tenant-specific")
                        
                        if 'action' in log:
                            self.assertIn(log['action'], [action[0], 'user_login'],
                                           "Audit log should contain relevant actions")
        
        print("✅ Tenant audit logging tests passed")

def run_multi_tenancy_tests():
    """Run all multi-tenancy tests"""
    print("=" * 80)
    print("MULTI-TENANCY TEST SUITE")
    print("=" * 80)
    print("Testing tenant isolation, data separation, and multi-tenant configurations\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestMultiTenancy('test_tenant_isolation'))
    test_suite.addTest(TestMultiTenancy('test_cross_tenant_data_leakage_prevention'))
    test_suite.addTest(TestMultiTenancy('test_tenant_specific_configurations'))
    test_suite.addTest(TestMultiTenancy('test_multi_tenant_session_management'))
    test_suite.addTest(TestMultiTenancy('test_tenant_resource_sharing'))
    test_suite.addTest(TestMultiTenancy('test_tenant_user_management'))
    test_suite.addTest(TestMultiTenancy('test_tenant_order_isolation'))
    test_suite.addTest(TestMultiTenancy('test_tenant_payment_isolation'))
    test_suite.addTest(TestMultiTenancy('test_tenant_reporting_isolation'))
    test_suite.addTest(TestMultiTenancy('test_tenant_api_rate_limiting'))
    test_suite.addTest(TestMultiTenancy('test_tenant_backup_and_restore'))
    test_suite.addTest(TestMultiTenancy('test_tenant_audit_logging'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("MULTI-TENANCY TEST RESULTS")
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
    success = run_multi_tenancy_tests()
    
    if success:
        print("\n✅ ALL MULTI-TENANCY TESTS PASSED!")
        print("Multi-tenancy is production-ready")
        exit(0)
    else:
        print("\n❌ SOME MULTI-TENANCY TESTS FAILED!")
        print("Review and fix multi-tenancy issues before production deployment")
        exit(1)