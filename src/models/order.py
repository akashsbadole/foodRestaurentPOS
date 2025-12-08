from ..utils.helpers import generate_order_number
from datetime import datetime

class Order:
    """Order model for order management"""
    
    def __init__(self, db):
        self.db = db
    
    def create(self, order_data):
        """Create a new order"""
        order_number = generate_order_number()
        
        # Create order record
        order_query = """
        INSERT INTO orders (order_number, table_id, customer_name, customer_mobile, order_type, 
                           subtotal, tax, discount, total, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.db.execute(order_query, (
            order_number,
            order_data.get('table_id'),
            order_data.get('customer_name'),
            order_data.get('customer_mobile'),
            order_data.get('order_type'),
            order_data.get('subtotal'),
            order_data.get('tax'),
            order_data.get('discount'),
            order_data.get('total'),
            "Completed"
        ))
        
        order_id = self.db.lastrowid()
        
        # Add order items
        for item in order_data.get('items', []):
            item_query = """
            INSERT INTO order_items (order_id, menu_item_id, quantity, price, total, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute(item_query, (
                order_id,
                item['id'],
                item['quantity'],
                item['price'],
                item['total'],
                "Completed"
            ))
            
            # Update inventory
            self.db.execute(
                "UPDATE menu_items SET stock_quantity = stock_quantity - ? WHERE id = ?",
                (item['quantity'], item['id'])
            )
        
        # Add payment record
        payment_query = """
        INSERT INTO payments (order_id, payment_mode, amount)
        VALUES (?, ?, ?)
        """
        self.db.execute(payment_query, (order_id, order_data.get('payment_mode'), order_data.get('total')))
        
        # Update table status if dine-in
        if order_data.get('order_type') == 'Dine-in' and order_data.get('table_id'):
            self.db.execute(
                "UPDATE tables SET status = 'Occupied' WHERE id = ?",
                (order_data.get('table_id'),)
            )
        
        self.db.commit()
        return order_id
    
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
        
        return self.db.fetch_all(query, params)
    
    def get_details(self, order_id):
        """Get detailed order information"""
        # Get order details
        order_query = """
        SELECT o.order_number, o.table_id, o.customer_name, o.customer_mobile, o.order_type, 
               o.subtotal, o.tax, o.discount, o.total, o.created_at, o.status
        FROM orders o
        WHERE o.id = ?
        """
        order = self.db.fetch_one(order_query, (order_id,))
        
        if not order:
            return None
        
        # Get order items
        items_query = """
        SELECT mi.name, oi.quantity, oi.price, oi.total, oi.status
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """
        items = self.db.fetch_all(items_query, (order_id,))
        
        # Get payment details
        payment_query = """
        SELECT payment_mode, amount, created_at
        FROM payments
        WHERE order_id = ?
        """
        payments = self.db.fetch_all(payment_query, (order_id,))
        
        return {
            'order': order,
            'items': items,
            'payments': payments
        }
