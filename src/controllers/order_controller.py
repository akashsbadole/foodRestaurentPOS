from ..models.database import Order, MenuItem, Table
from ..utils.helpers import generate_order_number, format_currency

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
        # Get item details
        item_data = self.menu_item_model.get_by_id(item_id)
        if not item_data:
            return False, "Item not found"
        
        name, price, category_id, stock, image_path, category_name = item_data
        
        # Check stock
        if stock <= 0:
            return False, f"{name} is out of stock"
        
        # Check if adding quantity exceeds stock
        existing_quantity = 0
        for cart_item in self.cart_items:
            if cart_item['id'] == item_id:
                existing_quantity = cart_item['quantity']
                break
        
        if existing_quantity + quantity > stock:
            return False, f"Only {stock} items available in stock"
        
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
                if item_data and quantity <= item_data[3]:  # stock is at index 3
                    cart_item['quantity'] = quantity
                    cart_item['total'] = cart_item['price'] * quantity
                    return True, "Cart updated"
                else:
                    return False, f"Only {item_data[3]} items available in stock"
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
        """Calculate order totals"""
        subtotal = sum(item['total'] for item in self.cart_items)
        tax_rate = 5.0 / 100  # Default 5% tax
        tax = subtotal * tax_rate
        
        if discount_type == "%":
            discount = subtotal * (discount_value / 100)
        else:  # Flat
            discount = discount_value
        
        total = subtotal + tax - discount
        
        return {
            'subtotal': subtotal,
            'tax': tax,
            'discount': discount,
            'total': total
        }
    
    def process_payment(self, payment_mode, discount_value=0, discount_type="%", 
                     customer_name=None, customer_mobile=None):
        """Process payment and create order"""
        if not self.cart_items:
            return False, "Cart is empty"
        
        if self.order_type == "Dine-in" and not self.selected_table:
            return False, "Please select a table"
        
        # Calculate totals
        totals = self.calculate_totals(discount_value, discount_type)
        
        # Generate order number
        order_number = generate_order_number()
        
        # Create order data
        order_data = (
            order_number,
            self.selected_table,
            customer_name,
            customer_mobile,
            self.order_type,
            totals['subtotal'],
            totals['tax'],
            totals['discount'],
            totals['total'],
            "Completed"
        )
        
        # Create order
        order_id = self.order_model.create(order_data)
        
        # Add order items
        for cart_item in self.cart_items:
            self.order_model.add_item(
                order_id,
                cart_item['id'],
                cart_item['quantity'],
                cart_item['price'],
                cart_item['total'],
                "Completed"
            )
            
            # Update inventory
            self.menu_item_model.update_stock(
                cart_item['id'],
                cart_item['quantity'] * -1  # Subtract from stock
            )
        
        # Add payment record
        self.order_model.add_payment(order_id, payment_mode, totals['total'])
        
        # Update table status if dine-in
        if self.order_type == "Dine-in":
            self.table_model.update_status(self.selected_table, "Occupied")
        
        # Reset order
        self.reset_order()
        
        return True, order_number
    
    def get_menu_items(self, search_term="", category="All"):
        """Get menu items for display"""
        return self.menu_item_model.get_all(search_term, category)
    
    def get_available_tables(self):
        """Get available tables"""
        return self.table_model.get_available()
    
    def get_categories(self):
        """Get all categories"""
        from ..models.database import Category
        category_model = Category(self.db)
        return category_model.get_all()
