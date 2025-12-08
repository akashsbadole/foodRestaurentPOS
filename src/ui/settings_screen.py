import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from utils.constants import *

class SettingsScreen(BaseUI):
    """Settings screen UI component (Admin only)"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern settings UI"""
        # Check if user has admin privileges
        if self.app.current_user['role'] != 'Admin':
            self.show_message("Access Denied", "You don't have permission to access settings", "error")
            return
        
        # Configure styles
        self.configure_styles()
        
        # Set background color for the entire content frame using a regular Frame
        bg_frame = tk.Frame(self.app.content_frame, bg=COLOR_BACKGROUND_LIGHT)
        bg_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create main container with padding
        main_container = self.create_modern_frame(
            bg_frame,
            style="Card.TFrame",
            padding=SPACING_L
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_XL, pady=SPACING_XL)
        
        # Title with modern styling
        title_label = self.create_modern_label(
            main_container, 
            text="Settings", 
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, SPACING_L), anchor=tk.W)
        
        # Create modern notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
        
        # Configure notebook style
        style = ttk.Style()
        style.configure("Modern.TNotebook", 
                       background=COLOR_BACKGROUND_LIGHT,
                       borderwidth=0)
        style.configure("Modern.TNotebook.Tab", 
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       padding=[SPACING_M, SPACING_S],
                       font=(FONT_FAMILY_PRIMARY, 12, 'medium'),
                       borderwidth=0)
        style.map("Modern.TNotebook.Tab",
                 background=[('selected', COLOR_PRIMARY)],
                 foreground=[('selected', COLOR_CARD_WHITE),
                           ('!selected', COLOR_TEXT_SECONDARY)])
        
        notebook.configure(style="Modern.TNotebook")
        
        # General settings tab with modern card design
        general_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_L)
        notebook.add(general_frame, text="General Settings")
        
        # General settings card
        general_card = self.create_modern_frame(general_frame, style="Panel.TFrame", padding=SPACING_M)
        general_card.pack(fill=tk.X, pady=SPACING_S)
        
        # Section title
        section_title = self.create_modern_label(
            general_card, 
            text="Restaurant Information", 
            style="SectionTitle.TLabel"
        )
        section_title.pack(pady=(0, SPACING_M), anchor=tk.W)
        
        # Restaurant name field
        restaurant_name_var = tk.StringVar(value=self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME))
        restaurant_name_container = ttk.Frame(general_card)
        restaurant_name_container.pack(fill=tk.X, pady=SPACING_S)
        restaurant_name_label = self.create_modern_label(restaurant_name_container, "Restaurant Name", style="Body.TLabel")
        restaurant_name_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        self.restaurant_name_field = self.create_modern_entry(restaurant_name_container, textvariable=restaurant_name_var, width=40)
        self.restaurant_name_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Restaurant address field
        address_var = tk.StringVar(value=self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS))
        address_container = ttk.Frame(general_card)
        address_container.pack(fill=tk.X, pady=SPACING_S)
        address_label = self.create_modern_label(address_container, "Address", style="Body.TLabel")
        address_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        self.address_field = self.create_modern_entry(address_container, textvariable=address_var, width=40)
        self.address_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Currency symbol field
        currency_var = tk.StringVar(value=self.app.settings.get('currency_symbol', DEFAULT_CURRENCY_SYMBOL))
        currency_container = ttk.Frame(general_card)
        currency_container.pack(fill=tk.X, pady=SPACING_S)
        currency_label = self.create_modern_label(currency_container, "Currency Symbol", style="Body.TLabel")
        currency_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        self.currency_field = self.create_modern_entry(currency_container, textvariable=currency_var, width=10)
        self.currency_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Tax settings tab with modern card design
        tax_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_L)
        notebook.add(tax_frame, text="Tax Settings")
        
        # Tax settings card
        tax_card = self.create_modern_frame(tax_frame, style="Panel.TFrame", padding=SPACING_M)
        tax_card.pack(fill=tk.X, pady=SPACING_S)
        
        # Section title
        tax_section_title = self.create_modern_label(
            tax_card, 
            text="Tax Configuration", 
            style="SectionTitle.TLabel"
        )
        tax_section_title.pack(pady=(0, SPACING_M), anchor=tk.W)
        
        # Tax rate field
        tax_rate_var = tk.StringVar(value=self.app.settings.get('tax_rate', str(DEFAULT_TAX_RATE)))
        tax_rate_container = ttk.Frame(tax_card)
        tax_rate_container.pack(fill=tk.X, pady=SPACING_S)
        tax_rate_label = self.create_modern_label(tax_rate_container, "Tax Rate (%)", style="Body.TLabel")
        tax_rate_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        self.tax_rate_field = self.create_modern_entry(tax_rate_container, textvariable=tax_rate_var, width=10)
        self.tax_rate_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # User management tab with modern design
        user_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_L)
        notebook.add(user_frame, text="User Management")
        
        # User management card
        user_card = self.create_modern_frame(user_frame, style="Panel.TFrame", padding=SPACING_M)
        user_card.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # Section title
        user_section_title = self.create_modern_label(
            user_card, 
            text="Manage Users", 
            style="SectionTitle.TLabel"
        )
        user_section_title.pack(pady=(0, SPACING_M), anchor=tk.W)
        
        # User list container with shadow effect
        user_list_container = self.create_modern_frame(user_card, style="Shadow.TFrame", padding=1)
        user_list_container.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # User list with modern treeview
        user_list_frame = self.create_modern_frame(user_list_container, style="Card.TFrame", padding=SPACING_S)
        user_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.user_tree, user_scrollbar = self.create_modern_treeview(
            user_list_frame,
            ("username", "role"),
            ("Username", "Role"),
            (200, 100)
        )
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # User action buttons with modern styling
        user_buttons_frame = self.create_button_group(
            user_card,
            [
                ("Add User", self.add_user, "Success.TButton"),
                ("Delete User", self.delete_user, "Danger.TButton")
            ],
            spacing=SPACING_M
        )
        
        # Save button container with modern styling
        save_container = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_M)
        save_container.pack(fill=tk.X, pady=SPACING_L)
        
        # Modern save button
        save_button = self.create_modern_button(
            save_container,
            text="Save Settings",
            command=self.save_settings,
            style="Success.TButton"
        )
        save_button.pack(side=tk.RIGHT, padx=SPACING_S, pady=SPACING_S)
        
        # Store references for user management
        self.restaurant_name_var = restaurant_name_var
        self.address_var = address_var
        self.currency_var = currency_var
        self.tax_rate_var = tax_rate_var
        
        # Load users
        self.load_users()
    
    def save_settings(self):
        """Save all settings with validation and feedback"""
        try:
            # Save general settings
            self.app.update_setting('restaurant_name', self.restaurant_name_var.get())
            self.app.update_setting('restaurant_address', self.address_var.get())
            self.app.update_setting('currency_symbol', self.currency_var.get())
            
            # Save tax settings with validation
            try:
                tax_rate = float(self.tax_rate_var.get())
                if tax_rate < 0 or tax_rate > 100:
                    raise ValueError("Tax rate must be between 0 and 100")
                self.app.update_setting('tax_rate', str(tax_rate))
            except ValueError as e:
                self.show_message("Validation Error", f"Invalid tax rate: {str(e)}", "error")
                return
            
            # Show success message
            self.show_message("Success", "Settings saved successfully", "info")
            
        except Exception as e:
            self.show_message("Error", f"Failed to save settings: {str(e)}", "error")
    
    def load_users(self):
        """Load users into the modern user tree"""
        users = self.app.user_model.get_all()
        
        # Clear tree
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Add users to tree with role-based styling
        for user in users:
            item_id = self.user_tree.insert("", tk.END, values=user)
            # Apply tag based on role
            if user[1] == 'Admin':
                self.user_tree.item(item_id, tags=('admin',))
            else:
                self.user_tree.item(item_id, tags=('cashier',))
        
        # Configure tags for visual distinction
        self.user_tree.tag_configure('admin', background=COLOR_SUCCESS_LIGHT)
        self.user_tree.tag_configure('cashier', background=COLOR_INFO)
    
    def add_user(self):
        """Add a new user with modern dialog"""
        # Create modern add user window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add New User")
        add_window.geometry("400x300")
        add_window.configure(background=COLOR_BACKGROUND_LIGHT)
        
        # Make window modal
        add_window.transient(self.app.root)
        add_window.grab_set()
        
        # Main container
        main_container = self.create_modern_frame(add_window, style="Card.TFrame", padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            main_container, 
            text="Add New User", 
            style="SectionTitle.TLabel"
        )
        title_label.pack(pady=(0, SPACING_M), anchor=tk.W)
        
        # Form container
        form_container = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        form_container.pack(fill=tk.BOTH, expand=True)
        
        # Username field
        username_var = tk.StringVar()
        username_container = ttk.Frame(form_container)
        username_container.pack(fill=tk.X, pady=SPACING_S)
        username_label = self.create_modern_label(username_container, "Username", style="Body.TLabel")
        username_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        username_field = self.create_modern_entry(username_container, textvariable=username_var, width=30)
        username_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Password field
        password_var = tk.StringVar()
        password_container = ttk.Frame(form_container)
        password_container.pack(fill=tk.X, pady=SPACING_S)
        password_label = self.create_modern_label(password_container, "Password", style="Body.TLabel")
        password_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        password_field = self.create_modern_entry(password_container, textvariable=password_var, show="*", width=30)
        password_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Role field
        role_var = tk.StringVar(value="Cashier")
        role_container = ttk.Frame(form_container)
        role_container.pack(fill=tk.X, pady=SPACING_S)
        role_label = self.create_modern_label(role_container, "Role", style="Body.TLabel")
        role_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        role_field = self.create_modern_combobox(role_container, textvariable=role_var, values=["Admin", "Cashier"], state="readonly", width=28)
        role_field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        # Button container
        button_container = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_M)
        button_container.pack(fill=tk.X)
        
        # Buttons with modern styling
        def save_user():
            username = username_var.get().strip()
            password = password_var.get().strip()
            role = role_var.get()
            
            if not username or not password:
                self.show_message("Validation Error", "Please enter username and password", "warning")
                return
            
            # Insert user
            success = self.app.user_model.add(username, password, role)
            
            if success:
                self.show_message("Success", "User added successfully", "info")
                add_window.destroy()
                self.load_users()
            else:
                self.show_message("Error", "Username already exists", "error")
        
        def cancel_add():
            add_window.destroy()
        
        # Create button group
        self.create_button_group(
            button_container,
            [
                ("Save", save_user, "Success.TButton"),
                ("Cancel", cancel_add, "Secondary.TButton")
            ],
            spacing=SPACING_M
        )
        
        # Focus on username field
        username_field.focus_set()
    
    def delete_user(self):
        """Delete selected user with confirmation"""
        selection = self.user_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select a user to delete", "warning")
            return
        
        # Get username
        user = self.user_tree.item(selection[0])
        username = user['values'][0]
        
        # Don't allow deleting the current user or the default admin
        if username == self.app.current_user['username'] or username == 'admin':
            self.show_message("Error", "Cannot delete this user", "error")
            return
        
        # Confirm deletion with modern dialog
        if self.show_message("Confirm Delete", f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone.", "yesno"):
            # Delete user
            self.app.user_model.delete(username)
            
            self.show_message("Success", "User deleted successfully", "info")
            self.load_users()