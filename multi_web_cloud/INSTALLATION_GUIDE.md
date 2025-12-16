# Multi-Retail POS System - Installation Guide

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Prerequisites](#prerequisites)
4. [Installation Methods](#installation-methods)
5. [Development Environment Setup](#development-environment-setup)
6. [Production Environment Setup](#production-environment-setup)
7. [Database Configuration](#database-configuration)
8. [Environment Configuration](#environment-configuration)
9. [Initial System Setup](#initial-system-setup)
10. [Verification and Testing](#verification-and-testing)
11. [Troubleshooting Installation](#troubleshooting-installation)
12. [Next Steps](#next-steps)

## Overview

This guide provides comprehensive instructions for installing the Multi-Retail POS System in various environments. The system supports multiple retail types including restaurants, apparel stores, bookstores, supermarkets, and specialized retail operations with advanced features like multi-tenancy, offline support, and enterprise-grade security.

## System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Operating System** | Windows 10, Ubuntu 18.04, CentOS 7 | Windows 11, Ubuntu 20.04+, CentOS 8+ |
| **Python** | 3.8+ | 3.9+ |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 2GB free space | 10GB+ free space |
| **Processor** | Dual-core 2GHz | Quad-core 3GHz+ |
| **Network** | Broadband internet | High-speed broadband |

### Production Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Server** | 2 CPU cores, 4GB RAM | 4+ CPU cores, 8GB+ RAM |
| **Database** | SQLite (small deployments) | PostgreSQL 12+ or MySQL 8.0+ |
| **Load Balancer** | Nginx 1.18+ | Nginx 1.20+ or Apache 2.4+ |
| **SSL Certificate** | Self-signed (development) | Valid SSL certificate |
| **Backup Storage** | Local disk | Cloud storage (S3, Azure, GCP) |

## Prerequisites

### Required Software

1. **Python 3.8+**
   ```bash
   # Ubuntu/Debian
   sudo apt update && sudo apt install python3 python3-pip python3-venv
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   
   # Windows
   # Download from https://www.python.org/downloads/
   ```

2. **Git**
   ```bash
   # Ubuntu/Debian
   sudo apt install git
   
   # CentOS/RHEL
   sudo yum install git
   
   # Windows
   # Download from https://git-scm.com/download/win
   ```

3. **Database (Production)**
   ```bash
   # PostgreSQL
   sudo apt install postgresql postgresql-contrib
   
   # MySQL
   sudo apt install mysql-server
   
   # SQLite (included with Python)
   ```

4. **Web Server (Production)**
   ```bash
   # Nginx
   sudo apt install nginx
   
   # Apache (alternative)
   sudo apt install apache2
   ```

### Optional Software

1. **Redis (Caching and Session Storage)**
   ```bash
   sudo apt install redis-server
   ```

2. **Docker (Container Deployment)**
   ```bash
   # Ubuntu
   sudo apt install docker.io docker-compose
   
   # CentOS
   sudo yum install docker docker-compose
   ```

## Installation Methods

### Method 1: Development Setup (Quick Start)

### Method 2: Traditional Server Deployment

### Method 3: Docker Container Deployment

### Method 4: Cloud Platform Deployment

## Development Environment Setup

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd multi_web_cloud

# Verify the structure
ls -la
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# Verify activation
which python  # Should show venv path
```

### Step 3: Install Dependencies

```bash
# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

Sample `.env` file:
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///restaurant_pos.db

# Security Configuration
RATE_LIMIT_AUTH=5
RATE_LIMIT_API=200
IP_BLOCK_DURATION=3600
MAX_FAILED_ATTEMPTS=5

# Payment Configuration (Razorpay)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
RAZORPAY_TEST_MODE=True

# Multi-tenancy
MULTI_TENANT=True
DEFAULT_TENANT=default

# Offline Configuration
OFFLINE_MODE=False
SYNC_INTERVAL=30
MAX_RETRY_ATTEMPTS=3

# Base URL
BASE_URL=http://localhost:5000
```

### Step 5: Database Initialization

```bash
# Initialize database
python init_database.py

# Run migrations for enhanced features
python migrations/add_multi_tenant_foundation.py
python migrations/add_crm_loyalty_tables.py
python migrations/add_multi_retail_models.py
python migrations/encrypt_existing_data.py

# Initialize feature management
python migrations/init_feature_management.py
```

### Step 6: Start Development Server

```bash
# Start the application
python app.py

# Or use Flask run
flask run --host=0.0.0.0 --port=5000
```

### Step 7: Access Application

Open your browser and navigate to:
- **Application**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs
- **Health Check**: http://localhost:5000/health

Default login credentials:
- **Username**: admin
- **Password**: admin123

## Production Environment Setup

### Option 1: Traditional Server Deployment

#### Step 1: Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx redis-server -y

# Create application user
sudo useradd -m -s /bin/bash flaskpos
sudo usermod -aG sudo flaskpos
```

#### Step 2: Application Setup

```bash
# Switch to application user
sudo su - flaskpos

# Clone repository
git clone <repository-url> /home/flaskpos/multi_web_cloud
cd /home/flaskpos/multi_web_cloud

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install production dependencies
pip install gunicorn psycopg2-binary redis
```

#### Step 3: Database Setup

```bash
# Switch to postgres user
sudo su - postgres

# Create database and user
createdb pos_production
createuser --interactive flaskpos
# Set password when prompted

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE pos_production TO flaskpos;"

# Exit postgres user
exit
```

#### Step 4: Production Configuration

Create production configuration file:
```bash
nano /home/flaskpos/multi_web_cloud/production.py
```

```python
import os
from config import ProductionConfig

class ProductionDeploymentConfig(ProductionConfig):
    # Database
    SQLALCHEMY_DATABASE_URI = 'postgresql://flaskpos:password@localhost/pos_production'
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-in-production')
    FORCE_HTTPS = True
    
    # Performance
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/flaskpos/app.log'
    
    # Redis
    REDIS_URL = 'redis://localhost:6379/0'
    
    # Multi-tenancy
    MULTI_TENANT = True
    SHARED_DB = False
```

#### Step 5: Environment Variables

```bash
# Create production environment file
nano /home/flaskpos/multi_web_cloud/.env.production
```

```bash
# Production Environment Variables
FLASK_APP=app.py
FLASK_ENV=production
CONFIG_CLASS=production.ProductionDeploymentConfig

# Security
SECRET_KEY=your-super-secret-production-key
SESSION_SALT=your-session-salt

# Database
DATABASE_URL=postgresql://flaskpos:password@localhost/pos_production

# Payment Gateway
RAZORPAY_KEY_ID=your_production_razorpay_key
RAZORPAY_KEY_SECRET=your_production_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret
RAZORPAY_TEST_MODE=False

# SSL
FORCE_HTTPS=True
BASE_URL=https://your-domain.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/flaskpos/app.log
```

#### Step 6: Database Initialization

```bash
# Set environment
export CONFIG_CLASS=production.ProductionDeploymentConfig

# Initialize database
python init_database.py

# Run migrations
python migrations/add_multi_tenant_foundation.py
python migrations/add_crm_loyalty_tables.py
python migrations/add_multi_retail_models.py
python migrations/encrypt_existing_data.py
python migrations/init_feature_management.py
```

#### Step 7: Systemd Service

Create systemd service file:
```bash
sudo nano /etc/systemd/system/flaskpos.service
```

```ini
[Unit]
Description=Flask POS Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=flaskpos
Group=flaskpos
WorkingDirectory=/home/flaskpos/multi_web_cloud
Environment=PATH=/home/flaskpos/multi_web_cloud/venv/bin
EnvironmentFile=/home/flaskpos/multi_web_cloud/.env.production
ExecStart=/home/flaskpos/multi_web_cloud/venv/bin/gunicorn --workers 3 --worker-class sync --bind unix:flaskpos.sock --timeout 120 --keepalive 5 --max-requests 1000 --max-requests-jitter 100 app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 8: Nginx Configuration

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/flaskpos
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Application
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskpos/multi_web_cloud/flaskpos.sock;
        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static Files
    location /static {
        alias /home/flaskpos/multi_web_cloud/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
    }

    # Uploads
    location /uploads {
        alias /home/flaskpos/multi_web_cloud/uploads;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Security
    location ~ /\. {
        deny all;
    }

    # Health Check
    location /health {
        access_log off;
        proxy_pass http://unix:/home/flaskpos/multi_web_cloud/flaskpos.sock;
    }
}
```

#### Step 9: Start Services

```bash
# Enable and start services
sudo systemctl enable flaskpos
sudo systemctl start flaskpos
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status flaskpos
sudo systemctl status nginx
```

### Option 2: Docker Container Deployment

#### Step 1: Create Dockerfile

```bash
nano Dockerfile
```

```dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start command
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
```

#### Step 2: Create Docker Compose

```bash
nano docker-compose.yml
```

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://posuser:password@db:5432/pos_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - RAZORPAY_KEY_ID=${RAZORPAY_KEY_ID}
      - RAZORPAY_KEY_SECRET=${RAZORPAY_KEY_SECRET}
      - RAZORPAY_WEBHOOK_SECRET=${RAZORPAY_WEBHOOK_SECRET}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./exports:/app/exports
    restart: unless-stopped
    networks:
      - pos-network

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=pos_db
      - POSTGRES_USER=posuser
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - pos-network

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - pos-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
      - ./static:/var/www/static
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - pos-network

volumes:
  postgres_data:
  redis_data:

networks:
  pos-network:
    driver: bridge
```

#### Step 3: Environment File for Docker

```bash
nano .env.docker
```

```bash
# Docker Environment Variables
SECRET_KEY=your-docker-secret-key
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Database
POSTGRES_DB=pos_db
POSTGRES_USER=posuser
POSTGRES_PASSWORD=password
```

#### Step 4: Deploy with Docker

```bash
# Build and start containers
docker-compose --env-file .env.docker up -d

# Initialize database
docker-compose exec app python init_database.py

# Run migrations
docker-compose exec app python migrations/add_multi_tenant_foundation.py
docker-compose exec app python migrations/add_crm_loyalty_tables.py
docker-compose exec app python migrations/add_multi_retail_models.py
docker-compose exec app python migrations/encrypt_existing_data.py
docker-compose exec app python migrations/init_feature_management.py

# Check logs
docker-compose logs -f app
```

## Database Configuration

### SQLite (Development/Small Deployments)

```python
# config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///restaurant_pos.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

### PostgreSQL (Production)

```python
# config.py
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/pos_db'
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True,
    'max_overflow': 20
}
```

### MySQL (Alternative)

```python
# config.py
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/pos_db'
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Database Connection Pooling

```python
# Advanced database configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'max_overflow': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'echo': False  # Set to True for SQL logging
}
```

## Environment Configuration

### Development Environment

```python
# config/development.py
import os
from config import Config

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant_pos.db'
    
    # Development-specific settings
    OFFLINE_MODE = False
    RAZORPAY_TEST_MODE = True
    
    # Relaxed security for development
    RATE_LIMITS = {
        'default': {'requests': 1000, 'window': 60},
        'auth': {'requests': 100, 'window': 300},
        'api': {'requests': 1000, 'window': 60}
    }
```

### Production Environment

```python
# config/production.py
import os
from config import Config

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Production database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Enhanced security
    FORCE_HTTPS = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance optimizations
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Production rate limits
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},
        'auth': {'requests': 5, 'window': 300},
        'api': {'requests': 200, 'window': 60}
    }
```

### Testing Environment

```python
# config/testing.py
from config import Config

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Test-specific settings
    OFFLINE_MODE = True
    RAZORPAY_TEST_MODE = True
    
    # Disable rate limiting for tests
    RATE_LIMIT_ENABLED = False
```

## Initial System Setup

### Step 1: Database Initialization

```bash
# Initialize database with all tables
python init_database.py

# Run all required migrations in order
python migrations/add_multi_tenant_foundation.py
python migrations/add_crm_loyalty_tables.py
python migrations/add_multi_retail_models.py
python migrations/encrypt_existing_data.py
python migrations/init_feature_management.py
python migrations/migrate_restaurant_data.py
```

### Step 2: Create Default Tenant

```bash
# Create default tenant with retail type
python -c "
from app import create_app, db
from models.tenant import Tenant
from utils.retail_type_manager import get_retail_type_manager

app = create_app()
with app.app_context():
    # Create default tenant
    tenant = Tenant(
        id='default',
        name='Default Restaurant',
        subdomain='default',
        retail_type='restaurant',
        status='active'
    )
    db.session.add(tenant)
    db.session.commit()
    
    # Apply retail type preset
    retail_manager = get_retail_type_manager()
    retail_manager.apply_retail_type_preset('default', 'restaurant')
    
    print('Default tenant created successfully')
"
```

### Step 3: Create Admin User

```bash
# Create admin user with secure password
python -c "
from app import create_app, db
from models.user import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@company.com',
        password_hash=generate_password_hash('secure_password'),
        role='admin',
        is_active=True,
        tenant_id='default'
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
```

### Step 4: Configure Feature Flags

```bash
# Initialize feature flags for default tenant
python -c "
from app import create_app, db
from utils.feature_flag_manager import feature_manager
from utils.retail_type_manager import get_retail_type_manager

app = create_app()
with app.app_context():
    # Initialize feature manager
    feature_manager.initialize()
    retail_manager = get_retail_type_manager()
    
    # Apply restaurant preset to default tenant
    retail_manager.apply_retail_type_preset('default', 'restaurant')
    
    print('Feature flags configured successfully')
"
```

### Step 5: Verify Setup

```bash
# Check application health
curl http://localhost:5000/health

# Check database connection
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    result = db.engine.execute('SELECT 1').fetchone()
    print('Database connection:', 'OK' if result else 'FAILED')
"

# Check feature flags
curl http://localhost:5000/api/features/status
```

## Verification and Testing

### Automated Tests

```bash
# Run comprehensive test suite
python test_comprehensive_features.py

# Run security tests
python test_security_comprehensive.py

# Run multi-tenancy tests
python test_multi_tenancy_implementation.py

# Run performance tests
python test_performance_load.py
```

### Manual Verification

1. **Application Access**
   - Navigate to http://localhost:5000
   - Login with admin credentials
   - Verify dashboard loads correctly

2. **Multi-tenancy**
   - Check tenant isolation
   - Verify tenant-specific data
   - Test tenant switching

3. **Feature Flags**
   - Access /api/features/status
   - Verify retail-type specific features
   - Test feature enable/disable

4. **Security Features**
   - Check rate limiting
   - Verify CSRF protection
   - Test session security

5. **Offline Support**
   - Test offline mode
   - Verify sync functionality
   - Check conflict resolution

## Troubleshooting Installation

### Common Issues and Solutions

#### Python Environment Issues

```bash
# Check Python version
python --version
python3 --version

# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### Database Connection Issues

```bash
# Check database status
sudo systemctl status postgresql
sudo systemctl status mysql

# Test database connection
psql -h localhost -U username -d database_name

# Recreate database
dropdb database_name
createdb database_name
```

#### Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER /path/to/application
chmod -R 755 /path/to/application
chmod +x /path/to/application/app.py

# Fix database permissions
sudo chown -R postgres:postgres /var/lib/postgresql/
```

#### Port Conflicts

```bash
# Find process using port
sudo lsof -i :5000
sudo netstat -tulpn | grep :5000

# Kill process
sudo kill -9 <PID>

# Use different port
export FLASK_RUN_PORT=5001
python app.py
```

#### Memory Issues

```bash
# Check memory usage
free -h
df -h

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Log Analysis

```bash
# Application logs
tail -f logs/pos_app.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Systemd logs
sudo journalctl -u flaskpos -f

# Database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Performance Issues

```bash
# Check system resources
top
htop
iotop

# Monitor database queries
python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.engine.execute('EXPLAIN ANALYZE SELECT * FROM users LIMIT 10')
"
```

## Next Steps

After successful installation:

1. **Configure Retail Type**
   - Set up your specific retail type (restaurant, apparel, etc.)
   - Configure retail-specific features
   - Customize workflows

2. **Set Up Multi-tenancy**
   - Create additional tenants
   - Configure tenant isolation
   - Set up custom domains

3. **Configure Payment Gateway**
   - Set up Razorpay or other payment providers
   - Configure webhooks
   - Test payment processing

4. **Set Up Monitoring**
   - Configure logging
   - Set up monitoring tools
   - Configure alerts

5. **Backup and Recovery**
   - Set up automated backups
   - Test recovery procedures
   - Document backup strategy

6. **Security Hardening**
   - Review security settings
   - Configure SSL/TLS
   - Set up firewall rules

7. **User Training**
   - Train administrative users
   - Create user documentation
   - Set up support procedures

For detailed configuration guides, see:
- [Configuration Guide](CONFIGURATION_GUIDE.md)
- [Security Configuration Guide](SECURITY_GUIDE.md)
- [Multi-Retail Configuration Guide](MULTI_RETAIL_CONFIGURATION_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

---

**Installation Complete!** 🎉

Your Multi-Retail POS System is now installed and ready for configuration. Proceed to the Configuration Guide to set up your specific retail type and customize the system for your business needs.