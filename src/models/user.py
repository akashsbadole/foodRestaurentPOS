import hashlib

class User:
    """User model for user management"""
    
    def __init__(self, db):
        self.db = db
    
    def authenticate(self, username, password):
        """Authenticate user with username and password"""
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        query = "SELECT id, username, role FROM users WHERE username = ? AND password = ?"
        result = self.db.fetch_one(query, (username, hashed_password))
        
        return result
    
    def get_all(self):
        """Get all users"""
        query = "SELECT username, role FROM users ORDER BY username"
        return self.db.fetch_all(query)
    
    def add(self, username, password, role):
        """Add a new user"""
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        try:
            query = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
            self.db.execute(query, (username, hashed_password, role))
            self.db.commit()
            return True
        except Exception:
            return False
    
    def delete(self, username):
        """Delete a user"""
        query = "DELETE FROM users WHERE username = ?"
        self.db.execute(query, (username,))
        self.db.commit()
