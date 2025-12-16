"""
Online Integration models for implementing online order processing, click-and-collect functionality,
home delivery management, and third-party integration framework.
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, Boolean, \
    ForeignKey, Numeric, JSON, Enum as SQLEnum, CheckConstraint, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from models import db, FeatureAwareModel


class OnlineOrderStatus(Enum):
    """Online order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class DeliveryType(Enum):
    """Delivery type enumeration"""
    HOME_DELIVERY = "home_delivery"
    CLICK_AND_COLLECT = "click_and_collect"
    CURBSIDE_PICKUP = "curbside_pickup"
    LOCKER_PICKUP = "locker_pickup"


class ThirdPartyPlatform(Enum):
    """Third-party platform enumeration"""
    NONE = "none"
    ZOMATO = "zomato"
    SWIGGY = "swiggy"
    UBER_EATS = "uber_eats"
    FOODPANDA = "foodpanda"
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    MEESHO = "meesho"
    INSTAMART = "instamart"
    BLINKIT = "blinkit"
    BIGBASKET = "bigbasket"
    GROCERY = "grocery"
    CUSTOM = "custom"


class OnlineOrder(FeatureAwareModel):
    """Online order model for managing orders from online channels"""
    __tablename__ = 'online_orders'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    platform_order_id = Column(String(100))  # Order ID from third-party platform
    platform = Column(SQLEnum(ThirdPartyPlatform), default=ThirdPartyPlatform.NONE, nullable=False)
    
    # Customer information
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100))
    customer_phone = Column(String(20), nullable=False)
    
    # Delivery information
    delivery_type = Column(SQLEnum(DeliveryType), nullable=False)
    delivery_address = Column(JSON)  # Address for home delivery
    delivery_instructions = Column(Text)
    preferred_delivery_time = Column(DateTime)
    delivery_time_slot = Column(String(50))
    
    # Store information
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    pickup_store = Column(JSON)  # Store details for click-and-collect
    
    # Order details
    order_items = Column(JSON)  # Array of ordered items
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=Decimal('0.00'))
    delivery_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    platform_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    discount_amount = Column(Numeric(15, 2), default=Decimal('0.00'))
    tip_amount = Column(Numeric(10, 2), default=Decimal('0.00'))
    total_amount = Column(Numeric(15, 2), nullable=False)
    
    # Status and tracking
    status = Column(SQLEnum(OnlineOrderStatus), default=OnlineOrderStatus.PENDING, nullable=False)
    payment_status = Column(String(20), default='pending')  # e.g., "pending", "paid", "failed"
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    
    # Processing details
    confirmed_at = Column(DateTime)
    processing_started_at = Column(DateTime)
    ready_for_pickup_at = Column(DateTime)
    out_for_delivery_at = Column(DateTime)
    delivered_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    # Delivery tracking
    tracking_number = Column(String(100))
    delivery_partner = Column(String(100))
    delivery_partner_phone = Column(String(20))
    estimated_delivery_time = Column(DateTime)
    
    # Staff assignments
    assigned_to = Column(Integer, ForeignKey('users.id'))
    delivery_assigned_to = Column(Integer, ForeignKey('users.id'))
    
    # Additional information
    notes = Column(Text)
    customer_notes = Column(Text)
    platform_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    customer = relationship("Customer", backref="online_orders")
    store = relationship("Store", backref="online_orders")
    assigned_staff = relationship("User", foreign_keys=[assigned_to])
    delivery_staff = relationship("User", foreign_keys=[delivery_assigned_to])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<OnlineOrder {self.order_number}>'
    
    def generate_order_number(self):
        """Generate a unique order number"""
        if not self.order_number:
            prefix = "ONL"
            date_str = datetime.utcnow().strftime("%Y%m%d")
            
            # Get count of online orders for today
            today_count = OnlineOrder.query.filter(
                OnlineOrder.tenant_id == self.tenant_id,
                func.date(OnlineOrder.created_at) == date.today()
            ).count()
            
            sequence = today_count + 1
            self.order_number = f"{prefix}{date_str}{sequence:04d}"
        return self.order_number
    
    @hybrid_property
    def is_ready_for_pickup(self):
        """Check if order is ready for pickup"""
        return self.status == OnlineOrderStatus.READY_FOR_PICKUP
    
    @hybrid_property
    def is_out_for_delivery(self):
        """Check if order is out for delivery"""
        return self.status == OnlineOrderStatus.OUT_FOR_DELIVERY
    
    @hybrid_property
    def is_delivered(self):
        """Check if order is delivered"""
        return self.status == OnlineOrderStatus.DELIVERED


class ClickAndCollect(FeatureAwareModel):
    """Click and collect model for managing in-store pickup orders"""
    __tablename__ = 'click_and_collect'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Order reference
    online_order_id = Column(Integer, ForeignKey('online_orders.id'), nullable=False)
    
    # Pickup details
    pickup_code = Column(String(20), unique=True, nullable=False, index=True)
    pickup_instructions = Column(Text)
    pickup_area = Column(String(100))  # e.g., "Front Desk", "Curbside Bay 1"
    
    # Time slots
    preferred_pickup_time = Column(DateTime)
    scheduled_pickup_time = Column(DateTime)
    actual_pickup_time = Column(DateTime)
    pickup_time_slot = Column(String(50))
    
    # Customer details for pickup
    pickup_customer_name = Column(String(100))
    pickup_customer_phone = Column(String(20))
    pickup_customer_email = Column(String(100))
    pickup_vehicle_details = Column(String(100))  # e.g., "White Honda City - DL-01-AB-1234"
    
    # Status
    is_ready = Column(Boolean, default=False, nullable=False)
    is_picked_up = Column(Boolean, default=False, nullable=False)
    ready_notification_sent = Column(Boolean, default=False, nullable=False)
    
    # Staff
    prepared_by = Column(Integer, ForeignKey('users.id'))
    handed_over_by = Column(Integer, ForeignKey('users.id'))
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    online_order = relationship("OnlineOrder", backref=backref("click_and_collect", uselist=False))
    preparer = relationship("User", foreign_keys=[prepared_by])
    handler = relationship("User", foreign_keys=[handed_over_by])
    
    def __repr__(self):
        return f'<ClickAndCollect {self.pickup_code}>'
    
    def generate_pickup_code(self):
        """Generate a unique pickup code"""
        if not self.pickup_code:
            # Generate a 6-character alphanumeric code
            import random
            import string
            chars = string.ascii_uppercase + string.digits
            self.pickup_code = ''.join(random.choice(chars) for _ in range(6))
        return self.pickup_code


class HomeDelivery(FeatureAwareModel):
    """Home delivery model for managing delivery orders"""
    __tablename__ = 'home_deliveries'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Order reference
    online_order_id = Column(Integer, ForeignKey('online_orders.id'), nullable=False)
    
    # Delivery address
    delivery_address = Column(JSON, nullable=False)
    delivery_latitude = Column(Numeric(10, 8))
    delivery_longitude = Column(Numeric(10, 8))
    delivery_instructions = Column(Text)
    landmark = Column(String(200))
    
    # Time details
    preferred_delivery_time = Column(DateTime)
    scheduled_delivery_time = Column(DateTime)
    actual_delivery_time = Column(DateTime)
    delivery_time_slot = Column(String(50))
    
    # Delivery partner
    delivery_partner_id = Column(Integer, ForeignKey('delivery_partners.id'))
    delivery_partner_name = Column(String(100))
    delivery_partner_phone = Column(String(20))
    delivery_partner_vehicle = Column(String(100))
    
    # Delivery tracking
    tracking_number = Column(String(100))
    tracking_url = Column(String(500))
    estimated_delivery_time = Column(DateTime)
    delivery_distance = Column(Numeric(8, 2))  # Distance in km
    delivery_duration = Column(Integer)  # Duration in minutes
    
    # Status
    is_ready_for_delivery = Column(Boolean, default=False, nullable=False)
    is_out_for_delivery = Column(Boolean, default=False, nullable=False)
    is_delivered = Column(Boolean, default=False, nullable=False)
    
    # Delivery proof
    delivery_photo_url = Column(String(500))
    delivery_signature = Column(Text)  # Base64 encoded signature
    recipient_name = Column(String(100))
    recipient_phone = Column(String(20))
    
    # Staff
    packed_by = Column(Integer, ForeignKey('users.id'))
    dispatched_by = Column(Integer, ForeignKey('users.id'))
    
    # Additional information
    notes = Column(Text)
    delivery_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    online_order = relationship("OnlineOrder", backref=backref("home_delivery", uselist=False))
    delivery_partner = relationship("DeliveryPartner", backref="deliveries")
    packer = relationship("User", foreign_keys=[packed_by])
    dispatcher = relationship("User", foreign_keys=[dispatched_by])
    
    def __repr__(self):
        return f'<HomeDelivery {self.id}>'
    
    @hybrid_property
    def is_late(self):
        """Check if delivery is late"""
        if self.scheduled_delivery_time and self.actual_delivery_time:
            return self.actual_delivery_time > self.scheduled_delivery_time
        return False


class DeliveryPartner(FeatureAwareModel):
    """Delivery partner model for managing third-party delivery services"""
    __tablename__ = 'delivery_partners'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Partner details
    partner_name = Column(String(100), nullable=False)
    partner_code = Column(String(50), unique=True, nullable=False, index=True)
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Service details
    service_areas = Column(JSON)  # Array of service areas/pincodes
    delivery_radius = Column(Numeric(8, 2))  # Service radius in km
    average_delivery_time = Column(Integer)  # Average delivery time in minutes
    
    # Pricing
    base_delivery_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    fee_per_km = Column(Numeric(8, 2), default=Decimal('0.00'))
    fee_per_minute = Column(Numeric(8, 2), default=Decimal('0.00'))
    minimum_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Integration
    api_endpoint = Column(String(500))
    api_key = Column(String(200))
    webhook_url = Column(String(500))
    integration_type = Column(String(50))  # e.g., "api", "manual", "third_party"
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<DeliveryPartner {self.partner_name}>'


class ThirdPartyIntegration(FeatureAwareModel):
    """Third-party integration model for managing external platform integrations"""
    __tablename__ = 'third_party_integrations'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Integration details
    platform = Column(SQLEnum(ThirdPartyPlatform), nullable=False)
    integration_name = Column(String(100), nullable=False)
    integration_code = Column(String(50), unique=True, nullable=False, index=True)
    
    # Configuration
    api_endpoint = Column(String(500))
    api_key = Column(String(200))
    api_secret = Column(String(200))
    webhook_url = Column(String(500))
    webhook_secret = Column(String(200))
    
    # Store mapping
    store_mapping = Column(JSON)  # Mapping of platform stores to local stores
    category_mapping = Column(JSON)  # Mapping of platform categories to local categories
    product_mapping = Column(JSON)  # Mapping of platform products to local products
    
    # Sync settings
    auto_sync_orders = Column(Boolean, default=True, nullable=False)
    auto_sync_menu = Column(Boolean, default=True, nullable=False)
    auto_update_inventory = Column(Boolean, default=True, nullable=False)
    sync_frequency = Column(Integer, default=5)  # Sync frequency in minutes
    
    # Business rules
    auto_accept_orders = Column(Boolean, default=False, nullable=False)
    auto_cancel_time = Column(Integer)  # Auto cancel time in minutes
    preparation_time_buffer = Column(Integer, default=15)  # Buffer time in minutes
    
    # Commission and fees
    commission_rate = Column(Numeric(5, 2))  # Platform commission percentage
    fixed_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    payment_gateway_fee = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime)
    last_error = Column(Text)
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<ThirdPartyIntegration {self.platform.value}>'


class OnlineOrderHistory(FeatureAwareModel):
    """Online order history model for tracking order status changes"""
    __tablename__ = 'online_order_history'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Order reference
    online_order_id = Column(Integer, ForeignKey('online_orders.id'), nullable=False)
    
    # Status change
    previous_status = Column(SQLEnum(OnlineOrderStatus))
    new_status = Column(SQLEnum(OnlineOrderStatus), nullable=False)
    
    # Change details
    changed_by = Column(Integer, ForeignKey('users.id'))
    change_reason = Column(String(200))
    change_notes = Column(Text)
    
    # System information
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    online_order = relationship("OnlineOrder", backref="status_history")
    user = relationship("User", foreign_keys=[changed_by])
    
    def __repr__(self):
        return f'<OnlineOrderHistory {self.online_order_id} {self.new_status.value}>'


class OnlineOrderReview(FeatureAwareModel):
    """Online order review model for customer feedback"""
    __tablename__ = 'online_order_reviews'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Order reference
    online_order_id = Column(Integer, ForeignKey('online_orders.id'), nullable=False)
    
    # Review details
    rating = Column(Integer, nullable=False)  # 1-5 rating
    review_title = Column(String(200))
    review_text = Column(Text)
    
    # Aspect ratings
    food_quality_rating = Column(Integer)  # 1-5 rating
    delivery_time_rating = Column(Integer)  # 1-5 rating
    packaging_rating = Column(Integer)  # 1-5 rating
    customer_service_rating = Column(Integer)  # 1-5 rating
    
    # Review status
    is_approved = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    staff_response = Column(Text)
    
    # Additional information
    review_source = Column(String(50))  # e.g., "app", "website", "platform"
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    online_order = relationship("OnlineOrder", backref="reviews")
    
    def __repr__(self):
        return f'<OnlineOrderReview {self.online_order_id}>'


class OnlineOrderAnalytics(FeatureAwareModel):
    """Online order analytics model for tracking performance metrics"""
    __tablename__ = 'online_order_analytics'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Analytics period
    date = Column(Date, nullable=False, index=True)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    
    # Order metrics
    total_orders = Column(Integer, default=0)
    pending_orders = Column(Integer, default=0)
    confirmed_orders = Column(Integer, default=0)
    delivered_orders = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
    
    # Platform breakdown
    platform_breakdown = Column(JSON)  # Orders by platform
    
    # Delivery type breakdown
    delivery_type_breakdown = Column(JSON)  # Orders by delivery type
    
    # Financial metrics
    total_revenue = Column(Numeric(15, 2), default=Decimal('0.00'))
    average_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    delivery_fee_revenue = Column(Numeric(15, 2), default=Decimal('0.00'))
    platform_fee_total = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Time metrics
    average_preparation_time = Column(Integer)  # Minutes
    average_delivery_time = Column(Integer)  # Minutes
    average_fulfillment_time = Column(Integer)  # Minutes
    
    # Customer metrics
    unique_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    customer_satisfaction_score = Column(Numeric(3, 2))  # 1-5 scale
    
    # Additional data
    metadata = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<OnlineOrderAnalytics {self.date}>'