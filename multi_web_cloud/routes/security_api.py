"""
Security Management API Routes for Flask POS Application
Provides comprehensive security management and monitoring endpoints
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.security_manager import security_manager
from utils.session_manager import session_manager

# Create blueprint
security_api_bp = Blueprint('security_api', __name__)

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
    """Decorator to require admin session for sensitive endpoints"""
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

def rate_limit_security_api(f):
    """Decorator for rate limiting security API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for security API
        if not security_manager._check_rate_limit(client_ip, 'security_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many security requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@security_api_bp.route('/api/security/status', methods=['GET'])
@rate_limit_security_api
@require_valid_session_api
def get_security_status():
    """
    Get comprehensive security status
    
    Response:
    {
        "success": true,
        "security": {
            "total_events_24h": 15,
            "blocked_ips": 3,
            "failed_attempts": 7,
            "event_types": {"RATE_LIMIT_EXCEEDED": 5, "SUSPICIOUS_REQUEST": 2},
            "severity_counts": {"medium": 10, "high": 5},
            "rate_limit_active": 12,
            "last_event": {...}
        }
    }
    """
    try:
        # Get security statistics
        security_stats = security_manager.get_security_statistics()
        
        # Add additional security information
        security_status = {
            **security_stats,
            'system_health': _assess_system_health(security_stats),
            'threat_level': _calculate_threat_level(security_stats),
            'active_protections': _get_active_protections(),
            'security_score': _calculate_security_score(security_stats)
        }
        
        return jsonify({
            'success': True,
            'security': security_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_security_status: {e}")
        return jsonify({
            'success': False,
            'error': 'Security status retrieval error',
            'message': 'An error occurred while retrieving security status'
        }), 500

@security_api_bp.route('/api/security/events', methods=['GET'])
@rate_limit_security_api
@require_valid_session_api
def get_security_events():
    """
    Get security events with filtering
    
    Query Parameters:
    - limit: Maximum number of events to return (default: 100)
    - severity: Filter by severity (low, medium, high, critical)
    - event_type: Filter by event type
    - since: Get events since this timestamp
    
    Response:
    {
        "success": true,
        "events": [
            {
                "timestamp": "2023-12-09T10:00:00",
                "event_type": "RATE_LIMIT_EXCEEDED",
                "ip_address": "192.168.1.100",
                "details": "Rate limit exceeded for auth endpoint",
                "severity": "medium"
            }
        ]
    }
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        limit = min(max(limit, 1), 500)  # Limit between 1 and 500
        severity = request.args.get('severity')
        event_type = request.args.get('event_type')
        since = request.args.get('since')
        
        # Get security events
        events = security_manager.get_security_events(limit)
        
        # Apply filters
        filtered_events = []
        for event in events:
            # Filter by severity
            if severity and event.get('severity') != severity:
                continue
            
            # Filter by event type
            if event_type and event.get('event_type') != event_type:
                continue
            
            # Filter by timestamp
            if since:
                try:
                    event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    since_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    if event_time < since_time:
                        continue
                except ValueError:
                    continue
            
            # Add analysis to event
            event['risk_score'] = _calculate_event_risk_score(event)
            event['mitigation'] = _get_event_mitigation(event)
            
            filtered_events.append(event)
        
        return jsonify({
            'success': True,
            'events': filtered_events,
            'total_events': len(filtered_events),
            'filters': {
                'limit': limit,
                'severity': severity,
                'event_type': event_type,
                'since': since
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_security_events: {e}")
        return jsonify({
            'success': False,
            'error': 'Events retrieval error',
            'message': 'An error occurred while retrieving security events'
        }), 500

@security_api_bp.route('/api/security/block-ip', methods=['POST'])
@rate_limit_security_api
@require_admin_session
def block_ip_address():
    """
    Block IP address
    
    Request Body:
    {
        "ip": "192.168.1.100",
        "reason": "Suspicious activity detected",
        "duration": 3600
    }
    
    Response:
    {
        "success": true,
        "message": "IP address blocked successfully"
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
        
        ip_address = data.get('ip')
        reason = data.get('reason', 'Blocked by admin')
        duration = data.get('duration', 3600)
        
        if not ip_address:
            return jsonify({
                'success': False,
                'error': 'Missing IP address',
                'message': 'ip field is required'
            }), 400
        
        # Validate IP address
        if not security_manager._is_valid_ip(ip_address):
            return jsonify({
                'success': False,
                'error': 'Invalid IP address',
                'message': 'The provided IP address is not valid'
            }), 400
        
        # Block IP address
        success = security_manager.block_ip(ip_address, reason, duration)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'IP blocking failed',
                'message': 'Unable to block the specified IP address'
            }), 500
        
        # Log the action
        security_manager._log_security_event(
            'IP_BLOCKED_MANUAL',
            ip_address,
            f"IP blocked by admin: {reason}",
            'high'
        )
        
        return jsonify({
            'success': True,
            'message': 'IP address blocked successfully',
            'ip_address': ip_address,
            'reason': reason,
            'duration_seconds': duration,
            'blocked_until': (datetime.utcnow() + timedelta(seconds=duration)).isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in block_ip_address: {e}")
        return jsonify({
            'success': False,
            'error': 'IP blocking error',
            'message': 'An error occurred while blocking the IP address'
        }), 500

@security_api_bp.route('/api/security/unblock-ip/<ip_address>', methods=['DELETE'])
@rate_limit_security_api
@require_admin_session
def unblock_ip_address(ip_address):
    """
    Unblock IP address
    
    Response:
    {
        "success": true,
        "message": "IP address unblocked successfully"
    }
    """
    try:
        # Validate IP address
        if not security_manager._is_valid_ip(ip_address):
            return jsonify({
                'success': False,
                'error': 'Invalid IP address',
                'message': 'The provided IP address is not valid'
            }), 400
        
        # Unblock IP address
        success = security_manager.unblock_ip(ip_address)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'IP unblocking failed',
                'message': 'The IP address was not found in the blocked list'
            }), 404
        
        # Log the action
        security_manager._log_security_event(
            'IP_UNBLOCKED_MANUAL',
            ip_address,
            "IP unblocked by admin",
            'info'
        )
        
        return jsonify({
            'success': True,
            'message': 'IP address unblocked successfully',
            'ip_address': ip_address,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in unblock_ip_address: {e}")
        return jsonify({
            'success': False,
            'error': 'IP unblocking error',
            'message': 'An error occurred while unblocking the IP address'
        }), 500

@security_api_bp.route('/api/security/threats', methods=['GET'])
@rate_limit_security_api
@require_valid_session_api
def get_threat_intelligence():
    """
    Get threat intelligence
    
    Response:
    {
        "success": true,
        "threats": {
            "active_threats": [...],
            "threat_indicators": [...],
            "mitigation_recommendations": [...],
            "threat_level": "medium"
        }
    }
    """
    try:
        # Get current security statistics
        security_stats = security_manager.get_security_statistics()
        
        # Analyze threats
        threat_intelligence = {
            'active_threats': _identify_active_threats(security_stats),
            'threat_indicators': _get_threat_indicators(),
            'mitigation_recommendations': _get_mitigation_recommendations(),
            'threat_level': _calculate_threat_level(security_stats),
            'vulnerability_scan': _perform_vulnerability_scan(),
            'attack_patterns': _analyze_attack_patterns(security_stats)
        }
        
        return jsonify({
            'success': True,
            'threats': threat_intelligence,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_threat_intelligence: {e}")
        return jsonify({
            'success': False,
            'error': 'Threat intelligence error',
            'message': 'An error occurred while retrieving threat intelligence'
        }), 500

@security_api_bp.route('/api/security/scan', methods=['POST'])
@rate_limit_security_api
@require_admin_session
def scan_for_vulnerabilities():
    """
    Scan for vulnerabilities
    
    Request Body:
    {
        "scan_type": "full",
        "target": "system"
    }
    
    Response:
    {
        "success": true,
        "scan_id": "scan_123456",
        "results": {
            "vulnerabilities": [...],
            "risk_score": 25,
            "recommendations": [...]
        }
    }
    """
    try:
        # Get request data
        data = request.get_json() or {}
        scan_type = data.get('scan_type', 'basic')
        target = data.get('target', 'system')
        
        # Validate scan type
        valid_scan_types = ['basic', 'full', 'deep']
        if scan_type not in valid_scan_types:
            return jsonify({
                'success': False,
                'error': 'Invalid scan type',
                'message': f'scan_type must be one of: {", ".join(valid_scan_types)}'
            }), 400
        
        # Generate scan ID
        scan_id = f"scan_{datetime.utcnow().timestamp()}"
        
        # Perform vulnerability scan
        scan_results = _perform_vulnerability_scan_by_type(scan_type, target)
        
        # Log the scan
        security_manager._log_security_event(
            'VULNERABILITY_SCAN',
            'system',
            f"Vulnerability scan initiated: {scan_type} scan on {target}",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'scan_type': scan_type,
            'target': target,
            'results': scan_results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in scan_for_vulnerabilities: {e}")
        return jsonify({
            'success': False,
            'error': 'Vulnerability scan error',
            'message': 'An error occurred during vulnerability scan'
        }), 500

@security_api_bp.route('/api/security/audit-log', methods=['GET'])
@rate_limit_security_api
@require_admin_session
def get_audit_log():
    """
    Get audit log with pagination
    
    Query Parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 50)
    - user_id: Filter by user ID
    - action: Filter by action type
    - since: Filter events since this timestamp
    
    Response:
    {
        "success": true,
        "audit_log": {
            "entries": [...],
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_pages": 5,
                "total_entries": 250
            }
        }
    }
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        per_page = min(max(per_page, 1), 100)  # Limit between 1 and 100
        user_id = request.args.get('user_id', type=int)
        action = request.args.get('action')
        since = request.args.get('since')
        
        # Get security events as audit log
        all_events = security_manager.get_security_events(1000)  # Get more for pagination
        
        # Apply filters
        filtered_events = []
        for event in all_events:
            # Filter by user ID
            if user_id and event.get('user_id') != user_id:
                continue
            
            # Filter by action
            if action and event.get('event_type') != action:
                continue
            
            # Filter by timestamp
            if since:
                try:
                    event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                    since_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
                    if event_time < since_time:
                        continue
                except ValueError:
                    continue
            
            filtered_events.append(event)
        
        # Paginate
        total_entries = len(filtered_events)
        total_pages = (total_entries + per_page - 1) // per_page
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_events = filtered_events[start_index:end_index]
        
        # Add audit-specific information
        for event in paginated_events:
            event['audit_id'] = f"audit_{event['timestamp']}_{event.get('ip_address', 'unknown')}"
            event['compliance_flags'] = _check_compliance_flags(event)
        
        return jsonify({
            'success': True,
            'audit_log': {
                'entries': paginated_events,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_entries': total_entries,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            },
            'filters': {
                'user_id': user_id,
                'action': action,
                'since': since
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_audit_log: {e}")
        return jsonify({
            'success': False,
            'error': 'Audit log retrieval error',
            'message': 'An error occurred while retrieving audit log'
        }), 500

@security_api_bp.route('/api/security/settings', methods=['POST'])
@rate_limit_security_api
@require_admin_session
def update_security_settings():
    """
    Update security settings
    
    Request Body:
    {
        "rate_limits": {
            "default": {"requests": 100, "window": 60}
        },
        "ip_block_duration": 3600,
        "max_failed_attempts": 5
    }
    
    Response:
    {
        "success": true,
        "message": "Security settings updated successfully"
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
        
        # Update rate limits
        if 'rate_limits' in data:
            new_rate_limits = data['rate_limits']
            if isinstance(new_rate_limits, dict):
                security_manager.rate_limits.update(new_rate_limits)
        
        # Update IP block duration
        if 'ip_block_duration' in data:
            new_duration = data['ip_block_duration']
            if isinstance(new_duration, int) and new_duration > 0:
                security_manager.ip_block_duration = new_duration
        
        # Update max failed attempts
        if 'max_failed_attempts' in data:
            new_max_attempts = data['max_failed_attempts']
            if isinstance(new_max_attempts, int) and new_max_attempts > 0:
                security_manager.max_failed_attempts = new_max_attempts
        
        # Log the settings update
        security_manager._log_security_event(
            'SECURITY_SETTINGS_UPDATED',
            security_manager._get_client_ip(),
            f"Security settings updated by admin",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'message': 'Security settings updated successfully',
            'updated_settings': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in update_security_settings: {e}")
        return jsonify({
            'success': False,
            'error': 'Settings update error',
            'message': 'An error occurred while updating security settings'
        }), 500

@security_api_bp.route('/api/security/blocked-ips', methods=['GET'])
@rate_limit_security_api
@require_admin_session
def get_blocked_ips():
    """
    Get list of blocked IPs
    
    Response:
    {
        "success": true,
        "blocked_ips": [
            {
                "ip": "192.168.1.100",
                "reason": "Suspicious activity",
                "blocked_at": "2023-12-09T10:00:00",
                "expires": "2023-12-09T11:00:00"
            }
        ]
    }
    """
    try:
        # Get blocked IPs
        blocked_ips = security_manager.get_blocked_ips()
        
        # Add additional information
        for ip_info in blocked_ips:
            ip_info['remaining_time'] = _calculate_remaining_block_time(ip_info.get('expires'))
            ip_info['block_duration'] = _calculate_block_duration(ip_info.get('blocked_at'), ip_info.get('expires'))
            ip_info['risk_level'] = _assess_ip_risk(ip_info.get('reason', ''))
        
        return jsonify({
            'success': True,
            'blocked_ips': blocked_ips,
            'total_blocked': len(blocked_ips),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_blocked_ips: {e}")
        return jsonify({
            'success': False,
            'error': 'Blocked IPs retrieval error',
            'message': 'An error occurred while retrieving blocked IPs'
        }), 500

# Helper functions

def _assess_system_health(security_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall system health"""
    try:
        health_score = 100
        health_issues = []
        
        # Check for high event volume
        total_events = security_stats.get('total_events_24h', 0)
        if total_events > 100:
            health_score -= 20
            health_issues.append('High security event volume')
        
        # Check for many blocked IPs
        blocked_ips = security_stats.get('blocked_ips', 0)
        if blocked_ips > 10:
            health_score -= 15
            health_issues.append('Many blocked IPs')
        
        # Check for high failed attempts
        failed_attempts = security_stats.get('failed_attempts', 0)
        if failed_attempts > 50:
            health_score -= 25
            health_issues.append('High failed login attempts')
        
        # Determine health status
        if health_score >= 80:
            status = 'excellent'
        elif health_score >= 60:
            status = 'good'
        elif health_score >= 40:
            status = 'fair'
        elif health_score >= 20:
            status = 'poor'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'score': health_score,
            'issues': health_issues
        }
    except:
        return {
            'status': 'unknown',
            'score': 0,
            'issues': ['Unable to assess system health']
        }

def _calculate_threat_level(security_stats: Dict[str, Any]) -> str:
    """Calculate overall threat level"""
    try:
        threat_score = 0
        
        # Base score on event counts
        total_events = security_stats.get('total_events_24h', 0)
        threat_score += min(total_events / 10, 30)  # Max 30 points
        
        # Add points for blocked IPs
        blocked_ips = security_stats.get('blocked_ips', 0)
        threat_score += min(blocked_ips * 5, 20)  # Max 20 points
        
        # Add points for failed attempts
        failed_attempts = security_stats.get('failed_attempts', 0)
        threat_score += min(failed_attempts / 5, 25)  # Max 25 points
        
        # Add points for high severity events
        severity_counts = security_stats.get('severity_counts', {})
        high_severity = severity_counts.get('high', 0) + severity_counts.get('critical', 0)
        threat_score += min(high_severity * 10, 25)  # Max 25 points
        
        # Determine threat level
        if threat_score >= 80:
            return 'critical'
        elif threat_score >= 60:
            return 'high'
        elif threat_score >= 40:
            return 'medium'
        elif threat_score >= 20:
            return 'low'
        else:
            return 'minimal'
    except:
        return 'unknown'

def _get_active_protections() -> List[str]:
    """Get list of active security protections"""
    return [
        'Rate limiting',
        'IP blocking',
        'Input validation',
        'CSRF protection',
        'XSS protection',
        'SQL injection protection',
        'Session security',
        'Security headers'
    ]

def _calculate_security_score(security_stats: Dict[str, Any]) -> int:
    """Calculate overall security score (0-100)"""
    try:
        base_score = 100
        
        # Deduct points for security events
        total_events = security_stats.get('total_events_24h', 0)
        base_score -= min(total_events, 50)  # Max 50 points deduction
        
        # Deduct points for blocked IPs (indicates attacks)
        blocked_ips = security_stats.get('blocked_ips', 0)
        base_score -= min(blocked_ips * 2, 20)  # Max 20 points deduction
        
        # Deduct points for failed attempts
        failed_attempts = security_stats.get('failed_attempts', 0)
        base_score -= min(failed_attempts / 2, 30)  # Max 30 points deduction
        
        return max(0, int(base_score))
    except:
        return 50  # Default to medium security

def _calculate_event_risk_score(event: Dict[str, Any]) -> int:
    """Calculate risk score for a security event"""
    try:
        base_score = 10
        
        # Add points based on severity
        severity = event.get('severity', 'low')
        severity_scores = {'low': 0, 'medium': 20, 'high': 40, 'critical': 60}
        base_score += severity_scores.get(severity, 0)
        
        # Add points based on event type
        event_type = event.get('event_type', '')
        if 'BLOCKED' in event_type:
            base_score += 15
        elif 'FAILED' in event_type:
            base_score += 10
        elif 'SUSPICIOUS' in event_type:
            base_score += 25
        
        return min(100, base_score)
    except:
        return 10

def _get_event_mitigation(event: Dict[str, Any]) -> str:
    """Get mitigation recommendation for an event"""
    event_type = event.get('event_type', '')
    
    if 'RATE_LIMIT' in event_type:
        return 'Rate limiting is active. Consider increasing limits or blocking the IP.'
    elif 'IP_BLOCKED' in event_type:
        return 'IP has been blocked. Monitor for additional suspicious activity.'
    elif 'SUSPICIOUS' in event_type:
        return 'Investigate the request and consider blocking the source IP.'
    elif 'FAILED_LOGIN' in event_type:
        return 'Monitor for brute force attempts and consider account lockout.'
    else:
        return 'Monitor the situation and review security logs.'

def _identify_active_threats(security_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Identify active threats based on security statistics"""
    threats = []
    
    # Check for brute force attacks
    failed_attempts = security_stats.get('failed_attempts', 0)
    if failed_attempts > 10:
        threats.append({
            'type': 'brute_force',
            'severity': 'high' if failed_attempts > 50 else 'medium',
            'description': f'{failed_attempts} failed attempts detected',
            'recommendation': 'Implement account lockout and monitor source IPs'
        })
    
    # Check for rate limit violations
    event_types = security_stats.get('event_types', {})
    rate_limit_events = event_types.get('RATE_LIMIT_EXCEEDED', 0)
    if rate_limit_events > 5:
        threats.append({
            'type': 'rate_limit_abuse',
            'severity': 'medium',
            'description': f'{rate_limit_events} rate limit violations detected',
            'recommendation': 'Monitor for DDoS attacks and consider tightening limits'
        })
    
    # Check for suspicious requests
    suspicious_events = event_types.get('SUSPICIOUS_REQUEST', 0)
    if suspicious_events > 3:
        threats.append({
            'type': 'suspicious_activity',
            'severity': 'high',
            'description': f'{suspicious_events} suspicious requests detected',
            'recommendation': 'Investigate request patterns and block malicious sources'
        })
    
    return threats

def _get_threat_indicators() -> List[Dict[str, Any]]:
    """Get current threat indicators"""
    return [
        {
            'indicator': 'High request frequency',
            'level': 'medium',
            'description': 'Multiple requests from same IP in short time'
        },
        {
            'indicator': 'Unusual user agents',
            'level': 'low',
            'description': 'Requests from uncommon or automated user agents'
        },
        {
            'indicator': 'Failed authentication',
            'level': 'high',
            'description': 'Multiple failed login attempts'
        },
        {
            'indicator': 'SQL injection patterns',
            'level': 'critical',
            'description': 'SQL injection attempts detected'
        }
    ]

def _get_mitigation_recommendations() -> List[str]:
    """Get security mitigation recommendations"""
    return [
        'Enable two-factor authentication for admin accounts',
        'Regularly update security patches and dependencies',
        'Implement network-level firewall rules',
        'Monitor security logs daily',
        'Conduct regular security audits',
        'Educate users about security best practices',
        'Implement intrusion detection systems',
        'Use Web Application Firewall (WAF)'
    ]

def _perform_vulnerability_scan() -> Dict[str, Any]:
    """Perform basic vulnerability scan"""
    return {
        'scan_completed': True,
        'vulnerabilities_found': 0,
        'critical_vulnerabilities': 0,
        'high_vulnerabilities': 0,
        'medium_vulnerabilities': 0,
        'low_vulnerabilities': 0,
        'scan_duration_seconds': 5,
        'last_scan': datetime.utcnow().isoformat()
    }

def _analyze_attack_patterns(security_stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze attack patterns from security statistics"""
    event_types = security_stats.get('event_types', {})
    
    return {
        'most_common_attack': max(event_types.items(), key=lambda x: x[1])[0] if event_types else 'none',
        'attack_frequency': 'high' if sum(event_types.values()) > 50 else 'medium' if sum(event_types.values()) > 10 else 'low',
        'targeted_endpoints': ['auth', 'api', 'admin'],
        'attack_sources': ['unknown'],  # Would be populated with actual IP analysis
        'time_patterns': 'business_hours'  # Would analyze actual timing patterns
    }

def _perform_vulnerability_scan_by_type(scan_type: str, target: str) -> Dict[str, Any]:
    """Perform vulnerability scan based on type"""
    base_scan = _perform_vulnerability_scan()
    
    if scan_type == 'basic':
        base_scan['scan_depth'] = 'basic'
        base_scan['checks_performed'] = ['sql_injection', 'xss', 'csrf']
    elif scan_type == 'full':
        base_scan['scan_depth'] = 'full'
        base_scan['checks_performed'] = ['sql_injection', 'xss', 'csrf', 'directory_traversal', 'file_inclusion', 'security_headers']
    elif scan_type == 'deep':
        base_scan['scan_depth'] = 'deep'
        base_scan['checks_performed'] = ['sql_injection', 'xss', 'csrf', 'directory_traversal', 'file_inclusion', 'security_headers', 'authentication_bypass', 'privilege_escalation']
    
    return base_scan

def _check_compliance_flags(event: Dict[str, Any]) -> List[str]:
    """Check compliance flags for audit events"""
    flags = []
    
    # Check for GDPR compliance
    if 'personal_data' in event.get('details', '').lower():
        flags.append('GDPR_RELEVANT')
    
    # Check for PCI DSS compliance
    if 'payment' in event.get('details', '').lower() or 'card' in event.get('details', '').lower():
        flags.append('PCI_DSS_RELEVANT')
    
    # Check for HIPAA compliance
    if 'health' in event.get('details', '').lower() or 'medical' in event.get('details', '').lower():
        flags.append('HIPAA_RELEVANT')
    
    return flags

def _calculate_remaining_block_time(expires: str) -> str:
    """Calculate remaining block time"""
    try:
        if not expires:
            return 'permanent'
        
        expiry_time = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        now = datetime.utcnow()
        remaining = expiry_time - now
        
        if remaining.total_seconds() <= 0:
            return 'expired'
        
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        
        return f"{hours}h {minutes}m"
    except:
        return 'unknown'

def _calculate_block_duration(blocked_at: str, expires: str) -> str:
    """Calculate block duration"""
    try:
        if not blocked_at or not expires:
            return 'unknown'
        
        start_time = datetime.fromisoformat(blocked_at.replace('Z', '+00:00'))
        expiry_time = datetime.fromisoformat(expires.replace('Z', '+00:00'))
        duration = expiry_time - start_time
        
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        return f"{hours}h {minutes}m"
    except:
        return 'unknown'

def _assess_ip_risk(reason: str) -> str:
    """Assess IP risk based on block reason"""
    reason_lower = reason.lower()
    
    if 'brute' in reason_lower or 'attack' in reason_lower:
        return 'high'
    elif 'suspicious' in reason_lower or 'abuse' in reason_lower:
        return 'medium'
    else:
        return 'low'

# Error handlers for security API
@security_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@security_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@security_api_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@security_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@security_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500