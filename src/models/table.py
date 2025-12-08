class Table:
    """Table model for table management"""
    
    def __init__(self, db):
        self.db = db
    
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
        """Add a new table"""
        try:
            query = "INSERT INTO tables (table_number, capacity) VALUES (?, ?)"
            self.db.execute(query, (table_number, capacity))
            self.db.commit()
            return True
        except Exception:
            return False
    
    def update(self, table_id, table_number, capacity, status):
        """Update a table"""
        try:
            query = """
            UPDATE tables 
            SET table_number = ?, capacity = ?, status = ?
            WHERE id = ?
            """
            self.db.execute(query, (table_number, capacity, status, table_id))
            self.db.commit()
            return True
        except Exception:
            return False
    
    def delete(self, table_id):
        """Delete a table"""
        query = "DELETE FROM tables WHERE id = ?"
        self.db.execute(query, (table_id,))
        self.db.commit()
    
    def update_status(self, table_id, status):
        """Update table status"""
        query = "UPDATE tables SET status = ? WHERE id = ?"
        self.db.execute(query, (status, table_id))
        self.db.commit()
    
    def reset_all(self):
        """Reset all tables to Available status"""
        query = "UPDATE tables SET status = 'Available'"
        self.db.execute(query)
        self.db.commit()
    
    def get_by_id(self, table_id):
        """Get table by ID"""
        query = "SELECT id, table_number, capacity, status FROM tables WHERE id = ?"
        self.db.execute_query(query, (table_id,))
        return self.db.fetch_one()
    
    def get_orders_for_table(self, table_id):
        """Get orders for a specific table"""
        query = """
        SELECT o.id, o.order_number, o.total, o.created_at, o.status
        FROM orders o
        WHERE o.table_id = ? AND o.status != 'Completed'
        ORDER BY o.created_at
        """
        self.db.execute_query(query, (table_id,))
        return self.db.fetch_all()
    
    def move_order_between_tables(self, order_id, from_table_id, to_table_id):
        """Move an order from one table to another"""
        try:
            # Update order's table
            query = "UPDATE orders SET table_id = ? WHERE id = ? AND table_id = ?"
            self.db.execute(query, (to_table_id, order_id, from_table_id))
            
            # Update table statuses
            self.update_status(from_table_id, 'Available')
            self.update_status(to_table_id, 'Occupied')
            
            self.db.commit()
            return True
        except Exception:
            return False
    
    def merge_orders(self, order_ids, target_table_id):
        """Merge multiple orders into one table"""
        try:
            for order_id in order_ids:
                query = "UPDATE orders SET table_id = ? WHERE id = ?"
                self.db.execute(query, (target_table_id, order_id))
            
            self.update_status(target_table_id, 'Occupied')
            self.db.commit()
            return True
        except Exception:
            return False
    
    def get_table_with_active_orders(self):
        """Get tables with active orders"""
        query = """
        SELECT t.id, t.table_number, t.capacity, t.status, 
               COUNT(o.id) as active_orders
        FROM tables t
        LEFT JOIN orders o ON t.id = o.table_id AND o.status != 'Completed'
        GROUP BY t.id, t.table_number, t.capacity, t.status
        ORDER BY t.table_number
        """
        self.db.execute_query(query)
        return self.db.fetch_all()
