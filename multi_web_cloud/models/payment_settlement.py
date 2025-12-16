"""
Payment & Settlement module models for handling enhanced payment methods, 
wallet payments, EMI options, denomination counting, cash management, 
split payments, and settlement processing.
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from models import db
from models.feature_aware_model import FeatureAwareModel


class PaymentMethod(FeatureAwareModel):
    """Enhanced payment method definitions"""
    __tablename__ = 'payment_methods'
    __feature_key__ = 'FEATURE_PAYMENT_METHODS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    method_name = Column(String(100), nullable=False)
    method_type = Column(String(50), nullable=False)  # cash, card, digital, wallet, emi, etc.
    display_name = Column(String(100))
    description = Column(Text)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    allows_partial = Column(Boolean, default=True)
    max_transaction_amount = Column(Numeric(12, 2))
    min_transaction_amount = Column(Numeric(12, 2))
    
    # Processing fees
    transaction_fee_type = Column(String(20))  # fixed, percentage, hybrid
    transaction_fee_amount = Column(Numeric(10, 2))
    transaction_fee_percentage = Column(Numeric(5, 2))
    
    # Settlement settings
    settlement_cycle = Column(String(20))  # daily, weekly, monthly
    settlement_delay_days = Column(Integer, default=0)
    auto_settle = Column(Boolean, default=True)
    
    # Integration details
    provider_name = Column(String(100))
    provider_config = Column(JSON)  # API keys, endpoints, etc.
    supported_currencies = Column(JSON)
    
    # Display settings
    icon_url = Column(String(500))
    button_color = Column(String(20))
    display_order = Column(Integer, default=0)
    show_on_receipt = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='payment_methods')
    creator = relationship('User', foreign_keys=[created_by])
    wallet_payments = relationship('WalletPayment', back_populates='payment_method')
    emi_payments = relationship('EMIPayment', back_populates='payment_method')
    split_payments = relationship('SplitPayment', back_populates='payment_method')
    settlement_records = relationship('SettlementRecord', back_populates='payment_method')
    
    def __repr__(self):
        return f'<PaymentMethod {self.method_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'method_name': self.method_name,
            'method_type': self.method_type,
            'display_name': self.display_name,
            'description': self.description,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'requires_approval': self.requires_approval,
            'allows_partial': self.allows_partial,
            'max_transaction_amount': float(self.max_transaction_amount) if self.max_transaction_amount else None,
            'min_transaction_amount': float(self.min_transaction_amount) if self.min_transaction_amount else None,
            'transaction_fee_type': self.transaction_fee_type,
            'transaction_fee_amount': float(self.transaction_fee_amount) if self.transaction_fee_amount else None,
            'transaction_fee_percentage': float(self.transaction_fee_percentage) if self.transaction_fee_percentage else None,
            'settlement_cycle': self.settlement_cycle,
            'settlement_delay_days': self.settlement_delay_days,
            'auto_settle': self.auto_settle,
            'provider_name': self.provider_name,
            'provider_config': self.provider_config,
            'supported_currencies': self.supported_currencies,
            'icon_url': self.icon_url,
            'button_color': self.button_color,
            'display_order': self.display_order,
            'show_on_receipt': self.show_on_receipt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def calculate_transaction_fee(self, amount):
        """Calculate transaction fee for a given amount"""
        if not self.transaction_fee_type or not amount:
            return Decimal('0')
        
        amount = Decimal(str(amount))
        
        if self.transaction_fee_type == 'fixed':
            return self.transaction_fee_amount or Decimal('0')
        elif self.transaction_fee_type == 'percentage':
            return amount * (self.transaction_fee_percentage or Decimal('0')) / Decimal('100')
        elif self.transaction_fee_type == 'hybrid':
            fixed_fee = self.transaction_fee_amount or Decimal('0')
            percentage_fee = amount * (self.transaction_fee_percentage or Decimal('0')) / Decimal('100')
            return fixed_fee + percentage_fee
        
        return Decimal('0')


class WalletPayment(FeatureAwareModel):
    """Wallet payment management"""
    __tablename__ = 'wallet_payments'
    __feature_key__ = 'FEATURE_WALLET_PAYMENTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    wallet_id = Column(String(100), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    
    # Transaction details
    transaction_id = Column(String(100), nullable=False, unique=True)
    transaction_type = Column(String(20), default='payment')  # payment, refund, topup
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default='USD')
    
    # Balance tracking
    balance_before = Column(Numeric(12, 2))
    balance_after = Column(Numeric(12, 2))
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, completed, failed, cancelled
    authorization_code = Column(String(100))
    reference_number = Column(String(100))
    
    # Processing details
    processed_at = Column(DateTime)
    failure_reason = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='wallet_payments')
    customer = relationship('Customer', back_populates='wallet_payments')
    payment_method = relationship('PaymentMethod', back_populates='wallet_payments')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<WalletPayment {self.transaction_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'wallet_id': self.wallet_id,
            'customer_id': self.customer_id,
            'payment_method_id': self.payment_method_id,
            'transaction_id': self.transaction_id,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'currency': self.currency,
            'balance_before': float(self.balance_before) if self.balance_before else None,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'status': self.status,
            'authorization_code': self.authorization_code,
            'reference_number': self.reference_number,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'failure_reason': self.failure_reason,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }


class EMIPayment(FeatureAwareModel):
    """EMI (Equated Monthly Installment) payment management"""
    __tablename__ = 'emi_payments'
    __feature_key__ = 'FEATURE_EMI_PAYMENTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    emi_plan_id = Column(String(100), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # EMI plan details
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2))
    tenure_months = Column(Integer, nullable=False)
    monthly_installment = Column(Numeric(12, 2), nullable=False)
    total_interest = Column(Numeric(12, 2))
    total_amount = Column(Numeric(12, 2))
    
    # Installment tracking
    installment_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_amount = Column(Numeric(12, 2))
    paid_date = Column(Date)
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, paid, overdue, cancelled
    late_fee = Column(Numeric(10, 2))
    penalty_interest = Column(Numeric(10, 2))
    
    # Processing details
    transaction_id = Column(String(100))
    payment_reference = Column(String(100))
    auto_debit_enabled = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='emi_payments')
    customer = relationship('Customer', back_populates='emi_payments')
    payment_method = relationship('PaymentMethod', back_populates='emi_payments')
    order = relationship('Order', back_populates='emi_payments')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<EMIPayment {self.emi_plan_id}:{self.installment_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'emi_plan_id': self.emi_plan_id,
            'customer_id': self.customer_id,
            'payment_method_id': self.payment_method_id,
            'order_id': self.order_id,
            'principal_amount': float(self.principal_amount),
            'interest_rate': float(self.interest_rate) if self.interest_rate else None,
            'tenure_months': self.tenure_months,
            'monthly_installment': float(self.monthly_installment),
            'total_interest': float(self.total_interest) if self.total_interest else None,
            'total_amount': float(self.total_amount),
            'installment_number': self.installment_number,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_amount': float(self.paid_amount) if self.paid_amount else None,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'status': self.status,
            'late_fee': float(self.late_fee) if self.late_fee else None,
            'penalty_interest': float(self.penalty_interest) if self.penalty_interest else None,
            'transaction_id': self.transaction_id,
            'payment_reference': self.payment_reference,
            'auto_debit_enabled': self.auto_debit_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_overdue(self):
        if self.status in ['paid', 'cancelled']:
            return False
        return self.due_date < date.today()
    
    @hybrid_property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @hybrid_property
    def outstanding_amount(self):
        if self.paid_amount:
            return float(self.monthly_installment) - float(self.paid_amount)
        return float(self.monthly_installment)


class DenominationCount(FeatureAwareModel):
    """Cash denomination counting and management"""
    __tablename__ = 'denomination_counts'
    __feature_key__ = 'FEATURE_DENOMINATION_COUNTING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    cash_drawer_id = Column(Integer, ForeignKey('cash_drawers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    shift_id = Column(String(100))
    
    # Denomination details
    currency = Column(String(10), default='USD')
    denomination_value = Column(Numeric(12, 2), nullable=False)  # e.g., 100, 50, 20, 10, 5, 1, 0.25, etc.
    denomination_type = Column(String(20))  # note, coin
    count = Column(Integer, nullable=False, default=0)
    
    # Value calculations
    total_value = Column(Numeric(12, 2))
    
    # Counting session
    count_type = Column(String(20), default='opening')  # opening, closing, interim
    count_time = Column(DateTime, default=datetime.utcnow)
    verified_by = Column(Integer, ForeignKey('users.id'))
    verification_notes = Column(Text)
    
    # Variance tracking
    expected_count = Column(Integer)
    variance_count = Column(Integer)
    variance_amount = Column(Numeric(12, 2))
    variance_reason = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='denomination_counts')
    cash_drawer = relationship('CashDrawer', back_populates='denomination_counts')
    user = relationship('User', foreign_keys=[user_id])
    verifier = relationship('User', foreign_keys=[verified_by])
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<DenominationCount {self.denomination_value}:{self.count}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'cash_drawer_id': self.cash_drawer_id,
            'user_id': self.user_id,
            'shift_id': self.shift_id,
            'currency': self.currency,
            'denomination_value': float(self.denomination_value),
            'denomination_type': self.denomination_type,
            'count': self.count,
            'total_value': float(self.total_value) if self.total_value else None,
            'count_type': self.count_type,
            'count_time': self.count_time.isoformat() if self.count_time else None,
            'verified_by': self.verified_by,
            'verification_notes': self.verification_notes,
            'expected_count': self.expected_count,
            'variance_count': self.variance_count,
            'variance_amount': float(self.variance_amount) if self.variance_amount else None,
            'variance_reason': self.variance_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def calculate_total_value(self):
        """Calculate total value for this denomination"""
        if self.denomination_value and self.count:
            return self.denomination_value * self.count
        return Decimal('0')
    
    def calculate_variance(self):
        """Calculate variance from expected count"""
        if self.expected_count is not None:
            self.variance_count = self.count - self.expected_count
            self.variance_amount = self.variance_count * self.denomination_value
        else:
            self.variance_count = None
            self.variance_amount = None


class SplitPayment(FeatureAwareModel):
    """Split payment management for multiple payment methods"""
    __tablename__ = 'split_payments'
    __feature_key__ = 'FEATURE_SPLIT_PAYMENTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'), nullable=False)
    
    # Payment details
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default='USD')
    sequence_number = Column(Integer, default=1)  # Order of payment methods
    
    # Transaction details
    transaction_id = Column(String(100))
    authorization_code = Column(String(100))
    reference_number = Column(String(100))
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, completed, failed, refunded
    processed_at = Column(DateTime)
    failure_reason = Column(Text)
    
    # Refund tracking
    refund_amount = Column(Numeric(12, 2))
    refund_date = Column(DateTime)
    refund_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='split_payments')
    order = relationship('Order', back_populates='split_payments')
    payment_method = relationship('PaymentMethod', back_populates='split_payments')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<SplitPayment {self.order_id}:{self.sequence_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'order_id': self.order_id,
            'payment_method_id': self.payment_method_id,
            'amount': float(self.amount),
            'currency': self.currency,
            'sequence_number': self.sequence_number,
            'transaction_id': self.transaction_id,
            'authorization_code': self.authorization_code,
            'reference_number': self.reference_number,
            'status': self.status,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'failure_reason': self.failure_reason,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'refund_date': self.refund_date.isoformat() if self.refund_date else None,
            'refund_reason': self.refund_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }


class SettlementRecord(FeatureAwareModel):
    """Payment settlement processing and tracking"""
    __tablename__ = 'settlement_records'
    __feature_key__ = 'FEATURE_SETTLEMENT_PROCESSING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    settlement_id = Column(String(100), nullable=False, unique=True)
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    
    # Settlement period
    settlement_start_date = Column(Date, nullable=False)
    settlement_end_date = Column(Date, nullable=False)
    settlement_date = Column(DateTime, nullable=False)
    
    # Transaction summary
    transaction_count = Column(Integer, default=0)
    gross_amount = Column(Numeric(15, 2), default=0)
    total_fees = Column(Numeric(12, 2), default=0)
    net_amount = Column(Numeric(15, 2), default=0)
    
    # Breakdown by status
    successful_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    refunded_transactions = Column(Integer, default=0)
    chargeback_transactions = Column(Integer, default=0)
    
    # Financial details
    currency = Column(String(10), default='USD')
    exchange_rate = Column(Numeric(10, 6))
    
    # Processing details
    processor_reference = Column(String(100))
    processor_response = Column(Text)
    batch_id = Column(String(100))
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, processing, completed, failed, cancelled
    initiated_at = Column(DateTime)
    completed_at = Column(DateTime)
    failure_reason = Column(Text)
    
    # Reconciliation
    reconciled = Column(Boolean, default=False)
    reconciled_by = Column(Integer, ForeignKey('users.id'))
    reconciled_at = Column(DateTime)
    reconciliation_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='settlement_records')
    payment_method = relationship('PaymentMethod', back_populates='settlement_records')
    reconciler = relationship('User', foreign_keys=[reconciled_by])
    creator = relationship('User', foreign_keys=[created_by])
    settlement_items = relationship('SettlementItem', back_populates='settlement', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SettlementRecord {self.settlement_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'settlement_id': self.settlement_id,
            'payment_method_id': self.payment_method_id,
            'settlement_start_date': self.settlement_start_date.isoformat() if self.settlement_start_date else None,
            'settlement_end_date': self.settlement_end_date.isoformat() if self.settlement_end_date else None,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'transaction_count': self.transaction_count,
            'gross_amount': float(self.gross_amount),
            'total_fees': float(self.total_fees),
            'net_amount': float(self.net_amount),
            'successful_transactions': self.successful_transactions,
            'failed_transactions': self.failed_transactions,
            'refunded_transactions': self.refunded_transactions,
            'chargeback_transactions': self.chargeback_transactions,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'processor_reference': self.processor_reference,
            'processor_response': self.processor_response,
            'batch_id': self.batch_id,
            'status': self.status,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failure_reason': self.failure_reason,
            'reconciled': self.reconciled,
            'reconciled_by': self.reconciled_by,
            'reconciled_at': self.reconciled_at.isoformat() if self.reconciled_at else None,
            'reconciliation_notes': self.reconciliation_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }


class SettlementItem(FeatureAwareModel):
    """Individual transaction items within a settlement"""
    __tablename__ = 'settlement_items'
    __feature_key__ = 'FEATURE_SETTLEMENT_PROCESSING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    settlement_id = Column(Integer, ForeignKey('settlement_records.id'), nullable=False)
    transaction_id = Column(String(100), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Transaction details
    transaction_date = Column(DateTime, nullable=False)
    transaction_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default='USD')
    
    # Fee breakdown
    transaction_fee = Column(Numeric(10, 2))
    processing_fee = Column(Numeric(10, 2))
    other_fee = Column(Numeric(10, 2))
    total_fee = Column(Numeric(10, 2))
    net_amount = Column(Numeric(12, 2))
    
    # Status and adjustments
    transaction_status = Column(String(20))  # success, failure, refund, chargeback
    adjustment_amount = Column(Numeric(12, 2))
    adjustment_reason = Column(String(200))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='settlement_items')
    settlement = relationship('SettlementRecord', back_populates='settlement_items')
    order = relationship('Order', back_populates='settlement_items')
    
    def __repr__(self):
        return f'<SettlementItem {self.transaction_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'settlement_id': self.settlement_id,
            'transaction_id': self.transaction_id,
            'order_id': self.order_id,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'transaction_amount': float(self.transaction_amount),
            'currency': self.currency,
            'transaction_fee': float(self.transaction_fee) if self.transaction_fee else None,
            'processing_fee': float(self.processing_fee) if self.processing_fee else None,
            'other_fee': float(self.other_fee) if self.other_fee else None,
            'total_fee': float(self.total_fee) if self.total_fee else None,
            'net_amount': float(self.net_amount) if self.net_amount else None,
            'transaction_status': self.transaction_status,
            'adjustment_amount': float(self.adjustment_amount) if self.adjustment_amount else None,
            'adjustment_reason': self.adjustment_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CashManagement(FeatureAwareModel):
    """Cash management and tracking"""
    __tablename__ = 'cash_management'
    __feature_key__ = 'FEATURE_CASH_MANAGEMENT'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    cash_drawer_id = Column(Integer, ForeignKey('cash_drawers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    shift_id = Column(String(100))
    
    # Cash amounts
    opening_balance = Column(Numeric(12, 2), default=0)
    cash_sales = Column(Numeric(12, 2), default=0)
    cash_received = Column(Numeric(12, 2), default=0)
    cash_paid_out = Column(Numeric(12, 2), default=0)
    closing_balance = Column(Numeric(12, 2), default=0)
    
    # Expected vs actual
    expected_closing_balance = Column(Numeric(12, 2))
    variance_amount = Column(Numeric(12, 2))
    variance_reason = Column(Text)
    
    # Session details
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime)
    session_type = Column(String(20), default='shift')  # shift, daily, custom
    
    # Status and verification
    status = Column(String(20), default='active')  # active, closed, verified
    verified_by = Column(Integer, ForeignKey('users.id'))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='cash_management')
    cash_drawer = relationship('CashDrawer', back_populates='cash_management')
    user = relationship('User', foreign_keys=[user_id])
    verifier = relationship('User', foreign_keys=[verified_by])
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<CashManagement {self.shift_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'cash_drawer_id': self.cash_drawer_id,
            'user_id': self.user_id,
            'shift_id': self.shift_id,
            'opening_balance': float(self.opening_balance),
            'cash_sales': float(self.cash_sales),
            'cash_received': float(self.cash_received),
            'cash_paid_out': float(self.cash_paid_out),
            'closing_balance': float(self.closing_balance),
            'expected_closing_balance': float(self.expected_closing_balance) if self.expected_closing_balance else None,
            'variance_amount': float(self.variance_amount) if self.variance_amount else None,
            'variance_reason': self.variance_reason,
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'session_end': self.session_end.isoformat() if self.session_end else None,
            'session_type': self.session_type,
            'status': self.status,
            'verified_by': self.verified_by,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'verification_notes': self.verification_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def calculate_expected_closing_balance(self):
        """Calculate expected closing balance"""
        return self.opening_balance + self.cash_sales + self.cash_received - self.cash_paid_out
    
    def calculate_variance(self):
        """Calculate variance amount"""
        if self.expected_closing_balance is not None:
            self.variance_amount = self.closing_balance - self.expected_closing_balance
        else:
            self.variance_amount = None