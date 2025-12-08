import tkinter as tk
from tkinter import ttk, messagebox
from .base_ui import BaseUI

class LoginScreen(BaseUI):
    """Login screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.login_frame = None
        self.username_entry = None
        self.password_entry = None
        self.status_bar = None
        self.key_bindings = []  # Track key bindings for cleanup
    
    def show(self):
        """Display the login screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create login frame
        self.login_frame = ttk.Frame(main_container, padding="40")
        self.login_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = ttk.Label(self.login_frame, text="Restaurant POS System", 
                             font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Restaurant name
        restaurant_label = ttk.Label(self.login_frame, 
                                  text=self.app.settings.get('restaurant_name', 'My Restaurant'),
                                  font=('Arial', 14))
        restaurant_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Username
        self.username_entry = self.create_form_entry(self.login_frame, "Username:", 2, 0)
        
        # Password
        self.password_entry = self.create_form_entry(self.login_frame, "Password:", 3, 0, show="*")
        
        # Login button
        login_button = ttk.Button(self.login_frame, text="Login", command=self.login)
        login_button.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Create status bar
        self.status_bar, _, _ = self.create_status_bar(self.root)
        
        # Enhanced login screen keyboard navigation
        self.setup_login_navigation()
        
        # Focus on username entry
        self.username_entry.focus()
    
    def setup_login_navigation(self):
        """Setup keyboard navigation for login screen"""
        def on_login_key_press(event):
            if event.keysym == 'Return':
                # If password field has focus, login; otherwise move to next field
                if self.password_entry.focus_get() == self.password_entry:
                    self.login()
                    if hasattr(self.app, 'keyboard_handler'):
                        self.app.keyboard_handler.show_keyboard_feedback("Login")
                else:
                    self.password_entry.focus()
                    if hasattr(self.app, 'keyboard_handler'):
                        self.app.keyboard_handler.show_keyboard_feedback("Next Field")
            elif event.keysym == 'Tab':
                # Tab navigation between fields
                if self.username_entry.focus_get() == self.username_entry:
                    self.password_entry.focus()
                    if hasattr(self.app, 'keyboard_handler'):
                        self.app.keyboard_handler.show_keyboard_feedback("Next Field")
                    return "break"  # Prevent default tab behavior
                elif self.password_entry.focus_get() == self.password_entry:
                    self.username_entry.focus()
                    if hasattr(self.app, 'keyboard_handler'):
                        self.app.keyboard_handler.show_keyboard_feedback("Previous Field")
                    return "break"  # Prevent default tab behavior
        
        # Clear any existing key bindings
        self.cleanup_key_bindings()
        
        # Bind keyboard events and track them
        return_binding = self.root.bind('<Return>', on_login_key_press)
        tab_binding = self.root.bind('<Tab>', on_login_key_press)
        self.key_bindings.extend([return_binding, tab_binding])
    
    def cleanup_key_bindings(self):
        """Clean up keyboard bindings to prevent callback errors"""
        for binding_id in self.key_bindings:
            try:
                self.root.unbind('<Return>', binding_id)
                self.root.unbind('<Tab>', binding_id)
            except:
                pass  # Ignore errors during cleanup
        self.key_bindings.clear()
    
    def login(self):
        """Authenticate user and show main application"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            self.show_message("Error", "Please enter username and password", "error")
            return
        
        # Authenticate using User model
        user = self.app.user_model.authenticate(username, password)
        
        if user:
            # Clean up key bindings before transitioning
            self.cleanup_key_bindings()
            
            self.app.current_user = {
                'id': user[0],
                'username': user[1],
                'role': user[2]
            }
            self.app.show_main_app()
        else:
            self.show_message("Error", "Invalid username or password", "error")
