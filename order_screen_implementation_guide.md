# Order Screen Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the new split-screen layout for the order screen. The implementation should be done in phases to ensure proper testing and integration.

## Phase 1: Foundation Setup

### Step 1.1: Create New OrderScreen Class Structure
1. **Backup Current Implementation**
   ```bash
   cp src/ui/order_screen.py src/ui/order_screen_backup.py
   ```

2. **Create New Class Structure**
   - Keep existing `OrderScreen` class as base
   - Add new methods for split-screen layout
   - Maintain backward compatibility during transition

3. **Update Constructor**
   ```python
   def __init__(self, root, app):
       super().__init__(root, app)
       # Existing initialization code...
       
       # New layout properties
       self.left_panel = None
       self.right_panel = None
       self.header_frame = None
       self.paned_window = None
       
       # Layout constants
       self.HEADER_HEIGHT = 60
       self.LEFT_PANEL_RATIO = 0.6  # 60%
       self.RIGHT_PANEL_RATIO = 0.4  # 40%
   ```

### Step 1.2: Setup Responsive Layout Framework
1. **Add Screen Size Detection**
   ```python
   def setup_responsive_layout(self):
       """Setup responsive layout for different screen sizes"""
       screen_width = self.root.winfo_screenwidth()
       screen_height = self.root.winfo_screenheight()
       
       # Set minimum window size
       min_width, min_height = 1280, 720
       self.root.minsize(min_width, min_height)
       
       # Center window
       x = (screen_width - min_width) // 2
       y = (screen_height - min_height) // 2
       self.root.geometry(f"{min_width}x{min_height}+{x}+{y}")
   ```

2. **Create Layout Manager**
   ```python
   def create_split_layout(self):
       """Create main split-screen layout"""
       # Clear existing content
       self.clear_content_frame()
       
       # Create main container
       self.main_frame = ttk.Frame(self.content_frame)
       self.main_frame.pack(fill=tk.BOTH, expand=True)
       
       # Create header
       self.create_header()
       
       # Create split panels
       self.paned_window = ttk.PanedWindow(
           self.main_frame, 
           orient=tk.HORIZONTAL
       )
       self.paned_window.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
       
       # Create panels
       self.create_panels()
   ```

## Phase 2: Header Implementation

### Step 2.1: Create Top Header Frame
1. **Header Structure**
   ```python
   def create_header(self):
       """Create top header with tabs and user info"""
       self.header_frame = ttk.Frame(self.main_frame, height=self.HEADER_HEIGHT)
       self.header_frame.pack(fill=tk.X, pady=(0, 10))
       self.header_frame.pack_propagate(False)  # Prevent height change
       
       # Create left side (tabs)
       self.create_tab_container()
       
       # Create right side (user info)
       self.create_user_info()
   ```

2. **Tab Container Implementation**
   ```python
   def create_tab_container(self):
       """Create browser-style tab container"""
       # Left side frame
       self.tab_bar_frame = ttk.Frame(self.header_frame)
       self.tab_bar_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
       
       # New Order button
       self.new_order_btn = ttk.Button(
           self.tab_bar_frame,
           text="+ New Order",
           command=self.new_order,
           style='Accent.TButton'
       )
       self.new_order_btn.pack(side=tk.LEFT, padx=(0, 5))
       
       # Tabs container
       self.tabs_container = ttk.Frame(self.tab_bar_frame)
       self.tabs_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
   ```

3. **User Info Implementation**
   ```python
   def create_user_info(self):
       """Create user profile section"""
       # Right side frame
       self.user_frame = ttk.Frame(self.header_frame)
       self.user_frame.pack(side=tk.RIGHT, padx=5, pady=5)
       
       # User label
       username = self.app.current_user.get('username', 'Admin')
       role = self.app.current_user.get('role', 'Admin')
       self.user_label = ttk.Label(
           self.user_frame,
           text=f"User: {username} ({role})",
           font=('Arial', 10)
       )
       self.user_label.pack(side=tk.LEFT, padx=(0, 10))
       
       # Logout button
       self.logout_btn = ttk.Button(
           self.user_frame,
           text="Logout",
           command=self.logout
       )
       self.logout_btn.pack(side=tk.LEFT)
   ```

### Step 2.2: Migrate Tab System
1. **Update Tab Creation Method**
   ```python
   def create_browser_tab(self, order_id: str):
       """Create browser-style tab for order"""
       order = self.order_manager.get_order(order_id)
       if not order:
           return
       
       # Tab container
       tab_container = ttk.Frame(self.tabs_container)
       tab_container.pack(side=tk.LEFT, padx=(0, 2))
       
       # Tab button
       tab_text = f"{order['order_number']}"
       if len(order['items']) > 0:
           tab_text += f" ({len(order['items'])})"
       
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
       
       # Store references
       if not hasattr(self, 'browser_tabs'):
           self.browser_tabs = {}
       self.browser_tabs[order_id] = {
           'container': tab_container,
           'button': tab_btn,
           'close_btn': close_btn
       }
       
       return tab_container
   ```

## Phase 3: Left Panel Implementation

### Step 3.1: Create Panel Structure
1. **Panel Creation**
   ```python
   def create_panels(self):
       """Create left and right panels"""
       # Left panel (60%)
       self.left_panel = ttk.Frame(self.paned_window)
       self.paned_window.add(self.left_panel, weight=6)
       
       # Right panel (40%)
       self.right_panel = ttk.Frame(self.paned_window)
       self.paned_window.add(self.right_panel, weight=4)
       
       # Create components in each panel
       self.create_left_panel_components()
       self.create_right_panel_components()
   ```

2. **Left Panel Components**
   ```python
   def create_left_panel_components(self):
       """Create all left panel components"""
       # Customer details frame
       self.create_customer_details_frame()
       
       # Item selection frame
       self.create_item_selection_frame()
       
       # Status control frame
       self.create_status_control_frame()
   ```

### Step 3.2: Customer Details Frame (2x2 Grid)
1. **Frame Structure**
   ```python
   def create_customer_details_frame(self):
       """Create customer details in 2x2 grid layout"""
       self.customer_frame = ttk.LabelFrame(
           self.left_panel, 
           text="Customer Info", 
           padding=10
       )
       self.customer_frame.pack(fill=tk.X, pady=(0, 10))
       
       # Order type (row 0, col 0-1)
       ttk.Label(self.customer_frame, text="Order Type:").grid(
           row=0, column=0, sticky=tk.W, padx=5
       )
       
       self.dine_radio = ttk.Radiobutton(
           self.customer_frame, 
           text="Dine-in", 
           variable=self.order_type, 
           value="Dine-in",
           command=self.on_order_type_changed
       )
       self.dine_radio.grid(row=0, column=1, sticky=tk.W, padx=5)
       
       self.takeaway_radio = ttk.Radiobutton(
           self.customer_frame, 
           text="Takeaway", 
           variable=self.order_type, 
           value="Takeaway",
           command=self.on_order_type_changed
       )
       self.takeaway_radio.grid(row=0, column=2, sticky=tk.W, padx=5)
       
       # Table selection (row 0, col 3)
       ttk.Label(self.customer_frame, text="Table:").grid(
           row=0, column=3, sticky=tk.W, padx=5
       )
       self.table_combo = ttk.Combobox(
           self.customer_frame, 
           width=15, 
           state="readonly"
       )
       self.table_combo.grid(row=0, column=4, padx=5, sticky=tk.W)
       self.table_combo.bind("<<ComboboxSelected>>", self.on_table_changed)
       
       # Customer name (row 1, col 0-2)
       ttk.Label(self.customer_frame, text="Name:").grid(
           row=1, column=0, sticky=tk.W, padx=5
       )
       self.customer_entry = ttk.Entry(self.customer_frame, width=25)
       self.customer_entry.grid(
           row=1, column=1, columnspan=2, 
           padx=5, sticky=tk.W+tk.E
       )
       self.customer_entry.bind("<KeyRelease>", self.on_customer_info_changed)
       
       # Mobile number (row 1, col 3-4)
       ttk.Label(self.customer_frame, text="Mobile:").grid(
           row=1, column=3, sticky=tk.W, padx=5
       )
       self.mobile_entry = ttk.Entry(self.customer_frame, width=15)
       self.mobile_entry.grid(
           row=1, column=4, 
           padx=5, sticky=tk.W+tk.E
       )
       self.mobile_entry.bind("<KeyRelease>", self.on_customer_info_changed)
   ```

### Step 3.3: Item Selection Frame
1. **Compact Item Selection**
   ```python
   def create_item_selection_frame(self):
       """Create compact item selection frame"""
       self.item_frame = ttk.LabelFrame(
           self.left_panel, 
           text="Add Items", 
           padding=10
       )
       self.item_frame.pack(fill=tk.X, pady=(0, 10))
       
       # Row 0: Category | Item | Quantity | Add
       self.category_combo = ttk.Combobox(
           self.item_frame, 
           width=20, 
           state="readonly"
       )
       self.category_combo.grid(row=0, column=0, padx=5, sticky=tk.W)
       self.category_combo.bind("<<ComboboxSelected>>", self.on_category_changed)
       
       self.menu_combo = ttk.Combobox(
           self.item_frame, 
           width=35, 
           state="readonly"
       )
       self.menu_combo.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
       
       self.quantity_var = tk.StringVar(value="1")
       self.quantity_spin = ttk.Spinbox(
           self.item_frame, 
           from_=1, to=99, 
           textvariable=self.quantity_var, 
           width=8
       )
       self.quantity_spin.grid(row=0, column=2, padx=5)
       
       self.add_btn = ttk.Button(
           self.item_frame, 
           text="ADD", 
           command=self.add_item,
           width=10
       )
       self.add_btn.grid(row=0, column=3, padx=5)
       
       # Row 1: Search | Clear | Clear Order
       self.search_var = tk.StringVar()
       self.search_entry = ttk.Entry(
           self.item_frame, 
           textvariable=self.search_var
       )
       self.search_entry.grid(
           row=1, column=0, columnspan=2, 
           padx=5, pady=5, sticky=tk.W+tk.E
       )
       self.search_entry.bind("<KeyRelease>", self.search_menu_items)
       
       self.clear_search_btn = ttk.Button(
           self.item_frame, 
           text="Clear", 
           command=self.clear_menu_search
       )
       self.clear_search_btn.grid(row=1, column=2, padx=5, pady=5)
       
       self.clear_order_btn = ttk.Button(
           self.item_frame, 
           text="Clear Order", 
           command=self.clear_current_order
       )
       self.clear_order_btn.grid(row=1, column=3, padx=5, pady=5)
   ```

### Step 3.4: Status Control Strip
1. **Status Buttons**
   ```python
   def create_status_control_frame(self):
       """Create status control strip with clickable buttons"""
       self.status_frame = ttk.LabelFrame(
           self.left_panel, 
           text="Order Status", 
           padding=10
       )
       self.status_frame.pack(fill=tk.X, pady=(0, 10))
       
       # Status buttons
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

2. **Status Control Logic**
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
       self.order_manager.update_order_status(
           self.order_manager.current_order_id, 
           status
       )
       
       # Update button appearances
       self.update_status_buttons()
       
       # Refresh displays
       self.refresh_orders_list()
   
   def update_status_buttons(self):
       """Update status button appearances"""
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

## Phase 4: Right Panel Implementation

### Step 4.1: Active Orders Treeview
1. **Treeview Structure**
   ```python
   def create_right_panel_components(self):
       """Create all right panel components"""
       # Active orders frame
       self.create_active_orders_frame()
       
       # Financial breakdown frame
       self.create_financial_breakdown_frame()
       
       # Action buttons frame
       self.create_action_buttons_frame()
   
   def create_active_orders_frame(self):
       """Create active orders treeview"""
       self.orders_frame = ttk.LabelFrame(
           self.right_panel, 
           text="Active Orders", 
           padding=10
       )
       self.orders_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
       
       # Create treeview
       self.order_tree = ttk.Treeview(
           self.orders_frame,
           columns=("item", "quantity", "price", "total"),
           show="headings",
           height=8
       )
       
       # Configure columns
       self.order_tree.heading("item", text="Item")
       self.order_tree.heading("quantity", text="Qty")
       self.order_tree.heading("price", text="Price")
       self.order_tree.heading("total", text="Total")
       
       self.order_tree.column("item", width=200)
       self.order_tree.column("quantity", width=60)
       self.order_tree.column("price", width=80)
       self.order_tree.column("total", width=80)
       
       self.order_tree.pack(fill=tk.BOTH, expand=True)
       
       # Add scrollbar
       scrollbar = ttk.Scrollbar(
           self.orders_frame, 
           orient=tk.VERTICAL, 
           command=self.order_tree.yview
       )
       self.order_tree.configure(yscrollcommand=scrollbar.set)
       scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
       
       # Info strip
       self.info_label = ttk.Label(
           self.orders_frame,
           text="Items: 0 | Status: New",
           font=('Arial', 9, 'bold')
       )
       self.info_label.pack(fill=tk.X, pady=(5, 0))
       
       # Right click menu
       self.order_tree.bind("<Button-3>", self.show_item_context_menu)
   ```

### Step 4.2: Financial Breakdown (Receipt-style)
1. **Right-aligned Financial Display**
   ```python
   def create_financial_breakdown_frame(self):
       """Create receipt-style financial breakdown"""
       self.financial_frame = ttk.Frame(self.right_panel)
       self.financial_frame.pack(fill=tk.X, pady=(0, 10))
       
       # Right-aligned labels
       self.subtotal_label = ttk.Label(
           self.financial_frame, 
           text="Subtotal:     Rs.0.00", 
           font=('Arial', 10)
       )
       self.subtotal_label.pack(anchor=tk.E, pady=2)
       
       self.cgst_label = ttk.Label(
           self.financial_frame, 
           text="CGST (2.5%):  Rs.0.00", 
           font=('Arial', 9)
       )
       self.cgst_label.pack(anchor=tk.E, pady=1)
       
       self.sgst_label = ttk.Label(
           self.financial_frame, 
           text="SGST (2.5%):  Rs.0.00", 
           font=('Arial', 9)
       )
       self.sgst_label.pack(anchor=tk.E, pady=1)
       
       self.discount_label = ttk.Label(
           self.financial_frame, 
           text="Discount:   - Rs.0.00", 
           font=('Arial', 10)
       )
       self.discount_label.pack(anchor=tk.E, pady=2)
       
       # Separator
       separator = ttk.Separator(self.financial_frame, orient='horizontal')
       separator.pack(fill=tk.X, pady=5)
       
       self.total_label = ttk.Label(
           self.financial_frame, 
           text="TOTAL:        Rs.0.00", 
           font=('Arial', 12, 'bold')
       )
       self.total_label.pack(anchor=tk.E, pady=2)
   ```

### Step 4.3: Action Buttons
1. **Horizontal Button Row**
   ```python
   def create_action_buttons_frame(self):
       """Create action buttons row"""
       self.action_frame = ttk.Frame(self.right_panel)
       self.action_frame.pack(fill=tk.X)
       
       # Discount button
       self.discount_btn = ttk.Button(
           self.action_frame,
           text="Apply Discount",
           command=self.apply_discount,
           width=15
       )
       self.discount_btn.pack(side=tk.LEFT, padx=5)
       
       # Export button
       self.export_btn = ttk.Button(
           self.action_frame,
           text="Export Order",
           command=self.export_order,
           width=15
       )
       self.export_btn.pack(side=tk.LEFT, padx=5)
       
       # Process payment button (emphasized)
       self.payment_btn = ttk.Button(
           self.action_frame,
           text="PROCESS PAYMENT",
           command=self.process_payment,
           width=18,
           style='Accent.TButton'
       )
       self.payment_btn.pack(side=tk.RIGHT, padx=5)
   ```

## Phase 5: Integration and Testing

### Step 5.1: Update Main Setup Method
1. **Replace setup_ui() Method**
   ```python
   def setup_ui(self):
       """Setup order screen UI with new split-screen layout"""
       # Setup responsive layout
       self.setup_responsive_layout()
       
       # Create split layout
       self.create_split_layout()
       
       # Configure styles
       self.configure_styles()
       
       # Load initial data
       self.load_initial_data()
       
       # Initialize orders
       self.initialize_orders()
   ```

2. **Style Configuration**
   ```python
   def configure_styles(self):
       """Configure styles for new layout"""
       style = ttk.Style()
       
       # Tab styles
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
       
       # Status button styles
       style.configure('ActiveStatus.TButton',
                    font=('Arial', 9, 'bold'),
                    relief='flat',
                    background='#0078d7',
                    foreground='white')
       
       # Accent button style
       style.configure('Accent.TButton',
                    font=('Arial', 9, 'bold'),
                    padding=(8, 4),
                    relief='flat',
                    background='#28a745',
                    foreground='white')
   ```

### Step 5.2: Data Loading and Initialization
1. **Load Initial Data**
   ```python
   def load_initial_data(self):
       """Load initial data for components"""
       # Load categories
       self.load_categories()
       
       # Load tables
       self.load_tables()
       
       # Setup event handlers
       self.setup_event_handlers()
   
   def setup_event_handlers(self):
       """Setup event handlers for components"""
       # Order manager events
       self.order_manager.on_order_switched = self.on_order_switched
       self.order_manager.on_order_updated = self.on_order_updated
       self.order_manager.on_status_changed = self.on_status_changed
   ```

### Step 5.3: Testing Checklist
1. **Functional Testing**
   - [ ] All tabs switch correctly
   - [ ] Order creation works
   - [ ] Item addition/removal works
   - [ ] Status updates work
   - [ ] Payment processing works
   - [ ] Export functionality works
   - [ ] Search functionality works
   - [ ] Discount application works

2. **Layout Testing**
   - [ ] No scrolling required on 1280×720
   - [ ] No scrolling required on 1920×1080
   - [ ] Components scale properly
   - [ ] Responsive layout works
   - [ ] All buttons are accessible
   - [ ] All text is readable

3. **Integration Testing**
   - [ ] OrderManager integration works
   - [ ] Database operations work
   - [ ] Event system works
   - [ ] Export system works
   - [ ] Payment system works

## Phase 6: Deployment

### Step 6.1: Final Testing
1. **Performance Testing**
   - Test with 10+ active orders
   - Test with large item lists
   - Test memory usage
   - Test response times

2. **User Acceptance Testing**
   - Test with real restaurant data
   - Test with different user roles
   - Test with different workflows
   - Gather user feedback

### Step 6.2: Documentation
1. **Update Documentation**
   - Update user manual
   - Update technical documentation
   - Create training materials
   - Update help files

2. **Deployment Checklist**
   - [ ] Backup current system
   - [ ] Deploy new version
   - [ ] Verify all functionality
   - [ ] Monitor performance
   - [ ] Collect user feedback

## Troubleshooting Guide

### Common Issues

1. **Layout Problems**
   - **Issue**: Components overlapping
   - **Solution**: Check pack/grid order and weights
   - **Code**: `self.paned_window.add(panel, weight=X)`

2. **Scrolling Issues**
   - **Issue**: Still requires scrolling
   - **Solution**: Check component heights and padding
   - **Code**: Reduce padding or component heights

3. **Tab Issues**
   - **Issue**: Tabs not switching
   - **Solution**: Check event handlers and order manager integration
   - **Code**: Verify `switch_to_order_tab()` method

4. **Status Issues**
   - **Issue**: Status buttons not updating
   - **Solution**: Check status button update logic
   - **Code**: Verify `update_status_buttons()` method

### Debug Commands

1. **Check Layout Structure**
   ```python
   print("Left panel size:", self.left_panel.winfo_width(), self.left_panel.winfo_height())
   print("Right panel size:", self.right_panel.winfo_width(), self.right_panel.winfo_height())
   ```

2. **Check Order Manager State**
   ```python
   print("Current order:", self.order_manager.get_current_order())
   print("All orders:", self.order_manager.get_all_orders())
   ```

3. **Check Component References**
   ```python
   print("Status buttons:", self.status_buttons)
   print("Browser tabs:", self.browser_tabs)
   ```

This implementation guide provides a comprehensive roadmap for implementing the new split-screen layout while maintaining all existing functionality and ensuring proper testing and deployment.