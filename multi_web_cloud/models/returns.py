from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class SalesReturn(FeatureAwareModel):
    """Sales return model for handling product returns"""
    __tablename__ = 'sales_returns'
    
    # Feature requirements
    required_features = ['FEATURE_SALES_RETURN']
    
    id = db.Column(db.Integer, primary_key=True)
    return_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    original_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    
    # Return details
    return_date = db.Column(db.Date, nullable=False, default=date.today)
    return_reason = db.Column(db.String(100), nullable=False)
    return_type = db.Column(db.String(20), default='Refund')  # Refund, Exchange, Store Credit
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Processed
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    
    # Financial information
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    refund_amount = db.Column(db.Numeric(12, 2), default=0)
    restocking_fee = db.Column(db.Numeric(10, 2), default=0)
    tax_adjustment = db.Column(db.Numeric(10, 2), default=0)
    
    # Resolution
    resolution_notes = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional information
    customer_notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    original_order = db.relationship('Order', backref='sales_returns')
    customer = db.relationship('Customer', backref='sales_returns')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_returns')
    processor = db.relationship('User', foreign_keys=[processed_by], backref='processed_returns')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_returns')
    items = db.relationship('ReturnItem', backref='sales_return', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, original_order_id, return_number=None, return_date=None,
                 return_reason=None, return_type='Refund', customer_id=None,
                 status='Pending', priority='Normal', total_amount=0,
                 refund_amount=0, restocking_fee=0, tax_adjustment=0,
                 customer_notes=None, internal_notes=None, tenant_id=None, created_by=None):
        self.original_order_id = original_order_id
        self.return_number = return_number or self.generate_return_number()
        self.return_date = return_date or date.today()
        self.return_reason = return_reason
        self.return_type = return_type
        self.customer_id = customer_id
        self.status = status
        self.priority = priority
        self.total_amount = Decimal(str(total_amount))
        self.refund_amount = Decimal(str(refund_amount))
        self.restocking_fee = Decimal(str(restocking_fee))
        self.tax_adjustment = Decimal(str(tax_adjustment))
        self.customer_notes = customer_notes
        self.internal_notes = internal_notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_return_number():
        """Generate unique return number"""
        prefix = "RTN"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_pending(self):
        """Check if return is pending"""
        return self.status == 'Pending'
    
    @property
    def is_approved(self):
        """Check if return is approved"""
        return self.status == 'Approved'
    
    @property
    def is_rejected(self):
        """Check if return is rejected"""
        return self.status == 'Rejected'
    
    @property
    def is_processed(self):
        """Check if return is processed"""
        return self.status == 'Processed'
    
    @property
    def net_refund_amount(self):
        """Get net refund amount after fees"""
        return self.refund_amount - self.restocking_fee
    
    def approve(self, approver_id, refund_amount=None, restocking_fee=0, tax_adjustment=0, notes=None):
        """Approve sales return"""
        if self.status != 'Pending':
            return False, "Only pending returns can be approved"
        
        self.status = 'Approved'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        
        if refund_amount is not None:
            self.refund_amount = Decimal(str(refund_amount))
        self.restocking_fee = Decimal(str(restocking_fee))
        self.tax_adjustment = Decimal(str(tax_adjustment))
        
        if notes:
            self.resolution_notes = notes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Return approved successfully"
    
    def reject(self, approver_id, rejection_reason):
        """Reject sales return"""
        if self.status != 'Pending':
            return False, "Only pending returns can be rejected"
        
        self.status = 'Rejected'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.resolution_notes = rejection_reason
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Return rejected successfully"
    
    def process(self, processor_id, notes=None):
        """Process approved return"""
        if self.status != 'Approved':
            return False, "Only approved returns can be processed"
        
        self.status = 'Processed'
        self.processed_by = processor_id
        self.processed_at = datetime.utcnow()
        
        if notes:
            self.resolution_notes = notes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Return processed successfully"
    
    def calculate_totals(self):
        """Calculate return totals from items"""
        self.total_amount = sum(item.total_amount for item in self.items)
        self.refund_amount = sum(item.refund_amount for item in self.items)
        self.restocking_fee = sum(item.restocking_fee for item in self.items)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_items=True):
        """Convert sales return to dictionary"""
        data = {
            'id': self.id,
            'return_number': self.return_number,
            'original_order_id': self.original_order_id,
            'original_order_number': self.original_order.order_number if self.original_order else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'return_reason': self.return_reason,
            'return_type': self.return_type,
            'status': self.status,
            'priority': self.priority,
            'total_amount': float(self.total_amount),
            'refund_amount': float(self.refund_amount),
            'restocking_fee': float(self.restocking_fee),
            'tax_adjustment': float(self.tax_adjustment),
            'net_refund_amount': float(self.net_refund_amount),
            'resolution_notes': self.resolution_notes,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'processed_by': self.processed_by,
            'processed_by_name': self.processor.username if self.processor else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'customer_notes': self.customer_notes,
            'internal_notes': self.internal_notes,
            'attachments': self.attachments,
            'is_pending': self.is_pending,
            'is_approved': self.is_approved,
            'is_rejected': self.is_rejected,
            'is_processed': self.is_processed,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    @staticmethod
    def get_by_status(status, tenant_id=None):
        """Get returns by status"""
        query = SalesReturn.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SalesReturn.created_at.desc()).all()
    
    @staticmethod
    def get_pending_returns(tenant_id=None):
        """Get pending returns"""
        query = SalesReturn.query.filter_by(status='Pending')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SalesReturn.priority.desc(), SalesReturn.created_at).all()
    
    def __repr__(self):
        return f'<SalesReturn {self.return_number} ({self.status})>'


class ReturnItem(db.Model):
    """Return item model for individual items in a return"""
    __tablename__ = 'return_items'
    
    id = db.Column(db.Integer, primary_key=True)
    sales_return_id = db.Column(db.Integer, db.ForeignKey('sales_returns.id'), nullable=False)
    original_order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Return details
    quantity_returned = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Condition assessment
    condition = db.Column(db.String(20), default='Good')  # New, Good, Fair, Poor, Damaged
    condition_notes = db.Column(db.Text, nullable=True)
    
    # Resolution
    resolution = db.Column(db.String(20), default='Refund')  # Refund, Exchange, Repair, Discard
    exchange_item_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)  # For exchanges
    exchange_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Financial calculation
    refund_percentage = db.Column(db.Numeric(5, 2), default=100)  # Percentage of price to refund
    refund_amount = db.Column(db.Numeric(12, 2), default=0)
    restocking_fee = db.Column(db.Numeric(10, 2), default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sales_return = db.relationship('SalesReturn', backref='return_items')
    original_order_item = db.relationship('OrderItem', backref='return_items')
    product = db.relationship('Product', backref='return_items')
    variant = db.relationship('ProductVariant', backref='return_items')
    exchange_item = db.relationship('Product', foreign_keys=[exchange_item_id], backref='exchange_returns')
    exchange_variant = db.relationship('ProductVariant', foreign_keys=[exchange_variant_id], backref='exchange_returns')
    
    def __init__(self, sales_return_id, product_id, quantity_returned, unit_price,
                 original_order_item_id=None, variant_id=None, condition='Good',
                 condition_notes=None, resolution='Refund', exchange_item_id=None,
                 exchange_variant_id=None, refund_percentage=100, notes=None,
                 tenant_id=None):
        self.sales_return_id = sales_return_id
        self.original_order_item_id = original_order_item_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.quantity_returned = quantity_returned
        self.unit_price = Decimal(str(unit_price))
        self.total_amount = self.unit_price * quantity_returned
        self.condition = condition
        self.condition_notes = condition_notes
        self.resolution = resolution
        self.exchange_item_id = exchange_item_id
        self.exchange_variant_id = exchange_variant_id
        self.refund_percentage = Decimal(str(refund_percentage))
        self.notes = notes
        self.tenant_id = tenant_id
        
        # Calculate refund amount
        self.refund_amount = (self.total_amount * self.refund_percentage) / Decimal('100')
    
    @property
    def net_refund_amount(self):
        """Get net refund amount after restocking fee"""
        return self.refund_amount - self.restocking_fee
    
    @property
    def is_exchange(self):
        """Check if item is for exchange"""
        return self.resolution == 'Exchange'
    
    @property
    def is_refund(self):
        """Check if item is for refund"""
        return self.resolution == 'Refund'
    
    def calculate_amounts(self):
        """Calculate financial amounts"""
        self.total_amount = self.unit_price * self.quantity_returned
        self.refund_amount = (self.total_amount * self.refund_percentage) / Decimal('100')
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert return item to dictionary"""
        return {
            'id': self.id,
            'sales_return_id': self.sales_return_id,
            'return_number': self.sales_return.return_number if self.sales_return else None,
            'original_order_item_id': self.original_order_item_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'quantity_returned': self.quantity_returned,
            'unit_price': float(self.unit_price),
            'total_amount': float(self.total_amount),
            'condition': self.condition,
            'condition_notes': self.condition_notes,
            'resolution': self.resolution,
            'exchange_item_id': self.exchange_item_id,
            'exchange_item_name': self.exchange_item.name if self.exchange_item else None,
            'exchange_variant_id': self.exchange_variant_id,
            'exchange_variant_name': self.exchange_variant.variant_name if self.exchange_variant else None,
            'refund_percentage': float(self.refund_percentage),
            'refund_amount': float(self.refund_amount),
            'restocking_fee': float(self.restocking_fee),
            'net_refund_amount': float(self.net_refund_amount),
            'notes': self.notes,
            'is_exchange': self.is_exchange,
            'is_refund': self.is_refund,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ReturnItem {self.product.name if self.product else "Unknown"}: {self.quantity_returned}>'


class ProductExchange(FeatureAwareModel):
    """Product exchange model for handling exchanges"""
    __tablename__ = 'product_exchanges'
    
    # Feature requirements
    required_features = ['FEATURE_EXCHANGE']
    
    id = db.Column(db.Integer, primary_key=True)
    exchange_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    original_return_id = db.Column(db.Integer, db.ForeignKey('sales_returns.id'), nullable=False)
    new_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Exchange details
    exchange_date = db.Column(db.Date, nullable=False, default=date.today)
    exchange_type = db.Column(db.String(20), default='Direct')  # Direct, With Payment, Store Credit
    
    # Price difference
    price_difference = db.Column(db.Numeric(12, 2), default=0)  # Positive = customer pays, Negative = store pays
    price_difference_reason = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Completed, Cancelled
    
    # Resolution
    resolution_notes = db.Column(db.Text, nullable=True)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    original_return = db.relationship('SalesReturn', backref='exchanges')
    new_order = db.relationship('Order', backref='exchange_origin')
    completer = db.relationship('User', backref='completed_exchanges')
    creator = db.relationship('User', backref='created_exchanges')
    exchange_items = db.relationship('ExchangeItem', backref='product_exchange', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, original_return_id, exchange_number=None, exchange_date=None,
                 exchange_type='Direct', price_difference=0, price_difference_reason=None,
                 status='Pending', notes=None, attachments=None, tenant_id=None, created_by=None):
        self.original_return_id = original_return_id
        self.exchange_number = exchange_number or self.generate_exchange_number()
        self.exchange_date = exchange_date or date.today()
        self.exchange_type = exchange_type
        self.price_difference = Decimal(str(price_difference))
        self.price_difference_reason = price_difference_reason
        self.status = status
        self.notes = notes
        self.attachments = attachments
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_exchange_number():
        """Generate unique exchange number"""
        prefix = "EXC"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_pending(self):
        """Check if exchange is pending"""
        return self.status == 'Pending'
    
    @property
    def is_approved(self):
        """Check if exchange is approved"""
        return self.status == 'Approved'
    
    @property
    def is_completed(self):
        """Check if exchange is completed"""
        return self.status == 'Completed'
    
    @property
    def is_cancelled(self):
        """Check if exchange is cancelled"""
        return self.status == 'Cancelled'
    
    @property
    def customer_pays_difference(self):
        """Check if customer pays price difference"""
        return self.price_difference > 0
    
    @property
    def store_pays_difference(self):
        """Check if store pays price difference"""
        return self.price_difference < 0
    
    def approve(self):
        """Approve product exchange"""
        if self.status != 'Pending':
            return False, "Only pending exchanges can be approved"
        
        self.status = 'Approved'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Exchange approved successfully"
    
    def complete(self, completer_id, new_order_id=None, notes=None):
        """Complete product exchange"""
        if self.status != 'Approved':
            return False, "Only approved exchanges can be completed"
        
        self.status = 'Completed'
        self.completed_by = completer_id
        self.completed_at = datetime.utcnow()
        
        if new_order_id:
            self.new_order_id = new_order_id
        
        if notes:
            self.resolution_notes = notes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Exchange completed successfully"
    
    def cancel(self, notes=None):
        """Cancel product exchange"""
        if self.status in ['Completed', 'Cancelled']:
            return False, "Cannot cancel completed or cancelled exchange"
        
        self.status = 'Cancelled'
        if notes:
            self.resolution_notes = notes
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Exchange cancelled successfully"
    
    def to_dict(self, include_items=True):
        """Convert product exchange to dictionary"""
        data = {
            'id': self.id,
            'exchange_number': self.exchange_number,
            'original_return_id': self.original_return_id,
            'original_return_number': self.original_return.return_number if self.original_return else None,
            'new_order_id': self.new_order_id,
            'new_order_number': self.new_order.order_number if self.new_order else None,
            'exchange_date': self.exchange_date.isoformat() if self.exchange_date else None,
            'exchange_type': self.exchange_type,
            'price_difference': float(self.price_difference),
            'price_difference_reason': self.price_difference_reason,
            'customer_pays_difference': self.customer_pays_difference,
            'store_pays_difference': self.store_pays_difference,
            'status': self.status,
            'resolution_notes': self.resolution_notes,
            'completed_by': self.completed_by,
            'completed_by_name': self.completer.username if self.completer else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'notes': self.notes,
            'attachments': self.attachments,
            'is_pending': self.is_pending,
            'is_approved': self.is_approved,
            'is_completed': self.is_completed,
            'is_cancelled': self.is_cancelled,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
        
        if include_items:
            data['exchange_items'] = [item.to_dict() for item in self.exchange_items]
        
        return data
    
    @staticmethod
    def get_by_status(status, tenant_id=None):
        """Get exchanges by status"""
        query = ProductExchange.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductExchange.created_at.desc()).all()
    
    @staticmethod
    def get_pending_exchanges(tenant_id=None):
        """Get pending exchanges"""
        query = ProductExchange.query.filter_by(status='Pending')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductExchange.created_at).all()
    
    def __repr__(self):
        return f'<ProductExchange {self.exchange_number} ({self.status})>'


class ExchangeItem(db.Model):
    """Exchange item model for individual items in an exchange"""
    __tablename__ = 'exchange_items'
    
    id = db.Column(db.Integer, primary_key=True)
    product_exchange_id = db.Column(db.Integer, db.ForeignKey('product_exchanges.id'), nullable=False)
    
    # Original item (being returned)
    original_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    original_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    original_quantity = db.Column(db.Integer, nullable=False)
    
    # New item (being exchanged for)
    new_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    new_variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    new_quantity = db.Column(db.Integer, nullable=False)
    
    # Price information
    original_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    new_unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    price_difference = db.Column(db.Numeric(12, 2), default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product_exchange = db.relationship('ProductExchange', backref='exchange_items')
    original_product = db.relationship('Product', foreign_keys=[original_product_id], backref='original_exchanges')
    original_variant = db.relationship('ProductVariant', foreign_keys=[original_variant_id], backref='original_exchanges')
    new_product = db.relationship('Product', foreign_keys=[new_product_id], backref='new_exchanges')
    new_variant = db.relationship('ProductVariant', foreign_keys=[new_variant_id], backref='new_exchanges')
    
    def __init__(self, product_exchange_id, original_product_id, new_product_id,
                 original_quantity, new_quantity, original_unit_price, new_unit_price,
                 original_variant_id=None, new_variant_id=None, notes=None, tenant_id=None):
        self.product_exchange_id = product_exchange_id
        self.original_product_id = original_product_id
        self.new_product_id = new_product_id
        self.original_quantity = original_quantity
        self.new_quantity = new_quantity
        self.original_unit_price = Decimal(str(original_unit_price))
        self.new_unit_price = Decimal(str(new_unit_price))
        self.original_variant_id = original_variant_id
        self.new_variant_id = new_variant_id
        self.notes = notes
        self.tenant_id = tenant_id
        
        # Calculate price difference
        self.price_difference = (self.new_unit_price * new_quantity) - (self.original_unit_price * original_quantity)
    
    @property
    def original_total(self):
        """Get total value of original items"""
        return self.original_unit_price * self.original_quantity
    
    @property
    def new_total(self):
        """Get total value of new items"""
        return self.new_unit_price * self.new_quantity
    
    @property
    def customer_pays_difference(self):
        """Check if customer pays price difference"""
        return self.price_difference > 0
    
    @property
    def store_pays_difference(self):
        """Check if store pays price difference"""
        return self.price_difference < 0
    
    def to_dict(self):
        """Convert exchange item to dictionary"""
        return {
            'id': self.id,
            'product_exchange_id': self.product_exchange_id,
            'exchange_number': self.product_exchange.exchange_number if self.product_exchange else None,
            'original_product_id': self.original_product_id,
            'original_product_name': self.original_product.name if self.original_product else None,
            'original_product_sku': self.original_product.sku if self.original_product else None,
            'original_variant_id': self.original_variant_id,
            'original_variant_name': self.original_variant.variant_name if self.original_variant else None,
            'original_quantity': self.original_quantity,
            'original_unit_price': float(self.original_unit_price),
            'original_total': float(self.original_total),
            'new_product_id': self.new_product_id,
            'new_product_name': self.new_product.name if self.new_product else None,
            'new_product_sku': self.new_product.sku if self.new_product else None,
            'new_variant_id': self.new_variant_id,
            'new_variant_name': self.new_variant.variant_name if self.new_variant else None,
            'new_quantity': self.new_quantity,
            'new_unit_price': float(self.new_unit_price),
            'new_total': float(self.new_total),
            'price_difference': float(self.price_difference),
            'customer_pays_difference': self.customer_pays_difference,
            'store_pays_difference': self.store_pays_difference,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ExchangeItem {self.original_product.name if self.original_product else "Unknown"} -> {self.new_product.name if self.new_product else "Unknown"}>'