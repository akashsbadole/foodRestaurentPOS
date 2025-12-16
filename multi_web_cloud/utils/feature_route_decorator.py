"""
Feature-aware route decorators for conditional route registration
"""

import json
from functools import wraps
from typing import List, Optional, Callable, Any
from flask import request, jsonify, redirect, url_for, flash, current_app
from utils.feature_flag_manager import feature_manager
from utils.tenant_query_manager import get_current_tenant_id


def feature_required(feature_name: str, tenant_aware: bool = True):
    """
    Decorator to protect routes based on feature flags
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get current tenant
                tenant_id = get_current_tenant_id() if tenant_aware else None
                
                # Check feature availability
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    if request_wants_json():
                        return jsonify({
                            'error': 'Feature not available',
                            'feature': feature_name,
                            'message': f'The {feature_name} feature is not enabled',
                            'tenant_id': tenant_id
                        }), 403
                    else:
                        flash(f'The {feature_name} feature is not available', 'error')
                        return redirect(url_for('dashboard.index'))
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in feature_required decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking feature availability'
                    }), 500
                else:
                    flash('An error occurred while checking feature availability', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def retail_type_required(*retail_types: str):
    """
    Decorator to restrict routes to specific retail types
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                if not tenant_id:
                    if request_wants_json():
                        return jsonify({
                            'error': 'Tenant context required',
                            'message': 'This endpoint requires tenant context'
                        }), 400
                    else:
                        flash('Tenant context is required', 'error')
                        return redirect(url_for('auth.login'))
                
                tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
                
                if tenant_retail_type not in retail_types:
                    if request_wants_json():
                        return jsonify({
                            'error': 'Retail type not supported',
                            'supported_types': list(retail_types),
                            'current_type': tenant_retail_type,
                            'tenant_id': tenant_id
                        }), 403
                    else:
                        flash('This feature is not available for your business type', 'error')
                        return redirect(url_for('dashboard.index'))
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in retail_type_required decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking retail type compatibility'
                    }), 500
                else:
                    flash('An error occurred while checking retail type compatibility', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def feature_optional(feature_name: str, default_return: Any = None):
    """
    Decorator that makes route optional based on feature flags
    Returns default_return if feature is not enabled
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                
                # Check feature availability
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    if callable(default_return):
                        return default_return()
                    return default_return
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in feature_optional decorator: {e}")
                if callable(default_return):
                    return default_return()
                return default_return
        
        return decorated_function
    return decorator


def any_feature_required(*feature_names: str):
    """
    Decorator that requires at least one of the specified features to be enabled
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                
                # Check if any feature is enabled
                for feature_name in feature_names:
                    if feature_manager.is_enabled(feature_name, tenant_id):
                        return f(*args, **kwargs)
                
                # No features enabled
                if request_wants_json():
                    return jsonify({
                        'error': 'Feature not available',
                        'required_features': list(feature_names),
                        'message': f'At least one of these features is required: {", ".join(feature_names)}',
                        'tenant_id': tenant_id
                    }), 403
                else:
                    flash(f'At least one of these features is required: {", ".join(feature_names)}', 'error')
                    return redirect(url_for('dashboard.index'))
                
            except Exception as e:
                current_app.logger.error(f"Error in any_feature_required decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking feature availability'
                    }), 500
                else:
                    flash('An error occurred while checking feature availability', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def all_features_required(*feature_names: str):
    """
    Decorator that requires all specified features to be enabled
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                
                # Check if all features are enabled
                disabled_features = []
                for feature_name in feature_names:
                    if not feature_manager.is_enabled(feature_name, tenant_id):
                        disabled_features.append(feature_name)
                
                if disabled_features:
                    if request_wants_json():
                        return jsonify({
                            'error': 'Features not available',
                            'disabled_features': disabled_features,
                            'required_features': list(feature_names),
                            'message': f'These features are required but not enabled: {", ".join(disabled_features)}',
                            'tenant_id': tenant_id
                        }), 403
                    else:
                        flash(f'These features are required but not enabled: {", ".join(disabled_features)}', 'error')
                        return redirect(url_for('dashboard.index'))
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in all_features_required decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking feature availability'
                    }), 500
                else:
                    flash('An error occurred while checking feature availability', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def feature_configuration_required(feature_name: str, config_key: str, expected_value: Any = None):
    """
    Decorator that requires specific feature configuration
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                
                # Check if feature is enabled
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    if request_wants_json():
                        return jsonify({
                            'error': 'Feature not available',
                            'feature': feature_name,
                            'message': f'The {feature_name} feature is not enabled'
                        }), 403
                    else:
                        flash(f'The {feature_name} feature is not available', 'error')
                        return redirect(url_for('dashboard.index'))
                
                # Get feature configuration
                from models import TenantFeatureFlag
                feature_flag = TenantFeatureFlag.query.filter_by(
                    tenant_id=tenant_id, 
                    feature_name=feature_name
                ).first()
                
                if not feature_flag or not feature_flag.configuration:
                    if request_wants_json():
                        return jsonify({
                            'error': 'Feature configuration not found',
                            'feature': feature_name,
                            'config_key': config_key,
                            'message': f'Configuration for {feature_name} is not available'
                        }), 403
                    else:
                        flash(f'Configuration for {feature_name} is not available', 'error')
                        return redirect(url_for('dashboard.index'))
                
                # Check specific configuration
                config_value = feature_flag.configuration.get(config_key)
                if expected_value is not None and config_value != expected_value:
                    if request_wants_json():
                        return jsonify({
                            'error': 'Feature configuration mismatch',
                            'feature': feature_name,
                            'config_key': config_key,
                            'expected_value': expected_value,
                            'actual_value': config_value,
                            'message': f'Configuration {config_key} for {feature_name} does not match expected value'
                        }), 403
                    else:
                        flash(f'Configuration for {feature_name} does not meet requirements', 'error')
                        return redirect(url_for('dashboard.index'))
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in feature_configuration_required decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking feature configuration'
                    }), 500
                else:
                    flash('An error occurred while checking feature configuration', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def experimental_feature(feature_name: str):
    """
    Decorator for experimental features with additional warnings
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                tenant_id = get_current_tenant_id()
                
                # Check if feature is enabled
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    if request_wants_json():
                        return jsonify({
                            'error': 'Experimental feature not available',
                            'feature': feature_name,
                            'message': f'The experimental feature {feature_name} is not enabled'
                        }), 403
                    else:
                        flash(f'The experimental feature {feature_name} is not available', 'error')
                        return redirect(url_for('dashboard.index'))
                
                # Add experimental warning for non-API requests
                if not request_wants_json():
                    flash(f'Warning: {feature_name} is an experimental feature and may be unstable', 'warning')
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error in experimental_feature decorator: {e}")
                if request_wants_json():
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'Error checking experimental feature'
                    }), 500
                else:
                    flash('An error occurred while accessing experimental feature', 'error')
                    return redirect(url_for('dashboard.index'))
        
        return decorated_function
    return decorator


def request_wants_json() -> bool:
    """Check if request wants JSON response"""
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']


def get_feature_context() -> dict:
    """Get current feature context for debugging"""
    try:
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            return {'error': 'No tenant context'}
        
        enabled_features = feature_manager.get_enabled_features(tenant_id)
        retail_type = feature_manager.get_tenant_retail_type(tenant_id)
        
        return {
            'tenant_id': tenant_id,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'feature_count': len(enabled_features)
        }
    except Exception as e:
        return {'error': str(e)}