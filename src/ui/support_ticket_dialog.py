"""
Support Ticket Dialog for POS System
Dialog for creating new support tickets
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional

from src.ui.base_ui import BaseUI
from src.utils.support_manager import SupportManager
from src.utils.constants import *

class SupportTicketDialog(BaseUI):
    """Dialog for creating new support tickets"""
    
    def __init__(self, root, app, support_manager):
        super().__init__(root, app)
        self.support_manager = support_manager
        
        # Dialog window
        self.dialog = None
        
        # Form variables
        self.title_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.category_var = tk.StringVar(value=TICKET_CATEGORY_GENERAL)
        self.priority_var = tk.StringVar(value=PRIORITY_MEDIUM)
        self.customer_email_var = tk.StringVar()
        self.customer_phone_var = tk.StringVar()
        self.contact_info_var = tk.StringVar()
        self.order_id_var = tk.StringVar()
        self.table_id_var = tk.StringVar()
        
        # Attachment variables
        self.attachments = []
    
    def show(self):
        """Show the dialog"""
        # Create dialog window
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Create Support Ticket")
        self.dialog.geometry("600x700")
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
        self._create_details_section(main_container)
        self._create_customer_section(main_container)
        self._create_attachments_section(main_container)
        self._create_button_section(main_container)
        
        # Focus on title field
        self.dialog.focus_set()
        
        # Center dialog
        self._center_dialog()
    
    def _create_header_section(self, parent):
        """Create header section"""
        header_frame = self.create_modern_frame(parent, padding=SPACING_S)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        title_label = self.create_modern_label(
            header_frame,
            "Create Support Ticket",
            style="SectionTitle.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = self.create_modern_label(
            header_frame,
            "Please provide details about your issue or question",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
    
    def _create_details_section(self, parent):
        """Create ticket details section"""
        details_frame = self.create_modern_frame(parent, padding=SPACING_S)
        details_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            details_frame,
            "Ticket Details",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Title
        title_field = self.create_form_field(
            details_frame,
            "Title:",
            "entry",
            textvariable=self.title_var,
            width=50
        )
        
        # Category
        category_field = self.create_form_field(
            details_frame,
            "Category:",
            "combobox",
            textvariable=self.category_var,
            values=[TICKET_CATEGORY_GENERAL, TICKET_CATEGORY_TECHNICAL, 
                    TICKET_CATEGORY_BILLING, TICKET_CATEGORY_FEATURE, TICKET_CATEGORY_BUG],
            width=47
        )
        
        # Priority
        priority_field = self.create_form_field(
            details_frame,
            "Priority:",
            "combobox",
            textvariable=self.priority_var,
            values=[PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL],
            width=47
        )
        
        # Description
        desc_label = self.create_modern_label(
            details_frame,
            "Description:",
            style="Body.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        description_text = tk.Text(
            details_frame,
            height=8,
            width=50,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        description_text.pack(fill=tk.X, pady=(0, SPACING_S))
        description_text.bind("<KeyRelease>", lambda e: self.description_var.set(description_text.get(1.0, tk.END)))
        
        # Add scrollbar for description
        desc_scrollbar = ttk.Scrollbar(description_text)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        description_text.config(yscrollcommand=desc_scrollbar.set)
        desc_scrollbar.config(command=description_text.yview)
    
    def _create_customer_section(self, parent):
        """Create customer information section"""
        customer_frame = self.create_modern_frame(parent, padding=SPACING_S)
        customer_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            customer_frame,
            "Customer Information (Optional)",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Customer Email
        email_field = self.create_form_field(
            customer_frame,
            "Email:",
            "entry",
            textvariable=self.customer_email_var,
            width=50
        )
        
        # Customer Phone
        phone_field = self.create_form_field(
            customer_frame,
            "Phone:",
            "entry",
            textvariable=self.customer_phone_var,
            width=50
        )
        
        # Related Order ID
        order_field = self.create_form_field(
            customer_frame,
            "Related Order ID:",
            "entry",
            textvariable=self.order_id_var,
            width=50
        )
        
        # Related Table ID
        table_field = self.create_form_field(
            customer_frame,
            "Related Table ID:",
            "entry",
            textvariable=self.table_id_var,
            width=50
        )
        
        # Additional Contact Info
        contact_label = self.create_modern_label(
            customer_frame,
            "Additional Contact Info:",
            style="Body.TLabel"
        )
        contact_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        contact_text = tk.Text(
            customer_frame,
            height=3,
            width=50,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        contact_text.pack(fill=tk.X, pady=(0, SPACING_S))
        contact_text.bind("<KeyRelease>", lambda e: self.contact_info_var.set(contact_text.get(1.0, tk.END)))
    
    def _create_attachments_section(self, parent):
        """Create attachments section"""
        attachments_frame = self.create_modern_frame(parent, padding=SPACING_S)
        attachments_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            attachments_frame,
            "Attachments (Optional)",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Attachment buttons frame
        button_frame = ttk.Frame(attachments_frame)
        button_frame.pack(fill=tk.X, pady=SPACING_S)
        
        add_attachment_btn = self.create_modern_button(
            button_frame,
            "Add Attachment",
            self.add_attachment,
            style="Secondary.TButton"
        )
        add_attachment_btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        clear_attachments_btn = self.create_modern_button(
            button_frame,
            "Clear All",
            self.clear_attachments,
            style="Danger.TButton"
        )
        clear_attachments_btn.pack(side=tk.LEFT)
        
        # Attachments list
        self.attachments_listbox = tk.Listbox(
            attachments_frame,
            height=4,
            font=('Arial', 9)
        )
        self.attachments_listbox.pack(fill=tk.X, pady=SPACING_S)
        
        # Attachments scrollbar
        attachments_scrollbar = ttk.Scrollbar(self.attachments_listbox)
        attachments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.attachments_listbox.config(yscrollcommand=attachments_scrollbar.set)
        attachments_scrollbar.config(command=self.attachments_listbox.yview)
    
    def _create_button_section(self, parent):
        """Create button section"""
        button_frame = self.create_button_group(parent, [
            ("Submit Ticket", self.submit_ticket, "Primary.TButton"),
            ("Cancel", self.close_dialog, "Secondary.TButton")
        ])
        button_frame.pack(fill=tk.X, pady=SPACING_L)
    
    def add_attachment(self):
        """Add attachment to the ticket"""
        file_path = filedialog.askopenfilename(
            title="Select Attachment",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx *.txt *.log"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # Validate file
            if self._validate_attachment(file_path):
                self.attachments.append(file_path)
                
                # Add to listbox
                import os
                filename = os.path.basename(file_path)
                self.attachments_listbox.insert(tk.END, filename)
            else:
                messagebox.showerror("Invalid File", 
                                 "The selected file is not allowed or is too large.")
    
    def clear_attachments(self):
        """Clear all attachments"""
        self.attachments.clear()
        self.attachments_listbox.delete(0, tk.END)
    
    def _validate_attachment(self, file_path):
        """Validate attachment file"""
        import os
        
        # Check file size (25MB limit)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 25:
            return False
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                           '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                           '.txt', '.log', '.zip', '.rar', '.7z']
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in allowed_extensions:
            return False
        
        return True
    
    def submit_ticket(self):
        """Submit the support ticket"""
        try:
            # Validate required fields
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Validation Error", "Title is required.")
                return
            
            description = self.description_var.get().strip()
            if not description:
                messagebox.showerror("Validation Error", "Description is required.")
                return
            
            # Prepare ticket data
            ticket_data = {
                'title': title,
                'description': description,
                'category': self.category_var.get(),
                'priority': self.priority_var.get(),
                'created_by': self.app.current_user['id'] if self.app.current_user else 1,
                'customer_email': self.customer_email_var.get().strip() or None,
                'customer_phone': self.customer_phone_var.get().strip() or None,
                'contact_info': self.contact_info_var.get().strip() or None,
                'order_id': self.order_id_var.get().strip() or None,
                'table_id': self.table_id_var.get().strip() or None
            }
            
            # Create ticket
            ticket_id = self.support_manager.create_ticket(ticket_data, self.attachments)
            
            if ticket_id:
                messagebox.showinfo("Success", 
                                 f"Support ticket created successfully!\nTicket ID: {ticket_id}")
                self.close_dialog()
            else:
                messagebox.showerror("Error", "Failed to create support ticket.")
        
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