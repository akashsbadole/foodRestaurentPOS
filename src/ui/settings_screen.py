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
        """Setup modern settings UI with improved design"""
        # Check if user has admin privileges
        if self.app.current_user['role'] != 'Admin':
            self.show_message("Access Denied", "You don't have permission to access settings", "error")
            return
        
        # Configure styles
        self.configure_styles()
        
        # Set background color for the entire content frame
        bg_frame = tk.Frame(self.app.content_frame, bg=COLOR_BACKGROUND_LIGHT)
        bg_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create main container with proper spacing and shadow effect
        shadow_container = tk.Frame(bg_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_XL, pady=SPACING_XL)
        
        main_container = self.create_modern_frame(
            shadow_container,
            style="Card.TFrame",
            padding=SPACING_XL
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Header section with title and description
        header_frame = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_M)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_L))
        
        title_label = self.create_modern_label(
            header_frame, 
            text="Settings", 
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = self.create_modern_label(
            header_frame, 
            text="Manage your restaurant settings, tax configuration, and user accounts", 
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        
        # Create modern notebook for tabs with enhanced styling
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Configure enhanced notebook style
        style = ttk.Style()
        style.configure("Settings.TNotebook", 
                       background=COLOR_BACKGROUND_LIGHT,
                       borderwidth=0)
        style.configure("Settings.TNotebook.Tab", 
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       padding=[SPACING_L, SPACING_M],
                       font=(FONT_FAMILY_PRIMARY, 12, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        style.map("Settings.TNotebook.Tab",
                 background=[('selected', COLOR_PRIMARY)],
                 foreground=[('selected', COLOR_CARD_WHITE),
                           ('!selected', COLOR_TEXT_SECONDARY)],
                 padding=[('selected', [SPACING_L, SPACING_M]),
                         ('!selected', [SPACING_M, SPACING_M])])
        
        notebook.configure(style="Settings.TNotebook")
        
        # Create tabs with improved content
        self.create_general_settings_tab(notebook)
        self.create_tax_settings_tab(notebook)
        self.create_user_management_tab(notebook)
        
        # Save button container with modern styling
        save_container = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_L)
        save_container.pack(fill=tk.X, pady=(SPACING_L, 0))
        
        # Add separator
        self.create_separator(save_container, orient=tk.HORIZONTAL, padding=SPACING_M)
        
        # Button container for save action
        button_container = ttk.Frame(save_container, style="Card.TFrame")
        button_container.pack(fill=tk.X, pady=SPACING_M)
        
        # Modern save button with enhanced styling
        save_button = self.create_modern_button(
            button_container,
            text="Save All Settings",
            command=self.save_settings,
            style="Success.TButton"
        )
        save_button.pack(side=tk.RIGHT, padx=SPACING_S)
        
        # Status label for feedback
        self.status_label = self.create_modern_label(
            button_container,
            text="",
            style="Small.TLabel"
        )
        self.status_label.pack(side=tk.LEFT, padx=SPACING_S)
        
        # Load users
        self.load_users()
    
    def create_general_settings_tab(self, notebook):
        """Create the General Settings tab with improved layout"""
        # General settings tab with modern card design
        general_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(general_frame, text="General Settings")
        
        # Tab description
        desc_label = self.create_modern_label(
            general_frame, 
            text="Configure your restaurant's basic information", 
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # General settings card with shadow effect
        shadow_container = tk.Frame(general_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        general_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        general_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(general_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header, 
            text="🏪 Restaurant Information", 
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
        # Form fields with improved layout
        form_container = ttk.Frame(general_card, style="Panel.TFrame")
        form_container.pack(fill=tk.X)
        
        # Restaurant name field
        self.restaurant_name_var = tk.StringVar(value=self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME))
        self.create_form_field(
            form_container,
            "Restaurant Name",
            entry_type="entry",
            textvariable=self.restaurant_name_var,
            width=50
        )
        
        # Restaurant address field
        self.address_var = tk.StringVar(value=self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS))
        self.create_form_field(
            form_container,
            "Address",
            entry_type="entry",
            textvariable=self.address_var,
            width=50
        )
        
        # Currency symbol field
        self.currency_var = tk.StringVar(value=self.app.settings.get('currency_symbol', DEFAULT_CURRENCY_SYMBOL))
        self.create_form_field(
            form_container,
            "Currency Symbol",
            entry_type="entry",
            textvariable=self.currency_var,
            width=10
        )
    
    def create_tax_settings_tab(self, notebook):
        """Create the Tax Settings tab with improved layout"""
        # Tax settings tab with modern card design
        tax_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(tax_frame, text="Tax Settings")
        
        # Tab description
        desc_label = self.create_modern_label(
            tax_frame, 
            text="Configure tax rates and financial settings", 
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # Tax settings card with shadow effect
        shadow_container = tk.Frame(tax_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        tax_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        tax_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(tax_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header, 
            text="💰 Tax Configuration", 
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
        # Form fields with improved layout
        form_container = ttk.Frame(tax_card, style="Panel.TFrame")
        form_container.pack(fill=tk.X)
        
        # Tax rate field
        self.tax_rate_var = tk.StringVar(value=self.app.settings.get('tax_rate', str(DEFAULT_TAX_RATE)))
        self.create_form_field(
            form_container,
            "Tax Rate (%)",
            entry_type="entry",
            textvariable=self.tax_rate_var,
            width=15
        )
        
        # Information note
        note_frame = self.create_modern_frame(tax_card, style="Card.TFrame", padding=SPACING_M)
        note_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        note_label = self.create_modern_label(
            note_frame,
            "💡 Note: Tax rate should be a value between 0 and 100",
            style="Small.TLabel"
        )
        note_label.pack(anchor=tk.W)
    
    def create_user_management_tab(self, notebook):
        """Create the User Management tab with improved layout"""
        # User management tab with modern design
        user_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(user_frame, text="User Management")
        
        # Tab description
        desc_label = self.create_modern_label(
            user_frame, 
            text="Add, remove, and manage user accounts and permissions", 
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # User management card with shadow effect
        shadow_container = tk.Frame(user_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        user_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        user_card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(user_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header, 
            text="👥 Manage Users", 
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
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
            (250, 120)
        )
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # User action buttons with modern styling
        user_buttons_frame = self.create_button_group(
            user_card,
            [
                ("➕ Add User", self.add_user, "Success.TButton"),
                ("🗑️ Delete User", self.delete_user, "Danger.TButton")
            ],
            spacing=SPACING_M
        )
    
    def save_settings(self):
        """Save all settings with validation and feedback"""
        try:
            # Show saving status
            self.status_label.configure(text="Saving settings...", foreground=COLOR_WARNING)
            self.app.root.update()
            
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
                self.status_label.configure(text=f"Error: {str(e)}", foreground=COLOR_ERROR)
                self.show_message("Validation Error", f"Invalid tax rate: {str(e)}", "error")
                return
            
            # Show success message
            self.status_label.configure(text="Settings saved successfully!", foreground=COLOR_SUCCESS)
            self.show_message("Success", "Settings saved successfully", "info")
            
            # Clear status after delay
            self.app.root.after(3000, lambda: self.status_label.configure(text=""))
            
        except Exception as e:
            self.status_label.configure(text=f"Error: {str(e)}", foreground=COLOR_ERROR)
            self.show_message("Error", f"Failed to save settings: {str(e)}", "error")
    
    def on_settings_changed(self, key, value):
        """Called when settings are changed elsewhere"""
        # Update the corresponding field if this setting is changed
        if key == 'restaurant_name':
            self.restaurant_name_var.set(value)
        elif key == 'restaurant_address':
            self.address_var.set(value)
        elif key == 'currency_symbol':
            self.currency_var.set(value)
        elif key == 'tax_rate':
            self.tax_rate_var.set(value)
    
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
        add_window.geometry("450x400")
        add_window.configure(background=COLOR_BACKGROUND_LIGHT)
        add_window.resizable(False, False)
        
        # Make window modal
        add_window.transient(self.app.root)
        add_window.grab_set()
        
        # Center the window
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (add_window.winfo_screenheight() // 2) - (400 // 2)
        add_window.geometry(f"450x400+{x}+{y}")
        
        # Main container with shadow effect
        shadow_container = tk.Frame(add_window, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        main_container = self.create_modern_frame(shadow_container, style="Card.TFrame", padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
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
        self.create_form_field(
            form_container,
            "Username",
            entry_type="entry",
            textvariable=username_var,
            width=30
        )
        
        # Password field
        password_var = tk.StringVar()
        self.create_form_field(
            form_container,
            "Password",
            entry_type="entry",
            textvariable=password_var,
            show="*",
            width=30
        )
        
        # Role field
        role_var = tk.StringVar(value="Cashier")
        self.create_form_field(
            form_container,
            "Role",
            entry_type="combobox",
            textvariable=role_var,
            values=["Admin", "Cashier"],
            state="readonly",
            width=28
        )
        
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
        add_window.after(100, lambda: add_window.focus_set())
    
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