
# Multi-Tenancy Architecture Design for Multi-Web-Cloud POS

## Executive Summary

This document outlines a comprehensive multi-tenancy architecture for the multi_web_cloud POS system, designed to evolve through 4 stages over a 6-month period using an incremental migration approach with shared database and row-level security.

## Current State Analysis

### Existing Application Structure
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (development), PostgreSQL (production target)
- **Current Models**: User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings
- **Authentication**: Flask-Login with role-based access control
- **Features**: Restaurant POS with CRM, Loyalty, Payment processing

### Current Multi-Tenancy Status
- **Status**: No multi-tenancy implemented yet
- **Documentation**: Comprehensive multi-tenancy guide exists
- **Tests**: Multi-tenancy test suite available but not implemented
- **Models**: No tenant_id columns in current models

---

## Stage 1: Single Store (Current State) - Month 1

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Single Tenant POS                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │   Users     │ │   Orders    │ │   Menu      │     │
│  │             │ │             │ │             │     │
│  │ - Admin     │ │ - Orders    │ │ - Items     │     │
│  │ - Staff     │ │ - Payments  │ │ - Categories│     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Current Implementation
- **Database**: Single database with all tables
- **Authentication**: Role-based (admin, cashier, manager)
- **Features**: Complete restaurant POS functionality
- **Configuration**: Settings table for app configuration

### Migration Requirements
1. **Add tenant_id columns** to all existing models
2. **Implement tenant context** middleware
3. **Update all queries** to include tenant filtering
4. **Add tenant management** interface
5. **Implement row-level security** policies

### Database Schema Changes
```sql
-- Add tenant_id to existing tables
ALTER TABLE users ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE categories ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE menu_items ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE tables ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE orders ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE order_items ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE payments ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';
ALTER TABLE settings ADD COLUMN tenant_id VARCHAR(36) NOT NULL DEFAULT 'default';

-- Create indexes for performance
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_categories_tenant_id ON categories(tenant_id);
CREATE INDEX idx_menu_items_tenant_id ON menu_items(tenant_id);
CREATE INDEX idx_tables_tenant_id ON tables(tenant_id);
CREATE INDEX idx_orders_tenant_id ON orders(tenant_id);
CREATE INDEX idx_order_items_tenant_id ON order_items(tenant_id);
CREATE INDEX idx_payments_tenant_id ON payments(tenant_id);
CREATE INDEX idx_settings_tenant_id ON settings(tenant_id);
```

---

## Stage 2: Multi-Store (Same Owner) - Months 2-3

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                Multi-Store Architecture                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │  Store A    │ │  Store B    │ │  Store C    │     │
│  │             │ │             │ │             │     │
│  │ - Local     │ │ - Local     │ │ - Local     │     │
│  │   Orders    │ │   Orders    │ │   Orders    │     │
│  │ - Local     │ │ - Local     │ │ - Local     │     │
│  │   Menu      │ │   Menu      │ │   Menu      │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                Shared Resources                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │   Users     │ │  Products   │ │   Reports   │     │
│  │ (Shared)    │ │ (Shared)    │ │ (Consolid-  │     │
│  │             │ │             │ │  ated)      │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Shared User Management**: Users can access multiple stores
2. **Store-Specific Menu**: Each store has its own menu items
3. **Consolidated Reporting**: Cross-store analytics and reporting
4. **Central Configuration**: Shared settings across stores
5. **Store Transfers**: Inventory and data transfers between stores

### New Models Required
```python
# Store Management
class Store(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    currency = db.Column(db.String(3), default='INR')
    tax_rate = db.Column(db.Float, default=5.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# User Store Permissions
class UserStore(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    role = db.Column(db.Enum('admin', 'manager', 'cashier'), default='cashier')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Store Transfers
class StoreTransfer(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    to_store_id = db.Column(db.String(36), db.ForeignKey('stores.id'), nullable=False)
    item_id = db.Column(db.String(36), db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected', 'completed'), default='pending')
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
```

### Database Schema Changes
```sql
-- Create stores table
CREATE TABLE stores (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    currency VARCHAR(3) DEFAULT 'INR',
    tax_rate FLOAT DEFAULT 5.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_store junction table
CREATE TABLE user_stores (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    store_id VARCHAR(36) NOT NULL,
    role ENUM('admin', 'manager', 'cashier') DEFAULT 'cashier',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (store_id) REFERENCES stores(id)
);

-- Update existing tables to use store_id instead of tenant_id
ALTER TABLE orders ADD COLUMN store_id VARCHAR(36);
ALTER TABLE menu_items ADD COLUMN store_id VARCHAR(36);
ALTER TABLE tables ADD COLUMN store_id VARCHAR(36);

-- Create store_transfers table
CREATE TABLE store_transfers (
    id VARCHAR(36) PRIMARY KEY,
    from_store_id VARCHAR(36) NOT NULL,
    to_store_id VARCHAR(36) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    quantity INTEGER NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (from_store_id) REFERENCES stores(id),
    FOREIGN KEY (to_store_id) REFERENCES stores(id),
    FOREIGN KEY (item_id) REFERENCES menu_items(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

---

## Stage 3: Franchise Model - Months 4-5

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                Franchise Architecture                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │ Franchisee  │ │ Franchisee  │ │ Franchisee  │     │
│  │     A       │ │     B       │ │     C       │     │
│  │             │ │             │ │             │     │
│  │ - Local     │ │ - Local     │ │ - Local     │     │
│  │   Orders    │ │   Orders    │ │   Orders    │     │
│  │ - Custom    │ │ - Custom    │ │ - Custom    │     │
│  │   Menu      │ │   Menu      │ │   Menu      │     │
│  │ - Local     │ │ - Local     │ │ - Local     │     │
│  │   Reports   │ │   Reports   │ │   Reports   │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                Central Franchise Management                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │   Master    │ │   Central   │ │  Royalty    │     │
│  │  Catalog    │ │  Products  │ │  Tracking  │     │
│  │             │ │             │ │             │     │
│  │ - Base      │ │ - Shared    │ │ - Commission│     │
│  │   Items     │ │   Inventory │ │ - Reports   │     │
│  │ - Branding  │ │ - Pricing   │ │ - Payments  │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Central Product Catalog**: Master catalog with franchisee customization
2. **Brand Customization**: Each franchisee can customize branding
3. **Royalty/Commission Tracking**: Automatic calculation and tracking
4. **Franchisee Management Interface**: Self-service portal for franchisees
5. **Store-Level Customization**: Local menu modifications and pricing

### New Models Required
```python
# Franchise Management
class Franchise(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    agreement_start_date = db.Column(db.Date)
    agreement_end_date = db.Column(db.Date)
    royalty_rate = db.Column(db.Float, default=5.0)  # Percentage
    commission_rate = db.Column(db.Float, default=0.0)  # Percentage
    status = db.Column(db.Enum('active', 'inactive', 'suspended'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Master Product Catalog
class MasterProduct(db.Model):
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

# Franchisee Product Customization
class FranchiseProduct(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    franchise_id = db.Column(db.String(36), db.ForeignKey('franchises.id'), nullable=False)
    master_product_id = db.Column(db.String(36), db.ForeignKey('master_products.id'), nullable=False)
    custom_name = db.Column(db.String(100))
    custom_price = db.Column(db.Float)
    custom_description = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Royalty Calculation
class RoyaltyCalculation(db.Model):
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

# Franchise Branding
class FranchiseBranding(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    franchise_id = db.Column(db.String(36), db.ForeignKey('franchises.id'), nullable=False)
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#FF6B6B')
    secondary_color = db.Column(db.String(7), default='#4ECDC4')
    custom_css = db.Column(db.Text)
    custom_domain = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Database Schema Changes
```sql
-- Create franchises table
CREATE TABLE franchises (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    agreement_start_date DATE,
    agreement_end_date DATE,
    royalty_rate FLOAT DEFAULT 5.0,
    commission_rate FLOAT DEFAULT 0.0,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create master_products table
CREATE TABLE master_products (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    base_price FLOAT NOT NULL,
    cost_price FLOAT,
    sku VARCHAR(50) UNIQUE,
    barcode VARCHAR(50),
    image_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create franchise_products table
CREATE TABLE franchise_products (
    id VARCHAR(36) PRIMARY KEY,
    franchise_id VARCHAR(36) NOT NULL,
    master_product_id VARCHAR(36) NOT NULL,
    custom_name VARCHAR(100),
    custom_price FLOAT,
    custom_description TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (franchise_id) REFERENCES franchises(id),
    FOREIGN KEY (master_product_id) REFERENCES master_products(id)
);

-- Create royalty_calculations table
CREATE TABLE royalty_calculations (
    id VARCHAR(36) PRIMARY KEY,
    franchise_id VARCHAR(36) NOT NULL,
    store_id VARCHAR(36) NOT NULL,
    order_id VARCHAR(36) NOT NULL,
    gross_sales FLOAT NOT NULL,
    royalty_amount FLOAT NOT NULL,
    commission_amount FLOAT NOT NULL,
    net_amount FLOAT NOT NULL,
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'calculated', 'paid') DEFAULT 'pending',
    FOREIGN KEY (franchise_id) REFERENCES franchises(id),
    FOREIGN KEY (store_id) REFERENCES stores(id),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Create franchise_branding table
CREATE TABLE franchise_branding (
    id VARCHAR(36) PRIMARY KEY,
    franchise_id VARCHAR(36) NOT NULL,
    logo_url VARCHAR(255),
    primary_color VARCHAR(7) DEFAULT '#FF6B6B',
    secondary_color VARCHAR(7) DEFAULT '#4ECDC4',
    custom_css TEXT,
    custom_domain VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (franchise_id) REFERENCES franchises(id)
);
```

---

## Database Architecture Design

### Tenant Isolation Strategy: Shared Database with Row-Level Security

#### Implementation Approach
```sql
-- Enable row-level security on all tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE tables ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Create tenant isolation policies
CREATE POLICY tenant_isolation_users ON users
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));

CREATE POLICY tenant_isolation_categories ON categories
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));

CREATE POLICY tenant_isolation_menu_items ON menu_items
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));

-- Similar policies for all other tables
```

#### Tenant-Aware Base Model
```python
class TenantAwareModel(db.Model):
    __abstract__ = True
    
    tenant_id = db.Column(db.String(36), nullable=False, index=True)
    
    @classmethod
    def query_tenant(cls, tenant_id=None):
        """Get query filtered by tenant"""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        return cls.query.filter(cls.tenant_id == tenant_id)
    
    @classmethod
    def get_tenant(cls, id, tenant_id=None):
        """Get record by ID within tenant context"""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        return cls.query.filter_by(id=id, tenant_id=tenant_id).first()
    
    def save(self, tenant_id=None):
        """Save with tenant context"""
        if tenant_id is None:
            tenant_id = get_current_tenant_id()
        
        if not self.tenant_id:
            self.tenant_id = tenant_id
        
        db.session.add(self)
        db.session.commit()
        return self
```

---

## Tenant Identification and Routing System

### Multi-Method Tenant Identification

#### 1. Subdomain-Based Identification
```python
class SubdomainTenantMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', '')
        subdomain = host.split('.')[0] if '.' in host else None
        
        if subdomain and subdomain != 'www':
            tenant = Tenant.query.filter_by(subdomain=subdomain, status='active').first()
            if tenant:
                environ['TENANT_ID'] = tenant.id
                environ['TENANT_INFO'] = tenant.to_dict()
        
        return self.app(environ, start_response)
```

#### 2. Header-Based Identification (for API)
```python
class HeaderTenantMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        tenant_id = environ.get('HTTP_X_TENANT_ID')
        
        if tenant_id:
            tenant = Tenant.query.get(tenant_id)
            if tenant and tenant.status == 'active':
                environ['TENANT_ID'] = tenant.id
                environ['TENANT_INFO'] = tenant.to_dict()
        
        return self.app(environ, start_response)
```

#### 3. Path-Based Identification
```python
class PathTenantMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path_parts = path.strip('/').split('/')
        
        if len(path_parts) > 1 and path_parts[0] == 'tenant':
            tenant_code = path_parts[1]
            tenant = Tenant.query.filter_by(subdomain=tenant_code, status='active').first()
            
            if tenant:
                environ['TENANT_ID'] = tenant.id
                environ['TENANT_INFO'] = tenant.to_dict()
                # Remove tenant prefix from path
                environ['PATH_INFO'] = '/' + '/'.join(path_parts[2:])
        
        return self.app(environ, start_response)
```

### Tenant Context Manager
```python
class TenantContext:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.original_tenant = None
    
    def __enter__(self):
        self.original_tenant = get_current_tenant_id()
        set_current_tenant_id(self.tenant_id)
        # Set PostgreSQL session variable for RLS
        db.session.execute(f"SET app.current_tenant_id = '{self.tenant_id}'")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_tenant:
            set_current_tenant_id(self.original_tenant)
            db.session.execute(f"SET app.current_tenant_id = '{self.original_tenant}'")
        else:
            db.session.execute("RESET app.current_tenant_id")

# Usage
with TenantContext(tenant_id):
    # All database operations here are automatically scoped to tenant
    orders = Order.query.all()  # Only returns orders for this tenant
```

---

## Security and Access Control Architecture

### Multi-Layer Security Model

#### 1. Tenant-Level Security
```python
class TenantSecurityManager:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.settings = self.get_tenant_security_settings()
    
    def get_tenant_security_settings(self):
        """Get security settings for tenant"""
        settings = TenantSecuritySettings.query.filter_by(
            tenant_id=self.tenant_id
        ).first()
        
        return {
            'password_policy': {
                'min_length': settings.password_min_length or 8,
                'require_uppercase': settings.require_uppercase,
                'require_lowercase': settings.require_lowercase,
                'require_digits': settings.require_digits,
                'require_special': settings.require_special
            },
            'session_policy': {
                'timeout': settings.session_timeout or 3600,
                'max_concurrent': settings.max_concurrent_sessions or 3,
                'require_2fa': settings.require_2fa
            },
            'ip_restrictions': {
                'allowed_ips': settings.allowed_ips or [],
                'block_unknown_ips': settings.block_unknown_ips
            }
        }
    
    def validate_password(self, password):
        """Validate password against tenant policy"""
        policy = self.settings['password_policy']
        
        if len(password) < policy['min_length']:
            return False, f"Password must be at least {policy['min_length']} characters"
        
        if policy['require_uppercase'] and not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letters"
        
        if policy['require_lowercase'] and not any(c.islower() for c in password):
            return False, "Password must contain lowercase letters"
        
        if policy['require_digits'] and not any(c.isdigit() for c in password):
            return False, "Password must contain digits"
        
        if policy['require_special'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Password must contain special characters"
        
        return True, "Password is valid"
```

#### 2. Role-Based Access Control (RBAC)
```python
class TenantRoleManager:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
    
    def check_permission(self, user, permission, resource=None):
        """Check if user has permission within tenant context"""
        # Check tenant-specific permissions
        if user.role == 'administrator':
            return True
        
        # Check role-based permissions
        role_permissions = self.get_role_permissions(user.role, self.tenant_id)
        return permission in role_permissions
    
    def get_role_permissions(self, role, tenant_id):
        """Get permissions for role within tenant"""
        # Get tenant-specific role permissions
        tenant_role = TenantRole.query.filter_by(
            tenant_id=tenant_id,
            role_name=role
        ).first()
        
        if tenant_role and tenant_role.custom_permissions:
            return tenant_role.custom_permissions
        
        # Return default permissions
        return self.get_default_role_permissions(role)
    
    def get_default_role_permissions(self, role):
        """Get default permissions for role"""
        permissions = {
            'administrator': [
                'user_management', 'system_settings', 'reports_all',
                'inventory_management', 'order_management', 'payment_processing'
            ],
            'manager': [
                'user_view', 'order_management', 'inventory_management',
                'reports_basic', 'payment_processing'
            ],
            'cashier': [
                'order_create', 'payment_process', 'inventory_view',
                'customer_management'
            ]
        }
        return permissions.get(role, [])
```

#### 3. Data Access Control
```python
class TenantDataAccessControl:
    @staticmethod
    def get_tenant_query(model, tenant_id):
        """Get query filtered by tenant"""
        return model.query.filter(model.tenant_id == tenant_id)
    
    @staticmethod
    def check_tenant_access(resource_id, model, tenant_id):
        """Check if resource belongs to tenant"""
        resource = model.query.filter_by(
            id=resource_id,
            tenant_id=tenant_id
        ).first()
        
        return resource is not None
    
    @staticmethod
    def create_tenant_resource(data, model, tenant_id):
        """Create resource with tenant context"""
        data['tenant_id'] = tenant_id
        return model(**data)
    
    @staticmethod
    def audit_data_access(user, action, resource, tenant_id):
        """Audit all data access attempts"""
        audit_log = AuditLog(
            user_id=user.id,
            tenant_id=tenant_id,
            action=action,
            resource_type=resource.__class__.__name__,
            resource_id=resource.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            timestamp=datetime.utcnow()
        )
        db.session.add(audit_log)
        db.session.commit()
```

---

## Migration Strategy

### Incremental Migration Approach

#### Phase 1: Foundation (Month 1)
1. **Add tenant_id columns** to all existing tables
2. **Implement tenant middleware** for identification
3. **Create tenant management** interface
4. **Update all queries** to include tenant filtering
5. **Implement row-level security** policies

#### Phase 2: Multi-Store Support (Months 2-3)
1. **Create stores table** and related models
2. **Implement user-store permissions**
3. **Add store transfer** functionality
4. **Create consolidated reporting**
5. **Update UI for multi-store** context

#### Phase 3: Franchise Features (Months 4-5)
1. **Implement franchise management**
2. **Create master product catalog**
3. **Add royalty calculation** system
4. **Implement franchise branding**
5. **Create franchisee dashboard**

#### Phase 4: SaaS Platform (Month 6)
1. **Complete tenant isolation**
2. **Implement feature flags**
3. **Add usage tracking** and billing
4. **Create tenant self-service** portal
5. **Implement auto-scaling** infrastructure

### Migration Scripts

#### Data Migration Script
```python
def migrate_to_multi_tenant():
    """Migrate existing data to multi-tenant structure"""
    
    # Create default tenant
    default_tenant = Tenant(
        name='Default Restaurant',
        subdomain='default',
        status='active',
        plan_id='basic_plan'
    )
    db.session.add(default_tenant)
    db.session.commit()
    
    # Update existing records with default tenant_id
    tables_to_migrate = [
        User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings
    ]
    
    for table in tables_to_migrate:
        table.query.update({'tenant_id': default_tenant.id})
        db.session.commit()
    
    print(f"Migrated {len(tables_to_migrate)} tables to multi-tenant structure")
```

#### Rollback Strategy
```python
def rollback_multi_tenant():
    """Rollback multi-tenant changes"""
    
    # Backup current data
    backup_data = {}
    tables_to_backup = [User, Category, MenuItem, Table, Order, OrderItem, Payment, Settings]
    
    for table in tables_to_backup:
        backup_data[table.__name__] = [row.to_dict() for row in table.query.all()]
    
    # Remove tenant_id columns (if needed)
    # This would be implemented based on specific rollback requirements
    
    print("Rollback completed. Data backed up.")
    return backup_data
```

---

## Performance Optimization and Caching Strategies

### Multi-Tenant Caching Architecture

#### Tenant-Aware Caching
```python
class TenantCacheManager:
    def __init__(self, cache_client):
        self.cache = cache_client
    
    def get_cache_key(self, tenant_id, key):
        """Generate cache key with tenant prefix"""
        return f"tenant_{tenant_id}:{key}"
    
    def get(self, tenant_id, key):
        """Get value from tenant cache"""
        cache_key = self.get_cache_key(tenant_id, key)
        return self.cache.get(cache_key)
    
    def set(self, tenant_id, key, value, timeout=300):
        """Set value in tenant cache"""
        cache_key = self.get_cache_key(tenant_id, key)
        return self.cache.set(cache_key, value, timeout)
    
    def delete(self, tenant_id, key):
        """Delete value from tenant cache"""
        cache_key = self.get_cache_key(tenant_id, key)
        return self.cache.delete(cache_key)
    
    def clear_tenant_cache(self, tenant_id):
        """Clear all cache for tenant"""
        pattern = f"tenant_{tenant_id}:*"
        return self.cache.delete_many(pattern)
```

#### Database Connection Pooling
```python
class TenantConnectionPool:
    def __init__(self):
        self.pools = {}
        self.pool_config = {
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600
        }
    
    def get_pool(self, tenant_id):
        """Get connection pool for tenant"""
        if tenant_id not in self.pools:
            tenant = Tenant.query.get(tenant_id)
            if tenant:
                database_url = self.get_tenant_database_url(tenant)
                self.pools[tenant_id] = create_engine(
                    database_url,
                    **self.pool_config
                )
        
        return self.pools.get(tenant_id)
    
    def remove_pool(self, tenant_id):
        """Remove connection pool for tenant"""
        if tenant_id in self.pools:
            self.pools[tenant_id].dispose()
            del self.pools[tenant_id]
```

#### Query Optimization
```python
class TenantQueryOptimizer:
    @staticmethod
    def optimize_tenant_query(query, tenant_id):
        """Optimize query for tenant context"""
        # Add tenant filter
        query = query.filter(query.column_mapper.c.tenant_id == tenant_id)
        
        # Add appropriate indexes
        query = query.with_for_update()
        
        # Use prepared statements for better performance
        return query.statement.compile(compile_kwargs={"literal_binds": True})
    
    @staticmethod
    def get_tenant_analytics(tenant_id, date_range):
        """Get optimized analytics query for tenant"""
        # Use CTEs for complex analytics
        analytics_query = text("""
            WITH tenant_orders AS (
                SELECT * FROM orders
                WHERE tenant_id = :tenant_id
                AND created_at BETWEEN :start_date AND :end_date
            ),
            daily_sales AS (
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as order_count,
                    SUM(total) as total_sales
                FROM tenant_orders
                GROUP BY DATE(created_at)
            )
            SELECT * FROM daily_sales ORDER BY date DESC
        """)
        
        return db.session.execute(
            analytics_query,
            {
                'tenant_id': tenant_id,
                'start_date': date_range['start'],
                'end_date': date_range['end']
            }
        ).fetchall()
```

---

## Implementation Timeline and Phases

### 6-Month Implementation Plan

#### Month 1: Foundation
- **Week 1-2**: Database schema changes and tenant_id columns
- **Week 3**: Tenant identification middleware implementation
- **Week 4**: Basic tenant management interface

#### Month 2: Multi-Store Foundation
- **Week 1-2**: Stores table and user-store permissions
- **Week 3**: Store transfer functionality
- **Week 4**: Basic multi-store UI updates

#### Month 3: Multi-Store Completion
- **Week 1-2**: Consolidated reporting system
- **Week 3**: Store-specific configurations
- **Week 4**: Testing and optimization

#### Month 4: Franchise Foundation
- **Week 1-2**: Franchise management system
- **Week 3**: Master product catalog
- **Week 4**: Basic franchisee interface

#### Month 5: Franchise Completion
- **Week 1-2**: Royalty calculation system
- **Week 3**: Franchise branding features
- **Week 4**: Franchisee dashboard completion

#### Month 6: SaaS Platform
- **Week 1-2**: Complete tenant isolation and feature flags
- **Week 3**: Usage tracking and billing system
- **Week 4**: Tenant self-service portal and deployment

### Critical Success Factors
1. **Data Migration**: Ensure zero data loss during migration
2. **Performance**: Maintain sub-second response times
3. **Security**: Complete tenant isolation and data protection
4. **Scalability**: Support for 1000+ tenants
5. **User Experience**: Seamless transition for existing users

---

## Conclusion

This multi-tenancy architecture provides a comprehensive roadmap for evolving multi_web_cloud POS system from a single-tenant application to a full SaaS platform. The incremental approach ensures minimal disruption to existing users while building a scalable, secure, and maintainable multi-tenant system.

### Key Benefits
1. **Scalability**: Support for unlimited tenants
2. **Security**: Complete data isolation and protection
3. **Flexibility**: Customizable features per tenant
4. **Performance**: Optimized for multi-tenant workloads
5. **Maintainability**: Clean, modular architecture

### Next Steps
1. **Review and approve** this architecture plan
2. **Set up development environment** for multi-tenant development
3. **Begin Phase 1 implementation** with database changes
4. **Establish testing framework** for multi-tenant functionality
5. **Plan deployment strategy** for production rollout

This architecture positions multi_web_cloud as a competitive multi-tenant POS solution capable of serving businesses from single restaurants to large franchise networks.

---

## Stage 4: SaaS Platform - Month 6

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                SaaS Platform Architecture                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │  Tenant A   │ │  Tenant B   │ │  Tenant C   │     │
│  │             │ │             │ │             │     │
│  │ - Complete  │ │ - Complete  │ │ - Complete  │     │
│  │   Isolation │ │   Isolation │ │   Isolation │     │
│  │ - Custom    │ │ - Custom    │ │ - Custom    │     │
│  │   Features  │ │   Features  │ │   Features  │     │
│  │ - Own       │ │ - Own       │ │ - Own       │     │
│  │   Domain    │ │   Domain    │ │   Domain    │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                Platform Management                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │   Tenant    │ │   Feature   │ │   Usage     │     │
│  │ Management  │ │   Flags     │ │  Billing    │     │
│  │             │ │             │ │             │     │
│  │ - Onboarding│ │ - Feature   │ │ - Usage     │     │
│  │ - Plans     │ │   Control   │ │   Tracking  │     │
│  │ - Billing   │ │ - Per Tenant │ │ - Invoices  │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
1. **Complete Multi-Tenant Architecture**: Full isolation between tenants
2. **Per-Tenant Feature Flags**: Customizable features per tenant
3. **Usage-Based Billing**: Track and bill based on usage
4. **Tenant Self-Service Portal**: Complete tenant management
5. **Scalable Infrastructure**: Auto-scaling and load balancing

### New Models Required
```python
# Enhanced Tenant Management
class Tenant(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    custom_domain = db.Column(db.String(100))
    status = db.Column(db.Enum('trial', 'active', 'suspended', 'cancelled'), default='trial')
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trial_ends_at = db.Column(db.DateTime)
    
    # Configuration
    max_users = db.Column(db.Integer, default=5)
    max_orders_per_month = db.Column(db.Integer, default=1000)
    max_storage_gb = db.Column(db.Integer, default=10)
    custom_features = db.Column(db.JSON)

# Subscription Plans
class SubscriptionPlan(db.Model):
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

# Tenant Feature Flags
class TenantFeatureFlag(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False)
    configuration = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Usage Tracking
class TenantUsage(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    usage_type = db.Column(db.Enum('orders', 'users', 'storage', 'api_calls'), nullable=False)
    usage_value = db.Column(db.Float, nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Billing
class TenantInvoice(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    billing_period_start = db.Column(db.Date, nullable=False)
    billing_period_end = db.Column(db.Date, nullable=False)
    
    # Charges
    base_fee = db.Column(db.Float, default=0.0)
    usage_charges = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.Enum('draft', 'sent', 'paid', 'overdue'), default='draft')
    due_date = db.Column(db.Date)
    paid_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Tenant Provisioning
class TenantProvisioning(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    provisioning_type = db.Column(db.Enum('database', 'storage', 'domain', 'features'), nullable=False)
    status = db.Column(db.Enum('pending', 'in_progress', 'completed', 'failed'), default='pending')
    configuration = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Database Schema Changes
```sql
-- Create tenants table
CREATE TABLE tenants (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    custom_domain VARCHAR(100),
    status ENUM('trial', 'active', 'suspended', 'cancelled') DEFAULT 'trial',
    plan_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trial_ends_at TIMESTAMP,
    max_users INTEGER DEFAULT 5,
    max_orders_per_month INTEGER DEFAULT 1000,
    max_storage_gb INTEGER DEFAULT 10,
    custom_features JSON,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);

-- Create subscription_plans table
CREATE TABLE subscription_plans (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    price_monthly FLOAT NOT NULL,
    price_yearly FLOAT NOT NULL,
    max_users INTEGER DEFAULT 5,
    max_orders_per_month INTEGER DEFAULT 1000,
    max_storage_gb INTEGER DEFAULT 10,
    features JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tenant_feature_flags table
CREATE TABLE tenant_feature_flags (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    configuration JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Create tenant_usage table
CREATE TABLE tenant_usage (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    usage_type ENUM('orders', 'users', 'storage', 'api_calls') NOT NULL,
    usage_value FLOAT NOT NULL,
    usage_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Create tenant_invoices table
CREATE TABLE tenant_invoices (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    base_fee FLOAT DEFAULT 0.0,
    usage_charges FLOAT DEFAULT 0.0,
    total_amount FLOAT NOT NULL,
    status ENUM('draft', 'sent', 'paid', 'overdue') DEFAULT 'draft',
    due_date DATE,
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

-- Create tenant_provisioning table
CREATE TABLE tenant_provisioning (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    provisioning_type ENUM('database', 'storage', 'domain', 'features') NOT NULL,
    status ENUM('pending', 'in_progress', 'completed', 'failed') DEFAULT 'pending',
    configuration JSON,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```