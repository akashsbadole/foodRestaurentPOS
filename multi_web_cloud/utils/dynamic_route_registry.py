"""
Register routes conditionally based on feature flags
"""

from typing import Dict, List, Optional, Callable, Any
from flask import Blueprint, current_app
from utils.feature_flag_manager import feature_manager
from utils.tenant_query_manager import get_current_tenant_id


class RouteMetadata:
    """Metadata for registered routes"""
    
    def __init__(self, rule: str, endpoint: str, view_func: Callable, 
                 required_features: Optional[List[str]] = None,
                 retail_types: Optional[List[str]] = None,
                 methods: Optional[List[str]] = None,
                 **options):
        self.rule = rule
        self.endpoint = endpoint
        self.view_func = view_func
        self.required_features = required_features or []
        self.retail_types = retail_types or []
        self.methods = methods or ['GET']
        self.options = options
        self.is_active = False
        self.last_check_tenant = None


class DynamicRouteRegistry:
    """
    Register routes conditionally based on feature flags
    """
    
    def __init__(self, app):
        self.app = app
        self.registered_blueprints = {}
        self.route_metadata = {}
        self.endpoint_registry = {}
        self.feature_routes = {}  # Maps features to routes that require them
        self.retail_type_routes = {}  # Maps retail types to routes that support them
        self._initialized = False
    
    def initialize(self):
        """Initialize the route registry"""
        if self._initialized:
            return
        
        self._build_feature_mappings()
        self._initialized = True
    
    def register_blueprint_conditional(self, blueprint: Blueprint, 
                                 required_features: Optional[List[str]] = None,
                                 retail_types: Optional[List[str]] = None):
        """Register blueprint only if requirements are met"""
        try:
            # Store blueprint metadata
            blueprint_name = blueprint.name
            self.registered_blueprints[blueprint_name] = {
                'blueprint': blueprint,
                'required_features': required_features or [],
                'retail_types': retail_types or [],
                'registered': False
            }
            
            # Build feature mappings
            if required_features:
                for feature in required_features:
                    if feature not in self.feature_routes:
                        self.feature_routes[feature] = []
                    self.feature_routes[feature].append(blueprint_name)
            
            if retail_types:
                for retail_type in retail_types:
                    if retail_type not in self.retail_type_routes:
                        self.retail_type_routes[retail_type] = []
                    self.retail_type_routes[retail_type].append(blueprint_name)
            
            current_app.logger.info(f"Registered conditional blueprint: {blueprint_name}")
            
        except Exception as e:
            current_app.logger.error(f"Error registering conditional blueprint: {e}")
    
    def register_route_conditional(self, rule: str, endpoint: str, view_func: Callable,
                                 required_features: Optional[List[str]] = None,
                                 retail_types: Optional[List[str]] = None,
                                 **options):
        """Register route with feature conditions"""
        try:
            # Create route metadata
            metadata = RouteMetadata(
                rule=rule,
                endpoint=endpoint,
                view_func=view_func,
                required_features=required_features,
                retail_types=retail_types,
                **options
            )
            
            # Store metadata
            self.route_metadata[endpoint] = metadata
            
            # Build feature mappings
            if required_features:
                for feature in required_features:
                    if feature not in self.feature_routes:
                        self.feature_routes[feature] = []
                    self.feature_routes[feature].append(endpoint)
            
            if retail_types:
                for retail_type in retail_types:
                    if retail_type not in self.retail_type_routes:
                        self.retail_type_routes[retail_type] = []
                    self.retail_type_routes[retail_type].append(endpoint)
            
            current_app.logger.info(f"Registered conditional route: {endpoint}")
            
        except Exception as e:
            current_app.logger.error(f"Error registering conditional route: {e}")
    
    def update_routes_for_tenant(self, tenant_id: str):
        """Update available routes for tenant"""
        if not self._initialized:
            self.initialize()
        
        try:
            # Get tenant's enabled features and retail type
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            
            # Update blueprints
            for blueprint_name, blueprint_info in self.registered_blueprints.items():
                should_register = self._should_register_blueprint(
                    blueprint_info, enabled_features, tenant_retail_type
                )
                
                if should_register and not blueprint_info['registered']:
                    # Register the blueprint
                    self.app.register_blueprint(blueprint_info['blueprint'])
                    blueprint_info['registered'] = True
                    current_app.logger.info(f"Registered blueprint for tenant {tenant_id}: {blueprint_name}")
                
                elif not should_register and blueprint_info['registered']:
                    # Blueprint would be unregistered if we could do that
                    # For now, we just mark it as inactive
                    blueprint_info['registered'] = False
                    current_app.logger.info(f"Unregistered blueprint for tenant {tenant_id}: {blueprint_name}")
            
            # Update routes
            for endpoint, metadata in self.route_metadata.items():
                should_activate = self._should_activate_route(
                    metadata, enabled_features, tenant_retail_type
                )
                
                if should_activate and not metadata.is_active:
                    # Register the route
                    self.app.add_url_rule(
                        metadata.rule,
                        endpoint=metadata.endpoint,
                        view_func=metadata.view_func,
                        methods=metadata.methods,
                        **metadata.options
                    )
                    metadata.is_active = True
                    metadata.last_check_tenant = tenant_id
                    current_app.logger.info(f"Activated route for tenant {tenant_id}: {endpoint}")
                
                elif not should_activate and metadata.is_active:
                    # Route would be unregistered if we could do that
                    # For now, we just mark it as inactive
                    metadata.is_active = False
                    metadata.last_check_tenant = tenant_id
                    current_app.logger.info(f"Deactivated route for tenant {tenant_id}: {endpoint}")
            
        except Exception as e:
            current_app.logger.error(f"Error updating routes for tenant {tenant_id}: {e}")
    
    def get_available_routes(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get list of routes available to tenant"""
        if not self._initialized:
            self.initialize()
        
        available_routes = []
        
        try:
            # Get tenant's enabled features and retail type
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            
            # Check blueprints
            for blueprint_name, blueprint_info in self.registered_blueprints.items():
                if self._should_register_blueprint(
                    blueprint_info, enabled_features, tenant_retail_type
                ):
                    available_routes.append({
                        'type': 'blueprint',
                        'name': blueprint_name,
                        'required_features': blueprint_info['required_features'],
                        'retail_types': blueprint_info['retail_types']
                    })
            
            # Check routes
            for endpoint, metadata in self.route_metadata.items():
                if self._should_activate_route(
                    metadata, enabled_features, tenant_retail_type
                ):
                    available_routes.append({
                        'type': 'route',
                        'endpoint': endpoint,
                        'rule': metadata.rule,
                        'methods': metadata.methods,
                        'required_features': metadata.required_features,
                        'retail_types': metadata.retail_types
                    })
            
            return available_routes
            
        except Exception as e:
            current_app.logger.error(f"Error getting available routes for tenant {tenant_id}: {e}")
            return []
    
    def get_routes_for_feature(self, feature_name: str) -> List[Dict[str, Any]]:
        """Get routes that require a specific feature"""
        routes = []
        
        # Check blueprints
        blueprint_names = self.feature_routes.get(feature_name, [])
        for blueprint_name in blueprint_names:
            if blueprint_name in self.registered_blueprints:
                blueprint_info = self.registered_blueprints[blueprint_name]
                routes.append({
                    'type': 'blueprint',
                    'name': blueprint_name,
                    'info': blueprint_info
                })
        
        # Check routes
        endpoints = self.feature_routes.get(feature_name, [])
        for endpoint in endpoints:
            if endpoint in self.route_metadata:
                metadata = self.route_metadata[endpoint]
                routes.append({
                    'type': 'route',
                    'endpoint': endpoint,
                    'metadata': metadata
                })
        
        return routes
    
    def get_routes_for_retail_type(self, retail_type: str) -> List[Dict[str, Any]]:
        """Get routes that support a specific retail type"""
        routes = []
        
        # Check blueprints
        blueprint_names = self.retail_type_routes.get(retail_type, [])
        for blueprint_name in blueprint_names:
            if blueprint_name in self.registered_blueprints:
                blueprint_info = self.registered_blueprints[blueprint_name]
                routes.append({
                    'type': 'blueprint',
                    'name': blueprint_name,
                    'info': blueprint_info
                })
        
        # Check routes
        endpoints = self.retail_type_routes.get(retail_type, [])
        for endpoint in endpoints:
            if endpoint in self.route_metadata:
                metadata = self.route_metadata[endpoint]
                routes.append({
                    'type': 'route',
                    'endpoint': endpoint,
                    'metadata': metadata
                })
        
        return routes
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            'total_blueprints': len(self.registered_blueprints),
            'total_routes': len(self.route_metadata),
            'feature_mappings': {feature: len(routes) for feature, routes in self.feature_routes.items()},
            'retail_type_mappings': {retail_type: len(routes) for retail_type, routes in self.retail_type_routes.items()},
            'active_blueprints': len([bp for bp in self.registered_blueprints.values() if bp['registered']]),
            'active_routes': len([route for route in self.route_metadata.values() if route.is_active])
        }
    
    def _should_register_blueprint(self, blueprint_info: Dict[str, Any], 
                               enabled_features: set, tenant_retail_type: str) -> bool:
        """Check if blueprint should be registered for tenant"""
        # Check required features
        for feature in blueprint_info['required_features']:
            if feature not in enabled_features:
                return False
        
        # Check retail type compatibility
        if blueprint_info['retail_types']:
            return tenant_retail_type in blueprint_info['retail_types']
        
        return True
    
    def _should_activate_route(self, metadata: RouteMetadata, 
                            enabled_features: set, tenant_retail_type: str) -> bool:
        """Check if route should be activated for tenant"""
        # Check required features
        for feature in metadata.required_features:
            if feature not in enabled_features:
                return False
        
        # Check retail type compatibility
        if metadata.retail_types:
            return tenant_retail_type in metadata.retail_types
        
        return True
    
    def _build_feature_mappings(self):
        """Build feature and retail type mappings from registered routes"""
        # Clear existing mappings
        self.feature_routes.clear()
        self.retail_type_routes.clear()
        
        # Rebuild from blueprints
        for blueprint_name, blueprint_info in self.registered_blueprints.items():
            for feature in blueprint_info['required_features']:
                if feature not in self.feature_routes:
                    self.feature_routes[feature] = []
                if blueprint_name not in self.feature_routes[feature]:
                    self.feature_routes[feature].append(blueprint_name)
            
            for retail_type in blueprint_info['retail_types']:
                if retail_type not in self.retail_type_routes:
                    self.retail_type_routes[retail_type] = []
                if blueprint_name not in self.retail_type_routes[retail_type]:
                    self.retail_type_routes[retail_type].append(blueprint_name)
        
        # Rebuild from routes
        for endpoint, metadata in self.route_metadata.items():
            for feature in metadata.required_features:
                if feature not in self.feature_routes:
                    self.feature_routes[feature] = []
                if endpoint not in self.feature_routes[feature]:
                    self.feature_routes[feature].append(endpoint)
            
            for retail_type in metadata.retail_types:
                if retail_type not in self.retail_type_routes:
                    self.retail_type_routes[retail_type] = []
                if endpoint not in self.retail_type_routes[retail_type]:
                    self.retail_type_routes[retail_type].append(endpoint)


# Global route registry instance
route_registry = None


def get_route_registry(app) -> DynamicRouteRegistry:
    """Get or create the global route registry instance"""
    global route_registry
    if route_registry is None:
        route_registry = DynamicRouteRegistry(app)
    return route_registry