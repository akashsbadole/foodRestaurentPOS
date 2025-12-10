class MenuItem:
    """Menu item model for menu management"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self, search_term="", category="All"):
        """Get all menu items with optional search and filter"""
        query = """
        SELECT mi.id, mi.name, c.name, mi.price, mi.stock_quantity, mi.shortcode
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE 1=1
        """
        params = []
        
        if search_term:
            # Search in name, shortcode
            query += " AND (mi.name LIKE ? OR mi.shortcode LIKE ?)"
            params.append(f"%{search_term}%")
            params.append(f"%{search_term}%")
            
            if category != "All":
                query += " AND c.name = ?"
                params.append(category)
        elif category != "All":
            query += " AND c.name = ?"
            params.append(category)
        
        query += " ORDER BY c.name, mi.name"
        
        self.db.execute_query(query, params)
        return self.db.fetch_all()
    
    def add(self, name, price, category_id, stock_quantity, image_path="", shortcode=""):
        """Add a new menu item"""
        try:
            # Handle empty stock quantity - default to 0
            if stock_quantity == "" or stock_quantity is None:
                stock_quantity = 0
            elif isinstance(stock_quantity, str) and not stock_quantity.strip():
                stock_quantity = 0
            else:
                # Try to convert to integer
                try:
                    stock_quantity = int(stock_quantity)
                except (ValueError, TypeError):
                    stock_quantity = 0
            
            print(f"[DEBUG] MenuItem.add: processed stock_quantity = {stock_quantity} (type: {type(stock_quantity)})")
            
            # Check shortcode uniqueness before adding
            if not self.is_shortcode_unique(shortcode, category_id):
                print(f"[DEBUG] Shortcode '{shortcode}' is not unique in category {category_id}")
                return False
            
            query = """
            INSERT INTO menu_items (name, price, category_id, stock_quantity, image_path, shortcode)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(query, (name, price, category_id, stock_quantity, image_path, shortcode))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding menu item: {e}")
            return False
    
    def update(self, item_id, name, price, category_id, stock_quantity, image_path="", shortcode=""):
        """Update a menu item"""
        try:
            # Check shortcode uniqueness before updating
            if not self.is_shortcode_unique(shortcode, category_id, item_id):
                print(f"[DEBUG] Shortcode '{shortcode}' is not unique in category {category_id}")
                return False
            
            query = """
            UPDATE menu_items
            SET name = ?, price = ?, category_id = ?, stock_quantity = ?, image_path = ?, shortcode = ?
            WHERE id = ?
            """
            self.db.execute_query(query, (name, price, category_id, stock_quantity, image_path, shortcode, item_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating menu item: {e}")
            return False
    
    def delete(self, item_id):
        """Delete a menu item"""
        query = "DELETE FROM menu_items WHERE id = ?"
        self.db.execute_query(query, (item_id,))
        self.db.commit()
    
    def get_by_id(self, item_id):
        """Get menu item by ID"""
        query = """
        SELECT mi.name, mi.price, mi.category_id, mi.stock_quantity, mi.image_path, mi.shortcode, c.name
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE mi.id = ?
        """
        self.db.execute_query(query, (item_id,))
        return self.db.fetch_one()
    
    def get_inventory_items(self, search_term="", filter_type="All"):
        """Get items for inventory management"""
        query = """
        SELECT mi.id, mi.name, c.name, mi.stock_quantity
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE 1=1
        """
        params = []
        
        if search_term:
            query += " AND (mi.name LIKE ? OR mi.shortcode LIKE ?)"
            params.append(f"%{search_term}%")
            params.append(f"%{search_term}%")
        
        if filter_type == "Low Stock":
            query += " AND mi.stock_quantity > 0 AND mi.stock_quantity <= 10"
        elif filter_type == "Out of Stock":
            query += " AND mi.stock_quantity = 0"
        
        query += " ORDER BY mi.stock_quantity ASC, mi.name"
        
        self.db.execute_query(query, params)
        return self.db.fetch_all()
    
    def update_stock(self, item_id, new_stock):
        """Update stock quantity for an item"""
        query = "UPDATE menu_items SET stock_quantity = ? WHERE id = ?"
        self.db.execute_query(query, (new_stock, item_id))
        self.db.commit()
        
        # Dispatch inventory updated event
        from src.utils.event_dispatcher import event_dispatcher
        event_dispatcher.inventory_updated(item_id, new_stock)
    
    def is_shortcode_unique(self, shortcode, category_id, item_id=None):
        """Check if shortcode is unique within a category"""
        if not shortcode:
            return True  # Empty shortcode is always valid
        
        query = """
        SELECT COUNT(*) FROM menu_items
        WHERE shortcode = ? AND category_id = ?
        """
        params = [shortcode, category_id]
        
        # Exclude current item when updating
        if item_id:
            query += " AND id != ?"
            params.append(item_id)
        
        self.db.execute_query(query, params)
        result = self.db.fetch_one()
        return result[0] == 0 if result else True
    
    def get_by_shortcode(self, shortcode):
        """Get menu item by shortcode"""
        if not shortcode:
            return None
        
        query = """
        SELECT mi.id, mi.name, mi.price, mi.category_id, mi.stock_quantity, mi.image_path, mi.shortcode, c.name
        FROM menu_items mi
        JOIN categories c ON mi.category_id = c.id
        WHERE mi.shortcode = ?
        """
        self.db.execute_query(query, (shortcode,))
        return self.db.fetch_one()
