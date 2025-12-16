"""
Parse and validate 100+ feature flags from .env file
"""

import os
import re
from typing import Dict, List, Any, Optional
from flask import current_app


class EnvironmentFlagParser:
    """
    Parse and validate 100+ feature flags from .env file
    """
    
    def __init__(self, env_file_path='.env'):
        self.env_file_path = env_file_path
        self.feature_definitions = self._load_feature_definitions()
        self.parsed_flags = {}
    
    def parse_environment_flags(self) -> Dict[str, bool]:
        """Parse all FEATURE_* variables from environment"""
        parsed_flags = {}
        
        # First, try to load from .env file
        if os.path.exists(self.env_file_path):
            parsed_flags.update(self._parse_env_file())
        
        # Then override with actual environment variables
        parsed_flags.update(self._parse_os_environment())
        
        # Validate and normalize flags
        validated_flags = self.validate_flag_values(parsed_flags)
        
        self.parsed_flags = validated_flags.valid_flags
        return self.parsed_flags
    
    def validate_flag_values(self, flags: Dict[str, Any]) -> 'ValidationResult':
        """Validate flag values against definitions"""
        valid_flags = {}
        errors = []
        warnings = []
        
        for flag_name, flag_value in flags.items():
            # Check if flag is a feature flag
            if not flag_name.startswith('FEATURE_'):
                continue
            
            # Get feature definition
            feature_def = self.feature_definitions.get(flag_name)
            if not feature_def:
                warnings.append(f"Unknown feature flag: {flag_name}")
                # Still include it with default boolean conversion
                valid_flags[flag_name] = self._convert_to_boolean(flag_value)
                continue
            
            # Validate based on feature type
            try:
                if feature_def['type'] == 'boolean':
                    valid_flags[flag_name] = self._convert_to_boolean(flag_value)
                elif feature_def['type'] == 'string':
                    valid_flags[flag_name] = str(flag_value)
                elif feature_def['type'] == 'numeric':
                    valid_flags[flag_name] = float(flag_value)
                elif feature_def['type'] == 'json':
                    valid_flags[flag_name] = flag_value if isinstance(flag_value, dict) else {}
                
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid value for {flag_name}: {flag_value}. Error: {e}")
                # Use default value
                valid_flags[flag_name] = feature_def.get('default', False)
        
        # Add default values for missing required features
        for flag_name, feature_def in self.feature_definitions.items():
            if feature_def.get('is_required', False) and flag_name not in valid_flags:
                valid_flags[flag_name] = feature_def.get('default', True)
        
        return ValidationResult(valid_flags, errors, warnings)
    
    def detect_flag_conflicts(self, flags: Dict[str, bool]) -> List[str]:
        """Detect conflicting flag combinations"""
        conflicts = []
        
        # Define conflict rules
        conflict_rules = {
            'FEATURE_TABLE_MANAGEMENT': ['FEATURE_QUICK_SALE'],
            'FEATURE_QUICK_SALE': ['FEATURE_TABLE_MANAGEMENT'],
            'FEATURE_ADVANCED_INVENTORY': ['FEATURE_BASIC_INVENTORY'],
            'FEATURE_BASIC_INVENTORY': ['FEATURE_ADVANCED_INVENTORY'],
        }
        
        for flag_name, is_enabled in flags.items():
            if is_enabled and flag_name in conflict_rules:
                conflicting_flags = conflict_rules[flag_name]
                for conflicting_flag in conflicting_flags:
                    if flags.get(conflicting_flag, False):
                        conflicts.append(f"{flag_name} conflicts with {conflicting_flag}")
        
        return conflicts
    
    def _parse_env_file(self) -> Dict[str, str]:
        """Parse .env file and return key-value pairs"""
        env_vars = {}
        
        try:
            with open(self.env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', line)
                    if match:
                        key, value = match.groups()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                        
        except Exception as e:
            current_app.logger.warning(f"Error parsing .env file: {e}")
        
        return env_vars
    
    def _parse_os_environment(self) -> Dict[str, str]:
        """Parse feature flags from OS environment"""
        env_vars = {}
        
        for key, value in os.environ.items():
            if key.startswith('FEATURE_'):
                env_vars[key] = value
        
        return env_vars
    
    def _convert_to_boolean(self, value: Any) -> bool:
        """Convert various value types to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        if isinstance(value, (int, float)):
            return bool(value)
        return bool(value)
    
    def _load_feature_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load feature definitions from configuration"""
        return {
            # Universal Core Features
            'FEATURE_SALES_PROCESSING': {
                'type': 'boolean',
                'default': True,
                'category': 'core',
                'description': 'Enable sales processing functionality',
                'is_required': True
            },
            'FEATURE_PRODUCT_CATALOG': {
                'type': 'boolean',
                'default': True,
                'category': 'core',
                'description': 'Enable product catalog management',
                'is_required': True
            },
            'FEATURE_INVENTORY_BASIC': {
                'type': 'boolean',
                'default': True,
                'category': 'core',
                'description': 'Enable basic inventory management',
                'is_required': False
            },
            'FEATURE_CUSTOMER_MANAGEMENT': {
                'type': 'boolean',
                'default': True,
                'category': 'core',
                'description': 'Enable customer management',
                'is_required': False
            },
            'FEATURE_PAYMENT_PROCESSING': {
                'type': 'boolean',
                'default': True,
                'category': 'core',
                'description': 'Enable payment processing',
                'is_required': True
            },
            
            # Restaurant Features
            'FEATURE_TABLE_MANAGEMENT': {
                'type': 'boolean',
                'default': False,
                'category': 'restaurant',
                'description': 'Enable table management for restaurants',
                'is_required': False,
                'supported_retail_types': ['restaurant']
            },
            'FEATURE_KOT_PRINTING': {
                'type': 'boolean',
                'default': False,
                'category': 'restaurant',
                'description': 'Enable KOT (Kitchen Order Ticket) printing',
                'is_required': False,
                'supported_retail_types': ['restaurant']
            },
            'FEATURE_KITCHEN_DISPLAY': {
                'type': 'boolean',
                'default': False,
                'category': 'restaurant',
                'description': 'Enable kitchen display system',
                'is_required': False,
                'supported_retail_types': ['restaurant']
            },
            'FEATURE_WAITER_MANAGEMENT': {
                'type': 'boolean',
                'default': False,
                'category': 'restaurant',
                'description': 'Enable waiter management',
                'is_required': False,
                'supported_retail_types': ['restaurant']
            },
            'FEATURE_RESERVATIONS': {
                'type': 'boolean',
                'default': False,
                'category': 'restaurant',
                'description': 'Enable table reservations',
                'is_required': False,
                'supported_retail_types': ['restaurant']
            },
            
            # Retail Features
            'FEATURE_BARCODE_SCANNING': {
                'type': 'boolean',
                'default': False,
                'category': 'retail',
                'description': 'Enable barcode scanning',
                'is_required': False,
                'supported_retail_types': ['retail', 'apparel', 'grocery']
            },
            'FEATURE_QUICK_SALE': {
                'type': 'boolean',
                'default': False,
                'category': 'retail',
                'description': 'Enable quick sale mode',
                'is_required': False,
                'supported_retail_types': ['retail', 'grocery']
            },
            'FEATURE_MULTI_STORE': {
                'type': 'boolean',
                'default': False,
                'category': 'retail',
                'description': 'Enable multi-store management',
                'is_required': False,
                'supported_retail_types': ['retail', 'apparel', 'grocery']
            },
            
            # Apparel Features
            'FEATURE_SIZE_VARIANTS': {
                'type': 'boolean',
                'default': False,
                'category': 'apparel',
                'description': 'Enable size variants for products',
                'is_required': False,
                'supported_retail_types': ['apparel']
            },
            'FEATURE_COLOR_VARIANTS': {
                'type': 'boolean',
                'default': False,
                'category': 'apparel',
                'description': 'Enable color variants for products',
                'is_required': False,
                'supported_retail_types': ['apparel']
            },
            'FEATURE_STYLE_VARIANTS': {
                'type': 'boolean',
                'default': False,
                'category': 'apparel',
                'description': 'Enable style variants for products',
                'is_required': False,
                'supported_retail_types': ['apparel']
            },
            'FEATURE_EXCHANGE_MANAGEMENT': {
                'type': 'boolean',
                'default': False,
                'category': 'apparel',
                'description': 'Enable product exchange management',
                'is_required': False,
                'supported_retail_types': ['apparel']
            },
            'FEATURE_ALTERATION_TRACKING': {
                'type': 'boolean',
                'default': False,
                'category': 'apparel',
                'description': 'Enable alteration tracking',
                'is_required': False,
                'supported_retail_types': ['apparel']
            },
            
            # Grocery Features
            'FEATURE_WEIGHING_SCALE': {
                'type': 'boolean',
                'default': False,
                'category': 'grocery',
                'description': 'Enable weighing scale integration',
                'is_required': False,
                'supported_retail_types': ['grocery']
            },
            'FEATURE_EXPIRY_TRACKING': {
                'type': 'boolean',
                'default': False,
                'category': 'grocery',
                'description': 'Enable product expiry tracking',
                'is_required': False,
                'supported_retail_types': ['grocery']
            },
            'FEATURE_BATCH_TRACKING': {
                'type': 'boolean',
                'default': False,
                'category': 'grocery',
                'description': 'Enable batch tracking',
                'is_required': False,
                'supported_retail_types': ['grocery']
            },
            'FEATURE_PRICE_BY_WEIGHT': {
                'type': 'boolean',
                'default': False,
                'category': 'grocery',
                'description': 'Enable pricing by weight',
                'is_required': False,
                'supported_retail_types': ['grocery']
            },
            'FEATURE_COMBO_OFFERS': {
                'type': 'boolean',
                'default': False,
                'category': 'grocery',
                'description': 'Enable combo offers',
                'is_required': False,
                'supported_retail_types': ['grocery']
            },
            
            # Advanced Features
            'FEATURE_LOYALTY_PROGRAM': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable customer loyalty program',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'FEATURE_CRM': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable CRM functionality',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'FEATURE_ONLINE_ORDERS': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable online ordering',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'grocery']
            },
            'FEATURE_DELIVERY_MANAGEMENT': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable delivery management',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'grocery']
            },
            'FEATURE_REPORTS_ADVANCED': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable advanced reporting',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            'FEATURE_API_ACCESS': {
                'type': 'boolean',
                'default': False,
                'category': 'advanced',
                'description': 'Enable API access',
                'is_required': False,
                'supported_retail_types': ['restaurant', 'retail', 'apparel', 'grocery']
            },
            
            # Experimental Features
            'FEATURE_AI_RECOMMENDATIONS': {
                'type': 'boolean',
                'default': False,
                'category': 'experimental',
                'description': 'Enable AI-powered recommendations',
                'is_required': False,
                'is_experimental': True
            },
            'FEATURE_VOICE_ORDERS': {
                'type': 'boolean',
                'default': False,
                'category': 'experimental',
                'description': 'Enable voice ordering',
                'is_required': False,
                'is_experimental': True
            },
        }


class ValidationResult:
    """Result of feature flag validation"""
    
    def __init__(self, valid_flags: Dict[str, Any], errors: List[str], warnings: List[str]):
        self.valid_flags = valid_flags
        self.errors = errors
        self.warnings = warnings
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed without errors"""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'valid': self.is_valid,
            'valid_flags': self.valid_flags,
            'errors': self.errors,
            'warnings': self.warnings
        }