import tkinter as tk
from tkinter import ttk, simpledialog
from .base_ui import BaseUI

class InventoryScreen(BaseUI):
    """Inventory management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup inventory management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Inventory Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Search frame
        search_frame = ttk.Frame(self.app.content_frame)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.inventory_search_entry = ttk.Entry(search_frame)
        self.inventory_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.inventory_search_entry.bind("<KeyRelease>", self.search_inventory)
        
        ttk.Label(search_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.inventory_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(search_frame, textvariable=self.inventory_filter_var, 
                                  values=["All", "Low Stock", "Out of Stock"], state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.filter_inventory)
        
        # Inventory tree
        inventory_frame = ttk.Frame(self.app.content_frame)
        inventory_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.inventory_tree, inventory_scrollbar = self.create_treeview(
            inventory_frame,
            ("name", "category", "stock", "status"),
            ("Item Name", "Category", "Stock Quantity", "Status"),
            (200, 150, 120, 120)
        )
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons
        buttons_frame = ttk.Frame(self.app.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("Update Stock", self.update_stock),
            ("Refresh", self.load_inventory)
        ])
        
        # Load inventory
        self.load_inventory()
    
    def load_inventory(self, search_term="", filter_type="All"):
        """Load inventory items"""
        items = self.app.menu_item_model.get_inventory_items(search_term, filter_type)
        
        # Clear tree
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, category, stock = item
            
            if stock <= 0:
                status = "Out of Stock"
                tag = "out_of_stock"
            elif stock <= 10:
                status = "Low Stock"
                tag = "low_stock"
            else:
                status = "In Stock"
                tag = "in_stock"
            
            self.inventory_tree.insert("", tk.END, values=(name, category, stock, status), tags=(item_id, tag))
        
        # Configure tags for color coding
        self.inventory_tree.tag_configure("out_of_stock", background="#ffcccc")
        self.inventory_tree.tag_configure("low_stock", background="#ffffcc")
        self.inventory_tree.tag_configure("in_stock", background="#ccffcc")

    def search_inventory(self, event=None):
        """Search inventory items"""
        search_term = self.inventory_search_entry.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)

    def filter_inventory(self, event=None):
        """Filter inventory items"""
        search_term = self.inventory_search_entry.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)

    def update_stock(self):
        """Update stock for selected item"""
        selection = self.inventory_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to update stock", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.inventory_tree.item(selection[0])['tags'][0])
        
        # Get current stock
        item = self.inventory_tree.item(selection[0])
        current_stock = item['values'][2]
        
        # Ask for new stock
        new_stock = self.show_input_dialog("Update Stock", 
                                       f"Enter new stock quantity (Current: {current_stock}):", 
                                       minvalue=0)
        if new_stock is not None:
            # Update stock in database
            self.app.menu_item_model.update_stock(item_id, new_stock)
            
            self.show_message("Success", "Stock updated successfully", "info")
            self.load_inventory()
