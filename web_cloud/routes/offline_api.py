"""
Offline API Routes for Flask POS Application
Handles offline operations, synchronization, and data management
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from utils.offline_manager import offline_manager, store_offline_order, store_offline_payment
from utils.session_manager import session_manager
import logging
from datetime import datetime

# Create blueprint
offline_api_bp = Blueprint('offline_api', __name__, url_prefix='/api/offline')

logger = logging.getLogger(__name__)

@offline_api_bp.route('/status')
def get_offline_status():
    """Get current offline status and sync information"""
    try:
        status = offline_manager.get_sync_status()
        
        # Add additional context
        status.update({
            'user_authenticated': current_user.is_authenticated if current_user else False,
            'session_valid': session_manager._is_session_valid() if current_user else False,
            'timestamp': datetime.utcnow().isoformat(),
            'cache_info': {
                'menu_items_count': len(offline_manager.get_cached_menu_items()),
                'categories_count': len(offline_manager.get_cached_categories()),
                'tables_count': len(offline_manager.get_cached_tables())
            }
        })
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"Error getting offline status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/sync', methods=['POST'])
@login_required
def force_sync():
    """Force immediate synchronization"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid',
                'redirect': '/auth/login'
            }), 401
        
        # Force sync
        sync_success = offline_manager.force_sync()
        
        if sync_success:
            return jsonify({
                'success': True,
                'message': 'Synchronization completed successfully',
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Synchronization failed - offline mode',
                'offline_mode': True
            })
            
    except Exception as e:
        logger.error(f"Error forcing sync: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/orders/store', methods=['POST'])
@login_required
def store_order_offline():
    """Store order for offline synchronization"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        order_data = request.get_json()
        if not order_data:
            return jsonify({
                'success': False,
                'message': 'No order data provided'
            }), 400
        
        # Add metadata
        order_data.update({
            'user_id': current_user.id,
            'username': current_user.username,
            'created_at': datetime.utcnow().isoformat(),
            'stored_offline': True
        })
        
        # Store order offline
        local_id = store_offline_order(order_data)
        
        return jsonify({
            'success': True,
            'message': 'Order stored for offline synchronization',
            'local_id': local_id,
            'offline_mode': True
        })
        
    except Exception as e:
        logger.error(f"Error storing order offline: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/payments/store', methods=['POST'])
@login_required
def store_payment_offline():
    """Store payment for offline synchronization"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        payment_data = request.get_json()
        if not payment_data:
            return jsonify({
                'success': False,
                'message': 'No payment data provided'
            }), 400
        
        order_local_id = payment_data.get('order_local_id')
        if not order_local_id:
            return jsonify({
                'success': False,
                'message': 'Order local ID is required'
            }), 400
        
        # Add metadata
        payment_data.update({
            'user_id': current_user.id,
            'username': current_user.username,
            'created_at': datetime.utcnow().isoformat(),
            'stored_offline': True
        })
        
        # Store payment offline
        local_id = store_offline_payment(payment_data, order_local_id)
        
        return jsonify({
            'success': True,
            'message': 'Payment stored for offline synchronization',
            'local_id': local_id,
            'offline_mode': True
        })
        
    except Exception as e:
        logger.error(f"Error storing payment offline: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/data/cache')
@login_required
def get_cached_data():
    """Get all cached data for offline use"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Get cached data
        menu_items = offline_manager.get_cached_menu_items()
        categories = offline_manager.get_cached_categories()
        tables = offline_manager.get_cached_tables()
        
        return jsonify({
            'success': True,
            'data': {
                'menu_items': menu_items,
                'categories': categories,
                'tables': tables,
                'cached_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cached data: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/data/menu_items')
@login_required
def get_cached_menu_items():
    """Get cached menu items"""
    try:
        menu_items = offline_manager.get_cached_menu_items()
        
        return jsonify({
            'success': True,
            'data': menu_items,
            'count': len(menu_items),
            'cached_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting cached menu items: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/data/categories')
@login_required
def get_cached_categories():
    """Get cached categories"""
    try:
        categories = offline_manager.get_cached_categories()
        
        return jsonify({
            'success': True,
            'data': categories,
            'count': len(categories),
            'cached_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting cached categories: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/data/tables')
@login_required
def get_cached_tables():
    """Get cached tables"""
    try:
        tables = offline_manager.get_cached_tables()
        
        return jsonify({
            'success': True,
            'data': tables,
            'count': len(tables),
            'cached_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting cached tables: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/orders')
@login_required
def get_offline_orders():
    """Get all offline orders"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        orders = offline_manager.get_offline_orders()
        
        # Filter by current user if not admin
        if current_user.role != 'admin':
            orders = [order for order in orders if order.get('user_id') == current_user.id]
        
        return jsonify({
            'success': True,
            'data': orders,
            'count': len(orders)
        })
        
    except Exception as e:
        logger.error(f"Error getting offline orders: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/clear_failed', methods=['POST'])
@login_required
def clear_failed_items():
    """Clear failed synchronization items"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Only admin can clear failed items
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        success = offline_manager.clear_failed_items()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Failed synchronization items cleared successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to clear synchronization items'
            })
            
    except Exception as e:
        logger.error(f"Error clearing failed items: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/check_connection')
def check_connection():
    """Check internet connection status"""
    try:
        # Force online status check
        offline_manager._check_online_status()
        
        return jsonify({
            'success': True,
            'data': {
                'is_online': offline_manager.is_online,
                'checked_at': datetime.utcnow().isoformat(),
                'can_reach_server': offline_manager.is_online
            }
        })
        
    except Exception as e:
        logger.error(f"Error checking connection: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'data': {
                'is_online': False,
                'checked_at': datetime.utcnow().isoformat(),
                'error': str(e)
            }
        }), 500

@offline_api_bp.route('/sync_history')
@login_required
def get_sync_history():
    """Get synchronization history"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Get sync history from offline database
        import sqlite3
        conn = sqlite3.connect(offline_manager.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT operation, data_type, data_id, status, timestamp, error_message
            FROM sync_log 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''')
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'operation': row[0],
                'data_type': row[1],
                'data_id': row[2],
                'status': row[3],
                'timestamp': row[4],
                'error_message': row[5]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/cache/refresh', methods=['POST'])
@login_required
def refresh_cache():
    """Force refresh of cached data"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Force update cached data
        offline_manager._update_cached_data()
        
        return jsonify({
            'success': True,
            'message': 'Cache refreshed successfully',
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/queue/status')
@login_required
def get_queue_status():
    """Get synchronization queue status"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Get queue status from offline database
        import sqlite3
        conn = sqlite3.connect(offline_manager.offline_db_path)
        cursor = conn.cursor()
        
        # Count pending items
        cursor.execute('SELECT COUNT(*) FROM offline_orders WHERE synced = 0')
        pending_orders = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM offline_payments WHERE synced = 0')
        pending_payments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sync_log WHERE status = "failed"')
        failed_items = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'queue': {
                    'size': pending_orders + pending_payments,
                    'pending_orders': pending_orders,
                    'pending_payments': pending_payments
                },
                'stats': {
                    'failed_items': failed_items,
                    'storage_usage': offline_manager._get_storage_usage()
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/queue/clear', methods=['POST'])
@login_required
def clear_queue():
    """Clear synchronization queue"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Only admin can clear queue
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        # Clear offline database
        import sqlite3
        conn = sqlite3.connect(offline_manager.offline_db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM offline_orders')
        cursor.execute('DELETE FROM offline_payments')
        cursor.execute('DELETE FROM sync_log')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Queue cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/mode/toggle', methods=['POST'])
@login_required
def toggle_offline_mode():
    """Toggle offline mode"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        # Only admin can toggle offline mode
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        data = request.get_json()
        if not data or 'enabled' not in data:
            return jsonify({
                'success': False,
                'message': 'enabled parameter required'
            }), 400
        
        enabled = data['enabled']
        offline_manager.set_offline_mode(enabled)
        
        return jsonify({
            'success': True,
            'message': f'Offline mode {"enabled" if enabled else "disabled"}',
            'offline_mode_enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Error toggling offline mode: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/orders/check_conflict', methods=['POST'])
@login_required
def check_order_conflict():
    """Check for order conflicts"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        order_data = request.get_json()
        if not order_data:
            return jsonify({
                'success': False,
                'message': 'No order data provided'
            }), 400
        
        # Check for existing order with same number
        from models.order import Order
        existing_order = Order.query.filter_by(order_number=order_data.get('order_number')).first()
        
        conflict = existing_order is not None
        
        return jsonify({
            'success': True,
            'conflict': conflict,
            'server_data': existing_order.to_dict() if conflict else None
        })
        
    except Exception as e:
        logger.error(f"Error checking order conflict: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/data/store', methods=['POST'])
@login_required
def store_data_offline():
    """Store general data for offline use"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Store data in offline cache
        offline_manager._cache_data(data)
        
        return jsonify({
            'success': True,
            'message': 'Data cached for offline use'
        })
        
    except Exception as e:
        logger.error(f"Error storing data offline: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@offline_api_bp.route('/orders/batch_store', methods=['POST'])
@login_required
def batch_store_orders():
    """Batch store multiple orders"""
    try:
        # Check session validity
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'message': 'Session expired or invalid'
            }), 401
        
        data = request.get_json()
        if not data or 'orders' not in data:
            return jsonify({
                'success': False,
                'message': 'orders array required'
            }), 400
        
        orders = data['orders']
        stored_count = 0
        
        for order_data in orders:
            try:
                # Add metadata
                order_data.update({
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'created_at': datetime.utcnow().isoformat(),
                    'stored_offline': True
                })
                
                store_offline_order(order_data)
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing batch order: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Stored {stored_count} orders for offline synchronization',
            'stored_count': stored_count
        })
        
    except Exception as e:
        logger.error(f"Error batch storing orders: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500