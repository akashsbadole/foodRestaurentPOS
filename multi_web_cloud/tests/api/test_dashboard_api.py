"""
Tests for Enhanced Dashboard API endpoints
"""
import pytest
import json
from test_base import BaseAPITestCase


class TestDashboardAPI(BaseAPITestCase):
    """Test cases for Enhanced Dashboard API endpoints"""
    
    def test_get_dashboard_overview(self, client, auth_headers):
        """Test getting dashboard overview with all metrics"""
        response = client.get('/api/dashboard/overview',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'overview' in data
        assert 'business_metrics' in data['overview']
        assert 'operational_metrics' in data['overview']
        assert 'financial_metrics' in data['overview']
        assert 'customer_metrics' in data['overview']
        assert 'last_updated' in data['overview']
    
    def test_get_performance_metrics(self, client, auth_headers):
        """Test getting performance metrics"""
        response = client.get('/api/dashboard/performance?period=7d',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'performance_metrics' in data
        assert 'response_times' in data['performance_metrics']
        assert 'throughput' in data['performance_metrics']
        assert 'error_rates' in data['performance_metrics']
        assert 'resource_usage' in data['performance_metrics']
        assert 'trends' in data['performance_metrics']
    
    def test_get_security_summary(self, client, auth_headers):
        """Test getting security summary"""
        response = client.get('/api/dashboard/security-summary',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'security_summary' in data
        assert 'threat_level' in data['security_summary']
        assert 'active_incidents' in data['security_summary']
        assert 'security_score' in data['security_summary']
        assert 'recent_events' in data['security_summary']
        assert 'blocked_attempts' in data['security_summary']
    
    def test_get_sync_status(self, client, auth_headers):
        """Test getting synchronization status"""
        response = client.get('/api/dashboard/sync-status',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'sync_status' in data
        assert 'last_sync' in data['sync_status']
        assert 'sync_queue_size' in data['sync_status']
        assert 'conflicts_count' in data['sync_status']
        assert 'sync_health' in data['sync_status']
        assert 'offline_operations' in data['sync_status']
    
    def test_get_recent_activity(self, client, auth_headers):
        """Test getting recent system activity"""
        response = client.get('/api/dashboard/recent-activity?limit=20',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'recent_activity' in data
        assert isinstance(data['recent_activity'], list)
        assert len(data['recent_activity']) <= 20
        
        if data['recent_activity']:
            activity = data['recent_activity'][0]
            assert 'id' in activity
            assert 'type' in activity
            assert 'description' in activity
            assert 'timestamp' in activity
            assert 'user' in activity
    
    def test_get_system_alerts(self, client, auth_headers):
        """Test getting system alerts"""
        response = client.get('/api/dashboard/alerts?severity=high',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'alerts' in data
        assert isinstance(data['alerts'], list)
        assert 'alert_count' in data
        
        if data['alerts']:
            alert = data['alerts'][0]
            assert 'id' in alert
            assert 'title' in alert
            assert 'message' in alert
            assert 'severity' in alert
            assert 'created_at' in alert
            assert 'is_dismissed' in alert
    
    def test_dismiss_alert(self, client, auth_headers):
        """Test dismissing a specific alert"""
        response = client.post('/api/dashboard/dismiss-alert',
                              data=json.dumps({
                                  'alert_id': 'test-alert-123',
                                  'dismiss_reason': 'Issue resolved'
                              }),
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'dismissed_alert' in data
        assert 'alert_id' in data['dismissed_alert']
        assert 'dismissed_at' in data['dismissed_alert']
        assert 'message' in data
    
    def test_get_sales_analytics(self, client, auth_headers):
        """Test getting sales analytics"""
        response = client.get('/api/dashboard/sales-analytics?period=30d',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'sales_analytics' in data
        assert 'total_sales' in data['sales_analytics']
        assert 'average_order_value' in data['sales_analytics']
        assert 'sales_by_category' in data['sales_analytics']
        assert 'sales_trend' in data['sales_analytics']
        assert 'top_selling_items' in data['sales_analytics']
    
    def test_get_customer_insights(self, client, auth_headers):
        """Test getting customer insights"""
        response = client.get('/api/dashboard/customer-insights',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'customer_insights' in data
        assert 'total_customers' in data['customer_insights']
        assert 'new_customers' in data['customer_insights']
        assert 'returning_customers' in data['customer_insights']
        assert 'customer_satisfaction' in data['customer_insights']
        assert 'customer_segments' in data['customer_insights']
    
    def test_get_inventory_status(self, client, auth_headers):
        """Test getting inventory status"""
        response = client.get('/api/dashboard/inventory-status',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'inventory_status' in data
        assert 'total_items' in data['inventory_status']
        assert 'low_stock_items' in data['inventory_status']
        assert 'out_of_stock_items' in data['inventory_status']
        assert 'inventory_value' in data['inventory_status']
        assert 'recent_movements' in data['inventory_status']
    
    def test_get_real_time_metrics(self, client, auth_headers):
        """Test getting real-time metrics"""
        response = client.get('/api/dashboard/real-time-metrics',
                              headers=auth_headers)
        
        data = self.assert_success_response(response)
        assert 'real_time_metrics' in data
        assert 'active_sessions' in data['real_time_metrics']
        assert 'current_orders' in data['real_time_metrics']
        assert 'online_users' in data['real_time_metrics']
        assert 'system_load' in data['real_time_metrics']
        assert 'timestamp' in data['real_time_metrics']
    
    def test_get_dashboard_overview_unauthorized(self, client):
        """Test getting dashboard overview without authentication"""
        response = client.get('/api/dashboard/overview',
                              headers={'Content-Type': 'application/json'})
        
        self.assert_error_response(response, 401)
    
    def test_dismiss_nonexistent_alert(self, client, auth_headers):
        """Test dismissing a non-existent alert"""
        response = client.post('/api/dashboard/dismiss-alert',
                              data=json.dumps({
                                  'alert_id': 'nonexistent-alert',
                                  'dismiss_reason': 'Test'
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 404)
    
    def test_dismiss_alert_missing_data(self, client, auth_headers):
        """Test dismissing alert with missing data"""
        response = client.post('/api/dashboard/dismiss-alert',
                              data=json.dumps({
                                  'dismiss_reason': 'Test'
                                  # Missing alert_id
                              }),
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)
    
    def test_get_performance_metrics_invalid_period(self, client, auth_headers):
        """Test getting performance metrics with invalid period"""
        response = client.get('/api/dashboard/performance?period=invalid',
                              headers=auth_headers)
        
        self.assert_error_response(response, 400)