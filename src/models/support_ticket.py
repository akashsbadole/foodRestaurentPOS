"""
Support Ticket Model for POS System
Handles support ticket creation, management, and operations
"""

from datetime import datetime
from src.utils.encryption import get_encryption_manager
from src.utils.constants import *

class SupportTicket:
    """Support Ticket model with encrypted sensitive data"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def create(self, ticket_data):
        """Create a new support ticket"""
        try:
            # Validate required fields
            if not ticket_data.get('title'):
                raise ValueError("Ticket title is required")
            if not ticket_data.get('description'):
                raise ValueError("Ticket description is required")
            if not ticket_data.get('created_by'):
                raise ValueError("Created by user ID is required")
            
            # Encrypt sensitive data
            encrypted_description = self.encryption_manager.encrypt_field(ticket_data['description'])
            encrypted_contact_info = None
            if ticket_data.get('contact_info'):
                encrypted_contact_info = self.encryption_manager.encrypt_field(ticket_data['contact_info'])
            
            encrypted_customer_email = None
            if ticket_data.get('customer_email'):
                encrypted_customer_email = self.encryption_manager.encrypt_field(ticket_data['customer_email'])
            
            encrypted_customer_phone = None
            if ticket_data.get('customer_phone'):
                encrypted_customer_phone = self.encryption_manager.encrypt_field(ticket_data['customer_phone'])
            
            query = """
            INSERT INTO support_tickets (
                title, description, category, priority, status, created_by, 
                assigned_to, customer_email, customer_phone, contact_info,
                order_id, table_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                ticket_data['title'],
                encrypted_description,
                ticket_data.get('category', TICKET_CATEGORY_GENERAL),
                ticket_data.get('priority', PRIORITY_MEDIUM),
                ticket_data.get('status', TICKET_STATUS_OPEN),
                ticket_data['created_by'],
                ticket_data.get('assigned_to'),
                encrypted_customer_email,
                encrypted_customer_phone,
                encrypted_contact_info,
                ticket_data.get('order_id'),
                ticket_data.get('table_id'),
                datetime.now(),
                datetime.now()
            )
            
            self.db.execute_query(query, params)
            ticket_id = self.db.lastrowid()
            self.db.commit()
            
            return ticket_id
            
        except Exception as e:
            print(f"Error creating support ticket: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return None
    
    def get_by_id(self, ticket_id):
        """Get support ticket by ID"""
        query = """
        SELECT id, title, description, category, priority, status, created_by, 
               assigned_to, customer_email, customer_phone, contact_info,
               order_id, table_id, created_at, updated_at
        FROM support_tickets
        WHERE id = ?
        """
        
        self.db.execute_query(query, (ticket_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        # Decrypt sensitive data
        ticket_data = {
            'id': result[0],
            'title': result[1],
            'description': self.encryption_manager.decrypt_field(result[2]),
            'category': result[3],
            'priority': result[4],
            'status': result[5],
            'created_by': result[6],
            'assigned_to': result[7],
            'customer_email': self.encryption_manager.decrypt_field(result[8]) if result[8] else None,
            'customer_phone': self.encryption_manager.decrypt_field(result[9]) if result[9] else None,
            'contact_info': self.encryption_manager.decrypt_field(result[10]) if result[10] else None,
            'order_id': result[11],
            'table_id': result[12],
            'created_at': result[13],
            'updated_at': result[14]
        }
        
        return ticket_data
    
    def get_all(self, filters=None):
        """Get all support tickets with optional filters"""
        query = """
        SELECT id, title, category, priority, status, created_by, 
               assigned_to, created_at, updated_at
        FROM support_tickets
        WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            
            if filters.get('priority'):
                query += " AND priority = ?"
                params.append(filters['priority'])
            
            if filters.get('category'):
                query += " AND category = ?"
                params.append(filters['category'])
            
            if filters.get('created_by'):
                query += " AND created_by = ?"
                params.append(filters['created_by'])
            
            if filters.get('assigned_to'):
                query += " AND assigned_to = ?"
                params.append(filters['assigned_to'])
            
            if filters.get('search'):
                query += " AND (title LIKE ? OR id LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        
        query += " ORDER BY created_at DESC"
        
        self.db.execute_query(query, params)
        results = self.db.fetch_all()
        
        tickets = []
        for result in results:
            tickets.append({
                'id': result[0],
                'title': result[1],
                'category': result[2],
                'priority': result[3],
                'status': result[4],
                'created_by': result[5],
                'assigned_to': result[6],
                'created_at': result[7],
                'updated_at': result[8]
            })
        
        return tickets
    
    def update(self, ticket_id, update_data):
        """Update support ticket"""
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            # Handle encrypted fields
            if 'description' in update_data:
                update_fields.append("description = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['description']))
            
            if 'contact_info' in update_data:
                update_fields.append("contact_info = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['contact_info']))
            
            if 'customer_email' in update_data:
                update_fields.append("customer_email = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['customer_email']))
            
            if 'customer_phone' in update_data:
                update_fields.append("customer_phone = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['customer_phone']))
            
            # Handle non-encrypted fields
            for field in ['title', 'category', 'priority', 'status', 'assigned_to', 'order_id', 'table_id']:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    params.append(update_data[field])
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            
            # Add ticket ID to params
            params.append(ticket_id)
            
            query = f"""
            UPDATE support_tickets 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating support ticket: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def assign_ticket(self, ticket_id, assigned_to):
        """Assign ticket to support staff"""
        return self.update(ticket_id, {
            'assigned_to': assigned_to,
            'status': TICKET_STATUS_IN_PROGRESS
        })
    
    def close_ticket(self, ticket_id, resolution=None):
        """Close support ticket"""
        update_data = {'status': TICKET_STATUS_CLOSED}
        if resolution:
            update_data['description'] = resolution  # This will be encrypted
        
        return self.update(ticket_id, update_data)
    
    def get_ticket_stats(self):
        """Get support ticket statistics"""
        stats = {}
        
        # Status counts
        status_query = """
        SELECT status, COUNT(*) as count
        FROM support_tickets
        GROUP BY status
        """
        self.db.execute_query(status_query)
        status_results = self.db.fetch_all()
        
        for status, count in status_results:
            stats[f'status_{status.lower().replace(" ", "_")}'] = count
        
        # Priority counts
        priority_query = """
        SELECT priority, COUNT(*) as count
        FROM support_tickets
        GROUP BY priority
        """
        self.db.execute_query(priority_query)
        priority_results = self.db.fetch_all()
        
        for priority, count in priority_results:
            stats[f'priority_{priority.lower()}'] = count
        
        # Total tickets
        total_query = "SELECT COUNT(*) FROM support_tickets"
        self.db.execute_query(total_query)
        stats['total_tickets'] = self.db.fetch_one()[0]
        
        # Open tickets
        open_query = "SELECT COUNT(*) FROM support_tickets WHERE status IN (?, ?)"
        self.db.execute_query(open_query, (TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS))
        stats['open_tickets'] = self.db.fetch_one()[0]
        
        return stats
    
    def delete(self, ticket_id):
        """Delete support ticket"""
        try:
            # First delete related conversations and attachments
            self.db.execute_query("DELETE FROM support_conversations WHERE ticket_id = ?", (ticket_id,))
            self.db.execute_query("DELETE FROM support_attachments WHERE ticket_id = ?", (ticket_id,))
            
            # Then delete the ticket
            self.db.execute_query("DELETE FROM support_tickets WHERE id = ?", (ticket_id,))
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting support ticket: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False