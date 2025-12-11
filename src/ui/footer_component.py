"""
Footer Component for Desktop POS System
Handles dynamic footer display for all screens
"""

import tkinter as tk
from tkinter import ttk, font
from datetime import datetime
from typing import Dict, Any, Optional
from models.settings import Settings


class FooterComponent(tk.Frame):
    """
    Footer Component for Desktop POS
    """
    
    def __init__(self, parent, settings_manager=None, **kwargs):
        """
        Initialize footer component
        
        Args:
            parent: Parent widget
            settings_manager: Settings manager instance
            **kwargs: Additional keyword arguments
        """
        super().__init__(parent, **kwargs)
        
        self.settings_manager = settings_manager
        self.footer_settings = {}
        self.current_order_data = {}
        self.current_user_data = {}
        
        # Load footer settings
        self.load_footer_settings()
        
        # Create footer UI
        self.create_footer_ui()
        
        # Start update timer
        self.update_timestamp()
    
    def load_footer_settings(self):
        """Load footer settings from settings manager"""
        if self.settings_manager:
            self.footer_settings = self.settings_manager.get_footer_settings()
        else:
            # Load directly from Settings
            self.footer_settings = {
                'footer_enabled': Settings.get('footer_enabled', 'true'),
                'footer_business_name': Settings.get('footer_business_name', ''),
                'footer_address': Settings.get('footer_address', ''),
                'footer_phone': Settings.get('footer_phone', ''),
                'footer_email': Settings.get('footer_email', ''),
                'footer_show_business_info': Settings.get('footer_show_business_info', 'true'),
                'footer_show_receipt_info': Settings.get('footer_show_receipt_info', 'true'),
                'footer_show_user_name': Settings.get('footer_show_user_name', 'true'),
                'footer_show_user_id': Settings.get('footer_show_user_id', 'false'),
                'footer_show_timestamp': Settings.get('footer_show_timestamp', 'true'),
                'footer_custom_text': Settings.get('footer_custom_text', 'Thank you for your business!'),
                'footer_font_size': Settings.get('footer_font_size', '10'),
                'footer_font_family': Settings.get('footer_font_family', 'Arial'),
                'footer_background_color': Settings.get('footer_background_color', '#2c3e50'),
                'footer_text_color': Settings.get('footer_text_color', '#ecf0f1'),
                'footer_alignment': Settings.get('footer_alignment', 'center'),
                'footer_logo_path': Settings.get('footer_logo_path', ''),
                'footer_show_logo': Settings.get('footer_show_logo', 'false'),
                'footer_multiline': Settings.get('footer_multiline', 'false'),
                'footer_line1': Settings.get('footer_line1', ''),
                'footer_line2': Settings.get('footer_line2', ''),
                'footer_line3': Settings.get('footer_line3', '')
            }
    
    def create_footer_ui(self):
        """Create footer UI components"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Check if footer is enabled
        if not self.footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return
        
        # Configure footer frame
        self.configure(
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            relief='raised',
            bd=1
        )
        
        # Create main container
        main_container = tk.Frame(self, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        main_container.pack(fill='both', expand=True, padx=5, pady=2)
        
        # Create sections based on settings
        self.create_footer_sections(main_container)
        
        # Create bottom bar
        self.create_bottom_bar(main_container)
    
    def create_footer_sections(self, parent):
        """Create footer sections"""
        sections_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        sections_frame.pack(fill='x', pady=(0, 5))
        
        # Business Info Section
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            self.create_business_section(sections_frame)
        
        # Receipt Info Section
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true':
            self.create_receipt_section(sections_frame)
        
        # User Info Section
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true':
            self.create_user_section(sections_frame)
        
        # Custom Text Section
        if self.footer_settings.get('footer_custom_text', ''):
            self.create_custom_section(sections_frame)
    
    def create_business_section(self, parent):
        """Create business information section"""
        business_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        business_frame.pack(side='left', padx=10)
        
        # Business name
        business_name = self.footer_settings.get('footer_business_name', 'Restaurant POS')
        if business_name:
            tk.Label(
                business_frame,
                text=business_name,
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)) + 2, 'bold')
            ).pack(anchor='w')
        
        # Address
        address = self.footer_settings.get('footer_address', '')
        if address:
            tk.Label(
                business_frame,
                text=address,
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)))
            ).pack(anchor='w')
        
        # Phone
        phone = self.footer_settings.get('footer_phone', '')
        if phone:
            tk.Label(
                business_frame,
                text=f"📞 {phone}",
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)))
            ).pack(anchor='w')
        
        # Email
        email = self.footer_settings.get('footer_email', '')
        if email:
            tk.Label(
                business_frame,
                text=f"✉️ {email}",
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)))
            ).pack(anchor='w')
    
    def create_receipt_section(self, parent):
        """Create receipt information section"""
        receipt_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        receipt_frame.pack(side='left', padx=10)
        
        tk.Label(
            receipt_frame,
            text="Receipt Details",
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)) + 2, 'bold')
        ).pack(anchor='w')
        
        # Order ID
        order_id = self.current_order_data.get('order_id', self.current_order_data.get('order_number', 'N/A'))
        self.order_id_label = tk.Label(
            receipt_frame,
            text=f"Order #: {order_id}",
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)))
        )
        self.order_id_label.pack(anchor='w')
        
        # Date and Time
        self.datetime_label = tk.Label(
            receipt_frame,
            text="",
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)))
        )
        self.datetime_label.pack(anchor='w')
        
        # Table
        table_name = self.current_order_data.get('table_name', self.current_order_data.get('table_number', ''))
        if table_name:
            self.table_label = tk.Label(
                receipt_frame,
                text=f"Table: {table_name}",
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)))
            )
            self.table_label.pack(anchor='w')
    
    def create_user_section(self, parent):
        """Create user information section"""
        user_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        user_frame.pack(side='left', padx=10)
        
        tk.Label(
            user_frame,
            text="Staff Information",
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)) + 2, 'bold')
        ).pack(anchor='w')
        
        # User name
        user_name = self.current_user_data.get('name', self.current_user_data.get('username', 'Staff'))
        self.user_name_label = tk.Label(
            user_frame,
            text=f"Served by: {user_name}",
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)))
        )
        self.user_name_label.pack(anchor='w')
        
        # User ID
        if self.footer_settings.get('footer_show_user_id', 'false').lower() == 'true':
            user_id = self.current_user_data.get('id', '')
            if user_id:
                tk.Label(
                    user_frame,
                    text=f"ID: {user_id}",
                    bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                    fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                    font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                          int(self.footer_settings.get('footer_font_size', 10)))
                ).pack(anchor='w')
    
    def create_custom_section(self, parent):
        """Create custom text section"""
        custom_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        custom_frame.pack(side='left', padx=10)
        
        custom_text = self.footer_settings.get('footer_custom_text', '')
        if custom_text:
            # Process placeholders
            processed_text = self.process_placeholders(custom_text)
            
            tk.Label(
                custom_frame,
                text=processed_text,
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10))),
                wraplength=300
            ).pack(anchor='w')
    
    def create_bottom_bar(self, parent):
        """Create bottom status bar"""
        bottom_frame = tk.Frame(parent, bg=self.footer_settings.get('footer_background_color', '#2c3e50'))
        bottom_frame.pack(fill='x', side='bottom')
        
        # Left side - Timestamp
        if self.footer_settings.get('footer_show_timestamp', 'true').lower() == 'true':
            self.timestamp_label = tk.Label(
                bottom_frame,
                text="",
                bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
                fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
                font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                      int(self.footer_settings.get('footer_font_size', 10)) - 1)
            )
            self.timestamp_label.pack(side='left', padx=5)
        
        # Right side - Status
        status_text = "Restaurant POS System"
        tk.Label(
            bottom_frame,
            text=status_text,
            bg=self.footer_settings.get('footer_background_color', '#2c3e50'),
            fg=self.footer_settings.get('footer_text_color', '#ecf0f1'),
            font=(self.footer_settings.get('footer_font_family', 'Arial'), 
                  int(self.footer_settings.get('footer_font_size', 10)) - 1)
        ).pack(side='right', padx=5)
    
    def update_order_data(self, order_data: Dict):
        """Update current order data"""
        self.current_order_data = order_data or {}
        self.refresh_footer()
    
    def update_user_data(self, user_data: Dict):
        """Update current user data"""
        self.current_user_data = user_data or {}
        self.refresh_footer()
    
    def refresh_footer(self):
        """Refresh footer display"""
        self.create_footer_ui()
    
    def update_timestamp(self):
        """Update timestamp display"""
        if hasattr(self, 'timestamp_label') and self.footer_settings.get('footer_show_timestamp', 'true').lower() == 'true':
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.timestamp_label.config(text=current_time)
        
        if hasattr(self, 'datetime_label'):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.datetime_label.config(text=current_time)
        
        # Schedule next update
        self.after(1000, self.update_timestamp)  # Update every second
    
    def process_placeholders(self, text: str) -> str:
        """Process placeholders in custom text"""
        placeholders = {
            '{{user_name}}': self.current_user_data.get('name', self.current_user_data.get('username', 'Staff')),
            '{{date}}': datetime.now().strftime('%Y-%m-%d'),
            '{{time}}': datetime.now().strftime('%H:%M:%S'),
            '{{restaurant_name}}': self.footer_settings.get('footer_business_name', 'Restaurant POS'),
            '{{order_id}}': str(self.current_order_data.get('order_id', '')),
            '{{table_name}}': str(self.current_order_data.get('table_name', ''))
        }
        
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def reload_settings(self):
        """Reload footer settings and refresh"""
        self.load_footer_settings()
        self.refresh_footer()


class FooterSettingsDialog(tk.Toplevel):
    """
    Dialog for configuring footer settings
    """
    
    def __init__(self, parent, settings_manager=None):
        """
        Initialize footer settings dialog
        
        Args:
            parent: Parent window
            settings_manager: Settings manager instance
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.title("Footer Settings")
        self.geometry("600x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Make dialog modal
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # Create UI
        self.create_ui()
        
        # Load current settings
        self.load_settings()
    
    def create_ui(self):
        """Create dialog UI"""
        # Main notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # General tab
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text='General')
        self.create_general_tab(general_frame)
        
        # Business info tab
        business_frame = ttk.Frame(notebook)
        notebook.add(business_frame, text='Business Info')
        self.create_business_tab(business_frame)
        
        # Display tab
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text='Display')
        self.create_display_tab(display_frame)
        
        # Custom text tab
        custom_frame = ttk.Frame(notebook)
        notebook.add(custom_frame, text='Custom Text')
        self.create_custom_tab(custom_frame)
        
        # Style tab
        style_frame = ttk.Frame(notebook)
        notebook.add(style_frame, text='Style')
        self.create_style_tab(style_frame)
        
        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(button_frame, text="Save", command=self.on_save, bg='#4CAF50', fg='white').pack(side='right', padx=5)
        tk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side='right', padx=5)
        tk.Button(button_frame, text="Reset to Defaults", command=self.on_reset).pack(side='left', padx=5)
    
    def create_general_tab(self, parent):
        """Create general settings tab"""
        # Enable footer
        self.footer_enabled_var = tk.BooleanVar()
        tk.Checkbutton(parent, text="Enable Footer", variable=self.footer_enabled_var).pack(anchor='w', pady=5)
        
        # Footer alignment
        tk.Label(parent, text="Footer Alignment:").pack(anchor='w', pady=(10, 0))
        self.footer_alignment_var = tk.StringVar(value='center')
        alignment_frame = tk.Frame(parent)
        alignment_frame.pack(anchor='w', pady=5)
        tk.Radiobutton(alignment_frame, text="Left", variable=self.footer_alignment_var, value='left').pack(side='left')
        tk.Radiobutton(alignment_frame, text="Center", variable=self.footer_alignment_var, value='center').pack(side='left')
        tk.Radiobutton(alignment_frame, text="Right", variable=self.footer_alignment_var, value='right').pack(side='left')
    
    def create_business_tab(self, parent):
        """Create business information tab"""
        # Business name
        tk.Label(parent, text="Business Name:").pack(anchor='w', pady=5)
        self.business_name_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.business_name_var, width=50).pack(anchor='w', pady=5)
        
        # Address
        tk.Label(parent, text="Address:").pack(anchor='w', pady=5)
        self.address_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.address_var, width=50).pack(anchor='w', pady=5)
        
        # Phone
        tk.Label(parent, text="Phone:").pack(anchor='w', pady=5)
        self.phone_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.phone_var, width=50).pack(anchor='w', pady=5)
        
        # Email
        tk.Label(parent, text="Email:").pack(anchor='w', pady=5)
        self.email_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.email_var, width=50).pack(anchor='w', pady=5)
    
    def create_display_tab(self, parent):
        """Create display options tab"""
        # Show options
        self.show_business_info_var = tk.BooleanVar()
        self.show_receipt_info_var = tk.BooleanVar()
        self.show_user_name_var = tk.BooleanVar()
        self.show_user_id_var = tk.BooleanVar()
        self.show_timestamp_var = tk.BooleanVar()
        
        tk.Checkbutton(parent, text="Show Business Information", variable=self.show_business_info_var).pack(anchor='w', pady=5)
        tk.Checkbutton(parent, text="Show Receipt Information", variable=self.show_receipt_info_var).pack(anchor='w', pady=5)
        tk.Checkbutton(parent, text="Show User Name", variable=self.show_user_name_var).pack(anchor='w', pady=5)
        tk.Checkbutton(parent, text="Show User ID", variable=self.show_user_id_var).pack(anchor='w', pady=5)
        tk.Checkbutton(parent, text="Show Timestamp", variable=self.show_timestamp_var).pack(anchor='w', pady=5)
    
    def create_custom_tab(self, parent):
        """Create custom text tab"""
        # Custom text
        tk.Label(parent, text="Custom Footer Text:").pack(anchor='w', pady=5)
        tk.Label(parent, text="Available placeholders: {{user_name}}, {{date}}, {{time}}, {{restaurant_name}}, {{order_id}}", 
                font=('Arial', 8)).pack(anchor='w', pady=2)
        
        self.custom_text_var = tk.StringVar()
        text_widget = tk.Text(parent, width=60, height=8, wrap='word')
        text_widget.pack(anchor='w', pady=5, fill='both', expand=True)
        self.custom_text_widget = text_widget
        
        # Multiline option
        self.multiline_var = tk.BooleanVar()
        tk.Checkbutton(parent, text="Enable Multiline Footer", variable=self.multiline_var,
                     command=self.toggle_multiline).pack(anchor='w', pady=5)
        
        # Multiline lines (initially hidden)
        self.multiline_frame = tk.Frame(parent)
        
        tk.Label(self.multiline_frame, text="Line 1:").pack(anchor='w', pady=2)
        self.line1_var = tk.StringVar()
        tk.Entry(self.multiline_frame, textvariable=self.line1_var, width=60).pack(anchor='w', pady=2)
        
        tk.Label(self.multiline_frame, text="Line 2:").pack(anchor='w', pady=2)
        self.line2_var = tk.StringVar()
        tk.Entry(self.multiline_frame, textvariable=self.line2_var, width=60).pack(anchor='w', pady=2)
        
        tk.Label(self.multiline_frame, text="Line 3:").pack(anchor='w', pady=2)
        self.line3_var = tk.StringVar()
        tk.Entry(self.multiline_frame, textvariable=self.line3_var, width=60).pack(anchor='w', pady=2)
    
    def create_style_tab(self, parent):
        """Create style settings tab"""
        # Font settings
        tk.Label(parent, text="Font Family:").pack(anchor='w', pady=5)
        self.font_family_var = tk.StringVar()
        font_combo = ttk.Combobox(parent, textvariable=self.font_family_var, width=20)
        font_combo['values'] = ('Arial', 'Times New Roman', 'Courier New', 'Georgia', 'Verdana')
        font_combo.pack(anchor='w', pady=5)
        
        tk.Label(parent, text="Font Size:").pack(anchor='w', pady=5)
        self.font_size_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.font_size_var, width=10).pack(anchor='w', pady=5)
        
        # Color settings
        tk.Label(parent, text="Background Color:").pack(anchor='w', pady=5)
        self.bg_color_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.bg_color_var, width=15).pack(anchor='w', pady=5)
        
        tk.Label(parent, text="Text Color:").pack(anchor='w', pady=5)
        self.text_color_var = tk.StringVar()
        tk.Entry(parent, textvariable=self.text_color_var, width=15).pack(anchor='w', pady=5)
    
    def toggle_multiline(self):
        """Toggle multiline footer options"""
        if self.multiline_var.get():
            self.multiline_frame.pack(anchor='w', pady=5, fill='x')
        else:
            self.multiline_frame.pack_forget()
    
    def load_settings(self):
        """Load current settings into form"""
        # General settings
        self.footer_enabled_var.set(Settings.get('footer_enabled', 'true').lower() == 'true')
        self.footer_alignment_var.set(Settings.get('footer_alignment', 'center'))
        
        # Business info
        self.business_name_var.set(Settings.get('footer_business_name', ''))
        self.address_var.set(Settings.get('footer_address', ''))
        self.phone_var.set(Settings.get('footer_phone', ''))
        self.email_var.set(Settings.get('footer_email', ''))
        
        # Display options
        self.show_business_info_var.set(Settings.get('footer_show_business_info', 'true').lower() == 'true')
        self.show_receipt_info_var.set(Settings.get('footer_show_receipt_info', 'true').lower() == 'true')
        self.show_user_name_var.set(Settings.get('footer_show_user_name', 'true').lower() == 'true')
        self.show_user_id_var.set(Settings.get('footer_show_user_id', 'false').lower() == 'true')
        self.show_timestamp_var.set(Settings.get('footer_show_timestamp', 'true').lower() == 'true')
        
        # Custom text
        custom_text = Settings.get('footer_custom_text', 'Thank you for your business!')
        self.custom_text_widget.delete('1.0', 'end')
        self.custom_text_widget.insert('1.0', custom_text)
        
        self.multiline_var.set(Settings.get('footer_multiline', 'false').lower() == 'true')
        self.line1_var.set(Settings.get('footer_line1', ''))
        self.line2_var.set(Settings.get('footer_line2', ''))
        self.line3_var.set(Settings.get('footer_line3', ''))
        
        if self.multiline_var.get():
            self.toggle_multiline()
        
        # Style settings
        self.font_family_var.set(Settings.get('footer_font_family', 'Arial'))
        self.font_size_var.set(Settings.get('footer_font_size', '10'))
        self.bg_color_var.set(Settings.get('footer_background_color', '#2c3e50'))
        self.text_color_var.set(Settings.get('footer_text_color', '#ecf0f1'))
    
    def save_settings(self):
        """Save settings to database"""
        # General settings
        Settings.set('footer_enabled', str(self.footer_enabled_var.get()).lower())
        Settings.set('footer_alignment', self.footer_alignment_var.get())
        
        # Business info
        Settings.set('footer_business_name', self.business_name_var.get())
        Settings.set('footer_address', self.address_var.get())
        Settings.set('footer_phone', self.phone_var.get())
        Settings.set('footer_email', self.email_var.get())
        
        # Display options
        Settings.set('footer_show_business_info', str(self.show_business_info_var.get()).lower())
        Settings.set('footer_show_receipt_info', str(self.show_receipt_info_var.get()).lower())
        Settings.set('footer_show_user_name', str(self.show_user_name_var.get()).lower())
        Settings.set('footer_show_user_id', str(self.show_user_id_var.get()).lower())
        Settings.set('footer_show_timestamp', str(self.show_timestamp_var.get()).lower())
        
        # Custom text
        custom_text = self.custom_text_widget.get('1.0', 'end').strip()
        Settings.set('footer_custom_text', custom_text)
        Settings.set('footer_multiline', str(self.multiline_var.get()).lower())
        Settings.set('footer_line1', self.line1_var.get())
        Settings.set('footer_line2', self.line2_var.get())
        Settings.set('footer_line3', self.line3_var.get())
        
        # Style settings
        Settings.set('footer_font_family', self.font_family_var.get())
        Settings.set('footer_font_size', self.font_size_var.get())
        Settings.set('footer_background_color', self.bg_color_var.get())
        Settings.set('footer_text_color', self.text_color_var.get())
    
    def on_save(self):
        """Handle save button click"""
        self.save_settings()
        self.destroy()
    
    def on_cancel(self):
        """Handle cancel button click"""
        self.destroy()
    
    def on_reset(self):
        """Handle reset button click"""
        if tk.messagebox.askyesno("Reset Settings", "Are you sure you want to reset all footer settings to defaults?"):
            # Reset to defaults
            defaults = {
                'footer_enabled': 'true',
                'footer_alignment': 'center',
                'footer_business_name': '',
                'footer_address': '',
                'footer_phone': '',
                'footer_email': '',
                'footer_show_business_info': 'true',
                'footer_show_receipt_info': 'true',
                'footer_show_user_name': 'true',
                'footer_show_user_id': 'false',
                'footer_show_timestamp': 'true',
                'footer_custom_text': 'Thank you for your business!',
                'footer_multiline': 'false',
                'footer_line1': '',
                'footer_line2': '',
                'footer_line3': '',
                'footer_font_family': 'Arial',
                'footer_font_size': '10',
                'footer_background_color': '#2c3e50',
                'footer_text_color': '#ecf0f1'
            }
            
            for key, value in defaults.items():
                Settings.set(key, value)
            
            # Reload settings
            self.load_settings()
            tk.messagebox.showinfo("Reset Complete", "Footer settings have been reset to defaults.")