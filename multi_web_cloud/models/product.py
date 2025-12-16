from datetime import datetime
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class ProductCategory(db.Model):
    """Product category model for organizing products"""
    __tablename__ = 'product_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True)
    image_path = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('ProductCategory', remote_side=[id], backref='children')
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __init__(self, name, description=None, parent_id=None, image_path=None, 
                 sort_order=0, tenant_id=None):
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.image_path = image_path
        self.sort_order = sort_order
        self.tenant_id = tenant_id
    
    def get_product_count(self):
        """Get count of products in this category (including subcategories)"""
        from .product import Product
        category_ids = [self.id] + [child.id for child in self.children]
        return Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.is_active == True
        ).count()
    
    def get_active_products(self):
        """Get all active products in this category"""
        return [p for p in self.products if p.is_active]
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'image_path': self.image_path,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'product_count': self.get_product_count(),
            'children': [child.to_dict() for child in self.children] if self.children else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_root_categories(tenant_id=None):
        """Get root level categories (no parent)"""
        query = ProductCategory.query.filter_by(parent_id=None, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductCategory.sort_order, ProductCategory.name).all()
    
    @staticmethod
    def get_all_active(tenant_id=None):
        """Get all active categories"""
        query = ProductCategory.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductCategory.sort_order, ProductCategory.name).all()
    
    def __repr__(self):
        return f'<ProductCategory {self.name}>'


class Product(db.Model):
    """Generic product model for all retail types"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sku = db.Column(db.String(100), unique=True, nullable=True, index=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    
    # Pricing
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    selling_price = db.Column(db.Numeric(10, 2), nullable=True)
    mrp = db.Column(db.Numeric(10, 2), nullable=True)  # Maximum Retail Price
    
    # Product classification
    product_type = db.Column(db.String(50), default='standard')  # standard, service, bundle, digital
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=False)
    brand = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    
    # Inventory
    track_inventory = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    max_stock_level = db.Column(db.Integer, nullable=True)
    reorder_point = db.Column(db.Integer, nullable=True)
    reorder_quantity = db.Column(db.Integer, nullable=True)
    
    # Physical attributes
    weight = db.Column(db.Numeric(8, 3), nullable=True)  # in kg
    dimensions = db.Column(db.String(50), nullable=True)  # LxWxH format
    unit_of_measure = db.Column(db.String(20), default='pcs')  # pcs, kg, ltr, mtr
    
    # Status and flags
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    is_taxable = db.Column(db.Boolean, default=True)
    is_discountable = db.Column(db.Boolean, default=True)
    is_returnable = db.Column(db.Boolean, default=True)
    
    # Tax and compliance
    hsn_code = db.Column(db.String(10), nullable=True)  # HSN/SAC code for GST
    tax_rate_id = db.Column(db.Integer, db.ForeignKey('tax_rates.id'), nullable=True)
    
    # Media
    image_path = db.Column(db.String(255), nullable=True)
    additional_images = db.Column(db.Text, nullable=True)  # JSON array of image paths
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    tax_rate = db.relationship('TaxRate', backref='products')
    creator = db.relationship('User', backref='created_products')
    variants = db.relationship('ProductVariant', backref='product', lazy=True, cascade='all, delete-orphan')
    attributes = db.relationship('ProductAttribute', backref='product', lazy=True, cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', backref='product', lazy=True)
    
    def __init__(self, name, base_price, category_id, description=None, sku=None, barcode=None,
                 cost_price=None, selling_price=None, mrp=None, product_type='standard',
                 brand=None, manufacturer=None, track_inventory=True, stock_quantity=0,
                 min_stock_level=10, max_stock_level=None, reorder_point=None, reorder_quantity=None,
                 weight=None, dimensions=None, unit_of_measure='pcs', is_active=True,
                 is_available=True, is_taxable=True, is_discountable=True, is_returnable=True,
                 hsn_code=None, tax_rate_id=None, image_path=None, additional_images=None,
                 tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.sku = sku
        self.barcode = barcode
        self.base_price = Decimal(str(base_price))
        self.cost_price = Decimal(str(cost_price)) if cost_price else None
        self.selling_price = Decimal(str(selling_price)) if selling_price else None
        self.mrp = Decimal(str(mrp)) if mrp else None
        self.product_type = product_type
        self.category_id = category_id
        self.brand = brand
        self.manufacturer = manufacturer
        self.track_inventory = track_inventory
        self.stock_quantity = stock_quantity
        self.min_stock_level = min_stock_level
        self.max_stock_level = max_stock_level
        self.reorder_point = reorder_point
        self.reorder_quantity = reorder_quantity
        self.weight = weight
        self.dimensions = dimensions
        self.unit_of_measure = unit_of_measure
        self.is_active = is_active
        self.is_available = is_available
        self.is_taxable = is_taxable
        self.is_discountable = is_discountable
        self.is_returnable = is_returnable
        self.hsn_code = hsn_code
        self.tax_rate_id = tax_rate_id
        self.image_path = image_path
        self.additional_images = additional_images
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def current_price(self):
        """Get current selling price or base price"""
        return self.selling_price or self.base_price
    
    @property
    def formatted_price(self):
        """Get formatted current price"""
        return f"₹{self.current_price:.2f}"
    
    @property
    def formatted_base_price(self):
        """Get formatted base price"""
        return f"₹{self.base_price:.2f}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if not self.cost_price or self.cost_price == 0:
            return 0
        return float(((self.current_price - self.cost_price) / self.cost_price) * 100)
    
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    def is_low_stock(self):
        """Check if product has low stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.min_stock_level and self.stock_quantity > 0
    
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity == 0
    
    def needs_reorder(self):
        """Check if product needs to be reordered"""
        if not self.track_inventory or not self.reorder_point:
            return False
        return self.stock_quantity <= self.reorder_point
    
    def update_stock(self, quantity_change, transaction_type='adjustment', reference_id=None, notes=None):
        """Update stock quantity and create inventory transaction"""
        from .inventory import InventoryTransaction
        
        old_quantity = self.stock_quantity
        new_quantity = old_quantity + quantity_change
        
        if new_quantity < 0:
            return False, "Insufficient stock"
        
        # Update stock
        self.stock_quantity = new_quantity
        self.updated_at = datetime.utcnow()
        
        # Create inventory transaction
        transaction = InventoryTransaction(
            product_id=self.id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        
        return True, "Stock updated successfully"
    
    def set_stock(self, new_quantity, transaction_type='adjustment', notes=None):
        """Set stock quantity directly"""
        from .inventory import InventoryTransaction
        
        old_quantity = self.stock_quantity
        quantity_change = new_quantity - old_quantity
        
        if new_quantity < 0:
            return False, "Stock quantity cannot be negative"
        
        # Update stock
        self.stock_quantity = new_quantity
        self.updated_at = datetime.utcnow()
        
        # Create inventory transaction
        transaction = InventoryTransaction(
            product_id=self.id,
            transaction_type=transaction_type,
            quantity_change=quantity_change,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        
        return True, "Stock set successfully"
    
    def get_variants_by_attribute(self, attribute_name):
        """Get variants grouped by attribute value"""
        variants = {}
        for variant in self.variants:
            if variant.is_active:
                attr_value = variant.get_attribute_value(attribute_name)
                if attr_value:
                    if attr_value not in variants:
                        variants[attr_value] = []
                    variants[attr_value].append(variant)
        return variants
    
    def get_lowest_price_variant(self):
        """Get variant with lowest price"""
        active_variants = [v for v in self.variants if v.is_active]
        if not active_variants:
            return None
        return min(active_variants, key=lambda v: v.current_price)
    
    def get_highest_price_variant(self):
        """Get variant with highest price"""
        active_variants = [v for v in self.variants if v.is_active]
        if not active_variants:
            return None
        return max(active_variants, key=lambda v: v.current_price)
    
    def to_dict(self, include_variants=False, include_attributes=False):
        """Convert product to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'sku': self.sku,
            'barcode': self.barcode,
            'base_price': float(self.base_price),
            'formatted_base_price': self.formatted_base_price,
            'current_price': float(self.current_price),
            'formatted_price': self.formatted_price,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'selling_price': float(self.selling_price) if self.selling_price else None,
            'mrp': float(self.mrp) if self.mrp else None,
            'product_type': self.product_type,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'brand': self.brand,
            'manufacturer': self.manufacturer,
            'track_inventory': self.track_inventory,
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'max_stock_level': self.max_stock_level,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'weight': float(self.weight) if self.weight else None,
            'dimensions': self.dimensions,
            'unit_of_measure': self.unit_of_measure,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'is_taxable': self.is_taxable,
            'is_discountable': self.is_discountable,
            'is_returnable': self.is_returnable,
            'hsn_code': self.hsn_code,
            'tax_rate_id': self.tax_rate_id,
            'tax_rate': self.tax_rate.to_dict() if self.tax_rate else None,
            'image_path': self.image_path,
            'additional_images': self.additional_images,
            'profit_margin': self.profit_margin,
            'is_in_stock': self.is_in_stock(),
            'is_low_stock': self.is_low_stock(),
            'is_out_of_stock': self.is_out_of_stock(),
            'needs_reorder': self.needs_reorder(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        if include_variants:
            data['variants'] = [variant.to_dict() for variant in self.variants if variant.is_active]
        
        if include_attributes:
            data['attributes'] = [attr.to_dict() for attr in self.attributes]
        
        return data
    
    @staticmethod
    def get_all_active(search_term="", category_id=None, brand=None, tenant_id=None):
        """Get all active products with optional filters"""
        query = Product.query.filter_by(is_active=True)
        
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        if search_term:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search_term}%'),
                    Product.sku.ilike(f'%{search_term}%'),
                    Product.barcode.ilike(f'%{search_term}%'),
                    Product.description.ilike(f'%{search_term}%')
                )
            )
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if brand:
            query = query.filter_by(brand=brand)
        
        return query.order_by(Product.name).all()
    
    @staticmethod
    def get_by_sku(sku, tenant_id=None):
        """Get product by SKU"""
        query = Product.query.filter_by(sku=sku)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_by_barcode(barcode, tenant_id=None):
        """Get product by barcode"""
        query = Product.query.filter_by(barcode=barcode)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_low_stock_items(tenant_id=None):
        """Get all products with low stock"""
        query = Product.query.filter(
            Product.is_active == True,
            Product.track_inventory == True,
            Product.stock_quantity <= Product.min_stock_level,
            Product.stock_quantity > 0
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_out_of_stock_items(tenant_id=None):
        """Get all out of stock products"""
        query = Product.query.filter(
            Product.is_active == True,
            Product.track_inventory == True,
            Product.stock_quantity == 0
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_reorder_needed_items(tenant_id=None):
        """Get all products that need to be reordered"""
        query = Product.query.filter(
            Product.is_active == True,
            Product.track_inventory == True,
            Product.stock_quantity <= Product.reorder_point,
            Product.reorder_point.isnot(None)
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    def __repr__(self):
        return f'<Product {self.name} (₹{self.current_price})>'


class ProductVariant(db.Model):
    """Product variant model for size, color, and other variations"""
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=True, index=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    
    # Pricing (can override product pricing)
    base_price = db.Column(db.Numeric(10, 2), nullable=True)
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    selling_price = db.Column(db.Numeric(10, 2), nullable=True)
    mrp = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Inventory
    track_inventory = db.Column(db.Boolean, default=True)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    
    # Physical attributes
    weight = db.Column(db.Numeric(8, 3), nullable=True)
    dimensions = db.Column(db.String(50), nullable=True)
    
    # Media
    image_path = db.Column(db.String(255), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_available = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attributes = db.relationship('VariantAttribute', backref='variant', lazy=True, cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', backref='variant', lazy=True)
    
    def __init__(self, product_id, variant_name, sku=None, barcode=None, base_price=None,
                 cost_price=None, selling_price=None, mrp=None, track_inventory=True,
                 stock_quantity=0, min_stock_level=10, weight=None, dimensions=None,
                 image_path=None, is_active=True, is_available=True, tenant_id=None):
        self.product_id = product_id
        self.variant_name = variant_name
        self.sku = sku
        self.barcode = barcode
        self.base_price = Decimal(str(base_price)) if base_price else None
        self.cost_price = Decimal(str(cost_price)) if cost_price else None
        self.selling_price = Decimal(str(selling_price)) if selling_price else None
        self.mrp = Decimal(str(mrp)) if mrp else None
        self.track_inventory = track_inventory
        self.stock_quantity = stock_quantity
        self.min_stock_level = min_stock_level
        self.weight = weight
        self.dimensions = dimensions
        self.image_path = image_path
        self.is_active = is_active
        self.is_available = is_available
        self.tenant_id = tenant_id
    
    @property
    def current_price(self):
        """Get current selling price or base price or product price"""
        if self.selling_price:
            return self.selling_price
        elif self.base_price:
            return self.base_price
        else:
            return self.product.current_price
    
    @property
    def formatted_price(self):
        """Get formatted current price"""
        return f"₹{self.current_price:.2f}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        cost = self.cost_price or self.product.cost_price
        if not cost or cost == 0:
            return 0
        return float(((self.current_price - cost) / cost) * 100)
    
    def is_in_stock(self):
        """Check if variant is in stock"""
        if not self.track_inventory:
            return True
        return self.stock_quantity > 0
    
    def is_low_stock(self):
        """Check if variant has low stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity <= self.min_stock_level and self.stock_quantity > 0
    
    def is_out_of_stock(self):
        """Check if variant is out of stock"""
        if not self.track_inventory:
            return False
        return self.stock_quantity == 0
    
    def get_attribute_value(self, attribute_name):
        """Get attribute value by name"""
        for attr in self.attributes:
            if attr.attribute.name.lower() == attribute_name.lower():
                return attr.value
        return None
    
    def get_all_attributes(self):
        """Get all attributes as dictionary"""
        return {attr.attribute.name: attr.value for attr in self.attributes}
    
    def to_dict(self, include_attributes=True):
        """Convert variant to dictionary"""
        data = {
            'id': self.id,
            'product_id': self.product_id,
            'variant_name': self.variant_name,
            'sku': self.sku,
            'barcode': self.barcode,
            'base_price': float(self.base_price) if self.base_price else None,
            'current_price': float(self.current_price),
            'formatted_price': self.formatted_price,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'selling_price': float(self.selling_price) if self.selling_price else None,
            'mrp': float(self.mrp) if self.mrp else None,
            'track_inventory': self.track_inventory,
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'weight': float(self.weight) if self.weight else None,
            'dimensions': self.dimensions,
            'image_path': self.image_path,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'profit_margin': self.profit_margin,
            'is_in_stock': self.is_in_stock(),
            'is_low_stock': self.is_low_stock(),
            'is_out_of_stock': self.is_out_of_stock(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_attributes:
            data['attributes'] = self.get_all_attributes()
        
        return data
    
    def __repr__(self):
        return f'<ProductVariant {self.variant_name} (₹{self.current_price})>'


class ProductAttribute(db.Model):
    """Product attribute model for custom attributes"""
    __tablename__ = 'product_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attribute = db.relationship('Attribute', backref='product_attributes')
    
    def __init__(self, product_id, attribute_id, value, tenant_id=None):
        self.product_id = product_id
        self.attribute_id = attribute_id
        self.value = value
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert product attribute to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'attribute_id': self.attribute_id,
            'attribute_name': self.attribute.name if self.attribute else None,
            'attribute_type': self.attribute.attribute_type if self.attribute else None,
            'value': self.value,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ProductAttribute {self.attribute.name if self.attribute else "Unknown"}: {self.value}>'


class VariantAttribute(db.Model):
    """Variant attribute model for variant-specific attributes"""
    __tablename__ = 'variant_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=False)
    attribute_id = db.Column(db.Integer, db.ForeignKey('attributes.id'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attribute = db.relationship('Attribute', backref='variant_attributes')
    
    def __init__(self, variant_id, attribute_id, value, tenant_id=None):
        self.variant_id = variant_id
        self.attribute_id = attribute_id
        self.value = value
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert variant attribute to dictionary"""
        return {
            'id': self.id,
            'variant_id': self.variant_id,
            'attribute_id': self.attribute_id,
            'attribute_name': self.attribute.name if self.attribute else None,
            'attribute_type': self.attribute.attribute_type if self.attribute else None,
            'value': self.value,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<VariantAttribute {self.attribute.name if self.attribute else "Unknown"}: {self.value}>'


class Attribute(db.Model):
    """Attribute definition model for custom product attributes"""
    __tablename__ = 'attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    attribute_type = db.Column(db.String(20), default='text')  # text, number, boolean, date, select
    options = db.Column(db.Text, nullable=True)  # JSON array for select type
    is_required = db.Column(db.Boolean, default=False)
    is_filterable = db.Column(db.Boolean, default=False)
    is_searchable = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, display_name, attribute_type='text', options=None,
                 is_required=False, is_filterable=False, is_searchable=True,
                 sort_order=0, is_active=True, tenant_id=None):
        self.name = name
        self.display_name = display_name
        self.attribute_type = attribute_type
        self.options = options
        self.is_required = is_required
        self.is_filterable = is_filterable
        self.is_searchable = is_searchable
        self.sort_order = sort_order
        self.is_active = is_active
        self.tenant_id = tenant_id
    
    def get_options_list(self):
        """Get options as list"""
        if not self.options or self.attribute_type != 'select':
            return []
        import json
        try:
            return json.loads(self.options)
        except:
            return []
    
    def to_dict(self):
        """Convert attribute to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'attribute_type': self.attribute_type,
            'options': self.get_options_list(),
            'is_required': self.is_required,
            'is_filterable': self.is_filterable,
            'is_searchable': self.is_searchable,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_all_active(tenant_id=None):
        """Get all active attributes"""
        query = Attribute.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Attribute.sort_order, Attribute.display_name).all()
    
    def __repr__(self):
        return f'<Attribute {self.display_name} ({self.attribute_type})>'