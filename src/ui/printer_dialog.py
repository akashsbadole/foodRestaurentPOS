"""
Printer selection dialog for Restaurant POS System
Allows users to select printer type and specific printer for printing bills and KOTs
"""

import tkinter as tk
from tkinter import ttk, messagebox
from src.utils.constants import *
from src.utils.printer import PrinterManager, PrinterType, PaperSize


class PrinterSelectionDialog:
    """Dialog for selecting printer and print options"""
    
    def __init__(self, parent, settings, print_type="bill"):
        self.parent = parent
        self.settings = settings
        self.print_type = print_type  # "bill" or "kot"
        self.result = None
        
        # Initialize printer manager
        self.printer_manager = PrinterManager(settings)
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Select Printer for {print_type.title()}")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=COLOR_BACKGROUND_LIGHT)
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"600x500+{x}+{y}")
        
        self.setup_ui()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        # Main container with shadow effect
        shadow_container = tk.Frame(self.dialog, bg=COLOR_SHADOW)
        shadow_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        main_container = self.create_modern_frame(shadow_container, style="Card.TFrame", padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text=f"Select Printer for {self.print_type.title()}",
            font=(FONT_FAMILY_PRIMARY, 16, 'bold'),
            foreground=COLOR_TEXT_PRIMARY
        )
        title_label.pack(pady=(0, SPACING_L))
        
        # Printer type selection
        type_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        type_frame.pack(fill=tk.X, pady=SPACING_S)
        
        type_label = ttk.Label(
            type_frame,
            text="Printer Type:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        )
        type_label.pack(anchor=tk.W)
        
        self.printer_type_var = tk.StringVar()
        
        # Determine default printer type
        if self.print_type == "bill":
            default_type = self.settings.get('default_bill_printer_type', PrinterType.STANDARD)
        else:
            default_type = self.settings.get('default_kot_printer_type', PrinterType.THERMAL)
        
        self.printer_type_var.set(default_type)
        
        # Radio buttons for printer type
        radio_frame = ttk.Frame(type_frame)
        radio_frame.pack(fill=tk.X, pady=SPACING_S)
        
        ttk.Radiobutton(
            radio_frame,
            text="Thermal Printer (Receipt)",
            variable=self.printer_type_var,
            value=PrinterType.THERMAL,
            command=self.on_printer_type_change
        ).pack(side=tk.LEFT, padx=(0, SPACING_L))
        
        ttk.Radiobutton(
            radio_frame,
            text="Standard Printer (A4/Letter)",
            variable=self.printer_type_var,
            value=PrinterType.STANDARD,
            command=self.on_printer_type_change
        ).pack(side=tk.LEFT)
        
        # Printer selection frame
        self.printer_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        self.printer_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # Available printers
        self.available_printers = self.printer_manager.get_available_printers()
        
        # Printer selection
        printer_label = ttk.Label(
            self.printer_frame,
            text="Select Printer:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        )
        printer_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Printer combobox
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(
            self.printer_frame,
            textvariable=self.printer_var,
            state="readonly",
            font=(FONT_FAMILY_PRIMARY, 10)
        )
        self.printer_combo.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Paper size (for thermal printers)
        self.paper_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        
        paper_label = ttk.Label(
            self.paper_frame,
            text="Paper Width:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        )
        paper_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.paper_var = tk.StringVar()
        paper_combo = ttk.Combobox(
            self.paper_frame,
            textvariable=self.paper_var,
            values=["58mm", "80mm"],
            state="readonly",
            font=(FONT_FAMILY_PRIMARY, 10),
            width=15
        )
        paper_combo.pack(anchor=tk.W)
        
        # Set default paper width
        default_paper = self.settings.get(f'{self.print_type}_paper_width', '58')
        self.paper_var.set(f"{default_paper}mm")
        
        # Options frame
        options_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        options_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Preview checkbox
        self.preview_var = tk.BooleanVar(value=True)
        preview_check = ttk.Checkbutton(
            options_frame,
            text="Show preview before printing",
            variable=self.preview_var
        )
        preview_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Set as default checkbox
        self.set_default_var = tk.BooleanVar(value=False)
        default_check = ttk.Checkbutton(
            options_frame,
            text=f"Set as default printer for {self.print_type}",
            variable=self.set_default_var
        )
        default_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Test button
        test_button = ttk.Button(
            options_frame,
            text="Test Printer",
            command=self.test_printer
        )
        test_button.pack(anchor=tk.W, pady=SPACING_S)
        
        # Button frame
        button_frame = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_M)
        button_frame.pack(fill=tk.X, pady=(SPACING_L, 0))
        
        # Buttons
        button_container = ttk.Frame(button_frame)
        button_container.pack(fill=tk.X)
        
        ttk.Button(
            button_container,
            text="Print",
            command=self.print_selected,
            style="Success.TButton"
        ).pack(side=tk.RIGHT, padx=(SPACING_S, 0))
        
        ttk.Button(
            button_container,
            text="Cancel",
            command=self.cancel
        ).pack(side=tk.RIGHT)
        
        # Initialize printer list
        self.on_printer_type_change()
    
    def create_modern_frame(self, parent, style="Card.TFrame", padding=SPACING_M):
        """Create a modern frame with styling"""
        frame = ttk.Frame(parent, style=style, padding=padding)
        return frame
    
    def on_printer_type_change(self):
        """Handle printer type change"""
        printer_type = self.printer_type_var.get()
        
        # Update printer list
        if printer_type == PrinterType.THERMAL:
            printers = self.available_printers.get('thermal', [])
            self.paper_frame.pack(fill=tk.X, pady=SPACING_S)
        else:
            printers = self.available_printers.get('standard', [])
            self.paper_frame.pack_forget()
        
        # Update combobox
        self.printer_combo['values'] = printers
        if printers:
            # Select default printer
            default_printer = self.settings.get(f'{printer_type}_printer_name', '')
            if default_printer and default_printer in printers:
                self.printer_var.set(default_printer)
            else:
                self.printer_var.set(printers[0])
        else:
            self.printer_var.set('')
    
    def test_printer(self):
        """Test the selected printer"""
        printer_type = self.printer_type_var.get()
        printer_name = self.printer_var.get()
        
        if not printer_name:
            messagebox.showwarning("Warning", "Please select a printer first")
            return
        
        # Show testing message
        messagebox.showinfo("Test Print", 
                         f"Sending test print to {printer_name}...\n\n"
                         "Please check if the test print is successful.")
        
        # Test printer
        success = self.printer_manager.test_printer(printer_type, printer_name)
        
        if success:
            messagebox.showinfo("Success", "Test print successful!")
        else:
            messagebox.showerror("Error", "Test print failed. Please check printer connection.")
    
    def print_selected(self):
        """Print with selected options"""
        printer_type = self.printer_type_var.get()
        printer_name = self.printer_var.get()
        
        if not printer_name:
            messagebox.showwarning("Warning", "Please select a printer")
            return
        
        # Set as default if requested
        if self.set_default_var.get():
            if self.print_type == "bill":
                self.settings['default_bill_printer_type'] = printer_type
            else:
                self.settings['default_kot_printer_type'] = printer_type
            
            self.settings[f'{printer_type}_printer_name'] = printer_name
            
            if printer_type == PrinterType.THERMAL:
                paper_width = self.paper_var.get().replace('mm', '')
                self.settings[f'{self.print_type}_paper_width'] = paper_width
        
        # Return result
        self.result = {
            'printer_type': printer_type,
            'printer_name': printer_name,
            'paper_width': self.paper_var.get().replace('mm', '') if printer_type == PrinterType.THERMAL else None,
            'preview': self.preview_var.get()
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Get dialog result"""
        return self.result


class PrintPreviewDialog:
    """Dialog for showing print preview"""
    
    def __init__(self, parent, content, title="Print Preview"):
        self.parent = parent
        self.content = content
        self.title = title
        self.result = False
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("700x600")
        self.dialog.configure(bg=COLOR_BACKGROUND_LIGHT)
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"700x600+{x}+{y}")
        
        self.setup_ui()
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def setup_ui(self):
        """Setup the preview dialog"""
        # Main container
        main_container = ttk.Frame(self.dialog, padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_container,
            text=self.title,
            font=(FONT_FAMILY_PRIMARY, 16, 'bold'),
            foreground=COLOR_TEXT_PRIMARY
        )
        title_label.pack(pady=(0, SPACING_M))
        
        # Preview text area
        preview_frame = ttk.Frame(main_container)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(preview_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_text = tk.Text(
            text_frame,
            wrap=tk.NONE,
            font=('Courier New', 10),
            bg=COLOR_CARD_WHITE,
            fg=COLOR_TEXT_PRIMARY
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        
        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add content
        self.preview_text.insert(tk.END, self.content)
        self.preview_text.configure(state='disabled')
        
        # Button frame
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        # Buttons
        ttk.Button(
            button_frame,
            text="Print",
            command=self.print,
            style="Success.TButton"
        ).pack(side=tk.RIGHT, padx=(SPACING_S, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel
        ).pack(side=tk.RIGHT)
    
    def print(self):
        """Proceed with printing"""
        self.result = True
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel printing"""
        self.result = False
        self.dialog.destroy()
    
    def get_result(self):
        """Get dialog result"""
        return self.result