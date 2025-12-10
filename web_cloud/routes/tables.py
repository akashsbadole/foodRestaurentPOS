from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Table, Order

tables_bp = Blueprint('tables', __name__)

@tables_bp.route('/')
@login_required
def index():
    """Tables management page"""
    tables = Table.query.order_by(Table.table_number).all()
    
    # Get table statistics
    total_tables = len(tables)
    available_tables = len([t for t in tables if t.is_available])
    occupied_tables = len([t for t in tables if not t.is_available])
    
    return render_template('tables/index.html', 
                        tables=tables,
                        total_tables=total_tables,
                        available_tables=available_tables,
                        occupied_tables=occupied_tables)

@tables_bp.route('/add', methods=['POST'])
@login_required
def add_table():
    """Add new table"""
    try:
        data = request.get_json()
        table_number = data.get('table_number', '').strip()
        capacity = data.get('capacity', type=int)
        
        if not table_number or not capacity:
            return jsonify({'success': False, 'message': 'Table number and capacity are required'}), 400
        
        if Table.query.filter_by(table_number=table_number).first():
            return jsonify({'success': False, 'message': 'Table number already exists'}), 400
        
        table = Table(table_number=table_number, capacity=capacity)
        db.session.add(table)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'table': table.to_dict(),
            'message': 'Table added successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@tables_bp.route('/update', methods=['POST'])
@login_required
def update_table():
    """Update table"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        table_number = data.get('table_number', '').strip()
        capacity = data.get('capacity', type=int)
        
        if not table_id or not table_number or not capacity:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        table = Table.query.get(table_id)
        if not table:
            return jsonify({'success': False, 'message': 'Table not found'}), 404
        
        # Check if table number already exists for another table
        existing = Table.query.filter_by(table_number=table_number).first()
        if existing and existing.id != table_id:
            return jsonify({'success': False, 'message': 'Table number already exists'}), 400
        
        table.table_number = table_number
        table.capacity = capacity
        db.session.commit()
        
        return jsonify({
            'success': True,
            'table': table.to_dict(),
            'message': 'Table updated successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@tables_bp.route('/delete', methods=['POST'])
@login_required
def delete_table():
    """Delete table"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        
        if not table_id:
            return jsonify({'success': False, 'message': 'Table ID required'}), 400
        
        table = Table.query.get(table_id)
        if not table:
            return jsonify({'success': False, 'message': 'Table not found'}), 404
        
        # Check if table has active orders
        active_orders = Order.query.filter_by(table_id=table_id, status='In Progress').count()
        if active_orders > 0:
            return jsonify({
                'success': False, 
                'message': 'Cannot delete table with active orders'
            }), 400
        
        db.session.delete(table)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Table deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@tables_bp.route('/toggle_status', methods=['POST'])
@login_required
def toggle_status():
    """Toggle table availability"""
    try:
        data = request.get_json()
        table_id = data.get('table_id')
        
        if not table_id:
            return jsonify({'success': False, 'message': 'Table ID required'}), 400
        
        table = Table.query.get(table_id)
        if not table:
            return jsonify({'success': False, 'message': 'Table not found'}), 404
        
        table.is_available = not table.is_available
        db.session.commit()
        
        status = 'available' if table.is_available else 'occupied'
        
        return jsonify({
            'success': True,
            'table': table.to_dict(),
            'message': f'Table marked as {status}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@tables_bp.route('/api/status')
@login_required
def api_status():
    """Get tables status via AJAX"""
    tables = Table.query.order_by(Table.table_number).all()
    
    return jsonify({
        'success': True,
        'tables': [table.to_dict() for table in tables]
    })
