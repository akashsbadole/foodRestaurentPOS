"""
Support Screen for POS System
Main support dashboard for managing tickets, bug reports, and contact submissions
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.ui.base_ui import BaseUI
from src.utils.support_manager import SupportManager
from src.utils.bug_logger import BugLogger
from src.utils.contact_manager import ContactManager
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType

class SupportScreen(BaseUI):
    """Support dashboard screen extending BaseUI"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        
        # Initialize managers
        self.support_manager = SupportManager(self.db, getattr(app, 'email_service', None))
        self.bug_logger = BugLogger(self.db)
        self.contact_manager = ContactManager(self.db, getattr(app, 'email_service', None))
        
        # Current filters
        self.current_filter = {
            'status': 'All',
            'priority': 'All',
            'category': 'All',
            'search': ''
        }
        
        # Data storage
        self.tickets_data = []
        self.bugs_data = []
        self.contacts_data = []
        
        # Current view
        self.current_view = 'tickets'  # tickets, bugs, contacts
        
        # UI components
        self.ticket_tree = None
        self.bug_tree = None
        self.contact_tree = None
        
        # Subscribe to events
        event_dispatcher.subscribe(EventType.SUPPORT_TICKET_CREATED, self.on_ticket_created)
        event_dispatcher.subscribe(EventType.SUPPORT_TICKET_UPDATED, self.on_ticket_updated)
        event_dispatcher.subscribe(EventType.BUG_REPORT_CREATED, self.on_bug_created)
        event_dispatcher.subscribe(EventType.CONTACT_SUBMISSION_CREATED, self.on_contact_created)
    
    def show(self, parent_frame):
        """Display the support screen"""
        self.clear_frame(parent_frame)
        
        # Configure styles
        self.configure_styles()
        
        # Create main container
        main_container = self.create_modern_frame(parent_frame)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Create header
        self._create_header(main_container)
        
        # Create tab control
        self._create_tab_control(main_container)
        
        # Create status bar
        self._create_status_bar(main_container)
        
        # Load initial data
        self.refresh_data()
    
    def _create_header(self, parent):
        """Create header section with statistics"""
        header_frame = self.create_modern_frame(parent, padding=SPACING_S)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Title
        title_label = self.create_modern_label(
            header_frame, 
            "Support Dashboard", 
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        # Statistics frame
        stats_frame = self.create_modern_frame(header_frame, padding=SPACING_S)
        stats_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Get statistics
        ticket_stats = self.support_manager.get_ticket_statistics()
        bug_stats = self.bug_logger.get_bug_statistics()
        contact_stats = self.contact_manager.get_submission_statistics()
        
        # Create stats display
        stats_data = [
            ("Open Tickets", ticket_stats.get('open_tickets', 0), COLOR_WARNING),
            ("Total Tickets", ticket_stats.get('total_tickets', 0), COLOR_PRIMARY),
            ("New Bugs", bug_stats.get('status_new', 0), COLOR_ERROR),
            ("New Contacts", contact_stats.get('new_submissions', 0), COLOR_SUCCESS)
        ]
        
        for i, (label, value, color) in enumerate(stats_data):
            stat_frame = ttk.Frame(stats_frame)
            stat_frame.pack(side=tk.LEFT, padx=SPACING_S)
            
            stat_label = ttk.Label(
                stat_frame,
                text=label,
                font=('Arial', 10),
                foreground=COLOR_TEXT_SECONDARY
            )
            stat_label.pack(anchor=tk.W)
            
            value_label = ttk.Label(
                stat_frame,
                text=str(value),
                font=('Arial', 16, 'bold'),
                foreground=color
            )
            value_label.pack(anchor=tk.W)
    
    def _create_tab_control(self, parent):
        """Create tab control for different support views"""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tickets tab
        tickets_frame = ttk.Frame(notebook)
        notebook.add(tickets_frame, text="Support Tickets")
        self._create_tickets_view(tickets_frame)
        
        # Bug reports tab
        bugs_frame = ttk.Frame(notebook)
        notebook.add(bugs_frame, text="Bug Reports")
        self._create_bugs_view(bugs_frame)
        
        # Contact submissions tab
        contacts_frame = ttk.Frame(notebook)
        notebook.add(contacts_frame, text="Contact Submissions")
        self._create_contacts_view(contacts_frame)
        
        # Bind tab change event
        notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def _create_tickets_view(self, parent):
        """Create support tickets view"""
        # Create filter frame
        filter_frame = self.create_modern_frame(parent, padding=SPACING_S)
        filter_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Status filter
        self.ticket_status_var = tk.StringVar(value="All")
        status_combo = self.create_modern_combobox(
            filter_frame,
            self.ticket_status_var,
            ["All", TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS, 
             TICKET_STATUS_RESOLVED, TICKET_STATUS_CLOSED],
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=SPACING_S)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_tickets())
        
        # Priority filter
        self.ticket_priority_var = tk.StringVar(value="All")
        priority_combo = self.create_modern_combobox(
            filter_frame,
            self.ticket_priority_var,
            ["All", PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH, PRIORITY_CRITICAL],
            width=15
        )
        priority_combo.pack(side=tk.LEFT, padx=SPACING_S)
        priority_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_tickets())
        
        # Search box
        self.ticket_search_var = tk.StringVar()
        search_entry = self.create_modern_entry(
            filter_frame,
            textvariable=self.ticket_search_var,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=SPACING_S, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_tickets())
        
        # Buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(side=tk.RIGHT, padx=SPACING_S)
        
        new_ticket_btn = self.create_modern_button(
            button_frame,
            "New Ticket",
            self.show_new_ticket_dialog,
            style="Primary.TButton"
        )
        new_ticket_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        refresh_btn = self.create_modern_button(
            button_frame,
            "Refresh",
            self.refresh_tickets,
            style="Secondary.TButton"
        )
        refresh_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        # Create tickets treeview
        self._create_tickets_tree(parent)
    
    def _create_tickets_tree(self, parent):
        """Create tickets treeview"""
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        columns = ('id', 'title', 'category', 'priority', 'status', 'created_by', 'created_at')
        self.ticket_tree, scrollbar = self.create_modern_treeview(
            tree_frame,
            columns,
            ['ID', 'Title', 'Category', 'Priority', 'Status', 'Created By', 'Created'],
            column_widths=[60, 200, 100, 80, 100, 100, 120]
        )
        
        self.ticket_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags for status colors
        self.ticket_tree.tag_configure('open', background=COLOR_WARNING_LIGHT)
        self.ticket_tree.tag_configure('in_progress', background=COLOR_INFO)
        self.ticket_tree.tag_configure('resolved', background=COLOR_SUCCESS_LIGHT)
        self.ticket_tree.tag_configure('closed', background=COLOR_CARD_WHITE)
        
        # Configure tags for priority colors
        self.ticket_tree.tag_configure('low', foreground=COLOR_SUCCESS)
        self.ticket_tree.tag_configure('medium', foreground=COLOR_WARNING)
        self.ticket_tree.tag_configure('high', foreground=COLOR_ERROR)
        self.ticket_tree.tag_configure('critical', foreground=COLOR_ERROR, font=('Arial', 9, 'bold'))
        
        # Bind double-click for details
        self.ticket_tree.bind("<Double-1>", self.on_ticket_double_click)
        self.ticket_tree.bind("<Button-3>", self.on_ticket_right_click)
    
    def _create_bugs_view(self, parent):
        """Create bug reports view"""
        # Similar structure to tickets view but for bug reports
        filter_frame = self.create_modern_frame(parent, padding=SPACING_S)
        filter_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Status filter
        self.bug_status_var = tk.StringVar(value="All")
        status_combo = self.create_modern_combobox(
            filter_frame,
            self.bug_status_var,
            ["All", BUG_STATUS_NEW, BUG_STATUS_ASSIGNED, BUG_STATUS_IN_PROGRESS, 
             BUG_STATUS_FIXED, BUG_STATUS_VERIFIED, BUG_STATUS_CLOSED],
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=SPACING_S)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_bugs())
        
        # Severity filter
        self.bug_severity_var = tk.StringVar(value="All")
        severity_combo = self.create_modern_combobox(
            filter_frame,
            self.bug_severity_var,
            ["All", SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL],
            width=15
        )
        severity_combo.pack(side=tk.LEFT, padx=SPACING_S)
        severity_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_bugs())
        
        # Search box
        self.bug_search_var = tk.StringVar()
        search_entry = self.create_modern_entry(
            filter_frame,
            textvariable=self.bug_search_var,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=SPACING_S, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_bugs())
        
        # Buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(side=tk.RIGHT, padx=SPACING_S)
        
        new_bug_btn = self.create_modern_button(
            button_frame,
            "Report Bug",
            self.show_bug_report_dialog,
            style="Danger.TButton"
        )
        new_bug_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        refresh_btn = self.create_modern_button(
            button_frame,
            "Refresh",
            self.refresh_bugs,
            style="Secondary.TButton"
        )
        refresh_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        # Create bug treeview
        self._create_bugs_tree(parent)
    
    def _create_bugs_tree(self, parent):
        """Create bug reports treeview"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        columns = ('id', 'title', 'severity', 'status', 'module', 'created_at')
        self.bug_tree, scrollbar = self.create_modern_treeview(
            tree_frame,
            columns,
            ['ID', 'Title', 'Severity', 'Status', 'Module', 'Created'],
            column_widths=[60, 200, 80, 100, 100, 120]
        )
        
        self.bug_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags
        self.bug_tree.tag_configure('new', background=COLOR_ERROR_LIGHT)
        self.bug_tree.tag_configure('assigned', background=COLOR_WARNING_LIGHT)
        self.bug_tree.tag_configure('in_progress', background=COLOR_INFO)
        self.bug_tree.tag_configure('fixed', background=COLOR_SUCCESS_LIGHT)
        
        # Bind events
        self.bug_tree.bind("<Double-1>", self.on_bug_double_click)
        self.bug_tree.bind("<Button-3>", self.on_bug_right_click)
    
    def _create_contacts_view(self, parent):
        """Create contact submissions view"""
        # Similar structure to tickets view but for contact submissions
        filter_frame = self.create_modern_frame(parent, padding=SPACING_S)
        filter_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Status filter
        self.contact_status_var = tk.StringVar(value="All")
        status_combo = self.create_modern_combobox(
            filter_frame,
            self.contact_status_var,
            ["All", "New", "In Progress", "Closed"],
            width=15
        )
        status_combo.pack(side=tk.LEFT, padx=SPACING_S)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_contacts())
        
        # Type filter
        self.contact_type_var = tk.StringVar(value="All")
        type_combo = self.create_modern_combobox(
            filter_frame,
            self.contact_type_var,
            ["All", CONTACT_TYPE_GENERAL, CONTACT_TYPE_SUPPORT, 
             CONTACT_TYPE_FEEDBACK, CONTACT_TYPE_COMPLAINT],
            width=15
        )
        type_combo.pack(side=tk.LEFT, padx=SPACING_S)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_contacts())
        
        # Search box
        self.contact_search_var = tk.StringVar()
        search_entry = self.create_modern_entry(
            filter_frame,
            textvariable=self.contact_search_var,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=SPACING_S, fill=tk.X, expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self.filter_contacts())
        
        # Buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.pack(side=tk.RIGHT, padx=SPACING_S)
        
        new_contact_btn = self.create_modern_button(
            button_frame,
            "New Contact",
            self.show_contact_form_dialog,
            style="Success.TButton"
        )
        new_contact_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        refresh_btn = self.create_modern_button(
            button_frame,
            "Refresh",
            self.refresh_contacts,
            style="Secondary.TButton"
        )
        refresh_btn.pack(side=tk.LEFT, padx=SPACING_XS)
        
        # Create contact treeview
        self._create_contacts_tree(parent)
    
    def _create_contacts_tree(self, parent):
        """Create contact submissions treeview"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        columns = ('id', 'name', 'subject', 'contact_type', 'priority', 'status', 'created_at')
        self.contact_tree, scrollbar = self.create_modern_treeview(
            tree_frame,
            columns,
            ['ID', 'Name', 'Subject', 'Type', 'Priority', 'Status', 'Created'],
            column_widths=[60, 150, 200, 100, 80, 100, 120]
        )
        
        self.contact_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tags
        self.contact_tree.tag_configure('new', background=COLOR_SUCCESS_LIGHT)
        self.contact_tree.tag_configure('in_progress', background=COLOR_WARNING_LIGHT)
        self.contact_tree.tag_configure('closed', background=COLOR_CARD_WHITE)
        
        # Bind events
        self.contact_tree.bind("<Double-1>", self.on_contact_double_click)
        self.contact_tree.bind("<Button-3>", self.on_contact_right_click)
    
    def _create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=SPACING_XS, pady=SPACING_XS)
    
    def refresh_data(self):
        """Refresh all data"""
        self.refresh_tickets()
        self.refresh_bugs()
        self.refresh_contacts()
    
    def refresh_tickets(self):
        """Refresh tickets data"""
        try:
            filters = self._get_ticket_filters()
            self.tickets_data = self.support_manager.search_tickets('', filters)
            self._populate_tickets_tree()
            self.status_label.config(text=f"Loaded {len(self.tickets_data)} tickets")
        except Exception as e:
            self.show_message("Error", f"Failed to refresh tickets: {e}", "error")
    
    def refresh_bugs(self):
        """Refresh bug reports data"""
        try:
            filters = self._get_bug_filters()
            self.bugs_data = self.bug_logger.search_bugs('', filters)
            self._populate_bugs_tree()
            self.status_label.config(text=f"Loaded {len(self.bugs_data)} bug reports")
        except Exception as e:
            self.show_message("Error", f"Failed to refresh bug reports: {e}", "error")
    
    def refresh_contacts(self):
        """Refresh contact submissions data"""
        try:
            filters = self._get_contact_filters()
            self.contacts_data = self.contact_manager.search_submissions('', filters)
            self._populate_contacts_tree()
            self.status_label.config(text=f"Loaded {len(self.contacts_data)} contact submissions")
        except Exception as e:
            self.show_message("Error", f"Failed to refresh contact submissions: {e}", "error")
    
    def _get_ticket_filters(self):
        """Get current ticket filters"""
        filters = {}
        
        status = self.ticket_status_var.get()
        if status != "All":
            filters['status'] = status
        
        priority = self.ticket_priority_var.get()
        if priority != "All":
            filters['priority'] = priority
        
        search = self.ticket_search_var.get().strip()
        if search:
            filters['search'] = search
        
        return filters
    
    def _get_bug_filters(self):
        """Get current bug filters"""
        filters = {}
        
        status = self.bug_status_var.get()
        if status != "All":
            filters['status'] = status
        
        severity = self.bug_severity_var.get()
        if severity != "All":
            filters['severity'] = severity
        
        search = self.bug_search_var.get().strip()
        if search:
            filters['search'] = search
        
        return filters
    
    def _get_contact_filters(self):
        """Get current contact filters"""
        filters = {}
        
        status = self.contact_status_var.get()
        if status != "All":
            filters['status'] = status
        
        contact_type = self.contact_type_var.get()
        if contact_type != "All":
            filters['contact_type'] = contact_type
        
        search = self.contact_search_var.get().strip()
        if search:
            filters['search'] = search
        
        return filters
    
    def _populate_tickets_tree(self):
        """Populate tickets treeview with data"""
        # Clear existing items
        for item in self.ticket_tree.get_children():
            self.ticket_tree.delete(item)
        
        # Add tickets
        for ticket in self.tickets_data:
            status_tag = ticket['status'].lower().replace(" ", "_")
            priority_tag = ticket['priority'].lower()
            
            # Format created date
            created_at = ticket['created_at']
            if isinstance(created_at, str):
                created_display = created_at
            else:
                created_display = created_at.strftime('%Y-%m-%d %H:%M')
            
            self.ticket_tree.insert('', 'end', values=(
                ticket['id'],
                ticket['title'][:50] + '...' if len(ticket['title']) > 50 else ticket['title'],
                ticket['category'],
                ticket['priority'],
                ticket['status'],
                ticket['created_by'],
                created_display
            ), tags=(status_tag, priority_tag))
    
    def _populate_bugs_tree(self):
        """Populate bug reports treeview with data"""
        # Clear existing items
        for item in self.bug_tree.get_children():
            self.bug_tree.delete(item)
        
        # Add bug reports
        for bug in self.bugs_data:
            status_tag = bug['status'].lower().replace(" ", "_")
            severity_tag = bug['severity'].lower()
            
            # Format created date
            created_at = bug['created_at']
            if isinstance(created_at, str):
                created_display = created_at
            else:
                created_display = created_at.strftime('%Y-%m-%d %H:%M')
            
            self.bug_tree.insert('', 'end', values=(
                bug['id'],
                bug['title'][:50] + '...' if len(bug['title']) > 50 else bug['title'],
                bug['severity'],
                bug['status'],
                bug.get('module', ''),
                created_display
            ), tags=(status_tag, severity_tag))
    
    def _populate_contacts_tree(self):
        """Populate contact submissions treeview with data"""
        # Clear existing items
        for item in self.contact_tree.get_children():
            self.contact_tree.delete(item)
        
        # Add contact submissions
        for contact in self.contacts_data:
            status_tag = contact['status'].lower().replace(" ", "_")
            
            # Format created date
            created_at = contact['created_at']
            if isinstance(created_at, str):
                created_display = created_at
            else:
                created_display = created_at.strftime('%Y-%m-%d %H:%M')
            
            self.contact_tree.insert('', 'end', values=(
                contact['id'],
                contact['name'][:30] + '...' if len(contact['name']) > 30 else contact['name'],
                contact['subject'][:40] + '...' if len(contact['subject']) > 40 else contact['subject'],
                contact['contact_type'],
                contact['priority'],
                contact['status'],
                created_display
            ), tags=(status_tag,))
    
    def filter_tickets(self):
        """Filter tickets based on current filters"""
        self.refresh_tickets()
    
    def filter_bugs(self):
        """Filter bug reports based on current filters"""
        self.refresh_bugs()
    
    def filter_contacts(self):
        """Filter contact submissions based on current filters"""
        self.refresh_contacts()
    
    def on_tab_changed(self, event):
        """Handle tab change event"""
        selected_tab = event.widget.tab('current')
        if selected_tab == 0:
            self.current_view = 'tickets'
        elif selected_tab == 1:
            self.current_view = 'bugs'
        elif selected_tab == 2:
            self.current_view = 'contacts'
    
    def on_ticket_double_click(self, event):
        """Handle ticket double-click"""
        selection = self.ticket_tree.selection()
        if selection:
            item = self.ticket_tree.item(selection[0])
            ticket_id = item['values'][0]
            self.show_ticket_details(ticket_id)
    
    def on_bug_double_click(self, event):
        """Handle bug report double-click"""
        selection = self.bug_tree.selection()
        if selection:
            item = self.bug_tree.item(selection[0])
            bug_id = item['values'][0]
            self.show_bug_details(bug_id)
    
    def on_contact_double_click(self, event):
        """Handle contact submission double-click"""
        selection = self.contact_tree.selection()
        if selection:
            item = self.contact_tree.item(selection[0])
            contact_id = item['values'][0]
            self.show_contact_details(contact_id)
    
    def on_ticket_right_click(self, event):
        """Handle ticket right-click"""
        # Show context menu with actions
        pass
    
    def on_bug_right_click(self, event):
        """Handle bug report right-click"""
        # Show context menu with actions
        pass
    
    def on_contact_right_click(self, event):
        """Handle contact submission right-click"""
        # Show context menu with actions
        pass
    
    def show_new_ticket_dialog(self):
        """Show new ticket creation dialog"""
        from src.ui.support_ticket_dialog import SupportTicketDialog
        dialog = SupportTicketDialog(self.root, self.app, self.support_manager)
        dialog.show()
    
    def show_bug_report_dialog(self):
        """Show bug report dialog"""
        from src.ui.bug_report_dialog import BugReportDialog
        dialog = BugReportDialog(self.root, self.app, self.bug_logger)
        dialog.show()
    
    def show_contact_form_dialog(self):
        """Show contact form dialog"""
        from src.ui.contact_form_dialog import ContactFormDialog
        dialog = ContactFormDialog(self.root, self.app, self.contact_manager)
        dialog.show()
    
    def show_ticket_details(self, ticket_id):
        """Show ticket details dialog"""
        from src.ui.support_detail_screen import SupportDetailScreen
        dialog = SupportDetailScreen(self.root, self.app, ticket_id, self.support_manager)
        dialog.show()
    
    def show_bug_details(self, bug_id):
        """Show bug details dialog"""
        # This would open a bug details dialog
        # For now, show basic info
        bug = self.bug_logger.get_bug_report(bug_id)
        if bug:
            self.show_message("Bug Details", f"Title: {bug['title']}\n\nDescription: {bug['description']}", "info")
    
    def show_contact_details(self, contact_id):
        """Show contact details dialog"""
        contact = self.contact_manager.get_submission_by_id(contact_id)
        if contact:
            message = f"Name: {contact['name']}\n"
            message += f"Email: {contact['email']}\n"
            message += f"Subject: {contact['subject']}\n\n"
            message += f"Message: {contact['message']}"
            self.show_message("Contact Details", message, "info")
    
    def on_ticket_created(self, data):
        """Handle ticket created event"""
        if self.current_view == 'tickets':
            self.refresh_tickets()
    
    def on_ticket_updated(self, data):
        """Handle ticket updated event"""
        if self.current_view == 'tickets':
            self.refresh_tickets()
    
    def on_bug_created(self, data):
        """Handle bug created event"""
        if self.current_view == 'bugs':
            self.refresh_bugs()
    
    def on_contact_created(self, data):
        """Handle contact created event"""
        if self.current_view == 'contacts':
            self.refresh_contacts()