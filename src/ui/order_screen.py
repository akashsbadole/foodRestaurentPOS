import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from .base_ui import BaseUI
from .export_dialog import ExportDialog
from src.utils.helpers import generate_order_number, format_currency
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.utils.pdf_exporter import PDFExporter
from src.utils.text_exporter import TextExporter
import os
import subprocess

class OrderScreen(BaseUI):
    """New Order Screen for creating and managing multiple orders"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.root = root
        self.app = app
        self.db = app.db  # Add database reference
        
        # Multiple orders management
        self.active_orders = {}  # {order_id: order_data}
        self.current_order_id = None
        
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
        
        # Payment options
        self.payment_methods = ["Cash", "Card", "UPI", "Wallet", "Credit"]
        
        # Export functionality
        self.pdf_exporter = PDFExporter({
            'name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
            'address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
            'phone': self.app.settings.get('restaurant_phone', ''),
            'email': self.app.settings.get('restaurant_email', ''),
            'gst_number': self.app.settings.get('gst_number', '')
        })
        self.text_exporter = TextExporter({
            'name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
            'address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
            'phone': self.app.settings.get('restaurant_phone', ''),
            'email': self.app.settings.get('restaurant_email', ''),
            'gst_number': self.app.settings.get('gst_number', '')
        })
        
        # UI components
        self.content_frame = None
        self.order_tree = None
        self.category_combo = None
        self.menu_combo = None
        self.quantity_var = None
        self.table_combo = None
        
    def setup_ui(self):
        """Setup order screen UI"""
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
        
        # Load categories and initialize first order
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
        
        # Multiple orders management
        orders_frame = ttk.Frame(summary_frame)
        orders_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        ttk.Label(orders_frame, text="Active Orders:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=2)
        
        # Orders listbox with scrollbar
        orders_list_frame = ttk.Frame(orders_frame)
        orders_list_frame.pack(fill=tk.BOTH, expand=True, pady=2)
        
        scrollbar = ttk.Scrollbar(orders_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.orders_listbox = tk.Listbox(orders_list_frame, height=4, yscrollcommand=scrollbar.set)
        self.orders_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.orders_listbox.yview)
        
        self.orders_listbox.bind('<<ListboxSelect>>', self.on_order_select)
        
        # Order management buttons
        order_mgmt_frame = ttk.Frame(orders_frame)
        order_mgmt_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(order_mgmt_frame, text="New Order", command=self.new_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(order_mgmt_frame, text="Switch To", command=self.switch_to_order).pack(side=tk.LEFT, padx=2)
        ttk.Button(order_mgmt_frame, text="Delete Order", command=self.delete_order).pack(side=tk.LEFT, padx=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(summary_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(buttons_frame, text="Apply Discount", command=self.apply_discount).pack(pady=2)
        ttk.Button(buttons_frame, text="Clear Order", command=self.clear_order).pack(pady=2)
        ttk.Button(buttons_frame, text="Process Payment", command=self.process_payment).pack(pady=2)
        
        # Export buttons
        ttk.Separator(buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(buttons_frame, text="Export Order", command=self.export_order).pack(pady=2)
        
        # Initialize first order after all UI components are created
        self.new_order()
        
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
    
    def save_order(self, print_bill=False, export_order=False):
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
            
            # Create order using dictionary format
            order_data = {
                'order_number': order_number,
                'table_id': table_id,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'order_type': order_type,
                'subtotal': self.subtotal,
                'tax': self.tax,
                'discount': self.discount,
                'total': self.total,
                'items': [{'id': item['menu_item_id'], 'quantity': item['quantity'],
                          'price': item['price'], 'total': item['total']}
                         for item in self.order_items]
            }
            
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
            
            # Handle export based on settings and parameters
            self._handle_post_payment_export(order_id, export_order)
            
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
    
    def save_and_export_order(self):
        """Save order and export with options"""
        self.save_order(export_order=True)
    
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
    
    def export_order(self):
        """Export current order without saving"""
        if not self.order_items:
            messagebox.showwarning("Warning", "No items in order to export")
            return
        
        # Prepare order data for export
        order_data = self._prepare_export_data()
        
        # Show export dialog
        dialog = ExportDialog(self.root, self.app.settings, order_data)
        result = dialog.get_result()
        
        if result:
            self._process_export(order_data, result)
    
    def export_order_with_id(self, order_id):
        """Export saved order by ID"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                messagebox.showerror("Error", "Order not found")
                return
            
            # Prepare order data for export
            order_data = self._prepare_export_data_from_details(order_details)
            
            # Show export dialog
            dialog = ExportDialog(self.root, self.app.settings, order_data)
            result = dialog.get_result()
            
            if result:
                self._process_export(order_data, result)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export order: {e}")
    
    def _prepare_export_data(self):
        """Prepare order data for export from current order"""
        # Get table number if dine-in
        table_number = None
        if self.order_type.get() == "Dine-in":
            table_selection = self.table_combo.get()
            if table_selection:
                table_number = table_selection.split(" ")[1]
        
        return {
            'order_number': generate_order_number(),
            'table_number': table_number,
            'customer_name': self.customer_entry.get().strip(),
            'customer_mobile': self.mobile_entry.get().strip(),
            'order_type': self.order_type.get(),
            'status': 'Completed',
            'subtotal': self.subtotal,
            'tax': self.tax,
            'discount': self.discount,
            'total': self.total,
            'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE)),
            'items': [(item['name'], item['quantity'], item['price'], item['total'])
                     for item in self.order_items],
            'payments': [('Cash', self.total, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _prepare_export_data_from_details(self, order_details):
        """Prepare order data for export from order details"""
        order = order_details['order']
        items = order_details['items']
        payments = order_details['payments']
        
        # Get table number if dine-in
        table_number = None
        if order[1]:  # table_id exists
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == order[1]:
                    table_number = table[1]
                    break
        
        return {
            'order_number': order[0],
            'table_number': table_number,
            'customer_name': order[2],
            'customer_mobile': order[3],
            'order_type': order[4],
            'status': order[10],
            'subtotal': order[5],
            'tax': order[6],
            'discount': order[7],
            'total': order[8],
            'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE)),
            'items': items,
            'payments': payments,
            'created_at': order[9]
        }
    
    def _process_export(self, order_data, export_options):
        """Process the export with selected options"""
        try:
            exported_files = []
            
            # Export to PDF if selected
            if export_options['export_pdf']:
                if export_options['custom_location'] and export_options['location']:
                    # Use custom location
                    filename = f"Order_{order_data['order_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    filepath = os.path.join(export_options['location'], filename)
                    success, result = self._export_pdf_to_location(order_data, filepath)
                else:
                    # Use default location
                    success, result = self.pdf_exporter.export_order(order_data)
                
                if success:
                    exported_files.append(result if isinstance(result, str) else filepath)
                    if export_options.get('auto_open'):
                        self._open_file(result if isinstance(result, str) else filepath)
                else:
                    messagebox.showerror("Export Error", f"Failed to export PDF: {result}")
                    return
            
            # Export to Text if selected
            if export_options['export_text']:
                if export_options['custom_location'] and export_options['location']:
                    # Use custom location
                    filename = f"Order_{order_data['order_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    filepath = os.path.join(export_options['location'], filename)
                    success, result = self._export_text_to_location(order_data, filepath)
                else:
                    # Use default location
                    success, result = self.text_exporter.export_order(order_data)
                
                if success:
                    exported_files.append(result if isinstance(result, str) else filepath)
                    if export_options.get('auto_open'):
                        self._open_file(result if isinstance(result, str) else filepath)
                else:
                    messagebox.showerror("Export Error", f"Failed to export Text: {result}")
                    return
            
            # Show success message
            if exported_files:
                file_count = len(exported_files)
                messagebox.showinfo(
                    "Export Successful",
                    f"Order exported successfully to {file_count} file{'s' if file_count > 1 else ''}!"
                )
            else:
                messagebox.showwarning("Export Warning", "No files were exported")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"An error occurred during export: {e}")
    
    def _export_pdf_to_location(self, order_data, filepath):
        """Export PDF to specific location"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                leftMargin=20 * mm,
                rightMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=20 * mm
            )
            
            # Build PDF content using the existing PDF exporter logic
            # Temporarily override the export directory
            original_dir = self.pdf_exporter.export_dir
            self.pdf_exporter.export_dir = os.path.dirname(filepath)
            
            # Export and then move the file to the exact location
            success, result = self.pdf_exporter.export_order(order_data)
            
            # Restore original directory
            self.pdf_exporter.export_dir = original_dir
            
            if success and os.path.exists(result):
                # Move to exact location if needed
                if result != filepath:
                    import shutil
                    shutil.move(result, filepath)
                return True, filepath
            else:
                return False, result
                
        except Exception as e:
            return False, str(e)
    
    def _export_text_to_location(self, order_data, filepath):
        """Export Text to specific location"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Temporarily override the export directory
            original_dir = self.text_exporter.export_dir
            self.text_exporter.export_dir = os.path.dirname(filepath)
            
            # Export and then move the file to the exact location
            success, result = self.text_exporter.export_order(order_data)
            
            # Restore original directory
            self.text_exporter.export_dir = original_dir
            
            if success and os.path.exists(result):
                # Move to exact location if needed
                if result != filepath:
                    import shutil
                    shutil.move(result, filepath)
                return True, filepath
            else:
                return False, result
                
        except Exception as e:
            return False, str(e)
    
    def _open_file(self, filepath):
        """Open file with default application"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open', filepath], check=True)
        except Exception as e:
            print(f"Failed to open file: {e}")
    
    def _handle_post_payment_export(self, order_id, manual_export=False):
        """Handle export after payment completion based on settings"""
        try:
            # Get export settings
            export_after_payment = self.app.settings.get('export_after_payment', 'false').lower() == 'true'
            default_export_format = self.app.settings.get('default_export_format', 'none')
            show_export_dialog = self.app.settings.get('show_export_dialog', 'true').lower() == 'true'
            
            # Skip if auto-export is disabled and this is not a manual export
            if not export_after_payment and not manual_export:
                return
            
            # If manual export or dialog is enabled, show export dialog
            if manual_export or show_export_dialog:
                self.export_order_with_id(order_id)
            else:
                # Auto-export with default format
                if default_export_format != 'none':
                    self._auto_export_order(order_id, default_export_format)
                    
        except Exception as e:
            # Export failures should not affect payment completion
            print(f"Export error (non-critical): {e}")
            # Optionally show a non-blocking notification
            # messagebox.showinfo("Export Info", f"Export completed with warnings: {e}")
    
    def _auto_export_order(self, order_id, export_format):
        """Automatically export order in specified format"""
        try:
            # Get order details
            order_details = self.app.order_model.get_details(order_id)
            if not order_details:
                print(f"Order {order_id} not found for auto-export")
                return
            
            # Prepare order data for export
            order_data = self._prepare_export_data_from_details(order_details)
            
            # Export based on format
            if export_format == 'pdf':
                success, result = self.pdf_exporter.export_order(order_data)
                if success:
                    print(f"Order {order_id} auto-exported to PDF: {result}")
                else:
                    print(f"Failed to auto-export order {order_id} to PDF: {result}")
                    
            elif export_format == 'text':
                success, result = self.text_exporter.export_order(order_data)
                if success:
                    print(f"Order {order_id} auto-exported to Text: {result}")
                else:
                    print(f"Failed to auto-export order {order_id} to Text: {result}")
                    
            elif export_format == 'both':
                # Export both formats
                pdf_success, pdf_result = self.pdf_exporter.export_order(order_data)
                text_success, text_result = self.text_exporter.export_order(order_data)
                
                if pdf_success:
                    print(f"Order {order_id} auto-exported to PDF: {pdf_result}")
                else:
                    print(f"Failed to auto-export order {order_id} to PDF: {pdf_result}")
                    
                if text_success:
                    print(f"Order {order_id} auto-exported to Text: {text_result}")
                else:
                    print(f"Failed to auto-export order {order_id} to Text: {text_result}")
                    
        except Exception as e:
            print(f"Auto-export error for order {order_id}: {e}")
    
    def new_order(self):
        """Create a new order"""
        if not self.current_order_id or self.order_items:
            # Save current order if it has items
            if self.order_items:
                if not messagebox.askyesno("Save Order", "Current order has items. Save before creating new order?"):
                    return
                self.save_current_order_to_memory()
        
        # Create new order
        self.current_order_id = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.order_items = []
        self.discount = 0.0
        self.update_totals()
        self.update_orders_list()
    
    def switch_to_order(self):
        """Switch to selected order"""
        selection = self.orders_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an order to switch to")
            return
        
        order_id = self.orders_listbox.get(selection[0]).split(" - ")[0]
        if order_id in self.active_orders:
            # Save current order if it has items
            if self.order_items:
                self.save_current_order_to_memory()
            
            # Load selected order
            self.load_order_from_memory(order_id)
    
    def delete_order(self):
        """Delete selected order"""
        selection = self.orders_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an order to delete")
            return
        
        order_id = self.orders_listbox.get(selection[0]).split(" - ")[0]
        if messagebox.askyesno("Confirm Delete", f"Delete order {order_id}?"):
            if order_id in self.active_orders:
                del self.active_orders[order_id]
                
                # If deleting current order, create new one
                if order_id == self.current_order_id:
                    self.new_order()
                else:
                    self.update_orders_list()
    
    def on_order_select(self, event):
        """Handle order selection from listbox"""
        pass  # Selection is handled by switch_to_order method
    
    def save_current_order_to_memory(self):
        """Save current order to memory"""
        if self.current_order_id:
            self.active_orders[self.current_order_id] = {
                'items': self.order_items.copy(),
                'discount': self.discount,
                'subtotal': self.subtotal,
                'tax': self.tax,
                'total': self.total,
                'customer_name': self.customer_entry.get(),
                'customer_mobile': self.mobile_entry.get(),
                'order_type': self.order_type.get(),
                'table_id': self.current_table_id
            }
    
    def load_order_from_memory(self, order_id):
        """Load order from memory"""
        if order_id not in self.active_orders:
            return
        
        order_data = self.active_orders[order_id]
        self.current_order_id = order_id
        self.order_items = order_data['items'].copy()
        self.discount = order_data['discount']
        self.subtotal = order_data['subtotal']
        self.tax = order_data['tax']
        self.total = order_data['total']
        
        # Update UI
        self.customer_entry.delete(0, tk.END)
        self.customer_entry.insert(0, order_data.get('customer_name', ''))
        self.mobile_entry.delete(0, tk.END)
        self.mobile_entry.insert(0, order_data.get('customer_mobile', ''))
        self.order_type.set(order_data.get('order_type', 'Dine-in'))
        self.current_table_id = order_data.get('table_id')
        
        # Update order items display
        self.order_tree.delete(*self.order_tree.get_children())
        for item in self.order_items:
            self.order_tree.insert("", tk.END, values=(
                item['name'],
                item['quantity'],
                f"₹{item['price']:.2f}",
                f"₹{item['total']:.2f}"
            ))
        
        self.update_totals()
        self.update_orders_list()
    
    def update_orders_list(self):
        """Update orders listbox"""
        self.orders_listbox.delete(0, tk.END)
        
        for order_id, order_data in self.active_orders.items():
            display_text = f"{order_id} - ₹{order_data['total']:.2f} ({order_data.get('order_type', 'Dine-in')})"
            self.orders_listbox.insert(tk.END, display_text)
        
        # Highlight current order
        for i in range(self.orders_listbox.size()):
            order_text = self.orders_listbox.get(i)
            if self.current_order_id and order_text.startswith(self.current_order_id):
                self.orders_listbox.selection_set(i)
                break
    
    def process_payment(self):
        """Process payment with multiple payment options"""
        if not self.order_items:
            messagebox.showwarning("Warning", "No items in order")
            return
        
        # Show payment dialog with multiple options
        payment_dialog = EnhancedPaymentDialog(self.root, self.total, self.payment_methods)
        payment_result = payment_dialog.get_result()
        
        if not payment_result:
            return
        
        payment_method, amount_paid, discount = payment_result
        
        # Apply discount if provided
        if discount > 0:
            self.discount = discount
            self.update_totals()
        
        # Save order with payment information
        self.save_order_with_payment(payment_method, amount_paid)
    
    def save_order_with_payment(self, payment_method, amount_paid):
        """Save order with specific payment method"""
        try:
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
            
            # Create order using dictionary format
            order_data = {
                'order_number': order_number,
                'table_id': table_id,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'order_type': order_type,
                'subtotal': self.subtotal,
                'tax': self.tax,
                'discount': self.discount,
                'total': self.total,
                'items': [{'id': item['menu_item_id'], 'quantity': item['quantity'],
                          'price': item['price'], 'total': item['total']}
                         for item in self.order_items]
            }
            
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
            
            # Add payment with specified method
            self.app.order_model.add_payment(order_id, payment_method, amount_paid)
            
            # Update table status if dine-in
            if order_type == "Dine-in" and table_id:
                self.app.table_model.update_status(table_id, "Occupied")
            
            # Show success message
            messagebox.showinfo("Success", f"Order {order_number} saved successfully!\nPayment: {payment_method} - ₹{amount_paid:.2f}")
            
            # Handle export based on settings
            self._handle_post_payment_export(order_id, False)
            
            # Remove from active orders and clear
            if self.current_order_id in self.active_orders:
                del self.active_orders[self.current_order_id]
            
            self.clear_order()
            
            # Create new order for next transaction
            self.new_order()
            
            # Dispatch events
            event_dispatcher.order_created(order_id)
            event_dispatcher.inventory_updated(None, None)  # Trigger inventory refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")
    
    def cleanup(self):
        """Cleanup resources when screen is destroyed"""
        # Save current order to memory if it has items
        if self.order_items and self.current_order_id:
            self.save_current_order_to_memory()
        
        # Clean up UI components
        if hasattr(self, 'orders_listbox'):
            self.orders_listbox = None
        if hasattr(self, 'order_tree'):
            self.order_tree = None
 

class EnhancedPaymentDialog:
    """Enhanced payment dialog with multiple payment options"""
    
    def __init__(self, parent, total_amount, payment_methods):
        self.result = None
        self.total_amount = total_amount
        self.payment_methods = payment_methods
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Process Payment")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup payment dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title and amount
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(title_frame, text="Payment Processing", 
                 font=('Arial', 16, 'bold')).pack(anchor=tk.W)
        ttk.Label(title_frame, text=f"Total Amount: ₹{self.total_amount:.2f}", 
                 font=('Arial', 14, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        
        # Payment method selection
        method_frame = ttk.LabelFrame(main_frame, text="Payment Method", padding=10)
        method_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.payment_method_var = tk.StringVar(value=self.payment_methods[0])
        
        # Create radio buttons for payment methods
        for i, method in enumerate(self.payment_methods):
            row = i // 2
            col = i % 2
            ttk.Radiobutton(method_frame, text=method, variable=self.payment_method_var, 
                           value=method, command=self.on_payment_method_change).grid(
                row=row, column=col, sticky=tk.W, padx=10, pady=5)
        
        # Amount details
        details_frame = ttk.LabelFrame(main_frame, text="Payment Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Discount
        ttk.Label(details_frame, text="Discount (₹):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.discount_var = tk.StringVar(value="0")
        discount_entry = ttk.Entry(details_frame, textvariable=self.discount_var, width=15)
        discount_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Amount paid
        ttk.Label(details_frame, text="Amount Paid (₹):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.amount_paid_var = tk.StringVar(value=str(self.total_amount))
        amount_paid_entry = ttk.Entry(details_frame, textvariable=self.amount_paid_var, width=15)
        amount_paid_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Balance
        ttk.Label(details_frame, text="Balance (₹):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.balance_label = ttk.Label(details_frame, text="₹0.00", font=('Arial', 10, 'bold'))
        self.balance_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Update calculations when values change
        self.discount_var.trace('w', self.update_calculations)
        self.amount_paid_var.trace('w', self.update_calculations)
        
        # Payment method specific fields
        self.method_fields_frame = ttk.LabelFrame(main_frame, text="Payment Details", padding=10)
        self.method_fields_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Initialize with first payment method
        self.on_payment_method_change()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Process Payment", command=self.process).pack(side=tk.RIGHT)
        
        # Initial calculation
        self.update_calculations()
    
    def on_payment_method_change(self):
        """Handle payment method change"""
        # Clear existing method-specific fields
        for widget in self.method_fields_frame.winfo_children():
            widget.destroy()
        
        method = self.payment_method_var.get()
        
        if method == "Card":
            ttk.Label(self.method_fields_frame, text="Card Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.card_number_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.card_number_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(self.method_fields_frame, text="Expiry:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.expiry_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.expiry_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)
            
        elif method == "UPI":
            ttk.Label(self.method_fields_frame, text="UPI ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.upi_id_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.upi_id_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Wallet":
            ttk.Label(self.method_fields_frame, text="Wallet Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.wallet_number_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.wallet_number_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Credit":
            ttk.Label(self.method_fields_frame, text="Customer Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.credit_customer_var = tk.StringVar()
            ttk.Entry(self.method_fields_frame, textvariable=self.credit_customer_var, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
            
        elif method == "Cash":
            ttk.Label(self.method_fields_frame, text="Cash Received:").grid(row=0, column=0, sticky=tk.W, pady=5)
            self.cash_received_var = tk.StringVar(value=str(self.total_amount))
            ttk.Entry(self.method_fields_frame, textvariable=self.cash_received_var, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
            
            ttk.Label(self.method_fields_frame, text="Change:").grid(row=1, column=0, sticky=tk.W, pady=5)
            self.change_label = ttk.Label(self.method_fields_frame, text="₹0.00", font=('Arial', 10, 'bold'))
            self.change_label.grid(row=1, column=1, sticky=tk.W, pady=5)
    
    def update_calculations(self, *args):
        """Update payment calculations"""
        try:
            discount = float(self.discount_var.get() or 0)
            if discount < 0:
                discount = 0
                self.discount_var.set("0")
            
            if discount > self.total_amount:
                discount = self.total_amount
                self.discount_var.set(str(self.total_amount))
            
            # Update amount paid to total minus discount for cash payments
            if self.payment_method_var.get() == "Cash":
                final_amount = self.total_amount - discount
                self.amount_paid_var.set(str(final_amount))
                
                # Update change calculation
                cash_received = float(self.cash_received_var.get() or 0)
                change = cash_received - final_amount
                self.change_label.config(text=f"₹{change:.2f}")
            
            # Update balance
            amount_paid = float(self.amount_paid_var.get() or 0)
            final_total = self.total_amount - discount
            balance = amount_paid - final_total
            self.balance_label.config(text=f"₹{balance:.2f}")
            
        except ValueError:
            self.balance_label.config(text="Invalid amount")
    
    def process(self):
        """Process payment"""
        try:
            amount_paid = float(self.amount_paid_var.get() or 0)
            discount = float(self.discount_var.get() or 0)
            
            # Validate payment
            if amount_paid < (self.total_amount - discount):
                messagebox.showerror("Error", "Insufficient payment amount")
                return
            
            # Validate payment method specific fields
            method = self.payment_method_var.get()
            if method == "Card":
                if not self.card_number_var.get().strip():
                    messagebox.showerror("Error", "Please enter card number")
                    return
            elif method == "UPI":
                if not self.upi_id_var.get().strip():
                    messagebox.showerror("Error", "Please enter UPI ID")
                    return
            elif method == "Wallet":
                if not self.wallet_number_var.get().strip():
                    messagebox.showerror("Error", "Please enter wallet number")
                    return
            elif method == "Credit":
                if not self.credit_customer_var.get().strip():
                    messagebox.showerror("Error", "Please enter customer name")
                    return
            
            self.result = (method, amount_paid, discount)
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid payment amount")
    
    def cancel(self):
        """Cancel payment"""
        self.dialog.destroy()
    
    def get_result(self):
        """Get payment result"""
        self.dialog.wait_window()
        return self.result