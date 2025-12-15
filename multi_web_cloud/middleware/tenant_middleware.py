"""
Tenant Identification Middleware
Handles tenant identification and context management for multi-tenant architecture
"""

from functools import wraps
from flask import request, g, current_app, jsonify, redirect, url_for
from models.tenant import Tenant, TenantSettings
from models.user import User
import re
from urllib.parse import urlparse


class TenantMiddleware:
    """Middleware for tenant identification and context management"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
        
        # Configuration
        app.config.setdefault('TENANT_IDENTIFICATION_METHODS', ['subdomain', 'header', 'path'])
        app.config.setdefault('DEFAULT_TENANT_DOMAIN', 'localhost')
        app.config.setdefault('TENANT_HEADER_NAME', 'X-Tenant-ID')
        app.config.setdefault('TENANT_PATH_PREFIX', '/t/')
        app.config.setdefault('SKIP_TENANT_ROUTES', ['/health', '/static', '/favicon.ico'])
    
    def before_request(self):
        """Process request to identify tenant and set context"""
        # Skip tenant identification for certain routes
        if self._should_skip_tenant_check():
            return
        
        # Identify tenant
        tenant_id = self._identify_tenant()
        
        if not tenant_id:
            # Handle missing tenant
            return self._handle_missing_tenant()
        
        # Set tenant context
        g.tenant_id = tenant_id
        g.tenant = Tenant.query.get(tenant_id)
        
        # Load tenant settings
        if g.tenant:
            g.tenant_settings = g.tenant.settings.first()
        else:
            g.tenant_settings = None
        
        # Track tenant usage
        self._track_tenant_usage(tenant_id)
    
    def after_request(self, response):
        """Process response to add tenant headers"""
        if hasattr(g, 'tenant_id'):
            response.headers['X-Tenant-ID'] = str(g.tenant_id)
        
        return response
    
    def teardown_request(self, exception):
        """Clean up tenant context"""
        if hasattr(g, 'tenant_id'):
            delattr(g, 'tenant_id')
        if hasattr(g, 'tenant'):
            delattr(g, 'tenant')
        if hasattr(g, 'tenant_settings'):
            delattr(g, 'tenant_settings')
    
    def _should_skip_tenant_check(self):
        """Check if tenant identification should be skipped"""
        path = request.path
        
        # Skip static files and health checks
        skip_routes = current_app.config.get('SKIP_TENANT_ROUTES', [])
        for skip_route in skip_routes:
            if path.startswith(skip_route):
                return True
        
        # Skip API routes that handle tenant identification themselves
        api_skip_routes = ['/api/tenant/', '/api/auth/login', '/api/auth/register']
        for api_route in api_skip_routes:
            if path.startswith(api_route):
                return True
        
        return False
    
    def _identify_tenant(self):
        """Identify tenant from request using configured methods"""
        methods = current_app.config.get('TENANT_IDENTIFICATION_METHODS', ['subdomain', 'header', 'path'])
        
        for method in methods:
            tenant_id = None
            
            if method == 'subdomain':
                tenant_id = self._identify_tenant_from_subdomain()
            elif method == 'header':
                tenant_id = self._identify_tenant_from_header()
            elif method == 'path':
                tenant_id = self._identify_tenant_from_path()
            elif method == 'domain':
                tenant_id = self._identify_tenant_from_domain()
            
            if tenant_id:
                # Validate tenant exists and is active
                if self._validate_tenant(tenant_id):
                    return tenant_id
        
        return None
    
    def _identify_tenant_from_subdomain(self):
        """Identify tenant from subdomain"""
        host = request.host.split(':')[0]  # Remove port if present
        
        # Extract subdomain
        parts = host.split('.')
        if len(parts) >= 3:  # subdomain.domain.tld
            subdomain = parts[0]
            
            # Skip www subdomain
            if subdomain.lower() != 'www':
                # Look up tenant by subdomain
                tenant = Tenant.query.filter_by(subdomain=subdomain).first()
                if tenant:
                    return tenant.id
        
        return None
    
    def _identify_tenant_from_header(self):
        """Identify tenant from HTTP header"""
        header_name = current_app.config.get('TENANT_HEADER_NAME', 'X-Tenant-ID')
        tenant_id = request.headers.get(header_name)
        
        if tenant_id:
            try:
                return int(tenant_id)
            except ValueError:
                # Try to find tenant by identifier
                tenant = Tenant.query.filter_by(identifier=tenant_id).first()
                if tenant:
                    return tenant.id
        
        return None
    
    def _identify_tenant_from_path(self):
        """Identify tenant from URL path"""
        path_prefix = current_app.config.get('TENANT_PATH_PREFIX', '/t/')
        
        if request.path.startswith(path_prefix):
            # Extract tenant identifier from path
            path_parts = request.path[len(path_prefix):].split('/')
            if path_parts:
                tenant_identifier = path_parts[0]
                
                # Try to find tenant by identifier
                tenant = Tenant.query.filter_by(identifier=tenant_identifier).first()
                if tenant:
                    return tenant.id
        
        return None
    
    def _identify_tenant_from_domain(self):
        """Identify tenant from full domain"""
        host = request.host.split(':')[0]  # Remove port if present
        
        # Look up tenant by domain
        tenant = Tenant.query.filter_by(domain=host).first()
        if tenant:
            return tenant.id
        
        return None
    
    def _validate_tenant(self, tenant_id):
        """Validate tenant exists and is active"""
        tenant = Tenant.query.get(tenant_id)
        
        if not tenant:
            return False
        
        if not tenant.is_active:
            return False
        
        # Check subscription status if required
        if current_app.config.get('REQUIRE_ACTIVE_SUBSCRIPTION', False):
            if not tenant.has_active_subscription():
                return False
        
        return True
    
    def _handle_missing_tenant(self):
        """Handle requests without valid tenant"""
        # For API requests, return JSON error
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Tenant not found or inactive',
                'message': 'Please provide a valid tenant identifier'
            }), 404
        
        # For web requests, redirect to tenant selection or error page
        if request.path.startswith('/admin/'):
            return redirect(url_for('tenant.select_tenant'))
        
        # Return error page
        return jsonify({
            'error': 'Tenant not found',
            'message': 'Please provide a valid tenant identifier'
        }), 404
    
    def _track_tenant_usage(self, tenant_id):
        """Track tenant usage for billing and analytics"""
        try:
            from models.tenant import TenantUsage
            from datetime import datetime
            
            # Get or create usage record for today
            today = datetime.utcnow().date()
            usage = TenantUsage.query.filter_by(
                tenant_id=tenant_id,
                usage_date=today
            ).first()
            
            if not usage:
                usage = TenantUsage(
                    tenant_id=tenant_id,
                    usage_date=today
                )
                db.session.add(usage)
            
            # Increment API calls
            if request.path.startswith('/api/'):
                usage.api_calls += 1
            
            # Track active users (simplified - in production, use more sophisticated tracking)
            if hasattr(g, 'user') and g.user:
                usage.active_users = max(usage.active_users, 1)
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error tracking tenant usage: {e}")
            # Don't fail the request if usage tracking fails


def tenant_required(f):
    """Decorator to require tenant context for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'tenant_id') or not g.tenant_id:
            return jsonify({
                'error': 'Tenant context required',
                'message': 'This endpoint requires tenant identification'
            }), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def tenant_optional(f):
    """Decorator to make tenant context optional for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure tenant context exists, even if None
        if not hasattr(g, 'tenant_id'):
            g.tenant_id = None
            g.tenant = None
            g.tenant_settings = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_tenant_feature(feature_name):
    """Decorator to require specific tenant feature"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                return jsonify({
                    'error': 'Tenant context required',
                    'message': 'This endpoint requires tenant identification'
                }), 400
            
            if not g.tenant.has_feature(feature_name):
                return jsonify({
                    'error': 'Feature not available',
                    'message': f'The "{feature_name}" feature is not available for your subscription plan'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_tenant_plan(plan_name):
    """Decorator to require specific tenant subscription plan"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'tenant') or not g.tenant:
                return jsonify({
                    'error': 'Tenant context required',
                    'message': 'This endpoint requires tenant identification'
                }), 400
            
            if not g.tenant.has_plan(plan_name):
                return jsonify({
                    'error': 'Plan upgrade required',
                    'message': f'This feature requires a {plan_name} subscription plan'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class TenantContext:
    """Helper class for managing tenant context"""
    
    @staticmethod
    def get_current_tenant():
        """Get current tenant from context"""
        return getattr(g, 'tenant', None)
    
    @staticmethod
    def get_current_tenant_id():
        """Get current tenant ID from context"""
        return getattr(g, 'tenant_id', None)
    
    @staticmethod
    def get_tenant_settings():
        """Get current tenant settings from context"""
        return getattr(g, 'tenant_settings', None)
    
    @staticmethod
    def set_tenant_context(tenant_id):
        """Manually set tenant context"""
        g.tenant_id = tenant_id
        g.tenant = Tenant.query.get(tenant_id)
        
        if g.tenant:
            g.tenant_settings = g.tenant.settings.first()
        else:
            g.tenant_settings = None
    
    @staticmethod
    def clear_tenant_context():
        """Clear tenant context"""
        if hasattr(g, 'tenant_id'):
            delattr(g, 'tenant_id')
        if hasattr(g, 'tenant'):
            delattr(g, 'tenant')
        if hasattr(g, 'tenant_settings'):
            delattr(g, 'tenant_settings')
    
    @staticmethod
    def is_tenant_context():
        """Check if tenant context is available"""
        return hasattr(g, 'tenant_id') and g.tenant_id is not None


# Utility functions for tenant URL generation
def tenant_url_for(endpoint, **values):
    """Generate URL with tenant context"""
    tenant = TenantContext.get_current_tenant()
    
    if tenant and tenant.subdomain:
        # Generate subdomain URL
        from flask import url_for
        url = url_for(endpoint, **values)
        
        # Replace domain with subdomain
        parsed = urlparse(url)
        netloc = f"{tenant.subdomain}.{parsed.netloc}"
        
        return parsed._replace(netloc=netloc).geturl()
    
    elif tenant and tenant.identifier:
        # Generate path-based URL
        from flask import url_for
        url = url_for(endpoint, **values)
        path_prefix = current_app.config.get('TENANT_PATH_PREFIX', '/t/')
        
        # Insert tenant identifier into path
        parsed = urlparse(url)
        path = f"{path_prefix}{tenant.identifier}{parsed.path}"
        
        return parsed._replace(path=path).geturl()
    
    # Fallback to regular URL
    from flask import url_for
    return url_for(endpoint, **values)