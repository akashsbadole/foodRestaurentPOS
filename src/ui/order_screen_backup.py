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
from src.managers.order_manager import OrderManager
import os
import subprocess
# ReportLab imports for PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ReportLab not available: {e}")
    REPORTLAB_AVAILABLE = False
    # Fallback imports for compatibility
    A4 = None
    mm = None
    SimpleDocTemplate = None

class OrderScreen(BaseUI):
    """New Order Screen for creating and managing multiple orders"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.root = root
        self.app = app
        self.db = app.db  # Add database reference
        
        # Initialize order manager
        self.order_manager = OrderManager()
        
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
        if REPORTLAB_AVAILABLE:
            self.pdf_exporter = PDFExporter({
                'name': self.app.settings.get('restaurant_name', DEFAULT_RESTAURANT_NAME),
                'address': self.app.settings.get('restaurant_address', DEFAULT_RESTAURANT_ADDRESS),
                'phone': self.app.settings.get('restaurant_phone', ''),
                'email': self.app.settings.get('restaurant_email', ''),
                'gst_number': self.app.settings.get('gst_number', '')
            })
        else:
            self.pdf_exporter = None
            print("Warning: PDF export functionality disabled due to missing ReportLab")
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
        # Tab-based interface components
        self.order_notebook = None
        self.order_frames = {}  # {order_id: frame}
        self.order_trees = {}  # {order_id: tree}
        
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
        
        # Configure styles for browser-style tabs
        style = ttk.Style()
        style.configure('Tab.TButton',
                     font=('Arial', 9),
                     padding=(8, 4),
                     relief='flat')
        style.configure('ActiveTab.TButton',
                     font=('Arial', 9, 'bold'),
                     padding=(8, 4),
                     relief='flat',
                     background='#0078d7')
        style.configure('CloseTab.TButton',
                     font=('Arial', 8),
                     padding=(2, 2),
                     relief='flat',
                     foreground='#666666')
        style.configure('Accent.TButton',
                     font=('Arial', 9, 'bold'),
                     padding=(8, 4),
                     relief='flat',
                     background='#28a745',
                     foreground='white')
        
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
        self.customer_entry.bind("<KeyRelease>", self.on_customer_info_changed)
        
        ttk.Label(info_frame, text="Mobile:").grid(row=0, column=5, sticky=tk.W, padx=5)
        self.mobile_entry = ttk.Entry(info_frame, width=15)
        self.mobile_entry.grid(row=0, column=6, padx=5)
        self.mobile_entry.bind("<KeyRelease>", self.on_customer_info_changed)
        
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
        
        # Browser-style tab bar
        self.tab_bar_frame = ttk.Frame(self.content_frame)
        self.tab_bar_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # New Order button (always visible)
        self.new_order_btn = ttk.Button(
            self.tab_bar_frame,
            text="+ New Order",
            command=self.new_order,
            style='Accent.TButton'
        )
        self.new_order_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Tab container for order tabs
        self.tabs_container = ttk.Frame(self.tab_bar_frame)
        self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Order management buttons frame
        order_mgmt_frame = ttk.Frame(self.tab_bar_frame)
        order_mgmt_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(order_mgmt_frame, text="Clear Order", command=self.clear_current_order).pack(side=tk.LEFT, padx=2)
        
        # Tab-based order management - Main order display area
        orders_frame = ttk.LabelFrame(self.content_frame, text="Active Orders", padding=10)
        # FIXED: Don't use expand=True to prevent it from taking all space
        orders_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # Create notebook for tabs - This is the main interface
        self.order_notebook = ttk.Notebook(orders_frame)
        self.order_notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        self.order_notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Order info display
        order_info_frame = ttk.Frame(orders_frame)
        order_info_frame.pack(fill=tk.X, pady=5)
        
        self.order_info_label = ttk.Label(order_info_frame, text="No active orders",
                                       font=('Arial', 10, 'bold'), foreground='gray')
        self.order_info_label.pack(anchor=tk.W)
        
        # Status legend
        status_legend_frame = ttk.Frame(orders_frame)
        status_legend_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_legend_frame, text="Status:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(status_legend_frame, text="New", foreground='#808080').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(status_legend_frame, text="In Progress", foreground='#FFA500').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(status_legend_frame, text="Ready", foreground='#008000').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(status_legend_frame, text="Completed", foreground='#0000FF').pack(side=tk.LEFT, padx=(0, 10))
        
        # Order summary and buttons frame
        summary_container = ttk.Frame(self.content_frame)
        # FIXED: Ensure summary container is packed after orders_frame and doesn't get hidden
        summary_container.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Summary labels frame
        summary_frame = ttk.Frame(summary_container)
        summary_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.subtotal_label = ttk.Label(summary_frame, text="Subtotal: Rs.0.00", font=('Arial', 10))
        self.subtotal_label.pack(anchor=tk.W, pady=2)
        
        # GST breakdown
        self.cgst_label = ttk.Label(summary_frame, text="CGST (2.5%): Rs.0.00", font=('Arial', 9))
        self.cgst_label.pack(anchor=tk.W, pady=1)
        
        self.sgst_label = ttk.Label(summary_frame, text="SGST (2.5%): Rs.0.00", font=('Arial', 9))
        self.sgst_label.pack(anchor=tk.W, pady=1)
        
        self.tax_label = ttk.Label(summary_frame, text="Total Tax: Rs.0.00", font=('Arial', 10))
        self.tax_label.pack(anchor=tk.W, pady=2)
        
        self.discount_label = ttk.Label(summary_frame, text="Discount: Rs.0.00", font=('Arial', 10))
        self.discount_label.pack(anchor=tk.W, pady=2)
        
        self.total_label = ttk.Label(summary_frame, text="Total: Rs.0.00", font=('Arial', 12, 'bold'))
        self.total_label.pack(anchor=tk.W, pady=2)
        
        # Buttons frame
        buttons_frame = ttk.Frame(summary_container)
        buttons_frame.pack(side=tk.RIGHT, padx=10)
        
        self.payment_btn = ttk.Button(buttons_frame, text="PROCESS PAYMENT", command=self.process_payment, style='Accent.TButton')
        self.payment_btn.pack(pady=2)
        
        ttk.Button(buttons_frame, text="Apply Discount", command=self.apply_discount).pack(pady=2)
        
        # Export buttons
        ttk.Separator(buttons_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        ttk.Button(buttons_frame, text="Export Order", command=self.export_order).pack(pady=2)
        
        # Create legacy treeview for compatibility (hidden)
        items_frame = ttk.Frame(self.content_frame)
        # Don't pack this frame - it's just for compatibility
        self.order_tree, scrollbar = self.create_treeview(
            items_frame,
            ("name", "quantity", "price", "total"),
            ("Item", "Quantity", "Price", "Total"),
            (200, 80, 100, 100)
        )
        # Right click menu for order items (legacy - redirects to current tab)
        self.order_tree.bind("<Button-3>", self.show_item_context_menu)
        
        # Initialize first order after all UI components are created
        self.initialize_orders()
        
    def on_table_changed(self, event=None):
        """Handle table selection change"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            table_selection = self.table_combo.get()
            table_id = None
            
            if table_selection:
                table_number = table_selection.split(" ")[1]
                tables = self.app.table_model.get_all()
                for table in tables:
                    if str(table[1]) == table_number:
                        table_id = table[0]
                        break
            
            # Update table in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                table_id=table_id
            )
            self.current_table_id = table_id
            self.refresh_orders_list()
    def on_customer_info_changed(self, event=None):
        """Handle customer information changes"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            # Update customer info in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                customer_name=self.customer_entry.get().strip(),
                customer_mobile=self.mobile_entry.get().strip()
            )
            self.refresh_orders_list()
    
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
        current_order = self.order_manager.get_current_order()
        if current_order:
            # Update order type in order manager
            self.order_manager.update_order_info(
                self.order_manager.current_order_id,
                order_type=self.order_type.get()
            )
            self.refresh_orders_list()
        
        if self.order_type.get() == "Dine-in":
            self.table_frame.pack(fill=tk.X, padx=10, pady=5, before=self.content_frame.winfo_children()[2])
        else:
            self.table_frame.pack_forget()
    
    def add_item(self):
        """Add item to current order"""
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
            
            # Get current order
            current_order = self.order_manager.get_current_order()
            if not current_order:
                messagebox.showerror("Error", "No active order. Please create a new order first.")
                return
            
            # Add item to order using order manager
            item_data = {
                'menu_item_id': menu_item_id,
                'name': item_name,
                'quantity': quantity,
                'price': price,
                'total': price * quantity
            }
            
            success = self.order_manager.add_item_to_order(
                self.order_manager.current_order_id,
                item_data
            )
            
            if success:
                # Refresh display
                self.refresh_order_display(self.order_manager.current_order_id)
                # Update tab
                self.update_order_tab(self.order_manager.current_order_id)
                # Update totals
                self.update_totals_from_order_manager()
                # Reset selection
                self.quantity_var.set("1")
            else:
                messagebox.showerror("Error", "Failed to add item to order")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {e}")
            print(f"Add item error details: {e}")
    
    def show_item_context_menu(self, event):
        """Show context menu for order items (legacy - redirects to current tab)"""
        if self.order_manager.current_order_id in self.order_trees:
            tree = self.order_trees[self.order_manager.current_order_id]
            selection = tree.selection()
            if selection:
                context_menu = tk.Menu(self.root, tearoff=0)
                context_menu.add_command(
                    label="Remove Item",
                    command=lambda: self.remove_item_from_tab(self.order_manager.current_order_id, selection[0])
                )
                context_menu.post(event.x_root, event.y_root)
    
    def remove_item(self, item_id):
        """Legacy method - redirects to tab-based removal"""
        if self.order_manager.current_order_id in self.order_trees:
            tree = self.order_trees[self.order_manager.current_order_id]
            selection = tree.selection()
            if selection:
                self.remove_item_from_tab(self.order_manager.current_order_id, selection[0])
        else:
            messagebox.showwarning("Warning", "Please select an item to remove")
    
    def update_totals_from_order_manager(self):
        """Update order totals from order manager"""
        try:
            current_order = self.order_manager.get_current_order()
            if current_order:
                self.subtotal = current_order['subtotal']
                self.cgst_amount = current_order.get('cgst_amount', 0.0)
                self.sgst_amount = current_order.get('sgst_amount', 0.0)
                self.tax = current_order['tax']
                self.discount = current_order['discount']
                self.total = current_order['total']
                
                # FIXED: Sync legacy order_items with order manager data
                self.order_items = current_order['items'].copy()
            else:
                self.subtotal = 0.0
                self.cgst_amount = 0.0
                self.sgst_amount = 0.0
                self.tax = 0.0
                self.discount = 0.0
                self.total = 0.0
                # FIXED: Clear legacy order_items when no current order
                self.order_items = []
            
            # Update labels - FIXED: Use Rs. instead of ₹ to avoid encoding issues
            self.subtotal_label.config(text=f"Subtotal: Rs.{self.subtotal:.2f}")
            self.cgst_label.config(text=f"CGST (2.5%): Rs.{self.cgst_amount:.2f}")
            self.sgst_label.config(text=f"SGST (2.5%): Rs.{self.sgst_amount:.2f}")
            self.tax_label.config(text=f"Total Tax: Rs.{self.tax:.2f}")
            self.discount_label.config(text=f"Discount: Rs.{self.discount:.2f}")
            self.total_label.config(text=f"Total: Rs.{self.total:.2f}")
            
            # Update payment button state based on order items
            if hasattr(self, 'payment_btn'):
                if current_order and current_order['items']:
                    self.payment_btn.config(state='normal')
                else:
                    self.payment_btn.config(state='disabled')
            
        except Exception as e:
            print(f"Error updating totals: {e}")
            # Reset to zero if there's an error
            self.subtotal = 0.0
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
            self.tax = 0.0
            self.total = 0.0
            self.discount = 0.0
            self.order_items = []
            # FIXED: Use Rs. instead of ₹ to avoid encoding issues
            self.subtotal_label.config(text="Subtotal: Rs.0.00")
            self.cgst_label.config(text="CGST (2.5%): Rs.0.00")
            self.sgst_label.config(text="SGST (2.5%): Rs.0.00")
            self.tax_label.config(text="Total Tax: Rs.0.00")
            self.discount_label.config(text="Discount: Rs.0.00")
            self.total_label.config(text="Total: Rs.0.00")
    
    def apply_discount(self):
        """Apply discount to current order"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            messagebox.showwarning("Warning", "No active order")
            return
            
        try:
            discount_str = simpledialog.askstring("Discount", "Enter discount amount:")
            if discount_str:
                discount = float(discount_str)
                if discount < 0:
                    raise ValueError("Discount cannot be negative")
                if discount > current_order['subtotal']:
                    raise ValueError("Discount cannot exceed subtotal")
                
                # Update discount using order manager
                self.order_manager.update_order_info(
                    self.order_manager.current_order_id,
                    discount=discount
                )
                
                # Update display
                self.update_totals_from_order_manager()
                self.update_order_tab(self.order_manager.current_order_id)
                self.refresh_orders_list()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid discount: {e}")
    
    def clear_order(self):
        """Clear current order (legacy method - redirects to clear_current_order)"""
        self.clear_current_order()
    
    def clear_current_order(self):
        """Clear current active order"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return
            
        if messagebox.askyesno("Confirm", "Clear current order?"):
            success = self.order_manager.clear_order(self.order_manager.current_order_id)
            if success:
                self.refresh_order_display(self.order_manager.current_order_id)
                self.update_order_tab(self.order_manager.current_order_id)
                self.update_totals_from_order_manager()
    
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
        current_order = self.order_manager.get_current_order()
        if not current_order or not current_order['items']:
            messagebox.showwarning("Warning", "No items in order to export")
            return
        
        # Prepare order data for export
        order_data = self.order_manager.get_order_for_export(self.order_manager.current_order_id)
        
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
        """Prepare order data for export from current order (legacy method)"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            return None
            
        # Get table number if dine-in
        table_number = None
        if current_order['order_type'] == "Dine-in" and current_order['table_id']:
            tables = self.app.table_model.get_all()
            for table in tables:
                if table[0] == current_order['table_id']:
                    table_number = table[1]
                    break
        
        return {
            'order_number': current_order['order_number'],
            'table_number': table_number,
            'customer_name': current_order['customer_name'],
            'customer_mobile': current_order['customer_mobile'],
            'order_type': current_order['order_type'],
            'status': current_order['status'],
            'subtotal': current_order['subtotal'],
            'tax': current_order['tax'],
            'discount': current_order['discount'],
            'total': current_order['total'],
            'tax_rate': float(self.app.settings.get('tax_rate', DEFAULT_TAX_RATE)),
            'items': [(item['name'], item['quantity'], item['price'], item['total'])
                     for item in current_order['items']],
            'payments': [('Cash', current_order['total'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'))],
            'created_at': current_order['created_at'].strftime('%Y-%m-%d %H:%M:%S')
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
            # Check if ReportLab is available
            if self.pdf_exporter is None:
                return False, "ReportLab library is not installed"
            
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
                if self.pdf_exporter is None:
                    print(f"Cannot auto-export order {order_id} to PDF: ReportLab library is not installed")
                    return
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
                if self.pdf_exporter is None:
                    print(f"Cannot auto-export order {order_id} to PDF: ReportLab library is not installed")
                    pdf_success = False
                    pdf_result = "ReportLab not available"
                else:
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
    
    def initialize_orders(self):
        """Initialize order manager and create first order"""
        # Create initial order
        order_id = self.order_manager.create_new_order(self.order_type.get())
        self.order_manager.switch_to_order(order_id)
        
        # Create tab for this order
        self.create_order_tab(order_id)
        
        # Update display
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
    
    def create_browser_tab(self, order_id: str):
        """Create a browser-style tab for an order"""
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Create tab frame container
        tab_container = ttk.Frame(self.tabs_container)
        tab_container.pack(side=tk.LEFT, padx=(0, 2))
        
        # Tab button with order info
        status_display = order.get('status_display', 'Unknown')
        tab_text = f"{order['order_number']}"
        tab_btn = ttk.Button(
            tab_container,
            text=tab_text,
            command=lambda: self.switch_to_order_tab(order_id),
            style='Tab.TButton'
        )
        tab_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Close button
        close_btn = ttk.Button(
            tab_container,
            text="✕",
            command=lambda: self.close_order_tab(order_id),
            width=3,
            style='CloseTab.TButton'
        )
        close_btn.pack(side=tk.LEFT)
        
        # Store tab references
        if not hasattr(self, 'browser_tabs'):
            self.browser_tabs = {}
        self.browser_tabs[order_id] = {
            'container': tab_container,
            'button': tab_btn,
            'close_btn': close_btn
        }
        
        # Create notebook tab frame (hidden from user)
        tab_frame = ttk.Frame(self.order_notebook)
        self.order_frames[order_id] = tab_frame
        
        # Create treeview for this order
        order_tree, scrollbar = self.create_treeview(
            tab_frame,
            ("name", "quantity", "price", "total"),
            ("Item", "Quantity", "Price", "Total"),
            (200, 80, 100, 100)
        )
        order_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.order_trees[order_id] = order_tree
        
        # Right click menu for order items
        order_tree.bind("<Button-3>", lambda e: self.show_item_context_menu_for_tab(e, order_id))
        
        # Add tab to notebook (hidden)
        self.order_notebook.add(tab_frame, text=tab_text)
        
        # Update tab appearance
        self.update_browser_tab_appearance(order_id)
        
        return tab_frame
    
    def create_order_tab(self, order_id: str):
        """Create a tab for an order (redirects to browser tab)"""
        return self.create_browser_tab(order_id)
    
    def switch_to_order_tab(self, order_id: str):
        """Switch to a specific order tab"""
        if order_id not in self.order_frames:
            return
        
        # Switch to this order in order manager
        self.order_manager.switch_to_order(order_id)
        
        # Find and select the notebook tab
        for i in range(self.order_notebook.index("end")):
            if self.order_notebook.tabs()[i] == self.order_frames[order_id]:
                self.order_notebook.select(i)
                break
        
        # Update display
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # Update tab appearance to show active state
        self.update_browser_tab_appearance(order_id)
    
    def close_order_tab(self, order_id: str):
        """Close an order tab with confirmation"""
        if order_id not in self.order_frames:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Check if order has items and ask for confirmation
        if order['items']:
            if not messagebox.askyesno(
                "Confirm Close",
                f"Order {order['order_number']} has items. Close anyway?"
            ):
                return
        
        # Remove browser tab
        if hasattr(self, 'browser_tabs') and order_id in self.browser_tabs:
            self.browser_tabs[order_id]['container'].destroy()
            del self.browser_tabs[order_id]
        
        # Remove notebook tab
        self.remove_order_tab(order_id)
        
        # Delete from order manager
        self.order_manager.delete_order(order_id)
        
        # Refresh displays
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # If no orders left, create a new one
        if not self.order_manager.get_order_ids():
            self.new_order()
    
    def update_browser_tab_appearance(self, order_id: str):
        """Update the appearance of browser-style tab"""
        if not hasattr(self, 'browser_tabs') or order_id not in self.browser_tabs:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        tab_info = self.browser_tabs[order_id]
        is_current = order_id == self.order_manager.current_order_id
        
        # Update button text with item count
        item_count = len(order['items'])
        tab_text = f"{order['order_number']}"
        if item_count > 0:
            tab_text += f" ({item_count})"
        
        tab_info['button'].config(text=tab_text)
        
        # Update button style based on active state
        if is_current:
            tab_info['button'].config(style='ActiveTab.TButton')
        else:
            tab_info['button'].config(style='Tab.TButton')
    
    def update_order_tab(self, order_id: str):
        """Update order tab title and appearance (redirects to browser tab update)"""
        self.update_browser_tab_appearance(order_id)
    
    def remove_order_tab(self, order_id: str):
        """Remove a tab for an order"""
        if order_id not in self.order_frames:
            return
        
        # Remove browser tab if it exists
        if hasattr(self, 'browser_tabs') and order_id in self.browser_tabs:
            self.browser_tabs[order_id]['container'].destroy()
            del self.browser_tabs[order_id]
        
        # Find and remove notebook tab
        for i in range(self.order_notebook.index("end")):
            if self.order_notebook.tabs()[i] == self.order_frames[order_id]:
                self.order_notebook.forget(i)
                break
        
        # Clean up references
        del self.order_frames[order_id]
        del self.order_trees[order_id]
    
    def on_tab_changed(self, event=None):
        """Handle tab change event"""
        if not self.order_notebook.tabs():
            return
        
        # Get selected tab
        selected_tab = self.order_notebook.select()
        if not selected_tab:
            return
        
        # Find order ID for this tab
        for order_id, frame in self.order_frames.items():
            if frame == selected_tab:
                # Switch to this order in order manager
                self.order_manager.switch_to_order(order_id)
                # Update display
                self.refresh_current_order_display()
                self.update_totals_from_order_manager()
                break
    
    def show_item_context_menu_for_tab(self, event, order_id: str):
        """Show context menu for order items in specific tab"""
        if order_id not in self.order_trees:
            return
        
        tree = self.order_trees[order_id]
        selection = tree.selection()
        if selection:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="Remove Item",
                command=lambda: self.remove_item_from_tab(order_id, selection[0])
            )
            context_menu.post(event.x_root, event.y_root)
    
    def remove_item_from_tab(self, order_id: str, item_id):
        """Remove item from specific order tab"""
        if order_id not in self.order_trees:
            return
        
        tree = self.order_trees[order_id]
        selected_index = tree.index(item_id)
        
        # Remove item using order manager
        success = self.order_manager.remove_item_from_order(order_id, selected_index)
        
        if success:
            # Refresh displays
            self.refresh_order_display(order_id)
            self.update_totals_from_order_manager()
            self.update_order_tab(order_id)
        else:
            messagebox.showerror("Error", "Failed to remove item")
    
    def refresh_order_display(self, order_id: str = None):
        """Refresh display for specific order or current order"""
        if order_id is None:
            order_id = self.order_manager.current_order_id
        
        if order_id is None:
            return
        
        order = self.order_manager.get_order(order_id)
        if not order:
            return
        
        # Update tree for this order
        if order_id in self.order_trees:
            tree = self.order_trees[order_id]
            tree.delete(*tree.get_children())
            for item in order['items']:
                tree.insert("", tk.END, values=(
                    item['name'],
                    item['quantity'],
                    f"₹{item['price']:.2f}",
                    f"₹{item['total']:.2f}"
                ))
        
        # Update main UI fields if this is current order
        if order_id == self.order_manager.current_order_id:
            self.customer_entry.delete(0, tk.END)
            self.customer_entry.insert(0, order.get('customer_name', ''))
            self.mobile_entry.delete(0, tk.END)
            self.mobile_entry.insert(0, order.get('customer_mobile', ''))
            self.order_type.set(order.get('order_type', 'Dine-in'))
            self.current_table_id = order.get('table_id')
    
    def new_order(self):
        """Create a new order"""
        current_order = self.order_manager.get_current_order()
        
        # Check if current order has items and ask to save
        if current_order and self.order_manager.has_items(self.order_manager.current_order_id):
            if not messagebox.askyesno("Save Order",
                "Current order has items. Save before creating new order?"):
                return
        
        # Create new order
        order_id = self.order_manager.create_new_order(self.order_type.get())
        self.order_manager.switch_to_order(order_id)
        
        # Create browser-style tab for new order
        self.create_browser_tab(order_id)
        
        # Switch to new tab
        self.switch_to_order_tab(order_id)
        
        # Update display
        self.refresh_orders_list()
        self.refresh_current_order_display()
        self.update_totals_from_order_manager()
        
        # Update UI fields for new order
        self.customer_entry.delete(0, tk.END)
        self.mobile_entry.delete(0, tk.END)
    
    def delete_current_tab_order(self):
        """Delete the order in the current tab"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            messagebox.showwarning("Warning", "No active order to delete")
            return
        
        order_id = self.order_manager.current_order_id
        order_number = current_order['order_number']
        
        if messagebox.askyesno("Confirm Delete", f"Delete order {order_number}?"):
            if self.order_manager.delete_order(order_id):
                # Remove tab
                self.remove_order_tab(order_id)
                
                # Refresh displays
                self.refresh_orders_list()
                self.refresh_current_order_display()
                self.update_totals_from_order_manager()
            else:
                messagebox.showerror("Error", "Failed to delete order")
    
    def delete_order(self):
        """Legacy method - redirects to delete_current_tab_order"""
        self.delete_current_tab_order()
    
    def on_order_select(self, event):
        """Legacy method - no longer needed with tab interface"""
        pass
    
    def update_order_info_display(self):
        """Update order information display"""
        current_order = self.order_manager.get_current_order()
        if current_order:
            status_display = current_order.get('status_display', 'Unknown')
            info_text = f"Current: {current_order['order_number']} | "
            info_text += f"Items: {len(current_order['items'])} | "
            info_text += f"Total: ₹{current_order['total']:.2f} | "
            info_text += f"Status: {status_display}"
            self.order_info_label.config(text=info_text)
        else:
            self.order_info_label.config(text="No active orders")
    
    def refresh_current_order_display(self):
        """Refresh the current order display"""
        current_order = self.order_manager.get_current_order()
        if not current_order:
            # Clear display
            self.order_tree.delete(*self.order_tree.get_children())
            self.customer_entry.delete(0, tk.END)
            self.mobile_entry.delete(0, tk.END)
            return
        
        # Update UI fields
        self.customer_entry.delete(0, tk.END)
        self.customer_entry.insert(0, current_order.get('customer_name', ''))
        self.mobile_entry.delete(0, tk.END)
        self.mobile_entry.insert(0, current_order.get('customer_mobile', ''))
        self.order_type.set(current_order.get('order_type', 'Dine-in'))
        self.current_table_id = current_order.get('table_id')
        
        # Update order items display
        self.order_tree.delete(*self.order_tree.get_children())
        for item in current_order['items']:
            self.order_tree.insert("", tk.END, values=(
                item['name'],
                item['quantity'],
                f"₹{item['price']:.2f}",
                f"₹{item['total']:.2f}"
            ))
    
    def refresh_orders_list(self):
        """Update orders display with current orders"""
        # Update order info display
        self.update_order_info_display()
        
        # Get orders summary
        orders_summary = self.order_manager.get_orders_summary()
        
        # Update status
        if orders_summary:
            total_value = self.order_manager.get_total_value_all_orders()
            if hasattr(self.app, 'status_bar') and self.app.status_bar:
                self.app.status_bar.config(text=f"Active Orders: {len(orders_summary)} | Total Value: ₹{total_value:.2f}")
        else:
            if hasattr(self.app, 'status_bar') and self.app.status_bar:
                self.app.status_bar.config(text="No active orders")
    
    def process_payment(self):
        """Process payment with multiple payment options"""
        print(f"[DEBUG] process_payment called")
        print(f"[DEBUG] self.order_items: {self.order_items}")
        current_order = self.order_manager.get_current_order()
        print(f"[DEBUG] current_order from manager: {current_order}")
        
        # Check both legacy and new order systems
        has_legacy_items = bool(self.order_items)
        has_manager_items = current_order and bool(current_order.get('items', []))
        print(f"[DEBUG] has_legacy_items: {has_legacy_items}, has_manager_items: {has_manager_items}")
        
        # FIXED: Check order manager items instead of legacy order_items
        if not has_manager_items:
            print("[DEBUG] No items in order manager")
            messagebox.showwarning("Warning", "No items in order")
            return
        
        # FIXED: Use current order total from order manager instead of legacy self.total
        total_amount = current_order['total'] if current_order else 0.0
        print(f"[DEBUG] Using total from order manager: ₹{total_amount}")
        
        # Show payment dialog with multiple options
        payment_dialog = EnhancedPaymentDialog(self.root, total_amount, self.payment_methods)
        payment_result = payment_dialog.get_result()
        
        if not payment_result:
            return
        
        payment_method, amount_paid, discount = payment_result
        
        # Apply discount if provided
        if discount > 0:
            self.discount = discount
            self.update_totals_from_order_manager()
        
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
            self.clear_order()
            
            # Create new order for next transaction
            self.new_order()
            
            # Dispatch events
            event_dispatcher.order_created(order_id)
            event_dispatcher.inventory_updated(None, None)  # Trigger inventory refresh
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save order: {e}")
    
    def load_tables(self):
        """Load available tables from database"""
        try:
            # Get available tables from database
            tables = self.app.table_model.get_available()
            
            # Format table options for combobox
            table_options = []
            for table in tables:
                table_id, table_number = table
                table_options.append(f"Table {table_number}")
            
            # Update combobox with table options
            self.table_combo['values'] = table_options
            
            # Select first table if available
            if table_options:
                self.table_combo.current(0)
                # Set table ID for first table
                first_table_id = tables[0][0]
                self.current_table_id = first_table_id
            else:
                self.current_table_id = None
                
        except Exception as e:
            print(f"Error loading tables: {e}")
            messagebox.showerror("Error", f"Failed to load tables: {e}")
    
    def cleanup(self):
        """Cleanup resources when screen is destroyed"""
        # Save current order to memory if it has items
        if self.order_items and self.current_order_id:
            pass  # Order is already managed by OrderManager
        
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
        ttk.Label(title_frame, text=f"Total Amount: Rs.{self.total_amount:.2f}",
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
