"""
Session Management API Routes for Flask POS Application
Provides comprehensive session management endpoints with security features
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.session_manager import session_manager
from utils.security_manager import security_manager

# Create blueprint
session_api_bp = Blueprint('session_api', __name__)

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

def rate_limit_session_api(f):
    """Decorator for rate limiting session API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for session API
        if not security_manager._check_rate_limit(client_ip, 'session_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many session requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@session_api_bp.route('/api/session/info', methods=['GET'])
@rate_limit_session_api
@require_valid_session_api
def get_session_info():
    """
    Get current session information
    
    Response:
    {
        "success": true,
        "session": {
            "session_id": "abc123...",
            "user_id": 1,
            "created_at": "2023-12-09T10:00:00",
            "last_activity": "2023-12-09T10:30:00",
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "remember_me": false,
            "expires_at": "2023-12-09T18:00:00"
        }
    }
    """
    try:
        # Get session information
        session_info = session_manager.get_session_info()
        
        if not session_info:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'message': 'No active session found'
            }), 404
        
        # Add additional security information
        session_info.update({
            'security': {
                'fingerprint_valid': session_manager._generate_fingerprint() == session.get('session_fingerprint'),
                'ip_consistent': session.get('ip_address') == request.remote_addr,
                'user_agent_consistent': session.get('user_agent') == request.headers.get('User-Agent', '')
            }
        })
        
        return jsonify({
            'success': True,
            'session': session_info,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_session_info: {e}")
        return jsonify({
            'success': False,
            'error': 'Session retrieval error',
            'message': 'An error occurred while retrieving session information'
        }), 500

@session_api_bp.route('/api/session/extend', methods=['POST'])
@rate_limit_session_api
@require_valid_session_api
def extend_session():
    """
    Extend session timeout
    
    Request Body:
    {
        "hours": 8
    }
    
    Response:
    {
        "success": true,
        "message": "Session extended successfully",
        "new_expires_at": "2023-12-10T02:00:00"
    }
    """
    try:
        # Get request data
        data = request.get_json() or {}
        hours = data.get('hours', 8)
        
        # Validate hours parameter
        if not isinstance(hours, int) or hours < 1 or hours > 24:
            return jsonify({
                'success': False,
                'error': 'Invalid extension period',
                'message': 'Hours must be an integer between 1 and 24'
            }), 400
        
        # Extend session
        success = session_manager.extend_session(hours)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Session extension failed',
                'message': 'Unable to extend session. Please log in again.'
            }), 400
        
        # Get new session info
        session_info = session_manager.get_session_info()
        
        return jsonify({
            'success': True,
            'message': 'Session extended successfully',
            'extended_hours': hours,
            'new_expires_at': session_info.get('expires_at') if session_info else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in extend_session: {e}")
        return jsonify({
            'success': False,
            'error': 'Session extension error',
            'message': 'An error occurred while extending the session'
        }), 500

@session_api_bp.route('/api/session/active', methods=['GET'])
@rate_limit_session_api
@require_valid_session_api
def get_active_sessions():
    """
    List all active sessions for user
    
    Response:
    {
        "success": true,
        "sessions": [
            {
                "session_id": "abc123...",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "created_at": "2023-12-09T10:00:00",
                "last_activity": "2023-12-09T10:30:00",
                "expires_at": "2023-12-09T18:00:00",
                "remember_me": false,
                "is_current": true
            }
        ]
    }
    """
    try:
        # Get current user ID from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not found in session',
                'message': 'No user information available in current session'
            }), 404
        
        # Get all active sessions for the user
        user_sessions = session_manager.get_user_sessions(user_id)
        
        # Add security analysis for each session
        for session_data in user_sessions:
            session_data['security'] = {
                'ip_risk': _analyze_ip_risk(session_data.get('ip_address')),
                'device_risk': _analyze_device_risk(session_data.get('user_agent')),
                'age_hours': _calculate_session_age_hours(session_data.get('created_at'))
            }
        
        return jsonify({
            'success': True,
            'sessions': user_sessions,
            'total_sessions': len(user_sessions),
            'current_user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_active_sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Sessions retrieval error',
            'message': 'An error occurred while retrieving active sessions'
        }), 500

@session_api_bp.route('/api/session/<session_id>', methods=['DELETE'])
@rate_limit_session_api
@require_valid_session_api
def revoke_session(session_id):
    """
    Revoke specific session
    
    Response:
    {
        "success": true,
        "message": "Session revoked successfully"
    }
    """
    try:
        # Validate session_id parameter
        if not session_id or not isinstance(session_id, str):
            return jsonify({
                'success': False,
                'error': 'Invalid session ID',
                'message': 'Session ID is required and must be a string'
            }), 400
        
        # Revoke the session
        success = session_manager.revoke_session(session_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Session revocation failed',
                'message': 'Unable to revoke the specified session. It may not exist or already be revoked.'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Session revoked successfully',
            'revoked_session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in revoke_session: {e}")
        return jsonify({
            'success': False,
            'error': 'Session revocation error',
            'message': 'An error occurred while revoking the session'
        }), 500

@session_api_bp.route('/api/session/others', methods=['DELETE'])
@rate_limit_session_api
@require_valid_session_api
def revoke_other_sessions():
    """
    Revoke all other sessions except current
    
    Response:
    {
        "success": true,
        "message": "Other sessions revoked successfully",
        "revoked_count": 2
    }
    """
    try:
        # Get current user ID and session ID
        user_id = session.get('user_id')
        current_session_id = session.get('session_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not found in session',
                'message': 'No user information available in current session'
            }), 404
        
        # Get all active sessions before revocation
        all_sessions = session_manager.get_user_sessions(user_id)
        other_sessions_count = len([s for s in all_sessions if not s.get('is_current', False)])
        
        # Revoke all sessions for the user
        success = session_manager.revoke_all_user_sessions(user_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Session revocation failed',
                'message': 'Unable to revoke other sessions'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Other sessions revoked successfully',
            'revoked_count': other_sessions_count,
            'current_session_preserved': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in revoke_other_sessions: {e}")
        return jsonify({
            'success': False,
            'error': 'Session revocation error',
            'message': 'An error occurred while revoking other sessions'
        }), 500

@session_api_bp.route('/api/session/security', methods=['GET'])
@rate_limit_session_api
@require_valid_session_api
def get_session_security_analysis():
    """
    Get session security analysis
    
    Response:
    {
        "success": true,
        "security": {
            "risk_score": 15,
            "risk_level": "low",
            "anomalies": [],
            "recommendations": [],
            "fingerprint_valid": true,
            "ip_consistent": true,
            "user_agent_consistent": true
        }
    }
    """
    try:
        # Get current session information
        session_info = session_manager.get_session_info()
        
        if not session_info:
            return jsonify({
                'success': False,
                'error': 'Session not found',
                'message': 'No active session found'
            }), 404
        
        # Perform security analysis
        security_analysis = {
            'fingerprint_valid': session_manager._generate_fingerprint() == session.get('session_fingerprint'),
            'ip_consistent': session.get('ip_address') == request.remote_addr,
            'user_agent_consistent': session.get('user_agent') == request.headers.get('User-Agent', ''),
            'session_age_hours': _calculate_session_age_hours(session_info.get('created_at')),
            'idle_time_minutes': _calculate_idle_time_minutes(session_info.get('last_activity')),
            'ip_risk': _analyze_ip_risk(request.remote_addr),
            'device_risk': _analyze_device_risk(request.headers.get('User-Agent', ''))
        }
        
        # Calculate risk score
        risk_score = 0
        anomalies = []
        recommendations = []
        
        if not security_analysis['fingerprint_valid']:
            risk_score += 40
            anomalies.append('Session fingerprint mismatch detected')
            recommendations.append('Re-authenticate immediately')
        
        if not security_analysis['ip_consistent']:
            risk_score += 30
            anomalies.append('IP address changed during session')
            recommendations.append('Verify your identity')
        
        if not security_analysis['user_agent_consistent']:
            risk_score += 20
            anomalies.append('User agent changed during session')
            recommendations.append('Check for unauthorized access')
        
        if security_analysis['idle_time_minutes'] > 120:  # 2 hours
            risk_score += 10
            anomalies.append('Long idle period detected')
            recommendations.append('Consider logging out after inactivity')
        
        if security_analysis['ip_risk']['suspicious']:
            risk_score += 25
            anomalies.append('Suspicious IP address detected')
            recommendations.append('Use VPN or trusted network')
        
        if security_analysis['device_risk']['suspicious']:
            risk_score += 15
            anomalies.append('Suspicious device/browser detected')
            recommendations.append('Use trusted devices only')
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        elif risk_score >= 10:
            risk_level = 'low'
        else:
            risk_level = 'minimal'
        
        security_analysis.update({
            'risk_score': risk_score,
            'risk_level': risk_level,
            'anomalies': anomalies,
            'recommendations': recommendations
        })
        
        return jsonify({
            'success': True,
            'security': security_analysis,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_session_security_analysis: {e}")
        return jsonify({
            'success': False,
            'error': 'Security analysis error',
            'message': 'An error occurred during security analysis'
        }), 500

@session_api_bp.route('/api/session/validate', methods=['POST'])
@rate_limit_session_api
def validate_session():
    """
    Validate session integrity
    
    Request Body:
    {
        "session_id": "abc123...",
        "csrf_token": "def456..."
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "details": {
            "session_valid": true,
            "csrf_valid": true,
            "fingerprint_valid": true
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() or {}
        provided_session_id = data.get('session_id')
        csrf_token = data.get('csrf_token')
        
        # Validate session
        session_valid = session_manager._is_session_valid()
        
        # Validate CSRF token if provided
        csrf_valid = False
        if csrf_token:
            csrf_valid = session_manager.validate_csrf_token(csrf_token)
        
        # Validate fingerprint
        fingerprint_valid = session_manager._generate_fingerprint() == session.get('session_fingerprint')
        
        # Overall validity
        overall_valid = session_valid and fingerprint_valid
        
        # Get session info for additional details
        session_info = session_manager.get_session_info() if session_valid else None
        
        validation_details = {
            'session_valid': session_valid,
            'csrf_valid': csrf_valid,
            'fingerprint_valid': fingerprint_valid,
            'overall_valid': overall_valid,
            'session_info': session_info
        }
        
        # Log validation attempt
        if not overall_valid:
            security_manager._log_security_event(
                'SESSION_VALIDATION_FAILED',
                security_manager._get_client_ip(),
                f"Session validation failed: {validation_details}",
                'medium'
            )
        
        return jsonify({
            'success': True,
            'valid': overall_valid,
            'details': validation_details,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_session: {e}")
        return jsonify({
            'success': False,
            'error': 'Session validation error',
            'message': 'An error occurred during session validation'
        }), 500

@session_api_bp.route('/api/session/activity', methods=['GET'])
@rate_limit_session_api
@require_valid_session_api
def get_session_activity():
    """
    Get activity log for current session
    
    Query Parameters:
    - limit: Number of activity records to return (default: 50)
    
    Response:
    {
        "success": true,
        "activities": [
            {
                "activity_type": "session_created",
                "details": "Session created successfully",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0...",
                "timestamp": "2023-12-09T10:00:00"
            }
        ]
    }
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        limit = min(max(limit, 1), 100)  # Limit between 1 and 100
        
        # Get current session ID
        session_id = session.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID not found',
                'message': 'No session ID available in current session'
            }), 404
        
        # Get session activity
        activities = session_manager.get_session_activity(session_id, limit)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'total_activities': len(activities),
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_session_activity: {e}")
        return jsonify({
            'success': False,
            'error': 'Activity retrieval error',
            'message': 'An error occurred while retrieving session activity'
        }), 500

@session_api_bp.route('/api/session/statistics', methods=['GET'])
@rate_limit_session_api
@require_valid_session_api
def get_session_statistics():
    """
    Get session statistics
    
    Response:
    {
        "success": true,
        "statistics": {
            "total_sessions": 1,
            "active_sessions": 1,
            "session_timeout_hours": 8,
            "max_sessions_per_user": 3,
            "current_user_id": 1,
            "session_created_at": "2023-12-09T10:00:00",
            "last_activity": "2023-12-09T10:30:00"
        }
    }
    """
    try:
        # Get session statistics
        statistics = session_manager.get_session_statistics()
        
        # Add additional statistics
        statistics.update({
            'current_endpoint': request.endpoint,
            'request_method': request.method,
            'client_ip': security_manager._get_client_ip(),
            'user_agent_summary': session_manager._summarize_user_agent(request.headers.get('User-Agent', ''))
        })
        
        return jsonify({
            'success': True,
            'statistics': statistics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_session_statistics: {e}")
        return jsonify({
            'success': False,
            'error': 'Statistics retrieval error',
            'message': 'An error occurred while retrieving session statistics'
        }), 500

# Helper functions

def _analyze_ip_risk(ip_address: str) -> Dict[str, Any]:
    """Analyze IP address for security risks"""
    if not ip_address:
        return {'risk': 'unknown', 'suspicious': False, 'details': 'No IP address'}
    
    risk_score = 0
    risk_factors = []
    
    # Check for private IP ranges
    if ip_address.startswith(('192.168.', '10.', '172.')):
        risk_score -= 10  # Lower risk for private IPs
        risk_factors.append('Private IP address')
    
    # Check for localhost
    if ip_address in ['127.0.0.1', '::1', 'localhost']:
        risk_score -= 20
        risk_factors.append('Localhost connection')
    
    # Check for common VPN/proxy patterns (simplified)
    if any(pattern in ip_address for pattern in ['vpn', 'proxy', 'tor']):
        risk_score += 15
        risk_factors.append('Potential VPN/Proxy detected')
    
    # Determine risk level
    if risk_score >= 20:
        risk_level = 'high'
        suspicious = True
    elif risk_score >= 10:
        risk_level = 'medium'
        suspicious = False
    elif risk_score >= 0:
        risk_level = 'low'
        suspicious = False
    else:
        risk_level = 'minimal'
        suspicious = False
    
    return {
        'risk_level': risk_level,
        'suspicious': suspicious,
        'risk_score': risk_score,
        'factors': risk_factors,
        'ip_address': ip_address
    }

def _analyze_device_risk(user_agent: str) -> Dict[str, Any]:
    """Analyze user agent for security risks"""
    if not user_agent:
        return {'risk': 'unknown', 'suspicious': True, 'details': 'No user agent'}
    
    risk_score = 0
    risk_factors = []
    
    # Check for common browsers
    common_browsers = ['Chrome', 'Firefox', 'Safari', 'Edge', 'Opera']
    if not any(browser in user_agent for browser in common_browsers):
        risk_score += 15
        risk_factors.append('Uncommon browser detected')
    
    # Check for bots/crawlers
    bot_indicators = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget']
    if any(indicator in user_agent.lower() for indicator in bot_indicators):
        risk_score += 25
        risk_factors.append('Bot or automated tool detected')
    
    # Check for empty or very short user agents
    if len(user_agent) < 10:
        risk_score += 20
        risk_factors.append('Suspiciously short user agent')
    
    # Determine risk level
    if risk_score >= 25:
        risk_level = 'high'
        suspicious = True
    elif risk_score >= 15:
        risk_level = 'medium'
        suspicious = False
    elif risk_score >= 5:
        risk_level = 'low'
        suspicious = False
    else:
        risk_level = 'minimal'
        suspicious = False
    
    return {
        'risk_level': risk_level,
        'suspicious': suspicious,
        'risk_score': risk_score,
        'factors': risk_factors,
        'user_agent_length': len(user_agent)
    }

def _calculate_session_age_hours(created_at: str) -> float:
    """Calculate session age in hours"""
    try:
        if not created_at:
            return 0
        
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.utcnow()
        age_seconds = (now - created_dt).total_seconds()
        return age_seconds / 3600  # Convert to hours
        
    except (ValueError, TypeError):
        return 0

def _calculate_idle_time_minutes(last_activity: str) -> float:
    """Calculate idle time in minutes"""
    try:
        if not last_activity:
            return 0
        
        activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        now = datetime.utcnow()
        idle_seconds = (now - activity_dt).total_seconds()
        return idle_seconds / 60  # Convert to minutes
        
    except (ValueError, TypeError):
        return 0

# Error handlers for session API
@session_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@session_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@session_api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': 'The requested resource was not found'
    }), 404

@session_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@session_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500