"""
Tests for Security Management API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestSecurityAPI(BaseAPITestCase):
    """Test cases for Security Management API endpoints"""
    
    def test_get_security_status(self, client, auth_headers):
        """Test getting comprehensive security status"""
        response = client.get('/api/security/status',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'security_status' in data
        assert 'overall_score' in data['security_status']
        assert 'threat_level' in data['security_status']
        assert 'active_threats' in data['security_status']
        assert 'security_features' in data['security_status']
    
    def test_get_security_events(self, client, auth_headers):
        """Test getting security events with filtering"""
        response = client.get('/api/security/events?event_type=login&limit=10',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'security_events' in data
        assert 'pagination' in data
        assert isinstance(data['security_events'], list)
        assert len(data['security_events']) <= 10
    
    def test_block_ip(self, client, auth_headers):
        """Test blocking an IP address"""
        response = client.post('/api/security/block-ip',
                              data=json.dumps({
                                  'ip_address': '192.168.1.100',
                                  'reason': 'Suspicious activity',
                                  'duration_hours': 24,
                                  'permanent': False
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'blocked_ip' in data
        assert 'block_id' in data['blocked_ip']
        assert 'expires_at' in data['blocked_ip']
        assert 'message' in data
    
    def test_unblock_ip(self, client, auth_headers):
        """Test unblocking an IP address"""
        # First block an IP
        client.post('/api/security/block-ip',
                   data=json.dumps({
                       'ip_address': '192.168.1.101',
                       'reason': 'Test block'
                   }),
                   headers=auth_headers)
        
        # Then unblock it
        response = client.delete('/api/security/unblock-ip/192.168.1.101',
                                headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'unblocked_ip' in data
        assert 'message' in data
    
    def test_get_threats(self, client, auth_headers):
        """Test getting threat intelligence"""
        response = client.get('/api/security/threats',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'threat_intelligence' in data
        assert 'active_threats' in data['threat_intelligence']
        assert 'threat_feed' in data['threat_intelligence']
        assert 'risk_assessment' in data['threat_intelligence']
    
    def test_scan_vulnerabilities(self, client, auth_headers):
        """Test scanning for vulnerabilities"""
        response = client.post('/api/security/scan',
                              data=json.dumps({
                                  'scan_type': 'comprehensive',
                                  'target_areas': ['authentication', 'authorization', 'data_protection']
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'scan_result' in data
        assert 'scan_id' in data['scan_result']
        assert 'vulnerabilities' in data['scan_result']
        assert 'risk_score' in data['scan_result']
    
    def test_get_audit_log(self, client, auth_headers):
        """Test getting audit log with pagination"""
        response = client.get('/api/security/audit-log?page=1&per_page=20',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'audit_log' in data
        assert 'pagination' in data
        assert isinstance(data['audit_log'], list)
        assert 'current_page' in data['pagination']
        assert 'total_pages' in data['pagination']
    
    def test_update_security_settings(self, client, auth_headers):
        """Test updating security settings"""
        response = client.post('/api/security/settings',
                              data=json.dumps({
                                  'password_policy': {
                                      'min_length': 12,
                                      'require_uppercase': True,
                                      'require_lowercase': True,
                                      'require_numbers': True,
                                      'require_special_chars': True
                                  },
                                  'session_settings': {
                                      'max_duration': 3600,
                                      'idle_timeout': 1800,
                                      'concurrent_sessions': 2
                                  },
                                  'ip_whitelist': ['192.168.1.0/24', '10.0.0.0/8']
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'settings' in data
        assert 'message' in data
    
    def test_get_blocked_ips(self, client, auth_headers):
        """Test getting list of blocked IPs"""
        response = client.get('/api/security/blocked-ips',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'blocked_ips' in data
        assert isinstance(data['blocked_ips'], list)
    
    def test_get_security_analytics(self, client, auth_headers):
        """Test getting security analytics"""
        response = client.get('/api/security/analytics?period=7d',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'analytics' in data
        assert 'attack_patterns' in data['analytics']
        assert 'security_metrics' in data['analytics']
        assert 'trend_analysis' in data['analytics']
    
    def test_report_security_incident(self, client, auth_headers):
        """Test reporting a security incident"""
        response = client.post('/api/security/incident',
                              data=json.dumps({
                                  'incident_type': 'unauthorized_access',
                                  'severity': 'high',
                                  'description': 'Suspicious login attempt detected',
                                  'affected_systems': ['authentication', 'user_management'],
                                  'evidence': {
                                      'ip_address': '192.168.1.200',
                                      'user_agent': 'Mozilla/5.0...',
                                      'timestamp': '2023-12-14T10:30:00Z'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'incident_report' in data
        assert 'incident_id' in data['incident_report']
        assert 'message' in data
    
    def test_security_status_unauthorized(self, client):
        """Test getting security status without authentication"""
        response = client.get('/api/security/status',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)
    
    def test_block_invalid_ip(self, client, auth_headers):
        """Test blocking an invalid IP address"""
        response = client.post('/api/security/block-ip',
                              data=json.dumps({
                                  'ip_address': 'invalid-ip-address',
                                  'reason': 'Test'
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_unblock_nonexistent_ip(self, client, auth_headers):
        """Test unblocking a non-existent IP"""
        response = client.delete('/api/security/unblock-ip/192.168.1.999',
                                headers=auth_headers)
        
        self.assert_error_response(response, 404)