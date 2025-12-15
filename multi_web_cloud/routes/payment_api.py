"""
Razorpay Payment API Routes for Flask POS Application
Provides comprehensive payment processing and management endpoints
"""

from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Import utility managers
from utils.razorpay_manager import razorpay_manager
from utils.session_manager import session_manager
from utils.security_manager import security_manager

# Create blueprint
payment_api_bp = Blueprint('payment_api', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Decorators for API security
def require_api_key(f):
    """Decorator to require API key for sensitive endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != current_app.config.get('API_KEY', 'default_api_key'):
            return jsonify({
                'success': False,
                'error': 'Invalid or missing API key',
                'message': 'Valid API key required for this endpoint'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_valid_session_api(f):
    """Decorator to require valid session for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session_manager._is_session_valid():
            return jsonify({
                'success': False,
                'error': 'Session expired or invalid',
                'message': 'Please log in again',
                'redirect': '/auth/login'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_payment_api(f):
    """Decorator for rate limiting payment API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = security_manager._get_client_ip()
        
        # Custom rate limiting for payment API
        if not security_manager._check_rate_limit(client_ip, 'payment_api'):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': 'Too many payment requests. Please try again later.'
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

# API Endpoints

@payment_api_bp.route('/api/payment/create-order', methods=['POST'])
@rate_limit_payment_api
@require_valid_session_api
def create_payment_order():
    """
    Create Razorpay order
    
    Request Body:
    {
        "amount": 100.50,
        "currency": "INR",
        "receipt": "receipt_123",
        "notes": {"order_id": "ORD123456"},
        "payment_capture": true
    }
    
    Response:
    {
        "success": true,
        "order": {
            "id": "order_123456",
            "entity": "order",
            "amount": 10050,
            "currency": "INR",
            "status": "created"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        amount = data.get('amount')
        if not amount:
            return jsonify({
                'success': False,
                'error': 'Missing amount',
                'message': 'amount is required'
            }), 400
        
        # Convert and validate amount
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid amount',
                'message': 'Amount must be a valid number'
            }), 400
        
        # Validate amount with Razorpay manager
        is_valid, error_message = razorpay_manager.validate_payment_amount(amount_decimal)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid amount',
                'message': error_message
            }), 400
        
        # Extract other parameters
        currency = data.get('currency', 'INR')
        receipt = data.get('receipt')
        notes = data.get('notes', {})
        payment_capture = data.get('payment_capture', True)
        
        # Create order
        order = razorpay_manager.create_order(
            amount=amount_decimal,
            currency=currency,
            receipt=receipt,
            notes=notes,
            payment_capture=payment_capture
        )
        
        if not order:
            return jsonify({
                'success': False,
                'error': 'Order creation failed',
                'message': 'Unable to create payment order. Please try again.'
            }), 500
        
        # Log order creation
        security_manager._log_security_event(
            'PAYMENT_ORDER_CREATED',
            security_manager._get_client_ip(),
            f"Payment order created: {order.get('id')} for amount {amount}",
            'low'
        )
        
        return jsonify({
            'success': True,
            'order': order,
            'amount_formatted': f"₹{amount_decimal:.2f}",
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in create_payment_order: {e}")
        return jsonify({
            'success': False,
            'error': 'Order creation error',
            'message': 'An error occurred while creating the payment order'
        }), 500

@payment_api_bp.route('/api/payment/verify-signature', methods=['POST'])
@rate_limit_payment_api
@require_valid_session_api
def verify_payment_signature():
    """
    Verify payment signature
    
    Request Body:
    {
        "razorpay_order_id": "order_123456",
        "razorpay_payment_id": "pay_123456",
        "razorpay_signature": "signature_hash"
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "message": "Payment signature verified successfully"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields',
                'message': 'razorpay_order_id, razorpay_payment_id, and razorpay_signature are required'
            }), 400
        
        # Verify signature
        is_valid = razorpay_manager.verify_payment_signature(
            razorpay_order_id,
            razorpay_payment_id,
            razorpay_signature
        )
        
        # Log verification attempt
        security_manager._log_security_event(
            'PAYMENT_SIGNATURE_VERIFICATION',
            security_manager._get_client_ip(),
            f"Payment signature verification: {'valid' if is_valid else 'invalid'} for order {razorpay_order_id}",
            'high' if not is_valid else 'low'
        )
        
        if not is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid signature',
                'message': 'Payment signature verification failed. Possible tampering detected.'
            }), 400
        
        return jsonify({
            'success': True,
            'valid': True,
            'message': 'Payment signature verified successfully',
            'payment_id': razorpay_payment_id,
            'order_id': razorpay_order_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in verify_payment_signature: {e}")
        return jsonify({
            'success': False,
            'error': 'Signature verification error',
            'message': 'An error occurred during signature verification'
        }), 500

@payment_api_bp.route('/api/payment/capture', methods=['POST'])
@rate_limit_payment_api
@require_valid_session_api
def capture_payment():
    """
    Capture payment
    
    Request Body:
    {
        "payment_id": "pay_123456",
        "amount": 100.50
    }
    
    Response:
    {
        "success": true,
        "payment": {
            "id": "pay_123456",
            "entity": "payment",
            "amount": 10050,
            "currency": "INR",
            "status": "captured"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        payment_id = data.get('payment_id')
        amount = data.get('amount')
        
        if not payment_id:
            return jsonify({
                'success': False,
                'error': 'Missing payment ID',
                'message': 'payment_id is required'
            }), 400
        
        # Convert amount if provided
        amount_decimal = None
        if amount:
            try:
                amount_decimal = Decimal(str(amount))
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid amount',
                    'message': 'Amount must be a valid number'
                }), 400
        
        # Capture payment
        payment = razorpay_manager.capture_payment(payment_id, amount_decimal)
        
        if not payment:
            return jsonify({
                'success': False,
                'error': 'Payment capture failed',
                'message': 'Unable to capture payment. Please check the payment ID and try again.'
            }), 500
        
        # Log payment capture
        security_manager._log_security_event(
            'PAYMENT_CAPTURED',
            security_manager._get_client_ip(),
            f"Payment captured: {payment_id} for amount {amount}",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'payment': payment,
            'amount_formatted': f"₹{amount_decimal:.2f}" if amount_decimal else None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in capture_payment: {e}")
        return jsonify({
            'success': False,
            'error': 'Payment capture error',
            'message': 'An error occurred while capturing the payment'
        }), 500

@payment_api_bp.route('/api/payment/refund', methods=['POST'])
@rate_limit_payment_api
@require_valid_session_api
def process_refund():
    """
    Process refund
    
    Request Body:
    {
        "payment_id": "pay_123456",
        "amount": 50.25,
        "reason": "Customer requested refund"
    }
    
    Response:
    {
        "success": true,
        "refund": {
            "id": "refund_123456",
            "entity": "refund",
            "amount": 5025,
            "currency": "INR",
            "status": "processed"
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        payment_id = data.get('payment_id')
        if not payment_id:
            return jsonify({
                'success': False,
                'error': 'Missing payment ID',
                'message': 'payment_id is required'
            }), 400
        
        # Convert amount if provided
        amount = data.get('amount')
        amount_decimal = None
        if amount:
            try:
                amount_decimal = Decimal(str(amount))
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid amount',
                    'message': 'Amount must be a valid number'
                }), 400
        
        # Process refund
        refund = razorpay_manager.refund_payment(payment_id, amount_decimal)
        
        if not refund:
            return jsonify({
                'success': False,
                'error': 'Refund failed',
                'message': 'Unable to process refund. Please check the payment ID and try again.'
            }), 500
        
        # Log refund
        reason = data.get('reason', 'No reason provided')
        security_manager._log_security_event(
            'PAYMENT_REFUND',
            security_manager._get_client_ip(),
            f"Refund processed: {refund.get('id')} for payment {payment_id}, reason: {reason}",
            'medium'
        )
        
        return jsonify({
            'success': True,
            'refund': refund,
            'amount_formatted': f"₹{amount_decimal:.2f}" if amount_decimal else None,
            'reason': reason,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process_refund: {e}")
        return jsonify({
            'success': False,
            'error': 'Refund processing error',
            'message': 'An error occurred while processing the refund'
        }), 500

@payment_api_bp.route('/api/payment/methods', methods=['GET'])
@rate_limit_payment_api
def get_payment_methods():
    """
    Get available payment methods
    
    Response:
    {
        "success": true,
        "methods": {
            "card": {...},
            "upi": {...},
            "netbanking": {...},
            "wallet": {...},
            "emi": {...}
        }
    }
    """
    try:
        # Get payment methods from Razorpay manager
        methods = razorpay_manager.get_payment_methods()
        
        # Add additional information
        for method_key, method_info in methods.items():
            method_info['available'] = True
            method_info['recommended'] = method_key in ['upi', 'card']
            method_info['processing_time'] = _get_processing_time(method_key)
            method_info['fees'] = _get_method_fees(method_key)
        
        return jsonify({
            'success': True,
            'methods': methods,
            'default_method': 'card',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_payment_methods: {e}")
        return jsonify({
            'success': False,
            'error': 'Payment methods retrieval error',
            'message': 'An error occurred while retrieving payment methods'
        }), 500

@payment_api_bp.route('/api/payment/emi-plans', methods=['GET'])
@rate_limit_payment_api
def get_emi_plans():
    """
    Get EMI plans
    
    Query Parameters:
    - amount: Loan amount
    - tenure: Preferred tenure in months
    
    Response:
    {
        "success": true,
        "plans": [
            {
                "tenure": 3,
                "interest_rate": 15.0,
                "monthly_emi": 3450.50,
                "total_amount": 10351.50,
                "total_interest": 351.50
            }
        ]
    }
    """
    try:
        # Get query parameters
        amount = request.args.get('amount', '10000')
        preferred_tenure = request.args.get('tenure', type=int)
        
        # Convert amount
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid amount',
                'message': 'Amount must be a valid number'
            }), 400
        
        # Generate EMI plans
        plans = []
        tenures = [3, 6, 9, 12, 18, 24]
        
        if preferred_tenure and preferred_tenure in tenures:
            tenures = [preferred_tenure]
        
        for tenure in tenures:
            # Calculate EMI details
            emi_details = razorpay_manager.process_emi_payment(
                amount_decimal,
                tenure,
                15.0  # Default interest rate
            )
            
            if emi_details and 'error' not in emi_details:
                plans.append(emi_details)
        
        # Sort by tenure
        plans.sort(key=lambda x: x['tenure_months'])
        
        return jsonify({
            'success': True,
            'plans': plans,
            'principal_amount': float(amount_decimal),
            'currency': 'INR',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_emi_plans: {e}")
        return jsonify({
            'success': False,
            'error': 'EMI plans retrieval error',
            'message': 'An error occurred while retrieving EMI plans'
        }), 500

@payment_api_bp.route('/api/payment/transactions', methods=['GET'])
@rate_limit_payment_api
@require_valid_session_api
def get_payment_history():
    """
    Get payment history
    
    Query Parameters:
    - from_date: Start date (YYYY-MM-DD)
    - to_date: End date (YYYY-MM-DD)
    - count: Number of transactions (default: 10)
    - skip: Number of transactions to skip (default: 0)
    
    Response:
    {
        "success": true,
        "transactions": [...],
        "pagination": {...}
    }
    """
    try:
        # Get query parameters
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        count = request.args.get('count', 10, type=int)
        skip = request.args.get('skip', 0, type=int)
        
        # Validate parameters
        count = min(max(count, 1), 100)  # Limit between 1 and 100
        skip = max(skip, 0)
        
        # Convert dates
        from_date = None
        to_date = None
        
        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid from_date',
                    'message': 'from_date must be in YYYY-MM-DD format'
                }), 400
        
        if to_date_str:
            try:
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid to_date',
                    'message': 'to_date must be in YYYY-MM-DD format'
                }), 400
        
        # Get transaction history
        transactions = razorpay_manager.get_transaction_history(from_date, to_date, count, skip)
        
        if not transactions:
            return jsonify({
                'success': False,
                'error': 'Transaction retrieval failed',
                'message': 'Unable to retrieve transaction history'
            }), 500
        
        # Process transactions
        processed_transactions = []
        for transaction in transactions.get('items', []):
            processed_transaction = {
                'id': transaction.get('id'),
                'entity': transaction.get('entity'),
                'amount': transaction.get('amount', 0) / 100,  # Convert from paise
                'currency': transaction.get('currency', 'INR'),
                'status': transaction.get('status'),
                'method': transaction.get('method'),
                'created_at': transaction.get('created_at'),
                'amount_formatted': f"₹{transaction.get('amount', 0) / 100:.2f}",
                'status_description': razorpay_manager.get_payment_status_description(transaction.get('status'))
            }
            processed_transactions.append(processed_transaction)
        
        # Create pagination info
        total_count = transactions.get('count', 0)
        pagination = {
            'count': len(processed_transactions),
            'skip': skip,
            'total': total_count,
            'has_more': (skip + count) < total_count
        }
        
        return jsonify({
            'success': True,
            'transactions': processed_transactions,
            'pagination': pagination,
            'filters': {
                'from_date': from_date_str,
                'to_date': to_date_str,
                'count': count,
                'skip': skip
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_payment_history: {e}")
        return jsonify({
            'success': False,
            'error': 'Transaction history retrieval error',
            'message': 'An error occurred while retrieving transaction history'
        }), 500

@payment_api_bp.route('/api/payment/webhook', methods=['POST'])
def process_webhook():
    """
    Process Razorpay webhooks
    
    Request Headers:
    X-Razorpay-Signature: Webhook signature
    
    Request Body:
    {
        "event": "payment.captured",
        "payload": {...}
    }
    
    Response:
    {
        "success": true,
        "message": "Webhook processed successfully"
    }
    """
    try:
        # Get webhook signature
        webhook_signature = request.headers.get('X-Razorpay-Signature')
        if not webhook_signature:
            return jsonify({
                'success': False,
                'error': 'Missing signature',
                'message': 'Webhook signature is required'
            }), 400
        
        # Get webhook body
        webhook_body = request.get_data(as_text=True)
        
        # Verify signature
        if not razorpay_manager.verify_webhook_signature(webhook_body, webhook_signature):
            security_manager._log_security_event(
                'INVALID_WEBHOOK_SIGNATURE',
                security_manager._get_client_ip(),
                'Invalid webhook signature received',
                'high'
            )
            return jsonify({
                'success': False,
                'error': 'Invalid signature',
                'message': 'Webhook signature verification failed'
            }), 400
        
        # Parse webhook data
        webhook_data = request.get_json()
        if not webhook_data:
            return jsonify({
                'success': False,
                'error': 'Invalid webhook data',
                'message': 'Webhook data must be valid JSON'
            }), 400
        
        # Process webhook
        success, message, data = razorpay_manager.process_webhook(webhook_data)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Webhook processing failed',
                'message': message
            }), 400
        
        # Log webhook processing
        security_manager._log_security_event(
            'WEBHOOK_PROCESSED',
            security_manager._get_client_ip(),
            f"Webhook processed: {webhook_data.get('event')}",
            'low'
        )
        
        return jsonify({
            'success': True,
            'message': 'Webhook processed successfully',
            'event_type': webhook_data.get('event'),
            'processed_data': data,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in process_webhook: {e}")
        return jsonify({
            'success': False,
            'error': 'Webhook processing error',
            'message': 'An error occurred during webhook processing'
        }), 500

@payment_api_bp.route('/api/payment/analytics', methods=['GET'])
@rate_limit_payment_api
@require_valid_session_api
def get_payment_analytics():
    """
    Get payment analytics
    
    Query Parameters:
    - from_date: Start date (YYYY-MM-DD)
    - to_date: End date (YYYY-MM-DD)
    
    Response:
    {
        "success": true,
        "analytics": {
            "total_transactions": 100,
            "total_amount": 50000.00,
            "success_rate": 95.5,
            "payment_methods": {...},
            "daily_breakdown": {...}
        }
    }
    """
    try:
        # Get query parameters
        from_date_str = request.args.get('from_date')
        to_date_str = request.args.get('to_date')
        
        # Convert dates
        from_date = None
        to_date = None
        
        if from_date_str:
            try:
                from_date = datetime.strptime(from_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid from_date',
                    'message': 'from_date must be in YYYY-MM-DD format'
                }), 400
        
        if to_date_str:
            try:
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid to_date',
                    'message': 'to_date must be in YYYY-MM-DD format'
                }), 400
        
        # Get analytics
        analytics = razorpay_manager.get_payment_analytics(from_date, to_date)
        
        # Add additional analytics
        analytics.update({
            'trends': _calculate_payment_trends(analytics),
            'insights': _generate_payment_insights(analytics),
            'recommendations': _get_payment_recommendations(analytics)
        })
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period': {
                'from_date': from_date_str,
                'to_date': to_date_str
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_payment_analytics: {e}")
        return jsonify({
            'success': False,
            'error': 'Analytics retrieval error',
            'message': 'An error occurred while retrieving payment analytics'
        }), 500

@payment_api_bp.route('/api/payment/validate-method', methods=['POST'])
@rate_limit_payment_api
@require_valid_session_api
def validate_payment_method():
    """
    Validate payment method details
    
    Request Body:
    {
        "method": "card",
        "details": {
            "card_number": "4111111111111111",
            "expiry": "12/25",
            "cvv": "123",
            "name": "John Doe"
        }
    }
    
    Response:
    {
        "success": true,
        "valid": true,
        "message": "Payment method is valid"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request',
                'message': 'Request must contain JSON data'
            }), 400
        
        # Validate required fields
        method = data.get('method')
        details = data.get('details', {})
        
        if not method:
            return jsonify({
                'success': False,
                'error': 'Missing payment method',
                'message': 'method is required'
            }), 400
        
        # Validate payment method
        is_valid, message = razorpay_manager.validate_payment_method(method, details)
        
        # Log validation attempt
        security_manager._log_security_event(
            'PAYMENT_METHOD_VALIDATION',
            security_manager._get_client_ip(),
            f"Payment method validation: {method} - {'valid' if is_valid else 'invalid'}",
            'medium' if not is_valid else 'low'
        )
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': message if is_valid else f"Validation failed: {message}",
            'method': method,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in validate_payment_method: {e}")
        return jsonify({
            'success': False,
            'error': 'Payment method validation error',
            'message': 'An error occurred during payment method validation'
        }), 500

# Helper functions

def _get_processing_time(method: str) -> str:
    """Get processing time for payment method"""
    processing_times = {
        'card': 'instant',
        'upi': 'instant',
        'netbanking': '2-3 business days',
        'wallet': 'instant',
        'emi': 'instant'
    }
    return processing_times.get(method, 'unknown')

def _get_method_fees(method: str) -> Dict[str, Any]:
    """Get fee information for payment method"""
    fees = {
        'card': {
            'percentage': 2.0,
            'fixed': 0,
            'description': '2% + GST'
        },
        'upi': {
            'percentage': 1.99,
            'fixed': 0,
            'description': '1.99% + GST'
        },
        'netbanking': {
            'percentage': 2.0,
            'fixed': 0,
            'description': '2.0% + GST'
        },
        'wallet': {
            'percentage': 2.0,
            'fixed': 0,
            'description': '2.0% + GST'
        },
        'emi': {
            'percentage': 3.0,
            'fixed': 0,
            'description': '3.0% + GST'
        }
    }
    return fees.get(method, {
        'percentage': 0,
        'fixed': 0,
        'description': 'No fees'
    })

def _calculate_payment_trends(analytics: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate payment trends from analytics"""
    try:
        daily_breakdown = analytics.get('daily_breakdown', {})
        
        if not daily_breakdown:
            return {
                'volume_trend': 'stable',
                'success_rate_trend': 'stable',
                'preferred_method': 'unknown'
            }
        
        # Calculate volume trend (simplified)
        volumes = list(daily_breakdown.values())
        if len(volumes) >= 2:
            recent_avg = sum(volumes[-3:]) / min(3, len(volumes))
            earlier_avg = sum(volumes[:-3]) / max(1, len(volumes) - 3)
            
            if recent_avg > earlier_avg * 1.1:
                volume_trend = 'increasing'
            elif recent_avg < earlier_avg * 0.9:
                volume_trend = 'decreasing'
            else:
                volume_trend = 'stable'
        else:
            volume_trend = 'insufficient_data'
        
        return {
            'volume_trend': volume_trend,
            'success_rate_trend': 'stable',  # Would need more data for this
            'preferred_method': 'card'  # Most common method
        }
    except:
        return {
            'volume_trend': 'unknown',
            'success_rate_trend': 'unknown',
            'preferred_method': 'unknown'
        }

def _generate_payment_insights(analytics: Dict[str, Any]) -> List[str]:
    """Generate insights from payment analytics"""
    insights = []
    
    try:
        total_transactions = analytics.get('total_transactions', 0)
        success_rate = analytics.get('success_rate', 0)
        payment_methods = analytics.get('payment_methods', {})
        
        # Volume insights
        if total_transactions > 100:
            insights.append("High transaction volume detected")
        elif total_transactions < 10:
            insights.append("Low transaction volume - consider marketing efforts")
        
        # Success rate insights
        if success_rate > 95:
            insights.append("Excellent payment success rate")
        elif success_rate < 90:
            insights.append("Payment success rate needs improvement")
        
        # Method insights
        if payment_methods:
            most_used_method = max(payment_methods.items(), key=lambda x: x[1].get('count', 0))
            insights.append(f"Most used payment method: {most_used_method[0]}")
        
    except:
        insights.append("Unable to generate insights")
    
    return insights

def _get_payment_recommendations(analytics: Dict[str, Any]) -> List[str]:
    """Get recommendations based on payment analytics"""
    recommendations = []
    
    try:
        success_rate = analytics.get('success_rate', 0)
        payment_methods = analytics.get('payment_methods', {})
        
        # Success rate recommendations
        if success_rate < 90:
            recommendations.append("Review payment failure reasons and optimize checkout process")
        
        # Method recommendations
        if payment_methods:
            # Check if UPI is underutilized
            upi_usage = payment_methods.get('upi', {}).get('count', 0)
            total_usage = sum(method.get('count', 0) for method in payment_methods.values())
            
            if total_usage > 0 and (upi_usage / total_usage) < 0.2:
                recommendations.append("Promote UPI payments for better success rates")
        
        # General recommendations
        recommendations.extend([
            "Monitor payment analytics regularly",
            "Consider offering multiple payment options",
            "Implement retry mechanisms for failed payments"
        ])
        
    except:
        recommendations.append("Review payment configuration")
    
    return recommendations

# Error handlers for payment API
@payment_api_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'The request is invalid or malformed'
    }), 400

@payment_api_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Authentication is required for this endpoint'
    }), 401

@payment_api_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many payment requests. Please try again later.'
    }), 429

@payment_api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500