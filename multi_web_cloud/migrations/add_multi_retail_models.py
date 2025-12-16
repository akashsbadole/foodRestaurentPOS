"""
Migration script for adding multi-retail models to the database
This script creates all the new tables for the multi-retail POS system
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
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

def migrate():
    """Run the migration"""
    with app.app_context():
        print("Starting multi-retail models migration...")
        
        # Create all tables
        db.create_all()
        print("All tables created successfully!")
        
        # Create indexes for performance
        create_indexes()
        print("Indexes created successfully!")
        
        # Add default data
        add_default_data()
        print("Default data added successfully!")
        
        print("Multi-retail models migration completed successfully!")

def create_indexes():
    """Create indexes for better performance"""
    print("Creating indexes...")
    
    # Product indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_tenant_id ON products(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active)")
    
    # Product category indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_categories_tenant_id ON product_categories(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_categories_parent_id ON product_categories(parent_id)")
    
    # Product variant indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_tenant_id ON product_variants(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_product_id ON product_variants(product_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_variants_sku ON product_variants(sku)")
    
    # Inventory transaction indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_tenant_id ON inventory_transactions(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product_id ON inventory_transactions(product_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_inventory_transactions_transaction_date ON inventory_transactions(transaction_date)")
    
    # Batch lot indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_tenant_id ON batch_lots(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_product_id ON batch_lots(product_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_batch_lots_expiry_date ON batch_lots(expiry_date)")
    
    # Serial number indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_tenant_id ON serial_numbers(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_product_id ON serial_numbers(product_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_serial_numbers_serial_number ON serial_numbers(serial_number)")
    
    # Supplier indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_tenant_id ON suppliers(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_suppliers_is_active ON suppliers(is_active)")
    
    # Purchase order indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_tenant_id ON purchase_orders(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)")
    
    # Tax jurisdiction indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_jurisdictions_tenant_id ON tax_jurisdictions(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_jurisdictions_code ON tax_jurisdictions(code)")
    
    # Tax rate indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_rates_tenant_id ON tax_rates(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_tax_rates_jurisdiction_id ON tax_rates(jurisdiction_id)")
    
    # Warehouse indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_tenant_id ON warehouses(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_is_active ON warehouses(is_active)")
    
    # Warehouse stock indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_tenant_id ON warehouse_stocks(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_warehouse_id ON warehouse_stocks(warehouse_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_product_id ON warehouse_stocks(product_id)")
    
    # Stock transfer indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_tenant_id ON stock_transfers(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_from_warehouse_id ON stock_transfers(from_warehouse_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_to_warehouse_id ON stock_transfers(to_warehouse_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_stock_transfers_status ON stock_transfers(status)")
    
    # Payment method indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_payment_methods_tenant_id ON payment_methods(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_payment_methods_is_active ON payment_methods(is_active)")
    
    # Split payment indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_split_payments_tenant_id ON split_payments(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_split_payments_order_id ON split_payments(order_id)")
    
    # Cash drawer indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_tenant_id ON cash_drawers(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_user_id ON cash_drawers(user_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_cash_drawers_status ON cash_drawers(status)")
    
    # Customer group indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_groups_tenant_id ON customer_groups(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_groups_is_active ON customer_groups(is_active)")
    
    # Customer credit indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_credits_tenant_id ON customer_credits(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_credits_customer_id ON customer_credits(customer_id)")
    
    # Sales return indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_tenant_id ON sales_returns(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_return_number ON sales_returns(return_number)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_returns_status ON sales_returns(status)")
    
    # Enhanced order indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_tenant_id ON enhanced_orders(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_order_number ON enhanced_orders(order_number)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_status ON enhanced_orders(status)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_enhanced_orders_order_date ON enhanced_orders(order_date)")
    
    # Barcode indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_tenant_id ON barcodes(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_barcode_value ON barcodes(barcode_value)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_barcodes_product_id ON barcodes(product_id)")
    
    # Report template indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_templates_tenant_id ON report_templates(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_templates_category ON report_templates(category)")
    
    # Report schedule indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_schedules_tenant_id ON report_schedules(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_report_schedules_next_run ON report_schedules(next_run)")
    
    # Analytics cache indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_tenant_id ON analytics_cache(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_cache_key ON analytics_cache(cache_key)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_analytics_cache_expires_at ON analytics_cache(expires_at)")
    
    # Business metric indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_tenant_id ON business_metrics(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_business_metrics_category ON business_metrics(category)")
    
    # Sales target indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_tenant_id ON sales_targets(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_period_start ON sales_targets(period_start)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_sales_targets_period_end ON sales_targets(period_end)")
    
    # Customer segment indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segments_tenant_id ON customer_segments(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_customer_segments_segment_type ON customer_segments(segment_type)")
    
    # Product performance indexes
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_tenant_id ON product_performances(tenant_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_product_id ON product_performances(product_id)")
    db.engine.execute("CREATE INDEX IF NOT EXISTS idx_product_performances_period_start ON product_performances(period_start)")

def add_default_data():
    """Add default data for the new models"""
    print("Adding default data...")
    
    # Add default product categories
    from models.tenant import Tenant
    
    # Get the first tenant (assuming there's at least one)
    tenant = Tenant.query.first()
    if not tenant:
        print("No tenant found, skipping default data creation")
        return
    
    # Add default product categories
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
        existing = ProductCategory.query.filter_by(name=cat_data["name"], tenant_id=tenant.id).first()
        if not existing:
            category = ProductCategory(
                name=cat_data["name"],
                description=cat_data["description"],
                tenant_id=tenant.id
            )
            db.session.add(category)
    
    # Add default payment methods
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
        existing = PaymentMethod.query.filter_by(name=pm_data["name"], tenant_id=tenant.id).first()
        if not existing:
            payment_method = PaymentMethod(
                name=pm_data["name"],
                method_type=pm_data["method_type"],
                is_active=pm_data["is_active"],
                tenant_id=tenant.id
            )
            db.session.add(payment_method)
    
    # Add default tax jurisdiction
    tax_jurisdictions = [
        {"name": "Default", "code": "DEFAULT", "country": "US", "state": None, "tax_rate": 0.00},
        {"name": "California", "code": "CA", "country": "US", "state": "CA", "tax_rate": 8.75},
        {"name": "New York", "code": "NY", "country": "US", "state": "NY", "tax_rate": 8.00},
        {"name": "Texas", "code": "TX", "country": "US", "state": "TX", "tax_rate": 6.25},
        {"name": "Florida", "code": "FL", "country": "US", "state": "FL", "tax_rate": 6.00}
    ]
    
    for tj_data in tax_jurisdictions:
        existing = TaxJurisdiction.query.filter_by(code=tj_data["code"], tenant_id=tenant.id).first()
        if not existing:
            tax_jurisdiction = TaxJurisdiction(
                name=tj_data["name"],
                code=tj_data["code"],
                country=tj_data["country"],
                state=tj_data["state"],
                tenant_id=tenant.id
            )
            db.session.add(tax_jurisdiction)
            
            # Add default tax rate for this jurisdiction
            tax_rate = TaxRate(
                name=f"Standard Rate - {tj_data['name']}",
                jurisdiction_id=tax_jurisdiction.id,
                rate_type="Percentage",
                rate_value=tj_data["tax_rate"],
                is_active=True,
                tenant_id=tenant.id
            )
            db.session.add(tax_rate)
    
    # Add default warehouse
    warehouse = Warehouse.query.filter_by(name="Main Warehouse", tenant_id=tenant.id).first()
    if not warehouse:
        warehouse = Warehouse(
            name="Main Warehouse",
            code="MAIN",
            address="Main Store Location",
            is_active=True,
            is_default=True,
            tenant_id=tenant.id
        )
        db.session.add(warehouse)
    
    # Add default customer groups
    customer_groups = [
        {"name": "Regular", "description": "Regular customers", "discount_percentage": 0.00},
        {"name": "VIP", "description": "VIP customers", "discount_percentage": 5.00},
        {"name": "Wholesale", "description": "Wholesale customers", "discount_percentage": 10.00}
    ]
    
    for cg_data in customer_groups:
        existing = CustomerGroup.query.filter_by(name=cg_data["name"], tenant_id=tenant.id).first()
        if not existing:
            customer_group = CustomerGroup(
                name=cg_data["name"],
                description=cg_data["description"],
                discount_percentage=cg_data["discount_percentage"],
                is_active=True,
                tenant_id=tenant.id
            )
            db.session.add(customer_group)
    
    # Add default business metrics
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
        existing = BusinessMetric.query.filter_by(name=bm_data["name"], tenant_id=tenant.id).first()
        if not existing:
            business_metric = BusinessMetric(
                name=bm_data["name"],
                category=bm_data["category"],
                metric_type=bm_data["metric_type"],
                unit=bm_data["unit"],
                tenant_id=tenant.id,
                created_by=1  # Assuming admin user has ID 1
            )
            db.session.add(business_metric)
    
    # Add default report templates
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
        existing = ReportTemplate.query.filter_by(name=rt_data["name"], tenant_id=tenant.id).first()
        if not existing:
            report_template = ReportTemplate(
                name=rt_data["name"],
                description=rt_data["description"],
                category=rt_data["category"],
                columns=rt_data["columns"],
                tenant_id=tenant.id,
                created_by=1  # Assuming admin user has ID 1
            )
            db.session.add(report_template)
    
    # Add default dashboard config
    dashboard_config = DashboardConfig.query.filter_by(name="Default Dashboard", tenant_id=tenant.id).first()
    if not dashboard_config:
        dashboard_config = DashboardConfig(
            name="Default Dashboard",
            description="Default dashboard configuration",
            dashboard_type="General",
            widgets='[{"type": "metric", "title": "Daily Sales", "metric_id": 1}, {"type": "chart", "title": "Sales Trend", "chart_type": "line"}]',
            is_default=True,
            is_public=True,
            tenant_id=tenant.id,
            created_by=1  # Assuming admin user has ID 1
        )
        db.session.add(dashboard_config)
    
    db.session.commit()
    print("Default data added successfully!")

if __name__ == "__main__":
    migrate()