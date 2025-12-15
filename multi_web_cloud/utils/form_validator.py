"""
Advanced Form Validation System for Flask POS Application
Provides real-time validation, custom validators, input sanitization, and security features
"""

import re
import html
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from flask import request, session, current_app
from wtforms import ValidationError
from urllib.parse import urlparse
import bleach

class FormValidator:
    """Advanced form validation with security features"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # XSS and SQL injection patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'vbscript:',
            r'data:text/html',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'<img[^>]*onerror[^>]*>',
            r'<svg[^>]* onload[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'<\s*script',
            r'<\s*object',
            r'<\s*embed',
            r'<\s*link',
            r'<\s*meta',
            r'<\s*style',
            r'<\s*img',
            r'<\s*svg'
        ]
        
        self.sql_injection_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
            r'(--|#|\/\*|\*\/)',
            r'(\bOR\b.*\b1\s*=\s*1\b)',
            r'(\bAND\b.*\b1\s*=\s*1\b)',
            r'(\'\s*OR\s*\'.*\'.*=.*\')',
            r'(;\s*(DROP|DELETE|UPDATE|INSERT|CREATE|ALTER))',
            r'(\bEXEC\b\s*\()',
            r'(\bxp_cmdshell\b)',
            r'(\bsp_executesql\b)',
            r'(\bwaitfor\s+delay\b)',
            r'(\bconvert\s*\()',
            r'(\bcast\s*\()',
            r'(\bsubstring\s*\()',
            r'(\bchar\s*\()',
            r'(\bascii\s*\()',
            r'(\blen\s*\()',
            r'(\bconcat\s*\()'
        ]
        
        # Business validation rules
        self.business_rules = {
            'gst_number': {
                'pattern': r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$',
                'message': 'GST number must be 15 characters in format: 2 digits + 5 letters + 4 digits + 1 letter + Z + 1 letter/number'
            },
            'phone_number': {
                'pattern': r'^[+]?[\d\s\-\(\)]{10,15}$',
                'message': 'Phone number must be 10-15 digits, may include +, spaces, hyphens, and parentheses'
            },
            'pincode': {
                'pattern': r'^[1-9][0-9]{5}$',
                'message': 'PIN code must be 6 digits starting with 1-9'
            },
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'message': 'Please enter a valid email address'
            },
            'username': {
                'pattern': r'^[a-zA-Z0-9_]{3,20}$',
                'message': 'Username must be 3-20 characters, letters, numbers, and underscores only'
            },
            'order_number': {
                'pattern': r'^[A-Z]{2,}\d{8,}$',
                'message': 'Order number must start with 2+ uppercase letters followed by 8+ digits'
            },
            'price': {
                'min': 0.01,
                'max': 999999.99,
                'message': 'Price must be between ₹0.01 and ₹999,999.99'
            },
            'quantity': {
                'min': 0,
                'max': 99999,
                'message': 'Quantity must be between 0 and 99,999'
            }
        }
    
    def sanitize_input(self, value: str, field_type: str = 'text') -> str:
        """
        Sanitize input against XSS and SQL injection
        
        Args:
            value: Input string to sanitize
            field_type: Type of field (text, html, email, etc.)
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            return str(value) if value is not None else ''
        
        # Remove null bytes and control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                self.logger.warning(f"XSS pattern detected in input: {value[:100]}...")
                # Remove dangerous content
                value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                self.logger.warning(f"SQL injection pattern detected in input: {value[:100]}...")
                # Remove dangerous content
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)
        
        # Additional sanitization based on field type
        if field_type == 'html':
            # Allow basic HTML tags but remove dangerous ones
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']
            allowed_attributes = {'*': ['class']}
            value = bleach.clean(value, tags=allowed_tags, attributes=allowed_attributes, strip=True)
            value = str(value) if isinstance(value, (bytes, type(''))) else value
        elif field_type == 'text':
            # Remove all HTML tags
            value = bleach.clean(value, tags=[], attributes={}, strip=True)
            value = str(value) if isinstance(value, (bytes, type(''))) else value
        elif field_type == 'email':
            # Email specific sanitization
            value = value.lower().strip()
        elif field_type == 'phone':
            # Phone specific sanitization
            value = re.sub(r'[^\d+()\s-]', '', value)
        
        # HTML entity encoding for remaining content
        value = html.escape(value)
        
        return value.strip()
    
    def validate_business_rules(self, field_name: str, value: str) -> Tuple[bool, str]:
        """
        Validate business rules for specific fields
        
        Args:
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if field_name not in self.business_rules:
            return True, ""
        
        rule = self.business_rules[field_name]
        
        # Pattern validation
        if 'pattern' in rule:
            if not re.match(rule['pattern'], value):
                return False, rule['message']
        
        # Range validation for numeric fields
        if 'min' in rule or 'max' in rule:
            try:
                numeric_value = float(value)
                if 'min' in rule and numeric_value < rule['min']:
                    return False, rule['message']
                if 'max' in rule and numeric_value > rule['max']:
                    return False, rule['message']
            except ValueError:
                return False, rule['message']
        
        return True, ""
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength with comprehensive checks
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) > 128:
            errors.append("Password must be less than 128 characters long")
        
        # Character type checks
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey',
            '1234567890', 'password1', 'qwerty123', 'admin123'
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common. Please choose a more secure password")
        
        # Sequential character check
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password cannot contain 3 or more repeated characters")
        
        # Sequential number/letter check
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            errors.append("Password cannot contain sequential characters")
        
        # Keyboard pattern check
        keyboard_patterns = [
            'qwerty', 'asdf', 'zxcv', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm',
            '12345678', '87654321', '1qaz', '2wsx', '3edc', '4rfv', '5tgb', '6yhn'
        ]
        for pattern in keyboard_patterns:
            if pattern in password.lower():
                errors.append("Password cannot contain keyboard patterns")
                break
        
        return len(errors) == 0, errors
    
    def validate_file_upload(self, file, allowed_extensions=None, max_size_mb=5) -> Tuple[bool, str]:
        """
        Validate file upload for security
        
        Args:
            file: File object from Flask request
            allowed_extensions: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file:
            return True, "No file provided"
        
        # Check file extension
        if allowed_extensions:
            filename = file.filename.lower()
            if not any(filename.endswith(f'.{ext.lower()}') for ext in allowed_extensions):
                return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
        
        # Check file content type (basic check)
        if file.content_type:
            allowed_mime_types = {
                'image/jpeg': ['.jpg', '.jpeg'],
                'image/png': ['.png'],
                'image/gif': ['.gif'],
                'application/pdf': ['.pdf'],
                'text/plain': ['.txt'],
                'application/vnd.ms-excel': ['.xls'],
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
            }
            
            if file.content_type not in allowed_mime_types:
                return False, f"File type {file.content_type} is not allowed"
        
        return True, "File validation passed"
    
    def validate_json_structure(self, data: Any, required_fields: Optional[List[str]] = None,
                             field_types: Optional[Dict[str, type]] = None) -> Tuple[bool, str]:
        """
        Validate JSON structure and content
        
        Args:
            data: JSON data to validate
            required_fields: List of required field names
            field_types: Dictionary of field names to expected types
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Invalid JSON data: must be an object"
        
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Check field types
        if field_types:
            for field_name, expected_type in field_types.items():
                if field_name in data:
                    if not isinstance(data[field_name], expected_type):
                        return False, f"Field '{field_name}' must be of type {expected_type.__name__}"
        
        return True, "JSON validation passed"
    
    def generate_validation_hash(self, data: Dict[str, Any]) -> str:
        """
        Generate hash for validation data to detect tampering
        
        Args:
            data: Dictionary of data to hash
            
        Returns:
            SHA256 hash of the data
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
        
        # Add secret key for security
        secret_key = current_app.config.get('SECRET_KEY', 'default_secret')
        data_with_secret = f"{sorted_data}{secret_key}"
        
        return hashlib.sha256(data_with_secret.encode()).hexdigest()
    
    def validate_timestamp(self, timestamp: str, max_age_minutes: int = 30) -> bool:
        """
        Validate timestamp to prevent replay attacks
        
        Args:
            timestamp: ISO format timestamp string
            max_age_minutes: Maximum age in minutes
            
        Returns:
            True if timestamp is valid and not too old
        """
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow()
            age = now - ts
            
            return age.total_seconds() <= (max_age_minutes * 60)
        except (ValueError, AttributeError):
            return False
    
    def get_validation_context(self) -> Dict[str, Any]:
        """
        Get validation context for security checks
        
        Returns:
            Dictionary with validation context information
        """
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'session_id': session.get('session_id'),
            'timestamp': datetime.utcnow().isoformat(),
            'request_method': request.method,
            'request_endpoint': request.endpoint
        }
    
    def log_validation_event(self, event_type: str, field_name: str, value: str,
                           details: Optional[str] = None, severity: str = 'medium'):
        """
        Log validation events for security monitoring
        
        Args:
            event_type: Type of validation event
            field_name: Name of the field being validated
            value: Value that was validated
            details: Additional details about the event
            severity: Severity level (low, medium, high, critical)
        """
        context = self.get_validation_context()
        
        log_data = {
            'event_type': event_type,
            'field_name': field_name,
            'value_preview': value[:50] if value else '',
            'details': details,
            'severity': severity,
            'context': context
        }
        
        if severity in ['high', 'critical']:
            self.logger.error(f"Security validation event: {json.dumps(log_data)}")
        else:
            self.logger.warning(f"Validation event: {json.dumps(log_data)}")

# Global form validator instance
form_validator = FormValidator()

# Custom WTForms validators
def validate_gst_number(form, field):
    """Custom WTForms validator for GST number"""
    if field.data:
        is_valid, message = form_validator.validate_business_rules('gst_number', field.data)
        if not is_valid:
            raise ValidationError(message)

def validate_phone_number(form, field):
    """Custom WTForms validator for phone number"""
    if field.data:
        is_valid, message = form_validator.validate_business_rules('phone_number', field.data)
        if not is_valid:
            raise ValidationError(message)

def validate_password_strength_wtforms(form, field):
    """Custom WTForms validator for password strength"""
    if field.data:
        is_valid, errors = form_validator.validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError('; '.join(errors))

def validate_safe_input(form, field):
    """Custom WTForms validator for safe input (XSS/SQL injection protection)"""
    if field.data:
        sanitized_value = form_validator.sanitize_input(field.data, field.type)
        if sanitized_value != field.data:
            form_validator.log_validation_event(
                'input_sanitization', 
                field.name, 
                field.data,
                'Input contained potentially dangerous content and was sanitized',
                'high'
            )
            # Update field data with sanitized value
            field.data = sanitized_value

def validate_business_logic(form, field):
    """Custom WTForms validator for business logic"""
    if field.data:
        field_name = field.name
        is_valid, message = form_validator.validate_business_rules(field_name, str(field.data))
        if not is_valid:
            raise ValidationError(message)

# Real-time validation utilities
class RealTimeValidator:
    """Real-time validation for AJAX requests"""
    
    @staticmethod
    def validate_field(field_name: str, value: str, field_type: str = 'text') -> Dict[str, Any]:
        """
        Validate a single field in real-time
        
        Args:
            field_name: Name of the field
            value: Value to validate
            field_type: Type of field
            
        Returns:
            Dictionary with validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'sanitized_value': value,
            'warnings': []
        }
        
        # Sanitize input
        sanitized_value = form_validator.sanitize_input(value, field_type)
        result['sanitized_value'] = sanitized_value
        
        # Check if sanitization changed the value
        if sanitized_value != value:
            result['warnings'].append('Input was sanitized for security')
        
        # Business rule validation
        is_valid, message = form_validator.validate_business_rules(field_name, sanitized_value)
        if not is_valid:
            result['valid'] = False
            result['errors'].append(message)
        
        # Password strength validation
        if field_name == 'password':
            is_valid, errors = form_validator.validate_password_strength(sanitized_value)
            if not is_valid:
                result['valid'] = False
                result['errors'].extend(errors)
        
        # Email validation
        if field_name == 'email' and sanitized_value:
            is_valid, message = form_validator.validate_business_rules('email', sanitized_value)
            if not is_valid:
                result['valid'] = False
                result['errors'].append(message)
        
        # Phone validation
        if field_name in ['phone', 'mobile', 'customer_mobile'] and sanitized_value:
            is_valid, message = form_validator.validate_business_rules('phone_number', sanitized_value)
            if not is_valid:
                result['valid'] = False
                result['errors'].append(message)
        
        return result
    
    @staticmethod
    def validate_form_data(data: Dict[str, Any], form_config: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Validate entire form data in real-time
        
        Args:
            data: Form data dictionary
            form_config: Form configuration with field types and validation rules
            
        Returns:
            Dictionary with validation results for all fields
        """
        results = {
            'valid': True,
            'field_results': {},
            'form_errors': [],
            'warnings': []
        }
        
        for field_name, field_config in form_config.items():
            field_value = data.get(field_name, '')
            field_type = field_config.get('type', 'text')
            
            field_result = RealTimeValidator.validate_field(field_name, field_value, field_type)
            results['field_results'][field_name] = field_result
            
            if not field_result['valid']:
                results['valid'] = False
            
            if field_result['warnings']:
                results['warnings'].extend(field_result['warnings'])
        
        return results

# Utility functions for easy access
def sanitize_input(value: str, field_type: str = 'text') -> str:
    """Sanitize input using the form validator"""
    return form_validator.sanitize_input(value, field_type)

def validate_password_strength_util(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    return form_validator.validate_password_strength(password)

def validate_business_rules_util(field_name: str, value: str) -> Tuple[bool, str]:
    """Validate business rules for a field"""
    return form_validator.validate_business_rules(field_name, value)

def validate_file_upload_util(file, allowed_extensions=None, max_size_mb=5) -> Tuple[bool, str]:
    """Validate file upload"""
    return form_validator.validate_file_upload(file, allowed_extensions, max_size_mb)

def validate_json_structure_util(data: Any, required_fields: Optional[List[str]] = None,
                          field_types: Optional[Dict[str, type]] = None) -> Tuple[bool, str]:
    """Validate JSON structure"""
    return form_validator.validate_json_structure(data, required_fields, field_types)