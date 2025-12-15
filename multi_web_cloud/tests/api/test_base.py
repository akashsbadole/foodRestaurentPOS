"""
Base test class for API endpoints
"""
import pytest
import json
from flask import testing
from multi_web_cloud.app import create_app
from multi_web_cloud.models import db, User


class BaseAPITestCase:
    """Base test case for API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create application for testing"""
        app = create_app('testing')
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        })
        
        with app.app_context():
            db.create_all()
            # Create test user
            test_user = User.create_user(
                username='testuser',
                password='testpass123',
                role='admin',
                email='test@example.com'
            )
            db.session.commit()
            
        yield app
        
        with app.app_context():
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers"""
        # Login to get session
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_json_response(self, response):
        """Get JSON response data"""
        return json.loads(response.data.decode('utf-8'))
    
    def assert_success_response(self, response, status_code=200):
        """Assert successful response"""
        assert response.status_code == status_code
        data = self.get_json_response(response)
        assert 'success' in data
        assert data['success'] is True
        return data
    
    def assert_error_response(self, response, status_code=400):
        """Assert error response"""
        assert response.status_code == status_code
        data = self.get_json_response(response)
        assert 'success' in data
        assert data['success'] is False
        assert 'error' in data
        return data