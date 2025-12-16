from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class Barcode(FeatureAwareModel):
    """Barcode model for product barcode generation and tracking"""
    __tablename__ = 'barcodes'
    
    # Feature requirements
    required_features = ['FEATURE_BARCODE']
    
    id = db.Column(db.Integer, primary_key=True)
    barcode_value = db.Column(db.String(50), unique=True, nullable=False, index=True)
    barcode_type = db.Column(db.String(20), default='CODE128')  # CODE128, EAN13, UPC, QR, etc.
    
    # Product association
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Barcode details
    barcode_format = db.Column(db.String(20), default='Standard')  # Standard, Custom, Supplier
    is_primary = db.Column(db.Boolean, default=False)  # Primary barcode for the product
    is_active = db.Column(db.Boolean, default=True)
    
    # Additional data (for QR codes, etc.)
    additional_data = db.Column(db.Text, nullable=True)  # JSON data for complex barcodes
    
    # Generation information
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    generation_method = db.Column(db.String(20), default='System')  # System, Manual, Imported
    
    # Usage tracking
    last_scanned = db.Column(db.DateTime, nullable=True)
    scan_count = db.Column(db.Integer, default=0)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='barcodes')
    variant = db.relationship('ProductVariant', backref='barcodes')
    generator = db.relationship('User', backref='generated_barcodes')
    
    def __init__(self, barcode_value, product_id, barcode_type='CODE128',
                 variant_id=None, barcode_format='Standard', is_primary=False,
                 is_active=True, additional_data=None, generated_at=None,
                 generated_by=None, generation_method='System', tenant_id=None):
        self.barcode_value = barcode_value
        self.barcode_type = barcode_type
        self.product_id = product_id
        self.variant_id = variant_id
        self.barcode_format = barcode_format
        self.is_primary = is_primary
        self.is_active = is_active
        self.additional_data = additional_data
        self.generated_at = generated_at or datetime.utcnow()
        self.generated_by = generated_by
        self.generation_method = generation_method
        self.tenant_id = tenant_id
    
    @property
    def is_qr_code(self):
        """Check if barcode is a QR code"""
        return self.barcode_type.upper() == 'QR'
    
    @property
    def is_upc(self):
        """Check if barcode is UPC format"""
        return self.barcode_type.upper() in ['UPC', 'UPCA', 'UPCE']
    
    @property
    def is_ean(self):
        """Check if barcode is EAN format"""
        return self.barcode_type.upper() in ['EAN', 'EAN13', 'EAN8']
    
    def record_scan(self):
        """Record a scan event"""
        self.last_scanned = datetime.utcnow()
        self.scan_count += 1
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate barcode"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def activate(self):
        """Activate barcode"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def set_primary(self):
        """Set as primary barcode for product"""
        # Unset other primary barcodes for this product
        if self.variant_id:
            Barcode.query.filter_by(
                product_id=self.product_id,
                variant_id=self.variant_id,
                is_primary=True
            ).update({'is_primary': False})
        else:
            Barcode.query.filter_by(
                product_id=self.product_id,
                variant_id=None,
                is_primary=True
            ).update({'is_primary': False})
        
        self.is_primary = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def generate_barcode(product_id, barcode_type='CODE128', variant_id=None, 
                        barcode_format='Standard', generated_by=None, tenant_id=None):
        """Generate a new barcode"""
        # Generate unique barcode value
        if barcode_type.upper() == 'CODE128':
            # Generate a random CODE128 barcode
            import random
            barcode_value = f"POS{random.randint(100000000, 999999999)}"
        elif barcode_type.upper() == 'EAN13':
            # Generate a valid EAN13 barcode
            import random
            base = f"{random.randint(100000000000, 999999999999)}"
            # Calculate checksum
            checksum = 0
            for i, digit in enumerate(base):
                multiplier = 1 if i % 2 == 0 else 3
                checksum += int(digit) * multiplier
            checksum = (10 - (checksum % 10)) % 10
            barcode_value = base + str(checksum)
        elif barcode_type.upper() == 'UPC':
            # Generate a valid UPC barcode
            import random
            base = f"{random.randint(10000000000, 99999999999)}"
            # Calculate checksum
            checksum = 0
            for i, digit in enumerate(base):
                multiplier = 3 if i % 2 == 0 else 1
                checksum += int(digit) * multiplier
            checksum = (10 - (checksum % 10)) % 10
            barcode_value = base + str(checksum)
        else:
            # Default to CODE128
            import random
            barcode_value = f"POS{random.randint(100000000, 999999999)}"
        
        # Create barcode
        barcode = Barcode(
            barcode_value=barcode_value,
            barcode_type=barcode_type,
            product_id=product_id,
            variant_id=variant_id,
            barcode_format=barcode_format,
            generated_by=generated_by,
            tenant_id=tenant_id
        )
        
        db.session.add(barcode)
        db.session.commit()
        return barcode
    
    @staticmethod
    def get_by_value(barcode_value, tenant_id=None):
        """Get barcode by value"""
        query = Barcode.query.filter_by(barcode_value=barcode_value)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_primary_barcode(product_id, variant_id=None, tenant_id=None):
        """Get primary barcode for product"""
        query = Barcode.query.filter_by(
            product_id=product_id,
            variant_id=variant_id,
            is_primary=True
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_product_barcodes(product_id, variant_id=None, tenant_id=None):
        """Get all barcodes for a product"""
        query = Barcode.query.filter_by(product_id=product_id)
        if variant_id is not None:
            query = query.filter_by(variant_id=variant_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(Barcode.is_primary.desc(), Barcode.created_at).all()
    
    def to_dict(self):
        """Convert barcode to dictionary"""
        return {
            'id': self.id,
            'barcode_value': self.barcode_value,
            'barcode_type': self.barcode_type,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'barcode_format': self.barcode_format,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'additional_data': self.additional_data,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'generated_by': self.generated_by,
            'generator_name': self.generator.username if self.generator else None,
            'generation_method': self.generation_method,
            'last_scanned': self.last_scanned.isoformat() if self.last_scanned else None,
            'scan_count': self.scan_count,
            'is_qr_code': self.is_qr_code,
            'is_upc': self.is_upc,
            'is_ean': self.is_ean,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Barcode {self.barcode_value} ({self.barcode_type})>'


class BarcodeScan(db.Model):
    """Barcode scan history model"""
    __tablename__ = 'barcode_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    barcode_id = db.Column(db.Integer, db.ForeignKey('barcodes.id'), nullable=False)
    
    # Scan details
    scan_time = db.Column(db.DateTime, default=datetime.utcnow)
    scan_type = db.Column(db.String(20), default='Product')  # Product, Inventory, Sale, Return
    
    # Context information
    context_type = db.Column(db.String(20), nullable=True)  # Order, StockAdjustment, etc.
    context_id = db.Column(db.Integer, nullable=True)
    
    # User and device information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    device_id = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    
    # Additional information
    notes = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Relationships
    barcode = db.relationship('Barcode', backref='scans')
    user = db.relationship('User', backref='barcode_scans')
    
    def __init__(self, barcode_id, scan_type='Product', context_type=None,
                 context_id=None, user_id=None, device_id=None, location=None,
                 notes=None, tenant_id=None):
        self.barcode_id = barcode_id
        self.scan_type = scan_type
        self.context_type = context_type
        self.context_id = context_id
        self.user_id = user_id
        self.device_id = device_id
        self.location = location
        self.notes = notes
        self.tenant_id = tenant_id
        
        # Update barcode scan count
        barcode = Barcode.query.get(barcode_id)
        if barcode:
            barcode.record_scan()
    
    def to_dict(self):
        """Convert barcode scan to dictionary"""
        return {
            'id': self.id,
            'barcode_id': self.barcode_id,
            'barcode_value': self.barcode.barcode_value if self.barcode else None,
            'product_id': self.barcode.product_id if self.barcode else None,
            'product_name': self.barcode.product.name if self.barcode and self.barcode.product else None,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None,
            'scan_type': self.scan_type,
            'context_type': self.context_type,
            'context_id': self.context_id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'device_id': self.device_id,
            'location': self.location,
            'notes': self.notes,
            'tenant_id': self.tenant_id
        }
    
    def __repr__(self):
        return f'<BarcodeScan {self.barcode.barcode_value if self.barcode else "Unknown"} at {self.scan_time}>'


class BarcodeLabel(FeatureAwareModel):
    """Barcode label template model"""
    __tablename__ = 'barcode_labels'
    
    # Feature requirements
    required_features = ['FEATURE_BARCODE_LABEL']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Label configuration
    label_size = db.Column(db.String(20), default='Standard')  # Standard, Small, Large, Custom
    width = db.Column(db.Numeric(8, 2), default=50.8)  # Width in mm (2 inches)
    height = db.Column(db.Numeric(8, 2), default=25.4)  # Height in mm (1 inch)
    
    # Barcode configuration
    barcode_type = db.Column(db.String(20), default='CODE128')
    barcode_height = db.Column(db.Numeric(5, 2), default=15.0)  # Height in mm
    barcode_width = db.Column(db.Numeric(5, 2), default=0.33)  # Width ratio
    
    # Text configuration
    show_product_name = db.Column(db.Boolean, default=True)
    show_sku = db.Column(db.Boolean, default=True)
    show_price = db.Column(db.Boolean, default=False)
    show_barcode_value = db.Column(db.Boolean, default=True)
    
    font_size = db.Column(db.Integer, default=8)
    text_alignment = db.Column(db.String(10), default='Center')  # Left, Center, Right
    
    # Layout configuration
    layout_type = db.Column(db.String(20), default='Standard')  # Standard, Compact, Detailed
    margin_top = db.Column(db.Numeric(5, 2), default=2.0)
    margin_bottom = db.Column(db.Numeric(5, 2), default=2.0)
    margin_left = db.Column(db.Numeric(5, 2), default=2.0)
    margin_right = db.Column(db.Numeric(5, 2), default=2.0)
    
    # Status
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_barcode_labels')
    
    def __init__(self, name, description=None, label_size='Standard',
                 width=50.8, height=25.4, barcode_type='CODE128',
                 barcode_height=15.0, barcode_width=0.33,
                 show_product_name=True, show_sku=True, show_price=False,
                 show_barcode_value=True, font_size=8, text_alignment='Center',
                 layout_type='Standard', margin_top=2.0, margin_bottom=2.0,
                 margin_left=2.0, margin_right=2.0, is_default=False,
                 is_active=True, tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.label_size = label_size
        self.width = Decimal(str(width))
        self.height = Decimal(str(height))
        self.barcode_type = barcode_type
        self.barcode_height = Decimal(str(barcode_height))
        self.barcode_width = Decimal(str(barcode_width))
        self.show_product_name = show_product_name
        self.show_sku = show_sku
        self.show_price = show_price
        self.show_barcode_value = show_barcode_value
        self.font_size = font_size
        self.text_alignment = text_alignment
        self.layout_type = layout_type
        self.margin_top = Decimal(str(margin_top))
        self.margin_bottom = Decimal(str(margin_bottom))
        self.margin_left = Decimal(str(margin_left))
        self.margin_right = Decimal(str(margin_right))
        self.is_default = is_default
        self.is_active = is_active
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    def set_default(self):
        """Set as default label template"""
        # Unset other default templates
        BarcodeLabel.query.filter_by(
            tenant_id=self.tenant_id,
            is_default=True
        ).update({'is_default': False})
        
        self.is_default = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate label template"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def activate(self):
        """Activate label template"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_default_template(tenant_id=None):
        """Get default label template"""
        query = BarcodeLabel.query.filter_by(is_default=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_active_templates(tenant_id=None):
        """Get all active label templates"""
        query = BarcodeLabel.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(BarcodeLabel.is_default.desc(), BarcodeLabel.name).all()
    
    def to_dict(self):
        """Convert barcode label to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'label_size': self.label_size,
            'width': float(self.width),
            'height': float(self.height),
            'barcode_type': self.barcode_type,
            'barcode_height': float(self.barcode_height),
            'barcode_width': float(self.barcode_width),
            'show_product_name': self.show_product_name,
            'show_sku': self.show_sku,
            'show_price': self.show_price,
            'show_barcode_value': self.show_barcode_value,
            'font_size': self.font_size,
            'text_alignment': self.text_alignment,
            'layout_type': self.layout_type,
            'margin_top': float(self.margin_top),
            'margin_bottom': float(self.margin_bottom),
            'margin_left': float(self.margin_left),
            'margin_right': float(self.margin_right),
            'is_default': self.is_default,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    def __repr__(self):
        return f'<BarcodeLabel {self.name}>'


class BarcodePrintJob(db.Model):
    """Barcode print job model"""
    __tablename__ = 'barcode_print_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # Job details
    label_template_id = db.Column(db.Integer, db.ForeignKey('barcode_labels.id'), nullable=False)
    printer_name = db.Column(db.String(100), nullable=True)
    
    # Print status
    status = db.Column(db.String(20), default='Pending')  # Pending, Printing, Completed, Failed
    total_labels = db.Column(db.Integer, default=0)
    printed_labels = db.Column(db.Integer, default=0)
    failed_labels = db.Column(db.Integer, default=0)
    
    # Timing
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    label_template = db.relationship('BarcodeLabel', backref='print_jobs')
    creator = db.relationship('User', backref='barcode_print_jobs')
    items = db.relationship('BarcodePrintItem', backref='print_job', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, label_template_id, printer_name=None, total_labels=0,
                 tenant_id=None, created_by=None):
        self.job_number = self.generate_job_number()
        self.label_template_id = label_template_id
        self.printer_name = printer_name
        self.total_labels = total_labels
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @staticmethod
    def generate_job_number():
        """Generate unique job number"""
        prefix = "BPJ"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_pending(self):
        """Check if job is pending"""
        return self.status == 'Pending'
    
    @property
    def is_printing(self):
        """Check if job is printing"""
        return self.status == 'Printing'
    
    @property
    def is_completed(self):
        """Check if job is completed"""
        return self.status == 'Completed'
    
    @property
    def is_failed(self):
        """Check if job failed"""
        return self.status == 'Failed'
    
    @property
    def progress_percentage(self):
        """Get progress percentage"""
        if self.total_labels == 0:
            return 0
        return (self.printed_labels / self.total_labels) * 100
    
    def start_printing(self):
        """Start printing job"""
        self.status = 'Printing'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete(self):
        """Complete printing job"""
        self.status = 'Completed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def fail(self, error_message=None):
        """Mark job as failed"""
        self.status = 'Failed'
        self.completed_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_progress(self, printed_labels=0, failed_labels=0):
        """Update print progress"""
        self.printed_labels += printed_labels
        self.failed_labels += failed_labels
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_items=True):
        """Convert print job to dictionary"""
        data = {
            'id': self.id,
            'job_number': self.job_number,
            'label_template_id': self.label_template_id,
            'template_name': self.label_template.name if self.label_template else None,
            'printer_name': self.printer_name,
            'status': self.status,
            'total_labels': self.total_labels,
            'printed_labels': self.printed_labels,
            'failed_labels': self.failed_labels,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'is_pending': self.is_pending,
            'is_printing': self.is_printing,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data
    
    def __repr__(self):
        return f'<BarcodePrintJob {self.job_number} ({self.status})>'


class BarcodePrintItem(db.Model):
    """Barcode print item model"""
    __tablename__ = 'barcode_print_items'
    
    id = db.Column(db.Integer, primary_key=True)
    print_job_id = db.Column(db.Integer, db.ForeignKey('barcode_print_jobs.id'), nullable=False)
    
    # Item details
    barcode_id = db.Column(db.Integer, db.ForeignKey('barcodes.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Print status
    status = db.Column(db.String(20), default='Pending')  # Pending, Printed, Failed
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    barcode = db.relationship('Barcode', backref='print_items')
    
    def __init__(self, print_job_id, barcode_id, quantity=1, tenant_id=None):
        self.print_job_id = print_job_id
        self.barcode_id = barcode_id
        self.quantity = quantity
        self.tenant_id = tenant_id
    
    @property
    def is_pending(self):
        """Check if item is pending"""
        return self.status == 'Pending'
    
    @property
    def is_printed(self):
        """Check if item is printed"""
        return self.status == 'Printed'
    
    @property
    def is_failed(self):
        """Check if item failed"""
        return self.status == 'Failed'
    
    def mark_printed(self):
        """Mark item as printed"""
        self.status = 'Printed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_failed(self, error_message=None):
        """Mark item as failed"""
        self.status = 'Failed'
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """Convert print item to dictionary"""
        return {
            'id': self.id,
            'print_job_id': self.print_job_id,
            'job_number': self.print_job.job_number if self.print_job else None,
            'barcode_id': self.barcode_id,
            'barcode_value': self.barcode.barcode_value if self.barcode else None,
            'product_id': self.barcode.product_id if self.barcode else None,
            'product_name': self.barcode.product.name if self.barcode and self.barcode.product else None,
            'quantity': self.quantity,
            'status': self.status,
            'error_message': self.error_message,
            'is_pending': self.is_pending,
            'is_printed': self.is_printed,
            'is_failed': self.is_failed,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<BarcodePrintItem {self.barcode.barcode_value if self.barcode else "Unknown"}: {self.quantity}>'