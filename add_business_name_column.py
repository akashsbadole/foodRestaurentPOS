"""
Add business_name column to licenses table
"""

import sqlite3

def add_business_name_column():
    """Add business_name column to licenses table if it doesn't exist"""
    try:
        # Connect to database
        conn = sqlite3.connect('restaurant_pos.db')
        cursor = conn.cursor()
        
        # Check if business_name column exists
        cursor.execute("PRAGMA table_info(licenses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'business_name' not in columns:
            print("Adding business_name column to licenses table")
            cursor.execute("ALTER TABLE licenses ADD COLUMN business_name TEXT")
            conn.commit()
            print("business_name column added successfully")
        else:
            print("business_name column already exists")
        
        # Check if is_active column exists
        if 'is_active' not in columns:
            print("Adding is_active column to licenses table")
            cursor.execute("ALTER TABLE licenses ADD COLUMN is_active INTEGER DEFAULT 1")
            conn.commit()
            print("is_active column added successfully")
        else:
            print("is_active column already exists")
            
        # Check if expires_at column exists
        if 'expires_at' not in columns:
            print("Adding expires_at column to licenses table")
            cursor.execute("ALTER TABLE licenses ADD COLUMN expires_at TEXT")
            conn.commit()
            print("expires_at column added successfully")
        else:
            print("expires_at column already exists")
            
        # Check if issued_at column exists
        if 'issued_at' not in columns:
            print("Adding issued_at column to licenses table")
            cursor.execute("ALTER TABLE licenses ADD COLUMN issued_at TEXT")
            conn.commit()
            print("issued_at column added successfully")
        else:
            print("issued_at column already exists")
        
        # Check license_activations table for activation_token column
        cursor.execute("PRAGMA table_info(license_activations)")
        activation_columns = [col[1] for col in cursor.fetchall()]
        
        if 'activation_token' not in activation_columns:
            print("Adding activation_token column to license_activations table")
            cursor.execute("ALTER TABLE license_activations ADD COLUMN activation_token TEXT")
            conn.commit()
            print("activation_token column added successfully")
        else:
            print("activation_token column already exists")
            
        # Check if activated_at column exists
        if 'activated_at' not in activation_columns:
            print("Adding activated_at column to license_activations table")
            cursor.execute("ALTER TABLE license_activations ADD COLUMN activated_at TEXT")
            conn.commit()
            print("activated_at column added successfully")
        else:
            print("activated_at column already exists")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding business_name column: {str(e)}")
        return False

if __name__ == "__main__":
    if add_business_name_column():
        print("Column addition completed successfully")
    else:
        print("Column addition failed")