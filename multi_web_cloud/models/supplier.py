from datetime import datetime, date
from decimal import Decimal
from utils.encryption import get_encryption_manager
from . import db
from .feature_aware_model import FeatureAwareModel

class Supplier(FeatureAwareModel):
    """Supplier model for purchase management"""
    __tablename__ = 'suppliers'
    
    # Feature requirements
    required_features = ['FEATURE_SUPPLIER_MANAGEMENT']
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_code = db.Column(db.String(20), unique=True, nullable=True, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    
    # Contact information
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Address information
    billing_address = db.Column(db.Text, nullable=True)
    shipping_address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Tax and business information
    tax_number = db.Column(db.String(50), nullable=True)  # GST/VAT/TIN
    pan_number = db.Column(db.String(20), nullable=True)  # PAN for Indian businesses
    business_type = db.Column(db.String(50), nullable=True)  # Individual, Partnership, Company, etc.
    
    # Payment information
    payment_terms = db.Column(db.String(100), nullable=True)  # Net 30, Net 60, etc.
    credit_limit = db.Column(db.Numeric(12, 2), nullable=True)
    bank_account_number = db.Column(db.Text, nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    ifsc_code = db.Column(db.String(20), nullable=True)
    
    # Performance metrics
    rating = db.Column(db.Integer, default=0)  # 1-5 rating
    total_orders = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(15, 2), default=0)
    average_delivery_days = db.Column(db.Integer, default=0)
    
    # Status and preferences
    is_active = db.Column(db.Boolean, default=True)
    is_preferred = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy=True)
    products = db.relationship('Product', backref='suppliers', secondary='supplier_products')
    
    def __init__(self, name, supplier_code=None, contact_person=None, phone=None,
                 email=None, website=None, billing_address=None, shipping_address=None,
                 city=None, state=None, postal_code=None, country=None,
                 tax_number=None, pan_number=None, business_type=None,
                 payment_terms=None, credit_limit=None, bank_account_number=None,
                 bank_name=None, ifsc_code=None, rating=0, is_active=True,
                 is_preferred=False, notes=None, tenant_id=None, created_by=None):
        self.name = name
        self.supplier_code = supplier_code
        self.contact_person = contact_person
        self.phone = self._encrypt_phone(phone) if phone else None
        self.email = self._encrypt_email(email) if email else None
        self.website = website
        self.billing_address = billing_address
        self.shipping_address = shipping_address
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.tax_number = tax_number
        self.pan_number = pan_number
        self.business_type = business_type
        self.payment_terms = payment_terms
        self.credit_limit = Decimal(str(credit_limit)) if credit_limit else None
        self.bank_account_number = self._encrypt_bank_account(bank_account_number) if bank_account_number else None
        self.bank_name = bank_name
        self.ifsc_code = ifsc_code
        self.rating = rating
        self.is_active = is_active
        self.is_preferred = is_preferred
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def phone_decrypted(self):
        """Get decrypted phone number"""
        return self._decrypt_phone(self.phone)
    
    @property
    def email_decrypted(self):
        """Get decrypted email address"""
        return self._decrypt_email(self.email)
    
    @property
    def bank_account_number_decrypted(self):
        """Get decrypted bank account number"""
        return self._decrypt_bank_account(self.bank_account_number)
    
    def update_performance_metrics(self, delivery_days, order_amount):
        """Update supplier performance metrics"""
        self.total_orders += 1
        self.total_amount += Decimal(str(order_amount))
        
        # Update average delivery days
        if self.average_delivery_days == 0:
            self.average_delivery_days = delivery_days
        else:
            self.average_delivery_days = (self.average_delivery_days + delivery_days) // 2
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_rating(self, new_rating):
        """Update supplier rating"""
        if 1 <= new_rating <= 5:
            self.rating = new_rating
            self.updated_at = datetime.utcnow()
            db.session.commit()
    
    def to_dict(self, include_financial=False):
        """Convert supplier to dictionary"""
        data = {
            'id': self.id,
            'supplier_code': self.supplier_code,
            'name': self.name,
            'contact_person': self.contact_person,
            'website': self.website,
            'billing_address': self.billing_address,
            'shipping_address': self.shipping_address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'tax_number': self.tax_number,
            'pan_number': self.pan_number,
            'business_type': self.business_type,
            'payment_terms': self.payment_terms,
            'bank_name': self.bank_name,
            'ifsc_code': self.ifsc_code,
            'rating': self.rating,
            'total_orders': self.total_orders,
            'total_amount': float(self.total_amount),
            'average_delivery_days': self.average_delivery_days,
            'is_active': self.is_active,
            'is_preferred': self.is_preferred,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        # Include sensitive financial information only if requested
        if include_financial:
            data.update({
                'phone': self.phone_decrypted,
                'email': self.email_decrypted,
                'credit_limit': float(self.credit_limit) if self.credit_limit else None,
                'bank_account_number': self.bank_account_number_decrypted
            })
        
        return data
    
    def _encrypt_phone(self, phone):
        """Encrypt phone number"""
        if not phone:
            return None
        return get_encryption_manager().encrypt_field(phone)
    
    def _decrypt_phone(self, encrypted_phone):
        """Decrypt phone number"""
        if not encrypted_phone:
            return None
        return get_encryption_manager().decrypt_field(encrypted_phone)
    
    def _encrypt_email(self, email):
        """Encrypt email address"""
        if not email:
            return None
        return get_encryption_manager().encrypt_field(email)
    
    def _decrypt_email(self, encrypted_email):
        """Decrypt email address"""
        if not encrypted_email:
            return None
        return get_encryption_manager().decrypt_field(encrypted_email)
    
    def _encrypt_bank_account(self, account_number):
        """Encrypt bank account number"""
        if not account_number:
            return None
        return get_encryption_manager().encrypt_field(account_number)
    
    def _decrypt_bank_account(self, encrypted_account_number):
        """Decrypt bank account number"""
        if not encrypted_account_number:
            return None
        return get_encryption_manager().decrypt_field(encrypted_account_number)
    
    @staticmethod
    def get_active_suppliers(tenant_id=None):
        """Get all active suppliers"""
        query = Supplier.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Supplier.name).all()
    
    @staticmethod
    def get_preferred_suppliers(tenant_id=None):
        """Get all preferred suppliers"""
        query = Supplier.query.filter_by(is_active=True, is_preferred=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Supplier.name).all()
    
    @staticmethod
    def get_by_code(supplier_code, tenant_id=None):
        """Get supplier by supplier code"""
        query = Supplier.query.filter_by(supplier_code=supplier_code)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<Supplier {self.name}>'


class PurchaseOrder(FeatureAwareModel):
    """Purchase order model for supplier orders"""
    __tablename__ = 'purchase_orders'
    
    # Feature requirements
    required_features = ['FEATURE_PURCHASE_ORDERS']
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    
    # Order information
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    actual_delivery_date = db.Column(db.Date, nullable=True)
    
    # Financial information
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    shipping_charges = db.Column(db.Numeric(10, 2), default=0)
    other_charges = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    
    # Status
    status = db.Column(db.String(20), default='Draft')  # Draft, Sent, Approved, Received, Cancelled
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    
    # Payment information
    payment_status = db.Column(db.String(20), default='Pending')  # Pending, Partial, Paid
    payment_terms = db.Column(db.String(100), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    
    # Delivery information
    shipping_address = db.Column(db.Text, nullable=True)
    delivery_instructions = db.Column(db.Text, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    terms_and_conditions = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Approval information
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    approver = db.relationship('User', backref='approved_purchase_orders')
    creator = db.relationship('User', backref='created_purchase_orders')
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy=True, cascade='all, delete-orphan')
    receipts = db.relationship('PurchaseReceipt', backref='purchase_order', lazy=True)
    
    def __init__(self, supplier_id, order_number=None, order_date=None, expected_delivery_date=None,
                 priority='Normal', payment_terms=None, shipping_address=None,
                 delivery_instructions=None, notes=None, terms_and_conditions=None,
                 tenant_id=None, created_by=None):
        self.order_number = order_number or self.generate_order_number()
        self.supplier_id = supplier_id
        self.order_date = order_date or date.today()
        self.expected_delivery_date = expected_delivery_date
        self.priority = priority
        self.payment_terms = payment_terms
        self.shipping_address = shipping_address
        self.delivery_instructions = delivery_instructions
        self.notes = notes
        self.terms_and_conditions = terms_and_conditions
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_order_number():
        """Generate unique purchase order number"""
        prefix = "PO"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_draft(self):
        """Check if PO is in draft status"""
        return self.status == 'Draft'
    
    @property
    def is_sent(self):
        """Check if PO is sent"""
        return self.status == 'Sent'
    
    @property
    def is_approved(self):
        """Check if PO is approved"""
        return self.status == 'Approved'
    
    @property
    def is_received(self):
        """Check if PO is received"""
        return self.status == 'Received'
    
    @property
    def is_cancelled(self):
        """Check if PO is cancelled"""
        return self.status == 'Cancelled'
    
    def calculate_totals(self):
        """Calculate order totals"""
        self.subtotal = sum(item.total_amount for item in self.items)
        self.tax_amount = sum(item.tax_amount for item in self.items)
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_charges + self.other_charges - self.discount_amount
    
    def approve(self, approver_id):
        """Approve purchase order"""
        if self.status != 'Draft':
            return False, "Only draft orders can be approved"
        
        self.status = 'Approved'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.calculate_totals()
        db.session.commit()
        return True, "Purchase order approved successfully"
    
    def send_to_supplier(self):
        """Mark purchase order as sent to supplier"""
        if self.status not in ['Draft', 'Approved']:
            return False, "Order must be draft or approved to send"
        
        self.status = 'Sent'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Purchase order sent to supplier"
    
    def mark_received(self, actual_delivery_date=None):
        """Mark purchase order as received"""
        if self.status != 'Sent':
            return False, "Order must be sent to mark as received"
        
        self.status = 'Received'
        self.actual_delivery_date = actual_delivery_date or date.today()
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Purchase order marked as received"
    
    def cancel(self):
        """Cancel purchase order"""
        if self.status in ['Received', 'Cancelled']:
            return False, "Cannot cancel received or cancelled order"
        
        self.status = 'Cancelled'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Purchase order cancelled"
    
    def to_dict(self, include_items=True):
        """Convert purchase order to dictionary"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'shipping_charges': float(self.shipping_charges),
            'other_charges': float(self.other_charges),
            'total_amount': float(self.total_amount),
            'status': self.status,
            'priority': self.priority,
            'payment_status': self.payment_status,
            'payment_terms': self.payment_terms,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'shipping_address': self.shipping_address,
            'delivery_instructions': self.delivery_instructions,
            'notes': self.notes,
            'terms_and_conditions': self.terms_and_conditions,
            'attachments': self.attachments,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'is_draft': self.is_draft,
            'is_sent': self.is_sent,
            'is_approved': self.is_approved,
            'is_received': self.is_received,
            'is_cancelled': self.is_cancelled,
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
        """Get purchase orders by status"""
        query = PurchaseOrder.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(PurchaseOrder.created_at.desc()).all()
    
    @staticmethod
    def get_pending_orders(tenant_id=None):
        """Get pending purchase orders"""
        query = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['Draft', 'Sent', 'Approved']))
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(PurchaseOrder.expected_delivery_date).all()
    
    def __repr__(self):
        return f'<PurchaseOrder {self.order_number} ({self.status})>'


class PurchaseOrderItem(db.Model):
    """Purchase order item model for individual items in a purchase order"""
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Quantity and pricing
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    tax_rate = db.Column(db.Numeric(5, 2), default=0)
    
    # Calculated amounts
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='purchase_order_items')
    variant = db.relationship('ProductVariant', backref='purchase_order_items')
    
    def __init__(self, purchase_order_id, product_id, quantity, unit_price,
                 variant_id=None, discount_percentage=0, tax_rate=0, notes=None,
                 tenant_id=None):
        self.purchase_order_id = purchase_order_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.quantity = quantity
        self.unit_price = Decimal(str(unit_price))
        self.discount_percentage = Decimal(str(discount_percentage))
        self.tax_rate = Decimal(str(tax_rate))
        self.notes = notes
        self.tenant_id = tenant_id
        self.calculate_amounts()
    
    def calculate_amounts(self):
        """Calculate line item amounts"""
        self.line_total = self.quantity * self.unit_price
        self.discount_amount = self.line_total * (self.discount_percentage / Decimal('100'))
        self.taxable_amount = self.line_total - self.discount_amount
        self.tax_amount = self.taxable_amount * (self.tax_rate / Decimal('100'))
        self.total_amount = self.taxable_amount + self.tax_amount
    
    def to_dict(self):
        """Convert purchase order item to dictionary"""
        return {
            'id': self.id,
            'purchase_order_id': self.purchase_order_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'discount_percentage': float(self.discount_percentage),
            'tax_rate': float(self.tax_rate),
            'line_total': float(self.line_total),
            'discount_amount': float(self.discount_amount),
            'tax_amount': float(self.tax_amount),
            'total_amount': float(self.total_amount),
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PurchaseOrderItem {self.product.name if self.product else "Unknown"} x{self.quantity}>'


class PurchaseReceipt(db.Model):
    """Purchase receipt model for receiving goods"""
    __tablename__ = 'purchase_receipts'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    
    # Receipt information
    receipt_date = db.Column(db.Date, nullable=False, default=date.today)
    received_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Partial
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    receiver = db.relationship('User', backref='purchase_receipts')
    items = db.relationship('PurchaseReceiptItem', backref='receipt', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, purchase_order_id, receipt_number=None, receipt_date=None,
                 received_by=None, notes=None, tenant_id=None):
        self.receipt_number = receipt_number or self.generate_receipt_number()
        self.purchase_order_id = purchase_order_id
        self.receipt_date = receipt_date or date.today()
        self.received_by = received_by
        self.notes = notes
        self.tenant_id = tenant_id
    
    @staticmethod
    def generate_receipt_number():
        """Generate unique receipt number"""
        prefix = "GRN"  # Goods Receipt Note
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    def to_dict(self, include_items=True):
        """Convert purchase receipt to dictionary"""
        data = {
            'id': self.id,
            'receipt_number': self.receipt_number,
            'purchase_order_id': self.purchase_order_id,
            'purchase_order_number': self.purchase_order.order_number if self.purchase_order else None,
            'receipt_date': self.receipt_date.isoformat() if self.receipt_date else None,
            'received_by': self.received_by,
            'received_by_name': self.receiver.username if self.receiver else None,
            'status': self.status,
            'notes': self.notes,
            'attachments': self.attachments,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    def __repr__(self):
        return f'<PurchaseReceipt {self.receipt_number}>'


class PurchaseReceiptItem(db.Model):
    """Purchase receipt item model for individual received items"""
    __tablename__ = 'purchase_receipt_items'
    
    id = db.Column(db.Integer, primary_key=True)
    receipt_id = db.Column(db.Integer, db.ForeignKey('purchase_receipts.id'), nullable=False)
    purchase_order_item_id = db.Column(db.Integer, db.ForeignKey('purchase_order_items.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Quantities
    ordered_quantity = db.Column(db.Integer, nullable=False)
    received_quantity = db.Column(db.Integer, nullable=False)
    rejected_quantity = db.Column(db.Integer, default=0)
    
    # Batch/lot information
    batch_number = db.Column(db.String(50), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    manufacturing_date = db.Column(db.Date, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    receipt = db.relationship('PurchaseReceipt', backref='receipt_items')
    purchase_order_item = db.relationship('PurchaseOrderItem', backref='receipt_items')
    product = db.relationship('Product', backref='receipt_items')
    variant = db.relationship('ProductVariant', backref='receipt_items')
    
    def __init__(self, receipt_id, purchase_order_item_id, product_id,
                 ordered_quantity, received_quantity, variant_id=None,
                 rejected_quantity=0, batch_number=None, expiry_date=None,
                 manufacturing_date=None, notes=None, tenant_id=None):
        self.receipt_id = receipt_id
        self.purchase_order_item_id = purchase_order_item_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.ordered_quantity = ordered_quantity
        self.received_quantity = received_quantity
        self.rejected_quantity = rejected_quantity
        self.batch_number = batch_number
        self.expiry_date = expiry_date
        self.manufacturing_date = manufacturing_date
        self.notes = notes
        self.tenant_id = tenant_id
    
    @property
    def accepted_quantity(self):
        """Get accepted quantity (received - rejected)"""
        return self.received_quantity - self.rejected_quantity
    
    def to_dict(self):
        """Convert purchase receipt item to dictionary"""
        return {
            'id': self.id,
            'receipt_id': self.receipt_id,
            'purchase_order_item_id': self.purchase_order_item_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'ordered_quantity': self.ordered_quantity,
            'received_quantity': self.received_quantity,
            'rejected_quantity': self.rejected_quantity,
            'accepted_quantity': self.accepted_quantity,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'manufacturing_date': self.manufacturing_date.isoformat() if self.manufacturing_date else None,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<PurchaseReceiptItem {self.product.name if self.product else "Unknown"}: {self.accepted_quantity}/{self.ordered_quantity}>'


# Association table for supplier-product relationship
supplier_products = db.Table('supplier_products',
    db.Column('supplier_id', db.Integer, db.ForeignKey('suppliers.id'), primary_key=True),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('supplier_sku', db.String(100), nullable=True),
    db.Column('supplier_product_code', db.String(100), nullable=True),
    db.Column('lead_time_days', db.Integer, default=7),
    db.Column('min_order_quantity', db.Integer, default=1),
    db.Column('is_preferred', db.Boolean, default=False),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)