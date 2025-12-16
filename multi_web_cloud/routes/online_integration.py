"""
Routes for Online Integration module handling online order processing, click-and-collect functionality,
home delivery management, and third-party integration framework.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps

from models import db
from models.online_integration import (
    OnlineOrder, ClickAndCollect, HomeDelivery, DeliveryPartner,
    ThirdPartyIntegration, OnlineOrderHistory, OnlineOrderReview,
    OnlineOrderAnalytics, OnlineOrderStatus, DeliveryType, ThirdPartyPlatform
)
from models.feature_flag import feature_flag_service
from services.online_integration_service import online_integration_service
from middleware.tenant_middleware import get_current_tenant
from routes.validation_api import validate_tenant_access

# Create blueprint
online_integration_bp = Blueprint('online_integration', __name__, url_prefix='/api/online-integration')

# Decorator to check feature flag
def feature_required(feature_name):
    """Decorator to check if a feature is enabled for the current tenant"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = get_current_tenant()
            if not tenant_id:
                return jsonify({'error': 'Tenant not found'}), 401
            
            if not feature_flag_service.is_feature_enabled(feature_name, tenant_id):
                return jsonify({'error': f'Feature {feature_name} is not enabled'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Online Order Routes

@online_integration_bp.route('/online-orders', methods=['POST'])
@feature_required('online_orders')
def create_online_order():
    """Create a new online order"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        order, error = online_integration_service.create_online_order(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Online order created successfully',
            'order': order.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating online order: {str(e)}")
        return jsonify({'error': 'Failed to create online order'}), 500


@online_integration_bp.route('/online-orders', methods=['GET'])
@feature_required('online_orders')
def get_online_orders():
    """Get online orders with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        status = request.args.get('status')
        platform = request.args.get('platform')
        store_id = request.args.get('store_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert date strings to date objects if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        orders = online_integration_service.get_online_orders(
            tenant_id, status, platform, store_id, start_date, end_date
        )
        
        return jsonify({
            'orders': [order.to_dict() for order in orders],
            'count': len(orders)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting online orders: {str(e)}")
        return jsonify({'error': 'Failed to get online orders'}), 500


@online_integration_bp.route('/online-orders/<int:order_id>', methods=['GET'])
@feature_required('online_orders')
def get_online_order(order_id):
    """Get a specific online order by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        order = online_integration_service.get_online_order(order_id, tenant_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'order': order.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting online order: {str(e)}")
        return jsonify({'error': 'Failed to get online order'}), 500


@online_integration_bp.route('/online-orders/<int:order_id>', methods=['PUT'])
@feature_required('online_orders')
def update_online_order(order_id):
    """Update online order"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        order, error = online_integration_service.update_online_order(order_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({
            'message': 'Online order updated successfully',
            'order': order.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating online order: {str(e)}")
        return jsonify({'error': 'Failed to update online order'}), 500


@online_integration_bp.route('/online-orders/<int:order_id>/confirm', methods=['POST'])
@feature_required('online_orders')
def confirm_online_order(order_id):
    """Confirm an online order"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        confirmed_by = data.get('confirmed_by')
        
        if not confirmed_by:
            return jsonify({'error': 'Confirmed by user ID is required'}), 400
        
        success, error = online_integration_service.confirm_online_order(order_id, confirmed_by, tenant_id)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'message': 'Online order confirmed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error confirming online order: {str(e)}")
        return jsonify({'error': 'Failed to confirm online order'}), 500


@online_integration_bp.route('/online-orders/<int:order_id>/cancel', methods=['POST'])
@feature_required('online_orders')
def cancel_online_order(order_id):
    """Cancel an online order"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        cancelled_by = data.get('cancelled_by')
        cancellation_reason = data.get('cancellation_reason')
        
        if not cancelled_by:
            return jsonify({'error': 'Cancelled by user ID is required'}), 400
        
        if not cancellation_reason:
            return jsonify({'error': 'Cancellation reason is required'}), 400
        
        success, error = online_integration_service.cancel_online_order(
            order_id, cancelled_by, tenant_id, cancellation_reason
        )
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Order not found'}), 404
        
        return jsonify({'message': 'Online order cancelled successfully'})
    except Exception as e:
        current_app.logger.error(f"Error cancelling online order: {str(e)}")
        return jsonify({'error': 'Failed to cancel online order'}), 500


# Click and Collect Routes

@online_integration_bp.route('/click-and-collect', methods=['POST'])
@feature_required('click_and_collect')
def create_click_and_collect():
    """Create a new click and collect record"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        collect, error = online_integration_service.create_click_and_collect(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Click and collect record created successfully',
            'collect': collect.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating click and collect: {str(e)}")
        return jsonify({'error': 'Failed to create click and collect'}), 500


@online_integration_bp.route('/click-and-collect/<int:collect_id>', methods=['GET'])
@feature_required('click_and_collect')
def get_click_and_collect(collect_id):
    """Get a specific click and collect record by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        collect = online_integration_service.get_click_and_collect(collect_id, tenant_id)
        if not collect:
            return jsonify({'error': 'Click and collect record not found'}), 404
        
        return jsonify({'collect': collect.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting click and collect: {str(e)}")
        return jsonify({'error': 'Failed to get click and collect'}), 500


@online_integration_bp.route('/click-and-collect/order/<int:order_id>', methods=['GET'])
@feature_required('click_and_collect')
def get_click_and_collect_by_order(order_id):
    """Get click and collect by order ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        collect = online_integration_service.get_click_and_collect_by_order(order_id, tenant_id)
        if not collect:
            return jsonify({'error': 'Click and collect record not found'}), 404
        
        return jsonify({'collect': collect.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting click and collect by order: {str(e)}")
        return jsonify({'error': 'Failed to get click and collect'}), 500


@online_integration_bp.route('/click-and-collect/<int:collect_id>', methods=['PUT'])
@feature_required('click_and_collect')
def update_click_and_collect(collect_id):
    """Update click and collect"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        collect, error = online_integration_service.update_click_and_collect(collect_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not collect:
            return jsonify({'error': 'Click and collect record not found'}), 404
        
        return jsonify({
            'message': 'Click and collect updated successfully',
            'collect': collect.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating click and collect: {str(e)}")
        return jsonify({'error': 'Failed to update click and collect'}), 500


@online_integration_bp.route('/click-and-collect/<int:collect_id>/ready', methods=['POST'])
@feature_required('click_and_collect')
def mark_ready_for_pickup(collect_id):
    """Mark click and collect as ready for pickup"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        prepared_by = data.get('prepared_by')
        
        if not prepared_by:
            return jsonify({'error': 'Prepared by user ID is required'}), 400
        
        success, error = online_integration_service.mark_ready_for_pickup(collect_id, prepared_by, tenant_id)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Click and collect record not found'}), 404
        
        return jsonify({'message': 'Click and collect marked as ready for pickup'})
    except Exception as e:
        current_app.logger.error(f"Error marking click and collect as ready: {str(e)}")
        return jsonify({'error': 'Failed to mark click and collect as ready'}), 500


@online_integration_bp.route('/click-and-collect/<int:collect_id>/complete', methods=['POST'])
@feature_required('click_and_collect')
def complete_pickup(collect_id):
    """Complete click and collect pickup"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        handed_over_by = data.get('handed_over_by')
        
        if not handed_over_by:
            return jsonify({'error': 'Handed over by user ID is required'}), 400
        
        success, error = online_integration_service.complete_pickup(collect_id, handed_over_by, tenant_id)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Click and collect record not found'}), 404
        
        return jsonify({'message': 'Click and collect pickup completed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error completing click and collect pickup: {str(e)}")
        return jsonify({'error': 'Failed to complete click and collect pickup'}), 500


# Home Delivery Routes

@online_integration_bp.route('/home-deliveries', methods=['POST'])
@feature_required('home_delivery')
def create_home_delivery():
    """Create a new home delivery record"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        delivery, error = online_integration_service.create_home_delivery(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Home delivery record created successfully',
            'delivery': delivery.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating home delivery: {str(e)}")
        return jsonify({'error': 'Failed to create home delivery'}), 500


@online_integration_bp.route('/home-deliveries/<int:delivery_id>', methods=['GET'])
@feature_required('home_delivery')
def get_home_delivery(delivery_id):
    """Get a specific home delivery record by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        delivery = online_integration_service.get_home_delivery(delivery_id, tenant_id)
        if not delivery:
            return jsonify({'error': 'Home delivery record not found'}), 404
        
        return jsonify({'delivery': delivery.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting home delivery: {str(e)}")
        return jsonify({'error': 'Failed to get home delivery'}), 500


@online_integration_bp.route('/home-deliveries/order/<int:order_id>', methods=['GET'])
@feature_required('home_delivery')
def get_home_delivery_by_order(order_id):
    """Get home delivery by order ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        delivery = online_integration_service.get_home_delivery_by_order(order_id, tenant_id)
        if not delivery:
            return jsonify({'error': 'Home delivery record not found'}), 404
        
        return jsonify({'delivery': delivery.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting home delivery by order: {str(e)}")
        return jsonify({'error': 'Failed to get home delivery'}), 500


@online_integration_bp.route('/home-deliveries/<int:delivery_id>', methods=['PUT'])
@feature_required('home_delivery')
def update_home_delivery(delivery_id):
    """Update home delivery"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        delivery, error = online_integration_service.update_home_delivery(delivery_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not delivery:
            return jsonify({'error': 'Home delivery record not found'}), 404
        
        return jsonify({
            'message': 'Home delivery updated successfully',
            'delivery': delivery.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating home delivery: {str(e)}")
        return jsonify({'error': 'Failed to update home delivery'}), 500


@online_integration_bp.route('/home-deliveries/<int:delivery_id>/dispatch', methods=['POST'])
@feature_required('home_delivery')
def dispatch_delivery(delivery_id):
    """Dispatch home delivery"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        dispatched_by = data.get('dispatched_by')
        delivery_partner_id = data.get('delivery_partner_id')
        
        if not dispatched_by:
            return jsonify({'error': 'Dispatched by user ID is required'}), 400
        
        if not delivery_partner_id:
            return jsonify({'error': 'Delivery partner ID is required'}), 400
        
        success, error = online_integration_service.dispatch_delivery(
            delivery_id, dispatched_by, tenant_id, delivery_partner_id
        )
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Home delivery record not found'}), 404
        
        return jsonify({'message': 'Home delivery dispatched successfully'})
    except Exception as e:
        current_app.logger.error(f"Error dispatching home delivery: {str(e)}")
        return jsonify({'error': 'Failed to dispatch home delivery'}), 500


@online_integration_bp.route('/home-deliveries/<int:delivery_id>/complete', methods=['POST'])
@feature_required('home_delivery')
def complete_delivery(delivery_id):
    """Complete home delivery"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        delivery_proof = data.get('delivery_proof', {})
        
        success, error = online_integration_service.complete_delivery(delivery_id, tenant_id, delivery_proof)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Home delivery record not found'}), 404
        
        return jsonify({'message': 'Home delivery completed successfully'})
    except Exception as e:
        current_app.logger.error(f"Error completing home delivery: {str(e)}")
        return jsonify({'error': 'Failed to complete home delivery'}), 500


# Delivery Partner Routes

@online_integration_bp.route('/delivery-partners', methods=['POST'])
@feature_required('delivery_partners')
def create_delivery_partner():
    """Create a new delivery partner"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        partner, error = online_integration_service.create_delivery_partner(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Delivery partner created successfully',
            'partner': partner.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating delivery partner: {str(e)}")
        return jsonify({'error': 'Failed to create delivery partner'}), 500


@online_integration_bp.route('/delivery-partners', methods=['GET'])
@feature_required('delivery_partners')
def get_delivery_partners():
    """Get all delivery partners for the current tenant"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        partners = online_integration_service.get_delivery_partners(tenant_id, active_only)
        
        return jsonify({
            'partners': [partner.to_dict() for partner in partners],
            'count': len(partners)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting delivery partners: {str(e)}")
        return jsonify({'error': 'Failed to get delivery partners'}), 500


@online_integration_bp.route('/delivery-partners/<int:partner_id>', methods=['GET'])
@feature_required('delivery_partners')
def get_delivery_partner(partner_id):
    """Get a specific delivery partner by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        partner = online_integration_service.get_delivery_partner(partner_id, tenant_id)
        if not partner:
            return jsonify({'error': 'Delivery partner not found'}), 404
        
        return jsonify({'partner': partner.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting delivery partner: {str(e)}")
        return jsonify({'error': 'Failed to get delivery partner'}), 500


@online_integration_bp.route('/delivery-partners/<int:partner_id>', methods=['PUT'])
@feature_required('delivery_partners')
def update_delivery_partner(partner_id):
    """Update delivery partner"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        partner, error = online_integration_service.update_delivery_partner(partner_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not partner:
            return jsonify({'error': 'Delivery partner not found'}), 404
        
        return jsonify({
            'message': 'Delivery partner updated successfully',
            'partner': partner.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating delivery partner: {str(e)}")
        return jsonify({'error': 'Failed to update delivery partner'}), 500


# Third-Party Integration Routes

@online_integration_bp.route('/third-party-integrations', methods=['POST'])
@feature_required('third_party_integration')
def create_third_party_integration():
    """Create a new third-party integration"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        integration, error = online_integration_service.create_third_party_integration(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Third-party integration created successfully',
            'integration': integration.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating third-party integration: {str(e)}")
        return jsonify({'error': 'Failed to create third-party integration'}), 500


@online_integration_bp.route('/third-party-integrations', methods=['GET'])
@feature_required('third_party_integration')
def get_third_party_integrations():
    """Get third-party integrations with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        platform = request.args.get('platform')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        integrations = online_integration_service.get_third_party_integrations(
            tenant_id, platform, active_only
        )
        
        return jsonify({
            'integrations': [integration.to_dict() for integration in integrations],
            'count': len(integrations)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting third-party integrations: {str(e)}")
        return jsonify({'error': 'Failed to get third-party integrations'}), 500


@online_integration_bp.route('/third-party-integrations/<int:integration_id>', methods=['GET'])
@feature_required('third_party_integration')
def get_third_party_integration(integration_id):
    """Get a specific third-party integration by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        integration = online_integration_service.get_third_party_integration(integration_id, tenant_id)
        if not integration:
            return jsonify({'error': 'Integration not found'}), 404
        
        return jsonify({'integration': integration.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting third-party integration: {str(e)}")
        return jsonify({'error': 'Failed to get third-party integration'}), 500


@online_integration_bp.route('/third-party-integrations/<int:integration_id>', methods=['PUT'])
@feature_required('third_party_integration')
def update_third_party_integration(integration_id):
    """Update third-party integration"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        integration, error = online_integration_service.update_third_party_integration(integration_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not integration:
            return jsonify({'error': 'Integration not found'}), 404
        
        return jsonify({
            'message': 'Third-party integration updated successfully',
            'integration': integration.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating third-party integration: {str(e)}")
        return jsonify({'error': 'Failed to update third-party integration'}), 500


# Online Order Review Routes

@online_integration_bp.route('/online-order-reviews', methods=['POST'])
@feature_required('order_reviews')
def create_online_order_review():
    """Create a new online order review"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        review, error = online_integration_service.create_online_order_review(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Online order review created successfully',
            'review': review.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating online order review: {str(e)}")
        return jsonify({'error': 'Failed to create online order review'}), 500


@online_integration_bp.route('/online-order-reviews', methods=['GET'])
@feature_required('order_reviews')
def get_online_order_reviews():
    """Get online order reviews with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        approved_only = request.args.get('approved_only', 'false').lower() == 'true'
        featured_only = request.args.get('featured_only', 'false').lower() == 'true'
        
        reviews = online_integration_service.get_online_order_reviews(tenant_id, approved_only, featured_only)
        
        return jsonify({
            'reviews': [review.to_dict() for review in reviews],
            'count': len(reviews)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting online order reviews: {str(e)}")
        return jsonify({'error': 'Failed to get online order reviews'}), 500


@online_integration_bp.route('/online-order-reviews/<int:review_id>', methods=['GET'])
@feature_required('order_reviews')
def get_online_order_review(review_id):
    """Get a specific online order review by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        review = online_integration_service.get_online_order_review(review_id, tenant_id)
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        return jsonify({'review': review.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting online order review: {str(e)}")
        return jsonify({'error': 'Failed to get online order review'}), 500


@online_integration_bp.route('/online-order-reviews/<int:review_id>', methods=['PUT'])
@feature_required('order_reviews')
def update_online_order_review(review_id):
    """Update online order review"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        review, error = online_integration_service.update_online_order_review(review_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not review:
            return jsonify({'error': 'Review not found'}), 404
        
        return jsonify({
            'message': 'Online order review updated successfully',
            'review': review.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating online order review: {str(e)}")
        return jsonify({'error': 'Failed to update online order review'}), 500


# Online Order Analytics Routes

@online_integration_bp.route('/online-order-analytics', methods=['POST'])
@feature_required('online_analytics')
def create_online_order_analytics():
    """Create a new online order analytics record"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        analytics, error = online_integration_service.create_online_order_analytics(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Online order analytics created successfully',
            'analytics': analytics.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating online order analytics: {str(e)}")
        return jsonify({'error': 'Failed to create online order analytics'}), 500


@online_integration_bp.route('/online-order-analytics/<int:analytics_id>', methods=['GET'])
@feature_required('online_analytics')
def get_online_order_analytics(analytics_id):
    """Get a specific online order analytics record by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        analytics = online_integration_service.get_online_order_analytics(analytics_id, tenant_id)
        if not analytics:
            return jsonify({'error': 'Analytics record not found'}), 404
        
        return jsonify({'analytics': analytics.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting online order analytics: {str(e)}")
        return jsonify({'error': 'Failed to get online order analytics'}), 500


@online_integration_bp.route('/online-order-analytics/date-range', methods=['GET'])
@feature_required('online_analytics')
def get_online_order_analytics_by_date_range():
    """Get online order analytics by date range"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        analytics = online_integration_service.get_online_order_analytics_by_date_range(
            tenant_id, start_date, end_date
        )
        
        return jsonify({
            'analytics': [analytics.to_dict() for analytics in analytics],
            'count': len(analytics)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting online order analytics by date range: {str(e)}")
        return jsonify({'error': 'Failed to get online order analytics'}), 500


@online_integration_bp.route('/online-order-analytics/generate', methods=['POST'])
@feature_required('online_analytics')
def generate_online_order_analytics():
    """Generate online order analytics for a specific date"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        analytics_date = datetime.strptime(data.get('analytics_date'), '%Y-%m-%d').date()
        
        analytics_data = online_integration_service.generate_online_order_analytics(tenant_id, analytics_date)
        
        if 'error' in analytics_data:
            return jsonify({'error': analytics_data['error']}), 400
        
        return jsonify({
            'message': 'Online order analytics generated successfully',
            'analytics_data': analytics_data
        })
    except Exception as e:
        current_app.logger.error(f"Error generating online order analytics: {str(e)}")
        return jsonify({'error': 'Failed to generate online order analytics'}), 500