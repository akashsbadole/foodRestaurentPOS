import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from ..utils.helpers import format_currency

class DashboardScreen(BaseUI):
    """Dashboard screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.content_frame = None
    
    def show(self, content_frame):
        """Display the dashboard"""
        self.content_frame = content_frame
        self.clear_frame(content_frame)
        
        # Set up dashboard shortcuts
        if hasattr(self.app, 'keyboard_handler'):
            self.app.keyboard_handler.setup_dashboard_shortcuts()
        
        # Title
        title_label = ttk.Label(content_frame, text="Dashboard", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Get today's stats
        stats = self.app.settings_model.get_dashboard_stats()
        
        # Create stats frame
        stats_frame = ttk.Frame(content_frame)
        stats_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Today's Sales
        sales_frame = ttk.LabelFrame(stats_frame, text="Today's Sales", padding=20)
        sales_frame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W+tk.E)
        
        currency_symbol = self.app.settings.get('currency_symbol', '₹')
        sales_label = ttk.Label(sales_frame, 
                              text=f"{currency_symbol}{stats['today_sales']:.2f}",
                              font=('Arial', 24, 'bold'))
        sales_label.pack()
        
        # Total Orders
        orders_frame = ttk.LabelFrame(stats_frame, text="Total Orders", padding=20)
        orders_frame.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        
        orders_label = ttk.Label(orders_frame, text=str(stats['total_orders']), 
                               font=('Arial', 24, 'bold'))
        orders_label.pack()
        
        # Items Sold
        items_frame = ttk.LabelFrame(stats_frame, text="Items Sold", padding=20)
        items_frame.grid(row=0, column=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        items_label = ttk.Label(items_frame, text=str(stats['items_sold']), 
                             font=('Arial', 24, 'bold'))
        items_label.pack()
        
        # Configure grid weights
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        
        # Quick access buttons with keyboard shortcuts hints
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Create buttons with shortcuts in labels
        self.create_quick_access_buttons(buttons_frame)
    
    def create_quick_access_buttons(self, parent):
        """Create quick access buttons with keyboard shortcuts"""
        buttons = [
            ("New Order (1)", self.app.show_new_order),
            ("View Orders (2)", self.app.show_orders),
            ("Menu Management (3)", self.app.show_menu)
        ]
        
        for i, (text, command) in enumerate(buttons):
            button = ttk.Button(parent, text=text, command=command)
            button.grid(row=0, column=i, padx=5, pady=5)
