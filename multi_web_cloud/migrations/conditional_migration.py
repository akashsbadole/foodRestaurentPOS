"""
Conditional migration script for multi-retail models
This script only creates tables based on enabled feature flags
"""

import os
import sys
from datetime import datetime

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    # Feature management
    FeatureDefinition, TenantFeatureFlag,
    
    # Product models
    Product, ProductCategory, ProductVariant, ProductAttribute, Attribute,
    
    # Inventory models
    InventoryTransaction, StockAdjustment, LowStockAlert, ReorderPoint,
    
    # Tracking models
    BatchLot, SerialNumber,
    
    # Supplier models
    Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt,
    
    # Tax models
    TaxJurisdiction, TaxRate, TaxRule, TaxExemption,
    
    # Warehouse models
    Warehouse, WarehouseStock, StockTransfer,
    
    # Enhanced payment models
    PaymentMethod, SplitPayment, EMIPayment, WalletPayment,
    
    # Cash management models
    CashDrawer, DenominationCount, CashTransaction,
    
    # Enhanced customer models
    CustomerGroup, CustomerCredit, CustomerNote, PurchaseHistory,
    
    # Returns and exchange models
    SalesReturn, ReturnItem, ProductExchange, ExchangeItem,
    
    # Enhanced order models
    EnhancedOrder, EnhancedOrderItem, OrderStatusHistory, EnhancedPayment,
    
    # Barcode models
    Barcode, BarcodeScan, BarcodeLabel, BarcodePrintJob, BarcodePrintItem,
    
    # Reporting models
    ReportTemplate, ReportSchedule, ReportExecution, AnalyticsCache, DashboardConfig,
    
    # Business intelligence models
    BusinessMetric, MetricValue, SalesTarget, CustomerSegment, 
    CustomerSegmentMember, ProductPerformance
)

# Mapping of feature flags to models
FEATURE_MODEL_MAPPING = {
    'FEATURE_PRODUCT_MANAGEMENT': [
        Product, ProductCategory, ProductVariant, ProductAttribute, Attribute
    ],
    'FEATURE_INVENTORY_MANAGEMENT': [
        InventoryTransaction, StockAdjustment, LowStockAlert, ReorderPoint
    ],
    'FEATURE_BATCH_TRACKING': [
        BatchLot
    ],
    'FEATURE_SERIAL_TRACKING': [
        SerialNumber
    ],
    'FEATURE_PURCHASING': [
        Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt
    ],
    'FEATURE_TAX_MANAGEMENT': [
        TaxJurisdiction, TaxRate, TaxRule, TaxExemption
    ],
    'FEATURE_WAREHOUSE': [
        Warehouse, WarehouseStock, StockTransfer
    ],
    'FEATURE_ENHANCED_PAYMENTS': [
        PaymentMethod, SplitPayment, EMIPayment, WalletPayment
    ],
    'FEATURE_CASH_MANAGEMENT': [
        CashDrawer, DenominationCount, CashTransaction
    ],
    'FEATURE_CUSTOMER_CRM': [
        CustomerGroup, CustomerCredit, CustomerNote, PurchaseHistory
    ],
    'FEATURE_SALES_RETURN': [
        SalesReturn, ReturnItem
    ],
    'FEATURE_EXCHANGE': [
        ProductExchange, ExchangeItem
    ],
    'FEATURE_ENHANCED_ORDERS': [
        EnhancedOrder, EnhancedOrderItem, OrderStatusHistory, EnhancedPayment
    ],
    'FEATURE_BARCODE': [
        Barcode, BarcodeScan
    ],
    'FEATURE_BARCODE_LABEL': [
        BarcodeLabel, BarcodePrintJob, BarcodePrintItem
    ],
    'FEATURE_REPORTING': [
        ReportTemplate, ReportExecution
    ],
    'FEATURE_SCHEDULED_REPORTS': [
        ReportSchedule
    ],
    'FEATURE_ANALYTICS': [
        AnalyticsCache
    ],
    'FEATURE_DASHBOARD': [
        DashboardConfig
    ],
    'FEATURE_BUSINESS_INTELLIGENCE': [
        BusinessMetric, MetricValue, SalesTarget, CustomerSegment, 
        CustomerSegmentMember, ProductPerformance
    ]
}

def is_feature_enabled(feature_code, tenant_id=None):
    """Check if a feature is enabled for a tenant or globally"""
    # Check if feature is defined
    feature = FeatureDefinition.query.filter_by(code=feature_code).first()
    if not feature:
        return False
    
    # If no tenant specified, check if feature is globally enabled
    if not tenant_id:
        return feature.is_enabled
    
    # Check tenant-specific feature flag
    tenant_feature = TenantFeatureFlag.query.filter_by(
        tenant_id=tenant_id,
        feature_id=feature.id
    ).first()
    
    if tenant_feature:
        return tenant_feature.is_enabled
    
    # Fall back to global feature setting
    return feature.is_enabled

def get_enabled_features(tenant_id=None):
    """Get list of enabled features for a tenant or globally"""
    enabled_features = []
    
    for feature_code in FEATURE_MODEL_MAPPING.keys():
        if is_feature_enabled(feature_code, tenant_id):
            enabled_features.append(feature_code)
    
    return enabled_features

def create_models_for_features(feature_codes):
    """Create database tables for specified features"""
    created_tables = []
    
    for feature_code in feature_codes:
        if feature_code in FEATURE_MODEL_MAPPING:
            models = FEATURE_MODEL_MAPPING[feature_code]
            for model in models:
                try:
                    model.__table__.create(db.engine, checkfirst=True)
                    table_name = model.__tablename__
                    if table_name not in created_tables:
                        created_tables.append(table_name)
                        print(f"Created table: {table_name}")
                except Exception as e:
                    print(f"Error creating table {model.__tablename__}: {str(e)}")
    
    return created_tables

def create_indexes_for_features(feature_codes):
    """Create indexes for specified features"""
    print("Creating indexes for enabled features...")
    
    # Product indexes
    if 'FEATURE_PRODUCT_MANAGEMENT' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_tenant_id ON products(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_categories_tenant_id ON product_categories(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_categories_parent_id ON product_categories(parent_id)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_tenant_id ON product_variants(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku)")
    
    # Inventory indexes
    if 'FEATURE_INVENTORY_MANAGEMENT' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_tenant_id ON inventory_transactions(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product_id ON inventory_transactions(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_transaction_date ON inventory_transactions(transaction_date)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_tenant_id ON low_stock_alerts(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_product_id ON low_stock_alerts(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_low_stock_alerts_is_resolved ON low_stock_alerts(is_resolved)")
    
    # Batch tracking indexes
    if 'FEATURE_BATCH_TRACKING' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_tenant_id ON batch_lots(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_product_id ON batch_lots(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_expiry_date ON batch_lots(expiry_date)")
    
    # Serial tracking indexes
    if 'FEATURE_SERIAL_TRACKING' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_tenant_id ON serial_numbers(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_product_id ON serial_numbers(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_serial_number ON serial_numbers(serial_number)")
    
    # Supplier indexes
    if 'FEATURE_PURCHASING' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_tenant_id ON suppliers(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_is_active ON suppliers(is_active)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_tenant_id ON purchase_orders(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)")
    
    # Tax indexes
    if 'FEATURE_TAX_MANAGEMENT' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_jurisdictions_tenant_id ON tax_jurisdictions(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_jurisdictions_code ON tax_jurisdictions(code)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_rates_tenant_id ON tax_rates(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_rates_jurisdiction_id ON tax_rates(jurisdiction_id)")
    
    # Warehouse indexes
    if 'FEATURE_WAREHOUSE' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_tenant_id ON warehouses(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_is_active ON warehouses(is_active)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_tenant_id ON warehouse_stocks(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_warehouse_id ON warehouse_stocks(warehouse_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_product_id ON warehouse_stocks(product_id)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_tenant_id ON stock_transfers(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_from_warehouse_id ON stock_transfers(from_warehouse_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_to_warehouse_id ON stock_transfers(to_warehouse_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_status ON stock_transfers(status)")
    
    # Enhanced payment indexes
    if 'FEATURE_ENHANCED_PAYMENTS' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_payment_methods_tenant_id ON payment_methods(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_payment_methods_is_active ON payment_methods(is_active)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_split_payments_tenant_id ON split_payments(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_split_payments_order_id ON split_payments(order_id)")
    
    # Cash management indexes
    if 'FEATURE_CASH_MANAGEMENT' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_tenant_id ON cash_drawers(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_user_id ON cash_drawers(user_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_status ON cash_drawers(status)")
    
    # Customer CRM indexes
    if 'FEATURE_CUSTOMER_CRM' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_groups_tenant_id ON customer_groups(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_groups_is_active ON customer_groups(is_active)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_credits_tenant_id ON customer_credits(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_credits_customer_id ON customer_credits(customer_id)")
    
    # Return and exchange indexes
    if 'FEATURE_SALES_RETURN' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_tenant_id ON sales_returns(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_return_number ON sales_returns(return_number)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_status ON sales_returns(status)")
    
    if 'FEATURE_EXCHANGE' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_exchanges_tenant_id ON product_exchanges(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_exchanges_exchange_number ON product_exchanges(exchange_number)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_exchanges_status ON product_exchanges(status)")
    
    # Enhanced order indexes
    if 'FEATURE_ENHANCED_ORDERS' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_tenant_id ON enhanced_orders(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_order_number ON enhanced_orders(order_number)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_status ON enhanced_orders(status)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_order_date ON enhanced_orders(order_date)")
    
    # Barcode indexes
    if 'FEATURE_BARCODE' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_tenant_id ON barcodes(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_barcode_value ON barcodes(barcode_value)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_product_id ON barcodes(product_id)")
    
    if 'FEATURE_BARCODE_LABEL' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcode_labels_tenant_id ON barcode_labels(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcode_print_jobs_tenant_id ON barcode_print_jobs(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcode_print_jobs_status ON barcode_print_jobs(status)")
    
    # Reporting indexes
    if 'FEATURE_REPORTING' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_templates_tenant_id ON report_templates(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_templates_category ON report_templates(category)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_executions_tenant_id ON report_executions(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_executions_execution_id ON report_executions(execution_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_executions_status ON report_executions(status)")
    
    if 'FEATURE_SCHEDULED_REPORTS' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_schedules_tenant_id ON report_schedules(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run)")
    
    # Analytics indexes
    if 'FEATURE_ANALYTICS' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_tenant_id ON analytics_cache(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_cache_key ON analytics_cache(cache_key)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires_at ON analytics_cache(expires_at)")
    
    # Dashboard indexes
    if 'FEATURE_DASHBOARD' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_configs_tenant_id ON dashboard_configs(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_dashboard_configs_is_default ON dashboard_configs(is_default)")
    
    # Business intelligence indexes
    if 'FEATURE_BUSINESS_INTELLIGENCE' in feature_codes:
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_tenant_id ON business_metrics(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_category ON business_metrics(category)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_metric_values_tenant_id ON metric_values(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_metric_values_metric_id ON metric_values(metric_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_metric_values_period_start ON metric_values(period_start)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_tenant_id ON sales_targets(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_period_start ON sales_targets(period_start)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_period_end ON sales_targets(period_end)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segments_tenant_id ON customer_segments(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segments_segment_type ON customer_segments(segment_type)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segment_members_tenant_id ON customer_segment_members(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segment_members_segment_id ON customer_segment_members(segment_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segment_members_customer_id ON customer_segment_members(customer_id)")
        
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_tenant_id ON product_performances(tenant_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_product_id ON product_performances(product_id)")
        db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_period_start ON product_performances(period_start)")

def migrate(tenant_id=None):
    """Run conditional migration"""
    with app.app_context():
        print(f"Starting conditional migration for tenant {tenant_id or 'global'}...")
        
        # Get enabled features
        enabled_features = get_enabled_features(tenant_id)
        print(f"Enabled features: {', '.join(enabled_features)}")
        
        # Create tables for enabled features
        created_tables = create_models_for_features(enabled_features)
        print(f"Created {len(created_tables)} tables")
        
        # Create indexes for enabled features
        create_indexes_for_features(enabled_features)
        print("Indexes created successfully!")
        
        # Add default data if this is a global migration
        if not tenant_id:
            add_default_data(enabled_features)
            print("Default data added successfully!")
        
        print("Conditional migration completed successfully!")

def add_default_data(enabled_features):
    """Add default data for enabled features"""
    print("Adding default data for enabled features...")
    
    from models.tenant import Tenant
    
    # Get first tenant (assuming there's at least one)
    tenant = Tenant.query.first()
    if not tenant:
        print("No tenant found, skipping default data creation")
        return
    
    # Add default data based on enabled features
    if 'FEATURE_PRODUCT_MANAGEMENT' in enabled_features:
        add_default_product_categories(tenant.id)
    
    if 'FEATURE_ENHANCED_PAYMENTS' in enabled_features:
        add_default_payment_methods(tenant.id)
    
    if 'FEATURE_TAX_MANAGEMENT' in enabled_features:
        add_default_tax_jurisdictions(tenant.id)
    
    if 'FEATURE_WAREHOUSE' in enabled_features:
        add_default_warehouse(tenant.id)
    
    if 'FEATURE_CUSTOMER_CRM' in enabled_features:
        add_default_customer_groups(tenant.id)
    
    if 'FEATURE_BUSINESS_INTELLIGENCE' in enabled_features:
        add_default_business_metrics(tenant.id)
    
    if 'FEATURE_REPORTING' in enabled_features:
        add_default_report_templates(tenant.id)
    
    if 'FEATURE_DASHBOARD' in enabled_features:
        add_default_dashboard_config(tenant.id)
    
    db.session.commit()
    print("Default data added successfully!")

def add_default_product_categories(tenant_id):
    """Add default product categories"""
    categories = [
        {"name": "Food & Beverages", "description": "Food and beverage items"},
        {"name": "Electronics", "description": "Electronic devices and accessories"},
        {"name": "Clothing", "description": "Apparel and clothing items"},
        {"name": "Home & Garden", "description": "Home and garden products"},
        {"name": "Sports & Outdoors", "description": "Sports and outdoor equipment"},
        {"name": "Books & Media", "description": "Books, movies, and media"},
        {"name": "Toys & Games", "description": "Toys and games"},
        {"name": "Health & Beauty", "description": "Health and beauty products"},
        {"name": "Automotive", "description": "Automotive parts and accessories"},
        {"name": "Office Supplies", "description": "Office and school supplies"}
    ]
    
    for cat_data in categories:
        existing = ProductCategory.query.filter_by(name=cat_data["name"], tenant_id=tenant_id).first()
        if not existing:
            category = ProductCategory(
                name=cat_data["name"],
                description=cat_data["description"],
                tenant_id=tenant_id
            )
            db.session.add(category)

def add_default_payment_methods(tenant_id):
    """Add default payment methods"""
    payment_methods = [
        {"name": "Cash", "method_type": "Cash", "is_active": True},
        {"name": "Credit Card", "method_type": "Card", "is_active": True},
        {"name": "Debit Card", "method_type": "Card", "is_active": True},
        {"name": "Mobile Wallet", "method_type": "Wallet", "is_active": True},
        {"name": "Bank Transfer", "method_type": "Bank", "is_active": True},
        {"name": "Check", "method_type": "Check", "is_active": True},
        {"name": "Gift Card", "method_type": "GiftCard", "is_active": True},
        {"name": "Store Credit", "method_type": "Credit", "is_active": True}
    ]
    
    for pm_data in payment_methods:
        existing = PaymentMethod.query.filter_by(name=pm_data["name"], tenant_id=tenant_id).first()
        if not existing:
            payment_method = PaymentMethod(
                name=pm_data["name"],
                method_type=pm_data["method_type"],
                is_active=pm_data["is_active"],
                tenant_id=tenant_id
            )
            db.session.add(payment_method)

def add_default_tax_jurisdictions(tenant_id):
    """Add default tax jurisdictions"""
    tax_jurisdictions = [
        {"name": "Default", "code": "DEFAULT", "country": "US", "state": None, "tax_rate": 0.00},
        {"name": "California", "code": "CA", "country": "US", "state": "CA", "tax_rate": 8.75},
        {"name": "New York", "code": "NY", "country": "US", "state": "NY", "tax_rate": 8.00},
        {"name": "Texas", "code": "TX", "country": "US", "state": "TX", "tax_rate": 6.25},
        {"name": "Florida", "code": "FL", "country": "US", "state": "FL", "tax_rate": 6.00}
    ]
    
    for tj_data in tax_jurisdictions:
        existing = TaxJurisdiction.query.filter_by(code=tj_data["code"], tenant_id=tenant_id).first()
        if not existing:
            tax_jurisdiction = TaxJurisdiction(
                name=tj_data["name"],
                code=tj_data["code"],
                country=tj_data["country"],
                state=tj_data["state"],
                tenant_id=tenant_id
            )
            db.session.add(tax_jurisdiction)
            
            # Add default tax rate for this jurisdiction
            tax_rate = TaxRate(
                name=f"Standard Rate - {tj_data['name']}",
                jurisdiction_id=tax_jurisdiction.id,
                rate_type="Percentage",
                rate_value=tj_data["tax_rate"],
                is_active=True,
                tenant_id=tenant_id
            )
            db.session.add(tax_rate)

def add_default_warehouse(tenant_id):
    """Add default warehouse"""
    warehouse = Warehouse.query.filter_by(name="Main Warehouse", tenant_id=tenant_id).first()
    if not warehouse:
        warehouse = Warehouse(
            name="Main Warehouse",
            code="MAIN",
            address="Main Store Location",
            is_active=True,
            is_default=True,
            tenant_id=tenant_id
        )
        db.session.add(warehouse)

def add_default_customer_groups(tenant_id):
    """Add default customer groups"""
    customer_groups = [
        {"name": "Regular", "description": "Regular customers", "discount_percentage": 0.00},
        {"name": "VIP", "description": "VIP customers", "discount_percentage": 5.00},
        {"name": "Wholesale", "description": "Wholesale customers", "discount_percentage": 10.00}
    ]
    
    for cg_data in customer_groups:
        existing = CustomerGroup.query.filter_by(name=cg_data["name"], tenant_id=tenant_id).first()
        if not existing:
            customer_group = CustomerGroup(
                name=cg_data["name"],
                description=cg_data["description"],
                discount_percentage=cg_data["discount_percentage"],
                is_active=True,
                tenant_id=tenant_id
            )
            db.session.add(customer_group)

def add_default_business_metrics(tenant_id):
    """Add default business metrics"""
    business_metrics = [
        {"name": "Daily Sales", "category": "Sales", "metric_type": "Value", "unit": "Currency"},
        {"name": "Total Orders", "category": "Sales", "metric_type": "Count", "unit": "Items"},
        {"name": "Average Order Value", "category": "Sales", "metric_type": "Value", "unit": "Currency"},
        {"name": "Customer Count", "category": "Customer", "metric_type": "Count", "unit": "Items"},
        {"name": "Inventory Value", "category": "Inventory", "metric_type": "Value", "unit": "Currency"},
        {"name": "Low Stock Items", "category": "Inventory", "metric_type": "Count", "unit": "Items"},
        {"name": "Profit Margin", "category": "Financial", "metric_type": "Percentage", "unit": "Percentage"}
    ]
    
    for bm_data in business_metrics:
        existing = BusinessMetric.query.filter_by(name=bm_data["name"], tenant_id=tenant_id).first()
        if not existing:
            business_metric = BusinessMetric(
                name=bm_data["name"],
                category=bm_data["category"],
                metric_type=bm_data["metric_type"],
                unit=bm_data["unit"],
                tenant_id=tenant_id,
                created_by=1  # Assuming admin user has ID 1
            )
            db.session.add(business_metric)

def add_default_report_templates(tenant_id):
    """Add default report templates"""
    report_templates = [
        {
            "name": "Sales Summary",
            "description": "Daily sales summary report",
            "category": "Sales",
            "columns": '[{"name": "Date", "field": "order_date"}, {"name": "Total Sales", "field": "total_amount"}, {"name": "Order Count", "field": "order_count"}]'
        },
        {
            "name": "Inventory Report",
            "description": "Current inventory status",
            "category": "Inventory",
            "columns": '[{"name": "Product", "field": "product_name"}, {"name": "Stock", "field": "quantity"}, {"name": "Value", "field": "total_value"}]'
        },
        {
            "name": "Customer Report",
            "description": "Customer activity report",
            "category": "Customers",
            "columns": '[{"name": "Customer", "field": "customer_name"}, {"name": "Orders", "field": "order_count"}, {"name": "Total Spent", "field": "total_spent"}]'
        }
    ]
    
    for rt_data in report_templates:
        existing = ReportTemplate.query.filter_by(name=rt_data["name"], tenant_id=tenant_id).first()
        if not existing:
            report_template = ReportTemplate(
                name=rt_data["name"],
                description=rt_data["description"],
                category=rt_data["category"],
                columns=rt_data["columns"],
                tenant_id=tenant_id,
                created_by=1  # Assuming admin user has ID 1
            )
            db.session.add(report_template)

def add_default_dashboard_config(tenant_id):
    """Add default dashboard config"""
    dashboard_config = DashboardConfig.query.filter_by(name="Default Dashboard", tenant_id=tenant_id).first()
    if not dashboard_config:
        dashboard_config = DashboardConfig(
            name="Default Dashboard",
            description="Default dashboard configuration",
            dashboard_type="General",
            widgets='[{"type": "metric", "title": "Daily Sales", "metric_id": 1}, {"type": "chart", "title": "Sales Trend", "chart_type": "line"}]',
            is_default=True,
            is_public=True,
            tenant_id=tenant_id,
            created_by=1  # Assuming admin user has ID 1
        )
        db.session.add(dashboard_config)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Conditional migration for multi-retail models')
    parser.add_argument('--tenant-id', type=int, help='Tenant ID for conditional migration (optional)')
    
    args = parser.parse_args()
    
    migrate(tenant_id=args.tenant_id)