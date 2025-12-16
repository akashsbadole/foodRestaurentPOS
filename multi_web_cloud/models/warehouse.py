from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class Warehouse(FeatureAwareModel):
    """Warehouse model for multi-warehouse inventory management"""
    __tablename__ = 'warehouses'
    
    # Feature requirements
    required_features = ['FEATURE_MULTI_WAREHOUSE']
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    
    # Address information
    address_line1 = db.Column(db.String(255), nullable=True)
    address_line2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    
    # Contact information
    manager_name = db.Column(db.String(100), nullable=True)
    manager_phone = db.Column(db.String(20), nullable=True)
    manager_email = db.Column(db.String(120), nullable=True)
    
    # Warehouse details
    warehouse_type = db.Column(db.String(50), default='Storage')  # Storage, Distribution, Retail, etc.
    capacity = db.Column(db.Integer, nullable=True)  # In square feet or cubic meters
    temperature_controlled = db.Column(db.Boolean, default=False)
    security_level = db.Column(db.String(20), default='Basic')  # Basic, High, Maximum
    
    # Operating hours
    operating_hours = db.Column(db.Text, nullable=True)  # JSON object with days and hours
    timezone = db.Column(db.String(50), default='UTC')
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_primary = db.Column(db.Boolean, default=False)  # Primary warehouse for tenant
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_warehouses')
    stock_items = db.relationship('WarehouseStock', backref='warehouse', lazy=True, cascade='all, delete-orphan')
    transfers_from = db.relationship('StockTransfer', foreign_keys='StockTransfer.from_warehouse_id', backref='from_warehouse', lazy=True)
    transfers_to = db.relationship('StockTransfer', foreign_keys='StockTransfer.to_warehouse_id', backref='to_warehouse', lazy=True)
    
    def __init__(self, warehouse_code, name, address_line1=None, address_line2=None,
                 city=None, state=None, postal_code=None, country=None,
                 manager_name=None, manager_phone=None, manager_email=None,
                 warehouse_type='Storage', capacity=None, temperature_controlled=False,
                 security_level='Basic', operating_hours=None, timezone='UTC',
                 is_active=True, is_primary=False, notes=None, tenant_id=None, created_by=None):
        self.warehouse_code = warehouse_code
        self.name = name
        self.address_line1 = address_line1
        self.address_line2 = address_line2
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country
        self.manager_name = manager_name
        self.manager_phone = manager_phone
        self.manager_email = manager_email
        self.warehouse_type = warehouse_type
        self.capacity = capacity
        self.temperature_controlled = temperature_controlled
        self.security_level = security_level
        self.operating_hours = operating_hours
        self.timezone = timezone
        self.is_active = is_active
        self.is_primary = is_primary
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def full_address(self):
        """Get full address as single string"""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ', '.join(address_parts)
    
    def get_operating_hours(self):
        """Get operating hours as dictionary"""
        if not self.operating_hours:
            return {}
        import json
        try:
            return json.loads(self.operating_hours)
        except:
            return {}
    
    def is_open_now(self):
        """Check if warehouse is currently open"""
        import pytz
        from datetime import datetime
        
        try:
            tz = pytz.timezone(self.timezone)
            now = datetime.now(tz)
            day_name = now.strftime('%A').lower()
            
            operating_hours = self.get_operating_hours()
            if day_name not in operating_hours:
                return False
            
            day_hours = operating_hours[day_name]
            if not day_hours.get('open', False):
                return False
            
            open_time = datetime.strptime(day_hours['open'], '%H:%M').time()
            close_time = datetime.strptime(day_hours['close'], '%H:%M').time()
            current_time = now.time()
            
            return open_time <= current_time <= close_time
        except:
            return True  # Assume open if there's an error
    
    def get_total_stock_value(self):
        """Get total value of all stock in warehouse"""
        total_value = Decimal('0')
        for stock_item in self.stock_items:
            if stock_item.product:
                cost_price = stock_item.product.cost_price or stock_item.product.base_price
                total_value += stock_item.quantity * cost_price
        return total_value
    
    def get_total_products(self):
        """Get total number of unique products in warehouse"""
        return len(set(stock_item.product_id for stock_item in self.stock_items if stock_item.quantity > 0))
    
    def to_dict(self, include_stock=False):
        """Convert warehouse to dictionary"""
        data = {
            'id': self.id,
            'warehouse_code': self.warehouse_code,
            'name': self.name,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'full_address': self.full_address,
            'manager_name': self.manager_name,
            'manager_phone': self.manager_phone,
            'manager_email': self.manager_email,
            'warehouse_type': self.warehouse_type,
            'capacity': self.capacity,
            'temperature_controlled': self.temperature_controlled,
            'security_level': self.security_level,
            'operating_hours': self.get_operating_hours(),
            'timezone': self.timezone,
            'is_open_now': self.is_open_now(),
            'is_active': self.is_active,
            'is_primary': self.is_primary,
            'notes': self.notes,
            'total_stock_value': float(self.get_total_stock_value()),
            'total_products': self.get_total_products(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
        
        if include_stock:
            data['stock_items'] = [item.to_dict() for item in self.stock_items if item.quantity > 0]
        
        return data
    
    @staticmethod
    def get_active_warehouses(tenant_id=None):
        """Get all active warehouses"""
        query = Warehouse.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Warehouse.name).all()
    
    @staticmethod
    def get_primary_warehouse(tenant_id=None):
        """Get primary warehouse"""
        query = Warehouse.query.filter_by(is_primary=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_by_code(warehouse_code, tenant_id=None):
        """Get warehouse by code"""
        query = Warehouse.query.filter_by(warehouse_code=warehouse_code)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<Warehouse {self.name} ({self.warehouse_code})>'


class WarehouseStock(db.Model):
    """Warehouse stock model for tracking inventory by warehouse"""
    __tablename__ = 'warehouse_stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Stock quantities
    quantity = db.Column(db.Integer, default=0)
    allocated_quantity = db.Column(db.Integer, default=0)
    available_quantity = db.Column(db.Integer, default=0)  # quantity - allocated_quantity
    
    # Location within warehouse
    location = db.Column(db.String(100), nullable=True)  # Aisle, Rack, Shelf, etc.
    zone = db.Column(db.String(50), nullable=True)
    
    # Stock information
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    last_count_date = db.Column(db.Date, nullable=True)
    count_variance = db.Column(db.Integer, default=0)  # Difference between system and physical count
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='warehouse_stocks')
    variant = db.relationship('ProductVariant', backref='warehouse_stocks')
    
    def __init__(self, warehouse_id, product_id, quantity=0, variant_id=None,
                 location=None, zone=None, tenant_id=None):
        self.warehouse_id = warehouse_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.quantity = quantity
        self.available_quantity = quantity
        self.location = location
        self.zone = zone
        self.tenant_id = tenant_id
    
    def update_quantity(self, new_quantity, reason=None):
        """Update stock quantity"""
        old_quantity = self.quantity
        self.quantity = new_quantity
        self.available_quantity = self.quantity - self.allocated_quantity
        self.last_updated = datetime.utcnow()
        
        # Create inventory transaction
        from .inventory import InventoryTransaction
        transaction = InventoryTransaction(
            product_id=self.product_id,
            variant_id=self.variant_id,
            transaction_type='adjustment',
            quantity_change=new_quantity - old_quantity,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            notes=f"Warehouse stock adjustment: {reason}" if reason else "Warehouse stock adjustment",
            tenant_id=self.tenant_id,
            created_by=1  # Should be passed as parameter
        )
        db.session.add(transaction)
        db.session.commit()
    
    def allocate_quantity(self, quantity_to_allocate):
        """Allocate quantity for orders"""
        if quantity_to_allocate > self.available_quantity:
            return False, "Insufficient available quantity"
        
        self.allocated_quantity += quantity_to_allocate
        self.available_quantity = self.quantity - self.allocated_quantity
        self.last_updated = datetime.utcnow()
        db.session.commit()
        return True, "Quantity allocated successfully"
    
    def release_allocation(self, quantity_to_release):
        """Release allocated quantity"""
        if quantity_to_release > self.allocated_quantity:
            return False, "Cannot release more than allocated"
        
        self.allocated_quantity -= quantity_to_release
        self.available_quantity = self.quantity - self.allocated_quantity
        self.last_updated = datetime.utcnow()
        db.session.commit()
        return True, "Allocation released successfully"
    
    def consume_quantity(self, quantity_to_consume):
        """Consume quantity from stock"""
        if quantity_to_consume > self.available_quantity:
            return False, "Insufficient available quantity"
        
        # Reduce allocated and available quantities
        actual_consumed = min(quantity_to_consume, self.allocated_quantity)
        self.allocated_quantity -= actual_consumed
        self.quantity -= quantity_to_consume
        self.available_quantity = self.quantity - self.allocated_quantity
        self.last_updated = datetime.utcnow()
        db.session.commit()
        return True, "Quantity consumed successfully"
    
    def record_physical_count(self, counted_quantity, counted_by=None):
        """Record physical stock count"""
        self.count_variance = counted_quantity - self.quantity
        self.last_count_date = date.today()
        
        if self.count_variance != 0:
            # Create stock adjustment
            from .inventory import StockAdjustment
            adjustment = StockAdjustment(
                adjustment_type='manual',
                reason=f"Physical count variance: {self.count_variance}",
                created_by=counted_by or 1,
                tenant_id=self.tenant_id
            )
            db.session.add(adjustment)
            db.session.flush()  # Get adjustment ID
            
            # Create adjustment item
            from .inventory import StockAdjustmentItem
            adjustment_item = StockAdjustmentItem(
                adjustment_id=adjustment.id,
                product_id=self.product_id,
                current_quantity=self.quantity,
                adjusted_quantity=counted_quantity,
                tenant_id=self.tenant_id
            )
            db.session.add(adjustment_item)
        
        self.quantity = counted_quantity
        self.available_quantity = self.quantity - self.allocated_quantity
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert warehouse stock to dictionary"""
        return {
            'id': self.id,
            'warehouse_id': self.warehouse_id,
            'warehouse_name': self.warehouse.name if self.warehouse else None,
            'warehouse_code': self.warehouse.warehouse_code if self.warehouse else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'quantity': self.quantity,
            'allocated_quantity': self.allocated_quantity,
            'available_quantity': self.available_quantity,
            'location': self.location,
            'zone': self.zone,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'last_count_date': self.last_count_date.isoformat() if self.last_count_date else None,
            'count_variance': self.count_variance,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_by_warehouse(warehouse_id, tenant_id=None):
        """Get all stock items for a warehouse"""
        query = WarehouseStock.query.filter_by(warehouse_id=warehouse_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_by_product(product_id, tenant_id=None):
        """Get stock for a product across all warehouses"""
        query = WarehouseStock.query.filter_by(product_id=product_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    def __repr__(self):
        return f'<WarehouseStock {self.product.name if self.product else "Unknown"}: {self.available_quantity}/{self.quantity}>'


class StockTransfer(FeatureAwareModel):
    """Stock transfer model for moving stock between warehouses"""
    __tablename__ = 'stock_transfers'
    
    # Feature requirements
    required_features = ['FEATURE_STOCK_TRANSFER']
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Source and destination
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    
    # Transfer information
    transfer_date = db.Column(db.Date, nullable=False, default=date.today)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    actual_delivery_date = db.Column(db.Date, nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='Draft')  # Draft, In Transit, Received, Cancelled
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    
    # Additional information
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Approval information
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    approver = db.relationship('User', backref='approved_transfers')
    creator = db.relationship('User', backref='created_transfers')
    items = db.relationship('StockTransferItem', backref='transfer', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, from_warehouse_id, to_warehouse_id, transfer_number=None,
                 transfer_date=None, expected_delivery_date=None, priority='Normal',
                 reason=None, notes=None, tenant_id=None, created_by=None):
        self.transfer_number = transfer_number or self.generate_transfer_number()
        self.from_warehouse_id = from_warehouse_id
        self.to_warehouse_id = to_warehouse_id
        self.transfer_date = transfer_date or date.today()
        self.expected_delivery_date = expected_delivery_date
        self.priority = priority
        self.reason = reason
        self.notes = notes
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_transfer_number():
        """Generate unique transfer number"""
        prefix = "ST"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_draft(self):
        """Check if transfer is in draft status"""
        return self.status == 'Draft'
    
    @property
    def is_in_transit(self):
        """Check if transfer is in transit"""
        return self.status == 'In Transit'
    
    @property
    def is_received(self):
        """Check if transfer is received"""
        return self.status == 'Received'
    
    @property
    def is_cancelled(self):
        """Check if transfer is cancelled"""
        return self.status == 'Cancelled'
    
    def approve(self, approver_id):
        """Approve stock transfer"""
        if self.status != 'Draft':
            return False, "Only draft transfers can be approved"
        
        self.status = 'In Transit'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        
        # Allocate stock from source warehouse
        for item in self.items:
            source_stock = WarehouseStock.query.filter_by(
                warehouse_id=self.from_warehouse_id,
                product_id=item.product_id,
                variant_id=item.variant_id
            ).first()
            
            if source_stock:
                source_stock.allocate_quantity(item.quantity)
        
        db.session.commit()
        return True, "Transfer approved successfully"
    
    def receive(self, received_by=None):
        """Receive stock transfer at destination"""
        if self.status != 'In Transit':
            return False, "Only in-transit transfers can be received"
        
        self.status = 'Received'
        self.actual_delivery_date = date.today()
        
        # Add stock to destination warehouse
        for item in self.items:
            dest_stock = WarehouseStock.query.filter_by(
                warehouse_id=self.to_warehouse_id,
                product_id=item.product_id,
                variant_id=item.variant_id
            ).first()
            
            if dest_stock:
                dest_stock.update_quantity(
                    dest_stock.quantity + item.received_quantity,
                    reason=f"Stock transfer {self.transfer_number}"
                )
            else:
                # Create new stock record
                dest_stock = WarehouseStock(
                    warehouse_id=self.to_warehouse_id,
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    quantity=item.received_quantity,
                    tenant_id=self.tenant_id
                )
                db.session.add(dest_stock)
        
        db.session.commit()
        return True, "Transfer received successfully"
    
    def cancel(self):
        """Cancel stock transfer"""
        if self.status in ['Received', 'Cancelled']:
            return False, "Cannot cancel received or cancelled transfer"
        
        self.status = 'Cancelled'
        
        # Release allocated stock
        if self.status == 'In Transit':
            for item in self.items:
                source_stock = WarehouseStock.query.filter_by(
                    warehouse_id=self.from_warehouse_id,
                    product_id=item.product_id,
                    variant_id=item.variant_id
                ).first()
                
                if source_stock:
                    source_stock.release_allocation(item.quantity)
        
        db.session.commit()
        return True, "Transfer cancelled successfully"
    
    def to_dict(self, include_items=True):
        """Convert stock transfer to dictionary"""
        data = {
            'id': self.id,
            'transfer_number': self.transfer_number,
            'from_warehouse_id': self.from_warehouse_id,
            'from_warehouse_name': self.from_warehouse.name if self.from_warehouse else None,
            'from_warehouse_code': self.from_warehouse.warehouse_code if self.from_warehouse else None,
            'to_warehouse_id': self.to_warehouse_id,
            'to_warehouse_name': self.to_warehouse.name if self.to_warehouse else None,
            'to_warehouse_code': self.to_warehouse.warehouse_code if self.to_warehouse else None,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'actual_delivery_date': self.actual_delivery_date.isoformat() if self.actual_delivery_date else None,
            'status': self.status,
            'priority': self.priority,
            'reason': self.reason,
            'notes': self.notes,
            'attachments': self.attachments,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'is_draft': self.is_draft,
            'is_in_transit': self.is_in_transit,
            'is_received': self.is_received,
            'is_cancelled': self.is_cancelled,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    @staticmethod
    def get_by_status(status, tenant_id=None):
        """Get transfers by status"""
        query = StockTransfer.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(StockTransfer.created_at.desc()).all()
    
    @staticmethod
    def get_pending_transfers(tenant_id=None):
        """Get pending transfers"""
        query = StockTransfer.query.filter(StockTransfer.status.in_(['Draft', 'In Transit']))
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(StockTransfer.transfer_date).all()
    
    def __repr__(self):
        return f'<StockTransfer {self.transfer_number} ({self.status})>'


class StockTransferItem(db.Model):
    """Stock transfer item model for individual items in a transfer"""
    __tablename__ = 'stock_transfer_items'
    
    id = db.Column(db.Integer, primary_key=True)
    transfer_id = db.Column(db.Integer, db.ForeignKey('stock_transfers.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Quantities
    quantity = db.Column(db.Integer, nullable=False)
    received_quantity = db.Column(db.Integer, default=0)
    damaged_quantity = db.Column(db.Integer, default=0)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='transfer_items')
    variant = db.relationship('ProductVariant', backref='transfer_items')
    
    def __init__(self, transfer_id, product_id, quantity, variant_id=None,
                 notes=None, tenant_id=None):
        self.transfer_id = transfer_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.quantity = quantity
        self.notes = notes
        self.tenant_id = tenant_id
    
    @property
    def pending_quantity(self):
        """Get pending quantity (not yet received)"""
        return self.quantity - self.received_quantity
    
    @property
    def is_fully_received(self):
        """Check if item is fully received"""
        return self.received_quantity >= self.quantity
    
    def receive_quantity(self, received_qty, damaged_qty=0):
        """Record received quantity"""
        if received_qty + damaged_qty > self.pending_quantity:
            return False, "Cannot receive more than transferred quantity"
        
        self.received_quantity += received_qty
        self.damaged_quantity += damaged_qty
        self.updated_at = datetime.utcnow()
        db.session.commit()
        return True, "Quantity received successfully"
    
    def to_dict(self):
        """Convert stock transfer item to dictionary"""
        return {
            'id': self.id,
            'transfer_id': self.transfer_id,
            'transfer_number': self.transfer.transfer_number if self.transfer else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'quantity': self.quantity,
            'received_quantity': self.received_quantity,
            'damaged_quantity': self.damaged_quantity,
            'pending_quantity': self.pending_quantity,
            'is_fully_received': self.is_fully_received,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<StockTransferItem {self.product.name if self.product else "Unknown"}: {self.received_quantity}/{self.quantity}>'