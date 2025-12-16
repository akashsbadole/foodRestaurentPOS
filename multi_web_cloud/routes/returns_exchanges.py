"""
Returns & Exchanges routes for handling comprehensive return management,
exchange processing with variant matching, refund processing and store credit,
and return approval workflows.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from models import db, get_tenant_id
from models.returns_exchanges import (
    ReturnRequest, ReturnItem, ExchangeRequest, ExchangeItem, ReturnPolicy, 
    ReturnWorkflow, ReturnAuditLog, ReturnStatus, ReturnReason, RefundMethod, ExchangeStatus
)
from services.returns_exchanges_service import create_returns_exchanges_service
from utils.feature_decorators import feature_required
from utils.tenant_query_manager import tenant_scoped
from utils.validation import validate_required_fields, validate_email, validate_phone
import logging

# Create blueprint
returns_exchanges_bp = Blueprint('returns_exchanges', __name__, url_prefix='/api/returns-exchanges')

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to create service instance
def get_service():
    """Create service instance with current tenant"""
    tenant_id = get_tenant_id()
    return create_returns_exchanges_service(tenant_id)

# Error handler
def handle_error(error_msg, status_code=400):
    """Handle API errors"""
    logger.error(f"Returns & Exchanges API Error: {error_msg}")
    return jsonify({'error': error_msg}), status_code

# Success response helper
def success_response(data=None, message="Success", status_code=200):
    """Create success response"""
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

# ==================== Return Request Routes ====================

@returns_exchanges_bp.route('/return-requests', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_requests():
    """Get all return requests with optional filters"""
    try:
        filters = {}
        for param in ['status', 'customer_id', 'return_reason', 'date_from', 'date_to', 'approved_by', 'search']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param in ['customer_id', 'approved_by']:
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        return_requests = service.get_return_requests(filters)
        
        result = []
        for return_request in return_requests:
            result.append({
                'id': return_request.id,
                'return_number': return_request.return_number,
                'original_order_id': return_request.original_order_id,
                'customer_id': return_request.customer_id,
                'customer_name': return_request.customer_name,
                'customer_email': return_request.customer_email,
                'customer_phone': return_request.customer_phone,
                'return_date': return_request.return_date.isoformat() if return_request.return_date else None,
                'status': return_request.status.value,
                'return_reason': return_request.return_reason.value,
                'return_reason_details': return_request.return_reason_details,
                'total_refund_amount': float(return_request.total_refund_amount) if return_request.total_refund_amount else None,
                'refund_method': return_request.refund_method.value if return_request.refund_method else None,
                'store_credit_issued': float(return_request.store_credit_issued) if return_request.store_credit_issued else None,
                'store_credit_expiry': return_request.store_credit_expiry.isoformat() if return_request.store_credit_expiry else None,
                'notes': return_request.notes,
                'created_at': return_request.created_at.isoformat() if return_request.created_at else None,
                'updated_at': return_request.updated_at.isoformat() if return_request.updated_at else None,
                'is_approved': return_request.is_approved,
                'is_completed': return_request.is_completed,
                'days_since_return': return_request.days_since_return
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return requests: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_request(return_id):
    """Get return request by ID with full details"""
    try:
        service = get_service()
        return_request = service.get_return_request_by_id(return_id)
        
        if not return_request:
            return handle_error("Return request not found", 404)
        
        # Get return items
        return_items = []
        for item in return_request.return_items:
            return_items.append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'variant_id': item.variant_id,
                'variant_name': item.variant_name,
                'variant_attributes': item.variant_attributes,
                'original_quantity': item.original_quantity,
                'original_unit_price': float(item.original_unit_price),
                'original_total_price': float(item.original_total_price),
                'return_quantity': item.return_quantity,
                'return_condition': item.return_condition,
                'condition_details': item.condition_details,
                'unit_price': float(item.unit_price),
                'total_value': float(item.total_value),
                'deduction_amount': float(item.deduction_amount),
                'deduction_reason': item.deduction_reason,
                'refundable_amount': float(item.refundable_amount),
                'restock_fee': float(item.restock_fee),
                'restock_fee_reason': item.restock_fee_reason,
                'should_restock': item.should_restock,
                'restocked_quantity': item.restocked_quantity,
                'restocked_at': item.restocked_at.isoformat() if item.restocked_at else None,
                'item_notes': item.item_notes
            })
        
        result = {
            'id': return_request.id,
            'return_number': return_request.return_number,
            'original_order_id': return_request.original_order_id,
            'customer_id': return_request.customer_id,
            'customer_name': return_request.customer_name,
            'customer_email': return_request.customer_email,
            'customer_phone': return_request.customer_phone,
            'return_date': return_request.return_date.isoformat() if return_request.return_date else None,
            'status': return_request.status.value,
            'return_reason': return_request.return_reason.value,
            'return_reason_details': return_request.return_reason_details,
            'approved_by': return_request.approved_by,
            'approved_at': return_request.approved_at.isoformat() if return_request.approved_at else None,
            'rejection_reason': return_request.rejection_reason,
            'received_by': return_request.received_by,
            'received_at': return_request.received_at.isoformat() if return_request.received_at else None,
            'processed_by': return_request.processed_by,
            'processed_at': return_request.processed_at.isoformat() if return_request.processed_at else None,
            'total_refund_amount': float(return_request.total_refund_amount) if return_request.total_refund_amount else None,
            'refund_method': return_request.refund_method.value if return_request.refund_method else None,
            'refund_processed_at': return_request.refund_processed_at.isoformat() if return_request.refund_processed_at else None,
            'refund_transaction_id': return_request.refund_transaction_id,
            'store_credit_issued': float(return_request.store_credit_issued) if return_request.store_credit_issued else None,
            'store_credit_expiry': return_request.store_credit_expiry.isoformat() if return_request.store_credit_expiry else None,
            'store_credit_reference': return_request.store_credit_reference,
            'notes': return_request.notes,
            'internal_notes': return_request.internal_notes,
            'customer_notes': return_request.customer_notes,
            'created_at': return_request.created_at.isoformat() if return_request.created_at else None,
            'updated_at': return_request.updated_at.isoformat() if return_request.updated_at else None,
            'return_items': return_items,
            'total_return_value': float(return_request.calculate_total_return_value()),
            'total_refundable_amount': float(return_request.calculate_total_refundable_amount())
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests', methods=['POST'])
@feature_required('returns_exchanges')
def create_return_request():
    """Create a new return request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['original_order_id', 'customer_id', 'customer_name', 'return_reason', 'return_items']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate return items
        if not data['return_items'] or len(data['return_items']) == 0:
            return handle_error("At least one return item is required")
        
        for item in data['return_items']:
            item_required_fields = ['product_id', 'product_name', 'original_quantity', 'original_unit_price', 'original_total_price', 'return_quantity']
            item_validation = validate_required_fields(item, item_required_fields)
            if item_validation:
                return handle_error(f"Return item validation error: {item_validation}")
        
        # Validate return date if provided
        if 'return_date' in data:
            try:
                datetime.strptime(data['return_date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid return date format. Use YYYY-MM-DD")
        
        # Validate return reason
        valid_reasons = [reason.value for reason in ReturnReason]
        if data['return_reason'] not in valid_reasons:
            return handle_error(f"Invalid return reason. Must be one of: {', '.join(valid_reasons)}")
        
        # Add tenant ID and user ID to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['user_id'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, return_request, message = service.create_return_request(data)
        
        if success:
            return success_response({
                'id': return_request.id,
                'return_number': return_request.return_number,
                'status': return_request.status.value
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>/approve', methods=['POST'])
@feature_required('returns_exchanges')
def approve_return_request(return_id):
    """Approve a return request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Get user ID from auth context
        approver_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.approve_return_request(return_id, approver_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error approving return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>/reject', methods=['POST'])
@feature_required('returns_exchanges')
def reject_return_request(return_id):
    """Reject a return request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        if 'rejection_reason' not in data or not data['rejection_reason']:
            return handle_error("Rejection reason is required")
        
        # Get user ID from auth context
        approver_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.reject_return_request(return_id, approver_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error rejecting return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>/receive', methods=['POST'])
@feature_required('returns_exchanges')
def receive_return_request(return_id):
    """Mark return request as received"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate items if provided
        if 'items' in data:
            for item in data['items']:
                if 'item_id' not in item:
                    return handle_error("Item ID is required for each item")
        
        # Get user ID from auth context
        receiver_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.receive_return_request(return_id, receiver_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error receiving return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>/process', methods=['POST'])
@feature_required('returns_exchanges')
def process_return_request(return_id):
    """Process a return request and issue refund/store credit"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate refund method if provided
        if 'refund_method' in data:
            valid_methods = [method.value for method in RefundMethod]
            if data['refund_method'] not in valid_methods:
                return handle_error(f"Invalid refund method. Must be one of: {', '.join(valid_methods)}")
        
        # Get user ID from auth context
        processor_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.process_return_request(return_id, processor_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error processing return request: {str(e)}")

@returns_exchanges_bp.route('/return-requests/<int:return_id>/complete', methods=['POST'])
@feature_required('returns_exchanges')
def complete_return_request(return_id):
    """Complete a return request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Get user ID from auth context
        processor_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.complete_return_request(return_id, processor_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error completing return request: {str(e)}")

# ==================== Exchange Request Routes ====================

@returns_exchanges_bp.route('/exchange-requests', methods=['GET'])
@feature_required('returns_exchanges')
def get_exchange_requests():
    """Get all exchange requests with optional filters"""
    try:
        filters = {}
        for param in ['status', 'customer_id', 'return_request_id', 'date_from', 'date_to', 'search']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param in ['customer_id', 'return_request_id']:
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        exchange_requests = service.get_exchange_requests(filters)
        
        result = []
        for exchange_request in exchange_requests:
            result.append({
                'id': exchange_request.id,
                'exchange_number': exchange_request.exchange_number,
                'return_request_id': exchange_request.return_request_id,
                'original_order_id': exchange_request.original_order_id,
                'customer_id': exchange_request.customer_id,
                'customer_name': exchange_request.customer_name,
                'customer_email': exchange_request.customer_email,
                'customer_phone': exchange_request.customer_phone,
                'exchange_date': exchange_request.exchange_date.isoformat() if exchange_request.exchange_date else None,
                'status': exchange_request.status.value,
                'exchange_reason': exchange_request.exchange_reason.value,
                'exchange_reason_details': exchange_request.exchange_reason_details,
                'price_difference': float(exchange_request.price_difference) if exchange_request.price_difference else None,
                'additional_payment_required': float(exchange_request.additional_payment_required) if exchange_request.additional_payment_required else None,
                'refund_amount': float(exchange_request.refund_amount) if exchange_request.refund_amount else None,
                'tracking_number': exchange_request.tracking_number,
                'shipping_carrier': exchange_request.shipping_carrier,
                'notes': exchange_request.notes,
                'created_at': exchange_request.created_at.isoformat() if exchange_request.created_at else None,
                'updated_at': exchange_request.updated_at.isoformat() if exchange_request.updated_at else None,
                'is_approved': exchange_request.is_approved,
                'is_completed': exchange_request.is_completed
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving exchange requests: {str(e)}")

@returns_exchanges_bp.route('/exchange-requests/<int:exchange_id>', methods=['GET'])
@feature_required('returns_exchanges')
def get_exchange_request(exchange_id):
    """Get exchange request by ID with full details"""
    try:
        service = get_service()
        exchange_request = service.get_exchange_request_by_id(exchange_id)
        
        if not exchange_request:
            return handle_error("Exchange request not found", 404)
        
        # Get exchange items
        exchange_items = []
        for item in exchange_request.exchange_items:
            exchange_items.append({
                'id': item.id,
                'original_product_id': item.original_product_id,
                'original_product_name': item.original_product_name,
                'original_product_sku': item.original_product_sku,
                'original_variant_id': item.original_variant_id,
                'original_variant_name': item.original_variant_name,
                'original_variant_attributes': item.original_variant_attributes,
                'original_quantity': item.original_quantity,
                'original_unit_price': float(item.original_unit_price),
                'original_total_price': float(item.original_total_price),
                'exchange_product_id': item.exchange_product_id,
                'exchange_product_name': item.exchange_product_name,
                'exchange_product_sku': item.exchange_product_sku,
                'exchange_variant_id': item.exchange_variant_id,
                'exchange_variant_name': item.exchange_variant_name,
                'exchange_variant_attributes': item.exchange_variant_attributes,
                'exchange_quantity': item.exchange_quantity,
                'exchange_unit_price': float(item.exchange_unit_price),
                'exchange_total_price': float(item.exchange_total_price),
                'original_available': item.original_available,
                'exchange_available': item.exchange_available,
                'exchange_stock_quantity': item.exchange_stock_quantity,
                'exchange_reserved_quantity': item.exchange_reserved_quantity,
                'exchange_reason': item.exchange_reason,
                'item_notes': item.item_notes,
                'is_variant_exchange': item.is_variant_exchange(),
                'is_product_exchange': item.is_product_exchange(),
                'price_difference': float(item.calculate_price_difference())
            })
        
        result = {
            'id': exchange_request.id,
            'exchange_number': exchange_request.exchange_number,
            'return_request_id': exchange_request.return_request_id,
            'original_order_id': exchange_request.original_order_id,
            'customer_id': exchange_request.customer_id,
            'customer_name': exchange_request.customer_name,
            'customer_email': exchange_request.customer_email,
            'customer_phone': exchange_request.customer_phone,
            'exchange_date': exchange_request.exchange_date.isoformat() if exchange_request.exchange_date else None,
            'status': exchange_request.status.value,
            'exchange_reason': exchange_request.exchange_reason.value,
            'exchange_reason_details': exchange_request.exchange_reason_details,
            'approved_by': exchange_request.approved_by,
            'approved_at': exchange_request.approved_at.isoformat() if exchange_request.approved_at else None,
            'rejection_reason': exchange_request.rejection_reason,
            'processed_by': exchange_request.processed_by,
            'processed_at': exchange_request.processed_at.isoformat() if exchange_request.processed_at else None,
            'shipped_by': exchange_request.shipped_by,
            'shipped_at': exchange_request.shipped_at.isoformat() if exchange_request.shipped_at else None,
            'tracking_number': exchange_request.tracking_number,
            'shipping_carrier': exchange_request.shipping_carrier,
            'price_difference': float(exchange_request.price_difference) if exchange_request.price_difference else None,
            'additional_payment_required': float(exchange_request.additional_payment_required) if exchange_request.additional_payment_required else None,
            'refund_amount': float(exchange_request.refund_amount) if exchange_request.refund_amount else None,
            'payment_processed_at': exchange_request.payment_processed_at.isoformat() if exchange_request.payment_processed_at else None,
            'refund_processed_at': exchange_request.refund_processed_at.isoformat() if exchange_request.refund_processed_at else None,
            'notes': exchange_request.notes,
            'internal_notes': exchange_request.internal_notes,
            'customer_notes': exchange_request.customer_notes,
            'created_at': exchange_request.created_at.isoformat() if exchange_request.created_at else None,
            'updated_at': exchange_request.updated_at.isoformat() if exchange_request.updated_at else None,
            'exchange_items': exchange_items
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving exchange request: {str(e)}")

@returns_exchanges_bp.route('/exchange-requests', methods=['POST'])
@feature_required('returns_exchanges')
def create_exchange_request():
    """Create a new exchange request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['original_order_id', 'customer_id', 'customer_name', 'exchange_reason', 'exchange_items']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate exchange items
        if not data['exchange_items'] or len(data['exchange_items']) == 0:
            return handle_error("At least one exchange item is required")
        
        for item in data['exchange_items']:
            item_required_fields = [
                'original_product_id', 'original_product_name', 'original_quantity', 
                'original_unit_price', 'original_total_price',
                'exchange_product_id', 'exchange_product_name', 'exchange_quantity', 
                'exchange_unit_price', 'exchange_total_price'
            ]
            item_validation = validate_required_fields(item, item_required_fields)
            if item_validation:
                return handle_error(f"Exchange item validation error: {item_validation}")
        
        # Validate exchange date if provided
        if 'exchange_date' in data:
            try:
                datetime.strptime(data['exchange_date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid exchange date format. Use YYYY-MM-DD")
        
        # Validate exchange reason
        valid_reasons = [reason.value for reason in ReturnReason]
        if data['exchange_reason'] not in valid_reasons:
            return handle_error(f"Invalid exchange reason. Must be one of: {', '.join(valid_reasons)}")
        
        # Add tenant ID and user ID to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['user_id'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, exchange_request, message = service.create_exchange_request(data)
        
        if success:
            return success_response({
                'id': exchange_request.id,
                'exchange_number': exchange_request.exchange_number,
                'status': exchange_request.status.value,
                'price_difference': float(exchange_request.price_difference) if exchange_request.price_difference else None
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating exchange request: {str(e)}")

@returns_exchanges_bp.route('/exchange-requests/<int:exchange_id>/approve', methods=['POST'])
@feature_required('returns_exchanges')
def approve_exchange_request(exchange_id):
    """Approve an exchange request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Get user ID from auth context
        approver_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.approve_exchange_request(exchange_id, approver_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error approving exchange request: {str(e)}")

@returns_exchanges_bp.route('/exchange-requests/<int:exchange_id>/process', methods=['POST'])
@feature_required('returns_exchanges')
def process_exchange_request(exchange_id):
    """Process an exchange request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Get user ID from auth context
        processor_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.process_exchange_request(exchange_id, processor_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error processing exchange request: {str(e)}")

@returns_exchanges_bp.route('/exchange-requests/<int:exchange_id>/ship', methods=['POST'])
@feature_required('returns_exchanges')
def ship_exchange_request(exchange_id):
    """Ship an exchange request"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate shipping data
        if 'tracking_number' not in data or not data['tracking_number']:
            return handle_error("Tracking number is required")
        
        # Get user ID from auth context
        shipper_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, message = service.ship_exchange_request(exchange_id, shipper_id, data)
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error shipping exchange request: {str(e)}")

# ==================== Return Policy Routes ====================

@returns_exchanges_bp.route('/return-policies', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_policies():
    """Get all return policies with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'is_default', 'policy_type', 'search']:
            if param in request.args:
                if param in ['is_active', 'is_default']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        policies = service.get_return_policies(filters)
        
        result = []
        for policy in policies:
            result.append({
                'id': policy.id,
                'name': policy.name,
                'description': policy.description,
                'policy_type': policy.policy_type,
                'return_period_days': policy.return_period_days,
                'exchange_period_days': policy.exchange_period_days,
                'require_original_receipt': policy.require_original_receipt,
                'require_original_packaging': policy.require_original_packaging,
                'require_unused_condition': policy.require_unused_condition,
                'require_tags_attached': policy.require_tags_attached,
                'restocking_fee_percentage': float(policy.restocking_fee_percentage),
                'restocking_fee_fixed': float(policy.restocking_fee_fixed),
                'max_restocking_fee': float(policy.max_restocking_fee) if policy.max_restocking_fee else None,
                'allowed_refund_methods': policy.allowed_refund_methods,
                'default_refund_method': policy.default_refund_method.value if policy.default_refund_method else None,
                'store_credit_expiry_days': policy.store_credit_expiry_days,
                'applies_to_all_products': policy.applies_to_all_products,
                'product_ids': policy.product_ids,
                'category_ids': policy.category_ids,
                'excluded_product_ids': policy.excluded_product_ids,
                'excluded_category_ids': policy.excluded_category_ids,
                'holiday_return_extension': policy.holiday_return_extension,
                'defective_item_policy': policy.defective_item_policy,
                'damaged_item_policy': policy.damaged_item_policy,
                'is_active': policy.is_active,
                'is_default': policy.is_default,
                'created_at': policy.created_at.isoformat() if policy.created_at else None,
                'updated_at': policy.updated_at.isoformat() if policy.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return policies: {str(e)}")

@returns_exchanges_bp.route('/return-policies/<int:policy_id>', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_policy(policy_id):
    """Get return policy by ID"""
    try:
        service = get_service()
        policy = service.get_return_policy_by_id(policy_id)
        
        if not policy:
            return handle_error("Return policy not found", 404)
        
        result = {
            'id': policy.id,
            'name': policy.name,
            'description': policy.description,
            'policy_type': policy.policy_type,
            'return_period_days': policy.return_period_days,
            'exchange_period_days': policy.exchange_period_days,
            'require_original_receipt': policy.require_original_receipt,
            'require_original_packaging': policy.require_original_packaging,
            'require_unused_condition': policy.require_unused_condition,
            'require_tags_attached': policy.require_tags_attached,
            'restocking_fee_percentage': float(policy.restocking_fee_percentage),
            'restocking_fee_fixed': float(policy.restocking_fee_fixed),
            'max_restocking_fee': float(policy.max_restocking_fee) if policy.max_restocking_fee else None,
            'allowed_refund_methods': policy.allowed_refund_methods,
            'default_refund_method': policy.default_refund_method.value if policy.default_refund_method else None,
            'store_credit_expiry_days': policy.store_credit_expiry_days,
            'applies_to_all_products': policy.applies_to_all_products,
            'product_ids': policy.product_ids,
            'category_ids': policy.category_ids,
            'excluded_product_ids': policy.excluded_product_ids,
            'excluded_category_ids': policy.excluded_category_ids,
            'holiday_return_extension': policy.holiday_return_extension,
            'defective_item_policy': policy.defective_item_policy,
            'damaged_item_policy': policy.damaged_item_policy,
            'is_active': policy.is_active,
            'is_default': policy.is_default,
            'created_at': policy.created_at.isoformat() if policy.created_at else None,
            'updated_at': policy.updated_at.isoformat() if policy.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return policy: {str(e)}")

@returns_exchanges_bp.route('/return-policies/default', methods=['GET'])
@feature_required('returns_exchanges')
def get_default_return_policy():
    """Get default return policy"""
    try:
        service = get_service()
        policy = service.get_default_return_policy()
        
        if not policy:
            return handle_error("Default return policy not found", 404)
        
        result = {
            'id': policy.id,
            'name': policy.name,
            'description': policy.description,
            'policy_type': policy.policy_type,
            'return_period_days': policy.return_period_days,
            'exchange_period_days': policy.exchange_period_days,
            'require_original_receipt': policy.require_original_receipt,
            'require_original_packaging': policy.require_original_packaging,
            'require_unused_condition': policy.require_unused_condition,
            'require_tags_attached': policy.require_tags_attached,
            'restocking_fee_percentage': float(policy.restocking_fee_percentage),
            'restocking_fee_fixed': float(policy.restocking_fee_fixed),
            'max_restocking_fee': float(policy.max_restocking_fee) if policy.max_restocking_fee else None,
            'allowed_refund_methods': policy.allowed_refund_methods,
            'default_refund_method': policy.default_refund_method.value if policy.default_refund_method else None,
            'store_credit_expiry_days': policy.store_credit_expiry_days,
            'applies_to_all_products': policy.applies_to_all_products,
            'product_ids': policy.product_ids,
            'category_ids': policy.category_ids,
            'excluded_product_ids': policy.excluded_product_ids,
            'excluded_category_ids': policy.excluded_category_ids,
            'holiday_return_extension': policy.holiday_return_extension,
            'defective_item_policy': policy.defective_item_policy,
            'damaged_item_policy': policy.damaged_item_policy,
            'is_active': policy.is_active,
            'is_default': policy.is_default,
            'created_at': policy.created_at.isoformat() if policy.created_at else None,
            'updated_at': policy.updated_at.isoformat() if policy.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving default return policy: {str(e)}")

@returns_exchanges_bp.route('/return-policies', methods=['POST'])
@feature_required('returns_exchanges')
def create_return_policy():
    """Create a new return policy"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'policy_type']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate refund method if provided
        if 'default_refund_method' in data:
            valid_methods = [method.value for method in RefundMethod]
            if data['default_refund_method'] not in valid_methods:
                return handle_error(f"Invalid default refund method. Must be one of: {', '.join(valid_methods)}")
        
        # Add tenant ID and user ID to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, policy, message = service.create_return_policy(data)
        
        if success:
            return success_response({
                'id': policy.id,
                'name': policy.name,
                'policy_type': policy.policy_type
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating return policy: {str(e)}")

@returns_exchanges_bp.route('/return-policies/applicable', methods=['POST'])
@feature_required('returns_exchanges')
def get_applicable_return_policy():
    """Get applicable return policy for a product"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        if 'product_id' not in data:
            return handle_error("Product ID is required")
        
        product_id = data['product_id']
        category_ids = data.get('category_ids', [])
        
        service = get_service()
        policy = service.get_applicable_return_policy(product_id, category_ids)
        
        if not policy:
            return handle_error("No applicable return policy found", 404)
        
        result = {
            'id': policy.id,
            'name': policy.name,
            'description': policy.description,
            'policy_type': policy.policy_type,
            'return_period_days': policy.return_period_days,
            'exchange_period_days': policy.exchange_period_days,
            'require_original_receipt': policy.require_original_receipt,
            'require_original_packaging': policy.require_original_packaging,
            'require_unused_condition': policy.require_unused_condition,
            'require_tags_attached': policy.require_tags_attached,
            'restocking_fee_percentage': float(policy.restocking_fee_percentage),
            'restocking_fee_fixed': float(policy.restocking_fee_fixed),
            'max_restocking_fee': float(policy.max_restocking_fee) if policy.max_restocking_fee else None,
            'allowed_refund_methods': policy.allowed_refund_methods,
            'default_refund_method': policy.default_refund_method.value if policy.default_refund_method else None,
            'store_credit_expiry_days': policy.store_credit_expiry_days,
            'is_active': policy.is_active,
            'is_default': policy.is_default
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving applicable return policy: {str(e)}")

# ==================== Return Workflow Routes ====================

@returns_exchanges_bp.route('/return-workflows', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_workflows():
    """Get all return workflows with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'is_default', 'workflow_type', 'search']:
            if param in request.args:
                if param in ['is_active', 'is_default']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        workflows = service.get_return_workflows(filters)
        
        result = []
        for workflow in workflows:
            result.append({
                'id': workflow.id,
                'name': workflow.name,
                'description': workflow.description,
                'workflow_type': workflow.workflow_type,
                'trigger_conditions': workflow.trigger_conditions,
                'minimum_amount': float(workflow.minimum_amount) if workflow.minimum_amount else None,
                'maximum_amount': float(workflow.maximum_amount) if workflow.maximum_amount else None,
                'required_reasons': workflow.required_reasons,
                'required_products': workflow.required_products,
                'required_categories': workflow.required_categories,
                'approval_steps': workflow.approval_steps,
                'auto_approve_conditions': workflow.auto_approve_conditions,
                'auto_reject_conditions': workflow.auto_reject_conditions,
                'notification_settings': workflow.notification_settings,
                'customer_notifications': workflow.customer_notifications,
                'is_active': workflow.is_active,
                'is_default': workflow.is_default,
                'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
                'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return workflows: {str(e)}")

@returns_exchanges_bp.route('/return-workflows/<int:workflow_id>', methods=['GET'])
@feature_required('returns_exchanges')
def get_return_workflow(workflow_id):
    """Get return workflow by ID"""
    try:
        service = get_service()
        workflow = service.get_return_workflow_by_id(workflow_id)
        
        if not workflow:
            return handle_error("Return workflow not found", 404)
        
        result = {
            'id': workflow.id,
            'name': workflow.name,
            'description': workflow.description,
            'workflow_type': workflow.workflow_type,
            'trigger_conditions': workflow.trigger_conditions,
            'minimum_amount': float(workflow.minimum_amount) if workflow.minimum_amount else None,
            'maximum_amount': float(workflow.maximum_amount) if workflow.maximum_amount else None,
            'required_reasons': workflow.required_reasons,
            'required_products': workflow.required_products,
            'required_categories': workflow.required_categories,
            'approval_steps': workflow.approval_steps,
            'auto_approve_conditions': workflow.auto_approve_conditions,
            'auto_reject_conditions': workflow.auto_reject_conditions,
            'notification_settings': workflow.notification_settings,
            'customer_notifications': workflow.customer_notifications,
            'is_active': workflow.is_active,
            'is_default': workflow.is_default,
            'created_at': workflow.created_at.isoformat() if workflow.created_at else None,
            'updated_at': workflow.updated_at.isoformat() if workflow.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving return workflow: {str(e)}")

# ==================== Analytics Routes ====================

@returns_exchanges_bp.route('/analytics', methods=['GET'])
@feature_required('returns_exchanges')
def get_returns_analytics():
    """Get returns analytics for a date range"""
    try:
        # Parse date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        service = get_service()
        analytics = service.get_returns_analytics(start_date, end_date)
        
        return success_response(analytics)
        
    except ValueError:
        return handle_error("Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        return handle_error(f"Error retrieving returns analytics: {str(e)}")

# ==================== Error Handlers ====================

@returns_exchanges_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@returns_exchanges_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500