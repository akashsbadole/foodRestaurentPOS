"""
Database Migration for Support System Tables
Adds all necessary tables for support tickets, bug reports, and contact submissions
"""

import sqlite3
from datetime import datetime

def migrate_support_tables(db_path='restaurant_pos.db'):
    """Create support system tables in the database"""
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting support system tables migration...")
        
        # Create support_tickets table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            created_by INTEGER NOT NULL,
            assigned_to INTEGER,
            customer_email TEXT,
            customer_phone TEXT,
            contact_info TEXT,
            order_id INTEGER,
            table_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id),
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (table_id) REFERENCES tables(id)
        )
        ''')
        
        # Create support_conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            sender_role TEXT DEFAULT 'User',
            message TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            is_internal BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id)
        )
        ''')
        
        # Create support_attachments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS support_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER,
            bug_report_id INTEGER,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            file_hash TEXT,
            file_extension TEXT,
            attachment_type TEXT DEFAULT 'Other',
            uploaded_by INTEGER NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES support_tickets(id) ON DELETE CASCADE,
            FOREIGN KEY (bug_report_id) REFERENCES bug_reports(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
        ''')
        
        # Create bug_reports table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bug_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT DEFAULT 'Bug Report',
            severity TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'New',
            reported_by INTEGER NOT NULL,
            assigned_to INTEGER,
            error_details TEXT,
            user_data TEXT,
            contact_info TEXT,
            system_info TEXT,
            reproduction_steps TEXT,
            expected_behavior TEXT,
            actual_behavior TEXT,
            module TEXT,
            function_name TEXT,
            line_number TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reported_by) REFERENCES users(id),
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        )
        ''')
        
        # Create contact_submissions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            subject TEXT,
            message TEXT NOT NULL,
            contact_type TEXT DEFAULT 'General Inquiry',
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'New',
            assigned_to INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users(id)
        )
        ''')
        
        # Create indexes for better performance
        indexes = [
            # Support tickets indexes
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_priority ON support_tickets(priority)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_created_by ON support_tickets(created_by)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_assigned_to ON support_tickets(assigned_to)',
            'CREATE INDEX IF NOT EXISTS idx_support_tickets_created_at ON support_tickets(created_at)',
            
            # Support conversations indexes
            'CREATE INDEX IF NOT EXISTS idx_support_conversations_ticket_id ON support_conversations(ticket_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_conversations_sender_id ON support_conversations(sender_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_conversations_created_at ON support_conversations(created_at)',
            
            # Support attachments indexes
            'CREATE INDEX IF NOT EXISTS idx_support_attachments_ticket_id ON support_attachments(ticket_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_attachments_bug_report_id ON support_attachments(bug_report_id)',
            'CREATE INDEX IF NOT EXISTS idx_support_attachments_uploaded_by ON support_attachments(uploaded_by)',
            
            # Bug reports indexes
            'CREATE INDEX IF NOT EXISTS idx_bug_reports_status ON bug_reports(status)',
            'CREATE INDEX IF NOT EXISTS idx_bug_reports_severity ON bug_reports(severity)',
            'CREATE INDEX IF NOT EXISTS idx_bug_reports_reported_by ON bug_reports(reported_by)',
            'CREATE INDEX IF NOT EXISTS idx_bug_reports_assigned_to ON bug_reports(assigned_to)',
            'CREATE INDEX IF NOT EXISTS idx_bug_reports_created_at ON bug_reports(created_at)',
            
            # Contact submissions indexes
            'CREATE INDEX IF NOT EXISTS idx_contact_submissions_status ON contact_submissions(status)',
            'CREATE INDEX IF NOT EXISTS idx_contact_submissions_priority ON contact_submissions(priority)',
            'CREATE INDEX IF NOT EXISTS idx_contact_submissions_contact_type ON contact_submissions(contact_type)',
            'CREATE INDEX IF NOT EXISTS idx_contact_submissions_assigned_to ON contact_submissions(assigned_to)',
            'CREATE INDEX IF NOT EXISTS idx_contact_submissions_created_at ON contact_submissions(created_at)'
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Insert default support settings
        default_settings = [
            ('support_email_notifications', 'true'),
            ('support_auto_assign_tickets', 'false'),
            ('support_default_priority', 'Medium'),
            ('support_max_attachment_size_mb', '25'),
            ('support_allowed_file_types', '.jpg,.jpeg,.png,.gif,.bmp,.webp,.pdf,.doc,.docx,.xls,.xlsx,.txt,.log,.zip,.rar,.7z')
        ]
        
        for key, value in default_settings:
            cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ''', (key, value, datetime.now()))
        
        # Commit changes
        conn.commit()
        
        print("Support system tables migration completed successfully!")
        
        # Print table info
        tables = ['support_tickets', 'support_conversations', 'support_attachments', 
                  'bug_reports', 'contact_submissions']
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} records")
        
        return True
        
    except Exception as e:
        print(f"Error during support system migration: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_migration(db_path='restaurant_pos.db'):
    """Verify that support tables were created correctly"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if all tables exist
        required_tables = [
            'support_tickets',
            'support_conversations', 
            'support_attachments',
            'bug_reports',
            'contact_submissions'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            return False
        
        # Check table structures
        table_schemas = {
            'support_tickets': [
                'id', 'title', 'description', 'category', 'priority', 'status',
                'created_by', 'assigned_to', 'customer_email', 'customer_phone',
                'contact_info', 'order_id', 'table_id', 'created_at', 'updated_at'
            ],
            'support_conversations': [
                'id', 'ticket_id', 'sender_id', 'sender_role', 'message',
                'message_type', 'is_internal', 'created_at', 'updated_at'
            ],
            'support_attachments': [
                'id', 'ticket_id', 'bug_report_id', 'file_name', 'file_path',
                'file_size', 'file_hash', 'file_extension', 'attachment_type',
                'uploaded_by', 'description', 'created_at', 'updated_at'
            ],
            'bug_reports': [
                'id', 'title', 'description', 'category', 'severity', 'status',
                'reported_by', 'assigned_to', 'error_details', 'user_data',
                'contact_info', 'system_info', 'reproduction_steps',
                'expected_behavior', 'actual_behavior', 'module', 'function_name',
                'line_number', 'created_at', 'updated_at'
            ],
            'contact_submissions': [
                'id', 'name', 'email', 'phone', 'address', 'subject', 'message',
                'contact_type', 'priority', 'status', 'assigned_to',
                'created_at', 'updated_at'
            ]
        }
        
        all_tables_valid = True
        
        for table, required_columns in table_schemas.items():
            cursor.execute(f"PRAGMA table_info({table})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            missing_columns = []
            for column in required_columns:
                if column not in existing_columns:
                    missing_columns.append(column)
            
            if missing_columns:
                print(f"Table '{table}' missing columns: {missing_columns}")
                all_tables_valid = False
        
        if all_tables_valid:
            print("All support system tables verified successfully!")
            return True
        else:
            print("Support system tables verification failed!")
            return False
        
    except Exception as e:
        print(f"Error during migration verification: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def rollback_migration(db_path='restaurant_pos.db'):
    """Rollback support system tables (for testing purposes)"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Rolling back support system tables...")
        
        # Drop support system tables
        tables_to_drop = [
            'support_conversations',
            'support_attachments',
            'support_tickets',
            'bug_reports',
            'contact_submissions'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"Dropped table: {table}")
        
        # Remove support settings
        cursor.execute("DELETE FROM settings WHERE key LIKE 'support_%'")
        
        conn.commit()
        print("Support system tables rollback completed!")
        
        return True
        
    except Exception as e:
        print(f"Error during rollback: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Run migration when script is executed directly
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "migrate":
            migrate_support_tables()
        elif command == "verify":
            verify_migration()
        elif command == "rollback":
            rollback_migration()
        else:
            print("Usage: python add_support_tables.py [migrate|verify|rollback]")
    else:
        print("Usage: python add_support_tables.py [migrate|verify|rollback]")