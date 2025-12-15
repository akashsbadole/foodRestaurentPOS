"""
Tests for Offline Support API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestOfflineAPI(BaseAPITestCase):
    """Test cases for Offline Support API endpoints"""
    
    def test_get_offline_status(self, client, auth_headers):
        """Test getting comprehensive offline status"""
        response = client.get('/api/offline/status',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'offline_status' in data
        assert 'connection_status' in data['offline_status']
        assert 'sync_status' in data['offline_status']
        assert 'queue_status' in data['offline_status']
        assert 'storage_status' in data['offline_status']
    
    def test_force_sync(self, client, auth_headers):
        """Test forcing immediate synchronization"""
        response = client.post('/api/offline/sync/force',
                              data=json.dumps({
                                  'sync_types': ['orders', 'customers', 'menu_items']
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'sync_result' in data
        assert 'sync_id' in data['sync_result']
        assert 'status' in data['sync_result']
        assert 'message' in data
    
    def test_get_pending_queue(self, client, auth_headers):
        """Test getting pending operations queue"""
        response = client.get('/api/offline/queue',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'queue_info' in data
        assert 'pending_operations' in data['queue_info']
        assert 'queue_size' in data['queue_info']
        assert isinstance(data['queue_info']['pending_operations'], list)
    
    def test_clear_pending_queue(self, client, auth_headers):
        """Test clearing pending queue"""
        response = client.post('/api/offline/queue/clear',
                              data=json.dumps({
                                  'operation_types': ['orders', 'customers'],
                                  'clear_all': False
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'cleared_count' in data
        assert 'message' in data
    
    def test_get_conflicts(self, client, auth_headers):
        """Test getting data conflicts list"""
        response = client.get('/api/offline/conflicts',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'conflicts' in data
        assert 'conflict_count' in data
        assert isinstance(data['conflicts'], list)
    
    def test_resolve_conflict(self, client, auth_headers):
        """Test resolving a specific conflict"""
        response = client.post('/api/offline/conflicts/resolve',
                              data=json.dumps({
                                  'conflict_id': 'test-conflict-123',
                                  'resolution_action': 'keep_local',
                                  'resolution_data': {
                                      'field1': 'local_value',
                                      'field2': 'merged_value'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'resolution_result' in data
        assert 'resolved_conflict_id' in data['resolution_result']
        assert 'message' in data
    
    def test_get_sync_statistics(self, client, auth_headers):
        """Test getting sync statistics"""
        response = client.get('/api/offline/statistics',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'statistics' in data
        assert 'sync_history' in data['statistics']
        assert 'success_rate' in data['statistics']
        assert 'average_sync_time' in data['statistics']
        assert 'last_sync' in data['statistics']
    
    def test_export_offline_data(self, client, auth_headers):
        """Test exporting offline data"""
        response = client.post('/api/offline/data/export',
                              data=json.dumps({
                                  'export_format': 'json',
                                  'data_types': ['orders', 'customers', 'menu_items'],
                                  'date_range': {
                                      'start_date': '2023-01-01',
                                      'end_date': '2023-12-31'
                                  }
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'export_result' in data
        assert 'export_id' in data['export_result']
        assert 'download_url' in data['export_result']
        assert 'file_size' in data['export_result']
    
    def test_test_connection(self, client, auth_headers):
        """Test connection quality testing"""
        response = client.post('/api/offline/test-connection',
                              data=json.dumps({
                                  'test_type': 'comprehensive',
                                  'timeout': 10
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'connection_test' in data
        assert 'latency' in data['connection_test']
        assert 'bandwidth' in data['connection_test']
        assert 'reliability' in data['connection_test']
        assert 'quality_score' in data['connection_test']
    
    def test_get_storage_usage(self, client, auth_headers):
        """Test getting storage usage information"""
        response = client.get('/api/offline/storage',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'storage_info' in data
        assert 'total_space' in data['storage_info']
        assert 'used_space' in data['storage_info']
        assert 'available_space' in data['storage_info']
        assert 'usage_percentage' in data['storage_info']
    
    def test_offline_status_unauthorized(self, client):
        """Test getting offline status without authentication"""
        response = client.get('/api/offline/status',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)
    
    def test_force_sync_invalid_data(self, client, auth_headers):
        """Test forcing sync with invalid data"""
        response = client.post('/api/offline/sync/force',
                              data=json.dumps({
                                  'sync_types': ['invalid_type']
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_resolve_nonexistent_conflict(self, client, auth_headers):
        """Test resolving a non-existent conflict"""
        response = client.post('/api/offline/conflicts/resolve',
                              data=json.dumps({
                                  'conflict_id': 'nonexistent-conflict',
                                  'resolution_action': 'keep_local'
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 404)