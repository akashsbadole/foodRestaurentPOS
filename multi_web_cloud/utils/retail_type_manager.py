"""
Manage retail-type specific configurations and workflows
"""

from typing import Dict, List, Optional, Any, Set
from flask import current_app
from models import db, RetailTypePreset, TenantFeatureFlag
from utils.feature_flag_manager import feature_manager


class RetailTypeManager:
    """
    Manage retail-type specific configurations and workflows
    """
    
    def __init__(self, feature_manager):
        self.feature_manager = feature_manager
        self.retail_types = {}
        self.workflows = {}
        self.payment_methods = {}
        self.tax_types = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize retail type manager"""
        if self._initialized:
            return
        
        self.load_retail_type_definitions()
        self.load_presets_from_database()
        self._initialized = True
    
    def load_retail_type_definitions(self):
        """Load retail type definitions and configurations"""
        self.retail_types = {
            'restaurant': {
                'name': 'Restaurant',
                'description': 'Food service establishment',
                'features': [
                    'FEATURE_TABLE_MANAGEMENT',
                    'FEATURE_KOT_PRINTING',
                    'FEATURE_KITCHEN_DISPLAY',
                    'FEATURE_WAITER_MANAGEMENT',
                    'FEATURE_RESERVATIONS',
                    'FEATURE_SALES_PROCESSING',
                    'FEATURE_PRODUCT_CATALOG'
                ],
                'workflows': ['dine_in', 'takeaway', 'delivery'],
                'payment_methods': ['cash', 'card', 'upi', 'wallet'],
                'tax_types': ['gst', 'service_charge'],
                'default_features': {
                    'FEATURE_SALES_PROCESSING': True,
                    'FEATURE_PRODUCT_CATALOG': True,
                    'FEATURE_TABLE_MANAGEMENT': True,
                    'FEATURE_KOT_PRINTING': True
                }
            },
            'retail': {
                'name': 'General Retail',
                'description': 'General retail store',
                'features': [
                    'FEATURE_PRODUCT_CATALOG',
                    'FEATURE_BARCODE_SCANNING',
                    'FEATURE_INVENTORY_BASIC',
                    'FEATURE_CUSTOMER_MANAGEMENT',
                    'FEATURE_SALES_PROCESSING',
                    'FEATURE_QUICK_SALE'
                ],
                'workflows': ['counter_sale', 'delivery', 'online_order'],
                'payment_methods': ['cash', 'card', 'upi', 'wallet'],
                'tax_types': ['gst', 'vat'],
                'default_features': {
                    'FEATURE_SALES_PROCESSING': True,
                    'FEATURE_PRODUCT_CATALOG': True,
                    'FEATURE_BARCODE_SCANNING': True,
                    'FEATURE_INVENTORY_BASIC': True
                }
            },
            'apparel': {
                'name': 'Apparel & Footwear',
                'description': 'Clothing and footwear store',
                'features': [
                    'FEATURE_SIZE_VARIANTS',
                    'FEATURE_COLOR_VARIANTS',
                    'FEATURE_STYLE_VARIANTS',
                    'FEATURE_EXCHANGE_MANAGEMENT',
                    'FEATURE_ALTERATION_TRACKING',
                    'FEATURE_BARCODE_SCANNING',
                    'FEATURE_CUSTOMER_MANAGEMENT',
                    'FEATURE_SALES_PROCESSING'
                ],
                'workflows': ['sale', 'exchange', 'alteration', 'return'],
                'payment_methods': ['cash', 'card', 'upi', 'emi'],
                'tax_types': ['gst', 'vat'],
                'default_features': {
                    'FEATURE_SALES_PROCESSING': True,
                    'FEATURE_PRODUCT_CATALOG': True,
                    'FEATURE_SIZE_VARIANTS': True,
                    'FEATURE_COLOR_VARIANTS': True,
                    'FEATURE_EXCHANGE_MANAGEMENT': True
                }
            },
            'grocery': {
                'name': 'Grocery & Supermarket',
                'description': 'Grocery store or supermarket',
                'features': [
                    'FEATURE_WEIGHING_SCALE',
                    'FEATURE_EXPIRY_TRACKING',
                    'FEATURE_BATCH_TRACKING',
                    'FEATURE_PRICE_BY_WEIGHT',
                    'FEATURE_COMBO_OFFERS',
                    'FEATURE_BARCODE_SCANNING',
                    'FEATURE_INVENTORY_BASIC',
                    'FEATURE_SALES_PROCESSING'
                ],
                'workflows': ['counter_sale', 'bulk_sale', 'home_delivery'],
                'payment_methods': ['cash', 'card', 'upi', 'wallet'],
                'tax_types': ['gst', 'vat'],
                'default_features': {
                    'FEATURE_SALES_PROCESSING': True,
                    'FEATURE_PRODUCT_CATALOG': True,
                    'FEATURE_BARCODE_SCANNING': True,
                    'FEATURE_WEIGHING_SCALE': True,
                    'FEATURE_EXPIRY_TRACKING': True
                }
            }
        }
        
        # Initialize workflows
        self.workflows = {
            'dine_in': {
                'name': 'Dine In',
                'description': 'Customers dine at the restaurant',
                'retail_types': ['restaurant'],
                'steps': ['seating', 'ordering', 'kitchen', 'serving', 'payment', 'billing']
            },
            'takeaway': {
                'name': 'Takeaway',
                'description': 'Customers order for takeout',
                'retail_types': ['restaurant'],
                'steps': ['ordering', 'kitchen', 'packaging', 'payment', 'pickup']
            },
            'delivery': {
                'name': 'Delivery',
                'description': 'Orders delivered to customers',
                'retail_types': ['restaurant', 'retail', 'grocery'],
                'steps': ['ordering', 'preparation', 'packaging', 'dispatch', 'delivery', 'payment']
            },
            'counter_sale': {
                'name': 'Counter Sale',
                'description': 'Direct sales at counter',
                'retail_types': ['retail', 'apparel', 'grocery'],
                'steps': ['selection', 'billing', 'payment', 'packaging']
            },
            'online_order': {
                'name': 'Online Order',
                'description': 'Orders placed online',
                'retail_types': ['retail', 'grocery'],
                'steps': ['online_ordering', 'processing', 'packaging', 'delivery', 'payment']
            },
            'sale': {
                'name': 'Sale',
                'description': 'Regular product sale',
                'retail_types': ['apparel'],
                'steps': ['selection', 'trial', 'billing', 'payment', 'packaging']
            },
            'exchange': {
                'name': 'Exchange',
                'description': 'Product exchange process',
                'retail_types': ['apparel'],
                'steps': ['return_request', 'verification', 'selection', 'exchange', 'payment']
            },
            'alteration': {
                'name': 'Alteration',
                'description': 'Clothing alteration service',
                'retail_types': ['apparel'],
                'steps': ['measurement', 'alteration', 'fitting', 'delivery', 'payment']
            },
            'return': {
                'name': 'Return',
                'description': 'Product return process',
                'retail_types': ['apparel'],
                'steps': ['return_request', 'verification', 'refund', 'restocking']
            },
            'bulk_sale': {
                'name': 'Bulk Sale',
                'description': 'Bulk quantity sales',
                'retail_types': ['grocery'],
                'steps': ['bulk_ordering', 'pricing', 'payment', 'delivery']
            },
            'home_delivery': {
                'name': 'Home Delivery',
                'description': 'Scheduled home deliveries',
                'retail_types': ['grocery'],
                'steps': ['scheduling', 'ordering', 'processing', 'delivery', 'payment']
            }
        }
        
        # Initialize payment methods
        self.payment_methods = {
            'cash': {
                'name': 'Cash',
                'description': 'Cash payment',
                'retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'card': {
                'name': 'Card',
                'description': 'Credit/Debit card payment',
                'retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'upi': {
                'name': 'UPI',
                'description': 'Unified Payments Interface',
                'retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'wallet': {
                'name': 'Wallet',
                'description': 'Digital wallet payment',
                'retail_types': ['restaurant', 'retail', 'grocery']
            },
            'emi': {
                'name': 'EMI',
                'description': 'Equated Monthly Installments',
                'retail_types': ['apparel']
            }
        }
        
        # Initialize tax types
        self.tax_types = {
            'gst': {
                'name': 'GST',
                'description': 'Goods and Services Tax',
                'retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'vat': {
                'name': 'VAT',
                'description': 'Value Added Tax',
                'retail_types': ['retail', 'apparel', 'grocery']
            },
            'service_charge': {
                'name': 'Service Charge',
                'description': 'Service charge for restaurants',
                'retail_types': ['restaurant']
            }
        }
    
    def get_retail_type_config(self, retail_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific retail type"""
        if not self._initialized:
            self.initialize()
        
        return self.retail_types.get(retail_type)
    
    def validate_retail_type_features(self, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Validate features for retail type"""
        if not self._initialized:
            self.initialize()
        
        validation_result = {
            'valid': True,
            'missing_required': [],
            'incompatible_features': [],
            'warnings': []
        }
        
        retail_config = self.get_retail_type_config(retail_type)
        if not retail_config:
            validation_result['valid'] = False
            validation_result['warnings'].append(f"Unknown retail type: {retail_type}")
            return validation_result
        
        # Check required features
        required_features = set(retail_config.get('features', []))
        missing_features = required_features - enabled_features
        
        if missing_features:
            validation_result['valid'] = False
            validation_result['missing_required'] = list(missing_features)
        
        # Check for incompatible features (features not supported by this retail type)
        all_supported_features = set()
        for rt_config in self.retail_types.values():
            all_supported_features.update(rt_config.get('features', []))
        
        incompatible_features = enabled_features - all_supported_features
        if incompatible_features:
            validation_result['warnings'].extend([
                f"Feature {feature} may not be compatible with any retail type"
                for feature in incompatible_features
            ])
        
        return validation_result
    
    def get_retail_type_workflows(self, retail_type: str) -> List[Dict[str, Any]]:
        """Get available workflows for retail type"""
        if not self._initialized:
            self.initialize()
        
        retail_config = self.get_retail_type_config(retail_type)
        if not retail_config:
            return []
        
        workflow_names = retail_config.get('workflows', [])
        workflows = []
        
        for workflow_name in workflow_names:
            workflow = self.workflows.get(workflow_name)
            if workflow:
                workflows.append(workflow)
        
        return workflows
    
    def get_retail_type_payment_methods(self, retail_type: str) -> List[Dict[str, Any]]:
        """Get available payment methods for retail type"""
        if not self._initialized:
            self.initialize()
        
        retail_config = self.get_retail_type_config(retail_type)
        if not retail_config:
            return []
        
        payment_method_names = retail_config.get('payment_methods', [])
        payment_methods = []
        
        for method_name in payment_method_names:
            method = self.payment_methods.get(method_name)
            if method:
                payment_methods.append(method)
        
        return payment_methods
    
    def get_retail_type_tax_types(self, retail_type: str) -> List[Dict[str, Any]]:
        """Get available tax types for retail type"""
        if not self._initialized:
            self.initialize()
        
        retail_config = self.get_retail_type_config(retail_type)
        if not retail_config:
            return []
        
        tax_type_names = retail_config.get('tax_types', [])
        tax_types = []
        
        for tax_name in tax_type_names:
            tax_type = self.tax_types.get(tax_name)
            if tax_type:
                tax_types.append(tax_type)
        
        return tax_types
    
    def get_default_features_for_retail_type(self, retail_type: str) -> Dict[str, bool]:
        """Get default features for a retail type"""
        if not self._initialized:
            self.initialize()
        
        retail_config = self.get_retail_type_config(retail_type)
        if not retail_config:
            return {}
        
        return retail_config.get('default_features', {})
    
    def apply_retail_type_preset(self, tenant_id: str, retail_type: str) -> Dict[str, Any]:
        """Apply retail type preset to tenant"""
        try:
            # Get preset from database or use default
            preset = RetailTypePreset.query.filter_by(retail_type=retail_type, is_active=True).first()
            
            if not preset:
                # Use default preset
                default_features = self.get_default_features_for_retail_type(retail_type)
                if not default_features:
                    return {'success': False, 'error': f'Unknown retail type: {retail_type}'}
                
                # Create preset from defaults
                preset_name = f"{retail_type.title()} Default"
                preset = RetailTypePreset(
                    retail_type=retail_type,
                    name=preset_name,
                    description=f"Default preset for {retail_type} retail type",
                    feature_flags=default_features
                )
            
            # Apply features to tenant
            applied_features = []
            failed_features = []
            
            for feature_name, is_enabled in preset.feature_flags.items():
                try:
                    if is_enabled:
                        success = self.feature_manager.enable_feature(
                            feature_name, tenant_id, 
                            preset.feature_flags.get(feature_name, {})
                        )
                    else:
                        success = self.feature_manager.disable_feature(feature_name, tenant_id)
                    
                    if success:
                        applied_features.append(feature_name)
                    else:
                        failed_features.append(feature_name)
                        
                except Exception as e:
                    current_app.logger.error(f"Error applying feature {feature_name}: {e}")
                    failed_features.append(feature_name)
            
            return {
                'success': len(failed_features) == 0,
                'applied_features': applied_features,
                'failed_features': failed_features,
                'preset_name': preset.name
            }
            
        except Exception as e:
            current_app.logger.error(f"Error applying retail type preset for tenant {tenant_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def load_presets_from_database(self):
        """Load retail type presets from database"""
        try:
            presets = RetailTypePreset.query.filter_by(is_active=True).all()
            
            for preset in presets:
                # Update retail type configuration with preset data
                if preset.retail_type in self.retail_types:
                    self.retail_types[preset.retail_type]['preset_features'] = preset.feature_flags
                    self.retail_types[preset.retail_type]['preset_name'] = preset.name
                    self.retail_types[preset.retail_type]['preset_description'] = preset.description
                    
        except Exception as e:
            current_app.logger.error(f"Error loading presets from database: {e}")
    
    def create_retail_type_preset(self, retail_type: str, name: str, 
                                feature_flags: Dict[str, bool], 
                                description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new retail type preset"""
        try:
            # Validate retail type
            if retail_type not in self.retail_types:
                return {'success': False, 'error': f'Unknown retail type: {retail_type}'}
            
            # Validate features
            validation_result = self.validate_retail_type_features(
                retail_type, set(feature_flags.keys())
            )
            if not validation_result['valid']:
                return {
                    'success': False, 
                    'error': 'Invalid feature combination',
                    'validation_errors': validation_result
                }
            
            # Create preset
            preset = RetailTypePreset(
                retail_type=retail_type,
                name=name,
                description=description,
                feature_flags=feature_flags
            )
            
            db.session.add(preset)
            db.session.commit()
            
            # Reload presets
            self.load_presets_from_database()
            
            return {
                'success': True,
                'preset_id': preset.id,
                'message': f'Preset {name} created successfully'
            }
            
        except Exception as e:
            current_app.logger.error(f"Error creating retail type preset: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_retail_type_statistics(self) -> Dict[str, Any]:
        """Get statistics for retail types"""
        if not self._initialized:
            self.initialize()
        
        stats = {
            'total_retail_types': len(self.retail_types),
            'retail_types': {},
            'workflows': len(self.workflows),
            'payment_methods': len(self.payment_methods),
            'tax_types': len(self.tax_types)
        }
        
        for retail_type, config in self.retail_types.items():
            stats['retail_types'][retail_type] = {
                'name': config['name'],
                'feature_count': len(config['features']),
                'workflow_count': len(config['workflows']),
                'payment_method_count': len(config['payment_methods']),
                'tax_type_count': len(config['tax_types'])
            }
        
        return stats
    
    def get_workflow_details(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a workflow"""
        if not self._initialized:
            self.initialize()
        
        return self.workflows.get(workflow_name)
    
    def get_payment_method_details(self, method_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a payment method"""
        if not self._initialized:
            self.initialize()
        
        return self.payment_methods.get(method_name)
    
    def get_tax_type_details(self, tax_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tax type"""
        if not self._initialized:
            self.initialize()
        
        return self.tax_types.get(tax_name)


# Global retail type manager instance
retail_type_manager = None


def get_retail_type_manager(feature_manager) -> RetailTypeManager:
    """Get or create global retail type manager instance"""
    global retail_type_manager
    if retail_type_manager is None:
        retail_type_manager = RetailTypeManager(feature_manager)
    return retail_type_manager