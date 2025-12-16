"""
Food & Confectionery routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.food_confectionery_service import create_food_confectionery_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.food_confectionery import (
    FoodProduct, FoodBatch, TemperatureLog, Recipe, RecipeItem, 
    FoodWastage, WeighingScaleIntegration
)
from models import db
from datetime import datetime, date
import json

# Create blueprint
food_confectionery_bp = Blueprint('food_confectionery', __name__, url_prefix='/food-confectionery')

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

# Food Product Routes

@food_confectionery_bp.route('/api/products', methods=['GET'])
@require_auth
@feature_required('FEATURE_FOOD_MANAGEMENT')
def get_food_products():
    """Get food products with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('food_category'):
            filters['food_category'] = request.args.get('food_category')
        if request.args.get('brand'):
            filters['brand'] = request.args.get('brand')
        if request.args.get('temperature_sensitive'):
            filters['temperature_sensitive'] = request.args.get('temperature_sensitive').lower() == 'true'
        if request.args.get('requires_batch_tracking'):
            filters['requires_batch_tracking'] = request.args.get('requires_batch_tracking').lower() == 'true'
        if request.args.get('sold_by_weight'):
            filters['sold_by_weight'] = request.args.get('sold_by_weight').lower() == 'true'
        if request.args.get('min_price'):
            filters['min_price'] = request.args.get('min_price')
        if request.args.get('max_price'):
            filters['max_price'] = request.args.get('max_price')
        if request.args.get('is_seasonal'):
            filters['is_seasonal'] = request.args.get('is_seasonal').lower() == 'true'
        
        products = service.get_food_products(filters)
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products],
            'count': len(products)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting food products: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/products', methods=['POST'])
@require_auth
@feature_required('FEATURE_FOOD_MANAGEMENT')
def create_food_product():
    """Create a new food product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, product, message = service.create_food_product(data)
        if success:
            return jsonify({
                'success': True,
                'data': product.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating food product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/products/<int:product_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_FOOD_MANAGEMENT')
def get_food_product(product_id):
    """Get a specific food product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        product = service.get_food_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        # Include expiry status
        product_dict = product.to_dict()
        product_dict['expiry_status'] = product.get_expiry_status()
        
        return jsonify({
            'success': True,
            'data': product_dict
        })
    except Exception as e:
        current_app.logger.error(f"Error getting food product: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/products/sku/<sku>', methods=['GET'])
@require_auth
@feature_required('FEATURE_FOOD_MANAGEMENT')
def get_food_product_by_sku(sku):
    """Get a food product by SKU"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        product = service.get_food_product_by_sku(sku)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting food product by SKU: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Batch Management Routes

@food_confectionery_bp.route('/api/batches', methods=['GET'])
@require_auth
@feature_required('FEATURE_BATCH_TRACKING')
def get_batches():
    """Get batches with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Parse filters from query parameters
        product_id = request.args.get('product_id', type=int)
        include_expired = request.args.get('include_expired', 'false').lower() == 'true'
        
        if not product_id:
            return jsonify({'success': False, 'message': 'Product ID is required'}), 400
        
        service = create_food_confectionery_service(tenant_id)
        batches = service.get_product_batches(product_id, include_expired)
        
        return jsonify({
            'success': True,
            'data': [batch.to_dict() for batch in batches],
            'count': len(batches)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting batches: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/batches', methods=['POST'])
@require_auth
@feature_required('FEATURE_BATCH_TRACKING')
def create_batch():
    """Create a new batch"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, batch, message = service.create_food_batch(data)
        if success:
            return jsonify({
                'success': True,
                'data': batch.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating batch: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/batches/expiring', methods=['GET'])
@require_auth
@feature_required('FEATURE_BATCH_TRACKING')
def get_expiring_batches():
    """Get batches expiring soon"""
    try:
        tenant_id = get_current_tenant_id()
        days_threshold = request.args.get('days_threshold', 7, type=int)
        
        service = create_food_confectionery_service(tenant_id)
        batches = service.get_expiring_batches(days_threshold)
        
        return jsonify({
            'success': True,
            'data': [batch.to_dict() for batch in batches],
            'count': len(batches),
            'days_threshold': days_threshold
        })
    except Exception as e:
        current_app.logger.error(f"Error getting expiring batches: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/batches/expired', methods=['GET'])
@require_auth
@feature_required('FEATURE_BATCH_TRACKING')
def get_expired_batches():
    """Get expired batches"""
    try:
        tenant_id = get_current_tenant_id()
        
        service = create_food_confectionery_service(tenant_id)
        batches = service.get_expired_batches()
        
        return jsonify({
            'success': True,
            'data': [batch.to_dict() for batch in batches],
            'count': len(batches)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting expired batches: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Temperature Logging Routes

@food_confectionery_bp.route('/api/temperature-logs', methods=['GET'])
@require_auth
@feature_required('FEATURE_TEMPERATURE_LOGGING')
def get_temperature_logs():
    """Get temperature logs with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('batch_id'):
            filters['batch_id'] = int(request.args.get('batch_id'))
        if request.args.get('reading_location'):
            filters['reading_location'] = request.args.get('reading_location')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('out_of_range_only'):
            filters['out_of_range_only'] = request.args.get('out_of_range_only').lower() == 'true'
        
        logs = service.get_temperature_logs(filters)
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in logs],
            'count': len(logs)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting temperature logs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/temperature-logs', methods=['POST'])
@require_auth
@feature_required('FEATURE_TEMPERATURE_LOGGING')
def create_temperature_log():
    """Create a new temperature log"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, log, message = service.create_temperature_log(data)
        if success:
            return jsonify({
                'success': True,
                'data': log.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating temperature log: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Recipe Management Routes

@food_confectionery_bp.route('/api/recipes', methods=['GET'])
@require_auth
@feature_required('FEATURE_RECIPE_MANAGEMENT')
def get_recipes():
    """Get recipes with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args.get('category')
        if request.args.get('cuisine_type'):
            filters['cuisine_type'] = request.args.get('cuisine_type')
        if request.args.get('difficulty_level'):
            filters['difficulty_level'] = request.args.get('difficulty_level')
        if request.args.get('is_standardized'):
            filters['is_standardized'] = request.args.get('is_standardized').lower() == 'true'
        
        recipes = service.get_recipes(filters)
        return jsonify({
            'success': True,
            'data': [recipe.to_dict() for recipe in recipes],
            'count': len(recipes)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting recipes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/recipes', methods=['POST'])
@require_auth
@feature_required('FEATURE_RECIPE_MANAGEMENT')
def create_recipe():
    """Create a new recipe"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, recipe, message = service.create_recipe(data)
        if success:
            return jsonify({
                'success': True,
                'data': recipe.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating recipe: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/recipes/<recipe_code>', methods=['GET'])
@require_auth
@feature_required('FEATURE_RECIPE_MANAGEMENT')
def get_recipe_by_code(recipe_code):
    """Get a recipe by code"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        recipe = service.get_recipe_by_code(recipe_code)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404
        
        return jsonify({
            'success': True,
            'data': recipe.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting recipe by code: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Wastage Management Routes

@food_confectionery_bp.route('/api/wastage', methods=['GET'])
@require_auth
@feature_required('FEATURE_WASTAGE_TRACKING')
def get_wastage_records():
    """Get wastage records with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('product_id'):
            filters['product_id'] = int(request.args.get('product_id'))
        if request.args.get('batch_id'):
            filters['batch_id'] = int(request.args.get('batch_id'))
        if request.args.get('wastage_reason'):
            filters['wastage_reason'] = request.args.get('wastage_reason')
        if request.args.get('wastage_category'):
            filters['wastage_category'] = request.args.get('wastage_category')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        records = service.get_wastage_records(filters)
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in records],
            'count': len(records)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting wastage records: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/wastage', methods=['POST'])
@require_auth
@feature_required('FEATURE_WASTAGE_TRACKING')
def create_wastage_record():
    """Create a new wastage record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, record, message = service.create_wastage_record(data)
        if success:
            return jsonify({
                'success': True,
                'data': record.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating wastage record: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Weighing Scale Integration Routes

@food_confectionery_bp.route('/api/weighing-scales', methods=['GET'])
@require_auth
@feature_required('FEATURE_WEIGHING_SCALE')
def get_weighing_scales():
    """Get weighing scales with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('connection_type'):
            filters['connection_type'] = request.args.get('connection_type')
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('department'):
            filters['department'] = request.args.get('department')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_connected'):
            filters['is_connected'] = request.args.get('is_connected').lower() == 'true'
        
        scales = service.get_weighing_scales(filters)
        return jsonify({
            'success': True,
            'data': [scale.to_dict() for scale in scales],
            'count': len(scales)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting weighing scales: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/weighing-scales', methods=['POST'])
@require_auth
@feature_required('FEATURE_WEIGHING_SCALE')
def create_weighing_scale():
    """Create a new weighing scale integration"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
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

# Analytics and Reporting Routes

@food_confectionery_bp.route('/api/reports/expiry', methods=['GET'])
@require_auth
@feature_required('FEATURE_EXPIRY_REPORTING')
def get_expiry_report():
    """Get expiry report"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        days_ahead = request.args.get('days_ahead', 30, type=int)
        report = service.get_expiry_report(days_ahead)
        
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        current_app.logger.error(f"Error generating expiry report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/reports/wastage', methods=['GET'])
@require_auth
@feature_required('FEATURE_WASTAGE_ANALYSIS')
def get_wastage_analysis():
    """Get wastage analysis"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        analysis = service.get_wastage_analysis(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        current_app.logger.error(f"Error generating wastage analysis: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@food_confectionery_bp.route('/api/reports/temperature-compliance', methods=['GET'])
@require_auth
@feature_required('FEATURE_TEMPERATURE_REPORTING')
def get_temperature_compliance_report():
    """Get temperature compliance report"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_food_confectionery_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        report = service.get_temperature_compliance_report(start_date, end_date)
        return jsonify({
            'success': True,
            'data': report
        })
    except Exception as e:
        current_app.logger.error(f"Error generating temperature compliance report: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@food_confectionery_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_FOOD_MANAGEMENT')
def get_food_config():
    """Get food & confectionery configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'food_management': feature_manager.is_enabled('FEATURE_FOOD_MANAGEMENT', tenant_id),
                'batch_tracking': feature_manager.is_enabled('FEATURE_BATCH_TRACKING', tenant_id),
                'temperature_logging': feature_manager.is_enabled('FEATURE_TEMPERATURE_LOGGING', tenant_id),
                'recipe_management': feature_manager.is_enabled('FEATURE_RECIPE_MANAGEMENT', tenant_id),
                'wastage_tracking': feature_manager.is_enabled('FEATURE_WASTAGE_TRACKING', tenant_id),
                'weighing_scale': feature_manager.is_enabled('FEATURE_WEIGHING_SCALE', tenant_id),
                'expiry_reporting': feature_manager.is_enabled('FEATURE_EXPIRY_REPORTING', tenant_id),
                'wastage_analysis': feature_manager.is_enabled('FEATURE_WASTAGE_ANALYSIS', tenant_id),
                'temperature_reporting': feature_manager.is_enabled('FEATURE_TEMPERATURE_REPORTING', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'batch_tracking_required': True,
                'temperature_logging_required': False,
                'expiry_warning_days': 7,
                'expiry_critical_days': 3,
                'temperature_tolerance': 2.0,
                'wastage_tracking_required': False,
                'recipe_cost_calculation': True,
                'weighing_scale_integration': False
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting food config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500