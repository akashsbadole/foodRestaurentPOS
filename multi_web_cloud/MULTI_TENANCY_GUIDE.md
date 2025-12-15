# Multi-Tenancy Guide - Enhanced Flask POS Application

## 📋 Table of Contents

1. [Multi-Tenancy Overview](#multi-tenancy-overview)
2. [Architecture](#architecture)
3. [Tenant Isolation](#tenant-isolation)
4. [Tenant Management](#tenant-management)
5. [Database Design](#database-design)
6. [Security in Multi-Tenancy](#security-in-multi-tenancy)
7. [Configuration](#configuration)
8. [Implementation Guide](#implementation-guide)
9. [Deployment Strategies](#deployment-strategies)
10. [Scaling and Performance](#scaling-and-performance)
11. [Monitoring and Analytics](#monitoring-and-analytics)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Multi-Tenancy Overview

### What is Multi-Tenancy?

Multi-tenancy is an architecture pattern where a single instance of software serves multiple customers (tenants), while keeping their data isolated and secure. Each tenant operates as if they have their own dedicated instance.

### Benefits of Multi-Tenancy

- **Cost Efficiency**: Shared infrastructure reduces operational costs
- **Scalability**: Easy to add new tenants without additional hardware
- **Maintenance**: Single codebase to maintain and update
- **Resource Optimization**: Better resource utilization
- **Rapid Deployment**: Quick tenant onboarding
- **Centralized Management**: Unified administration and monitoring

### Multi-Tenancy Models

#### 1. Database per Tenant

```
Tenant A → Database A (tenant_a_pos)
Tenant B → Database B (tenant_b_pos)
Tenant C → Database C (tenant_c_pos)
```

**Pros:**
- Maximum data isolation
- Independent backup/restore
- Per-tenant performance tuning

**Cons:**
- Higher resource usage
- Complex management
- Higher cost

#### 2. Schema per Tenant

```
Database (multi_tenant_pos)
├── Schema A (tenant_a_schema)
├── Schema B (tenant_b_schema)
└── Schema C (tenant_c_schema)
```

**Pros:**
- Good data isolation
- Shared database resources
- Easier management

**Cons:**
- Schema complexity
- Cross-tenant queries difficult
- Migration complexity

#### 3. Shared Database, Row-Level Security

```
Database (shared_pos)
├── orders (tenant_id column)
├── customers (tenant_id column)
├── menu_items (tenant_id column)
└── Row-level security filters
```

**Pros:**
- Most resource efficient
- Easy to manage
- Simple scaling

**Cons:**
- Security complexity
- Performance overhead
- Backup complexity

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                  Application Layer                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            Tenant Router                           │   │
│  │  - Identify tenant from request                   │   │
│  │  - Route to appropriate tenant context           │   │
│  │  - Apply tenant-specific settings               │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Business Logic Layer                      │   │
│  │  - Order processing                            │   │
│  │  - Payment handling                            │   │
│  │  - CRM operations                             │   │
│  │  - Loyalty management                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Data Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │   Tenant A  │ │   Tenant B  │ │   Tenant C  │     │
│  │   Database  │ │   Database  │ │   Database  │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```
1. User Request → Load Balancer
2. Load Balancer → Application Server
3. Tenant Router → Identify Tenant
4. Apply Tenant Context → Business Logic
5. Tenant-Specific Database → Data Operations
6. Response → User (with tenant-specific branding)
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Multi-Tenant Components                  │
├─────────────────────────────────────────────────────────────┤
│ Tenant Management                                        │
│ ├── Tenant Creation                                     │
│ ├── Tenant Configuration                                │
│ ├── Tenant Billing                                     │
│ └── Tenant Deactivation                                │
├─────────────────────────────────────────────────────────────┤
│ Security & Isolation                                    │
│ ├── Data Isolation                                    │
│ ├── Authentication                                     │
│ ├── Authorization                                      │
│ └── Audit Logging                                     │
├─────────────────────────────────────────────────────────────┤
│ Customization                                          │
│ ├── Branding                                          │
│ ├── Feature Flags                                      │
│ ├── Configuration                                     │
│ └── Themes                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Tenant Isolation

### Data Isolation Strategies

#### 1. Complete Database Isolation

```python
# models/tenant.py
class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    domain = db.Column(db.String(100))
    database_name = db.Column(db.String(100), nullable=False)
    database_host = db.Column(db.String(100))
    database_port = db.Column(db.Integer, default=5432)
    database_user = db.Column(db.String(50), nullable=False)
    database_password = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('active', 'inactive', 'suspended'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database connection per tenant
def get_tenant_database(tenant_id):
    tenant = Tenant.query.get(tenant_id)
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    
    connection_string = (
        f"postgresql://{tenant.database_user}:{tenant.database_password}"
        f"@{tenant.database_host}:{tenant.database_port}/{tenant.database_name}"
    )
    
    return create_engine(connection_string)
```

#### 2. Schema-Based Isolation

```python
# models/tenant.py
class TenantSchema(db.Model):
    __tablename__ = 'tenant_schemas'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), nullable=False)
    schema_name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Schema switching middleware
class TenantSchemaMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        tenant_id = self.get_tenant_id(environ)
        if tenant_id:
            self.switch_schema(tenant_id)
        
        return self.app(environ, start_response)
    
    def switch_schema(self, tenant_id):
        tenant = Tenant.query.get(tenant_id)
        if tenant:
            db.session.execute(f"SET search_path TO {tenant.schema_name}")
    
    def get_tenant_id(self, environ):
        # Extract tenant ID from subdomain, header, or cookie
        return environ.get('HTTP_X_TENANT_ID')
```

#### 3. Row-Level Security

```python
# models/base.py
class TenantAwareModel(db.Model):
    __abstract__ = True
    
    tenant_id = db.Column(db.String(36), nullable=False, index=True)
    
    @classmethod
    def query_tenant(cls, tenant_id):
        return cls.query.filter(cls.tenant_id == tenant_id)

# Row-level security policy
def create_row_level_security_policy():
    """Create PostgreSQL RLS policies for tenant isolation"""
    
    # Enable row-level security
    db.session.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")
    db.session.execute("ALTER TABLE customers ENABLE ROW LEVEL SECURITY")
    
    # Create policies
    db.session.execute("""
        CREATE POLICY tenant_isolation_orders ON orders
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
    
    db.session.execute("""
        CREATE POLICY tenant_isolation_customers ON customers
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
```

### Resource Isolation

#### File Storage Isolation

```python
# utils/file_storage.py
class TenantFileStorage:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.base_path = f"uploads/tenants/{tenant_id}"
    
    def save_file(self, file, filename):
        tenant_path = os.path.join(self.base_path, filename)
        os.makedirs(os.path.dirname(tenant_path), exist_ok=True)
        file.save(tenant_path)
        return tenant_path
    
    def get_file_url(self, filename):
        return f"/static/uploads/tenants/{self.tenant_id}/{filename}"
    
    def delete_file(self, filename):
        file_path = os.path.join(self.base_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

# Integration in Flask app
@app.before_request
def setup_tenant_storage():
    tenant_id = get_current_tenant_id()
    if tenant_id:
        g.tenant_storage = TenantFileStorage(tenant_id)
```

#### Cache Isolation

```python
# utils/cache.py
class TenantCache:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
        self.prefix = f"tenant_{tenant_id}:"
    
    def get(self, key):
        full_key = self.prefix + key
        return cache.get(full_key)
    
    def set(self, key, value, timeout=300):
        full_key = self.prefix + key
        return cache.set(full_key, value, timeout)
    
    def delete(self, key):
        full_key = self.prefix + key
        return cache.delete(full_key)

# Cache middleware
@app.before_request
def setup_tenant_cache():
    tenant_id = get_current_tenant_id()
    if tenant_id:
        g.cache = TenantCache(tenant_id)
```

---

## Tenant Management

### Tenant Creation

#### Tenant Registration Form

```python
# forms/tenant.py
class TenantRegistrationForm(FlaskForm):
    # Basic Information
    name = StringField('Restaurant Name', validators=[DataRequired(), Length(1, 100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(10, 15)])
    
    # Address
    address = TextAreaField('Address', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    postal_code = StringField('Postal Code', validators=[DataRequired()])
    country = StringField('Country', validators=[DataRequired()])
    
    # Domain Configuration
    subdomain = StringField('Subdomain', validators=[DataRequired(), Length(3, 50)])
    custom_domain = StringField('Custom Domain (Optional)')
    
    # Plan Selection
    plan = SelectField('Subscription Plan', 
                     choices=[('basic', 'Basic'), ('pro', 'Pro'), ('enterprise', 'Enterprise')])
    
    # Admin User
    admin_username = StringField('Admin Username', validators=[DataRequired()])
    admin_email = StringField('Admin Email', validators=[DataRequired(), Email()])
    admin_password = PasswordField('Admin Password', validators=[DataRequired(), Length(8, 128)])
    
    # Terms
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    
    submit = SubmitField('Create Tenant')
```

#### Tenant Creation Process

```python
# routes/tenant.py
@app.route('/register-tenant', methods=['GET', 'POST'])
def register_tenant():
    form = TenantRegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create tenant
            tenant = Tenant(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                postal_code=form.postal_code.data,
                country=form.country.data,
                subdomain=form.subdomain.data,
                custom_domain=form.custom_domain.data,
                plan=form.plan.data,
                status='pending_setup'
            )
            
            db.session.add(tenant)
            db.session.flush()  # Get tenant ID
            
            # Create tenant database
            create_tenant_database(tenant)
            
            # Create admin user
            admin_user = User(
                username=form.admin_username.data,
                email=form.admin_email.data,
                password=generate_password_hash(form.admin_password.data),
                role='administrator',
                tenant_id=tenant.id
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Initialize tenant data
            initialize_tenant_data(tenant.id)
            
            # Send welcome email
            send_tenant_welcome_email(tenant, admin_user)
            
            flash('Tenant created successfully! Check your email for login details.', 'success')
            return redirect(url_for('tenant.success', tenant_id=tenant.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tenant: {str(e)}', 'error')
    
    return render_template('tenant/register.html', form=form)

def create_tenant_database(tenant):
    """Create database for new tenant"""
    database_name = f"tenant_{tenant.id}_pos"
    
    # Create database
    db.engine.execute(f"CREATE DATABASE {database_name}")
    
    # Update tenant record
    tenant.database_name = database_name
    tenant.database_host = current_app.config['DATABASE_HOST']
    tenant.database_user = f"tenant_{tenant.id}"
    tenant.database_password = generate_secure_password()
    
    # Create database user
    db.engine.execute(f"CREATE USER {tenant.database_user} WITH PASSWORD '{tenant.database_password}'")
    db.engine.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database_name} TO {tenant.database_user}")
```

### Tenant Configuration

#### Tenant Settings Model

```python
# models/tenant.py
class TenantSettings(db.Model):
    __tablename__ = 'tenant_settings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # Restaurant Information
    restaurant_name = db.Column(db.String(100))
    gst_number = db.Column(db.String(15))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    
    # Branding
    logo_url = db.Column(db.String(255))
    primary_color = db.Column(db.String(7), default='#FF6B6B')
    secondary_color = db.Column(db.String(7), default='#4ECDC4')
    
    # Business Settings
    currency = db.Column(db.String(3), default='INR')
    tax_rate = db.Column(db.Float, default=5.0)
    service_charge = db.Column(db.Float, default=0.0)
    
    # Feature Flags
    enable_crm = db.Column(db.Boolean, default=True)
    enable_loyalty = db.Column(db.Boolean, default=True)
    enable_offline = db.Column(db.Boolean, default=True)
    enable_reports = db.Column(db.Boolean, default=True)
    
    # Integration Settings
    razorpay_key_id = db.Column(db.String(100))
    razorpay_key_secret = db.Column(db.String(100))
    email_settings = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Tenant Configuration Interface

```python
# routes/tenant.py
@app.route('/tenant/settings', methods=['GET', 'POST'])
@login_required
def tenant_settings():
    tenant_id = get_current_tenant_id()
    settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
    
    if not settings:
        settings = TenantSettings(tenant_id=tenant_id)
        db.session.add(settings)
    
    form = TenantSettingsForm(obj=settings)
    
    if form.validate_on_submit():
        # Update settings
        settings.restaurant_name = form.restaurant_name.data
        settings.gst_number = form.gst_number.data
        settings.contact_email = form.contact_email.data
        settings.contact_phone = form.contact_phone.data
        
        # Branding
        if form.logo.data:
            logo_filename = save_tenant_logo(form.logo.data, tenant_id)
            settings.logo_url = logo_filename
        
        settings.primary_color = form.primary_color.data
        settings.secondary_color = form.secondary_color.data
        
        # Business settings
        settings.currency = form.currency.data
        settings.tax_rate = form.tax_rate.data
        settings.service_charge = form.service_charge.data
        
        # Feature flags
        settings.enable_crm = form.enable_crm.data
        settings.enable_loyalty = form.enable_loyalty.data
        settings.enable_offline = form.enable_offline.data
        settings.enable_reports = form.enable_reports.data
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('tenant.settings'))
    
    return render_template('tenant/settings.html', form=form, settings=settings)
```

### Tenant Billing

#### Subscription Plans

```python
# models/tenant.py
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

class TenantSubscription(db.Model):
    __tablename__ = 'tenant_subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    
    status = db.Column(db.Enum('active', 'cancelled', 'expired', 'suspended'), default='active')
    billing_cycle = db.Column(db.Enum('monthly', 'yearly'), default='monthly')
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Billing Management

```python
# routes/billing.py
@app.route('/billing/plans')
@login_required
def billing_plans():
    plans = SubscriptionPlan.query.all()
    current_subscription = TenantSubscription.query.filter_by(
        tenant_id=get_current_tenant_id(),
        status='active'
    ).first()
    
    return render_template('billing/plans.html', 
                        plans=plans, 
                        current_subscription=current_subscription)

@app.route('/billing/subscribe/<plan_id>')
@login_required
def subscribe_plan(plan_id):
    tenant_id = get_current_tenant_id()
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Create subscription
    subscription = TenantSubscription(
        tenant_id=tenant_id,
        plan_id=plan_id,
        status='active',
        billing_cycle='monthly',
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    # Process payment
    payment_result = process_subscription_payment(subscription)
    
    if payment_result['success']:
        flash('Subscription activated successfully!', 'success')
    else:
        flash('Payment failed. Please try again.', 'error')
    
    return redirect(url_for('billing.dashboard'))
```

---

## Database Design

### Multi-Tenant Database Schema

#### Central Management Database

```sql
-- Central database for tenant management
CREATE DATABASE tenant_management;

-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    subdomain VARCHAR(50) UNIQUE NOT NULL,
    custom_domain VARCHAR(100),
    database_name VARCHAR(100) NOT NULL,
    database_host VARCHAR(100),
    database_port INTEGER DEFAULT 5432,
    database_user VARCHAR(50) NOT NULL,
    database_password VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    plan_id UUID REFERENCES subscription_plans(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subscription plans
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2) NOT NULL,
    max_users INTEGER DEFAULT 5,
    max_orders_per_month INTEGER DEFAULT 1000,
    max_storage_gb INTEGER DEFAULT 10,
    features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tenant subscriptions
CREATE TABLE tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) NOT NULL,
    plan_id UUID REFERENCES subscription_plans(id) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    billing_cycle VARCHAR(10) DEFAULT 'monthly',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Tenant-Specific Database Template

```sql
-- Template database for new tenants
CREATE DATABASE tenant_template;

-- Core tables with tenant_id for row-level security
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    customer_id UUID REFERENCES customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE menu_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    category_id UUID,
    available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable row-level security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY customer_tenant_isolation ON customers
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));

CREATE POLICY order_tenant_isolation ON orders
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));

CREATE POLICY menu_item_tenant_isolation ON menu_items
    FOR ALL TO application_user
    USING (tenant_id = current_setting('app.current_tenant_id'));
```

### Database Migration Strategy

#### Tenant Migration Script

```python
# migrations/multi_tenant.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create central management tables
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('subdomain', sa.String(length=50), nullable=False),
        sa.Column('custom_domain', sa.String(length=100), nullable=True),
        sa.Column('database_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subdomain')
    )
    
    # Add tenant_id to existing tables
    op.add_column('customers', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('orders', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('menu_items', sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False))
    
    # Create indexes
    op.create_index('idx_customers_tenant_id', 'customers', ['tenant_id'])
    op.create_index('idx_orders_tenant_id', 'orders', ['tenant_id'])
    op.create_index('idx_menu_items_tenant_id', 'menu_items', ['tenant_id'])
    
    # Enable row-level security
    op.execute("ALTER TABLE customers ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE menu_items ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policies
    op.execute("""
        CREATE POLICY tenant_isolation_customers ON customers
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)
    
    op.execute("""
        CREATE POLICY tenant_isolation_orders ON orders
        FOR ALL TO application_user
        USING (tenant_id = current_setting('app.current_tenant_id'))
    """)

def downgrade():
    # Remove RLS policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_customers ON customers")
    op.execute("DROP POLICY IF EXISTS tenant_isolation_orders ON orders")
    
    # Disable row-level security
    op.execute("ALTER TABLE customers DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE orders DISABLE ROW LEVEL SECURITY")
    
    # Remove indexes
    op.drop_index('idx_menu_items_tenant_id', table_name='menu_items')
    op.drop_index('idx_orders_tenant_id', table_name='orders')
    op.drop_index('idx_customers_tenant_id', table_name='customers')
    
    # Remove tenant_id columns
    op.drop_column('menu_items', 'tenant_id')
    op.drop_column('orders', 'tenant_id')
    op.drop_column('customers', 'tenant_id')
    
    # Drop central management tables
    op.drop_table('tenants')
```

---

## Security in Multi-Tenancy

### Tenant Identification

#### Subdomain-Based Identification

```python
# middleware/tenant_identification.py
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

# Flask app integration
app.wsgi_app = SubdomainTenantMiddleware(app.wsgi_app)
```

#### Header-Based Identification

```python
# middleware/tenant_identification.py
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

#### Path-Based Identification

```python
# middleware/tenant_identification.py
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

### Authentication and Authorization

#### Tenant-Aware Authentication

```python
# auth/tenant_auth.py
class TenantAwareAuth:
    @staticmethod
    def authenticate_user(username, password, tenant_id):
        """Authenticate user for specific tenant"""
        user = User.query.filter_by(
            username=username,
            tenant_id=tenant_id,
            status='active'
        ).first()
        
        if user and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def check_user_permission(user, permission, resource=None):
        """Check user permission within tenant context"""
        # Check tenant-specific permissions
        if user.role == 'administrator':
            return True
        
        # Check role-based permissions
        role_permissions = get_role_permissions(user.role, user.tenant_id)
        return permission in role_permissions

# Login route with tenant awareness
@app.route('/login', methods=['GET', 'POST'])
def login():
    tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        flash('Invalid tenant', 'error')
        return redirect(url_for('main.invalid_tenant'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = TenantAwareAuth.authenticate_user(
            form.username.data, 
            form.password.data, 
            tenant_id
        )
        
        if user:
            login_user(user, remember=form.remember_me.data)
            
            # Set tenant context in session
            session['tenant_id'] = tenant_id
            session['tenant_subdomain'] = get_tenant_subdomain(tenant_id)
            
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html', form=form, tenant=get_tenant_info(tenant_id))
```

#### Data Access Control

```python
# utils/tenant_data_access.py
class TenantDataAccess:
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

# Usage in routes
@app.route('/orders/<order_id>')
@login_required
def get_order(order_id):
    tenant_id = get_current_tenant_id()
    
    # Check tenant access
    if not TenantDataAccess.check_tenant_access(order_id, Order, tenant_id):
        abort(403)  # Forbidden
    
    order = Order.query.filter_by(id=order_id, tenant_id=tenant_id).first()
    return render_template('orders/detail.html', order=order)
```

### Security Policies

#### Tenant Security Configuration

```python
# config/tenant_security.py
class TenantSecurityConfig:
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

---

## Configuration

### Multi-Tenant Configuration

```python
# config/multi_tenant.py
import os

class MultiTenantConfig:
    # Multi-tenancy settings
    MULTI_TENANT = os.environ.get('MULTI_TENANT', 'True').lower() == 'true'
    TENANT_MODEL = 'models.tenant.Tenant'
    TENANT_COOKIE_NAME = 'tenant_id'
    DEFAULT_TENANT = os.environ.get('DEFAULT_TENANT', 'default')
    
    # Tenant identification
    TENANT_IDENTIFICATION = os.environ.get('TENANT_IDENTIFICATION', 'subdomain')
    TENANT_HEADER = 'X-Tenant-ID'
    TENANT_PATH_PREFIX = '/tenant'
    
    # Database isolation
    TENANT_ISOLATION = os.environ.get('TENANT_ISOLATION', 'database')
    SHARED_DB = os.environ.get('SHARED_DB', 'False').lower() == 'true'
    
    # Tenant database settings
    TENANT_DB_PREFIX = os.environ.get('TENANT_DB_PREFIX', 'tenant_')
    TENANT_DB_SUFFIX = os.environ.get('TENANT_DB_SUFFIX', '_pos')
    TENANT_DB_HOST = os.environ.get('TENANT_DB_HOST', 'localhost')
    TENANT_DB_PORT = int(os.environ.get('TENANT_DB_PORT', 5432))
    
    # Tenant limits
    DEFAULT_MAX_USERS = int(os.environ.get('DEFAULT_MAX_USERS', 5))
    DEFAULT_MAX_ORDERS = int(os.environ.get('DEFAULT_MAX_ORDERS', 1000))
    DEFAULT_MAX_STORAGE = int(os.environ.get('DEFAULT_MAX_STORAGE', 10))  # GB
    
    # Tenant customization
    ALLOW_CUSTOM_DOMAINS = os.environ.get('ALLOW_CUSTOM_DOMAINS', 'True').lower() == 'true'
    ALLOW_CUSTOM_BRANDING = os.environ.get('ALLOW_CUSTOM_BRANDING', 'True').lower() == 'true'
    ALLOW_FEATURE_CUSTOMIZATION = os.environ.get('ALLOW_FEATURE_CUSTOMIZATION', 'True').lower() == 'true'
```

### Environment Configuration

```bash
# .env file for multi-tenancy
# Multi-tenancy
MULTI_TENANT=True
TENANT_IDENTIFICATION=subdomain
DEFAULT_TENANT=default

# Database
TENANT_ISOLATION=database
SHARED_DB=False
TENANT_DB_PREFIX=tenant_
TENANT_DB_SUFFIX=_pos
TENANT_DB_HOST=localhost
TENANT_DB_PORT=5432

# Tenant limits
DEFAULT_MAX_USERS=5
DEFAULT_MAX_ORDERS=1000
DEFAULT_MAX_STORAGE=10

# Customization
ALLOW_CUSTOM_DOMAINS=True
ALLOW_CUSTOM_BRANDING=True
ALLOW_FEATURE_CUSTOMIZATION=True
```

### Dynamic Configuration Loading

```python
# utils/tenant_config.py
class TenantConfigLoader:
    @staticmethod
    def load_tenant_config(tenant_id):
        """Load configuration for specific tenant"""
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return None
        
        settings = TenantSettings.query.filter_by(tenant_id=tenant_id).first()
        
        return {
            'database': {
                'url': f"postgresql://{tenant.database_user}:{tenant.database_password}@{tenant.database_host}:{tenant.database_port}/{tenant.database_name}",
                'pool_size': 5,
                'max_overflow': 10
            },
            'branding': {
                'name': settings.restaurant_name if settings else tenant.name,
                'logo': settings.logo_url if settings else None,
                'primary_color': settings.primary_color if settings else '#FF6B6B',
                'secondary_color': settings.secondary_color if settings else '#4ECDC4'
            },
            'business': {
                'currency': settings.currency if settings else 'INR',
                'tax_rate': settings.tax_rate if settings else 5.0,
                'gst_number': settings.gst_number if settings else None
            },
            'features': {
                'crm': settings.enable_crm if settings else True,
                'loyalty': settings.enable_loyalty if settings else True,
                'offline': settings.enable_offline if settings else True,
                'reports': settings.enable_reports if settings else True
            },
            'integrations': {
                'razorpay': {
                    'key_id': settings.razorpay_key_id if settings else None,
                    'key_secret': settings.razorpay_key_secret if settings else None
                },
                'email': settings.email_settings if settings else {}
            }
        }
    
    @staticmethod
    def apply_tenant_config(app, tenant_id):
        """Apply tenant-specific configuration to Flask app"""
        config = TenantConfigLoader.load_tenant_config(tenant_id)
        
        if config:
            # Update app config
            app.config.update(config)
            
            # Store in application context
            app.current_tenant_id = tenant_id
            app.current_tenant_config = config
```

---

## Implementation Guide

### Step 1: Database Setup

```python
# scripts/setup_multi_tenancy.py
def setup_multi_tenancy():
    """Setup multi-tenancy database structure"""
    
    # 1. Create central management database
    create_central_database()
    
    # 2. Create tenant template database
    create_tenant_template()
    
    # 3. Setup tenant management tables
    setup_tenant_tables()
    
    # 4. Create database user management functions
    setup_database_user_management()
    
    print("Multi-tenancy setup completed successfully!")

def create_central_database():
    """Create central management database"""
    engine = create_engine('postgresql://postgres:password@localhost/postgres')
    engine.execute("CREATE DATABASE tenant_management")
    print("Created central management database")

def create_tenant_template():
    """Create template database for new tenants"""
    engine = create_engine('postgresql://postgres:password@localhost/postgres')
    engine.execute("CREATE DATABASE tenant_template")
    
    # Connect to template database and create tables
    template_engine = create_engine('postgresql://postgres:password@localhost/tenant_template')
    Base.metadata.create_all(template_engine)
    print("Created tenant template database")

def setup_database_user_management():
    """Create functions for tenant database management"""
    engine = create_engine('postgresql://postgres:password@localhost/tenant_management')
    
    # Function to create tenant database
    engine.execute("""
        CREATE OR REPLACE FUNCTION create_tenant_database(tenant_id UUID, database_name VARCHAR)
        RETURNS VOID AS $$
        BEGIN
            EXECUTE format('CREATE DATABASE %I', database_name);
            EXECUTE format('CREATE USER %I WITH PASSWORD %L', 'tenant_' || tenant_id, generate_secure_password());
            EXECUTE format('GRANT ALL PRIVILEGES ON DATABASE %I TO %I', database_name, 'tenant_' || tenant_id);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Function to drop tenant database
    engine.execute("""
        CREATE OR REPLACE FUNCTION drop_tenant_database(tenant_id UUID, database_name VARCHAR)
        RETURNS VOID AS $$
        BEGIN
            EXECUTE format('DROP DATABASE IF EXISTS %I', database_name);
            EXECUTE format('DROP USER IF EXISTS %I', 'tenant_' || tenant_id);
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    print("Created database user management functions")
```

### Step 2: Tenant Middleware

```python
# middleware/tenant.py
class TenantMiddleware:
    def __init__(self, app):
        self.app = app
        self.tenant_identifiers = {
            'subdomain': self.get_tenant_from_subdomain,
            'header': self.get_tenant_from_header,
            'path': self.get_tenant_from_path,
            'cookie': self.get_tenant_from_cookie
        }
    
    def __call__(self, environ, start_response):
        tenant_id = None
        
        # Try different identification methods
        identification_method = current_app.config.get('TENANT_IDENTIFICATION', 'subdomain')
        
        if identification_method in self.tenant_identifiers:
            tenant_id = self.tenant_identifiers[identification_method](environ)
        
        if tenant_id:
            # Load tenant information
            tenant = self.load_tenant(tenant_id)
            if tenant and tenant.status == 'active':
                environ['TENANT_ID'] = tenant.id
                environ['TENANT_INFO'] = tenant.to_dict()
                
                # Apply tenant configuration
                self.apply_tenant_config(tenant.id)
        
        return self.app(environ, start_response)
    
    def get_tenant_from_subdomain(self, environ):
        host = environ.get('HTTP_HOST', '')
        subdomain = host.split('.')[0] if '.' in host else None
        
        if subdomain and subdomain != 'www':
            tenant = Tenant.query.filter_by(subdomain=subdomain, status='active').first()
            return tenant.id if tenant else None
    
    def get_tenant_from_header(self, environ):
        tenant_id = environ.get('HTTP_X_TENANT_ID')
        return tenant_id
    
    def get_tenant_from_path(self, environ):
        path = environ.get('PATH_INFO', '')
        path_parts = path.strip('/').split('/')
        
        if len(path_parts) > 1 and path_parts[0] == 'tenant':
            return path_parts[1]
        
        return None
    
    def get_tenant_from_cookie(self, environ):
        # Implementation for cookie-based tenant identification
        pass
    
    def load_tenant(self, tenant_id):
        """Load tenant from database"""
        return Tenant.query.get(tenant_id)
    
    def apply_tenant_config(self, tenant_id):
        """Apply tenant-specific configuration"""
        config = TenantConfigLoader.load_tenant_config(tenant_id)
        if config:
            current_app.config.update(config)
            current_app.current_tenant_id = tenant_id
            current_app.current_tenant_config = config
```

### Step 3: Tenant-Aware Models

```python
# models/base.py
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

# Example tenant-aware models
class Customer(TenantAwareModel):
    __tablename__ = 'customers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Order(TenantAwareModel):
    __tablename__ = 'orders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'))
    order_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    subtotal = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Step 4: Tenant Management Interface

```python
# routes/admin.py
@app.route('/admin/tenants')
@login_required
@admin_required
def list_tenants():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Tenant.query
    
    if search:
        query = query.filter(
            Tenant.name.ilike(f'%{search}%') |
            Tenant.subdomain.ilike(f'%{search}%') |
            Tenant.email.ilike(f'%{search}%')
        )
    
    tenants = query.paginate(
        page=page, 
        per_page=20, 
        error_out=False
    )
    
    return render_template('admin/tenants/list.html', tenants=tenants, search=search)

@app.route('/admin/tenants/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_tenant():
    form = TenantCreationForm()
    
    if form.validate_on_submit():
        try:
            # Create tenant
            tenant = Tenant(
                name=form.name.data,
                email=form.email.data,
                subdomain=form.subdomain.data,
                plan_id=form.plan_id.data,
                status='pending_setup'
            )
            
            db.session.add(tenant)
            db.session.flush()
            
            # Setup tenant infrastructure
            setup_tenant_infrastructure(tenant)
            
            # Create admin user
            admin_user = User(
                username=form.admin_username.data,
                email=form.admin_email.data,
                password=generate_password_hash(form.admin_password.data),
                role='administrator',
                tenant_id=tenant.id
            )
            
            db.session.add(admin_user)
            db.session.commit()
            
            # Send setup email
            send_tenant_setup_email(tenant, admin_user)
            
            flash('Tenant created successfully!', 'success')
            return redirect(url_for('admin.list_tenants'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating tenant: {str(e)}', 'error')
    
    return render_template('admin/tenants/create.html', form=form)

def setup_tenant_infrastructure(tenant):
    """Setup infrastructure for new tenant"""
    # 1. Create database
    database_name = f"{current_app.config['TENANT_DB_PREFIX']}{tenant.id}{current_app.config['TENANT_DB_SUFFIX']}"
    
    engine = create_engine('postgresql://postgres:password@localhost/tenant_management')
    engine.execute(f"SELECT create_tenant_database('{tenant.id}', '{database_name}')")
    
    # 2. Update tenant record
    tenant.database_name = database_name
    tenant.database_host = current_app.config['TENANT_DB_HOST']
    tenant.database_port = current_app.config['TENANT_DB_PORT']
    tenant.database_user = f"tenant_{tenant.id}"
    
    # 3. Create tables in tenant database
    tenant_engine = create_engine(
        f"postgresql://{tenant.database_user}:{tenant.database_password}@{tenant.database_host}:{tenant.database_port}/{database_name}"
    )
    Base.metadata.create_all(tenant_engine)
    
    # 4. Initialize tenant data
    initialize_tenant_data(tenant.id)
```

---

## Deployment Strategies

### Single Instance Multi-Tenancy

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│              Application Servers (Multiple)               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   App 1     │ │   App 2     │ │   App 3     │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Database Cluster                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Master    │ │   Replica   │ │   Replica   │   │
│  │   Database  │ │   Database  │ │   Database  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### Docker Compose Configuration

```yaml
# docker-compose.multi-tenant.yml
version: '3.8'

services:
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

  app:
    build: .
    environment:
      - FLASK_ENV=production
      - MULTI_TENANT=True
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/tenant_management
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    deploy:
      replicas: 3

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=tenant_management
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Multi-Instance Multi-Tenancy

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Global Load Balancer                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                         │
┌───────▼────────┐    ┌────────▼───────┐
│  Region A      │    │  Region B      │
│                │    │                │
│ ┌────────────┐  │    │ ┌────────────┐ │
│ │ Load Bal.  │  │    │ │ Load Bal.  │ │
│ └─────┬──────┘  │    │ └─────┬──────┘ │
│       │         │    │       │         │
│ ┌─────▼──────┐  │    │ ┌─────▼──────┐ │
│ │ App Servers │  │    │ │ App Servers │ │
│ └─────┬──────┘  │    │ └─────┬──────┘ │
│       │         │    │       │         │
│ ┌─────▼──────┐  │    │ ┌─────▼──────┐ │
│ │ Database   │  │    │ │ Database   │ │
│ │ Cluster    │  │    │ │ Cluster    │ │
│ └────────────┘  │    │ └────────────┘ │
└─────────────────┘    └─────────────────┘
```

#### Kubernetes Deployment

```yaml
# k8s/multi-tenant-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pos-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: pos-app
  template:
    metadata:
      labels:
        app: pos-app
    spec:
      containers:
      - name: pos-app
        image: pos-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: MULTI_TENANT
          value: "True"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pos-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: pos-secrets
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: pos-app-service
spec:
  selector:
    app: pos-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pos-ingress
spec:
  tls:
  - hosts:
    - "*.yourdomain.com"
    secretName: pos-tls
  rules:
  - host: "*.yourdomain.com"
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: pos-app-service
            port:
              number: 80
```

---

## Scaling and Performance

### Horizontal Scaling

#### Database Sharding Strategy

```python
# utils/tenant_sharding.py
class TenantShardingManager:
    def __init__(self):
        self.shard_map = {}
        self.shard_count = int(os.environ.get('TENANT_SHARD_COUNT', 4))
    
    def get_tenant_shard(self, tenant_id):
        """Determine shard for tenant based on hash"""
        shard_index = hash(tenant_id) % self.shard_count
        return f"shard_{shard_index}"
    
    def get_shard_database_url(self, shard_name):
        """Get database URL for specific shard"""
        shard_config = current_app.config.get('TENANT_SHARDS', {})[shard_name]
        return (
            f"postgresql://{shard_config['user']}:{shard_config['password']}"
            f"@{shard_config['host']}:{shard_config['port']}/{shard_config['database']}"
        )
    
    def get_tenant_database_url(self, tenant_id):
        """Get database URL for tenant on appropriate shard"""
        shard_name = self.get_tenant_shard(tenant_id)
        return self.get_shard_database_url(shard_name)

# Configuration for sharding
TENANT_SHARDS = {
    'shard_0': {
        'host': 'shard0-db.example.com',
        'port': 5432,
        'database': 'tenant_shard_0',
        'user': 'shard0_user',
        'password': 'shard0_password'
    },
    'shard_1': {
        'host': 'shard1-db.example.com',
        'port': 5432,
        'database': 'tenant_shard_1',
        'user': 'shard1_user',
        'password': 'shard1_password'
    },
    # ... more shards
}
```

#### Connection Pool Management

```python
# utils/tenant_connection_pool.py
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
    
    def cleanup_inactive_pools(self):
        """Clean up pools for inactive tenants"""
        active_tenants = set(t.id for t in Tenant.query.filter_by(status='active').all())
        inactive_pools = set(self.pools.keys()) - active_tenants
        
        for tenant_id in inactive_pools:
            self.remove_pool(tenant_id)

# Global connection pool manager
tenant_pool_manager = TenantConnectionPool()
```

### Performance Optimization

#### Tenant-Aware Caching

```python
# utils/tenant_cache.py
class TenantCacheManager:
    def __init__(self):
        self.cache = current_app.config['CACHE']
    
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

# Usage in views
@app.route('/menu/items')
@login_required
def get_menu_items():
    tenant_id = get_current_tenant_id()
    cache_key = 'menu_items'
    
    # Try to get from cache
    cached_items = tenant_cache.get(tenant_id, cache_key)
    if cached_items:
        return jsonify(cached_items)
    
    # Get from database
    items = MenuItem.query_tenant(tenant_id).all()
    items_data = [item.to_dict() for item in items]
    
    # Cache for 1 hour
    tenant_cache.set(tenant_id, cache_key, items_data, timeout=3600)
    
    return jsonify(items_data)
```

#### Database Query Optimization

```python
# utils/tenant_queries.py
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

## Monitoring and Analytics

### Tenant Monitoring

#### Resource Usage Monitoring

```python
# monitoring/tenant_monitor.py
class TenantMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
    
    def track_tenant_usage(self, tenant_id):
        """Track resource usage for tenant"""
        # Database usage
        db_usage = self.get_database_usage(tenant_id)
        
        # Storage usage
        storage_usage = self.get_storage_usage(tenant_id)
        
        # API usage
        api_usage = self.get_api_usage(tenant_id)
        
        # Active users
        active_users = self.get_active_users(tenant_id)
        
        metrics = {
            'tenant_id': tenant_id,
            'timestamp': datetime.utcnow(),
            'database_usage': db_usage,
            'storage_usage': storage_usage,
            'api_usage': api_usage,
            'active_users': active_users
        }
        
        self.metrics_collector.record(metrics)
    
    def get_database_usage(self, tenant_id):
        """Get database usage statistics"""
        query = text("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                pg_size_pretty(pg_total_relation_size()) as total_relation_size,
                (SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database()) as active_connections
        """)
        
        result = db.session.execute(query).fetchone()
        return {
            'database_size': result[0],
            'total_relation_size': result[1],
            'active_connections': result[2]
        }
    
    def get_storage_usage(self, tenant_id):
        """Get storage usage for tenant"""
        tenant_path = f"uploads/tenants/{tenant_id}"
        
        if not os.path.exists(tenant_path):
            return {'total_size': 0, 'file_count': 0}
        
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(tenant_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return {
            'total_size': total_size,
            'file_count': file_count,
            'total_size_human': self.format_bytes(total_size)
        }
    
    def get_api_usage(self, tenant_id):
        """Get API usage statistics"""
        # This would typically come from your API gateway or logging system
        return {
            'requests_today': 1250,
            'requests_this_month': 35000,
            'average_response_time': 150,  # ms
            'error_rate': 0.5  # percentage
        }
```

#### Tenant Analytics Dashboard

```python
# routes/analytics.py
@app.route('/admin/analytics/tenant/<tenant_id>')
@login_required
@admin_required
def tenant_analytics(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    
    # Get analytics data
    date_range = {
        'start': request.args.get('start', datetime.utcnow() - timedelta(days=30)),
        'end': request.args.get('end', datetime.utcnow())
    }
    
    # Usage metrics
    usage_metrics = TenantMonitor().get_tenant_usage_metrics(tenant_id, date_range)
    
    # Business metrics
    business_metrics = TenantQueryOptimizer().get_tenant_analytics(tenant_id, date_range)
    
    # Performance metrics
    performance_metrics = TenantMonitor().get_tenant_performance_metrics(tenant_id, date_range)
    
    return render_template('admin/analytics/tenant.html',
                        tenant=tenant,
                        usage_metrics=usage_metrics,
                        business_metrics=business_metrics,
                        performance_metrics=performance_metrics,
                        date_range=date_range)
```

### Health Monitoring

#### Tenant Health Checks

```python
# monitoring/health_check.py
class TenantHealthChecker:
    def __init__(self):
        self.healthy_tenants = set()
        self.unhealthy_tenants = set()
    
    def check_tenant_health(self, tenant_id):
        """Check health of specific tenant"""
        health_status = {
            'tenant_id': tenant_id,
            'timestamp': datetime.utcnow(),
            'checks': {}
        }
        
        # Database connectivity
        try:
            tenant_db = get_tenant_database(tenant_id)
            tenant_db.execute('SELECT 1')
            health_status['checks']['database'] = {'status': 'healthy', 'response_time': 50}
        except Exception as e:
            health_status['checks']['database'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Cache connectivity
        try:
            cache_key = f"health_check_{tenant_id}"
            cache.set(cache_key, 'test', timeout=10)
            cache_result = cache.get(cache_key)
            health_status['checks']['cache'] = {'status': 'healthy', 'response_time': 10}
        except Exception as e:
            health_status['checks']['cache'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Storage accessibility
        try:
            tenant_path = f"uploads/tenants/{tenant_id}"
            os.makedirs(tenant_path, exist_ok=True)
            test_file = os.path.join(tenant_path, 'health_check.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            health_status['checks']['storage'] = {'status': 'healthy'}
        except Exception as e:
            health_status['checks']['storage'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Overall health
        overall_status = 'healthy'
        for check in health_status['checks'].values():
            if check['status'] != 'healthy':
                overall_status = 'unhealthy'
                break
        
        health_status['overall_status'] = overall_status
        
        # Update tracking sets
        if overall_status == 'healthy':
            self.healthy_tenants.add(tenant_id)
            self.unhealthy_tenants.discard(tenant_id)
        else:
            self.unhealthy_tenants.add(tenant_id)
            self.healthy_tenants.discard(tenant_id)
        
        return health_status
    
    def get_all_tenants_health(self):
        """Check health of all active tenants"""
        active_tenants = Tenant.query.filter_by(status='active').all()
        health_results = {}
        
        for tenant in active_tenants:
            health_results[tenant.id] = self.check_tenant_health(tenant.id)
        
        return health_results

# Health check endpoint
@app.route('/health/tenants')
def tenants_health():
    """Health check endpoint for all tenants"""
    health_checker = TenantHealthChecker()
    health_results = health_checker.get_all_tenants_health()
    
    return jsonify({
        'status': 'healthy' if health_checker.unhealthy_tenants else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'tenants': health_results,
        'summary': {
            'total_tenants': len(health_results),
            'healthy_tenants': len(health_checker.healthy_tenants),
            'unhealthy_tenants': len(health_checker.unhealthy_tenants)
        }
    })
```

---

## Best Practices

### Security Best Practices

#### 1. Data Isolation

```python
# ✅ Good: Always filter by tenant_id
def get_customer_orders(customer_id):
    tenant_id = get_current_tenant_id()
    return Order.query.filter_by(
        customer_id=customer_id,
        tenant_id=tenant_id
    ).all()

# ❌ Bad: Missing tenant filter
def get_customer_orders(customer_id):
    return Order.query.filter_by(customer_id=customer_id).all()
```

#### 2. Input Validation

```python
# ✅ Good: Validate tenant access
def get_order(order_id):
    tenant_id = get_current_tenant_id()
    order = Order.query.filter_by(
        id=order_id,
        tenant_id=tenant_id
    ).first()
    
    if not order:
        abort(404)  # Not found
    
    return order

# ❌ Bad: No tenant validation
def get_order(order_id):
    order = Order.query.get(order_id)
    return order
```

#### 3. Secure Configuration

```python
# ✅ Good: Use environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
TENANT_SECRET_KEY = os.environ.get('TENANT_SECRET_KEY')

# ❌ Bad: Hardcode sensitive data
DATABASE_URL = 'postgresql://user:pass@localhost/db'
TENANT_SECRET_KEY = 'hardcoded_secret_key'
```

### Performance Best Practices

#### 1. Connection Pooling

```python
# ✅ Good: Use connection pools per tenant
class TenantConnectionManager:
    def __init__(self):
        self.pools = {}
    
    def get_connection(self, tenant_id):
        if tenant_id not in self.pools:
            self.pools[tenant_id] = create_tenant_pool(tenant_id)
        return self.pools[tenant_id]

# ❌ Bad: Create new connection for each request
def get_tenant_connection(tenant_id):
    return create_engine(get_tenant_database_url(tenant_id))
```

#### 2. Caching Strategy

```python
# ✅ Good: Tenant-aware caching
def get_tenant_menu_items(tenant_id):
    cache_key = f"menu_items_{tenant_id}"
    cached_items = cache.get(cache_key)
    
    if cached_items:
        return cached_items
    
    items = MenuItem.query_tenant(tenant_id).all()
    cache.set(cache_key, items, timeout=3600)
    return items

# ❌ Bad: No caching or global cache
def get_menu_items():
    return MenuItem.query.all()
```

### Operational Best Practices

#### 1. Tenant Onboarding

```python
# ✅ Good: Structured onboarding process
def onboard_new_tenant(tenant_data):
    try:
        # 1. Create tenant record
        tenant = create_tenant(tenant_data)
        
        # 2. Setup infrastructure
        setup_tenant_infrastructure(tenant)
        
        # 3. Initialize data
        initialize_tenant_data(tenant.id)
        
        # 4. Send welcome email
        send_welcome_email(tenant)
        
        # 5. Log onboarding
        log_tenant_onboarding(tenant, 'success')
        
        return tenant
        
    except Exception as e:
        # Rollback on failure
        rollback_tenant_creation(tenant)
        log_tenant_onboarding(tenant, f'failed: {str(e)}')
        raise

# ❌ Bad: No error handling or rollback
def onboard_new_tenant(tenant_data):
    tenant = create_tenant(tenant_data)
    setup_tenant_infrastructure(tenant)
    return tenant
```

#### 2. Monitoring and Alerting

```python
# ✅ Good: Comprehensive monitoring
def monitor_tenant_health():
    for tenant in get_active_tenants():
        health_status = check_tenant_health(tenant.id)
        
        if health_status['overall_status'] != 'healthy':
            send_alert(
                recipient='admin@example.com',
                subject=f'Tenant {tenant.name} Health Issue',
                message=health_status
            )
        
        record_health_metrics(tenant.id, health_status)

# ❌ Bad: No monitoring or alerting
def monitor_tenant_health():
    pass  # No implementation
```

---

## Troubleshooting

### Common Multi-Tenancy Issues

#### 1. Tenant Data Leakage

**Problem**: Data from one tenant visible to another

**Causes**:
- Missing tenant_id filters
- Incorrect database connections
- Broken row-level security

**Solutions**:
```python
# Add tenant_id to all queries
def secure_query(model):
    tenant_id = get_current_tenant_id()
    return model.query.filter(model.tenant_id == tenant_id)

# Verify database connection
def verify_tenant_isolation(tenant_id):
    # Test query with wrong tenant_id
    wrong_tenant_data = secure_query(Order).filter(
        Order.tenant_id == 'wrong_tenant_id'
    ).first()
    assert wrong_tenant_data is None
```

#### 2. Performance Issues

**Problem**: Slow queries for large tenant counts

**Causes**:
- Missing indexes on tenant_id
- Inefficient connection pooling
- No query optimization

**Solutions**:
```sql
-- Add indexes for tenant_id
CREATE INDEX idx_orders_tenant_id ON orders(tenant_id);
CREATE INDEX idx_customers_tenant_id ON customers(tenant_id);

-- Use partitioning for large tables
CREATE TABLE orders_partitioned (
    LIKE orders INCLUDING ALL
) PARTITION BY LIST (tenant_id);

CREATE TABLE orders_tenant_001 PARTITION OF orders_partitioned
FOR VALUES IN ('tenant_001');
```

#### 3. Resource Contention

**Problem**: One tenant affecting others

**Causes**:
- No resource limits
- Unoptimized queries
- Connection pool exhaustion

**Solutions**:
```python
# Implement resource limits
class TenantResourceLimiter:
    def __init__(self):
        self.limits = {
            'max_connections': 10,
            'max_queries_per_minute': 1000,
            'max_storage_gb': 50
        }
    
    def check_tenant_limits(self, tenant_id):
        current_usage = self.get_tenant_usage(tenant_id)
        
        for resource, limit in self.limits.items():
            if current_usage[resource] > limit:
                raise TenantLimitExceeded(resource, limit)
```

### Debugging Tools

#### Tenant Debug Middleware

```python
# middleware/tenant_debug.py
class TenantDebugMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        if current_app.debug:
            # Add debug headers
            tenant_id = environ.get('TENANT_ID')
            if tenant_id:
                environ['HTTP_X_DEBUG_TENANT_ID'] = tenant_id
                environ['HTTP_X_DEBUG_DATABASE'] = get_tenant_database_url(tenant_id)
        
        return self.app(environ, start_response)

# Add to app for debugging
if app.debug:
    app.wsgi_app = TenantDebugMiddleware(app.wsgi_app)
```

#### Tenant Isolation Validator

```python
# utils/tenant_validator.py
class TenantIsolationValidator:
    @staticmethod
    def validate_tenant_isolation():
        """Validate tenant isolation is working correctly"""
        issues = []
        
        # Check 1: Verify tenant_id filters
        test_tenant_id = 'test_tenant_001'
        test_query = Order.query.filter_by(tenant_id=test_tenant_id)
        
        if 'tenant_id' not in str(test_query):
            issues.append("Missing tenant_id filter in Order query")
        
        # Check 2: Verify database connections
        for tenant in Tenant.query.limit(10).all():
            try:
                conn = get_tenant_database(tenant.id)
                conn.execute('SELECT 1')
            except Exception as e:
                issues.append(f"Database connection failed for tenant {tenant.id}: {e}")
        
        # Check 3: Verify row-level security
        test_query = "SELECT * FROM orders WHERE tenant_id = 'wrong_tenant'"
        try:
            result = db.session.execute(test_query).fetchall()
            if result:
                issues.append("Row-level security not working correctly")
        except Exception as e:
            # Expected to fail with RLS
            pass
        
        return issues

# Run validation periodically
@app.cli.command()
def validate_tenant_isolation():
    """Validate tenant isolation"""
    issues = TenantIsolationValidator.validate_tenant_isolation()
    
    if issues:
        print("Tenant isolation issues found:")
        for issue in issues:
            print(f"  ❌ {issue}")
    else:
        print("✅ Tenant isolation is working correctly")
```

---

**Version**: 2.0.0 Multi-Tenancy Guide  
**Last Updated**: December 2024  
**Documentation**: Flask POS Development Team