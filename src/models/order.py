from src.utils.helpers import generate_order_number
from datetime import datetime

class Order:
    """Order model for order management"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, order_data):
        """Create a new order"""
        try:
            # Validate input
            if not order_data:
                raise ValueError("Order data is required")
            
            # Handle both dictionary and tuple inputs for backward compatibility
            if isinstance(order_data, dict):
                # Dictionary input
                order_number = order_data.get('order_number') or generate_order_number()
                table_id = order_data.get('table_id')
                customer_name = order_data.get('customer_name')
                customer_mobile = order_data.get('customer_mobile')
                order_type = order_data.get('order_type')
                subtotal = order_data.get('subtotal', 0)
                tax = order_data.get('tax', 0)
                discount = order_data.get('discount', 0)
                total = order_data.get('total', 0)
                items = order_data.get('items', [])
                payment_mode = order_data.get('payment_mode')
            else:
                # Legacy tuple support
                raise ValueError("Tuple input is not supported in this model. Please use dictionary format.")
            
            # Validate required fields
            if not order_number:
                raise ValueError("Order number is required")
            if not total or total <= 0:
                raise ValueError("Order total must be greater than 0")
            
            # Create order record
            order_query = """
            INSERT INTO orders (order_number, table_id, customer_name, customer_mobile, order_type,
                               subtotal, tax, discount, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(order_query, (
                order_number,
                table_id,
                customer_name,
                customer_mobile,
                order_type,
                subtotal,
                tax,
                discount,
                total,
                "Pending"  # Start with Pending status for KOT workflow
            ))
            
            order_id = self.db.lastrowid()
            
            if not order_id:
                raise ValueError("Failed to create order record")
            
            # Add order items
            if isinstance(order_data, dict) and items:
                for item in items:
                    # Validate item structure
                    if not isinstance(item, dict):
                        raise ValueError("Order items must be dictionaries")
                    
                    required_item_fields = ['id', 'quantity', 'price', 'total']
                    for field in required_item_fields:
                        if field not in item:
                            raise ValueError(f"Item missing required field: {field}")
                    
                    item_query = """
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price, total, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """
                    self.db.execute_query(item_query, (
                        order_id,
                        item['id'],
                        item['quantity'],
                        item['price'],
                        item['total'],
                        "Pending"  # Start with Pending status for KOT workflow
                    ))
                    
                    # Update inventory
                    self.db.execute_query(
                        "UPDATE menu_items SET stock_quantity = stock_quantity - ? WHERE id = ?",
                        (item['quantity'], item['id'])
                    )
            
            # Add payment record if payment mode is provided
            if isinstance(order_data, dict) and payment_mode:
                payment_query = """
                INSERT INTO payments (order_id, payment_mode, amount)
                VALUES (?, ?, ?)
                """
                self.db.execute_query(payment_query, (order_id, payment_mode, total))
            
            # Commit all changes
            self.db.commit()
            return order_id
            
        except Exception as e:
            # Rollback on error
            try:
                self.db.execute_query("ROLLBACK")
            except:
                pass
            print(f"Error creating order: {str(e)}")
            raise e
    
    def add_payment(self, order_id, payment_mode, amount):
        """Add payment record"""
        payment_query = """
        INSERT INTO payments (order_id, payment_mode, amount)
        VALUES (?, ?, ?)
        """
        self.db.execute_query(payment_query, (order_id, payment_mode, amount))
        self.db.commit()
        return order_id
    
    def add_item(self, order_id, menu_item_id, quantity, price, total, status="Completed"):
        """Add item to order"""
        query = """
        INSERT INTO order_items (order_id, menu_item_id, quantity, price, total, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (order_id, menu_item_id, quantity, price, total, status))
        self.db.commit()
    
    def get_all(self, filter_value="All", search_term=""):
        """Get orders with filtering"""
        query = """
        SELECT o.id, o.order_number, o.created_at, o.order_type, t.table_number, 
               o.total, o.status, o.customer_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE 1=1
        """
        params = []
        
        # Apply filter
        if filter_value == "Today":
            query += " AND DATE(o.created_at) = DATE('now')"
        elif filter_value == "This Week":
            query += " AND o.created_at >= DATE('now', '-7 days')"
        elif filter_value == "This Month":
            query += " AND o.created_at >= DATE('now', '-30 days')"
        
        # Apply search
        if search_term:
            query += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR t.table_number LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY o.created_at DESC"
        
        self.db.execute_query(query, params)
        return self.db.fetch_all()
    
    def get_details(self, order_id):
        """Get detailed order information"""
        # Get order details
        order_query = """
        SELECT o.order_number, o.table_id, o.customer_name, o.customer_mobile, o.order_type, 
               o.subtotal, o.tax, o.discount, o.total, o.created_at, o.status
        FROM orders o
        WHERE o.id = ?
        """
        self.db.execute_query(order_query, (order_id,))
        order = self.db.fetch_one()
        
        if not order:
            return None
        
        # Get order items
        items_query = """
        SELECT mi.name, oi.quantity, oi.price, oi.total, oi.status
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """
        self.db.execute_query(items_query, (order_id,))
        items = self.db.fetch_all()
        
        # Get payment details
        payment_query = """
        SELECT payment_mode, amount, created_at
        FROM payments
        WHERE order_id = ?
        """
        self.db.execute_query(payment_query, (order_id,))
        payments = self.db.fetch_all()
        
        return {
            'order': order,
            'items': items,
            'payments': payments
        }
    
    def get_details_by_number(self, order_number):
        """Get order details by order number"""
        # First get the order ID from the order number
        order_id_query = "SELECT id FROM orders WHERE order_number = ?"
        self.db.execute_query(order_id_query, (order_number,))
        result = self.db.fetch_one()
        
        if not result:
            return None
            
        order_id = result[0]
        
        # Use existing get_details method
        return self.get_details(order_id)
    
    def get_items_by_order_number(self, order_number):
        """Get order items by order number"""
        # First get the order ID from the order number
        order_id_query = "SELECT id FROM orders WHERE order_number = ?"
        self.db.execute_query(order_id_query, (order_number,))
        result = self.db.fetch_one()
        
        if not result:
            return []
            
        order_id = result[0]
        
        # Get order items
        items_query = """
        SELECT mi.name, oi.quantity, oi.price, oi.total, oi.status
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """
        
        self.db.execute_query(items_query, (order_id,))
        return self.db.fetch_all()
    
    def get_orders(self, filter_value="All", search_term=""):
        """Get orders with filtering"""
        query = """
        SELECT o.id, o.order_number, o.created_at, o.order_type, t.table_number, 
               o.total, o.status, o.customer_name
        FROM orders o
        LEFT JOIN tables t ON o.table_id = t.id
        WHERE 1=1
        """
        params = []
        
        # Apply filter
        if filter_value == "Today":
            query += " AND DATE(o.created_at) = DATE('now')"
        elif filter_value == "This Week":
            query += " AND o.created_at >= DATE('now', '-7 days')"
        elif filter_value == "This Month":
            query += " AND o.created_at >= DATE('now', '-30 days')"
        
        # Apply search
        if search_term:
            query += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR t.table_number LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY o.created_at DESC"
        
        self.db.execute_query(query, params)
        return self.db.fetch_all()
