"""
Reporting & Analytics models for creating retail-specific reports,
implementing profit/loss analysis, adding customer and staff performance reports,
creating ABC analysis and hourly sales tracking.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, \
    ForeignKey, Numeric, JSON, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

from models import db, FeatureAwareModel


class ReportType(Enum):
    """Report type enumeration"""
    SALES_SUMMARY = "sales_summary"
    PROFIT_LOSS = "profit_loss"
    CUSTOMER_ANALYTICS = "customer_analytics"
    STAFF_PERFORMANCE = "staff_performance"
    INVENTORY_ANALYSIS = "inventory_analysis"
    ABC_ANALYSIS = "abc_analysis"
    HOURLY_SALES = "hourly_sales"
    PRODUCT_PERFORMANCE = "product_performance"
    CATEGORY_PERFORMANCE = "category_performance"
    PAYMENT_ANALYSIS = "payment_analysis"
    DISCOUNT_ANALYSIS = "discount_analysis"
    RETURN_ANALYSIS = "return_analysis"
    TAX_REPORT = "tax_report"
    COMMISSION_REPORT = "commission_report"


class ReportFrequency(Enum):
    """Report frequency enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


class ReportStatus(Enum):
    """Report status enumeration"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class ReportTemplate(FeatureAwareModel):
    """Report template model for defining report structures"""
    __tablename__ = 'report_templates'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Template details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    category = Column(String(50))  # e.g., "financial", "operational", "marketing"
    
    # Template configuration
    template_config = Column(JSON)  # Report structure and fields
    filters = Column(JSON)  # Default filters for the report
    group_by = Column(JSON)  # Grouping options
    calculations = Column(JSON)  # Calculation formulas
    chart_config = Column(JSON)  # Chart configuration
    
    # Scheduling
    auto_generate = Column(Boolean, default=False)
    frequency = Column(SQLEnum(ReportFrequency))
    schedule_config = Column(JSON)  # Schedule configuration
    recipients = Column(JSON)  # Email recipients
    
    # Access control
    roles_allowed = Column(JSON)  # Roles that can access this report
    users_allowed = Column(JSON)  # Specific users that can access this report
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)  # Available to all users
    is_system = Column(Boolean, default=False, nullable=False)  # System template
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    report_instances = relationship("ReportInstance", backref="template")
    
    def __repr__(self):
        return f'<ReportTemplate {self.name}>'


class ReportInstance(FeatureAwareModel):
    """Report instance model for generated reports"""
    __tablename__ = 'report_instances'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Instance details
    template_id = Column(Integer, ForeignKey('report_templates.id'))
    report_name = Column(String(100), nullable=False)
    report_type = Column(SQLEnum(ReportType), nullable=False)
    
    # Generation details
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(Integer, ForeignKey('users.id'))
    generation_time = Column(Integer)  # Generation time in seconds
    
    # Report parameters
    parameters = Column(JSON)  # Parameters used for generation
    filters = Column(JSON)  # Filters applied
    
    # Report data
    data = Column(JSON)  # Report data
    summary = Column(JSON)  # Report summary
    insights = Column(JSON)  # AI-generated insights
    
    # File information
    file_path = Column(String(500))
    file_format = Column(String(20))  # e.g., "pdf", "excel", "csv"
    file_size = Column(Integer)  # File size in bytes
    
    # Status
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    error_message = Column(Text)
    
    # Sharing
    is_shared = Column(Boolean, default=False)
    shared_with = Column(JSON)  # Users/groups shared with
    share_token = Column(String(100))  # Public share token
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    generator = relationship("User", backref="generated_reports")
    
    def __repr__(self):
        return f'<ReportInstance {self.report_name}>'


class SalesAnalytics(FeatureAwareModel):
    """Sales analytics model for tracking sales performance"""
    __tablename__ = 'sales_analytics'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer)  # Hour of the day (0-23)
    day_of_week = Column(Integer)  # Day of week (0-6)
    week_of_year = Column(Integer)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    
    # Sales metrics
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_cost = Column(Numeric(15, 2), default=Decimal('0.00'))
    gross_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Order metrics
    average_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    items_per_order = Column(Numeric(5, 2), default=Decimal('0.00'))
    discount_total = Column(Numeric(15, 2), default=Decimal('0.00'))
    tax_total = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Customer metrics
    unique_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    customer_retention_rate = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Product metrics
    unique_products_sold = Column(Integer, default=0)
    top_selling_product_id = Column(Integer, ForeignKey('products.id'))
    top_selling_category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Channel metrics
    online_orders = Column(Integer, default=0)
    offline_orders = Column(Integer, default=0)
    phone_orders = Column(Integer, default=0)
    
    # Payment metrics
    cash_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    card_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    digital_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Additional data
    metadata = Column(JSON)
    
    # Relationships
    top_selling_product = relationship("Product", foreign_keys=[top_selling_product_id])
    top_selling_category = relationship("Category", foreign_keys=[top_selling_category_id])
    
    def __repr__(self):
        return f'<SalesAnalytics {self.date}>'


class CustomerAnalytics(FeatureAwareModel):
    """Customer analytics model for tracking customer behavior"""
    __tablename__ = 'customer_analytics'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    
    # Customer metrics
    total_customers = Column(Integer, default=0)
    active_customers = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    churned_customers = Column(Integer, default=0)
    
    # Customer value
    average_customer_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    customer_lifetime_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    average_order_frequency = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Segmentation
    customer_segments = Column(JSON)  # Customer segment distribution
    demographic_data = Column(JSON)  # Demographic breakdown
    
    # Loyalty metrics
    loyalty_members = Column(Integer, default=0)
    loyalty_redemption_rate = Column(Numeric(5, 2), default=Decimal('0.00'))
    points_issued = Column(Integer, default=0)
    points_redeemed = Column(Integer, default=0)
    
    # Engagement metrics
    website_visits = Column(Integer, default=0)
    app_sessions = Column(Integer, default=0)
    email_open_rate = Column(Numeric(5, 2), default=Decimal('0.00'))
    social_media_engagement = Column(JSON)
    
    # Geographic distribution
    geographic_distribution = Column(JSON)  # Customer distribution by location
    
    # Additional data
    metadata = Column(JSON)
    
    def __repr__(self):
        return f'<CustomerAnalytics {self.date}>'


class StaffPerformance(FeatureAwareModel):
    """Staff performance model for tracking employee metrics"""
    __tablename__ = 'staff_performance'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    month = Column(Integer)
    quarter = Column(Integer)
    year = Column(Integer)
    
    # Staff details
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    staff_name = Column(String(100), nullable=False)
    staff_role = Column(String(50))
    department = Column(String(50))
    
    # Sales metrics
    total_sales = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_orders = Column(Integer, default=0)
    average_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    sales_target = Column(Numeric(15, 2))
    target_achievement_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Performance metrics
    items_per_hour = Column(Numeric(5, 2), default=Decimal('0.00'))
    conversion_rate = Column(Numeric(5, 2), default=Decimal('0.00'))
    upsell_value = Column(Numeric(15, 2), default=Decimal('0.00'))
    cross_sell_value = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Customer service metrics
    customer_satisfaction_score = Column(Numeric(5, 2), default=Decimal('0.00'))
    returns_handled = Column(Integer, default=0)
    complaints_resolved = Column(Integer, default=0)
    average_response_time = Column(Integer)  # In minutes
    
    # Attendance metrics
    hours_worked = Column(Numeric(5, 2), default=Decimal('0.00'))
    overtime_hours = Column(Numeric(5, 2), default=Decimal('0.00'))
    punctuality_rate = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Commission and bonuses
    commission_earned = Column(Numeric(15, 2), default=Decimal('0.00'))
    bonus_earned = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Additional data
    metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", backref="performance_records")
    
    def __repr__(self):
        return f'<StaffPerformance {self.staff_name} {self.date}>'


class ABCAnalysis(FeatureAwareModel):
    """ABC analysis model for product categorization by importance"""
    __tablename__ = 'abc_analysis'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Analysis period
    analysis_date = Column(Date, nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Product details
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    product_name = Column(String(200), nullable=False)
    product_sku = Column(String(100))
    category_id = Column(Integer, ForeignKey('categories.id'))
    category_name = Column(String(100))
    
    # Sales data
    total_quantity_sold = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_orders = Column(Integer, default=0)
    
    # ABC classification
    abc_class = Column(String(1))  # A, B, or C
    class_rank = Column(Integer)  # Rank within class
    contribution_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    cumulative_percentage = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Analysis criteria
    revenue_contribution = Column(Numeric(15, 2), default=Decimal('0.00'))
    quantity_contribution = Column(Numeric(15, 2), default=Decimal('0.00'))
    frequency_contribution = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Additional metrics
    average_order_quantity = Column(Numeric(5, 2), default=Decimal('0.00'))
    profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    inventory_turnover = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Additional data
    metadata = Column(JSON)
    
    # Relationships
    product = relationship("Product", backref="abc_analysis")
    category = relationship("Category", backref="abc_analysis")
    
    def __repr__(self):
        return f'<ABCAnalysis {self.product_name} {self.abc_class}>'


class HourlySales(FeatureAwareModel):
    """Hourly sales model for tracking sales by hour"""
    __tablename__ = 'hourly_sales'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Time period
    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=False)  # Hour of the day (0-23)
    day_of_week = Column(Integer)  # Day of week (0-6)
    
    # Sales metrics
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_customers = Column(Integer, default=0)
    average_order_value = Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Product metrics
    unique_products_sold = Column(Integer, default=0)
    top_product_id = Column(Integer, ForeignKey('products.id'))
    top_category_id = Column(Integer, ForeignKey('categories.id'))
    
    # Payment metrics
    cash_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    card_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    digital_payments = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Staff metrics
    staff_on_duty = Column(Integer)  # Number of staff on duty
    peak_hour_indicator = Column(Boolean, default=False)  # Is this a peak hour
    
    # Weather and external factors
    weather_condition = Column(String(50))
    temperature = Column(Numeric(5, 2))
    special_events = Column(JSON)  # Special events affecting sales
    
    # Additional data
    metadata = Column(JSON)
    
    # Relationships
    top_product = relationship("Product", foreign_keys=[top_product_id])
    top_category = relationship("Category", foreign_keys=[top_category_id])
    
    def __repr__(self):
        return f'<HourlySales {self.date} {self.hour}:00>'


class ProfitLossAnalysis(FeatureAwareModel):
    """Profit and loss analysis model"""
    __tablename__ = 'profit_loss_analysis'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Analysis period
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    period_type = Column(String(20))  # e.g., "daily", "weekly", "monthly"
    
    # Revenue
    gross_sales = Column(Numeric(15, 2), default=Decimal('0.00'))
    sales_returns = Column(Numeric(15, 2), default=Decimal('0.00'))
    discounts_given = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_sales = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Cost of goods sold
    beginning_inventory = Column(Numeric(15, 2), default=Decimal('0.00'))
    purchases = Column(Numeric(15, 2), default=Decimal('0.00'))
    ending_inventory = Column(Numeric(15, 2), default=Decimal('0.00'))
    cost_of_goods_sold = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Gross profit
    gross_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    gross_profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Operating expenses
    rent_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    salaries_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    utilities_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    marketing_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    other_expenses = Column(Numeric(15, 2), default=Decimal('0.00'))
    total_expenses = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Operating profit
    operating_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    operating_profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Other income/expenses
    interest_income = Column(Numeric(15, 2), default=Decimal('0.00'))
    interest_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    other_income = Column(Numeric(15, 2), default=Decimal('0.00'))
    other_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    
    # Net profit
    net_profit_before_tax = Column(Numeric(15, 2), default=Decimal('0.00'))
    tax_expense = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_profit = Column(Numeric(15, 2), default=Decimal('0.00'))
    net_profit_margin = Column(Numeric(5, 2), default=Decimal('0.00'))
    
    # Breakdown by category
    revenue_by_category = Column(JSON)
    expenses_by_category = Column(JSON)
    
    # Additional data
    metadata = Column(JSON)
    
    def __repr__(self):
        return f'<ProfitLossAnalysis {self.period_start} to {self.period_end}>'


class DashboardWidget(FeatureAwareModel):
    """Dashboard widget model for custom dashboard components"""
    __tablename__ = 'dashboard_widgets'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Widget details
    name = Column(String(100), nullable=False)
    widget_type = Column(String(50), nullable=False)  # e.g., "chart", "metric", "table"
    title = Column(String(200))
    description = Column(Text)
    
    # Configuration
    data_source = Column(String(100))  # Data source for the widget
    query_config = Column(JSON)  # Query configuration
    display_config = Column(JSON)  # Display configuration
    refresh_interval = Column(Integer)  # Refresh interval in seconds
    
    # Position and size
    dashboard_id = Column(String(50))  # Dashboard identifier
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    width = Column(Integer, default=4)  # Grid width
    height = Column(Integer, default=3)  # Grid height
    
    # Access control
    roles_allowed = Column(JSON)  # Roles that can see this widget
    users_allowed = Column(JSON)  # Specific users that can see this widget
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f'<DashboardWidget {self.name}>'


class AnalyticsCache(FeatureAwareModel):
    """Analytics cache model for storing pre-calculated analytics"""
    __tablename__ = 'analytics_cache'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(50), nullable=False, index=True)
    
    # Cache key
    cache_key = Column(String(200), nullable=False, index=True)
    cache_type = Column(String(50))  # e.g., "sales", "customers", "products"
    
    # Cache data
    cache_data = Column(JSON)
    cache_summary = Column(JSON)
    
    # Cache metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f'<AnalyticsCache {self.cache_key}>'
    
    @hybrid_property
    def is_expired(self):
        """Check if cache is expired"""
        return datetime.utcnow() > self.expires_at