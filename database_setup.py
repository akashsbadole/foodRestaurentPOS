#!/usr/bin/env python3
"""
Database setup script for Restaurant POS System
Creates the initial database structure with all required tables
"""

import sqlite3
import os
from datetime import datetime

def setup_database():
    """Create database and all required tables"""
    
    # Remove existing database if it exists
    if os.path.exists('restaurant_pos.db'):
        os.remove('restaurant_pos.db')
    
    # Create new database connection
    conn = sqlite3.connect('restaurant_pos.db')
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Cashier',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create categories table
        cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create menu_items table
        cursor.execute("""
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category_id INTEGER,
            stock_quantity INTEGER DEFAULT 0,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        """)
        
        # Create tables table
        cursor.execute("""
        CREATE TABLE tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 4,
            status TEXT NOT NULL DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create orders table
        cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            table_id INTEGER,
            customer_name TEXT,
            customer_mobile TEXT,
            order_type TEXT NOT NULL DEFAULT 'Dine-in',
            subtotal REAL NOT NULL DEFAULT 0,
            tax REAL NOT NULL DEFAULT 0,
            discount REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES tables (id)
        )
        """)
        
        # Create order_items table
        cursor.execute("""
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
        """)
        
        # Create payments table
        cursor.execute("""
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            payment_mode TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        """)
        
        # Create settings table
        cursor.execute("""
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Insert default data
        
        # Insert default admin user
        cursor.execute("""
        INSERT INTO users (username, password, role) 
        VALUES ('admin', '0192023a7bbd73250516f069df18b500', 'Admin')
        """)
        
        # Insert default categories
        categories = [
            ('Starters',),
            ('Main Course',),
            ('Desserts',),
            ('Beverages',),
            ('Snacks',)
        ]
        
        cursor.executemany("INSERT INTO categories (name) VALUES (?)", categories)
        
        # Insert default menu items
        menu_items = [
            ('Samosa', 30.00, 1, 50),
            ('Paneer Tikka', 120.00, 2, 30),
            ('Butter Chicken', 150.00, 2, 25),
            ('Ice Cream', 60.00, 3, 40),
            ('Soft Drink', 40.00, 4, 100),
            ('French Fries', 50.00, 5, 60)
        ]
        
        cursor.executemany("""
        INSERT INTO menu_items (name, price, category_id, stock_quantity) 
        VALUES (?, ?, ?, ?)
        """, menu_items)
        
        # Insert default tables
        tables = [
            ('T1', 4),
            ('T2', 4),
            ('T3', 6),
            ('T4', 6),
            ('T5', 8),
            ('T6', 8),
            ('T7', 10),
            ('T8', 10)
        ]
        
        cursor.executemany("""
        INSERT INTO tables (table_number, capacity) 
        VALUES (?, ?)
        """, tables)
        
        # Insert default settings
        settings = [
            ('restaurant_name', 'My Restaurant'),
            ('restaurant_address', '123 Main Street, City'),
            ('currency_symbol', '₹'),
            ('tax_rate', '5.0'),
            # Printer settings
            ('thermal_printer_name', ''),
            ('standard_printer_name', ''),
            ('default_bill_printer_type', 'standard'),
            ('default_kot_printer_type', 'thermal'),
            ('bill_paper_width', '58'),
            ('kot_paper_width', '58'),
            ('auto_print_bill', 'False'),
            ('auto_print_kot', 'True')
        ]
        
        cursor.executemany("""
        INSERT INTO settings (key, value) 
        VALUES (?, ?)
        """, settings)
        
        # Commit all changes
        conn.commit()
        
        print("Database setup completed successfully!")
        print(f"Created {len(menu_items)} menu items")
        print(f"Created {len(categories)} categories")
        print(f"Created {len(tables)} tables")
        print(f"Created default admin user: admin")
        print("Default password: admin123")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_database()
