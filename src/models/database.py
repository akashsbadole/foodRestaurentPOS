import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    """Database connection and operations manager"""
    
    def __init__(self, db_path='restaurant_pos.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def commit(self):
        """Commit database transaction"""
        if self.conn:
            self.conn.commit()
    
    def execute_query(self, query, params=None):
        """Execute a database query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    
    def execute_many(self, query, params_list):
        """Execute query with multiple parameter sets"""
        try:
            self.cursor.executemany(query, params_list)
            return True
        except Exception as e:
            print(f"Error executing many queries: {e}")
            return False
    
    def fetch_one(self):
        """Fetch one row from last query"""
        if self.cursor:
            return self.cursor.fetchone()
        return None
    
    def fetch_all(self):
        """Fetch all rows from last query"""
        if self.cursor:
            return self.cursor.fetchall()
        return None
    
    def lastrowid(self):
        """Get last inserted row ID"""
        if self.cursor:
            return self.cursor.lastrowid
        return None

class User:
    """User model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def authenticate(self, username, password):
        """Authenticate user credentials"""
        from src.utils.helpers import hash_password
        hashed_password = hash_password(password)
        
        query = "SELECT id, username, role FROM users WHERE username = ? AND password = ?"
        self.db.execute_query(query, (username, hashed_password))
        return self.db.fetch_one()
    
    def get_all(self):
        """Get all users"""
        query = "SELECT username, role FROM users ORDER BY username"
        self.db.execute_query(query)
        return self.db.fetch_all()
    
    def add(self, username, password, role):
        """Add new user"""
        from src.utils.helpers import hash_password
        hashed_password = hash_password(password)
        
        query = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
        try:
            self.db.execute_query(query, (username, hashed_password, role))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def delete(self, username):
        """Delete user"""
        query = "DELETE FROM users WHERE username = ?"
        self.db.execute_query(query, (username,))
        self.db.commit()

class Category:
    """Category model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all(self):
        """Get all categories"""
        query = "SELECT id, name FROM categories ORDER BY name"
        self.db.execute_query(query)
        return self.db.fetch_all()
    
    def add(self, name):
        """Add new category"""
        query = "INSERT INTO categories (name) VALUES (?)"
        try:
            self.db.execute_query(query, (name,))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update(self, category_id, name):
        """Update category"""
        query = "UPDATE categories SET name = ? WHERE id = ?"
        try:
            self.db.execute_query(query, (name, category_id))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def delete(self, category_id):
        """Delete category"""
        query = "DELETE FROM categories WHERE id = ?"
        self.db.execute_query(query, (category_id,))
        self.db.commit()
    
    def get_item_count(self, category_id):
        """Get count of menu items in category"""
        query = "SELECT COUNT(*) FROM menu_items WHERE category_id = ?"
        self.db.execute_query(query, (category_id,))
        result = self.db.fetch_one()
        return result[0] if result else 0


class Table:
    """Table model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all(self):
        """Get all tables"""
        query = "SELECT id, table_number, capacity, status FROM tables ORDER BY table_number"
        self.db.execute_query(query)
        return self.db.fetch_all()
    
    def get_available(self):
        """Get available tables"""
        query = "SELECT id, table_number FROM tables WHERE status = 'Available' ORDER BY table_number"
        self.db.execute_query(query)
        return self.db.fetch_all()
    
    def add(self, table_number, capacity):
        """Add new table"""
        query = "INSERT INTO tables (table_number, capacity) VALUES (?, ?)"
        try:
            self.db.execute_query(query, (table_number, capacity))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def update(self, table_id, table_number, capacity, status):
        """Update table"""
        query = """
        UPDATE tables 
        SET table_number = ?, capacity = ?, status = ?
        WHERE id = ?
        """
        try:
            self.db.execute_query(query, (table_number, capacity, status, table_id))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def delete(self, table_id):
        """Delete table"""
        query = "DELETE FROM tables WHERE id = ?"
        self.db.execute_query(query, (table_id,))
        self.db.commit()
    
    def update_status(self, table_id, status):
        """Update table status"""
        query = "UPDATE tables SET status = ? WHERE id = ?"
        self.db.execute_query(query, (status, table_id))
        self.db.commit()
    
    def reset_all(self):
        """Reset all tables to Available"""
        query = "UPDATE tables SET status = 'Available'"
        self.db.execute_query(query)
        self.db.commit()

class Order:
    """Order model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create(self, order_data):
        """Create new order"""
        try:
            # Validate input
            if not order_data:
                raise ValueError("Order data is required")
            
            # Handle both dictionary and tuple inputs for backward compatibility
            if isinstance(order_data, dict):
                # Dictionary input
                order_number = order_data.get('order_number')
                table_id = order_data.get('table_id')
                customer_name = order_data.get('customer_name')
                customer_mobile = order_data.get('customer_mobile')
                order_type = order_data.get('order_type')
                subtotal = order_data.get('subtotal', 0)
                tax = order_data.get('tax', 0)
                discount = order_data.get('discount', 0)
                total = order_data.get('total', 0)
                status = order_data.get('status', "Pending")  # Default status for KOT workflow
                items = order_data.get('items', [])
                payment_mode = order_data.get('payment_mode')
            else:
                # Legacy tuple support
                if len(order_data) < 1:
                    raise ValueError("Order data tuple is missing required fields")
                order_number = order_data[0]
                table_id = order_data[1] if len(order_data) > 1 else None
                customer_name = order_data[2] if len(order_data) > 2 else None
                customer_mobile = order_data[3] if len(order_data) > 3 else None
                order_type = order_data[4] if len(order_data) > 4 else None
                subtotal = order_data[5] if len(order_data) > 5 else None
                tax = order_data[6] if len(order_data) > 6 else None
                discount = order_data[7] if len(order_data) > 7 else None
                total = order_data[8] if len(order_data) > 8 else None
                status = order_data[9] if len(order_data) > 9 else "Pending"
                items = []  # Items not supported in tuple format
                payment_mode = None  # Payment mode not supported in tuple format
            
            # Validate required fields
            if not order_number:
                raise ValueError("Order number is required")
            if not total or total <= 0:
                raise ValueError("Order total must be greater than 0")
            
            # Check if order number already exists to prevent duplicates
            check_query = "SELECT id FROM orders WHERE order_number = ?"
            self.db.execute_query(check_query, (order_number,))
            existing_order = self.db.fetch_one()
            
            if existing_order:
                print(f"Warning: Order number {order_number} already exists!")
                return None
            
            query = """
            INSERT INTO orders (order_number, table_id, customer_name, customer_mobile, order_type,
                               subtotal, tax, discount, total, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (order_number, table_id, customer_name, customer_mobile, order_type,
                     subtotal, tax, discount, total, status)
            self.db.execute_query(query, params)
            order_id = self.db.lastrowid()
            
            if not order_id:
                raise ValueError("Failed to create order record")
            
            # If dictionary input contains items, add them to order_items
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
            
            # If dictionary input contains payment_mode, add payment record
            if isinstance(order_data, dict) and payment_mode:
                payment_query = """
                INSERT INTO payments (order_id, payment_mode, amount)
                VALUES (?, ?, ?)
                """
                self.db.execute_query(payment_query, (order_id, payment_mode, total))
            
            self.db.commit()
            return order_id
            
        except Exception as e:
            # Rollback on error
            try:
                self.db.conn.rollback() if hasattr(self.db, 'conn') and self.db.conn else None
            except:
                pass
            print(f"Error creating order: {str(e)}")
            raise e
    
    def add_item(self, order_id, menu_item_id, quantity, price, total, status="Completed"):
        """Add item to order"""
        query = """
        INSERT INTO order_items (order_id, menu_item_id, quantity, price, total, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        self.db.execute_query(query, (order_id, menu_item_id, quantity, price, total, status))
        self.db.commit()
    
    def add_payment(self, order_id, payment_mode, amount):
        """Add payment record"""
        query = """
        INSERT INTO payments (order_id, payment_mode, amount)
        VALUES (?, ?, ?)
        """
        self.db.execute_query(query, (order_id, payment_mode, amount))
        self.db.commit()
    
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
        
        if filter_value == "Today":
            query += " AND DATE(o.created_at) = DATE('now')"
        elif filter_value == "This Week":
            query += " AND o.created_at >= DATE('now', '-7 days')"
        elif filter_value == "This Month":
            query += " AND o.created_at >= DATE('now', '-30 days')"
        
        if search_term:
            query += " AND (o.order_number LIKE ? OR o.customer_name LIKE ? OR t.table_number LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY o.created_at DESC"
        
        self.db.execute_query(query, params)
        return self.db.fetch_all()
    
    def get_details(self, order_id):
        """Get order details"""
        query = """
        SELECT o.order_number, o.table_id, o.customer_name, o.customer_mobile, o.order_type, 
               o.subtotal, o.tax, o.discount, o.total, o.created_at, o.status
        FROM orders o
        WHERE o.id = ?
        """
        self.db.execute_query(query, (order_id,))
        return self.db.fetch_one()
    
    def get_items(self, order_id):
        """Get order items"""
        query = """
        SELECT mi.name, oi.quantity, oi.price, oi.total, oi.status
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
        """
        self.db.execute_query(query, (order_id,))
        return self.db.fetch_all()
    
    def get_payments(self, order_id):
        """Get order payments"""
        query = """
        SELECT payment_mode, amount, created_at
        FROM payments
        WHERE order_id = ?
        """
        self.db.execute_query(query, (order_id,))
        return self.db.fetch_all()

class KOT:
    """Kitchen Order Ticket model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_items(self, status="Pending"):
        """Get KOT items by status"""
        query = """
        SELECT oi.id, o.order_number, mi.name, oi.quantity, oi.created_at, oi.status
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.status = ?
        ORDER BY oi.created_at ASC
        """
        self.db.execute_query(query, (status,))
        return self.db.fetch_all()
    
    def update_status(self, item_id, status):
        """Update KOT item status"""
        query = "UPDATE order_items SET status = ? WHERE id = ?"
        self.db.execute_query(query, (status, item_id))
        self.db.commit()
    
    def get_kot_details(self, item_id):
        """Get KOT item details"""
        query = """
        SELECT o.order_number, mi.name, oi.quantity, oi.created_at
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.id = ?
        """
        self.db.execute_query(query, (item_id,))
        return self.db.fetch_one()

class Report:
    """Report model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def daily_sales_summary(self, from_date, to_date):
        """Get daily sales summary"""
        query = """
        SELECT DATE(created_at) as date, COUNT(*) as orders, SUM(total) as revenue
        FROM orders
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        self.db.execute_query(query, (from_date, to_date))
        return self.db.fetch_all()
    
    def sales_by_item(self, from_date, to_date):
        """Get sales by item"""
        query = """
        SELECT mi.name, SUM(oi.quantity) as quantity_sold, SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) BETWEEN ? AND ?
        GROUP BY mi.name
        ORDER BY total_revenue DESC
        """
        self.db.execute_query(query, (from_date, to_date))
        return self.db.fetch_all()
    
    def sales_by_category(self, from_date, to_date):
        """Get sales by category"""
        query = """
        SELECT c.name, SUM(oi.quantity) as quantity_sold, SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN categories c ON mi.category_id = c.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) BETWEEN ? AND ?
        GROUP BY c.name
        ORDER BY total_revenue DESC
        """
        self.db.execute_query(query, (from_date, to_date))
        return self.db.fetch_all()

class Settings:
    """Settings model"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_all(self):
        """Get all settings"""
        query = "SELECT key, value FROM settings"
        self.db.execute_query(query)
        settings = {}
        for row in self.db.fetch_all():
            settings[row[0]] = row[1]
        return settings
    
    def get(self, key, default=None):
        """Get setting value"""
        query = "SELECT value FROM settings WHERE key = ?"
        self.db.execute_query(query, (key,))
        result = self.db.fetch_one()
        return result[0] if result else default
    
    def update(self, key, value):
        """Update setting"""
        query = "UPDATE settings SET value = ?, updated_at = ? WHERE key = ?"
        self.db.execute_query(query, (value, datetime.now(), key))
        self.db.commit()
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        # Today's orders
        query = "SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?"
        self.db.execute_query(query, (today,))
        total_orders = self.db.fetch_one()[0]
        
        # Today's sales
        query = "SELECT SUM(total) FROM orders WHERE DATE(created_at) = ?"
        self.db.execute_query(query, (today,))
        today_sales = self.db.fetch_one()[0] or 0
        
        # Items sold
        query = """
        SELECT SUM(oi.quantity) 
        FROM order_items oi 
        JOIN orders o ON oi.order_id = o.id 
        WHERE DATE(o.created_at) = ?
        """
        self.db.execute_query(query, (today,))
        items_sold = self.db.fetch_one()[0] or 0
        
        # Occupied tables
        query = "SELECT COUNT(*) FROM tables WHERE status = 'Occupied'"
        self.db.execute_query(query)
        occupied_tables = self.db.fetch_one()[0]
        
        # Recent orders
        query = """
        SELECT o.order_number, o.total, o.created_at, o.order_type
        FROM orders o
        WHERE DATE(o.created_at) = ?
        ORDER BY o.created_at DESC
        LIMIT 5
        """
        self.db.execute_query(query, (today,))
        recent_orders = self.db.fetch_all()
        
        # Top items
        query = """
        SELECT mi.name, SUM(oi.quantity) as quantity, SUM(oi.total) as revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) = ?
        GROUP BY mi.name
        ORDER BY revenue DESC
        LIMIT 5
        """
        self.db.execute_query(query, (today,))
        top_items = self.db.fetch_all()
        
        return {
            'total_orders': total_orders,
            'today_sales': today_sales,
            'items_sold': items_sold,
            'occupied_tables': occupied_tables,
            'recent_orders': recent_orders,
            'top_items': top_items
        }