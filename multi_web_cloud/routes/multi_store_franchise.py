"""
Routes for Multi-Store & Franchise module handling multi-store inventory management,
store transfers, consolidated reporting, franchise management and royalty tracking.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date, timedelta
from decimal import Decimal
from functools import wraps

from models import db
from models.multi_store_franchise import (
    Store, InventoryTransfer, ConsolidatedReport, FranchiseAgreement,
    RoyaltyPayment, StorePerformance, StoreInventory, StoreUser,
    StoreType, TransferStatus, FranchiseStatus
)
from models.feature_flag import feature_flag_service
from services.multi_store_franchise_service import multi_store_franchise_service
from middleware.tenant_middleware import get_current_tenant
from routes.validation_api import validate_tenant_access

# Create blueprint
multi_store_franchise_bp = Blueprint('multi_store_franchise', __name__, url_prefix='/api/multi-store-franchise')

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


# Store Management Routes

@multi_store_franchise_bp.route('/stores', methods=['POST'])
@feature_required('multi_store_management')
def create_store():
    """Create a new store"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        store, error = multi_store_franchise_service.create_store(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Store created successfully',
            'store': store.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating store: {str(e)}")
        return jsonify({'error': 'Failed to create store'}), 500


@multi_store_franchise_bp.route('/stores', methods=['GET'])
@feature_required('multi_store_management')
def get_stores():
    """Get all stores for the current tenant"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        stores = multi_store_franchise_service.get_stores(tenant_id, include_inactive)
        
        return jsonify({
            'stores': [store.to_dict() for store in stores],
            'count': len(stores)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting stores: {str(e)}")
        return jsonify({'error': 'Failed to get stores'}), 500


@multi_store_franchise_bp.route('/stores/<int:store_id>', methods=['GET'])
@feature_required('multi_store_management')
def get_store(store_id):
    """Get a specific store by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        store = multi_store_franchise_service.get_store(store_id, tenant_id)
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        
        return jsonify({'store': store.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting store: {str(e)}")
        return jsonify({'error': 'Failed to get store'}), 500


@multi_store_franchise_bp.route('/stores/<int:store_id>', methods=['PUT'])
@feature_required('multi_store_management')
def update_store(store_id):
    """Update store information"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        store, error = multi_store_franchise_service.update_store(store_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        
        return jsonify({
            'message': 'Store updated successfully',
            'store': store.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating store: {str(e)}")
        return jsonify({'error': 'Failed to update store'}), 500


@multi_store_franchise_bp.route('/stores/<int:store_id>', methods=['DELETE'])
@feature_required('multi_store_management')
def delete_store(store_id):
    """Delete a store"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        success, error = multi_store_franchise_service.delete_store(store_id, tenant_id)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Store not found'}), 404
        
        return jsonify({'message': 'Store deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting store: {str(e)}")
        return jsonify({'error': 'Failed to delete store'}), 500


# Inventory Transfer Routes

@multi_store_franchise_bp.route('/inventory-transfers', methods=['POST'])
@feature_required('inventory_transfers')
def create_inventory_transfer():
    """Create a new inventory transfer"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        transfer, error = multi_store_franchise_service.create_inventory_transfer(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Inventory transfer created successfully',
            'transfer': transfer.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating inventory transfer: {str(e)}")
        return jsonify({'error': 'Failed to create inventory transfer'}), 500


@multi_store_franchise_bp.route('/inventory-transfers', methods=['GET'])
@feature_required('inventory_transfers')
def get_inventory_transfers():
    """Get inventory transfers with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        from_store_id = request.args.get('from_store_id', type=int)
        to_store_id = request.args.get('to_store_id', type=int)
        status = request.args.get('status')
        
        transfers = multi_store_franchise_service.get_inventory_transfers(
            tenant_id, from_store_id, to_store_id, status
        )
        
        return jsonify({
            'transfers': [transfer.to_dict() for transfer in transfers],
            'count': len(transfers)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting inventory transfers: {str(e)}")
        return jsonify({'error': 'Failed to get inventory transfers'}), 500


@multi_store_franchise_bp.route('/inventory-transfers/<int:transfer_id>', methods=['GET'])
@feature_required('inventory_transfers')
def get_inventory_transfer(transfer_id):
    """Get a specific inventory transfer by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        transfer = multi_store_franchise_service.get_inventory_transfer(transfer_id, tenant_id)
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        return jsonify({'transfer': transfer.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting inventory transfer: {str(e)}")
        return jsonify({'error': 'Failed to get inventory transfer'}), 500


@multi_store_franchise_bp.route('/inventory-transfers/<int:transfer_id>', methods=['PUT'])
@feature_required('inventory_transfers')
def update_inventory_transfer(transfer_id):
    """Update inventory transfer"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        transfer, error = multi_store_franchise_service.update_inventory_transfer(transfer_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        return jsonify({
            'message': 'Inventory transfer updated successfully',
            'transfer': transfer.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating inventory transfer: {str(e)}")
        return jsonify({'error': 'Failed to update inventory transfer'}), 500


@multi_store_franchise_bp.route('/inventory-transfers/<int:transfer_id>/approve', methods=['POST'])
@feature_required('inventory_transfers')
def approve_transfer(transfer_id):
    """Approve an inventory transfer"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        approved_by = data.get('approved_by')
        
        if not approved_by:
            return jsonify({'error': 'Approved by user ID is required'}), 400
        
        success, error = multi_store_franchise_service.approve_transfer(transfer_id, approved_by, tenant_id)
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Transfer not found'}), 404
        
        return jsonify({'message': 'Transfer approved successfully'})
    except Exception as e:
        current_app.logger.error(f"Error approving transfer: {str(e)}")
        return jsonify({'error': 'Failed to approve transfer'}), 500


@multi_store_franchise_bp.route('/inventory-transfers/<int:transfer_id>/receive', methods=['POST'])
@feature_required('inventory_transfers')
def receive_transfer(transfer_id):
    """Receive an inventory transfer"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        received_by = data.get('received_by')
        received_items = data.get('received_items')
        
        if not received_by:
            return jsonify({'error': 'Received by user ID is required'}), 400
        
        success, error = multi_store_franchise_service.receive_transfer(
            transfer_id, received_by, tenant_id, received_items
        )
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Transfer not found'}), 404
        
        return jsonify({'message': 'Transfer received successfully'})
    except Exception as e:
        current_app.logger.error(f"Error receiving transfer: {str(e)}")
        return jsonify({'error': 'Failed to receive transfer'}), 500


# Consolidated Reporting Routes

@multi_store_franchise_bp.route('/consolidated-reports', methods=['POST'])
@feature_required('consolidated_reporting')
def create_consolidated_report():
    """Create a new consolidated report"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        report, error = multi_store_franchise_service.create_consolidated_report(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Consolidated report created successfully',
            'report': report.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating consolidated report: {str(e)}")
        return jsonify({'error': 'Failed to create consolidated report'}), 500


@multi_store_franchise_bp.route('/consolidated-reports', methods=['GET'])
@feature_required('consolidated_reporting')
def get_consolidated_reports():
    """Get consolidated reports with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        report_type = request.args.get('report_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert date strings to date objects if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        reports = multi_store_franchise_service.get_consolidated_reports(
            tenant_id, report_type, start_date, end_date
        )
        
        return jsonify({
            'reports': [report.to_dict() for report in reports],
            'count': len(reports)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting consolidated reports: {str(e)}")
        return jsonify({'error': 'Failed to get consolidated reports'}), 500


@multi_store_franchise_bp.route('/consolidated-reports/<int:report_id>', methods=['GET'])
@feature_required('consolidated_reporting')
def get_consolidated_report(report_id):
    """Get a specific consolidated report by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        report = multi_store_franchise_service.get_consolidated_report(report_id, tenant_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify({'report': report.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting consolidated report: {str(e)}")
        return jsonify({'error': 'Failed to get consolidated report'}), 500


@multi_store_franchise_bp.route('/consolidated-reports/sales', methods=['POST'])
@feature_required('consolidated_reporting')
def generate_sales_consolidated_report():
    """Generate consolidated sales report"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        store_ids = data.get('store_ids', [])
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        report_data = multi_store_franchise_service.generate_sales_consolidated_report(
            tenant_id, store_ids, start_date, end_date
        )
        
        if 'error' in report_data:
            return jsonify({'error': report_data['error']}), 400
        
        return jsonify({
            'message': 'Sales consolidated report generated successfully',
            'report_data': report_data
        })
    except Exception as e:
        current_app.logger.error(f"Error generating sales consolidated report: {str(e)}")
        return jsonify({'error': 'Failed to generate sales consolidated report'}), 500


# Franchise Management Routes

@multi_store_franchise_bp.route('/franchise-agreements', methods=['POST'])
@feature_required('franchise_management')
def create_franchise_agreement():
    """Create a new franchise agreement"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        agreement, error = multi_store_franchise_service.create_franchise_agreement(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Franchise agreement created successfully',
            'agreement': agreement.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating franchise agreement: {str(e)}")
        return jsonify({'error': 'Failed to create franchise agreement'}), 500


@multi_store_franchise_bp.route('/franchise-agreements', methods=['GET'])
@feature_required('franchise_management')
def get_franchise_agreements():
    """Get franchise agreements with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        status = request.args.get('status')
        
        agreements = multi_store_franchise_service.get_franchise_agreements(tenant_id, status)
        
        return jsonify({
            'agreements': [agreement.to_dict() for agreement in agreements],
            'count': len(agreements)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting franchise agreements: {str(e)}")
        return jsonify({'error': 'Failed to get franchise agreements'}), 500


@multi_store_franchise_bp.route('/franchise-agreements/<int:agreement_id>', methods=['GET'])
@feature_required('franchise_management')
def get_franchise_agreement(agreement_id):
    """Get a specific franchise agreement by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        agreement = multi_store_franchise_service.get_franchise_agreement(agreement_id, tenant_id)
        if not agreement:
            return jsonify({'error': 'Agreement not found'}), 404
        
        return jsonify({'agreement': agreement.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting franchise agreement: {str(e)}")
        return jsonify({'error': 'Failed to get franchise agreement'}), 500


@multi_store_franchise_bp.route('/franchise-agreements/<int:agreement_id>', methods=['PUT'])
@feature_required('franchise_management')
def update_franchise_agreement(agreement_id):
    """Update franchise agreement"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        agreement, error = multi_store_franchise_service.update_franchise_agreement(agreement_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not agreement:
            return jsonify({'error': 'Agreement not found'}), 404
        
        return jsonify({
            'message': 'Franchise agreement updated successfully',
            'agreement': agreement.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating franchise agreement: {str(e)}")
        return jsonify({'error': 'Failed to update franchise agreement'}), 500


# Royalty Payment Routes

@multi_store_franchise_bp.route('/royalty-payments', methods=['POST'])
@feature_required('royalty_tracking')
def create_royalty_payment():
    """Create a new royalty payment"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        payment, error = multi_store_franchise_service.create_royalty_payment(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Royalty payment created successfully',
            'payment': payment.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating royalty payment: {str(e)}")
        return jsonify({'error': 'Failed to create royalty payment'}), 500


@multi_store_franchise_bp.route('/royalty-payments', methods=['GET'])
@feature_required('royalty_tracking')
def get_royalty_payments():
    """Get royalty payments with filters"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        franchise_id = request.args.get('franchise_id')
        status = request.args.get('status')
        
        payments = multi_store_franchise_service.get_royalty_payments(tenant_id, franchise_id, status)
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments],
            'count': len(payments)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting royalty payments: {str(e)}")
        return jsonify({'error': 'Failed to get royalty payments'}), 500


@multi_store_franchise_bp.route('/royalty-payments/<int:payment_id>', methods=['GET'])
@feature_required('royalty_tracking')
def get_royalty_payment(payment_id):
    """Get a specific royalty payment by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        payment = multi_store_franchise_service.get_royalty_payment(payment_id, tenant_id)
        if not payment:
            return jsonify({'error': 'Payment not found'}), 404
        
        return jsonify({'payment': payment.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting royalty payment: {str(e)}")
        return jsonify({'error': 'Failed to get royalty payment'}), 500


@multi_store_franchise_bp.route('/royalty-payments/calculate', methods=['POST'])
@feature_required('royalty_tracking')
def calculate_monthly_royalty():
    """Calculate monthly royalty for a franchise"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        franchise_id = data.get('franchise_id')
        period_start = datetime.strptime(data.get('period_start'), '%Y-%m-%d').date()
        period_end = datetime.strptime(data.get('period_end'), '%Y-%m-%d').date()
        
        calculation = multi_store_franchise_service.calculate_monthly_royalty(
            tenant_id, franchise_id, period_start, period_end
        )
        
        if 'error' in calculation:
            return jsonify({'error': calculation['error']}), 400
        
        return jsonify({
            'message': 'Monthly royalty calculated successfully',
            'calculation': calculation
        })
    except Exception as e:
        current_app.logger.error(f"Error calculating monthly royalty: {str(e)}")
        return jsonify({'error': 'Failed to calculate monthly royalty'}), 500


# Store Performance Routes

@multi_store_franchise_bp.route('/store-performance', methods=['POST'])
@feature_required('store_performance_tracking')
def create_store_performance():
    """Create a new store performance record"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        performance, error = multi_store_franchise_service.create_store_performance(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Store performance record created successfully',
            'performance': performance.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating store performance: {str(e)}")
        return jsonify({'error': 'Failed to create store performance'}), 500


@multi_store_franchise_bp.route('/store-performance/<int:performance_id>', methods=['GET'])
@feature_required('store_performance_tracking')
def get_store_performance(performance_id):
    """Get a specific store performance record by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        performance = multi_store_franchise_service.get_store_performance(performance_id, tenant_id)
        if not performance:
            return jsonify({'error': 'Performance record not found'}), 404
        
        return jsonify({'performance': performance.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting store performance: {str(e)}")
        return jsonify({'error': 'Failed to get store performance'}), 500


@multi_store_franchise_bp.route('/store-performance/store/<int:store_id>', methods=['GET'])
@feature_required('store_performance_tracking')
def get_store_performance_by_store(store_id):
    """Get store performance by store with date range"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Convert date strings to date objects if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        performances = multi_store_franchise_service.get_store_performance_by_store(
            tenant_id, store_id, start_date, end_date
        )
        
        return jsonify({
            'performances': [performance.to_dict() for performance in performances],
            'count': len(performances)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting store performance by store: {str(e)}")
        return jsonify({'error': 'Failed to get store performance'}), 500


@multi_store_franchise_bp.route('/store-performance/comparison', methods=['POST'])
@feature_required('store_performance_tracking')
def get_store_performance_comparison():
    """Compare performance across multiple stores"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        store_ids = data.get('store_ids', [])
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        comparison = multi_store_franchise_service.get_store_performance_comparison(
            tenant_id, store_ids, start_date, end_date
        )
        
        if 'error' in comparison:
            return jsonify({'error': comparison['error']}), 400
        
        return jsonify({
            'message': 'Store performance comparison generated successfully',
            'comparison': comparison
        })
    except Exception as e:
        current_app.logger.error(f"Error generating store performance comparison: {str(e)}")
        return jsonify({'error': 'Failed to generate store performance comparison'}), 500


# Store Inventory Routes

@multi_store_franchise_bp.route('/store-inventory', methods=['POST'])
@feature_required('store_inventory_tracking')
def create_store_inventory():
    """Create a new store inventory record"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        inventory, error = multi_store_franchise_service.create_store_inventory(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Store inventory record created successfully',
            'inventory': inventory.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating store inventory: {str(e)}")
        return jsonify({'error': 'Failed to create store inventory'}), 500


@multi_store_franchise_bp.route('/store-inventory/<int:inventory_id>', methods=['GET'])
@feature_required('store_inventory_tracking')
def get_store_inventory(inventory_id):
    """Get a specific store inventory record by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        inventory = multi_store_franchise_service.get_store_inventory(inventory_id, tenant_id)
        if not inventory:
            return jsonify({'error': 'Inventory record not found'}), 404
        
        return jsonify({'inventory': inventory.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting store inventory: {str(e)}")
        return jsonify({'error': 'Failed to get store inventory'}), 500


@multi_store_franchise_bp.route('/store-inventory/store/<int:store_id>', methods=['GET'])
@feature_required('store_inventory_tracking')
def get_store_inventory_by_store(store_id):
    """Get store inventory by store with optional filter for low stock"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        below_reorder_point = request.args.get('below_reorder_point', 'false').lower() == 'true'
        
        inventory = multi_store_franchise_service.get_store_inventory_by_store(
            tenant_id, store_id, below_reorder_point
        )
        
        return jsonify({
            'inventory': [item.to_dict() for item in inventory],
            'count': len(inventory)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting store inventory by store: {str(e)}")
        return jsonify({'error': 'Failed to get store inventory'}), 500


@multi_store_franchise_bp.route('/store-inventory/<int:inventory_id>', methods=['PUT'])
@feature_required('store_inventory_tracking')
def update_store_inventory(inventory_id):
    """Update store inventory"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        inventory, error = multi_store_franchise_service.update_store_inventory(inventory_id, data)
        if error:
            return jsonify({'error': error}), 400
        
        if not inventory:
            return jsonify({'error': 'Inventory record not found'}), 404
        
        return jsonify({
            'message': 'Store inventory updated successfully',
            'inventory': inventory.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error updating store inventory: {str(e)}")
        return jsonify({'error': 'Failed to update store inventory'}), 500


# Store User Routes

@multi_store_franchise_bp.route('/store-users', methods=['POST'])
@feature_required('store_user_management')
def create_store_user():
    """Create a new store user assignment"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        data['tenant_id'] = tenant_id
        
        store_user, error = multi_store_franchise_service.create_store_user(data)
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'message': 'Store user assignment created successfully',
            'store_user': store_user.to_dict()
        }), 201
    except Exception as e:
        current_app.logger.error(f"Error creating store user: {str(e)}")
        return jsonify({'error': 'Failed to create store user'}), 500


@multi_store_franchise_bp.route('/store-users/<int:store_user_id>', methods=['GET'])
@feature_required('store_user_management')
def get_store_user(store_user_id):
    """Get a specific store user assignment by ID"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        store_user = multi_store_franchise_service.get_store_user(store_user_id, tenant_id)
        if not store_user:
            return jsonify({'error': 'Store user assignment not found'}), 404
        
        return jsonify({'store_user': store_user.to_dict()})
    except Exception as e:
        current_app.logger.error(f"Error getting store user: {str(e)}")
        return jsonify({'error': 'Failed to get store user'}), 500


@multi_store_franchise_bp.route('/store-users/store/<int:store_id>', methods=['GET'])
@feature_required('store_user_management')
def get_store_users_by_store(store_id):
    """Get store users by store"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        store_users = multi_store_franchise_service.get_store_users_by_store(
            tenant_id, store_id, active_only
        )
        
        return jsonify({
            'store_users': [store_user.to_dict() for store_user in store_users],
            'count': len(store_users)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting store users by store: {str(e)}")
        return jsonify({'error': 'Failed to get store users'}), 500


@multi_store_franchise_bp.route('/store-users/user/<int:user_id>', methods=['GET'])
@feature_required('store_user_management')
def get_store_users_by_user(user_id):
    """Get store assignments by user"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        store_users = multi_store_franchise_service.get_store_users_by_user(
            tenant_id, user_id, active_only
        )
        
        return jsonify({
            'store_users': [store_user.to_dict() for store_user in store_users],
            'count': len(store_users)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting store users by user: {str(e)}")
        return jsonify({'error': 'Failed to get store users'}), 500


@multi_store_franchise_bp.route('/store-users/<int:store_user_id>/terminate', methods=['POST'])
@feature_required('store_user_management')
def terminate_store_user(store_user_id):
    """Terminate a store user assignment"""
    try:
        tenant_id = get_current_tenant()
        if not tenant_id:
            return jsonify({'error': 'Tenant not found'}), 401
        
        data = request.get_json()
        termination_reason = data.get('termination_reason')
        
        if not termination_reason:
            return jsonify({'error': 'Termination reason is required'}), 400
        
        success, error = multi_store_franchise_service.terminate_store_user(
            store_user_id, tenant_id, termination_reason
        )
        if error:
            return jsonify({'error': error}), 400
        
        if not success:
            return jsonify({'error': 'Store user assignment not found'}), 404
        
        return jsonify({'message': 'Store user assignment terminated successfully'})
    except Exception as e:
        current_app.logger.error(f"Error terminating store user: {str(e)}")
        return jsonify({'error': 'Failed to terminate store user'}), 500


# Analytics Routes

@multi_store_franchise_bp.route('/analytics/multi-store', methods=['GET'])
@feature_required('multi_store_analytics')
def get_multi_store_analytics():
    """Get multi-store analytics for a date range"""
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
        
        analytics = multi_store_franchise_service.get_multi_store_analytics(
            tenant_id, start_date, end_date
        )
        
        if 'error' in analytics:
            return jsonify({'error': analytics['error']}), 400
        
        return jsonify({
            'message': 'Multi-store analytics generated successfully',
            'analytics': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error generating multi-store analytics: {str(e)}")
        return jsonify({'error': 'Failed to generate multi-store analytics'}), 500