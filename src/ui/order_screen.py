import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from controllers.order_controller import OrderController
from utils.constants import *

class OrderScreen(BaseUI):
    """Order screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.order_controller = OrderController(self.db)
        self.menu_tree = None
        self.cart_tree = None
    
    def setup_ui(self):
        """Setup the modern order screen UI"""
        # Reset the order controller to ensure clean state
        self.order_controller.reset_order()
        
        # Configure modern styles
        self.configure_styles()
        
        # Set main background - use style configuration for ttk.Frame
        try:
            self.app.content_frame.configure(background=COLOR_BACKGROUND_LIGHT)
        except tk.TclError:
            # If it's a ttk.Frame, use style configuration
            style = ttk.Style()
            style.configure("OrderScreen.TFrame", background=COLOR_BACKGROUND_LIGHT)
            self.app.content_frame.configure(style="OrderScreen.TFrame")
        
        # Title with modern styling
        title_frame = self.create_modern_frame(self.app.content_frame, padding=(SPACING_L, SPACING_M, SPACING_L, SPACING_S))
        title_frame.pack(fill=tk.X)
        
        title_label = self.create_modern_label(title_frame, "New Order", style="Title.TLabel")
        title_label.pack()
        
        # Create main order container with modern styling
        order_container = self.create_modern_frame(self.app.content_frame, padding=SPACING_L)
        order_container.pack(fill=tk.BOTH, expand=True)
        
        # Create two-panel layout with proper spacing
        panels_frame = ttk.Frame(order_container)
        panels_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Order details and menu
        left_panel = self.create_modern_frame(panels_frame, padding=SPACING_M)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING_S))
        
        # Right panel - Cart and payment
        right_panel = self.create_modern_frame(panels_frame, padding=SPACING_M)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(SPACING_S, 0))
        
        # === LEFT PANEL CONTENT ===
        
        # Order Type Section
        order_type_frame = self.create_modern_frame(left_panel, padding=SPACING_M)
        order_type_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        order_type_title = self.create_modern_label(order_type_frame, "Order Type", style="CardTitle.TLabel")
        order_type_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.order_type_var = tk.StringVar(value="Dine-in")
        order_type_buttons_frame = ttk.Frame(order_type_frame)
        order_type_buttons_frame.pack(fill=tk.X)
        
        dine_in_radio = ttk.Radiobutton(order_type_buttons_frame, text="Dine-in",
                                       variable=self.order_type_var, value="Dine-in",
                                       command=self.change_order_type)
        dine_in_radio.pack(side=tk.LEFT, padx=(0, SPACING_L))
        
        takeaway_radio = ttk.Radiobutton(order_type_buttons_frame, text="Takeaway",
                                        variable=self.order_type_var, value="Takeaway",
                                        command=self.change_order_type)
        takeaway_radio.pack(side=tk.LEFT)
        
        # Table Selection Section (for dine-in)
        self.table_frame = self.create_modern_frame(left_panel, padding=SPACING_M)
        self.table_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        table_title = self.create_modern_label(self.table_frame, "Table Selection", style="CardTitle.TLabel")
        table_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.table_var = tk.StringVar()
        self.table_combo = self.create_modern_combobox(self.table_frame, self.table_var, [], state="readonly")
        self.table_combo.pack(fill=tk.X)
        self.table_combo.bind("<<ComboboxSelected>>", self.select_table)
        
        # Customer Details Section (for takeaway)
        self.customer_frame = self.create_modern_frame(left_panel, padding=SPACING_M)
        
        customer_title = self.create_modern_label(self.customer_frame, "Customer Details", style="CardTitle.TLabel")
        customer_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Customer name field
        self.customer_name_entry = self.create_form_field(
            self.customer_frame, "Name:", "entry"
        )
        
        # Customer mobile field
        self.customer_mobile_entry = self.create_form_field(
            self.customer_frame, "Mobile:", "entry"
        )
        
        # Initially hide customer frame
        self.customer_frame.pack_forget()
        
        # Menu Items Section
        menu_frame = self.create_modern_frame(left_panel, padding=SPACING_M)
        menu_frame.pack(fill=tk.BOTH, expand=True)
        
        menu_title = self.create_modern_label(menu_frame, "Menu Items", style="CardTitle.TLabel")
        menu_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Search and Filter Section
        search_filter_frame = ttk.Frame(menu_frame)
        search_filter_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Search field
        search_label = self.create_modern_label(search_filter_frame, "Search:", style="Body.TLabel")
        search_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        self.search_entry = self.create_modern_entry(search_filter_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, SPACING_M))
        self.search_entry.bind("<KeyRelease>", self.search_menu)
        
        # Category filter
        category_label = self.create_modern_label(search_filter_frame, "Category:", style="Body.TLabel")
        category_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        self.category_var = tk.StringVar()
        self.category_combo = self.create_modern_combobox(search_filter_frame, self.category_var, [], state="readonly", width=15)
        self.category_combo.pack(side=tk.LEFT)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu)
        
        # Menu items treeview with modern styling
        self.menu_tree, menu_scrollbar = self.create_modern_treeview(
            menu_frame,
            ("name", "price", "stock"),
            ("Name", "Price", "Stock"),
            (250, 100, 80)
        )
        self.menu_tree.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        # Add to cart button with modern styling
        add_to_cart_button = self.create_modern_button(
            menu_frame, "Add to Cart", self.add_to_cart, "Primary.TButton"
        )
        add_to_cart_button.pack(fill=tk.X)
        
        # === RIGHT PANEL CONTENT ===
        
        # Cart Section
        cart_frame = self.create_modern_frame(right_panel, padding=SPACING_M)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        cart_title = self.create_modern_label(cart_frame, "Cart", style="CardTitle.TLabel")
        cart_title.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Cart treeview with modern styling
        self.cart_tree, cart_scrollbar = self.create_modern_treeview(
            cart_frame,
            ("name", "price", "quantity", "total"),
            ("Item", "Price", "Quantity", "Total"),
            (200, 80, 80, 80)
        )
        self.cart_tree.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        # Cart action buttons
        cart_buttons = [
            ("Update Quantity", self.update_cart_quantity, "Secondary.TButton"),
            ("Remove Item", self.remove_from_cart, "Danger.TButton"),
            ("Clear Cart", self.clear_cart, "Danger.TButton")
        ]
        self.create_button_group(cart_frame, cart_buttons)
        
        # Order Summary Section
        summary_frame = self.create_modern_frame(right_panel, padding=SPACING_M)
        summary_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        summary_title = self.create_modern_label(summary_frame, "Order Summary", style="CardTitle.TLabel")
        summary_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Summary labels with modern styling
        self.subtotal_label = self.create_modern_label(summary_frame, "Subtotal: ₹0.00", style="Body.TLabel")
        self.subtotal_label.pack(anchor=tk.W, pady=SPACING_XS)
        
        self.tax_label = self.create_modern_label(summary_frame, f"Tax (5%): ₹0.00", style="Body.TLabel")
        self.tax_label.pack(anchor=tk.W, pady=SPACING_XS)
        
        # Discount section
        discount_frame = ttk.Frame(summary_frame)
        discount_frame.pack(fill=tk.X, pady=SPACING_XS)
        
        discount_label = self.create_modern_label(discount_frame, "Discount:", style="Body.TLabel")
        discount_label.pack(side=tk.LEFT)
        
        self.discount_var = tk.StringVar(value="0")
        self.discount_entry = self.create_modern_entry(discount_frame, textvariable=self.discount_var, width=8)
        self.discount_entry.pack(side=tk.LEFT, padx=SPACING_S)
        
        self.discount_type_var = tk.StringVar(value="%")
        percent_radio = ttk.Radiobutton(discount_frame, text="%", variable=self.discount_type_var, value="%")
        percent_radio.pack(side=tk.LEFT, padx=(SPACING_S, 0))
        
        flat_radio = ttk.Radiobutton(discount_frame, text="Flat", variable=self.discount_type_var, value="Flat")
        flat_radio.pack(side=tk.LEFT, padx=(SPACING_S, 0))
        
        self.discount_entry.bind("<KeyRelease>", self.calculate_totals)
        self.discount_type_var.trace("w", lambda *args: self.calculate_totals())
        
        # Total with emphasis
        self.total_label = self.create_modern_label(summary_frame, "Total: ₹0.00", style="CardTitle.TLabel")
        self.total_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        
        # Payment Section
        payment_frame = self.create_modern_frame(right_panel, padding=SPACING_M)
        payment_frame.pack(fill=tk.X)
        
        payment_title = self.create_modern_label(payment_frame, "Payment", style="CardTitle.TLabel")
        payment_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Payment buttons with modern styling
        payment_buttons = [
            ("Cash Payment", self.process_cash_payment, "Success.TButton"),
            ("Card Payment", self.process_card_payment, "Primary.TButton"),
            ("UPI Payment", self.process_upi_payment, "Primary.TButton")
        ]
        
        # Create payment buttons in a vertical layout
        for text, command, style in payment_buttons:
            button = self.create_modern_button(payment_frame, text, command, style)
            button.pack(fill=tk.X, pady=SPACING_XS)
        
        # Load initial data
        self.load_tables()
        self.load_categories()
        
        # Ensure menu tree is properly initialized before loading items
        if self.menu_tree:
            self.load_menu_items()
        else:
            # If menu tree is not initialized, wait a bit and try again
            self.root.after(100, self.load_menu_items)
    
    def change_order_type(self):
        """Handle order type change"""
        self.order_controller.set_order_type(self.order_type_var.get())
        
        if self.order_type_var.get() == "Dine-in":
            self.table_frame.pack(fill=tk.X, pady=5)
            self.customer_frame.pack_forget()
        else:  # Takeaway
            self.table_frame.pack_forget()
            self.customer_frame.pack(fill=tk.X, pady=5)
    
    def load_tables(self):
        """Load available tables"""
        tables = self.order_controller.get_available_tables()
        table_list = [f"{table[1]} (ID: {table[0]})" for table in tables]
        self.table_combo['values'] = table_list
        
        if table_list:
            self.table_combo.current(0)
            self.select_table()
    
    def select_table(self, event=None):
        """Handle table selection"""
        selection = self.table_var.get()
        if selection:
            # Extract table ID from selection
            table_id = selection.split("(ID: ")[1].rstrip(")")
            self.order_controller.set_table(int(table_id))
    
    def load_categories(self):
        """Load menu categories"""
        categories = self.order_controller.get_categories()
        category_list = ["All"] + [category[1] for category in categories]
        self.category_combo['values'] = category_list
        self.category_combo.current(0)
    
    def load_menu_items(self, search_term="", category="All"):
        """Load menu items with modern styling"""
        # Check if menu tree exists
        if not self.menu_tree:
            return
            
        items = self.order_controller.get_menu_items(search_term, category)
        
        # Clear tree
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)
        
        # Add items to tree with modern styling
        for item in items:
            item_id, name, category, price, stock = item
            
            # Determine stock status for styling
            stock_int = int(stock) if isinstance(stock, str) and stock.isdigit() else (stock if isinstance(stock, int) else 0)
            tag = "low_stock" if stock_int < LOW_STOCK_THRESHOLD else "normal_stock"
            
            self.menu_tree.insert("", tk.END, values=(name, f"₹{price:.2f}", stock),
                                 tags=(item_id, tag))
            
        # Configure tag styling
        self.menu_tree.tag_configure("low_stock", foreground=COLOR_WARNING)
        self.menu_tree.tag_configure("normal_stock", foreground=COLOR_TEXT_PRIMARY)
        
        # Ensure tree is properly selectable
        self.menu_tree.configure(selectmode="extended")
    
    def search_menu(self, event=None):
        """Search menu items"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items(search_term, category)
    
    def filter_menu(self, event=None):
        """Filter menu items by category"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items(search_term, category)
    
    def add_to_cart(self):
        """Add selected menu item to cart"""
        # Check if menu tree exists and has items
        if not self.menu_tree:
            self.show_message("Error", "Menu not loaded. Please try again.", "error")
            return
            
        selection = self.menu_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to add to cart", "warning")
            return
        
        try:
            # Get selected item
            item = self.menu_tree.item(selection[0])
            values = item['values']
            
            # Validate values structure
            if len(values) < 3:
                self.show_message("Error", "Invalid item data structure", "error")
                return
                
            item_name = values[0]
            item_price_str = values[1].replace("₹", "")
            item_stock = values[2]
            
            # Validate and convert price
            try:
                item_price = float(item_price_str)
            except ValueError:
                self.show_message("Error", f"Invalid price format: {item_price_str}", "error")
                return
            
            # Validate and convert stock
            try:
                item_stock = int(item_stock)
            except ValueError:
                self.show_message("Error", f"Invalid stock format: {item_stock}", "error")
                return
            
            # Get item ID from tags
            tags = item.get('tags', [])
            if not tags:
                self.show_message("Error", "Item ID not found", "error")
                return
                
            item_id = int(tags[0])
            
            # Ask for quantity
            quantity = self.show_input_dialog("Quantity", f"Enter quantity for {item_name}:", minvalue=1, maxvalue=item_stock)
            if not quantity:
                return
            
            # Add to cart using controller
            success, message = self.order_controller.add_to_cart(item_id, quantity)
            
            if success:
                self.update_cart_display()
                # Clear selection after successful addition
                self.menu_tree.selection_remove(selection[0])
            else:
                self.show_message("Warning", message, "warning")
                
        except Exception as e:
            self.show_message("Error", f"Failed to add item to cart: {str(e)}", "error")
    
    def update_cart_display(self):
        """Update the cart display with modern styling"""
        # Clear cart tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add items to cart tree with modern styling
        for cart_item in self.order_controller.cart_items:
            self.cart_tree.insert("", tk.END, values=(
                cart_item['name'],
                f"₹{cart_item['price']:.2f}",
                cart_item['quantity'],
                f"₹{cart_item['total']:.2f}"
            ), tags=(cart_item['id'], 'cart_item'))
        
        # Configure cart item styling
        self.cart_tree.tag_configure("cart_item", foreground=COLOR_TEXT_PRIMARY)
        
        # Calculate totals
        self.calculate_totals()
    
    def calculate_totals(self, *args):
        """Calculate order totals"""
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
        except ValueError:
            discount_value = 0
            discount_type = self.discount_type_var.get()  # Add this line
        
        totals = self.order_controller.calculate_totals(discount_value, discount_type)
        
        # Update labels
        self.subtotal_label.config(text=f"Subtotal: ₹{totals['subtotal']:.2f}")
        self.tax_label.config(text=f"Tax (5%): ₹{totals['tax']:.2f}")
        self.total_label.config(text=f"Total: ₹{totals['total']:.2f}")
    
    def update_cart_quantity(self):
        """Update quantity of selected cart item"""
        selection = self.cart_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to update", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.cart_tree.item(selection[0])['tags'][0])
        
        # Get current quantity
        for cart_item in self.order_controller.cart_items:
            if cart_item['id'] == item_id:
                current_quantity = cart_item['quantity']
                break
        
        # Ask for new quantity
        new_quantity = self.show_input_dialog("Update Quantity", 
                                           f"Enter new quantity (Current: {current_quantity}):", 
                                           minvalue=1, maxvalue=100)
        if new_quantity:
            success, message = self.order_controller.update_cart_quantity(item_id, new_quantity)
            
            if success:
                self.update_cart_display()
            else:
                self.show_message("Warning", message, "warning")
    
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selection = self.cart_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to remove", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.cart_tree.item(selection[0])['tags'][0])
        
        # Remove item from cart
        self.order_controller.remove_from_cart(item_id)
        self.update_cart_display()
    
    def clear_cart(self):
        """Clear all items from cart"""
        if not self.order_controller.cart_items:
            return
        
        if self.show_message("Confirm", "Are you sure you want to clear the cart?", "yesno"):
            self.order_controller.clear_cart()
            self.update_cart_display()
    
    def process_payment(self, payment_mode):
        """Process payment for the order"""
        if not self.order_controller.cart_items:
            self.show_message("Warning", "Cart is empty. Please add items to the cart.", "warning")
            return
        
        if self.order_controller.order_type == "Dine-in" and not self.order_controller.selected_table:
            self.show_message("Warning", "Please select a table.", "warning")
            return
        
        # Get discount values
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
        except ValueError:
            discount_value = 0
            discount_type = "%"
        
        # Get customer details for takeaway
        customer_name = None
        customer_mobile = None
        if self.order_controller.order_type == "Takeaway":
            customer_name = self.customer_name_entry.get()
            customer_mobile = self.customer_mobile_entry.get()
        
        # Process payment using controller
        success, result = self.order_controller.process_payment(
            payment_mode, discount_value, discount_type, customer_name, customer_mobile
        )
        
        if success:
            self.show_message("Success", f"Order {result} completed successfully!", "info")
            # Reset order
            self.order_controller.reset_order()
            self.setup_ui()  # Reset UI
        else:
            self.show_message("Error", result, "error")
    
    def process_cash_payment(self):
        """Process cash payment"""
        self.process_payment("Cash")
    
    def process_card_payment(self):
        """Process card payment with modern dialog"""
        # Ask for card details
        card_details = self.show_input_dialog("Card Payment", "Enter last 4 digits of card:")
        if card_details:
            self.show_message("Payment Successful", f"Card payment processed successfully!\nCard ending in: {card_details}", "info")
            self.process_payment("Card")
    
    def process_upi_payment(self):
        """Process UPI payment with modern dialog"""
        # Ask for UPI ID
        upi_id = self.show_input_dialog("UPI Payment", "Enter UPI ID:")
        if upi_id:
            self.show_message("Payment Successful", f"UPI payment processed successfully!\nUPI ID: {upi_id}", "info")
            self.process_payment("UPI")
    
    def cleanup(self):
        """Clean up resources when the screen is being destroyed"""
        # Reset the order controller state
        self.order_controller.reset_order()
        
        # Clear any references to widgets
        self.menu_tree = None
        self.cart_tree = None
        
        # Clear any other resources
        self.search_entry = None
        self.category_combo = None
        self.table_combo = None
        self.customer_name_entry = None
        self.customer_mobile_entry = None
        self.discount_entry = None
