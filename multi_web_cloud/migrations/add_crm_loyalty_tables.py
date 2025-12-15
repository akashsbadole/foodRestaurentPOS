"""
Migration script to add CRM and Loyalty program tables to existing database
Run this script to update your database with the new CRM and loyalty functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db
from models.customer import Customer
from models.loyalty import LoyaltyTier, LoyaltyProgram, PointsTransaction, Reward, RewardRedemption, CustomerFeedback, Referral
from utils.encryption import EncryptionManager
from datetime import datetime, timedelta
from decimal import Decimal

def create_app():
    """Create Flask app for migration"""
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_pos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def migrate_database():
    """Run database migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting CRM and Loyalty database migration...")
        
        try:
            # Create all new tables
            print("Creating CRM and Loyalty tables...")
            db.create_all()
            
            # Initialize default loyalty tiers
            print("Initializing default loyalty tiers...")
            init_default_tiers()
            
            # Initialize default loyalty program
            print("Initializing default loyalty program...")
            init_default_program()
            
            # Initialize default rewards
            print("Initializing default rewards...")
            init_default_rewards()
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()
            raise

def init_default_tiers():
    """Initialize default loyalty tiers"""
    tiers_data = [
        {
            'name': 'Bronze',
            'description': 'Entry level membership',
            'min_spending': 0,
            'tier_order': 1,
            'points_multiplier': 1.0,
            'benefits': 'Basic points earning',
            'color': '#cd7f32'
        },
        {
            'name': 'Silver',
            'description': 'Regular customer membership',
            'min_spending': 5000,
            'tier_order': 2,
            'points_multiplier': 1.2,
            'benefits': '20% bonus points, special offers',
            'color': '#c0c0c0'
        },
        {
            'name': 'Gold',
            'description': 'Premium customer membership',
            'min_spending': 15000,
            'tier_order': 3,
            'points_multiplier': 1.5,
            'benefits': '50% bonus points, exclusive offers, priority service',
            'color': '#ffd700'
        },
        {
            'name': 'Platinum',
            'description': 'VIP customer membership',
            'min_spending': 50000,
            'tier_order': 4,
            'points_multiplier': 2.0,
            'benefits': 'Double points, exclusive rewards, dedicated support',
            'color': '#e5e4e2'
        }
    ]
    
    for tier_data in tiers_data:
        existing_tier = LoyaltyTier.query.filter_by(name=tier_data['name']).first()
        if not existing_tier:
            tier = LoyaltyTier(**tier_data)
            db.session.add(tier)
            print(f"Created tier: {tier_data['name']}")
    
    db.session.commit()

def init_default_program():
    """Initialize default loyalty program"""
    existing_program = LoyaltyProgram.query.first()
    if not existing_program:
        program = LoyaltyProgram(
            name='Default Loyalty Program',
            description='Earn points on every purchase and redeem for rewards',
            points_per_rupee=0.1,  # 1 point per ₹10
            min_order_amount=100,  # Minimum ₹100 to earn points
            max_points_per_order=500,  # Maximum 500 points per order
            points_expiry_days=365,  # Points expire after 1 year
            birthday_bonus_points=50,
            anniversary_bonus_points=100,
            is_active=True
        )
        db.session.add(program)
        print("Created default loyalty program")
        db.session.commit()

def init_default_rewards():
    """Initialize default rewards"""
    rewards_data = [
        {
            'name': '₹50 Discount',
            'description': 'Get ₹50 off on your next order',
            'reward_type': 'DISCOUNT',
            'reward_value': 50,
            'points_required': 500,
            'tier_order': 1,
            'is_active': True,
            'terms_conditions': 'Valid on orders above ₹200'
        },
        {
            'name': '₹100 Discount',
            'description': 'Get ₹100 off on your next order',
            'reward_type': 'DISCOUNT',
            'reward_value': 100,
            'points_required': 900,
            'tier_order': 2,
            'is_active': True,
            'terms_conditions': 'Valid on orders above ₹300'
        },
        {
            'name': 'Free Beverage',
            'description': 'Get any beverage free on your next order',
            'reward_type': 'ITEM',
            'reward_value': 150,
            'points_required': 300,
            'tier_order': 1,
            'is_active': True,
            'terms_conditions': 'Valid on beverages up to ₹150'
        },
        {
            'name': '₹250 Gift Voucher',
            'description': 'Gift voucher worth ₹250',
            'reward_type': 'VOUCHER',
            'reward_value': 250,
            'points_required': 2000,
            'tier_order': 3,
            'is_active': True,
            'terms_conditions': 'Valid for 3 months from issue date'
        },
        {
            'name': '₹500 Discount',
            'description': 'Get ₹500 off on your next order',
            'reward_type': 'DISCOUNT',
            'reward_value': 500,
            'points_required': 4000,
            'tier_order': 4,
            'is_active': True,
            'terms_conditions': 'Valid on orders above ₹1000'
        }
    ]
    
    for reward_data in rewards_data:
        existing_reward = Reward.query.filter_by(name=reward_data['name']).first()
        if not existing_reward:
            reward = Reward(**reward_data)
            db.session.add(reward)
            print(f"Created reward: {reward_data['name']}")
    
    db.session.commit()

def verify_migration():
    """Verify that migration was successful"""
    app = create_app()
    
    with app.app_context():
        print("\nVerifying migration...")
        
        # Check tables exist
        tables = [
            'customer', 'loyalty_tier', 'loyalty_program', 'points_transaction',
            'reward', 'reward_redemption', 'customer_feedback', 'referral'
        ]
        
        for table in tables:
            try:
                result = db.engine.execute(f"SELECT COUNT(*) FROM {table}")
                print(f"✓ Table '{table}' exists")
            except Exception as e:
                print(f"✗ Table '{table}' missing: {e}")
        
        # Check default data
        tier_count = LoyaltyTier.query.count()
        program_count = LoyaltyProgram.query.count()
        reward_count = Reward.query.count()
        
        print(f"\nDefault data created:")
        print(f"- Loyalty Tiers: {tier_count}")
        print(f"- Loyalty Programs: {program_count}")
        print(f"- Rewards: {reward_count}")
        
        if tier_count >= 4 and program_count >= 1 and reward_count >= 5:
            print("\n✓ Migration verification successful!")
            return True
        else:
            print("\n✗ Migration verification failed - missing default data")
            return False

if __name__ == '__main__':
    try:
        migrate_database()
        verify_migration()
        print("\nCRM and Loyalty system migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Access CRM at /crm")
        print("3. Access Loyalty Program at /loyalty")
        print("4. Configure loyalty settings as needed")
        
    except Exception as e:
        print(f"\nMigration failed: {str(e)}")
        print("Please check the error above and fix any issues before retrying.")
        sys.exit(1)