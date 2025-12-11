"""
Support Detail Screen for POS System
Detailed view for support tickets with conversations and attachments
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from typing import Dict, List, Optional

from src.ui.base_ui import BaseUI
from src.utils.support_manager import SupportManager
from src.utils.constants import *

class SupportDetailScreen(BaseUI):
    """Support ticket detail screen extending BaseUI"""
    
    def __init__(self, root, app, ticket_id, support_manager):
        super().__init__(root, app)
        
        self.ticket_id = ticket_id
        self.support_manager = support_manager
        
        # Ticket data
        self.ticket_data = None
        self.conversations_data = []
        self.attachments_data = []
        
        # UI components
        self.conversation_text = None
        self.attachments_tree = None
        
        # Load ticket data
        self.load_ticket_data()
    
    def show(self):
        """Show the support detail dialog"""
        if not self.ticket_data:
            messagebox.showerror("Error", "Ticket not found")
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title(f"Support Ticket #{self.ticket_id}")
        self.dialog.geometry("900x700")
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
        self._create_ticket_info(main_frame)
        self._create_conversation_section(main_frame)
        self._create_attachments_section(main_frame)
        self._create_action_section(main_frame)
        
        # Bind events
        main_frame.bind("<Configure>", self.on_frame_configure)
        main_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Center dialog
        self._center_dialog()
    
    def load_ticket_data(self):
        """Load ticket data from database"""
        try:
            ticket_details = self.support_manager.get_ticket_with_details(self.ticket_id)
            if ticket_details:
                self.ticket_data = ticket_details['ticket']
                self.conversations_data = ticket_details['conversations']
                self.attachments_data = ticket_details['attachments']
            else:
                print(f"Ticket {self.ticket_id} not found")
        except Exception as e:
            print(f"Error loading ticket data: {e}")
    
    def _create_ticket_info(self, parent):
        """Create ticket information section"""
        info_frame = self.create_modern_frame(parent, padding=SPACING_M)
        info_frame.pack(fill=tk.X, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            info_frame,
            f"Ticket #{self.ticket_id}: {self.ticket_data['title']}",
            style="SectionTitle.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Info grid
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X, pady=SPACING_S)
        
        # Ticket details
        details = [
            ("Status:", self.ticket_data['status'], self._get_status_color),
            ("Priority:", self.ticket_data['priority'], self._get_priority_color),
            ("Category:", self.ticket_data['category'], None),
            ("Created By:", str(self.ticket_data['created_by']), None),
            ("Assigned To:", str(self.ticket_data.get('assigned_to', 'Unassigned')), None),
            ("Created:", self._format_datetime(self.ticket_data['created_at']), None),
            ("Updated:", self._format_datetime(self.ticket_data['updated_at']), None)
        ]
        
        for i, (label, value, color_func) in enumerate(details):
            row_frame = ttk.Frame(info_grid)
            row_frame.grid(row=i, column=0, sticky=tk.W, pady=SPACING_XS)
            
            label_widget = self.create_modern_label(
                row_frame,
                label,
                style="Body.TLabel",
                width=15
            )
            label_widget.pack(side=tk.LEFT)
            
            value_widget = self.create_modern_label(
                row_frame,
                value,
                style="Body.TLabel"
            )
            if color_func:
                value_widget.configure(foreground=color_func(value))
            value_widget.pack(side=tk.LEFT, padx=(SPACING_S, 0))
        
        # Description
        desc_label = self.create_modern_label(
            info_frame,
            "Description:",
            style="CardTitle.TLabel"
        )
        desc_label.pack(anchor=tk.W, pady=(SPACING_M, SPACING_S))
        
        desc_text = scrolledtext.ScrolledText(
            info_frame,
            height=6,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        desc_text.pack(fill=tk.X, pady=(0, SPACING_M))
        desc_text.insert(tk.END, self.ticket_data['description'])
        desc_text.config(state=tk.DISABLED)
    
    def _create_conversation_section(self, parent):
        """Create conversation section"""
        conv_frame = self.create_modern_frame(parent, padding=SPACING_M)
        conv_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            conv_frame,
            "Conversation History",
            style="CardTitle.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Conversation display
        conv_display_frame = ttk.Frame(conv_frame)
        conv_display_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # Split into conversation list and message input
        conv_list_frame = ttk.Frame(conv_display_frame)
        conv_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create conversation list
        self._create_conversation_list(conv_list_frame)
        
        # Message input frame
        input_frame = ttk.Frame(conv_display_frame)
        input_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(SPACING_M, 0))
        
        # Message input
        msg_label = self.create_modern_label(
            input_frame,
            "Add Message:",
            style="Body.TLabel"
        )
        msg_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.conversation_text = tk.Text(
            input_frame,
            height=6,
            width=40,
            wrap=tk.WORD,
            font=('Arial', 10)
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True)
        
        # Send button
        send_btn = self.create_modern_button(
            input_frame,
            "Send Message",
            self.send_message,
            style="Primary.TButton"
        )
        send_btn.pack(fill=tk.X, pady=SPACING_S)
    
    def _create_conversation_list(self, parent):
        """Create conversation list with scrollbar"""
        # Create scrolled frame for conversations
        conv_canvas = tk.Canvas(parent, highlightthickness=0)
        conv_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=conv_canvas.yview)
        conv_list_frame = ttk.Frame(conv_canvas)
        
        # Configure canvas
        conv_canvas.configure(yscrollcommand=conv_scrollbar.set)
        conv_canvas_frame = conv_canvas.create_window((0, 0), window=conv_list_frame, anchor="nw")
        
        # Pack canvas and scrollbar
        conv_canvas.pack(side="left", fill="both", expand=True)
        conv_scrollbar.pack(side="right", fill="y")
        
        # Add conversation items
        for conversation in self.conversations_data:
            self._add_conversation_item(conv_list_frame, conversation)
    
    def _add_conversation_item(self, parent, conversation):
        """Add a single conversation item"""
        # Conversation item frame
        item_frame = self.create_modern_frame(parent, padding=SPACING_S)
        item_frame.pack(fill=tk.X, pady=SPACING_XS)
        
        # Header with sender and time
        header_frame = ttk.Frame(item_frame)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_XS))
        
        # Sender and role
        sender_color = COLOR_PRIMARY if conversation['sender_role'] == SUPPORT_ROLE_STAFF else COLOR_SECONDARY
        sender_label = self.create_modern_label(
            header_frame,
            f"{conversation['sender_role']} - {conversation['sender_id']}",
            style="Small.TLabel"
        )
        sender_label.configure(foreground=sender_color)
        sender_label.pack(side=tk.LEFT)
        
        # Time
        time_label = self.create_modern_label(
            header_frame,
            self._format_datetime(conversation['created_at']),
            style="Small.TLabel"
        )
        time_label.configure(foreground=COLOR_TEXT_SECONDARY)
        time_label.pack(side=tk.RIGHT)
        
        # Message
        msg_frame = ttk.Frame(item_frame)
        msg_frame.pack(fill=tk.X, pady=SPACING_XS)
        
        msg_text = tk.Text(
            msg_frame,
            height=3,
            wrap=tk.WORD,
            font=('Arial', 9),
            state=tk.DISABLED
        )
        msg_text.pack(fill=tk.X)
        msg_text.insert(tk.END, conversation['message'])
        
        # Internal indicator
        if conversation.get('is_internal', False):
            internal_label = self.create_modern_label(
                item_frame,
                "INTERNAL NOTE",
                style="Small.TLabel"
            )
            internal_label.configure(foreground=COLOR_WARNING)
            internal_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
    
    def _create_attachments_section(self, parent):
        """Create attachments section"""
        attach_frame = self.create_modern_frame(parent, padding=SPACING_M)
        attach_frame.pack(fill=tk.X, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            attach_frame,
            f"Attachments ({len(self.attachments_data)})",
            style="CardTitle.TLabel"
        )
        title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        if self.attachments_data:
            # Create attachments treeview
            self._create_attachments_tree(attach_frame)
        else:
            # No attachments message
            no_attach_label = self.create_modern_label(
                attach_frame,
                "No attachments for this ticket",
                style="Body.TLabel"
            )
            no_attach_label.pack(anchor=tk.W, pady=SPACING_S)
    
    def _create_attachments_tree(self, parent):
        """Create attachments treeview"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.X, pady=SPACING_S)
        
        columns = ('id', 'file_name', 'file_size', 'attachment_type', 'created_at')
        self.attachments_tree, scrollbar = self.create_modern_treeview(
            tree_frame,
            columns,
            ['ID', 'File Name', 'Size', 'Type', 'Uploaded'],
            column_widths=[50, 200, 80, 100, 120]
        )
        
        self.attachments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate tree
        for attachment in self.attachments_data:
            # Format file size
            size_mb = attachment['file_size'] / (1024 * 1024) if attachment['file_size'] else 0
            size_display = f"{size_mb:.2f} MB"
            
            self.attachments_tree.insert('', 'end', values=(
                attachment['id'],
                attachment['file_name'],
                size_display,
                attachment['attachment_type'],
                self._format_datetime(attachment['created_at'])
            ))
        
        # Bind double-click for download
        self.attachments_tree.bind("<Double-1>", self.on_attachment_double_click)
    
    def _create_action_section(self, parent):
        """Create action buttons section"""
        action_frame = self.create_button_group(parent, [
            ("Update Status", self.update_status, "Secondary.TButton"),
            ("Assign Ticket", self.assign_ticket, "Primary.TButton"),
            ("Close Ticket", self.close_ticket, "Success.TButton")
        ])
        action_frame.pack(fill=tk.X, pady=SPACING_M)
        
        # Add export button for admin users
        if self.app.current_user and self.app.current_user.get('role') == ROLE_ADMIN:
            export_btn = self.create_modern_button(
                action_frame,
                "Export Ticket",
                self.export_ticket,
                style="Secondary.TButton"
            )
            export_btn.pack(side=tk.LEFT, padx=SPACING_S)
    
    def send_message(self):
        """Send a new message to the conversation"""
        try:
            message = self.conversation_text.get(1.0, tk.END).strip()
            if not message:
                messagebox.showwarning("Validation Error", "Message cannot be empty.")
                return
            
            # Create conversation data
            conversation_data = {
                'ticket_id': self.ticket_id,
                'message': message,
                'sender_id': self.app.current_user['id'] if self.app.current_user else 1,
                'sender_role': self.app.current_user.get('role', SUPPORT_ROLE_USER) if self.app.current_user else SUPPORT_ROLE_USER,
                'message_type': 'text',
                'is_internal': False
            }
            
            # Add conversation
            conversation_id = self.support_manager.add_conversation_message(conversation_data)
            
            if conversation_id:
                # Clear input
                self.conversation_text.delete(1.0, tk.END)
                
                # Refresh conversations
                self.load_ticket_data()
                self._refresh_conversation_list()
                
                messagebox.showinfo("Success", "Message sent successfully!")
            else:
                messagebox.showerror("Error", "Failed to send message.")
        
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
    
    def update_status(self):
        """Update ticket status"""
        # Create status selection dialog
        status_dialog = tk.Toplevel(self.dialog)
        status_dialog.title("Update Ticket Status")
        status_dialog.geometry("300x200")
        status_dialog.transient(self.dialog)
        status_dialog.grab_set()
        
        # Status selection
        status_var = tk.StringVar(value=self.ticket_data['status'])
        ttk.Label(status_dialog, text="New Status:").pack(pady=SPACING_M)
        
        status_combo = ttk.Combobox(
            status_dialog,
            textvariable=status_var,
            values=[TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS, 
                    TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED],
            state="readonly",
            width=20
        )
        status_combo.pack(pady=SPACING_S)
        
        # Buttons
        button_frame = ttk.Frame(status_dialog)
        button_frame.pack(pady=SPACING_M)
        
        ttk.Button(button_frame, text="Update", 
                 command=lambda: self._update_status_action(status_var.get(), status_dialog)).pack(side=tk.LEFT, padx=SPACING_S)
        ttk.Button(button_frame, text="Cancel", 
                 command=status_dialog.destroy).pack(side=tk.LEFT)
    
    def assign_ticket(self):
        """Assign ticket to current user"""
        if self.app.current_user:
            success = self.support_manager.assign_ticket(
                self.ticket_id, 
                self.app.current_user['id']
            )
            
            if success:
                messagebox.showinfo("Success", "Ticket assigned successfully!")
                self.load_ticket_data()  # Refresh data
            else:
                messagebox.showerror("Error", "Failed to assign ticket.")
        else:
            messagebox.showerror("Error", "No user logged in.")
    
    def close_ticket(self):
        """Close the ticket"""
        # Get resolution from user
        resolution = messagebox.askstring("Close Ticket", 
                                      "Enter resolution details (optional):")
        
        success = self.support_manager.close_ticket(self.ticket_id, resolution)
        
        if success:
            messagebox.showinfo("Success", "Ticket closed successfully!")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to close ticket.")
    
    def export_ticket(self):
        """Export ticket details"""
        # This would export ticket details to a file
        messagebox.showinfo("Export", "Ticket export functionality not yet implemented.")
    
    def on_attachment_double_click(self, event):
        """Handle attachment double-click"""
        selection = self.attachments_tree.selection()
        if selection:
            item = self.attachments_tree.item(selection[0])
            attachment_id = item['values'][0]
            
            # Get attachment details and open/download
            messagebox.showinfo("Attachment", f"Attachment ID: {attachment_id}\nDownload functionality not yet implemented.")
    
    def _update_status_action(self, new_status, dialog):
        """Perform status update"""
        success = self.support_manager.update_ticket(self.ticket_id, {'status': new_status})
        
        if success:
            messagebox.showinfo("Success", "Status updated successfully!")
            self.load_ticket_data()  # Refresh data
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to update status.")
    
    def _refresh_conversation_list(self):
        """Refresh the conversation list"""
        # Clear and repopulate
        # This is a simplified refresh - in a real implementation, 
        # you'd want to preserve scroll position
        pass
    
    def _get_status_color(self, status):
        """Get color for status"""
        colors = {
            TICKET_STATUS_OPEN: COLOR_WARNING,
            TICKET_STATUS_IN_PROGRESS: COLOR_INFO,
            TICKET_STATUS_RESOLVED: COLOR_SUCCESS,
            TICKET_STATUS_CLOSED: COLOR_TEXT_SECONDARY
        }
        return colors.get(status, COLOR_TEXT_PRIMARY)
    
    def _get_priority_color(self, priority):
        """Get color for priority"""
        colors = {
            PRIORITY_LOW: COLOR_SUCCESS,
            PRIORITY_MEDIUM: COLOR_WARNING,
            PRIORITY_HIGH: COLOR_ERROR,
            PRIORITY_CRITICAL: COLOR_ERROR
        }
        return colors.get(priority, COLOR_TEXT_PRIMARY)
    
    def _format_datetime(self, dt):
        """Format datetime for display"""
        if isinstance(dt, str):
            return dt
        elif dt:
            return dt.strftime('%Y-%m-%d %H:%M')
        else:
            return "N/A"
    
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