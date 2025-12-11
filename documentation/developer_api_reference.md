# Developer API Reference for Support and License Systems

## Overview

This document provides comprehensive API reference for developers integrating with or extending the support system and license validation system in Restaurant POS MVP application. It includes REST APIs, Python APIs, and integration examples.

## Table of Contents

1. [API Overview](#api-overview)
2. [License System API](#license-system-api)
3. [Support System API](#support-system-api)
4. [Python SDK Reference](#python-sdk-reference)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)
7. [Security Considerations](#security-considerations)
8. [Rate Limiting](#rate-limiting)

## API Overview

### Base URLs

#### Production Environment
```
https://api.restaurantpos.com/v1
```

#### Staging Environment
```
https://staging-api.restaurantpos.com/v1
```

#### Development Environment
```
https://dev-api.restaurantpos.com/v1
```

### Authentication

All API requests require authentication using API keys:

```http
Authorization: Bearer YOUR_API_KEY
```

#### Obtaining API Keys

1. **Register for Developer Account**:
   - Visit https://developers.restaurantpos.com
   - Register your application
   - Receive API key and secret

2. **API Key Types**:
   - **Test Key**: For development and testing
   - **Production Key**: For production use
   - **Read-only Key**: For data access only

### Response Format

All API responses follow consistent format:

```json
{
    "success": true,
    "data": {
        // Response data
    },
    "message": "Operation completed successfully",
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
}
```

#### Error Response Format

```json
{
    "success": false,
    "error": {
        "code": "LICENSE_NOT_FOUND",
        "message": "License not found",
        "details": "The specified license key does not exist in our system"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
}
```

## License System API

### License Validation

#### Validate License

```http
POST /licenses/validate
```

**Request Body**:
```json
{
    "license_key": "TRIAL-12345-ABCDE",
    "hardware_fingerprint": "abc123def456",
    "validation_type": "online"
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "license_id": "lic_123456789",
        "license_type": "trial",
        "status": "active",
        "expiry_date": "2024-02-14T10:30:00Z",
        "features": [
            "order_management",
            "inventory_management",
            "reporting",
            "multi_user"
        ],
        "hardware_binding": {
            "is_bound": true,
            "binding_date": "2024-01-15T10:30:00Z",
            "fingerprint_match": true
        },
        "validation_result": {
            "is_valid": true,
            "validation_method": "online",
            "validated_at": "2024-01-15T10:30:00Z",
            "next_validation_due": "2024-01-22T10:30:00Z"
        }
    }
}
```

#### Check Feature Access

```http
POST /licenses/check-feature
```

**Request Body**:
```json
{
    "license_key": "STD-67890-FGHIJ",
    "feature": "inventory_management",
    "context": {
        "user_id": "user_123",
        "location_id": "loc_456"
    }
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "feature_allowed": true,
        "license_type": "standard",
        "restrictions": [],
        "expiry_date": null,
        "grace_period_active": false
    }
}
```

### License Management

#### Activate License

```http
POST /licenses/activate
```

**Request Body**:
```json
{
    "license_key": "PRO-98765-KLMNO",
    "hardware_fingerprint": "xyz789abc456",
    "customer_info": {
        "name": "John Doe",
        "email": "john.doe@restaurant.com",
        "company": "Doe's Restaurant",
        "phone": "+1-555-123-4567"
    },
    "activation_context": {
        "app_version": "2.1.0",
        "os_version": "Windows 11",
        "installation_id": "inst_123456789"
    }
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "activation_id": "act_123456789",
        "license_id": "lic_123456789",
        "status": "activated",
        "activated_at": "2024-01-15T10:30:00Z",
        "features": [
            "order_management",
            "inventory_management",
            "advanced_reporting",
            "gst_reporting",
            "data_export",
            "multi_user",
            "email_notifications"
        ]
    }
}
```

#### Deactivate License

```http
POST /licenses/deactivate
```

**Request Body**:
```json
{
    "license_key": "PRO-98765-KLMNO",
    "deactivation_reason": "Hardware upgrade",
    "deactivation_context": {
        "old_hardware_id": "hw_123456",
        "new_hardware_id": "hw_789012"
    }
}
```

#### Transfer License

```http
POST /licenses/transfer
```

**Request Body**:
```json
{
    "license_key": "PRO-98765-KLMNO",
    "transfer_to": {
        "new_customer_id": "cust_456789",
        "new_hardware_fingerprint": "new_fingerprint_123",
        "transfer_reason": "Equipment upgrade"
    },
    "transfer_context": {
        "initiated_by": "admin_123",
        "approval_code": "transfer_approval_456"
    }
}
```

### License Information

#### Get License Details

```http
GET /licenses/{license_key}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "license_id": "lic_123456789",
        "license_key": "PRO-98765-KLMNO",
        "license_type": "professional",
        "status": "active",
        "customer_info": {
            "name": "John Doe",
            "email": "john.doe@restaurant.com",
            "company": "Doe's Restaurant"
        },
        "issued_date": "2023-06-15T10:30:00Z",
        "activated_date": "2023-06-15T11:00:00Z",
        "expiry_date": null,
        "features": [
            "order_management",
            "inventory_management",
            "advanced_reporting",
            "gst_reporting",
            "data_export",
            "multi_user",
            "email_notifications"
        ],
        "hardware_bindings": [
            {
                "hardware_id": "hw_123456",
                "fingerprint": "abc123def456",
                "bound_at": "2023-06-15T11:00:00Z",
                "is_active": true
            }
        ],
        "validation_history": [
            {
                "validated_at": "2024-01-15T10:30:00Z",
                "validation_method": "online",
                "result": "success",
                "ip_address": "192.168.1.100"
            }
        ]
    }
}
```

#### Get License Usage Statistics

```http
GET /licenses/{license_key}/usage
```

**Query Parameters**:
- `start_date`: Start date for statistics (ISO 8601 format)
- `end_date`: End date for statistics (ISO 8601 format)
- `group_by`: Grouping for statistics (day, week, month)

**Response**:
```json
{
    "success": true,
    "data": {
        "usage_period": {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z"
        },
        "feature_usage": {
            "order_management": {
                "access_count": 1247,
                "unique_users": 5,
                "total_usage_minutes": 8476
            },
            "inventory_management": {
                "access_count": 892,
                "unique_users": 3,
                "total_usage_minutes": 5234
            }
        },
        "validation_statistics": {
            "total_validations": 31,
            "successful_validations": 30,
            "failed_validations": 1,
            "average_response_time_ms": 245
        }
    }
}
```

## Support System API

### Support Tickets

#### Create Support Ticket

```http
POST /support/tickets
```

**Request Body**:
```json
{
    "subject": "KOT orders not appearing in kitchen display",
    "category": "Bug Report",
    "priority": "High",
    "description": "When customers place orders, they don't appear on the kitchen display. This started happening after the latest update.",
    "customer_info": {
        "name": "Jane Smith",
        "email": "jane.smith@restaurant.com",
        "user_id": "user_123456"
    },
    "system_info": {
        "app_version": "2.1.0",
        "os_version": "Windows 11",
        "license_type": "professional",
        "hardware_fingerprint": "abc123def456"
    },
    "attachments": [
        {
            "filename": "screenshot.png",
            "content_type": "image/png",
            "data": "base64_encoded_image_data"
        }
    ]
}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "ticket_id": "ticket_123456789",
        "ticket_number": "SUP-2024-0115",
        "status": "Open",
        "created_at": "2024-01-15T10:30:00Z",
        "estimated_response_time": "2 hours"
    }
}
```

#### Get Support Ticket

```http
GET /support/tickets/{ticket_id}
```

**Response**:
```json
{
    "success": true,
    "data": {
        "ticket_id": "ticket_123456789",
        "ticket_number": "SUP-2024-0115",
        "subject": "KOT orders not appearing in kitchen display",
        "category": "Bug Report",
        "priority": "High",
        "status": "In Progress",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T12:45:00Z",
        "customer_info": {
            "name": "Jane Smith",
            "email": "jane.smith@restaurant.com",
            "user_id": "user_123456"
        },
        "assigned_to": {
            "staff_id": "staff_789",
            "name": "John Support",
            "email": "john.support@restaurantpos.com"
        },
        "conversation": [
            {
                "message_id": "msg_123",
                "sender_type": "customer",
                "message": "When customers place orders, they don't appear on the kitchen display...",
                "created_at": "2024-01-15T10:30:00Z",
                "is_internal": false
            },
            {
                "message_id": "msg_124",
                "sender_type": "staff",
                "message": "Thank you for reporting this issue. We're investigating...",
                "created_at": "2024-01-15T11:15:00Z",
                "is_internal": false
            }
        ],
        "attachments": [
            {
                "attachment_id": "att_123",
                "filename": "screenshot.png",
                "content_type": "image/png",
                "size_bytes": 245768,
                "uploaded_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
}
```

#### Update Support Ticket

```http
PUT /support/tickets/{ticket_id}
```

**Request Body**:
```json
{
    "status": "In Progress",
    "assigned_to": "staff_789",
    "priority": "High",
    "internal_note": "Customer is using version 2.1.0. Need to check for known issues.",
    "customer_message": "Thank you for reporting this issue. We're investigating the KOT display problem and will get back to you shortly."
}
```

#### Add Ticket Message

```http
POST /support/tickets/{ticket_id}/messages
```

**Request Body**:
```json
{
    "message": "I've tried restarting the application, but the issue persists.",
    "message_type": "customer_response",
    "attachments": [
        {
            "filename": "error_log.txt",
            "content_type": "text/plain",
            "data": "base64_encoded_log_data"
        }
    ]
}
```

### Contact Forms

#### Submit Contact Form

```http
POST /support/contact
```

**Request Body**:
```json
{
    "contact_type": "Technical Support",
    "name": "Bob Johnson",
    "email": "bob.johnson@restaurant.com",
    "phone": "+1-555-987-6543",
    "company": "Bob's Bistro",
    "subject": "Question about inventory management",
    "message": "I'd like to know how to set up automatic inventory updates.",
    "preferred_contact_method": "email",
    "urgency": "Medium"
}
```

### Bug Reports

#### Submit Bug Report

```http
POST /support/bugs
```

**Request Body**:
```json
{
    "error_type": "Application Crash",
    "error_message": "Application crashes when generating GST reports",
    "stack_trace": "Traceback (most recent call last):\n  File \"gst_reports.py\", line 234, in generate_report\n    total_tax = calculate_tax(order_total)\nZeroDivisionError: division by zero",
    "reproduction_steps": [
        "Navigate to Reports → GST Reports",
        "Select date range for last month",
        "Click Generate Report",
        "Application crashes"
    ],
    "system_info": {
        "app_version": "2.1.0",
        "os_version": "Windows 11",
        "python_version": "3.9.7",
        "license_type": "professional",
        "available_memory_mb": 8192,
        "disk_space_gb": 456
    },
    "attachments": [
        {
            "filename": "crash_log.txt",
            "content_type": "text/plain",
            "data": "base64_encoded_log_data"
        }
    ]
}
```

## Python SDK Reference

### License System SDK

#### LicenseManager Class

```python
# license_sdk.py
from restaurantpos_sdk import LicenseManager

class LicenseManager:
    """Python SDK for license system integration"""
    
    def __init__(self, api_key, base_url="https://api.restaurantpos.com/v1"):
        """Initialize license manager"""
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def validate_license(self, license_key, hardware_fingerprint, validation_type='online'):
        """Validate a license key"""
        endpoint = f"{self.base_url}/licenses/validate"
        
        payload = {
            'license_key': license_key,
            'hardware_fingerprint': hardware_fingerprint,
            'validation_type': validation_type
        }
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def check_feature_access(self, license_key, feature, context=None):
        """Check if a feature is accessible with a license"""
        endpoint = f"{self.base_url}/licenses/check-feature"
        
        payload = {
            'license_key': license_key,
            'feature': feature
        }
        
        if context:
            payload['context'] = context
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def activate_license(self, license_key, hardware_fingerprint, customer_info, activation_context=None):
        """Activate a license key"""
        endpoint = f"{self.base_url}/licenses/activate"
        
        payload = {
            'license_key': license_key,
            'hardware_fingerprint': hardware_fingerprint,
            'customer_info': customer_info
        }
        
        if activation_context:
            payload['activation_context'] = activation_context
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def get_license_details(self, license_key):
        """Get detailed license information"""
        endpoint = f"{self.base_url}/licenses/{license_key}"
        
        response = self.session.get(endpoint)
        return response.json()
    
    def deactivate_license(self, license_key, deactivation_reason, deactivation_context=None):
        """Deactivate a license key"""
        endpoint = f"{self.base_url}/licenses/deactivate"
        
        payload = {
            'license_key': license_key,
            'deactivation_reason': deactivation_reason
        }
        
        if deactivation_context:
            payload['deactivation_context'] = deactivation_context
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
```

#### Usage Example

```python
# license_example.py
from restaurantpos_sdk import LicenseManager

# Initialize license manager
license_manager = LicenseManager(api_key="your_api_key_here")

# Validate license
validation_result = license_manager.validate_license(
    license_key="TRIAL-12345-ABCDE",
    hardware_fingerprint="abc123def456"
)

if validation_result['success']:
    license_data = validation_result['data']
    print(f"License type: {license_data['license_type']}")
    print(f"Status: {license_data['status']}")
    print(f"Features: {', '.join(license_data['features'])}")
else:
    print(f"Validation failed: {validation_result['error']['message']}")

# Check feature access
feature_result = license_manager.check_feature_access(
    license_key="TRIAL-12345-ABCDE",
    feature="inventory_management",
    context={'user_id': 'user_123'}
)

if feature_result['success'] and feature_result['data']['feature_allowed']:
    print("Feature access granted")
else:
    print("Feature access denied")
```

### Support System SDK

#### SupportManager Class

```python
# support_sdk.py
from restaurantpos_sdk import SupportManager

class SupportManager:
    """Python SDK for support system integration"""
    
    def __init__(self, api_key, base_url="https://api.restaurantpos.com/v1"):
        """Initialize support manager"""
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def create_ticket(self, subject, category, priority, description, customer_info, system_info=None, attachments=None):
        """Create a new support ticket"""
        endpoint = f"{self.base_url}/support/tickets"
        
        payload = {
            'subject': subject,
            'category': category,
            'priority': priority,
            'description': description,
            'customer_info': customer_info
        }
        
        if system_info:
            payload['system_info'] = system_info
        
        if attachments:
            payload['attachments'] = attachments
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def get_ticket(self, ticket_id):
        """Get support ticket details"""
        endpoint = f"{self.base_url}/support/tickets/{ticket_id}"
        
        response = self.session.get(endpoint)
        return response.json()
    
    def update_ticket(self, ticket_id, status=None, assigned_to=None, priority=None, internal_note=None, customer_message=None):
        """Update a support ticket"""
        endpoint = f"{self.base_url}/support/tickets/{ticket_id}"
        
        payload = {}
        if status is not None:
            payload['status'] = status
        if assigned_to is not None:
            payload['assigned_to'] = assigned_to
        if priority is not None:
            payload['priority'] = priority
        if internal_note is not None:
            payload['internal_note'] = internal_note
        if customer_message is not None:
            payload['customer_message'] = customer_message
        
        response = self.session.put(endpoint, json=payload)
        return response.json()
    
    def add_ticket_message(self, ticket_id, message, message_type='customer_response', attachments=None):
        """Add message to support ticket"""
        endpoint = f"{self.base_url}/support/tickets/{ticket_id}/messages"
        
        payload = {
            'message': message,
            'message_type': message_type
        }
        
        if attachments:
            payload['attachments'] = attachments
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def submit_contact_form(self, contact_type, name, email, phone=None, company=None, subject, message, preferred_contact_method='email', urgency='Medium'):
        """Submit a contact form"""
        endpoint = f"{self.base_url}/support/contact"
        
        payload = {
            'contact_type': contact_type,
            'name': name,
            'email': email,
            'subject': subject,
            'message': message,
            'preferred_contact_method': preferred_contact_method,
            'urgency': urgency
        }
        
        if phone:
            payload['phone'] = phone
        if company:
            payload['company'] = company
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
    
    def submit_bug_report(self, error_type, error_message, stack_trace=None, reproduction_steps=None, system_info=None, attachments=None):
        """Submit a bug report"""
        endpoint = f"{self.base_url}/support/bugs"
        
        payload = {
            'error_type': error_type,
            'error_message': error_message
        }
        
        if stack_trace:
            payload['stack_trace'] = stack_trace
        if reproduction_steps:
            payload['reproduction_steps'] = reproduction_steps
        if system_info:
            payload['system_info'] = system_info
        if attachments:
            payload['attachments'] = attachments
        
        response = self.session.post(endpoint, json=payload)
        return response.json()
```

#### Usage Example

```python
# support_example.py
from restaurantpos_sdk import SupportManager

# Initialize support manager
support_manager = SupportManager(api_key="your_api_key_here")

# Create support ticket
ticket_result = support_manager.create_ticket(
    subject="KOT display not working",
    category="Bug Report",
    priority="High",
    description="Kitchen Order Ticket display is not showing new orders",
    customer_info={
        'name': 'Jane Smith',
        'email': 'jane.smith@restaurant.com',
        'user_id': 'user_123456'
    },
    system_info={
        'app_version': '2.1.0',
        'os_version': 'Windows 11',
        'license_type': 'professional'
    }
)

if ticket_result['success']:
    ticket_data = ticket_result['data']
    print(f"Ticket created: {ticket_data['ticket_number']}")
    print(f"Ticket ID: {ticket_data['ticket_id']}")
else:
    print(f"Failed to create ticket: {ticket_result['error']['message']}")

# Add message to ticket
message_result = support_manager.add_ticket_message(
    ticket_id=ticket_data['ticket_id'],
    message="I've tried restarting the system but the issue persists.",
    message_type='customer_response'
)

if message_result['success']:
    print("Message added to ticket")
else:
    print(f"Failed to add message: {message_result['error']['message']}")
```

## Integration Examples

### Webhook Integration

#### License Webhooks

Configure webhooks to receive real-time license events:

```python
# webhook_handlers.py
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/license-events', methods=['POST'])
def handle_license_event():
    """Handle license webhook events"""
    event_data = request.json
    
    # Verify webhook signature
    if not verify_webhook_signature(request):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event_type = event_data.get('event_type')
    license_data = event_data.get('license_data')
    
    if event_type == 'license_activated':
        handle_license_activated(license_data)
    elif event_type == 'license_expired':
        handle_license_expired(license_data)
    elif event_type == 'license_validated':
        handle_license_validated(license_data)
    
    return jsonify({'status': 'received'}), 200

def handle_license_activated(license_data):
    """Handle license activation event"""
    license_key = license_data['license_key']
    customer_email = license_data['customer_info']['email']
    
    # Send welcome email
    send_welcome_email(customer_email, license_key)
    
    # Update internal systems
    update_customer_record(license_data)
    
    # Log activation
    log_license_event('activation', license_data)

def verify_webhook_signature(request):
    """Verify webhook signature for security"""
    signature = request.headers.get('X-Webhook-Signature')
    payload = request.data
    
    # Calculate expected signature
    expected_signature = calculate_signature(payload, webhook_secret)
    
    return hmac.compare_digest(signature, expected_signature)
```

#### Support Webhooks

```python
@app.route('/webhooks/support-events', methods=['POST'])
def handle_support_event():
    """Handle support webhook events"""
    event_data = request.json
    
    if not verify_webhook_signature(request):
        return jsonify({'error': 'Invalid signature'}), 401
    
    event_type = event_data.get('event_type')
    ticket_data = event_data.get('ticket_data')
    
    if event_type == 'ticket_created':
        handle_ticket_created(ticket_data)
    elif event_type == 'ticket_updated':
        handle_ticket_updated(ticket_data)
    elif event_type == 'ticket_assigned':
        handle_ticket_assigned(ticket_data)
    
    return jsonify({'status': 'received'}), 200

def handle_ticket_created(ticket_data):
    """Handle new ticket creation"""
    ticket_id = ticket_data['ticket_id']
    priority = ticket_data['priority']
    
    # Notify support team
    if priority == 'Critical':
        send_critical_alert(ticket_data)
    else:
        send_new_ticket_notification(ticket_data)
    
    # Create task in project management system
    create_support_task(ticket_data)
```

### Database Integration

#### License Database Integration

```python
# database_integration.py
import sqlite3
from restaurantpos_sdk import LicenseManager

class LicenseDatabaseIntegration:
    """Integrate license system with local database"""
    
    def __init__(self, db_path, license_manager):
        self.db_path = db_path
        self.license_manager = license_manager
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
    
    def sync_license_with_database(self, license_key):
        """Sync license information with local database"""
        # Get license details from API
        license_result = self.license_manager.get_license_details(license_key)
        
        if license_result['success']:
            license_data = license_result['data']
            
            # Update local database
            self.cursor.execute("""
                INSERT OR REPLACE INTO licenses 
                (license_key, license_type, status, features, expiry_date, sync_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                license_key,
                license_data['license_type'],
                license_data['status'],
                json.dumps(license_data['features']),
                license_data['expiry_date'],
                datetime.now().isoformat()
            ))
            
            self.connection.commit()
            
            return True
        else:
            return False
    
    def validate_license_locally(self, license_key):
        """Validate license using local database"""
        self.cursor.execute("""
            SELECT * FROM licenses WHERE license_key = ?
        """, (license_key,))
        
        license_record = self.cursor.fetchone()
        
        if not license_record:
            return False
        
        # Check if license is expired
        expiry_date = license_record[3]  # expiry_date column
        if expiry_date and datetime.fromisoformat(expiry_date) < datetime.now():
            return False
        
        return True
```

## Error Handling

### Error Codes

#### License System Error Codes

| Error Code | Description | HTTP Status |
|-------------|-------------|--------------|
| LICENSE_NOT_FOUND | License key not found | 404 |
| LICENSE_EXPIRED | License has expired | 403 |
| LICENSE_REVOKED | License has been revoked | 403 |
| HARDWARE_MISMATCH | Hardware fingerprint doesn't match | 403 |
| VALIDATION_FAILED | License validation failed | 400 |
| ACTIVATION_LIMIT_EXCEEDED | Too many activations | 429 |
| INVALID_LICENSE_FORMAT | Invalid license key format | 400 |

#### Support System Error Codes

| Error Code | Description | HTTP Status |
|-------------|-------------|--------------|
| TICKET_NOT_FOUND | Ticket not found | 404 |
| INVALID_TICKET_STATUS | Invalid ticket status | 400 |
| UNAUTHORIZED_ACCESS | Unauthorized access to ticket | 403 |
| ATTACHMENT_TOO_LARGE | Attachment file too large | 413 |
| INVALID_CATEGORY | Invalid ticket category | 400 |
| RATE_LIMIT_EXCEEDED | Rate limit exceeded | 429 |

### Error Handling Best Practices

```python
# error_handling.py
from restaurantpos_sdk.exceptions import (
    LicenseNotFoundError,
    LicenseExpiredError,
    HardwareMismatchError,
    TicketNotFoundError,
    UnauthorizedAccessError
)

def handle_license_validation(license_key, hardware_fingerprint):
    """Example of robust error handling"""
    try:
        license_manager = LicenseManager(api_key="your_api_key")
        result = license_manager.validate_license(license_key, hardware_fingerprint)
        
        if result['success']:
            return result['data']
        else:
            error = result['error']
            raise Exception(f"License validation failed: {error['message']}")
    
    except LicenseNotFoundError:
        # Handle license not found
        log_error(f"License not found: {license_key}")
        return None
    
    except LicenseExpiredError:
        # Handle expired license
        log_error(f"License expired: {license_key}")
        return {'status': 'expired', 'renewal_required': True}
    
    except HardwareMismatchError:
        # Handle hardware mismatch
        log_error(f"Hardware mismatch for license: {license_key}")
        return {'status': 'hardware_mismatch', 'retransfer_required': True}
    
    except Exception as e:
        # Handle unexpected errors
        log_error(f"Unexpected error: {str(e)}")
        return {'status': 'error', 'message': str(e)}
```

## Security Considerations

### API Key Security

1. **Key Protection**:
   - Never expose API keys in client-side code
   - Use environment variables for key storage
   - Implement key rotation policies
   - Monitor key usage for anomalies

2. **Secure Storage**:
   ```python
   # secure_config.py
   import os
   from cryptography.fernet import Fernet
   
   def encrypt_api_key(api_key, encryption_key):
       """Encrypt API key for storage"""
       f = Fernet(encryption_key)
       encrypted_key = f.encrypt(api_key.encode())
       return encrypted_key.decode()
   
   def decrypt_api_key(encrypted_key, encryption_key):
       """Decrypt API key for use"""
       f = Fernet(encryption_key)
       decrypted_key = f.decrypt(encrypted_key.encode())
       return decrypted_key.decode()
   
   # Load encrypted API key from environment
   encrypted_key = os.environ.get('ENCRYPTED_API_KEY')
   encryption_key = os.environ.get('ENCRYPTION_KEY').encode()
   
   api_key = decrypt_api_key(encrypted_key, encryption_key)
   ```

### Request Security

1. **HTTPS Only**:
   - All API requests must use HTTPS
   - Certificate validation is enforced
   - HTTP requests are rejected

2. **Request Signing**:
   ```python
   # request_signing.py
   import hmac
   import hashlib
   import time
   
   def sign_request(api_key, method, endpoint, payload, timestamp):
       """Sign API request for security"""
       # Create canonical request string
       canonical_string = f"{method}\n{endpoint}\n{payload}\n{timestamp}"
       
       # Create signature
       signature = hmac.new(
           api_key.encode(),
           canonical_string.encode(),
           hashlib.sha256
       ).hexdigest()
       
       return signature
   
   def make_signed_request(api_key, method, endpoint, payload):
       """Make signed API request"""
       timestamp = str(int(time.time()))
       signature = sign_request(api_key, method, endpoint, payload, timestamp)
       
       headers = {
           'X-API-Signature': signature,
           'X-API-Timestamp': timestamp,
           'Authorization': f'Bearer {api_key}'
       }
       
       # Make request with headers
       return requests.request(method, endpoint, json=payload, headers=headers)
   ```

## Rate Limiting

### Rate Limits

#### License System Limits

| Endpoint | Rate Limit | Time Window |
|-----------|-------------|--------------|
| /licenses/validate | 100 requests | 1 hour |
| /licenses/activate | 10 requests | 1 hour |
| /licenses/deactivate | 5 requests | 1 hour |
| /licenses/transfer | 3 requests | 1 hour |

#### Support System Limits

| Endpoint | Rate Limit | Time Window |
|-----------|-------------|--------------|
| /support/tickets | 50 requests | 1 hour |
| /support/tickets/{id}/messages | 100 requests | 1 hour |
| /support/contact | 20 requests | 1 hour |
| /support/bugs | 10 requests | 1 hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

### Handling Rate Limits

```python
# rate_limiting.py
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RateLimitHandler:
    """Handle API rate limits gracefully"""
    
    def __init__(self):
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 503]
        )
        
        self.session = requests.Session()
        self.session.mount('https://', HTTPAdapter(max_retries=self.retry_strategy))
    
    def make_request_with_retry(self, method, url, **kwargs):
        """Make request with automatic retry on rate limit"""
        while True:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 429:
                # Get rate limit reset time
                reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 60))
                wait_time = max(0, reset_time - time.time())
                
                if wait_time > 0:
                    print(f"Rate limit reached. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
            
            return response
```

---

This API reference provides comprehensive information for developers integrating with the support system and license validation system. For additional assistance, consult our developer documentation or contact our developer support team.