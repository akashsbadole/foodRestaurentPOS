
"""
Hypermarket & Departmental Store models with multi-category management
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal

from models.feature_aware_model import FeatureAwareModel
from models import db


class Department(FeatureAwareModel):
    """Department model for hypermarket and departmental stores"""
    
    __tablename__ = 'departments'
    
    # Basic department information
    department_code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Hierarchy information
    parent_department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    level = Column(Integer, default=1)  # 1 for main departments, 2 for sub-departments
    sort_order = Column(Integer, default=0)
    
    # Location information
    floor_number = Column(Integer)
    section = Column(String(50))
    aisle_range = Column(String(50))  # e.g., "A1-A10"
    
    # Management information
    manager_name = Column(String(100))
    manager_contact = Column(String(50))
    assistant_manager = Column(String(100))
    
    # Operating information
    opening_time = Column(String(10))  # HH:MM format
    closing_time = Column(String(10))  # HH:MM format
    operating_days = Column(JSON)  # List of operating days
    
    # Target and performance
    monthly_sales_target = Column(Numeric(12, 2))
    monthly_footfall_target = Column(Integer)
    average_transaction_value_target = Column(Numeric(10, 2))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_seasonal = Column(Boolean, default=False)
    season_start_date = Column(Date)
    season_end_date = Column(Date)
    
    # Relationships
    parent_department = relationship('Department', remote_side=[id], backref='sub_departments')
    products = relationship('HypermarketProduct', back_populates='department')
    sales_records = relationship('DepartmentSales', back_populates='department')
    promotions = relationship('DepartmentPromotion', back_populates='department')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('monthly_sales_target'):
            result['monthly_sales_target'] = float(result['monthly_sales_target'])
        if result.get('average_transaction_value_target'):
            result['average_transaction_value_target'] = float(result['average_transaction_value_target'])
        return result


class HypermarketProduct(FeatureAwareModel):
    """Hypermarket product model with multi-category support"""
    
    __tablename__ = 'hypermarket_products'
    
    # Basic product information
    product_id = Column(String(50), nullable=False, unique=True, index=True)
    sku_base = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Department and category information
    primary_department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    secondary_departments = Column(JSON)  # List of secondary department IDs
    
    # Multi-category support
    categories = Column(JSON)  # List of categories this product belongs to
    tags = Column(JSON)  # Product tags for search and filtering
    
    # Pricing information
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    wholesale_price = Column(Numeric(10, 2))
    
    # Bulk and promotional pricing
    bulk_pricing_tiers = Column(JSON)  # Quantity-based pricing tiers
    promotional_price = Column(Numeric(10, 2))
    promotional_start_date = Column(Date)
    promotional_end_date = Column(Date)
    
    # Inventory information
    current_stock = Column(Integer, default=0)
    minimum_stock_level = Column(Integer, default=5)
    maximum_stock_level = Column(Integer, default=1000)
    reorder_point = Column(Integer, default=10)
    
    # Physical attributes
    weight = Column(Float)  # in kg
    dimensions = Column(JSON)  # Length, Width, Height in cm
    volume = Column(Float)  # in cubic cm
    
    # Packaging information
    package_type = Column(String(50))  # Box, Bottle, Pack, etc.
    units_per_package = Column(Integer)
    package_quantity = Column(Integer)  # How many packages in a case
    
    # Supplier information
    primary_supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_sku = Column(String(50))
    alternate_suppliers = Column(JSON)  # List of alternate supplier IDs
    
    # Barcode information
    barcode = Column(String(50))
    upc = Column(String(20))
    ean = Column(String(20))
    
    # Status and flags
    is_active = Column(Boolean, default=True)
    is_perishable = Column(Boolean, default=False)
    is_fragile = Column(Boolean, default=False)
    is_hazardous = Column(Boolean, default=False)
    is_age_restricted = Column(Boolean, default=False)
    minimum_age = Column(Integer)  # Minimum age for purchase
    
    # Tax information
    tax_category = Column(String(50))
    tax_rate = Column(Numeric(5, 4))  # Tax rate as decimal (e.g., 0.075 for 7.5%)
    
    # Relationships
    primary_department = relationship('Department', back_populates='products')
    shopping_cart_items = relationship('ShoppingCartItem', back_populates='product')
    abandoned_carts = relationship('AbandonedCart', back_populates='product')
    
    def get_effective_price(self, quantity: int = 1) -> Decimal:
        """Get effective price based on quantity and promotions"""
        # Check promotional price first
        if (self.promotional_price and self.promotional_start_date and self.promotional_end_date and
            self.promotional_start_date <= date.today() <= self.promotional_end_date):
            return self.promotional_price
        
        # Check bulk pricing
        if self.bulk_pricing_tiers and quantity > 1:
            for tier in sorted(self.bulk_pricing_tiers, key=lambda x: x['min_quantity'], reverse=True):
                if quantity >= tier['min_quantity']:
                    return Decimal(str(tier['price_per_unit']))
        
        # Return regular price
        return self.unit_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('unit_price'):
            result['unit_price'] = float(result['unit_price'])
        if result.get('cost_price'):
            result['cost_price'] = float(result['cost_price'])
        if result.get('wholesale_price'):
            result['wholesale_price'] = float(result['wholesale_price'])
        if result.get('promotional_price'):
            result['promotional_price'] = float(result['promotional_price'])
        if result.get('tax_rate'):
            result['tax_rate'] = float(result['tax_rate'])
        # Add computed fields
        result['effective_price'] = float(self.get_effective_price())
        return result


class ShoppingCartItem(FeatureAwareModel):
    """Shopping cart item for abandoned cart analysis"""
    
    __tablename__ = 'shopping_cart_items'
    
    # Reference information
    cart_id = Column(String(100), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('hypermarket_products.id'), nullable=False)
    
    # Item information
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))
    
    # Customer information
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    session_id = Column(String(100))  # For guest customers
    
    # Timing information
    added_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_purchased = Column(Boolean, default=False)
    
    # Relationships
    product = relationship('HypermarketProduct', back_populates='shopping_cart_items')
    
    def calculate_total_price(self):
        """Calculate total price for this item"""
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        return self.total_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('unit_price'):
            result['unit_price'] = float(result['unit_price'])
        if result.get('total_price'):
            result['total_price'] = float(result['total_price'])
        # Include product information
        if self.product:
            result['product_name'] = self.product.name
            result['product_sku'] = self.product.sku_base
        return result


class AbandonedCart(FeatureAwareModel):
    """Abandoned cart analysis for recovery strategies"""
    
    __tablename__ = 'abandoned_carts'
    
    # Cart information
    cart_id = Column(String(100), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    session_id = Column(String(100))  # For guest customers
    
    # Cart value
    total_items = Column(Integer, default=0)
    total_value = Column(Numeric(10, 2))
    
    # Timing information
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    abandoned_at = Column(DateTime)
    
    # Recovery information
    recovery_email_sent = Column(Boolean, default=False)
    recovery_email_sent_at = Column(DateTime)
    recovery_sms_sent = Column(Boolean, default=False)
    recovery_sms_sent_at = Column(DateTime)
    recovery_status = Column(String(20))  # Not Attempted, Email Sent, SMS Sent, Recovered, Lost
    
    # Analysis data
    abandonment_reason = Column(String(100))  # High Price, Shipping Cost, etc.
    abandonment_stage = Column(String(50))  # Browse, Cart, Checkout, Payment
    
    # Relationships
    product = relationship('HypermarketProduct', back_populates='abandoned_carts')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('total_value'):
            result['total_value'] = float(result['total_value'])
        return result


class DepartmentPromotion(FeatureAwareModel):
    """Department-specific promotions"""
    
    __tablename__ = 'department_promotions'
    
    # Basic promotion information
    promotion_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Department information
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    
    # Promotion timing
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Promotion type and details
    promotion_type = Column(String(50), nullable=False)  # Percentage, Fixed Amount, BOGO, etc.
    discount_value = Column(Numeric(10, 2))  # Discount percentage or amount
    minimum_purchase = Column(Numeric(10, 2))
    maximum_discount = Column(Numeric(10, 2))
    
    # Product applicability
    applicable_categories = Column(JSON)  # Categories this applies to
    applicable_products = Column(JSON)  # Specific product IDs
    excluded_products = Column(JSON)  # Product IDs to exclude
    
    # Usage limits
    usage_limit = Column(Integer)  # Total usage limit
    usage_limit_per_customer = Column(Integer)
    current_usage_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Relationships
    department = relationship('Department', back_populates='promotions')
    
    def is_valid(self) -> bool:
        """Check if promotion is currently valid"""
        if not self.is_active:
            return False
        
        today = date.today()
        if not (self.start_date <= today <= self.end_date):
            return False
        
        if self.usage_limit and self.current_usage_count >= self.usage_limit:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('discount_value'):
            result['discount_value'] = float(result['discount_value'])
        if result.get('minimum_purchase'):
            result['minimum_purchase'] = float(result['minimum_purchase'])
        if result.get('maximum_discount'):
            result['maximum_discount'] = float(result['maximum_discount'])
        # Add computed fields
        result['is_valid'] = self.is_valid()
        return result


class DepartmentSales(FeatureAwareModel):
    """Department-wise sales tracking"""
    
    __tablename__ = 'department_sales'
    
    # Reference information
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    
    # Period information
    sales_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), default='Daily')  # Daily, Weekly, Monthly
    
    # Sales metrics
    total_sales = Column(Numeric(12, 2), nullable=False)
    total_transactions = Column(Integer, default=0)
    total_items_sold = Column(Integer, default=0)
    total_customers = Column(Integer, default=0)
    
    # Performance metrics
    average_transaction_value = Column(Numeric(10, 2))
    conversion_rate = Column(Numeric(5, 4))  # As decimal (e.g., 0.125 for 12.5%)
    footfall_count = Column(Integer)
    
    # Product metrics
    unique_products_sold = Column(Integer, default=0)
    top_selling_products = Column(JSON)  # Top 5 products with quantities
    
    # Staff metrics
    staff_count = Column(Integer)
    sales_per_staff = Column(Numeric(10, 2))
    
    # Relationships
    department = relationship('Department', back_populates='sales_records')
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics"""
        if self.total_transactions and self.total_transactions > 0:
            self.average_transaction_value = self.total_sales / self.total_transactions
        
        if self.footfall_count and self.footfall_count > 0:
            self.conversion_rate = Decimal(str(self.total_customers)) / self.footfall_count
        
        if self.staff_count and self.staff_count > 0:
            self.sales_per_staff = self.total_sales / self.staff_count
        
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('total_sales'):
            result['total_sales'] = float(result['total_sales'])
        if result.get('average_transaction_value'):
            result['average_transaction_value'] = float(result['average_transaction_value'])
        if result.get('conversion_rate'):
            result['conversion_rate'] = float(result['conversion_rate'])
        if result.get('sales_per_staff'):
            result['sales_per_staff'] = float(result['sales_per_staff'])
        return result


class SelfCheckout(FeatureAwareModel):
    """Self-checkout station management"""
    
    __tablename__ = 'self_checkouts'
    
    # Basic information
    checkout_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    
    # Location information
    location = Column(String(100))
    department_id = Column(Integer, ForeignKey('departments.id'))
    
    # Status information
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    status = Column(String(20), default='Offline')  # Online, Offline, Maintenance, Error
    
    # Configuration
    supports_cash = Column(Boolean, default=False)
    supports_card = Column(Boolean, default=True)
    supports_mobile = Column(Boolean, default=True)
    weight_limit_kg = Column(Float)
    
    # Usage statistics
    total_transactions = Column(Integer, default=0)
    total_sales_amount = Column(Numeric(12, 2), default=0)
    average_transaction_time_seconds = Column(Integer)
    
    # Maintenance information
    last_maintenance_date = Column(Date)
    next_maintenance_date = Column(Date)
    maintenance_interval_days = Column(Integer, default=30)
    
    # Relationships
    department = relationship('Department')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('total_sales_amount'):
            result['total_sales_amount'] = float(result['total_sales_amount'])
        # Add computed fields
        if result.get('next_maintenance_date'):
            result['maintenance_due'] = date.today() >= result['next_maintenance_date']
        return result


class QueueManagement(FeatureAwareModel):
    """Queue management system"""
    
    __tablename__ = 'queue_management'
    
    # Basic information
    queue_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    queue_type = Column(String(50), nullable=False)  # Checkout, Service, Information, etc.
    
    # Location information
    location = Column(String(100))
    department_id = Column(Integer, ForeignKey('departments.id'))
    
    # Current status
    is_active = Column(Boolean, default=True)
    current_length = Column(Integer, default=0)
    average_wait_time_minutes = Column(Integer, default=0)
    maximum_capacity = Column(Integer)
    
    # Service configuration
    service_points = Column(Integer, default=1)  # Number of service points
    average_service_time_minutes = Column(Integer)
    
    # Performance metrics
    total_customers_served_today = Column(Integer, default=0)
    average_service_time_today = Column(Integer)
    peak_queue_length_today = Column(Integer, default=0)
    
    # Staffing information
    current_staff_count = Column(Integer, default=0)
    
    # Relationships
    department = relationship('Department')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Add computed fields
        if self.maximum_capacity and self.current_length:
            result['capacity_percentage'] = (self.current_length / self.maximum_capacity * 100) if self.maximum_capacity > 0 else 0
        else:
            result['capacity_percentage'] = 0
        return result