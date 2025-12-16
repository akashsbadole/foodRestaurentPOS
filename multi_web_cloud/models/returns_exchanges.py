"""
Returns & Exchanges models for handling comprehensive return management,
exchange processing with variant matching, refund processing and store credit,
and return approval workflows.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, \
    ForeignKey, Numeric, JSON, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from models import db, FeatureAwareModel


class ReturnStatus(Enum):
    """Return status enumeration"""
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReturnReason(Enum):
    """Return reason enumeration"""
    DAMAGED = "damaged"
    DEFECTIVE = "defective"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    SIZE_ISSUE = "size_issue"
    COLOR_ISSUE = "color_issue"
    CHANGE_OF_MIND = "change_of_mind"
    DUPLICATE_PURCHASE = "duplicate_purchase"
    GIFT_PURCHASE = "gift_purchase"
    OTHER = "other"


class RefundMethod(Enum):
    """Refund method enumeration"""
    ORIGINAL_PAYMENT = "original_payment"
    STORE_CREDIT = "store_credit"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    GIFT_CARD = "gift_card"
    EXCHANGE = "exchange"


class ExchangeStatus(Enum):
    """Exchange status enumeration"""
    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReturnRequest(FeatureAwareModel):
    """Return request model for managing customer returns"""
    __tablename__ = 'return_requests'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Return details
    return_number = Column(String(50), unique=True, nullable=False, index=True)
    original_order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    return_date = Column(Date, nullable=False, default=date.today)
    
    # Return status and reason
    status = Column(SQLEnum(ReturnStatus), default=ReturnStatus.REQUESTED, nullable=False)
    return_reason = Column(SQLEnum(ReturnReason), nullable=False)
    return_reason_details = Column(Text)
    
    # Customer information
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100))
    customer_phone = Column(String(20))
    
    # Return processing
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    received_by = Column(Integer, ForeignKey('users.id'))
    received_at = Column(DateTime)
    processed_by = Column(Integer, ForeignKey('users.id'))
    processed_at = Column(DateTime)
    
    # Financial details
    total_refund_amount = Column(Numeric(10, 2), default=Decimal('0.00'))
    refund_method = Column(SQLEnum(RefundMethod))
    refund_processed_at = Column(DateTime)
    refund_transaction_id = Column(String(100))
    
    # Store credit details
    store_credit_issued = Column(Numeric(10, 2), default=Decimal('0.00'))
    store_credit_expiry = Column(Date)
    store_credit_reference = Column(String(100))
    
    # Additional information
    notes = Column(Text)
    internal_notes = Column(Text)
    customer_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    original_order = relationship("Order", backref="return_requests")
    customer = relationship("Customer", backref="return_requests")
    approver = relationship("User", foreign_keys=[approved_by])
    receiver = relationship("User", foreign_keys=[received_by])
    processor = relationship("User", foreign_keys=[processed_by])
    return_items = relationship("ReturnItem", backref="return_request", cascade="all, delete-orphan")
    exchange_requests = relationship("ExchangeRequest", backref="return_request")
    
    def __repr__(self):
        return f'<ReturnRequest {self.return_number}>'
    
    def generate_return_number(self):
        """Generate a unique return number"""
        if not self.return_number:
            prefix = "RTN"
            date_str = self.return_date.strftime("%Y%m%d") if self.return_date else date.today().strftime("%Y%m%d")
            
            # Get count of returns for today
            today_count = ReturnRequest.query.filter(
                ReturnRequest.tenant_id == self.tenant_id,
                ReturnRequest.return_date == date.today()
            ).count()
            
            sequence = today_count + 1
            self.return_number = f"{prefix}{date_str}{sequence:04d}"
        return self.return_number
    
    @hybrid_property
    def is_approved(self):
        """Check if return is approved"""
        return self.status in [ReturnStatus.APPROVED, ReturnStatus.RECEIVED, ReturnStatus.PROCESSING, ReturnStatus.COMPLETED]
    
    @hybrid_property
    def is_completed(self):
        """Check if return is completed"""
        return self.status == ReturnStatus.COMPLETED
    
    @hybrid_property
    def days_since_return(self):
        """Calculate days since return date"""
        if self.return_date:
            return (date.today() - self.return_date).days
        return 0
    
    def calculate_total_return_value(self):
        """Calculate total value of returned items"""
        return sum(item.total_value for item in self.return_items)
    
    def calculate_total_refundable_amount(self):
        """Calculate total refundable amount after deductions"""
        total_value = self.calculate_total_return_value()
        total_deductions = sum(item.deduction_amount for item in self.return_items)
        return total_value - total_deductions


class ReturnItem(FeatureAwareModel):
    """Individual return item model"""
    __tablename__ = 'return_items'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    return_request_id = Column(Integer, ForeignKey('return_requests.id'), nullable=False)
    
    # Product details
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100))
    variant_id = Column(Integer, ForeignKey('product_variants.id'))
    variant_name = Column(String(100))
    variant_attributes = Column(JSON)
    
    # Original order details
    original_order_item_id = Column(Integer, ForeignKey('order_items.id'))
    original_quantity = Column(Integer, nullable=False)
    original_unit_price = Column(Numeric(10, 2), nullable=False)
    original_total_price = Column(Numeric(10, 2), nullable=False)
    
    # Return details
    return_quantity = Column(Integer, nullable=False)
    return_reason = Column(SQLEnum(ReturnReason))
    return_condition = Column(String(100))  # e.g., "new", "used", "damaged", "defective"
    condition_details = Column(Text)
    
    # Financial calculations
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_value = Column(Numeric(10, 2), nullable=False)
    deduction_amount = Column(Numeric(10, 2), default=Decimal('0.00'))
    deduction_reason = Column(String(200))
    refundable_amount = Column(Numeric(10, 2), nullable=False)
    
    # Restocking
    restock_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    restock_fee_reason = Column(String(200))
    should_restock = Column(Boolean, default=True)
    restocked_quantity = Column(Integer, default=0)
    restocked_at = Column(DateTime)
    restocked_by = Column(Integer, ForeignKey('users.id'))
    
    # Additional information
    item_notes = Column(Text)
    customer_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = relationship("Product", backref="return_items")
    variant = relationship("ProductVariant", backref="return_items")
    original_order_item = relationship("OrderItem", backref="return_items")
    restocker = relationship("User", foreign_keys=[restocked_by])
    
    def __repr__(self):
        return f'<ReturnItem {self.product_name} x {self.return_quantity}>'
    
    def calculate_refundable_amount(self):
        """Calculate refundable amount after deductions"""
        return self.total_value - self.deduction_amount - self.restock_fee
    
    def calculate_total_deductions(self):
        """Calculate total deductions"""
        return self.deduction_amount + self.restock_fee


class ExchangeRequest(FeatureAwareModel):
    """Exchange request model for handling product exchanges"""
    __tablename__ = 'exchange_requests'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    return_request_id = Column(Integer, ForeignKey('return_requests.id'))
    
    # Exchange details
    exchange_number = Column(String(50), unique=True, nullable=False, index=True)
    original_order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    exchange_date = Column(Date, nullable=False, default=date.today)
    
    # Exchange status
    status = Column(SQLEnum(ExchangeStatus), default=ExchangeStatus.REQUESTED, nullable=False)
    exchange_reason = Column(SQLEnum(ReturnReason), nullable=False)
    exchange_reason_details = Column(Text)
    
    # Exchange processing
    approved_by = Column(Integer, ForeignKey('users.id'))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)
    processed_by = Column(Integer, ForeignKey('users.id'))
    processed_at = Column(DateTime)
    shipped_by = Column(Integer, ForeignKey('users.id'))
    shipped_at = Column(DateTime)
    tracking_number = Column(String(100))
    shipping_carrier = Column(String(100))
    
    # Financial details
    price_difference = Column(Numeric(10, 2), default=Decimal('0.00'))  # Positive = customer pays, Negative = store pays
    additional_payment_required = Column(Numeric(10, 2), default=Decimal('0.00'))
    refund_amount = Column(Numeric(10, 2), default=Decimal('0.00'))
    payment_processed_at = Column(DateTime)
    refund_processed_at = Column(DateTime)
    
    # Additional information
    notes = Column(Text)
    internal_notes = Column(Text)
    customer_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    original_order = relationship("Order", backref="exchange_requests")
    customer = relationship("Customer", backref="exchange_requests")
    approver = relationship("User", foreign_keys=[approved_by])
    processor = relationship("User", foreign_keys=[processed_by])
    shipper = relationship("User", foreign_keys=[shipped_by])
    exchange_items = relationship("ExchangeItem", backref="exchange_request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ExchangeRequest {self.exchange_number}>'
    
    def generate_exchange_number(self):
        """Generate a unique exchange number"""
        if not self.exchange_number:
            prefix = "EXC"
            date_str = self.exchange_date.strftime("%Y%m%d") if self.exchange_date else date.today().strftime("%Y%m%d")
            
            # Get count of exchanges for today
            today_count = ExchangeRequest.query.filter(
                ExchangeRequest.tenant_id == self.tenant_id,
                ExchangeRequest.exchange_date == date.today()
            ).count()
            
            sequence = today_count + 1
            self.exchange_number = f"{prefix}{date_str}{sequence:04d}"
        return self.exchange_number
    
    @hybrid_property
    def is_approved(self):
        """Check if exchange is approved"""
        return self.status in [ExchangeStatus.APPROVED, ExchangeStatus.PROCESSING, ExchangeStatus.SHIPPED, ExchangeStatus.COMPLETED]
    
    @hybrid_property
    def is_completed(self):
        """Check if exchange is completed"""
        return self.status == ExchangeStatus.COMPLETED
    
    def calculate_price_difference(self):
        """Calculate price difference between original and exchange items"""
        original_total = sum(item.original_total_price for item in self.exchange_items)
        exchange_total = sum(item.exchange_total_price for item in self.exchange_items)
        return exchange_total - original_total


class ExchangeItem(FeatureAwareModel):
    """Individual exchange item model"""
    __tablename__ = 'exchange_items'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    exchange_request_id = Column(Integer, ForeignKey('exchange_requests.id'), nullable=False)
    
    # Original item details (what customer is returning)
    original_product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    original_product_name = Column(String(200), nullable=False)
    original_product_sku = Column(String(100))
    original_variant_id = Column(Integer, ForeignKey('product_variants.id'))
    original_variant_name = Column(String(100))
    original_variant_attributes = Column(JSON)
    original_quantity = Column(Integer, nullable=False)
    original_unit_price = Column(Numeric(10, 2), nullable=False)
    original_total_price = Column(Numeric(10, 2), nullable=False)
    
    # Exchange item details (what customer wants instead)
    exchange_product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    exchange_product_name = Column(String(200), nullable=False)
    exchange_product_sku = Column(String(100))
    exchange_variant_id = Column(Integer, ForeignKey('product_variants.id'))
    exchange_variant_name = Column(String(100))
    exchange_variant_attributes = Column(JSON)
    exchange_quantity = Column(Integer, nullable=False)
    exchange_unit_price = Column(Numeric(10, 2), nullable=False)
    exchange_total_price = Column(Numeric(10, 2), nullable=False)
    
    # Inventory and availability
    original_available = Column(Boolean, default=True)  # Was original item available for exchange
    exchange_available = Column(Boolean, default=True)  # Is exchange item available
    exchange_stock_quantity = Column(Integer, default=0)  # Current stock of exchange item
    exchange_reserved_quantity = Column(Integer, default=0)  # Reserved quantity for this exchange
    
    # Additional information
    exchange_reason = Column(String(200))
    item_notes = Column(Text)
    customer_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    original_product = relationship("Product", foreign_keys=[original_product_id])
    original_variant = relationship("ProductVariant", foreign_keys=[original_variant_id])
    exchange_product = relationship("Product", foreign_keys=[exchange_product_id])
    exchange_variant = relationship("ProductVariant", foreign_keys=[exchange_variant_id])
    
    def __repr__(self):
        return f'<ExchangeItem {self.original_product_name} -> {self.exchange_product_name}>'
    
    def calculate_price_difference(self):
        """Calculate price difference for this item"""
        return self.exchange_total_price - self.original_total_price
    
    def is_variant_exchange(self):
        """Check if this is a variant exchange (same product, different variant)"""
        return self.original_product_id == self.exchange_product_id and self.original_variant_id != self.exchange_variant_id
    
    def is_product_exchange(self):
        """Check if this is a product exchange (different product)"""
        return self.original_product_id != self.exchange_product_id


class ReturnPolicy(FeatureAwareModel):
    """Return policy model for defining return rules"""
    __tablename__ = 'return_policies'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Policy details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    policy_type = Column(String(50), nullable=False)  # e.g., "standard", "extended", "final_sale"
    
    # Time limits
    return_period_days = Column(Integer, default=30)  # Days from purchase for returns
    exchange_period_days = Column(Integer, default=30)  # Days from purchase for exchanges
    
    # Conditions
    require_original_receipt = Column(Boolean, default=True)
    require_original_packaging = Column(Boolean, default=False)
    require_unused_condition = Column(Boolean, default=False)
    require_tags_attached = Column(Boolean, default=False)
    
    # Restocking fees
    restocking_fee_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))  # Percentage of item price
    restocking_fee_fixed = Column(Numeric(10, 2), default=Decimal('0.00'))  # Fixed fee amount
    max_restocking_fee = Column(Numeric(10, 2))  # Maximum restocking fee
    
    # Refund methods
    allowed_refund_methods = Column(JSON)  # Array of allowed refund methods
    default_refund_method = Column(SQLEnum(RefundMethod))
    store_credit_expiry_days = Column(Integer)  # Days until store credit expires
    
    # Product and category restrictions
    applies_to_all_products = Column(Boolean, default=True)
    product_ids = Column(JSON)  # Specific products this policy applies to
    category_ids = Column(JSON)  # Specific categories this policy applies to
    excluded_product_ids = Column(JSON)  # Products excluded from this policy
    excluded_category_ids = Column(JSON)  # Categories excluded from this policy
    
    # Special conditions
    holiday_return_extension = Column(Integer, default=0)  # Extra days during holiday season
    defective_item_policy = Column(String(100))  # Policy for defective items
    damaged_item_policy = Column(String(100))  # Policy for damaged items
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<ReturnPolicy {self.name}>'
    
    def is_applicable_to_product(self, product_id, category_ids=None):
        """Check if policy applies to a specific product"""
        if self.applies_to_all_products:
            # Check if product is excluded
            if self.excluded_product_ids and product_id in self.excluded_product_ids:
                return False
            if category_ids and self.excluded_category_ids:
                if any(cat_id in self.excluded_category_ids for cat_id in category_ids):
                    return False
            return True
        else:
            # Check if product is included
            if self.product_ids and product_id in self.product_ids:
                return True
            if category_ids and self.category_ids:
                if any(cat_id in self.category_ids for cat_id in category_ids):
                    return True
            return False
    
    def calculate_restocking_fee(self, item_price):
        """Calculate restocking fee for an item"""
        percentage_fee = item_price * (self.restocking_fee_percentage / Decimal('100'))
        total_fee = percentage_fee + self.restocking_fee_fixed
        
        if self.max_restocking_fee and total_fee > self.max_restocking_fee:
            total_fee = self.max_restocking_fee
        
        return total_fee
    
    def get_extended_return_period(self, purchase_date):
        """Get return period with holiday extensions"""
        base_period = self.return_period_days
        if self.holiday_return_extension > 0:
            # Check if purchase was during holiday season (simplified)
            # In a real implementation, this would check specific holiday dates
            pass
        return base_period


class ReturnWorkflow(FeatureAwareModel):
    """Return workflow model for defining approval processes"""
    __tablename__ = 'return_workflows'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Workflow details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    workflow_type = Column(String(50), nullable=False)  # e.g., "standard", "high_value", "defective"
    
    # Triggers
    trigger_conditions = Column(JSON)  # Conditions that trigger this workflow
    minimum_amount = Column(Numeric(10, 2))  # Minimum return amount to trigger
    maximum_amount = Column(Numeric(10, 2))  # Maximum return amount to trigger
    required_reasons = Column(JSON)  # Reasons that trigger this workflow
    required_products = Column(JSON)  # Products that trigger this workflow
    required_categories = Column(JSON)  # Categories that trigger this workflow
    
    # Approval steps
    approval_steps = Column(JSON)  # Array of approval steps with roles and conditions
    auto_approve_conditions = Column(JSON)  # Conditions for automatic approval
    auto_reject_conditions = Column(JSON)  # Conditions for automatic rejection
    
    # Notifications
    notification_settings = Column(JSON)  # Who to notify at each step
    customer_notifications = Column(JSON)  # Customer notification settings
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<ReturnWorkflow {self.name}>'
    
    def is_triggered(self, return_request):
        """Check if this workflow is triggered by a return request"""
        # Check amount conditions
        if self.minimum_amount and return_request.calculate_total_return_value() < self.minimum_amount:
            return False
        if self.maximum_amount and return_request.calculate_total_return_value() > self.maximum_amount:
            return False
        
        # Check reason conditions
        if self.required_reasons and return_request.return_reason not in self.required_reasons:
            return False
        
        # Check product conditions
        if self.required_products:
            return_product_ids = [item.product_id for item in return_request.return_items]
            if not any(pid in self.required_products for pid in return_product_ids):
                return False
        
        # Check category conditions
        if self.required_categories:
            # This would need to be implemented based on product-category relationships
            pass
        
        return True


class ReturnAuditLog(FeatureAwareModel):
    """Audit log for return and exchange operations"""
    __tablename__ = 'return_audit_logs'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Reference details
    return_request_id = Column(Integer, ForeignKey('return_requests.id'))
    exchange_request_id = Column(Integer, ForeignKey('exchange_requests.id'))
    
    # Action details
    action = Column(String(50), nullable=False)  # e.g., "created", "approved", "rejected", "processed"
    action_details = Column(JSON)  # Additional details about the action
    
    # User details
    user_id = Column(Integer, ForeignKey('users.id'))
    user_name = Column(String(100))
    user_role = Column(String(50))
    
    # System details
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    return_request = relationship("ReturnRequest", backref="audit_logs")
    exchange_request = relationship("ExchangeRequest", backref="audit_logs")
    user = relationship("User", backref="return_audit_logs")
    
    def __repr__(self):
        return f'<ReturnAuditLog {self.action} on {self.created_at}>'