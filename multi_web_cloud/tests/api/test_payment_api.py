"""
Tests for Razorpay Payment API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestPaymentAPI(BaseAPITestCase):
    """Test cases for Razorpay Payment API endpoints"""
    
    def test_create_order(self, client, auth_headers):
        """Test creating a Razorpay order"""
        response = client.post('/api/payment/create-order',
                              data=json.dumps({
                                  'amount': 50000,  # 500.00 INR in paise
                                  'currency': 'INR',
                                  'receipt': 'receipt_order_123',
                                  'notes': {
                                      'customer_name': 'John Doe',
                                      'order_type': 'food_order'
                                  },
                                  'payment_capture': 1
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'order' in data
        assert 'id' in data['order']
        assert 'amount' in data['order']
        assert 'currency' in data['order']
        assert 'receipt' in data['order']
    
    def test_verify_signature(self, client, auth_headers):
        """Test verifying payment signature"""
        response = client.post('/api/payment/verify-signature',
                              data=json.dumps({
                                  'razorpay_order_id': 'order_test_123',
                                  'razorpay_payment_id': 'pay_test_123',
                                  'razorpay_signature': 'test_signature_123'
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'verification_result' in data
        assert 'is_valid' in data['verification_result']
        assert 'message' in data
    
    def test_capture_payment(self, client, auth_headers):
        """Test capturing a payment"""
        response = client.post('/api/payment/capture',
                              data=json.dumps({
                                  'payment_id': 'pay_test_123',
                                  'amount': 50000,
                                  'currency': 'INR'
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'capture_result' in data
        assert 'payment_id' in data['capture_result']
        assert 'amount' in data['capture_result']
        assert 'status' in data['capture_result']
    
    def test_process_refund(self, client, auth_headers):
        """Test processing a refund"""
        response = client.post('/api/payment/refund',
                              data=json.dumps({
                                  'payment_id': 'pay_test_123',
                                  'amount': 25000,  # Partial refund
                                  'notes': {
                                      'reason': 'Customer requested refund',
                                      'processed_by': 'test_user'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'refund_result' in data
        assert 'refund_id' in data['refund_result']
        assert 'amount' in data['refund_result']
        assert 'status' in data['refund_result']
    
    def test_get_payment_methods(self, client, auth_headers):
        """Test getting available payment methods"""
        response = client.get('/api/payment/methods',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'payment_methods' in data
        assert isinstance(data['payment_methods'], list)
        # Check for common payment methods
        method_names = [method['name'] for method in data['payment_methods']]
        assert 'card' in method_names
        assert 'netbanking' in method_names
        assert 'wallet' in method_names
    
    def test_get_emi_plans(self, client, auth_headers):
        """Test getting EMI plans"""
        response = client.get('/api/payment/emi-plans?amount=50000',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'emi_plans' in data
        assert isinstance(data['emi_plans'], list)
        if data['emi_plans']:
            plan = data['emi_plans'][0]
            assert 'tenure' in plan
            assert 'interest_rate' in plan
            assert 'monthly_installment' in plan
    
    def test_get_transactions(self, client, auth_headers):
        """Test getting payment history"""
        response = client.get('/api/payment/transactions?page=1&per_page=10',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'transactions' in data
        assert 'pagination' in data
        assert isinstance(data['transactions'], list)
        assert 'current_page' in data['pagination']
        assert 'total_pages' in data['pagination']
    
    def test_process_webhook(self, client):
        """Test processing Razorpay webhooks"""
        webhook_data = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test_123',
                        'amount': 50000,
                        'currency': 'INR',
                        'status': 'captured'
                    }
                }
            }
        }
        
        response = client.post('/api/payment/webhook',
                              data=json.dumps(webhook_data),
                              headers={
                                  'Content-Type': 'application/json',
                                  'X-Razorpay-Signature': 'test_signature'
                              })
        
        data = self.assert_success_response(response)
        assert 'webhook_processed' in data
        assert 'event_type' in data
        assert 'message' in data
    
    def test_get_payment_analytics(self, client, auth_headers):
        """Test getting payment analytics"""
        response = client.get('/api/payment/analytics?period=30d',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'analytics' in data
        assert 'total_revenue' in data['analytics']
        assert 'transaction_count' in data['analytics']
        assert 'success_rate' in data['analytics']
        assert 'payment_methods_breakdown' in data['analytics']
    
    def test_validate_payment_method(self, client, auth_headers):
        """Test validating payment method details"""
        response = client.post('/api/payment/validate-method',
                              data=json.dumps({
                                  'method_type': 'card',
                                  'card_details': {
                                      'number': '4111111111111111',
                                      'expiry_month': '12',
                                      'expiry_year': '2025',
                                      'cvv': '123'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert 'is_valid' in data['validation_result']
        assert 'method_type' in data['validation_result']
    
    def test_create_order_invalid_amount(self, client, auth_headers):
        """Test creating order with invalid amount"""
        response = client.post('/api/payment/create-order',
                              data=json.dumps({
                                  'amount': -100,  # Negative amount
                                  'currency': 'INR'
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_verify_signature_missing_data(self, client, auth_headers):
        """Test signature verification with missing data"""
        response = client.post('/api/payment/verify-signature',
                              data=json.dumps({
                                  'razorpay_order_id': 'order_test_123'
                                  # Missing payment_id and signature
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_refund_invalid_amount(self, client, auth_headers):
        """Test refund with invalid amount"""
        response = client.post('/api/payment/refund',
                              data=json.dumps({
                                  'payment_id': 'pay_test_123',
                                  'amount': 0  # Zero amount
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_payment_analytics_unauthorized(self, client):
        """Test getting payment analytics without authentication"""
        response = client.get('/api/payment/analytics',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)