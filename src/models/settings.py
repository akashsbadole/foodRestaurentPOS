from datetime import datetime

class Settings:
    """Settings model for application settings management"""
    
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """Get all settings as dictionary"""
        query = "SELECT key, value FROM settings"
        self.db.execute_query(query)
        results = self.db.fetch_all()
        
        settings = {}
        for row in results:
            settings[row[0]] = row[1]
        
        return settings
    
    def get(self, key, default=None):
        """Get a specific setting value"""
        query = "SELECT value FROM settings WHERE key = ?"
        self.db.execute_query(query, (key,))
        result = self.db.fetch_one()
        
        return result[0] if result else default
    
    def update(self, key, value):
        """Update a setting value"""
        query = """
        UPDATE settings SET value = ?, updated_at = ? WHERE key = ?
        """
        self.db.execute(query, (value, datetime.now(), key))
        self.db.commit()
    
    def create(self, key, value):
        """Create a new setting"""
        query = """
        INSERT INTO settings (key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """
        self.db.execute(query, (key, value, datetime.now(), datetime.now()))
        self.db.commit()
    
    def ensure_exists(self, key, default_value):
        """Ensure a setting exists, create with default if not"""
        if not self.get(key):
            self.create(key, default_value)
