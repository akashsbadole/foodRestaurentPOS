import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from utils.helpers import format_currency

class DashboardScreen(BaseUI):
    """Dashboard screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.content_frame = None
    
    def show(self, content_frame):
        """Display dashboard"""
        self.content_frame = content_frame
        self.clear_frame(content_frame)
        
        # Set up dashboard shortcuts
        if hasattr(self.app, 'keyboard_handler'):
            self.app.keyboard_handler.setup_dashboard_shortcuts()
        
        # Title
        title_label = ttk.Label(content_frame, text="Dashboard", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Get today's stats
        stats = self.app.report_model.get_dashboard_stats()
        
        # Create main stats frame
        main_stats_frame = ttk.Frame(content_frame)
        main_stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Today's Sales
        sales_frame = ttk.LabelFrame(main_stats_frame, text="Today's Sales", padding=15)
        sales_frame.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W+tk.E)
        
        currency_symbol = self.app.settings.get('currency_symbol', '₹')
        sales_label = ttk.Label(sales_frame, 
                              text=f"{currency_symbol}{stats['today_sales']:.2f}",
                              font=('Arial', 20, 'bold'))
        sales_label.pack()
        
        # Total Orders
        orders_frame = ttk.LabelFrame(main_stats_frame, text="Total Orders", padding=15)
        orders_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W+tk.E)
        
        orders_label = ttk.Label(orders_frame, text=str(stats['total_orders']), 
                               font=('Arial', 20, 'bold'))
        orders_label.pack()
        
        # Items Sold
        items_frame = ttk.LabelFrame(main_stats_frame, text="Items Sold", padding=15)
        items_frame.grid(row=0, column=2, padx=10, pady=5, sticky=tk.W+tk.E)
        
        items_label = ttk.Label(items_frame, text=str(stats['items_sold']), 
                             font=('Arial', 20, 'bold'))
        items_label.pack()
        
        # Occupied Tables
        tables_frame = ttk.LabelFrame(main_stats_frame, text="Occupied Tables", padding=15)
        tables_frame.grid(row=0, column=3, padx=10, pady=5, sticky=tk.W+tk.E)
        
        tables_label = ttk.Label(tables_frame, text=str(stats['occupied_tables']), 
                              font=('Arial', 20, 'bold'))
        tables_label.pack()
        
        # Configure grid weights
        main_stats_frame.columnconfigure(0, weight=1)
        main_stats_frame.columnconfigure(1, weight=1)
        main_stats_frame.columnconfigure(2, weight=1)
        main_stats_frame.columnconfigure(3, weight=1)
        
        # Additional info section
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left column - Recent Orders
        recent_frame = ttk.LabelFrame(info_frame, text="Recent Orders", padding=10)
        recent_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        self.create_recent_orders_list(recent_frame, stats['recent_orders'])
        
        # Right column - Top Items & Quick Actions
        right_frame = ttk.Frame(info_frame)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Top Selling Items
        top_items_frame = ttk.LabelFrame(right_frame, text="Top Selling Items", padding=10)
        top_items_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_top_items_list(top_items_frame, stats['top_items'])
        
        # Quick access buttons
        buttons_frame = ttk.LabelFrame(right_frame, text="Quick Actions", padding=10)
        buttons_frame.pack(fill=tk.X)
        
        self.create_quick_access_buttons(buttons_frame)
    
    def create_recent_orders_list(self, parent, recent_orders):
        """Create recent orders list"""
        if not recent_orders:
            ttk.Label(parent, text="No recent orders", foreground="gray").pack()
            return
        
        # Create treeview for recent orders
        columns = ("order_number", "total", "time", "type")
        recent_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        recent_tree.heading("order_number", text="Order #")
        recent_tree.heading("total", text="Total")
        recent_tree.heading("time", text="Time")
        recent_tree.heading("type", text="Type")
        
        recent_tree.column("order_number", width=100)
        recent_tree.column("total", width=80)
        recent_tree.column("time", width=80)
        recent_tree.column("type", width=80)
        
        recent_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add recent orders
        for order in recent_orders:
            order_number, total, created_at, order_type = order
            
            # Format time
            from utils.helpers import format_datetime
            time_str = format_datetime(created_at, '%Y-%m-%d %H:%M:%S', '%H:%M')
            
            recent_tree.insert("", tk.END, values=(
                order_number,
                f"{self.app.settings.get('currency_symbol', '₹')}{total:.2f}",
                time_str,
                order_type
            ))
    
    def create_top_items_list(self, parent, top_items):
        """Create top selling items list"""
        if not top_items:
            ttk.Label(parent, text="No sales data", foreground="gray").pack()
            return
        
        # Create treeview for top items
        columns = ("item_name", "quantity", "revenue")
        top_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        top_tree.heading("item_name", text="Item Name")
        top_tree.heading("quantity", text="Quantity")
        top_tree.heading("revenue", text="Revenue")
        
        top_tree.column("item_name", width=150)
        top_tree.column("quantity", width=80)
        top_tree.column("revenue", width=80)
        
        top_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add top items
        for item in top_items:
            name, quantity, revenue = item
            top_tree.insert("", tk.END, values=(
                name[:20] + "..." if len(name) > 20 else name,  # Truncate long names
                quantity,
                f"{self.app.settings.get('currency_symbol', '₹')}{revenue:.2f}"
            ))
    
    def create_quick_access_buttons(self, parent):
        """Create quick access buttons with keyboard shortcuts"""
        buttons = [
            ("New Order (1)", self.app.show_new_order),
            ("View Orders (2)", self.app.show_orders),
            ("Menu Management (3)", self.app.show_menu),
            ("Tables (4)", self.app.show_tables),
            ("Inventory (5)", self.app.show_inventory),
            ("Reports (6)", self.app.show_reports)
        ]
        
        # Create 2 rows of buttons
        for i, (text, command) in enumerate(buttons):
            row = i // 3
            col = i % 3
            button = ttk.Button(parent, text=text, command=command)
            button.grid(row=row, column=col, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Configure column weights
        for col in range(3):
            parent.columnconfigure(col, weight=1)
