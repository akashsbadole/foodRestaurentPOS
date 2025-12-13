"""
Database Migration Script to Remove License Tables
This script drops all license-related tables from the database as they are no longer needed.
"""

import sqlite3
import os
import sys
from datetime import datetime

def remove_license_tables(db_path='restaurant_pos.db'):
    """Remove all license-related tables from the database"""
    
    # List of license tables to be removed
    license_tables = [
        'licenses',
        'license_activations',
        'hardware_bindings',
        'license_audit_logs',
        'blacklisted_licenses',
        'license_fragments',
        'license_heartbeat',
        'license_features',
        'license_servers',
        'license_settings'
    ]
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Starting license tables removal from {db_path}...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check which license tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        tables_to_drop = []
        for table in license_tables:
            if table in existing_tables:
                tables_to_drop.append(table)
        
        if not tables_to_drop:
            print("No license tables found to remove.")
            return True
        
        print(f"Found {len(tables_to_drop)} license tables to remove:")
        for table in tables_to_drop:
            print(f"  - {table}")
        print()
        
        # Drop each license table
        dropped_count = 0
        for table in tables_to_drop:
            try:
                # Drop the table
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                dropped_count += 1
                print(f"[OK] Dropped table: {table}")
            except Exception as e:
                print(f"[ERROR] Error dropping table {table}: {e}")
        
        # Remove any license-related settings
        try:
            cursor.execute("DELETE FROM settings WHERE key LIKE 'license_%'")
            settings_removed = cursor.rowcount
            if settings_removed > 0:
                print(f"[OK] Removed {settings_removed} license-related settings")
        except Exception as e:
            print(f"[ERROR] Error removing license settings: {e}")
        
        # Commit changes
        conn.commit()
        
        print()
        print(f"License tables removal completed successfully!")
        print(f"Dropped {dropped_count} license tables.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during license tables removal: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_removal(db_path='restaurant_pos.db'):
    """Verify that license tables have been successfully removed"""
    
    # List of license tables that should be removed
    license_tables = [
        'licenses',
        'license_activations',
        'hardware_bindings',
        'license_audit_logs',
        'blacklisted_licenses',
        'license_fragments',
        'license_heartbeat',
        'license_features',
        'license_servers',
        'license_settings'
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"Verifying license tables removal in {db_path}...")
        
        # Check which license tables still exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        remaining_tables = []
        for table in license_tables:
            if table in existing_tables:
                remaining_tables.append(table)
        
        if remaining_tables:
            print(f"[ERROR] Verification failed - {len(remaining_tables)} license tables still exist:")
            for table in remaining_tables:
                print(f"  - {table}")
            return False
        else:
            print("[OK] Verification successful - All license tables have been removed.")
            
            # Check for license-related settings (only if settings table exists)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
            settings_exists = cursor.fetchone()
            
            license_settings = []
            if settings_exists:
                cursor.execute("SELECT key FROM settings WHERE key LIKE 'license_%'")
                license_settings = [row[0] for row in cursor.fetchall()]
            
            if license_settings:
                print(f"[WARNING] {len(license_settings)} license-related settings still exist:")
                for setting in license_settings:
                    print(f"  - {setting}")
            else:
                print("[OK] No license-related settings found.")
            
            return True
        
    except Exception as e:
        print(f"[ERROR] Error during verification: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function"""
    print("=" * 60)
    print("License Tables Removal Migration")
    print("=" * 60)
    
    # Default database paths
    db_paths = [
        'restaurant_pos.db',
        'src/restaurant_pos.db'
    ]
    
    success = True
    
    for db_path in db_paths:
        print(f"\nProcessing database: {db_path}")
        print("-" * 40)
        
        if not os.path.exists(db_path):
            print(f"Database not found: {db_path}")
            continue
        
        # Remove license tables
        if remove_license_tables(db_path):
            # Verify removal
            if verify_removal(db_path):
                print(f"[OK] Migration completed successfully for {db_path}")
            else:
                print(f"[ERROR] Migration verification failed for {db_path}")
                success = False
        else:
            print(f"[ERROR] Migration failed for {db_path}")
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] All migrations completed successfully!")
    else:
        print("[FAILED] Some migrations failed. Please check the errors above.")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        db_path = sys.argv[2] if len(sys.argv) > 2 else 'restaurant_pos.db'
        
        if command == "migrate":
            remove_license_tables(db_path)
        elif command == "verify":
            verify_removal(db_path)
        else:
            print("Usage: python remove_license_tables.py [migrate|verify] [db_path]")
    else:
        # Run full migration
        success = main()
        sys.exit(0 if success else 1)