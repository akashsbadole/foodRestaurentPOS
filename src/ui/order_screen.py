import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from .base_ui import BaseUI
from src.utils.helpers import generate_order_number, format_currency
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType

class OrderScreen(BaseUI):
    """New Order Screen for creating and managing orders"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.root = root
        self.app = app
        self.db = app.db  # Add database reference
        
        # Order data
        self.order_items = []
        self.current_table_id = None
        self.current_customer = ""
        self.current_customer_mobile = ""
        self.order_type = tk.StringVar(value="Dine-in")
        self.subtotal = 0.0
        self.tax = 0.0
        self.discount = 0.0
        self.total = 0.0
        
        # UI components
        self.content_frame = None
        self.order_tree = None
        self.category_combo = None
        self.menu_combo = None
        self.quantity_var = None
        self.table_combo = None
        
    def setup_ui(self):
        """Setup the order screen UI"""
        # Clear content frame
        if self.app.content_frame:
            for widget in self.app.content_frame.winfo_children():
                widget.destroy()
        else:
            # Create content frame if it doesn't exist
            self.app.content_frame = ttk.Frame(self.app.root)
            self.app.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.content_frame = self.app.content_frame
        
        # Title
        title_label = ttk.Label(self.content_frame, text="New Order", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Order type and customer info frame
        info_frame = ttk.Frame(self.content_frame)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Order type
        ttk.Label(info_frame, text="Order Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Radiobutton(info_frame, text="Dine-in", variable=self.order_type, 
                       value="Dine-in", command=self.on_order_type_changed).grid(row=0, column=1, padx=5)
        ttk.Radiobutton(info_frame, text="Takeaway", variable=self.order_type, 
                       value="Takeaway", command=self.on_order_type_changed).grid(row=0, column=2, padx=5)
        
        # Customer info
        ttk.Label(info_frame, text="Customer Name:").grid(row=0, column=3, sticky=tk.W, padx=5)
        self.customer_entry = ttk.Entry(info_frame, width=20)
        self.customer_entry.grid(row=0, column=4, padx=5)
        
        ttk.Label(info_frame, text="Mobile:").grid(row=0, column=5, sticky=tk.W, padx=5)
        self.mobile_entry = ttk.Entry(info_frame, width=15)
        self.mobile_entry.grid(row=0, column=6, padx=5)
        
        # Table selection (for dine-in)
        self.table_frame = ttk.Frame(self.content_frame)
        self.table_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.table_frame, text="Table:").pack(side=tk.LEFT, padx=5)
        self.table_combo = ttk.Combobox(self.table_frame, width=20, state="readonly")
        self.table_combo.pack(side=tk.LEFT, padx=5)
        
        # Load available tables
        self.load_tables()
        
        # Menu selection frame
        menu_frame = ttk.LabelFrame(self.content_frame, text="Add Items", padding=10)
        menu_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # First row - Category and Menu Item
        ttk.Label(menu_frame, text="Category:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.category_combo = ttk.Combobox(menu_frame, width=20, state="readonly")
        self.category_combo.grid(row=0, column=1, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_changed)
        
        ttk.Label(menu_frame, text="Item:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.menu_combo = ttk.Combobox(menu_frame, width=30, state="readonly")
        self.menu_combo.grid(row=0, column=3, padx=5)
        
        # Second row - Search
        ttk.Label(menu_frame, text="Search:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.menu_search_var = tk.StringVar()
        self.menu_search_entry = ttk.Entry(menu_frame, textvariable=self.menu_search_var, width=30)
        self.menu_search_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        self.menu_search_entry.bind("<KeyRelease>", self.search_menu_items)
        
        # Clear search button
        clear_search_btn = ttk.Button(menu_frame, text="Clear", command=self.clear_menu_search)
        clear_search_btn.grid(row=1, column=3, padx=5, pady=5)
        
        # Third row - Quantity and Add button
        ttk.Label(menu_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.quantity_var = tk.StringVar(value="1")
        quantity_spin = ttk.Spinbox(menu_frame, from_=1, to=99, textvariable=self.quantity_var, width=10)
        quantity_spin.grid(row=2, column=1, padx=5, pady=5)
        
        # Add button
        add_button = ttk.Button(menu_frame, text="Add Item", command=self.add_item)
        add_button.grid(row=2, column=2, columnspan=2, padx=5, pady=5)
        
        # Load categories
        self.load_categories()
        
        # Order items frame
        items_frame = ttk.LabelFrame(self.content_frame, text="Order Items", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for order items
        self.order_tree, scrollbar = self.create_treeview(
            items_frame,
            ("name", "quantity", "price", "total"),
            ("Item", "Quantity", "Price", "Total"),
            (200, 80, 100, 100)
        )
        self.order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Right click menu for order items
        self.order_tree.bind("<Button-3>", self.show_item_context_menu)
        
        # Order summary frame
        summary_frame = ttk.Frame(self.content_frame)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Summary labels
        summary_info = ttk.Frame(summary_frame)
        summary_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.subtotal_label = ttk.Label(summary_info, text="Subtotal: ₹0.00")
        self.subtotal_label.pack(anchor=tk.W, pady=2)
        
        self.tax_label = ttk.Label(summary_info, text="Tax: ₹0.00")
        self.tax_label.pack(anchor=tk.W, pady=2)
        
        self.discount_label = ttk.Label(summary_info, text="Discount: ₹0.00")
        self.discount_label.pack(anchor=tk.W, pady=2)
        
        self.total_label = ttk.Label(summary_info, text="Total: ₹0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(anchor=tk.W, pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(summary_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(buttons_frame, text="Apply Discount", command=self.apply_discount).pack(pady=2)
        ttk.Button(buttons_frame, text="Clear Order", command=self.clear_order).pack(pady=2)
        ttk.Button(buttons_frame, text="Save Order", command=self.save_order).pack(pady=2)
        ttk.Button(buttons_frame, text="Save & Print", command=self.save_and_print_order).pack(pady=2)
        
    def load_tables(self):
        """Load available tables"""
        tables = self.app.table_model.get_available()
        table_list = [(f"Table {table[1]}", table[0]) for table in tables]
        self.table_combo['values'] = [table[0] for table in table_list]
        if table_list:
            self.table_combo.current(0)
            self.current_table_id = table_list[0][1]
    
    def load_categories(self):
        """Load menu categories"""
        categories = self.app.category_model.get_all()
        category_list = [("All Categories", "All")] + [(cat[1], cat[0]) for cat in categories]
        self.category_combo['values'] = [cat[0] for cat in category_list]
        if category_list:
            self.category_combo.current(0)
    
    def on_category_changed(self, event=None):
        """Handle category selection change"""
        category_name = self.category_combo.get()
        if category_name == "All Categories":
            self.load_menu_items("")
        else:
            self.load_menu_items(category_name)
    
    def load_menu_items(self, category_name):
        """Load menu items for selected category"""
        if category_name == "All Categories":
            menu_items = self.app.menu_item_model.get_all()
        else:
            menu_items = self.app.menu_item_model.get_all("", category_name)
        
        self._update_menu_combo(menu_items)
    
    def _update_menu_combo(self, menu_items):
        """Update the menu combo box with the provided items"""
        menu_list = [(f"{item[1]} - ₹{item[3]:.2f}", item[0]) for item in menu_items]
        self.menu_combo['values'] = [item[0] for item in menu_list]
        if menu_list:
            self.menu_combo.current(0)
    
    def search_menu_items(self, event=None):
        """Search menu items based on search term"""
        search_term = self.menu_search_var.get().strip()
        category_name = self.category_combo.get()
        
        if not search_term:
            # If search is empty, load items for the selected category
            self.load_menu_items(category_name)
            return
        
        # Search items by name in the selected category
        if category_name == "All Categories":
            menu_items = self.app.menu_item_model.get_all(search_term)
        else:
            menu_items = self.app.menu_item_model.get_all(search_term, category_name)
        
        self._update_menu_combo(menu_items)
    
    def clear_menu_search(self):
        """Clear the search and reload items for the selected category"""
        self.menu_search_var.set("")
        category_name = self.category_combo.get()
        self.load_menu_items(category_name)
    
    def on_order_type_changed(self):
        """Handle order type change"""
        if self.order_type.get() == "Dine-in":
            self.table_frame.pack(fill=tk.X, padx=10, pady=5, before=self.content_frame.winfo_children()[2])
        else:
            self.table_frame.pack_forget()
    
    def add_item(self):
        """Add item to order"""
        try:
            # Get selected menu item
            menu_selection = self.menu_combo.get()
            if not menu_selection:
                messagebox.showwarning("Warning", "Please select a menu item")
                return
            
            # Parse menu item name and get menu item ID
            menu_item_name = menu_selection.split(" - ₹")[0]
            menu_items = self.app.menu_item_model.get_all(menu_item_name)
            if not menu_items:
                messagebox.showerror("Error", "Menu item not found")
                return
            
            menu_item = menu_items[0]
            menu_item_id = menu_item[0]
            item_name = menu_item[1]
            price = float(menu_item[3])
            
            # Get quantity
            try:
                quantity = int(self.quantity_var.get())
                if quantity <= 0:
                    raise ValueError("Quantity must be positive")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid quantity: {e}")
                return
            
            # Check stock availability
            if menu_item[4] < quantity:
                messagebox.showwarning("Warning", f"Insufficient stock. Available: {menu_item[4]}")
                return
            
            # Add to order items
            item_total = price * quantity
            self.order_items.append({
                'menu_item_id': menu_item_id,
                'name': item_name,
                'quantity': quantity,
                'price': price,
                'total': item_total
            })
            
            # Add to treeview
            self.order_tree.insert("", tk.END, values=(
                item_name,
                quantity,
                f"₹{price:.2f}",
                f"₹{item_total:.2f}"
            ))
            
            # Update totals
            self.update_totals()
            
            # Reset selection
            self.quantity_var.set("1")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")
            print(f"Add item error details: {e}")
    
    def show_item_context_menu(self, event):
        """Show context menu for order items"""
        selection = self.order_tree.selection()
        if selection:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Remove Item", command=lambda: self.remove_item(selection[0]))
            context_menu.post(event.x_root, event.y_root)
    
    def remove_item(self, item_id):
        """Remove item from order"""
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove")
            return
        
        # Get selected index
        selected_index = self.order_tree.index(selection[0])
        
        # Remove from order items
        if 0 <= selected_index < len(self.order_items):
            del self.order_items[selected_index]
        else:
            messagebox.showerror("Error", "Invalid item selection")
            return
        
        # Remove from treeview
        self.order_tree.delete(selection[0])
        
        # Update totals
        self.update_totals()
        
        # Reset selection if no items left
        if not self.order_items:
            self.order_tree.selection_set("")
    
    def update_totals(self):
        """Update order totals"""
        try:
            self.subtotal = sum(item['total'] for item in self.order_items)
            tax_rate = float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE))
            self.tax = self.subtotal * (tax_rate / 100)
            self.total = self.subtotal + self.tax - self.discount
            
            # Update labels
            self.subtotal_label.config(text=f"Subtotal: ₹{self.subtotal:.2f}")
            self.tax_label.config(text=f"Tax: ₹{self.tax:.2f}")
            self.discount_label.config(text=f"Discount: ₹{self.discount:.2f}")
            self.total_label.config(text=f"Total: ₹{self.total:.2f}")
        except Exception as e:
            print(f"Error updating totals: {e}")
            # Reset to zero if there's an error
            self.subtotal = 0.0
            self.tax = 0.0
            self.total = 0.0
            self.discount = 0.0
            self.subtotal_label.config(text="Subtotal: ₹0.00")
            self.tax_label.config(text="Tax: ₹0.00")
            self.discount_label.config(text="Discount: ₹0.00")
            self.total_label.config(text="Total: ₹0.00")
    
    def apply_discount(self):
        """Apply discount to order"""
        try:
            discount_str = simpledialog.askstring("Discount", "Enter discount amount:")
            if discount_str:
                discount = float(discount_str)
                if discount < 0:
                    raise ValueError("Discount cannot be negative")
                if discount > self.subtotal:
                    raise ValueError("Discount cannot exceed subtotal")
                
                self.discount = discount
                self.update_totals()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid discount: {e}")
    
    def clear_order(self):
        """Clear current order"""
        if messagebox.askyesno("Confirm", "Clear current order?"):
            self.order_items = []
            self.order_tree.delete(*self.order_tree.get_children())
            self.discount = 0.0
            self.update_totals()
    
    def save_order(self, print_bill=False):
        """Save the order"""
        try:
            if not self.order_items:
                messagebox.showwarning("Warning", "No items in order")
                return
            
            # Get order details
            order_type = self.order_type.get()
            table_id = None
            
            if order_type == "Dine-in":
                table_selection = self.table_combo.get()
                if table_selection:
                    table_number = table_selection.split(" ")[1]
                    tables = self.app.table_model.get_all()
                    for table in tables:
                        if str(table[1]) == table_number:
                            table_id = table[0]
                            break
                
                if not table_id:
                    messagebox.showwarning("Warning", "Please select a table")
                    return
            
            customer_name = self.customer_entry.get().strip()
            customer_mobile = self.mobile_entry.get().strip()
            
            if order_type == "Takeaway" and not customer_name:
                messagebox.showwarning("Warning", "Please enter customer name for takeaway order")
                return
            
            # Generate order number
            order_number = generate_order_number()
            
            # Create order
            order_data = (
                order_number,
                table_id,
                customer_name,
                customer_mobile,
                order_type,
                self.subtotal,
                self.tax,
                self.discount,
                self.total
            )
            
            order_id = self.app.order_model.create(order_data)
            if not order_id:
                messagebox.showerror("Error", "Failed to create order")
                return
            
            # Add order items
            for item in self.order_items:
                self.app.order_model.add_item(
                    order_id,
                    item['menu_item_id'],
                    item['quantity'],
                    item['price'],
                    item['total']
                )
                
                # Update stock
                menu_item = self.app.menu_item_model.get_by_id(item['menu_item_id'])
                if menu_item:
                    new_stock = menu_item[3] - item['quantity']
                    self.app.menu_item_model.update_stock(item['menu_item_id'], new_stock)
            
            # Add payment (default to cash for now)
            self.app.order_model.add_payment(order_id, "Cash", self.total)
            
            # Update table status if dine-in
            if order_type == "Dine-in" and table_id:
                self.app.table_model.update_status(table_id, "Occupied")
            
            # Show success message
            messagebox.showinfo("Success", f"Order {order_number} saved successfully!")
            
            # Print bill if requested
            if print_bill:
                self.print_bill(order_id)
            
            # Clear order and refresh
            self.clear_order()
            
            # Dispatch events
            event_dispatcher.order_created(order_id)
            event_dispatcher.inventory_updated(None, None)  # Trigger inventory refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")
    
    def save_and_print_order(self):
        """Save order and print bill"""
        self.save_order(print_bill=True)
    
    def print_bill(self, order_id):
        """Print bill for the order"""
        try:
            from src.ui.printer_dialog import PrinterSelectionDialog
            from src.utils.printer import PrinterManager
            
            # Show printer selection dialog
            dialog = PrinterSelectionDialog(self.root, self.app.settings, "bill")
            result = dialog.get_result()
            
            if result:
                # Prepare bill data
                bill_data = self._prepare_bill_data(order_id)
                
                # Print the bill
                printer_manager = PrinterManager(self.app.settings)
                success = printer_manager.print_bill(
                    bill_data,
                    result['printer_type'],
                    result['printer_name']
                )
                
                if success:
                    messagebox.showinfo("Success", "Bill printed successfully!")
                else:
                    messagebox.showerror("Error", "Failed to print bill")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Print error: {e}")
    
    def _prepare_bill_data(self, order_id):
        """Prepare bill data for printing"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                return {}
            
            order_number, table_id, customer_name, customer_mobile, order_type, subtotal, tax, discount, total, created_at, status = order_details
            
            # Get table number if dine-in
            table_number = None
            if table_id:
                tables = self.app.table_model.get_all()
                for table in tables:
                    if table[0] == table_id:
                        table_number = table[1]
                        break
            
            # Get order items
            items = self.app.order_model.get_items(order_id)
            
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
                'discount': discount,
                'total': total,
                'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE))
            }
            
        except Exception as e:
            print(f"Error preparing bill data: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup resources when screen is destroyed"""
        # Add any cleanup code here
        pass
