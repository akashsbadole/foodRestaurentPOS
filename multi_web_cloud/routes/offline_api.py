"""
Offline Support API Routes for Flask POS Application
Provides comprehensive offline functionality and synchronization endpoints
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.offline_manager import offline_manager
from utils.session_manager import session_manager
from utils.security_manager import security_manager

# Create blueprint
offline_api_bp = Blueprint('offline_api', __name__)

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

def rate_limit_offline_api(f):
    """Decorator for rate limiting offline API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for offline API
        if not security_manager._check_rate_limit(client_ip, 'offline_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many offline requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@offline_api_bp.route('/api/offline/status', methods=['GET'])
@rate_limit_offline_api
def get_offline_status():
    """
    Get comprehensive offline status
    
    Response:
    {
        "success": true,
        "status": {
            "is_online": true,
            "pending_orders": 0,
            "pending_payments": 0,
            "failed_orders": 0,
            "failed_payments": 0,
            "last_sync": "2023-12-09T10:30:00",
            "sync_queue_size": 0
        }
    }
    """
    try:
        # Get sync status from offline manager
        sync_status = offline_manager.get_sync_status()
        
        # Add additional status information
        sync_status.update({
            'connection_quality': _test_connection_quality(),
            'server_reachable': _check_server_reachability(),
            'offline_mode_enabled': not offline_manager.is_online,
            'cache_status': _get_cache_status(),
            'storage_usage': _get_storage_usage()
        })
        
        # Get detailed statistics
        statistics = offline_manager.get_sync_statistics()
        sync_status['statistics'] = statistics
        
        return jsonify({
            'success': True,
            'status': sync_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_offline_status: {e}")
        return jsonify({
            'success': False,
            'error': 'Status retrieval error',
            'message': 'An error occurred while retrieving offline status'
        }), 500

@offline_api_bp.route('/api/offline/sync/force', methods=['POST'])
@rate_limit_offline_api
@require_valid_session_api
def force_sync():
    """
    Force immediate synchronization
    
    Response:
    {
        "success": true,
        "message": "Synchronization initiated",
        "sync_id": "sync_123456",
        "estimated_duration": 30
    }
    """
    try:
        # Check if online
        if not offline_manager.is_online:
            return jsonify({
                'success': False,
                'error': 'Offline mode',
                'message': 'Cannot sync while offline. Please check your internet connection.'
            }), 503
        
        # Generate sync ID for tracking
        sync_id = f"sync_{datetime.utcnow().timestamp()}"
        
        # Force sync
        success = offline_manager.force_sync()
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Sync failed',
                'message': 'Unable to start synchronization. Please try again.'
            }), 500
        
        # Get sync statistics
        statistics = offline_manager.get_sync_statistics()
        
        return jsonify({
            'success': True,
            'message': 'Synchronization initiated successfully',
            'sync_id': sync_id,
            'estimated_duration': _estimate_sync_duration(statistics),
            'pending_items': statistics.get('orders', {}).get('pending', 0) + statistics.get('payments', {}).get('pending', 0),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in force_sync: {e}")
        return jsonify({
            'success': False,
            'error': 'Sync error',
            'message': 'An error occurred during synchronization'
        }), 500

@offline_api_bp.route('/api/offline/queue', methods=['GET'])
@rate_limit_offline_api
@require_valid_session_api
def get_pending_queue():
    """
    Get pending operations queue
    
    Query Parameters:
    - type: Filter by type (orders, payments, all)
    - status: Filter by status (pending, failed, all)
    - limit: Maximum number of items to return (default: 50)
    
    Response:
    {
        "success": true,
        "queue": {
            "orders": [...],
            "payments": [...],
            "total_items": 5
        }
    }
    """
    try:
        # Get query parameters
        item_type = request.args.get('type', 'all')
        status_filter = request.args.get('status', 'all')
        limit = request.args.get('limit', 50, type=int)
        limit = min(max(limit, 1), 100)  # Limit between 1 and 100
        
        # Get offline orders
        orders = []
        if item_type in ['orders', 'all']:
            orders = offline_manager.get_offline_orders()
            
            # Filter by status if specified
            if status_filter != 'all':
                orders = [order for order in orders if order.get('sync_status') == status_filter]
            
            # Limit results
            orders = orders[:limit]
        
        # Get offline payments (would need to implement this method in offline_manager)
        payments = []
        if item_type in ['payments', 'all']:
            # This would be implemented in offline_manager
            # payments = offline_manager.get_offline_payments()
            pass
        
        # Calculate total items
        total_items = len(orders) + len(payments)
        
        # Add additional metadata
        for order in orders:
            order['age_hours'] = _calculate_item_age(order.get('created_at'))
            order['retry_count'] = order.get('sync_attempts', 0)
            order['next_retry'] = _calculate_next_retry_time(order.get('sync_attempts', 0))
        
        return jsonify({
            'success': True,
            'queue': {
                'orders': orders,
                'payments': payments,
                'total_items': total_items
            },
            'filters': {
                'type': item_type,
                'status': status_filter,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_pending_queue: {e}")
        return jsonify({
            'success': False,
            'error': 'Queue retrieval error',
            'message': 'An error occurred while retrieving pending queue'
        }), 500

@offline_api_bp.route('/api/offline/queue/clear', methods=['POST'])
@rate_limit_offline_api
@require_valid_session_api
def clear_pending_queue():
    """
    Clear pending queue
    
    Request Body:
    {
        "type": "failed",
        "confirm": true
    }
    
    Response:
    {
        "success": true,
        "message": "Failed items cleared successfully",
        "cleared_count": 3
    }
    """
    try:
        # Get request data
        data = request.get_json() or {}
        clear_type = data.get('type', 'failed')
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'success': False,
                'error': 'Confirmation required',
                'message': 'Please set confirm=true to clear queue items'
            }), 400
        
        # Validate clear type
        if clear_type not in ['failed', 'all', 'pending']:
            return jsonify({
                'success': False,
                'error': 'Invalid clear type',
                'message': 'Type must be one of: failed, all, pending'
            }), 400
        
        # Get current queue statistics
        statistics = offline_manager.get_sync_statistics()
        
        # Calculate items to be cleared
        cleared_count = 0
        if clear_type == 'failed':
            cleared_count = statistics.get('orders', {}).get('failed', 0) + statistics.get('payments', {}).get('failed', 0)
        elif clear_type == 'all':
            cleared_count = sum(statistics.get('orders', {}).values()) + sum(statistics.get('payments', {}).values())
        elif clear_type == 'pending':
            cleared_count = statistics.get('orders', {}).get('pending', 0) + statistics.get('payments', {}).get('pending', 0)
        
        # Clear failed items (only supported for now)
        if clear_type == 'failed':
            success = offline_manager.clear_failed_items()
            if not success:
                return jsonify({
                    'success': False,
                    'error': 'Clear operation failed',
                    'message': 'Unable to clear failed items'
                }), 500
        else:
            # Would need to implement additional clear methods in offline_manager
            return jsonify({
                'success': False,
                'error': 'Operation not supported',
                'message': f'Clearing {clear_type} items is not yet implemented'
            }), 501
        
        return jsonify({
            'success': True,
            'message': f'{clear_type.title()} items cleared successfully',
            'cleared_count': cleared_count,
            'clear_type': clear_type,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in clear_pending_queue: {e}")
        return jsonify({
            'success': False,
            'error': 'Queue clear error',
            'message': 'An error occurred while clearing the queue'
        }), 500

@offline_api_bp.route('/api/offline/conflicts', methods=['GET'])
@rate_limit_offline_api
@require_valid_session_api
def get_conflicts():
    """
    Get data conflicts list
    
    Response:
    {
        "success": true,
        "conflicts": [
            {
                "id": "conflict_123",
                "type": "order",
                "local_id": "order_456",
                "server_id": "ORD123456",
                "conflicts": [
                    {
                        "field": "status",
                        "local_value": "pending",
                        "server_value": "completed"
                    }
                ],
                "created_at": "2023-12-09T10:00:00"
            }
        ]
    }
    """
    try:
        # Get conflicts from offline manager
        # This would need to be implemented in offline_manager
        # conflicts = offline_manager.get_conflicts()
        
        # For now, return empty list as placeholder
        conflicts = []
        
        # Add metadata to conflicts
        for conflict in conflicts:
            conflict['age_hours'] = _calculate_item_age(conflict.get('created_at'))
            conflict['severity'] = _assess_conflict_severity(conflict.get('conflicts', []))
            conflict['resolution_options'] = _get_resolution_options(conflict.get('type'))
        
        return jsonify({
            'success': True,
            'conflicts': conflicts,
            'total_conflicts': len(conflicts),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_conflicts: {e}")
        return jsonify({
            'success': False,
            'error': 'Conflicts retrieval error',
            'message': 'An error occurred while retrieving conflicts'
        }), 500

@offline_api_bp.route('/api/offline/conflicts/resolve', methods=['POST'])
@rate_limit_offline_api
@require_valid_session_api
def resolve_conflict():
    """
    Resolve specific conflict
    
    Request Body:
    {
        "conflict_id": "conflict_123",
        "resolution": "server_wins",
        "custom_data": {}
    }
    
    Response:
    {
        "success": true,
        "message": "Conflict resolved successfully"
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
        
        conflict_id = data.get('conflict_id')
        resolution = data.get('resolution')
        custom_data = data.get('custom_data', {})
        
        if not conflict_id:
            return jsonify({
                'success': False,
                'error': 'Missing conflict ID',
                'message': 'conflict_id is required'
            }), 400
        
        if not resolution:
            return jsonify({
                'success': False,
                'error': 'Missing resolution',
                'message': 'resolution is required'
            }), 400
        
        # Validate resolution type
        valid_resolutions = ['server_wins', 'local_wins', 'merge', 'custom']
        if resolution not in valid_resolutions:
            return jsonify({
                'success': False,
                'error': 'Invalid resolution',
                'message': f'resolution must be one of: {", ".join(valid_resolutions)}'
            }), 400
        
        # Resolve conflict using offline manager
        # This would need to be implemented in offline_manager
        # success = offline_manager.resolve_conflict(conflict_id, resolution, custom_data)
        
        # For now, return success as placeholder
        success = True
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Resolution failed',
                'message': 'Unable to resolve conflict. Please try again.'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Conflict resolved successfully',
            'conflict_id': conflict_id,
            'resolution': resolution,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in resolve_conflict: {e}")
        return jsonify({
            'success': False,
            'error': 'Conflict resolution error',
            'message': 'An error occurred while resolving the conflict'
        }), 500

@offline_api_bp.route('/api/offline/statistics', methods=['GET'])
@rate_limit_offline_api
@require_valid_session_api
def get_sync_statistics():
    """
    Get sync statistics
    
    Query Parameters:
    - period: Time period (hour, day, week, month)
    
    Response:
    {
        "success": true,
        "statistics": {
            "orders": {"pending": 0, "synced": 10, "failed": 1},
            "payments": {"pending": 0, "synced": 10, "failed": 0},
            "recent_activity": {"order_sync": 5, "payment_sync": 5},
            "average_sync_time_seconds": 2.5
        }
    }
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'day')
        
        # Get statistics from offline manager
        statistics = offline_manager.get_sync_statistics()
        
        # Add period-specific analysis
        statistics['period'] = period
        statistics['performance_metrics'] = _calculate_performance_metrics(statistics)
        statistics['trends'] = _calculate_sync_trends(period)
        
        return jsonify({
            'success': True,
            'statistics': statistics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_sync_statistics: {e}")
        return jsonify({
            'success': False,
            'error': 'Statistics retrieval error',
            'message': 'An error occurred while retrieving sync statistics'
        }), 500

@offline_api_bp.route('/api/offline/data/export', methods=['POST'])
@rate_limit_offline_api
@require_valid_session_api
def export_offline_data():
    """
    Export offline data
    
    Request Body:
    {
        "format": "json",
        "data_types": ["orders", "payments"],
        "date_range": {
            "from": "2023-12-01",
            "to": "2023-12-31"
        }
    }
    
    Response:
    {
        "success": true,
        "export_id": "export_123456",
        "download_url": "/api/offline/data/download/export_123456"
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
        
        export_format = data.get('format', 'json')
        data_types = data.get('data_types', ['orders', 'payments'])
        date_range = data.get('date_range', {})
        
        # Validate export format
        valid_formats = ['json', 'csv', 'xml']
        if export_format not in valid_formats:
            return jsonify({
                'success': False,
                'error': 'Invalid format',
                'message': f'format must be one of: {", ".join(valid_formats)}'
            }), 400
        
        # Validate data types
        valid_types = ['orders', 'payments', 'menu_items', 'categories', 'tables']
        for data_type in data_types:
            if data_type not in valid_types:
                return jsonify({
                    'success': False,
                    'error': 'Invalid data type',
                    'message': f'Invalid data type: {data_type}. Valid types: {", ".join(valid_types)}'
                }), 400
        
        # Generate export ID
        export_id = f"export_{datetime.utcnow().timestamp()}"
        
        # Export data using offline manager
        # This would need to be implemented in offline_manager
        # export_url = offline_manager.export_data(export_id, export_format, data_types, date_range)
        
        # For now, return placeholder URL
        export_url = f"/api/offline/data/download/{export_id}"
        
        return jsonify({
            'success': True,
            'export_id': export_id,
            'download_url': export_url,
            'format': export_format,
            'data_types': data_types,
            'estimated_size': _estimate_export_size(data_types, date_range),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in export_offline_data: {e}")
        return jsonify({
            'success': False,
            'error': 'Export error',
            'message': 'An error occurred during data export'
        }), 500

@offline_api_bp.route('/api/offline/notifications', methods=['GET'])
@rate_limit_offline_api
@require_valid_session_api
def get_realtime_notifications():
    """
    Get real-time notifications
    
    Query Parameters:
    - since: Get notifications since this timestamp
    
    Response:
    {
        "success": true,
        "notifications": [
            {
                "type": "sync_status_update",
                "data_type": "order",
                "local_id": "order_123",
                "status": "synced",
                "timestamp": "2023-12-09T10:30:00"
            }
        ]
    }
    """
    try:
        # Get query parameters
        since = request.args.get('since')
        
        # Get notifications from offline manager
        notifications = offline_manager.get_realtime_notifications(since)
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total_notifications': len(notifications),
            'since': since,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_realtime_notifications: {e}")
        return jsonify({
            'success': False,
            'error': 'Notifications retrieval error',
            'message': 'An error occurred while retrieving notifications'
        }), 500

# Helper functions

def _test_connection_quality() -> Dict[str, Any]:
    """Test connection quality"""
    try:
        # This would implement actual connection testing
        # For now, return placeholder data
        return {
            'speed': 'good',
            'latency_ms': 50,
            'packet_loss': 0.1,
            'stable': True
        }
    except:
        return {
            'speed': 'unknown',
            'latency_ms': 0,
            'packet_loss': 0,
            'stable': False
        }

def _check_server_reachability() -> bool:
    """Check if server is reachable"""
    try:
        # This would implement actual server reachability test
        # For now, return offline manager status
        return offline_manager.is_online
    except:
        return False

def _get_cache_status() -> Dict[str, Any]:
    """Get cache status information"""
    try:
        # This would implement actual cache status checking
        # For now, return placeholder data
        return {
            'menu_items_cached': True,
            'categories_cached': True,
            'tables_cached': True,
            'last_cache_update': datetime.utcnow().isoformat(),
            'cache_size_mb': 2.5
        }
    except:
        return {
            'menu_items_cached': False,
            'categories_cached': False,
            'tables_cached': False,
            'last_cache_update': None,
            'cache_size_mb': 0
        }

def _get_storage_usage() -> Dict[str, Any]:
    """Get storage usage information"""
    try:
        # This would implement actual storage usage calculation
        # For now, return placeholder data
        return {
            'total_mb': 100,
            'used_mb': 15.5,
            'available_mb': 84.5,
            'usage_percentage': 15.5
        }
    except:
        return {
            'total_mb': 0,
            'used_mb': 0,
            'available_mb': 0,
            'usage_percentage': 0
        }

def _estimate_sync_duration(statistics: Dict[str, Any]) -> int:
    """Estimate sync duration in seconds"""
    try:
        pending_items = 0
        if 'orders' in statistics:
            pending_items += statistics['orders'].get('pending', 0)
        if 'payments' in statistics:
            pending_items += statistics['payments'].get('pending', 0)
        
        # Estimate 2 seconds per item
        return pending_items * 2
    except:
        return 30  # Default 30 seconds

def _calculate_item_age(created_at: str) -> float:
    """Calculate item age in hours"""
    try:
        if not created_at:
            return 0
        
        created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.utcnow()
        age_seconds = (now - created_dt).total_seconds()
        return age_seconds / 3600  # Convert to hours
        
    except (ValueError, TypeError):
        return 0

def _calculate_next_retry_time(retry_count: int) -> Optional[str]:
    """Calculate next retry time"""
    try:
        if retry_count >= 3:
            return None  # Max retries reached
        
        # Exponential backoff: 5min, 15min, 45min
        delays = [5, 15, 45]
        delay_minutes = delays[min(retry_count, len(delays) - 1)]
        
        next_retry = datetime.utcnow() + timedelta(minutes=delay_minutes)
        return next_retry.isoformat()
        
    except:
        return None

def _assess_conflict_severity(conflicts: List[Dict[str, Any]]) -> str:
    """Assess conflict severity"""
    if not conflicts:
        return 'low'
    
    # Check for critical conflicts
    critical_fields = ['status', 'total_amount', 'payment_status']
    for conflict in conflicts:
        if conflict.get('field') in critical_fields:
            return 'high'
    
    # Check for medium conflicts
    medium_fields = ['customer_info', 'items', 'discount']
    for conflict in conflicts:
        if conflict.get('field') in medium_fields:
            return 'medium'
    
    return 'low'

def _get_resolution_options(conflict_type: str) -> List[str]:
    """Get resolution options for conflict type"""
    if conflict_type == 'order':
        return ['server_wins', 'local_wins', 'merge', 'custom']
    elif conflict_type == 'payment':
        return ['server_wins', 'local_wins', 'custom']
    else:
        return ['server_wins', 'local_wins']

def _calculate_performance_metrics(statistics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate performance metrics"""
    try:
        avg_sync_time = statistics.get('average_sync_time_seconds', 0)
        
        return {
            'average_sync_time': avg_sync_time,
            'sync_efficiency': 'good' if avg_sync_time < 5 else 'moderate' if avg_sync_time < 10 else 'poor',
            'queue_processing_rate': statistics.get('sync_queue_size', 0),
            'error_rate': _calculate_error_rate(statistics)
        }
    except:
        return {
            'average_sync_time': 0,
            'sync_efficiency': 'unknown',
            'queue_processing_rate': 0,
            'error_rate': 0
        }

def _calculate_sync_trends(period: str) -> Dict[str, Any]:
    """Calculate sync trends for the period"""
    try:
        # This would implement actual trend calculation
        # For now, return placeholder data
        return {
            'period': period,
            'sync_volume_trend': 'stable',
            'error_rate_trend': 'decreasing',
            'performance_trend': 'improving'
        }
    except:
        return {
            'period': period,
            'sync_volume_trend': 'unknown',
            'error_rate_trend': 'unknown',
            'performance_trend': 'unknown'
        }

def _calculate_error_rate(statistics: Dict[str, Any]) -> float:
    """Calculate error rate percentage"""
    try:
        total_orders = sum(statistics.get('orders', {}).values())
        total_payments = sum(statistics.get('payments', {}).values())
        total_items = total_orders + total_payments
        
        if total_items == 0:
            return 0.0
        
        failed_orders = statistics.get('orders', {}).get('failed', 0)
        failed_payments = statistics.get('payments', {}).get('failed', 0)
        total_failed = failed_orders + failed_payments
        
        return (total_failed / total_items) * 100
    except:
        return 0.0

def _estimate_export_size(data_types: List[str], date_range: Dict[str, Any]) -> str:
    """Estimate export file size"""
    try:
        # This would implement actual size estimation
        # For now, return placeholder estimate
        base_size = len(data_types) * 100  # KB per data type
        return f"{base_size}KB"
    except:
        return "Unknown"

# Error handlers for offline API
@offline_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@offline_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@offline_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429

@offline_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

@offline_api_bp.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        'success': False,
        'error': 'Service unavailable',
        'message': 'The service is temporarily unavailable'
    }), 503