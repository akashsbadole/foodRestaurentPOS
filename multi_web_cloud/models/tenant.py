"""
Tenant model for multi-tenant support
"""

from datetime import datetime
import uuid
from . import db

class Tenant(db.Model):
    """Tenant model for multi-tenant architecture"""
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    subdomain = db.Column(db.String(50), unique=True, nullable=False)
    custom_domain = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum('trial', 'active', 'suspended', 'cancelled', name='tenant_status'), default='trial')
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=True)
    
    # Database configuration (for database-per-tenant strategy)
    database_name = db.Column(db.String(100), nullable=True)
    database_host = db.Column(db.String(100), nullable=True)
    database_port = db.Column(db.Integer, default=5432)
    database_user = db.Column(db.String(50), nullable=True)
    database_password = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True)
    orders = db.relationship('Order', backref='tenant', lazy=True)
    settings = db.relationship('Settings', backref='tenant', lazy=True)
    tenant_settings = db.relationship('TenantSettings', backref='tenant', lazy=True, uselist=False)
    subscription = db.relationship('TenantSubscription', backref='tenant', lazy=True, uselist=False)
    feature_flags = db.relationship('TenantFeatureFlag', backref='tenant', lazy=True)
    usage_records = db.relationship('TenantUsage', backref='tenant', lazy=True)
    
    def __init__(self, name, subdomain, custom_domain=None, status='trial'):
        self.name = name
        self.subdomain = subdomain
        self.custom_domain = custom_domain
        self.status = status
    
    def to_dict(self):
        """Convert tenant to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'status': self.status,
            'plan_id': self.plan_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_active(self):
        """Check if tenant is active"""
        return self.status == 'active'
    
    def is_trial(self):
        """Check if tenant is in trial period"""
        return self.status == 'trial'
    
    def is_suspended(self):
        """Check if tenant is suspended"""
        return self.status == 'suspended'
    
    def is_cancelled(self):
        """Check if tenant is cancelled"""
        return self.status == 'cancelled'
    
    def activate(self):
        """Activate tenant"""
        self.status = 'active'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def suspend(self):
        """Suspend tenant"""
        self.status = 'suspended'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel(self):
        """Cancel tenant"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_by_subdomain(subdomain):
        """Get tenant by subdomain"""
        return Tenant.query.filter_by(subdomain=subdomain).first()
    
    @staticmethod
    def get_by_domain(domain):
        """Get tenant by custom domain"""
        return Tenant.query.filter_by(custom_domain=domain).first()
    
    @staticmethod
    def get_active_tenants():
        """Get all active tenants"""
        return Tenant.query.filter_by(status='active').all()
    
    @staticmethod
    def get_trial_tenants():
        """Get all trial tenants"""
        return Tenant.query.filter_by(status='trial').all()
    
    def __repr__(self):
        return f'<Tenant {self.name} ({self.subdomain})>'


class TenantSettings(db.Model):
    """Tenant-specific settings"""
    __tablename__ = 'tenant_settings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    
    # Restaurant Information
    restaurant_name = db.Column(db.String(100), nullable=True)
    gst_number = db.Column(db.String(15), nullable=True)
    contact_email = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(20), nullable=True)
    
    # Branding
    logo_url = db.Column(db.String(255), nullable=True)
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
    razorpay_key_id = db.Column(db.String(100), nullable=True)
    razorpay_key_secret = db.Column(db.String(100), nullable=True)
    email_settings = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert tenant settings to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'restaurant_name': self.restaurant_name,
            'gst_number': self.gst_number,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'logo_url': self.logo_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'currency': self.currency,
            'tax_rate': self.tax_rate,
            'service_charge': self.service_charge,
            'enable_crm': self.enable_crm,
            'enable_loyalty': self.enable_loyalty,
            'enable_offline': self.enable_offline,
            'enable_reports': self.enable_reports,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<TenantSettings for {self.tenant_id}>'


class SubscriptionPlan(db.Model):
    """Subscription plans for tenants"""
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
    features = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenants = db.relationship('TenantSubscription', backref='plan', lazy=True)
    
    def __init__(self, name, code, price_monthly, price_yearly):
        self.name = name
        self.code = code
        self.price_monthly = price_monthly
        self.price_yearly = price_yearly
    
    def to_dict(self):
        """Convert subscription plan to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'price_monthly': self.price_monthly,
            'price_yearly': self.price_yearly,
            'max_users': self.max_users,
            'max_orders_per_month': self.max_orders_per_month,
            'max_storage_gb': self.max_storage_gb,
            'features': self.features,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def has_feature(self, feature_name):
        """Check if plan includes a feature"""
        if not self.features:
            return False
        return self.features.get(feature_name, False)
    
    @staticmethod
    def get_by_code(code):
        """Get plan by code"""
        return SubscriptionPlan.query.filter_by(code=code).first()
    
    @staticmethod
    def get_all_active():
        """Get all active plans"""
        return SubscriptionPlan.query.all()
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name} ({self.code})>'


class TenantSubscription(db.Model):
    """Tenant subscription information"""
    __tablename__ = 'tenant_subscriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    plan_id = db.Column(db.String(36), db.ForeignKey('subscription_plans.id'), nullable=False)
    
    status = db.Column(db.Enum('active', 'cancelled', 'expired', 'suspended', name='subscription_status'), default='active')
    billing_cycle = db.Column(db.Enum('monthly', 'yearly', name='billing_cycle'), default='monthly')
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, tenant_id, plan_id, billing_cycle='monthly'):
        self.tenant_id = tenant_id
        self.plan_id = plan_id
        self.billing_cycle = billing_cycle
    
    def is_active(self):
        """Check if subscription is active"""
        return self.status == 'active' and (not self.expires_at or self.expires_at > datetime.utcnow())
    
    def is_expired(self):
        """Check if subscription is expired"""
        return self.expires_at and self.expires_at <= datetime.utcnow()
    
    def extend(self, months=1):
        """Extend subscription by specified months"""
        from datetime import timedelta
        
        if self.expires_at:
            self.expires_at += timedelta(days=30 * months)
        else:
            self.expires_at = datetime.utcnow() + timedelta(days=30 * months)
        
        self.status = 'active'
        db.session.commit()
    
    def cancel(self):
        """Cancel subscription"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'plan_id': self.plan_id,
            'status': self.status,
            'billing_cycle': self.billing_cycle,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<TenantSubscription for {self.tenant_id}>'


class TenantFeatureFlag(db.Model):
    """Feature flags for tenants"""
    __tablename__ = 'tenant_feature_flags'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    is_enabled = db.Column(db.Boolean, default=False)
    configuration = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, tenant_id, feature_name, is_enabled=False, configuration=None):
        self.tenant_id = tenant_id
        self.feature_name = feature_name
        self.is_enabled = is_enabled
        self.configuration = configuration
    
    def enable(self, configuration=None):
        """Enable feature"""
        self.is_enabled = True
        if configuration:
            self.configuration = configuration
        db.session.commit()
    
    def disable(self):
        """Disable feature"""
        self.is_enabled = False
        db.session.commit()
    
    def to_dict(self):
        """Convert feature flag to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'feature_name': self.feature_name,
            'is_enabled': self.is_enabled,
            'configuration': self.configuration,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<TenantFeatureFlag {self.feature_name} for {self.tenant_id}>'


class TenantUsage(db.Model):
    """Usage tracking for tenants"""
    __tablename__ = 'tenant_usage'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    usage_type = db.Column(db.Enum('orders', 'users', 'storage', 'api_calls', name='usage_type'), nullable=False)
    usage_value = db.Column(db.Float, nullable=False)
    usage_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, tenant_id, usage_type, usage_value, usage_date):
        self.tenant_id = tenant_id
        self.usage_type = usage_type
        self.usage_value = usage_value
        self.usage_date = usage_date
    
    def to_dict(self):
        """Convert usage record to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'usage_type': self.usage_type,
            'usage_value': self.usage_value,
            'usage_date': self.usage_date.isoformat() if self.usage_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<TenantUsage {self.usage_type}: {self.usage_value} for {self.tenant_id}>'