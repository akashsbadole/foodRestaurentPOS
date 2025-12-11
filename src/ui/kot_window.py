import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time
from .base_ui import BaseUI
from src.utils.helpers import generate_kot_content
from src.utils.printer import PrinterManager
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType
import winsound  # For Windows sound notifications
import platform
from src.utils.sound_manager import sound_manager

class KOTWindow(BaseUI):
    """Kitchen Order Ticket window that opens in a separate window"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.printer_manager = PrinterManager(app.settings)
        
        # Create new window for KOT
        self.kot_window = tk.Toplevel(root)
        self.kot_window.title("Kitchen Order Tickets (KOT)")
        self.kot_window.geometry("1400x800")
        self.kot_window.configure(bg=COLOR_BACKGROUND_DARK)
        
        # Make window stay on top
        self.kot_window.attributes('-topmost', True)
        
        # Center window on screen
        self.center_window()
        
        # Initialize variables
        self.auto_refresh = tk.BooleanVar(value=True)
        self.sound_enabled = tk.BooleanVar(value=sound_manager.is_enabled())
        self.current_filter = tk.StringVar(value="all")
        self.selected_orders = set()
        self.last_order_count = 0
        self.refresh_interval = None
        
        # Subscribe to events for real-time updates
        event_dispatcher.subscribe(EventType.ORDER_CREATED, self._on_order_created)
        event_dispatcher.subscribe(EventType.KOT_STATUS_CHANGED, self._on_kot_status_changed)
        
        # Setup UI
        self.setup_ui()
        
        # Start auto-refresh
        if self.auto_refresh.get():
            self.start_auto_refresh()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Handle window closing
        self.kot_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def center_window(self):
        """Center the KOT window on screen"""
        self.kot_window.update_idletasks()
        width = self.kot_window.winfo_width()
        height = self.kot_window.winfo_height()
        x = (self.kot_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.kot_window.winfo_screenheight() // 2) - (height // 2)
        self.kot_window.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """Setup KOT window UI with modern dark theme"""
        # Configure styles
        self.configure_styles()
        
        # Main container
        main_container = tk.Frame(self.kot_window, bg=COLOR_BACKGROUND_DARK)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Header section
        self.create_header(main_container)
        
        # Filter section
        self.create_filter_section(main_container)
        
        # Content area with columns
        self.create_content_area(main_container)
        
        # Bulk actions panel
        self.create_bulk_actions_panel(main_container)
        
        # Load initial data
        self.refresh_orders()
    
    def configure_styles(self):
        """Configure styles for KOT window"""
        style = ttk.Style()
        
        # Configure dark theme styles
        style.configure('Dark.TFrame', background=COLOR_BACKGROUND_DARK)
        style.configure('Card.TFrame', background=COLOR_CARD_DARK, relief='solid', bd=1)
        style.configure('Header.TFrame', background=COLOR_PRIMARY_DARK)
        
        # Button styles
        style.configure('Control.TButton',
                     background=COLOR_PRIMARY,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 10, 'bold'),
                     relief='flat',
                     padding=(SPACING_S, SPACING_S))
        
        style.configure('Filter.TButton',
                     background=COLOR_SECONDARY_DARK,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 10),
                     relief='flat',
                     padding=(SPACING_S, SPACING_S))
        
        style.configure('FilterActive.TButton',
                     background=COLOR_PRIMARY,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 10, 'bold'),
                     relief='flat',
                     padding=(SPACING_S, SPACING_S))
        
        # Label styles
        style.configure('Title.TLabel',
                     background=COLOR_BACKGROUND_DARK,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 18, 'bold'))
        
        style.configure('Header.TLabel',
                     background=COLOR_PRIMARY_DARK,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 14, 'bold'))
        
        style.configure('Card.TLabel',
                     background=COLOR_CARD_DARK,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 10))
        
        style.configure('Urgent.TLabel',
                     background=COLOR_ERROR,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 9, 'bold'))
        
        style.configure('Medium.TLabel',
                     background=COLOR_WARNING,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 9, 'bold'))
        
        style.configure('Normal.TLabel',
                     background=COLOR_SUCCESS,
                     foreground='white',
                     font=(FONT_FAMILY_PRIMARY, 9, 'bold'))
    
    def create_header(self, parent):
        """Create header section with controls"""
        header_frame = ttk.Frame(parent, style='Header.TFrame', padding=SPACING_M)
        header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Title
        title_label = ttk.Label(header_frame, text="🍳 Kitchen Order Tickets", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Control buttons
        controls_frame = ttk.Frame(header_frame, style='Header.TFrame')
        controls_frame.pack(side=tk.RIGHT, padx=(SPACING_L, 0))
        
        # Auto-refresh toggle
        self.auto_refresh_btn = ttk.Button(
            controls_frame,
            text="🔄 Auto Refresh",
            style='Control.TButton',
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        # Sound toggle
        self.sound_btn = ttk.Button(
            controls_frame,
            text="🔊 Sound",
            style='Control.TButton',
            command=self.toggle_sound
        )
        self.sound_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        # Refresh button
        refresh_btn = ttk.Button(
            controls_frame,
            text="🔄 Refresh",
            style='Control.TButton',
            command=self.refresh_orders
        )
        refresh_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        # Print all button
        print_all_btn = ttk.Button(
            controls_frame,
            text="🖨️ Print All",
            style='Control.TButton',
            command=self.print_all_pending
        )
        print_all_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        # Bulk actions button
        bulk_btn = ttk.Button(
            controls_frame,
            text="📋 Bulk Actions",
            style='Control.TButton',
            command=self.toggle_bulk_actions
        )
        bulk_btn.pack(side=tk.LEFT, padx=SPACING_S)
    
    def create_filter_section(self, parent):
        """Create filter section"""
        filter_frame = ttk.Frame(parent, style='Dark.TFrame', padding=SPACING_M)
        filter_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Filter buttons
        filters = [
            ("All Orders", "all"),
            ("New", "new"),
            ("In Progress", "progress"),
            ("Ready", "ready"),
            ("Completed", "completed")
        ]
        
        for text, value in filters:
            btn = ttk.Button(
                filter_frame,
                text=text,
                style='Filter.TButton',
                command=lambda v=value: self.set_filter(v)
            )
            btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            # Store button reference for style updates
            setattr(self, f'filter_btn_{value}', btn)
        
        # Update initial button styles
        self.update_filter_button_styles()
    
    def create_content_area(self, parent):
        """Create main content area with order columns"""
        content_frame = ttk.Frame(parent, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create three columns for different order statuses
        self.columns_frame = ttk.Frame(content_frame, style='Dark.TFrame')
        self.columns_frame.pack(fill=tk.BOTH, expand=True)
        
        # New Orders Column
        self.new_orders_frame = self.create_order_column(
            self.columns_frame, 
            "🆕 New Orders", 
            COLOR_ERROR,
            "new"
        )
        self.new_orders_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING_S))
        
        # In Progress Column
        self.progress_orders_frame = self.create_order_column(
            self.columns_frame, 
            "👨‍🍳 In Progress", 
            COLOR_WARNING,
            "progress"
        )
        self.progress_orders_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=SPACING_S)
        
        # Ready Orders Column
        self.ready_orders_frame = self.create_order_column(
            self.columns_frame, 
            "✅ Ready for Pickup", 
            COLOR_SUCCESS,
            "ready"
        )
        self.ready_orders_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(SPACING_S, 0))
    
    def create_order_column(self, parent, title, color, status_type):
        """Create a single order column"""
        column_frame = ttk.Frame(parent, style='Dark.TFrame')
        
        # Column header
        header_frame = tk.Frame(column_frame, bg=color, height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(
            header_frame,
            text=title,
            bg=color,
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 12, 'bold')
        )
        header_label.pack(expand=True, fill=tk.BOTH)
        
        # Order count label
        count_label = tk.Label(
            header_frame,
            text="0",
            bg=color,
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 10, 'bold')
        )
        count_label.place(relx=0.9, rely=0.5, anchor='e')
        
        # Scrollable area for orders
        canvas = tk.Canvas(column_frame, bg=COLOR_CARD_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(column_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Card.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Store references
        column_frame.canvas = canvas
        column_frame.scrollable_frame = scrollable_frame
        column_frame.count_label = count_label
        column_frame.status_type = status_type
        
        return column_frame
    
    def create_bulk_actions_panel(self, parent):
        """Create bulk actions panel"""
        self.bulk_actions_frame = ttk.Frame(parent, style='Card.TFrame', padding=SPACING_M)
        
        # Initially hidden
        self.bulk_actions_visible = False
        
        # Title
        title_label = ttk.Label(
            self.bulk_actions_frame,
            text="Bulk Actions",
            style='Header.TLabel'
        )
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Select all checkbox
        self.select_all_var = tk.BooleanVar()
        select_all_cb = ttk.Checkbutton(
            self.bulk_actions_frame,
            text="Select All Visible",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        select_all_cb.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Action buttons
        actions_frame = ttk.Frame(self.bulk_actions_frame, style='Card.TFrame')
        actions_frame.pack(fill=tk.X)
        
        start_all_btn = ttk.Button(
            actions_frame,
            text="▶️ Start All",
            style='Control.TButton',
            command=lambda: self.bulk_update_status('In Progress')
        )
        start_all_btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        ready_all_btn = ttk.Button(
            actions_frame,
            text="✅ Mark All Ready",
            style='Control.TButton',
            command=lambda: self.bulk_update_status('Ready')
        )
        ready_all_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        complete_all_btn = ttk.Button(
            actions_frame,
            text="✔️ Complete All",
            style='Control.TButton',
            command=lambda: self.bulk_update_status('Completed')
        )
        complete_all_btn.pack(side=tk.LEFT, padx=SPACING_S)
        
        close_btn = ttk.Button(
            actions_frame,
            text="❌ Close",
            style='Control.TButton',
            command=self.hide_bulk_actions
        )
        close_btn.pack(side=tk.RIGHT, padx=(SPACING_S, 0))
    
    def refresh_orders(self):
        """Refresh orders from database"""
        try:
            # Get orders based on current filter
            status_filter = self.get_status_filter()
            orders = self.app.kot_model.get_items(status_filter)
            
            # Clear existing order cards
            self.clear_all_columns()
            
            # Group orders by status
            new_orders = []
            progress_orders = []
            ready_orders = []
            
            for order in orders:
                item_id, order_number, name, quantity, created_at, status = order
                
                # Calculate order age and urgency
                time_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                current_time = datetime.now()
                order_age = current_time - time_obj
                
                urgency_level, urgency_color = self._get_urgency_level(order_age)
                
                order_data = {
                    'id': item_id,
                    'order_number': order_number,
                    'name': name,
                    'quantity': quantity,
                    'created_at': created_at,
                    'status': status,
                    'urgency_level': urgency_level,
                    'urgency_color': urgency_color,
                    'age_minutes': int(order_age.total_seconds() / 60)
                }
                
                if status == "Pending":
                    new_orders.append(order_data)
                elif status == "Preparing":
                    progress_orders.append(order_data)
                elif status == "Ready":
                    ready_orders.append(order_data)
            
            # Display orders in appropriate columns
            self.display_orders_in_column(self.new_orders_frame, new_orders)
            self.display_orders_in_column(self.progress_orders_frame, progress_orders)
            self.display_orders_in_column(self.ready_orders_frame, ready_orders)
            
            # Update counts
            self.update_order_counts()
            
            # Check for new orders and play sound
            if self.sound_enabled.get():
                self.check_for_new_orders(len(new_orders))
            
            self.last_order_count = len(new_orders)
            
        except Exception as e:
            print(f"Error refreshing orders: {e}")
            self.show_error_message("Failed to refresh orders")
    
    def get_status_filter(self):
        """Get database status filter based on current UI filter"""
        filter_map = {
            'all': None,  # Will get all active orders
            'new': 'Pending',
            'progress': 'Preparing',
            'ready': 'Ready',
            'completed': 'Completed'
        }
        return filter_map.get(self.current_filter.get(), None)
    
    def clear_all_columns(self):
        """Clear all order columns"""
        for column_frame in [self.new_orders_frame, self.progress_orders_frame, self.ready_orders_frame]:
            # Clear scrollable frame
            for widget in column_frame.scrollable_frame.winfo_children():
                widget.destroy()
    
    def display_orders_in_column(self, column_frame, orders):
        """Display orders in a specific column"""
        for order in orders:
            self.create_order_card(column_frame.scrollable_frame, order)
    
    def create_order_card(self, parent, order):
        """Create an order card"""
        # Main card container
        card_frame = tk.Frame(
            parent,
            bg=COLOR_CARD_DARK,
            relief='solid',
            bd=1,
            highlightbackground=order['urgency_color'],
            highlightthickness=3
        )
        card_frame.pack(fill=tk.X, pady=SPACING_S, padx=SPACING_S)
        
        # Order header
        header_frame = tk.Frame(card_frame, bg=COLOR_PRIMARY_DARK)
        header_frame.pack(fill=tk.X)
        
        # Order number and time
        order_info = f"Order #{order['order_number']} - {self.format_time(order['created_at'])}"
        order_label = tk.Label(
            header_frame,
            text=order_info,
            bg=COLOR_PRIMARY_DARK,
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 10, 'bold')
        )
        order_label.pack(side=tk.LEFT, padx=SPACING_S, pady=SPACING_S)
        
        # Urgency badge
        urgency_label = tk.Label(
            header_frame,
            text=order['urgency_level'].upper(),
            bg=order['urgency_color'],
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 8, 'bold')
        )
        urgency_label.pack(side=tk.RIGHT, padx=SPACING_S, pady=SPACING_S)
        
        # Item details
        item_frame = tk.Frame(card_frame, bg=COLOR_CARD_DARK)
        item_frame.pack(fill=tk.X, padx=SPACING_S, pady=SPACING_S)
        
        # Item name and quantity
        item_text = f"{order['quantity']}x {order['name']}"
        item_label = tk.Label(
            item_frame,
            text=item_text,
            bg=COLOR_CARD_DARK,
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 11)
        )
        item_label.pack(anchor=tk.W)
        
        # Age indicator
        age_text = f"Age: {order['age_minutes']} min"
        age_label = tk.Label(
            item_frame,
            text=age_text,
            bg=COLOR_CARD_DARK,
            fg=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY_PRIMARY, 9)
        )
        age_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
        
        # Action buttons
        actions_frame = tk.Frame(card_frame, bg=COLOR_CARD_DARK)
        actions_frame.pack(fill=tk.X, padx=SPACING_S, pady=SPACING_S)
        
        # Status-specific actions
        if order['status'] == 'Pending':
            start_btn = tk.Button(
                actions_frame,
                text="▶️ Start",
                bg=COLOR_WARNING,
                fg='white',
                font=(FONT_FAMILY_PRIMARY, 9, 'bold'),
                relief='flat',
                command=lambda: self.start_order(order['id'])
            )
            start_btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        elif order['status'] == 'Preparing':
            ready_btn = tk.Button(
                actions_frame,
                text="✅ Ready",
                bg=COLOR_SUCCESS,
                fg='white',
                font=(FONT_FAMILY_PRIMARY, 9, 'bold'),
                relief='flat',
                command=lambda: self.mark_ready(order['id'])
            )
            ready_btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        elif order['status'] == 'Ready':
            complete_btn = tk.Button(
                actions_frame,
                text="✔️ Complete",
                bg=COLOR_PRIMARY,
                fg='white',
                font=(FONT_FAMILY_PRIMARY, 9, 'bold'),
                relief='flat',
                command=lambda: self.complete_order(order['id'])
            )
            complete_btn.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        # Print button (always available)
        print_btn = tk.Button(
            actions_frame,
            text="🖨️ Print",
            bg=COLOR_SECONDARY_DARK,
            fg='white',
            font=(FONT_FAMILY_PRIMARY, 9, 'bold'),
            relief='flat',
            command=lambda: self.print_kot(order)
        )
        print_btn.pack(side=tk.RIGHT)
        
        # Store order data for later use
        card_frame.order_data = order
    
    def update_order_counts(self):
        """Update order count labels in column headers"""
        for column_frame in [self.new_orders_frame, self.progress_orders_frame, self.ready_orders_frame]:
            count = len(column_frame.scrollable_frame.winfo_children())
            column_frame.count_label.config(text=str(count))
    
    def format_time(self, time_string):
        """Format time for display"""
        time_obj = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
        return time_obj.strftime('%H:%M:%S')
    
    def _get_urgency_level(self, order_age):
        """Determine urgency level based on order age"""
        if order_age > timedelta(minutes=30):
            return "High", COLOR_ERROR
        elif order_age > timedelta(minutes=15):
            return "Medium", COLOR_WARNING
        else:
            return "Normal", COLOR_SUCCESS
    
    def set_filter(self, filter_value):
        """Set current filter and refresh"""
        self.current_filter.set(filter_value)
        self.update_filter_button_styles()
        self.refresh_orders()
    
    def update_filter_button_styles(self):
        """Update filter button styles based on selection"""
        current_filter = self.current_filter.get()
        
        filters = ['all', 'new', 'progress', 'ready', 'completed']
        for filter_value in filters:
            btn = getattr(self, f'filter_btn_{filter_value}', None)
            if btn:
                if filter_value == current_filter:
                    btn.configure(style='FilterActive.TButton')
                else:
                    btn.configure(style='Filter.TButton')
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh"""
        self.auto_refresh.set(not self.auto_refresh.get())
        
        if self.auto_refresh.get():
            self.start_auto_refresh()
            self.show_info_message("Auto-refresh enabled")
        else:
            self.stop_auto_refresh()
            self.show_info_message("Auto-refresh disabled")
    
    def start_auto_refresh(self):
        """Start auto-refresh timer"""
        if self.refresh_interval:
            self.kot_window.after_cancel(self.refresh_interval)
        
        self.refresh_interval = self.kot_window.after(10000, self.auto_refresh_callback)
    
    def stop_auto_refresh(self):
        """Stop auto-refresh timer"""
        if self.refresh_interval:
            self.kot_window.after_cancel(self.refresh_interval)
            self.refresh_interval = None
    
    def auto_refresh_callback(self):
        """Auto-refresh callback"""
        if self.auto_refresh.get():
            self.refresh_orders()
            self.start_auto_refresh()  # Schedule next refresh
    
    def toggle_sound(self):
        """Toggle sound notifications"""
        new_state = not self.sound_enabled.get()
        self.sound_enabled.set(new_state)
        sound_manager.set_enabled(new_state)
        
        if new_state:
            self.show_info_message("Sound enabled")
        else:
            self.show_info_message("Sound disabled")
    
    def toggle_bulk_actions(self):
        """Toggle bulk actions panel"""
        if self.bulk_actions_visible:
            self.hide_bulk_actions()
        else:
            self.show_bulk_actions()
    
    def show_bulk_actions(self):
        """Show bulk actions panel"""
        if not self.bulk_actions_visible:
            self.bulk_actions_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
            self.bulk_actions_visible = True
    
    def hide_bulk_actions(self):
        """Hide bulk actions panel"""
        if self.bulk_actions_visible:
            self.bulk_actions_frame.pack_forget()
            self.bulk_actions_visible = False
    
    def toggle_select_all(self):
        """Toggle selection of all visible orders"""
        select_all = self.select_all_var.get()
        
        # This would need implementation of order selection logic
        # For now, just show a message
        if select_all:
            self.show_info_message("All orders selected")
        else:
            self.show_info_message("All orders deselected")
    
    def check_for_new_orders(self, current_new_count):
        """Check for new orders and play sound"""
        if current_new_count > self.last_order_count and self.sound_enabled.get():
            # Check if any orders are urgent (older than 15 minutes)
            urgent_orders = [order for order in self.new_orders_frame.scrollable_frame.winfo_children()
                           if hasattr(order, 'order_data') and order.order_data.get('urgency_level') == 'High']
            
            if urgent_orders:
                sound_manager.play_notification_sound('urgent')
                self.show_info_message(f"{current_new_count - self.last_order_count} URGENT order(s) received!")
            else:
                sound_manager.play_notification_sound('new_order')
                self.show_info_message(f"{current_new_count - self.last_order_count} new order(s) received!")
    
    def play_notification_sound(self):
        """Play notification sound"""
        try:
            if platform.system() == 'Windows':
                # Play Windows default notification sound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            else:
                # For other systems, you could use a different method
                print("Notification sound played")
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    def start_order(self, item_id):
        """Start preparing an order"""
        try:
            self.app.kot_model.update_status(item_id, "Preparing")
            self.show_success_message("Order started")
            self.refresh_orders()
        except Exception as e:
            self.show_error_message(f"Failed to start order: {e}")
    
    def mark_ready(self, item_id):
        """Mark order as ready"""
        try:
            self.app.kot_model.update_status(item_id, "Ready")
            self.show_success_message("Order marked as ready")
            self.refresh_orders()
        except Exception as e:
            self.show_error_message(f"Failed to mark order as ready: {e}")
    
    def complete_order(self, item_id):
        """Complete an order"""
        try:
            self.app.kot_model.update_status(item_id, "Completed")
            self.show_success_message("Order completed")
            self.refresh_orders()
        except Exception as e:
            self.show_error_message(f"Failed to complete order: {e}")
    
    def print_kot(self, order):
        """Print KOT for an order"""
        try:
            # Prepare KOT data
            kot_data = {
                'order_number': order['order_number'],
                'time': order['created_at'],
                'item_name': order['name'],
                'quantity': order['quantity'],
                'notes': ''
            }
            
            # Get default printer settings
            printer_type = self.app.settings.get('default_kot_printer_type', PRINTER_TYPE_THERMAL)
            printer_name = self.app.settings.get('thermal_printer_name' if printer_type == PRINTER_TYPE_THERMAL else 'standard_printer_name', '')
            
            # Print KOT
            success = self.printer_manager.print_kot(kot_data, printer_type, printer_name)
            
            if success:
                self.show_success_message("KOT printed successfully!")
            else:
                self.show_error_message("Failed to print KOT")
                
        except Exception as e:
            self.show_error_message(f"Print error: {e}")
    
    def print_all_pending(self):
        """Print all pending orders"""
        try:
            # Get all pending orders
            pending_orders = self.app.kot_model.get_items("Pending")
            
            if not pending_orders:
                self.show_info_message("No pending orders to print")
                return
            
            printed_count = 0
            for order in pending_orders:
                item_id, order_number, name, quantity, created_at, status = order
                
                kot_data = {
                    'order_number': order_number,
                    'time': created_at,
                    'item_name': name,
                    'quantity': quantity,
                    'notes': ''
                }
                
                printer_type = self.app.settings.get('default_kot_printer_type', PRINTER_TYPE_THERMAL)
                printer_name = self.app.settings.get('thermal_printer_name' if printer_type == PRINTER_TYPE_THERMAL else 'standard_printer_name', '')
                
                if self.printer_manager.print_kot(kot_data, printer_type, printer_name):
                    printed_count += 1
                
                # Small delay between prints
                time.sleep(0.5)
            
            self.show_success_message(f"Printed {printed_count} KOTs")
            
        except Exception as e:
            self.show_error_message(f"Error printing all KOTs: {e}")
    
    def bulk_update_status(self, status):
        """Update status for multiple orders"""
        # This would need implementation of bulk selection logic
        # For now, just show a message
        self.show_info_message(f"Bulk update to {status} - selection not implemented yet")
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.kot_window.bind('<Control-r>', lambda e: self.refresh_orders())
        self.kot_window.bind('<Control-s>', lambda e: self.toggle_sound())
        self.kot_window.bind('<Control-a>', lambda e: self.toggle_auto_refresh())
        self.kot_window.bind('<Control-b>', lambda e: self.toggle_bulk_actions())
        self.kot_window.bind('<Control-p>', lambda e: self.print_all_pending())
        self.kot_window.bind('<Escape>', lambda e: self.hide_bulk_actions())
        
        # Number keys for filters
        self.kot_window.bind('<Key-1>', lambda e: self.set_filter('all'))
        self.kot_window.bind('<Key-2>', lambda e: self.set_filter('new'))
        self.kot_window.bind('<Key-3>', lambda e: self.set_filter('progress'))
        self.kot_window.bind('<Key-4>', lambda e: self.set_filter('ready'))
        self.kot_window.bind('<Key-5>', lambda e: self.set_filter('completed'))
    
    def show_success_message(self, message):
        """Show success message"""
        messagebox.showinfo("Success", message)
    
    def show_info_message(self, message):
        """Show info message"""
        messagebox.showinfo("Info", message)
    
    def show_error_message(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)
    
    def _on_order_created(self, data):
        """Handle order creation events for real-time updates"""
        if data and 'order_number' in data:
            # Auto-refresh KOT window when new order is created
            if self.auto_refresh.get():
                self.refresh_orders()
    
    def _on_kot_status_changed(self, data):
        """Handle KOT status change events for real-time updates"""
        if data and 'item_id' in data:
            # Auto-refresh KOT window when status changes
            if self.auto_refresh.get():
                self.refresh_orders()
    
    def on_closing(self):
        """Handle window closing"""
        # Stop auto-refresh
        self.stop_auto_refresh()
        
        # Unsubscribe from events
        event_dispatcher.unsubscribe(EventType.ORDER_CREATED, self._on_order_created)
        event_dispatcher.unsubscribe(EventType.KOT_STATUS_CHANGED, self._on_kot_status_changed)
        
        # Destroy window
        self.kot_window.destroy()
    
    def show(self):
        """Show the KOT window"""
        self.kot_window.deiconify()
        self.kot_window.lift()
        self.kot_window.focus_force()