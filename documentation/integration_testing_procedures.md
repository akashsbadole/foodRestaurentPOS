# Integration Testing Procedures for Support and License Systems

## Overview

This document outlines comprehensive integration testing procedures for the support system and license validation system in the Restaurant POS MVP application. Integration testing verifies that different components work together correctly and that the systems integrate properly with external dependencies.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Environment Setup](#test-environment-setup)
3. [License System Integration Tests](#license-system-integration-tests)
4. [Support System Integration Tests](#support-system-integration-tests)
5. [Cross-System Integration Tests](#cross-system-integration-tests)
6. [Database Integration Tests](#database-integration-tests)
7. [External Service Integration Tests](#external-service-integration-tests)
8. [UI Integration Tests](#ui-integration-tests)
9. [Error Handling Integration Tests](#error-handling-integration-tests)
10. [Performance Integration Tests](#performance-integration-tests)
11. [Test Execution and Reporting](#test-execution-and-reporting)

## Testing Strategy

### Integration Testing Goals

1. **Component Interaction**: Verify that components interact correctly
2. **Data Flow**: Ensure data flows properly between systems
3. **External Dependencies**: Test integration with external services
4. **End-to-End Workflows**: Validate complete user workflows
5. **System Boundaries**: Test system boundaries and interfaces
6. **Error Propagation**: Verify error handling across component boundaries

### Test Categories

1. **Component Integration**: Test interaction between system components
2. **Database Integration**: Test database operations and transactions
3. **API Integration**: Test integration with external APIs
4. **UI Integration**: Test integration between UI and backend systems
5. **Cross-System Integration**: Test interaction between license and support systems
6. **Performance Integration**: Test performance under realistic conditions

## Test Environment Setup

### Environment Requirements

```bash
# Environment Setup Script
#!/bin/bash

# Create test environment
echo "Setting up integration test environment..."

# Create test database
python scripts/create_test_database.py

# Set up test configuration
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///test_restaurant_pos.db
export LICENSE_SERVER_URL=https://test-license.restaurantpos.com/api/v1
export EMAIL_SERVICE_URL=https://test-email.restaurantpos.com/api/v1

# Install test dependencies
pip install -r requirements-test.txt

# Start test services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run database migrations
python scripts/run_migrations.py

echo "Test environment setup complete"
```

### Docker Test Configuration

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-db:
    image: sqlite:latest
    volumes:
      - ./test_data:/data
    environment:
      - SQLITE_DATABASE=test_restaurant_pos.db
  
  license-server:
    image: restaurantpos/license-server:test
    ports:
      - "8081:8080"
    environment:
      - ENVIRONMENT=test
      - DATABASE_URL=sqlite:///data/test_licenses.db
    depends_on:
      - test-db
  
  email-service:
    image: restaurantpos/email-service:test
    ports:
      - "8082:8080"
    environment:
      - ENVIRONMENT=test
      - SMTP_HOST=mailhog
    depends_on:
      - mailhog
  
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "1025:1025"
      - "8025:8025"
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### Test Data Setup

```python
# scripts/setup_test_data.py
"""Script to set up test data for integration testing"""

import sqlite3
import json
from datetime import datetime, timedelta

def create_test_database():
    """Create test database with required tables"""
    conn = sqlite3.connect('test_restaurant_pos.db')
    cursor = conn.cursor()
    
    # Create tables
    with open('schema.sql', 'r') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    conn.commit()
    conn.close()

def insert_test_licenses():
    """Insert test license data"""
    conn = sqlite3.connect('test_restaurant_pos.db')
    cursor = conn.cursor()
    
    test_licenses = [
        {
            'license_key': 'TEST-LIC-001-PROFESSIONAL',
            'license_type': 'professional',
            'status': 'active',
            'customer_info': json.dumps({
                'name': 'Test Restaurant 1',
                'email': 'test1@restaurant.com'
            }),
            'features': json.dumps([
                'order_management', 'inventory_tracking', 'reporting',
                'multi_user', 'api_access'
            ]),
            'issued_date': datetime.now() - timedelta(days=30),
            'expiry_date': datetime.now() + timedelta(days=335),
            'validation_count': 5
        },
        {
            'license_key': 'TEST-LIC-002-STANDARD',
            'license_type': 'standard',
            'status': 'active',
            'customer_info': json.dumps({
                'name': 'Test Restaurant 2',
                'email': 'test2@restaurant.com'
            }),
            'features': json.dumps([
                'order_management', 'inventory_tracking'
            ]),
            'issued_date': datetime.now() - timedelta(days=60),
            'expiry_date': datetime.now() + timedelta(days=305),
            'validation_count': 3
        },
        {
            'license_key': 'TEST-LIC-003-TRIAL',
            'license_type': 'trial',
            'status': 'active',
            'customer_info': json.dumps({
                'name': 'Test Restaurant 3',
                'email': 'test3@restaurant.com'
            }),
            'features': json.dumps([
                'order_management', 'basic_reporting'
            ]),
            'issued_date': datetime.now() - timedelta(days=5),
            'expiry_date': datetime.now() + timedelta(days=25),
            'validation_count': 1
        }
    ]
    
    for license_data in test_licenses:
        cursor.execute("""
            INSERT INTO licenses (
                license_key, license_type, status, customer_info,
                features, issued_date, expiry_date, validation_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            license_data['license_key'],
            license_data['license_type'],
            license_data['status'],
            license_data['customer_info'],
            license_data['features'],
            license_data['issued_date'],
            license_data['expiry_date'],
            license_data['validation_count']
        ))
    
    conn.commit()
    conn.close()

def insert_test_tickets():
    """Insert test support ticket data"""
    conn = sqlite3.connect('test_restaurant_pos.db')
    cursor = conn.cursor()
    
    test_tickets = [
        {
            'ticket_number': 'SUP-TEST-001',
            'user_id': 1,
            'category': 'Technical Support',
            'priority': 'High',
            'subject': 'Login Issue',
            'description': 'Unable to login with valid credentials',
            'status': 'Open'
        },
        {
            'ticket_number': 'SUP-TEST-002',
            'user_id': 2,
            'category': 'Bug Report',
            'priority': 'Medium',
            'subject': 'Calculation Error',
            'description': 'Order total calculated incorrectly',
            'status': 'In Progress'
        },
        {
            'ticket_number': 'SUP-TEST-003',
            'user_id': 3,
            'category': 'Feature Request',
            'priority': 'Low',
            'subject': 'Add Customer Loyalty',
            'description': 'Implement customer loyalty points system',
            'status': 'Closed'
        }
    ]
    
    for ticket_data in test_tickets:
        cursor.execute("""
            INSERT INTO support_tickets (
                ticket_number, user_id, category, priority,
                subject, description, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_data['ticket_number'],
            ticket_data['user_id'],
            ticket_data['category'],
            ticket_data['priority'],
            ticket_data['subject'],
            ticket_data['description'],
            ticket_data['status']
        ))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_test_database()
    insert_test_licenses()
    insert_test_tickets()
    print("Test data setup complete")
```

## License System Integration Tests

### Test Class Structure

```python
# tests/integration/test_license_integration.py
"""Integration tests for License System"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, Mock
import requests
from src.utils.license_manager import LicenseManager
from src.utils.license_validator import LicenseValidator
from src.utils.hardware_fingerprint import HardwareFingerprinter
from src.utils.license_storage import LicenseStorage

class TestLicenseIntegration(unittest.TestCase):
    """Integration tests for license system components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.test_db_path = 'test_restaurant_pos.db'
        cls.test_license_file = 'test_license.dat'
        
    def setUp(self):
        """Set up test fixtures"""
        # Create test application instance
        self.app = self.create_test_app()
        
        # Initialize license manager
        self.license_manager = LicenseManager(self.app)
        
        # Set up test license file
        self.setup_test_license_file()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_license_file):
            os.remove(self.test_license_file)
    
    def create_test_app(self):
        """Create test application instance"""
        app = Mock()
        app.db = self.create_test_database()
        return app
    
    def create_test_database(self):
        """Create test database connection"""
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        return conn
    
    def setup_test_license_file(self):
        """Set up test license file"""
        test_license_data = {
            'license_key': 'TEST-LIC-001-PROFESSIONAL',
            'license_type': 'professional',
            'status': 'active',
            'customer_info': {
                'name': 'Test Restaurant',
                'email': 'test@restaurant.com'
            },
            'features': [
                'order_management', 'inventory_tracking', 'reporting',
                'multi_user', 'api_access'
            ],
            'issued_date': '2023-01-01T00:00:00Z',
            'expiry_date': '2024-12-31T23:59:59Z',
            'validation_count': 5
        }
        
        with open(self.test_license_file, 'w') as f:
            json.dump(test_license_data, f)
    
    def test_license_activation_workflow(self):
        """Test complete license activation workflow"""
        # Arrange
        license_key = 'TEST-LIC-002-STANDARD'
        customer_info = {
            'name': 'New Restaurant',
            'email': 'new@restaurant.com'
        }
        
        # Mock license server response
        server_response = {
            'valid': True,
            'license_data': {
                'license_key': license_key,
                'license_type': 'standard',
                'status': 'active',
                'customer_info': customer_info,
                'features': ['order_management', 'inventory_tracking'],
                'issued_date': '2023-01-01T00:00:00Z',
                'expiry_date': '2024-12-31T23:59:59Z'
            },
            'signature': 'test_signature'
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = server_response
            mock_post.return_value.status_code = 200
            
            # Act
            result = self.license_manager.activate_license(license_key, customer_info)
            
            # Assert
            self.assertTrue(result)
            self.assertIsNotNone(self.license_manager.license_data)
            self.assertEqual(self.license_manager.license_data['license_key'], license_key)
            self.assertEqual(self.license_manager.license_data['license_type'], 'standard')
    
    def test_license_validation_with_database(self):
        """Test license validation with database integration"""
        # Arrange
        self.license_manager.license_data = self.load_test_license_from_db()
        
        # Act
        result = self.license_manager.validate_license()
        
        # Assert
        self.assertTrue(result.is_valid)
        self.assertEqual(result.validation_method, 'offline')
    
    def test_license_feature_access_control(self):
        """Test feature access control integration"""
        # Arrange
        self.license_manager.license_data = self.load_test_license_from_db()
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act & Assert
        # Test allowed features
        self.assertTrue(self.license_manager.check_feature_access('order_management'))
        self.assertTrue(self.license_manager.check_feature_access('inventory_tracking'))
        self.assertTrue(self.license_manager.check_feature_access('reporting'))
        
        # Test disallowed features
        self.assertFalse(self.license_manager.check_feature_access('advanced_analytics'))
        self.assertFalse(self.license_manager.check_feature_access('multi_location'))
    
    def test_license_expiry_enforcement(self):
        """Test license expiry enforcement"""
        # Arrange
        expired_license = self.load_test_license_from_db()
        expired_license['expiry_date'] = '2022-12-31T23:59:59Z'
        
        self.license_manager.license_data = expired_license
        
        # Act
        result = self.license_manager.validate_license()
        
        # Assert
        self.assertFalse(result.is_valid)
        self.assertIn('expired', result.error.lower())
    
    def test_hardware_binding_integration(self):
        """Test hardware binding integration"""
        # Arrange
        self.license_manager.license_data = self.load_test_license_from_db()
        
        # Mock hardware fingerprint
        with patch.object(self.license_manager.hardware_fingerprinter, 'generate_fingerprint') as mock_fingerprint:
            mock_fingerprint.return_value = 'test_hardware_fingerprint'
            
            # Act
            result = self.license_manager.validate_license()
            
            # Assert
            mock_fingerprint.assert_called_once()
    
    def test_license_storage_integration(self):
        """Test license storage integration"""
        # Arrange
        test_license_data = {
            'license_key': 'TEST-LIC-STORAGE',
            'license_type': 'professional',
            'features': ['order_management', 'reporting']
        }
        
        # Act
        save_result = self.license_manager.license_storage.save_license_data(test_license_data)
        loaded_data = self.license_manager.license_storage.load_license_data()
        
        # Assert
        self.assertTrue(save_result)
        self.assertIsNotNone(loaded_data)
        self.assertEqual(loaded_data['license_key'], test_license_data['license_key'])
        self.assertEqual(loaded_data['license_type'], test_license_data['license_type'])
    
    def test_license_audit_logging(self):
        """Test license audit logging integration"""
        # Arrange
        self.license_manager.license_data = self.load_test_license_from_db()
        
        # Act
        self.license_manager.validate_license()
        
        # Assert
        # Check that audit log entry was created
        cursor = self.app.db.cursor()
        cursor.execute("SELECT * FROM license_audit_log WHERE event_type = 'validation'")
        log_entries = cursor.fetchall()
        self.assertGreater(len(log_entries), 0)
    
    def test_license_transfer_workflow(self):
        """Test license transfer workflow"""
        # Arrange
        transfer_data = {
            'license_key': 'TEST-LIC-001-PROFESSIONAL',
            'new_hardware_fingerprint': 'new_hardware_fingerprint',
            'transfer_reason': 'Hardware upgrade'
        }
        
        # Mock license server response
        server_response = {
            'valid': True,
            'transfer_approved': True,
            'new_license_data': {
                'license_key': transfer_data['license_key'],
                'hardware_fingerprint': transfer_data['new_hardware_fingerprint']
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = server_response
            mock_post.return_value.status_code = 200
            
            # Act
            result = self.license_manager.transfer_license(transfer_data)
            
            # Assert
            self.assertTrue(result)
    
    def test_license_upgrade_workflow(self):
        """Test license upgrade workflow"""
        # Arrange
        upgrade_data = {
            'license_key': 'TEST-LIC-002-STANDARD',
            'upgrade_to': 'professional',
            'payment_info': {
                'payment_method': 'credit_card',
                'amount': 299.99
            }
        }
        
        # Mock license server response
        server_response = {
            'valid': True,
            'upgrade_approved': True,
            'new_license_data': {
                'license_key': upgrade_data['license_key'],
                'license_type': upgrade_data['upgrade_to'],
                'features': [
                    'order_management', 'inventory_tracking', 'reporting',
                    'multi_user', 'api_access'
                ]
            }
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = server_response
            mock_post.return_value.status_code = 200
            
            # Act
            result = self.license_manager.upgrade_license(upgrade_data)
            
            # Assert
            self.assertTrue(result)
    
    def load_test_license_from_db(self):
        """Load test license from database"""
        cursor = self.app.db.cursor()
        cursor.execute("SELECT * FROM licenses WHERE license_key = 'TEST-LIC-001-PROFESSIONAL'")
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        
        return None
```

## Support System Integration Tests

### Test Class Structure

```python
# tests/integration/test_support_integration.py
"""Integration tests for Support System"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, Mock
from src.utils.support_manager import SupportManager
from src.managers.ticket_manager import TicketManager
from src.managers.contact_manager import ContactManager
from src.utils.email_service import EmailService

class TestSupportIntegration(unittest.TestCase):
    """Integration tests for support system components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.test_db_path = 'test_restaurant_pos.db'
        
    def setUp(self):
        """Set up test fixtures"""
        # Create test application instance
        self.app = self.create_test_app()
        
        # Initialize support manager
        self.support_manager = SupportManager(self.app)
        
        # Set up test email service
        self.setup_test_email_service()
    
    def create_test_app(self):
        """Create test application instance"""
        app = Mock()
        app.db = self.create_test_database()
        return app
    
    def create_test_database(self):
        """Create test database connection"""
        import sqlite3
        conn = sqlite3.connect(self.test_db_path)
        return conn
    
    def setup_test_email_service(self):
        """Set up test email service configuration"""
        self.email_config = {
            'smtp_server': 'localhost',
            'smtp_port': 1025,
            'username': 'test@test.com',
            'password': 'test_password',
            'use_tls': False
        }
        self.support_manager.email_service = EmailService(self.email_config)
    
    def test_ticket_creation_workflow(self):
        """Test complete ticket creation workflow"""
        # Arrange
        ticket_data = {
            'user_id': 1,
            'category': 'Technical Support',
            'subject': 'Login Issue',
            'description': 'Unable to login with valid credentials',
            'priority': 'High'
        }
        
        # Act
        ticket_id = self.support_manager.create_ticket(
            ticket_data['user_id'],
            ticket_data['category'],
            ticket_data['subject'],
            ticket_data['description'],
            ticket_data['priority']
        )
        
        # Assert
        self.assertIsNotNone(ticket_id)
        
        # Verify ticket was created in database
        cursor = self.app.db.cursor()
        cursor.execute("SELECT * FROM support_tickets WHERE id = ?", (ticket_id,))
        ticket = cursor.fetchone()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket[2], ticket_data['category'])  # category
        self.assertEqual(ticket[3], ticket_data['priority'])  # priority
        self.assertEqual(ticket[4], ticket_data['subject'])  # subject
    
    def test_ticket_assignment_workflow(self):
        """Test ticket assignment workflow"""
        # Arrange
        # Create a ticket first
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
        )
        
        assigned_to = 2  # Support agent ID
        
        # Act
        result = self.support_manager.assign_ticket(ticket_id, assigned_to)
        
        # Assert
        self.assertTrue(result)
        
        # Verify assignment in database
        cursor = self.app.db.cursor()
        cursor.execute("SELECT assigned_to FROM support_tickets WHERE id = ?", (ticket_id,))
        assigned = cursor.fetchone()
        self.assertEqual(assigned[0], assigned_to)
    
    def test_ticket_conversation_workflow(self):
        """Test ticket conversation workflow"""
        # Arrange
        # Create a ticket first
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
        )
        
        # Add conversation messages
        messages = [
            {'user_id': 1, 'message': 'This is an update from the customer', 'is_internal': False},
            {'user_id': 2, 'message': 'This is an internal note', 'is_internal': True},
            {'user_id': 2, 'message': 'This is a response to the customer', 'is_internal': False}
        ]
        
        # Act
        conversation_ids = []
        for message in messages:
            conv_id = self.support_manager.ticket_manager.add_conversation(
                ticket_id, message['user_id'], message['message'], message['is_internal']
            )
            conversation_ids.append(conv_id)
        
        # Assert
        self.assertEqual(len(conversation_ids), 3)
        
        # Verify conversations in database
        cursor = self.app.db.cursor()
        cursor.execute(
            "SELECT * FROM ticket_conversations WHERE ticket_id = ? ORDER BY created_at",
            (ticket_id,)
        )
        conversations = cursor.fetchall()
        self.assertEqual(len(conversations), 3)
    
    def test_contact_form_workflow(self):
        """Test contact form submission workflow"""
        # Arrange
        contact_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1234567890',
            'contact_method': 'email',
            'subject': 'General Inquiry',
            'message': 'I would like to know more about your POS system'
        }
        
        # Act
        contact_id = self.support_manager.contact_manager.submit_contact_form(contact_data)
        
        # Assert
        self.assertIsNotNone(contact_id)
        
        # Verify contact form in database
        cursor = self.app.db.cursor()
        cursor.execute("SELECT * FROM contact_forms WHERE id = ?", (contact_id,))
        contact = cursor.fetchone()
        self.assertIsNotNone(contact)
        self.assertEqual(contact[2], contact_data['name'])  # name
        self.assertEqual(contact[5], contact_data['subject'])  # subject
    
    def test_bug_report_workflow(self):
        """Test bug report submission workflow"""
        # Arrange
        bug_data = {
            'user_id': 1,
            'error_type': 'RuntimeError',
            'error_message': 'Division by zero error',
            'stack_trace': 'Traceback (most recent call last)...',
            'reproduction_steps': '1. Create order with zero quantity\n2. Try to calculate total',
            'session_info': json.dumps({'user_id': 1, 'session_id': 'sess_123'}),
            'system_info': json.dumps({'os': 'Windows 10', 'app_version': '2.1.0'}),
            'app_version': '2.1.0',
            'priority': 'High'
        }
        
        # Act
        bug_id = self.support_manager.bug_manager.submit_bug_report(bug_data)
        
        # Assert
        self.assertIsNotNone(bug_id)
        
        # Verify bug report in database
        cursor = self.app.db.cursor()
        cursor.execute("SELECT * FROM bug_reports WHERE id = ?", (bug_id,))
        bug = cursor.fetchone()
        self.assertIsNotNone(bug)
        self.assertEqual(bug[2], bug_data['error_type'])  # error_type
        self.assertEqual(bug[3], bug_data['error_message'])  # error_message
        self.assertEqual(bug[10], bug_data['priority'])  # priority
    
    def test_email_notification_integration(self):
        """Test email notification integration"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-TEST-001',
            'user_email': 'user@example.com',
            'subject': 'Test Ticket',
            'description': 'Test description'
        }
        
        # Mock SMTP server
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.support_manager.email_service.send_ticket_acknowledgment(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    def test_ticket_search_integration(self):
        """Test ticket search functionality"""
        # Arrange
        # Create test tickets
        ticket_ids = []
        for i in range(5):
            ticket_id = self.support_manager.create_ticket(
                i+1, 'Technical Support', f'Test Issue {i+1}', 
                f'Test description {i+1}', 'Medium'
            )
            ticket_ids.append(ticket_id)
        
        # Search criteria
        search_criteria = {
            'category': 'Technical Support',
            'status': 'Open'
        }
        
        # Act
        results = self.support_manager.search_tickets(search_criteria)
        
        # Assert
        self.assertGreaterEqual(len(results), 5)  # Should find at least our test tickets
        
        # Verify all results match search criteria
        for ticket in results:
            self.assertEqual(ticket['category'], 'Technical Support')
            self.assertEqual(ticket['status'], 'Open')
    
    def test_ticket_statistics_integration(self):
        """Test ticket statistics generation"""
        # Arrange
        # Create test tickets with different priorities
        priorities = ['Low', 'Medium', 'High', 'Critical']
        for priority in priorities:
            self.support_manager.create_ticket(
                1, 'Technical Support', f'{priority} Priority Issue',
                f'Test description with {priority.lower()} priority', priority
            )
        
        # Act
        stats = self.support_manager.get_ticket_statistics()
        
        # Assert
        self.assertIsNotNone(stats)
        self.assertIn('total_tickets', stats)
        self.assertIn('tickets_by_priority', stats)
        self.assertIn('tickets_by_category', stats)
        
        # Verify priority statistics
        for priority in priorities:
            self.assertIn(priority, stats['tickets_by_priority'])
    
    def test_file_attachment_workflow(self):
        """Test file attachment workflow"""
        # Arrange
        # Create a ticket first
        ticket_id = self.support_manager.create_ticket(
            1, 'Bug Report', 'UI Issue', 'Button not working', 'High'
        )
        
        # Create test file
        test_file_path = 'test_screenshot.png'
        with open(test_file_path, 'wb') as f:
            f.write(b'fake image data')
        
        try:
            # Act
            attachment_id = self.support_manager.ticket_manager.add_attachment(
                ticket_id, test_file_path, 'screenshot.png'
            )
            
            # Assert
            self.assertIsNotNone(attachment_id)
            
            # Verify attachment in database
            cursor = self.app.db.cursor()
            cursor.execute(
                "SELECT * FROM support_attachments WHERE ticket_id = ?",
                (ticket_id,)
            )
            attachment = cursor.fetchone()
            self.assertIsNotNone(attachment)
            self.assertEqual(attachment[3], 'screenshot.png')  # filename
            
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
    
    def test_ticket_escalation_workflow(self):
        """Test ticket escalation workflow"""
        # Arrange
        # Create a high priority ticket
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'System Crash', 
            'Application crashes on startup', 'High'
        )
        
        # Act
        result = self.support_manager.escalate_ticket(ticket_id)
        
        # Assert
        self.assertTrue(result)
        
        # Verify escalation in database
        cursor = self.app.db.cursor()
        cursor.execute("SELECT priority FROM support_tickets WHERE id = ?", (ticket_id,))
        priority = cursor.fetchone()
        self.assertEqual(priority[0], 'Critical')
```

## Cross-System Integration Tests

### Test Class Structure

```python
# tests/integration/test_cross_system_integration.py
"""Cross-system integration tests"""

import unittest
from unittest.mock import patch, Mock
from src.utils.support_manager import SupportManager
from src.utils.license_manager import LicenseManager
from src.utils.license_decorator import require_license

class TestCrossSystemIntegration(unittest.TestCase):
    """Cross-system integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = self.create_test_app()
        self.license_manager = LicenseManager(self.app)
        self.support_manager = SupportManager(self.app)
    
    def create_test_app(self):
        """Create test application instance"""
        app = Mock()
        app.db = self.create_test_database()
        return app
    
    def create_test_database(self):
        """Create test database connection"""
        import sqlite3
        conn = sqlite3.connect('test_restaurant_pos.db')
        return conn
    
    def test_license_required_support_features(self):
        """Test support features that require specific licenses"""
        # Arrange
        # Set up professional license
        self.license_manager.license_data = {
            'license_type': 'professional',
            'features': ['order_management', 'inventory_tracking', 'reporting', 'multi_user', 'api_access']
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Test professional license features
        self.assertTrue(self.support_manager.check_feature_access('priority_support'))
        self.assertTrue(self.support_manager.check_feature_access('advanced_reporting'))
        self.assertTrue(self.support_manager.check_feature_access('api_integration'))
        
        # Test unavailable features
        self.assertFalse(self.support_manager.check_feature_access('enterprise_analytics'))
        self.assertFalse(self.support_manager.check_feature_access('custom_integrations'))
    
    def test_license_based_support_limits(self):
        """Test support limits based on license type"""
        # Arrange
        test_cases = [
            {
                'license_type': 'trial',
                'max_tickets': 5,
                'max_attachments': 2,
                'priority_support': False
            },
            {
                'license_type': 'standard',
                'max_tickets': 25,
                'max_attachments': 5,
                'priority_support': False
            },
            {
                'license_type': 'professional',
                'max_tickets': 100,
                'max_attachments': 10,
                'priority_support': True
            },
            {
                'license_type': 'enterprise',
                'max_tickets': -1,  # Unlimited
                'max_attachments': 20,
                'priority_support': True
            }
        ]
        
        for case in test_cases:
            with self.subTest(license_type=case['license_type']):
                # Set up license
                self.license_manager.license_data = {
                    'license_type': case['license_type'],
                    'features': ['basic_support']
                }
                self.license_manager.validation_result = Mock(is_valid=True)
                
                # Check support limits
                limits = self.support_manager.get_support_limits()
                
                self.assertEqual(limits['max_tickets'], case['max_tickets'])
                self.assertEqual(limits['max_attachments'], case['max_attachments'])
                self.assertEqual(limits['priority_support'], case['priority_support'])
    
    def test_support_ticket_license_validation(self):
        """Test license validation for support ticket creation"""
        # Arrange
        # Set up expired license
        self.license_manager.license_data = {
            'license_type': 'standard',
            'expiry_date': '2022-12-31T23:59:59Z'
        }
        self.license_manager.validation_result = Mock(is_valid=False)
        
        # Act & Assert
        # Should not be able to create support tickets with expired license
        with self.assertRaises(Exception):
            self.support_manager.create_ticket(
                1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
            )
    
    def test_license_upgrade_support_benefits(self):
        """Test support benefits after license upgrade"""
        # Arrange
        # Start with standard license
        self.license_manager.license_data = {
            'license_type': 'standard',
            'features': ['basic_support']
        }
        
        # Check initial support benefits
        initial_benefits = self.support_manager.get_support_benefits()
        self.assertFalse(initial_benefits['priority_support'])
        self.assertEqual(initial_benefits['response_time'], '48 hours')
        
        # Upgrade to professional license
        self.license_manager.license_data = {
            'license_type': 'professional',
            'features': ['priority_support', 'advanced_reporting']
        }
        
        # Act
        upgraded_benefits = self.support_manager.get_support_benefits()
        
        # Assert
        self.assertTrue(upgraded_benefits['priority_support'])
        self.assertEqual(upgraded_benefits['response_time'], '24 hours')
        self.assertTrue(upgraded_benefits['advanced_reporting'])
    
    def test_support_usage_license_impact(self):
        """Test support usage impact on license validation"""
        # Arrange
        # Set up license with support usage limits
        self.license_manager.license_data = {
            'license_type': 'standard',
            'features': ['basic_support'],
            'support_limits': {
                'max_monthly_tickets': 25,
                'current_monthly_tickets': 24
            }
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act - Create one more ticket (should reach limit)
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
        )
        
        # Assert
        self.assertIsNotNone(ticket_id)
        
        # Check license validation after reaching limit
        validation_result = self.license_manager.validate_license()
        self.assertTrue(validation_result.is_valid)  # Still valid but at limit
        
        # Try to create another ticket (should exceed limit)
        with self.assertRaises(Exception):
            self.support_manager.create_ticket(
                2, 'Technical Support', 'Another Issue', 'Another description', 'Medium'
            )
    
    def test_license_audit_support_events(self):
        """Test license audit logging for support events"""
        # Arrange
        self.license_manager.license_data = {
            'license_type': 'professional',
            'features': ['priority_support']
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act - Create support ticket
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'Test Issue', 'Test description', 'High'
        )
        
        # Assert - Check audit log
        cursor = self.app.db.cursor()
        cursor.execute(
            "SELECT * FROM license_audit_log WHERE event_type = 'support_ticket_created'"
        )
        audit_entries = cursor.fetchall()
        self.assertGreater(len(audit_entries), 0)
        
        # Verify audit entry contains ticket information
        audit_entry = audit_entries[0]
        event_data = json.loads(audit_entry[3])  # event_data column
        self.assertIn('ticket_id', event_data)
        self.assertEqual(event_data['ticket_id'], ticket_id)
    
    @require_license('priority_support')
    def test_license_decorator_support_features(self):
        """Test license decorator for support features"""
        # This test verifies that the license decorator properly restricts access
        # to support features based on license
        
        # Arrange - Mock license without priority support
        self.license_manager.license_data = {
            'license_type': 'standard',
            'features': ['basic_support']  # No priority_support
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act & Assert - Should raise exception due to missing feature
        with self.assertRaises(Exception):
            self.support_manager.create_priority_ticket(
                1, 'Critical Issue', 'This is a critical issue', 'Critical'
            )
    
    def test_support_license_integration_error_handling(self):
        """Test error handling in support-license integration"""
        # Arrange
        # Mock license manager to raise exception
        self.license_manager.validate_license.side_effect = Exception("License validation failed")
        
        # Act & Assert
        # Support system should handle license validation errors gracefully
        with self.assertRaises(Exception):
            self.support_manager.create_ticket(
                1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
            )
    
    def test_support_license_data_synchronization(self):
        """Test data synchronization between support and license systems"""
        # Arrange
        # Create support ticket
        ticket_id = self.support_manager.create_ticket(
            1, 'Technical Support', 'Test Issue', 'Test description', 'Medium'
        )
        
        # Update license
        self.license_manager.license_data = {
            'license_type': 'professional',
            'features': ['priority_support']
        }
        
        # Act - Update ticket to use priority support
        result = self.support_manager.update_ticket(ticket_id, priority='High')
        
        # Assert
        self.assertTrue(result)
        
        # Verify license system was notified of priority support usage
        cursor = self.app.db.cursor()
        cursor.execute(
            "SELECT * FROM license_audit_log WHERE event_type = 'priority_support_used'"
        )
        audit_entries = cursor.fetchall()
        self.assertGreater(len(audit_entries), 0)
```

## Database Integration Tests

### Test Class Structure

```python
# tests/integration/test_database_integration.py
"""Database integration tests"""

import unittest
import sqlite3
import tempfile
import os
from src.models.database import DatabaseManager
from src.models.license import License
from src.models.support_ticket import SupportTicket

class TestDatabaseIntegration(unittest.TestCase):
    """Database integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(self.test_db_path)
        self.create_test_tables()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def create_test_tables(self):
        """Create test database tables"""
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.executescript(schema)
        conn.commit()
        conn.close()
    
    def test_license_crud_operations(self):
        """Test license CRUD operations"""
        # Create license
        license_data = {
            'license_key': 'TEST-LIC-001',
            'license_type': 'professional',
            'status': 'active',
            'customer_info': '{"name": "Test Restaurant"}',
            'features': '["order_management", "reporting"]',
            'issued_date': '2023-01-01',
            'expiry_date': '2024-12-31'
        }
        
        license_id = self.db_manager.insert('licenses', license_data)
        self.assertIsNotNone(license_id)
        
        # Read license
        retrieved_license = self.db_manager.get_by_id('licenses', license_id)
        self.assertIsNotNone(retrieved_license)
        self.assertEqual(retrieved_license['license_key'], 'TEST-LIC-001')
        self.assertEqual(retrieved_license['license_type'], 'professional')
        
        # Update license
        update_data = {'status': 'inactive'}
        update_result = self.db_manager.update('licenses', license_id, update_data)
        self.assertTrue(update_result)
        
        updated_license = self.db_manager.get_by_id('licenses', license_id)
        self.assertEqual(updated_license['status'], 'inactive')
        
        # Delete license
        delete_result = self.db_manager.delete('licenses', license_id)
        self.assertTrue(delete_result)
        
        deleted_license = self.db_manager.get_by_id('licenses', license_id)
        self.assertIsNone(deleted_license)
    
    def test_support_ticket_crud_operations(self):
        """Test support ticket CRUD operations"""
        # Create support ticket
        ticket_data = {
            'ticket_number': 'SUP-TEST-001',
            'user_id': 1,
            'category': 'Technical Support',
            'priority': 'High',
            'subject': 'Login Issue',
            'description': 'Unable to login with valid credentials',
            'status': 'Open'
        }
        
        ticket_id = self.db_manager.insert('support_tickets', ticket_data)
        self.assertIsNotNone(ticket_id)
        
        # Read support ticket
        retrieved_ticket = self.db_manager.get_by_id('support_tickets', ticket_id)
        self.assertIsNotNone(retrieved_ticket)
        self.assertEqual(retrieved_ticket['ticket_number'], 'SUP-TEST-001')
        self.assertEqual(retrieved_ticket['category'], 'Technical Support')
        
        # Update support ticket
        update_data = {'status': 'In Progress', 'assigned_to': 2}
        update_result = self.db_manager.update('support_tickets', ticket_id, update_data)
        self.assertTrue(update_result)
        
        updated_ticket = self.db_manager.get_by_id('support_tickets', ticket_id)
        self.assertEqual(updated_ticket['status'], 'In Progress')
        self.assertEqual(updated_ticket['assigned_to'], 2)
        
        # Delete support ticket
        delete_result = self.db_manager.delete('support_tickets', ticket_id)
        self.assertTrue(delete_result)
        
        deleted_ticket = self.db_manager.get_by_id('support_tickets', ticket_id)
        self.assertIsNone(deleted_ticket)
    
    def test_database_transaction_rollback(self):
        """Test database transaction rollback on error"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-TRANSACTION',
            'license_type': 'professional',
            'status': 'active'
        }
        
        # Act & Assert
        try:
            with self.db_manager.transaction():
                # Insert license
                license_id = self.db_manager.insert('licenses', license_data)
                self.assertIsNotNone(license_id)
                
                # Intentionally cause an error
                raise Exception("Intentional error for rollback test")
        except Exception:
            pass  # Expected error
        
        # Verify license was not inserted due to rollback
        retrieved_license = self.db_manager.get_one('licenses', 
                                                 {'license_key': 'TEST-LIC-TRANSACTION'})
        self.assertIsNone(retrieved_license)
    
    def test_database_foreign_key_constraints(self):
        """Test database foreign key constraints"""
        # Create support ticket
        ticket_data = {
            'ticket_number': 'SUP-TEST-FK-001',
            'user_id': 999,  # Non-existent user ID
            'category': 'Technical Support',
            'priority': 'Medium',
            'subject': 'Test Issue',
            'description': 'Test description',
            'status': 'Open'
        }
        
        # Act & Assert
        # Should fail due to foreign key constraint
        with self.assertRaises(Exception):
            self.db_manager.insert('support_tickets', ticket_data)
    
    def test_database_index_performance(self):
        """Test database index performance"""
        # Insert test data
        for i in range(1000):
            ticket_data = {
                'ticket_number': f'SUP-PERF-{i:04d}',
                'user_id': (i % 10) + 1,
                'category': ['Technical Support', 'Bug Report', 'Feature Request'][i % 3],
                'priority': ['Low', 'Medium', 'High', 'Critical'][i % 4],
                'subject': f'Performance Test Issue {i}',
                'description': f'Test description {i}',
                'status': 'Open'
            }
            self.db_manager.insert('support_tickets', ticket_data)
        
        # Test query performance with indexed columns
        import time
        
        # Query with indexed column (user_id)
        start_time = time.time()
        results = self.db_manager.get_many('support_tickets', {'user_id': 5})
        indexed_time = time.time() - start_time
        
        # Query with non-indexed column (description)
        start_time = time.time()
        results = self.db_manager.get_many('support_tickets', 
                                         {'description': 'Test description 500'})
        non_indexed_time = time.time() - start_time
        
        # Indexed query should be faster
        self.assertLess(indexed_time, non_indexed_time)
    
    def test_database_connection_pooling(self):
        """Test database connection pooling"""
        # Create multiple concurrent connections
        import threading
        import queue
        
        results = queue.Queue()
        
        def db_operation(thread_id):
            try:
                # Perform database operation
                license_data = {
                    'license_key': f'TEST-LIC-POOL-{thread_id}',
                    'license_type': 'professional',
                    'status': 'active'
                }
                license_id = self.db_manager.insert('licenses', license_data)
                results.put(('success', thread_id, license_id))
            except Exception as e:
                results.put(('error', thread_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=db_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations succeeded
        success_count = 0
        error_count = 0
        
        while not results.empty():
            status, thread_id, result = results.get()
            if status == 'success':
                success_count += 1
            else:
                error_count += 1
        
        self.assertEqual(success_count, 10)
        self.assertEqual(error_count, 0)
    
    def test_database_backup_and_restore(self):
        """Test database backup and restore"""
        # Insert test data
        license_data = {
            'license_key': 'TEST-LIC-BACKUP',
            'license_type': 'professional',
            'status': 'active'
        }
        license_id = self.db_manager.insert('licenses', license_data)
        
        # Create backup
        backup_path = tempfile.mktemp(suffix='.db')
        self.db_manager.backup(backup_path)
        
        # Verify backup exists
        self.assertTrue(os.path.exists(backup_path))
        
        # Delete original data
        self.db_manager.delete('licenses', license_id)
        deleted_license = self.db_manager.get_by_id('licenses', license_id)
        self.assertIsNone(deleted_license)
        
        # Restore from backup
        self.db_manager.restore(backup_path)
        
        # Verify data restored
        restored_license = self.db_manager.get_one('licenses', 
                                                {'license_key': 'TEST-LIC-BACKUP'})
        self.assertIsNotNone(restored_license)
        
        # Clean up
        os.remove(backup_path)
    
    def test_database_migration(self):
        """Test database migration"""
        # Get current database version
        current_version = self.db_manager.get_schema_version()
        
        # Apply migration
        migration_sql = """
        CREATE TABLE IF NOT EXISTS migration_test (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_data TEXT
        );
        
        INSERT INTO schema_versions (version, applied_at) 
        VALUES (2, datetime('now'));
        """
        
        self.db_manager.execute_migration(migration_sql)
        
        # Verify migration applied
        new_version = self.db_manager.get_schema_version()
        self.assertEqual(new_version, current_version + 1)
        
        # Verify new table exists
        table_exists = self.db_manager.table_exists('migration_test')
        self.assertTrue(table_exists)
```

## External Service Integration Tests

### Test Class Structure

```python
# tests/integration/test_external_service_integration.py
"""External service integration tests"""

import unittest
from unittest.mock import patch, Mock
import requests
from src.utils.license_api_client import LicenseApiClient
from src.utils.email_service import EmailService

class TestExternalServiceIntegration(unittest.TestCase):
    """External service integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.license_api_client = LicenseApiClient(
            base_url='https://test-license.restaurantpos.com/api/v1',
            api_key='test_api_key'
        )
        
        self.email_service = EmailService({
            'smtp_server': 'localhost',
            'smtp_port': 1025,
            'username': 'test@test.com',
            'password': 'test_password',
            'use_tls': False
        })
    
    def test_license_server_integration(self):
        """Test license server integration"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-EXTERNAL',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        expected_response = {
            'valid': True,
            'license_data': {
                'license_key': 'TEST-LIC-EXTERNAL',
                'license_type': 'professional',
                'status': 'active',
                'features': ['order_management', 'reporting']
            },
            'signature': 'test_signature'
        }
        
        # Mock HTTP response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response
            
            # Act
            result = self.license_api_client.validate_license(license_data, 'test_signature')
            
            # Assert
            self.assertIsNotNone(result)
            self.assertTrue(result['valid'])
            self.assertEqual(result['license_data']['license_key'], 'TEST-LIC-EXTERNAL')
            mock_post.assert_called_once()
    
    def test_license_server_error_handling(self):
        """Test license server error handling"""
        # Arrange
        license_data = {
            'license_key': 'INVALID-LICENSE',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        # Mock HTTP error response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'error': 'Invalid license key',
                'code': 'INVALID_LICENSE'
            }
            mock_post.return_value = mock_response
            
            # Act
            with self.assertRaises(Exception):
                self.license_api_client.validate_license(license_data, 'test_signature')
            
            # Assert
            mock_post.assert_called_once()
    
    def test_license_server_timeout_handling(self):
        """Test license server timeout handling"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-TIMEOUT',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        # Mock timeout
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            # Act & Assert
            with self.assertRaises(requests.exceptions.Timeout):
                self.license_api_client.validate_license(license_data, 'test_signature')
    
    def test_email_service_integration(self):
        """Test email service integration"""
        # Arrange
        email_data = {
            'to': 'recipient@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email'
        }
        
        # Mock SMTP server
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_email(email_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    def test_email_service_authentication(self):
        """Test email service authentication"""
        # Arrange
        email_config = {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'user@example.com',
            'password': 'password123',
            'use_tls': True
        }
        
        email_service = EmailService(email_config)
        email_data = {
            'to': 'recipient@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email'
        }
        
        # Mock SMTP server with authentication
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = email_service.send_email(email_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.example.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('user@example.com', 'password123')
    
    def test_email_service_error_handling(self):
        """Test email service error handling"""
        # Arrange
        email_data = {
            'to': 'invalid-email',
            'subject': 'Test Email',
            'body': 'This is a test email'
        }
        
        # Mock SMTP error
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_server.send_message.side_effect = Exception("Invalid email address")
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_email(email_data)
            
            # Assert
            self.assertFalse(result)
    
    def test_external_service_retry_mechanism(self):
        """Test external service retry mechanism"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-RETRY',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        expected_response = {
            'valid': True,
            'license_data': {
                'license_key': 'TEST-LIC-RETRY',
                'license_type': 'professional'
            }
        }
        
        # Mock initial failure followed by success
        with patch('requests.post') as mock_post:
            mock_response_fail = Mock()
            mock_response_fail.status_code = 500
            mock_response_fail.raise_for_status.side_effect = Exception("Server error")
            
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = expected_response
            
            mock_post.side_effect = [mock_response_fail, mock_response_success]
            
            # Act
            result = self.license_api_client.validate_license(license_data, 'test_signature')
            
            # Assert
            self.assertIsNotNone(result)
            self.assertTrue(result['valid'])
            self.assertEqual(mock_post.call_count, 2)  # Should retry once
    
    def test_external_service_rate_limiting(self):
        """Test external service rate limiting"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-RATELIMIT',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        # Mock rate limit response
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            mock_response.json.return_value = {
                'error': 'Rate limit exceeded',
                'retry_after': 60
            }
            mock_post.return_value = mock_response
            
            # Act & Assert
            with self.assertRaises(Exception):
                self.license_api_client.validate_license(license_data, 'test_signature')
    
    def test_external_service_ssl_verification(self):
        """Test external service SSL verification"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-SSL',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        # Mock SSL error
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.SSLError("SSL verification failed")
            
            # Act & Assert
            with self.assertRaises(requests.exceptions.SSLError):
                self.license_api_client.validate_license(license_data, 'test_signature')
    
    def test_external_service_response_validation(self):
        """Test external service response validation"""
        # Arrange
        license_data = {
            'license_key': 'TEST-LIC-VALIDATION',
            'hardware_fingerprint': 'test_fingerprint',
            'validation_type': 'online'
        }
        
        # Mock invalid response format
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'invalid_format': 'missing_required_fields'
            }
            mock_post.return_value = mock_response
            
            # Act & Assert
            with self.assertRaises(Exception):
                self.license_api_client.validate_license(license_data, 'test_signature')
```

## UI Integration Tests

### Test Class Structure

```python
# tests/integration/test_ui_integration.py
"""UI integration tests"""

import unittest
from unittest.mock import patch, Mock
import tkinter as tk
from src.ui.license_activation_dialog import LicenseActivationDialog
from src.ui.support_screen import SupportScreen
from src.utils.license_manager import LicenseManager
from src.utils.support_manager import SupportManager

class TestUIIntegration(unittest.TestCase):
    """UI integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.root = tk.Tk()
        self.app = Mock()
        self.app.db = Mock()
        
        self.license_manager = LicenseManager(self.app)
        self.support_manager = SupportManager(self.app)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.root.destroy()
    
    def test_license_activation_dialog_integration(self):
        """Test license activation dialog integration"""
        # Arrange
        dialog = LicenseActivationDialog(self.root, self.license_manager)
        
        # Mock successful license activation
        with patch.object(self.license_manager, 'activate_license') as mock_activate:
            mock_activate.return_value = True
            
            # Simulate user input
            dialog.license_key_entry.insert(0, 'TEST-LIC-001')
            dialog.customer_name_entry.insert(0, 'Test Restaurant')
            dialog.customer_email_entry.insert(0, 'test@restaurant.com')
            
            # Act
            dialog.activate_license()
            
            # Assert
            mock_activate.assert_called_once()
            self.assertEqual(mock_activate.call_args[0][0], 'TEST-LIC-001')
            self.assertEqual(mock_activate.call_args[0][1]['name'], 'Test Restaurant')
            self.assertEqual(mock_activate.call_args[0][1]['email'], 'test@restaurant.com')
    
    def test_license_status_display_integration(self):
        """Test license status display integration"""
        # Arrange
        from src.ui.license_status_screen import LicenseStatusScreen
        status_screen = LicenseStatusScreen(self.root, self.license_manager)
        
        # Mock license data
        self.license_manager.license_data = {
            'license_key': 'TEST-LIC-001',
            'license_type': 'professional',
            'status': 'active',
            'expiry_date': '2024-12-31',
            'features': ['order_management', 'inventory_tracking', 'reporting']
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act
        status_screen.update_license_display()
        
        # Assert
        self.assertIn('TEST-LIC-001', status_screen.license_key_label.cget("text"))
        self.assertIn('professional', status_screen.license_type_label.cget("text"))
        self.assertIn('active', status_screen.status_label.cget("text"))
    
    def test_support_ticket_creation_ui_integration(self):
        """Test support ticket creation UI integration"""
        # Arrange
        support_screen = SupportScreen(self.root, self.support_manager)
        
        # Mock successful ticket creation
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            mock_create.return_value = 123
            
            # Simulate user input
            support_screen.category_var.set('Technical Support')
            support_screen.priority_var.set('High')
            support_screen.subject_entry.insert(0, 'Test Issue')
            support_screen.description_text.insert('1.0', 'Test description')
            
            # Act
            support_screen.create_ticket()
            
            # Assert
            mock_create.assert_called_once()
            self.assertEqual(mock_create.call_args[0][1], 'Technical Support')
            self.assertEqual(mock_create.call_args[0][3], 'Test Issue')
            self.assertEqual(mock_create.call_args[0][4], 'High')
    
    def test_support_ticket_list_display_integration(self):
        """Test support ticket list display integration"""
        # Arrange
        support_screen = SupportScreen(self.root, self.support_manager)
        
        # Mock ticket data
        mock_tickets = [
            {
                'id': 1,
                'ticket_number': 'SUP-001',
                'subject': 'Login Issue',
                'status': 'Open',
                'priority': 'High',
                'created_at': '2023-01-01 10:00:00'
            },
            {
                'id': 2,
                'ticket_number': 'SUP-002',
                'subject': 'Calculation Error',
                'status': 'In Progress',
                'priority': 'Medium',
                'created_at': '2023-01-02 14:30:00'
            }
        ]
        
        with patch.object(self.support_manager, 'get_user_tickets') as mock_get:
            mock_get.return_value = mock_tickets
            
            # Act
            support_screen.refresh_ticket_list()
            
            # Assert
            self.assertEqual(len(support_screen.ticket_tree.get_children()), 2)
            
            # Verify first ticket
            first_item = support_screen.ticket_tree.get_children()[0]
            values = support_screen.ticket_tree.item(first_item)['values']
            self.assertEqual(values[0], 'SUP-001')
            self.assertEqual(values[1], 'Login Issue')
            self.assertEqual(values[2], 'Open')
            self.assertEqual(values[3], 'High')
    
    def test_license_feature_access_ui_integration(self):
        """Test license feature access UI integration"""
        # Arrange
        from src.ui.main_screen import MainScreen
        main_screen = MainScreen(self.root, self.license_manager)
        
        # Mock license with limited features
        self.license_manager.license_data = {
            'license_type': 'standard',
            'features': ['order_management', 'inventory_tracking']
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act
        main_screen.update_feature_access()
        
        # Assert
        # Standard features should be enabled
        self.assertTrue(main_screen.order_management_button.cget('state') == 'normal')
        self.assertTrue(main_screen.inventory_tracking_button.cget('state') == 'normal')
        
        # Professional features should be disabled
        self.assertTrue(main_screen.advanced_reporting_button.cget('state') == 'disabled')
        self.assertTrue(main_screen.multi_user_button.cget('state') == 'disabled')
    
    def test_error_display_ui_integration(self):
        """Test error display UI integration"""
        # Arrange
        dialog = LicenseActivationDialog(self.root, self.license_manager)
        
        # Mock license activation error
        with patch.object(self.license_manager, 'activate_license') as mock_activate:
            mock_activate.return_value = False
            mock_activate.side_effect = Exception("Invalid license key")
            
            # Act
            dialog.activate_license()
            
            # Assert
            # Error message should be displayed
            self.assertTrue(hasattr(dialog, 'error_label'))
            self.assertIn('Invalid license key', dialog.error_label.cget('text'))
    
    def test_ui_data_validation_integration(self):
        """Test UI data validation integration"""
        # Arrange
        dialog = LicenseActivationDialog(self.root, self.license_manager)
        
        # Test empty license key
        dialog.license_key_entry.delete(0, tk.END)
        dialog.customer_name_entry.insert(0, 'Test Restaurant')
        dialog.customer_email_entry.insert(0, 'test@restaurant.com')
        
        # Act
        is_valid = dialog.validate_input()
        
        # Assert
        self.assertFalse(is_valid)
        self.assertIn('License key is required', dialog.error_label.cget('text'))
        
        # Test invalid email
        dialog.license_key_entry.insert(0, 'TEST-LIC-001')
        dialog.customer_email_entry.delete(0, tk.END)
        dialog.customer_email_entry.insert(0, 'invalid-email')
        
        # Act
        is_valid = dialog.validate_input()
        
        # Assert
        self.assertFalse(is_valid)
        self.assertIn('Invalid email address', dialog.error_label.cget('text'))
    
    def test_ui_responsiveness_integration(self):
        """Test UI responsiveness during operations"""
        # Arrange
        support_screen = SupportScreen(self.root, self.support_manager)
        
        # Mock slow ticket creation
        with patch.object(self.support_manager, 'create_ticket') as mock_create:
            import time
            def slow_create(*args, **kwargs):
                time.sleep(0.1)  # Simulate slow operation
                return 123
            
            mock_create.side_effect = slow_create
            
            # Act
            start_time = time.time()
            support_screen.create_ticket()
            end_time = time.time()
            
            # Assert
            # UI should remain responsive (operation should not block)
            self.assertLess(end_time - start_time, 0.2)  # Should complete quickly
    
    def test_ui_theme_integration(self):
        """Test UI theme integration with license status"""
        # Arrange
        from src.ui.main_screen import MainScreen
        main_screen = MainScreen(self.root, self.license_manager)
        
        # Test with active license
        self.license_manager.license_data = {
            'license_type': 'professional',
            'status': 'active'
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act
        main_screen.update_theme_based_on_license()
        
        # Assert
        # Should use professional theme colors
        self.assertEqual(main_screen.title_label.cget('foreground'), '#2E86AB')  # Professional blue
        
        # Test with expired license
        self.license_manager.license_data['status'] = 'expired'
        self.license_manager.validation_result = Mock(is_valid=False)
        
        # Act
        main_screen.update_theme_based_on_license()
        
        # Assert
        # Should use warning theme colors
        self.assertEqual(main_screen.title_label.cget('foreground'), '#E74C3C')  # Warning red
```

## Error Handling Integration Tests

### Test Class Structure

```python
# tests/integration/test_error_handling_integration.py
"""Error handling integration tests"""

import unittest
from unittest.mock import patch, Mock
import sqlite3
import requests
from src.utils.license_manager import LicenseManager
from src.utils.support_manager import SupportManager
from src.utils.license_validator import LicenseValidator

class TestErrorHandlingIntegration(unittest.TestCase):
    """Error handling integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.db = Mock()
        self.license_manager = LicenseManager(self.app)
        self.support_manager = SupportManager(self.app)
    
    def test_database_connection_error_handling(self):
        """Test database connection error handling"""
        # Arrange
        self.app.db.cursor.side_effect = sqlite3.Error("Database connection failed")
        
        # Act & Assert
        with self.assertRaises(sqlite3.Error):
            self.license_manager.validate_license()
        
        with self.assertRaises(sqlite3.Error):
            self.support_manager.create_ticket(1, 'Technical Support', 'Test', 'Test', 'Medium')
    
    def test_license_server_unavailable_handling(self):
        """Test license server unavailable handling"""
        # Arrange
        self.license_manager.license_data = {
            'license_key': 'TEST-LIC-001',
            'license_type': 'professional'
        }
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            
            # Act
            result = self.license_manager.validate_license(force_online=True)
            
            # Assert
            self.assertFalse(result.is_valid)
            self.assertIn('connection', result.error.lower())
    
    def test_email_service_failure_handling(self):
        """Test email service failure handling"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-TEST-001',
            'user_email': 'user@example.com',
            'subject': 'Test Ticket'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = Exception("SMTP server unavailable")
            
            # Act
            result = self.support_manager.email_service.send_ticket_acknowledgment(ticket_data)
            
            # Assert
            self.assertFalse(result)
    
    def test_license_validation_error_propagation(self):
        """Test license validation error propagation"""
        # Arrange
        self.license_manager.license_data = {
            'license_key': 'INVALID-LICENSE',
            'license_type': 'professional'
        }
        
        # Mock hardware fingerprint error
        with patch.object(self.license_manager.hardware_fingerprinter, 'generate_fingerprint') as mock_fingerprint:
            mock_fingerprint.side_effect = Exception("Hardware access denied")
            
            # Act
            result = self.license_manager.validate_license()
            
            # Assert
            self.assertFalse(result.is_valid)
            self.assertIn('hardware', result.error.lower())
    
    def test_support_ticket_creation_error_handling(self):
        """Test support ticket creation error handling"""
        # Arrange
        with patch.object(self.support_manager.ticket_manager, 'create') as mock_create:
            mock_create.side_effect = Exception("Database constraint violation")
            
            # Act & Assert
            with self.assertRaises(Exception):
                self.support_manager.create_ticket(1, 'Technical Support', 'Test', 'Test', 'Medium')
    
    def test_file_upload_error_handling(self):
        """Test file upload error handling"""
        # Arrange
        # Mock file that doesn't exist
        non_existent_file = '/path/to/non/existent/file.png'
        
        # Act & Assert
        with self.assertRaises(FileNotFoundError):
            self.support_manager.ticket_manager.add_attachment(1, non_existent_file, 'test.png')
    
    def test_encryption_decryption_error_handling(self):
        """Test encryption/decryption error handling"""
        # Arrange
        sensitive_data = 'Sensitive information'
        
        # Mock encryption error
        with patch.object(self.support_manager.encryption_manager, 'encrypt') as mock_encrypt:
            mock_encrypt.side_effect = Exception("Encryption key corrupted")
            
            # Act & Assert
            with self.assertRaises(Exception):
                self.support_manager.create_ticket(1, 'Technical Support', 'Test', sensitive_data, 'Medium')
    
    def test_license_expiry_error_handling(self):
        """Test license expiry error handling"""
        # Arrange
        expired_license = {
            'license_key': 'EXPIRED-LIC-001',
            'license_type': 'professional',
            'expiry_date': '2022-12-31T23:59:59Z'
        }
        
        self.license_manager.license_data = expired_license
        
        # Act
        result = self.license_manager.validate_license()
        
        # Assert
        self.assertFalse(result.is_valid)
        self.assertIn('expired', result.error.lower())
    
    def test_support_system_licensing_error_handling(self):
        """Test support system licensing error handling"""
        # Arrange
        # Mock license without support features
        self.license_manager.license_data = {
            'license_type': 'trial',
            'features': ['order_management']  # No support features
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act & Assert
        with self.assertRaises(Exception):
            self.support_manager.create_ticket(1, 'Technical Support', 'Test', 'Test', 'Medium')
    
    def test_concurrent_access_error_handling(self):
        """Test concurrent access error handling"""
        # Arrange
        import threading
        
        # Mock database locking error
        def simulate_lock_error(*args, **kwargs):
            if threading.current_thread().name == 'Thread-2':
                raise sqlite3.OperationalError("Database is locked")
            return 1
        
        with patch.object(self.support_manager.ticket_manager, 'create') as mock_create:
            mock_create.side_effect = simulate_lock_error
            
            # Act
            results = []
            
            def create_ticket_thread():
                try:
                    result = self.support_manager.create_ticket(
                        1, 'Technical Support', 'Test', 'Test', 'Medium'
                    )
                    results.append(('success', result))
                except Exception as e:
                    results.append(('error', str(e)))
            
            # Create two threads
            thread1 = threading.Thread(target=create_ticket_thread, name='Thread-1')
            thread2 = threading.Thread(target=create_ticket_thread, name='Thread-2')
            
            thread1.start()
            thread2.start()
            
            thread1.join()
            thread2.join()
            
            # Assert
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0][0], 'success')
            self.assertEqual(results[1][0], 'error')
            self.assertIn('locked', results[1][1].lower())
    
    def test_memory_exhaustion_error_handling(self):
        """Test memory exhaustion error handling"""
        # Arrange
        # Mock memory error
        with patch.object(self.support_manager.ticket_manager, 'search') as mock_search:
            mock_search.side_effect = MemoryError("Out of memory")
            
            # Act & Assert
            with self.assertRaises(MemoryError):
                self.support_manager.search_tickets({'category': 'Technical Support'})
    
    def test_network_timeout_error_handling(self):
        """Test network timeout error handling"""
        # Arrange
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
            
            # Act
            result = self.license_manager.validate_license(force_online=True)
            
            # Assert
            self.assertFalse(result.is_valid)
            self.assertIn('timeout', result.error.lower())
    
    def test_data_corruption_error_handling(self):
        """Test data corruption error handling"""
        # Arrange
        # Mock corrupted license data
        corrupted_license = {
            'license_key': 'CORRUPTED-LIC',
            'license_type': 'professional',
            'features': None  # Corrupted data
        }
        
        self.license_manager.license_data = corrupted_license
        
        # Act
        result = self.license_manager.validate_license()
        
        # Assert
        self.assertFalse(result.is_valid)
        self.assertIn('corrupted', result.error.lower())
    
    def test_graceful_degradation_handling(self):
        """Test graceful degradation when services are unavailable"""
        # Arrange
        # Mock both online license validation and email service failures
        with patch('requests.post') as mock_post, \
             patch('smtplib.SMTP') as mock_smtp:
            
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
            mock_smtp.side_effect = Exception("SMTP server unavailable")
            
            # Act
            # License validation should fall back to offline
            license_result = self.license_manager.validate_license(force_online=True)
            
            # Ticket creation should succeed even without email
            ticket_id = self.support_manager.create_ticket(
                1, 'Technical Support', 'Test', 'Test', 'Medium'
            )
            
            # Assert
            # License should still validate offline
            self.assertIsNotNone(license_result)
            
            # Ticket should be created despite email failure
            self.assertIsNotNone(ticket_id)
```

## Performance Integration Tests

### Test Class Structure

```python
# tests/integration/test_performance_integration.py
"""Performance integration tests"""

import unittest
import time
import statistics
import threading
import queue
from unittest.mock import patch, Mock
from src.utils.license_manager import LicenseManager
from src.utils.support_manager import SupportManager

class TestPerformanceIntegration(unittest.TestCase):
    """Performance integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = Mock()
        self.app.db = Mock()
        self.license_manager = LicenseManager(self.app)
        self.support_manager = SupportManager(self.app)
    
    def test_license_validation_performance_under_load(self):
        """Test license validation performance under load"""
        # Arrange
        self.license_manager.license_data = {
            'license_key': 'PERF-LIC-001',
            'license_type': 'professional',
            'features': ['order_management', 'reporting']
        }
        self.license_manager.validation_result = Mock(is_valid=True)
        
        # Act
        validation_times = []
        
        # Perform 100 concurrent validations
        def validate_license_thread():
            start_time = time.time()
            result = self.license_manager.validate_license()
            end_time = time.time()
            validation_times.append(end_time - start_time)
            return result
        
        threads = []
        for _ in range(100):
            thread = threading.Thread(target=validate_license_thread)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        average_time = statistics.mean(validation_times)
        max_time = max(validation_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.05, "Average validation time should be less than 50ms")
        self.assertLess(max_time, 0.1, "Maximum validation time should be less than 100ms")
    
    def test_support_ticket_creation_performance_under_load(self):
        """Test support ticket creation performance under load"""
        # Arrange
        with patch.object(self.support_manager.ticket_manager, 'create') as mock_create:
            mock_create.return_value = 1
            
            # Act
            creation_times = []
            
            # Perform 50 concurrent ticket creations
            def create_ticket_thread():
                start_time = time.time()
                result = self.support_manager.create_ticket(
                    1, 'Technical Support', 'Test Issue', 'Test Description', 'Medium'
                )
                end_time = time.time()
                creation_times.append(end_time - start_time)
                return result
            
            threads = []
            for i in range(50):
                thread = threading.Thread(target=create_ticket_thread)
                threads.append(thread)
                thread.start()
            
            for thread in threads:
                thread.join()
            
            # Assert
            average_time = statistics.mean(creation_times)
            max_time = max(creation_times)
            
            # Performance requirements
            self.assertLess(average_time, 0.1, "Average ticket creation time should be less than 100ms")
            self.assertLess(max_time, 0.2, "Maximum ticket creation time should be less than 200ms")
    
    def test_database_performance_with_large_dataset(self):
        """Test database performance with large dataset"""
        # Arrange
        # Create mock large dataset
        mock_tickets = []
        for i in range(10000):
            mock_tickets.append({
                'id': i,
                'ticket_number': f'SUP-LARGE-{i:06d}',
                'subject': f'Large Dataset Test {i}',
                'status': 'Open',
                'priority': 'Medium'
            })
        
        with patch.object(self.support_manager.ticket_manager, 'search') as mock_search:
            mock_search.return_value = mock_tickets
            
            # Act
            search_times = []
            
            # Perform multiple searches
            for _ in range(10):
                start_time = time.time()
                results = self.support_manager.search_tickets({'status': 'Open'})
                end_time = time.time()
                search_times.append(end_time - start_time)
                
                # Verify results
                self.assertEqual(len(results), 10000)
            
            # Assert
            average_time = statistics.mean(search_times)
            max_time = max(search_times)
            
            # Performance requirements for large dataset
            self.assertLess(average_time, 0.5, "Average search time should be less than 500ms")
            self.assertLess(max_time, 1.0, "Maximum search time should be less than 1 second")
    
    def test_memory_usage_under_sustained_load(self):
        """Test memory usage under sustained load"""
        # Arrange
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Act
        # Perform sustained operations for 10 seconds
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < 10:
            # License validation
            self.license_manager.validate_license()
            
            # Ticket search
            self.support_manager.search_tickets({'status': 'Open'})
            
            operation_count += 1
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert
        # Memory increase should be minimal
        self.assertLess(memory_increase, 50 * 1024 * 1024,  # Less than 50MB
                       f"Memory increase should be less than 50MB after {operation_count} operations")
        
        # Operations per second should be reasonable
        operations_per_second = operation_count / 10
        self.assertGreater(operations_per_second, 10, 
                         "Should perform at least 10 operations per second")
    
    def test_concurrent_user_simulation(self):
        """Test performance with concurrent user simulation"""
        # Arrange
        num_users = 20
        operations_per_user = 10
        
        results = queue.Queue()
        
        def user_simulation(user_id):
            user_times = []
            
            for operation in range(operations_per_user):
                # Mix of license validations and support operations
                if operation % 2 == 0:
                    # License validation
                    start_time = time.time()
                    self.license_manager.validate_license()
                    end_time = time.time()
                else:
                    # Support ticket search
                    start_time = time.time()
                    self.support_manager.search_tickets({'status': 'Open'})
                    end_time = time.time()
                
                user_times.append(end_time - start_time)
            
            results.put({
                'user_id': user_id,
                'average_time': statistics.mean(user_times),
                'max_time': max(user_times),
                'total_operations': operations_per_user
            })
        
        # Act
        threads = []
        for user_id in range(num_users):
            thread = threading.Thread(target=user_simulation, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Collect results
        user_results = []
        while not results.empty():
            user_results.append(results.get())
        
        # Assert
        # Check average performance across all users
        all_average_times = [result['average_time'] for result in user_results]
        overall_average = statistics.mean(all_average_times)
        
        self.assertLess(overall_average, 0.1, 
                       "Average operation time should be less than 100ms across all users")
        
        # Verify all users completed their operations
        total_operations = sum(result['total_operations'] for result in user_results)
        self.assertEqual(total_operations, num_users * operations_per_user)
    
    def test_external_service_performance_degradation(self):
        """Test performance when external services degrade"""
        # Arrange
        # Mock slow license server response
        with patch('requests.post') as mock_post:
            def slow_response(*args, **kwargs):
                time.sleep(0.1)  # 100ms delay
                response = Mock()
                response.status_code = 200
                response.json.return_value = {
                    'valid': True,
                    'license_data': {'license_key': 'SLOW-LIC-001'}
                }
                return response
            
            mock_post.side_effect = slow_response
            
            # Act
            # Test online validation with slow server
            start_time = time.time()
            result = self.license_manager.validate_license(force_online=True)
            end_time = time.time()
            
            # Test fallback to offline validation
            start_time_offline = time.time()
            result_offline = self.license_manager.validate_license(force_online=False)
            end_time_offline = time.time()
            
            # Assert
            online_time = end_time - start_time
            offline_time = end_time_offline - start_time_offline
            
            # Online validation should be slower due to external service
            self.assertGreater(online_time, offline_time)
            
            # Offline validation should still meet performance requirements
            self.assertLess(offline_time, 0.05, "Offline validation should be fast")
    
    def test_cache_performance_impact(self):
        """Test cache performance impact"""
        # Arrange
        search_criteria = {'category': 'Technical Support'}
        
        # Mock search without cache
        with patch.object(self.support_manager.ticket_manager, 'search') as mock_search:
            def slow_search(criteria):
                time.sleep(0.02)  # 20ms delay
                return [{'id': 1, 'subject': 'Test Ticket'}]
            
            mock_search.side_effect = slow_search
            
            # Act
            # First search (no cache)
            start_time = time.time()
            self.support_manager.search_tickets(search_criteria)
            first_search_time = time.time() - start_time
            
            # Second search (with cache)
            start_time = time.time()
            self.support_manager.search_tickets(search_criteria)
            second_search_time = time.time() - start_time
            
            # Assert
            # Cached search should be significantly faster
            self.assertLess(second_search_time, first_search_time * 0.5,
                           "Cached search should be at least 50% faster")
    
    def test_scalability_with_increasing_data(self):
        """Test scalability with increasing data volumes"""
        # Arrange
        data_sizes = [100, 1000, 5000, 10000]
        performance_results = []
        
        for data_size in data_sizes:
            # Mock dataset of current size
            mock_tickets = []
            for i in range(data_size):
                mock_tickets.append({
                    'id': i,
                    'ticket_number': f'SUP-SCALE-{i:06d}',
                    'subject': f'Scalability Test {i}',
                    'status': 'Open'
                })
            
            with patch.object(self.support_manager.ticket_manager, 'search') as mock_search:
                mock_search.return_value = mock_tickets
                
                # Act
                start_time = time.time()
                results = self.support_manager.search_tickets({'status': 'Open'})
                end_time = time.time()
                
                search_time = end_time - start_time
                
                performance_results.append({
                    'data_size': data_size,
                    'search_time': search_time,
                    'throughput': data_size / search_time
                })
                
                # Verify results
                self.assertEqual(len(results), data_size)
        
        # Assert
        # Performance should degrade gracefully
        for i in range(1, len(performance_results)):
            prev_result = performance_results[i-1]
            curr_result = performance_results[i]
            
            # Throughput should not decrease dramatically
            throughput_ratio = curr_result['throughput'] / prev_result['throughput']
            self.assertGreater(throughput_ratio, 0.5,
                             f"Throughput should not decrease by more than 50% when data size increases from {prev_result['data_size']} to {curr_result['data_size']}")
```

## Test Execution and Reporting

### Test Runner Script

```python
# scripts/run_integration_tests.py
"""Script to run integration tests"""

import subprocess
import sys
import os
import time
import json
from datetime import datetime

def run_test_suite(test_name, test_path):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"Running {test_name} Integration Tests")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Run tests
    result = subprocess.run([
        sys.executable, '-m', 'unittest', 
        test_path, '-v'
    ], capture_output=True, text=True)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Parse results
    output_lines = result.stdout.split('\n')
    test_count = 0
    failure_count = 0
    error_count = 0
    
    for line in output_lines:
        if 'Ran' in line and 'tests' in line:
            parts = line.split()
            test_count = int(parts[1])
        if 'FAIL:' in line:
            failure_count += 1
        if 'ERROR:' in line:
            error_count += 1
    
    success_count = test_count - failure_count - error_count
    
    # Print results
    print(f"Tests: {test_count}")
    print(f"Passed: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Errors: {error_count}")
    print(f"Duration: {duration:.2f} seconds")
    
    if result.returncode == 0:
        print(f"✅ {test_name} tests PASSED")
    else:
        print(f"❌ {test_name} tests FAILED")
        print("\nFailures:")
        print(result.stdout)
        print("\nErrors:")
        print(result.stderr)
    
    return {
        'test_name': test_name,
        'test_count': test_count,
        'success_count': success_count,
        'failure_count': failure_count,
        'error_count': error_count,
        'duration': duration,
        'success': result.returncode == 0
    }

def generate_test_report(results):
    """Generate comprehensive test report"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_suites': len(results),
            'total_tests': sum(r['test_count'] for r in results),
            'total_passed': sum(r['success_count'] for r in results),
            'total_failed': sum(r['failure_count'] for r in results),
            'total_errors': sum(r['error_count'] for r in results),
            'total_duration': sum(r['duration'] for r in results)
        },
        'suites': results
    }
    
    # Calculate success rate
    total_tests = report['summary']['total_tests']
    total_passed = report['summary']['total_passed']
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    report['summary']['success_rate'] = success_rate
    
    # Save report
    with open('integration_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Suites: {report['summary']['total_suites']}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Total Passed: {report['summary']['total_passed']}")
    print(f"Total Failed: {report['summary']['total_failed']}")
    print(f"Total Errors: {report['summary']['total_errors']}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Duration: {report['summary']['total_duration']:.2f} seconds")
    
    return report

def main():
    """Main test runner"""
    print("Starting Integration Test Suite")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Set up test environment
    print("\nSetting up test environment...")
    os.system('bash scripts/setup_test_environment.sh')
    
    # Define test suites
    test_suites = [
        ('License System Integration', 'tests.integration.test_license_integration'),
        ('Support System Integration', 'tests.integration.test_support_integration'),
        ('Cross-System Integration', 'tests.integration.test_cross_system_integration'),
        ('Database Integration', 'tests.integration.test_database_integration'),
        ('External Service Integration', 'tests.integration.test_external_service_integration'),
        ('UI Integration', 'tests.integration.test_ui_integration'),
        ('Error Handling Integration', 'tests.integration.test_error_handling_integration'),
        ('Performance Integration', 'tests.integration.test_performance_integration')
    ]
    
    # Run test suites
    results = []
    overall_success = True
    
    for test_name, test_path in test_suites:
        result = run_test_suite(test_name, test_path)
        results.append(result)
        
        if not result['success']:
            overall_success = False
    
    # Generate report
    report = generate_test_report(results)
    
    # Save detailed report
    with open('integration_test_report.html', 'w') as f:
        f.write(generate_html_report(report))
    
    print(f"\nDetailed report saved to: integration_test_report.json")
    print(f"HTML report saved to: integration_test_report.html")
    
    # Return appropriate exit code
    sys.exit(0 if overall_success else 1)

def generate_html_report(report):
    """Generate HTML test report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Integration Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
            .summary {{ margin: 20px 0; }}
            .suite {{ margin: 20px 0; border: 1px solid #ddd; border-radius: 5px; }}
            .suite-header {{ background-color: #f9f9f9; padding: 15px; font-weight: bold; }}
            .suite-details {{ padding: 15px; }}
            .pass {{ color: green; }}
            .fail {{ color: red; }}
            .error {{ color: orange; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Integration Test Report</h1>
            <p>Generated: {report['timestamp']}</p>
        </div>
        
        <div class="summary">
            <h2>Summary</h2>
            <table>
                <tr><th>Total Suites</th><td>{report['summary']['total_suites']}</td></tr>
                <tr><th>Total Tests</th><td>{report['summary']['total_tests']}</td></tr>
                <tr><th>Total Passed</th><td class="pass">{report['summary']['total_passed']}</td></tr>
                <tr><th>Total Failed</th><td class="fail">{report['summary']['total_failed']}</td></tr>
                <tr><th>Total Errors</th><td class="error">{report['summary']['total_errors']}</td></tr>
                <tr><th>Success Rate</th><td>{report['summary']['success_rate']:.1f}%</td></tr>
                <tr><th>Total Duration</th><td>{report['summary']['total_duration']:.2f} seconds</td></tr>
            </table>
        </div>
        
        <div class="suites">
            <h2>Test Suites</h2>
    """
    
    for suite in report['suites']:
        status_class = 'pass' if suite['success'] else 'fail'
        html += f"""
            <div class="suite">
                <div class="suite-header">
                    {suite['test_name']} - <span class="{status_class}">{'PASSED' if suite['success'] else 'FAILED'}</span>
                </div>
                <div class="suite-details">
                    <table>
                        <tr><th>Tests</th><td>{suite['test_count']}</td></tr>
                        <tr><th>Passed</th><td class="pass">{suite['success_count']}</td></tr>
                        <tr><th>Failed</th><td class="fail">{suite['failure_count']}</td></tr>
                        <tr><th>Errors</th><td class="error">{suite['error_count']}</td></tr>
                        <tr><th>Duration</th><td>{suite['duration']:.2f} seconds</td></tr>
                    </table>
                </div>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    main()
```

---

This comprehensive integration testing framework ensures that all components of the support and license systems work together correctly, both internally and with external dependencies. The framework includes tests for database integration, external service communication, UI interactions, error handling, and performance under realistic conditions.