"""
Performance and Load Tests for Multi-Web-Cloud POS Application
Tests system performance, database query optimization, API response times, and concurrent user handling
"""

import unittest
import json
import tempfile
import os
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, session, request, g
import logging
import psutil
import gc

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

class TestPerformanceLoad(unittest.TestCase):
    """Performance and load test suite"""
    
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
                'default': {'requests': 1000, 'window': 60},  # Higher limits for load testing
                'auth': {'requests': 100, 'window': 300},
                'api': {'requests': 1000, 'window': 60}
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
        
        # Performance tracking
        cls.performance_metrics = {}
    
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
        
        # Clear performance metrics
        self.performance_metrics = {
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'db_query_times': [],
            'error_count': 0
        }
    
    @classmethod
    def _create_test_data(cls):
        """Create comprehensive test data for performance testing"""
        # Create test users
        cls.test_users = []
        for i in range(10):
            user = User(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                role='cashier' if i > 0 else 'admin'
            )
            user.set_password('testpass123')
            cls.test_users.append(user)
            db.session.add(user)
        
        # Create test categories
        cls.test_categories = []
        for i in range(5):
            category = Category(
                name=f'Category {i}',
                description=f'Test category {i} description'
            )
            cls.test_categories.append(category)
            db.session.add(category)
        
        # Create test menu items
        cls.test_menu_items = []
        for i in range(50):
            item = MenuItem(
                name=f'Test Item {i}',
                description=f'Test item {i} description',
                category_id=(i % 5) + 1,
                price=Decimal(str(100 + i * 10)),
                stock_quantity=100 + i,
                min_stock_level=10,
                unit='pcs'
            )
            cls.test_menu_items.append(item)
            db.session.add(item)
        
        # Create test tables
        cls.test_tables = []
        for i in range(20):
            table = Table(
                table_number=f'T{i+1}',
                capacity=4 + (i % 4),
                location=f'Area {i % 3}',
                description=f'Test table {i}'
            )
            cls.test_tables.append(table)
            db.session.add(table)
        
        db.session.commit()
    
    def _measure_performance(self, test_name, func, *args, **kwargs):
        """Measure performance metrics for a function"""
        # Record initial system state
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        initial_cpu = psutil.cpu_percent()
        
        # Measure execution time
        start_time = time.time()
        gc.collect()  # Force garbage collection before test
        
        try:
            result = func(*args, **kwargs)
            success = True
        except Exception as e:
            result = None
            success = False
            self.performance_metrics['error_count'] += 1
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Record final system state
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        final_cpu = psutil.cpu_percent()
        
        # Store metrics
        metrics = {
            'test_name': test_name,
            'execution_time': execution_time,
            'initial_memory': initial_memory,
            'final_memory': final_memory,
            'memory_delta': final_memory - initial_memory,
            'initial_cpu': initial_cpu,
            'final_cpu': final_cpu,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.performance_metrics['response_times'].append(execution_time)
        self.performance_metrics['memory_usage'].append(final_memory)
        self.performance_metrics['cpu_usage'].append(final_cpu)
        
        return result, metrics
    
    def test_database_query_performance(self):
        """Test database query performance"""
        print("\n=== Testing Database Query Performance ===")
        
        # Test simple queries
        def get_all_menu_items():
            return MenuItem.query.all()
        
        result, metrics = self._measure_performance(
            'get_all_menu_items', get_all_menu_items
        )
        
        self.assertIsNotNone(result, "Query should return results")
        self.assertLess(metrics['execution_time'], 0.1, "Simple query should be fast")
        
        # Test complex queries with joins
        def get_orders_with_items():
            return db.session.query(Order).join(OrderItem).join(MenuItem).all()
        
        result, metrics = self._measure_performance(
            'get_orders_with_items', get_orders_with_items
        )
        
        self.assertLess(metrics['execution_time'], 0.5, "Complex query should be reasonable")
        
        # Test filtered queries
        def get_filtered_menu_items():
            return MenuItem.query.filter(
                MenuItem.price.between(100, 500)
            ).filter(
                MenuItem.stock_quantity > 50
            ).all()
        
        result, metrics = self._measure_performance(
            'get_filtered_menu_items', get_filtered_menu_items
        )
        
        self.assertLess(metrics['execution_time'], 0.2, "Filtered query should be fast")
        
        # Test aggregate queries
        def get_sales_summary():
            return db.session.query(
                db.func.count(Order.id).label('total_orders'),
                db.func.sum(Order.total_amount).label('total_revenue')
            ).first()
        
        result, metrics = self._measure_performance(
            'get_sales_summary', get_sales_summary
        )
        
        self.assertLess(metrics['execution_time'], 0.3, "Aggregate query should be fast")
        
        print("✅ Database query performance tests passed")
    
    def test_api_response_times(self):
        """Test API response times under various loads"""
        print("\n=== Testing API Response Times ===")
        
        # Test simple GET endpoints
        endpoints = [
            '/api/menu/items',
            '/api/categories',
            '/api/tables',
            '/api/offline/status'
        ]
        
        for endpoint in endpoints:
            def make_request():
                return self.client.get(endpoint)
            
            result, metrics = self._measure_performance(
                f'GET_{endpoint}', make_request
            )
            
            self.assertEqual(result.status_code, 200, f"Endpoint {endpoint} should work")
            self.assertLess(metrics['execution_time'], 0.5, f"Endpoint {endpoint} should be fast")
        
        # Test POST endpoints
        def create_order():
            order_data = {
                'customer_name': 'Performance Test Customer',
                'order_type': 'Dine-in',
                'table_id': 1,
                'items': [
                    {'menu_item_id': 1, 'quantity': 2, 'price': 100.00}
                ]
            }
            return self.client.post('/api/orders', json=order_data)
        
        result, metrics = self._measure_performance(
            'POST_create_order', create_order
        )
        
        self.assertIn(result.status_code, [200, 401], "Order creation should work")
        self.assertLess(metrics['execution_time'], 1.0, "Order creation should be fast")
        
        # Test validation endpoints
        def validate_field():
            return self.client.post('/api/validation/validate-field', json={
                'field_name': 'email',
                'field_value': 'test@example.com',
                'field_type': 'email'
            })
        
        result, metrics = self._measure_performance(
            'POST_validate_field', validate_field
        )
        
        self.assertEqual(result.status_code, 200, "Field validation should work")
        self.assertLess(metrics['execution_time'], 0.2, "Field validation should be fast")
        
        print("✅ API response times tests passed")
    
    def test_concurrent_user_handling(self):
        """Test system performance with concurrent users"""
        print("\n=== Testing Concurrent User Handling ===")
        
        # Simulate concurrent users accessing the system
        def simulate_user_session(user_id):
            """Simulate a user session with various operations"""
            operations = []
            
            # Login simulation
            def login():
                return self.client.post('/auth/login', json={
                    'username': f'testuser{user_id}',
                    'password': 'testpass123'
                })
            
            operations.append(('login', login))
            
            # Browse menu
            def browse_menu():
                return self.client.get('/api/menu/items')
            
            operations.append(('browse_menu', browse_menu))
            
            # Create order
            def create_order():
                order_data = {
                    'customer_name': f'Concurrent User {user_id}',
                    'order_type': 'Dine-in',
                    'items': [
                        {'menu_item_id': (user_id % 50) + 1, 'quantity': 1, 'price': 100.00}
                    ]
                }
                return self.client.post('/api/orders', json=order_data)
            
            operations.append(('create_order', create_order))
            
            # Execute operations and measure times
            results = {}
            for op_name, op_func in operations:
                try:
                    start_time = time.time()
                    response = op_func()
                    end_time = time.time()
                    results[op_name] = {
                        'response_time': end_time - start_time,
                        'status_code': response.status_code,
                        'success': response.status_code in [200, 302]
                    }
                except Exception as e:
                    results[op_name] = {
                        'error': str(e),
                        'success': False
                    }
            
            return results
        
        # Run concurrent user simulations
        num_users = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            # Submit user simulation tasks
            futures = [
                executor.submit(simulate_user_session, i)
                for i in range(num_users)
            ]
            
            # Collect results
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    all_results.append(result)
                except Exception as e:
                    print(f"User simulation failed: {e}")
        
        # Analyze results
        successful_sessions = sum(1 for r in all_results if any(op.get('success', False) for op in r.values()))
        self.assertGreater(successful_sessions, num_users * 0.8, "Most sessions should succeed")
        
        # Calculate average response times
        response_times = []
        for session_results in all_results:
            for op_result in session_results.values():
                if 'response_time' in op_result:
                    response_times.append(op_result['response_time'])
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            self.assertLess(avg_response_time, 2.0, "Average response time should be reasonable")
        
        print("✅ Concurrent user handling tests passed")
    
    def test_memory_usage_under_load(self):
        """Test memory usage under various loads"""
        print("\n=== Testing Memory Usage Under Load ===")
        
        # Test memory usage with large datasets
        def create_large_dataset():
            """Create a large dataset to test memory usage"""
            # Create many orders
            orders = []
            for i in range(1000):
                order = Order(
                    order_number=f'PERF{i:06d}',
                    customer_name=f'Customer {i}',
                    order_type='Dine-in',
                    status='Completed',
                    total_amount=Decimal(str(100 + i % 500))
                )
                orders.append(order)
            
            # Bulk insert
            db.session.bulk_save_objects(orders)
            db.session.commit()
            
            return len(orders)
        
        result, metrics = self._measure_performance(
            'create_large_dataset', create_large_dataset
        )
        
        self.assertEqual(result, 1000, "All orders should be created")
        self.assertLess(metrics['memory_delta'], 100, "Memory usage should be reasonable")
        
        # Test memory usage with complex queries
        def complex_query_with_large_dataset():
            """Run complex queries on large dataset"""
            # Query with joins and aggregations
            results = db.session.query(
                Order.customer_name,
                db.func.count(Order.id).label('order_count'),
                db.func.sum(Order.total_amount).label('total_spent')
            ).group_by(Order.customer_name).all()
            
            return len(results)
        
        result, metrics = self._measure_performance(
            'complex_query_with_large_dataset', complex_query_with_large_dataset
        )
        
        self.assertGreater(result, 0, "Query should return results")
        self.assertLess(metrics['memory_delta'], 50, "Complex query memory usage should be reasonable")
        
        # Test memory cleanup
        def cleanup_large_dataset():
            """Clean up large dataset"""
            Order.query.delete()
            db.session.commit()
            gc.collect()  # Force garbage collection
            
            return True
        
        result, metrics = self._measure_performance(
            'cleanup_large_dataset', cleanup_large_dataset
        )
        
        self.assertTrue(result, "Cleanup should succeed")
        
        print("✅ Memory usage under load tests passed")
    
    def test_cpu_usage_under_load(self):
        """Test CPU usage under various loads"""
        print("\n=== Testing CPU Usage Under Load ===")
        
        # Test CPU usage with intensive operations
        def cpu_intensive_operation():
            """Perform CPU-intensive operations"""
            # Complex calculations
            result = 0
            for i in range(100000):
                result += i * i
            
            # String operations
            text = "test string"
            for i in range(10000):
                text = text.replace('test', 'TEST')
                text = text.upper()
                text = text.lower()
            
            return result
        
        result, metrics = self._measure_performance(
            'cpu_intensive_operation', cpu_intensive_operation
        )
        
        self.assertGreater(result, 0, "CPU operation should produce result")
        self.assertLess(metrics['execution_time'], 5.0, "CPU operation should complete in reasonable time")
        
        # Test CPU usage with concurrent operations
        def concurrent_cpu_operations():
            """Run concurrent CPU-intensive operations"""
            def worker():
                return sum(i * i for i in range(50000))
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(worker) for _ in range(10)]
                results = [future.result() for future in futures]
            
            return sum(results)
        
        result, metrics = self._measure_performance(
            'concurrent_cpu_operations', concurrent_cpu_operations
        )
        
        self.assertGreater(result, 0, "Concurrent operations should produce result")
        self.assertLess(metrics['execution_time'], 10.0, "Concurrent operations should complete in reasonable time")
        
        print("✅ CPU usage under load tests passed")
    
    def test_offline_sync_performance(self):
        """Test offline synchronization performance"""
        print("\n=== Testing Offline Sync Performance ===")
        
        # Test offline order storage performance
        def store_many_offline_orders():
            """Store many orders offline"""
            orders = []
            for i in range(100):
                order_data = {
                    'order_id': f'OFFLINE{i:06d}',
                    'customer_name': f'Offline Customer {i}',
                    'items': [
                        {'name': f'Item {i}', 'price': 100 + i, 'quantity': 1}
                    ],
                    'total_amount': 100 + i
                }
                local_id = self.offline_manager.store_order_offline(order_data)
                orders.append(local_id)
            
            return len(orders)
        
        result, metrics = self._measure_performance(
            'store_many_offline_orders', store_many_offline_orders
        )
        
        self.assertEqual(result, 100, "All offline orders should be stored")
        self.assertLess(metrics['execution_time'], 5.0, "Offline storage should be fast")
        
        # Test sync performance
        def sync_offline_data():
            """Sync offline data"""
            with patch.object(self.offline_manager, 'is_online', True):
                with patch.object(self.offline_manager, '_make_api_request') as mock_api:
                    mock_api.return_value = {'success': True}
                    
                    success = self.offline_manager.force_sync()
                    return success
        
        result, metrics = self._measure_performance(
            'sync_offline_data', sync_offline_data
        )
        
        self.assertTrue(result, "Sync should succeed")
        self.assertLess(metrics['execution_time'], 10.0, "Sync should complete in reasonable time")
        
        print("✅ Offline sync performance tests passed")
    
    def test_validation_performance(self):
        """Test validation system performance"""
        print("\n=== Testing Validation Performance ===")
        
        # Test field validation performance
        def validate_many_fields():
            """Validate many fields"""
            test_data = [
                ('email', 'test@example.com', 'email'),
                ('phone', '+919876543210', 'phone'),
                ('gst_number', '27AAPCE2839H1ZV', 'gst_number'),
                ('password', 'StrongP@ssw0rd123', 'password'),
                ('order_number', 'ORD20231209001', 'order_number')
            ] * 100  # Repeat 100 times
            
            results = []
            for field_name, field_value, field_type in test_data:
                is_valid, message = self.form_validator.validate_business_rules(field_name, field_value)
                results.append(is_valid)
            
            return sum(results)
        
        result, metrics = self._measure_performance(
            'validate_many_fields', validate_many_fields
        )
        
        self.assertGreater(result, 0, "Validations should produce results")
        self.assertLess(metrics['execution_time'], 2.0, "Field validation should be fast")
        
        # Test input sanitization performance
        def sanitize_many_inputs():
            """Sanitize many inputs"""
            test_inputs = [
                '<script>alert("xss")</script>',
                "'; DROP TABLE users; --",
                'Normal text input',
                'Another normal input'
            ] * 100  # Repeat 100 times
            
            results = []
            for input_text in test_inputs:
                sanitized = self.form_validator.sanitize_input(input_text)
                results.append(sanitized)
            
            return len(results)
        
        result, metrics = self._measure_performance(
            'sanitize_many_inputs', sanitize_many_inputs
        )
        
        self.assertEqual(result, 400, "All inputs should be sanitized")
        self.assertLess(metrics['execution_time'], 2.0, "Input sanitization should be fast")
        
        # Test password strength validation performance
        def validate_many_passwords():
            """Validate many passwords"""
            passwords = [
                'StrongP@ssw0rd123',
                'WeakPassword',
                'AnotherStrongP@ss456',
                '123456'
            ] * 100  # Repeat 100 times
            
            results = []
            for password in passwords:
                is_valid, errors = self.form_validator.validate_password_strength(password)
                results.append(is_valid)
            
            return sum(results)
        
        result, metrics = self._measure_performance(
            'validate_many_passwords', validate_many_passwords
        )
        
        self.assertGreater(result, 0, "Password validations should produce results")
        self.assertLess(metrics['execution_time'], 3.0, "Password validation should be fast")
        
        print("✅ Validation performance tests passed")
    
    def test_session_management_performance(self):
        """Test session management performance"""
        print("\n=== Testing Session Management Performance ===")
        
        # Test concurrent session creation
        def create_many_sessions():
            """Create many sessions concurrently"""
            def create_session(user_id):
                with self.app.test_request_context('/', headers={
                    'User-Agent': f'Test Browser {user_id}',
                    'Accept-Language': 'en-US,en;q=0.9'
                }):
                    return self.session_manager.create_session(
                        user_id=user_id,
                        remember_me=True
                    )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_session, i) for i in range(50)]
                results = [future.result() for future in futures]
            
            return len(results)
        
        result, metrics = self._measure_performance(
            'create_many_sessions', create_many_sessions
        )
        
        self.assertEqual(result, 50, "All sessions should be created")
        self.assertLess(metrics['execution_time'], 5.0, "Session creation should be fast")
        
        # Test session validation performance
        def validate_many_sessions():
            """Validate many sessions"""
            # Create test session data
            session_data = {
                'user_id': 1,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'session_fingerprint': 'test_fingerprint'
            }
            
            with patch('flask.session', session_data):
                validations = []
                for i in range(100):
                    is_valid = self.session_manager._is_session_valid()
                    validations.append(is_valid)
                
                return sum(validations)
        
        result, metrics = self._measure_performance(
            'validate_many_sessions', validate_many_sessions
        )
        
        self.assertGreater(result, 0, "Session validations should produce results")
        self.assertLess(metrics['execution_time'], 2.0, "Session validation should be fast")
        
        print("✅ Session management performance tests passed")
    
    def test_performance_summary(self):
        """Generate performance summary report"""
        print("\n=== Performance Summary Report ===")
        
        if not self.performance_metrics['response_times']:
            print("No performance metrics collected")
            return
        
        # Calculate statistics
        response_times = self.performance_metrics['response_times']
        memory_usage = self.performance_metrics['memory_usage']
        cpu_usage = self.performance_metrics['cpu_usage']
        
        summary = {
            'response_time_stats': {
                'min': min(response_times),
                'max': max(response_times),
                'avg': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'p95': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
            },
            'memory_usage_stats': {
                'min': min(memory_usage),
                'max': max(memory_usage),
                'avg': statistics.mean(memory_usage),
                'median': statistics.median(memory_usage)
            },
            'cpu_usage_stats': {
                'min': min(cpu_usage),
                'max': max(cpu_usage),
                'avg': statistics.mean(cpu_usage),
                'median': statistics.median(cpu_usage)
            },
            'total_tests': len(response_times),
            'error_count': self.performance_metrics['error_count'],
            'success_rate': ((len(response_times) - self.performance_metrics['error_count']) / len(response_times)) * 100
        }
        
        print(f"Response Time Statistics:")
        print(f"  Min: {summary['response_time_stats']['min']:.3f}s")
        print(f"  Max: {summary['response_time_stats']['max']:.3f}s")
        print(f"  Avg: {summary['response_time_stats']['avg']:.3f}s")
        print(f"  Median: {summary['response_time_stats']['median']:.3f}s")
        print(f"  95th percentile: {summary['response_time_stats']['p95']:.3f}s")
        
        print(f"\nMemory Usage Statistics:")
        print(f"  Min: {summary['memory_usage_stats']['min']:.1f}MB")
        print(f"  Max: {summary['memory_usage_stats']['max']:.1f}MB")
        print(f"  Avg: {summary['memory_usage_stats']['avg']:.1f}MB")
        print(f"  Median: {summary['memory_usage_stats']['median']:.1f}MB")
        
        print(f"\nCPU Usage Statistics:")
        print(f"  Min: {summary['cpu_usage_stats']['min']:.1f}%")
        print(f"  Max: {summary['cpu_usage_stats']['max']:.1f}%")
        print(f"  Avg: {summary['cpu_usage_stats']['avg']:.1f}%")
        print(f"  Median: {summary['cpu_usage_stats']['median']:.1f}%")
        
        print(f"\nOverall Statistics:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  Error Count: {summary['error_count']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        # Performance assertions
        self.assertLess(summary['response_time_stats']['avg'], 1.0, "Average response time should be under 1 second")
        self.assertLess(summary['response_time_stats']['p95'], 2.0, "95th percentile response time should be under 2 seconds")
        self.assertGreater(summary['success_rate'], 95.0, "Success rate should be above 95%")
        self.assertLess(summary['memory_usage_stats']['avg'], 200.0, "Average memory usage should be reasonable")
        
        print("✅ Performance summary completed")
        print("✅ All performance tests passed")

def run_performance_load_tests():
    """Run all performance and load tests"""
    print("=" * 80)
    print("PERFORMANCE AND LOAD TEST SUITE")
    print("=" * 80)
    print("Testing system performance, scalability, and resource usage\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods
    test_suite.addTest(TestPerformanceLoad('test_database_query_performance'))
    test_suite.addTest(TestPerformanceLoad('test_api_response_times'))
    test_suite.addTest(TestPerformanceLoad('test_concurrent_user_handling'))
    test_suite.addTest(TestPerformanceLoad('test_memory_usage_under_load'))
    test_suite.addTest(TestPerformanceLoad('test_cpu_usage_under_load'))
    test_suite.addTest(TestPerformanceLoad('test_offline_sync_performance'))
    test_suite.addTest(TestPerformanceLoad('test_validation_performance'))
    test_suite.addTest(TestPerformanceLoad('test_session_management_performance'))
    test_suite.addTest(TestPerformanceLoad('test_performance_summary'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("PERFORMANCE AND LOAD TEST RESULTS")
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
    success = run_performance_load_tests()
    
    if success:
        print("\n✅ ALL PERFORMANCE AND LOAD TESTS PASSED!")
        print("System performance is production-ready")
        exit(0)
    else:
        print("\n❌ SOME PERFORMANCE TESTS FAILED!")
        print("Review and fix performance issues before production deployment")
        exit(1)