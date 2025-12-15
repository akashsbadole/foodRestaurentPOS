"""
CRM Routes for Customer Management
Handles customer creation, search, updates, and loyalty management
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from flask_login import login_required, current_user
from models import db, Customer, LoyaltyTier, PointsTransaction
from utils.security_manager import security_manager, validate_security_json_input, rate_limit
from utils.loyalty_engine import get_loyalty_engine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

crm_bp = Blueprint('crm', __name__)

@crm_bp.route('/')
@login_required
def index():
    """CRM main page"""
    return render_template('crm/index.html')

@crm_bp.route('/create', methods=['POST'])
@login_required
@validate_security_json_input(['name', 'mobile'])
@rate_limit(limit=20, window=60)
def create_customer():
    """Create new customer"""
    try:
        data = g.sanitized_json
        
        # Validate required fields
        if not data.get('name') or not data.get('mobile'):
            return jsonify({
                'success': False,
                'message': 'Name and mobile number are required'
            }), 400
        
        # Validate mobile number format
        mobile = data.get('mobile', '').replace(' ', '').replace('-', '')
        if not mobile.isdigit() or len(mobile) != 10:
            return jsonify({
                'success': False,
                'message': 'Invalid mobile number format'
            }), 400
        
        # Check if customer already exists
        existing_customer = Customer.get_by_mobile(mobile)
        if existing_customer:
            return jsonify({
                'success': False,
                'message': 'Customer with this mobile number already exists'
            }), 400
        
        # Check email if provided
        email = data.get('email', '').strip()
        if email:
            email_customer = Customer.get_by_email(email)
            if email_customer:
                return jsonify({
                    'success': False,
                    'message': 'Customer with this email already exists'
                }), 400
        
        # Create new customer
        customer = Customer(
            name=data.get('name').strip(),
            mobile=mobile,
            email=email if email else None,
            address=data.get('address', '').strip(),
            city=data.get('city', '').strip(),
            state=data.get('state', '').strip(),
            postal_code=data.get('postal_code', '').strip(),
            loyalty_tier_id=data.get('loyalty_tier_id'),
            created_by=current_user.id
        )
        
        # Set dates if provided
        if data.get('date_of_birth'):
            try:
                customer.date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                pass  # Invalid date, skip
        
        if data.get('anniversary_date'):
            try:
                customer.anniversary_date = datetime.strptime(data.get('anniversary_date'), '%Y-%m-%d').date()
            except ValueError:
                pass  # Invalid date, skip
        
        db.session.add(customer)
        db.session.commit()
        
        # Log customer creation
        security_manager.log_security_event(
            'CUSTOMER_CREATED',
            f'Customer {customer.name_decrypted} created by {current_user.username}'
        )
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict(),
            'message': 'Customer created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to create customer'
        }), 500

@crm_bp.route('/list', methods=['GET'])
@login_required
@rate_limit(limit=50, window=60)
def get_customers():
    """Get customers list with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 per page
        search = request.args.get('search', '').strip()
        tier_filter = request.args.get('tier', '')
        status_filter = request.args.get('status', '')
        
        # Start with base query
        query = Customer.query
        
        # Apply search filter
        if search:
            # This is a simplified search - in production, you'd want more sophisticated search
            encrypted_search = security_manager.encrypt_field(search)
            query = query.filter(
                db.or_(
                    Customer._name.like(f'%{encrypted_search}%'),
                    Customer._mobile.like(f'%{encrypted_search}%'),
                    Customer._email.like(f'%{encrypted_search}%')
                )
            )
        
        # Apply tier filter
        if tier_filter.isdigit():
            query = query.filter_by(loyalty_tier_id=int(tier_filter))
        
        # Apply status filter
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
        
        # Order by most recent activity
        query = query.order_by(
            Customer.last_order_date.desc().nullslast(),
            Customer.created_at.desc()
        )
        
        # Paginate
        customers = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Prepare response data
        customers_data = []
        for customer in customers.items:
            # Apply data masking based on user role
            customer_dict = customer.to_dict(
                mask_data=True, 
                user_role=current_user.role
            )
            customers_data.append(customer_dict)
        
        return jsonify({
            'success': True,
            'customers': customers_data,
            'pagination': {
                'page': customers.page,
                'pages': customers.pages,
                'per_page': customers.per_page,
                'total': customers.total,
                'has_prev': customers.has_prev,
                'has_next': customers.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting customers: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customers'
        }), 500

@crm_bp.route('/<int:customer_id>', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer(customer_id):
    """Get customer details"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        # Get customer with related data
        customer_data = customer.to_dict(
            mask_data=current_user.role not in ['admin', 'manager'],
            user_role=current_user.role
        )
        
        # Add loyalty summary
        loyalty_engine = get_loyalty_engine()
        loyalty_summary = loyalty_engine.get_customer_summary(customer)
        customer_data['loyalty_summary'] = loyalty_summary
        
        return jsonify({
            'success': True,
            'customer': customer_data
        })
        
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customer'
        }), 500

@crm_bp.route('/<int:customer_id>/update', methods=['PUT'])
@login_required
@validate_security_json_input([])
@rate_limit(limit=20, window=60)
def update_customer(customer_id):
    """Update customer information"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = g.sanitized_json
        
        # Update fields if provided
        if 'name' in data and data['name'].strip():
            customer.name = data['name'].strip()
        
        if 'email' in data:
            email = data['email'].strip() if data['email'] else None
            if email and email != customer.email_decrypted:
                # Check if email is already used by another customer
                existing_customer = Customer.get_by_email(email)
                if existing_customer and existing_customer.id != customer_id:
                    return jsonify({
                        'success': False,
                        'message': 'Email already exists'
                    }), 400
            customer.email = email
        
        if 'mobile' in data and data['mobile'].strip():
            mobile = data['mobile'].replace(' ', '').replace('-', '')
            if not mobile.isdigit() or len(mobile) != 10:
                return jsonify({
                    'success': False,
                    'message': 'Invalid mobile number format'
                }), 400
            
            if mobile != customer.mobile_decrypted:
                # Check if mobile is already used by another customer
                existing_customer = Customer.get_by_mobile(mobile)
                if existing_customer and existing_customer.id != customer_id:
                    return jsonify({
                        'success': False,
                        'message': 'Mobile number already exists'
                    }), 400
            customer.mobile = mobile
        
        if 'address' in data:
            customer.address = data['address'].strip() if data['address'] else None
        
        if 'city' in data:
            customer.city = data['city'].strip() if data['city'] else None
        
        if 'state' in data:
            customer.state = data['state'].strip() if data['state'] else None
        
        if 'postal_code' in data:
            customer.postal_code = data['postal_code'].strip() if data['postal_code'] else None
        
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                customer.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date of birth format'
                }), 400
        
        if 'anniversary_date' in data and data['anniversary_date']:
            try:
                customer.anniversary_date = datetime.strptime(data['anniversary_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid anniversary date format'
                }), 400
        
        if 'loyalty_tier_id' in data:
            customer.loyalty_tier_id = data['loyalty_tier_id']
        
        if 'preferred_language' in data:
            customer.preferred_language = data['preferred_language']
        
        if 'communication_preferences' in data:
            customer.communication_preferences = data['communication_preferences']
        
        if 'is_active' in data and current_user.role in ['admin', 'manager']:
            customer.is_active = data['is_active']
        
        db.session.commit()
        
        # Log customer update
        security_manager.log_security_event(
            'CUSTOMER_UPDATED',
            f'Customer {customer.name_decrypted} updated by {current_user.username}'
        )
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict(
                mask_data=current_user.role not in ['admin', 'manager'],
                user_role=current_user.role
            ),
            'message': 'Customer updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update customer'
        }), 500

@crm_bp.route('/<int:customer_id>/points/add', methods=['POST'])
@login_required
@validate_security_json_input(['points', 'description'])
@rate_limit(limit=20, window=60)
def add_points(customer_id):
    """Add points to customer account"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = g.sanitized_json
        
        points = int(data.get('points', 0))
        description = data.get('description', '').strip()
        
        if points <= 0:
            return jsonify({
                'success': False,
                'message': 'Points must be greater than 0'
            }), 400
        
        if not description:
            return jsonify({
                'success': False,
                'message': 'Description is required'
            }), 400
        
        # Add points using loyalty engine
        loyalty_engine = get_loyalty_engine()
        transaction = loyalty_engine.award_points(
            customer, 
            0,  # No order amount for manual points
            None, 
            description
        )
        
        if transaction:
            # Log points addition
            security_manager.log_security_event(
                'POINTS_ADDED',
                f'{points} points added to customer {customer.name_decrypted} by {current_user.username}'
            )
            
            return jsonify({
                'success': True,
                'transaction': transaction.to_dict(),
                'customer': {
                    'id': customer.id,
                    'current_points': customer.current_points,
                    'total_points_earned': customer.total_points_earned
                },
                'message': f'{points} points added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to add points'
            }), 500
        
    except Exception as e:
        logger.error(f"Error adding points to customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to add points'
        }), 500

@crm_bp.route('/<int:customer_id>/points/redeem', methods=['POST'])
@login_required
@validate_security_json_input(['points', 'description'])
@rate_limit(limit=20, window=60)
def redeem_points(customer_id):
    """Redeem points from customer account"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        data = g.sanitized_json
        
        points = int(data.get('points', 0))
        description = data.get('description', '').strip()
        
        if points <= 0:
            return jsonify({
                'success': False,
                'message': 'Points must be greater than 0'
            }), 400
        
        if not description:
            return jsonify({
                'success': False,
                'message': 'Description is required'
            }), 400
        
        # Check if customer has enough points
        if customer.current_points < points:
            return jsonify({
                'success': False,
                'message': f'Insufficient points. Customer has {customer.current_points} points'
            }), 400
        
        # Redeem points using loyalty engine
        loyalty_engine = get_loyalty_engine()
        transaction = loyalty_engine.redeem_points(
            customer, 
            points, 
            description
        )
        
        if transaction:
            # Log points redemption
            security_manager.log_security_event(
                'POINTS_REDEEMED',
                f'{points} points redeemed from customer {customer.name_decrypted} by {current_user.username}'
            )
            
            return jsonify({
                'success': True,
                'transaction': transaction.to_dict(),
                'customer': {
                    'id': customer.id,
                    'current_points': customer.current_points,
                    'total_points_redeemed': customer.total_points_redeemed
                },
                'message': f'{points} points redeemed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to redeem points'
            }), 500
        
    except Exception as e:
        logger.error(f"Error redeeming points from customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to redeem points'
        }), 500

@crm_bp.route('/<int:customer_id>/transactions', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer_transactions(customer_id):
    """Get customer points transactions"""
    try:
        customer = Customer.query.get_or_404(customer_id)
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        transaction_type = request.args.get('type', '')
        
        # Get transactions
        transactions = PointsTransaction.get_customer_transactions(
            customer_id, 
            page=page, 
            per_page=per_page,
            transaction_type=transaction_type if transaction_type else None
        )
        
        return jsonify({
            'success': True,
            'transactions': [t.to_dict() for t in transactions.items],
            'pagination': {
                'page': transactions.page,
                'pages': transactions.pages,
                'per_page': transactions.per_page,
                'total': transactions.total,
                'has_prev': transactions.has_prev,
                'has_next': transactions.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting transactions for customer {customer_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve transactions'
        }), 500

@crm_bp.route('/tiers', methods=['GET'])
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

@crm_bp.route('/search', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def search_customers():
    """Search customers by name, mobile, or email"""
    try:
        search_term = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'Search term is required'
            }), 400
        
        # Search customers
        customers = Customer.search_customers(search_term, page=page, per_page=per_page)
        
        # Prepare response data
        customers_data = []
        for customer in customers.items:
            customer_dict = customer.to_dict(
                mask_data=current_user.role not in ['admin', 'manager'],
                user_role=current_user.role
            )
            customers_data.append(customer_dict)
        
        return jsonify({
            'success': True,
            'customers': customers_data,
            'search_term': search_term,
            'pagination': {
                'page': customers.page,
                'pages': customers.pages,
                'per_page': customers.per_page,
                'total': customers.total,
                'has_prev': customers.has_prev,
                'has_next': customers.has_next
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to search customers'
        }), 500

@crm_bp.route('/stats', methods=['GET'])
@login_required
@rate_limit(limit=30, window=60)
def get_customer_stats():
    """Get customer statistics"""
    try:
        # Get basic stats
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(is_active=True).count()
        
        # Get tier distribution
        tier_stats = db.session.query(
            LoyaltyTier.name,
            db.func.count(Customer.id).label('customer_count')
        ).join(
            Customer, LoyaltyTier.id == Customer.loyalty_tier_id
        ).filter(
            Customer.is_active == True
        ).group_by(LoyaltyTier.name).all()
        
        # Get points stats
        total_points_earned = db.session.query(
            db.func.sum(Customer.total_points_earned)
        ).filter(
            Customer.is_active == True
        ).scalar() or 0
        
        total_points_redeemed = db.session.query(
            db.func.sum(Customer.total_points_redeemed)
        ).filter(
            Customer.is_active == True
        ).scalar() or 0
        
        current_points_total = db.session.query(
            db.func.sum(Customer.current_points)
        ).filter(
            Customer.is_active == True
        ).scalar() or 0
        
        # Get recent registrations
        from datetime import timedelta
        recent_date = datetime.utcnow() - timedelta(days=30)
        recent_registrations = Customer.query.filter(
            Customer.created_at >= recent_date
        ).count()
        
        stats = {
            'total_customers': total_customers,
            'active_customers': active_customers,
            'inactive_customers': total_customers - active_customers,
            'recent_registrations': recent_registrations,
            'total_points_earned': total_points_earned,
            'total_points_redeemed': total_points_redeemed,
            'current_points_total': current_points_total,
            'tier_distribution': [
                {'tier': tier_name, 'count': count}
                for tier_name, count in tier_stats
            ]
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting customer stats: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve customer statistics'
        }), 500