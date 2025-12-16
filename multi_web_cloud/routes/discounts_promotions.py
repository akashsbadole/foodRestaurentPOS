"""
Discounts & Promotions routes for handling coupon codes, BOGO offers,
volume and time-based discounts, category discounts, happy hours,
and promotional pricing engine.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date, time
from decimal import Decimal
from functools import wraps
from models import db, get_tenant_id
from models.discounts_promotions import (
    CouponCode, CouponUsage, BOGOOffer, BOGOUsage, VolumeDiscount, VolumeDiscountUsage,
    TimeBasedDiscount, TimeDiscountUsage, CategoryDiscount, CategoryDiscountUsage,
    PromotionalPricing, PromotionalPricingUsage
)
from services.discounts_promotions_service import create_discounts_promotions_service
from utils.feature_decorators import feature_required
from utils.tenant_query_manager import tenant_scoped
from utils.validation import validate_required_fields, validate_email, validate_phone
import logging

# Create blueprint
discounts_promotions_bp = Blueprint('discounts_promotions', __name__, url_prefix='/api/discounts-promotions')

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to create service instance
def get_service():
    """Create service instance with current tenant"""
    tenant_id = get_tenant_id()
    return create_discounts_promotions_service(tenant_id)

# Error handler
def handle_error(error_msg, status_code=400):
    """Handle API errors"""
    logger.error(f"Discounts & Promotions API Error: {error_msg}")
    return jsonify({'error': error_msg}), status_code

# Success response helper
def success_response(data=None, message="Success", status_code=200):
    """Create success response"""
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

# ==================== Coupon Code Routes ====================

@discounts_promotions_bp.route('/coupon-codes', methods=['GET'])
@feature_required('discounts_promotions')
def get_coupon_codes():
    """Get all coupon codes with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'is_public', 'discount_type', 'valid_only', 'expired', 'search']:
            if param in request.args:
                if param in ['is_active', 'is_public', 'valid_only', 'expired']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        coupon_codes = service.get_coupon_codes(filters)
        
        result = []
        for coupon in coupon_codes:
            result.append({
                'id': coupon.id,
                'coupon_code': coupon.coupon_code,
                'name': coupon.name,
                'description': coupon.description,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'minimum_order_amount': float(coupon.minimum_order_amount) if coupon.minimum_order_amount else None,
                'maximum_discount_amount': float(coupon.maximum_discount_amount) if coupon.maximum_discount_amount else None,
                'usage_limit': coupon.usage_limit,
                'usage_limit_per_customer': coupon.usage_limit_per_customer,
                'used_count': coupon.used_count,
                'valid_from': coupon.valid_from.isoformat() if coupon.valid_from else None,
                'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                'applies_to': coupon.applies_to,
                'exclude_items': coupon.exclude_items,
                'first_time_customers_only': coupon.first_time_customers_only,
                'is_active': coupon.is_active,
                'is_public': coupon.is_public,
                'created_at': coupon.created_at.isoformat() if coupon.created_at else None,
                'updated_at': coupon.updated_at.isoformat() if coupon.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving coupon codes: {str(e)}")

@discounts_promotions_bp.route('/coupon-codes/<int:coupon_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_coupon_code(coupon_id):
    """Get coupon code by ID"""
    try:
        service = get_service()
        coupon = service.get_coupon_code_by_id(coupon_id)
        
        if not coupon:
            return handle_error("Coupon code not found", 404)
        
        # Get usage statistics
        usage_stats = {
            'total_uses': len(coupon.coupon_usages),
            'unique_customers': len(set(usage.customer_id for usage in coupon.coupon_usages if usage.customer_id)),
            'total_discount': float(sum(usage.discount_amount for usage in coupon.coupon_usages))
        }
        
        result = {
            'id': coupon.id,
            'coupon_code': coupon.coupon_code,
            'name': coupon.name,
            'description': coupon.description,
            'discount_type': coupon.discount_type,
            'discount_value': float(coupon.discount_value),
            'minimum_order_amount': float(coupon.minimum_order_amount) if coupon.minimum_order_amount else None,
            'maximum_discount_amount': float(coupon.maximum_discount_amount) if coupon.maximum_discount_amount else None,
            'usage_limit': coupon.usage_limit,
            'usage_limit_per_customer': coupon.usage_limit_per_customer,
            'used_count': coupon.used_count,
            'valid_from': coupon.valid_from.isoformat() if coupon.valid_from else None,
            'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
            'applies_to': coupon.applies_to,
            'exclude_items': coupon.exclude_items,
            'first_time_customers_only': coupon.first_time_customers_only,
            'is_active': coupon.is_active,
            'is_public': coupon.is_public,
            'created_at': coupon.created_at.isoformat() if coupon.created_at else None,
            'updated_at': coupon.updated_at.isoformat() if coupon.updated_at else None,
            'usage_stats': usage_stats
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving coupon code: {str(e)}")

@discounts_promotions_bp.route('/coupon-codes', methods=['POST'])
@feature_required('discounts_promotions')
def create_coupon_code():
    """Create a new coupon code"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['coupon_code', 'name', 'discount_type', 'discount_value', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate discount value
        try:
            discount_value = Decimal(str(data['discount_value']))
            if discount_value <= 0:
                return handle_error("Discount value must be positive")
        except (ValueError, TypeError):
            return handle_error("Invalid discount value")
        
        # Validate dates
        if 'valid_from' in data:
            try:
                datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return handle_error("Invalid valid_from date format. Use YYYY-MM-DD HH:MM:SS")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD HH:MM:SS")
        
        # Validate discount type
        valid_discount_types = ['percentage', 'fixed_amount', 'buy_x_get_y']
        if data['discount_type'] not in valid_discount_types:
            return handle_error(f"Invalid discount type. Must be one of: {', '.join(valid_discount_types)}")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, coupon, message = service.create_coupon_code(data)
        
        if success:
            return success_response({
                'id': coupon.id,
                'coupon_code': coupon.coupon_code,
                'name': coupon.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating coupon code: {str(e)}")

@discounts_promotions_bp.route('/coupon-codes/validate', methods=['POST'])
@feature_required('discounts_promotions')
def validate_coupon_code():
    """Validate a coupon code for use"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        if 'coupon_code' not in data:
            return handle_error("Coupon code is required")
        
        customer_id = data.get('customer_id')
        order_amount = Decimal(str(data['order_amount'])) if data.get('order_amount') else None
        
        service = get_service()
        is_valid, coupon, message = service.validate_coupon_code(data['coupon_code'], customer_id, order_amount)
        
        if is_valid:
            result = {
                'is_valid': True,
                'coupon_code': coupon.coupon_code,
                'name': coupon.name,
                'description': coupon.description,
                'discount_type': coupon.discount_type,
                'discount_value': float(coupon.discount_value),
                'minimum_order_amount': float(coupon.minimum_order_amount) if coupon.minimum_order_amount else None,
                'maximum_discount_amount': float(coupon.maximum_discount_amount) if coupon.maximum_discount_amount else None,
                'valid_until': coupon.valid_until.isoformat() if coupon.valid_until else None,
                'message': message
            }
            return success_response(result)
        else:
            return success_response({
                'is_valid': False,
                'message': message
            })
        
    except Exception as e:
        return handle_error(f"Error validating coupon code: {str(e)}")

@discounts_promotions_bp.route('/coupon-codes/use', methods=['POST'])
@feature_required('discounts_promotions')
def use_coupon_code():
    """Use a coupon code and create usage record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['coupon_code', 'customer_id', 'order_id', 'order_amount']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Get coupon by code first
        service = get_service()
        coupon = service.get_coupon_code_by_code(data['coupon_code'])
        if not coupon:
            return handle_error("Coupon code not found")
        
        # Use the coupon
        success, usage, message = service.use_coupon_code(
            coupon.id,
            data['customer_id'],
            data['order_id'],
            Decimal(str(data['order_amount']))
        )
        
        if success:
            result = {
                'usage_id': usage.id,
                'coupon_code': coupon.coupon_code,
                'discount_amount': float(usage.discount_amount),
                'order_amount': float(usage.order_amount),
                'used_at': usage.used_at.isoformat() if usage.used_at else None,
                'message': message
            }
            return success_response(result, "Coupon code used successfully")
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error using coupon code: {str(e)}")

# ==================== BOGO Offer Routes ====================

@discounts_promotions_bp.route('/bogo-offers', methods=['GET'])
@feature_required('discounts_promotions')
def get_bogo_offers():
    """Get all BOGO offers with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'auto_apply', 'buy_type', 'get_type', 'valid_only', 'search']:
            if param in request.args:
                if param in ['is_active', 'auto_apply', 'valid_only']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        offers = service.get_bogo_offers(filters)
        
        result = []
        for offer in offers:
            result.append({
                'id': offer.id,
                'offer_code': offer.offer_code,
                'name': offer.name,
                'description': offer.description,
                'buy_quantity': offer.buy_quantity,
                'get_quantity': offer.get_quantity,
                'buy_type': offer.buy_type,
                'get_type': offer.get_type,
                'buy_products': offer.buy_products,
                'buy_categories': offer.buy_categories,
                'get_products': offer.get_products,
                'get_categories': offer.get_categories,
                'get_value_limit': float(offer.get_value_limit) if offer.get_value_limit else None,
                'get_discount_type': offer.get_discount_type,
                'get_discount_value': float(offer.get_discount_value) if offer.get_discount_value else None,
                'usage_limit': offer.usage_limit,
                'used_count': offer.used_count,
                'valid_from': offer.valid_from.isoformat() if offer.valid_from else None,
                'valid_until': offer.valid_until.isoformat() if offer.valid_until else None,
                'valid_days': offer.valid_days,
                'valid_hours_start': offer.valid_hours_start.isoformat() if offer.valid_hours_start else None,
                'valid_hours_end': offer.valid_hours_end.isoformat() if offer.valid_hours_end else None,
                'is_active': offer.is_active,
                'auto_apply': offer.auto_apply,
                'created_at': offer.created_at.isoformat() if offer.created_at else None,
                'updated_at': offer.updated_at.isoformat() if offer.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving BOGO offers: {str(e)}")

@discounts_promotions_bp.route('/bogo-offers/<int:offer_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_bogo_offer(offer_id):
    """Get BOGO offer by ID"""
    try:
        service = get_service()
        offer = service.get_bogo_offer_by_id(offer_id)
        
        if not offer:
            return handle_error("BOGO offer not found", 404)
        
        # Get usage statistics
        usage_stats = {
            'total_uses': len(offer.bogo_usages),
            'unique_customers': len(set(usage.customer_id for usage in offer.bogo_usages if usage.customer_id)),
            'total_discount': float(sum(usage.total_discount for usage in offer.bogo_usages))
        }
        
        result = {
            'id': offer.id,
            'offer_code': offer.offer_code,
            'name': offer.name,
            'description': offer.description,
            'buy_quantity': offer.buy_quantity,
            'get_quantity': offer.get_quantity,
            'buy_type': offer.buy_type,
            'get_type': offer.get_type,
            'buy_products': offer.buy_products,
            'buy_categories': offer.buy_categories,
            'get_products': offer.get_products,
            'get_categories': offer.get_categories,
            'get_value_limit': float(offer.get_value_limit) if offer.get_value_limit else None,
            'get_discount_type': offer.get_discount_type,
            'get_discount_value': float(offer.get_discount_value) if offer.get_discount_value else None,
            'usage_limit': offer.usage_limit,
            'used_count': offer.used_count,
            'valid_from': offer.valid_from.isoformat() if offer.valid_from else None,
            'valid_until': offer.valid_until.isoformat() if offer.valid_until else None,
            'valid_days': offer.valid_days,
            'valid_hours_start': offer.valid_hours_start.isoformat() if offer.valid_hours_start else None,
            'valid_hours_end': offer.valid_hours_end.isoformat() if offer.valid_hours_end else None,
            'is_active': offer.is_active,
            'auto_apply': offer.auto_apply,
            'created_at': offer.created_at.isoformat() if offer.created_at else None,
            'updated_at': offer.updated_at.isoformat() if offer.updated_at else None,
            'usage_stats': usage_stats
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving BOGO offer: {str(e)}")

@discounts_promotions_bp.route('/bogo-offers', methods=['POST'])
@feature_required('discounts_promotions')
def create_bogo_offer():
    """Create a new BOGO offer"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['offer_code', 'name', 'buy_quantity', 'get_quantity', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate quantities
        if data['buy_quantity'] <= 0 or data['get_quantity'] <= 0:
            return handle_error("Buy and get quantities must be positive")
        
        # Validate dates
        if 'valid_from' in data:
            try:
                datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return handle_error("Invalid valid_from date format. Use YYYY-MM-DD HH:MM:SS")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD HH:MM:SS")
        
        # Validate times if provided
        if 'valid_hours_start' in data:
            try:
                time.fromisoformat(data['valid_hours_start'])
            except ValueError:
                return handle_error("Invalid valid_hours_start time format. Use HH:MM:SS")
        
        if 'valid_hours_end' in data:
            try:
                time.fromisoformat(data['valid_hours_end'])
            except ValueError:
                return handle_error("Invalid valid_hours_end time format. Use HH:MM:SS")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, offer, message = service.create_bogo_offer(data)
        
        if success:
            return success_response({
                'id': offer.id,
                'offer_code': offer.offer_code,
                'name': offer.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating BOGO offer: {str(e)}")

@discounts_promotions_bp.route('/bogo-offers/validate', methods=['POST'])
@feature_required('discounts_promotions')
def validate_bogo_offer():
    """Validate BOGO offer against cart items"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        if 'offer_id' not in data or 'cart_items' not in data:
            return handle_error("Offer ID and cart items are required")
        
        service = get_service()
        is_valid, offer, validation_data = service.validate_bogo_offer(data['offer_id'], data['cart_items'])
        
        if is_valid:
            result = {
                'is_valid': True,
                'offer_id': offer.id,
                'offer_code': offer.offer_code,
                'name': offer.name,
                'buy_quantity': offer.buy_quantity,
                'get_quantity': offer.get_quantity,
                'free_quantity': validation_data.get('free_quantity', 0),
                'buy_items': validation_data.get('buy_items', []),
                'get_items': validation_data.get('get_items', []),
                'message': "BOGO offer is applicable"
            }
            return success_response(result)
        else:
            return success_response({
                'is_valid': False,
                'message': "BOGO offer is not applicable"
            })
        
    except Exception as e:
        return handle_error(f"Error validating BOGO offer: {str(e)}")

@discounts_promotions_bp.route('/bogo-offers/use', methods=['POST'])
@feature_required('discounts_promotions')
def use_bogo_offer():
    """Use a BOGO offer and create usage record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['offer_id', 'customer_id', 'order_id', 'buy_items', 'get_items']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        service = get_service()
        success, usage, message = service.use_bogo_offer(
            data['offer_id'],
            data['customer_id'],
            data['order_id'],
            data['buy_items'],
            data['get_items']
        )
        
        if success:
            result = {
                'usage_id': usage.id,
                'offer_id': usage.bogo_offer_id,
                'total_discount': float(usage.total_discount),
                'buy_items': usage.buy_items,
                'get_items': usage.get_items,
                'used_at': usage.used_at.isoformat() if usage.used_at else None,
                'message': message
            }
            return success_response(result, "BOGO offer used successfully")
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error using BOGO offer: {str(e)}")

# ==================== Volume Discount Routes ====================

@discounts_promotions_bp.route('/volume-discounts', methods=['GET'])
@feature_required('discounts_promotions')
def get_volume_discounts():
    """Get all volume discounts with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'auto_apply', 'can_stack', 'valid_only', 'search']:
            if param in request.args:
                if param in ['is_active', 'auto_apply', 'can_stack', 'valid_only']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        discounts = service.get_volume_discounts(filters)
        
        result = []
        for discount in discounts:
            result.append({
                'id': discount.id,
                'name': discount.name,
                'description': discount.description,
                'discount_type': discount.discount_type,
                'tiers': discount.tiers,
                'applies_to': discount.applies_to,
                'product_ids': discount.product_ids,
                'category_ids': discount.category_ids,
                'brand_ids': discount.brand_ids,
                'based_on': discount.based_on,
                'measurement_unit': discount.measurement_unit,
                'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
                'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
                'priority': discount.priority,
                'can_stack': discount.can_stack,
                'is_active': discount.is_active,
                'auto_apply': discount.auto_apply,
                'created_at': discount.created_at.isoformat() if discount.created_at else None,
                'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving volume discounts: {str(e)}")

@discounts_promotions_bp.route('/volume-discounts/<int:discount_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_volume_discount(discount_id):
    """Get volume discount by ID"""
    try:
        service = get_service()
        discount = service.get_volume_discount_by_id(discount_id)
        
        if not discount:
            return handle_error("Volume discount not found", 404)
        
        result = {
            'id': discount.id,
            'name': discount.name,
            'description': discount.description,
            'discount_type': discount.discount_type,
            'tiers': discount.tiers,
            'applies_to': discount.applies_to,
            'product_ids': discount.product_ids,
            'category_ids': discount.category_ids,
            'brand_ids': discount.brand_ids,
            'based_on': discount.based_on,
            'measurement_unit': discount.measurement_unit,
            'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
            'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
            'priority': discount.priority,
            'can_stack': discount.can_stack,
            'is_active': discount.is_active,
            'auto_apply': discount.auto_apply,
            'created_at': discount.created_at.isoformat() if discount.created_at else None,
            'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving volume discount: {str(e)}")

@discounts_promotions_bp.route('/volume-discounts', methods=['POST'])
@feature_required('discounts_promotions')
def create_volume_discount():
    """Create a new volume discount"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'discount_type', 'tiers', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate tiers
        if not isinstance(data['tiers'], list) or len(data['tiers']) == 0:
            return handle_error("Tiers must be a non-empty array")
        
        # Validate discount type
        valid_discount_types = ['percentage', 'fixed_amount', 'fixed_price']
        if data['discount_type'] not in valid_discount_types:
            return handle_error(f"Invalid discount type. Must be one of: {', '.join(valid_discount_types)}")
        
        # Validate dates
        if 'valid_from' in data:
            try:
                datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return handle_error("Invalid valid_from date format. Use YYYY-MM-DD HH:MM:SS")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD HH:MM:SS")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, discount, message = service.create_volume_discount(data)
        
        if success:
            return success_response({
                'id': discount.id,
                'name': discount.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating volume discount: {str(e)}")

@discounts_promotions_bp.route('/volume-discounts/calculate', methods=['POST'])
@feature_required('discounts_promotions')
def calculate_volume_discount():
    """Calculate volume discount for given quantity/amount"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        if 'discount_id' not in data:
            return handle_error("Discount ID is required")
        
        if 'quantity' not in data and 'amount' not in data:
            return handle_error("Either quantity or amount is required")
        
        quantity = data.get('quantity')
        amount = Decimal(str(data['amount'])) if data.get('amount') else None
        
        service = get_service()
        is_applicable, discount_amount, details = service.calculate_volume_discount(
            data['discount_id'], quantity, amount
        )
        
        result = {
            'is_applicable': is_applicable,
            'discount_amount': float(discount_amount),
            'details': details
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error calculating volume discount: {str(e)}")

# ==================== Time-based Discount Routes ====================

@discounts_promotions_bp.route('/time-based-discounts', methods=['GET'])
@feature_required('discounts_promotions')
def get_time_based_discounts():
    """Get all time-based discounts with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'auto_apply', 'can_stack', 'valid_only', 'search']:
            if param in request.args:
                if param in ['is_active', 'auto_apply', 'can_stack', 'valid_only']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        discounts = service.get_time_based_discounts(filters)
        
        result = []
        for discount in discounts:
            result.append({
                'id': discount.id,
                'name': discount.name,
                'description': discount.description,
                'discount_type': discount.discount_type,
                'discount_value': float(discount.discount_value),
                'days_of_week': discount.days_of_week,
                'start_time': discount.start_time.isoformat() if discount.start_time else None,
                'end_time': discount.end_time.isoformat() if discount.end_time else None,
                'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
                'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
                'applies_to': discount.applies_to,
                'product_ids': discount.product_ids,
                'category_ids': discount.category_ids,
                'minimum_order_amount': float(discount.minimum_order_amount) if discount.minimum_order_amount else None,
                'priority': discount.priority,
                'can_stack': discount.can_stack,
                'is_active': discount.is_active,
                'auto_apply': discount.auto_apply,
                'created_at': discount.created_at.isoformat() if discount.created_at else None,
                'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving time-based discounts: {str(e)}")

@discounts_promotions_bp.route('/time-based-discounts/<int:discount_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_time_based_discount(discount_id):
    """Get time-based discount by ID"""
    try:
        service = get_service()
        discount = service.get_time_based_discount_by_id(discount_id)
        
        if not discount:
            return handle_error("Time-based discount not found", 404)
        
        result = {
            'id': discount.id,
            'name': discount.name,
            'description': discount.description,
            'discount_type': discount.discount_type,
            'discount_value': float(discount.discount_value),
            'days_of_week': discount.days_of_week,
            'start_time': discount.start_time.isoformat() if discount.start_time else None,
            'end_time': discount.end_time.isoformat() if discount.end_time else None,
            'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
            'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
            'applies_to': discount.applies_to,
            'product_ids': discount.product_ids,
            'category_ids': discount.category_ids,
            'minimum_order_amount': float(discount.minimum_order_amount) if discount.minimum_order_amount else None,
            'priority': discount.priority,
            'can_stack': discount.can_stack,
            'is_active': discount.is_active,
            'auto_apply': discount.auto_apply,
            'created_at': discount.created_at.isoformat() if discount.created_at else None,
            'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving time-based discount: {str(e)}")

@discounts_promotions_bp.route('/time-based-discounts', methods=['POST'])
@feature_required('discounts_promotions')
def create_time_based_discount():
    """Create a new time-based discount"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'discount_type', 'discount_value', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate discount value
        try:
            discount_value = Decimal(str(data['discount_value']))
            if discount_value <= 0:
                return handle_error("Discount value must be positive")
        except (ValueError, TypeError):
            return handle_error("Invalid discount value")
        
        # Validate discount type
        valid_discount_types = ['percentage', 'fixed_amount']
        if data['discount_type'] not in valid_discount_types:
            return handle_error(f"Invalid discount type. Must be one of: {', '.join(valid_discount_types)}")
        
        # Validate dates
        try:
            datetime.strptime(data['valid_from'], '%Y-%m-%d') if data.get('valid_from') else None
        except ValueError:
            return handle_error("Invalid valid_from date format. Use YYYY-MM-DD")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD")
        
        # Validate times if provided
        if 'start_time' in data:
            try:
                time.fromisoformat(data['start_time'])
            except ValueError:
                return handle_error("Invalid start_time format. Use HH:MM:SS")
        
        if 'end_time' in data:
            try:
                time.fromisoformat(data['end_time'])
            except ValueError:
                return handle_error("Invalid end_time format. Use HH:MM:SS")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, discount, message = service.create_time_based_discount(data)
        
        if success:
            return success_response({
                'id': discount.id,
                'name': discount.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating time-based discount: {str(e)}")

@discounts_promotions_bp.route('/time-based-discounts/<int:discount_id>/check-active', methods=['GET'])
@feature_required('discounts_promotions')
def check_time_discount_active(discount_id):
    """Check if time-based discount is active at current time"""
    try:
        service = get_service()
        is_active = service.is_time_discount_active_now(discount_id)
        
        result = {
            'discount_id': discount_id,
            'is_active_now': is_active,
            'current_time': datetime.utcnow().isoformat()
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error checking time discount status: {str(e)}")

# ==================== Category Discount Routes ====================

@discounts_promotions_bp.route('/category-discounts', methods=['GET'])
@feature_required('discounts_promotions')
def get_category_discounts():
    """Get all category discounts with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'auto_apply', 'can_stack', 'valid_only', 'category_id', 'search']:
            if param in request.args:
                if param in ['is_active', 'auto_apply', 'can_stack', 'valid_only']:
                    filters[param] = request.args.get(param).lower() == 'true'
                elif param == 'category_id':
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        discounts = service.get_category_discounts(filters)
        
        result = []
        for discount in discounts:
            result.append({
                'id': discount.id,
                'name': discount.name,
                'description': discount.description,
                'discount_type': discount.discount_type,
                'discount_value': float(discount.discount_value),
                'category_ids': discount.category_ids,
                'exclude_subcategories': discount.exclude_subcategories,
                'include_child_categories': discount.include_child_categories,
                'minimum_quantity': discount.minimum_quantity,
                'minimum_amount': float(discount.minimum_amount) if discount.minimum_amount else None,
                'maximum_discount_amount': float(discount.maximum_discount_amount) if discount.maximum_discount_amount else None,
                'customer_groups': discount.customer_groups,
                'first_purchase_only': discount.first_purchase_only,
                'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
                'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
                'priority': discount.priority,
                'can_stack': discount.can_stack,
                'is_active': discount.is_active,
                'auto_apply': discount.auto_apply,
                'created_at': discount.created_at.isoformat() if discount.created_at else None,
                'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving category discounts: {str(e)}")

@discounts_promotions_bp.route('/category-discounts/<int:discount_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_category_discount(discount_id):
    """Get category discount by ID"""
    try:
        service = get_service()
        discount = service.get_category_discount_by_id(discount_id)
        
        if not discount:
            return handle_error("Category discount not found", 404)
        
        result = {
            'id': discount.id,
            'name': discount.name,
            'description': discount.description,
            'discount_type': discount.discount_type,
            'discount_value': float(discount.discount_value),
            'category_ids': discount.category_ids,
            'exclude_subcategories': discount.exclude_subcategories,
            'include_child_categories': discount.include_child_categories,
            'minimum_quantity': discount.minimum_quantity,
            'minimum_amount': float(discount.minimum_amount) if discount.minimum_amount else None,
            'maximum_discount_amount': float(discount.maximum_discount_amount) if discount.maximum_discount_amount else None,
            'customer_groups': discount.customer_groups,
            'first_purchase_only': discount.first_purchase_only,
            'valid_from': discount.valid_from.isoformat() if discount.valid_from else None,
            'valid_until': discount.valid_until.isoformat() if discount.valid_until else None,
            'priority': discount.priority,
            'can_stack': discount.can_stack,
            'is_active': discount.is_active,
            'auto_apply': discount.auto_apply,
            'created_at': discount.created_at.isoformat() if discount.created_at else None,
            'updated_at': discount.updated_at.isoformat() if discount.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving category discount: {str(e)}")

@discounts_promotions_bp.route('/category-discounts', methods=['POST'])
@feature_required('discounts_promotions')
def create_category_discount():
    """Create a new category discount"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'discount_type', 'discount_value', 'category_ids', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate category IDs
        if not isinstance(data['category_ids'], list) or len(data['category_ids']) == 0:
            return handle_error("Category IDs must be a non-empty array")
        
        # Validate discount value
        try:
            discount_value = Decimal(str(data['discount_value']))
            if discount_value <= 0:
                return handle_error("Discount value must be positive")
        except (ValueError, TypeError):
            return handle_error("Invalid discount value")
        
        # Validate discount type
        valid_discount_types = ['percentage', 'fixed_amount']
        if data['discount_type'] not in valid_discount_types:
            return handle_error(f"Invalid discount type. Must be one of: {', '.join(valid_discount_types)}")
        
        # Validate dates
        if 'valid_from' in data:
            try:
                datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return handle_error("Invalid valid_from date format. Use YYYY-MM-DD HH:MM:SS")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD HH:MM:SS")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, discount, message = service.create_category_discount(data)
        
        if success:
            return success_response({
                'id': discount.id,
                'name': discount.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating category discount: {str(e)}")

# ==================== Promotional Pricing Routes ====================

@discounts_promotions_bp.route('/promotional-pricing', methods=['GET'])
@feature_required('discounts_promotions')
def get_promotional_pricing():
    """Get all promotional pricing rules with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'auto_apply', 'is_exclusive', 'valid_only', 'pricing_type', 'search']:
            if param in request.args:
                if param in ['is_active', 'auto_apply', 'is_exclusive', 'valid_only']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        pricing_rules = service.get_promotional_pricing(filters)
        
        result = []
        for pricing in pricing_rules:
            result.append({
                'id': pricing.id,
                'name': pricing.name,
                'description': pricing.description,
                'pricing_type': pricing.pricing_type,
                'trigger_condition': pricing.trigger_condition,
                'product_ids': pricing.product_ids,
                'category_ids': pricing.category_ids,
                'brand_ids': pricing.brand_ids,
                'special_prices': pricing.special_prices,
                'discount_rules': pricing.discount_rules,
                'bundle_config': pricing.bundle_config,
                'valid_from': pricing.valid_from.isoformat() if pricing.valid_from else None,
                'valid_until': pricing.valid_until.isoformat() if pricing.valid_until else None,
                'usage_limit': pricing.usage_limit,
                'customer_usage_limit': pricing.customer_usage_limit,
                'priority': pricing.priority,
                'is_exclusive': pricing.is_exclusive,
                'is_active': pricing.is_active,
                'auto_apply': pricing.auto_apply,
                'show_original_price': pricing.show_original_price,
                'promo_label': pricing.promo_label,
                'created_at': pricing.created_at.isoformat() if pricing.created_at else None,
                'updated_at': pricing.updated_at.isoformat() if pricing.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving promotional pricing: {str(e)}")

@discounts_promotions_bp.route('/promotional-pricing/<int:pricing_id>', methods=['GET'])
@feature_required('discounts_promotions')
def get_promotional_pricing_detail(pricing_id):
    """Get promotional pricing by ID"""
    try:
        service = get_service()
        pricing = service.get_promotional_pricing_by_id(pricing_id)
        
        if not pricing:
            return handle_error("Promotional pricing not found", 404)
        
        result = {
            'id': pricing.id,
            'name': pricing.name,
            'description': pricing.description,
            'pricing_type': pricing.pricing_type,
            'trigger_condition': pricing.trigger_condition,
            'product_ids': pricing.product_ids,
            'category_ids': pricing.category_ids,
            'brand_ids': pricing.brand_ids,
            'special_prices': pricing.special_prices,
            'discount_rules': pricing.discount_rules,
            'bundle_config': pricing.bundle_config,
            'valid_from': pricing.valid_from.isoformat() if pricing.valid_from else None,
            'valid_until': pricing.valid_until.isoformat() if pricing.valid_until else None,
            'usage_limit': pricing.usage_limit,
            'customer_usage_limit': pricing.customer_usage_limit,
            'priority': pricing.priority,
            'is_exclusive': pricing.is_exclusive,
            'is_active': pricing.is_active,
            'auto_apply': pricing.auto_apply,
            'show_original_price': pricing.show_original_price,
            'promo_label': pricing.promo_label,
            'created_at': pricing.created_at.isoformat() if pricing.created_at else None,
            'updated_at': pricing.updated_at.isoformat() if pricing.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving promotional pricing: {str(e)}")

@discounts_promotions_bp.route('/promotional-pricing', methods=['POST'])
@feature_required('discounts_promotions')
def create_promotional_pricing():
    """Create a new promotional pricing rule"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'pricing_type', 'valid_until']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate pricing type
        valid_pricing_types = ['special_price', 'discount_rule', 'bundle']
        if data['pricing_type'] not in valid_pricing_types:
            return handle_error(f"Invalid pricing type. Must be one of: {', '.join(valid_pricing_types)}")
        
        # Validate dates
        if 'valid_from' in data:
            try:
                datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return handle_error("Invalid valid_from date format. Use YYYY-MM-DD HH:MM:SS")
        
        try:
            datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return handle_error("Invalid valid_until date format. Use YYYY-MM-DD HH:MM:SS")
        
        # Add tenant ID and created_by to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, pricing, message = service.create_promotional_pricing(data)
        
        if success:
            return success_response({
                'id': pricing.id,
                'name': pricing.name
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating promotional pricing: {str(e)}")

@discounts_promotions_bp.route('/promotional-pricing/calculate', methods=['POST'])
@feature_required('discounts_promotions')
def calculate_promotional_price():
    """Calculate promotional price for a product"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['pricing_id', 'product_id', 'original_price']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate original price
        try:
            original_price = Decimal(str(data['original_price']))
            if original_price <= 0:
                return handle_error("Original price must be positive")
        except (ValueError, TypeError):
            return handle_error("Invalid original price")
        
        quantity = data.get('quantity', 1)
        if quantity <= 0:
            return handle_error("Quantity must be positive")
        
        customer_id = data.get('customer_id')
        
        service = get_service()
        is_applicable, promotional_price, details = service.calculate_promotional_price(
            data['pricing_id'],
            data['product_id'],
            original_price,
            quantity,
            customer_id
        )
        
        result = {
            'is_applicable': is_applicable,
            'original_price': float(original_price),
            'promotional_price': float(promotional_price),
            'quantity': quantity,
            'discount_amount': float(original_price - promotional_price) if is_applicable else 0,
            'details': details
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error calculating promotional price: {str(e)}")

# ==================== Analytics Routes ====================

@discounts_promotions_bp.route('/analytics', methods=['GET'])
@feature_required('discounts_promotions')
def get_discount_analytics():
    """Get discount analytics for a date range"""
    try:
        # Parse date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        service = get_service()
        analytics = service.get_discount_analytics(start_date, end_date)
        
        return success_response(analytics)
        
    except ValueError:
        return handle_error("Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        return handle_error(f"Error retrieving discount analytics: {str(e)}")

# ==================== Error Handlers ====================

@discounts_promotions_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@discounts_promotions_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500