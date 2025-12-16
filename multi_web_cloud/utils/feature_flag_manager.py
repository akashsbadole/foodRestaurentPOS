"""
Centralized feature flag management system with hierarchical configuration
Environment > Tenant > Runtime precedence
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from flask import current_app, g
from models import db, TenantFeatureFlag, FeatureDefinition, FeatureDependency, FeatureConflict, FeatureFlagAuditLog
from utils.feature_cache import FeatureCache
from utils.feature_validator import FeatureValidator
from utils.environment_flag_parser import EnvironmentFlagParser


class FeatureFlagManager:
    """
    Centralized feature flag management system with hierarchical configuration
    Environment > Tenant > Runtime precedence
    """
    
    def __init__(self, cache_size=1000, ttl=300):
        self.environment_flags = {}
        self.tenant_flags = {}
        self.runtime_flags = {}
        self.feature_dependencies = {}
        self.feature_validators = {}
        self.cache = FeatureCache(cache_size, ttl)
        self.validator = FeatureValidator()
        self.parser = EnvironmentFlagParser()
        self._initialized = False
    
    def initialize(self):
        """Initialize the feature flag manager"""
        if self._initialized:
            return
        
        # Load environment flags
        self.load_environment_flags()
        
        # Load feature definitions and dependencies
        self.load_feature_definitions()
        
        self._initialized = True
    
    def load_environment_flags(self):
        """Parse and validate all 100+ feature flags from .env"""
        self.environment_flags = self.parser.parse_environment_flags()
        
        # Validate environment flags
        validation_result = self.validator.validate_flag_values(self.environment_flags)
        if not validation_result.is_valid:
            current_app.logger.warning(f"Invalid environment flags detected: {validation_result.errors}")
    
    def load_feature_definitions(self):
        """Load feature definitions and dependencies from database"""
        try:
            # Load feature definitions
            definitions = FeatureDefinition.query.all()
            for definition in definitions:
                self.feature_validators[definition.name] = definition
            
            # Load feature dependencies
            dependencies = FeatureDependency.query.all()
            for dep in dependencies:
                if dep.feature_name not in self.feature_dependencies:
                    self.feature_dependencies[dep.feature_name] = {
                        'requires': [],
                        'conflicts': [],
                        'optional': []
                    }
                
                if dep.dependency_type == 'required':
                    self.feature_dependencies[dep.feature_name]['requires'].append(dep.depends_on_feature)
                elif dep.dependency_type == 'conflicts':
                    self.feature_dependencies[dep.feature_name]['conflicts'].append(dep.depends_on_feature)
                elif dep.dependency_type == 'optional':
                    self.feature_dependencies[dep.feature_name]['optional'].append(dep.depends_on_feature)
            
            # Load feature conflicts
            conflicts = FeatureConflict.query.all()
            for conflict in conflicts:
                # Add conflicts to both features
                for feature in [conflict.feature_1, conflict.feature_2]:
                    other_feature = conflict.feature_2 if feature == conflict.feature_1 else conflict.feature_1
                    if feature not in self.feature_dependencies:
                        self.feature_dependencies[feature] = {
                            'requires': [],
                            'conflicts': [],
                            'optional': []
                        }
                    self.feature_dependencies[feature]['conflicts'].append(other_feature)
                    
        except Exception as e:
            current_app.logger.error(f"Error loading feature definitions: {e}")
    
    def load_tenant_flags(self, tenant_id: str) -> Dict[str, Any]:
        """Load tenant-specific feature overrides"""
        if tenant_id in self.tenant_flags:
            return self.tenant_flags[tenant_id]
        
        try:
            flags = TenantFeatureFlag.query.filter_by(tenant_id=tenant_id).all()
            tenant_flags = {}
            
            for flag in flags:
                tenant_flags[flag.feature_name] = {
                    'enabled': flag.is_active(),
                    'configuration': flag.configuration,
                    'retail_type': flag.retail_type,
                    'priority': flag.priority,
                    'expires_at': flag.expires_at
                }
            
            self.tenant_flags[tenant_id] = tenant_flags
            return tenant_flags
            
        except Exception as e:
            current_app.logger.error(f"Error loading tenant flags for {tenant_id}: {e}")
            return {}
    
    def is_enabled(self, feature_name: str, tenant_id: Optional[str] = None, context: Optional[Dict] = None) -> bool:
        """
        Check if feature is enabled with hierarchical precedence
        Environment > Tenant > Runtime
        """
        # Initialize if not already done
        if not self._initialized:
            self.initialize()
        
        # Check cache first
        cache_key = f"{feature_name}:{tenant_id or 'global'}"
        cached_value = self.cache.get(cache_key, tenant_id)
        if cached_value is not None:
            return cached_value
        
        # Get feature value with hierarchy
        value = self._resolve_feature_value(feature_name, tenant_id, context)
        
        # Cache the result
        self.cache.set(cache_key, value, tenant_id)
        
        return value
    
    def _resolve_feature_value(self, feature_name: str, tenant_id: Optional[str] = None, context: Optional[Dict] = None) -> bool:
        """Resolve feature value with hierarchical precedence"""
        
        # 1. Check runtime overrides first (highest priority)
        if tenant_id and tenant_id in self.runtime_flags:
            if feature_name in self.runtime_flags[tenant_id]:
                return self.runtime_flags[tenant_id][feature_name]
        
        # 2. Check tenant-specific flags
        if tenant_id:
            tenant_flags = self.load_tenant_flags(tenant_id)
            if feature_name in tenant_flags:
                return tenant_flags[feature_name]['enabled']
        
        # 3. Check environment flags (lowest priority)
        if feature_name in self.environment_flags:
            return self.environment_flags[feature_name]
        
        # 4. Check feature definition for default value
        if feature_name in self.feature_validators:
            return self.feature_validators[feature_name].default_value
        
        # Default to disabled
        return False
    
    def validate_feature_combination(self, features: List[str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate feature dependencies and conflicts"""
        return self.validator.validate_feature_combination(features, tenant_id)
    
    def enable_feature(self, feature_name: str, tenant_id: str, configuration: Optional[Dict] = None, 
                     expires_at: Optional[datetime] = None, user_id: Optional[str] = None) -> bool:
        """Enable a feature for a tenant"""
        try:
            # Validate feature can be enabled
            validation_result = self._validate_feature_enablement(feature_name, tenant_id)
            if not validation_result['valid']:
                return False
            
            # Get or create feature flag
            flag = TenantFeatureFlag.query.filter_by(tenant_id=tenant_id, feature_name=feature_name).first()
            if not flag:
                flag = TenantFeatureFlag(
                    tenant_id=tenant_id,
                    feature_name=feature_name,
                    created_by=user_id
                )
                db.session.add(flag)
            
            # Enable the feature
            flag.enable(configuration, expires_at)
            
            # Clear cache
            self.cache.invalidate_tenant_cache(tenant_id)
            
            # Log the change
            self._log_feature_change(tenant_id, feature_name, 'enabled', flag, user_id)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error enabling feature {feature_name} for tenant {tenant_id}: {e}")
            db.session.rollback()
            return False
    
    def disable_feature(self, feature_name: str, tenant_id: str, user_id: Optional[str] = None) -> bool:
        """Disable a feature for a tenant"""
        try:
            flag = TenantFeatureFlag.query.filter_by(tenant_id=tenant_id, feature_name=feature_name).first()
            if not flag:
                return False
            
            old_value = flag.to_dict()
            flag.disable()
            
            # Clear cache
            self.cache.invalidate_tenant_cache(tenant_id)
            
            # Log the change
            self._log_feature_change(tenant_id, feature_name, 'disabled', flag, user_id, old_value)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error disabling feature {feature_name} for tenant {tenant_id}: {e}")
            db.session.rollback()
            return False
    
    def apply_runtime_override(self, feature_name: str, value: bool, tenant_id: str, context: Optional[Dict] = None):
        """Apply temporary runtime override"""
        if tenant_id not in self.runtime_flags:
            self.runtime_flags[tenant_id] = {}
        
        self.runtime_flags[tenant_id][feature_name] = value
        
        # Clear cache for this feature
        cache_key = f"{feature_name}:{tenant_id}"
        self.cache.invalidate_feature_cache(feature_name)
    
    def get_enabled_features(self, tenant_id: Optional[str] = None) -> Set[str]:
        """Get all enabled features for a tenant or globally"""
        enabled_features = set()
        
        # Get all feature definitions
        all_features = set(self.feature_validators.keys())
        
        for feature_name in all_features:
            if self.is_enabled(feature_name, tenant_id):
                enabled_features.add(feature_name)
        
        return enabled_features
    
    def get_feature_dependencies(self, feature_name: str) -> Dict[str, List[str]]:
        """Get dependencies for a feature"""
        return self.feature_dependencies.get(feature_name, {'requires': [], 'conflicts': [], 'optional': []})
    
    def get_tenant_retail_type(self, tenant_id: str) -> Optional[str]:
        """Get retail type for a tenant"""
        try:
            from models.tenant import TenantSettings
            settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
            if settings:
                # Check if retail_type field exists, otherwise infer from settings
                return getattr(settings, 'retail_type', 'restaurant')  # Default to restaurant
        except Exception as e:
            current_app.logger.error(f"Error getting retail type for tenant {tenant_id}: {e}")
        
        return 'restaurant'  # Default fallback
    
    def _validate_feature_enablement(self, feature_name: str, tenant_id: str) -> Dict[str, Any]:
        """Validate if a feature can be enabled"""
        result = {'valid': True, 'errors': []}
        
        # Check if feature exists
        if feature_name not in self.feature_validators:
            result['valid'] = False
            result['errors'].append(f"Feature {feature_name} is not defined")
            return result
        
        # Check retail type compatibility
        feature_def = self.feature_validators[feature_name]
        tenant_retail_type = self.get_tenant_retail_type(tenant_id)
        
        if not feature_def.is_supported_by_retail_type(tenant_retail_type):
            result['valid'] = False
            result['errors'].append(f"Feature {feature_name} is not supported for retail type {tenant_retail_type}")
        
        return result
    
    def _log_feature_change(self, tenant_id: str, feature_name: str, action: str, 
                           flag: TenantFeatureFlag, user_id: Optional[str] = None, 
                           old_value: Optional[Dict] = None):
        """Log feature flag changes"""
        try:
            from flask import request
            
            audit_log = FeatureFlagAuditLog(
                tenant_id=tenant_id,
                feature_name=feature_name,
                action=action,
                old_value=old_value,
                new_value=flag.to_dict(),
                changed_by=user_id,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent') if request else None
            )
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error logging feature change: {e}")
    
    def get_feature_statistics(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get feature flag statistics"""
        stats = {
            'total_features': len(self.feature_validators),
            'enabled_features': 0,
            'disabled_features': 0,
            'features_by_category': {},
            'retail_type': None
        }
        
        if tenant_id:
            stats['retail_type'] = self.get_tenant_retail_type(tenant_id)
            enabled_features = self.get_enabled_features(tenant_id)
            stats['enabled_features'] = len(enabled_features)
            stats['disabled_features'] = stats['total_features'] - stats['enabled_features']
        else:
            # Global statistics
            for feature_name in self.feature_validators:
                if self.is_enabled(feature_name):
                    stats['enabled_features'] += 1
                else:
                    stats['disabled_features'] += 1
        
        # Categorize features
        for feature_name, feature_def in self.feature_validators.items():
            category = feature_def.category
            if category not in stats['features_by_category']:
                stats['features_by_category'][category] = {'total': 0, 'enabled': 0}
            
            stats['features_by_category'][category]['total'] += 1
            if self.is_enabled(feature_name, tenant_id):
                stats['features_by_category'][category]['enabled'] += 1
        
        return stats


# Global feature manager instance
feature_manager = FeatureFlagManager()