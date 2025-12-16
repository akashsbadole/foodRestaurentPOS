from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class CashDrawer(FeatureAwareModel):
    """Cash drawer model for cash management"""
    __tablename__ = 'cash_drawers'
    
    # Feature requirements
    required_features = ['FEATURE_CASH_DRAWER']
    
    id = db.Column(db.Integer, primary_key=True)
    drawer_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Assignment
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Assigned user
    terminal_id = db.Column(db.String(50), nullable=True)  # Terminal/POS identifier
    location = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Closed')  # Open, Closed, Balanced, Discrepancy
    opening_balance = db.Column(db.Numeric(12, 2), default=0)
    current_balance = db.Column(db.Numeric(12, 2), default=0)
    expected_balance = db.Column(db.Numeric(12, 2), default=0)
    
    # Session information
    session_start = db.Column(db.DateTime, nullable=True)
    session_end = db.Column(db.DateTime, nullable=True)
    last_opened = db.Column(db.DateTime, nullable=True)
    last_closed = db.Column(db.DateTime, nullable=True)
    
    # Security
    is_locked = db.Column(db.Boolean, default=True)
    lock_code = db.Column(db.String(20), nullable=True)  # Encrypted lock code
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='assigned_cash_drawers')
    denomination_counts = db.relationship('DenominationCount', backref='cash_drawer', lazy=True, cascade='all, delete-orphan')
    cash_transactions = db.relationship('CashTransaction', backref='cash_drawer', lazy=True)
    
    def __init__(self, drawer_number, name, user_id=None, terminal_id=None,
                 location=None, opening_balance=0, is_locked=True, tenant_id=None):
        self.drawer_number = drawer_number
        self.name = name
        self.user_id = user_id
        self.terminal_id = terminal_id
        self.location = location
        self.opening_balance = Decimal(str(opening_balance))
        self.current_balance = Decimal(str(opening_balance))
        self.expected_balance = Decimal(str(opening_balance))
        self.is_locked = is_locked
        self.tenant_id = tenant_id
    
    @property
    def is_open(self):
        """Check if cash drawer is open"""
        return self.status == 'Open'
    
    @property
    def is_closed(self):
        """Check if cash drawer is closed"""
        return self.status == 'Closed'
    
    @property
    def is_balanced(self):
        """Check if cash drawer is balanced"""
        return self.status == 'Balanced'
    
    @property
    def has_discrepancy(self):
        """Check if cash drawer has discrepancy"""
        return self.status == 'Discrepancy'
    
    @property
    def session_duration(self):
        """Get session duration in minutes"""
        if not self.session_start:
            return None
        
        end_time = self.session_end or datetime.utcnow()
        duration = end_time - self.session_start
        return int(duration.total_seconds() / 60)
    
    @property
    def variance(self):
        """Get variance between expected and actual balance"""
        return self.current_balance - self.expected_balance
    
    def open_drawer(self, user_id, opening_balance=None):
        """Open cash drawer"""
        if self.is_open:
            return False, "Cash drawer is already open"
        
        self.status = 'Open'
        self.user_id = user_id
        self.session_start = datetime.utcnow()
        self.last_opened = datetime.utcnow()
        
        if opening_balance is not None:
            self.opening_balance = Decimal(str(opening_balance))
            self.current_balance = Decimal(str(opening_balance))
            self.expected_balance = Decimal(str(opening_balance))
        
        self.is_locked = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Cash drawer opened successfully"
    
    def close_drawer(self, closing_balance=None, notes=None):
        """Close cash drawer"""
        if not self.is_open:
            return False, "Cash drawer is not open"
        
        self.status = 'Closed'
        self.session_end = datetime.utcnow()
        self.last_closed = datetime.utcnow()
        
        if closing_balance is not None:
            self.current_balance = Decimal(str(closing_balance))
        
        # Check for discrepancy
        if abs(self.variance) > Decimal('0.01'):  # Allow small rounding differences
            self.status = 'Discrepancy'
        
        self.is_locked = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create cash transaction record
        transaction = CashTransaction(
            cash_drawer_id=self.id,
            transaction_type='close',
            amount=self.current_balance,
            expected_amount=self.expected_balance,
            variance=self.variance,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True, "Cash drawer closed successfully"
    
    def add_cash(self, amount, transaction_type='sale', notes=None):
        """Add cash to drawer"""
        if not self.is_open:
            return False, "Cash drawer is not open"
        
        amount = Decimal(str(amount))
        self.current_balance += amount
        self.expected_balance += amount
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create cash transaction record
        transaction = CashTransaction(
            cash_drawer_id=self.id,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=self.current_balance,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True, "Cash added successfully"
    
    def remove_cash(self, amount, transaction_type='payout', notes=None):
        """Remove cash from drawer"""
        if not self.is_open:
            return False, "Cash drawer is not open"
        
        amount = Decimal(str(amount))
        if self.current_balance < amount:
            return False, "Insufficient cash in drawer"
        
        self.current_balance -= amount
        self.expected_balance -= amount
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create cash transaction record
        transaction = CashTransaction(
            cash_drawer_id=self.id,
            transaction_type=transaction_type,
            amount=-amount,
            balance_after=self.current_balance,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True, "Cash removed successfully"
    
    def balance_drawer(self, user_id, denomination_counts=None, notes=None):
        """Balance cash drawer with denomination counts"""
        if not self.is_open:
            return False, "Cash drawer is not open"
        
        # Calculate total from denominations
        calculated_total = Decimal('0')
        if denomination_counts:
            for denom_count in denomination_counts:
                calculated_total += denom_count.denomination_value * denom_count.count
        
        # Update denomination counts
        if denomination_counts:
            # Clear existing counts
            DenominationCount.query.filter_by(cash_drawer_id=self.id).delete()
            
            # Add new counts
            for denom_count in denomination_counts:
                denom_count.cash_drawer_id = self.id
                db.session.add(denom_count)
        
        self.status = 'Balanced'
        self.current_balance = calculated_total
        self.session_end = datetime.utcnow()
        self.is_locked = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create cash transaction record
        transaction = CashTransaction(
            cash_drawer_id=self.id,
            transaction_type='balance',
            amount=calculated_total,
            expected_amount=self.expected_balance,
            variance=self.variance,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        return True, "Cash drawer balanced successfully"
    
    def to_dict(self, include_denominations=True, include_transactions=False):
        """Convert cash drawer to dictionary"""
        data = {
            'id': self.id,
            'drawer_number': self.drawer_number,
            'name': self.name,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'terminal_id': self.terminal_id,
            'location': self.location,
            'status': self.status,
            'opening_balance': float(self.opening_balance),
            'current_balance': float(self.current_balance),
            'expected_balance': float(self.expected_balance),
            'variance': float(self.variance),
            'session_start': self.session_start.isoformat() if self.session_start else None,
            'session_end': self.session_end.isoformat() if self.session_end else None,
            'session_duration': self.session_duration,
            'last_opened': self.last_opened.isoformat() if self.last_opened else None,
            'last_closed': self.last_closed.isoformat() if self.last_closed else None,
            'is_locked': self.is_locked,
            'is_open': self.is_open,
            'is_closed': self.is_closed,
            'is_balanced': self.is_balanced,
            'has_discrepancy': self.has_discrepancy,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_denominations:
            data['denomination_counts'] = [denom.to_dict() for denom in self.denomination_counts]
        
        if include_transactions:
            data['recent_transactions'] = [tx.to_dict() for tx in 
                self.cash_transactions.order_by(CashTransaction.created_at.desc()).limit(10)]
        
        return data
    
    @staticmethod
    def get_active_drawers(tenant_id=None):
        """Get all active (open) cash drawers"""
        query = CashDrawer.query.filter_by(status='Open')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_by_number(drawer_number, tenant_id=None):
        """Get cash drawer by number"""
        query = CashDrawer.query.filter_by(drawer_number=drawer_number)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<CashDrawer {self.name} ({self.status})>'


class DenominationCount(db.Model):
    """Denomination count model for cash drawer management"""
    __tablename__ = 'denomination_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    cash_drawer_id = db.Column(db.Integer, db.ForeignKey('cash_drawers.id'), nullable=False)
    
    # Denomination details
    denomination = db.Column(db.String(20), nullable=False)  # e.g., "2000", "500", "200", "100", "50", "20", "10", "5", "2", "1"
    denomination_value = db.Column(db.Numeric(10, 2), nullable=False)  # Actual value
    count = db.Column(db.Integer, default=0)
    
    # Count type
    count_type = db.Column(db.String(20), default='actual')  # actual, expected
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, cash_drawer_id, denomination, denomination_value, count=0,
                 count_type='actual', tenant_id=None):
        self.cash_drawer_id = cash_drawer_id
        self.denomination = denomination
        self.denomination_value = Decimal(str(denomination_value))
        self.count = count
        self.count_type = count_type
        self.tenant_id = tenant_id
    
    @property
    def total_value(self):
        """Get total value for this denomination"""
        return self.denomination_value * self.count
    
    def update_count(self, new_count):
        """Update denomination count"""
        self.count = new_count
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert denomination count to dictionary"""
        return {
            'id': self.id,
            'cash_drawer_id': self.cash_drawer_id,
            'denomination': self.denomination,
            'denomination_value': float(self.denomination_value),
            'count': self.count,
            'total_value': float(self.total_value),
            'count_type': self.count_type,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_by_cash_drawer(cash_drawer_id, count_type='actual', tenant_id=None):
        """Get denomination counts for a cash drawer"""
        query = DenominationCount.query.filter_by(cash_drawer_id=cash_drawer_id, count_type=count_type)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Denomination.denomination_value.desc()).all()
    
    def __repr__(self):
        return f'<DenominationCount {self.denomination}: {self.count}>'


class CashTransaction(db.Model):
    """Cash transaction model for tracking cash movements"""
    __tablename__ = 'cash_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    cash_drawer_id = db.Column(db.Integer, db.ForeignKey('cash_drawers.id'), nullable=False)
    
    # Transaction details
    transaction_type = db.Column(db.String(20), nullable=False)  # open, close, sale, refund, payout, balance
    amount = db.Column(db.Numeric(12, 2), nullable=False)  # Can be negative for cash out
    balance_before = db.Column(db.Numeric(12, 2), nullable=True)
    balance_after = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Variance information
    expected_amount = db.Column(db.Numeric(12, 2), nullable=True)
    variance = db.Column(db.Numeric(12, 2), nullable=True)
    
    # Reference information
    reference_type = db.Column(db.String(20), nullable=True)  # order, shift_end, etc.
    reference_id = db.Column(db.Integer, nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    cash_drawer = db.relationship('CashDrawer', backref='cash_transactions')
    creator = db.relationship('User', backref='created_cash_transactions')
    
    def __init__(self, cash_drawer_id, transaction_type, amount, balance_before=None,
                 expected_amount=None, variance=None, reference_type=None,
                 reference_id=None, notes=None, tenant_id=None, created_by=None):
        self.cash_drawer_id = cash_drawer_id
        self.transaction_type = transaction_type
        self.amount = Decimal(str(amount))
        self.balance_before = Decimal(str(balance_before)) if balance_before else None
        self.expected_amount = Decimal(str(expected_amount)) if expected_amount else None
        self.variance = Decimal(str(variance)) if variance else None
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
        
        # Calculate balance after if not provided
        if self.balance_before is not None:
            self.balance_after = self.balance_before + self.amount
    
    @property
    def is_cash_in(self):
        """Check if transaction is cash in"""
        return self.amount > 0
    
    @property
    def is_cash_out(self):
        """Check if transaction is cash out"""
        return self.amount < 0
    
    @property
    def has_variance(self):
        """Check if transaction has variance"""
        return self.variance is not None and abs(self.variance) > Decimal('0.01')
    
    def to_dict(self):
        """Convert cash transaction to dictionary"""
        return {
            'id': self.id,
            'cash_drawer_id': self.cash_drawer_id,
            'cash_drawer_name': self.cash_drawer.name if self.cash_drawer else None,
            'transaction_type': self.transaction_type,
            'amount': float(self.amount),
            'balance_before': float(self.balance_before) if self.balance_before else None,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'expected_amount': float(self.expected_amount) if self.expected_amount else None,
            'variance': float(self.variance) if self.variance else None,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'is_cash_in': self.is_cash_in,
            'is_cash_out': self.is_cash_out,
            'has_variance': self.has_variance,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    @staticmethod
    def get_by_cash_drawer(cash_drawer_id, start_date=None, end_date=None, tenant_id=None):
        """Get cash transactions for a cash drawer"""
        query = CashTransaction.query.filter_by(cash_drawer_id=cash_drawer_id)
        
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        if start_date:
            query = query.filter(CashTransaction.created_at >= start_date)
        
        if end_date:
            query = query.filter(CashTransaction.created_at <= end_date)
        
        return query.order_by(CashTransaction.created_at.desc()).all()
    
    @staticmethod
    def get_by_date_range(start_date, end_date, tenant_id=None):
        """Get cash transactions within date range"""
        query = CashTransaction.query.filter(
            CashTransaction.created_at >= start_date,
            CashTransaction.created_at <= end_date
        )
        
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        return query.order_by(CashTransaction.created_at.desc()).all()
    
    def __repr__(self):
        return f'<CashTransaction {self.transaction_type}: {self.amount}>'