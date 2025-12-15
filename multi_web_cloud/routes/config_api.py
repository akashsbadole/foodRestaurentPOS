"""
Configuration Management API Routes for Flask POS Application
Provides comprehensive configuration management endpoints
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.session_manager import session_manager
from utils.security_manager import security_manager
from utils.offline_manager import offline_manager
from utils.razorpay_manager import razorpay_manager
from utils.form_validator import form_validator

# Import models for settings
from models import Settings

# Create blueprint
config_api_bp = Blueprint('config_api', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Decorators for API security
def require_api_key(f):
    """Decorator to require API key for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_KEY', 'default_api_key'):
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': 'Valid API key required for this endpoint'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_valid_session_api(f):
    """Decorator to require valid session for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'error': 'Session expired or invalid',
                'message': 'Please log in again',
                'redirect': '/auth/login'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_admin_session(f):
    """Decorator to require admin session for configuration endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'error': 'Session expired or invalid',
                'message': 'Please log in again',
                'redirect': '/auth/login'
            }), 401
        
        # Check if user is admin (simplified check)
        user_id = session.get('user_id')
        if not user_id or user_id != 1:  # Assuming user ID 1 is admin
            return jsonify({
                'success': False,
                'error': 'Access denied',
                'message': 'Admin privileges required for this endpoint'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_config_api(f):
    """Decorator for rate limiting configuration API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for config API
        if not security_manager._check_rate_limit(client_ip, 'config_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many configuration requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@config_api_bp.route('/api/config/validation', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def get_validation_config():
    """
    Get validation configuration
    
    Response:
    {
        "success": true,
        "config": {
            "business_rules": {...},
            "password_requirements": {...},
            "file_upload_limits": {...}
        }
    }
    """
    try:
        # Get validation configuration from form validator
        business_rules = form_validator.business_rules
        
        # Define password requirements
        password_requirements = {
            "min_length": 8,
            "max_length": 128,
            "require_lowercase": True,
            "require_uppercase": True,
            "require_digits": True,
            "require_special_chars": True,
            "forbidden_patterns": [
                "password", "123456", "qwerty", "abc123",
                "password123", "admin", "letmein", "welcome"
            ],
            "no_repeated_chars": True,
            "no_sequential_chars": True,
            "no_keyboard_patterns": True
        }
        
        # Define file upload limits
        file_upload_limits = {
            "max_size_mb": 5,
            "allowed_extensions": [
                "jpg", "jpeg", "png", "gif", "pdf", 
                "txt", "xls", "xlsx", "doc", "docx"
            ],
            "allowed_mime_types": [
                "image/jpeg", "image/png", "image/gif",
                "application/pdf", "text/plain",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ]
        }
        
        # Get validation settings from database
        validation_settings = _get_validation_settings_from_db()
        
        config = {
            'business_rules': business_rules,
            'password_requirements': password_requirements,
            'file_upload_limits': file_upload_limits,
            'custom_settings': validation_settings
        }
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_validation_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Validation config retrieval error',
            'message': 'An error occurred while retrieving validation configuration'
        }), 500

@config_api_bp.route('/api/config/validation', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def update_validation_config():
    """
    Update validation configuration
    
    Request Body:
    {
        "business_rules": {...},
        "password_requirements": {...},
        "file_upload_limits": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Validation configuration updated successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_validation_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Update validation configuration
        success = _update_validation_config_in_db(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration update failed',
                'message': 'Unable to update validation configuration'
            }), 500
        
        # Log configuration update
        security_manager._log_security_event(
            'VALIDATION_CONFIG_UPDATED',
            security_manager._get_client_ip(),
            "Validation configuration updated by admin",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'message': 'Validation configuration updated successfully',
            'updated_sections': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_validation_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration update error',
            'message': 'An error occurred while updating validation configuration'
        }), 500

@config_api_bp.route('/api/config/session', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def get_session_config():
    """
    Get session configuration
    
    Response:
    {
        "success": true,
        "config": {
            "timeout_hours": 8,
            "max_sessions_per_user": 3,
            "security_settings": {...}
        }
    }
    """
    try:
        # Get session configuration from session manager
        config = {
            'timeout_hours': session_manager.session_timeout.total_seconds() / 3600,
            'max_sessions_per_user': session_manager.max_sessions_per_user,
            'security_settings': {
                'fingerprint_validation': True,
                'ip_validation': True,
                'user_agent_validation': True,
                'csrf_protection': True
            }
        }
        
        # Get session settings from database
        session_settings = _get_session_settings_from_db()
        config['custom_settings'] = session_settings
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_session_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Session config retrieval error',
            'message': 'An error occurred while retrieving session configuration'
        }), 500

@config_api_bp.route('/api/config/session', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def update_session_config():
    """
    Update session configuration
    
    Request Body:
    {
        "timeout_hours": 8,
        "max_sessions_per_user": 3,
        "security_settings": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Session configuration updated successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_session_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Update session configuration
        success = _update_session_config_in_db(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration update failed',
                'message': 'Unable to update session configuration'
            }), 500
        
        # Update session manager settings
        if 'timeout_hours' in data:
            session_manager.session_timeout = datetime(hours=data['timeout_hours'])
        
        if 'max_sessions_per_user' in data:
            session_manager.max_sessions_per_user = data['max_sessions_per_user']
        
        # Log configuration update
        security_manager._log_security_event(
            'SESSION_CONFIG_UPDATED',
            security_manager._get_client_ip(),
            "Session configuration updated by admin",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'message': 'Session configuration updated successfully',
            'updated_sections': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_session_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration update error',
            'message': 'An error occurred while updating session configuration'
        }), 500

@config_api_bp.route('/api/config/security', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def get_security_config():
    """
    Get security configuration
    
    Response:
    {
        "success": true,
        "config": {
            "rate_limits": {...},
            "ip_blocking": {...},
            "security_headers": {...}
        }
    }
    """
    try:
        # Get security configuration from security manager
        config = {
            'rate_limits': security_manager.rate_limits,
            'ip_blocking': {
                'enabled': True,
                'default_duration_hours': security_manager.ip_block_duration / 3600,
                'max_failed_attempts': security_manager.max_failed_attempts
            },
            'security_headers': {
                'x_frame_options': 'DENY',
                'x_content_type_options': 'nosniff',
                'x_xss_protection': '1; mode=block',
                'strict_transport_security': True,
                'content_security_policy': True
            },
            'advanced_threat_detection': {
                'enabled': True,
                'brute_force_detection': True,
                'rapid_request_detection': True,
                'unusual_user_agent_detection': True
            }
        }
        
        # Get security settings from database
        security_settings = _get_security_settings_from_db()
        config['custom_settings'] = security_settings
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_security_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Security config retrieval error',
            'message': 'An error occurred while retrieving security configuration'
        }), 500

@config_api_bp.route('/api/config/security', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def update_security_config():
    """
    Update security configuration
    
    Request Body:
    {
        "rate_limits": {...},
        "ip_blocking": {...},
        "security_headers": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Security configuration updated successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_security_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Update security configuration
        success = _update_security_config_in_db(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration update failed',
                'message': 'Unable to update security configuration'
            }), 500
        
        # Update security manager settings
        if 'rate_limits' in data:
            security_manager.rate_limits.update(data['rate_limits'])
        
        if 'ip_blocking' in data:
            ip_blocking = data['ip_blocking']
            if 'default_duration_hours' in ip_blocking:
                security_manager.ip_block_duration = ip_blocking['default_duration_hours'] * 3600
            if 'max_failed_attempts' in ip_blocking:
                security_manager.max_failed_attempts = ip_blocking['max_failed_attempts']
        
        # Log configuration update
        security_manager._log_security_event(
            'SECURITY_CONFIG_UPDATED',
            security_manager._get_client_ip(),
            "Security configuration updated by admin",
            'high'
        )
        
        return jsonify({
            'success': True,
            'message': 'Security configuration updated successfully',
            'updated_sections': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_security_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration update error',
            'message': 'An error occurred while updating security configuration'
        }), 500

@config_api_bp.route('/api/config/offline', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def get_offline_config():
    """
    Get offline configuration
    
    Response:
    {
        "success": true,
        "config": {
            "sync_settings": {...},
            "cache_settings": {...},
            "conflict_resolution": {...}
        }
    }
    """
    try:
        # Get offline configuration from offline manager
        config = {
            'sync_settings': {
                'auto_sync_enabled': True,
                'sync_interval_seconds': offline_manager.sync_interval,
                'max_retry_attempts': offline_manager.max_retry_attempts,
                'conflict_resolution_strategy': 'server_wins'
            },
            'cache_settings': {
                'menu_items_cache_ttl': 3600,  # seconds
                'categories_cache_ttl': 3600,
                'tables_cache_ttl': 3600,
                'max_cache_size_mb': 100
            },
            'conflict_resolution': {
                'strategy': 'server_wins',
                'auto_resolve': True,
                'manual_review_required': False
            }
        }
        
        # Get offline settings from database
        offline_settings = _get_offline_settings_from_db()
        config['custom_settings'] = offline_settings
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_offline_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Offline config retrieval error',
            'message': 'An error occurred while retrieving offline configuration'
        }), 500

@config_api_bp.route('/api/config/offline', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def update_offline_config():
    """
    Update offline configuration
    
    Request Body:
    {
        "sync_settings": {...},
        "cache_settings": {...},
        "conflict_resolution": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Offline configuration updated successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_offline_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Update offline configuration
        success = _update_offline_config_in_db(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration update failed',
                'message': 'Unable to update offline configuration'
            }), 500
        
        # Update offline manager settings
        if 'sync_settings' in data:
            sync_settings = data['sync_settings']
            if 'sync_interval_seconds' in sync_settings:
                offline_manager.sync_interval = sync_settings['sync_interval_seconds']
            if 'max_retry_attempts' in sync_settings:
                offline_manager.max_retry_attempts = sync_settings['max_retry_attempts']
        
        # Log configuration update
        security_manager._log_security_event(
            'OFFLINE_CONFIG_UPDATED',
            security_manager._get_client_ip(),
            "Offline configuration updated by admin",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'message': 'Offline configuration updated successfully',
            'updated_sections': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_offline_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration update error',
            'message': 'An error occurred while updating offline configuration'
        }), 500

@config_api_bp.route('/api/config/payment', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def get_payment_config():
    """
    Get payment configuration
    
    Response:
    {
        "success": true,
        "config": {
            "razorpay_settings": {...},
            "payment_methods": {...},
            "transaction_settings": {...}
        }
    }
    """
    try:
        # Get payment configuration from Razorpay manager
        config = {
            'razorpay_settings': razorpay_manager.get_configuration_info(),
            'payment_methods': razorpay_manager.get_payment_methods(),
            'transaction_settings': {
                'auto_capture': True,
                'refund_policy': 'manual_approval',
                'webhook_enabled': True,
                'webhook_url': '/razorpay/webhook'
            },
            'fee_settings': {
                'card_fee_percentage': 2.0,
                'upi_fee_percentage': 1.99,
                'netbanking_fee_percentage': 2.0,
                'wallet_fee_percentage': 2.0
            }
        }
        
        # Get payment settings from database
        payment_settings = _get_payment_settings_from_db()
        config['custom_settings'] = payment_settings
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_payment_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Payment config retrieval error',
            'message': 'An error occurred while retrieving payment configuration'
        }), 500

@config_api_bp.route('/api/config/payment', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def update_payment_config():
    """
    Update payment configuration
    
    Request Body:
    {
        "razorpay_settings": {...},
        "payment_methods": {...},
        "transaction_settings": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Payment configuration updated successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_payment_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Update payment configuration
        success = _update_payment_config_in_db(data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration update failed',
                'message': 'Unable to update payment configuration'
            }), 500
        
        # Log configuration update
        security_manager._log_security_event(
            'PAYMENT_CONFIG_UPDATED',
            security_manager._get_client_ip(),
            "Payment configuration updated by admin",
            'high'
        )
        
        return jsonify({
            'success': True,
            'message': 'Payment configuration updated successfully',
            'updated_sections': list(data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_payment_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration update error',
            'message': 'An error occurred while updating payment configuration'
        }), 500

@config_api_bp.route('/api/config/export', methods=['GET'])
@rate_limit_config_api
@require_admin_session
def export_config():
    """
    Export all configuration
    
    Query Parameters:
    - format: Export format (json, yaml)
    
    Response:
    {
        "success": true,
        "export_url": "/api/config/download/export_123456"
    }
    """
    try:
        # Get query parameters
        export_format = request.args.get('format', 'json')
        
        # Validate export format
        if export_format not in ['json', 'yaml']:
            return jsonify({
                'success': False,
                'error': 'Invalid export format',
                'message': 'Format must be one of: json, yaml'
            }), 400
        
        # Get all configuration
        all_config = {
            'validation': _get_validation_config_data(),
            'session': _get_session_config_data(),
            'security': _get_security_config_data(),
            'offline': _get_offline_config_data(),
            'payment': _get_payment_config_data()
        }
        
        # Generate export ID
        export_id = f"export_{datetime.utcnow().timestamp()}"
        
        # Export configuration
        export_url = _export_configuration(export_id, all_config, export_format)
        
        # Log configuration export
        security_manager._log_security_event(
            'CONFIG_EXPORTED',
            security_manager._get_client_ip(),
            f"Configuration exported in {export_format} format",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'export_id': export_id,
            'export_url': export_url,
            'format': export_format,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in export_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration export error',
            'message': 'An error occurred while exporting configuration'
        }), 500

@config_api_bp.route('/api/config/import', methods=['POST'])
@rate_limit_config_api
@require_admin_session
def import_config():
    """
    Import configuration
    
    Request Body:
    {
        "config_data": {...},
        "merge_strategy": "replace" // or "merge"
    }
    
    Response:
    {
        "success": true,
        "message": "Configuration imported successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        config_data = data.get('config_data', {})
        merge_strategy = data.get('merge_strategy', 'replace')
        
        if not config_data:
            return jsonify({
                'success': False,
                'error': 'Missing configuration data',
                'message': 'config_data is required'
            }), 400
        
        # Validate merge strategy
        if merge_strategy not in ['replace', 'merge']:
            return jsonify({
                'success': False,
                'error': 'Invalid merge strategy',
                'message': 'merge_strategy must be one of: replace, merge'
            }), 400
        
        # Validate configuration data
        validation_errors = _validate_import_config(config_data)
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Invalid configuration',
                'message': 'Configuration validation failed',
                'errors': validation_errors
            }), 400
        
        # Import configuration
        success = _import_configuration(config_data, merge_strategy)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Configuration import failed',
                'message': 'Unable to import configuration'
            }), 500
        
        # Log configuration import
        security_manager._log_security_event(
            'CONFIG_IMPORTED',
            security_manager._get_client_ip(),
            f"Configuration imported with {merge_strategy} strategy",
            'high'
        )
        
        return jsonify({
            'success': True,
            'message': 'Configuration imported successfully',
            'merge_strategy': merge_strategy,
            'imported_sections': list(config_data.keys()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in import_config: {e}")
        return jsonify({
            'success': False,
            'error': 'Configuration import error',
            'message': 'An error occurred while importing configuration'
        }), 500

# Helper functions

def _get_validation_settings_from_db() -> Dict[str, Any]:
    """Get validation settings from database"""
    try:
        settings = {}
        
        # Get validation-related settings from database
        validation_settings = Settings.query.filter(
            Settings.key.like('validation_%')
        ).all()
        
        for setting in validation_settings:
            settings[setting.key] = setting.value
        
        return settings
    except Exception as e:
        logger.error(f"Error in _get_validation_settings_from_db: {e}")
        return {}

def _update_validation_config_in_db(config_data: Dict[str, Any]) -> bool:
    """Update validation configuration in database"""
    try:
        for section, settings in config_data.items():
            for key, value in settings.items():
                setting_key = f"validation_{section}_{key}"
                
                # Update or create setting
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Settings(key=setting_key, value=str(value))
                    db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error in _update_validation_config_in_db: {e}")
        db.session.rollback()
        return False

def _validate_validation_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate validation configuration"""
    errors = []
    
    try:
        # Validate business rules
        if 'business_rules' in config_data:
            business_rules = config_data['business_rules']
            for rule_name, rule_config in business_rules.items():
                if 'pattern' in rule_config:
                    # Test if pattern is valid regex
                    try:
                        import re
                        re.compile(rule_config['pattern'])
                    except re.error:
                        errors.append(f"Invalid regex pattern for {rule_name}")
        
        # Validate password requirements
        if 'password_requirements' in config_data:
            password_req = config_data['password_requirements']
            if 'min_length' in password_req:
                min_len = password_req['min_length']
                if not isinstance(min_len, int) or min_len < 1:
                    errors.append("Password min_length must be a positive integer")
            
            if 'max_length' in password_req:
                max_len = password_req['max_length']
                if not isinstance(max_len, int) or max_len < 1:
                    errors.append("Password max_length must be a positive integer")
        
        # Validate file upload limits
        if 'file_upload_limits' in config_data:
            file_limits = config_data['file_upload_limits']
            if 'max_size_mb' in file_limits:
                max_size = file_limits['max_size_mb']
                if not isinstance(max_size, int) or max_size < 1:
                    errors.append("File max_size_mb must be a positive integer")
                elif max_size > 100:
                    errors.append("File max_size_mb should not exceed 100MB")
    
    except Exception as e:
        logger.error(f"Error in _validate_validation_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

def _get_session_settings_from_db() -> Dict[str, Any]:
    """Get session settings from database"""
    try:
        settings = {}
        
        # Get session-related settings from database
        session_settings = Settings.query.filter(
            Settings.key.like('session_%')
        ).all()
        
        for setting in session_settings:
            settings[setting.key] = setting.value
        
        return settings
    except Exception as e:
        logger.error(f"Error in _get_session_settings_from_db: {e}")
        return {}

def _update_session_config_in_db(config_data: Dict[str, Any]) -> bool:
    """Update session configuration in database"""
    try:
        for section, settings in config_data.items():
            for key, value in settings.items():
                setting_key = f"session_{section}_{key}"
                
                # Update or create setting
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Settings(key=setting_key, value=str(value))
                    db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error in _update_session_config_in_db: {e}")
        db.session.rollback()
        return False

def _validate_session_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate session configuration"""
    errors = []
    
    try:
        # Validate timeout settings
        if 'security_settings' in config_data:
            security_settings = config_data['security_settings']
            
            if 'timeout_hours' in security_settings:
                timeout = security_settings['timeout_hours']
                if not isinstance(timeout, (int, float)) or timeout < 0.1 or timeout > 24:
                    errors.append("Session timeout must be between 0.1 and 24 hours")
            
            if 'max_sessions_per_user' in security_settings:
                max_sessions = security_settings['max_sessions_per_user']
                if not isinstance(max_sessions, int) or max_sessions < 1 or max_sessions > 10:
                    errors.append("Max sessions per user must be between 1 and 10")
    
    except Exception as e:
        logger.error(f"Error in _validate_session_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

def _get_security_settings_from_db() -> Dict[str, Any]:
    """Get security settings from database"""
    try:
        settings = {}
        
        # Get security-related settings from database
        security_settings = Settings.query.filter(
            Settings.key.like('security_%')
        ).all()
        
        for setting in security_settings:
            settings[setting.key] = setting.value
        
        return settings
    except Exception as e:
        logger.error(f"Error in _get_security_settings_from_db: {e}")
        return {}

def _update_security_config_in_db(config_data: Dict[str, Any]) -> bool:
    """Update security configuration in database"""
    try:
        for section, settings in config_data.items():
            for key, value in settings.items():
                setting_key = f"security_{section}_{key}"
                
                # Update or create setting
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Settings(key=setting_key, value=str(value))
                    db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error in _update_security_config_in_db: {e}")
        db.session.rollback()
        return False

def _validate_security_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate security configuration"""
    errors = []
    
    try:
        # Validate rate limits
        if 'rate_limits' in config_data:
            rate_limits = config_data['rate_limits']
            for limit_name, limit_config in rate_limits.items():
                if 'requests' in limit_config:
                    requests = limit_config['requests']
                    if not isinstance(requests, int) or requests < 1:
                        errors.append(f"Rate limit requests for {limit_name} must be a positive integer")
                
                if 'window' in limit_config:
                    window = limit_config['window']
                    if not isinstance(window, int) or window < 1:
                        errors.append(f"Rate limit window for {limit_name} must be a positive integer")
        
        # Validate IP blocking settings
        if 'ip_blocking' in config_data:
            ip_blocking = config_data['ip_blocking']
            
            if 'default_duration_hours' in ip_blocking:
                duration = ip_blocking['default_duration_hours']
                if not isinstance(duration, (int, float)) or duration < 0.1 or duration > 168:
                    errors.append("IP block duration must be between 0.1 and 168 hours")
            
            if 'max_failed_attempts' in ip_blocking:
                max_attempts = ip_blocking['max_failed_attempts']
                if not isinstance(max_attempts, int) or max_attempts < 1 or max_attempts > 20:
                    errors.append("Max failed attempts must be between 1 and 20")
    
    except Exception as e:
        logger.error(f"Error in _validate_security_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

def _get_offline_settings_from_db() -> Dict[str, Any]:
    """Get offline settings from database"""
    try:
        settings = {}
        
        # Get offline-related settings from database
        offline_settings = Settings.query.filter(
            Settings.key.like('offline_%')
        ).all()
        
        for setting in offline_settings:
            settings[setting.key] = setting.value
        
        return settings
    except Exception as e:
        logger.error(f"Error in _get_offline_settings_from_db: {e}")
        return {}

def _update_offline_config_in_db(config_data: Dict[str, Any]) -> bool:
    """Update offline configuration in database"""
    try:
        for section, settings in config_data.items():
            for key, value in settings.items():
                setting_key = f"offline_{section}_{key}"
                
                # Update or create setting
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Settings(key=setting_key, value=str(value))
                    db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error in _update_offline_config_in_db: {e}")
        db.session.rollback()
        return False

def _validate_offline_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate offline configuration"""
    errors = []
    
    try:
        # Validate sync settings
        if 'sync_settings' in config_data:
            sync_settings = config_data['sync_settings']
            
            if 'sync_interval_seconds' in sync_settings:
                interval = sync_settings['sync_interval_seconds']
                if not isinstance(interval, int) or interval < 10 or interval > 3600:
                    errors.append("Sync interval must be between 10 and 3600 seconds")
            
            if 'max_retry_attempts' in sync_settings:
                max_retries = sync_settings['max_retry_attempts']
                if not isinstance(max_retries, int) or max_retries < 1 or max_retries > 10:
                    errors.append("Max retry attempts must be between 1 and 10")
        
        # Validate cache settings
        if 'cache_settings' in config_data:
            cache_settings = config_data['cache_settings']
            
            if 'max_cache_size_mb' in cache_settings:
                cache_size = cache_settings['max_cache_size_mb']
                if not isinstance(cache_size, int) or cache_size < 10 or cache_size > 1000:
                    errors.append("Cache size must be between 10 and 1000 MB")
    
    except Exception as e:
        logger.error(f"Error in _validate_offline_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

def _get_payment_settings_from_db() -> Dict[str, Any]:
    """Get payment settings from database"""
    try:
        settings = {}
        
        # Get payment-related settings from database
        payment_settings = Settings.query.filter(
            Settings.key.like('payment_%')
        ).all()
        
        for setting in payment_settings:
            settings[setting.key] = setting.value
        
        return settings
    except Exception as e:
        logger.error(f"Error in _get_payment_settings_from_db: {e}")
        return {}

def _update_payment_config_in_db(config_data: Dict[str, Any]) -> bool:
    """Update payment configuration in database"""
    try:
        for section, settings in config_data.items():
            for key, value in settings.items():
                setting_key = f"payment_{section}_{key}"
                
                # Update or create setting
                setting = Settings.query.filter_by(key=setting_key).first()
                if setting:
                    setting.value = str(value)
                else:
                    setting = Settings(key=setting_key, value=str(value))
                    db.session.add(setting)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error in _update_payment_config_in_db: {e}")
        db.session.rollback()
        return False

def _validate_payment_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate payment configuration"""
    errors = []
    
    try:
        # Validate transaction settings
        if 'transaction_settings' in config_data:
            transaction_settings = config_data['transaction_settings']
            
            if 'fee_settings' in transaction_settings:
                fee_settings = transaction_settings['fee_settings']
                
                for fee_type, fee_percentage in fee_settings.items():
                    if not isinstance(fee_percentage, (int, float)) or fee_percentage < 0 or fee_percentage > 10:
                        errors.append(f"Fee percentage for {fee_type} must be between 0 and 10")
    
    except Exception as e:
        logger.error(f"Error in _validate_payment_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

def _get_validation_config_data() -> Dict[str, Any]:
    """Get validation configuration data"""
    return {
        'business_rules': form_validator.business_rules,
        'password_requirements': {
            "min_length": 8,
            "max_length": 128,
            "require_lowercase": True,
            "require_uppercase": True,
            "require_digits": True,
            "require_special_chars": True
        },
        'file_upload_limits': {
            "max_size_mb": 5,
            "allowed_extensions": ["jpg", "jpeg", "png", "gif", "pdf", "txt", "xls", "xlsx"]
        }
    }

def _get_session_config_data() -> Dict[str, Any]:
    """Get session configuration data"""
    return {
        'timeout_hours': session_manager.session_timeout.total_seconds() / 3600,
        'max_sessions_per_user': session_manager.max_sessions_per_user,
        'security_settings': {
            'fingerprint_validation': True,
            'ip_validation': True,
            'csrf_protection': True
        }
    }

def _get_security_config_data() -> Dict[str, Any]:
    """Get security configuration data"""
    return {
        'rate_limits': security_manager.rate_limits,
        'ip_blocking': {
            'enabled': True,
            'default_duration_hours': security_manager.ip_block_duration / 3600,
            'max_failed_attempts': security_manager.max_failed_attempts
        },
        'security_headers': {
            'x_frame_options': 'DENY',
            'x_content_type_options': 'nosniff',
            'x_xss_protection': '1; mode=block'
        }
    }

def _get_offline_config_data() -> Dict[str, Any]:
    """Get offline configuration data"""
    return {
        'sync_settings': {
            'auto_sync_enabled': True,
            'sync_interval_seconds': offline_manager.sync_interval,
            'max_retry_attempts': offline_manager.max_retry_attempts
        },
        'cache_settings': {
            'max_cache_size_mb': 100,
            'cache_ttl_seconds': 3600
        }
    }

def _get_payment_config_data() -> Dict[str, Any]:
    """Get payment configuration data"""
    return {
        'razorpay_settings': razorpay_manager.get_configuration_info(),
        'payment_methods': razorpay_manager.get_payment_methods(),
        'transaction_settings': {
            'auto_capture': True,
            'webhook_enabled': True
        }
    }

def _export_configuration(export_id: str, config_data: Dict[str, Any], export_format: str) -> str:
    """Export configuration to file"""
    try:
        # This would implement actual file export
        # For now, return placeholder URL
        return f"/api/config/download/{export_id}"
    except Exception as e:
        logger.error(f"Error in _export_configuration: {e}")
        return f"/api/config/download/{export_id}"

def _import_configuration(config_data: Dict[str, Any], merge_strategy: str) -> bool:
    """Import configuration from data"""
    try:
        if merge_strategy == 'replace':
            # Replace all configuration
            if 'validation' in config_data:
                _update_validation_config_in_db(config_data['validation'])
            if 'session' in config_data:
                _update_session_config_in_db(config_data['session'])
            if 'security' in config_data:
                _update_security_config_in_db(config_data['security'])
            if 'offline' in config_data:
                _update_offline_config_in_db(config_data['offline'])
            if 'payment' in config_data:
                _update_payment_config_in_db(config_data['payment'])
        
        elif merge_strategy == 'merge':
            # Merge with existing configuration
            # This would implement more complex merge logic
            pass
        
        return True
    except Exception as e:
        logger.error(f"Error in _import_configuration: {e}")
        return False

def _validate_import_config(config_data: Dict[str, Any]) -> List[str]:
    """Validate import configuration data"""
    errors = []
    
    try:
        # Validate each section
        if 'validation' in config_data:
            validation_errors = _validate_validation_config({'validation': config_data['validation']})
            errors.extend(validation_errors)
        
        if 'session' in config_data:
            session_errors = _validate_session_config({'session': config_data['session']})
            errors.extend(session_errors)
        
        if 'security' in config_data:
            security_errors = _validate_security_config({'security': config_data['security']})
            errors.extend(security_errors)
        
        if 'offline' in config_data:
            offline_errors = _validate_offline_config({'offline': config_data['offline']})
            errors.extend(offline_errors)
        
        if 'payment' in config_data:
            payment_errors = _validate_payment_config({'payment': config_data['payment']})
            errors.extend(payment_errors)
    
    except Exception as e:
        logger.error(f"Error in _validate_import_config: {e}")
        errors.append("Configuration validation error")
    
    return errors

# Error handlers for config API
@config_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@config_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@config_api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@config_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many configuration requests. Please try again later.'
    }), 429

@config_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500