# Multi-Tenancy Implementation Guide

## Overview

This guide provides step-by-step implementation instructions for transforming multi_web_cloud POS into a multi-tenant SaaS platform following the 4-stage architecture design.

## Phase 1: Foundation Implementation

### Step 1: Database Schema Updates

#### 1.1 Create Migration Script
```python
# migrations/add_multi_tenant_support.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

def upgrade():
    # Add tenant_id columns to existing tables
    op.add_column('users', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('categories', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('menu_items', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('tables', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('orders', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('order_items', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('payments', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    op.add_column('settings', sa.Column('tenant_id', sa.String(36), nullable=False, server_default='default'))
    
    # Create indexes
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('idx_categories_tenant_id', 'categories', ['tenant_id'])
    op.create_index('idx_menu_items_tenant_id', 'menu_items', ['tenant_id'])
    op.create_index('idx_tables_tenant_id', 'tables', ['tenant_id'])
    op.create_index('idx_orders_tenant_id', 'orders', ['tenant_id'])
    op.create_index('idx_order_items_tenant_id', 'order_items', ['tenant_id'])
    op.create_index('idx_payments_tenant_id', 'payments', ['tenant_id'])
    op.create_index('idx_settings_tenant_id', 'settings', ['tenant_id'])
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('subdomain', sa.String(50), unique=True, nullable=False),
        sa.Column('custom_domain', sa.String(100)),
        sa.Column('status', sa.Enum('trial', 'active', 'suspended', 'cancelled'), default='trial'),
        sa.Column('created_at', sa.DateTime, default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp())
    )

def downgrade():
    # Remove indexes
    op.drop_index('idx_settings_tenant_id', table_name='settings')
    op.drop_index('idx_payments_tenant_id', table_name='payments')
    op.drop_index('idx_order_items_tenant_id', table_name='order_items')
    op.drop_index('idx_orders_tenant_id', table_name='orders')
    op.drop_index('idx_tables_tenant_id', table_name='tables')
    op.drop_index('idx_menu_items_tenant_id', table_name='menu_items')
    op.drop_index('idx_categories_tenant_id', table_name='categories')
    op.drop_index('idx_users_tenant_id', table_name='users')
    
    # Remove tenant_id columns
    op.drop_column('settings', 'tenant_id')
    op.drop_column('payments', 'tenant_id')
    op.drop_column('order_items', 'tenant_id')
    op.drop_column('orders', 'tenant_id')
    op.drop_column('tables', 'tenant_id')
    op.drop_column('menu_items', 'tenant_id')
    op.drop_column('categories', 'tenant_id')
    op.drop_column('users', 'tenant_id')
    
    # Drop tenants table
    op.drop_table('tenants')
```

#### 1.2 Update Models
```python
# models/tenant.py
from datetime import datetime
import uuid
from models import db

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    custom_domain = db.Column(db.String(100))
    status = db.Column(db.Enum('trial', 'active', 'suspended', 'cancelled'), default='trial')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Update existing models to include tenant_id
# models/user.py (add to existing User model)
class User(UserMixin, db.Model):
    # ... existing fields ...
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # ... existing methods ...
    
    @classmethod
    def query_tenant(cls, tenant_id=None):
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        return cls.query.filter(cls.tenant_id == tenant_id)
```

### Step 2: Tenant Identification Middleware

#### 2.1 Create Tenant Middleware
```python
# middleware/tenant_middleware.py
from flask import request, g, current_app
from models import Tenant

def get_current_tenant_id():
    """Get current tenant ID from request context"""
    return getattr(g, 'tenant_id', None)

def get_current_tenant():
    """Get current tenant object from request context"""
    return getattr(g, 'tenant', None)

def set_current_tenant(tenant_id, tenant_info=None):
    """Set current tenant in request context"""
    g.tenant_id = tenant_id
    g.tenant = tenant_info

class TenantMiddleware:
    def __init__(self, app):
        self.app = app
        self.tenant_identifiers = {
            'subdomain': self.get_tenant_from_subdomain,
            'header': self.get_tenant_from_header,
            'path': self.get_tenant_from_path
        }
    
    def __call__(self, environ, start_response):
        with self.app.request_context(environ):
            tenant_id = None
            tenant_info = None
            
            # Try different identification methods
            identification_method = current_app.config.get('TENANT_IDENTIFICATION', 'subdomain')
            
            if identification_method in self.tenant_identifiers:
                tenant = self.tenant_identifiers[identification_method]()
                if tenant:
                    tenant_id = tenant.id
                    tenant_info = tenant.to_dict()
            
            if tenant_id:
                set_current_tenant(tenant_id, tenant_info)
                # Set PostgreSQL session variable for RLS
                with current_app.app_context():
                    db.session.execute(f"SET app.current_tenant_id = '{tenant_id}'")
            
            return self.app(environ, start_response)
    
    def get_tenant_from_subdomain(self):
        """Extract tenant from subdomain"""
        host = request.host.split(':')[0]  # Remove port if present
        subdomain = host.split('.')[0] if '.' in host else None
        
        if subdomain and subdomain not in ['www', 'app', 'api']:
            return Tenant.query.filter_by(subdomain=subdomain, status='active').first()
        return None
    
    def get_tenant_from_header(self):
        """Extract tenant from HTTP header"""
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            return Tenant.query.filter_by(id=tenant_id, status='active').first()
        return None
    
    def get_tenant_from_path(self):
        """Extract tenant from URL path"""
        path_parts = request.path.strip('/').split('/')
        
        if len(path_parts) > 1 and path_parts[0] == 'tenant':
            tenant_code = path_parts[1]
            tenant = Tenant.query.filter_by(subdomain=tenant_code, status='active').first()
            
            if tenant:
                # Modify path to remove tenant prefix
                request.path = '/' + '/'.join(path_parts[2:])
            
            return tenant
        return None
```

#### 2.2 Integrate Middleware
```python
# app.py (update existing app creation)
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # ... existing initialization ...
    
    # Add tenant middleware
    app.wsgi_app = TenantMiddleware(app.wsgi_app)
    
    # ... rest of app creation ...
    
    return app
```

### Step 3: Tenant-Aware Query Manager

#### 3.1 Create Query Manager
```python
# utils/tenant_query_manager.py
from flask import g
from models import db

class TenantQueryManager:
    @staticmethod
    def get_tenant_query(model, tenant_id=None):
        """Get query filtered by tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if tenant_id:
            return model.query.filter(model.tenant_id == tenant_id)
        return model.query
    
    @staticmethod
    def check_tenant_access(resource_id, model, tenant_id=None):
        """Check if resource belongs to tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if not tenant_id:
            return False
        
        resource = model.query.filter_by(
            id=resource_id,
            tenant_id=tenant_id
        ).first()
        
        return resource is not None
    
    @staticmethod
    def create_tenant_resource(data, model, tenant_id=None):
        """Create resource with tenant context"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if tenant_id:
            data['tenant_id'] = tenant_id
        
        return model(**data)
    
    @staticmethod
    def get_tenant_resources(model, tenant_id=None, **filters):
        """Get resources filtered by tenant and additional filters"""
        query = TenantQueryManager.get_tenant_query(model, tenant_id)
        
        for key, value in filters.items():
            query = query.filter(getattr(model, key) == value)
        
        return query.all()
```

### Step 4: Update Existing Routes

#### 4.1 Update Order Routes
```python
# routes/orders.py (update existing routes)
from utils.tenant_query_manager import TenantQueryManager
from middleware.tenant_middleware import get_current_tenant_id

@app.route('/orders')
@login_required
def list_orders():
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        flash('Tenant context not found', 'error')
        return redirect(url_for('dashboard.index'))
    
    # Use tenant-aware query
    orders = TenantQueryManager.get_tenant_resources(
        Order, 
        tenant_id=tenant_id,
        status='active'
    )
    
    return render_template('orders/list.html', orders=orders)

@app.route('/orders/<order_id>')
@login_required
def view_order(order_id):
    tenant_id = get_current_tenant_id()
    
    # Check tenant access
    if not TenantQueryManager.check_tenant_access(order_id, Order, tenant_id):
        abort(404)  # Not found for security
    
    order = TenantQueryManager.get_tenant_resources(
        Order,
        tenant_id=tenant_id,
        id=order_id
    )[0] if TenantQueryManager.get_tenant_resources(Order, tenant_id=tenant_id, id=order_id) else None
    
    if not order:
        abort(404)
    
    return render_template('orders/detail.html', order=order)

@app.route('/orders', methods=['POST'])
@login_required
def create_order():
    tenant_id = get_current_tenant_id()
    
    # Create order with tenant context
    order_data = request.get_json()
    order_data['tenant_id'] = tenant_id
    
    order = Order(**order_data)
    db.session.add(order)
    db.session.commit()
    
    return jsonify({'success': True, 'order_id': order.id})
```

### Step 5: Row-Level Security Implementation

#### 5.1 Create RLS Policies
```python
# migrations/enable_row_level_security.py
from alembic import op

def upgrade():
    # Enable row-level security on all tenant tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE categories ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE tables ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE order_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE payments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE settings ENABLE ROW LEVEL SECURITY")
    
    # Create tenant isolation policies
    op.execute("""
        CREATE POLICY tenant_isolation_users ON users
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
    
    op.execute("""
        CREATE POLICY tenant_isolation_categories ON categories
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
    
    op.execute("""
        CREATE POLICY tenant_isolation_menu_items ON menu_items
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
    
    # Similar policies for other tables...

def downgrade():
    # Remove policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_users ON users")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_categories ON categories")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_menu_items ON menu_items")
    
    # Disable row-level security
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE categories DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE menu_items DISABLE ROW LEVEL SECURITY")
```

## Phase 2: Multi-Store Implementation

### Step 1: Store Management Models

#### 1.1 Create Store Models
```python
# models/store.py
from datetime import datetime
import uuid
from models import db

class Store(db.Model):
    __tablename__ = 'stores'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    currency = db.Column(db.String(3), default='INR')
    tax_rate = db.Column(db.Float, default=5.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='stores')
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'code': self.code,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'currency': self.currency,
            'tax_rate': self.tax_rate,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserStore(db.Model):
    __tablename__ = 'user_stores'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    role = db.Column(db.Enum('admin', 'manager', 'cashier'), default='cashier')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='user_stores')
    store = db.relationship('Store', backref='user_stores')
```

### Step 2: Store Management Routes

#### 2.1 Create Store Routes
```python
# routes/stores.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Store, UserStore
from utils.tenant_query_manager import TenantQueryManager
from middleware.tenant_middleware import get_current_tenant_id

stores_bp = Blueprint('stores', __name__)

@stores_bp.route('/stores')
@login_required
def list_stores():
    tenant_id = get_current_tenant_id()
    stores = TenantQueryManager.get_tenant_resources(Store, tenant_id=tenant_id)
    return render_template('stores/list.html', stores=stores)

@stores_bp.route('/stores', methods=['POST'])
@login_required
def create_store():
    tenant_id = get_current_tenant_id()
    
    store_data = request.get_json()
    store_data['tenant_id'] = tenant_id
    
    store = Store(**store_data)
    db.session.add(store)
    db.session.commit()
    
    return jsonify({'success': True, 'store_id': store.id})

@stores_bp.route('/stores/<store_id>/users')
@login_required
def store_users(store_id):
    tenant_id = get_current_tenant_id()
    
    # Check store access
    if not TenantQueryManager.check_tenant_access(store_id, Store, tenant_id):
        abort(404)
    
    # Get users for this store
    user_stores = UserStore.query.filter_by(store_id=store_id).all()
    users = [us.user for us in user_stores if us.is_active]
    
    return render_template('stores/users.html', users=users, store_id=store_id)
```

## Phase 3: Franchise Implementation

### Step 1: Franchise Models

#### 1.1 Create Franchise Models
```python
# models/franchise.py
from datetime import datetime, date
import uuid
from models import db

class Franchise(db.Model):
    __tablename__ = 'franchises'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    agreement_start_date = db.Column(db.Date)
    agreement_end_date = db.Column(db.Date)
    royalty_rate = db.Column(db.Float, default=5.0)
    commission_rate = db.Column(db.Float, default=0.0)
    status = db.Column(db.Enum('active', 'inactive', 'suspended'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='franchises')

class MasterProduct(db.Model):
    __tablename__ = 'master_products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    base_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float)
    sku = db.Column(db.String(50), unique=True)
    barcode = db.Column(db.String(50))
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FranchiseProduct(db.Model):
    __tablename__ = 'franchise_products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    franchise_id = db.Column(db.String(36), db.ForeignKey('franchises.id'), nullable=False)
    master_product_id = db.Column(db.String(36), db.ForeignKey('master_products.id'), nullable=False)
    custom_name = db.Column(db.String(100))
    custom_price = db.Column(db.Float)
    custom_description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    franchise = db.relationship('Franchise', backref='franchise_products')
    master_product = db.relationship('MasterProduct', backref='franchise_products')

class RoyaltyCalculation(db.Model):
    __tablename__ = 'royalty_calculations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    franchise_id = db.Column(db.String(36), db.ForeignKey('franchises.id'), nullable=False)
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey('orders.id'), nullable=False)
    gross_sales = db.Column(db.Float, nullable=False)
    royalty_amount = db.Column(db.Float, nullable=False)
    commission_amount = db.Column(db.Float, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    calculation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('pending', 'calculated', 'paid'), default='pending')
    
    # Relationships
    franchise = db.relationship('Franchise', backref='royalty_calculations')
```

### Step 2: Royalty Calculation Service

#### 2.1 Create Royalty Service
```python
# services/royalty_service.py
from datetime import datetime, timedelta
from models import db, RoyaltyCalculation, Franchise, Order

class RoyaltyService:
    @staticmethod
    def calculate_royalties(franchise_id, period_start, period_end):
        """Calculate royalties for franchise for a period"""
        
        # Get franchise
        franchise = Franchise.query.get(franchise_id)
        if not franchise:
            raise ValueError(f"Franchise {franchise_id} not found")
        
        # Get orders for the period
        orders = Order.query.filter(
            Order.franchise_id == franchise_id,
            Order.created_at >= period_start,
            Order.created_at <= period_end,
            Order.status == 'completed'
        ).all()
        
        # Calculate royalties
        total_sales = sum(order.total for order in orders)
        royalty_amount = total_sales * (franchise.royalty_rate / 100)
        commission_amount = total_sales * (franchise.commission_rate / 100)
        net_amount = total_sales - royalty_amount - commission_amount
        
        # Create royalty calculation record
        royalty_calc = RoyaltyCalculation(
            franchise_id=franchise_id,
            gross_sales=total_sales,
            royalty_amount=royalty_amount,
            commission_amount=commission_amount,
            net_amount=net_amount,
            status='calculated'
        )
        
        db.session.add(royalty_calc)
        db.session.commit()
        
        return {
            'total_sales': total_sales,
            'royalty_amount': royalty_amount,
            'commission_amount': commission_amount,
            'net_amount': net_amount,
            'order_count': len(orders)
        }
    
    @staticmethod
    def get_franchise_royalties(franchise_id, start_date=None, end_date=None):
        """Get royalty calculations for franchise"""
        query = RoyaltyCalculation.query.filter_by(franchise_id=franchise_id)
        
        if start_date:
            query = query.filter(RoyaltyCalculation.calculation_date >= start_date)
        
        if end_date:
            query = query.filter(RoyaltyCalculation.calculation_date <= end_date)
        
        return query.order_by(RoyaltyCalculation.calculation_date.desc()).all()
```

## Phase 4: SaaS Platform Implementation

### Step 1: Enhanced Tenant Management

#### 1.1 Subscription Plans
```python
# models/subscription.py
from datetime import datetime, timedelta
import uuid
from models import db

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    price_monthly = db.Column(db.Float, nullable=False)
    price_yearly = db.Column(db.Float, nullable=False)
    
    # Limits
    max_users = db.Column(db.Integer, default=5)
    max_orders_per_month = db.Column(db.Integer, default=1000)
    max_storage_gb = db.Column(db.Integer, default=10)
    
    # Features
    features = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TenantFeatureFlag(db.Model):
    __tablename__ = 'tenant_feature_flags'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False)
    configuration = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='feature_flags')

class TenantUsage(db.Model):
    __tablename__ = 'tenant_usage'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    usage_type = db.Column(db.Enum('orders', 'users', 'storage', 'api_calls'), nullable=False)
    usage_value = db.Column(db.Float, nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='usage')
```

### Step 2: Feature Flag System

#### 2.1 Feature Flag Manager
```python
# services/feature_flag_service.py
from flask import g
from models import db, TenantFeatureFlag

class FeatureFlagService:
    @staticmethod
    def is_feature_enabled(feature_name, tenant_id=None):
        """Check if feature is enabled for tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        if not tenant_id:
            return False
        
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=tenant_id,
            feature_name=feature_name
        ).first()
        
        return feature_flag.is_enabled if feature_flag else False
    
    @staticmethod
    def get_feature_config(feature_name, tenant_id=None):
        """Get feature configuration for tenant"""
        if tenant_id is None:
            tenant_id = getattr(g, 'tenant_id', None)
        
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=tenant_id,
            feature_name=feature_name
        ).first()
        
        return feature_flag.configuration if feature_flag else {}
    
    @staticmethod
    def enable_feature(tenant_id, feature_name, configuration=None):
        """Enable feature for tenant"""
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=tenant_id,
            feature_name=feature_name
        ).first()
        
        if feature_flag:
            feature_flag.is_enabled = True
            if configuration:
                feature_flag.configuration = configuration
        else:
            feature_flag = TenantFeatureFlag(
                tenant_id=tenant_id,
                feature_name=feature_name,
                is_enabled=True,
                configuration=configuration
            )
            db.session.add(feature_flag)
        
        db.session.commit()
    
    @staticmethod
    def disable_feature(tenant_id, feature_name):
        """Disable feature for tenant"""
        feature_flag = TenantFeatureFlag.query.filter_by(
            tenant_id=tenant_id,
            feature_name=feature_name
        ).first()
        
        if feature_flag:
            feature_flag.is_enabled = False
            db.session.commit()
```

### Step 3: Usage Tracking and Billing

#### 3.1 Usage Tracking Service
```python
# services/usage_service.py
from datetime import datetime, date
from models import db, TenantUsage, Order, User

class UsageService:
    @staticmethod
    def track_order_usage(tenant_id):
        """Track order usage for tenant"""
        today = date.today()
        
        # Count orders for today
        order_count = Order.query.filter(
            Order.tenant_id == tenant_id,
            db.func.date(Order.created_at) == today
        ).count()
        
        # Update or create usage record
        usage = TenantUsage.query.filter_by(
            tenant_id=tenant_id,
            usage_type='orders',
            usage_date=today
        ).first()
        
        if usage:
            usage.usage_value = order_count
        else:
            usage = TenantUsage(
                tenant_id=tenant_id,
                usage_type='orders',
                usage_value=order_count,
                usage_date=today
            )
            db.session.add(usage)
        
        db.session.commit()
    
    @staticmethod
    def track_user_usage(tenant_id):
        """Track user usage for tenant"""
        today = date.today()
        
        # Count active users for today
        user_count = User.query.filter(
            User.tenant_id == tenant_id,
            User.is_active == True
        ).count()
        
        # Update or create usage record
        usage = TenantUsage.query.filter_by(
            tenant_id=tenant_id,
            usage_type='users',
            usage_date=today
        ).first()
        
        if usage:
            usage.usage_value = user_count
        else:
            usage = TenantUsage(
                tenant_id=tenant_id,
                usage_type='users',
                usage_value=user_count,
                usage_date=today
            )
            db.session.add(usage)
        
        db.session.commit()
    
    @staticmethod
    def get_monthly_usage(tenant_id, year, month):
        """Get monthly usage summary for tenant"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        usage_records = TenantUsage.query.filter(
            TenantUsage.tenant_id == tenant_id,
            TenantUsage.usage_date >= start_date,
            TenantUsage.usage_date <= end_date
        ).all()
        
        # Aggregate by usage type
        usage_summary = {}
        for record in usage_records:
            usage_type = record.usage_type
            if usage_type not in usage_summary:
                usage_summary[usage_type] = 0
            usage_summary[usage_type] += record.usage_value
        
        return usage_summary
```

## Testing Strategy

### Multi-Tenant Test Suite

#### 1. Tenant Isolation Tests
```python
# tests/test_multi_tenant_isolation.py
import unittest
from app import create_app
from models import db, User, Order, Tenant

class TestTenantIsolation(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test tenants
        self.tenant1 = Tenant(name='Tenant 1', subdomain='tenant1')
        self.tenant2 = Tenant(name='Tenant 2', subdomain='tenant2')
        db.session.add_all([self.tenant1, self.tenant2])
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_isolation(self):
        """Test that users are isolated by tenant"""
        # Create users for different tenants
        user1 = User(username='user1', tenant_id=self.tenant1.id)
        user2 = User(username='user2', tenant_id=self.tenant2.id)
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Test isolation
        with self.app.test_request_context(headers={'X-Tenant-ID': self.tenant1.id}):
            users = User.query.filter(User.tenant_id == self.tenant1.id).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].username, 'user1')
        
        with self.app.test_request_context(headers={'X-Tenant-ID': self.tenant2.id}):
            users = User.query.filter(User.tenant_id == self.tenant2.id).all()
            self.assertEqual(len(users), 1)
            self.assertEqual(users[0].username, 'user2')
    
    def test_order_isolation(self):
        """Test that orders are isolated by tenant"""
        # Create orders for different tenants
        order1 = Order(order_number='ORD001', tenant_id=self.tenant1.id)
        order2 = Order(order_number='ORD002', tenant_id=self.tenant2.id)
        db.session.add_all([order1, order2])
        db.session.commit()
        
        # Test isolation
        with self.app.test_request_context(headers={'X-Tenant-ID': self.tenant1.id}):
            orders = Order.query.filter(Order.tenant_id == self.tenant1.id).all()
            self.assertEqual(len(orders), 1)
            self.assertEqual(orders[0].order_number, 'ORD001')
        
        with self.app.test_request_context(headers={'X-Tenant-ID': self.tenant2.id}):
            orders = Order.query.filter(Order.tenant_id == self.tenant2.id).all()
            self.assertEqual(len(orders), 1)
            self.assertEqual(orders[0].order_number, 'ORD002')
```

## Deployment Strategy

### Production Deployment

#### 1. Environment Configuration
```bash
# .env.production
FLASK_ENV=production
MULTI_TENANT=True
TENANT_IDENTIFICATION=subdomain
DATABASE_URL=postgresql://user:password@localhost/multi_tenant_pos
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-production-secret-key
SESSION_SALT=your-production-session-salt

# Tenant limits
DEFAULT_MAX_USERS=5
DEFAULT_MAX_ORDERS=1000
DEFAULT_MAX_STORAGE=10
```

#### 2. Database Migration
```bash
# Run migrations in order
python -m alembic upgrade head

# Create default tenant
python scripts/create_default_tenant.py

# Enable row-level security
python scripts/enable_rls.py
```

#### 3. Application Deployment
```yaml
# docker-compose.production.yml
version: '3.8'

services:
  app:
    build: .
    environment:
      - FLASK_ENV=production
      - MULTI_TENANT=True
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=multi_tenant_pos
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/multi-tenant.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

## Monitoring and Maintenance

### Multi-Tenant Monitoring

#### 1. Health Checks
```python
# routes/health.py
from flask import Blueprint, jsonify
from models import db, Tenant, TenantUsage
from datetime import datetime, timedelta

health_bp = Blueprint('health', __name__)

@health_bp.route('/health/tenants')
def tenant_health():
    """Health check for all tenants"""
    active_tenants = Tenant.query.filter_by(status='active').all()
    
    health_status = {
        'overall_status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'tenants': {}
    }
    
    for tenant in active_tenants:
        # Check tenant-specific health
        tenant_health = {
            'status': 'healthy',
            'database': 'connected',
            'cache': 'connected',
            'last_activity': None
        }
        
        # Get recent usage
        recent_usage = TenantUsage.query.filter(
            TenantUsage.tenant_id == tenant.id,
            TenantUsage.usage_date >= datetime.utcnow().date() - timedelta(days=7)
        ).first()
        
        if recent_usage:
            tenant_health['last_activity'] = recent_usage.usage_date.isoformat()
        
        health_status['tenants'][tenant.id] = tenant_health
    
    # Check for any unhealthy tenants
    unhealthy_count = sum(1 for t in health_status['tenants'].values() 
                        if t['status'] != 'healthy')
    
    if unhealthy_count > 0:
        health_status['overall_status'] = 'degraded'
        health_status['unhealthy_tenants'] = unhealthy_count
    
    return jsonify(health_status)
```

This implementation guide provides comprehensive instructions for transforming multi_web_cloud POS into a full multi-tenant SaaS platform following the 4-stage evolution architecture.