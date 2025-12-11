"""
Bug Report Dialog for POS System
Dialog for submitting bug reports with automatic system information
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional

from src.ui.base_ui import BaseUI
from src.utils.bug_logger import BugLogger
from src.utils.constants import *

class BugReportDialog(BaseUI):
    """Dialog for creating bug reports"""
    
    def __init__(self, root, app, bug_logger):
        super().__init__(root, app)
        self.bug_logger = bug_logger
        
        # Dialog window
        self.dialog = None
        
        # Form variables
        self.title_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.category_var = tk.StringVar(value=TICKET_CATEGORY_BUG)
        self.severity_var = tk.StringVar(value=SEVERITY_MEDIUM)
        self.reproduction_steps_var = tk.StringVar()
        self.expected_behavior_var = tk.StringVar()
        self.actual_behavior_var = tk.StringVar()
        self.additional_info_var = tk.StringVar()
        
        # Attachment variables
        self.attachments = []
        
        # System info (auto-collected)
        self.system_info = ""
    
    def show(self):
        """Show the bug report dialog"""
        # Collect system information
        self.system_info = self.bug_logger.bug_model._collect_system_info()
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("Report a Bug")
        self.dialog.geometry("600x800")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.root)
        self.dialog.grab_set()
        
        # Configure styles
        self.configure_styles()
        
        # Create main container with scrollbar
        main_canvas = tk.Canvas(self.dialog)
        main_scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)
        
        # Configure canvas
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        main_canvas_frame = main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # Create content
        self._create_header_section(main_frame)
        self._create_basic_section(main_frame)
        self._create_details_section(main_frame)
        self._create_attachments_section(main_frame)
        self._create_system_info_section(main_frame)
        self._create_button_section(main_frame)
        
        # Bind events
        main_frame.bind("<Configure>", self.on_frame_configure)
        main_canvas.bind("<Configure>", self.on_canvas_configure)
        
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
            "Report a Bug",
            style="SectionTitle.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = self.create_modern_label(
            header_frame,
            "Please provide details about the bug you encountered",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
    
    def _create_basic_section(self, parent):
        """Create basic bug information section"""
        basic_frame = self.create_modern_frame(parent, padding=SPACING_S)
        basic_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            basic_frame,
            "Basic Information",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Title (required)
        title_field = self.create_form_field(
            basic_frame,
            "Bug Title *:",
            "entry",
            textvariable=self.title_var,
            width=60
        )
        
        # Category
        category_field = self.create_form_field(
            basic_frame,
            "Category:",
            "combobox",
            textvariable=self.category_var,
            values=[TICKET_CATEGORY_BUG, TICKET_CATEGORY_TECHNICAL, 
                    TICKET_CATEGORY_GENERAL, TICKET_CATEGORY_FEATURE],
            width=57
        )
        
        # Severity
        severity_field = self.create_form_field(
            basic_frame,
            "Severity:",
            "combobox",
            textvariable=self.severity_var,
            values=[SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL],
            width=57
        )
        
        # Description (required)
        desc_label = self.create_modern_label(
            basic_frame,
            "Description *:",
            style="Body.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        description_text = tk.Text(
            basic_frame,
            height=6,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        description_text.pack(fill=tk.X, pady=(0, SPACING_S))
        description_text.bind("<KeyRelease>", lambda e: self.description_var.set(description_text.get(1.0, tk.END)))
    
    def _create_details_section(self, parent):
        """Create detailed bug information section"""
        details_frame = self.create_modern_frame(parent, padding=SPACING_S)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            details_frame,
            "Detailed Information",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Reproduction Steps
        repro_label = self.create_modern_label(
            details_frame,
            "Steps to Reproduce:",
            style="Body.TLabel"
        )
        repro_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        repro_text = tk.Text(
            details_frame,
            height=4,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        repro_text.pack(fill=tk.X, pady=(0, SPACING_S))
        repro_text.bind("<KeyRelease>", lambda e: self.reproduction_steps_var.set(repro_text.get(1.0, tk.END)))
        
        # Expected Behavior
        expected_label = self.create_modern_label(
            details_frame,
            "Expected Behavior:",
            style="Body.TLabel"
        )
        expected_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        expected_text = tk.Text(
            details_frame,
            height=3,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        expected_text.pack(fill=tk.X, pady=(0, SPACING_S))
        expected_text.bind("<KeyRelease>", lambda e: self.expected_behavior_var.set(expected_text.get(1.0, tk.END)))
        
        # Actual Behavior
        actual_label = self.create_modern_label(
            details_frame,
            "Actual Behavior:",
            style="Body.TLabel"
        )
        actual_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        actual_text = tk.Text(
            details_frame,
            height=3,
            width=60,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        actual_text.pack(fill=tk.X, pady=(0, SPACING_S))
        actual_text.bind("<KeyRelease>", lambda e: self.actual_behavior_var.set(actual_text.get(1.0, tk.END)))
    
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
    
    def _create_system_info_section(self, parent):
        """Create system information section"""
        system_frame = self.create_modern_frame(parent, padding=SPACING_S)
        system_frame.pack(fill=tk.X, pady=SPACING_S)
        
        section_title = self.create_modern_label(
            system_frame,
            "System Information (Auto-collected)",
            style="CardTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # System info display
        info_text = tk.Text(
            system_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            font=('Courier', 9),
            state=tk.DISABLED
        )
        info_text.pack(fill=tk.X, pady=SPACING_S)
        info_text.insert(tk.END, self.system_info)
        
        # Add scrollbar
        info_scrollbar = ttk.Scrollbar(info_text)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        info_text.config(yscrollcommand=info_scrollbar.set)
        info_scrollbar.config(command=info_text.yview)
    
    def _create_button_section(self, parent):
        """Create button section"""
        button_frame = self.create_button_group(parent, [
            ("Submit Bug Report", self.submit_bug_report, "Danger.TButton"),
            ("Cancel", self.close_dialog, "Secondary.TButton")
        ])
        button_frame.pack(fill=tk.X, pady=SPACING_L)
    
    def add_attachment(self):
        """Add attachment to bug report"""
        file_path = filedialog.askopenfilename(
            title="Select Attachment",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Log files", "*.log *.txt"),
                ("Documents", "*.pdf *.doc *.docx *.xls *.xlsx"),
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
                           '.log', '.txt', '.pdf', '.doc', '.docx', 
                           '.xls', '.xlsx', '.zip', '.rar', '.7z']
        
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in allowed_extensions:
            return False
        
        return True
    
    def submit_bug_report(self):
        """Submit the bug report"""
        try:
            # Validate required fields
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("Validation Error", "Bug title is required.")
                return
            
            description = self.description_var.get().strip()
            if not description:
                messagebox.showerror("Validation Error", "Description is required.")
                return
            
            # Prepare bug report data
            bug_data = {
                'title': title,
                'description': description,
                'category': self.category_var.get(),
                'severity': self.severity_var.get(),
                'reproduction_steps': self.reproduction_steps_var.get().strip(),
                'expected_behavior': self.expected_behavior_var.get().strip(),
                'actual_behavior': self.actual_behavior_var.get().strip(),
                'user_data': self.additional_info_var.get().strip()
            }
            
            # Create bug report
            bug_id = self.bug_logger.create_manual_bug_report(
                bug_data, 
                self.app.current_user['id'] if self.app.current_user else None
            )
            
            if bug_id:
                # Add attachments if any
                if self.attachments:
                    from src.models.support_attachment import SupportAttachment
                    attachment_model = SupportAttachment(self.db)
                    
                    for attachment_path in self.attachments:
                        attachment_data = {
                            'bug_report_id': bug_id,
                            'file_path': attachment_path,
                            'uploaded_by': self.app.current_user['id'] if self.app.current_user else 1
                        }
                        attachment_model.add_attachment(attachment_data)
                
                messagebox.showinfo("Success", 
                                 f"Bug report submitted successfully!\nBug ID: {bug_id}")
                self.close_dialog()
            else:
                messagebox.showerror("Error", "Failed to submit bug report.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def close_dialog(self):
        """Close the dialog"""
        if self.dialog:
            self.dialog.destroy()
    
    def on_frame_configure(self, event):
        """Handle frame configure event"""
        # Update scroll region
        self.dialog.update_idletasks()
    
    def on_canvas_configure(self, event):
        """Handle canvas configure event"""
        # Update scroll region
        self.dialog.update_idletasks()
    
    def _center_dialog(self):
        """Center the dialog on screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')