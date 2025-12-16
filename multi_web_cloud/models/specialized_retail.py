"""
Specialized Retail module models for handling custom attributes, service booking, 
repair and warranty tracking, and rental and consignment management.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from models import db
from models.feature_aware_model import FeatureAwareModel


class CustomProduct(FeatureAwareModel):
    """Custom product with specialized attributes for niche retail businesses"""
    __tablename__ = 'custom_products'
    __feature_key__ = 'FEATURE_SPECIALIZED_PRODUCTS'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    product_code = Column(String(50), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    specialized_category = Column(String(100))  # Electronics, Jewelry, Art, etc.
    brand = Column(String(100))
    model = Column(String(100))
    sku = Column(String(100))
    
    # Pricing
    cost_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2))
    market_price = Column(Numeric(10, 2))
    
    # Inventory
    quantity = Column(Integer, default=0)
    min_quantity = Column(Integer, default=0)
    max_quantity = Column(Integer)
    reorder_level = Column(Integer, default=0)
    
    # Custom attributes (JSON field for flexibility)
    custom_attributes = Column(JSON)
    technical_specifications = Column(JSON)
    dimensions = Column(JSON)  # Length, width, height, weight
    material_specifications = Column(JSON)
    
    # Specialized fields
    serial_number_required = Column(Boolean, default=False)
    warranty_period_months = Column(Integer)
    warranty_terms = Column(Text)
    care_instructions = Column(Text)
    usage_instructions = Column(Text)
    safety_warnings = Column(Text)
    
    # Service and maintenance
    service_required = Column(Boolean, default=False)
    service_interval_months = Column(Integer)
    last_service_date = Column(Date)
    next_service_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_new_arrival = Column(Boolean, default=False)
    is_on_sale = Column(Boolean, default=False)
    is_discontinued = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='custom_products')
    creator = relationship('User', foreign_keys=[created_by])
    custom_attributes_values = relationship('CustomAttributeValue', back_populates='product', cascade='all, delete-orphan')
    service_bookings = relationship('ServiceBooking', back_populates='product')
    repair_records = relationship('RepairRecord', back_populates='product')
    warranty_claims = relationship('WarrantyClaim', back_populates='product')
    rental_items = relationship('RentalItem', back_populates='product')
    consignment_items = relationship('ConsignmentItem', back_populates='product')
    
    def __repr__(self):
        return f'<CustomProduct {self.product_code}: {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'product_code': self.product_code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'specialized_category': self.specialized_category,
            'brand': self.brand,
            'model': self.model,
            'sku': self.sku,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'selling_price': float(self.selling_price) if self.selling_price else None,
            'market_price': float(self.market_price) if self.market_price else None,
            'quantity': self.quantity,
            'min_quantity': self.min_quantity,
            'max_quantity': self.max_quantity,
            'reorder_level': self.reorder_level,
            'custom_attributes': self.custom_attributes,
            'technical_specifications': self.technical_specifications,
            'dimensions': self.dimensions,
            'material_specifications': self.material_specifications,
            'serial_number_required': self.serial_number_required,
            'warranty_period_months': self.warranty_period_months,
            'warranty_terms': self.warranty_terms,
            'care_instructions': self.care_instructions,
            'usage_instructions': self.usage_instructions,
            'safety_warnings': self.safety_warnings,
            'service_required': self.service_required,
            'service_interval_months': self.service_interval_months,
            'last_service_date': self.last_service_date.isoformat() if self.last_service_date else None,
            'next_service_date': self.next_service_date.isoformat() if self.next_service_date else None,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'is_new_arrival': self.is_new_arrival,
            'is_on_sale': self.is_on_sale,
            'is_discontinued': self.is_discontinued,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level
    
    @hybrid_property
    def is_service_due(self):
        if not self.next_service_date:
            return False
        return self.next_service_date <= date.today()
    
    @hybrid_property
    def warranty_expired_date(self):
        if not self.warranty_period_months:
            return None
        # This would need to be calculated based on purchase date
        return None


class CustomAttribute(FeatureAwareModel):
    """Custom attribute definitions for specialized products"""
    __tablename__ = 'custom_attributes'
    __feature_key__ = 'FEATURE_CUSTOM_ATTRIBUTES'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    attribute_name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    attribute_type = Column(String(50), nullable=False)  # text, number, date, boolean, select, multiselect
    data_type = Column(String(50))  # string, integer, decimal, date, boolean
    description = Column(Text)
    
    # Validation rules
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    min_value = Column(Numeric(10, 2))
    max_value = Column(Numeric(10, 2))
    min_length = Column(Integer)
    max_length = Column(Integer)
    default_value = Column(String(500))
    
    # Options for select/multiselect types
    options = Column(JSON)  # List of valid options
    
    # Categorization
    category = Column(String(100))
    applies_to_categories = Column(JSON)  # Categories this attribute applies to
    applies_to_brands = Column(JSON)  # Brands this attribute applies to
    
    # Display settings
    display_order = Column(Integer, default=0)
    show_in_list = Column(Boolean, default=True)
    show_in_detail = Column(Boolean, default=True)
    show_in_filters = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='custom_attributes')
    attribute_values = relationship('CustomAttributeValue', back_populates='attribute', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CustomAttribute {self.attribute_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'attribute_name': self.attribute_name,
            'display_name': self.display_name,
            'attribute_type': self.attribute_type,
            'data_type': self.data_type,
            'description': self.description,
            'is_required': self.is_required,
            'is_unique': self.is_unique,
            'min_value': float(self.min_value) if self.min_value else None,
            'max_value': float(self.max_value) if self.max_value else None,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'default_value': self.default_value,
            'options': self.options,
            'category': self.category,
            'applies_to_categories': self.applies_to_categories,
            'applies_to_brands': self.applies_to_brands,
            'display_order': self.display_order,
            'show_in_list': self.show_in_list,
            'show_in_detail': self.show_in_detail,
            'show_in_filters': self.show_in_filters,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CustomAttributeValue(FeatureAwareModel):
    """Values for custom attributes assigned to products"""
    __tablename__ = 'custom_attribute_values'
    __feature_key__ = 'FEATURE_CUSTOM_ATTRIBUTES'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'), nullable=False)
    attribute_id = Column(Integer, ForeignKey('custom_attributes.id'), nullable=False)
    
    # Value storage (use appropriate column based on attribute type)
    text_value = Column(Text)
    number_value = Column(Numeric(15, 4))
    date_value = Column(Date)
    boolean_value = Column(Boolean)
    
    # For select/multiselect types
    selected_options = Column(JSON)  # Array of selected option values
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='custom_attribute_values')
    product = relationship('CustomProduct', back_populates='custom_attributes_values')
    attribute = relationship('CustomAttribute', back_populates='attribute_values')
    
    def __repr__(self):
        return f'<CustomAttributeValue {self.product_id}:{self.attribute_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'product_id': self.product_id,
            'attribute_id': self.attribute_id,
            'text_value': self.text_value,
            'number_value': float(self.number_value) if self.number_value else None,
            'date_value': self.date_value.isoformat() if self.date_value else None,
            'boolean_value': self.boolean_value,
            'selected_options': self.selected_options,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def value(self):
        """Get the appropriate value based on attribute type"""
        if self.text_value is not None:
            return self.text_value
        elif self.number_value is not None:
            return float(self.number_value)
        elif self.date_value is not None:
            return self.date_value.isoformat()
        elif self.boolean_value is not None:
            return self.boolean_value
        elif self.selected_options is not None:
            return self.selected_options
        return None


class ServiceBooking(FeatureAwareModel):
    """Service booking management for specialized products"""
    __tablename__ = 'service_bookings'
    __feature_key__ = 'FEATURE_SERVICE_BOOKING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    booking_number = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    
    # Service details
    service_type = Column(String(100), nullable=False)  # Installation, Maintenance, Repair, etc.
    service_description = Column(Text)
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Scheduling
    preferred_date = Column(Date)
    preferred_time = Column(String(50))  # Morning, Afternoon, Evening, or specific time
    scheduled_date = Column(Date)
    scheduled_time = Column(String(50))
    duration_hours = Column(Numeric(5, 2))
    
    # Location
    service_location = Column(String(100))  # On-site, In-store, Remote
    service_address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(20))
    
    # Technician assignment
    technician_id = Column(Integer, ForeignKey('users.id'))
    technician_notes = Column(Text)
    
    # Status tracking
    status = Column(String(50), default='scheduled')  # scheduled, in_progress, completed, cancelled
    completion_notes = Column(Text)
    completion_date = Column(DateTime)
    
    # Cost and billing
    estimated_cost = Column(Numeric(10, 2))
    actual_cost = Column(Numeric(10, 2))
    labor_cost = Column(Numeric(10, 2))
    parts_cost = Column(Numeric(10, 2))
    is_billable = Column(Boolean, default=True)
    invoice_id = Column(Integer, ForeignKey('payments.id'))
    
    # Customer feedback
    customer_rating = Column(Integer)  # 1-5 stars
    customer_feedback = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='service_bookings')
    product = relationship('CustomProduct', back_populates='service_bookings')
    customer = relationship('Customer', back_populates='service_bookings')
    technician = relationship('User', foreign_keys=[technician_id])
    creator = relationship('User', foreign_keys=[created_by])
    invoice = relationship('Payment', foreign_keys=[invoice_id])
    
    def __repr__(self):
        return f'<ServiceBooking {self.booking_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'booking_number': self.booking_number,
            'product_id': self.product_id,
            'customer_id': self.customer_id,
            'service_type': self.service_type,
            'service_description': self.service_description,
            'priority': self.priority,
            'preferred_date': self.preferred_date.isoformat() if self.preferred_date else None,
            'preferred_time': self.preferred_time,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'scheduled_time': self.scheduled_time,
            'duration_hours': float(self.duration_hours) if self.duration_hours else None,
            'service_location': self.service_location,
            'service_address': self.service_address,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'technician_id': self.technician_id,
            'technician_notes': self.technician_notes,
            'status': self.status,
            'completion_notes': self.completion_notes,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'estimated_cost': float(self.estimated_cost) if self.estimated_cost else None,
            'actual_cost': float(self.actual_cost) if self.actual_cost else None,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': float(self.parts_cost) if self.parts_cost else None,
            'is_billable': self.is_billable,
            'invoice_id': self.invoice_id,
            'customer_rating': self.customer_rating,
            'customer_feedback': self.customer_feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_overdue(self):
        if not self.scheduled_date or self.status in ['completed', 'cancelled']:
            return False
        return self.scheduled_date < date.today() and self.status == 'scheduled'


class RepairRecord(FeatureAwareModel):
    """Repair and maintenance records for specialized products"""
    __tablename__ = 'repair_records'
    __feature_key__ = 'FEATURE_REPAIR_TRACKING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    repair_number = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    
    # Repair details
    repair_type = Column(String(100), nullable=False)  # Warranty, Paid, Diagnostic, etc.
    problem_description = Column(Text)
    diagnosis = Column(Text)
    repair_actions = Column(Text)
    parts_replaced = Column(JSON)  # List of parts with quantities and costs
    
    # Status tracking
    status = Column(String(50), default='pending')  # pending, in_progress, completed, cancelled
    priority = Column(String(20), default='normal')
    
    # Technician assignment
    technician_id = Column(Integer, ForeignKey('users.id'))
    technician_notes = Column(Text)
    
    # Timing
    received_date = Column(DateTime, default=datetime.utcnow)
    estimated_completion_date = Column(DateTime)
    actual_completion_date = Column(DateTime)
    
    # Cost and billing
    diagnostic_fee = Column(Numeric(10, 2))
    labor_cost = Column(Numeric(10, 2))
    parts_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))
    is_warranty_repair = Column(Boolean, default=False)
    warranty_claim_id = Column(Integer, ForeignKey('warranty_claims.id'))
    invoice_id = Column(Integer, ForeignKey('payments.id'))
    
    # Customer communication
    customer_notified = Column(Boolean, default=False)
    customer_approval = Column(Boolean)
    customer_notes = Column(Text)
    
    # Quality control
    quality_check_passed = Column(Boolean)
    quality_check_notes = Column(Text)
    quality_check_by = Column(Integer, ForeignKey('users.id'))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='repair_records')
    product = relationship('CustomProduct', back_populates='repair_records')
    customer = relationship('Customer', back_populates='repair_records')
    technician = relationship('User', foreign_keys=[technician_id])
    creator = relationship('User', foreign_keys=[created_by])
    quality_checker = relationship('User', foreign_keys=[quality_check_by])
    warranty_claim = relationship('WarrantyClaim', back_populates='repair_records')
    invoice = relationship('Payment', foreign_keys=[invoice_id])
    
    def __repr__(self):
        return f'<RepairRecord {self.repair_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'repair_number': self.repair_number,
            'product_id': self.product_id,
            'customer_id': self.customer_id,
            'repair_type': self.repair_type,
            'problem_description': self.problem_description,
            'diagnosis': self.diagnosis,
            'repair_actions': self.repair_actions,
            'parts_replaced': self.parts_replaced,
            'status': self.status,
            'priority': self.priority,
            'technician_id': self.technician_id,
            'technician_notes': self.technician_notes,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'estimated_completion_date': self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,
            'actual_completion_date': self.actual_completion_date.isoformat() if self.actual_completion_date else None,
            'diagnostic_fee': float(self.diagnostic_fee) if self.diagnostic_fee else None,
            'labor_cost': float(self.labor_cost) if self.labor_cost else None,
            'parts_cost': float(self.parts_cost) if self.parts_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'is_warranty_repair': self.is_warranty_repair,
            'warranty_claim_id': self.warranty_claim_id,
            'invoice_id': self.invoice_id,
            'customer_notified': self.customer_notified,
            'customer_approval': self.customer_approval,
            'customer_notes': self.customer_notes,
            'quality_check_passed': self.quality_check_passed,
            'quality_check_notes': self.quality_check_notes,
            'quality_check_by': self.quality_check_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def is_overdue(self):
        if not self.estimated_completion_date or self.status in ['completed', 'cancelled']:
            return False
        return datetime.utcnow() > self.estimated_completion_date and self.status in ['pending', 'in_progress']


class WarrantyClaim(FeatureAwareModel):
    """Warranty claim management for specialized products"""
    __tablename__ = 'warranty_claims'
    __feature_key__ = 'FEATURE_WARRANTY_TRACKING'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    claim_number = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    
    # Purchase information
    purchase_date = Column(Date)
    purchase_invoice = Column(String(100))
    serial_number = Column(String(100))
    
    # Claim details
    claim_type = Column(String(100), nullable=False)  # Manufacturing defect, Damage, Performance issue, etc.
    issue_description = Column(Text)
    claim_date = Column(Date, default=date.today)
    
    # Warranty validation
    warranty_valid = Column(Boolean)
    warranty_expiry_date = Column(Date)
    warranty_terms_violated = Column(Boolean, default=False)
    violation_reason = Column(Text)
    
    # Assessment
    assessment_notes = Column(Text)
    assessment_by = Column(Integer, ForeignKey('users.id'))
    assessment_date = Column(DateTime)
    
    # Decision
    claim_status = Column(String(50), default='pending')  # pending, approved, rejected, in_progress, completed
    decision_date = Column(Date)
    decision_by = Column(Integer, ForeignKey('users.id'))
    decision_notes = Column(Text)
    
    # Resolution
    resolution_type = Column(String(100))  # Repair, Replacement, Refund, Partial refund
    resolution_details = Column(Text)
    replacement_product_id = Column(Integer, ForeignKey('custom_products.id'))
    refund_amount = Column(Numeric(10, 2))
    repair_cost = Column(Numeric(10, 2))
    
    # Customer communication
    customer_notified = Column(Boolean, default=False)
    customer_response = Column(String(500))
    customer_satisfaction = Column(Integer)  # 1-5 scale
    
    # Timeline tracking
    submission_date = Column(DateTime, default=datetime.utcnow)
    processing_start_date = Column(DateTime)
    completion_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='warranty_claims')
    product = relationship('CustomProduct', foreign_keys=[product_id], back_populates='warranty_claims')
    replacement_product = relationship('CustomProduct', foreign_keys=[replacement_product_id])
    customer = relationship('Customer', back_populates='warranty_claims')
    assessor = relationship('User', foreign_keys=[assessment_by])
    decision_maker = relationship('User', foreign_keys=[decision_by])
    creator = relationship('User', foreign_keys=[created_by])
    repair_records = relationship('RepairRecord', back_populates='warranty_claim')
    
    def __repr__(self):
        return f'<WarrantyClaim {self.claim_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'claim_number': self.claim_number,
            'product_id': self.product_id,
            'customer_id': self.customer_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_invoice': self.purchase_invoice,
            'serial_number': self.serial_number,
            'claim_type': self.claim_type,
            'issue_description': self.issue_description,
            'claim_date': self.claim_date.isoformat() if self.claim_date else None,
            'warranty_valid': self.warranty_valid,
            'warranty_expiry_date': self.warranty_expiry_date.isoformat() if self.warranty_expiry_date else None,
            'warranty_terms_violated': self.warranty_terms_violated,
            'violation_reason': self.violation_reason,
            'assessment_notes': self.assessment_notes,
            'assessment_by': self.assessment_by,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None,
            'claim_status': self.claim_status,
            'decision_date': self.decision_date.isoformat() if self.decision_date else None,
            'decision_by': self.decision_by,
            'decision_notes': self.decision_notes,
            'resolution_type': self.resolution_type,
            'resolution_details': self.resolution_details,
            'replacement_product_id': self.replacement_product_id,
            'refund_amount': float(self.refund_amount) if self.refund_amount else None,
            'repair_cost': float(self.repair_cost) if self.repair_cost else None,
            'customer_notified': self.customer_notified,
            'customer_response': self.customer_response,
            'customer_satisfaction': self.customer_satisfaction,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'processing_start_date': self.processing_start_date.isoformat() if self.processing_start_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def processing_days(self):
        if not self.submission_date:
            return None
        end_date = self.completion_date or datetime.utcnow()
        return (end_date - self.submission_date).days
    
    @hybrid_property
    def is_warranty_expired(self):
        if not self.warranty_expiry_date:
            return False
        return date.today() > self.warranty_expiry_date


class RentalItem(FeatureAwareModel):
    """Rental item management for specialized products"""
    __tablename__ = 'rental_items'
    __feature_key__ = 'FEATURE_RENTAL_MANAGEMENT'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    rental_number = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'))
    customer_id = Column(Integer, ForeignKey('customers.id'))
    
    # Rental terms
    rental_start_date = Column(Date, nullable=False)
    rental_end_date = Column(Date, nullable=False)
    actual_return_date = Column(Date)
    
    # Pricing
    daily_rate = Column(Numeric(10, 2))
    weekly_rate = Column(Numeric(10, 2))
    monthly_rate = Column(Numeric(10, 2))
    deposit_amount = Column(Numeric(10, 2))
    total_rental_cost = Column(Numeric(10, 2))
    
    # Insurance and liability
    insurance_required = Column(Boolean, default=False)
    insurance_cost = Column(Numeric(10, 2))
    damage_waiver = Column(Boolean, default=False)
    liability_limit = Column(Numeric(10, 2))
    
    # Item details
    serial_number = Column(String(100))
    condition_on_rental = Column(Text)
    condition_on_return = Column(Text)
    damage_notes = Column(Text)
    damage_charges = Column(Numeric(10, 2))
    
    # Status tracking
    status = Column(String(50), default='reserved')  # reserved, active, overdue, returned, closed
    payment_status = Column(String(50), default='pending')  # pending, paid, overdue, partial
    
    # Extension and renewal
    extension_allowed = Column(Boolean, default=True)
    extension_rate = Column(Numeric(10, 2))
    current_extension_end_date = Column(Date)
    
    # Late return handling
    late_fee_per_day = Column(Numeric(10, 2))
    grace_period_days = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='rental_items')
    product = relationship('CustomProduct', back_populates='rental_items')
    customer = relationship('Customer', back_populates='rental_items')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<RentalItem {self.rental_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'rental_number': self.rental_number,
            'product_id': self.product_id,
            'customer_id': self.customer_id,
            'rental_start_date': self.rental_start_date.isoformat() if self.rental_start_date else None,
            'rental_end_date': self.rental_end_date.isoformat() if self.rental_end_date else None,
            'actual_return_date': self.actual_return_date.isoformat() if self.actual_return_date else None,
            'daily_rate': float(self.daily_rate) if self.daily_rate else None,
            'weekly_rate': float(self.weekly_rate) if self.weekly_rate else None,
            'monthly_rate': float(self.monthly_rate) if self.monthly_rate else None,
            'deposit_amount': float(self.deposit_amount) if self.deposit_amount else None,
            'total_rental_cost': float(self.total_rental_cost) if self.total_rental_cost else None,
            'insurance_required': self.insurance_required,
            'insurance_cost': float(self.insurance_cost) if self.insurance_cost else None,
            'damage_waiver': self.damage_waiver,
            'liability_limit': float(self.liability_limit) if self.liability_limit else None,
            'serial_number': self.serial_number,
            'condition_on_rental': self.condition_on_rental,
            'condition_on_return': self.condition_on_return,
            'damage_notes': self.damage_notes,
            'damage_charges': float(self.damage_charges) if self.damage_charges else None,
            'status': self.status,
            'payment_status': self.payment_status,
            'extension_allowed': self.extension_allowed,
            'extension_rate': float(self.extension_rate) if self.extension_rate else None,
            'current_extension_end_date': self.current_extension_end_date.isoformat() if self.current_extension_end_date else None,
            'late_fee_per_day': float(self.late_fee_per_day) if self.late_fee_per_day else None,
            'grace_period_days': self.grace_period_days,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def rental_days(self):
        if not self.rental_start_date or not self.rental_end_date:
            return 0
        return (self.rental_end_date - self.rental_start_date).days + 1
    
    @hybrid_property
    def days_overdue(self):
        if not self.rental_end_date or self.actual_return_date or self.status in ['returned', 'closed']:
            return 0
        overdue_days = (date.today() - self.rental_end_date).days
        return max(0, overdue_days - self.grace_period_days)
    
    @hybrid_property
    def is_overdue(self):
        return self.days_overdue > 0
    
    @hybrid_property
    def late_fees(self):
        return self.days_overdue * (self.late_fee_per_day or 0)


class ConsignmentItem(FeatureAwareModel):
    """Consignment item management for specialized products"""
    __tablename__ = 'consignment_items'
    __feature_key__ = 'FEATURE_CONSIGNMENT_MANAGEMENT'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    consignment_number = Column(String(50), nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey('custom_products.id'))
    consignor_id = Column(Integer, ForeignKey('customers.id'))  # The person who owns the item
    
    # Consignment terms
    consignment_start_date = Column(Date, nullable=False)
    consignment_end_date = Column(Date)
    actual_sale_date = Column(Date)
    
    # Pricing
    asking_price = Column(Numeric(10, 2))
    minimum_acceptable_price = Column(Numeric(10, 2))
    actual_sale_price = Column(Numeric(10, 2))
    
    # Commission structure
    commission_rate = Column(Numeric(5, 2))  # Percentage
    commission_amount = Column(Numeric(10, 2))
    flat_fee = Column(Numeric(10, 2))
    commission_type = Column(String(20), default='percentage')  # percentage, flat, hybrid
    
    # Payment to consignor
    payment_status = Column(String(50), default='pending')  # pending, paid, partial, withheld
    payment_date = Column(Date)
    payment_amount = Column(Numeric(10, 2))
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    
    # Item details
    item_condition = Column(String(50))  # new, like_new, good, fair, poor
    condition_notes = Column(Text)
    authenticity_verified = Column(Boolean, default=False)
    appraisal_value = Column(Numeric(10, 2))
    appraisal_date = Column(Date)
    appraiser_notes = Column(Text)
    
    # Marketing and display
    display_location = Column(String(100))
    featured_item = Column(Boolean, default=False)
    marketing_notes = Column(Text)
    photo_urls = Column(JSON)  # Array of image URLs
    
    # Status tracking
    status = Column(String(50), default='received')  # received, on_display, sold, returned, expired
    
    # Contract terms
    contract_terms = Column(Text)
    auto_price_reduction = Column(Boolean, default=False)
    price_reduction_schedule = Column(JSON)  # Schedule for automatic price reductions
    return_unsold_items = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    tenant = relationship('Tenant', back_populates='consignment_items')
    product = relationship('CustomProduct', back_populates='consignment_items')
    consignor = relationship('Customer', foreign_keys=[consignor_id], back_populates='consignment_items')
    creator = relationship('User', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<ConsignmentItem {self.consignment_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'consignment_number': self.consignment_number,
            'product_id': self.product_id,
            'consignor_id': self.consignor_id,
            'consignment_start_date': self.consignment_start_date.isoformat() if self.consignment_start_date else None,
            'consignment_end_date': self.consignment_end_date.isoformat() if self.consignment_end_date else None,
            'actual_sale_date': self.actual_sale_date.isoformat() if self.actual_sale_date else None,
            'asking_price': float(self.asking_price) if self.asking_price else None,
            'minimum_acceptable_price': float(self.minimum_acceptable_price) if self.minimum_acceptable_price else None,
            'actual_sale_price': float(self.actual_sale_price) if self.actual_sale_price else None,
            'commission_rate': float(self.commission_rate) if self.commission_rate else None,
            'commission_amount': float(self.commission_amount) if self.commission_amount else None,
            'flat_fee': float(self.flat_fee) if self.flat_fee else None,
            'commission_type': self.commission_type,
            'payment_status': self.payment_status,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_amount': float(self.payment_amount) if self.payment_amount else None,
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'item_condition': self.item_condition,
            'condition_notes': self.condition_notes,
            'authenticity_verified': self.authenticity_verified,
            'appraisal_value': float(self.appraisal_value) if self.appraisal_value else None,
            'appraisal_date': self.appraisal_date.isoformat() if self.appraisal_date else None,
            'appraiser_notes': self.appraiser_notes,
            'display_location': self.display_location,
            'featured_item': self.featured_item,
            'marketing_notes': self.marketing_notes,
            'photo_urls': self.photo_urls,
            'status': self.status,
            'contract_terms': self.contract_terms,
            'auto_price_reduction': self.auto_price_reduction,
            'price_reduction_schedule': self.price_reduction_schedule,
            'return_unsold_items': self.return_unsold_items,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @hybrid_property
    def days_on_consignment(self):
        if not self.consignment_start_date:
            return 0
        end_date = self.actual_sale_date or date.today()
        return (end_date - self.consignment_start_date).days
    
    @hybrid_property
    def is_expired(self):
        if not self.consignment_end_date:
            return False
        return date.today() > self.consignment_end_date and self.status != 'sold'
    
    @hybrid_property
    def calculate_commission(self):
        """Calculate commission based on sale price and commission structure"""
        if not self.actual_sale_price:
            return 0
        
        if self.commission_type == 'percentage':
            return float(self.actual_sale_price) * (float(self.commission_rate or 0) / 100)
        elif self.commission_type == 'flat':
            return float(self.flat_fee or 0)
        elif self.commission_type == 'hybrid':
            return float(self.actual_sale_price) * (float(self.commission_rate or 0) / 100) + float(self.flat_fee or 0)
        
        return 0
    
    @hybrid_property
    def consignor_payout(self):
        """Calculate the amount to be paid to the consignor"""
        if not self.actual_sale_price:
            return 0
        return float(self.actual_sale_price) - self.calculate_commission