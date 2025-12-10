"""
Export Dialog for Restaurant POS System
Allows users to select export format and options for order export
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from src.utils.constants import *
import os


class ExportDialog:
    """Dialog for selecting export format and options"""
    
    def __init__(self, parent, settings, order_data=None):
        self.parent = parent
        self.settings = settings
        self.order_data = order_data
        self.result = None
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Order")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg=COLOR_BACKGROUND_LIGHT)
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")
        
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
            text="Export Order",
            font=(FONT_FAMILY_PRIMARY, 16, 'bold'),
            foreground=COLOR_TEXT_PRIMARY
        )
        title_label.pack(pady=(0, SPACING_L))
        
        # Export format selection
        format_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        format_frame.pack(fill=tk.X, pady=SPACING_S)
        
        format_label = ttk.Label(
            format_frame,
            text="Export Format:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        )
        format_label.pack(anchor=tk.W)
        
        # Format selection variables
        self.export_pdf_var = tk.BooleanVar(value=True)
        self.export_text_var = tk.BooleanVar(value=False)
        
        # Format checkboxes
        pdf_check = ttk.Checkbutton(
            format_frame,
            text="PDF Format (Professional Invoice)",
            variable=self.export_pdf_var,
            command=self.on_format_change
        )
        pdf_check.pack(anchor=tk.W, pady=SPACING_S)
        
        text_check = ttk.Checkbutton(
            format_frame,
            text="Text Format (Thermal Printer Compatible)",
            variable=self.export_text_var,
            command=self.on_format_change
        )
        text_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Export options frame
        options_frame = self.create_modern_frame(main_container, style="Panel.TFrame", padding=SPACING_M)
        options_frame.pack(fill=tk.X, pady=SPACING_S)
        
        options_label = ttk.Label(
            options_frame,
            text="Export Options:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        )
        options_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Preview checkbox
        self.preview_var = tk.BooleanVar(value=True)
        preview_check = ttk.Checkbutton(
            options_frame,
            text="Show preview before export",
            variable=self.preview_var
        )
        preview_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Auto-open checkbox
        self.auto_open_var = tk.BooleanVar(value=False)
        auto_open_check = ttk.Checkbutton(
            options_frame,
            text="Open file after export",
            variable=self.auto_open_var
        )
        auto_open_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Custom location checkbox
        self.custom_location_var = tk.BooleanVar(value=False)
        custom_location_check = ttk.Checkbutton(
            options_frame,
            text="Save to custom location",
            variable=self.custom_location_var,
            command=self.on_location_change
        )
        custom_location_check.pack(anchor=tk.W, pady=SPACING_S)
        
        # Location selection (initially hidden)
        self.location_frame = ttk.Frame(options_frame)
        
        location_label = ttk.Label(
            self.location_frame,
            text="Export Location:",
            font=(FONT_FAMILY_PRIMARY, 10),
            foreground=COLOR_TEXT_SECONDARY
        )
        location_label.pack(side=tk.LEFT, padx=(SPACING_L, SPACING_S))
        
        self.location_var = tk.StringVar()
        self.location_entry = ttk.Entry(
            self.location_frame,
            textvariable=self.location_var,
            width=40
        )
        self.location_entry.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        browse_button = ttk.Button(
            self.location_frame,
            text="Browse",
            command=self.browse_location
        )
        browse_button.pack(side=tk.LEFT)
        
        # Default export locations
        self.default_pdf_dir = os.path.join(os.getcwd(), 'exports', 'orders', 'pdf')
        self.default_text_dir = os.path.join(os.getcwd(), 'exports', 'orders', 'text')
        
        # Button frame
        button_frame = self.create_modern_frame(main_container, style="Card.TFrame", padding=SPACING_M)
        button_frame.pack(fill=tk.X, pady=(SPACING_L, 0))
        
        # Buttons
        button_container = ttk.Frame(button_frame)
        button_container.pack(fill=tk.X)
        
        ttk.Button(
            button_container,
            text="Export",
            command=self.export_order,
            style="Success.TButton"
        ).pack(side=tk.RIGHT, padx=(SPACING_S, 0))
        
        ttk.Button(
            button_container,
            text="Cancel",
            command=self.cancel
        ).pack(side=tk.RIGHT)
    
    def create_modern_frame(self, parent, style="Card.TFrame", padding=SPACING_M):
        """Create a modern frame with styling"""
        frame = ttk.Frame(parent, style=style, padding=padding)
        return frame
    
    def on_format_change(self):
        """Handle format selection change"""
        # Ensure at least one format is selected
        if not self.export_pdf_var.get() and not self.export_text_var.get():
            self.export_pdf_var.set(True)
    
    def on_location_change(self):
        """Handle custom location checkbox change"""
        if self.custom_location_var.get():
            self.location_frame.pack(fill=tk.X, pady=(SPACING_S, 0), after=self.location_frame.master.winfo_children()[-2])
            # Set default location
            if self.export_pdf_var.get():
                self.location_var.set(self.default_pdf_dir)
            else:
                self.location_var.set(self.default_text_dir)
        else:
            self.location_frame.pack_forget()
    
    def browse_location(self):
        """Browse for custom export location"""
        location = filedialog.askdirectory(
            title="Select Export Location",
            initialdir=self.location_var.get() or os.getcwd()
        )
        if location:
            self.location_var.set(location)
    
    def export_order(self):
        """Process the export with selected options"""
        # Validate at least one format is selected
        if not self.export_pdf_var.get() and not self.export_text_var.get():
            messagebox.showwarning("Warning", "Please select at least one export format")
            return
        
        # Validate custom location if selected
        if self.custom_location_var.get():
            location = self.location_var.get().strip()
            if not location:
                messagebox.showwarning("Warning", "Please specify an export location")
                return
            
            if not os.path.exists(location):
                try:
                    os.makedirs(location, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to create export directory: {e}")
                    return
        
        # Prepare result
        self.result = {
            'export_pdf': self.export_pdf_var.get(),
            'export_text': self.export_text_var.get(),
            'preview': self.preview_var.get(),
            'auto_open': self.auto_open_var.get(),
            'custom_location': self.custom_location_var.get(),
            'location': self.location_var.get() if self.custom_location_var.get() else None
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.result = None
        self.dialog.destroy()
    
    def get_result(self):
        """Get dialog result"""
        return self.result