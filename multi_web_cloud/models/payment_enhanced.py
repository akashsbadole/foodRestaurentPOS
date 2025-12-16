from datetime import datetime, date
from decimal import Decimal
from utils.encryption import get_encryption_manager
from . import db
from .feature_aware_model import FeatureAwareModel

class PaymentMethod(FeatureAwareModel):
    """Payment method model for different payment types"""
    __tablename__ = 'payment_methods'
    
    # Feature requirements
    required_features = ['FEATURE_CASH_PAYMENT', 'FEATURE_CARD_PAYMENT', 'FEATURE_UPI_PAYMENT', 
                       'FEATURE_WALLET_PAYMENT', 'FEATURE_EMI_OPTIONS']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    payment_type = db.Column(db.String(20), nullable=False)  # cash, card, upi, wallet, emi, bank_transfer
    
    # Configuration
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    requires_reference = db.Column(db.Boolean, default=False)  # Requires reference number
    allows_partial = db.Column(db.Boolean, default=True)  # Allows partial payments
    max_amount = db.Column(db.Numeric(12, 2), nullable=True)  # Maximum transaction amount
    
    # Fees and charges
    transaction_fee = db.Column(db.Numeric(5, 2), default=0)  # Percentage fee
    fixed_fee = db.Column(db.Numeric(10, 2), default=0)  # Fixed fee per transaction
    
    # Integration details
    gateway_provider = db.Column(db.String(100), nullable=True)  # Payment gateway provider
    gateway_config = db.Column(db.Text, nullable=True)  # JSON configuration
    
    # Display settings
    display_order = db.Column(db.Integer, default=0)
    icon_class = db.Column(db.String(100), nullable=True)  # CSS icon class
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, code, payment_type, is_active=True, is_default=False,
                 requires_reference=False, allows_partial=True, max_amount=None,
                 transaction_fee=0, fixed_fee=0, gateway_provider=None,
                 gateway_config=None, display_order=0, icon_class=None,
                 tenant_id=None):
        self.name = name
        self.code = code
        self.payment_type = payment_type
        self.is_active = is_active
        self.is_default = is_default
        self.requires_reference = requires_reference
        self.allows_partial = allows_partial
        self.max_amount = Decimal(str(max_amount)) if max_amount else None
        self.transaction_fee = Decimal(str(transaction_fee))
        self.fixed_fee = Decimal(str(fixed_fee))
        self.gateway_provider = gateway_provider
        self.gateway_config = gateway_config
        self.display_order = display_order
        self.icon_class = icon_class
        self.tenant_id = tenant_id
    
    def calculate_fees(self, amount):
        """Calculate transaction fees for given amount"""
        if not amount:
            return {'transaction_fee': 0, 'fixed_fee': 0, 'total_fee': 0}
        
        transaction_fee_amount = amount * (self.transaction_fee / Decimal('100'))
        total_fee = transaction_fee_amount + self.fixed_fee
        
        return {
            'transaction_fee': float(transaction_fee_amount),
            'fixed_fee': float(self.fixed_fee),
            'total_fee': float(total_fee)
        }
    
    def get_gateway_config(self):
        """Get gateway configuration as dictionary"""
        if not self.gateway_config:
            return {}
        import json
        try:
            return json.loads(self.gateway_config)
        except:
            return {}
    
    def to_dict(self):
        """Convert payment method to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'payment_type': self.payment_type,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'requires_reference': self.requires_reference,
            'allows_partial': self.allows_partial,
            'max_amount': float(self.max_amount) if self.max_amount else None,
            'transaction_fee': float(self.transaction_fee),
            'fixed_fee': float(self.fixed_fee),
            'gateway_provider': self.gateway_provider,
            'gateway_config': self.get_gateway_config(),
            'display_order': self.display_order,
            'icon_class': self.icon_class,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_active_methods(tenant_id=None):
        """Get all active payment methods"""
        query = PaymentMethod.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(PaymentMethod.display_order, PaymentMethod.name).all()
    
    @staticmethod
    def get_by_code(code, tenant_id=None):
        """Get payment method by code"""
        query = PaymentMethod.query.filter_by(code=code)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<PaymentMethod {self.name} ({self.code})>'


class SplitPayment(FeatureAwareModel):
    """Split payment model for multiple payment methods"""
    __tablename__ = 'split_payments'
    
    # Feature requirements
    required_features = ['FEATURE_SPLIT_PAYMENT']
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    
    # Split information
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    split_count = db.Column(db.Integer, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Partial, Completed, Failed
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order = db.relationship('Order', backref='split_payments')
    creator = db.relationship('User', backref='created_split_payments')
    payment_items = db.relationship('SplitPaymentItem', backref='split_payment', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, order_id, total_amount, split_count, tenant_id=None, created_by=None):
        self.order_id = order_id
        self.total_amount = Decimal(str(total_amount))
        self.split_count = split_count
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def paid_amount(self):
        """Get total paid amount"""
        return sum(item.amount for item in self.payment_items if item.status == 'Completed')
    
    @property
    def pending_amount(self):
        """Get pending amount"""
        return self.total_amount - self.paid_amount
    
    @property
    def is_completed(self):
        """Check if split payment is completed"""
        return self.status == 'Completed'
    
    @property
    def is_partial(self):
        """Check if split payment is partially paid"""
        return self.status == 'Partial'
    
    @property
    def is_pending(self):
        """Check if split payment is pending"""
        return self.status == 'Pending'
    
    def update_status(self):
        """Update split payment status based on payment items"""
        completed_count = sum(1 for item in self.payment_items if item.status == 'Completed')
        failed_count = sum(1 for item in self.payment_items if item.status == 'Failed')
        
        if completed_count == self.split_count:
            self.status = 'Completed'
        elif completed_count > 0:
            self.status = 'Partial'
        elif failed_count > 0:
            self.status = 'Failed'
        else:
            self.status = 'Pending'
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_items=True):
        """Convert split payment to dictionary"""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'pending_amount': float(self.pending_amount),
            'split_count': self.split_count,
            'status': self.status,
            'is_completed': self.is_completed,
            'is_partial': self.is_partial,
            'is_pending': self.is_pending,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        if include_items:
            data['payment_items'] = [item.to_dict() for item in self.payment_items]
        
        return data
    
    @staticmethod
    def get_by_order(order_id, tenant_id=None):
        """Get split payments for an order"""
        query = SplitPayment.query.filter_by(order_id=order_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    def __repr__(self):
        return f'<SplitPayment {self.total_amount} ({self.status})>'


class SplitPaymentItem(db.Model):
    """Split payment item model for individual payment methods"""
    __tablename__ = 'split_payment_items'
    
    id = db.Column(db.Integer, primary_key=True)
    split_payment_id = db.Column(db.Integer, db.ForeignKey('split_payments.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Failed, Refunded
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)  # Gateway response data
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    split_payment = db.relationship('SplitPayment', backref='payment_items')
    payment_method = db.relationship('PaymentMethod', backref='split_payment_items')
    processor = db.relationship('User', backref='processed_split_payments')
    
    def __init__(self, split_payment_id, payment_method_id, amount, reference_number=None,
                 notes=None, gateway_response=None, tenant_id=None, processed_by=None):
        self.split_payment_id = split_payment_id
        self.payment_method_id = payment_method_id
        self.amount = Decimal(str(amount))
        self.reference_number = self._encrypt_reference_number(reference_number) if reference_number else None
        self.notes = notes
        self.gateway_response = gateway_response
        self.tenant_id = tenant_id
        self.processed_by = processed_by
    
    def mark_completed(self):
        """Mark payment item as completed"""
        self.status = 'Completed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update split payment status
        self.split_payment.update_status()
    
    def mark_failed(self):
        """Mark payment item as failed"""
        self.status = 'Failed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update split payment status
        self.split_payment.update_status()
    
    def get_gateway_response(self):
        """Get gateway response as dictionary"""
        if not self.gateway_response:
            return {}
        import json
        try:
            return json.loads(self.gateway_response)
        except:
            return {}
    
    def _encrypt_reference_number(self, reference_number):
        """Encrypt reference number"""
        if not reference_number:
            return None
        return get_encryption_manager().encrypt_field(reference_number)
    
    def _decrypt_reference_number(self, encrypted_reference_number):
        """Decrypt reference number"""
        if not encrypted_reference_number:
            return None
        return get_encryption_manager().decrypt_field(encrypted_reference_number)
    
    @property
    def reference_number_decrypted(self):
        """Get decrypted reference number"""
        return self._decrypt_reference_number(self.reference_number)
    
    def to_dict(self):
        """Convert split payment item to dictionary"""
        return {
            'id': self.id,
            'split_payment_id': self.split_payment_id,
            'payment_method_id': self.payment_method_id,
            'payment_method_name': self.payment_method.name if self.payment_method else None,
            'payment_method_code': self.payment_method.code if self.payment_method else None,
            'amount': float(self.amount),
            'reference_number': self._decrypt_reference_number(self.reference_number),
            'status': self.status,
            'notes': self.notes,
            'gateway_response': self.get_gateway_response(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_by': self.processed_by
        }
    
    def __repr__(self):
        return f'<SplitPaymentItem {self.payment_method.name if self.payment_method else "Unknown"}: {self.amount}>'


class EMIPayment(FeatureAwareModel):
    """EMI payment model for installment payments"""
    __tablename__ = 'emi_payments'
    
    # Feature requirements
    required_features = ['FEATURE_EMI_OPTIONS']
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=False)
    
    # EMI details
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    down_payment = db.Column(db.Numeric(12, 2), default=0)
    emi_amount = db.Column(db.Numeric(12, 2), nullable=False)
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)
    tenure_months = db.Column(db.Integer, nullable=False)
    processing_fee = db.Column(db.Numeric(10, 2), default=0)
    
    # EMI provider
    emi_provider = db.Column(db.String(100), nullable=True)  # Bank/EMI provider
    emi_plan = db.Column(db.String(100), nullable=True)  # Specific EMI plan
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Defaulted, Closed
    
    # Dates
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=True)
    next_payment_date = db.Column(db.Date, nullable=True)
    
    # Additional information
    reference_number = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order = db.relationship('Order', backref='emi_payments')
    payment_method = db.relationship('PaymentMethod', backref='emi_payments')
    creator = db.relationship('User', backref='created_emi_payments')
    installments = db.relationship('EMIInstallment', backref='emi_payment', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, order_id, payment_method_id, total_amount, emi_amount,
                 interest_rate, tenure_months, emi_provider=None, emi_plan=None,
                 down_payment=0, processing_fee=0, reference_number=None,
                 notes=None, tenant_id=None, created_by=None):
        self.order_id = order_id
        self.payment_method_id = payment_method_id
        self.total_amount = Decimal(str(total_amount))
        self.down_payment = Decimal(str(down_payment))
        self.emi_amount = Decimal(str(emi_amount))
        self.interest_rate = Decimal(str(interest_rate))
        self.tenure_months = tenure_months
        self.processing_fee = Decimal(str(processing_fee))
        self.emi_provider = emi_provider
        self.emi_plan = emi_plan
        self.reference_number = reference_number
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
        
        # Calculate end date
        from datetime import date, timedelta
        self.end_date = self.start_date + timedelta(days=tenure_months * 30)
        self.next_payment_date = self.start_date
    
    @property
    def financed_amount(self):
        """Get financed amount (total - down payment)"""
        return self.total_amount - self.down_payment
    
    @property
    def total_interest(self):
        """Get total interest amount"""
        return (self.emi_amount * self.tenure_months) - self.financed_amount
    
    @property
    def total_payable(self):
        """Get total payable amount"""
        return self.down_payment + (self.emi_amount * self.tenure_months) + self.processing_fee
    
    @property
    def paid_installments(self):
        """Get count of paid installments"""
        return sum(1 for installment in self.installments if installment.status == 'Paid')
    
    @property
    def pending_installments(self):
        """Get count of pending installments"""
        return sum(1 for installment in self.installments if installment.status == 'Pending')
    
    @property
    def overdue_installments(self):
        """Get count of overdue installments"""
        return sum(1 for installment in self.installments 
                  if installment.status == 'Pending' and installment.is_overdue)
    
    @property
    def is_completed(self):
        """Check if EMI is completed"""
        return self.status == 'Completed'
    
    @property
    def is_defaulted(self):
        """Check if EMI is defaulted"""
        return self.status == 'Defaulted'
    
    def create_installments(self):
        """Create EMI installments"""
        from datetime import date, timedelta
        
        # Clear existing installments
        for installment in self.installments:
            db.session.delete(installment)
        
        # Create new installments
        for i in range(1, self.tenure_months + 1):
            due_date = self.start_date + timedelta(days=i * 30)
            
            installment = EMIInstallment(
                emi_payment_id=self.id,
                installment_number=i,
                due_date=due_date,
                amount=self.emi_amount,
                tenant_id=self.tenant_id
            )
            db.session.add(installment)
        
        db.session.commit()
    
    def mark_completed(self):
        """Mark EMI as completed"""
        self.status = 'Completed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_defaulted(self):
        """Mark EMI as defaulted"""
        self.status = 'Defaulted'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_installments=True):
        """Convert EMI payment to dictionary"""
        data = {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'payment_method_id': self.payment_method_id,
            'payment_method_name': self.payment_method.name if self.payment_method else None,
            'total_amount': float(self.total_amount),
            'down_payment': float(self.down_payment),
            'financed_amount': float(self.financed_amount),
            'emi_amount': float(self.emi_amount),
            'interest_rate': float(self.interest_rate),
            'tenure_months': self.tenure_months,
            'total_interest': float(self.total_interest),
            'processing_fee': float(self.processing_fee),
            'total_payable': float(self.total_payable),
            'emi_provider': self.emi_provider,
            'emi_plan': self.emi_plan,
            'status': self.status,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'next_payment_date': self.next_payment_date.isoformat() if self.next_payment_date else None,
            'reference_number': self.reference_number,
            'notes': self.notes,
            'paid_installments': self.paid_installments,
            'pending_installments': self.pending_installments,
            'overdue_installments': self.overdue_installments,
            'is_completed': self.is_completed,
            'is_defaulted': self.is_defaulted,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        if include_installments:
            data['installments'] = [installment.to_dict() for installment in self.installments]
        
        return data
    
    @staticmethod
    def get_active_emis(tenant_id=None):
        """Get all active EMI payments"""
        query = EMIPayment.query.filter_by(status='Active')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(EMIPayment.next_payment_date).all()
    
    def __repr__(self):
        return f'<EMIPayment {self.total_amount} ({self.tenure_months} months)>'


class EMIInstallment(db.Model):
    """EMI installment model for individual installment payments"""
    __tablename__ = 'emi_installments'
    
    id = db.Column(db.Integer, primary_key=True)
    emi_payment_id = db.Column(db.Integer, db.ForeignKey('emi_payments.id'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    
    # Payment details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Paid, Overdue, Partial
    
    # Additional information
    late_fee = db.Column(db.Numeric(10, 2), default=0)
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emi_payment = db.relationship('EMIPayment', backref='installments')
    
    def __init__(self, emi_payment_id, installment_number, amount, due_date,
                 late_fee=0, notes=None, tenant_id=None):
        self.emi_payment_id = emi_payment_id
        self.installment_number = installment_number
        self.amount = Decimal(str(amount))
        self.due_date = due_date
        self.late_fee = Decimal(str(late_fee))
        self.notes = notes
        self.tenant_id = tenant_id
    
    @property
    def total_amount(self):
        """Get total amount including late fee"""
        return self.amount + self.late_fee
    
    @property
    def is_paid(self):
        """Check if installment is paid"""
        return self.status == 'Paid'
    
    @property
    def is_pending(self):
        """Check if installment is pending"""
        return self.status == 'Pending'
    
    @property
    def is_overdue(self):
        """Check if installment is overdue"""
        if self.status in ['Paid', 'Partial']:
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Get days overdue"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    def mark_paid(self, paid_date=None):
        """Mark installment as paid"""
        self.status = 'Paid'
        self.paid_date = paid_date or date.today()
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Update EMI payment status
        self.emi_payment.paid_installments = self.emi_payment.paid_installments + 1
        if self.emi_payment.paid_installments >= self.emi_payment.tenure_months:
            self.emi_payment.mark_completed()
    
    def mark_overdue(self):
        """Mark installment as overdue"""
        if self.status == 'Pending' and self.is_overdue:
            self.status = 'Overdue'
            self.updated_at = datetime.utcnow()
            db.session.commit()
    
    def to_dict(self):
        """Convert EMI installment to dictionary"""
        return {
            'id': self.id,
            'emi_payment_id': self.emi_payment_id,
            'installment_number': self.installment_number,
            'amount': float(self.amount),
            'late_fee': float(self.late_fee),
            'total_amount': float(self.total_amount),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'status': self.status,
            'is_paid': self.is_paid,
            'is_pending': self.is_pending,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<EMIInstallment #{self.installment_number} ({self.status})>'


class WalletPayment(FeatureAwareModel):
    """Wallet payment model for digital wallet payments"""
    __tablename__ = 'wallet_payments'
    
    # Feature requirements
    required_features = ['FEATURE_WALLET_PAYMENT']
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    wallet_provider = db.Column(db.String(50), nullable=False)  # Paytm, PhonePe, Amazon Pay, etc.
    
    # Payment details
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)  # Wallet transaction ID
    reference_number = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Failed, Refunded
    
    # Wallet balance
    wallet_balance_before = db.Column(db.Numeric(12, 2), nullable=True)
    wallet_balance_after = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    order = db.relationship('Order', backref='wallet_payments')
    customer = db.relationship('Customer', backref='wallet_payments')
    processor = db.relationship('User', backref='processed_wallet_payments')
    
    def __init__(self, order_id, customer_id, wallet_provider, amount,
                 transaction_id=None, reference_number=None, wallet_balance_before=None,
                 wallet_balance_after=None, notes=None, gateway_response=None,
                 tenant_id=None, processed_by=None):
        self.order_id = order_id
        self.customer_id = customer_id
        self.wallet_provider = wallet_provider
        self.amount = Decimal(str(amount))
        self.transaction_id = self._encrypt_transaction_id(transaction_id) if transaction_id else None
        self.reference_number = self._encrypt_reference_number(reference_number) if reference_number else None
        self.wallet_balance_before = Decimal(str(wallet_balance_before)) if wallet_balance_before else None
        self.wallet_balance_after = Decimal(str(wallet_balance_after)) if wallet_balance_after else None
        self.notes = notes
        self.gateway_response = gateway_response
        self.tenant_id = tenant_id
        self.processed_by = processed_by
    
    def mark_completed(self, wallet_balance_after=None):
        """Mark wallet payment as completed"""
        self.status = 'Completed'
        if wallet_balance_after is not None:
            self.wallet_balance_after = Decimal(str(wallet_balance_after))
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self):
        """Mark wallet payment as failed"""
        self.status = 'Failed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_refunded(self):
        """Mark wallet payment as refunded"""
        self.status = 'Refunded'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def get_gateway_response(self):
        """Get gateway response as dictionary"""
        if not self.gateway_response:
            return {}
        import json
        try:
            return json.loads(self.gateway_response)
        except:
            return {}
    
    def _encrypt_transaction_id(self, transaction_id):
        """Encrypt transaction ID"""
        if not transaction_id:
            return None
        return get_encryption_manager().encrypt_field(transaction_id)
    
    def _decrypt_transaction_id(self, encrypted_transaction_id):
        """Decrypt transaction ID"""
        if not encrypted_transaction_id:
            return None
        return get_encryption_manager().decrypt_field(encrypted_transaction_id)
    
    def _encrypt_reference_number(self, reference_number):
        """Encrypt reference number"""
        if not reference_number:
            return None
        return get_encryption_manager().encrypt_field(reference_number)
    
    def _decrypt_reference_number(self, encrypted_reference_number):
        """Decrypt reference number"""
        if not encrypted_reference_number:
            return None
        return get_encryption_manager().decrypt_field(encrypted_reference_number)
    
    @property
    def transaction_id_decrypted(self):
        """Get decrypted transaction ID"""
        return self._decrypt_transaction_id(self.transaction_id)
    
    @property
    def reference_number_decrypted(self):
        """Get decrypted reference number"""
        return self._decrypt_reference_number(self.reference_number)
    
    def to_dict(self):
        """Convert wallet payment to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'wallet_provider': self.wallet_provider,
            'amount': float(self.amount),
            'transaction_id': self._decrypt_transaction_id(self.transaction_id),
            'reference_number': self._decrypt_reference_number(self.reference_number),
            'status': self.status,
            'wallet_balance_before': float(self.wallet_balance_before) if self.wallet_balance_before else None,
            'wallet_balance_after': float(self.wallet_balance_after) if self.wallet_balance_after else None,
            'notes': self.notes,
            'gateway_response': self.get_gateway_response(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processed_by': self.processed_by
        }
    
    @staticmethod
    def get_by_customer(customer_id, tenant_id=None):
        """Get wallet payments for a customer"""
        query = WalletPayment.query.filter_by(customer_id=customer_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(WalletPayment.created_at.desc()).all()
    
    def __repr__(self):
        return f'<WalletPayment {self.wallet_provider}: {self.amount} ({self.status})>'