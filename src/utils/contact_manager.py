"""
Contact Manager for POS System
Centralized management for contact form submissions and inquiries
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.models.contact_submission import ContactSubmission
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.utils.constants import *
from src.utils.email_service import EmailService

class ContactManager:
    """Centralized contact form management"""
    
    def __init__(self, db, email_service=None):
        self.db = db
        self.email_service = email_service
        
        # Initialize model
        self.contact_model = ContactSubmission(db)
        
        # Contact settings (can be loaded from database)
        self.settings = {
            'auto_assign_submissions': True,
            'default_priority': PRIORITY_MEDIUM,
            'email_notifications': True,
            'auto_reply_enabled': True,
            'response_time_hours': 24
        }
    
    def create_submission(self, contact_data) -> Optional[int]:
        """Create a new contact submission"""
        try:
            # Validate required fields
            if not contact_data.get('name'):
                raise ValueError("Name is required")
            if not contact_data.get('email'):
                raise ValueError("Email is required")
            if not contact_data.get('message'):
                raise ValueError("Message is required")
            
            # Set default values
            contact_data.setdefault('contact_type', CONTACT_TYPE_GENERAL)
            contact_data.setdefault('priority', self.settings.get('default_priority', PRIORITY_MEDIUM))
            contact_data.setdefault('status', 'New')
            
            # Create the submission
            submission_id = self.contact_model.create(contact_data)
            
            if not submission_id:
                return None
            
            # Auto-assign if enabled
            if self.settings.get('auto_assign_submissions'):
                self._auto_assign_submission(submission_id)
            
            # Send auto-reply if enabled
            if self.settings.get('auto_reply_enabled') and self.email_service:
                self._send_auto_reply(submission_id)
            
            # Send notification email if enabled
            if self.settings.get('email_notifications') and self.email_service:
                self._send_submission_notification(submission_id, 'created')
            
            # Dispatch event
            event_dispatcher.contact_submission_created(submission_id, contact_data)
            
            return submission_id
            
        except Exception as e:
            print(f"Error creating contact submission: {e}")
            return None
    
    def update_submission(self, submission_id, update_data) -> bool:
        """Update contact submission"""
        try:
            success = self.contact_model.update(submission_id, update_data)
            
            if success:
                # Send email notification for status changes
                if self.settings.get('email_notifications') and self.email_service:
                    if 'status' in update_data:
                        self._send_submission_notification(submission_id, 'status_changed')
                
                # Dispatch event (would need a new event type for updates)
                # For now, just log the update
                print(f"Contact submission {submission_id} updated")
            
            return success
            
        except Exception as e:
            print(f"Error updating contact submission: {e}")
            return False
    
    def assign_submission(self, submission_id, assigned_to) -> bool:
        """Assign contact submission to staff"""
        try:
            success = self.contact_model.assign_submission(submission_id, assigned_to)
            
            if success:
                # Send email notification
                if self.settings.get('email_notifications') and self.email_service:
                    self._send_submission_notification(submission_id, 'assigned')
                
                # Log assignment
                print(f"Contact submission {submission_id} assigned to {assigned_to}")
            
            return success
            
        except Exception as e:
            print(f"Error assigning contact submission: {e}")
            return False
    
    def close_submission(self, submission_id, resolution=None) -> bool:
        """Close contact submission"""
        try:
            success = self.contact_model.close_submission(submission_id, resolution)
            
            if success:
                # Send email notification
                if self.settings.get('email_notifications') and self.email_service:
                    self._send_submission_notification(submission_id, 'closed')
                
                # Log closure
                print(f"Contact submission {submission_id} closed")
            
            return success
            
        except Exception as e:
            print(f"Error closing contact submission: {e}")
            return False
    
    def get_submission_by_id(self, submission_id) -> Optional[Dict]:
        """Get contact submission by ID"""
        try:
            return self.contact_model.get_by_id(submission_id)
            
        except Exception as e:
            print(f"Error getting contact submission: {e}")
            return None
    
    def get_all_submissions(self, filters=None) -> List[Dict]:
        """Get all contact submissions with optional filters"""
        try:
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting contact submissions: {e}")
            return []
    
    def get_user_submissions(self, user_id, role=SUPPORT_ROLE_USER) -> List[Dict]:
        """Get submissions for a specific user based on their role"""
        try:
            if role == SUPPORT_ROLE_USER:
                # Regular users see their own submissions
                filters = {'reported_by': user_id}
            else:
                # Support staff see submissions assigned to them or unassigned
                filters = {
                    'assigned_to': user_id,
                    'status': ['New', 'In Progress']
                }
            
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting user submissions: {e}")
            return []
    
    def get_new_submissions(self) -> List[Dict]:
        """Get all new (unprocessed) submissions"""
        try:
            filters = {'status': 'New'}
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting new submissions: {e}")
            return []
    
    def get_submissions_by_type(self, contact_type) -> List[Dict]:
        """Get submissions filtered by contact type"""
        try:
            filters = {'contact_type': contact_type}
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting submissions by type: {e}")
            return []
    
    def get_submissions_by_priority(self, priority) -> List[Dict]:
        """Get submissions filtered by priority"""
        try:
            filters = {'priority': priority}
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting submissions by priority: {e}")
            return []
    
    def get_unassigned_submissions(self) -> List[Dict]:
        """Get all unassigned submissions"""
        try:
            filters = {
                'assigned_to': None,
                'status': ['New', 'In Progress']
            }
            
            return self.contact_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting unassigned submissions: {e}")
            return []
    
    def search_submissions(self, search_term, filters=None) -> List[Dict]:
        """Search submissions by name, email, or subject"""
        try:
            if filters:
                # Combine search with filters
                # This would need to be implemented in the model
                pass
            
            return self.contact_model.search_submissions(search_term)
            
        except Exception as e:
            print(f"Error searching submissions: {e}")
            return []
    
    def get_submissions_by_date_range(self, start_date, end_date) -> List[Dict]:
        """Get submissions within a date range"""
        try:
            return self.contact_model.get_submissions_by_date_range(start_date, end_date)
            
        except Exception as e:
            print(f"Error getting submissions by date range: {e}")
            return []
    
    def get_recent_submissions(self, limit=10) -> List[Dict]:
        """Get recent contact submissions"""
        try:
            return self.contact_model.get_recent_submissions(limit)
            
        except Exception as e:
            print(f"Error getting recent submissions: {e}")
            return []
    
    def get_submission_statistics(self) -> Dict:
        """Get comprehensive contact submission statistics"""
        try:
            stats = self.contact_model.get_submission_stats()
            
            # Add additional statistics
            stats.update({
                'avg_response_time': self._calculate_avg_response_time(),
                'submissions_today': self._get_submissions_today(),
                'submissions_this_week': self._get_submissions_this_week(),
                'submissions_this_month': self._get_submissions_this_month(),
                'overdue_submissions': self._get_overdue_submissions()
            })
            
            return stats
            
        except Exception as e:
            print(f"Error getting submission statistics: {e}")
            return {}
    
    def _auto_assign_submission(self, submission_id):
        """Automatically assign submission to available staff"""
        try:
            # This is a simple round-robin assignment
            # In a real system, you might want more sophisticated logic
            
            # Get all support staff users (this would need to be implemented)
            # For now, we'll just leave it unassigned
            pass
            
        except Exception as e:
            print(f"Error auto-assigning submission: {e}")
    
    def _send_auto_reply(self, submission_id):
        """Send automatic reply to contact submission"""
        try:
            if not self.email_service:
                return
            
            submission = self.contact_model.get_by_id(submission_id)
            if not submission:
                return
            
            # Prepare auto-reply message
            auto_reply_subject = f"Re: {submission.get('subject', 'Your Inquiry')}"
            auto_reply_body = f"""
            Dear {submission['name']},
            
            Thank you for contacting us. We have received your message and will get back to you within {self.settings.get('response_time_hours', 24)} hours.
            
            Your reference number: #{submission_id}
            
            Best regards,
            Support Team
            """
            
            # Send auto-reply (implementation depends on EmailService)
            # This would need to be implemented based on EmailService capabilities
            print(f"Auto-reply sent to {submission['email']}: {auto_reply_subject}")
            
        except Exception as e:
            print(f"Error sending auto reply: {e}")
    
    def _send_submission_notification(self, submission_id, notification_type):
        """Send email notification for submission events"""
        try:
            if not self.email_service:
                return
            
            submission = self.contact_model.get_by_id(submission_id)
            if not submission:
                return
            
            # Prepare notification data
            notification_data = {
                'submission_id': submission_id,
                'name': submission['name'],
                'email': submission['email'],
                'subject': submission['subject'],
                'contact_type': submission['contact_type'],
                'priority': submission['priority'],
                'status': submission['status'],
                'notification_type': notification_type,
                'created_at': submission['created_at']
            }
            
            # Send notification (implementation depends on EmailService)
            print(f"Notification sent for submission {submission_id}: {notification_type}")
            
        except Exception as e:
            print(f"Error sending submission notification: {e}")
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time for submissions"""
        try:
            # This would need to be implemented with proper time tracking
            # For now, return a placeholder
            return 0.0
            
        except Exception as e:
            print(f"Error calculating average response time: {e}")
            return 0.0
    
    def _get_submissions_today(self) -> int:
        """Get count of submissions created today"""
        try:
            today = datetime.now().date()
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting today's submissions: {e}")
            return 0
    
    def _get_submissions_this_week(self) -> int:
        """Get count of submissions created this week"""
        try:
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting this week's submissions: {e}")
            return 0
    
    def _get_submissions_this_month(self) -> int:
        """Get count of submissions created this month"""
        try:
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting this month's submissions: {e}")
            return 0
    
    def _get_overdue_submissions(self) -> int:
        """Get count of overdue submissions"""
        try:
            # This would need to be implemented with proper SLA tracking
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting overdue submissions: {e}")
            return 0
    
    def update_settings(self, settings: Dict) -> bool:
        """Update contact manager settings"""
        try:
            self.settings.update(settings)
            return True
            
        except Exception as e:
            print(f"Error updating contact settings: {e}")
            return False
    
    def get_settings(self) -> Dict:
        """Get current contact manager settings"""
        return self.settings.copy()
    
    def delete_submission(self, submission_id) -> bool:
        """Delete contact submission"""
        try:
            success = self.contact_model.delete(submission_id)
            
            if success:
                print(f"Contact submission {submission_id} deleted")
            
            return success
            
        except Exception as e:
            print(f"Error deleting contact submission: {e}")
            return False