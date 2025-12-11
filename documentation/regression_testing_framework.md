# Regression Testing Framework for Support and License Systems

## Overview

This document outlines a comprehensive regression testing framework designed to ensure that new changes to the support system and license validation system do not break existing functionality. The framework includes automated test suites, continuous integration procedures, and performance regression detection.

## Table of Contents

1. [Regression Testing Strategy](#regression-testing-strategy)
2. [Test Suite Organization](#test-suite-organization)
3. [Automated Test Execution](#automated-test-execution)
4. [Performance Regression Testing](#performance-regression-testing)
5. [Continuous Integration Pipeline](#continuous-integration-pipeline)
6. [Test Data Management](#test-data-management)
7. [Regression Test Prioritization](#regression-test-prioritization)
8. [Defect Classification and Analysis](#defect-classification-and-analysis)
9. [Reporting and Metrics](#reporting-and-metrics)
10. [Maintenance and Evolution](#maintenance-and-evolution)

## Regression Testing Strategy

### Objectives

1. **Detect Functional Regressions**: Identify when new code breaks existing functionality
2. **Detect Performance Regressions**: Identify when changes negatively impact system performance
3. **Ensure Backward Compatibility**: Verify that system changes maintain compatibility with previous versions
4. **Validate Integration Points**: Ensure changes don't break system integrations
5. **Maintain Quality Standards**: Uphold established quality benchmarks

### Testing Levels

1. **Smoke Tests**: Quick validation of critical functionality
2. **Core Functionality Tests**: In-depth testing of essential features
3. **Integration Tests**: Validation of system interactions
4. **Performance Tests**: Benchmarking and performance comparison
5. **Security Tests**: Security regression validation
6. **Compatibility Tests**: Backward and forward compatibility validation

### Regression Testing Types

1. **Build Regression Testing**: Validation after each build
2. **Feature Regression Testing**: Validation after feature implementation
3. **Release Regression Testing**: Comprehensive validation before release
4. **Production Regression Testing**: Validation in production-like environment

## Test Suite Organization

### Test Suite Structure

```
tests/regression/
├── smoke_tests/
│   ├── test_license_smoke.py
│   ├── test_support_smoke.py
│   └── test_integration_smoke.py
├── core_functionality/
│   ├── license/
│   │   ├── test_license_validation.py
│   │   ├── test_license_activation.py
│   │   ├── test_license_management.py
│   │   └── test_license_security.py
│   ├── support/
│   │   ├── test_ticket_creation.py
│   │   ├── test_ticket_management.py
│   │   ├── test_support_notifications.py
│   │   └── test_support_security.py
│   └── integration/
│       ├── test_license_support_integration.py
│       ├── test_database_integration.py
│       └── test_external_service_integration.py
├── performance/
│   ├── test_license_performance.py
│   ├── test_support_performance.py
│   ├── test_database_performance.py
│   └── test_ui_performance.py
├── security/
│   ├── test_license_security_regression.py
│   ├── test_support_security_regression.py
│   └── test_integration_security.py
├── compatibility/
│   ├── test_backward_compatibility.py
│   ├── test_forward_compatibility.py
│   └── test_api_compatibility.py
└── data/
    ├── test_scenarios.json
    ├── performance_baselines.json
    └── security_test_data.json
```

### Test Suite Base Classes

```python
# tests/regression/base_regression_test.py
"""Base class for regression tests"""

import unittest
import time
import json
import os
from datetime import datetime
from unittest.mock import patch, Mock

class BaseRegressionTest(unittest.TestCase):
    """Base class for all regression tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up regression test environment"""
        cls.test_data_dir = os.path.join(os.path.dirname(__file__), 'data')
        cls.performance_baselines = cls.load_performance_baselines()
        cls.test_scenarios = cls.load_test_scenarios()
        cls.start_time = datetime.now()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up regression test environment"""
        duration = datetime.now() - cls.start_time
        print(f"\n{cls.__name__} completed in {duration.total_seconds():.2f} seconds")
    
    def setUp(self):
        """Set up individual test"""
        self.test_start_time = time.time()
    
    def tearDown(self):
        """Clean up individual test"""
        test_duration = time.time() - self.test_start_time
        self.record_test_performance(test_duration)
    
    @classmethod
    def load_performance_baselines(cls):
        """Load performance baseline data"""
        baseline_file = os.path.join(cls.test_data_dir, 'performance_baselines.json')
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return {}
    
    @classmethod
    def load_test_scenarios(cls):
        """Load test scenario data"""
        scenario_file = os.path.join(cls.test_data_dir, 'test_scenarios.json')
        if os.path.exists(scenario_file):
            with open(scenario_file, 'r') as f:
                return json.load(f)
        return {}
    
    def record_test_performance(self, duration):
        """Record test performance for analysis"""
        test_name = self._testMethodName
        if test_name not in self.performance_baselines:
            self.performance_baselines[test_name] = []
        
        self.performance_baselines[test_name].append({
            'timestamp': datetime.now().isoformat(),
            'duration': duration
        })
    
    def assert_performance_baseline(self, metric_name, actual_value, tolerance=0.1):
        """Assert that performance meets baseline"""
        if metric_name in self.performance_baselines:
            baseline = self.performance_baselines[metric_name]
            if isinstance(baseline, dict) and 'average' in baseline:
                expected = baseline['average']
                deviation = abs(actual_value - expected) / expected
                self.assertLessEqual(deviation, tolerance, 
                    f"Performance regression detected: {metric_name} "
                    f"expected {expected:.3f}, got {actual_value:.3f} "
                    f"(deviation: {deviation:.1%})")
    
    def assert_no_regression(self, test_result, baseline_result):
        """Assert no regression compared to baseline"""
        if baseline_result is None:
            return  # No baseline to compare against
        
        if test_result != baseline_result:
            self.fail(f"Regression detected: expected {baseline_result}, got {test_result}")
    
    def create_test_app(self):
        """Create test application instance"""
        app = Mock()
        app.db = self.create_test_database()
        return app
    
    def create_test_database(self):
        """Create test database connection"""
        import sqlite3
        conn = sqlite3.connect(':memory:')
        self.create_test_tables(conn)
        return conn
    
    def create_test_tables(self, conn):
        """Create test database tables"""
        cursor = conn.cursor()
        
        # Create licenses table
        cursor.execute("""
            CREATE TABLE licenses (
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
            CREATE TABLE support_tickets (
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
            CREATE TABLE users (
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
```

## Automated Test Execution

### Regression Test Runner

```python
# scripts/run_regression_tests.py
"""Regression test runner"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class RegressionTestRunner:
    """Automated regression test runner"""
    
    def __init__(self):
        self.test_results = []
        self.performance_results = []
        self.start_time = datetime.now()
        self.test_dir = Path(__file__).parent.parent / 'tests' / 'regression'
    
    def run_smoke_tests(self):
        """Run smoke tests"""
        print("Running smoke tests...")
        smoke_dir = self.test_dir / 'smoke_tests'
        return self.run_test_directory(smoke_dir, 'Smoke Tests')
    
    def run_core_functionality_tests(self):
        """Run core functionality tests"""
        print("Running core functionality tests...")
        core_dir = self.test_dir / 'core_functionality'
        return self.run_test_directory(core_dir, 'Core Functionality')
    
    def run_performance_tests(self):
        """Run performance tests"""
        print("Running performance tests...")
        perf_dir = self.test_dir / 'performance'
        return self.run_test_directory(perf_dir, 'Performance')
    
    def run_security_tests(self):
        """Run security tests"""
        print("Running security tests...")
        security_dir = self.test_dir / 'security'
        return self.run_test_directory(security_dir, 'Security')
    
    def run_compatibility_tests(self):
        """Run compatibility tests"""
        print("Running compatibility tests...")
        compat_dir = self.test_dir / 'compatibility'
        return self.run_test_directory(compat_dir, 'Compatibility')
    
    def run_test_directory(self, test_dir, suite_name):
        """Run all tests in a directory"""
        if not test_dir.exists():
            return {
                'suite_name': suite_name,
                'test_count': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'duration': 0,
                'success': True
            }
        
        # Discover and run tests
        test_files = list(test_dir.glob('test_*.py'))
        test_count = 0
        passed = 0
        failed = 0
        errors = 0
        start_time = time.time()
        
        for test_file in test_files:
            result = self.run_test_file(test_file)
            test_count += result['test_count']
            passed += result['passed']
            failed += result['failed']
            errors += result['errors']
        
        duration = time.time() - start_time
        success = (failed == 0 and errors == 0)
        
        result = {
            'suite_name': suite_name,
            'test_count': test_count,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'duration': duration,
            'success': success
        }
        
        self.test_results.append(result)
        return result
    
    def run_test_file(self, test_file):
        """Run a single test file"""
        cmd = [sys.executable, '-m', 'unittest', str(test_file), '-v']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse output
        output_lines = result.stdout.split('\n')
        test_count = 0
        passed = 0
        failed = 0
        errors = 0
        
        for line in output_lines:
            if 'Ran' in line and 'tests' in line:
                parts = line.split()
                test_count = int(parts[1])
            if 'FAIL:' in line:
                failed += 1
            if 'ERROR:' in line:
                errors += 1
        
        passed = test_count - failed - errors
        
        return {
            'test_file': str(test_file),
            'test_count': test_count,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    
    def run_all_tests(self):
        """Run all regression tests"""
        print("Starting regression test suite...")
        print(f"Started at: {self.start_time.isoformat()}")
        
        # Run test suites
        smoke_result = self.run_smoke_tests()
        core_result = self.run_core_functionality_tests()
        perf_result = self.run_performance_tests()
        security_result = self.run_security_tests()
        compat_result = self.run_compatibility_tests()
        
        # Generate report
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            'timestamp': self.start_time.isoformat(),
            'duration': duration,
            'suites': self.test_results,
            'summary': {
                'total_suites': len(self.test_results),
                'total_tests': sum(r['test_count'] for r in self.test_results),
                'total_passed': sum(r['passed'] for r in self.test_results),
                'total_failed': sum(r['failed'] for r in self.test_results),
                'total_errors': sum(r['errors'] for r in self.test_results),
                'overall_success': all(r['success'] for r in self.test_results)
            }
        }
        
        # Save report
        report_file = f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report):
        """Print regression test summary"""
        print("\n" + "="*60)
        print("REGRESSION TEST SUMMARY")
        print("="*60)
        
        for suite in report['suites']:
            status = "✅ PASSED" if suite['success'] else "❌ FAILED"
            print(f"{suite['suite_name']}: {status}")
            print(f"  Tests: {suite['test_count']}")
            print(f"  Passed: {suite['passed']}")
            print(f"  Failed: {suite['failed']}")
            print(f"  Errors: {suite['errors']}")
            print(f"  Duration: {suite['duration']:.2f}s")
            print()
        
        print("OVERALL SUMMARY:")
        print(f"Total Suites: {report['summary']['total_suites']}")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Total Passed: {report['summary']['total_passed']}")
        print(f"Total Failed: {report['summary']['total_failed']}")
        print(f"Total Errors: {report['summary']['total_errors']}")
        print(f"Overall Success: {'✅ PASSED' if report['summary']['overall_success'] else '❌ FAILED'}")
        print(f"Total Duration: {report['duration']:.2f}s")

def main():
    """Main regression test runner"""
    runner = RegressionTestRunner()
    report = runner.run_all_tests()
    
    # Return appropriate exit code
    sys.exit(0 if report['summary']['overall_success'] else 1)

if __name__ == '__main__':
    main()
```

## Performance Regression Testing

### Performance Benchmarking

```python
# tests/regression/performance/test_license_performance.py
"""Performance regression tests for license system"""

import unittest
import time
import statistics
from tests.regression.base_regression_test import BaseRegressionTest
from src.utils.license_manager import LicenseManager

class TestLicensePerformanceRegression(BaseRegressionTest):
    """Performance regression tests for license system"""
    
    def setUp(self):
        """Set up performance test"""
        super().setUp()
        self.app = self.create_test_app()
        self.license_manager = LicenseManager(self.app)
        self.setup_test_license()
    
    def setup_test_license(self):
        """Set up test license for performance testing"""
        self.license_manager.license_data = {
            'license_key': 'PERF-TEST-LICENSE',
            'license_type': 'professional',
            'status': 'active',
            'features': ['order_management', 'inventory_tracking', 'reporting'],
            'validation_count': 0
        }
    
    def test_license_validation_performance(self):
        """Test license validation performance regression"""
        # Collect performance samples
        validation_times = []
        iterations = 100
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                result = self.license_manager.validate_license()
            
            end_time = time.perf_counter()
            validation_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(validation_times)
        median_time = statistics.median(validation_times)
        p95_time = sorted(validation_times)[int(iterations * 0.95)]
        
        # Assert against baseline
        self.assert_performance_baseline('license_validation_avg', avg_time)
        self.assert_performance_baseline('license_validation_p95', p95_time)
        
        # Performance requirements
        self.assertLess(avg_time, 0.05, "Average validation time should be < 50ms")
        self.assertLess(p95_time, 0.1, "95th percentile validation time should be < 100ms")
        
        # Record performance data
        self.performance_results.append({
            'test': 'license_validation',
            'iterations': iterations,
            'avg_time': avg_time,
            'median_time': median_time,
            'p95_time': p95_time,
            'min_time': min(validation_times),
            'max_time': max(validation_times)
        })
    
    def test_license_activation_performance(self):
        """Test license activation performance regression"""
        activation_times = []
        iterations = 50
        
        for i in range(iterations):
            license_key = f'PERF-TEST-{i:04d}'
            customer_data = {
                'name': f'Test Customer {i}',
                'email': f'test{i}@example.com'
            }
            
            start_time = time.perf_counter()
            
            with patch.object(self.license_manager, 'activate_license') as mock_activate:
                mock_activate.return_value = True
                result = self.license_manager.activate_license(license_key, customer_data)
            
            end_time = time.perf_counter()
            activation_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = statistics.mean(activation_times)
        p95_time = sorted(activation_times)[int(iterations * 0.95)]
        
        # Assert against baseline
        self.assert_performance_baseline('license_activation_avg', avg_time)
        self.assert_performance_baseline('license_activation_p95', p95_time)
        
        # Performance requirements
        self.assertLess(avg_time, 0.2, "Average activation time should be < 200ms")
        self.assertLess(p95_time, 0.5, "95th percentile activation time should be < 500ms")
        
        # Record performance data
        self.performance_results.append({
            'test': 'license_activation',
            'iterations': iterations,
            'avg_time': avg_time,
            'p95_time': p95_time,
            'min_time': min(activation_times),
            'max_time': max(activation_times)
        })
    
    def test_concurrent_license_validation(self):
        """Test concurrent license validation performance"""
        import threading
        import queue
        
        num_threads = 10
        validations_per_thread = 20
        results = queue.Queue()
        
        def worker():
            thread_times = []
            for _ in range(validations_per_thread):
                start_time = time.perf_counter()
                
                with patch.object(self.license_manager, '_validate_online') as mock_validate:
                    mock_validate.return_value = True
                    result = self.license_manager.validate_license()
                
                end_time = time.perf_counter()
                thread_times.append(end_time - start_time)
            
            results.put(thread_times)
        
        # Start threads
        threads = []
        start_time = time.perf_counter()
        
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Collect results
        all_times = []
        while not results.empty():
            all_times.extend(results.get())
        
        # Calculate statistics
        avg_time = statistics.mean(all_times)
        throughput = len(all_times) / total_time
        
        # Assert against baseline
        self.assert_performance_baseline('concurrent_validation_avg', avg_time)
        self.assert_performance_baseline('concurrent_validation_throughput', throughput)
        
        # Performance requirements
        self.assertLess(avg_time, 0.1, "Average concurrent validation time should be < 100ms")
        self.assertGreater(throughput, 50, "Throughput should be > 50 validations/second")
        
        # Record performance data
        self.performance_results.append({
            'test': 'concurrent_license_validation',
            'threads': num_threads,
            'validations_per_thread': validations_per_thread,
            'total_validations': len(all_times),
            'total_time': total_time,
            'avg_time': avg_time,
            'throughput': throughput
        })
    
    def test_memory_usage_regression(self):
        """Test memory usage regression"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform many license operations
        for i in range(1000):
            with patch.object(self.license_manager, '_validate_online') as mock_validate:
                mock_validate.return_value = True
                self.license_manager.validate_license()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert against baseline
        self.assert_performance_baseline('memory_usage_increase', memory_increase)
        
        # Memory requirements
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                        "Memory increase should be < 10MB for 1000 operations")
        
        # Record performance data
        self.performance_results.append({
            'test': 'memory_usage_regression',
            'operations': 1000,
            'initial_memory_mb': initial_memory / (1024 * 1024),
            'final_memory_mb': final_memory / (1024 * 1024),
            'memory_increase_mb': memory_increase / (1024 * 1024)
        })
```

## Continuous Integration Pipeline

### CI/CD Configuration

```yaml
# .github/workflows/regression_tests.yml
name: Regression Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # Run regression tests daily at 2 AM UTC
    - cron: '0 2 * * *'

jobs:
  smoke-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run smoke tests
      run: |
        python scripts/run_regression_tests.py --smoke-only
    
    - name: Upload smoke test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: smoke-test-results
        path: regression_report_*.json

  regression-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    if: success()
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Set up test database
      run: |
        python scripts/setup_test_database.py
    
    - name: Run regression tests
      run: |
        python scripts/run_regression_tests.py
    
    - name: Upload regression test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: regression-test-results
        path: regression_report_*.json
    
    - name: Generate performance report
      run: |
        python scripts/generate_performance_report.py
    
    - name: Upload performance report
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: performance-report
        path: performance_report_*.html

  performance-comparison:
    runs-on: ubuntu-latest
    needs: regression-tests
    if: success()
    steps:
    - uses: actions/checkout@v3
    
    - name: Download artifacts
      uses: actions/download-artifact@v3
      with:
        name: regression-test-results
        path: ./results
    
    - name: Compare with baseline
      run: |
        python scripts/compare_performance_baseline.py
    
    - name: Create performance issue
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: 'Performance Regression Detected',
            body: 'Automated performance regression testing has detected a performance degradation. See the attached performance report for details.',
            labels: ['performance', 'regression', 'automated']
          })

  security-tests:
    runs-on: ubuntu-latest
    needs: smoke-tests
    if: success()
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
        pip install bandit safety
    
    - name: Run security regression tests
      run: |
        python scripts/run_security_regression_tests.py
    
    - name: Run static security analysis
      run: |
        bandit -r src/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json
          security_regression_report_*.json

  compatibility-tests:
    runs-on: ${{ matrix.os }}
    needs: smoke-tests
    if: success()
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run compatibility tests
      run: |
        python scripts/run_compatibility_tests.py
    
    - name: Upload compatibility results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: compatibility-results-${{ matrix.os }}-${{ matrix.python-version }}
        path: compatibility_report_*.json
```

## Test Data Management

### Test Data Generator

```python
# scripts/generate_regression_test_data.py
"""Generate test data for regression testing"""

import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

class RegressionTestDataGenerator:
    """Generate test data for regression testing"""
    
    def __init__(self, output_dir='tests/regression/data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_license_test_data(self):
        """Generate license test data"""
        licenses = []
        
        # Generate different license types
        license_types = ['trial', 'standard', 'professional', 'enterprise']
        
        for i in range(100):
            license_type = random.choice(license_types)
            status = random.choice(['active', 'expired', 'suspended'])
            
            license_data = {
                'license_key': f'REG-TEST-{license_type.upper()}-{i:04d}',
                'license_type': license_type,
                'status': status,
                'customer_info': {
                    'name': f'Test Customer {i}',
                    'email': f'test{i}@example.com',
                    'phone': f'+123456789{i:02d}'
                },
                'features': self.get_features_for_license_type(license_type),
                'issued_date': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'expiry_date': (datetime.now() + timedelta(days=random.randint(-30, 365))).isoformat(),
                'validation_count': random.randint(0, 100)
            }
            
            licenses.append(license_data)
        
        # Save license test data
        with open(self.output_dir / 'license_test_data.json', 'w') as f:
            json.dump(licenses, f, indent=2)
        
        return licenses
    
    def get_features_for_license_type(self, license_type):
        """Get features for license type"""
        feature_sets = {
            'trial': ['order_management', 'basic_reporting'],
            'standard': ['order_management', 'inventory_tracking', 'basic_reporting'],
            'professional': ['order_management', 'inventory_tracking', 'reporting', 'multi_user'],
            'enterprise': ['order_management', 'inventory_tracking', 'reporting', 'multi_user', 'api_access', 'advanced_analytics']
        }
        return feature_sets.get(license_type, [])
    
    def generate_support_test_data(self):
        """Generate support test data"""
        tickets = []
        
        categories = ['Technical Support', 'Bug Report', 'Feature Request', 'General Inquiry']
        priorities = ['Low', 'Medium', 'High', 'Critical']
        statuses = ['Open', 'In Progress', 'Pending Customer', 'Resolved', 'Closed']
        
        for i in range(200):
            category = random.choice(categories)
            priority = random.choice(priorities)
            status = random.choice(statuses)
            
            ticket_data = {
                'ticket_number': f'REG-TICKET-{i:05d}',
                'user_id': random.randint(1, 50),
                'category': category,
                'subject': f'Test Ticket {i}: {self.generate_random_subject(category)}',
                'description': self.generate_random_description(category),
                'priority': priority,
                'status': status,
                'assigned_to': random.randint(1, 10) if status != 'Open' else None,
                'created_at': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                'updated_at': (datetime.now() - timedelta(hours=random.randint(0, 24))).isoformat()
            }
            
            tickets.append(ticket_data)
        
        # Save support test data
        with open(self.output_dir / 'support_test_data.json', 'w') as f:
            json.dump(tickets, f, indent=2)
        
        return tickets
    
    def generate_random_subject(self, category):
        """Generate random subject based on category"""
        subjects = {
            'Technical Support': [
                'Login issues after password change',
                'System crash during peak hours',
                'Performance degradation in reports',
                'Network connectivity problems',
                'Database connection timeout'
            ],
            'Bug Report': [
                'Calculation error in order total',
                'UI elements not displaying correctly',
                'Missing data in export files',
                'Incorrect tax calculation',
                'Payment processing failure'
            ],
            'Feature Request': [
                'Add customer loyalty program',
                'Implement inventory forecasting',
                'Create mobile app interface',
                'Add advanced reporting features',
                'Implement API for third-party integration'
            ],
            'General Inquiry': [
                'How to upgrade license',
                'Questions about data backup',
                'Training materials availability',
                'System requirements clarification',
                'Pricing and billing questions'
            ]
        }
        return random.choice(subjects.get(category, ['General support request']))
    
    def generate_random_description(self, category):
        """Generate random description based on category"""
        descriptions = {
            'Technical Support': [
                'System is experiencing issues that prevent normal operation. '
                'Error logs show connection timeout errors occurring frequently.',
                'Performance has degraded significantly after recent update. '
                'Response times have increased from <1s to >5s for basic operations.'
            ],
            'Bug Report': [
                'When processing orders with multiple items and discounts, '
                'the final calculation is incorrect. Expected total does not match actual total.',
                'UI elements are not rendering properly on certain screen resolutions. '
                'Buttons and input fields are overlapping or not visible.'
            ],
            'Feature Request': [
                'We would like to request a new feature that would allow us to '
                'track customer loyalty points and provide rewards based on purchase history.',
                'It would be beneficial to have a mobile app version of the system '
                'for staff to use tablets for order taking and table management.'
            ],
            'General Inquiry': [
                'We are interested in upgrading our current license to access '
                'additional features. What is the process and cost involved?',
                'We need clarification on the data backup and recovery procedures. '
                'How often are backups performed and how can we restore data?'
            ]
        }
        return random.choice(descriptions.get(category, ['General support request description']))
    
    def generate_performance_baselines(self):
        """Generate performance baseline data"""
        baselines = {
            'license_validation': {
                'average': 0.025,
                'p95': 0.05,
                'p99': 0.1,
                'max': 0.15,
                'samples': 1000
            },
            'license_activation': {
                'average': 0.15,
                'p95': 0.3,
                'p99': 0.5,
                'max': 0.75,
                'samples': 500
            },
            'concurrent_validation': {
                'average': 0.05,
                'throughput': 100,
                'max': 0.1,
                'threads': 10,
                'samples': 200
            },
            'support_ticket_creation': {
                'average': 0.1,
                'p95': 0.2,
                'p99': 0.3,
                'max': 0.5,
                'samples': 500
            },
            'support_ticket_search': {
                'average': 0.05,
                'p95': 0.1,
                'p99': 0.15,
                'max': 0.25,
                'samples': 1000
            },
            'memory_usage': {
                'baseline_mb': 50,
                'increase_per_1000_ops_mb': 2,
                'max_mb': 100
            }
        }
        
        # Save performance baselines
        with open(self.output_dir / 'performance_baselines.json', 'w') as f:
            json.dump(baselines, f, indent=2)
        
        return baselines
    
    def generate_test_scenarios(self):
        """Generate test scenarios"""
        scenarios = {
            'license_scenarios': [
                {
                    'name': 'valid_license_validation',
                    'description': 'Validate a valid active license',
                    'input': {
                        'license_key': 'VALID-LICENSE-KEY',
                        'license_type': 'professional',
                        'status': 'active'
                    },
                    'expected_output': {
                        'is_valid': True,
                        'validation_method': 'online',
                        'features_accessible': True
                    }
                },
                {
                    'name': 'expired_license_validation',
                    'description': 'Validate an expired license',
                    'input': {
                        'license_key': 'EXPIRED-LICENSE-KEY',
                        'license_type': 'standard',
                        'status': 'expired'
                    },
                    'expected_output': {
                        'is_valid': False,
                        'error_message': 'License has expired'
                    }
                }
            ],
            'support_scenarios': [
                {
                    'name': 'create_technical_ticket',
                    'description': 'Create a technical support ticket',
                    'input': {
                        'category': 'Technical Support',
                        'subject': 'Login issue',
                        'description': 'Cannot log in with new password',
                        'priority': 'High'
                    },
                    'expected_output': {
                        'ticket_created': True,
                        'ticket_number_prefix': 'TECH-',
                        'notification_sent': True
                    }
                },
                {
                    'name': 'search_tickets_by_status',
                    'description': 'Search tickets by status',
                    'input': {
                        'search_criteria': {'status': 'Open'},
                        'expected_results': 10
                    },
                    'expected_output': {
                        'results_found': True,
                        'result_count': 10,
                        'all_status_open': True
                    }
                }
            ]
        }
        
        # Save test scenarios
        with open(self.output_dir / 'test_scenarios.json', 'w') as f:
            json.dump(scenarios, f, indent=2)
        
        return scenarios
    
    def generate_all_test_data(self):
        """Generate all test data"""
        print("Generating regression test data...")
        
        # Generate test data
        licenses = self.generate_license_test_data()
        tickets = self.generate_support_test_data()
        baselines = self.generate_performance_baselines()
        scenarios = self.generate_test_scenarios()
        
        print(f"Generated {len(licenses)} license test records")
        print(f"Generated {len(tickets)} support test records")
        print(f"Generated {len(baselines)} performance baselines")
        print(f"Generated {len(scenarios)} test scenarios")
        print(f"Test data saved to {self.output_dir}")
        
        return {
            'licenses': licenses,
            'tickets': tickets,
            'baselines': baselines,
            'scenarios': scenarios
        }

def main():
    """Main test data generator"""
    generator = RegressionTestDataGenerator()
    test_data = generator.generate_all_test_data()
    print("Regression test data generation complete")

if __name__ == '__main__':
    main()
```

## Regression Test Prioritization

### Test Prioritization Framework

```python
# tests/regression/prioritization/test_prioritizer.py
"""Test prioritization framework for regression testing"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple

class TestPrioritizer:
    """Prioritize regression tests based on risk and impact"""
    
    def __init__(self, config_file='tests/regression/config/test_prioritization.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.test_history = self.load_test_history()
        self.code_changes = self.analyze_code_changes()
    
    def load_config(self):
        """Load prioritization configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'priority_weights': {
                'failure_rate': 0.3,
                'execution_time': 0.2,
                'code_coverage': 0.2,
                'business_criticality': 0.3
            },
            'test_categories': {
                'smoke': {'priority': 1, 'always_run': True},
                'critical': {'priority': 2, 'always_run': True},
                'high': {'priority': 3, 'always_run': False},
                'medium': {'priority': 4, 'always_run': False},
                'low': {'priority': 5, 'always_run': False}
            },
            'business_impact': {
                'license_validation': 10,
                'license_activation': 9,
                'support_ticket_creation': 8,
                'support_ticket_management': 7,
                'reporting': 6,
                'ui_responsiveness': 5
            }
        }
    
    def load_test_history(self):
        """Load test execution history"""
        history_file = 'tests/regression/data/test_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def analyze_code_changes(self):
        """Analyze recent code changes"""
        # This would integrate with Git or version control system
        # For now, return mock data
        return {
            'changed_modules': [
                'src/utils/license_manager.py',
                'src/utils/support_manager.py',
                'src/ui/license_activation_dialog.py'
            ],
            'change_types': {
                'feature': 2,
                'bugfix': 1,
                'refactor': 0,
                'documentation': 0
            }
        }
    
    def prioritize_tests(self, test_list: List[str], time_limit: int = 3600) -> List[str]:
        """Prioritize tests based on various factors"""
        test_scores = []
        
        for test in test_list:
            score = self.calculate_test_score(test)
            test_scores.append((test, score))
        
        # Sort by score (lower score = higher priority)
        test_scores.sort(key=lambda x: x[1])
        
        # Select tests within time limit
        selected_tests = []
        total_time = 0
        
        for test, score in test_scores:
            test_time = self.get_test_execution_time(test)
            if total_time + test_time <= time_limit:
                selected_tests.append(test)
                total_time += test_time
            elif self.config['test_categories'].get(self.get_test_category(test), {}).get('always_run', False):
                selected_tests.append(test)
                total_time += test_time
        
        return selected_tests
    
    def calculate_test_score(self, test: str) -> float:
        """Calculate priority score for a test"""
        weights = self.config['priority_weights']
        
        # Failure rate score
        failure_rate = self.get_test_failure_rate(test)
        failure_score = 1.0 - failure_rate  # Lower failure rate = lower score
        
        # Execution time score
        execution_time = self.get_test_execution_time(test)
        time_score = min(execution_time / 10.0, 1.0)  # Normalize to 0-1
        
        # Code coverage score
        coverage = self.get_test_code_coverage(test)
        coverage_score = 1.0 - coverage  # Higher coverage = lower score
        
        # Business criticality score
        business_impact = self.get_business_impact(test)
        business_score = 1.0 - (business_impact / 10.0)  # Higher impact = lower score
        
        # Code change relevance score
        change_relevance = self.get_code_change_relevance(test)
        change_score = 1.0 - change_relevance  # Higher relevance = lower score
        
        # Calculate weighted score
        total_score = (
            failure_score * weights['failure_rate'] +
            time_score * weights['execution_time'] +
            coverage_score * weights['code_coverage'] +
            business_score * weights['business_criticality'] +
            change_score * 0.2  # Additional weight for code changes
        )
        
        return total_score
    
    def get_test_failure_rate(self, test: str) -> float:
        """Get failure rate for a test"""
        if test in self.test_history:
            history = self.test_history[test]
            total_runs = history.get('total_runs', 0)
            failures = history.get('failures', 0)
            
            if total_runs > 0:
                return failures / total_runs
        
        return 0.1  # Default failure rate for new tests
    
    def get_test_execution_time(self, test: str) -> float:
        """Get average execution time for a test"""
        if test in self.test_history:
            history = self.test_history[test]
            return history.get('avg_execution_time', 1.0)
        
        return 1.0  # Default execution time for new tests
    
    def get_test_code_coverage(self, test: str) -> float:
        """Get code coverage for a test"""
        # This would integrate with coverage tools
        # For now, return mock data
        coverage_map = {
            'test_license_validation': 0.85,
            'test_license_activation': 0.75,
            'test_support_ticket_creation': 0.80,
            'test_support_ticket_management': 0.70,
            'test_reporting': 0.60
        }
        return coverage_map.get(test, 0.5)
    
    def get_business_impact(self, test: str) -> float:
        """Get business impact score for a test"""
        # Map test to business impact
        impact_map = self.config['business_impact']
        
        for key, impact in impact_map.items():
            if key in test:
                return impact
        
        return 5.0  # Default business impact
    
    def get_code_change_relevance(self, test: str) -> float:
        """Get relevance score based on code changes"""
        relevance = 0.0
        
        # Check if test relates to changed modules
        for module in self.code_changes['changed_modules']:
            if self.test_uses_module(test, module):
                relevance += 0.5
        
        # Check change type relevance
        if self.code_changes['change_types']['feature'] > 0:
            relevance += 0.3
        if self.code_changes['change_types']['bugfix'] > 0:
            relevance += 0.4
        
        return min(relevance, 1.0)
    
    def test_uses_module(self, test: str, module: str) -> bool:
        """Check if test uses a specific module"""
        # This would analyze test imports and dependencies
        # For now, use simple string matching
        module_name = module.split('/')[-1].replace('.py', '')
        return module_name in test
    
    def get_test_category(self, test: str) -> str:
        """Get category of a test"""
        if 'smoke' in test:
            return 'smoke'
        elif 'critical' in test:
            return 'critical'
        elif 'license' in test and ('validation' in test or 'activation' in test):
            return 'critical'
        elif 'support' in test and ('creation' in test or 'management' in test):
            return 'high'
        elif 'performance' in test:
            return 'medium'
        else:
            return 'low'
    
    def generate_prioritized_test_suite(self, time_limit: int = 3600) -> Dict:
        """Generate prioritized test suite"""
        # Get all available tests
        test_dir = Path('tests/regression')
        all_tests = []
        
        for test_file in test_dir.rglob('test_*.py'):
            test_name = str(test_file.relative_to(test_dir))
            all_tests.append(test_name)
        
        # Prioritize tests
        prioritized_tests = self.prioritize_tests(all_tests, time_limit)
        
        # Categorize tests
        categorized_tests = {
            'smoke': [],
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for test in prioritized_tests:
            category = self.get_test_category(test)
            categorized_tests[category].append(test)
        
        # Calculate estimated execution time
        total_time = sum(self.get_test_execution_time(test) for test in prioritized_tests)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'time_limit': time_limit,
            'total_tests': len(all_tests),
            'selected_tests': len(prioritized_tests),
            'estimated_time': total_time,
            'categorized_tests': categorized_tests,
            'prioritized_tests': prioritized_tests
        }
    
    def update_test_history(self, test_results: Dict):
        """Update test execution history"""
        for test, result in test_results.items():
            if test not in self.test_history:
                self.test_history[test] = {
                    'total_runs': 0,
                    'failures': 0,
                    'avg_execution_time': 0.0,
                    'last_run': None
                }
            
            history = self.test_history[test]
            history['total_runs'] += 1
            
            if not result.get('success', True):
                history['failures'] += 1
            
            # Update average execution time
            execution_time = result.get('execution_time', 0.0)
            if history['avg_execution_time'] == 0.0:
                history['avg_execution_time'] = execution_time
            else:
                history['avg_execution_time'] = (
                    (history['avg_execution_time'] * (history['total_runs'] - 1) + execution_time) /
                    history['total_runs']
                )
            
            history['last_run'] = datetime.now().isoformat()
        
        # Save updated history
        history_file = 'tests/regression/data/test_history.json'
        with open(history_file, 'w') as f:
            json.dump(self.test_history, f, indent=2)

def main():
    """Main test prioritizer"""
    prioritizer = TestPrioritizer()
    
    # Generate prioritized test suite
    test_suite = prioritizer.generate_prioritized_test_suite(time_limit=3600)
    
    # Print results
    print("Prioritized Test Suite:")
    print(f"Total Tests Available: {test_suite['total_tests']}")
    print(f"Tests Selected: {test_suite['selected_tests']}")
    print(f"Estimated Execution Time: {test_suite['estimated_time']:.2f} seconds")
    print(f"Time Limit: {test_suite['time_limit']} seconds")
    
    print("\nTests by Category:")
    for category, tests in test_suite['categorized_tests'].items():
        print(f"{category}: {len(tests)} tests")
    
    # Save test suite
    with open('tests/regression/data/prioritized_test_suite.json', 'w') as f:
        json.dump(test_suite, f, indent=2)
    
    print("\nPrioritized test suite saved to tests/regression/data/prioritized_test_suite.json")

if __name__ == '__main__':
    main()
```

## Defect Classification and Analysis

### Defect Classification Framework

```python
# tests/regression/analysis/defect_classifier.py
"""Defect classification and analysis framework"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from enum import Enum

class DefectSeverity(Enum):
    """Defect severity levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    COSMETIC = 5

class DefectCategory(Enum):
    """Defect categories"""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USABILITY = "usability"
    COMPATIBILITY = "compatibility"
    INSTALLATION = "installation"
    DOCUMENTATION = "documentation"

class DefectClassifier:
    """Classify and analyze defects from regression tests"""
    
    def __init__(self, config_file='tests/regression/config/defect_classification.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.defect_history = self.load_defect_history()
        self.classification_rules = self.load_classification_rules()
    
    def load_config(self):
        """Load defect classification configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'severity_keywords': {
                'critical': ['crash', 'system unavailable', 'data loss', 'security breach'],
                'high': ['major functionality broken', 'performance degradation', 'security vulnerability'],
                'medium': ['workaround available', 'minor functionality broken', 'performance impact'],
                'low': ['cosmetic issue', 'minor inconvenience', 'documentation error'],
                'cosmetic': ['typo', 'formatting', 'cosmetic only']
            },
            'category_keywords': {
                'functional': ['functionality', 'feature', 'behavior', 'calculation', 'logic'],
                'performance': ['slow', 'performance', 'timeout', 'memory', 'resource'],
                'security': ['security', 'authentication', 'authorization', 'encryption', 'vulnerability'],
                'usability': ['usability', 'user experience', 'interface', 'navigation', 'accessibility'],
                'compatibility': ['compatibility', 'browser', 'os', 'version', 'integration'],
                'installation': ['installation', 'setup', 'deployment', 'configuration'],
                'documentation': ['documentation', 'help', 'manual', 'guide', 'instructions']
            }
        }
    
    def load_defect_history(self):
        """Load defect history"""
        history_file = 'tests/regression/data/defect_history.json'
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                return json.load(f)
        return {}
    
    def load_classification_rules(self):
        """Load classification rules"""
        rules_file = 'tests/regression/config/classification_rules.json'
        if os.path.exists(rules_file):
            with open(rules_file, 'r') as f:
                return json.load(f)
        return {}
    
    def classify_defect(self, test_name: str, error_message: str, stack_trace: str = None) -> Dict:
        """Classify a defect based on test failure information"""
        # Extract features from error information
        features = self.extract_features(test_name, error_message, stack_trace)
        
        # Apply classification rules
        severity = self.classify_severity(features)
        category = self.classify_category(features)
        impact = self.classify_impact(features)
        urgency = self.classify_urgency(severity, impact)
        
        # Create defect record
        defect = {
            'test_name': test_name,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'severity': severity.name,
            'category': category.value,
            'impact': impact,
            'urgency': urgency,
            'classification_timestamp': datetime.now().isoformat(),
            'features': features,
            'similar_defects': self.find_similar_defects(features)
        }
        
        return defect
    
    def extract_features(self, test_name: str, error_message: str, stack_trace: str = None) -> Dict:
        """Extract features from defect information"""
        features = {
            'test_name': test_name.lower(),
            'error_message': error_message.lower(),
            'stack_trace': stack_trace.lower() if stack_trace else '',
            'error_type': self.extract_error_type(error_message),
            'affected_module': self.extract_affected_module(test_name, stack_trace),
            'keywords': self.extract_keywords(error_message),
            'test_category': self.extract_test_category(test_name)
        }
        
        return features
    
    def extract_error_type(self, error_message: str) -> str:
        """Extract error type from error message"""
        error_types = [
            'AssertionError', 'ValueError', 'TypeError', 'KeyError',
            'AttributeError', 'ImportError', 'IndexError', 'MemoryError',
            'TimeoutError', 'ConnectionError', 'ValidationError'
        ]
        
        for error_type in error_types:
            if error_type.lower() in error_message.lower():
                return error_type
        
        return 'Unknown'
    
    def extract_affected_module(self, test_name: str, stack_trace: str = None) -> str:
        """Extract affected module from test name and stack trace"""
        # Extract from test name
        if 'license' in test_name.lower():
            return 'license_system'
        elif 'support' in test_name.lower():
            return 'support_system'
        elif 'integration' in test_name.lower():
            return 'integration'
        
        # Extract from stack trace
        if stack_trace:
            lines = stack_trace.split('\n')
            for line in lines:
                if 'src/' in line:
                    parts = line.split('src/')
                    if len(parts) > 1:
                        module_path = parts[1].split('/')[0]
                        return module_path
        
        return 'unknown'
    
    def extract_keywords(self, error_message: str) -> List[str]:
        """Extract keywords from error message"""
        keywords = []
        message_words = error_message.lower().split()
        
        # Add common technical keywords
        technical_keywords = [
            'null', 'none', 'undefined', 'missing', 'invalid', 'failed',
            'timeout', 'connection', 'database', 'network', 'memory',
            'permission', 'access', 'denied', 'unauthorized', 'forbidden'
        ]
        
        for word in message_words:
            if word in technical_keywords:
                keywords.append(word)
        
        return keywords
    
    def extract_test_category(self, test_name: str) -> str:
        """Extract test category from test name"""
        if 'smoke' in test_name.lower():
            return 'smoke'
        elif 'performance' in test_name.lower():
            return 'performance'
        elif 'security' in test_name.lower():
            return 'security'
        elif 'integration' in test_name.lower():
            return 'integration'
        elif 'regression' in test_name.lower():
            return 'regression'
        else:
            return 'functional'
    
    def classify_severity(self, features: Dict) -> DefectSeverity:
        """Classify defect severity"""
        error_message = features['error_message']
        test_category = features['test_category']
        
        # Check for severity keywords
        for severity_name, keywords in self.config['severity_keywords'].items():
            for keyword in keywords:
                if keyword in error_message:
                    return DefectSeverity[severity_name.upper()]
        
        # Apply rule-based classification
        if test_category == 'smoke':
            return DefectSeverity.CRITICAL
        elif test_category == 'security':
            return DefectSeverity.HIGH
        elif test_category == 'performance':
            return DefectSeverity.MEDIUM
        elif features['error_type'] in ['MemoryError', 'TimeoutError']:
            return DefectSeverity.HIGH
        elif features['error_type'] in ['AssertionError', 'ValueError']:
            return DefectSeverity.MEDIUM
        else:
            return DefectSeverity.LOW
    
    def classify_category(self, features: Dict) -> DefectCategory:
        """Classify defect category"""
        error_message = features['error_message']
        affected_module = features['affected_module']
        
        # Check for category keywords
        for category_name, keywords in self.config['category_keywords'].items():
            for keyword in keywords:
                if keyword in error_message:
                    return DefectCategory[category_name.upper()]
        
        # Apply rule-based classification
        if affected_module == 'license_system':
            return DefectCategory.FUNCTIONAL
        elif affected_module == 'support_system':
            return DefectCategory.FUNCTIONAL
        elif features['error_type'] in ['MemoryError', 'TimeoutError']:
            return DefectCategory.PERFORMANCE
        elif 'security' in error_message or 'auth' in error_message:
            return DefectCategory.SECURITY
        elif 'ui' in error_message or 'interface' in error_message:
            return DefectCategory.USABILITY
        else:
            return DefectCategory.FUNCTIONAL
    
    def classify_impact(self, features: Dict) -> str:
        """Classify defect impact"""
        test_category = features['test_category']
        affected_module = features['affected_module']
        
        if test_category == 'smoke':
            return 'system_wide'
        elif test_category == 'integration':
            return 'cross_system'
        elif affected_module in ['license_system', 'support_system']:
            return 'major_feature'
        else:
            return 'minor_feature'
    
    def classify_urgency(self, severity: DefectSeverity, impact: str) -> str:
        """Classify defect urgency based on severity and impact"""
        urgency_matrix = {
            (DefectSeverity.CRITICAL, 'system_wide'): 'immediate',
            (DefectSeverity.CRITICAL, 'cross_system'): 'immediate',
            (DefectSeverity.CRITICAL, 'major_feature'): 'immediate',
            (DefectSeverity.HIGH, 'system_wide'): 'immediate',
            (DefectSeverity.HIGH, 'cross_system'): 'high',
            (DefectSeverity.HIGH, 'major_feature'): 'high',
            (DefectSeverity.MEDIUM, 'system_wide'): 'high',
            (DefectSeverity.MEDIUM, 'cross_system'): 'medium',
            (DefectSeverity.MEDIUM, 'major_feature'): 'medium',
            (DefectSeverity.LOW, 'system_wide'): 'medium',
            (DefectSeverity.LOW, 'cross_system'): 'low',
            (DefectSeverity.LOW, 'major_feature'): 'low'
        }
        
        return urgency_matrix.get((severity, impact), 'low')
    
    def find_similar_defects(self, features: Dict) -> List[Dict]:
        """Find similar defects from history"""
        similar_defects = []
        
        for defect_id, defect_data in self.defect_history.items():
            similarity_score = self.calculate_similarity(features, defect_data['features'])
            
            if similarity_score > 0.7:  # Similarity threshold
                similar_defects.append({
                    'defect_id': defect_id,
                    'similarity_score': similarity_score,
                    'severity': defect_data['severity'],
                    'category': defect_data['category'],
                    'resolution': defect_data.get('resolution', 'unresolved')
                })
        
        # Sort by similarity score
        similar_defects.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_defects[:5]  # Return top 5 similar defects
    
    def calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate similarity between two defect feature sets"""
        similarity_score = 0.0
        
        # Compare error types
        if features1['error_type'] == features2['error_type']:
            similarity_score += 0.3
        
        # Compare affected modules
        if features1['affected_module'] == features2['affected_module']:
            similarity_score += 0.2
        
        # Compare test categories
        if features1['test_category'] == features2['test_category']:
            similarity_score += 0.2
        
        # Compare keywords
        keywords1 = set(features1['keywords'])
        keywords2 = set(features2['keywords'])
        
        if keywords1 and keywords2:
            keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
            similarity_score += keyword_similarity * 0.3
        
        return similarity_score
    
    def analyze_defect_trends(self, time_period: int = 30) -> Dict:
        """Analyze defect trends over time"""
        cutoff_date = datetime.now() - timedelta(days=time_period)
        
        recent_defects = []
        for defect_id, defect_data in self.defect_history.items():
            defect_date = datetime.fromisoformat(defect_data['classification_timestamp'])
            if defect_date >= cutoff_date:
                recent_defects.append(defect_data)
        
        # Calculate trends
        trends = {
            'total_defects': len(recent_defects),
            'severity_distribution': self.calculate_severity_distribution(recent_defects),
            'category_distribution': self.calculate_category_distribution(recent_defects),
            'module_distribution': self.calculate_module_distribution(recent_defects),
            'top_error_types': self.calculate_top_error_types(recent_defects),
            'recurring_defects': self.identify_recurring_defects(recent_defects)
        }
        
        return trends
    
    def calculate_severity_distribution(self, defects: List[Dict]) -> Dict:
        """Calculate severity distribution"""
        distribution = {severity.name: 0 for severity in DefectSeverity}
        
        for defect in defects:
            severity = defect.get('severity', 'UNKNOWN')
            if severity in distribution:
                distribution[severity] += 1
        
        return distribution
    
    def calculate_category_distribution(self, defects: List[Dict]) -> Dict:
        """Calculate category distribution"""
        distribution = {category.value: 0 for category in DefectCategory}
        
        for defect in defects:
            category = defect.get('category', 'functional')
            if category in distribution:
                distribution[category] += 1
        
        return distribution
    
    def calculate_module_distribution(self, defects: List[Dict]) -> Dict:
        """Calculate module distribution"""
        distribution = {}
        
        for defect in defects:
            module = defect['features']['affected_module']
            distribution[module] = distribution.get(module, 0) + 1
        
        return distribution
    
    def calculate_top_error_types(self, defects: List[Dict]) -> List[Dict]:
        """Calculate top error types"""
        error_types = {}
        
        for defect in defects:
            error_type = defect['features']['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Sort by count
        sorted_errors = sorted(error_types.items(), key=lambda x: x[1], reverse=True)
        
        return [{'error_type': error_type, 'count': count} for error_type, count in sorted_errors[:10]]
    
    def identify_recurring_defects(self, defects: List[Dict]) -> List[Dict]:
        """Identify recurring defects"""
        recurring_defects = []
        
        # Group by similarity
        defect_groups = {}
        
        for i, defect1 in enumerate(defects):
            group_id = f"group_{i}"
            defect_groups[group_id] = [defect1]
            
            for j, defect2 in enumerate(defects[i+1:], i+1):
                similarity = self.calculate_similarity(defect1['features'], defect2['features'])
                
                if similarity > 0.8:  # High similarity threshold
                    defect_groups[group_id].append(defect2)
        
        # Find groups with multiple defects
        for group_id, group_defects in defect_groups.items():
            if len(group_defects) > 1:
                recurring_defects.append({
                    'group_id': group_id,
                    'defect_count': len(group_defects),
                    'common_features': self.find_common_features(group_defects),
                    'defects': group_defects
                })
        
        # Sort by defect count
        recurring_defects.sort(key=lambda x: x['defect_count'], reverse=True)
        
        return recurring_defects[:5]  # Return top 5 recurring defect groups
    
    def find_common_features(self, defects: List[Dict]) -> Dict:
        """Find common features among a group of defects"""
        common_features = {}
        
        if not defects:
            return common_features
        
        # Find common error type
        error_types = [defect['features']['error_type'] for defect in defects]
        if len(set(error_types)) == 1:
            common_features['error_type'] = error_types[0]
        
        # Find common affected module
        modules = [defect['features']['affected_module'] for defect in defects]
        if len(set(modules)) == 1:
            common_features['affected_module'] = modules[0]
        
        # Find common keywords
        all_keywords = []
        for defect in defects:
            all_keywords.extend(defect['features']['keywords'])
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        common_keywords = [kw for kw, count in keyword_counts.items() if count == len(defects)]
        if common_keywords:
            common_features['keywords'] = common_keywords
        
        return common_features
    
    def generate_defect_report(self, test_results: Dict) -> Dict:
        """Generate comprehensive defect report"""
        # Classify defects from test results
        classified_defects = []
        
        for test_name, result in test_results.items():
            if not result.get('success', True):
                error_message = result.get('error_message', 'Unknown error')
                stack_trace = result.get('stack_trace', '')
                
                defect = self.classify_defect(test_name, error_message, stack_trace)
                classified_defects.append(defect)
        
        # Analyze trends
        trends = self.analyze_defect_trends()
        
        # Generate recommendations
        recommendations = self.generate_recommendations(classified_defects, trends)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(test_results),
                'failed_tests': len(classified_defects),
                'pass_rate': (len(test_results) - len(classified_defects)) / len(test_results) * 100
            },
            'defects': classified_defects,
            'trends': trends,
            'recommendations': recommendations
        }
        
        return report
    
    def generate_recommendations(self, defects: List[Dict], trends: Dict) -> List[str]:
        """Generate recommendations based on defect analysis"""
        recommendations = []
        
        # Critical defects
        critical_defects = [d for d in defects if d['severity'] == 'CRITICAL']
        if critical_defects:
            recommendations.append(
                f"IMMEDIATE ACTION REQUIRED: {len(critical_defects)} critical defects detected. "
                "These should be addressed before any release."
            )
        
        # High severity defects
        high_defects = [d for d in defects if d['severity'] == 'HIGH']
        if high_defects:
            recommendations.append(
                f"HIGH PRIORITY: {len(high_defects)} high severity defects detected. "
                "These should be addressed in the next release."
            )
        
        # Recurring defects
        if trends['recurring_defects']:
            recommendations.append(
                f"RECURRING ISSUES: {len(trends['recurring_defects'])} groups of similar defects detected. "
                "Consider root cause analysis to prevent future occurrences."
            )
        
        # Module-specific issues
        module_dist = trends['module_distribution']
        if module_dist:
            top_module = max(module_dist.items(), key=lambda x: x[1])
            recommendations.append(
                f"MODULE FOCUS: {top_module[0]} module has {top_module[1]} defects. "
                "Consider additional testing or code review for this module."
            )
        
        # Error type patterns
        top_errors = trends['top_error_types']
        if top_errors:
            top_error = top_errors[0]
            recommendations.append(
                f"ERROR PATTERN: {top_error['error_type']} occurs {top_error['count']} times. "
                "Consider preventive measures or additional validation."
            )
        
        return recommendations

def main():
    """Main defect classifier"""
    classifier = DefectClassifier()
    
    # Load test results (mock data for demonstration)
    test_results = {
        'test_license_validation': {
            'success': False,
            'error_message': 'License validation failed: Connection timeout',
            'stack_trace': 'File "license_manager.py", line 123, in validate_license\n    result = server.validate(key)\nTimeoutError: Connection timeout'
        },
        'test_support_ticket_creation': {
            'success': False,
            'error_message': 'Support ticket creation failed: Invalid email format',
            'stack_trace': 'File "support_manager.py", line 45, in create_ticket\n    validate_email(email)\nValueError: Invalid email format'
        }
    }
    
    # Generate defect report
    report = classifier.generate_defect_report(test_results)
    
    # Print summary
    print("Defect Classification Report:")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Failed Tests: {report['summary']['failed_tests']}")
    print(f"Pass Rate: {report['summary']['pass_rate']:.1f}%")
    print(f"Defects Classified: {len(report['defects'])}")
    
    print("\nDefects:")
    for defect in report['defects']:
        print(f"- {defect['test_name']}: {defect['severity']} {defect['category']}")
    
    print("\nRecommendations:")
    for recommendation in report['recommendations']:
        print(f"- {recommendation}")
    
    # Save report
    with open('tests/regression/data/defect_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nDefect report saved to tests/regression/data/defect_report.json")

if __name__ == '__main__':
    main()
```

---

This comprehensive regression testing framework provides a structured approach to detecting and preventing regressions in both the support system and license validation system. The framework includes automated test execution, performance monitoring, test prioritization, and sophisticated defect classification to ensure system quality and reliability over time.