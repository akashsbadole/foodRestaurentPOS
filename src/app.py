import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import sys
from datetime import datetime
import hashlib
import random
import string

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
    # Create dummy classes to prevent AttributeError
    class Image:
        __version__ = "Not Available"
    ImageTk = Image
    ImageDraw = Image
    ImageFont = Image
except Exception as e:
    PIL_AVAILABLE = False
    PIL_VERSION = None
    print(f"Warning: PIL (Pillow) import error: {e}")
    print("Image features will be disabled due to import issues")
    # Create dummy classes to prevent AttributeError
    class Image:
        __version__ = "Not Available"
    ImageTk = Image
    ImageDraw = Image
    ImageFont = Image

import csv
from io import StringIO
import tempfile

# Import our modular components
from src.models.database import DatabaseManager, User, Category, Table, KOT, Settings
from src.models.order import Order
from src.models.menu_item import MenuItem
from src.models.report import Report
from src.ui.login_screen import LoginScreen
from src.ui.dashboard_screen import DashboardScreen
from src.ui.order_screen import OrderScreen
from src.ui.menu_screen import MenuScreen
from src.ui.orders_screen import OrdersScreen
from src.ui.tables_screen import TablesScreen
from src.ui.inventory_screen import InventoryScreen
from src.ui.kot_screen import KOTScreen
from src.ui.kot_window import KOTWindow
from src.ui.reports_screen import ReportsScreen
from src.ui.gst_reports_screen import GSTReportsScreen
from src.ui.settings_screen import SettingsScreen
from src.ui.data_management_screen import DataManagementScreen
from src.utils.keyboard_handler import KeyboardHandler
from src.utils.helpers import generate_order_number, format_currency, format_datetime, export_to_csv, generate_bill_content, generate_kot_content
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.managers.data_manager import init_data_manager

class RestaurantPOSApp:
    """Main Restaurant POS Application Class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant POS System")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.state('zoomed')  # Maximize window
        
        # Set window icon
        self.set_window_icon()
        
        # Initialize database connection
        self.db = DatabaseManager()
        
        # Initialize models
        self.user_model = User(self.db)
        self.category_model = Category(self.db)
        self.menu_item_model = MenuItem(self.db)
        self.table_model = Table(self.db)
        self.order_model = Order(self.db)
        self.kot_model = KOT(self.db)
        self.report_model = Report(self.db)
        self.settings_model = Settings(self.db)
        
        # Initialize UI components
        self.login_screen = LoginScreen(root, self)
        self.dashboard_screen = DashboardScreen(root, self)
        
        # Initialize keyboard handler
        self.keyboard_handler = KeyboardHandler(root, self)
        
        # Track current OrderScreen instance
        self.current_order_screen = None
        
        # Initialize variables
        self.current_user = None
        self.settings = {}
        self.content_frame = None
        self.status_bar = None
        
        # Initialize event dispatcher
        event_dispatcher.set_tk_root(root)
        
        # Load settings
        self.load_settings()
        
        # Initialize data manager
        init_data_manager(self)
        
        # Check if database exists, if not create it
        if not os.path.exists('restaurant_pos.db'):
            import database_setup
            database_setup.setup_database()
        
        # Show login screen
        self.show_login_screen()
    
    def set_window_icon(self):
        """Set the window icon using the POS logo"""
        if not PIL_AVAILABLE:
            print("PIL not available - cannot set window icon")
            return
        
        try:
            # Path to the logo image
            logo_path = os.path.join(project_root, 'images', 'pos-logo.png')
            
            # Check if logo file exists
            if not os.path.exists(logo_path):
                print(f"Logo file not found at: {logo_path}")
                return
            
            # Load and resize image for icon (typical icon size is 32x32)
            image = Image.open(logo_path)
            
            # Resize to appropriate icon size
            icon_size = (32, 32)
            image.thumbnail(icon_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and set as window icon
            photo = ImageTk.PhotoImage(image)
            self.root.iconphoto(True, photo)
            
            # Keep a reference to prevent garbage collection
            self.window_icon = photo
            
            print("Window icon set successfully")
            
        except Exception as e:
            print(f"Error setting window icon: {e}")
    
    def load_settings(self):
        """Load application settings from database"""
        self.settings = self.settings_model.get_all()
    
    def update_setting(self, key, value):
        """Update a setting in database"""
        self.settings_model.update(key, value)
        # Notify UI components that settings have changed
        self.on_settings_changed(key, value)
        self.settings[key] = value
    
    def on_settings_changed(self, key, value):
        """Called when settings are changed - override in UI components if needed"""
        # Update UI components that depend on settings
        self.update_ui_for_setting_change(key, value)
        # Update top bar restaurant name if it changed
        if key == 'restaurant_name' and hasattr(self, 'top_bar_restaurant_label'):
            self.top_bar_restaurant_label.config(text=value)
    
    def update_ui_for_setting_change(self, key, value):
        """Update UI components when settings change"""
        # Update top bar restaurant name if it changed
        if key == 'restaurant_name' and hasattr(self, 'top_bar_restaurant_label'):
            self.top_bar_restaurant_label.config(text=value)
        
        # Force refresh of current screen if it needs to Update
        if hasattr(self, 'current_screen') and hasattr(self.current_screen, 'on_settings_changed'):
            self.current_screen.on_settings_changed(key, value)
    
    def show_login_screen(self):
        """Display the login screen"""
        self.login_screen.show()
    
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
        
        # Initialize event dispatcher after UI is ready
        event_dispatcher.set_tk_root(self.root)
        
        # Set up global keyboard shortcuts
        self.keyboard_handler.setup_global_keyboard_shortcuts()
        
        # Show dashboard by default
        self.show_dashboard()
    
    def create_top_bar(self, parent):
        """Create top navigation bar"""
        top_bar = ttk.Frame(parent)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Left side - Logo and Restaurant name
        left_frame = ttk.Frame(top_bar)
        left_frame.pack(side=tk.LEFT, padx=10)
        
        # Add logo
        logo_label = self.create_top_bar_logo(left_frame)
        if logo_label:
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Restaurant name
        self.top_bar_restaurant_label = ttk.Label(left_frame,
                                  text=self.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
                                  font=('Arial', 14, 'bold'))
        self.top_bar_restaurant_label.pack(side=tk.LEFT)
        
        # User info
        user_frame = ttk.Frame(top_bar)
        user_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(user_frame, 
                 text=f"User: {self.current_user['username']} ({self.current_user['role']})").pack(side=tk.LEFT, padx=5)
        
        # Logout button
        logout_button = ttk.Button(user_frame, text="Logout", command=self.logout)
        logout_button.pack(side=tk.LEFT, padx=5)
    
    def create_top_bar_logo(self, parent):
        """Create and return a logo label for the top bar"""
        if not PIL_AVAILABLE:
            return None
        
        try:
            # Path to the logo image
            logo_path = os.path.join(project_root, 'images', 'pos-logo.png')
            
            # Check if logo file exists
            if not os.path.exists(logo_path):
                print(f"Logo file not found at: {logo_path}")
                return None
            
            # Load and resize image
            image = Image.open(logo_path)
            
            # Resize logo to appropriate size for top bar (smaller than dashboard)
            max_size = (32, 32)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Create label with logo
            logo_label = ttk.Label(parent, image=photo)
            logo_label.image = photo  # Keep a reference to prevent garbage collection
            
            return logo_label
            
        except Exception as e:
            print(f"Error loading top bar logo: {e}")
            return None
    
    def create_sidebar(self, parent):
        """Create the sidebar navigation"""
        sidebar = ttk.Frame(parent, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        sidebar.pack_propagate(False)
        
        # Navigation buttons
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("New Order", self.show_new_order),
            ("Orders", self.show_orders),
            ("Menu", self.show_menu),
            ("Tables", self.show_tables),
            ("Inventory", self.show_inventory),
            ("KOT", self.show_kot),
            ("KOT Window", self.show_kot_window),
            ("Reports", self.show_reports),
            ("GST Reports", self.show_gst_reports)
        ]
        
        for text, command in buttons:
            ttk.Button(sidebar, text=text, command=command).pack(fill=tk.X, pady=5)
        
        # Data Management button (only for admin)
        if self.current_user['role'] == ROLE_ADMIN:
            ttk.Button(sidebar, text="Data Management", command=self.show_data_management).pack(fill=tk.X, pady=5)
            ttk.Button(sidebar, text="Settings", command=self.show_settings).pack(fill=tk.X, pady=5)
    
    def create_status_bar(self, parent):
        """Create a status bar at the bottom of the window"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # Keyboard shortcut indicator
        shortcut_indicator = ttk.Label(status_frame, text="Press F1 for shortcuts", relief=tk.SUNKEN)
        shortcut_indicator.pack(side=tk.RIGHT, padx=2, pady=2)
        self.current_screen = self.dashboard_screen
    
    def clear_content_frame(self):
        """Clear all widgets from the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Display dashboard"""
        self.dashboard_screen.show(self.content_frame)
    
    def show_new_order(self):
        """Display new order screen"""
        self.clear_content_frame()
        
        # Clean up existing OrderScreen if it exists
        if self.current_order_screen:
            self.current_order_screen.cleanup()
        
        # Create new OrderScreen instance
        self.current_order_screen = OrderScreen(self.root, self)
        self.current_order_screen.setup_ui()
    
    def show_orders(self):
        """Display orders screen"""
        self.clear_content_frame()
        orders_screen = OrdersScreen(self.root, self)
        self.current_screen = orders_screen
    
    def show_menu(self):
        """Display menu management screen"""
        self.clear_content_frame()
        menu_screen = MenuScreen(self.root, self)
        self.current_screen = menu_screen
    
    def show_tables(self):
        """Display tables management screen"""
        self.clear_content_frame()
        tables_screen = TablesScreen(self.root, self)
        self.current_screen = tables_screen
    
    def show_inventory(self):
        """Display inventory management screen"""
        self.clear_content_frame()
        inventory_screen = InventoryScreen(self.root, self)
        self.current_screen = inventory_screen
    
    def show_kot(self):
        """Display Kitchen Order Ticket screen"""
        self.clear_content_frame()
        kot_screen = KOTScreen(self.root, self)
        self.current_screen = kot_screen
    
    def show_kot_window(self):
        """Open KOT screen in a new window"""
        kot_window = KOTWindow(self.root, self)
        kot_window.show()
    
    def show_reports(self):
        """Display reports screen"""
        self.clear_content_frame()
        reports_screen = ReportsScreen(self.root, self)
        self.current_screen = reports_screen
    
    def show_gst_reports(self):
        """Display GST reports screen"""
        self.clear_content_frame()
        gst_reports_screen = GSTReportsScreen(self.root, self)
        self.current_screen = gst_reports_screen
    
    def show_data_management(self):
        """Display data management screen (Admin only)"""
        self.clear_content_frame()
        data_management_screen = DataManagementScreen(self.root, self)
        self.current_screen = data_management_screen
    
    def show_settings(self):
        """Display settings screen (Admin only)"""
        self.clear_content_frame()
        settings_screen = SettingsScreen(self.root, self)
        self.current_screen = settings_screen
    
    def logout(self):
        """Logout the current user"""
        self.current_user = None
        self.show_login_screen()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.db.close()
            self.root.destroy()

# Main execution
def main():
    root = tk.Tk()
    app = RestaurantPOSApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
