import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from .base_ui import BaseUI
from src.utils.constants import *
from src.utils.helpers import export_to_csv, export_report_to_csv, create_export_options_dialog
from src.utils.license_decorator import require_license_feature, LicenseFeatureMixin

class ReportsScreen(BaseUI, LicenseFeatureMixin):
    """Reports screen UI component with modern design"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.loading_indicator = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern reports UI"""
        # Main container with background
        main_container = tk.Frame(self.app.content_frame, bg=COLOR_BACKGROUND_LIGHT)
        main_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Title with modern styling
        title_frame = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        title_frame.pack(fill=tk.X, pady=(0, 16))
        
        title_label = tk.Label(
            title_frame,
            text="📊 Business Analytics Reports",
            font=("Segoe UI", 24, "bold"),
            fg=COLOR_PRIMARY_DARK,
            bg=COLOR_CARD_WHITE
        )
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Generate and analyze comprehensive business reports",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_SECONDARY,
            bg=COLOR_CARD_WHITE
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Controls card
        controls_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        controls_card.pack(fill=tk.X, pady=(0, 16))
        
        # Report type selection with modern styling
        report_type_container = tk.Frame(controls_card, bg=COLOR_CARD_WHITE)
        report_type_container.pack(fill=tk.X, padx=20, pady=16)
        
        type_label = tk.Label(
            report_type_container,
            text="📋 Report Type",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        type_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.report_type_var = tk.StringVar(value="Daily Sales Summary")
        report_type_combo = ttk.Combobox(
            report_type_container, 
            textvariable=self.report_type_var,
            values=["Daily Sales Summary", "Sales by Item", "Sales by Category"],
            state="readonly",
            width=40,
            font=("Segoe UI", 11)
        )
        report_type_combo.pack(fill=tk.X, pady=(0, 8))
        
        # Date range selection with modern styling
        date_range_container = tk.Frame(controls_card, bg=COLOR_CARD_WHITE)
        date_range_container.pack(fill=tk.X, padx=20, pady=(0, 16))
        
        date_label = tk.Label(
            date_range_container,
            text="📅 Date Range",
            font=("Segoe UI", 12, "normal"),
            fg=COLOR_TEXT_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        date_label.pack(anchor=tk.W, pady=(0, 8))
        
        date_fields_frame = tk.Frame(date_range_container, bg=COLOR_CARD_WHITE)
        date_fields_frame.pack(fill=tk.X)
        
        # From date
        from_date_frame = tk.Frame(date_fields_frame, bg=COLOR_CARD_WHITE)
        from_date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        from_label = tk.Label(
            from_date_frame,
            text="From:",
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
        self.from_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # To date
        to_date_frame = tk.Frame(date_fields_frame, bg=COLOR_CARD_WHITE)
        to_date_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        
        to_label = tk.Label(
            to_date_frame,
            text="To:",
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
        
        # Action buttons with modern styling
        buttons_container = tk.Frame(controls_card, bg=COLOR_CARD_WHITE)
        buttons_container.pack(fill=tk.X, padx=20, pady=(0, 20))
        
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
        
        # Export Button (Secondary)
        self.export_btn = tk.Button(
            buttons_container,
            text="📥 Export Options",
            command=self.advanced_export_csv,
            font=("Segoe UI", 12, "bold"),
            bg=COLOR_CARD_WHITE,
            fg=COLOR_PRIMARY,
            relief=tk.SOLID,
            bd=2,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=COLOR_PRIMARY,
            activeforeground="white"
        )
        self.export_btn.pack(side=tk.LEFT, padx=8)
        
        # Report display card
        report_card = tk.Frame(main_container, bg=COLOR_CARD_WHITE, relief=tk.RAISED, bd=1)
        report_card.pack(fill=tk.BOTH, expand=True)
        
        # Report header
        report_header = tk.Frame(report_card, bg="#f8f9fa", relief=tk.RIDGE, bd=1)
        report_header.pack(fill=tk.X)
        
        self.report_title_label = tk.Label(
            report_header,
            text="📈 Report Data",
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
        
        # Loading indicator (initially hidden)
        self.loading_indicator = tk.Label(
            report_card,
            text="⏳ Generating report...",
            font=("Segoe UI", 14, "normal"),
            fg=COLOR_PRIMARY,
            bg=COLOR_CARD_WHITE
        )
        
        # Generate default report
        self.generate_report()
    
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
        
        # Configure headings to use modern style
        # Note: We'll apply the heading style when columns are added dynamically
        
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
        """Generate the selected report with modern loading feedback"""
        # Show loading state
        self.show_loading_state(True)
        self.app.root.update()
        
        # Simulate processing delay for visual feedback
        self.app.root.after(500, self._process_report)
    
    def _process_report(self):
        """Process report generation after loading delay"""
        report_type = self.report_type_var.get()
        from_date = self.from_date_entry.get()
        to_date = self.to_date_entry.get()
        
        # Update report title based on type
        report_titles = {
            "Daily Sales Summary": "📈 Daily Sales Summary",
            "Sales by Item": "🍽️ Sales by Item",
            "Sales by Category": "📂 Sales by Category"
        }
        self.report_title_label.config(text=report_titles.get(report_type, "📈 Report Data"))
        
        # Clear existing columns and data
        self.report_tree['columns'] = ()
        self.report_tree["show"] = "headings"
        for col in self.report_tree["columns"]:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=100)
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        try:
            if report_type == "Daily Sales Summary":
                self.generate_daily_sales_summary(from_date, to_date)
            elif report_type == "Sales by Item":
                self.generate_sales_by_item_report(from_date, to_date)
            elif report_type == "Sales by Category":
                self.generate_sales_by_category_report(from_date, to_date)
            
            # Hide loading state
            self.show_loading_state(False)
            
            # Show success message
            self.show_message("Success", f"Report generated successfully!", "success")
            
        except Exception as e:
            # Hide loading state
            self.show_loading_state(False)
            # Show error message
            self.show_message("Error", f"Failed to generate report: {str(e)}", "error")
    
    def generate_daily_sales_summary(self, from_date, to_date):
        """Generate daily sales summary report with enhanced formatting"""
        self.report_tree['columns'] = ("date", "orders", "revenue", "avg_order")
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("orders", text="Orders")
        self.report_tree.heading("revenue", text="Revenue")
        self.report_tree.heading("avg_order", text="Avg Order")
        
        self.report_tree.column("date", width=120, anchor=tk.CENTER)
        self.report_tree.column("orders", width=100, anchor=tk.CENTER)
        self.report_tree.column("revenue", width=120, anchor=tk.E)
        self.report_tree.column("avg_order", width=120, anchor=tk.E)
        
        data = self.app.report_model.daily_sales_summary(from_date, to_date)
        
        for row in data:
            date, orders, revenue = row
            avg_order = revenue / orders if orders > 0 else 0
            self.report_tree.insert("", tk.END, values=(
                date, 
                f"{orders:,}", 
                f"₹{revenue:,.2f}",
                f"₹{avg_order:,.2f}"
            ))
    
    def generate_sales_by_item_report(self, from_date, to_date):
        """Generate sales by item report with enhanced formatting"""
        self.report_tree['columns'] = ("item_name", "quantity_sold", "total_revenue", "avg_price")
        self.report_tree.heading("item_name", text="Item Name")
        self.report_tree.heading("quantity_sold", text="Quantity")
        self.report_tree.heading("total_revenue", text="Revenue")
        self.report_tree.heading("avg_price", text="Avg Price")
        
        self.report_tree.column("item_name", width=200, anchor=tk.W)
        self.report_tree.column("quantity_sold", width=100, anchor=tk.CENTER)
        self.report_tree.column("total_revenue", width=120, anchor=tk.E)
        self.report_tree.column("avg_price", width=120, anchor=tk.E)
        
        data = self.app.report_model.sales_by_item(from_date, to_date)
        
        for row in data:
            name, quantity, revenue = row
            avg_price = revenue / quantity if quantity > 0 else 0
            self.report_tree.insert("", tk.END, values=(
                name, 
                f"{quantity:,}", 
                f"₹{revenue:,.2f}",
                f"₹{avg_price:,.2f}"
            ))
    
    def generate_sales_by_category_report(self, from_date, to_date):
        """Generate sales by category report with enhanced formatting"""
        self.report_tree['columns'] = ("category", "quantity_sold", "total_revenue", "percentage")
        self.report_tree.heading("category", text="Category")
        self.report_tree.heading("quantity_sold", text="Quantity")
        self.report_tree.heading("total_revenue", text="Revenue")
        self.report_tree.heading("percentage", text="% of Total")
        
        self.report_tree.column("category", width=200, anchor=tk.W)
        self.report_tree.column("quantity_sold", width=100, anchor=tk.CENTER)
        self.report_tree.column("total_revenue", width=120, anchor=tk.E)
        self.report_tree.column("percentage", width=100, anchor=tk.CENTER)
        
        data = self.app.report_model.sales_by_category(from_date, to_date)
        
        # Calculate total revenue for percentage calculation
        total_revenue = sum(row[2] for row in data) if data else 1
        
        for row in data:
            name, quantity, revenue = row
            percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            self.report_tree.insert("", tk.END, values=(
                name, 
                f"{quantity:,}", 
                f"₹{revenue:,.2f}",
                f"{percentage:.1f}%"
            ))
    
    def export_report_to_csv(self):
        """Export the current report to CSV with modern feedback"""
        if not self.report_tree.get_children():
            self.show_message("Warning", "No report data to export", "warning")
            return
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not file_path:
            return
        
        # Get report data
        headers = [self.report_tree.heading(col)['text'] for col in self.report_tree['columns']]
        data = []
        for child in self.report_tree.get_children():
            data.append(self.report_tree.item(child)['values'])
        
        # Write to CSV
        success = export_to_csv(file_path, headers, data)
        
        if success:
            self.show_message("Success", f"Report exported to {file_path}", "success")
        else:
            self.show_message("Error", "Failed to export report", "error")
    
    @require_license_feature('advanced_reports', "Advanced export features require a Professional or Enterprise license.")
    def advanced_export_csv(self):
        """Show advanced export dialog with modern styling"""
        if not self.report_tree.get_children():
            self.show_message("Warning", "No report data to export", "warning")
            return
        
        # Create export options dialog
        export_dialog = create_export_options_dialog(self.app.root, self.report_type_var.get())
        
        # Add custom export logic for the dialog
        def do_export():
            # Get report data
            headers = [self.report_tree.heading(col)['text'] for col in self.report_tree['columns']]
            data = []
            for child in self.report_tree.get_children():
                data.append(self.report_tree.item(child)['values'])
            
            # Use enhanced export functionality
            success, file_path = export_report_to_csv(
                self.report_tree, 
                self.report_type_var.get()
            )
            
            if success:
                self.show_message("Success", f"Report exported to {file_path}", "success")
                export_dialog.destroy()
            else:
                self.show_message("Error", "Failed to export report", "error")
        
        # Override the dialog's export function
        export_dialog.children['!frame'].children['!frame'].children['!button'].config(command=do_export)