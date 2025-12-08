import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from .base_ui import BaseUI

class MenuScreen(BaseUI):
    """Menu management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup menu management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Menu Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create menu frame
        menu_frame = ttk.Frame(self.app.content_frame)
        menu_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Menu items
        left_panel = ttk.Frame(menu_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Search and filter
        search_frame = ttk.Frame(left_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_menu_items)
        
        ttk.Label(search_frame, text="Category:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, state="readonly")
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu_items)
        
        # Menu items treeview
        self.menu_items_tree, menu_scrollbar = self.create_treeview(
            left_panel, 
            ("name", "category", "price", "stock"), 
            ("Name", "Category", "Price", "Stock"),
            (200, 150, 100, 100)
        )
        self.menu_items_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("Add Item", self.add_menu_item),
            ("Edit Item", self.edit_menu_item),
            ("Delete Item", self.delete_menu_item)
        ])
        
        # Right panel - Categories
        right_panel = ttk.Frame(menu_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Categories frame
        categories_frame = ttk.LabelFrame(right_panel, text="Categories", padding=10)
        categories_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Categories tree
        self.categories_tree, categories_scrollbar = self.create_treeview(
            categories_frame,
            ("name",),
            ("Name",),
            (200,)
        )
        self.categories_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Category buttons
        category_buttons_frame = ttk.Frame(categories_frame)
        category_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.create_button_frame(category_buttons_frame, [
            ("Add Category", self.add_category),
            ("Edit Category", self.edit_category),
            ("Delete Category", self.delete_category)
        ])
        
        # Load initial data
        self.load_menu_categories()
        self.load_menu_items_management()
    
    def load_menu_categories(self):
        """Load menu categories"""
        categories = self.app.category_model.get_all()
        
        # Clear categories tree
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)
        
        # Add categories to tree
        for category in categories:
            self.categories_tree.insert("", tk.END, values=(category[1],), tags=(category[0],))
        
        # Update category combo
        category_list = ["All"] + [category[1] for category in categories]
        self.category_combo['values'] = category_list
        self.category_combo.current(0)
    
    def load_menu_items_management(self, search_term="", category="All"):
        """Load menu items for menu management screen"""
        items = self.app.menu_item_model.get_all(search_term, category)
        
        # Clear menu items tree
        for item in self.menu_items_tree.get_children():
            self.menu_items_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, name, category, price, stock = item
            self.menu_items_tree.insert("", tk.END, values=(
                name,
                category,
                f"₹{price:.2f}",
                stock
            ), tags=(item_id,))
    
    def search_menu_items(self, event=None):
        """Search menu items"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items_management(search_term, category)
    
    def filter_menu_items(self, event=None):
        """Filter menu items by category"""
        search_term = self.search_entry.get()
        category = self.category_var.get()
        self.load_menu_items_management(search_term, category)
    
    def add_menu_item(self):
        """Add a new menu item"""
        # Create add item window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add Menu Item")
        add_window.geometry("400x400")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, state="readonly", width=28)
        category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Load categories
        categories = self.app.category_model.get_all()
        category_list = [category[1] for category in categories]
        category_combo['values'] = category_list
        if category_list:
            category_combo.current(0)
        
        # Price
        ttk.Label(form_frame, text="Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Stock
        ttk.Label(form_frame, text="Stock Quantity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_entry = ttk.Entry(form_frame, width=30)
        stock_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Image path
        ttk.Label(form_frame, text="Image Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
        image_path_var = tk.StringVar()
        image_path_entry = ttk.Entry(form_frame, textvariable=image_path_var, width=30)
        image_path_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")]
            )
            if file_path:
                image_path_var.set(file_path)
        
        ttk.Button(form_frame, text="Browse", command=browse_image).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        def save_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            
            if not name or not category or not price or not stock:
                self.show_message("Warning", "Please fill in all required fields", "warning")
                return
            
            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                self.show_message("Warning", "Price must be a number and Stock must be an integer", "warning")
                return
            
            # Get category ID
            categories = self.app.category_model.get_all()
            category_id = None
            for cat in categories:
                if cat[1] == category:
                    category_id = cat[0]
                    break
            
            if not category_id:
                self.show_message("Warning", "Invalid category", "warning")
                return
            
            # Insert menu item
            self.app.menu_item_model.add(name, price, category_id, stock, image_path)
            
            self.show_message("Success", "Menu item added successfully", "info")
            add_window.destroy()
            self.load_menu_items_management()
        
        self.create_button_frame(buttons_frame, [
            ("Save", save_item),
            ("Cancel", add_window.destroy)
        ])
    
    def edit_menu_item(self):
        """Edit selected menu item"""
        selection = self.menu_items_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to edit", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.menu_items_tree.item(selection[0])['tags'][0])
        
        # Get item details
        item_details = self.app.menu_item_model.get_by_id(item_id)
        if not item_details:
            return
        
        name, price, category_id, stock, image_path, category_name = item_details
        
        # Create edit item window
        edit_window = tk.Toplevel(self.app.root)
        edit_window.title("Edit Menu Item")
        edit_window.geometry("400x400")
        
        # Create form
        form_frame = ttk.Frame(edit_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        name_entry.insert(0, name)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar(value=category_name)
        category_combo = ttk.Combobox(form_frame, textvariable=category_var, state="readonly", width=28)
        category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Load categories
        categories = self.app.category_model.get_all()
        category_list = [category[1] for category in categories]
        category_combo['values'] = category_list
        
        # Price
        ttk.Label(form_frame, text="Price:").grid(row=2, column=0, sticky=tk.W, pady=5)
        price_entry = ttk.Entry(form_frame, width=30)
        price_entry.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        price_entry.insert(0, str(price))
        
        # Stock
        ttk.Label(form_frame, text="Stock Quantity:").grid(row=3, column=0, sticky=tk.W, pady=5)
        stock_entry = ttk.Entry(form_frame, width=30)
        stock_entry.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        stock_entry.insert(0, str(stock))
        
        # Image path
        ttk.Label(form_frame, text="Image Path:").grid(row=4, column=0, sticky=tk.W, pady=5)
        image_path_var = tk.StringVar(value=image_path or "")
        image_path_entry = ttk.Entry(form_frame, textvariable=image_path_var, width=30)
        image_path_entry.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")]
            )
            if file_path:
                image_path_var.set(file_path)
        
        ttk.Button(form_frame, text="Browse", command=browse_image).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        def update_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            
            if not name or not category or not price or not stock:
                self.show_message("Warning", "Please fill in all required fields", "warning")
                return
            
            try:
                price = float(price)
                stock = int(stock)
            except ValueError:
                self.show_message("Warning", "Price must be a number and Stock must be an integer", "warning")
                return
            
            # Get category ID
            categories = self.app.category_model.get_all()
            new_category_id = None
            for cat in categories:
                if cat[1] == category:
                    new_category_id = cat[0]
                    break
            
            if not new_category_id:
                self.show_message("Warning", "Invalid category", "warning")
                return
            
            # Update menu item
            self.app.menu_item_model.update(item_id, name, price, new_category_id, stock, image_path)
            
            self.show_message("Success", "Menu item updated successfully", "info")
            edit_window.destroy()
            self.load_menu_items_management()
        
        self.create_button_frame(buttons_frame, [
            ("Update", update_item),
            ("Cancel", edit_window.destroy)
        ])
    
    def delete_menu_item(self):
        """Delete selected menu item"""
        selection = self.menu_items_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to delete", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.menu_items_tree.item(selection[0])['tags'][0])
        
        # Get item name
        item = self.menu_items_tree.item(selection[0])
        item_name = item['values'][0]
        
        # Confirm deletion
        if self.show_message("Confirm Delete", f"Are you sure you want to delete {item_name}?", "yesno"):
            # Delete menu item
            self.app.menu_item_model.delete(item_id)
            
            self.show_message("Success", "Menu item deleted successfully", "info")
            self.load_menu_items_management()
    
    def add_category(self):
        """Add a new category"""
        # Create add category window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add Category")
        add_window.geometry("300x150")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=10)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        def save_category():
            name = name_entry.get().strip()
            
            if not name:
                self.show_message("Warning", "Please enter a category name", "warning")
                return
            
            # Insert category
            success = self.app.category_model.add(name)
            
            if success:
                self.show_message("Success", "Category added successfully", "info")
                add_window.destroy()
                self.load_menu_categories()
                self.load_menu_items_management()
            else:
                self.show_message("Error", "Category already exists", "error")
        
        self.create_button_frame(buttons_frame, [
            ("Save", save_category),
            ("Cancel", add_window.destroy)
        ])
    
    def edit_category(self):
        """Edit selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select a category to edit", "warning")
            return
        
        # Get category ID from tags
        category_id = int(self.categories_tree.item(selection[0])['tags'][0])
        
        # Get category name
        category = self.categories_tree.item(selection[0])
        category_name = category['values'][0]
        
        # Create edit category window
        edit_window = tk.Toplevel(self.app.root)
        edit_window.title("Edit Category")
        edit_window.geometry("300x150")
        
        # Create form
        form_frame = ttk.Frame(edit_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=10)
        name_entry = ttk.Entry(form_frame, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        name_entry.insert(0, category_name)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        def update_category():
            name = name_entry.get().strip()
            
            if not name:
                self.show_message("Warning", "Please enter a category name", "warning")
                return
            
            # Update category
            success = self.app.category_model.update(category_id, name)
            
            if success:
                self.show_message("Success", "Category updated successfully", "info")
                edit_window.destroy()
                self.load_menu_categories()
                self.load_menu_items_management()
            else:
                self.show_message("Error", "Category already exists", "error")
        
        self.create_button_frame(buttons_frame, [
            ("Update", update_category),
            ("Cancel", edit_window.destroy)
        ])
    
    def delete_category(self):
        """Delete selected category"""
        selection = self.categories_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select a category to delete", "warning")
            return
        
        # Get category ID from tags
        category_id = int(self.categories_tree.item(selection[0])['tags'][0])
        
        # Get category name
        category = self.categories_tree.item(selection[0])
        category_name = category['values'][0]
        
        # Check if category is being used by menu items
        item_count = self.app.category_model.get_item_count(category_id)
        
        if item_count > 0:
            self.show_message("Warning", f"Cannot delete category '{category_name}' as it is being used by {item_count} menu items", "warning")
            return
        
        # Confirm deletion
        if self.show_message("Confirm Delete", f"Are you sure you want to delete {category_name}?", "yesno"):
            # Delete category
            self.app.category_model.delete(category_id)
            
            self.show_message("Success", "Category deleted successfully", "info")
            self.load_menu_categories()
