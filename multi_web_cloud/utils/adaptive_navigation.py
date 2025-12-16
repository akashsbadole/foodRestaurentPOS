"""
Adaptive Navigation System with Dynamic Menu Generation
Creates navigation menus based on enabled features and retail types
"""

from typing import Dict, List, Optional, Any, Set
from flask import url_for, current_app, request
from utils.feature_flag_manager import feature_manager
from utils.retail_type_manager import get_retail_type_manager


class AdaptiveNavigationManager:
    """
    Manage adaptive navigation menus based on features and retail types
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.menu_configurations = {}
        self.breadcrumb_configurations = {}
        self.role_permissions = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize navigation manager"""
        if self._initialized:
            return
        
        self._load_menu_configurations()
        self._load_breadcrumb_configurations()
        self._load_role_permissions()
        self._initialized = True
    
    def _load_menu_configurations(self):
        """Load menu configurations for different retail types"""
        self.menu_configurations = {
            'restaurant': {
                'main': {
                    'template': 'navigation/restaurant_main.html',
                    'items': [
                        {
                            'id': 'dashboard',
                            'title': 'Dashboard',
                            'icon': 'bi-house',
                            'url': 'dashboard.index',
                            'order': 1,
                            'required_features': [],
                            'roles': ['admin', 'manager', 'staff']
                        },
                        {
                            'id': 'orders',
                            'title': 'Orders',
                            'icon': 'bi-cart-plus',
                            'url': 'orders.new_order',
                            'order': 2,
                            'required_features': ['FEATURE_SALES_PROCESSING'],
                            'roles': ['admin', 'manager', 'staff'],
                            'submenu': [
                                {
                                    'id': 'new_order',
                                    'title': 'New Order',
                                    'url': 'orders.new_order',
                                    'required_features': ['FEATURE_SALES_PROCESSING']
                                },
                                {
                                    'id': 'order_list',
                                    'title': 'Order History',
                                    'url': 'orders.list_orders',
                                    'required_features': ['FEATURE_SALES_PROCESSING']
                                }
                            ]
                        },
                        {
                            'id': 'tables',
                            'title': 'Table Management',
                            'icon': 'bi-grid-3x3-gap',
                            'url': 'tables.index',
                            'order': 3,
                            'required_features': ['FEATURE_TABLE_MANAGEMENT'],
                            'roles': ['admin', 'manager', 'staff']
                        },
                        {
                            'id': 'menu',
                            'title': 'Menu Management',
                            'icon': 'bi-list-ul',
                            'url': 'menu.index',
                            'order': 4,
                            'required_features': ['FEATURE_PRODUCT_CATALOG'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'kitchen',
                            'title': 'Kitchen Display',
                            'icon': 'bi-clipboard-check',
                            'url': 'kot.index',
                            'order': 5,
                            'required_features': ['FEATURE_KITCHEN_DISPLAY'],
                            'roles': ['admin', 'manager', 'staff', 'kitchen']
                        },
                        {
                            'id': 'reservations',
                            'title': 'Reservations',
                            'icon': 'bi-calendar-check',
                            'url': 'reservations.index',
                            'order': 6,
                            'required_features': ['FEATURE_RESERVATIONS'],
                            'roles': ['admin', 'manager', 'staff']
                        }
                    ]
                },
                'sidebar': {
                    'template': 'navigation/restaurant_sidebar.html',
                    'items': []  # Will inherit from main
                },
                'top': {
                    'template': 'navigation/restaurant_top.html',
                    'items': []  # Will inherit from main
                }
            },
            'retail': {
                'main': {
                    'template': 'navigation/retail_main.html',
                    'items': [
                        {
                            'id': 'dashboard',
                            'title': 'Dashboard',
                            'icon': 'bi-house',
                            'url': 'dashboard.index',
                            'order': 1,
                            'required_features': [],
                            'roles': ['admin', 'manager', 'staff']
                        },
                        {
                            'id': 'sales',
                            'title': 'Point of Sale',
                            'icon': 'bi-cash-stack',
                            'url': 'pos.index',
                            'order': 2,
                            'required_features': ['FEATURE_SALES_PROCESSING'],
                            'roles': ['admin', 'manager', 'staff'],
                            'submenu': [
                                {
                                    'id': 'quick_sale',
                                    'title': 'Quick Sale',
                                    'url': 'pos.quick_sale',
                                    'required_features': ['FEATURE_QUICK_SALE']
                                },
                                {
                                    'id': 'counter_sale',
                                    'title': 'Counter Sale',
                                    'url': 'pos.counter_sale',
                                    'required_features': ['FEATURE_SALES_PROCESSING']
                                }
                            ]
                        },
                        {
                            'id': 'products',
                            'title': 'Product Catalog',
                            'icon': 'bi-box',
                            'url': 'products.index',
                            'order': 3,
                            'required_features': ['FEATURE_PRODUCT_CATALOG'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'inventory',
                            'title': 'Inventory',
                            'icon': 'bi-box-seam',
                            'url': 'inventory.index',
                            'order': 4,
                            'required_features': ['FEATURE_INVENTORY_BASIC'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'customers',
                            'title': 'Customers',
                            'icon': 'bi-people',
                            'url': 'customers.index',
                            'order': 5,
                            'required_features': ['FEATURE_CUSTOMER_MANAGEMENT'],
                            'roles': ['admin', 'manager', 'staff']
                        }
                    ]
                }
            },
            'apparel': {
                'main': {
                    'template': 'navigation/apparel_main.html',
                    'items': [
                        {
                            'id': 'dashboard',
                            'title': 'Dashboard',
                            'icon': 'bi-house',
                            'url': 'dashboard.index',
                            'order': 1,
                            'required_features': [],
                            'roles': ['admin', 'manager', 'staff']
                        },
                        {
                            'id': 'sales',
                            'title': 'Sales',
                            'icon': 'bi-cash-stack',
                            'url': 'sales.index',
                            'order': 2,
                            'required_features': ['FEATURE_SALES_PROCESSING'],
                            'roles': ['admin', 'manager', 'staff'],
                            'submenu': [
                                {
                                    'id': 'new_sale',
                                    'title': 'New Sale',
                                    'url': 'sales.new',
                                    'required_features': ['FEATURE_SALES_PROCESSING']
                                },
                                {
                                    'id': 'exchanges',
                                    'title': 'Exchanges',
                                    'url': 'exchanges.index',
                                    'required_features': ['FEATURE_EXCHANGE_MANAGEMENT']
                                },
                                {
                                    'id': 'alterations',
                                    'title': 'Alterations',
                                    'url': 'alterations.index',
                                    'required_features': ['FEATURE_ALTERATION_TRACKING']
                                }
                            ]
                        },
                        {
                            'id': 'products',
                            'title': 'Products',
                            'icon': 'bi-bag',
                            'url': 'products.index',
                            'order': 3,
                            'required_features': ['FEATURE_PRODUCT_CATALOG'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'inventory',
                            'title': 'Inventory',
                            'icon': 'bi-box-seam',
                            'url': 'inventory.index',
                            'order': 4,
                            'required_features': ['FEATURE_INVENTORY_BASIC'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'variants',
                            'title': 'Variants',
                            'icon': 'bi-palette',
                            'url': 'variants.index',
                            'order': 5,
                            'required_features': ['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS'],
                            'roles': ['admin', 'manager']
                        }
                    ]
                }
            },
            'grocery': {
                'main': {
                    'template': 'navigation/grocery_main.html',
                    'items': [
                        {
                            'id': 'dashboard',
                            'title': 'Dashboard',
                            'icon': 'bi-house',
                            'url': 'dashboard.index',
                            'order': 1,
                            'required_features': [],
                            'roles': ['admin', 'manager', 'staff']
                        },
                        {
                            'id': 'sales',
                            'title': 'Sales',
                            'icon': 'bi-cash-stack',
                            'url': 'sales.index',
                            'order': 2,
                            'required_features': ['FEATURE_SALES_PROCESSING'],
                            'roles': ['admin', 'manager', 'staff'],
                            'submenu': [
                                {
                                    'id': 'counter_sale',
                                    'title': 'Counter Sale',
                                    'url': 'sales.counter',
                                    'required_features': ['FEATURE_SALES_PROCESSING']
                                },
                                {
                                    'id': 'bulk_sale',
                                    'title': 'Bulk Sale',
                                    'url': 'sales.bulk',
                                    'required_features': ['FEATURE_BULK_SALES']
                                },
                                {
                                    'id': 'weighing',
                                    'title': 'Weighing Scale',
                                    'url': 'sales.weighing',
                                    'required_features': ['FEATURE_WEIGHING_SCALE']
                                }
                            ]
                        },
                        {
                            'id': 'products',
                            'title': 'Products',
                            'icon': 'bi-basket',
                            'url': 'products.index',
                            'order': 3,
                            'required_features': ['FEATURE_PRODUCT_CATALOG'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'inventory',
                            'title': 'Inventory',
                            'icon': 'bi-box-seam',
                            'url': 'inventory.index',
                            'order': 4,
                            'required_features': ['FEATURE_INVENTORY_BASIC'],
                            'roles': ['admin', 'manager']
                        },
                        {
                            'id': 'expiry',
                            'title': 'Expiry Tracking',
                            'icon': 'bi-clock-history',
                            'url': 'expiry.index',
                            'order': 5,
                            'required_features': ['FEATURE_EXPIRY_TRACKING'],
                            'roles': ['admin', 'manager']
                        }
                    ]
                }
            }
        }
    
    def _load_breadcrumb_configurations(self):
        """Load breadcrumb configurations"""
        self.breadcrumb_configurations = {
            'dashboard': {
                'title': 'Dashboard',
                'icon': 'bi-house',
                'parent': None
            },
            'orders': {
                'title': 'Orders',
                'icon': 'bi-cart-plus',
                'parent': 'dashboard'
            },
            'orders.new': {
                'title': 'New Order',
                'icon': 'bi-plus-circle',
                'parent': 'orders'
            },
            'orders.list': {
                'title': 'Order History',
                'icon': 'bi-list-ul',
                'parent': 'orders'
            },
            'tables': {
                'title': 'Tables',
                'icon': 'bi-grid-3x3-gap',
                'parent': 'dashboard'
            },
            'menu': {
                'title': 'Menu',
                'icon': 'bi-list-ul',
                'parent': 'dashboard'
            },
            'inventory': {
                'title': 'Inventory',
                'icon': 'bi-box-seam',
                'parent': 'dashboard'
            },
            'reports': {
                'title': 'Reports',
                'icon': 'bi-graph-up',
                'parent': 'dashboard'
            },
            'settings': {
                'title': 'Settings',
                'icon': 'bi-gear',
                'parent': 'dashboard'
            }
        }
    
    def _load_role_permissions(self):
        """Load role-based permissions"""
        self.role_permissions = {
            'admin': ['*'],  # Full access
            'manager': ['dashboard', 'orders', 'tables', 'menu', 'inventory', 'reports'],
            'staff': ['dashboard', 'orders', 'tables'],
            'kitchen': ['dashboard', 'kitchen'],
            'cashier': ['dashboard', 'sales', 'products']
        }
    
    def get_navigation_menu(self, menu_type: str = 'main', tenant_id: Optional[str] = None, 
                          user_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Get navigation menu based on retail type, features, and user role
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        # Get retail type and enabled features
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Get menu configuration
        menu_config = self._get_menu_config(retail_type, menu_type)
        
        # Filter menu items based on features and roles
        filtered_items = self._filter_menu_items(
            menu_config.get('items', []), 
            enabled_features, 
            user_role
        )
        
        return {
            'menu_type': menu_type,
            'retail_type': retail_type,
            'template': menu_config.get('template', f'navigation/{menu_type}.html'),
            'items': filtered_items,
            'enabled_features': list(enabled_features),
            'user_role': user_role
        }
    
    def get_breadcrumb_navigation(self, current_page: str, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get breadcrumb navigation for current page
        """
        if not self._initialized:
            self.initialize()
        
        breadcrumbs = []
        current = current_page
        
        while current:
            if current in self.breadcrumb_configurations:
                config = self.breadcrumb_configurations[current]
                breadcrumb = {
                    'id': current,
                    'title': config['title'],
                    'icon': config.get('icon'),
                    'url': self._get_page_url(current)
                }
                breadcrumbs.insert(0, breadcrumb)
                current = config.get('parent')
            else:
                break
        
        return breadcrumbs
    
    def get_mobile_navigation(self, tenant_id: Optional[str] = None, 
                           user_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Get mobile-optimized navigation
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Mobile navigation is simplified
        mobile_items = self._get_mobile_menu_items(retail_type, enabled_features, user_role)
        
        return {
            'template': 'navigation/mobile.html',
            'items': mobile_items,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features)
        }
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def _get_menu_config(self, retail_type: str, menu_type: str) -> Dict[str, Any]:
        """Get menu configuration for retail type and menu type"""
        retail_config = self.menu_configurations.get(retail_type, {})
        menu_config = retail_config.get(menu_type, {})
        
        # Inherit from main menu if not specified
        if not menu_config and menu_type != 'main':
            main_config = retail_config.get('main', {})
            menu_config = {
                'template': f'navigation/{retail_type}_{menu_type}.html',
                'items': main_config.get('items', [])
            }
        
        return menu_config
    
    def _filter_menu_items(self, items: List[Dict], enabled_features: Set[str], 
                         user_role: Optional[str] = None) -> List[Dict]:
        """Filter menu items based on features and roles"""
        filtered_items = []
        
        for item in items:
            # Check feature requirements
            required_features = item.get('required_features', [])
            if required_features and not all(feature in enabled_features for feature in required_features):
                continue
            
            # Check role permissions
            allowed_roles = item.get('roles', [])
            if user_role and allowed_roles and user_role not in allowed_roles:
                # Check if user has wildcard permission
                if not any(role == '*' or role == user_role for role in self.role_permissions.get(user_role, [])):
                    continue
            
            # Create filtered item
            filtered_item = item.copy()
            
            # Filter submenu if exists
            if 'submenu' in item:
                filtered_item['submenu'] = self._filter_menu_items(
                    item['submenu'], enabled_features, user_role
                )
            
            # Generate URL
            if 'url' in filtered_item and isinstance(filtered_item['url'], str):
                try:
                    filtered_item['url'] = url_for(filtered_item['url'])
                except:
                    # Keep original URL if url_for fails
                    pass
            
            filtered_items.append(filtered_item)
        
        return filtered_items
    
    def _get_mobile_menu_items(self, retail_type: str, enabled_features: Set[str], 
                             user_role: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get simplified mobile menu items"""
        # Get main menu items and simplify for mobile
        main_menu = self.get_navigation_menu('main', None, user_role)
        mobile_items = []
        
        for item in main_menu['items']:
            mobile_item = {
                'id': item['id'],
                'title': item['title'],
                'icon': item.get('icon'),
                'url': item.get('url'),
                'priority': item.get('order', 999)
            }
            
            # Include only top-level items for mobile
            if mobile_item['priority'] <= 5:  # Only top 5 items
                mobile_items.append(mobile_item)
        
        # Add mobile-specific items
        mobile_items.extend([
            {
                'id': 'search',
                'title': 'Search',
                'icon': 'bi-search',
                'url': '#search',
                'priority': 100
            },
            {
                'id': 'profile',
                'title': 'Profile',
                'icon': 'bi-person',
                'url': '#profile',
                'priority': 101
            }
        ])
        
        return sorted(mobile_items, key=lambda x: x['priority'])
    
    def _get_page_url(self, page_id: str) -> str:
        """Get URL for page ID"""
        url_mapping = {
            'dashboard': 'dashboard.index',
            'orders': 'orders.list_orders',
            'orders.new': 'orders.new_order',
            'orders.list': 'orders.list_orders',
            'tables': 'tables.index',
            'menu': 'menu.index',
            'inventory': 'inventory.index',
            'reports': 'reports.index',
            'settings': 'auth.profile'
        }
        
        endpoint = url_mapping.get(page_id)
        if endpoint:
            try:
                return url_for(endpoint)
            except:
                return '#'
        
        return '#'
    
    def register_menu_item(self, retail_type: str, menu_type: str, item: Dict[str, Any]):
        """Register a new menu item"""
        if retail_type not in self.menu_configurations:
            self.menu_configurations[retail_type] = {}
        
        if menu_type not in self.menu_configurations[retail_type]:
            self.menu_configurations[retail_type][menu_type] = {
                'template': f'navigation/{retail_type}_{menu_type}.html',
                'items': []
            }
        
        self.menu_configurations[retail_type][menu_type]['items'].append(item)
    
    def register_breadcrumb(self, page_id: str, config: Dict[str, Any]):
        """Register breadcrumb configuration"""
        self.breadcrumb_configurations[page_id] = config
    
    def update_menu_item(self, retail_type: str, menu_type: str, item_id: str, 
                        updates: Dict[str, Any]):
        """Update existing menu item"""
        if retail_type in self.menu_configurations:
            if menu_type in self.menu_configurations[retail_type]:
                items = self.menu_configurations[retail_type][menu_type].get('items', [])
                for item in items:
                    if item.get('id') == item_id:
                        item.update(updates)
                        break
    
    def remove_menu_item(self, retail_type: str, menu_type: str, item_id: str):
        """Remove menu item"""
        if retail_type in self.menu_configurations:
            if menu_type in self.menu_configurations[retail_type]:
                items = self.menu_configurations[retail_type][menu_type].get('items', [])
                self.menu_configurations[retail_type][menu_type]['items'] = [
                    item for item in items if item.get('id') != item_id
                ]


# Global navigation manager instance
navigation_manager = None


def get_navigation_manager(feature_manager=None) -> AdaptiveNavigationManager:
    """Get or create global navigation manager instance"""
    global navigation_manager
    if navigation_manager is None:
        navigation_manager = AdaptiveNavigationManager(feature_manager)
    return navigation_manager