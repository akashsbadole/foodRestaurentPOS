"""
Multi-Store & Franchise models for implementing multi-store inventory management,
creating store transfers and consolidated reporting, adding franchise management
and royalty tracking.
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


class StoreType(Enum):
    """Store type enumeration"""
    CORPORATE = "corporate"
    FRANCHISE = "franchise"
    PARTNER = "partner"
    POPUP = "popup"
    KIOSK = "kiosk"


class TransferStatus(Enum):
    """Transfer status enumeration"""
    REQUESTED = "requested"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FranchiseStatus(Enum):
    """Franchise status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class Store(FeatureAwareModel):
    """Store model for multi-store management"""
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Store details
    store_code = Column(String(20), unique=True, nullable=False, index=True)
    store_name = Column(String(100), nullable=False)
    store_type = Column(SQLEnum(StoreType), nullable=False)
    
    # Contact information
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    
    # Location
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(10, 8))
    timezone = Column(String(50))
    
    # Store management
    manager_id = Column(Integer, ForeignKey('users.id'))
    assistant_managers = Column(JSON)  # Array of user IDs
    store_hours = Column(JSON)  # Operating hours by day
    holidays = Column(JSON)  # Store-specific holidays
    
    # Capabilities
    features = Column(JSON)  # Store-specific features enabled
    departments = Column(JSON)  # Departments available at this store
    payment_methods = Column(JSON)  # Payment methods accepted
    
    # Inventory settings
    inventory_tracking = Column(Boolean, default=True)
    auto_reorder = Column(Boolean, default=False)
    reorder_point_days = Column(Integer, default=7)
    
    # Franchise details (if applicable)
    franchise_id = Column(String(50))  # Franchise identifier
    franchise_agreement_date = Column(Date)
    franchise_expiry_date = Column(Date)
    royalty_rate = Column(Numeric(5, 2))  # Percentage
    minimum_monthly_fee = Column(Numeric(10, 2))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_headquarters = Column(Boolean, default=False, nullable=False)
    opening_date = Column(Date)
    closing_date = Column(Date)
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    manager = relationship("User", foreign_keys=[manager_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    inventory_transfers_from = relationship("InventoryTransfer", foreign_keys="from_store_id")
    inventory_transfers_to = relationship("InventoryTransfer", foreign_keys="to_store_id")
    
    def __repr__(self):
        return f'<Store {self.store_name}>'


class InventoryTransfer(FeatureAwareModel):
    """Inventory transfer model for inter-store stock movement"""
    __tablename__ = 'inventory_transfers'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Transfer details
    transfer_number = Column(String(50), unique=True, nullable=False, index=True)
    from_store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    to_store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    
    # Transfer information
    transfer_date = Column(Date, nullable=False)
    requested_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    approved_by = Column(Integer, ForeignKey('users.id'))
    shipped_by = Column(Integer, ForeignKey('users.id'))
    received_by = Column(Integer, ForeignKey('users.id'))
    
    # Status and tracking
    status = Column(SQLEnum(TransferStatus), default=TransferStatus.REQUESTED, nullable=False)
    tracking_number = Column(String(100))
    shipping_carrier = Column(String(100))
    estimated_arrival = Column(Date)
    actual_arrival = Column(Date)
    
    # Transfer items
    transfer_items = Column(JSON)  # Array of transferred items
    total_items = Column(Integer, default=0)
    total_value = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Additional information
    transfer_reason = Column(String(200))
    priority = Column(String(20))  # e.g., "urgent", "normal", "low"
    notes = Column(Text)
    
    # Financial
    shipping_cost = Column(Numeric(10, 2), default=Decimal('0.00'))
    insurance_cost = Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_store = relationship("Store", foreign_keys=[from_store_id])
    to_store = relationship("Store", foreign_keys=[to_store_id])
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    shipper = relationship("User", foreign_keys=[shipped_by])
    receiver = relationship("User", foreign_keys=[received_by])
    
    def __repr__(self):
        return f'<InventoryTransfer {self.transfer_number}>'
    
    def generate_transfer_number(self):
        """Generate a unique transfer number"""
        if not self.transfer_number:
            prefix = "TRF"
            date_str = self.transfer_date.strftime("%Y%m%d") if self.transfer_date else date.today().strftime("%Y%m%d")
            
            # Get count of transfers for today
            today_count = InventoryTransfer.query.filter(
                InventoryTransfer.tenant_id == self.tenant_id,
                InventoryTransfer.transfer_date == date.today()
            ).count()
            
            sequence = today_count + 1
            self.transfer_number = f"{prefix}{date_str}{sequence:04d}"
        return self.transfer_number


class ConsolidatedReport(FeatureAwareModel):
    """Consolidated report model for multi-store reporting"""
    __tablename__ = 'consolidated_reports'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Report details
    report_name = Column(String(100), nullable=False)
    report_type = Column(String(50), nullable=False)  # e.g., "sales", "inventory", "financial"
    report_period = Column(String(20))  # e.g., "daily", "weekly", "monthly"
    
    # Time period
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    
    # Store selection
    store_ids = Column(JSON)  # Array of store IDs included in report
    include_headquarters = Column(Boolean, default=True)
    include_inactive_stores = Column(Boolean, default=False)
    
    # Report data
    report_data = Column(JSON)  # Consolidated data
    summary_data = Column(JSON)  # Summary statistics
    insights = Column(JSON)  # AI-generated insights
    
    # Generation details
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey('users.id'))
    generation_time = Column(Integer)  # Generation time in seconds
    
    # File information
    file_path = Column(String(500))
    file_format = Column(String(20))  # e.g., "pdf", "excel", "csv"
    file_size = Column(Integer)  # File size in bytes
    
    # Distribution
    email_recipients = Column(JSON)  # Who receives this report
    auto_distribute = Column(Boolean, default=False)
    last_distributed_at = Column(DateTime)
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generator = relationship("User", foreign_keys=[generated_by])
    
    def __repr__(self):
        return f'<ConsolidatedReport {self.report_name}>'


class FranchiseAgreement(FeatureAwareModel):
    """Franchise agreement model"""
    __tablename__ = 'franchise_agreements'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Agreement details
    franchise_id = Column(String(50), unique=True, nullable=False, index=True)
    franchise_name = Column(String(100), nullable=False)
    legal_entity_name = Column(String(200))
    
    # Agreement period
    agreement_date = Column(Date, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    initial_term_years = Column(Integer, nullable=False)
    
    # Financial terms
    royalty_rate = Column(Numeric(5, 2), nullable=False)  # Percentage
    royalty_type = Column(String(50))  # e.g., "revenue", "profit", "fixed"
    minimum_monthly_royalty = Column(Numeric(10, 2), default=Decimal('0.00'))
    franchise_fee = Column(Numeric(10, 2))  # One-time fee
    marketing_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    training_fee = Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Territory and exclusivity
    territory_description = Column(Text)
    exclusive_territory = Column(Boolean, default=True)
    protected_radius = Column(Numeric(10, 2))  # Miles
    protected_zip_codes = Column(JSON)  # Array of zip codes
    
    # Requirements and obligations
    minimum_investment = Column(Numeric(15, 2))
    experience_requirements = Column(JSON)
    training_requirements = Column(JSON)
    operational_standards = Column(JSON)
    reporting_requirements = Column(JSON)
    
    # Brand and marketing
    brand_guidelines = Column(JSON)
    marketing_materials_provided = Column(Boolean, default=False)
    local_marketing_allowed = Column(Boolean, default=False)
    
    # Status
    status = Column(SQLEnum(FranchiseStatus), default=FranchiseStatus.PENDING, nullable=False)
    termination_date = Column(Date)
    termination_reason = Column(String(200))
    
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
        return f'<FranchiseAgreement {self.franchise_name}>'


class RoyaltyPayment(FeatureAwareModel):
    """Royalty payment model for franchise management"""
    __tablename__ = 'royalty_payments'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Payment details
    franchise_id = Column(String(50), nullable=False, index=True)
    payment_period = Column(String(20))  # e.g., "monthly", "quarterly"
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    
    # Financial details
    gross_revenue = Column(Numeric(15, 2), nullable=False)
    deductible_expenses = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_revenue = Column(Numeric(15, 2), nullable=False)
    royalty_rate = Column(Numeric(5, 2), nullable=False)
    royalty_amount = Column(Numeric(15, 2), nullable=False)
    
    # Payment information
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50))  # e.g., "check", "wire", "ACH"
    reference_number = Column(String(100))
    
    # Status
    status = Column(String(20))  # e.g., "pending", "paid", "overdue", "disputed"
    due_date = Column(Date)
    paid_date = Column(Date)
    
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
        return f'<RoyaltyPayment {self.franchise_id} {self.period_start}>'


class StorePerformance(FeatureAwareModel):
    """Store performance model for comparing store metrics"""
    __tablename__ = 'store_performance'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Performance period
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    
    # Sales metrics
    total_sales = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_orders = Column(Integer, default=0)
    average_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    items_per_order = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Customer metrics
    unique_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    
    # Product metrics
    unique_products_sold = Column(Integer, default=0)
    top_product_id = Column(Integer, ForeignKey('products.id'))
    top_category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Staff metrics
    staff_count = Column(Integer, default=0)
    staff_hours_worked = Column(Numeric(8, 2), default=Decimal('0.00'))
    sales_per_staff_hour = Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Financial metrics
    gross_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Inventory metrics
    inventory_turnover = Column(Numeric(5, 2), default=Decimal('0.00'))
    stockout_count = Column(Integer, default=0)
    waste_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Additional data
    metadata = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store", backref="performance_records")
    top_product = relationship("Product", foreign_keys=[top_product_id])
    top_category = relationship("Category", foreign_keys=[top_category_id])
    
    def __repr__(self):
        return f'<StorePerformance {self.store_id} {self.date}>'


class StoreInventory(FeatureAwareModel):
    """Store inventory model for tracking inventory by store"""
    __tablename__ = 'store_inventory'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Inventory details
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    variant_id = Column(Integer, ForeignKey('product_variants.id'))
    
    # Quantity and values
    quantity_on_hand = Column(Integer, default=0)
    quantity_reserved = Column(Integer, default=0)
    quantity_available = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    reorder_quantity = Column(Integer, default=0)
    
    # Financial values
    unit_cost = Column(Numeric(10, 2), default=Decimal('0.00'))
    total_cost = Column(Numeric(15, 2), default=Decimal('0.00'))
    unit_price = Column(Numeric(10, 2), default=Decimal('0.00'))
    total_value = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Location
    aisle = Column(String(20))
    shelf = Column(String(20))
    bin_location = Column(String(20))
    
    # Tracking
    last_counted = Column(DateTime)
    last_received = Column(DateTime)
    last_sold = Column(DateTime)
    
    # Additional data
    metadata = Column(JSON)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store", backref="inventory")
    product = relationship("Product", backref="store_inventory")
    variant = relationship("ProductVariant", backref="store_inventory")
    
    def __repr__(self):
        return f'<StoreInventory {self.store_id} {self.product_id}>'
    
    @hybrid_property
    def is_below_reorder_point(self):
        """Check if inventory is below reorder point"""
        return self.quantity_available <= self.reorder_point


class StoreUser(FeatureAwareModel):
    """Store user model for managing user access across stores"""
    __tablename__ = 'store_users'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Assignment details
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Role and permissions
    role = Column(String(50))  # e.g., "manager", "assistant", "cashier"
    permissions = Column(JSON)  # Array of permissions
    
    # Assignment details
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey('users.id'))
    terminated_at = Column(DateTime)
    termination_reason = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Additional information
    notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    store = relationship("Store", backref="store_users")
    user = relationship("User", backref="store_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f'<StoreUser {self.store_id} {self.user_id}>'