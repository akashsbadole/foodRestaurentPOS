import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI

class SettingsScreen(BaseUI):
    """Settings screen UI component (Admin only)"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup settings UI"""
        # Check if user has admin privileges
        if self.app.current_user['role'] != 'Admin':
            self.show_message("Access Denied", "You don't have permission to access settings", "error")
            return
        
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Settings", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self.app.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings tab
        general_frame = ttk.Frame(notebook, padding="20")
        notebook.add(general_frame, text="General")
        
        # Restaurant name
        ttk.Label(general_frame, text="Restaurant Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        restaurant_name_var = tk.StringVar(value=self.app.settings.get('restaurant_name', ''))
        restaurant_name_entry = ttk.Entry(general_frame, textvariable=restaurant_name_var, width=40)
        restaurant_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Restaurant address
        ttk.Label(general_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        address_var = tk.StringVar(value=self.app.settings.get('restaurant_address', ''))
        address_entry = ttk.Entry(general_frame, textvariable=address_var, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Currency symbol
        ttk.Label(general_frame, text="Currency Symbol:").grid(row=2, column=0, sticky=tk.W, pady=5)
        currency_var = tk.StringVar(value=self.app.settings.get('currency_symbol', '₹'))
        currency_entry = ttk.Entry(general_frame, textvariable=currency_var, width=10)
        currency_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Tax settings tab
        tax_frame = ttk.Frame(notebook, padding="20")
        notebook.add(tax_frame, text="Tax")
        
        # Tax rate
        ttk.Label(tax_frame, text="Tax Rate (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        tax_rate_var = tk.StringVar(value=self.app.settings.get('tax_rate', '5'))
        tax_rate_entry = ttk.Entry(tax_frame, textvariable=tax_rate_var, width=10)
        tax_rate_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # User management tab
        user_frame = ttk.Frame(notebook, padding="20")
        notebook.add(user_frame, text="Users")
        
        # User list
        user_list_frame = ttk.Frame(user_frame)
        user_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.user_tree, user_scrollbar = self.create_treeview(
            user_list_frame,
            ("username", "role"),
            ("Username", "Role"),
            (200, 100)
        )
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # User buttons
        user_buttons_frame = ttk.Frame(user_frame)
        user_buttons_frame.pack(fill=tk.X, pady=10)
        
        self.create_button_frame(user_buttons_frame, [
            ("Add User", self.add_user),
            ("Delete User", self.delete_user)
        ])
        
        # Save button
        save_button_frame = ttk.Frame(self.app.content_frame)
        save_button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            # Save general settings
            self.app.update_setting('restaurant_name', restaurant_name_var.get())
            self.app.update_setting('restaurant_address', address_var.get())
            self.app.update_setting('currency_symbol', currency_var.get())
            
            # Save tax settings
            try:
                tax_rate = float(tax_rate_var.get())
                self.app.update_setting('tax_rate', str(tax_rate))
            except ValueError:
                self.show_message("Error", "Invalid tax rate", "error")
                return
            
            self.show_message("Success", "Settings saved successfully", "info")
        
        ttk.Button(save_button_frame, text="Save Settings", command=save_settings).pack(side=tk.RIGHT)
        
        # Store references for user management
        self.restaurant_name_var = restaurant_name_var
        self.address_var = address_var
        self.currency_var = currency_var
        self.tax_rate_var = tax_rate_var
        
        # Load users
        self.load_users()
    
    def load_users(self):
        """Load users into the user tree"""
        users = self.app.user_model.get_all()
        
        # Clear tree
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # Add users to tree
        for user in users:
            self.user_tree.insert("", tk.END, values=user)
    
    def add_user(self):
        """Add a new user"""
        # Create add user window
        add_window = tk.Toplevel(self.app.root)
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
                self.show_message("Warning", "Please enter username and password", "warning")
                return
            
            # Insert user
            success = self.app.user_model.add(username, password, role)
            
            if success:
                self.show_message("Success", "User added successfully", "info")
                add_window.destroy()
                self.load_users()
            else:
                self.show_message("Error", "Username already exists", "error")
        
        self.create_button_frame(buttons_frame, [
            ("Save", save_user),
            ("Cancel", add_window.destroy)
        ])
    
    def delete_user(self):
        """Delete selected user"""
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
        
        # Confirm deletion
        if self.show_message("Confirm Delete", f"Are you sure you want to delete user '{username}'?", "yesno"):
            # Delete user
            self.app.user_model.delete(username)
            
            self.show_message("Success", "User deleted successfully", "info")
            self.load_users()
