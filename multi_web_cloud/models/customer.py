from datetime import datetime, timedelta
from decimal import Decimal
from utils.encryption import get_encryption_manager
from . import db

class Customer(db.Model):
    """Customer model for CRM system"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    # Encrypted personal information
    _name = db.Column('name', db.Text)
    _email = db.Column('email', db.Text)
    _mobile = db.Column('mobile', db.Text)
    _address = db.Column('address', db.Text)
    _city = db.Column('city', db.Text)
    _state = db.Column('state', db.Text)
    _postal_code = db.Column('postal_code', db.Text)
    _date_of_birth = db.Column('date_of_birth', db.Text)
    _anniversary_date = db.Column('anniversary_date', db.Text)
    
    # Loyalty program fields
    loyalty_tier_id = db.Column(db.Integer, db.ForeignKey('loyalty_tiers.id'), nullable=True)
    total_points_earned = db.Column(db.Integer, default=0)
    total_points_redeemed = db.Column(db.Integer, default=0)
    current_points = db.Column(db.Integer, default=0)
    
    # Order statistics
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Numeric(10, 2), default=0)
    average_order_value = db.Column(db.Numeric(10, 2), default=0)
    last_order_date = db.Column(db.DateTime)
    first_order_date = db.Column(db.DateTime)
    
    # Preferences and settings
    preferred_language = db.Column(db.String(10), default='en')
    communication_preferences = db.Column(db.Text)  # JSON string
    is_active = db.Column(db.Boolean, default=True)
    is_anonymized = db.Column(db.Boolean, default=False)
    anonymized_date = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    loyalty_tier = db.relationship('LoyaltyTier', backref='customers')
    creator = db.relationship('User', backref='created_customers', foreign_keys=[created_by])
    points_transactions = db.relationship('PointsTransaction', backref='customer', lazy='dynamic')
    reward_redemptions = db.relationship('RewardRedemption', backref='customer', lazy='dynamic')
    sent_referrals = db.relationship('Referral', foreign_keys='Referral.referrer_id', backref='referring_customers', lazy='dynamic')
    received_referral = db.relationship('Referral', foreign_keys='Referral.referred_customer_id', backref='referred_customers', lazy='select')
    
    def __init__(self, name, mobile, email=None, address=None, city=None, state=None, 
                 postal_code=None, date_of_birth=None, anniversary_date=None, 
                 loyalty_tier_id=None, created_by=None):
        self._name = self._encrypt_field(name) if name else None
        self._mobile = self._encrypt_field(mobile) if mobile else None
        self._email = self._encrypt_field(email) if email else None
        self._address = self._encrypt_field(address) if address else None
        self._city = self._encrypt_field(city) if city else None
        self._state = self._encrypt_field(state) if state else None
        self._postal_code = self._encrypt_field(postal_code) if postal_code else None
        self._date_of_birth = self._encrypt_field(date_of_birth.isoformat() if date_of_birth else None) if date_of_birth else None
        self._anniversary_date = self._encrypt_field(anniversary_date.isoformat() if anniversary_date else None) if anniversary_date else None
        self.loyalty_tier_id = loyalty_tier_id
        self.created_by = created_by
    
    # Property accessors for encrypted fields
    @property
    def name(self):
        return self._decrypt_field(self._name)
    
    @name.setter
    def name(self, value):
        self._name = self._encrypt_field(value) if value else None
    
    @property
    def name_decrypted(self):
        return self._decrypt_field(self._name)
    
    @property
    def email(self):
        return self._decrypt_field(self._email)
    
    @email.setter
    def email(self, value):
        self._email = self._encrypt_field(value) if value else None
    
    @property
    def email_decrypted(self):
        return self._decrypt_field(self._email)
    
    @property
    def mobile(self):
        return self._decrypt_field(self._mobile)
    
    @mobile.setter
    def mobile(self, value):
        self._mobile = self._encrypt_field(value) if value else None
    
    @property
    def mobile_decrypted(self):
        return self._decrypt_field(self._mobile)
    
    @property
    def address(self):
        return self._decrypt_field(self._address)
    
    @address.setter
    def address(self, value):
        self._address = self._encrypt_field(value) if value else None
    
    @property
    def address_decrypted(self):
        return self._decrypt_field(self._address)
    
    @property
    def city(self):
        return self._decrypt_field(self._city)
    
    @city.setter
    def city(self, value):
        self._city = self._encrypt_field(value) if value else None
    
    @property
    def city_decrypted(self):
        return self._decrypt_field(self._city)
    
    @property
    def state(self):
        return self._decrypt_field(self._state)
    
    @state.setter
    def state(self, value):
        self._state = self._encrypt_field(value) if value else None
    
    @property
    def state_decrypted(self):
        return self._decrypt_field(self._state)
    
    @property
    def postal_code(self):
        return self._decrypt_field(self._postal_code)
    
    @postal_code.setter
    def postal_code(self, value):
        self._postal_code = self._encrypt_field(value) if value else None
    
    @property
    def postal_code_decrypted(self):
        return self._decrypt_field(self._postal_code)
    
    @property
    def date_of_birth(self):
        date_str = self._decrypt_field(self._date_of_birth)
        return datetime.fromisoformat(date_str) if date_str else None
    
    @date_of_birth.setter
    def date_of_birth(self, value):
        self._date_of_birth = self._encrypt_field(value.isoformat() if value else None) if value else None
    
    @property
    def date_of_birth_decrypted(self):
        date_str = self._decrypt_field(self._date_of_birth)
        return datetime.fromisoformat(date_str) if date_str else None
    
    @property
    def anniversary_date(self):
        date_str = self._decrypt_field(self._anniversary_date)
        return datetime.fromisoformat(date_str) if date_str else None
    
    @anniversary_date.setter
    def anniversary_date(self, value):
        self._anniversary_date = self._encrypt_field(value.isoformat() if value else None) if value else None
    
    @property
    def anniversary_date_decrypted(self):
        date_str = self._decrypt_field(self._anniversary_date)
        return datetime.fromisoformat(date_str) if date_str else None
    
    def _encrypt_field(self, field_value):
        """Encrypt a field value"""
        if not field_value:
            return None
        return get_encryption_manager().encrypt_field(field_value)
    
    def _decrypt_field(self, encrypted_value):
        """Decrypt a field value"""
        if not encrypted_value:
            return None
        return get_encryption_manager().decrypt_field(encrypted_value)
    
    def add_points(self, points, description, expiry_date=None):
        """Add points to customer account"""
        from .loyalty import PointsTransaction
        
        # Create points transaction
        transaction = PointsTransaction(
            customer_id=self.id,
            points=points,
            transaction_type='EARN',
            description=description,
            expiry_date=expiry_date
        )
        
        # Update customer points
        self.total_points_earned += points
        self.current_points += points
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    def redeem_points(self, points, description):
        """Redeem points from customer account"""
        from .loyalty import PointsTransaction
        
        # Check if customer has enough points
        if self.current_points < points:
            return False
        
        # Create points transaction
        transaction = PointsTransaction(
            customer_id=self.id,
            points=-points,
            transaction_type='REDEEM',
            description=description
        )
        
        # Update customer points
        self.total_points_redeemed += points
        self.current_points -= points
        
        db.session.add(transaction)
        db.session.commit()
        
        return transaction
    
    def update_order_statistics(self, order_amount):
        """Update customer order statistics"""
        self.total_orders += 1
        self.total_spent += Decimal(str(order_amount))
        self.average_order_value = self.total_spent / self.total_orders
        self.last_order_date = datetime.utcnow()
        
        if not self.first_order_date:
            self.first_order_date = datetime.utcnow()
        
        # Check for tier progression
        self.check_tier_progression()
        
        db.session.commit()
    
    def check_tier_progression(self):
        """Check and update loyalty tier based on spending"""
        if not self.loyalty_tier_id:
            # Assign default tier if none exists
            from .loyalty import LoyaltyTier
            default_tier = LoyaltyTier.query.filter_by(min_spending=0).first()
            if default_tier:
                self.loyalty_tier_id = default_tier.id
            return
        
        from .loyalty import LoyaltyTier
        current_tier = self.loyalty_tier
        
        # Find appropriate tier based on total spending
        new_tier = LoyaltyTier.query.filter(
            LoyaltyTier.min_spending <= self.total_spent
        ).order_by(LoyaltyTier.min_spending.desc()).first()
        
        if new_tier and new_tier.id != self.loyalty_tier_id:
            self.loyalty_tier_id = new_tier.id
            return new_tier
        
        return None
    
    def get_expiring_points(self, days=30):
        """Get points that will expire within specified days"""
        from .loyalty import PointsTransaction
        from datetime import datetime, timedelta
        
        expiry_date = datetime.utcnow() + timedelta(days=days)
        
        expiring_points = PointsTransaction.query.filter(
            PointsTransaction.customer_id == self.id,
            PointsTransaction.transaction_type == 'EARN',
            PointsTransaction.expiry_date <= expiry_date,
            PointsTransaction.expiry_date > datetime.utcnow()
        ).with_entities(
            db.func.sum(PointsTransaction.points)
        ).scalar() or 0
        
        return expiring_points
    
    def mask_data_for_role(self, user_role):
        """Mask sensitive data based on user role"""
        if user_role in ['admin', 'manager']:
            return self  # Full access for admin/manager
        
        # Create masked copy for other roles
        masked_data = {
            'id': self.id,
            'name': self.name_decrypted,  # Show name
            'loyalty_tier': self.loyalty_tier.name if self.loyalty_tier else None,
            'current_points': self.current_points,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        # Mask mobile number - show only last 4 digits
        if self.mobile_decrypted:
            mobile = self.mobile_decrypted
            if len(mobile) > 4:
                masked_data['mobile'] = '*' * (len(mobile) - 4) + mobile[-4:]
            else:
                masked_data['mobile'] = mobile
        
        # Mask email - show only domain
        if self.email_decrypted and '@' in self.email_decrypted:
            email = self.email_decrypted
            local, domain = email.split('@', 1)
            if len(local) > 2:
                masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
            else:
                masked_local = local
            masked_data['email'] = f"{masked_local}@{domain}"
        
        return masked_data
    
    def to_dict(self, mask_data=False, user_role=None):
        """Convert customer to dictionary"""
        data = {
            'id': self.id,
            'loyalty_tier_id': self.loyalty_tier_id,
            'loyalty_tier_name': self.loyalty_tier.name if self.loyalty_tier else None,
            'total_points_earned': self.total_points_earned,
            'total_points_redeemed': self.total_points_redeemed,
            'current_points': self.current_points,
            'total_orders': self.total_orders,
            'total_spent': float(self.total_spent),
            'average_order_value': float(self.average_order_value),
            'last_order_date': self.last_order_date.isoformat() if self.last_order_date else None,
            'first_order_date': self.first_order_date.isoformat() if self.first_order_date else None,
            'preferred_language': self.preferred_language,
            'communication_preferences': self.communication_preferences,
            'is_active': self.is_active,
            'is_anonymized': self.is_anonymized,
            'anonymized_date': self.anonymized_date.isoformat() if self.anonymized_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        # Add personal information if not masking
        if not mask_data:
            data.update({
                'name': self.name_decrypted,
                'email': self.email_decrypted,
                'mobile': self.mobile_decrypted,
                'address': self.address_decrypted,
                'city': self.city_decrypted,
                'state': self.state_decrypted,
                'postal_code': self.postal_code_decrypted,
                'date_of_birth': self.date_of_birth_decrypted.isoformat() if self.date_of_birth_decrypted else None,
                'anniversary_date': self.anniversary_date_decrypted.isoformat() if self.anniversary_date_decrypted else None
            })
        elif user_role:
            # Apply role-based masking
            masked_data = self.mask_data_for_role(user_role)
            data.update(masked_data)
        
        return data
    
    @staticmethod
    def get_by_mobile(mobile):
        """Get customer by mobile number"""
        encrypted_mobile = get_encryption_manager().encrypt_field(mobile)
        return Customer.query.filter_by(_mobile=encrypted_mobile).first()
    
    @staticmethod
    def get_by_email(email):
        """Get customer by email address"""
        encrypted_email = get_encryption_manager().encrypt_field(email)
        return Customer.query.filter_by(_email=encrypted_email).first()
    
    @staticmethod
    def search_customers(search_term, page=1, per_page=20):
        """Search customers by name, mobile, or email"""
        encrypted_search = get_encryption_manager().encrypt_field(search_term)
        
        # This is a simplified search - in production, you'd want more sophisticated search
        customers = Customer.query.filter(
            db.or_(
                Customer._name.like(f'%{encrypted_search}%'),
                Customer._mobile.like(f'%{encrypted_search}%'),
                Customer._email.like(f'%{encrypted_search}%')
            )
        ).filter_by(is_active=True).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return customers
    
    def __repr__(self):
        return f'<Customer {self.name_decrypted} ({self.mobile_decrypted})>'