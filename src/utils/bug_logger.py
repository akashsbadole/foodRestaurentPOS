"""
Bug Logger for POS System
Automatic error capture and bug reporting with system information
"""

import sys
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from src.models.bug_report import BugReport
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.utils.constants import *

class BugLogger:
    """Automatic bug logging and error capture system"""
    
    def __init__(self, db, auto_capture=True):
        self.db = db
        self.auto_capture = auto_capture
        self.bug_model = BugReport(db)
        
        # Configure logging for bug capture
        self.logger = logging.getLogger('bug_logger')
        self.logger.setLevel(logging.ERROR)
        
        # File handler for bug logs
        handler = logging.FileHandler('bugs.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Install exception hook if auto_capture is enabled
        if self.auto_capture:
            self.install_exception_hook()
    
    def install_exception_hook(self):
        """Install global exception hook for automatic bug capture"""
        sys.excepthook = self.exception_handler
    
    def exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler for automatic bug reporting"""
        try:
            # Log the exception
            self.logger.error(
                f"Uncaught exception: {exc_type.__name__}: {exc_value}",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
            
            # Create automatic bug report
            self.log_exception(exc_type, exc_value, exc_traceback)
            
            # Call original exception handler
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            
        except Exception as e:
            # Fallback logging if bug logger fails
            print(f"Error in bug logger exception handler: {e}")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def log_exception(self, exception_type=None, exception_value=None, 
                    exception_traceback=None, user_id=None, additional_info=None):
        """Log an exception and create bug report"""
        try:
            if exception_type is None or exception_value is None:
                # Get current exception info
                exc_type, exc_value, exc_traceback = sys.exc_info()
            
            if not exc_type or not exc_value:
                return None
            
            # Get exception details
            error_details = ''.join(traceback.format_exception(
                exc_type, exc_value, exc_traceback
            ))
            
            # Extract function and line info
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
                
                # Extract just module name from full path
                if module:
                    module = module.split('\\')[-1].split('/')[-1]
            
            # Create bug report data
            bug_data = {
                'title': f"Automatic Bug Report: {exc_type.__name__}",
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
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"Automatic bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create automatic bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in log_exception: {e}")
            return None
    
    def log_error(self, error_message, severity=SEVERITY_MEDIUM, 
                 user_id=None, additional_info=None):
        """Log an error message as a bug report"""
        try:
            bug_data = {
                'title': f"Error Report: {error_message[:50]}{'...' if len(error_message) > 50 else ''}",
                'description': error_message,
                'category': TICKET_CATEGORY_BUG,
                'severity': severity,
                'reported_by': user_id or 1,
                'user_data': additional_info
            }
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"Error bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create error bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in log_error: {e}")
            return None
    
    def log_performance_issue(self, operation, duration_ms, threshold_ms=5000, 
                          user_id=None, additional_info=None):
        """Log performance issues as bug reports"""
        try:
            if duration_ms < threshold_ms:
                return None  # Only log if above threshold
            
            bug_data = {
                'title': f"Performance Issue: {operation}",
                'description': f"Operation '{operation}' took {duration_ms}ms (threshold: {threshold_ms}ms)",
                'category': TICKET_CATEGORY_BUG,
                'severity': SEVERITY_MEDIUM,
                'reported_by': user_id or 1,
                'user_data': {
                    'operation': operation,
                    'duration_ms': duration_ms,
                    'threshold_ms': threshold_ms,
                    'additional_info': additional_info
                }
            }
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"Performance bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create performance bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in log_performance_issue: {e}")
            return None
    
    def log_ui_error(self, component, error_message, user_action=None, 
                   user_id=None, additional_info=None):
        """Log UI-related errors"""
        try:
            bug_data = {
                'title': f"UI Error: {component}",
                'description': f"UI error in component '{component}': {error_message}",
                'category': TICKET_CATEGORY_BUG,
                'severity': SEVERITY_MEDIUM,
                'reported_by': user_id or 1,
                'module': 'UI',
                'function_name': component,
                'user_data': {
                    'component': component,
                    'user_action': user_action,
                    'additional_info': additional_info
                }
            }
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"UI bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create UI bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in log_ui_error: {e}")
            return None
    
    def log_database_error(self, operation, error_message, query=None, 
                        user_id=None, additional_info=None):
        """Log database-related errors"""
        try:
            bug_data = {
                'title': f"Database Error: {operation}",
                'description': f"Database error during '{operation}': {error_message}",
                'category': TICKET_CATEGORY_BUG,
                'severity': SEVERITY_HIGH,  # Database errors are high severity
                'reported_by': user_id or 1,
                'module': 'Database',
                'function_name': operation,
                'user_data': {
                    'operation': operation,
                    'query': query,
                    'additional_info': additional_info
                }
            }
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"Database bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create database bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in log_database_error: {e}")
            return None
    
    def create_manual_bug_report(self, bug_data, user_id=None) -> Optional[int]:
        """Create a manual bug report from user input"""
        try:
            # Add system info if not provided
            if 'system_info' not in bug_data:
                bug_data['system_info'] = self.bug_model._collect_system_info()
            
            # Set reported by
            if user_id:
                bug_data['reported_by'] = user_id
            
            # Create bug report
            bug_id = self.bug_model.create(bug_data)
            
            if bug_id:
                # Dispatch event
                event_dispatcher.bug_report_created(bug_id, bug_data)
                
                # Log success
                self.logger.info(f"Manual bug report created with ID: {bug_id}")
                
                return bug_id
            else:
                self.logger.error("Failed to create manual bug report")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in create_manual_bug_report: {e}")
            return None
    
    def get_bug_statistics(self) -> Dict[str, Any]:
        """Get bug report statistics"""
        try:
            return self.bug_model.get_bug_stats()
            
        except Exception as e:
            self.logger.error(f"Error getting bug statistics: {e}")
            return {}
    
    def get_recent_bugs(self, limit=10) -> list:
        """Get recent bug reports"""
        try:
            return self.bug_model.get_all({'limit': limit})
            
        except Exception as e:
            self.logger.error(f"Error getting recent bugs: {e}")
            return []
    
    def search_bugs(self, search_term: str, filters: Dict = None) -> list:
        """Search bug reports"""
        try:
            search_filters = {'search': search_term}
            if filters:
                search_filters.update(filters)
            
            return self.bug_model.get_all(search_filters)
            
        except Exception as e:
            self.logger.error(f"Error searching bugs: {e}")
            return []
    
    def uninstall_exception_hook(self):
        """Uninstall the exception hook"""
        if self.auto_capture:
            sys.excepthook = sys.__excepthook__
            self.auto_capture = False
    
    def enable_auto_capture(self):
        """Enable automatic exception capture"""
        if not self.auto_capture:
            self.install_exception_hook()
            self.auto_capture = True
    
    def disable_auto_capture(self):
        """Disable automatic exception capture"""
        if self.auto_capture:
            self.uninstall_exception_hook()
    
    def is_auto_capture_enabled(self) -> bool:
        """Check if auto capture is enabled"""
        return self.auto_capture
    
    def set_log_level(self, level):
        """Set logging level for bug logger"""
        self.logger.setLevel(level)
    
    def get_bug_report(self, bug_id: int) -> Optional[Dict]:
        """Get bug report by ID"""
        try:
            return self.bug_model.get_by_id(bug_id)
            
        except Exception as e:
            self.logger.error(f"Error getting bug report: {e}")
            return None
    
    def update_bug_report(self, bug_id: int, update_data: Dict) -> bool:
        """Update bug report"""
        try:
            success = self.bug_model.update(bug_id, update_data)
            
            if success:
                # Dispatch event
                event_dispatcher.bug_report_updated(bug_id, update_data)
                
                # Log success
                self.logger.info(f"Bug report {bug_id} updated")
                
                return True
            else:
                self.logger.error(f"Failed to update bug report {bug_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating bug report: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        try:
            # Uninstall exception hook if it was installed
            if self.auto_capture:
                self.uninstall_exception_hook()
            
            # Close file handlers
            for handler in self.logger.handlers:
                handler.close()
            
            # Clear all handlers
            self.logger.handlers.clear()
            
            print("BugLogger cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during BugLogger cleanup: {e}")