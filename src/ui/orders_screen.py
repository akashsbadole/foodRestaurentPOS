import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from .base_ui import BaseUI
from ..utils.helpers import format_datetime, generate_bill_content

class OrdersScreen(BaseUI):
    """Orders management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup orders management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Orders", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.app.content_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        
        self.order_filter_var = tk.StringVar(value="All")
        ttk.Radiobutton(filter_frame, text="All", variable=self.order_filter_var, 
                       value="All", command=self.filter_orders).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Today", variable=self.order_filter_var, 
                       value="Today", command=self.filter_orders).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="This Week", variable=self.order_filter_var, 
                       value="This Week", command=self.filter_orders).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="This Month", variable=self.order_filter_var, 
                       value="This Month", command=self.filter_orders).pack(side=tk.LEFT, padx=5)
        
        # Search frame
        search_frame = ttk.Frame(self.app.content_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.order_search_entry = ttk.Entry(search_frame)
        self.order_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.order_search_entry.bind("<KeyRelease>", self.search_orders)
        
        # Orders tree
        orders_frame = ttk.Frame(self.app.content_frame)
        orders_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.orders_tree, orders_scrollbar = self.create_treeview(
            orders_frame,
            ("order_number", "date", "type", "table", "total", "status"),
            ("Order No", "Date", "Type", "Table", "Total", "Status"),
            (120, 150, 80, 80, 100, 100)
        )
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.app.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("View Details", self.view_order_details),
            ("Print Bill", self.print_bill),
            ("Refresh", self.refresh_orders)
        ])
        
        # Load orders
        self.load_orders()
    
    def filter_orders(self):
        """Filter orders based on selected filter"""
        self.load_orders()
    
    def search_orders(self, event=None):
        """Search orders"""
        self.load_orders()
    
    def load_orders(self):
        """Load orders from database"""
        filter_value = self.order_filter_var.get()
        search_term = self.order_search_entry.get()
        
        orders = self.app.order_model.get_orders(filter_value, search_term)
        
        # Clear tree
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        
        # Add orders to tree
        for order in orders:
            order_id, order_number, created_at, order_type, table_number, total, status, customer_name = order
            
            # Format date
            date_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%d-%m-%Y %H:%M')
            
            # Format table/customer
            if order_type == "Dine-in":
                table_customer = table_number or "N/A"
            else:  # Takeaway
                table_customer = customer_name or "N/A"
            
            self.orders_tree.insert("", tk.END, values=(
                order_number,
                formatted_date,
                order_type,
                table_customer,
                f"₹{total:.2f}",
                status
            ), tags=(order_id,))
    
    def view_order_details(self):
        """View details of selected order"""
        selection = self.orders_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an order to view details", "warning")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Create order details window
        details_window = tk.Toplevel(self.app.root)
        details_window.title("Order Details")
        details_window.geometry("600x500")
        
        # Get order details
        order_details = self.app.order_model.get_details(order_id)
        if not order_details:
            return
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, discount, total, created_at, status = order_details
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == table_id:
                    table_number = table[1]
                    break
        
        # Get order items
        items = self.app.order_model.get_items(order_id)
        
        # Get payment details
        payments = self.app.order_model.get_payments(order_id)
        
        # Create details frame
        details_frame = ttk.Frame(details_window, padding="20")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Order info
        info_frame = ttk.LabelFrame(details_frame, text="Order Information", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text=f"Order Number: {order_number}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Date: {created_at}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Type: {order_type}").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        if order_type == "Dine-in" and table_number:
            ttk.Label(info_frame, text=f"Table: {table_number}").grid(row=3, column=0, sticky=tk.W, pady=2)
        elif order_type == "Takeaway" and customer_name:
            ttk.Label(info_frame, text=f"Customer: {customer_name}").grid(row=3, column=0, sticky=tk.W, pady=2)
            if customer_mobile:
                ttk.Label(info_frame, text=f"Mobile: {customer_mobile}").grid(row=4, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text=f"Status: {status}").grid(row=5, column=0, sticky=tk.W, pady=2)
        
        # Order items
        items_frame = ttk.LabelFrame(details_frame, text="Order Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        items_tree, items_scrollbar = self.create_treeview(
            items_frame,
            ("name", "quantity", "price", "total", "status"),
            ("Item", "Quantity", "Price", "Total", "Status"),
            (150, 80, 80, 80, 80)
        )
        items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add items to tree
        for item in items:
            name, quantity, price, item_total, item_status = item
            items_tree.insert("", tk.END, values=(
                name,
                quantity,
                f"₹{price:.2f}",
                f"₹{item_total:.2f}",
                item_status
            ))
        
        # Order summary
        summary_frame = ttk.LabelFrame(details_frame, text="Order Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=10)
        
        tax_rate = float(self.app.settings.get('tax_rate', 5))
        ttk.Label(summary_frame, text=f"Subtotal: ₹{subtotal:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Tax ({tax_rate}%): ₹{tax:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Discount: ₹{discount:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Total: ₹{total:.2f}", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        
        # Payment details
        if payments:
            payment_frame = ttk.LabelFrame(details_frame, text="Payment Details", padding=10)
            payment_frame.pack(fill=tk.X, pady=10)
            
            for payment in payments:
                payment_mode, amount, payment_date = payment
                ttk.Label(payment_frame, text=f"{payment_mode}: ₹{amount:.2f} ({payment_date})").pack(anchor=tk.W, pady=2)
    
    def print_bill(self):
        """Print bill for selected order"""
        selection = self.orders_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an order to print bill", "warning")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Generate bill
        self.generate_bill(order_id)
    
    def generate_bill(self, order_id):
        """Generate bill for the order"""
        # Get order details
        order_details = self.app.order_model.get_details(order_id)
        if not order_details:
            return
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, discount, total, created_at, status = order_details
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == table_id:
                    table_number = table[1]
                    break
        
        # Get order items
        items = self.app.order_model.get_items(order_id)
        
        # Create bill content
        bill_content = generate_bill_content(
            self.app.settings, order_number, created_at, order_type, table_number,
            customer_name, customer_mobile, items, subtotal, tax, discount, total
        )
        
        # Save bill to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"Bill_{order_number}.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bill_content)
            self.show_message("Bill Saved", f"Bill saved to {file_path}", "info")
    
    def refresh_orders(self):
        """Refresh orders list"""
        self.load_orders()
