"""
Reporting & Analytics routes for creating retail-specific reports,
implementing profit/loss analysis, adding customer and staff performance reports,
creating ABC analysis and hourly sales tracking.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, date
from decimal import Decimal
from functools import wraps
from models import db, get_tenant_id
from models.reporting_analytics import (
    ReportTemplate, ReportInstance, SalesAnalytics, CustomerAnalytics, StaffPerformance,
    ABCAnalysis, HourlySales, ProfitLossAnalysis, DashboardWidget, AnalyticsCache,
    ReportType, ReportFrequency, ReportStatus
)
from services.reporting_analytics_service import create_reporting_analytics_service
from utils.feature_decorators import feature_required
from utils.tenant_query_manager import tenant_scoped
from utils.validation import validate_required_fields, validate_email, validate_phone
import logging

# Create blueprint
reporting_analytics_bp = Blueprint('reporting_analytics', __name__, url_prefix='/api/reporting-analytics')

# Configure logging
logger = logging.getLogger(__name__)

# Helper function to create service instance
def get_service():
    """Create service instance with current tenant"""
    tenant_id = get_tenant_id()
    return create_reporting_analytics_service(tenant_id)

# Error handler
def handle_error(error_msg, status_code=400):
    """Handle API errors"""
    logger.error(f"Reporting & Analytics API Error: {error_msg}")
    return jsonify({'error': error_msg}), status_code

# Success response helper
def success_response(data=None, message="Success", status_code=200):
    """Create success response"""
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code

# ==================== Report Template Routes ====================

@reporting_analytics_bp.route('/report-templates', methods=['GET'])
@feature_required('reporting_analytics')
def get_report_templates():
    """Get all report templates with optional filters"""
    try:
        filters = {}
        for param in ['is_active', 'is_public', 'is_system', 'report_type', 'category', 'search']:
            if param in request.args:
                if param in ['is_active', 'is_public', 'is_system']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        templates = service.get_report_templates(filters)
        
        result = []
        for template in templates:
            result.append({
                'id': template.id,
                'name': template.name,
                'description': template.description,
                'report_type': template.report_type.value,
                'category': template.category,
                'template_config': template.template_config,
                'filters': template.filters,
                'group_by': template.group_by,
                'calculations': template.calculations,
                'chart_config': template.chart_config,
                'auto_generate': template.auto_generate,
                'frequency': template.frequency.value if template.frequency else None,
                'schedule_config': template.schedule_config,
                'recipients': template.recipients,
                'roles_allowed': template.roles_allowed,
                'users_allowed': template.users_allowed,
                'is_active': template.is_active,
                'is_public': template.is_public,
                'is_system': template.is_system,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving report templates: {str(e)}")

@reporting_analytics_bp.route('/report-templates/<int:template_id>', methods=['GET'])
@feature_required('reporting_analytics')
def get_report_template(template_id):
    """Get report template by ID"""
    try:
        service = get_service()
        template = service.get_report_template_by_id(template_id)
        
        if not template:
            return handle_error("Report template not found", 404)
        
        result = {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'report_type': template.report_type.value,
            'category': template.category,
            'template_config': template.template_config,
            'filters': template.filters,
            'group_by': template.group_by,
            'calculations': template.calculations,
            'chart_config': template.chart_config,
            'auto_generate': template.auto_generate,
            'frequency': template.frequency.value if template.frequency else None,
            'schedule_config': template.schedule_config,
            'recipients': template.recipients,
            'roles_allowed': template.roles_allowed,
            'users_allowed': template.users_allowed,
            'is_active': template.is_active,
            'is_public': template.is_public,
            'is_system': template.is_system,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving report template: {str(e)}")

@reporting_analytics_bp.route('/report-templates', methods=['POST'])
@feature_required('reporting_analytics')
def create_report_template():
    """Create a new report template"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'report_type']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate report type
        valid_types = [rtype.value for rtype in ReportType]
        if data['report_type'] not in valid_types:
            return handle_error(f"Invalid report type. Must be one of: {', '.join(valid_types)}")
        
        # Validate frequency if provided
        if 'frequency' in data:
            valid_frequencies = [freq.value for freq in ReportFrequency]
            if data['frequency'] not in valid_frequencies:
                return handle_error(f"Invalid frequency. Must be one of: {', '.join(valid_frequencies)}")
        
        # Add tenant ID and user ID to data
        tenant_id = get_tenant_id()
        data['tenant_id'] = tenant_id
        data['created_by'] = request.environ.get('user_id', 1)  # Get from auth context
        
        service = get_service()
        success, template, message = service.create_report_template(data)
        
        if success:
            return success_response({
                'id': template.id,
                'name': template.name,
                'report_type': template.report_type.value
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating report template: {str(e)}")

# ==================== Report Instance Routes ====================

@reporting_analytics_bp.route('/report-instances', methods=['GET'])
@feature_required('reporting_analytics')
def get_report_instances():
    """Get all report instances with optional filters"""
    try:
        filters = {}
        for param in ['template_id', 'report_type', 'status', 'date_from', 'date_to', 'generated_by', 'search']:
            if param in request.args:
                if param in ['template_id', 'generated_by']:
                    filters[param] = int(request.args.get(param))
                elif param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d')
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        instances = service.get_report_instances(filters)
        
        result = []
        for instance in instances:
            result.append({
                'id': instance.id,
                'template_id': instance.template_id,
                'report_name': instance.report_name,
                'report_type': instance.report_type.value,
                'generated_at': instance.generated_at.isoformat() if instance.generated_at else None,
                'generated_by': instance.generated_by,
                'generation_time': instance.generation_time,
                'parameters': instance.parameters,
                'filters': instance.filters,
                'data': instance.data,
                'summary': instance.summary,
                'insights': instance.insights,
                'file_path': instance.file_path,
                'file_format': instance.file_format,
                'file_size': instance.file_size,
                'status': instance.status.value,
                'error_message': instance.error_message,
                'is_shared': instance.is_shared,
                'shared_with': instance.shared_with,
                'share_token': instance.share_token,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'updated_at': instance.updated_at.isoformat() if instance.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving report instances: {str(e)}")

@reporting_analytics_bp.route('/report-instances/<int:instance_id>', methods=['GET'])
@feature_required('reporting_analytics')
def get_report_instance(instance_id):
    """Get report instance by ID"""
    try:
        service = get_service()
        instance = service.get_report_instance_by_id(instance_id)
        
        if not instance:
            return handle_error("Report instance not found", 404)
        
        result = {
            'id': instance.id,
            'template_id': instance.template_id,
            'report_name': instance.report_name,
            'report_type': instance.report_type.value,
            'generated_at': instance.generated_at.isoformat() if instance.generated_at else None,
            'generated_by': instance.generated_by,
            'generation_time': instance.generation_time,
            'parameters': instance.parameters,
            'filters': instance.filters,
            'data': instance.data,
            'summary': instance.summary,
            'insights': instance.insights,
            'file_path': instance.file_path,
            'file_format': instance.file_format,
            'file_size': instance.file_size,
            'status': instance.status.value,
            'error_message': instance.error_message,
            'is_shared': instance.is_shared,
            'shared_with': instance.shared_with,
            'share_token': instance.share_token,
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving report instance: {str(e)}")

@reporting_analytics_bp.route('/reports/generate', methods=['POST'])
@feature_required('reporting_analytics')
def generate_report():
    """Generate a report from template"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['template_id', 'parameters']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Get user ID from auth context
        user_id = request.environ.get('user_id', 1)
        
        service = get_service()
        success, instance, message = service.generate_report(data['template_id'], data['parameters'], user_id)
        
        if success:
            return success_response({
                'id': instance.id,
                'report_name': instance.report_name,
                'status': instance.status.value,
                'generation_time': instance.generation_time
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error generating report: {str(e)}")

# ==================== Sales Analytics Routes ====================

@reporting_analytics_bp.route('/sales-analytics', methods=['GET'])
@feature_required('reporting_analytics')
def get_sales_analytics():
    """Get sales analytics with optional filters"""
    try:
        filters = {}
        for param in ['date_from', 'date_to', 'year', 'month', 'quarter']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                else:
                    filters[param] = int(request.args.get(param))
        
        service = get_service()
        analytics = service.get_sales_analytics(filters)
        
        result = []
        for analytic in analytics:
            result.append({
                'id': analytic.id,
                'date': analytic.date.isoformat() if analytic.date else None,
                'hour': analytic.hour,
                'day_of_week': analytic.day_of_week,
                'week_of_year': analytic.week_of_year,
                'month': analytic.month,
                'quarter': analytic.quarter,
                'year': analytic.year,
                'total_orders': analytic.total_orders,
                'total_revenue': float(analytic.total_revenue) if analytic.total_revenue else None,
                'total_cost': float(analytic.total_cost) if analytic.total_cost else None,
                'gross_profit': float(analytic.gross_profit) if analytic.gross_profit else None,
                'net_profit': float(analytic.net_profit) if analytic.net_profit else None,
                'profit_margin': float(analytic.profit_margin) if analytic.profit_margin else None,
                'average_order_value': float(analytic.average_order_value) if analytic.average_order_value else None,
                'items_per_order': float(analytic.items_per_order) if analytic.items_per_order else None,
                'discount_total': float(analytic.discount_total) if analytic.discount_total else None,
                'tax_total': float(analytic.tax_total) if analytic.tax_total else None,
                'unique_customers': analytic.unique_customers,
                'returning_customers': analytic.returning_customers,
                'new_customers': analytic.new_customers,
                'customer_retention_rate': float(analytic.customer_retention_rate) if analytic.customer_retention_rate else None,
                'unique_products_sold': analytic.unique_products_sold,
                'top_selling_product_id': analytic.top_selling_product_id,
                'top_selling_category_id': analytic.top_selling_category_id,
                'online_orders': analytic.online_orders,
                'offline_orders': analytic.offline_orders,
                'phone_orders': analytic.phone_orders,
                'cash_payments': float(analytic.cash_payments) if analytic.cash_payments else None,
                'card_payments': float(analytic.card_payments) if analytic.card_payments else None,
                'digital_payments': float(analytic.digital_payments) if analytic.digital_payments else None,
                'metadata': analytic.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving sales analytics: {str(e)}")

@reporting_analytics_bp.route('/sales-analytics', methods=['POST'])
@feature_required('reporting_analytics')
def create_sales_analytics():
    """Create sales analytics record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['date']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate date
        if 'date' in data:
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid date format. Use YYYY-MM-DD")
        
        service = get_service()
        success, analytics, message = service.create_sales_analytics(data)
        
        if success:
            return success_response({
                'id': analytics.id,
                'date': analytics.date.isoformat() if analytics.date else None
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating sales analytics: {str(e)}")

# ==================== Customer Analytics Routes ====================

@reporting_analytics_bp.route('/customer-analytics', methods=['GET'])
@feature_required('reporting_analytics')
def get_customer_analytics():
    """Get customer analytics with optional filters"""
    try:
        filters = {}
        for param in ['date_from', 'date_to', 'year', 'month', 'quarter']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                else:
                    filters[param] = int(request.args.get(param))
        
        service = get_service()
        analytics = service.get_customer_analytics(filters)
        
        result = []
        for analytic in analytics:
            result.append({
                'id': analytic.id,
                'date': analytic.date.isoformat() if analytic.date else None,
                'month': analytic.month,
                'quarter': analytic.quarter,
                'year': analytic.year,
                'total_customers': analytic.total_customers,
                'active_customers': analytic.active_customers,
                'new_customers': analytic.new_customers,
                'churned_customers': analytic.churned_customers,
                'average_customer_value': float(analytic.average_customer_value) if analytic.average_customer_value else None,
                'customer_lifetime_value': float(analytic.customer_lifetime_value) if analytic.customer_lifetime_value else None,
                'average_order_frequency': float(analytic.average_order_frequency) if analytic.average_order_frequency else None,
                'customer_segments': analytic.customer_segments,
                'demographic_data': analytic.demographic_data,
                'loyalty_members': analytic.loyalty_members,
                'loyalty_redemption_rate': float(analytic.loyalty_redemption_rate) if analytic.loyalty_redemption_rate else None,
                'points_issued': analytic.points_issued,
                'points_redeemed': analytic.points_redeemed,
                'website_visits': analytic.website_visits,
                'app_sessions': analytic.app_sessions,
                'email_open_rate': float(analytic.email_open_rate) if analytic.email_open_rate else None,
                'social_media_engagement': analytic.social_media_engagement,
                'geographic_distribution': analytic.geographic_distribution,
                'metadata': analytic.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving customer analytics: {str(e)}")

@reporting_analytics_bp.route('/customer-analytics', methods=['POST'])
@feature_required('reporting_analytics')
def create_customer_analytics():
    """Create customer analytics record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['date']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate date
        if 'date' in data:
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid date format. Use YYYY-MM-DD")
        
        service = get_service()
        success, analytics, message = service.create_customer_analytics(data)
        
        if success:
            return success_response({
                'id': analytics.id,
                'date': analytics.date.isoformat() if analytics.date else None
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating customer analytics: {str(e)}")

# ==================== Staff Performance Routes ====================

@reporting_analytics_bp.route('/staff-performance', methods=['GET'])
@feature_required('reporting_analytics')
def get_staff_performance():
    """Get staff performance with optional filters"""
    try:
        filters = {}
        for param in ['date_from', 'date_to', 'year', 'month', 'quarter', 'user_id', 'staff_role', 'department']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param in ['user_id', 'year', 'month', 'quarter']:
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        performance = service.get_staff_performance(filters)
        
        result = []
        for perf in performance:
            result.append({
                'id': perf.id,
                'date': perf.date.isoformat() if perf.date else None,
                'month': perf.month,
                'quarter': perf.quarter,
                'year': perf.year,
                'user_id': perf.user_id,
                'staff_name': perf.staff_name,
                'staff_role': perf.staff_role,
                'department': perf.department,
                'total_sales': float(perf.total_sales) if perf.total_sales else None,
                'total_orders': perf.total_orders,
                'average_order_value': float(perf.average_order_value) if perf.average_order_value else None,
                'sales_target': float(perf.sales_target) if perf.sales_target else None,
                'target_achievement_percentage': float(perf.target_achievement_percentage) if perf.target_achievement_percentage else None,
                'items_per_hour': float(perf.items_per_hour) if perf.items_per_hour else None,
                'conversion_rate': float(perf.conversion_rate) if perf.conversion_rate else None,
                'upsell_value': float(perf.upsell_value) if perf.upsell_value else None,
                'cross_sell_value': float(perf.cross_sell_value) if perf.cross_sell_value else None,
                'customer_satisfaction_score': float(perf.customer_satisfaction_score) if perf.customer_satisfaction_score else None,
                'returns_handled': perf.returns_handled,
                'complaints_resolved': perf.complaints_resolved,
                'average_response_time': perf.average_response_time,
                'hours_worked': float(perf.hours_worked) if perf.hours_worked else None,
                'overtime_hours': float(perf.overtime_hours) if perf.overtime_hours else None,
                'punctuality_rate': float(perf.punctuality_rate) if perf.punctuality_rate else None,
                'commission_earned': float(perf.commission_earned) if perf.commission_earned else None,
                'bonus_earned': float(perf.bonus_earned) if perf.bonus_earned else None,
                'metadata': perf.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving staff performance: {str(e)}")

@reporting_analytics_bp.route('/staff-performance', methods=['POST'])
@feature_required('reporting_analytics')
def create_staff_performance():
    """Create staff performance record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['date', 'user_id', 'staff_name']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate date
        if 'date' in data:
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid date format. Use YYYY-MM-DD")
        
        service = get_service()
        success, performance, message = service.create_staff_performance(data)
        
        if success:
            return success_response({
                'id': performance.id,
                'staff_name': performance.staff_name,
                'date': performance.date.isoformat() if performance.date else None
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating staff performance: {str(e)}")

# ==================== ABC Analysis Routes ====================

@reporting_analytics_bp.route('/abc-analysis', methods=['GET'])
@feature_required('reporting_analytics')
def get_abc_analysis():
    """Get ABC analysis with optional filters"""
    try:
        filters = {}
        for param in ['analysis_date', 'date_from', 'date_to', 'abc_class', 'category_id']:
            if param in request.args:
                if param in ['analysis_date', 'date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param in ['category_id']:
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        analysis = service.get_abc_analysis(filters)
        
        result = []
        for item in analysis:
            result.append({
                'id': item.id,
                'analysis_date': item.analysis_date.isoformat() if item.analysis_date else None,
                'start_date': item.start_date.isoformat() if item.start_date else None,
                'end_date': item.end_date.isoformat() if item.end_date else None,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'product_sku': item.product_sku,
                'category_id': item.category_id,
                'category_name': item.category_name,
                'total_quantity_sold': item.total_quantity_sold,
                'total_revenue': float(item.total_revenue) if item.total_revenue else None,
                'total_orders': item.total_orders,
                'abc_class': item.abc_class,
                'class_rank': item.class_rank,
                'contribution_percentage': float(item.contribution_percentage) if item.contribution_percentage else None,
                'cumulative_percentage': float(item.cumulative_percentage) if item.cumulative_percentage else None,
                'revenue_contribution': float(item.revenue_contribution) if item.revenue_contribution else None,
                'quantity_contribution': float(item.quantity_contribution) if item.quantity_contribution else None,
                'frequency_contribution': float(item.frequency_contribution) if item.frequency_contribution else None,
                'average_order_quantity': float(item.average_order_quantity) if item.average_order_quantity else None,
                'profit_margin': float(item.profit_margin) if item.profit_margin else None,
                'inventory_turnover': float(item.inventory_turnover) if item.inventory_turnover else None,
                'metadata': item.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving ABC analysis: {str(e)}")

@reporting_analytics_bp.route('/abc-analysis', methods=['POST'])
@feature_required('reporting_analytics')
def create_abc_analysis():
    """Create ABC analysis record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['analysis_date', 'start_date', 'end_date', 'product_id', 'product_name', 'abc_class']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate dates
        for date_field in ['analysis_date', 'start_date', 'end_date']:
            if date_field in data:
                try:
                    datetime.strptime(data[date_field], '%Y-%m-%d')
                except ValueError:
                    return handle_error(f"Invalid {date_field} format. Use YYYY-MM-DD")
        
        # Validate ABC class
        if data.get('abc_class') not in ['A', 'B', 'C']:
            return handle_error("ABC class must be one of: A, B, C")
        
        service = get_service()
        success, analysis, message = service.create_abc_analysis(data)
        
        if success:
            return success_response({
                'id': analysis.id,
                'product_name': analysis.product_name,
                'abc_class': analysis.abc_class
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating ABC analysis: {str(e)}")

# ==================== Hourly Sales Routes ====================

@reporting_analytics_bp.route('/hourly-sales', methods=['GET'])
@feature_required('reporting_analytics')
def get_hourly_sales():
    """Get hourly sales with optional filters"""
    try:
        filters = {}
        for param in ['date_from', 'date_to', 'hour', 'day_of_week']:
            if param in request.args:
                if param in ['date_from', 'date_to']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param in ['hour', 'day_of_week']:
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        hourly_sales = service.get_hourly_sales(filters)
        
        result = []
        for sales in hourly_sales:
            result.append({
                'id': sales.id,
                'date': sales.date.isoformat() if sales.date else None,
                'hour': sales.hour,
                'day_of_week': sales.day_of_week,
                'total_orders': sales.total_orders,
                'total_revenue': float(sales.total_revenue) if sales.total_revenue else None,
                'total_customers': sales.total_customers,
                'average_order_value': float(sales.average_order_value) if sales.average_order_value else None,
                'unique_products_sold': sales.unique_products_sold,
                'top_product_id': sales.top_product_id,
                'top_category_id': sales.top_category_id,
                'cash_payments': float(sales.cash_payments) if sales.cash_payments else None,
                'card_payments': float(sales.card_payments) if sales.card_payments else None,
                'digital_payments': float(sales.digital_payments) if sales.digital_payments else None,
                'staff_on_duty': sales.staff_on_duty,
                'peak_hour_indicator': sales.peak_hour_indicator,
                'weather_condition': sales.weather_condition,
                'temperature': float(sales.temperature) if sales.temperature else None,
                'special_events': sales.special_events,
                'metadata': sales.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving hourly sales: {str(e)}")

@reporting_analytics_bp.route('/hourly-sales', methods=['POST'])
@feature_required('reporting_analytics')
def create_hourly_sales():
    """Create hourly sales record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['date', 'hour']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate date
        if 'date' in data:
            try:
                datetime.strptime(data['date'], '%Y-%m-%d')
            except ValueError:
                return handle_error("Invalid date format. Use YYYY-MM-DD")
        
        # Validate hour
        if not (0 <= int(data['hour']) <= 23):
            return handle_error("Hour must be between 0 and 23")
        
        service = get_service()
        success, hourly_sales, message = service.create_hourly_sales(data)
        
        if success:
            return success_response({
                'id': hourly_sales.id,
                'date': hourly_sales.date.isoformat() if hourly_sales.date else None,
                'hour': hourly_sales.hour
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating hourly sales: {str(e)}")

# ==================== Profit/Loss Analysis Routes ====================

@reporting_analytics_bp.route('/profit-loss-analysis', methods=['GET'])
@feature_required('reporting_analytics')
def get_profit_loss_analysis():
    """Get profit/loss analysis with optional filters"""
    try:
        filters = {}
        for param in ['period_start', 'period_end', 'period_type', 'year']:
            if param in request.args:
                if param in ['period_start', 'period_end']:
                    filters[param] = datetime.strptime(request.args.get(param), '%Y-%m-%d').date()
                elif param == 'year':
                    filters[param] = int(request.args.get(param))
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        analysis = service.get_profit_loss_analysis(filters)
        
        result = []
        for item in analysis:
            result.append({
                'id': item.id,
                'period_start': item.period_start.isoformat() if item.period_start else None,
                'period_end': item.period_end.isoformat() if item.period_end else None,
                'period_type': item.period_type,
                'gross_sales': float(item.gross_sales) if item.gross_sales else None,
                'sales_returns': float(item.sales_returns) if item.sales_returns else None,
                'discounts_given': float(item.discounts_given) if item.discounts_given else None,
                'net_sales': float(item.net_sales) if item.net_sales else None,
                'beginning_inventory': float(item.beginning_inventory) if item.beginning_inventory else None,
                'purchases': float(item.purchases) if item.purchases else None,
                'ending_inventory': float(item.ending_inventory) if item.ending_inventory else None,
                'cost_of_goods_sold': float(item.cost_of_goods_sold) if item.cost_of_goods_sold else None,
                'gross_profit': float(item.gross_profit) if item.gross_profit else None,
                'gross_profit_margin': float(item.gross_profit_margin) if item.gross_profit_margin else None,
                'rent_expense': float(item.rent_expense) if item.rent_expense else None,
                'salaries_expense': float(item.salaries_expense) if item.salaries_expense else None,
                'utilities_expense': float(item.utilities_expense) if item.utilities_expense else None,
                'marketing_expense': float(item.marketing_expense) if item.marketing_expense else None,
                'other_expenses': float(item.other_expenses) if item.other_expenses else None,
                'total_expenses': float(item.total_expenses) if item.total_expenses else None,
                'operating_profit': float(item.operating_profit) if item.operating_profit else None,
                'operating_profit_margin': float(item.operating_profit_margin) if item.operating_profit_margin else None,
                'interest_income': float(item.interest_income) if item.interest_income else None,
                'interest_expense': float(item.interest_expense) if item.interest_expense else None,
                'other_income': float(item.other_income) if item.other_income else None,
                'other_expense': float(item.other_expense) if item.other_expense else None,
                'net_profit_before_tax': float(item.net_profit_before_tax) if item.net_profit_before_tax else None,
                'tax_expense': float(item.tax_expense) if item.tax_expense else None,
                'net_profit': float(item.net_profit) if item.net_profit else None,
                'net_profit_margin': float(item.net_profit_margin) if item.net_profit_margin else None,
                'revenue_by_category': item.revenue_by_category,
                'expenses_by_category': item.expenses_by_category,
                'metadata': item.metadata
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving profit/loss analysis: {str(e)}")

@reporting_analytics_bp.route('/profit-loss-analysis', methods=['POST'])
@feature_required('reporting_analytics')
def create_profit_loss_analysis():
    """Create profit/loss analysis record"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['period_start', 'period_end', 'period_type']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        # Validate dates
        for date_field in ['period_start', 'period_end']:
            if date_field in data:
                try:
                    datetime.strptime(data[date_field], '%Y-%m-%d')
                except ValueError:
                    return handle_error(f"Invalid {date_field} format. Use YYYY-MM-DD")
        
        service = get_service()
        success, analysis, message = service.create_profit_loss_analysis(data)
        
        if success:
            return success_response({
                'id': analysis.id,
                'period_start': analysis.period_start.isoformat() if analysis.period_start else None,
                'period_end': analysis.period_end.isoformat() if analysis.period_end else None,
                'period_type': analysis.period_type
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating profit/loss analysis: {str(e)}")

# ==================== Dashboard Widget Routes ====================

@reporting_analytics_bp.route('/dashboard-widgets', methods=['GET'])
@feature_required('reporting_analytics')
def get_dashboard_widgets():
    """Get dashboard widgets with optional filters"""
    try:
        filters = {}
        for param in ['dashboard_id', 'widget_type', 'is_active', 'is_default']:
            if param in request.args:
                if param in ['is_active', 'is_default']:
                    filters[param] = request.args.get(param).lower() == 'true'
                else:
                    filters[param] = request.args.get(param)
        
        service = get_service()
        widgets = service.get_dashboard_widgets(filters)
        
        result = []
        for widget in widgets:
            result.append({
                'id': widget.id,
                'name': widget.name,
                'widget_type': widget.widget_type,
                'title': widget.title,
                'description': widget.description,
                'data_source': widget.data_source,
                'query_config': widget.query_config,
                'display_config': widget.display_config,
                'refresh_interval': widget.refresh_interval,
                'dashboard_id': widget.dashboard_id,
                'position_x': widget.position_x,
                'position_y': widget.position_y,
                'width': widget.width,
                'height': widget.height,
                'roles_allowed': widget.roles_allowed,
                'users_allowed': widget.users_allowed,
                'is_active': widget.is_active,
                'is_default': widget.is_default,
                'created_at': widget.created_at.isoformat() if widget.created_at else None,
                'updated_at': widget.updated_at.isoformat() if widget.updated_at else None
            })
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving dashboard widgets: {str(e)}")

@reporting_analytics_bp.route('/dashboard-widgets', methods=['POST'])
@feature_required('reporting_analytics')
def create_dashboard_widget():
    """Create a dashboard widget"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['name', 'widget_type']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        service = get_service()
        success, widget, message = service.create_dashboard_widget(data)
        
        if success:
            return success_response({
                'id': widget.id,
                'name': widget.name,
                'widget_type': widget.widget_type
            }, message, 201)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error creating dashboard widget: {str(e)}")

# ==================== Analytics Cache Routes ====================

@reporting_analytics_bp.route('/analytics-cache/<cache_key>', methods=['GET'])
@feature_required('reporting_analytics')
def get_analytics_cache(cache_key):
    """Get analytics cache by key"""
    try:
        service = get_service()
        cache = service.get_analytics_cache(cache_key)
        
        if not cache:
            return handle_error("Cache not found or expired", 404)
        
        result = {
            'cache_key': cache.cache_key,
            'cache_type': cache.cache_type,
            'cache_data': cache.cache_data,
            'created_at': cache.created_at.isoformat() if cache.created_at else None,
            'expires_at': cache.expires_at.isoformat() if cache.expires_at else None,
            'hit_count': cache.hit_count,
            'is_expired': cache.is_expired
        }
        
        return success_response(result)
        
    except Exception as e:
        return handle_error(f"Error retrieving analytics cache: {str(e)}")

@reporting_analytics_bp.route('/analytics-cache', methods=['POST'])
@feature_required('reporting_analytics')
def set_analytics_cache():
    """Set analytics cache"""
    try:
        data = request.get_json()
        if not data:
            return handle_error("No data provided")
        
        # Validate required fields
        required_fields = ['cache_key', 'cache_type', 'cache_data']
        validation_result = validate_required_fields(data, required_fields)
        if validation_result:
            return handle_error(validation_result)
        
        expires_in_minutes = data.get('expires_in_minutes', 60)
        
        service = get_service()
        success, message = service.set_analytics_cache(
            data['cache_key'],
            data['cache_type'],
            data['cache_data'],
            expires_in_minutes
        )
        
        if success:
            return success_response(message=message)
        else:
            return handle_error(message)
        
    except Exception as e:
        return handle_error(f"Error setting analytics cache: {str(e)}")

# ==================== Error Handlers ====================

@reporting_analytics_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@reporting_analytics_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500