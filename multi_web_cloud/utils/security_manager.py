"""
Security Manager for Flask POS Application
Provides comprehensive security features including rate limiting, IP blocking,
suspicious activity detection, and security event logging
"""

import os
import json
import hashlib
import secrets
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import request, g, current_app, session, jsonify
from functools import wraps
import logging
from collections import defaultdict, deque
import ipaddress

class SecurityManager:
    """Comprehensive security management system"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Security settings
        self.rate_limits = {
            'default': {'requests': 100, 'window': 60},  # 100 requests per minute
            'auth': {'requests': 5, 'window': 300},     # 5 login attempts per 5 minutes
            'api': {'requests': 200, 'window': 60},       # 200 API requests per minute
            'upload': {'requests': 10, 'window': 300}      # 10 uploads per 5 minutes
        }
        
        self.ip_block_duration = 3600  # 1 hour
        self.max_failed_attempts = 5
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',           # XSS
            r'javascript:',                           # JavaScript protocol
            r'on\w+\s*=',                         # Event handlers
            r'union\s+select',                       # SQL injection
            r'drop\s+table',                         # SQL injection
            r'insert\s+into',                        # SQL injection
            r'delete\s+from',                        # SQL injection
            r'exec\s*\(',                            # Code execution
            r'eval\s*\(',                            # Code execution
            r'system\s*\(',                          # Code execution
            r'base64_decode',                        # Base64 encoding attacks
            r'file_get_contents',                    # File inclusion attacks
            r'curl\s*exec',                          # Remote execution
            r'wget\s*exec',                          # Remote execution
            r'cmd\.exe',                             # Windows command execution
            r'/bin/sh',                              # Shell execution
            r'powershell',                           # PowerShell execution
            r'\.\./',                                # Directory traversal
            r'%2e%2e%2f',                           # URL encoded directory traversal
            r'null\s*byte',                          # Null byte injection
            r'char\s*\(',                            # Character encoding attacks
            r'ascii\s*\(',                           # ASCII encoding attacks
            r'concat\s*\(',                          # SQL concatenation attacks
            r'substring\s*\(',                       # SQL substring attacks
            r'benchmark\s*\(',                       # SQL timing attacks
            r'sleep\s*\(',                           # SQL timing attacks
            r'waitfor\s+delay',                      # SQL timing attacks
        ]
        
        # Advanced threat patterns
        self.advanced_threat_patterns = {
            'brute_force': {
                'threshold': 5,                      # Failed attempts
                'window': 300,                       # 5 minutes
                'action': 'block_ip'
            },
            'rapid_requests': {
                'threshold': 100,                     # Requests
                'window': 60,                        # 1 minute
                'action': 'rate_limit'
            },
            'unusual_user_agent': {
                'patterns': [
                    r'^$',                           # Empty user agent
                    r'^curl/',                       # curl client
                    r'^wget/',                       # wget client
                    r'^python-requests/',             # Python requests
                    r'^scrapy/',                     # Scrapy crawler
                    r'^bot',                         # Generic bot
                    r'^crawler',                     # Generic crawler
                    r'^spider',                      # Generic spider
                ],
                'action': 'monitor'
            },
            'suspicious_endpoints': {
                'patterns': [
                    r'/admin',                       # Admin endpoints
                    r'/wp-admin',                    # WordPress admin
                    r'/phpmyadmin',                  # phpMyAdmin
                    r'/\.env',                       # Environment files
                    r'/config',                      # Config files
                    r'/backup',                      # Backup files
                    r'/\.git',                       # Git files
                    r'/\.svn',                       # SVN files
                ],
                'action': 'block'
            },
            'data_exfiltration': {
                'large_response_threshold': 10485760,  # 10MB
                'rapid_download_threshold': 5,          # Downloads
                'download_window': 60,                  # 1 minute
                'action': 'monitor'
            }
        }
        
        # In-memory storage for rate limiting and blocking
        self.rate_limit_store = defaultdict(lambda: defaultdict(deque))
        self.blocked_ips = {}
        self.failed_attempts = defaultdict(list)
        self.security_events = deque(maxlen=1000)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security manager with Flask app"""
        self.app = app
        
        # Load security settings from config
        self.rate_limits.update(app.config.get('RATE_LIMITS', {}))
        self.ip_block_duration = app.config.get('IP_BLOCK_DURATION', 3600)
        self.max_failed_attempts = app.config.get('MAX_FAILED_ATTEMPTS', 5)
        
        # Register before request handler
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        self.logger.info("Security manager initialized")
    
    def _before_request(self):
        """Before request security checks"""
        # Get client IP
        client_ip = self._get_client_ip()
        g.client_ip = client_ip
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            self._log_security_event('IP_BLOCKED', client_ip, 'Blocked IP attempted access')
            return jsonify({'error': 'Access denied', 'message': 'Your IP has been blocked'}), 403
        
        # Check rate limiting
        if not self._check_rate_limit(client_ip, request.endpoint):
            self._log_security_event('RATE_LIMIT_EXCEEDED', client_ip, f'Rate limit exceeded for {request.endpoint}')
            return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests'}), 429
        
        # Validate request for suspicious patterns
        if self._contains_suspicious_content():
            self._log_security_event('SUSPICIOUS_REQUEST', client_ip, 'Request contains suspicious content')
            return jsonify({'error': 'Invalid request', 'message': 'Request contains invalid content'}), 400
        
        # Validate headers
        if not self._validate_headers():
            self._log_security_event('INVALID_HEADERS', client_ip, 'Invalid request headers')
            return jsonify({'error': 'Invalid headers', 'message': 'Request headers are invalid'}), 400
    
    def _after_request(self, response):
        """After request security headers"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # Add custom security headers
        response.headers['X-API-Version'] = '1.0.0'
        response.headers['X-Security-Policy'] = 'strict'
        
        return response
    
    def _get_client_ip(self) -> str:
        """Get client IP address with proxy support"""
        # Check for forwarded headers
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        if ip in self.blocked_ips:
            block_info = self.blocked_ips[ip]
            if datetime.utcnow() < block_info['expires']:
                return True
            else:
                # Block expired, remove it
                del self.blocked_ips[ip]
        
        return False
    
    def _check_rate_limit(self, ip: str, endpoint: str) -> bool:
        """Check rate limiting for IP and endpoint"""
        # Determine rate limit category
        category = 'default'
        if endpoint and 'auth' in endpoint:
            category = 'auth'
        elif endpoint and 'api' in endpoint:
            category = 'api'
        elif request.method == 'POST' and 'upload' in request.path:
            category = 'upload'
        
        rate_limit = self.rate_limits.get(category, self.rate_limits['default'])
        now = time.time()
        window_start = now - rate_limit['window']
        
        # Clean old entries
        while self.rate_limit_store[ip][category] and self.rate_limit_store[ip][category][0] < window_start:
            self.rate_limit_store[ip][category].popleft()
        
        # Check if limit exceeded
        if len(self.rate_limit_store[ip][category]) >= rate_limit['requests']:
            return False
        
        # Add current request
        self.rate_limit_store[ip][category].append(now)
        return True
    
    def _contains_suspicious_content(self) -> bool:
        """Check if request contains suspicious content"""
        # Check URL parameters
        for key, value in request.args.items():
            if self._is_suspicious_string(str(value)):
                return True
        
        # Check form data
        for key, value in request.form.items():
            if self._is_suspicious_string(str(value)):
                return True
        
        # Check JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if self._is_suspicious_string(str(value)):
                            return True
            except:
                pass
        
        # Check headers
        for key, value in request.headers.items():
            if self._is_suspicious_string(str(value)):
                return True
        
        return False
    
    def _is_suspicious_string(self, value: str) -> bool:
        """Check if string contains suspicious patterns"""
        for pattern in self.suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _validate_headers(self) -> bool:
        """Validate request headers"""
        # Check for required headers
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.headers.get('Content-Type', '')
            if not content_type:
                return False
        
        # Check host header
        host = request.headers.get('Host', '')
        if not host or self._is_suspicious_string(host):
            return False
        
        # Check user agent length
        user_agent = request.headers.get('User-Agent', '')
        if len(user_agent) > 500:
            return False
        
        return True
    
    def _log_security_event(self, event_type: str, ip: str, details: str, severity: str = 'medium'):
        """Log security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'ip_address': ip,
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': request.endpoint,
            'method': request.method,
            'details': details,
            'severity': severity,
            'session_id': session.get('session_id'),
            'user_id': session.get('user_id')
        }
        
        self.security_events.append(event)
        self.logger.warning(f"Security Event: {event_type} from {ip} - {details}")
        
        # Check if IP should be blocked
        if event_type in ['RATE_LIMIT_EXCEEDED', 'SUSPICIOUS_REQUEST', 'INVALID_HEADERS']:
            self._increment_failed_attempts(ip)
    
    def _increment_failed_attempts(self, ip: str):
        """Increment failed attempts for IP"""
        now = datetime.utcnow()
        self.failed_attempts[ip].append(now)
        
        # Clean old attempts (older than 1 hour)
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[ip] = [attempt for attempt in self.failed_attempts[ip] if attempt > cutoff]
        
        # Block IP if too many failed attempts
        if len(self.failed_attempts[ip]) >= self.max_failed_attempts:
            self._block_ip(ip, f'Too many failed attempts: {len(self.failed_attempts[ip])}')
    
    def _block_ip(self, ip: str, reason: str, duration: int = None):
        """Block an IP address"""
        if duration is None:
            duration = self.ip_block_duration
        
        self.blocked_ips[ip] = {
            'reason': reason,
            'blocked_at': datetime.utcnow().isoformat(),
            'expires': datetime.utcnow() + timedelta(seconds=duration)
        }
        
        self._log_security_event('IP_BLOCKED', ip, f'IP blocked: {reason}', 'high')
        self.logger.warning(f"IP {ip} blocked for {duration} seconds: {reason}")
    
    def _unblock_ip(self, ip: str):
        """Unblock an IP address"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            self._log_security_event('IP_UNBLOCKED', ip, 'IP unblocked', 'info')
            self.logger.info(f"IP {ip} unblocked")
    
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(32)
    
    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
        
        stored_token = session.get('csrf_token')
        if not stored_token:
            return False
        
        return secrets.compare_digest(token, stored_token)
    
    def _sanitize_input(self, value: str) -> str:
        """Sanitize input string"""
        if not isinstance(value, str):
            return str(value)
        
        # Remove potentially dangerous characters
        value = re.sub(r'[<>"\']', '', value)
        
        # Limit length
        value = value[:1000]
        
        return value.strip()
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin', 'letmein']:
            errors.append("Password is too common")
        
        # Check for sequential characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password cannot contain repeated characters")
        
        return len(errors) == 0, errors
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def _detect_brute_force(self, ip: str, username: str = None) -> bool:
        """Detect brute force attack patterns"""
        now = datetime.utcnow()
        recent_attempts = []
        
        # Get recent failed attempts for this IP
        for attempt_time, attempt_username in self.failed_attempts.get(ip, []):
            if now - attempt_time < timedelta(minutes=15):
                recent_attempts.append((attempt_time, attempt_username))
        
        # Check for multiple usernames from same IP
        if username:
            username_attempts = [ua for _, ua in recent_attempts if ua == username]
            if len(username_attempts) >= 3:
                return True
        
        # Check for high frequency attempts
        if len(recent_attempts) >= 10:
            return True
        
        return False
    
    def _detect_advanced_threats(self, ip: str, user_agent: str, endpoint: str) -> List[Dict[str, Any]]:
        """Detect advanced threat patterns"""
        threats = []
        
        # Check for unusual user agents
        for pattern in self.advanced_threat_patterns['unusual_user_agent']['patterns']:
            if re.search(pattern, user_agent, re.IGNORECASE):
                threats.append({
                    'type': 'unusual_user_agent',
                    'pattern': pattern,
                    'user_agent': user_agent,
                    'severity': 'medium'
                })
        
        # Check for suspicious endpoints
        for pattern in self.advanced_threat_patterns['suspicious_endpoints']['patterns']:
            if re.search(pattern, endpoint, re.IGNORECASE):
                threats.append({
                    'type': 'suspicious_endpoint',
                    'pattern': pattern,
                    'endpoint': endpoint,
                    'severity': 'high'
                })
        
        # Check for rapid requests
        if self._is_rapid_request_pattern(ip):
            threats.append({
                'type': 'rapid_requests',
                'ip': ip,
                'severity': 'high'
            })
        
        # Check for potential data exfiltration
        if self._is_data_exfiltration_pattern(ip):
            threats.append({
                'type': 'data_exfiltration',
                'ip': ip,
                'severity': 'critical'
            })
        
        return threats
    
    def _is_rapid_request_pattern(self, ip: str) -> bool:
        """Check for rapid request pattern"""
        now = time.time()
        window_start = now - self.advanced_threat_patterns['rapid_requests']['window']
        
        # Count recent requests from this IP
        recent_count = 0
        for timestamp in self.rate_limit_store[ip].get('default', []):
            if timestamp > window_start:
                recent_count += 1
        
        return recent_count >= self.advanced_threat_patterns['rapid_requests']['threshold']
    
    def _is_data_exfiltration_pattern(self, ip: str) -> bool:
        """Check for data exfiltration patterns"""
        # This would track response sizes and download patterns
        # For now, return False as this requires response tracking
        return False
    
    def _analyze_request_anomaly(self, ip: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for anomalies"""
        anomalies = []
        
        # Check request size
        request_size = len(str(request_data))
        if request_size > 100000:  # 100KB
            anomalies.append({
                'type': 'large_request',
                'size': request_size,
                'severity': 'medium'
            })
        
        # Check parameter count
        param_count = len(request_data)
        if param_count > 50:
            anomalies.append({
                'type': 'excessive_parameters',
                'count': param_count,
                'severity': 'medium'
            })
        
        # Check for unusual parameter names
        unusual_params = []
        for param in request_data.keys():
            if len(param) > 50 or param.startswith('_') or param.startswith('$'):
                unusual_params.append(param)
        
        if unusual_params:
            anomalies.append({
                'type': 'unusual_parameters',
                'parameters': unusual_params,
                'severity': 'low'
            })
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'anomalies': anomalies,
            'risk_score': self._calculate_risk_score(anomalies)
        }
    
    def _calculate_risk_score(self, anomalies: List[Dict[str, Any]]) -> int:
        """Calculate risk score based on anomalies"""
        score = 0
        severity_weights = {
            'low': 1,
            'medium': 3,
            'high': 5,
            'critical': 10
        }
        
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'low')
            score += severity_weights.get(severity, 1)
        
        return min(score, 100)  # Cap at 100
    
    def _handle_threat(self, threat: Dict[str, Any], ip: str) -> str:
        """Handle detected threat based on type and severity"""
        threat_type = threat.get('type')
        severity = threat.get('severity', 'medium')
        
        if threat_type == 'suspicious_endpoint':
            return 'block'
        elif threat_type == 'rapid_requests':
            return 'block'
        elif threat_type == 'data_exfiltration':
            return 'block'
        elif threat_type == 'unusual_user_agent':
            return 'monitor'
        elif severity == 'critical':
            return 'block'
        elif severity == 'high':
            return 'block'
        else:
            return 'monitor'
    
    def _generate_security_hash(self, data: str) -> str:
        """Generate security hash for data"""
        salt = current_app.config.get('SECRET_KEY', 'default_salt')
        return hashlib.sha256(f"{data}{salt}".encode()).hexdigest()
    
    # Public API methods
    
    def block_ip(self, ip: str, reason: str, duration: int = None):
        """Block an IP address"""
        if self._is_valid_ip(ip):
            self._block_ip(ip, reason, duration)
            return True
        return False
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        if ip in self.blocked_ips:
            self._unblock_ip(ip)
            return True
        return False
    
    def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs"""
        return [
            {
                'ip': ip,
                'reason': info['reason'],
                'blocked_at': info['blocked_at'],
                'expires': info['expires'].isoformat()
            }
            for ip, info in self.blocked_ips.items()
        ]
    
    def get_security_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent security events"""
        return list(self.security_events)[-limit:]
    
    def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        
        recent_events = [
            event for event in self.security_events 
            if datetime.fromisoformat(event['timestamp']) > last_24h
        ]
        
        event_types = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_types[event['event_type']] += 1
            severity_counts[event['severity']] += 1
        
        return {
            'total_events_24h': len(recent_events),
            'blocked_ips': len(self.blocked_ips),
            'failed_attempts': len(self.failed_attempts),
            'event_types': dict(event_types),
            'severity_counts': dict(severity_counts),
            'rate_limit_active': len(self.rate_limit_store),
            'last_event': self.security_events[-1] if self.security_events else None
        }
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        return self._validate_password_strength(password)
    
    def sanitize_input(self, value: str) -> str:
        """Sanitize input string"""
        return self._sanitize_input(value)
    
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return self._generate_csrf_token()
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token"""
        return self._validate_csrf_token(token)
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return self._is_ip_blocked(ip)
    
    def detect_brute_force(self, ip: str, username: str = None) -> bool:
        """Detect brute force attack"""
        return self._detect_brute_force(ip, username)
    
    def generate_security_hash(self, data: str) -> str:
        """Generate security hash"""
        return self._generate_security_hash(data)

# Global security manager instance
security_manager = SecurityManager()

# Decorators for security
def rate_limit(limit: int = None, window: int = None, category: str = 'default'):
    """Decorator for rate limiting"""
    def decorator(f):
        @wraps(f)
        def _security_rate_limited_wrapper_func(*args, **kwargs):
            client_ip = security_manager._get_client_ip()
            
            if not security_manager._check_rate_limit(client_ip, request.endpoint):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Limit: {limit or security_manager.rate_limits[category]["requests"]} per {window or security_manager.rate_limits[category]["window"]} seconds'
                }), 429
            
            return f(*args, **kwargs)
        return _security_rate_limited_wrapper_func
    return decorator

def require_security_csrf_token(f):
    """Decorator to require valid CSRF token"""
    @wraps(f)
    def _security_csrf_wrapper_func(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            if not security_manager.validate_csrf_token(csrf_token):
                return jsonify({
                    'error': 'Invalid CSRF token',
                    'message': 'CSRF token validation failed'
                }), 403
        
        return f(*args, **kwargs)
    return _security_csrf_wrapper_func

def validate_security_json_input(required_fields: List[str] = None, optional_fields: List[str] = None):
    """Decorator to validate JSON input"""
    def decorator(f):
        @wraps(f)
        def _security_json_wrapper_func(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'Request must be JSON'
                }), 400
            
            data = request.get_json()
            if not isinstance(data, dict):
                return jsonify({
                    'error': 'Invalid JSON',
                    'message': 'Request must contain a JSON object'
                }), 400
            
            # Check required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'message': f'Missing fields: {", ".join(missing_fields)}'
                    }), 400
            
            # Sanitize input data
            sanitized_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    sanitized_data[key] = security_manager.sanitize_input(value)
                else:
                    sanitized_data[key] = value
            
            # Store sanitized data in request context
            g.sanitized_json = sanitized_data
            
            return f(*args, **kwargs)
        return _security_json_wrapper_func
    return decorator

def log_security_event(event_type: str, details: str, severity: str = 'medium'):
    """Log security event"""
    ip = security_manager._get_client_ip()
    security_manager._log_security_event(event_type, ip, details, severity)

# Utility functions
def block_ip(ip: str, reason: str, duration: int = None) -> bool:
    """Block an IP address"""
    return security_manager.block_ip(ip, reason, duration)

def unblock_ip(ip: str) -> bool:
    """Unblock an IP address"""
    return security_manager.unblock_ip(ip)

def get_blocked_ips() -> List[Dict[str, Any]]:
    """Get list of blocked IPs"""
    return security_manager.get_blocked_ips()

def get_security_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Get recent security events"""
    return security_manager.get_security_events(limit)

def get_security_statistics() -> Dict[str, Any]:
    """Get security statistics"""
    return security_manager.get_security_statistics()

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength"""
    return security_manager.validate_password(password)

def sanitize_input(value: str) -> str:
    """Sanitize input string"""
    return security_manager.sanitize_input(value)

def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return security_manager.generate_csrf_token()

def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token"""
    return security_manager.validate_csrf_token(token)

def is_ip_blocked(ip: str) -> bool:
    """Check if IP is blocked"""
    return security_manager.is_ip_blocked(ip)

def detect_brute_force(ip: str, username: str = None) -> bool:
    """Detect brute force attack"""
    return security_manager.detect_brute_force(ip, username)

def generate_security_hash(data: str) -> str:
    """Generate security hash"""
    return security_manager.generate_security_hash(data)