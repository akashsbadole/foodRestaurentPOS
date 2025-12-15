"""
Multi-Tenant Foundation Migration
Adds tenant support to existing database schema
"""

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers
revision = 'add_multi_tenant_foundation'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Add multi-tenant support to database"""
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('subdomain', sa.String(50), unique=True, nullable=False),
        sa.Column('custom_domain', sa.String(100), nullable=True),
        sa.Column('status', sa.Enum('trial', 'active', 'suspended', 'cancelled', name='tenant_status'), default='trial'),
        sa.Column('plan_id', sa.String(36), nullable=True),
        sa.Column('database_name', sa.String(100), nullable=True),
        sa.Column('database_host', sa.String(100), nullable=True),
        sa.Column('database_port', sa.Integer, default=5432),
        sa.Column('database_user', sa.String(50), nullable=True),
        sa.Column('database_password', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp())
    )
    
    # Create tenant_settings table
    op.create_table('tenant_settings',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('restaurant_name', sa.String(100), nullable=True),
        sa.Column('gst_number', sa.String(15), nullable=True),
        sa.Column('contact_email', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('logo_url', sa.String(255), nullable=True),
        sa.Column('primary_color', sa.String(7), default='#FF6B6B'),
        sa.Column('secondary_color', sa.String(7), default='#4ECDC4'),
        sa.Column('currency', sa.String(3), default='INR'),
        sa.Column('tax_rate', sa.Float, default=5.0),
        sa.Column('service_charge', sa.Float, default=0.0),
        sa.Column('enable_crm', sa.Boolean, default=True),
        sa.Column('enable_loyalty', sa.Boolean, default=True),
        sa.Column('enable_offline', sa.Boolean, default=True),
        sa.Column('enable_reports', sa.Boolean, default=True),
        sa.Column('razorpay_key_id', sa.String(100), nullable=True),
        sa.Column('razorpay_key_secret', sa.String(100), nullable=True),
        sa.Column('email_settings', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp())
    )
    
    # Create subscription_plans table
    op.create_table('subscription_plans',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('price_monthly', sa.Float, nullable=False),
        sa.Column('price_yearly', sa.Float, nullable=False),
        sa.Column('max_users', sa.Integer, default=5),
        sa.Column('max_orders_per_month', sa.Integer, default=1000),
        sa.Column('max_storage_gb', sa.Integer, default=10),
        sa.Column('features', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp())
    )
    
    # Create tenant_subscriptions table
    op.create_table('tenant_subscriptions',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('plan_id', sa.String(36), sa.ForeignKey('subscription_plans.id'), nullable=False),
        sa.Column('status', sa.Enum('active', 'cancelled', 'expired', 'suspended', name='subscription_status'), default='active'),
        sa.Column('billing_cycle', sa.Enum('monthly', 'yearly', name='billing_cycle'), default='monthly'),
        sa.Column('started_at', sa.DateTime, default=sa.func.current_timestamp()),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('cancelled_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp())
    )
    
    # Create tenant_feature_flags table
    op.create_table('tenant_feature_flags',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('feature_name', sa.String(100), nullable=False),
        sa.Column('is_enabled', sa.Boolean, default=False),
        sa.Column('configuration', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp())
    )
    
    # Create tenant_usage table
    op.create_table('tenant_usage',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('usage_type', sa.Enum('orders', 'users', 'storage', 'api_calls', name='usage_type'), nullable=False),
        sa.Column('usage_value', sa.Float, nullable=False),
        sa.Column('usage_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp())
    )
    
    # Add tenant_id columns to existing tables
    tables_to_update = [
        ('users', 'user'),
        ('categories', 'category'),
        ('menu_items', 'menu_item'),
        ('tables', 'table'),
        ('orders', 'order'),
        ('order_items', 'order_item'),
        ('payments', 'payment'),
        ('settings', 'setting'),
        ('customers', 'customer'),
        ('loyalty_tiers', 'loyalty_tier'),
        ('loyalty_programs', 'loyalty_program'),
        ('points_transactions', 'points_transaction'),
        ('rewards', 'reward'),
        ('reward_redemptions', 'reward_redemption'),
        ('customer_feedback', 'customer_feedback'),
        ('referrals', 'referral')
    ]
    
    for table_name, entity_name in tables_to_update:
        # Add tenant_id column
        op.add_column(table_name, sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
        
        # Create index for tenant_id
        op.create_index(f'idx_{table_name}_tenant_id', table_name, ['tenant_id'])
        
        # Create unique constraint for tenant + entity (where applicable)
        if table_name in ['users', 'categories', 'menu_items']:
            if table_name == 'users':
                op.create_unique_constraint(f'uq_{table_name}_tenant_username', table_name, ['tenant_id', 'username'])
            elif table_name == 'categories':
                op.create_unique_constraint(f'uq_{table_name}_tenant_name', table_name, ['tenant_id', 'name'])
            elif table_name == 'menu_items':
                op.create_unique_constraint(f'uq_{table_name}_tenant_name', table_name, ['tenant_id', 'name'])
    
    # Create default tenant
    op.execute("""
        INSERT INTO tenants (id, name, subdomain, status) 
        VALUES ('default', 'Default Restaurant', 'default', 'active')
    """)
    
    # Create default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (id, name, code, price_monthly, price_yearly, max_users, max_orders_per_month, max_storage_gb, features) VALUES
        ('basic', 'Basic', 'basic', 999.0, 9999.0, 5, 1000, 10, '{"crm": false, "loyalty": false, "reports": true, "offline": true}'),
        ('pro', 'Professional', 'pro', 1999.0, 19999.0, 20, 5000, 50, '{"crm": true, "loyalty": true, "reports": true, "offline": true}'),
        ('enterprise', 'Enterprise', 'enterprise', 4999.0, 49999.0, 100, 20000, 200, '{"crm": true, "loyalty": true, "reports": true, "offline": true, "api_access": true, "custom_integrations": true}')
    """)
    
    # Update existing records to belong to default tenant
    for table_name, _ in tables_to_update:
        op.execute(f"UPDATE {table_name} SET tenant_id = 'default' WHERE tenant_id = 'default'")

def downgrade():
    """Remove multi-tenant support from database"""
    
    # Remove tenant_id columns from existing tables
    tables_to_update = [
        'users', 'categories', 'menu_items', 'tables', 'orders', 'order_items',
        'payments', 'settings', 'customers', 'loyalty_tiers', 'loyalty_programs',
        'points_transactions', 'rewards', 'reward_redemptions', 'customer_feedback', 'referrals'
    ]
    
    for table_name in tables_to_update:
        # Drop indexes
        op.drop_index(f'idx_{table_name}_tenant_id', table_name=table_name)
        
        # Drop unique constraints
        if table_name in ['users', 'categories', 'menu_items']:
            if table_name == 'users':
                op.drop_constraint(f'uq_{table_name}_tenant_username', table_name, type_='unique')
            elif table_name in ['categories', 'menu_items']:
                op.drop_constraint(f'uq_{table_name}_tenant_name', table_name, type_='unique')
        
        # Drop tenant_id column
        op.drop_column(table_name, 'tenant_id')
    
    # Drop tenant-related tables
    op.drop_table('tenant_usage')
    op.drop_table('tenant_feature_flags')
    op.drop_table('tenant_subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('tenant_settings')
    op.drop_table('tenants')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS tenant_status")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS billing_cycle")
    op.execute("DROP TYPE IF EXISTS usage_type")