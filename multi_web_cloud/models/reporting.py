from datetime import datetime, date
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class ReportTemplate(FeatureAwareModel):
    """Report template model for custom reports"""
    __tablename__ = 'report_templates'
    
    # Feature requirements
    required_features = ['FEATURE_REPORTING']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), default='Sales')  # Sales, Inventory, Customers, Employees, Financial
    
    # Report configuration
    report_type = db.Column(db.String(20), default='Summary')  # Summary, Detailed, Comparative, Trend
    data_source = db.Column(db.String(50), default='Orders')  # Orders, Products, Customers, Inventory
    
    # Report structure
    columns = db.Column(db.Text, nullable=False)  # JSON array of column definitions
    filters = db.Column(db.Text, nullable=True)  # JSON array of filter definitions
    groupings = db.Column(db.Text, nullable=True)  # JSON array of grouping definitions
    calculations = db.Column(db.Text, nullable=True)  # JSON array of calculation definitions
    
    # Report formatting
    date_format = db.Column(db.String(20), default='%Y-%m-%d')
    number_format = db.Column(db.String(20), default='0.00')
    currency_format = db.Column(db.String(20), default='$0.00')
    
    # Chart configuration
    chart_type = db.Column(db.String(20), nullable=True)  # Bar, Line, Pie, Area, etc.
    chart_config = db.Column(db.Text, nullable=True)  # JSON chart configuration
    
    # Status
    is_public = db.Column(db.Boolean, default=False)  # Available to all users
    is_active = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_report_templates')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_report_templates')
    schedules = db.relationship('ReportSchedule', backref='template', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, description=None, category='Sales', report_type='Summary',
                 data_source='Orders', columns=None, filters=None, groupings=None,
                 calculations=None, date_format='%Y-%m-%d', number_format='0.00',
                 currency_format='$0.00', chart_type=None, chart_config=None,
                 is_public=False, is_active=True, tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.category = category
        self.report_type = report_type
        self.data_source = data_source
        self.columns = columns or '[]'
        self.filters = filters or '[]'
        self.groupings = groupings or '[]'
        self.calculations = calculations or '[]'
        self.date_format = date_format
        self.number_format = number_format
        self.currency_format = currency_format
        self.chart_type = chart_type
        self.chart_config = chart_config
        self.is_public = is_public
        self.is_active = is_active
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    @property
    def has_chart(self):
        """Check if report has chart configuration"""
        return self.chart_type is not None and self.chart_config is not None
    
    def activate(self):
        """Activate report template"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate report template"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def make_public(self):
        """Make report template public"""
        self.is_public = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def make_private(self):
        """Make report template private"""
        self.is_public = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_by_category(category, tenant_id=None):
        """Get report templates by category"""
        query = ReportTemplate.query.filter_by(category=category, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportTemplate.name).all()
    
    @staticmethod
    def get_public_templates(tenant_id=None):
        """Get public report templates"""
        query = ReportTemplate.query.filter_by(is_public=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportTemplate.category, ReportTemplate.name).all()
    
    @staticmethod
    def get_user_templates(user_id, tenant_id=None):
        """Get templates created by user"""
        query = ReportTemplate.query.filter_by(created_by=user_id, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportTemplate.category, ReportTemplate.name).all()
    
    def to_dict(self):
        """Convert report template to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'report_type': self.report_type,
            'data_source': self.data_source,
            'columns': self.columns,
            'filters': self.filters,
            'groupings': self.groupings,
            'calculations': self.calculations,
            'date_format': self.date_format,
            'number_format': self.number_format,
            'currency_format': self.currency_format,
            'chart_type': self.chart_type,
            'chart_config': self.chart_config,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'has_chart': self.has_chart,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
    
    def __repr__(self):
        return f'<ReportTemplate {self.name}>'


class ReportSchedule(FeatureAwareModel):
    """Report schedule model for automated report generation"""
    __tablename__ = 'report_schedules'
    
    # Feature requirements
    required_features = ['FEATURE_SCHEDULED_REPORTS']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Report configuration
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'), nullable=False)
    
    # Schedule configuration
    frequency = db.Column(db.String(20), default='Daily')  # Daily, Weekly, Monthly, Quarterly, Yearly
    schedule_time = db.Column(db.Time, nullable=True)  # Time of day to run
    schedule_day = db.Column(db.Integer, nullable=True)  # Day of week (1-7) or day of month (1-31)
    
    # Date range configuration
    date_range_type = db.Column(db.String(20), default='Previous')  # Previous, Current, Custom
    custom_date_range = db.Column(db.Text, nullable=True)  # JSON with start_date and end_date
    
    # Output configuration
    output_format = db.Column(db.String(10), default='PDF')  # PDF, Excel, CSV, HTML
    email_recipients = db.Column(db.Text, nullable=True)  # JSON array of email addresses
    save_to_file = db.Column(db.Boolean, default=True)
    file_path = db.Column(db.String(255), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    creator = db.relationship('User', backref='created_report_schedules')
    executions = db.relationship('ReportExecution', backref='schedule', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, template_id, frequency='Daily', schedule_time=None,
                 schedule_day=None, date_range_type='Previous', custom_date_range=None,
                 output_format='PDF', email_recipients=None, save_to_file=True,
                 file_path=None, is_active=True, description=None, tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.template_id = template_id
        self.frequency = frequency
        self.schedule_time = schedule_time
        self.schedule_day = schedule_day
        self.date_range_type = date_range_type
        self.custom_date_range = custom_date_range
        self.output_format = output_format
        self.email_recipients = email_recipients or '[]'
        self.save_to_file = save_to_file
        self.file_path = file_path
        self.is_active = is_active
        self.tenant_id = tenant_id
        self.created_by = created_by
        
        # Calculate next run time
        self.calculate_next_run()
    
    @property
    def is_daily(self):
        """Check if schedule is daily"""
        return self.frequency == 'Daily'
    
    @property
    def is_weekly(self):
        """Check if schedule is weekly"""
        return self.frequency == 'Weekly'
    
    @property
    def is_monthly(self):
        """Check if schedule is monthly"""
        return self.frequency == 'Monthly'
    
    @property
    def is_quarterly(self):
        """Check if schedule is quarterly"""
        return self.frequency == 'Quarterly'
    
    @property
    def is_yearly(self):
        """Check if schedule is yearly"""
        return self.frequency == 'Yearly'
    
    def calculate_next_run(self):
        """Calculate next run time based on schedule"""
        from datetime import time, timedelta
        
        now = datetime.utcnow()
        
        if self.frequency == 'Daily':
            next_run = now.date() + timedelta(days=1)
            if self.schedule_time:
                next_run = datetime.combine(next_run, self.schedule_time)
            else:
                next_run = datetime.combine(next_run, time(9, 0))  # Default 9:00 AM
        
        elif self.frequency == 'Weekly':
            days_ahead = (self.schedule_day or 1) - now.weekday() - 1
            if days_ahead <= 0:
                days_ahead += 7
            next_run_date = now.date() + timedelta(days=days_ahead)
            if self.schedule_time:
                next_run = datetime.combine(next_run_date, self.schedule_time)
            else:
                next_run = datetime.combine(next_run_date, time(9, 0))
        
        elif self.frequency == 'Monthly':
            if now.day <= (self.schedule_day or 1):
                next_run_month = now.month
                next_run_year = now.year
            else:
                if now.month == 12:
                    next_run_month = 1
                    next_run_year = now.year + 1
                else:
                    next_run_month = now.month + 1
                    next_run_year = now.year
            
            next_run_date = date(next_run_year, next_run_month, self.schedule_day or 1)
            if self.schedule_time:
                next_run = datetime.combine(next_run_date, self.schedule_time)
            else:
                next_run = datetime.combine(next_run_date, time(9, 0))
        
        elif self.frequency == 'Quarterly':
            current_quarter = (now.month - 1) // 3 + 1
            if now.month <= (self.schedule_day or 1):
                next_quarter = current_quarter
                next_year = now.year
            else:
                if current_quarter == 4:
                    next_quarter = 1
                    next_year = now.year + 1
                else:
                    next_quarter = current_quarter + 1
                    next_year = now.year
            
            next_month = (next_quarter - 1) * 3 + 1
            next_run_date = date(next_year, next_month, self.schedule_day or 1)
            if self.schedule_time:
                next_run = datetime.combine(next_run_date, self.schedule_time)
            else:
                next_run = datetime.combine(next_run_date, time(9, 0))
        
        elif self.frequency == 'Yearly':
            if now.month <= (self.schedule_day or 1):
                next_year = now.year
            else:
                next_year = now.year + 1
            
            next_run_date = date(next_year, self.schedule_day or 1, 1)
            if self.schedule_time:
                next_run = datetime.combine(next_run_date, self.schedule_time)
            else:
                next_run = datetime.combine(next_run_date, time(9, 0))
        
        else:
            next_run = now + timedelta(days=1)
        
        self.next_run = next_run
        db.session.commit()
    
    def activate(self):
        """Activate schedule"""
        self.is_active = True
        self.calculate_next_run()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate schedule"""
        self.is_active = False
        self.next_run = None
        db.session.commit()
    
    @staticmethod
    def get_due_schedules():
        """Get schedules that are due to run"""
        now = datetime.utcnow()
        return ReportSchedule.query.filter(
            ReportSchedule.is_active == True,
            ReportSchedule.next_run <= now
        ).all()
    
    @staticmethod
    def get_active_schedules(tenant_id=None):
        """Get all active schedules"""
        query = ReportSchedule.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportSchedule.next_run).all()
    
    def to_dict(self):
        """Convert report schedule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_id': self.template_id,
            'template_name': self.template.name if self.template else None,
            'frequency': self.frequency,
            'schedule_time': self.schedule_time.isoformat() if self.schedule_time else None,
            'schedule_day': self.schedule_day,
            'date_range_type': self.date_range_type,
            'custom_date_range': self.custom_date_range,
            'output_format': self.output_format,
            'email_recipients': self.email_recipients,
            'save_to_file': self.save_to_file,
            'file_path': self.file_path,
            'is_active': self.is_active,
            'is_daily': self.is_daily,
            'is_weekly': self.is_weekly,
            'is_monthly': self.is_monthly,
            'is_quarterly': self.is_quarterly,
            'is_yearly': self.is_yearly,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None
        }
    
    def __repr__(self):
        return f'<ReportSchedule {self.name} ({self.frequency})>'


class ReportExecution(db.Model):
    """Report execution model for tracking report runs"""
    __tablename__ = 'report_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('report_schedules.id'), nullable=True)
    
    # Execution details
    execution_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'), nullable=False)
    
    # Execution status
    status = db.Column(db.String(20), default='Running')  # Running, Completed, Failed, Cancelled
    
    # Timing
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    
    # Results
    records_processed = db.Column(db.Integer, default=0)
    output_file_path = db.Column(db.String(255), nullable=True)
    output_file_size = db.Column(db.Integer, nullable=True)
    
    # Error information
    error_message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    
    # Execution parameters
    parameters = db.Column(db.Text, nullable=True)  # JSON of parameters used
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    # Relationships
    template = db.relationship('ReportTemplate', backref='executions')
    
    def __init__(self, template_id, schedule_id=None, parameters=None, tenant_id=None):
        self.execution_id = self.generate_execution_id()
        self.template_id = template_id
        self.schedule_id = schedule_id
        self.parameters = parameters or '{}'
        self.tenant_id = tenant_id
    
    @staticmethod
    def generate_execution_id():
        """Generate unique execution ID"""
        prefix = "EXEC"
        date_str = datetime.now().strftime("%Y%m%d")
        import random
        random_str = f"{random.randint(1000, 9999)}"
        return f"{prefix}{date_str}{random_str}"
    
    @property
    def is_running(self):
        """Check if execution is running"""
        return self.status == 'Running'
    
    @property
    def is_completed(self):
        """Check if execution is completed"""
        return self.status == 'Completed'
    
    @property
    def is_failed(self):
        """Check if execution failed"""
        return self.status == 'Failed'
    
    @property
    def is_cancelled(self):
        """Check if execution is cancelled"""
        return self.status == 'Cancelled'
    
    @property
    def duration(self):
        """Get execution duration in human readable format"""
        if not self.duration_seconds:
            return "N/A"
        
        if self.duration_seconds < 60:
            return f"{self.duration_seconds} seconds"
        elif self.duration_seconds < 3600:
            minutes = self.duration_seconds // 60
            seconds = self.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = self.duration_seconds // 3600
            minutes = (self.duration_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def complete(self, output_file_path=None, output_file_size=None, records_processed=0):
        """Mark execution as completed"""
        self.status = 'Completed'
        self.completed_at = datetime.utcnow()
        self.output_file_path = output_file_path
        self.output_file_size = output_file_size
        self.records_processed = records_processed
        
        # Calculate duration
        if self.started_at and self.completed_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        db.session.commit()
    
    def fail(self, error_message=None, error_details=None):
        """Mark execution as failed"""
        self.status = 'Failed'
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_details = error_details
        
        # Calculate duration
        if self.started_at and self.completed_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        db.session.commit()
    
    def cancel(self):
        """Mark execution as cancelled"""
        self.status = 'Cancelled'
        self.completed_at = datetime.utcnow()
        
        # Calculate duration
        if self.started_at and self.completed_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        db.session.commit()
    
    @staticmethod
    def get_by_status(status, tenant_id=None):
        """Get executions by status"""
        query = ReportExecution.query.filter_by(status=status)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportExecution.started_at.desc()).all()
    
    @staticmethod
    def get_recent_executions(limit=10, tenant_id=None):
        """Get recent executions"""
        query = ReportExecution.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(ReportExecution.started_at.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert report execution to dictionary"""
        return {
            'id': self.id,
            'schedule_id': self.schedule_id,
            'schedule_name': self.schedule.name if self.schedule else None,
            'execution_id': self.execution_id,
            'template_id': self.template_id,
            'template_name': self.template.name if self.template else None,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'duration': self.duration,
            'records_processed': self.records_processed,
            'output_file_path': self.output_file_path,
            'output_file_size': self.output_file_size,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'parameters': self.parameters,
            'is_running': self.is_running,
            'is_completed': self.is_completed,
            'is_failed': self.is_failed,
            'is_cancelled': self.is_cancelled,
            'tenant_id': self.tenant_id
        }
    
    def __repr__(self):
        return f'<ReportExecution {self.execution_id} ({self.status})>'


class AnalyticsCache(FeatureAwareModel):
    """Analytics cache model for storing pre-calculated metrics"""
    __tablename__ = 'analytics_cache'
    
    # Feature requirements
    required_features = ['FEATURE_ANALYTICS']
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Cache data
    data_type = db.Column(db.String(20), default='Summary')  # Summary, Chart, Metric
    metric_name = db.Column(db.String(100), nullable=True)
    
    # Time period
    period_type = db.Column(db.String(20), default='Daily')  # Hourly, Daily, Weekly, Monthly, Yearly
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Cache data
    cache_data = db.Column(db.Text, nullable=False)  # JSON data
    data_hash = db.Column(db.String(64), nullable=True)  # Hash of data for integrity check
    
    # Cache metadata
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    hit_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, nullable=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    
    def __init__(self, cache_key, data_type='Summary', metric_name=None,
                 period_type='Daily', period_start=None, period_end=None,
                 cache_data=None, expires_hours=24, tenant_id=None):
        self.cache_key = cache_key
        self.data_type = data_type
        self.metric_name = metric_name
        self.period_type = period_type
        self.period_start = period_start or date.today()
        self.period_end = period_end or date.today()
        self.cache_data = cache_data or '{}'
        self.tenant_id = tenant_id
        
        # Set expiration
        if expires_hours:
            from datetime import timedelta
            self.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        # Calculate data hash
        self.calculate_hash()
    
    @property
    def is_expired(self):
        """Check if cache is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if cache is valid (not expired)"""
        return not self.is_expired
    
    def calculate_hash(self):
        """Calculate hash of cache data"""
        import hashlib
        self.data_hash = hashlib.sha256(self.cache_data.encode()).hexdigest()
    
    def record_access(self):
        """Record cache access"""
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()
        db.session.commit()
    
    def update_data(self, cache_data, expires_hours=None):
        """Update cache data"""
        self.cache_data = cache_data
        self.calculate_hash()
        
        if expires_hours:
            from datetime import timedelta
            self.expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        self.calculated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_by_key(cache_key, tenant_id=None):
        """Get cache by key"""
        query = AnalyticsCache.query.filter_by(cache_key=cache_key)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_valid_cache(cache_key, tenant_id=None):
        """Get valid cache by key"""
        cache = AnalyticsCache.get_by_key(cache_key, tenant_id)
        if cache and cache.is_valid:
            cache.record_access()
            return cache
        return None
    
    @staticmethod
    def get_by_period(period_type, period_start, period_end, tenant_id=None):
        """Get cache by period"""
        query = AnalyticsCache.query.filter_by(
            period_type=period_type,
            period_start=period_start,
            period_end=period_end
        )
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def get_expired_cache(tenant_id=None):
        """Get expired cache entries"""
        now = datetime.utcnow()
        query = AnalyticsCache.query.filter(AnalyticsCache.expires_at < now)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    @staticmethod
    def cleanup_expired(tenant_id=None):
        """Clean up expired cache entries"""
        expired = AnalyticsCache.get_expired_cache(tenant_id)
        for cache in expired:
            db.session.delete(cache)
        db.session.commit()
        return len(expired)
    
    def to_dict(self):
        """Convert analytics cache to dictionary"""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'data_type': self.data_type,
            'metric_name': self.metric_name,
            'period_type': self.period_type,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'cache_data': self.cache_data,
            'data_hash': self.data_hash,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'hit_count': self.hit_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'tenant_id': self.tenant_id
        }
    
    def __repr__(self):
        return f'<AnalyticsCache {self.cache_key}>'


class DashboardConfig(FeatureAwareModel):
    """Dashboard configuration model"""
    __tablename__ = 'dashboard_configs'
    
    # Feature requirements
    required_features = ['FEATURE_DASHBOARD']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Dashboard type
    dashboard_type = db.Column(db.String(20), default='General')  # General, Sales, Inventory, Financial
    
    # Layout configuration
    layout_type = db.Column(db.String(20), default='Grid')  # Grid, Tabs, Accordion
    columns = db.Column(db.Integer, default=3)
    rows = db.Column(db.Integer, default=4)
    
    # Widget configuration
    widgets = db.Column(db.Text, nullable=False)  # JSON array of widget definitions
    
    # Filters configuration
    filters = db.Column(db.Text, nullable=True)  # JSON array of filter definitions
    
    # Refresh configuration
    auto_refresh = db.Column(db.Boolean, default=True)
    refresh_interval = db.Column(db.Integer, default=300)  # Seconds
    
    # Status
    is_default = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_dashboard_configs')
    updater = db.relationship('User', foreign_keys=[updated_by], backref='updated_dashboard_configs')
    
    def __init__(self, name, description=None, dashboard_type='General',
                 layout_type='Grid', columns=3, rows=4, widgets=None,
                 filters=None, auto_refresh=True, refresh_interval=300,
                 is_default=False, is_public=False, is_active=True,
                 tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.dashboard_type = dashboard_type
        self.layout_type = layout_type
        self.columns = columns
        self.rows = rows
        self.widgets = widgets or '[]'
        self.filters = filters or '[]'
        self.auto_refresh = auto_refresh
        self.refresh_interval = refresh_interval
        self.is_default = is_default
        self.is_public = is_public
        self.is_active = is_active
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    def set_default(self):
        """Set as default dashboard"""
        # Unset other default dashboards
        DashboardConfig.query.filter_by(
            tenant_id=self.tenant_id,
            is_default=True
        ).update({'is_default': False})
        
        self.is_default = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def activate(self):
        """Activate dashboard"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate dashboard"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def make_public(self):
        """Make dashboard public"""
        self.is_public = True
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def make_private(self):
        """Make dashboard private"""
        self.is_public = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_default_dashboard(tenant_id=None):
        """Get default dashboard"""
        query = DashboardConfig.query.filter_by(is_default=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_public_dashboards(tenant_id=None):
        """Get public dashboards"""
        query = DashboardConfig.query.filter_by(is_public=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(DashboardConfig.dashboard_type, DashboardConfig.name).all()
    
    @staticmethod
    def get_user_dashboards(user_id, tenant_id=None):
        """Get dashboards created by user"""
        query = DashboardConfig.query.filter_by(created_by=user_id, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(DashboardConfig.dashboard_type, DashboardConfig.name).all()
    
    def to_dict(self):
        """Convert dashboard config to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dashboard_type': self.dashboard_type,
            'layout_type': self.layout_type,
            'columns': self.columns,
            'rows': self.rows,
            'widgets': self.widgets,
            'filters': self.filters,
            'auto_refresh': self.auto_refresh,
            'refresh_interval': self.refresh_interval,
            'is_default': self.is_default,
            'is_public': self.is_public,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'updated_by': self.updated_by,
            'updater_name': self.updater.username if self.updater else None
        }
    
    def __repr__(self):
        return f'<DashboardConfig {self.name}>'