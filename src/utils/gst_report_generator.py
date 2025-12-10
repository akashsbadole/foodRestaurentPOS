#!/usr/bin/env python3
"""
GST Report Generator for Restaurant POS System
Provides comprehensive GST-compliant reporting functionality
"""

import csv
import os
from datetime import datetime, timedelta
from io import StringIO


class GSTReportGenerator:
    """GST Report Generator for comprehensive GST compliance reporting"""
    
    def __init__(self, db):
        self.db = db
        self.gst_rate = 5.0  # Default GST rate (5% total: 2.5% CGST + 2.5% SGST)
    
    def get_daily_gst_report(self, date=None):
        """
        Generate daily GST report
        Args:
            date: Date string in YYYY-MM-DD format (default: today)
        Returns:
            dict: Report data with summary and details
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Query orders for the specified date
        query = """
        SELECT 
            o.order_number,
            o.created_at,
            o.customer_name,
            o.subtotal,
            o.cgst_amount,
            o.sgst_amount,
            o.total_tax,
            o.total,
            o.order_type
        FROM orders o
        WHERE DATE(o.created_at) = DATE(?)
        AND o.status != 'Cancelled'
        ORDER BY o.created_at
        """
        
        self.db.execute_query(query, (date,))
        orders = self.db.fetch_all()
        
        # Calculate totals
        total_subtotal = sum(order[3] or 0 for order in orders)
        total_cgst = sum(order[4] or 0 for order in orders)
        total_sgst = sum(order[5] or 0 for order in orders)
        total_tax = sum(order[6] or 0 for order in orders)
        total_amount = sum(order[7] or 0 for order in orders)
        total_orders = len(orders)
        
        return {
            'date': date,
            'summary': {
                'total_orders': total_orders,
                'total_subtotal': total_subtotal,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_tax': total_tax,
                'total_amount': total_amount
            },
            'details': orders
        }
    
    def get_monthly_gst_report(self, year=None, month=None):
        """
        Generate monthly GST report
        Args:
            year: Year (default: current year)
            month: Month (1-12) (default: current month)
        Returns:
            dict: Report data with summary and details
        """
        if not year:
            year = datetime.now().year
        if not month:
            month = datetime.now().month
        
        # Format month for SQL query
        month_str = f"{year:04d}-{month:02d}"
        
        # Query orders for the specified month
        query = """
        SELECT 
            o.order_number,
            o.created_at,
            o.customer_name,
            o.subtotal,
            o.cgst_amount,
            o.sgst_amount,
            o.total_tax,
            o.total,
            o.order_type
        FROM orders o
        WHERE strftime('%Y-%m', o.created_at) = ?
        AND o.status != 'Cancelled'
        ORDER BY o.created_at
        """
        
        self.db.execute_query(query, (month_str,))
        orders = self.db.fetch_all()
        
        # Calculate totals
        total_subtotal = sum(order[3] or 0 for order in orders)
        total_cgst = sum(order[4] or 0 for order in orders)
        total_sgst = sum(order[5] or 0 for order in orders)
        total_tax = sum(order[6] or 0 for order in orders)
        total_amount = sum(order[7] or 0 for order in orders)
        total_orders = len(orders)
        
        return {
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B %Y'),
            'summary': {
                'total_orders': total_orders,
                'total_subtotal': total_subtotal,
                'total_cgst': total_cgst,
                'total_sgst': total_sgst,
                'total_tax': total_tax,
                'total_amount': total_amount
            },
            'details': orders
        }
    
    def get_gstr1_data(self, from_date=None, to_date=None):
        """
        Generate GSTR-1 compliant data for export
        Args:
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        Returns:
            list: GSTR-1 compliant data rows
        """
        if not from_date:
            from_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        # Query orders for GSTR-1 format
        query = """
        SELECT 
            o.order_number,
            DATE(o.created_at) as invoice_date,
            COALESCE(o.customer_name, 'Cash Customer') as customer_name,
            o.subtotal as taxable_value,
            o.cgst_amount,
            o.sgst_amount,
            o.total_tax,
            o.total as total_amount
        FROM orders o
        WHERE DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
        AND o.status != 'Cancelled'
        ORDER BY o.created_at
        """
        
        self.db.execute_query(query, (from_date, to_date))
        orders = self.db.fetch_all()
        
        # Format for GSTR-1
        gstr1_data = []
        for order in orders:
            gstr1_data.append({
                'invoice_number': order[0],
                'invoice_date': order[1],
                'customer_name': order[2],
                'taxable_value': order[3] or 0,
                'cgst_amount': order[4] or 0,
                'sgst_amount': order[5] or 0,
                'total_tax': order[6] or 0,
                'total_amount': order[7] or 0
            })
        
        return gstr1_data
    
    def export_gstr1_csv(self, file_path, from_date=None, to_date=None):
        """
        Export GSTR-1 compliant CSV file
        Args:
            file_path: Path to save the CSV file
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        Returns:
            bool: Success status
        """
        try:
            gstr1_data = self.get_gstr1_data(from_date, to_date)
            
            # GSTR-1 CSV headers as per GST compliance
            headers = [
                'Invoice Number',
                'Invoice Date',
                'Customer Name',
                'Taxable Value',
                'CGST Rate',
                'CGST Amount',
                'SGST Rate',
                'SGST Amount',
                'Total Tax',
                'Total Amount'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write metadata
                csvfile.write("# GSTR-1 Export for GST Compliance\n")
                csvfile.write(f"# Period: {from_date or 'Start'} to {to_date or 'End'}\n")
                csvfile.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                csvfile.write(f"# Total Records: {len(gstr1_data)}\n\n")
                
                # Write headers
                writer.writerow(headers)
                
                # Write data
                for order in gstr1_data:
                    writer.writerow([
                        order['invoice_number'],
                        order['invoice_date'],
                        order['customer_name'],
                        f"{order['taxable_value']:.2f}",
                        "2.5%",  # CGST Rate
                        f"{order['cgst_amount']:.2f}",
                        "2.5%",  # SGST Rate
                        f"{order['sgst_amount']:.2f}",
                        f"{order['total_tax']:.2f}",
                        f"{order['total_amount']:.2f}"
                    ])
                
                # Write summary
                total_taxable = sum(order['taxable_value'] for order in gstr1_data)
                total_cgst = sum(order['cgst_amount'] for order in gstr1_data)
                total_sgst = sum(order['sgst_amount'] for order in gstr1_data)
                total_tax = sum(order['total_tax'] for order in gstr1_data)
                total_amount = sum(order['total_amount'] for order in gstr1_data)
                
                csvfile.write(f"\n# SUMMARY\n")
                csvfile.write(f"# Total Taxable Value: ₹{total_taxable:.2f}\n")
                csvfile.write(f"# Total CGST: ₹{total_cgst:.2f}\n")
                csvfile.write(f"# Total SGST: ₹{total_sgst:.2f}\n")
                csvfile.write(f"# Total Tax: ₹{total_tax:.2f}\n")
                csvfile.write(f"# Total Amount: ₹{total_amount:.2f}\n")
            
            return True
            
        except Exception as e:
            print(f"Error exporting GSTR-1 CSV: {e}")
            return False
    
    def export_daily_report_csv(self, file_path, date=None):
        """
        Export daily GST report to CSV
        Args:
            file_path: Path to save the CSV file
            date: Date in YYYY-MM-DD format
        Returns:
            bool: Success status
        """
        try:
            report_data = self.get_daily_gst_report(date)
            
            headers = [
                'Order Number',
                'Time',
                'Customer Name',
                'Order Type',
                'Taxable Value',
                'CGST (2.5%)',
                'SGST (2.5%)',
                'Total Tax',
                'Grand Total'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write metadata
                csvfile.write(f"# Daily GST Report\n")
                csvfile.write(f"# Date: {report_data['date']}\n")
                csvfile.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write summary
                summary = report_data['summary']
                csvfile.write("# SUMMARY\n")
                writer.writerow(['Total Orders', summary['total_orders']])
                writer.writerow(['Total Taxable Value', f"₹{summary['total_subtotal']:.2f}"])
                writer.writerow(['Total CGST', f"₹{summary['total_cgst']:.2f}"])
                writer.writerow(['Total SGST', f"₹{summary['total_sgst']:.2f}"])
                writer.writerow(['Total Tax', f"₹{summary['total_tax']:.2f}"])
                writer.writerow(['Grand Total', f"₹{summary['total_amount']:.2f}"])
                csvfile.write("\n")
                
                # Write headers
                writer.writerow(headers)
                
                # Write details
                for order in report_data['details']:
                    order_number, created_at, customer_name, subtotal, cgst, sgst, total_tax, total, order_type = order
                    # Extract time from datetime
                    time_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
                    
                    writer.writerow([
                        order_number,
                        time_str,
                        customer_name or 'Cash Customer',
                        order_type,
                        f"{subtotal or 0:.2f}",
                        f"{cgst or 0:.2f}",
                        f"{sgst or 0:.2f}",
                        f"{total_tax or 0:.2f}",
                        f"{total or 0:.2f}"
                    ])
            
            return True
            
        except Exception as e:
            print(f"Error exporting daily report CSV: {e}")
            return False
    
    def export_monthly_report_csv(self, file_path, year=None, month=None):
        """
        Export monthly GST report to CSV
        Args:
            file_path: Path to save the CSV file
            year: Year (default: current year)
            month: Month (1-12) (default: current month)
        Returns:
            bool: Success status
        """
        try:
            report_data = self.get_monthly_gst_report(year, month)
            
            headers = [
                'Order Number',
                'Date',
                'Customer Name',
                'Order Type',
                'Taxable Value',
                'CGST (2.5%)',
                'SGST (2.5%)',
                'Total Tax',
                'Grand Total'
            ]
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write metadata
                csvfile.write(f"# Monthly GST Report\n")
                csvfile.write(f"# Period: {report_data['month_name']}\n")
                csvfile.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Write summary
                summary = report_data['summary']
                csvfile.write("# SUMMARY\n")
                writer.writerow(['Total Orders', summary['total_orders']])
                writer.writerow(['Total Taxable Value', f"₹{summary['total_subtotal']:.2f}"])
                writer.writerow(['Total CGST', f"₹{summary['total_cgst']:.2f}"])
                writer.writerow(['Total SGST', f"₹{summary['total_sgst']:.2f}"])
                writer.writerow(['Total Tax', f"₹{summary['total_tax']:.2f}"])
                writer.writerow(['Grand Total', f"₹{summary['total_amount']:.2f}"])
                csvfile.write("\n")
                
                # Write headers
                writer.writerow(headers)
                
                # Write details
                for order in report_data['details']:
                    order_number, created_at, customer_name, subtotal, cgst, sgst, total_tax, total, order_type = order
                    # Extract date from datetime
                    date_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    
                    writer.writerow([
                        order_number,
                        date_str,
                        customer_name or 'Cash Customer',
                        order_type,
                        f"{subtotal or 0:.2f}",
                        f"{cgst or 0:.2f}",
                        f"{sgst or 0:.2f}",
                        f"{total_tax or 0:.2f}",
                        f"{total or 0:.2f}"
                    ])
            
            return True
            
        except Exception as e:
            print(f"Error exporting monthly report CSV: {e}")
            return False
    
    def get_gst_summary(self, from_date=None, to_date=None):
        """
        Get GST summary for a date range
        Args:
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        Returns:
            dict: GST summary data
        """
        if not from_date:
            from_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        query = """
        SELECT 
            COUNT(*) as total_orders,
            SUM(o.subtotal) as total_subtotal,
            SUM(o.cgst_amount) as total_cgst,
            SUM(o.sgst_amount) as total_sgst,
            SUM(o.total_tax) as total_tax,
            SUM(o.total) as total_amount
        FROM orders o
        WHERE DATE(o.created_at) BETWEEN DATE(?) AND DATE(?)
        AND o.status != 'Cancelled'
        """
        
        self.db.execute_query(query, (from_date, to_date))
        result = self.db.fetch_one()
        
        if result:
            return {
                'from_date': from_date,
                'to_date': to_date,
                'total_orders': result[0] or 0,
                'total_subtotal': result[1] or 0,
                'total_cgst': result[2] or 0,
                'total_sgst': result[3] or 0,
                'total_tax': result[4] or 0,
                'total_amount': result[5] or 0
            }
        else:
            return {
                'from_date': from_date,
                'to_date': to_date,
                'total_orders': 0,
                'total_subtotal': 0,
                'total_cgst': 0,
                'total_sgst': 0,
                'total_tax': 0,
                'total_amount': 0
            }