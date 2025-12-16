from datetime import datetime, date
from decimal import Decimal
from utils.encryption import get_encryption_manager
from . import db
from .feature_aware_model import FeatureAwareModel

class CustomerGroup(FeatureAwareModel):
    """Customer group model for customer segmentation"""
    __tablename__ = 'customer_groups'
    
    # Feature requirements
    required_features = ['FEATURE_CUSTOMER_GROUPS']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    
    # Discount and pricing
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    special_pricing = db.Column(db.Boolean, default=False)
    
    # Loyalty benefits
    loyalty_multiplier = db.Column(db.Numeric(3, 2), default=1.0)  # Points earning multiplier
    special_offers = db.Column(db.Boolean, default=False)
    
    # Credit terms
    credit_limit = db.Column(db.Numeric(12, 2), nullable=True)
    credit_days = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_customer_groups')
    customers = db.relationship('Customer', backref='customer_group', lazy=True)
    
    def __init__(self, name, code, description=None, discount_percentage=0,
                 special_pricing=False, loyalty_multiplier=1.0, special_offers=False,
                 credit_limit=None, credit_days=0, is_active=True,
                 is_default=False, tenant_id=None, created_by=None):
        self.name = name
        self.code = code
        self.description = description
        self.discount_percentage = Decimal(str(discount_percentage))
        self.special_pricing = special_pricing
        self.loyalty_multiplier = Decimal(str(loyalty_multiplier))
        self.special_offers = special_offers
        self.credit_limit = Decimal(str(credit_limit)) if credit_limit else None
        self.credit_days = credit_days
        self.is_active = is_active
        self.is_default = is_default
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def has_credit_facility(self):
        """Check if group has credit facility"""
        return self.credit_limit is not None and self.credit_days > 0
    
    def to_dict(self):
        """Convert customer group to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'discount_percentage': float(self.discount_percentage),
            'special_pricing': self.special_pricing,
            'loyalty_multiplier': float(self.loyalty_multiplier),
            'special_offers': self.special_offers,
            'credit_limit': float(self.credit_limit) if self.credit_limit else None,
            'credit_days': self.credit_days,
            'has_credit_facility': self.has_credit_facility,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_active_groups(tenant_id=None):
        """Get all active customer groups"""
        query = CustomerGroup.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(CustomerGroup.name).all()
    
    @staticmethod
    def get_default_group(tenant_id=None):
        """Get default customer group"""
        query = CustomerGroup.query.filter_by(is_default=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<CustomerGroup {self.name} ({self.code})>'


class CustomerCredit(FeatureAwareModel):
    """Customer credit model for credit management"""
    __tablename__ = 'customer_credits'
    
    # Feature requirements
    required_features = ['FEATURE_CUSTOMER_CREDIT']
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Credit limits and terms
    credit_limit = db.Column(db.Numeric(12, 2), nullable=False)
    credit_used = db.Column(db.Numeric(12, 2), default=0)
    available_credit = db.Column(db.Numeric(12, 2), nullable=False)
    credit_days = db.Column(db.Integer, default=30)
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Suspended, Blocked, Closed
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', backref='credit_account')
    approver = db.relationship('User', backref='approved_customer_credits')
    creator = db.relationship('User', backref='created_customer_credits')
    credit_transactions = db.relationship('CreditTransaction', backref='customer_credit', lazy=True)
    
    def __init__(self, customer_id, credit_limit, credit_days=30, status='Active',
                 notes=None, tenant_id=None, created_by=None):
        self.customer_id = customer_id
        self.credit_limit = Decimal(str(credit_limit))
        self.credit_used = Decimal('0')
        self.available_credit = Decimal(str(credit_limit))
        self.credit_days = credit_days
        self.status = status
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_active(self):
        """Check if credit is active"""
        return self.status == 'Active'
    
    @property
    def is_suspended(self):
        """Check if credit is suspended"""
        return self.status == 'Suspended'
    
    @property
    def is_blocked(self):
        """Check if credit is blocked"""
        return self.status == 'Blocked'
    
    @property
    def is_closed(self):
        """Check if credit is closed"""
        return self.status == 'Closed'
    
    @property
    def credit_utilization(self):
        """Get credit utilization percentage"""
        if self.credit_limit == 0:
            return 0
        return float((self.credit_used / self.credit_limit) * 100)
    
    @property
    def is_over_limit(self):
        """Check if credit is over limit"""
        return self.credit_used > self.credit_limit
    
    def approve_credit(self, approver_id):
        """Approve customer credit"""
        self.status = 'Active'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def suspend_credit(self, notes=None):
        """Suspend customer credit"""
        self.status = 'Suspended'
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def block_credit(self, notes=None):
        """Block customer credit"""
        self.status = 'Blocked'
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def close_credit(self, notes=None):
        """Close customer credit"""
        self.status = 'Closed'
        if notes:
            self.notes = notes
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def use_credit(self, amount, reference_type=None, reference_id=None, notes=None):
        """Use credit for purchase"""
        if not self.is_active:
            return False, "Credit account is not active"
        
        amount = Decimal(str(amount))
        if self.credit_used + amount > self.credit_limit:
            return False, "Insufficient credit limit"
        
        # Create credit transaction
        transaction = CreditTransaction(
            customer_credit_id=self.id,
            transaction_type='debit',
            amount=amount,
            balance_before=self.credit_used,
            balance_after=self.credit_used + amount,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            tenant_id=self.tenant_id
        )
        
        # Update credit usage
        self.credit_used += amount
        self.available_credit = self.credit_limit - self.credit_used
        self.updated_at = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        return True, "Credit used successfully"
    
    def repay_credit(self, amount, reference_type=None, reference_id=None, notes=None):
        """Repay credit"""
        if not self.is_active:
            return False, "Credit account is not active"
        
        amount = Decimal(str(amount))
        
        # Create credit transaction
        transaction = CreditTransaction(
            customer_credit_id=self.id,
            transaction_type='credit',
            amount=amount,
            balance_before=self.credit_used,
            balance_after=max(Decimal('0'), self.credit_used - amount),
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            tenant_id=self.tenant_id
        )
        
        # Update credit usage
        self.credit_used = max(Decimal('0'), self.credit_used - amount)
        self.available_credit = self.credit_limit - self.credit_used
        self.updated_at = datetime.utcnow()
        
        db.session.add(transaction)
        db.session.commit()
        return True, "Credit repaid successfully"
    
    def to_dict(self, include_transactions=False):
        """Convert customer credit to dictionary"""
        data = {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'credit_limit': float(self.credit_limit),
            'credit_used': float(self.credit_used),
            'available_credit': float(self.available_credit),
            'credit_utilization': self.credit_utilization,
            'credit_days': self.credit_days,
            'status': self.status,
            'is_active': self.is_active,
            'is_suspended': self.is_suspended,
            'is_blocked': self.is_blocked,
            'is_closed': self.is_closed,
            'is_over_limit': self.is_over_limit,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        if include_transactions:
            data['recent_transactions'] = [tx.to_dict() for tx in 
                self.credit_transactions.order_by(CreditTransaction.created_at.desc()).limit(10)]
        
        return data
    
    @staticmethod
    def get_by_customer(customer_id, tenant_id=None):
        """Get credit account for customer"""
        query = CustomerCredit.query.filter_by(customer_id=customer_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<CustomerCredit {self.credit_used}/{self.credit_limit}>'


class CreditTransaction(db.Model):
    """Credit transaction model for tracking credit movements"""
    __tablename__ = 'credit_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_credit_id = db.Column(db.Integer, db.ForeignKey('customer_credits.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False)  # debit, credit
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    balance_before = db.Column(db.Numeric(12, 2), nullable=False)
    balance_after = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Reference information
    reference_type = db.Column(db.String(20), nullable=True)  # order, payment, adjustment
    reference_id = db.Column(db.Integer, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    customer_credit = db.relationship('CustomerCredit', backref='credit_transactions')
    creator = db.relationship('User', backref='created_credit_transactions')
    
    def __init__(self, customer_credit_id, transaction_type, amount, balance_before,
                 balance_after, reference_type=None, reference_id=None,
                 notes=None, tenant_id=None, created_by=None):
        self.customer_credit_id = customer_credit_id
        self.transaction_type = transaction_type
        self.amount = Decimal(str(amount))
        self.balance_before = Decimal(str(balance_before))
        self.balance_after = Decimal(str(balance_after))
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_debit(self):
        """Check if transaction is a debit"""
        return self.transaction_type == 'debit'
    
    @property
    def is_credit(self):
        """Check if transaction is a credit"""
        return self.transaction_type == 'credit'
    
    def to_dict(self):
        """Convert credit transaction to dictionary"""
        return {
            'id': self.id,
            'customer_credit_id': self.customer_credit_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'balance_before': float(self.balance_before),
            'balance_after': float(self.balance_after),
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'is_debit': self.is_debit,
            'is_credit': self.is_credit,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_by_customer_credit(customer_credit_id, tenant_id=None):
        """Get transactions for customer credit"""
        query = CreditTransaction.query.filter_by(customer_credit_id=customer_credit_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(CreditTransaction.created_at.desc()).all()
    
    def __repr__(self):
        return f'<CreditTransaction {self.transaction_type}: {self.amount}>'


class CustomerNote(FeatureAwareModel):
    """Customer note model for customer interaction tracking"""
    __tablename__ = 'customer_notes'
    
    # Feature requirements
    required_features = ['FEATURE_CUSTOMER_NOTES']
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Note details
    note_type = db.Column(db.String(20), default='General')  # General, Complaint, Compliment, Issue, etc.
    subject = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    
    # Priority and status
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    status = db.Column(db.String(20), default='Open')  # Open, In Progress, Resolved, Closed
    
    # Resolution
    resolution = db.Column(db.Text, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Visibility
    is_internal = db.Column(db.Boolean, default=True)  # Visible to staff only
    is_visible_to_customer = db.Column(db.Boolean, default=False)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    customer = db.relationship('Customer', backref='notes')
    resolver = db.relationship('User', backref='resolved_customer_notes')
    creator = db.relationship('User', backref='created_customer_notes')
    
    def __init__(self, customer_id, content, note_type='General', subject=None,
                 priority='Normal', status='Open', is_internal=True,
                 is_visible_to_customer=False, tenant_id=None, created_by=None):
        self.customer_id = customer_id
        self.note_type = note_type
        self.subject = subject
        self.content = content
        self.priority = priority
        self.status = status
        self.is_internal = is_internal
        self.is_visible_to_customer = is_visible_to_customer
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_open(self):
        """Check if note is open"""
        return self.status == 'Open'
    
    @property
    def is_in_progress(self):
        """Check if note is in progress"""
        return self.status == 'In Progress'
    
    @property
    def is_resolved(self):
        """Check if note is resolved"""
        return self.status == 'Resolved'
    
    @property
    def is_closed(self):
        """Check if note is closed"""
        return self.status == 'Closed'
    
    def resolve(self, resolver_id, resolution=None):
        """Resolve customer note"""
        self.status = 'Resolved'
        self.resolved_by = resolver_id
        self.resolved_at = datetime.utcnow()
        if resolution:
            self.resolution = resolution
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def close(self, resolver_id=None, resolution=None):
        """Close customer note"""
        self.status = 'Closed'
        if resolver_id:
            self.resolved_by = resolver_id
        if resolution:
            self.resolution = resolution
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert customer note to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'note_type': self.note_type,
            'subject': self.subject,
            'content': self.content,
            'priority': self.priority,
            'status': self.status,
            'resolution': self.resolution,
            'resolved_by': self.resolved_by,
            'resolved_by_name': self.resolver.username if self.resolver else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_internal': self.is_internal,
            'is_visible_to_customer': self.is_visible_to_customer,
            'is_open': self.is_open,
            'is_in_progress': self.is_in_progress,
            'is_resolved': self.is_resolved,
            'is_closed': self.is_closed,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    @staticmethod
    def get_by_customer(customer_id, tenant_id=None, include_resolved=True):
        """Get notes for customer"""
        query = CustomerNote.query.filter_by(customer_id=customer_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        if not include_resolved:
            query = query.filter(CustomerNote.status.in_(['Open', 'In Progress']))
        
        return query.order_by(CustomerNote.priority.desc(), CustomerNote.created_at.desc()).all()
    
    @staticmethod
    def get_open_notes(tenant_id=None):
        """Get all open customer notes"""
        query = CustomerNote.query.filter(CustomerNote.status.in_(['Open', 'In Progress']))
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(CustomerNote.priority.desc(), CustomerNote.created_at.desc()).all()
    
    def __repr__(self):
        return f'<CustomerNote {self.subject or "No Subject"} ({self.status})>'


class PurchaseHistory(db.Model):
    """Purchase history model for customer purchase tracking"""
    __tablename__ = 'purchase_histories'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Purchase details
    purchase_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    items_count = db.Column(db.Integer, default=0)
    
    # Product information
    product_categories = db.Column(db.Text, nullable=True)  # JSON array of categories
    brands = db.Column(db.Text, nullable=True)  # JSON array of brands
    
    # Payment information
    payment_methods = db.Column(db.Text, nullable=True)  # JSON array of payment methods
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    loyalty_points_earned = db.Column(db.Integer, default=0)
    loyalty_points_redeemed = db.Column(db.Integer, default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='purchase_history')
    order = db.relationship('Order', backref='purchase_history')
    
    def __init__(self, customer_id, order_id, purchase_date, total_amount,
                 items_count=0, product_categories=None, brands=None,
                 payment_methods=None, discount_amount=0, loyalty_points_earned=0,
                 loyalty_points_redeemed=0, notes=None, tenant_id=None):
        self.customer_id = customer_id
        self.order_id = order_id
        self.purchase_date = purchase_date
        self.total_amount = Decimal(str(total_amount))
        self.items_count = items_count
        self.product_categories = product_categories
        self.brands = brands
        self.payment_methods = payment_methods
        self.discount_amount = Decimal(str(discount_amount))
        self.loyalty_points_earned = loyalty_points_earned
        self.loyalty_points_redeemed = loyalty_points_redeemed
        self.notes = notes
        self.tenant_id = tenant_id
    
    def get_product_categories(self):
        """Get product categories as list"""
        if not self.product_categories:
            return []
        import json
        try:
            return json.loads(self.product_categories)
        except:
            return []
    
    def get_brands(self):
        """Get brands as list"""
        if not self.brands:
            return []
        import json
        try:
            return json.loads(self.brands)
        except:
            return []
    
    def get_payment_methods(self):
        """Get payment methods as list"""
        if not self.payment_methods:
            return []
        import json
        try:
            return json.loads(self.payment_methods)
        except:
            return []
    
    @property
    def net_amount(self):
        """Get net amount after discounts"""
        return self.total_amount - self.discount_amount
    
    @property
    def net_points_earned(self):
        """Get net points earned"""
        return self.loyalty_points_earned - self.loyalty_points_redeemed
    
    def to_dict(self):
        """Convert purchase history to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'total_amount': float(self.total_amount),
            'discount_amount': float(self.discount_amount),
            'net_amount': float(self.net_amount),
            'items_count': self.items_count,
            'product_categories': self.get_product_categories(),
            'brands': self.get_brands(),
            'payment_methods': self.get_payment_methods(),
            'loyalty_points_earned': self.loyalty_points_earned,
            'loyalty_points_redeemed': self.loyalty_points_redeemed,
            'net_points_earned': self.net_points_earned,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_by_customer(customer_id, tenant_id=None, limit=50):
        """Get purchase history for customer"""
        query = PurchaseHistory.query.filter_by(customer_id=customer_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(PurchaseHistory.purchase_date.desc()).limit(limit).all()
    
    @staticmethod
    def get_customer_spending(customer_id, start_date=None, end_date=None, tenant_id=None):
        """Get customer spending summary"""
        query = db.session.query(
            db.func.count(PurchaseHistory.id).label('purchase_count'),
            db.func.sum(PurchaseHistory.total_amount).label('total_spent'),
            db.func.sum(PurchaseHistory.discount_amount).label('total_discount'),
            db.func.sum(PurchaseHistory.loyalty_points_earned).label('total_points_earned')
        ).filter_by(customer_id=customer_id)
        
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        if start_date:
            query = query.filter(PurchaseHistory.purchase_date >= start_date)
        
        if end_date:
            query = query.filter(PurchaseHistory.purchase_date <= end_date)
        
        result = query.first()
        return {
            'purchase_count': result.purchase_count or 0,
            'total_spent': float(result.total_spent or 0),
            'total_discount': float(result.total_discount or 0),
            'total_points_earned': result.total_points_earned or 0
        }
    
    def __repr__(self):
        return f'<PurchaseHistory {self.customer.name if self.customer else "Unknown"}: {self.total_amount}>'