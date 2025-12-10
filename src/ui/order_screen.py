import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from .base_ui import BaseUI
from .export_dialog import ExportDialog
from src.utils.helpers import generate_order_number, format_currency
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.utils.pdf_exporter import PDFExporter
from src.utils.text_exporter import TextExporter
from src.utils.encryption import get_encryption_manager
from src.managers.order_manager import OrderManager
import os
import subprocess
# ReportLab imports for PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ReportLab not available: {e}")
    REPORTLAB_AVAILABLE = False
    # Fallback imports for compatibility
    A4 = None
    mm = None
    SimpleDocTemplate = None

class OrderScreen(BaseUI):
    """New Order Screen with split-screen layout for creating and managing multiple orders"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.root = root
        self.app = app
        self.db = app.db  # Add database reference
        
        # Initialize encryption manager
        self.encryption_manager = get_encryption_manager()
        
        # Initialize order manager
        self.order_manager = OrderManager()
        
        # Order data
        self.order_items = []
        self.current_table_id = None
        self.current_customer = ""
        self.current_customer_mobile = ""
        self.order_type = tk.StringVar(value="Dine-in")
        self.subtotal = 0.0
        self.tax = 0.0
        self.discount = 0.0
        self.total = 0.0
        
        # Payment options
        self.payment_methods = ["Cash", "Card", "UPI", "Wallet", "Credit"]
        
        # Export functionality
        if REPORTLAB_AVAILABLE:
            self.pdf_exporter = PDFExporter({
                'name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
                'address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
                'phone': self.app.settings.get('restaurant_phone', ''),
                'email': self.app.settings.get('restaurant_email', ''),
                'gst_number': self.app.settings.get('gst_number', '')
            })
        else:
            self.pdf_exporter = None
            print("Warning: PDF export functionality disabled due to missing ReportLab")
        self.text_exporter = TextExporter({
            'name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
            'address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
            'phone': self.app.settings.get('restaurant_phone', ''),
            'email': self.app.settings.get('restaurant_email', ''),
            'gst_number': self.app.settings.get('gst_number', '')
        })
        
        # UI components
        self.content_frame = None
        self.order_tree = None
        self.category_combo = None
        self.menu_combo = None
        self.quantity_var = None
        self.table_combo = None
        
        # Tab-based interface components
        self.order_notebook = None
        self.order_frames = {}  # {order_id: frame}
        self.order_trees = {}  # {order_id: tree}
        
        # New layout components
        self.main_frame = None
        self.header_frame = None
        self.left_panel = None
        self.right_panel = None
        self.paned_window = None
        self.tab_bar_frame = None
        self.tabs_container = None
        self.user_frame = None
        
        # Layout constants
        self.HEADER_HEIGHT = 60
        self.LEFT_PANEL_RATIO = 0.6  # 60%
        self.RIGHT_PANEL_RATIO = 0.4  # 40%
        
        # Status buttons
        self.status_buttons = {}
        
        # Browser tabs
        self.browser_tabs = {}
        
    def setup_ui(self):
        """Setup order screen UI with new split-screen layout"""
        # Clear content frame
        if self.app.content_frame:
            for widget in self.app.content_frame.winfo_children():
                widget.destroy()
        else:
            # Create content frame if it doesn't exist
            self.app.content_frame = ttk.Frame(self.app.root)
            self.app.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_frame = self.app.content_frame
        
        # Setup responsive layout
        self.setup_responsive_layout()
        
        # Configure styles for new layout
        self.configure_styles()
        
        # Create split layout
        self.create_split_layout()
        
        # Load initial data
        self.load_initial_data()
        
        # Initialize orders
        self.initialize_orders()
        
    def setup_responsive_layout(self):
        """Setup responsive layout for different screen sizes"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set minimum window size
        min_width, min_height = 1280, 720
        self.root.minsize(min_width, min_height)
        
        # Center window
        x = (screen_width - min_width) // 2
        y = (screen_height - min_height) // 2
        self.root.geometry(f"{min_width}x{min_height}+{x}+{y}")
        
    def configure_styles(self):
        """Configure styles for new layout"""
        style = ttk.Style()
        
        # Tab styles
        style.configure('Tab.TButton',
                     font=('Arial', 9),
                     padding=(8, 4),
                     relief='flat')
        style.configure('ActiveTab.TButton',
                     font=('Arial', 9, 'bold'),
                     padding=(8, 4),
                     relief='flat',
                     background='#0078d7')
        style.configure('CloseTab.TButton',
                     font=('Arial', 8),
                     padding=(2, 2),
                     relief='flat',
                     foreground='#666666')
        
        # Status button styles
        style.configure('ActiveStatus.TButton',
                     font=('Arial', 9, 'bold'),
                     relief='flat',
                     background='#0078d7',
                     foreground='white')
        
        # Accent button style
        style.configure('Accent.TButton',
                     font=('Arial', 9, 'bold'),
                     padding=(8, 4),
                     relief='flat',
                     background='#28a745',
                     foreground='white')
        
    def create_split_layout(self):
        """Create main split-screen layout"""
        # Create main container
        self.main_frame = ttk.Frame(self.content_frame)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Create split panels
        self.paned_window = ttk.PanedWindow(
            self.main_frame, 
            orient=tk.HORIZONTAL
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create panels
        self.create_panels()
        
    def create_header(self):
        """Create top header with tabs and user info"""
        self.header_frame = ttk.Frame(self.main_frame, height=self.HEADER_HEIGHT)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        self.header_frame.pack_propagate(False)  # Prevent height change
        
        # Create left side (tabs)
        self.create_tab_container()
        
        # Create right side (user info)
        # self.create_user_info()
        
    def create_tab_container(self):
        """Create browser-style tab container"""
        # Left side frame
        self.tab_bar_frame = ttk.Frame(self.header_frame)
        self.tab_bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # New Order button
        self.new_order_btn = ttk.Button(
            self.tab_bar_frame,
            text="+ New Order",
            command=self.new_order,
            style='Accent.TButton'
        )
        self.new_order_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Tabs container
        self.tabs_container = ttk.Frame(self.tab_bar_frame)
        self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
    # def create_user_info(self):
    #     """Create user profile section"""
    #     # Right side frame
    #     self.user_frame = ttk.Frame(self.header_frame)
    #     self.user_frame.pack(side=tk.RIGHT, padx=5, pady=5)
        
    #     # User label
    #     username = self.app.current_user.get('username', 'Admin')
    #     role = self.app.current_user.get('role', 'Admin')
    #     self.user_label = ttk.Label(
    #         self.user_frame,
    #         text=f"User: {username} ({role})",
    #         font=('Arial', 10)
    #     )
    #     self.user_label.pack(side=tk.LEFT, padx=(0, 10))
        
    #     # Logout button
    #     self.logout_btn = ttk.Button(
    #         self.user_frame,
    #         text="Logout",
    #         command=self.logout
    #     )
    #     self.logout_btn.pack(side=tk.LEFT)
        
    def create_panels(self):
        """Create left and right panels"""
        # Left panel (60%)
        self.left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_panel, weight=6)
        
        # Right panel (40%)
        self.right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_panel, weight=4)
        
        # Create components in each panel
        self.create_left_panel_components()
        self.create_right_panel_components()
        
    def create_left_panel_components(self):
        """Create all left panel components"""
        # Customer details frame
        self.create_customer_details_frame()
        
        # Item selection frame
        self.create_item_selection_frame()
        
        # Status control frame
        self.create_status_control_frame()
        
    def create_customer_details_frame(self):
        """Create customer details in 2x2 grid layout"""
        self.customer_frame = ttk.LabelFrame(
            self.left_panel, 
            text="Customer Info", 
            padding=10
        )
        self.customer_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Order type (row 0, col 0-1)
        ttk.Label(self.customer_frame, text="Order Type:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        
        self.dine_radio = ttk.Radiobutton(
            self.customer_frame, 
            text="Dine-in", 
            variable=self.order_type, 
            value="Dine-in",
            command=self.on_order_type_changed
        )
        self.dine_radio.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.takeaway_radio = ttk.Radiobutton(
            self.customer_frame, 
            text="Takeaway", 
            variable=self.order_type, 
            value="Takeaway",
            command=self.on_order_type_changed
        )
        self.takeaway_radio.grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Table selection (row 0, col 3)
        ttk.Label(self.customer_frame, text="Table:").grid(
            row=0, column=3, sticky=tk.W, padx=5
        )
        self.table_combo = ttk.Combobox(
            self.customer_frame, 
            width=15, 
            state="readonly"
        )
        self.table_combo.grid(row=0, column=4, padx=5, sticky=tk.W)
        self.table_combo.bind("<<ComboboxSelected>>", self.on_table_changed)
        
        # Customer name (row 1, col 0-2)
        ttk.Label(self.customer_frame, text="Name:").grid(
            row=1, column=0, sticky=tk.W, padx=5
        )
        self.customer_entry = ttk.Entry(self.customer_frame, width=25)
        self.customer_entry.grid(
            row=1, column=1, columnspan=2, 
            padx=5, sticky=tk.W+tk.E
        )
        self.customer_entry.bind("<KeyRelease>", self.on_customer_info_changed)
        
        # Mobile number (row 1, col 3-4)
        ttk.Label(self.customer_frame, text="Mobile:").grid(
            row=1, column=3, sticky=tk.W, padx=5
        )
        self.mobile_entry = ttk.Entry(self.customer_frame, width=15)
        self.mobile_entry.grid(
            row=1, column=4, 
            padx=5, sticky=tk.W+tk.E
        )
        self.mobile_entry.bind("<KeyRelease>", self.on_customer_info_changed)
        
    def create_item_selection_frame(self):
        """Create compact item selection frame"""
        self.item_frame = ttk.LabelFrame(
            self.left_panel,
            text="Add Items",
            padding=10
        )
        self.item_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Row 0: Category | Item | Quantity | Add
        self.category_combo = ttk.Combobox(
            self.item_frame,
            width=20,
            state="readonly"
        )
        self.category_combo.grid(row=0, column=0, padx=5, sticky=tk.W)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_changed)
        
        self.menu_combo = ttk.Combobox(
            self.item_frame,
            width=35,
            state="readonly"
        )
        self.menu_combo.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_spin = ttk.Spinbox(
            self.item_frame,
            from_=1, to=99,
            textvariable=self.quantity_var,
            width=8
        )
        self.quantity_spin.grid(row=0, column=2, padx=5)
        
        self.add_btn = ttk.Button(
            self.item_frame,
            text="ADD",
            command=self.add_item,
            width=10
        )
        self.add_btn.grid(row=0, column=3, padx=5)
        
        # Row 1: Shortcode | Search | Clear | Clear Order
        self.shortcode_var = tk.StringVar()
        self.shortcode_entry = ttk.Entry(
            self.item_frame,
            textvariable=self.shortcode_var,
            width=15
        )
        self.shortcode_entry.grid(
            row=1, column=0,
            padx=5, pady=5, sticky=tk.W
        )
        self.shortcode_entry.bind("<KeyRelease>", self.on_shortcode_changed)
        self.shortcode_entry.bind("<Return>", self.add_item_by_shortcode)
        
        # Add shortcode label
        shortcode_label = ttk.Label(
            self.item_frame,
            text="Shortcode:",
            font=('Arial', 9)
        )
        shortcode_label.grid(
            row=1, column=0,
            padx=5, sticky=tk.W, pady=(5, 0)
        )
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.item_frame,
            textvariable=self.search_var
        )
        self.search_entry.grid(
            row=1, column=1,
            padx=5, pady=5, sticky=tk.W+tk.E
        )
        self.search_entry.bind("<KeyRelease>", self.search_menu_items)
        
        self.clear_search_btn = ttk.Button(
            self.item_frame,
            text="Clear",
            command=self.clear_menu_search
        )
        self.clear_search_btn.grid(row=1, column=2, padx=5, pady=5)
        
        self.clear_order_btn = ttk.Button(
            self.item_frame,
            text="Clear Order",
            command=self.clear_current_order
        )
        self.clear_order_btn.grid(row=1, column=3, padx=5, pady=5)
        
    def create_status_control_frame(self):
        """Create status control strip with clickable buttons"""
        self.status_frame = ttk.LabelFrame(
            self.left_panel, 
            text="Order Status", 
            padding=10
        )
        self.status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status buttons
        self.status_buttons = {}
        status_options = [
            ("new", "New", "#808080"),
            ("in_progress", "In Progress", "#FFA500"),
            ("ready", "Ready", "#008000"),
            ("completed", "Completed", "#0000FF")
        ]
        
        for i, (key, text, color) in enumerate(status_options):
            btn = ttk.Button(
                self.status_frame,
                text=text,
                command=lambda k=key: self.set_order_status(k),
                width=15
            )
            btn.grid(row=0, column=i, padx=5, pady=5)
            self.status_buttons[key] = btn
            
    def create_right_panel_components(self):
        """Create all right panel components"""
        # Active orders frame
        self.create_active_orders_frame()
        
        # Financial breakdown frame
        self.create_financial_breakdown_frame()
        
        # Action buttons frame
        self.create_action_buttons_frame()
        
    def create_active_orders_frame(self):
        """Create active orders treeview"""
        self.orders_frame = ttk.LabelFrame(
            self.right_panel, 
            text="Active Orders", 
            padding=10
        )
        self.orders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview
        self.order_tree = ttk.Treeview(
            self.orders_frame,
            columns=("item", "quantity", "price", "total"),
            show="headings",
            height=8
        )
        
        # Configure columns
        self.order_tree.heading("item", text="Item")
        self.order_tree.heading("quantity", text="Qty")
        self.order_tree.heading("price", text="Price")
        self.order_tree.heading("total", text="Total")
        
        self.order_tree.column("item", width=200)
        self.order_tree.column("quantity", width=60)
        self.order_tree.column("price", width=80)
        self.order_tree.column("total", width=80)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            self.orders_frame, 
            orient=tk.VERTICAL, 
            command=self.order_tree.yview
        )
        self.order_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Info strip
        self.info_label = ttk.Label(
            self.orders_frame,
            text="Items: 0 | Status: New",
            font=('Arial', 9, 'bold')
        )
        self.info_label.pack(fill=tk.X, pady=(5, 0))
        
        # Right click menu
        self.order_tree.bind("<Button-3>", self.show_item_context_menu)
        
    def create_financial_breakdown_frame(self):
        """Create receipt-style financial breakdown"""
        self.financial_frame = ttk.Frame(self.right_panel)
        self.financial_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Right-aligned labels
        self.subtotal_label = ttk.Label(
            self.financial_frame, 
            text="Subtotal:     Rs.0.00", 
            font=('Arial', 10)
        )
        self.subtotal_label.pack(anchor=tk.E, pady=2)
        
        self.cgst_label = ttk.Label(
            self.financial_frame, 
            text="CGST (2.5%):  Rs.0.00", 
            font=('Arial', 9)
        )
        self.cgst_label.pack(anchor=tk.E, pady=1)
        
        self.sgst_label = ttk.Label(
            self.financial_frame, 
            text="SGST (2.5%):  Rs.0.00", 
            font=('Arial', 9)
        )
        self.sgst_label.pack(anchor=tk.E, pady=1)
        
        self.discount_label = ttk.Label(
            self.financial_frame, 
            text="Discount:   - Rs.0.00", 
            font=('Arial', 10)
        )
        self.discount_label.pack(anchor=tk.E, pady=2)
        
        # Separator
        separator = ttk.Separator(self.financial_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)
        
        self.total_label = ttk.Label(
            self.financial_frame, 
            text="TOTAL:        Rs.0.00", 
            font=('Arial', 12, 'bold')
        )
        self.total_label.pack(anchor=tk.E, pady=2)
        
    def create_action_buttons_frame(self):
        """Create action buttons row"""
        self.action_frame = ttk.Frame(self.right_panel)
        self.action_frame.pack(fill=tk.X)
        
        # Discount button
        self.discount_btn = ttk.Button(
            self.action_frame,
            text="Apply Discount",
            command=self.apply_discount,
            width=15
        )
        self.discount_btn.pack(side=tk.LEFT, padx=5)
        
        # Export button
        self.export_btn = ttk.Button(
            self.action_frame,
            text="Export Order",
            command=self.export_order,
            width=15
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Process payment button (emphasized)
        self.payment_btn = ttk.Button(
            self.action_frame,
            text="PROCESS PAYMENT",
            command=self.process_payment,
            width=18,
            style='Accent.TButton'
        )
        self.payment_btn.pack(side=tk.RIGHT, padx=5)
        
    def load_initial_data(self):
        """Load initial data for components"""
        # Load categories
        self.load_categories()
        
        # Load tables
        self.load_tables()
        
        # Setup event handlers
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        """Setup event handlers for components"""
        # Order manager events
        self.order_manager.on_order_switched = self.on_order_switched
        self.order_manager.on_order_updated = self.on_order_updated
        self.order_manager.on_status_changed = self.on_status_changed
        
    def set_order_status(self, status):
        """Set order status with validation"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return
        
        # Validate status transitions
        if status == "completed" and not current_order['items']:
            messagebox.showwarning("Warning", "Cannot complete empty order")
            return
        
        # Update status in order manager
        self.order_manager.update_order_status(
            self.order_manager.current_order_id, 
            status
        )
        
        # Update button appearances
        self.update_status_buttons()
        
        # Refresh displays
        self.refresh_orders_list()
        
    def update_status_buttons(self):
        """Update status button appearances"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return
        
        current_status = current_order['status']
        
        for status_key, button in self.status_buttons.items():
            if status_key == current_status:
                button.configure(style='ActiveStatus.TButton')
            else:
                button.configure(style='TButton')
                
    def logout(self):
        """Handle user logout"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.app.logout()
            
    # Include all existing methods from original OrderScreen class
    # These methods will be copied in the next implementation step
    
    def on_table_changed(self, event=None):
        """Handle table selection change"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            table_selection = self.table_combo.get()
            table_id = None
            
            if table_selection:
                table_number = table_selection.split(" ")[1]
                tables = self.app.table_model.get_all()
                for table in tables:
                    if str(table[1]) == table_number:
                        table_id = table[0]
                        break
            
            # Update table in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                table_id=table_id
            )
            self.current_table_id = table_id
            self.refresh_orders_list()
            
    def on_customer_info_changed(self, event=None):
        """Handle customer information changes"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            # Update customer info in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                customer_name=self.customer_entry.get().strip(),
                customer_mobile=self.mobile_entry.get().strip()
            )
            self.refresh_orders_list()
    
    def load_categories(self):
        """Load menu categories"""
        categories = self.app.category_model.get_all()
        category_list = [("All Categories", "All")] + [(cat[1], cat[0]) for cat in categories]
        self.category_combo['values'] = [cat[0] for cat in category_list]
        if category_list:
            self.category_combo.current(0)
    
    def on_category_changed(self, event=None):
        """Handle category selection change"""
        category_name = self.category_combo.get()
        if category_name == "All Categories":
            self.load_menu_items("")
        else:
            self.load_menu_items(category_name)
    
    def load_menu_items(self, category_name):
        """Load menu items for selected category"""
        if category_name == "All Categories":
            menu_items = self.app.menu_item_model.get_all()
        else:
            menu_items = self.app.menu_item_model.get_all("", category_name)
        
        self._update_menu_combo(menu_items)
    
    def _update_menu_combo(self, menu_items):
        """Update the menu combo box with the provided items"""
        menu_list = []
        for item in menu_items:
            item_id, name, category, price, stock, shortcode = item
            display_text = f"{name} - ₹{price:.2f}"
            if shortcode:
                display_text += f" [{shortcode}]"
            menu_list.append((display_text, item_id))
        
        self.menu_combo['values'] = [item[0] for item in menu_list]
        if menu_list:
            self.menu_combo.current(0)
    
    def search_menu_items(self, event=None):
        """Search menu items based on search term"""
        search_term = self.search_var.get().strip()
        category_name = self.category_combo.get()
        
        if not search_term:
            # If search is empty, load items for the selected category
            self.load_menu_items(category_name)
            return
        
        # Search items by name in the selected category
        if category_name == "All Categories":
            menu_items = self.app.menu_item_model.get_all(search_term)
        else:
            menu_items = self.app.menu_item_model.get_all(search_term, category_name)
        
        self._update_menu_combo(menu_items)
    
    def clear_menu_search(self):
        """Clear the search and reload items for the selected category"""
        self.search_var.set("")
        self.shortcode_var.set("")
        category_name = self.category_combo.get()
        self.load_menu_items(category_name)
    
    def on_order_type_changed(self):
        """Handle order type change"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            # Update order type in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                order_type=self.order_type.get()
            )
            self.refresh_orders_list()
        
        # Show/hide table selection based on order type
        if self.order_type.get() == "Dine-in":
            # Make table selection visible
            pass  # Table is always visible in new layout
        else:
            # Clear table selection for takeaway
            self.table_combo.set("")
            self.current_table_id = None
    
    def add_item(self):
        """Add item to current order"""
        try:
            # Get selected menu item
            menu_selection = self.menu_combo.get()
            if not menu_selection:
                messagebox.showwarning("Warning", "Please select a menu item")
                return
            
            # Parse menu item name and get menu item ID
            menu_item_name = menu_selection.split(" - ₹")[0]
            menu_items = self.app.menu_item_model.get_all(menu_item_name)
            if not menu_items:
                messagebox.showerror("Error", "Menu item not found")
                return
            
            menu_item = menu_items[0]
            menu_item_id = menu_item[0]
            item_name = menu_item[1]
            price = float(menu_item[3])
            
            # Get quantity
            try:
                quantity = int(self.quantity_var.get())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid quantity: {e}")
                return
            
            # Check stock availability
            if menu_item[4] < quantity:
                messagebox.showwarning("Warning", f"Insufficient stock. Available: {menu_item[4]}")
                return
            
            # Get current order
            current_order = self.order_manager.get_current_order()
            if not current_order:
                messagebox.showerror("Error", "No active order. Please create a new order first.")
                return
            
            # Add item to order using order manager
            item_data = {
                'menu_item_id': menu_item_id,
                'name': item_name,
                'quantity': quantity,
                'price': price,
                'total': price * quantity
            }
            
            success = self.order_manager.add_item_to_order(
                self.order_manager.current_order_id,
                item_data
            )
            
            if success:
                # Refresh display
                self.refresh_order_display(self.order_manager.current_order_id)
                # Update tab
                self.update_order_tab(self.order_manager.current_order_id)
                # Update totals
                self.update_totals_from_order_manager()
                # Reset selection
                self.quantity_var.set("1")
                # Clear shortcode entry
                self.shortcode_var.set("")
            else:
                messagebox.showerror("Error", "Failed to add item to order")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")
            print(f"Add item error details: {e}")
    
    def on_shortcode_changed(self, event=None):
        """Handle shortcode input change"""
        shortcode = self.shortcode_var.get().strip()
        
        if not shortcode:
            return
        
        # Look up item by shortcode
        item = self.app.menu_item_model.get_by_shortcode(shortcode)
        if item:
            # Select the item in the menu combo
            item_id = item[0]
            item_name = item[1]
            price = item[2]
            
            # Update menu combo to show this item
            menu_items = self.app.menu_item_model.get_all()
            for i, menu_item in enumerate(menu_items):
                if menu_item[0] == item_id:
                    display_text = f"{item_name} - ₹{price:.2f}"
                    if item[5]:  # shortcode
                        display_text += f" [{item[5]}]"
                    
                    # Update combo values and select this item
                    self.menu_combo['values'] = [display_text]
                    self.menu_combo.set(display_text)
                    break
    
    def add_item_by_shortcode(self, event=None):
        """Add item by shortcode when Enter is pressed"""
        shortcode = self.shortcode_var.get().strip()
        
        if not shortcode:
            return
        
        # Look up item by shortcode
        item = self.app.menu_item_model.get_by_shortcode(shortcode)
        if not item:
            messagebox.showwarning("Warning", f"No item found with shortcode: {shortcode}")
            return
        
        try:
            menu_item_id = item[0]
            item_name = item[1]
            price = item[2]
            stock = item[4]
            
            # Get quantity
            try:
                quantity = int(self.quantity_var.get())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid quantity: {e}")
                return
            
            # Check stock availability
            if stock < quantity:
                messagebox.showwarning("Warning", f"Insufficient stock. Available: {stock}")
                return
            
            # Get current order
            current_order = self.order_manager.get_current_order()
            if not current_order:
                messagebox.showerror("Error", "No active order. Please create a new order first.")
                return
            
            # Add item to order using order manager
            item_data = {
                'menu_item_id': menu_item_id,
                'name': item_name,
                'quantity': quantity,
                'price': price,
                'total': price * quantity
            }
            
            success = self.order_manager.add_item_to_order(
                self.order_manager.current_order_id,
                item_data
            )
            
            if success:
                # Refresh display
                self.refresh_order_display(self.order_manager.current_order_id)
                # Update tab
                self.update_order_tab(self.order_manager.current_order_id)
                # Update totals
                self.update_totals_from_order_manager()
                # Reset fields
                self.quantity_var.set("1")
                self.shortcode_var.set("")
                # Reset menu combo to show all items
                category_name = self.category_combo.get()
                self.load_menu_items(category_name)
            else:
                messagebox.showerror("Error", "Failed to add item to order")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")
            print(f"Add item by shortcode error details: {e}")
    
    def show_item_context_menu(self, event):
        """Show context menu for order items"""
        selection = self.order_tree.selection()
        if selection:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="Remove Item",
                command=lambda: self.remove_item_from_current_order(selection[0])
            )
            context_menu.post(event.x_root, event.y_root)
    
    def remove_item_from_current_order(self, item_id):
        """Remove item from current order"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return
        
        # Get item index from treeview
        selected_index = self.order_tree.index(item_id)
        
        # Remove item using order manager
        success = self.order_manager.remove_item_from_order(
            self.order_manager.current_order_id, 
            selected_index
        )
        
        if success:
            # Refresh displays
            self.refresh_order_display(self.order_manager.current_order_id)
            self.update_totals_from_order_manager()
            self.update_order_tab(self.order_manager.current_order_id)
        else:
            messagebox.showerror("Error", "Failed to remove item")
    
    def update_totals_from_order_manager(self):
        """Update order totals from order manager"""
        try:
            current_order = self.order_manager.get_current_order()
            if current_order:
                self.subtotal = current_order['subtotal']
                self.cgst_amount = current_order.get('cgst_amount', 0.0)
                self.sgst_amount = current_order.get('sgst_amount', 0.0)
                self.tax = current_order['tax']
                self.discount = current_order['discount']
                self.total = current_order['total']
                
                # Sync legacy order_items with order manager data
                self.order_items = current_order['items'].copy()
            else:
                self.subtotal = 0.0
                self.cgst_amount = 0.0
                self.sgst_amount = 0.0
                self.tax = 0.0
                self.discount = 0.0
                self.total = 0.0
                # Clear legacy order_items when no current order
                self.order_items = []
            
            # Update labels - Use Rs. instead of ₹ to avoid encoding issues
            self.subtotal_label.config(text=f"Subtotal:     Rs.{self.subtotal:.2f}")
            self.cgst_label.config(text=f"CGST (2.5%):  Rs.{self.cgst_amount:.2f}")
            self.sgst_label.config(text=f"SGST (2.5%):  Rs.{self.sgst_amount:.2f}")
            self.discount_label.config(text=f"Discount:   - Rs.{self.discount:.2f}")
            self.total_label.config(text=f"TOTAL:        Rs.{self.total:.2f}")
            
            # Update info label
            if current_order:
                status_display = current_order.get('status_display', 'Unknown')
                info_text = f"Items: {len(current_order['items'])} | Status: {status_display}"
                self.info_label.config(text=info_text)
            else:
                self.info_label.config(text="Items: 0 | Status: New")
            
            # Update payment button state based on order items
            if hasattr(self, 'payment_btn'):
                if current_order and current_order['items']:
                    self.payment_btn.config(state='normal')
                else:
                    self.payment_btn.config(state='disabled')
            
            # Update payment button state based on order items
            if hasattr(self, 'payment_btn'):
                if current_order and current_order['items']:
                    self.payment_btn.config(state='normal')
                else:
                    self.payment_btn.config(state='disabled')
            
        except Exception as e:
            print(f"Error updating totals: {e}")
            # Reset to zero if there's an error
            self.subtotal = 0.0
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
            self.tax = 0.0
            self.total = 0.0
            self.discount = 0.0
            self.order_items = []
            # Use Rs. instead of ₹ to avoid encoding issues
            self.subtotal_label.config(text="Subtotal:     Rs.0.00")
            self.cgst_label.config(text="CGST (2.5%):  Rs.0.00")
            self.sgst_label.config(text="SGST (2.5%):  Rs.0.00")
            self.discount_label.config(text="Discount:   - Rs.0.00")
            self.total_label.config(text="TOTAL:        Rs.0.00")
            self.info_label.config(text="Items: 0 | Status: New")
    
    def apply_discount(self):
        """Apply discount to current order"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            messagebox.showwarning("Warning", "No active order")
            return
            
        try:
            discount_str = simpledialog.askstring("Discount", "Enter discount amount:")
            if discount_str:
                discount = float(discount_str)
                if discount < 0:
                    raise ValueError("Discount cannot be negative")
                if discount > current_order['subtotal']:
                    raise ValueError("Discount cannot exceed subtotal")
                
                # Update discount using order manager
                self.order_manager.update_order_info(
                    self.order_manager.current_order_id,
                    discount=discount
                )
                
                # Update display
                self.update_totals_from_order_manager()
                self.update_order_tab(self.order_manager.current_order_id)
                self.refresh_orders_list()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid discount: {e}")
    
    def clear_current_order(self):
        """Clear current active order"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return
            
        if messagebox.askyesno("Confirm", "Clear current order?"):
            success = self.order_manager.clear_order(self.order_manager.current_order_id)
            if success:
                self.refresh_order_display(self.order_manager.current_order_id)
                self.update_order_tab(self.order_manager.current_order_id)
                self.update_totals_from_order_manager()
    
    def load_tables(self):
        """Load available tables from database"""
        try:
            # Get available tables from database
            tables = self.app.table_model.get_available()
            
            # Format table options for combobox
            table_options = []
            for table in tables:
                table_id, table_number = table
                table_options.append(f"Table {table_number}")
            
            # Update combobox with table options
            self.table_combo['values'] = table_options
            
            # Select first table if available
            if table_options:
                self.table_combo.current(0)
                # Set table ID for first table
                first_table_id = tables[0][0]
                self.current_table_id = first_table_id
            else:
                self.current_table_id = None
                
        except Exception as e:
            print(f"Error loading tables: {e}")
            messagebox.showerror("Error", f"Failed to load tables: {e}")
    
    # Placeholder methods for tab functionality - will be implemented in next step
    def initialize_orders(self):
        """Initialize order manager and create first order"""
        # Create initial order
        order_id = self.order_manager.create_new_order(self.order_type.get())
        self.order_manager.switch_to_order(order_id)
        
        # Create tab for this order
        self.create_order_tab(order_id)
        
        # Update display
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
    
    def create_order_tab(self, order_id: str):
        """Create a browser-style tab for an order"""
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Create tab frame container
        tab_container = ttk.Frame(self.tabs_container)
        tab_container.pack(side=tk.LEFT, padx=(0, 2))
        
        # Tab button with order info
        status_display = order.get('status_display', 'Unknown')
        tab_text = f"{order['order_number']}"
        if len(order['items']) > 0:
            tab_text += f" ({len(order['items'])})"
        
        tab_btn = ttk.Button(
            tab_container,
            text=tab_text,
            command=lambda: self.switch_to_order_tab(order_id),
            style='Tab.TButton'
        )
        tab_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Close button
        close_btn = ttk.Button(
            tab_container,
            text="✕",
            command=lambda: self.close_order_tab(order_id),
            width=3,
            style='CloseTab.TButton'
        )
        close_btn.pack(side=tk.LEFT)
        
        # Store tab references
        self.browser_tabs[order_id] = {
            'container': tab_container,
            'button': tab_btn,
            'close_btn': close_btn
        }
        
        # Update tab appearance
        self.update_browser_tab_appearance(order_id)
        
        return tab_container
    
    def switch_to_order_tab(self, order_id: str):
        """Switch to a specific order tab"""
        if order_id not in self.browser_tabs:
            return
        
        # Switch to this order in order manager
        self.order_manager.switch_to_order(order_id)
        
        # Update display
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # Update tab appearance to show active state
        self.update_browser_tab_appearance(order_id)
    
    def close_order_tab(self, order_id: str):
        """Close an order tab with confirmation"""
        if order_id not in self.browser_tabs:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Check if order has items and ask for confirmation
        if order['items']:
            if not messagebox.askyesno(
                "Confirm Close",
                f"Order {order['order_number']} has items. Close anyway?"
            ):
                return
        
        # Remove browser tab
        if order_id in self.browser_tabs:
            self.browser_tabs[order_id]['container'].destroy()
            del self.browser_tabs[order_id]
        
        # Delete from order manager
        self.order_manager.delete_order(order_id)
        
        # Refresh displays
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # If no orders left, create a new one
        if not self.order_manager.get_order_ids():
            self.new_order()
    
    def update_browser_tab_appearance(self, order_id: str):
        """Update the appearance of browser-style tab"""
        if order_id not in self.browser_tabs:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        tab_info = self.browser_tabs[order_id]
        is_current = order_id == self.order_manager.current_order_id
        
        # Update button text with item count
        item_count = len(order['items'])
        tab_text = f"{order['order_number']}"
        if item_count > 0:
            tab_text += f" ({item_count})"
        
        tab_info['button'].config(text=tab_text)
        
        # Update button style based on active state
        if is_current:
            tab_info['button'].config(style='ActiveTab.TButton')
        else:
            tab_info['button'].config(style='Tab.TButton')
    
    def update_order_tab(self, order_id: str):
        """Update order tab title and appearance"""
        self.update_browser_tab_appearance(order_id)
    
    def refresh_order_display(self, order_id: str = None):
        """Refresh display for specific order or current order"""
        if order_id is None:
            order_id = self.order_manager.current_order_id
        
        if order_id is None:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Update tree for this order
        self.order_tree.delete(*self.order_tree.get_children())
        for item in order['items']:
            self.order_tree.insert("", tk.END, values=(
                item['name'],
                item['quantity'],
                f"Rs.{item['price']:.2f}",
                f"Rs.{item['total']:.2f}"
            ))
        
        # Update main UI fields if this is current order
        if order_id == self.order_manager.current_order_id:
            self.customer_entry.delete(0, tk.END)
            self.customer_entry.insert(0, order.get('customer_name', ''))
            self.mobile_entry.delete(0, tk.END)
            self.mobile_entry.insert(0, order.get('customer_mobile', ''))
            self.order_type.set(order.get('order_type', 'Dine-in'))
            self.current_table_id = order.get('table_id')
    
    def refresh_current_order_display(self):
        """Refresh the current order display"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            # Clear display
            self.order_tree.delete(*self.order_tree.get_children())
            self.customer_entry.delete(0, tk.END)
            self.mobile_entry.delete(0, tk.END)
            return
        
        # Update UI fields
        self.customer_entry.delete(0, tk.END)
        self.customer_entry.insert(0, current_order.get('customer_name', ''))
        self.mobile_entry.delete(0, tk.END)
        self.mobile_entry.insert(0, current_order.get('customer_mobile', ''))
        self.order_type.set(current_order.get('order_type', 'Dine-in'))
        self.current_table_id = current_order.get('table_id')
        
        # Update order items display
        self.order_tree.delete(*self.order_tree.get_children())
        for item in current_order['items']:
            self.order_tree.insert("", tk.END, values=(
                item['name'],
                item['quantity'],
                f"Rs.{item['price']:.2f}",
                f"Rs.{item['total']:.2f}"
            ))
    
    def refresh_orders_list(self):
        """Update orders display with current orders"""
        # Update order info display
        self.update_order_info_display()
        
        # Get orders summary
        orders_summary = self.order_manager.get_orders_summary()
        
        # Update status
        if orders_summary:
            total_value = self.order_manager.get_total_value_all_orders()
            if hasattr(self.app, 'status_bar') and self.app.status_bar:
                self.app.status_bar.config(text=f"Active Orders: {len(orders_summary)} | Total Value: Rs.{total_value:.2f}")
        else:
            if hasattr(self.app, 'status_bar') and self.app.status_bar:
                self.app.status_bar.config(text="No active orders")
    
    def update_order_info_display(self):
        """Update order information display"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            status_display = current_order.get('status_display', 'Unknown')
            info_text = f"Items: {len(current_order['items'])} | Status: {status_display}"
            self.info_label.config(text=info_text)
        else:
            self.info_label.config(text="Items: 0 | Status: New")
    
    def new_order(self):
        """Create a new order"""
        current_order = self.order_manager.get_current_order()
        
        # Check if current order has items and ask to save
        if current_order and self.order_manager.has_items(self.order_manager.current_order_id):
            if not messagebox.askyesno("Save Order",
                "Current order has items. Save before creating new order?"):
                return
        
        # Create new order
        order_id = self.order_manager.create_new_order(self.order_type.get())
        self.order_manager.switch_to_order(order_id)
        
        # Create browser-style tab for new order
        self.create_order_tab(order_id)
        
        # Switch to new tab
        self.switch_to_order_tab(order_id)
        
        # Update display
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # Update UI fields for new order
        self.customer_entry.delete(0, tk.END)
        self.mobile_entry.delete(0, tk.END)
    
    # Event handler placeholders
    def on_order_switched(self, order_id):
        """Handle order switching from OrderManager"""
        pass
    
    def on_order_updated(self, order_id):
        """Handle order updates from OrderManager"""
        pass
    
    def on_status_changed(self, order_id):
        """Handle status changes from OrderManager"""
        pass
    
    # Placeholder methods for payment and export - will be implemented in next step
    
    def process_payment(self):
        """Process payment with multiple payment options"""
        try:
            current_order = self.order_manager.get_current_order()
            if not current_order:
                messagebox.showerror("Error", "No active order")
                return
                
            if not current_order['items']:
                messagebox.showwarning("Warning", "Cannot process payment for empty order")
                return
            
            # Get total amount from order manager
            total_amount = current_order['total'] if current_order else 0.0
            print(f"[DEBUG] Using total from order manager: Rs.{total_amount}")
            
            # Show payment dialog with multiple options
            from src.ui.order_screen import EnhancedPaymentDialog
            payment_dialog = EnhancedPaymentDialog(self.root, total_amount, self.payment_methods)
            payment_result = payment_dialog.get_result()
            
            if not payment_result:
                return
            
            payment_method, amount_paid, discount, payment_details = payment_result
            
            # Apply discount if provided
            if discount > 0:
                self.order_manager.update_order_info(
                    self.order_manager.current_order_id,
                    discount=discount
                )
                self.update_totals_from_order_manager()
            
            # Save order with payment information
            self.save_order_with_payment(payment_method, amount_paid, payment_details)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process payment: {e}")
            print(f"Payment processing error: {e}")
    
    def save_order_with_payment(self, payment_method, amount_paid, payment_details=None):
        """Save order with specific payment method and encrypted payment details"""
        try:
            # Get order details from order manager
            current_order = self.order_manager.get_current_order()
            if not current_order:
                messagebox.showerror("Error", "No active order")
                return
            
            # Get order details
            order_type = current_order['order_type']
            table_id = current_order['table_id']
            customer_name = current_order['customer_name']
            customer_mobile = current_order['customer_mobile']
            
            # Encrypt customer mobile number if provided
            encrypted_mobile = None
            if customer_mobile:
                try:
                    encrypted_mobile = self.encryption_manager.encrypt_field(customer_mobile)
                except Exception as e:
                    print(f"Error encrypting mobile number: {e}")
                    encrypted_mobile = customer_mobile  # Fallback to unencrypted
            
            if order_type == "Dine-in" and not table_id:
                messagebox.showwarning("Warning", "Please select a table")
                return
            
            if order_type == "Takeaway" and not customer_name:
                messagebox.showwarning("Warning", "Please enter customer name for takeaway order")
                return
            
            # Generate order number
            order_number = generate_order_number()
            
            # Create order using dictionary format
            order_data = {
                'order_number': order_number,
                'table_id': table_id,
                'customer_name': customer_name,
                'customer_mobile': encrypted_mobile,
                'order_type': order_type,
                'subtotal': current_order['subtotal'],
                'tax': current_order['tax'],
                'discount': current_order['discount'],
                'total': current_order['total'],
                'items': [{'id': item['menu_item_id'], 'quantity': item['quantity'],
                          'price': item['price'], 'total': item['total']}
                         for item in current_order['items']]
            }
            
            order_id = self.app.order_model.create(order_data)
            if not order_id:
                messagebox.showerror("Error", "Failed to create order")
                return
            
            # Add order items
            for item in current_order['items']:
                self.app.order_model.add_item(
                    order_id,
                    item['menu_item_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                )
                
                # Update stock
                menu_item = self.app.menu_item_model.get_by_id(item['menu_item_id'])
                if menu_item:
                    new_stock = menu_item[3] - item['quantity']
                    self.app.menu_item_model.update_stock(item['menu_item_id'], new_stock)
            
            # Add payment with encrypted details using the new payment model
            try:
                from src.models.payment import Payment
                payment_model = Payment(self.db)
                payment_model.add_payment(order_id, payment_method, amount_paid, payment_details)
            except Exception as e:
                print(f"Error adding encrypted payment, falling back to basic payment: {e}")
                # Fallback to basic payment without encryption
                self.app.order_model.add_payment(order_id, payment_method, amount_paid)
            
            # Update table status if dine-in
            if order_type == "Dine-in" and table_id:
                self.app.table_model.update_status(table_id, "Occupied")
            
            # Show success message
            messagebox.showinfo("Success", f"Order {order_number} saved successfully!\nPayment: {payment_method} - Rs.{amount_paid:.2f}")
            
            # Handle export based on settings
            self._handle_post_payment_export(order_id, False)
            
            # Remove from active orders and clear
            self.clear_order()
            
            # Create new order for next transaction
            self.new_order()
            
            # Dispatch events
            event_dispatcher.order_created(order_id)
            event_dispatcher.inventory_updated(None, None)  # Trigger inventory refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")
            print(f"Save order with payment error: {e}")
    # Remove duplicate method - real implementation is above
    
    def export_order(self):
        """Export current order without saving"""
        current_order = self.order_manager.get_current_order()
        if not current_order or not current_order['items']:
            messagebox.showwarning("Warning", "No items in order to export")
            return
        
        # Prepare order data for export
        order_data = self.order_manager.get_order_for_export(self.order_manager.current_order_id)
        
        # Show export dialog
        dialog = ExportDialog(self.root, self.app.settings, order_data)
        result = dialog.get_result()
        
        if result:
            self._process_export(order_data, result)
    def save_order(self, print_bill=False, export_order=False):
        """Save the order"""
        try:
            if not self.order_items:
                messagebox.showwarning("Warning", "No items in order")
                return
            
            # Get order details
            order_type = self.order_type.get()
            table_id = None
            
            if order_type == "Dine-in":
                table_selection = self.table_combo.get()
                if table_selection:
                    table_number = table_selection.split(" ")[1]
                    tables = self.app.table_model.get_all()
                    for table in tables:
                        if str(table[1]) == table_number:
                            table_id = table[0]
                            break
                
                if not table_id:
                    messagebox.showwarning("Warning", "Please select a table")
                    return
            
            customer_name = self.customer_entry.get().strip()
            customer_mobile = self.mobile_entry.get().strip()
            
            if order_type == "Takeaway" and not customer_name:
                messagebox.showwarning("Warning", "Please enter customer name for takeaway order")
                return
            
            # Generate order number
            order_number = generate_order_number()
            
            # Create order using dictionary format
            order_data = {
                'order_number': order_number,
                'table_id': table_id,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'order_type': order_type,
                'subtotal': self.subtotal,
                'tax': self.tax,
                'discount': self.discount,
                'total': self.total,
                'items': [{'id': item['menu_item_id'], 'quantity': item['quantity'],
                          'price': item['price'], 'total': item['total']}
                         for item in self.order_items]
            }
            
            order_id = self.app.order_model.create(order_data)
            if not order_id:
                messagebox.showerror("Error", "Failed to create order")
                return
            
            # Add order items
            for item in self.order_items:
                self.app.order_model.add_item(
                    order_id,
                    item['menu_item_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                )
                
                # Update stock
                menu_item = self.app.menu_item_model.get_by_id(item['menu_item_id'])
                if menu_item:
                    new_stock = menu_item[3] - item['quantity']
                    self.app.menu_item_model.update_stock(item['menu_item_id'], new_stock)
            
            # Add payment (default to cash for now)
            self.app.order_model.add_payment(order_id, "Cash", self.total)
            
            # Update table status if dine-in
            if order_type == "Dine-in" and table_id:
                self.app.table_model.update_status(table_id, "Occupied")
            
            # Show success message
            messagebox.showinfo("Success", f"Order {order_number} saved successfully!")
            
            # Print bill if requested
            if print_bill:
                self.print_bill(order_id)
            
            # Handle export based on settings and parameters
            self._handle_post_payment_export(order_id, export_order)
            
            # Clear order and refresh
            self.clear_order()
            
            # Dispatch events
            event_dispatcher.order_created(order_id)
            event_dispatcher.inventory_updated(None, None)  # Trigger inventory refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")
    
    def save_and_print_order(self):
        """Save order and print bill"""
        self.save_order(print_bill=True)
    
    def save_and_export_order(self):
        """Save order and export with options"""
        self.save_order(export_order=True)
    
    def print_bill(self, order_id):
        """Print bill for the order"""
        try:
            from src.ui.printer_dialog import PrinterSelectionDialog
            from src.utils.printer import PrinterManager
            
            # Show printer selection dialog
            dialog = PrinterSelectionDialog(self.root, self.app.settings, "bill")
            result = dialog.get_result()
            
            if result:
                # Prepare bill data
                bill_data = self._prepare_bill_data(order_id)
                
                # Print the bill
                printer_manager = PrinterManager(self.app.settings)
                success = printer_manager.print_bill(
                    bill_data,
                    result['printer_type'],
                    result['printer_name']
                )
                
                if success:
                    messagebox.showinfo("Success", "Bill printed successfully!")
                else:
                    messagebox.showerror("Error", "Failed to print bill")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Print error: {e}")
    
    def _prepare_bill_data(self, order_id):
        """Prepare bill data for printing"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                return {}
            
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
            
            # Format items for printing
            formatted_items = []
            for item in items:
                name, quantity, price, item_total, item_status = item
                formatted_items.append((name, quantity, price, item_total))
            
            return {
                'restaurant_name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
                'restaurant_address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
                'order_number': order_number,
                'date': created_at,
                'order_type': order_type,
                'table_number': table_number,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'items': formatted_items,
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total': total,
                'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE))
            }
            
        except Exception as e:
            print(f"Error preparing bill data: {e}")
            return {}
    
    def _handle_post_payment_export(self, order_id, manual_export=False):
        """Handle export after payment completion based on settings"""
        try:
            # Get export settings
            export_after_payment = self.app.settings.get('export_after_payment', 'false').lower() == 'true'
            default_export_format = self.app.settings.get('default_export_format', 'none')
            show_export_dialog = self.app.settings.get('show_export_dialog', 'true').lower() == 'true'
            
            # Skip if auto-export is disabled and this is not a manual export
            if not export_after_payment and not manual_export:
                return
            
            # If manual export or dialog is enabled, show export dialog
            if manual_export or show_export_dialog:
                self.export_order_with_id(order_id)
            else:
                # Auto-export with default format
                if default_export_format != 'none':
                    self._auto_export_order(order_id, default_export_format)
                    
        except Exception as e:
            # Export failures should not affect payment completion
            print(f"Export error (non-critical): {e}")
    
    def _auto_export_order(self, order_id, export_format):
        """Automatically export order in specified format"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                print(f"Order {order_id} not found for auto-export")
                return
            
            # Prepare order data for export
            order_data = self._prepare_export_data_from_details(order_details)
            
            # Export based on format
            if export_format == 'pdf':
                if self.pdf_exporter is None:
                    print(f"Cannot auto-export order {order_id} to PDF: ReportLab library is not installed")
                    return
                success, result = self.pdf_exporter.export_order(order_data)
                if success:
                    print(f"Order {order_id} auto-exported to PDF: {result}")
                else:
                    print(f"Failed to auto-export order {order_id} to PDF: {result}")
                    
            elif export_format == 'text':
                success, result = self.text_exporter.export_order(order_data)
                if success:
                    print(f"Order {order_id} auto-exported to Text: {result}")
                else:
                    print(f"Failed to auto-export order {order_id} to Text: {result}")
                    
            elif export_format == 'both':
                # Export both formats
                if self.pdf_exporter is None:
                    print(f"Cannot auto-export order {order_id} to PDF: ReportLab library is not installed")
                    pdf_success = False
                    pdf_result = "ReportLab not available"
                else:
                    pdf_success, pdf_result = self.pdf_exporter.export_order(order_data)
                
                text_success, text_result = self.text_exporter.export_order(order_data)
                
                if pdf_success:
                    print(f"Order {order_id} auto-exported to PDF: {pdf_result}")
                else:
                    print(f"Failed to auto-export order {order_id} to PDF: {pdf_result}")
                    
                if text_success:
                    print(f"Order {order_id} auto-exported to Text: {text_result}")
                else:
                    print(f"Failed to auto-export order {order_id} to Text: {text_result}")
                    
        except Exception as e:
            print(f"Auto-export error for order {order_id}: {e}")
    
    def _prepare_export_data_from_details(self, order_details):
        """Prepare order data for export from order details"""
        order = order_details['order']
        items = order_details['items']
        payments = order_details['payments']
        
        # Get table number if dine-in
        table_number = None
        if order[1]:  # table_id exists
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == order[1]:
                    table_number = table[1]
                    break
        
        return {
            'order_number': order[0],
            'table_number': table_number,
            'customer_name': order[2],
            'customer_mobile': order[3],
            'order_type': order[4],
            'status': order[10],
            'subtotal': order[5],
            'tax': order[6],
            'discount': order[7],
            'total': order[8],
            'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE)),
            'items': items,
            'payments': payments,
            'created_at': order[9]
        }
    
    def export_order_with_id(self, order_id):
        """Export saved order by ID"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                messagebox.showerror("Error", "Order not found")
                return
            
            # Prepare order data for export
            order_data = self._prepare_export_data_from_details(order_details)
            
            # Show export dialog
            dialog = ExportDialog(self.root, self.app.settings, order_data)
            result = dialog.get_result()
            
            if result:
                self._process_export(order_data, result)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export order: {e}")
    
    def _process_export(self, order_data, export_options):
        """Process the export with selected options"""
        try:
            exported_files = []
            
            # Export to PDF if selected
            if export_options['export_pdf']:
                success, result = self.pdf_exporter.export_order(order_data)
                if success:
                    exported_files.append(result)
                    if export_options.get('auto_open'):
                        self._open_file(result)
                else:
                    messagebox.showerror("Export Error", f"Failed to export PDF: {result}")
                    return
            
            # Export to Text if selected
            if export_options['export_text']:
                success, result = self.text_exporter.export_order(order_data)
                if success:
                    exported_files.append(result)
                    if export_options.get('auto_open'):
                        self._open_file(result)
                else:
                    messagebox.showerror("Export Error", f"Failed to export Text: {result}")
                    return
            
            # Show success message
            if exported_files:
                file_count = len(exported_files)
                messagebox.showinfo(
                    "Export Successful",
                    f"Order exported successfully to {file_count} file{'s' if file_count > 1 else ''}!"
                )
            else:
                messagebox.showwarning("Export Warning", "No files were exported")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}")
    
    def _open_file(self, filepath):
        """Open file with default application"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', filepath], check=True)
        except Exception as e:
            print(f"Failed to open file: {e}")
    
    def clear_order(self):
        """Clear current order (legacy method - redirects to clear_current_order)"""
        self.clear_current_order()
    
    def cleanup(self):
        """Cleanup resources when screen is destroyed"""
        # Save current order to memory if it has items
        if self.order_items and hasattr(self, 'current_order_id'):
            pass  # Order is already managed by OrderManager
        
        # Clean up UI components
        if hasattr(self, 'orders_listbox'):
            self.orders_listbox = None
        if hasattr(self, 'order_tree'):
            self.order_tree = None
        pass


class EnhancedPaymentDialog:
    """Enhanced payment dialog with multiple payment options"""
    
    def __init__(self, parent, total_amount, payment_methods):
        self.result = None
        self.total_amount = total_amount
        self.payment_methods = payment_methods
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Process Payment")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup payment dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and amount
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Payment Processing", 
                 font=('Arial', 16, 'bold')).pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"Total Amount: Rs.{self.total_amount:.2f}",
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        
        # Payment method selection
        method_frame = ttk.LabelFrame(main_frame, text="Payment Method", padding=10)
        method_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.payment_method_var = tk.StringVar(value=self.payment_methods[0])
        
        # Create radio buttons for payment methods
        for i, method in enumerate(self.payment_methods):
            row = i // 2
            col = i % 2
            ttk.Radiobutton(method_frame, text=method, variable=self.payment_method_var, 
                           value=method, command=self.on_payment_method_change).grid(
                row=row, column=col, sticky=tk.W, padx=10, pady=5)
        
        # Amount details
        details_frame = ttk.LabelFrame(main_frame, text="Payment Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Discount
        ttk.Label(details_frame, text="Discount (Rs):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = ttk.Entry(details_frame, textvariable=self.discount_var, width=15)
        discount_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Amount paid
        ttk.Label(details_frame, text="Amount Paid (Rs):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_paid_var = tk.StringVar(value=str(self.total_amount))
        amount_paid_entry = ttk.Entry(details_frame, textvariable=self.amount_paid_var, width=15)
        amount_paid_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Balance
        ttk.Label(details_frame, text="Balance (Rs):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.balance_label = ttk.Label(details_frame, text="Rs.0.00", font=('Arial', 10, 'bold'))
        self.balance_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Update calculations when values change
        self.discount_var.trace('w', self.update_calculations)
        self.amount_paid_var.trace('w', self.update_calculations)
        
        # Payment method specific fields
        self.method_fields_frame = ttk.LabelFrame(main_frame, text="Payment Details", padding=10)
        self.method_fields_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Initialize with first payment method
        self.on_payment_method_change()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Process Payment", command=self.process).pack(side=tk.RIGHT)
        
        # Initial calculation
        self.update_calculations()
    
    def on_payment_method_change(self):
        """Handle payment method change"""
        # Clear existing method-specific fields
        for widget in self.method_fields_frame.winfo_children():
            widget.destroy()
        
        method = self.payment_method_var.get()
        
        if method == "Card":
            ttk.Label(self.method_fields_frame, text="Card Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.card_number_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.card_number_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(self.method_fields_frame, text="Expiry:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.expiry_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.expiry_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
            
        elif method == "UPI":
            ttk.Label(self.method_fields_frame, text="UPI ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.upi_id_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.upi_id_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Wallet":
            ttk.Label(self.method_fields_frame, text="Wallet Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.wallet_number_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.wallet_number_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Credit":
            ttk.Label(self.method_fields_frame, text="Customer Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.credit_customer_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.credit_customer_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Cash":
            ttk.Label(self.method_fields_frame, text="Cash Received:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.cash_received_var = tk.StringVar(value=str(self.total_amount))
            ttk.Entry(self.method_fields_frame, textvariable=self.cash_received_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(self.method_fields_frame, text="Change:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.change_label = ttk.Label(self.method_fields_frame, text="Rs.0.00", font=('Arial', 10, 'bold'))
            self.change_label.grid(row=1, column=1, sticky=tk.W, pady=5)
    
    def update_calculations(self, *args):
        """Update payment calculations"""
        try:
            discount = float(self.discount_var.get() or 0)
            if discount < 0:
                discount = 0
                self.discount_var.set("0")
            
            if discount > self.total_amount:
                discount = self.total_amount
                self.discount_var.set(str(self.total_amount))
            
            # Update amount paid to total minus discount for cash payments
            if self.payment_method_var.get() == "Cash":
                final_amount = self.total_amount - discount
                self.amount_paid_var.set(str(final_amount))
                
                # Update change calculation
                cash_received = float(self.cash_received_var.get() or 0)
                change = cash_received - final_amount
                self.change_label.config(text=f"Rs.{change:.2f}")
            
            # Update balance
            amount_paid = float(self.amount_paid_var.get() or 0)
            final_total = self.total_amount - discount
            balance = amount_paid - final_total
            self.balance_label.config(text=f"Rs.{balance:.2f}")
            
        except ValueError:
            self.balance_label.config(text="Invalid amount")
    
    def process(self):
        """Process payment"""
        try:
            amount_paid = float(self.amount_paid_var.get() or 0)
            discount = float(self.discount_var.get() or 0)
            
            # Validate payment
            if amount_paid < (self.total_amount - discount):
                messagebox.showerror("Error", "Insufficient payment amount")
                return
            
            # Validate payment method specific fields
            method = self.payment_method_var.get()
            if method == "Card":
                if not self.card_number_var.get().strip():
                    messagebox.showerror("Error", "Please enter card number")
                    return
            elif method == "UPI":
                if not self.upi_id_var.get().strip():
                    messagebox.showerror("Error", "Please enter UPI ID")
                    return
            elif method == "Wallet":
                if not self.wallet_number_var.get().strip():
                    messagebox.showerror("Error", "Please enter wallet number")
                    return
            elif method == "Credit":
                if not self.credit_customer_var.get().strip():
                    messagebox.showerror("Error", "Please enter customer name")
                    return
            
            # Prepare payment details for encryption
            payment_details = None
            if method == "Card":
                payment_details = {
                    'card_number': getattr(self, 'card_number_var', None) and self.card_number_var.get(),
                    'expiry': getattr(self, 'expiry_var', None) and self.expiry_var.get()
                }
            elif method == "UPI":
                payment_details = {
                    'upi_id': getattr(self, 'upi_id_var', None) and self.upi_id_var.get()
                }
            elif method == "Wallet":
                payment_details = {
                    'wallet_number': getattr(self, 'wallet_number_var', None) and self.wallet_number_var.get()
                }
            elif method == "Credit":
                payment_details = {
                    'customer_name': getattr(self, 'credit_customer_var', None) and self.credit_customer_var.get()
                }
            
            self.result = (method, amount_paid, discount, payment_details)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid payment amount")
    
    def cancel(self):
        """Cancel payment"""
        self.dialog.destroy()
    
    def get_result(self):
        """Get payment result"""
        self.dialog.wait_window()
        return self.result

