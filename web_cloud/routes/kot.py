from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models import db, Order, OrderItem, MenuItem, Table
from datetime import datetime, timedelta

kot_bp = Blueprint('kot', __name__)

@kot_bp.route('/')
@login_required
def index():
    """KOT dashboard page"""
    # Get active orders (not completed or cancelled)
    active_orders = Order.query.filter(
        Order.status.in_(['New', 'In Progress', 'Ready'])
    ).order_by(Order.created_at.desc()).all()
    
    # Get completed orders in last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_orders = Order.query.filter(
        Order.status == 'Completed',
        Order.created_at >= yesterday
    ).order_by(Order.created_at.desc()).limit(20).all()
    
    return render_template('kot/index.html', 
                        active_orders=active_orders, 
                        recent_orders=recent_orders)

@kot_bp.route('/active')
@login_required
def active_orders():
    """Get active orders via AJAX"""
    orders = Order.query.filter(
        Order.status.in_(['New', 'In Progress', 'Ready'])
    ).order_by(Order.created_at.desc()).all()
    
    order_data = []
    for order in orders:
        items = OrderItem.query.filter_by(order_id=order.id).all()
        
        order_dict = order.to_dict()
        order_dict['items'] = [
            {
                'id': item.id,
                'item_name': item.menu_item.name if item.menu_item else 'Unknown',
                'quantity': item.quantity,
                'status': item.status,
                'special_instructions': item.special_instructions
            }
            for item in items
        ]
        
        if order.table_id:
            table = Table.query.get(order.table_id)
            order_dict['table_number'] = table.table_number if table else None
        
        order_data.append(order_dict)
    
    return jsonify({
        'success': True,
        'orders': order_data
    })

@kot_bp.route('/update_item_status', methods=['POST'])
@login_required
def update_item_status():
    """Update KOT item status via AJAX"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        status = data.get('status')
        
        valid_statuses = ['Pending', 'In Progress', 'Ready', 'Completed', 'Cancelled']
        if status not in valid_statuses:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
        order_item = OrderItem.query.get(item_id)
        if not order_item:
            return jsonify({'success': False, 'message': 'Order item not found'}), 404
        
        order_item.status = status
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Item status updated to {status}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@kot_bp.route('/print/<int:order_id>')
@login_required
def print_kot(order_id):
    """Print KOT for order"""
    order = Order.query.get_or_404(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()
    
    return render_template('kot/print.html', order=order, items=items)

@kot_bp.route('/kitchen_display')
@login_required
def kitchen_display():
    """Kitchen display for monitors"""
    active_orders = Order.query.filter(
        Order.status.in_(['New', 'In Progress'])
    ).order_by(Order.created_at.desc()).all()
    
    # Group by status for display
    pending_orders = [o for o in active_orders if o.status == 'New']
    progress_orders = [o for o in active_orders if o.status == 'In Progress']
    ready_orders = [o for o in active_orders if o.status == 'Ready']
    
    return render_template('kot/kitchen_display.html',
                        pending_orders=pending_orders,
                        progress_orders=progress_orders,
                        ready_orders=ready_orders)
