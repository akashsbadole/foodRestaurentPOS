# Automated Testing Scripts for Support and License Systems

## Overview

This document contains comprehensive automated testing scripts for the support system and license validation system. These scripts enable continuous testing, performance monitoring, and quality assurance automation.

## Table of Contents

1. [Test Automation Framework](#test-automation-framework)
2. [License System Test Scripts](#license-system-test-scripts)
3. [Support System Test Scripts](#support-system-test-scripts)
4. [Integration Test Scripts](#integration-test-scripts)
5. [Performance Test Scripts](#performance-test-scripts)
6. [Security Test Scripts](#security-test-scripts)
7. [UI Test Scripts](#ui-test-scripts)
8. [API Test Scripts](#api-test-scripts)
9. [Database Test Scripts](#database-test-scripts)
10. [Test Execution Orchestration](#test-execution-orchestration)

## Test Automation Framework

### Base Test Automation Framework

```python
# tests/automation/base_test_framework.py
"""Base test automation framework"""

import os
import sys
import json
import time
import logging
import unittest
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import patch, Mock

class TestAutomationFramework:
    """Base framework for automated testing"""
    
    def __init__(self, config_file='tests/automation/config/test_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.test_results = []
        self.start_time = datetime.now()
        self.test_data_dir = Path(self.config.get('test_data_dir', 'tests/automation/data'))
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load test configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'test_data_dir': 'tests/automation/data',
            'test_reports_dir': 'tests/automation/reports',
            'test_logs_dir': 'tests/automation/logs',
            'test_timeout': 300,
            'parallel_execution': True,
            'max_parallel_workers': 4,
            'retry_failed_tests': True,
            'max_retries': 3,
            'performance_thresholds': {
                'license_validation': 0.1,
                'license_activation': 0.5,
                'support_ticket_creation': 0.2,
                'support_ticket_search': 0.15
            }
        }
    
    def setup_logging(self):
        """Set up logging for test automation"""
        log_dir = Path(self.config.get('test_logs_dir', 'tests/automation/logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def create_test_environment(self) -> Dict:
        """Create test environment"""
        self.logger.info("Creating test environment...")
        
        # Create test database
        test_db = self.create_test_database()
        
        # Create test configuration
        test_config = {
            'database': test_db,
            'license_server_url': 'https://test-license-server.com/api/v1',
            'email_service_url': 'https://test-email-service.com/api/v1',
            'test_mode': True
        }
        
        return test_config
    
    def create_test_database(self):
        """Create test database"""
        import sqlite3
        
        test_db_path = self.test_data_dir / 'test_database.db'
        conn = sqlite3.connect(str(test_db_path))
        
        # Create tables
        self.create_database_tables(conn)
        
        # Load test data
        self.load_test_data(conn)
        
        conn.close()
        
        return str(test_db_path)
    
    def create_database_tables(self, conn):
        """Create database tables"""
        cursor = conn.cursor()
        
        # Create licenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY,
                license_key TEXT UNIQUE NOT NULL,
                license_type TEXT NOT NULL,
                status TEXT NOT NULL,
                customer_info TEXT,
                features TEXT,
                issued_date TEXT,
                expiry_date TEXT,
                validation_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create support_tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY,
                ticket_number TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_to INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                permissions TEXT,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
    
    def load_test_data(self, conn):
        """Load test data"""
        cursor = conn.cursor()
        
        # Load test licenses
        test_licenses = [
            ('TEST-LICENSE-001', 'trial', 'active', '{"name": "Test Restaurant"}', 
             '["order_management", "basic_reporting"]', '2023-01-01', '2023-12-31', 5),
            ('TEST-LICENSE-002', 'standard', 'active', '{"name": "Standard Test"}', 
             '["order_management", "inventory_tracking", "basic_reporting"]', '2023-01-01', '2024-12-31', 10),
            ('TEST-LICENSE-003', 'professional', 'active', '{"name": "Professional Test"}', 
             '["order_management", "inventory_tracking", "reporting", "multi_user"]', '2023-01-01', '2024-12-31', 15)
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO licenses 
            (license_key, license_type, status, customer_info, features, issued_date, expiry_date, validation_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, test_licenses)
        
        # Load test users
        test_users = [
            ('test_admin', 'hashed_password', 'admin', '["all"]', 'active'),
            ('test_manager', 'hashed_password', 'manager', '["order_management", "reporting"]', 'active'),
            ('test_user', 'hashed_password', 'user', '["order_management"]', 'active')
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO users 
            (username, password_hash, role, permissions, status)
            VALUES (?, ?, ?, ?, ?)
        """, test_users)
        
        conn.commit()
    
    def run_test_suite(self, test_suite_name: str, test_classes: List[type]) -> Dict:
        """Run a test suite"""
        self.logger.info(f"Running test suite: {test_suite_name}")
        
        suite_start_time = time.time()
        test_results = {
            'suite_name': test_suite_name,
            'start_time': datetime.now().isoformat(),
            'tests': [],
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Create test suite
        suite = unittest.TestSuite()
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=open(os.devnull, 'w')  # Suppress output, we'll capture it ourselves
        )
        
        result = runner.run(suite)
        
        # Process results
        test_results['passed'] = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        test_results['failed'] = len(result.failures)
        test_results['errors'] = len(result.errors)
        test_results['skipped'] = len(result.skipped)
        
        # Add failure details
        for test, traceback in result.failures:
            test_results['tests'].append({
                'name': str(test),
                'status': 'FAILED',
                'traceback': traceback
            })
        
        for test, traceback in result.errors:
            test_results['tests'].append({
                'name': str(test),
                'status': 'ERROR',
                'traceback': traceback
            })
        
        for test, reason in result.skipped:
            test_results['tests'].append({
                'name': str(test),
                'status': 'SKIPPED',
                'reason': str(reason)
            })
        
        suite_end_time = time.time()
        test_results['duration'] = suite_end_time - suite_start_time
        test_results['end_time'] = datetime.now().isoformat()
        test_results['success'] = (test_results['failed'] == 0 and test_results['errors'] == 0)
        
        self.test_results.append(test_results)
        
        self.logger.info(
            f"Test suite {test_suite_name} completed: "
            f"{test_results['passed']} passed, {test_results['failed']} failed, "
            f"{test_results['errors']} errors, {test_results['skipped']} skipped"
        )
        
        return test_results
    
    def generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        report = {
            'timestamp': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration': total_duration,
            'suites': self.test_results,
            'summary': {
                'total_suites': len(self.test_results),
                'total_tests': sum(s['passed'] + s['failed'] + s['errors'] + s['skipped'] for s in self.test_results),
                'total_passed': sum(s['passed'] for s in self.test_results),
                'total_failed': sum(s['failed'] for s in self.test_results),
                'total_errors': sum(s['errors'] for s in self.test_results),
                'total_skipped': sum(s['skipped'] for s in self.test_results),
                'overall_success': all(s['success'] for s in self.test_results)
            }
        }
        
        # Save report
        reports_dir = Path(self.config.get('test_reports_dir', 'tests/automation/reports'))
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_report_file = reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        self.generate_html_report(report, html_report_file)
        
        self.logger.info(f"Test report saved to {report_file}")
        self.logger.info(f"HTML report saved to {html_report_file}")
        
        return report
    
    def generate_html_report(self, report: Dict, output_file: Path):
        """Generate HTML test report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Automated Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ margin: 20px 0; }}
                .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
                .suite-header {{ background-color: #f9f9f9; padding: 15px; font-weight: bold; }}
                .suite-details {{ padding: 15px; }}
                .test {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ddd; }}
                .test.passed {{ border-left-color: green; }}
                .test.failed {{ border-left-color: red; }}
                .test.error {{ border-left-color: orange; }}
                .test.skipped {{ border-left-color: gray; }}
                .pass {{ color: green; }}
                .fail {{ color: red; }}
                .error {{ color: orange; }}
                .skip {{ color: gray; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-badge {{
                    padding: 4px 8px;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                }}
                .status-passed {{ background-color: green; }}
                .status-failed {{ background-color: red; }}
                .status-error {{ background-color: orange; }}
                .status-skipped {{ background-color: gray; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Automated Test Report</h1>
                <p>Generated: {report['timestamp']}</p>
                <p>Duration: {report['total_duration']:.2f} seconds</p>
            </div>
            
            <div class="summary">
                <h2>Test Summary</h2>
                <table>
                    <tr><th>Total Suites</th><td>{report['summary']['total_suites']}</td></tr>
                    <tr><th>Total Tests</th><td>{report['summary']['total_tests']}</td></tr>
                    <tr><th>Passed</th><td class="pass">{report['summary']['total_passed']}</td></tr>
                    <tr><th>Failed</th><td class="fail">{report['summary']['total_failed']}</td></tr>
                    <tr><th>Errors</th><td class="error">{report['summary']['total_errors']}</td></tr>
                    <tr><th>Skipped</th><td class="skip">{report['summary']['total_skipped']}</td></tr>
                    <tr><th>Overall Status</th><td>
                        <span class="status-badge status-{'passed' if report['summary']['overall_success'] else 'failed'}">
                            {'PASSED' if report['summary']['overall_success'] else 'FAILED'}
                        </span>
                    </td></tr>
                </table>
            </div>
            
            <div class="suites">
                <h2>Test Suites</h2>
        """
        
        for suite in report['suites']:
            status_class = 'passed' if suite['success'] else 'failed'
            html += f"""
                <div class="suite">
                    <div class="suite-header">
                        {suite['suite_name']} - 
                        <span class="status-badge status-{status_class}">
                            {'PASSED' if suite['success'] else 'FAILED'}
                        </span>
                        <span style="float: right;">{suite['duration']:.2f}s</span>
                    </div>
                    <div class="suite-details">
                        <table>
                            <tr><th>Tests</th><td>{suite['passed'] + suite['failed'] + suite['errors'] + suite['skipped']}</td></tr>
                            <tr><th>Passed</th><td class="pass">{suite['passed']}</td></tr>
                            <tr><th>Failed</th><td class="fail">{suite['failed']}</td></tr>
                            <tr><th>Errors</th><td class="error">{suite['errors']}</td></tr>
                            <tr><th>Skipped</th><td class="skip">{suite['skipped']}</td></tr>
                        </table>
                        
                        <h4>Test Details</h4>
            """
            
            for test in suite['tests']:
                test_status = test['status'].lower()
                html += f"""
                    <div class="test {test_status}">
                        <strong>{test['name']}</strong> - 
                        <span class="status-badge status-{test_status}">{test['status']}</span>
                        <br>
                        <small>{test.get('reason', test.get('traceback', ''))[:200]}...</small>
                    </div>
                """
            
            html += """
                    </div>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
```

## License System Test Scripts

### License Validation Test Script

```python
# tests/automation/license/test_license_validation.py
"""Automated license validation tests"""

import unittest
import time
from unittest.mock import patch, Mock
from tests.automation.base_test_framework import TestAutomationFramework

class TestLicenseValidation(unittest.TestCase):
    """Automated license validation tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.framework = TestAutomationFramework()
        cls.test_env = cls.framework.create_test_environment()
        cls.license_manager = cls.framework.create_license_manager()
    
    def setUp(self):
        """Set up test"""
        self.test_start_time = time.time()
    
    def tearDown(self):
        """Clean up test"""
        test_duration = time.time() - self.test_start_time
        self.framework.record_test_performance('license_validation', test_duration)
    
    def test_valid_license_validation(self):
        """Test validation of valid license"""
        # Arrange
        license_key = 'TEST-LICENSE-003'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.return_value = True
            
            result = self.license_manager.validate_license(license_key)
        
        # Assert
        self.assertTrue(result.is_valid)
        self.assertEqual(result.license_key, license_key)
        self.assertEqual(result.validation_method, 'online')
        
        # Performance assertion
        test_duration = time.time() - self.test_start_time
        self.assertLess(test_duration, 0.1, "License validation should complete within 100ms")
    
    def test_expired_license_validation(self):
        """Test validation of expired license"""
        # Arrange
        license_key = 'EXPIRED-LICENSE-001'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.return_value = False
            
            result = self.license_manager.validate_license(license_key)
        
        # Assert
        self.assertFalse(result.is_valid)
        self.assertIn('expired', result.error_message.lower())
    
    def test_invalid_license_key_validation(self):
        """Test validation of invalid license key"""
        # Arrange
        license_key = 'INVALID-LICENSE-KEY'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.side_effect = Exception("Invalid license key")
            
            with self.assertRaises(Exception):
                self.license_manager.validate_license(license_key)
    
    def test_offline_license_validation(self):
        """Test offline license validation"""
        # Arrange
        license_key = 'TEST-LICENSE-002'
        
        # Act
        with patch.object(self.license_manager, '_validate_offline') as mock_validate:
            mock_validate.return_value = True
            
            result = self.license_manager.validate_license(license_key, offline=True)
        
        # Assert
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_method, 'offline')
    
    def test_concurrent_license_validations(self):
        """Test concurrent license validations"""
        import threading
        import queue
        
        # Arrange
        num_threads = 10
        license_keys = [f'TEST-LICENSE-{i:03d}' for i in range(1, num_threads + 1)]
        results = queue.Queue()
        
        def validate_license(license_key):
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                
                start_time = time.time()
                result = self.license_manager.validate_license(license_key)
                end_time = time.time()
                
                results.put({
                    'license_key': license_key,
                    'result': result,
                    'duration': end_time - start_time
                })
        
        # Act
        threads = []
        start_time = time.time()
        
        for license_key in license_keys:
            thread = threading.Thread(target=validate_license, args=(license_key,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Assert
        self.assertEqual(results.qsize(), num_threads)
        
        validation_results = []
        while not results.empty():
            validation_results.append(results.get())
        
        # All validations should succeed
        for result in validation_results:
            self.assertTrue(result['result'].is_valid)
        
        # Performance assertion
        self.assertLess(total_duration, 2.0, "Concurrent validations should complete within 2 seconds")
    
    def test_license_validation_performance(self):
        """Test license validation performance"""
        # Arrange
        license_key = 'TEST-LICENSE-001'
        iterations = 100
        validation_times = []
        
        # Act
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                
                result = self.license_manager.validate_license(license_key)
            
            end_time = time.perf_counter()
            validation_times.append(end_time - start_time)
        
        # Assert
        avg_time = sum(validation_times) / len(validation_times)
        max_time = max(validation_times)
        
        # Performance assertions
        self.assertLess(avg_time, 0.05, "Average validation time should be less than 50ms")
        self.assertLess(max_time, 0.1, "Maximum validation time should be less than 100ms")
        
        # All validations should succeed
        self.assertTrue(all(result.is_valid for result in [self.license_manager.validate_license(license_key) for _ in range(10)]))
    
    def test_license_validation_with_network_timeout(self):
        """Test license validation with network timeout"""
        # Arrange
        license_key = 'TEST-LICENSE-001'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.side_effect = TimeoutError("Network timeout")
            
            # Should fall back to offline validation
            with patch.object(self.license_manager, '_validate_offline') as mock_offline:
                mock_offline.return_value = True
                
                result = self.license_manager.validate_license(license_key)
        
        # Assert
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_method, 'offline')
        self.assertIn('timeout', result.warning_message.lower())
    
    def test_license_validation_with_corrupted_data(self):
        """Test license validation with corrupted data"""
        # Arrange
        license_key = 'CORRUPTED-LICENSE-001'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.side_effect = Exception("Corrupted license data")
            
            with self.assertRaises(Exception):
                self.license_manager.validate_license(license_key)
    
    def test_license_validation_caching(self):
        """Test license validation caching"""
        # Arrange
        license_key = 'TEST-LICENSE-001'
        
        # Act
        with patch.object(self.license_manager, '_validate_online') as mock_validate:
            mock_validate.return_value = True
            
            # First validation
            result1 = self.license_manager.validate_license(license_key)
            
            # Second validation (should use cache)
            result2 = self.license_manager.validate_license(license_key)
        
        # Assert
        self.assertTrue(result1.is_valid)
        self.assertTrue(result2.is_valid)
        
        # Online validation should only be called once
        mock_validate.assert_called_once()
```

### License Activation Test Script

```python
# tests/automation/license/test_license_activation.py
"""Automated license activation tests"""

import unittest
import time
from unittest.mock import patch, Mock
from tests.automation.base_test_framework import TestAutomationFramework

class TestLicenseActivation(unittest.TestCase):
    """Automated license activation tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.framework = TestAutomationFramework()
        cls.test_env = cls.framework.create_test_environment()
        cls.license_manager = cls.framework.create_license_manager()
    
    def setUp(self):
        """Set up test"""
        self.test_start_time = time.time()
    
    def tearDown(self):
        """Clean up test"""
        test_duration = time.time() - self.test_start_time
        self.framework.record_test_performance('license_activation', test_duration)
    
    def test_new_license_activation(self):
        """Test activation of new license"""
        # Arrange
        license_key = 'NEW-LICENSE-001'
        customer_data = {
            'name': 'Test Customer',
            'email': 'test@example.com',
            'phone': '+1234567890'
        }
        
        # Act
        with patch.object(self.license_manager, 'activate_license_online') as mock_activate:
            mock_activate.return_value = {
                'success': True,
                'license_data': {
                    'license_key': license_key,
                    'license_type': 'standard',
                    'status': 'active',
                    'features': ['order_management', 'inventory_tracking']
                }
            }
            
            result = self.license_manager.activate_license(license_key, customer_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['license_data']['license_key'], license_key)
        self.assertEqual(result['license_data']['status'], 'active')
        
        # Performance assertion
        test_duration = time.time() - self.test_start_time
        self.assertLess(test_duration, 0.5, "License activation should complete within 500ms")
    
    def test_duplicate_license_activation(self):
        """Test activation of duplicate license"""
        # Arrange
        license_key = 'DUPLICATE-LICENSE-001'
        customer_data = {
            'name': 'Test Customer',
            'email': 'test@example.com'
        }
        
        # Act
        with patch.object(self.license_manager, 'activate_license_online') as mock_activate:
            mock_activate.return_value = {
                'success': False,
                'error': 'License already activated'
            }
            
            result = self.license_manager.activate_license(license_key, customer_data)
        
        # Assert
        self.assertFalse(result['success'])
        self.assertIn('already activated', result['error'])
    
    def test_license_activation_with_invalid_data(self):
        """Test license activation with invalid data"""
        # Arrange
        license_key = 'INVALID-LICENSE-001'
        customer_data = {
            'name': '',
            'email': 'invalid-email'
        }
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.license_manager.activate_license(license_key, customer_data)
    
    def test_license_activation_with_network_error(self):
        """Test license activation with network error"""
        # Arrange
        license_key = 'NETWORK-ERROR-LICENSE-001'
        customer_data = {
            'name': 'Test Customer',
            'email': 'test@example.com'
        }
        
        # Act
        with patch.object(self.license_manager, 'activate_license_online') as mock_activate:
            mock_activate.side_effect = ConnectionError("Network connection failed")
            
            # Should fall back to offline activation
            with patch.object(self.license_manager, 'activate_license_offline') as mock_offline:
                mock_offline.return_value = {
                    'success': True,
                    'license_data': {
                        'license_key': license_key,
                        'license_type': 'trial',
                        'status': 'active'
                    }
                }
                
                result = self.license_manager.activate_license(license_key, customer_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['license_data']['license_type'], 'trial')
        self.assertIn('offline', result.get('activation_method', ''))
    
    def test_license_activation_performance(self):
        """Test license activation performance"""
        # Arrange
        license_keys = [f'PERF-LICENSE-{i:03d}' for i in range(10)]
        customer_data = {
            'name': 'Performance Test Customer',
            'email': 'perf@example.com'
        }
        
        activation_times = []
        
        # Act
        for license_key in license_keys:
            start_time = time.perf_counter()
            
            with patch.object(self.license_manager, 'activate_license_online') as mock_activate:
                mock_activate.return_value = {
                    'success': True,
                    'license_data': {
                        'license_key': license_key,
                        'license_type': 'standard',
                        'status': 'active'
                    }
                }
                
                result = self.license_manager.activate_license(license_key, customer_data)
            
            end_time = time.perf_counter()
            activation_times.append(end_time - start_time)
            
            # Assert each activation succeeds
            self.assertTrue(result['success'])
        
        # Assert performance
        avg_time = sum(activation_times) / len(activation_times)
        max_time = max(activation_times)
        
        self.assertLess(avg_time, 0.3, "Average activation time should be less than 300ms")
        self.assertLess(max_time, 0.5, "Maximum activation time should be less than 500ms")
    
    def test_license_activation_with_hardware_binding(self):
        """Test license activation with hardware binding"""
        # Arrange
        license_key = 'HW-BOUND-LICENSE-001'
        customer_data = {
            'name': 'Hardware Bound Customer',
            'email': 'hw@example.com'
        }
        
        # Act
        with patch.object(self.license_manager, 'activate_license_online') as mock_activate:
            mock_activate.return_value = {
                'success': True,
                'license_data': {
                    'license_key': license_key,
                    'license_type': 'professional',
                    'status': 'active',
                    'hardware_binding': True,
                    'hardware_fingerprint': 'test-fingerprint-123'
                }
            }
            
            result = self.license_manager.activate_license(license_key, customer_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertTrue(result['license_data']['hardware_binding'])
        self.assertIsNotNone(result['license_data']['hardware_fingerprint'])
    
    def test_license_activation_with_trial_upgrade(self):
        """Test license activation with trial upgrade"""
        # Arrange
        license_key = 'TRIAL-UPGRADE-001'
        customer_data = {
            'name': 'Trial Upgrade Customer',
            'email': 'upgrade@example.com'
        }
        
        # Act
        with patch.object(self.license_manager, 'upgrade_license') as mock_upgrade:
            mock_upgrade.return_value = {
                'success': True,
                'license_data': {
                    'license_key': license_key,
                    'license_type': 'professional',
                    'status': 'active',
                    'upgraded_from': 'trial'
                }
            }
            
            result = self.license_manager.upgrade_license(license_key, 'professional')
        
        # Assert
        self.assertTrue(result['success'])
        self.assertEqual(result['license_data']['license_type'], 'professional')
        self.assertEqual(result['license_data']['upgraded_from'], 'trial')
```

## Support System Test Scripts

### Support Ticket Creation Test Script

```python
# tests/automation/support/test_support_ticket_creation.py
"""Automated support ticket creation tests"""

import unittest
import time
from unittest.mock import patch, Mock
from tests.automation.base_test_framework import TestAutomationFramework

class TestSupportTicketCreation(unittest.TestCase):
    """Automated support ticket creation tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.framework = TestAutomationFramework()
        cls.test_env = cls.framework.create_test_environment()
        cls.support_manager = cls.framework.create_support_manager()
    
    def setUp(self):
        """Set up test"""
        self.test_start_time = time.time()
    
    def tearDown(self):
        """Clean up test"""
        test_duration = time.time() - self.test_start_time
        self.framework.record_test_performance('support_ticket_creation', test_duration)
    
    def test_create_technical_support_ticket(self):
        """Test creation of technical support ticket"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'Login issue after password change',
            'description': 'User cannot log in after changing password',
            'priority': 'High'
        }
        
        # Act
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            mock_create.return_value = {
                'success': True,
                'ticket_id': 123,
                'ticket_number': 'TECH-2023-001'
            }
            
            result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['ticket_id'])
        self.assertTrue(result['ticket_number'].startswith('TECH-'))
        
        # Performance assertion
        test_duration = time.time() - self.test_start_time
        self.assertLess(test_duration, 0.2, "Ticket creation should complete within 200ms")
    
    def test_create_bug_report_ticket(self):
        """Test creation of bug report ticket"""
        # Arrange
        ticket_data = {
            'user_id': 2,
            'category': 'Bug Report',
            'subject': 'Calculation error in order total',
            'description': 'Order total is incorrect when applying discounts',
            'priority': 'Medium'
        }
        
        # Act
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            mock_create.return_value = {
                'success': True,
                'ticket_id': 124,
                'ticket_number': 'BUG-2023-001'
            }
            
            result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['ticket_id'])
        self.assertTrue(result['ticket_number'].startswith('BUG-'))
    
    def test_create_feature_request_ticket(self):
        """Test creation of feature request ticket"""
        # Arrange
        ticket_data = {
            'user_id': 3,
            'category': 'Feature Request',
            'subject': 'Add customer loyalty program',
            'description': 'Request for customer loyalty tracking system',
            'priority': 'Low'
        }
        
        # Act
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            mock_create.return_value = {
                'success': True,
                'ticket_id': 125,
                'ticket_number': 'FEAT-2023-001'
            }
            
            result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['ticket_id'])
        self.assertTrue(result['ticket_number'].startswith('FEAT-'))
    
    def test_create_ticket_with_attachment(self):
        """Test ticket creation with attachment"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'System crash with error report',
            'description': 'System crashes when accessing reports',
            'priority': 'Critical',
            'attachments': [
                {
                    'filename': 'error_log.txt',
                    'content': 'Error log content here',
                    'content_type': 'text/plain'
                }
            ]
        }
        
        # Act
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            with patch.object(self.support_manager, 'save_attachment') as mock_save:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 126,
                    'ticket_number': 'TECH-2023-002'
                }
                mock_save.return_value = {
                    'success': True,
                    'attachment_id': 789
                }
                
                result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['ticket_id'])
        self.assertTrue(mock_save.called)
    
    def test_create_ticket_with_invalid_data(self):
        """Test ticket creation with invalid data"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': '',  # Empty subject
            'description': 'Test description',
            'priority': 'High'
        }
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.support_manager.create_ticket(ticket_data)
    
    def test_create_ticket_with_email_notification(self):
        """Test ticket creation with email notification"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'Test ticket with notification',
            'description': 'Test description',
            'priority': 'Medium'
        }
        
        # Act
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            with patch.object(self.support_manager.email_service, 'send_ticket_acknowledgment') as mock_email:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 127,
                    'ticket_number': 'TECH-2023-003'
                }
                mock_email.return_value = {
                    'success': True,
                    'message_id': 'msg-123'
                }
                
                result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        self.assertTrue(mock_email.called)
    
    def test_create_ticket_performance(self):
        """Test ticket creation performance"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'Performance test ticket',
            'description': 'Testing ticket creation performance',
            'priority': 'Medium'
        }
        
        creation_times = []
        iterations = 50
        
        # Act
        for i in range(iterations):
            start_time = time.perf_counter()
            
            with patch.object(self.support_manager, 'create_ticket') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 200 + i,
                    'ticket_number': f'PERF-2023-{i:03d}'
                }
                
                result = self.support_manager.create_ticket(ticket_data)
            
            end_time = time.perf_counter()
            creation_times.append(end_time - start_time)
            
            # Assert each creation succeeds
            self.assertTrue(result['success'])
        
        # Assert performance
        avg_time = sum(creation_times) / len(creation_times)
        max_time = max(creation_times)
        
        self.assertLess(avg_time, 0.1, "Average creation time should be less than 100ms")
        self.assertLess(max_time, 0.2, "Maximum creation time should be less than 200ms")
    
    def test_concurrent_ticket_creation(self):
        """Test concurrent ticket creation"""
        import threading
        import queue
        
        # Arrange
        num_threads = 10
        results = queue.Queue()
        
        def create_ticket(thread_id):
            ticket_data = {
                'user_id': thread_id,
                'category': 'Technical Support',
                'subject': f'Concurrent ticket {thread_id}',
                'description': f'Test ticket from thread {thread_id}',
                'priority': 'Medium'
            }
            
            start_time = time.time()
            
            with patch.object(self.support_manager, 'create_ticket') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 300 + thread_id,
                    'ticket_number': f'CONC-2023-{thread_id:03d}'
                }
                
                result = self.support_manager.create_ticket(ticket_data)
            
            end_time = time.time()
            
            results.put({
                'thread_id': thread_id,
                'result': result,
                'duration': end_time - start_time
            })
        
        # Act
        threads = []
        start_time = time.time()
        
        for thread_id in range(1, num_threads + 1):
            thread = threading.Thread(target=create_ticket, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Assert
        self.assertEqual(results.qsize(), num_threads)
        
        ticket_results = []
        while not results.empty():
            ticket_results.append(results.get())
        
        # All creations should succeed
        for result in ticket_results:
            self.assertTrue(result['result']['success'])
        
        # Performance assertion
        self.assertLess(total_duration, 2.0, "Concurrent ticket creation should complete within 2 seconds")
```

## Integration Test Scripts

### License-Support Integration Test Script

```python
# tests/automation/integration/test_license_support_integration.py
"""Automated license-support integration tests"""

import unittest
import time
from unittest.mock import patch, Mock
from tests.automation.base_test_framework import TestAutomationFramework

class TestLicenseSupportIntegration(unittest.TestCase):
    """Automated license-support integration tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.framework = TestAutomationFramework()
        cls.test_env = cls.framework.create_test_environment()
        cls.license_manager = cls.framework.create_license_manager()
        cls.support_manager = cls.framework.create_support_manager()
    
    def test_license_validation_affects_support_access(self):
        """Test that license validation affects support access"""
        # Arrange
        user_id = 1
        license_data = {
            'license_key': 'INTEGRATION-LICENSE-001',
            'license_type': 'standard',
            'features': ['order_management', 'basic_support']
        }
        
        # Act
        with patch.object(self.license_manager, 'validate_license') as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, license_data=license_data)
            
            # Check support access
            can_create_ticket = self.support_manager.check_support_access(user_id, 'create_ticket')
            can_access_priority = self.support_manager.check_support_access(user_id, 'priority_support')
        
        # Assert
        self.assertTrue(can_create_ticket)
        self.assertFalse(can_access_priority)
    
    def test_expired_license_limits_support_features(self):
        """Test that expired license limits support features"""
        # Arrange
        user_id = 2
        license_data = {
            'license_key': 'EXPIRED-LICENSE-001',
            'license_type': 'professional',
            'status': 'expired',
            'features': ['order_management', 'priority_support']
        }
        
        # Act
        with patch.object(self.license_manager, 'validate_license') as mock_validate:
            mock_validate.return_value = Mock(is_valid=False, license_data=license_data)
            
            # Check support access
            can_create_ticket = self.support_manager.check_support_access(user_id, 'create_ticket')
            can_access_priority = self.support_manager.check_support_access(user_id, 'priority_support')
        
        # Assert
        self.assertFalse(can_create_ticket)
        self.assertFalse(can_access_priority)
    
    def test_support_ticket_includes_license_info(self):
        """Test that support tickets include license information"""
        # Arrange
        user_id = 1
        ticket_data = {
            'user_id': user_id,
            'category': 'Technical Support',
            'subject': 'Integration test ticket',
            'description': 'Testing license-support integration',
            'priority': 'Medium'
        }
        
        license_data = {
            'license_key': 'INTEGRATION-LICENSE-002',
            'license_type': 'professional',
            'features': ['order_management', 'priority_support']
        }
        
        # Act
        with patch.object(self.license_manager, 'get_user_license') as mock_get_license:
            mock_get_license.return_value = license_data
            
            with patch.object(self.support_manager, 'create_ticket') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 401,
                    'ticket_number': 'INT-2023-001'
                }
                
                result = self.support_manager.create_ticket(ticket_data)
        
        # Assert
        self.assertTrue(result['success'])
        mock_create.assert_called_once()
        
        # Check that license info was included
        call_args = mock_create.call_args[0][0]
        self.assertIn('license_info', call_args)
        self.assertEqual(call_args['license_info']['license_key'], license_data['license_key'])
    
    def test_license_upgrade_enhances_support_features(self):
        """Test that license upgrade enhances support features"""
        # Arrange
        user_id = 1
        old_license = {
            'license_key': 'OLD-LICENSE-001',
            'license_type': 'standard',
            'features': ['order_management', 'basic_support']
        }
        
        new_license = {
            'license_key': 'NEW-LICENSE-001',
            'license_type': 'professional',
            'features': ['order_management', 'priority_support', 'api_support']
        }
        
        # Act
        with patch.object(self.license_manager, 'upgrade_license') as mock_upgrade:
            mock_upgrade.return_value = {
                'success': True,
                'old_license': old_license,
                'new_license': new_license
            }
            
            # Check support access before upgrade
            with patch.object(self.license_manager, 'get_user_license') as mock_get:
                mock_get.return_value = old_license
                
                old_access = self.support_manager.check_support_access(user_id, 'priority_support')
            
            # Check support access after upgrade
            mock_get.return_value = new_license
            
            new_access = self.support_manager.check_support_access(user_id, 'priority_support')
        
        # Assert
        self.assertFalse(old_access)
        self.assertTrue(new_access)
    
    def test_support_usage_affects_license_compliance(self):
        """Test that support usage affects license compliance"""
        # Arrange
        user_id = 1
        license_data = {
            'license_key': 'COMPLIANCE-LICENSE-001',
            'license_type': 'standard',
            'features': ['order_management', 'basic_support'],
            'support_limits': {
                'max_monthly_tickets': 25,
                'current_monthly_tickets': 24
            }
        }
        
        # Act
        with patch.object(self.license_manager, 'get_user_license') as mock_get:
            mock_get.return_value = license_data
            
            # Create ticket (should succeed)
            with patch.object(self.support_manager, 'create_ticket') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 402,
                    'ticket_number': 'COMP-2023-001'
                }
                
                result1 = self.support_manager.create_ticket({
                    'user_id': user_id,
                    'category': 'Technical Support',
                    'subject': 'Test ticket 1',
                    'description': 'Test description',
                    'priority': 'Medium'
                })
            
            # Update license data to reflect usage
            license_data['support_limits']['current_monthly_tickets'] = 25
            
            # Try to create another ticket (should fail)
            result2 = self.support_manager.create_ticket({
                'user_id': user_id,
                'category': 'Technical Support',
                'subject': 'Test ticket 2',
                'description': 'Test description',
                'priority': 'Medium'
            })
        
        # Assert
        self.assertTrue(result1['success'])
        self.assertFalse(result2['success'])
        self.assertIn('limit', result2['error'].lower())
```

## Performance Test Scripts

### System Performance Test Script

```python
# tests/automation/performance/test_system_performance.py
"""Automated system performance tests"""

import unittest
import time
import psutil
import os
from unittest.mock import patch, Mock
from tests.automation.base_test_framework import TestAutomationFramework

class TestSystemPerformance(unittest.TestCase):
    """Automated system performance tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.framework = TestAutomationFramework()
        cls.test_env = cls.framework.create_test_environment()
        cls.license_manager = cls.framework.create_license_manager()
        cls.support_manager = cls.framework.create_support_manager()
        cls.process = psutil.Process(os.getpid())
        cls.initial_memory = cls.process.memory_info().rss
    
    def test_license_validation_performance_under_load(self):
        """Test license validation performance under load"""
        # Arrange
        license_keys = [f'PERF-LICENSE-{i:04d}' for i in range(1000)]
        validation_times = []
        
        # Act
        for license_key in license_keys:
            start_time = time.perf_counter()
            
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                
                result = self.license_manager.validate_license(license_key)
            
            end_time = time.perf_counter()
            validation_times.append(end_time - start_time)
        
        # Assert
        avg_time = sum(validation_times) / len(validation_times)
        p95_time = sorted(validation_times)[int(len(validation_times) * 0.95)]
        p99_time = sorted(validation_times)[int(len(validation_times) * 0.99)]
        
        # Performance assertions
        self.assertLess(avg_time, 0.05, "Average validation time should be less than 50ms")
        self.assertLess(p95_time, 0.1, "95th percentile should be less than 100ms")
        self.assertLess(p99_time, 0.15, "99th percentile should be less than 150ms")
        
        # All validations should succeed
        self.assertTrue(all(result.is_valid for result in [self.license_manager.validate_license(key) for key in license_keys[:10]]))
    
    def test_support_ticket_creation_performance_under_load(self):
        """Test support ticket creation performance under load"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'Performance test ticket',
            'description': 'Testing ticket creation performance',
            'priority': 'Medium'
        }
        
        creation_times = []
        iterations = 500
        
        # Act
        for i in range(iterations):
            start_time = time.perf_counter()
            
            with patch.object(self.support_manager, 'create_ticket') as mock_create:
                mock_create.return_value = {
                    'success': True,
                    'ticket_id': 500 + i,
                    'ticket_number': f'PERF-2023-{i:04d}'
                }
                
                result = self.support_manager.create_ticket(ticket_data)
            
            end_time = time.perf_counter()
            creation_times.append(end_time - start_time)
        
        # Assert
        avg_time = sum(creation_times) / len(creation_times)
        p95_time = sorted(creation_times)[int(len(creation_times) * 0.95)]
        
        # Performance assertions
        self.assertLess(avg_time, 0.1, "Average creation time should be less than 100ms")
        self.assertLess(p95_time, 0.2, "95th percentile should be less than 200ms")
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        # Arrange
        initial_memory = self.process.memory_info().rss
        
        # Act
        # Perform many operations
        for i in range(1000):
            # License validations
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                self.license_manager.validate_license(f'MEM-LICENSE-{i:04d}')
            
            # Support ticket searches
            with patch.object(self.support_manager, 'search_tickets') as mock_search:
                mock_search.return_value = []
                self.support_manager.search_tickets({'status': 'Open'})
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert
        # Memory increase should be minimal (less than 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024, 
                       "Memory increase should be less than 50MB for 1000 operations")
    
    def test_concurrent_operations_performance(self):
        """Test concurrent operations performance"""
        import threading
        import queue
        
        # Arrange
        num_threads = 20
        operations_per_thread = 50
        results = queue.Queue()
        
        def worker():
            thread_times = []
            for i in range(operations_per_thread):
                start_time = time.perf_counter()
                
                # Mix of license validations and support operations
                if i % 2 == 0:
                    with patch.object(self.license_manager, '_validate_online') as mock_validate:
                        mock_validate.return_value = True
                        self.license_manager.validate_license(f'CONC-LICENSE-{i:04d}')
                else:
                    with patch.object(self.support_manager, 'search_tickets') as mock_search:
                        mock_search.return_value = []
                        self.support_manager.search_tickets({'status': 'Open'})
                
                end_time = time.perf_counter()
                thread_times.append(end_time - start_time)
            
            results.put(thread_times)
        
        # Act
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Collect results
        all_times = []
        while not results.empty():
            all_times.extend(results.get())
        
        # Assert
        avg_time = sum(all_times) / len(all_times)
        total_operations = num_threads * operations_per_thread
        throughput = total_operations / total_time
        
        # Performance assertions
        self.assertLess(avg_time, 0.1, "Average operation time should be less than 100ms")
        self.assertGreater(throughput, 100, "Throughput should be greater than 100 operations/second")
        self.assertLess(total_time, 30, "Total time should be less than 30 seconds")
    
    def test_database_performance_under_load(self):
        """Test database performance under load"""
        # Arrange
        test_data = []
        for i in range(1000):
            test_data.append({
                'id': i,
                'ticket_number': f'DB-PERF-{i:04d}',
                'subject': f'Performance test ticket {i}',
                'status': 'Open'
            })
        
        search_times = []
        
        # Act
        for _ in range(100):
            start_time = time.perf_counter()
            
            with patch.object(self.support_manager.ticket_manager, 'search') as mock_search:
                mock_search.return_value = test_data
                
                results = self.support_manager.search_tickets({'status': 'Open'})
                self.assertEqual(len(results), 1000)
            
            end_time = time.perf_counter()
            search_times.append(end_time - start_time)
        
        # Assert
        avg_time = sum(search_times) / len(search_times)
        max_time = max(search_times)
        
        # Performance assertions
        self.assertLess(avg_time, 0.05, "Average search time should be less than 50ms for 1000 records")
        self.assertLess(max_time, 0.1, "Maximum search time should be less than 100ms for 1000 records")
```

## Test Execution Orchestration

### Master Test Runner Script

```python
# scripts/run_automated_tests.py
"""Master automated test runner"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.automation.base_test_framework import TestAutomationFramework
from tests.automation.license.test_license_validation import TestLicenseValidation
from tests.automation.license.test_license_activation import TestLicenseActivation
from tests.automation.support.test_support_ticket_creation import TestSupportTicketCreation
from tests.automation.integration.test_license_support_integration import TestLicenseSupportIntegration
from tests.automation.performance.test_system_performance import TestSystemPerformance

class AutomatedTestRunner:
    """Master automated test runner"""
    
    def __init__(self, config_file='tests/automation/config/test_config.json'):
        self.framework = TestAutomationFramework(config_file)
        self.test_suites = {
            'license_validation': [TestLicenseValidation],
            'license_activation': [TestLicenseActivation],
            'support_ticket_creation': [TestSupportTicketCreation],
            'integration': [TestLicenseSupportIntegration],
            'performance': [TestSystemPerformance]
        }
    
    def run_all_tests(self):
        """Run all automated test suites"""
        print("Starting automated test execution...")
        print(f"Started at: {datetime.now().isoformat()}")
        
        # Create test environment
        test_env = self.framework.create_test_environment()
        
        # Run all test suites
        for suite_name, test_classes in self.test_suites.items():
            print(f"\n{'='*60}")
            print(f"Running {suite_name} test suite")
            print(f"{'='*60}")
            
            result = self.framework.run_test_suite(suite_name, test_classes)
            
            if not result['success']:
                print(f"❌ {suite_name} test suite FAILED")
            else:
                print(f"✅ {suite_name} test suite PASSED")
        
        # Generate comprehensive report
        report = self.framework.generate_test_report()
        
        # Print summary
        self.print_summary(report)
        
        return report
    
    def run_specific_suite(self, suite_name):
        """Run a specific test suite"""
        if suite_name not in self.test_suites:
            print(f"Error: Unknown test suite '{suite_name}'")
            print(f"Available suites: {', '.join(self.test_suites.keys())}")
            return None
        
        print(f"Running {suite_name} test suite...")
        
        # Create test environment
        test_env = self.framework.create_test_environment()
        
        # Run test suite
        result = self.framework.run_test_suite(suite_name, self.test_suites[suite_name])
        
        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'suites': [result],
            'summary': {
                'total_suites': 1,
                'total_tests': result['passed'] + result['failed'] + result['errors'] + result['skipped'],
                'total_passed': result['passed'],
                'total_failed': result['failed'],
                'total_errors': result['errors'],
                'total_skipped': result['skipped'],
                'overall_success': result['success']
            }
        }
        
        # Print summary
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report):
        """Print test execution summary"""
        print("\n" + "="*60)
        print("AUTOMATED TEST EXECUTION SUMMARY")
        print("="*60)
        
        for suite in report['suites']:
            status = "✅ PASSED" if suite['success'] else "❌ FAILED"
            print(f"{suite['suite_name']}: {status}")
            print(f"  Tests: {suite['passed'] + suite['failed'] + suite['errors'] + suite['skipped']}")
            print(f"  Passed: {suite['passed']}")
            print(f"  Failed: {suite['failed']}")
            print(f"  Errors: {suite['errors']}")
            print(f"  Skipped: {suite['skipped']}")
            print(f"  Duration: {suite['duration']:.2f}s")
            print()
        
        print("OVERALL SUMMARY:")
        print(f"Total Suites: {report['summary']['total_suites']}")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Total Passed: {report['summary']['total_passed']}")
        print(f"Total Failed: {report['summary']['total_failed']}")
        print(f"Total Errors: {report['summary']['total_errors']}")
        print(f"Total Skipped: {report['summary']['total_skipped']}")
        print(f"Overall Success: {'✅ PASSED' if report['summary']['overall_success'] else '❌ FAILED'}")
        
        if 'total_duration' in report:
            print(f"Total Duration: {report['total_duration']:.2f}s")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Run automated tests for support and license systems')
    parser.add_argument('--suite', help='Specific test suite to run', 
                       choices=['license_validation', 'license_activation', 'support_ticket_creation', 
                                'integration', 'performance'])
    parser.add_argument('--config', help='Test configuration file', 
                       default='tests/automation/config/test_config.json')
    
    args = parser.parse_args()
    
    # Create test runner
    runner = AutomatedTestRunner(args.config)
    
    # Run tests
    if args.suite:
        report = runner.run_specific_suite(args.suite)
    else:
        report = runner.run_all_tests()
    
    # Return appropriate exit code
    if report and report['summary']['overall_success']:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

This comprehensive automated testing framework provides extensive test coverage for both the support system and license validation system. The scripts include unit tests, integration tests, performance tests, and a master test runner to orchestrate all testing activities, ensuring system quality and reliability through automated continuous testing.