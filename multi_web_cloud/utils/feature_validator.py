"""
Feature validation and conflict detection system
"""

from typing import Dict, List, Set, Any, Optional, Tuple
from flask import current_app
from models import FeatureDefinition, FeatureDependency, FeatureConflict


class ValidationResult:
    """Result of feature validation"""
    
    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str], 
                 enabled_features: Optional[Set[str]] = None):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.enabled_features = enabled_features or set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'enabled_features': list(self.enabled_features)
        }


class FeatureValidator:
    """
    Validate feature flags and detect conflicts
    """
    
    def __init__(self):
        self.dependency_cache = {}
        self.conflict_cache = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize the validator with database data"""
        if self._initialized:
            return
        
        self._load_dependencies()
        self._load_conflicts()
        self._initialized = True
    
    def validate_flag_values(self, flags: Dict[str, Any]) -> 'ValidationResult':
        """Validate flag values against definitions"""
        errors = []
        warnings = []
        valid_flags = {}
        
        # Get all feature definitions
        feature_definitions = {}
        try:
            definitions = FeatureDefinition.query.all()
            for definition in definitions:
                feature_definitions[definition.name] = definition
        except Exception as e:
            current_app.logger.error(f"Error loading feature definitions: {e}")
        
        # Validate each flag
        for flag_name, flag_value in flags.items():
            # Check if flag is a feature flag
            if not flag_name.startswith('FEATURE_'):
                continue
            
            # Get feature definition
            feature_def = feature_definitions.get(flag_name)
            if not feature_def:
                warnings.append(f"Unknown feature flag: {flag_name}")
                # Still include it with default boolean conversion
                valid_flags[flag_name] = self._convert_to_boolean(flag_value)
                continue
            
            # Check if feature is deprecated
            if feature_def.deprecated:
                warnings.append(f"Feature {flag_name} is deprecated: {feature_def.deprecation_message}")
            
            # Validate based on feature type
            try:
                if feature_def.feature_type == 'boolean':
                    valid_flags[flag_name] = self._convert_to_boolean(flag_value)
                elif feature_def.feature_type == 'string':
                    valid_flags[flag_name] = str(flag_value)
                elif feature_def.feature_type == 'numeric':
                    valid_flags[flag_name] = float(flag_value)
                elif feature_def.feature_type == 'json':
                    valid_flags[flag_name] = flag_value if isinstance(flag_value, dict) else {}
                
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid value for {flag_name}: {flag_value}. Error: {e}")
                # Use default value
                valid_flags[flag_name] = feature_def.default_value
        
        # Add default values for missing required features
        for flag_name, feature_def in feature_definitions.items():
            if feature_def.is_required and flag_name not in valid_flags:
                valid_flags[flag_name] = feature_def.default_value
        
        return ValidationResult(len(errors) == 0, errors, warnings, set(valid_flags.keys()))
    
    def validate_feature_combination(self, features: List[str], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate feature dependencies and conflicts"""
        if not self._initialized:
            self.initialize()
        
        errors = []
        warnings = []
        feature_set = set(features)
        
        # Check dependencies
        dependency_errors = self._check_dependencies(feature_set)
        errors.extend(dependency_errors)
        
        # Check conflicts
        conflict_errors = self._check_conflicts(feature_set)
        errors.extend(conflict_errors)
        
        # Check retail type compatibility
        retail_warnings = self._check_retail_type_compatibility(feature_set, tenant_id)
        warnings.extend(retail_warnings)
        
        # Check experimental features
        experimental_warnings = self._check_experimental_features(feature_set)
        warnings.extend(experimental_warnings)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'enabled_features': features
        }
    
    def validate_feature_enablement(self, feature_name: str, tenant_id: Optional[str] = None, 
                                current_features: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Validate if a feature can be enabled"""
        if not self._initialized:
            self.initialize()
        
        errors = []
        warnings = []
        
        # Check if feature exists
        feature_def = FeatureDefinition.query.filter_by(name=feature_name).first()
        if not feature_def:
            errors.append(f"Feature {feature_name} is not defined")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # Check if feature is deprecated
        if feature_def.deprecated:
            warnings.append(f"Feature {feature_name} is deprecated: {feature_def.deprecation_message}")
        
        # Check retail type compatibility
        if tenant_id:
            retail_warnings = self._check_retail_type_compatibility({feature_name}, tenant_id)
            warnings.extend(retail_warnings)
        
        # Check dependencies
        if current_features:
            # Check if enabling this feature would conflict with current features
            test_features = current_features.union({feature_name})
            dependency_errors = self._check_dependencies(test_features)
            conflict_errors = self._check_conflicts(test_features)
            errors.extend(dependency_errors)
            errors.extend(conflict_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def get_feature_dependencies(self, feature_name: str) -> Dict[str, List[str]]:
        """Get dependencies for a feature"""
        if not self._initialized:
            self.initialize()
        
        return self.dependency_cache.get(feature_name, {'requires': [], 'conflicts': [], 'optional': []})
    
    def get_feature_conflicts(self, feature_name: str) -> List[str]:
        """Get conflicts for a feature"""
        if not self._initialized:
            self.initialize()
        
        dependencies = self.dependency_cache.get(feature_name, {})
        return dependencies.get('conflicts', [])
    
    def get_required_features(self, feature_name: str) -> List[str]:
        """Get features required by a feature"""
        if not self._initialized:
            self.initialize()
        
        dependencies = self.dependency_cache.get(feature_name, {})
        return dependencies.get('requires', [])
    
    def _load_dependencies(self):
        """Load feature dependencies from database"""
        try:
            dependencies = FeatureDependency.query.all()
            
            for dep in dependencies:
                if dep.feature_name not in self.dependency_cache:
                    self.dependency_cache[dep.feature_name] = {
                        'requires': [],
                        'conflicts': [],
                        'optional': []
                    }
                
                if dep.dependency_type == 'required':
                    self.dependency_cache[dep.feature_name]['requires'].append(dep.depends_on_feature)
                elif dep.dependency_type == 'conflicts':
                    self.dependency_cache[dep.feature_name]['conflicts'].append(dep.depends_on_feature)
                elif dep.dependency_type == 'optional':
                    self.dependency_cache[dep.feature_name]['optional'].append(dep.depends_on_feature)
                    
        except Exception as e:
            current_app.logger.error(f"Error loading feature dependencies: {e}")
    
    def _load_conflicts(self):
        """Load feature conflicts from database"""
        try:
            conflicts = FeatureConflict.query.all()
            
            for conflict in conflicts:
                # Add conflicts to both features
                for feature in [conflict.feature_1, conflict.feature_2]:
                    other_feature = conflict.feature_2 if feature == conflict.feature_1 else conflict.feature_1
                    
                    if feature not in self.dependency_cache:
                        self.dependency_cache[feature] = {
                            'requires': [],
                            'conflicts': [],
                            'optional': []
                        }
                    
                    if other_feature not in self.dependency_cache[feature]['conflicts']:
                        self.dependency_cache[feature]['conflicts'].append(other_feature)
                        
        except Exception as e:
            current_app.logger.error(f"Error loading feature conflicts: {e}")
    
    def _check_dependencies(self, feature_set: Set[str]) -> List[str]:
        """Check if all dependencies are satisfied"""
        errors = []
        
        for feature in feature_set:
            dependencies = self.dependency_cache.get(feature, {})
            required_features = dependencies.get('requires', [])
            
            for required_feature in required_features:
                if required_feature not in feature_set:
                    errors.append(f"Feature {feature} requires {required_feature} to be enabled")
        
        return errors
    
    def _check_conflicts(self, feature_set: Set[str]) -> List[str]:
        """Check for conflicting features"""
        errors = []
        
        for feature in feature_set:
            dependencies = self.dependency_cache.get(feature, {})
            conflicting_features = dependencies.get('conflicts', [])
            
            for conflicting_feature in conflicting_features:
                if conflicting_feature in feature_set:
                    errors.append(f"Feature {feature} conflicts with {conflicting_feature}")
        
        return errors
    
    def _check_retail_type_compatibility(self, feature_set: Set[str], tenant_id: Optional[str] = None) -> List[str]:
        """Check if features are compatible with tenant's retail type"""
        warnings = []
        
        if not tenant_id:
            return warnings
        
        try:
            # Get tenant's retail type
            from models.tenant import TenantSettings
            settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
            if not settings:
                return warnings
            
            retail_type = getattr(settings, 'retail_type', 'restaurant')
            
            # Check each feature's retail type compatibility
            for feature_name in feature_set:
                feature_def = FeatureDefinition.query.filter_by(name=feature_name).first()
                if feature_def and not feature_def.is_supported_by_retail_type(retail_type):
                    warnings.append(f"Feature {feature_name} may not be fully compatible with {retail_type} retail type")
                    
        except Exception as e:
            current_app.logger.error(f"Error checking retail type compatibility: {e}")
        
        return warnings
    
    def _check_experimental_features(self, feature_set: Set[str]) -> List[str]:
        """Check for experimental features"""
        warnings = []
        
        for feature_name in feature_set:
            feature_def = FeatureDefinition.query.filter_by(name=feature_name).first()
            if feature_def and feature_def.is_experimental:
                warnings.append(f"Feature {feature_name} is experimental and may be unstable")
        
        return warnings
    
    def _convert_to_boolean(self, value: Any) -> bool:
        """Convert various value types to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        if isinstance(value, (int, float)):
            return bool(value)
        return bool(value)
    
    def get_dependency_graph(self) -> Dict[str, Dict[str, List[str]]]:
        """Get complete dependency graph"""
        if not self._initialized:
            self.initialize()
        
        return self.dependency_cache.copy()
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the feature graph"""
        if not self._initialized:
            self.initialize()
        
        visited = set()
        rec_stack = set()
        circular_deps = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found circular dependency
                cycle_start = path.index(node)
                circular_deps.append(path[cycle_start:] + [node])
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Check dependencies
            dependencies = self.dependency_cache.get(node, {})
            for dep in dependencies.get('requires', []):
                if dfs(dep, path.copy()):
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check all features
        for feature in self.dependency_cache:
            if feature not in visited:
                dfs(feature, [])
        
        return circular_deps