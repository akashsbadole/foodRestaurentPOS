import tkinter as tk
from tkinter import ttk
from .base_ui import BaseUI
from controllers.order_controller import OrderController

class OrderScreen(BaseUI):
    """Order screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.order_controller = OrderController(self.db)
        self.menu_tree = None
        self.cart_tree = None
    
    def setup_ui(self):
        """Setup the order screen UI"""
        # Reset the order controller to ensure clean state
        self.order_controller.reset_order()
        
        # Title
        title_label = ttk.Label(self.app.content_frame, text="New Order", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create order frame
        order_frame = ttk.Frame(self.app.content_frame)
        order_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Order details
        left_panel = ttk.Frame(order_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Order type
        order_type_frame = ttk.LabelFrame(left_panel, text="Order Type", padding=10)
        order_type_frame.pack(fill=tk.X, pady=5)
        
        self.order_type_var = tk.StringVar(value="Dine-in")
        ttk.Radiobutton(order_type_frame, text="Dine-in", variable=self.order_type_var, 
                       value="Dine-in", command=self.change_order_type).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(order_type_frame, text="Takeaway", variable=self.order_type_var, 
                       value="Takeaway", command=self.change_order_type).pack(side=tk.LEFT, padx=10)
        
        # Table selection (for dine-in)
        self.table_frame = ttk.LabelFrame(left_panel, text="Table Selection", padding=10)
        self.table_frame.pack(fill=tk.X, pady=5)
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(self.table_frame, textvariable=self.table_var, state="readonly")
        self.table_combo.pack(fill=tk.X, pady=5)
        self.table_combo.bind("<<ComboboxSelected>>", self.select_table)
        
        # Customer details (for takeaway)
        self.customer_frame = ttk.LabelFrame(left_panel, text="Customer Details", padding=10)
        self.customer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.customer_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customer_name_entry = ttk.Entry(self.customer_frame)
        self.customer_name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        ttk.Label(self.customer_frame, text="Mobile:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.customer_mobile_entry = ttk.Entry(self.customer_frame)
        self.customer_mobile_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        self.customer_frame.columnconfigure(1, weight=1)
        
        # Initially hide customer frame
        self.customer_frame.pack_forget()
        
        # Menu items
        menu_frame = ttk.LabelFrame(left_panel, text="Menu Items", padding=10)
        menu_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Search bar
        search_frame = ttk.Frame(menu_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_menu)
        
        # Category filter
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu)
        
        # Menu items treeview
        self.menu_tree, menu_scrollbar = self.create_treeview(
            menu_frame, 
            ("name", "price", "stock"), 
            ("Name", "Price", "Stock"),
            (200, 100, 100)
        )
        self.menu_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add to cart button
        add_to_cart_button = ttk.Button(menu_frame, text="Add to Cart", command=self.add_to_cart)
        add_to_cart_button.pack(pady=5)
        
        # Right panel - Cart
        right_panel = ttk.Frame(order_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Cart items
        cart_frame = ttk.LabelFrame(right_panel, text="Cart", padding=10)
        cart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Cart treeview
        self.cart_tree, cart_scrollbar = self.create_treeview(
            cart_frame,
            ("name", "price", "quantity", "total"),
            ("Item", "Price", "Quantity", "Total"),
            (200, 100, 100, 100)
        )
        self.cart_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Cart buttons
        cart_buttons_frame = ttk.Frame(cart_frame)
        cart_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.create_button_frame(cart_buttons_frame, [
            ("Update Quantity", self.update_cart_quantity),
            ("Remove Item", self.remove_from_cart),
            ("Clear Cart", self.clear_cart)
        ])
        
        # Order summary
        summary_frame = ttk.LabelFrame(right_panel, text="Order Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=5)
        
        # Subtotal
        self.subtotal_label = ttk.Label(summary_frame, text="Subtotal: ₹0.00")
        self.subtotal_label.pack(anchor=tk.W, pady=2)
        
        # Tax
        self.tax_label = ttk.Label(summary_frame, text=f"Tax (5%): ₹0.00")
        self.tax_label.pack(anchor=tk.W, pady=2)
        
        # Discount
        discount_frame = ttk.Frame(summary_frame)
        discount_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(discount_frame, text="Discount:").pack(side=tk.LEFT)
        self.discount_var = tk.StringVar(value="0")
        self.discount_entry = ttk.Entry(discount_frame, textvariable=self.discount_var, width=10)
        self.discount_entry.pack(side=tk.LEFT, padx=5)
        
        self.discount_type_var = tk.StringVar(value="%")
        ttk.Radiobutton(discount_frame, text="%", variable=self.discount_type_var, 
                       value="%").pack(side=tk.LEFT)
        ttk.Radiobutton(discount_frame, text="Flat", variable=self.discount_type_var, 
                       value="Flat").pack(side=tk.LEFT)
        
        self.discount_entry.bind("<KeyRelease>", self.calculate_totals)
        self.discount_type_var.trace("w", lambda *args: self.calculate_totals())
        
        # Total
        self.total_label = ttk.Label(summary_frame, text="Total: ₹0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(anchor=tk.W, pady=2)
        
        # Payment buttons
        payment_frame = ttk.Frame(right_panel)
        payment_frame.pack(fill=tk.X, pady=10)
        
        self.create_button_frame(payment_frame, [
            ("Cash Payment", self.process_cash_payment),
            ("Card Payment", self.process_card_payment),
            ("UPI Payment", self.process_upi_payment)
        ])
        
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
        """Load menu items"""
        # Check if menu tree exists
        if not self.menu_tree:
            return
            
        items = self.order_controller.get_menu_items(search_term, category)
        
        # Clear tree
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, category, price, stock = item
            self.menu_tree.insert("", tk.END, values=(name, f"₹{price:.2f}", stock), tags=(item_id,))
            
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
        """Update the cart display"""
        # Clear cart tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        # Add items to cart tree
        for cart_item in self.order_controller.cart_items:
            self.cart_tree.insert("", tk.END, values=(
                cart_item['name'],
                f"₹{cart_item['price']:.2f}",
                cart_item['quantity'],
                f"₹{cart_item['total']:.2f}"
            ), tags=(cart_item['id'],))
        
        # Calculate totals
        self.calculate_totals()
    
    def calculate_totals(self, *args):
        """Calculate order totals"""
        try:
            discount_value = float(self.discount_var.get())
            discount_type = self.discount_type_var.get()
        except ValueError:
            discount_value = 0
        
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
        """Process card payment"""
        # Ask for card details
        card_details = self.show_input_dialog("Card Payment", "Enter last 4 digits of card:")
        if card_details:
            self.show_message("Payment", f"Card payment successful!\nCard ending in: {card_details}", "info")
            self.process_payment("Card")
    
    def process_upi_payment(self):
        """Process UPI payment"""
        # Ask for UPI ID
        upi_id = self.show_input_dialog("UPI Payment", "Enter UPI ID:")
        if upi_id:
            self.show_message("Payment", f"UPI payment successful!\nUPI ID: {upi_id}", "info")
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
