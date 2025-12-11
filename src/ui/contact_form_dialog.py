"""
Contact Form Dialog for POS System
Dialog for submitting contact forms and inquiries
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from src.ui.base_ui import BaseUI
from src.utils.contact_manager import ContactManager
from src.utils.constants import *

class ContactFormDialog(BaseUI):
    """Dialog for creating contact form submissions"""
    
    def __init__(self, root, app, contact_manager):
        super().__init__(root, app)
        self.contact_manager = contact_manager
        
        # Dialog window
        self.dialog = None
        
        # Form variables
        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.subject_var = tk.StringVar()
        self.message_var = tk.StringVar()
        self.contact_type_var = tk.StringVar(value=CONTACT_TYPE_GENERAL)
        self.priority_var = tk.StringVar(value=PRIORITY_MEDIUM)
    
    def show(self):
        """Show the contact form dialog"""
        # Create dialog window
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Contact Us")
        self.dialog.geometry("500x650")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        # Configure styles
        self.configure_styles()
        
        # Create main container
        main_container = self.create_modern_frame(self.dialog, padding=SPACING_M)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Create form sections
        self._create_header_section(main_container)
        self._create_personal_section(main_container)
        self._create_message_section(main_container)
        self._create_button_section(main_container)
        
        # Focus on name field
        self.dialog.focus_set()
        
        # Center dialog
        self._center_dialog()
    
    def _create_header_section(self, parent):
        """Create header section"""
        header_frame = self.create_modern_frame(parent, padding=SPACING_S)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        title_label = self.create_modern_label(
            header_frame,
            "Contact Us",
            style="SectionTitle.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = self.create_modern_label(
            header_frame,
            "Please provide your contact information and message",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
    
    def _create_personal_section(self, parent):
        """Create personal information section"""
        personal_frame = self.create_modern_frame(parent, padding=SPACING_S)
        personal_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            personal_frame,
            "Personal Information",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Name (required)
        name_field = self.create_form_field(
            personal_frame,
            "Name *:",
            "entry",
            textvariable=self.name_var,
            width=50
        )
        
        # Email (required)
        email_field = self.create_form_field(
            personal_frame,
            "Email *:",
            "entry",
            textvariable=self.email_var,
            width=50
        )
        
        # Phone (optional)
        phone_field = self.create_form_field(
            personal_frame,
            "Phone:",
            "entry",
            textvariable=self.phone_var,
            width=50
        )
        
        # Address (optional)
        address_label = self.create_modern_label(
            personal_frame,
            "Address:",
            style="Body.TLabel"
        )
        address_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        address_text = tk.Text(
            personal_frame,
            height=3,
            width=50,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        address_text.pack(fill=tk.X, pady=(0, SPACING_S))
        address_text.bind("<KeyRelease>", lambda e: self.address_var.set(address_text.get(1.0, tk.END)))
    
    def _create_message_section(self, parent):
        """Create message section"""
        message_frame = self.create_modern_frame(parent, padding=SPACING_S)
        message_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            message_frame,
            "Message Details",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Contact Type
        type_field = self.create_form_field(
            message_frame,
            "Contact Type:",
            "combobox",
            textvariable=self.contact_type_var,
            values=[CONTACT_TYPE_GENERAL, CONTACT_TYPE_SUPPORT, 
                    CONTACT_TYPE_FEEDBACK, CONTACT_TYPE_COMPLAINT],
            width=47
        )
        
        # Subject
        subject_field = self.create_form_field(
            message_frame,
            "Subject:",
            "entry",
            textvariable=self.subject_var,
            width=50
        )
        
        # Priority
        priority_field = self.create_form_field(
            message_frame,
            "Priority:",
            "combobox",
            textvariable=self.priority_var,
            values=[PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL],
            width=47
        )
        
        # Message (required)
        msg_label = self.create_modern_label(
            message_frame,
            "Message *:",
            style="Body.TLabel"
        )
        msg_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        message_text = tk.Text(
            message_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        message_text.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_S))
        message_text.bind("<KeyRelease>", lambda e: self.message_var.set(message_text.get(1.0, tk.END)))
        
        # Add scrollbar for message
        msg_scrollbar = ttk.Scrollbar(message_text)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        message_text.config(yscrollcommand=msg_scrollbar.set)
        msg_scrollbar.config(command=message_text.yview)
    
    def _create_button_section(self, parent):
        """Create button section"""
        button_frame = self.create_button_group(parent, [
            ("Submit", self.submit_contact, "Primary.TButton"),
            ("Cancel", self.close_dialog, "Secondary.TButton")
        ])
        button_frame.pack(fill=tk.X, pady=SPACING_L)
    
    def submit_contact(self):
        """Submit the contact form"""
        try:
            # Validate required fields
            name = self.name_var.get().strip()
            if not name:
                messagebox.showerror("Validation Error", "Name is required.")
                return
            
            email = self.email_var.get().strip()
            if not email:
                messagebox.showerror("Validation Error", "Email is required.")
                return
            
            # Basic email validation
            if '@' not in email or '.' not in email:
                messagebox.showerror("Validation Error", "Please enter a valid email address.")
                return
            
            message = self.message_var.get().strip()
            if not message:
                messagebox.showerror("Validation Error", "Message is required.")
                return
            
            # Prepare contact data
            contact_data = {
                'name': name,
                'email': email,
                'phone': self.phone_var.get().strip() or None,
                'address': self.address_var.get().strip() or None,
                'subject': self.subject_var.get().strip() or None,
                'message': message,
                'contact_type': self.contact_type_var.get(),
                'priority': self.priority_var.get()
            }
            
            # Create contact submission
            submission_id = self.contact_manager.create_submission(contact_data)
            
            if submission_id:
                messagebox.showinfo("Success", 
                                 f"Contact form submitted successfully!\nReference ID: {submission_id}")
                self.close_dialog()
            else:
                messagebox.showerror("Error", "Failed to submit contact form.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def close_dialog(self):
        """Close the dialog"""
        if self.dialog:
            self.dialog.destroy()
    
    def _center_dialog(self):
        """Center the dialog on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')