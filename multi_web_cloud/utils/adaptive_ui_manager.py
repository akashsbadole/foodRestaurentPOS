"""
Adaptive UI Manager
Main integration point for all adaptive UI/UX systems
"""

from typing import Dict, List, Optional, Any, Set
from flask import current_app, request, g
from utils.feature_flag_manager import feature_manager
from utils.template_engine import get_template_engine
from utils.adaptive_navigation import get_navigation_manager
from utils.dynamic_forms import get_form_manager
from utils.dynamic_dashboard import get_dashboard_manager
from utils.adaptive_components import get_component_manager
from utils.mobile_optimization import get_mobile_manager
from utils.accessibility import get_accessibility_manager
from utils.performance_optimization import get_performance_optimizer
from utils.user_experience import get_ux_manager


class AdaptiveUIManager:
    """
    Main manager for all adaptive UI/UX systems
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.template_engine = None
        self.navigation_manager = None
        self.form_manager = None
        self.dashboard_manager = None
        self.component_manager = None
        self.mobile_manager = None
        self.accessibility_manager = None
        self.performance_optimizer = None
        self.ux_manager = None
        self._initialized = False
    
    def initialize(self):
        """Initialize all adaptive UI systems"""
        if self._initialized:
            return
        
        # Initialize all managers
        self.template_engine = get_template_engine(current_app)
        self.navigation_manager = get_navigation_manager(self.feature_manager)
        self.form_manager = get_form_manager(self.feature_manager)
        self.dashboard_manager = get_dashboard_manager(self.feature_manager)
        self.component_manager = get_component_manager(self.feature_manager)
        self.mobile_manager = get_mobile_manager(self.feature_manager)
        self.accessibility_manager = get_accessibility_manager(self.feature_manager)
        self.performance_optimizer = get_performance_optimizer(self.feature_manager)
        self.ux_manager = get_ux_manager(self.feature_manager)
        
        # Initialize each manager
        self.template_engine.initialize()
        self.navigation_manager.initialize()
        self.form_manager.initialize()
        self.dashboard_manager.initialize()
        self.component_manager.initialize()
        self.mobile_manager.initialize()
        self.accessibility_manager.initialize()
        self.performance_optimizer.initialize()
        self.ux_manager.initialize()
        
        self._initialized = True
    
    def get_adaptive_config(self, tenant_id: Optional[str] = None, 
                            user_id: Optional[str] = None, 
                            request_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Get complete adaptive configuration for current context
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        # Get basic context
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get user agent and device info
        user_agent = request.headers.get('User-Agent', '') if request else ''
        request_context = request_context or self._get_request_context()
        
        # Get configurations from all managers
        template_config = self._get_template_config(tenant_id, enabled_features, retail_type)
        navigation_config = self.navigation_manager.get_navigation_menu('main', tenant_id)
        mobile_config = self.mobile_manager.get_mobile_config(tenant_id, user_agent)
        accessibility_config = self.accessibility_manager.get_accessibility_config(tenant_id, request_context.get('user_preferences'))
        performance_config = self.performance_optimizer.get_optimization_config(tenant_id, user_agent)
        ux_config = self.ux_manager.get_ux_config(tenant_id, user_id, request_context)
        
        # Get forms and components
        available_forms = self._get_available_forms(tenant_id, enabled_features, retail_type)
        available_components = self.component_manager.get_components_for_tenant(tenant_id)
        dashboard_config = self.dashboard_manager.get_dashboard(None, tenant_id)
        
        # Combine all configurations
        adaptive_config = {
            'tenant_id': tenant_id,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'request_context': request_context,
            'template': template_config,
            'navigation': navigation_config,
            'mobile': mobile_config,
            'accessibility': accessibility_config,
            'performance': performance_config,
            'ux': ux_config,
            'forms': available_forms,
            'components': available_components,
            'dashboard': dashboard_config,
            'css_classes': self._generate_css_classes(tenant_id, enabled_features, retail_type, request_context),
            'javascript_config': self._generate_javascript_config(tenant_id, enabled_features, retail_type, request_context),
            'meta_tags': self._generate_meta_tags(tenant_id, enabled_features, retail_type, request_context)
        }
        
        return adaptive_config
    
    def render_adaptive_template(self, template_name: str, **context) -> str:
        """
        Render template with adaptive features
        """
        if not self._initialized:
            self.initialize()
        
        # Add adaptive context to template context
        adaptive_config = self.get_adaptive_config()
        context['adaptive_config'] = adaptive_config
        
        # Render using adaptive template engine
        return self.template_engine.render_template(template_name, **context)
    
    def get_adaptive_navigation(self, menu_type: str = 'main', tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get adaptive navigation configuration
        """
        if not self._initialized:
            self.initialize()
        
        return self.navigation_manager.get_navigation_menu(menu_type, tenant_id)
    
    def get_adaptive_form(self, form_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get adaptive form configuration
        """
        if not self._initialized:
            self.initialize()
        
        return self.form_manager.get_form(form_id, tenant_id)
    
    def get_adaptive_dashboard(self, layout_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get adaptive dashboard configuration
        """
        if not self._initialized:
            self.initialize()
        
        return self.dashboard_manager.get_dashboard(layout_id, tenant_id)
    
    def validate_form_data(self, form_id: str, form_data, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate form data with adaptive rules
        """
        if not self._initialized:
            self.initialize()
        
        return self.form_manager.validate_form_data(form_id, form_data, tenant_id)
    
    def get_accessibility_validation(self, html_content: str, wcag_level: str = 'AA') -> Dict[str, Any]:
        """
        Validate content for accessibility compliance
        """
        if not self._initialized:
            self.initialize()
        
        return self.accessibility_manager.validate_accessibility(html_content, wcag_level)
    
    def track_user_interaction(self, event_name: str, event_data: Dict[str, Any], 
                           user_id: Optional[str] = None):
        """
        Track user interaction for analytics and personalization
        """
        if not self._initialized:
            self.initialize()
        
        # Track in UX manager
        self.ux_manager.track_analytics_event(event_name, event_data)
        
        # Track in performance optimizer
        self.performance_optimizer.record_performance_metric(f'user_{event_name}', 1, event_data)
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        Update user preferences
        """
        if not self._initialized:
            self.initialize()
        
        # This would typically save to database
        # For now, just track the change
        self.ux_manager.track_analytics_event('preferences_updated', {
            'user_id': user_id,
            'preferences': preferences
        })
    
    def get_theme_css(self, theme_name: Optional[str] = None, tenant_id: Optional[str] = None) -> str:
        """
        Get theme CSS classes
        """
        if not self._initialized:
            self.initialize()
        
        return self.template_engine.theme_manager.get_theme_classes(theme_name, tenant_id)
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Get request context information"""
        return {
            'path': request.path if request else '/',
            'method': request.method if request else 'GET',
            'user_agent': request.headers.get('User-Agent', '') if request else '',
            'is_ajax': request.is_xhr if request else False,
            'is_mobile': self._is_mobile_request(),
            'user_preferences': session.get('user_preferences', {}),
            'current_page': self._get_current_page(),
            'referrer': request.referrer if request else None
        }
    
    def _is_mobile_request(self) -> bool:
        """Check if request is from mobile device"""
        user_agent = request.headers.get('User-Agent', '').lower() if request else ''
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipad', 'tablet']
        return any(indicator in user_agent for indicator in mobile_indicators)
    
    def _get_current_page(self) -> str:
        """Get current page identifier"""
        if not request:
            return 'unknown'
        
        # Map URL paths to page identifiers
        path_mappings = {
            '/': 'dashboard',
            '/dashboard': 'dashboard',
            '/orders/new': 'new_order',
            '/orders': 'order_list',
            '/menu': 'menu_management',
            '/tables': 'table_management',
            '/inventory': 'inventory_management',
            '/reports': 'reports',
            '/settings': 'settings'
        }
        
        return path_mappings.get(request.path, 'unknown')
    
    def _get_template_config(self, tenant_id: Optional[str], enabled_features: Set[str], 
                           retail_type: str) -> Dict[str, Any]:
        """Get template configuration"""
        return {
            'engine': 'adaptive',
            'features': {
                'feature_aware_rendering': True,
                'retail_type_adaptation': True,
                'dynamic_component_loading': True,
                'conditional_display': True
            },
            'helpers': {
                'feature_enabled': True,
                'retail_type_is': True,
                'get_enabled_features': True,
                'get_retail_config': True,
                'render_component': True,
                'render_adaptive_menu': True,
                'render_dynamic_form': True,
                'render_dashboard_widget': True,
                'get_theme': True,
                'get_theme_css': True
            }
        }
    
    def _get_available_forms(self, tenant_id: Optional[str], enabled_features: Set[str], 
                           retail_type: str) -> List[str]:
        """Get available forms for current context"""
        available_forms = []
        
        # Common forms
        common_forms = ['order_form', 'product_form', 'customer_form']
        
        # Retail-specific forms
        retail_forms = {
            'restaurant': ['table_reservation_form', 'kot_form'],
            'retail': ['quick_sale_form', 'return_form'],
            'apparel': ['exchange_form', 'alteration_form'],
            'grocery': ['weighing_form', 'expiry_form']
        }
        
        all_forms = common_forms + retail_forms.get(retail_type, [])
        
        for form_id in all_forms:
            form_config = self.form_manager.get_form(form_id, tenant_id)
            if form_config:
                available_forms.append(form_id)
        
        return available_forms
    
    def _generate_css_classes(self, tenant_id: Optional[str], enabled_features: Set[str], 
                           retail_type: str, request_context: Dict[str, Any]) -> List[str]:
        """Generate CSS classes based on context"""
        css_classes = []
        
        # Retail type classes
        css_classes.append(f'retail-type-{retail_type}')
        
        # Feature classes
        for feature in enabled_features:
            css_classes.append(f'feature-{feature.lower()}')
        
        # Device classes
        if request_context.get('is_mobile'):
            css_classes.append('mobile-device')
        else:
            css_classes.append('desktop-device')
        
        # Theme classes
        theme = request_context.get('user_preferences', {}).get('theme', 'default')
        css_classes.append(f'theme-{theme}')
        
        # Accessibility classes
        accessibility_prefs = request_context.get('user_preferences', {})
        if accessibility_prefs.get('high_contrast'):
            css_classes.append('high-contrast')
        if accessibility_prefs.get('large_text'):
            css_classes.append('large-text')
        
        # Performance classes
        css_classes.append('adaptive-ui')
        css_classes.append('feature-aware')
        
        return css_classes
    
    def _generate_javascript_config(self, tenant_id: Optional[str], enabled_features: Set[str], 
                                retail_type: str, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate JavaScript configuration"""
        return {
            'adaptive_ui': {
                'enabled': True,
                'retail_type': retail_type,
                'enabled_features': list(enabled_features),
                'is_mobile': request_context.get('is_mobile', False),
                'user_preferences': request_context.get('user_preferences', {}),
                'theme': request_context.get('user_preferences', {}).get('theme', 'default')
            },
            'components': self.component_manager.get_components_for_tenant(tenant_id),
            'performance': {
                'lazy_loading': True,
                'component_caching': True,
                'asset_bundling': True
            },
            'accessibility': {
                'screen_reader_support': True,
                'keyboard_navigation': True,
                'high_contrast': request_context.get('user_preferences', {}).get('high_contrast', False)
            },
            'mobile': {
                'touch_optimized': request_context.get('is_mobile', False),
                'gesture_support': True,
                'responsive_layout': True
            }
        }
    
    def _generate_meta_tags(self, tenant_id: Optional[str], enabled_features: Set[str], 
                          retail_type: str, request_context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate meta tags for adaptive UI"""
        meta_tags = []
        
        # Basic meta tags
        meta_tags.extend([
            {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'},
            {'name': 'description', 'content': f'Adaptive {retail_type} POS System'},
            {'name': 'theme-color', 'content': '#3498db'}
        ])
        
        # Retail type specific meta tags
        if retail_type == 'restaurant':
            meta_tags.append({'name': 'application-name', 'content': 'Restaurant POS'})
        elif retail_type == 'retail':
            meta_tags.append({'name': 'application-name', 'content': 'Retail POS'})
        elif retail_type == 'apparel':
            meta_tags.append({'name': 'application-name', 'content': 'Apparel POS'})
        elif retail_type == 'grocery':
            meta_tags.append({'name': 'application-name', 'content': 'Grocery POS'})
        
        # Mobile optimization meta tags
        if request_context.get('is_mobile'):
            meta_tags.extend([
                {'name': 'mobile-web-app-capable', 'content': 'yes'},
                {'name': 'apple-mobile-web-app-capable', 'content': 'yes'},
                {'name': 'format-detection', 'content': 'telephone=no'}
            ])
        
        # Accessibility meta tags
        meta_tags.append({'name': 'accessibility', 'content': 'WCAG-AA compliant'})
        
        return meta_tags


# Global adaptive UI manager instance
adaptive_ui_manager = None


def get_adaptive_ui_manager(feature_manager=None) -> AdaptiveUIManager:
    """Get or create global adaptive UI manager instance"""
    global adaptive_ui_manager
    if adaptive_ui_manager is None:
        adaptive_ui_manager = AdaptiveUIManager(feature_manager)
    return adaptive_ui_manager