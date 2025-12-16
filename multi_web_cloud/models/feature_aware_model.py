"""
Base class for models that can be conditionally loaded based on feature flags
"""

from typing import List, Optional, Dict, Any, Set
from flask import current_app
from . import db


class FeatureAwareModel(db.Model):
    """
    Base class for models that can be conditionally loaded
    """
    
    __abstract__ = True
    
    # Feature requirements
    required_features = []  # List of feature names that must be enabled
    optional_features = []  # List of feature names that are optional
    retail_types = []  # List of retail types this model supports
    conflicts_with = []  # List of features that conflict with this model
    
    # Model metadata
    model_category = 'core'  # core, retail_type, advanced, experimental
    model_version = '1.0.0'
    deprecated = False
    deprecation_message = None
    
    @classmethod
    def is_available_for_tenant(cls, tenant_id: Optional[str] = None) -> bool:
        """Check if model is available for tenant"""
        try:
            from utils.feature_flag_manager import feature_manager
            
            # Check required features
            for feature_name in cls.required_features:
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    return False
            
            # Check conflicting features
            for feature_name in cls.conflicts_with:
                if feature_manager.is_enabled(feature_name, tenant_id):
                    return False
            
            # Check retail type compatibility
            if cls.retail_types and tenant_id:
                tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
                if tenant_retail_type not in cls.retail_types:
                    return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error checking model availability: {e}")
            return False
    
    @classmethod
    def create_table_if_needed(cls, tenant_id: Optional[str] = None):
        """Create table only if required features are enabled"""
        if cls.is_available_for_tenant(tenant_id):
            try:
                cls.__table__.create(db.engine, checkfirst=True)
                current_app.logger.info(f"Created table for {cls.__name__}")
                return True
            except Exception as e:
                current_app.logger.error(f"Error creating table for {cls.__name__}: {e}")
                return False
        return False
    
    @classmethod
    def get_feature_aware_query(cls, tenant_id: Optional[str] = None):
        """Get query filtered by feature availability"""
        if not cls.is_available_for_tenant(tenant_id):
            # Return empty query if model is not available
            return cls.query.filter(db.false())
        
        return cls.query
    
    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        """Get model information and requirements"""
        return {
            'name': cls.__name__,
            'table_name': cls.__table__.name,
            'required_features': cls.required_features,
            'optional_features': cls.optional_features,
            'retail_types': cls.retail_types,
            'conflicts_with': cls.conflicts_with,
            'category': cls.model_category,
            'version': cls.model_version,
            'deprecated': cls.deprecated,
            'deprecation_message': cls.deprecation_message
        }
    
    @classmethod
    def validate_feature_requirements(cls, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate feature requirements for this model"""
        try:
            from utils.feature_flag_manager import feature_manager
            
            validation_result = {
                'valid': True,
                'missing_features': [],
                'conflicting_features': [],
                'incompatible_retail_types': []
            }
            
            # Check required features
            for feature_name in cls.required_features:
                if not feature_manager.is_enabled(feature_name, tenant_id):
                    validation_result['missing_features'].append(feature_name)
                    validation_result['valid'] = False
            
            # Check conflicting features
            for feature_name in cls.conflicts_with:
                if feature_manager.is_enabled(feature_name, tenant_id):
                    validation_result['conflicting_features'].append(feature_name)
                    validation_result['valid'] = False
            
            # Check retail type compatibility
            if cls.retail_types and tenant_id:
                tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
                if tenant_retail_type not in cls.retail_types:
                    validation_result['incompatible_retail_types'].append(tenant_retail_type)
                    validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            current_app.logger.error(f"Error validating model requirements: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    @classmethod
    def get_feature_summary(cls, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get summary of feature status for this model"""
        try:
            from utils.feature_flag_manager import feature_manager
            
            summary = {
                'model_name': cls.__name__,
                'available': cls.is_available_for_tenant(tenant_id),
                'features': {},
                'retail_type_compatible': True
            }
            
            # Check required features
            for feature_name in cls.required_features:
                is_enabled = feature_manager.is_enabled(feature_name, tenant_id)
                summary['features'][feature_name] = {
                    'required': True,
                    'enabled': is_enabled,
                    'status': 'satisfied' if is_enabled else 'missing'
                }
            
            # Check optional features
            for feature_name in cls.optional_features:
                is_enabled = feature_manager.is_enabled(feature_name, tenant_id)
                summary['features'][feature_name] = {
                    'required': False,
                    'enabled': is_enabled,
                    'status': 'optional'
                }
            
            # Check conflicting features
            for feature_name in cls.conflicts_with:
                is_enabled = feature_manager.is_enabled(feature_name, tenant_id)
                summary['features'][feature_name] = {
                    'required': False,
                    'enabled': is_enabled,
                    'status': 'conflict' if is_enabled else 'ok'
                }
            
            # Check retail type compatibility
            if cls.retail_types and tenant_id:
                tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
                summary['retail_type_compatible'] = tenant_retail_type in cls.retail_types
                summary['tenant_retail_type'] = tenant_retail_type
                summary['supported_retail_types'] = cls.retail_types
            
            return summary
            
        except Exception as e:
            current_app.logger.error(f"Error getting feature summary: {e}")
            return {
                'model_name': cls.__name__,
                'available': False,
                'error': str(e)
            }


class ConditionalModelRegistry:
    """
    Registry for conditional models based on feature flags
    """
    
    def __init__(self):
        self.models = {}
        self.feature_models = {}  # Maps feature names to models that require them
        self.retail_type_models = {}  # Maps retail types to models that support them
    
    def register_model(self, model_class, feature_requirements=None, retail_types=None):
        """Register a model with feature requirements"""
        model_name = model_class.__name__
        
        # Store model info
        self.models[model_name] = {
            'class': model_class,
            'required_features': feature_requirements or getattr(model_class, 'required_features', []),
            'retail_types': retail_types or getattr(model_class, 'retail_types', [])
        }
        
        # Update feature mappings
        for feature in self.models[model_name]['required_features']:
            if feature not in self.feature_models:
                self.feature_models[feature] = []
            self.feature_models[feature].append(model_name)
        
        # Update retail type mappings
        for retail_type in self.models[model_name]['retail_types']:
            if retail_type not in self.retail_type_models:
                self.retail_type_models[retail_type] = []
            self.retail_type_models[retail_type].append(model_name)
    
    def get_available_models(self, tenant_id: Optional[str] = None) -> List[str]:
        """Get list of models available for tenant"""
        available_models = []
        
        try:
            from utils.feature_flag_manager import feature_manager
            
            for model_name, model_info in self.models.items():
                # Check required features
                features_satisfied = True
                for feature in model_info['required_features']:
                    if not feature_manager.is_enabled(feature, tenant_id):
                        features_satisfied = False
                        break
                
                # Check retail type compatibility
                retail_type_compatible = True
                if model_info['retail_types'] and tenant_id:
                    tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
                    if tenant_retail_type not in model_info['retail_types']:
                        retail_type_compatible = False
                
                if features_satisfied and retail_type_compatible:
                    available_models.append(model_name)
            
            return available_models
            
        except Exception as e:
            current_app.logger.error(f"Error getting available models: {e}")
            return []
    
    def get_models_for_feature(self, feature_name: str) -> List[str]:
        """Get models that require a specific feature"""
        return self.feature_models.get(feature_name, [])
    
    def get_models_for_retail_type(self, retail_type: str) -> List[str]:
        """Get models that support a specific retail type"""
        return self.retail_type_models.get(retail_type, [])
    
    def create_tables_for_tenant(self, tenant_id: Optional[str] = None):
        """Create tables for all available models for a tenant"""
        created_tables = []
        failed_tables = []
        
        available_models = self.get_available_models(tenant_id)
        
        for model_name in available_models:
            model_class = self.models[model_name]['class']
            try:
                if model_class.create_table_if_needed(tenant_id):
                    created_tables.append(model_name)
                else:
                    failed_tables.append(model_name)
            except Exception as e:
                current_app.logger.error(f"Error creating table for {model_name}: {e}")
                failed_tables.append(model_name)
        
        return {
            'created': created_tables,
            'failed': failed_tables,
            'total_attempted': len(available_models)
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            'total_models': len(self.models),
            'feature_mappings': {feature: len(models) for feature, models in self.feature_models.items()},
            'retail_type_mappings': {retail_type: len(models) for retail_type, models in self.retail_type_models.items()},
            'models_by_category': self._get_models_by_category()
        }
    
    def _get_models_by_category(self) -> Dict[str, List[str]]:
        """Group models by category"""
        categories = {}
        
        for model_name, model_info in self.models.items():
            model_class = model_info['class']
            category = getattr(model_class, 'model_category', 'core')
            
            if category not in categories:
                categories[category] = []
            categories[category].append(model_name)
        
        return categories


# Global model registry instance
model_registry = ConditionalModelRegistry()