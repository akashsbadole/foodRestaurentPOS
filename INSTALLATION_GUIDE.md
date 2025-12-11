# POS System Installation Guide

## Overview
This guide provides step-by-step instructions for installing and configuring the Restaurant POS system with all newly implemented features. It covers both the Flask web version and Tkinter desktop version.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.10 or higher
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 2GB free disk space
- **Network**: Internet connection for email features

### Recommended Requirements
- **Operating System**: Windows 11 or macOS 12+
- **Python**: 3.11 or higher
- **Memory**: 8GB RAM or higher
- **Storage**: 5GB free disk space
- **Processor**: Multi-core CPU (4+ cores recommended)

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Feature Configuration](#feature-configuration)
6. [Testing the Installation](#testing-the-installation)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Python Installation
```bash
# Windows (using Python launcher)
py --version

# Install Python 3.11 if not installed
# Download from https://www.python.org/downloads/

# macOS (using Homebrew)
brew install python@3.11

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

### 2. Git Installation
```bash
# Windows
# Download from https://git-scm.com/download/win

# macOS
brew install git

# Linux
sudo apt install git
```

### 3. Database Requirements
```bash
# SQLite is included with Python, but ensure it's available
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"

# For production, consider PostgreSQL or MySQL
# PostgreSQL
sudo apt install postgresql postgresql-contrib

# MySQL
sudo apt install mysql-server mysql-client
```

---

## Installation Steps

### 1. Clone Repository
```bash
# Clone the POS system repository
git clone https://github.com/your-org/restaurant-pos.git
cd restaurant-pos

# Checkout the latest stable branch
git checkout stable
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv pos_env

# Activate virtual environment
# Windows
pos_env\Scripts\activate

# macOS/Linux
source pos_env/bin/activate
```

### 3. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For development with additional tools
pip install -r requirements-dev.txt
```

### 4. Web Version Dependencies
```bash
# Navigate to web_cloud directory
cd web_cloud

# Install web-specific dependencies
pip install -r requirements.txt

# Install Node.js dependencies (if applicable)
npm install
```

### 5. Verify Installation
```bash
# Check Python dependencies
pip check

# Test imports
python -c "
import sys
sys.path.insert(0, 'src')
try:
    from src.utils.encryption import get_encryption_manager
    from src.utils.image_handler import ImageHandler
    from src.utils.email_service import EmailService
    from src.utils.performance_utils import get_performance_manager
    from src.utils.footer_generator import FooterGenerator
    from src.ui.kot_window import KOTWindow
    print('All imports successful')
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
"
```

---

## Configuration

### 1. Environment Variables
```bash
# Create .env file for sensitive configuration
cat > .env << EOF
# Database Configuration
DATABASE_URL=sqlite:///restaurant_pos.db
# For production: DATABASE_URL=postgresql://user:password@localhost/restaurant_pos

# Security Configuration
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY_PATH=src/config/encryption.key

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Performance Configuration
DEBUG_MODE=false
LOG_LEVEL=INFO
MEMORY_LIMIT_MB=512

# Feature Flags
ENABLE_IMAGE_UPLOAD=true
ENABLE_ENCRYPTION=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_PERFORMANCE_OPTIMIZATION=true
EOF

# Set appropriate permissions
chmod 600 .env
```

### 2. Create Configuration Files
```bash
# Create configuration directories
mkdir -p src/config
mkdir -p logs
mkdir -p backups
mkdir -p uploads/menu_items

# Performance configuration
cat > src/config/performance_config.json << EOF
{
    "memory": {
        "max_usage_mb": 512,
        "cleanup_interval": 300,
        "cache_size": 100
    },
    "lazy_loading": {
        "enabled": true,
        "preload_count": 5,
        "cache_ttl": 3600
    },
    "pagination": {
        "default_page_size": 50,
        "max_page_size": 200
    },
    "image_upload": {
        "max_file_size": 5242880,
        "allowed_formats": ["jpg", "jpeg", "png", "webp"],
        "thumbnail_size": [200, 200],
        "compression_quality": 85
    }
}
EOF

# Encryption configuration
cat > src/config/encryption_config.json << EOF
{
    "algorithm": "AES-256-GCM",
    "key_rotation_days": 90,
    "backup_encryption": true,
    "field_encryption": ["email", "phone", "address", "credit_card"]
}
EOF
```

---

## Database Setup

### 1. Initialize Database
```bash
# Run database initialization
python database_setup.py

# For web version
cd web_cloud
python init_db.py
```

### 2. Run Migrations
```bash
# Run all migrations
python src/migrations/add_image_path_column.py
python src/migrations/encrypt_existing_data.py

# For web version
cd web_cloud
python migrations/add_image_path_column.py
python migrations/encrypt_existing_data.py
```

### 3. Create Default Data
```bash
# Create default categories, menu items, and settings
python -c "
from src.models.database import DatabaseManager
from src.models.category import Category
from src.models.menu_item import MenuItem
from src.models.settings import Settings

db = DatabaseManager()

# Create default categories
categories = [
    {'name': 'Beverages', 'description': 'Soft drinks, juices, water'},
    {'name': 'Appetizers', 'description': 'Starters and small dishes'},
    {'name': 'Main Course', 'description': 'Main dishes and entrees'},
    {'name': 'Desserts', 'description': 'Sweet dishes and desserts'}
]

for cat_data in categories:
    category = Category(db)
    category.name = cat_data['name']
    category.description = cat_data['description']
    category.save()

# Create default admin user
from src.models.user import User
admin = User.create_user('admin', 'admin123', 'Administrator', 'admin@restaurant.com')
print('Default data created successfully')
"
```

---

## Feature Configuration

### 1. Image Upload Configuration
```python
# Configure image upload settings
from src.utils.image_handler import ImageHandler

# Test image upload
handler = ImageHandler()

# Verify supported formats
formats = ['jpg', 'jpeg', 'png', 'webp']
for fmt in formats:
    test_file = f"test.{fmt}"
    print(f"Testing {fmt} support: {handler.validate_image(test_file)}")

# Configure upload directory
import os
upload_dir = 'uploads/menu_items'
os.makedirs(upload_dir, exist_ok=True)
print(f"Upload directory: {os.path.abspath(upload_dir)}")
```

### 2. Encryption Configuration
```python
# Initialize encryption
from src.utils.encryption import get_encryption_manager

# Get encryption manager
enc_manager = get_encryption_manager()

# Test encryption
test_data = "Sensitive POS data"
encrypted = enc_manager.encrypt(test_data)
decrypted = enc_manager.decrypt(encrypted)

print(f"Encryption test: {'PASS' if decrypted == test_data else 'FAIL'}")

# Generate encryption key if needed
if not enc_manager.key_exists():
    enc_manager.generate_key()
    print("New encryption key generated")
```

### 3. Email Configuration
```python
# Configure email service
from src.utils.email_service import EmailService, EmailConfig

# Create email configuration
config = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password",
    use_tls=True
)

# Initialize email service
email_service = EmailService(config)

# Test email configuration
print(f"Email config: {'VALID' if email_service.validate_config() else 'INVALID'}")
```

### 4. Performance Configuration
```python
# Configure performance optimizations
from src.utils.performance_utils import get_performance_manager

# Get performance manager
perf_manager = get_performance_manager()

# Configure memory settings
perf_manager.set_memory_limit(512 * 1024 * 1024)  # 512MB

# Enable lazy loading
perf_manager.enable_lazy_loading(True)

# Test performance monitoring
report = perf_manager.get_performance_report()
print(f"Performance monitoring: {'ACTIVE' if report else 'INACTIVE'}")
```

### 5. Footer Configuration
```python
# Configure footer generator
from src.utils.footer_generator import FooterGenerator

# Initialize footer generator
footer_gen = FooterGenerator()

# Test footer generation
test_order_data = {
    'order_number': 'TEST001',
    'created_at': '2023-12-09 12:00:00'
}
test_user_data = {
    'username': 'testuser'
}

footer = footer_gen.generate_footer('receipt', test_order_data, test_user_data)
print(f"Footer generation: {'SUCCESS' if footer else 'FAILED'}")
```

### 6. KOT Configuration
```python
# Configure KOT system
from src.ui.kot_window import KOTWindow
from src.utils.sound_manager import sound_manager

# Test KOT window
import tkinter as tk
root = tk.Tk()

try:
    kot_window = KOTWindow(parent=root)
    print("KOT window: SUCCESS")
except Exception as e:
    print(f"KOT window: FAILED - {e}")

# Test sound manager
if sound_manager:
    print("Sound manager: ACTIVE")
else:
    print("Sound manager: INACTIVE")
```

---

## Testing the Installation

### 1. Desktop Version Test
```bash
# Run desktop application
python main.py

# Check for errors in logs
tail -f logs/pos_app.log

# Test main features
python -c "
from src.utils.image_handler import ImageHandler
from src.utils.encryption import get_encryption_manager
from src.utils.email_service import EmailService
from src.utils.performance_utils import get_performance_manager
from src.utils.footer_generator import FooterGenerator

print('Desktop version components loaded successfully')
"
```

### 2. Web Version Test
```bash
# Navigate to web directory
cd web_cloud

# Run Flask application
python app.py

# Test in development mode
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py

# Test health endpoint
curl http://localhost:5000/health

# Expected response:
# {
#     "status": "healthy",
#     "timestamp": "2023-12-09T12:00:00.000Z",
#     "version": "1.0.0"
# }
```

### 3. Integration Tests
```bash
# Run comprehensive test suite
python comprehensive_feature_tests.py

# Check test results
# All tests should pass
# KOT window test should show: PASSED
# Performance tests should show memory usage within limits
# Email tests should show successful configuration
```

---

## Production Deployment

### 1. Web Server Configuration
```nginx
# Nginx configuration for Flask app
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/web_cloud/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Systemd Service
```ini
# /etc/systemd/system/pos-web.service
[Unit]
Description=POS Web Application
After=network.target

[Service]
Type=simple
User=pos
WorkingDirectory=/path/to/restaurant-pos/web_cloud
Environment=PATH=/path/to/pos_env/bin
ExecStart=/path/to/pos_env/bin/gunicorn app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. SSL Configuration
```bash
# Generate SSL certificate
certbot --nginx -d your-domain.com

# Configure Nginx for SSL
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## Troubleshooting

### Common Installation Issues

#### 1. Python Module Not Found
```bash
# Error: ModuleNotFoundError: No module named 'PIL'
# Solution: Install Pillow
pip install Pillow

# Error: ModuleNotFoundError: No module named 'cryptography'
# Solution: Install cryptography
pip install cryptography

# Error: ModuleNotFoundError: No module named 'flask'
# Solution: Install Flask
pip install flask
```

#### 2. Database Connection Issues
```bash
# Error: sqlite3.OperationalError: unable to open database file
# Solution: Check permissions
ls -la restaurant_pos.db
chmod 664 restaurant_pos.db

# Error: sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
# Solution: Check PostgreSQL service
sudo systemctl status postgresql
sudo systemctl start postgresql
```

#### 3. Permission Denied Errors
```bash
# Error: PermissionError: [Errno 13] Permission denied
# Solution: Check file permissions
sudo chown -R $USER:$USER /path/to/restaurant-pos
chmod -R 755 /path/to/restaurant-pos
```

#### 4. Port Already in Use
```bash
# Error: [Errno 98] Address already in use
# Solution: Find and kill process
lsof -i :5000
kill -9 <PID>

# Or use different port
export FLASK_RUN_PORT=5001
python app.py
```

### Verification Commands
```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "(Pillow|cryptography|flask|sqlalchemy)"

# Check database connection
python -c "from src.models.database import DatabaseManager; print('DB OK')"

# Check configuration files
ls -la src/config/
cat src/config/performance_config.json

# Check logs
tail -f logs/pos_app.log
tail -f logs/encryption.log
tail -f logs/email.log
```

---

## Post-Installation Checklist

### Security
- [ ] Encryption key generated and secured
- [ ] Database permissions configured correctly
- [ ] SSL certificates installed (for production)
- [ ] Environment variables set correctly
- [ ] Default admin password changed

### Performance
- [ ] Memory limits configured
- [ ] Lazy loading enabled
- [ ] Pagination configured
- [ ] Image optimization enabled
- [ ] Database indexes created

### Features
- [ ] Image upload working with all formats
- [ ] Email service configured and tested
- [ ] Footer generation working
- [ ] KOT window functional
- [ ] Performance monitoring active
- [ ] All integration tests passing

### Monitoring
- [ ] Log rotation configured
- [ ] Health checks accessible
- [ ] Backup system scheduled
- [ ] Error notifications configured
- [ ] Performance metrics collecting

---

## Support and Maintenance

### Regular Maintenance
1. **Weekly**: Review error logs, check disk space
2. **Monthly**: Update dependencies, rotate encryption keys
3. **Quarterly**: Performance review, security audit
4. **Yearly**: Complete system review, update documentation

### Getting Help
- **Documentation**: Check `docs/` directory
- **Issues**: Report bugs at GitHub repository
- **Community**: Join discussion forums for support
- **Professional**: Contact support team for enterprise assistance

---

This installation guide provides comprehensive instructions for setting up the POS system with all new features. Follow each step carefully and verify each component before proceeding to the next.

For specific issues not covered in this guide, refer to the Troubleshooting Guide or contact the support team.