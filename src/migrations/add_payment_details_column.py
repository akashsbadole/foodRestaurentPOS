"""
Database migration script to add payment_details column to payments table
for storing encrypted payment details as JSON data
"""

import os
import sys
import sqlite3
from datetime import datetime

def add_payment_details_column(db_path="restaurant_pos.db"):
    """Add payment_details column to payments table if it doesn't exist"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First check if payments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("- payments table does not exist. Creating it first...")
            cursor.execute("""
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    payment_mode TEXT NOT NULL,
                    amount REAL NOT NULL,
                    payment_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            """)
            conn.commit()
            print("+ payments table created successfully")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'payment_details' not in columns:
            print("Adding payment_details column to payments table...")
            
            # Add the column
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN payment_details TEXT
            """)
            
            conn.commit()
            print("+ payment_details column added successfully")
        else:
            print("+ payment_details column already exists")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'payment_details' in columns:
            print("+ Migration completed successfully")
            success = True
        else:
            print("- Migration failed - column not found after addition")
            success = False
            
        conn.close()
        return success
            
    except Exception as e:
        print(f"- Error during migration: {str(e)}")
        return False

def verify_migration(db_path="restaurant_pos.db"):
    """Verify that the payment_details column was added successfully"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("- payments table does not exist")
            return False
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(payments)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'payment_details' in columns:
            print("+ payment_details column exists in payments table")
            
            # Get column details
            cursor.execute("PRAGMA table_info(payments)")
            for row in cursor.fetchall():
                if row[1] == 'payment_details':
                    print(f"  - Column type: {row[2]}")
                    print(f"  - Not null: {row[3]}")
                    print(f"  - Default value: {row[4]}")
                    break
            
            return True
        else:
            print("- payment_details column not found in payments table")
            return False
            
    except Exception as e:
        print(f"- Error during verification: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function"""
    print("=" * 50)
    print("Payment Details Column Migration")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Determine database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Default to src/restaurant_pos.db for the desktop version
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'restaurant_pos.db')
    
    if not os.path.exists(db_path):
        print(f"- Database file not found: {db_path}")
        return 1
    
    print(f"Using database: {db_path}")
    print()
    
    # Add payment_details column
    migration_success = add_payment_details_column(db_path)
    
    print()
    if migration_success:
        print("Migration completed successfully!")
        print()
        print("Verification:")
        verify_migration(db_path)
        print()
        print("Next steps:")
        print("1. Restart your application")
        print("2. The payment_details column is now available for storing")
        print("   encrypted payment information as JSON data")
    else:
        print("- Migration failed!")
        print("Please check the error messages above and fix any issues.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)