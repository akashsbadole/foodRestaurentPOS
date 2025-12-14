"""
Razorpay Payment Routes for Flask POS Application
Handles Razorpay payment processing, webhooks, and integration
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, session
from flask_login import login_required, current_user
from models import db, Order, Payment
from forms import PaymentForm
from utils.razorpay_manager import (
    create_razorpay_order, capture_razorpay_payment, verify_razorpay_signature,
    get_razorpay_payment_details, validate_razorpay_amount, is_razorpay_configured
)
from utils.security_manager import require_security_csrf_token, log_security_event
from utils.session_manager import require_valid_session
from utils.offline_manager import store_offline_payment
from datetime import datetime
from decimal import Decimal
import logging

razorpay_bp = Blueprint('razorpay', __name__)

@razorpay_bp.route('/create_order/<int:order_id>', methods=['POST'])
@login_required
@require_security_csrf_token
def create_razorpay_order(order_id):
    """Create Razorpay order for payment"""
    try:
        # Get order details
        order = Order.query.get_or_404(order_id)
        
        # Validate order
        if order.status not in ['New', 'In Progress']:
            return jsonify({
                'success': False,
                'message': 'Order cannot be paid - invalid status'
            }), 400
        
        if order.items.count() == 0:
            return jsonify({
                'success': False,
                'message': 'Cannot pay for empty order'
            }), 400
        
        # Validate amount
        amount = order.grand_total
        is_valid, message = validate_razorpay_amount(amount)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        # Create Razorpay order
        razorpay_order = create_razorpay_order(
            amount=amount,
            receipt=f"order_{order.order_number}",
            notes={
                'order_id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'customer_mobile': order.customer_mobile,
                'user_id': current_user.id
            }
        )
        
        if not razorpay_order:
            return jsonify({
                'success': False,
                'message': 'Failed to create payment order'
            }), 500
        
        # Store Razorpay order ID in session
        session['razorpay_order_id'] = razorpay_order['id']
        session['razorpay_order_amount'] = float(amount)
        
        return jsonify({
            'success': True,
            'razorpay_order': razorpay_order,
            'order_id': order.id,
            'order_number': order.order_number,
            'amount': float(amount),
            'currency': 'INR',
            'key_id': current_app.config.get('RAZORPAY_KEY_ID'),
            'callback_url': url_for('razorpay.payment_callback', _external=True)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error creating Razorpay order: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@razorpay_bp.route('/payment/callback')
@login_required
def payment_callback():
    """Handle Razorpay payment callback"""
    try:
        # Get payment details from request
        razorpay_order_id = request.form.get('razorpay_order_id')
        razorpay_payment_id = request.form.get('razorpay_payment_id')
        razorpay_signature = request.form.get('razorpay_signature')
        
        # Verify required parameters
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            flash('Invalid payment response', 'error')
            return redirect(url_for('orders.view_order', order_id=session.get('pending_order_id')))
        
        # Verify signature
        if not verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
            log_security_event('INVALID_RAZORPAY_SIGNATURE', f'Invalid signature for payment {razorpay_payment_id}')
            flash('Invalid payment signature', 'error')
            return redirect(url_for('orders.view_order', order_id=session.get('pending_order_id')))
        
        # Get payment details from Razorpay
        payment_details = get_razorpay_payment_details(razorpay_payment_id)
        if not payment_details:
            flash('Failed to verify payment', 'error')
            return redirect(url_for('orders.view_order', order_id=session.get('pending_order_id')))
        
        # Process payment
        success, message = process_razorpay_payment_result(payment_details)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        # Redirect to order view
        order_id = session.get('pending_order_id')
        if order_id:
            return redirect(url_for('orders.view_order', order_id=order_id))
        else:
            return redirect(url_for('dashboard.index'))
        
    except Exception as e:
        current_app.logger.error(f"Error processing Razorpay callback: {e}")
        flash('Payment processing failed', 'error')
        return redirect(url_for('dashboard.index'))

@razorpay_bp.route('/payment/page/<int:order_id>')
@login_required
def payment_page(order_id):
    """Razorpay payment page"""
    try:
        # Get order details
        order = Order.query.get_or_404(order_id)
        
        # Validate order
        if order.status not in ['New', 'In Progress']:
            flash('Order cannot be paid - invalid status', 'error')
            return redirect(url_for('orders.view_order', order_id=order_id))
        
        # Store pending order ID in session
        session['pending_order_id'] = order_id
        
        # Get Razorpay configuration
        razorpay_config = {
            'key_id': current_app.config.get('RAZORPAY_KEY_ID'),
            'currency': 'INR',
            'amount': float(order.grand_total),
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_email': current_user.email_decrypted if current_user else '',
            'customer_mobile': order.customer_mobile,
            'callback_url': url_for('razorpay.payment_callback', _external=True)
        }
        
        return render_template('razorpay/payment.html', 
                            order=order, 
                            razorpay_config=razorpay_config)
        
    except Exception as e:
        current_app.logger.error(f"Error loading Razorpay payment page: {e}")
        flash('Failed to load payment page', 'error')
        return redirect(url_for('orders.view_order', order_id=order_id))

@razorpay_bp.route('/capture/<int:order_id>', methods=['POST'])
@login_required
@require_security_csrf_token
def capture_payment(order_id):
    """Capture Razorpay payment after authorization"""
    try:
        # Get order details
        order = Order.query.get_or_404(order_id)
        
        # Get payment details from request
        razorpay_payment_id = request.json.get('razorpay_payment_id')
        
        if not razorpay_payment_id:
            return jsonify({
                'success': False,
                'message': 'Payment ID is required'
            }), 400
        
        # Capture payment
        capture_result = capture_razorpay_payment(razorpay_payment_id, order.grand_total)
        
        if not capture_result:
            return jsonify({
                'success': False,
                'message': 'Failed to capture payment'
            }), 500
        
        # Process payment result
        success, message = process_razorpay_payment_result(capture_result, order)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'order_number': order.order_number
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
    except Exception as e:
        current_app.logger.error(f"Error capturing Razorpay payment: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@razorpay_bp.route('/check/<int:order_id>')
@login_required
def check_payment_status(order_id):
    """Check Razorpay payment status"""
    try:
        # Get order details
        order = Order.query.get_or_404(order_id)
        
        # Get Razorpay order ID from session
        razorpay_order_id = session.get('razorpay_order_id')
        
        if not razorpay_order_id:
            return jsonify({
                'success': False,
                'message': 'No Razorpay order found'
            }), 404
        
        # Get payment details from Razorpay
        payment_details = get_razorpay_payment_details(razorpay_order_id)
        
        if not payment_details:
            return jsonify({
                'success': False,
                'message': 'Payment not found'
            }), 404
        
        return jsonify({
            'success': True,
            'payment_status': payment_details.get('status'),
            'payment_method': payment_details.get('method'),
            'amount': payment_details.get('amount'),
            'currency': payment_details.get('currency'),
            'created_at': payment_details.get('created_at')
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking Razorpay payment status: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@razorpay_bp.route('/methods')
@login_required
def payment_methods():
    """Get available Razorpay payment methods"""
    try:
        from utils.razorpay_manager import razorpay_manager
        
        methods = razorpay_manager.get_payment_methods()
        
        return jsonify({
            'success': True,
            'methods': methods,
            'configured': is_razorpay_configured()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting Razorpay payment methods: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@razorpay_bp.route('/history')
@login_required
def payment_history():
    """Get Razorpay payment history"""
    try:
        from utils.razorpay_manager import razorpay_manager
        
        # Get query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        count = request.args.get('count', 10, type=int)
        skip = request.args.get('skip', 0, type=int)
        
        # Parse dates
        from_dt = None
        to_dt = None
        
        if from_date:
            try:
                from_dt = datetime.fromisoformat(from_date)
            except ValueError:
                pass
        
        if to_date:
            try:
                to_dt = datetime.fromisoformat(to_date)
            except ValueError:
                pass
        
        # Get transaction history
        history = razorpay_manager.get_transaction_history(
            from_date=from_dt, 
            to_date=to_dt, 
            count=count, 
            skip=skip
        )
        
        return jsonify({
            'success': True,
            'history': history,
            'from_date': from_date,
            'to_date': to_date,
            'count': count,
            'skip': skip
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting Razorpay payment history: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@razorpay_bp.route('/config')
@login_required
def configuration():
    """Get Razorpay configuration"""
    try:
        from utils.razorpay_manager import razorpay_manager
        
        config = razorpay_manager.get_configuration_info()
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting Razorpay configuration: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

def process_razorpay_payment_result(payment_details, order=None):
    """Process Razorpay payment result"""
    try:
        payment_id = payment_details.get('id')
        status = payment_details.get('status')
        amount = Decimal(payment_details.get('amount', 0)) / 100
        method = payment_details.get('method')
        email = payment_details.get('email')
        contact = payment_details.get('contact')
        
        # Get order if not provided
        if not order:
            order_id = session.get('pending_order_id')
            if order_id:
                order = Order.query.get(order_id)
        
        if not order:
            return False, 'Order not found'
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(
            razorpay_payment_id=payment_id
        ).first()
        
        if existing_payment:
            return False, 'Payment already processed'
        
        if status == 'captured':
            # Payment successful - create payment record
            payment = Payment(
                order_id=order.id,
                payment_mode='Razorpay',
                amount=amount,
                processed_by=current_user.id,
                reference_number=payment_id,
                payment_details={
                    'razorpay_payment_id': payment_id,
                    'method': method,
                    'email': email,
                    'contact': contact,
                    'captured_at': payment_details.get('created_at'),
                    'status': status
                }
            )
            
            db.session.add(payment)
            
            # Update order status
            order.status = 'Completed'
            order.grand_total = amount  # Ensure amount matches
            
            # Update table availability if dine-in
            if order.order_type == 'Dine-in' and order.table_id:
                table = order.table
                if table:
                    table.status = 'Available'
            
            db.session.commit()
            
            # Clear session data
            session.pop('razorpay_order_id', None)
            session.pop('razorpay_order_amount', None)
            session.pop('pending_order_id', None)
            
            return True, f'Payment of ₹{amount:.2f} processed successfully via Razorpay'
        
        elif status == 'failed':
            # Payment failed
            error_description = payment_details.get('error_description', 'Payment failed')
            
            # Create failed payment record for tracking
            payment = Payment(
                order_id=order.id,
                payment_mode='Razorpay',
                amount=amount,
                processed_by=current_user.id,
                reference_number=payment_id,
                payment_details={
                    'razorpay_payment_id': payment_id,
                    'method': method,
                    'status': status,
                    'error_description': error_description,
                    'failed_at': payment_details.get('created_at')
                }
            )
            
            payment.status = 'Failed'
            db.session.add(payment)
            db.session.commit()
            
            return False, f'Payment failed: {error_description}'
        
        elif status == 'authorized':
            # Payment authorized but not captured
            return False, 'Payment authorized but not yet captured'
        
        else:
            # Other status
            return False, f'Payment status: {status}'
        
    except Exception as e:
        current_app.logger.error(f"Error processing Razorpay payment result: {e}")
        return False, 'Payment processing failed'

@razorpay_bp.route('/test')
@login_required
def test_configuration():
    """Test Razorpay configuration"""
    try:
        if not is_razorpay_configured():
            return jsonify({
                'success': False,
                'message': 'Razorpay not configured'
            }), 400
        
        from utils.razorpay_manager import razorpay_manager
        
        # Test API connection
        balance = razorpay_manager.get_account_balance()
        
        if balance is not None:
            return jsonify({
                'success': True,
                'message': 'Razorpay configuration is valid',
                'balance': balance
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect to Razorpay API'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"Error testing Razorpay configuration: {e}")
        return jsonify({
            'success': False,
            'message': 'Configuration test failed'
        }), 500