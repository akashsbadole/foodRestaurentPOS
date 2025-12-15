#!/usr/bin/env python3
"""
Multi-Tenant Migration Script
Migrates existing single-tenant data to multi-tenant architecture
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings, Customer, Tenant
from migrations.add_multi_tenant_foundation import upgrade as run_migration

def migrate_to_multi_tenant():
    """Migrate existing single-tenant data to multi-tenant"""
    
    print("Starting multi-tenant migration...")
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Run database schema migration
            print("Step 1: Running database schema migration...")
            run_migration()
            print("✅ Database schema migration completed")
            
            # Step 2: Create default tenant if not exists
            print("Step 2: Creating default tenant...")
            default_tenant = Tenant.query.filter_by(id='default').first()
            if not default_tenant:
                default_tenant = Tenant(
                    id='default',
                    name='Default Restaurant',
                    subdomain='default',
                    status='active'
                )
                db.session.add(default_tenant)
                db.session.flush()
                print("✅ Default tenant created")
            else:
                print("✅ Default tenant already exists")
            
            # Step 3: Update existing records with default tenant
            print("Step 3: Updating existing records with default tenant...")
            
            # Update users
            users_updated = db.session.execute(
                "UPDATE users SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {users_updated} users")
            
            # Update categories
            categories_updated = db.session.execute(
                "UPDATE categories SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {categories_updated} categories")
            
            # Update menu items
            menu_items_updated = db.session.execute(
                "UPDATE menu_items SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {menu_items_updated} menu items")
            
            # Update tables
            tables_updated = db.session.execute(
                "UPDATE tables SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {tables_updated} tables")
            
            # Update orders
            orders_updated = db.session.execute(
                "UPDATE orders SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {orders_updated} orders")
            
            # Update order items
            order_items_updated = db.session.execute(
                "UPDATE order_items SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {order_items_updated} order items")
            
            # Update payments
            payments_updated = db.session.execute(
                "UPDATE payments SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {payments_updated} payments")
            
            # Update settings
            settings_updated = db.session.execute(
                "UPDATE settings SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {settings_updated} settings")
            
            # Update customers
            customers_updated = db.session.execute(
                "UPDATE customers SET tenant_id = 'default' WHERE tenant_id IS NULL OR tenant_id = 'default'"
            ).rowcount
            print(f"✅ Updated {customers_updated} customers")
            
            # Step 4: Create tenant settings for default tenant
            print("Step 4: Creating tenant settings for default tenant...")
            from models.tenant import TenantSettings
            
            tenant_settings = TenantSettings.query.filter_by(tenant_id='default').first()
            if not tenant_settings:
                # Get existing restaurant settings
                restaurant_name = Settings.get('restaurant_name', 'Default Restaurant')
                gst_number = Settings.get('gst_number', '')
                contact_email = Settings.get('restaurant_email', '')
                contact_phone = Settings.get('restaurant_phone', '')
                currency = Settings.get('currency_symbol', '₹')
                tax_rate = float(Settings.get('tax_rate', '5.0'))
                
                tenant_settings = TenantSettings(
                    tenant_id='default',
                    restaurant_name=restaurant_name,
                    gst_number=gst_number,
                    contact_email=contact_email,
                    contact_phone=contact_phone,
                    currency=currency.replace('₹', 'INR'),
                    tax_rate=tax_rate
                )
                db.session.add(tenant_settings)
                print("✅ Default tenant settings created")
            else:
                print("✅ Default tenant settings already exist")
            
            # Step 5: Commit all changes
            db.session.commit()
            print("✅ All changes committed successfully")
            
            # Step 6: Verify migration
            print("Step 6: Verifying migration...")
            
            # Verify tenant exists
            tenant_count = Tenant.query.count()
            print(f"✅ Total tenants: {tenant_count}")
            
            # Verify all records have tenant_id
            users_without_tenant = User.query.filter_by(tenant_id=None).count()
            categories_without_tenant = Category.query.filter_by(tenant_id=None).count()
            menu_items_without_tenant = MenuItem.query.filter_by(tenant_id=None).count()
            
            if users_without_tenant == 0 and categories_without_tenant == 0 and menu_items_without_tenant == 0:
                print("✅ Migration verification successful - all records have tenant_id")
            else:
                print(f"❌ Migration verification failed - records without tenant_id: "
                      f"users={users_without_tenant}, categories={categories_without_tenant}, "
                      f"menu_items={menu_items_without_tenant}")
                return False
            
            print("\n🎉 Multi-tenant migration completed successfully!")
            print("\nNext steps:")
            print("1. Update application configuration to enable multi-tenancy")
            print("2. Implement tenant identification middleware")
            print("3. Update APIs to use tenant-aware queries")
            print("4. Test tenant isolation")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

def rollback_multi_tenant():
    """Rollback multi-tenant changes (use with caution!)"""
    
    print("WARNING: This will rollback all multi-tenant changes!")
    print("This action cannot be undone. Type 'ROLLBACK' to continue:")
    
    confirmation = input().strip()
    if confirmation != 'ROLLBACK':
        print("Rollback cancelled.")
        return False
    
    print("Starting multi-tenant rollback...")
    app = create_app()
    
    with app.app_context():
        try:
            # Remove tenant_id columns (optional - keep for future use)
            # tables_to_rollback = ['users', 'categories', 'menu_items', 'tables', 'orders', 'order_items', 'payments', 'settings', 'customers']
            
            # Drop tenant tables
            print("Dropping tenant tables...")
            db.session.execute("DROP TABLE IF EXISTS tenant_usage")
            db.session.execute("DROP TABLE IF EXISTS tenant_feature_flags")
            db.session.execute("DROP TABLE IF EXISTS tenant_subscriptions")
            db.session.execute("DROP TABLE IF EXISTS subscription_plans")
            db.session.execute("DROP TABLE IF EXISTS tenant_settings")
            db.session.execute("DROP TABLE IF EXISTS tenants")
            
            db.session.commit()
            print("✅ Multi-tenant rollback completed")
            
            return True
            
        except Exception as e:
            print(f"❌ Rollback failed: {str(e)}")
            db.session.rollback()
            return False

def verify_migration():
    """Verify multi-tenant migration status"""
    
    print("Verifying multi-tenant migration status...")
    app = create_app()
    
    with app.app_context():
        try:
            # Check if tenant table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'tenants' in tables:
                print("✅ Tenant table exists")
                
                # Check tenant count
                tenant_count = Tenant.query.count()
                print(f"✅ Total tenants: {tenant_count}")
                
                # Check default tenant
                default_tenant = Tenant.query.filter_by(id='default').first()
                if default_tenant:
                    print("✅ Default tenant exists")
                    print(f"   Name: {default_tenant.name}")
                    print(f"   Subdomain: {default_tenant.subdomain}")
                    print(f"   Status: {default_tenant.status}")
                else:
                    print("❌ Default tenant not found")
                
                # Check if records have tenant_id
                users_without_tenant = User.query.filter_by(tenant_id=None).count()
                categories_without_tenant = Category.query.filter_by(tenant_id=None).count()
                menu_items_without_tenant = MenuItem.query.filter_by(tenant_id=None).count()
                
                if users_without_tenant == 0 and categories_without_tenant == 0 and menu_items_without_tenant == 0:
                    print("✅ All records have tenant_id")
                    print("🎉 Multi-tenant migration is complete!")
                    return True
                else:
                    print(f"❌ Some records missing tenant_id: "
                          f"users={users_without_tenant}, categories={categories_without_tenant}, "
                          f"menu_items={menu_items_without_tenant}")
                    return False
            else:
                print("❌ Tenant table does not exist - migration not completed")
                return False
                
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python migrate_to_multi_tenant.py migrate    - Run migration")
        print("  python migrate_to_multi_tenant.py rollback  - Rollback changes")
        print("  python migrate_to_multi_tenant.py verify    - Verify migration status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'migrate':
        success = migrate_to_multi_tenant()
        sys.exit(0 if success else 1)
    elif command == 'rollback':
        success = rollback_multi_tenant()
        sys.exit(0 if success else 1)
    elif command == 'verify':
        success = verify_migration()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: migrate, rollback, verify")
        sys.exit(1)