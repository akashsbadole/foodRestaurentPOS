# Unit Testing Framework for Support System

## Overview

This document outlines a comprehensive unit testing framework for the support system in the Restaurant POS MVP application. The framework ensures all components of the support system are thoroughly tested, including ticket management, contact form processing, bug reporting, and email notifications.

## Table of Contents

1. [Testing Strategy](#testing-strategy)
2. [Test Structure](#test-structure)
3. [Support Manager Tests](#support-manager-tests)
4. [Ticket Manager Tests](#ticket-manager-tests)
5. [Contact Manager Tests](#contact-manager-tests)
6. [Bug Manager Tests](#bug-manager-tests)
7. [Email Service Tests](#email-service-tests)
8. [Security Tests](#security-tests)
9. [Performance Tests](#performance-tests)
10. [Test Coverage Requirements](#test-coverage-requirements)
11. [Test Execution](#test-execution)

## Testing Strategy

### Testing Principles

1. **Isolation**: Each unit test should be independent and not rely on external systems
2. **Comprehensiveness**: Test all code paths, including edge cases and error conditions
3. **Repeatability**: Tests should produce the same results on every execution
4. **Clarity**: Test names and assertions should clearly indicate what is being tested
5. **Maintainability**: Tests should be easy to understand and modify

### Test Categories

1. **Functional Tests**: Verify correct functionality of support system components
2. **Security Tests**: Validate data encryption and access control
3. **Performance Tests**: Ensure acceptable performance under various conditions
4. **Error Handling Tests**: Verify proper handling of error conditions
5. **Integration Tests**: Test interaction between components

## Test Structure

### Directory Structure

```
tests/
├── unit/
│   ├── support_system/
│   │   ├── __init__.py
│   │   ├── test_support_manager.py
│   │   ├── test_ticket_manager.py
│   │   ├── test_contact_manager.py
│   │   ├── test_bug_manager.py
│   │   ├── test_email_service.py
│   │   ├── test_support_integration.py
│   │   └── fixtures/
│   │       ├── __init__.py
│   │       ├── ticket_data.py
│   │       ├── contact_data.py
│   │       └── bug_data.py
├── integration/
├── security/
├── performance/
└── conftest.py
```

### Test Fixtures

```python
# tests/unit/support_system/fixtures/ticket_data.py
"""Test fixtures for ticket data"""

import datetime
from typing import Dict, Any

def get_valid_ticket_data() -> Dict[str, Any]:
    """Get valid ticket data for testing"""
    return {
        'ticket_number': 'SUP-2023-001',
        'user_id': 123,
        'category': 'Technical Support',
        'priority': 'Medium',
        'subject': 'Login Issue',
        'description': 'Unable to login with valid credentials',
        'status': 'Open',
        'created_at': datetime.datetime.now()
    }

def get_high_priority_ticket_data() -> Dict[str, Any]:
    """Get high priority ticket data for testing"""
    ticket_data = get_valid_ticket_data()
    ticket_data['priority'] = 'High'
    ticket_data['subject'] = 'System Crash - Urgent'
    ticket_data['description'] = 'Application crashes when opening order screen'
    return ticket_data

def get_bug_report_ticket_data() -> Dict[str, Any]:
    """Get bug report ticket data for testing"""
    return {
        'ticket_number': 'BUG-2023-001',
        'user_id': 456,
        'category': 'Bug Report',
        'priority': 'High',
        'subject': 'Calculation Error in Order Total',
        'description': 'Order total calculated incorrectly when applying discounts',
        'status': 'Open',
        'created_at': datetime.datetime.now()
    }

def get_feature_request_ticket_data() -> Dict[str, Any]:
    """Get feature request ticket data for testing"""
    return {
        'ticket_number': 'FEAT-2023-001',
        'user_id': 789,
        'category': 'Feature Request',
        'priority': 'Low',
        'subject': 'Add Customer Loyalty Program',
        'description': 'Implement customer loyalty points system',
        'status': 'Open',
        'created_at': datetime.datetime.now()
    }
```

```python
# tests/unit/support_system/fixtures/contact_data.py
"""Test fixtures for contact form data"""

import datetime
from typing import Dict, Any

def get_valid_contact_data() -> Dict[str, Any]:
    """Get valid contact form data for testing"""
    return {
        'name': 'John Doe',
        'email': 'john.doe@restaurant.com',
        'phone': '+1234567890',
        'contact_method': 'email',
        'subject': 'General Inquiry',
        'message': 'I would like to know more about your POS system features',
        'status': 'New',
        'created_at': datetime.datetime.now()
    }

def get_phone_contact_data() -> Dict[str, Any]:
    """Get phone contact form data for testing"""
    contact_data = get_valid_contact_data()
    contact_data['contact_method'] = 'phone'
    contact_data['subject'] 'Urgent Support Required'
    return contact_data

def get_incomplete_contact_data() -> Dict[str, Any]:
    """Get incomplete contact form data for testing"""
    return {
        'name': 'Jane Smith',
        'email': '',  # Missing email
        'phone': '+0987654321',
        'contact_method': 'email',
        'subject': 'Question about pricing',
        'message': 'What are the pricing plans available?'
    }
```

```python
# tests/unit/support_system/fixtures/bug_data.py
"""Test fixtures for bug report data"""

import datetime
from typing import Dict, Any

def get_valid_bug_report_data() -> Dict[str, Any]:
    """Get valid bug report data for testing"""
    return {
        'bug_id': 'BUG-2023-001',
        'user_id': 123,
        'error_type': 'RuntimeError',
        'error_message': 'Division by zero error in order calculation',
        'stack_trace': '''Traceback (most recent call last):
  File "order.py", line 45, in calculate_total
    total = amount / quantity
ZeroDivisionError: division by zero''',
        'reproduction_steps': '1. Create order with zero quantity\n2. Try to calculate total',
        'session_info': {
            'user_id': 123,
            'session_id': 'sess_abc123',
            'login_time': '2023-01-01T10:00:00Z'
        },
        'system_info': {
            'os': 'Windows 10',
            'app_version': '2.1.0',
            'memory_usage': '256MB'
        },
        'app_version': '2.1.0',
        'priority': 'High',
        'status': 'New',
        'created_at': datetime.datetime.now()
    }

def get_critical_bug_report_data() -> Dict[str, Any]:
    """Get critical bug report data for testing"""
    bug_data = get_valid_bug_report_data()
    bug_data['error_type'] = 'SystemCrash'
    bug_data['error_message'] = 'Application crashes on startup'
    bug_data['priority'] = 'Critical'
    return bug_data
```

## Support Manager Tests

### Test Class Structure

```python
# tests/unit/support_system/test_support_manager.py
"""Unit tests for Support Manager"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
from src.utils.support_manager import SupportManager
from tests.unit.support_system.fixtures.ticket_data import (
    get_valid_ticket_data,
    get_high_priority_ticket_data
)
from tests.unit.support_system.fixtures.contact_data import get_valid_contact_data
from tests.unit.support_system.fixtures.bug_data import get_valid_bug_report_data

class TestSupportManager(unittest.TestCase):
    """Test cases for Support Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app_mock = Mock()
        self.app_mock.db = Mock()
        self.support_manager = SupportManager(self.app_mock)
        
        # Mock dependencies
        self.support_manager.ticket_manager = Mock()
        self.support_manager.contact_manager = Mock()
        self.support_manager.bug_manager = Mock()
        self.support_manager.email_service = Mock()
        self.support_manager.encryption_manager = Mock()
    
    def test_create_ticket_success(self):
        """Test successful ticket creation"""
        # Arrange
        user_id = 123
        category = 'Technical Support'
        subject = 'Login Issue'
        description = 'Unable to login with valid credentials'
        priority = 'Medium'
        
        expected_ticket_data = get_valid_ticket_data()
        
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        # Act
        ticket_id = self.support_manager.create_ticket(
            user_id, category, subject, description, priority
        )
        
        # Assert
        self.assertEqual(ticket_id, 1)
        self.support_manager.ticket_manager.create.assert_called_once()
        self.support_manager.email_service.send_ticket_acknowledgment.assert_called_once()
    
    def test_create_ticket_with_attachments(self):
        """Test ticket creation with attachments"""
        # Arrange
        user_id = 123
        category = 'Bug Report'
        subject = 'UI Issue'
        description = 'Button not working'
        priority = 'High'
        attachments = ['screenshot.png', 'log_file.txt']
        
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        with patch.object(self.support_manager, 'process_attachments') as mock_process:
            # Act
            ticket_id = self.support_manager.create_ticket(
                user_id, category, subject, description, priority, attachments
            )
            
            # Assert
            self.assertEqual(ticket_id, 1)
            mock_process.assert_called_once_with(1, attachments)
    
    def test_create_ticket_high_priority_escalation(self):
        """Test high priority ticket escalation"""
        # Arrange
        high_priority_ticket = get_high_priority_ticket_data()
        
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        with patch.object(self.support_manager, 'escalate_ticket') as mock_escalate:
            # Act
            ticket_id = self.support_manager.create_ticket(
                high_priority_ticket['user_id'],
                high_priority_ticket['category'],
                high_priority_ticket['subject'],
                high_priority_ticket['description'],
                high_priority_ticket['priority']
            )
            
            # Assert
            self.assertEqual(ticket_id, 1)
            mock_escalate.assert_called_once_with(1)
    
    def test_update_ticket_success(self):
        """Test successful ticket update"""
        # Arrange
        ticket_id = 1
        status = 'In Progress'
        assigned_to = 456
        
        mock_ticket = Mock()
        mock_ticket.status = 'Open'
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        
        # Act
        result = self.support_manager.update_ticket(
            ticket_id, status=status, assigned_to=assigned_to
        )
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_ticket.status, status)
        self.assertEqual(mock_ticket.assigned_to, assigned_to)
        self.support_manager.ticket_manager.update.assert_called_once()
        self.support_manager.email_service.send_ticket_update.assert_called_once()
    
    def test_update_ticket_not_found(self):
        """Test ticket update with non-existent ticket"""
        # Arrange
        ticket_id = 999
        self.support_manager.ticket_manager.get_by_id.return_value = None
        
        # Act
        result = self.support_manager.update_ticket(ticket_id, status='Closed')
        
        # Assert
        self.assertFalse(result)
        self.support_manager.ticket_manager.update.assert_not_called()
    
    def test_process_contact_form_success(self):
        """Test successful contact form processing"""
        # Arrange
        contact_data = get_valid_contact_data()
        
        self.support_manager.contact_manager.submit_contact_form.return_value = 1
        
        # Act
        result = self.support_manager.process_contact_form(contact_data)
        
        # Assert
        self.assertEqual(result, 1)
        self.support_manager.contact_manager.submit_contact_form.assert_called_once_with(contact_data)
    
    def test_submit_bug_report_success(self):
        """Test successful bug report submission"""
        # Arrange
        bug_data = get_valid_bug_report_data()
        
        self.support_manager.bug_manager.submit_bug_report.return_value = 1
        
        # Act
        result = self.support_manager.submit_bug_report(bug_data)
        
        # Assert
        self.assertEqual(result, 1)
        self.support_manager.bug_manager.submit_bug_report.assert_called_once_with(bug_data)
    
    def test_escalate_ticket_success(self):
        """Test successful ticket escalation"""
        # Arrange
        ticket_id = 1
        mock_ticket = Mock()
        mock_ticket.priority = 'High'
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        
        # Act
        result = self.support_manager.escalate_ticket(ticket_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_ticket.priority, 'Critical')
        self.support_manager.ticket_manager.update.assert_called_once()
        self.support_manager.email_service.send_escalation_notification.assert_called_once()
    
    def test_get_ticket_statistics(self):
        """Test ticket statistics retrieval"""
        # Arrange
        expected_stats = {
            'total_tickets': 100,
            'open_tickets': 25,
            'closed_tickets': 75,
            'average_resolution_time': 48.5,
            'tickets_by_category': {
                'Technical Support': 40,
                'Bug Report': 30,
                'Feature Request': 20,
                'General Inquiry': 10
            },
            'tickets_by_priority': {
                'Low': 20,
                'Medium': 50,
                'High': 25,
                'Critical': 5
            }
        }
        
        self.support_manager.ticket_manager.get_statistics.return_value = expected_stats
        
        # Act
        stats = self.support_manager.get_ticket_statistics()
        
        # Assert
        self.assertEqual(stats, expected_stats)
        self.support_manager.ticket_manager.get_statistics.assert_called_once()
    
    def test_assign_ticket_success(self):
        """Test successful ticket assignment"""
        # Arrange
        ticket_id = 1
        assigned_to = 456
        
        mock_ticket = Mock()
        mock_ticket.assigned_to = None
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        
        # Act
        result = self.support_manager.assign_ticket(ticket_id, assigned_to)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_ticket.assigned_to, assigned_to)
        self.support_manager.ticket_manager.update.assert_called_once()
        self.support_manager.email_service.send_assignment_notification.assert_called_once()
    
    def test_close_ticket_success(self):
        """Test successful ticket closure"""
        # Arrange
        ticket_id = 1
        resolution_note = 'Issue resolved by updating user credentials'
        
        mock_ticket = Mock()
        mock_ticket.status = 'In Progress'
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        
        with patch.object(self.support_manager, 'update_ticket') as mock_update:
            # Act
            result = self.support_manager.close_ticket(ticket_id, resolution_note)
            
            # Assert
            self.assertTrue(result)
            mock_update.assert_called_once_with(
                ticket_id, 
                status='Closed', 
                resolution_note=resolution_note
            )
            self.support_manager.email_service.send_closure_notification.assert_called_once()
    
    def test_reopen_ticket_success(self):
        """Test successful ticket reopening"""
        # Arrange
        ticket_id = 1
        reopen_reason = 'Issue persists after attempted fix'
        
        mock_ticket = Mock()
        mock_ticket.status = 'Closed'
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        
        with patch.object(self.support_manager, 'update_ticket') as mock_update:
            # Act
            result = self.support_manager.reopen_ticket(ticket_id, reopen_reason)
            
            # Assert
            self.assertTrue(result)
            mock_update.assert_called_once_with(
                ticket_id, 
                status='Open', 
                reopen_reason=reopen_reason
            )
            self.support_manager.email_service.send_reopen_notification.assert_called_once()
    
    def test_search_tickets_success(self):
        """Test successful ticket search"""
        # Arrange
        search_criteria = {
            'category': 'Technical Support',
            'status': 'Open',
            'priority': 'High'
        }
        
        expected_results = [
            {'id': 1, 'subject': 'Login Issue', 'priority': 'High'},
            {'id': 2, 'subject': 'System Crash', 'priority': 'High'}
        ]
        
        self.support_manager.ticket_manager.search.return_value = expected_results
        
        # Act
        results = self.support_manager.search_tickets(search_criteria)
        
        # Assert
        self.assertEqual(results, expected_results)
        self.support_manager.ticket_manager.search.assert_called_once_with(search_criteria)
    
    def test_generate_ticket_report_success(self):
        """Test successful ticket report generation"""
        # Arrange
        report_type = 'monthly'
        date_range = {
            'start_date': datetime.datetime(2023, 1, 1),
            'end_date': datetime.datetime(2023, 1, 31)
        }
        
        expected_report = {
            'report_type': 'monthly',
            'period': 'January 2023',
            'total_tickets': 150,
            'resolution_rate': 85.5,
            'average_resolution_time': 24.5,
            'top_issues': [
                {'issue': 'Login Problems', 'count': 25},
                {'issue': 'Payment Issues', 'count': 20},
                {'issue': 'UI Problems', 'count': 15}
            ]
        }
        
        self.support_manager.ticket_manager.generate_report.return_value = expected_report
        
        # Act
        report = self.support_manager.generate_ticket_report(report_type, date_range)
        
        # Assert
        self.assertEqual(report, expected_report)
        self.support_manager.ticket_manager.generate_report.assert_called_once_with(report_type, date_range)
```

## Ticket Manager Tests

### Test Class Structure

```python
# tests/unit/support_system/test_ticket_manager.py
"""Unit tests for Ticket Manager"""

import unittest
from unittest.mock import Mock, patch
import datetime
from src.managers.ticket_manager import TicketManager
from tests.unit.support_system.fixtures.ticket_data import (
    get_valid_ticket_data,
    get_high_priority_ticket_data,
    get_bug_report_ticket_data
)

class TestTicketManager(unittest.TestCase):
    """Test cases for Ticket Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_mock = Mock()
        self.ticket_manager = TicketManager(self.db_mock)
        self.ticket_manager.encryption_manager = Mock()
    
    def test_create_ticket_success(self):
        """Test successful ticket creation"""
        # Arrange
        ticket_data = get_valid_ticket_data()
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        # Act
        ticket_id = self.ticket_manager.create(ticket_data)
        
        # Assert
        self.assertEqual(ticket_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.ticket_manager.encryption_manager.encrypt.assert_called_once_with(ticket_data['description'])
    
    def test_create_ticket_invalid_data(self):
        """Test ticket creation with invalid data"""
        # Arrange
        invalid_ticket_data = {
            'user_id': 123,
            # Missing required fields
        }
        
        with patch.object(self.ticket_manager, 'validate_ticket_data') as mock_validate:
            mock_validate.side_effect = ValueError("Invalid ticket data")
            
            # Act & Assert
            with self.assertRaises(ValueError):
                self.ticket_manager.create(invalid_ticket_data)
            
            self.db_mock.rollback.assert_called_once()
    
    def test_get_ticket_by_id_success(self):
        """Test successful ticket retrieval by ID"""
        # Arrange
        ticket_id = 1
        expected_ticket = get_valid_ticket_data()
        expected_ticket['id'] = ticket_id
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = expected_ticket
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_description'
        
        # Act
        ticket = self.ticket_manager.get_by_id(ticket_id)
        
        # Assert
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket['id'], ticket_id)
        self.db_mock.execute_query.assert_called_once()
        self.ticket_manager.encryption_manager.decrypt.assert_called_once()
    
    def test_get_ticket_by_id_not_found(self):
        """Test ticket retrieval with non-existent ID"""
        # Arrange
        ticket_id = 999
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        ticket = self.ticket_manager.get_by_id(ticket_id)
        
        # Assert
        self.assertIsNone(ticket)
        self.db_mock.execute_query.assert_called_once()
    
    def test_update_ticket_success(self):
        """Test successful ticket update"""
        # Arrange
        ticket_id = 1
        update_data = {
            'status': 'In Progress',
            'assigned_to': 456
        }
        
        self.ticket_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        result = self.ticket_manager.update(ticket_id, update_data)
        
        # Assert
        self.assertTrue(result)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_update_ticket_not_found(self):
        """Test ticket update with non-existent ticket"""
        # Arrange
        ticket_id = 999
        update_data = {'status': 'Closed'}
        
        self.db_mock.execute_query.side_effect = Exception("Ticket not found")
        
        # Act
        result = self.ticket_manager.update(ticket_id, update_data)
        
        # Assert
        self.assertFalse(result)
        self.db_mock.rollback.assert_called_once()
    
    def test_delete_ticket_success(self):
        """Test successful ticket deletion"""
        # Arrange
        ticket_id = 1
        
        # Act
        result = self.ticket_manager.delete(ticket_id)
        
        # Assert
        self.assertTrue(result)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_get_tickets_by_user_success(self):
        """Test successful retrieval of tickets by user"""
        # Arrange
        user_id = 123
        expected_tickets = [
            get_valid_ticket_data(),
            get_high_priority_ticket_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_tickets
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_description'
        
        # Act
        tickets = self.ticket_manager.get_by_user(user_id)
        
        # Assert
        self.assertEqual(len(tickets), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_tickets_by_category_success(self):
        """Test successful retrieval of tickets by category"""
        # Arrange
        category = 'Technical Support'
        expected_tickets = [
            get_valid_ticket_data(),
            get_high_priority_ticket_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_tickets
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_description'
        
        # Act
        tickets = self.ticket_manager.get_by_category(category)
        
        # Assert
        self.assertEqual(len(tickets), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_tickets_by_status_success(self):
        """Test successful retrieval of tickets by status"""
        # Arrange
        status = 'Open'
        expected_tickets = [
            get_valid_ticket_data(),
            get_bug_report_ticket_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_tickets
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_description'
        
        # Act
        tickets = self.ticket_manager.get_by_status(status)
        
        # Assert
        self.assertEqual(len(tickets), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_search_tickets_success(self):
        """Test successful ticket search"""
        # Arrange
        search_criteria = {
            'subject': 'Login',
            'category': 'Technical Support',
            'priority': 'High'
        }
        
        expected_results = [
            get_high_priority_ticket_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_results
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_description'
        
        # Act
        results = self.ticket_manager.search(search_criteria)
        
        # Assert
        self.assertEqual(len(results), 1)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_ticket_statistics_success(self):
        """Test successful ticket statistics retrieval"""
        # Arrange
        expected_stats = {
            'total_tickets': 100,
            'open_tickets': 25,
            'closed_tickets': 75,
            'average_resolution_time': 48.5,
            'tickets_by_category': {
                'Technical Support': 40,
                'Bug Report': 30,
                'Feature Request': 20,
                'General Inquiry': 10
            }
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (100, 25, 75, 48.5)
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        stats = self.ticket_manager.get_statistics()
        
        # Assert
        self.assertEqual(stats['total_tickets'], 100)
        self.assertEqual(stats['open_tickets'], 25)
        self.assertEqual(stats['closed_tickets'], 75)
        self.assertEqual(stats['average_resolution_time'], 48.5)
    
    def test_validate_ticket_data_success(self):
        """Test successful ticket data validation"""
        # Arrange
        ticket_data = get_valid_ticket_data()
        
        # Act
        result = self.ticket_manager.validate_ticket_data(ticket_data)
        
        # Assert
        self.assertTrue(result)
    
    def test_validate_ticket_data_missing_required_field(self):
        """Test ticket data validation with missing required field"""
        # Arrange
        invalid_ticket_data = {
            'user_id': 123,
            'category': 'Technical Support',
            # Missing subject
            'description': 'Test description'
        }
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.ticket_manager.validate_ticket_data(invalid_ticket_data)
    
    def test_validate_ticket_data_invalid_priority(self):
        """Test ticket data validation with invalid priority"""
        # Arrange
        invalid_ticket_data = get_valid_ticket_data()
        invalid_ticket_data['priority'] = 'Invalid Priority'
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.ticket_manager.validate_ticket_data(invalid_ticket_data)
    
    def test_add_ticket_conversation_success(self):
        """Test successful addition of ticket conversation"""
        # Arrange
        ticket_id = 1
        user_id = 123
        message = 'This is an update on the ticket'
        is_internal = False
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.encrypt.return_value = 'encrypted_message'
        
        # Act
        conversation_id = self.ticket_manager.add_conversation(ticket_id, user_id, message, is_internal)
        
        # Assert
        self.assertEqual(conversation_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.ticket_manager.encryption_manager.encrypt.assert_called_once_with(message)
    
    def test_get_ticket_conversations_success(self):
        """Test successful retrieval of ticket conversations"""
        # Arrange
        ticket_id = 1
        expected_conversations = [
            {
                'id': 1,
                'ticket_id': ticket_id,
                'user_id': 123,
                'message': 'encrypted_message_1',
                'is_internal': False,
                'created_at': datetime.datetime.now()
            },
            {
                'id': 2,
                'ticket_id': ticket_id,
                'user_id': 456,
                'message': 'encrypted_message_2',
                'is_internal': True,
                'created_at': datetime.datetime.now()
            }
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_conversations
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.ticket_manager.encryption_manager.decrypt.return_value = 'decrypted_message'
        
        # Act
        conversations = self.ticket_manager.get_conversations(ticket_id)
        
        # Assert
        self.assertEqual(len(conversations), 2)
        self.db_mock.execute_query.assert_called_once()
        self.ticket_manager.encryption_manager.decrypt.assert_called()
```

## Contact Manager Tests

### Test Class Structure

```python
# tests/unit/support_system/test_contact_manager.py
"""Unit tests for Contact Manager"""

import unittest
from unittest.mock import Mock, patch
import datetime
from src.managers.contact_manager import ContactManager
from tests.unit.support_system.fixtures.contact_data import (
    get_valid_contact_data,
    get_phone_contact_data,
    get_incomplete_contact_data
)

class TestContactManager(unittest.TestCase):
    """Test cases for Contact Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_mock = Mock()
        self.contact_manager = ContactManager(self.db_mock)
        self.contact_manager.encryption_manager = Mock()
        self.contact_manager.email_service = Mock()
    
    def test_submit_contact_form_success(self):
        """Test successful contact form submission"""
        # Arrange
        contact_data = get_valid_contact_data()
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        contact_id = self.contact_manager.submit_contact_form(contact_data)
        
        # Assert
        self.assertEqual(contact_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.contact_manager.email_service.send_contact_acknowledgment.assert_called_once()
    
    def test_submit_contact_form_phone_method(self):
        """Test contact form submission with phone contact method"""
        # Arrange
        contact_data = get_phone_contact_data()
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        contact_id = self.contact_manager.submit_contact_form(contact_data)
        
        # Assert
        self.assertEqual(contact_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.contact_manager.email_service.send_contact_acknowledgment.assert_called_once()
    
    def test_submit_contact_form_incomplete_data(self):
        """Test contact form submission with incomplete data"""
        # Arrange
        incomplete_contact_data = get_incomplete_contact_data()
        
        with patch.object(self.contact_manager, 'validate_contact_data') as mock_validate:
            mock_validate.side_effect = ValueError("Missing required fields")
            
            # Act & Assert
            with self.assertRaises(ValueError):
                self.contact_manager.submit_contact_form(incomplete_contact_data)
            
            self.db_mock.rollback.assert_called_once()
    
    def test_get_contact_by_id_success(self):
        """Test successful contact retrieval by ID"""
        # Arrange
        contact_id = 1
        expected_contact = get_valid_contact_data()
        expected_contact['id'] = contact_id
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = expected_contact
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        contact = self.contact_manager.get_by_id(contact_id)
        
        # Assert
        self.assertIsNotNone(contact)
        self.assertEqual(contact['id'], contact_id)
        self.db_mock.execute_query.assert_called_once()
        self.contact_manager.encryption_manager.decrypt.assert_called()
    
    def test_get_contact_by_id_not_found(self):
        """Test contact retrieval with non-existent ID"""
        # Arrange
        contact_id = 999
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        contact = self.contact_manager.get_by_id(contact_id)
        
        # Assert
        self.assertIsNone(contact)
        self.db_mock.execute_query.assert_called_once()
    
    def test_update_contact_success(self):
        """Test successful contact update"""
        # Arrange
        contact_id = 1
        update_data = {
            'status': 'Responded',
            'assigned_to': 456
        }
        
        self.contact_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        result = self.contact_manager.update(contact_id, update_data)
        
        # Assert
        self.assertTrue(result)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_get_contacts_by_status_success(self):
        """Test successful retrieval of contacts by status"""
        # Arrange
        status = 'New'
        expected_contacts = [
            get_valid_contact_data(),
            get_phone_contact_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_contacts
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        contacts = self.contact_manager.get_by_status(status)
        
        # Assert
        self.assertEqual(len(contacts), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_contacts_by_contact_method_success(self):
        """Test successful retrieval of contacts by contact method"""
        # Arrange
        contact_method = 'email'
        expected_contacts = [
            get_valid_contact_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_contacts
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        contacts = self.contact_manager.get_by_contact_method(contact_method)
        
        # Assert
        self.assertEqual(len(contacts), 1)
        self.db_mock.execute_query.assert_called_once()
    
    def test_search_contacts_success(self):
        """Test successful contact search"""
        # Arrange
        search_criteria = {
            'name': 'John',
            'email': 'john.doe@restaurant.com',
            'status': 'New'
        }
        
        expected_results = [
            get_valid_contact_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_results
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.contact_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        results = self.contact_manager.search(search_criteria)
        
        # Assert
        self.assertEqual(len(results), 1)
        self.db_mock.execute_query.assert_called_once()
    
    def test_apply_template_response_success(self):
        """Test successful application of template response"""
        # Arrange
        contact_id = 1
        template_name = 'general_inquiry'
        contact_data = get_valid_contact_data()
        
        with patch.object(self.contact_manager, 'get_template_by_name') as mock_get_template:
            mock_get_template.return_value = {
                'subject': 'Re: Your Inquiry',
                'message': 'Thank you for your inquiry. We will respond within 24 hours.'
            }
            
            # Act
            result = self.contact_manager.apply_template_response(contact_id, template_name, contact_data)
            
            # Assert
            self.assertTrue(result)
            mock_get_template.assert_called_once_with(template_name)
    
    def test_validate_contact_data_success(self):
        """Test successful contact data validation"""
        # Arrange
        contact_data = get_valid_contact_data()
        
        # Act
        result = self.contact_manager.validate_contact_data(contact_data)
        
        # Assert
        self.assertTrue(result)
    
    def test_validate_contact_data_missing_email(self):
        """Test contact data validation with missing email"""
        # Arrange
        invalid_contact_data = get_valid_contact_data()
        invalid_contact_data['email'] = ''
        invalid_contact_data['contact_method'] = 'email'
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.contact_manager.validate_contact_data(invalid_contact_data)
    
    def test_validate_contact_data_invalid_contact_method(self):
        """Test contact data validation with invalid contact method"""
        # Arrange
        invalid_contact_data = get_valid_contact_data()
        invalid_contact_data['contact_method'] = 'invalid_method'
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.contact_manager.validate_contact_data(invalid_contact_data)
    
    def test_generate_contact_id_success(self):
        """Test successful contact ID generation"""
        # Act
        contact_id = self.contact_manager.generate_contact_id()
        
        # Assert
        self.assertIsNotNone(contact_id)
        self.assertIsInstance(contact_id, str)
        self.assertTrue(contact_id.startswith('CON-'))
    
    def test_get_contact_statistics_success(self):
        """Test successful contact statistics retrieval"""
        # Arrange
        expected_stats = {
            'total_contacts': 50,
            'new_contacts': 15,
            'responded_contacts': 30,
            'closed_contacts': 5,
            'contacts_by_method': {
                'email': 35,
                'phone': 10,
                'in_app': 5
            }
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (50, 15, 30, 5)
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        stats = self.contact_manager.get_statistics()
        
        # Assert
        self.assertEqual(stats['total_contacts'], 50)
        self.assertEqual(stats['new_contacts'], 15)
        self.assertEqual(stats['responded_contacts'], 30)
        self.assertEqual(stats['closed_contacts'], 5)
```

## Bug Manager Tests

### Test Class Structure

```python
# tests/unit/support_system/test_bug_manager.py
"""Unit tests for Bug Manager"""

import unittest
from unittest.mock import Mock, patch
import datetime
from src.managers.bug_manager import BugManager
from tests.unit.support_system.fixtures.bug_data import (
    get_valid_bug_report_data,
    get_critical_bug_report_data
)

class TestBugManager(unittest.TestCase):
    """Test cases for Bug Manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_mock = Mock()
        self.bug_manager = BugManager(self.db_mock)
        self.bug_manager.encryption_manager = Mock()
    
    def test_submit_bug_report_success(self):
        """Test successful bug report submission"""
        # Arrange
        bug_data = get_valid_bug_report_data()
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        bug_id = self.bug_manager.submit_bug_report(bug_data)
        
        # Assert
        self.assertEqual(bug_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
        self.bug_manager.encryption_manager.encrypt.assert_called()
    
    def test_submit_bug_report_critical_priority(self):
        """Test bug report submission with critical priority"""
        # Arrange
        critical_bug_data = get_critical_bug_report_data()
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        with patch.object(self.bug_manager, 'escalate_bug_report') as mock_escalate:
            # Act
            bug_id = self.bug_manager.submit_bug_report(critical_bug_data)
            
            # Assert
            self.assertEqual(bug_id, 1)
            mock_escalate.assert_called_once_with(1)
    
    def test_get_bug_report_by_id_success(self):
        """Test successful bug report retrieval by ID"""
        # Arrange
        bug_id = 1
        expected_bug = get_valid_bug_report_data()
        expected_bug['id'] = bug_id
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = expected_bug
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        bug_report = self.bug_manager.get_by_id(bug_id)
        
        # Assert
        self.assertIsNotNone(bug_report)
        self.assertEqual(bug_report['id'], bug_id)
        self.db_mock.execute_query.assert_called_once()
        self.bug_manager.encryption_manager.decrypt.assert_called()
    
    def test_get_bug_report_by_id_not_found(self):
        """Test bug report retrieval with non-existent ID"""
        # Arrange
        bug_id = 999
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        bug_report = self.bug_manager.get_by_id(bug_id)
        
        # Assert
        self.assertIsNone(bug_report)
        self.db_mock.execute_query.assert_called_once()
    
    def test_update_bug_report_success(self):
        """Test successful bug report update"""
        # Arrange
        bug_id = 1
        update_data = {
            'status': 'Investigating',
            'assigned_to': 456
        }
        
        self.bug_manager.encryption_manager.encrypt.return_value = 'encrypted_data'
        
        # Act
        result = self.bug_manager.update(bug_id, update_data)
        
        # Assert
        self.assertTrue(result)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_get_bug_reports_by_status_success(self):
        """Test successful retrieval of bug reports by status"""
        # Arrange
        status = 'New'
        expected_bugs = [
            get_valid_bug_report_data(),
            get_critical_bug_report_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_bugs
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        bug_reports = self.bug_manager.get_by_status(status)
        
        # Assert
        self.assertEqual(len(bug_reports), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_bug_reports_by_priority_success(self):
        """Test successful retrieval of bug reports by priority"""
        # Arrange
        priority = 'Critical'
        expected_bugs = [
            get_critical_bug_report_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_bugs
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        bug_reports = self.bug_manager.get_by_priority(priority)
        
        # Assert
        self.assertEqual(len(bug_reports), 1)
        self.db_mock.execute_query.assert_called_once()
    
    def test_get_bug_reports_by_app_version_success(self):
        """Test successful retrieval of bug reports by app version"""
        # Arrange
        app_version = '2.1.0'
        expected_bugs = [
            get_valid_bug_report_data(),
            get_critical_bug_report_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_bugs
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        bug_reports = self.bug_manager.get_by_app_version(app_version)
        
        # Assert
        self.assertEqual(len(bug_reports), 2)
        self.db_mock.execute_query.assert_called_once()
    
    def test_search_bug_reports_success(self):
        """Test successful bug report search"""
        # Arrange
        search_criteria = {
            'error_type': 'RuntimeError',
            'app_version': '2.1.0',
            'status': 'New'
        }
        
        expected_results = [
            get_valid_bug_report_data()
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_results
        self.db_mock.execute_query.return_value = mock_cursor
        
        self.bug_manager.encryption_manager.decrypt.return_value = 'decrypted_data'
        
        # Act
        results = self.bug_manager.search(search_criteria)
        
        # Assert
        self.assertEqual(len(results), 1)
        self.db_mock.execute_query.assert_called_once()
    
    def test_escalate_bug_report_success(self):
        """Test successful bug report escalation"""
        # Arrange
        bug_id = 1
        mock_bug = Mock()
        mock_bug.priority = 'High'
        self.bug_manager.get_by_id.return_value = mock_bug
        
        # Act
        result = self.bug_manager.escalate_bug_report(bug_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_bug.priority, 'Critical')
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_resolve_bug_report_success(self):
        """Test successful bug report resolution"""
        # Arrange
        bug_id = 1
        resolution_notes = 'Fixed division by zero error in order calculation'
        mock_bug = Mock()
        mock_bug.status = 'Investigating'
        self.bug_manager.get_by_id.return_value = mock_bug
        
        # Act
        result = self.bug_manager.resolve_bug_report(bug_id, resolution_notes)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_bug.status, 'Fixed')
        self.assertEqual(mock_bug.resolution_notes, resolution_notes)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_verify_bug_report_success(self):
        """Test successful bug report verification"""
        # Arrange
        bug_id = 1
        mock_bug = Mock()
        mock_bug.status = 'Fixed'
        self.bug_manager.get_by_id.return_value = mock_bug
        
        # Act
        result = self.bug_manager.verify_bug_report(bug_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_bug.status, 'Verified')
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_close_bug_report_success(self):
        """Test successful bug report closure"""
        # Arrange
        bug_id = 1
        mock_bug = Mock()
        mock_bug.status = 'Verified'
        self.bug_manager.get_by_id.return_value = mock_bug
        
        # Act
        result = self.bug_manager.close_bug_report(bug_id)
        
        # Assert
        self.assertTrue(result)
        self.assertEqual(mock_bug.status, 'Closed')
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_get_bug_statistics_success(self):
        """Test successful bug statistics retrieval"""
        # Arrange
        expected_stats = {
            'total_bugs': 25,
            'new_bugs': 5,
            'investigating_bugs': 8,
            'fixed_bugs': 10,
            'verified_bugs': 2,
            'bugs_by_priority': {
                'Low': 5,
                'Medium': 10,
                'High': 8,
                'Critical': 2
            },
            'bugs_by_version': {
                '2.1.0': 15,
                '2.0.0': 8,
                '1.9.0': 2
            }
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (25, 5, 8, 10, 2)
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        stats = self.bug_manager.get_statistics()
        
        # Assert
        self.assertEqual(stats['total_bugs'], 25)
        self.assertEqual(stats['new_bugs'], 5)
        self.assertEqual(stats['investigating_bugs'], 8)
        self.assertEqual(stats['fixed_bugs'], 10)
        self.assertEqual(stats['verified_bugs'], 2)
    
    def test_validate_bug_report_data_success(self):
        """Test successful bug report data validation"""
        # Arrange
        bug_data = get_valid_bug_report_data()
        
        # Act
        result = self.bug_manager.validate_bug_report_data(bug_data)
        
        # Assert
        self.assertTrue(result)
    
    def test_validate_bug_report_data_missing_required_field(self):
        """Test bug report data validation with missing required field"""
        # Arrange
        invalid_bug_data = {
            'user_id': 123,
            'error_type': 'RuntimeError',
            # Missing error_message
            'stack_trace': 'Traceback...'
        }
        
        # Act & Assert
        with self.assertRaises(ValueError):
            self.bug_manager.validate_bug_report_data(invalid_bug_data)
    
    def test_generate_bug_id_success(self):
        """Test successful bug ID generation"""
        # Act
        bug_id = self.bug_manager.generate_bug_id()
        
        # Assert
        self.assertIsNotNone(bug_id)
        self.assertIsInstance(bug_id, str)
        self.assertTrue(bug_id.startswith('BUG-'))
    
    def test_attach_screenshot_success(self):
        """Test successful screenshot attachment"""
        # Arrange
        bug_id = 1
        screenshot_path = '/path/to/screenshot.png'
        
        mock_cursor = Mock()
        mock_cursor.lastrowid = 1
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        attachment_id = self.bug_manager.attach_screenshot(bug_id, screenshot_path)
        
        # Assert
        self.assertEqual(attachment_id, 1)
        self.db_mock.execute_query.assert_called_once()
        self.db_mock.commit.assert_called_once()
    
    def test_get_bug_attachments_success(self):
        """Test successful retrieval of bug attachments"""
        # Arrange
        bug_id = 1
        expected_attachments = [
            {
                'id': 1,
                'bug_id': bug_id,
                'filename': 'screenshot.png',
                'file_path': '/path/to/screenshot.png',
                'file_size': 1024,
                'mime_type': 'image/png'
            }
        ]
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = expected_attachments
        self.db_mock.execute_query.return_value = mock_cursor
        
        # Act
        attachments = self.bug_manager.get_attachments(bug_id)
        
        # Assert
        self.assertEqual(len(attachments), 1)
        self.db_mock.execute_query.assert_called_once()
```

## Email Service Tests

### Test Class Structure

```python
# tests/unit/support_system/test_email_service.py
"""Unit tests for Email Service"""

import unittest
from unittest.mock import Mock, patch
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.email_service import EmailService

class TestEmailService(unittest.TestCase):
    """Test cases for Email Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.email_config = {
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@test.com',
            'password': 'test_password',
            'use_tls': True
        }
        
        self.email_service = EmailService(self.email_config)
    
    def test_send_ticket_acknowledgment_success(self):
        """Test successful ticket acknowledgment email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'user_email': 'user@example.com',
            'subject': 'Login Issue',
            'description': 'Unable to login with valid credentials'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_ticket_acknowledgment(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@test.com', 'test_password')
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    def test_send_ticket_update_success(self):
        """Test successful ticket update email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'user_email': 'user@example.com',
            'status': 'In Progress',
            'assigned_to': 'support_agent@example.com'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_ticket_update(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_contact_acknowledgment_success(self):
        """Test successful contact acknowledgment email"""
        # Arrange
        contact_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'subject': 'General Inquiry',
            'message': 'I would like to know more about your POS system'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_contact_acknowledgment(contact_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_escalation_notification_success(self):
        """Test successful escalation notification email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'priority': 'Critical',
            'subject': 'System Crash',
            'assigned_to': 'manager@example.com'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_escalation_notification(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_assignment_notification_success(self):
        """Test successful assignment notification email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'assigned_to': 'agent@example.com',
            'subject': 'Login Issue',
            'priority': 'Medium'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_assignment_notification(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_closure_notification_success(self):
        """Test successful closure notification email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'user_email': 'user@example.com',
            'subject': 'Login Issue',
            'resolution_note': 'Issue resolved by updating user credentials'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_closure_notification(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_reopen_notification_success(self):
        """Test successful reopen notification email"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'assigned_to': 'agent@example.com',
            'subject': 'Login Issue',
            'reopen_reason': 'Issue persists after attempted fix'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_reopen_notification(ticket_data)
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.send_message.assert_called_once()
    
    def test_send_email_smtp_error(self):
        """Test email sending with SMTP error"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'user_email': 'user@example.com',
            'subject': 'Login Issue'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("SMTP connection failed")
            
            # Act
            result = self.email_service.send_ticket_acknowledgment(ticket_data)
            
            # Assert
            self.assertFalse(result)
    
    def test_send_email_authentication_error(self):
        """Test email sending with authentication error"""
        # Arrange
        ticket_data = {
            'ticket_number': 'SUP-2023-001',
            'user_email': 'user@example.com',
            'subject': 'Login Issue'
        }
        
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.send_ticket_acknowledgment(ticket_data)
            
            # Assert
            self.assertFalse(result)
    
    def test_create_email_message_success(self):
        """Test successful email message creation"""
        # Arrange
        to_email = 'recipient@example.com'
        subject = 'Test Subject'
        body = 'Test email body'
        
        # Act
        message = self.email_service.create_email_message(to_email, subject, body)
        
        # Assert
        self.assertIsInstance(message, MIMEMultipart)
        self.assertEqual(message['To'], to_email)
        self.assertEqual(message['Subject'], subject)
        self.assertIn(body, message.as_string())
    
    def test_create_html_email_message_success(self):
        """Test successful HTML email message creation"""
        # Arrange
        to_email = 'recipient@example.com'
        subject = 'Test Subject'
        html_body = '<html><body><h1>Test HTML Email</h1></body></html>'
        
        # Act
        message = self.email_service.create_html_email_message(to_email, subject, html_body)
        
        # Assert
        self.assertIsInstance(message, MIMEMultipart)
        self.assertEqual(message['To'], to_email)
        self.assertEqual(message['Subject'], subject)
        self.assertIn(html_body, message.as_string())
    
    def test_test_connection_success(self):
        """Test successful SMTP connection test"""
        # Arrange
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            
            # Act
            result = self.email_service.test_connection()
            
            # Assert
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@test.com', 'test_password')
            mock_server.quit.assert_called_once()
    
    def test_test_connection_failure(self):
        """Test SMTP connection test failure"""
        # Arrange
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.side_effect = smtplib.SMTPException("Connection failed")
            
            # Act
            result = self.email_service.test_connection()
            
            # Assert
            self.assertFalse(result)
    
    def test_validate_email_address_success(self):
        """Test successful email address validation"""
        # Arrange
        valid_emails = [
            'user@example.com',
            'test.email@domain.co.uk',
            'user+tag@example.org',
            'user.name@sub.domain.com'
        ]
        
        # Act & Assert
        for email in valid_emails:
            result = self.email_service.validate_email_address(email)
            self.assertTrue(result, f"Email {email} should be valid")
    
    def test_validate_email_address_failure(self):
        """Test email address validation failure"""
        # Arrange
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user..name@example.com',
            'user@.example.com',
            'user@example.'
        ]
        
        # Act & Assert
        for email in invalid_emails:
            result = self.email_service.validate_email_address(email)
            self.assertFalse(result, f"Email {email} should be invalid")
    
    def test_get_email_template_success(self):
        """Test successful email template retrieval"""
        # Arrange
        template_name = 'ticket_acknowledgment'
        expected_template = {
            'subject': 'Ticket #{ticket_number} Acknowledgment',
            'body': 'Dear {name},\n\nYour ticket #{ticket_number} has been received.\n\nSubject: {subject}\n\nWe will respond within 24 hours.\n\nBest regards,\nSupport Team'
        }
        
        with patch.object(self.email_service, 'load_template') as mock_load:
            mock_load.return_value = expected_template
            
            # Act
            template = self.email_service.get_template(template_name)
            
            # Assert
            self.assertEqual(template, expected_template)
            mock_load.assert_called_once_with(template_name)
    
    def test_render_email_template_success(self):
        """Test successful email template rendering"""
        # Arrange
        template = {
            'subject': 'Ticket #{ticket_number} Acknowledgment',
            'body': 'Dear {name},\n\nYour ticket #{ticket_number} has been received.\n\nSubject: {subject}'
        }
        
        context = {
            'ticket_number': 'SUP-2023-001',
            'name': 'John Doe',
            'subject': 'Login Issue'
        }
        
        # Act
        rendered = self.email_service.render_template(template, context)
        
        # Assert
        self.assertIn('Ticket #SUP-2023-001 Acknowledgment', rendered['subject'])
        self.assertIn('Dear John Doe', rendered['body'])
        self.assertIn('Your ticket #SUP-2023-001 has been received', rendered['body'])
        self.assertIn('Subject: Login Issue', rendered['body'])
```

## Security Tests

### Security Test Class Structure

```python
# tests/unit/support_system/test_support_security.py
"""Security tests for Support System"""

import unittest
from unittest.mock import Mock, patch
import os
import tempfile
from src.utils.support_manager import SupportManager
from src.managers.ticket_manager import TicketManager
from src.managers.contact_manager import ContactManager
from src.utils.encryption import EncryptionManager
from tests.unit.support_system.fixtures.ticket_data import get_valid_ticket_data
from tests.unit.support_system.fixtures.contact_data import get_valid_contact_data

class TestSupportSecurity(unittest.TestCase):
    """Security test cases for Support System"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app_mock = Mock()
        self.app_mock.db = Mock()
        self.support_manager = SupportManager(self.app_mock)
        
        # Mock dependencies
        self.support_manager.ticket_manager = Mock()
        self.support_manager.contact_manager = Mock()
        self.support_manager.bug_manager = Mock()
        self.support_manager.email_service = Mock()
        self.support_manager.encryption_manager = Mock()
        
        self.ticket_manager = TicketManager(self.app_mock.db)
        self.ticket_manager.encryption_manager = Mock()
        
        self.contact_manager = ContactManager(self.app_mock.db)
        self.contact_manager.encryption_manager = Mock()
        
        self.encryption_manager = EncryptionManager()
    
    def test_sensitive_data_encryption(self):
        """Test encryption of sensitive data in tickets"""
        # Arrange
        sensitive_description = 'User password: secret123, Credit card: 4111-1111-1111-1111'
        ticket_data = get_valid_ticket_data()
        ticket_data['description'] = sensitive_description
        
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_sensitive_data'
        self.support_manager.ticket_manager.create.return_value = 1
        
        # Act
        ticket_id = self.support_manager.create_ticket(
            ticket_data['user_id'],
            ticket_data['category'],
            ticket_data['subject'],
            sensitive_description,
            ticket_data['priority']
        )
        
        # Assert
        self.assertEqual(ticket_id, 1)
        self.support_manager.encryption_manager.encrypt.assert_called_once_with(sensitive_description)
        
        # Verify sensitive data is not stored in plain text
        call_args = self.support_manager.ticket_manager.create.call_args[0][0]
        self.assertNotIn('secret123', call_args['description'])
        self.assertNotIn('4111-1111-1111-1111', call_args['description'])
    
    def test_sensitive_data_decryption(self):
        """Test decryption of sensitive data from tickets"""
        # Arrange
        encrypted_description = 'encrypted_sensitive_data'
        decrypted_description = 'User password: secret123, Credit card: 4111-1111-1111-1111'
        
        mock_ticket = {
            'id': 1,
            'description': encrypted_description,
            'subject': 'Login Issue'
        }
        
        self.support_manager.ticket_manager.get_by_id.return_value = mock_ticket
        self.support_manager.encryption_manager.decrypt.return_value = decrypted_description
        
        # Act
        ticket = self.support_manager.get_ticket(1)
        
        # Assert
        self.assertEqual(ticket['description'], decrypted_description)
        self.support_manager.encryption_manager.decrypt.assert_called_once_with(encrypted_description)
    
    def test_contact_information_encryption(self):
        """Test encryption of contact information"""
        # Arrange
        contact_data = get_valid_contact_data()
        
        self.contact_manager.encryption_manager.encrypt.return_value = 'encrypted_email'
        self.contact_manager.encryption_manager.encrypt.return_value = 'encrypted_phone'
        
        # Act
        contact_id = self.contact_manager.submit_contact_form(contact_data)
        
        # Assert
        self.contact_manager.encryption_manager.encrypt.assert_called()
        
        # Verify email and phone are encrypted
        email_call = self.contact_manager.encryption_manager.encrypt.call_args_list[0]
        phone_call = self.contact_manager.encryption_manager.encrypt.call_args_list[1]
        
        self.assertEqual(email_call[0][0], contact_data['email'])
        self.assertEqual(phone_call[0][0], contact_data['phone'])
    
    def test_access_control_ticket_creation(self):
        """Test access control for ticket creation"""
        # Arrange
        user_permissions = ['ticket_create', 'ticket_view']
        unauthorized_permissions = ['ticket_view']
        
        # Act & Assert
        # User with create permissions should be able to create tickets
        result = self.support_manager.check_access('ticket_create', user_permissions)
        self.assertTrue(result)
        
        # User without create permissions should not be able to create tickets
        result = self.support_manager.check_access('ticket_create', unauthorized_permissions)
        self.assertFalse(result)
    
    def test_access_control_ticket_assignment(self):
        """Test access control for ticket assignment"""
        # Arrange
        agent_permissions = ['ticket_view', 'ticket_update']
        manager_permissions = ['ticket_view', 'ticket_update', 'ticket_assign']
        
        # Act & Assert
        # Agent should not be able to assign tickets
        result = self.support_manager.check_access('ticket_assign', agent_permissions)
        self.assertFalse(result)
        
        # Manager should be able to assign tickets
        result = self.support_manager.check_access('ticket_assign', manager_permissions)
        self.assertTrue(result)
    
    def test_access_control_bug_report_deletion(self):
        """Test access control for bug report deletion"""
        # Arrange
        developer_permissions = ['bug_view', 'bug_update', 'bug_create']
        admin_permissions = ['bug_view', 'bug_update', 'bug_create', 'bug_delete']
        
        # Act & Assert
        # Developer should not be able to delete bug reports
        result = self.support_manager.check_access('bug_delete', developer_permissions)
        self.assertFalse(result)
        
        # Admin should be able to delete bug reports
        result = self.support_manager.check_access('bug_delete', admin_permissions)
        self.assertTrue(result)
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in search queries"""
        # Arrange
        malicious_input = "'; DROP TABLE support_tickets; --"
        search_criteria = {
            'subject': malicious_input
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        self.app_mock.db.execute_query.return_value = mock_cursor
        
        # Act
        results = self.support_manager.search_tickets(search_criteria)
        
        # Assert
        # Verify the query was executed with parameterized values
        self.app_mock.db.execute_query.assert_called_once()
        call_args = self.app_mock.db.execute_query.call_args[0]
        
        # The malicious input should be passed as a parameter, not concatenated
        self.assertIn(malicious_input, call_args[1])
    
    def test_xss_prevention_in_ticket_content(self):
        """Test XSS prevention in ticket content"""
        # Arrange
        xss_payload = '<script>alert("XSS Attack")</script>'
        ticket_data = get_valid_ticket_data()
        ticket_data['description'] = xss_payload
        
        self.support_manager.ticket_manager.create.return_value = 1
        
        # Act
        ticket_id = self.support_manager.create_ticket(
            ticket_data['user_id'],
            ticket_data['category'],
            ticket_data['subject'],
            xss_payload,
            ticket_data['priority']
        )
        
        # Assert
        self.assertEqual(ticket_id, 1)
        
        # Verify the XSS payload is sanitized
        call_args = self.support_manager.ticket_manager.create.call_args[0][0]
        self.assertNotIn('<script>', call_args['description'])
        self.assertNotIn('alert(', call_args['description'])
    
    def test_file_upload_security(self):
        """Test security of file uploads"""
        # Arrange
        malicious_file = 'malicious.exe'
        allowed_extensions = ['.png', '.jpg', '.pdf', '.txt']
        
        # Act
        is_allowed = self.support_manager.is_file_extension_allowed(malicious_file, allowed_extensions)
        
        # Assert
        self.assertFalse(is_allowed)
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        # Arrange
        large_file_size = 10 * 1024 * 1024  # 10MB
        max_file_size = 5 * 1024 * 1024  # 5MB
        
        # Act
        is_allowed = self.support_manager.is_file_size_allowed(large_file_size, max_file_size)
        
        # Assert
        self.assertFalse(is_allowed)
    
    def test_rate_limiting_ticket_creation(self):
        """Test rate limiting for ticket creation"""
        # Arrange
        user_id = 123
        rate_limit_window = 300  # 5 minutes
        max_tickets_per_window = 5
        
        # Mock recent ticket count
        self.support_manager.ticket_manager.get_recent_ticket_count.return_value = 5
        
        # Act
        is_allowed = self.support_manager.check_rate_limit(
            user_id, 'ticket_create', rate_limit_window, max_tickets_per_window
        )
        
        # Assert
        self.assertFalse(is_allowed)  # Should be at the limit
    
    def test_session_security(self):
        """Test session security measures"""
        # Arrange
        user_id = 123
        user_role = 'support_agent'
        
        # Act
        session_token = self.support_manager.create_secure_session(user_id, user_role)
        
        # Assert
        self.assertIsNotNone(session_token)
        self.assertIsInstance(session_token, str)
        self.assertGreater(len(session_token), 20)  # Should be sufficiently long
        
        # Verify session token format
        import re
        self.assertTrue(re.match(r'^[a-zA-Z0-9_-]+$', session_token))
    
    def test_audit_logging(self):
        """Test audit logging for security events"""
        # Arrange
        security_event = {
            'event_type': 'unauthorized_access_attempt',
            'user_id': 123,
            'resource': 'ticket_assignment',
            'timestamp': '2023-01-01T12:00:00Z',
            'ip_address': '192.168.1.100'
        }
        
        # Act
        self.support_manager.log_security_event(security_event)
        
        # Assert
        self.support_manager.ticket_manager.log_security_event.assert_called_once_with(security_event)
    
    def test_password_policy_enforcement(self):
        """Test password policy enforcement"""
        # Arrange
        weak_passwords = [
            'password',
            '123456',
            'qwerty',
            'admin'
        ]
        
        strong_passwords = [
            'SecureP@ss123!',
            'MyStr0ngP@ssword',
            'C0mpl3xP@ssw0rd!'
        ]
        
        # Act & Assert
        for password in weak_passwords:
            is_strong = self.support_manager.validate_password_strength(password)
            self.assertFalse(is_strong, f"Password '{password}' should be weak")
        
        for password in strong_passwords:
            is_strong = self.support_manager.validate_password_strength(password)
            self.assertTrue(is_strong, f"Password '{password}' should be strong")
    
    def test_data_retention_policy(self):
        """Test data retention policy enforcement"""
        # Arrange
        old_ticket_date = datetime.datetime(2020, 1, 1)  # Very old ticket
        current_date = datetime.datetime(2023, 1, 1)
        retention_period_days = 730  # 2 years
        
        # Act
        should_retain = self.support_manager.should_retain_data(old_ticket_date, current_date, retention_period_days)
        
        # Assert
        self.assertFalse(should_retain)  # Should not retain data older than retention period
    
    def test_backup_encryption(self):
        """Test backup file encryption"""
        # Arrange
        backup_data = 'Sensitive ticket and contact data'
        
        # Act
        encrypted_backup = self.support_manager.encrypt_backup_data(backup_data)
        
        # Assert
        self.assertNotEqual(encrypted_backup, backup_data)
        self.assertIsNotNone(encrypted_backup)
        
        # Verify backup can be decrypted
        decrypted_backup = self.support_manager.decrypt_backup_data(encrypted_backup)
        self.assertEqual(decrypted_backup, backup_data)
```

## Performance Tests

### Performance Test Class Structure

```python
# tests/unit/support_system/test_support_performance.py
"""Performance tests for Support System"""

import unittest
import time
import statistics
from unittest.mock import Mock, patch
from src.utils.support_manager import SupportManager
from src.managers.ticket_manager import TicketManager
from src.managers.contact_manager import ContactManager
from tests.unit.support_system.fixtures.ticket_data import get_valid_ticket_data
from tests.unit.support_system.fixtures.contact_data import get_valid_contact_data

class TestSupportPerformance(unittest.TestCase):
    """Performance test cases for Support System"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app_mock = Mock()
        self.app_mock.db = Mock()
        self.support_manager = SupportManager(self.app_mock)
        
        # Mock dependencies
        self.support_manager.ticket_manager = Mock()
        self.support_manager.contact_manager = Mock()
        self.support_manager.bug_manager = Mock()
        self.support_manager.email_service = Mock()
        self.support_manager.encryption_manager = Mock()
        
        self.ticket_manager = TicketManager(self.app_mock.db)
        self.ticket_manager.encryption_manager = Mock()
        
        self.contact_manager = ContactManager(self.app_mock.db)
        self.contact_manager.encryption_manager = Mock()
    
    def test_ticket_creation_performance(self):
        """Test ticket creation performance"""
        # Arrange
        ticket_data = get_valid_ticket_data()
        
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        # Act
        creation_times = []
        for _ in range(100):
            start_time = time.time()
            self.support_manager.create_ticket(
                ticket_data['user_id'],
                ticket_data['category'],
                ticket_data['subject'],
                ticket_data['description'],
                ticket_data['priority']
            )
            end_time = time.time()
            creation_times.append(end_time - start_time)
        
        # Assert
        average_time = statistics.mean(creation_times)
        max_time = max(creation_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.2, "Average ticket creation time should be less than 200ms")
        self.assertLess(max_time, 0.5, "Maximum ticket creation time should be less than 500ms")
    
    def test_ticket_search_performance(self):
        """Test ticket search performance"""
        # Arrange
        search_criteria = {
            'category': 'Technical Support',
            'status': 'Open',
            'priority': 'High'
        }
        
        expected_results = [get_valid_ticket_data() for _ in range(50)]
        self.support_manager.ticket_manager.search.return_value = expected_results
        
        # Act
        search_times = []
        for _ in range(100):
            start_time = time.time()
            self.support_manager.search_tickets(search_criteria)
            end_time = time.time()
            search_times.append(end_time - start_time)
        
        # Assert
        average_time = statistics.mean(search_times)
        max_time = max(search_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.1, "Average ticket search time should be less than 100ms")
        self.assertLess(max_time, 0.3, "Maximum ticket search time should be less than 300ms")
    
    def test_contact_form_processing_performance(self):
        """Test contact form processing performance"""
        # Arrange
        contact_data = get_valid_contact_data()
        
        self.support_manager.contact_manager.submit_contact_form.return_value = 1
        
        # Act
        processing_times = []
        for _ in range(100):
            start_time = time.time()
            self.support_manager.process_contact_form(contact_data)
            end_time = time.time()
            processing_times.append(end_time - start_time)
        
        # Assert
        average_time = statistics.mean(processing_times)
        max_time = max(processing_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.15, "Average contact form processing time should be less than 150ms")
        self.assertLess(max_time, 0.4, "Maximum contact form processing time should be less than 400ms")
    
    def test_email_notification_performance(self):
        """Test email notification performance"""
        # Arrange
        ticket_data = get_valid_ticket_data()
        
        # Mock email sending with delay
        def mock_send_email(*args, **kwargs):
            time.sleep(0.01)  # Simulate 10ms email sending time
        
        self.support_manager.email_service.send_ticket_acknowledgment.side_effect = mock_send_email
        
        # Act
        notification_times = []
        for _ in range(50):
            start_time = time.time()
            self.support_manager.email_service.send_ticket_acknowledgment(ticket_data)
            end_time = time.time()
            notification_times.append(end_time - start_time)
        
        # Assert
        average_time = statistics.mean(notification_times)
        max_time = max(notification_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.05, "Average email notification time should be less than 50ms")
        self.assertLess(max_time, 0.1, "Maximum email notification time should be less than 100ms")
    
    def test_encryption_decryption_performance(self):
        """Test encryption/decryption performance"""
        # Arrange
        test_data_sizes = [100, 1000, 10000, 100000]  # bytes
        
        for data_size in test_data_sizes:
            with self.subTest(data_size=data_size):
                test_data = 'A' * data_size
                
                # Act
                encryption_times = []
                decryption_times = []
                
                for _ in range(20):
                    # Encryption
                    start_time = time.time()
                    encrypted_data = self.support_manager.encryption_manager.encrypt(test_data)
                    encryption_time = time.time() - start_time
                    encryption_times.append(encryption_time)
                    
                    # Decryption
                    start_time = time.time()
                    decrypted_data = self.support_manager.encryption_manager.decrypt(encrypted_data)
                    decryption_time = time.time() - start_time
                    decryption_times.append(decryption_time)
                    
                    # Verify correctness
                    self.assertEqual(decrypted_data, test_data)
                
                # Assert
                avg_encryption_time = statistics.mean(encryption_times)
                avg_decryption_time = statistics.mean(decryption_times)
                
                # Performance requirements (data size dependent)
                max_encryption_time = 0.01 * (data_size / 100)  # 10ms per 100 bytes
                max_decryption_time = 0.01 * (data_size / 100)  # 10ms per 100 bytes
                
                self.assertLess(avg_encryption_time, max_encryption_time,
                               f"Encryption for {data_size} bytes should be faster than {max_encryption_time}s")
                self.assertLess(avg_decryption_time, max_decryption_time,
                               f"Decryption for {data_size} bytes should be faster than {max_decryption_time}s")
    
    def test_concurrent_ticket_operations(self):
        """Test performance under concurrent ticket operations"""
        # Arrange
        import threading
        import queue
        
        ticket_data = get_valid_ticket_data()
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        # Act
        results = queue.Queue()
        threads = []
        
        def create_ticket_thread():
            start_time = time.time()
            self.support_manager.create_ticket(
                ticket_data['user_id'],
                ticket_data['category'],
                ticket_data['subject'],
                ticket_data['description'],
                ticket_data['priority']
            )
            end_time = time.time()
            results.put(end_time - start_time)
        
        # Create 10 concurrent threads
        for _ in range(10):
            thread = threading.Thread(target=create_ticket_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        operation_times = []
        while not results.empty():
            operation_times.append(results.get())
        
        # Assert
        average_time = statistics.mean(operation_times)
        max_time = max(operation_times)
        
        # Performance requirements for concurrent execution
        self.assertLess(average_time, 0.3, "Average concurrent ticket creation time should be less than 300ms")
        self.assertLess(max_time, 0.6, "Maximum concurrent ticket creation time should be less than 600ms")
    
    def test_memory_usage_during_operations(self):
        """Test memory usage during support operations"""
        # Arrange
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        ticket_data = get_valid_ticket_data()
        self.support_manager.ticket_manager.create.return_value = 1
        self.support_manager.encryption_manager.encrypt.return_value = 'encrypted_description'
        
        # Act
        # Perform many ticket creations to test memory usage
        for _ in range(1000):
            self.support_manager.create_ticket(
                ticket_data['user_id'],
                ticket_data['category'],
                ticket_data['subject'],
                ticket_data['description'],
                ticket_data['priority']
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Assert
        # Memory increase should be minimal (less than 10MB)
        self.assertLess(memory_increase, 10 * 1024 * 1024, 
                       "Memory increase should be less than 10MB after 1000 ticket creations")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [get_valid_ticket_data() for _ in range(100)]
        self.app_mock.db.execute_query.return_value = mock_cursor
        
        # Act
        query_times = []
        for _ in range(50):
            start_time = time.time()
            self.support_manager.ticket_manager.search({})
            end_time = time.time()
            query_times.append(end_time - start_time)
        
        # Assert
        average_time = statistics.mean(query_times)
        max_time = max(query_times)
        
        # Performance requirements
        self.assertLess(average_time, 0.05, "Average database query time should be less than 50ms")
        self.assertLess(max_time, 0.1, "Maximum database query time should be less than 100ms")
    
    def test_file_upload_performance(self):
        """Test file upload performance"""
        # Arrange
        file_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB
        
        for file_size in file_sizes:
            with self.subTest(file_size=file_size):
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(b'A' * file_size)
                    temp_file_path = temp_file.name
                
                try:
                    # Act
                    upload_times = []
                    for _ in range(10):
                        start_time = time.time()
                        # Simulate file processing
                        with open(temp_file_path, 'rb') as f:
                            file_content = f.read()
                        end_time = time.time()
                        upload_times.append(end_time - start_time)
                    
                    # Assert
                    average_time = statistics.mean(upload_times)
                    max_time = max(upload_times)
                    
                    # Performance requirements (file size dependent)
                    max_upload_time = 0.01 * (file_size / 1024)  # 10ms per KB
                    
                    self.assertLess(average_time, max_upload_time,
                                   f"File upload for {file_size} bytes should be faster than {max_upload_time}s")
                    
                finally:
                    # Clean up
                    os.unlink(temp_file_path)
    
    def test_cache_performance(self):
        """Test performance improvement with caching"""
        # Arrange
        search_criteria = {'category': 'Technical Support'}
        
        # Mock search with delay
        def mock_search_with_delay(criteria):
            time.sleep(0.02)  # Simulate 20ms search time
            return [get_valid_ticket_data()]
        
        self.support_manager.ticket_manager.search.side_effect = mock_search_with_delay
        
        # Act - First search (no cache)
        start_time = time.time()
        self.support_manager.search_tickets(search_criteria)
        first_search_time = time.time() - start_time
        
        # Act - Second search (with cache)
        start_time = time.time()
        self.support_manager.search_tickets(search_criteria)
        second_search_time = time.time() - start_time
        
        # Assert
        # Cached search should be significantly faster
        self.assertLess(second_search_time, first_search_time * 0.5,
                       "Cached search should be at least 50% faster")
```

## Test Coverage Requirements

### Coverage Metrics

1. **Statement Coverage**: Minimum 95%
2. **Branch Coverage**: Minimum 90%
3. **Function Coverage**: Minimum 100%
4. **Line Coverage**: Minimum 95%

### Coverage Configuration

```ini
# .coveragerc
[run]
source = src/utils,src/managers
omit = 
    */tests/*
    */venv/*
    */env/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

[html]
directory = htmlcov
```

### Coverage Script

```python
# scripts/run_support_coverage.py
"""Script to run support system test coverage analysis"""

import subprocess
import sys

def run_coverage():
    """Run coverage analysis"""
    print("Running support system test coverage analysis...")
    
    # Run coverage
    result = subprocess.run([
        sys.executable, '-m', 'coverage', 'run',
        '--source=src/utils,src/managers',
        '-m', 'unittest', 'discover', 'tests/unit/support_system',
        '-v'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Coverage run failed:")
        print(result.stderr)
        return False
    
    # Generate coverage report
    result = subprocess.run([
        sys.executable, '-m', 'coverage', 'report',
        '--fail-under=90'
    ], capture_output=True, text=True)
    
    print("Coverage Report:")
    print(result.stdout)
    
    if result.returncode != 0:
        print("Coverage requirements not met")
        return False
    
    # Generate HTML report
    subprocess.run([
        sys.executable, '-m', 'coverage', 'html'
    ])
    
    print("HTML coverage report generated in htmlcov/")
    return True

if __name__ == '__main__':
    success = run_coverage()
    sys.exit(0 if success else 1)
```

## Test Execution

### Running Tests

```bash
# Run all support system tests
python -m unittest discover tests/unit/support_system -v

# Run specific test class
python -m unittest tests.unit.support_system.test_support_manager.TestSupportManager -v

# Run specific test method
python -m unittest tests.unit.support_system.test_support_manager.TestSupportManager.test_create_ticket_success -v

# Run with coverage
python -m coverage run -m unittest discover tests/unit/support_system
python -m coverage report
python -m coverage html

# Run performance tests
python -m unittest tests.unit.support_system.test_support_performance -v

# Run security tests
python -m unittest tests.unit.support_system.test_support_security -v
```

### Test Configuration

```python
# tests/conftest.py
"""Pytest configuration for support system tests"""

import pytest
import tempfile
import os
from unittest.mock import Mock

@pytest.fixture
def temp_support_dir():
    """Create temporary directory for support files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_app_instance():
    """Create mock application instance"""
    app = Mock()
    app.db = Mock()
    return app

@pytest.fixture
def mock_encryption_manager():
    """Create mock encryption manager"""
    manager = Mock()
    manager.encrypt.return_value = 'encrypted_data'
    manager.decrypt.return_value = 'decrypted_data'
    return manager

@pytest.fixture
def valid_ticket_data():
    """Get valid ticket data for testing"""
    from tests.unit.support_system.fixtures.ticket_data import get_valid_ticket_data
    return get_valid_ticket_data()

@pytest.fixture
def valid_contact_data():
    """Get valid contact data for testing"""
    from tests.unit.support_system.fixtures.contact_data import get_valid_contact_data
    return get_valid_contact_data()
```

---

This comprehensive unit testing framework provides thorough coverage of the support system, ensuring all components are properly tested for functionality, security, and performance. The framework includes test fixtures, mock objects, and performance benchmarks to maintain high code quality and reliability.