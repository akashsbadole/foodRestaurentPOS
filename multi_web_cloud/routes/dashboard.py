from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Order, MenuItem, Table, Category, Settings, Customer, LoyaltyTier, PointsTransaction
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Dashboard home page"""
    # Get dashboard statistics
    stats = get_dashboard_stats()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Get low stock items
    low_stock_items = MenuItem.query.filter_by(is_low_stock=True, is_active=True).limit(5).all()
    
    # Get available tables
    available_tables = Table.query.filter_by(status='Available', is_active=True).count()
    
    # Get CRM and loyalty stats
    crm_stats = get_crm_stats()
    loyalty_stats = get_loyalty_stats()
    
    # Get recent customers
    recent_customers = Customer.query.order_by(Customer.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html',
                        stats=stats,
                        recent_orders=recent_orders,
                        recent_customers=recent_customers,
                        low_stock_items=low_stock_items,
                        available_tables=available_tables,
                        crm_stats=crm_stats,
                        loyalty_stats=loyalty_stats)

@dashboard_bp.route('/stats')
@login_required
def get_stats():
    """Get dashboard statistics via AJAX"""
    stats = get_dashboard_stats()
    return jsonify(stats)

def get_dashboard_stats():
    """Get dashboard statistics"""
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Today's stats
    today_orders = Order.query.filter(Order.created_at >= datetime.combine(today, datetime.min.time())).count()
    today_revenue = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= datetime.combine(today, datetime.min.time())
    ).scalar() or 0
    
    # This week's stats
    week_orders = Order.query.filter(Order.created_at >= datetime.combine(week_ago, datetime.min.time())).count()
    week_revenue = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= datetime.combine(week_ago, datetime.min.time())
    ).scalar() or 0
    
    # This month's stats
    month_orders = Order.query.filter(Order.created_at >= datetime.combine(month_ago, datetime.min.time())).count()
    month_revenue = db.session.query(db.func.sum(Order.grand_total)).filter(
        Order.created_at >= datetime.combine(month_ago, datetime.min.time())
    ).scalar() or 0
    
    # Order status breakdown
    order_stats = {}
    for status in ['New', 'In Progress', 'Ready', 'Completed', 'Cancelled']:
        count = Order.query.filter_by(status=status).count()
        order_stats[status.lower().replace(' ', '_')] = count
    
    # Menu and table stats
    total_menu_items = MenuItem.query.filter_by(is_active=True).count()
    total_categories = Category.query.filter_by(is_active=True).count()
    total_tables = Table.query.count()
    
    return {
        'today': {
            'orders': today_orders,
            'revenue': float(today_revenue)
        },
        'week': {
            'orders': week_orders,
            'revenue': float(week_revenue)
        },
        'month': {
            'orders': month_orders,
            'revenue': float(month_revenue)
        },
        'orders': order_stats,
        'menu': {
            'items': total_menu_items,
            'categories': total_categories
        },
        'tables': {
            'total': total_tables,
            'available': Table.query.filter_by(status='Available', is_active=True).count()
        }
    }

def get_crm_stats():
    """Get CRM statistics"""
    try:
        # Total customers
        total_customers = Customer.query.count()
        
        # New customers this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_customers_month = Customer.query.filter(
            Customer.created_at >= month_start
        ).count()
        
        return {
            'total_customers': total_customers,
            'new_customers_month': new_customers_month
        }
    except Exception as e:
        return {
            'total_customers': 0,
            'new_customers_month': 0
        }

def get_loyalty_stats():
    """Get loyalty program statistics"""
    try:
        # Get tier distribution
        tier_distribution = {}
        tiers = LoyaltyTier.query.all()
        
        for tier in tiers:
            count = Customer.query.filter(Customer.tier == tier.name).count()
            tier_distribution[tier.name.lower()] = count
        
        # Get points issued today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        points_issued_today = PointsTransaction.query.filter(
            PointsTransaction.transaction_type == 'earned',
            PointsTransaction.created_at >= today_start
        ).with_entities(db.func.sum(PointsTransaction.points)).scalar() or 0
        
        points_redeemed_today = PointsTransaction.query.filter(
            PointsTransaction.transaction_type == 'redeemed',
            PointsTransaction.created_at >= today_start
        ).with_entities(db.func.sum(PointsTransaction.points)).scalar() or 0
        
        # Get active members
        active_members = Customer.query.filter(Customer.points_earned > 0).count()
        
        return {
            'total_members': active_members,
            'active_members': active_members,
            'points_issued_today': int(points_issued_today),
            'points_redeemed_today': int(points_redeemed_today),
            'tier_distribution': tier_distribution
        }
    except Exception as e:
        return {
            'total_members': 0,
            'active_members': 0,
            'points_issued_today': 0,
            'points_redeemed_today': 0,
            'tier_distribution': {}
        }