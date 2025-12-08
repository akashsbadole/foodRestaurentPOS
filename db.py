import sqlite3
import os
from datetime import datetime

def setup_database():
    # Create database if it doesn't exist
    if not os.path.exists('restaurant_pos.db'):
        conn = sqlite3.connect('restaurant_pos.db')
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Categories table
        cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Menu items table
        cursor.execute('''
        CREATE TABLE menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category_id INTEGER,
            stock_quantity INTEGER DEFAULT 0,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')
        
        # Tables table
        cursor.execute('''
        CREATE TABLE tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT UNIQUE NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT DEFAULT 'Available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Orders table
        cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            table_id INTEGER,
            customer_name TEXT,
            customer_mobile TEXT,
            order_type TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            discount REAL NOT NULL,
            total REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (table_id) REFERENCES tables (id)
        )
        ''')
        
        # Order items table
        cursor.execute('''
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
        ''')
        
        # Payments table
        cursor.execute('''
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            payment_mode TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        ''')
        
        # Settings table
        cursor.execute('''
        CREATE TABLE settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Insert default data
        # Default admin user
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                      ("admin", "admin123", "Admin"))
        
        # Default categories
        cursor.execute("INSERT INTO categories (name) VALUES (?)", ("Snacks",))
        cursor.execute("INSERT INTO categories (name) VALUES (?)", ("Meals",))
        cursor.execute("INSERT INTO categories (name) VALUES (?)", ("Drinks",))
        cursor.execute("INSERT INTO categories (name) VALUES (?)", ("Desserts",))
        
        # Default menu items
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("French Fries", 99, 1, 100))
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("Burger", 149, 1, 50))
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("Pizza", 249, 2, 30))
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("Pasta", 199, 2, 40))
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("Coke", 49, 3, 200))
        cursor.execute("INSERT INTO menu_items (name, price, category_id, stock_quantity) VALUES (?, ?, ?, ?)", 
                      ("Ice Cream", 79, 4, 60))
        
        # Default tables
        for i in range(1, 11):
            cursor.execute("INSERT INTO tables (table_number, capacity) VALUES (?, ?)", 
                          (f"T{i}", 4))
        
        # Default settings
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                      ("restaurant_name", "My Restaurant"))
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                      ("restaurant_address", "123 Main Street, City"))
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                      ("tax_rate", "5"))
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                      ("currency_symbol", "₹"))
        
        conn.commit()
        conn.close()
        print("Database setup complete!")
    else:
        print("Database already exists.")

if __name__ == "__main__":
    setup_database()