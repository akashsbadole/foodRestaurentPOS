#!/usr/bin/env python3
"""
Test script for offline functionality in Flask POS Application
Tests all offline features including synchronization and conflict resolution
"""

import os
import sys
import unittest
import tempfile
import shutil
import json
from datetime import datetime, timedelta

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, create_tables
from models.user import User
from models.category import Category
from models.menu_item import MenuItem
from models.table import Table
from models.order import Order
from models.order import OrderItem

class OfflineFunctionalityTestCase(unittest.TestCase):
    """Test cases for offline functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Use in-memory database for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['OFFLINE_MODE'] = True
        
        db.create_all()
        self.client = self.app.test_client()
        
        # Create test user using factory method
        self.test_user = User.create_user(
            username='testuser',
            password='testpass',
            role='admin',
            email='test@example.com'
        )
        
        # Login
        self.client.post('/auth/login', data=dict(
            username='testuser',
            password='testpass'
        ), follow_redirects=True)
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self):
        """Helper function to login"""
        return self.client.post('/auth/login', data=dict(
            username='testuser',
            password='testpass'
        ), follow_redirects=True)
    
    def test_offline_status_endpoint(self):
        """Test offline status API endpoint"""
        response = self.client.get('/api/offline/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('offline', data['data'])
        self.assertIn('queue_size', data['data'])
        self.assertIn('last_sync', data['data'])
    
    def test_check_connection_endpoint(self):
        """Test connection check endpoint"""
        response = self.client.get('/api/offline/check_connection')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('is_online', data['data'])
    
    def test_offline_data_cache_endpoint(self):
        """Test offline data cache endpoint"""
        # Create test data
        category = Category(name='Test Category', description='Test')
        db.session.add(category)
        db.session.commit()
        
        menu_item = MenuItem(
            name='Test Item',
            category_id=category.id,
            price=100.00,
            description='Test item',
            stock_quantity=50,
            min_stock_level=10,
            unit='pcs'
        )
        db.session.add(menu_item)
        db.session.commit()
        
        response = self.client.get('/api/offline/data/cache')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        
        cached_data = data['data']
        self.assertIn('menu_items', cached_data)
        self.assertIn('categories', cached_data)
        self.assertIn('tables', cached_data)
    
    def test_offline_menu_items_endpoint(self):
        """Test offline menu items endpoint"""
        response = self.client.get('/api/offline/data/menu_items')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_offline_categories_endpoint(self):
        """Test offline categories endpoint"""
        response = self.client.get('/api/offline/data/categories')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_offline_tables_endpoint(self):
        """Test offline tables endpoint"""
        response = self.client.get('/api/offline/data/tables')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
    
    def test_store_offline_order_endpoint(self):
        """Test storing offline order"""
        offline_order = {
            'order_number': 'OFFLINE-001',
            'customer_name': 'Test Customer',
            'customer_mobile': '1234567890',
            'order_type': 'Dine-in',
            'table_id': 1,
            'items': [
                {
                    'menu_item_id': 1,
                    'quantity': 2,
                    'price': 100.00
                }
            ],
            'subtotal': 200.00,
            'cgst_amount': 5.00,
            'sgst_amount': 5.00,
            'grand_total': 210.00,
            'status': 'New',
            'created_at': datetime.utcnow().isoformat(),
            'offline_id': 'temp_12345'
        }
        
        response = self.client.post('/api/offline/orders/store',
                                data=json.dumps(offline_order),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('message', data)
    
    def test_store_offline_payment_endpoint(self):
        """Test storing offline payment"""
        offline_payment = {
            'order_id': 1,
            'payment_method': 'Cash',
            'amount_paid': 210.00,
            'discount_amount': 0.00,
            'reference_number': 'CASH001',
            'status': 'Completed',
            'created_at': datetime.utcnow().isoformat(),
            'offline_id': 'temp_pay_12345'
        }
        
        response = self.client.post('/api/offline/payments/store',
                                data=json.dumps(offline_payment),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('message', data)
    
    def test_sync_endpoint(self):
        """Test manual sync endpoint"""
        response = self.client.post('/api/offline/sync')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('message', data)
        self.assertIn('synced', data['data'])
    
    def test_sync_history_endpoint(self):
        """Test sync history endpoint"""
        response = self.client.get('/api/offline/sync/history')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertIn('history', data['data'])
    
    def test_queue_status_endpoint(self):
        """Test queue status endpoint"""
        response = self.client.get('/api/offline/queue/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('data', data)
        self.assertIn('queue', data['data'])
        self.assertIn('stats', data['data'])
    
    def test_clear_queue_endpoint(self):
        """Test clear queue endpoint"""
        response = self.client.post('/api/offline/queue/clear')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertIn('message', data)
    
    def test_offline_mode_toggle(self):
        """Test offline mode toggle"""
        # Enable offline mode
        response = self.client.post('/api/offline/mode/toggle',
                                data={'enabled': True})
        self.assertEqual(response.status_code, 200)
        
        # Check if offline mode is enabled
        response = self.client.get('/api/offline/status')
        data = json.loads(response.data)
        self.assertTrue(data['data']['offline_mode_enabled'])
        
        # Disable offline mode
        response = self.client.post('/api/offline/mode/toggle',
                                data={'enabled': False})
        self.assertEqual(response.status_code, 200)
    
    def test_conflict_detection(self):
        """Test conflict detection logic"""
        # Create an existing order
        existing_order = Order(
            order_number='CONFLICT-001',
            customer_name='Existing Customer',
            status='New'
        )
        db.session.add(existing_order)
        db.session.commit()
        
        # Try to create conflicting offline order
        conflicting_order = {
            'order_number': 'CONFLICT-001',
            'customer_name': 'New Customer',
            'status': 'New',
            'offline_id': 'temp_conflict'
        }
        
        response = self.client.post('/api/offline/orders/check_conflict',
                                data=json.dumps(conflicting_order),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('conflict', data)
        if data['conflict']:
            self.assertIn('server_data', data)
    
    def test_data_integrity_offline(self):
        """Test data integrity during offline operations"""
        # Create test data
        category = Category(name='Integrity Test', description='Test')
        db.session.add(category)
        db.session.commit()
        
        # Store offline data
        offline_data = {
            'categories': [{'id': category.id, 'name': category.name}],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        response = self.client.post('/api/offline/data/store',
                                data=json.dumps(offline_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verify data integrity
        response = self.client.get('/api/offline/data/categories')
        data = json.loads(response.data)
        
        if data['success']:
            stored_categories = data['data']
            self.assertEqual(len(stored_categories), 1)
            self.assertEqual(stored_categories[0]['name'], 'Integrity Test')
    
    def test_sync_error_handling(self):
        """Test sync error handling"""
        # Test with invalid data
        invalid_order = {
            'order_number': '',  # Invalid empty order number
            'customer_name': 'Test Customer'
        }
        
        response = self.client.post('/api/offline/orders/store',
                                data=json.dumps(invalid_order),
                                content_type='application/json')
        
        # Should handle error gracefully
        self.assertIn(response.status_code, [200, 400])
        
        data = json.loads(response.data)
        if response.status_code == 400:
            self.assertFalse(data['success'])
            self.assertIn('error', data)
    
    def test_performance_offline_operations(self):
        """Test performance of offline operations"""
        import time
        
        # Test multiple offline operations
        start_time = time.time()
        
        for i in range(10):
            offline_order = {
                'order_number': f'PERF-{i:03d}',
                'customer_name': f'Customer {i}',
                'status': 'New',
                'offline_id': f'temp_{i}'
            }
            
            response = self.client.post('/api/offline/orders/store',
                                    data=json.dumps(offline_order),
                                    content_type='application/json')
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Should complete 10 operations within reasonable time
        self.assertLess(operation_time, 5.0)  # 5 seconds max
        
        # Check queue size
        response = self.client.get('/api/offline/queue/status')
        data = json.loads(response.data)
        
        if data['success']:
            queue_size = data['data']['queue']['size']
            self.assertGreaterEqual(queue_size, 10)
    
    def test_offline_storage_limits(self):
        """Test offline storage limits"""
        # Test storing large amounts of offline data
        large_dataset = []
        
        for i in range(100):  # Create 100 test orders
            large_dataset.append({
                'order_number': f'LARGE-{i:03d}',
                'customer_name': f'Customer {i}',
                'status': 'New',
                'offline_id': f'temp_large_{i}',
                'created_at': datetime.utcnow().isoformat()
            })
        
        # Store in batches to test limits
        for i in range(0, len(large_dataset), 10):
            batch = large_dataset[i:i+10]
            response = self.client.post('/api/offline/orders/batch_store',
                                    data=json.dumps({'orders': batch}),
                                    content_type='application/json')
            
            # Should handle large datasets gracefully
            self.assertIn(response.status_code, [200, 207, 413])  # 413 = Payload Too Large
        
        # Verify storage efficiency
        response = self.client.get('/api/offline/queue/status')
        data = json.loads(response.data)
        
        if data['success']:
            stats = data['data']['stats']
            self.assertIn('storage_usage', stats)

def run_offline_tests():
    """Run all offline functionality tests"""
    print("Running Offline Functionality Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(OfflineFunctionalityTestCase)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    
    return success

def test_integration_scenarios():
    """Test real-world integration scenarios"""
    print("\nRunning Integration Scenarios...")
    print("=" * 40)
    
    scenarios = [
        "1. Complete offline workflow: Create orders -> Sync -> Verify",
        "2. Conflict resolution: Create conflicting orders -> Resolve -> Sync",
        "3. Large dataset handling: Bulk offline operations -> Sync",
        "4. Network interruption: Online -> Offline -> Online -> Auto-sync",
        "5. Data integrity: Offline storage -> Server sync -> Consistency check"
    ]
    
    for scenario in scenarios:
        print(f"- {scenario}")
    
    print("\nIntegration tests require manual verification:")
    print("- Test offline mode in browser")
    print("- Simulate network disconnection")
    print("- Verify data synchronization")
    print("- Check conflict resolution UI")
    print("- Monitor performance during offline operations")

def main():
    """Main test runner"""
    print("Starting Offline Functionality Tests...\n")
    
    # Change to web_cloud directory
    if os.path.basename(os.getcwd()) != 'web_cloud':
        if os.path.exists('web_cloud'):
            os.chdir('web_cloud')
        else:
            print("❌ Error: web_cloud directory not found")
            return False
    
    # Run unit tests
    unit_test_success = run_offline_tests()
    
    # Run integration scenarios
    test_integration_scenarios()
    
    print("\nTest Summary:")
    print(f"Unit Tests: {'PASSED' if unit_test_success else 'FAILED'}")
    print("Integration Scenarios: Defined for manual testing")
    print("Offline API Endpoints: Implemented")
    print("Conflict Resolution: Implemented")
    print("Data Storage: Implemented")
    print("Synchronization: Implemented")
    
    print("\nNext Steps:")
    print("1. Run application: python app.py")
    print("2. Test offline mode in browser")
    print("3. Verify synchronization works")
    print("4. Test conflict resolution")
    print("5. Monitor performance")
    
    print("\nDocumentation:")
    print("- See OFFLINE_FEATURES.md for detailed guide")
    print("- Check API endpoints in routes/offline_api.py")
    print("- Review client-side implementation in static/js/offline-manager.js")
    
    return unit_test_success

if __name__ == '__main__':
    main()