"""
Razorpay Payment Integration Manager for Flask POS Application
Provides comprehensive Razorpay payment processing with security and error handling
"""

import os
import json
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from flask import current_app, request, session
import logging
from decimal import Decimal

class RazorpayManager:
    """Razorpay payment processing manager"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = logging.getLogger(__name__)
        self.api_base_url = 'https://api.razorpay.com/v1'
        
        # Razorpay configuration
        self.key_id = None
        self.key_secret = None
        self.webhook_secret = None
        self.test_mode = True
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Razorpay manager with Flask app"""
        self.app = app
        
        # Load configuration
        self.key_id = app.config.get('RAZORPAY_KEY_ID') or os.environ.get('RAZORPAY_KEY_ID')
        self.key_secret = app.config.get('RAZORPAY_KEY_SECRET') or os.environ.get('RAZORPAY_KEY_SECRET')
        self.webhook_secret = app.config.get('RAZORPAY_WEBHOOK_SECRET') or os.environ.get('RAZORPAY_WEBHOOK_SECRET')
        self.test_mode = app.config.get('RAZORPAY_TEST_MODE', True)
        
        if not self.key_id or not self.key_secret:
            self.logger.warning("Razorpay credentials not configured")
        
        self.logger.info("Razorpay manager initialized")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Razorpay API"""
        auth_string = f"{self.key_id}:{self.key_secret}"
        import base64
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        return {
            'Authorization': f'Basic {auth_encoded}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_api_request(self, endpoint: str, method: str = 'GET', data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make API request to Razorpay"""
        try:
            url = f"{self.api_base_url}/{endpoint}"
            headers = self._get_auth_headers()
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Razorpay API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in Razorpay API request: {e}")
            return None
    
    def create_order(self, amount: Decimal, currency: str = 'INR', 
                   receipt: str = None, notes: Dict[str, Any] = None,
                   payment_capture: bool = True) -> Optional[Dict[str, Any]]:
        """Create Razorpay order"""
        try:
            # Convert amount to paise (multiply by 100)
            amount_paise = int(amount * 100)
            
            order_data = {
                'amount': amount_paise,
                'currency': currency,
                'receipt': receipt or f"receipt_{datetime.utcnow().timestamp()}",
                'notes': notes or {},
                'payment_capture': payment_capture
            }
            
            response = self._make_api_request('orders', 'POST', order_data)
            
            if response:
                self.logger.info(f"Razorpay order created: {response.get('id')}")
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating Razorpay order: {e}")
            return None
    
    def capture_payment(self, payment_id: str, amount: Decimal) -> Optional[Dict[str, Any]]:
        """Capture a Razorpay payment"""
        try:
            amount_paise = int(amount * 100)
            capture_data = {
                'amount': amount_paise,
                'currency': 'INR'
            }
            
            response = self._make_api_request(f'payments/{payment_id}/capture', 'POST', capture_data)
            
            if response:
                self.logger.info(f"Razorpay payment captured: {payment_id}")
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error capturing Razorpay payment: {e}")
            return None
    
    def refund_payment(self, payment_id: str, amount: Decimal = None) -> Optional[Dict[str, Any]]:
        """Refund a Razorpay payment"""
        try:
            refund_data = {}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            response = self._make_api_request(f'payments/{payment_id}/refund', 'POST', refund_data)
            
            if response:
                self.logger.info(f"Razorpay refund processed: {response.get('id')}")
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error processing Razorpay refund: {e}")
            return None
    
    def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment details from Razorpay"""
        try:
            response = self._make_api_request(f'payments/{payment_id}')
            
            if response:
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Razorpay payment details: {e}")
            return None
    
    def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details from Razorpay"""
        try:
            response = self._make_api_request(f'orders/{order_id}')
            
            if response:
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Razorpay order details: {e}")
            return None
    
    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, 
                            razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature"""
        try:
            # Create signature string
            signature_string = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.key_secret.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, razorpay_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying Razorpay signature: {e}")
            return False
    
    def verify_webhook_signature(self, webhook_body: str, webhook_signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                webhook_body.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, webhook_signature)
            
        except Exception as e:
            self.logger.error(f"Error verifying Razorpay webhook signature: {e}")
            return False
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Process Razorpay webhook"""
        try:
            event_type = webhook_data.get('event', '')
            payload = webhook_data.get('payload', {})
            
            self.logger.info(f"Processing Razorpay webhook: {event_type}")
            
            if event_type == 'payment.captured':
                return self._handle_payment_captured(payload)
            elif event_type == 'payment.failed':
                return self._handle_payment_failed(payload)
            elif event_type == 'payment.refunded':
                return self._handle_payment_refunded(payload)
            elif event_type == 'order.paid':
                return self._handle_order_paid(payload)
            else:
                self.logger.warning(f"Unhandled webhook event: {event_type}")
                return False, f"Unhandled event: {event_type}", webhook_data
            
        except Exception as e:
            self.logger.error(f"Error processing Razorpay webhook: {e}")
            return False, f"Webhook processing error: {e}", webhook_data
    
    def _handle_payment_captured(self, payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle payment captured webhook"""
        try:
            payment_entity = payload.get('payment', {}).get('entity', {})
            order_entity = payload.get('order', {}).get('entity', {})
            
            payment_id = payment_entity.get('id')
            order_id = order_entity.get('id')
            amount = Decimal(payment_entity.get('amount', 0)) / 100
            currency = payment_entity.get('currency', 'INR')
            status = payment_entity.get('status')
            method = payment_entity.get('method')
            email = payment_entity.get('email')
            contact = payment_entity.get('contact')
            
            if status == 'captured':
                # Payment was successful
                payment_info = {
                    'razorpay_payment_id': payment_id,
                    'razorpay_order_id': order_id,
                    'amount': amount,
                    'currency': currency,
                    'method': method,
                    'email': email,
                    'contact': contact,
                    'status': 'captured',
                    'captured_at': payment_entity.get('created_at'),
                    'webhook_processed_at': datetime.utcnow().isoformat()
                }
                
                self.logger.info(f"Razorpay payment captured successfully: {payment_id}")
                return True, "Payment captured successfully", payment_info
            else:
                self.logger.warning(f"Razorpay payment not captured: {payment_id}, status: {status}")
                return False, f"Payment not captured: {status}", payload
                
        except Exception as e:
            self.logger.error(f"Error handling payment captured webhook: {e}")
            return False, f"Error processing payment captured: {e}", payload
    
    def _handle_payment_failed(self, payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle payment failed webhook"""
        try:
            payment_entity = payload.get('payment', {}).get('entity', {})
            
            payment_id = payment_entity.get('id')
            order_id = payment_entity.get('order_id')
            amount = Decimal(payment_entity.get('amount', 0)) / 100
            error_code = payment_entity.get('error_code')
            error_description = payment_entity.get('error_description')
            
            payment_info = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'amount': amount,
                'error_code': error_code,
                'error_description': error_description,
                'status': 'failed',
                'failed_at': payment_entity.get('created_at'),
                'webhook_processed_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Razorpay payment failed: {payment_id}, error: {error_description}")
            return True, "Payment failed", payment_info
            
        except Exception as e:
            self.logger.error(f"Error handling payment failed webhook: {e}")
            return False, f"Error processing payment failed: {e}", payload
    
    def _handle_payment_refunded(self, payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle payment refunded webhook"""
        try:
            refund_entity = payload.get('refund', {}).get('entity', {})
            payment_entity = refund_entity.get('payment', {})
            
            refund_id = refund_entity.get('id')
            payment_id = payment_entity.get('id')
            amount = Decimal(refund_entity.get('amount', 0)) / 100
            status = refund_entity.get('status')
            
            payment_info = {
                'razorpay_payment_id': payment_id,
                'razorpay_refund_id': refund_id,
                'amount': amount,
                'status': 'refunded',
                'refunded_at': refund_entity.get('created_at'),
                'webhook_processed_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Razorpay payment refunded: {payment_id}, refund: {refund_id}")
            return True, "Payment refunded", payment_info
            
        except Exception as e:
            self.logger.error(f"Error handling payment refunded webhook: {e}")
            return False, f"Error processing payment refunded: {e}", payload
    
    def _handle_order_paid(self, payload: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle order paid webhook"""
        try:
            order_entity = payload.get('order', {}).get('entity', {})
            
            order_id = order_entity.get('id')
            amount = Decimal(order_entity.get('amount', 0)) / 100
            status = order_entity.get('status')
            
            order_info = {
                'razorpay_order_id': order_id,
                'amount': amount,
                'status': status,
                'paid_at': order_entity.get('created_at'),
                'webhook_processed_at': datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Razorpay order paid: {order_id}")
            return True, "Order paid", order_info
            
        except Exception as e:
            self.logger.error(f"Error handling order paid webhook: {e}")
            return False, f"Error processing order paid: {e}", payload
    
    def create_payment_link(self, amount: Decimal, description: str, 
                          customer_email: str = None, customer_contact: str = None,
                          expire_by: datetime = None) -> Optional[Dict[str, Any]]:
        """Create Razorpay payment link"""
        try:
            amount_paise = int(amount * 100)
            
            link_data = {
                'amount': amount_paise,
                'currency': 'INR',
                'accept_partial': False,
                'description': description,
                'reference_id': f"link_{datetime.utcnow().timestamp()}"
            }
            
            if customer_email:
                link_data['customer'] = {'email': customer_email}
            
            if customer_contact:
                if 'customer' not in link_data:
                    link_data['customer'] = {}
                link_data['customer']['contact'] = customer_contact
            
            if expire_by:
                link_data['expire_by'] = int(expire_by.timestamp())
            
            response = self._make_api_request('payment_links', 'POST', link_data)
            
            if response:
                self.logger.info(f"Razorpay payment link created: {response.get('id')}")
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating Razorpay payment link: {e}")
            return None
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Get available payment methods"""
        return {
            'card': {
                'name': 'Card',
                'supported': True,
                'brands': ['Visa', 'Mastercard', 'Maestro', 'Rupay', 'Amex', 'Diners Club']
            },
            'upi': {
                'name': 'UPI',
                'supported': True,
                'apps': ['Google Pay', 'PhonePe', 'Paytm', 'BHIM', 'Amazon Pay']
            },
            'netbanking': {
                'name': 'Net Banking',
                'supported': True,
                'banks': ['HDFC', 'ICICI', 'SBI', 'PNB', 'Axis', 'Kotak', 'Yes Bank']
            },
            'wallet': {
                'name': 'Wallet',
                'supported': True,
                'providers': ['Paytm Wallet', 'PhonePe Wallet', 'Amazon Pay Balance', 'FreeCharge']
            },
            'emi': {
                'name': 'EMI',
                'supported': True,
                'tenures': [3, 6, 9, 12, 18, 24]
            }
        }
    
    def get_transaction_history(self, from_date: datetime = None, to_date: datetime = None,
                           count: int = 10, skip: int = 0) -> Optional[Dict[str, Any]]:
        """Get transaction history from Razorpay"""
        try:
            params = {'count': count, 'skip': skip}
            
            if from_date:
                params['from'] = int(from_date.timestamp())
            
            if to_date:
                params['to'] = int(to_date.timestamp())
            
            # Build query string
            query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
            
            response = self._make_api_request(f'payments?{query_string}')
            
            if response:
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Razorpay transaction history: {e}")
            return None
    
    def get_account_balance(self) -> Optional[Dict[str, Any]]:
        """Get Razorpay account balance"""
        try:
            response = self._make_api_request('balance')
            
            if response:
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting Razorpay account balance: {e}")
            return None
    
    def validate_payment_amount(self, amount: Decimal) -> Tuple[bool, str]:
        """Validate payment amount for Razorpay"""
        try:
            # Minimum amount is ₹1 (100 paise)
            if amount < Decimal('1.00'):
                return False, "Minimum amount is ₹1.00"
            
            # Maximum amount is ₹100,000 (10,000,000 paise)
            if amount > Decimal('100000.00'):
                return False, "Maximum amount is ₹100,000.00"
            
            # Amount should have maximum 2 decimal places
            if amount.as_tuple().exponent < -2:
                return False, "Amount can have maximum 2 decimal places"
            
            return True, "Valid amount"
            
        except Exception as e:
            self.logger.error(f"Error validating payment amount: {e}")
            return False, "Invalid amount format"
    
    def get_payment_status_description(self, status: str) -> str:
        """Get human-readable payment status description"""
        status_descriptions = {
            'created': 'Payment created but not yet processed',
            'authorized': 'Payment authorized by bank',
            'captured': 'Payment captured successfully',
            'refunded': 'Payment refunded',
            'failed': 'Payment failed',
            'pending': 'Payment is being processed'
        }
        
        return status_descriptions.get(status, f'Unknown status: {status}')
    
    def is_configured(self) -> bool:
        """Check if Razorpay is properly configured"""
        return bool(self.key_id and self.key_secret)
    
    def get_payment_analytics(self, from_date: datetime = None, to_date: datetime = None) -> Dict[str, Any]:
        """Get payment analytics and statistics"""
        try:
            # Get transaction history
            transactions = self.get_transaction_history(from_date, to_date, count=1000)
            
            if not transactions or not transactions.get('items'):
                return {
                    'total_transactions': 0,
                    'total_amount': 0,
                    'success_rate': 0,
                    'payment_methods': {},
                    'daily_breakdown': {},
                    'error_analysis': {}
                }
            
            items = transactions['items']
            total_transactions = len(items)
            total_amount = 0
            successful_payments = 0
            payment_methods = {}
            daily_breakdown = {}
            error_analysis = {}
            
            for payment in items:
                amount = Decimal(payment.get('amount', 0)) / 100
                status = payment.get('status')
                method = payment.get('method', 'unknown')
                created_at = payment.get('created_at', '')
                
                # Total amount calculation
                if status == 'captured':
                    total_amount += amount
                    successful_payments += 1
                
                # Payment method breakdown
                if method not in payment_methods:
                    payment_methods[method] = {'count': 0, 'amount': 0}
                payment_methods[method]['count'] += 1
                if status == 'captured':
                    payment_methods[method]['amount'] += amount
                
                # Daily breakdown
                if created_at:
                    try:
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).date().isoformat()
                        if date not in daily_breakdown:
                            daily_breakdown[date] = {'count': 0, 'amount': 0}
                        daily_breakdown[date]['count'] += 1
                        if status == 'captured':
                            daily_breakdown[date]['amount'] += amount
                    except:
                        pass
                
                # Error analysis
                if status == 'failed':
                    error_code = payment.get('error_code', 'unknown')
                    if error_code not in error_analysis:
                        error_analysis[error_code] = 0
                    error_analysis[error_code] += 1
            
            success_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0
            
            return {
                'total_transactions': total_transactions,
                'total_amount': float(total_amount),
                'successful_payments': successful_payments,
                'success_rate': round(success_rate, 2),
                'payment_methods': payment_methods,
                'daily_breakdown': daily_breakdown,
                'error_analysis': error_analysis,
                'average_transaction_value': float(total_amount / successful_payments) if successful_payments > 0 else 0,
                'period': {
                    'from': from_date.isoformat() if from_date else None,
                    'to': to_date.isoformat() if to_date else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting payment analytics: {e}")
            return {
                'error': str(e),
                'total_transactions': 0,
                'total_amount': 0,
                'success_rate': 0
            }
    
    def create_recurring_payment(self, amount: Decimal, frequency: str,
                              start_date: datetime, end_date: datetime = None,
                              customer_email: str = None, customer_contact: str = None) -> Optional[Dict[str, Any]]:
        """Create recurring payment plan"""
        try:
            amount_paise = int(amount * 100)
            
            subscription_data = {
                'plan_id': f"plan_{datetime.utcnow().timestamp()}",
                'total_count': 12,  # Default to 12 months
                'customer_notify': True,
                'quantity': 1,
                'start_at': int(start_date.timestamp()),
                'expire_by': int(end_date.timestamp()) if end_date else None,
                'notes': {
                    'frequency': frequency,
                    'created_by': 'pos_system'
                }
            }
            
            if customer_email:
                subscription_data['customer'] = {'email': customer_email}
            
            if customer_contact:
                if 'customer' not in subscription_data:
                    subscription_data['customer'] = {}
                subscription_data['customer']['contact'] = customer_contact
            
            response = self._make_api_request('subscriptions', 'POST', subscription_data)
            
            if response:
                self.logger.info(f"Recurring payment created: {response.get('id')}")
                return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating recurring payment: {e}")
            return None
    
    def process_emi_payment(self, amount: Decimal, tenure_months: int,
                         interest_rate: float = 0.0) -> Dict[str, Any]:
        """Calculate EMI payment details"""
        try:
            # Simple EMI calculation (can be enhanced with complex formulas)
            monthly_rate = interest_rate / 12 / 100
            monthly_payment = amount * (monthly_rate * (1 + monthly_rate) ** tenure_months) / ((1 + monthly_rate) ** tenure_months - 1)
            total_amount = monthly_payment * tenure_months
            total_interest = total_amount - amount
            
            return {
                'principal_amount': float(amount),
                'tenure_months': tenure_months,
                'interest_rate': interest_rate,
                'monthly_emi': round(float(monthly_payment), 2),
                'total_amount': round(float(total_amount), 2),
                'total_interest': round(float(total_interest), 2),
                'processing_fee': 0.0,  # Can be configured
                'effective_rate': round(float((total_interest / amount) * 100 / tenure_months * 12), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating EMI: {e}")
            return {
                'error': str(e),
                'monthly_emi': 0,
                'total_amount': 0
            }
    
    def validate_payment_method(self, method: str, details: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate payment method details"""
        try:
            if method == 'card':
                card_number = details.get('card_number', '')
                expiry = details.get('expiry', '')
                cvv = details.get('cvv', '')
                name = details.get('name', '')
                
                # Basic card validation
                if not card_number or len(card_number.replace(' ', '')) < 13:
                    return False, "Invalid card number"
                
                if not expiry or '/' not in expiry:
                    return False, "Invalid expiry date"
                
                if not cvv or len(cvv) not in [3, 4]:
                    return False, "Invalid CVV"
                
                if not name or len(name) < 3:
                    return False, "Invalid cardholder name"
            
            elif method == 'upi':
                upi_id = details.get('upi_id', '')
                
                if not upi_id or '@' not in upi_id:
                    return False, "Invalid UPI ID"
                
                if len(upi_id) > 50:
                    return False, "UPI ID too long"
            
            elif method == 'netbanking':
                bank_code = details.get('bank_code', '')
                
                if not bank_code:
                    return False, "Bank selection required"
                
                supported_banks = ['HDFC', 'ICICI', 'SBI', 'PNB', 'Axis', 'Kotak', 'Yes Bank']
                if bank_code not in supported_banks:
                    return False, "Unsupported bank"
            
            elif method == 'wallet':
                wallet_type = details.get('wallet_type', '')
                wallet_number = details.get('wallet_number', '')
                
                if not wallet_type:
                    return False, "Wallet type required"
                
                supported_wallets = ['Paytm Wallet', 'PhonePe Wallet', 'Amazon Pay Balance']
                if wallet_type not in supported_wallets:
                    return False, "Unsupported wallet"
            
            return True, "Valid payment method"
            
        except Exception as e:
            self.logger.error(f"Error validating payment method: {e}")
            return False, f"Validation error: {str(e)}"
    
    def get_configuration_info(self) -> Dict[str, Any]:
        """Get Razorpay configuration information"""
        return {
            'configured': self.is_configured(),
            'test_mode': self.test_mode,
            'key_id': self.key_id[:8] + '...' if self.key_id else None,
            'api_base_url': self.api_base_url,
            'supported_methods': self.get_payment_methods(),
            'minimum_amount': '1.00',
            'maximum_amount': '100000.00',
            'currencies': ['INR'],
            'webhook_configured': bool(self.webhook_secret),
            'features': {
                'recurring_payments': True,
                'emi_support': True,
                'payment_analytics': True,
                'multi_method_support': True,
                'instant_refunds': True,
                'webhook_support': True
            }
        }

# Global Razorpay manager instance
razorpay_manager = RazorpayManager()

# Utility functions
def create_razorpay_order(amount: Decimal, receipt: str = None, notes: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """Create Razorpay order"""
    return razorpay_manager.create_order(amount, 'INR', receipt, notes)

def capture_razorpay_payment(payment_id: str, amount: Decimal) -> Optional[Dict[str, Any]]:
    """Capture Razorpay payment"""
    return razorpay_manager.capture_payment(payment_id, amount)

def refund_razorpay_payment(payment_id: str, amount: Decimal = None) -> Optional[Dict[str, Any]]:
    """Refund Razorpay payment"""
    return razorpay_manager.refund_payment(payment_id, amount)

def verify_razorpay_signature(razorpay_order_id: str, razorpay_payment_id: str, 
                            razorpay_signature: str) -> bool:
    """Verify Razorpay payment signature"""
    return razorpay_manager.verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)

def process_razorpay_webhook(webhook_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Process Razorpay webhook"""
    return razorpay_manager.process_webhook(webhook_data)

def get_razorpay_payment_details(payment_id: str) -> Optional[Dict[str, Any]]:
    """Get Razorpay payment details"""
    return razorpay_manager.get_payment_details(payment_id)

def validate_razorpay_amount(amount: Decimal) -> Tuple[bool, str]:
    """Validate Razorpay payment amount"""
    return razorpay_manager.validate_payment_amount(amount)

def is_razorpay_configured() -> bool:
    """Check if Razorpay is configured"""
    return razorpay_manager.is_configured()

def get_razorpay_configuration() -> Dict[str, Any]:
    """Get Razorpay configuration"""
    return razorpay_manager.get_configuration_info()

def get_razorpay_payment_analytics(from_date: datetime = None, to_date: datetime = None) -> Dict[str, Any]:
    """Get Razorpay payment analytics"""
    return razorpay_manager.get_payment_analytics(from_date, to_date)

def create_razorpay_recurring_payment(amount: Decimal, frequency: str,
                                   start_date: datetime, end_date: datetime = None,
                                   customer_email: str = None, customer_contact: str = None) -> Optional[Dict[str, Any]]:
    """Create Razorpay recurring payment"""
    return razorpay_manager.create_recurring_payment(amount, frequency, start_date, end_date, customer_email, customer_contact)

def calculate_razorpay_emi(amount: Decimal, tenure_months: int, interest_rate: float = 0.0) -> Dict[str, Any]:
    """Calculate Razorpay EMI details"""
    return razorpay_manager.process_emi_payment(amount, tenure_months, interest_rate)

def validate_razorpay_payment_method(method: str, details: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate Razorpay payment method"""
    return razorpay_manager.validate_payment_method(method, details)