# Comprehensive Configuration Guide - Multi-Retail POS System

## 📋 Table of Contents

1. [Configuration Overview](#configuration-overview)
2. [Feature Flag Configuration](#feature-flag-configuration)
3. [Retail-Type Specific Configuration](#retail-type-specific-configuration)
4. [Multi-Tenant Configuration](#multi-tenant-configuration)
5. [Security Configuration](#security-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Integration Configuration](#integration-configuration)
8. [Environment-Specific Configuration](#environment-specific-configuration)
9. [Configuration Management](#configuration-management)
10. [Validation and Testing](#validation-and-testing)

---

## Configuration Overview

### Configuration Architecture

The multi-retail POS system uses a hierarchical configuration system with multiple layers:

```
┌─────────────────────────────────────────────────────────────┐
│                Configuration Hierarchy                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Environment Variables (.env)                           │
│ 2. Base Configuration (config.py)                          │
│ 3. Environment-Specific Configs                            │
│ 4. Tenant-Specific Settings                                │
│ 5. Feature Flag Overrides                                  │
│ 6. Runtime Configuration                                   │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Priority

1. **Runtime Configuration** (highest priority)
2. **Feature Flag Overrides**
3. **Tenant-Specific Settings**
4. **Environment-Specific Configs**
5. **Base Configuration**
6. **Environment Variables** (lowest priority, but foundational)

### Configuration Files Structure

```
multi_web_cloud/
├── config.py                    # Base configuration
├── .env                         # Environment variables
├── .env.example                # Environment template
├── config/
│   ├── __init__.py
│   ├── development.py          # Development config
│   ├── production.py           # Production config
│   ├── testing.py             # Testing config
│   ├── retail_types.py        # Retail type configs
│   ├── feature_flags.py       # Feature flag defaults
│   └── security.py            # Security configurations
├── models/
│   ├── tenant.py              # Tenant model
│   ├── feature_flag.py        # Feature flag models
│   └── settings.py            # Settings models
└── utils/
    ├── config_manager.py       # Configuration management
    └── feature_manager.py     # Feature flag management
```

---

## Feature Flag Configuration

### Feature Flag System Architecture

The feature flag system enables dynamic activation/deactivation of features for different retail types and tenants.

```python
# Feature flag hierarchy
Environment Variables → Feature Definitions → Tenant Overrides → Runtime Settings
```

### Core Feature Categories

#### 1. Universal Core Features

```python
# config/feature_flags.py
UNIVERSAL_CORE_FEATURES = {
    'FEATURE_SALES_PROCESSING': {
        'default': True,
        'category': 'core',
        'description': 'Enable sales processing functionality',
        'required_retail_types': ['restaurant', 'retail', 'apparel', 'grocery'],
        'dependencies': ['FEATURE_PRODUCT_CATALOG']
    },
    'FEATURE_PRODUCT_CATALOG': {
        'default': True,
        'category': 'core',
        'description': 'Enable product catalog management',
        'required_retail_types': ['restaurant', 'retail', 'apparel', 'grocery'],
        'dependencies': []
    },
    'FEATURE_PAYMENT_PROCESSING': {
        'default': True,
        'category': 'core',
        'description': 'Enable payment processing',
        'required_retail_types': ['restaurant', 'retail', 'apparel', 'grocery'],
        'dependencies': ['FEATURE_SALES_PROCESSING']
    },
    'FEATURE_CUSTOMER_MANAGEMENT': {
        'default': True,
        'category': 'core',
        'description': 'Enable customer management',
        'required_retail_types': ['restaurant', 'retail', 'apparel', 'grocery'],
        'dependencies': []
    },
    'FEATURE_INVENTORY_BASIC': {
        'default': True,
        'category': 'core',
        'description': 'Enable basic inventory management',
        'required_retail_types': ['restaurant', 'retail', 'apparel', 'grocery'],
        'dependencies': ['FEATURE_PRODUCT_CATALOG']
    }
}
```

#### 2. Retail-Type Specific Features

```python
RETAIL_TYPE_FEATURES = {
    'restaurant': {
        'FEATURE_TABLE_MANAGEMENT': {
            'default': True,
            'description': 'Enable table management for restaurants',
            'dependencies': ['FEATURE_SALES_PROCESSING']
        },
        'FEATURE_KOT_PRINTING': {
            'default': True,
            'description': 'Enable Kitchen Order Ticket printing',
            'dependencies': ['FEATURE_TABLE_MANAGEMENT']
        },
        'FEATURE_KITCHEN_DISPLAY': {
            'default': False,
            'description': 'Enable Kitchen Display System',
            'dependencies': ['FEATURE_KOT_PRINTING']
        },
        'FEATURE_WAITER_MANAGEMENT': {
            'default': True,
            'description': 'Enable waiter/staff management',
            'dependencies': ['FEATURE_TABLE_MANAGEMENT']
        },
        'FEATURE_RESERVATIONS': {
            'default': False,
            'description': 'Enable table reservations',
            'dependencies': ['FEATURE_TABLE_MANAGEMENT']
        }
    },
    'apparel': {
        'FEATURE_SIZE_VARIANTS': {
            'default': True,
            'description': 'Enable size variants for products',
            'dependencies': ['FEATURE_PRODUCT_CATALOG']
        },
        'FEATURE_COLOR_VARIANTS': {
            'default': True,
            'description': 'Enable color variants for products',
            'dependencies': ['FEATURE_PRODUCT_CATALOG']
        },
        'FEATURE_STYLE_VARIANTS': {
            'default': True,
            'description': 'Enable style variants for products',
            'dependencies': ['FEATURE_PRODUCT_CATALOG']
        },
        'FEATURE_EXCHANGE_MANAGEMENT': {
            'default': True,
            'description': 'Enable product exchange management',
            'dependencies': ['FEATURE_SALES_PROCESSING']
        },
        'FEATURE_ALTERATION_TRACKING': {
            'default': False,
            'description': 'Enable alteration tracking',
            'dependencies': ['FEATURE_EXCHANGE_MANAGEMENT']
        }
    },
    'grocery': {
        'FEATURE_WEIGHING_SCALE': {
            'default': True,
            'description': 'Enable weighing scale integration',
            'dependencies': ['FEATURE_PRODUCT_CATALOG']
        },
        'FEATURE_EXPIRY_TRACKING': {
            'default': True,
            'description': 'Enable expiry date tracking',
            'dependencies': ['FEATURE_INVENTORY_BASIC']
        },
        'FEATURE_BATCH_TRACKING': {
            'default': True,
            'description': 'Enable batch tracking',
            'dependencies': ['FEATURE_INVENTORY_BASIC']
        },
        'FEATURE_PRICE_BY_WEIGHT': {
            'default': True,
            'description': 'Enable price by weight calculation',
            'dependencies': ['FEATURE_WEIGHING_SCALE']
        },
        'FEATURE_COMBO_OFFERS': {
            'default': True,
            'description': 'Enable combo offers',
            'dependencies': ['FEATURE_SALES_PROCESSING']
        }
    }
}
```

#### 3. Advanced Features

```python
ADVANCED_FEATURES = {
    'FEATURE_CRM_LOYALTY': {
        'default': False,
        'category': 'advanced',
        'description': 'Enable CRM and loyalty program',
        'dependencies': ['FEATURE_CUSTOMER_MANAGEMENT'],
        'configuration': {
            'points_per_rupee': 1.0,
            'redemption_rate': 100,
            'tier_levels': ['bronze', 'silver', 'gold', 'platinum']
        }
    },
    'FEATURE_MULTI_STORE': {
        'default': False,
        'category': 'advanced',
        'description': 'Enable multi-store management',
        'dependencies': ['FEATURE_INVENTORY_BASIC'],
        'configuration': {
            'max_stores': 10,
            'interstore_transfer': True,
            'centralized_inventory': False
        }
    },
    'FEATURE_ONLINE_ORDERS': {
        'default': False,
        'category': 'advanced',
        'description': 'Enable online order processing',
        'dependencies': ['FEATURE_SALES_PROCESSING'],
        'configuration': {
            'delivery_tracking': True,
            'order_notifications': True,
            'auto_accept_orders': False
        }
    },
    'FEATURE_ANALYTICS_REPORTING': {
        'default': False,
        'category': 'advanced',
        'description': 'Enable advanced analytics and reporting',
        'dependencies': [],
        'configuration': {
            'real_time_analytics': True,
            'custom_reports': True,
            'data_export': True
        }
    }
}
```

### Feature Flag Configuration in Environment

```bash
# .env file
# Core Features
FEATURE_SALES_PROCESSING=true
FEATURE_PRODUCT_CATALOG=true
FEATURE_PAYMENT_PROCESSING=true
FEATURE_CUSTOMER_MANAGEMENT=true
FEATURE_INVENTORY_BASIC=true

# Retail Type Configuration
RETAIL_TYPE=restaurant
FEATURE_TABLE_MANAGEMENT=true
FEATURE_KOT_PRINTING=true
FEATURE_KITCHEN_DISPLAY=false
FEATURE_WAITER_MANAGEMENT=true
FEATURE_RESERVATIONS=false

# Advanced Features
FEATURE_CRM_LOYALTY=false
FEATURE_MULTI_STORE=false
FEATURE_ONLINE_ORDERS=false
FEATURE_ANALYTICS_REPORTING=true

# Feature Configuration
FEATURE_CRM_LOYALTY_POINTS_PER_RUPEE=1.0
FEATURE_CRM_LOYALTY_REDEMPTION_RATE=100
FEATURE_MULTI_STORE_MAX_STORES=10
```

### Feature Flag Management

#### Creating Feature Definitions

```python
# utils/feature_manager.py
from models.feature_flag import FeatureDefinition, FeatureDependency

class FeatureManager:
    def __init__(self, db):
        self.db = db
    
    def create_feature_definition(self, name, display_name, description, 
                               category, **kwargs):
        """Create a new feature definition"""
        feature = FeatureDefinition(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            **kwargs
        )
        
        self.db.session.add(feature)
        self.db.session.commit()
        return feature
    
    def add_feature_dependency(self, feature_name, depends_on, 
                              dependency_type='required', **kwargs):
        """Add dependency between features"""
        dependency = FeatureDependency(
            feature_name=feature_name,
            depends_on_feature=depends_on,
            dependency_type=dependency_type,
            **kwargs
        )
        
        self.db.session.add(dependency)
        self.db.session.commit()
        return dependency
    
    def validate_feature_combination(self, features):
        """Validate feature combination for conflicts and dependencies"""
        issues = []
        
        # Check dependencies
        for feature in features:
            feature_def = FeatureDefinition.query.filter_by(name=feature).first()
            if feature_def:
                for dep in feature_def.dependencies:
                    if dep.dependency_type == 'required' and dep.depends_on_feature not in features:
                        issues.append(f"Feature {feature} requires {dep.depends_on_feature}")
        
        # Check conflicts
        enabled_features = set(features)
        for feature in features:
            feature_def = FeatureDefinition.query.filter_by(name=feature).first()
            if feature_def:
                for conflict in feature_def.conflicts:
                    if conflict.feature_2 in enabled_features:
                        issues.append(f"Feature {feature} conflicts with {conflict.feature_2}")
        
        return issues
```

#### Tenant-Specific Feature Configuration

```python
# routes/tenant_features.py
@app.route('/tenant/<tenant_id>/features', methods=['GET', 'POST'])
@login_required
def manage_tenant_features(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    
    if request.method == 'POST':
        # Update feature flags
        for feature_name, is_enabled in request.form.items():
            if feature_name.startswith('FEATURE_'):
                feature_flag = TenantFeatureFlag.query.filter_by(
                    tenant_id=tenant_id,
                    feature_name=feature_name
                ).first()
                
                if not feature_flag:
                    feature_flag = TenantFeatureFlag(
                        tenant_id=tenant_id,
                        feature_name=feature_name,
                        is_enabled=is_enabled == 'true'
                    )
                    db.session.add(feature_flag)
                else:
                    feature_flag.is_enabled = is_enabled == 'true'
                    feature_flag.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Features updated successfully!', 'success')
        return redirect(url_for('manage_tenant_features', tenant_id=tenant_id))
    
    # Get all available features
    all_features = FeatureDefinition.query.all()
    tenant_features = {
        f.feature_name: f.is_enabled 
        for f in TenantFeatureFlag.query.filter_by(tenant_id=tenant_id).all()
    }
    
    return render_template('tenant/features.html',
                        tenant=tenant,
                        all_features=all_features,
                        tenant_features=tenant_features)
```

---

## Retail-Type Specific Configuration

### Retail Type Configuration System

Each retail type has specific configuration requirements and feature sets.

#### Restaurant Configuration

```python
# config/retail_types.py
RESTAURANT_CONFIG = {
    'name': 'Restaurant',
    'description': 'Food service establishment',
    'features': {
        'required': [
            'FEATURE_SALES_PROCESSING',
            'FEATURE_PRODUCT_CATALOG',
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_KOT_PRINTING'
        ],
        'optional': [
            'FEATURE_KITCHEN_DISPLAY',
            'FEATURE_WAITER_MANAGEMENT',
            'FEATURE_RESERVATIONS',
            'FEATURE_DELIVERY_MANAGEMENT'
        ]
    },
    'workflows': {
        'dine_in': {
            'enabled': True,
            'steps': ['table_selection', 'order_placement', 'kot_printing', 'payment']
        },
        'takeaway': {
            'enabled': True,
            'steps': ['order_placement', 'order_preparation', 'pickup', 'payment']
        },
        'delivery': {
            'enabled': False,
            'steps': ['order_placement', 'order_preparation', 'delivery', 'payment']
        }
    },
    'settings': {
        'default_currency': 'INR',
        'tax_inclusive': False,
        'service_charge_enabled': True,
        'tip_enabled': True,
        'table_management': {
            'auto_merge_tables': False,
            'table_transfer_enabled': True,
            'split_bill_enabled': True
        },
        'kitchen_display': {
            'auto_refresh_interval': 30,
            'sound_alerts': True,
            'color_coding': True
        }
    },
    'payment_methods': {
        'cash': {'enabled': True, 'required': True},
        'card': {'enabled': True, 'required': False},
        'upi': {'enabled': True, 'required': False},
        'wallet': {'enabled': True, 'required': False}
    }
}
```

#### Apparel & Footwear Configuration

```python
APPAREL_CONFIG = {
    'name': 'Apparel & Footwear',
    'description': 'Clothing and footwear store',
    'features': {
        'required': [
            'FEATURE_SALES_PROCESSING',
            'FEATURE_PRODUCT_CATALOG',
            'FEATURE_SIZE_VARIANTS',
            'FEATURE_COLOR_VARIANTS',
            'FEATURE_EXCHANGE_MANAGEMENT'
        ],
        'optional': [
            'FEATURE_STYLE_VARIANTS',
            'FEATURE_ALTERATION_TRACKING',
            'FEATURE_SEASONAL_COLLECTIONS',
            'FEATURE_SIZE_CHARTS'
        ]
    },
    'product_attributes': {
        'size_variants': {
            'enabled': True,
            'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL'],
            'custom_sizes': True,
            'size_charts': True
        },
        'color_variants': {
            'enabled': True,
            'color_mapping': True,
            'color_images': True
        },
        'style_variants': {
            'enabled': True,
            'style_categories': ['casual', 'formal', 'sports', 'ethnic'],
            'custom_styles': True
        }
    },
    'workflows': {
        'sale': {
            'enabled': True,
            'steps': ['product_selection', 'variant_selection', 'payment']
        },
        'exchange': {
            'enabled': True,
            'steps': ['original_order_lookup', 'exchange_selection', 'price_adjustment', 'payment']
        },
        'return': {
            'enabled': True,
            'steps': ['original_order_lookup', 'return_reason', 'refund_processing']
        },
        'alteration': {
            'enabled': False,
            'steps': ['measurement', 'alteration_request', 'tracking', 'completion']
        }
    },
    'settings': {
        'exchange_policy': {
            'days_allowed': 30,
            'original_tags_required': True,
            'exchange_conditions': ['size', 'color', 'style']
        },
        'inventory_management': {
            'track_by_variant': True,
            'low_stock_alerts': True,
            'reorder_points': True
        }
    }
}
```

#### Grocery & Supermarket Configuration

```python
GROCERY_CONFIG = {
    'name': 'Grocery & Supermarket',
    'description': 'Grocery store or supermarket',
    'features': {
        'required': [
            'FEATURE_SALES_PROCESSING',
            'FEATURE_PRODUCT_CATALOG',
            'FEATURE_WEIGHING_SCALE',
            'FEATURE_EXPIRY_TRACKING'
        ],
        'optional': [
            'FEATURE_BATCH_TRACKING',
            'FEATURE_PRICE_BY_WEIGHT',
            'FEATURE_COMBO_OFFERS',
            'FEATURE_MEMBERSHIP_PROGRAM'
        ]
    },
    'product_attributes': {
        'weighing_scale': {
            'enabled': True,
            'scale_integration': True,
            'price_by_weight': True,
            'weight_units': ['kg', 'g', 'lb', 'oz']
        },
        'expiry_tracking': {
            'enabled': True,
            'expiry_alerts': True,
            'discount_near_expiry': True,
            'auto_remove_expired': True
        },
        'batch_tracking': {
            'enabled': True,
            'batch_numbers': True,
            'manufacture_date': True,
            'supplier_tracking': True
        }
    },
    'workflows': {
        'counter_sale': {
            'enabled': True,
            'steps': ['product_scanning', 'weighing', 'pricing', 'payment']
        },
        'bulk_sale': {
            'enabled': True,
            'steps': ['bulk_selection', 'quantity_pricing', 'payment']
        },
        'home_delivery': {
            'enabled': False,
            'steps': ['order_placement', 'packing', 'delivery', 'payment']
        }
    },
    'settings': {
        'pricing': {
            'dynamic_pricing': True,
            'happy_hours': False,
            'bulk_discounts': True,
            'membership_pricing': False
        },
        'inventory': {
            'perishable_tracking': True,
            'auto_reorder': True,
            'supplier_management': True
        }
    }
}
```

### Retail Type Configuration Management

#### Retail Type Manager

```python
# utils/retail_type_manager.py
class RetailTypeManager:
    def __init__(self):
        self.retail_configs = {
            'restaurant': RESTAURANT_CONFIG,
            'apparel': APPAREL_CONFIG,
            'grocery': GROCERY_CONFIG
        }
    
    def get_retail_type_config(self, retail_type):
        """Get configuration for specific retail type"""
        return self.retail_configs.get(retail_type)
    
    def get_required_features(self, retail_type):
        """Get required features for retail type"""
        config = self.get_retail_type_config(retail_type)
        return config['features']['required'] if config else []
    
    def get_optional_features(self, retail_type):
        """Get optional features for retail type"""
        config = self.get_retail_type_config(retail_type)
        return config['features']['optional'] if config else []
    
    def get_workflows(self, retail_type):
        """Get available workflows for retail type"""
        config = self.get_retail_type_config(retail_type)
        return config['workflows'] if config else {}
    
    def validate_retail_type_features(self, retail_type, enabled_features):
        """Validate features for retail type"""
        config = self.get_retail_type_config(retail_type)
        if not config:
            return False, f"Unknown retail type: {retail_type}"
        
        required_features = config['features']['required']
        missing_features = [f for f in required_features if f not in enabled_features]
        
        if missing_features:
            return False, f"Missing required features: {missing_features}"
        
        return True, "Features are valid for retail type"
    
    def apply_retail_type_defaults(self, tenant_id, retail_type):
        """Apply retail type default configuration to tenant"""
        config = self.get_retail_type_config(retail_type)
        if not config:
            return False, f"Unknown retail type: {retail_type}"
        
        # Enable required features
        for feature in config['features']['required']:
            feature_flag = TenantFeatureFlag.query.filter_by(
                tenant_id=tenant_id,
                feature_name=feature
            ).first()
            
            if not feature_flag:
                feature_flag = TenantFeatureFlag(
                    tenant_id=tenant_id,
                    feature_name=feature,
                    is_enabled=True
                )
                db.session.add(feature_flag)
            else:
                feature_flag.is_enabled = True
                feature_flag.updated_at = datetime.utcnow()
        
        # Apply default settings
        tenant_settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
        if tenant_settings:
            tenant_settings.retail_type = retail_type
            # Apply retail type specific settings
            if 'settings' in config:
                for key, value in config['settings'].items():
                    if hasattr(tenant_settings, key):
                        setattr(tenant_settings, key, value)
        
        db.session.commit()
        return True, f"Applied {retail_type} configuration to tenant"
```

---

## Multi-Tenant Configuration

### Tenant Configuration Architecture

The multi-tenant system supports different isolation strategies and configuration options.

#### Tenant Isolation Strategies

```python
# config/multi_tenant.py
TENANT_ISOLATION_STRATEGIES = {
    'database': {
        'name': 'Database per Tenant',
        'description': 'Each tenant gets a separate database',
        'isolation_level': 'high',
        'performance': 'high',
        'complexity': 'high',
        'cost': 'high'
    },
    'schema': {
        'name': 'Schema per Tenant',
        'description': 'Each tenant gets a separate schema in shared database',
        'isolation_level': 'medium',
        'performance': 'medium',
        'complexity': 'medium',
        'cost': 'medium'
    },
    'row_level': {
        'name': 'Row-Level Security',
        'description': 'All tenants share tables with row-level security',
        'isolation_level': 'low',
        'performance': 'low',
        'complexity': 'low',
        'cost': 'low'
    }
}
```

#### Tenant Configuration

```python
# models/tenant.py
class TenantConfiguration:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.load_configuration()
    
    def load_configuration(self):
        """Load tenant configuration from database"""
        tenant = Tenant.query.get(self.tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {self.tenant_id} not found")
        
        self.tenant = tenant
        self.settings = TenantSettings.query.filter_by(tenant_id=self.tenant_id).first()
        self.feature_flags = self.load_feature_flags()
        self.retail_config = self.load_retail_config()
    
    def load_feature_flags(self):
        """Load tenant-specific feature flags"""
        return {
            flag.feature_name: flag.is_enabled
            for flag in TenantFeatureFlag.query.filter_by(tenant_id=self.tenant_id).all()
        }
    
    def load_retail_config(self):
        """Load retail type configuration"""
        if not self.settings or not self.settings.retail_type:
            return None
        
        from utils.retail_type_manager import RetailTypeManager
        manager = RetailTypeManager()
        return manager.get_retail_type_config(self.settings.retail_type)
    
    def get_database_config(self):
        """Get database configuration for tenant"""
        if self.tenant.isolation_strategy == 'database':
            return {
                'database_name': self.tenant.database_name,
                'host': self.tenant.database_host,
                'port': self.tenant.database_port,
                'user': self.tenant.database_user,
                'password': self.tenant.database_password
            }
        elif self.tenant.isolation_strategy == 'schema':
            return {
                'database_name': 'shared_database',
                'schema': self.tenant.schema_name,
                'host': 'localhost',
                'port': 5432,
                'user': 'shared_user',
                'password': 'shared_password'
            }
        else:  # row_level
            return {
                'database_name': 'shared_database',
                'host': 'localhost',
                'port': 5432,
                'user': 'shared_user',
                'password': 'shared_password',
                'tenant_id': self.tenant_id
            }
    
    def get_feature_config(self, feature_name):
        """Get configuration for specific feature"""
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=self.tenant_id,
            feature_name=feature_name
        ).first()
        
        if feature_flag:
            return {
                'enabled': feature_flag.is_enabled,
                'configuration': feature_flag.configuration,
                'expires_at': feature_flag.expires_at
            }
        
        return None
    
    def update_feature_config(self, feature_name, enabled, configuration=None):
        """Update feature configuration"""
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=self.tenant_id,
            feature_name=feature_name
        ).first()
        
        if not feature_flag:
            feature_flag = TenantFeatureFlag(
                tenant_id=self.tenant_id,
                feature_name=feature_name,
                is_enabled=enabled
            )
            db.session.add(feature_flag)
        else:
            feature_flag.is_enabled = enabled
            feature_flag.updated_at = datetime.utcnow()
        
        if configuration:
            feature_flag.configuration = configuration
        
        db.session.commit()
        return feature_flag
```

#### Tenant Creation Configuration

```python
# routes/tenant.py
@app.route('/admin/tenants/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_tenant():
    form = TenantCreationForm()
    
    if form.validate_on_submit():
        try:
            # Create tenant
            tenant = Tenant(
                name=form.name.data,
                subdomain=form.subdomain.data,
                custom_domain=form.custom_domain.data,
                isolation_strategy=form.isolation_strategy.data,
                retail_type=form.retail_type.data,
                plan_id=form.plan_id.data,
                status='pending_setup'
            )
            
            db.session.add(tenant)
            db.session.flush()  # Get tenant ID
            
            # Setup tenant infrastructure based on isolation strategy
            if tenant.isolation_strategy == 'database':
                setup_database_isolation(tenant)
            elif tenant.isolation_strategy == 'schema':
                setup_schema_isolation(tenant)
            else:  # row_level
                setup_row_level_isolation(tenant)
            
            # Create tenant settings
            settings = TenantSettings(tenant_id=tenant.id)
            settings.retail_type = form.retail_type.data
            
            # Apply retail type defaults
            from utils.retail_type_manager import RetailTypeManager
            manager = RetailTypeManager()
            manager.apply_retail_type_defaults(tenant.id, form.retail_type.data)
            
            db.session.add(settings)
            
            # Create admin user
            admin_user = User(
                username=form.admin_username.data,
                email=form.admin_email.data,
                password=generate_password_hash(form.admin_password.data),
                role='administrator',
                tenant_id=tenant.id
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Send welcome email
            send_tenant_welcome_email(tenant, admin_user)
            
            flash('Tenant created successfully!', 'success')
            return redirect(url_for('admin.list_tenants'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tenant: {str(e)}', 'error')
    
    return render_template('admin/tenants/create.html', form=form)

def setup_database_isolation(tenant):
    """Setup database isolation for tenant"""
    database_name = f"tenant_{tenant.id}_pos"
    
    # Create database
    engine = create_engine('postgresql://postgres:password@localhost/postgres')
    engine.execute(f"CREATE DATABASE {database_name}")
    
    # Update tenant record
    tenant.database_name = database_name
    tenant.database_host = 'localhost'
    tenant.database_port = 5432
    tenant.database_user = f"tenant_{tenant.id}"
    tenant.database_password = generate_secure_password()
    
    # Create database user
    engine.execute(f"CREATE USER {tenant.database_user} WITH PASSWORD '{tenant.database_password}'")
    engine.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO {tenant.database_user}")
    
    # Create tables in tenant database
    tenant_engine = create_engine(
        f"postgresql://{tenant.database_user}:{tenant.database_password}@localhost:5432/{database_name}"
    )
    Base.metadata.create_all(tenant_engine)

def setup_schema_isolation(tenant):
    """Setup schema isolation for tenant"""
    schema_name = f"tenant_{tenant.id}"
    
    # Create schema
    db.session.execute(f"CREATE SCHEMA {schema_name}")
    
    # Update tenant record
    tenant.schema_name = schema_name
    
    # Create tables in schema
    db.session.execute(f"SET search_path TO {schema_name}")
    Base.metadata.create_all(db.engine)
    db.session.execute(f"SET search_path TO public")

def setup_row_level_isolation(tenant):
    """Setup row-level security for tenant"""
    # Enable row-level security on all tables
    tables = ['customers', 'orders', 'menu_items', 'payments']
    
    for table in tables:
        db.session.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        
        # Create policy
        db.session.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            FOR ALL TO application_user
            USING (tenant_id = '{tenant.id}')
        """)
```

---

## Security Configuration

### Security Configuration Layers

The POS system implements multiple layers of security configuration.

#### 1. Application Security

```python
# config/security.py
class SecurityConfig:
    # Authentication
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Session Security
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour
    MAX_CONCURRENT_SESSIONS = int(os.environ.get('MAX_CONCURRENT_SESSIONS', 3))
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Password Policy
    PASSWORD_MIN_LENGTH = int(os.environ.get('PASSWORD_MIN_LENGTH', 8))
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_EXPIRY_DAYS = int(os.environ.get('PASSWORD_EXPIRY_DAYS', 90))
    
    # Rate Limiting
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},
        'auth': {'requests': 5, 'window': 300},
        'api': {'requests': 200, 'window': 60},
        'upload': {'requests': 10, 'window': 300}
    }
    
    # IP Blocking
    IP_BLOCK_DURATION = int(os.environ.get('IP_BLOCK_DURATION', 3600))
    MAX_FAILED_ATTEMPTS = int(os.environ.get('MAX_FAILED_ATTEMPTS', 5))
    
    # Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    ENCRYPTION_ALGORITHM = 'AES-256-GCM'
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https://api.razorpay.com"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
```

#### 2. Tenant Security Configuration

```python
# models/tenant_security.py
class TenantSecuritySettings(db.Model):
    __tablename__ = 'tenant_security_settings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # Password Policy
    password_min_length = db.Column(db.Integer, default=8)
    password_require_uppercase = db.Column(db.Boolean, default=True)
    password_require_lowercase = db.Column(db.Boolean, default=True)
    password_require_digits = db.Column(db.Boolean, default=True)
    password_require_special = db.Column(db.Boolean, default=True)
    password_expiry_days = db.Column(db.Integer, default=90)
    
    # Session Policy
    session_timeout = db.Column(db.Integer, default=3600)
    max_concurrent_sessions = db.Column(db.Integer, default=3)
    require_2fa = db.Column(db.Boolean, default=False)
    
    # IP Restrictions
    allowed_ips = db.Column(db.JSON, nullable=True)
    block_unknown_ips = db.Column(db.Boolean, default=False)
    
    # API Security
    api_rate_limit = db.Column(db.Integer, default=1000)
    api_key_required = db.Column(db.Boolean, default=False)
    
    # Audit Settings
    audit_login_attempts = db.Column(db.Boolean, default=True)
    audit_data_access = db.Column(db.Boolean, default=True)
    audit_data_changes = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def validate_password(self, password):
        """Validate password against tenant policy"""
        if len(password) < self.password_min_length:
            return False, f"Password must be at least {self.password_min_length} characters"
        
        if self.password_require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letters"
        
        if self.password_require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain lowercase letters"
        
        if self.password_require_digits and not any(c.isdigit() for c in password):
            return False, "Password must contain digits"
        
        if self.password_require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Password must contain special characters"
        
        return True, "Password is valid"
    
    def is_ip_allowed(self, ip_address):
        """Check if IP address is allowed"""
        if not self.allowed_ips:
            return True
        
        return ip_address in self.allowed_ips
    
    def to_dict(self):
        """Convert security settings to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'password_min_length': self.password_min_length,
            'password_require_uppercase': self.password_require_uppercase,
            'password_require_lowercase': self.password_require_lowercase,
            'password_require_digits': self.password_require_digits,
            'password_require_special': self.password_require_special,
            'password_expiry_days': self.password_expiry_days,
            'session_timeout': self.session_timeout,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'require_2fa': self.require_2fa,
            'allowed_ips': self.allowed_ips,
            'block_unknown_ips': self.block_unknown_ips,
            'api_rate_limit': self.api_rate_limit,
            'api_key_required': self.api_key_required,
            'audit_login_attempts': self.audit_login_attempts,
            'audit_data_access': self.audit_data_access,
            'audit_data_changes': self.audit_data_changes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

#### 3. Data Encryption Configuration

```python
# utils/encryption.py
from cryptography.fernet import Fernet
import os

class DataEncryption:
    def __init__(self, key=None):
        self.key = key or os.environ.get('ENCRYPTION_KEY')
        if not self.key:
            raise ValueError("Encryption key not provided")
        self.cipher = Fernet(self.key.encode())
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        return self.cipher.decrypt(encrypted_data).decode()
    
    def encrypt_sensitive_fields(self, model_instance, sensitive_fields):
        """Encrypt sensitive fields in model instance"""
        for field in sensitive_fields:
            if hasattr(model_instance, field):
                value = getattr(model_instance, field)
                if value:
                    encrypted_value = self.encrypt_data(str(value))
                    setattr(model_instance, field, encrypted_value)
    
    def decrypt_sensitive_fields(self, model_instance, sensitive_fields):
        """Decrypt sensitive fields in model instance"""
        for field in sensitive_fields:
            if hasattr(model_instance, field):
                value = getattr(model_instance, field)
                if value:
                    try:
                        decrypted_value = self.decrypt_data(value)
                        setattr(model_instance, field, decrypted_value)
                    except Exception:
                        # Field might not be encrypted
                        pass

# Usage in models
class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    
    # Sensitive fields
    credit_card = db.Column(db.String(255), nullable=True)
    ssn = db.Column(db.String(20), nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.encrypt_sensitive_data()
    
    def encrypt_sensitive_data(self):
        """Encrypt sensitive fields"""
        encryption = DataEncryption()
        sensitive_fields = ['credit_card', 'ssn']
        encryption.encrypt_sensitive_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary with optional sensitive data"""
        data = {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone
        }
        
        if include_sensitive:
            encryption = DataEncryption()
            sensitive_fields = ['credit_card', 'ssn']
            temp_instance = Customer(
                credit_card=self.credit_card,
                ssn=self.ssn
            )
            encryption.decrypt_sensitive_fields(temp_instance, sensitive_fields)
            data.update({
                'credit_card': temp_instance.credit_card,
                'ssn': temp_instance.ssn
            })
        
        return data
```

---

## Performance Tuning

### Database Performance Configuration

#### Connection Pooling

```python
# config/database.py
class DatabaseConfig:
    # Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', 30)),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'pool_reset_on_return': 'commit'
    }
    
    # Query Optimization
    SQLALCHEMY_RECORD_QUERIES = os.environ.get('FLASK_ENV') == 'development'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Index Strategy
    AUTO_CREATE_INDEXES = True
    INDEX_ANALYSIS_ENABLED = True
    
    # Query Caching
    QUERY_CACHE_ENABLED = True
    QUERY_CACHE_TTL = int(os.environ.get('QUERY_CACHE_TTL', 300))
    
    @staticmethod
    def get_tenant_database_config(tenant_id):
        """Get database configuration for specific tenant"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        if tenant.isolation_strategy == 'database':
            return {
                'database_url': (
                    f"postgresql://{tenant.database_user}:{tenant.database_password}"
                    f"@{tenant.database_host}:{tenant.database_port}/{tenant.database_name}"
                ),
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 30,
                'pool_recycle': 3600
            }
        else:
            return {
                'database_url': os.environ.get('DATABASE_URL'),
                'pool_size': 20,
                'max_overflow': 30,
                'pool_timeout': 30,
                'pool_recycle': 3600
            }
```

#### Database Indexing Strategy

```python
# utils/database_indexing.py
class DatabaseIndexManager:
    def __init__(self, db):
        self.db = db
    
    def create_tenant_indexes(self, tenant_id):
        """Create indexes for tenant-specific queries"""
        indexes = [
            # Customer indexes
            "CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tenant_email ON customers(tenant_id, email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tenant_phone ON customers(tenant_id, phone)",
            
            # Order indexes
            "CREATE INDEX IF NOT EXISTS idx_orders_tenant_id ON orders(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_tenant_status ON orders(tenant_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_orders_tenant_date ON orders(tenant_id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_tenant_customer ON orders(tenant_id, customer_id)",
            
            # Product indexes
            "CREATE INDEX IF NOT EXISTS idx_menu_items_tenant_id ON menu_items(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_menu_items_tenant_category ON menu_items(tenant_id, category)",
            "CREATE INDEX IF NOT EXISTS idx_menu_items_tenant_available ON menu_items(tenant_id, available)",
            
            # Payment indexes
            "CREATE INDEX IF NOT EXISTS idx_payments_tenant_id ON payments(tenant_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_tenant_status ON payments(tenant_id, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_tenant_date ON payments(tenant_id, created_at)"
        ]
        
        for index_sql in indexes:
            try:
                self.db.session.execute(index_sql)
            except Exception as e:
                print(f"Error creating index: {e}")
        
        self.db.session.commit()
    
    def analyze_query_performance(self, tenant_id, query):
        """Analyze query performance and suggest optimizations"""
        # Execute EXPLAIN ANALYZE
        explain_query = f"EXPLAIN ANALYZE {query}"
        result = self.db.session.execute(explain_query).fetchall()
        
        # Analyze results
        suggestions = []
        for row in result:
            plan = row[0]
            if 'Seq Scan' in plan and 'tenant_id' in query:
                suggestions.append("Consider adding index on tenant_id column")
            if 'Sort' in plan and 'ORDER BY' in query:
                suggestions.append("Consider adding index for ORDER BY columns")
            if 'Hash Join' in plan:
                suggestions.append("Consider optimizing join conditions")
        
        return {
            'query': query,
            'execution_plan': result,
            'suggestions': suggestions
        }
```

### Caching Configuration

#### Multi-Level Caching Strategy

```python
# utils/cache_manager.py
class CacheManager:
    def __init__(self, app=None):
        self.app = app
        self.l1_cache = {}  # In-memory cache
        self.l2_cache = None  # Redis cache
        self.l3_cache = None  # Database cache
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache manager with Flask app"""
        self.app = app
        
        # Initialize Redis cache
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        self.l2_cache = redis.from_url(redis_url)
        
        # Cache configuration
        self.l1_cache_size = app.config.get('L1_CACHE_SIZE', 1000)
        self.l1_cache_ttl = app.config.get('L1_CACHE_TTL', 300)
        self.l2_cache_ttl = app.config.get('L2_CACHE_TTL', 3600)
    
    def get(self, key, tenant_id=None):
        """Get value from cache with tenant isolation"""
        cache_key = self._get_cache_key(key, tenant_id)
        
        # Try L1 cache first
        if cache_key in self.l1_cache:
            item = self.l1_cache[cache_key]
            if not self._is_expired(item):
                return item['value']
            else:
                del self.l1_cache[cache_key]
        
        # Try L2 cache
        if self.l2_cache:
            try:
                value = self.l2_cache.get(cache_key)
                if value:
                    # Store in L1 cache
                    self._set_l1_cache(cache_key, value)
                    return value
            except Exception:
                pass
        
        return None
    
    def set(self, key, value, tenant_id=None, timeout=None):
        """Set value in cache with tenant isolation"""
        cache_key = self._get_cache_key(key, tenant_id)
        
        # Set in L1 cache
        self._set_l1_cache(cache_key, value, timeout)
        
        # Set in L2 cache
        if self.l2_cache:
            try:
                ttl = timeout or self.l2_cache_ttl
                self.l2_cache.setex(cache_key, ttl, value)
            except Exception:
                pass
    
    def delete(self, key, tenant_id=None):
        """Delete value from cache"""
        cache_key = self._get_cache_key(key, tenant_id)
        
        # Delete from L1 cache
        if cache_key in self.l1_cache:
            del self.l1_cache[cache_key]
        
        # Delete from L2 cache
        if self.l2_cache:
            try:
                self.l2_cache.delete(cache_key)
            except Exception:
                pass
    
    def clear_tenant_cache(self, tenant_id):
        """Clear all cache for specific tenant"""
        # Clear L1 cache
        keys_to_delete = [k for k in self.l1_cache.keys() if f"tenant:{tenant_id}:" in k]
        for key in keys_to_delete:
            del self.l1_cache[key]
        
        # Clear L2 cache
        if self.l2_cache:
            try:
                pattern = f"tenant:{tenant_id}:*"
                keys = self.l2_cache.keys(pattern)
                if keys:
                    self.l2_cache.delete(*keys)
            except Exception:
                pass
    
    def _get_cache_key(self, key, tenant_id=None):
        """Generate cache key with tenant isolation"""
        if tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return f"global:{key}"
    
    def _set_l1_cache(self, key, value, timeout=None):
        """Set value in L1 cache with TTL"""
        ttl = timeout or self.l1_cache_ttl
        
        # Check cache size limit
        if len(self.l1_cache) >= self.l1_cache_size:
            # Remove oldest item
            oldest_key = min(self.l1_cache.keys(), 
                          key=lambda k: self.l1_cache[k]['timestamp'])
            del self.l1_cache[oldest_key]
        
        self.l1_cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'ttl': ttl
        }
    
    def _is_expired(self, item):
        """Check if cache item is expired"""
        return time.time() - item['timestamp'] > item['ttl']

# Cache decorator for functions
def cached(timeout=300, key_prefix=None):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix or f.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Get current tenant ID
            tenant_id = get_current_tenant_id()
            
            # Try to get from cache
            cache_manager = current_app.extensions.get('cache_manager')
            if cache_manager:
                cached_result = cache_manager.get(cache_key, tenant_id)
                if cached_result is not None:
                    return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache result
            if cache_manager:
                cache_manager.set(cache_key, result, tenant_id, timeout)
            
            return result
        return decorated_function
    return decorator
```

---

## Integration Configuration

### Payment Gateway Configuration

#### Razorpay Configuration

```python
# config/payments.py
class PaymentConfig:
    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')
    RAZORPAY_TEST_MODE = os.environ.get('RAZORPAY_TEST_MODE', 'True').lower() == 'true'
    
    # Payment Settings
    MIN_PAYMENT_AMOUNT = float(os.environ.get('MIN_PAYMENT_AMOUNT', 1.00))  # ₹1.00
    MAX_PAYMENT_AMOUNT = float(os.environ.get('MAX_PAYMENT_AMOUNT', 100000.00))  # ₹100,000.00
    CURRENCY = 'INR'
    
    # Webhook Settings
    WEBHOOK_ENDPOINT = '/api/webhooks/razorpay'
    WEBHOOK_TIMEOUT = 30
    
    # Refund Settings
    AUTO_REFUND_ENABLED = True
    REFUND_TIMEOUT = 7  # days
    
    # Payment Methods Configuration
    PAYMENT_METHODS = {
        'card': {
            'enabled': True,
            'display_name': 'Credit/Debit Card',
            'min_amount': 1.00,
            'max_amount': 100000.00,
            'supported_networks': ['Visa', 'Mastercard', 'Rupay', 'Amex']
        },
        'upi': {
            'enabled': True,
            'display_name': 'UPI',
            'min_amount': 1.00,
            'max_amount': 100000.00,
            'supported_apps': ['gpay', 'phonepe', 'paytm', 'bhim']
        },
        'netbanking': {
            'enabled': True,
            'display_name': 'Net Banking',
            'min_amount': 100.00,
            'max_amount': 100000.00,
            'supported_banks': ['HDFC', 'ICICI', 'SBI', 'PNB', 'Axis']
        },
        'wallet': {
            'enabled': True,
            'display_name': 'Mobile Wallet',
            'min_amount': 1.00,
            'max_amount': 10000.00,
            'supported_wallets': ['paytm', 'phonepe', 'amazonpay', 'freecharge']
        }
    }
    
    @staticmethod
    def get_tenant_payment_config(tenant_id):
        """Get payment configuration for specific tenant"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
        if not settings:
            return None
        
        return {
            'key_id': settings.razorpay_key_id or PaymentConfig.RAZORPAY_KEY_ID,
            'key_secret': settings.razorpay_key_secret or PaymentConfig.RAZORPAY_KEY_SECRET,
            'webhook_secret': settings.razorpay_webhook_secret or PaymentConfig.RAZORPAY_WEBHOOK_SECRET,
            'test_mode': settings.razorpay_test_mode if settings.razorpay_test_mode is not None else PaymentConfig.RAZORPAY_TEST_MODE,
            'payment_methods': settings.payment_methods or PaymentConfig.PAYMENT_METHODS
        }
```

#### Email Configuration

```python
# config/email.py
class EmailConfig:
    # SMTP Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    
    # Authentication
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Email Settings
    MAIL_SUPPRESS_SEND = os.environ.get('FLASK_ENV') == 'development'
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_MAX_EMAILS = 50
    MAIL_MAX_ATTACHMENTS = 10
    
    # Templates
    EMAIL_TEMPLATES_DIR = 'templates/email'
    EMAIL_TEMPLATE_AUTO_RELOAD = os.environ.get('FLASK_ENV') == 'development'
    
    # Email Services Configuration
    EMAIL_SERVICES = {
        'notifications': {
            'enabled': True,
            'templates': ['order_confirmation', 'payment_receipt', 'loyalty_update']
        },
        'marketing': {
            'enabled': True,
            'templates': ['promotion', 'newsletter', 'birthday_offer']
        },
        'alerts': {
            'enabled': True,
            'templates': ['security_alert', 'system_alert', 'payment_failure']
        }
    }
    
    @staticmethod
    def get_tenant_email_config(tenant_id):
        """Get email configuration for specific tenant"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
        if not settings or not settings.email_settings:
            return EmailConfig()
        
        email_settings = settings.email_settings
        
        return {
            'mail_server': email_settings.get('mail_server', EmailConfig.MAIL_SERVER),
            'mail_port': email_settings.get('mail_port', EmailConfig.MAIL_PORT),
            'mail_use_tls': email_settings.get('mail_use_tls', EmailConfig.MAIL_USE_TLS),
            'mail_username': email_settings.get('mail_username', EmailConfig.MAIL_USERNAME),
            'mail_password': email_settings.get('mail_password', EmailConfig.MAIL_PASSWORD),
            'mail_default_sender': email_settings.get('mail_default_sender', EmailConfig.MAIL_DEFAULT_SENDER),
            'email_services': email_settings.get('email_services', EmailConfig.EMAIL_SERVICES)
        }
```

---

## Environment-Specific Configuration

### Development Environment

```python
# config/development.py
from . import Config
import os

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///restaurant_pos_dev.db')
    SQLALCHEMY_ECHO = True
    
    # Security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    
    # Email
    MAIL_SUPPRESS_SEND = True
    
    # Caching
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Debug toolbar
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    
    # Feature flags for development
    FEATURE_CRM_LOYALTY = True
    FEATURE_MULTI_STORE = True
    FEATURE_ONLINE_ORDERS = True
    FEATURE_ANALYTICS_REPORTING = True
    
    # Performance monitoring
    PERFORMANCE_MONITORING = True
    SLOW_QUERY_THRESHOLD = 0.5  # seconds
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_TO_CONSOLE = True
```

### Production Environment

```python
# config/production.py
from . import Config
import os

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ECHO = False
    
    # Connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 20)),
        'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 30)),
        'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True
    }
    
    # Security
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Performance
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Feature flags for production
    FEATURE_CRM_LOYALTY = os.environ.get('FEATURE_CRM_LOYALTY', 'False').lower() == 'true'
    FEATURE_MULTI_STORE = os.environ.get('FEATURE_MULTI_STORE', 'False').lower() == 'true'
    FEATURE_ONLINE_ORDERS = os.environ.get('FEATURE_ONLINE_ORDERS', 'False').lower() == 'true'
    FEATURE_ANALYTICS_REPORTING = True
    
    # Performance monitoring
    PERFORMANCE_MONITORING = True
    SLOW_QUERY_THRESHOLD = 1.0  # seconds
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_TO_CONSOLE = False
    LOG_FILE = '/var/log/pos/app.log'
    
    # Security headers
    FORCE_HTTPS = True
    SECURITY_HEADERS_ENABLED = True
```

### Testing Environment

```python
# config/testing.py
from . import Config
import os

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    
    # Security
    WTF_CSRF_ENABLED = False
    
    # Caching
    CACHE_TYPE = 'null'
    
    # Feature flags for testing
    FEATURE_CRM_LOYALTY = True
    FEATURE_MULTI_STORE = True
    FEATURE_ONLINE_ORDERS = True
    FEATURE_ANALYTICS_REPORTING = True
    
    # Performance monitoring
    PERFORMANCE_MONITORING = False
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_TO_CONSOLE = True
    
    # Test-specific settings
    TEST_DATA_GENERATION = True
    TEST_USER_PASSWORD = 'testpassword123'
    TEST_TENANT_SUBDOMAIN = 'test-tenant'
```

---

## Configuration Management

### Configuration Validation

```python
# utils/config_validator.py
class ConfigurationValidator:
    def __init__(self, config):
        self.config = config
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """Validate all configuration sections"""
        self.validate_database()
        self.validate_security()
        self.validate_payment()
        self.validate_email()
        self.validate_features()
        self.validate_multi_tenancy()
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def validate_database(self):
        """Validate database configuration"""
        if not self.config.get('SQLALCHEMY_DATABASE_URI'):
            self.errors.append("Database URL is required")
        
        if self.config.get('SQLALCHEMY_ENGINE_OPTIONS'):
            options = self.config['SQLALCHEMY_ENGINE_OPTIONS']
            if options.get('pool_size', 0) < 1:
                self.errors.append("Database pool size must be at least 1")
            
            if options.get('max_overflow', 0) < 0:
                self.errors.append("Database max overflow cannot be negative")
    
    def validate_security(self):
        """Validate security configuration"""
        if not self.config.get('SECRET_KEY'):
            self.errors.append("SECRET_KEY is required")
        elif len(self.config['SECRET_KEY']) < 32:
            self.warnings.append("SECRET_KEY should be at least 32 characters")
        
        if not self.config.get('SECURITY_PASSWORD_SALT'):
            self.warnings.append("SECURITY_PASSWORD_SALT is recommended")
        
        if self.config.get('SESSION_TIMEOUT', 0) < 300:
            self.warnings.append("Session timeout should be at least 5 minutes")
    
    def validate_payment(self):
        """Validate payment configuration"""
        if self.config.get('RAZORPAY_TEST_MODE', False):
            self.warnings.append("Payment gateway is in test mode")
        
        if not self.config.get('RAZORPAY_KEY_ID'):
            self.errors.append("Razorpay Key ID is required")
        
        if not self.config.get('RAZORPAY_KEY_SECRET'):
            self.errors.append("Razorpay Key Secret is required")
    
    def validate_email(self):
        """Validate email configuration"""
        if not self.config.get('MAIL_SERVER'):
            self.warnings.append("Mail server not configured")
        
        if not self.config.get('MAIL_USERNAME'):
            self.warnings.append("Mail username not configured")
        
        if not self.config.get('MAIL_PASSWORD'):
            self.warnings.append("Mail password not configured")
    
    def validate_features(self):
        """Validate feature configuration"""
        required_features = ['FEATURE_SALES_PROCESSING', 'FEATURE_PRODUCT_CATALOG']
        
        for feature in required_features:
            if not self.config.get(feature):
                self.errors.append(f"Required feature {feature} is disabled")
    
    def validate_multi_tenancy(self):
        """Validate multi-tenancy configuration"""
        if self.config.get('MULTI_TENANT', False):
            if not self.config.get('TENANT_ISOLATION_STRATEGY'):
                self.errors.append("Tenant isolation strategy is required for multi-tenancy")
            
            if not self.config.get('DEFAULT_TENANT'):
                self.warnings.append("Default tenant is recommended for multi-tenancy")
```

### Configuration Management CLI

```python
# cli/config_cli.py
import click
from utils.config_validator import ConfigurationValidator
from utils.feature_manager import FeatureManager
from utils.retail_type_manager import RetailTypeManager

@app.cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command()
@click.option('--environment', default='development', help='Environment to validate')
def validate(environment):
    """Validate configuration for specific environment"""
    from flask import current_app
    
    with current_app.app_context():
        validator = ConfigurationValidator(current_app.config)
        result = validator.validate_all()
        
        if result['valid']:
            click.echo("✅ Configuration is valid")
        else:
            click.echo("❌ Configuration validation failed")
            for error in result['errors']:
                click.echo(f"  Error: {error}")
        
        if result['warnings']:
            click.echo("⚠️  Configuration warnings:")
            for warning in result['warnings']:
                click.echo(f"  Warning: {warning}")

@config.command()
@click.option('--tenant-id', required=True, help='Tenant ID')
@click.option('--retail-type', required=True, help='Retail type')
def apply_retail_type(tenant_id, retail_type):
    """Apply retail type configuration to tenant"""
    manager = RetailTypeManager()
    success, message = manager.apply_retail_type_defaults(tenant_id, retail_type)
    
    if success:
        click.echo(f"✅ {message}")
    else:
        click.echo(f"❌ {message}")

@config.command()
@click.option('--tenant-id', required=True, help='Tenant ID')
@click.option('--feature-name', required=True, help='Feature name')
@click.option('--enabled', type=bool, help='Enable/disable feature')
def toggle_feature(tenant_id, feature_name, enabled):
    """Toggle feature for tenant"""
    manager = FeatureManager(db)
    
    try:
        feature_flag = manager.update_feature_config(tenant_id, feature_name, enabled)
        click.echo(f"✅ Feature {feature_name} {'enabled' if enabled else 'disabled'} for tenant {tenant_id}")
    except Exception as e:
        click.echo(f"❌ Error updating feature: {str(e)}")

@config.command()
def list_features():
    """List all available features"""
    from models.feature_flag import FeatureDefinition
    
    features = FeatureDefinition.query.all()
    
    click.echo("Available Features:")
    for feature in features:
        status = "✅" if feature.default_value else "❌"
        click.echo(f"  {status} {feature.name} - {feature.description}")
        click.echo(f"      Category: {feature.category}")
        if feature.supported_retail_types:
            click.echo(f"      Supported: {', '.join(feature.supported_retail_types)}")
        click.echo()

@config.command()
@click.option('--retail-type', required=True, help='Retail type')
def list_retail_features(retail_type):
    """List features for specific retail type"""
    manager = RetailTypeManager()
    config = manager.get_retail_type_config(retail_type)
    
    if not config:
        click.echo(f"❌ Unknown retail type: {retail_type}")
        return
    
    click.echo(f"Features for {retail_type}:")
    
    click.echo("\nRequired Features:")
    for feature in config['features']['required']:
        click.echo(f"  ✅ {feature}")
    
    click.echo("\nOptional Features:")
    for feature in config['features']['optional']:
        click.echo(f"  ⚪ {feature}")
```

---

## Validation and Testing

### Configuration Testing

```python
# tests/test_configuration.py
import pytest
from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig

class TestConfiguration:
    def test_base_config(self):
        """Test base configuration"""
        config = Config()
        
        assert config.SECRET_KEY is not None
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False
        assert config.WTF_CSRF_ENABLED is True
        assert config.CURRENCY_SYMBOL == '₹'
    
    def test_development_config(self):
        """Test development configuration"""
        config = DevelopmentConfig()
        
        assert config.DEBUG is True
        assert config.SQLALCHEMY_ECHO is True
        assert config.MAIL_SUPPRESS_SEND is True
        assert config.CACHE_TYPE == 'simple'
    
    def test_production_config(self):
        """Test production configuration"""
        config = ProductionConfig()
        
        assert config.DEBUG is False
        assert config.SQLALCHEMY_ECHO is False
        assert config.SESSION_COOKIE_SECURE is True
        assert config.CACHE_TYPE == 'redis'
    
    def test_testing_config(self):
        """Test testing configuration"""
        config = TestingConfig()
        
        assert config.TESTING is True
        assert config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
        assert config.WTF_CSRF_ENABLED is False
        assert config.CACHE_TYPE == 'null'
    
    def test_feature_flags(self):
        """Test feature flag configuration"""
        config = DevelopmentConfig()
        
        assert hasattr(config, 'FEATURE_SALES_PROCESSING')
        assert hasattr(config, 'FEATURE_PRODUCT_CATALOG')
        assert hasattr(config, 'FEATURE_CRM_LOYALTY')
    
    def test_security_configuration(self):
        """Test security configuration"""
        config = ProductionConfig()
        
        assert config.FORCE_HTTPS is True
        assert config.SECURITY_HEADERS_ENABLED is True
        assert config.SESSION_COOKIE_SECURE is True
        assert config.SESSION_COOKIE_HTTPONLY is True

class TestConfigurationValidator:
    def test_valid_configuration(self):
        """Test validation of valid configuration"""
        config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key-that-is-long-enough',
            'FEATURE_SALES_PROCESSING': True,
            'FEATURE_PRODUCT_CATALOG': True,
            'MULTI_TENANT': False
        }
        
        validator = ConfigurationValidator(config)
        result = validator.validate_all()
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    def test_invalid_configuration(self):
        """Test validation of invalid configuration"""
        config = {
            'SECRET_KEY': 'short',
            'FEATURE_SALES_PROCESSING': False,
            'MULTI_TENANT': True
        }
        
        validator = ConfigurationValidator(config)
        result = validator.validate_all()
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_configuration_warnings(self):
        """Test configuration warnings"""
        config = {
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db',
            'SECRET_KEY': 'test-secret-key',
            'FEATURE_SALES_PROCESSING': True,
            'FEATURE_PRODUCT_CATALOG': True,
            'MULTI_TENANT': False,
            'SESSION_TIMEOUT': 60  # Too short
        }
        
        validator = ConfigurationValidator(config)
        result = validator.validate_all()
        
        assert len(result['warnings']) > 0

class TestRetailTypeConfiguration:
    def test_restaurant_config(self):
        """Test restaurant configuration"""
        manager = RetailTypeManager()
        config = manager.get_retail_type_config('restaurant')
        
        assert config is not None
        assert 'FEATURE_TABLE_MANAGEMENT' in config['features']['required']
        assert 'dine_in' in config['workflows']
        assert config['settings']['service_charge_enabled'] is True
    
    def test_apparel_config(self):
        """Test apparel configuration"""
        manager = RetailTypeManager()
        config = manager.get_retail_type_config('apparel')
        
        assert config is not None
        assert 'FEATURE_SIZE_VARIANTS' in config['features']['required']
        assert 'exchange' in config['workflows']
        assert config['product_attributes']['size_variants']['enabled'] is True
    
    def test_grocery_config(self):
        """Test grocery configuration"""
        manager = RetailTypeManager()
        config = manager.get_retail_type_config('grocery')
        
        assert config is not None
        assert 'FEATURE_WEIGHING_SCALE' in config['features']['required']
        assert 'counter_sale' in config['workflows']
        assert config['product_attributes']['expiry_tracking']['enabled'] is True
    
    def test_feature_validation(self):
        """Test feature validation for retail types"""
        manager = RetailTypeManager()
        
        # Valid features for restaurant
        valid, message = manager.validate_retail_type_features(
            'restaurant',
            ['FEATURE_SALES_PROCESSING', 'FEATURE_TABLE_MANAGEMENT', 'FEATURE_KOT_PRINTING']
        )
        assert valid is True
        
        # Invalid features for restaurant (missing required)
        valid, message = manager.validate_retail_type_features(
            'restaurant',
            ['FEATURE_SALES_PROCESSING']  # Missing table management
        )
        assert valid is False
```

---

**Version**: 1.0.0 Comprehensive Configuration Guide  
**Last Updated**: December 2024  
**Documentation**: Flask POS Development Team