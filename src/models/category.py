class Category:
    """Category model for menu item categories"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """Get all categories"""
        query = "SELECT id, name FROM categories ORDER BY name"
        return self.db.fetch_all(query)
    
    def add(self, name):
        """Add a new category"""
        try:
            query = "INSERT INTO categories (name) VALUES (?)"
            self.db.execute(query, (name,))
            self.db.commit()
            return True
        except Exception:
            return False
    
    def update(self, category_id, name):
        """Update a category"""
        try:
            query = "UPDATE categories SET name = ? WHERE id = ?"
            self.db.execute(query, (name, category_id))
            self.db.commit()
            return True
        except Exception:
            return False
    
    def delete(self, category_id):
        """Delete a category"""
        query = "DELETE FROM categories WHERE id = ?"
        self.db.execute(query, (category_id,))
        self.db.commit()
    
    def get_menu_item_count(self, category_id):
        """Get count of menu items in a category"""
        query = "SELECT COUNT(*) FROM menu_items WHERE category_id = ?"
        result = self.db.fetch_one(query, (category_id,))
        return result[0] if result else 0
