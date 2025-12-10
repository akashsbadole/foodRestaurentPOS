"""
Footer Generator for Desktop POS Version
Handles dynamic footer generation for receipts, invoices, and documents
"""

from datetime import datetime
from typing import Dict, List, Optional, Any


class FooterGenerator:
    """Footer generator for POS documents"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.footer_settings = self.settings.get_footer_settings()
        self.restaurant_info = self.settings.get_all()
    
    def generate_footer(self, document_type: str = 'receipt', order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """
        Generate footer content based on settings and context
        
        Args:
            document_type: Type of document (receipt, invoice, report, etc.)
            order_data: Order information for dynamic content
            user_data: User information for dynamic content
            
        Returns:
            List of formatted footer lines
        """
        if not self.footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return []
        
        # Determine which template to use
        template = self._get_template(document_type)
        
        # Generate footer content based on template
        if template == 'minimal':
            return self._generate_minimal_footer(document_type, order_data, user_data)
        elif template == 'detailed':
            return self._generate_detailed_footer(document_type, order_data, user_data)
        else:
            return self._generate_default_footer(document_type, order_data, user_data)
    
    def _get_template(self, document_type: str) -> str:
        """Get appropriate template for document type"""
        if self.footer_settings.get('footer_different_receipts', 'false').lower() == 'true':
            if document_type in ['receipt', 'bill']:
                return self.footer_settings.get('footer_receipt_template', 'default')
            elif document_type == 'invoice':
                return self.footer_settings.get('footer_invoice_template', 'default')
        
        return self.footer_settings.get('footer_template', 'default')
    
    def _generate_default_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate default footer"""
        lines = []
        
        # Add separator
        lines.append("-" * 40)
        
        # Add custom text or default
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            lines.append(custom_text)
        
        # Add user name if enabled
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and user_data:
            user_name = user_data.get('username', 'Staff')
            lines.append(f"Served by: {user_name}")
        
        # Add receipt info if enabled
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            receipt_lines = self._generate_receipt_info(order_data)
            lines.extend(receipt_lines)
        
        # Add business info if enabled
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            business_lines = self._generate_business_info()
            lines.extend(business_lines)
        
        # Add multiline footer if enabled
        if self.footer_settings.get('footer_multiline', 'false').lower() == 'true':
            multiline_lines = self._generate_multiline_footer()
            lines.extend(multiline_lines)
        
        # Add final separator
        lines.append("-" * 40)
        
        return lines
    
    def _generate_minimal_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate minimal footer"""
        lines = []
        
        # Add separator
        lines.append("-" * 30)
        
        # Just custom text for minimal
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you!')
        if custom_text:
            lines.append(custom_text)
        
        # Add separator
        lines.append("-" * 30)
        
        return lines
    
    def _generate_detailed_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> List[str]:
        """Generate detailed footer"""
        lines = []
        
        # Add separator
        lines.append("=" * 50)
        
        # Custom text
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            lines.append(f"*** {custom_text} ***")
        
        # User info
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and user_data:
            user_name = user_data.get('username', 'Staff')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"Processed by: {user_name} at {timestamp}")
        
        # Receipt info
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            receipt_lines = self._generate_receipt_info(order_data, detailed=True)
            lines.extend(receipt_lines)
        
        # Business info
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            business_lines = self._generate_business_info(detailed=True)
            lines.extend(business_lines)
        
        # Additional terms
        lines.append("-" * 50)
        lines.append("This is a computer generated document.")
        lines.append("Goods once sold will not be taken back.")
        lines.append("All disputes are subject to local jurisdiction.")
        
        # Add final separator
        lines.append("=" * 50)
        
        return lines
    
    def _generate_receipt_info(self, order_data: Dict, detailed: bool = False) -> List[str]:
        """Generate receipt information lines"""
        lines = []
        
        if not order_data:
            return lines
        
        order_number = order_data.get('order_number', 'N/A')
        created_at = order_data.get('created_at', '')
        
        if created_at:
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    dt = created_at
                formatted_date = dt.strftime('%d-%m-%Y %H:%M:%S')
            except:
                formatted_date = str(created_at)
        else:
            formatted_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        
        if detailed:
            lines.append(f"Receipt: {order_number}")
            lines.append(f"Date: {formatted_date}")
        else:
            lines.append(f"Receipt #{order_number} - {formatted_date}")
        
        return lines
    
    def _generate_business_info(self, detailed: bool = False) -> List[str]:
        """Generate business information lines"""
        lines = []
        
        name = self.restaurant_info.get('restaurant_name', '')
        address = self.restaurant_info.get('restaurant_address', '')
        phone = self.restaurant_info.get('restaurant_phone', '')
        email = self.restaurant_info.get('restaurant_email', '')
        gst = self.restaurant_info.get('gst_number', '')
        
        if detailed:
            if name:
                lines.append(f"Business: {name}")
            if address:
                lines.append(f"Address: {address}")
            if phone:
                lines.append(f"Phone: {phone}")
            if email:
                lines.append(f"Email: {email}")
            if gst:
                lines.append(f"GST: {gst}")
        else:
            # Compact format
            info_parts = []
            if name:
                info_parts.append(name)
            if phone:
                info_parts.append(phone)
            if gst:
                info_parts.append(f"GST: {gst}")
            
            if info_parts:
                lines.append(" | ".join(info_parts))
        
        return lines
    
    def _generate_multiline_footer(self) -> List[str]:
        """Generate multiline footer text"""
        lines = []
        
        line1 = self.footer_settings.get('footer_line1', '')
        line2 = self.footer_settings.get('footer_line2', '')
        line3 = self.footer_settings.get('footer_line3', '')
        
        if line1:
            lines.append(line1)
        if line2:
            lines.append(line2)
        if line3:
            lines.append(line3)
        
        return lines
    
    def format_for_thermal_printer(self, lines: List[str], paper_width: int = 58) -> List[str]:
        """
        Format footer lines for thermal printer
        
        Args:
            lines: Footer lines to format
            paper_width: Paper width in mm (58 or 80)
            
        Returns:
            Formatted lines for thermal printer
        """
        max_chars = 32 if paper_width == 58 else 48
        formatted_lines = []
        
        alignment = self.footer_settings.get('footer_alignment', 'center')
        
        for line in lines:
            if len(line) <= max_chars:
                # Apply alignment
                if alignment == 'center':
                    spaces = (max_chars - len(line)) // 2
                    formatted_line = ' ' * spaces + line
                elif alignment == 'right':
                    spaces = max_chars - len(line)
                    formatted_line = ' ' * spaces + line
                else:  # left
                    formatted_line = line
                
                formatted_lines.append(formatted_line)
            else:
                # Wrap long lines
                words = line.split(' ')
                current_line = ''
                for word in words:
                    if len(current_line + word) <= max_chars:
                        current_line += word + ' '
                    else:
                        if current_line:
                            formatted_lines.append(current_line.rstrip())
                        current_line = word + ' '
                if current_line:
                    formatted_lines.append(current_line.rstrip())
        
        return formatted_lines
    
    def update_settings(self):
        """Update footer settings from settings manager"""
        self.footer_settings = self.settings.get_footer_settings()
        self.restaurant_info = self.settings.get_all()