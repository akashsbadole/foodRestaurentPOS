"""
Load models conditionally based on feature flags
"""

import importlib
import inspect
from typing import Dict, List, Optional, Any, Type
from flask import current_app
from models import db
from models.feature_aware_model import model_registry, FeatureAwareModel


class DynamicModelLoader:
    """
    Load models conditionally based on feature flags
    """
    
    def __init__(self, feature_manager):
        self.feature_manager = feature_manager
        self.loaded_models = {}
        self.model_dependencies = {}
        self.module_cache = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize the model loader"""
        if self._initialized:
            return
        
        self._discover_models()
        self._build_dependency_graph()
        self._initialized = True
    
    def load_models_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Load models based on tenant's feature flags"""
        if not self._initialized:
            self.initialize()
        
        results = {
            'loaded': [],
            'skipped': [],
            'failed': [],
            'dependencies': {}
        }
        
        try:
            # Get available models for tenant
            available_models = model_registry.get_available_models(tenant_id)
            
            # Load models in dependency order
            load_order = self._get_load_order(available_models)
            
            for model_name in load_order:
                try:
                    model_info = model_registry.models.get(model_name)
                    if not model_info:
                        continue
                    
                    model_class = model_info['class']
                    
                    # Check if model is already loaded
                    if model_name in self.loaded_models:
                        results['loaded'].append(model_name)
                        continue
                    
                    # Load and create table
                    if model_class.create_table_if_needed(tenant_id):
                        self.loaded_models[model_name] = model_class
                        results['loaded'].append(model_name)
                        
                        # Track dependencies
                        results['dependencies'][model_name] = model_info['required_features']
                    else:
                        results['skipped'].append({
                            'model': model_name,
                            'reason': 'Table creation failed or features not satisfied'
                        })
                        
                except Exception as e:
                    current_app.logger.error(f"Error loading model {model_name}: {e}")
                    results['failed'].append({
                        'model': model_name,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            current_app.logger.error(f"Error loading models for tenant {tenant_id}: {e}")
            return results
    
    def register_conditional_model(self, model_class: Type[FeatureAwareModel], 
                               required_features: Optional[List[str]] = None,
                               retail_types: Optional[List[str]] = None):
        """Register model with feature requirements"""
        try:
            # Set model attributes if provided
            if required_features:
                model_class.required_features = required_features
            if retail_types:
                model_class.retail_types = retail_types
            
            # Register with model registry
            model_registry.register_model(model_class, required_features, retail_types)
            
            current_app.logger.info(f"Registered conditional model: {model_class.__name__}")
            
        except Exception as e:
            current_app.logger.error(f"Error registering model {model_class.__name__}: {e}")
    
    def create_model_tables(self, tenant_id: str) -> Dict[str, Any]:
        """Create tables only for enabled features"""
        return model_registry.create_tables_for_tenant(tenant_id)
    
    def get_model(self, model_name: str, tenant_id: Optional[str] = None) -> Optional[Type[FeatureAwareModel]]:
        """Get model instance if available"""
        if not self._initialized:
            self.initialize()
        
        # Check if model is loaded
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        # Check if model is available for tenant
        if tenant_id and model_registry.get_available_models(tenant_id):
            available_models = model_registry.get_available_models(tenant_id)
            if model_name in available_models:
                model_info = model_registry.models.get(model_name)
                if model_info:
                    return model_info['class']
        
        return None
    
    def get_loaded_models(self) -> Dict[str, Type[FeatureAwareModel]]:
        """Get all loaded models"""
        return self.loaded_models.copy()
    
    def reload_models_for_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Reload models for tenant (useful for feature changes)"""
        # Clear cache for tenant
        self.feature_manager.cache.invalidate_tenant_cache(tenant_id)
        
        # Clear loaded models for this tenant
        tenant_models = [name for name, model in self.loaded_models.items() 
                        if model.is_available_for_tenant(tenant_id)]
        
        for model_name in tenant_models:
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]
        
        # Reload models
        return self.load_models_for_tenant(tenant_id)
    
    def get_model_dependencies(self, model_name: str) -> Dict[str, Any]:
        """Get dependencies for a model"""
        model_info = model_registry.models.get(model_name)
        if not model_info:
            return {}
        
        return {
            'required_features': model_info['required_features'],
            'retail_types': model_info['retail_types'],
            'feature_models': self.feature_manager.get_feature_dependencies(model_name)
        }
    
    def validate_model_dependencies(self, tenant_id: str) -> Dict[str, Any]:
        """Validate all model dependencies for tenant"""
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'model_status': {}
        }
        
        try:
            available_models = model_registry.get_available_models(tenant_id)
            
            for model_name in available_models:
                model_info = model_registry.models.get(model_name)
                if not model_info:
                    continue
                
                model_class = model_info['class']
                validation = model_class.validate_feature_requirements(tenant_id)
                
                validation_results['model_status'][model_name] = validation
                
                if not validation['valid']:
                    validation_results['valid'] = False
                    validation_results['errors'].append(
                        f"Model {model_name} has validation errors: {validation}"
                    )
            
            return validation_results
            
        except Exception as e:
            current_app.logger.error(f"Error validating model dependencies: {e}")
            validation_results['valid'] = False
            validation_results['errors'].append(str(e))
            return validation_results
    
    def _discover_models(self):
        """Discover all feature-aware models in the application"""
        try:
            # Import all model modules
            model_modules = [
                'models.user',
                'models.category',
                'models.menu_item',
                'models.table',
                'models.order',
                'models.payment',
                'models.settings',
                'models.customer',
                'models.loyalty',
                'models.tenant'
            ]
            
            for module_name in model_modules:
                try:
                    module = importlib.import_module(module_name)
                    self.module_cache[module_name] = module
                    
                    # Find all FeatureAwareModel subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, FeatureAwareModel) and 
                            obj != FeatureAwareModel and 
                            hasattr(obj, '__tablename__')):
                            
                            # Auto-register the model
                            self.register_conditional_model(obj)
                            
                except ImportError as e:
                    current_app.logger.warning(f"Could not import module {module_name}: {e}")
                    
        except Exception as e:
            current_app.logger.error(f"Error discovering models: {e}")
    
    def _build_dependency_graph(self):
        """Build dependency graph for models"""
        self.model_dependencies = {}
        
        for model_name, model_info in model_registry.models.items():
            dependencies = model_info['required_features']
            self.model_dependencies[model_name] = dependencies
    
    def _get_load_order(self, models: List[str]) -> List[str]:
        """Get models in dependency order (topological sort)"""
        visited = set()
        temp_visited = set()
        load_order = []
        
        def visit(model_name: str):
            if model_name in temp_visited:
                # Circular dependency detected
                current_app.logger.warning(f"Circular dependency detected for model {model_name}")
                return
            
            if model_name in visited:
                return
            
            temp_visited.add(model_name)
            
            # Visit dependencies first
            dependencies = self.model_dependencies.get(model_name, [])
            for dep in dependencies:
                # Find models that require this feature
                dep_models = model_registry.get_models_for_feature(dep)
                for dep_model in dep_models:
                    if dep_model in models:
                        visit(dep_model)
            
            temp_visited.remove(model_name)
            visited.add(model_name)
            load_order.append(model_name)
        
        for model_name in models:
            if model_name not in visited:
                visit(model_name)
        
        return load_order
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get model loading statistics"""
        return {
            'total_models_discovered': len(model_registry.models),
            'loaded_models': len(self.loaded_models),
            'model_dependencies': self.model_dependencies,
            'registry_stats': model_registry.get_registry_stats()
        }


# Global model loader instance
dynamic_model_loader = None


def get_model_loader(feature_manager) -> DynamicModelLoader:
    """Get or create the global model loader instance"""
    global dynamic_model_loader
    if dynamic_model_loader is None:
        dynamic_model_loader = DynamicModelLoader(feature_manager)
    return dynamic_model_loader