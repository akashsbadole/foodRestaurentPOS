from flask_sqlalchemy import SQLAlchemy

# Create shared database instance
db = SQLAlchemy()

from .user import User
from .category import Category
from .menu_item import MenuItem
from .table import Table
from .order import Order, OrderItem
from .payment import Payment
from .settings import Settings
from .customer import Customer
from .loyalty import LoyaltyTier, LoyaltyProgram, PointsTransaction, Reward, RewardRedemption, CustomerFeedback, Referral
from .tenant import (
    Tenant, TenantSettings, SubscriptionPlan, TenantSubscription,
    TenantFeatureFlag, TenantUsage
)

def create_tables():
    """Create all database tables"""
    db.create_all()

__all__ = [
    'db', 'User', 'Category', 'MenuItem', 'Table', 'Order', 'OrderItem', 'Payment', 'Settings',
    'Customer', 'LoyaltyTier', 'LoyaltyProgram', 'PointsTransaction', 'Reward', 'RewardRedemption',
    'CustomerFeedback', 'Referral', 'create_tables', 'Tenant', 'TenantSettings', 'SubscriptionPlan',
    'TenantSubscription', 'TenantFeatureFlag', 'TenantUsage'
]
