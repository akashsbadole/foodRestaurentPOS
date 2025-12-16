from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class EnhancedOrder(FeatureAwareModel):
    """Enhanced order model for multi-retail workflows"""
    __tablename__ = 'enhanced_orders'
    
    # Feature requirements
    required_features = ['FEATURE_ENHANCED_ORDERS']
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Order classification
    order_type = db.Column(db.String(20), default='Sale')  # Sale, Return, Exchange, Quote, Layaway
    order_subtype = db.Column(db.String(20), nullable=True)  # DineIn, Takeaway, Delivery, Pickup, Shipping
    retail_type = db.Column(db.String(20), nullable=True)  # Restaurant, Retail, Service, E-commerce
    
    # Customer information
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    customer_email = db.Column(db.String(100), nullable=True)
    
    # Conditional table management (restaurant-specific)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    covers = db.Column(db.Integer, nullable=True)
    server_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Order timing
    order_date = db.Column(db.Date, nullable=False, default=date.today)
    order_time = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_time = db.Column(db.DateTime, nullable=True)  # Estimated completion/delivery time
    completed_time = db.Column(db.DateTime, nullable=True)
    
    # Order status
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Preparing, Ready, Completed, Cancelled
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    
    # Financial information
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    discount_amount = db.Column(db.Numeric(12, 2), default=0)
    service_charge = db.Column(db.Numeric(10, 2), default=0)
    delivery_charge = db.Column(db.Numeric(10, 2), default=0)
    tip_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    
    # Payment information
    payment_status = db.Column(db.String(20), default='Unpaid')  # Unpaid, Partial, Paid, Refunded
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    
    # Delivery information (for delivery orders)
    delivery_address = db.Column(db.Text, nullable=True)
    delivery_instructions = db.Column(db.Text, nullable=True)
    delivery_partner = db.Column(db.String(50), nullable=True)
    delivery_tracking = db.Column(db.String(100), nullable=True)
    
    # Order notes
    order_notes = db.Column(db.Text, nullable=True)
    kitchen_notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    source = db.Column(db.String(20), default='POS')  # POS, Online, Mobile, Phone, ThirdParty
    device_id = db.Column(db.String(50), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    customer = db.relationship('Customer', backref='enhanced_orders')
    table = db.relationship('Table', backref='enhanced_orders')
    server = db.relationship('User', foreign_keys=[server_id], backref='served_orders')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_enhanced_orders')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_enhanced_orders')
    items = db.relationship('EnhancedOrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('EnhancedPayment', backref='order', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, order_number=None, order_type='Sale', order_subtype=None,
                 retail_type=None, customer_id=None, customer_name=None,
                 customer_phone=None, customer_email=None, table_id=None,
                 covers=None, server_id=None, order_date=None, order_time=None,
                 estimated_time=None, status='Pending', priority='Normal',
                 subtotal=0, tax_amount=0, discount_amount=0, service_charge=0,
                 delivery_charge=0, tip_amount=0, total_amount=0,
                 payment_status='Unpaid', payment_method=None, payment_reference=None,
                 delivery_address=None, delivery_instructions=None, delivery_partner=None,
                 delivery_tracking=None, order_notes=None, kitchen_notes=None,
                 internal_notes=None, source='POS', device_id=None, session_id=None,
                 tenant_id=None, created_by=None):
        self.order_number = order_number or self.generate_order_number()
        self.order_type = order_type
        self.order_subtype = order_subtype
        self.retail_type = retail_type
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.table_id = table_id
        self.covers = covers
        self.server_id = server_id
        self.order_date = order_date or date.today()
        self.order_time = order_time or datetime.utcnow()
        self.estimated_time = estimated_time
        self.status = status
        self.priority = priority
        self.subtotal = Decimal(str(subtotal))
        self.tax_amount = Decimal(str(tax_amount))
        self.discount_amount = Decimal(str(discount_amount))
        self.service_charge = Decimal(str(service_charge))
        self.delivery_charge = Decimal(str(delivery_charge))
        self.tip_amount = Decimal(str(tip_amount))
        self.total_amount = Decimal(str(total_amount))
        self.payment_status = payment_status
        self.payment_method = payment_method
        self.payment_reference = payment_reference
        self.delivery_address = delivery_address
        self.delivery_instructions = delivery_instructions
        self.delivery_partner = delivery_partner
        self.delivery_tracking = delivery_tracking
        self.order_notes = order_notes
        self.kitchen_notes = kitchen_notes
        self.internal_notes = internal_notes
        self.source = source
        self.device_id = device_id
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        prefix = "ORD"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_restaurant_order(self):
        """Check if this is a restaurant order"""
        return self.retail_type == 'Restaurant'
    
    @property
    def is_retail_order(self):
        """Check if this is a retail order"""
        return self.retail_type == 'Retail'
    
    @property
    def is_service_order(self):
        """Check if this is a service order"""
        return self.retail_type == 'Service'
    
    @property
    def is_ecommerce_order(self):
        """Check if this is an e-commerce order"""
        return self.retail_type == 'E-commerce'
    
    @property
    def is_dine_in(self):
        """Check if this is a dine-in order"""
        return self.order_subtype == 'DineIn'
    
    @property
    def is_takeaway(self):
        """Check if this is a takeaway order"""
        return self.order_subtype == 'Takeaway'
    
    @property
    def is_delivery(self):
        """Check if this is a delivery order"""
        return self.order_subtype == 'Delivery'
    
    @property
    def is_pickup(self):
        """Check if this is a pickup order"""
        return self.order_subtype == 'Pickup'
    
    @property
    def is_shipping(self):
        """Check if this is a shipping order"""
        return self.order_subtype == 'Shipping'
    
    @property
    def is_pending(self):
        """Check if order is pending"""
        return self.status == 'Pending'
    
    @property
    def is_confirmed(self):
        """Check if order is confirmed"""
        return self.status == 'Confirmed'
    
    @property
    def is_preparing(self):
        """Check if order is preparing"""
        return self.status == 'Preparing'
    
    @property
    def is_ready(self):
        """Check if order is ready"""
        return self.status == 'Ready'
    
    @property
    def is_completed(self):
        """Check if order is completed"""
        return self.status == 'Completed'
    
    @property
    def is_cancelled(self):
        """Check if order is cancelled"""
        return self.status == 'Cancelled'
    
    @property
    def is_paid(self):
        """Check if order is fully paid"""
        return self.payment_status == 'Paid'
    
    @property
    def is_unpaid(self):
        """Check if order is unpaid"""
        return self.payment_status == 'Unpaid'
    
    @property
    def is_partially_paid(self):
        """Check if order is partially paid"""
        return self.payment_status == 'Partial'
    
    def calculate_totals(self):
        """Calculate order totals"""
        # Calculate subtotal from items
        self.subtotal = sum(item.total_price for item in self.items)
        
        # Calculate total
        self.total_amount = (
            self.subtotal + 
            self.tax_amount + 
            self.service_charge + 
            self.delivery_charge + 
            self.tip_amount - 
            self.discount_amount
        )
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_status(self, new_status, user_id, notes=None):
        """Update order status"""
        old_status = self.status
        self.status = new_status
        self.updated_by = user_id
        self.updated_at = datetime.utcnow()
        
        # Set completion time
        if new_status == 'Completed' and not self.completed_time:
            self.completed_time = datetime.utcnow()
        
        # Add to status history
        history = OrderStatusHistory(
            order_id=self.id,
            old_status=old_status,
            new_status=new_status,
            user_id=user_id,
            notes=notes,
            tenant_id=self.tenant_id
        )
        db.session.add(history)
        db.session.commit()
    
    def confirm(self, user_id):
        """Confirm order"""
        if self.status not in ['Pending']:
            return False, "Only pending orders can be confirmed"
        
        self.update_status('Confirmed', user_id, "Order confirmed")
        return True, "Order confirmed successfully"
    
    def start_preparation(self, user_id):
        """Start order preparation"""
        if self.status not in ['Confirmed']:
            return False, "Only confirmed orders can be prepared"
        
        self.update_status('Preparing', user_id, "Order preparation started")
        return True, "Order preparation started"
    
    def mark_ready(self, user_id):
        """Mark order as ready"""
        if self.status not in ['Preparing']:
            return False, "Only preparing orders can be marked ready"
        
        self.update_status('Ready', user_id, "Order ready")
        return True, "Order marked as ready"
    
    def complete(self, user_id):
        """Complete order"""
        if self.status not in ['Ready']:
            return False, "Only ready orders can be completed"
        
        self.update_status('Completed', user_id, "Order completed")
        return True, "Order completed successfully"
    
    def cancel(self, user_id, reason=None):
        """Cancel order"""
        if self.status in ['Completed', 'Cancelled']:
            return False, "Cannot cancel completed or cancelled order"
        
        self.update_status('Cancelled', user_id, reason or "Order cancelled")
        return True, "Order cancelled successfully"
    
    def to_dict(self, include_items=True, include_payments=True):
        """Convert order to dictionary"""
        data = {
            'id': self.id,
            'order_number': self.order_number,
            'order_type': self.order_type,
            'order_subtype': self.order_subtype,
            'retail_type': self.retail_type,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'table_id': self.table_id,
            'table_name': self.table.name if self.table else None,
            'covers': self.covers,
            'server_id': self.server_id,
            'server_name': self.server.username if self.server else None,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'order_time': self.order_time.isoformat() if self.order_time else None,
            'estimated_time': self.estimated_time.isoformat() if self.estimated_time else None,
            'completed_time': self.completed_time.isoformat() if self.completed_time else None,
            'status': self.status,
            'priority': self.priority,
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount_amount': float(self.discount_amount),
            'service_charge': float(self.service_charge),
            'delivery_charge': float(self.delivery_charge),
            'tip_amount': float(self.tip_amount),
            'total_amount': float(self.total_amount),
            'payment_status': self.payment_status,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'delivery_address': self.delivery_address,
            'delivery_instructions': self.delivery_instructions,
            'delivery_partner': self.delivery_partner,
            'delivery_tracking': self.delivery_tracking,
            'order_notes': self.order_notes,
            'kitchen_notes': self.kitchen_notes,
            'internal_notes': self.internal_notes,
            'source': self.source,
            'device_id': self.device_id,
            'session_id': self.session_id,
            'is_restaurant_order': self.is_restaurant_order,
            'is_retail_order': self.is_retail_order,
            'is_service_order': self.is_service_order,
            'is_ecommerce_order': self.is_ecommerce_order,
            'is_dine_in': self.is_dine_in,
            'is_takeaway': self.is_takeaway,
            'is_delivery': self.is_delivery,
            'is_pickup': self.is_pickup,
            'is_shipping': self.is_shipping,
            'is_pending': self.is_pending,
            'is_confirmed': self.is_confirmed,
            'is_preparing': self.is_preparing,
            'is_ready': self.is_ready,
            'is_completed': self.is_completed,
            'is_cancelled': self.is_cancelled,
            'is_paid': self.is_paid,
            'is_unpaid': self.is_unpaid,
            'is_partially_paid': self.is_partially_paid,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        if include_payments:
            data['payments'] = [payment.to_dict() for payment in self.payments]
        
        return data
    
    @staticmethod
    def get_by_status(status, tenant_id=None):
        """Get orders by status"""
        query = EnhancedOrder.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(EnhancedOrder.order_time.desc()).all()
    
    @staticmethod
    def get_by_date_range(start_date, end_date, tenant_id=None):
        """Get orders within date range"""
        query = EnhancedOrder.query.filter(
            EnhancedOrder.order_date >= start_date,
            EnhancedOrder.order_date <= end_date
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(EnhancedOrder.order_time.desc()).all()
    
    @staticmethod
    def get_active_orders(tenant_id=None):
        """Get active orders (not completed or cancelled)"""
        query = EnhancedOrder.query.filter(
            EnhancedOrder.status.in_(['Pending', 'Confirmed', 'Preparing', 'Ready'])
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(EnhancedOrder.priority.desc(), EnhancedOrder.order_time).all()
    
    def __repr__(self):
        return f'<EnhancedOrder {self.order_number} ({self.status})>'


class EnhancedOrderItem(db.Model):
    """Enhanced order item model for multi-retail workflows"""
    __tablename__ = 'enhanced_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('enhanced_orders.id'), nullable=False)
    
    # Product information
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Item details
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Discount information
    discount_type = db.Column(db.String(20), default=None)  # Percentage, Fixed, None
    discount_value = db.Column(db.Numeric(10, 2), default=0)
    discount_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Tax information
    tax_rate = db.Column(db.Numeric(5, 2), default=0)  # Tax percentage
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Preparing, Ready, Served, Cancelled
    
    # Restaurant-specific fields
    course = db.Column(db.String(50), nullable=True)  # Appetizer, Main, Dessert, etc.
    dietary_info = db.Column(db.Text, nullable=True)
    preparation_notes = db.Column(db.Text, nullable=True)
    
    # Retail-specific fields
    serial_numbers = db.Column(db.Text, nullable=True)  # JSON array of serial numbers
    batch_numbers = db.Column(db.Text, nullable=True)  # JSON array of batch numbers
    warranty_info = db.Column(db.Text, nullable=True)
    
    # Service-specific fields
    service_duration = db.Column(db.Integer, nullable=True)  # Duration in minutes
    service_provider = db.Column(db.String(100), nullable=True)
    service_location = db.Column(db.String(100), nullable=True)
    
    # Item notes
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='enhanced_order_items')
    variant = db.relationship('ProductVariant', backref='enhanced_order_items')
    
    def __init__(self, order_id, product_id, quantity, unit_price,
                 variant_id=None, discount_type=None, discount_value=0,
                 tax_rate=0, status='Pending', course=None, dietary_info=None,
                 preparation_notes=None, serial_numbers=None, batch_numbers=None,
                 warranty_info=None, service_duration=None, service_provider=None,
                 service_location=None, notes=None, tenant_id=None):
        self.order_id = order_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.quantity = quantity
        self.unit_price = Decimal(str(unit_price))
        self.total_price = self.unit_price * quantity
        self.discount_type = discount_type
        self.discount_value = Decimal(str(discount_value))
        self.tax_rate = Decimal(str(tax_rate))
        self.status = status
        self.course = course
        self.dietary_info = dietary_info
        self.preparation_notes = preparation_notes
        self.serial_numbers = serial_numbers
        self.batch_numbers = batch_numbers
        self.warranty_info = warranty_info
        self.service_duration = service_duration
        self.service_provider = service_provider
        self.service_location = service_location
        self.notes = notes
        self.tenant_id = tenant_id
        
        # Calculate discount and tax amounts
        self.calculate_amounts()
    
    @property
    def net_unit_price(self):
        """Get unit price after discount"""
        if self.discount_type == 'Percentage':
            return self.unit_price * (1 - self.discount_value / 100)
        elif self.discount_type == 'Fixed':
            return max(0, self.unit_price - self.discount_value)
        return self.unit_price
    
    @property
    def net_total_price(self):
        """Get total price after discount"""
        return self.net_unit_price * self.quantity
    
    def calculate_amounts(self):
        """Calculate discount and tax amounts"""
        # Calculate discount amount
        if self.discount_type == 'Percentage':
            self.discount_amount = self.total_price * (self.discount_value / 100)
        elif self.discount_type == 'Fixed':
            self.discount_amount = min(self.total_price, self.discount_value * self.quantity)
        else:
            self.discount_amount = 0
        
        # Calculate tax amount on discounted price
        self.tax_amount = (self.total_price - self.discount_amount) * (self.tax_rate / 100)
        
        self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status):
        """Update item status"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'discount_amount': float(self.discount_amount),
            'net_unit_price': float(self.net_unit_price),
            'net_total_price': float(self.net_total_price),
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'status': self.status,
            'course': self.course,
            'dietary_info': self.dietary_info,
            'preparation_notes': self.preparation_notes,
            'serial_numbers': self.serial_numbers,
            'batch_numbers': self.batch_numbers,
            'warranty_info': self.warranty_info,
            'service_duration': self.service_duration,
            'service_provider': self.service_provider,
            'service_location': self.service_location,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<EnhancedOrderItem {self.product.name if self.product else "Unknown"}: {self.quantity}>'


class OrderStatusHistory(db.Model):
    """Order status history model for tracking status changes"""
    __tablename__ = 'order_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('enhanced_orders.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='order_status_changes')
    
    def __init__(self, order_id, new_status, user_id, old_status=None, notes=None, tenant_id=None):
        self.order_id = order_id
        self.old_status = old_status
        self.new_status = new_status
        self.user_id = user_id
        self.notes = notes
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert status history to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.order_id}: {self.old_status} -> {self.new_status}>'


class EnhancedPayment(db.Model):
    """Enhanced payment model for multi-retail workflows"""
    __tablename__ = 'enhanced_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('enhanced_orders.id'), nullable=False)
    payment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Payment details
    payment_method = db.Column(db.String(50), nullable=False)
    payment_type = db.Column(db.String(20), default='Payment')  # Payment, Refund, Partial
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Payment information
    reference_number = db.Column(db.String(100), nullable=True)
    transaction_id = db.Column(db.String(100), nullable=True)
    authorization_code = db.Column(db.String(100), nullable=True)
    
    # Card information (for card payments)
    card_type = db.Column(db.String(20), nullable=True)
    card_last_four = db.Column(db.String(4), nullable=True)
    card_expiry = db.Column(db.String(10), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Completed, Failed, Refunded
    
    # Payment processing
    processor = db.Column(db.String(50), nullable=True)  # Payment processor (Stripe, PayPal, etc.)
    processor_response = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_payments')
    
    def __init__(self, order_id, payment_method, amount, payment_type='Payment',
                 reference_number=None, transaction_id=None, authorization_code=None,
                 card_type=None, card_last_four=None, card_expiry=None,
                 status='Pending', processor=None, processor_response=None,
                 tenant_id=None, created_by=None):
        self.order_id = order_id
        self.payment_number = self.generate_payment_number()
        self.payment_method = payment_method
        self.payment_type = payment_type
        self.amount = Decimal(str(amount))
        self.reference_number = reference_number
        self.transaction_id = transaction_id
        self.authorization_code = authorization_code
        self.card_type = card_type
        self.card_last_four = card_last_four
        self.card_expiry = card_expiry
        self.status = status
        self.processor = processor
        self.processor_response = processor_response
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_payment_number():
        """Generate unique payment number"""
        prefix = "PAY"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'Pending'
    
    @property
    def is_processing(self):
        """Check if payment is processing"""
        return self.status == 'Processing'
    
    @property
    def is_completed(self):
        """Check if payment is completed"""
        return self.status == 'Completed'
    
    @property
    def is_failed(self):
        """Check if payment failed"""
        return self.status == 'Failed'
    
    @property
    def is_refunded(self):
        """Check if payment is refunded"""
        return self.status == 'Refunded'
    
    def complete(self, transaction_id=None, authorization_code=None, processor_response=None):
        """Complete payment"""
        self.status = 'Completed'
        if transaction_id:
            self.transaction_id = transaction_id
        if authorization_code:
            self.authorization_code = authorization_code
        if processor_response:
            self.processor_response = processor_response
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail(self, processor_response=None):
        """Mark payment as failed"""
        self.status = 'Failed'
        if processor_response:
            self.processor_response = processor_response
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def refund(self, amount=None):
        """Refund payment"""
        self.status = 'Refunded'
        if amount:
            self.amount = Decimal(str(amount))
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert payment to dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order.order_number if self.order else None,
            'payment_number': self.payment_number,
            'payment_method': self.payment_method,
            'payment_type': self.payment_type,
            'amount': float(self.amount),
            'reference_number': self.reference_number,
            'transaction_id': self.transaction_id,
            'authorization_code': self.authorization_code,
            'card_type': self.card_type,
            'card_last_four': self.card_last_four,
            'card_expiry': self.card_expiry,
            'status': self.status,
            'processor': self.processor,
            'processor_response': self.processor_response,
            'is_pending': self.is_pending,
            'is_processing': self.is_processing,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'is_refunded': self.is_refunded,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    def __repr__(self):
        return f'<EnhancedPayment {self.payment_number} ({self.status})>'