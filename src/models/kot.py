class KOT:
    """Kitchen Order Ticket model for KOT management"""
    
    def __init__(self, db):
        self.db = db
    
    def get_items(self, status_filter="Pending"):
        """Get KOT items by status"""
        query = """
        SELECT oi.id, o.order_number, mi.name, oi.quantity, oi.created_at, oi.status
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.status = ?
        ORDER BY oi.created_at ASC
        """
        
        return self.db.fetch_all(query, (status_filter,))
    
    def update_status(self, item_id, status):
        """Update KOT item status"""
        query = "UPDATE order_items SET status = ? WHERE id = ?"
        self.db.execute(query, (status, item_id))
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
        
        return self.db.fetch_one(query, (item_id,))
