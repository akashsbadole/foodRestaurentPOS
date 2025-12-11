"""
Footer Generator for Desktop POS System
Handles dynamic footer generation for receipts and documents
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from models.settings import Settings


class FooterGenerator:
    """
    Footer Generator for creating dynamic footers in desktop version
    """
    
    def __init__(self, settings_manager=None):
        """
        Initialize footer generator
        
        Args:
            settings_manager: Settings manager instance
        """
        self.settings_manager = settings_manager
        self.load_settings()
    
    def load_settings(self):
        """Load footer settings"""
        if self.settings_manager:
            self.footer_settings = self.settings_manager.get_footer_settings()
        else:
            # Use default settings if no settings manager
            self.footer_settings = {
                'footer_enabled': 'true',
                'footer_template': 'default',
                'footer_custom_text': 'Thank you for your business!',
                'footer_alignment': 'center',
                'footer_font_size': '10',
                'footer_show_user_name': 'true',
                'footer_show_receipt_info': 'true',
                'footer_show_business_info': 'true',
                'footer_multiline': 'false',
                'footer_line1': '',
                'footer_line2': '',
                'footer_line3': '',
                'footer_show_logo': 'false',
                'footer_logo_path': '',
                'footer_different_receipts': 'false',
                'footer_invoice_template': 'default',
                'footer_receipt_template': 'default'
            }
    
    def generate_footer(self, document_type: str = 'receipt', 
                      order_data: Dict = None, 
                      user_data: Dict = None) -> List[str]:
        """
        Generate footer lines for specified document type
        
        Args:
            document_type: Type of document (receipt, invoice, kot, etc.)
            order_data: Order information for dynamic content
            user_data: User information for dynamic content
            
        Returns:
            List of footer lines
        """
        if not self.footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return []
        
        footer_lines = []
        template = self.footer_settings.get('footer_template', 'default')
        
        # Use specific template if configured for different receipts
        if self.footer_settings.get('footer_different_receipts', 'false').lower() == 'true':
            if document_type == 'invoice':
                template = self.footer_settings.get('footer_invoice_template', 'default')
            elif document_type == 'receipt':
                template = self.footer_settings.get('footer_receipt_template', 'default')
        
        if template == 'minimal':
            footer_lines = self._generate_minimal_footer(order_data, user_data)
        elif template == 'detailed':
            footer_lines = self._generate_detailed_footer(order_data, user_data)
        else:
            footer_lines = self._generate_default_footer(order_data, user_data)
        
        return footer_lines
    
    def _generate_default_footer(self, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate default footer"""
        footer_lines = []
        
        # Custom text
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            processed_text = self._process_placeholders(custom_text, order_data, user_data)
            footer_lines.append(processed_text)
        
        # User info
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and user_data:
            username = user_data.get('username', user_data.get('name', 'Staff'))
            footer_lines.append(f"Served by: {username}")
        
        # Receipt info
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            order_number = order_data.get('order_number', order_data.get('order_id', 'N/A'))
            created_at = order_data.get('created_at', '')
            if created_at:
                formatted_date = self._format_datetime(created_at)
                footer_lines.append(f"Receipt #{order_number} - {formatted_date}")
        
        # Business info
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            business_info = []
            # Use default values when no settings manager is provided
            restaurant_name = 'Restaurant POS'
            if restaurant_name:
                business_info.append(restaurant_name)
            
            restaurant_phone = '+91-9876543210'
            if restaurant_phone:
                business_info.append(restaurant_phone)
            
            gst_number = 'GSTIN1234567890'
            if gst_number:
                business_info.append(f"GST: {gst_number}")
            
            if business_info:
                footer_lines.append(" | ".join(business_info))
        
        # Multiline footer
        if self.footer_settings.get('footer_multiline', 'false').lower() == 'true':
            lines = [
                self.footer_settings.get('footer_line1', ''),
                self.footer_settings.get('footer_line2', ''),
                self.footer_settings.get('footer_line3', '')
            ]
            for line in lines:
                if line:
                    footer_lines.append(line)
        
        # Default terms
        footer_lines.extend([
            "This is a computer generated receipt.",
            "Goods once sold will not be taken back.",
            "All disputes are subject to local jurisdiction."
        ])
        
        return footer_lines
    
    def _generate_minimal_footer(self, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate minimal footer"""
        footer_lines = []
        
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you!')
        if custom_text:
            processed_text = self._process_placeholders(custom_text, order_data, user_data)
            footer_lines.append(processed_text)
        
        return footer_lines
    
    def _generate_detailed_footer(self, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate detailed footer"""
        footer_lines = []
        
        # Custom text with emphasis
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            processed_text = self._process_placeholders(custom_text, order_data, user_data)
            footer_lines.append(f"*** {processed_text} ***")
        
        # User info with timestamp
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true':
            username = user_data.get('username', user_data.get('name', 'Staff')) if user_data else 'Staff'
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            footer_lines.append(f"Processed by {username} at {timestamp}")
        
        # Receipt info
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            order_number = order_data.get('order_number', order_data.get('order_id', 'N/A'))
            created_at = order_data.get('created_at', '')
            if created_at:
                formatted_date = self._format_datetime(created_at)
                footer_lines.append(f"Receipt: {order_number}")
                footer_lines.append(f"Date: {formatted_date}")
        
        # Business info
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            # Use default values when no settings manager is provided
            restaurant_name = 'Restaurant POS'
            if restaurant_name:
                footer_lines.append(f"Business: {restaurant_name}")
            
            restaurant_address = '123 Main Street, City, State 123456'
            if restaurant_address:
                footer_lines.append(f"Address: {restaurant_address}")
            
            restaurant_phone = '+91-9876543210'
            if restaurant_phone:
                footer_lines.append(f"Phone: {restaurant_phone}")
            
            gst_number = 'GSTIN1234567890'
            if gst_number:
                footer_lines.append(f"GST: {gst_number}")
        
        # Additional terms
        footer_lines.extend([
            "This is a computer generated document.",
            "Goods once sold will not be taken back.",
            "All disputes are subject to local jurisdiction."
        ])
        
        return footer_lines
    
    def _process_placeholders(self, text: str, order_data: Dict = None, user_data: Dict = None) -> str:
        """Process placeholders in text"""
        placeholders = {
            '{{user_name}}': user_data.get('username', user_data.get('name', 'Staff')) if user_data else 'Staff',
            '{{date}}': datetime.now().strftime('%Y-%m-%d'),
            '{{time}}': datetime.now().strftime('%H:%M:%S'),
            '{{restaurant_name}}': 'Restaurant POS',
            '{{order_id}}': str(order_data.get('order_id', order_data.get('order_number', ''))) if order_data else '',
            '{{table_name}}': str(order_data.get('table_name', order_data.get('table_number', ''))) if order_data else ''
        }
        
        for placeholder, value in placeholders.items():
            text = text.replace(placeholder, value)
        
        return text
    
    def _format_datetime(self, date_str: str) -> str:
        """Format datetime string for display"""
        if not date_str:
            return ""
        
        try:
            # Try to parse datetime string
            if isinstance(date_str, str):
                # Handle different datetime formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime('%d-%m-%Y %H:%M:%S')
                    except ValueError:
                        continue
                return date_str  # Return original if parsing fails
            else:
                # Handle datetime objects
                return date_str.strftime('%d-%m-%Y %H:%M:%S')
        except Exception:
            return str(date_str)
    
    def get_footer_for_printing(self, document_type: str = 'receipt', 
                               order_data: Dict = None, 
                               user_data: Dict = None,
                               max_width: int = 40) -> List[str]:
        """
        Get footer formatted for printing with line wrapping
        
        Args:
            document_type: Type of document
            order_data: Order information
            user_data: User information
            max_width: Maximum line width for printing
            
        Returns:
            List of formatted footer lines
        """
        footer_lines = self.generate_footer(document_type, order_data, user_data)
        
        # Wrap lines to fit within max_width
        wrapped_lines = []
        for line in footer_lines:
            if len(line) <= max_width:
                wrapped_lines.append(line)
            else:
                # Wrap long lines
                words = line.split(' ')
                current_line = ""
                for word in words:
                    if len(current_line + word) <= max_width:
                        current_line += word + " "
                    else:
                        if current_line:
                            wrapped_lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    wrapped_lines.append(current_line.strip())
        
        return wrapped_lines
    
    def get_footer_css_styles(self) -> Dict:
        """
        Get CSS styles for footer (for web integration)
        
        Returns:
            Dictionary of CSS styles
        """
        font_size = self.footer_settings.get('footer_font_size', '10')
        alignment = self.footer_settings.get('footer_alignment', 'center')
        
        css_styles = {
            'font-size': f"{font_size}pt",
            'text-align': alignment,
            'margin-top': '20px',
            'padding-top': '10px',
            'border-top': '1px dashed #ccc',
            'color': '#666'
        }
        
        return css_styles
    
    def reload_settings(self):
        """Reload footer settings"""
        self.load_settings()
    
    def update_setting(self, key: str, value: str):
        """Update a specific footer setting"""
        if self.settings_manager:
            self.settings_manager.update_setting(key, value)
        else:
            Settings.set(key, value)
        
        # Reload settings
        self.load_settings()