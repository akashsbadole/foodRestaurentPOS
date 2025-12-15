"""
Form Validation API Routes for Flask POS Application
Provides comprehensive validation endpoints for real-time form validation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.form_validator import form_validator, RealTimeValidator
from utils.session_manager import session_manager
from utils.security_manager import security_manager

# Create blueprint
validation_api_bp = Blueprint('validation_api', __name__)

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

def rate_limit_validation_api(f):
    """Decorator for rate limiting validation API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for validation API
        if not security_manager._check_rate_limit(client_ip, 'validation_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many validation requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@validation_api_bp.route('/api/validation/field', methods=['POST'])
@rate_limit_validation_api
def validate_field():
    """
    Validate single field with real-time feedback
    
    Request Body:
    {
        "field_name": "email",
        "value": "user@example.com",
        "field_type": "email"
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "errors": [],
        "sanitized_value": "user@example.com",
        "warnings": [],
        "field_name": "email"
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
        
        field_name = data.get('field_name')
        value = data.get('value', '')
        field_type = data.get('field_type', 'text')
        
        if not field_name:
            return jsonify({
                'success': False,
                'error': 'Missing field name',
                'message': 'field_name is required'
            }), 400
        
        # Validate field using RealTimeValidator
        result = RealTimeValidator.validate_field(field_name, value, field_type)
        
        # Log validation event for security monitoring
        if not result['valid']:
            form_validator.log_validation_event(
                'field_validation_failed',
                field_name,
                value,
                f"Validation errors: {', '.join(result['errors'])}",
                'medium'
            )
        
        # Add metadata to response
        result.update({
            'success': True,
            'field_name': field_name,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in validate_field: {e}")
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'message': 'An error occurred during field validation'
        }), 500

@validation_api_bp.route('/api/validation/form', methods=['POST'])
@rate_limit_validation_api
@require_valid_session_api
def validate_form():
    """
    Validate entire form
    
    Request Body:
    {
        "form_data": {
            "email": "user@example.com",
            "phone": "+1234567890",
            "password": "SecurePass123"
        },
        "form_config": {
            "email": {"type": "email", "required": true},
            "phone": {"type": "phone", "required": true},
            "password": {"type": "password", "required": true}
        }
    }
    
    Response:
    {
        "success": true,
        "valid": false,
        "field_results": {
            "email": {...},
            "phone": {...},
            "password": {...}
        },
        "form_errors": [],
        "warnings": []
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
        
        form_data = data.get('form_data', {})
        form_config = data.get('form_config', {})
        
        if not form_data:
            return jsonify({
                'success': False,
                'error': 'Missing form data',
                'message': 'form_data is required'
            }), 400
        
        # Validate form using RealTimeValidator
        result = RealTimeValidator.validate_form_data(form_data, form_config)
        
        # Log form validation event
        if not result['valid']:
            form_validator.log_validation_event(
                'form_validation_failed',
                'form',
                str(form_data.keys()),
                f"Form validation failed with {len(result['form_errors'])} errors",
                'medium'
            )
        
        # Add metadata to response
        result.update({
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'form_fields_count': len(form_data)
        })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in validate_form: {e}")
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'message': 'An error occurred during form validation'
        }), 500

@validation_api_bp.route('/api/validation/password-strength', methods=['POST'])
@rate_limit_validation_api
def check_password_strength():
    """
    Check password strength with scoring
    
    Request Body:
    {
        "password": "MySecurePassword123!"
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "strength_score": 85,
        "strength_level": "strong",
        "errors": [],
        "suggestions": []
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
        
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Missing password',
                'message': 'password is required'
            }), 400
        
        # Validate password strength
        is_valid, errors = form_validator.validate_password_strength(password)
        
        # Calculate strength score (0-100)
        strength_score = 100
        suggestions = []
        
        # Deduct points for each weakness
        if len(password) < 8:
            strength_score -= 20
            suggestions.append("Use at least 8 characters")
        elif len(password) < 12:
            strength_score -= 10
            suggestions.append("Consider using 12+ characters for better security")
        
        if not any(c.islower() for c in password):
            strength_score -= 15
            suggestions.append("Include lowercase letters")
        
        if not any(c.isupper() for c in password):
            strength_score -= 15
            suggestions.append("Include uppercase letters")
        
        if not any(c.isdigit() for c in password):
            strength_score -= 15
            suggestions.append("Include numbers")
        
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            strength_score -= 15
            suggestions.append("Include special characters")
        
        # Check for common patterns
        common_patterns = ['123', 'abc', 'qwerty', 'password']
        for pattern in common_patterns:
            if pattern.lower() in password.lower():
                strength_score -= 10
                suggestions.append(f"Avoid common patterns like '{pattern}'")
        
        # Determine strength level
        if strength_score >= 80:
            strength_level = "very_strong"
        elif strength_score >= 60:
            strength_level = "strong"
        elif strength_score >= 40:
            strength_level = "moderate"
        elif strength_score >= 20:
            strength_level = "weak"
        else:
            strength_level = "very_weak"
        
        # Log password validation for security
        if strength_score < 40:
            form_validator.log_validation_event(
                'weak_password_attempt',
                'password',
                password[:10] + '...',
                f"Weak password with score {strength_score}",
                'medium'
            )
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'strength_score': max(0, min(100, strength_score)),
            'strength_level': strength_level,
            'errors': errors,
            'suggestions': suggestions,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in check_password_strength: {e}")
        return jsonify({
            'success': False,
            'error': 'Validation error',
            'message': 'An error occurred during password strength check'
        }), 500

@validation_api_bp.route('/api/validation/sanitize', methods=['POST'])
@rate_limit_validation_api
def sanitize_input():
    """
    Sanitize input data
    
    Request Body:
    {
        "data": {
            "name": "<script>alert('xss')</script>John",
            "email": "john@example.com",
            "comment": "Hello <b>world</b>"
        },
        "field_types": {
            "name": "text",
            "email": "email",
            "comment": "html"
        }
    }
    
    Response:
    {
        "success": true,
        "sanitized_data": {
            "name": "John",
            "email": "john@example.com",
            "comment": "Hello <b>world</b>"
        },
        "warnings": ["Input contained potentially dangerous content"]
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
        
        input_data = data.get('data', {})
        field_types = data.get('field_types', {})
        
        if not input_data:
            return jsonify({
                'success': False,
                'error': 'Missing input data',
                'message': 'data is required'
            }), 400
        
        sanitized_data = {}
        warnings = []
        
        # Sanitize each field
        for field_name, field_value in input_data.items():
            if isinstance(field_value, str):
                field_type = field_types.get(field_name, 'text')
                original_value = field_value
                sanitized_value = form_validator.sanitize_input(field_value, field_type)
                sanitized_data[field_name] = sanitized_value
                
                # Check if sanitization changed the value
                if original_value != sanitized_value:
                    warnings.append(f"Field '{field_name}' contained potentially dangerous content and was sanitized")
                    
                    # Log sanitization event
                    form_validator.log_validation_event(
                        'input_sanitization',
                        field_name,
                        original_value[:50],
                        'Input contained potentially dangerous content',
                        'high'
                    )
            else:
                sanitized_data[field_name] = field_value
        
        return jsonify({
            'success': True,
            'sanitized_data': sanitized_data,
            'warnings': warnings,
            'fields_processed': len(input_data),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in sanitize_input: {e}")
        return jsonify({
            'success': False,
            'error': 'Sanitization error',
            'message': 'An error occurred during input sanitization'
        }), 500

@validation_api_bp.route('/api/validation/rules', methods=['GET'])
@rate_limit_validation_api
def get_validation_rules():
    """
    Get validation rules for forms
    
    Response:
    {
        "success": true,
        "rules": {
            "business_rules": {
                "gst_number": {...},
                "phone_number": {...},
                "email": {...}
            },
            "password_requirements": {...},
            "file_upload_limits": {...}
        }
    }
    """
    try:
        # Get business rules from form validator
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
        
        # Define field type mappings
        field_types = {
            "text": {
                "description": "Plain text input",
                "sanitization": "HTML tags removed, special characters encoded"
            },
            "html": {
                "description": "HTML content",
                "sanitization": "Dangerous tags removed, safe tags allowed",
                "allowed_tags": ["p", "br", "strong", "em", "u", "ul", "ol", "li"]
            },
            "email": {
                "description": "Email address",
                "validation": "Standard email format",
                "sanitization": "Lowercase, trimmed"
            },
            "phone": {
                "description": "Phone number",
                "validation": "10-15 digits with optional symbols",
                "sanitization": "Numbers and basic symbols only"
            }
        }
        
        return jsonify({
            'success': True,
            'rules': {
                'business_rules': business_rules,
                'password_requirements': password_requirements,
                'file_upload_limits': file_upload_limits,
                'field_types': field_types
            },
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_validation_rules: {e}")
        return jsonify({
            'success': False,
            'error': 'Rules retrieval error',
            'message': 'An error occurred while retrieving validation rules'
        }), 500

@validation_api_bp.route('/api/validation/validate-json', methods=['POST'])
@rate_limit_validation_api
def validate_json_structure():
    """
    Validate JSON structure and content
    
    Request Body:
    {
        "data": {"name": "John", "age": 25},
        "required_fields": ["name", "email"],
        "field_types": {"name": "str", "age": "int"}
    }
    
    Response:
    {
        "success": true,
        "valid": false,
        "errors": ["Missing required fields: email"]
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
        
        json_data = data.get('data', {})
        required_fields = data.get('required_fields', [])
        field_types = data.get('field_types', {})
        
        # Validate JSON structure
        is_valid, error_message = form_validator.validate_json_structure(
            json_data, required_fields, field_types
        )
        
        # Additional validation for field types
        errors = []
        if not is_valid:
            errors.append(error_message)
        
        # Validate field types if specified
        if field_types:
            type_mapping = {
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict
            }
            
            for field_name, expected_type_name in field_types.items():
                if field_name in json_data:
                    expected_type = type_mapping.get(expected_type_name)
                    if expected_type and not isinstance(json_data[field_name], expected_type):
                        errors.append(f"Field '{field_name}' must be of type {expected_type_name}")
        
        return jsonify({
            'success': True,
            'valid': len(errors) == 0,
            'errors': errors,
            'fields_validated': len(json_data),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_json_structure: {e}")
        return jsonify({
            'success': False,
            'error': 'JSON validation error',
            'message': 'An error occurred during JSON structure validation'
        }), 500

@validation_api_bp.route('/api/validation/file-upload', methods=['POST'])
@rate_limit_validation_api
@require_valid_session_api
def validate_file_upload():
    """
    Validate file upload for security
    
    Request: multipart/form-data with file
    
    Response:
    {
        "success": true,
        "valid": true,
        "file_info": {
            "name": "document.pdf",
            "size": 1024000,
            "type": "application/pdf"
        }
    }
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'message': 'file field is required in multipart form data'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a file to upload'
            }), 400
        
        # Get allowed extensions from request or use defaults
        allowed_extensions = request.form.get('allowed_extensions', '').split(',')
        allowed_extensions = [ext.strip() for ext in allowed_extensions if ext.strip()]
        
        if not allowed_extensions:
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'txt', 'xls', 'xlsx']
        
        max_size_mb = request.form.get('max_size_mb', '5')
        try:
            max_size_mb = int(max_size_mb)
        except ValueError:
            max_size_mb = 5
        
        # Validate file
        is_valid, error_message = form_validator.validate_file_upload(
            file, allowed_extensions, max_size_mb
        )
        
        # Get file info
        file_info = {
            'name': file.filename,
            'size': file.content_length if hasattr(file, 'content_length') else 0,
            'type': file.content_type if hasattr(file, 'content_type') else 'unknown'
        }
        
        # Log file upload validation
        if not is_valid:
            form_validator.log_validation_event(
                'file_upload_validation_failed',
                'file_upload',
                file.filename,
                f"File validation failed: {error_message}",
                'high'
            )
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'file_info': file_info,
            'error_message': error_message if not is_valid else None,
            'allowed_extensions': allowed_extensions,
            'max_size_mb': max_size_mb,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_file_upload: {e}")
        return jsonify({
            'success': False,
            'error': 'File validation error',
            'message': 'An error occurred during file upload validation'
        }), 500

# Error handlers for validation API
@validation_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@validation_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@validation_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@validation_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500