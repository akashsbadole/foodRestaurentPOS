"""
Hypermarket & Departmental Store routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.hypermarket_departmental_service import create_hypermarket_departmental_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.hypermarket_departmental import (
    Department, HypermarketProduct, ShoppingCartItem, AbandonedCart, 
    DepartmentPromotion, DepartmentSales, SelfCheckout, QueueManagement
)
from models import db
from datetime import datetime, date
import json

# Create blueprint
hypermarket_departmental_bp = Blueprint('hypermarket_departmental', __name__, url_prefix='/hypermarket')

def feature_required(feature_name):
    """Decorator to check if a feature is enabled"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = get_current_tenant_id()
            if not feature_manager.is_enabled(feature_name, tenant_id):
                return jsonify({
                    'success': False,
                    'message': f'Feature {feature_name} is not enabled'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Department Routes

@hypermarket_departmental_bp.route('/api/departments', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_MANAGEMENT')
def get_departments():
    """Get departments with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('parent_department_id'):
            filters['parent_department_id'] = int(request.args.get('parent_department_id'))
        if request.args.get('level'):
            filters['level'] = int(request.args.get('level'))
        if request.args.get('floor_number'):
            filters['floor_number'] = int(request.args.get('floor_number'))
        if request.args.get('manager_name'):
            filters['manager_name'] = request.args.get('manager_name')
        
        departments = service.get_departments(filters)
        return jsonify({
            'success': True,
            'data': [department.to_dict() for department in departments],
            'count': len(departments)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting departments: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/departments', methods=['POST'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_MANAGEMENT')
def create_department():
    """Create a new department"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, department, message = service.create_department(data)
        if success:
            return jsonify({
                'success': True,
                'data': department.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating department: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/departments/hierarchy', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_MANAGEMENT')
def get_department_hierarchy():
    """Get department hierarchy"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        hierarchy = service.get_department_hierarchy()
        return jsonify({
            'success': True,
            'data': hierarchy
        })
    except Exception as e:
        current_app.logger.error(f"Error getting department hierarchy: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Product Routes

@hypermarket_departmental_bp.route('/api/products', methods=['GET'])
@require_auth
@feature_required('FEATURE_MULTICATEGORY_PRODUCTS')
def get_hypermarket_products():
    """Get hypermarket products with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('primary_department_id'):
            filters['primary_department_id'] = int(request.args.get('primary_department_id'))
        if request.args.get('categories'):
            filters['categories'] = request.args.get('categories').split(',')
        if request.args.get('tags'):
            filters['tags'] = request.args.get('tags').split(',')
        if request.args.get('is_perishable'):
            filters['is_perishable'] = request.args.get('is_perishable').lower() == 'true'
        if request.args.get('is_age_restricted'):
            filters['is_age_restricted'] = request.args.get('is_age_restricted').lower() == 'true'
        if request.args.get('min_price'):
            filters['min_price'] = request.args.get('min_price')
        if request.args.get('max_price'):
            filters['max_price'] = request.args.get('max_price')
        if request.args.get('in_stock'):
            filters['in_stock'] = request.args.get('in_stock').lower() == 'true'
        
        products = service.get_hypermarket_products(filters)
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting hypermarket products: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/products', methods=['POST'])
@require_auth
@feature_required('FEATURE_MULTICATEGORY_PRODUCTS')
def create_hypermarket_product():
    """Create a new hypermarket product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, product, message = service.create_hypermarket_product(data)
        if success:
            return jsonify({
                'success': True,
                'data': product.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating hypermarket product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/products/sku/<sku>', methods=['GET'])
@require_auth
@feature_required('FEATURE_MULTICATEGORY_PRODUCTS')
def get_product_by_sku(sku):
    """Get a product by SKU"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        product = service.get_product_by_sku(sku)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting product by SKU: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Shopping Cart Routes

@hypermarket_departmental_bp.route('/api/cart/items', methods=['GET'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def get_cart_items():
    """Get items in a shopping cart"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        cart_id = request.args.get('cart_id')
        if not cart_id:
            return jsonify({'success': False, 'message': 'Cart ID is required'}), 400
        
        items = service.get_cart_items(cart_id)
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting cart items: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/cart/items', methods=['POST'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def create_cart_item():
    """Create a new shopping cart item"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, item, message = service.create_shopping_cart_item(data)
        if success:
            return jsonify({
                'success': True,
                'data': item.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating cart item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/cart/items/<int:item_id>', methods=['PUT'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def update_cart_item(item_id):
    """Update cart item quantity"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data or 'quantity' not in data:
            return jsonify({'success': False, 'message': 'Quantity is required'}), 400
        
        success, message = service.update_cart_item(item_id, int(data['quantity']))
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating cart item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Abandoned Cart Routes

@hypermarket_departmental_bp.route('/api/abandoned-carts', methods=['GET'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def get_abandoned_carts():
    """Get abandoned carts with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('recovery_status'):
            filters['recovery_status'] = request.args.get('recovery_status')
        if request.args.get('abandoned_after'):
            filters['abandoned_after'] = request.args.get('abandoned_after')
        if request.args.get('abandoned_before'):
            filters['abandoned_before'] = request.args.get('abandoned_before')
        if request.args.get('min_value'):
            filters['min_value'] = request.args.get('min_value')
        if request.args.get('max_value'):
            filters['max_value'] = request.args.get('max_value')
        
        carts = service.get_abandoned_carts(filters)
        return jsonify({
            'success': True,
            'data': [cart.to_dict() for cart in carts],
            'count': len(carts)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting abandoned carts: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/abandoned-carts', methods=['POST'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def create_abandoned_cart():
    """Create an abandoned cart record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, cart, message = service.create_abandoned_cart(data)
        if success:
            return jsonify({
                'success': True,
                'data': cart.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating abandoned cart: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/abandoned-carts/<cart_id>/recover', methods=['POST'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def process_cart_recovery(cart_id):
    """Process cart recovery (email or SMS)"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data or 'recovery_type' not in data:
            return jsonify({'success': False, 'message': 'Recovery type is required'}), 400
        
        success, message = service.process_cart_recovery(cart_id, data['recovery_type'])
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error processing cart recovery: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Department Promotion Routes

@hypermarket_departmental_bp.route('/api/promotions', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_PROMOTIONS')
def get_department_promotions():
    """Get department promotions with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        if request.args.get('promotion_type'):
            filters['promotion_type'] = request.args.get('promotion_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_featured'):
            filters['is_featured'] = request.args.get('is_featured').lower() == 'true'
        if request.args.get('valid_only'):
            filters['valid_only'] = request.args.get('valid_only').lower() == 'true'
        
        promotions = service.get_department_promotions(filters)
        return jsonify({
            'success': True,
            'data': [promotion.to_dict() for promotion in promotions],
            'count': len(promotions)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting department promotions: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/promotions', methods=['POST'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_PROMOTIONS')
def create_department_promotion():
    """Create a new department promotion"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, promotion, message = service.create_department_promotion(data)
        if success:
            return jsonify({
                'success': True,
                'data': promotion.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating department promotion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/promotions/<int:promotion_id>/use', methods=['POST'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_PROMOTIONS')
def use_promotion(promotion_id):
    """Use a promotion and increment usage count"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        customer_id = data.get('customer_id') if data else None
        
        success, message = service.use_promotion(promotion_id, customer_id)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error using promotion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Department Sales Routes

@hypermarket_departmental_bp.route('/api/sales', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_SALES')
def get_department_sales():
    """Get department sales with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        if request.args.get('period_type'):
            filters['period_type'] = request.args.get('period_type')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        sales = service.get_department_sales(filters)
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales],
            'count': len(sales)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting department sales: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/sales', methods=['POST'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_SALES')
def create_department_sales():
    """Create a department sales record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, sales, message = service.create_department_sales(data)
        if success:
            return jsonify({
                'success': True,
                'data': sales.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating department sales: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Self-Checkout Routes

@hypermarket_departmental_bp.route('/api/self-checkouts', methods=['GET'])
@require_auth
@feature_required('FEATURE_SELF_CHECKOUT')
def get_self_checkouts():
    """Get self-checkout stations with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_online'):
            filters['is_online'] = request.args.get('is_online').lower() == 'true'
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('maintenance_due'):
            filters['maintenance_due'] = request.args.get('maintenance_due').lower() == 'true'
        
        checkouts = service.get_self_checkouts(filters)
        return jsonify({
            'success': True,
            'data': [checkout.to_dict() for checkout in checkouts],
            'count': len(checkouts)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting self-checkouts: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/self-checkouts', methods=['POST'])
@require_auth
@feature_required('FEATURE_SELF_CHECKOUT')
def create_self_checkout():
    """Create a new self-checkout station"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, checkout, message = service.create_self_checkout(data)
        if success:
            return jsonify({
                'success': True,
                'data': checkout.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating self-checkout: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/self-checkouts/<checkout_id>/status', methods=['PUT'])
@require_auth
@feature_required('FEATURE_SELF_CHECKOUT')
def update_checkout_status(checkout_id):
    """Update self-checkout status"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'success': False, 'message': 'Status is required'}), 400
        
        is_online = data.get('is_online')
        
        success, message = service.update_checkout_status(checkout_id, data['status'], is_online)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating checkout status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Queue Management Routes

@hypermarket_departmental_bp.route('/api/queues', methods=['GET'])
@require_auth
@feature_required('FEATURE_QUEUE_MANAGEMENT')
def get_queues():
    """Get queues with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('department_id'):
            filters['department_id'] = int(request.args.get('department_id'))
        if request.args.get('queue_type'):
            filters['queue_type'] = request.args.get('queue_type')
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        
        queues = service.get_queues(filters)
        return jsonify({
            'success': True,
            'data': [queue.to_dict() for queue in queues],
            'count': len(queues)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting queues: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/queues', methods=['POST'])
@require_auth
@feature_required('FEATURE_QUEUE_MANAGEMENT')
def create_queue():
    """Create a new queue"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, queue, message = service.create_queue(data)
        if success:
            return jsonify({
                'success': True,
                'data': queue.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating queue: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/queues/<queue_id>/status', methods=['PUT'])
@require_auth
@feature_required('FEATURE_QUEUE_MANAGEMENT')
def update_queue_status(queue_id):
    """Update queue status"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        data = request.get_json()
        if not data or 'current_length' not in data:
            return jsonify({'success': False, 'message': 'Current length is required'}), 400
        
        staff_count = data.get('staff_count')
        
        success, message = service.update_queue_status(queue_id, int(data['current_length']), staff_count)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating queue status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Analytics and Reporting Routes

@hypermarket_departmental_bp.route('/api/reports/department-performance', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_ANALYTICS')
def get_department_performance_report():
    """Get department performance report"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        report = service.get_department_performance_report(start_date, end_date)
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        current_app.logger.error(f"Error generating department performance report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@hypermarket_departmental_bp.route('/api/reports/cart-abandonment', methods=['GET'])
@require_auth
@feature_required('FEATURE_CART_ABANDONMENT')
def get_cart_abandonment_analysis():
    """Get cart abandonment analysis"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_hypermarket_departmental_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        analysis = service.get_cart_abandonment_analysis(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        current_app.logger.error(f"Error generating cart abandonment analysis: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@hypermarket_departmental_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_DEPARTMENT_MANAGEMENT')
def get_hypermarket_config():
    """Get hypermarket & departmental store configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'department_management': feature_manager.is_enabled('FEATURE_DEPARTMENT_MANAGEMENT', tenant_id),
                'multicategory_products': feature_manager.is_enabled('FEATURE_MULTICATEGORY_PRODUCTS', tenant_id),
                'cart_abandonment': feature_manager.is_enabled('FEATURE_CART_ABANDONMENT', tenant_id),
                'department_promotions': feature_manager.is_enabled('FEATURE_DEPARTMENT_PROMOTIONS', tenant_id),
                'department_sales': feature_manager.is_enabled('FEATURE_DEPARTMENT_SALES', tenant_id),
                'self_checkout': feature_manager.is_enabled('FEATURE_SELF_CHECKOUT', tenant_id),
                'queue_management': feature_manager.is_enabled('FEATURE_QUEUE_MANAGEMENT', tenant_id),
                'department_analytics': feature_manager.is_enabled('FEATURE_DEPARTMENT_ANALYTICS', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'department_hierarchy_enabled': True,
                'multi_category_products': True,
                'bulk_pricing_enabled': True,
                'promotional_pricing_enabled': True,
                'cart_tracking_enabled': True,
                'abandonment_analysis_enabled': True,
                'self_checkout_enabled': False,
                'queue_management_enabled': True
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting hypermarket config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500