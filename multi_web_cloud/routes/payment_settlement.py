"""
Payment & Settlement routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.payment_settlement_service import create_payment_settlement_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.payment_settlement import (
    PaymentMethod, WalletPayment, EMIPayment, DenominationCount,
    SplitPayment, SettlementRecord, CashManagement
)
from models import db
from datetime import datetime, date
import json

# Create blueprint
payment_settlement_bp = Blueprint('payment_settlement', __name__, url_prefix='/payment')

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

# Payment Method Routes

@payment_settlement_bp.route('/api/methods', methods=['GET'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def get_payment_methods():
    """Get payment methods with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('method_type'):
            filters['method_type'] = request.args.get('method_type')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active').lower() == 'true'
        if request.args.get('is_default'):
            filters['is_default'] = request.args.get('is_default').lower() == 'true'
        if request.args.get('requires_approval'):
            filters['requires_approval'] = request.args.get('requires_approval').lower() == 'true'
        if request.args.get('allows_partial'):
            filters['allows_partial'] = request.args.get('allows_partial').lower() == 'true'
        if request.args.get('settlement_cycle'):
            filters['settlement_cycle'] = request.args.get('settlement_cycle')
        
        methods = service.get_payment_methods(filters)
        return jsonify({
            'success': True,
            'data': [method.to_dict() for method in methods],
            'count': len(methods)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting payment methods: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/methods', methods=['POST'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def create_payment_method():
    """Create a new payment method"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, method, message = service.create_payment_method(data)
        if success:
            return jsonify({
                'success': True,
                'data': method.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating payment method: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/methods/<int:method_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def get_payment_method(method_id):
    """Get payment method by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        method = service.get_payment_method_by_id(method_id)
        if not method:
            return jsonify({'success': False, 'message': 'Payment method not found'}), 404
        
        return jsonify({
            'success': True,
            'data': method.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting payment method: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/methods/<int:method_id>', methods=['PUT'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def update_payment_method(method_id):
    """Update an existing payment method"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, method, message = service.update_payment_method(method_id, data)
        if success:
            return jsonify({
                'success': True,
                'data': method.to_dict(),
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating payment method: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/methods/default', methods=['GET'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def get_default_payment_method():
    """Get default payment method"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        method = service.get_default_payment_method()
        if not method:
            return jsonify({'success': False, 'message': 'No default payment method found'}), 404
        
        return jsonify({
            'success': True,
            'data': method.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting default payment method: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Wallet Payment Routes

@payment_settlement_bp.route('/api/wallet/payments', methods=['GET'])
@require_auth
@feature_required('FEATURE_WALLET_PAYMENTS')
def get_wallet_payments():
    """Get wallet payments with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('wallet_id'):
            filters['wallet_id'] = request.args.get('wallet_id')
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('payment_method_id'):
            filters['payment_method_id'] = int(request.args.get('payment_method_id'))
        if request.args.get('transaction_type'):
            filters['transaction_type'] = request.args.get('transaction_type')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        payments = service.get_wallet_payments(filters)
        return jsonify({
            'success': True,
            'data': [payment.to_dict() for payment in payments],
            'count': len(payments)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting wallet payments: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/wallet/payments', methods=['POST'])
@require_auth
@feature_required('FEATURE_WALLET_PAYMENTS')
def create_wallet_payment():
    """Create a new wallet payment"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, payment, message = service.create_wallet_payment(data)
        if success:
            return jsonify({
                'success': True,
                'data': payment.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating wallet payment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/wallet/payments/<int:payment_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_WALLET_PAYMENTS')
def get_wallet_payment(payment_id):
    """Get wallet payment by ID"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        payment = service.get_wallet_payment_by_id(payment_id)
        if not payment:
            return jsonify({'success': False, 'message': 'Wallet payment not found'}), 404
        
        return jsonify({
            'success': True,
            'data': payment.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting wallet payment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/wallet/payments/<int:payment_id>/process', methods=['POST'])
@require_auth
@feature_required('FEATURE_WALLET_PAYMENTS')
def process_wallet_payment(payment_id):
    """Process a wallet payment (approve/reject)"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        status = data.get('status')
        processed_at = None
        failure_reason = None
        
        if data.get('processed_at'):
            processed_at = datetime.strptime(data['processed_at'], '%Y-%m-%d %H:%M:%S')
        
        if data.get('failure_reason'):
            failure_reason = data['failure_reason']
        
        success, message = service.process_wallet_payment(payment_id, status, processed_at, failure_reason)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error processing wallet payment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/wallet/balance/<wallet_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_WALLET_PAYMENTS')
def get_wallet_balance(wallet_id):
    """Get wallet balance"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        balance = service.get_wallet_balance(wallet_id)
        return jsonify({
            'success': True,
            'data': balance
        })
    except Exception as e:
        current_app.logger.error(f"Error getting wallet balance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# EMI Payment Routes

@payment_settlement_bp.route('/api/emi/payments', methods=['GET'])
@require_auth
@feature_required('FEATURE_EMI_PAYMENTS')
def get_emi_payments():
    """Get EMI payments with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('emi_plan_id'):
            filters['emi_plan_id'] = request.args.get('emi_plan_id')
        if request.args.get('customer_id'):
            filters['customer_id'] = int(request.args.get('customer_id'))
        if request.args.get('payment_method_id'):
            filters['payment_method_id'] = int(request.args.get('payment_method_id'))
        if request.args.get('order_id'):
            filters['order_id'] = int(request.args.get('order_id'))
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('overdue'):
            filters['overdue'] = request.args.get('overdue').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        payments = service.get_emi_payments(filters)
        return jsonify({
            'success': True,
            'data': [payment.to_dict() for payment in payments],
            'count': len(payments)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting EMI payments: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/emi/plan', methods=['POST'])
@require_auth
@feature_required('FEATURE_EMI_PAYMENTS')
def create_emi_plan():
    """Create a new EMI plan"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, installments, message = service.create_emi_plan(data)
        if success:
            return jsonify({
                'success': True,
                'data': [installment.to_dict() for installment in installments],
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating EMI plan: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/emi/payments/<int:payment_id>/pay', methods=['POST'])
@require_auth
@feature_required('FEATURE_EMI_PAYMENTS')
def pay_emi_installment(payment_id):
    """Pay an EMI installment"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, message = service.pay_emi_installment(payment_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error paying EMI installment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Denomination Count Routes

@payment_settlement_bp.route('/api/denomination/counts', methods=['GET'])
@require_auth
@feature_required('FEATURE_DENOMINATION_COUNTING')
def get_denomination_counts():
    """Get denomination counts with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('cash_drawer_id'):
            filters['cash_drawer_id'] = int(request.args.get('cash_drawer_id'))
        if request.args.get('user_id'):
            filters['user_id'] = int(request.args.get('user_id'))
        if request.args.get('shift_id'):
            filters['shift_id'] = request.args.get('shift_id')
        if request.args.get('currency'):
            filters['currency'] = request.args.get('currency')
        if request.args.get('denomination_type'):
            filters['denomination_type'] = request.args.get('denomination_type')
        if request.args.get('count_type'):
            filters['count_type'] = request.args.get('count_type')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        counts = service.get_denomination_counts(filters)
        return jsonify({
            'success': True,
            'data': [count.to_dict() for count in counts],
            'count': len(counts)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting denomination counts: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/denomination/counts', methods=['POST'])
@require_auth
@feature_required('FEATURE_DENOMINATION_COUNTING')
def create_denomination_count():
    """Create a new denomination count"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, count, message = service.create_denomination_count(data)
        if success:
            return jsonify({
                'success': True,
                'data': count.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating denomination count: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/denomination/counts/<int:count_id>/verify', methods=['POST'])
@require_auth
@feature_required('FEATURE_DENOMINATION_COUNTING')
def verify_denomination_count(count_id):
    """Verify a denomination count"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, message = service.verify_denomination_count(count_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error verifying denomination count: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/denomination/total/<currency>', methods=['GET'])
@require_auth
@feature_required('FEATURE_DENOMINATION_COUNTING')
def calculate_total_by_currency(currency):
    """Calculate total cash by currency"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        count_type = request.args.get('count_type')
        
        total = service.calculate_total_by_currency(currency, count_type)
        return jsonify({
            'success': True,
            'data': total
        })
    except Exception as e:
        current_app.logger.error(f"Error calculating total by currency: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Split Payment Routes

@payment_settlement_bp.route('/api/split/payments', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPLIT_PAYMENTS')
def get_split_payments():
    """Get split payments with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('order_id'):
            filters['order_id'] = int(request.args.get('order_id'))
        if request.args.get('payment_method_id'):
            filters['payment_method_id'] = int(request.args.get('payment_method_id'))
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        payments = service.get_split_payments(filters)
        return jsonify({
            'success': True,
            'data': [payment.to_dict() for payment in payments],
            'count': len(payments)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting split payments: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/split/payments', methods=['POST'])
@require_auth
@feature_required('FEATURE_SPLIT_PAYMENTS')
def create_split_payment():
    """Create a new split payment"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, payment, message = service.create_split_payment(data)
        if success:
            return jsonify({
                'success': True,
                'data': payment.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating split payment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/split/payments/<int:payment_id>/process', methods=['POST'])
@require_auth
@feature_required('FEATURE_SPLIT_PAYMENTS')
def process_split_payment(payment_id):
    """Process a split payment"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        status = data.get('status')
        processed_at = None
        failure_reason = None
        
        if data.get('processed_at'):
            processed_at = datetime.strptime(data['processed_at'], '%Y-%m-%d %H:%M:%S')
        
        if data.get('failure_reason'):
            failure_reason = data['failure_reason']
        
        success, message = service.process_split_payment(payment_id, status, processed_at, failure_reason)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error processing split payment: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Settlement Routes

@payment_settlement_bp.route('/api/settlements', methods=['GET'])
@require_auth
@feature_required('FEATURE_SETTLEMENT_PROCESSING')
def get_settlement_records():
    """Get settlement records with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('payment_method_id'):
            filters['payment_method_id'] = int(request.args.get('payment_method_id'))
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('reconciled'):
            filters['reconciled'] = request.args.get('reconciled').lower() == 'true'
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        settlements = service.get_settlement_records(filters)
        return jsonify({
            'success': True,
            'data': [settlement.to_dict() for settlement in settlements],
            'count': len(settlements)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting settlement records: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/settlements', methods=['POST'])
@require_auth
@feature_required('FEATURE_SETTLEMENT_PROCESSING')
def create_settlement_record():
    """Create a new settlement record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, settlement, message = service.create_settlement_record(data)
        if success:
            return jsonify({
                'success': True,
                'data': settlement.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating settlement record: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/settlements/<int:settlement_id>/reconcile', methods=['POST'])
@require_auth
@feature_required('FEATURE_SETTLEMENT_PROCESSING')
def reconcile_settlement(settlement_id):
    """Reconcile a settlement record"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, message = service.reconcile_settlement(settlement_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error reconciling settlement: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Cash Management Routes

@payment_settlement_bp.route('/api/cash/management', methods=['GET'])
@require_auth
@feature_required('FEATURE_CASH_MANAGEMENT')
def get_cash_management_records():
    """Get cash management records with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('cash_drawer_id'):
            filters['cash_drawer_id'] = int(request.args.get('cash_drawer_id'))
        if request.args.get('user_id'):
            filters['user_id'] = int(request.args.get('user_id'))
        if request.args.get('shift_id'):
            filters['shift_id'] = request.args.get('shift_id')
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('session_type'):
            filters['session_type'] = request.args.get('session_type')
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        
        records = service.get_cash_management_records(filters)
        return jsonify({
            'success': True,
            'data': [record.to_dict() for record in records],
            'count': len(records)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting cash management records: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/cash/management', methods=['POST'])
@require_auth
@feature_required('FEATURE_CASH_MANAGEMENT')
def create_cash_management_session():
    """Create a new cash management session"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, session, message = service.create_cash_management_session(data)
        if success:
            return jsonify({
                'success': True,
                'data': session.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating cash management session: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_settlement_bp.route('/api/cash/management/<int:session_id>/close', methods=['POST'])
@require_auth
@feature_required('FEATURE_CASH_MANAGEMENT')
def close_cash_management_session(session_id):
    """Close a cash management session"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, message = service.close_cash_management_session(session_id, data)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error closing cash management session: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Analytics Routes

@payment_settlement_bp.route('/api/analytics/payments', methods=['GET'])
@require_auth
@feature_required('FEATURE_PAYMENT_ANALYTICS')
def get_payment_analytics():
    """Get payment analytics"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_payment_settlement_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date')).date()
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date')).date()
        
        analytics = service.get_payment_analytics(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error generating payment analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@payment_settlement_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_PAYMENT_METHODS')
def get_payment_config():
    """Get payment & settlement configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'payment_methods': feature_manager.is_enabled('FEATURE_PAYMENT_METHODS', tenant_id),
                'wallet_payments': feature_manager.is_enabled('FEATURE_WALLET_PAYMENTS', tenant_id),
                'emi_payments': feature_manager.is_enabled('FEATURE_EMI_PAYMENTS', tenant_id),
                'denomination_counting': feature_manager.is_enabled('FEATURE_DENOMINATION_COUNTING', tenant_id),
                'split_payments': feature_manager.is_enabled('FEATURE_SPLIT_PAYMENTS', tenant_id),
                'settlement_processing': feature_manager.is_enabled('FEATURE_SETTLEMENT_PROCESSING', tenant_id),
                'cash_management': feature_manager.is_enabled('FEATURE_CASH_MANAGEMENT', tenant_id),
                'payment_analytics': feature_manager.is_enabled('FEATURE_PAYMENT_ANALYTICS', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'payment_methods_enabled': True,
                'wallet_payments_enabled': True,
                'emi_payments_enabled': True,
                'denomination_counting_enabled': True,
                'split_payments_enabled': True,
                'settlement_processing_enabled': True,
                'cash_management_enabled': True,
                'default_settlement_cycle': 'daily',
                'default_settlement_delay_days': 2,
                'auto_settlement_enabled': True,
                'max_transaction_amount': 10000.00,
                'min_transaction_amount': 0.50,
                'late_fee_rate': 0.02,
                'grace_period_days': 3
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting payment config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500