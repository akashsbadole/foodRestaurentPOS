import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import os
from datetime import datetime
import hashlib
import random
import string
# Enhanced PIL import with better error handling
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    PIL_VERSION = Image.__version__
    print(f"PIL (Pillow) v{PIL_VERSION} loaded successfully")
except ImportError as e:
    PIL_AVAILABLE = False
    PIL_VERSION = None
    print(f"Warning: PIL (Pillow) not installed or import failed: {e}")
    print("Image features will be disabled. Install with: pip install Pillow")
except Exception as e:
    PIL_AVAILABLE = False
    PIL_VERSION = None
    print(f"Warning: PIL (Pillow) import error: {e}")
    print("Image features will be disabled due to import issues")
import csv
from io import StringIO
import tempfile

class RestaurantPOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant POS System")
        self.root.geometry("1200x700")
        self.root.state('zoomed')  # Maximize window
        
        # Check if database exists, if not create it
        if not os.path.exists('restaurant_pos.db'):
            import database_setup
            database_setup.setup_database()
        
        # Initialize variables
        self.current_user = None
        self.current_order = None
        self.cart_items = []
        self.selected_table = None
        self.order_type = "Dine-in"
        
        # Initialize database connection
        self.conn = sqlite3.connect('restaurant_pos.db')
        self.cursor = self.conn.cursor()
        
        # Load settings
        self.load_settings()
        
        # Show login screen
        self.show_login_screen()
    
    def setup_global_keyboard_shortcuts(self):
        """Set up global keyboard shortcuts for the application"""
        # Clear any existing bindings
        self.root.unbind('<Alt-d>')
        self.root.unbind('<Alt-D>')
        self.root.unbind('<Alt-n>')
        self.root.unbind('<Alt-N>')
        self.root.unbind('<Alt-o>')
        self.root.unbind('<Alt-O>')
        self.root.unbind('<Alt-m>')
        self.root.unbind('<Alt-M>')
        self.root.unbind('<Alt-t>')
        self.root.unbind('<Alt-T>')
        self.root.unbind('<Alt-i>')
        self.root.unbind('<Alt-I>')
        self.root.unbind('<Alt-k>')
        self.root.unbind('<Alt-K>')
        self.root.unbind('<Alt-r>')
        self.root.unbind('<Alt-R>')
        self.root.unbind('<Alt-s>')
        self.root.unbind('<Alt-S>')
        self.root.unbind('<Alt-l>')
        self.root.unbind('<Alt-L>')
        self.root.unbind('<F1>')
        
        # Global shortcuts (Alt+key combinations)
        self.root.bind('<Alt-d>', lambda e: (self.show_dashboard(), self.show_keyboard_feedback("Dashboard")))
        self.root.bind('<Alt-D>', lambda e: (self.show_dashboard(), self.show_keyboard_feedback("Dashboard")))
        self.root.bind('<Alt-n>', lambda e: (self.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-N>', lambda e: (self.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-o>', lambda e: (self.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('<Alt-O>', lambda e: (self.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('<Alt-m>', lambda e: (self.show_menu(), self.show_keyboard_feedback("Menu Management")))
        self.root.bind('<Alt-M>', lambda e: (self.show_menu(), self.show_keyboard_feedback("Menu Management")))
        self.root.bind('<Alt-t>', lambda e: (self.show_tables(), self.show_keyboard_feedback("Table Management")))
        self.root.bind('<Alt-T>', lambda e: (self.show_tables(), self.show_keyboard_feedback("Table Management")))
        self.root.bind('<Alt-i>', lambda e: (self.show_inventory(), self.show_keyboard_feedback("Inventory")))
        self.root.bind('<Alt-I>', lambda e: (self.show_inventory(), self.show_keyboard_feedback("Inventory")))
        self.root.bind('<Alt-k>', lambda e: (self.show_kot(), self.show_keyboard_feedback("KOT")))
        self.root.bind('<Alt-K>', lambda e: (self.show_kot(), self.show_keyboard_feedback("KOT")))
        self.root.bind('<Alt-r>', lambda e: (self.show_reports(), self.show_keyboard_feedback("Reports")))
        self.root.bind('<Alt-R>', lambda e: (self.show_reports(), self.show_keyboard_feedback("Reports")))
        
        # Settings shortcut (Admin only)
        if self.current_user and self.current_user['role'] == 'Admin':
            self.root.bind('<Alt-s>', lambda e: (self.show_settings(), self.show_keyboard_feedback("Settings")))
            self.root.bind('<Alt-S>', lambda e: (self.show_settings(), self.show_keyboard_feedback("Settings")))
        
        # Logout shortcut
        self.root.bind('<Alt-l>', lambda e: (self.logout(), self.show_keyboard_feedback("Logout")))
        self.root.bind('<Alt-L>', lambda e: (self.logout(), self.show_keyboard_feedback("Logout")))
        
        # Help shortcut
        self.root.bind('<F1>', lambda e: (self.show_keyboard_shortcuts_help(), self.show_keyboard_feedback("Help")))
    
    def setup_dashboard_shortcuts(self):
        """Set up dashboard numeric key shortcuts"""
        # Clear any existing bindings
        self.root.unbind('1')
        self.root.unbind('2')
        self.root.unbind('3')
        
        # Dashboard shortcuts (numeric keys)
        self.root.bind('1', lambda e: (self.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('2', lambda e: (self.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('3', lambda e: (self.show_menu(), self.show_keyboard_feedback("Menu Management")))
    
    def setup_order_screen_shortcuts(self):
        """Set up order screen specific shortcuts"""
        # Clear any existing bindings
        self.root.unbind('<F1>')
        self.root.unbind('<F2>')
        self.root.unbind('<F3>')
        self.root.unbind('<F4>')
        self.root.unbind('<F5>')
        self.root.unbind('<Control-Return>')
        
        # Order screen shortcuts
        self.root.bind('<F1>', lambda e: (self.add_to_cart(), self.show_keyboard_feedback("Add to Cart")))
        self.root.bind('<F2>', lambda e: (self.update_cart_quantity(), self.show_keyboard_feedback("Update Quantity")))
        self.root.bind('<F3>', lambda e: (self.remove_from_cart(), self.show_keyboard_feedback("Remove from Cart")))
        self.root.bind('<F4>', lambda e: (self.clear_cart(), self.show_keyboard_feedback("Clear Cart")))
        self.root.bind('<F5>', lambda e: (self.load_menu_items(), self.show_keyboard_feedback("Refresh Menu")))
        self.root.bind('<Control-Return>', lambda e: (self.process_payment("Cash"), self.show_keyboard_feedback("Process Payment")))
    
    def enhance_treeview_navigation(self, treeview):
        """Enhance treeview with better keyboard navigation"""
        def on_tree_key_press(event):
            if event.keysym == 'Return':
                # Trigger default action based on current screen
                self.handle_treeview_enter_key(treeview)
            elif event.keysym == 'Delete':
                # Trigger delete action if applicable
                self.handle_treeview_delete_key(treeview)
        
        treeview.bind('<KeyRelease>', on_tree_key_press)
    
    def handle_treeview_enter_key(self, treeview):
        """Handle Enter key press on treeview"""
        selection = treeview.selection()
        if not selection:
            return
        
        # Determine current screen and trigger appropriate action
        if hasattr(self, 'orders_tree') and treeview == self.orders_tree:
            self.view_order_details()
            self.show_keyboard_feedback("View Order Details")
        elif hasattr(self, 'menu_items_tree') and treeview == self.menu_items_tree:
            self.edit_menu_item()
            self.show_keyboard_feedback("Edit Menu Item")
        elif hasattr(self, 'categories_tree') and treeview == self.categories_tree:
            self.edit_category()
            self.show_keyboard_feedback("Edit Category")
        elif hasattr(self, 'inventory_tree') and treeview == self.inventory_tree:
            self.update_stock()
            self.show_keyboard_feedback("Update Stock")
        elif hasattr(self, 'kot_tree') and treeview == self.kot_tree:
            # Toggle between statuses
            if self.kot_filter_var.get() == "Pending":
                self.mark_kot_preparing()
                self.show_keyboard_feedback("Mark as Preparing")
            else:
                self.mark_kot_completed()
                self.show_keyboard_feedback("Mark as Completed")
    
    def handle_treeview_delete_key(self, treeview):
        """Handle Delete key press on treeview"""
        selection = treeview.selection()
        if not selection:
            return
        
        # Determine current screen and trigger appropriate delete action
        if hasattr(self, 'menu_items_tree') and treeview == self.menu_items_tree:
            self.delete_menu_item()
            self.show_keyboard_feedback("Delete Menu Item")
        elif hasattr(self, 'categories_tree') and treeview == self.categories_tree:
            self.delete_category()
            self.show_keyboard_feedback("Delete Category")
    
    def setup_form_navigation(self, parent_frame):
        """Setup improved form navigation with Enter and Escape keys"""
        def on_form_key_press(event):
            if event.keysym == 'Return':
                # Find the next widget to focus
                widget = event.widget
                next_widget = parent_frame.tk_focusNext().focus_get()
                if next_widget:
                    next_widget.focus()
                    self.show_keyboard_feedback("Next Field")
                else:
                    # If no next widget, try to submit form
                    self.try_submit_form(parent_frame)
                    self.show_keyboard_feedback("Submit Form")
            elif event.keysym == 'Escape':
                # Try to cancel/close dialog
                self.try_cancel_dialog(parent_frame)
                self.show_keyboard_feedback("Cancel Dialog")
        
        # Bind to all entry widgets in the form
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.bind('<KeyRelease>', on_form_key_press)
    
    def try_submit_form(self, parent_frame):
        """Try to submit the current form"""
        # Look for a save/submit button in the parent frame
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        button_text = child.cget('text').lower()
                        if 'save' in button_text or 'submit' in button_text or 'login' in button_text:
                            child.invoke()
                            return
    
    def try_cancel_dialog(self, parent_frame):
        """Try to cancel/close the current dialog"""
        # Look for a cancel button in the parent frame
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        button_text = child.cget('text').lower()
                        if 'cancel' in button_text:
                            child.invoke()
                            return
        
        # If no cancel button found, try to close the window
        try:
            parent_frame.winfo_toplevel().destroy()
        except:
            pass
    
    def show_keyboard_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Keyboard Shortcuts Help")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        # Create notebook for different sections
        notebook = ttk.Notebook(help_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Global shortcuts tab
        global_frame = ttk.Frame(notebook, padding="10")
        notebook.add(global_frame, text="Global Shortcuts")
        
        global_text = """
        ALT + D: Dashboard
        ALT + N: New Order
        ALT + O: Orders
        ALT + M: Menu Management
        ALT + T: Table Management
        ALT + I: Inventory
        ALT + K: KOT (Kitchen Order Tickets)
        ALT + R: Reports
        ALT + S: Settings (Admin only)
        ALT + L: Logout
        F1: Show this help dialog
        """
        
        global_label = ttk.Label(global_frame, text=global_text, justify=tk.LEFT)
        global_label.pack(anchor=tk.W)
        
        # Dashboard shortcuts tab
        dashboard_frame = ttk.Frame(notebook, padding="10")
        notebook.add(dashboard_frame, text="Dashboard")
        
        dashboard_text = """
        1: New Order
        2: View Orders
        3: Menu Management
        """
        
        dashboard_label = ttk.Label(dashboard_frame, text=dashboard_text, justify=tk.LEFT)
        dashboard_label.pack(anchor=tk.W)
        
        # Order screen shortcuts tab
        order_frame = ttk.Frame(notebook, padding="10")
        notebook.add(order_frame, text="Order Screen")
        
        order_text = """
        F1: Add to Cart
        F2: Update Quantity
        F3: Remove from Cart
        F4: Clear Cart
        F5: Refresh Menu
        Ctrl + Enter: Process Payment (Cash)
        """
        
        order_label = ttk.Label(order_frame, text=order_text, justify=tk.LEFT)
        order_label.pack(anchor=tk.W)
        
        # Treeview navigation tab
        treeview_frame = ttk.Frame(notebook, padding="10")
        notebook.add(treeview_frame, text="Treeview Navigation")
        
        treeview_text = """
        Enter: Trigger default action (view details, edit, etc.)
        Delete: Delete selected item where applicable
        Arrow Keys: Navigate between items
        Tab: Move between fields/sections
        """
        
        treeview_label = ttk.Label(treeview_frame, text=treeview_text, justify=tk.LEFT)
        treeview_label.pack(anchor=tk.W)
        
        # Form navigation tab
        form_frame = ttk.Frame(notebook, padding="10")
        notebook.add(form_frame, text="Form Navigation")
        
        form_text = """
        Enter: Move to next field or submit form
        Escape: Cancel dialog/close window
        Tab: Move between form fields
        """
        
        form_label = ttk.Label(form_frame, text=form_text, justify=tk.LEFT)
        form_label.pack(anchor=tk.W)
        
        # Close button
        close_button = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_button.pack(pady=10)
        
        # Center the window
        help_window.transient(self.root)
        help_window.grab_set()
    
    def show_keyboard_feedback(self, action):
        """Show visual feedback for keyboard shortcut action"""
        if hasattr(self, 'status_bar') and self.status_bar:
            # Update status bar with action
            self.status_bar.config(text=f"Keyboard shortcut: {action}")
            # Schedule clearing the status after 2 seconds
            self.root.after(2000, lambda: self.status_bar.config(text="Ready"))
    
    def create_status_bar(self, parent):
        """Create a status bar at the bottom of the window"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # Keyboard shortcut indicator
        self.shortcut_indicator = ttk.Label(status_frame, text="Press F1 for shortcuts", relief=tk.SUNKEN)
        self.shortcut_indicator.pack(side=tk.RIGHT, padx=2, pady=2)
    
    def load_settings(self):
        """Load application settings from database"""
        self.settings = {}
        self.cursor.execute("SELECT key, value FROM settings")
        for row in self.cursor.fetchall():
            self.settings[row[0]] = row[1]
    
    def update_setting(self, key, value):
        """Update a setting in the database"""
        self.cursor.execute("UPDATE settings SET value = ?, updated_at = ? WHERE key = ?", 
                           (value, datetime.now(), key))
        self.conn.commit()
        self.settings[key] = value
    
    def show_login_screen(self):
        """Display the login screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create login frame
        login_frame = ttk.Frame(main_container, padding="40")
        login_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = ttk.Label(login_frame, text="Restaurant POS System", font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Restaurant name
        restaurant_label = ttk.Label(login_frame, text=self.settings.get('restaurant_name', 'My Restaurant'),
                                   font=('Arial', 14))
        restaurant_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Username
        ttk.Label(login_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.username_entry = ttk.Entry(login_frame, width=20)
        self.username_entry.grid(row=2, column=1, pady=10)
        
        # Password
        ttk.Label(login_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=10)
        self.password_entry = ttk.Entry(login_frame, width=20, show="*")
        self.password_entry.grid(row=3, column=1, pady=10)
        
        # Login button
        login_button = ttk.Button(login_frame, text="Login", command=self.login)
        login_button.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Create status bar for login screen
        self.create_status_bar(self.root)
        
        # Enhanced login screen keyboard navigation
        def on_login_key_press(event):
            if event.keysym == 'Return':
                # If password field has focus, login; otherwise move to next field
                if self.password_entry.focus_get() == self.password_entry:
                    self.login()
                    self.show_keyboard_feedback("Login")
                else:
                    self.password_entry.focus()
                    self.show_keyboard_feedback("Next Field")
            elif event.keysym == 'Tab':
                # Tab navigation between fields
                if self.username_entry.focus_get() == self.username_entry:
                    self.password_entry.focus()
                    self.show_keyboard_feedback("Next Field")
                    return "break"  # Prevent default tab behavior
                elif self.password_entry.focus_get() == self.password_entry:
                    self.username_entry.focus()
                    self.show_keyboard_feedback("Previous Field")
                    return "break"  # Prevent default tab behavior
        
        # Bind keyboard events
        self.root.bind('<Return>', on_login_key_press)
        self.root.bind('<Tab>', on_login_key_press)
        
        # Focus on username entry
        self.username_entry.focus()
    
    def login(self):
        """Authenticate user and show main application"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        # Hash password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Check credentials
        self.cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
                          (username, hashed_password))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
            self.show_main_app()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def show_main_app(self):
        """Display the main application interface"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create top bar
        self.create_top_bar(main_container)
        
        # Create content area
        content_container = ttk.Frame(main_container)
        content_container.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.create_sidebar(content_container)
        
        # Create main content area
        self.content_frame = ttk.Frame(content_container)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create status bar
        self.create_status_bar(self.root)
        
        # Set up global keyboard shortcuts
        self.setup_global_keyboard_shortcuts()
        
        # Show dashboard by default
        self.show_dashboard()
    
    def create_top_bar(self, parent):
        """Create the top navigation bar"""
        top_bar = ttk.Frame(parent)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Restaurant name
        restaurant_label = ttk.Label(top_bar, text=self.settings.get('restaurant_name', 'My Restaurant'), 
                                    font=('Arial', 14, 'bold'))
        restaurant_label.pack(side=tk.LEFT, padx=10)
        
        # User info
        user_frame = ttk.Frame(top_bar)
        user_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(user_frame, text=f"User: {self.current_user['username']} ({self.current_user['role']})").pack(side=tk.LEFT, padx=5)
        
        # Logout button
        logout_button = ttk.Button(user_frame, text="Logout", command=self.logout)
        logout_button.pack(side=tk.LEFT, padx=5)
    
    def create_sidebar(self, parent):
        """Create the sidebar navigation"""
        sidebar = ttk.Frame(parent, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        sidebar.pack_propagate(False)
        
        # Navigation buttons
        ttk.Button(sidebar, text="Dashboard", command=self.show_dashboard).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="New Order", command=self.show_new_order).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="Orders", command=self.show_orders).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="Menu", command=self.show_menu).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="Tables", command=self.show_tables).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="Inventory", command=self.show_inventory).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="KOT", command=self.show_kot).pack(fill=tk.X, pady=5)
        ttk.Button(sidebar, text="Reports", command=self.show_reports).pack(fill=tk.X, pady=5)
        
        # Settings button (only for admin)
        if self.current_user['role'] == 'Admin':
            ttk.Button(sidebar, text="Settings", command=self.show_settings).pack(fill=tk.X, pady=5)
    
    def clear_content_frame(self):
        """Clear all widgets from the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Display the dashboard"""
        self.clear_content_frame()
        
        # Set up dashboard shortcuts
        self.setup_dashboard_shortcuts()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Dashboard", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get today's stats
        self.cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?", (today,))
        total_orders = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(total) FROM orders WHERE DATE(created_at) = ?", (today,))
        today_sales = self.cursor.fetchone()[0] or 0
        
        self.cursor.execute("SELECT SUM(oi.quantity) FROM order_items oi JOIN orders o ON oi.order_id = o.id WHERE DATE(o.created_at) = ?", (today,))
        items_sold = self.cursor.fetchone()[0] or 0
        
        # Create stats frame
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Today's Sales
        sales_frame = ttk.LabelFrame(stats_frame, text="Today's Sales", padding=20)
        sales_frame.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W+tk.E)
        
        sales_label = ttk.Label(sales_frame, text=f"{self.settings.get('currency_symbol', '₹')}{today_sales:.2f}",
                              font=('Arial', 24, 'bold'))
        sales_label.pack()
        
        # Total Orders
        orders_frame = ttk.LabelFrame(stats_frame, text="Total Orders", padding=20)
        orders_frame.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        
        orders_label = ttk.Label(orders_frame, text=str(total_orders), font=('Arial', 24, 'bold'))
        orders_label.pack()
        
        # Items Sold
        items_frame = ttk.LabelFrame(stats_frame, text="Items Sold", padding=20)
        items_frame.grid(row=0, column=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        items_label = ttk.Label(items_frame, text=str(items_sold), font=('Arial', 24, 'bold'))
        items_label.pack()
        
        # Configure grid weights
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)
        
        # Quick access buttons with keyboard shortcuts hints
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Create buttons with shortcuts in labels
        new_order_btn = ttk.Button(buttons_frame, text="New Order (1)", command=self.show_new_order)
        new_order_btn.grid(row=0, column=0, padx=5, pady=5)
        
        view_orders_btn = ttk.Button(buttons_frame, text="View Orders (2)", command=self.show_orders)
        view_orders_btn.grid(row=0, column=1, padx=5, pady=5)
        
        menu_mgmt_btn = ttk.Button(buttons_frame, text="Menu Management (3)", command=self.show_menu)
        menu_mgmt_btn.grid(row=0, column=2, padx=5, pady=5)
    
    def show_new_order(self):
        """Display the new order screen"""
        self.clear_content_frame()
        
        # Reset current order
        self.current_order = None
        self.cart_items = []
        self.selected_table = None
        self.order_type = "Dine-in"
        
        # Title
        title_label = ttk.Label(self.content_frame, text="New Order", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create order frame
        order_frame = ttk.Frame(self.content_frame)
        order_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Order details
        left_panel = ttk.Frame(order_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Order type
        order_type_frame = ttk.LabelFrame(left_panel, text="Order Type", padding=10)
        order_type_frame.pack(fill=tk.X, pady=5)
        
        self.order_type_var = tk.StringVar(value="Dine-in")
        ttk.Radiobutton(order_type_frame, text="Dine-in", variable=self.order_type_var, 
                       value="Dine-in", command=self.change_order_type).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(order_type_frame, text="Takeaway", variable=self.order_type_var, 
                       value="Takeaway", command=self.change_order_type).pack(side=tk.LEFT, padx=10)
        
        # Table selection (for dine-in)
        self.table_frame = ttk.LabelFrame(left_panel, text="Table Selection", padding=10)
        self.table_frame.pack(fill=tk.X, pady=5)
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(self.table_frame, textvariable=self.table_var, state="readonly")
        self.table_combo.pack(fill=tk.X, pady=5)
        self.table_combo.bind("<<ComboboxSelected>>", self.select_table)
        
        # Customer details (for takeaway)
        self.customer_frame = ttk.LabelFrame(left_panel, text="Customer Details", padding=10)
        self.customer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.customer_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customer_name_entry = ttk.Entry(self.customer_frame)
        self.customer_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(self.customer_frame, text="Mobile:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.customer_mobile_entry = ttk.Entry(self.customer_frame)
        self.customer_mobile_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        self.customer_frame.columnconfigure(1, weight=1)
        
        # Initially hide customer frame
        self.customer_frame.pack_forget()
        
        # Menu items
        menu_frame = ttk.LabelFrame(left_panel, text="Menu Items", padding=10)
        menu_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Search bar
        search_frame = ttk.Frame(menu_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_menu)
        
        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu)
        
        # Menu items treeview
        self.menu_tree = ttk.Treeview(menu_frame, columns=("name", "price", "stock"), show="headings")
        self.menu_tree.heading("name", text="Name")
        self.menu_tree.heading("price", text="Price")
        self.menu_tree.heading("stock", text="Stock")
        
        self.menu_tree.column("name", width=200)
        self.menu_tree.column("price", width=100)
        self.menu_tree.column("stock", width=100)
        
        self.menu_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar for menu tree
        menu_scrollbar = ttk.Scrollbar(menu_frame, orient=tk.VERTICAL, command=self.menu_tree.yview)
        menu_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.menu_tree.configure(yscrollcommand=menu_scrollbar.set)
        
        # Add to cart button
        add_to_cart_button = ttk.Button(menu_frame, text="Add to Cart (F1)", command=self.add_to_cart)
        add_to_cart_button.pack(pady=5)
        
        # Right panel - Cart
        right_panel = ttk.Frame(order_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Cart items
        cart_frame = ttk.LabelFrame(right_panel, text="Cart", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Cart treeview
        self.cart_tree = ttk.Treeview(cart_frame, columns=("name", "price", "quantity", "total"), show="headings")
        self.cart_tree.heading("name", text="Item")
        self.cart_tree.heading("price", text="Price")
        self.cart_tree.heading("quantity", text="Quantity")
        self.cart_tree.heading("total", text="Total")
        
        self.cart_tree.column("name", width=200)
        self.cart_tree.column("price", width=100)
        self.cart_tree.column("quantity", width=100)
        self.cart_tree.column("total", width=100)
        
        self.cart_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Cart buttons
        cart_buttons_frame = ttk.Frame(cart_frame)
        cart_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(cart_buttons_frame, text="Update Quantity (F2)", command=self.update_cart_quantity).pack(side=tk.LEFT, padx=5)
        ttk.Button(cart_buttons_frame, text="Remove Item (F3)", command=self.remove_from_cart).pack(side=tk.LEFT, padx=5)
        ttk.Button(cart_buttons_frame, text="Clear Cart (F4)", command=self.clear_cart).pack(side=tk.LEFT, padx=5)
        
        # Order summary
        summary_frame = ttk.LabelFrame(right_panel, text="Order Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=5)
        
        # Subtotal
        self.subtotal_label = ttk.Label(summary_frame, text="Subtotal: ₹0.00")
        self.subtotal_label.pack(anchor=tk.W, pady=2)
        
        # Tax
        self.tax_label = ttk.Label(summary_frame, text=f"Tax ({self.settings.get('tax_rate', '5')}%): ₹0.00")
        self.tax_label.pack(anchor=tk.W, pady=2)
        
        # Discount
        discount_frame = ttk.Frame(summary_frame)
        discount_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(discount_frame, text="Discount:").pack(side=tk.LEFT)
        self.discount_var = tk.StringVar(value="0")
        self.discount_entry = ttk.Entry(discount_frame, textvariable=self.discount_var, width=10)
        self.discount_entry.pack(side=tk.LEFT, padx=5)
        
        self.discount_type_var = tk.StringVar(value="%")
        ttk.Radiobutton(discount_frame, text="%", variable=self.discount_type_var, 
                       value="%").pack(side=tk.LEFT)
        ttk.Radiobutton(discount_frame, text="Flat", variable=self.discount_type_var, 
                       value="Flat").pack(side=tk.LEFT)
        
        self.discount_entry.bind("<KeyRelease>", self.calculate_totals)
        self.discount_type_var.trace("w", lambda *args: self.calculate_totals())
        
        # Total
        self.total_label = ttk.Label(summary_frame, text="Total: ₹0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(anchor=tk.W, pady=2)
        
        # Payment buttons
        payment_frame = ttk.Frame(right_panel)
        payment_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(payment_frame, text="Cash Payment (Ctrl+Enter)", command=self.process_cash_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(payment_frame, text="Card Payment", command=self.process_card_payment).pack(side=tk.LEFT, padx=5)
        ttk.Button(payment_frame, text="UPI Payment", command=self.process_upi_payment).pack(side=tk.LEFT, padx=5)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.menu_tree)
        self.enhance_treeview_navigation(self.cart_tree)
        
        # Set up form navigation
        self.setup_form_navigation(self.customer_frame)
        self.setup_form_navigation(discount_frame)
        
        # Load initial data
        self.load_tables()
        self.load_categories()
        self.load_menu_items()
    
    def change_order_type(self):
        """Handle order type change"""
        self.order_type = self.order_type_var.get()
        
        if self.order_type == "Dine-in":
            self.table_frame.pack(fill=tk.X, pady=5)
            self.customer_frame.pack_forget()
        else:  # Takeaway
            self.table_frame.pack_forget()
            self.customer_frame.pack(fill=tk.X, pady=5)
    
    def load_tables(self):
        """Load available tables"""
        self.cursor.execute("SELECT id, table_number FROM tables WHERE status = 'Available' ORDER BY table_number")
        tables = self.cursor.fetchall()
        
        table_list = [f"{table[1]} (ID: {table[0]})" for table in tables]
        self.table_combo['values'] = table_list
        
        if table_list:
            self.table_combo.current(0)
            self.select_table()
    
    def select_table(self, event=None):
        """Handle table selection"""
        selection = self.table_var.get()
        if selection:
            # Extract table ID from selection
            table_id = selection.split("(ID: ")[1].rstrip(")")
            self.selected_table = int(table_id)
    
    def load_categories(self):
        """Load menu categories"""
        self.cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = self.cursor.fetchall()
        
        category_list = ["All"] + [category[0] for category in categories]
        self.category_combo['values'] = category_list
        self.category_combo.current(0)
    
    def load_menu_items(self, search_term="", category="All"):
        """Load menu items"""
        query = "SELECT mi.id, mi.name, mi.price, mi.stock_quantity, c.name FROM menu_items mi JOIN categories c ON mi.category_id = c.id"
        params = []
        
        if search_term:
            query += " WHERE mi.name LIKE ?"
            params.append(f"%{search_term}%")
            
            if category != "All":
                query += " AND c.name = ?"
                params.append(category)
        elif category != "All":
            query += " WHERE c.name = ?"
            params.append(category)
        
        query += " ORDER BY c.name, mi.name"
        
        self.cursor.execute(query, params)
        items = self.cursor.fetchall()
        
        # Clear tree
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, price, stock, category = item
            self.menu_tree.insert("", tk.END, values=(name, f"₹{price:.2f}", stock), tags=(item_id,))
    
    def search_menu(self, event=None):
        """Search menu items"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items(search_term, category)
    
    def filter_menu(self, event=None):
        """Filter menu items by category"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items(search_term, category)
    
    def add_to_cart(self):
        """Add selected menu item to cart"""
        selection = self.menu_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to add to cart")
            return
        
        # Get selected item
        item = self.menu_tree.item(selection[0])
        values = item['values']
        item_name = values[0]
        item_price = float(values[1].replace("₹", ""))
        item_stock = int(values[2])
        
        # Get item ID from tags
        item_id = int(self.menu_tree.item(selection[0])['tags'][0])
        
        # Check if item is in stock
        if item_stock <= 0:
            messagebox.showwarning("Warning", f"{item_name} is out of stock")
            return
        
        # Ask for quantity
        quantity = simpledialog.askinteger("Quantity", f"Enter quantity for {item_name}:", 
                                           minvalue=1, maxvalue=item_stock)
        if not quantity:
            return
        
        # Check if item already in cart
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                # Update quantity
                new_quantity = cart_item['quantity'] + quantity
                if new_quantity > item_stock:
                    messagebox.showwarning("Warning", f"Only {item_stock} items available in stock")
                    return
                
                cart_item['quantity'] = new_quantity
                cart_item['total'] = cart_item['price'] * new_quantity
                break
        else:
            # Add new item to cart
            self.cart_items.append({
                'id': item_id,
                'name': item_name,
                'price': item_price,
                'quantity': quantity,
                'total': item_price * quantity
            })
        
        # Update cart display
        self.update_cart_display()
    
    def update_cart_display(self):
        """Update the cart display"""
        # Clear cart tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add items to cart tree
        for cart_item in self.cart_items:
            self.cart_tree.insert("", tk.END, values=(
                cart_item['name'],
                f"₹{cart_item['price']:.2f}",
                cart_item['quantity'],
                f"₹{cart_item['total']:.2f}"
            ), tags=(cart_item['id'],))
        
        # Calculate totals
        self.calculate_totals()
    
    def calculate_totals(self, *args):
        """Calculate order totals"""
        subtotal = sum(item['total'] for item in self.cart_items)
        tax_rate = float(self.settings.get('tax_rate', 5)) / 100
        tax = subtotal * tax_rate
        
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
            
            if discount_type == "%":
                discount = subtotal * (discount_value / 100)
            else:  # Flat
                discount = discount_value
        except ValueError:
            discount = 0
        
        total = subtotal + tax - discount
        
        # Update labels
        self.subtotal_label.config(text=f"Subtotal: ₹{subtotal:.2f}")
        self.tax_label.config(text=f"Tax ({self.settings.get('tax_rate', '5')}%): ₹{tax:.2f}")
        self.total_label.config(text=f"Total: ₹{total:.2f}")
    
    def update_cart_quantity(self):
        """Update quantity of selected cart item"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
        
        # Get selected item
        item = self.cart_tree.item(selection[0])
        values = item['values']
        item_name = values[0]
        
        # Get item ID from tags
        item_id = int(self.cart_tree.item(selection[0])['tags'][0])
        
        # Find item in cart
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                # Get current stock
                self.cursor.execute("SELECT stock_quantity FROM menu_items WHERE id = ?", (item_id,))
                stock = self.cursor.fetchone()[0]
                
                # Ask for new quantity
                new_quantity = simpledialog.askinteger("Update Quantity", 
                                                      f"Enter new quantity for {item_name}:", 
                                                      minvalue=1, maxvalue=stock)
                if new_quantity:
                    cart_item['quantity'] = new_quantity
                    cart_item['total'] = cart_item['price'] * new_quantity
                    self.update_cart_display()
                break
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove")
            return
        
        # Get item ID from tags
        item_id = int(self.cart_tree.item(selection[0])['tags'][0])
        
        # Remove item from cart
        self.cart_items = [item for item in self.cart_items if item['id'] != item_id]
        
        # Update cart display
        self.update_cart_display()
    
    def clear_cart(self):
        """Clear all items from cart"""
        if not self.cart_items:
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the cart?"):
            self.cart_items = []
            self.update_cart_display()
    
    def process_payment(self, payment_mode):
        """Process payment for the order"""
        if not self.cart_items:
            messagebox.showwarning("Warning", "Cart is empty. Please add items to the cart.")
            return
        
        if self.order_type == "Dine-in" and not self.selected_table:
            messagebox.showwarning("Warning", "Please select a table.")
            return
        
        # Calculate totals
        subtotal = sum(item['total'] for item in self.cart_items)
        tax_rate = float(self.settings.get('tax_rate', 5)) / 100
        tax = subtotal * tax_rate
        
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
            
            if discount_type == "%":
                discount = subtotal * (discount_value / 100)
            else:  # Flat
                discount = discount_value
        except ValueError:
            discount = 0
        
        total = subtotal + tax - discount
        
        # Generate order number
        order_number = "ORD" + datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Get customer details for takeaway
        customer_name = None
        customer_mobile = None
        if self.order_type == "Takeaway":
            customer_name = self.customer_name_entry.get()
            customer_mobile = self.customer_mobile_entry.get()
        
        # Create order in database
        self.cursor.execute("""
        INSERT INTO orders (order_number, table_id, customer_name, customer_mobile, order_type, 
                           subtotal, tax, discount, total, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_number, self.selected_table, customer_name, customer_mobile, self.order_type,
              subtotal, tax, discount, total, "Completed"))
        
        order_id = self.cursor.lastrowid
        
        # Add order items
        for cart_item in self.cart_items:
            self.cursor.execute("""
            INSERT INTO order_items (order_id, menu_item_id, quantity, price, total, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, cart_item['id'], cart_item['quantity'], cart_item['price'], 
                  cart_item['total'], "Completed"))
            
            # Update inventory
            self.cursor.execute("""
            UPDATE menu_items SET stock_quantity = stock_quantity - ? WHERE id = ?
            """, (cart_item['quantity'], cart_item['id']))
        
        # Add payment record
        self.cursor.execute("""
        INSERT INTO payments (order_id, payment_mode, amount)
        VALUES (?, ?, ?)
        """, (order_id, payment_mode, total))
        
        # Update table status if dine-in
        if self.order_type == "Dine-in":
            self.cursor.execute("""
            UPDATE tables SET status = 'Occupied' WHERE id = ?
            """, (self.selected_table,))
        
        # Commit changes
        self.conn.commit()
        
        # Generate bill
        self.generate_bill(order_id)
        
        # Show success message
        messagebox.showinfo("Success", f"Order {order_number} completed successfully!")
        
        # Reset order
        self.show_new_order()
    
    def process_cash_payment(self):
        """Process cash payment"""
        # Calculate total
        subtotal = sum(item['total'] for item in self.cart_items)
        tax_rate = float(self.settings.get('tax_rate', 5)) / 100
        tax = subtotal * tax_rate
        
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
            
            if discount_type == "%":
                discount = subtotal * (discount_value / 100)
            else:  # Flat
                discount = discount_value
        except ValueError:
            discount = 0
        
        total = subtotal + tax - discount
        
        # Ask for cash amount
        cash_amount = simpledialog.askfloat("Cash Payment", f"Total amount: ₹{total:.2f}\nEnter cash amount:", 
                                           minvalue=total)
        if cash_amount:
            change = cash_amount - total
            messagebox.showinfo("Payment", f"Payment successful!\nCash received: ₹{cash_amount:.2f}\nChange: ₹{change:.2f}")
            self.process_payment("Cash")
    
    def process_card_payment(self):
        """Process card payment"""
        # Ask for card details
        card_details = simpledialog.askstring("Card Payment", "Enter last 4 digits of card:")
        if card_details:
            messagebox.showinfo("Payment", f"Card payment successful!\nCard ending in: {card_details}")
            self.process_payment("Card")
    
    def process_upi_payment(self):
        """Process UPI payment"""
        # Ask for UPI ID
        upi_id = simpledialog.askstring("UPI Payment", "Enter UPI ID:")
        if upi_id:
            messagebox.showinfo("Payment", f"UPI payment successful!\nUPI ID: {upi_id}")
            self.process_payment("UPI")
    
    def generate_bill(self, order_id):
        """Generate bill for the order"""
        # Get order details
        self.cursor.execute("""
        SELECT o.order_number, o.table_id, o.customer_name, o.customer_mobile, o.order_type, 
               o.subtotal, o.tax, o.discount, o.total, o.created_at
        FROM orders o
        WHERE o.id = ?
        """, (order_id,))
        order = self.cursor.fetchone()
        
        if not order:
            return
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, discount, total, created_at = order
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            self.cursor.execute("SELECT table_number FROM tables WHERE id = ?", (table_id,))
            table_result = self.cursor.fetchone()
            if table_result:
                table_number = table_result[0]
        
        # Get order items
        self.cursor.execute("""
        SELECT mi.name, oi.quantity, oi.price, oi.total
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """, (order_id,))
        items = self.cursor.fetchall()
        
        # Create bill content
        bill_content = f"""
{self.settings.get('restaurant_name', 'My Restaurant')}
{self.settings.get('restaurant_address', '123 Main Street, City')}
{'='*40}
BILL
{'='*40}
Order No: {order_number}
Date: {created_at}
Order Type: {order_type}
"""
        
        if order_type == "Dine-in" and table_number:
            bill_content += f"Table: {table_number}\n"
        elif order_type == "Takeaway" and customer_name:
            bill_content += f"Customer: {customer_name}\n"
            if customer_mobile:
                bill_content += f"Mobile: {customer_mobile}\n"
        
        bill_content += f"""
{'='*40}
{'Item':<20} {'Qty':<5} {'Price':<10} {'Total':<10}
{'-'*50}
"""
        
        for item in items:
            name, quantity, price, item_total = item
            bill_content += f"{name:<20} {quantity:<5} ₹{price:<9.2f} ₹{item_total:<9.2f}\n"
        
        bill_content += f"""
{'-'*50}
Subtotal: ₹{subtotal:.2f}
Tax ({self.settings.get('tax_rate', '5')}%): ₹{tax:.2f}
Discount: ₹{discount:.2f}
{'='*50}
Total: ₹{total:.2f}
{'='*50}
Thank you for dining with us!
"""
        
        # Save bill to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"Bill_{order_number}.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bill_content)
            messagebox.showinfo("Bill Saved", f"Bill saved to {file_path}")
    
    def show_orders(self):
        """Display the orders screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Orders", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.content_frame)
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
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.order_search_entry = ttk.Entry(search_frame)
        self.order_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.order_search_entry.bind("<KeyRelease>", self.search_orders)
        
        # Orders tree
        orders_frame = ttk.Frame(self.content_frame)
        orders_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.orders_tree = ttk.Treeview(orders_frame, columns=("order_number", "date", "type", "table", "total", "status"), show="headings")
        self.orders_tree.heading("order_number", text="Order No")
        self.orders_tree.heading("date", text="Date")
        self.orders_tree.heading("type", text="Type")
        self.orders_tree.heading("table", text="Table")
        self.orders_tree.heading("total", text="Total")
        self.orders_tree.heading("status", text="Status")
        
        self.orders_tree.column("order_number", width=120)
        self.orders_tree.column("date", width=150)
        self.orders_tree.column("type", width=80)
        self.orders_tree.column("table", width=80)
        self.orders_tree.column("total", width=100)
        self.orders_tree.column("status", width=100)
        
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        orders_scrollbar = ttk.Scrollbar(orders_frame, orient=tk.VERTICAL, command=self.orders_tree.yview)
        orders_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.orders_tree.configure(yscrollcommand=orders_scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="View Details", command=self.view_order_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Print Bill", command=self.print_bill).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.refresh_orders).pack(side=tk.LEFT, padx=5)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.orders_tree)
        
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
        
        query = """
        SELECT o.id, o.order_number, o.created_at, o.order_type, t.table_number, 
               o.total, o.status, o.customer_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE 1=1
        """
        params = []
        
        # Apply filter
        if filter_value == "Today":
            query += " AND DATE(o.created_at) = DATE('now')"
        elif filter_value == "This Week":
            query += " AND o.created_at >= DATE('now', '-7 days')"
        elif filter_value == "This Month":
            query += " AND o.created_at >= DATE('now', '-30 days')"
        
        # Apply search
        if search_term:
            query += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR t.table_number LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY o.created_at DESC"
        
        self.cursor.execute(query, params)
        orders = self.cursor.fetchall()
        
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
            messagebox.showwarning("Warning", "Please select an order to view details")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Create order details window
        details_window = tk.Toplevel(self.root)
        details_window.title("Order Details")
        details_window.geometry("600x500")
        
        # Get order details
        self.cursor.execute("""
        SELECT o.order_number, o.table_id, o.customer_name, o.customer_mobile, o.order_type, 
               o.subtotal, o.tax, o.discount, o.total, o.created_at, o.status
        FROM orders o
        WHERE o.id = ?
        """, (order_id,))
        order = self.cursor.fetchone()
        
        if not order:
            return
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, discount, total, created_at, status = order
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            self.cursor.execute("SELECT table_number FROM tables WHERE id = ?", (table_id,))
            table_result = self.cursor.fetchone()
            if table_result:
                table_number = table_result[0]
        
        # Get order items
        self.cursor.execute("""
        SELECT mi.name, oi.quantity, oi.price, oi.total, oi.status
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """, (order_id,))
        items = self.cursor.fetchall()
        
        # Get payment details
        self.cursor.execute("""
        SELECT payment_mode, amount, created_at
        FROM payments
        WHERE order_id = ?
        """, (order_id,))
        payments = self.cursor.fetchall()
        
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
        
        items_tree = ttk.Treeview(items_frame, columns=("name", "quantity", "price", "total", "status"), show="headings")
        items_tree.heading("name", text="Item")
        items_tree.heading("quantity", text="Quantity")
        items_tree.heading("price", text="Price")
        items_tree.heading("total", text="Total")
        items_tree.heading("status", text="Status")
        
        items_tree.column("name", width=150)
        items_tree.column("quantity", width=80)
        items_tree.column("price", width=80)
        items_tree.column("total", width=80)
        items_tree.column("status", width=80)
        
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
        
        ttk.Label(summary_frame, text=f"Subtotal: ₹{subtotal:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Tax ({self.settings.get('tax_rate', '5')}%): ₹{tax:.2f}").pack(anchor=tk.W, pady=2)
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
            messagebox.showwarning("Warning", "Please select an order to print bill")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Generate bill
        self.generate_bill(order_id)
    
    def refresh_orders(self):
        """Refresh orders list"""
        self.load_orders()
    
    def show_menu(self):
        """Display the menu management screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Menu Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create menu frame
        menu_frame = ttk.Frame(self.content_frame)
        menu_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Menu items
        left_panel = ttk.Frame(menu_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Search and filter
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.menu_search_entry = ttk.Entry(search_frame)
        self.menu_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.menu_search_entry.bind("<KeyRelease>", self.search_menu_items)
        
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.menu_category_var = tk.StringVar()
        self.menu_category_combo = ttk.Combobox(search_frame, textvariable=self.menu_category_var, state="readonly")
        self.menu_category_combo.pack(side=tk.LEFT, padx=5)
        self.menu_category_combo.bind("<<ComboboxSelected>>", self.filter_menu_items)
        
        # Menu items tree
        self.menu_items_tree = ttk.Treeview(left_panel, columns=("name", "category", "price", "stock"), show="headings")
        self.menu_items_tree.heading("name", text="Name")
        self.menu_items_tree.heading("category", text="Category")
        self.menu_items_tree.heading("price", text="Price")
        self.menu_items_tree.heading("stock", text="Stock")
        
        self.menu_items_tree.column("name", width=200)
        self.menu_items_tree.column("category", width=150)
        self.menu_items_tree.column("price", width=100)
        self.menu_items_tree.column("stock", width=100)
        
        self.menu_items_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar for menu items tree
        menu_items_scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.menu_items_tree.yview)
        menu_items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.menu_items_tree.configure(yscrollcommand=menu_items_scrollbar.set)
        
        # Buttons
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(buttons_frame, text="Add Item", command=self.add_menu_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Edit Item", command=self.edit_menu_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Delete Item", command=self.delete_menu_item).pack(side=tk.LEFT, padx=5)
        
        # Right panel - Categories
        right_panel = ttk.Frame(menu_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Categories frame
        categories_frame = ttk.LabelFrame(right_panel, text="Categories", padding=10)
        categories_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Categories tree
        self.categories_tree = ttk.Treeview(categories_frame, columns=("name",), show="headings")
        self.categories_tree.heading("name", text="Name")
        self.categories_tree.column("name", width=200)
        
        self.categories_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Category buttons
        category_buttons_frame = ttk.Frame(categories_frame)
        category_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(category_buttons_frame, text="Add Category", command=self.add_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(category_buttons_frame, text="Edit Category", command=self.edit_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(category_buttons_frame, text="Delete Category", command=self.delete_category).pack(side=tk.LEFT, padx=5)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.menu_items_tree)
        self.enhance_treeview_navigation(self.categories_tree)
        
        # Load data
        self.load_menu_categories()
        self.load_menu_items_management()
    
    def load_menu_categories(self):
        """Load menu categories"""
        self.cursor.execute("SELECT id, name FROM categories ORDER BY name")
        categories = self.cursor.fetchall()
        
        # Clear categories tree
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        
        # Add categories to tree
        for category in categories:
            self.categories_tree.insert("", tk.END, values=(category[1],), tags=(category[0],))
        
        # Update category combo
        category_list = ["All"] + [category[1] for category in categories]
        self.menu_category_combo['values'] = category_list
        self.menu_category_combo.current(0)
    
    def load_menu_items_management(self, search_term="", category="All"):
        """Load menu items for menu management screen"""
        query = """
        SELECT mi.id, mi.name, c.name, mi.price, mi.stock_quantity
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE 1=1
        """
        params = []
        
        if search_term:
            query += " AND mi.name LIKE ?"
            params.append(f"%{search_term}%")
            
            if category != "All":
                query += " AND c.name = ?"
                params.append(category)
        elif category != "All":
            query += " AND c.name = ?"
            params.append(category)
        
        query += " ORDER BY c.name, mi.name"
        
        self.cursor.execute(query, params)
        items = self.cursor.fetchall()
        
        # Clear menu items tree
        for item in self.menu_items_tree.get_children():
            self.menu_items_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, category, price, stock = item
            self.menu_items_tree.insert("", tk.END, values=(
                name,
                category,
                f"₹{price:.2f}",
                stock
            ), tags=(item_id,))
    
    def search_menu_items(self, event=None):
        """Search menu items"""
        search_term = self.menu_search_entry.get()
        category = self.menu_category_var.get()
        self.load_menu_items_management(search_term, category)
    
    def filter_menu_items(self, event=None):
        """Filter menu items by category"""
        search_term = self.menu_search_entry.get()
        category = self.menu_category_var.get()
        self.load_menu_items_management(search_term, category)
    
    def add_menu_item(self):
        """Add a new menu item"""
        # Create add item window
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Menu Item")
        add_window.geometry("400x400")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, state="readonly", width=28)
        category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Load categories
        self.cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in self.cursor.fetchall()]
        category_combo['values'] = categories
        if categories:
            category_combo.current(0)
        
        # Price
        ttk.Label(form_frame, text="Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Stock
        ttk.Label(form_frame, text="Stock Quantity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_entry = ttk.Entry(form_frame, width=30)
        stock_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Image path
        ttk.Label(form_frame, text="Image Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
        image_path_var = tk.StringVar()
        image_path_entry = ttk.Entry(form_frame, textvariable=image_path_var, width=30)
        image_path_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")]
            )
            if file_path:
                image_path_var.set(file_path)
        
        ttk.Button(form_frame, text="Browse", command=browse_image).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Set up form navigation
        self.setup_form_navigation(form_frame)
        
        def save_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            
            if not name or not category or not price or not stock:
                messagebox.showwarning("Warning", "Please fill in all required fields")
                return
            
            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                messagebox.showwarning("Warning", "Price must be a number and Stock must be an integer")
                return
            
            # Get category ID
            self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_result = self.cursor.fetchone()
            if not category_result:
                messagebox.showwarning("Warning", "Invalid category")
                return
            
            category_id = category_result[0]
            
            # Insert menu item
            self.cursor.execute("""
            INSERT INTO menu_items (name, price, category_id, stock_quantity, image_path)
            VALUES (?, ?, ?, ?, ?)
            """, (name, price, category_id, stock, image_path))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Menu item added successfully")
            add_window.destroy()
            self.load_menu_items()
        
        ttk.Button(buttons_frame, text="Save", command=save_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def edit_menu_item(self):
        """Edit selected menu item"""
        selection = self.menu_items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return
        
        # Get item ID from tags
        item_id = int(self.menu_items_tree.item(selection[0])['tags'][0])
        
        # Get item details
        self.cursor.execute("""
        SELECT mi.name, mi.price, mi.category_id, mi.stock_quantity, mi.image_path, c.name
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE mi.id = ?
        """, (item_id,))
        item = self.cursor.fetchone()
        
        if not item:
            return
        
        name, price, category_id, stock, image_path, category_name = item
        
        # Create edit item window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Menu Item")
        edit_window.geometry("400x400")
        
        # Create form
        form_frame = ttk.Frame(edit_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        name_entry.insert(0, name)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar(value=category_name)
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, state="readonly", width=28)
        category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Load categories
        self.cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in self.cursor.fetchall()]
        category_combo['values'] = categories
        
        # Price
        ttk.Label(form_frame, text="Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        price_entry.insert(0, str(price))
        
        # Stock
        ttk.Label(form_frame, text="Stock Quantity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_entry = ttk.Entry(form_frame, width=30)
        stock_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        stock_entry.insert(0, str(stock))
        
        # Image path
        ttk.Label(form_frame, text="Image Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
        image_path_var = tk.StringVar(value=image_path or "")
        image_path_entry = ttk.Entry(form_frame, textvariable=image_path_var, width=30)
        image_path_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")]
            )
            if file_path:
                image_path_var.set(file_path)
        
        ttk.Button(form_frame, text="Browse", command=browse_image).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        # Set up form navigation
        self.setup_form_navigation(form_frame)
        
        def update_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            
            if not name or not category or not price or not stock:
                messagebox.showwarning("Warning", "Please fill in all required fields")
                return
            
            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                messagebox.showwarning("Warning", "Price must be a number and Stock must be an integer")
                return
            
            # Get category ID
            self.cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            category_result = self.cursor.fetchone()
            if not category_result:
                messagebox.showwarning("Warning", "Invalid category")
                return
            
            new_category_id = category_result[0]
            
            # Update menu item
            self.cursor.execute("""
            UPDATE menu_items 
            SET name = ?, price = ?, category_id = ?, stock_quantity = ?, image_path = ?
            WHERE id = ?
            """, (name, price, new_category_id, stock, image_path, item_id))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Menu item updated successfully")
            edit_window.destroy()
            self.load_menu_items()
        
        ttk.Button(buttons_frame, text="Update", command=update_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_menu_item(self):
        """Delete selected menu item"""
        selection = self.menu_items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        # Get item ID from tags
        item_id = int(self.menu_items_tree.item(selection[0])['tags'][0])
        
        # Get item name
        item = self.menu_items_tree.item(selection[0])
        item_name = item['values'][0]
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {item_name}?"):
            # Delete menu item
            self.cursor.execute("DELETE FROM menu_items WHERE id = ?", (item_id,))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Menu item deleted successfully")
            self.load_menu_items()
    
    def add_category(self):
        """Add a new category"""
        # Create add category window
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Category")
        add_window.geometry("300x150")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=10)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Set up form navigation
        self.setup_form_navigation(form_frame)
        
        def save_category():
            name = name_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Warning", "Please enter a category name")
                return
            
            # Insert category
            try:
                self.cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                self.conn.commit()
                
                messagebox.showinfo("Success", "Category added successfully")
                add_window.destroy()
                self.load_menu_categories()
                self.load_menu_items()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category already exists")
        
        ttk.Button(buttons_frame, text="Save", command=save_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def edit_category(self):
        """Edit selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to edit")
            return
        
        # Get category ID from tags
        category_id = int(self.categories_tree.item(selection[0])['tags'][0])
        
        # Get category name
        category = self.categories_tree.item(selection[0])
        category_name = category['values'][0]
        
        # Create edit category window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Category")
        edit_window.geometry("300x150")
        
        # Create form
        form_frame = ttk.Frame(edit_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=10)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        name_entry.insert(0, category_name)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Set up form navigation
        self.setup_form_navigation(form_frame)
        
        def update_category():
            name = name_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Warning", "Please enter a category name")
                return
            
            # Update category
            try:
                self.cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
                self.conn.commit()
                
                messagebox.showinfo("Success", "Category updated successfully")
                edit_window.destroy()
                self.load_menu_categories()
                self.load_menu_items()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category already exists")
        
        ttk.Button(buttons_frame, text="Update", command=update_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_category(self):
        """Delete selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a category to delete")
            return
        
        # Get category ID from tags
        category_id = int(self.categories_tree.item(selection[0])['tags'][0])
        
        # Get category name
        category = self.categories_tree.item(selection[0])
        category_name = category['values'][0]
        
        # Check if category is being used by menu items
        self.cursor.execute("SELECT COUNT(*) FROM menu_items WHERE category_id = ?", (category_id,))
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showwarning("Warning", f"Cannot delete category '{category_name}' as it is being used by {count} menu items")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {category_name}?"):
            # Delete category
            self.cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Category deleted successfully")
            self.load_menu_categories()
    
    def show_tables(self):
        """Display the tables management screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Table Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Add Table", command=self.add_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Edit Table", command=self.edit_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Delete Table", command=self.delete_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reset All Tables", command=self.reset_all_tables).pack(side=tk.LEFT, padx=5)
        
        # Tables frame
        tables_frame = ttk.Frame(self.content_frame)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create table grid
        self.table_buttons_frame = ttk.Frame(tables_frame)
        self.table_buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load tables
        self.load_tables_grid()
    
    def load_tables_grid(self):
        """Load tables in grid view"""
        # Clear existing widgets
        for widget in self.table_buttons_frame.winfo_children():
            widget.destroy()
        
        # Get tables
        self.cursor.execute("SELECT id, table_number, capacity, status FROM tables ORDER BY table_number")
        tables = self.cursor.fetchall()
        
        # Create table buttons in grid
        rows = 3
        cols = 4
        
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            
            row = i // cols
            col = i % cols
            
            # Create frame for table
            table_frame = ttk.Frame(self.table_buttons_frame, relief=tk.RAISED, borderwidth=2)
            table_frame.grid(row=row, column=col, padx=10, pady=10, sticky=tk.W+tk.E)
            
            # Table number
            table_label = ttk.Label(table_frame, text=table_number, font=('Arial', 14, 'bold'))
            table_label.pack(pady=5)
            
            # Table capacity
            capacity_label = ttk.Label(table_frame, text=f"Capacity: {capacity}")
            capacity_label.pack()
            
            # Table status
            status_label = ttk.Label(table_frame, text=status)
            status_label.pack(pady=5)
            
            # Set color based on status
            if status == "Available":
                table_frame.configure(style="Available.TFrame")
                status_label.configure(foreground="green")
            else:  # Occupied
                table_frame.configure(style="Occupied.TFrame")
                status_label.configure(foreground="red")
            
            # Add click event to toggle status
            def toggle_status(event, tid=table_id, tnum=table_number):
                # Get current status
                self.cursor.execute("SELECT status FROM tables WHERE id = ?", (tid,))
                current_status = self.cursor.fetchone()[0]
                
                # Toggle status
                new_status = "Occupied" if current_status == "Available" else "Available"
                
                # Update status
                self.cursor.execute("UPDATE tables SET status = ? WHERE id = ?", (new_status, tid))
                self.conn.commit()
                
                # Reload tables
                self.load_tables_grid()
                
                # Show message
                messagebox.showinfo("Table Status", f"Table {tnum} status changed to {new_status}")
            
            table_frame.bind("<Button-1>", toggle_status)
            table_label.bind("<Button-1>", toggle_status)
            capacity_label.bind("<Button-1>", toggle_status)
            status_label.bind("<Button-1>", toggle_status)
    
    def add_table(self):
        """Add a new table"""
        # Create add table window
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Table")
        add_window.geometry("300x200")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table number
        ttk.Label(form_frame, text="Table Number:").grid(row=0, column=0, sticky=tk.W, pady=10)
        table_number_entry = ttk.Entry(form_frame, width=30)
        table_number_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Capacity
        ttk.Label(form_frame, text="Capacity:").grid(row=1, column=0, sticky=tk.W, pady=10)
        capacity_entry = ttk.Entry(form_frame, width=30)
        capacity_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Set up form navigation
        self.setup_form_navigation(form_frame)
        
        def save_table():
            table_number = table_number_entry.get().strip()
            capacity = capacity_entry.get().strip()
            
            if not table_number or not capacity:
                messagebox.showwarning("Warning", "Please fill in all fields")
                return
            
            try:
                capacity = int(capacity)
            except ValueError:
                messagebox.showwarning("Warning", "Capacity must be a number")
                return
            
            # Insert table
            try:
                self.cursor.execute("INSERT INTO tables (table_number, capacity) VALUES (?, ?)", 
                                  (table_number, capacity))
                self.conn.commit()
                
                messagebox.showinfo("Success", "Table added successfully")
                add_window.destroy()
                self.load_tables_grid()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Table number already exists")
        
        ttk.Button(buttons_frame, text="Save", command=save_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)
    

    def edit_table(self):
        """Edit selected table"""
        # Create select table window
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Table to Edit")
        select_window.geometry("300x400")
        
        # Create form
        form_frame = ttk.Frame(select_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Select Table:").pack(anchor=tk.W, pady=5)
        
        # Table list
        table_listbox = tk.Listbox(form_frame, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load tables
        self.cursor.execute("SELECT id, table_number, capacity, status FROM tables ORDER BY table_number")
        tables = self.cursor.fetchall()
        
        table_data = {} # To store table info by index
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            table_listbox.insert(tk.END, f"{table_number} (Capacity: {capacity}, Status: {status})")
            table_data[i] = table

        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        def select_table_to_edit():
            selection = table_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a table")
                return
            
            index = selection[0]
            table_id, table_number, capacity, status = table_data[index]
            
            # Close select window
            select_window.destroy()
            
            # Create edit table window
            edit_window = tk.Toplevel(self.root)
            edit_window.title("Edit Table")
            edit_window.geometry("300x250")
            
            # Create form
            edit_form_frame = ttk.Frame(edit_window, padding="20")
            edit_form_frame.pack(fill=tk.BOTH, expand=True)
            
            # Table number
            ttk.Label(edit_form_frame, text="Table Number:").grid(row=0, column=0, sticky=tk.W, pady=10)
            table_number_entry = ttk.Entry(edit_form_frame, width=30)
            table_number_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
            table_number_entry.insert(0, table_number)
            
            # Capacity
            ttk.Label(edit_form_frame, text="Capacity:").grid(row=1, column=0, sticky=tk.W, pady=10)
            capacity_entry = ttk.Entry(edit_form_frame, width=30)
            capacity_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)
            capacity_entry.insert(0, str(capacity))
            
            # Status
            ttk.Label(edit_form_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=10)
            status_var = tk.StringVar(value=status)
            status_combo = ttk.Combobox(edit_form_frame, textvariable=status_var, values=["Available", "Occupied"], state="readonly", width=28)
            status_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)

            # Buttons
            edit_buttons_frame = ttk.Frame(edit_form_frame)
            edit_buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
            
            # Set up form navigation
            self.setup_form_navigation(edit_form_frame)
            
            def update_table():
                new_table_number = table_number_entry.get().strip()
                new_capacity = capacity_entry.get().strip()
                new_status = status_var.get()
                
                if not new_table_number or not new_capacity:
                    messagebox.showwarning("Warning", "Please fill in all fields")
                    return
                
                try:
                    new_capacity = int(new_capacity)
                except ValueError:
                    messagebox.showwarning("Warning", "Capacity must be a number")
                    return
                
                # Update table
                try:
                    self.cursor.execute("""
                    UPDATE tables 
                    SET table_number = ?, capacity = ?, status = ?
                    WHERE id = ?
                    """, (new_table_number, new_capacity, new_status, table_id))
                    self.conn.commit()
                    
                    messagebox.showinfo("Success", "Table updated successfully")
                    edit_window.destroy()
                    self.load_tables_grid()
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Table number already exists")
            
            ttk.Button(edit_buttons_frame, text="Update", command=update_table).pack(side=tk.LEFT, padx=5)
            ttk.Button(edit_buttons_frame, text="Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)

        ttk.Button(buttons_frame, text="Edit", command=select_table_to_edit).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=select_window.destroy).pack(side=tk.LEFT, padx=5)

    def delete_table(self):
        """Delete selected table"""
        # Create select table window
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Table to Delete")
        select_window.geometry("300x400")
        
        # Create form
        form_frame = ttk.Frame(select_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Select Table:").pack(anchor=tk.W, pady=5)
        
        # Table list
        table_listbox = tk.Listbox(form_frame, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load tables
        self.cursor.execute("SELECT id, table_number FROM tables ORDER BY table_number")
        tables = self.cursor.fetchall()
        
        table_data = {}
        for i, table in enumerate(tables):
            table_id, table_number = table
            table_listbox.insert(tk.END, f"{table_number}")
            table_data[i] = {'id': table_id, 'name': table_number}

        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        def select_table_to_delete():
            selection = table_listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a table")
                return
            
            index = selection[0]
            table_id = table_data[index]['id']
            table_name = table_data[index]['name']

            # Confirm deletion
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {table_name}? This action cannot be undone."):
                # Delete table
                self.cursor.execute("DELETE FROM tables WHERE id = ?", (table_id,))
                self.conn.commit()
                
                messagebox.showinfo("Success", "Table deleted successfully")
                select_window.destroy()
                self.load_tables_grid()

        ttk.Button(buttons_frame, text="Delete", command=select_table_to_delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=select_window.destroy).pack(side=tk.LEFT, padx=5)

    def reset_all_tables(self):
        """Reset status of all tables to Available"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all tables to 'Available'?"):
            self.cursor.execute("UPDATE tables SET status = 'Available'")
            self.conn.commit()
            messagebox.showinfo("Success", "All tables have been reset to 'Available'")
            self.load_tables_grid()

    def show_inventory(self):
        """Display the inventory management screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Inventory Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Search frame
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.inventory_search_entry = ttk.Entry(search_frame)
        self.inventory_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.inventory_search_entry.bind("<KeyRelease>", self.search_inventory)
        
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.inventory_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.inventory_filter_var, values=["All", "Low Stock", "Out of Stock"], state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_inventory)
        
        # Inventory tree
        inventory_frame = ttk.Frame(self.content_frame)
        inventory_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.inventory_tree = ttk.Treeview(inventory_frame, columns=("name", "category", "stock", "status"), show="headings")
        self.inventory_tree.heading("name", text="Item Name")
        self.inventory_tree.heading("category", text="Category")
        self.inventory_tree.heading("stock", text="Stock Quantity")
        self.inventory_tree.heading("status", text="Status")
        
        self.inventory_tree.column("name", width=200)
        self.inventory_tree.column("category", width=150)
        self.inventory_tree.column("stock", width=120)
        self.inventory_tree.column("status", width=120)
        
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        inventory_scrollbar = ttk.Scrollbar(inventory_frame, orient=tk.VERTICAL, command=self.inventory_tree.yview)
        inventory_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inventory_tree.configure(yscrollcommand=inventory_scrollbar.set)
        
        # Buttons
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Update Stock", command=self.update_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.load_inventory).pack(side=tk.LEFT, padx=5)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.inventory_tree)
        
        # Load inventory
        self.load_inventory()

    def load_inventory(self, search_term="", filter_type="All"):
        """Load inventory items"""
        query = """
        SELECT mi.id, mi.name, c.name, mi.stock_quantity
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE 1=1
        """
        params = []

        if search_term:
            query += " AND mi.name LIKE ?"
            params.append(f"%{search_term}%")

        if filter_type == "Low Stock":
            query += " AND mi.stock_quantity > 0 AND mi.stock_quantity <= 10"
        elif filter_type == "Out of Stock":
            query += " AND mi.stock_quantity = 0"

        query += " ORDER BY mi.stock_quantity ASC, mi.name"

        self.cursor.execute(query, params)
        items = self.cursor.fetchall()
        
        # Clear tree
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, category, stock = item
            
            if stock <= 0:
                status = "Out of Stock"
                tag = "out_of_stock"
            elif stock <= 10:
                status = "Low Stock"
                tag = "low_stock"
            else:
                status = "In Stock"
                tag = "in_stock"
            
            self.inventory_tree.insert("", tk.END, values=(name, category, stock, status), tags=(item_id, tag))
        
        # Configure tags for color coding
        self.inventory_tree.tag_configure("out_of_stock", background="#ffcccc")
        self.inventory_tree.tag_configure("low_stock", background="#ffffcc")
        self.inventory_tree.tag_configure("in_stock", background="#ccffcc")

    def search_inventory(self, event=None):
        """Search inventory items"""
        search_term = self.inventory_search_entry.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)

    def filter_inventory(self, event=None):
        """Filter inventory items"""
        search_term = self.inventory_search_entry.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)

    def update_stock(self):
        """Update stock for selected item"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to update stock")
            return
        
        # Get item ID from tags
        item_id = int(self.inventory_tree.item(selection[0])['tags'][0])
        
        # Get current stock
        item = self.inventory_tree.item(selection[0])
        current_stock = item['values'][2]
        
        # Ask for new stock
        new_stock = simpledialog.askinteger("Update Stock", 
                                           f"Enter new stock quantity (Current: {current_stock}):", 
                                           minvalue=0)
        if new_stock is not None:
            # Update stock in database
            self.cursor.execute("UPDATE menu_items SET stock_quantity = ? WHERE id = ?", 
                              (new_stock, item_id))
            self.conn.commit()
            
            messagebox.showinfo("Success", "Stock updated successfully")
            self.load_inventory()

    def show_kot(self):
        """Display the Kitchen Order Ticket screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Kitchen Order Tickets (KOT)", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.content_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.kot_filter_var = tk.StringVar(value="Pending")
        ttk.Radiobutton(filter_frame, text="Pending", variable=self.kot_filter_var, 
                       value="Pending", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Preparing", variable=self.kot_filter_var, 
                       value="Preparing", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Completed", variable=self.kot_filter_var, 
                       value="Completed", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        
        # KOT tree
        kot_frame = ttk.Frame(self.content_frame)
        kot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.kot_tree = ttk.Treeview(kot_frame, columns=("order_number", "item", "quantity", "time", "status"), show="headings")
        self.kot_tree.heading("order_number", text="Order #")
        self.kot_tree.heading("item", text="Item")
        self.kot_tree.heading("quantity", text="Quantity")
        self.kot_tree.heading("time", text="Time")
        self.kot_tree.heading("status", text="Status")
        
        self.kot_tree.column("order_number", width=100)
        self.kot_tree.column("item", width=200)
        self.kot_tree.column("quantity", width=80)
        self.kot_tree.column("time", width=120)
        self.kot_tree.column("status", width=100)
        
        self.kot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        kot_scrollbar = ttk.Scrollbar(kot_frame, orient=tk.VERTICAL, command=self.kot_tree.yview)
        kot_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.kot_tree.configure(yscrollcommand=kot_scrollbar.set)
        
        # Buttons
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Mark as Preparing", command=self.mark_kot_preparing).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Mark as Completed", command=self.mark_kot_completed).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Print KOT", command=self.print_kot).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.kot_tree)
        
        # Load KOT items
        self.load_kot()

    def load_kot(self):
        """Load KOT items"""
        status_filter = self.kot_filter_var.get()
        
        query = """
        SELECT oi.id, o.order_number, mi.name, oi.quantity, oi.created_at, oi.status
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.status = ?
        ORDER BY oi.created_at ASC
        """
        
        self.cursor.execute(query, (status_filter,))
        items = self.cursor.fetchall()
        
        # Clear tree
        for item in self.kot_tree.get_children():
            self.kot_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, order_number, name, quantity, created_at, status = item
            
            # Format time
            time_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            formatted_time = time_obj.strftime('%H:%M:%S')
            
            self.kot_tree.insert("", tk.END, values=(
                order_number,
                name,
                quantity,
                formatted_time,
                status
            ), tags=(item_id,))

    def mark_kot_preparing(self):
        """Mark selected KOT item as preparing"""
        selection = self.kot_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Update status
        self.cursor.execute("UPDATE order_items SET status = 'Preparing' WHERE id = ?", (item_id,))
        self.conn.commit()
        
        messagebox.showinfo("Success", "Item marked as 'Preparing'")
        self.load_kot()

    def mark_kot_completed(self):
        """Mark selected KOT item as completed"""
        selection = self.kot_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to update")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Update status
        self.cursor.execute("UPDATE order_items SET status = 'Completed' WHERE id = ?", (item_id,))
        self.conn.commit()
        
        messagebox.showinfo("Success", "Item marked as 'Completed'")
        self.load_kot()

    def print_kot(self):
        """Print selected KOT item"""
        selection = self.kot_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to print")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Get item details
        self.cursor.execute("""
        SELECT o.order_number, mi.name, oi.quantity, oi.created_at
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.id = ?
        """, (item_id,))
        item = self.cursor.fetchone()
        
        if not item:
            return
        
        order_number, name, quantity, created_at = item
        
        # Create KOT content
        kot_content = f"""
{'='*30}
KITCHEN ORDER TICKET
{'='*30}
Order No: {order_number}
Time: {created_at}
{'-'*30}
Item: {name}
Quantity: {quantity}
{'='*30}
"""
        
        # Save KOT to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"KOT_{order_number}_{name}.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(kot_content)
            messagebox.showinfo("KOT Saved", f"KOT saved to {file_path}")

    def show_reports(self):
        """Display the reports screen"""
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Reports", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Report type selection
        report_type_frame = ttk.Frame(self.content_frame)
        report_type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(report_type_frame, text="Select Report Type:").pack(side=tk.LEFT, padx=5)
        self.report_type_var = tk.StringVar(value="Daily Sales Summary")
        report_type_combo = ttk.Combobox(report_type_frame, textvariable=self.report_type_var, 
                                        values=["Daily Sales Summary", "Sales by Item", "Sales by Category"], 
                                        state="readonly", width=30)
        report_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Date range frame
        date_range_frame = ttk.Frame(self.content_frame)
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
        buttons_frame = ttk.Frame(self.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Export to CSV", command=self.export_report_to_csv).pack(side=tk.LEFT, padx=5)
        
        # Report display
        report_frame = ttk.Frame(self.content_frame)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.report_tree = ttk.Treeview(report_frame, show="headings")
        self.report_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        report_scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
        report_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_tree.configure(yscrollcommand=report_scrollbar.set)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.report_tree)
        
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
        
        query = """
        SELECT DATE(created_at) as date, COUNT(*) as orders, SUM(total) as revenue
        FROM orders
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        
        self.cursor.execute(query, (from_date, to_date))
        data = self.cursor.fetchall()
        
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
        
        query = """
        SELECT mi.name, SUM(oi.quantity) as quantity_sold, SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) BETWEEN ? AND ?
        GROUP BY mi.name
        ORDER BY total_revenue DESC
        """
        
        self.cursor.execute(query, (from_date, to_date))
        data = self.cursor.fetchall()
        
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
        
        query = """
        SELECT c.name, SUM(oi.quantity) as quantity_sold, SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN categories c ON mi.category_id = c.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) BETWEEN ? AND ?
        GROUP BY c.name
        ORDER BY total_revenue DESC
        """
        
        self.cursor.execute(query, (from_date, to_date))
        data = self.cursor.fetchall()
        
        for row in data:
            name, quantity, revenue = row
            self.report_tree.insert("", tk.END, values=(name, quantity, f"₹{revenue:.2f}"))

    def export_report_to_csv(self):
        """Export the current report to CSV"""
        if not self.report_tree.get_children():
            messagebox.showwarning("Warning", "No report data to export")
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
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data)
        
        messagebox.showinfo("Success", f"Report exported to {file_path}")

    def show_settings(self):
        """Display the settings screen (Admin only)"""
        if self.current_user['role'] != 'Admin':
            messagebox.showerror("Access Denied", "You don't have permission to access settings")
            return
        
        self.clear_content_frame()
        
        # Title
        title_label = ttk.Label(self.content_frame, text="Settings", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook, padding="20")
        notebook.add(general_frame, text="General")
        
        # Restaurant name
        ttk.Label(general_frame, text="Restaurant Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        restaurant_name_var = tk.StringVar(value=self.settings.get('restaurant_name', ''))
        restaurant_name_entry = ttk.Entry(general_frame, textvariable=restaurant_name_var, width=40)
        restaurant_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Restaurant address
        ttk.Label(general_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar(value=self.settings.get('restaurant_address', ''))
        address_entry = ttk.Entry(general_frame, textvariable=address_var, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Currency symbol
        ttk.Label(general_frame, text="Currency Symbol:").grid(row=2, column=0, sticky=tk.W, pady=5)
        currency_var = tk.StringVar(value=self.settings.get('currency_symbol', '₹'))
        currency_entry = ttk.Entry(general_frame, textvariable=currency_var, width=10)
        currency_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Tax settings tab
        tax_frame = ttk.Frame(notebook, padding="20")
        notebook.add(tax_frame, text="Tax")
        
        # Tax rate
        ttk.Label(tax_frame, text="Tax Rate (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        tax_rate_var = tk.StringVar(value=self.settings.get('tax_rate', '5'))
        tax_rate_entry = ttk.Entry(tax_frame, textvariable=tax_rate_var, width=10)
        tax_rate_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # User management tab
        user_frame = ttk.Frame(notebook, padding="20")
        notebook.add(user_frame, text="Users")
        
        # User list
        user_list_frame = ttk.Frame(user_frame)
        user_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.user_tree = ttk.Treeview(user_list_frame, columns=("username", "role"), show="headings")
        self.user_tree.heading("username", text="Username")
        self.user_tree.heading("role", text="Role")
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        user_scrollbar = ttk.Scrollbar(user_list_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        user_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_tree.configure(yscrollcommand=user_scrollbar.set)
        
        # Set up enhanced treeview navigation
        self.enhance_treeview_navigation(self.user_tree)
        
        # User buttons
        user_buttons_frame = ttk.Frame(user_frame)
        user_buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(user_buttons_frame, text="Add User", command=self.add_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(user_buttons_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_button_frame = ttk.Frame(self.content_frame)
        save_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            # Save general settings
            self.update_setting('restaurant_name', restaurant_name_var.get())
            self.update_setting('restaurant_address', address_var.get())
            self.update_setting('currency_symbol', currency_var.get())
            
            # Save tax settings
            try:
                tax_rate = float(tax_rate_var.get())
                self.update_setting('tax_rate', str(tax_rate))
            except ValueError:
                messagebox.showerror("Error", "Invalid tax rate")
                return
            
            messagebox.showinfo("Success", "Settings saved successfully")
        
        ttk.Button(save_button_frame, text="Save Settings", command=save_settings).pack(side=tk.RIGHT)
        
        # Load users
        self.load_users()

    def load_users(self):
        """Load users into the user tree"""
        # Clear tree
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Get users
        self.cursor.execute("SELECT username, role FROM users ORDER BY username")
        users = self.cursor.fetchall()
        
        # Add users to tree
        for user in users:
            self.user_tree.insert("", tk.END, values=user)

    def add_user(self):
        """Add a new user"""
        # Create add user window
        add_window = tk.Toplevel(self.root)
        add_window.title("Add User")
        add_window.geometry("300x200")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=10)
        username_entry = ttk.Entry(form_frame, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=10)
        password_entry = ttk.Entry(form_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Role
        ttk.Label(form_frame, text="Role:").grid(row=2, column=0, sticky=tk.W, pady=10)
        role_var = tk.StringVar(value="Cashier")
        role_combo = ttk.Combobox(form_frame, textvariable=role_var, values=["Admin", "Cashier"], state="readonly", width=28)
        role_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_var.get()
            
            if not username or not password:
                messagebox.showwarning("Warning", "Please enter username and password")
                return
            
            # Hash password
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            
            # Insert user
            try:
                self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                                  (username, hashed_password, role))
                self.conn.commit()
                
                messagebox.showinfo("Success", "User added successfully")
                add_window.destroy()
                self.load_users()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")
        
        ttk.Button(buttons_frame, text="Save", command=save_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=add_window.destroy).pack(side=tk.LEFT, padx=5)

    def delete_user(self):
        """Delete selected user"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to delete")
            return
        
        # Get username
        user = self.user_tree.item(selection[0])
        username = user['values'][0]
        
        # Don't allow deleting the current user or the default admin
        if username == self.current_user['username'] or username == 'admin':
            messagebox.showerror("Error", "Cannot delete this user")
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?"):
            # Delete user
            self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            self.conn.commit()
            
            messagebox.showinfo("Success", "User deleted successfully")
            self.load_users()

    def logout(self):
        """Logout the current user"""
        self.current_user = None
        self.show_login_screen()

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.conn.close()
            self.root.destroy()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantPOSApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()