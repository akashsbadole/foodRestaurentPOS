import hashlib
from src.utils.encryption import get_encryption_manager

class User:
    """User model for user management with encrypted passwords"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def authenticate(self, username, password):
        """Authenticate user with username and password"""
        try:
            # Get the stored encrypted password for the user
            query = "SELECT id, username, role, password FROM users WHERE username = ?"
            self.db.execute_query(query, (username,))
            result = self.db.fetch_one()
            
            if not result:
                return None
            
            # Decrypt the stored password
            stored_password = self.encryption_manager.decrypt_field(result[3])
            
            # Compare with provided password
            if password == stored_password:
                # Return user info without password
                return (result[0], result[1], result[2])
            
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_all(self):
        """Get all users"""
        query = "SELECT username, role FROM users ORDER BY username"
        self.db.execute_query(query)
        return self.db.fetch_all()
    
    def add(self, username, password, role):
        """Add a new user with encrypted password"""
        try:
            # Encrypt the password before storing
            encrypted_password = self.encryption_manager.encrypt_field(password)
            
            query = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
            self.db.execute_query(query, (username, encrypted_password, role))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def delete(self, username):
        """Delete a user"""
        query = "DELETE FROM users WHERE username = ?"
        self.db.execute_query(query, (username,))
        self.db.commit()
    
    def update_password(self, username, new_password):
        """Update user password with encryption"""
        try:
            # Encrypt the new password
            encrypted_password = self.encryption_manager.encrypt_field(new_password)
            
            query = "UPDATE users SET password = ? WHERE username = ?"
            self.db.execute_query(query, (encrypted_password, username))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error updating password: {e}")
            return False
    
    def verify_encrypted_passwords(self):
        """Utility method to verify all passwords are encrypted"""
        try:
            query = "SELECT username, password FROM users"
            self.db.execute_query(query)
            users = self.db.fetch_all()
            
            unencrypted_count = 0
            for username, password in users:
                # Try to decrypt, if it fails it might be unencrypted
                try:
                    decrypted = self.encryption_manager.decrypt_field(password)
                    # If decrypted equals original, it was likely unencrypted
                    if password == decrypted:
                        unencrypted_count += 1
                        print(f"User {username} has unencrypted password")
                except:
                    # Decryption failed, likely unencrypted
                    unencrypted_count += 1
                    print(f"User {username} may have unencrypted password")
            
            if unencrypted_count > 0:
                print(f"Found {unencrypted_count} users with potentially unencrypted passwords")
            else:
                print("All user passwords appear to be properly encrypted")
            
            return unencrypted_count == 0
        except Exception as e:
            print(f"Error verifying encrypted passwords: {e}")
            return False
