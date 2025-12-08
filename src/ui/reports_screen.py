import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from .base_ui import BaseUI
from utils.helpers import export_to_csv, export_report_to_csv, create_export_options_dialog

class ReportsScreen(BaseUI):
    """Reports screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup reports UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Reports", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Report type selection
        report_type_frame = ttk.Frame(self.app.content_frame)
        report_type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(report_type_frame, text="Select Report Type:").pack(side=tk.LEFT, padx=5)
        self.report_type_var = tk.StringVar(value="Daily Sales Summary")
        report_type_combo = ttk.Combobox(report_type_frame, textvariable=self.report_type_var, 
                                        values=["Daily Sales Summary", "Sales by Item", "Sales by Category"], 
                                        state="readonly", width=30)
        report_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Date range frame
        date_range_frame = ttk.Frame(self.app.content_frame)
        date_range_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_range_frame, text="From:").pack(side=tk.LEFT, padx=5)
        self.from_date_entry = ttk.Entry(date_range_frame, width=15)
        self.from_date_entry.pack(side=tk.LEFT, padx=5)
        self.from_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(date_range_frame, text="To:").pack(side=tk.LEFT, padx=5)
        self.to_date_entry = ttk.Entry(date_range_frame, width=15)
        self.to_date_entry.pack(side=tk.LEFT, padx=5)
        self.to_date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Buttons
        buttons_frame = ttk.Frame(self.app.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("Generate Report", self.generate_report),
            ("Advanced Export", self.advanced_export_csv)
        ])
        
        # Report display
        report_frame = ttk.Frame(self.app.content_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.report_tree, report_scrollbar = self.create_treeview(report_frame, (), (), ())
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Generate default report
        self.generate_report()

    def generate_report(self):
        """Generate the selected report"""
        report_type = self.report_type_var.get()
        from_date = self.from_date_entry.get()
        to_date = self.to_date_entry.get()
        
        # Clear existing columns and data
        self.report_tree['columns'] = ()
        self.report_tree["show"] = "headings"
        for col in self.report_tree["columns"]:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=100)
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)
        
        if report_type == "Daily Sales Summary":
            self.generate_daily_sales_summary(from_date, to_date)
        elif report_type == "Sales by Item":
            self.generate_sales_by_item_report(from_date, to_date)
        elif report_type == "Sales by Category":
            self.generate_sales_by_category_report(from_date, to_date)

    def generate_daily_sales_summary(self, from_date, to_date):
        """Generate daily sales summary report"""
        self.report_tree['columns'] = ("date", "orders", "revenue")
        self.report_tree.heading("date", text="Date")
        self.report_tree.heading("orders", text="Total Orders")
        self.report_tree.heading("revenue", text="Total Revenue")
        
        self.report_tree.column("date", width=150)
        self.report_tree.column("orders", width=150)
        self.report_tree.column("revenue", width=150)
        
        data = self.app.report_model.daily_sales_summary(from_date, to_date)
        
        for row in data:
            date, orders, revenue = row
            self.report_tree.insert("", tk.END, values=(date, orders, f"₹{revenue:.2f}"))

    def generate_sales_by_item_report(self, from_date, to_date):
        """Generate sales by item report"""
        self.report_tree['columns'] = ("item_name", "quantity_sold", "total_revenue")
        self.report_tree.heading("item_name", text="Item Name")
        self.report_tree.heading("quantity_sold", text="Quantity Sold")
        self.report_tree.heading("total_revenue", text="Total Revenue")
        
        self.report_tree.column("item_name", width=200)
        self.report_tree.column("quantity_sold", width=150)
        self.report_tree.column("total_revenue", width=150)
        
        data = self.app.report_model.sales_by_item(from_date, to_date)
        
        for row in data:
            name, quantity, revenue = row
            self.report_tree.insert("", tk.END, values=(name, quantity, f"₹{revenue:.2f}"))

    def generate_sales_by_category_report(self, from_date, to_date):
        """Generate sales by category report"""
        self.report_tree['columns'] = ("category", "quantity_sold", "total_revenue")
        self.report_tree.heading("category", text="Category")
        self.report_tree.heading("quantity_sold", text="Quantity Sold")
        self.report_tree.heading("total_revenue", text="Total Revenue")
        
        self.report_tree.column("category", width=200)
        self.report_tree.column("quantity_sold", width=150)
        self.report_tree.column("total_revenue", width=150)
        
        data = self.app.report_model.sales_by_category(from_date, to_date)
        
        for row in data:
            name, quantity, revenue = row
            self.report_tree.insert("", tk.END, values=(name, quantity, f"₹{revenue:.2f}"))

    def export_report_to_csv(self):
        """Export the current report to CSV"""
        if not self.report_tree.get_children():
            self.show_message("Warning", "No report data to export", "warning")
            return
        
        # Ask for file location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="report.csv"
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
            self.show_message("Success", f"Report exported to {file_path}", "info")
        else:
            self.show_message("Error", "Failed to export report", "error")
    
    def advanced_export_csv(self):
        """Show advanced export dialog"""
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
                self.show_message("Success", f"Report exported to {file_path}", "info")
                export_dialog.destroy()
            else:
                self.show_message("Error", "Failed to export report", "error")
        
        # Override the dialog's export function
        export_dialog.children['!frame'].children['!frame'].children['!button'].config(command=do_export)
