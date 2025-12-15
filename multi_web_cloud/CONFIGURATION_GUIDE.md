# Configuration Guide - Enhanced Flask POS Application

## 📋 Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Payment Gateway Configuration](#payment-gateway-configuration)
6. [Offline Sync Configuration](#offline-sync-configuration)
7. [CRM & Loyalty Configuration](#crm--loyalty-configuration)
8. [Multi-Tenancy Configuration](#multi-tenancy-configuration)
9. [Email Configuration](#email-configuration)
10. [Performance Configuration](#performance-configuration)
11. [Logging Configuration](#logging-configuration)
12. [API Configuration](#api-configuration)
13. [Frontend Configuration](#frontend-configuration)
14. [Production Deployment](#production-deployment)
15. [Configuration Validation](#configuration-validation)

---

## Configuration Overview

### Configuration Files Structure

```
multi_web_cloud/
├── config.py                 # Main configuration file
├── config/
│   ├── __init__.py
│   ├── development.py        # Development environment config
│   ├── production.py         # Production environment config
│   ├── testing.py           # Testing environment config
│   ├── security.py          # Security settings
│   ├── database.py          # Database configuration
│   ├── payments.py          # Payment gateway settings
│   ├── email.py            # Email service settings
│   ├── performance.py      # Performance optimization settings
│   └── logging.py          # Logging configuration
├── .env                    # Environment variables
├── .env.example           # Environment variables template
└── docker-compose.yml      # Docker configuration
```

### Configuration Priority

1. **Environment Variables** (highest priority)
2. **Configuration Files** (medium priority)
3. **Default Values** (lowest priority)

### Environment Types

- **Development**: Local development environment
- **Testing**: Automated testing environment
- **Staging**: Pre-production testing environment
- **Production**: Live production environment

---

## Environment Setup

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Environment
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///restaurant_pos.db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Security
SECURITY_PASSWORD_SALT=your-password-salt
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password

# Redis (for caching and sessions)
REDIS_URL=redis://localhost:6379/0
REDIS_SESSION_PREFIX=pos_session:

# Multi-tenancy
MULTI_TENANT=True
DEFAULT_TENANT=default

# Performance
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Environment-Specific Configurations

#### Development Configuration

```python
# config/development.py
from . import *

DEBUG = True
TESTING = False

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///restaurant_pos_dev.db'
SQLALCHEMY_ECHO = True

# Security
WTF_CSRF_ENABLED = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# Email
MAIL_SUPPRESS_SEND = True

# Debug toolbar
DEBUG_TB_ENABLED = True
DEBUG_TB_INTERCEPT_REDIRECTS = False
```

#### Production Configuration

```python
# config/production.py
from . import *

DEBUG = False
TESTING = False

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 30

# Security
WTF_CSRF_ENABLED = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Performance
CACHE_TYPE = 'redis'
CACHE_REDIS_URL = os.environ.get('REDIS_URL')

# Logging
LOG_LEVEL = 'WARNING'
LOG_FILE = '/var/log/pos/app.log'
```

---

## Database Configuration

### SQLite Configuration (Development)

```python
# config/database.py
import os

class DatabaseConfig:
    # SQLite for development
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///restaurant_pos.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
```

### PostgreSQL Configuration (Production)

```python
# config/database.py
import os

class ProductionDatabaseConfig:
    # PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 30)),
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 30,
    }
```

### Database Migration Configuration

```python
# config/database.py
class MigrationConfig:
    # Migration settings
    MIGRATION_DIR = 'migrations'
    MIGRATION_TABLE = 'alembic_version'
    
    # Backup before migration
    BACKUP_BEFORE_MIGRATION = True
    BACKUP_DIR = 'backups/migrations'
```

### Offline Database Configuration

```python
# config/database.py
class OfflineDatabaseConfig:
    # Offline SQLite database
    OFFLINE_DATABASE_PATH = 'offline_data.db'
    OFFLINE_DATABASE_URI = f'sqlite:///{OFFLINE_DATABASE_PATH}'
    
    # Sync settings
    SYNC_BATCH_SIZE = 100
    SYNC_TIMEOUT = 30
    SYNC_RETRY_ATTEMPTS = 3
```

---

## Security Configuration

### Basic Security Settings

```python
# config/security.py
import os

class SecurityConfig:
    # Secret keys
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Session settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 3))
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_SSL_STRICT = os.environ.get('FLASK_ENV') == 'production'
```

### Advanced Security Configuration

```python
# config/security.py
class AdvancedSecurityConfig:
    # Rate limiting
    RATE_LIMIT_AUTH = int(os.environ.get('RATE_LIMIT_AUTH', 5))  # 5 per 5 minutes
    RATE_LIMIT_API = int(os.environ.get('RATE_LIMIT_API', 200))  # 200 per minute
    RATE_LIMIT_DEFAULT = int(os.environ.get('RATE_LIMIT_DEFAULT', 100))  # 100 per minute
    
    # IP blocking
    IP_BLOCK_DURATION = int(os.environ.get('IP_BLOCK_DURATION', 300))  # 5 minutes
    MAX_FAILED_ATTEMPTS = int(os.environ.get('MAX_FAILED_ATTEMPTS', 5))
    
    # Password policy
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    
    # Browser fingerprinting
    BROWSER_FINGERPRINTING = True
    FINGERPRINT_SALT = os.environ.get('FINGERPRINT_SALT', 'fingerprint_salt')
```

### Security Headers Configuration

```python
# config/security.py
class SecurityHeadersConfig:
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https://api.razorpay.com"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
```

---

## Payment Gateway Configuration

### Razorpay Configuration

```python
# config/payments.py
import os

class RazorpayConfig:
    # Razorpay credentials
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
    
    # Payment settings
    MIN_PAYMENT_AMOUNT = float(os.environ.get('MIN_PAYMENT_AMOUNT', 1.00))  # ₹1.00
    MAX_PAYMENT_AMOUNT = float(os.environ.get('MAX_PAYMENT_AMOUNT', 100000.00))  # ₹100,000.00
    CURRENCY = 'INR'
    
    # Webhook settings
    WEBHOOK_ENDPOINT = '/api/webhooks/razorpay'
    WEBHOOK_TIMEOUT = 30
    
    # Refund settings
    AUTO_REFUND_ENABLED = True
    REFUND_TIMEOUT = 7  # days
```

### Payment Method Configuration

```python
# config/payments.py
class PaymentMethodsConfig:
    # Available payment methods
    PAYMENT_METHODS = {
        'card': {
            'enabled': True,
            'display_name': 'Credit/Debit Card',
            'min_amount': 1.00,
            'max_amount': 100000.00,
            'supported_networks': ['Visa', 'Mastercard', 'Rupay', 'Amex']
        },
        'upi': {
            'enabled': True,
            'display_name': 'UPI',
            'min_amount': 1.00,
            'max_amount': 100000.00,
            'supported_apps': ['gpay', 'phonepe', 'paytm', 'bhim']
        },
        'netbanking': {
            'enabled': True,
            'display_name': 'Net Banking',
            'min_amount': 100.00,
            'max_amount': 100000.00,
            'supported_banks': ['HDFC', 'ICICI', 'SBI', 'PNB', 'Axis']
        },
        'wallet': {
            'enabled': True,
            'display_name': 'Mobile Wallet',
            'min_amount': 1.00,
            'max_amount': 10000.00,
            'supported_wallets': ['paytm', 'phonepe', 'amazonpay', 'freecharge']
        }
    }
```

### Payment Security Configuration

```python
# config/payments.py
class PaymentSecurityConfig:
    # 3D Secure settings
    THREE_D_SECURE_ENABLED = True
    THREE_D_SECURE_THRESHOLD = 2000.00  # ₹2000.00 and above
    
    # Fraud detection
    FRAUD_DETECTION_ENABLED = True
    FRAUD_RISK_THRESHOLD = 0.7
    VELOCITY_CHECK_ENABLED = True
    VELOCITY_LIMIT = 5  # transactions per hour
    
    # PCI DSS compliance
    PCI_DSS_MODE = 'strict'
    TOKENIZE_CARD_DATA = True
    STORE_CARD_DATA = False
```

---

## Offline Sync Configuration

### Sync Configuration

```python
# config/offline.py
import os

class OfflineSyncConfig:
    # Sync settings
    SYNC_ENABLED = True
    SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL', 30))  # seconds
    SYNC_BATCH_SIZE = int(os.environ.get('SYNC_BATCH_SIZE', 100))
    SYNC_TIMEOUT = int(os.environ.get('SYNC_TIMEOUT', 30))
    
    # Retry settings
    MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', 3))
    RETRY_BACKOFF_FACTOR = 2  # exponential backoff
    RETRY_DELAY = 5  # seconds
    
    # Conflict resolution
    CONFLICT_RESOLUTION = 'manual'  # manual, auto_online, auto_offline, merge
    CONFLICT_TIMEOUT = 86400  # 24 hours
    
    # Queue settings
    QUEUE_MAX_SIZE = 1000
    QUEUE_RETENTION_DAYS = 30
```

### Offline Data Configuration

```python
# config/offline.py
class OfflineDataConfig:
    # Data types to sync
    SYNC_DATA_TYPES = {
        'orders': True,
        'payments': True,
        'customers': True,
        'menu_items': True,
        'inventory': True,
        'settings': False
    }
    
    # Data retention
    OFFLINE_DATA_RETENTION_DAYS = int(os.environ.get('OFFLINE_DATA_RETENTION_DAYS', 90))
    BACKUP_INTERVAL = 3600  # 1 hour
    MAX_BACKUP_SIZE = 100  # MB
    
    # Encryption
    OFFLINE_DATA_ENCRYPTION = True
    OFFLINE_ENCRYPTION_KEY = os.environ.get('OFFLINE_ENCRYPTION_KEY')
```

---

## CRM & Loyalty Configuration

### CRM Configuration

```python
# config/crm.py
import os

class CRMConfig:
    # CRM settings
    CRM_ENABLED = os.environ.get('CRM_ENABLED', 'True').lower() == 'true'
    CUSTOMER_ANALYTICS = True
    COMMUNICATION_HISTORY = True
    
    # Customer data
    CUSTOMER_FIELDS = {
        'basic_info': ['name', 'email', 'phone', 'address'],
        'preferences': ['dietary', 'allergies', 'favorite_items'],
        'special_dates': ['birthday', 'anniversary'],
        'notes': True
    }
    
    # Communication settings
    EMAIL_COMMUNICATION = True
    SMS_COMMUNICATION = os.environ.get('SMS_ENABLED', 'False').lower() == 'true'
    PUSH_NOTIFICATIONS = True
    
    # Data retention
    CUSTOMER_DATA_RETENTION_DAYS = int(os.environ.get('CUSTOMER_DATA_RETENTION_DAYS', 2555))  # 7 years
```

### Loyalty Program Configuration

```python
# config/loyalty.py
import os

class LoyaltyConfig:
    # Loyalty settings
    LOYALTY_ENABLED = os.environ.get('LOYALTY_ENABLED', 'True').lower() == 'true'
    POINTS_PER_RUPEE = float(os.environ.get('POINTS_PER_RUPEE', 1.0))
    REDEMPTION_RATE = int(os.environ.get('REDEMPTION_RATE', 100))  # 100 points = ₹1
    
    # Tier configuration
    LOYALTY_TIERS = {
        'bronze': {
            'min_points': 0,
            'max_points': 999,
            'points_multiplier': 1.0,
            'discount_percentage': 5,
            'birthday_bonus': 100
        },
        'silver': {
            'min_points': 1000,
            'max_points': 4999,
            'points_multiplier': 1.2,
            'discount_percentage': 10,
            'birthday_bonus': 250
        },
        'gold': {
            'min_points': 5000,
            'max_points': 9999,
            'points_multiplier': 1.5,
            'discount_percentage': 15,
            'birthday_bonus': 500
        },
        'platinum': {
            'min_points': 10000,
            'max_points': None,
            'points_multiplier': 2.0,
            'discount_percentage': 20,
            'birthday_bonus': 1000
        }
    }
    
    # Referral program
    REFERRAL_ENABLED = True
    REFERRAL_BONUS_POINTS = int(os.environ.get('REFERRAL_BONUS_POINTS', 500))
    REFERRER_BONUS_POINTS = int(os.environ.get('REFERRER_BONUS_POINTS', 250))
    
    # Points expiration
    POINTS_EXPIRY_ENABLED = True
    POINTS_EXPIRY_DAYS = int(os.environ.get('POINTS_EXPIRY_DAYS', 365))
```

---

## Multi-Tenancy Configuration

### Multi-Tenancy Settings

```python
# config/multi_tenant.py
import os

class MultiTenancyConfig:
    # Multi-tenancy settings
    MULTI_TENANT = os.environ.get('MULTI_TENANT', 'True').lower() == 'true'
    TENANT_MODEL = 'models.tenant.Tenant'
    TENANT_COOKIE_NAME = 'tenant_id'
    DEFAULT_TENANT = os.environ.get('DEFAULT_TENANT', 'default')
    
    # Database isolation
    TENANT_ISOLATION = 'database'  # database, schema, row_level
    SHARED_DB = False  # Each tenant gets separate database
    
    # Tenant identification
    TENANT_IDENTIFICATION = 'subdomain'  # subdomain, path, header, cookie
    TENANT_HEADER = 'X-Tenant-ID'
    
    # Tenant settings
    TENANT_CUSTOMIZATION = {
        'branding': True,
        'domain': True,
        'features': True,
        'configuration': True
    }
```

### Tenant Database Configuration

```python
# config/multi_tenant.py
class TenantDatabaseConfig:
    # Database template
    TEMPLATE_DATABASE = 'template_pos'
    TENANT_DB_PREFIX = 'tenant_'
    TENANT_DB_SUFFIX = '_pos'
    
    # Database creation
    AUTO_CREATE_TENANT_DB = True
    TENANT_DB_CHARSET = 'utf8mb4'
    TENANT_DB_COLLATION = 'utf8mb4_unicode_ci'
    
    # Connection pooling
    TENANT_POOL_SIZE = 5
    TENANT_MAX_OVERFLOW = 10
    TENANT_POOL_TIMEOUT = 30
```

---

## Email Configuration

### SMTP Configuration

```python
# config/email.py
import os

class EmailConfig:
    # SMTP settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    
    # Authentication
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Email settings
    MAIL_SUPPRESS_SEND = os.environ.get('FLASK_ENV') == 'development'
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_MAX_EMAILS = 50
    MAIL_MAX_ATTACHMENTS = 10
    
    # Templates
    EMAIL_TEMPLATES_DIR = 'templates/email'
    EMAIL_TEMPLATE_AUTO_RELOAD = os.environ.get('FLASK_ENV') == 'development'
```

### Email Service Configuration

```python
# config/email.py
class EmailServiceConfig:
    # Email services
    EMAIL_SERVICES = {
        'notifications': {
            'enabled': True,
            'templates': ['order_confirmation', 'payment_receipt', 'loyalty_update']
        },
        'marketing': {
            'enabled': True,
            'templates': ['promotion', 'newsletter', 'birthday_offer']
        },
        'alerts': {
            'enabled': True,
            'templates': ['security_alert', 'system_alert', 'payment_failure']
        }
    }
    
    # Rate limiting
    EMAIL_RATE_LIMIT = 100  # emails per hour
    EMAIL_BATCH_SIZE = 50
    
    # Unsubscribe
    UNSUBSCRIBE_ENABLED = True
    UNSUBSCRIBE_URL = '/unsubscribe'
```

---

## Performance Configuration

### Caching Configuration

```python
# config/performance.py
import os

class CacheConfig:
    # Cache settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Cache keys
    CACHE_KEY_PREFIX = 'pos_cache_'
    CACHE_VERSION = 'v1'
    
    # Cache regions
    CACHE_REGIONS = {
        'menu': {'timeout': 3600},  # 1 hour
        'customers': {'timeout': 1800},  # 30 minutes
        'orders': {'timeout': 300},  # 5 minutes
        'reports': {'timeout': 1800},  # 30 minutes
        'settings': {'timeout': 86400}  # 24 hours
    }
```

### Database Performance Configuration

```python
# config/performance.py
class DatabasePerformanceConfig:
    # Connection pooling
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('SQLALCHEMY_POOL_SIZE', 20))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('SQLALCHEMY_MAX_OVERFLOW', 30))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('SQLALCHEMY_POOL_TIMEOUT', 30))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('SQLALCHEMY_POOL_RECYCLE', 3600))
    
    # Query optimization
    SQLALCHEMY_RECORD_QUERIES = os.environ.get('FLASK_ENV') == 'development'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Index optimization
    AUTO_CREATE_INDEXES = True
    INDEX_ANALYSIS_ENABLED = True
```

### Application Performance Configuration

```python
# config/performance.py
class ApplicationPerformanceConfig:
    # Session handling
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'pos_session:'
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.pdf']
    UPLOAD_FOLDER = 'uploads'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Background tasks
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/2')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')
```

---

## Logging Configuration

### Basic Logging Configuration

```python
# config/logging.py
import os
import logging
from logging.handlers import RotatingFileHandler

class LoggingConfig:
    # Log level
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Log files
    LOG_DIR = 'logs'
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Loggers
    LOGGERS = {
        'app': {'level': 'INFO', 'file': 'app.log'},
        'security': {'level': 'WARNING', 'file': 'security.log'},
        'payment': {'level': 'INFO', 'file': 'payment.log'},
        'sync': {'level': 'INFO', 'file': 'sync.log'},
        'api': {'level': 'INFO', 'file': 'api.log'}
    }
```

### Advanced Logging Configuration

```python
# config/logging.py
class AdvancedLoggingConfig:
    # Structured logging
    STRUCTURED_LOGGING = True
    LOG_FORMAT = 'json'
    
    # Log aggregation
    LOG_AGGREGATION_ENABLED = True
    LOG_AGGREGATION_ENDPOINT = os.environ.get('LOG_AGGREGATION_ENDPOINT')
    LOG_AGGREGATION_API_KEY = os.environ.get('LOG_AGGREGATION_API_KEY')
    
    # Security logging
    SECURITY_LOG_LEVEL = 'INFO'
    SECURITY_LOG_EVENTS = [
        'login_success', 'login_failure', 'password_change',
        'session_created', 'session_terminated', 'suspicious_activity'
    ]
    
    # Performance logging
    PERFORMANCE_LOGGING = True
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
    SLOW_REQUEST_THRESHOLD = 2.0  # seconds
```

---

## API Configuration

### API Settings Configuration

```python
# config/api.py
import os

class APIConfig:
    # API versioning
    API_VERSION = 'v2'
    API_VERSION_HEADER = 'X-API-Version'
    API_VERSION_URL_PREFIX = '/api/v2'
    
    # Rate limiting
    API_RATE_LIMITS = {
        'default': '200/hour',
        'auth': '5/minute',
        'payment': '100/hour',
        'upload': '10/hour'
    }
    
    # Pagination
    API_DEFAULT_PAGE_SIZE = 20
    API_MAX_PAGE_SIZE = 100
    
    # Response format
    API_DEFAULT_FORMAT = 'json'
    API_WRAP_RESPONSES = True
    API_INCLUDE_METADATA = True
```

### API Security Configuration

```python
# config/api.py
class APISecurityConfig:
    # Authentication
    API_AUTH_REQUIRED = True
    API_AUTH_METHODS = ['session', 'jwt', 'api_key']
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization', 'X-API-Key']
    
    # API keys
    API_KEY_HEADER = 'X-API-Key'
    API_KEY_LENGTH = 32
    API_KEY_EXPIRY_DAYS = 365
```

---

## Frontend Configuration

### Static Assets Configuration

```python
# config/frontend.py
import os

class FrontendConfig:
    # Static files
    STATIC_FOLDER = 'static'
    STATIC_URL_PATH = '/static'
    
    # Asset versioning
    ASSET_VERSIONING = True
    ASSET_VERSION = os.environ.get('ASSET_VERSION', '1.0.0')
    
    # CDN settings
    CDN_ENABLED = os.environ.get('CDN_ENABLED', 'False').lower() == 'true'
    CDN_BASE_URL = os.environ.get('CDN_BASE_URL')
    
    # Minification
    MINIFY_JS = os.environ.get('FLASK_ENV') == 'production'
    MINIFY_CSS = os.environ.get('FLASK_ENV') == 'production'
    
    # Cache headers
    STATIC_CACHE_DURATION = 31536000  # 1 year
    STATIC_CACHE_HEADERS = {
        'Cache-Control': 'public, max-age=31536000',
        'Expires': 'Thu, 31 Dec 2030 23:59:59 GMT'
    }
```

### UI Configuration

```python
# config/frontend.py
class UIConfig:
    # Theme settings
    DEFAULT_THEME = 'light'
    AVAILABLE_THEMES = ['light', 'dark', 'auto']
    
    # Language settings
    DEFAULT_LANGUAGE = 'en'
    AVAILABLE_LANGUAGES = ['en', 'hi', 'gu', 'mr']
    
    # UI settings
    ITEMS_PER_PAGE = 20
    AUTO_REFRESH_INTERVAL = 30  # seconds
    NOTIFICATION_DURATION = 5000  # milliseconds
    
    # Feature flags
    FEATURE_FLAGS = {
        'offline_mode': True,
        'real_time_updates': True,
        'advanced_analytics': True,
        'customer_photos': False
    }
```

---

## Production Deployment

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/pos
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Application Proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static Files
    location /static/ {
        alias /path/to/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API Rate Limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
    }
}

# Rate Limiting Zones
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;
}
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', 4))
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeout settings
timeout = 30
keepalive = 2
graceful_timeout = 30

# Logging
accesslog = "/var/log/pos/access.log"
errorlog = "/var/log/pos/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "pos_app"

# Server mechanics
daemon = False
pidfile = "/var/run/pos/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:password@db:5432/pos_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=pos_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## Configuration Validation

### Configuration Validation Script

```python
# scripts/validate_config.py
import os
import sys
from config import Config

def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []

    # Check required environment variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'RAZORPAY_KEY_ID',
        'RAZORPAY_KEY_SECRET'
    ]

    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f"Required environment variable {var} is missing")

    # Validate database connection
    try:
        from app import db
        db.engine.execute('SELECT 1')
    except Exception as e:
        errors.append(f"Database connection failed: {str(e)}")

    # Validate Redis connection
    try:
        import redis
        r = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
    except Exception as e:
        warnings.append(f"Redis connection failed: {str(e)}")

    # Validate payment gateway
    try:
        import razorpay
        client = razorpay.Client(
            auth=(os.environ.get('RAZORPAY_KEY_ID'), 
                   os.environ.get('RAZORPAY_KEY_SECRET'))
        )
        client.orders.all({'count': 1})
    except Exception as e:
        errors.append(f"Razorpay connection failed: {str(e)}")

    # Report results
    if errors:
        print("Configuration Errors:")
        for error in errors:
            print(f"  ❌ {error}")
        sys.exit(1)

    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")

    if not errors and not warnings:
        print("✅ Configuration is valid")

if __name__ == '__main__':
    validate_config()
```

### Configuration Testing

```python
# tests/test_config.py
import pytest
import os
from config import Config, DevelopmentConfig, ProductionConfig

class TestConfig:
    def test_default_config(self):
        """Test default configuration"""
        assert Config.SECRET_KEY is not None
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert Config.WTF_CSRF_ENABLED is True

    def test_development_config(self):
        """Test development configuration"""
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.SQLALCHEMY_ECHO is True
        assert DevelopmentConfig.MAIL_SUPPRESS_SEND is True

    def test_production_config(self):
        """Test production configuration"""
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.SQLALCHEMY_ECHO is False
        assert ProductionConfig.SESSION_COOKIE_SECURE is True

    def test_environment_variables(self):
        """Test environment variable loading"""
        os.environ['TEST_VAR'] = 'test_value'
        from config import Config
        assert hasattr(Config, 'TEST_VAR')
        assert Config.TEST_VAR == 'test_value'
```

### Configuration Monitoring

```python
# scripts/monitor_config.py
import os
import time
import logging
from datetime import datetime

def monitor_config_changes():
    """Monitor configuration file changes"""
    config_files = [
        'config.py',
        '.env',
        'config/production.py'
    ]

    last_modified = {}

    for file in config_files:
        if os.path.exists(file):
            last_modified[file] = os.path.getmtime(file)

    while True:
        for file in config_files:
            if os.path.exists(file):
                current_modified = os.path.getmtime(file)
                if current_modified > last_modified.get(file, 0):
                    logging.warning(f"Configuration file {file} was modified")
                    last_modified[file] = current_modified
        
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    monitor_config_changes()
```

---

## Advanced Configuration Topics

### SSL/TLS Configuration

#### SSL Certificate Setup

```bash
# Generate SSL certificate (for development)
openssl req -x509 -newkey rsa:4096 -keyout ssl/private.key -out ssl/cert.pem -days 365 -nodes

# Production SSL configuration (Let's Encrypt)
certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### SSL Configuration in Nginx

```nginx
# Enhanced SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### Database Replication Configuration

#### Master-Slave Replication

```python
# config/database.py
class ReplicationConfig:
    # Master database
    MASTER_DATABASE_URI = os.environ.get('MASTER_DATABASE_URL')
    
    # Slave databases
    SLAVE_DATABASE_URIS = [
        os.environ.get('SLAVE_DATABASE_1_URL'),
        os.environ.get('SLAVE_DATABASE_2_URL')
    ]
    
    # Replication settings
    REPLICATION_ENABLED = True
    READ_FROM_SLAVE = True
    WRITE_TO_MASTER = True
    
    # Health check
    SLAVE_HEALTH_CHECK_INTERVAL = 30  # seconds
    SLAVE_TIMEOUT = 5  # seconds
```

#### Database Connection Routing

```python
# config/database.py
class DatabaseRouter:
    def __init__(self):
        self.master_engine = create_engine(MASTER_DATABASE_URI)
        self.slave_engines = [
            create_engine(uri) for uri in SLAVE_DATABASE_URIS
        ]
        self.current_slave = 0
    
    def get_read_engine(self):
        """Round-robin slave selection for read operations"""
        engine = self.slave_engines[self.current_slave]
        self.current_slave = (self.current_slave + 1) % len(self.slave_engines)
        return engine
    
    def get_write_engine(self):
        """Master engine for write operations"""
        return self.master_engine
```

### Advanced Caching Strategies

#### Multi-Level Caching

```python
# config/caching.py
class MultiLevelCacheConfig:
    # L1: In-memory cache (fastest)
    L1_CACHE_SIZE = 1000
    L1_CACHE_TTL = 300  # 5 minutes
    
    # L2: Redis cache (fast)
    L2_CACHE_SIZE = 10000
    L2_CACHE_TTL = 3600  # 1 hour
    
    # L3: Database cache (slowest)
    L3_CACHE_SIZE = 100000
    L3_CACHE_TTL = 86400  # 24 hours
    
    # Cache invalidation
    CACHE_INVALIDATION_STRATEGY = 'tagged'  # tagged, ttl, manual
    CACHE_TAGS = {
        'menu': ['menu_items', 'categories', 'prices'],
        'customers': ['customer_data', 'preferences', 'loyalty'],
        'orders': ['order_status', 'payments', 'kots']
    }
```

#### Cache Warming Strategy

```python
# config/caching.py
class CacheWarmingConfig:
    # Pre-warm cache on startup
    WARM_CACHE_ON_STARTUP = True
    
    # Cache warming schedule
    WARMING_SCHEDULE = {
        'menu_items': '*/5 * * * *',  # Every 5 minutes
        'customer_data': '0 */2 * * *',  # Every 2 hours
        'reports': '0 0 * * *'  # Daily at midnight
    }
    
    # Critical data to pre-warm
    CRITICAL_CACHE_KEYS = [
        'menu_items',
        'active_customers',
        'system_settings',
        'payment_methods'
    ]
```

### High Availability Configuration

#### Load Balancer Configuration

```nginx
# nginx.conf - Load balancing
upstream app_servers {
    least_conn;
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Health check
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

#### Health Check Configuration

```python
# config/health.py
class HealthCheckConfig:
    # Health check endpoints
    HEALTH_CHECK_ENDPOINTS = {
        'database': '/health/db',
        'redis': '/health/redis',
        'payment_gateway': '/health/payment',
        'external_apis': '/health/external'
    }
    
    # Health check thresholds
    HEALTH_CHECK_THRESHOLDS = {
        'response_time': 2.0,  # seconds
        'cpu_usage': 80.0,  # percentage
        'memory_usage': 85.0,  # percentage
        'disk_usage': 90.0  # percentage
    }
    
    # Alert configuration
    HEALTH_ALERT_ENABLED = True
    HEALTH_ALERT_EMAIL = 'admin@your-domain.com'
    HEALTH_ALERT_WEBHOOK = 'https://hooks.slack.com/your-webhook-url'
```

### Monitoring and Analytics Configuration

#### Application Performance Monitoring (APM)

```python
# config/monitoring.py
class APMConfig:
    # APM provider settings
    APM_PROVIDER = 'newrelic'  # newrelic, datadog, prometheus
    APM_ENABLED = True
    
    # New Relic configuration
    NEW_RELIC_LICENSE_KEY = os.environ.get('NEW_RELIC_LICENSE_KEY')
    NEW_RELIC_APP_NAME = 'Restaurant POS'
    NEW_RELIC_LOG_LEVEL = 'info'
    
    # Custom metrics
    CUSTOM_METRICS = {
        'order_processing_time': True,
        'payment_success_rate': True,
        'customer_satisfaction': True,
        'inventory_turnover': True
    }
    
    # Distributed tracing
    DISTRIBUTED_TRACING_ENABLED = True
    TRACE_SAMPLE_RATE = 0.1  # 10% of requests
```

#### Business Intelligence Configuration

```python
# config/analytics.py
class AnalyticsConfig:
    # Analytics providers
    ANALYTICS_PROVIDERS = {
        'google_analytics': {
            'enabled': True,
            'tracking_id': os.environ.get('GA_TRACKING_ID')
        },
        'mixpanel': {
            'enabled': True,
            'token': os.environ.get('MIXPANEL_TOKEN')
        }
    }
    
    # Custom events to track
    TRACKED_EVENTS = [
        'order_created',
        'payment_completed',
        'customer_registered',
        'loyalty_points_earned',
        'menu_item_viewed',
        'search_performed'
    ]
    
    # Data retention
    ANALYTICS_DATA_RETENTION_DAYS = 365
    AGGREGATED_DATA_RETENTION_DAYS = 2555  # 7 years
```

### Compliance and Audit Configuration

#### GDPR Compliance Configuration

```python
# config/compliance.py
class GDPRConfig:
    # Data protection settings
    GDPR_COMPLIANCE_ENABLED = True
    DATA_ENCRYPTION_AT_REST = True
    DATA_ENCRYPTION_IN_TRANSIT = True
    
    # Data retention policies
    PERSONAL_DATA_RETENTION_DAYS = 2555  # 7 years
    INACTIVE_CUSTOMER_RETENTION_DAYS = 1095  # 3 years
    
    # Consent management
    CONSENT_REQUIRED = True
    CONSENT_TYPES = ['marketing', 'analytics', 'functional']
    CONSENT_STORAGE = 'database'  # database, file, encrypted_cookie
    
    # Data subject rights
    DATA_EXPORT_FORMAT = 'json'
    DATA_DELETION_METHOD = 'soft_delete'  # soft_delete, hard_delete, anonymize
```

#### Audit Logging Configuration

```python
# config/audit.py
class AuditConfig:
    # Audit settings
    AUDIT_ENABLED = True
    AUDIT_LEVEL = 'detailed'  # basic, detailed, comprehensive
    
    # Audit events
    AUDIT_EVENTS = {
        'authentication': ['login', 'logout', 'password_change', 'failed_login'],
        'data_access': ['customer_view', 'order_view', 'report_generation'],
        'data_modification': ['customer_update', 'order_create', 'price_change'],
        'system': ['config_change', 'user_management', 'permission_change']
    }
    
    # Audit storage
    AUDIT_STORAGE = 'database'  # database, file, syslog
    AUDIT_RETENTION_DAYS = 2555  # 7 years
    AUDIT_ENCRYPTION = True
    
    # Audit alerts
    AUDIT_ALERTS = {
        'suspicious_activity': True,
        'data_breach': True,
        'privilege_escalation': True,
        'config_changes': True
    }
```

## Configuration Best Practices

### Security Best Practices

1. **Use Environment Variables**: Never hardcode sensitive information
2. **Separate Configurations**: Use different configs for different environments
3. **Encrypt Sensitive Data**: Use encryption for passwords and API keys
4. **Regular Key Rotation**: Rotate encryption keys and secrets regularly
5. **Access Control**: Limit access to configuration files
6. **Security Headers**: Implement comprehensive security headers
7. **SSL/TLS**: Always use HTTPS in production with proper certificates
8. **Regular Audits**: Conduct regular security audits and penetration testing

### Performance Best Practices

1. **Connection Pooling**: Configure appropriate database connection pools
2. **Caching Strategy**: Implement multi-level caching
3. **Resource Limits**: Set appropriate resource limits
4. **Monitoring**: Monitor configuration performance impact
5. **Optimization**: Regularly review and optimize settings
6. **Load Balancing**: Implement load balancing for high availability
7. **CDN Usage**: Use CDN for static assets in production
8. **Database Indexing**: Ensure proper database indexing for queries

### Maintenance Best Practices

1. **Version Control**: Keep configuration files in version control
2. **Documentation**: Document all configuration options
3. **Testing**: Test configuration changes before deployment
4. **Backup**: Backup configuration files regularly
5. **Validation**: Validate configuration on startup
6. **Monitoring**: Monitor configuration changes and impacts
7. **Rollback Plan**: Have rollback procedures for configuration changes
8. **Change Management**: Implement formal change management process

### Compliance Best Practices

1. **Data Protection**: Implement GDPR/CCPA compliance measures
2. **Audit Logging**: Maintain comprehensive audit trails
3. **Data Retention**: Follow legal requirements for data retention
4. **Access Logs**: Maintain detailed access logs
5. **Incident Response**: Have incident response procedures
6. **Regular Reviews**: Conduct regular compliance reviews
7. **Documentation**: Maintain compliance documentation
8. **Training**: Ensure staff is trained on compliance requirements

---

## Troubleshooting Configuration Issues

### Common Configuration Problems

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify database server is running
   - Check network connectivity
   - Validate credentials

2. **Payment Gateway Issues**
   - Verify API keys are correct
   - Check webhook URL configuration
   - Validate SSL certificates
   - Test with sandbox mode

3. **Security Configuration Errors**
   - Check SECRET_KEY is set
   - Verify CSRF token configuration
   - Validate security headers
   - Check rate limiting settings

4. **Performance Issues**
   - Review database connection pooling
   - Check caching configuration
   - Monitor resource usage
   - Optimize query performance

### Debug Configuration

```python
# scripts/debug_config.py
import os
import sys
from config import Config

def debug_config():
    """Debug configuration issues"""
    print("=== Configuration Debug ===")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    print(f"Debug Mode: {Config.DEBUG}")
    print(f"Database URL: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f"Secret Key Set: {'Yes' if Config.SECRET_KEY else 'No'}")
    print(f"Razorpay Key Set: {'Yes' if Config.RAZORPAY_KEY_ID else 'No'}")
    print(f"Redis URL: {getattr(Config, 'REDIS_URL', 'Not set')}")
    
    # Test imports
    try:
        import redis
        print("Redis: Available")
    except ImportError:
        print("Redis: Not available")
    
    try:
        import psycopg2
        print("PostgreSQL: Available")
    except ImportError:
        print("PostgreSQL: Not available")

if __name__ == '__main__':
    debug_config()
```

---

**Version**: 2.0.0 Configuration Guide  
**Last Updated**: December 2024  
**Documentation**: Flask POS Development Team