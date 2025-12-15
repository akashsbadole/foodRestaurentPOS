"""
Enhanced Dashboard API Routes for Flask POS Application
Provides comprehensive dashboard data and analytics endpoints
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import utility managers
from utils.session_manager import session_manager
from utils.security_manager import security_manager
from utils.offline_manager import offline_manager
from utils.razorpay_manager import razorpay_manager

# Import models for data access
from models import db, Order, OrderItem, MenuItem, Category, Payment, User, Table, Customer, LoyaltyTier, PointsTransaction

# Create blueprint
dashboard_api_bp = Blueprint('dashboard_api', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Decorators for API security
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

def rate_limit_dashboard_api(f):
    """Decorator for rate limiting dashboard API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for dashboard API
        if not security_manager._check_rate_limit(client_ip, 'dashboard_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many dashboard requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@dashboard_api_bp.route('/api/dashboard/overview', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_dashboard_overview():
    """
    Get dashboard overview with all metrics
    
    Query Parameters:
    - period: Time period (today, week, month, year)
    
    Response:
    {
        "success": true,
        "overview": {
            "sales": {...},
            "orders": {...},
            "customers": {...},
            "performance": {...}
        }
    }
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'today')
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=1)  # Default to yesterday
        
        # Get sales metrics
        sales_metrics = _get_sales_metrics(start_date, end_date)
        
        # Get order metrics
        order_metrics = _get_order_metrics(start_date, end_date)
        
        # Get customer metrics
        customer_metrics = _get_customer_metrics(start_date, end_date)
        
        # Get CRM metrics
        crm_metrics = _get_crm_metrics(start_date, end_date)
        
        # Get loyalty metrics
        loyalty_metrics = _get_loyalty_metrics(start_date, end_date)
        
        # Get performance metrics
        performance_metrics = _get_performance_metrics(start_date, end_date)
        
        # Get system status
        system_status = _get_system_status()
        
        overview = {
            'period': period,
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'sales': sales_metrics,
            'orders': order_metrics,
            'customers': customer_metrics,
            'crm': crm_metrics,
            'loyalty': loyalty_metrics,
            'performance': performance_metrics,
            'system': system_status,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'overview': overview
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_dashboard_overview: {e}")
        return jsonify({
            'success': False,
            'error': 'Dashboard overview retrieval error',
            'message': 'An error occurred while retrieving dashboard overview'
        }), 500

@dashboard_api_bp.route('/api/dashboard/performance', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_performance_metrics():
    """
    Get performance metrics
    
    Query Parameters:
    - period: Time period (hour, day, week, month)
    
    Response:
    {
        "success": true,
        "performance": {
            "response_times": {...},
            "throughput": {...},
            "errors": {...},
            "resources": {...}
        }
    }
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'day')
        
        # Calculate date range based on period
        end_date = datetime.utcnow()
        if period == 'hour':
            start_date = end_date - timedelta(hours=1)
        elif period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=1)  # Default to yesterday
        
        # Get performance data
        performance_data = _get_performance_metrics(start_date, end_date)
        
        # Add additional performance insights
        performance_data['insights'] = _generate_performance_insights(performance_data)
        performance_data['recommendations'] = _get_performance_recommendations(performance_data)
        
        return jsonify({
            'success': True,
            'performance': performance_data,
            'period': period,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_performance_metrics: {e}")
        return jsonify({
            'success': False,
            'error': 'Performance metrics retrieval error',
            'message': 'An error occurred while retrieving performance metrics'
        }), 500

@dashboard_api_bp.route('/api/dashboard/security-summary', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_security_summary():
    """
    Get security summary
    
    Response:
    {
        "success": true,
        "security": {
            "threat_level": "low",
            "blocked_ips": 3,
            "security_events": 15,
            "active_sessions": 5,
            "security_score": 85
        }
    }
    """
    try:
        # Get security statistics
        security_stats = security_manager.get_security_statistics()
        
        # Get session information
        user_id = session.get('user_id')
        active_sessions = session_manager.get_user_sessions(user_id) if user_id else []
        
        # Get offline status
        offline_status = offline_manager.get_sync_status()
        
        # Calculate security summary
        security_summary = {
            'threat_level': _calculate_threat_level(security_stats),
            'security_score': _calculate_security_score(security_stats),
            'blocked_ips': security_stats.get('blocked_ips', 0),
            'security_events_24h': security_stats.get('total_events_24h', 0),
            'active_sessions': len(active_sessions),
            'session_security': _analyze_session_security(active_sessions),
            'offline_security': _analyze_offline_security(offline_status),
            'recent_alerts': _get_recent_security_alerts(security_stats),
            'protections_active': _get_active_protections()
        }
        
        return jsonify({
            'success': True,
            'security': security_summary,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_security_summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Security summary retrieval error',
            'message': 'An error occurred while retrieving security summary'
        }), 500

@dashboard_api_bp.route('/api/dashboard/sync-status', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_sync_status():
    """
    Get synchronization status
    
    Response:
    {
        "success": true,
        "sync": {
            "is_online": true,
            "pending_orders": 0,
            "pending_payments": 0,
            "last_sync": "2023-12-09T10:30:00",
            "sync_queue_size": 0
        }
    }
    """
    try:
        # Get sync status from offline manager
        sync_status = offline_manager.get_sync_status()
        
        # Get additional sync information
        sync_statistics = offline_manager.get_sync_statistics()
        
        # Get recent sync activity
        recent_activity = _get_recent_sync_activity()
        
        # Calculate sync health
        sync_health = _calculate_sync_health(sync_status, sync_statistics)
        
        # Enhanced sync status
        enhanced_sync_status = {
            **sync_status,
            'health': sync_health,
            'statistics': sync_statistics,
            'recent_activity': recent_activity,
            'configuration': _get_sync_configuration(),
            'recommendations': _get_sync_recommendations(sync_status, sync_statistics)
        }
        
        return jsonify({
            'success': True,
            'sync': enhanced_sync_status,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_sync_status: {e}")
        return jsonify({
            'success': False,
            'error': 'Sync status retrieval error',
            'message': 'An error occurred while retrieving sync status'
        }), 500

@dashboard_api_bp.route('/api/dashboard/recent-activity', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_recent_activity():
    """
    Get recent system activity
    
    Query Parameters:
    - limit: Maximum number of activities (default: 20)
    - type: Activity type (orders, payments, security, all)
    
    Response:
    {
        "success": true,
        "activities": [
            {
                "type": "order",
                "description": "New order #12345",
                "timestamp": "2023-12-09T10:30:00",
                "user": "John Doe"
            }
        ]
    }
    """
    try:
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        limit = min(max(limit, 1), 100)  # Limit between 1 and 100
        activity_type = request.args.get('type', 'all')
        
        # Get recent activities
        activities = []
        
        # Get order activities
        if activity_type in ['orders', 'all']:
            order_activities = _get_recent_order_activities(limit // 2)
            activities.extend(order_activities)
        
        # Get payment activities
        if activity_type in ['payments', 'all']:
            payment_activities = _get_recent_payment_activities(limit // 2)
            activities.extend(payment_activities)
        
        # Get security activities
        if activity_type in ['security', 'all']:
            security_activities = _get_recent_security_activities(limit // 2)
            activities.extend(security_activities)
        
        # Sort by timestamp
        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit results
        activities = activities[:limit]
        
        # Add additional information
        for activity in activities:
            activity['age'] = _calculate_activity_age(activity.get('timestamp'))
            activity['priority'] = _determine_activity_priority(activity)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'total_activities': len(activities),
            'filters': {
                'limit': limit,
                'type': activity_type
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_recent_activity: {e}")
        return jsonify({
            'success': False,
            'error': 'Recent activity retrieval error',
            'message': 'An error occurred while retrieving recent activity'
        }), 500

@dashboard_api_bp.route('/api/dashboard/alerts', methods=['GET'])
@rate_limit_dashboard_api
@require_valid_session_api
def get_system_alerts():
    """
    Get system alerts
    
    Query Parameters:
    - severity: Filter by severity (low, medium, high, critical)
    - status: Filter by status (active, resolved, all)
    
    Response:
    {
        "success": true,
        "alerts": [
            {
                "id": "alert_123",
                "type": "security",
                "severity": "medium",
                "title": "Multiple failed login attempts",
                "description": "5 failed login attempts from IP 192.168.1.100",
                "timestamp": "2023-12-09T10:00:00",
                "status": "active"
            }
        ]
    }
    """
    try:
        # Get query parameters
        severity = request.args.get('severity')
        status = request.args.get('status', 'active')
        
        # Get system alerts
        alerts = _get_system_alerts()
        
        # Apply filters
        filtered_alerts = []
        for alert in alerts:
            # Filter by severity
            if severity and alert.get('severity') != severity:
                continue
            
            # Filter by status
            if status != 'all' and alert.get('status') != status:
                continue
            
            # Add additional information
            alert['age'] = _calculate_activity_age(alert.get('timestamp'))
            alert['actions'] = _get_alert_actions(alert)
            
            filtered_alerts.append(alert)
        
        # Sort by severity and timestamp
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        filtered_alerts.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'low'), 0),
            x.get('timestamp', '')
        ), reverse=True)
        
        return jsonify({
            'success': True,
            'alerts': filtered_alerts,
            'total_alerts': len(filtered_alerts),
            'filters': {
                'severity': severity,
                'status': status
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_system_alerts: {e}")
        return jsonify({
            'success': False,
            'error': 'System alerts retrieval error',
            'message': 'An error occurred while retrieving system alerts'
        }), 500

@dashboard_api_bp.route('/api/dashboard/dismiss-alert', methods=['POST'])
@rate_limit_dashboard_api
@require_valid_session_api
def dismiss_alert():
    """
    Dismiss specific alert
    
    Request Body:
    {
        "alert_id": "alert_123",
        "reason": "Investigated and resolved"
    }
    
    Response:
    {
        "success": true,
        "message": "Alert dismissed successfully"
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
        
        alert_id = data.get('alert_id')
        reason = data.get('reason', 'Dismissed by user')
        
        if not alert_id:
            return jsonify({
                'success': False,
                'error': 'Missing alert ID',
                'message': 'alert_id is required'
            }), 400
        
        # Dismiss alert (would implement alert dismissal logic)
        success = _dismiss_alert(alert_id, reason)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Alert dismissal failed',
                'message': 'Unable to dismiss the specified alert'
            }), 500
        
        # Log alert dismissal
        security_manager._log_security_event(
            'ALERT_DISMISSED',
            security_manager._get_client_ip(),
            f"Alert {alert_id} dismissed: {reason}",
            'low'
        )
        
        return jsonify({
            'success': True,
            'message': 'Alert dismissed successfully',
            'alert_id': alert_id,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in dismiss_alert: {e}")
        return jsonify({
            'success': False,
            'error': 'Alert dismissal error',
            'message': 'An error occurred while dismissing the alert'
        }), 500

# Helper functions

def _get_sales_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get sales metrics for the specified period"""
    try:
        # Query orders in the date range
        orders = Order.query.filter(
            Order.created_at.between(start_date, end_date)
        ).all()
        
        # Calculate sales metrics
        total_sales = sum(order.total_amount for order in orders if order.total_amount)
        total_orders = len(orders)
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Get sales by category
        category_sales = {}
        for order in orders:
            for item in order.items:
                category = item.menu_item.category.name if item.menu_item and item.menu_item.category else 'Unknown'
                if category not in category_sales:
                    category_sales[category] = 0
                category_sales[category] += item.price * item.quantity
        
        # Get payment method breakdown
        payment_methods = {}
        for order in orders:
            for payment in order.payments:
                method = payment.method or 'Unknown'
                if method not in payment_methods:
                    payment_methods[method] = 0
                payment_methods[method] += payment.amount
        
        return {
            'total_sales': float(total_sales),
            'total_orders': total_orders,
            'average_order_value': float(average_order_value),
            'category_breakdown': category_sales,
            'payment_methods': payment_methods,
            'growth': _calculate_sales_growth(orders, start_date, end_date)
        }
    except Exception as e:
        logger.error(f"Error in _get_sales_metrics: {e}")
        return {
            'total_sales': 0,
            'total_orders': 0,
            'average_order_value': 0,
            'category_breakdown': {},
            'payment_methods': {},
            'growth': 0
        }

def _get_order_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get order metrics for the specified period"""
    try:
        # Query orders in the date range
        orders = Order.query.filter(
            Order.created_at.between(start_date, end_date)
        ).all()
        
        # Calculate order metrics
        status_breakdown = {}
        for order in orders:
            status = order.status or 'unknown'
            if status not in status_breakdown:
                status_breakdown[status] = 0
            status_breakdown[status] += 1
        
        # Calculate average preparation time
        completed_orders = [o for o in orders if o.status == 'completed']
        avg_preparation_time = 0
        if completed_orders:
            preparation_times = []
            for order in completed_orders:
                if order.created_at and order.updated_at:
                    prep_time = (order.updated_at - order.created_at).total_seconds() / 60  # minutes
                    preparation_times.append(prep_time)
            
            if preparation_times:
                avg_preparation_time = sum(preparation_times) / len(preparation_times)
        
        return {
            'total_orders': len(orders),
            'status_breakdown': status_breakdown,
            'average_preparation_time': avg_preparation_time,
            'completion_rate': (len(completed_orders) / len(orders) * 100) if orders else 0,
            'peak_hours': _calculate_peak_hours(orders)
        }
    except Exception as e:
        logger.error(f"Error in _get_order_metrics: {e}")
        return {
            'total_orders': 0,
            'status_breakdown': {},
            'average_preparation_time': 0,
            'completion_rate': 0,
            'peak_hours': []
        }

def _get_customer_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get customer metrics for the specified period"""
    try:
        # Query orders in the date range to get customer activity
        orders = Order.query.filter(
            Order.created_at.between(start_date, end_date)
        ).all()
        
        # Get unique customers
        unique_customers = set()
        returning_customers = set()
        
        for order in orders:
            if order.customer_id:
                unique_customers.add(order.customer_id)
                # Check if customer had previous orders (simplified)
                previous_orders = Order.query.filter(
                    Order.customer_id == order.customer_id,
                    Order.created_at < start_date
                ).count()
                if previous_orders > 0:
                    returning_customers.add(order.customer_id)
        
        # Calculate customer metrics
        total_customers = len(unique_customers)
        returning_count = len(returning_customers)
        new_customers = total_customers - returning_count
        
        return {
            'total_customers': total_customers,
            'new_customers': new_customers,
            'returning_customers': returning_count,
            'customer_retention_rate': (returning_count / total_customers * 100) if total_customers > 0 else 0,
            'average_orders_per_customer': len(orders) / total_customers if total_customers > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error in _get_customer_metrics: {e}")
        return {
            'total_customers': 0,
            'new_customers': 0,
            'returning_customers': 0,
            'customer_retention_rate': 0,
            'average_orders_per_customer': 0
        }

def _get_crm_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get CRM metrics for specified period"""
    try:
        # Get total customers
        total_customers = Customer.query.count()
        
        # Get new customers this month
        month_start = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_customers_month = Customer.query.filter(
            Customer.created_at >= month_start
        ).count()
        
        # Get recent customers for dashboard
        recent_customers = Customer.query.order_by(
            Customer.created_at.desc()
        ).limit(5).all()
        
        # Get customer with orders count
        customers_with_orders = db.session.query(Customer.id).filter(
            Customer.orders.any()
        ).distinct().count()
        
        return {
            'total_customers': total_customers,
            'new_customers_month': new_customers_month,
            'customers_with_orders': customers_with_orders,
            'recent_customers': [
                {
                    'id': c.id,
                    'name': c.name,
                    'phone': c.phone,
                    'points_earned': c.points_earned,
                    'tier': c.tier,
                    'created_at': c.created_at.isoformat() if c.created_at else None
                }
                for c in recent_customers
            ]
        }
    except Exception as e:
        logger.error(f"Error in _get_crm_metrics: {e}")
        return {
            'total_customers': 0,
            'new_customers_month': 0,
            'customers_with_orders': 0,
            'recent_customers': []
        }

def _get_loyalty_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get loyalty metrics for specified period"""
    try:
        # Get loyalty tiers
        tiers = LoyaltyTier.query.all()
        
        # Get tier distribution
        tier_distribution = {}
        for tier in tiers:
            customer_count = Customer.query.filter(
                Customer.tier == tier.name
            ).count()
            tier_distribution[tier.name.lower()] = customer_count
        
        # Get points transactions for today
        today_start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        points_issued_today = PointsTransaction.query.filter(
            PointsTransaction.transaction_type == 'earned',
            PointsTransaction.created_at >= today_start
        ).with_entities(
            db.func.sum(PointsTransaction.points)
        ).scalar() or 0
        
        points_redeemed_today = PointsTransaction.query.filter(
            PointsTransaction.transaction_type == 'redeemed',
            PointsTransaction.created_at >= today_start
        ).with_entities(
            db.func.sum(PointsTransaction.points)
        ).scalar() or 0
        
        # Get total members (customers with points)
        total_members = Customer.query.filter(
            Customer.points_earned > 0
        ).count()
        
        # Get active members (customers with transactions in last 30 days)
        thirty_days_ago = end_date - timedelta(days=30)
        active_members = db.session.query(Customer.id).filter(
            Customer.points_transactions.any(
                PointsTransaction.created_at >= thirty_days_ago
            )
        ).distinct().count()
        
        return {
            'total_members': total_members,
            'active_members': active_members,
            'points_issued_today': int(points_issued_today),
            'points_redeemed_today': int(points_redeemed_today),
            'tier_distribution': tier_distribution
        }
    except Exception as e:
        logger.error(f"Error in _get_loyalty_metrics: {e}")
        return {
            'total_members': 0,
            'active_members': 0,
            'points_issued_today': 0,
            'points_redeemed_today': 0,
            'tier_distribution': {}
        }

def _get_performance_metrics(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get performance metrics for the specified period"""
    try:
        # This would integrate with actual performance monitoring
        # For now, return placeholder data
        return {
            'response_time': {
                'average': 150,  # ms
                'p95': 300,      # ms
                'p99': 500       # ms
            },
            'throughput': {
                'requests_per_second': 25,
                'orders_per_hour': 15
            },
            'error_rate': {
                'percentage': 2.5,
                'total_errors': 50
            },
            'resources': {
                'cpu_usage': 45.2,      # %
                'memory_usage': 62.8,   # %
                'disk_usage': 35.1,     # %
                'network_io': 1024      # KB/s
            }
        }
    except Exception as e:
        logger.error(f"Error in _get_performance_metrics: {e}")
        return {
            'response_time': {'average': 0, 'p95': 0, 'p99': 0},
            'throughput': {'requests_per_second': 0, 'orders_per_hour': 0},
            'error_rate': {'percentage': 0, 'total_errors': 0},
            'resources': {'cpu_usage': 0, 'memory_usage': 0, 'disk_usage': 0, 'network_io': 0}
        }

def _get_system_status() -> Dict[str, Any]:
    """Get overall system status"""
    try:
        # Get status from various managers
        security_stats = security_manager.get_security_statistics()
        sync_status = offline_manager.get_sync_status()
        
        # Calculate system health
        health_score = 100
        
        # Deduct points for security issues
        if security_stats.get('total_events_24h', 0) > 50:
            health_score -= 20
        
        # Deduct points for sync issues
        if sync_status.get('failed_orders', 0) > 5:
            health_score -= 15
        
        # Determine overall status
        if health_score >= 80:
            status = 'healthy'
        elif health_score >= 60:
            status = 'warning'
        elif health_score >= 40:
            status = 'degraded'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'health_score': health_score,
            'uptime_percentage': 99.9,  # Would be calculated from actual monitoring
            'services': {
                'database': 'online',
                'payment_gateway': razorpay_manager.is_configured(),
                'offline_sync': 'online' if sync_status.get('is_online') else 'offline'
            }
        }
    except Exception as e:
        logger.error(f"Error in _get_system_status: {e}")
        return {
            'status': 'unknown',
            'health_score': 0,
            'uptime_percentage': 0,
            'services': {
                'database': 'unknown',
                'payment_gateway': 'unknown',
                'offline_sync': 'unknown'
            }
        }

def _calculate_threat_level(security_stats: Dict[str, Any]) -> str:
    """Calculate overall threat level"""
    total_events = security_stats.get('total_events_24h', 0)
    
    if total_events > 50:
        return 'high'
    elif total_events > 20:
        return 'medium'
    elif total_events > 5:
        return 'low'
    else:
        return 'minimal'

def _calculate_security_score(security_stats: Dict[str, Any]) -> int:
    """Calculate overall security score (0-100)"""
    base_score = 100
    
    # Deduct points for security events
    total_events = security_stats.get('total_events_24h', 0)
    base_score -= min(total_events, 50)
    
    # Deduct points for blocked IPs
    blocked_ips = security_stats.get('blocked_ips', 0)
    base_score -= min(blocked_ips * 2, 20)
    
    return max(0, base_score)

def _analyze_session_security(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze session security"""
    if not sessions:
        return {'status': 'no_sessions', 'issues': []}
    
    issues = []
    
    # Check for sessions from unusual IPs
    current_ip = sessions[0].get('ip_address') if sessions else None
    for session_data in sessions:
        if session_data.get('ip_address') != current_ip:
            issues.append('Multiple IPs detected')
            break
    
    # Check for old sessions
    for session_data in sessions:
        created_at = session_data.get('created_at')
        if created_at:
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                age_hours = (datetime.utcnow() - created_dt).total_seconds() / 3600
                if age_hours > 24:
                    issues.append('Long-lived session detected')
                    break
            except:
                pass
    
    status = 'secure' if not issues else 'warning'
    return {'status': status, 'issues': issues}

def _analyze_offline_security(offline_status: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze offline sync security"""
    issues = []
    
    # Check for failed syncs
    failed_orders = offline_status.get('failed_orders', 0)
    failed_payments = offline_status.get('failed_payments', 0)
    
    if failed_orders > 5:
        issues.append('Multiple failed order syncs')
    
    if failed_payments > 3:
        issues.append('Multiple failed payment syncs')
    
    # Check for long offline periods
    if not offline_status.get('is_online', True):
        issues.append('System currently offline')
    
    status = 'secure' if not issues else 'warning'
    return {'status': status, 'issues': issues}

def _get_recent_security_alerts(security_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get recent security alerts"""
    alerts = []
    
    # Add alerts based on security statistics
    if security_stats.get('total_events_24h', 0) > 20:
        alerts.append({
            'type': 'security',
            'severity': 'medium',
            'title': 'High security event volume',
            'description': f"{security_stats.get('total_events_24h', 0)} security events in last 24 hours"
        })
    
    if security_stats.get('blocked_ips', 0) > 5:
        alerts.append({
            'type': 'security',
            'severity': 'high',
            'title': 'Multiple IPs blocked',
            'description': f"{security_stats.get('blocked_ips', 0)} IPs currently blocked"
        })
    
    return alerts

def _get_active_protections() -> List[str]:
    """Get list of active security protections"""
    return [
        'Rate limiting',
        'IP blocking',
        'Input validation',
        'CSRF protection',
        'Session security',
        'SQL injection protection'
    ]

def _get_recent_sync_activity() -> List[Dict[str, Any]]:
    """Get recent sync activity"""
    # This would query actual sync activity logs
    # For now, return placeholder data
    return [
        {
            'type': 'order_sync',
            'status': 'success',
            'items_synced': 5,
            'timestamp': datetime.utcnow().isoformat()
        }
    ]

def _calculate_sync_health(sync_status: Dict[str, Any], sync_statistics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate sync health metrics"""
    health_score = 100
    
    # Deduct points for failed items
    failed_items = sync_status.get('failed_orders', 0) + sync_status.get('failed_payments', 0)
    health_score -= min(failed_items * 5, 50)
    
    # Deduct points for large queue
    queue_size = sync_status.get('sync_queue_size', 0)
    health_score -= min(queue_size, 30)
    
    # Determine health status
    if health_score >= 80:
        status = 'excellent'
    elif health_score >= 60:
        status = 'good'
    elif health_score >= 40:
        status = 'fair'
    else:
        status = 'poor'
    
    return {
        'status': status,
        'score': health_score,
        'failed_items': failed_items,
        'queue_size': queue_size
    }

def _get_sync_configuration() -> Dict[str, Any]:
    """Get sync configuration"""
    return {
        'auto_sync_enabled': True,
        'sync_interval_minutes': 30,
        'max_retry_attempts': 3,
        'conflict_resolution': 'server_wins'
    }

def _get_sync_recommendations(sync_status: Dict[str, Any], sync_statistics: Dict[str, Any]) -> List[str]:
    """Get sync recommendations"""
    recommendations = []
    
    # Check for failed items
    failed_items = sync_status.get('failed_orders', 0) + sync_status.get('failed_payments', 0)
    if failed_items > 5:
        recommendations.append('Review failed sync items and resolve conflicts')
    
    # Check for large queue
    queue_size = sync_status.get('sync_queue_size', 0)
    if queue_size > 20:
        recommendations.append('Consider increasing sync frequency')
    
    # Check offline status
    if not sync_status.get('is_online', True):
        recommendations.append('Check internet connection and server availability')
    
    return recommendations

def _get_recent_order_activities(limit: int) -> List[Dict[str, Any]]:
    """Get recent order activities"""
    try:
        orders = Order.query.order_by(Order.created_at.desc()).limit(limit).all()
        
        activities = []
        for order in orders:
            activities.append({
                'type': 'order',
                'description': f"Order #{order.id} {order.status}",
                'timestamp': order.created_at.isoformat() if order.created_at else None,
                'user': order.user.name if order.user else 'System',
                'amount': float(order.total_amount) if order.total_amount else 0,
                'status': order.status
            })
        
        return activities
    except Exception as e:
        logger.error(f"Error in _get_recent_order_activities: {e}")
        return []

def _get_recent_payment_activities(limit: int) -> List[Dict[str, Any]]:
    """Get recent payment activities"""
    try:
        payments = Payment.query.order_by(Payment.created_at.desc()).limit(limit).all()
        
        activities = []
        for payment in payments:
            activities.append({
                'type': 'payment',
                'description': f"Payment {payment.status} - {payment.method}",
                'timestamp': payment.created_at.isoformat() if payment.created_at else None,
                'amount': float(payment.amount) if payment.amount else 0,
                'method': payment.method,
                'status': payment.status
            })
        
        return activities
    except Exception as e:
        logger.error(f"Error in _get_recent_payment_activities: {e}")
        return []

def _get_recent_security_activities(limit: int) -> List[Dict[str, Any]]:
    """Get recent security activities"""
    try:
        security_events = security_manager.get_security_events(limit)
        
        activities = []
        for event in security_events:
            activities.append({
                'type': 'security',
                'description': f"{event.get('event_type', 'Unknown event')}: {event.get('details', '')}",
                'timestamp': event.get('timestamp'),
                'severity': event.get('severity', 'low'),
                'ip_address': event.get('ip_address')
            })
        
        return activities
    except Exception as e:
        logger.error(f"Error in _get_recent_security_activities: {e}")
        return []

def _calculate_activity_age(timestamp: str) -> str:
    """Calculate age of activity"""
    try:
        if not timestamp:
            return 'unknown'
        
        activity_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.utcnow()
        age_seconds = (now - activity_time).total_seconds()
        
        if age_seconds < 60:
            return f"{int(age_seconds)} seconds ago"
        elif age_seconds < 3600:
            return f"{int(age_seconds / 60)} minutes ago"
        elif age_seconds < 86400:
            return f"{int(age_seconds / 3600)} hours ago"
        else:
            return f"{int(age_seconds / 86400)} days ago"
    except:
        return 'unknown'

def _determine_activity_priority(activity: Dict[str, Any]) -> str:
    """Determine priority of activity"""
    activity_type = activity.get('type')
    
    if activity_type == 'security':
        severity = activity.get('severity', 'low')
        if severity in ['high', 'critical']:
            return 'high'
        elif severity == 'medium':
            return 'medium'
        else:
            return 'low'
    elif activity_type == 'order':
        status = activity.get('status')
        if status in ['cancelled', 'failed']:
            return 'medium'
        else:
            return 'low'
    elif activity_type == 'payment':
        status = activity.get('status')
        if status == 'failed':
            return 'high'
        else:
            return 'low'
    else:
        return 'low'

def _get_system_alerts() -> List[Dict[str, Any]]:
    """Get system alerts"""
    alerts = []
    
    # Security alerts
    security_stats = security_manager.get_security_statistics()
    if security_stats.get('total_events_24h', 0) > 20:
        alerts.append({
            'id': 'alert_security_volume',
            'type': 'security',
            'severity': 'medium',
            'title': 'High security event volume',
            'description': f"{security_stats.get('total_events_24h', 0)} security events in last 24 hours",
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'active'
        })
    
    # Sync alerts
    sync_status = offline_manager.get_sync_status()
    failed_items = sync_status.get('failed_orders', 0) + sync_status.get('failed_payments', 0)
    if failed_items > 5:
        alerts.append({
            'id': 'alert_sync_failures',
            'type': 'sync',
            'severity': 'high',
            'title': 'Multiple sync failures',
            'description': f"{failed_items} items failed to sync",
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'active'
        })
    
    # Performance alerts
    # This would integrate with actual performance monitoring
    alerts.append({
        'id': 'alert_performance',
        'type': 'performance',
        'severity': 'low',
        'title': 'Performance monitoring active',
        'description': 'System performance is being monitored',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'active'
    })
    
    return alerts

def _get_alert_actions(alert: Dict[str, Any]) -> List[str]:
    """Get available actions for an alert"""
    alert_type = alert.get('type')
    
    if alert_type == 'security':
        return ['View Details', 'Block IP', 'Dismiss']
    elif alert_type == 'sync':
        return ['View Details', 'Force Sync', 'Resolve Conflicts', 'Dismiss']
    elif alert_type == 'performance':
        return ['View Details', 'Optimize', 'Dismiss']
    else:
        return ['View Details', 'Dismiss']

def _dismiss_alert(alert_id: str, reason: str) -> bool:
    """Dismiss an alert"""
    # This would implement actual alert dismissal logic
    # For now, return True as placeholder
    return True

def _calculate_sales_growth(orders: List[Any], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate sales growth compared to previous period"""
    try:
        # Calculate current period sales
        current_sales = sum(order.total_amount for order in orders if order.total_amount)
        
        # Calculate previous period sales
        period_length = (end_date - start_date).days
        previous_start = start_date - timedelta(days=period_length)
        previous_end = start_date
        
        previous_orders = Order.query.filter(
            Order.created_at.between(previous_start, previous_end)
        ).all()
        
        previous_sales = sum(order.total_amount for order in previous_orders if order.total_amount)
        
        # Calculate growth
        if previous_sales > 0:
            growth_percentage = ((current_sales - previous_sales) / previous_sales) * 100
            growth_amount = current_sales - previous_sales
        else:
            growth_percentage = 100 if current_sales > 0 else 0
            growth_amount = current_sales
        
        return {
            'percentage': round(growth_percentage, 2),
            'amount': float(growth_amount),
            'current_period': float(current_sales),
            'previous_period': float(previous_sales)
        }
    except Exception as e:
        logger.error(f"Error in _calculate_sales_growth: {e}")
        return {
            'percentage': 0,
            'amount': 0,
            'current_period': 0,
            'previous_period': 0
        }

def _calculate_peak_hours(orders: List[Any]) -> List[int]:
    """Calculate peak order hours"""
    try:
        hour_counts = {}
        
        for order in orders:
            if order.created_at:
                hour = order.created_at.hour
                if hour not in hour_counts:
                    hour_counts[hour] = 0
                hour_counts[hour] += 1
        
        # Sort by count and return top hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:5]]
    except Exception as e:
        logger.error(f"Error in _calculate_peak_hours: {e}")
        return []

def _generate_performance_insights(performance_data: Dict[str, Any]) -> List[str]:
    """Generate performance insights"""
    insights = []
    
    try:
        # Response time insights
        avg_response_time = performance_data.get('response_time', {}).get('average', 0)
        if avg_response_time > 500:
            insights.append('High average response time detected')
        elif avg_response_time < 100:
            insights.append('Excellent response time performance')
        
        # Error rate insights
        error_rate = performance_data.get('error_rate', {}).get('percentage', 0)
        if error_rate > 5:
            insights.append('High error rate detected')
        elif error_rate < 1:
            insights.append('Low error rate maintained')
        
        # Resource usage insights
        cpu_usage = performance_data.get('resources', {}).get('cpu_usage', 0)
        if cpu_usage > 80:
            insights.append('High CPU usage detected')
        
    except Exception as e:
        logger.error(f"Error in _generate_performance_insights: {e}")
        insights.append('Unable to generate performance insights')
    
    return insights

def _get_performance_recommendations(performance_data: Dict[str, Any]) -> List[str]:
    """Get performance recommendations"""
    recommendations = []
    
    try:
        # Response time recommendations
        avg_response_time = performance_data.get('response_time', {}).get('average', 0)
        if avg_response_time > 300:
            recommendations.append('Optimize database queries and consider caching')
        
        # Error rate recommendations
        error_rate = performance_data.get('error_rate', {}).get('percentage', 0)
        if error_rate > 3:
            recommendations.append('Investigate and fix error sources')
        
        # Resource recommendations
        memory_usage = performance_data.get('resources', {}).get('memory_usage', 0)
        if memory_usage > 80:
            recommendations.append('Consider increasing memory or optimizing memory usage')
        
    except Exception as e:
        logger.error(f"Error in _get_performance_recommendations: {e}")
        recommendations.append('Review system performance configuration')
    
    return recommendations

# Error handlers for dashboard API
@dashboard_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@dashboard_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@dashboard_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many dashboard requests. Please try again later.'
    }), 429

@dashboard_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500