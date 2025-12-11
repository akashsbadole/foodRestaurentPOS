"""
Contact Submission Model for POS System
Handles contact form submissions and inquiries
"""

from datetime import datetime
from src.utils.encryption import get_encryption_manager
from src.utils.constants import *

class ContactSubmission:
    """Contact submission model with encrypted personal data"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def create(self, contact_data):
        """Create a new contact submission"""
        try:
            # Validate required fields
            if not contact_data.get('name'):
                raise ValueError("Name is required")
            if not contact_data.get('email'):
                raise ValueError("Email is required")
            if not contact_data.get('message'):
                raise ValueError("Message is required")
            
            # Encrypt sensitive data
            encrypted_name = self.encryption_manager.encrypt_field(contact_data['name'])
            encrypted_email = self.encryption_manager.encrypt_field(contact_data['email'])
            encrypted_phone = None
            if contact_data.get('phone'):
                encrypted_phone = self.encryption_manager.encrypt_field(contact_data['phone'])
            encrypted_message = self.encryption_manager.encrypt_field(contact_data['message'])
            encrypted_address = None
            if contact_data.get('address'):
                encrypted_address = self.encryption_manager.encrypt_field(contact_data['address'])
            
            query = """
            INSERT INTO contact_submissions (
                name, email, phone, address, subject, message, contact_type,
                priority, status, assigned_to, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                encrypted_name,
                encrypted_email,
                encrypted_phone,
                encrypted_address,
                contact_data.get('subject', ''),
                encrypted_message,
                contact_data.get('contact_type', CONTACT_TYPE_GENERAL),
                contact_data.get('priority', PRIORITY_MEDIUM),
                contact_data.get('status', 'New'),
                contact_data.get('assigned_to'),
                datetime.now(),
                datetime.now()
            )
            
            self.db.execute_query(query, params)
            submission_id = self.db.lastrowid()
            self.db.commit()
            
            return submission_id
            
        except Exception as e:
            print(f"Error creating contact submission: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return None
    
    def get_by_id(self, submission_id):
        """Get contact submission by ID"""
        query = """
        SELECT id, name, email, phone, address, subject, message, contact_type,
               priority, status, assigned_to, created_at, updated_at
        FROM contact_submissions
        WHERE id = ?
        """
        
        self.db.execute_query(query, (submission_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        # Decrypt sensitive data
        contact_data = {
            'id': result[0],
            'name': self.encryption_manager.decrypt_field(result[1]),
            'email': self.encryption_manager.decrypt_field(result[2]),
            'phone': self.encryption_manager.decrypt_field(result[3]) if result[3] else None,
            'address': self.encryption_manager.decrypt_field(result[4]) if result[4] else None,
            'subject': result[5],
            'message': self.encryption_manager.decrypt_field(result[6]),
            'contact_type': result[7],
            'priority': result[8],
            'status': result[9],
            'assigned_to': result[10],
            'created_at': result[11],
            'updated_at': result[12]
        }
        
        return contact_data
    
    def get_all(self, filters=None):
        """Get all contact submissions with optional filters"""
        query = """
        SELECT id, name, email, subject, contact_type, priority, status,
               assigned_to, created_at, updated_at
        FROM contact_submissions
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
            
            if filters.get('contact_type'):
                query += " AND contact_type = ?"
                params.append(filters['contact_type'])
            
            if filters.get('assigned_to'):
                query += " AND assigned_to = ?"
                params.append(filters['assigned_to'])
            
            if filters.get('search'):
                query += " AND (subject LIKE ? OR id LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        
        query += " ORDER BY created_at DESC"
        
        self.db.execute_query(query, params)
        results = self.db.fetch_all()
        
        submissions = []
        for result in results:
            submissions.append({
                'id': result[0],
                'name': self.encryption_manager.decrypt_field(result[1]),
                'email': self.encryption_manager.decrypt_field(result[2]),
                'subject': result[3],
                'contact_type': result[4],
                'priority': result[5],
                'status': result[6],
                'assigned_to': result[7],
                'created_at': result[8],
                'updated_at': result[9]
            })
        
        return submissions
    
    def update(self, submission_id, update_data):
        """Update contact submission"""
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            # Handle encrypted fields
            if 'name' in update_data:
                update_fields.append("name = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['name']))
            
            if 'email' in update_data:
                update_fields.append("email = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['email']))
            
            if 'phone' in update_data:
                update_fields.append("phone = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['phone']))
            
            if 'address' in update_data:
                update_fields.append("address = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['address']))
            
            if 'message' in update_data:
                update_fields.append("message = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['message']))
            
            # Handle non-encrypted fields
            for field in ['subject', 'contact_type', 'priority', 'status', 'assigned_to']:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    params.append(update_data[field])
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            
            # Add submission ID to params
            params.append(submission_id)
            
            query = f"""
            UPDATE contact_submissions 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating contact submission: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def assign_submission(self, submission_id, assigned_to):
        """Assign contact submission to staff"""
        return self.update(submission_id, {
            'assigned_to': assigned_to,
            'status': 'In Progress'
        })
    
    def update_status(self, submission_id, status, notes=None):
        """Update contact submission status"""
        update_data = {'status': status}
        
        if notes:
            update_data['message'] = notes
        
        return self.update(submission_id, update_data)
    
    def close_submission(self, submission_id, resolution=None):
        """Close contact submission"""
        update_data = {'status': 'Closed'}
        
        if resolution:
            update_data['subject'] = f"RESOLVED: {resolution}"
        
        return self.update(submission_id, update_data)
    
    def get_submission_stats(self):
        """Get contact submission statistics"""
        stats = {}
        
        # Status counts
        status_query = """
        SELECT status, COUNT(*) as count
        FROM contact_submissions
        GROUP BY status
        """
        self.db.execute_query(status_query)
        status_results = self.db.fetch_all()
        
        for status, count in status_results:
            stats[f'status_{status.lower().replace(" ", "_")}'] = count
        
        # Type counts
        type_query = """
        SELECT contact_type, COUNT(*) as count
        FROM contact_submissions
        GROUP BY contact_type
        """
        self.db.execute_query(type_query)
        type_results = self.db.fetch_all()
        
        for contact_type, count in type_results:
            stats[f'type_{contact_type.lower().replace(" ", "_")}'] = count
        
        # Priority counts
        priority_query = """
        SELECT priority, COUNT(*) as count
        FROM contact_submissions
        GROUP BY priority
        """
        self.db.execute_query(priority_query)
        priority_results = self.db.fetch_all()
        
        for priority, count in priority_results:
            stats[f'priority_{priority.lower()}'] = count
        
        # Total submissions
        total_query = "SELECT COUNT(*) FROM contact_submissions"
        self.db.execute_query(total_query)
        stats['total_submissions'] = self.db.fetch_one()[0]
        
        # New submissions
        new_query = "SELECT COUNT(*) FROM contact_submissions WHERE status = 'New'"
        self.db.execute_query(new_query)
        stats['new_submissions'] = self.db.fetch_one()[0]
        
        return stats
    
    def delete(self, submission_id):
        """Delete contact submission"""
        try:
            self.db.execute_query("DELETE FROM contact_submissions WHERE id = ?", (submission_id,))
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting contact submission: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def get_recent_submissions(self, limit=10):
        """Get recent contact submissions"""
        query = """
        SELECT id, name, email, subject, contact_type, priority, status, created_at
        FROM contact_submissions
        ORDER BY created_at DESC
        LIMIT ?
        """
        
        self.db.execute_query(query, (limit,))
        results = self.db.fetch_all()
        
        submissions = []
        for result in results:
            submissions.append({
                'id': result[0],
                'name': self.encryption_manager.decrypt_field(result[1]),
                'email': self.encryption_manager.decrypt_field(result[2]),
                'subject': result[3],
                'contact_type': result[4],
                'priority': result[5],
                'status': result[6],
                'created_at': result[7]
            })
        
        return submissions
    
    def get_submissions_by_date_range(self, start_date, end_date):
        """Get submissions within a date range"""
        query = """
        SELECT id, name, email, subject, contact_type, priority, status, created_at
        FROM contact_submissions
        WHERE DATE(created_at) BETWEEN DATE(?) AND DATE(?)
        ORDER BY created_at DESC
        """
        
        self.db.execute_query(query, (start_date, end_date))
        results = self.db.fetch_all()
        
        submissions = []
        for result in results:
            submissions.append({
                'id': result[0],
                'name': self.encryption_manager.decrypt_field(result[1]),
                'email': self.encryption_manager.decrypt_field(result[2]),
                'subject': result[3],
                'contact_type': result[4],
                'priority': result[5],
                'status': result[6],
                'created_at': result[7]
            })
        
        return submissions
    
    def search_submissions(self, search_term):
        """Search submissions by name, email, or subject"""
        query = """
        SELECT id, name, email, subject, contact_type, priority, status, created_at
        FROM contact_submissions
        WHERE name LIKE ? OR email LIKE ? OR subject LIKE ? OR message LIKE ?
        ORDER BY created_at DESC
        """
        
        search_pattern = f"%{search_term}%"
        params = [search_pattern] * 4
        
        self.db.execute_query(query, params)
        results = self.db.fetch_all()
        
        submissions = []
        for result in results:
            submissions.append({
                'id': result[0],
                'name': self.encryption_manager.decrypt_field(result[1]),
                'email': self.encryption_manager.decrypt_field(result[2]),
                'subject': result[3],
                'contact_type': result[4],
                'priority': result[5],
                'status': result[6],
                'created_at': result[7]
            })
        
        return submissions