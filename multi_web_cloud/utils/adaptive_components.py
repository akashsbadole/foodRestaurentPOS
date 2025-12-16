"""
Feature-Aware JavaScript Components System
Manages dynamic JavaScript module loading and component behavior
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import current_app, request, jsonify
import json
from utils.feature_flag_manager import feature_manager


class AdaptiveComponent:
    """
    Represents an adaptive JavaScript component with feature dependencies
    """
    
    def __init__(self, component_id: str, **kwargs):
        self.component_id = component_id
        self.name = kwargs.get('name', component_id.title())
        self.description = kwargs.get('description', '')
        self.component_type = kwargs.get('component_type', 'module')  # module, script, style
        self.required_features = kwargs.get('required_features', [])
        self.excluded_features = kwargs.get('excluded_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.dependencies = kwargs.get('dependencies', [])  # Other components this depends on
        self.files = kwargs.get('files', [])  # JS/CSS files to load
        self.init_function = kwargs.get('init_function', f'init_{component_id}')
        self.config = kwargs.get('config', {})
        self.lazy_load = kwargs.get('lazy_load', False)
        self.priority = kwargs.get('priority', 100)  # Lower number = higher priority
        self.version = kwargs.get('version', '1.0.0')
        self.minified = kwargs.get('minified', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            'id': self.component_id,
            'name': self.name,
            'description': self.description,
            'type': self.component_type,
            'required_features': self.required_features,
            'excluded_features': self.excluded_features,
            'retail_types': self.retail_types,
            'dependencies': self.dependencies,
            'files': self.files,
            'init_function': self.init_function,
            'config': self.config,
            'lazy_load': self.lazy_load,
            'priority': self.priority,
            'version': self.version,
            'minified': self.minified
        }


class ComponentRegistry:
    """
    Registry for managing adaptive components
    """
    
    def __init__(self):
        self.components = {}
        self.component_groups = {}
        self.load_order = []
        self.loaded_components = set()
    
    def register_component(self, component: AdaptiveComponent):
        """Register a component"""
        self.components[component.component_id] = component
        self._update_load_order()
    
    def get_component(self, component_id: str) -> Optional[AdaptiveComponent]:
        """Get component by ID"""
        return self.components.get(component_id)
    
    def get_components_for_context(self, enabled_features: Set[str], retail_type: str, 
                                 user_role: Optional[str] = None) -> List[AdaptiveComponent]:
        """Get components that match the current context"""
        matching_components = []
        
        for component in self.components.values():
            # Check required features
            if component.required_features:
                if not all(feature in enabled_features for feature in component.required_features):
                    continue
            
            # Check excluded features
            if component.excluded_features:
                if any(feature in enabled_features for feature in component.excluded_features):
                    continue
            
            # Check retail type compatibility
            if component.retail_types and retail_type not in component.retail_types:
                continue
            
            matching_components.append(component)
        
        # Sort by priority
        matching_components.sort(key=lambda x: x.priority)
        
        return matching_components
    
    def get_load_order(self, components: List[AdaptiveComponent]) -> List[AdaptiveComponent]:
        """Get components in correct load order based on dependencies"""
        ordered_components = []
        processed = set()
        
        def process_component(component):
            if component.component_id in processed:
                return
            
            # Process dependencies first
            for dep_id in component.dependencies:
                dep_component = self.components.get(dep_id)
                if dep_component and dep_component in components:
                    process_component(dep_component)
            
            ordered_components.append(component)
            processed.add(component.component_id)
        
        for component in components:
            process_component(component)
        
        return ordered_components
    
    def _update_load_order(self):
        """Update the global load order"""
        all_components = list(self.components.values())
        all_components.sort(key=lambda x: x.priority)
        self.load_order = [comp.component_id for comp in all_components]


class ClientSideValidation:
    """
    Client-side validation rules and functions
    """
    
    def __init__(self):
        self.validation_rules = {}
        self.custom_validators = {}
    
    def register_validation_rule(self, rule_name: str, rule_config: Dict[str, Any]):
        """Register a validation rule"""
        self.validation_rules[rule_name] = rule_config
    
    def register_custom_validator(self, validator_name: str, validator_func: str):
        """Register a custom validator function"""
        self.custom_validators[validator_name] = validator_func
    
    def get_validation_config(self, form_config: Dict[str, Any]) -> Dict[str, Any]:
        """Get validation configuration for a form"""
        validation_config = {
            'rules': {},
            'messages': {},
            'custom_validators': self.custom_validators
        }
        
        for group_name, fields in form_config.get('field_groups', {}).items():
            for field in fields:
                field_id = field['id']
                field_validation = {}
                
                # Apply validation rules
                for rule_name, rule_config in field.get('validation', {}).items():
                    if rule_name in self.validation_rules:
                        field_validation[rule_name] = rule_config
                
                if field_validation:
                    validation_config['rules'][field_id] = field_validation
        
        return validation_config


class WorkflowManager:
    """
    Manages adaptive workflows for different retail types
    """
    
    def __init__(self):
        self.workflows = {}
        self.workflow_steps = {}
        self.current_workflows = {}  # tenant_id -> active workflows
    
    def register_workflow(self, workflow_id: str, workflow_config: Dict[str, Any]):
        """Register a workflow"""
        self.workflows[workflow_id] = workflow_config
    
    def register_workflow_step(self, workflow_id: str, step_id: str, step_config: Dict[str, Any]):
        """Register a workflow step"""
        if workflow_id not in self.workflow_steps:
            self.workflow_steps[workflow_id] = {}
        self.workflow_steps[workflow_id][step_id] = step_config
    
    def get_workflow(self, workflow_id: str, retail_type: str, 
                   enabled_features: Set[str]) -> Optional[Dict[str, Any]]:
        """Get workflow configuration"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        # Check if workflow is compatible with retail type
        if workflow.get('retail_types') and retail_type not in workflow['retail_types']:
            return None
        
        # Check required features
        if workflow.get('required_features'):
            if not all(feature in enabled_features for feature in workflow['required_features']):
                return None
        
        # Get workflow steps
        steps = self.workflow_steps.get(workflow_id, {})
        filtered_steps = {}
        
        for step_id, step_config in steps.items():
            # Check step requirements
            if step_config.get('required_features'):
                if not all(feature in enabled_features for feature in step_config['required_features']):
                    continue
            
            filtered_steps[step_id] = step_config
        
        return {
            'id': workflow_id,
            'name': workflow['name'],
            'description': workflow['description'],
            'steps': filtered_steps,
            'config': workflow.get('config', {})
        }


class AdaptiveComponentManager:
    """
    Main manager for adaptive components
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.component_registry = ComponentRegistry()
        self.validation = ClientSideValidation()
        self.workflow_manager = WorkflowManager()
        self.asset_bundles = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize component manager"""
        if self._initialized:
            return
        
        self._load_default_components()
        self._load_validation_rules()
        self._load_workflows()
        self._load_asset_bundles()
        self._initialized = True
    
    def _load_default_components(self):
        """Load default adaptive components"""
        # Core Components
        core_components = [
            AdaptiveComponent(
                'pos_core',
                name='POS Core',
                description='Core POS functionality',
                component_type='module',
                required_features=['FEATURE_SALES_PROCESSING'],
                files=['js/pos-core.js', 'css/pos-core.css'],
                init_function='initPOSCore',
                priority=1
            ),
            AdaptiveComponent(
                'product_catalog',
                name='Product Catalog',
                description='Product catalog management',
                component_type='module',
                required_features=['FEATURE_PRODUCT_CATALOG'],
                files=['js/product-catalog.js', 'css/product-catalog.css'],
                init_function='initProductCatalog',
                priority=10,
                dependencies=['pos_core']
            ),
            AdaptiveComponent(
                'barcode_scanner',
                name='Barcode Scanner',
                description='Barcode scanning functionality',
                component_type='module',
                required_features=['FEATURE_BARCODE_SCANNING'],
                files=['js/barcode-scanner.js'],
                init_function='initBarcodeScanner',
                priority=20,
                dependencies=['pos_core', 'product_catalog']
            ),
            AdaptiveComponent(
                'customer_management',
                name='Customer Management',
                description='Customer management functionality',
                component_type='module',
                required_features=['FEATURE_CUSTOMER_MANAGEMENT'],
                files=['js/customer-management.js', 'css/customer-management.css'],
                init_function='initCustomerManagement',
                priority=15,
                dependencies=['pos_core']
            ),
            AdaptiveComponent(
                'inventory_management',
                name='Inventory Management',
                description='Inventory management functionality',
                component_type='module',
                required_features=['FEATURE_INVENTORY_BASIC'],
                files=['js/inventory-management.js', 'css/inventory-management.css'],
                init_function='initInventoryManagement',
                priority=25,
                dependencies=['pos_core', 'product_catalog']
            )
        ]
        
        # Restaurant-specific Components
        restaurant_components = [
            AdaptiveComponent(
                'table_management',
                name='Table Management',
                description='Restaurant table management',
                component_type='module',
                required_features=['FEATURE_TABLE_MANAGEMENT'],
                retail_types=['restaurant'],
                files=['js/table-management.js', 'css/table-management.css'],
                init_function='initTableManagement',
                priority=30,
                dependencies=['pos_core']
            ),
            AdaptiveComponent(
                'kitchen_display',
                name='Kitchen Display',
                description='Kitchen order display',
                component_type='module',
                required_features=['FEATURE_KITCHEN_DISPLAY'],
                retail_types=['restaurant'],
                files=['js/kitchen-display.js', 'css/kitchen-display.css'],
                init_function='initKitchenDisplay',
                priority=35,
                dependencies=['pos_core', 'table_management']
            ),
            AdaptiveComponent(
                'reservation_system',
                name='Reservation System',
                description='Restaurant reservation management',
                component_type='module',
                required_features=['FEATURE_RESERVATIONS'],
                retail_types=['restaurant'],
                files=['js/reservation-system.js', 'css/reservation-system.css'],
                init_function='initReservationSystem',
                priority=40,
                dependencies=['pos_core', 'table_management', 'customer_management']
            )
        ]
        
        # Retail-specific Components
        retail_components = [
            AdaptiveComponent(
                'quick_sale',
                name='Quick Sale',
                description='Quick sale functionality',
                component_type='module',
                required_features=['FEATURE_QUICK_SALE'],
                retail_types=['retail'],
                files=['js/quick-sale.js', 'css/quick-sale.css'],
                init_function='initQuickSale',
                priority=30,
                dependencies=['pos_core', 'product_catalog']
            )
        ]
        
        # Apparel-specific Components
        apparel_components = [
            AdaptiveComponent(
                'variant_management',
                name='Variant Management',
                description='Product variant management',
                component_type='module',
                required_features=['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS'],
                retail_types=['apparel'],
                files=['js/variant-management.js', 'css/variant-management.css'],
                init_function='initVariantManagement',
                priority=30,
                dependencies=['pos_core', 'product_catalog']
            ),
            AdaptiveComponent(
                'exchange_management',
                name='Exchange Management',
                description='Product exchange management',
                component_type='module',
                required_features=['FEATURE_EXCHANGE_MANAGEMENT'],
                retail_types=['apparel'],
                files=['js/exchange-management.js', 'css/exchange-management.css'],
                init_function='initExchangeManagement',
                priority=35,
                dependencies=['pos_core', 'product_catalog', 'customer_management']
            ),
            AdaptiveComponent(
                'alteration_tracking',
                name='Alteration Tracking',
                description='Clothing alteration tracking',
                component_type='module',
                required_features=['FEATURE_ALTERATION_TRACKING'],
                retail_types=['apparel'],
                files=['js/alteration-tracking.js', 'css/alteration-tracking.css'],
                init_function='initAlterationTracking',
                priority=40,
                dependencies=['pos_core', 'customer_management']
            )
        ]
        
        # Grocery-specific Components
        grocery_components = [
            AdaptiveComponent(
                'weighing_scale',
                name='Weighing Scale',
                description='Weighing scale integration',
                component_type='module',
                required_features=['FEATURE_WEIGHING_SCALE'],
                retail_types=['grocery'],
                files=['js/weighing-scale.js'],
                init_function='initWeighingScale',
                priority=30,
                dependencies=['pos_core']
            ),
            AdaptiveComponent(
                'expiry_tracking',
                name='Expiry Tracking',
                description='Product expiry tracking',
                component_type='module',
                required_features=['FEATURE_EXPIRY_TRACKING'],
                retail_types=['grocery'],
                files=['js/expiry-tracking.js', 'css/expiry-tracking.css'],
                init_function='initExpiryTracking',
                priority=35,
                dependencies=['pos_core', 'inventory_management']
            ),
            AdaptiveComponent(
                'batch_tracking',
                name='Batch Tracking',
                description='Product batch tracking',
                component_type='module',
                required_features=['FEATURE_BATCH_TRACKING'],
                retail_types=['grocery'],
                files=['js/batch-tracking.js', 'css/batch-tracking.css'],
                init_function='initBatchTracking',
                priority=40,
                dependencies=['pos_core', 'inventory_management']
            )
        ]
        
        # Register all components
        for component in core_components + restaurant_components + retail_components + apparel_components + grocery_components:
            self.component_registry.register_component(component)
    
    def _load_validation_rules(self):
        """Load client-side validation rules"""
        validation_rules = {
            'required': {
                'rule': 'value !== "" && value !== null && value !== undefined',
                'message': 'This field is required'
            },
            'email': {
                'rule': '/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value)',
                'message': 'Please enter a valid email address'
            },
            'phone': {
                'rule': '/^[+]?[\\d\\s\\-\\(\\)]+$/.test(value) && value.replace(/\\D/g, "").length >= 10',
                'message': 'Please enter a valid phone number'
            },
            'min_length': {
                'rule': 'value.length >= params.min',
                'message': 'Minimum length is {min} characters'
            },
            'max_length': {
                'rule': 'value.length <= params.max',
                'message': 'Maximum length is {max} characters'
            },
            'numeric': {
                'rule': '!isNaN(value) && value.trim() !== ""',
                'message': 'Please enter a valid number'
            },
            'positive': {
                'rule': 'parseFloat(value) > 0',
                'message': 'Value must be positive'
            },
            'date': {
                'rule': '!isNaN(Date.parse(value))',
                'message': 'Please enter a valid date'
            },
            'future_date': {
                'rule': 'Date.parse(value) > new Date()',
                'message': 'Date must be in the future'
            },
            'past_date': {
                'rule': 'Date.parse(value) < new Date()',
                'message': 'Date must be in the past'
            }
        }
        
        for rule_name, rule_config in validation_rules.items():
            self.validation.register_validation_rule(rule_name, rule_config)
    
    def _load_workflows(self):
        """Load default workflows"""
        # Restaurant workflows
        self.workflow_manager.register_workflow(
            'restaurant_order',
            {
                'name': 'Restaurant Order',
                'description': 'Complete restaurant order workflow',
                'retail_types': ['restaurant'],
                'required_features': ['FEATURE_SALES_PROCESSING'],
                'config': {
                    'allow_table_selection': True,
                    'allow_kot_printing': True,
                    'allow_waiter_assignment': True
                }
            }
        )
        
        self.workflow_manager.register_workflow_step(
            'restaurant_order',
            'select_table',
            {
                'name': 'Select Table',
                'description': 'Select or create table for order',
                'required_features': ['FEATURE_TABLE_MANAGEMENT'],
                'component': 'table_management',
                'config': {
                    'show_available_only': True,
                    'allow_table_creation': True
                }
            }
        )
        
        self.workflow_manager.register_workflow_step(
            'restaurant_order',
            'take_order',
            {
                'name': 'Take Order',
                'description': 'Add items to order',
                'component': 'pos_core',
                'config': {
                    'show_menu_categories': True,
                    'allow_modifications': True
                }
            }
        )
        
        self.workflow_manager.register_workflow_step(
            'restaurant_order',
            'send_to_kitchen',
            {
                'name': 'Send to Kitchen',
                'description': 'Send order to kitchen display',
                'required_features': ['FEATURE_KITCHEN_DISPLAY'],
                'component': 'kitchen_display',
                'config': {
                    'auto_send': True,
                    'print_kot': True
                }
            }
        )
        
        # Retail workflows
        self.workflow_manager.register_workflow(
            'retail_sale',
            {
                'name': 'Retail Sale',
                'description': 'Complete retail sale workflow',
                'retail_types': ['retail'],
                'required_features': ['FEATURE_SALES_PROCESSING'],
                'config': {
                    'allow_barcode_scanning': True,
                    'allow_customer_search': True
                }
            }
        )
        
        self.workflow_manager.register_workflow_step(
            'retail_sale',
            'scan_products',
            {
                'name': 'Scan Products',
                'description': 'Add products via barcode or search',
                'component': 'barcode_scanner',
                'config': {
                    'auto_focus_scanner': True,
                    'show_product_search': True
                }
            }
        )
        
        self.workflow_manager.register_workflow_step(
            'retail_sale',
            'customer_info',
            {
                'name': 'Customer Information',
                'description': 'Add customer details',
                'required_features': ['FEATURE_CUSTOMER_MANAGEMENT'],
                'component': 'customer_management',
                'config': {
                    'optional_for_guest': True,
                    'show_loyalty_info': True
                }
            }
        )
    
    def _load_asset_bundles(self):
        """Load asset bundles for optimization"""
        self.asset_bundles = {
            'core': {
                'js': ['js/pos-core.js', 'js/utils.js'],
                'css': ['css/pos-core.css', 'css/common.css'],
                'components': ['pos_core']
            },
            'restaurant': {
                'js': ['js/table-management.js', 'js/kitchen-display.js'],
                'css': ['css/table-management.css', 'css/kitchen-display.css'],
                'components': ['table_management', 'kitchen_display']
            },
            'retail': {
                'js': ['js/barcode-scanner.js', 'js/quick-sale.js'],
                'css': ['css/barcode-scanner.css', 'css/quick-sale.css'],
                'components': ['barcode_scanner', 'quick_sale']
            },
            'apparel': {
                'js': ['js/variant-management.js', 'js/exchange-management.js'],
                'css': ['css/variant-management.css', 'css/exchange-management.css'],
                'components': ['variant_management', 'exchange_management']
            },
            'grocery': {
                'js': ['js/weighing-scale.js', 'js/expiry-tracking.js'],
                'css': ['css/weighing-scale.css', 'css/expiry-tracking.css'],
                'components': ['weighing_scale', 'expiry_tracking']
            }
        }
    
    def get_components_for_tenant(self, tenant_id: Optional[str] = None, 
                                user_role: Optional[str] = None) -> Dict[str, Any]:
        """Get components for a specific tenant"""
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get matching components
        components = self.component_registry.get_components_for_context(
            enabled_features, retail_type, user_role
        )
        
        # Get components in load order
        ordered_components = self.component_registry.get_load_order(components)
        
        # Separate into immediate and lazy-loaded components
        immediate_components = [c for c in ordered_components if not c.lazy_load]
        lazy_components = [c for c in ordered_components if c.lazy_load]
        
        return {
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'immediate_components': [c.to_dict() for c in immediate_components],
            'lazy_components': [c.to_dict() for c in lazy_components],
            'asset_bundles': self._get_asset_bundles(retail_type, enabled_features),
            'validation_config': self.validation.validation_rules
        }
    
    def get_workflow_for_tenant(self, workflow_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get workflow for a specific tenant"""
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        return self.workflow_manager.get_workflow(workflow_id, retail_type, enabled_features)
    
    def _get_asset_bundles(self, retail_type: str, enabled_features: Set[str]) -> List[str]:
        """Get asset bundles for the current context"""
        bundles = ['core']  # Always include core bundle
        
        # Add retail-type specific bundles
        if retail_type in self.asset_bundles:
            bundles.append(retail_type)
        
        # Add feature-specific bundles
        if 'FEATURE_TABLE_MANAGEMENT' in enabled_features:
            bundles.append('table_management')
        if 'FEATURE_BARCODE_SCANNING' in enabled_features:
            bundles.append('barcode_scanning')
        if 'FEATURE_INVENTORY_BASIC' in enabled_features:
            bundles.append('inventory')
        
        return bundles
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def register_component(self, component: AdaptiveComponent):
        """Register a new component"""
        self.component_registry.register_component(component)
    
    def register_workflow(self, workflow_id: str, workflow_config: Dict[str, Any]):
        """Register a new workflow"""
        self.workflow_manager.register_workflow(workflow_id, workflow_config)
    
    def register_validation_rule(self, rule_name: str, rule_config: Dict[str, Any]):
        """Register a validation rule"""
        self.validation.register_validation_rule(rule_name, rule_config)


# Global component manager instance
component_manager = None


def get_component_manager(feature_manager=None) -> AdaptiveComponentManager:
    """Get or create global component manager instance"""
    global component_manager
    if component_manager is None:
        component_manager = AdaptiveComponentManager(feature_manager)
    return component_manager