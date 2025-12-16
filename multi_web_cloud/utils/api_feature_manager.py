"""
Manage API endpoints based on feature flags
"""

from typing import Dict, List, Optional, Callable, Any
from flask import jsonify, request, current_app
from utils.feature_flag_manager import feature_manager
from utils.tenant_query_manager import get_current_tenant_id


class APIEndpoint:
    """API endpoint metadata"""
    
    def __init__(self, endpoint: str, path: str, method: str, handler: Callable,
                 required_features: Optional[List[str]] = None,
                 retail_types: Optional[List[str]] = None,
                 description: Optional[str] = None,
                 category: Optional[str] = None):
        self.endpoint = endpoint
        self.path = path
        self.method = method.upper()
        self.handler = handler
        self.required_features = required_features or []
        self.retail_types = retail_types or []
        self.description = description
        self.category = category
        self.is_active = False
        self.last_check_tenant = None


class APIFeatureManager:
    """
    Manage API endpoints based on feature flags
    """
    
    def __init__(self, feature_manager):
        self.feature_manager = feature_manager
        self.endpoint_registry = {}
        self.feature_endpoints = {}  # Maps features to endpoints that require them
        self.retail_type_endpoints = {}  # Maps retail types to endpoints that support them
        self.category_endpoints = {}  # Maps categories to endpoints
        self._initialized = False
    
    def initialize(self):
        """Initialize API feature manager"""
        if self._initialized:
            return
        
        self._build_feature_mappings()
        self._initialized = True
    
    def register_api_endpoint(self, endpoint: str, path: str, method: str, handler: Callable,
                           required_features: Optional[List[str]] = None,
                           retail_types: Optional[List[str]] = None,
                           description: Optional[str] = None,
                           category: Optional[str] = None):
        """Register API endpoint with feature requirements"""
        try:
            # Create endpoint metadata
            api_endpoint = APIEndpoint(
                endpoint=endpoint,
                path=path,
                method=method,
                handler=handler,
                required_features=required_features,
                retail_types=retail_types,
                description=description,
                category=category
            )
            
            # Store endpoint
            self.endpoint_registry[endpoint] = api_endpoint
            
            # Build feature mappings
            if required_features:
                for feature in required_features:
                    if feature not in self.feature_endpoints:
                        self.feature_endpoints[feature] = []
                    self.feature_endpoints[feature].append(endpoint)
            
            if retail_types:
                for retail_type in retail_types:
                    if retail_type not in self.retail_type_endpoints:
                        self.retail_type_endpoints[retail_type] = []
                    self.retail_type_endpoints[retail_type].append(endpoint)
            
            if category:
                if category not in self.category_endpoints:
                    self.category_endpoints[category] = []
                self.category_endpoints[category].append(endpoint)
            
            current_app.logger.info(f"Registered API endpoint: {endpoint} ({method} {path})")
            
        except Exception as e:
            current_app.logger.error(f"Error registering API endpoint {endpoint}: {e}")
    
    def filter_api_response(self, response_data: Any, endpoint: str, tenant_id: Optional[str] = None) -> Any:
        """Filter API response based on available features"""
        try:
            if not self._initialized:
                self.initialize()
            
            # Get endpoint metadata
            api_endpoint = self.endpoint_registry.get(endpoint)
            if not api_endpoint:
                return response_data
            
            # Check if endpoint is available
            if not self._is_endpoint_available(api_endpoint, tenant_id):
                return {
                    'error': 'Endpoint not available',
                    'endpoint': endpoint,
                    'message': f'The {endpoint} endpoint is not available for your tenant'
                }
            
            # Filter response data based on features
            if isinstance(response_data, dict):
                filtered_data = self._filter_response_data(response_data, tenant_id)
                return filtered_data
            elif isinstance(response_data, list):
                filtered_list = []
                for item in response_data:
                    if isinstance(item, dict):
                        filtered_item = self._filter_response_data(item, tenant_id)
                        filtered_list.append(filtered_item)
                    else:
                        filtered_list.append(item)
                return filtered_list
            
            return response_data
            
        except Exception as e:
            current_app.logger.error(f"Error filtering API response: {e}")
            return response_data
    
    def generate_feature_aware_swagger(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate Swagger documentation for available features"""
        if not self._initialized:
            self.initialize()
        
        try:
            # Get tenant's enabled features and retail type
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            
            swagger = {
                'openapi': '3.0.0',
                'info': {
                    'title': 'Multi-Retail POS API',
                    'description': f'API documentation for {tenant_retail_type or "default"} retail type',
                    'version': '1.0.0'
                },
                'paths': {},
                'components': {
                    'schemas': {},
                    'securitySchemes': {}
                }
            }
            
            # Add available endpoints to paths
            for endpoint, api_endpoint in self.endpoint_registry.items():
                if self._is_endpoint_available(api_endpoint, tenant_id):
                    path_doc = self._generate_endpoint_documentation(api_endpoint, enabled_features)
                    swagger['paths'][api_endpoint.path] = path_doc
            
            return swagger
            
        except Exception as e:
            current_app.logger.error(f"Error generating Swagger documentation: {e}")
            return {'error': 'Failed to generate documentation'}
    
    def get_available_endpoints(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of endpoints available to tenant"""
        if not self._initialized:
            self.initialize()
        
        available_endpoints = []
        
        try:
            # Get tenant's enabled features and retail type
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            
            for endpoint, api_endpoint in self.endpoint_registry.items():
                if self._is_endpoint_available(api_endpoint, tenant_id):
                    available_endpoints.append({
                        'endpoint': endpoint,
                        'path': api_endpoint.path,
                        'method': api_endpoint.method,
                        'description': api_endpoint.description,
                        'category': api_endpoint.category,
                        'required_features': api_endpoint.required_features,
                        'retail_types': api_endpoint.retail_types
                    })
            
            return available_endpoints
            
        except Exception as e:
            current_app.logger.error(f"Error getting available endpoints: {e}")
            return []
    
    def get_endpoints_for_feature(self, feature_name: str) -> List[Dict[str, Any]]:
        """Get endpoints that require a specific feature"""
        endpoints = []
        
        endpoint_names = self.feature_endpoints.get(feature_name, [])
        for endpoint_name in endpoint_names:
            if endpoint_name in self.endpoint_registry:
                api_endpoint = self.endpoint_registry[endpoint_name]
                endpoints.append({
                    'endpoint': endpoint_name,
                    'path': api_endpoint.path,
                    'method': api_endpoint.method,
                    'description': api_endpoint.description,
                    'category': api_endpoint.category
                })
        
        return endpoints
    
    def get_endpoints_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get endpoints in a specific category"""
        endpoints = []
        
        endpoint_names = self.category_endpoints.get(category, [])
        for endpoint_name in endpoint_names:
            if endpoint_name in self.endpoint_registry:
                api_endpoint = self.endpoint_registry[endpoint_name]
                endpoints.append({
                    'endpoint': endpoint_name,
                    'path': api_endpoint.path,
                    'method': api_endpoint.method,
                    'description': api_endpoint.description,
                    'required_features': api_endpoint.required_features,
                    'retail_types': api_endpoint.retail_types
                })
        
        return endpoints
    
    def update_endpoints_for_tenant(self, tenant_id: str):
        """Update available endpoints for tenant"""
        if not self._initialized:
            self.initialize()
        
        try:
            # Get tenant's enabled features and retail type
            enabled_features = feature_manager.get_enabled_features(tenant_id)
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            
            # Update endpoint availability
            for endpoint, api_endpoint in self.endpoint_registry.items():
                is_available = self._is_endpoint_available(api_endpoint, tenant_id)
                
                if is_available and not api_endpoint.is_active:
                    api_endpoint.is_active = True
                    api_endpoint.last_check_tenant = tenant_id
                    current_app.logger.info(f"Activated API endpoint for tenant {tenant_id}: {endpoint}")
                
                elif not is_available and api_endpoint.is_active:
                    api_endpoint.is_active = False
                    api_endpoint.last_check_tenant = tenant_id
                    current_app.logger.info(f"Deactivated API endpoint for tenant {tenant_id}: {endpoint}")
            
        except Exception as e:
            current_app.logger.error(f"Error updating endpoints for tenant {tenant_id}: {e}")
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get API endpoint statistics"""
        return {
            'total_endpoints': len(self.endpoint_registry),
            'feature_mappings': {feature: len(endpoints) for feature, endpoints in self.feature_endpoints.items()},
            'retail_type_mappings': {retail_type: len(endpoints) for retail_type, endpoints in self.retail_type_endpoints.items()},
            'category_mappings': {category: len(endpoints) for category, endpoints in self.category_endpoints.items()},
            'active_endpoints': len([ep for ep in self.endpoint_registry.values() if ep.is_active])
        }
    
    def _is_endpoint_available(self, api_endpoint: APIEndpoint, tenant_id: Optional[str] = None) -> bool:
        """Check if endpoint is available for tenant"""
        # Check required features
        for feature in api_endpoint.required_features:
            if not feature_manager.is_enabled(feature, tenant_id):
                return False
        
        # Check retail type compatibility
        if api_endpoint.retail_types and tenant_id:
            tenant_retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            if tenant_retail_type not in api_endpoint.retail_types:
                return False
        
        return True
    
    def _filter_response_data(self, data: Dict[str, Any], tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Filter response data based on available features"""
        filtered_data = data.copy()
        
        # Remove fields that require features not enabled
        field_feature_mapping = {
            'table_id': 'FEATURE_TABLE_MANAGEMENT',
            'kot_data': 'FEATURE_KOT_PRINTING',
            'kitchen_display': 'FEATURE_KITCHEN_DISPLAY',
            'size_variants': 'FEATURE_SIZE_VARIANTS',
            'color_variants': 'FEATURE_COLOR_VARIANTS',
            'expiry_date': 'FEATURE_EXPIRY_TRACKING',
            'batch_number': 'FEATURE_BATCH_TRACKING',
            'weight': 'FEATURE_WEIGHING_SCALE'
        }
        
        for field, feature in field_feature_mapping.items():
            if field in filtered_data and not feature_manager.is_enabled(feature, tenant_id):
                del filtered_data[field]
        
        return filtered_data
    
    def _generate_endpoint_documentation(self, api_endpoint: APIEndpoint, enabled_features: set) -> Dict[str, Any]:
        """Generate Swagger documentation for an endpoint"""
        doc = {
            api_endpoint.method.lower(): {
                'summary': api_endpoint.description or f"{api_endpoint.endpoint} endpoint",
                'description': f"Requires features: {', '.join(api_endpoint.required_features)}",
                'tags': [api_endpoint.category or 'default'],
                'responses': {
                    '200': {
                        'description': 'Successful response'
                    },
                    '403': {
                        'description': 'Feature not available'
                    }
                }
            }
        }
        
        # Add parameter documentation based on features
        if api_endpoint.required_features:
            doc[api_endpoint.method.lower()]['parameters'] = [
                {
                    'name': 'X-Tenant-ID',
                    'in': 'header',
                    'required': True,
                    'description': 'Tenant ID for multi-tenant access'
                }
            ]
        
        return doc
    
    def _build_feature_mappings(self):
        """Build feature and retail type mappings from registered endpoints"""
        # Clear existing mappings
        self.feature_endpoints.clear()
        self.retail_type_endpoints.clear()
        self.category_endpoints.clear()
        
        # Rebuild from endpoints
        for endpoint, api_endpoint in self.endpoint_registry.items():
            for feature in api_endpoint.required_features:
                if feature not in self.feature_endpoints:
                    self.feature_endpoints[feature] = []
                if endpoint not in self.feature_endpoints[feature]:
                    self.feature_endpoints[feature].append(endpoint)
            
            for retail_type in api_endpoint.retail_types:
                if retail_type not in self.retail_type_endpoints:
                    self.retail_type_endpoints[retail_type] = []
                if endpoint not in self.retail_type_endpoints[retail_type]:
                    self.retail_type_endpoints[retail_type].append(endpoint)
            
            if api_endpoint.category:
                if api_endpoint.category not in self.category_endpoints:
                    self.category_endpoints[api_endpoint.category] = []
                if endpoint not in self.category_endpoints[api_endpoint.category]:
                    self.category_endpoints[api_endpoint.category].append(endpoint)


# Global API feature manager instance
api_feature_manager = None


def get_api_feature_manager(feature_manager) -> APIFeatureManager:
    """Get or create global API feature manager instance"""
    global api_feature_manager
    if api_feature_manager is None:
        api_feature_manager = APIFeatureManager(feature_manager)
    return api_feature_manager