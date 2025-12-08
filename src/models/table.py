class Table:
    """Table model for table management"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """Get all tables"""
        query = "SELECT id, table_number, capacity, status FROM tables ORDER BY table_number"
        return self.db.fetch_all(query)
    
    def get_available(self):
        """Get available tables"""
        query = "SELECT id, table_number FROM tables WHERE status = 'Available' ORDER BY table_number"
        return self.db.fetch_all(query)
    
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
