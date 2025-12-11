"""
Support Conversation Model for POS System
Handles support ticket conversations and messages
"""

from datetime import datetime
from src.utils.encryption import get_encryption_manager
from src.utils.constants import *

class SupportConversation:
    """Support conversation model with encrypted messages"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def add_message(self, conversation_data):
        """Add a new message to support conversation"""
        try:
            # Validate required fields
            if not conversation_data.get('ticket_id'):
                raise ValueError("Ticket ID is required")
            if not conversation_data.get('message'):
                raise ValueError("Message is required")
            if not conversation_data.get('sender_id'):
                raise ValueError("Sender ID is required")
            
            # Encrypt message content
            encrypted_message = self.encryption_manager.encrypt_field(conversation_data['message'])
            
            query = """
            INSERT INTO support_conversations (
                ticket_id, sender_id, sender_role, message, message_type,
                is_internal, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                conversation_data['ticket_id'],
                conversation_data['sender_id'],
                conversation_data.get('sender_role', SUPPORT_ROLE_USER),
                encrypted_message,
                conversation_data.get('message_type', 'text'),
                conversation_data.get('is_internal', False),
                datetime.now()
            )
            
            self.db.execute_query(query, params)
            conversation_id = self.db.lastrowid()
            self.db.commit()
            
            return conversation_id
            
        except Exception as e:
            print(f"Error adding support conversation: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return None
    
    def get_conversation_by_ticket(self, ticket_id):
        """Get all conversations for a specific ticket"""
        query = """
        SELECT id, ticket_id, sender_id, sender_role, message, message_type,
               is_internal, created_at
        FROM support_conversations
        WHERE ticket_id = ?
        ORDER BY created_at ASC
        """
        
        self.db.execute_query(query, (ticket_id,))
        results = self.db.fetch_all()
        
        conversations = []
        for result in results:
            conversations.append({
                'id': result[0],
                'ticket_id': result[1],
                'sender_id': result[2],
                'sender_role': result[3],
                'message': self.encryption_manager.decrypt_field(result[4]),
                'message_type': result[5],
                'is_internal': bool(result[6]),
                'created_at': result[7]
            })
        
        return conversations
    
    def get_by_id(self, conversation_id):
        """Get conversation message by ID"""
        query = """
        SELECT id, ticket_id, sender_id, sender_role, message, message_type,
               is_internal, created_at
        FROM support_conversations
        WHERE id = ?
        """
        
        self.db.execute_query(query, (conversation_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'ticket_id': result[1],
            'sender_id': result[2],
            'sender_role': result[3],
            'message': self.encryption_manager.decrypt_field(result[4]),
            'message_type': result[5],
            'is_internal': bool(result[6]),
            'created_at': result[7]
        }
    
    def update_message(self, conversation_id, new_message):
        """Update a conversation message"""
        try:
            encrypted_message = self.encryption_manager.encrypt_field(new_message)
            
            query = """
            UPDATE support_conversations
            SET message = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (encrypted_message, datetime.now(), conversation_id)
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating support conversation: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def delete_message(self, conversation_id):
        """Delete a conversation message"""
        try:
            self.db.execute_query("DELETE FROM support_conversations WHERE id = ?", (conversation_id,))
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting support conversation: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def get_conversation_count(self, ticket_id):
        """Get count of messages for a ticket"""
        query = "SELECT COUNT(*) FROM support_conversations WHERE ticket_id = ?"
        self.db.execute_query(query, (ticket_id,))
        result = self.db.fetch_one()
        
        return result[0] if result else 0
    
    def get_latest_message(self, ticket_id):
        """Get the latest message for a ticket"""
        query = """
        SELECT id, sender_id, sender_role, message, created_at
        FROM support_conversations
        WHERE ticket_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        self.db.execute_query(query, (ticket_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'sender_id': result[1],
            'sender_role': result[2],
            'message': self.encryption_manager.decrypt_field(result[3]),
            'created_at': result[4]
        }
    
    def get_user_conversations(self, user_id, role=None):
        """Get all conversations for a specific user"""
        if role == SUPPORT_ROLE_USER:
            # For regular users, get conversations from tickets they created
            query = """
            SELECT sc.id, sc.ticket_id, sc.sender_id, sc.sender_role, sc.message, 
                   sc.message_type, sc.is_internal, sc.created_at, st.title
            FROM support_conversations sc
            JOIN support_tickets st ON sc.ticket_id = st.id
            WHERE st.created_by = ?
            ORDER BY sc.created_at DESC
            """
            params = (user_id,)
        else:
            # For support staff, get conversations from tickets they're assigned to
            query = """
            SELECT sc.id, sc.ticket_id, sc.sender_id, sc.sender_role, sc.message, 
                   sc.message_type, sc.is_internal, sc.created_at, st.title
            FROM support_conversations sc
            JOIN support_tickets st ON sc.ticket_id = st.id
            WHERE sc.sender_id = ? OR st.assigned_to = ?
            ORDER BY sc.created_at DESC
            """
            params = (user_id, user_id)
        
        self.db.execute_query(query, params)
        results = self.db.fetch_all()
        
        conversations = []
        for result in results:
            conversations.append({
                'id': result[0],
                'ticket_id': result[1],
                'sender_id': result[2],
                'sender_role': result[3],
                'message': self.encryption_manager.decrypt_field(result[4]),
                'message_type': result[5],
                'is_internal': bool(result[6]),
                'created_at': result[7],
                'ticket_title': result[8]
            })
        
        return conversations
    
    def mark_internal(self, conversation_id, is_internal=True):
        """Mark a conversation as internal (visible only to staff)"""
        try:
            query = """
            UPDATE support_conversations
            SET is_internal = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (is_internal, datetime.now(), conversation_id)
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error marking conversation as internal: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def get_internal_conversations(self, ticket_id):
        """Get only internal conversations for a ticket"""
        query = """
        SELECT id, ticket_id, sender_id, sender_role, message, message_type, created_at
        FROM support_conversations
        WHERE ticket_id = ? AND is_internal = 1
        ORDER BY created_at ASC
        """
        
        self.db.execute_query(query, (ticket_id,))
        results = self.db.fetch_all()
        
        conversations = []
        for result in results:
            conversations.append({
                'id': result[0],
                'ticket_id': result[1],
                'sender_id': result[2],
                'sender_role': result[3],
                'message': self.encryption_manager.decrypt_field(result[4]),
                'message_type': result[5],
                'created_at': result[6]
            })
        
        return conversations
    
    def get_public_conversations(self, ticket_id):
        """Get only public conversations for a ticket (visible to customers)"""
        query = """
        SELECT id, ticket_id, sender_id, sender_role, message, message_type, created_at
        FROM support_conversations
        WHERE ticket_id = ? AND is_internal = 0
        ORDER BY created_at ASC
        """
        
        self.db.execute_query(query, (ticket_id,))
        results = self.db.fetch_all()
        
        conversations = []
        for result in results:
            conversations.append({
                'id': result[0],
                'ticket_id': result[1],
                'sender_id': result[2],
                'sender_role': result[3],
                'message': self.encryption_manager.decrypt_field(result[4]),
                'message_type': result[5],
                'created_at': result[6]
            })
        
        return conversations