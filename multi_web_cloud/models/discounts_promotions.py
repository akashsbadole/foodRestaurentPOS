"""
Discounts & Promotions module models for handling coupon codes, BOGO offers,
volume and time-based discounts, category discounts, happy hours,
and promotional pricing engine.
"""

from datetime import datetime, date, time
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from models import db
from models.feature_aware_model import FeatureAwareModel


class CouponCode(FeatureAwareModel):
    """Coupon code management"""
    __tablename__ = 'coupon_codes'
    __feature_key__ = 'FEATURE_COUPON_CODES'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    coupon_code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Discount details
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount, buy_x_get_y
    discount_value = Column(Numeric(10, 2), nullable=False)  # Percentage or fixed amount
    minimum_order_amount = Column(Numeric(12, 2))
    maximum_discount_amount = Column(Numeric(12, 2))
    
    # Usage limits
    usage_limit = Column(Integer)  # Total uses allowed
    usage_limit_per_customer = Column(Integer)  # Uses per customer
    used_count = Column(Integer, default=0)
    
    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Applicability
    applies_to = Column(JSON)  # products, categories, customers, etc.
    exclude_items = Column(JSON)  # Items excluded from discount
    first_time_customers_only = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # Can be used by anyone or specific customers only
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='coupon_codes')
    creator = relationship('User', foreign_keys=[created_by])
    coupon_usages = relationship('CouponUsage', back_populates='coupon', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CouponCode {self.coupon_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'coupon_code': self.coupon_code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'minimum_order_amount': float(self.minimum_order_amount) if self.minimum_order_amount else None,
            'maximum_discount_amount': float(self.maximum_discount_amount) if self.maximum_discount_amount else None,
            'usage_limit': self.usage_limit,
            'usage_limit_per_customer': self.usage_limit_per_customer,
            'used_count': self.used_count,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'applies_to': self.applies_to,
            'exclude_items': self.exclude_items,
            'first_time_customers_only': self.first_time_customers_only,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            self.valid_until >= now and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    @hybrid_property
    def is_expired(self):
        """Check if coupon has expired"""
        return datetime.utcnow() > self.valid_until
    
    @hybrid_property
    def remaining_uses(self):
        """Calculate remaining uses"""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.used_count)


class CouponUsage(FeatureAwareModel):
    """Coupon usage tracking"""
    __tablename__ = 'coupon_usages'
    __feature_key__ = 'FEATURE_COUPON_CODES'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    coupon_id = Column(Integer, ForeignKey('coupon_codes.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    discount_amount = Column(Numeric(12, 2), nullable=False)
    order_amount = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='coupon_usages')
    coupon = relationship('CouponCode', back_populates='coupon_usages')
    customer = relationship('Customer', back_populates='coupon_usages')
    order = relationship('Order', back_populates='coupon_usages')
    
    def __repr__(self):
        return f'<CouponUsage {self.coupon_id}:{self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'coupon_id': self.coupon_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'discount_amount': float(self.discount_amount),
            'order_amount': float(self.order_amount),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BOGOOffer(FeatureAwareModel):
    """Buy One Get One (BOGO) offers"""
    __tablename__ = 'bogo_offers'
    __feature_key__ = 'FEATURE_BOGO_OFFERS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    offer_code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # BOGO configuration
    buy_quantity = Column(Integer, nullable=False)
    get_quantity = Column(Integer, nullable=False)
    buy_type = Column(String(20))  # specific, category, brand
    get_type = Column(String(20))  # specific, category, brand, same_price, lower_price
    
    # Product/category mappings
    buy_products = Column(JSON)  # Array of product IDs for "buy" items
    buy_categories = Column(JSON)  # Array of category IDs for "buy" items
    get_products = Column(JSON)  # Array of product IDs for "get" items
    get_categories = Column(JSON)  # Array of category IDs for "get" items
    get_value_limit = Column(Numeric(10, 2))  # Maximum value of "get" item
    
    # Discount on get item
    get_discount_type = Column(String(20))  # percentage, fixed, free
    get_discount_value = Column(Numeric(10, 2))
    
    # Usage limits
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0)
    customer_usage_limit = Column(Integer)
    
    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Time restrictions
    valid_days = Column(JSON)  # Days of week [0,1,2,3,4,5,6]
    valid_hours_start = Column(Time)  # Start time for daily validity
    valid_hours_end = Column(Time)  # End time for daily validity
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)  # Automatically apply in cart
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='bogo_offers')
    creator = relationship('User', foreign_keys=[created_by])
    bogo_usages = relationship('BOGOUsage', back_populates='bogo_offer', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BOGOOffer {self.offer_code}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'offer_code': self.offer_code,
            'name': self.name,
            'description': self.description,
            'buy_quantity': self.buy_quantity,
            'get_quantity': self.get_quantity,
            'buy_type': self.buy_type,
            'get_type': self.get_type,
            'buy_products': self.buy_products,
            'buy_categories': self.buy_categories,
            'get_products': self.get_products,
            'get_categories': self.get_categories,
            'get_value_limit': float(self.get_value_limit) if self.get_value_limit else None,
            'get_discount_type': self.get_discount_type,
            'get_discount_value': float(self.get_discount_value) if self.get_discount_value else None,
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'customer_usage_limit': self.customer_usage_limit,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'valid_days': self.valid_days,
            'valid_hours_start': self.valid_hours_start.isoformat() if self.valid_hours_start else None,
            'valid_hours_end': self.valid_hours_end.isoformat() if self.valid_hours_end else None,
            'is_active': self.is_active,
            'auto_apply': self.auto_apply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_valid(self):
        """Check if BOGO offer is currently valid"""
        now = datetime.utcnow()
        if not self.is_active or now < self.valid_from or now > self.valid_until:
            return False
        
        # Check day of week
        if self.valid_days and now.weekday() not in self.valid_days:
            return False
        
        # Check time of day
        if self.valid_hours_start and self.valid_hours_end:
            current_time = now.time()
            if not (self.valid_hours_start <= current_time <= self.valid_hours_end):
                return False
        
        return True
    
    @hybrid_property
    def remaining_uses(self):
        """Calculate remaining uses"""
        if self.usage_limit is None:
            return None
        return max(0, self.usage_limit - self.used_count)


class BOGOUsage(FeatureAwareModel):
    """BOGO offer usage tracking"""
    __tablename__ = 'bogo_usages'
    __feature_key__ = 'FEATURE_BOGO_OFFERS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    bogo_offer_id = Column(Integer, ForeignKey('bogo_offers.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    buy_items = Column(JSON)  # Items that qualified as "buy"
    get_items = Column(JSON)  # Items that were given as "get"
    total_discount = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='bogo_usages')
    bogo_offer = relationship('BOGOOffer', back_populates='bogo_usages')
    customer = relationship('Customer', back_populates='bogo_usages')
    order = relationship('Order', back_populates='bogo_usages')
    
    def __repr__(self):
        return f'<BOGOUsage {self.bogo_offer_id}:{self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'bogo_offer_id': self.bogo_offer_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'buy_items': self.buy_items,
            'get_items': self.get_items,
            'total_discount': float(self.total_discount),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VolumeDiscount(FeatureAwareModel):
    """Volume-based discounts"""
    __tablename__ = 'volume_discounts'
    __feature_key__ = 'FEATURE_VOLUME_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Discount tiers
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    tiers = Column(JSON)  # Array of {min_quantity, max_quantity, discount_value}
    
    # Applicability
    applies_to = Column(JSON)  # products, categories, brands
    product_ids = Column(JSON)
    category_ids = Column(JSON)
    brand_ids = Column(JSON)
    
    # Calculation method
    based_on = Column(String(20), default='quantity')  # quantity, amount, weight
    measurement_unit = Column(String(20))  # pieces, kg, liters, etc.
    
    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Priority and stacking
    priority = Column(Integer, default=0)  # Higher priority takes precedence
    can_stack = Column(Boolean, default=False)  # Can be combined with other discounts
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='volume_discounts')
    creator = relationship('User', foreign_keys=[created_by])
    volume_discount_usages = relationship('VolumeDiscountUsage', back_populates='volume_discount', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<VolumeDiscount {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'tiers': self.tiers,
            'applies_to': self.applies_to,
            'product_ids': self.product_ids,
            'category_ids': self.category_ids,
            'brand_ids': self.brand_ids,
            'based_on': self.based_on,
            'measurement_unit': self.measurement_unit,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'priority': self.priority,
            'can_stack': self.can_stack,
            'is_active': self.is_active,
            'auto_apply': self.auto_apply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def calculate_discount(self, quantity, amount=None):
        """Calculate discount based on quantity/amount"""
        if not self.is_active or not self.tiers:
            return Decimal('0')
        
        value = quantity if self.based_on == 'quantity' else amount
        if value is None:
            return Decimal('0')
        
        # Find applicable tier
        applicable_tier = None
        for tier in self.tiers:
            min_qty = tier.get('min_quantity', 0)
            max_qty = tier.get('max_quantity', float('inf'))
            
            if min_qty <= value <= max_qty:
                applicable_tier = tier
                break
        
        if not applicable_tier:
            return Decimal('0')
        
        discount_value = Decimal(str(applicable_tier.get('discount_value', 0)))
        
        if self.discount_type == 'percentage':
            return amount * (discount_value / Decimal('100')) if amount else Decimal('0')
        else:
            return discount_value
    
    @hybrid_property
    def is_valid(self):
        """Check if volume discount is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            self.valid_until >= now
        )


class VolumeDiscountUsage(FeatureAwareModel):
    """Volume discount usage tracking"""
    __tablename__ = 'volume_discount_usages'
    __feature_key__ = 'FEATURE_VOLUME_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    volume_discount_id = Column(Integer, ForeignKey('volume_discounts.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    quantity = Column(Numeric(12, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    applied_tier = Column(JSON)  # Which tier was applied
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='volume_discount_usages')
    volume_discount = relationship('VolumeDiscount', back_populates='volume_discount_usages')
    customer = relationship('Customer', back_populates='volume_discount_usages')
    order = relationship('Order', back_populates='volume_discount_usages')
    
    def __repr__(self):
        return f'<VolumeDiscountUsage {self.volume_discount_id}:{self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'volume_discount_id': self.volume_discount_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'quantity': float(self.quantity),
            'amount': float(self.amount),
            'discount_amount': float(self.discount_amount),
            'applied_tier': self.applied_tier,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TimeBasedDiscount(FeatureAwareModel):
    """Time-based discounts (happy hours, etc.)"""
    __tablename__ = 'time_based_discounts'
    __feature_key__ = 'FEATURE_TIME_BASED_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Discount details
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)
    
    # Time schedule
    days_of_week = Column(JSON)  # [0,1,2,3,4,5,6] for Mon-Sun
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    # Date range
    valid_from = Column(Date)
    valid_until = Column(Date)
    
    # Applicability
    applies_to = Column(JSON)  # products, categories, entire_order
    product_ids = Column(JSON)
    category_ids = Column(JSON)
    minimum_order_amount = Column(Numeric(12, 2))
    
    # Priority and stacking
    priority = Column(Integer, default=0)
    can_stack = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='time_based_discounts')
    creator = relationship('User', foreign_keys=[created_by])
    time_discount_usages = relationship('TimeDiscountUsage', back_populates='time_discount', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TimeBasedDiscount {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'days_of_week': self.days_of_week,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'applies_to': self.applies_to,
            'product_ids': self.product_ids,
            'category_ids': self.category_ids,
            'minimum_order_amount': float(self.minimum_order_amount) if self.minimum_order_amount else None,
            'priority': self.priority,
            'can_stack': self.can_stack,
            'is_active': self.is_active,
            'auto_apply': self.auto_apply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_active_now(self):
        """Check if discount is active at current time"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        current_date = now.date()
        current_time = now.time()
        current_day = now.weekday()
        
        # Check date range
        if self.valid_from and current_date < self.valid_from:
            return False
        if self.valid_until and current_date > self.valid_until:
            return False
        
        # Check day of week
        if self.days_of_week and current_day not in self.days_of_week:
            return False
        
        # Check time range
        if self.start_time and self.end_time:
            if not (self.start_time <= current_time <= self.end_time):
                return False
        
        return True


class TimeDiscountUsage(FeatureAwareModel):
    """Time-based discount usage tracking"""
    __tablename__ = 'time_discount_usages'
    __feature_key__ = 'FEATURE_TIME_BASED_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    time_discount_id = Column(Integer, ForeignKey('time_based_discounts.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    order_amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='time_discount_usages')
    time_discount = relationship('TimeBasedDiscount', back_populates='time_discount_usages')
    customer = relationship('Customer', back_populates='time_discount_usages')
    order = relationship('Order', back_populates='time_discount_usages')
    
    def __repr__(self):
        return f'<TimeDiscountUsage {self.time_discount_id}:{self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'time_discount_id': self.time_discount_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'order_amount': float(self.order_amount),
            'discount_amount': float(self.discount_amount),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CategoryDiscount(FeatureAwareModel):
    """Category-based discounts"""
    __tablename__ = 'category_discounts'
    __feature_key__ = 'FEATURE_CATEGORY_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Discount details
    discount_type = Column(String(20), nullable=False)  # percentage, fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)
    
    # Category configuration
    category_ids = Column(JSON)  # Array of category IDs
    exclude_subcategories = Column(Boolean, default=False)
    include_child_categories = Column(Boolean, default=True)
    
    # Additional conditions
    minimum_quantity = Column(Integer)
    minimum_amount = Column(Numeric(12, 2))
    maximum_discount_amount = Column(Numeric(12, 2))
    
    # Customer eligibility
    customer_groups = Column(JSON)  # Array of customer group IDs
    first_purchase_only = Column(Boolean, default=False)
    
    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Priority and stacking
    priority = Column(Integer, default=0)
    can_stack = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='category_discounts')
    creator = relationship('User', foreign_keys=[created_by])
    category_discount_usages = relationship('CategoryDiscountUsage', back_populates='category_discount', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CategoryDiscount {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'category_ids': self.category_ids,
            'exclude_subcategories': self.exclude_subcategories,
            'include_child_categories': self.include_child_categories,
            'minimum_quantity': self.minimum_quantity,
            'minimum_amount': float(self.minimum_amount) if self.minimum_amount else None,
            'maximum_discount_amount': float(self.maximum_discount_amount) if self.maximum_discount_amount else None,
            'customer_groups': self.customer_groups,
            'first_purchase_only': self.first_purchase_only,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'priority': self.priority,
            'can_stack': self.can_stack,
            'is_active': self.is_active,
            'auto_apply': self.auto_apply,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_valid(self):
        """Check if category discount is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            self.valid_until >= now
        )


class CategoryDiscountUsage(FeatureAwareModel):
    """Category discount usage tracking"""
    __tablename__ = 'category_discount_usages'
    __feature_key__ = 'FEATURE_CATEGORY_DISCOUNTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    category_discount_id = Column(Integer, ForeignKey('category_discounts.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    category_id = Column(Integer, ForeignKey('categories.id'))  # Which category was applied
    order_amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='category_discount_usages')
    category_discount = relationship('CategoryDiscount', back_populates='category_discount_usages')
    customer = relationship('Customer', back_populates='category_discount_usages')
    order = relationship('Order', back_populates='category_discount_usages')
    category = relationship('Category', back_populates='category_discount_usages')
    
    def __repr__(self):
        return f'<CategoryDiscountUsage {self.category_discount_id}:{self.customer_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'category_discount_id': self.category_discount_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'category_id': self.category_id,
            'order_amount': float(self.order_amount),
            'discount_amount': float(self.discount_amount),
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PromotionalPricing(FeatureAwareModel):
    """Promotional pricing engine"""
    __tablename__ = 'promotional_pricing'
    __feature_key__ = 'FEATURE_PROMOTIONAL_PRICING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Pricing rules
    pricing_type = Column(String(20), nullable=False)  # special_price, discount, bundle
    trigger_condition = Column(JSON)  # Conditions to trigger this pricing
    
    # Product configuration
    product_ids = Column(JSON)  # Products this applies to
    category_ids = Column(JSON)  # Categories this applies to
    brand_ids = Column(JSON)  # Brands this applies to
    
    # Pricing details
    special_prices = Column(JSON)  # {product_id: new_price}
    discount_rules = Column(JSON)  # Complex discount rules
    bundle_config = Column(JSON)  # Bundle pricing configuration
    
    # Validity period
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    
    # Usage limits
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0)
    customer_usage_limit = Column(Integer)
    
    # Priority and exclusivity
    priority = Column(Integer, default=0)
    is_exclusive = Column(Boolean, default=False)  # Cannot be combined with other offers
    
    # Status
    is_active = Column(Boolean, default=True)
    auto_apply = Column(Boolean, default=True)
    
    # Display settings
    show_original_price = Column(Boolean, default=True)
    promo_label = Column(String(100))  # Label to show on product
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='promotional_pricing')
    creator = relationship('User', foreign_keys=[created_by])
    promotional_pricing_usages = relationship('PromotionalPricingUsage', back_populates='promotional_pricing', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PromotionalPricing {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'name': self.name,
            'description': self.description,
            'pricing_type': self.pricing_type,
            'trigger_condition': self.trigger_condition,
            'product_ids': self.product_ids,
            'category_ids': self.category_ids,
            'brand_ids': self.brand_ids,
            'special_prices': self.special_prices,
            'discount_rules': self.discount_rules,
            'bundle_config': self.bundle_config,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'usage_limit': self.usage_limit,
            'used_count': self.used_count,
            'customer_usage_limit': self.customer_usage_limit,
            'priority': self.priority,
            'is_exclusive': self.is_exclusive,
            'is_active': self.is_active,
            'auto_apply': self.auto_apply,
            'show_original_price': self.show_original_price,
            'promo_label': self.promo_label,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_valid(self):
        """Check if promotional pricing is currently valid"""
        now = datetime.utcnow()
        return (
            self.is_active and
            self.valid_from <= now and
            self.valid_until >= now and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    def calculate_price(self, product_id, original_price, quantity=1, customer_id=None):
        """Calculate promotional price for a product"""
        if not self.is_valid:
            return original_price
        
        # Check if product is eligible
        if (self.product_ids and product_id not in self.product_ids):
            return original_price
        
        # Check trigger conditions
        # This would need to be implemented based on specific trigger conditions
        # For now, return special price if available
        
        if self.special_prices and str(product_id) in self.special_prices:
            return Decimal(str(self.special_prices[str(product_id)]))
        
        # Apply discount rules if available
        if self.discount_rules:
            # Simple implementation - could be more complex
            discount_type = self.discount_rules.get('type', 'percentage')
            discount_value = Decimal(str(self.discount_rules.get('value', 0)))
            
            if discount_type == 'percentage':
                return original_price * (1 - discount_value / Decimal('100'))
            elif discount_type == 'fixed':
                return max(Decimal('0'), original_price - discount_value)
        
        return original_price


class PromotionalPricingUsage(FeatureAwareModel):
    """Promotional pricing usage tracking"""
    __tablename__ = 'promotional_pricing_usages'
    __feature_key__ = 'FEATURE_PROMOTIONAL_PRICING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    promotional_pricing_id = Column(Integer, ForeignKey('promotional_pricing.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Usage details
    product_id = Column(Integer, ForeignKey('products.id'))
    original_price = Column(Numeric(12, 2), nullable=False)
    promotional_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='promotional_pricing_usages')
    promotional_pricing = relationship('PromotionalPricing', back_populates='promotional_pricing_usages')
    customer = relationship('Customer', back_populates='promotional_pricing_usages')
    order = relationship('Order', back_populates='promotional_pricing_usages')
    product = relationship('Product', back_populates='promotional_pricing_usages')
    
    def __repr__(self):
        return f'<PromotionalPricingUsage {self.promotional_pricing_id}:{self.product_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'promotional_pricing_id': self.promotional_pricing_id,
            'customer_id': self.customer_id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'original_price': float(self.original_price),
            'promotional_price': float(self.promotional_price),
            'discount_amount': float(self.discount_amount),
            'quantity': self.quantity,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }