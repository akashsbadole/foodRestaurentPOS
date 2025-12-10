# Order Screen Component Architecture

## Component Hierarchy

```
OrderScreen (Main Container)
├── Top Header Frame
│   ├── Left Side: Tab Container
│   │   ├── New Order Button
│   │   └── Order Tabs (Dynamic)
│   └── Right Side: User Profile
│       ├── User Label
│       └── Logout Button
├── Main Content Frame
│   ├── Left Panel (60% width)
│   │   ├── Customer Details Frame (2x2 Grid)
│   │   │   ├── Order Type Radio Buttons
│   │   │   ├── Table Dropdown
│   │   │   ├── Customer Name Entry
│   │   │   └── Mobile Number Entry
│   │   ├── Item Selection Frame
│   │   │   ├── Category Dropdown
│   │   │   ├── Item Dropdown
│   │   │   ├── Quantity Spinbox
│   │   │   ├── Add Button
│   │   │   ├── Search Entry
│   │   │   ├── Clear Search Button
│   │   │   └── Clear Order Button
│   │   └── Status Control Strip
│   │       ├── Status Buttons (New, In Progress, Ready, Completed)
│   │       └── Status Indicator
│   └── Right Panel (40% width)
│       ├── Active Orders Frame
│       │   ├── Orders Treeview
│       │   └── Order Info Strip
│       ├── Financial Breakdown Frame
│       │   ├── Subtotal Label
│       │   ├── CGST Label
│       │   ├── SGST Label
│       │   ├── Discount Label
│       │   ├── Separator Line
│       │   └── Total Label
│       └── Action Buttons Frame
│           ├── Discount Button
│           ├── Export Button
│           └── Process Payment Button
```

## Detailed Component Specifications

### 1. Top Header Frame

#### Properties
- Height: Fixed 60px
- Background: Light gray (#f0f0f0)
- Border: Bottom border for visual separation

#### Left Side: Tab Container
```python
self.tab_bar_frame = ttk.Frame(self.header_frame)
self.tab_bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

# New Order Button
self.new_order_btn = ttk.Button(
    self.tab_bar_frame,
    text="+ New Order",
    command=self.new_order,
    style='Accent.TButton'
)
self.new_order_btn.pack(side=tk.LEFT, padx=(0, 5))

# Tabs Container
self.tabs_container = ttk.Frame(self.tab_bar_frame)
self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
```

#### Right Side: User Profile
```python
self.user_frame = ttk.Frame(self.header_frame)
self.user_frame.pack(side=tk.RIGHT, padx=5, pady=5)

self.user_label = ttk.Label(
    self.user_frame,
    text=f"User: {self.app.current_user['username']} ({self.app.current_user['role']})"
)
self.user_label.pack(side=tk.LEFT, padx=(0, 10))

self.logout_btn = ttk.Button(
    self.user_frame,
    text="Logout",
    command=self.logout
)
self.logout_btn.pack(side=tk.LEFT)
```

### 2. Left Panel (60% width)

#### Properties
- Width: 60% of available width
- Padding: 10px on all sides
- Background: White

#### A. Customer Details Frame (2x2 Grid)
```python
self.customer_frame = ttk.LabelFrame(self.left_panel, text="Customer Info", padding=10)
self.customer_frame.pack(fill=tk.X, pady=(0, 10))

# Row 0: Order Type | Table
ttk.Label(self.customer_frame, text="Order Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
self.dine_radio = ttk.Radiobutton(
    self.customer_frame, text="Dine-in", 
    variable=self.order_type, value="Dine-in",
    command=self.on_order_type_changed
)
self.dine_radio.grid(row=0, column=1, sticky=tk.W, padx=5)

self.takeaway_radio = ttk.Radiobutton(
    self.customer_frame, text="Takeaway", 
    variable=self.order_type, value="Takeaway",
    command=self.on_order_type_changed
)
self.takeaway_radio.grid(row=0, column=2, sticky=tk.W, padx=5)

ttk.Label(self.customer_frame, text="Table:").grid(row=0, column=3, sticky=tk.W, padx=5)
self.table_combo = ttk.Combobox(self.customer_frame, width=15, state="readonly")
self.table_combo.grid(row=0, column=4, padx=5)

# Row 1: Customer Name | Mobile
ttk.Label(self.customer_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, padx=5)
self.customer_entry = ttk.Entry(self.customer_frame, width=20)
self.customer_entry.grid(row=1, column=1, columnspan=2, padx=5, sticky=tk.W+tk.E)

ttk.Label(self.customer_frame, text="Mobile:").grid(row=1, column=3, sticky=tk.W, padx=5)
self.mobile_entry = ttk.Entry(self.customer_frame, width=15)
self.mobile_entry.grid(row=1, column=4, padx=5, sticky=tk.W+tk.E)
```

#### B. Item Selection Frame
```python
self.item_frame = ttk.LabelFrame(self.left_panel, text="Add Items", padding=10)
self.item_frame.pack(fill=tk.X, pady=(0, 10))

# Row 0: Category | Item | Quantity | Add
self.category_combo = ttk.Combobox(self.item_frame, width=20, state="readonly")
self.category_combo.grid(row=0, column=0, padx=5, sticky=tk.W)

self.menu_combo = ttk.Combobox(self.item_frame, width=30, state="readonly")
self.menu_combo.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)

self.quantity_var = tk.StringVar(value="1")
self.quantity_spin = ttk.Spinbox(self.item_frame, from_=1, to=99, textvariable=self.quantity_var, width=8)
self.quantity_spin.grid(row=0, column=2, padx=5)

self.add_btn = ttk.Button(self.item_frame, text="ADD", command=self.add_item, width=10)
self.add_btn.grid(row=0, column=3, padx=5)

# Row 1: Search | Clear | Clear Order
self.search_var = tk.StringVar()
self.search_entry = ttk.Entry(self.item_frame, textvariable=self.search_var)
self.search_entry.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)

self.clear_search_btn = ttk.Button(self.item_frame, text="Clear", command=self.clear_search)
self.clear_search_btn.grid(row=1, column=2, padx=5, pady=5)

self.clear_order_btn = ttk.Button(self.item_frame, text="Clear Order", command=self.clear_current_order)
self.clear_order_btn.grid(row=1, column=3, padx=5, pady=5)
```

#### C. Status Control Strip
```python
self.status_frame = ttk.LabelFrame(self.left_panel, text="Order Status", padding=10)
self.status_frame.pack(fill=tk.X, pady=(0, 10))

self.status_var = tk.StringVar(value="new")
self.status_buttons = {}

status_options = [
    ("new", "New", "#808080"),
    ("in_progress", "In Progress", "#FFA500"),
    ("ready", "Ready", "#008000"),
    ("completed", "Completed", "#0000FF")
]

for i, (key, text, color) in enumerate(status_options):
    btn = ttk.Button(
        self.status_frame,
        text=text,
        command=lambda k=key: self.set_order_status(k),
        width=15
    )
    btn.grid(row=0, column=i, padx=5, pady=5)
    self.status_buttons[key] = btn
```

### 3. Right Panel (40% width)

#### Properties
- Width: 40% of available width
- Padding: 10px on all sides
- Background: Light gray (#f8f8f8)

#### A. Active Orders Frame
```python
self.orders_frame = ttk.LabelFrame(self.right_panel, text="Active Orders", padding=10)
self.orders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

# Treeview
self.order_tree = ttk.Treeview(
    self.orders_frame,
    columns=("item", "quantity", "price", "total"),
    show="headings",
    height=8
)
self.order_tree.heading("item", text="Item")
self.order_tree.heading("quantity", text="Qty")
self.order_tree.heading("price", text="Price")
self.order_tree.heading("total", text="Total")

self.order_tree.column("item", width=200)
self.order_tree.column("quantity", width=60)
self.order_tree.column("price", width=80)
self.order_tree.column("total", width=80)

self.order_tree.pack(fill=tk.BOTH, expand=True)

# Scrollbar
scrollbar = ttk.Scrollbar(self.orders_frame, orient=tk.VERTICAL, command=self.order_tree.yview)
self.order_tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Info Strip
self.info_label = ttk.Label(
    self.orders_frame,
    text="Items: 0 | Status: New",
    font=('Arial', 9, 'bold')
)
self.info_label.pack(fill=tk.X, pady=(5, 0))
```

#### B. Financial Breakdown Frame
```python
self.financial_frame = ttk.Frame(self.right_panel)
self.financial_frame.pack(fill=tk.X, pady=(0, 10))

# Right-aligned labels
self.subtotal_label = ttk.Label(self.financial_frame, text="Subtotal:     Rs.0.00", font=('Arial', 10))
self.subtotal_label.pack(anchor=tk.E, pady=2)

self.cgst_label = ttk.Label(self.financial_frame, text="CGST (2.5%):  Rs.0.00", font=('Arial', 9))
self.cgst_label.pack(anchor=tk.E, pady=1)

self.sgst_label = ttk.Label(self.financial_frame, text="SGST (2.5%):  Rs.0.00", font=('Arial', 9))
self.sgst_label.pack(anchor=tk.E, pady=1)

self.discount_label = ttk.Label(self.financial_frame, text="Discount:   - Rs.0.00", font=('Arial', 10))
self.discount_label.pack(anchor=tk.E, pady=2)

# Separator
separator = ttk.Separator(self.financial_frame, orient='horizontal')
separator.pack(fill=tk.X, pady=5)

self.total_label = ttk.Label(self.financial_frame, text="TOTAL:        Rs.0.00", font=('Arial', 12, 'bold'))
self.total_label.pack(anchor=tk.E, pady=2)
```

#### C. Action Buttons Frame
```python
self.action_frame = ttk.Frame(self.right_panel)
self.action_frame.pack(fill=tk.X)

self.discount_btn = ttk.Button(
    self.action_frame,
    text="Apply Discount",
    command=self.apply_discount,
    width=15
)
self.discount_btn.pack(side=tk.LEFT, padx=5)

self.export_btn = ttk.Button(
    self.action_frame,
    text="Export Order",
    command=self.export_order,
    width=15
)
self.export_btn.pack(side=tk.LEFT, padx=5)

self.payment_btn = ttk.Button(
    self.action_frame,
    text="PROCESS PAYMENT",
    command=self.process_payment,
    width=18,
    style='Accent.TButton'
)
self.payment_btn.pack(side=tk.RIGHT, padx=5)
```

## Event Handlers and Methods

### Status Control Methods
```python
def set_order_status(self, status):
    """Set order status with validation"""
    current_order = self.order_manager.get_current_order()
    if not current_order:
        return
    
    # Validate status transitions
    if status == "completed" and not current_order['items']:
        messagebox.showwarning("Warning", "Cannot complete empty order")
        return
    
    # Update status in order manager
    self.order_manager.update_order_status(self.order_manager.current_order_id, status)
    
    # Update button appearances
    self.update_status_buttons()
    
    # Refresh displays
    self.refresh_orders_list()

def update_status_buttons(self):
    """Update status button appearances based on current status"""
    current_order = self.order_manager.get_current_order()
    if not current_order:
        return
    
    current_status = current_order['status']
    
    for status_key, button in self.status_buttons.items():
        if status_key == current_status:
            button.configure(style='ActiveStatus.TButton')
        else:
            button.configure(style='TButton')
```

### Layout Management Methods
```python
def create_split_layout(self):
    """Create the main split-screen layout"""
    # Main container
    self.main_frame = ttk.Frame(self.content_frame)
    self.main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create horizontal paned window for 60/40 split
    self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
    self.paned_window.pack(fill=tk.BOTH, expand=True)
    
    # Left panel (60%)
    self.left_panel = ttk.Frame(self.paned_window)
    self.paned_window.add(self.left_panel, weight=6)
    
    # Right panel (40%)
    self.right_panel = ttk.Frame(self.paned_window)
    self.paned_window.add(self.right_panel, weight=4)
    
    # Create components in each panel
    self.create_header()
    self.create_left_panel_components()
    self.create_right_panel_components()

def create_header(self):
    """Create top header with tabs and user info"""
    self.header_frame = ttk.Frame(self.main_frame, height=60)
    self.header_frame.pack(fill=tk.X, pady=(0, 10))
    self.header_frame.pack_propagate(False)  # Prevent height from changing
    
    # Create tab container and user info
    self.create_tab_container()
    self.create_user_info()
```

## Responsive Design Considerations

### Screen Size Handling
```python
def setup_responsive_layout(self):
    """Setup responsive layout for different screen sizes"""
    # Get screen dimensions
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    
    # Set minimum window size
    min_width = 1280
    min_height = 720
    
    if screen_width < min_width or screen_height < min_height:
        messagebox.showwarning(
            "Screen Resolution",
            f"Minimum resolution required: {min_width}x{min_height}\n"
            f"Current resolution: {screen_width}x{screen_height}"
        )
    
    # Configure window
    self.root.minsize(min_width, min_height)
    
    # Center window on screen
    x = (screen_width - min_width) // 2
    y = (screen_height - min_height) // 2
    self.root.geometry(f"{min_width}x{min_height}+{x}+{y}")
```

### Component Scaling
```python
def scale_components(self):
    """Scale components based on window size"""
    # Get current window size
    window_width = self.content_frame.winfo_width()
    window_height = self.content_frame.winfo_height()
    
    # Calculate scaling factors
    if window_width > 1600:  # Large screens
        font_scale = 1.1
        padding_scale = 1.2
    elif window_width < 1400:  # Small screens
        font_scale = 0.9
        padding_scale = 0.8
    else:  # Standard screens
        font_scale = 1.0
        padding_scale = 1.0
    
    # Apply scaling to components
    self.apply_component_scaling(font_scale, padding_scale)
```

## Integration with Existing Systems

### OrderManager Integration
```python
def integrate_with_order_manager(self):
    """Connect UI components to OrderManager"""
    # Connect tab switching
    self.order_manager.on_order_switched = self.on_order_switched
    
    # Connect order updates
    self.order_manager.on_order_updated = self.on_order_updated
    
    # Connect status changes
    self.order_manager.on_status_changed = self.on_status_changed

def on_order_switched(self, order_id):
    """Handle order switching from OrderManager"""
    # Update UI to reflect new active order
    self.refresh_current_order_display()
    self.update_status_buttons()
    self.update_totals_from_order_manager()

def on_order_updated(self, order_id):
    """Handle order updates from OrderManager"""
    # Update treeview if this is the current order
    if order_id == self.order_manager.current_order_id:
        self.refresh_order_display(order_id)
        self.update_totals_from_order_manager()
```

### Data Validation
```python
def validate_order_data(self):
    """Validate order data before processing"""
    current_order = self.order_manager.get_current_order()
    if not current_order:
        return False, "No active order"
    
    # Check items
    if not current_order['items']:
        return False, "Order has no items"
    
    # Check customer info for takeaway
    if current_order['order_type'] == 'Takeaway' and not current_order['customer_name']:
        return False, "Customer name required for takeaway orders"
    
    # Check table for dine-in
    if current_order['order_type'] == 'Dine-in' and not current_order['table_id']:
        return False, "Table selection required for dine-in orders"
    
    return True, "Order is valid"
```

## Performance Optimization

### Lazy Loading
```python
def setup_lazy_loading(self):
    """Setup lazy loading for performance optimization"""
    # Load menu items only when needed
    self.menu_items_loaded = False
    
    # Load tables only when order type is dine-in
    self.tables_loaded = False

def load_menu_items_lazy(self):
    """Load menu items only when first accessed"""
    if not self.menu_items_loaded:
        self.load_categories()
        self.menu_items_loaded = True

def load_tables_lazy(self):
    """Load tables only when dine-in is selected"""
    if not self.tables_loaded and self.order_type.get() == "Dine-in":
        self.load_tables()
        self.tables_loaded = True
```

### Event Throttling
```python
def setup_event_throttling(self):
    """Setup event throttling to prevent excessive updates"""
    self.update_pending = False
    self.update_queue = []

def throttled_update(self, update_func):
    """Throttle updates to prevent excessive UI refreshes"""
    if not self.update_pending:
        self.update_pending = True
        self.root.after(100, self._process_update_queue, update_func)

def _process_update_queue(self, update_func):
    """Process queued updates"""
    update_func()
    self.update_pending = False
    
    # Process any queued updates
    if self.update_queue:
        next_update = self.update_queue.pop(0)
        self.throttled_update(next_update)
```

This component architecture provides a comprehensive foundation for implementing the split-screen layout while maintaining all existing functionality and ensuring optimal performance.