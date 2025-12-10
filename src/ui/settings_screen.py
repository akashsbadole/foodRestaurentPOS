import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from src.utils.constants import *

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
        self.create_printer_settings_tab(notebook)
        self.create_export_settings_tab(notebook)
        self.create_footer_settings_tab(notebook)
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
    
    def create_printer_settings_tab(self, notebook):
        """Create Printer Settings tab with improved layout"""
        # Printer settings tab with modern card design
        printer_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(printer_frame, text="Printer Settings")
        
        # Tab description
        desc_label = self.create_modern_label(
            printer_frame,
            text="Configure printer settings for bills and kitchen orders",
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # Bill printer settings card with shadow effect
        shadow_container = tk.Frame(printer_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        bill_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        bill_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(bill_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header,
            text="🧾 Bill Printer Settings",
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
        # Form fields with improved layout
        form_container = ttk.Frame(bill_card, style="Panel.TFrame")
        form_container.pack(fill=tk.X)
        
        # Default bill printer type
        self.bill_printer_type_var = tk.StringVar(
            value=self.app.settings.get('default_bill_printer_type', DEFAULT_BILL_PRINTER_TYPE)
        )
        self.create_form_field(
            form_container,
            "Default Printer Type",
            entry_type="combobox",
            textvariable=self.bill_printer_type_var,
            values=["thermal", "standard"],
            state="readonly",
            width=28
        )
        
        # Thermal printer name for bills
        self.thermal_printer_var = tk.StringVar(
            value=self.app.settings.get('thermal_printer_name', DEFAULT_THERMAL_PRINTER)
        )
        self.create_form_field(
            form_container,
            "Thermal Printer Name",
            entry_type="entry",
            textvariable=self.thermal_printer_var,
            width=50
        )
        
        # Standard printer name for bills
        self.standard_printer_var = tk.StringVar(
            value=self.app.settings.get('standard_printer_name', DEFAULT_STANDARD_PRINTER)
        )
        self.create_form_field(
            form_container,
            "Standard Printer Name",
            entry_type="entry",
            textvariable=self.standard_printer_var,
            width=50
        )
        
        # Bill paper width
        self.bill_paper_width_var = tk.StringVar(
            value=str(self.app.settings.get('bill_paper_width', DEFAULT_BILL_PAPER_WIDTH))
        )
        self.create_form_field(
            form_container,
            "Bill Paper Width (mm)",
            entry_type="combobox",
            textvariable=self.bill_paper_width_var,
            values=["58", "80"],
            state="readonly",
            width=28
        )
        
        # Auto-print bill checkbox
        self.auto_print_bill_var = tk.BooleanVar(
            value=self.app.settings.get('auto_print_bill', DEFAULT_AUTO_PRINT_BILL) == 'True'
        )
        self.create_form_field(
            form_container,
            "Auto-print Bill after Payment",
            entry_type="checkbutton",
            textvariable=self.auto_print_bill_var
        )
        
        # KOT printer settings card with shadow effect
        kot_shadow_container = tk.Frame(printer_frame, bg=COLOR_SHADOW)
        kot_shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        kot_card = self.create_modern_frame(kot_shadow_container, style="Panel.TFrame", padding=SPACING_L)
        kot_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        kot_section_header = ttk.Frame(kot_card, style="Panel.TFrame")
        kot_section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        kot_section_title = self.create_modern_label(
            kot_section_header,
            text="🧾 KOT Printer Settings",
            style="SectionTitle.TLabel"
        )
        kot_section_title.pack(side=tk.LEFT)
        
        # KOT form fields
        kot_form_container = ttk.Frame(kot_card, style="Panel.TFrame")
        kot_form_container.pack(fill=tk.X)
        
        # Default KOT printer type
        self.kot_printer_type_var = tk.StringVar(
            value=self.app.settings.get('default_kot_printer_type', DEFAULT_KOT_PRINTER_TYPE)
        )
        self.create_form_field(
            kot_form_container,
            "Default KOT Printer Type",
            entry_type="combobox",
            textvariable=self.kot_printer_type_var,
            values=["thermal", "standard"],
            state="readonly",
            width=28
        )
        
        # KOT paper width
        self.kot_paper_width_var = tk.StringVar(
            value=str(self.app.settings.get('kot_paper_width', DEFAULT_KOT_PAPER_WIDTH))
        )
        self.create_form_field(
            kot_form_container,
            "KOT Paper Width (mm)",
            entry_type="combobox",
            textvariable=self.kot_paper_width_var,
            values=["58", "80"],
            state="readonly",
            width=28
        )
        
        # Auto-print KOT checkbox
        self.auto_print_kot_var = tk.BooleanVar(
            value=self.app.settings.get('auto_print_kot', DEFAULT_AUTO_PRINT_KOT) == 'True'
        )
        self.create_form_field(
            kot_form_container,
            "Auto-print KOT after Order",
            entry_type="checkbutton",
            textvariable=self.auto_print_kot_var
        )
    def create_export_settings_tab(self, notebook):
        """Create Export Settings tab with improved layout"""
        # Export settings tab with modern card design
        export_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(export_frame, text="Export Settings")
        
        # Tab description
        desc_label = self.create_modern_label(
            export_frame, 
            text="Configure export options for orders and invoices", 
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # Export settings card with shadow effect
        shadow_container = tk.Frame(export_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        export_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        export_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(export_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header, 
            text="📄 Export Configuration", 
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
        # Form fields with improved layout
        form_container = ttk.Frame(export_card, style="Panel.TFrame")
        form_container.pack(fill=tk.X)
        
        # Export after payment checkbox
        self.export_after_payment_var = tk.BooleanVar(
            value=self.app.settings.get('export_after_payment', 'false').lower() == 'true'
        )
        self.create_form_field(
            form_container,
            "Export Order After Payment",
            entry_type="checkbutton",
            textvariable=self.export_after_payment_var
        )
        
        # Default export format
        self.default_export_format_var = tk.StringVar(
            value=self.app.settings.get('default_export_format', 'none')
        )
        self.create_form_field(
            form_container,
            "Default Export Format",
            entry_type="combobox",
            textvariable=self.default_export_format_var,
            values=["none", "pdf", "text", "both"],
            state="readonly",
            width=28
        )
        
        # Show export dialog checkbox
        self.show_export_dialog_var = tk.BooleanVar(
            value=self.app.settings.get('show_export_dialog', 'true').lower() == 'true'
        )
        self.create_form_field(
            form_container,
            "Show Export Dialog After Payment",
            entry_type="checkbutton",
            textvariable=self.show_export_dialog_var
        )
        
        # Auto-open exported files checkbox
        self.auto_open_exported_var = tk.BooleanVar(
            value=self.app.settings.get('auto_open_exported_files', 'false').lower() == 'true'
        )
        self.create_form_field(
            form_container,
            "Auto-open Exported Files",
            entry_type="checkbutton",
            textvariable=self.auto_open_exported_var
        )
        
        # Information note
        note_frame = self.create_modern_frame(export_card, style="Card.TFrame", padding=SPACING_M)
        note_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        note_label = self.create_modern_label(
            note_frame,
            "💡 Export settings control how orders are exported after payment completion.",
            style="Small.TLabel"
        )
        note_label.pack(anchor=tk.W)
        
        # Test buttons
        test_button_frame = self.create_modern_frame(printer_frame, style="Card.TFrame", padding=SPACING_M)
        test_button_frame.pack(fill=tk.X, pady=SPACING_S)
        
        test_container = ttk.Frame(test_button_frame, style="Card.TFrame")
        test_container.pack(fill=tk.X)
        
        # Test buttons
        def test_thermal_printer():
            printer_name = self.thermal_printer_var.get()
            if not printer_name:
                self.show_message("Warning", "Please enter thermal printer name", "warning")
                return
            
            from src.utils.printer import PrinterManager
            manager = PrinterManager(self.app.settings)
            success = manager.test_printer("thermal", printer_name)
            
            if success:
                self.show_message("Success", "Thermal printer test successful!", "info")
            else:
                self.show_message("Error", "Thermal printer test failed", "error")
        
        def test_standard_printer():
            printer_name = self.standard_printer_var.get()
            if not printer_name:
                self.show_message("Warning", "Please enter standard printer name", "warning")
                return
            
            from src.utils.printer import PrinterManager
            manager = PrinterManager(self.app.settings)
            success = manager.test_printer("standard", printer_name)
            # Save export settings
            self.app.update_setting('export_after_payment', str(self.export_after_payment_var.get()))
            self.app.update_setting('default_export_format', self.default_export_format_var.get())
            self.app.update_setting('show_export_dialog', str(self.show_export_dialog_var.get()))
            self.app.update_setting('auto_open_exported_files', str(self.auto_open_exported_var.get()))
            
            if success:
                self.show_message("Success", "Standard printer test successful!", "info")
            else:
                self.show_message("Error", "Standard printer test failed", "error")
        
        # Create test button group
        self.create_button_group(
            test_container,
            [
                ("🧪 Test Thermal Printer", test_thermal_printer, "Primary.TButton"),
                ("🖨️ Test Standard Printer", test_standard_printer, "Secondary.TButton")
            ],
            spacing=SPACING_M
        )
    
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
            
            # Save printer settings
            self.app.update_setting('thermal_printer_name', self.thermal_printer_var.get())
            self.app.update_setting('standard_printer_name', self.standard_printer_var.get())
            self.app.update_setting('default_bill_printer_type', self.bill_printer_type_var.get())
            self.app.update_setting('default_kot_printer_type', self.kot_printer_type_var.get())
            self.app.update_setting('bill_paper_width', self.bill_paper_width_var.get())
            self.app.update_setting('kot_paper_width', self.kot_paper_width_var.get())
            self.app.update_setting('auto_print_bill', str(self.auto_print_bill_var.get()))
            self.app.update_setting('auto_print_kot', str(self.auto_print_kot_var.get()))
            
            # Save export settings
            self.app.update_setting('export_after_payment', str(self.export_after_payment_var.get()))
            self.app.update_setting('default_export_format', self.default_export_format_var.get())
            self.app.update_setting('show_export_dialog', str(self.show_export_dialog_var.get()))
            self.app.update_setting('auto_open_exported_files', str(self.auto_open_exported_var.get()))
            
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
            
            # Save footer settings
            self.app.update_setting('footer_enabled', str(self.footer_enabled_var.get()))
            self.app.update_setting('footer_template', self.footer_template_var.get())
            self.app.update_setting('footer_custom_text', self.footer_custom_text_var.get())
            self.app.update_setting('footer_alignment', self.footer_alignment_var.get())
            self.app.update_setting('footer_font_size', self.footer_font_size_var.get())
            self.app.update_setting('footer_show_user_name', str(self.footer_show_user_name_var.get()))
            self.app.update_setting('footer_show_receipt_info', str(self.footer_show_receipt_info_var.get()))
            self.app.update_setting('footer_show_business_info', str(self.footer_show_business_info_var.get()))
            self.app.update_setting('footer_multiline', str(self.footer_multiline_var.get()))
            self.app.update_setting('footer_line1', self.footer_line1_var.get())
            self.app.update_setting('footer_line2', self.footer_line2_var.get())
            self.app.update_setting('footer_line3', self.footer_line3_var.get())
            
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
        elif key == 'thermal_printer_name':
            self.thermal_printer_var.set(value)
        elif key == 'standard_printer_name':
            self.standard_printer_var.set(value)
        elif key == 'default_bill_printer_type':
            self.bill_printer_type_var.set(value)
        elif key == 'default_kot_printer_type':
            self.kot_printer_type_var.set(value)
        elif key == 'bill_paper_width':
            self.bill_paper_width_var.set(value)
        elif key == 'kot_paper_width':
            self.kot_paper_width_var.set(value)
        elif key == 'auto_print_bill':
            self.auto_print_bill_var.set(value == 'True')
        elif key == 'auto_print_kot':
            self.auto_print_kot_var.set(value == 'True')
        elif key == 'export_after_payment':
            self.export_after_payment_var.set(value == 'True')
        elif key == 'default_export_format':
            self.default_export_format_var.set(value)
        elif key == 'show_export_dialog':
            self.show_export_dialog_var.set(value == 'True')
        elif key == 'auto_open_exported_files':
            self.auto_open_exported_var.set(value == 'True')
        elif key == 'footer_enabled':
            self.footer_enabled_var.set(value == 'True')
        elif key == 'footer_template':
            self.footer_template_var.set(value)
        elif key == 'footer_custom_text':
            self.footer_custom_text_var.set(value)
        elif key == 'footer_alignment':
            self.footer_alignment_var.set(value)
        elif key == 'footer_font_size':
            self.footer_font_size_var.set(value)
        elif key == 'footer_show_user_name':
            self.footer_show_user_name_var.set(value == 'True')
        elif key == 'footer_show_receipt_info':
            self.footer_show_receipt_info_var.set(value == 'True')
        elif key == 'footer_show_business_info':
            self.footer_show_business_info_var.set(value == 'True')
        elif key == 'footer_multiline':
            self.footer_multiline_var.set(value == 'True')
        elif key == 'footer_line1':
            self.footer_line1_var.set(value)
        elif key == 'footer_line2':
            self.footer_line2_var.set(value)
        elif key == 'footer_line3':
            self.footer_line3_var.set(value)
    
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
    
    def create_footer_settings_tab(self, notebook):
        """Create the Footer Settings tab with improved layout"""
        # Footer settings tab with modern card design
        footer_frame = self.create_modern_frame(notebook, style="Card.TFrame", padding=SPACING_XL)
        notebook.add(footer_frame, text="Footer Settings")
        
        # Tab description
        desc_label = self.create_modern_label(
            footer_frame,
            text="Configure footer text and appearance for receipts and documents",
            style="Subtitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(0, SPACING_L))
        
        # Footer settings card with shadow effect
        shadow_container = tk.Frame(footer_frame, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.X, pady=SPACING_S)
        
        footer_card = self.create_modern_frame(shadow_container, style="Panel.TFrame", padding=SPACING_L)
        footer_card.pack(fill=tk.X, padx=1, pady=1)
        
        # Section header with icon
        section_header = ttk.Frame(footer_card, style="Panel.TFrame")
        section_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        section_title = self.create_modern_label(
            section_header,
            text="📝 Footer Configuration",
            style="SectionTitle.TLabel"
        )
        section_title.pack(side=tk.LEFT)
        
        # Form fields with improved layout
        form_container = ttk.Frame(footer_card, style="Panel.TFrame")
        form_container.pack(fill=tk.X)
        
        # Enable footer checkbox
        self.footer_enabled_var = tk.BooleanVar(
            value=self.app.settings.get('footer_enabled', 'true').lower() == 'true'
        )
        self.create_form_field(
            form_container,
            "Enable Footer on Documents",
            entry_type="checkbutton",
            textvariable=self.footer_enabled_var
        )
        
        # Footer template
        self.footer_template_var = tk.StringVar(
            value=self.app.settings.get('footer_template', 'default')
        )
        self.create_form_field(
            form_container,
            "Footer Template",
            entry_type="combobox",
            textvariable=self.footer_template_var,
            values=["default", "minimal", "detailed"],
            state="readonly",
            width=28
        )
        
        # Custom text
        self.footer_custom_text_var = tk.StringVar(
            value=self.app.settings.get('footer_custom_text', 'Thank you for your business!')
        )
        self.create_form_field(
            form_container,
            "Custom Footer Text",
            entry_type="entry",
            textvariable=self.footer_custom_text_var,
            width=50
        )
        
        # Alignment
        self.footer_alignment_var = tk.StringVar(
            value=self.app.settings.get('footer_alignment', 'center')
        )
        self.create_form_field(
            form_container,
            "Text Alignment",
            entry_type="combobox",
            textvariable=self.footer_alignment_var,
            values=["left", "center", "right"],
            state="readonly",
            width=28
        )
        
        # Font size
        self.footer_font_size_var = tk.StringVar(
            value=self.app.settings.get('footer_font_size', '10')
        )
        self.create_form_field(
            form_container,
            "Font Size",
            entry_type="combobox",
            textvariable=self.footer_font_size_var,
            values=["8", "10", "12", "14"],
            state="readonly",
            width=28
        )
        
        # Content options frame
        content_frame = self.create_modern_frame(footer_card, style="Card.TFrame", padding=SPACING_M)
        content_frame.pack(fill=tk.X, pady=SPACING_S)
        
        content_header = ttk.Frame(content_frame, style="Card.TFrame")
        content_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        content_title = self.create_modern_label(
            content_header,
            text="📄 Content Options",
            style="SectionTitle.TLabel"
        )
        content_title.pack(side=tk.LEFT)
        
        content_form_container = ttk.Frame(content_frame, style="Panel.TFrame")
        content_form_container.pack(fill=tk.X)
        
        # Show user name checkbox
        self.footer_show_user_name_var = tk.BooleanVar(
            value=self.app.settings.get('footer_show_user_name', 'true').lower() == 'true'
        )
        self.create_form_field(
            content_form_container,
            "Show User Name",
            entry_type="checkbutton",
            textvariable=self.footer_show_user_name_var
        )
        
        # Show receipt info checkbox
        self.footer_show_receipt_info_var = tk.BooleanVar(
            value=self.app.settings.get('footer_show_receipt_info', 'true').lower() == 'true'
        )
        self.create_form_field(
            content_form_container,
            "Show Receipt Info",
            entry_type="checkbutton",
            textvariable=self.footer_show_receipt_info_var
        )
        
        # Show business info checkbox
        self.footer_show_business_info_var = tk.BooleanVar(
            value=self.app.settings.get('footer_show_business_info', 'true').lower() == 'true'
        )
        self.create_form_field(
            content_form_container,
            "Show Business Info",
            entry_type="checkbutton",
            textvariable=self.footer_show_business_info_var
        )
        
        # Multiline footer frame
        multiline_frame = self.create_modern_frame(footer_card, style="Card.TFrame", padding=SPACING_M)
        multiline_frame.pack(fill=tk.X, pady=SPACING_S)
        
        multiline_header = ttk.Frame(multiline_frame, style="Card.TFrame")
        multiline_header.pack(fill=tk.X, pady=(0, SPACING_M))
        
        multiline_title = self.create_modern_label(
            multiline_header,
            text="📝 Multiline Footer",
            style="SectionTitle.TLabel"
        )
        multiline_title.pack(side=tk.LEFT)
        
        multiline_form_container = ttk.Frame(multiline_frame, style="Panel.TFrame")
        multiline_form_container.pack(fill=tk.X)
        
        # Enable multiline checkbox
        self.footer_multiline_var = tk.BooleanVar(
            value=self.app.settings.get('footer_multiline', 'false').lower() == 'true'
        )
        self.create_form_field(
            multiline_form_container,
            "Enable Multiline Footer",
            entry_type="checkbutton",
            textvariable=self.footer_multiline_var
        )
        
        # Multiline text fields
        self.footer_line1_var = tk.StringVar(
            value=self.app.settings.get('footer_line1', '')
        )
        self.create_form_field(
            multiline_form_container,
            "Line 1",
            entry_type="entry",
            textvariable=self.footer_line1_var,
            width=50
        )
        
        self.footer_line2_var = tk.StringVar(
            value=self.app.settings.get('footer_line2', '')
        )
        self.create_form_field(
            multiline_form_container,
            "Line 2",
            entry_type="entry",
            textvariable=self.footer_line2_var,
            width=50
        )
        
        self.footer_line3_var = tk.StringVar(
            value=self.app.settings.get('footer_line3', '')
        )
        self.create_form_field(
            multiline_form_container,
            "Line 3",
            entry_type="entry",
            textvariable=self.footer_line3_var,
            width=50
        )
        
        # Preview button
        preview_button_frame = self.create_modern_frame(footer_frame, style="Card.TFrame", padding=SPACING_M)
        preview_button_frame.pack(fill=tk.X, pady=SPACING_S)
        
        preview_container = ttk.Frame(preview_button_frame, style="Card.TFrame")
        preview_container.pack(fill=tk.X)
        
        def preview_footer():
            from src.utils.footer_generator import FooterGenerator
            generator = FooterGenerator(self.app.settings)
            
            # Sample order data for preview
            sample_order = {
                'order_number': 'TEST001',
                'created_at': '2024-01-01 12:00:00'
            }
            
            # Sample user data for preview
            sample_user = {
                'username': self.app.current_user['username']
            }
            
            footer_lines = generator.generate_footer('receipt', sample_order, sample_user)
            
            # Show preview dialog
            preview_window = tk.Toplevel(self.app.root)
            preview_window.title("Footer Preview")
            preview_window.geometry("500x400")
            preview_window.configure(background=COLOR_BACKGROUND_LIGHT)
            preview_window.resizable(False, False)
            
            # Make window modal
            preview_window.transient(self.app.root)
            preview_window.grab_set()
            
            # Preview content
            preview_frame = self.create_modern_frame(preview_window, style="Card.TFrame", padding=SPACING_L)
            preview_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
            
            title_label = self.create_modern_label(
                preview_frame,
                text="Footer Preview",
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
            
            # Text widget for preview
            preview_text = tk.Text(preview_frame, height=15, width=60, wrap=tk.WORD)
            preview_text.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
            
            # Insert footer lines
            for line in footer_lines:
                preview_text.insert(tk.END, line + "\n")
            
            preview_text.config(state=tk.DISABLED)
            
            # Close button
            close_button = self.create_modern_button(
                preview_frame,
                text="Close",
                command=preview_window.destroy,
                style="Secondary.TButton"
            )
            close_button.pack(pady=SPACING_M)
        
        self.create_button_group(
            preview_container,
            [("👁 Preview Footer", preview_footer, "Primary.TButton")],
            spacing=SPACING_M
        )
    
    def update_footer_field(self, key, value):
        """Update footer field in settings"""
        self.app.settings.update(key, str(value))