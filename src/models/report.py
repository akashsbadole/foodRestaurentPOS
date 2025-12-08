from datetime import datetime

class Report:
    """Report model for generating reports"""
    
    def __init__(self, db):
        self.db = db
    
    def get_dashboard_stats(self):
        """Get comprehensive dashboard statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Today's basic stats
        query = """
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(total), 0) as today_sales
        FROM orders 
        WHERE DATE(created_at) = ?
        """
        self.db.execute_query(query, (today,))
        result = self.db.fetch_one()
        
        # Items sold today
        items_query = """
        SELECT COALESCE(SUM(oi.quantity), 0) as items_sold
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) = ?
        """
        self.db.execute_query(items_query, (today,))
        items_result = self.db.fetch_one()
        
        # Occupied tables count
        tables_query = """
        SELECT COUNT(*) as occupied_tables
        FROM tables 
        WHERE status = 'Occupied'
        """
        self.db.execute_query(tables_query)
        tables_result = self.db.fetch_one()
        
        # Recent orders (last 5)
        recent_query = """
        SELECT order_number, total, created_at, order_type
        FROM orders 
        ORDER BY created_at DESC 
        LIMIT 5
        """
        self.db.execute_query(recent_query)
        recent_orders = self.db.fetch_all()
        
        # Hourly sales for trend
        hourly_query = """
        SELECT 
            strftime('%H', created_at) as hour,
            COUNT(*) as orders,
            COALESCE(SUM(total), 0) as revenue
        FROM orders 
        WHERE DATE(created_at) = ?
        GROUP BY strftime('%H', created_at)
        ORDER BY hour
        """
        self.db.execute_query(hourly_query, (today,))
        hourly_sales = self.db.fetch_all()
        
        # Top selling items today
        top_items_query = """
        SELECT 
            mi.name,
            SUM(oi.quantity) as total_quantity,
            SUM(oi.total) as total_revenue
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        JOIN orders o ON oi.order_id = o.id
        WHERE DATE(o.created_at) = ?
        GROUP BY mi.name
        ORDER BY total_quantity DESC
        LIMIT 5
        """
        self.db.execute_query(top_items_query, (today,))
        top_items = self.db.fetch_all()
        
        return {
            'total_orders': result[0] if result else 0,
            'today_sales': result[1] if result else 0,
            'items_sold': items_result[0] if items_result else 0,
            'occupied_tables': tables_result[0] if tables_result else 0,
            'recent_orders': recent_orders,
            'hourly_sales': hourly_sales,
            'top_items': top_items
        }
    
    def daily_sales_summary(self, from_date, to_date):
        """Generate daily sales summary report"""
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
        
        self.db.execute_query(query, (from_date, to_date))
        return self.db.fetch_all()
    
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
        
        self.db.execute_query(query, (from_date, to_date))
        return self.db.fetch_all()
