from src.models.database import Table
from src.models.order import Order
from src.models.menu_item import MenuItem
from src.utils.helpers import generate_order_number, format_currency
from src.utils.event_dispatcher import event_dispatcher, EventType

class OrderController:
    """Controller for order-related operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.order_model = Order(db_manager)
        self.menu_item_model = MenuItem(db_manager)
        self.table_model = Table(db_manager)
        self.current_order = None
        self.cart_items = []
        self.selected_table = None
        self.order_type = "Dine-in"
    
    def reset_order(self):
        """Reset current order state"""
        self.current_order = None
        self.cart_items = []
        self.selected_table = None
        self.order_type = "Dine-in"
    
    def set_order_type(self, order_type):
        """Set order type (Dine-in or Takeaway)"""
        self.order_type = order_type
    
    def set_table(self, table_id):
        """Set selected table"""
        self.selected_table = table_id
    
    def add_to_cart(self, item_id, quantity):
        """Add item to cart"""
        # Validate inputs
        if not item_id or quantity <= 0:
            return False, "Invalid item ID or quantity"
            
        # Get item details
        item_data = self.menu_item_model.get_by_id(item_id)
        if not item_data:
            return False, "Item not found"
        
        # Ensure item_data has all expected fields
        if len(item_data) < 6:
            return False, "Invalid item data structure"
            
        # Handle both 6 and 7 field responses (category_name may or may not be included)
        if len(item_data) == 6:
            name, price, category_id, stock, image_path, category_name = item_data
        else:
            name, price, category_id, stock, image_path, shortcode, category_name = item_data
        
        # Check stock (handle both numeric and string values)
        try:
            stock_value = int(stock) if stock is not None else 0
            if stock_value <= 0:
                return False, f"{name} is out of stock"
        except (ValueError, TypeError):
            return False, f"{name} has invalid stock data"
        
        # Check if adding quantity exceeds stock
        existing_quantity = 0
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                existing_quantity = cart_item['quantity']
                break
        
        try:
            stock_value = int(stock) if stock is not None else 0
            if existing_quantity + quantity > stock_value:
                return False, f"Only {stock_value} items available in stock"
        except (ValueError, TypeError):
            return False, f"Invalid stock data for {name}"
        
        # Check if item already in cart
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                cart_item['quantity'] += quantity
                cart_item['total'] = cart_item['price'] * cart_item['quantity']
                return True, f"{name} updated in cart"
        
        # Add new item to cart
        self.cart_items.append({
            'id': item_id,
            'name': name,
            'price': price,
            'quantity': quantity,
            'total': price * quantity
        })
        
        return True, f"{name} added to cart"
    
    def update_cart_quantity(self, item_id, quantity):
        """Update quantity of item in cart"""
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                # Check stock
                item_data = self.menu_item_model.get_by_id(item_id)
                if item_data:
                    try:
                        stock_value = int(item_data[3]) if item_data[3] is not None else 0
                        if quantity <= stock_value:
                            cart_item['quantity'] = quantity
                            cart_item['total'] = cart_item['price'] * cart_item['quantity']
                            return True, "Cart updated"
                        else:
                            return False, f"Only {stock_value} items available in stock"
                    except (ValueError, TypeError):
                        return False, "Invalid stock data"
                else:
                    return False, "Item not found"
        return False, "Item not found in cart"
    
    def remove_from_cart(self, item_id):
        """Remove item from cart"""
        initial_count = len(self.cart_items)
        self.cart_items = [item for item in self.cart_items if item['id'] != item_id]
        return len(self.cart_items) < initial_count
    
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart_items = []
    
    def calculate_totals(self, discount_value=0, discount_type="%"):
        """Calculate order totals with GST breakdown"""
        subtotal = sum(item['total'] for item in self.cart_items)
        
        # GST calculation (5% total: 2.5% CGST + 2.5% SGST)
        gst_rate = 5.0 / 100  # 5% total GST
        cgst_rate = 2.5 / 100  # 2.5% CGST
        sgst_rate = 2.5 / 100  # 2.5% SGST
        
        cgst_amount = subtotal * cgst_rate
        sgst_amount = subtotal * sgst_rate
        total_tax = cgst_amount + sgst_amount
        
        if discount_type == "%":
            discount = subtotal * (discount_value / 100)
        else:  # Flat
            discount = discount_value
        
        total = subtotal + total_tax - discount
        
        return {
            'subtotal': subtotal,
            'tax': total_tax,  # For backward compatibility
            'cgst_amount': cgst_amount,
            'sgst_amount': sgst_amount,
            'total_tax': total_tax,
            'gst_rate': 5.0,
            'discount': discount,
            'total': total
        }
    
    def process_payment(self, payment_mode, discount_value=0, discount_type="%",
                     customer_name=None, customer_mobile=None, 
                     auto_export=False, export_format=None):
        """Process payment and create order"""
        # Validate cart state
        if not self.cart_items:
            return False, "Cart is empty"
        
        # Validate order type and table selection
        if self.order_type == "Dine-in" and not self.selected_table:
            return False, "Please select a table"
        
        # Validate payment mode
        if not payment_mode:
            return False, "Invalid payment mode"
        
        try:
            # Calculate totals
            totals = self.calculate_totals(discount_value, discount_type)
            
            # Generate order number
            order_number = generate_order_number()
            
            # Create order data with order_number included
            order_data = {
                'order_number': order_number,  # Include order_number in the data
                'table_id': self.selected_table,
                'customer_name': customer_name,
                'customer_mobile': customer_mobile,
                'order_type': self.order_type,
                'subtotal': totals['subtotal'],
                'tax': totals['tax'],
                'cgst_amount': totals['cgst_amount'],
                'sgst_amount': totals['sgst_amount'],
                'total_tax': totals['total_tax'],
                'gst_rate': totals['gst_rate'],
                'discount': totals['discount'],
                'total': totals['total'],
                'payment_mode': payment_mode,
                'items': self.cart_items.copy()  # Add items to order data
            }
            
            # Create order
            order_id = self.order_model.create(order_data)
            
            if not order_id:
                return False, "Failed to create order"
            
            # Add payment record
            self.order_model.add_payment(order_id, payment_mode, totals['total'])
            
            # Update table status if dine-in
            if self.order_type == "Dine-in":
                self.table_model.update_status(self.selected_table, "Occupied")
            
            # Emit events for real-time updates
            event_dispatcher.order_created(order_number, {
                'order_type': self.order_type,
                'table_id': self.selected_table,
                'items': self.cart_items.copy(),
                'totals': totals
            })
            
            # Emit inventory updates for each item
            for cart_item in self.cart_items:
                item_data = self.menu_item_model.get_by_id(cart_item['id'])
                if item_data:
                    new_stock = item_data[3] - cart_item['quantity']  # stock is at index 3
                    event_dispatcher.inventory_updated(cart_item['id'], new_stock)
            
            # Emit table status change if dine-in
            if self.order_type == "Dine-in":
                event_dispatcher.table_status_changed(self.selected_table, "Occupied")
            
            # Reset order
            self.reset_order()
            
            # Return success with order details for potential export
            return True, {
                'order_number': order_number,
                'order_id': order_id,
                'order_data': order_data,
                'totals': totals
            }
            
        except Exception as e:
            return False, f"Payment processing failed: {str(e)}"
    
    def get_menu_items(self, search_term="", category="All"):
        """Get menu items for display"""
        return self.menu_item_model.get_all(search_term, category)
    
    def get_available_tables(self):
        """Get available tables"""
        return self.table_model.get_available()
    
    def get_categories(self):
        """Get all categories"""
        from src.models.database import Category
        category_model = Category(self.db)
        return category_model.get_all()