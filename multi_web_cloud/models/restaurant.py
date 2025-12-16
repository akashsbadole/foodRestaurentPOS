"""
Enhanced restaurant-specific models with feature-aware capabilities
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from . import db
from .feature_aware_model import FeatureAwareModel


class RestaurantTable(FeatureAwareModel, db.Model):
    """Enhanced restaurant table model with feature-aware capabilities"""
    __tablename__ = 'restaurant_tables'
    
    # Feature requirements
    required_features = ['FEATURE_RESTAURANT_TABLES']
    optional_features = ['FEATURE_TABLE_RESERVATIONS', 'FEATURE_KITCHEN_STATIONS']
    retail_types = ['restaurant']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=4)
    min_capacity = db.Column(db.Integer, default=1)  # Minimum capacity for reservations
    max_capacity = db.Column(db.Integer, default=8)  # Maximum capacity with extensions
    status = db.Column(db.String(20), default='Available')  # Available, Occupied, Reserved, Maintenance, Cleaning
    table_type = db.Column(db.String(50), default='Standard')  # Standard, Booth, Private, Outdoor, Bar
    location = db.Column(db.String(100), nullable=True)  # Dining Area, Patio, Bar, Private Room
    section = db.Column(db.String(50), nullable=True)  # Section within location
    description = db.Column(db.Text, nullable=True)
    
    # Physical attributes
    x_position = db.Column(db.Float, nullable=True)  # Position on floor plan
    y_position = db.Column(db.Float, nullable=True)
    width = db.Column(db.Float, default=1.0)  # Table width on floor plan
    height = db.Column(db.Float, default=1.0)  # Table height on floor plan
    shape = db.Column(db.String(20), default='Rectangle')  # Rectangle, Circle, Square
    
    # Reservation settings
    reservable = db.Column(db.Boolean, default=True)
    reservation_advance_days = db.Column(db.Integer, default=30)
    min_reservation_duration = db.Column(db.Integer, default=30)  # minutes
    max_reservation_duration = db.Column(db.Integer, default=240)  # minutes
    
    # Merge/Split capabilities
    can_merge = db.Column(db.Boolean, default=False)
    merge_group_id = db.Column(db.String(50), nullable=True)  # Tables that can be merged together
    parent_table_id = db.Column(db.Integer, db.ForeignKey('restaurant_tables.id'), nullable=True)
    
    # Accessibility features
    wheelchair_accessible = db.Column(db.Boolean, default=False)
    near_entrance = db.Column(db.Boolean, default=False)
    quiet_area = db.Column(db.Boolean, default=False)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    # Relationships
    child_tables = db.relationship('RestaurantTable', backref=db.backref('parent_table', remote_side=[id]))
    reservations = db.relationship('TableReservation', backref='table', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, table_number: str, capacity: int = 4, **kwargs):
        self.table_number = table_number
        self.capacity = capacity
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def is_available(self) -> bool:
        """Check if table is currently available"""
        return self.status == 'Available'
    
    @property
    def is_occupied(self) -> bool:
        """Check if table is occupied"""
        return self.status == 'Occupied'
    
    @property
    def is_reserved(self) -> bool:
        return self.status == 'Reserved'
    
    @property
    def can_be_reserved(self) -> bool:
        """Check if table can be reserved"""
        return self.reservable and self.is_active
    
    def get_current_reservation(self) -> Optional['TableReservation']:
        """Get current active reservation for this table"""
        now = datetime.utcnow()
        return TableReservation.query.filter(
            TableReservation.table_id == self.id,
            TableReservation.status == 'Confirmed',
            TableReservation.start_time <= now,
            TableReservation.end_time > now
        ).first()
    
    def is_available_for_reservation(self, start_time: datetime, end_time: datetime) -> bool:
        """Check if table is available for reservation during time period"""
        if not self.can_be_reserved:
            return False
        
        # Check for conflicting reservations
        conflicting = TableReservation.query.filter(
            TableReservation.table_id == self.id,
            TableReservation.status.in_(['Confirmed', 'Pending']),
            db.or_(
                db.and_(TableReservation.start_time <= start_time, TableReservation.end_time > start_time),
                db.and_(TableReservation.start_time < end_time, TableReservation.end_time >= end_time),
                db.and_(TableReservation.start_time >= start_time, TableReservation.end_time <= end_time)
            )
        ).first()
        
        return conflicting is None
    
    def get_mergeable_tables(self) -> List['RestaurantTable']:
        """Get tables that can be merged with this table"""
        if not self.can_merge or not self.merge_group_id:
            return []
        
        return RestaurantTable.query.filter(
            RestaurantTable.merge_group_id == self.merge_group_id,
            RestaurantTable.id != self.id,
            RestaurantTable.is_active == True,
            RestaurantTable.can_merge == True
        ).all()
    
    def get_total_capacity_with_merges(self) -> int:
        """Get total capacity if table is merged with compatible tables"""
        total_capacity = self.capacity
        mergeable_tables = self.get_mergeable_tables()
        total_capacity += sum(table.capacity for table in mergeable_tables)
        return total_capacity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert table to dictionary"""
        return {
            'id': self.id,
            'table_number': self.table_number,
            'capacity': self.capacity,
            'min_capacity': self.min_capacity,
            'max_capacity': self.max_capacity,
            'status': self.status,
            'table_type': self.table_type,
            'location': self.location,
            'section': self.section,
            'description': self.description,
            'x_position': self.x_position,
            'y_position': self.y_position,
            'width': self.width,
            'height': self.height,
            'shape': self.shape,
            'reservable': self.reservable,
            'can_merge': self.can_merge,
            'merge_group_id': self.merge_group_id,
            'wheelchair_accessible': self.wheelchair_accessible,
            'near_entrance': self.near_entrance,
            'quiet_area': self.quiet_area,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TableReservation(FeatureAwareModel, db.Model):
    """Table reservation model"""
    __tablename__ = 'table_reservations'
    
    # Feature requirements
    required_features = ['FEATURE_TABLE_RESERVATIONS']
    retail_types = ['restaurant']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    reservation_code = db.Column(db.String(20), unique=True, nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('restaurant_tables.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_email = db.Column(db.String(100), nullable=True)
    party_size = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Cancelled, Completed, No-Show
    
    # Reservation details
    special_requests = db.Column(db.Text, nullable=True)
    occasion = db.Column(db.String(50), nullable=True)  # Birthday, Anniversary, Business, etc.
    notes = db.Column(db.Text, nullable=True)
    
    # Deposit and payment
    requires_deposit = db.Column(db.Boolean, default=False)
    deposit_amount = db.Column(db.Float, default=0.0)
    deposit_paid = db.Column(db.Boolean, default=False)
    deposit_payment_id = db.Column(db.String(36), nullable=True)
    
    # Confirmation
    confirmed_at = db.Column(db.DateTime, nullable=True)
    confirmed_by = db.Column(db.String(36), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancelled_by = db.Column(db.String(36), nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    def __init__(self, reservation_code: str, table_id: int, customer_name: str, 
                 party_size: int, start_time: datetime, end_time: datetime, **kwargs):
        self.reservation_code = reservation_code
        self.table_id = table_id
        self.customer_name = customer_name
        self.party_size = party_size
        self.start_time = start_time
        self.end_time = end_time
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @property
    def duration_minutes(self) -> int:
        """Get reservation duration in minutes"""
        return int((self.end_time - self.start_time).total_seconds() / 60)
    
    @property
    def is_active(self) -> bool:
        """Check if reservation is currently active"""
        now = datetime.utcnow()
        return self.status == 'Confirmed' and self.start_time <= now <= self.end_time
    
    @property
    def is_upcoming(self) -> bool:
        """Check if reservation is upcoming"""
        return self.status == 'Confirmed' and datetime.utcnow() < self.start_time
    
    def confirm(self, user_id: Optional[str] = None) -> bool:
        """Confirm reservation"""
        try:
            self.status = 'Confirmed'
            self.confirmed_at = datetime.utcnow()
            self.confirmed_by = user_id
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def cancel(self, reason: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """Cancel reservation"""
        try:
            self.status = 'Cancelled'
            self.cancelled_at = datetime.utcnow()
            self.cancelled_by = user_id
            self.cancellation_reason = reason
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reservation to dictionary"""
        return {
            'id': self.id,
            'reservation_code': self.reservation_code,
            'table_id': self.table_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'party_size': self.party_size,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'special_requests': self.special_requests,
            'occasion': self.occasion,
            'notes': self.notes,
            'requires_deposit': self.requires_deposit,
            'deposit_amount': self.deposit_amount,
            'deposit_paid': self.deposit_paid,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'cancellation_reason': self.cancellation_reason,
            'is_active': self.is_active,
            'is_upcoming': self.is_upcoming,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KitchenStation(FeatureAwareModel, db.Model):
    """Kitchen station model for restaurant operations"""
    __tablename__ = 'kitchen_stations'
    
    # Feature requirements
    required_features = ['FEATURE_KITCHEN_STATIONS']
    retail_types = ['restaurant']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    station_type = db.Column(db.String(50), default='Preparation')  # Preparation, Cooking, Grilling, Fry, Bar, Dessert
    printer_name = db.Column(db.String(100), nullable=True)  # KOT printer for this station
    
    # Display settings
    display_order = db.Column(db.Integer, default=0)  # Order in which stations are displayed
    color_code = db.Column(db.String(7), default='#000000')  # Hex color for UI
    icon = db.Column(db.String(50), nullable=True)  # Icon class or emoji
    
    # Status and settings
    is_active = db.Column(db.Boolean, default=True)
    auto_complete_items = db.Column(db.Boolean, default=False)  # Auto-complete items after certain time
    prep_time_alert_minutes = db.Column(db.Integer, default=15)  # Alert when items take longer than this
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    def __init__(self, name: str, display_name: str, **kwargs):
        self.name = name
        self.display_name = display_name
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def get_active_items(self) -> List['OrderItem']:
        """Get active items for this station"""
        from .order import OrderItem
        from .menu_item import MenuItem
        
        return db.session.query(OrderItem).join(MenuItem).filter(
            MenuItem.kitchen_station == self.name,
            OrderItem.status.in_(['Pending', 'In Progress'])
        ).order_by(OrderItem.created_at).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert kitchen station to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'station_type': self.station_type,
            'printer_name': self.printer_name,
            'display_order': self.display_order,
            'color_code': self.color_code,
            'icon': self.icon,
            'is_active': self.is_active,
            'auto_complete_items': self.auto_complete_items,
            'prep_time_alert_minutes': self.prep_time_alert_minutes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RestaurantShift(FeatureAwareModel, db.Model):
    """Restaurant shift management model"""
    __tablename__ = 'restaurant_shifts'
    
    # Feature requirements
    required_features = ['FEATURE_SHIFT_MANAGEMENT']
    retail_types = ['restaurant']
    model_category = 'retail_type'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Breakfast, Lunch, Dinner, Late Night
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    days_of_week = db.Column(db.String(20), nullable=False)  # Comma-separated days: 1,2,3,4,5
    
    # Staffing
    manager_required = db.Column(db.Boolean, default=True)
    min_waitstaff = db.Column(db.Integer, default=2)
    min_kitchen_staff = db.Column(db.Integer, default=2)
    max_waitstaff = db.Column(db.Integer, default=8)
    max_kitchen_staff = db.Column(db.Integer, default=6)
    
    # Operations
    auto_open_tables = db.Column(db.Boolean, default=True)
    auto_close_shift = db.Column(db.Boolean, default=False)
    shift_change_minutes = db.Column(db.Integer, default=30)  # Minutes before/after for shift change
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    tenant_id = db.Column(db.String(36), nullable=False, default='default')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(36), nullable=True)
    
    def __init__(self, name: str, start_time, end_time, days_of_week: str, **kwargs):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.days_of_week = days_of_week
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def is_active_now(self) -> bool:
        """Check if shift is currently active"""
        from datetime import time
        
        now = datetime.now()
        current_time = now.time()
        current_day = str(now.isoweekday())
        
        # Check if today is in shift days
        if current_day not in self.days_of_week.split(','):
            return False
        
        # Check if current time is within shift hours
        if self.start_time <= self.end_time:
            # Same day shift (e.g., 9:00 AM to 5:00 PM)
            return self.start_time <= current_time <= self.end_time
        else:
            # Overnight shift (e.g., 10:00 PM to 6:00 AM)
            return current_time >= self.start_time or current_time <= self.end_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shift to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'days_of_week': self.days_of_week,
            'manager_required': self.manager_required,
            'min_waitstaff': self.min_waitstaff,
            'min_kitchen_staff': self.min_kitchen_staff,
            'max_waitstaff': self.max_waitstaff,
            'max_kitchen_staff': self.max_kitchen_staff,
            'auto_open_tables': self.auto_open_tables,
            'auto_close_shift': self.auto_close_shift,
            'shift_change_minutes': self.shift_change_minutes,
            'is_active': self.is_active,
            'is_active_now': self.is_active_now(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }