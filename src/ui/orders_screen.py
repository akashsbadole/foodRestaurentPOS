import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
from .base_ui import BaseUI
from src.utils.helpers import format_datetime, generate_bill_content
from src.utils.printer import PrinterManager
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType

class OrdersScreen(BaseUI):
    """Orders management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.item_data = {}  # Initialize item data dictionary
        self.printer_manager = PrinterManager(app.settings)
        self.current_order_items = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup simplified orders management UI"""
        # Configure modern styles
        self.configure_styles()
        
        # Main container with card styling
        main_container = self.create_modern_frame(self.app.content_frame, style="Card.TFrame", padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title with modern styling
        title_label = self.create_modern_label(main_container, "Orders Management", style="Title.TLabel")
        title_label.pack(pady=(0, SPACING_M))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Orders List Tab
        orders_tab = ttk.Frame(notebook)
        notebook.add(orders_tab, text="Orders List")
        self.setup_orders_list_tab(orders_tab)
        
        # New Order Tab
        new_order_tab = ttk.Frame(notebook)
        notebook.add(new_order_tab, text="New Order")
        self.setup_new_order_tab(new_order_tab)
        
        # Load orders
        self.load_orders()
    
    def setup_orders_list_tab(self, parent):
        """Setup the orders list tab"""
        # Filter and search container
        controls_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        controls_container.pack(fill=tk.X, pady=(SPACING_M, SPACING_S))
        
        # Simplified filter and search in one row
        filter_search_frame = ttk.Frame(controls_container)
        filter_search_frame.pack(fill=tk.X)
        
        # Filter dropdown
        self.order_filter_var = tk.StringVar(value="All")
        filter_combo = self.create_modern_combobox(
            filter_search_frame,
            textvariable=self.order_filter_var,
            values=["All", "Today", "This Week", "This Month"],
            state="readonly"
        )
        filter_combo.pack(side=tk.LEFT, padx=(0, SPACING_M))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_orders())
        
        # Search entry
        self.order_search_entry = self.create_modern_entry(filter_search_frame)
        self.order_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, SPACING_M))
        self.order_search_entry.bind("<KeyRelease>", self.search_orders)
        
        # Search button
        search_button = self.create_modern_button(
            filter_search_frame, 
            "🔍 Search", 
            self.search_orders,
            style="Primary.TButton"
        )
        search_button.pack(side=tk.RIGHT)
        
        # Orders tree
        tree_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        self.orders_tree, orders_scrollbar = self.create_modern_treeview(
            tree_container,
            ("order_number", "date", "type", "table", "total", "status"),
            ("Order No", "Date", "Type", "Table", "Total", "Status"),
            (120, 150, 80, 80, 100, 100)
        )
        self.orders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Action buttons
        buttons_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        buttons_container.pack(fill=tk.X)
        
        buttons = [
            ("📋 View Details", self.view_order_details, "Secondary.TButton"),
            ("🧾 Print Bill", self.print_bill, "Success.TButton"),
            ("🔄 Refresh", self.refresh_orders, "Secondary.TButton")
        ]
        
        self.create_button_group(buttons_container, buttons, spacing=SPACING_M)
    
    def setup_new_order_tab(self, parent):
        """Setup the new order tab with the exact layout design"""
        # Order type selection
        type_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        type_container.pack(fill=tk.X, pady=(SPACING_M, SPACING_S))
        
        type_label = self.create_modern_label(type_container, "Order Type:", style="SectionTitle.TLabel")
        type_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.order_type_var = tk.StringVar(value="Dine-in")
        type_frame = ttk.Frame(type_container)
        type_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(type_frame, text="Dine-in", variable=self.order_type_var, 
                       value="Dine-in", command=self.on_order_type_change).pack(side=tk.LEFT, padx=SPACING_M)
        ttk.Radiobutton(type_frame, text="Takeaway", variable=self.order_type_var, 
                       value="Takeaway", command=self.on_order_type_change).pack(side=tk.LEFT, padx=SPACING_M)
        
        # Customer/Table info
        info_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        info_container.pack(fill=tk.X, pady=(0, SPACING_S))
        
        self.table_frame = ttk.Frame(info_container)
        self.table_frame.pack(fill=tk.X)
        
        self.customer_frame = ttk.Frame(info_container)
        
        # Table selection (for dine-in)
        self.table_label = self.create_modern_label(self.table_frame, "Table:", style="Body.TLabel")
        self.table_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.table_var = tk.StringVar()
        self.table_combo = self.create_modern_combobox(
            self.table_frame,
            textvariable=self.table_var,
            values=self.get_available_tables(),
            state="readonly"
        )
        self.table_combo.pack(fill=tk.X)
        
        # Customer info (for takeaway)
        self.customer_label = self.create_modern_label(self.customer_frame, "Customer Name:", style="Body.TLabel")
        self.customer_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.customer_name_entry = self.create_modern_entry(self.customer_frame)
        self.customer_name_entry.pack(fill=tk.X, pady=(0, SPACING_M))
        
        self.mobile_label = self.create_modern_label(self.customer_frame, "Mobile:", style="Body.TLabel")
        self.mobile_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.customer_mobile_entry = self.create_modern_entry(self.customer_frame)
        self.customer_mobile_entry.pack(fill=tk.X)
        
        # Initialize with dine-in view
        self.on_order_type_change()
        
        # Item entry section with exact layout design
        item_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        item_container.pack(fill=tk.X, pady=(0, SPACING_S))
        
        item_label = self.create_modern_label(item_container, "Add Items:", style="SectionTitle.TLabel")
        item_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        # Create the exact layout as specified: Category | Item | Search | Qty | Add | Clear
        entry_row_frame = ttk.Frame(item_container)
        entry_row_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Category dropdown
        self.category_var = tk.StringVar()
        self.category_combo = self.create_modern_combobox(
            entry_row_frame,
            textvariable=self.category_var,
            values=self.get_all_categories(),
            state="readonly",
            width=15
        )
        self.category_combo.pack(side=tk.LEFT, padx=(0, SPACING_M))
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)
        
        # Item dropdown
        self.item_var = tk.StringVar()
        self.item_combo = self.create_modern_combobox(
            entry_row_frame,
            textvariable=self.item_var,
            values=[],
            state="readonly",
            width=20
        )
        self.item_combo.pack(side=tk.LEFT, padx=(0, SPACING_M))
        self.item_combo.bind("<<ComboboxSelected>>", self.on_item_selected)
        
        # Search bar
        self.search_entry = self.create_modern_entry(entry_row_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(0, SPACING_M))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        
        # Quantity field
        self.quantity_var = tk.StringVar(value="1")
        self.quantity_entry = self.create_modern_entry(entry_row_frame, textvariable=self.quantity_var, width=5)
        self.quantity_entry.pack(side=tk.LEFT, padx=(0, SPACING_M))
        
        # Add button
        add_button = self.create_modern_button(
            entry_row_frame,
            "Add",
            self.add_item_from_selection,
            style="Success.TButton"
        )
        add_button.pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        # Clear button
        clear_button = self.create_modern_button(
            entry_row_frame,
            "Clear",
            self.clear_item_selection,
            style="Secondary.TButton"
        )
        clear_button.pack(side=tk.LEFT)
        
        # Quick add buttons for common items
        quick_add_frame = ttk.Frame(item_container)
        quick_add_frame.pack(fill=tk.X, pady=(SPACING_S, 0))
        
        quick_add_label = self.create_modern_label(quick_add_frame, "Quick Add:", style="Body.TLabel")
        quick_add_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.setup_quick_add_buttons(quick_add_frame)
        
        # Current order items
        items_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        items_container.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_S))
        
        items_label = self.create_modern_label(items_container, "Current Order:", style="SectionTitle.TLabel")
        items_label.pack(anchor=tk.W, pady=(0, SPACING_S))
        
        items_frame = ttk.Frame(items_container)
        items_frame.pack(fill=tk.BOTH, expand=True)
        
        self.order_items_tree, items_scrollbar = self.create_modern_treeview(
            items_frame,
            ("name", "quantity", "price", "total"),
            ("Item", "Quantity", "Price", "Total"),
            (200, 80, 80, 80)
        )
        self.order_items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Order summary and action buttons
        summary_container = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
        summary_container.pack(fill=tk.X)
        
        self.summary_label = self.create_modern_label(summary_container, "Total: ₹0.00", style="SectionTitle.TLabel")
        self.summary_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Action buttons
        action_buttons = [
            ("🗑️ Clear Order", self.clear_current_order, "Secondary.TButton"),
            ("💳 Process Payment", self.process_order_payment, "Primary.TButton")
        ]
        
        self.create_button_group(summary_container, action_buttons, spacing=SPACING_M)
    
    def setup_quick_add_buttons(self, parent):
        """Setup quick add buttons for common items"""
        # Get some popular items for quick add
        try:
            popular_items = self.app.menu_item_model.get_all("", "All")[:8]  # Get first 8 items
            buttons_frame = ttk.Frame(parent)
            buttons_frame.pack(fill=tk.X)
            
            for i, item in enumerate(popular_items):
                if i % 4 == 0:
                    row_frame = ttk.Frame(buttons_frame)
                    row_frame.pack(fill=tk.X, pady=(0, SPACING_S))
                
                # item contains: id, name, category, price, stock_quantity, shortcode
                item_id, name, category, price, stock_quantity, shortcode = item
                button_text = f"{name[:15]} (₹{price:.0f})"
                
                btn = self.create_modern_button(
                    row_frame,
                    button_text,
                    lambda iid=item_id, n=name, p=price: self.quick_add_item(iid, n, p),
                    "Secondary.TButton"
                )
                btn.pack(side=tk.LEFT, padx=(0, SPACING_M), pady=SPACING_S)
                
        except Exception as e:
            print(f"Error setting up quick add buttons: {e}")
    
    def on_order_type_change(self):
        """Handle order type change"""
        if self.order_type_var.get() == "Dine-in":
            self.table_frame.pack(fill=tk.X)
            self.customer_frame.pack_forget()
        else:  # Takeaway
            self.table_frame.pack_forget()
            self.customer_frame.pack(fill=tk.X)
    
    def get_available_tables(self):
        """Get list of available tables"""
        try:
            tables = self.app.table_model.get_available()
            return [table[1] for table in tables]  # Return table numbers
        except Exception as e:
            print(f"Error getting available tables: {e}")
            return []
    
    def add_item_to_order(self):
        """Add item to current order"""
        item_text = self.item_entry.get().strip()
        if not item_text:
            return
        
        try:
            # Try to find item by ID first, then by name
            item_data = None
            
            # Try by ID if it's a number
            if item_text.isdigit():
                item_data = self.app.menu_item_model.get_by_id(int(item_text))
            
            # If not found by ID, try by name
            if not item_data:
                items = self.app.menu_item_model.get_all(item_text, "All")
                if items:
                    # Use the first match
                    item_id = items[0][0]
                    item_data = self.app.menu_item_model.get_by_id(item_id)
            
            if not item_data:
                self.show_message("Error", "Item not found", "error")
                return
            
            # Extract item data
            name, price, category_id, stock, image_path, category_name = item_data
            
            # Check stock
            if stock <= 0:
                self.show_message("Error", f"{name} is out of stock", "error")
                return
            
            # Ask for quantity
            quantity = simpledialog.askinteger(
                "Quantity",
                f"Enter quantity for {name}:",
                initialvalue=1,
                minvalue=1,
                maxvalue=stock
            )
            
            if not quantity:
                return
            
            # Add to current order
            self.add_item_to_cart(item_data[0], name, price, quantity)
            
            # Clear entry
            self.item_entry.delete(0, tk.END)
            
        except Exception as e:
            self.show_message("Error", f"Failed to add item: {e}", "error")
    
    def quick_add_item(self, item_id, name, price):
        """Quick add item with default quantity of 1"""
        try:
            # Get item data to check stock
            item_data = self.app.menu_item_model.get_by_id(item_id)
            if not item_data:
                self.show_message("Error", "Item not found", "error")
                return
            
            stock = item_data[3]  # stock is at index 3
            if stock <= 0:
                self.show_message("Error", f"{name} is out of stock", "error")
                return
            
            # Add to current order
            self.add_item_to_cart(item_id, name, price, 1)
            
        except Exception as e:
            self.show_message("Error", f"Failed to add item: {e}", "error")
    
    def add_item_to_cart(self, item_id, name, price, quantity):
        """Add item to cart"""
        # Check if item already in cart
        for item in self.current_order_items:
            if item['id'] == item_id:
                # Update quantity
                item['quantity'] += quantity
                item['total'] = item['price'] * item['quantity']
                self.update_order_display()
                return
        
        # Add new item
        self.current_order_items.append({
            'id': item_id,
            'name': name,
            'price': price,
            'quantity': quantity,
            'total': price * quantity
        })
        
        self.update_order_display()
    
    def update_order_display(self):
        """Update the order items display"""
        # Clear tree
        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)
        
        # Add items
        total = 0
        for item in self.current_order_items:
            self.order_items_tree.insert("", tk.END, values=(
                item['name'],
                item['quantity'],
                f"₹{item['price']:.2f}",
                f"₹{item['total']:.2f}"
            ))
            total += item['total']
        
        # Update total
        self.summary_label.config(text=f"Total: ₹{total:.2f}")
    
    def clear_current_order(self):
        """Clear current order"""
        if self.current_order_items:
            if self.show_message("Clear Order", "Are you sure you want to clear the current order?", "yesno"):
                self.current_order_items = []
                self.update_order_display()
    
    def process_order_payment(self):
        """Process payment for current order"""
        if not self.current_order_items:
            self.show_message("Error", "No items in order", "error")
            return
        
        # Validate order type and table/customer
        if self.order_type_var.get() == "Dine-in":
            if not self.table_var.get():
                self.show_message("Error", "Please select a table", "error")
                return
        else:  # Takeaway
            customer_name = self.customer_name_entry.get().strip()
            if not customer_name:
                self.show_message("Error", "Please enter customer name", "error")
                return
        
        # Calculate totals
        subtotal = sum(item['total'] for item in self.current_order_items)
        tax_rate = float(self.app.settings.get('tax_rate', 5))
        tax = subtotal * (tax_rate / 100)
        total = subtotal + tax
        
        # Show payment dialog
        payment_dialog = PaymentDialog(self.root, total)
        payment_mode, discount = payment_dialog.get_result()
        
        if not payment_mode:
            return
        
        # Calculate final total with discount
        final_total = total - discount
        
        try:
            # Create order data
            order_data = {
                'table_id': self.get_table_id(self.table_var.get()) if self.order_type_var.get() == "Dine-in" else None,
                'customer_name': self.customer_name_entry.get().strip() if self.order_type_var.get() == "Takeaway" else None,
                'customer_mobile': self.customer_mobile_entry.get().strip() if self.order_type_var.get() == "Takeaway" else None,
                'order_type': self.order_type_var.get(),
                'subtotal': subtotal,
                'tax': tax,
                'discount': discount,
                'total': final_total,
                'payment_mode': payment_mode,
                'items': self.current_order_items.copy()
            }
            
            # Create order
            order_id = self.app.order_model.create(order_data)
            
            # Show success
            self.show_message("Success", f"Order created successfully! Order ID: {order_id}", "info")
            
            # Clear order
            self.current_order_items = []
            self.update_order_display()
            
            # Clear form fields
            self.customer_name_entry.delete(0, tk.END)
            self.customer_mobile_entry.delete(0, tk.END)
            self.table_var.set("")
            
            # Refresh orders list
            self.load_orders()
            
        except Exception as e:
            self.show_message("Error", f"Failed to create order: {e}", "error")
    
    def get_table_id(self, table_number):
        """Get table ID from table number"""
        try:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[1] == table_number:  # table[1] is table_number
                    return table[0]  # table[0] is id
        except Exception as e:
            print(f"Error getting table ID: {e}")
        return None
    
    def filter_orders(self):
        """Filter orders based on selected filter"""
        self.load_orders()
    
    def search_orders(self, event=None):
        """Search orders"""
        self.load_orders()
    
    def load_orders(self):
        """Load orders from database"""
        filter_value = self.order_filter_var.get()
        search_term = self.order_search_entry.get()
        
        try:
            orders = self.app.order_model.get_all(filter_value, search_term)
            
            # Clear tree
            for item in self.orders_tree.get_children():
                self.orders_tree.delete(item)
            
            # Track seen order IDs to prevent duplicates
            seen_order_ids = set()
            
            # Add orders to tree
            for order in orders:
                # Ensure we have the expected number of columns
                if len(order) < 8:
                    print(f"Warning: Order data has unexpected format: {order}")
                    continue
                
                order_id, order_number, created_at, order_type, table_number, total, status, customer_name = order
                
                # Skip if we've already seen this order ID
                if order_id in seen_order_ids:
                    print(f"Warning: Duplicate order ID {order_id} found in results")
                    continue
                    
                seen_order_ids.add(order_id)
                
                # Format date
                try:
                    date_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    formatted_date = date_obj.strftime('%d-%m-%Y %H:%M')
                except (ValueError, TypeError):
                    formatted_date = str(created_at) if created_at else "N/A"
                
                # Format table/customer
                if order_type == "Dine-in":
                    table_customer = table_number or "N/A"
                else:  # Takeaway
                    table_customer = customer_name or "N/A"
                
                self.orders_tree.insert("", tk.END, values=(
                    order_number,
                    formatted_date,
                    order_type,
                    table_customer,
                    f"₹{total:.2f}",
                    status
                ), tags=(order_id,))
                
        except Exception as e:
            print(f"Error loading orders: {e}")
            self.show_message("Error", f"Failed to load orders: {e}", "error")
            
            # For debugging: show what's in the database
            try:
                # Try to get a sample order to see what data is available
                sample_orders = self.app.order_model.get_all("All", "")
                print(f"Sample orders data: {sample_orders}")
            except Exception as debug_e:
                print(f"Debug error: {debug_e}")
    
    def view_order_details(self):
        """View details of selected order"""
        selection = self.orders_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an order to view details", "warning")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Create order details window
        details_window = tk.Toplevel(self.app.root)
        details_window.title("Order Details")
        details_window.geometry("600x500")
        
        # Get order details
        order_details = self.app.order_model.get_details(order_id)
        if not order_details:
            return
        
        # order_details is a dictionary with 'order', 'items', and 'payments' keys
        order_data = order_details['order']
        items = order_details['items']
        payments = order_details['payments']
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, cgst_amount, sgst_amount, total_tax, gst_rate, discount, total, created_at, status = order_data
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == table_id:
                    table_number = table[1]
                    break
        
        # Create details frame
        details_frame = ttk.Frame(details_window, padding="20")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Order info
        info_frame = ttk.LabelFrame(details_frame, text="Order Information", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(info_frame, text=f"Order Number: {order_number}").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Date: {created_at}").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Type: {order_type}").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        if order_type == "Dine-in" and table_number:
            ttk.Label(info_frame, text=f"Table: {table_number}").grid(row=3, column=0, sticky=tk.W, pady=2)
        elif order_type == "Takeaway" and customer_name:
            ttk.Label(info_frame, text=f"Customer: {customer_name}").grid(row=3, column=0, sticky=tk.W, pady=2)
            if customer_mobile:
                ttk.Label(info_frame, text=f"Mobile: {customer_mobile}").grid(row=4, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text=f"Status: {status}").grid(row=5, column=0, sticky=tk.W, pady=2)
        
        # Order items
        items_frame = ttk.LabelFrame(details_frame, text="Order Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        items_tree, items_scrollbar = self.create_treeview(
            items_frame,
            ("name", "quantity", "price", "total", "status"),
            ("Item", "Quantity", "Price", "Total", "Status"),
            (150, 80, 80, 80, 80)
        )
        items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add items to tree
        for item in items:
            name, quantity, price, item_total, item_status = item
            items_tree.insert("", tk.END, values=(
                name,
                quantity,
                f"₹{price:.2f}",
                f"₹{item_total:.2f}",
                item_status
            ))
        
        # Order summary
        summary_frame = ttk.LabelFrame(details_frame, text="Order Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(summary_frame, text=f"Subtotal: ₹{subtotal:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"CGST ({gst_rate/2}%): ₹{cgst_amount:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"SGST ({gst_rate/2}%): ₹{sgst_amount:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Total GST ({gst_rate}%): ₹{total_tax:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Discount: ₹{discount:.2f}").pack(anchor=tk.W, pady=2)
        ttk.Label(summary_frame, text=f"Total: ₹{total:.2f}", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        
        # Payment details
        if payments:
            payment_frame = ttk.LabelFrame(details_frame, text="Payment Details", padding=10)
            payment_frame.pack(fill=tk.X, pady=10)
            
            for payment in payments:
                payment_mode, amount, payment_date = payment
                ttk.Label(payment_frame, text=f"{payment_mode}: ₹{amount:.2f} ({payment_date})").pack(anchor=tk.W, pady=2)
    
    def print_bill(self):
        """Print bill for selected order"""
        selection = self.orders_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an order to print bill", "warning")
            return
        
        # Get order ID from tags
        order_id = int(self.orders_tree.item(selection[0])['tags'][0])
        
        # Show print options dialog
        self.show_print_options(order_id)
    
    def generate_bill(self, order_id):
        """Generate bill for the order"""
        # Get order details
        order_details = self.app.order_model.get_details(order_id)
        if not order_details:
            return
        
        # order_details is a dictionary with 'order', 'items', and 'payments' keys
        order_data = order_details['order']
        items = order_details['items']
        
        order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, cgst_amount, sgst_amount, total_tax, gst_rate, discount, total, created_at, status = order_data
        
        # Get table number if dine-in
        table_number = None
        if table_id:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == table_id:
                    table_number = table[1]
                    break
        
        # Create bill content
        bill_content = generate_bill_content(
            self.app.settings, order_number, created_at, order_type, table_number,
            customer_name, customer_mobile, items, subtotal, tax, discount, total
        )
        
        # Save bill to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"Bill_{order_number}.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(bill_content)
            self.show_message("Bill Saved", f"Bill saved to {file_path}", "info")
    
    def refresh_orders(self):
        """Refresh orders list"""
        self.load_orders()
    
    def show_print_options(self, order_id):
        """Show print options dialog"""
        try:
            from src.ui.printer_dialog import PrinterSelectionDialog, PrintPreviewDialog
            
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                self.show_message("Error", "Order not found", "error")
                return
            
            # order_details is a dictionary with 'order', 'items', and 'payments' keys
            order_data = order_details['order']
            order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, cgst_amount, sgst_amount, total_tax, gst_rate, discount, total, created_at, status = order_data
            
            # Show printer selection dialog
            dialog = PrinterSelectionDialog(self.root, self.app.settings, "bill")
            result = dialog.get_result()
            
            if result:
                # Prepare bill data
                bill_data = self._prepare_bill_data(order_id)
                
                # Show preview if requested
                if result.get('preview', False):
                    content = self._get_bill_preview_content(bill_data)
                    preview_dialog = PrintPreviewDialog(self.root, content, "Bill Preview")
                    if not preview_dialog.get_result():
                        return
                
                # Print the bill
                success = self.printer_manager.print_bill(
                    bill_data,
                    result['printer_type'],
                    result['printer_name']
                )
                
                if success:
                    self.show_message("Success", "Bill printed successfully!", "info")
                else:
                    self.show_message("Error", "Failed to print bill", "error")
                    
        except Exception as e:
            self.show_message("Error", f"Print error: {str(e)}", "error")
    
    def _prepare_bill_data(self, order_id):
        """Prepare bill data for printing"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                return {}
            
            # order_details is a dictionary with 'order', 'items', and 'payments' keys
            order_data = order_details['order']
            items = order_details['items']
            
            order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, cgst_amount, sgst_amount, total_tax, gst_rate, discount, total, created_at, status = order_data
            
            # Get table number if dine-in
            table_number = None
            if table_id:
                tables = self.app.table_model.get_all()
                for table in tables:
                    if table[0] == table_id:
                        table_number = table[1]
                        break
            
            # Format items for printing
            formatted_items = []
            for item in items:
                name, quantity, price, item_total, item_status = item
                formatted_items.append((name, quantity, price, item_total))
            
            return {
                'restaurant_name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
                'restaurant_address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
                'order_number': order_number,
                'date': created_at,
                'order_type': order_type,
                'table_number': table_number,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'items': formatted_items,
                'subtotal': subtotal,
                'tax': tax,
                'cgst_amount': cgst_amount,
                'sgst_amount': sgst_amount,
                'total_tax': total_tax,
                'gst_rate': gst_rate,
                'discount': discount,
                'total': total,
                'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE))
            }
            
        except Exception as e:
            print(f"Error preparing bill data: {e}")
            return {}
    
    def _get_bill_preview_content(self, bill_data):
        """Get bill preview content for display"""
        return generate_bill_content(
            bill_data.get('restaurant_name', ''),
            bill_data.get('restaurant_address', ''),
            bill_data,
            bill_data.get('items', []),
            bill_data.get('subtotal', 0),
            bill_data.get('tax', 0),
            bill_data.get('discount', 0),
            bill_data.get('total', 0)
        )
    
    def get_all_categories(self):
        """Get all categories for the dropdown"""
        try:
            categories = ["All"]  # Add "All" option
            category_list = self.app.category_model.get_all()
            for category in category_list:
                categories.append(category[1])  # category[1] is name
            return categories
        except Exception as e:
            print(f"Error getting categories: {e}")
            return ["All"]
    
    def get_items_by_category(self, category_name):
        """Get items filtered by category"""
        try:
            if category_name == "All":
                items = self.app.menu_item_model.get_all("", "All")
            else:
                items = self.app.menu_item_model.get_all("", category_name)
            
            # Format items for display
            item_list = []
            for item in items:
                # item contains: id, name, category, price, stock_quantity, shortcode
                item_id, name, category, price, stock_quantity, shortcode = item
                display_text = f"{name} (₹{price:.0f})"
                item_list.append((display_text, item_id))
            return item_list
        except Exception as e:
            print(f"Error getting items by category: {e}")
            return []
    
    def on_category_change(self, event=None):
        """Handle category selection change"""
        category_name = self.category_var.get()
        items = self.get_items_by_category(category_name)
        
        # Update item dropdown
        item_values = [item[0] for item in items]
        self.item_combo['values'] = item_values
        self.item_var.set("")  # Clear selection
        
        # Store item IDs for later use
        self.item_data = {item[0]: item[1] for item in items}
    
    def on_item_selected(self, event=None):
        """Handle item selection"""
        # When an item is selected, update the search field with the item name
        selected_item = self.item_var.get()
        if selected_item:
            # Extract item name from the display text (remove price part)
            item_name = selected_item.split(" (₹")[0]
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, item_name)
    
    def on_search_change(self, event=None):
        """Handle search text change"""
        search_text = self.search_entry.get().strip()
        
        if search_text:
            # Filter items based on search text
            category_name = self.category_var.get()
            all_items = self.get_items_by_category(category_name)
            
            # Filter items that contain the search text
            filtered_items = [item[0] for item in all_items if search_text.lower() in item[0].lower()]
            
            # Update item dropdown with filtered results
            self.item_combo['values'] = filtered_items
            if filtered_items and not self.item_var.get():
                self.item_combo['values'] = filtered_items
        else:
            # If search is empty, show all items for the selected category
            self.on_category_change()
    
    def add_item_from_selection(self):
        """Add item based on current selection"""
        try:
            # Get selected item
            selected_item = self.item_var.get()
            if not selected_item:
                # Try to use search text if no item is selected
                selected_item = self.search_entry.get().strip()
            
            if not selected_item:
                self.show_message("Error", "Please select or search for an item", "error")
                return
            
            # Get item ID
            item_id = None
            if selected_item in self.item_data:
                item_id = self.item_data[selected_item]
            else:
                # Try to find by exact name match
                category_name = self.category_var.get()
                all_items = self.get_items_by_category(category_name)
                for display_text, id in all_items:
                    item_name = display_text.split(" (₹")[0]
                    if item_name == selected_item:
                        item_id = id
                        break
            
            if not item_id:
                self.show_message("Error", "Item not found", "error")
                return
            
            # Get item details
            item_data = self.app.menu_item_model.get_by_id(item_id)
            if not item_data:
                self.show_message("Error", "Item not found", "error")
                return
            
            # Extract item data
            name, price, category_id, stock, image_path, category_name = item_data
            
            # Check stock
            if stock <= 0:
                self.show_message("Error", f"{name} is out of stock", "error")
                return
            
            # Get quantity
            try:
                quantity = int(self.quantity_var.get())
                if quantity < 1:
                    quantity = 1
                if quantity > stock:
                    self.show_message("Error", f"Only {stock} items available in stock", "error")
                    return
            except ValueError:
                quantity = 1
                self.quantity_var.set("1")
            
            # Add to current order
            self.add_item_to_cart(item_id, name, price, quantity)
            
            # Clear selection
            self.clear_item_selection()
            
        except Exception as e:
            self.show_message("Error", f"Failed to add item: {e}", "error")
    
    def clear_item_selection(self):
        """Clear all item selection fields"""
        self.item_var.set("")
        self.search_entry.delete(0, tk.END)
        self.quantity_var.set("1")
        self.item_combo['values'] = []


class PaymentDialog:
    """Simple payment dialog"""
    
    def __init__(self, parent, total_amount):
        self.result = None
        self.total_amount = total_amount
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Process Payment")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup payment dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Order total
        total_label = ttk.Label(main_frame, text=f"Order Total: ₹{self.total_amount:.2f}", 
                               font=('Arial', 12, 'bold'))
        total_label.pack(pady=(0, 20))
        
        # Payment mode
        mode_label = ttk.Label(main_frame, text="Payment Mode:")
        mode_label.pack(anchor=tk.W)
        
        self.payment_mode_var = tk.StringVar(value="Cash")
        payment_modes = ["Cash", "Card", "UPI"]
        
        for mode in payment_modes:
            ttk.Radiobutton(main_frame, text=mode, variable=self.payment_mode_var, 
                           value=mode).pack(anchor=tk.W, pady=2)
        
        # Discount
        discount_label = ttk.Label(main_frame, text="Discount (₹):")
        discount_label.pack(anchor=tk.W, pady=(20, 5))
        
        self.discount_var = tk.StringVar(value="0")
        discount_entry = ttk.Entry(main_frame, textvariable=self.discount_var)
        discount_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Final amount
        self.final_amount_label = ttk.Label(main_frame, text=f"Final Amount: ₹{self.total_amount:.2f}", 
                                          font=('Arial', 11, 'bold'))
        self.final_amount_label.pack(pady=(10, 20))
        
        # Update final amount when discount changes
        self.discount_var.trace('w', self.update_final_amount)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Process Payment", command=self.process).pack(side=tk.RIGHT)
    
    def update_final_amount(self, *args):
        """Update final amount when discount changes"""
        try:
            discount = float(self.discount_var.get() or 0)
            final_amount = max(0, self.total_amount - discount)
            self.final_amount_label.config(text=f"Final Amount: ₹{final_amount:.2f}")
        except ValueError:
            self.final_amount_label.config(text=f"Final Amount: ₹{self.total_amount:.2f}")
    
    def process(self):
        """Process payment"""
        try:
            discount = float(self.discount_var.get() or 0)
            if discount < 0 or discount > self.total_amount:
                messagebox.showerror("Error", "Invalid discount amount")
                return
            
            self.result = (self.payment_mode_var.get(), discount)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid discount amount")
    
    def cancel(self):
        """Cancel payment"""
        self.dialog.destroy()
    
    def get_result(self):
        """Get payment result"""
        self.dialog.wait_window()
        return self.result
