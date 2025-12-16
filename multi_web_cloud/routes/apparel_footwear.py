"""
Apparel & Footwear specific routes with feature-aware capabilities
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models import db
from models.apparel_footwear import (
    ApparelProduct, ApparelVariant, ApparelSizeMatrix, 
    ApparelExchange, ApparelExchangeItem, ApparelInventoryTransaction
)
from services.apparel_footwear_service import create_apparel_footwear_service
from utils.feature_flag_manager import feature_manager
from utils.tenant_query_manager import get_current_tenant_id

apparel_footwear_bp = Blueprint('apparel_footwear', __name__, url_prefix='/apparel')


def get_apparel_service():
    """Get apparel service instance with current tenant context"""
    tenant_id = get_current_tenant_id()
    return create_apparel_footwear_service(tenant_id)


def feature_required(feature_name: str):
    """Decorator to check if feature is enabled"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            tenant_id = get_current_tenant_id()
            if not feature_manager.is_enabled(feature_name, tenant_id):
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({
                        'success': False,
                        'error': f'Feature {feature_name} is not enabled'
                    }), 403
                flash(f'Feature {feature_name} is not enabled', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# Product Management Routes

@apparel_footwear_bp.route('/products')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def products():
    """Apparel products management page"""
    service = get_apparel_service()
    
    # Get filters from query parameters
    filters = {}
    if request.args.get('brand'):
        filters['brand_name'] = request.args.get('brand')
    if request.args.get('season'):
        filters['season'] = request.args.get('season')
    if request.args.get('gender'):
        filters['gender'] = request.args.get('gender')
    if request.args.get('min_price'):
        filters['min_price'] = request.args.get('min_price')
    if request.args.get('max_price'):
        filters['max_price'] = request.args.get('max_price')
    
    products = service.get_apparel_products(filters)
    
    return render_template('apparel_footwear/products/index.html', products=products)


@apparel_footwear_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def add_product():
    """Add new apparel product"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            service = get_apparel_service()
            
            success, product, message = service.create_apparel_product(
                product_data=data,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'product': product.to_dict(),
                    'message': message
                })
            else:
                return jsonify({'success': False, 'message': message}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('apparel_footwear/products/add.html')


@apparel_footwear_bp.route('/products/<int:product_id>')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def view_product(product_id):
    """View apparel product details"""
    try:
        product = ApparelProduct.query.get_or_404(product_id)
        service = get_apparel_service()
        
        # Get product variants
        variants = service.get_product_variants(product_id)
        
        # Get size matrix if feature is enabled
        size_matrix = []
        if service.is_feature_enabled('FEATURE_SIZE_MATRIX'):
            size_matrix = service.get_size_matrix(product_id)
        
        return render_template('apparel_footwear/products/view.html',
                            product=product,
                            variants=variants,
                            size_matrix=size_matrix)
                            
    except Exception as e:
        flash(f'Error loading product: {str(e)}', 'error')
        return redirect(url_for('apparel_footwear.products'))


@apparel_footwear_bp.route('/products/<int:product_id>/variants')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def product_variants(product_id):
    """Get product variants via API"""
    try:
        service = get_apparel_service()
        variants = service.get_product_variants(product_id)
        
        return jsonify({
            'success': True,
            'variants': [variant.to_dict() for variant in variants]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/products/<int:product_id>/sizes')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def available_sizes(product_id):
    """Get available sizes for a product"""
    try:
        service = get_apparel_service()
        sizes = service.get_available_sizes_for_product(product_id)
        
        return jsonify({
            'success': True,
            'sizes': sizes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/products/<int:product_id>/colors')
@login_required
@feature_required('FEATURE_COLOR_VARIANTS')
def available_colors(product_id):
    """Get available colors for a product"""
    try:
        size = request.args.get('size')  # Optional size filter
        service = get_apparel_service()
        
        if size:
            colors = service.get_available_colors_for_product(product_id, size)
        else:
            colors = service.get_available_colors_for_product(product_id)
        
        return jsonify({
            'success': True,
            'colors': colors
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Inventory Management Routes

@apparel_footwear_bp.route('/inventory/stock')
@login_required
@feature_required('FEATURE_STOCK_TRACKING')
def inventory_stock():
    """Inventory stock management page"""
    service = get_apparel_service()
    
    # Get inventory summary
    inventory_summary = service.get_inventory_summary()
    
    # Get low stock variants
    low_stock_variants = service.get_low_stock_variants()
    
    # Get out of stock variants
    out_of_stock_variants = service.get_out_of_stock_variants()
    
    return render_template('apparel_footwear/inventory/stock.html',
                        inventory_summary=inventory_summary,
                        low_stock_variants=low_stock_variants,
                        out_of_stock_variants=out_of_stock_variants)


@apparel_footwear_bp.route('/inventory/adjust', methods=['POST'])
@login_required
@feature_required('FEATURE_STOCK_TRACKING')
def adjust_stock():
    """Adjust variant stock"""
    try:
        data = request.get_json()
        service = get_apparel_service()
        
        success, message = service.adjust_variant_stock(
            variant_id=int(data['variant_id']),
            quantity=int(data['quantity']),
            reason=data.get('reason', 'Manual Adjustment'),
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/inventory/low_stock')
@login_required
@feature_required('FEATURE_LOW_STOCK_ALERTS')
def low_stock_alerts():
    """Get low stock alerts"""
    try:
        threshold = int(request.args.get('threshold', 5))
        service = get_apparel_service()
        variants = service.get_low_stock_variants(threshold)
        
        return jsonify({
            'success': True,
            'variants': [variant.to_dict() for variant in variants]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/inventory/out_of_stock')
@login_required
@feature_required('FEATURE_STOCK_TRACKING')
def out_of_stock():
    """Get out of stock variants"""
    try:
        service = get_apparel_service()
        variants = service.get_out_of_stock_variants()
        
        return jsonify({
            'success': True,
            'variants': [variant.to_dict() for variant in variants]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Exchange Management Routes

@apparel_footwear_bp.route('/exchanges')
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def exchanges():
    """Exchanges management page"""
    service = get_apparel_service()
    
    # Get filters
    status_filter = request.args.get('status')
    customer_id = request.args.get('customer_id')
    
    exchanges = []
    if customer_id:
        exchanges = service.get_customer_exchanges(int(customer_id), status_filter)
    
    return render_template('apparel_footwear/exchanges/index.html', exchanges=exchanges)


@apparel_footwear_bp.route('/exchanges/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def add_exchange():
    """Add new exchange request"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            service = get_apparel_service()
            
            success, exchange, message = service.create_exchange(
                exchange_data=data,
                user_id=current_user.id if current_user.is_authenticated else None
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'exchange': exchange.to_dict(),
                    'message': message
                })
            else:
                return jsonify({'success': False, 'message': message}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('apparel_footwear/exchanges/add.html')


@apparel_footwear_bp.route('/exchanges/<int:exchange_id>/approve', methods=['POST'])
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def approve_exchange(exchange_id):
    """Approve exchange request"""
    try:
        service = get_apparel_service()
        success, message = service.approve_exchange(
            exchange_id=exchange_id,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/exchanges/<int:exchange_id>/complete', methods=['POST'])
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def complete_exchange(exchange_id):
    """Complete exchange"""
    try:
        data = request.get_json()
        service = get_apparel_service()
        
        success, message = service.complete_exchange(
            exchange_id=exchange_id,
            completion_data=data
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/exchanges/customer/<int:customer_id>')
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def customer_exchanges(customer_id):
    """Get exchanges for a customer"""
    try:
        status_filter = request.args.get('status')
        service = get_apparel_service()
        exchanges = service.get_customer_exchanges(customer_id, status_filter)
        
        return jsonify({
            'success': True,
            'exchanges': [exchange.to_dict() for exchange in exchanges]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Size Matrix Routes

@apparel_footwear_bp.route('/size_matrix/<int:product_id>')
@login_required
@feature_required('FEATURE_SIZE_MATRIX')
def size_matrix(product_id):
    """Get size matrix for a product"""
    try:
        size_system = request.args.get('size_system')
        service = get_apparel_service()
        matrix = service.get_size_matrix(product_id, size_system)
        
        return jsonify({
            'success': True,
            'matrix': [entry.to_dict() for entry in matrix]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Analytics Routes

@apparel_footwear_bp.route('/analytics/performance')
@login_required
@feature_required('FEATURE_ANALYTICS')
def performance_analytics():
    """Product performance analytics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        service = get_apparel_service()
        analytics = service.get_product_performance(start_date, end_date)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/analytics/inventory')
@login_required
@feature_required('FEATURE_ANALYTICS')
def inventory_analytics():
    """Inventory analytics"""
    try:
        service = get_apparel_service()
        analytics = service.get_inventory_summary()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Variant Lookup Routes

@apparel_footwear_bp.route('/variant/sku/<sku>')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def variant_by_sku(sku):
    """Get variant by SKU"""
    try:
        service = get_apparel_service()
        variant = service.get_variant_by_sku(sku)
        
        if variant:
            return jsonify({
                'success': True,
                'variant': variant.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': 'Variant not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/variant/lookup')
@login_required
@feature_required('FEATURE_SIZE_VARIANTS')
def variant_lookup():
    """Lookup variant by size and color"""
    try:
        product_id = int(request.args.get('product_id'))
        size = request.args.get('size')
        color = request.args.get('color')
        
        service = get_apparel_service()
        variant = service.get_variant_by_size_color(product_id, size, color)
        
        if variant:
            return jsonify({
                'success': True,
                'variant': variant.to_dict()
            })
        else:
            return jsonify({'success': False, 'message': 'Variant not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Bulk Operations Routes

@apparel_footwear_bp.route('/bulk/stock_adjust', methods=['POST'])
@login_required
@feature_required('FEATURE_STOCK_TRACKING')
def bulk_stock_adjust():
    """Bulk stock adjustment"""
    try:
        data = request.get_json()
        adjustments = data.get('adjustments', [])
        reason = data.get('reason', 'Bulk Adjustment')
        
        service = get_apparel_service()
        results = []
        
        for adjustment in adjustments:
            success, message = service.adjust_variant_stock(
                variant_id=int(adjustment['variant_id']),
                quantity=int(adjustment['quantity']),
                reason=f"{reason}: {adjustment.get('note', '')}",
                user_id=current_user.id if current_user.is_authenticated else None
            )
            
            results.append({
                'variant_id': adjustment['variant_id'],
                'success': success,
                'message': message
            })
        
        successful_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'successful': successful_count,
            'failed': len(results) - successful_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@apparel_footwear_bp.route('/bulk/exchange_approve', methods=['POST'])
@login_required
@feature_required('FEATURE_EXCHANGE_MANAGEMENT')
def bulk_exchange_approve():
    """Bulk approve exchanges"""
    try:
        data = request.get_json()
        exchange_ids = data.get('exchange_ids', [])
        
        service = get_apparel_service()
        results = []
        
        for exchange_id in exchange_ids:
            success, message = service.approve_exchange(
                exchange_id=int(exchange_id),
                user_id=current_user.id if current_user.is_authenticated else None
            )
            
            results.append({
                'exchange_id': exchange_id,
                'success': success,
                'message': message
            })
        
        successful_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'successful': successful_count,
            'failed': len(results) - successful_count,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500