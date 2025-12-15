from datetime import datetime, timedelta
from decimal import Decimal
from utils.encryption import get_encryption_manager
from . import db

class LoyaltyTier(db.Model):
    """Loyalty tier model for customer segmentation"""
    __tablename__ = 'loyalty_tiers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    min_spending = db.Column(db.Numeric(10, 2), nullable=False)
    max_spending = db.Column(db.Numeric(10, 2), nullable=False)
    points_multiplier = db.Column(db.Numeric(3, 2), default=1.0)
    benefits = db.Column(db.Text)
    color_code = db.Column(db.String(7), default='#808080')  # Hex color code
    icon = db.Column(db.String(50))  # Icon class name
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, min_spending, max_spending, points_multiplier=1.0, 
                 description=None, benefits=None, color_code='#808080', icon=None):
        self.name = name
        self.min_spending = Decimal(str(min_spending))
        self.max_spending = Decimal(str(max_spending))
        self.points_multiplier = Decimal(str(points_multiplier))
        self.description = description
        self.benefits = benefits
        self.color_code = color_code
        self.icon = icon
    
    @property
    def formatted_min_spending(self):
        """Get formatted minimum spending"""
        return f"₹{self.min_spending:.2f}"
    
    @property
    def formatted_max_spending(self):
        """Get formatted maximum spending"""
        if self.max_spending >= 999999:
            return "₹∞"
        return f"₹{self.max_spending:.2f}"
    
    @property
    def spending_range(self):
        """Get spending range as string"""
        if self.max_spending >= 999999:
            return f"₹{self.min_spending:.2f}+"
        return f"₹{self.min_spending:.2f} - ₹{self.max_spending:.2f}"
    
    def is_eligible(self, total_spending):
        """Check if customer is eligible for this tier"""
        spending = Decimal(str(total_spending))
        return self.min_spending <= spending < self.max_spending
    
    def calculate_points(self, base_points):
        """Calculate points with tier multiplier"""
        return int(base_points * self.points_multiplier)
    
    def to_dict(self):
        """Convert loyalty tier to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'min_spending': float(self.min_spending),
            'max_spending': float(self.max_spending),
            'formatted_min_spending': self.formatted_min_spending,
            'formatted_max_spending': self.formatted_max_spending,
            'spending_range': self.spending_range,
            'points_multiplier': float(self.points_multiplier),
            'benefits': self.benefits,
            'color_code': self.color_code,
            'icon': self.icon,
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_tier_by_spending(total_spending):
        """Get loyalty tier based on total spending"""
        spending = Decimal(str(total_spending))
        return LoyaltyTier.query.filter(
            LoyaltyTier.min_spending <= spending,
            LoyaltyTier.max_spending > spending,
            LoyaltyTier.is_active == True
        ).first()
    
    @staticmethod
    def get_all_active():
        """Get all active loyalty tiers ordered by spending"""
        return LoyaltyTier.query.filter_by(is_active=True).order_by(LoyaltyTier.min_spending).all()
    
    def __repr__(self):
        return f'<LoyaltyTier {self.name} ({self.spending_range})>'


class LoyaltyProgram(db.Model):
    """Loyalty program configuration"""
    __tablename__ = 'loyalty_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_per_rupee = db.Column(db.Numeric(5, 3), default=0.1)  # Points per ₹1 spent
    min_order_amount = db.Column(db.Numeric(10, 2), default=100)  # Min order for points
    max_points_per_order = db.Column(db.Integer, default=1000)  # Max points per order
    points_expiry_days = db.Column(db.Integer, default=365)  # Points validity in days
    birthday_bonus_points = db.Column(db.Integer, default=50)  # Birthday bonus points
    anniversary_bonus_points = db.Column(db.Integer, default=25)  # Anniversary bonus points
    referral_bonus_points = db.Column(db.Integer, default=100)  # Referral bonus points
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, description=None, points_per_rupee=0.1, min_order_amount=100,
                 max_points_per_order=1000, points_expiry_days=365, birthday_bonus_points=50,
                 anniversary_bonus_points=25, referral_bonus_points=100):
        self.name = name
        self.description = description
        self.points_per_rupee = Decimal(str(points_per_rupee))
        self.min_order_amount = Decimal(str(min_order_amount))
        self.max_points_per_order = max_points_per_order
        self.points_expiry_days = points_expiry_days
        self.birthday_bonus_points = birthday_bonus_points
        self.anniversary_bonus_points = anniversary_bonus_points
        self.referral_bonus_points = referral_bonus_points
    
    @property
    def is_valid(self):
        """Check if loyalty program is currently valid"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    def calculate_points_for_order(self, order_amount, customer=None):
        """Calculate points for an order"""
        # Check if order meets minimum amount
        if order_amount < self.min_order_amount:
            return 0
        
        # Calculate base points
        base_points = int(order_amount * self.points_per_rupee)
        
        # Apply maximum points limit
        base_points = min(base_points, self.max_points_per_order)
        
        # Apply birthday bonus if applicable
        if customer and customer.date_of_birth_decrypted:
            today = datetime.utcnow().date()
            customer_birthday = customer.date_of_birth_decrypted.date()
            if today.month == customer_birthday.month and today.day == customer_birthday.day:
                base_points += self.birthday_bonus_points
        
        # Apply anniversary bonus if applicable
        if customer and customer.anniversary_date_decrypted:
            today = datetime.utcnow().date()
            customer_anniversary = customer.anniversary_date_decrypted.date()
            if today.month == customer_anniversary.month and today.day == customer_anniversary.day:
                base_points += self.anniversary_bonus_points
        
        return base_points
    
    def get_points_expiry_date(self):
        """Get expiry date for points earned today"""
        return datetime.utcnow() + timedelta(days=self.points_expiry_days)
    
    def to_dict(self):
        """Convert loyalty program to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'points_per_rupee': float(self.points_per_rupee),
            'min_order_amount': float(self.min_order_amount),
            'max_points_per_order': self.max_points_per_order,
            'points_expiry_days': self.points_expiry_days,
            'birthday_bonus_points': self.birthday_bonus_points,
            'anniversary_bonus_points': self.anniversary_bonus_points,
            'referral_bonus_points': self.referral_bonus_points,
            'is_active': self.is_active,
            'is_valid': self.is_valid,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_active_program():
        """Get currently active loyalty program"""
        return LoyaltyProgram.query.filter_by(is_active=True).first()
    
    def __repr__(self):
        return f'<LoyaltyProgram {self.name} (Active: {self.is_active})>'


class PointsTransaction(db.Model):
    """Points transaction model for tracking customer points"""
    __tablename__ = 'points_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)  # Positive for earning, negative for redemption
    transaction_type = db.Column(db.String(20), nullable=False)  # EARN, REDEEM, EXPIRE, ADJUST
    description = db.Column(db.Text)
    reference_type = db.Column(db.String(50))  # ORDER, REDEMPTION, BONUS, REFERRAL
    reference_id = db.Column(db.Integer)  # ID of the reference entity
    expiry_date = db.Column(db.DateTime)
    expired_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='points_transactions')
    
    def __init__(self, customer_id, points, transaction_type, description=None,
                 reference_type=None, reference_id=None, expiry_date=None, created_by=None):
        self.customer_id = customer_id
        self.points = points
        self.transaction_type = transaction_type
        self.description = description
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.expiry_date = expiry_date
        self.created_by = created_by
    
    @property
    def is_expired(self):
        """Check if points have expired"""
        if self.expired_at:
            return True
        
        if self.expiry_date and datetime.utcnow() > self.expiry_date:
            return True
        
        return False
    
    @property
    def is_earning(self):
        """Check if this is an earning transaction"""
        return self.points > 0
    
    @property
    def is_redemption(self):
        """Check if this is a redemption transaction"""
        return self.points < 0
    
    @property
    def formatted_points(self):
        """Get formatted points with sign"""
        if self.points > 0:
            return f"+{self.points}"
        elif self.points < 0:
            return f"{self.points}"
        else:
            return "0"
    
    def expire_points(self):
        """Mark points as expired"""
        if not self.is_expired and self.points > 0:
            self.expired_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        """Convert points transaction to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'points': self.points,
            'formatted_points': self.formatted_points,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'is_expired': self.is_expired,
            'is_earning': self.is_earning,
            'is_redemption': self.is_redemption,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_customer_transactions(customer_id, page=1, per_page=20, transaction_type=None):
        """Get customer points transactions with pagination"""
        query = PointsTransaction.query.filter_by(customer_id=customer_id)
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        return query.order_by(PointsTransaction.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_expiring_points(customer_id, days=30):
        """Get points that will expire within specified days"""
        from datetime import timedelta
        
        expiry_date = datetime.utcnow() + timedelta(days=days)
        
        expiring_points = PointsTransaction.query.filter(
            PointsTransaction.customer_id == customer_id,
            PointsTransaction.transaction_type == 'EARN',
            PointsTransaction.expiry_date <= expiry_date,
            PointsTransaction.expiry_date > datetime.utcnow(),
            PointsTransaction.expired_at.is_(None)
        ).with_entities(
            db.func.sum(PointsTransaction.points)
        ).scalar() or 0
        
        return expiring_points
    
    @staticmethod
    def expire_customer_points(customer_id):
        """Expire all expired points for a customer"""
        expired_transactions = PointsTransaction.query.filter(
            PointsTransaction.customer_id == customer_id,
            PointsTransaction.transaction_type == 'EARN',
            PointsTransaction.expiry_date <= datetime.utcnow(),
            PointsTransaction.expired_at.is_(None)
        ).all()
        
        for transaction in expired_transactions:
            transaction.expire_points()
        
        return len(expired_transactions)
    
    def __repr__(self):
        return f'<PointsTransaction {self.formatted_points} ({self.transaction_type})>'


class Reward(db.Model):
    """Reward model for loyalty program"""
    __tablename__ = 'rewards'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    points_required = db.Column(db.Integer, nullable=False)
    reward_type = db.Column(db.String(20), default='DISCOUNT')  # DISCOUNT, ITEM, VOUCHER
    reward_value = db.Column(db.Numeric(10, 2))  # Discount amount or item value
    reward_unit = db.Column(db.String(20))  # %, ₹, item
    min_tier_id = db.Column(db.Integer, db.ForeignKey('loyalty_tiers.id'))
    max_quantity = db.Column(db.Integer)  # Maximum quantity available
    current_quantity = db.Column(db.Integer)  # Current quantity available
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    image_url = db.Column(db.String(255))
    terms_conditions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    min_tier = db.relationship('LoyaltyTier', backref='rewards')
    
    def __init__(self, name, points_required, reward_type='DISCOUNT', description=None,
                 reward_value=None, reward_unit=None, min_tier_id=None, max_quantity=None,
                 valid_until=None, image_url=None, terms_conditions=None):
        self.name = name
        self.points_required = points_required
        self.reward_type = reward_type
        self.description = description
        self.reward_value = Decimal(str(reward_value)) if reward_value else None
        self.reward_unit = reward_unit
        self.min_tier_id = min_tier_id
        self.max_quantity = max_quantity
        self.current_quantity = max_quantity if max_quantity else None
        self.valid_until = valid_until
        self.image_url = image_url
        self.terms_conditions = terms_conditions
    
    @property
    def is_available(self):
        """Check if reward is currently available"""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.max_quantity and self.current_quantity <= 0:
            return False
        
        return True
    
    @property
    def formatted_reward_value(self):
        """Get formatted reward value"""
        if not self.reward_value:
            return ""
        
        if self.reward_unit == '%':
            return f"{self.reward_value}%"
        elif self.reward_unit == '₹':
            return f"₹{self.reward_value:.2f}"
        elif self.reward_unit == 'item':
            return f"{int(self.reward_value)} items"
        else:
            return str(self.reward_value)
    
    @property
    def availability_status(self):
        """Get availability status"""
        if not self.is_active:
            return "Inactive"
        
        if self.valid_until and datetime.utcnow() > self.valid_until:
            return "Expired"
        
        if self.max_quantity and self.current_quantity <= 0:
            return "Out of Stock"
        
        return "Available"
    
    def redeem(self, quantity=1):
        """Redeem reward (reduce quantity)"""
        if self.max_quantity and self.current_quantity >= quantity:
            self.current_quantity -= quantity
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        """Convert reward to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'points_required': self.points_required,
            'reward_type': self.reward_type,
            'reward_value': float(self.reward_value) if self.reward_value else None,
            'formatted_reward_value': self.formatted_reward_value,
            'reward_unit': self.reward_unit,
            'min_tier_id': self.min_tier_id,
            'min_tier_name': self.min_tier.name if self.min_tier else None,
            'max_quantity': self.max_quantity,
            'current_quantity': self.current_quantity,
            'valid_from': self.valid_from.isoformat() if self.valid_from else None,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'image_url': self.image_url,
            'terms_conditions': self.terms_conditions,
            'is_active': self.is_active,
            'is_available': self.is_available,
            'availability_status': self.availability_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_available_rewards(customer_tier_id=None):
        """Get available rewards, optionally filtered by customer tier"""
        query = Reward.query.filter_by(is_active=True)
        
        # Filter by customer tier if specified
        if customer_tier_id:
            query = query.filter(
                db.or_(
                    Reward.min_tier_id.is_(None),
                    Reward.min_tier_id <= customer_tier_id
                )
            )
        
        # Filter by availability
        now = datetime.utcnow()
        query = query.filter(
            Reward.valid_from <= now,
            db.or_(
                Reward.valid_until.is_(None),
                Reward.valid_until > now
            )
        )
        
        # Filter by quantity
        query = query.filter(
            db.or_(
                Reward.max_quantity.is_(None),
                Reward.current_quantity > 0
            )
        )
        
        return query.order_by(Reward.points_required).all()
    
    def __repr__(self):
        return f'<Reward {self.name} ({self.points_required} points)>'


class RewardRedemption(db.Model):
    """Reward redemption model"""
    __tablename__ = 'reward_redemptions'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('rewards.id'), nullable=False)
    points_used = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    redemption_code = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='ACTIVE')  # ACTIVE, USED, EXPIRED
    redeemed_at = db.Column(db.DateTime, default=datetime.utcnow)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    reward = db.relationship('Reward', backref='redemptions')
    creator = db.relationship('User', backref='reward_redemptions')
    
    def __init__(self, customer_id, reward_id, points_used, quantity=1, expires_at=None,
                 notes=None, created_by=None):
        self.customer_id = customer_id
        self.reward_id = reward_id
        self.points_used = points_used
        self.quantity = quantity
        self.redemption_code = self._generate_redemption_code()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(days=30))
        self.notes = notes
        self.created_by = created_by
    
    def _generate_redemption_code(self):
        """Generate unique redemption code"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits, 
                k=8
            ))
            
            if not RewardRedemption.query.filter_by(redemption_code=code).first():
                return code
    
    @property
    def is_valid(self):
        """Check if redemption is valid"""
        if self.status != 'ACTIVE':
            return False
        
        if self.used_at:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    @property
    def is_used(self):
        """Check if redemption has been used"""
        return self.status == 'USED'
    
    @property
    def is_expired(self):
        """Check if redemption has expired"""
        return self.status == 'EXPIRED' or (
            self.expires_at and datetime.utcnow() > self.expires_at
        )
    
    def use(self):
        """Mark redemption as used"""
        if self.is_valid:
            self.status = 'USED'
            self.used_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    def expire(self):
        """Mark redemption as expired"""
        if self.status == 'ACTIVE':
            self.status = 'EXPIRED'
            db.session.commit()
            return True
        return False
    
    def to_dict(self):
        """Convert reward redemption to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'reward_id': self.reward_id,
            'reward_name': self.reward.name if self.reward else None,
            'points_used': self.points_used,
            'quantity': self.quantity,
            'redemption_code': self.redemption_code,
            'status': self.status,
            'is_valid': self.is_valid,
            'is_used': self.is_used,
            'is_expired': self.is_expired,
            'redeemed_at': self.redeemed_at.isoformat() if self.redeemed_at else None,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'notes': self.notes,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_customer_redemptions(customer_id, page=1, per_page=20, status=None):
        """Get customer reward redemptions with pagination"""
        query = RewardRedemption.query.filter_by(customer_id=customer_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(RewardRedemption.redeemed_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def __repr__(self):
        return f'<RewardRedemption {self.redemption_code} ({self.status})>'


class CustomerFeedback(db.Model):
    """Customer feedback model for loyalty program"""
    __tablename__ = 'customer_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 star rating
    feedback_text = db.Column(db.Text)
    feedback_type = db.Column(db.String(20), default='GENERAL')  # GENERAL, COMPLAINT, SUGGESTION
    status = db.Column(db.String(20), default='NEW')  # NEW, REVIEWED, RESOLVED
    response_text = db.Column(db.Text)
    responded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    responded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer')
    order = db.relationship('Order', backref='customer_feedback')
    responder = db.relationship('User', backref='feedback_responses')
    
    def __init__(self, customer_id, rating, feedback_text=None, feedback_type='GENERAL',
                 order_id=None):
        self.customer_id = customer_id
        self.rating = max(1, min(5, rating))  # Ensure rating is between 1-5
        self.feedback_text = feedback_text
        self.feedback_type = feedback_type
        self.order_id = order_id
    
    @property
    def rating_stars(self):
        """Get rating as stars"""
        return '★' * self.rating + '☆' * (5 - self.rating)
    
    @property
    def is_responded(self):
        """Check if feedback has been responded to"""
        return self.response_text is not None and self.responded_at is not None
    
    def respond(self, response_text, responded_by):
        """Respond to feedback"""
        self.response_text = response_text
        self.responded_by = responded_by
        self.responded_at = datetime.utcnow()
        self.status = 'REVIEWED'
        db.session.commit()
    
    def resolve(self):
        """Mark feedback as resolved"""
        self.status = 'RESOLVED'
        db.session.commit()
    
    def to_dict(self):
        """Convert feedback to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else None,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'rating': self.rating,
            'rating_stars': self.rating_stars,
            'feedback_text': self.feedback_text,
            'feedback_type': self.feedback_type,
            'status': self.status,
            'response_text': self.response_text,
            'responded_by': self.responded_by,
            'responded_by_name': self.responder.username if self.responder else None,
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'is_responded': self.is_responded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_customer_feedback(customer_id, page=1, per_page=20):
        """Get customer feedback with pagination"""
        return CustomerFeedback.query.filter_by(customer_id=customer_id).order_by(
            CustomerFeedback.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_pending_feedback():
        """Get all pending feedback"""
        return CustomerFeedback.query.filter_by(status='NEW').order_by(
            CustomerFeedback.created_at.desc()
        ).all()
    
    @staticmethod
    def get_feedback_stats(days=30):
        """Get feedback statistics for the last N days"""
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            func.count(CustomerFeedback.id).label('total_feedback'),
            func.avg(CustomerFeedback.rating).label('average_rating'),
            func.count(CustomerFeedback.id).filter(CustomerFeedback.rating >= 4).label('positive_feedback'),
            func.count(CustomerFeedback.id).filter(CustomerFeedback.rating <= 2).label('negative_feedback')
        ).filter(CustomerFeedback.created_at >= cutoff_date).first()
        
        return {
            'total_feedback': stats.total_feedback or 0,
            'average_rating': float(stats.average_rating or 0),
            'positive_feedback': stats.positive_feedback or 0,
            'negative_feedback': stats.negative_feedback or 0,
            'satisfaction_rate': (stats.positive_feedback / stats.total_feedback * 100) if stats.total_feedback > 0 else 0
        }
    
    def __repr__(self):
        return f'<CustomerFeedback {self.rating} stars from Customer {self.customer_id}>'


class Referral(db.Model):
    """Customer referral model for loyalty program"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    referred_customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    referral_code = db.Column(db.String(20), unique=True, nullable=False)
    referral_email = db.Column(db.String(120), nullable=True)
    referral_phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='PENDING')  # PENDING, REGISTERED, COMPLETED, EXPIRED
    bonus_points = db.Column(db.Integer, default=0)
    referrer_points_awarded = db.Column(db.Boolean, default=False)
    referred_points_awarded = db.Column(db.Boolean, default=False)
    registered_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrer = db.relationship('Customer', foreign_keys=[referrer_id], backref='referrals_made')
    referred_customer = db.relationship('Customer', foreign_keys=[referred_customer_id], backref='referral_received')
    
    def __init__(self, referrer_id, referral_code, referral_email=None, referral_phone=None,
                 bonus_points=100, expires_days=30):
        self.referrer_id = referrer_id
        self.referral_code = referral_code
        self.referral_email = referral_email
        self.referral_phone = referral_phone
        self.bonus_points = bonus_points
        self.expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    @property
    def is_expired(self):
        """Check if referral has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self):
        """Check if referral is active (not expired and not completed)"""
        return not self.is_expired and self.status in ['PENDING', 'REGISTERED']
    
    @property
    def can_award_referrer_points(self):
        """Check if referrer points can be awarded"""
        return (self.status == 'COMPLETED' and
                not self.referrer_points_awarded and
                self.referred_customer_id is not None)
    
    @property
    def can_award_referred_points(self):
        """Check if referred customer points can be awarded"""
        return (self.status == 'COMPLETED' and
                not self.referred_points_awarded and
                self.referred_customer_id is not None)
    
    def register_referred_customer(self, customer_id):
        """Register the referred customer"""
        if self.is_expired:
            return False
        
        self.referred_customer_id = customer_id
        self.status = 'REGISTERED'
        self.registered_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def complete_referral(self):
        """Mark referral as completed"""
        if self.status != 'REGISTERED':
            return False
        
        self.status = 'COMPLETED'
        self.completed_at = datetime.utcnow()
        db.session.commit()
        return True
    
    def expire_referral(self):
        """Mark referral as expired"""
        if self.status in ['COMPLETED', 'EXPIRED']:
            return False
        
        self.status = 'EXPIRED'
        db.session.commit()
        return True
    
    def award_referrer_points(self):
        """Award points to referrer"""
        if not self.can_award_referrer_points:
            return False
        
        try:
            # Create points transaction for referrer
            transaction = PointsTransaction(
                customer_id=self.referrer_id,
                points=self.bonus_points,
                transaction_type='EARN',
                description=f'Referral bonus for {self.referred_customer.name if self.referred_customer else "referred customer"}',
                reference_type='REFERRAL',
                reference_id=self.id
            )
            
            db.session.add(transaction)
            self.referrer_points_awarded = True
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            return False
    
    def award_referred_points(self):
        """Award points to referred customer"""
        if not self.can_award_referred_points:
            return False
        
        try:
            # Create points transaction for referred customer
            transaction = PointsTransaction(
                customer_id=self.referred_customer_id,
                points=self.bonus_points,
                transaction_type='EARN',
                description=f'Welcome bonus from referral by {self.referrer.name if self.referrer else "referrer"}',
                reference_type='REFERRAL',
                reference_id=self.id
            )
            
            db.session.add(transaction)
            self.referred_points_awarded = True
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            return False
    
    def award_both_points(self):
        """Award points to both referrer and referred customer"""
        referrer_success = self.award_referrer_points()
        referred_success = self.award_referred_points()
        return referrer_success and referred_success
    
    def to_dict(self):
        """Convert referral to dictionary"""
        return {
            'id': self.id,
            'referrer_id': self.referrer_id,
            'referrer_name': self.referrer.name if self.referrer else None,
            'referred_customer_id': self.referred_customer_id,
            'referred_customer_name': self.referred_customer.name if self.referred_customer else None,
            'referral_code': self.referral_code,
            'referral_email': self.referral_email,
            'referral_phone': self.referral_phone,
            'status': self.status,
            'bonus_points': self.bonus_points,
            'referrer_points_awarded': self.referrer_points_awarded,
            'referred_points_awarded': self.referred_points_awarded,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired,
            'is_active': self.is_active,
            'can_award_referrer_points': self.can_award_referrer_points,
            'can_award_referred_points': self.can_award_referred_points,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def generate_referral_code():
        """Generate unique referral code"""
        import random
        import string
        
        while True:
            code = ''.join(random.choices(
                string.ascii_uppercase + string.digits,
                k=8
            ))
            
            if not Referral.query.filter_by(referral_code=code).first():
                return code
    
    @staticmethod
    def get_by_code(referral_code):
        """Get referral by code"""
        return Referral.query.filter_by(referral_code=referral_code).first()
    
    @staticmethod
    def get_customer_referrals(customer_id, page=1, per_page=20):
        """Get customer's referrals with pagination"""
        return Referral.query.filter_by(referrer_id=customer_id).order_by(
            Referral.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_referral_stats(days=30):
        """Get referral statistics for the last N days"""
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            func.count(Referral.id).label('total_referrals'),
            func.count(Referral.id).filter(Referral.status == 'COMPLETED').label('completed_referrals'),
            func.count(Referral.id).filter(Referral.status == 'PENDING').label('pending_referrals'),
            func.sum(Referral.bonus_points).label('total_points_awarded')
        ).filter(Referral.created_at >= cutoff_date).first()
        
        return {
            'total_referrals': stats.total_referrals or 0,
            'completed_referrals': stats.completed_referrals or 0,
            'pending_referrals': stats.pending_referrals or 0,
            'completion_rate': (stats.completed_referrals / stats.total_referrals * 100) if stats.total_referrals > 0 else 0,
            'total_points_awarded': stats.total_points_awarded or 0
        }
    
    @staticmethod
    def cleanup_expired_referrals():
        """Clean up expired referrals"""
        expired_referrals = Referral.query.filter(
            Referral.expires_at < datetime.utcnow(),
            Referral.status.in_(['PENDING', 'REGISTERED'])
        ).all()
        
        count = 0
        for referral in expired_referrals:
            if referral.expire_referral():
                count += 1
        
        return count
    
    def __repr__(self):
        return f'<Referral {self.referral_code} ({self.status})>'