"""
Initialize feature management system for existing installations
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, FeatureDefinition, FeatureDependency, FeatureConflict, RetailTypePreset, TenantFeatureFlag
from utils.environment_flag_parser import EnvironmentFlagParser
from utils.retail_type_manager import RetailTypeManager
from utils.feature_flag_manager import feature_manager


def init_feature_definitions():
    """Initialize feature definitions from parser"""
    print("Initializing feature definitions...")
    
    try:
        parser = EnvironmentFlagParser()
        feature_definitions = parser._load_feature_definitions()
        
        # Create feature definitions in database
        created_count = 0
        for feature_name, definition in feature_definitions.items():
            existing = FeatureDefinition.query.filter_by(name=feature_name).first()
            if not existing:
                feature_def = FeatureDefinition(
                    name=feature_name,
                    display_name=definition.get('display_name', feature_name),
                    description=definition.get('description', ''),
                    category=definition.get('category', 'core'),
                    feature_type=definition.get('type', 'boolean'),
                    default_value=definition.get('default', False),
                    is_required=definition.get('is_required', False),
                    is_experimental=definition.get('is_experimental', False),
                    supported_retail_types=definition.get('supported_retail_types'),
                    required_retail_types=definition.get('required_retail_types')
                )
                db.session.add(feature_def)
                created_count += 1
        
        db.session.commit()
        print(f"Created {created_count} feature definitions")
        
    except Exception as e:
        print(f"Error initializing feature definitions: {e}")
        db.session.rollback()


def init_retail_type_presets():
    """Initialize retail type presets"""
    print("Initializing retail type presets...")
    
    try:
        retail_manager = RetailTypeManager(feature_manager)
        retail_manager.load_retail_type_definitions()
        
        # Create default retail type presets
        created_count = 0
        for retail_type, config in retail_manager.retail_types.items():
            existing = RetailTypePreset.query.filter_by(retail_type=retail_type).first()
            if not existing:
                preset = RetailTypePreset(
                    retail_type=retail_type,
                    name=f"{config['name']} Default",
                    description=f"Default preset for {config['name']}",
                    feature_flags=config.get('default_features', {})
                )
                db.session.add(preset)
                created_count += 1
        
        db.session.commit()
        print(f"Created {created_count} retail type presets")
        
    except Exception as e:
        print(f"Error initializing retail type presets: {e}")
        db.session.rollback()


def init_feature_dependencies():
    """Initialize feature dependencies"""
    print("Initializing feature dependencies...")
    
    try:
        # Define common dependencies
        dependencies = [
            # Core dependencies
            ('FEATURE_SALES_PROCESSING', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_LOYALTY_PROGRAM', 'FEATURE_CUSTOMER_MANAGEMENT', 'required'),
            ('FEATURE_TABLE_MANAGEMENT', 'FEATURE_SALES_PROCESSING', 'required'),
            ('FEATURE_KOT_PRINTING', 'FEATURE_SALES_PROCESSING', 'required'),
            ('FEATURE_KITCHEN_DISPLAY', 'FEATURE_SALES_PROCESSING', 'required'),
            
            # Retail-specific dependencies
            ('FEATURE_SIZE_VARIANTS', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_COLOR_VARIANTS', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_STYLE_VARIANTS', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_EXCHANGE_MANAGEMENT', 'FEATURE_CUSTOMER_MANAGEMENT', 'required'),
            ('FEATURE_ALTERATION_TRACKING', 'FEATURE_CUSTOMER_MANAGEMENT', 'required'),
            
            ('FEATURE_WEIGHING_SCALE', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_EXPIRY_TRACKING', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_BATCH_TRACKING', 'FEATURE_PRODUCT_CATALOG', 'required'),
            ('FEATURE_PRICE_BY_WEIGHT', 'FEATURE_WEIGHING_SCALE', 'required'),
            
            # Conflicts
            ('FEATURE_TABLE_MANAGEMENT', 'FEATURE_QUICK_SALE', 'conflicts'),
            ('FEATURE_QUICK_SALE', 'FEATURE_TABLE_MANAGEMENT', 'conflicts'),
        ]
        
        created_count = 0
        for feature, depends_on, dep_type in dependencies:
            existing = FeatureDependency.query.filter_by(
                feature_name=feature, 
                depends_on_feature=depends_on
            ).first()
            
            if not existing:
                dependency = FeatureDependency(
                    feature_name=feature,
                    depends_on_feature=depends_on,
                    dependency_type=dep_type,
                    description=f"Auto-generated dependency: {feature} -> {depends_on}"
                )
                db.session.add(dependency)
                created_count += 1
        
        db.session.commit()
        print(f"Created {created_count} feature dependencies")
        
    except Exception as e:
        print(f"Error initializing feature dependencies: {e}")
        db.session.rollback()


def migrate_existing_tenant_flags():
    """Migrate existing tenant settings to new feature flag system"""
    print("Migrating existing tenant settings...")
    
    try:
        from models.tenant import Tenant, TenantSettings
        
        tenants = Tenant.query.all()
        migrated_count = 0
        
        for tenant in tenants:
            # Get tenant settings
            settings = TenantSettings.query.filter_by(tenant_id=tenant.id).first()
            if not settings:
                continue
            
            # Map existing settings to feature flags
            feature_mappings = {
                'restaurant': {
                    'FEATURE_TABLE_MANAGEMENT': True,
                    'FEATURE_KOT_PRINTING': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                    'FEATURE_KITCHEN_DISPLAY': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                    'FEATURE_WAITER_MANAGEMENT': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                    'FEATURE_RESERVATIONS': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                },
                'retail': {
                    'FEATURE_BARCODE_SCANNING': True,
                    'FEATURE_QUICK_SALE': True,
                    'FEATURE_CUSTOMER_MANAGEMENT': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                },
                'apparel': {
                    'FEATURE_SIZE_VARIANTS': True,
                    'FEATURE_COLOR_VARIANTS': True,
                    'FEATURE_EXCHANGE_MANAGEMENT': True,
                    'FEATURE_CUSTOMER_MANAGEMENT': settings.enable_crm if hasattr(settings, 'enable_crm') else True,
                },
                'grocery': {
                    'FEATURE_WEIGHING_SCALE': True,
                    'FEATURE_EXPIRY_TRACKING': True,
                    'FEATURE_BATCH_TRACKING': True,
                    'FEATURE_PRICE_BY_WEIGHT': True,
                    'FEATURE_BARCODE_SCANNING': True,
                }
            }
            
            # Determine retail type (default to restaurant)
            retail_type = 'restaurant'  # Could be enhanced to detect from settings
            features_to_enable = feature_mappings.get(retail_type, {})
            
            # Create feature flags for tenant
            for feature_name, is_enabled in features_to_enable.items():
                existing_flag = TenantFeatureFlag.query.filter_by(
                    tenant_id=tenant.id,
                    feature_name=feature_name
                ).first()
                
                if not existing_flag:
                    flag = TenantFeatureFlag(
                        tenant_id=tenant.id,
                        feature_name=feature_name,
                        is_enabled=is_enabled,
                        retail_type=retail_type
                    )
                    db.session.add(flag)
                    migrated_count += 1
            
            migrated_count += 1
        
        db.session.commit()
        print(f"Migrated {migrated_count} tenants to new feature flag system")
        
    except Exception as e:
        print(f"Error migrating tenant settings: {e}")
        db.session.rollback()


def main():
    """Main migration function"""
    print("Starting feature management system initialization...")
    print(f"Timestamp: {datetime.utcnow()}")
    
    # Initialize all components
    init_feature_definitions()
    init_retail_type_presets()
    init_feature_dependencies()
    migrate_existing_tenant_flags()
    
    print("Feature management system initialization completed!")


if __name__ == '__main__':
    main()