"""
Support Manager for POS System
Centralized management for support tickets, conversations, and notifications
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from src.models.support_ticket import SupportTicket
from src.models.support_conversation import SupportConversation
from src.models.support_attachment import SupportAttachment
from src.utils.event_dispatcher import event_dispatcher, EventType
from src.utils.constants import *
from src.utils.email_service import EmailService

class SupportManager:
    """Centralized support system management"""
    
    def __init__(self, db, email_service=None):
        self.db = db
        self.email_service = email_service
        
        # Initialize models
        self.ticket_model = SupportTicket(db)
        self.conversation_model = SupportConversation(db)
        self.attachment_model = SupportAttachment(db)
        
        # Support settings (can be loaded from database)
        self.settings = {
            'auto_assign_tickets': True,
            'default_priority': PRIORITY_MEDIUM,
            'email_notifications': True,
            'max_attachment_size_mb': 25,
            'allowed_file_types': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                                   '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                                   '.txt', '.log', '.zip', '.rar', '.7z']
        }
    
    def create_ticket(self, ticket_data, attachments=None) -> Optional[int]:
        """Create a new support ticket with optional attachments"""
        try:
            # Create the ticket
            ticket_id = self.ticket_model.create(ticket_data)
            
            if not ticket_id:
                return None
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    if self._validate_attachment(attachment_path):
                        attachment_data = {
                            'ticket_id': ticket_id,
                            'file_path': attachment_path,
                            'uploaded_by': ticket_data['created_by']
                        }
                        self.attachment_model.add_attachment(attachment_data)
            
            # Auto-assign if enabled
            if self.settings.get('auto_assign_tickets'):
                self._auto_assign_ticket(ticket_id)
            
            # Send email notification if enabled
            if self.settings.get('email_notifications') and self.email_service:
                self._send_ticket_notification(ticket_id, 'created')
            
            # Dispatch event
            event_dispatcher.support_ticket_created(ticket_id, ticket_data)
            
            return ticket_id
            
        except Exception as e:
            print(f"Error creating support ticket: {e}")
            return None
    
    def update_ticket(self, ticket_id, update_data) -> bool:
        """Update support ticket"""
        try:
            success = self.ticket_model.update(ticket_id, update_data)
            
            if success:
                # Send email notification for status changes
                if self.settings.get('email_notifications') and self.email_service:
                    if 'status' in update_data:
                        self._send_ticket_notification(ticket_id, 'status_changed')
                
                # Dispatch event
                event_dispatcher.support_ticket_updated(ticket_id, update_data)
            
            return success
            
        except Exception as e:
            print(f"Error updating support ticket: {e}")
            return False
    
    def assign_ticket(self, ticket_id, assigned_to) -> bool:
        """Assign ticket to support staff"""
        try:
            success = self.ticket_model.assign_ticket(ticket_id, assigned_to)
            
            if success:
                # Send email notification
                if self.settings.get('email_notifications') and self.email_service:
                    self._send_ticket_notification(ticket_id, 'assigned')
                
                # Dispatch event
                event_dispatcher.support_ticket_assigned(ticket_id, assigned_to)
            
            return success
            
        except Exception as e:
            print(f"Error assigning support ticket: {e}")
            return False
    
    def close_ticket(self, ticket_id, resolution=None) -> bool:
        """Close support ticket"""
        try:
            success = self.ticket_model.close_ticket(ticket_id, resolution)
            
            if success:
                # Send email notification
                if self.settings.get('email_notifications') and self.email_service:
                    self._send_ticket_notification(ticket_id, 'closed')
                
                # Dispatch event
                event_dispatcher.support_ticket_closed(ticket_id, resolution)
            
            return success
            
        except Exception as e:
            print(f"Error closing support ticket: {e}")
            return False
    
    def add_conversation_message(self, conversation_data) -> Optional[int]:
        """Add message to support conversation"""
        try:
            conversation_id = self.conversation_model.add_message(conversation_data)
            
            if conversation_id:
                # Send email notification for new messages
                if self.settings.get('email_notifications') and self.email_service:
                    self._send_conversation_notification(conversation_id)
                
                # Dispatch event
                event_dispatcher.support_conversation_added(
                    conversation_data['ticket_id'],
                    conversation_id,
                    conversation_data
                )
            
            return conversation_id
            
        except Exception as e:
            print(f"Error adding conversation message: {e}")
            return None
    
    def get_ticket_with_details(self, ticket_id) -> Optional[Dict]:
        """Get ticket with full details including conversations and attachments"""
        try:
            # Get ticket details
            ticket = self.ticket_model.get_by_id(ticket_id)
            if not ticket:
                return None
            
            # Get conversations
            conversations = self.conversation_model.get_conversation_by_ticket(ticket_id)
            
            # Get attachments
            attachments = self.attachment_model.get_by_ticket(ticket_id)
            
            return {
                'ticket': ticket,
                'conversations': conversations,
                'attachments': attachments
            }
            
        except Exception as e:
            print(f"Error getting ticket details: {e}")
            return None
    
    def get_user_tickets(self, user_id, role=SUPPORT_ROLE_USER) -> List[Dict]:
        """Get tickets for a specific user based on their role"""
        try:
            if role == SUPPORT_ROLE_USER:
                # Regular users see tickets they created
                filters = {'created_by': user_id}
            else:
                # Support staff see tickets assigned to them or unassigned
                filters = {
                    'assigned_to': user_id,
                    'status': [TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS]
                }
            
            return self.ticket_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting user tickets: {e}")
            return []
    
    def get_ticket_statistics(self) -> Dict:
        """Get comprehensive support ticket statistics"""
        try:
            stats = self.ticket_model.get_ticket_stats()
            
            # Add additional statistics
            stats.update({
                'avg_resolution_time': self._calculate_avg_resolution_time(),
                'tickets_today': self._get_tickets_today(),
                'tickets_this_week': self._get_tickets_this_week(),
                'tickets_this_month': self._get_tickets_this_month(),
                'overdue_tickets': self._get_overdue_tickets()
            })
            
            return stats
            
        except Exception as e:
            print(f"Error getting ticket statistics: {e}")
            return {}
    
    def search_tickets(self, search_term, filters=None) -> List[Dict]:
        """Search tickets with optional filters"""
        try:
            search_filters = {'search': search_term}
            if filters:
                search_filters.update(filters)
            
            return self.ticket_model.get_all(search_filters)
            
        except Exception as e:
            print(f"Error searching tickets: {e}")
            return []
    
    def get_tickets_by_priority(self, priority=None) -> List[Dict]:
        """Get tickets filtered by priority"""
        try:
            filters = {}
            if priority:
                filters['priority'] = priority
            
            return self.ticket_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting tickets by priority: {e}")
            return []
    
    def get_unassigned_tickets(self) -> List[Dict]:
        """Get all unassigned tickets"""
        try:
            filters = {
                'assigned_to': None,
                'status': [TICKET_STATUS_OPEN, TICKET_STATUS_IN_PROGRESS]
            }
            
            return self.ticket_model.get_all(filters)
            
        except Exception as e:
            print(f"Error getting unassigned tickets: {e}")
            return []
    
    def _validate_attachment(self, file_path) -> bool:
        """Validate attachment file"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Check file size
            file_size_mb = self.attachment_model.get_file_size_mb(file_path)
            if file_size_mb > self.settings.get('max_attachment_size_mb', 25):
                return False
            
            # Check file type
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension not in self.settings.get('allowed_file_types', []):
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating attachment: {e}")
            return False
    
    def _auto_assign_ticket(self, ticket_id):
        """Automatically assign ticket to available support staff"""
        try:
            # This is a simple round-robin assignment
            # In a real system, you might want more sophisticated logic
            
            # Get all support staff users (this would need to be implemented)
            # For now, we'll just leave it unassigned
            pass
            
        except Exception as e:
            print(f"Error auto-assigning ticket: {e}")
    
    def _send_ticket_notification(self, ticket_id, notification_type):
        """Send email notification for ticket events"""
        try:
            if not self.email_service:
                return
            
            ticket = self.ticket_model.get_by_id(ticket_id)
            if not ticket:
                return
            
            # Prepare notification data
            notification_data = {
                'ticket_id': ticket_id,
                'title': ticket['title'],
                'status': ticket['status'],
                'priority': ticket['priority'],
                'notification_type': notification_type,
                'created_at': ticket['created_at']
            }
            
            # Send notification (implementation depends on EmailService)
            # This would need to be implemented based on EmailService capabilities
            
        except Exception as e:
            print(f"Error sending ticket notification: {e}")
    
    def _send_conversation_notification(self, conversation_id):
        """Send email notification for new conversation messages"""
        try:
            if not self.email_service:
                return
            
            conversation = self.conversation_model.get_by_id(conversation_id)
            if not conversation:
                return
            
            # Get ticket details
            ticket = self.ticket_model.get_by_id(conversation['ticket_id'])
            if not ticket:
                return
            
            # Prepare notification data
            notification_data = {
                'ticket_id': conversation['ticket_id'],
                'ticket_title': ticket['title'],
                'message': conversation['message'],
                'sender_role': conversation['sender_role'],
                'created_at': conversation['created_at']
            }
            
            # Send notification (implementation depends on EmailService)
            
        except Exception as e:
            print(f"Error sending conversation notification: {e}")
    
    def _calculate_avg_resolution_time(self) -> float:
        """Calculate average resolution time for closed tickets"""
        try:
            # This would need to be implemented with proper time tracking
            # For now, return a placeholder
            return 0.0
            
        except Exception as e:
            print(f"Error calculating average resolution time: {e}")
            return 0.0
    
    def _get_tickets_today(self) -> int:
        """Get count of tickets created today"""
        try:
            today = datetime.now().date()
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting today's tickets: {e}")
            return 0
    
    def _get_tickets_this_week(self) -> int:
        """Get count of tickets created this week"""
        try:
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting this week's tickets: {e}")
            return 0
    
    def _get_tickets_this_month(self) -> int:
        """Get count of tickets created this month"""
        try:
            # This would need to be implemented with proper date filtering
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting this month's tickets: {e}")
            return 0
    
    def _get_overdue_tickets(self) -> int:
        """Get count of overdue tickets"""
        try:
            # This would need to be implemented with proper SLA tracking
            # For now, return a placeholder
            return 0
            
        except Exception as e:
            print(f"Error getting overdue tickets: {e}")
            return 0
    
    def update_settings(self, settings: Dict) -> bool:
        """Update support manager settings"""
        try:
            self.settings.update(settings)
            return True
            
        except Exception as e:
            print(f"Error updating support settings: {e}")
            return False
    
    def get_settings(self) -> Dict:
        """Get current support manager settings"""
        return self.settings.copy()
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        try:
            # No specific resources to clean up for SupportManager
            # But we can log the cleanup for consistency
            print("SupportManager cleanup completed successfully")
            
        except Exception as e:
            print(f"Error during SupportManager cleanup: {e}")