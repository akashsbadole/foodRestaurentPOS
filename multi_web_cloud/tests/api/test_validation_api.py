"""
Tests for Validation API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestValidationAPI(BaseAPITestCase):
    """Test cases for Validation API endpoints"""
    
    def test_validate_field_success(self, client, auth_headers):
        """Test successful field validation"""
        response = client.post('/api/validation/field',
                              data=json.dumps({
                                  'field_name': 'email',
                                  'field_value': 'test@example.com',
                                  'validation_rules': {
                                      'required': True,
                                      'email': True
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is True
    
    def test_validate_field_failure(self, client, auth_headers):
        """Test field validation failure"""
        response = client.post('/api/validation/field',
                              data=json.dumps({
                                  'field_name': 'email',
                                  'field_value': 'invalid-email',
                                  'validation_rules': {
                                      'required': True,
                                      'email': True
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is False
        assert 'errors' in data['validation_result']
    
    def test_validate_form_success(self, client, auth_headers):
        """Test successful form validation"""
        response = client.post('/api/validation/form',
                              data=json.dumps({
                                  'form_data': {
                                      'name': 'John Doe',
                                      'email': 'john@example.com',
                                      'phone': '1234567890'
                                  },
                                  'form_rules': {
                                      'name': {'required': True, 'min_length': 2},
                                      'email': {'required': True, 'email': True},
                                      'phone': {'required': True, 'min_length': 10}
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is True
    
    def test_validate_form_failure(self, client, auth_headers):
        """Test form validation failure"""
        response = client.post('/api/validation/form',
                              data=json.dumps({
                                  'form_data': {
                                      'name': '',
                                      'email': 'invalid-email',
                                      'phone': '123'
                                  },
                                  'form_rules': {
                                      'name': {'required': True, 'min_length': 2},
                                      'email': {'required': True, 'email': True},
                                      'phone': {'required': True, 'min_length': 10}
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is False
        assert 'field_errors' in data['validation_result']
    
    def test_password_strength_check(self, client, auth_headers):
        """Test password strength checking"""
        # Test strong password
        response = client.post('/api/validation/password-strength',
                              data=json.dumps({
                                  'password': 'StrongP@ssw0rd123!'
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'strength_score' in data
        assert 'strength_level' in data
        assert 'feedback' in data
        assert data['strength_score'] >= 80
        
        # Test weak password
        response = client.post('/api/validation/password-strength',
                              data=json.dumps({
                                  'password': 'weak'
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert data['strength_score'] < 30
    
    def test_sanitize_input(self, client, auth_headers):
        """Test input sanitization"""
        response = client.post('/api/validation/sanitize',
                              data=json.dumps({
                                  'input_data': {
                                      'name': '<script>alert("xss")</script>John',
                                      'description': 'Test <b>bold</b> text',
                                      'comment': 'Normal comment'
                                  },
                                  'sanitization_rules': {
                                      'name': {'strip_html': True, 'escape_html': True},
                                      'description': {'strip_html': False, 'escape_html': True},
                                      'comment': {'strip_html': False, 'escape_html': False}
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'sanitized_data' in data
        assert '<script>' not in data['sanitized_data']['name']
        assert '<b>' in data['sanitized_data']['description']
        assert data['sanitized_data']['comment'] == 'Normal comment'
    
    def test_get_validation_rules(self, client, auth_headers):
        """Test getting validation rules"""
        response = client.get('/api/validation/rules',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_rules' in data
        assert 'default_rules' in data
        assert isinstance(data['validation_rules'], dict)
    
    def test_validate_json_structure(self, client, auth_headers):
        """Test JSON structure validation"""
        response = client.post('/api/validation/json-structure',
                              data=json.dumps({
                                  'json_data': {
                                      'name': 'John',
                                      'age': 30,
                                      'email': 'john@example.com'
                                  },
                                  'schema': {
                                      'type': 'object',
                                      'required': ['name', 'age', 'email'],
                                      'properties': {
                                          'name': {'type': 'string'},
                                          'age': {'type': 'number'},
                                          'email': {'type': 'string', 'format': 'email'}
                                      }
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is True
    
    def test_validate_file_upload(self, client, auth_headers):
        """Test file upload validation"""
        response = client.post('/api/validation/file-upload',
                              data=json.dumps({
                                  'file_info': {
                                      'filename': 'test.jpg',
                                      'content_type': 'image/jpeg',
                                      'size': 1024000  # 1MB
                                  },
                                  'validation_rules': {
                                      'allowed_types': ['image/jpeg', 'image/png'],
                                      'max_size': 2097152,  # 2MB
                                      'allowed_extensions': ['.jpg', '.jpeg', '.png']
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert data['validation_result']['is_valid'] is True
    
    def test_validate_field_missing_data(self, client, auth_headers):
        """Test field validation with missing data"""
        response = client.post('/api/validation/field',
                              data=json.dumps({}),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_validate_field_unauthorized(self, client):
        """Test field validation without authentication"""
        response = client.post('/api/validation/field',
                              data=json.dumps({
                                  'field_name': 'email',
                                  'field_value': 'test@example.com'
                              }),
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)