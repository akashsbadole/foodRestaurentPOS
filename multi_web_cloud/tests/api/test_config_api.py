"""
Tests for Configuration Management API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestConfigAPI(BaseAPITestCase):
    """Test cases for Configuration Management API endpoints"""
    
    def test_get_validation_config(self, client, auth_headers):
        """Test getting validation configuration"""
        response = client.get('/api/config/validation',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_config' in data
        assert 'field_rules' in data['validation_config']
        assert 'form_rules' in data['validation_config']
        assert 'password_policy' in data['validation_config']
        assert 'sanitization_rules' in data['validation_config']
    
    def test_update_validation_config(self, client, auth_headers):
        """Test updating validation configuration"""
        response = client.post('/api/config/validation',
                              data=json.dumps({
                                  'field_rules': {
                                      'email': {
                                          'required': True,
                                          'email': True,
                                          'max_length': 100
                                      },
                                      'phone': {
                                          'required': True,
                                          'min_length': 10,
                                          'max_length': 15,
                                          'pattern': '^[0-9+-]+$'
                                      }
                                  },
                                  'password_policy': {
                                      'min_length': 12,
                                      'require_uppercase': True,
                                      'require_lowercase': True,
                                      'require_numbers': True,
                                      'require_special_chars': True
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_updated' in data
        assert 'validation_config' in data['config_updated']
        assert 'message' in data
    
    def test_get_session_config(self, client, auth_headers):
        """Test getting session configuration"""
        response = client.get('/api/config/session',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'session_config' in data
        assert 'timeout_settings' in data['session_config']
        assert 'security_settings' in data['session_config']
        assert 'concurrent_sessions' in data['session_config']
        assert 'auto_extend' in data['session_config']
    
    def test_update_session_config(self, client, auth_headers):
        """Test updating session configuration"""
        response = client.post('/api/config/session',
                              data=json.dumps({
                                  'timeout_settings': {
                                      'idle_timeout': 1800,
                                      'absolute_timeout': 7200,
                                      'warning_time': 300
                                  },
                                  'security_settings': {
                                      'require_ip_validation': True,
                                      'require_user_agent_validation': True,
                                      'csrf_protection': True
                                  },
                                  'concurrent_sessions': {
                                      'max_sessions': 3,
                                      'allow_multiple_devices': True
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_updated' in data
        assert 'session_config' in data['config_updated']
        assert 'message' in data
    
    def test_get_security_config(self, client, auth_headers):
        """Test getting security configuration"""
        response = client.get('/api/config/security',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'security_config' in data
        assert 'authentication_settings' in data['security_config']
        assert 'authorization_settings' in data['security_config']
        assert 'ip_settings' in data['security_config']
        assert 'audit_settings' in data['security_config']
    
    def test_update_security_config(self, client, auth_headers):
        """Test updating security configuration"""
        response = client.post('/api/config/security',
                              data=json.dumps({
                                  'authentication_settings': {
                                      'max_login_attempts': 5,
                                      'lockout_duration': 900,
                                      'password_expiration': 7776000
                                  },
                                  'ip_settings': {
                                      'enable_ip_whitelist': True,
                                      'enable_ip_blacklist': True,
                                      'default_action': 'block'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_updated' in data
        assert 'security_config' in data['config_updated']
        assert 'message' in data
    
    def test_get_offline_config(self, client, auth_headers):
        """Test getting offline configuration"""
        response = client.get('/api/config/offline',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'offline_config' in data
        assert 'sync_settings' in data['offline_config']
        assert 'storage_settings' in data['offline_config']
        assert 'conflict_resolution' in data['offline_config']
        assert 'cache_settings' in data['offline_config']
    
    def test_update_offline_config(self, client, auth_headers):
        """Test updating offline configuration"""
        response = client.post('/api/config/offline',
                              data=json.dumps({
                                  'sync_settings': {
                                      'auto_sync': True,
                                      'sync_interval': 300,
                                      'retry_attempts': 3
                                  },
                                  'storage_settings': {
                                      'max_storage_size': 1073741824,  # 1GB
                                      'cleanup_interval': 86400
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_updated' in data
        assert 'offline_config' in data['config_updated']
        assert 'message' in data
    
    def test_get_payment_config(self, client, auth_headers):
        """Test getting payment configuration"""
        response = client.get('/api/config/payment',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'payment_config' in data
        assert 'razorpay_settings' in data['payment_config']
        assert 'payment_methods' in data['payment_config']
        assert 'refund_settings' in data['payment_config']
        assert 'webhook_settings' in data['payment_config']
    
    def test_update_payment_config(self, client, auth_headers):
        """Test updating payment configuration"""
        response = client.post('/api/config/payment',
                              data=json.dumps({
                                  'razorpay_settings': {
                                      'key_id': 'rzp_test_key_id',
                                      'webhook_secret': 'test_webhook_secret'
                                  },
                                  'payment_methods': {
                                      'card': True,
                                      'netbanking': True,
                                      'wallet': True,
                                      'upi': True
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_updated' in data
        assert 'payment_config' in data['config_updated']
        assert 'message' in data
    
    def test_export_config(self, client, auth_headers):
        """Test exporting configuration"""
        response = client.post('/api/config/export',
                              data=json.dumps({
                                  'config_types': ['validation', 'session', 'security'],
                                  'format': 'json',
                                  'include_sensitive': False
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'export_result' in data
        assert 'export_id' in data['export_result']
        assert 'download_url' in data['export_result']
        assert 'file_format' in data['export_result']
    
    def test_import_config(self, client, auth_headers):
        """Test importing configuration"""
        config_data = {
            'validation_config': {
                'field_rules': {
                    'email': {'required': True, 'email': True}
                }
            }
        }
        
        response = client.post('/api/config/import',
                              data=json.dumps({
                                  'config_data': config_data,
                                  'merge_strategy': 'merge',
                                  'backup_existing': True
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'import_result' in data
        assert 'imported_configs' in data['import_result']
        assert 'backup_id' in data['import_result']
        assert 'message' in data
    
    def test_reset_config(self, client, auth_headers):
        """Test resetting configuration to defaults"""
        response = client.post('/api/config/reset',
                              data=json.dumps({
                                  'config_types': ['validation'],
                                  'confirm_reset': True
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'reset_result' in data
        assert 'reset_configs' in data['reset_result']
        assert 'message' in data
    
    def test_get_config_history(self, client, auth_headers):
        """Test getting configuration change history"""
        response = client.get('/api/config/history?config_type=validation&page=1',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'config_history' in data
        assert 'pagination' in data
        assert isinstance(data['config_history'], list)
        assert 'current_page' in data['pagination']
    
    def test_get_validation_config_unauthorized(self, client):
        """Test getting validation config without authentication"""
        response = client.get('/api/config/validation',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)
    
    def test_update_validation_config_invalid_data(self, client, auth_headers):
        """Test updating validation config with invalid data"""
        response = client.post('/api/config/validation',
                              data=json.dumps({
                                  'field_rules': {
                                      'email': {
                                          'required': 'invalid_boolean'  # Should be boolean
                                      }
                                  }
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_reset_config_without_confirmation(self, client, auth_headers):
        """Test resetting config without confirmation"""
        response = client.post('/api/config/reset',
                              data=json.dumps({
                                  'config_types': ['validation']
                                  # Missing confirm_reset: True
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)