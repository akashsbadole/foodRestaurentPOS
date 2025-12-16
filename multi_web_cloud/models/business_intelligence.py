from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class BusinessMetric(FeatureAwareModel):
    """Business metric model for tracking KPIs and performance indicators"""
    __tablename__ = 'business_metrics'
    
    # Feature requirements
    required_features = ['FEATURE_BUSINESS_INTELLIGENCE']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Metric classification
    category = db.Column(db.String(50), default='Sales')  # Sales, Inventory, Customer, Financial, Operational
    metric_type = db.Column(db.String(20), default='Value')  # Value, Count, Percentage, Ratio, Rate
    
    # Metric configuration
    unit = db.Column(db.String(20), nullable=True)  # Currency, Items, Hours, Percentage, etc.
    target_value = db.Column(db.Numeric(15, 4), nullable=True)
    warning_threshold = db.Column(db.Numeric(15, 4), nullable=True)
    critical_threshold = db.Column(db.Numeric(15, 4), nullable=True)
    
    # Calculation configuration
    calculation_method = db.Column(db.String(50), default='Sum')  # Sum, Average, Count, Min, Max, Custom
    calculation_formula = db.Column(db.Text, nullable=True)  # SQL or custom formula
    
    # Data source
    data_source = db.Column(db.String(50), default='Orders')  # Orders, Products, Customers, Inventory
    data_filters = db.Column(db.Text, nullable=True)  # JSON filters for data source
    
    # Visualization
    chart_type = db.Column(db.String(20), default='Line')  # Line, Bar, Pie, Gauge, etc.
    color_scheme = db.Column(db.String(20), default='Default')
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_real_time = db.Column(db.Boolean, default=False)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_metrics')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_metrics')
    values = db.relationship('MetricValue', backref='metric', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, description=None, category='Sales', metric_type='Value',
                 unit=None, target_value=None, warning_threshold=None, critical_threshold=None,
                 calculation_method='Sum', calculation_formula=None, data_source='Orders',
                 data_filters=None, chart_type='Line', color_scheme='Default',
                 is_active=True, is_real_time=False, tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.category = category
        self.metric_type = metric_type
        self.unit = unit
        self.target_value = Decimal(str(target_value)) if target_value else None
        self.warning_threshold = Decimal(str(warning_threshold)) if warning_threshold else None
        self.critical_threshold = Decimal(str(critical_threshold)) if critical_threshold else None
        self.calculation_method = calculation_method
        self.calculation_formula = calculation_formula
        self.data_source = data_source
        self.data_filters = data_filters or '{}'
        self.chart_type = chart_type
        self.color_scheme = color_scheme
        self.is_active = is_active
        self.is_real_time = is_real_time
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_percentage_metric(self):
        """Check if metric is percentage-based"""
        return self.metric_type == 'Percentage' or self.unit == 'Percentage'
    
    @property
    def is_currency_metric(self):
        """Check if metric is currency-based"""
        return self.unit == 'Currency'
    
    @property
    def has_targets(self):
        """Check if metric has target values"""
        return self.target_value is not None
    
    @property
    def has_thresholds(self):
        """Check if metric has warning/critical thresholds"""
        return self.warning_threshold is not None or self.critical_threshold is not None
    
    def get_latest_value(self):
        """Get the latest metric value"""
        return MetricValue.query.filter_by(metric_id=self.id).order_by(MetricValue.recorded_at.desc()).first()
    
    def get_value_status(self, value):
        """Get status based on value thresholds"""
        if not self.has_thresholds:
            return 'Normal'
        
        if self.critical_threshold is not None:
            if self.metric_type in ['Value', 'Count']:
                if value >= self.critical_threshold:
                    return 'Critical'
            elif self.metric_type == 'Percentage':
                if value >= self.critical_threshold:
                    return 'Critical'
        
        if self.warning_threshold is not None:
            if self.metric_type in ['Value', 'Count']:
                if value >= self.warning_threshold:
                    return 'Warning'
            elif self.metric_type == 'Percentage':
                if value >= self.warning_threshold:
                    return 'Warning'
        
        return 'Normal'
    
    def activate(self):
        """Activate metric"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate metric"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_by_category(category, tenant_id=None):
        """Get metrics by category"""
        query = BusinessMetric.query.filter_by(category=category, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(BusinessMetric.name).all()
    
    @staticmethod
    def get_real_time_metrics(tenant_id=None):
        """Get real-time metrics"""
        query = BusinessMetric.query.filter_by(is_active=True, is_real_time=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(BusinessMetric.category, BusinessMetric.name).all()
    
    def to_dict(self, include_latest_value=False):
        """Convert business metric to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'metric_type': self.metric_type,
            'unit': self.unit,
            'target_value': float(self.target_value) if self.target_value else None,
            'warning_threshold': float(self.warning_threshold) if self.warning_threshold else None,
            'critical_threshold': float(self.critical_threshold) if self.critical_threshold else None,
            'calculation_method': self.calculation_method,
            'calculation_formula': self.calculation_formula,
            'data_source': self.data_source,
            'data_filters': self.data_filters,
            'chart_type': self.chart_type,
            'color_scheme': self.color_scheme,
            'is_active': self.is_active,
            'is_real_time': self.is_real_time,
            'is_percentage_metric': self.is_percentage_metric,
            'is_currency_metric': self.is_currency_metric,
            'has_targets': self.has_targets,
            'has_thresholds': self.has_thresholds,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
        
        if include_latest_value:
            latest_value = self.get_latest_value()
            if latest_value:
                data['latest_value'] = latest_value.to_dict()
                data['latest_value']['status'] = self.get_value_status(latest_value.value)
            else:
                data['latest_value'] = None
        
        return data
    
    def __repr__(self):
        return f'<BusinessMetric {self.name}>'


class MetricValue(db.Model):
    """Metric value model for storing historical metric values"""
    __tablename__ = 'metric_values'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_id = db.Column(db.Integer, db.ForeignKey('business_metrics.id'), nullable=False)
    
    # Value details
    value = db.Column(db.Numeric(15, 4), nullable=False)
    previous_value = db.Column(db.Numeric(15, 4), nullable=True)
    
    # Time period
    period_type = db.Column(db.String(20), default='Daily')  # Hourly, Daily, Weekly, Monthly, Yearly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Additional data
    metadata = db.Column(db.Text, nullable=True)  # JSON with additional context
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, metric_id, value, period_type='Daily', period_start=None,
                 period_end=None, previous_value=None, metadata=None, tenant_id=None):
        self.metric_id = metric_id
        self.value = Decimal(str(value))
        self.period_type = period_type
        self.period_start = period_start or date.today()
        self.period_end = period_end or date.today()
        self.previous_value = Decimal(str(previous_value)) if previous_value else None
        self.metadata = metadata or '{}'
        self.tenant_id = tenant_id
    
    @property
    def change_percentage(self):
        """Calculate percentage change from previous value"""
        if not self.previous_value or self.previous_value == 0:
            return None
        return ((self.value - self.previous_value) / self.previous_value) * 100
    
    @property
    def is_positive_change(self):
        """Check if change is positive"""
        if not self.previous_value:
            return None
        return self.value > self.previous_value
    
    @property
    def is_negative_change(self):
        """Check if change is negative"""
        if not self.previous_value:
            return None
        return self.value < self.previous_value
    
    @staticmethod
    def get_by_metric(metric_id, limit=100, tenant_id=None):
        """Get values for a metric"""
        query = MetricValue.query.filter_by(metric_id=metric_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(MetricValue.period_start.desc()).limit(limit).all()
    
    @staticmethod
    def get_by_period(period_type, period_start, period_end, tenant_id=None):
        """Get values by period"""
        query = MetricValue.query.filter(
            MetricValue.period_type == period_type,
            MetricValue.period_start >= period_start,
            MetricValue.period_end <= period_end
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(MetricValue.metric_id, MetricValue.period_start).all()
    
    def to_dict(self):
        """Convert metric value to dictionary"""
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'metric_name': self.metric.name if self.metric else None,
            'value': float(self.value),
            'previous_value': float(self.previous_value) if self.previous_value else None,
            'change_percentage': float(self.change_percentage) if self.change_percentage is not None else None,
            'is_positive_change': self.is_positive_change,
            'is_negative_change': self.is_negative_change,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'metadata': self.metadata,
            'tenant_id': self.tenant_id,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None
        }
    
    def __repr__(self):
        return f'<MetricValue {self.metric.name if self.metric else "Unknown"}: {self.value}>'


class SalesTarget(FeatureAwareModel):
    """Sales target model for setting and tracking sales goals"""
    __tablename__ = 'sales_targets'
    
    # Feature requirements
    required_features = ['FEATURE_SALES_TARGETS']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Target period
    period_type = db.Column(db.String(20), default='Monthly')  # Daily, Weekly, Monthly, Quarterly, Yearly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Target values
    target_amount = db.Column(db.Numeric(15, 2), nullable=False)
    target_quantity = db.Column(db.Integer, default=0)
    target_transactions = db.Column(db.Integer, default=0)
    
    # Target breakdown
    product_targets = db.Column(db.Text, nullable=True)  # JSON with product-specific targets
    category_targets = db.Column(db.Text, nullable=True)  # JSON with category-specific targets
    
    # Assignment
    assigned_to = db.Column(db.String(20), default='All')  # All, User, Team, Store
    assigned_id = db.Column(db.Integer, nullable=True)  # User ID, Team ID, or Store ID
    
    # Status
    status = db.Column(db.String(20), default='Active')  # Active, Completed, Cancelled
    
    # Achievement tracking
    achieved_amount = db.Column(db.Numeric(15, 2), default=0)
    achieved_quantity = db.Column(db.Integer, default=0)
    achieved_transactions = db.Column(db.Integer, default=0)
    achievement_percentage = db.Column(db.Numeric(5, 2), default=0)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_sales_targets')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_sales_targets')
    
    def __init__(self, name, period_type='Monthly', period_start=None, period_end=None,
                 target_amount=0, target_quantity=0, target_transactions=0,
                 product_targets=None, category_targets=None, assigned_to='All',
                 assigned_id=None, status='Active', description=None, tenant_id=None, created_by=None):
        self.name = name
        self.period_type = period_type
        self.period_start = period_start or date.today()
        self.period_end = period_end or date.today()
        self.target_amount = Decimal(str(target_amount))
        self.target_quantity = target_quantity
        self.target_transactions = target_transactions
        self.product_targets = product_targets or '{}'
        self.category_targets = category_targets or '{}'
        self.assigned_to = assigned_to
        self.assigned_id = assigned_id
        self.status = status
        self.description = description
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_active(self):
        """Check if target is active"""
        return self.status == 'Active'
    
    @property
    def is_completed(self):
        """Check if target is completed"""
        return self.status == 'Completed'
    
    @property
    def is_cancelled(self):
        """Check if target is cancelled"""
        return self.status == 'Cancelled'
    
    @property
    def is_achieved(self):
        """Check if target is achieved"""
        return self.achievement_percentage >= 100
    
    @property
    def days_remaining(self):
        """Calculate days remaining in target period"""
        if not self.is_active:
            return 0
        today = date.today()
        if today > self.period_end:
            return 0
        return (self.period_end - today).days + 1
    
    def calculate_achievement(self):
        """Calculate achievement percentage"""
        if self.target_amount == 0:
            self.achievement_percentage = 0
        else:
            self.achievement_percentage = (self.achieved_amount / self.target_amount) * 100
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_achievement(self, achieved_amount=0, achieved_quantity=0, achieved_transactions=0):
        """Update achievement values"""
        self.achieved_amount = Decimal(str(achieved_amount))
        self.achieved_quantity = achieved_quantity
        self.achieved_transactions = achieved_transactions
        self.calculate_achievement()
    
    def complete(self):
        """Mark target as completed"""
        self.status = 'Completed'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def cancel(self):
        """Cancel target"""
        self.status = 'Cancelled'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_active_targets(tenant_id=None):
        """Get active sales targets"""
        query = SalesTarget.query.filter_by(status='Active')
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SalesTarget.period_end).all()
    
    @staticmethod
    def get_by_period(period_type, period_start, period_end, tenant_id=None):
        """Get targets by period"""
        query = SalesTarget.query.filter(
            SalesTarget.period_type == period_type,
            SalesTarget.period_start >= period_start,
            SalesTarget.period_end <= period_end
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(SalesTarget.name).all()
    
    def to_dict(self):
        """Convert sales target to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'target_amount': float(self.target_amount),
            'target_quantity': self.target_quantity,
            'target_transactions': self.target_transactions,
            'product_targets': self.product_targets,
            'category_targets': self.category_targets,
            'assigned_to': self.assigned_to,
            'assigned_id': self.assigned_id,
            'status': self.status,
            'achieved_amount': float(self.achieved_amount),
            'achieved_quantity': self.achieved_quantity,
            'achieved_transactions': self.achieved_transactions,
            'achievement_percentage': float(self.achievement_percentage),
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'is_cancelled': self.is_cancelled,
            'is_achieved': self.is_achieved,
            'days_remaining': self.days_remaining,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
    
    def __repr__(self):
        return f'<SalesTarget {self.name} ({self.achievement_percentage:.1f}%)>'


class CustomerSegment(FeatureAwareModel):
    """Customer segment model for customer segmentation analysis"""
    __tablename__ = 'customer_segments'
    
    # Feature requirements
    required_features = ['FEATURE_CUSTOMER_SEGMENTATION']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Segment criteria
    criteria = db.Column(db.Text, nullable=False)  # JSON with segmentation criteria
    
    # Segment type
    segment_type = db.Column(db.String(20), default='Custom')  # Custom, RFM, Demographic, Behavioral
    
    # Segment statistics
    customer_count = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Numeric(15, 2), default=0)
    average_order_value = db.Column(db.Numeric(10, 2), default=0)
    last_purchase_date = db.Column(db.Date, nullable=True)
    
    # Segment characteristics
    characteristics = db.Column(db.Text, nullable=True)  # JSON with segment characteristics
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_dynamic = db.Column(db.Boolean, default=True)  # Auto-update based on criteria
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_segments')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_segments')
    members = db.relationship('CustomerSegmentMember', backref='segment', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, criteria, segment_type='Custom', description=None,
                 characteristics=None, is_active=True, is_dynamic=True,
                 tenant_id=None, created_by=None):
        self.name = name
        self.criteria = criteria
        self.segment_type = segment_type
        self.description = description
        self.characteristics = characteristics or '{}'
        self.is_active = is_active
        self.is_dynamic = is_dynamic
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def is_custom_segment(self):
        """Check if segment is custom"""
        return self.segment_type == 'Custom'
    
    @property
    def is_rfm_segment(self):
        """Check if segment is RFM-based"""
        return self.segment_type == 'RFM'
    
    @property
    def is_demographic_segment(self):
        """Check if segment is demographic-based"""
        return self.segment_type == 'Demographic'
    
    @property
    def is_behavioral_segment(self):
        """Check if segment is behavioral-based"""
        return self.segment_type == 'Behavioral'
    
    def calculate_statistics(self):
        """Calculate segment statistics"""
        from sqlalchemy import func
        
        # Get customer count
        self.customer_count = CustomerSegmentMember.query.filter_by(segment_id=self.id).count()
        
        # Calculate total revenue and average order value
        # This would need to be implemented based on your actual data structure
        # For now, we'll set placeholder values
        self.total_revenue = Decimal('0')
        self.average_order_value = Decimal('0')
        
        # Get last purchase date
        # This would need to be implemented based on your actual data structure
        self.last_purchase_date = None
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_members(self, customer_ids):
        """Update segment members"""
        # Remove existing members
        CustomerSegmentMember.query.filter_by(segment_id=self.id).delete()
        
        # Add new members
        for customer_id in customer_ids:
            member = CustomerSegmentMember(
                segment_id=self.id,
                customer_id=customer_id,
                tenant_id=self.tenant_id
            )
            db.session.add(member)
        
        # Calculate statistics
        self.calculate_statistics()
    
    def activate(self):
        """Activate segment"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate segment"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_active_segments(tenant_id=None):
        """Get active segments"""
        query = CustomerSegment.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(CustomerSegment.segment_type, CustomerSegment.name).all()
    
    @staticmethod
    def get_by_type(segment_type, tenant_id=None):
        """Get segments by type"""
        query = CustomerSegment.query.filter_by(segment_type=segment_type, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(CustomerSegment.name).all()
    
    def to_dict(self):
        """Convert customer segment to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'criteria': self.criteria,
            'segment_type': self.segment_type,
            'customer_count': self.customer_count,
            'total_revenue': float(self.total_revenue),
            'average_order_value': float(self.average_order_value),
            'last_purchase_date': self.last_purchase_date.isoformat() if self.last_purchase_date else None,
            'characteristics': self.characteristics,
            'is_active': self.is_active,
            'is_dynamic': self.is_dynamic,
            'is_custom_segment': self.is_custom_segment,
            'is_rfm_segment': self.is_rfm_segment,
            'is_demographic_segment': self.is_demographic_segment,
            'is_behavioral_segment': self.is_behavioral_segment,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
    
    def __repr__(self):
        return f'<CustomerSegment {self.name} ({self.customer_count} customers)>'


class CustomerSegmentMember(db.Model):
    """Customer segment member model for linking customers to segments"""
    __tablename__ = 'customer_segment_members'
    
    id = db.Column(db.Integer, primary_key=True)
    segment_id = db.Column(db.Integer, db.ForeignKey('customer_segments.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    
    # Membership details
    score = db.Column(db.Numeric(5, 2), nullable=True)  # Segment score or confidence
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Relationships
    customer = db.relationship('Customer', backref='segment_memberships')
    
    def __init__(self, segment_id, customer_id, score=None, tenant_id=None):
        self.segment_id = segment_id
        self.customer_id = customer_id
        self.score = Decimal(str(score)) if score else None
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert segment member to dictionary"""
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'segment_name': self.segment.name if self.segment else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'score': float(self.score) if self.score else None,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'tenant_id': self.tenant_id
        }
    
    def __repr__(self):
        return f'<CustomerSegmentMember {self.customer.name_decrypted if self.customer else "Unknown"} in {self.segment.name if self.segment else "Unknown"}>'


class ProductPerformance(FeatureAwareModel):
    """Product performance model for tracking product analytics"""
    __tablename__ = 'product_performance'
    
    # Feature requirements
    required_features = ['FEATURE_PRODUCT_ANALYTICS']
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id'), nullable=True)
    
    # Performance period
    period_type = db.Column(db.String(20), default='Monthly')  # Daily, Weekly, Monthly, Quarterly, Yearly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Sales metrics
    quantity_sold = db.Column(db.Integer, default=0)
    revenue = db.Column(db.Numeric(15, 2), default=0)
    profit = db.Column(db.Numeric(15, 2), default=0)
    profit_margin = db.Column(db.Numeric(5, 2), default=0)
    
    # Order metrics
    order_count = db.Column(db.Integer, default=0)
    average_order_quantity = db.Column(db.Numeric(10, 2), default=0)
    average_order_value = db.Column(db.Numeric(10, 2), default=0)
    
    # Customer metrics
    unique_customers = db.Column(db.Integer, default=0)
    repeat_customers = db.Column(db.Integer, default=0)
    repeat_purchase_rate = db.Column(db.Numeric(5, 2), default=0)
    
    # Inventory metrics
    inventory_turns = db.Column(db.Numeric(10, 2), default=0)
    days_of_supply = db.Column(db.Numeric(10, 2), default=0)
    
    # Performance rating
    performance_rating = db.Column(db.String(10), default='Average')  # Excellent, Good, Average, Poor, Critical
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    product = db.relationship('Product', backref='performance_data')
    variant = db.relationship('ProductVariant', backref='performance_data')
    
    def __init__(self, product_id, period_type='Monthly', period_start=None, period_end=None,
                 variant_id=None, quantity_sold=0, revenue=0, profit=0, order_count=0,
                 unique_customers=0, repeat_customers=0, inventory_turns=0,
                 days_of_supply=0, tenant_id=None):
        self.product_id = product_id
        self.period_type = period_type
        self.period_start = period_start or date.today()
        self.period_end = period_end or date.today()
        self.variant_id = variant_id
        self.quantity_sold = quantity_sold
        self.revenue = Decimal(str(revenue))
        self.profit = Decimal(str(profit))
        self.order_count = order_count
        self.unique_customers = unique_customers
        self.repeat_customers = repeat_customers
        self.inventory_turns = Decimal(str(inventory_turns))
        self.days_of_supply = Decimal(str(days_of_supply))
        self.tenant_id = tenant_id
        
        # Calculate derived metrics
        self.calculate_derived_metrics()
    
    def calculate_derived_metrics(self):
        """Calculate derived performance metrics"""
        # Calculate profit margin
        if self.revenue > 0:
            self.profit_margin = (self.profit / self.revenue) * 100
        else:
            self.profit_margin = 0
        
        # Calculate average order quantity
        if self.order_count > 0:
            self.average_order_quantity = self.quantity_sold / self.order_count
        else:
            self.average_order_quantity = 0
        
        # Calculate average order value
        if self.order_count > 0:
            self.average_order_value = self.revenue / self.order_count
        else:
            self.average_order_value = 0
        
        # Calculate repeat purchase rate
        if self.unique_customers > 0:
            self.repeat_purchase_rate = (self.repeat_customers / self.unique_customers) * 100
        else:
            self.repeat_purchase_rate = 0
        
        # Calculate performance rating
        if self.profit_margin >= 50:
            self.performance_rating = 'Excellent'
        elif self.profit_margin >= 30:
            self.performance_rating = 'Good'
        elif self.profit_margin >= 10:
            self.performance_rating = 'Average'
        elif self.profit_margin >= 0:
            self.performance_rating = 'Poor'
        else:
            self.performance_rating = 'Critical'
        
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def get_by_product(product_id, limit=12, tenant_id=None):
        """Get performance data for a product"""
        query = ProductPerformance.query.filter_by(product_id=product_id)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductPerformance.period_start.desc()).limit(limit).all()
    
    @staticmethod
    def get_top_performing(period_type='Monthly', limit=10, tenant_id=None):
        """Get top performing products"""
        query = ProductPerformance.query.filter_by(period_type=period_type)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductPerformance.revenue.desc()).limit(limit).all()
    
    @staticmethod
    def get_bottom_performing(period_type='Monthly', limit=10, tenant_id=None):
        """Get bottom performing products"""
        query = ProductPerformance.query.filter_by(period_type=period_type)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ProductPerformance.revenue.asc()).limit(limit).all()
    
    def to_dict(self):
        """Convert product performance to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'variant_id': self.variant_id,
            'variant_name': self.variant.variant_name if self.variant else None,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'quantity_sold': self.quantity_sold,
            'revenue': float(self.revenue),
            'profit': float(self.profit),
            'profit_margin': float(self.profit_margin),
            'order_count': self.order_count,
            'average_order_quantity': float(self.average_order_quantity),
            'average_order_value': float(self.average_order_value),
            'unique_customers': self.unique_customers,
            'repeat_customers': self.repeat_customers,
            'repeat_purchase_rate': float(self.repeat_purchase_rate),
            'inventory_turns': float(self.inventory_turns),
            'days_of_supply': float(self.days_of_supply),
            'performance_rating': self.performance_rating,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ProductPerformance {self.product.name if self.product else "Unknown"}: {float(self.revenue)} revenue>'