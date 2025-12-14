"""
Session Management Utility for Flask POS Application
Provides enhanced session security, validation, and management features
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from flask import session, request, current_app, g
from flask_login import current_user
from typing import Dict, Optional, Any
import logging

class SessionManager:
    """Enhanced session management with security features"""
    
    def __init__(self, app=None):
        self.app = app
        self.session_timeout = timedelta(hours=8)  # Default session timeout
        self.max_sessions_per_user = 3  # Maximum concurrent sessions per user
        self.session_salt = os.environ.get('SESSION_SALT', 'pos_session_salt')
        self.logger = logging.getLogger(__name__)
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize session manager with Flask app"""
        self.app = app
        
        # Handle PERMANENT_SESSION_LIFETIME - it might already be a timedelta
        lifetime = app.config.get('PERMANENT_SESSION_LIFETIME', 8)
        if isinstance(lifetime, timedelta):
            self.session_timeout = lifetime
        else:
            self.session_timeout = timedelta(hours=lifetime)
        
        # Register before request handler
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Configure session settings
        app.config.update({
            'SESSION_COOKIE_SECURE': app.config.get('SESSION_COOKIE_SECURE', False),
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'SESSION_PERMANENT': True,
            'PERMANENT_SESSION_LIFETIME': self.session_timeout
        })
        
        self.logger.info("Session manager initialized")
    
    def _before_request(self):
        """Before request handler for session validation"""
        # Validate session integrity
        if self._is_session_valid():
            self._update_session_activity()
        else:
            self._invalidate_session()
    
    def _after_request(self, response):
        """After request handler for session security"""
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Set session cookie security
        if current_app.config.get('FORCE_HTTPS', False):
            response.headers['Set-Cookie'] = self._secure_cookie_header()
        
        return response
    
    def _is_session_valid(self) -> bool:
        """Check if current session is valid"""
        if not session or not session.get('user_id'):
            return False
        
        # Check session timeout
        last_activity = session.get('last_activity')
        if not last_activity:
            return False
        
        try:
            last_activity_dt = datetime.fromisoformat(last_activity)
            if datetime.utcnow() - last_activity_dt > self.session_timeout:
                return False
        except (ValueError, TypeError):
            return False
        
        # Check session fingerprint
        current_fingerprint = self._generate_fingerprint()
        stored_fingerprint = session.get('session_fingerprint')
        
        if current_fingerprint != stored_fingerprint:
            self.logger.warning(f"Session fingerprint mismatch for user {session.get('user_id')}")
            return False
        
        return True
    
    def _update_session_activity(self):
        """Update session activity timestamp"""
        session['last_activity'] = datetime.utcnow().isoformat()
        session['ip_address'] = request.remote_addr
        session['user_agent'] = request.headers.get('User-Agent', '')
        
        # Mark session as modified to ensure it's saved
        session.permanent = True
    
    def _invalidate_session(self):
        """Invalidate current session"""
        session.clear()
        if 'user_id' in g:
            del g.user_id
    
    def _generate_fingerprint(self) -> str:
        """Generate session fingerprint for security"""
        fingerprint_data = [
            request.remote_addr or '',
            request.headers.get('User-Agent', ''),
            request.headers.get('Accept-Language', ''),
            self.session_salt
        ]
        
        fingerprint_string = '|'.join(fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def _secure_cookie_header(self) -> str:
        """Generate secure cookie header"""
        cookie_parts = [
            'Path=/',
            'HttpOnly',
            'Secure',
            'SameSite=Lax',
            'Max-Age={}'.format(int(self.session_timeout.total_seconds()))
        ]
        return '; '.join(cookie_parts)
    
    def create_session(self, user_id: int, remember_me: bool = False) -> Dict[str, Any]:
        """Create new session for user"""
        # Check existing sessions for this user
        existing_sessions = self.get_user_sessions(user_id)
        
        # Remove oldest sessions if limit exceeded
        if len(existing_sessions) >= self.max_sessions_per_user:
            sessions_to_remove = len(existing_sessions) - self.max_sessions_per_user + 1
            for i in range(sessions_to_remove):
                self._remove_session_by_id(existing_sessions[i]['session_id'])
        
        # Generate session ID
        session_id = secrets.token_urlsafe(32)
        
        # Create session data
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'session_fingerprint': self._generate_fingerprint(),
            'remember_me': remember_me
        }
        
        # Store session data
        session.update(session_data)
        session.permanent = remember_me
        
        # Log session creation
        self.logger.info(f"Session created for user {user_id} from {request.remote_addr}")
        
        return session_data
    
    def get_user_sessions(self, user_id: int) -> list:
        """Get all active sessions for a user"""
        # In a real implementation, this would query a database
        # For now, return current session info
        if session.get('user_id') == user_id:
            return [{
                'session_id': session.get('session_id'),
                'created_at': session.get('created_at'),
                'last_activity': session.get('last_activity'),
                'ip_address': session.get('ip_address'),
                'user_agent': session.get('user_agent'),
                'is_current': True
            }]
        return []
    
    def _remove_session_by_id(self, session_id: str):
        """Remove session by ID"""
        # In a real implementation, this would remove from database
        pass
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session"""
        try:
            if session.get('session_id') == session_id:
                self._invalidate_session()
                self.logger.info(f"Session {session_id} revoked")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error revoking session {session_id}: {e}")
            return False
    
    def revoke_all_user_sessions(self, user_id: int) -> bool:
        """Revoke all sessions for a user"""
        try:
            if session.get('user_id') == user_id:
                self._invalidate_session()
                self.logger.info(f"All sessions revoked for user {user_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error revoking sessions for user {user_id}: {e}")
            return False
    
    def extend_session(self, hours: int = 8) -> bool:
        """Extend current session timeout"""
        try:
            if not self._is_session_valid():
                return False
            
            session['last_activity'] = datetime.utcnow().isoformat()
            session.permanent = True
            
            self.logger.info(f"Session extended for user {session.get('user_id')}")
            return True
        except Exception as e:
            self.logger.error(f"Error extending session: {e}")
            return False
    
    def get_session_info(self) -> Optional[Dict[str, Any]]:
        """Get current session information"""
        if not self._is_session_valid():
            return None
        
        return {
            'session_id': session.get('session_id'),
            'user_id': session.get('user_id'),
            'created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'ip_address': session.get('ip_address'),
            'user_agent': session.get('user_agent'),
            'remember_me': session.get('remember_me', False),
            'expires_at': (
                datetime.fromisoformat(session.get('last_activity')) + self.session_timeout
            ).isoformat() if session.get('last_activity') else None
        }
    
    def is_session_expired(self) -> bool:
        """Check if current session is expired"""
        if not session.get('last_activity'):
            return True
        
        try:
            last_activity = datetime.fromisoformat(session['last_activity'])
            return datetime.utcnow() - last_activity > self.session_timeout
        except (ValueError, TypeError):
            return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (should be called periodically)"""
        # In a real implementation, this would clean up database
        self.logger.info("Expired session cleanup completed")
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token for AJAX requests"""
        if not token:
            return False
        
        # Get stored CSRF token
        stored_token = session.get('csrf_token')
        if not stored_token:
            return False
        
        # Use secrets.compare_digest for timing attack protection
        return secrets.compare_digest(token, stored_token)
    
    def generate_csrf_token(self) -> str:
        """Generate new CSRF token"""
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
        return token
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            'total_sessions': 1 if session.get('user_id') else 0,
            'active_sessions': 1 if self._is_session_valid() else 0,
            'session_timeout_hours': self.session_timeout.total_seconds() / 3600,
            'max_sessions_per_user': self.max_sessions_per_user,
            'current_user_id': session.get('user_id'),
            'session_created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'ip_address': session.get('ip_address'),
            'user_agent_summary': self._summarize_user_agent(session.get('user_agent', ''))
        }
    
    def _summarize_user_agent(self, user_agent: str) -> str:
        """Summarize user agent string for logging"""
        if not user_agent:
            return "Unknown"
        
        # Extract browser name
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
        for browser in browsers:
            if browser in user_agent:
                return f"{browser} Browser"
        
        # Check for mobile
        if any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone']):
            return "Mobile Browser"
        
        return "Other Browser"

# Global session manager instance
session_manager = SessionManager()

# Session validation decorators
def require_valid_session(f):
    """Decorator to require valid session"""
    def _session_valid_wrapper_func(*args, **kwargs):
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid',
                'redirect': '/auth/login'
            }), 401
        return f(*args, **kwargs)
    return _session_valid_wrapper_func

def require_csrf_token(f):
    """Decorator to require valid CSRF token for AJAX requests"""
    def _session_csrf_wrapper_func(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            # Get CSRF token from header or form
            csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            
            if not session_manager.validate_csrf_token(csrf_token):
                return jsonify({
                    'success': False,
                    'message': 'Invalid CSRF token'
                }), 403
        return f(*args, **kwargs)
    return _session_csrf_wrapper_func

# Session utility functions
def get_current_session_info():
    """Get current session information"""
    return session_manager.get_session_info()

def extend_current_session(hours: int = 8):
    """Extend current session"""
    return session_manager.extend_session(hours)

def revoke_current_session():
    """Revoke current session"""
    return session_manager.revoke_session(session.get('session_id'))

def is_session_valid():
    """Check if current session is valid"""
    return session_manager._is_session_valid()

def generate_session_csrf_token():
    """Generate CSRF token for current session"""
    return session_manager.generate_csrf_token()