from datetime import datetime
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class InventoryTransaction(db.Model):
    """Inventory transaction model for tracking stock movements"""
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # purchase, sale, adjustment, transfer, return
    quantity_change = db.Column(db.Integer, nullable=False)  # Positive for increase, negative for decrease
    old_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    
    # Reference information
    reference_type = db.Column(db.String(20), nullable=True)  # order, purchase_order, adjustment, transfer
    reference_id = db.Column(db.Integer, nullable=True)
    
    # Additional details
    notes = db.Column(db.Text, nullable=True)
    cost_per_unit = db.Column(db.Numeric(10, 2), nullable=True)  # For purchase transactions
    total_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Batch/lot tracking
    batch_number = db.Column(db.String(50), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    serial_numbers = db.Column(db.Text, nullable=True)  # JSON array of serial numbers
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    product = db.relationship('Product', backref='inventory_transactions')
    variant = db.relationship('ProductVariant', backref='inventory_transactions')
    creator = db.relationship('User', backref='inventory_transactions')
    
    def __init__(self, product_id=None, variant_id=None, transaction_type='adjustment',
                 quantity_change=0, old_quantity=0, new_quantity=0, reference_type=None,
                 reference_id=None, notes=None, cost_per_unit=None, total_cost=None,
                 batch_number=None, expiry_date=None, serial_numbers=None,
                 tenant_id=None, created_by=None):
        self.product_id = product_id
        self.variant_id = variant_id
        self.transaction_type = transaction_type
        self.quantity_change = quantity_change
        self.old_quantity = old_quantity
        self.new_quantity = new_quantity
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.notes = notes
        self.cost_per_unit = Decimal(str(cost_per_unit)) if cost_per_unit else None
        self.total_cost = Decimal(str(total_cost)) if total_cost else None
        self.batch_number = batch_number
        self.expiry_date = expiry_date
        self.serial_numbers = serial_numbers
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def transaction_description(self):
        """Get human-readable transaction description"""
        descriptions = {
            'purchase': 'Purchase',
            'sale': 'Sale',
            'adjustment': 'Stock Adjustment',
            'transfer': 'Stock Transfer',
            'return': 'Return',
            'damage': 'Damage/Loss',
            'expiry': 'Expiry'
        }
        return descriptions.get(self.transaction_type, self.transaction_type.title())
    
    @property
    def is_increase(self):
        """Check if transaction increases stock"""
        return self.quantity_change > 0
    
    @property
    def is_decrease(self):
        """Check if transaction decreases stock"""
        return self.quantity_change < 0
    
    def get_serial_numbers_list(self):
        """Get serial numbers as list"""
        if not self.serial_numbers:
            return []
        import json
        try:
            return json.loads(self.serial_numbers)
        except:
            return []
    
    def to_dict(self):
        """Convert inventory transaction to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'transaction_type': self.transaction_type,
            'transaction_description': self.transaction_description,
            'quantity_change': self.quantity_change,
            'old_quantity': self.old_quantity,
            'new_quantity': self.new_quantity,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'batch_number': self.batch_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'serial_numbers': self.get_serial_numbers_list(),
            'is_increase': self.is_increase,
            'is_decrease': self.is_decrease,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    @staticmethod
    def get_by_product(product_id, tenant_id=None, limit=50):
        """Get transactions for a specific product"""
        query = InventoryTransaction.query.filter_by(product_id=product_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_date_range(start_date, end_date, tenant_id=None):
        """Get transactions within date range"""
        query = InventoryTransaction.query.filter(
            InventoryTransaction.created_at >= start_date,
            InventoryTransaction.created_at <= end_date
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(InventoryTransaction.created_at.desc()).all()
    
    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type}: {self.quantity_change}>'


class StockAdjustment(FeatureAwareModel):
    """Stock adjustment model for manual stock corrections"""
    __tablename__ = 'stock_adjustments'
    
    # Feature requirements
    required_features = ['FEATURE_STOCK_ADJUSTMENT']
    
    id = db.Column(db.Integer, primary_key=True)
    adjustment_number = db.Column(db.String(50), unique=True, nullable=False)
    adjustment_type = db.Column(db.String(20), nullable=False)  # manual, damage, expiry, theft, system
    
    # Status and approval
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Financial impact
    total_loss_value = db.Column(db.Numeric(10, 2), default=0)
    
    # Notes and attachments
    reason = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    attachments = db.Column(db.Text, nullable=True)  # JSON array of file paths
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_adjustments')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_adjustments')
    items = db.relationship('StockAdjustmentItem', backref='adjustment', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, adjustment_type='manual', reason='', created_by=None, tenant_id=None):
        self.adjustment_number = self.generate_adjustment_number()
        self.adjustment_type = adjustment_type
        self.reason = reason
        self.created_by = created_by
        self.tenant_id = tenant_id
    
    @staticmethod
    def generate_adjustment_number():
        """Generate unique adjustment number"""
        prefix = "ADJ"
        date_str = datetime.now().strftime("%Y%m%d")
        # Simple implementation - in production, use proper sequence
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_pending(self):
        """Check if adjustment is pending"""
        return self.status == 'Pending'
    
    @property
    def is_approved(self):
        """Check if adjustment is approved"""
        return self.status == 'Approved'
    
    @property
    def is_rejected(self):
        """Check if adjustment is rejected"""
        return self.status == 'Rejected'
    
    def approve(self, approver_id):
        """Approve the stock adjustment"""
        if self.status != 'Pending':
            return False, "Adjustment is not pending"
        
        self.status = 'Approved'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        
        # Process the adjustment items
        for item in self.items:
            if item.product:
                item.product.update_stock(
                    item.quantity_change,
                    transaction_type='adjustment',
                    reference_id=self.id,
                    notes=f"Stock adjustment: {self.adjustment_number}"
                )
        
        db.session.commit()
        return True, "Adjustment approved successfully"
    
    def reject(self, approver_id, rejection_reason):
        """Reject the stock adjustment"""
        if self.status != 'Pending':
            return False, "Adjustment is not pending"
        
        self.status = 'Rejected'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.rejection_reason = rejection_reason
        
        db.session.commit()
        return True, "Adjustment rejected successfully"
    
    def calculate_total_loss(self):
        """Calculate total loss value"""
        total_loss = Decimal('0')
        for item in self.items:
            if item.quantity_change < 0 and item.product:
                cost_price = item.product.cost_price or item.product.base_price
                total_loss += abs(item.quantity_change) * cost_price
        
        self.total_loss_value = total_loss
        return total_loss
    
    def to_dict(self, include_items=True):
        """Convert stock adjustment to dictionary"""
        data = {
            'id': self.id,
            'adjustment_number': self.adjustment_number,
            'adjustment_type': self.adjustment_type,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_by_name': self.approver.username if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejection_reason': self.rejection_reason,
            'total_loss_value': float(self.total_loss_value),
            'reason': self.reason,
            'notes': self.notes,
            'attachments': self.attachments,
            'is_pending': self.is_pending,
            'is_approved': self.is_approved,
            'is_rejected': self.is_rejected,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    @staticmethod
    def get_pending(tenant_id=None):
        """Get pending adjustments"""
        query = StockAdjustment.query.filter_by(status='Pending')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(StockAdjustment.created_at).all()
    
    def __repr__(self):
        return f'<StockAdjustment {self.adjustment_number} ({self.status})>'


class StockAdjustmentItem(db.Model):
    """Stock adjustment item model for individual items in an adjustment"""
    __tablename__ = 'stock_adjustment_items'
    
    id = db.Column(db.Integer, primary_key=True)
    adjustment_id = db.Column(db.Integer, db.ForeignKey('stock_adjustments.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Stock information
    current_quantity = db.Column(db.Integer, nullable=False)
    adjusted_quantity = db.Column(db.Integer, nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # Can be positive or negative
    
    # Cost calculation
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)
    total_cost = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Notes
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='adjustment_items')
    variant = db.relationship('ProductVariant', backref='adjustment_items')
    
    def __init__(self, adjustment_id, product_id, current_quantity, adjusted_quantity,
                 variant_id=None, unit_cost=None, notes=None, tenant_id=None):
        self.adjustment_id = adjustment_id
        self.product_id = product_id
        self.variant_id = variant_id
        self.current_quantity = current_quantity
        self.adjusted_quantity = adjusted_quantity
        self.quantity_change = adjusted_quantity - current_quantity
        self.unit_cost = Decimal(str(unit_cost)) if unit_cost else None
        self.total_cost = abs(self.quantity_change) * self.unit_cost if self.unit_cost else None
        self.notes = notes
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert stock adjustment item to dictionary"""
        return {
            'id': self.id,
            'adjustment_id': self.adjustment_id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'current_quantity': self.current_quantity,
            'adjusted_quantity': self.adjusted_quantity,
            'quantity_change': self.quantity_change,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'notes': self.notes,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<StockAdjustmentItem {self.product.name if self.product else "Unknown"}: {self.quantity_change}>'


class LowStockAlert(FeatureAwareModel):
    """Low stock alert model for inventory notifications"""
    __tablename__ = 'low_stock_alerts'
    
    # Feature requirements
    required_features = ['FEATURE_LOW_STOCK_ALERTS']
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Alert information
    alert_type = db.Column(db.String(20), default='low_stock')  # low_stock, out_of_stock, reorder
    current_quantity = db.Column(db.Integer, nullable=False)
    threshold_quantity = db.Column(db.Integer, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Acknowledged, Resolved
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Notification
    notification_sent = db.Column(db.Boolean, default=False)
    notification_sent_at = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='low_stock_alerts')
    variant = db.relationship('ProductVariant', backref='low_stock_alerts')
    acknowledged_by_user = db.relationship('User', backref='acknowledged_alerts')
    
    def __init__(self, product_id, alert_type='low_stock', current_quantity=0,
                 threshold_quantity=0, variant_id=None, tenant_id=None):
        self.product_id = product_id
        self.alert_type = alert_type
        self.current_quantity = current_quantity
        self.threshold_quantity = threshold_quantity
        self.variant_id = variant_id
        self.tenant_id = tenant_id
    
    @property
    def is_active(self):
        """Check if alert is active"""
        return self.status == 'Active'
    
    @property
    def is_acknowledged(self):
        """Check if alert is acknowledged"""
        return self.status == 'Acknowledged'
    
    @property
    def is_resolved(self):
        """Check if alert is resolved"""
        return self.status == 'Resolved'
    
    def acknowledge(self, user_id):
        """Acknowledge the alert"""
        self.status = 'Acknowledged'
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def resolve(self):
        """Resolve the alert"""
        self.status = 'Resolved'
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_notification_sent(self):
        """Mark notification as sent"""
        self.notification_sent = True
        self.notification_sent_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert low stock alert to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'alert_type': self.alert_type,
            'current_quantity': self.current_quantity,
            'threshold_quantity': self.threshold_quantity,
            'status': self.status,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_by_name': self.acknowledged_by_user.username if self.acknowledged_by_user else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'notification_sent': self.notification_sent,
            'notification_sent_at': self.notification_sent_at.isoformat() if self.notification_sent_at else None,
            'is_active': self.is_active,
            'is_acknowledged': self.is_acknowledged,
            'is_resolved': self.is_resolved,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_active_alerts(tenant_id=None):
        """Get all active alerts"""
        query = LowStockAlert.query.filter_by(status='Active')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(LowStockAlert.created_at.desc()).all()
    
    @staticmethod
    def check_and_create_alerts(tenant_id=None):
        """Check all products and create alerts if needed"""
        from .product import Product
        
        products = Product.query.filter_by(is_active=True, track_inventory=True)
        if tenant_id:
            products = products.filter_by(tenant_id=tenant_id)
        
        alerts_created = 0
        
        for product in products.all():
            # Check for out of stock
            if product.is_out_of_stock():
                existing_alert = LowStockAlert.query.filter_by(
                    product_id=product.id,
                    alert_type='out_of_stock',
                    status='Active'
                ).first()
                
                if not existing_alert:
                    alert = LowStockAlert(
                        product_id=product.id,
                        alert_type='out_of_stock',
                        current_quantity=0,
                        threshold_quantity=1,
                        tenant_id=product.tenant_id
                    )
                    db.session.add(alert)
                    alerts_created += 1
            
            # Check for low stock
            elif product.is_low_stock():
                existing_alert = LowStockAlert.query.filter_by(
                    product_id=product.id,
                    alert_type='low_stock',
                    status='Active'
                ).first()
                
                if not existing_alert:
                    alert = LowStockAlert(
                        product_id=product.id,
                        alert_type='low_stock',
                        current_quantity=product.stock_quantity,
                        threshold_quantity=product.min_stock_level,
                        tenant_id=product.tenant_id
                    )
                    db.session.add(alert)
                    alerts_created += 1
            
            # Check for reorder needed
            elif product.needs_reorder():
                existing_alert = LowStockAlert.query.filter_by(
                    product_id=product.id,
                    alert_type='reorder',
                    status='Active'
                ).first()
                
                if not existing_alert:
                    alert = LowStockAlert(
                        product_id=product.id,
                        alert_type='reorder',
                        current_quantity=product.stock_quantity,
                        threshold_quantity=product.reorder_point,
                        tenant_id=product.tenant_id
                    )
                    db.session.add(alert)
                    alerts_created += 1
        
        if alerts_created > 0:
            db.session.commit()
        
        return alerts_created
    
    def __repr__(self):
        return f'<LowStockAlert {self.product.name if self.product else "Unknown"} ({self.alert_type})>'


class ReorderPoint(FeatureAwareModel):
    """Reorder point model for automatic reordering"""
    __tablename__ = 'reorder_points'
    
    # Feature requirements
    required_features = ['FEATURE_STOCK_TRACKING']
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Reorder parameters
    reorder_point = db.Column(db.Integer, nullable=False)
    reorder_quantity = db.Column(db.Integer, nullable=False)
    max_stock_level = db.Column(db.Integer, nullable=True)
    
    # Supplier information
    preferred_supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    lead_time_days = db.Column(db.Integer, default=7)  # Expected lead time in days
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    product = db.relationship('Product', backref='reorder_points')
    variant = db.relationship('ProductVariant', backref='reorder_points')
    preferred_supplier = db.relationship('Supplier', backref='reorder_points')
    creator = db.relationship('User', backref='created_reorder_points')
    
    def __init__(self, product_id, reorder_point, reorder_quantity, variant_id=None,
                 max_stock_level=None, preferred_supplier_id=None, lead_time_days=7,
                 is_active=True, tenant_id=None, created_by=None):
        self.product_id = product_id
        self.reorder_point = reorder_point
        self.reorder_quantity = reorder_quantity
        self.variant_id = variant_id
        self.max_stock_level = max_stock_level
        self.preferred_supplier_id = preferred_supplier_id
        self.lead_time_days = lead_time_days
        self.is_active = is_active
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    def needs_reorder(self):
        """Check if product needs to be reordered"""
        if not self.is_active:
            return False
        
        if self.variant_id:
            current_stock = self.variant.stock_quantity if self.variant else 0
        else:
            current_stock = self.product.stock_quantity if self.product else 0
        
        return current_stock <= self.reorder_point
    
    def calculate_suggested_order_quantity(self):
        """Calculate suggested order quantity based on current stock and max level"""
        if not self.is_active or not self.max_stock_level:
            return self.reorder_quantity
        
        if self.variant_id:
            current_stock = self.variant.stock_quantity if self.variant else 0
        else:
            current_stock = self.product.stock_quantity if self.product else 0
        
        suggested_qty = self.max_stock_level - current_stock
        return max(suggested_qty, self.reorder_quantity)
    
    def to_dict(self):
        """Convert reorder point to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'reorder_point': self.reorder_point,
            'reorder_quantity': self.reorder_quantity,
            'max_stock_level': self.max_stock_level,
            'preferred_supplier_id': self.preferred_supplier_id,
            'preferred_supplier_name': self.preferred_supplier.name if self.preferred_supplier else None,
            'lead_time_days': self.lead_time_days,
            'is_active': self.is_active,
            'needs_reorder': self.needs_reorder(),
            'suggested_order_quantity': self.calculate_suggested_order_quantity(),
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_active_reorder_points(tenant_id=None):
        """Get all active reorder points"""
        query = ReorderPoint.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_items_needing_reorder(tenant_id=None):
        """Get all items that need to be reordered"""
        items = []
        reorder_points = ReorderPoint.get_active_reorder_points(tenant_id)
        
        for rp in reorder_points:
            if rp.needs_reorder():
                items.append(rp)
        
        return items
    
    def __repr__(self):
        return f'<ReorderPoint {self.product.name if self.product else "Unknown"}: {self.reorder_point}>'