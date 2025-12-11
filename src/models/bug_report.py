"""
Bug Report Model for POS System
Handles bug reporting with automatic error capture and system information
"""

import platform
import traceback
import sys
from datetime import datetime
from src.utils.encryption import get_encryption_manager
from src.utils.constants import *

class BugReport:
    """Bug report model with automatic error capture"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def create(self, bug_data):
        """Create a new bug report"""
        try:
            # Validate required fields
            if not bug_data.get('title'):
                raise ValueError("Bug title is required")
            if not bug_data.get('description'):
                raise ValueError("Bug description is required")
            if not bug_data.get('reported_by'):
                raise ValueError("Reported by user ID is required")
            
            # Collect automatic system information if not provided
            if not bug_data.get('system_info'):
                bug_data['system_info'] = self._collect_system_info()
            
            # Encrypt sensitive data
            encrypted_description = self.encryption_manager.encrypt_field(bug_data['description'])
            encrypted_error_details = None
            if bug_data.get('error_details'):
                encrypted_error_details = self.encryption_manager.encrypt_field(bug_data['error_details'])
            
            encrypted_user_data = None
            if bug_data.get('user_data'):
                encrypted_user_data = self.encryption_manager.encrypt_field(bug_data['user_data'])
            
            encrypted_contact_info = None
            if bug_data.get('contact_info'):
                encrypted_contact_info = self.encryption_manager.encrypt_field(bug_data['contact_info'])
            
            query = """
            INSERT INTO bug_reports (
                title, description, category, severity, status, reported_by,
                assigned_to, error_details, user_data, contact_info,
                system_info, reproduction_steps, expected_behavior, actual_behavior,
                module, function_name, line_number, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                bug_data['title'],
                encrypted_description,
                bug_data.get('category', TICKET_CATEGORY_BUG),
                bug_data.get('severity', SEVERITY_MEDIUM),
                bug_data.get('status', BUG_STATUS_NEW),
                bug_data['reported_by'],
                bug_data.get('assigned_to'),
                encrypted_error_details,
                encrypted_user_data,
                encrypted_contact_info,
                bug_data['system_info'],
                bug_data.get('reproduction_steps', ''),
                bug_data.get('expected_behavior', ''),
                bug_data.get('actual_behavior', ''),
                bug_data.get('module', ''),
                bug_data.get('function_name', ''),
                bug_data.get('line_number', ''),
                datetime.now(),
                datetime.now()
            )
            
            self.db.execute_query(query, params)
            bug_id = self.db.lastrowid()
            self.db.commit()
            
            return bug_id
            
        except Exception as e:
            print(f"Error creating bug report: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return None
    
    def create_from_exception(self, exception, title=None, user_id=None, additional_info=None):
        """Create bug report from an exception automatically"""
        try:
            # Get exception details
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            if not title:
                title = f"Automatic Bug Report: {exc_type.__name__}"
            
            # Get traceback
            error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Extract function and line info from traceback
            function_name = ''
            line_number = ''
            module = ''
            
            if exc_traceback:
                tb = exc_traceback
                while tb.tb_next:
                    tb = tb.tb_next
                
                function_name = tb.tb_frame.f_code.co_name
                line_number = str(tb.tb_lineno)
                module = tb.tb_frame.f_code.co_filename
                
                # Extract just the module name from full path
                if module:
                    module = module.split('\\')[-1].split('/')[-1]
            
            bug_data = {
                'title': title,
                'description': f"Automatic bug report generated from exception: {str(exc_value)}",
                'error_details': error_details,
                'category': TICKET_CATEGORY_BUG,
                'severity': SEVERITY_HIGH,  # Auto-reports are high severity by default
                'reported_by': user_id or 1,  # Default to system user if not provided
                'module': module,
                'function_name': function_name,
                'line_number': line_number,
                'user_data': additional_info
            }
            
            return self.create(bug_data)
            
        except Exception as e:
            print(f"Error creating automatic bug report: {e}")
            return None
    
    def get_by_id(self, bug_id):
        """Get bug report by ID"""
        query = """
        SELECT id, title, description, category, severity, status, reported_by,
               assigned_to, error_details, user_data, contact_info, system_info,
               reproduction_steps, expected_behavior, actual_behavior,
               module, function_name, line_number, created_at, updated_at
        FROM bug_reports
        WHERE id = ?
        """
        
        self.db.execute_query(query, (bug_id,))
        result = self.db.fetch_one()
        
        if not result:
            return None
        
        # Decrypt sensitive data
        bug_data = {
            'id': result[0],
            'title': result[1],
            'description': self.encryption_manager.decrypt_field(result[2]),
            'category': result[3],
            'severity': result[4],
            'status': result[5],
            'reported_by': result[6],
            'assigned_to': result[7],
            'error_details': self.encryption_manager.decrypt_field(result[8]) if result[8] else None,
            'user_data': self.encryption_manager.decrypt_field(result[9]) if result[9] else None,
            'contact_info': self.encryption_manager.decrypt_field(result[10]) if result[10] else None,
            'system_info': result[11],
            'reproduction_steps': result[12],
            'expected_behavior': result[13],
            'actual_behavior': result[14],
            'module': result[15],
            'function_name': result[16],
            'line_number': result[17],
            'created_at': result[18],
            'updated_at': result[19]
        }
        
        return bug_data
    
    def get_all(self, filters=None):
        """Get all bug reports with optional filters"""
        query = """
        SELECT id, title, category, severity, status, reported_by,
               assigned_to, module, function_name, created_at, updated_at
        FROM bug_reports
        WHERE 1=1
        """
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            
            if filters.get('severity'):
                query += " AND severity = ?"
                params.append(filters['severity'])
            
            if filters.get('category'):
                query += " AND category = ?"
                params.append(filters['category'])
            
            if filters.get('reported_by'):
                query += " AND reported_by = ?"
                params.append(filters['reported_by'])
            
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
        
        bug_reports = []
        for result in results:
            bug_reports.append({
                'id': result[0],
                'title': result[1],
                'category': result[2],
                'severity': result[3],
                'status': result[4],
                'reported_by': result[5],
                'assigned_to': result[6],
                'module': result[7],
                'function_name': result[8],
                'created_at': result[9],
                'updated_at': result[10]
            })
        
        return bug_reports
    
    def update(self, bug_id, update_data):
        """Update bug report"""
        try:
            # Build dynamic update query
            update_fields = []
            params = []
            
            # Handle encrypted fields
            if 'description' in update_data:
                update_fields.append("description = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['description']))
            
            if 'error_details' in update_data:
                update_fields.append("error_details = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['error_details']))
            
            if 'user_data' in update_data:
                update_fields.append("user_data = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['user_data']))
            
            if 'contact_info' in update_data:
                update_fields.append("contact_info = ?")
                params.append(self.encryption_manager.encrypt_field(update_data['contact_info']))
            
            # Handle non-encrypted fields
            for field in ['title', 'category', 'severity', 'status', 'assigned_to', 
                         'reproduction_steps', 'expected_behavior', 'actual_behavior',
                         'module', 'function_name', 'line_number']:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    params.append(update_data[field])
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            params.append(datetime.now())
            
            # Add bug ID to params
            params.append(bug_id)
            
            query = f"""
            UPDATE bug_reports 
            SET {', '.join(update_fields)}
            WHERE id = ?
            """
            
            self.db.execute_query(query, params)
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error updating bug report: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def assign_bug(self, bug_id, assigned_to):
        """Assign bug to developer"""
        return self.update(bug_id, {
            'assigned_to': assigned_to,
            'status': BUG_STATUS_ASSIGNED
        })
    
    def update_status(self, bug_id, status, resolution_notes=None):
        """Update bug status"""
        update_data = {'status': status}
        
        if resolution_notes:
            update_data['description'] = resolution_notes
        
        return self.update(bug_id, update_data)
    
    def mark_fixed(self, bug_id, fix_description=None):
        """Mark bug as fixed"""
        update_data = {'status': BUG_STATUS_FIXED}
        
        if fix_description:
            update_data['actual_behavior'] = f"FIXED: {fix_description}"
        
        return self.update(bug_id, update_data)
    
    def get_bug_stats(self):
        """Get bug report statistics"""
        stats = {}
        
        # Status counts
        status_query = """
        SELECT status, COUNT(*) as count
        FROM bug_reports
        GROUP BY status
        """
        self.db.execute_query(status_query)
        status_results = self.db.fetch_all()
        
        for status, count in status_results:
            stats[f'status_{status.lower().replace(" ", "_")}'] = count
        
        # Severity counts
        severity_query = """
        SELECT severity, COUNT(*) as count
        FROM bug_reports
        GROUP BY severity
        """
        self.db.execute_query(severity_query)
        severity_results = self.db.fetch_all()
        
        for severity, count in severity_results:
            stats[f'severity_{severity.lower()}'] = count
        
        # Total bugs
        total_query = "SELECT COUNT(*) FROM bug_reports"
        self.db.execute_query(total_query)
        stats['total_bugs'] = self.db.fetch_one()[0]
        
        # Open bugs
        open_query = "SELECT COUNT(*) FROM bug_reports WHERE status IN (?, ?, ?, ?)"
        self.db.execute_query(open_query, (BUG_STATUS_NEW, BUG_STATUS_ASSIGNED, 
                                        BUG_STATUS_IN_PROGRESS, BUG_STATUS_FIXED))
        stats['open_bugs'] = self.db.fetch_one()[0]
        
        return stats
    
    def delete(self, bug_id):
        """Delete bug report"""
        try:
            # First delete related attachments
            from src.models.support_attachment import SupportAttachment
            attachment_model = SupportAttachment(self.db)
            
            # Get attachments for this bug report
            attachments = attachment_model.get_by_bug_report(bug_id)
            for attachment in attachments:
                attachment_model.delete_attachment(attachment['id'])
            
            # Then delete bug report
            self.db.execute_query("DELETE FROM bug_reports WHERE id = ?", (bug_id,))
            self.db.commit()
            
            return True
            
        except Exception as e:
            print(f"Error deleting bug report: {e}")
            self.db.conn.rollback() if hasattr(self.db, 'conn') else None
            return False
    
    def _collect_system_info(self):
        """Collect system information for bug reports"""
        try:
            info = {
                'platform': platform.platform(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture(),
                'node': platform.node(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add application-specific info if available
            try:
                import src
                info['app_version'] = getattr(src, '__version__', 'Unknown')
            except:
                info['app_version'] = 'Unknown'
            
            return str(info)
            
        except Exception as e:
            return f"Error collecting system info: {e}"