"""
Reporting & Analytics service layer for creating retail-specific reports,
implementing profit/loss analysis, adding customer and staff performance reports,
creating ABC analysis and hourly sales tracking.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload

from models import db
from models.reporting_analytics import (
    ReportTemplate, ReportInstance, SalesAnalytics, CustomerAnalytics, StaffPerformance,
    ABCAnalysis, HourlySales, ProfitLossAnalysis, DashboardWidget, AnalyticsCache,
    ReportType, ReportFrequency, ReportStatus
)
from utils.tenant_query_manager import tenant_scoped, get_tenant_id


class ReportingAnalyticsService:
    """Service class for reporting and analytics operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    # Report Template Management
    
    def get_report_templates(self, filters: Optional[Dict] = None) -> List[ReportTemplate]:
        """Get report templates with optional filters"""
        query = ReportTemplate.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(ReportTemplate.is_active == filters['is_active'])
            if 'is_public' in filters:
                query = query.filter(ReportTemplate.is_public == filters['is_public'])
            if 'is_system' in filters:
                query = query.filter(ReportTemplate.is_system == filters['is_system'])
            if 'report_type' in filters:
                query = query.filter(ReportTemplate.report_type == filters['report_type'])
            if 'category' in filters:
                query = query.filter(ReportTemplate.category == filters['category'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ReportTemplate.name.ilike(search_term),
                    ReportTemplate.description.ilike(search_term)
                ))
        
        return query.order_by(ReportTemplate.is_system.desc(), ReportTemplate.name).all()
    
    def get_report_template_by_id(self, template_id: int) -> Optional[ReportTemplate]:
        """Get report template by ID"""
        return ReportTemplate.query.filter_by(id=template_id, tenant_id=self.tenant_id).first()
    
    def create_report_template(self, data: Dict) -> Tuple[bool, Optional[ReportTemplate], str]:
        """Create a new report template"""
        try:
            template = ReportTemplate(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                report_type=data['report_type'],
                category=data.get('category'),
                template_config=data.get('template_config'),
                filters=data.get('filters'),
                group_by=data.get('group_by'),
                calculations=data.get('calculations'),
                chart_config=data.get('chart_config'),
                auto_generate=data.get('auto_generate', False),
                frequency=data.get('frequency'),
                schedule_config=data.get('schedule_config'),
                recipients=data.get('recipients'),
                roles_allowed=data.get('roles_allowed'),
                users_allowed=data.get('users_allowed'),
                is_active=data.get('is_active', True),
                is_public=data.get('is_public', False),
                is_system=data.get('is_system', False),
                created_by=data.get('created_by')
            )
            
            db.session.add(template)
            db.session.commit()
            return True, template, "Report template created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating report template: {str(e)}"
    
    # Report Instance Management
    
    def get_report_instances(self, filters: Optional[Dict] = None) -> List[ReportInstance]:
        """Get report instances with optional filters"""
        query = ReportInstance.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'template_id' in filters:
                query = query.filter(ReportInstance.template_id == filters['template_id'])
            if 'report_type' in filters:
                query = query.filter(ReportInstance.report_type == filters['report_type'])
            if 'status' in filters:
                query = query.filter(ReportInstance.status == filters['status'])
            if 'date_from' in filters:
                query = query.filter(ReportInstance.generated_at >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(ReportInstance.generated_at <= filters['date_to'])
            if 'generated_by' in filters:
                query = query.filter(ReportInstance.generated_by == filters['generated_by'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ReportInstance.report_name.ilike(search_term)
                ))
        
        return query.order_by(desc(ReportInstance.generated_at)).all()
    
    def get_report_instance_by_id(self, instance_id: int) -> Optional[ReportInstance]:
        """Get report instance by ID"""
        return ReportInstance.query.options(
            joinedload(ReportInstance.generator)
        ).filter_by(id=instance_id, tenant_id=self.tenant_id).first()
    
    def generate_report(self, template_id: int, parameters: Dict, user_id: int) -> Tuple[bool, Optional[ReportInstance], str]:
        """Generate a report from template"""
        try:
            template = self.get_report_template_by_id(template_id)
            if not template:
                return False, None, "Report template not found"
            
            # Create report instance
            instance = ReportInstance(
                tenant_id=self.tenant_id,
                template_id=template_id,
                report_name=f"{template.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                report_type=template.report_type,
                parameters=parameters,
                filters=parameters.get('filters', template.filters),
                status=ReportStatus.GENERATING,
                generated_by=user_id
            )
            
            db.session.add(instance)
            db.session.flush()  # Get the ID
            
            # Generate report data based on type
            start_time = datetime.now()
            
            if template.report_type == ReportType.SALES_SUMMARY:
                data = self._generate_sales_summary(parameters)
            elif template.report_type == ReportType.PROFIT_LOSS:
                data = self._generate_profit_loss(parameters)
            elif template.report_type == ReportType.CUSTOMER_ANALYTICS:
                data = self._generate_customer_analytics(parameters)
            elif template.report_type == ReportType.STAFF_PERFORMANCE:
                data = self._generate_staff_performance(parameters)
            elif template.report_type == ReportType.ABC_ANALYSIS:
                data = self._generate_abc_analysis(parameters)
            elif template.report_type == ReportType.HOURLY_SALES:
                data = self._generate_hourly_sales(parameters)
            else:
                data = {'error': 'Unsupported report type'}
            
            end_time = datetime.now()
            generation_time = int((end_time - start_time).total_seconds())
            
            # Update instance with results
            instance.data = data.get('data', {})
            instance.summary = data.get('summary', {})
            instance.insights = data.get('insights', {})
            instance.generation_time = generation_time
            instance.status = ReportStatus.COMPLETED if 'error' not in data else ReportStatus.FAILED
            instance.error_message = data.get('error')
            
            db.session.commit()
            return True, instance, "Report generated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error generating report: {str(e)}"
    
    # Sales Analytics
    
    def get_sales_analytics(self, filters: Optional[Dict] = None) -> List[SalesAnalytics]:
        """Get sales analytics with optional filters"""
        query = SalesAnalytics.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'date_from' in filters:
                query = query.filter(SalesAnalytics.date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(SalesAnalytics.date <= filters['date_to'])
            if 'year' in filters:
                query = query.filter(SalesAnalytics.year == filters['year'])
            if 'month' in filters:
                query = query.filter(SalesAnalytics.month == filters['month'])
            if 'quarter' in filters:
                query = query.filter(SalesAnalytics.quarter == filters['quarter'])
        
        return query.order_by(desc(SalesAnalytics.date)).all()
    
    def create_sales_analytics(self, data: Dict) -> Tuple[bool, Optional[SalesAnalytics], str]:
        """Create sales analytics record"""
        try:
            analytics = SalesAnalytics(
                tenant_id=self.tenant_id,
                date=data['date'],
                hour=data.get('hour'),
                day_of_week=data.get('day_of_week'),
                week_of_year=data.get('week_of_year'),
                month=data.get('month'),
                quarter=data.get('quarter'),
                year=data.get('year'),
                total_orders=data.get('total_orders', 0),
                total_revenue=Decimal(str(data.get('total_revenue', '0'))),
                total_cost=Decimal(str(data.get('total_cost', '0'))),
                gross_profit=Decimal(str(data.get('gross_profit', '0'))),
                net_profit=Decimal(str(data.get('net_profit', '0'))),
                profit_margin=Decimal(str(data.get('profit_margin', '0'))),
                average_order_value=Decimal(str(data.get('average_order_value', '0'))),
                items_per_order=Decimal(str(data.get('items_per_order', '0'))),
                discount_total=Decimal(str(data.get('discount_total', '0'))),
                tax_total=Decimal(str(data.get('tax_total', '0'))),
                unique_customers=data.get('unique_customers', 0),
                returning_customers=data.get('returning_customers', 0),
                new_customers=data.get('new_customers', 0),
                customer_retention_rate=Decimal(str(data.get('customer_retention_rate', '0'))),
                unique_products_sold=data.get('unique_products_sold', 0),
                top_selling_product_id=data.get('top_selling_product_id'),
                top_selling_category_id=data.get('top_selling_category_id'),
                online_orders=data.get('online_orders', 0),
                offline_orders=data.get('offline_orders', 0),
                phone_orders=data.get('phone_orders', 0),
                cash_payments=Decimal(str(data.get('cash_payments', '0'))),
                card_payments=Decimal(str(data.get('card_payments', '0'))),
                digital_payments=Decimal(str(data.get('digital_payments', '0'))),
                metadata=data.get('metadata')
            )
            
            db.session.add(analytics)
            db.session.commit()
            return True, analytics, "Sales analytics created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating sales analytics: {str(e)}"
    
    # Customer Analytics
    
    def get_customer_analytics(self, filters: Optional[Dict] = None) -> List[CustomerAnalytics]:
        """Get customer analytics with optional filters"""
        query = CustomerAnalytics.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'date_from' in filters:
                query = query.filter(CustomerAnalytics.date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(CustomerAnalytics.date <= filters['date_to'])
            if 'year' in filters:
                query = query.filter(CustomerAnalytics.year == filters['year'])
            if 'month' in filters:
                query = query.filter(CustomerAnalytics.month == filters['month'])
            if 'quarter' in filters:
                query = query.filter(CustomerAnalytics.quarter == filters['quarter'])
        
        return query.order_by(desc(CustomerAnalytics.date)).all()
    
    def create_customer_analytics(self, data: Dict) -> Tuple[bool, Optional[CustomerAnalytics], str]:
        """Create customer analytics record"""
        try:
            analytics = CustomerAnalytics(
                tenant_id=self.tenant_id,
                date=data['date'],
                month=data.get('month'),
                quarter=data.get('quarter'),
                year=data.get('year'),
                total_customers=data.get('total_customers', 0),
                active_customers=data.get('active_customers', 0),
                new_customers=data.get('new_customers', 0),
                churned_customers=data.get('churned_customers', 0),
                average_customer_value=Decimal(str(data.get('average_customer_value', '0'))),
                customer_lifetime_value=Decimal(str(data.get('customer_lifetime_value', '0'))),
                average_order_frequency=Decimal(str(data.get('average_order_frequency', '0'))),
                customer_segments=data.get('customer_segments'),
                demographic_data=data.get('demographic_data'),
                loyalty_members=data.get('loyalty_members', 0),
                loyalty_redemption_rate=Decimal(str(data.get('loyalty_redemption_rate', '0'))),
                points_issued=data.get('points_issued', 0),
                points_redeemed=data.get('points_redeemed', 0),
                website_visits=data.get('website_visits', 0),
                app_sessions=data.get('app_sessions', 0),
                email_open_rate=Decimal(str(data.get('email_open_rate', '0'))),
                social_media_engagement=data.get('social_media_engagement'),
                geographic_distribution=data.get('geographic_distribution'),
                metadata=data.get('metadata')
            )
            
            db.session.add(analytics)
            db.session.commit()
            return True, analytics, "Customer analytics created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating customer analytics: {str(e)}"
    
    # Staff Performance
    
    def get_staff_performance(self, filters: Optional[Dict] = None) -> List[StaffPerformance]:
        """Get staff performance with optional filters"""
        query = StaffPerformance.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'date_from' in filters:
                query = query.filter(StaffPerformance.date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(StaffPerformance.date <= filters['date_to'])
            if 'year' in filters:
                query = query.filter(StaffPerformance.year == filters['year'])
            if 'month' in filters:
                query = query.filter(StaffPerformance.month == filters['month'])
            if 'quarter' in filters:
                query = query.filter(StaffPerformance.quarter == filters['quarter'])
            if 'user_id' in filters:
                query = query.filter(StaffPerformance.user_id == filters['user_id'])
            if 'staff_role' in filters:
                query = query.filter(StaffPerformance.staff_role == filters['staff_role'])
            if 'department' in filters:
                query = query.filter(StaffPerformance.department == filters['department'])
        
        return query.order_by(desc(StaffPerformance.date)).all()
    
    def create_staff_performance(self, data: Dict) -> Tuple[bool, Optional[StaffPerformance], str]:
        """Create staff performance record"""
        try:
            performance = StaffPerformance(
                tenant_id=self.tenant_id,
                date=data['date'],
                month=data.get('month'),
                quarter=data.get('quarter'),
                year=data.get('year'),
                user_id=data['user_id'],
                staff_name=data['staff_name'],
                staff_role=data.get('staff_role'),
                department=data.get('department'),
                total_sales=Decimal(str(data.get('total_sales', '0'))),
                total_orders=data.get('total_orders', 0),
                average_order_value=Decimal(str(data.get('average_order_value', '0'))),
                sales_target=Decimal(str(data.get('sales_target'))) if data.get('sales_target') else None,
                target_achievement_percentage=Decimal(str(data.get('target_achievement_percentage', '0'))),
                items_per_hour=Decimal(str(data.get('items_per_hour', '0'))),
                conversion_rate=Decimal(str(data.get('conversion_rate', '0'))),
                upsell_value=Decimal(str(data.get('upsell_value', '0'))),
                cross_sell_value=Decimal(str(data.get('cross_sell_value', '0'))),
                customer_satisfaction_score=Decimal(str(data.get('customer_satisfaction_score', '0'))),
                returns_handled=data.get('returns_handled', 0),
                complaints_resolved=data.get('complaints_resolved', 0),
                average_response_time=data.get('average_response_time'),
                hours_worked=Decimal(str(data.get('hours_worked', '0'))),
                overtime_hours=Decimal(str(data.get('overtime_hours', '0'))),
                punctuality_rate=Decimal(str(data.get('punctuality_rate', '0'))),
                commission_earned=Decimal(str(data.get('commission_earned', '0'))),
                bonus_earned=Decimal(str(data.get('bonus_earned', '0'))),
                metadata=data.get('metadata')
            )
            
            db.session.add(performance)
            db.session.commit()
            return True, performance, "Staff performance created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating staff performance: {str(e)}"
    
    # ABC Analysis
    
    def get_abc_analysis(self, filters: Optional[Dict] = None) -> List[ABCAnalysis]:
        """Get ABC analysis with optional filters"""
        query = ABCAnalysis.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'analysis_date' in filters:
                query = query.filter(ABCAnalysis.analysis_date == filters['analysis_date'])
            if 'date_from' in filters:
                query = query.filter(ABCAnalysis.analysis_date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(ABCAnalysis.analysis_date <= filters['date_to'])
            if 'abc_class' in filters:
                query = query.filter(ABCAnalysis.abc_class == filters['abc_class'])
            if 'category_id' in filters:
                query = query.filter(ABCAnalysis.category_id == filters['category_id'])
        
        return query.order_by(ABCAnalysis.class_rank).all()
    
    def create_abc_analysis(self, data: Dict) -> Tuple[bool, Optional[ABCAnalysis], str]:
        """Create ABC analysis record"""
        try:
            analysis = ABCAnalysis(
                tenant_id=self.tenant_id,
                analysis_date=data['analysis_date'],
                start_date=data['start_date'],
                end_date=data['end_date'],
                product_id=data['product_id'],
                product_name=data['product_name'],
                product_sku=data.get('product_sku'),
                category_id=data.get('category_id'),
                category_name=data.get('category_name'),
                total_quantity_sold=data.get('total_quantity_sold', 0),
                total_revenue=Decimal(str(data.get('total_revenue', '0'))),
                total_orders=data.get('total_orders', 0),
                abc_class=data['abc_class'],
                class_rank=data.get('class_rank'),
                contribution_percentage=Decimal(str(data.get('contribution_percentage', '0'))),
                cumulative_percentage=Decimal(str(data.get('cumulative_percentage', '0'))),
                revenue_contribution=Decimal(str(data.get('revenue_contribution', '0'))),
                quantity_contribution=Decimal(str(data.get('quantity_contribution', '0'))),
                frequency_contribution=Decimal(str(data.get('frequency_contribution', '0'))),
                average_order_quantity=Decimal(str(data.get('average_order_quantity', '0'))),
                profit_margin=Decimal(str(data.get('profit_margin', '0'))),
                inventory_turnover=Decimal(str(data.get('inventory_turnover', '0'))),
                metadata=data.get('metadata')
            )
            
            db.session.add(analysis)
            db.session.commit()
            return True, analysis, "ABC analysis created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating ABC analysis: {str(e)}"
    
    # Hourly Sales
    
    def get_hourly_sales(self, filters: Optional[Dict] = None) -> List[HourlySales]:
        """Get hourly sales with optional filters"""
        query = HourlySales.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'date_from' in filters:
                query = query.filter(HourlySales.date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(HourlySales.date <= filters['date_to'])
            if 'hour' in filters:
                query = query.filter(HourlySales.hour == filters['hour'])
            if 'day_of_week' in filters:
                query = query.filter(HourlySales.day_of_week == filters['day_of_week'])
        
        return query.order_by(desc(HourlySales.date), desc(HourlySales.hour)).all()
    
    def create_hourly_sales(self, data: Dict) -> Tuple[bool, Optional[HourlySales], str]:
        """Create hourly sales record"""
        try:
            hourly_sales = HourlySales(
                tenant_id=self.tenant_id,
                date=data['date'],
                hour=data['hour'],
                day_of_week=data.get('day_of_week'),
                total_orders=data.get('total_orders', 0),
                total_revenue=Decimal(str(data.get('total_revenue', '0'))),
                total_customers=data.get('total_customers', 0),
                average_order_value=Decimal(str(data.get('average_order_value', '0'))),
                unique_products_sold=data.get('unique_products_sold', 0),
                top_product_id=data.get('top_product_id'),
                top_category_id=data.get('top_category_id'),
                cash_payments=Decimal(str(data.get('cash_payments', '0'))),
                card_payments=Decimal(str(data.get('card_payments', '0'))),
                digital_payments=Decimal(str(data.get('digital_payments', '0'))),
                staff_on_duty=data.get('staff_on_duty'),
                peak_hour_indicator=data.get('peak_hour_indicator', False),
                weather_condition=data.get('weather_condition'),
                temperature=Decimal(str(data.get('temperature'))) if data.get('temperature') else None,
                special_events=data.get('special_events'),
                metadata=data.get('metadata')
            )
            
            db.session.add(hourly_sales)
            db.session.commit()
            return True, hourly_sales, "Hourly sales created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating hourly sales: {str(e)}"
    
    # Profit/Loss Analysis
    
    def get_profit_loss_analysis(self, filters: Optional[Dict] = None) -> List[ProfitLossAnalysis]:
        """Get profit/loss analysis with optional filters"""
        query = ProfitLossAnalysis.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'period_start' in filters:
                query = query.filter(ProfitLossAnalysis.period_start >= filters['period_start'])
            if 'period_end' in filters:
                query = query.filter(ProfitLossAnalysis.period_end <= filters['period_end'])
            if 'period_type' in filters:
                query = query.filter(ProfitLossAnalysis.period_type == filters['period_type'])
            if 'year' in filters:
                query = query.filter(ProfitLossAnalysis.period_start.between(
                    date(filters['year'], 1, 1),
                    date(filters['year'], 12, 31)
                ))
        
        return query.order_by(desc(ProfitLossAnalysis.period_start)).all()
    
    def create_profit_loss_analysis(self, data: Dict) -> Tuple[bool, Optional[ProfitLossAnalysis], str]:
        """Create profit/loss analysis record"""
        try:
            analysis = ProfitLossAnalysis(
                tenant_id=self.tenant_id,
                period_start=data['period_start'],
                period_end=data['period_end'],
                period_type=data.get('period_type'),
                gross_sales=Decimal(str(data.get('gross_sales', '0'))),
                sales_returns=Decimal(str(data.get('sales_returns', '0'))),
                discounts_given=Decimal(str(data.get('discounts_given', '0'))),
                net_sales=Decimal(str(data.get('net_sales', '0'))),
                beginning_inventory=Decimal(str(data.get('beginning_inventory', '0'))),
                purchases=Decimal(str(data.get('purchases', '0'))),
                ending_inventory=Decimal(str(data.get('ending_inventory', '0'))),
                cost_of_goods_sold=Decimal(str(data.get('cost_of_goods_sold', '0'))),
                gross_profit=Decimal(str(data.get('gross_profit', '0'))),
                gross_profit_margin=Decimal(str(data.get('gross_profit_margin', '0'))),
                rent_expense=Decimal(str(data.get('rent_expense', '0'))),
                salaries_expense=Decimal(str(data.get('salaries_expense', '0'))),
                utilities_expense=Decimal(str(data.get('utilities_expense', '0'))),
                marketing_expense=Decimal(str(data.get('marketing_expense', '0'))),
                other_expenses=Decimal(str(data.get('other_expenses', '0'))),
                total_expenses=Decimal(str(data.get('total_expenses', '0'))),
                operating_profit=Decimal(str(data.get('operating_profit', '0'))),
                operating_profit_margin=Decimal(str(data.get('operating_profit_margin', '0'))),
                interest_income=Decimal(str(data.get('interest_income', '0'))),
                interest_expense=Decimal(str(data.get('interest_expense', '0'))),
                other_income=Decimal(str(data.get('other_income', '0'))),
                other_expense=Decimal(str(data.get('other_expense', '0'))),
                net_profit_before_tax=Decimal(str(data.get('net_profit_before_tax', '0'))),
                tax_expense=Decimal(str(data.get('tax_expense', '0'))),
                net_profit=Decimal(str(data.get('net_profit', '0'))),
                net_profit_margin=Decimal(str(data.get('net_profit_margin', '0'))),
                revenue_by_category=data.get('revenue_by_category'),
                expenses_by_category=data.get('expenses_by_category'),
                metadata=data.get('metadata')
            )
            
            db.session.add(analysis)
            db.session.commit()
            return True, analysis, "Profit/loss analysis created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating profit/loss analysis: {str(e)}"
    
    # Dashboard Widgets
    
    def get_dashboard_widgets(self, filters: Optional[Dict] = None) -> List[DashboardWidget]:
        """Get dashboard widgets with optional filters"""
        query = DashboardWidget.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'dashboard_id' in filters:
                query = query.filter(DashboardWidget.dashboard_id == filters['dashboard_id'])
            if 'widget_type' in filters:
                query = query.filter(DashboardWidget.widget_type == filters['widget_type'])
            if 'is_active' in filters:
                query = query.filter(DashboardWidget.is_active == filters['is_active'])
            if 'is_default' in filters:
                query = query.filter(DashboardWidget.is_default == filters['is_default'])
        
        return query.order_by(DashboardWidget.position_y, DashboardWidget.position_x).all()
    
    def create_dashboard_widget(self, data: Dict) -> Tuple[bool, Optional[DashboardWidget], str]:
        """Create a dashboard widget"""
        try:
            widget = DashboardWidget(
                tenant_id=self.tenant_id,
                name=data['name'],
                widget_type=data['widget_type'],
                title=data.get('title'),
                description=data.get('description'),
                data_source=data.get('data_source'),
                query_config=data.get('query_config'),
                display_config=data.get('display_config'),
                refresh_interval=data.get('refresh_interval'),
                dashboard_id=data.get('dashboard_id', 'default'),
                position_x=data.get('position_x', 0),
                position_y=data.get('position_y', 0),
                width=data.get('width', 4),
                height=data.get('height', 3),
                roles_allowed=data.get('roles_allowed'),
                users_allowed=data.get('users_allowed'),
                is_active=data.get('is_active', True),
                is_default=data.get('is_default', False),
                created_by=data.get('created_by')
            )
            
            db.session.add(widget)
            db.session.commit()
            return True, widget, "Dashboard widget created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating dashboard widget: {str(e)}"
    
    # Analytics Cache
    
    def get_analytics_cache(self, cache_key: str) -> Optional[AnalyticsCache]:
        """Get analytics cache by key"""
        cache = AnalyticsCache.query.filter_by(
            cache_key=cache_key, 
            tenant_id=self.tenant_id
        ).first()
        
        if cache and not cache.is_expired:
            # Update hit count
            cache.hit_count += 1
            db.session.commit()
            return cache
        
        return None
    
    def set_analytics_cache(self, cache_key: str, cache_type: str, data: Dict, 
                        expires_in_minutes: int = 60) -> Tuple[bool, str]:
        """Set analytics cache"""
        try:
            # Check if cache already exists
            existing_cache = self.get_analytics_cache(cache_key)
            
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
            
            if existing_cache:
                existing_cache.cache_data = data
                existing_cache.cache_type = cache_type
                existing_cache.expires_at = expires_at
                existing_cache.created_at = datetime.utcnow()
            else:
                cache = AnalyticsCache(
                    tenant_id=self.tenant_id,
                    cache_key=cache_key,
                    cache_type=cache_type,
                    cache_data=data,
                    expires_at=expires_at
                )
                db.session.add(cache)
            
            db.session.commit()
            return True, "Cache set successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error setting cache: {str(e)}"
    
    # Report Generation Methods
    
    def _generate_sales_summary(self, parameters: Dict) -> Dict:
        """Generate sales summary report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # Query sales data
            query = db.session.query(
                func.count(Order.id).label('total_orders'),
                func.sum(Order.total_amount).label('total_revenue'),
                func.count(func.distinct(Order.customer_id)).label('unique_customers')
            ).filter(
                Order.tenant_id == self.tenant_id,
                Order.created_at >= date_from,
                Order.created_at <= date_to
            )
            
            result = query.first()
            
            return {
                'data': {
                    'total_orders': result.total_orders or 0,
                    'total_revenue': float(result.total_revenue or 0),
                    'unique_customers': result.unique_customers or 0
                },
                'summary': {
                    'period': f"{date_from} to {date_to}",
                    'average_order_value': float(result.total_revenue or 0) / max(result.total_orders or 1, 1)
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating sales summary: {str(e)}"}
    
    def _generate_profit_loss(self, parameters: Dict) -> Dict:
        """Generate profit/loss report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # This would need to be implemented based on actual data structure
            # For now, return a placeholder
            return {
                'data': {
                    'period': f"{date_from} to {date_to}",
                    'revenue': 0,
                    'expenses': 0,
                    'profit': 0
                },
                'summary': {
                    'profit_margin': 0
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating profit/loss: {str(e)}"}
    
    def _generate_customer_analytics(self, parameters: Dict) -> Dict:
        """Generate customer analytics report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # This would need to be implemented based on actual data structure
            # For now, return a placeholder
            return {
                'data': {
                    'period': f"{date_from} to {date_to}",
                    'total_customers': 0,
                    'new_customers': 0,
                    'returning_customers': 0
                },
                'summary': {
                    'customer_retention_rate': 0
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating customer analytics: {str(e)}"}
    
    def _generate_staff_performance(self, parameters: Dict) -> Dict:
        """Generate staff performance report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # This would need to be implemented based on actual data structure
            # For now, return a placeholder
            return {
                'data': {
                    'period': f"{date_from} to {date_to}",
                    'staff_performance': []
                },
                'summary': {
                    'total_staff': 0,
                    'average_performance': 0
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating staff performance: {str(e)}"}
    
    def _generate_abc_analysis(self, parameters: Dict) -> Dict:
        """Generate ABC analysis report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # This would need to be implemented based on actual data structure
            # For now, return a placeholder
            return {
                'data': {
                    'period': f"{date_from} to {date_to}",
                    'abc_analysis': []
                },
                'summary': {
                    'total_products': 0,
                    'class_distribution': {'A': 0, 'B': 0, 'C': 0}
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating ABC analysis: {str(e)}"}
    
    def _generate_hourly_sales(self, parameters: Dict) -> Dict:
        """Generate hourly sales report"""
        try:
            filters = parameters.get('filters', {})
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            # This would need to be implemented based on actual data structure
            # For now, return a placeholder
            return {
                'data': {
                    'period': f"{date_from} to {date_to}",
                    'hourly_sales': []
                },
                'summary': {
                    'peak_hour': None,
                    'total_sales': 0
                }
            }
            
        except Exception as e:
            return {'error': f"Error generating hourly sales: {str(e)}"}


# Factory function to create service instances
def create_reporting_analytics_service(tenant_id: str) -> ReportingAnalyticsService:
    """Factory function to create a reporting & analytics service instance"""
    return ReportingAnalyticsService(tenant_id)