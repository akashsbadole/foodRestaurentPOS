import tkinter as tk
from tkinter import ttk, messagebox, Canvas
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
        self.card_frame = None  # Card frame for modern design
        self.shadow_frame = None  # Shadow frame for card effect
    
    def show(self):
        """Display the login screen"""
        # Clear window
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Configure window properties
        self.root.configure(bg='#f0f0f0')
        
        # Create main container with gradient background
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create a gradient background using Canvas
        self.create_gradient_background(main_container)
        
        # Create centered card container
        card_container = tk.Frame(main_container, bg='#f0f0f0')
        card_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Create modern card frame with shadow effect
        self.card_frame = tk.Frame(card_container, bg='white', relief=tk.RAISED, bd=1)
        self.card_frame.pack(padx=50, pady=50)
        
        # Add shadow effect using a slightly larger frame behind
        self.shadow_frame = tk.Frame(card_container, bg='#d0d0d0', relief=tk.SOLID, bd=0)
        self.shadow_frame.place(x=52, y=52, width=400, height=400)
        self.card_frame.lift()
        
        # Create login frame inside the card
        self.login_frame = ttk.Frame(self.card_frame, padding="40")
        self.login_frame.pack(expand=True, fill=tk.BOTH)
        
        # Configure grid weights for proper centering
        self.login_frame.columnconfigure(0, weight=1)
        self.login_frame.columnconfigure(1, weight=1)
        
        # Title with modern styling
        title_label = ttk.Label(self.login_frame, text="Restaurant POS System",
                             font=('Segoe UI', 28, 'bold'), foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky='n')
        
        # Restaurant name with subtle styling
        restaurant_label = ttk.Label(self.login_frame,
                                  text=self.app.settings.get('restaurant_name', 'My Restaurant'),
                                  font=('Segoe UI', 16), foreground='#7f8c8d')
        restaurant_label.grid(row=1, column=0, columnspan=2, pady=(0, 30), sticky='n')
        
        # Separator line
        separator = ttk.Separator(self.login_frame, orient='horizontal')
        separator.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        
        # Username with custom styling
        username_label = ttk.Label(self.login_frame, text="Username:",
                                  font=('Segoe UI', 12), foreground='#34495e')
        username_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        self.username_entry = ttk.Entry(self.login_frame, width=30, font=('Segoe UI', 12))
        self.username_entry.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Password with custom styling
        password_label = ttk.Label(self.login_frame, text="Password:",
                                  font=('Segoe UI', 12), foreground='#34495e')
        password_label.grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.password_entry = ttk.Entry(self.login_frame, width=30, show="*", font=('Segoe UI', 12))
        self.password_entry.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(0, 30))
        
        # Modern login button with styling
        login_button_style = ttk.Style()
        login_button_style.configure('Login.TButton',
                                    font=('Segoe UI', 12, 'bold'),
                                    foreground='black',
                                    background='#3498db',
                                    borderwidth=0,
                                    focuscolor='none',
                                    padding=(20, 10))
        
        # Configure hover effect styles
        login_button_style.map('Login.TButton',
                             background=[('active', '#2980b9')])
        
        login_button = ttk.Button(self.login_frame, text="Login", command=self.login,
                                 style='Login.TButton', width=20)
        login_button.grid(row=7, column=0, columnspan=2, pady=(10, 20))
        
        # Create status bar
        self.status_bar, _, _ = self.create_status_bar(self.root)
        
        # Enhanced login screen keyboard navigation
        self.setup_login_navigation()
        
        # Focus on username entry
        self.username_entry.focus()
        
        # Update the window to ensure proper centering
        self.root.update_idletasks()
    
    def create_gradient_background(self, parent):
        """Create a gradient background for the login screen"""
        canvas = Canvas(parent, highlightthickness=0, bg='#f0f0f0')
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Update canvas to get proper dimensions
        parent.update_idletasks()
        canvas.update_idletasks()
        
        # Create gradient effect
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Draw gradient rectangles
        for i in range(0, height, 2):
            # Calculate color transition from light blue to light gray
            r1, g1, b1 = 240, 248, 255  # Light blue
            r2, g2, b2 = 240, 240, 240  # Light gray
            
            ratio = i / height
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, i, width, i+2, fill=color, outline=color)
    
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
