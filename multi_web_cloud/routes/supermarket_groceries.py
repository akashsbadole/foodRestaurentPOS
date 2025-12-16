"""
Supermarket & Groceries routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.supermarket_groceries_service import create_supermarket_groceries_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.supermarket_groceries import (
    FreshProduce, FreshProduceInventory, FreshProducePriceUpdate, FreshProduceQualityCheck,
    WeighingScaleIntegration, ComboOffer, ShelfLifeManagement, FreshCounter
)
from models import db
from datetime import datetime, date
import json

# Create blueprint
supermarket_groceries_bp = Blueprint('supermarket_groceries', __name__, url_prefix='/supermarket')

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

# Fresh Produce Routes

@supermarket_groceries_bp.route('/api/fresh-produce', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_PRODUCE')
def get_fresh_produce():
    """Get fresh produce with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('produce_category'):
            filters['produce_category'] = request.args.get('produce_category')
        if request.args.get('variety'):
            filters['variety'] = request.args.get('variety')
        if request.args.get('origin'):
            filters['origin'] = request.args.get('origin')
        if request.args.get('grade'):
            filters['grade'] = request.args.get('grade')
        if request.args.get('certification'):
            filters['certification'] = request.args.get('certification')
        if request.args.get('is_seasonal'):
            filters['is_seasonal'] = request.args.get('is_seasonal').lower() == 'true'
        if request.args.get('is_on_promotion'):
            filters['is_on_promotion'] = request.args.get('is_on_promotion').lower() == 'true'
        if request.args.get('min_quality_score'):
            filters['min_quality_score'] = int(request.args.get('min_quality_score'))
        if request.args.get('max_quality_score'):
            filters['max_quality_score'] = int(request.args.get('max_quality_score'))
        if request.args.get('in_stock'):
            filters['in_stock'] = request.args.get('in_stock').lower() == 'true'
        
        produce = service.get_fresh_produce(filters)
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in produce],
            'count': len(produce)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting fresh produce: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-produce', methods=['POST'])
@require_auth
@feature_required('FEATURE_FRESH_PRODUCE')
def create_fresh_produce():
    """Create a new fresh produce item"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, produce, message = service.create_fresh_produce(data)
        if success:
            return jsonify({
                'success': True,
                'data': produce.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating fresh produce: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-produce/sku/<sku>', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_PRODUCE')
def get_produce_by_sku(sku):
    """Get produce by SKU"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        produce = service.get_produce_by_sku(sku)
        if not produce:
            return jsonify({'success': False, 'message': 'Produce not found'}), 404
        
        return jsonify({
            'success': True,
            'data': produce.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting produce by SKU: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Fresh Produce Inventory Routes

@supermarket_groceries_bp.route('/api/fresh-produce/inventory', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_INVENTORY')
def get_fresh_produce_inventory():
    """Get fresh produce inventory with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('produce_id'):
            filters['produce_id'] = int(request.args.get('produce_id'))
        if request.args.get('batch_number'):
            filters['batch_number'] = request.args.get('batch_number')
        if request.args.get('quality_grade'):
            filters['quality_grade'] = request.args.get('quality_grade')
        if request.args.get('storage_location'):
            filters['storage_location'] = request.args.get('storage_location')
        if request.args.get('display_area'):
            filters['display_area'] = request.args.get('display_area')
        if request.args.get('near_expiry'):
            filters['near_expiry'] = request.args.get('near_expiry').lower() == 'true'
        if request.args.get('low_stock'):
            filters['low_stock'] = request.args.get('low_stock').lower() == 'true'
        
        inventory = service.get_produce_inventory(filters)
        return jsonify({
            'success': True,
            'data': [item.to_dict() for item in inventory],
            'count': len(inventory)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting fresh produce inventory: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-produce/inventory', methods=['POST'])
@require_auth
@feature_required('FEATURE_FRESH_INVENTORY')
def create_fresh_produce_inventory():
    """Create a new fresh produce inventory record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, inventory, message = service.create_fresh_produce_inventory(data)
        if success:
            return jsonify({
                'success': True,
                'data': inventory.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating fresh produce inventory: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Price Update Routes

@supermarket_groceries_bp.route('/api/fresh-produce/price-updates', methods=['GET'])
@require_auth
@feature_required('FEATURE_PRICE_MANAGEMENT')
def get_price_updates():
    """Get price updates with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('produce_id'):
            filters['produce_id'] = int(request.args.get('produce_id'))
        if request.args.get('change_reason'):
            filters['change_reason'] = request.args.get('change_reason')
        if request.args.get('supplier_price_change'):
            filters['supplier_price_change'] = request.args.get('supplier_price_change').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        updates = service.get_price_updates(filters)
        return jsonify({
            'success': True,
            'data': [update.to_dict() for update in updates],
            'count': len(updates)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting price updates: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-produce/price-updates', methods=['POST'])
@require_auth
@feature_required('FEATURE_PRICE_MANAGEMENT')
def create_price_update():
    """Create a new price update record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, update, message = service.create_price_update(data)
        if success:
            return jsonify({
                'success': True,
                'data': update.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating price update: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Quality Check Routes

@supermarket_groceries_bp.route('/api/fresh-produce/quality-checks', methods=['GET'])
@require_auth
@feature_required('FEATURE_QUALITY_MANAGEMENT')
def get_quality_checks():
    """Get quality checks with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('produce_id'):
            filters['produce_id'] = int(request.args.get('produce_id'))
        if request.args.get('batch_number'):
            filters['batch_number'] = request.args.get('batch_number')
        if request.args.get('inspector_name'):
            filters['inspector_name'] = request.args.get('inspector_name')
        if request.args.get('grade_assigned'):
            filters['grade_assigned'] = request.args.get('grade_assigned')
        if request.args.get('passed_inspection'):
            filters['passed_inspection'] = request.args.get('passed_inspection').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        checks = service.get_quality_checks(filters)
        return jsonify({
            'success': True,
            'data': [check.to_dict() for check in checks],
            'count': len(checks)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting quality checks: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-produce/quality-checks', methods=['POST'])
@require_auth
@feature_required('FEATURE_QUALITY_MANAGEMENT')
def create_quality_check():
    """Create a new quality check record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, check, message = service.create_quality_check(data)
        if success:
            return jsonify({
                'success': True,
                'data': check.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating quality check: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Weighing Scale Integration Routes

@supermarket_groceries_bp.route('/api/weighing-scales', methods=['GET'])
@require_auth
@feature_required('FEATURE_WEIGHING_SCALE')
def get_weighing_scales():
    """Get weighing scales with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('department'):
            filters['department'] = request.args.get('department')
        if request.args.get('connection_type'):
            filters['connection_type'] = request.args.get('connection_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_connected'):
            filters['is_connected'] = request.args.get('is_connected').lower() == 'true'
        if request.args.get('calibration_due'):
            filters['calibration_due'] = request.args.get('calibration_due').lower() == 'true'
        
        scales = service.get_weighing_scales(filters)
        return jsonify({
            'success': True,
            'data': [scale.to_dict() for scale in scales],
            'count': len(scales)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting weighing scales: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/weighing-scales', methods=['POST'])
@require_auth
@feature_required('FEATURE_WEIGHING_SCALE')
def create_weighing_scale():
    """Create a new weighing scale integration"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, scale, message = service.create_weighing_scale(data)
        if success:
            return jsonify({
                'success': True,
                'data': scale.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating weighing scale: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Combo Offer Routes

@supermarket_groceries_bp.route('/api/combo-offers', methods=['GET'])
@require_auth
@feature_required('FEATURE_COMBO_OFFERS')
def get_combo_offers():
    """Get combo offers with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('combo_type'):
            filters['combo_type'] = request.args.get('combo_type')
        if request.args.get('discount_type'):
            filters['discount_type'] = request.args.get('discount_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('valid_only'):
            filters['valid_only'] = request.args.get('valid_only').lower() == 'true'
        if request.args.get('applicable_categories'):
            filters['applicable_categories'] = request.args.get('applicable_categories').split(',')
        
        offers = service.get_combo_offers(filters)
        return jsonify({
            'success': True,
            'data': [offer.to_dict() for offer in offers],
            'count': len(offers)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting combo offers: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/combo-offers', methods=['POST'])
@require_auth
@feature_required('FEATURE_COMBO_OFFERS')
def create_combo_offer():
    """Create a new combo offer"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, offer, message = service.create_combo_offer(data)
        if success:
            return jsonify({
                'success': True,
                'data': offer.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating combo offer: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/combo-offers/<int:combo_id>/use', methods=['POST'])
@require_auth
@feature_required('FEATURE_COMBO_OFFERS')
def use_combo_offer(combo_id):
    """Use a combo offer and increment usage count"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        success, message = service.use_combo_offer(combo_id)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error using combo offer: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Shelf Life Management Routes

@supermarket_groceries_bp.route('/api/shelf-life-management', methods=['GET'])
@require_auth
@feature_required('FEATURE_SHELF_LIFE_MANAGEMENT')
def get_shelf_life_management():
    """Get shelf life management records with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = request.args.get('product_id')
        if request.args.get('batch_number'):
            filters['batch_number'] = request.args.get('batch_number')
        if request.args.get('requires_action'):
            filters['requires_action'] = request.args.get('requires_action').lower() == 'true'
        if request.args.get('action_taken'):
            filters['action_taken'] = request.args.get('action_taken')
        if request.args.get('disposal_method'):
            filters['disposal_method'] = request.args.get('disposal_method')
        if request.args.get('near_expiry'):
            filters['near_expiry'] = request.args.get('near_expiry').lower() == 'true'
        
        records = service.get_shelf_life_management(filters)
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in records],
            'count': len(records)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting shelf life management: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/shelf-life-management', methods=['POST'])
@require_auth
@feature_required('FEATURE_SHELF_LIFE_MANAGEMENT')
def create_shelf_life_management():
    """Create a new shelf life management record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, record, message = service.create_shelf_life_management(data)
        if success:
            return jsonify({
                'success': True,
                'data': record.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating shelf life management: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Fresh Counter Routes

@supermarket_groceries_bp.route('/api/fresh-counters', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_COUNTERS')
def get_fresh_counters():
    """Get fresh counters with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('counter_type'):
            filters['counter_type'] = request.args.get('counter_type')
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('department'):
            filters['department'] = request.args.get('department')
        if request.args.get('section'):
            filters['section'] = request.args.get('section')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        
        counters = service.get_fresh_counters(filters)
        return jsonify({
            'success': True,
            'data': [counter.to_dict() for counter in counters],
            'count': len(counters)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting fresh counters: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/fresh-counters', methods=['POST'])
@require_auth
@feature_required('FEATURE_FRESH_COUNTERS')
def create_fresh_counter():
    """Create a new fresh counter"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, counter, message = service.create_fresh_counter(data)
        if success:
            return jsonify({
                'success': True,
                'data': counter.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating fresh counter: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Analytics and Reporting Routes

@supermarket_groceries_bp.route('/api/analytics/fresh-produce', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_ANALYTICS')
def get_fresh_produce_analytics():
    """Get fresh produce analytics"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        analytics = service.get_fresh_produce_analytics(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error generating fresh produce analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@supermarket_groceries_bp.route('/api/analytics/inventory-turnover', methods=['GET'])
@require_auth
@feature_required('FEATURE_INVENTORY_ANALYTICS')
def get_inventory_turnover_report():
    """Get inventory turnover report"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_supermarket_groceries_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        report = service.get_inventory_turnover_report(start_date, end_date)
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        current_app.logger.error(f"Error generating inventory turnover report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@supermarket_groceries_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_FRESH_PRODUCE')
def get_supermarket_config():
    """Get supermarket & groceries configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'fresh_produce': feature_manager.is_enabled('FEATURE_FRESH_PRODUCE', tenant_id),
                'fresh_inventory': feature_manager.is_enabled('FEATURE_FRESH_INVENTORY', tenant_id),
                'price_management': feature_manager.is_enabled('FEATURE_PRICE_MANAGEMENT', tenant_id),
                'quality_management': feature_manager.is_enabled('FEATURE_QUALITY_MANAGEMENT', tenant_id),
                'weighing_scale': feature_manager.is_enabled('FEATURE_WEIGHING_SCALE', tenant_id),
                'combo_offers': feature_manager.is_enabled('FEATURE_COMBO_OFFERS', tenant_id),
                'shelf_life_management': feature_manager.is_enabled('FEATURE_SHELF_LIFE_MANAGEMENT', tenant_id),
                'fresh_counters': feature_manager.is_enabled('FEATURE_FRESH_COUNTERS', tenant_id),
                'fresh_analytics': feature_manager.is_enabled('FEATURE_FRESH_ANALYTICS', tenant_id),
                'inventory_analytics': feature_manager.is_enabled('FEATURE_INVENTORY_ANALYTICS', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'fresh_produce_enabled': True,
                'quality_tracking_enabled': True,
                'price_by_weight_enabled': True,
                'shelf_life_tracking_enabled': True,
                'combo_offers_enabled': True,
                'fresh_counter_management': True,
                'weighing_scale_integration': False,
                'default_quality_score': 5,
                'expiry_warning_days': 3,
                'expiry_critical_days': 1
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting supermarket config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500