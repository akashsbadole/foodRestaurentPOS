"""
Specialized Retail routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.specialized_retail_service import create_specialized_retail_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.specialized_retail import (
    CustomProduct, CustomAttribute, CustomAttributeValue, ServiceBooking,
    RepairRecord, WarrantyClaim, RentalItem, ConsignmentItem
)
from models import db
from datetime import datetime, date
import json

# Create blueprint
specialized_retail_bp = Blueprint('specialized_retail', __name__, url_prefix='/specialized')

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

# Custom Product Routes

@specialized_retail_bp.route('/api/custom-products', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def get_custom_products():
    """Get custom products with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('specialized_category'):
            filters['specialized_category'] = request.args.get('specialized_category')
        if request.args.get('brand'):
            filters['brand'] = request.args.get('brand')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_featured'):
            filters['is_featured'] = request.args.get('is_featured').lower() == 'true'
        if request.args.get('is_on_sale'):
            filters['is_on_sale'] = request.args.get('is_on_sale').lower() == 'true'
        if request.args.get('min_price'):
            filters['min_price'] = float(request.args.get('min_price'))
        if request.args.get('max_price'):
            filters['max_price'] = float(request.args.get('max_price'))
        if request.args.get('low_stock'):
            filters['low_stock'] = request.args.get('low_stock').lower() == 'true'
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        products = service.get_custom_products(filters)
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting custom products: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-products', methods=['POST'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def create_custom_product():
    """Create a new custom product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, product, message = service.create_custom_product(data)
        if success:
            return jsonify({
                'success': True,
                'data': product.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating custom product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-products/<int:product_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def get_custom_product(product_id):
    """Get custom product by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        product = service.get_custom_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting custom product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-products/<int:product_id>', methods=['PUT'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def update_custom_product(product_id):
    """Update an existing custom product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, product, message = service.update_custom_product(product_id, data)
        if success:
            return jsonify({
                'success': True,
                'data': product.to_dict(),
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating custom product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-products/<int:product_id>', methods=['DELETE'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def delete_custom_product(product_id):
    """Delete a custom product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        success, message = service.delete_custom_product(product_id)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error deleting custom product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-products/sku/<sku>', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def get_custom_product_by_sku(sku):
    """Get custom product by SKU"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        product = service.get_custom_product_by_sku(sku)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting custom product by SKU: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Custom Attribute Routes

@specialized_retail_bp.route('/api/custom-attributes', methods=['GET'])
@require_auth
@feature_required('FEATURE_CUSTOM_ATTRIBUTES')
def get_custom_attributes():
    """Get custom attributes with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('attribute_type'):
            filters['attribute_type'] = request.args.get('attribute_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('show_in_filters'):
            filters['show_in_filters'] = request.args.get('show_in_filters').lower() == 'true'
        
        attributes = service.get_custom_attributes(filters)
        return jsonify({
            'success': True,
            'data': [attribute.to_dict() for attribute in attributes],
            'count': len(attributes)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting custom attributes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-attributes', methods=['POST'])
@require_auth
@feature_required('FEATURE_CUSTOM_ATTRIBUTES')
def create_custom_attribute():
    """Create a new custom attribute"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, attribute, message = service.create_custom_attribute(data)
        if success:
            return jsonify({
                'success': True,
                'data': attribute.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating custom attribute: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-attributes/<int:attribute_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_CUSTOM_ATTRIBUTES')
def get_custom_attribute(attribute_id):
    """Get custom attribute by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        attribute = service.get_custom_attribute_by_id(attribute_id)
        if not attribute:
            return jsonify({'success': False, 'message': 'Attribute not found'}), 404
        
        return jsonify({
            'success': True,
            'data': attribute.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting custom attribute: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/custom-attributes/<int:attribute_id>', methods=['PUT'])
@require_auth
@feature_required('FEATURE_CUSTOM_ATTRIBUTES')
def update_custom_attribute(attribute_id):
    """Update an existing custom attribute"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, attribute, message = service.update_custom_attribute(attribute_id, data)
        if success:
            return jsonify({
                'success': True,
                'data': attribute.to_dict(),
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating custom attribute: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Service Booking Routes

@specialized_retail_bp.route('/api/service-bookings', methods=['GET'])
@require_auth
@feature_required('FEATURE_SERVICE_BOOKING')
def get_service_bookings():
    """Get service bookings with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('service_type'):
            filters['service_type'] = request.args.get('service_type')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('technician_id'):
            filters['technician_id'] = int(request.args.get('technician_id'))
        if request.args.get('service_location'):
            filters['service_location'] = request.args.get('service_location')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('overdue'):
            filters['overdue'] = request.args.get('overdue').lower() == 'true'
        
        bookings = service.get_service_bookings(filters)
        return jsonify({
            'success': True,
            'data': [booking.to_dict() for booking in bookings],
            'count': len(bookings)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting service bookings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/service-bookings', methods=['POST'])
@require_auth
@feature_required('FEATURE_SERVICE_BOOKING')
def create_service_booking():
    """Create a new service booking"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, booking, message = service.create_service_booking(data)
        if success:
            return jsonify({
                'success': True,
                'data': booking.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating service booking: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/service-bookings/<int:booking_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_SERVICE_BOOKING')
def get_service_booking(booking_id):
    """Get service booking by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        booking = service.get_service_booking_by_id(booking_id)
        if not booking:
            return jsonify({'success': False, 'message': 'Service booking not found'}), 404
        
        return jsonify({
            'success': True,
            'data': booking.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting service booking: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/service-bookings/<int:booking_id>', methods=['PUT'])
@require_auth
@feature_required('FEATURE_SERVICE_BOOKING')
def update_service_booking(booking_id):
    """Update an existing service booking"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, booking, message = service.update_service_booking(booking_id, data)
        if success:
            return jsonify({
                'success': True,
                'data': booking.to_dict(),
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating service booking: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Repair Record Routes

@specialized_retail_bp.route('/api/repair-records', methods=['GET'])
@require_auth
@feature_required('FEATURE_REPAIR_TRACKING')
def get_repair_records():
    """Get repair records with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('repair_type'):
            filters['repair_type'] = request.args.get('repair_type')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('technician_id'):
            filters['technician_id'] = int(request.args.get('technician_id'))
        if request.args.get('is_warranty_repair'):
            filters['is_warranty_repair'] = request.args.get('is_warranty_repair').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('overdue'):
            filters['overdue'] = request.args.get('overdue').lower() == 'true'
        
        records = service.get_repair_records(filters)
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in records],
            'count': len(records)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting repair records: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/repair-records', methods=['POST'])
@require_auth
@feature_required('FEATURE_REPAIR_TRACKING')
def create_repair_record():
    """Create a new repair record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, record, message = service.create_repair_record(data)
        if success:
            return jsonify({
                'success': True,
                'data': record.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating repair record: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/repair-records/<int:repair_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_REPAIR_TRACKING')
def get_repair_record(repair_id):
    """Get repair record by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        record = service.get_repair_record_by_id(repair_id)
        if not record:
            return jsonify({'success': False, 'message': 'Repair record not found'}), 404
        
        return jsonify({
            'success': True,
            'data': record.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting repair record: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Warranty Claim Routes

@specialized_retail_bp.route('/api/warranty-claims', methods=['GET'])
@require_auth
@feature_required('FEATURE_WARRANTY_TRACKING')
def get_warranty_claims():
    """Get warranty claims with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('claim_type'):
            filters['claim_type'] = request.args.get('claim_type')
        if request.args.get('claim_status'):
            filters['claim_status'] = request.args.get('claim_status')
        if request.args.get('warranty_valid'):
            filters['warranty_valid'] = request.args.get('warranty_valid').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        claims = service.get_warranty_claims(filters)
        return jsonify({
            'success': True,
            'data': [claim.to_dict() for claim in claims],
            'count': len(claims)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting warranty claims: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/warranty-claims', methods=['POST'])
@require_auth
@feature_required('FEATURE_WARRANTY_TRACKING')
def create_warranty_claim():
    """Create a new warranty claim"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, claim, message = service.create_warranty_claim(data)
        if success:
            return jsonify({
                'success': True,
                'data': claim.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating warranty claim: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/warranty-claims/<int:claim_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_WARRANTY_TRACKING')
def get_warranty_claim(claim_id):
    """Get warranty claim by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        claim = service.get_warranty_claim_by_id(claim_id)
        if not claim:
            return jsonify({'success': False, 'message': 'Warranty claim not found'}), 404
        
        return jsonify({
            'success': True,
            'data': claim.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting warranty claim: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Rental Item Routes

@specialized_retail_bp.route('/api/rental-items', methods=['GET'])
@require_auth
@feature_required('FEATURE_RENTAL_MANAGEMENT')
def get_rental_items():
    """Get rental items with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('payment_status'):
            filters['payment_status'] = request.args.get('payment_status')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('overdue'):
            filters['overdue'] = request.args.get('overdue').lower() == 'true'
        
        items = service.get_rental_items(filters)
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting rental items: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/rental-items', methods=['POST'])
@require_auth
@feature_required('FEATURE_RENTAL_MANAGEMENT')
def create_rental_item():
    """Create a new rental item"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, item, message = service.create_rental_item(data)
        if success:
            return jsonify({
                'success': True,
                'data': item.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating rental item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/rental-items/<int:rental_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_RENTAL_MANAGEMENT')
def get_rental_item(rental_id):
    """Get rental item by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        item = service.get_rental_item_by_id(rental_id)
        if not item:
            return jsonify({'success': False, 'message': 'Rental item not found'}), 404
        
        return jsonify({
            'success': True,
            'data': item.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting rental item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Consignment Item Routes

@specialized_retail_bp.route('/api/consignment-items', methods=['GET'])
@require_auth
@feature_required('FEATURE_CONSIGNMENT_MANAGEMENT')
def get_consignment_items():
    """Get consignment items with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('consignor_id'):
            filters['consignor_id'] = int(request.args.get('consignor_id'))
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('payment_status'):
            filters['payment_status'] = request.args.get('payment_status')
        if request.args.get('item_condition'):
            filters['item_condition'] = request.args.get('item_condition')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('expired'):
            filters['expired'] = request.args.get('expired').lower() == 'true'
        
        items = service.get_consignment_items(filters)
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting consignment items: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/consignment-items', methods=['POST'])
@require_auth
@feature_required('FEATURE_CONSIGNMENT_MANAGEMENT')
def create_consignment_item():
    """Create a new consignment item"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, item, message = service.create_consignment_item(data)
        if success:
            return jsonify({
                'success': True,
                'data': item.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating consignment item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@specialized_retail_bp.route('/api/consignment-items/<int:consignment_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_CONSIGNMENT_MANAGEMENT')
def get_consignment_item(consignment_id):
    """Get consignment item by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        item = service.get_consignment_item_by_id(consignment_id)
        if not item:
            return jsonify({'success': False, 'message': 'Consignment item not found'}), 404
        
        return jsonify({
            'success': True,
            'data': item.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting consignment item: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Analytics Routes

@specialized_retail_bp.route('/api/analytics/specialized-retail', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_ANALYTICS')
def get_specialized_retail_analytics():
    """Get specialized retail analytics"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_specialized_retail_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        analytics = service.get_specialized_retail_analytics(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error generating specialized retail analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@specialized_retail_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIALIZED_PRODUCTS')
def get_specialized_retail_config():
    """Get specialized retail configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'specialized_products': feature_manager.is_enabled('FEATURE_SPECIALIZED_PRODUCTS', tenant_id),
                'custom_attributes': feature_manager.is_enabled('FEATURE_CUSTOM_ATTRIBUTES', tenant_id),
                'service_booking': feature_manager.is_enabled('FEATURE_SERVICE_BOOKING', tenant_id),
                'repair_tracking': feature_manager.is_enabled('FEATURE_REPAIR_TRACKING', tenant_id),
                'warranty_tracking': feature_manager.is_enabled('FEATURE_WARRANTY_TRACKING', tenant_id),
                'rental_management': feature_manager.is_enabled('FEATURE_RENTAL_MANAGEMENT', tenant_id),
                'consignment_management': feature_manager.is_enabled('FEATURE_CONSIGNMENT_MANAGEMENT', tenant_id),
                'specialized_analytics': feature_manager.is_enabled('FEATURE_SPECIALIZED_ANALYTICS', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'specialized_products_enabled': True,
                'custom_attributes_enabled': True,
                'service_booking_enabled': True,
                'repair_tracking_enabled': True,
                'warranty_tracking_enabled': True,
                'rental_management_enabled': True,
                'consignment_management_enabled': True,
                'default_warranty_period_months': 12,
                'default_service_interval_months': 6,
                'default_late_fee_per_day': 10.00,
                'default_grace_period_days': 3,
                'default_commission_rate': 20.0,
                'default_consignment_period_days': 90
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting specialized retail config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500