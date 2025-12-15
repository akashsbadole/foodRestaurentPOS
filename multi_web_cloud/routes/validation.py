"""
Real-time Validation API Routes for Flask POS Application
Provides instant validation feedback for form fields
"""

from flask import Blueprint, request, jsonify
from utils.form_validator import RealTimeValidator, form_validator
from utils.security_manager import require_security_csrf_token, log_security_event
import logging

validation_bp = Blueprint('validation', __name__)

@validation_bp.route('/validate-field', methods=['POST'])
@require_security_csrf_token
def validate_field():
    """
    Validate a single form field in real-time
    
    Expected JSON payload:
    {
        "field_name": "username",
        "value": "john_doe",
        "field_type": "text"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        field_name = data.get('field_name')
        value = data.get('value', '')
        field_type = data.get('field_type', 'text')
        
        if not field_name:
            return jsonify({
                'success': False,
                'message': 'Field name is required'
            }), 400
        
        # Validate field
        result = RealTimeValidator.validate_field(field_name, value, field_type)
        
        # Log validation events for security monitoring
        if not result['valid']:
            log_security_event(
                'FORM_VALIDATION_FAILED',
                f'Validation failed for field: {field_name}',
                'medium'
            )
        
        return jsonify({
            'success': True,
            'validation': result
        })
        
    except Exception as e:
        logging.error(f"Error in field validation: {e}")
        return jsonify({
            'success': False,
            'message': 'Validation error occurred'
        }), 500

@validation_bp.route('/validate-form', methods=['POST'])
@require_security_csrf_token
def validate_form():
    """
    Validate entire form data in real-time
    
    Expected JSON payload:
    {
        "form_data": {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepassword123"
        },
        "form_config": {
            "username": {"type": "text"},
            "email": {"type": "email"},
            "password": {"type": "password"}
        }
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        form_data = data.get('form_data', {})
        form_config = data.get('form_config', {})
        
        if not form_data:
            return jsonify({
                'success': False,
                'message': 'Form data is required'
            }), 400
        
        # Validate form
        result = RealTimeValidator.validate_form_data(form_data, form_config)
        
        # Log validation events for security monitoring
        if not result['valid']:
            log_security_event(
                'FORM_VALIDATION_FAILED',
                f'Form validation failed with {len(result["field_results"])} fields',
                'medium'
            )
        
        return jsonify({
            'success': True,
            'validation': result
        })
        
    except Exception as e:
        logging.error(f"Error in form validation: {e}")
        return jsonify({
            'success': False,
            'message': 'Validation error occurred'
        }), 500

@validation_bp.route('/sanitize-input', methods=['POST'])
@require_security_csrf_token
def sanitize_input():
    """
    Sanitize input data
    
    Expected JSON payload:
    {
        "value": "some <script>alert('xss')</script> content",
        "field_type": "text"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        value = data.get('value', '')
        field_type = data.get('field_type', 'text')
        
        # Sanitize input
        sanitized_value = form_validator.sanitize_input(value, field_type)
        
        # Check if sanitization changed the value
        was_sanitized = sanitized_value != value
        
        if was_sanitized:
            log_security_event(
                'INPUT_SANITIZATION',
                f'Input was sanitized for field type: {field_type}',
                'medium'
            )
        
        return jsonify({
            'success': True,
            'original_value': value,
            'sanitized_value': sanitized_value,
            'was_sanitized': was_sanitized
        })
        
    except Exception as e:
        logging.error(f"Error in input sanitization: {e}")
        return jsonify({
            'success': False,
            'message': 'Sanitization error occurred'
        }), 500

@validation_bp.route('/validate-password-strength', methods=['POST'])
@require_security_csrf_token
def validate_password_strength():
    """
    Validate password strength
    
    Expected JSON payload:
    {
        "password": "userpassword123"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        password = data.get('password', '')
        
        if not password:
            return jsonify({
                'success': False,
                'message': 'Password is required'
            }), 400
        
        # Validate password strength
        is_valid, errors = form_validator.validate_password_strength(password)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'errors': errors,
            'strength_score': _calculate_password_strength(password)
        })
        
    except Exception as e:
        logging.error(f"Error in password validation: {e}")
        return jsonify({
            'success': False,
            'message': 'Password validation error occurred'
        }), 500

@validation_bp.route('/validate-business-rule', methods=['POST'])
@require_security_csrf_token
def validate_business_rule():
    """
    Validate business rules for specific fields
    
    Expected JSON payload:
    {
        "field_name": "gst_number",
        "value": "27AAAPL1234C1ZV"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        field_name = data.get('field_name')
        value = data.get('value', '')
        
        if not field_name:
            return jsonify({
                'success': False,
                'message': 'Field name is required'
            }), 400
        
        # Validate business rule
        is_valid, message = form_validator.validate_business_rules(field_name, value)
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'message': message
        })
        
    except Exception as e:
        logging.error(f"Error in business rule validation: {e}")
        return jsonify({
            'success': False,
            'message': 'Business rule validation error occurred'
        }), 500

def _calculate_password_strength(password: str) -> int:
    """
    Calculate password strength score (0-100)
    
    Args:
        password: Password to evaluate
        
    Returns:
        Strength score from 0 (very weak) to 100 (very strong)
    """
    score = 0
    
    # Length contribution (up to 30 points)
    length_score = min(len(password) * 2, 30)
    score += length_score
    
    # Character variety contribution (up to 40 points)
    if re.search(r'[a-z]', password):
        score += 10  # lowercase
    if re.search(r'[A-Z]', password):
        score += 10  # uppercase
    if re.search(r'\d', password):
        score += 10  # digits
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 10  # special characters
    
    # Complexity contribution (up to 30 points)
    if len(password) >= 12:
        score += 10  # long password
    if re.search(r'[a-zA-Z].*[a-zA-Z].*[a-zA-Z]', password):
        score += 10  # multiple letters
    if re.search(r'\d.*\d.*\d', password):
        score += 10  # multiple digits
    
    # Penalties for common patterns
    if password.lower() in ['password', '123456', 'qwerty', 'admin']:
        score -= 20
    if re.search(r'(.)\1{2,}', password):
        score -= 15  # repeated characters
    if re.search(r'(012|123|234|345|456|567|678|789|890)', password.lower()):
        score -= 10  # sequential numbers
    
    return max(0, min(100, score))

# Validation configuration for different form types
VALIDATION_CONFIGS = {
    'registration': {
        'username': {'type': 'text'},
        'email': {'type': 'email'},
        'password': {'type': 'password'},
        'confirm_password': {'type': 'password'}
    },
    'login': {
        'username': {'type': 'text'},
        'password': {'type': 'password'}
    },
    'order': {
        'customer_name': {'type': 'text'},
        'customer_mobile': {'type': 'phone'},
        'special_instructions': {'type': 'text'}
    },
    'settings': {
        'restaurant_name': {'type': 'text'},
        'restaurant_address': {'type': 'text'},
        'restaurant_phone': {'type': 'phone'},
        'restaurant_email': {'type': 'email'},
        'gst_number': {'type': 'text'}
    }
}

@validation_bp.route('/get-validation-config/<form_type>', methods=['GET'])
def get_validation_config(form_type):
    """
    Get validation configuration for a specific form type
    
    Args:
        form_type: Type of form (registration, login, order, settings)
    """
    try:
        config = VALIDATION_CONFIGS.get(form_type, {})
        
        return jsonify({
            'success': True,
            'form_type': form_type,
            'config': config
        })
        
    except Exception as e:
        logging.error(f"Error getting validation config: {e}")
        return jsonify({
            'success': False,
            'message': 'Error getting validation configuration'
        }), 500