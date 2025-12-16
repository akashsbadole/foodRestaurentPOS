"""
Restaurant-specific routes with feature-aware capabilities
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models import db
from models.restaurant import RestaurantTable, TableReservation, KitchenStation, RestaurantShift
from services.restaurant_service import create_restaurant_service
from utils.feature_flag_manager import feature_manager
from utils.tenant_query_manager import get_current_tenant_id

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')


def get_restaurant_service():
    """Get restaurant service instance with current tenant context"""
    tenant_id = get_current_tenant_id()
    return create_restaurant_service(tenant_id)


def feature_required(feature_name: str):
    """Decorator to check if feature is enabled"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            tenant_id = get_current_tenant_id()
            if not feature_manager.is_enabled(feature_name, tenant_id):
                if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
                    return jsonify({
                        'success': False,
                        'error': f'Feature {feature_name} is not enabled'
                    }), 403
                flash(f'Feature {feature_name} is not enabled', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


# Table Management Routes

@restaurant_bp.route('/tables')
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def tables_management():
    """Enhanced tables management page"""
    service = get_restaurant_service()
    
    # Get all tables
    tables = RestaurantTable.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).order_by(RestaurantTable.location, RestaurantTable.table_number).all()
    
    # Get table statistics
    stats = service.get_table_statistics()
    
    return render_template('restaurant/tables/index.html',
                        tables=tables,
                        stats=stats)


@restaurant_bp.route('/tables/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def add_table():
    """Add new restaurant table"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            service = get_restaurant_service()
            
            success, table, message = service.create_table(
                table_number=data.get('table_number'),
                capacity=int(data.get('capacity', 4)),
                location=data.get('location'),
                description=data.get('description'),
                table_type=data.get('table_type', 'Standard'),
                reservable=data.get('reservable', True),
                can_merge=data.get('can_merge', False),
                merge_group_id=data.get('merge_group_id'),
                wheelchair_accessible=data.get('wheelchair_accessible', False),
                near_entrance=data.get('near_entrance', False),
                quiet_area=data.get('quiet_area', False),
                x_position=data.get('x_position'),
                y_position=data.get('y_position'),
                width=data.get('width', 1.0),
                height=data.get('height', 1.0),
                shape=data.get('shape', 'Rectangle')
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'table': table.to_dict(),
                    'message': message
                })
            else:
                return jsonify({'success': False, 'message': message}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('restaurant/tables/add.html')


@restaurant_bp.route('/tables/<int:table_id>/edit', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def edit_table(table_id):
    """Edit restaurant table"""
    table = RestaurantTable.query.get_or_404(table_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update table fields
            for field in ['table_number', 'capacity', 'location', 'description', 'table_type',
                         'reservable', 'can_merge', 'merge_group_id', 'wheelchair_accessible',
                         'near_entrance', 'quiet_area', 'x_position', 'y_position', 'width', 'height', 'shape']:
                if field in data:
                    setattr(table, field, data[field))
            
            table.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'table': table.to_dict(),
                'message': 'Table updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('restaurant/tables/edit.html', table=table)


@restaurant_bp.route('/tables/<int:table_id>/status', methods=['POST'])
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def update_table_status(table_id):
    """Update table status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        service = get_restaurant_service()
        success, message = service.update_table_status(
            table_id=table_id,
            new_status=new_status,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@restaurant_bp.route('/tables/suggest')
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def suggest_tables():
    """Suggest tables for party size"""
    try:
        party_size = int(request.args.get('party_size', 1))
        location = request.args.get('location')
        
        service = get_restaurant_service()
        suggested_tables = service.suggest_tables(party_size, location)
        
        return jsonify({
            'success': True,
            'tables': [table.to_dict() for table in suggested_tables]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@restaurant_bp.route('/tables/floor_plan')
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def floor_plan():
    """Restaurant floor plan view"""
    tables = RestaurantTable.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).all()
    
    return render_template('restaurant/tables/floor_plan.html', tables=tables)


# Reservation Routes

@restaurant_bp.route('/reservations')
@login_required
@feature_required('FEATURE_TABLE_RESERVATIONS')
def reservations():
    """Reservations management page"""
    date_filter = request.args.get('date', datetime.utcnow().date().isoformat())
    
    try:
        filter_date = datetime.fromisoformat(date_filter).date()
    except ValueError:
        filter_date = datetime.utcnow().date()
    
    # Get reservations for the selected date
    start_of_day = datetime.combine(filter_date, datetime.min.time())
    end_of_day = datetime.combine(filter_date, datetime.max.time())
    
    reservations = TableReservation.query.filter(
        TableReservation.tenant_id == get_current_tenant_id(),
        TableReservation.start_time >= start_of_day,
        TableReservation.start_time <= end_of_day
    ).order_by(TableReservation.start_time).all()
    
    return render_template('restaurant/reservations/index.html',
                        reservations=reservations,
                        selected_date=filter_date)


@restaurant_bp.route('/reservations/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_TABLE_RESERVATIONS')
def add_reservation():
    """Add new reservation"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Generate unique reservation code
            reservation_code = f"RES{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            reservation = TableReservation(
                reservation_code=reservation_code,
                table_id=int(data['table_id']),
                customer_name=data['customer_name'],
                customer_phone=data.get('customer_phone'),
                customer_email=data.get('customer_email'),
                party_size=int(data['party_size']),
                start_time=datetime.fromisoformat(data['start_time']),
                end_time=datetime.fromisoformat(data['end_time']),
                special_requests=data.get('special_requests'),
                occasion=data.get('occasion'),
                notes=data.get('notes'),
                requires_deposit=data.get('requires_deposit', False),
                deposit_amount=float(data.get('deposit_amount', 0)),
                tenant_id=get_current_tenant_id(),
                created_by=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(reservation)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'reservation': reservation.to_dict(),
                'message': 'Reservation created successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    # Get available tables for reservation form
    tables = RestaurantTable.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True,
        reservable=True
    ).order_by(RestaurantTable.table_number).all()
    
    return render_template('restaurant/reservations/add.html', tables=tables)


@restaurant_bp.route('/reservations/<int:reservation_id>/confirm', methods=['POST'])
@login_required
@feature_required('FEATURE_TABLE_RESERVATIONS')
def confirm_reservation(reservation_id):
    """Confirm reservation"""
    try:
        reservation = TableReservation.query.get_or_404(reservation_id)
        success = reservation.confirm(current_user.id if current_user.is_authenticated else None)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reservation confirmed successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to confirm reservation'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@restaurant_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
@feature_required('FEATURE_TABLE_RESERVATIONS')
def cancel_reservation(reservation_id):
    """Cancel reservation"""
    try:
        data = request.get_json()
        reason = data.get('reason', '')
        
        reservation = TableReservation.query.get_or_404(reservation_id)
        success = reservation.cancel(
            reason=reason,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Reservation cancelled successfully'
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to cancel reservation'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# Kitchen Station Routes

@restaurant_bp.route('/kitchen/stations')
@login_required
@feature_required('FEATURE_KITCHEN_STATIONS')
def kitchen_stations():
    """Kitchen stations management page"""
    stations = KitchenStation.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).order_by(KitchenStation.display_order, KitchenStation.name).all()
    
    return render_template('restaurant/kitchen/stations.html', stations=stations)


@restaurant_bp.route('/kitchen/stations/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_KITCHEN_STATIONS')
def add_kitchen_station():
    """Add new kitchen station"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            station = KitchenStation(
                name=data['name'],
                display_name=data['display_name'],
                description=data.get('description'),
                station_type=data.get('station_type', 'Preparation'),
                printer_name=data.get('printer_name'),
                display_order=int(data.get('display_order', 0)),
                color_code=data.get('color_code', '#000000'),
                icon=data.get('icon'),
                auto_complete_items=data.get('auto_complete_items', False),
                prep_time_alert_minutes=int(data.get('prep_time_alert_minutes', 15)),
                tenant_id=get_current_tenant_id(),
                created_by=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(station)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'station': station.to_dict(),
                'message': 'Kitchen station created successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('restaurant/kitchen/add_station.html')


@restaurant_bp.route('/kitchen/display')
@login_required
@feature_required('FEATURE_KITCHEN_STATIONS')
def kitchen_display():
    """Enhanced kitchen display with station support"""
    service = get_restaurant_service()
    
    # Get all active stations
    stations = KitchenStation.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).order_by(KitchenStation.display_order, KitchenStation.name).all()
    
    # Get active orders for each station
    station_orders = {}
    for station in stations:
        orders = service.get_active_kot_orders(station.name)
        station_orders[station.name] = orders
    
    return render_template('restaurant/kitchen/display.html',
                        stations=stations,
                        station_orders=station_orders)


# Shift Management Routes

@restaurant_bp.route('/shifts')
@login_required
@feature_required('FEATURE_SHIFT_MANAGEMENT')
def shifts():
    """Shift management page"""
    shifts = RestaurantShift.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).order_by(RestaurantShift.start_time).all()
    
    return render_template('restaurant/shifts/index.html', shifts=shifts)


@restaurant_bp.route('/shifts/add', methods=['GET', 'POST'])
@login_required
@feature_required('FEATURE_SHIFT_MANAGEMENT')
def add_shift():
    """Add new shift"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            shift = RestaurantShift(
                name=data['name'],
                start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
                end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
                days_of_week=','.join(data.get('days_of_week', [])),
                manager_required=data.get('manager_required', True),
                min_waitstaff=int(data.get('min_waitstaff', 2)),
                min_kitchen_staff=int(data.get('min_kitchen_staff', 2)),
                max_waitstaff=int(data.get('max_waitstaff', 8)),
                max_kitchen_staff=int(data.get('max_kitchen_staff', 6)),
                auto_open_tables=data.get('auto_open_tables', True),
                auto_close_shift=data.get('auto_close_shift', False),
                shift_change_minutes=int(data.get('shift_change_minutes', 30)),
                tenant_id=get_current_tenant_id(),
                created_by=current_user.id if current_user.is_authenticated else None
            )
            
            db.session.add(shift)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'shift': shift.to_dict(),
                'message': 'Shift created successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('restaurant/shifts/add.html')


# Configuration Routes

@restaurant_bp.route('/config')
@login_required
def restaurant_config():
    """Restaurant configuration page"""
    service = get_restaurant_service()
    config = service.get_restaurant_config()
    
    return render_template('restaurant/config.html', config=config)


@restaurant_bp.route('/config/update', methods=['POST'])
@login_required
def update_restaurant_config():
    """Update restaurant configuration"""
    try:
        data = request.get_json()
        service = get_restaurant_service()
        
        success, message = service.update_restaurant_config(
            config_updates=data,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# API Routes

@restaurant_bp.route('/api/tables/status')
@login_required
@feature_required('FEATURE_RESTAURANT_TABLES')
def api_tables_status():
    """Get tables status via API"""
    tables = RestaurantTable.query.filter_by(
        tenant_id=get_current_tenant_id(),
        is_active=True
    ).all()
    
    return jsonify({
        'success': True,
        'tables': [table.to_dict() for table in tables]
    })


@restaurant_bp.route('/api/reservations/check_availability')
@login_required
@feature_required('FEATURE_TABLE_RESERVATIONS')
def check_availability():
    """Check table availability for reservation"""
    try:
        table_id = int(request.args.get('table_id'))
        start_time = datetime.fromisoformat(request.args.get('start_time'))
        end_time = datetime.fromisoformat(request.args.get('end_time'))
        
        table = RestaurantTable.query.get(table_id)
        if not table:
            return jsonify({'success': False, 'message': 'Table not found'}), 404
        
        available = table.is_available_for_reservation(start_time, end_time)
        
        return jsonify({
            'success': True,
            'available': available,
            'table': table.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@restaurant_bp.route('/api/kitchen/performance')
@login_required
@feature_required('FEATURE_KITCHEN_STATIONS')
def kitchen_performance():
    """Get kitchen performance metrics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        service = get_restaurant_service()
        metrics = service.get_kitchen_performance_metrics(start_date, end_date)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500