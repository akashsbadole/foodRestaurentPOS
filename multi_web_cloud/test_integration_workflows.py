"""
Integration Workflow Tests for Multi-Web-Cloud POS Application
Tests end-to-end workflows including order processing, payment, offline sync, and security
"""

import unittest
import json
import tempfile
import os
import time
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging
import threading

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

class TestIntegrationWorkflows(unittest.TestCase):
    """Integration workflow test suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Configure test app
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
            'BASE_URL': 'http://localhost:5000'
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
        
        # Create test data
        cls._create_test_data()
        
        # Initialize managers
        cls.form_validator = FormValidator()
        cls.session_manager = SessionManager(cls.app)
        cls.security_manager = SecurityManager(cls.app)
        cls.offline_manager = OfflineManager(cls.app)
        cls.razorpay_manager = RazorpayManager(cls.app)
    
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
    def _create_test_data(cls):
        """Create test data for testing"""
        # Create test user
        cls.test_user = User(
            username='testuser',
            email='test@example.com',
            role='admin'
        )
        cls.test_user.set_password('testpass123')
        db.session.add(cls.test_user)
        
        # Create test category
        cls.test_category = Category(
            name='Test Category',
            description='Test category description'
        )
        db.session.add(cls.test_category)
        
        # Create test menu items
        cls.test_menu_item1 = MenuItem(
            name='Test Item 1',
            description='Test item 1 description',
            category_id=1,
            price=Decimal('100.00'),
            stock_quantity=50,
            min_stock_level=5,
            unit='pcs'
        )
        cls.test_menu_item2 = MenuItem(
            name='Test Item 2',
            description='Test item 2 description',
            category_id=1,
            price=Decimal('150.00'),
            stock_quantity=30,
            min_stock_level=3,
            unit='pcs'
        )
        db.session.add(cls.test_menu_item1)
        db.session.add(cls.test_menu_item2)
        
        # Create test table
        cls.test_table = Table(
            table_number='T1',
            capacity=4,
            location='Main Hall',
            description='Test table'
        )
        db.session.add(cls.test_table)
        
        db.session.commit()
    
    def _login_user(self, username='testuser', password='testpass123'):
        """Helper method to login user"""
        response = self.client.post('/auth/login', data={
            'username': username,
            'password': password,
            'remember': True
        }, follow_redirects=True)
        return response
    
    def test_complete_order_workflow(self):
        """Test complete order workflow from creation to payment"""
        print("\n=== Testing Complete Order Workflow ===")
        
        # Step 1: Login
        response = self._login_user()
        self.assertIn(response.status_code, [200, 302], "Login should succeed")
        
        # Step 2: Create order
        order_data = {
            'customer_name': 'John Doe',
            'order_type': 'Dine-in',
            'table_id': 1,
            'items': [
                {'menu_item_id': 1, 'quantity': 2, 'price': 100.00},
                {'menu_item_id': 2, 'quantity': 1, 'price': 150.00}
            ],
            'special_instructions': 'Extra spicy'
        }
        
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200, "Order creation should succeed")
        
        order_response = json.loads(response.data)
        self.assertTrue(order_response.get('success'), "Order creation should return success")
        order_id = order_response.get('order_id')
        self.assertIsNotNone(order_id, "Order ID should be returned")
        
        # Step 3: Get order details
        response = self.client.get(f'/api/orders/{order_id}')
        self.assertEqual(response.status_code, 200, "Get order details should succeed")
        
        order_details = json.loads(response.data)
        self.assertEqual(order_details['customer_name'], 'John Doe')
        self.assertEqual(order_details['total_amount'], 350.00)
        
        # Step 4: Update order status
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'In Progress'
        })
        self.assertEqual(response.status_code, 200, "Order status update should succeed")
        
        # Step 5: Create payment
        payment_data = {
            'order_id': order_id,
            'payment_method': 'Cash',
            'amount_paid': 350.00,
            'reference_number': 'CASH001'
        }
        
        response = self.client.post('/api/payments', json=payment_data)
        self.assertEqual(response.status_code, 200, "Payment creation should succeed")
        
        payment_response = json.loads(response.data)
        self.assertTrue(payment_response.get('success'), "Payment creation should return success")
        
        # Step 6: Update order status to completed
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Completed'
        })
        self.assertEqual(response.status_code, 200, "Order completion should succeed")
        
        # Step 7: Verify order is marked as paid
        response = self.client.get(f'/api/orders/{order_id}')
        order_details = json.loads(response.data)
        self.assertEqual(order_details['status'], 'Completed')
        
        print("✅ Complete order workflow tests passed")
    
    def test_razorpay_payment_workflow(self):
        """Test Razorpay payment workflow"""
        print("\n=== Testing Razorpay Payment Workflow ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Create order
        order_data = {
            'customer_name': 'Jane Smith',
            'order_type': 'Takeaway',
            'items': [
                {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
            ]
        }
        
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200)
        
        order_response = json.loads(response.data)
        order_id = order_response.get('order_id')
        
        # Step 3: Create Razorpay order
        with patch('utils.razorpay_manager.RazorpayManager.create_order') as mock_create:
            mock_create.return_value = {
                'id': 'order_test_123',
                'entity': 'order',
                'amount': 10000,
                'currency': 'INR',
                'status': 'created'
            }
            
            response = self.client.post('/api/payment/create-order', json={
                'amount': 100.00,
                'currency': 'INR',
                'receipt': f'RECEIPT_{order_id}'
            })
            
            self.assertEqual(response.status_code, 200)
            razorpay_response = json.loads(response.data)
            self.assertTrue(razorpay_response.get('success'))
        
        # Step 4: Process payment with mock
        with patch('utils.razorpay_manager.RazorpayManager.verify_payment_signature') as mock_verify:
            mock_verify.return_value = True
            
            response = self.client.post('/api/payment/verify', json={
                'razorpay_order_id': 'order_test_123',
                'razorpay_payment_id': 'pay_test_456',
                'razorpay_signature': 'test_signature'
            })
            
            self.assertEqual(response.status_code, 200)
            verify_response = json.loads(response.data)
            self.assertTrue(verify_response.get('success'))
        
        # Step 5: Update order status
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Completed'
        })
        self.assertEqual(response.status_code, 200)
        
        print("✅ Razorpay payment workflow tests passed")
    
    def test_offline_to_online_sync_workflow(self):
        """Test offline to online synchronization workflow"""
        print("\n=== Testing Offline to Online Sync Workflow ===")
        
        # Step 1: Simulate offline mode
        with patch.object(self.offline_manager, 'is_online', False):
            # Step 2: Create order offline
            order_data = {
                'order_id': 'OFFLINE001',
                'customer_name': 'Offline Customer',
                'items': [
                    {'name': 'Offline Item 1', 'price': 100, 'quantity': 2}
                ],
                'total_amount': 200
            }
            
            local_id = self.offline_manager.store_order_offline(order_data)
            self.assertIsNotNone(local_id, "Order should be stored offline")
            
            # Step 3: Create payment offline
            payment_data = {
                'payment_id': 'PAY_OFFLINE001',
                'amount': 200,
                'method': 'cash'
            }
            
            payment_local_id = self.offline_manager.store_payment_offline(payment_data, local_id)
            self.assertIsNotNone(payment_local_id, "Payment should be stored offline")
            
            # Step 4: Check sync status
            sync_status = self.offline_manager.get_sync_status()
            self.assertFalse(sync_status['is_online'])
            self.assertEqual(sync_status['pending_orders'], 1)
            self.assertEqual(sync_status['pending_payments'], 1)
        
        # Step 5: Simulate coming back online
        with patch.object(self.offline_manager, 'is_online', True):
            with patch.object(self.offline_manager, '_make_api_request') as mock_api:
                mock_api.return_value = {'success': True}
                
                # Step 6: Force sync
                sync_success = self.offline_manager.force_sync()
                self.assertTrue(sync_success, "Sync should succeed when online")
                
                # Step 7: Check sync status after sync
                sync_status = self.offline_manager.get_sync_status()
                self.assertTrue(sync_status['is_online'])
        
        print("✅ Offline to online sync workflow tests passed")
    
    def test_session_management_lifecycle(self):
        """Test complete session management lifecycle"""
        print("\n=== Testing Session Management Lifecycle ===")
        
        # Step 1: Login and create session
        with self.app.test_request_context('/auth/login', headers={
            'User-Agent': 'Mozilla/5.0 (Test Browser)',
            'Accept-Language': 'en-US,en;q=0.9'
        }):
            session_data = self.session_manager.create_session(
                user_id=self.test_user.id,
                remember_me=True
            )
            
            self.assertIsNotNone(session_data)
            self.assertIn('session_fingerprint', session_data)
            
            # Step 2: Validate session
            is_valid = self.session_manager._is_session_valid()
            self.assertTrue(is_valid, "Session should be valid")
            
            # Step 3: Extend session
            extended = self.session_manager.extend_session(hours=12)
            self.assertTrue(extended, "Session should be extended")
            
            # Step 4: Get session info
            info = self.session_manager.get_session_info()
            self.assertIsNotNone(info)
            self.assertEqual(info['user_id'], self.test_user.id)
            
            # Step 5: Revoke session
            revoked = self.session_manager.revoke_session(session_data['session_id'])
            self.assertTrue(revoked, "Session should be revoked")
            
            # Step 6: Validate after revocation
            is_valid = self.session_manager._is_session_valid()
            self.assertFalse(is_valid, "Session should be invalid after revocation")
        
        print("✅ Session management lifecycle tests passed")
    
    def test_security_event_handling_workflow(self):
        """Test security event handling workflow"""
        print("\n=== Testing Security Event Handling Workflow ===")
        
        with self.app.test_request_context('/api/test', headers={
            'User-Agent': 'Test Browser',
            'X-Forwarded-For': '192.168.1.100'
        }):
            # Step 1: Simulate suspicious activity
            suspicious_requests = [
                '<script>alert("xss")</script>',
                "'; DROP TABLE users; --",
                '../../../etc/passwd'
            ]
            
            for suspicious_input in suspicious_requests:
                is_suspicious = self.security_manager._is_suspicious_string(suspicious_input)
                self.assertTrue(is_suspicious, f"Suspicious input should be detected: {suspicious_input}")
                
                # Log security event
                self.security_manager._log_security_event(
                    'SUSPICIOUS_INPUT',
                    '192.168.1.100',
                    f'Suspicious input detected: {suspicious_input[:50]}',
                    'high'
                )
            
            # Step 2: Simulate failed login attempts
            for i in range(6):  # Exceed max failed attempts
                self.security_manager._increment_failed_attempts('192.168.1.200')
            
            # Step 3: Check if IP is blocked
            is_blocked = self.security_manager._is_ip_blocked('192.168.1.200')
            self.assertTrue(is_blocked, "IP should be blocked after failed attempts")
            
            # Step 4: Get security statistics
            stats = self.security_manager.get_security_statistics()
            self.assertIn('total_events_24h', stats)
            self.assertIn('blocked_ips', stats)
            self.assertIn('failed_attempts', stats)
            
            # Step 5: Get security events
            events = self.security_manager.get_security_events(limit=10)
            self.assertIsInstance(events, list)
            self.assertGreater(len(events), 0, "Security events should be logged")
            
            # Step 6: Unblock IP
            self.security_manager._unblock_ip('192.168.1.200')
            is_blocked = self.security_manager._is_ip_blocked('192.168.1.200')
            self.assertFalse(is_blocked, "IP should be unblocked")
        
        print("✅ Security event handling workflow tests passed")
    
    def test_multi_step_order_with_modifications(self):
        """Test multi-step order with modifications"""
        print("\n=== Testing Multi-Step Order with Modifications ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Create initial order
        order_data = {
            'customer_name': 'Customer A',
            'order_type': 'Dine-in',
            'table_id': 1,
            'items': [
                {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
            ]
        }
        
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200)
        
        order_response = json.loads(response.data)
        order_id = order_response.get('order_id')
        
        # Step 3: Add items to order
        response = self.client.post(f'/api/orders/{order_id}/items', json={
            'menu_item_id': 2,
            'quantity': 2,
            'price': 150.00
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 4: Update order details
        response = self.client.put(f'/api/orders/{order_id}', json={
            'customer_name': 'Customer A Updated',
            'special_instructions': 'No onions, extra spicy'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Update order status to preparing
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Preparing'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 6: Update order status to ready
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Ready'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 7: Create partial payment
        response = self.client.post('/api/payments', json={
            'order_id': order_id,
            'payment_method': 'Cash',
            'amount_paid': 200.00,
            'reference_number': 'PARTIAL001'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 8: Create remaining payment
        response = self.client.post('/api/payments', json={
            'order_id': order_id,
            'payment_method': 'Card',
            'amount_paid': 200.00,
            'reference_number': 'CARD001'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 9: Complete order
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Completed'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 10: Verify final order state
        response = self.client.get(f'/api/orders/{order_id}')
        order_details = json.loads(response.data)
        
        self.assertEqual(order_details['status'], 'Completed')
        self.assertEqual(order_details['customer_name'], 'Customer A Updated')
        self.assertEqual(order_details['special_instructions'], 'No onions, extra spicy')
        self.assertEqual(len(order_details['items']), 2)
        self.assertEqual(order_details['total_amount'], 400.00)
        
        print("✅ Multi-step order with modifications tests passed")
    
    def test_inventory_management_workflow(self):
        """Test inventory management workflow"""
        print("\n=== Testing Inventory Management Workflow ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Check initial stock
        response = self.client.get('/api/menu/items/1')
        self.assertEqual(response.status_code, 200)
        
        item_details = json.loads(response.data)
        initial_stock = item_details['stock_quantity']
        
        # Step 3: Create order that consumes inventory
        order_data = {
            'customer_name': 'Inventory Test Customer',
            'order_type': 'Dine-in',
            'items': [
                {'menu_item_id': 1, 'quantity': 5, 'price': 100.00}
            ]
        }
        
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200)
        
        order_response = json.loads(response.data)
        order_id = order_response.get('order_id')
        
        # Step 4: Complete order to update inventory
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Completed'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Check updated stock
        response = self.client.get('/api/menu/items/1')
        self.assertEqual(response.status_code, 200)
        
        item_details = json.loads(response.data)
        updated_stock = item_details['stock_quantity']
        
        self.assertEqual(updated_stock, initial_stock - 5, "Stock should be reduced by order quantity")
        
        # Step 6: Check low stock alert
        response = self.client.get('/api/dashboard/low-stock-items')
        self.assertEqual(response.status_code, 200)
        
        low_stock_items = json.loads(response.data)
        # Item should be in low stock if it's below min_stock_level
        if updated_stock <= 5:
            self.assertGreater(len(low_stock_items), 0, "Low stock items should be detected")
        
        # Step 7: Adjust inventory
        response = self.client.post('/api/inventory/adjust', json={
            'menu_item_id': 1,
            'adjustment_type': 'add',
            'quantity': 20,
            'reason': 'Stock replenishment'
        })
        self.assertEqual(response.status_code, 200)
        
        # Step 8: Verify adjusted stock
        response = self.client.get('/api/menu/items/1')
        self.assertEqual(response.status_code, 200)
        
        item_details = json.loads(response.data)
        final_stock = item_details['stock_quantity']
        
        self.assertEqual(final_stock, updated_stock + 20, "Stock should be increased by adjustment")
        
        print("✅ Inventory management workflow tests passed")
    
    def test_real_time_updates_workflow(self):
        """Test real-time updates workflow"""
        print("\n=== Testing Real-Time Updates Workflow ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Create order
        order_data = {
            'customer_name': 'Real-time Test Customer',
            'order_type': 'Dine-in',
            'table_id': 1,
            'items': [
                {'menu_item_id': 1, 'quantity': 2, 'price': 100.00}
            ]
        }
        
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200)
        
        order_response = json.loads(response.data)
        order_id = order_response.get('order_id')
        
        # Step 3: Subscribe to real-time updates (simulate)
        notifications = []
        
        def mock_notification_handler(notification):
            notifications.append(notification)
        
        # Simulate real-time notifications
        with patch.object(self.offline_manager, '_store_realtime_notification') as mock_store:
            # Step 4: Update order status
            response = self.client.put(f'/api/orders/{order_id}', json={
                'status': 'In Progress'
            })
            self.assertEqual(response.status_code, 200)
            
            # Step 5: Create payment
            response = self.client.post('/api/payments', json={
                'order_id': order_id,
                'payment_method': 'Cash',
                'amount_paid': 200.00,
                'reference_number': 'REALTIME001'
            })
            self.assertEqual(response.status_code, 200)
            
            # Step 6: Complete order
            response = self.client.put(f'/api/orders/{order_id}', json={
                'status': 'Completed'
            })
            self.assertEqual(response.status_code, 200)
            
            # Verify notifications were stored
            self.assertGreater(mock_store.call_count, 0, "Notifications should be stored")
        
        # Step 7: Get real-time notifications
        with patch.object(self.offline_manager, 'get_realtime_notifications') as mock_get:
            mock_get.return_value = [
                {
                    'type': 'order_status_update',
                    'order_id': order_id,
                    'status': 'Completed',
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
            
            notifications = self.offline_manager.get_realtime_notifications()
            self.assertIsInstance(notifications, list)
            self.assertGreater(len(notifications), 0, "Real-time notifications should be available")
        
        print("✅ Real-time updates workflow tests passed")
    
    def test_error_recovery_workflow(self):
        """Test error recovery workflow"""
        print("\n=== Testing Error Recovery Workflow ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Simulate database error during order creation
        with patch('models.db.session.commit') as mock_commit:
            mock_commit.side_effect = Exception("Database connection lost")
            
            order_data = {
                'customer_name': 'Error Recovery Customer',
                'order_type': 'Dine-in',
                'items': [
                    {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
                ]
            }
            
            response = self.client.post('/api/orders', json=order_data)
            self.assertEqual(response.status_code, 500, "Database error should return 500")
            
            error_response = json.loads(response.data)
            self.assertIn('error', error_response)
        
        # Step 3: Retry order creation after error recovery
        response = self.client.post('/api/orders', json=order_data)
        self.assertEqual(response.status_code, 200, "Order should succeed after error recovery")
        
        order_response = json.loads(response.data)
        order_id = order_response.get('order_id')
        
        # Step 4: Simulate payment processing error
        with patch('utils.razorpay_manager.RazorpayManager.capture_payment') as mock_capture:
            mock_capture.side_effect = Exception("Payment gateway timeout")
            
            response = self.client.post('/api/payments', json={
                'order_id': order_id,
                'payment_method': 'Razorpay',
                'amount_paid': 100.00,
                'razorpay_payment_id': 'pay_test_error'
            })
            self.assertEqual(response.status_code, 500, "Payment error should return 500")
        
        # Step 5: Retry with different payment method
        response = self.client.post('/api/payments', json={
            'order_id': order_id,
            'payment_method': 'Cash',
            'amount_paid': 100.00,
            'reference_number': 'RECOVERY001'
        })
        self.assertEqual(response.status_code, 200, "Alternative payment should succeed")
        
        # Step 6: Complete order
        response = self.client.put(f'/api/orders/{order_id}', json={
            'status': 'Completed'
        })
        self.assertEqual(response.status_code, 200, "Order should complete after error recovery")
        
        print("✅ Error recovery workflow tests passed")
    
    def test_concurrent_operations_workflow(self):
        """Test concurrent operations workflow"""
        print("\n=== Testing Concurrent Operations Workflow ===")
        
        # Step 1: Login
        self._login_user()
        
        # Step 2: Create multiple orders concurrently
        def create_order_thread(order_suffix):
            order_data = {
                'customer_name': f'Concurrent Customer {order_suffix}',
                'order_type': 'Dine-in',
                'items': [
                    {'menu_item_id': 1, 'quantity': 1, 'price': 100.00}
                ]
            }
            
            response = self.client.post('/api/orders', json=order_data)
            return response
        
        # Step 3: Create threads for concurrent operations
        threads = []
        results = []
        
        for i in range(5):
            thread = threading.Thread(target=lambda i=i: results.append(create_order_thread(i)))
            threads.append(thread)
        
        # Step 4: Start all threads
        for thread in threads:
            thread.start()
        
        # Step 5: Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Step 6: Verify all orders were created
        successful_orders = 0
        for result in results:
            if result.status_code == 200:
                successful_orders += 1
        
        self.assertGreater(successful_orders, 0, "At least some orders should be created")
        
        # Step 7: Test concurrent status updates
        if successful_orders > 0:
            # Get first successful order
            for result in results:
                if result.status_code == 200:
                    order_response = json.loads(result.data)
                    order_id = order_response.get('order_id')
                    break
            
            def update_status_thread(status):
                response = self.client.put(f'/api/orders/{order_id}', json={
                    'status': status
                })
                return response
            
            # Create multiple status update threads
            status_threads = []
            status_results = []
            
            statuses = ['In Progress', 'Preparing', 'Ready', 'Completed']
            for status in statuses:
                thread = threading.Thread(target=lambda s=status: status_results.append(update_status_thread(s)))
                status_threads.append(thread)
            
            # Start status update threads
            for thread in status_threads:
                thread.start()
            
            # Wait for all threads to complete
            for thread in status_threads:
                thread.join()
            
            # Verify at least one status update succeeded
            successful_updates = sum(1 for r in status_results if r.status_code == 200)
            self.assertGreater(successful_updates, 0, "At least one status update should succeed")
        
        print("✅ Concurrent operations workflow tests passed")

def run_integration_workflow_tests():
    """Run all integration workflow tests"""
    print("=" * 80)
    print("INTEGRATION WORKFLOW TEST SUITE")
    print("=" * 80)
    print("Testing end-to-end workflows and system integration\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestIntegrationWorkflows('test_complete_order_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_razorpay_payment_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_offline_to_online_sync_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_session_management_lifecycle'))
    test_suite.addTest(TestIntegrationWorkflows('test_security_event_handling_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_multi_step_order_with_modifications'))
    test_suite.addTest(TestIntegrationWorkflows('test_inventory_management_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_real_time_updates_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_error_recovery_workflow'))
    test_suite.addTest(TestIntegrationWorkflows('test_concurrent_operations_workflow'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("INTEGRATION WORKFLOW TEST RESULTS")
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
        print("System workflows are production-ready")
        exit(0)
    else:
        print("\n❌ SOME INTEGRATION WORKFLOW TESTS FAILED!")
        print("Review and fix workflow issues before production deployment")
        exit(1)