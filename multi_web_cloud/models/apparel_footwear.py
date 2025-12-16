"""
Apparel & Footwear specific models with feature-aware capabilities
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from . import db
from .feature_aware_model import FeatureAwareModel


class ApparelProduct(FeatureAwareModel, db.Model):
    """Enhanced product model for apparel and footwear"""
    __tablename__ = 'apparel_products'
    
    # Feature requirements
    required_features = ['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS']
    optional_features = ['FEATURE_STYLE_VARIANTS', 'FEATURE_SEASON_MANAGEMENT', 'FEATURE_DESIGNER_BRANDS']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    sku_base = db.Column(db.String(50), nullable=False)  # Base SKU without variant codes
    
    # Apparel specific attributes
    clothing_type = db.Column(db.String(50), nullable=True)  # Shirt, Pants, Dress, etc.
    footwear_type = db.Column(db.String(50), nullable=True)  # Sneakers, Boots, Sandals, etc.
    material = db.Column(db.String(100), nullable=True)
    fit_type = db.Column(db.String(50), nullable=True)  # Regular, Slim, Loose, etc.
    care_instructions = db.Column(db.Text, nullable=True)
    
    # Style and design
    style_name = db.Column(db.String(100), nullable=True)
    collection_name = db.Column(db.String(100), nullable=True)
    season = db.Column(db.String(50), nullable=True)  # Spring, Summer, Fall, Winter, All Season
    year = db.Column(db.Integer, nullable=True)
    
    # Brand and designer
    brand_name = db.Column(db.String(100), nullable=True)
    designer_name = db.Column(db.String(100), nullable=True)
    brand_tier = db.Column(db.String(50), default='Standard')  # Luxury, Premium, Standard, Budget
    
    # Size and fit information
    size_system = db.Column(db.String(50), default='US')  # US, EU, UK, etc.
    size_range = db.Column(db.String(200), nullable=True)  # Available sizes as string
    has_plus_sizes = db.Column(db.Boolean, default=False)
    has_petite_sizes = db.Column(db.Boolean, default=False)
    has_tall_sizes = db.Column(db.Boolean, default=False)
    
    # Color and pattern
    primary_color = db.Column(db.String(50), nullable=True)
    secondary_color = db.Column(db.String(50), nullable=True)
    pattern_type = db.Column(db.String(50), nullable=True)  # Solid, Striped, Plaid, etc.
    
    # Target demographic
    gender = db.Column(db.String(20), nullable=True)  # Men, Women, Unisex, Kids
    age_group = db.Column(db.String(50), nullable=True)  # Adult, Teen, Kids, Toddler, Infant
    
    # Pricing and inventory
    base_price = db.Column(db.Float, nullable=False)
    price_variance = db.Column(db.Float, default=0.0)  # Price difference between variants
    cost_price = db.Column(db.Float, nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    # Relationships
    variants = db.relationship('ApparelVariant', backref='apparel_product', lazy=True, cascade='all, delete-orphan')
    size_matrix = db.relationship('ApparelSizeMatrix', backref='apparel_product', lazy=True, cascade='all, delete-orphan')
    exchanges = db.relationship('ApparelExchange', backref='apparel_product', lazy=True)
    
    def __init__(self, product_id: int, sku_base: str, base_price: float, **kwargs):
        self.product_id = product_id
        self.sku_base = sku_base
        self.base_price = base_price
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_available_sizes(self) -> List[str]:
        """Get list of available sizes"""
        return [variant.size for variant in self.variants if variant.is_active and variant.stock > 0]
    
    def get_available_colors(self) -> List[str]:
        """Get list of available colors"""
        colors = set()
        for variant in self.variants:
            if variant.is_active and variant.stock > 0:
                colors.add(variant.color)
        return list(colors)
    
    def get_price_for_variant(self, size: str, color: str) -> float:
        """Get price for specific variant"""
        variant = ApparelVariant.query.filter_by(
            apparel_product_id=self.id,
            size=size,
            color=color,
            is_active=True
        ).first()
        
        if variant:
            return self.base_price + variant.price_adjustment
        return self.base_price
    
    def get_low_stock_variants(self, threshold: int = 5) -> List['ApparelVariant']:
        """Get variants with low stock"""
        return [v for v in self.variants if v.is_active and v.stock <= threshold]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert apparel product to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'sku_base': self.sku_base,
            'clothing_type': self.clothing_type,
            'footwear_type': self.footwear_type,
            'material': self.material,
            'fit_type': self.fit_type,
            'care_instructions': self.care_instructions,
            'style_name': self.style_name,
            'collection_name': self.collection_name,
            'season': self.season,
            'year': self.year,
            'brand_name': self.brand_name,
            'designer_name': self.designer_name,
            'brand_tier': self.brand_tier,
            'size_system': self.size_system,
            'size_range': self.size_range,
            'has_plus_sizes': self.has_plus_sizes,
            'has_petite_sizes': self.has_petite_sizes,
            'has_tall_sizes': self.has_tall_sizes,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'pattern_type': self.pattern_type,
            'gender': self.gender,
            'age_group': self.age_group,
            'base_price': self.base_price,
            'price_variance': self.price_variance,
            'cost_price': self.cost_price,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ApparelVariant(FeatureAwareModel, db.Model):
    """Size and color variants for apparel products"""
    __tablename__ = 'apparel_variants'
    
    # Feature requirements
    required_features = ['FEATURE_SIZE_VARIANTS', 'FEATURE_COLOR_VARIANTS']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    apparel_product_id = db.Column(db.Integer, db.ForeignKey('apparel_products.id'), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    
    # Variant attributes
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    color_code = db.Column(db.String(7), nullable=True)  # Hex color code
    upc = db.Column(db.String(20), unique=True, nullable=True)
    ean = db.Column(db.String(20), unique=True, nullable=True)
    
    # Inventory and pricing
    stock = db.Column(db.Integer, default=0)
    price_adjustment = db.Column(db.Float, default=0.0)  # Price difference from base
    cost_adjustment = db.Column(db.Float, default=0.0)  # Cost difference from base
    weight = db.Column(db.Float, nullable=True)  # Additional weight for shipping
    
    # Physical measurements (for footwear)
    length = db.Column(db.Float, nullable=True)  # For shoes
    width = db.Column(db.String(10), nullable=True)  # Narrow, Medium, Wide, etc.
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_discontinued = db.Column(db.Boolean, default=False)
    discontinued_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    inventory_transactions = db.relationship('ApparelInventoryTransaction', backref='variant', lazy=True)
    exchange_items = db.relationship('ApparelExchangeItem', backref='variant', lazy=True)
    
    def __init__(self, apparel_product_id: int, sku: str, size: str, color: str, **kwargs):
        self.apparel_product_id = apparel_product_id
        self.sku = sku
        self.size = size
        self.color = color
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock"""
        return self.stock > 0 and self.is_active and not self.is_discontinued
    
    @property
    def is_low_stock(self, threshold: int = 5) -> bool:
        """Check if variant has low stock"""
        return self.stock <= threshold and self.stock > 0
    
    @property
    def full_sku(self) -> str:
        """Generate full SKU with variant codes"""
        return f"{self.apparel_product.sku_base}-{self.size}-{self.color}"
    
    def adjust_stock(self, quantity: int, reason: str = 'Adjustment') -> bool:
        """Adjust stock quantity"""
        try:
            old_stock = self.stock
            self.stock += quantity
            self.updated_at = datetime.utcnow()
            
            # Record inventory transaction
            transaction = ApparelInventoryTransaction(
                variant_id=self.id,
                quantity=quantity,
                old_stock=old_stock,
                new_stock=self.stock,
                reason=reason,
                tenant_id=self.tenant_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary"""
        return {
            'id': self.id,
            'apparel_product_id': self.apparel_product_id,
            'sku': self.sku,
            'full_sku': self.full_sku,
            'size': self.size,
            'color': self.color,
            'color_code': self.color_code,
            'upc': self.upc,
            'ean': self.ean,
            'stock': self.stock,
            'price_adjustment': self.price_adjustment,
            'cost_adjustment': self.cost_adjustment,
            'weight': self.weight,
            'length': self.length,
            'width': self.width,
            'is_active': self.is_active,
            'is_discontinued': self.is_discontinued,
            'discontinued_at': self.discontinued_at.isoformat() if self.discontinued_at else None,
            'is_in_stock': self.is_in_stock,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ApparelSizeMatrix(FeatureAwareModel, db.Model):
    """Size matrix for apparel products with conversion charts"""
    __tablename__ = 'apparel_size_matrix'
    
    # Feature requirements
    required_features = ['FEATURE_SIZE_MATRIX']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    apparel_product_id = db.Column(db.Integer, db.ForeignKey('apparel_products.id'), nullable=False)
    size_system = db.Column(db.String(20), nullable=False)  # US, EU, UK, etc.
    size_name = db.Column(db.String(20), nullable=False)  # S, M, L, XL, etc.
    
    # Measurements
    chest_measurement = db.Column(db.Float, nullable=True)  # For shirts
    waist_measurement = db.Column(db.Float, nullable=True)  # For pants
    hip_measurement = db.Column(db.Float, nullable=True)  # For pants/skirts
    inseam_measurement = db.Column(db.Float, nullable=True)  # For pants
    sleeve_length = db.Column(db.Float, nullable=True)  # For shirts
    
    # Footwear specific
    foot_length_cm = db.Column(db.Float, nullable=True)  # For shoes
    foot_width = db.Column(db.String(10), nullable=True)  # N, M, W, etc.
    
    # Display order
    display_order = db.Column(db.Integer, default=0)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, apparel_product_id: int, size_system: str, size_name: str, **kwargs):
        self.apparel_product_id = apparel_product_id
        self.size_system = size_system
        self.size_name = size_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert size matrix entry to dictionary"""
        return {
            'id': self.id,
            'apparel_product_id': self.apparel_product_id,
            'size_system': self.size_system,
            'size_name': self.size_name,
            'chest_measurement': self.chest_measurement,
            'waist_measurement': self.waist_measurement,
            'hip_measurement': self.hip_measurement,
            'inseam_measurement': self.inseam_measurement,
            'sleeve_length': self.sleeve_length,
            'foot_length_cm': self.foot_length_cm,
            'foot_width': self.foot_width,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ApparelExchange(FeatureAwareModel, db.Model):
    """Exchange tracking for apparel items"""
    __tablename__ = 'apparel_exchanges'
    
    # Feature requirements
    required_features = ['FEATURE_EXCHANGE_MANAGEMENT']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    exchange_code = db.Column(db.String(20), unique=True, nullable=False)
    apparel_product_id = db.Column(db.Integer, db.ForeignKey('apparel_products.id'), nullable=False)
    original_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Exchange details
    exchange_reason = db.Column(db.String(100), nullable=False)
    exchange_type = db.Column(db.String(50), default='Size')  # Size, Color, Defect, Style
    original_size = db.Column(db.String(20), nullable=True)
    original_color = db.Column(db.String(50), nullable=True)
    new_size = db.Column(db.String(20), nullable=True)
    new_color = db.Column(db.String(50), nullable=True)
    
    # Status and timing
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Completed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Financial
    price_difference = db.Column(db.Float, default=0.0)  # Additional amount to pay/refund
    refund_amount = db.Column(db.Float, default=0.0)
    store_credit = db.Column(db.Boolean, default=False)
    
    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    staff_notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_by = db.Column(db.String(36), nullable=True)
    approved_by = db.Column(db.String(36), nullable=True)
    
    # Relationships
    items = db.relationship('ApparelExchangeItem', backref='exchange', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, exchange_code: str, apparel_product_id: int, original_order_id: int, 
                 customer_id: int, exchange_reason: str, **kwargs):
        self.exchange_code = exchange_code
        self.apparel_product_id = apparel_product_id
        self.original_order_id = original_order_id
        self.customer_id = customer_id
        self.exchange_reason = exchange_reason
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_expired(self) -> bool:
        """Check if exchange has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until exchange expires"""
        if not self.expires_at:
            return -1
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    def approve(self, user_id: Optional[str] = None) -> bool:
        """Approve exchange"""
        try:
            self.status = 'Approved'
            self.approved_at = datetime.utcnow()
            self.approved_by = user_id
            
            # Set expiry date (e.g., 30 days from approval)
            self.expires_at = datetime.utcnow() + timedelta(days=30)
            
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def complete(self, new_size: Optional[str] = None, new_color: Optional[str] = None) -> bool:
        """Complete exchange"""
        try:
            self.status = 'Completed'
            self.completed_at = datetime.utcnow()
            
            if new_size:
                self.new_size = new_size
            if new_color:
                self.new_color = new_color
            
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exchange to dictionary"""
        return {
            'id': self.id,
            'exchange_code': self.exchange_code,
            'apparel_product_id': self.apparel_product_id,
            'original_order_id': self.original_order_id,
            'customer_id': self.customer_id,
            'exchange_reason': self.exchange_reason,
            'exchange_type': self.exchange_type,
            'original_size': self.original_size,
            'original_color': self.original_color,
            'new_size': self.new_size,
            'new_color': self.new_color,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'days_until_expiry': self.days_until_expiry,
            'price_difference': self.price_difference,
            'refund_amount': self.refund_amount,
            'store_credit': self.store_credit,
            'customer_notes': self.customer_notes,
            'staff_notes': self.staff_notes,
            'created_by': self.created_by,
            'approved_by': self.approved_by
        }


class ApparelExchangeItem(FeatureAwareModel, db.Model):
    """Individual items in an apparel exchange"""
    __tablename__ = 'apparel_exchange_items'
    
    # Feature requirements
    required_features = ['FEATURE_EXCHANGE_MANAGEMENT']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey('apparel_exchanges.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('apparel_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Condition assessment
    original_condition = db.Column(db.String(50), nullable=True)  # New, Like New, Good, Fair
    returned_condition = db.Column(db.String(50), nullable=True)
    condition_notes = db.Column(db.Text, nullable=True)
    
    # Alteration details
    requires_alteration = db.Column(db.Boolean, default=False)
    alteration_type = db.Column(db.String(100), nullable=True)
    alteration_cost = db.Column(db.Float, default=0.0)
    alteration_notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, exchange_id: int, variant_id: int, quantity: int = 1, **kwargs):
        self.exchange_id = exchange_id
        self.variant_id = variant_id
        self.quantity = quantity
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exchange item to dictionary"""
        return {
            'id': self.id,
            'exchange_id': self.exchange_id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'original_condition': self.original_condition,
            'returned_condition': self.returned_condition,
            'condition_notes': self.condition_notes,
            'requires_alteration': self.requires_alteration,
            'alteration_type': self.alteration_type,
            'alteration_cost': self.alteration_cost,
            'alteration_notes': self.alteration_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ApparelInventoryTransaction(FeatureAwareModel, db.Model):
    """Inventory transactions for apparel variants"""
    __tablename__ = 'apparel_inventory_transactions'
    
    # Feature requirements
    required_features = ['FEATURE_STOCK_TRACKING']
    retail_types = ['apparel', 'footwear']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('apparel_variants.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Positive for in, negative for out
    old_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(50), nullable=False)  # Sale, Purchase, Adjustment, Return, Transfer
    reference_id = db.Column(db.String(50), nullable=True)  # Order ID, Purchase Order ID, etc.
    reason = db.Column(db.String(100), nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    def __init__(self, variant_id: int, quantity: int, old_stock: int, new_stock: int, **kwargs):
        self.variant_id = variant_id
        self.quantity = quantity
        self.old_stock = old_stock
        self.new_stock = new_stock
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'variant_id': self.variant_id,
            'quantity': self.quantity,
            'old_stock': self.old_stock,
            'new_stock': self.new_stock,
            'transaction_type': self.transaction_type,
            'reference_id': self.reference_id,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }