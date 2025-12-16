"""
Dynamic Template Engine with Feature-Aware Rendering
Provides adaptive templates based on enabled features and retail types
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import current_app, g, request, session
from jinja2 import Environment, BaseLoader, TemplateNotFound
from functools import wraps
import json
import os
from utils.feature_flag_manager import feature_manager
from utils.retail_type_manager import get_retail_type_manager


class FeatureAwareTemplateLoader(BaseLoader):
    """
    Custom template loader that supports feature-aware template resolution
    """
    
    def __init__(self, app, searchpath="templates"):
        super().__init__()
        self.app = app
        self.searchpath = searchpath
        self.template_cache = {}
        
    def get_source(self, environment, template):
        """
        Get template source with feature-aware resolution
        Priority: feature-specific -> retail-type -> base template
        """
        # Get current context
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Try feature-specific templates first
        for feature in enabled_features:
            feature_template = self._resolve_feature_template(template, feature, retail_type)
            if feature_template:
                return self._load_template_file(feature_template)
        
        # Try retail-type specific templates
        retail_template = self._resolve_retail_template(template, retail_type)
        if retail_template:
            return self._load_template_file(retail_template)
        
        # Fall back to base template
        return self._load_template_file(template)
    
    def _get_tenant_id(self):
        """Get current tenant ID from context"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def _resolve_feature_template(self, template: str, feature: str, retail_type: str) -> Optional[str]:
        """
        Resolve feature-specific template path
        Examples:
        - orders/new.html -> features/FEATURE_ORDERS/orders/new.html
        - features/FEATURE_ORDERS/orders/new_retail.html
        """
        # Clean feature name
        clean_feature = feature.replace('FEATURE_', '').lower()
        
        # Try different template patterns
        patterns = [
            f"features/{feature}/{template}",
            f"features/{clean_feature}/{template}",
            f"features/{feature}/{retail_type}/{template}",
            f"features/{clean_feature}/{retail_type}/{template}",
            f"{template.rsplit('.', 1)[0]}.{clean_feature}.html",  # orders.new.html -> orders.new.orders.html
            f"{template.rsplit('.', 1)[0]}.{clean_feature}_{retail_type}.html"
        ]
        
        for pattern in patterns:
            if self._template_exists(pattern):
                return pattern
        
        return None
    
    def _resolve_retail_template(self, template: str, retail_type: str) -> Optional[str]:
        """
        Resolve retail-type specific template path
        Examples:
        - orders/new.html -> retail/restaurant/orders/new.html
        - orders/new_retail.html
        """
        patterns = [
            f"retail/{retail_type}/{template}",
            f"{template.rsplit('.', 1)[0]}.{retail_type}.html"
        ]
        
        for pattern in patterns:
            if self._template_exists(pattern):
                return pattern
        
        return None
    
    def _template_exists(self, template_path: str) -> bool:
        """Check if template file exists"""
        try:
            full_path = os.path.join(self.searchpath, template_path)
            return os.path.exists(full_path)
        except:
            return False
    
    def _load_template_file(self, template_path: str):
        """Load template file and return source info"""
        full_path = os.path.join(self.searchpath, template_path)
        
        if not os.path.exists(full_path):
            raise TemplateNotFound(template_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Get modification time for caching
        mtime = os.path.getmtime(full_path)
        
        def uptodate():
            try:
                return os.path.getmtime(full_path) == mtime
            except:
                return False
        
        return source, full_path, uptodate


class DynamicTemplateEngine:
    """
    Dynamic template engine with feature-aware rendering capabilities
    """
    
    def __init__(self, app=None):
        self.app = app
        self.template_functions = {}
        self.template_filters = {}
        self.template_globals = {}
        self.component_registry = {}
        self.theme_manager = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize template engine with Flask app"""
        self.app = app
        
        # Create custom Jinja2 environment
        self.jinja_env = Environment(
            loader=FeatureAwareTemplateLoader(app),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom functions and filters
        self._register_template_helpers()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(app)
        
        # Register with app context
        app.context_processor(self._inject_template_context)
    
    def _register_template_helpers(self):
        """Register custom template functions and filters"""
        
        # Feature checking functions
        self.jinja_env.globals['feature_enabled'] = self._feature_enabled_helper
        self.jinja_env.globals['retail_type_is'] = self._retail_type_helper
        self.jinja_env.globals['get_enabled_features'] = self._get_enabled_features_helper
        self.jinja_env.globals['get_retail_config'] = self._get_retail_config_helper
        
        # Component rendering functions
        self.jinja_env.globals['render_component'] = self._render_component_helper
        self.jinja_env.globals['render_adaptive_menu'] = self._render_adaptive_menu_helper
        self.jinja_env.globals['render_dynamic_form'] = self._render_dynamic_form_helper
        self.jinja_env.globals['render_dashboard_widget'] = self._render_dashboard_widget_helper
        
        # Theme functions
        self.jinja_env.globals['get_theme'] = self._get_theme_helper
        self.jinja_env.globals['get_theme_css'] = self._get_theme_css_helper
        
        # Utility functions
        self.jinja_env.globals['get_component_config'] = self._get_component_config_helper
        self.jinja_env.globals['get_workflow_config'] = self._get_workflow_config_helper
        
        # Filters
        self.jinja_env.filters['feature_enabled'] = self._feature_enabled_filter
        self.jinja_env.filters['retail_type_is'] = self._retail_type_filter
        self.jinja_env.filters['adapt_text'] = self._adapt_text_filter
        self.jinja_env.filters['theme_color'] = self._theme_color_filter
    
    def _inject_template_context(self):
        """Inject global context into templates"""
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        return {
            'ui_context': {
                'tenant_id': tenant_id,
                'retail_type': retail_type,
                'enabled_features': list(enabled_features),
                'feature_count': len(enabled_features),
                'is_mobile': self._is_mobile_request(),
                'theme': self.theme_manager.get_current_theme(tenant_id) if self.theme_manager else None
            }
        }
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def _is_mobile_request(self) -> bool:
        """Check if request is from mobile device"""
        user_agent = request.headers.get('User-Agent', '').lower()
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        return any(indicator in user_agent for indicator in mobile_indicators)
    
    # Template Helper Functions
    def _feature_enabled_helper(self, feature_name: str, tenant_id: Optional[str] = None) -> bool:
        """Check if feature is enabled"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        return feature_manager.is_enabled(feature_name, tenant_id)
    
    def _retail_type_helper(self, retail_type: str, tenant_id: Optional[str] = None) -> bool:
        """Check if current retail type matches"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        current_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        return current_type == retail_type
    
    def _get_enabled_features_helper(self, tenant_id: Optional[str] = None) -> Set[str]:
        """Get all enabled features"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        return feature_manager.get_enabled_features(tenant_id)
    
    def _get_retail_config_helper(self, retail_type: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get retail type configuration"""
        if retail_type is None:
            retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        
        retail_manager = get_retail_type_manager(feature_manager)
        return retail_manager.get_retail_type_config(retail_type) or {}
    
    # Component Rendering Helpers
    def _render_component_helper(self, component_name: str, **kwargs) -> str:
        """Render adaptive component based on features"""
        return self.render_component(component_name, **kwargs)
    
    def _render_adaptive_menu_helper(self, menu_type: str = 'main', **kwargs) -> str:
        """Render adaptive navigation menu"""
        return self.render_adaptive_menu(menu_type, **kwargs)
    
    def _render_dynamic_form_helper(self, form_name: str, **kwargs) -> str:
        """Render dynamic form with conditional fields"""
        return self.render_dynamic_form(form_name, **kwargs)
    
    def _render_dashboard_widget_helper(self, widget_name: str, **kwargs) -> str:
        """Render dashboard widget based on features"""
        return self.render_dashboard_widget(widget_name, **kwargs)
    
    # Theme Helpers
    def _get_theme_helper(self, theme_name: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get theme configuration"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        return self.theme_manager.get_theme(theme_name, tenant_id) if self.theme_manager else {}
    
    def _get_theme_css_helper(self, theme_name: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """Get theme CSS classes"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        return self.theme_manager.get_theme_classes(theme_name, tenant_id) if self.theme_manager else ''
    
    # Utility Helpers
    def _get_component_config_helper(self, component_name: str, **kwargs) -> Dict[str, Any]:
        """Get component configuration"""
        return self.get_component_config(component_name, **kwargs)
    
    def _get_workflow_config_helper(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """Get workflow configuration"""
        return self.get_workflow_config(workflow_name, **kwargs)
    
    # Filters
    def _feature_enabled_filter(self, feature_name: str, tenant_id: Optional[str] = None) -> bool:
        """Filter to check if feature is enabled"""
        return self._feature_enabled_helper(feature_name, tenant_id)
    
    def _retail_type_filter(self, retail_type: str, tenant_id: Optional[str] = None) -> bool:
        """Filter to check retail type"""
        return self._retail_type_helper(retail_type, tenant_id)
    
    def _adapt_text_filter(self, text: str, retail_type: Optional[str] = None) -> str:
        """Adapt text based on retail type"""
        if retail_type is None:
            tenant_id = self._get_tenant_id()
            retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        
        # Apply retail-type specific text adaptations
        adaptations = {
            'restaurant': {
                'product': 'menu item',
                'customer': 'guest',
                'sale': 'order',
                'inventory': 'stock'
            },
            'retail': {
                'product': 'product',
                'customer': 'customer',
                'sale': 'sale',
                'inventory': 'inventory'
            },
            'apparel': {
                'product': 'garment',
                'customer': 'customer',
                'sale': 'purchase',
                'inventory': 'stock'
            },
            'grocery': {
                'product': 'item',
                'customer': 'shopper',
                'sale': 'purchase',
                'inventory': 'stock'
            }
        }
        
        if retail_type in adaptations:
            for generic, specific in adaptations[retail_type].items():
                text = text.replace(generic, specific)
        
        return text
    
    def _theme_color_filter(self, color_name: str, theme_name: Optional[str] = None) -> str:
        """Get theme color value"""
        if self.theme_manager:
            return self.theme_manager.get_color(color_name, theme_name)
        return color_name
    
    def render_template(self, template_name: str, **context) -> str:
        """Render template with feature-aware resolution"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            # Fall back to default template rendering
            return self.app.jinja_env.get_template(template_name).render(**context)
    
    def render_component(self, component_name: str, **kwargs) -> str:
        """Render adaptive component"""
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get component configuration
        component_config = self.get_component_config(component_name, retail_type, enabled_features)
        
        # Determine template to use
        template_name = component_config.get('template', f'components/{component_name}.html')
        
        # Add component context
        context = {
            'component_name': component_name,
            'component_config': component_config,
            'retail_type': retail_type,
            'enabled_features': enabled_features,
            **kwargs
        }
        
        return self.render_template(template_name, **context)
    
    def render_adaptive_menu(self, menu_type: str = 'main', **kwargs) -> str:
        """Render adaptive navigation menu"""
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get menu configuration
        menu_config = self.get_menu_config(menu_type, retail_type, enabled_features)
        
        # Filter menu items based on features and permissions
        filtered_items = self._filter_menu_items(menu_config.get('items', []), enabled_features)
        
        context = {
            'menu_type': menu_type,
            'menu_items': filtered_items,
            'menu_config': menu_config,
            'retail_type': retail_type,
            'enabled_features': enabled_features,
            **kwargs
        }
        
        template_name = menu_config.get('template', f'navigation/{menu_type}_menu.html')
        return self.render_template(template_name, **context)
    
    def render_dynamic_form(self, form_name: str, **kwargs) -> str:
        """Render dynamic form with conditional fields"""
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get form configuration
        form_config = self.get_form_config(form_name, retail_type, enabled_features)
        
        # Filter fields based on features
        filtered_fields = self._filter_form_fields(form_config.get('fields', []), enabled_features)
        
        context = {
            'form_name': form_name,
            'form_fields': filtered_fields,
            'form_config': form_config,
            'retail_type': retail_type,
            'enabled_features': enabled_features,
            **kwargs
        }
        
        template_name = form_config.get('template', f'forms/{form_name}.html')
        return self.render_template(template_name, **context)
    
    def render_dashboard_widget(self, widget_name: str, **kwargs) -> str:
        """Render dashboard widget based on features"""
        tenant_id = self._get_tenant_id()
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get widget configuration
        widget_config = self.get_widget_config(widget_name, retail_type, enabled_features)
        
        context = {
            'widget_name': widget_name,
            'widget_config': widget_config,
            'retail_type': retail_type,
            'enabled_features': enabled_features,
            **kwargs
        }
        
        template_name = widget_config.get('template', f'dashboard/widgets/{widget_name}.html')
        return self.render_template(template_name, **context)
    
    def get_component_config(self, component_name: str, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Get component configuration based on retail type and features"""
        # Check for component-specific configuration
        if component_name in self.component_registry:
            config = self.component_registry[component_name]
            
            # Apply retail-type specific overrides
            if retail_type in config.get('retail_overrides', {}):
                config.update(config['retail_overrides'][retail_type])
            
            # Apply feature-specific overrides
            for feature in enabled_features:
                if feature in config.get('feature_overrides', {}):
                    config.update(config['feature_overrides'][feature])
            
            return config
        
        # Default component configuration
        return {
            'template': f'components/{component_name}.html',
            'enabled': True,
            'retail_overrides': {},
            'feature_overrides': {}
        }
    
    def get_menu_config(self, menu_type: str, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Get menu configuration based on retail type and features"""
        # Default menu configurations
        menu_configs = {
            'main': {
                'template': 'navigation/main_menu.html',
                'items': self._get_main_menu_items(retail_type, enabled_features)
            },
            'sidebar': {
                'template': 'navigation/sidebar_menu.html',
                'items': self._get_sidebar_menu_items(retail_type, enabled_features)
            },
            'top': {
                'template': 'navigation/top_menu.html',
                'items': self._get_top_menu_items(retail_type, enabled_features)
            }
        }
        
        return menu_configs.get(menu_type, menu_configs['main'])
    
    def get_form_config(self, form_name: str, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Get form configuration based on retail type and features"""
        # This would be expanded with specific form configurations
        return {
            'template': f'forms/{form_name}.html',
            'fields': [],
            'validation': {},
            'retail_overrides': {},
            'feature_overrides': {}
        }
    
    def get_widget_config(self, widget_name: str, retail_type: str, enabled_features: Set[str]) -> Dict[str, Any]:
        """Get widget configuration based on retail type and features"""
        # This would be expanded with specific widget configurations
        return {
            'template': f'dashboard/widgets/{widget_name}.html',
            'enabled': True,
            'retail_overrides': {},
            'feature_overrides': {}
        }
    
    def get_workflow_config(self, workflow_name: str, **kwargs) -> Dict[str, Any]:
        """Get workflow configuration"""
        retail_manager = get_retail_type_manager(feature_manager)
        return retail_manager.get_workflow_details(workflow_name) or {}
    
    def _filter_menu_items(self, items: List[Dict], enabled_features: Set[str]) -> List[Dict]:
        """Filter menu items based on enabled features"""
        filtered_items = []
        
        for item in items:
            # Check if item requires specific features
            required_features = item.get('required_features', [])
            if required_features and not all(feature in enabled_features for feature in required_features):
                continue
            
            # Check if item is excluded by features
            excluded_features = item.get('excluded_features', [])
            if any(feature in enabled_features for feature in excluded_features):
                continue
            
            # Recursively filter sub-items
            if 'items' in item:
                item['items'] = self._filter_menu_items(item['items'], enabled_features)
            
            filtered_items.append(item)
        
        return filtered_items
    
    def _filter_form_fields(self, fields: List[Dict], enabled_features: Set[str]) -> List[Dict]:
        """Filter form fields based on enabled features"""
        filtered_fields = []
        
        for field in fields:
            # Check if field requires specific features
            required_features = field.get('required_features', [])
            if required_features and not all(feature in enabled_features for feature in required_features):
                continue
            
            # Check if field is excluded by features
            excluded_features = field.get('excluded_features', [])
            if any(feature in enabled_features for feature in excluded_features):
                continue
            
            filtered_fields.append(field)
        
        return filtered_fields
    
    def _get_main_menu_items(self, retail_type: str, enabled_features: Set[str]) -> List[Dict]:
        """Get main menu items based on retail type and features"""
        items = [
            {
                'name': 'dashboard',
                'title': 'Dashboard',
                'icon': 'bi-house',
                'url': url_for('dashboard.index'),
                'order': 1
            },
            {
                'name': 'orders',
                'title': 'Orders',
                'icon': 'bi-cart-plus',
                'url': url_for('orders.new_order'),
                'order': 2,
                'required_features': ['FEATURE_SALES_PROCESSING']
            }
        ]
        
        # Add retail-type specific items
        if retail_type == 'restaurant':
            items.extend([
                {
                    'name': 'tables',
                    'title': 'Tables',
                    'icon': 'bi-grid-3x3-gap',
                    'url': url_for('tables.index'),
                    'order': 3,
                    'required_features': ['FEATURE_TABLE_MANAGEMENT']
                },
                {
                    'name': 'kot',
                    'title': 'Kitchen Display',
                    'icon': 'bi-clipboard-check',
                    'url': url_for('kot.index'),
                    'order': 4,
                    'required_features': ['FEATURE_KITCHEN_DISPLAY']
                }
            ])
        
        # Add feature-specific items
        if 'FEATURE_INVENTORY_BASIC' in enabled_features:
            items.append({
                'name': 'inventory',
                'title': 'Inventory',
                'icon': 'bi-box-seam',
                'url': url_for('inventory.index'),
                'order': 10
            })
        
        return sorted(items, key=lambda x: x['order'])
    
    def _get_sidebar_menu_items(self, retail_type: str, enabled_features: Set[str]) -> List[Dict]:
        """Get sidebar menu items"""
        return self._get_main_menu_items(retail_type, enabled_features)
    
    def _get_top_menu_items(self, retail_type: str, enabled_features: Set[str]) -> List[Dict]:
        """Get top menu items"""
        return self._get_main_menu_items(retail_type, enabled_features)
    
    def register_component(self, name: str, config: Dict[str, Any]):
        """Register a component configuration"""
        self.component_registry[name] = config


class ThemeManager:
    """
    Manage retail-type specific themes and styling
    """
    
    def __init__(self, app=None):
        self.app = app
        self.themes = {}
        self.current_themes = {}  # tenant_id -> theme_name
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize theme manager"""
        self.app = app
        self._load_default_themes()
    
    def _load_default_themes(self):
        """Load default themes for different retail types"""
        self.themes = {
            'restaurant': {
                'name': 'Restaurant',
                'primary_color': '#2c3e50',
                'secondary_color': '#e74c3c',
                'accent_color': '#f39c12',
                'background_color': '#ecf0f1',
                'text_color': '#2c3e50',
                'font_family': 'Inter, sans-serif',
                'border_radius': '8px',
                'css_classes': 'theme-restaurant'
            },
            'retail': {
                'name': 'Retail',
                'primary_color': '#3498db',
                'secondary_color': '#2980b9',
                'accent_color': '#e67e22',
                'background_color': '#f8f9fa',
                'text_color': '#2c3e50',
                'font_family': 'Roboto, sans-serif',
                'border_radius': '4px',
                'css_classes': 'theme-retail'
            },
            'apparel': {
                'name': 'Apparel & Footwear',
                'primary_color': '#9b59b6',
                'secondary_color': '#8e44ad',
                'accent_color': '#e74c3c',
                'background_color': '#fdfdfd',
                'text_color': '#2c3e50',
                'font_family': 'Poppins, sans-serif',
                'border_radius': '12px',
                'css_classes': 'theme-apparel'
            },
            'grocery': {
                'name': 'Grocery & Supermarket',
                'primary_color': '#27ae60',
                'secondary_color': '#229954',
                'accent_color': '#f39c12',
                'background_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_family': 'Roboto, sans-serif',
                'border_radius': '6px',
                'css_classes': 'theme-grocery'
            }
        }
    
    def get_theme(self, theme_name: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get theme configuration"""
        if theme_name is None:
            theme_name = self.get_current_theme(tenant_id)
        
        return self.themes.get(theme_name, self.themes['restaurant'])
    
    def get_current_theme(self, tenant_id: Optional[str] = None) -> str:
        """Get current theme for tenant"""
        if tenant_id and tenant_id in self.current_themes:
            return self.current_themes[tenant_id]
        
        # Default to retail type theme
        if tenant_id:
            retail_type = feature_manager.get_tenant_retail_type(tenant_id)
            return retail_type if retail_type in self.themes else 'restaurant'
        
        return 'restaurant'
    
    def set_theme(self, theme_name: str, tenant_id: str):
        """Set theme for tenant"""
        if theme_name in self.themes:
            self.current_themes[tenant_id] = theme_name
    
    def get_theme_classes(self, theme_name: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """Get CSS classes for theme"""
        theme = self.get_theme(theme_name, tenant_id)
        return theme.get('css_classes', '')
    
    def get_color(self, color_name: str, theme_name: Optional[str] = None) -> str:
        """Get color value from theme"""
        theme = self.get_theme(theme_name)
        return theme.get(color_name, color_name)


# Global template engine instance
template_engine = None


def get_template_engine(app=None) -> DynamicTemplateEngine:
    """Get or create global template engine instance"""
    global template_engine
    if template_engine is None:
        template_engine = DynamicTemplateEngine(app)
    return template_engine