#!/usr/bin/env python3
"""
GST Reports Screen for Restaurant POS System
Provides comprehensive GST-compliant reporting interface
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
from .base_ui import BaseUI
from src.utils.constants import *
from src.utils.gst_report_generator import GSTReportGenerator


class GSTReportsScreen(BaseUI):
    """GST Reports screen UI component with modern design"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.gst_generator = GSTReportGenerator(app.db)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern GST reports UI"""
        # Main container with background
        main_container = tk.Frame(self.app.content_frame, bg=COLOR_BACKGROUND_LIGHT)
        main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Title with modern styling
        title_frame = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        title_frame.pack(fill=tk.X, pady=(0, 16))
        
        title_label = tk.Label(
            title_frame,
            text="🧾 GST Compliance Reports",
            font=("Segoe UI", 24, "bold"),
            fg=COLOR_PRIMARY_DARK,
            bg=COLOR_CARD_WHITE
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Generate GST-compliant reports for Indian restaurant compliance",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Report type selection card
        report_type_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        report_type_card.pack(fill=tk.X, pady=(0, 16))
        
        # Report type selection with modern styling
        report_type_container = tk.Frame(report_type_card, bg=COLOR_CARD_WHITE)
        report_type_container.pack(fill=tk.X, padx=20, pady=16)
        
        type_label = tk.Label(
            report_type_container,
            text="📊 Report Type",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        type_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.report_type_var = tk.StringVar(value="Daily GST Report")
        report_type_combo = ttk.Combobox(
            report_type_container, 
            textvariable=self.report_type_var,
            values=["Daily GST Report", "Monthly GST Report", "GSTR-1 Export"],
            state="readonly",
            width=40,
            font=("Segoe UI", 11)
        )
        report_type_combo.pack(fill=tk.X, pady=(0, 8))
        report_type_combo.bind("<<ComboboxSelected>>", self.on_report_type_change)
        
        # Date range selection card
        date_range_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        date_range_card.pack(fill=tk.X, pady=(0, 16))
        
        date_range_container = tk.Frame(date_range_card, bg=COLOR_CARD_WHITE)
        date_range_container.pack(fill=tk.X, padx=20, pady=16)
        
        date_label = tk.Label(
            date_range_container,
            text="📅 Date Selection",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        date_label.pack(anchor=tk.W, pady=(0, 8))
        
        # Date selection frame
        self.date_frame = tk.Frame(date_range_container, bg=COLOR_CARD_WHITE)
        self.date_frame.pack(fill=tk.X)
        
        # Daily report date selection
        self.daily_frame = tk.Frame(self.date_frame, bg=COLOR_CARD_WHITE)
        
        daily_date_frame = tk.Frame(self.daily_frame, bg=COLOR_CARD_WHITE)
        daily_date_frame.pack(fill=tk.X)
        
        daily_label = tk.Label(
            daily_date_frame,
            text="Select Date:",
            font=("Segoe UI", 11, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        daily_label.pack(anchor=tk.W, pady=(0, 4))
        
        self.daily_date_entry = tk.Entry(
            daily_date_frame,
            width=20,
            font=("Segoe UI", 11),
            relief=tk.SOLID,
            bd=1,
            bg=COLOR_CARD_WHITE,
            fg=COLOR_TEXT_PRIMARY
        )
        self.daily_date_entry.pack(fill=tk.X)
        self.daily_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Monthly report date selection
        self.monthly_frame = tk.Frame(self.date_frame, bg=COLOR_CARD_WHITE)
        
        monthly_date_frame = tk.Frame(self.monthly_frame, bg=COLOR_CARD_WHITE)
        monthly_date_frame.pack(fill=tk.X)
        
        month_label = tk.Label(
            monthly_date_frame,
            text="Select Month:",
            font=("Segoe UI", 11, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        month_label.pack(anchor=tk.W, pady=(0, 4))
        
        month_select_frame = tk.Frame(monthly_date_frame, bg=COLOR_CARD_WHITE)
        month_select_frame.pack(fill=tk.X)
        
        self.month_var = tk.StringVar(value=datetime.now().strftime('%Y-%m'))
        month_combo = ttk.Combobox(
            month_select_frame,
            textvariable=self.month_var,
            values=self.generate_month_options(),
            state="readonly",
            width=15,
            font=("Segoe UI", 11)
        )
        month_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # GSTR-1 date range selection
        self.gstr1_frame = tk.Frame(self.date_frame, bg=COLOR_CARD_WHITE)
        
        gstr1_date_frame = tk.Frame(self.gstr1_frame, bg=COLOR_CARD_WHITE)
        gstr1_date_frame.pack(fill=tk.X)
        
        # From date
        from_date_frame = tk.Frame(gstr1_date_frame, bg=COLOR_CARD_WHITE)
        from_date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        from_label = tk.Label(
            from_date_frame,
            text="From Date:",
            font=("Segoe UI", 11, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        from_label.pack(anchor=tk.W, pady=(0, 4))
        
        self.from_date_entry = tk.Entry(
            from_date_frame,
            width=15,
            font=("Segoe UI", 11),
            relief=tk.SOLID,
            bd=1,
            bg=COLOR_CARD_WHITE,
            fg=COLOR_TEXT_PRIMARY
        )
        self.from_date_entry.pack(fill=tk.X)
        self.from_date_entry.insert(0, datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        
        # To date
        to_date_frame = tk.Frame(gstr1_date_frame, bg=COLOR_CARD_WHITE)
        to_date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        to_label = tk.Label(
            to_date_frame,
            text="To Date:",
            font=("Segoe UI", 11, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        to_label.pack(anchor=tk.W, pady=(0, 4))
        
        self.to_date_entry = tk.Entry(
            to_date_frame,
            width=15,
            font=("Segoe UI", 11),
            relief=tk.SOLID,
            bd=1,
            bg=COLOR_CARD_WHITE,
            fg=COLOR_TEXT_PRIMARY
        )
        self.to_date_entry.pack(fill=tk.X)
        self.to_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Show daily frame by default
        self.daily_frame.pack(fill=tk.X)
        
        # Action buttons card
        buttons_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        buttons_card.pack(fill=tk.X, pady=(0, 16))
        
        buttons_container = tk.Frame(buttons_card, bg=COLOR_CARD_WHITE)
        buttons_container.pack(fill=tk.X, padx=20, pady=16)
        
        # Generate Report Button (Primary)
        self.generate_btn = tk.Button(
            buttons_container,
            text="🔍 Generate Report",
            command=self.generate_report,
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_PRIMARY,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=COLOR_PRIMARY_LIGHT,
            activeforeground="white"
        )
        self.generate_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        # Export CSV Button (Secondary)
        self.export_csv_btn = tk.Button(
            buttons_container,
            text="📄 Export CSV",
            command=self.export_csv,
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_SUCCESS,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#27ae60",
            activeforeground="white"
        )
        self.export_csv_btn.pack(side=tk.LEFT, padx=8)
        
        # Export GSTR-1 Button (Tertiary)
        self.export_gstr1_btn = tk.Button(
            buttons_container,
            text="📋 Export GSTR-1",
            command=self.export_gstr1,
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_WARNING,
            fg="white",
            relief=tk.FLAT,
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground="#f39c12",
            activeforeground="white"
        )
        self.export_gstr1_btn.pack(side=tk.LEFT, padx=8)
        
        # Report display card
        report_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # Report header
        report_header = tk.Frame(report_card, bg="#f8f9fa", relief=tk.RIDGE, bd=1)
        report_header.pack(fill=tk.X)
        
        self.report_title_label = tk.Label(
            report_header,
            text="📈 GST Report Data",
            font=("Segoe UI", 16, "bold"),
            fg=COLOR_PRIMARY_DARK,
            bg="#f8f9fa"
        )
        self.report_title_label.pack(pady=12)
        
        # Report content with modern treeview
        report_content = tk.Frame(report_card, bg=COLOR_CARD_WHITE)
        report_content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Create modern styled treeview
        self.report_tree, report_scrollbar = self.create_modern_treeview(report_content)
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Loading indicator (initially hidden)
        self.loading_indicator = tk.Label(
            report_card,
            text="⏳ Generating GST report...",
            font=("Segoe UI", 14, "normal"),
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        
        # Generate default report
        self.generate_report()
    
    def generate_month_options(self):
        """Generate month options for the combobox"""
        months = []
        current_date = datetime.now()
        
        # Generate last 12 months
        for i in range(12):
            month_date = current_date.replace(day=1) - timedelta(days=i*30)
            month_str = month_date.strftime('%Y-%m')
            display_str = month_date.strftime('%B %Y')
            months.append(month_str)
        
        return sorted(months, reverse=True)
    
    def on_report_type_change(self, event=None):
        """Handle report type change"""
        report_type = self.report_type_var.get()
        
        # Hide all date frames
        self.daily_frame.pack_forget()
        self.monthly_frame.pack_forget()
        self.gstr1_frame.pack_forget()
        
        # Show appropriate date frame
        if report_type == "Daily GST Report":
            self.daily_frame.pack(fill=tk.X)
            self.report_title_label.config(text="📈 Daily GST Report")
        elif report_type == "Monthly GST Report":
            self.monthly_frame.pack(fill=tk.X)
            self.report_title_label.config(text="📊 Monthly GST Report")
        elif report_type == "GSTR-1 Export":
            self.gstr1_frame.pack(fill=tk.X)
            self.report_title_label.config(text="📋 GSTR-1 Export Data")
    
    def create_modern_treeview(self, parent):
        """Create modern styled treeview with enhanced design"""
        # Create treeview with modern styling
        tree = ttk.Treeview(parent)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure modern style for treeview
        style = ttk.Style()
        
        # Configure heading style
        style.configure(
            "Modern.Treeview.Heading",
            background="#f8f9fa",
            foreground=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 10, "bold"),
            relief=tk.RIDGE,
            borderwidth=1
        )
        
        # Configure treeview style
        style.configure(
            "Modern.Treeview",
            background=COLOR_CARD_WHITE,
            foreground=COLOR_TEXT_PRIMARY,
            font=("Segoe UI", 10),
            fieldbackground=COLOR_CARD_WHITE,
            borderwidth=1,
            relief=tk.SOLID
        )
        
        # Configure selected style
        style.map(
            "Modern.Treeview",
            background=[("selected", "#e3f2fd")],
            foreground=[("selected", COLOR_TEXT_PRIMARY)]
        )
        
        tree.configure(style="Modern.Treeview")
        
        return tree, scrollbar
    
    def show_loading_state(self, show=True):
        """Show or hide loading indicator"""
        if show:
            self.report_tree.pack_forget()
            self.loading_indicator.pack(pady=50)
            self.generate_btn.config(state=tk.DISABLED, text="⏳ Generating...")
        else:
            self.loading_indicator.pack_forget()
            self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            self.generate_btn.config(state=tk.NORMAL, text="🔍 Generate Report")
    
    def show_message(self, title, message, msg_type="info"):
        """Show modern styled message dialog"""
        if msg_type == "success":
            messagebox.showinfo(title, f"✅ {message}")
        elif msg_type == "error":
            messagebox.showerror(title, f"❌ {message}")
        elif msg_type == "warning":
            messagebox.showwarning(title, f"⚠️ {message}")
        else:
            messagebox.showinfo(title, f"ℹ️ {message}")
    
    def generate_report(self):
        """Generate the selected GST report"""
        # Show loading state
        self.show_loading_state(True)
        self.app.root.update()
        
        # Process report generation after a short delay for visual feedback
        self.app.root.after(500, self._process_report)
    
    def _process_report(self):
        """Process report generation after loading delay"""
        report_type = self.report_type_var.get()
        
        # Clear existing columns and data
        self.report_tree['columns'] = ()
        self.report_tree["show"] = "headings"
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        try:
            if report_type == "Daily GST Report":
                self.generate_daily_report()
            elif report_type == "Monthly GST Report":
                self.generate_monthly_report()
            elif report_type == "GSTR-1 Export":
                self.generate_gstr1_report()
            
            # Hide loading state
            self.show_loading_state(False)
            
            # Show success message
            self.show_message("Success", f"GST report generated successfully!", "success")
            
        except Exception as e:
            # Hide loading state
            self.show_loading_state(False)
            # Show error message
            self.show_message("Error", f"Failed to generate GST report: {str(e)}", "error")
    
    def generate_daily_report(self):
        """Generate daily GST report"""
        date = self.daily_date_entry.get()
        report_data = self.gst_generator.get_daily_gst_report(date)
        
        # Configure columns
        self.report_tree['columns'] = ("order_number", "time", "customer", "type", "subtotal", "cgst", "sgst", "tax", "total")
        
        # Configure headings
        self.report_tree.heading("order_number", text="Order #")
        self.report_tree.heading("time", text="Time")
        self.report_tree.heading("customer", text="Customer")
        self.report_tree.heading("type", text="Type")
        self.report_tree.heading("subtotal", text="Taxable Value")
        self.report_tree.heading("cgst", text="CGST (2.5%)")
        self.report_tree.heading("sgst", text="SGST (2.5%)")
        self.report_tree.heading("tax", text="Total Tax")
        self.report_tree.heading("total", text="Grand Total")
        
        # Configure columns
        self.report_tree.column("order_number", width=120, anchor=tk.CENTER)
        self.report_tree.column("time", width=80, anchor=tk.CENTER)
        self.report_tree.column("customer", width=150, anchor=tk.W)
        self.report_tree.column("type", width=80, anchor=tk.CENTER)
        self.report_tree.column("subtotal", width=120, anchor=tk.E)
        self.report_tree.column("cgst", width=100, anchor=tk.E)
        self.report_tree.column("sgst", width=100, anchor=tk.E)
        self.report_tree.column("tax", width=100, anchor=tk.E)
        self.report_tree.column("total", width=120, anchor=tk.E)
        
        # Add summary row
        summary = report_data['summary']
        self.report_tree.insert("", tk.END, values=(
            "SUMMARY", "", "", "",
            f"₹{summary['total_subtotal']:.2f}",
            f"₹{summary['total_cgst']:.2f}",
            f"₹{summary['total_sgst']:.2f}",
            f"₹{summary['total_tax']:.2f}",
            f"₹{summary['total_amount']:.2f}"
        ), tags=("summary",))
        
        # Add detail rows
        for order in report_data['details']:
            order_number, created_at, customer_name, subtotal, cgst, sgst, total_tax, total, order_type = order
            # Extract time from datetime
            time_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
            
            self.report_tree.insert("", tk.END, values=(
                order_number,
                time_str,
                customer_name or 'Cash Customer',
                order_type,
                f"₹{subtotal or 0:.2f}",
                f"₹{cgst or 0:.2f}",
                f"₹{sgst or 0:.2f}",
                f"₹{total_tax or 0:.2f}",
                f"₹{total or 0:.2f}"
            ))
        
        # Configure summary tag styling
        self.report_tree.tag_configure("summary", background="#e8f5e8", font=("Segoe UI", 10, "bold"))
    
    def generate_monthly_report(self):
        """Generate monthly GST report"""
        month_str = self.month_var.get()
        year, month = map(int, month_str.split('-'))
        
        report_data = self.gst_generator.get_monthly_gst_report(year, month)
        
        # Configure columns
        self.report_tree['columns'] = ("order_number", "date", "customer", "type", "subtotal", "cgst", "sgst", "tax", "total")
        
        # Configure headings
        self.report_tree.heading("order_number", text="Order #")
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("customer", text="Customer")
        self.report_tree.heading("type", text="Type")
        self.report_tree.heading("subtotal", text="Taxable Value")
        self.report_tree.heading("cgst", text="CGST (2.5%)")
        self.report_tree.heading("sgst", text="SGST (2.5%)")
        self.report_tree.heading("tax", text="Total Tax")
        self.report_tree.heading("total", text="Grand Total")
        
        # Configure columns
        self.report_tree.column("order_number", width=120, anchor=tk.CENTER)
        self.report_tree.column("date", width=100, anchor=tk.CENTER)
        self.report_tree.column("customer", width=150, anchor=tk.W)
        self.report_tree.column("type", width=80, anchor=tk.CENTER)
        self.report_tree.column("subtotal", width=120, anchor=tk.E)
        self.report_tree.column("cgst", width=100, anchor=tk.E)
        self.report_tree.column("sgst", width=100, anchor=tk.E)
        self.report_tree.column("tax", width=100, anchor=tk.E)
        self.report_tree.column("total", width=120, anchor=tk.E)
        
        # Add summary row
        summary = report_data['summary']
        self.report_tree.insert("", tk.END, values=(
            "SUMMARY", "", "", "",
            f"₹{summary['total_subtotal']:.2f}",
            f"₹{summary['total_cgst']:.2f}",
            f"₹{summary['total_sgst']:.2f}",
            f"₹{summary['total_tax']:.2f}",
            f"₹{summary['total_amount']:.2f}"
        ), tags=("summary",))
        
        # Add detail rows
        for order in report_data['details']:
            order_number, created_at, customer_name, subtotal, cgst, sgst, total_tax, total, order_type = order
            # Extract date from datetime
            date_str = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
            
            self.report_tree.insert("", tk.END, values=(
                order_number,
                date_str,
                customer_name or 'Cash Customer',
                order_type,
                f"₹{subtotal or 0:.2f}",
                f"₹{cgst or 0:.2f}",
                f"₹{sgst or 0:.2f}",
                f"₹{total_tax or 0:.2f}",
                f"₹{total or 0:.2f}"
            ))
        
        # Configure summary tag styling
        self.report_tree.tag_configure("summary", background="#e8f5e8", font=("Segoe UI", 10, "bold"))
    
    def generate_gstr1_report(self):
        """Generate GSTR-1 compliant report"""
        from_date = self.from_date_entry.get()
        to_date = self.to_date_entry.get()
        
        gstr1_data = self.gst_generator.get_gstr1_data(from_date, to_date)
        
        # Configure columns for GSTR-1 format
        self.report_tree['columns'] = ("invoice_no", "invoice_date", "customer", "taxable_value", "cgst", "sgst", "total_tax", "total_amount")
        
        # Configure headings
        self.report_tree.heading("invoice_no", text="Invoice Number")
        self.report_tree.heading("invoice_date", text="Invoice Date")
        self.report_tree.heading("customer", text="Customer Name")
        self.report_tree.heading("taxable_value", text="Taxable Value")
        self.report_tree.heading("cgst", text="CGST (2.5%)")
        self.report_tree.heading("sgst", text="SGST (2.5%)")
        self.report_tree.heading("total_tax", text="Total Tax")
        self.report_tree.heading("total_amount", text="Total Amount")
        
        # Configure columns
        self.report_tree.column("invoice_no", width=120, anchor=tk.CENTER)
        self.report_tree.column("invoice_date", width=100, anchor=tk.CENTER)
        self.report_tree.column("customer", width=150, anchor=tk.W)
        self.report_tree.column("taxable_value", width=120, anchor=tk.E)
        self.report_tree.column("cgst", width=100, anchor=tk.E)
        self.report_tree.column("sgst", width=100, anchor=tk.E)
        self.report_tree.column("total_tax", width=100, anchor=tk.E)
        self.report_tree.column("total_amount", width=120, anchor=tk.E)
        
        # Calculate totals
        total_taxable = sum(order['taxable_value'] for order in gstr1_data)
        total_cgst = sum(order['cgst_amount'] for order in gstr1_data)
        total_sgst = sum(order['sgst_amount'] for order in gstr1_data)
        total_tax = sum(order['total_tax'] for order in gstr1_data)
        total_amount = sum(order['total_amount'] for order in gstr1_data)
        
        # Add summary row
        self.report_tree.insert("", tk.END, values=(
            "TOTAL", "", "", "",
            f"₹{total_taxable:.2f}",
            f"₹{total_cgst:.2f}",
            f"₹{total_sgst:.2f}",
            f"₹{total_tax:.2f}",
            f"₹{total_amount:.2f}"
        ), tags=("summary",))
        
        # Add detail rows
        for order in gstr1_data:
            self.report_tree.insert("", tk.END, values=(
                order['invoice_number'],
                order['invoice_date'],
                order['customer_name'],
                f"₹{order['taxable_value']:.2f}",
                f"₹{order['cgst_amount']:.2f}",
                f"₹{order['sgst_amount']:.2f}",
                f"₹{order['total_tax']:.2f}",
                f"₹{order['total_amount']:.2f}"
            ))
        
        # Configure summary tag styling
        self.report_tree.tag_configure("summary", background="#fff3cd", font=("Segoe UI", 10, "bold"))
    
    def export_csv(self):
        """Export current report to CSV"""
        report_type = self.report_type_var.get()
        
        if not self.report_tree.get_children():
            self.show_message("Warning", "No report data to export", "warning")
            return
        
        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if report_type == "Daily GST Report":
            date = self.daily_date_entry.get()
            default_filename = f"daily_gst_report_{date}_{timestamp}.csv"
            success = self.gst_generator.export_daily_report_csv(default_filename, date)
        elif report_type == "Monthly GST Report":
            month_str = self.month_var.get()
            default_filename = f"monthly_gst_report_{month_str}_{timestamp}.csv"
            year, month = map(int, month_str.split('-'))
            success = self.gst_generator.export_monthly_report_csv(default_filename, year, month)
        else:
            self.show_message("Info", "Use 'Export GSTR-1' button for GSTR-1 format", "info")
            return
        
        if success:
            self.show_message("Success", f"Report exported to {default_filename}", "success")
        else:
            self.show_message("Error", "Failed to export report", "error")
    
    def export_gstr1(self):
        """Export GSTR-1 compliant CSV"""
        if not self.report_tree.get_children():
            self.show_message("Warning", "No report data to export", "warning")
            return
        
        # Ask for file location
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"GSTR1_export_{timestamp}.csv"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if not file_path:
            return
        
        from_date = self.from_date_entry.get()
        to_date = self.to_date_entry.get()
        
        success = self.gst_generator.export_gstr1_csv(file_path, from_date, to_date)
        
        if success:
            self.show_message("Success", f"GSTR-1 data exported to {file_path}", "success")
        else:
            self.show_message("Error", "Failed to export GSTR-1 data", "error")