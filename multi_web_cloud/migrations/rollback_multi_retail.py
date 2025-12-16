"""
Rollback script for multi-retail models
This script removes all multi-retail tables and data
"""

import os
import sys
from datetime import datetime

# Add parent directory to path so we can import from app
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

# List of tables to drop in order (respecting foreign key dependencies)
TABLES_TO_DROP = [
    # Business Intelligence (depends on other tables)
    'customer_segment_members',
    'product_performances',
    'metric_values',
    'sales_targets',
    'customer_segments',
    'business_metrics',
    
    # Reporting
    'report_executions',
    'report_schedules',
    'analytics_cache',
    'dashboard_configs',
    'report_templates',
    
    # Barcode
    'barcode_print_items',
    'barcode_print_jobs',
    'barcode_scans',
    'barcode_labels',
    'barcodes',
    
    # Returns and Exchanges
    'exchange_items',
    'product_exchanges',
    'return_items',
    'sales_returns',
    
    # Enhanced Orders
    'enhanced_payments',
    'order_status_histories',
    'enhanced_order_items',
    'enhanced_orders',
    
    # Customer Enhancements
    'purchase_histories',
    'customer_notes',
    'customer_credits',
    'customer_groups',
    
    # Cash Management
    'cash_transactions',
    'denomination_counts',
    'cash_drawers',
    
    # Enhanced Payments
    'wallet_payments',
    'emi_payments',
    'split_payments',
    'payment_methods',
    
    # Warehouse
    'stock_transfers',
    'warehouse_stocks',
    'warehouses',
    
    # Tax
    'tax_exemptions',
    'tax_rules',
    'tax_rates',
    'tax_jurisdictions',
    
    # Supplier
    'purchase_receipts',
    'purchase_order_items',
    'purchase_orders',
    'suppliers',
    
    # Tracking
    'serial_numbers',
    'batch_lots',
    
    # Inventory
    'reorder_points',
    'low_stock_alerts',
    'stock_adjustments',
    'inventory_transactions',
    
    # Product
    'product_attributes',
    'attributes',
    'product_variants',
    'products',
    'product_categories'
]

def drop_tables():
    """Drop all multi-retail tables"""
    print("Dropping multi-retail tables...")
    
    with app.app_context():
        # Drop tables in reverse order of creation to respect foreign key constraints
        for table_name in reversed(TABLES_TO_DROP):
            try:
                # Check if table exists
                result = db.engine.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if result.fetchone():
                    print(f"Dropping table: {table_name}")
                    db.engine.execute(f"DROP TABLE {table_name}")
                else:
                    print(f"Table {table_name} does not exist, skipping")
            except Exception as e:
                print(f"Error dropping table {table_name}: {str(e)}")
        
        db.session.commit()
        print("All multi-retail tables dropped successfully!")

def drop_indexes():
    """Drop indexes created for multi-retail models"""
    print("Dropping indexes...")
    
    with app.app_context():
        # List of indexes to drop
        indexes_to_drop = [
            # Product indexes
            'idx_products_tenant_id',
            'idx_products_sku',
            'idx_products_barcode',
            'idx_products_is_active',
            'idx_product_categories_tenant_id',
            'idx_product_categories_parent_id',
            'idx_product_variants_tenant_id',
            'idx_product_variants_product_id',
            'idx_product_variants_sku',
            
            # Inventory indexes
            'idx_inventory_transactions_tenant_id',
            'idx_inventory_transactions_product_id',
            'idx_inventory_transactions_transaction_date',
            'idx_low_stock_alerts_tenant_id',
            'idx_low_stock_alerts_product_id',
            'idx_low_stock_alerts_is_resolved',
            
            # Batch lot indexes
            'idx_batch_lots_tenant_id',
            'idx_batch_lots_product_id',
            'idx_batch_lots_expiry_date',
            
            # Serial number indexes
            'idx_serial_numbers_tenant_id',
            'idx_serial_numbers_product_id',
            'idx_serial_numbers_serial_number',
            
            # Supplier indexes
            'idx_suppliers_tenant_id',
            'idx_suppliers_is_active',
            'idx_purchase_orders_tenant_id',
            'idx_purchase_orders_supplier_id',
            'idx_purchase_orders_status',
            
            # Tax indexes
            'idx_tax_jurisdictions_tenant_id',
            'idx_tax_jurisdictions_code',
            'idx_tax_rates_tenant_id',
            'idx_tax_rates_jurisdiction_id',
            
            # Warehouse indexes
            'idx_warehouses_tenant_id',
            'idx_warehouses_is_active',
            'idx_warehouse_stocks_tenant_id',
            'idx_warehouse_stocks_warehouse_id',
            'idx_warehouse_stocks_product_id',
            'idx_stock_transfers_tenant_id',
            'idx_stock_transfers_from_warehouse_id',
            'idx_stock_transfers_to_warehouse_id',
            'idx_stock_transfers_status',
            
            # Payment indexes
            'idx_payment_methods_tenant_id',
            'idx_payment_methods_is_active',
            'idx_split_payments_tenant_id',
            'idx_split_payments_order_id',
            
            # Cash management indexes
            'idx_cash_drawers_tenant_id',
            'idx_cash_drawers_user_id',
            'idx_cash_drawers_status',
            
            # Customer indexes
            'idx_customer_groups_tenant_id',
            'idx_customer_groups_is_active',
            'idx_customer_credits_tenant_id',
            'idx_customer_credits_customer_id',
            
            # Return indexes
            'idx_sales_returns_tenant_id',
            'idx_sales_returns_return_number',
            'idx_sales_returns_status',
            'idx_product_exchanges_tenant_id',
            'idx_product_exchanges_exchange_number',
            'idx_product_exchanges_status',
            
            # Enhanced order indexes
            'idx_enhanced_orders_tenant_id',
            'idx_enhanced_orders_order_number',
            'idx_enhanced_orders_status',
            'idx_enhanced_orders_order_date',
            
            # Barcode indexes
            'idx_barcodes_tenant_id',
            'idx_barcodes_barcode_value',
            'idx_barcodes_product_id',
            'idx_barcode_labels_tenant_id',
            'idx_barcode_print_jobs_tenant_id',
            'idx_barcode_print_jobs_status',
            
            # Reporting indexes
            'idx_report_templates_tenant_id',
            'idx_report_templates_category',
            'idx_report_executions_tenant_id',
            'idx_report_executions_execution_id',
            'idx_report_executions_status',
            'idx_report_schedules_tenant_id',
            'idx_report_schedules_next_run',
            
            # Analytics indexes
            'idx_analytics_cache_tenant_id',
            'idx_analytics_cache_cache_key',
            'idx_analytics_cache_expires_at',
            'idx_dashboard_configs_tenant_id',
            'idx_dashboard_configs_is_default',
            
            # Business intelligence indexes
            'idx_business_metrics_tenant_id',
            'idx_business_metrics_category',
            'idx_metric_values_tenant_id',
            'idx_metric_values_metric_id',
            'idx_metric_values_period_start',
            'idx_sales_targets_tenant_id',
            'idx_sales_targets_period_start',
            'idx_sales_targets_period_end',
            'idx_customer_segments_tenant_id',
            'idx_customer_segments_segment_type',
            'idx_customer_segment_members_tenant_id',
            'idx_customer_segment_members_segment_id',
            'idx_customer_segment_members_customer_id',
            'idx_product_performances_tenant_id',
            'idx_product_performances_product_id',
            'idx_product_performances_period_start'
        ]
        
        for index_name in indexes_to_drop:
            try:
                print(f"Dropping index: {index_name}")
                db.engine.execute(f"DROP INDEX IF EXISTS {index_name}")
            except Exception as e:
                print(f"Error dropping index {index_name}: {str(e)}")
        
        db.session.commit()
        print("All indexes dropped successfully!")

def backup_data():
    """Create backup of existing data before rollback"""
    print("Creating backup of existing data...")
    
    with app.app_context():
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"multi_retail_backup_{timestamp}.sql")
        
        try:
            # Export data to SQL file
            with open(backup_file, 'w') as f:
                for line in db.engine.iterdump():
                    # Only include tables we're about to drop
                    for table_name in TABLES_TO_DROP:
                        if f"CREATE TABLE {table_name}" in line or f"INSERT INTO {table_name}" in line:
                            f.write(line)
                            break
            
            print(f"Backup created at: {backup_file}")
            return True
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False

def confirm_rollback():
    """Confirm rollback with user"""
    print("\n" + "="*60)
    print("WARNING: This will permanently delete all multi-retail data!")
    print("This includes products, inventory, orders, customers, and all other")
    print("multi-retail specific data. This action cannot be undone.")
    print("="*60)
    
    response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
    return response.lower() == 'yes'

def rollback():
    """Run rollback process"""
    if not confirm_rollback():
        print("Rollback cancelled by user.")
        return
    
    print("\nStarting rollback process...")
    
    # Create backup before rollback
    if not backup_data():
        print("Failed to create backup. Aborting rollback.")
        return
    
    # Drop indexes first
    drop_indexes()
    
    # Drop tables
    drop_tables()
    
    print("\nRollback completed successfully!")
    print("The system has been reverted to the original restaurant POS state.")
    print("All multi-retail data has been removed.")

if __name__ == "__main__":
    rollback()