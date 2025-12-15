# API Documentation - Enhanced Flask POS Application

## 📋 Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Security API](#security-api)
4. [Session Management API](#session-management-api)
5. [Offline Sync API](#offline-sync-api)
6. [Payment API](#payment-api)
7. [Form Validation API](#form-validation-api)
8. [CRM API](#crm-api)
9. [Loyalty Program API](#loyalty-program-api)
10. [Multi-Tenancy API](#multi-tenancy-api)
11. [Core POS API](#core-pos-api)
12. [Reports API](#reports-api)
13. [Inventory API](#inventory-api)
14. [Tables Management API](#tables-management-api)
15. [KOT (Kitchen Order Ticket) API](#kot-kitchen-order-ticket-api)
16. [Email Notifications API](#email-notifications-api)
17. [Error Handling](#error-handling)
18. [Rate Limiting](#rate-limiting)
19. [Webhooks](#webhooks)
20. [API Best Practices](#api-best-practices)

---

## API Overview

### Base URL

```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

### API Versioning

```
Current Version: v2.0
Version Format: /api/v2/{endpoint}
Backward Compatibility: v1.0 deprecated
```

### Authentication Methods

1. **Session-based Authentication**: Use existing user session
2. **JWT Token Authentication**: Bearer token for API access
3. **API Key Authentication**: For third-party integrations

### Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "timestamp": "2024-12-14T11:30:00Z",
  "request_id": "req_123456789",
  "version": "2.0"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  },
  "timestamp": "2024-12-14T11:30:00Z",
  "request_id": "req_123456789"
}
```

---

## Authentication

### Login

Authenticate user and create session.

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123",
  "remember_me": false,
  "tenant_id": "tenant_001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user_001",
    "username": "admin",
    "role": "administrator",
    "tenant_id": "tenant_001",
    "session_id": "sess_123456789",
    "expires_at": "2024-12-14T19:30:00Z",
    "permissions": ["read", "write", "admin"]
  },
  "message": "Login successful"
}
```

### Logout

End user session.

```http
POST /api/auth/logout
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### Refresh Token

Refresh authentication token.

```http
POST /api/auth/refresh
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "new_jwt_token",
    "expires_at": "2024-12-14T19:30:00Z"
  },
  "message": "Token refreshed"
}
```

### Check Authentication Status

Verify current authentication status.

```http
GET /api/auth/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "authenticated": true,
    "user_id": "user_001",
    "session_valid": true,
    "expires_at": "2024-12-14T19:30:00Z",
    "tenant_id": "tenant_001"
  }
}
```

---

## Security API

### Get Security Status

Retrieve current security status and events.

```http
GET /api/security/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "security_level": "high",
    "active_threats": 0,
    "blocked_ips": 3,
    "failed_attempts": 5,
    "last_security_scan": "2024-12-14T11:00:00Z",
    "security_events": [
      {
        "id": "sec_001",
        "type": "failed_login",
        "severity": "medium",
        "ip_address": "192.168.1.100",
        "timestamp": "2024-12-14T11:15:00Z",
        "details": "Failed login attempt for user admin"
      }
    ]
  }
}
```

### Get Blocked IPs

Retrieve list of blocked IP addresses.

```http
GET /api/security/blocked-ips
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "blocked_ips": [
      {
        "ip_address": "192.168.1.100",
        "reason": "Multiple failed login attempts",
        "blocked_at": "2024-12-14T11:00:00Z",
        "expires_at": "2024-12-14T11:30:00Z",
        "severity": "medium"
      }
    ],
    "total_blocked": 1
  }
}
```

### Unblock IP Address

Remove IP from blocked list.

```http
POST /api/security/unblock-ip
Authorization: Bearer {token}
Content-Type: application/json

{
  "ip_address": "192.168.1.100",
  "reason": "Manual unblock"
}
```

**Response:**
```json
{
  "success": true,
  "message": "IP address unblocked successfully"
}
```

### Get Security Audit Log

Retrieve security audit log entries.

```http
GET /api/security/audit-log
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- severity: high|medium|low
- event_type: login|payment|data_access
- limit: 100
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "audit_log": [
      {
        "id": "audit_001",
        "user_id": "user_001",
        "action": "login",
        "resource": "/api/auth/login",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "timestamp": "2024-12-14T11:30:00Z",
        "success": true,
        "details": "User login successful"
      }
    ],
    "total_entries": 150,
    "page": 1,
    "per_page": 100
  }
}
```

### Report Suspicious Activity

Report suspicious activity for security review.

```http
POST /api/security/report-activity
Authorization: Bearer {token}
Content-Type: application/json

{
  "activity_type": "suspicious_login",
  "description": "Multiple failed login attempts from unknown IP",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "severity": "high",
  "evidence": {
    "attempts": 10,
    "timeframe": "5 minutes",
    "usernames": ["admin", "root", "test"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Suspicious activity reported successfully",
  "data": {
    "report_id": "report_001",
    "status": "under_review"
  }
}
```

---

## Session Management API

### Get Active Sessions

Retrieve all active sessions for current user.

```http
GET /api/session/active
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "sess_001",
        "device_type": "desktop",
        "browser": "Chrome",
        "os": "Windows",
        "ip_address": "192.168.1.100",
        "location": "Mumbai, India",
        "created_at": "2024-12-14T09:30:00Z",
        "last_activity": "2024-12-14T11:15:00Z",
        "is_current": true,
        "fingerprint": "fp_123456789"
      }
    ],
    "total_sessions": 1
  }
}
```

### Create New Session

Create new session for additional device.

```http
POST /api/session/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "device_name": "Mobile App",
  "device_type": "mobile",
  "user_agent": "MobileApp/1.0"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_002",
    "device_name": "Mobile App",
    "created_at": "2024-12-14T11:30:00Z",
    "expires_at": "2024-12-14T19:30:00Z"
  },
  "message": "New session created successfully"
}
```

### Terminate Session

End specific session.

```http
DELETE /api/session/{session_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "message": "Session terminated successfully"
}
```

### Terminate All Sessions

End all sessions except current.

```http
DELETE /api/session/all
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "terminated_sessions": 2
  },
  "message": "All other sessions terminated successfully"
}
```

### Extend Session

Extend session expiration time.

```http
POST /api/session/{session_id}/extend
Authorization: Bearer {token}
Content-Type: application/json

{
  "extension_hours": 8
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_001",
    "new_expires_at": "2024-12-15T03:30:00Z"
  },
  "message": "Session extended successfully"
}
```

### Get Session Analytics

Retrieve session analytics and insights.

```http
GET /api/session/analytics
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- group_by: day|week|month
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "total_sessions": 45,
      "average_duration": "2h 30m",
      "peak_hours": ["12:00", "19:00"],
      "devices": {
        "desktop": 60,
        "mobile": 30,
        "tablet": 10
      },
      "locations": [
        {
          "city": "Mumbai",
          "sessions": 25,
          "percentage": 55.6
        }
      ]
    }
  }
}
```

---

## Offline Sync API

### Get Sync Status

Retrieve current synchronization status.

```http
GET /api/offline/status
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sync_status": "online",
    "last_sync": "2024-12-14T11:25:00Z",
    "next_sync": "2024-12-14T11:30:00Z",
    "pending_operations": {
      "orders": 5,
      "payments": 3,
      "customers": 1,
      "inventory": 2
    },
    "sync_queue": [
      {
        "id": "sync_001",
        "type": "order",
        "operation": "create",
        "status": "pending",
        "created_at": "2024-12-14T11:20:00Z",
        "retry_count": 0
      }
    ],
    "conflicts": []
  }
}
```

### Manual Sync

Trigger manual synchronization.

```http
POST /api/offline/sync
Authorization: Bearer {token}
Content-Type: application/json

{
  "sync_types": ["orders", "payments", "customers"],
  "force_conflict_resolution": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sync_id": "sync_manual_001",
    "status": "started",
    "estimated_duration": "2 minutes"
  },
  "message": "Manual sync started"
}
```

### Get Sync Queue

Retrieve current sync queue status.

```http
GET /api/offline/queue
Authorization: Bearer {token}
Query Parameters:
- status: pending|processing|completed|failed
- type: order|payment|customer|inventory
- limit: 50
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "queue": [
      {
        "id": "queue_001",
        "type": "order",
        "operation": "create",
        "data": {
          "order_id": "ORD001",
          "amount": 1200.00
        },
        "status": "pending",
        "priority": "high",
        "created_at": "2024-12-14T11:20:00Z",
        "retry_count": 0,
        "max_retries": 3
      }
    ],
    "total_items": 11,
    "processing": 1,
    "pending": 8,
    "failed": 2
  }
}
```

### Clear Sync Queue

Clear items from sync queue.

```http
DELETE /api/offline/queue
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "failed",
  "older_than": "2024-12-13T00:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cleared_items": 5
  },
  "message": "Sync queue cleared successfully"
}
```

### Resolve Conflicts

Resolve data synchronization conflicts.

```http
POST /api/offline/resolve-conflict
Authorization: Bearer {token}
Content-Type: application/json

{
  "conflict_id": "conflict_001",
  "resolution": "use_online",
  "manual_data": {}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Conflict resolved successfully",
  "data": {
    "conflict_id": "conflict_001",
    "resolution_applied": "use_online"
  }
}
```

### Get Offline Data

Retrieve locally stored offline data.

```http
GET /api/offline/data
Authorization: Bearer {token}
Query Parameters:
- data_type: orders|customers|menu|settings
- limit: 100
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "offline_orders": [
      {
        "order_id": "ORD_OFFLINE_001",
        "customer_id": "CUST_001",
        "amount": 850.00,
        "status": "pending_sync",
        "created_at": "2024-12-14T11:00:00Z",
        "items": []
      }
    ],
    "total_count": 5
  }
}
```

---

## Payment API

### Create Payment Order

Create new payment order with Razorpay.

```http
POST /api/payment/create-order
Authorization: Bearer {token}
Content-Type: application/json

{
  "order_id": "ORD20241214001",
  "amount": 120000,  // in paise (₹1200.00)
  "currency": "INR",
  "receipt": "receipt_001",
  "payment_capture": true,
  "notes": {
    "customer_name": "John Doe",
    "table_number": "T-05"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "razorpay_order_id": "order_1234567890",
    "order_id": "ORD20241214001",
    "amount": 120000,
    "currency": "INR",
    "receipt": "receipt_001",
    "status": "created",
    "created_at": 1643123456,
    "notes": {
      "customer_name": "John Doe",
      "table_number": "T-05"
    }
  },
  "message": "Payment order created successfully"
}
```

### Capture Payment

Capture payment after successful authorization.

```http
POST /api/payment/capture
Authorization: Bearer {token}
Content-Type: application/json

{
  "razorpay_payment_id": "pay_1234567890",
  "razorpay_order_id": "order_1234567890",
  "razorpay_signature": "signature_hash",
  "amount": 120000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payment_id": "pay_1234567890",
    "order_id": "ORD20241214001",
    "amount": 120000,
    "currency": "INR",
    "status": "captured",
    "method": "card",
    "card": {
      "last4": "1234",
      "network": "Visa",
      "type": "credit"
    },
    "captured_at": 1643123456
  },
  "message": "Payment captured successfully"
}
```

### Process Refund

Process refund for captured payment.

```http
POST /api/payment/refund
Authorization: Bearer {token}
Content-Type: application/json

{
  "payment_id": "pay_1234567890",
  "amount": 50000,  // in paise (₹500.00)
  "reason": "requested_by_customer",
  "notes": {
    "reason": "Customer requested refund",
    "processed_by": "staff_001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "refund_id": "rfnd_1234567890",
    "payment_id": "pay_1234567890",
    "amount": 50000,
    "currency": "INR",
    "status": "processed",
    "created_at": 1643123456,
    "batch_id": null,
    "notes": {
      "reason": "Customer requested refund",
      "processed_by": "staff_001"
    }
  },
  "message": "Refund processed successfully"
}
```

### Get Payment Details

Retrieve payment information.

```http
GET /api/payment/{payment_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payment_id": "pay_1234567890",
    "order_id": "ORD20241214001",
    "amount": 120000,
    "currency": "INR",
    "status": "captured",
    "method": "card",
    "email": "customer@example.com",
    "contact": "+919876543210",
    "created_at": 1643123456,
    "captured_at": 1643123456,
    "card": {
      "last4": "1234",
      "network": "Visa",
      "type": "credit",
      "name": "John Doe"
    }
  }
}
```

### Get Payment Analytics

Retrieve payment analytics and insights.

```http
GET /api/payment/analytics
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- group_by: day|week|month
- method: card|upi|netbanking|wallet
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "total_amount": 2500000,
      "total_transactions": 245,
      "average_amount": 10204,
      "success_rate": 98.5,
      "methods": {
        "card": {
          "count": 150,
          "amount": 1500000,
          "percentage": 60.0
        },
        "upi": {
          "count": 80,
          "amount": 800000,
          "percentage": 32.0
        },
        "netbanking": {
          "count": 15,
          "amount": 200000,
          "percentage": 8.0
        }
      },
      "daily_breakdown": [
        {
          "date": "2024-12-14",
          "transactions": 25,
          "amount": 250000,
          "success_rate": 100.0
        }
      ]
    }
  }
}
```

### Get Payment Methods

Retrieve available payment methods.

```http
GET /api/payment/methods
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "methods": [
      {
        "type": "card",
        "name": "Credit/Debit Card",
        "enabled": true,
        "supported_networks": ["Visa", "Mastercard", "Rupay", "Amex"],
        "min_amount": 100,
        "max_amount": 10000000
      },
      {
        "type": "upi",
        "name": "UPI",
        "enabled": true,
        "supported_apps": ["gpay", "phonepe", "paytm", "bhim"],
        "min_amount": 100,
        "max_amount": 10000000
      },
      {
        "type": "netbanking",
        "name": "Net Banking",
        "enabled": true,
        "supported_banks": ["HDFC", "ICICI", "SBI", "PNB"],
        "min_amount": 100,
        "max_amount": 10000000
      }
    ]
  }
}
```

---

## Form Validation API

### Validate Field

Validate single field value.

```http
POST /api/validation/field
Authorization: Bearer {token}
Content-Type: application/json

{
  "field_name": "email",
  "field_value": "user@example.com",
  "validation_rules": ["required", "email", "unique"],
  "context": {
    "table": "customers",
    "exclude_id": "cust_001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "sanitized_value": "user@example.com",
    "validation_results": {
      "required": {
        "passed": true,
        "message": "Field is required"
      },
      "email": {
        "passed": true,
        "message": "Valid email format"
      },
      "unique": {
        "passed": true,
        "message": "Email is unique"
      }
    }
  }
}
```

### Validate Form

Validate entire form data.

```http
POST /api/validation/form
Authorization: Bearer {token}
Content-Type: application/json

{
  "form_name": "customer_registration",
  "form_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+919876543210",
    "gst_number": "27AAAPL1234C1ZV",
    "address": "123 Main St, Mumbai"
  },
  "validation_rules": "customer_rules"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "is_valid": false,
    "errors": [
      {
        "field": "phone",
        "message": "Phone number is required",
        "code": "REQUIRED_FIELD"
      }
    ],
    "warnings": [
      {
        "field": "gst_number",
        "message": "GST number format may be invalid",
        "code": "FORMAT_WARNING"
      }
    ],
    "sanitized_data": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+919876543210",
      "gst_number": "27AAAPL1234C1ZV",
      "address": "123 Main St, Mumbai"
    },
    "field_results": {
      "name": {
        "valid": true,
        "errors": []
      },
      "email": {
        "valid": true,
        "errors": []
      },
      "phone": {
        "valid": false,
        "errors": ["Phone number is required"]
      }
    }
  }
}
```

### Get Validation Rules

Retrieve validation rules for form.

```http
GET /api/validation/rules/{form_name}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "form_name": "customer_registration",
    "rules": {
      "name": {
        "required": true,
        "min_length": 2,
        "max_length": 100,
        "pattern": "^[a-zA-Z\\s]+$",
        "sanitization": "trim,escape"
      },
      "email": {
        "required": true,
        "format": "email",
        "unique": "customers.email",
        "sanitization": "lowercase,trim"
      },
      "phone": {
        "required": true,
        "format": "phone_international",
        "min_length": 10,
        "max_length": 15,
        "sanitization": "digits_only"
      },
      "gst_number": {
        "required": false,
        "format": "gstin",
        "length": 15,
        "sanitization": "uppercase,trim"
      }
    }
  }
}
```

### Custom Validation

Perform custom validation logic.

```http
POST /api/validation/custom
Authorization: Bearer {token}
Content-Type: application/json

{
  "validation_type": "business_logic",
  "data": {
    "order_amount": 1200.00,
    "customer_discount": 150.00,
    "loyalty_points": 1000
  },
  "rules": {
    "max_discount_percentage": 15,
    "min_order_amount": 100.00,
    "max_points_redemption": 500
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      {
        "rule": "discount_percentage",
        "message": "Discount is close to maximum allowed",
        "severity": "warning"
      }
    ],
    "calculated_values": {
      "discount_percentage": 12.5,
      "points_value": 100.00,
      "final_amount": 950.00
    }
  }
}
```

---

## CRM API

### Get Customers

Retrieve customer list with filtering and pagination.

```http
GET /api/crm/customers
Authorization: Bearer {token}
Query Parameters:
- search: John
- status: active|inactive|vip
- loyalty_tier: bronze|silver|gold|platinum
- created_from: 2024-12-01
- created_to: 2024-12-31
- limit: 50
- offset: 0
- sort_by: name|created_at|total_orders
- sort_order: asc|desc
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customers": [
      {
        "id": "cust_001",
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+919876543210",
        "address": "123 Main St, Mumbai",
        "birthday": "1990-01-15",
        "anniversary": "2020-06-20",
        "loyalty_tier": "gold",
        "loyalty_points": 2450,
        "total_orders": 47,
        "total_spent": 39850.00,
        "average_order": 847.87,
        "last_visit": "2024-12-14",
        "status": "active",
        "preferences": {
          "dietary": ["vegetarian"],
          "allergies": ["nuts"],
          "favorite_items": ["burger", "pizza"]
        },
        "created_at": "2020-01-15T10:30:00Z",
        "updated_at": "2024-12-14T11:00:00Z"
      }
    ],
    "total_customers": 150,
    "page": 1,
    "per_page": 50,
    "total_pages": 3
  }
}
```

### Create Customer

Create new customer record.

```http
POST /api/crm/customers
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+919876543211",
  "address": "456 Oak Ave, Mumbai",
  "birthday": "1985-05-22",
  "anniversary": "2015-11-10",
  "preferences": {
    "dietary": ["vegan"],
    "allergies": ["dairy"],
    "favorite_items": ["salad", "smoothie"]
  },
  "notes": "Prefers window seating"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cust_002",
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "+919876543211",
    "loyalty_tier": "bronze",
    "loyalty_points": 0,
    "created_at": "2024-12-14T11:30:00Z"
  },
  "message": "Customer created successfully"
}
```

### Get Customer Details

Retrieve detailed customer information.

```http
GET /api/crm/customers/{customer_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cust_001",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+919876543210",
    "address": "123 Main St, Mumbai",
    "birthday": "1990-01-15",
    "anniversary": "2020-06-20",
    "loyalty_tier": "gold",
    "loyalty_points": 2450,
    "total_orders": 47,
    "total_spent": 39850.00,
    "average_order": 847.87,
    "last_visit": "2024-12-14",
    "status": "active",
    "preferences": {
      "dietary": ["vegetarian"],
      "allergies": ["nuts"],
      "favorite_items": ["burger", "pizza"]
    },
    "order_history": [
      {
        "order_id": "ORD20241214001",
        "date": "2024-12-14",
        "amount": 1200.00,
        "items": ["Burger", "Fries", "Coke"],
        "status": "completed"
      }
    ],
    "communication_history": [
      {
        "type": "email",
        "date": "2024-12-10",
        "subject": "Special Birthday Offer",
        "status": "sent"
      }
    ],
    "notes": [
      {
        "id": "note_001",
        "content": "Prefers window seating",
        "created_by": "staff_001",
        "created_at": "2024-12-01T10:00:00Z"
      }
    ],
    "created_at": "2020-01-15T10:30:00Z",
    "updated_at": "2024-12-14T11:00:00Z"
  }
}
```

### Update Customer

Update customer information.

```http
PUT /api/crm/customers/{customer_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "John Doe Jr.",
  "phone": "+919876543212",
  "preferences": {
    "dietary": ["vegetarian", "gluten-free"],
    "allergies": ["nuts", "dairy"],
    "favorite_items": ["burger", "pizza", "salad"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "cust_001",
    "updated_fields": ["name", "phone", "preferences"],
    "updated_at": "2024-12-14T11:35:00Z"
  },
  "message": "Customer updated successfully"
}
```

### Get Customer Analytics

Retrieve customer analytics and insights.

```http
GET /api/crm/analytics
Authorization: Bearer {token}
Query Parameters:
- customer_id: cust_001
- start_date: 2024-12-01
- end_date: 2024-12-31
- analytics_type: behavior|spending|frequency|loyalty
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customer_analytics": {
      "behavior_patterns": {
        "peak_visiting_hours": ["12:00", "19:00"],
        "preferred_days": ["Saturday", "Sunday"],
        "average_stay_duration": "45 minutes",
        "table_preference": "window"
      },
      "spending_analysis": {
        "total_spent": 39850.00,
        "average_order": 847.87,
        "highest_order": 2500.00,
        "lowest_order": 350.00,
        "spending_trend": "increasing",
        "category_breakdown": {
          "appetizers": 15.5,
          "main_course": 65.2,
          "desserts": 12.3,
          "beverages": 7.0
        }
      },
      "frequency_metrics": {
        "visit_frequency": "twice_week",
        "days_since_last_visit": 2,
        "churn_risk": "low",
        "loyalty_score": 85
      },
      "loyalty_engagement": {
        "points_earned": 3985,
        "points_redeemed": 1535,
        "redemption_rate": 38.5,
        "tier_progression": {
          "current_tier": "gold",
          "points_to_next_tier": 2550,
          "estimated_upgrade": "3 months"
        }
      }
    }
  }
}
```

---

## Loyalty Program API

### Get Loyalty Points

Retrieve customer loyalty points balance.

```http
GET /api/loyalty/points/{customer_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": "cust_001",
    "current_balance": 2450,
    "tier": "gold",
    "points_history": [
      {
        "id": "points_001",
        "type": "earned",
        "amount": 120,
        "order_id": "ORD20241214001",
        "description": "Points earned from order",
        "created_at": "2024-12-14T11:30:00Z"
      },
      {
        "id": "points_002",
        "type": "redeemed",
        "amount": -200,
        "description": "Redeemed for discount",
        "created_at": "2024-12-13T15:20:00Z"
      }
    ],
    "tier_benefits": {
      "points_per_rupee": 1.5,
      "discount_percentage": 15,
      "birthday_bonus": 500,
      "exclusive_offers": true
    }
  }
}
```

### Earn Points

Add loyalty points to customer account.

```http
POST /api/loyalty/earn
Authorization: Bearer {token}
Content-Type: application/json

{
  "customer_id": "cust_001",
  "order_id": "ORD20241214001",
  "amount": 1200.00,
  "points": 120,
  "type": "purchase",
  "multiplier": 1.0,
  "bonus_reason": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transaction_id": "loyalty_001",
    "customer_id": "cust_001",
    "points_earned": 120,
    "new_balance": 2570,
    "tier": "gold",
    "transaction_date": "2024-12-14T11:30:00Z"
  },
  "message": "Loyalty points earned successfully"
}
```

### Redeem Points

Redeem loyalty points for rewards.

```http
POST /api/loyalty/redeem
Authorization: Bearer {token}
Content-Type: application/json

{
  "customer_id": "cust_001",
  "order_id": "ORD20241214002",
  "points_to_redeem": 200,
  "reward_type": "discount",
  "reward_value": 200.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transaction_id": "loyalty_002",
    "customer_id": "cust_001",
    "points_redeemed": 200,
    "discount_amount": 200.00,
    "new_balance": 2370,
    "transaction_date": "2024-12-14T12:00:00Z"
  },
  "message": "Points redeemed successfully"
}
```

### Get Loyalty Tiers

Retrieve loyalty tier information.

```http
GET /api/loyalty/tiers
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tiers": [
      {
        "name": "bronze",
        "min_points": 0,
        "max_points": 999,
        "benefits": {
          "points_per_rupee": 1.0,
          "discount_percentage": 5,
          "birthday_bonus": 100,
          "exclusive_offers": false
        },
        "color": "#CD7F32"
      },
      {
        "name": "silver",
        "min_points": 1000,
        "max_points": 4999,
        "benefits": {
          "points_per_rupee": 1.2,
          "discount_percentage": 10,
          "birthday_bonus": 250,
          "exclusive_offers": true
        },
        "color": "#C0C0C0"
      },
      {
        "name": "gold",
        "min_points": 5000,
        "max_points": 9999,
        "benefits": {
          "points_per_rupee": 1.5,
          "discount_percentage": 15,
          "birthday_bonus": 500,
          "exclusive_offers": true
        },
        "color": "#FFD700"
      },
      {
        "name": "platinum",
        "min_points": 10000,
        "max_points": null,
        "benefits": {
          "points_per_rupee": 2.0,
          "discount_percentage": 20,
          "birthday_bonus": 1000,
          "exclusive_offers": true
        },
        "color": "#E5E4E2"
      }
    ]
  }
}
```

### Process Referral

Process customer referral and award points.

```http
POST /api/loyalty/referral
Authorization: Bearer {token}
Content-Type: application/json

{
  "referrer_id": "cust_001",
  "referee_email": "newcustomer@example.com",
  "referee_name": "New Customer",
  "referral_code": "REF123456"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "referral_id": "ref_001",
    "referrer_id": "cust_001",
    "referee_id": "cust_002",
    "points_awarded": 500,
    "referral_bonus": 500,
    "status": "completed",
    "created_at": "2024-12-14T12:30:00Z"
  },
  "message": "Referral processed successfully"
}
```

### Get Loyalty Analytics

Retrieve loyalty program analytics.

```http
GET /api/loyalty/analytics
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- group_by: day|week|month
- analytics_type: engagement|redemption|tier_progression
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "engagement_metrics": {
        "total_members": 850,
        "active_members": 650,
        "engagement_rate": 76.5,
        "points_earned": 125000,
        "points_redeemed": 48000,
        "redemption_rate": 38.4
      },
      "tier_distribution": {
        "bronze": 425,
        "silver": 280,
        "gold": 120,
        "platinum": 25
      },
      "redemption_patterns": {
        "most_popular_rewards": ["discount", "free_item"],
        "average_redemption": 320,
        "peak_redemption_days": ["Friday", "Saturday"]
      },
      "referral_performance": {
        "total_referrals": 45,
        "conversion_rate": 65.5,
        "referral_points_awarded": 22500
      }
    }
  }
}
```

---

## Multi-Tenancy API

### Get Tenant Information

Retrieve current tenant information.

```http
GET /api/tenant/info
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tenant_id": "tenant_001",
    "tenant_name": "Restaurant A - Main Branch",
    "domain": "restaurant-a.example.com",
    "status": "active",
    "subscription": {
      "plan": "enterprise",
      "expires_at": "2025-12-31",
      "features": ["crm", "loyalty", "analytics", "multi_location"]
    },
    "branding": {
      "logo_url": "https://example.com/logo.png",
      "primary_color": "#FF6B6B",
      "secondary_color": "#4ECDC4",
      "theme": "modern"
    },
    "settings": {
      "timezone": "Asia/Kolkata",
      "currency": "INR",
      "tax_rate": 5.0,
      "gst_number": "27AAAPL1234C1ZV"
    },
    "usage": {
      "users": 15,
      "storage_used": "2.5 GB",
      "api_calls_today": 1250,
      "orders_this_month": 850
    }
  }
}
```

### Switch Tenant

Switch to different tenant (for users with multiple tenant access).

```http
POST /api/tenant/switch
Authorization: Bearer {token}
Content-Type: application/json

{
  "tenant_id": "tenant_002",
  "reason": "Managing branch operations"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "previous_tenant": "tenant_001",
    "current_tenant": "tenant_002",
    "session_id": "sess_tenant_002",
    "switched_at": "2024-12-14T12:45:00Z"
  },
  "message": "Tenant switched successfully"
}
```

### Get Tenant Users

Retrieve users for current tenant.

```http
GET /api/tenant/users
Authorization: Bearer {token}
Query Parameters:
- role: admin|manager|staff|cashier
- status: active|inactive|suspended
- limit: 50
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "user_id": "user_001",
        "username": "admin",
        "email": "admin@restaurant.com",
        "role": "administrator",
        "permissions": ["read", "write", "admin", "manage_users"],
        "status": "active",
        "last_login": "2024-12-14T11:30:00Z",
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total_users": 15,
    "active_users": 12,
    "inactive_users": 3
  }
}
```

### Create Tenant User

Create new user for current tenant.

```http
POST /api/tenant/users
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "new_user",
  "email": "newuser@restaurant.com",
  "password": "SecurePassword123!",
  "role": "staff",
  "permissions": ["read", "write"],
  "profile": {
    "first_name": "New",
    "last_name": "User",
    "phone": "+919876543210"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": "user_016",
    "username": "new_user",
    "email": "newuser@restaurant.com",
    "role": "staff",
    "status": "active",
    "created_at": "2024-12-14T12:50:00Z"
  },
  "message": "User created successfully"
}
```

### Get Tenant Analytics

Retrieve tenant-specific analytics.

```http
GET /api/tenant/analytics
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- metrics: sales|users|performance|storage
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analytics": {
      "sales_metrics": {
        "total_revenue": 2500000,
        "total_orders": 2450,
        "average_order_value": 1020.41,
        "growth_rate": 15.5
      },
      "user_metrics": {
        "total_users": 15,
        "active_users": 12,
        "user_satisfaction": 4.5,
        "support_tickets": 8
      },
      "performance_metrics": {
        "api_response_time": "120ms",
        "uptime": "99.9%",
        "error_rate": "0.1%",
        "storage_usage": "2.5 GB"
      },
      "resource_usage": {
        "cpu_usage": "45%",
        "memory_usage": "60%",
        "database_size": "1.8 GB",
        "bandwidth_usage": "125 GB"
      }
    }
  }
}
```

---

## Core POS API

### Get Orders

Retrieve orders with filtering and pagination.

```http
GET /api/orders
Authorization: Bearer {token}
Query Parameters:
- status: pending|preparing|ready|completed|cancelled
- table_id: T-05
- customer_id: cust_001
- start_date: 2024-12-01
- end_date: 2024-12-31
- limit: 50
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "id": "ORD20241214001",
        "customer_id": "cust_001",
        "table_id": "T-05",
        "status": "completed",
        "subtotal": 1142.86,
        "tax": 57.14,
        "total": 1200.00,
        "payment_status": "paid",
        "payment_method": "card",
        "items": [
          {
            "menu_item_id": "menu_001",
            "name": "Burger",
            "quantity": 2,
            "price": 300.00,
            "total": 600.00
          }
        ],
        "created_at": "2024-12-14T11:30:00Z",
        "updated_at": "2024-12-14T12:00:00Z"
      }
    ],
    "total_orders": 100,
    "page": 1,
    "per_page": 50
  }
}
```

### Create Order

Create new order.

```http
POST /api/orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "customer_id": "cust_001",
  "table_id": "T-05",
  "order_type": "dine_in",
  "items": [
    {
      "menu_item_id": "menu_001",
      "quantity": 2,
      "special_instructions": "Extra cheese"
    }
  ],
  "discount": {
    "type": "percentage",
    "value": 10,
    "reason": "Loyalty discount"
  },
  "notes": "Customer prefers window seating"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "order_id": "ORD20241214002",
    "customer_id": "cust_001",
    "table_id": "T-05",
    "status": "pending",
    "subtotal": 600.00,
    "tax": 30.00,
    "discount": 60.00,
    "total": 570.00,
    "created_at": "2024-12-14T13:00:00Z"
  },
  "message": "Order created successfully"
}
```

### Get Menu Items

Retrieve menu items with categories.

```http
GET /api/menu/items
Authorization: Bearer {token}
Query Parameters:
- category: appetizers|main_course|desserts|beverages
- available: true|false
- search: burger
- limit: 100
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "id": "cat_001",
        "name": "Main Course",
        "description": "Main course items",
        "items": [
          {
            "id": "menu_001",
            "name": "Classic Burger",
            "description": "Juicy beef patty with fresh vegetables",
            "price": 300.00,
            "category_id": "cat_001",
            "available": true,
            "image_url": "https://example.com/burger.jpg",
            "ingredients": ["beef", "lettuce", "tomato", "onion"],
            "allergens": ["gluten", "dairy"],
            "preparation_time": 15,
            "calories": 650
          }
        ]
      }
    ],
    "total_items": 50
  }
}
```

---

## Reports API

### Get Sales Report

Generate comprehensive sales report.

```http
GET /api/reports/sales
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- group_by: day|week|month|category|item
- format: json|csv|pdf
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "sales_2024_12",
    "period": {
      "start_date": "2024-12-01",
      "end_date": "2024-12-31"
    },
    "summary": {
      "total_revenue": 2500000,
      "total_orders": 2450,
      "average_order_value": 1020.41,
      "total_customers": 1250,
      "growth_rate": 15.5
    },
    "breakdown": {
      "daily": [
        {
          "date": "2024-12-14",
          "revenue": 85000,
          "orders": 85,
          "customers": 75
        }
      ],
      "category": [
        {
          "category": "Main Course",
          "revenue": 1500000,
          "orders": 1200,
          "percentage": 60.0
        }
      ],
      "payment_methods": [
        {
          "method": "card",
          "revenue": 1500000,
          "orders": 1470,
          "percentage": 60.0
        }
      ]
    }
  }
}
```

### Get Inventory Report

Generate inventory usage and valuation report.

```http
GET /api/reports/inventory
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- category: all|vegetables|meat|beverages
- report_type: usage|valuation|wastage
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "inventory_2024_12",
    "period": {
      "start_date": "2024-12-01",
      "end_date": "2024-12-31"
    },
    "summary": {
      "total_items": 150,
      "total_value": 450000,
      "usage_rate": 78.5,
      "wastage_percentage": 3.2
    },
    "items": [
      {
        "item_id": "inv_001",
        "name": "Tomatoes",
        "category": "vegetables",
        "opening_stock": 100,
        "purchases": 50,
        "usage": 120,
        "closing_stock": 30,
        "unit_cost": 20.00,
        "total_value": 600.00,
        "wastage": 5,
        "wastage_percentage": 4.2
      }
    ]
  }
}
```

### Get Customer Analytics Report

Generate customer behavior and analytics report.

```http
GET /api/reports/customers
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- segment: all|new|returning|vip
- metrics: behavior|spending|frequency|retention
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "customers_2024_12",
    "period": {
      "start_date": "2024-12-01",
      "end_date": "2024-12-31"
    },
    "summary": {
      "total_customers": 1250,
      "new_customers": 150,
      "returning_customers": 1100,
      "retention_rate": 88.0,
      "average_lifetime_value": 12500
    },
    "segments": {
      "new": {
        "count": 150,
        "revenue": 225000,
        "average_order": 750.00
      },
      "returning": {
        "count": 1100,
        "revenue": 2275000,
        "average_order": 847.73
      },
      "vip": {
        "count": 85,
        "revenue": 425000,
        "average_order": 1250.00
      }
    }
  }
}
```

### Get Staff Performance Report

Generate staff performance and productivity report.

```http
GET /api/reports/staff
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- staff_id: user_001 (optional)
- role: all|cashier|manager|kitchen
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "staff_2024_12",
    "period": {
      "start_date": "2024-12-01",
      "end_date": "2024-12-31"
    },
    "summary": {
      "total_staff": 15,
      "average_hours": 168,
      "total_orders_processed": 2450,
      "average_efficiency": 92.5
    },
    "staff_members": [
      {
        "staff_id": "user_001",
        "name": "John Doe",
        "role": "cashier",
        "hours_worked": 168,
        "orders_processed": 325,
        "revenue_generated": 325000,
        "efficiency_score": 95.2,
        "customer_satisfaction": 4.7
      }
    ]
  }
}
```

---

## Inventory API

### Get Inventory Items

Retrieve inventory items with stock levels.

```http
GET /api/inventory/items
Authorization: Bearer {token}
Query Parameters:
- category: vegetables|meat|beverages|dairy
- low_stock: true|false
- search: tomato
- limit: 100
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "inv_001",
        "name": "Tomatoes",
        "category": "vegetables",
        "description": "Fresh red tomatoes",
        "unit": "kg",
        "current_stock": 25.5,
        "minimum_stock": 10.0,
        "maximum_stock": 50.0,
        "unit_cost": 20.00,
        "supplier": "Fresh Farm Supplies",
        "last_updated": "2024-12-14T10:30:00Z",
        "expiry_date": "2024-12-20",
        "status": "in_stock",
        "low_stock_alert": false
      }
    ],
    "total_items": 150,
    "low_stock_items": 8,
    "total_value": 450000
  }
}
```

### Update Inventory Stock

Update inventory stock levels.

```http
POST /api/inventory/update-stock
Authorization: Bearer {token}
Content-Type: application/json

{
  "item_id": "inv_001",
  "quantity": 15.5,
  "operation": "add|subtract|set",
  "reason": "Purchase from supplier",
  "reference": "PO_001",
  "cost_per_unit": 18.50
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "item_id": "inv_001",
    "previous_stock": 25.5,
    "new_stock": 41.0,
    "operation": "add",
    "quantity": 15.5,
    "updated_at": "2024-12-14T11:30:00Z"
  },
  "message": "Inventory stock updated successfully"
}
```

### Create Inventory Item

Add new inventory item.

```http
POST /api/inventory/items
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Onions",
  "category": "vegetables",
  "description": "Fresh white onions",
  "unit": "kg",
  "initial_stock": 20.0,
  "minimum_stock": 5.0,
  "maximum_stock": 40.0,
  "unit_cost": 15.00,
  "supplier": "Fresh Farm Supplies",
  "expiry_tracking": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "inv_151",
    "name": "Onions",
    "category": "vegetables",
    "current_stock": 20.0,
    "created_at": "2024-12-14T11:45:00Z"
  },
  "message": "Inventory item created successfully"
}
```

### Get Inventory Alerts

Retrieve inventory alerts and notifications.

```http
GET /api/inventory/alerts
Authorization: Bearer {token}
Query Parameters:
- alert_type: low_stock|expiry|wastage
- severity: high|medium|low
- resolved: true|false
```

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert_001",
        "item_id": "inv_045",
        "item_name": "Cheese",
        "alert_type": "low_stock",
        "severity": "high",
        "message": "Cheese stock below minimum level",
        "current_stock": 2.5,
        "minimum_stock": 5.0,
        "created_at": "2024-12-14T09:00:00Z",
        "resolved": false
      }
    ],
    "total_alerts": 12,
    "unresolved_alerts": 8,
    "high_priority_alerts": 3
  }
}
```

---

## Tables Management API

### Get Tables

Retrieve restaurant tables with status.

```http
GET /api/tables
Authorization: Bearer {token}
Query Parameters:
- status: available|occupied|reserved|maintenance
- section: indoor|outdoor|private
- capacity_min: 2
- capacity_max: 6
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tables": [
      {
        "id": "T-01",
        "name": "Table 1",
        "section": "indoor",
        "capacity": 4,
        "status": "available",
        "current_order": null,
        "reserved_until": null,
        "server": null,
        "created_at": "2024-01-01T00:00:00Z",
        "last_updated": "2024-12-14T11:30:00Z"
      },
      {
        "id": "T-05",
        "name": "Table 5",
        "section": "indoor",
        "capacity": 2,
        "status": "occupied",
        "current_order": "ORD20241214001",
        "server": "user_003",
        "occupied_since": "2024-12-14T12:00:00Z"
      }
    ],
    "total_tables": 20,
    "available_tables": 12,
    "occupied_tables": 6,
    "reserved_tables": 2
  }
}
```

### Update Table Status

Update table status and assign server.

```http
POST /api/tables/{table_id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "occupied",
  "order_id": "ORD20241214002",
  "server_id": "user_003",
  "guests": 3,
  "notes": "Customers prefer window seating"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "table_id": "T-01",
    "previous_status": "available",
    "new_status": "occupied",
    "order_id": "ORD20241214002",
    "server_id": "user_003",
    "updated_at": "2024-12-14T12:15:00Z"
  },
  "message": "Table status updated successfully"
}
```

### Reserve Table

Create table reservation.

```http
POST /api/tables/reserve
Authorization: Bearer {token}
Content-Type: application/json

{
  "table_id": "T-03",
  "customer_id": "cust_001",
  "customer_name": "John Doe",
  "customer_phone": "+919876543210",
  "reservation_time": "2024-12-14T19:00:00Z",
  "duration_hours": 2,
  "guests": 4,
  "special_requests": "Birthday celebration",
  "deposit_required": true,
  "deposit_amount": 500.00
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "reservation_id": "res_001",
    "table_id": "T-03",
    "customer_id": "cust_001",
    "reservation_time": "2024-12-14T19:00:00Z",
    "status": "confirmed",
    "deposit_paid": false,
    "created_at": "2024-12-14T12:30:00Z"
  },
  "message": "Table reservation created successfully"
}
```

### Get Table Layout

Retrieve restaurant table layout.

```http
GET /api/tables/layout
Authorization: Bearer {token}
Query Parameters:
- section: all|indoor|outdoor|private
```

**Response:**
```json
{
  "success": true,
  "data": {
    "layout": {
      "sections": [
        {
          "name": "indoor",
          "tables": [
            {
              "id": "T-01",
              "x": 100,
              "y": 150,
              "width": 80,
              "height": 80,
              "shape": "rectangle",
              "rotation": 0,
              "capacity": 4,
              "status": "available"
            }
          ]
        }
      ],
      "dimensions": {
        "width": 800,
        "height": 600
      }
    }
  }
}
```

---

## KOT (Kitchen Order Ticket) API

### Get KOT Orders

Retrieve active kitchen orders.

```http
GET /api/kot/orders
Authorization: Bearer {token}
Query Parameters:
- status: pending|preparing|ready|served
- station: grill|bar|kitchen
- priority: high|medium|low
- time_range: 30min|1hour|2hours
```

**Response:**
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "kot_id": "KOT20241214001",
        "order_id": "ORD20241214001",
        "table_id": "T-05",
        "customer_name": "John Doe",
        "status": "pending",
        "priority": "medium",
        "items": [
          {
            "menu_item_id": "menu_001",
            "name": "Classic Burger",
            "quantity": 2,
            "special_instructions": "Extra cheese, no onions",
            "station": "grill",
            "preparation_time": 15,
            "status": "pending"
          }
        ],
        "created_at": "2024-12-14T12:00:00Z",
        "estimated_ready_time": "2024-12-14T12:15:00Z"
      }
    ],
    "total_orders": 8,
    "pending_orders": 3,
    "preparing_orders": 4,
    "ready_orders": 1
  }
}
```

### Update KOT Status

Update kitchen order item status.

```http
POST /api/kot/{kot_id}/status
Authorization: Bearer {token}
Content-Type: application/json

{
  "item_id": "menu_001",
  "status": "preparing",
  "station": "grill",
  "estimated_time": 10,
  "notes": "Started preparation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "kot_id": "KOT20241214001",
    "item_id": "menu_001",
    "previous_status": "pending",
    "new_status": "preparing",
    "updated_at": "2024-12-14T12:05:00Z"
  },
  "message": "KOT status updated successfully"
}
```

### Mark KOT Ready

Mark kitchen order as ready for serving.

```http
POST /api/kot/{kot_id}/ready
Authorization: Bearer {token}
Content-Type: application/json

{
  "items": ["menu_001", "menu_003"],
  "notes": "Items ready for serving",
  "quality_check": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "kot_id": "KOT20241214001",
    "ready_items": 2,
    "remaining_items": 1,
    "ready_at": "2024-12-14T12:12:00Z"
  },
  "message": "KOT items marked as ready"
}
```

### Get KOT Summary

Get kitchen order summary and analytics.

```http
GET /api/kot/summary
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- station: all|grill|bar|kitchen
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "total_orders": 2450,
      "total_items": 7350,
      "average_preparation_time": "12 minutes",
      "on_time_delivery_rate": 94.5,
      "quality_score": 4.7
    },
    "station_performance": [
      {
        "station": "grill",
        "orders_processed": 850,
        "average_time": "15 minutes",
        "efficiency": 92.3
      }
    ],
    "popular_items": [
      {
        "menu_item_id": "menu_001",
        "name": "Classic Burger",
        "orders": 450,
        "percentage": 18.4
      }
    ]
  }
}
```

---

## Email Notifications API

### Get Email Templates

Retrieve available email templates.

```http
GET /api/email/templates
Authorization: Bearer {token}
Query Parameters:
- category: order|payment|loyalty|marketing
- active: true|false
```

**Response:**
```json
{
  "success": true,
  "data": {
    "templates": [
      {
        "id": "tpl_001",
        "name": "Order Confirmation",
        "category": "order",
        "subject": "Your Order {{order_id}} is Confirmed",
        "body": "Dear {{customer_name}}, your order has been confirmed...",
        "variables": ["order_id", "customer_name", "total_amount"],
        "active": true,
        "created_at": "2024-01-01T00:00:00Z"
      }
    ],
    "total_templates": 15,
    "active_templates": 12
  }
}
```

### Send Email

Send transactional email.

```http
POST /api/email/send
Authorization: Bearer {token}
Content-Type: application/json

{
  "template_id": "tpl_001",
  "to": "customer@example.com",
  "cc": ["manager@restaurant.com"],
  "variables": {
    "order_id": "ORD20241214001",
    "customer_name": "John Doe",
    "total_amount": "1200.00"
  },
  "attachments": [
    {
      "name": "order_receipt.pdf",
      "content": "base64_encoded_content",
      "type": "application/pdf"
    }
  ],
  "send_immediately": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "email_id": "email_001",
    "template_id": "tpl_001",
    "to": "customer@example.com",
    "status": "sent",
    "sent_at": "2024-12-14T12:30:00Z",
    "delivery_status": "delivered"
  },
  "message": "Email sent successfully"
}
```

### Get Email History

Retrieve email sending history.

```http
GET /api/email/history
Authorization: Bearer {token}
Query Parameters:
- start_date: 2024-12-01
- end_date: 2024-12-31
- status: sent|delivered|failed|bounced
- template_id: tpl_001
- limit: 50
- offset: 0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "emails": [
      {
        "id": "email_001",
        "template_id": "tpl_001",
        "to": "customer@example.com",
        "subject": "Your Order ORD20241214001 is Confirmed",
        "status": "delivered",
        "sent_at": "2024-12-14T12:30:00Z",
        "delivered_at": "2024-12-14T12:30:15Z",
        "opens": 1,
        "clicks": 0,
        "bounces": 0
      }
    ],
    "total_emails": 1250,
    "delivered_emails": 1180,
    "failed_emails": 45,
    "delivery_rate": 94.4
  }
}
```

### Configure Email Settings

Update email configuration settings.

```http
POST /api/email/configure
Authorization: Bearer {token}
Content-Type: application/json

{
  "provider": "smtp",
  "settings": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "noreply@restaurant.com",
    "password": "app_password",
    "use_tls": true,
    "from_email": "noreply@restaurant.com",
    "from_name": "Restaurant POS"
  },
  "limits": {
    "per_hour": 100,
    "per_day": 1000
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "provider": "smtp",
    "configured_at": "2024-12-14T12:45:00Z",
    "test_email_status": "sent"
  },
  "message": "Email configuration updated successfully"
}
```

---

## Error Handling

### Error Codes

| Category | Code | Description | HTTP Status |
|----------|------|-------------|-------------|
| Authentication | AUTH001 | Invalid credentials | 401 |
| Authentication | AUTH002 | Token expired | 401 |
| Authentication | AUTH003 | Insufficient permissions | 403 |
| Validation | VAL001 | Required field missing | 400 |
| Validation | VAL002 | Invalid data format | 400 |
| Validation | VAL003 | Data validation failed | 400 |
| Payment | PAY001 | Payment declined | 400 |
| Payment | PAY002 | Insufficient funds | 400 |
| Payment | PAY003 | Payment timeout | 408 |
| Sync | SYNC001 | Sync failed | 500 |
| Sync | SYNC002 | Data conflict | 409 |
| Security | SEC001 | Rate limit exceeded | 429 |
| Security | SEC002 | IP blocked | 403 |
| Tenant | TEN001 | Tenant not found | 404 |
| Tenant | TEN002 | Access denied | 403 |

### Error Response Structure

```json
{
  "success": false,
  "error": {
    "code": "VAL001",
    "message": "Required field missing",
    "details": {
      "field": "email",
      "reason": "Email address is required"
    },
    "suggestion": "Please provide a valid email address"
  },
  "timestamp": "2024-12-14T13:00:00Z",
  "request_id": "req_123456789"
}
```

---

## Rate Limiting

### Rate Limits by Endpoint

| Endpoint Type | Requests | Time Window |
|---------------|----------|-------------|
| Authentication | 5 | 5 minutes |
| Payment API | 100 | 1 minute |
| General API | 200 | 1 minute |
| File Upload | 10 | 5 minutes |
| Bulk Operations | 50 | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 195
X-RateLimit-Reset: 1643123456
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "SEC001",
    "message": "Rate limit exceeded",
    "details": {
      "limit": 200,
      "window": "1 minute",
      "retry_after": 30
    }
  }
}
```

---

## Webhooks

### Payment Webhook

Handle Razorpay payment webhooks.

```http
POST /api/webhooks/razorpay
Content-Type: application/json
X-Razorpay-Signature: signature_hash

{
  "event": "payment.captured",
  "payload": {
    "payment": {
      "id": "pay_1234567890",
      "entity": "payment",
      "amount": 120000,
      "currency": "INR",
      "status": "captured"
    }
  }
}
```

### Order Status Webhook

Send order status updates to external systems.

```http
POST https://external-system.com/webhooks/order-status
Authorization: Bearer {webhook_token}
Content-Type: application/json

{
  "event": "order.status_changed",
  "order_id": "ORD20241214001",
  "old_status": "preparing",
  "new_status": "ready",
  "timestamp": "2024-12-14T13:15:00Z",
  "tenant_id": "tenant_001"
}
```

### Loyalty Webhook

Send loyalty program events.

```http
POST https://external-system.com/webhooks/loyalty
Authorization: Bearer {webhook_token}
Content-Type: application/json

{
  "event": "loyalty.points_earned",
  "customer_id": "cust_001",
  "points": 120,
  "order_id": "ORD20241214001",
  "timestamp": "2024-12-14T13:20:00Z"
}
```

---

## API Testing

### Test Environment

```
Base URL: https://test-api.restaurant.com/api
Test Credentials:
- Username: test_user
- Password: TestPassword123!
- Tenant ID: test_tenant_001
```

### Test Cards

```
Visa: 4111 1111 1111 1111
Mastercard: 5555 5555 5555 4444
Rupay: 6521 1111 1111 1111
Amex: 3782 822463 10005
```

### Sample API Calls

```bash
# Login
curl -X POST https://test-api.restaurant.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "TestPassword123!",
    "tenant_id": "test_tenant_001"
  }'

# Create Order
curl -X POST https://test-api.restaurant.com/api/orders \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust_001",
    "table_id": "T-05",
    "items": [{"menu_item_id": "menu_001", "quantity": 2}]
  }'
```

---

## SDK and Libraries

### JavaScript/Node.js

```javascript
const RestaurantPOS = require('@restaurant/pos-sdk');

const client = new RestaurantPOS({
  baseURL: 'https://api.restaurant.com/api',
  apiKey: 'your-api-key',
  tenantId: 'tenant_001'
});

// Create order
const order = await client.orders.create({
  customer_id: 'cust_001',
  items: [{menu_item_id: 'menu_001', quantity: 2}]
});
```

### Python

```python
from restaurant_pos import RestaurantPOSClient

client = RestaurantPOSClient(
    base_url='https://api.restaurant.com/api',
    api_key='your-api-key',
    tenant_id='tenant_001'
)

# Create order
order = client.orders.create({
    'customer_id': 'cust_001',
    'items': [{'menu_item_id': 'menu_001', 'quantity': 2}]
})
```

---

## Support and Documentation

### API Documentation

- **Interactive API Docs**: https://docs.restaurant.com/api
- **Postman Collection**: Available for download
- **OpenAPI Specification**: /api/openapi.json

### Support

- **API Support**: api-support@restaurant.com
- **Developer Forum**: https://forum.restaurant.com
- **Status Page**: https://status.restaurant.com

### Changelog

- **v2.0.0**: Enhanced security, CRM, loyalty, multi-tenancy
- **v1.5.0**: Added payment analytics
- **v1.2.0**: Introduced offline sync API
- **v1.0.0**: Initial API release

---

## API Best Practices

### Authentication and Security

#### 1. Token Management
```javascript
// Store tokens securely
localStorage.setItem('pos_token', token);

// Include token in all API calls
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// Handle token expiration
if (response.status === 401) {
  // Refresh token or redirect to login
  refreshToken();
}
```

#### 2. Secure API Calls
```python
# Use HTTPS in production
base_url = 'https://your-domain.com/api'

# Validate and sanitize input data
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Handle sensitive data properly
def create_payment_order(amount, customer_id):
    # Never log sensitive payment information
    logger.info(f"Creating payment order for customer {customer_id}")
    # Use secure payment gateway
    return payment_gateway.create_order(amount)
```

### Error Handling

#### 1. Comprehensive Error Handling
```javascript
try {
  const response = await apiClient.post('/orders', orderData);
  return response.data;
} catch (error) {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        showValidationError(data.error.details);
        break;
      case 401:
        redirectToLogin();
        break;
      case 403:
        showPermissionError();
        break;
      case 429:
        showRateLimitError(data.error.retry_after);
        break;
      case 500:
        showServerError();
        break;
      default:
        showGenericError();
    }
  } else if (error.request) {
    // Network error
    showNetworkError();
  } else {
    // Request configuration error
    showConfigError();
  }
}
```

#### 2. Retry Logic
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=3)
def create_order(order_data):
    return api_client.post('/orders', order_data)
```

### Performance Optimization

#### 1. Request Batching
```javascript
// Batch multiple requests
const batchRequests = async (requests) => {
  const batchPayload = {
    requests: requests.map(req => ({
      method: req.method,
      endpoint: req.endpoint,
      data: req.data
    }))
  };
  
  const response = await apiClient.post('/batch', batchPayload);
  return response.data.results;
};

// Usage
const results = await batchRequests([
  { method: 'GET', endpoint: '/customers/cust_001' },
  { method: 'GET', endpoint: '/orders/ORD_001' },
  { method: 'POST', endpoint: '/loyalty/earn', data: loyaltyData }
]);
```

#### 2. Caching Strategy
```python
from functools import lru_cache
import redis

# Redis caching for frequently accessed data
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_menu_items():
    cache_key = 'menu_items'
    cached_data = redis_client.get(cache_key)
    
    if cached_data:
        return json.loads(cached_data)
    
    # Fetch from API
    response = api_client.get('/menu/items')
    menu_data = response.json()
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(menu_data))
    return menu_data

# In-memory caching for static data
@lru_cache(maxsize=128)
def get_loyalty_tiers():
    response = api_client.get('/loyalty/tiers')
    return response.json()
```

### Data Validation

#### 1. Client-side Validation
```javascript
// Validate order data before sending
const validateOrder = (orderData) => {
  const errors = [];
  
  if (!orderData.customer_id) {
    errors.push('Customer ID is required');
  }
  
  if (!orderData.items || orderData.items.length === 0) {
    errors.push('At least one item is required');
  }
  
  orderData.items.forEach((item, index) => {
    if (!item.menu_item_id) {
      errors.push(`Menu item ID is required for item ${index + 1}`);
    }
    if (!item.quantity || item.quantity <= 0) {
      errors.push(`Valid quantity is required for item ${index + 1}`);
    }
  });
  
  return errors;
};

// Usage
const errors = validateOrder(orderData);
if (errors.length > 0) {
  showValidationErrors(errors);
  return;
}
```

#### 2. Server-side Validation
```python
from pydantic import BaseModel, validator

class OrderItem(BaseModel):
    menu_item_id: str
    quantity: int
    special_instructions: str = None
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class Order(BaseModel):
    customer_id: str
    table_id: str
    items: List[OrderItem]
    
    @validator('items')
    def validate_items(cls, v):
        if len(v) == 0:
            raise ValueError('At least one item is required')
        return v
```

### Monitoring and Logging

#### 1. API Call Monitoring
```javascript
// Log API calls for debugging
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000
});

apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    return Promise.reject(error);
  }
);
```

#### 2. Performance Monitoring
```python
import time
import logging

logger = logging.getLogger(__name__)

def log_api_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"API call {func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API call {func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

@log_api_call
def create_customer(customer_data):
    return api_client.post('/crm/customers', customer_data)
```

### Testing

#### 1. Unit Testing
```python
import unittest
from unittest.mock import Mock, patch

class TestAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = APIClient(base_url='http://test-api.com')
    
    @patch('requests.post')
    def test_create_order_success(self, mock_post):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'data': {'order_id': 'ORD_001'}
        }
        mock_post.return_value = mock_response
        
        # Test order creation
        order_data = {
            'customer_id': 'cust_001',
            'items': [{'menu_item_id': 'menu_001', 'quantity': 2}]
        }
        
        result = self.client.create_order(order_data)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['order_id'], 'ORD_001')
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_create_order_validation_error(self, mock_post):
        # Mock validation error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'success': False,
            'error': {'code': 'VAL001', 'message': 'Validation failed'}
        }
        mock_post.return_value = mock_response
        
        # Test order creation with invalid data
        order_data = {'customer_id': ''}  # Invalid data
        
        with self.assertRaises(ValidationError):
            self.client.create_order(order_data)
```

#### 2. Integration Testing
```javascript
// Integration test for order flow
describe('Order Integration Tests', () => {
  let authToken;
  
  beforeAll(async () => {
    // Login and get auth token
    const loginResponse = await apiClient.post('/auth/login', {
      username: 'test_user',
      password: 'test_password'
    });
    authToken = loginResponse.data.data.token;
  });
  
  test('Complete order flow', async () => {
    // 1. Create customer
    const customerResponse = await apiClient.post('/crm/customers', {
      name: 'Test Customer',
      email: 'test@example.com'
    }, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    const customerId = customerResponse.data.data.id;
    
    // 2. Create order
    const orderResponse = await apiClient.post('/orders', {
      customer_id: customerId,
      items: [{menu_item_id: 'menu_001', quantity: 2}]
    }, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    expect(orderResponse.data.success).toBe(true);
    expect(orderResponse.data.data.order_id).toBeDefined();
    
    // 3. Process payment
    const paymentResponse = await apiClient.post('/payment/create-order', {
      order_id: orderResponse.data.data.order_id,
      amount: 60000
    }, {
      headers: { 'Authorization': `Bearer ${authToken}` }
    });
    
    expect(paymentResponse.data.success).toBe(true);
  });
});
```

### Security Best Practices

#### 1. Input Sanitization
```python
import bleach
import html

def sanitize_input(user_input):
    """Sanitize user input to prevent XSS attacks"""
    # Remove HTML tags
    cleaned = bleach.clean(user_input)
    # Escape special characters
    cleaned = html.escape(cleaned)
    return cleaned.strip()

def validate_phone_number(phone):
    """Validate and normalize phone number"""
    # Remove non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Validate length (assuming 10-digit phone numbers)
    if len(digits_only) != 10:
        raise ValueError("Invalid phone number format")
    
    return f"+91{digits_only}"
```

#### 2. Rate Limiting
```javascript
// Implement client-side rate limiting
class RateLimiter {
  constructor(maxRequests, timeWindow) {
    this.maxRequests = maxRequests;
    this.timeWindow = timeWindow;
    this.requests = [];
  }
  
  async makeRequest(apiCall) {
    const now = Date.now();
    
    // Remove old requests outside time window
    this.requests = this.requests.filter(
      timestamp => now - timestamp < this.timeWindow
    );
    
    // Check if rate limit exceeded
    if (this.requests.length >= this.maxRequests) {
      const waitTime = this.timeWindow - (now - this.requests[0]);
      throw new Error(`Rate limit exceeded. Wait ${waitTime}ms`);
    }
    
    // Add current request to tracking
    this.requests.push(now);
    
    // Make API call
    return await apiCall();
  }
}

// Usage
const rateLimiter = new RateLimiter(100, 60000); // 100 requests per minute

try {
  const result = await rateLimiter.makeRequest(() =>
    apiClient.get('/orders')
  );
} catch (error) {
  console.error('Rate limit exceeded:', error.message);
}
```

---

**Version**: 2.0.0 API Documentation
**Last Updated**: December 2024
**Documentation**: Flask POS Development Team