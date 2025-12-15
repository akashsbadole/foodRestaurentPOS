"""
Tests for Session Management API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestSessionAPI(BaseAPITestCase):
    """Test cases for Session Management API endpoints"""
    
    def test_get_session_info(self, client, auth_headers):
        """Test getting current session information"""
        response = client.get('/api/session/info',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'session_info' in data
        assert 'user_id' in data['session_info']
        assert 'username' in data['session_info']
        assert 'session_id' in data['session_info']
        assert 'created_at' in data['session_info']
        assert 'expires_at' in data['session_info']
    
    def test_extend_session(self, client, auth_headers):
        """Test extending session timeout"""
        response = client.post('/api/session/extend',
                              data=json.dumps({
                                  'extension_minutes': 30
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'session_info' in data
        assert 'extended_until' in data['session_info']
        assert 'message' in data
    
    def test_get_active_sessions(self, client, auth_headers):
        """Test getting all active sessions for user"""
        response = client.get('/api/session/active',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'active_sessions' in data
        assert isinstance(data['active_sessions'], list)
    
    def test_revoke_session(self, client, auth_headers):
        """Test revoking a specific session"""
        # First get active sessions
        response = client.get('/api/session/active',
                              headers=auth_headers)
        data = self.assert_success_response(response)
        
        if data['active_sessions']:
            session_id = data['active_sessions'][0]['session_id']
            
            # Revoke the session
            response = client.delete(f'/api/session/{session_id}',
                                    headers=auth_headers)
            
            data = self.assert_success_response(response)
            assert 'message' in data
            assert 'revoked_session_id' in data
    
    def test_revoke_other_sessions(self, client, auth_headers):
        """Test revoking all other sessions"""
        response = client.delete('/api/session/others',
                                 headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'message' in data
        assert 'revoked_count' in data
    
    def test_get_session_security(self, client, auth_headers):
        """Test getting session security analysis"""
        response = client.get('/api/session/security',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'security_analysis' in data
        assert 'ip_risk_level' in data['security_analysis']
        assert 'device_risk_level' in data['security_analysis']
        assert 'session_integrity' in data['security_analysis']
        assert 'anomalies' in data['security_analysis']
    
    def test_validate_session(self, client, auth_headers):
        """Test session integrity validation"""
        response = client.post('/api/session/validate',
                              data=json.dumps({
                                  'validate_ip': True,
                                  'validate_user_agent': True,
                                  'validate_csrf': True
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'validation_result' in data
        assert 'is_valid' in data['validation_result']
        assert 'checks' in data['validation_result']
    
    def test_get_session_activity(self, client, auth_headers):
        """Test getting session activity log"""
        response = client.get('/api/session/activity',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'activity_log' in data
        assert isinstance(data['activity_log'], list)
    
    def test_update_session_preferences(self, client, auth_headers):
        """Test updating session preferences"""
        response = client.post('/api/session/preferences',
                              data=json.dumps({
                                  'timeout_duration': 3600,
                                  'auto_extend': True,
                                  'security_notifications': True
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'preferences' in data
        assert 'message' in data
    
    def test_get_session_unauthorized(self, client):
        """Test getting session info without authentication"""
        response = client.get('/api/session/info',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)
    
    def test_extend_session_invalid_data(self, client, auth_headers):
        """Test extending session with invalid data"""
        response = client.post('/api/session/extend',
                              data=json.dumps({
                                  'extension_minutes': -10  # Invalid negative value
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_revoke_nonexistent_session(self, client, auth_headers):
        """Test revoking a non-existent session"""
        response = client.delete('/api/session/nonexistent-session-id',
                                headers=auth_headers)
        
        self.assert_error_response(response, 404)