"""
Loyalty Routes for CRM System
Handles loyalty program operations, rewards, and points management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from flask_login import login_required, current_user
from models import db, Customer, LoyaltyTier, LoyaltyProgram, PointsTransaction, Reward, RewardRedemption
from utils.security_manager import security_manager, validate_security_json_input, rate_limit
from utils.loyalty_engine import get_loyalty_engine
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

loyalty_bp = Blueprint('loyalty', __name__)

@loyalty_bp.route('/')
@login_required
def index():
    """Loyalty program main page"""
    return render_template('loyalty/index.html')

@loyalty_bp.route('/program', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_loyalty_program():
    """Get current loyalty program configuration"""
    try:
        program = LoyaltyProgram.get_active_program()
        
        if not program:
            return jsonify({
                'success': False,
                'message': 'No active loyalty program found'
            }), 404
        
        return jsonify({
            'success': True,
            'program': program.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting loyalty program: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve loyalty program'
        }), 500

@loyalty_bp.route('/rewards', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_rewards():
    """Get available rewards"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        tier_filter = request.args.get('tier', '')
        type_filter = request.args.get('type', '')
        
        # Get customer tier if specified
        customer_tier_id = None
        if tier_filter.isdigit():
            customer_tier_id = int(tier_filter)
        
        # Get available rewards
        rewards = Reward.get_available_rewards(customer_tier_id)
        
        # Apply type filter
        if type_filter:
            rewards = [r for r in rewards if r.reward_type == type_filter]
        
        # Manual pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_rewards = rewards[start:end]
        
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
        
        pagination = Pagination(
            paginated_rewards, 
            page, 
            per_page, 
            len(rewards)
        )
        
        return jsonify({
            'success': True,
            'rewards': [reward.to_dict() for reward in pagination.items],
            'filters': {
                'tier': tier_filter,
                'type': type_filter
            },
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting rewards: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve rewards'
        }), 500

@loyalty_bp.route('/rewards/<int:reward_id>/redeem', methods=['POST'])
@login_required
@validate_security_json_input(['customer_id', 'quantity'])
@rate_limit(limit=20, window=60)
def redeem_reward(reward_id):
    """Redeem a reward for customer"""
    try:
        data = g.sanitized_json
        customer_id = data.get('customer_id')
        quantity = data.get('quantity', 1)
        
        # Validate inputs
        if not customer_id:
            return jsonify({
                'success': False,
                'message': 'Customer ID is required'
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'message': 'Quantity must be greater than 0'
            }), 400
        
        # Get customer and reward
        customer = Customer.query.get_or_404(customer_id)
        reward = Reward.query.get_or_404(reward_id)
        
        # Use loyalty engine to redeem reward
        loyalty_engine = get_loyalty_engine()
        redemption = loyalty_engine.redeem_reward(customer, reward, quantity)
        
        if redemption:
            # Log reward redemption
            security_manager.log_security_event(
                'REWARD_REDEEMED',
                f'Reward {reward.name} redeemed by customer {customer.name_decrypted}'
            )
            
            return jsonify({
                'success': True,
                'redemption': redemption.to_dict(),
                'customer': {
                    'id': customer.id,
                    'current_points': customer.current_points,
                    'total_points_redeemed': customer.total_points_redeemed
                },
                'message': f'{reward.name} redeemed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to redeem reward'
            }), 400
        
    except Exception as e:
        logger.error(f"Error redeeming reward {reward_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to redeem reward'
        }), 500

@loyalty_bp.route('/customers/<int:customer_id>/rewards', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer_rewards(customer_id):
    """Get available rewards for a specific customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # Use loyalty engine to get customer rewards
        loyalty_engine = get_loyalty_engine()
        rewards_pagination = loyalty_engine.get_customer_rewards(customer, page, per_page)
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name_decrypted,
                'current_points': customer.current_points,
                'loyalty_tier': customer.loyalty_tier.to_dict() if customer.loyalty_tier else None
            },
            'rewards': [reward.to_dict() for reward in rewards_pagination.items],
            'pagination': {
                'page': rewards_pagination.page,
                'pages': rewards_pagination.pages,
                'per_page': rewards_pagination.per_page,
                'total': rewards_pagination.total,
                'has_prev': rewards_pagination.has_prev,
                'has_next': rewards_pagination.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting rewards for customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customer rewards'
        }), 500

@loyalty_bp.route('/customers/<int:customer_id>/redemptions', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer_redemptions(customer_id):
    """Get customer reward redemptions"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status', '')
        
        # Get redemptions
        redemptions = RewardRedemption.get_customer_redemptions(
            customer_id, 
            page=page, 
            per_page=per_page,
            status=status_filter if status_filter else None
        )
        
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name_decrypted
            },
            'redemptions': [redemption.to_dict() for redemption in redemptions.items],
            'filters': {
                'status': status_filter
            },
            'pagination': {
                'page': redemptions.page,
                'pages': redemptions.pages,
                'per_page': redemptions.per_page,
                'total': redemptions.total,
                'has_prev': redemptions.has_prev,
                'has_next': redemptions.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting redemptions for customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customer redemptions'
        }), 500

@loyalty_bp.route('/redemptions/<int:redemption_id>/use', methods=['POST'])
@login_required
@validate_security_json_input([])
@rate_limit(limit=20, window=60)
def use_redemption(redemption_id):
    """Mark a redemption as used"""
    try:
        redemption = RewardRedemption.query.get_or_404(redemption_id)
        
        if not redemption.is_valid:
            return jsonify({
                'success': False,
                'message': 'Redemption is not valid or has already been used'
            }), 400
        
        # Use redemption
        if redemption.use():
            # Log redemption usage
            security_manager.log_security_event(
                'REDEMPTION_USED',
                f'Redemption {redemption.redemption_code} used by {current_user.username}'
            )
            
            return jsonify({
                'success': True,
                'redemption': redemption.to_dict(),
                'message': 'Redemption marked as used successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to use redemption'
            }), 500
        
    except Exception as e:
        logger.error(f"Error using redemption {redemption_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to use redemption'
        }), 500

@loyalty_bp.route('/points/expire', methods=['POST'])
@login_required
@validate_security_json_input([])
@rate_limit(limit=5, window=60)
def expire_points():
    """Manually expire points (admin function)"""
    if current_user.role not in ['admin', 'manager']:
        return jsonify({
            'success': False,
            'message': 'Insufficient permissions'
        }), 403
    
    try:
        # Use loyalty engine to expire points
        loyalty_engine = get_loyalty_engine()
        expired_count = loyalty_engine.expire_points()
        
        # Log points expiration
        security_manager.log_security_event(
            'POINTS_EXPIRED',
            f'{expired_count} point transactions expired by {current_user.username}'
        )
        
        return jsonify({
            'success': True,
            'expired_count': expired_count,
            'message': f'{expired_count} point transactions expired successfully'
        })
        
    except Exception as e:
        logger.error(f"Error expiring points: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to expire points'
        }), 500

@loyalty_bp.route('/stats', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_loyalty_stats():
    """Get loyalty program statistics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get basic stats
        total_customers = Customer.query.filter_by(is_active=True).count()
        customers_with_points = Customer.query.filter(
            Customer.is_active == True,
            Customer.current_points > 0
        ).count()
        
        # Get points stats
        total_points_earned = db.session.query(
            db.func.sum(PointsTransaction.points)
        ).filter(
            PointsTransaction.transaction_type == 'EARN',
            PointsTransaction.created_at >= datetime.utcnow() - timedelta(days=days)
        ).scalar() or 0
        
        total_points_redeemed = db.session.query(
            db.func.sum(db.func.abs(PointsTransaction.points))
        ).filter(
            PointsTransaction.transaction_type == 'REDEEM',
            PointsTransaction.created_at >= datetime.utcnow() - timedelta(days=days)
        ).scalar() or 0
        
        # Get redemption stats
        total_redemptions = RewardRedemption.query.filter(
            RewardRedemption.redeemed_at >= datetime.utcnow() - timedelta(days=days)
        ).count()
        
        used_redemptions = RewardRedemption.query.filter(
            RewardRedemption.used_at >= datetime.utcnow() - timedelta(days=days)
        ).count()
        
        # Get tier distribution
        tier_stats = db.session.query(
            LoyaltyTier.name,
            db.func.count(Customer.id).label('customer_count')
        ).join(
            Customer, LoyaltyTier.id == Customer.loyalty_tier_id
        ).filter(
            Customer.is_active == True
        ).group_by(LoyaltyTier.name).all()
        
        # Get reward stats
        active_rewards = Reward.query.filter_by(is_active=True).count()
        total_redemptions_all = RewardRedemption.query.count()
        
        stats = {
            'period_days': days,
            'customer_stats': {
                'total_customers': total_customers,
                'customers_with_points': customers_with_points,
                'customers_without_points': total_customers - customers_with_points
            },
            'points_stats': {
                'total_points_earned': total_points_earned,
                'total_points_redeemed': total_points_redeemed,
                'net_points': total_points_earned - total_points_redeemed
            },
            'redemption_stats': {
                'total_redemptions': total_redemptions,
                'used_redemptions': used_redemptions,
                'unused_redemptions': total_redemptions - used_redemptions
            },
            'tier_distribution': [
                {'tier': tier_name, 'count': count}
                for tier_name, count in tier_stats
            ],
            'reward_stats': {
                'active_rewards': active_rewards,
                'total_redemptions_all': total_redemptions_all
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting loyalty stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve loyalty statistics'
        }), 500

@loyalty_bp.route('/tiers', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_loyalty_tiers():
    """Get all loyalty tiers"""
    try:
        tiers = LoyaltyTier.get_all_active()
        
        return jsonify({
            'success': True,
            'tiers': [tier.to_dict() for tier in tiers]
        })
        
    except Exception as e:
        logger.error(f"Error getting loyalty tiers: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve loyalty tiers'
        }), 500

@loyalty_bp.route('/customers/<int:customer_id>/summary', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer_loyalty_summary(customer_id):
    """Get comprehensive loyalty summary for customer"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Use loyalty engine to get summary
        loyalty_engine = get_loyalty_engine()
        summary = loyalty_engine.get_customer_summary(customer)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting loyalty summary for customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customer loyalty summary'
        }), 500