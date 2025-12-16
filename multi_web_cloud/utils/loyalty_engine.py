"""
Loyalty Engine for CRM System
Handles points calculation, tier progression, and loyalty program logic
"""

from datetime import datetime, timedelta
from decimal import Decimal
from models import db, Customer, LoyaltyTier, LoyaltyProgram, PointsTransaction, Reward, RewardRedemption
import logging

logger = logging.getLogger(__name__)

class LoyaltyEngine:
    """Loyalty engine for managing customer loyalty programs"""
    
    def __init__(self):
        self.program = None
        self._load_active_program()
    
    def _load_active_program(self):
        """Load the active loyalty program"""
        try:
            self.program = LoyaltyProgram.get_active_program()
            if not self.program:
                logger.warning("No active loyalty program found")
        except Exception as e:
            logger.error(f"Error loading loyalty program: {str(e)}")
    
    def calculate_points(self, customer, order_amount, order_date=None):
        """
        Calculate points for an order based on loyalty program and customer tier
        
        Args:
            customer: Customer object
            order_amount: Order amount (Decimal)
            order_date: Order date (datetime), defaults to now
            
        Returns:
            Calculated points (int)
        """
        if not self.program or not self.program.is_valid:
            logger.warning("No valid loyalty program available")
            return 0
        
        try:
            # Get base points from loyalty program
            base_points = self.program.calculate_points_for_order(order_amount, customer)
            
            # Apply tier multiplier if customer has a tier
            if customer and customer.loyalty_tier:
                base_points = customer.loyalty_tier.calculate_points(base_points)
            
            return base_points
            
        except Exception as e:
            logger.error(f"Error calculating points: {str(e)}")
            return 0
    
    def calculate_points_bulk(self, customers, order_amount):
        """
        Calculate points for multiple customers efficiently
        
        Args:
            customers: List of Customer objects
            order_amount: Order amount (Decimal)
            
        Returns:
            Dictionary mapping customer_id to points
        """
        if not self.program or not self.program.is_valid:
            return {}
        
        points_map = {}
        
        try:
            # Get base points once
            base_points = self.program.calculate_points_for_order(order_amount)
            
            # Calculate points for each customer
            for customer in customers:
                customer_points = base_points
                
                # Apply tier multiplier
                if customer.loyalty_tier:
                    customer_points = customer.loyalty_tier.calculate_points(customer_points)
                
                points_map[customer.id] = customer_points
            
            return points_map
            
        except Exception as e:
            logger.error(f"Error calculating bulk points: {str(e)}")
            return {}
    
    def award_points(self, customer, order_amount, order_id=None, description=None):
        """
        Award points to customer for an order
        
        Args:
            customer: Customer object
            order_amount: Order amount (Decimal)
            order_id: Order ID for reference
            description: Transaction description
            
        Returns:
            PointsTransaction object or None
        """
        if not self.program or not self.program.is_valid:
            logger.warning("Cannot award points: No valid loyalty program")
            return None
        
        try:
            # Calculate points
            points = self.calculate_points(customer, order_amount)
            
            if points <= 0:
                logger.info(f"No points to award for order amount: {order_amount}")
                return None
            
            # Create transaction
            expiry_date = self.program.get_points_expiry_date()
            transaction_description = description or f"Points earned from order #{order_id}" if order_id else "Points earned"
            
            transaction = PointsTransaction(
                customer_id=customer.id,
                points=points,
                transaction_type='EARN',
                description=transaction_description,
                reference_type='ORDER',
                reference_id=order_id,
                expiry_date=expiry_date
            )
            
            # Update customer points
            customer.total_points_earned += points
            customer.current_points += points
            
            # Save transaction
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Awarded {points} points to customer {customer.id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Error awarding points: {str(e)}")
            db.session.rollback()
            return None
    
    def redeem_points(self, customer, points, description=None, reference_type=None, reference_id=None):
        """
        Redeem points from customer account
        
        Args:
            customer: Customer object
            points: Points to redeem (int)
            description: Redemption description
            reference_type: Reference type
            reference_id: Reference ID
            
        Returns:
            PointsTransaction object or None
        """
        try:
            # Check if customer has enough points
            if customer.current_points < points:
                logger.warning(f"Insufficient points: customer has {customer.current_points}, trying to redeem {points}")
                return None
            
            # Create transaction
            transaction_description = description or f"Points redeemed"
            
            transaction = PointsTransaction(
                customer_id=customer.id,
                points=-points,
                transaction_type='REDEEM',
                description=transaction_description,
                reference_type=reference_type,
                reference_id=reference_id
            )
            
            # Update customer points
            customer.total_points_redeemed += points
            customer.current_points -= points
            
            # Save transaction
            db.session.add(transaction)
            db.session.commit()
            
            logger.info(f"Redeemed {points} points from customer {customer.id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Error redeeming points: {str(e)}")
            db.session.rollback()
            return None
    
    def can_redeem_points(self, customer, points):
        """
        Check if customer can redeem specified points
        
        Args:
            customer: Customer object
            points: Points to check (int)
            
        Returns:
            Boolean indicating if redemption is possible
        """
        return customer.current_points >= points
    
    def check_tier_progression(self, customer):
        """
        Check and update customer's loyalty tier based on spending
        
        Args:
            customer: Customer object
            
        Returns:
            New LoyaltyTier object if tier changed, None otherwise
        """
        try:
            # Get appropriate tier based on spending
            new_tier = LoyaltyTier.get_tier_by_spending(customer.total_spent)
            
            if new_tier and (not customer.loyalty_tier_id or new_tier.id != customer.loyalty_tier_id):
                # Update customer tier
                old_tier_name = customer.loyalty_tier.name if customer.loyalty_tier else "None"
                customer.loyalty_tier_id = new_tier.id
                
                db.session.commit()
                
                logger.info(f"Customer {customer.id} progressed from {old_tier_name} to {new_tier.name}")
                return new_tier
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking tier progression: {str(e)}")
            return None
    
    def get_expiring_points(self, customer, days=30):
        """
        Get points that will expire within specified days
        
        Args:
            customer: Customer object
            days: Number of days to look ahead (int)
            
        Returns:
            Number of expiring points (int)
        """
        try:
            return PointsTransaction.get_expiring_points(customer.id, days)
        except Exception as e:
            logger.error(f"Error getting expiring points: {str(e)}")
            return 0
    
    def expire_points(self):
        """
        Expire all points that have passed their expiry date
        Should be run periodically (e.g., daily)
        
        Returns:
            Number of expired transactions (int)
        """
        try:
            # Get all customers with active points
            customers_with_points = Customer.query.filter(
                Customer.current_points > 0
            ).all()
            
            total_expired = 0
            
            for customer in customers_with_points:
                expired_count = PointsTransaction.expire_customer_points(customer.id)
                total_expired += expired_count
                
                if expired_count > 0:
                    # Update customer's current points
                    remaining_points = db.session.query(
                        db.func.sum(PointsTransaction.points)
                    ).filter(
                        PointsTransaction.customer_id == customer.id,
                        PointsTransaction.expired_at.is_(None)
                    ).scalar() or 0
                    
                    customer.current_points = max(0, remaining_points)
            
            db.session.commit()
            logger.info(f"Expired {total_expired} point transactions")
            return total_expired
            
        except Exception as e:
            logger.error(f"Error expiring points: {str(e)}")
            db.session.rollback()
            return 0
    
    def redeem_reward(self, customer, reward, quantity=1):
        """
        Redeem a reward for customer
        
        Args:
            customer: Customer object
            reward: Reward object
            quantity: Quantity to redeem (int)
            
        Returns:
            RewardRedemption object or None
        """
        try:
            # Check if reward is available
            if not reward.is_available:
                logger.warning(f"Reward {reward.id} is not available")
                return None
            
            # Check if customer meets tier requirements
            if reward.min_tier_id and customer.loyalty_tier_id:
                if customer.loyalty_tier.sort_order < reward.min_tier.sort_order:
                    logger.warning(f"Customer {customer.id} tier not eligible for reward {reward.id}")
                    return None
            
            # Calculate total points needed
            total_points_needed = reward.points_required * quantity
            
            # Check if customer has enough points
            if not self.can_redeem_points(customer, total_points_needed):
                logger.warning(f"Insufficient points for reward redemption")
                return None
            
            # Create redemption
            redemption = RewardRedemption(
                customer_id=customer.id,
                reward_id=reward.id,
                points_used=total_points_needed,
                quantity=quantity
            )
            
            # Redeem points from customer account
            self.redeem_points(
                customer, 
                total_points_needed, 
                f"Redeemed reward: {reward.name}",
                'REDEMPTION',
                redemption.id
            )
            
            # Update reward quantity
            reward.redeem(quantity)
            
            # Save redemption
            db.session.add(redemption)
            db.session.commit()
            
            logger.info(f"Customer {customer.id} redeemed reward {reward.id}")
            return redemption
            
        except Exception as e:
            logger.error(f"Error redeeming reward: {str(e)}")
            db.session.rollback()
            return None
    
    def get_customer_rewards(self, customer, page=1, per_page=20):
        """
        Get available rewards for customer based on their tier
        
        Args:
            customer: Customer object
            page: Page number (int)
            per_page: Items per page (int)
            
        Returns:
            Pagination object with available rewards
        """
        try:
            customer_tier_id = customer.loyalty_tier_id
            
            # Get available rewards for customer's tier
            available_rewards = Reward.get_available_rewards(customer_tier_id)
            
            # Filter rewards customer can afford
            affordable_rewards = [
                reward for reward in available_rewards 
                if reward.points_required <= customer.current_points
            ]
            
            # Manual pagination for filtering
            start = (page - 1) * per_page
            end = start + per_page
            
            paginated_rewards = affordable_rewards[start:end]
            
            # Create pagination-like object
            class Pagination:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page
                    self.has_prev = page > 1
                    self.has_next = page < self.pages
            
            return Pagination(
                paginated_rewards, 
                page, 
                per_page, 
                len(affordable_rewards)
            )
            
        except Exception as e:
            logger.error(f"Error getting customer rewards: {str(e)}")
            return None
    
    def get_customer_summary(self, customer):
        """
        Get comprehensive loyalty summary for customer
        
        Args:
            customer: Customer object
            
        Returns:
            Dictionary with loyalty summary
        """
        try:
            # Get basic info
            summary = {
                'customer_id': customer.id,
                'current_points': customer.current_points,
                'total_points_earned': customer.total_points_earned,
                'total_points_redeemed': customer.total_points_redeemed,
                'total_orders': customer.total_orders,
                'total_spent': float(customer.total_spent),
                'average_order_value': float(customer.average_order_value),
                'loyalty_tier': customer.loyalty_tier.to_dict() if customer.loyalty_tier else None,
                'expiring_points': self.get_expiring_points(customer, 30),
                'last_order_date': customer.last_order_date.isoformat() if customer.last_order_date else None,
                'first_order_date': customer.first_order_date.isoformat() if customer.first_order_date else None
            }
            
            # Get recent transactions
            recent_transactions = PointsTransaction.get_customer_transactions(
                customer.id, page=1, per_page=5
            )
            
            summary['recent_transactions'] = [
                transaction.to_dict() for transaction in recent_transactions.items
            ]
            
            # Get available rewards count
            available_rewards = self.get_customer_rewards(customer, page=1, per_page=1)
            summary['available_rewards_count'] = available_rewards.total if available_rewards else 0
            
            # Get next tier info
            if customer.loyalty_tier:
                current_tier = customer.loyalty_tier
                next_tier = LoyaltyTier.query.filter(
                    LoyaltyTier.min_spending > current_tier.min_spending,
                    LoyaltyTier.is_active == True
                ).order_by(LoyaltyTier.min_spending).first()
                
                if next_tier:
                    points_to_next_tier = next_tier.min_spending - customer.total_spent
                    summary['next_tier'] = {
                        'name': next_tier.name,
                        'min_spending': float(next_tier.min_spending),
                        'points_multiplier': float(next_tier.points_multiplier),
                        'points_needed': float(points_to_next_tier),
                        'spending_needed': float(points_to_next_tier)
                    }
                else:
                    summary['next_tier'] = None
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting customer summary: {str(e)}")
            return {}
    
    def refresh_program(self):
        """Refresh the active loyalty program (useful after program updates)"""
        self._load_active_program()
        logger.info("Loyalty program refreshed")

# Global loyalty engine instance
_loyalty_engine = None

def get_loyalty_engine():
    """Get the global loyalty engine instance"""
    global _loyalty_engine
    if _loyalty_engine is None:
        _loyalty_engine = LoyaltyEngine()
    return _loyalty_engine

# Convenience functions
def calculate_customer_points(customer, order_amount):
    """Calculate points for customer order"""
    return get_loyalty_engine().calculate_points(customer, order_amount)

def award_customer_points(customer, order_amount, order_id=None, description=None):
    """Award points to customer"""
    return get_loyalty_engine().award_points(customer, order_amount, order_id, description)

def redeem_customer_points(customer, points, description=None):
    """Redeem points from customer"""
    return get_loyalty_engine().redeem_points(customer, points, description)

def check_customer_tier_progression(customer):
    """Check and update customer tier"""
    return get_loyalty_engine().check_tier_progression(customer)

def get_customer_loyalty_summary(customer):
    """Get customer loyalty summary"""
    return get_loyalty_engine().get_customer_summary(customer)