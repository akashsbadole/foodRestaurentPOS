import tkinter as tk
from tkinter import ttk, simpledialog
from .base_ui import BaseUI
from src.utils.constants import *
from src.utils.event_dispatcher import event_dispatcher, EventType

class InventoryScreen(BaseUI):
    """Inventory management screen UI component with modern design"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        
        # Subscribe to events for real-time updates
        event_dispatcher.subscribe(EventType.INVENTORY_UPDATED, self._on_inventory_updated)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern inventory management UI"""
        # Configure modern styles
        self.configure_styles()
        
        # Create main container with padding
        main_container = ttk.Frame(self.app.content_frame, style="Card.TFrame", padding=SPACING_L)
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Header section with title
        self._create_header_section(main_container)
        
        # Search and filter section
        self._create_search_filter_section(main_container)
        
        # Inventory display section
        self._create_inventory_section(main_container)
        
        # Action buttons section
        self._create_action_section(main_container)
        
        # Load inventory data
        self.load_inventory()
    
    def _create_header_section(self, parent):
        """Create the header section with title"""
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Main title
        title_label = self.create_modern_label(
            header_frame, 
            "Inventory Management", 
            style="Title.TLabel"
        )
        title_label.pack(anchor=tk.W)
        
        # Subtitle
        subtitle_label = self.create_modern_label(
            header_frame,
            "Manage stock levels and track inventory status",
            style="Subtitle.TLabel"
        )
        subtitle_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
    
    def _create_search_filter_section(self, parent):
        """Create modern search and filter section"""
        # Search filter card
        search_card = self.create_modern_frame(parent, style="Card.TFrame", padding=SPACING_M)
        search_card.pack(fill=tk.X, pady=SPACING_S)
        
        # Search field
        self.search_field = self.create_form_field(
            search_card,
            "Search Inventory Items",
            "entry",
            style="Modern.TEntry",
            font=(FONT_FAMILY_PRIMARY, 12)
        )
        self.search_field.bind("<KeyRelease>", self.search_inventory)
        
        # Filter combo
        filter_frame = ttk.Frame(search_card, style="Card.TFrame")
        filter_frame.pack(fill=tk.X, pady=(SPACING_S, 0))
        
        filter_label = self.create_modern_label(
            filter_frame,
            "Stock Status Filter",
            style="Body.TLabel"
        )
        filter_label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        
        self.inventory_filter_var = tk.StringVar(value="All")
        self.filter_combo = self.create_modern_combobox(
            filter_frame,
            textvariable=self.inventory_filter_var,
            values=["All", "Low Stock", "Out of Stock"],
            style="Modern.TCombobox",
            state="readonly"
        )
        self.filter_combo.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        self.filter_combo.bind("<<ComboboxSelected>>", self.filter_inventory)
    
    def _create_inventory_section(self, parent):
        """Create modern inventory display section"""
        # Inventory card container
        inventory_card = self.create_modern_frame(parent, style="Card.TFrame", padding=SPACING_M)
        inventory_card.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
        
        # Section title
        section_title = self.create_modern_label(
            inventory_card,
            "Inventory Items",
            style="SectionTitle.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Create modern treeview with shadow effect
        tree_container = ttk.Frame(inventory_card, style="Shadow.TFrame")
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # Inner frame for treeview
        inner_frame = ttk.Frame(tree_container, style="Card.TFrame")
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_XS, pady=SPACING_XS)
        
        # Create modern treeview
        self.inventory_tree, inventory_scrollbar = self.create_modern_treeview(
            inner_frame,
            ("name", "category", "stock", "status"),
            ("Item Name", "Category", "Stock Quantity", "Status"),
            (250, 180, 140, 120)
        )
        self.inventory_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=SPACING_S, pady=SPACING_S)
        
        # Configure row colors for stock status
        self.inventory_tree.tag_configure("out_of_stock", background=COLOR_ERROR_LIGHT)
        self.inventory_tree.tag_configure("low_stock", background=COLOR_WARNING_LIGHT)
        self.inventory_tree.tag_configure("in_stock", background=COLOR_SUCCESS_LIGHT)
        
        # Configure hover effects
        self.inventory_tree.bind("<Motion>", self._on_tree_motion)
        self.inventory_tree.bind("<Leave>", self._on_tree_leave)
    
    def _create_action_section(self, parent):
        """Create modern action buttons section"""
        # Action buttons card
        action_card = self.create_modern_frame(parent, style="Card.TFrame", padding=SPACING_M)
        action_card.pack(fill=tk.X, pady=SPACING_S)
        
        # Create button group with modern styling
        buttons = [
            ("Update Stock", self.update_stock, "Primary.TButton"),
            ("Refresh Inventory", self.load_inventory, "Secondary.TButton"),
            ("Export Data", self.export_inventory, "Success.TButton")
        ]
        
        self.create_button_group(action_card, buttons, spacing=SPACING_M)
    
    def _on_tree_motion(self, event):
        """Handle mouse motion over treeview for hover effects"""
        # Get the item under the cursor
        item = self.inventory_tree.identify_row(event.y)
        if item:
            # Temporarily change background to show hover effect
            tags = self.inventory_tree.item(item)['tags']
            if 'hover' not in tags:
                # Convert tags to list if it's a tuple, then append hover tag
                tags_list = list(tags) if isinstance(tags, tuple) else tags
                tags_list.append('hover')
                self.inventory_tree.item(item, tags=tuple(tags_list))
                self.inventory_tree.tag_configure('hover', background='#e3f2fd')
    
    def _on_tree_leave(self, event):
        """Handle mouse leaving treeview"""
        # Remove all hover tags
        for item in self.inventory_tree.get_children():
            tags = self.inventory_tree.item(item)['tags']
            if 'hover' in tags:
                new_tags = [tag for tag in tags if tag != 'hover']
                self.inventory_tree.item(item, tags=new_tags)
    
    def load_inventory(self, search_term="", filter_type="All"):
        """Load inventory items with modern styling"""
        items = self.app.menu_item_model.get_inventory_items(search_term, filter_type)
        
        # Clear tree
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Add items to tree with proper styling
        for item in items:
            item_id, name, category, stock = item
            
            # Convert stock to integer if it's a string
            try:
                stock_int = int(stock) if isinstance(stock, str) else stock
            except (ValueError, TypeError):
                stock_int = 0
            
            # Determine status and styling
            if stock_int <= 0:
                status = "Out of Stock"
                tag = "out_of_stock"
                status_style = "Error"
            elif stock_int <= 10:
                status = "Low Stock"
                tag = "low_stock"
                status_style = "Warning"
            else:
                status = "In Stock"
                tag = "in_stock"
                status_style = "Success"
            
            # Insert item with tags
            self.inventory_tree.insert("", tk.END, values=(name, category, stock_int, status), tags=(item_id, tag))
        
        # Update status message
        total_items = len(items)
        low_stock_count = 0
        out_of_stock_count = 0
        
        for item in items:
            try:
                stock_val = int(item[3]) if isinstance(item[3], str) else item[3]
                if stock_val <= 10 and stock_val > 0:
                    low_stock_count += 1
                elif stock_val <= 0:
                    out_of_stock_count += 1
            except (ValueError, TypeError):
                out_of_stock_count += 1
        
        status_text = f"Total: {total_items} items"
        if low_stock_count > 0:
            status_text += f" | Low Stock: {low_stock_count}"
        if out_of_stock_count > 0:
            status_text += f" | Out of Stock: {out_of_stock_count}"
        
        # You could update a status label here if needed
    
    def search_inventory(self, event=None):
        """Search inventory items with modern feedback"""
        search_term = self.search_field.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)
    
    def filter_inventory(self, event=None):
        """Filter inventory items with modern feedback"""
        search_term = self.search_field.get()
        filter_type = self.inventory_filter_var.get()
        self.load_inventory(search_term, filter_type)
    
    def update_stock(self):
        """Update stock for selected item with modern dialog"""
        selection = self.inventory_tree.selection()
        if not selection:
            self.show_message("Selection Required", "Please select an item to update stock", "warning")
            return
        
        # Get item details
        item_id = int(self.inventory_tree.item(selection[0])['tags'][0])
        item = self.inventory_tree.item(selection[0])
        item_name = item['values'][0]
        current_stock = item['values'][2]
        
        # Show modern stock update dialog
        dialog = ModernStockUpdateDialog(self.root, item_name, current_stock)
        new_stock = dialog.result
        
        if new_stock is not None:
            # Update stock in database
            self.app.menu_item_model.update_stock(item_id, new_stock)
            
            # Dispatch inventory updated event for real-time updates
            event_dispatcher.inventory_updated(item_id, new_stock)
            
            # Show success message
            self.show_message("Success", f"Stock for '{item_name}' updated to {new_stock} units", "info")
            
            # Refresh inventory display
            self.load_inventory()
    
    def export_inventory(self):
        """Export inventory data (placeholder for future implementation)"""
        self.show_message("Coming Soon", "Inventory export feature will be available in the next update", "info")
    def _on_inventory_updated(self, data):
        """Handle inventory update events for real-time updates"""
        if data and 'item_id' in data:
            # Auto-refresh inventory when stock changes
            self.load_inventory()


class ModernStockUpdateDialog(simpledialog.Dialog):
    """Modern dialog for updating stock levels"""
    
    def __init__(self, parent, item_name, current_stock):
        self.item_name = item_name
        self.current_stock = current_stock
        self.result = None
        super().__init__(parent, title="Update Stock")
    
    def body(self, master):
        """Create dialog body with modern styling"""
        # Configure styles
        style = ttk.Style()
        
        # Main container
        main_frame = ttk.Frame(master, style="Card.TFrame", padding=SPACING_L)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text=f"Update Stock: {self.item_name}",
            font=(FONT_FAMILY_PRIMARY, 16, 'bold'),
            foreground=COLOR_PRIMARY_DARK
        )
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Current stock display
        current_frame = ttk.Frame(main_frame, style="Card.TFrame")
        current_frame.pack(fill=tk.X, pady=SPACING_S)
        
        ttk.Label(
            current_frame,
            text="Current Stock:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_SECONDARY
        ).pack(side=tk.LEFT, padx=(0, SPACING_S))
        
        ttk.Label(
            current_frame,
            text=str(self.current_stock),
            font=(FONT_FAMILY_PRIMARY, 14, 'bold'),
            foreground=COLOR_PRIMARY
        ).pack(side=tk.LEFT)
        
        # New stock entry
        entry_frame = ttk.Frame(main_frame, style="Card.TFrame")
        entry_frame.pack(fill=tk.X, pady=SPACING_M)
        
        ttk.Label(
            entry_frame,
            text="New Stock Quantity:",
            font=(FONT_FAMILY_PRIMARY, 12),
            foreground=COLOR_TEXT_PRIMARY
        ).pack(anchor=tk.W, pady=(0, SPACING_S))
        
        self.stock_entry = ttk.Entry(
            entry_frame,
            font=(FONT_FAMILY_PRIMARY, 12),
            style="Modern.TEntry"
        )
        self.stock_entry.pack(fill=tk.X)
        self.stock_entry.insert(0, str(self.current_stock))
        self.stock_entry.select_range(0, tk.END)
        self.stock_entry.focus()
        
        # Validation label
        self.validation_label = ttk.Label(
            main_frame,
            text="",
            font=(FONT_FAMILY_PRIMARY, 10),
            foreground=COLOR_ERROR
        )
        self.validation_label.pack(anchor=tk.W, pady=(SPACING_XS, 0))
        
        # Bind validation
        self.stock_entry.bind("<KeyRelease>", self.validate_input)
        
        return self.stock_entry
    
    def validate_input(self, event=None):
        """Validate the input"""
        try:
            value = self.stock_entry.get()
            if value:
                stock_value = int(value)
                if stock_value < 0:
                    self.validation_label.config(text="Stock cannot be negative")
                    return False
                else:
                    self.validation_label.config(text="")
                    return True
            else:
                self.validation_label.config(text="")
                return True
        except ValueError:
            self.validation_label.config(text="Please enter a valid number")
            return False
    
    def apply(self):
        """Apply the stock update"""
        try:
            value = self.stock_entry.get()
            if value and self.validate_input():
                self.result = int(value)
            else:
                self.result = None
        except ValueError:
            self.result = None
    
