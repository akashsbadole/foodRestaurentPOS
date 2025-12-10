"""
Database migration script to add image_path column to menu_items table
for the Tkinter version if it doesn't already exist
"""

import os
import sys
import sqlite3
from datetime import datetime

def add_image_path_column(db_path="restaurant_pos.db"):
    """Add image_path column to menu_items table if it doesn't exist"""
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(menu_items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'image_path' not in columns:
            print("Adding image_path column to menu_items table...")
            
            # Add the column
            cursor.execute("""
                ALTER TABLE menu_items 
                ADD COLUMN image_path TEXT
            """)
            
            conn.commit()
            print("✓ image_path column added successfully")
        else:
            print("✓ image_path column already exists")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(menu_items)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'image_path' in columns:
            print("✓ Migration completed successfully")
            success = True
        else:
            print("✗ Migration failed - column not found after addition")
            success = False
            
        conn.close()
        return success
            
    except Exception as e:
        print(f"✗ Error during migration: {str(e)}")
        return False

def create_images_directory():
    """Create images directory structure if it doesn't exist"""
    try:
        # Create main images directory
        images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Create menu_items subdirectory
        menu_items_dir = os.path.join(images_dir, 'menu_items')
        os.makedirs(menu_items_dir, exist_ok=True)
        
        print(f"✓ Images directory created/verified: {menu_items_dir}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating images directory: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("=" * 50)
    print("Image Path Column Migration (Tkinter Version)")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create images directory
    create_images_directory()
    
    # Add image_path column
    migration_success = add_image_path_column()
    
    print()
    if migration_success:
        print("🎉 Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart your Tkinter application")
        print("2. Test image upload functionality")
        print("3. Verify images are stored in src/images/menu_items/")
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above and fix any issues.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)