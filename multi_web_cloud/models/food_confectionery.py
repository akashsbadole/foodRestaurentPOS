"""
Food & Confectionery models with expiry tracking and batch management
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, JSON, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal

from models.feature_aware_model import FeatureAwareModel
from models import db


class FoodProduct(FeatureAwareModel):
    """Food and confectionery product model with expiry tracking"""
    
    __tablename__ = 'food_products'
    
    # Basic product information
    product_id = Column(String(50), nullable=False, unique=True, index=True)
    sku_base = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Food-specific attributes
    food_category = Column(String(100))  # Bakery, Confectionery, Dairy, Frozen, etc.
    subcategory = Column(String(100))
    brand = Column(String(100))
    flavor_variety = Column(String(100))
    size_description = Column(String(100))
    unit_of_measure = Column(String(20))  # kg, g, ml, l, pcs, etc.
    
    # Pricing
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    wholesale_price = Column(Numeric(10, 2))
    
    # Expiry and shelf life
    shelf_life_days = Column(Integer)  # Standard shelf life in days
    storage_temperature_min = Column(Float)  # Minimum storage temperature (°C)
    storage_temperature_max = Column(Float)  # Maximum storage temperature (°C)
    storage_requirements = Column(String(200))  # Refrigerated, Frozen, Ambient, etc.
    handling_instructions = Column(Text)
    
    # Nutritional information
    calories_per_serving = Column(Integer)
    serving_size = Column(String(50))
    nutritional_info = Column(JSON)  # Detailed nutritional breakdown
    
    # Allergen and dietary information
    allergens = Column(JSON)  # List of allergens
    dietary_restrictions = Column(JSON)  # Vegetarian, Vegan, Gluten-Free, etc.
    certifications = Column(JSON)  # Organic, Halal, Kosher, etc.
    
    # Weight and dimensions
    net_weight = Column(Float)  # Net weight in grams
    gross_weight = Column(Float)  # Gross weight including packaging
    package_dimensions = Column(JSON)  # Length, Width, Height in cm
    
    # Batch and expiry tracking
    requires_batch_tracking = Column(Boolean, default=False)
    expiry_date_required = Column(Boolean, default=True)
    sell_by_days_before_expiry = Column(Integer, default=3)  # Days to remove before expiry
    
    # Temperature sensitive
    temperature_sensitive = Column(Boolean, default=False)
    cold_chain_required = Column(Boolean, default=False)
    
    # Recipe and preparation
    is_prepared_item = Column(Boolean, default=False)
    recipe_id = Column(String(50))  # Reference to recipe if prepared item
    preparation_time_minutes = Column(Integer)
    cooking_instructions = Column(Text)
    
    # Weighing scale integration
    sold_by_weight = Column(Boolean, default=False)
    price_per_kg = Column(Numeric(10, 2))
    tare_weight = Column(Float, default=0.0)  # Container weight for weighed items
    
    # Inventory management
    minimum_stock_level = Column(Integer, default=5)
    maximum_stock_level = Column(Integer, default=100)
    reorder_point = Column(Integer, default=10)
    
    # Supplier information
    primary_supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_sku = Column(String(50))
    
    # Barcode information
    barcode = Column(String(50))
    upc = Column(String(20))
    ean = Column(String(20))
    
    # Status and flags
    is_seasonal = Column(Boolean, default=False)
    is_promotional = Column(Boolean, default=False)
    is_best_seller = Column(Boolean, default=False)
    is_new_product = Column(Boolean, default=False)
    
    # Relationships
    batches = relationship('FoodBatch', back_populates='product', cascade='all, delete-orphan')
    temperature_logs = relationship('TemperatureLog', back_populates='product', cascade='all, delete-orphan')
    recipe_items = relationship('RecipeItem', back_populates='product', cascade='all, delete-orphan')
    wastage_records = relationship('FoodWastage', back_populates='product', cascade='all, delete-orphan')
    
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
        if result.get('price_per_kg'):
            result['price_per_kg'] = float(result['price_per_kg'])
        return result
    
    def get_current_stock(self) -> int:
        """Get current stock across all batches"""
        total_stock = 0
        for batch in self.batches:
            if batch.is_active and not batch.is_expired():
                total_stock += batch.current_quantity
        return total_stock
    
    def get_expiry_status(self) -> Dict[str, Any]:
        """Get expiry status summary"""
        now = date.today()
        expired_count = 0
        expiring_soon_count = 0
        normal_count = 0
        
        for batch in self.batches:
            if not batch.is_active:
                continue
                
            if batch.is_expired():
                expired_count += batch.current_quantity
            elif batch.is_expiring_soon():
                expiring_soon_count += batch.current_quantity
            else:
                normal_count += batch.current_quantity
        
        return {
            'expired_quantity': expired_count,
            'expiring_soon_quantity': expiring_soon_count,
            'normal_quantity': normal_count,
            'total_quantity': expired_count + expiring_soon_count + normal_count
        }


class FoodBatch(FeatureAwareModel):
    """Batch tracking for food products with expiry dates"""
    
    __tablename__ = 'food_batches'
    
    # Basic batch information
    batch_number = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('food_products.id'), nullable=False)
    
    # Date information
    production_date = Column(Date)
    expiry_date = Column(Date, nullable=False)
    received_date = Column(Date, default=date.today)
    
    # Quantity information
    initial_quantity = Column(Integer, nullable=False)
    current_quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2))
    
    # Quality information
    quality_grade = Column(String(20))  # A, B, C, etc.
    quality_notes = Column(Text)
    
    # Supplier information
    supplier_id = Column(Integer, ForeignKey('suppliers.id'))
    supplier_batch_number = Column(String(50))
    
    # Storage information
    storage_location = Column(String(100))
    storage_temperature = Column(Float)  # Actual storage temperature
    storage_humidity = Column(Float)  # Storage humidity percentage
    
    # Status
    is_active = Column(Boolean, default=True)
    is_quarantined = Column(Boolean, default=False)
    quarantine_reason = Column(Text)
    
    # Relationships
    product = relationship('FoodProduct', back_populates='batches')
    temperature_logs = relationship('TemperatureLog', back_populates='batch', cascade='all, delete-orphan')
    wastage_records = relationship('FoodWastage', back_populates='batch', cascade='all, delete-orphan')
    
    def is_expired(self) -> bool:
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    def is_expiring_soon(self, days_threshold: int = 7) -> bool:
        """Check if batch is expiring soon"""
        if not self.expiry_date:
            return False
        threshold_date = date.today() + timedelta(days=days_threshold)
        return self.expiry_date <= threshold_date
    
    def get_days_to_expiry(self) -> int:
        """Get days remaining until expiry"""
        if not self.expiry_date:
            return 999  # Large number for no expiry date
        delta = self.expiry_date - date.today()
        return max(0, delta.days)
    
    def get_sell_by_date(self) -> date:
        """Get sell by date (expiry date minus buffer)"""
        if not self.expiry_date or not self.product:
            return self.expiry_date or date.max
        
        buffer_days = self.product.sell_by_days_before_expiry or 3
        return self.expiry_date - timedelta(days=buffer_days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('unit_cost'):
            result['unit_cost'] = float(result['unit_cost'])
        # Add computed fields
        result['is_expired'] = self.is_expired()
        result['is_expiring_soon'] = self.is_expiring_soon()
        result['days_to_expiry'] = self.get_days_to_expiry()
        result['sell_by_date'] = self.get_sell_by_date().isoformat() if self.get_sell_by_date() else None
        return result


class TemperatureLog(FeatureAwareModel):
    """Temperature logging for food safety compliance"""
    
    __tablename__ = 'temperature_logs'
    
    # Reference information
    product_id = Column(Integer, ForeignKey('food_products.id'), nullable=False)
    batch_id = Column(Integer, ForeignKey('food_batches.id'), nullable=True)  # Optional if not batch-specific
    
    # Temperature information
    temperature_celsius = Column(Float, nullable=False)
    target_temperature = Column(Float)  # Required temperature for this product
    tolerance_plus = Column(Float, default=2.0)  # Upper tolerance
    tolerance_minus = Column(Float, default=2.0)  # Lower tolerance
    
    # Reading information
    reading_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    reading_device_id = Column(String(50))  # Thermometer or sensor ID
    reading_location = Column(String(100))  # Fridge, freezer, storage area, etc.
    
    # Status
    is_within_range = Column(Boolean)  # Calculated field
    requires_action = Column(Boolean, default=False)
    action_taken = Column(Text)
    
    # Staff information
    recorded_by = Column(String(100))
    verified_by = Column(String(100))
    verification_time = Column(DateTime)
    
    # Relationships
    product = relationship('FoodProduct', back_populates='temperature_logs')
    batch = relationship('FoodBatch', back_populates='temperature_logs')
    
    def check_temperature_range(self) -> bool:
        """Check if temperature is within acceptable range"""
        if not self.target_temperature:
            return True  # No target means always acceptable
        
        min_temp = self.target_temperature - (self.tolerance_minus or 2.0)
        max_temp = self.target_temperature + (self.tolerance_plus or 2.0)
        
        return min_temp <= self.temperature_celsius <= max_temp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Check and set is_within_range if not already set
        if result.get('is_within_range') is None:
            result['is_within_range'] = self.check_temperature_range()
        return result


class Recipe(FeatureAwareModel):
    """Recipe management for prepared food items"""
    
    __tablename__ = 'recipes'
    
    # Basic recipe information
    recipe_code = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    cuisine_type = Column(String(50))
    
    # Preparation information
    preparation_time_minutes = Column(Integer)
    cooking_time_minutes = Column(Integer)
    total_time_minutes = Column(Integer)
    difficulty_level = Column(String(20))  # Easy, Medium, Hard
    
    # Yield information
    yield_quantity = Column(Float, nullable=False)  # How much the recipe makes
    yield_unit = Column(String(20))  # kg, g, liters, portions, etc.
    serving_size = Column(String(50))
    
    # Cost information
    total_cost = Column(Numeric(10, 2))
    cost_per_unit = Column(Numeric(10, 2))
    
    # Instructions
    preparation_method = Column(Text)
    cooking_instructions = Column(Text)
    presentation_notes = Column(Text)
    
    # Nutritional information
    calories_per_serving = Column(Integer)
    nutritional_info = Column(JSON)
    
    # Allergen information
    allergens = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_standardized = Column(Boolean, default=False)
    
    # Version control
    version = Column(String(20), default="1.0")
    last_revision_date = Column(Date, default=date.today)
    revised_by = Column(String(100))
    
    # Relationships
    recipe_items = relationship('RecipeItem', back_populates='recipe', cascade='all, delete-orphan')
    
    def calculate_cost(self):
        """Calculate recipe cost based on ingredients"""
        total_cost = Decimal('0.00')
        for item in self.recipe_items:
            if item.ingredient_product and item.ingredient_product.unit_price:
                ingredient_cost = Decimal(str(item.ingredient_product.unit_price))
                total_cost += ingredient_cost * Decimal(str(item.quantity))
        
        self.total_cost = total_cost
        if self.yield_quantity and self.yield_quantity > 0:
            self.cost_per_unit = total_cost / Decimal(str(self.yield_quantity))
        
        return total_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('total_cost'):
            result['total_cost'] = float(result['total_cost'])
        if result.get('cost_per_unit'):
            result['cost_per_unit'] = float(result['cost_per_unit'])
        return result


class RecipeItem(FeatureAwareModel):
    """Individual ingredients in a recipe"""
    
    __tablename__ = 'recipe_items'
    
    # Reference information
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('food_products.id'), nullable=False)
    
    # Quantity information
    quantity = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    
    # Preparation instructions
    preparation_method = Column(String(100))  # Chopped, diced, boiled, etc.
    cooking_instruction = Column(Text)
    
    # Substitution information
    can_be_substituted = Column(Boolean, default=False)
    substitution_options = Column(JSON)  # Alternative ingredients
    
    # Quality requirements
    quality_grade_required = Column(String(20))
    special_requirements = Column(Text)
    
    # Relationships
    recipe = relationship('Recipe', back_populates='recipe_items')
    ingredient_product = relationship('FoodProduct', back_populates='recipe_items')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Include ingredient product information
        if self.ingredient_product:
            result['ingredient_name'] = self.ingredient_product.name
            result['ingredient_sku'] = self.ingredient_product.sku_base
        return result


class FoodWastage(FeatureAwareModel):
    """Wastage tracking for food items"""
    
    __tablename__ = 'food_wastage'
    
    # Reference information
    product_id = Column(Integer, ForeignKey('food_products.id'), nullable=False)
    batch_id = Column(Integer, ForeignKey('food_batches.id'), nullable=True)
    
    # Wastage information
    wastage_date = Column(Date, default=date.today, nullable=False)
    quantity = Column(Float, nullable=False)
    unit_of_measure = Column(String(20), nullable=False)
    
    # Reason for wastage
    wastage_reason = Column(String(100), nullable=False)  # Expired, Spoiled, Damaged, etc.
    wastage_category = Column(String(50))  # Waste, Spoilage, Theft, etc.
    detailed_reason = Column(Text)
    
    # Financial impact
    unit_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))
    
    # Prevention information
    prevention_measures = Column(Text)
    is_preventable = Column(Boolean, default=True)
    
    # Staff information
    reported_by = Column(String(100))
    approved_by = Column(String(100))
    
    # Status
    is_documented = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    
    # Relationships
    product = relationship('FoodProduct', back_populates='wastage_records')
    batch = relationship('FoodBatch', back_populates='wastage_records')
    
    def calculate_cost(self):
        """Calculate wastage cost"""
        if self.unit_cost and self.quantity:
            self.total_cost = Decimal(str(self.unit_cost)) * Decimal(str(self.quantity))
        return self.total_cost
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Convert Decimal to float for JSON serialization
        if result.get('unit_cost'):
            result['unit_cost'] = float(result['unit_cost'])
        if result.get('total_cost'):
            result['total_cost'] = float(result['total_cost'])
        # Include product information
        if self.product:
            result['product_name'] = self.product.name
            result['product_sku'] = self.product.sku_base
        # Include batch information
        if self.batch:
            result['batch_number'] = self.batch.batch_number
            result['batch_expiry_date'] = self.batch.expiry_date.isoformat() if self.batch.expiry_date else None
        return result


class WeighingScaleIntegration(FeatureAwareModel):
    """Weighing scale integration configuration"""
    
    __tablename__ = 'weighing_scale_integrations'
    
    # Scale information
    scale_id = Column(String(50), nullable=False, unique=True, index=True)
    scale_name = Column(String(100), nullable=False)
    scale_model = Column(String(100))
    manufacturer = Column(String(100))
    
    # Connection information
    connection_type = Column(String(20), nullable=False)  # USB, Serial, Network, Bluetooth
    connection_parameters = Column(JSON)  # Port, baud rate, IP address, etc.
    
    # Scale configuration
    capacity_kg = Column(Float)  # Maximum capacity in kg
    readability_g = Column(Float)  # Smallest readable increment in grams
    units_supported = Column(JSON)  # List of supported units
    
    # Calibration information
    last_calibration_date = Column(Date)
    calibration_frequency_days = Column(Integer, default=30)
    next_calibration_date = Column(Date)
    calibration_certificate = Column(String(200))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=False)
    last_connection_time = Column(DateTime)
    
    # Location
    location = Column(String(100))
    department = Column(String(50))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = super().to_dict()
        # Add computed fields
        if result.get('next_calibration_date'):
            result['calibration_due'] = date.today() >= result['next_calibration_date']
        return result