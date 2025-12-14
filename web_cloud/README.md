# Flask POS - Restaurant Management System

A modern, web-based Point of Sale (POS) system for restaurants with GST compliance, built using Flask, Alpine.js, and Bootstrap.

## 🚀 Features

### Core Features

- **Multi-Order Management**: Handle multiple orders simultaneously with tabbed interface
- **GST-Compliant Billing**: Automatic tax calculations (2.5% CGST + 2.5% SGST)
- **Menu Management**: Full CRUD operations with categories and stock tracking
- **Table Management**: Visual table layout and status tracking
- **Inventory Management**: Stock tracking with low-stock alerts
- **KOT System**: Real-time Kitchen Order Ticket management
- **GST Reports**: GSTR-1 and GSTR-3B compliance reports
- **Export Functionality**: CSV and PDF export capabilities
- **Mobile Responsive**: Works seamlessly on all devices

### Enhanced Features (NEW!)

- **🔐 Advanced Form Validation**: Comprehensive form validation with custom validators for GST, password strength, phone numbers, and business logic
- **🍪 Advanced Session Management**: Session fingerprinting, timeout management, concurrent session limits, and CSRF protection
- **📱 Full Offline Support**: Complete offline functionality with SQLite storage and automatic synchronization when online
- **🛡️ Enterprise Security**: Multi-layer security with rate limiting, IP blocking, suspicious activity detection, and comprehensive audit logging
- **💳 Razorpay Integration**: Complete payment gateway integration with multiple payment methods (Card, UPI, Net Banking, Wallet)
- **🔄 Automatic Sync**: Intelligent synchronization with conflict resolution, retry logic, and webhook processing
- **📊 Enhanced Monitoring**: Real-time performance monitoring, security event tracking, and sync status dashboard

### Technical Features

- **Modern Stack**: Flask 2.3.3 + Alpine.js + Bootstrap 5
- **Database**: SQLAlchemy with SQLite/PostgreSQL support + Offline SQLite storage
- **Real-time Updates**: Auto-refresh KOT system + Background sync processing
- **Advanced Security**: CSRF protection, session fingerprinting, rate limiting, IP blocking
- **Payment Processing**: Razorpay integration with signature verification
- **Offline-First Architecture**: Complete offline functionality with automatic sync
- **ES5 Compatible**: JavaScript works on all browsers

## 📋 Requirements

### System Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 2GB RAM minimum
- 100MB disk space

### Python Dependencies

```
# Core Flask
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
Werkzeug==2.3.7

# Database & Forms
SQLAlchemy==2.0.21
WTForms==3.0.1
email-validator==2.1.0

# Security & Encryption
Flask-Bcrypt==1.0.1
cryptography>=41.0.0

# File Handling & Export
python-dotenv==1.0.0
ReportLab==4.0.4
Pillow>=9.0.0
openpyxl==3.1.2

# API & Communication
requests>=2.31.0

# Date/Time
python-dateutil==2.8.2

# Development
pytest==7.4.2
pytest-flask==1.2.0
```

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd posmvp/web_cloud
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
python init_db.py
```

### 5. Run Application

```bash
python app.py
```

### 6. Access Application

Open browser and navigate to: `http://localhost:5000`

## 🔑 Default Login

- **Username**: `admin`
- **Password**: `admin123`

⚠️ **Important**: Change the default password after first login!

## 📱 Usage

### Getting Started

1. **Login**: Use default credentials to access the system
2. **Dashboard**: View overview of orders, sales, and inventory
3. **Orders**: Create and manage customer orders
4. **Menu**: Add/edit menu items and categories
5. **Tables**: Manage restaurant tables and seating
6. **KOT**: Monitor kitchen orders in real-time
7. **Inventory**: Track stock levels and manage supplies
8. **Reports**: Generate GST-compliant reports

### Order Management

1. Select order type (Dine-in/Takeaway/Delivery)
2. Choose table (for dine-in orders)
3. Add items from menu categories
4. Apply discounts if needed
5. Save order and proceed to payment
6. Print KOT automatically sent to kitchen

### GST Compliance

- Automatic tax calculation at 5% (2.5% CGST + 2.5% SGST)
- GST reports for filing (GSTR-1, GSTR-3B)
- Tax breakdown on receipts
- Export data in GST-compliant format

## 🔐 Enhanced Security Features

### Multi-Layer Security Protection

- **🛡️ CSRF Protection**: Token-based CSRF protection on all forms
- **🚦 Rate Limiting**: Configurable rate limits per endpoint (auth: 5/5min, API: 200/min)
- **🚫 IP Blocking**: Automatic IP blocking for suspicious activity
- **🔍 Suspicious Activity Detection**: Pattern-based threat detection (XSS, SQL injection, etc.)
- **📝 Security Event Logging**: Complete audit trail with severity levels
- **🔐 Session Security**: Fingerprinting, timeout, concurrent session limits
- **🔒 Password Security**: Strong password requirements and hashing
- **🛡️ Input Validation**: Comprehensive input sanitization and validation

### Security Monitoring

Access security dashboard at `/api/security/status` to monitor:
- Active security events
- Blocked IPs and rate limit violations
- Suspicious activity patterns
- Security statistics and trends

## 📱 Offline Support & Synchronization

### Offline-First Architecture

- **💾 Local Storage**: SQLite database for complete offline functionality
- **🔄 Automatic Sync**: Background synchronization when online
- **⚡ Conflict Resolution**: Smart handling of data conflicts
- **📊 Sync Status**: Real-time sync monitoring and management
- **🔄 Retry Logic**: Automatic retry with exponential backoff

### Offline Capabilities

Continue working during internet outages:
- ✅ Create and manage orders
- ✅ Process payments
- ✅ Update menu items and categories
- ✅ Manage table status
- ✅ Generate reports (stored locally)

### Sync Management

Access sync status at `/api/offline/status`:
- Pending orders and payments
- Failed sync items
- Last successful sync time
- Queue status and retry attempts

## 💳 Razorpay Payment Integration

### Supported Payment Methods

- **💳 Credit/Debit Cards**: All major cards supported
- **📱 UPI**: Unified Payments Interface
- **🏦 Net Banking**: All major Indian banks
- **👛 Wallets**: Popular digital wallets

### Payment Features

- **🔒 Secure Processing**: Signature verification and webhook validation
- **💰 Amount Validation**: Configurable min/max limits (₹1.00 - ₹100,000.00)
- **🔄 Refund Support**: Complete refund processing
- **📧 Notifications**: Automatic payment status updates
- **🧪 Test Mode**: Development and testing support

### Payment Flow

1. Order creation → Razorpay order generation
2. Customer payment → Razorpay payment capture
3. Webhook processing → Automatic status updates
4. Order completion → Final order processing

## 📋 Enhanced Form Validation

### Comprehensive Validation System

- **✅ Business Logic Validation**: GST format, phone numbers, email validation
- **🔒 Security Validation**: Password strength, XSS prevention
- **📊 Data Validation**: Type checking, range validation, required fields
- **🌐 Input Sanitization**: Automatic cleaning and encoding
- **⚠️ Custom Error Messages**: User-friendly error feedback

### Available Forms

- **Authentication**: Login, Registration, Password Change
- **Menu Management**: Categories, Menu Items with validation
- **Order Management**: Orders, Payments with business rules
- **Settings**: Restaurant settings with validation
- **User Management**: User creation and editing

## 🧪 Testing

Run the comprehensive test suite to verify installation:

```bash
# Basic functionality tests
python test_app.py

# Enhanced features tests
python test_enhanced_features.py
```

This will run:

- Database connection tests
- Model validation tests
- Route functionality tests
- Template and static file checks
- GST calculation verification
- **NEW**: Form validation tests (25+ test cases)
- **NEW**: Session management tests
- **NEW**: Security feature tests
- **NEW**: Offline functionality tests
- **NEW**: Razorpay integration tests
- **NEW**: Integration tests between all features

## 📊 Reports

### Available Reports

- **Daily Sales**: Day-wise sales summary with GST
- **Monthly Sales**: Monthly sales analysis
- **GSTR-1**: Outward supplies report
- **GSTR-3B**: Tax summary and ITC details
- **Item-wise**: Sales by menu items
- **Category-wise**: Sales by categories

### Export Options

- **CSV**: For Excel/Google Sheets
- **PDF**: Print-ready reports
- **Print**: Direct printer output

## 🔧 Configuration

### Database Settings

Edit `config.py` to change database:

```python
# SQLite (default)
SQLALCHEMY_DATABASE_URI = 'sqlite:///restaurant_pos.db'

# PostgreSQL
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/pos_db'

# MySQL
SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/pos_db'
```

### Razorpay Configuration

Set up Razorpay payment gateway:

```python
# Add to config.py or environment variables
RAZORPAY_KEY_ID = 'your_razorpay_key_id'
RAZORPAY_KEY_SECRET = 'your_razorpay_key_secret'
RAZORPAY_WEBHOOK_SECRET = 'your_webhook_secret'

# Payment settings
MIN_PAYMENT_AMOUNT = 1.00  # ₹1.00 minimum
MAX_PAYMENT_AMOUNT = 100000.00  # ₹100,000.00 maximum
```

### Security Configuration

Configure security settings in `config.py`:

```python
# Rate limiting
RATE_LIMIT_AUTH = 5  # requests per 5 minutes for auth
RATE_LIMIT_API = 200  # requests per minute for API
RATE_LIMIT_DEFAULT = 100  # requests per minute default

# IP blocking
IP_BLOCK_DURATION = 300  # seconds (5 minutes)
MAX_FAILED_ATTEMPTS = 5  # before IP blocking

# Session settings
SESSION_TIMEOUT = 3600  # seconds (1 hour)
MAX_CONCURRENT_SESSIONS = 3  # per user
```

### Offline Sync Configuration

Configure offline synchronization:

```python
# Sync settings
SYNC_INTERVAL = 30  # seconds between sync attempts
MAX_RETRY_ATTEMPTS = 3  # maximum retry attempts
OFFLINE_DB_PATH = 'offline_data.db'  # offline database location
```

### Restaurant Settings

Update restaurant information in Settings menu:

- Restaurant name and address
- GST number
- Contact details
- Receipt footer
- Tax rates
- Payment method configuration
- Security preferences

## 📱 Mobile Usage

The application is fully mobile-responsive:

### Phone/Tablet Features

- Touch-friendly interface
- Swipe gestures for order tabs
- Optimized layouts
- Mobile KOT view

### Recommended Devices

- **Counter**: Desktop/Laptop
- **Floor Staff**: Tablets/iPads
- **Kitchen**: Large monitor/tablet
- **Mobile**: Managers on the go

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Error

```bash
# Check database file exists
ls -la restaurant_pos.db

# Reinitialize database
python init_db.py
```

#### Missing Dependencies

```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

#### JavaScript Errors

- Check browser console (F12)
- Ensure all static files are loading
- Clear browser cache

#### Permission Issues

```bash
# Linux/Mac - Fix permissions
chmod +x init_db.py
chmod +x app.py

# Windows - Run as administrator
```

### Log Files

Check application logs in:

- Console output (when running `python app.py`)
- Browser developer tools
- Web server logs (if using production server)

## 🔄 Updates

### Updating the Application

1. **Backup Database**: Copy `restaurant_pos.db`
2. **Update Code**: Pull latest changes
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Run Migrations**: If database schema changed
5. **Test**: Run `python test_app.py`

### Data Backup

Regular backups are recommended:

```bash
# Backup database
cp restaurant_pos.db backup/restaurant_pos_$(date +%Y%m%d).db

# Backup settings
cp config.py backup/config_$(date +%Y%m%d).py
```

## 🛡️ Security

### Production Deployment

1. **Change Default Password**: Immediately update admin password
2. **Use HTTPS**: Configure SSL certificate
3. **Environment Variables**: Use .env file for secrets
4. **Regular Updates**: Keep dependencies updated
5. **Firewall**: Restrict access to production server

### Security Features

- CSRF protection enabled
- Session management
- Password hashing
- SQL injection protection
- XSS prevention
- Input validation

## 📞 Support

### Getting Help

1. **Documentation**: Check this README first
2. **Logs**: Review application logs
3. **Test Suite**: Run `python test_app.py`
4. **GitHub Issues**: Report bugs and feature requests

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Flask**: Web framework
- **Alpine.js**: Reactive JavaScript framework
- **Bootstrap**: UI framework
- **Font Awesome**: Icons
- **ReportLab**: PDF generation
- **SQLAlchemy**: Database ORM

## 🌟 Enhanced Features Summary

The Flask POS system has been significantly enhanced with enterprise-grade features:

### ✅ What's New in Version 2.0

- **🔐 Advanced Security**: Multi-layer protection with rate limiting, IP blocking, and activity monitoring
- **📱 Offline-First**: Complete offline functionality with automatic synchronization
- **💳 Modern Payments**: Razorpay integration with multiple payment methods
- **📋 Smart Forms**: Comprehensive validation with business logic enforcement
- **🍪 Session Management**: Advanced session security with fingerprinting
- **🔄 Intelligent Sync**: Conflict resolution and retry logic
- **📊 Real-time Monitoring**: Performance, security, and sync dashboards

### 🚀 Production Ready

The enhanced system is now production-ready with:
- Enterprise-grade security
- Offline resilience
- Modern payment processing
- Comprehensive monitoring
- Automatic data synchronization

### 📚 Additional Documentation

For detailed technical documentation, see:
- [`ENHANCED_FEATURES.md`](ENHANCED_FEATURES.md) - Technical implementation details
- [`USER_GUIDE.md`](USER_GUIDE.md) - Complete user guide
- [`ENHANCED_FEATURES_SUMMARY.md`](ENHANCED_FEATURES_SUMMARY.md) - Implementation summary

---

**Version**: 2.0.0 Enhanced Features
**Last Updated**: December 2024
**Developer**: Restaurant POS Team
**Status**: ✅ PRODUCTION READY
