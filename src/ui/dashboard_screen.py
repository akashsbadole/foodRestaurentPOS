import tkinter as tk
from tkinter import ttk, Canvas, Frame
from .base_ui import BaseUI
from utils.helpers import format_currency

class DashboardScreen(BaseUI):
    """Dashboard screen UI component"""
    
    # Design system colors
    COLORS = {
        'primary': '#3498db',
        'primary_dark': '#2c3e50',
        'primary_light': '#2980b9',
        'secondary': '#7f8c8d',
        'secondary_light': '#95a5a6',
        'background': '#f0f0f0',
        'card': '#ffffff',
        'success': '#27ae60',
        'success_light': '#ccffcc',
        'warning': '#f39c12',
        'warning_light': '#ffffcc',
        'error': '#e74c3c',
        'error_light': '#ffcccc',
        'info': '#3498db',
        'text_primary': '#2c3e50',
        'text_secondary': '#7f8c8d',
        'text_disabled': '#bdc3c7',
        'border_light': '#ecf0f1',
        'border_medium': '#bdc3c7',
        'shadow': '#d0d0d0'
    }
    
    # Typography
    FONTS = {
        'h1': ('Segoe UI', 24, 'bold'),
        'h2': ('Segoe UI', 18, 'bold'),
        'h3': ('Segoe UI', 16, 'bold'),
        'h4': ('Segoe UI', 14, 'normal'),
        'body_large': ('Segoe UI', 14, 'normal'),
        'body_normal': ('Segoe UI', 12, 'normal'),
        'body_small': ('Segoe UI', 10, 'normal'),
        'button': ('Segoe UI', 12, 'bold'),
        'stat_value': ('Segoe UI', 20, 'bold'),
        'stat_label': ('Segoe UI', 12, 'normal')
    }
    
    # Spacing
    SPACING = {
        'xs': 4,
        's': 8,
        'm': 16,
        'l': 24,
        'xl': 32,
        'xxl': 48
    }
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.content_frame = None
    
    def show(self, content_frame):
        """Display dashboard"""
        self.content_frame = content_frame
        self.clear_frame(content_frame)
        
        # Set background color - check if it's a tk.Frame or ttk.Frame
        try:
            content_frame.configure(bg=self.COLORS['background'])
        except tk.TclError:
            # If it's a ttk.Frame, use style configuration
            style = ttk.Style()
            style.configure("Dashboard.TFrame", background=self.COLORS['background'])
            content_frame.configure(style="Dashboard.TFrame")
        
        # Set up dashboard shortcuts
        if hasattr(self.app, 'keyboard_handler'):
            self.app.keyboard_handler.setup_dashboard_shortcuts()
        
        # Title with modern styling
        title_label = tk.Label(content_frame, text="Dashboard", 
                              font=self.FONTS['h1'], 
                              fg=self.COLORS['text_primary'],
                              bg=self.COLORS['background'])
        title_label.pack(anchor=tk.W, padx=self.SPACING['xl'], pady=self.SPACING['m'])
        
        # Get today's stats
        stats = self.app.report_model.get_dashboard_stats()
        
        # Create main stats frame with proper spacing
        main_stats_frame = Frame(content_frame, bg=self.COLORS['background'])
        main_stats_frame.pack(fill=tk.X, padx=self.SPACING['xl'], pady=self.SPACING['s'])
        
        # Modern stat cards
        self.create_stat_card(main_stats_frame, 0, 0, "Today's Sales", 
                            f"{self.app.settings.get('currency_symbol', '₹')}{stats['today_sales']:.2f}",
                            self.COLORS['primary'], "💰")
        
        self.create_stat_card(main_stats_frame, 0, 1, "Total Orders", 
                            str(stats['total_orders']),
                            self.COLORS['success'], "📋")
        
        self.create_stat_card(main_stats_frame, 0, 2, "Items Sold", 
                            str(stats['items_sold']),
                            self.COLORS['warning'], "📦")
        
        self.create_stat_card(main_stats_frame, 0, 3, "Occupied Tables", 
                            str(stats['occupied_tables']),
                            self.COLORS['error'], "🪑")
        
        # Configure grid weights
        for i in range(4):
            main_stats_frame.columnconfigure(i, weight=1)
        
        # Additional info section with proper spacing
        info_frame = Frame(content_frame, bg=self.COLORS['background'])
        info_frame.pack(fill=tk.BOTH, expand=True, padx=self.SPACING['xl'], pady=self.SPACING['l'])
        
        # Left column - Recent Orders
        recent_container = Frame(info_frame, bg=self.COLORS['background'])
        recent_container.grid(row=0, column=0, padx=self.SPACING['s'], pady=self.SPACING['s'], 
                           sticky=tk.W+tk.E+tk.N+tk.S)
        
        self.create_card_header(recent_container, "Recent Orders")
        recent_content = Frame(recent_container, bg=self.COLORS['card'], relief=tk.RAISED, bd=1)
        recent_content.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.create_recent_orders_list(recent_content, stats['recent_orders'])
        
        # Right column - Top Items & Quick Actions
        right_container = Frame(info_frame, bg=self.COLORS['background'])
        right_container.grid(row=0, column=1, padx=self.SPACING['s'], pady=self.SPACING['s'], 
                          sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Top Selling Items
        self.create_card_header(right_container, "Top Selling Items")
        top_items_content = Frame(right_container, bg=self.COLORS['card'], relief=tk.RAISED, bd=1)
        top_items_content.pack(fill=tk.BOTH, expand=True, pady=(0, self.SPACING['m']))
        self.create_top_items_list(top_items_content, stats['top_items'])
        
        # Quick access buttons
        self.create_card_header(right_container, "Quick Actions")
        buttons_content = Frame(right_container, bg=self.COLORS['card'], relief=tk.RAISED, bd=1)
        buttons_content.pack(fill=tk.X)
        self.create_quick_access_buttons(buttons_content)
        
        # Configure grid weights for responsive layout
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
    
    def create_card_header(self, parent, title):
        """Create a card header with title"""
        header_frame = Frame(parent, bg=self.COLORS['card'], relief=tk.RAISED, bd=1)
        header_frame.pack(fill=tk.X, pady=(0, self.SPACING['s']))
        
        title_label = tk.Label(header_frame, text=title, font=self.FONTS['h3'], 
                             fg=self.COLORS['text_primary'], bg=self.COLORS['card'])
        title_label.pack(anchor=tk.W, padx=self.SPACING['m'], pady=self.SPACING['m'])
        
        # Separator line
        separator = Frame(header_frame, height=1, bg=self.COLORS['border_light'])
        separator.pack(fill=tk.X, padx=self.SPACING['m'])
    
    def create_stat_card(self, parent, row, col, title, value, color, icon):
        """Create a modern stat card with shadow and visual hierarchy"""
        # Card container with shadow effect
        card_frame = Frame(parent, bg=self.COLORS['card'], relief=tk.RAISED, bd=1)
        card_frame.grid(row=row, column=col, padx=self.SPACING['s'], pady=self.SPACING['s'], 
                        sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Card content with proper spacing
        content_frame = Frame(card_frame, bg=self.COLORS['card'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=self.SPACING['m'], pady=self.SPACING['m'])
        
        # Accent border at top
        accent_frame = Frame(card_frame, bg=color, height=4)
        accent_frame.pack(fill=tk.X)
        
        # Icon and title row
        title_row = Frame(content_frame, bg=self.COLORS['card'])
        title_row.pack(fill=tk.X, pady=(self.SPACING['s'], 0))
        
        icon_label = tk.Label(title_row, text=icon, font=('Segoe UI', 16), 
                            fg=color, bg=self.COLORS['card'])
        icon_label.pack(side=tk.LEFT)
        
        title_label = tk.Label(title_row, text=title, font=self.FONTS['stat_label'], 
                             fg=self.COLORS['text_secondary'], bg=self.COLORS['card'])
        title_label.pack(side=tk.LEFT, padx=self.SPACING['s'])
        
        # Value
        value_label = tk.Label(content_frame, text=value, font=self.FONTS['stat_value'], 
                             fg=self.COLORS['text_primary'], bg=self.COLORS['card'])
        value_label.pack(anchor=tk.W, pady=(self.SPACING['m'], 0))
        
        # Bind hover effects
        def on_enter(e):
            card_frame.configure(bg=self.COLORS['background'])
            content_frame.configure(bg=self.COLORS['background'])
            title_row.configure(bg=self.COLORS['background'])
            icon_label.configure(bg=self.COLORS['background'])
            title_label.configure(bg=self.COLORS['background'])
            value_label.configure(bg=self.COLORS['background'])
        
        def on_leave(e):
            card_frame.configure(bg=self.COLORS['card'])
            content_frame.configure(bg=self.COLORS['card'])
            title_row.configure(bg=self.COLORS['card'])
            icon_label.configure(bg=self.COLORS['card'])
            title_label.configure(bg=self.COLORS['card'])
            value_label.configure(bg=self.COLORS['card'])
        
        card_frame.bind('<Enter>', on_enter)
        content_frame.bind('<Enter>', on_enter)
        title_row.bind('<Enter>', on_enter)
        icon_label.bind('<Enter>', on_enter)
        title_label.bind('<Enter>', on_enter)
        value_label.bind('<Enter>', on_enter)
        
        card_frame.bind('<Leave>', on_leave)
        content_frame.bind('<Leave>', on_leave)
        title_row.bind('<Leave>', on_leave)
        icon_label.bind('<Leave>', on_leave)
        title_label.bind('<Leave>', on_leave)
        value_label.bind('<Leave>', on_leave)
    
    def create_recent_orders_list(self, parent, recent_orders):
        """Create modern recent orders list with enhanced styling"""
        parent.configure(bg=self.COLORS['card'])
        
        if not recent_orders:
            no_data_label = tk.Label(parent, text="No recent orders", 
                                    font=self.FONTS['body_normal'],
                                    fg=self.COLORS['text_secondary'],
                                    bg=self.COLORS['card'])
            no_data_label.pack(pady=self.SPACING['l'])
            return
        
        # Create modern treeview with custom styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure treeview styling
        style.configure("Modern.Treeview",
                       background=self.COLORS['card'],
                       foreground=self.COLORS['text_primary'],
                       fieldbackground=self.COLORS['card'],
                       borderwidth=0,
                       font=self.FONTS['body_normal'])
        
        style.configure("Modern.Treeview.Heading",
                       background=self.COLORS['background'],
                       foreground=self.COLORS['text_primary'],
                       fieldbackground=self.COLORS['background'],
                       font=self.FONTS['body_small'],
                       relief=tk.FLAT)
        
        style.map("Modern.Treeview",
                 background=[('selected', self.COLORS['primary_light'])],
                 foreground=[('selected', self.COLORS['card'])])
        
        # Create treeview with modern styling
        columns = ("order_number", "total", "time", "type")
        recent_tree = ttk.Treeview(parent, columns=columns, show="headings", 
                                  height=6, style="Modern.Treeview")
        
        # Configure headings
        recent_tree.heading("order_number", text="Order #")
        recent_tree.heading("total", text="Total")
        recent_tree.heading("time", text="Time")
        recent_tree.heading("type", text="Type")
        
        # Configure columns with proper spacing
        recent_tree.column("order_number", width=100, minwidth=80)
        recent_tree.column("total", width=80, minwidth=60)
        recent_tree.column("time", width=80, minwidth=60)
        recent_tree.column("type", width=80, minwidth=60)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=recent_tree.yview)
        recent_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        recent_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.SPACING['m'], pady=self.SPACING['m'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=self.SPACING['m'])
        
        # Add recent orders with enhanced formatting
        for order in recent_orders:
            order_number, total, created_at, order_type = order
            
            # Format time
            from utils.helpers import format_datetime
            time_str = format_datetime(created_at, '%Y-%m-%d %H:%M:%S', '%H:%M')
            
            # Format total with currency
            currency_symbol = self.app.settings.get('currency_symbol', '₹')
            total_str = f"{currency_symbol}{total:.2f}"
            
            # Insert with tags for styling
            item = recent_tree.insert("", tk.END, values=(order_number, total_str, time_str, order_type))
            
            # Alternate row colors
            if recent_tree.get_children().index(item) % 2 == 0:
                recent_tree.set(item, "order_number", order_number)
    
    def create_top_items_list(self, parent, top_items):
        """Create modern top selling items list with enhanced styling"""
        parent.configure(bg=self.COLORS['card'])
        
        if not top_items:
            no_data_label = tk.Label(parent, text="No sales data", 
                                    font=self.FONTS['body_normal'],
                                    fg=self.COLORS['text_secondary'],
                                    bg=self.COLORS['card'])
            no_data_label.pack(pady=self.SPACING['l'])
            return
        
        # Create modern treeview with custom styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure treeview styling
        style.configure("Modern.Treeview",
                       background=self.COLORS['card'],
                       foreground=self.COLORS['text_primary'],
                       fieldbackground=self.COLORS['card'],
                       borderwidth=0,
                       font=self.FONTS['body_normal'])
        
        style.configure("Modern.Treeview.Heading",
                       background=self.COLORS['background'],
                       foreground=self.COLORS['text_primary'],
                       fieldbackground=self.COLORS['background'],
                       font=self.FONTS['body_small'],
                       relief=tk.FLAT)
        
        style.map("Modern.Treeview",
                 background=[('selected', self.COLORS['primary_light'])],
                 foreground=[('selected', self.COLORS['card'])])
        
        # Create treeview with modern styling
        columns = ("item_name", "quantity", "revenue")
        top_tree = ttk.Treeview(parent, columns=columns, show="headings", 
                               height=6, style="Modern.Treeview")
        
        # Configure headings
        top_tree.heading("item_name", text="Item Name")
        top_tree.heading("quantity", text="Quantity")
        top_tree.heading("revenue", text="Revenue")
        
        # Configure columns with proper spacing
        top_tree.column("item_name", width=150, minwidth=120)
        top_tree.column("quantity", width=80, minwidth=60)
        top_tree.column("revenue", width=80, minwidth=60)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=top_tree.yview)
        top_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        top_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.SPACING['m'], pady=self.SPACING['m'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=self.SPACING['m'])
        
        # Add top items with enhanced formatting
        for item in top_items:
            name, quantity, revenue = item
            
            # Truncate long names with ellipsis
            display_name = name[:20] + "..." if len(name) > 20 else name
            
            # Format revenue with currency
            currency_symbol = self.app.settings.get('currency_symbol', '₹')
            revenue_str = f"{currency_symbol}{revenue:.2f}"
            
            # Insert with proper formatting
            top_tree.insert("", tk.END, values=(display_name, quantity, revenue_str))
    
    def create_quick_access_buttons(self, parent):
        """Create modern quick access buttons with hover effects"""
        parent.configure(bg=self.COLORS['card'])
        
        buttons = [
            ("New Order (1)", self.app.show_new_order, self.COLORS['primary']),
            ("View Orders (2)", self.app.show_orders, self.COLORS['secondary']),
            ("Menu Management (3)", self.app.show_menu, self.COLORS['success']),
            ("Tables (4)", self.app.show_tables, self.COLORS['warning']),
            ("Inventory (5)", self.app.show_inventory, self.COLORS['error']),
            ("Reports (6)", self.app.show_reports, self.COLORS['info'])
        ]
        
        # Create button grid with proper spacing
        button_frame = Frame(parent, bg=self.COLORS['card'])
        button_frame.pack(fill=tk.BOTH, expand=True, padx=self.SPACING['m'], pady=self.SPACING['m'])
        
        for i, (text, command, color) in enumerate(buttons):
            row = i // 3
            col = i % 3
            
            # Create modern button with custom styling
            button = tk.Button(button_frame, text=text, command=command,
                             font=self.FONTS['button'],
                             bg=color, fg=self.COLORS['card'],
                             activebackground=self.COLORS['primary_dark'],
                             activeforeground=self.COLORS['card'],
                             relief=tk.FLAT, bd=0,
                             padx=self.SPACING['m'], pady=self.SPACING['s'],
                             cursor="hand2")
            button.grid(row=row, column=col, padx=self.SPACING['s'], 
                       pady=self.SPACING['s'], sticky=tk.W+tk.E)
            
            # Add hover effects
            def on_enter(e, btn=button, hover_color=color):
                btn.configure(bg=self.COLORS['primary_dark'])
            
            def on_leave(e, btn=button, normal_color=color):
                btn.configure(bg=normal_color)
            
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
        
        # Configure column weights for responsive layout
        for col in range(3):
            button_frame.columnconfigure(col, weight=1)