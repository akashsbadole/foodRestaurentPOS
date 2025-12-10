import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
import os
from .base_ui import BaseUI
from src.utils.constants import *
from src.utils.image_handler import TkinterImageHandler

class MenuScreen(BaseUI):
    """Menu management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup modern menu management UI"""
        # Configure modern styles
        self.configure_styles()
        
        # Set main background - use style configuration for ttk.Frame
        try:
            self.app.content_frame.configure(background=COLOR_BACKGROUND_LIGHT)
        except tk.TclError:
            # If it's a ttk.Frame, use style configuration
            style = ttk.Style()
            style.configure("MenuScreen.TFrame", background=COLOR_BACKGROUND_LIGHT)
            self.app.content_frame.configure(style="MenuScreen.TFrame")
        
        # Title with modern styling
        title_frame = self.create_modern_frame(self.app.content_frame, style="Card.TFrame", padding=(SPACING_L, SPACING_M, SPACING_L, SPACING_M))
        title_frame.pack(fill=tk.X, padx=SPACING_L, pady=(SPACING_L, SPACING_M))
        
        title_label = self.create_modern_label(title_frame, "Menu Management", style="Title.TLabel")
        title_label.pack()
        
        # Create main menu container with modern styling
        menu_container = self.create_modern_frame(self.app.content_frame, style="Card.TFrame", padding=SPACING_L)
        menu_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=(0, SPACING_L))
        
        # Create two-panel layout with better visual separation
        panels_frame = ttk.Frame(menu_container, style="Card.TFrame")
        panels_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Menu items with modern card design
        left_panel = self.create_modern_frame(panels_frame, style="Panel.TFrame", padding=SPACING_M)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, SPACING_S))
        
        # Section title for menu items
        menu_title = self.create_modern_label(left_panel, "Menu Items", style="SectionTitle.TLabel")
        menu_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Modern search and filter section
        search_frame = self.create_modern_frame(left_panel, style="Card.TFrame", padding=SPACING_M)
        search_frame.pack(fill=tk.X, pady=(0, SPACING_M))
        
        # Search field with modern styling
        search_label = self.create_modern_label(search_frame, "Search:", style="Body.TLabel")
        search_label.grid(row=0, column=0, sticky=tk.W, padx=(0, SPACING_S), pady=SPACING_S)
        
        self.search_entry = self.create_modern_entry(search_frame, style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12))
        self.search_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, SPACING_M), pady=SPACING_S)
        self.search_entry.bind("<KeyRelease>", self.search_menu_items)
        
        # Category filter with modern styling
        category_label = self.create_modern_label(search_frame, "Category:", style="Body.TLabel")
        category_label.grid(row=1, column=0, sticky=tk.W, padx=(0, SPACING_S), pady=SPACING_S)
        
        self.category_var = tk.StringVar()
        self.category_combo = self.create_modern_combobox(
            search_frame,
            self.category_var,
            [],
            style="Modern.TCombobox",
            state="readonly",
            font=(FONT_FAMILY_PRIMARY, 12)
        )
        self.category_combo.grid(row=1, column=1, sticky=tk.W+tk.E, padx=(0, SPACING_M), pady=SPACING_S)
        self.category_combo.bind("<<ComboboxSelected>>", self.filter_menu_items)
        
        # Price range filter
        price_label = self.create_modern_label(search_frame, "Price Range:", style="Body.TLabel")
        price_label.grid(row=2, column=0, sticky=tk.W, padx=(0, SPACING_S), pady=SPACING_S)
        
        price_range_frame = ttk.Frame(search_frame, style="Card.TFrame")
        price_range_frame.grid(row=2, column=1, sticky=tk.W+tk.E, padx=(0, SPACING_M), pady=SPACING_S)
        
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        
        min_price_entry = self.create_modern_entry(
            price_range_frame,
            textvariable=self.min_price_var,
            style="Modern.TEntry",
            font=(FONT_FAMILY_PRIMARY, 12),
            width=10
        )
        min_price_entry.pack(side=tk.LEFT, padx=(0, SPACING_XS))
        
        to_label = self.create_modern_label(price_range_frame, "to", style="Body.TLabel")
        to_label.pack(side=tk.LEFT, padx=SPACING_XS)
        
        max_price_entry = self.create_modern_entry(
            price_range_frame,
            textvariable=self.max_price_var,
            style="Modern.TEntry",
            font=(FONT_FAMILY_PRIMARY, 12),
            width=10
        )
        max_price_entry.pack(side=tk.LEFT, padx=(SPACING_XS, 0))
        
        # Stock status filter
        stock_label = self.create_modern_label(search_frame, "Stock Status:", style="Body.TLabel")
        stock_label.grid(row=3, column=0, sticky=tk.W, padx=(0, SPACING_S), pady=SPACING_S)
        
        self.stock_var = tk.StringVar(value="All")
        stock_combo = self.create_modern_combobox(
            search_frame,
            self.stock_var,
            ["All", "In Stock", "Low Stock", "Out of Stock"],
            style="Modern.TCombobox",
            state="readonly",
            font=(FONT_FAMILY_PRIMARY, 12)
        )
        stock_combo.grid(row=3, column=1, sticky=tk.W+tk.E, padx=(0, SPACING_M), pady=SPACING_S)
        stock_combo.bind("<<ComboboxSelected>>", self.filter_menu_items)
        
        # Clear filters button
        clear_button = self.create_modern_button(
            search_frame, "Clear Filters", self.clear_filters,
            style="Secondary.TButton"
        )
        clear_button.grid(row=4, column=1, sticky=tk.E, padx=(0, SPACING_M), pady=SPACING_S)
        
        # Configure grid weights for responsive layout
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Modern menu items treeview with card design
        items_card = self.create_modern_frame(left_panel, style="Card.TFrame", padding=SPACING_S)
        items_card.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        self.menu_items_tree, menu_scrollbar = self.create_modern_treeview(
            items_card,
            ("name", "category", "price", "stock", "shortcode", "image"),
            ("Name", "Category", "Price", "Stock", "Shortcode", "Image"),
            (180, 120, 80, 70, 80, 60)
        )
        self.menu_items_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure treeview tags for stock status
        self.menu_items_tree.tag_configure("in_stock", background=COLOR_SUCCESS_LIGHT)
        self.menu_items_tree.tag_configure("low_stock", background=COLOR_WARNING_LIGHT)
        self.menu_items_tree.tag_configure("out_of_stock", background=COLOR_ERROR_LIGHT)
        
        # Modern CRUD buttons with proper styling
        self.create_button_group(left_panel, [
            ("Add Item", self.add_menu_item, "Success.TButton"),
            ("Edit Item", self.edit_menu_item, "Primary.TButton"),
            ("Delete Item", self.delete_menu_item, "Danger.TButton")
        ], spacing=SPACING_S)
        
        # Right panel - Categories with modern design
        right_panel = self.create_modern_frame(panels_frame, style="Panel.TFrame", padding=SPACING_M)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(SPACING_S, 0))
        
        # Section title for categories
        categories_title = self.create_modern_label(right_panel, "Categories", style="SectionTitle.TLabel")
        categories_title.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Modern categories container
        categories_card = self.create_modern_frame(right_panel, style="Card.TFrame", padding=SPACING_M)
        categories_card.pack(fill=tk.BOTH, expand=True, pady=(0, SPACING_M))
        
        # Modern categories treeview
        self.categories_tree, categories_scrollbar = self.create_modern_treeview(
            categories_card,
            ("name",),
            ("Category Name",),
            (200,)
        )
        self.categories_tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure treeview tags for active categories
        self.categories_tree.tag_configure("active", background=COLOR_PRIMARY_LIGHT)
        
        # Modern category management buttons
        self.create_button_group(right_panel, [
            ("Add Category", self.add_category, "Success.TButton"),
            ("Edit Category", self.edit_category, "Primary.TButton"),
            ("Delete Category", self.delete_category, "Danger.TButton")
        ], spacing=SPACING_S)
        
        # Load initial data
        self.load_menu_categories()
        self.load_menu_items_management()
    
    def show_image_preview(self, image_path, parent_frame):
        """Show image preview in the given parent frame"""
        try:
            # Clear previous preview
            for widget in parent_frame.winfo_children():
                widget.destroy()
            
            # Load and resize image for preview
            image = Image.open(image_path)
            image.thumbnail((150, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Create label with image
            preview_label = ttk.Label(parent_frame, image=photo)
            preview_label.image = photo  # Keep a reference
            preview_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            # Add image info
            info_text = f"Size: {image.size[0]}x{image.size[1]}"
            info_label = self.create_modern_label(parent_frame, info_text, style="Small.TLabel")
            info_label.pack(side=tk.LEFT, padx=(SPACING_S, 0))
            
        except Exception as e:
            error_label = self.create_modern_label(parent_frame, f"Preview error: {str(e)}", style="Small.TLabel")
            error_label.pack(side=tk.LEFT)
    
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
    
    def clear_filters(self):
        """Clear all search filters"""
        self.search_entry.delete(0, tk.END)
        self.category_combo.current(0)
        self.min_price_var.set("")
        self.max_price_var.set("")
        self.stock_var.set("All")
        self.load_menu_items_management()
    
    def load_menu_items_management(self, search_term="", category="All"):
        """Load menu items for menu management screen with enhanced error handling"""
        try:
            # Get filter values
            search_term = self.search_entry.get()
            category = self.category_var.get()
            min_price = self.min_price_var.get().strip()
            max_price = self.max_price_var.get().strip()
            stock_status = self.stock_var.get()
            
            items = self.app.menu_item_model.get_all(search_term, category)
            
            # Apply additional filters
            filtered_items = []
            for item in items:
                item_id, name, item_category, price, stock = item
                
                # Price filter
                if min_price and max_price:
                    try:
                        if price < float(min_price) or price > float(max_price):
                            continue
                    except ValueError:
                        pass
                elif min_price:
                    try:
                        if price < float(min_price):
                            continue
                    except ValueError:
                        pass
                elif max_price:
                    try:
                        if price > float(max_price):
                            continue
                    except ValueError:
                        pass
                
                # Stock status filter
                if stock_status != "All":
                    try:
                        stock_int = int(stock) if isinstance(stock, str) else stock
                        if stock_status == "In Stock" and stock_int <= LOW_STOCK_THRESHOLD:
                            continue
                        elif stock_status == "Low Stock" and (stock_int <= 0 or stock_int > LOW_STOCK_THRESHOLD):
                            continue
                        elif stock_status == "Out of Stock" and stock_int > 0:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                filtered_items.append(item)
            
            items = filtered_items
            
            # Clear menu items tree
            for item in self.menu_items_tree.get_children():
                self.menu_items_tree.delete(item)
            
            # Add items to tree with stock status tags
            for item in items:
                item_id, name, category, price, stock, shortcode = item
                
                # Convert stock to integer if it's a string
                try:
                    stock_int = int(stock) if isinstance(stock, str) else stock
                except (ValueError, TypeError):
                    stock_int = 0
                
                # Determine stock status tag
                if stock_int <= 0:
                    stock_tag = "out_of_stock"
                elif stock_int <= LOW_STOCK_THRESHOLD:
                    stock_tag = "low_stock"
                else:
                    stock_tag = "in_stock"
                
                # Get image info for display
                image_display = "No Image"
                if len(item) > 5 and item[5]:  # Check if image_path exists
                    image_display = "Has Image"
                
                self.menu_items_tree.insert("", tk.END, values=(
                    name,
                    category,
                    f"₹{price:.2f}",
                    f"{stock_int} units",
                    shortcode or "",
                    image_display
                ), tags=(item_id, stock_tag))
                
        except Exception as e:
            print(f"Error loading menu items: {e}")
            # Show error message
            error_frame = self.create_modern_frame(self.menu_items_tree.master, style="Card.TFrame", padding=SPACING_XL)
            error_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_L)
            
            error_icon = self.create_modern_label(error_frame, text="⚠", style="Title.TLabel")
            error_icon.pack(pady=(0, SPACING_M))
            
            error_label = self.create_modern_label(error_frame, text="Failed to load menu items", style="Subtitle.TLabel")
            error_label.pack()
            
            error_sublabel = self.create_modern_label(error_frame, text="Please try refreshing the screen", style="Small.TLabel")
            error_sublabel.pack(pady=(SPACING_S, 0))
    
    def search_menu_items(self, event=None):
        """Search menu items with all filters"""
        self.load_menu_items_management()
    
    def filter_menu_items(self, event=None):
        """Filter menu items by all criteria"""
        self.load_menu_items_management()
    
    def add_menu_item(self):
        """Add a new menu item with modern dialog"""
        # Create modern add item window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add Menu Item")
        add_window.geometry("450x500")
        add_window.configure(bg=COLOR_BACKGROUND_LIGHT)
        
        # Apply modern styling to the window
        self.configure_styles()
        
        # Create modern form container
        form_container = self.create_modern_frame(add_window, style="Card.TFrame", padding=SPACING_L)
        form_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title
        title_label = self.create_modern_label(form_container, "Add New Menu Item", style="SectionTitle.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Form fields with modern styling
        form_frame = ttk.Frame(form_container, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        name_entry = self.create_form_field(
            form_frame, "Item Name:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        
        # Category field
        categories = self.app.category_model.get_all()
        category_list = [category[1] for category in categories]
        category_var = tk.StringVar()
        category_combo = self.create_form_field(
            form_frame, "Category:", "combobox",
            textvariable=category_var, values=category_list,
            style="Modern.TCombobox", font=(FONT_FAMILY_PRIMARY, 12), width=28
        )
        if category_list:
            category_combo.current(0)
        
        # Price field
        price_entry = self.create_form_field(
            form_frame, "Price (₹):", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        
        # Stock field
        stock_entry = self.create_form_field(
            form_frame, "Stock Quantity:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        stock_entry.insert(0, "0")  # Set default value to 0
        
        # Shortcode field
        shortcode_entry = self.create_form_field(
            form_frame, "Shortcode (Optional):", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        
        # Image path field
        image_path_var = tk.StringVar()
        image_frame = ttk.Frame(form_frame, style="Card.TFrame")
        image_frame.pack(fill=tk.X, pady=SPACING_M)
        
        image_label = self.create_modern_label(image_frame, "Image Path:", style="Body.TLabel")
        image_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        image_path_frame = ttk.Frame(image_frame, style="Card.TFrame")
        image_path_frame.pack(fill=tk.X)
        
        image_path_entry = self.create_modern_entry(
            image_path_frame, 
            textvariable=image_path_var,
            style="Modern.TEntry", 
            font=(FONT_FAMILY_PRIMARY, 12)
        )
        image_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, SPACING_S))
        
        # Image preview label
        self.image_preview_label = None
        
        def browse_image():
            file_path, error = TkinterImageHandler.select_image_file(add_window)
            if file_path:
                # Store the selected file path
                image_path_var.set(file_path)
                
                # Show preview
                self.show_image_preview(file_path, preview_frame)
        
        browse_button = self.create_modern_button(
            image_path_frame, "Browse", browse_image,
            style="Secondary.TButton"
        )
        browse_button.pack(side=tk.RIGHT)
        
        # Image preview frame
        preview_frame = ttk.Frame(image_frame, style="Card.TFrame")
        preview_frame.pack(fill=tk.X, pady=(SPACING_S, 0))
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Modern buttons
        button_frame = ttk.Frame(form_container, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        def save_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            shortcode = shortcode_entry.get().strip()
            
            if not name or not category or not price:
                self.show_message("Warning", "Please fill in all required fields", "warning")
                return
            
            # Handle empty stock field by defaulting to 0
            if not stock:
                stock = "0"
            
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
            
            # Validate shortcode uniqueness
            if not self.app.menu_item_model.is_shortcode_unique(shortcode, category_id):
                self.show_message("Warning", f"Shortcode '{shortcode}' already exists in this category", "warning")
                return
            
            # Process image if provided
            processed_image_path = image_path
            if image_path:
                # Create storage folder if it doesn't exist
                storage_folder = os.path.join(os.path.dirname(__file__), '..', '..', 'images', 'menu_items')
                os.makedirs(storage_folder, exist_ok=True)
                
                # Copy and process image
                success, result = TkinterImageHandler.copy_image_to_storage(
                    image_path, storage_folder, 'menu_item'
                )
                
                if success:
                    processed_image_path = result['filename']
                else:
                    self.show_message("Warning", f"Image processing failed: {result}. Using original path.", "warning")
            
            # Insert menu item
            self.app.menu_item_model.add(name, price, category_id, stock, processed_image_path, shortcode)
            
            self.show_message("Success", "Menu item added successfully", "info")
            add_window.destroy()
            self.load_menu_items_management()
        
        def cancel_add():
            add_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Save Item", save_item, "Success.TButton"),
            ("Cancel", cancel_add, "Secondary.TButton")
        ], spacing=SPACING_S)
    
    def edit_menu_item(self):
        """Edit selected menu item with modern dialog"""
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
        
        # Create modern edit item window
        edit_window = tk.Toplevel(self.app.root)
        edit_window.title("Edit Menu Item")
        edit_window.geometry("450x500")
        edit_window.configure(bg=COLOR_BACKGROUND_LIGHT)
        
        # Apply modern styling to the window
        self.configure_styles()
        
        # Create modern form container
        form_container = self.create_modern_frame(edit_window, style="Card.TFrame", padding=SPACING_L)
        form_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title
        title_label = self.create_modern_label(form_container, "Edit Menu Item", style="SectionTitle.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Form fields with modern styling
        form_frame = ttk.Frame(form_container, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        name_entry = self.create_form_field(
            form_frame, "Item Name:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        name_entry.insert(0, name)
        
        # Category field
        categories = self.app.category_model.get_all()
        category_list = [category[1] for category in categories]
        category_var = tk.StringVar(value=category_name)
        category_combo = self.create_form_field(
            form_frame, "Category:", "combobox",
            textvariable=category_var, values=category_list,
            style="Modern.TCombobox", font=(FONT_FAMILY_PRIMARY, 12), width=28
        )
        
        # Price field
        price_entry = self.create_form_field(
            form_frame, "Price (₹):", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        price_entry.insert(0, str(price))
        
        # Stock field
        stock_entry = self.create_form_field(
            form_frame, "Stock Quantity:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        stock_entry.insert(0, str(stock))
        
        # Shortcode field
        shortcode_entry = self.create_form_field(
            form_frame, "Shortcode (Optional):", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        # Note: We need to get the shortcode from the item details, but we need to update get_by_id to include it
        # For now, we'll leave it empty
        if len(item_details) > 5:
            shortcode_entry.insert(0, item_details[5] or "")
        
        # Image path field
        image_path_var = tk.StringVar(value=image_path or "")
        image_frame = ttk.Frame(form_frame, style="Card.TFrame")
        image_frame.pack(fill=tk.X, pady=SPACING_M)
        
        image_label = self.create_modern_label(image_frame, "Image Path:", style="Body.TLabel")
        image_label.pack(anchor=tk.W, pady=(SPACING_S, SPACING_XS))
        
        image_path_frame = ttk.Frame(image_frame, style="Card.TFrame")
        image_path_frame.pack(fill=tk.X)
        
        image_path_entry = self.create_modern_entry(
            image_path_frame, 
            textvariable=image_path_var,
            style="Modern.TEntry", 
            font=(FONT_FAMILY_PRIMARY, 12)
        )
        image_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, SPACING_S))
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                title="Select Image",
                filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")]
            )
            if file_path:
                image_path_var.set(file_path)
        
        browse_button = self.create_modern_button(
            image_path_frame, "Browse", browse_image, 
            style="Secondary.TButton"
        )
        browse_button.pack(side=tk.RIGHT)
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Modern buttons
        button_frame = ttk.Frame(form_container, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
        def update_item():
            name = name_entry.get().strip()
            category = category_var.get()
            price = price_entry.get().strip()
            stock = stock_entry.get().strip()
            image_path = image_path_var.get().strip()
            shortcode = shortcode_entry.get().strip()
            
            if not name or not category or not price:
                self.show_message("Warning", "Please fill in all required fields", "warning")
                return
            
            # Handle empty stock field by defaulting to 0
            if not stock:
                stock = "0"
            
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
            
            # Validate shortcode uniqueness
            if not self.app.menu_item_model.is_shortcode_unique(shortcode, new_category_id, item_id):
                self.show_message("Warning", f"Shortcode '{shortcode}' already exists in this category", "warning")
                return
            
            # Update menu item
            self.app.menu_item_model.update(item_id, name, price, new_category_id, stock, image_path, shortcode)
            
            self.show_message("Success", "Menu item updated successfully", "info")
            edit_window.destroy()
            self.load_menu_items_management()
        
        def cancel_edit():
            edit_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Update Item", update_item, "Primary.TButton"),
            ("Cancel", cancel_edit, "Secondary.TButton")
        ], spacing=SPACING_S)
    
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
        """Add a new category with modern dialog"""
        # Create modern add category window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add Category")
        add_window.geometry("350x200")
        add_window.configure(bg=COLOR_BACKGROUND_LIGHT)
        
        # Apply modern styling to the window
        self.configure_styles()
        
        # Create modern form container
        form_container = self.create_modern_frame(add_window, style="Card.TFrame", padding=SPACING_L)
        form_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title
        title_label = self.create_modern_label(form_container, "Add New Category", style="SectionTitle.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Form fields with modern styling
        form_frame = ttk.Frame(form_container, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        name_entry = self.create_form_field(
            form_frame, "Category Name:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Modern buttons
        button_frame = ttk.Frame(form_container, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
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
        
        def cancel_add():
            add_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Save Category", save_category, "Success.TButton"),
            ("Cancel", cancel_add, "Secondary.TButton")
        ], spacing=SPACING_S)
    
    def edit_category(self):
        """Edit selected category with modern dialog"""
        selection = self.categories_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select a category to edit", "warning")
            return
        
        # Get category ID from tags
        category_id = int(self.categories_tree.item(selection[0])['tags'][0])
        
        # Get category name
        category = self.categories_tree.item(selection[0])
        category_name = category['values'][0]
        
        # Create modern edit category window
        edit_window = tk.Toplevel(self.app.root)
        edit_window.title("Edit Category")
        edit_window.geometry("350x200")
        edit_window.configure(bg=COLOR_BACKGROUND_LIGHT)
        
        # Apply modern styling to the window
        self.configure_styles()
        
        # Create modern form container
        form_container = self.create_modern_frame(edit_window, style="Card.TFrame", padding=SPACING_L)
        form_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
        
        # Title
        title_label = self.create_modern_label(form_container, "Edit Category", style="SectionTitle.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, SPACING_M))
        
        # Form fields with modern styling
        form_frame = ttk.Frame(form_container, style="Card.TFrame")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Name field
        name_entry = self.create_form_field(
            form_frame, "Category Name:", "entry",
            style="Modern.TEntry", font=(FONT_FAMILY_PRIMARY, 12), width=30
        )
        name_entry.insert(0, category_name)
        
        # Configure grid weights
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Modern buttons
        button_frame = ttk.Frame(form_container, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=(SPACING_M, 0))
        
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
        
        def cancel_edit():
            edit_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Update Category", update_category, "Primary.TButton"),
            ("Cancel", cancel_edit, "Secondary.TButton")
        ], spacing=SPACING_S)
    
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