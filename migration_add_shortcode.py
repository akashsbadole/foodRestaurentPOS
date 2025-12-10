#!/usr/bin/env python3
"""
Migration script to add shortcode field to menu_items table
"""

import sqlite3
import os

def add_shortcode_field():
    """Add shortcode field to menu_items table"""
    
    db_path = 'restaurant_pos.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if shortcode column already exists
        cursor.execute("PRAGMA table_info(menu_items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'shortcode' in columns:
            print("Shortcode field already exists in menu_items table")
            return True
        
        # Add shortcode column
        cursor.execute("""
        ALTER TABLE menu_items 
        ADD COLUMN shortcode TEXT
        """)
        
        # Create index for faster lookups
        cursor.execute("""
        CREATE INDEX idx_menu_items_shortcode 
        ON menu_items(shortcode)
        """)
        
        # Commit changes
        conn.commit()
        
        print("Successfully added shortcode field to menu_items table")
        return True
        
    except Exception as e:
        print(f"Error adding shortcode field: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = add_shortcode_field()
    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed!")