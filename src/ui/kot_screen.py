import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime, timedelta
from .base_ui import BaseUI
from src.utils.helpers import generate_kot_content
from src.utils.printer import PrinterManager
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType

class KOTScreen(BaseUI):
    """Kitchen Order Ticket screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.printer_manager = PrinterManager(app.settings)
        
        # Subscribe to events for real-time updates
        event_dispatcher.subscribe(EventType.ORDER_CREATED, self._on_order_created)
        event_dispatcher.subscribe(EventType.KOT_STATUS_CHANGED, self._on_kot_status_changed)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup KOT management UI with modern design"""
        # Configure styles for this screen
        self.configure_styles()
        
        # Main container with background
        main_container = tk.Frame(self.app.content_frame, bg=COLOR_BACKGROUND_LIGHT)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title section with enhanced styling
        title_frame = self.create_modern_frame(main_container, style="Card.TFrame", 
                                               padding=(SPACING_L, SPACING_M, SPACING_L, SPACING_L))
        title_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        title_label = self.create_modern_label(title_frame, text="Kitchen Order Tickets (KOT)",
                                              style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = self.create_modern_label(title_frame,
                                                text="Manage and track kitchen orders efficiently",
                                                style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
        
        # Filter section with modern styling
        filter_container = self.create_modern_frame(main_container, style="Card.TFrame", 
                                                   padding=SPACING_L)
        filter_container.pack(fill=tk.X, pady=(0, SPACING_M))
        
        filter_title = self.create_modern_label(filter_container, text="Filter Orders",
                                              style="SectionTitle.TLabel")
        filter_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Modern filter buttons container with improved layout
        filter_buttons_frame = ttk.Frame(filter_container, style="Card.TFrame")
        filter_buttons_frame.pack(fill=tk.X, pady=(0, SPACING_S))
        
        self.kot_filter_var = tk.StringVar(value="Pending")
        
        # Create modern filter buttons with enhanced styling
        self.filter_buttons = {}
        filter_options = [
            ("Pending", COLOR_WARNING, COLOR_WARNING_LIGHT),
            ("Preparing", COLOR_PRIMARY, COLOR_BACKGROUND_LIGHT),
            ("Completed", COLOR_SUCCESS, COLOR_SUCCESS_LIGHT)
        ]
        
        for i, (text, color, bg_color) in enumerate(filter_options):
            # Create modern filter button frame
            button_frame = tk.Frame(filter_buttons_frame, bg=bg_color,
                                   highlightbackground=color, highlightthickness=2,
                                   relief='solid', bd=0)
            button_frame.pack(side=tk.LEFT, padx=(0 if i == 0 else SPACING_S, 0), 
                             fill=tk.BOTH, expand=True)
            
            # Modern filter button with hover effects
            button = tk.Radiobutton(button_frame, text=text, variable=self.kot_filter_var,
                                   value=text, command=self.load_kot,
                                   bg=bg_color, fg=color,
                                   font=(FONT_FAMILY_PRIMARY, 11, 'bold'),
                                   activebackground=color, activeforeground=COLOR_CARD_WHITE,
                                   relief='flat', bd=0, pady=SPACING_S, cursor='hand2',
                                   selectcolor=COLOR_CARD_WHITE, indicatoron=False,
                                   borderwidth=2, highlightbackground=color, highlightthickness=1)
            button.pack(fill=tk.BOTH, expand=True, padx=SPACING_S, pady=SPACING_S)
            
            # Bind hover effects
            button.bind("<Enter>", lambda e, b=button, c=color, bg=bg_color: 
                        self._on_filter_hover(e, b, c, bg, True))
            button.bind("<Leave>", lambda e, b=button, c=color, bg=bg_color: 
                        self._on_filter_hover(e, b, c, bg, False))
            
            self.filter_buttons[text] = (button_frame, button)
        
        # KOT display section with modern card-based design
        kot_container = self.create_modern_frame(main_container, style="Card.TFrame", 
                                                 padding=SPACING_L)
        kot_container.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        # KOT list title with enhanced styling
        kot_title_frame = ttk.Frame(kot_container, style="Card.TFrame")
        kot_title_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        kot_title = self.create_modern_label(kot_title_frame, text="Order Tickets",
                                           style="SectionTitle.TLabel")
        kot_title.pack(side=tk.LEFT)
        
        # Add order count label
        self.order_count_label = self.create_modern_label(kot_title_frame, text="",
                                                         style="Small.TLabel")
        self.order_count_label.pack(side=tk.RIGHT)
        
        # Create enhanced scrollable frame for KOT cards with modern styling
        canvas_frame = ttk.Frame(kot_container, style="Card.TFrame")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.kot_canvas = tk.Canvas(canvas_frame, bg=COLOR_CARD_WHITE, 
                                   highlightthickness=0, highlightbackground=COLOR_BORDER_LIGHT)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.kot_canvas.yview)
        self.kot_scrollable_frame = ttk.Frame(self.kot_canvas, style="Card.TFrame")
        
        self.kot_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.kot_canvas.configure(scrollregion=self.kot_canvas.bbox("all"))
        )
        
        self.kot_canvas.create_window((0, 0), window=self.kot_scrollable_frame, anchor="nw")
        self.kot_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.kot_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons section with enhanced styling
        actions_container = self.create_modern_frame(main_container, style="Card.TFrame", 
                                                     padding=SPACING_L)
        actions_container.pack(fill=tk.X)
        
        # Create modern action buttons with improved spacing
        self.create_button_group(actions_container, [
            ("Start Preparing", self.mark_kot_preparing, "Primary.TButton"),
            ("Mark Completed", self.mark_kot_completed, "Success.TButton"),
            ("Print KOT", self.print_kot, "Secondary.TButton"),
            ("Refresh", self.load_kot, "Secondary.TButton")
        ], spacing=SPACING_M)
        
        # Load KOT items
        self.load_kot()

    def load_kot(self):
        """Load KOT items with modern card-based display"""
        status_filter = self.kot_filter_var.get()
        
        try:
            items = self.app.kot_model.get_items(status_filter)
            
            # Clear existing KOT cards
            for widget in self.kot_scrollable_frame.winfo_children():
                widget.destroy()
            
            # Update filter button styling
            self._update_filter_button_styles()
            
            # Update order count
            self.order_count_label.config(text=f"Total: {len(items)} orders")
            
            if not items:
                # Show enhanced empty state message
                empty_frame = self.create_modern_frame(self.kot_scrollable_frame, style="Card.TFrame",
                                                     padding=SPACING_XL)
                empty_frame.pack(fill=tk.X, pady=SPACING_L)
                
                empty_icon = self.create_modern_label(empty_frame, text="📋",
                                                    style="Title.TLabel")
                empty_icon.pack(pady=(0, SPACING_M))
                
                empty_label = self.create_modern_label(empty_frame,
                                                    text=f"No {status_filter.lower()} orders found",
                                                    style="Subtitle.TLabel")
                empty_label.pack()
                
                empty_sublabel = self.create_modern_label(empty_frame,
                                                        text="Orders will appear here when they are created",
                                                        style="Small.TLabel")
                empty_sublabel.pack(pady=(SPACING_S, 0))
                return
            
            # Create KOT cards for each item
            for item in items:
                self._create_kot_card(item)
                
        except Exception as e:
            print(f"Error loading KOT items: {e}")
            # Show error message
            error_frame = self.create_modern_frame(self.kot_scrollable_frame, style="Card.TFrame",
                                            padding=SPACING_XL)
            error_frame.pack(fill=tk.X, pady=SPACING_L)
            
            error_icon = self.create_modern_label(error_frame, text="⚠",
                                            style="Title.TLabel")
            error_icon.pack(pady=(0, SPACING_M))
            
            error_label = self.create_modern_label(error_frame,
                                            text="Failed to load orders",
                                            style="Subtitle.TLabel")
            error_label.pack()
            
            error_sublabel = self.create_modern_label(error_frame,
                                              text="Please try refreshing the screen",
                                              style="Small.TLabel")
            error_sublabel.pack(pady=(SPACING_S, 0))
    
    def _create_kot_card(self, item):
        """Create a modern card for a KOT item with enhanced styling"""
        item_id, order_number, name, quantity, created_at, status = item
        
        # Calculate order age for urgency indicator
        time_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
        current_time = datetime.now()
        order_age = current_time - time_obj
        formatted_time = time_obj.strftime('%H:%M:%S')
        
        # Determine urgency level and color
        urgency_level, urgency_color = self._get_urgency_level(order_age)
        
        # Main card container with enhanced shadow effect
        card_container = tk.Frame(self.kot_scrollable_frame, bg=COLOR_CARD_WHITE,
                                relief='solid', bd=1, highlightbackground=COLOR_BORDER_LIGHT,
                                highlightthickness=1)
        card_container.pack(fill=tk.X, pady=SPACING_S, padx=SPACING_S)
        
        # Enhanced shadow effect
        shadow_frame = tk.Frame(card_container, bg=COLOR_SHADOW, height=3)
        shadow_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Card content frame with improved padding
        card_content = self.create_modern_frame(card_container, style="Card.TFrame",
                                               padding=(SPACING_M, SPACING_M, SPACING_M, SPACING_S))
        card_content.pack(fill=tk.X)
        
        # Header row with order number and status
        header_frame = ttk.Frame(card_content, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, SPACING_S))
        
        # Order number with enhanced styling
        order_frame = ttk.Frame(header_frame, style="Card.TFrame")
        order_frame.pack(side=tk.LEFT)
        
        order_label = self.create_modern_label(order_frame, text=f"Order #{order_number}",
                                              style="CardTitle.TLabel")
        order_label.pack(side=tk.LEFT)
        
        # Enhanced urgency indicator with icon
        if urgency_level != "Normal":
            urgency_frame = tk.Frame(order_frame, bg=urgency_color,
                                   highlightbackground=urgency_color,
                                   highlightthickness=1, relief='solid', bd=0)
            urgency_frame.pack(side=tk.LEFT, padx=(SPACING_S, 0))
            
            urgency_icon = "⚠" if urgency_level == "High" else "⏰"
            urgency_label = tk.Label(urgency_frame, text=f"{urgency_icon} {urgency_level}",
                                    bg=urgency_color, fg=COLOR_CARD_WHITE,
                                    font=(FONT_FAMILY_PRIMARY, 9, 'bold'),
                                    padx=SPACING_S, pady=2)
            urgency_label.pack()
        
        # Enhanced status badge with icon
        status_frame = ttk.Frame(header_frame, style="Card.TFrame")
        status_frame.pack(side=tk.RIGHT)
        
        status_color = self._get_status_color(status)
        status_badge = tk.Frame(status_frame, bg=status_color,
                              highlightbackground=status_color,
                              highlightthickness=1, relief='solid', bd=0)
        status_badge.pack()
        
        status_icon = "⏳" if status == "Pending" else "👨‍🍳" if status == "Preparing" else "✅"
        status_label = tk.Label(status_badge, text=f"{status_icon} {status}",
                              bg=status_color, fg=COLOR_CARD_WHITE,
                              font=(FONT_FAMILY_PRIMARY, 10, 'bold'),
                              padx=SPACING_M, pady=2)
        status_label.pack()
        
        # Enhanced item details with better spacing
        details_frame = ttk.Frame(card_content, style="Card.TFrame")
        details_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Item name with improved styling
        item_label = self.create_modern_label(details_frame, text=name,
                                            style="Body.TLabel")
        item_label.pack(anchor=tk.W)
        
        # Enhanced quantity and time row with icons
        meta_frame = ttk.Frame(card_content, style="Card.TFrame")
        meta_frame.pack(fill=tk.X)
        
        # Quantity with icon
        quantity_label = self.create_modern_label(meta_frame,
                                                text=f"📦 Quantity: {quantity}",
                                                style="Small.TLabel")
        quantity_label.pack(side=tk.LEFT)
        
        # Time with icon
        time_label = self.create_modern_label(meta_frame, text=f"🕐 Time: {formatted_time}",
                                            style="Small.TLabel")
        time_label.pack(side=tk.RIGHT)
        
        # Enhanced order age indicator with color coding
        age_text = self._format_order_age(order_age)
        age_color = COLOR_ERROR if urgency_level == "High" else COLOR_WARNING if urgency_level == "Medium" else COLOR_TEXT_SECONDARY
        age_label = tk.Label(meta_frame, text=f"⏱ Age: {age_text}",
                            bg=COLOR_CARD_WHITE, fg=age_color,
                            font=(FONT_FAMILY_PRIMARY, 10, 'bold'))
        age_label.pack(side=tk.RIGHT, padx=(0, SPACING_M))
        
        # Store item data for later use
        card_content.item_id = item_id
        card_content.status = status
        card_content.card_container = card_container
        
        # Add enhanced click handlers with hover effects
        card_content.bind("<Button-1>", lambda e, card=card_content: self._select_kot_card(card))
        card_content.bind("<Enter>", lambda e, container=card_container: self._on_card_hover(e, container, True))
        card_content.bind("<Leave>", lambda e, container=card_container: self._on_card_hover(e, container, False))
        
        for child in card_content.winfo_children():
            child.bind("<Button-1>", lambda e, card=card_content: self._select_kot_card(card))
            child.bind("<Enter>", lambda e, container=card_container: self._on_card_hover(e, container, True))
            child.bind("<Leave>", lambda e, container=card_container: self._on_card_hover(e, container, False))
    
    def _get_urgency_level(self, order_age):
        """Determine urgency level based on order age"""
        if order_age > timedelta(minutes=30):
            return "High", COLOR_ERROR
        elif order_age > timedelta(minutes=15):
            return "Medium", COLOR_WARNING
        else:
            return "Normal", COLOR_SUCCESS
    
    def _get_status_color(self, status):
        """Get color based on KOT status"""
        if status == "Pending":
            return COLOR_WARNING
        elif status == "Preparing":
            return COLOR_PRIMARY
        elif status == "Completed":
            return COLOR_SUCCESS
        else:
            return COLOR_SECONDARY
    
    def _format_order_age(self, order_age):
        """Format order age for display"""
        total_minutes = int(order_age.total_seconds() / 60)
        if total_minutes < 60:
            return f"{total_minutes} min"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _select_kot_card(self, card):
        """Handle KOT card selection with enhanced visual feedback"""
        try:
            # Deselect all cards
            for widget in self.kot_scrollable_frame.winfo_children():
                if hasattr(widget, 'item_id'):
                    if hasattr(widget, 'card_container'):
                        widget.card_container.configure(highlightbackground=COLOR_BORDER_LIGHT, 
                                                      highlightthickness=1)
                    # Reset card background
                    for child in widget.winfo_children():
                        if hasattr(child, 'configure'):
                            try:
                                # Only attempt to configure background if the widget supports it
                                config_options = child.configure()
                                if 'background' in config_options:
                                    child.configure(background=COLOR_CARD_WHITE)
                            except (tk.TclError, AttributeError):
                                pass
            
            # Select clicked card with enhanced styling
            if hasattr(card, 'card_container'):
                card.card_container.configure(highlightbackground=COLOR_PRIMARY, 
                                            highlightthickness=3)
            self.selected_card = card
        except Exception as e:
            print(f"Error selecting KOT card: {e}")
    
    def _update_filter_button_styles(self):
        """Update filter button styles based on selection with enhanced visual feedback"""
        selected_filter = self.kot_filter_var.get()
        
        filter_options = [
            ("Pending", COLOR_WARNING, COLOR_WARNING_LIGHT),
            ("Preparing", COLOR_PRIMARY, COLOR_BACKGROUND_LIGHT),
            ("Completed", COLOR_SUCCESS, COLOR_SUCCESS_LIGHT)
        ]
        
        for filter_text, (frame, button) in self.filter_buttons.items():
            # Find the matching color scheme
            color = COLOR_PRIMARY
            bg_color = COLOR_BACKGROUND_LIGHT
            for text, c, bg in filter_options:
                if text == filter_text:
                    color = c
                    bg_color = bg
                    break
            
            if filter_text == selected_filter:
                # Highlight selected filter
                frame.configure(highlightbackground=color, highlightthickness=3)
                button.configure(bg=color, fg=COLOR_CARD_WHITE,
                               font=(FONT_FAMILY_PRIMARY, 11, 'bold'),
                               selectcolor=COLOR_CARD_WHITE, highlightbackground=color, highlightthickness=2)
            else:
                # Dim unselected filters
                frame.configure(highlightbackground=COLOR_BORDER_MEDIUM, highlightthickness=1)
                button.configure(bg=bg_color, fg=color,
                               font=(FONT_FAMILY_PRIMARY, 10, 'normal'),
                               selectcolor=COLOR_CARD_WHITE, highlightbackground=color, highlightthickness=1)
    
    def _on_filter_hover(self, event, button, color, bg_color, is_entering):
        """Handle hover effects for filter buttons"""
        if is_entering:
            if button['fg'] != COLOR_CARD_WHITE:  # Not selected
                button.configure(bg=color, fg=COLOR_CARD_WHITE, selectcolor=COLOR_CARD_WHITE,
                              highlightbackground=color, highlightthickness=2)
        else:
            if self.kot_filter_var.get() != button['text'].replace("⚠ ", "").replace("⏰ ", "").replace("✅ ", "").replace("⏳ ", "").replace("👨‍🍳 ", ""):
                button.configure(bg=bg_color, fg=color, selectcolor=COLOR_CARD_WHITE,
                              highlightbackground=color, highlightthickness=1)
    
    def _on_card_hover(self, event, card_container, is_entering):
        """Handle hover effects for KOT cards"""
        if is_entering:
            card_container.configure(highlightbackground=COLOR_PRIMARY_LIGHT, highlightthickness=2)
        else:
            if hasattr(self, 'selected_card') and self.selected_card and hasattr(self.selected_card, 'card_container'):
                if self.selected_card.card_container == card_container:
                    card_container.configure(highlightbackground=COLOR_PRIMARY, highlightthickness=3)
                else:
                    card_container.configure(highlightbackground=COLOR_BORDER_LIGHT, highlightthickness=1)
            else:
                card_container.configure(highlightbackground=COLOR_BORDER_LIGHT, highlightthickness=1)

    def mark_kot_preparing(self):
        """Mark selected KOT item as preparing"""
        if not hasattr(self, 'selected_card') or not self.selected_card:
            self.show_message("Warning", "Please select an order to update", "warning")
            return
        
        # Get item ID from selected card
        item_id = self.selected_card.item_id
        
        # Update status
        self.app.kot_model.update_status(item_id, "Preparing")
        
        self.show_message("Success", "Order marked as 'Preparing'", "info")
        self.load_kot()

    def mark_kot_completed(self):
        """Mark selected KOT item as completed"""
        if not hasattr(self, 'selected_card') or not self.selected_card:
            self.show_message("Warning", "Please select an order to update", "warning")
            return
        
        # Get item ID from selected card
        item_id = self.selected_card.item_id
        
        # Update status
        self.app.kot_model.update_status(item_id, "Completed")
        
        self.show_message("Success", "Order marked as 'Completed'", "info")
        self.load_kot()

    def print_kot(self):
        """Print selected KOT item"""
        if not hasattr(self, 'selected_card') or not self.selected_card:
            self.show_message("Warning", "Please select an order to print", "warning")
            return
        
        # Get item ID from selected card
        item_id = self.selected_card.item_id
        
        # Get item details
        kot_details = self.app.kot_model.get_kot_details(item_id)
        if not kot_details:
            return
        
        order_number, name, quantity, created_at = kot_details
        
        # Check auto-print settings
        auto_print_kot = self.app.settings.get('auto_print_kot', 'True') == 'True'
        
        if auto_print_kot:
            # Auto-print KOT using default settings
            self.print_kot_auto(order_number, name, quantity, created_at)
        else:
            # Show print options dialog
            self.show_print_options(order_number, name, quantity, created_at)
    
    def print_kot_auto(self, order_number, name, quantity, created_at):
        """Auto-print KOT using default settings"""
        try:
            # Prepare KOT data
            kot_data = {
                'order_number': order_number,
                'time': created_at,
                'item_name': name,
                'quantity': quantity,
                'notes': ''
            }
            
            # Get default printer settings
            printer_type = self.app.settings.get('default_kot_printer_type', PRINTER_TYPE_THERMAL)
            printer_name = self.app.settings.get('thermal_printer_name' if printer_type == PRINTER_TYPE_THERMAL else 'standard_printer_name', '')
            
            # Print KOT
            success = self.printer_manager.print_kot(kot_data, printer_type, printer_name)
            
            if not success:
                self.show_message("Warning", "Auto-print failed. Please check printer settings.", "warning")
                
        except Exception as e:
            print(f"Auto-print KOT error: {e}")
    
    def show_print_options(self, order_number, name, quantity, created_at):
        """Show print options dialog"""
        try:
            from .printer_dialog import PrinterSelectionDialog, PrintPreviewDialog
            
            # Show printer selection dialog
            dialog = PrinterSelectionDialog(self.root, self.app.settings, "kot")
            result = dialog.get_result()
            
            if result:
                # Prepare KOT data
                kot_data = {
                    'order_number': order_number,
                    'time': created_at,
                    'item_name': name,
                    'quantity': quantity,
                    'notes': ''
                }
                
                # Show preview if requested
                if result.get('preview', False):
                    content = generate_kot_content(order_number, name, quantity, created_at)
                    preview_dialog = PrintPreviewDialog(self.root, content, "KOT Preview")
                    if not preview_dialog.get_result():
                        return
                
                # Print the KOT
                success = self.printer_manager.print_kot(
                    kot_data,
                    result['printer_type'],
                    result['printer_name']
                )
                
                if success:
                    self.show_message("Success", "KOT printed successfully!", "info")
                else:
                    self.show_message("Error", "Failed to print KOT", "error")
                    
        except Exception as e:
            self.show_message("Error", f"Print error: {str(e)}", "error")
    
    def _on_order_created(self, data):
        """Handle order creation events for real-time updates"""
        if data and 'order_number' in data:
            # Auto-refresh KOT screen when new order is created
            self.load_kot()
    
    def _on_kot_status_changed(self, data):
        """Handle KOT status change events for real-time updates"""
        if data and 'item_id' in data:
            # Auto-refresh KOT screen when status changes
            self.load_kot()
    
    def cleanup(self):
        """Clean up resources when screen is destroyed"""
        # Unsubscribe from events
        event_dispatcher.unsubscribe(EventType.ORDER_CREATED, self._on_order_created)
        event_dispatcher.unsubscribe(EventType.KOT_STATUS_CHANGED, self._on_kot_status_changed)
        
        # Clean up UI components
        if hasattr(self, 'kot_canvas'):
            self.kot_canvas.destroy()
        if hasattr(self, 'selected_card'):
            self.selected_card = None
