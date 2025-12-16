"""
Dynamic Dashboard System with Adaptive Widgets
Creates adaptive dashboards based on retail type and enabled features
"""

from typing import Dict, List, Optional, Any, Set, Callable
from flask import current_app, request
from datetime import datetime, timedelta
import json
from utils.feature_flag_manager import feature_manager
from utils.retail_type_manager import get_retail_type_manager


class DashboardWidget:
    """
    Represents a dashboard widget with dynamic content
    """
    
    def __init__(self, widget_id: str, **kwargs):
        self.widget_id = widget_id
        self.title = kwargs.get('title', widget_id.title())
        self.description = kwargs.get('description', '')
        self.widget_type = kwargs.get('widget_type', 'card')
        self.size = kwargs.get('size', 'medium')  # small, medium, large, full
        self.position = kwargs.get('position', {'x': 0, 'y': 0, 'w': 4, 'h': 3})
        self.required_features = kwargs.get('required_features', [])
        self.excluded_features = kwargs.get('excluded_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.roles = kwargs.get('roles', [])
        self.refresh_interval = kwargs.get('refresh_interval', 0)  # seconds, 0 = no auto-refresh
        self.data_source = kwargs.get('data_source', None)
        self.template = kwargs.get('template', f'dashboard/widgets/{widget_id}.html')
        self.css_classes = kwargs.get('css_classes', [])
        self.attributes = kwargs.get('attributes', {})
        self.config = kwargs.get('config', {})
        self.data_cache = {}
        self.last_refresh = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert widget to dictionary"""
        return {
            'id': self.widget_id,
            'title': self.title,
            'description': self.description,
            'type': self.widget_type,
            'size': self.size,
            'position': self.position,
            'required_features': self.required_features,
            'excluded_features': self.excluded_features,
            'retail_types': self.retail_types,
            'roles': self.roles,
            'refresh_interval': self.refresh_interval,
            'template': self.template,
            'css_classes': self.css_classes,
            'attributes': self.attributes,
            'config': self.config
        }
    
    def get_data(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get widget data"""
        # Check cache first
        if self._is_cache_valid():
            return self.data_cache.get('data', {})
        
        # Fetch fresh data
        data = self._fetch_data(tenant_id)
        
        # Cache the data
        self.data_cache = {
            'data': data,
            'timestamp': datetime.utcnow()
        }
        
        return data
    
    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid"""
        if not self.data_cache or self.refresh_interval == 0:
            return False
        
        last_refresh = self.data_cache.get('timestamp')
        if not last_refresh:
            return False
        
        return (datetime.utcnow() - last_refresh).total_seconds() < self.refresh_interval
    
    def _fetch_data(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Fetch widget data (to be overridden by subclasses)"""
        if self.data_source:
            # Call data source function if provided
            if callable(self.data_source):
                return self.data_source(tenant_id)
        
        return {}


class DashboardLayout:
    """
    Represents a dashboard layout with widgets
    """
    
    def __init__(self, layout_id: str, **kwargs):
        self.layout_id = layout_id
        self.title = kwargs.get('title', layout_id.title())
        self.description = kwargs.get('description', '')
        self.retail_types = kwargs.get('retail_types', [])
        self.required_features = kwargs.get('required_features', [])
        self.default_widgets = kwargs.get('default_widgets', [])
        self.widget_positions = kwargs.get('widget_positions', {})
        self.grid_config = kwargs.get('grid_config', {
            'cols': 12,
            'row_height': 100,
            'margin': [10, 10]
        })
        self.css_classes = kwargs.get('css_classes', [])
        self.attributes = kwargs.get('attributes', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert layout to dictionary"""
        return {
            'id': self.layout_id,
            'title': self.title,
            'description': self.description,
            'retail_types': self.retail_types,
            'required_features': self.required_features,
            'default_widgets': self.default_widgets,
            'widget_positions': self.widget_positions,
            'grid_config': self.grid_config,
            'css_classes': self.css_classes,
            'attributes': self.attributes
        }


class DynamicDashboardManager:
    """
    Manages dynamic dashboards with adaptive widgets
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.widgets = {}
        self.layouts = {}
        self.data_providers = {}
        self.widget_types = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize dashboard manager"""
        if self._initialized:
            return
        
        self._load_widget_types()
        self._load_data_providers()
        self._load_default_widgets()
        self._load_default_layouts()
        self._initialized = True
    
    def _load_widget_types(self):
        """Load available widget types"""
        self.widget_types = {
            'card': {
                'template': 'dashboard/widgets/card.html',
                'default_size': 'medium'
            },
            'chart': {
                'template': 'dashboard/widgets/chart.html',
                'default_size': 'large'
            },
            'table': {
                'template': 'dashboard/widgets/table.html',
                'default_size': 'large'
            },
            'metric': {
                'template': 'dashboard/widgets/metric.html',
                'default_size': 'small'
            },
            'list': {
                'template': 'dashboard/widgets/list.html',
                'default_size': 'medium'
            },
            'progress': {
                'template': 'dashboard/widgets/progress.html',
                'default_size': 'small'
            },
            'calendar': {
                'template': 'dashboard/widgets/calendar.html',
                'default_size': 'large'
            },
            'map': {
                'template': 'dashboard/widgets/map.html',
                'default_size': 'large'
            },
            'feed': {
                'template': 'dashboard/widgets/feed.html',
                'default_size': 'medium'
            },
            'alert': {
                'template': 'dashboard/widgets/alert.html',
                'default_size': 'small'
            }
        }
    
    def _load_data_providers(self):
        """Load data providers for widgets"""
        self.data_providers = {
            'sales_summary': self._provide_sales_summary,
            'order_stats': self._provide_order_stats,
            'top_products': self._provide_top_products,
            'recent_orders': self._provide_recent_orders,
            'customer_stats': self._provide_customer_stats,
            'inventory_alerts': self._provide_inventory_alerts,
            'revenue_chart': self._provide_revenue_chart,
            'table_status': self._provide_table_status,
            'kitchen_orders': self._provide_kitchen_orders,
            'low_stock': self._provide_low_stock,
            'expiry_alerts': self._provide_expiry_alerts,
            'daily_sales': self._provide_daily_sales,
            'hourly_sales': self._provide_hourly_sales,
            'category_sales': self._provide_category_sales,
            'payment_methods': self._provide_payment_methods,
            'staff_performance': self._provide_staff_performance,
            'customer_loyalty': self._provide_customer_loyalty,
            'promotion_performance': self._provide_promotion_performance
        }
    
    def _load_default_widgets(self):
        """Load default widgets"""
        # Sales Summary Widget
        sales_summary_widget = DashboardWidget(
            'sales_summary',
            title='Sales Summary',
            description='Today\'s sales overview',
            widget_type='metric',
            size='medium',
            required_features=['FEATURE_SALES_PROCESSING'],
            data_source='sales_summary',
            refresh_interval=300,  # 5 minutes
            config={
                'show_daily': True,
                'show_weekly': True,
                'show_monthly': True,
                'currency': '₹'
            }
        )
        self.widgets['sales_summary'] = sales_summary_widget
        
        # Order Statistics Widget
        order_stats_widget = DashboardWidget(
            'order_stats',
            title='Order Statistics',
            description='Order status and counts',
            widget_type='card',
            size='medium',
            required_features=['FEATURE_SALES_PROCESSING'],
            data_source='order_stats',
            refresh_interval=180,  # 3 minutes
            config={
                'show_pending': True,
                'show_completed': True,
                'show_cancelled': True
            }
        )
        self.widgets['order_stats'] = order_stats_widget
        
        # Top Products Widget
        top_products_widget = DashboardWidget(
            'top_products',
            title='Top Products',
            description='Best selling products',
            widget_type='list',
            size='medium',
            required_features=['FEATURE_SALES_PROCESSING', 'FEATURE_PRODUCT_CATALOG'],
            data_source='top_products',
            refresh_interval=600,  # 10 minutes
            config={
                'limit': 10,
                'show_revenue': True,
                'show_quantity': True
            }
        )
        self.widgets['top_products'] = top_products_widget
        
        # Recent Orders Widget
        recent_orders_widget = DashboardWidget(
            'recent_orders',
            title='Recent Orders',
            description='Latest orders',
            widget_type='table',
            size='large',
            required_features=['FEATURE_SALES_PROCESSING'],
            data_source='recent_orders',
            refresh_interval=120,  # 2 minutes
            config={
                'limit': 20,
                'show_customer': True,
                'show_amount': True,
                'show_status': True
            }
        )
        self.widgets['recent_orders'] = recent_orders_widget
        
        # Customer Statistics Widget
        customer_stats_widget = DashboardWidget(
            'customer_stats',
            title='Customer Statistics',
            description='Customer metrics',
            widget_type='card',
            size='medium',
            required_features=['FEATURE_CUSTOMER_MANAGEMENT'],
            data_source='customer_stats',
            refresh_interval=600,  # 10 minutes
            config={
                'show_new_customers': True,
                'show_returning_customers': True,
                'show_loyalty_members': True
            }
        )
        self.widgets['customer_stats'] = customer_stats_widget
        
        # Restaurant-specific widgets
        table_status_widget = DashboardWidget(
            'table_status',
            title='Table Status',
            description='Restaurant table occupancy',
            widget_type='card',
            size='medium',
            retail_types=['restaurant'],
            required_features=['FEATURE_TABLE_MANAGEMENT'],
            data_source='table_status',
            refresh_interval=60,  # 1 minute
            config={
                'show_occupied': True,
                'show_available': True,
                'show_reserved': True
            }
        )
        self.widgets['table_status'] = table_status_widget
        
        kitchen_orders_widget = DashboardWidget(
            'kitchen_orders',
            title='Kitchen Orders',
            description='Active kitchen orders',
            widget_type='list',
            size='large',
            retail_types=['restaurant'],
            required_features=['FEATURE_KITCHEN_DISPLAY'],
            data_source='kitchen_orders',
            refresh_interval=30,  # 30 seconds
            config={
                'show_pending': True,
                'show_preparing': True,
                'show_ready': True,
                'limit': 15
            }
        )
        self.widgets['kitchen_orders'] = kitchen_orders_widget
        
        # Retail-specific widgets
        inventory_alerts_widget = DashboardWidget(
            'inventory_alerts',
            title='Inventory Alerts',
            description='Low stock and inventory issues',
            widget_type='alert',
            size='small',
            required_features=['FEATURE_INVENTORY_BASIC'],
            data_source='inventory_alerts',
            refresh_interval=300,  # 5 minutes
            config={
                'show_low_stock': True,
                'show_out_of_stock': True,
                'limit': 5
            }
        )
        self.widgets['inventory_alerts'] = inventory_alerts_widget
        
        # Grocery-specific widgets
        low_stock_widget = DashboardWidget(
            'low_stock',
            title='Low Stock Items',
            description='Products running low on stock',
            widget_type='list',
            size='medium',
            retail_types=['grocery'],
            required_features=['FEATURE_INVENTORY_BASIC'],
            data_source='low_stock',
            refresh_interval=600,  # 10 minutes
            config={
                'threshold': 10,
                'limit': 10
            }
        )
        self.widgets['low_stock'] = low_stock_widget
        
        expiry_alerts_widget = DashboardWidget(
            'expiry_alerts',
            title='Expiry Alerts',
            description='Products approaching expiry',
            widget_type='alert',
            size='small',
            retail_types=['grocery'],
            required_features=['FEATURE_EXPIRY_TRACKING'],
            data_source='expiry_alerts',
            refresh_interval=3600,  # 1 hour
            config={
                'days_threshold': 7,
                'limit': 10
            }
        )
        self.widgets['expiry_alerts'] = expiry_alerts_widget
        
        # Revenue Chart Widget
        revenue_chart_widget = DashboardWidget(
            'revenue_chart',
            title='Revenue Overview',
            description='Revenue trends and analytics',
            widget_type='chart',
            size='large',
            required_features=['FEATURE_SALES_PROCESSING'],
            data_source='revenue_chart',
            refresh_interval=900,  # 15 minutes
            config={
                'chart_type': 'line',
                'period': '7d',
                'show_comparison': True
            }
        )
        self.widgets['revenue_chart'] = revenue_chart_widget
    
    def _load_default_layouts(self):
        """Load default dashboard layouts"""
        # Restaurant Dashboard Layout
        restaurant_layout = DashboardLayout(
            'restaurant_dashboard',
            title='Restaurant Dashboard',
            description='Main dashboard for restaurant operations',
            retail_types=['restaurant'],
            default_widgets=[
                'sales_summary',
                'order_stats',
                'table_status',
                'kitchen_orders',
                'top_products',
                'recent_orders',
                'revenue_chart'
            ],
            widget_positions={
                'sales_summary': {'x': 0, 'y': 0, 'w': 4, 'h': 3},
                'order_stats': {'x': 4, 'y': 0, 'w': 4, 'h': 3},
                'table_status': {'x': 8, 'y': 0, 'w': 4, 'h': 3},
                'kitchen_orders': {'x': 0, 'y': 3, 'w': 6, 'h': 4},
                'top_products': {'x': 6, 'y': 3, 'w': 6, 'h': 4},
                'recent_orders': {'x': 0, 'y': 7, 'w': 8, 'h': 4},
                'revenue_chart': {'x': 8, 'y': 7, 'w': 4, 'h': 4}
            }
        )
        self.layouts['restaurant_dashboard'] = restaurant_layout
        
        # Retail Dashboard Layout
        retail_layout = DashboardLayout(
            'retail_dashboard',
            title='Retail Dashboard',
            description='Main dashboard for retail operations',
            retail_types=['retail'],
            default_widgets=[
                'sales_summary',
                'order_stats',
                'top_products',
                'recent_orders',
                'customer_stats',
                'inventory_alerts',
                'revenue_chart'
            ],
            widget_positions={
                'sales_summary': {'x': 0, 'y': 0, 'w': 4, 'h': 3},
                'order_stats': {'x': 4, 'y': 0, 'w': 4, 'h': 3},
                'top_products': {'x': 8, 'y': 0, 'w': 4, 'h': 3},
                'recent_orders': {'x': 0, 'y': 3, 'w': 8, 'h': 4},
                'customer_stats': {'x': 8, 'y': 3, 'w': 4, 'h': 4},
                'inventory_alerts': {'x': 0, 'y': 7, 'w': 6, 'h': 3},
                'revenue_chart': {'x': 6, 'y': 7, 'w': 6, 'h': 3}
            }
        )
        self.layouts['retail_dashboard'] = retail_layout
        
        # Apparel Dashboard Layout
        apparel_layout = DashboardLayout(
            'apparel_dashboard',
            title='Apparel Dashboard',
            description='Main dashboard for apparel operations',
            retail_types=['apparel'],
            default_widgets=[
                'sales_summary',
                'order_stats',
                'top_products',
                'recent_orders',
                'customer_stats',
                'inventory_alerts',
                'revenue_chart'
            ],
            widget_positions={
                'sales_summary': {'x': 0, 'y': 0, 'w': 4, 'h': 3},
                'order_stats': {'x': 4, 'y': 0, 'w': 4, 'h': 3},
                'customer_stats': {'x': 8, 'y': 0, 'w': 4, 'h': 3},
                'top_products': {'x': 0, 'y': 3, 'w': 6, 'h': 4},
                'recent_orders': {'x': 6, 'y': 3, 'w': 6, 'h': 4},
                'inventory_alerts': {'x': 0, 'y': 7, 'w': 6, 'h': 3},
                'revenue_chart': {'x': 6, 'y': 7, 'w': 6, 'h': 3}
            }
        )
        self.layouts['apparel_dashboard'] = apparel_layout
        
        # Grocery Dashboard Layout
        grocery_layout = DashboardLayout(
            'grocery_dashboard',
            title='Grocery Dashboard',
            description='Main dashboard for grocery operations',
            retail_types=['grocery'],
            default_widgets=[
                'sales_summary',
                'order_stats',
                'top_products',
                'recent_orders',
                'low_stock',
                'expiry_alerts',
                'revenue_chart'
            ],
            widget_positions={
                'sales_summary': {'x': 0, 'y': 0, 'w': 4, 'h': 3},
                'order_stats': {'x': 4, 'y': 0, 'w': 4, 'h': 3},
                'low_stock': {'x': 8, 'y': 0, 'w': 4, 'h': 3},
                'recent_orders': {'x': 0, 'y': 3, 'w': 8, 'h': 4},
                'top_products': {'x': 8, 'y': 3, 'w': 4, 'h': 4},
                'expiry_alerts': {'x': 0, 'y': 7, 'w': 6, 'h': 3},
                'revenue_chart': {'x': 6, 'y': 7, 'w': 6, 'h': 3}
            }
        )
        self.layouts['grocery_dashboard'] = grocery_layout
    
    def get_dashboard(self, layout_id: Optional[str] = None, tenant_id: Optional[str] = None, 
                     user_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Get dashboard configuration with filtered widgets
        """
        if not self._initialized:
            self.initialize()
        
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = self.feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = self.feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Determine layout
        if layout_id is None:
            layout_id = f'{retail_type}_dashboard'
        
        layout = self.layouts.get(layout_id)
        if not layout:
            # Fallback to retail type dashboard
            layout_id = f'{retail_type}_dashboard'
            layout = self.layouts.get(layout_id)
        
        if not layout:
            # Fallback to restaurant dashboard
            layout_id = 'restaurant_dashboard'
            layout = self.layouts.get(layout_id)
        
        if not layout:
            return {'error': 'No suitable dashboard layout found'}
        
        # Filter widgets based on features and permissions
        filtered_widgets = self._filter_widgets(
            layout.default_widgets, enabled_features, user_role, retail_type
        )
        
        # Get widget configurations with data
        widget_configs = []
        for widget_id in filtered_widgets:
            if widget_id in self.widgets:
                widget = self.widgets[widget_id]
                widget_config = widget.to_dict()
                widget_config['data'] = widget.get_data(tenant_id)
                widget_configs.append(widget_config)
        
        return {
            'layout': layout.to_dict(),
            'widgets': widget_configs,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'user_role': user_role,
            'tenant_id': tenant_id
        }
    
    def get_widget(self, widget_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get specific widget configuration with data"""
        if not self._initialized:
            self.initialize()
        
        if widget_id not in self.widgets:
            return None
        
        widget = self.widgets[widget_id]
        widget_config = widget.to_dict()
        widget_config['data'] = widget.get_data(tenant_id)
        
        return widget_config
    
    def _filter_widgets(self, widget_ids: List[str], enabled_features: Set[str], 
                       user_role: Optional[str], retail_type: str) -> List[str]:
        """Filter widgets based on features and permissions"""
        filtered_widgets = []
        
        for widget_id in widget_ids:
            if widget_id not in self.widgets:
                continue
            
            widget = self.widgets[widget_id]
            
            # Check required features
            if widget.required_features:
                if not all(feature in enabled_features for feature in widget.required_features):
                    continue
            
            # Check excluded features
            if widget.excluded_features:
                if any(feature in enabled_features for feature in widget.excluded_features):
                    continue
            
            # Check retail type compatibility
            if widget.retail_types and retail_type not in widget.retail_types:
                continue
            
            # Check role permissions
            if widget.roles and user_role and user_role not in widget.roles:
                continue
            
            filtered_widgets.append(widget_id)
        
        return filtered_widgets
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    # Data Provider Methods
    def _provide_sales_summary(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide sales summary data"""
        # This would fetch real data from database
        return {
            'daily_sales': 15420.50,
            'weekly_sales': 108750.25,
            'monthly_sales': 435200.75,
            'daily_orders': 45,
            'weekly_orders': 315,
            'monthly_orders': 1260,
            'growth': {
                'daily': 12.5,
                'weekly': 8.3,
                'monthly': 15.7
            }
        }
    
    def _provide_order_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide order statistics data"""
        return {
            'pending_orders': 12,
            'preparing_orders': 8,
            'ready_orders': 5,
            'completed_orders': 45,
            'cancelled_orders': 2,
            'total_orders': 72
        }
    
    def _provide_top_products(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide top products data"""
        return {
            'products': [
                {'name': 'Burger', 'quantity': 125, 'revenue': 3750.00},
                {'name': 'Pizza', 'quantity': 89, 'revenue': 3560.00},
                {'name': 'Pasta', 'quantity': 67, 'revenue': 2010.00},
                {'name': 'Salad', 'quantity': 54, 'revenue': 1080.00},
                {'name': 'Sandwich', 'quantity': 48, 'revenue': 960.00}
            ]
        }
    
    def _provide_recent_orders(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide recent orders data"""
        return {
            'orders': [
                {'id': 'ORD001', 'customer': 'John Doe', 'amount': 450.50, 'status': 'completed', 'time': '10:30 AM'},
                {'id': 'ORD002', 'customer': 'Jane Smith', 'amount': 320.00, 'status': 'preparing', 'time': '10:25 AM'},
                {'id': 'ORD003', 'customer': 'Bob Johnson', 'amount': 280.75, 'status': 'pending', 'time': '10:20 AM'},
                {'id': 'ORD004', 'customer': 'Alice Brown', 'amount': 520.25, 'status': 'completed', 'time': '10:15 AM'},
                {'id': 'ORD005', 'customer': 'Charlie Wilson', 'amount': 195.00, 'status': 'preparing', 'time': '10:10 AM'}
            ]
        }
    
    def _provide_customer_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide customer statistics data"""
        return {
            'new_customers': 15,
            'returning_customers': 30,
            'loyalty_members': 45,
            'total_customers': 1250,
            'active_today': 45
        }
    
    def _provide_inventory_alerts(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide inventory alerts data"""
        return {
            'alerts': [
                {'item': 'Tomatoes', 'type': 'low_stock', 'current': 5, 'min_required': 20},
                {'item': 'Cheese', 'type': 'low_stock', 'current': 8, 'min_required': 15},
                {'item': 'Bread', 'type': 'out_of_stock', 'current': 0, 'min_required': 25}
            ]
        }
    
    def _provide_table_status(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide table status data"""
        return {
            'total_tables': 20,
            'occupied': 12,
            'available': 6,
            'reserved': 2,
            'occupancy_rate': 60.0
        }
    
    def _provide_kitchen_orders(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide kitchen orders data"""
        return {
            'orders': [
                {'id': 'KOT001', 'table': 'T5', 'items': 3, 'status': 'pending', 'time': '10:35 AM'},
                {'id': 'KOT002', 'table': 'T8', 'items': 2, 'status': 'preparing', 'time': '10:30 AM'},
                {'id': 'KOT003', 'table': 'T3', 'items': 4, 'status': 'ready', 'time': '10:25 AM'},
                {'id': 'KOT004', 'table': 'T12', 'items': 1, 'status': 'preparing', 'time': '10:20 AM'}
            ]
        }
    
    def _provide_low_stock(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide low stock data"""
        return {
            'items': [
                {'name': 'Milk', 'current_stock': 8, 'min_stock': 20, 'unit': 'liters'},
                {'name': 'Eggs', 'current_stock': 15, 'min_stock': 50, 'unit': 'pieces'},
                {'name': 'Bread', 'current_stock': 5, 'min_stock': 25, 'unit': 'loaves'},
                {'name': 'Butter', 'current_stock': 3, 'min_stock': 15, 'unit': 'kg'}
            ]
        }
    
    def _provide_expiry_alerts(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide expiry alerts data"""
        return {
            'items': [
                {'name': 'Yogurt', 'expiry_date': '2023-12-18', 'days_left': 2, 'quantity': 15},
                {'name': 'Cream', 'expiry_date': '2023-12-19', 'days_left': 3, 'quantity': 8},
                {'name': 'Cheese', 'expiry_date': '2023-12-20', 'days_left': 4, 'quantity': 12}
            ]
        }
    
    def _provide_revenue_chart(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Provide revenue chart data"""
        return {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'datasets': [
                {
                    'label': 'This Week',
                    'data': [12000, 15000, 13500, 16000, 18000, 22000, 20000],
                    'borderColor': '#3498db',
                    'backgroundColor': 'rgba(52, 152, 219, 0.1)'
                },
                {
                    'label': 'Last Week',
                    'data': [10000, 12000, 11500, 14000, 15000, 18000, 16000],
                    'borderColor': '#95a5a6',
                    'backgroundColor': 'rgba(149, 165, 166, 0.1)'
                }
            ]
        }
    
    def register_widget(self, widget: DashboardWidget):
        """Register a new widget"""
        self.widgets[widget.widget_id] = widget
    
    def register_layout(self, layout: DashboardLayout):
        """Register a new layout"""
        self.layouts[layout.layout_id] = layout
    
    def register_data_provider(self, provider_name: str, provider_func: Callable):
        """Register a data provider"""
        self.data_providers[provider_name] = provider_func


# Global dashboard manager instance
dashboard_manager = None


def get_dashboard_manager(feature_manager=None) -> DynamicDashboardManager:
    """Get or create global dashboard manager instance"""
    global dashboard_manager
    if dashboard_manager is None:
        dashboard_manager = DynamicDashboardManager(feature_manager)
    return dashboard_manager