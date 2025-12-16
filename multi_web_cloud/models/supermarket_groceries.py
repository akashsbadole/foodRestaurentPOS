"""
Supermarket & Groceries models with fresh produce and weighing scale integration
"""

from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal

from models.feature_aware_model import FeatureAwareModel
from models import db


class FreshProduce(FeatureAwareModel):
    """Fresh produce model with shelf life management"""
    
    __tablename__ = 'fresh_produce'
    
    # Basic product information
    product_id = Column(String(50), nullable=False, unique=True, index=True)
    sku_base = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Produce-specific attributes
    produce_category = Column(String(100))  # Fruits, Vegetables, Herbs, etc.
    variety = Column(String(100))  # Specific variety (e.g., "Roma", "Gala")
    origin = Column(String(100))  # Country or region of origin
    grade = Column(String(50))  # Grade A, Grade B, Premium, etc.
    certification = Column(String(100))  # Organic, Fair Trade, etc.
    
    # Pricing information
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    price_per_kg = Column(Numeric(10, 2))  # Price per kilogram for weighed items
    
    # Weight and sizing
    average_weight_per_unit = Column(Float)  # Average weight in grams
    weight_variance = Column(Float)  # Weight variance percentage
    size_category = Column(String(50))  # Small, Medium, Large, etc.
    
    # Shelf life and freshness
    shelf_life_days = Column(Integer)  # Standard shelf life
    optimal_storage_temp = Column(Float)  # Optimal storage temperature
    optimal_humidity = Column(Float)  # Optimal humidity percentage
    ripeness_indicators = Column(JSON)  # Color, firmness, etc.
    
    # Seasonal information
    is_seasonal = Column(Boolean, default=False)
    peak_season_start = Column(Date)
    peak_season_end = Column(Date)
    off_season_available = Column(Boolean, default=True)
    
    # Quality attributes
    quality_score = Column(Integer)  # 1-10 quality score
    inspection_date = Column(Date)
    inspector_name = Column(String(100))
    quality_notes = Column(Text)
    
    # Barcode and identification
    barcode = Column(String(50))
    plu_code = Column(String(10))  # Price Look-Up code
    batch_number = Column(String(50))
    
    # Supplier information
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_farm = Column(String(100))
    
    # Inventory management
    current_stock = Column(Integer, default=0)
    minimum_stock_level = Column(Integer, default=5)
    maximum_stock_level = Column(Integer, default=100)
    reorder_point = Column(Integer, default=10)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_on_promotion = Column(Boolean, default=False)
    
    # Relationships
    inventory_movements = relationship('FreshProduceInventory', back_populates='produce')
    price_updates = relationship('FreshProducePriceUpdate', back_populates='produce')
    quality_checks = relationship('FreshProduceQualityCheck', back_populates='produce')
    
    def get_current_price(self) -> Decimal:
        """Get current price based on promotions and seasonality"""
        # Check for promotional pricing
        if self.is_on_promotion:
            # This would integrate with promotion system
            pass
        
        # Check for seasonal pricing
        if self.is_seasonal and self.peak_season_start and self.peak_season_end:
            today = date.today()
            if self.peak_season_start <= today <= self.peak_season_end:
                # Apply seasonal price adjustment (e.g., 10% premium)
                return self.unit_price * Decimal('1.1')
        
        return self.unit_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('unit_price'):
            result['unit_price'] = float(result['unit_price'])
        if result.get('cost_price'):
            result['cost_price'] = float(result['cost_price'])
        if result.get('price_per_kg'):
            result['price_per_kg'] = float(result['price_per_kg'])
        # Add computed fields
        result['current_price'] = float(self.get_current_price())
        return result


class FreshProduceInventory(FeatureAwareModel):
    """Inventory tracking for fresh produce with quality monitoring"""
    
    __tablename__ = 'fresh_produce_inventory'
    
    # Reference information
    produce_id = Column(Integer, ForeignKey('fresh_produce.id'), nullable=False)
    batch_number = Column(String(50))
    
    # Quantity information
    initial_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, nullable=False)
    unit_of_measure = Column(String(20), default='units')
    
    # Date information
    received_date = Column(Date, nullable=False)
    expiry_date = Column(Date)
    last_quality_check = Column(Date)
    
    # Quality information
    quality_grade = Column(String(50))
    quality_score = Column(Integer)  # 1-10 score
    spoilage_percentage = Column(Float, default=0.0)
    
    # Location information
    storage_location = Column(String(100))
    display_area = Column(String(100))
    
    # Temperature monitoring
    storage_temperature = Column(Float)  # Current storage temperature
    temperature_log = Column(JSON)  # Temperature history
    
    # Movement tracking
    last_sale_date = Column(Date)
    last_waste_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_on_display = Column(Boolean, default=True)
    
    # Relationships
    produce = relationship('FreshProduce', back_populates='inventory_movements')
    
    def calculate_waste_value(self) -> Decimal:
        """Calculate value of wasted produce"""
        if self.produce and self.spoilage_percentage:
            wasted_quantity = self.initial_quantity * (self.spoilage_percentage / 100)
            return wasted_quantity * self.produce.cost_price or Decimal('0.00')
        return Decimal('0.00')
    
    def is_near_expiry(self, days_threshold: int = 3) -> bool:
        """Check if produce is near expiry"""
        if not self.expiry_date:
            return False
        threshold_date = date.today() + timedelta(days=days_threshold)
        return self.expiry_date <= threshold_date
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Add computed fields
        result['waste_value'] = float(self.calculate_waste_value())
        result['is_near_expiry'] = self.is_near_expiry()
        result['days_to_expiry'] = (self.expiry_date - date.today()).days if self.expiry_date else None
        return result


class FreshProducePriceUpdate(FeatureAwareModel):
    """Price update tracking for fresh produce"""
    
    __tablename__ = 'fresh_produce_price_updates'
    
    # Reference information
    produce_id = Column(Integer, ForeignKey('fresh_produce.id'), nullable=False)
    
    # Price information
    old_price = Column(Numeric(10, 2))
    new_price = Column(Numeric(10, 2), nullable=False)
    price_change_percentage = Column(Float)
    
    # Reason for change
    change_reason = Column(String(100))  # Market Price, Quality, Seasonal, etc.
    supplier_price_change = Column(Boolean, default=False)
    
    # Date information
    effective_date = Column(Date, nullable=False)
    approved_by = Column(String(100))
    approval_date = Column(Date)
    
    # Market information
    market_price = Column(Numeric(10, 2))  # Current market price
    competitor_price = Column(Numeric(10, 2))  # Average competitor price
    
    # Relationships
    produce = relationship('FreshProduce', back_populates='price_updates')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('old_price'):
            result['old_price'] = float(result['old_price'])
        if result.get('new_price'):
            result['new_price'] = float(result['new_price'])
        if result.get('market_price'):
            result['market_price'] = float(result['market_price'])
        if result.get('competitor_price'):
            result['competitor_price'] = float(result['competitor_price'])
        return result


class FreshProduceQualityCheck(FeatureAwareModel):
    """Quality check records for fresh produce"""
    
    __tablename__ = 'fresh_produce_quality_checks'
    
    # Reference information
    produce_id = Column(Integer, ForeignKey('fresh_produce.id'), nullable=False)
    batch_number = Column(String(50))
    
    # Check information
    check_date = Column(Date, nullable=False)
    check_time = Column(DateTime)
    inspector_name = Column(String(100), nullable=False)
    
    # Quality metrics
    overall_quality_score = Column(Integer)  # 1-10 score
    appearance_score = Column(Integer)  # 1-10 score
    freshness_score = Column(Integer)  # 1-10 score
    size_consistency = Column(Integer)  # 1-10 score
    
    # Specific checks
    color_quality = Column(String(50))  # Excellent, Good, Fair, Poor
    firmness = Column(String(50))
    ripeness = Column(String(50))
    defects = Column(JSON)  # List of identified defects
    
    # Measurements
    temperature_fahrenheit = Column(Float)
    humidity_percentage = Column(Float)
    weight_sample_size = Column(Integer)  # Number of items weighed
    average_weight = Column(Float)  # Average weight in grams
    
    # Results
    grade_assigned = Column(String(50))
    passed_inspection = Column(Boolean)
    rejection_reasons = Column(JSON)  # Reasons for rejection if any
    
    # Actions taken
    actions_required = Column(JSON)  # Actions needed (repack, discount, etc.)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    
    # Relationships
    produce = relationship('FreshProduce', back_populates='quality_checks')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        return result


class WeighingScaleIntegration(FeatureAwareModel):
    """Weighing scale integration for fresh produce"""
    
    __tablename__ = 'weighing_scale_integrations'
    
    # Scale information
    scale_id = Column(String(50), nullable=False, unique=True, index=True)
    scale_name = Column(String(100), nullable=False)
    location = Column(String(100))  # Produce section, deli, etc.
    department = Column(String(50))
    
    # Connection information
    connection_type = Column(String(20), nullable=False)  # USB, Serial, Network, Bluetooth
    connection_parameters = Column(JSON)  # Port, baud rate, IP address, etc.
    
    # Scale specifications
    capacity_kg = Column(Float)
    readability_g = Column(Float)  # Smallest readable increment
    units_supported = Column(JSON)  # kg, g, lb, oz
    
    # Configuration
    tare_weight_g = Column(Float, default=0.0)  # Container weight
    auto_tare_enabled = Column(Boolean, default=True)
    price_per_weight_enabled = Column(Boolean, default=True)
    
    # Calibration information
    last_calibration_date = Column(Date)
    calibration_frequency_days = Column(Integer, default=7)
    next_calibration_date = Column(Date)
    calibration_certificate = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_connection_time = Column(DateTime)
    
    # Usage statistics
    daily_weighings = Column(Integer, default=0)
    total_weight_kg = Column(Float, default=0.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Add computed fields
        if result.get('next_calibration_date'):
            result['calibration_due'] = date.today() >= result['next_calibration_date']
        return result


class ComboOffer(FeatureAwareModel):
    """Combo offers for grocery items"""
    
    __tablename__ = 'combo_offers'
    
    # Basic information
    combo_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Timing information
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)
    
    # Combo configuration
    combo_type = Column(String(50), nullable=False)  # Fixed Price, Percentage Discount, etc.
    discount_type = Column(String(50))  # Fixed Amount, Percentage
    discount_value = Column(Numeric(10, 2))
    combo_price = Column(Numeric(10, 2))
    
    # Product composition
    main_product_id = Column(Integer, ForeignKey('products.id'))
    main_product_quantity = Column(Integer, default=1)
    additional_products = Column(JSON)  # List of product IDs and quantities
    
    # Restrictions
    minimum_purchase_quantity = Column(Integer, default=1)
    maximum_per_customer = Column(Integer)
    applicable_categories = Column(JSON)
    excluded_products = Column(JSON)
    
    # Display information
    display_name = Column(String(200))
    image_url = Column(String(500))
    promotional_text = Column(Text)
    
    # Analytics
    usage_count = Column(Integer, default=0)
    revenue_generated = Column(Numeric(12, 2), default=0.00)
    
    def calculate_effective_price(self) -> Decimal:
        """Calculate effective price based on combo configuration"""
        # This would integrate with product pricing
        return self.combo_price or Decimal('0.00')
    
    def is_valid(self) -> bool:
        """Check if combo offer is currently valid"""
        if not self.is_active:
            return False
        
        today = date.today()
        if not (self.start_date <= today <= (self.end_date or date.max)):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('discount_value'):
            result['discount_value'] = float(result['discount_value'])
        if result.get('combo_price'):
            result['combo_price'] = float(result['combo_price'])
        if result.get('revenue_generated'):
            result['revenue_generated'] = float(result['revenue_generated'])
        # Add computed fields
        result['effective_price'] = float(self.calculate_effective_price())
        result['is_valid'] = self.is_valid()
        return result


class ShelfLifeManagement(FeatureAwareModel):
    """Shelf life management for perishable items"""
    
    __tablename__ = 'shelf_life_management'
    
    # Reference information
    product_id = Column(String(50), nullable=False, index=True)
    batch_number = Column(String(50))
    
    # Shelf life information
    production_date = Column(Date)
    received_date = Column(Date, default=date.today)
    expiry_date = Column(Date, nullable=False)
    
    # Quality stages
    optimal_until = Column(Date)  # Peak quality until this date
    good_until = Column(Date)  # Good quality until this date
    sell_by_date = Column(Date)  # Should be sold by this date
    
    # Storage requirements
    optimal_temperature = Column(Float)
    optimal_humidity = Column(Float)
    light_requirements = Column(String(50))  # Dark, Low Light, etc.
    
    # Quality degradation tracking
    quality_loss_rate = Column(Float, default=0.0)  # Percentage per day
    current_quality_score = Column(Integer, default=10)  # Starts at 10 (perfect)
    
    # Discount schedule
    discount_schedule = Column(JSON)  # Progressive discounts as expiry approaches
    
    # Actions
    mark_down_schedule = Column(JSON)  # Scheduled price reductions
    disposal_method = Column(String(50))  # Donate, Discount, Dispose
    
    # Status
    is_active = Column(Boolean, default=True)
    requires_action = Column(Boolean, default=False)
    action_taken = Column(String(100))
    
    def get_current_quality_stage(self) -> str:
        """Get current quality stage based on date"""
        today = date.today()
        
        if self.optimal_until and today <= self.optimal_until:
            return "Optimal"
        elif self.good_until and today <= self.good_until:
            return "Good"
        elif self.sell_by_date and today <= self.sell_by_date:
            return "Acceptable"
        else:
            return "Expired"
    
    def get_recommended_action(self) -> str:
        """Get recommended action based on current quality"""
        stage = self.get_current_quality_stage()
        
        if stage == "Optimal":
            return "Display at full price"
        elif stage == "Good":
            return "Consider minor promotion"
        elif stage == "Acceptable":
            return "Apply discount or mark down"
        else:
            return "Remove from display - dispose"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Add computed fields
        result['current_quality_stage'] = self.get_current_quality_stage()
        result['recommended_action'] = self.get_recommended_action()
        return result


class FreshCounter(FeatureAwareModel):
    """Fresh counter management (deli, butcher, bakery, etc.)"""
    
    __tablename__ = 'fresh_counters'
    
    # Basic information
    counter_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    counter_type = Column(String(50), nullable=False)  # Deli, Butcher, Bakery, etc.
    
    # Location information
    location = Column(String(100))
    department = Column(String(50))
    section = Column(String(50))
    
    # Operating information
    opening_time = Column(String(10))  # HH:MM format
    closing_time = Column(String(10))  # HH:MM format
    operating_days = Column(JSON)  # List of operating days
    
    # Staffing information
    manager_name = Column(String(100))
    staff_count = Column(Integer, default=1)
    required_skills = Column(JSON)  # Butchery, baking, etc.
    
    # Equipment
    equipment_list = Column(JSON)  # Slicers, ovens, scales, etc.
    weighing_scale_id = Column(String(50))  # Reference to scale
    
    # Service configuration
    service_time_minutes = Column(Integer, default=5)
    queue_management_enabled = Column(Boolean, default=True)
    advance_ordering_enabled = Column(Boolean, default=True)
    
    # Performance metrics
    daily_customers = Column(Integer, default=0)
    average_transaction_value = Column(Numeric(10, 2))
    customer_satisfaction_score = Column(Float)  # 1-5 scale
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default='Open')  # Open, Closed, Maintenance
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('average_transaction_value'):
            result['average_transaction_value'] = float(result['average_transaction_value'])
        return result