import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant_pos.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Upload configuration
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # GST Configuration
    CGST_RATE = 0.025  # 2.5%
    SGST_RATE = 0.025  # 2.5%
    TOTAL_GST_RATE = 0.05  # 5%
    
    # Currency
    CURRENCY_SYMBOL = '₹'
    DECIMAL_PLACES = 2
    
    # Pagination
    ITEMS_PER_PAGE = 50
    
    # Export settings
    EXPORT_FOLDER = 'exports'
    
    # POS Settings
    DEFAULT_RESTAURANT_NAME = 'Restaurant POS'
    DEFAULT_TAX_RATE = 5.0
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
    RAZORPAY_TEST_MODE = os.environ.get('RAZORPAY_TEST_MODE', 'True').lower() == 'true'
    
    # Security Configuration
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},
        'auth': {'requests': 5, 'window': 300},
        'api': {'requests': 200, 'window': 60},
        'upload': {'requests': 10, 'window': 300}
    }
    IP_BLOCK_DURATION = int(os.environ.get('IP_BLOCK_DURATION', 3600))
    MAX_FAILED_ATTEMPTS = int(os.environ.get('MAX_FAILED_ATTEMPTS', 5))
    SESSION_SALT = os.environ.get('SESSION_SALT', 'pos_session_salt')
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'False').lower() == 'true'
    
    # Offline Configuration
    OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'False').lower() == 'true'
    SYNC_INTERVAL = int(os.environ.get('SYNC_INTERVAL', 30))
    MAX_RETRY_ATTEMPTS = int(os.environ.get('MAX_RETRY_ATTEMPTS', 3))
    
    # Base URL for API callbacks
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
