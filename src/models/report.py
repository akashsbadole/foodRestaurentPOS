class Report:
    """Report model for generating reports"""
    
    def __init__(self, db):
        self.db = db
    
    def daily_sales_summary(self, from_date, to_date):
        """Generate daily sales summary report"""
        query = """
        SELECT DATE(created_at) as date, COUNT(*) as orders, SUM(total) as revenue
        FROM orders
        WHERE DATE(created_at) BETWEEN ? AND ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        
        return self.db.fetch_all(query, (from_date, to_date))
    
    def sales_by_item(self, from_date, to_date):
        """Generate sales by item report"""
        query = """
        SELECT mi.name, SUM(oi.quantity) as quantity_sold, SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) BETWEEN ? AND ?
        GROUP BY mi.name
        ORDER BY total_revenue DESC
        """
        
        return self.db.fetch_all(query, (from_date, to_date))
    
    def sales_by_category(self, from_date, to_date):
        """Generate sales by category report"""
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
        
        return self.db.fetch_all(query, (from_date, to_date))
