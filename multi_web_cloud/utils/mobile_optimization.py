"""
Mobile Optimization for Different Retail Types
Provides mobile-optimized interfaces and touch-friendly components
"""

from typing import Dict, List, Optional, Any, Set
from flask import request, current_app
from utils.feature_flag_manager import feature_manager


class MobileLayout:
    """
    Represents a mobile layout configuration
    """
    
    def __init__(self, layout_id: str, **kwargs):
        self.layout_id = layout_id
        self.name = kwargs.get('name', layout_id.title())
        self.description = kwargs.get('description', '')
        self.retail_types = kwargs.get('retail_types', [])
        self.required_features = kwargs.get('required_features', [])
        self.screen_sizes = kwargs.get('screen_sizes', ['mobile', 'tablet'])
        self.orientation = kwargs.get('orientation', ['portrait', 'landscape'])
        self.template = kwargs.get('template', f'mobile/{layout_id}.html')
        self.components = kwargs.get('components', [])
        self.navigation = kwargs.get('navigation', {})
        self.gestures = kwargs.get('gestures', [])
        self.touch_targets = kwargs.get('touch_targets', {})
        self.swipe_actions = kwargs.get('swipe_actions', {})
        self.css_classes = kwargs.get('css_classes', [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert layout to dictionary"""
        return {
            'id': self.layout_id,
            'name': self.name,
            'description': self.description,
            'retail_types': self.retail_types,
            'required_features': self.required_features,
            'screen_sizes': self.screen_sizes,
            'orientation': self.orientation,
            'template': self.template,
            'components': self.components,
            'navigation': self.navigation,
            'gestures': self.gestures,
            'touch_targets': self.touch_targets,
            'swipe_actions': self.swipe_actions,
            'css_classes': self.css_classes
        }


class MobileComponent:
    """
    Represents a mobile-optimized component
    """
    
    def __init__(self, component_id: str, **kwargs):
        self.component_id = component_id
        self.name = kwargs.get('name', component_id.title())
        self.component_type = kwargs.get('component_type', 'view')
        self.required_features = kwargs.get('required_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.template = kwargs.get('template', f'mobile/components/{component_id}.html')
        self.touch_optimized = kwargs.get('touch_optimized', True)
        self.gesture_enabled = kwargs.get('gesture_enabled', False)
        self.swipe_actions = kwargs.get('swipe_actions', {})
        self.long_press_actions = kwargs.get('long_press_actions', {})
        self.pinch_actions = kwargs.get('pinch_actions', {})
        self.min_touch_size = kwargs.get('min_touch_size', 44)  # iOS recommendation
        self.css_classes = kwargs.get('css_classes', [])
        self.config = kwargs.get('config', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary"""
        return {
            'id': self.component_id,
            'name': self.name,
            'type': self.component_type,
            'required_features': self.required_features,
            'retail_types': self.retail_types,
            'template': self.template,
            'touch_optimized': self.touch_optimized,
            'gesture_enabled': self.gesture_enabled,
            'swipe_actions': self.swipe_actions,
            'long_press_actions': self.long_press_actions,
            'pinch_actions': self.pinch_actions,
            'min_touch_size': self.min_touch_size,
            'css_classes': self.css_classes,
            'config': self.config
        }


class MobileNavigation:
    """
    Represents mobile navigation configuration
    """
    
    def __init__(self, nav_id: str, **kwargs):
        self.nav_id = nav_id
        self.nav_type = kwargs.get('nav_type', 'bottom')  # bottom, side, top, floating
        self.retail_types = kwargs.get('retail_types', [])
        self.required_features = kwargs.get('required_features', [])
        self.items = kwargs.get('items', [])
        self.gestures = kwargs.get('gestures', [])
        self.template = kwargs.get('template', f'mobile/navigation/{nav_id}.html')
        self.css_classes = kwargs.get('css_classes', [])
        self.config = kwargs.get('config', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert navigation to dictionary"""
        return {
            'id': self.nav_id,
            'type': self.nav_type,
            'retail_types': self.retail_types,
            'required_features': self.required_features,
            'items': self.items,
            'gestures': self.gestures,
            'template': self.template,
            'css_classes': self.css_classes,
            'config': self.config
        }


class MobileOptimizationManager:
    """
    Manages mobile optimization for different retail types
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.layouts = {}
        self.components = {}
        self.navigation_configs = {}
        self.touch_gestures = {}
        self.responsive_breakpoints = {}
        self.mobile_themes = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize mobile optimization manager"""
        if self._initialized:
            return
        
        self._load_responsive_breakpoints()
        self._load_touch_gestures()
        self._load_mobile_themes()
        self._load_default_layouts()
        self._load_default_components()
        self._load_navigation_configs()
        self._initialized = True
    
    def _load_responsive_breakpoints(self):
        """Load responsive breakpoints"""
        self.responsive_breakpoints = {
            'mobile': {
                'max_width': 767,
                'orientation': ['portrait', 'landscape'],
                'touch_optimized': True,
                'font_scale': 0.9,
                'spacing_scale': 0.8
            },
            'tablet': {
                'min_width': 768,
                'max_width': 1023,
                'orientation': ['portrait', 'landscape'],
                'touch_optimized': True,
                'font_scale': 1.0,
                'spacing_scale': 0.9
            },
            'desktop': {
                'min_width': 1024,
                'orientation': ['landscape'],
                'touch_optimized': False,
                'font_scale': 1.0,
                'spacing_scale': 1.0
            }
        }
    
    def _load_touch_gestures(self):
        """Load touch gesture configurations"""
        self.touch_gestures = {
            'swipe_left': {
                'name': 'Swipe Left',
                'action': 'next',
                'threshold': 50,
                'velocity': 0.3
            },
            'swipe_right': {
                'name': 'Swipe Right',
                'action': 'previous',
                'threshold': 50,
                'velocity': 0.3
            },
            'swipe_up': {
                'name': 'Swipe Up',
                'action': 'scroll_down',
                'threshold': 50,
                'velocity': 0.3
            },
            'swipe_down': {
                'name': 'Swipe Down',
                'action': 'scroll_up',
                'threshold': 50,
                'velocity': 0.3
            },
            'tap': {
                'name': 'Tap',
                'action': 'select',
                'threshold': 10,
                'time_limit': 300
            },
            'double_tap': {
                'name': 'Double Tap',
                'action': 'zoom',
                'threshold': 10,
                'time_limit': 300,
                'tap_interval': 300
            },
            'long_press': {
                'name': 'Long Press',
                'action': 'context_menu',
                'threshold': 10,
                'time_limit': 500
            },
            'pinch': {
                'name': 'Pinch',
                'action': 'zoom',
                'threshold': 20,
                'scale_threshold': 0.1
            }
        }
    
    def _load_mobile_themes(self):
        """Load mobile-specific themes"""
        self.mobile_themes = {
            'restaurant_mobile': {
                'name': 'Restaurant Mobile',
                'primary_color': '#e74c3c',
                'secondary_color': '#c0392b',
                'accent_color': '#f39c12',
                'background_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_size': '16px',
                'button_height': '48px',
                'touch_target_size': '44px',
                'border_radius': '8px',
                'spacing': '16px'
            },
            'retail_mobile': {
                'name': 'Retail Mobile',
                'primary_color': '#3498db',
                'secondary_color': '#2980b9',
                'accent_color': '#e67e22',
                'background_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_size': '16px',
                'button_height': '48px',
                'touch_target_size': '44px',
                'border_radius': '6px',
                'spacing': '16px'
            },
            'apparel_mobile': {
                'name': 'Apparel Mobile',
                'primary_color': '#9b59b6',
                'secondary_color': '#8e44ad',
                'accent_color': '#e74c3c',
                'background_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_size': '16px',
                'button_height': '48px',
                'touch_target_size': '44px',
                'border_radius': '12px',
                'spacing': '16px'
            },
            'grocery_mobile': {
                'name': 'Grocery Mobile',
                'primary_color': '#27ae60',
                'secondary_color': '#229954',
                'accent_color': '#f39c12',
                'background_color': '#ffffff',
                'text_color': '#2c3e50',
                'font_size': '16px',
                'button_height': '48px',
                'touch_target_size': '44px',
                'border_radius': '6px',
                'spacing': '16px'
            }
        }
    
    def _load_default_layouts(self):
        """Load default mobile layouts"""
        # Restaurant Mobile Layout
        restaurant_layout = MobileLayout(
            'restaurant_mobile',
            name='Restaurant Mobile Layout',
            description='Mobile-optimized layout for restaurants',
            retail_types=['restaurant'],
            required_features=['FEATURE_SALES_PROCESSING'],
            template='mobile/restaurant/layout.html',
            components=[
                'mobile_header',
                'mobile_order_panel',
                'mobile_menu_grid',
                'mobile_order_summary',
                'mobile_payment_panel',
                'mobile_navigation'
            ],
            navigation={
                'type': 'bottom',
                'items': [
                    {'id': 'orders', 'icon': 'bi-cart-plus', 'label': 'Orders'},
                    {'id': 'menu', 'icon': 'bi-list-ul', 'label': 'Menu'},
                    {'id': 'tables', 'icon': 'bi-grid-3x3-gap', 'label': 'Tables'},
                    {'id': 'kitchen', 'icon': 'bi-clipboard-check', 'label': 'Kitchen'}
                ]
            },
            gestures=['swipe_left', 'swipe_right', 'tap', 'long_press'],
            swipe_actions={
                'menu_panel': {'left': 'show_categories', 'right': 'show_favorites'},
                'order_panel': {'up': 'show_summary', 'down': 'hide_summary'}
            },
            css_classes=['mobile-layout', 'restaurant-layout']
        )
        self.layouts['restaurant_mobile'] = restaurant_layout
        
        # Retail Mobile Layout
        retail_layout = MobileLayout(
            'retail_mobile',
            name='Retail Mobile Layout',
            description='Mobile-optimized layout for retail stores',
            retail_types=['retail'],
            required_features=['FEATURE_SALES_PROCESSING'],
            template='mobile/retail/layout.html',
            components=[
                'mobile_header',
                'mobile_scanner',
                'mobile_cart',
                'mobile_product_search',
                'mobile_payment_panel',
                'mobile_navigation'
            ],
            navigation={
                'type': 'bottom',
                'items': [
                    {'id': 'scan', 'icon': 'bi-upc-scan', 'label': 'Scan'},
                    {'id': 'search', 'icon': 'bi-search', 'label': 'Search'},
                    {'id': 'cart', 'icon': 'bi-cart', 'label': 'Cart'},
                    {'id': 'products', 'icon': 'bi-box', 'label': 'Products'}
                ]
            },
            gestures=['swipe_left', 'swipe_right', 'tap', 'long_press'],
            swipe_actions={
                'scanner': {'up': 'show_history', 'down': 'show_categories'},
                'cart': {'left': 'apply_discount', 'right': 'add_customer'}
            },
            css_classes=['mobile-layout', 'retail-layout']
        )
        self.layouts['retail_mobile'] = retail_layout
        
        # Apparel Mobile Layout
        apparel_layout = MobileLayout(
            'apparel_mobile',
            name='Apparel Mobile Layout',
            description='Mobile-optimized layout for apparel stores',
            retail_types=['apparel'],
            required_features=['FEATURE_SALES_PROCESSING'],
            template='mobile/apparel/layout.html',
            components=[
                'mobile_header',
                'mobile_variant_selector',
                'mobile_size_chart',
                'mobile_try_on',
                'mobile_cart',
                'mobile_navigation'
            ],
            navigation={
                'type': 'bottom',
                'items': [
                    {'id': 'products', 'icon': 'bi-bag', 'label': 'Products'},
                    {'id': 'variants', 'icon': 'bi-palette', 'label': 'Variants'},
                    {'id': 'cart', 'icon': 'bi-cart', 'label': 'Cart'},
                    {'id': 'exchange', 'icon': 'bi-arrow-repeat', 'label': 'Exchange'}
                ]
            },
            gestures=['swipe_left', 'swipe_right', 'tap', 'long_press', 'pinch'],
            swipe_actions={
                'product_gallery': {'left': 'next_image', 'right': 'previous_image'},
                'variant_selector': {'up': 'show_sizes', 'down': 'show_colors'}
            },
            css_classes=['mobile-layout', 'apparel-layout']
        )
        self.layouts['apparel_mobile'] = apparel_layout
        
        # Grocery Mobile Layout
        grocery_layout = MobileLayout(
            'grocery_mobile',
            name='Grocery Mobile Layout',
            description='Mobile-optimized layout for grocery stores',
            retail_types=['grocery'],
            required_features=['FEATURE_SALES_PROCESSING'],
            template='mobile/grocery/layout.html',
            components=[
                'mobile_header',
                'mobile_weighing_scale',
                'mobile_category_browser',
                'mobile_cart',
                'mobile_expiry_checker',
                'mobile_navigation'
            ],
            navigation={
                'type': 'bottom',
                'items': [
                    {'id': 'categories', 'icon': 'bi-grid', 'label': 'Categories'},
                    {'id': 'weigh', 'icon': 'bi-speedometer2', 'label': 'Weigh'},
                    {'id': 'cart', 'icon': 'bi-cart', 'label': 'Cart'},
                    {'id': 'expiry', 'icon': 'bi-clock-history', 'label': 'Expiry'}
                ]
            },
            gestures=['swipe_left', 'swipe_right', 'tap', 'long_press'],
            swipe_actions={
                'category_browser': {'left': 'next_category', 'right': 'previous_category'},
                'cart': {'up': 'show_totals', 'down': 'show_items'}
            },
            css_classes=['mobile-layout', 'grocery-layout']
        )
        self.layouts['grocery_mobile'] = grocery_layout
    
    def _load_default_components(self):
        """Load default mobile components"""
        # Common mobile components
        common_components = [
            MobileComponent(
                'mobile_header',
                name='Mobile Header',
                component_type='layout',
                template='mobile/components/header.html',
                touch_optimized=True,
                gesture_enabled=True,
                swipe_actions={'left': 'show_menu', 'right': 'show_notifications'},
                css_classes=['mobile-header']
            ),
            MobileComponent(
                'mobile_navigation',
                name='Mobile Navigation',
                component_type='navigation',
                template='mobile/components/navigation.html',
                touch_optimized=True,
                min_touch_size=48,
                css_classes=['mobile-navigation']
            ),
            MobileComponent(
                'mobile_cart',
                name='Mobile Cart',
                component_type='view',
                template='mobile/components/cart.html',
                touch_optimized=True,
                gesture_enabled=True,
                swipe_actions={'up': 'expand', 'down': 'collapse'},
                long_press_actions={'item': 'show_options'},
                css_classes=['mobile-cart']
            ),
            MobileComponent(
                'mobile_payment_panel',
                name='Mobile Payment Panel',
                component_type='view',
                template='mobile/components/payment.html',
                touch_optimized=True,
                required_features=['FEATURE_SALES_PROCESSING'],
                css_classes=['mobile-payment']
            )
        ]
        
        # Restaurant-specific components
        restaurant_components = [
            MobileComponent(
                'mobile_order_panel',
                name='Mobile Order Panel',
                component_type='view',
                template='mobile/components/restaurant/order_panel.html',
                retail_types=['restaurant'],
                required_features=['FEATURE_SALES_PROCESSING'],
                touch_optimized=True,
                gesture_enabled=True,
                swipe_actions={'left': 'show_menu', 'right': 'show_summary'},
                css_classes=['mobile-order-panel']
            ),
            MobileComponent(
                'mobile_menu_grid',
                name='Mobile Menu Grid',
                component_type='view',
                template='mobile/components/restaurant/menu_grid.html',
                retail_types=['restaurant'],
                required_features=['FEATURE_PRODUCT_CATALOG'],
                touch_optimized=True,
                min_touch_size=60,
                css_classes=['mobile-menu-grid']
            ),
            MobileComponent(
                'mobile_table_selector',
                name='Mobile Table Selector',
                component_type='view',
                template='mobile/components/restaurant/table_selector.html',
                retail_types=['restaurant'],
                required_features=['FEATURE_TABLE_MANAGEMENT'],
                touch_optimized=True,
                gesture_enabled=True,
                tap_action='select_table',
                long_press_actions={'table': 'show_details'},
                css_classes=['mobile-table-selector']
            )
        ]
        
        # Retail-specific components
        retail_components = [
            MobileComponent(
                'mobile_scanner',
                name='Mobile Scanner',
                component_type='view',
                template='mobile/components/retail/scanner.html',
                retail_types=['retail'],
                required_features=['FEATURE_BARCODE_SCANNING'],
                touch_optimized=True,
                min_touch_size=80,
                css_classes=['mobile-scanner']
            ),
            MobileComponent(
                'mobile_product_search',
                name='Mobile Product Search',
                component_type='view',
                template='mobile/components/retail/product_search.html',
                retail_types=['retail'],
                required_features=['FEATURE_PRODUCT_CATALOG'],
                touch_optimized=True,
                css_classes=['mobile-product-search']
            )
        ]
        
        # Apparel-specific components
        apparel_components = [
            MobileComponent(
                'mobile_variant_selector',
                name='Mobile Variant Selector',
                component_type='view',
                template='mobile/components/apparel/variant_selector.html',
                retail_types=['apparel'],
                required_features=['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS'],
                touch_optimized=True,
                gesture_enabled=True,
                swipe_actions={'left': 'next_color', 'right': 'previous_color'},
                css_classes=['mobile-variant-selector']
            ),
            MobileComponent(
                'mobile_size_chart',
                name='Mobile Size Chart',
                component_type='view',
                template='mobile/components/apparel/size_chart.html',
                retail_types=['apparel'],
                touch_optimized=True,
                pinch_actions={'zoom': 'toggle_zoom'},
                css_classes=['mobile-size-chart']
            )
        ]
        
        # Grocery-specific components
        grocery_components = [
            MobileComponent(
                'mobile_weighing_scale',
                name='Mobile Weighing Scale',
                component_type='view',
                template='mobile/components/grocery/weighing_scale.html',
                retail_types=['grocery'],
                required_features=['FEATURE_WEIGHING_SCALE'],
                touch_optimized=True,
                min_touch_size=60,
                css_classes=['mobile-weighing-scale']
            ),
            MobileComponent(
                'mobile_category_browser',
                name='Mobile Category Browser',
                component_type='view',
                template='mobile/components/grocery/category_browser.html',
                retail_types=['grocery'],
                required_features=['FEATURE_PRODUCT_CATALOG'],
                touch_optimized=True,
                gesture_enabled=True,
                swipe_actions={'left': 'next_category', 'right': 'previous_category'},
                css_classes=['mobile-category-browser']
            ),
            MobileComponent(
                'mobile_expiry_checker',
                name='Mobile Expiry Checker',
                component_type='view',
                template='mobile/components/grocery/expiry_checker.html',
                retail_types=['grocery'],
                required_features=['FEATURE_EXPIRY_TRACKING'],
                touch_optimized=True,
                css_classes=['mobile-expiry-checker']
            )
        ]
        
        # Register all components
        for component in common_components + restaurant_components + retail_components + apparel_components + grocery_components:
            self.components[component.component_id] = component
    
    def _load_navigation_configs(self):
        """Load navigation configurations"""
        # Bottom navigation (most common for mobile)
        bottom_nav = MobileNavigation(
            'bottom_nav',
            nav_type='bottom',
            template='mobile/navigation/bottom.html',
            items=[
                {'id': 'home', 'icon': 'bi-house', 'label': 'Home', 'priority': 1},
                {'id': 'orders', 'icon': 'bi-cart-plus', 'label': 'Orders', 'priority': 2},
                {'id': 'menu', 'icon': 'bi-list-ul', 'label': 'Menu', 'priority': 3},
                {'id': 'more', 'icon': 'bi-three-dots', 'label': 'More', 'priority': 4}
            ],
            gestures=['tap', 'swipe_up'],
            css_classes=['bottom-navigation']
        )
        self.navigation_configs['bottom_nav'] = bottom_nav
        
        # Side navigation (hamburger menu)
        side_nav = MobileNavigation(
            'side_nav',
            nav_type='side',
            template='mobile/navigation/side.html',
            items=[
                {'id': 'dashboard', 'icon': 'bi-speedometer2', 'label': 'Dashboard'},
                {'id': 'orders', 'icon': 'bi-cart-plus', 'label': 'Orders'},
                {'id': 'products', 'icon': 'bi-box', 'label': 'Products'},
                {'id': 'customers', 'icon': 'bi-people', 'label': 'Customers'},
                {'id': 'reports', 'icon': 'bi-graph-up', 'label': 'Reports'},
                {'id': 'settings', 'icon': 'bi-gear', 'label': 'Settings'}
            ],
            gestures=['swipe_left', 'tap'],
            css_classes=['side-navigation']
        )
        self.navigation_configs['side_nav'] = side_nav
        
        # Floating action button
        fab_nav = MobileNavigation(
            'fab_nav',
            nav_type='floating',
            template='mobile/navigation/fab.html',
            items=[
                {'id': 'quick_order', 'icon': 'bi-plus-lg', 'label': 'Quick Order'},
                {'id': 'scan', 'icon': 'bi-upc-scan', 'label': 'Scan'},
                {'id': 'search', 'icon': 'bi-search', 'label': 'Search'}
            ],
            gestures=['tap', 'long_press'],
            css_classes=['fab-navigation']
        )
        self.navigation_configs['fab_nav'] = fab_nav
    
    def get_mobile_config(self, tenant_id: Optional[str] = None, 
                        user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Get mobile configuration for tenant
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Detect device type
        device_info = self._detect_device(user_agent or request.headers.get('User-Agent', ''))
        
        # Get appropriate layout
        layout_id = f'{retail_type}_mobile'
        layout = self.layouts.get(layout_id)
        
        if not layout:
            layout_id = 'restaurant_mobile'
            layout = self.layouts.get(layout_id)
        
        # Get navigation configuration
        nav_config = self._get_navigation_config(layout.navigation.get('type', 'bottom'))
        
        # Get filtered components
        components = self._filter_components(layout.components, enabled_features, retail_type)
        
        # Get mobile theme
        theme = self.mobile_themes.get(f'{retail_type}_mobile', self.mobile_themes['restaurant_mobile'])
        
        return {
            'device_info': device_info,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'layout': layout.to_dict() if layout else None,
            'navigation': nav_config.to_dict() if nav_config else None,
            'components': [comp.to_dict() for comp in components],
            'theme': theme,
            'gestures': self.touch_gestures,
            'responsive_breakpoints': self.responsive_breakpoints
        }
    
    def _detect_device(self, user_agent: str) -> Dict[str, Any]:
        """Detect device type from user agent"""
        user_agent = user_agent.lower()
        
        device_info = {
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True,
            'screen_size': 'desktop',
            'orientation': 'landscape',
            'touch_capable': False,
            'platform': 'unknown',
            'browser': 'unknown'
        }
        
        # Detect mobile devices
        mobile_indicators = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
        if any(indicator in user_agent for indicator in mobile_indicators):
            device_info['is_mobile'] = True
            device_info['is_desktop'] = False
            device_info['screen_size'] = 'mobile'
            device_info['touch_capable'] = True
        
        # Detect tablets
        tablet_indicators = ['ipad', 'tablet', 'kindle', 'silk']
        if any(indicator in user_agent for indicator in tablet_indicators):
            device_info['is_tablet'] = True
            device_info['is_desktop'] = False
            device_info['screen_size'] = 'tablet'
            device_info['touch_capable'] = True
        
        # Detect platform
        if 'android' in user_agent:
            device_info['platform'] = 'android'
        elif 'iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent:
            device_info['platform'] = 'ios'
        elif 'windows' in user_agent:
            device_info['platform'] = 'windows'
        elif 'mac' in user_agent:
            device_info['platform'] = 'mac'
        elif 'linux' in user_agent:
            device_info['platform'] = 'linux'
        
        # Detect browser
        if 'chrome' in user_agent:
            device_info['browser'] = 'chrome'
        elif 'firefox' in user_agent:
            device_info['browser'] = 'firefox'
        elif 'safari' in user_agent:
            device_info['browser'] = 'safari'
        elif 'edge' in user_agent:
            device_info['browser'] = 'edge'
        
        return device_info
    
    def _get_navigation_config(self, nav_type: str) -> Optional[MobileNavigation]:
        """Get navigation configuration by type"""
        nav_mapping = {
            'bottom': 'bottom_nav',
            'side': 'side_nav',
            'floating': 'fab_nav'
        }
        
        nav_id = nav_mapping.get(nav_type, 'bottom_nav')
        return self.navigation_configs.get(nav_id)
    
    def _filter_components(self, component_ids: List[str], enabled_features: Set[str], 
                         retail_type: str) -> List[MobileComponent]:
        """Filter components based on features and retail type"""
        filtered_components = []
        
        for component_id in component_ids:
            if component_id not in self.components:
                continue
            
            component = self.components[component_id]
            
            # Check required features
            if component.required_features:
                if not all(feature in enabled_features for feature in component.required_features):
                    continue
            
            # Check retail type compatibility
            if component.retail_types and retail_type not in component.retail_types:
                continue
            
            filtered_components.append(component)
        
        return filtered_components
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def register_layout(self, layout: MobileLayout):
        """Register a mobile layout"""
        self.layouts[layout.layout_id] = layout
    
    def register_component(self, component: MobileComponent):
        """Register a mobile component"""
        self.components[component.component_id] = component
    
    def register_navigation(self, navigation: MobileNavigation):
        """Register a mobile navigation"""
        self.navigation_configs[navigation.nav_id] = navigation
    
    def register_theme(self, theme_id: str, theme_config: Dict[str, Any]):
        """Register a mobile theme"""
        self.mobile_themes[theme_id] = theme_config


# Global mobile optimization manager instance
mobile_manager = None


def get_mobile_manager(feature_manager=None) -> MobileOptimizationManager:
    """Get or create global mobile optimization manager instance"""
    global mobile_manager
    if mobile_manager is None:
        mobile_manager = MobileOptimizationManager(feature_manager)
    return mobile_manager