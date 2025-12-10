from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Order, Payment, MenuItem, Category, Settings
from datetime import datetime, timedelta
from decimal import Decimal
import io
import csv

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    """Reports dashboard"""
    return render_template('reports/index.html')

@reports_bp.route('/daily')
@login_required
def daily_report():
    """Daily sales report"""
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        report_date = datetime.utcnow().date()
    
    # Get orders for the day
    orders = Order.query.filter(
        db.func.date(Order.created_at) == report_date
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate totals
    total_orders = len(orders)
    total_revenue = sum(order.grand_total or 0 for order in orders)
    total_cgst = sum(order.cgst_amount or 0 for order in orders)
    total_sgst = sum(order.sgst_amount or 0 for order in orders)
    
    # Payment breakdown
    payment_breakdown = {}
    for order in orders:
        payments = Payment.get_completed_payments_by_order(order.id)
        for payment in payments:
            mode = payment.payment_mode
            payment_breakdown[mode] = payment_breakdown.get(mode, Decimal('0')) + payment.amount
    
    # Order status breakdown
    status_breakdown = {}
    for order in orders:
        status = order.status
        status_breakdown[status] = status_breakdown.get(status, 0) + 1
    
    return render_template('reports/daily.html',
                        report_date=report_date,
                        orders=orders,
                        total_orders=total_orders,
                        total_revenue=total_revenue,
                        total_cgst=total_cgst,
                        total_sgst=total_sgst,
                        payment_breakdown=payment_breakdown,
                        status_breakdown=status_breakdown)

@reports_bp.route('/monthly')
@login_required
def monthly_report():
    """Monthly sales report"""
    month_str = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
    except ValueError:
        year = datetime.utcnow().year
        month = datetime.utcnow().month
    
    # Get orders for the month
    orders = Order.query.filter(
        db.func.extract('year', Order.created_at) == year,
        db.func.extract('month', Order.created_at) == month
    ).order_by(Order.created_at.desc()).all()
    
    # Calculate totals
    total_orders = len(orders)
    total_revenue = sum(order.grand_total or 0 for order in orders)
    total_cgst = sum(order.cgst_amount or 0 for order in orders)
    total_sgst = sum(order.sgst_amount or 0 for order in orders)
    
    # Daily breakdown
    daily_breakdown = {}
    for order in orders:
        day = order.created_at.day
        if day not in daily_breakdown:
            daily_breakdown[day] = {
                'orders': 0,
                'revenue': Decimal('0'),
                'cgst': Decimal('0'),
                'sgst': Decimal('0')
            }
        
        daily_breakdown[day]['orders'] += 1
        daily_breakdown[day]['revenue'] += order.grand_total or 0
        daily_breakdown[day]['cgst'] += order.cgst_amount or 0
        daily_breakdown[day]['sgst'] += order.sgst_amount or 0
    
    return render_template('reports/monthly.html',
                        year=year,
                        month=month,
                        orders=orders,
                        total_orders=total_orders,
                        total_revenue=total_revenue,
                        total_cgst=total_cgst,
                        total_sgst=total_sgst,
                        daily_breakdown=daily_breakdown)

@reports_bp.route('/gstr1')
@login_required
def gstr1_report():
    """GSTR-1 report generation"""
    month_str = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
    except ValueError:
        year = datetime.utcnow().year
        month = datetime.utcnow().month
    
    # Get orders for the month (completed orders only)
    orders = Order.query.filter(
        db.func.extract('year', Order.created_at) == year,
        db.func.extract('month', Order.created_at) == month,
        Order.status == 'Completed'
    ).order_by(Order.created_at.desc()).all()
    
    # GSTR-1 calculations
    total_turnover = sum(order.grand_total or 0 for order in orders)
    total_cgst = sum(order.cgst_amount or 0 for order in orders)
    total_sgst = sum(order.sgst_amount or 0 for order in orders)
    total_igst = Decimal('0')  # Interstate sales (if applicable)
    
    # Taxable supplies (inter-state)
    taxable_supplies = total_turnover
    
    return render_template('reports/gstr1.html',
                        year=year,
                        month=month,
                        orders=orders,
                        total_turnover=total_turnover,
                        total_cgst=total_cgst,
                        total_sgst=total_sgst,
                        total_igst=total_igst,
                        taxable_supplies=taxable_supplies)

@reports_bp.route('/export/daily')
@login_required
def export_daily():
    """Export daily report as CSV"""
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        report_date = datetime.utcnow().date()
    
    orders = Order.query.filter(
        db.func.date(Order.created_at) == report_date
    ).order_by(Order.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Order Number', 'Date', 'Customer', 'Subtotal', 'CGST', 'SGST', 
        'Total', 'Status', 'Payment Mode'
    ])
    
    # Write data
    for order in orders:
        payments = Payment.get_completed_payments_by_order(order.id)
        payment_mode = payments[0].payment_mode if payments else 'N/A'
        
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.customer_name or 'N/A',
            order.subtotal or 0,
            order.cgst_amount or 0,
            order.sgst_amount or 0,
            order.grand_total or 0,
            order.status,
            payment_mode
        ])
    
    # Create response
    output.seek(0)
    filename = f'daily_report_{report_date.strftime("%Y%m%d")}.csv'
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        filename=filename,
        as_attachment=True,
        mimetype='text/csv'
    )

@reports_bp.route('/export/monthly')
@login_required
def export_monthly():
    """Export monthly report as CSV"""
    month_str = request.args.get('month', datetime.utcnow().strftime('%Y-%m'))
    
    try:
        year, month = map(int, month_str.split('-'))
    except ValueError:
        year = datetime.utcnow().year
        month = datetime.utcnow().month
    
    orders = Order.query.filter(
        db.func.extract('year', Order.created_at) == year,
        db.func.extract('month', Order.created_at) == month
    ).order_by(Order.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Order Number', 'Date', 'Customer', 'Subtotal', 'CGST', 'SGST', 
        'Total', 'Status', 'Payment Mode'
    ])
    
    # Write data
    for order in orders:
        payments = Payment.get_completed_payments_by_order(order.id)
        payment_mode = payments[0].payment_mode if payments else 'N/A'
        
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.customer_name or 'N/A',
            order.subtotal or 0,
            order.cgst_amount or 0,
            order.sgst_amount or 0,
            order.grand_total or 0,
            order.status,
            payment_mode
        ])
    
    # Create response
    output.seek(0)
    filename = f'monthly_report_{year}{month:02d}.csv'
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        filename=filename,
        as_attachment=True,
        mimetype='text/csv'
    )
