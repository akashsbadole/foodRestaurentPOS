import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
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

# Import our modular components
from models.database import DatabaseManager, User, Category, MenuItem, Table, Order, KOT, Settings
from models.report import Report
from ui.login_screen import LoginScreen
from ui.dashboard_screen import DashboardScreen
from ui.order_screen import OrderScreen
from ui.menu_screen import MenuScreen
from ui.orders_screen import OrdersScreen
from ui.tables_screen import TablesScreen
from ui.inventory_screen import InventoryScreen
from ui.kot_screen import KOTScreen
from ui.reports_screen import ReportsScreen
from ui.settings_screen import SettingsScreen
from utils.keyboard_handler import KeyboardHandler
from utils.helpers import generate_order_number, format_currency, format_datetime, export_to_csv, generate_bill_content, generate_kot_content
from utils.constants import *

class RestaurantPOSApp:
    """Main Restaurant POS Application Class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Restaurant POS System")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.state('zoomed')  # Maximize window
        
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
        
        # Load settings
        self.load_settings()
        
        # Check if database exists, if not create it
        if not os.path.exists('restaurant_pos.db'):
            import database_setup
            database_setup.setup_database()
        
        # Show login screen
        self.show_login_screen()
    
    def load_settings(self):
        """Load application settings from database"""
        self.settings = self.settings_model.get_all()
    
    def update_setting(self, key, value):
        """Update a setting in the database"""
        self.settings_model.update(key, value)
        self.settings[key] = value
    
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
        
        # Set up global keyboard shortcuts
        self.keyboard_handler.setup_global_keyboard_shortcuts()
        
        # Show dashboard by default
        self.show_dashboard()
    
    def create_top_bar(self, parent):
        """Create the top navigation bar"""
        top_bar = ttk.Frame(parent)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        # Restaurant name
        restaurant_label = ttk.Label(top_bar, 
                                  text=self.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME), 
                                  font=('Arial',34, 'bold'))
        restaurant_label.pack(side=tk.LEFT, padx=10)
        
        # User info
        user_frame = ttk.Frame(top_bar)
        user_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Label(user_frame, 
                 text=f"User: {self.current_user['username']} ({self.current_user['role']})").pack(side=tk.LEFT, padx=5)
        
        # Logout button
        logout_button = ttk.Button(user_frame, text="Logout", command=self.logout)
        logout_button.pack(side=tk.LEFT, padx=5)
    
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
            ("Reports", self.show_reports)
        ]
        
        for text, command in buttons:
            ttk.Button(sidebar, text=text, command=command).pack(fill=tk.X, pady=5)
        
        # Settings button (only for admin)
        if self.current_user['role'] == ROLE_ADMIN:
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
    
    def clear_content_frame(self):
        """Clear all widgets from the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """Display the dashboard"""
        self.dashboard_screen.show(self.content_frame)
    
    def show_new_order(self):
        """Display the new order screen"""
        self.clear_content_frame()
        
        # Clean up existing OrderScreen if it exists
        if self.current_order_screen:
            self.current_order_screen.cleanup()
        
        # Create new OrderScreen instance
        self.current_order_screen = OrderScreen(self.root, self)
        self.current_order_screen.setup_ui()
    
    def show_orders(self):
        """Display the orders screen"""
        self.clear_content_frame()
        orders_screen = OrdersScreen(self.root, self)
    
    def show_menu(self):
        """Display the menu management screen"""
        self.clear_content_frame()
        menu_screen = MenuScreen(self.root, self)
    
    def show_tables(self):
        """Display the tables management screen"""
        self.clear_content_frame()
        tables_screen = TablesScreen(self.root, self)
    
    def show_inventory(self):
        """Display the inventory management screen"""
        self.clear_content_frame()
        inventory_screen = InventoryScreen(self.root, self)
    
    def show_kot(self):
        """Display the Kitchen Order Ticket screen"""
        self.clear_content_frame()
        kot_screen = KOTScreen(self.root, self)
    
    def show_reports(self):
        """Display the reports screen"""
        self.clear_content_frame()
        reports_screen = ReportsScreen(self.root, self)
    
    def show_settings(self):
        """Display the settings screen (Admin only)"""
        self.clear_content_frame()
        settings_screen = SettingsScreen(self.root, self)
    
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
