"""
Books & Office Supplies specific models with feature-aware capabilities
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from . import db
from .feature_aware_model import FeatureAwareModel


class BookProduct(FeatureAwareModel, db.Model):
    """Enhanced product model for books"""
    __tablename__ = 'book_products'
    
    # Feature requirements
    required_features = ['FEATURE_ISBN_TRACKING']
    optional_features = ['FEATURE_AUTHOR_PUBLISHER_DB', 'FEATURE_BOOK_CATEGORIES', 'FEATURE_SPECIAL_ORDERS', 'FEATURE_TEXTBOOK_BUYBACK']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    sku_base = db.Column(db.String(50), nullable=False)  # Base SKU without variant codes
    
    # Book specific attributes
    book_type = db.Column(db.String(50), nullable=True)  # Fiction, Non-Fiction, Textbook, Reference, etc.
    genre = db.Column(db.String(100), nullable=True)
    subgenre = db.Column(db.String(100), nullable=True)
    series = db.Column(db.String(100), nullable=True)  # Book series name
    series_number = db.Column(db.Integer, nullable=True)  # Number in series
    
    # Author and publisher information
    primary_author = db.Column(db.String(100), nullable=True)
    additional_authors = db.Column(db.Text, nullable=True)  # JSON array of additional authors
    publisher = db.Column(db.String(100), nullable=True)
    imprint = db.Column(db.String(100), nullable=True)  # Publisher imprint
    publication_date = db.Column(db.Date, nullable=True)
    edition = db.Column(db.String(50), nullable=True)  # 1st, 2nd, Revised, etc.
    language = db.Column(db.String(50), nullable=True)
    
    # Physical attributes
    format_type = db.Column(db.String(50), nullable=True)  # Hardcover, Paperback, Ebook, Audiobook
    page_count = db.Column(db.Integer, nullable=True)
    dimensions = db.Column(db.String(100), nullable=True)  # "8.5 x 11" etc.
    weight_oz = db.Column(db.Float, nullable=True)  # Weight in ounces
    cover_type = db.Column(db.String(50), nullable=True)  # Dust Jacket, Paperback, etc.
    
    # ISBN and identifiers
    isbn_10 = db.Column(db.String(10), unique=True, nullable=True)  # ISBN-10
    isbn_13 = db.Column(db.String(13), unique=True, nullable=True)  # ISBN-13
    upc = db.Column(db.String(20), unique=True, nullable=True)
    ean = db.Column(db.String(20), unique=True, nullable=True)
    doi = db.Column(db.String(100), unique=True, nullable=True)  # Digital Object Identifier
    
    # Academic/Educational
    grade_level = db.Column(db.String(50), nullable=True)  # K-12, College, etc.
    subject_area = db.Column(db.String(100), nullable=True)  # Math, Science, etc.
    curriculum_standard = db.Column(db.String(100), nullable=True)  # Common Core, etc.
    
    # Pricing and inventory
    list_price = db.Column(db.Float, nullable=False)  # Manufacturer suggested retail price
    wholesale_price = db.Column(db.Float, nullable=True)
    cost_price = db.Column(db.Float, nullable=True)
    
    # Special flags
    is_bestseller = db.Column(db.Boolean, default=False)
    is_new_release = db.Column(db.Boolean, default=False)
    is_backordered = db.Column(db.Boolean, default=False)
    is_out_of_print = db.Column(db.Boolean, default=False)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    # Relationships
    variants = db.relationship('BookVariant', backref='book_product', lazy=True, cascade='all, delete-orphan')
    author = db.relationship('BookAuthor', backref='books', lazy=True)
    publisher_info = db.relationship('BookPublisher', backref='books', lazy=True)
    categories = db.relationship('BookCategory', backref='books', lazy=True)
    special_orders = db.relationship('BookSpecialOrder', backref='book_product', lazy=True)
    buyback_records = db.relationship('TextbookBuyback', backref='book_product', lazy=True)
    
    def __init__(self, product_id: int, sku_base: str, list_price: float, **kwargs):
        self.product_id = product_id
        self.sku_base = sku_base
        self.list_price = list_price
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_textbook(self) -> bool:
        """Check if this is a textbook"""
        return self.book_type in ['Textbook', 'Educational', 'Reference']
    
    @property
    def full_title(self) -> str:
        """Get full title including series"""
        if self.series and self.series_number:
            return f"{self.product.name if hasattr(self, 'product') else ''} ({self.series} #{self.series_number})"
        return self.product.name if hasattr(self, 'product') else ''
    
    @property
    def is_available(self) -> bool:
        """Check if book is available for order"""
        return (self.is_active and 
                not self.is_out_of_print and 
                not self.is_backordered)
    
    def get_variants_by_format(self, format_type: str) -> List['BookVariant']:
        """Get variants by format type"""
        return [v for v in self.variants if v.format_type == format_type and v.is_active]
    
    def get_current_price(self) -> float:
        """Get current effective price"""
        # Use list price as default, could be overridden by promotions
        return self.list_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert book product to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'sku_base': self.sku_base,
            'book_type': self.book_type,
            'genre': self.genre,
            'subgenre': self.subgenre,
            'series': self.series,
            'series_number': self.series_number,
            'primary_author': self.primary_author,
            'additional_authors': self.additional_authors,
            'publisher': self.publisher,
            'imprint': self.imprint,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'edition': self.edition,
            'language': self.language,
            'format_type': self.format_type,
            'page_count': self.page_count,
            'dimensions': self.dimensions,
            'weight_oz': self.weight_oz,
            'cover_type': self.cover_type,
            'isbn_10': self.isbn_10,
            'isbn_13': self.isbn_13,
            'upc': self.upc,
            'ean': self.ean,
            'doi': self.doi,
            'grade_level': self.grade_level,
            'subject_area': self.subject_area,
            'curriculum_standard': self.curriculum_standard,
            'list_price': self.list_price,
            'wholesale_price': self.wholesale_price,
            'cost_price': self.cost_price,
            'is_bestseller': self.is_bestseller,
            'is_new_release': self.is_new_release,
            'is_backordered': self.is_backordered,
            'is_out_of_print': self.is_out_of_print,
            'is_available': self.is_available,
            'is_textbook': self.is_textbook,
            'full_title': self.full_title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BookVariant(FeatureAwareModel, db.Model):
    """Format and condition variants for book products"""
    __tablename__ = 'book_variants'
    
    # Feature requirements
    required_features = ['FEATURE_ISBN_TRACKING']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    book_product_id = db.Column(db.Integer, db.ForeignKey('book_products.id'), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=False)
    
    # Variant attributes
    format_type = db.Column(db.String(50), nullable=False)  # Hardcover, Paperback, Ebook, Audiobook
    condition = db.Column(db.String(50), nullable=True)  # New, Like New, Good, Acceptable
    binding = db.Column(db.String(50), nullable=True)  # Paperback, Hardcover, Spiral, etc.
    
    # Inventory and pricing
    stock = db.Column(db.Integer, default=0)
    price_adjustment = db.Column(db.Float, default=0.0)  # Price difference from base
    cost_adjustment = db.Column(db.Float, default=0.0)  # Cost difference from base
    
    # Digital specific
    file_format = db.Column(db.String(20), nullable=True)  # PDF, EPUB, MOBI, MP3
    file_size_mb = db.Column(db.Float, nullable=True)
    drm_type = db.Column(db.String(50), nullable=True)  # None, Adobe DRM, etc.
    download_limit_days = db.Column(db.Integer, nullable=True)
    
    # Physical specific
    weight_oz = db.Column(db.Float, nullable=True)  # Additional weight for shipping
    requires_shipping = db.Column(db.Boolean, default=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_discontinued = db.Column(db.Boolean, default=False)
    discontinued_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, book_product_id: int, sku: str, format_type: str, **kwargs):
        self.book_product_id = book_product_id
        self.sku = sku
        self.format_type = format_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock"""
        return self.stock > 0 and self.is_active and not self.is_discontinued
    
    @property
    def is_digital(self) -> bool:
        """Check if this is a digital variant"""
        return self.format_type in ['Ebook', 'Audiobook', 'Digital']
    
    @property
    def is_physical(self) -> bool:
        """Check if this is a physical variant"""
        return not self.is_digital
    
    @property
    def full_sku(self) -> str:
        """Generate full SKU with variant codes"""
        return f"{self.book_product.sku_base}-{self.format_type}"
    
    def get_effective_price(self) -> float:
        """Get effective price including adjustments"""
        base_price = self.book_product.list_price if self.book_product else 0.0
        return base_price + self.price_adjustment
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variant to dictionary"""
        return {
            'id': self.id,
            'book_product_id': self.book_product_id,
            'sku': self.sku,
            'full_sku': self.full_sku,
            'format_type': self.format_type,
            'condition': self.condition,
            'binding': self.binding,
            'stock': self.stock,
            'price_adjustment': self.price_adjustment,
            'cost_adjustment': self.cost_adjustment,
            'effective_price': self.get_effective_price(),
            'file_format': self.file_format,
            'file_size_mb': self.file_size_mb,
            'drm_type': self.drm_type,
            'download_limit_days': self.download_limit_days,
            'weight_oz': self.weight_oz,
            'requires_shipping': self.requires_shipping,
            'is_active': self.is_active,
            'is_discontinued': self.is_discontinued,
            'discontinued_at': self.discontinued_at.isoformat() if self.discontinued_at else None,
            'is_in_stock': self.is_in_stock,
            'is_digital': self.is_digital,
            'is_physical': self.is_physical,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BookAuthor(FeatureAwareModel, db.Model):
    """Author information for books"""
    __tablename__ = 'book_authors'
    
    # Feature requirements
    required_features = ['FEATURE_AUTHOR_PUBLISHER_DB']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    bio = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    
    # Author details
    birth_date = db.Column(db.Date, nullable=True)
    nationality = db.Column(db.String(50), nullable=True)
    literary_genre = db.Column(db.String(100), nullable=True)
    awards = db.Column(db.Text, nullable=True)  # JSON array of awards
    
    # Social media
    twitter_handle = db.Column(db.String(50), nullable=True)
    instagram_handle = db.Column(db.String(50), nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert author to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'bio': self.bio,
            'photo_url': self.photo_url,
            'website_url': self.website_url,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'nationality': self.nationality,
            'literary_genre': self.literary_genre,
            'awards': self.awards,
            'twitter_handle': self.twitter_handle,
            'instagram_handle': self.instagram_handle,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BookPublisher(FeatureAwareModel, db.Model):
    """Publisher information for books"""
    __tablename__ = 'book_publishers'
    
    # Feature requirements
    required_features = ['FEATURE_AUTHOR_PUBLISHER_DB']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    imprint = db.Column(db.String(100), nullable=True)  # Publisher imprint
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    
    # Publisher details
    founded_year = db.Column(db.Integer, nullable=True)
    location = db.Column(db.String(200), nullable=True)  # City, State, Country
    distribution = db.Column(db.String(200), nullable=True)  # Distribution channels
    specialties = db.Column(db.Text, nullable=True)  # JSON array of specialties
    
    # Contact information
    contact_email = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert publisher to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'imprint': self.imprint,
            'description': self.description,
            'logo_url': self.logo_url,
            'website_url': self.website_url,
            'founded_year': self.founded_year,
            'location': self.location,
            'distribution': self.distribution,
            'specialties': self.specialties,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class BookCategory(FeatureAwareModel, db.Model):
    """Book categorization system"""
    __tablename__ = 'book_categories'
    
    # Feature requirements
    required_features = ['FEATURE_BOOK_CATEGORIES']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)  # Category code
    parent_id = db.Column(db.Integer, db.ForeignKey('book_categories.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Category hierarchy
    level = db.Column(db.Integer, default=1)  # 1=Main, 2=Sub, 3=Sub-sub
    sort_order = db.Column(db.Integer, default=0)
    
    # Category attributes
    age_group = db.Column(db.String(50), nullable=True)  # Children, YA, Adult, etc.
    target_audience = db.Column(db.String(100), nullable=True)
    educational_level = db.Column(db.String(50), nullable=True)  # Elementary, Middle School, etc.
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('BookCategory', remote_side=[id], backref='children')
    books = db.relationship('BookProduct', secondary='book_product_categories', backref='categories')
    
    def __init__(self, name: str, code: str, **kwargs):
        self.name = name
        self.code = code
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_subcategories(self) -> List['BookCategory']:
        """Get direct subcategories"""
        return [cat for cat in self.children if cat.is_active]
    
    def get_all_descendants(self) -> List['BookCategory']:
        """Get all descendant categories"""
        descendants = []
        for child in self.children:
            if child.is_active:
                descendants.append(child)
                descendants.extend(child.get_all_descendants())
        return descendants
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert category to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'parent_id': self.parent_id,
            'description': self.description,
            'level': self.level,
            'sort_order': self.sort_order,
            'age_group': self.age_group,
            'target_audience': self.target_audience,
            'educational_level': self.educational_level,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class BookSpecialOrder(FeatureAwareModel, db.Model):
    """Special orders for books"""
    __tablename__ = 'book_special_orders'
    
    # Feature requirements
    required_features = ['FEATURE_SPECIAL_ORDERS']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    book_product_id = db.Column(db.Integer, db.ForeignKey('book_products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Order details
    quantity = db.Column(db.Integer, nullable=False)
    format_preference = db.Column(db.String(50), nullable=True)  # Preferred format
    special_instructions = db.Column(db.Text, nullable=True)
    urgency = db.Column(db.String(20), default='Normal')  # Normal, Rush, etc.
    
    # Pricing
    quoted_price = db.Column(db.Float, nullable=False)
    deposit_required = db.Column(db.Boolean, default=False)
    deposit_amount = db.Column(db.Float, default=0.0)
    final_price = db.Column(db.Float, nullable=True)
    
    # Status and timing
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Ordered, Received, Cancelled
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    confirmed_at = db.Column(db.DateTime, nullable=True)
    ordered_at = db.Column(db.DateTime, nullable=True)
    expected_at = db.Column(db.DateTime, nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
    
    # Communication
    customer_notified = db.Column(db.Boolean, default=False)
    notification_method = db.Column(db.String(50), nullable=True)  # Email, Phone, SMS
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_by = db.Column(db.String(36), nullable=True)
    updated_by = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, order_number: str, book_product_id: int, customer_id: int, **kwargs):
        self.order_number = order_number
        self.book_product_id = book_product_id
        self.customer_id = customer_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_pending(self) -> bool:
        """Check if order is pending"""
        return self.status == 'Pending'
    
    @property
    def is_confirmed(self) -> bool:
        """Check if order is confirmed"""
        return self.status == 'Confirmed'
    
    @property
    def days_pending(self) -> int:
        """Get days order has been pending"""
        if not self.requested_at:
            return 0
        delta = datetime.utcnow() - self.requested_at
        return delta.days
    
    def confirm(self, user_id: Optional[str] = None) -> bool:
        """Confirm special order"""
        try:
            self.status = 'Confirmed'
            self.confirmed_at = datetime.utcnow()
            self.updated_by = user_id
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert special order to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'book_product_id': self.book_product_id,
            'customer_id': self.customer_id,
            'quantity': self.quantity,
            'format_preference': self.format_preference,
            'special_instructions': self.special_instructions,
            'urgency': self.urgency,
            'quoted_price': self.quoted_price,
            'deposit_required': self.deposit_required,
            'deposit_amount': self.deposit_amount,
            'final_price': self.final_price,
            'status': self.status,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'ordered_at': self.ordered_at.isoformat() if self.ordered_at else None,
            'expected_at': self.expected_at.isoformat() if self.expected_at else None,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'customer_notified': self.customer_notified,
            'notification_method': self.notification_method,
            'is_pending': self.is_pending,
            'is_confirmed': self.is_confirmed,
            'days_pending': self.days_pending,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TextbookBuyback(FeatureAwareModel, db.Model):
    """Textbook buyback program"""
    __tablename__ = 'textbook_buybacks'
    
    # Feature requirements
    required_features = ['FEATURE_TEXTBOOK_BUYBACK']
    retail_types = ['books', 'office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    buyback_code = db.Column(db.String(20), unique=True, nullable=False)
    book_product_id = db.Column(db.Integer, db.ForeignKey('book_products.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Buyback details
    original_purchase_date = db.Column(db.Date, nullable=True)
    original_purchase_price = db.Column(db.Float, nullable=True)
    original_receipt_number = db.Column(db.String(50), nullable=True)
    
    # Condition assessment
    condition = db.Column(db.String(50), nullable=False)  # New, Like New, Good, Fair, Poor
    condition_notes = db.Column(db.Text, nullable=True)
    missing_items = db.Column(db.Text, nullable=True)  # What's missing from the book
    damage_description = db.Column(db.Text, nullable=True)
    
    # Buyback pricing
    quoted_buyback_price = db.Column(db.Float, nullable=False)
    final_buyback_price = db.Column(db.Float, nullable=True)
    store_credit_amount = db.Column(db.Float, default=0.0)
    cash_payout_amount = db.Column(db.Float, default=0.0)
    
    # Status and timing
    status = db.Column(db.String(20), default='Pending')  # Pending, Inspected, Approved, Rejected, Paid
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    inspected_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    inspected_by = db.Column(db.String(36), nullable=True)
    approved_by = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, buyback_code: str, book_product_id: int, customer_id: int, **kwargs):
        self.buyback_code = buyback_code
        self.book_product_id = book_product_id
        self.customer_id = customer_id
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_pending(self) -> bool:
        """Check if buyback is pending"""
        return self.status == 'Pending'
    
    @property
    def total_payout(self) -> float:
        """Get total payout amount"""
        return self.store_credit_amount + self.cash_payout_amount
    
    def approve(self, final_price: float, store_credit: float, cash_payout: float,
                user_id: Optional[str] = None) -> bool:
        """Approve buyback"""
        try:
            self.status = 'Approved'
            self.final_buyback_price = final_price
            self.store_credit_amount = store_credit
            self.cash_payout_amount = cash_payout
            self.approved_at = datetime.utcnow()
            self.approved_by = user_id
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert buyback to dictionary"""
        return {
            'id': self.id,
            'buyback_code': self.buyback_code,
            'book_product_id': self.book_product_id,
            'customer_id': self.customer_id,
            'original_purchase_date': self.original_purchase_date.isoformat() if self.original_purchase_date else None,
            'original_purchase_price': self.original_purchase_price,
            'original_receipt_number': self.original_receipt_number,
            'condition': self.condition,
            'condition_notes': self.condition_notes,
            'missing_items': self.missing_items,
            'damage_description': self.damage_description,
            'quoted_buyback_price': self.quoted_buyback_price,
            'final_buyback_price': self.final_buyback_price,
            'store_credit_amount': self.store_credit_amount,
            'cash_payout_amount': self.cash_payout_amount,
            'total_payout': self.total_payout,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'inspected_at': self.inspected_at.isoformat() if self.inspected_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'is_pending': self.is_pending,
            'inspected_by': self.inspected_by,
            'approved_by': self.approved_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Association table for many-to-many relationship between books and categories
book_product_categories = db.Table('book_product_categories',
    db.Column('book_product_id', db.Integer, db.ForeignKey('book_products.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('book_categories.id'), primary_key=True)
)


class OfficeSupplyProduct(FeatureAwareModel, db.Model):
    """Enhanced product model for office supplies"""
    __tablename__ = 'office_supply_products'
    
    # Feature requirements
    required_features = ['FEATURE_OFFICE_SUPPLY_MANAGEMENT']
    optional_features = ['FEATURE_BULK_ORDERING', 'FEATURE_RECURRING_ORDERS']
    retail_types = ['office_supplies']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    sku_base = db.Column(db.String(50), nullable=False)
    
    # Office supply specific attributes
    supply_type = db.Column(db.String(50), nullable=True)  # Writing, Paper, Desk, Technology, etc.
    subcategory = db.Column(db.String(100), nullable=True)
    brand_line = db.Column(db.String(100), nullable=True)  # Product line within brand
    
    # Technical specifications
    specifications = db.Column(db.Text, nullable=True)  # JSON object of technical specs
    compatibility = db.Column(db.Text, nullable=True)  # Compatibility information
    warranty_months = db.Column(db.Integer, nullable=True)
    
    # Usage and capacity
    typical_use = db.Column(db.String(200), nullable=True)  # Office, School, Home, etc.
    capacity_units = db.Column(db.String(50), nullable=True)  # Sheets, Pages, etc.
    capacity_quantity = db.Column(db.Float, nullable=True)  # 500, 1000, etc.
    
    # Environmental and safety
    eco_friendly = db.Column(db.Boolean, default=False)
    recyclable = db.Column(db.Boolean, default=False)
    safety_certifications = db.Column(db.Text, nullable=True)  # JSON array of certifications
    
    # Ordering and inventory
    min_order_quantity = db.Column(db.Integer, default=1)
    order_multiples = db.Column(db.Integer, default=1)  # Must order in multiples of
    bulk_pricing_tiers = db.Column(db.Text, nullable=True)  # JSON array of bulk pricing
    
    # Pricing
    unit_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=True)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    def __init__(self, product_id: int, sku_base: str, unit_price: float, **kwargs):
        self.product_id = product_id
        self.sku_base = sku_base
        self.unit_price = unit_price
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_available(self) -> bool:
        """Check if supply is available"""
        return self.is_active
    
    def get_bulk_price(self, quantity: int) -> float:
        """Get price for bulk order"""
        if not self.bulk_pricing_tiers:
            return self.unit_price * quantity
        
        # Parse bulk pricing tiers
        import json
        try:
            tiers = json.loads(self.bulk_pricing_tiers)
            applicable_price = self.unit_price
            
            for tier in sorted(tiers, key=lambda x: x['min_quantity']):
                if quantity >= tier['min_quantity']:
                    applicable_price = tier['unit_price']
            
            return applicable_price * quantity
        except (json.JSONDecodeError, KeyError):
            return self.unit_price * quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert office supply to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'sku_base': self.sku_base,
            'supply_type': self.supply_type,
            'subcategory': self.subcategory,
            'brand_line': self.brand_line,
            'specifications': self.specifications,
            'compatibility': self.compatibility,
            'warranty_months': self.warranty_months,
            'typical_use': self.typical_use,
            'capacity_units': self.capacity_units,
            'capacity_quantity': self.capacity_quantity,
            'min_order_quantity': self.min_order_quantity,
            'order_multiples': self.order_multiples,
            'bulk_pricing_tiers': self.bulk_pricing_tiers,
            'unit_price': self.unit_price,
            'cost_price': self.cost_price,
            'eco_friendly': self.eco_friendly,
            'recyclable': self.recyclable,
            'safety_certifications': self.safety_certifications,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }