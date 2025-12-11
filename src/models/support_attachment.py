"""
Support Attachment Model for POS System
Handles file attachments for support tickets and bug reports
"""

import os
import hashlib
from datetime import datetime
from src.utils.encryption import get_encryption_manager
from src.utils.constants import *

class SupportAttachment:
    """Support attachment model for handling file uploads"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def add_attachment(self, attachment_data):
        """Add a new attachment to support ticket or bug report"""
        try:
            # Validate required fields
            if not attachment_data.get('file_path'):
                raise ValueError("File path is required")
            if not attachment_data.get('ticket_id') and not attachment_data.get('bug_report_id'):
                raise ValueError("Either ticket_id or bug_report_id is required")
            if not attachment_data.get('uploaded_by'):
                raise ValueError("Uploaded by user ID is required")
            
            # Check if file exists
            if not os.path.exists(attachment_data['file_path']):
                raise ValueError("File does not exist")
            
            # Get file info
            file_path = attachment_data['file_path']
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
            # Calculate file hash for integrity check
            file_hash = self._calculate_file_hash(file_path)
            
            # Determine attachment type based on file extension
            attachment_type = self._determine_attachment_type(file_extension, file_name)
            
            # Encrypt file path for security
            encrypted_file_path = self.encryption_manager.encrypt_field(file_path)
            
            query = """
            INSERT INTO support_attachments (
                ticket_id, bug_report_id, file_name, file_path, file_size,
                file_hash, file_extension, attachment_type, uploaded_by,
                description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                attachment_data.get('ticket_id'),
                attachment_data.get('bug_report_id'),
                file_name,
                encrypted_file_path,
                file_size,
                file_hash,
                file_extension,
                attachment_type,
                attachment_data['uploaded_by'],
                attachment_data.get('description', ''),
                datetime.now()
            )
            
            self.db.execute_query(query, params)
            attachment_id = self.db.lastrowid()
            self.db.commit()
            
            return attachment_id
            
        except Exception as e:
            print(f"Error adding support attachment: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return None
    
    def get_by_id(self, attachment_id):
        """Get attachment by ID"""
        query = """
        SELECT id, ticket_id, bug_report_id, file_name, file_path, file_size,
               file_hash, file_extension, attachment_type, uploaded_by,
               description, created_at
        FROM support_attachments
        WHERE id = ?
        """
        
        self.db.execute_query(query, (attachment_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        return {
            'id': result[0],
            'ticket_id': result[1],
            'bug_report_id': result[2],
            'file_name': result[3],
            'file_path': self.encryption_manager.decrypt_field(result[4]),
            'file_size': result[5],
            'file_hash': result[6],
            'file_extension': result[7],
            'attachment_type': result[8],
            'uploaded_by': result[9],
            'description': result[10],
            'created_at': result[11]
        }
    
    def get_by_ticket(self, ticket_id):
        """Get all attachments for a support ticket"""
        query = """
        SELECT id, file_name, file_size, file_extension, attachment_type,
               uploaded_by, description, created_at
        FROM support_attachments
        WHERE ticket_id = ?
        ORDER BY created_at ASC
        """
        
        self.db.execute_query(query, (ticket_id,))
        results = self.db.fetch_all()
        
        attachments = []
        for result in results:
            attachments.append({
                'id': result[0],
                'file_name': result[1],
                'file_size': result[2],
                'file_extension': result[3],
                'attachment_type': result[4],
                'uploaded_by': result[5],
                'description': result[6],
                'created_at': result[7]
            })
        
        return attachments
    
    def get_by_bug_report(self, bug_report_id):
        """Get all attachments for a bug report"""
        query = """
        SELECT id, file_name, file_size, file_extension, attachment_type,
               uploaded_by, description, created_at
        FROM support_attachments
        WHERE bug_report_id = ?
        ORDER BY created_at ASC
        """
        
        self.db.execute_query(query, (bug_report_id,))
        results = self.db.fetch_all()
        
        attachments = []
        for result in results:
            attachments.append({
                'id': result[0],
                'file_name': result[1],
                'file_size': result[2],
                'file_extension': result[3],
                'attachment_type': result[4],
                'uploaded_by': result[5],
                'description': result[6],
                'created_at': result[7]
            })
        
        return attachments
    
    def update_description(self, attachment_id, description):
        """Update attachment description"""
        try:
            query = """
            UPDATE support_attachments
            SET description = ?, updated_at = ?
            WHERE id = ?
            """
            
            params = (description, datetime.now(), attachment_id)
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating attachment description: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def delete_attachment(self, attachment_id):
        """Delete attachment and optionally remove file"""
        try:
            # Get attachment info first
            attachment = self.get_by_id(attachment_id)
            if not attachment:
                return False
            
            # Delete from database
            self.db.execute_query("DELETE FROM support_attachments WHERE id = ?", (attachment_id,))
            self.db.commit()
            
            # Optionally delete the actual file
            # Note: Uncomment the following lines if you want to delete files from disk
            # try:
            #     if os.path.exists(attachment['file_path']):
            #         os.remove(attachment['file_path'])
            # except Exception as e:
            #     print(f"Error deleting file: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting support attachment: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def verify_file_integrity(self, attachment_id):
        """Verify file integrity using stored hash"""
        try:
            attachment = self.get_by_id(attachment_id)
            if not attachment:
                return False, "Attachment not found"
            
            if not os.path.exists(attachment['file_path']):
                return False, "File not found on disk"
            
            # Calculate current file hash
            current_hash = self._calculate_file_hash(attachment['file_path'])
            
            # Compare with stored hash
            if current_hash == attachment['file_hash']:
                return True, "File integrity verified"
            else:
                return False, "File integrity check failed - file may be corrupted"
                
        except Exception as e:
            return False, f"Error verifying file integrity: {e}"
    
    def get_attachment_stats(self, ticket_id=None, bug_report_id=None):
        """Get attachment statistics"""
        stats = {}
        
        if ticket_id:
            query = """
            SELECT COUNT(*) as total_count, 
                   SUM(file_size) as total_size,
                   attachment_type,
                   COUNT(*) as type_count
            FROM support_attachments
            WHERE ticket_id = ?
            GROUP BY attachment_type
            """
            self.db.execute_query(query, (ticket_id,))
        elif bug_report_id:
            query = """
            SELECT COUNT(*) as total_count, 
                   SUM(file_size) as total_size,
                   attachment_type,
                   COUNT(*) as type_count
            FROM support_attachments
            WHERE bug_report_id = ?
            GROUP BY attachment_type
            """
            self.db.execute_query(query, (bug_report_id,))
        else:
            return stats
        
        results = self.db.fetch_all()
        
        total_count = 0
        total_size = 0
        
        for result in results:
            total_count += result[2]  # type_count
            total_size += result[1] or 0  # total_size
            stats[f'type_{result[2].lower().replace(" ", "_")}'] = result[2]
        
        stats['total_count'] = total_count
        stats['total_size'] = total_size
        stats['total_size_mb'] = round(total_size / (1024 * 1024), 2) if total_size else 0
        
        return stats
    
    def _calculate_file_hash(self, file_path):
        """Calculate SHA-256 hash of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read and update hash in chunks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return None
    
    def _determine_attachment_type(self, file_extension, file_name):
        """Determine attachment type based on file extension"""
        file_extension = file_extension.lower()
        file_name = file_name.lower()
        
        # Image files
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return ATTACHMENT_TYPE_IMAGE
        elif 'screenshot' in file_name or 'screen' in file_name:
            return ATTACHMENT_TYPE_SCREENSHOT
        
        # Log files
        elif file_extension in ['.log', '.txt'] or 'log' in file_name:
            return ATTACHMENT_TYPE_LOG
        
        # Document files
        elif file_extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
            return ATTACHMENT_TYPE_DOCUMENT
        
        # Default to other
        else:
            return ATTACHMENT_TYPE_OTHER
    
    def is_allowed_file_type(self, file_extension):
        """Check if file type is allowed for upload"""
        allowed_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',  # Images
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
            '.txt', '.log',  # Text and log files
            '.zip', '.rar', '.7z'  # Archives
        ]
        
        return file_extension.lower() in allowed_extensions
    
    def get_file_size_mb(self, file_path):
        """Get file size in MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            return round(size_bytes / (1024 * 1024), 2)
        except:
            return 0