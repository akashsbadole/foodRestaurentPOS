"""
Test Documentation Generator
Creates comprehensive test documentation and user guides for the testing framework.
"""

import os
import json
import unittest
import inspect
import importlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class TestDocumentationGenerator:
    """Generates comprehensive documentation for the testing framework"""
    
    def __init__(self, test_directory: str = "tests", output_directory: str = "test_docs"):
        self.test_directory = Path(test_directory)
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(exist_ok=True)
        
        self.test_modules = []
        self.test_classes = {}
        self.test_methods = {}
        
    def scan_test_files(self) -> None:
        """Scan test directory for all test files"""
        print("Scanning test files...")
        
        for file_path in self.test_directory.glob("test_*.py"):
            if file_path.is_file():
                module_name = file_path.stem
                self.test_modules.append({
                    'name': module_name,
                    'path': str(file_path),
                    'module': None
                })
        
        print(f"Found {len(self.test_modules)} test files")
    
    def analyze_test_structure(self) -> None:
        """Analyze the structure of all test files"""
        print("Analyzing test structure...")
        
        for test_module in self.test_modules:
            try:
                # Import the module
                module_path = f"multi_web_cloud.tests.{test_module['name']}"
                module = importlib.import_module(module_path)
                test_module['module'] = module
                
                # Get all test classes
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name.startswith('Test'):
                        class_info = {
                            'name': name,
                            'module': module.__name__,
                            'docstring': inspect.getdoc(obj) or "",
                            'methods': [],
                            'file': test_module['path']
                        }
                        
                        # Get all test methods
                        for method_name, method_obj in inspect.getmembers(obj):
                            if inspect.ismethod(method_obj) or inspect.isfunction(method_obj):
                                if method_name.startswith('test_'):
                                    method_info = {
                                        'name': method_name,
                                        'docstring': inspect.getdoc(method_obj) or "",
                                        'signature': str(inspect.signature(method_obj))
                                    }
                                    class_info['methods'].append(method_info)
                        
                        self.test_classes[name] = class_info
            
            except ImportError as e:
                print(f"Could not import {test_module['name']}: {e}")
    
    def generate_test_overview(self) -> str:
        """Generate an overview of the testing framework"""
        overview = f"""# Multi-Retail POS System Testing Framework Documentation

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This document provides comprehensive documentation for the Multi-Retail POS System testing framework. The framework is designed to ensure all features work correctly across different retail types and feature combinations.

## Testing Framework Components

The testing framework consists of the following components:

"""
        
        # Add component descriptions
        components = [
            {
                'name': 'Feature Flag Testing',
                'description': 'Tests for feature flag parsing, validation, dependency resolution, and hierarchical precedence',
                'file': 'test_feature_flags.py'
            },
            {
                'name': 'Multi-Retail Module Testing',
                'description': 'Tests for all retail modules including restaurant, apparel, books, and grocery',
                'file': 'test_multi_retail_modules.py'
            },
            {
                'name': 'Database Schema Testing',
                'description': 'Tests for conditional table creation, data integrity, tenant isolation, and rollback procedures',
                'file': 'test_database_schema.py'
            },
            {
                'name': 'API Testing Framework',
                'description': 'Comprehensive API tests for all endpoints with authentication, authorization, and error handling',
                'file': 'test_api_comprehensive.py'
            },
            {
                'name': 'UI/UX Testing Framework',
                'description': 'Tests for adaptive templates, dynamic navigation, form generation, and accessibility',
                'file': 'test_ui_ux.py'
            },
            {
                'name': 'Performance Testing',
                'description': 'Load tests for different feature combinations, database performance, and UI rendering',
                'file': 'test_performance.py'
            },
            {
                'name': 'Security Testing Framework',
                'description': 'Tests for access control, data encryption, input validation, and vulnerability prevention',
                'file': 'test_security_comprehensive.py'
            },
            {
                'name': 'Integration Testing',
                'description': 'End-to-end workflow tests for each retail type and multi-tenant scenarios',
                'file': 'test_integration_workflows.py'
            },
            {
                'name': 'Retail-Type Specific Test Scenarios',
                'description': 'Specific test scenarios for restaurant, apparel, books, and grocery workflows',
                'file': 'test_retail_specific_scenarios.py'
            },
            {
                'name': 'Feature Combination Testing',
                'description': 'Tests for all possible feature combinations, conflicts, and performance with all features',
                'file': 'test_feature_combinations.py'
            }
        ]
        
        for component in components:
            overview += f"### {component['name']}\n\n"
            overview += f"**File:** `{component['file']}`\n\n"
            overview += f"{component['description']}\n\n"
        
        # Add test statistics
        overview += "## Test Statistics\n\n"
        overview += f"- **Total Test Files:** {len(self.test_modules)}\n"
        overview += f"- **Total Test Classes:** {len(self.test_classes)}\n"
        
        total_methods = sum(len(cls['methods']) for cls in self.test_classes.values())
        overview += f"- **Total Test Methods:** {total_methods}\n\n"
        
        return overview
    
    def generate_test_class_documentation(self) -> str:
        """Generate documentation for all test classes"""
        doc = "## Test Classes Documentation\n\n"
        
        for class_name, class_info in self.test_classes.items():
            doc += f"### {class_name}\n\n"
            doc += f"**Module:** `{class_info['module']}`\n"
            doc += f"**File:** `{class_info['file']}`\n\n"
            
            if class_info['docstring']:
                doc += f"**Description:** {class_info['docstring']}\n\n"
            
            doc += "#### Test Methods\n\n"
            
            for method in class_info['methods']:
                doc += f"**{method['name']}**\n"
                doc += f"```python\n{method['signature']}\n```\n\n"
                
                if method['docstring']:
                    doc += f"{method['docstring']}\n\n"
            
            doc += "---\n\n"
        
        return doc
    
    def generate_test_execution_guide(self) -> str:
        """Generate a guide for running tests"""
        guide = """# Test Execution Guide

This guide provides instructions for running tests and interpreting results.

## Prerequisites

Before running tests, ensure you have:

1. Python 3.8+ installed
2. All required dependencies installed (`pip install -r requirements-test.txt`)
3. Database configured for testing
4. Environment variables set up

## Running Tests

### Run All Tests

```bash
# Using the test runner
python run_tests.py

# Using pytest directly
pytest

# Using unittest
python -m unittest discover tests
```

### Run Specific Test Components

```bash
# Feature flag tests
python run_tests.py --component feature_flags

# Multi-retail module tests
python run_tests.py --component multi_retail

# Database schema tests
python run_tests.py --component database

# API tests
python run_tests.py --component api

# UI/UX tests
python run_tests.py --component ui_ux

# Performance tests
python run_tests.py --component performance

# Security tests
python run_tests.py --component security

# Integration tests
python run_tests.py --component integration

# Retail-specific tests
python run_tests.py --component retail_specific

# Feature combination tests
python run_tests.py --component feature_combinations
```

### Run Specific Test Classes

```bash
# Using pytest
pytest tests/test_feature_flags.py::TestFeatureFlagParsing

# Using unittest
python -m unittest tests.test_feature_flags.TestFeatureFlagParsing
```

### Run Specific Test Methods

```bash
# Using pytest
pytest tests/test_feature_flags.py::TestFeatureFlagParsing::test_feature_flag_parsing

# Using unittest
python -m unittest tests.test_feature_flags.TestFeatureFlagParsing.test_feature_flag_parsing
```

## Test Options

### Coverage Reporting

```bash
# Generate coverage report
python run_tests.py --coverage

# Generate HTML coverage report
python run_tests.py --coverage-html

# Coverage with specific threshold
python run_tests.py --coverage --threshold 80
```

### Performance Testing

```bash
# Run performance tests
python run_tests.py --component performance

# Performance with specific load
python run_tests.py --component performance --load 100

# Performance with specific duration
python run_tests.py --component performance --duration 60
```

### Parallel Execution

```bash
# Run tests in parallel
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

### Verbose Output

```bash
# Verbose output
python run_tests.py --verbose

# Very verbose output
python run_tests.py --verbose --verbose
```

## Test Configuration

### Environment Variables

- `TEST_DATABASE_URL`: Database URL for testing
- `TEST_REDIS_URL`: Redis URL for testing
- `TEST_EMAIL_BACKEND`: Email backend for testing
- `TEST_PAYMENT_GATEWAY`: Payment gateway for testing

### Configuration Files

- `pytest.ini`: Pytest configuration
- `conftest.py`: Test fixtures and configuration
- `requirements-test.txt`: Test dependencies

## Interpreting Results

### Test Output Format

```
============================= test session starts ==============================
platform linux -- Python 3.9.0, pytest-6.2.4, py-1.10.0, pluggy-0.13.1
rootdir: /path/to/project
collected 150 items

tests/test_feature_flags.py::TestFeatureFlagParsing::test_feature_flag_parsing PASSED [  0%]
tests/test_feature_flags.py::TestFeatureFlagParsing::test_invalid_feature_flag FAILED [  0%]

============================== FAILURES ==============================
________________________ TestFeatureFlagParsing.test_invalid_feature_flag ________________________

self = <tests.test_feature_flags.TestFeatureFlagParsing object at 0x7f8b0c0d4a90>

    def test_invalid_feature_flag(self):
        """Test handling of invalid feature flags"""
        with self.assertRaises(ValueError):
            feature_manager.parse_feature_flag("INVALID_FLAG_FORMAT")
>           feature_manager.parse_feature_flag("INVALID_FLAG_FORMAT")

tests/test_feature_flags.py:45: 
E           AssertionError: ValueError not raised

=========================== short test summary info ============================
FAILED tests/test_feature_flags.py::TestFeatureFlagParsing::test_invalid_feature_flag
========================= 1 failed, 149 passed in 5.23s ==========================
```

### Exit Codes

- `0`: All tests passed
- `1`: Tests failed
- `2`: No tests collected
- `3`: Internal error
- `4`: Usage error

### Coverage Report Format

```
Name                              Stmts   Miss  Cover
-----------------------------------------------------
models/__init__.py                  45      5    89%
models/feature_flag.py              78     12    85%
models/tenant.py                    56      8    86%
utils/feature_manager.py           123     15    88%
-----------------------------------------------------
TOTAL                              302     40    87%
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed
   - Check PYTHONPATH includes the project directory
   - Verify module structure is correct

2. **Database Connection Errors**
   - Check database configuration
   - Ensure test database exists
   - Verify database permissions

3. **Timeout Errors**
   - Increase timeout values
   - Check system resources
   - Optimize test data setup

4. **Memory Errors**
   - Reduce test data size
   - Run tests with fewer parallel workers
   - Check for memory leaks

### Debug Mode

```bash
# Run with debug output
python run_tests.py --debug

# Run with specific log level
python run_tests.py --log-level DEBUG

# Stop on first failure
pytest -x
```

### Test Isolation

Tests are isolated using:
- In-memory SQLite database
- Mock objects for external services
- Transaction rollback after each test
- Separate test fixtures

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    - name: Run tests
      run: |
        python run_tests.py --coverage
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
```

### Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'pip install -r requirements-test.txt'
                sh 'python run_tests.py --coverage --threshold 80'
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: 'Coverage Report'
            ])
        }
    }
}
```

## Best Practices

1. **Write Descriptive Tests**
   - Use clear test names
   - Add docstrings explaining the purpose
   - Include setup and teardown comments

2. **Maintain Test Independence**
   - Tests should not depend on each other
   - Use fixtures for shared setup
   - Clean up after each test

3. **Use Appropriate Assertions**
   - Choose the most specific assertion
   - Include helpful error messages
   - Test both positive and negative cases

4. **Mock External Dependencies**
   - Mock databases, APIs, and services
   - Use consistent mock data
   - Verify mock interactions

5. **Regular Test Maintenance**
   - Update tests with code changes
   - Remove obsolete tests
   - Improve test coverage
"""
        
        return guide
    
    def generate_api_test_documentation(self) -> str:
        """Generate documentation for API testing"""
        doc = """# API Testing Documentation

This document provides detailed information about API testing in the Multi-Retail POS System.

## API Test Structure

### Authentication Tests

Tests for API authentication and authorization:

- `TestAPIAuthentication`: Tests login, logout, token validation, and session management
- `TestFeatureProtectedAPIs`: Tests access control based on feature flags
- `TestAPIErrorHandling`: Tests error responses and validation

### Endpoint Tests

Tests for all API endpoints organized by module:

#### Restaurant Module
- `GET /api/restaurant/tables` - List restaurant tables
- `POST /api/restaurant/tables` - Create new table
- `PUT /api/restaurant/tables/{id}` - Update table
- `DELETE /api/restaurant/tables/{id}` - Delete table

#### Apparel Module
- `GET /api/apparel/products` - List apparel products
- `POST /api/apparel/products` - Create new product
- `GET /api/apparel/variants` - List product variants
- `POST /api/apparel/exchanges` - Process exchange

#### Books Module
- `GET /api/books/products` - List book products
- `GET /api/books/isbn/{isbn}` - Lookup by ISBN
- `POST /api/books/special-orders` - Create special order
- `GET /api/books/publishers` - List publishers

#### Grocery Module
- `GET /api/grocery/produce` - List fresh produce
- `GET /api/grocery/expiry` - Check expiry tracking
- `GET /api/grocery/scales` - List weighing scales
- `POST /api/grocery/price-by-weight` - Calculate price by weight

## Test Data

### Fixtures

Common test data fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def test_tenant():
    """Create test tenant"""
    return Tenant(
        name="Test Tenant",
        subdomain="test",
        retail_type="general"
    )

@pytest.fixture
def test_user(test_tenant):
    """Create test user"""
    return User(
        username="testuser",
        email="test@example.com",
        tenant_id=test_tenant.id
    )
```

### Factories

Test data factories for creating complex objects:

```python
class ProductFactory:
    """Factory for creating test products"""
    
    @staticmethod
    def create_apparel_product(**kwargs):
        """Create apparel product with variants"""
        defaults = {
            'name': 'Test Apparel Product',
            'category_id': 1,
            'base_price': Decimal('99.99')
        }
        defaults.update(kwargs)
        
        product = ApparelProduct(**defaults)
        
        # Add variants
        for size in ['S', 'M', 'L']:
            for color in ['Red', 'Blue']:
                variant = ApparelVariant(
                    product_id=product.id,
                    size=size,
                    color=color
                )
                product.variants.append(variant)
        
        return product
```

## API Response Testing

### Success Responses

Test successful API responses:

```python
def test_create_table_success(self):
    """Test successful table creation"""
    table_data = {
        'table_number': 'T1',
        'capacity': 4,
        'location': 'Main Hall'
    }
    
    response = self.client.post('/api/restaurant/tables',
                               data=json.dumps(table_data),
                               content_type='application/json',
                               headers=self.headers)
    
    self.assertEqual(response.status_code, 201)
    
    data = json.loads(response.data)
    self.assertEqual(data['table_number'], 'T1')
    self.assertEqual(data['capacity'], 4)
    self.assertIn('id', data)
```

### Error Responses

Test error handling:

```python
def test_create_table_validation_error(self):
    """Test table creation with invalid data"""
    invalid_data = {
        'table_number': '',  # Invalid: empty string
        'capacity': -1,      # Invalid: negative number
        'location': 'A' * 201  # Invalid: too long
    }
    
    response = self.client.post('/api/restaurant/tables',
                               data=json.dumps(invalid_data),
                               content_type='application/json',
                               headers=self.headers)
    
    self.assertEqual(response.status_code, 400)
    
    data = json.loads(response.data)
    self.assertIn('errors', data)
    self.assertIn('table_number', data['errors'])
    self.assertIn('capacity', data['errors'])
    self.assertIn('location', data['errors'])
```

### Feature-Protected Endpoints

Test endpoints protected by feature flags:

```python
def test_kitchen_display_feature_required(self):
    """Test kitchen display endpoint requires feature flag"""
    # Disable feature
    feature_manager.disable_feature('FEATURE_KITCHEN_DISPLAY', self.tenant_id)
    
    response = self.client.get('/api/restaurant/kitchen/display',
                              headers=self.headers)
    
    self.assertEqual(response.status_code, 403)
    
    data = json.loads(response.data)
    self.assertIn('message', data)
    self.assertIn('FEATURE_KITCHEN_DISPLAY', data['message'])
    
    # Enable feature
    feature_manager.enable_feature('FEATURE_KITCHEN_DISPLAY', self.tenant_id)
    
    response = self.client.get('/api/restaurant/kitchen/display',
                              headers=self.headers)
    
    self.assertEqual(response.status_code, 200)
```

## Performance Testing

### Load Testing

Test API performance under load:

```python
def test_api_load_performance(self):
    """Test API performance under load"""
    import concurrent.futures
    
    def make_request():
        response = self.client.get('/api/products', headers=self.headers)
        return response.status_code == 200
    
    # Make 100 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [f.result() for f in futures]
    
    # 95% of requests should succeed
    success_rate = sum(results) / len(results)
    self.assertGreater(success_rate, 0.95)
```

### Response Time Testing

Test API response times:

```python
def test_api_response_time(self):
    """Test API response times"""
    import time
    
    start_time = time.time()
    response = self.client.get('/api/products', headers=self.headers)
    response_time = time.time() - start_time
    
    self.assertEqual(response.status_code, 200)
    self.assertLess(response_time, 1.0)  # Should respond in under 1 second
```

## Security Testing

### Authentication Testing

Test API authentication:

```python
def test_unauthorized_access(self):
    """Test API access without authentication"""
    response = self.client.get('/api/products')
    
    self.assertEqual(response.status_code, 401)
    
    data = json.loads(response.data)
    self.assertIn('message', data)
    self.assertEqual(data['message'], 'Authentication required')
```

### Authorization Testing

Test API authorization:

```python
def test_forbidden_access(self):
    """Test API access with insufficient permissions"""
    # Create user with limited permissions
    limited_user = User(
        username='limited',
        role='cashier',  # Limited role
        tenant_id=self.tenant_id
    )
    
    # Login as limited user
    token = self.login_user(limited_user)
    headers = {'Authorization': f'Bearer {token}'}
    
    # Try to access admin endpoint
    response = self.client.get('/api/admin/users', headers=headers)
    
    self.assertEqual(response.status_code, 403)
```

### Input Validation Testing

Test input validation and sanitization:

```python
def test_sql_injection_protection(self):
    """Test SQL injection protection"""
    malicious_input = "'; DROP TABLE products; --"
    
    response = self.client.get(f'/api/products?search={malicious_input}',
                              headers=self.headers)
    
    # Should not cause database error
    self.assertEqual(response.status_code, 200)
    
    # Products table should still exist
    products = Product.query.all()
    self.assertIsInstance(products, list)
```

## Test Utilities

### API Client Helper

Helper class for API testing:

```python
class APITestClient:
    """Helper class for API testing"""
    
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
        self.token = None
        self.headers = {}
    
    def login(self, username, password, tenant_id):
        """Login and set authentication headers"""
        login_data = {
            'username': username,
            'password': password,
            'tenant_id': tenant_id
        }
        
        response = self.client.post('/api/auth/login',
                                   data=json.dumps(login_data),
                                   content_type='application/json')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            self.token = data['access_token']
            self.headers = {'Authorization': f'Bearer {self.token}'}
            return True
        
        return False
    
    def get(self, endpoint, **kwargs):
        """Make GET request"""
        return self.client.get(endpoint, headers=self.headers, **kwargs)
    
    def post(self, endpoint, data=None, **kwargs):
        """Make POST request"""
        if data:
            data = json.dumps(data)
            kwargs['content_type'] = 'application/json'
        
        return self.client.post(endpoint, data=data, headers=self.headers, **kwargs)
```

### Response Assertions

Custom assertion methods for API responses:

```python
def assert_api_success(self, response, expected_status=200):
    """Assert API response is successful"""
    self.assertEqual(response.status_code, expected_status)
    
    data = json.loads(response.data)
    self.assertIsInstance(data, dict)
    
    return data

def assert_api_error(self, response, expected_status=400):
    """Assert API response is an error"""
    self.assertEqual(response.status_code, expected_status)
    
    data = json.loads(response.data)
    self.assertIn('error', data)
    
    return data
```

## Mock Services

### External API Mocks

Mock external services:

```python
@patch('services.payment_gateway.charge')
def test_payment_processing(self, mock_charge):
    """Test payment processing with mocked gateway"""
    # Configure mock
    mock_charge.return_value = {
        'success': True,
        'transaction_id': 'txn_123456',
        'amount': 99.99
    }
    
    # Process payment
    payment_data = {
        'amount': 99.99,
        'method': 'credit_card',
        'card_token': 'tok_123456'
    }
    
    response = self.client.post('/api/payments/process',
                               data=json.dumps(payment_data),
                               content_type='application/json',
                               headers=self.headers)
    
    self.assertEqual(response.status_code, 200)
    
    # Verify mock was called
    mock_charge.assert_called_once_with(
        amount=99.99,
        token='tok_123456'
    )
```

### Database Mocks

Mock database operations:

```python
@patch('models.db.session')
def test_database_transaction(self, mock_session):
    """Test database transaction handling"""
    # Configure mock
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.rollback.return_value = None
    
    # Create product
    product_data = {
        'name': 'Test Product',
        'price': 99.99
    }
    
    response = self.client.post('/api/products',
                               data=json.dumps(product_data),
                               content_type='application/json',
                               headers=self.headers)
    
    self.assertEqual(response.status_code, 201)
    
    # Verify database operations
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
```

## Continuous Integration

### Automated Testing

Automated testing in CI/CD pipeline:

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  api-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run API tests
      run: |
        pytest tests/test_api_comprehensive.py -v
      env:
        TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
    
    - name: Generate API documentation
      run: |
        python tests/generate_api_docs.py
    
    - name: Upload API docs
      uses: actions/upload-artifact@v2
      with:
        name: api-documentation
        path: docs/api/
```
"""
        
        return doc
    
    def generate_test_report_template(self) -> str:
        """Generate a template for test reports"""
        template = """# Test Execution Report

**Date:** {date}
**Test Suite:** {test_suite}
**Environment:** {environment}
**Executor:** {executor}

## Executive Summary

{summary}

## Test Results

### Overall Results

- **Total Tests:** {total_tests}
- **Passed:** {passed_tests}
- **Failed:** {failed_tests}
- **Skipped:** {skipped_tests}
- **Success Rate:** {success_rate}%

### Test Execution Time

- **Total Time:** {total_time}
- **Average Time per Test:** {avg_time}

## Test Coverage

### Coverage Metrics

{coverage_metrics}

### Coverage by Module

{coverage_by_module}

## Test Results by Component

### Feature Flag Tests

{feature_flag_results}

### Multi-Retail Module Tests

{multi_retail_results}

### Database Schema Tests

{database_results}

### API Tests

{api_results}

### UI/UX Tests

{ui_ux_results}

### Performance Tests

{performance_results}

### Security Tests

{security_results}

### Integration Tests

{integration_results}

### Retail-Specific Tests

{retail_specific_results}

### Feature Combination Tests

{feature_combination_results}

## Failed Tests

### Critical Failures

{critical_failures}

### Non-Critical Failures

{non_critical_failures}

## Performance Metrics

### Response Times

{response_times}

### Resource Usage

{resource_usage}

### Load Test Results

{load_test_results}

## Security Test Results

### Vulnerability Assessment

{vulnerability_assessment}

### Authentication/Authorization Tests

{auth_tests}

### Input Validation Tests

{input_validation_tests}

## Recommendations

### Immediate Actions

{immediate_actions}

### Long-term Improvements

{long_term_improvements}

## Appendices

### Test Environment Details

{environment_details}

### Test Data Summary

{test_data_summary}

### Known Issues

{known_issues}
"""
        
        return template
    
    def generate_all_documentation(self) -> None:
        """Generate all documentation files"""
        print("Generating documentation...")
        
        # Generate overview
        overview = self.generate_test_overview()
        with open(self.output_directory / "overview.md", 'w') as f:
            f.write(overview)
        
        # Generate test class documentation
        class_doc = self.generate_test_class_documentation()
        with open(self.output_directory / "test_classes.md", 'w') as f:
            f.write(class_doc)
        
        # Generate execution guide
        guide = self.generate_test_execution_guide()
        with open(self.output_directory / "execution_guide.md", 'w') as f:
            f.write(guide)
        
        # Generate API documentation
        api_doc = self.generate_api_test_documentation()
        with open(self.output_directory / "api_testing.md", 'w') as f:
            f.write(api_doc)
        
        # Generate report template
        template = self.generate_test_report_template()
        with open(self.output_directory / "report_template.md", 'w') as f:
            f.write(template)
        
        print(f"Documentation generated in {self.output_directory}")


def generate_documentation():
    """Generate all test documentation"""
    generator = TestDocumentationGenerator()
    generator.scan_test_files()
    generator.analyze_test_structure()
    generator.generate_all_documentation()


if __name__ == '__main__':
    generate_documentation()