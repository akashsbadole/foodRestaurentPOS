from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class BatchLot(FeatureAwareModel):
    """Batch/lot tracking model for inventory management"""
    __tablename__ = 'batch_lots'
    
    # Feature requirements
    required_features = ['FEATURE_BATCH_TRACKING']
    
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False, index=True)
    lot_number = db.Column(db.String(50), nullable=True, index=True)
    
    # Product information
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Quantity and tracking
    initial_quantity = db.Column(db.Integer, nullable=False)
    current_quantity = db.Column(db.Integer, nullable=False)
    allocated_quantity = db.Column(db.Integer, default=0)  # Quantity allocated for orders
    
    # Dates
    manufacturing_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    received_date = db.Column(db.Date, nullable=False)
    
    # Cost information
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)
    total_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Supplier information
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    
    # Quality and testing
    quality_status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Quarantine
    tested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tested_at = db.Column(db.DateTime, nullable=True)
    test_notes = db.Column(db.Text, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)  # Warehouse location
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Exhausted, Expired, Recalled
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='batch_lots')
    variant = db.relationship('ProductVariant', backref='batch_lots')
    supplier = db.relationship('Supplier', backref='batch_lots')
    purchase_order = db.relationship('PurchaseOrder', backref='batch_lots')
    tester = db.relationship('User', backref='tested_batches')
    creator = db.relationship('User', backref='created_batches')
    serial_numbers = db.relationship('SerialNumber', backref='batch_lot', lazy=True)
    
    def __init__(self, batch_number, product_id, initial_quantity, received_date,
                 lot_number=None, variant_id=None, unit_cost=None, total_cost=None,
                 supplier_id=None, purchase_order_id=None, manufacturing_date=None,
                 expiry_date=None, quality_status='Pending', notes=None,
                 location=None, tenant_id=None, created_by=None):
        self.batch_number = batch_number
        self.lot_number = lot_number
        self.product_id = product_id
        self.variant_id = variant_id
        self.initial_quantity = initial_quantity
        self.current_quantity = initial_quantity
        self.received_date = received_date
        self.unit_cost = Decimal(str(unit_cost)) if unit_cost else None
        self.total_cost = Decimal(str(total_cost)) if total_cost else None
        self.supplier_id = supplier_id
        self.purchase_order_id = purchase_order_id
        self.manufacturing_date = manufacturing_date
        self.expiry_date = expiry_date
        self.quality_status = quality_status
        self.notes = notes
        self.location = location
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def available_quantity(self):
        """Get available quantity (current - allocated)"""
        return self.current_quantity - self.allocated_quantity
    
    @property
    def is_expired(self):
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date
    
    @property
    def is_near_expiry(self, days=30):
        """Check if batch is near expiry"""
        if not self.expiry_date:
            return False
        from datetime import timedelta
        near_expiry_date = date.today() + timedelta(days=days)
        return self.expiry_date <= near_expiry_date
    
    @property
    def is_exhausted(self):
        """Check if batch is exhausted"""
        return self.current_quantity <= 0
    
    @property
    def days_to_expiry(self):
        """Get days until expiry"""
        if not self.expiry_date:
            return None
        delta = self.expiry_date - date.today()
        return delta.days
    
    def allocate_quantity(self, quantity):
        """Allocate quantity for an order"""
        if quantity > self.available_quantity:
            return False, "Insufficient available quantity"
        
        self.allocated_quantity += quantity
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Quantity allocated successfully"
    
    def release_allocation(self, quantity):
        """Release allocated quantity"""
        if quantity > self.allocated_quantity:
            return False, "Cannot release more than allocated"
        
        self.allocated_quantity -= quantity
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Allocation released successfully"
    
    def consume_quantity(self, quantity):
        """Consume quantity from batch"""
        if quantity > self.current_quantity:
            return False, "Insufficient quantity"
        
        # Reduce current and allocated quantities
        actual_consumed = min(quantity, self.allocated_quantity)
        self.allocated_quantity -= actual_consumed
        self.current_quantity -= quantity
        
        # Update status if exhausted
        if self.current_quantity <= 0:
            self.status = 'Exhausted'
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Quantity consumed successfully"
    
    def approve_quality(self, user_id, notes=None):
        """Approve batch quality"""
        self.quality_status = 'Approved'
        self.tested_by = user_id
        self.tested_at = datetime.utcnow()
        if notes:
            self.test_notes = notes
        db.session.commit()
    
    def reject_quality(self, user_id, notes=None):
        """Reject batch quality"""
        self.quality_status = 'Rejected'
        self.tested_by = user_id
        self.tested_at = datetime.utcnow()
        if notes:
            self.test_notes = notes
        db.session.commit()
    
    def to_dict(self):
        """Convert batch/lot to dictionary"""
        return {
            'id': self.id,
            'batch_number': self.batch_number,
            'lot_number': self.lot_number,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'initial_quantity': self.initial_quantity,
            'current_quantity': self.current_quantity,
            'allocated_quantity': self.allocated_quantity,
            'available_quantity': self.available_quantity,
            'manufacturing_date': self.manufacturing_date.isoformat() if self.manufacturing_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'purchase_order_id': self.purchase_order_id,
            'quality_status': self.quality_status,
            'tested_by': self.tested_by,
            'tested_by_name': self.tester.username if self.tester else None,
            'tested_at': self.tested_at.isoformat() if self.tested_at else None,
            'test_notes': self.test_notes,
            'notes': self.notes,
            'location': self.location,
            'status': self.status,
            'is_expired': self.is_expired,
            'is_near_expiry': self.is_near_expiry(),
            'is_exhausted': self.is_exhausted,
            'days_to_expiry': self.days_to_expiry,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_by_batch_number(batch_number, tenant_id=None):
        """Get batch by batch number"""
        query = BatchLot.query.filter_by(batch_number=batch_number)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_expiring_batches(days=30, tenant_id=None):
        """Get batches expiring within specified days"""
        from datetime import timedelta
        expiry_date = date.today() + timedelta(days=days)
        
        query = BatchLot.query.filter(
            BatchLot.expiry_date.isnot(None),
            BatchLot.expiry_date <= expiry_date,
            BatchLot.current_quantity > 0,
            BatchLot.status == 'Active'
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(BatchLot.expiry_date).all()
    
    @staticmethod
    def get_active_batches(tenant_id=None):
        """Get all active batches"""
        query = BatchLot.query.filter_by(status='Active')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(BatchLot.received_date.desc()).all()
    
    def __repr__(self):
        return f'<BatchLot {self.batch_number} ({self.current_quantity}/{self.initial_quantity})>'


class SerialNumber(FeatureAwareModel):
    """Serial number tracking model for individual item tracking"""
    __tablename__ = 'serial_numbers'
    
    # Feature requirements
    required_features = ['FEATURE_SERIAL_NUMBER_TRACKING']
    
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Product information
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    batch_lot_id = db.Column(db.Integer, db.ForeignKey('batch_lots.id'), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='In Stock')  # In Stock, Allocated, Sold, Returned, Damaged, Warranty
    
    # Cost and pricing
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)
    selling_price = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Warranty information
    warranty_start_date = db.Column(db.Date, nullable=True)
    warranty_end_date = db.Column(db.Date, nullable=True)
    warranty_type = db.Column(db.String(50), nullable=True)  # Manufacturer, Extended, None
    
    # Sale information
    sale_date = db.Column(db.Date, nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    
    # Return information
    return_date = db.Column(db.Date, nullable=True)
    return_reason = db.Column(db.String(100), nullable=True)
    return_order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='serial_numbers')
    variant = db.relationship('ProductVariant', backref='serial_numbers')
    order = db.relationship('Order', backref='serial_numbers', foreign_keys=[order_id])
    customer = db.relationship('Customer', backref='serial_numbers')
    return_order = db.relationship('Order', backref='returned_serial_numbers', foreign_keys=[return_order_id])
    creator = db.relationship('User', backref='created_serial_numbers')
    
    def __init__(self, serial_number, product_id, cost_price=None, selling_price=None,
                 variant_id=None, batch_lot_id=None, warranty_start_date=None,
                 warranty_end_date=None, warranty_type=None, notes=None,
                 location=None, tenant_id=None, created_by=None):
        self.serial_number = serial_number
        self.product_id = product_id
        self.variant_id = variant_id
        self.batch_lot_id = batch_lot_id
        self.cost_price = Decimal(str(cost_price)) if cost_price else None
        self.selling_price = Decimal(str(selling_price)) if selling_price else None
        self.warranty_start_date = warranty_start_date
        self.warranty_end_date = warranty_end_date
        self.warranty_type = warranty_type
        self.notes = notes
        self.location = location
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_in_stock(self):
        """Check if serial number is in stock"""
        return self.status == 'In Stock'
    
    @property
    def is_allocated(self):
        """Check if serial number is allocated"""
        return self.status == 'Allocated'
    
    @property
    def is_sold(self):
        """Check if serial number is sold"""
        return self.status == 'Sold'
    
    @property
    def is_returned(self):
        """Check if serial number is returned"""
        return self.status == 'Returned'
    
    @property
    def is_damaged(self):
        """Check if serial number is damaged"""
        return self.status == 'Damaged'
    
    @property
    def is_under_warranty(self):
        """Check if item is under warranty"""
        if not self.warranty_end_date:
            return False
        return date.today() <= self.warranty_end_date
    
    @property
    def warranty_days_remaining(self):
        """Get days remaining in warranty"""
        if not self.warranty_end_date:
            return None
        delta = self.warranty_end_date - date.today()
        return max(0, delta.days)
    
    def allocate(self):
        """Allocate serial number for sale"""
        if self.status != 'In Stock':
            return False, "Serial number is not in stock"
        
        self.status = 'Allocated'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Serial number allocated successfully"
    
    def sell(self, order_id, customer_id, sale_date=None):
        """Mark serial number as sold"""
        if self.status != 'Allocated':
            return False, "Serial number is not allocated"
        
        self.status = 'Sold'
        self.order_id = order_id
        self.customer_id = customer_id
        self.sale_date = sale_date or date.today()
        
        # Start warranty if not already set
        if not self.warranty_start_date:
            self.warranty_start_date = self.sale_date
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Serial number sold successfully"
    
    def return_item(self, return_reason, return_order_id=None, return_date=None):
        """Return serial number"""
        if self.status != 'Sold':
            return False, "Serial number is not sold"
        
        self.status = 'Returned'
        self.return_reason = return_reason
        self.return_order_id = return_order_id
        self.return_date = return_date or date.today()
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Serial number returned successfully"
    
    def mark_damaged(self, notes=None):
        """Mark serial number as damaged"""
        self.status = 'Damaged'
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Serial number marked as damaged"
    
    def restock(self):
        """Restock returned serial number"""
        if self.status != 'Returned':
            return False, "Serial number is not returned"
        
        self.status = 'In Stock'
        self.return_reason = None
        self.return_order_id = None
        self.return_date = None
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Serial number restocked successfully"
    
    def to_dict(self):
        """Convert serial number to dictionary"""
        return {
            'id': self.id,
            'serial_number': self.serial_number,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'batch_lot_id': self.batch_lot_id,
            'batch_number': self.batch_lot.batch_number if self.batch_lot else None,
            'status': self.status,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'selling_price': float(self.selling_price) if self.selling_price else None,
            'warranty_start_date': self.warranty_start_date.isoformat() if self.warranty_start_date else None,
            'warranty_end_date': self.warranty_end_date.isoformat() if self.warranty_end_date else None,
            'warranty_type': self.warranty_type,
            'is_under_warranty': self.is_under_warranty,
            'warranty_days_remaining': self.warranty_days_remaining,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'order_id': self.order_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'return_date': self.return_date.isoformat() if self.return_date else None,
            'return_reason': self.return_reason,
            'return_order_id': self.return_order_id,
            'notes': self.notes,
            'location': self.location,
            'is_in_stock': self.is_in_stock,
            'is_allocated': self.is_allocated,
            'is_sold': self.is_sold,
            'is_returned': self.is_returned,
            'is_damaged': self.is_damaged,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_by_serial_number(serial_number, tenant_id=None):
        """Get serial number by serial number"""
        query = SerialNumber.query.filter_by(serial_number=serial_number)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_in_stock(tenant_id=None):
        """Get all serial numbers in stock"""
        query = SerialNumber.query.filter_by(status='In Stock')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SerialNumber.created_at.desc()).all()
    
    @staticmethod
    def get_sold(tenant_id=None):
        """Get all sold serial numbers"""
        query = SerialNumber.query.filter_by(status='Sold')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SerialNumber.sale_date.desc()).all()
    
    @staticmethod
    def get_warranty_expiring(days=30, tenant_id=None):
        """Get serial numbers with warranty expiring soon"""
        from datetime import timedelta
        expiry_date = date.today() + timedelta(days=days)
        
        query = SerialNumber.query.filter(
            SerialNumber.warranty_end_date.isnot(None),
            SerialNumber.warranty_end_date <= expiry_date,
            SerialNumber.status == 'Sold'
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SerialNumber.warranty_end_date).all()
    
    def __repr__(self):
        return f'<SerialNumber {self.serial_number} ({self.status})>'