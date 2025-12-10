"""
Footer Generator for Flask Web Version
Handles dynamic footer generation for receipts, invoices, and documents
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from models.settings import Settings


class FooterGenerator:
    """Footer generator for POS documents"""
    
    def __init__(self):
        self.footer_settings = Settings.get_footer_settings()
        self.restaurant_info = Settings.get_restaurant_info()
    
    def generate_footer(self, document_type: str = 'receipt', order_data: Dict = None, user_data: Dict = None) -> str:
        """
        Generate footer content based on settings and context
        
        Args:
            document_type: Type of document (receipt, invoice, report, etc.)
            order_data: Order information for dynamic content
            user_data: User information for dynamic content
            
        Returns:
            Formatted footer HTML
        """
        if not self.footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return ""
        
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
        """Get the appropriate template for the document type"""
        if self.footer_settings.get('footer_different_receipts', 'false').lower() == 'true':
            if document_type in ['receipt', 'bill']:
                return self.footer_settings.get('footer_receipt_template', 'default')
            elif document_type == 'invoice':
                return self.footer_settings.get('footer_invoice_template', 'default')
        
        return self.footer_settings.get('footer_template', 'default')
    
    def _generate_default_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> str:
        """Generate default footer"""
        lines = []
        
        # Add custom text or default
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            lines.append(f"<p class='footer-custom'>{custom_text}</p>")
        
        # Add user name if enabled
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and user_data:
            user_name = user_data.get('username', 'Staff')
            lines.append(f"<p class='footer-user'>Served by: {user_name}</p>")
        
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
        
        return self._wrap_footer_html(lines, document_type)
    
    def _generate_minimal_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> str:
        """Generate minimal footer"""
        lines = []
        
        # Just custom text for minimal
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you!')
        if custom_text:
            lines.append(f"<p class='footer-custom'>{custom_text}</p>")
        
        return self._wrap_footer_html(lines, document_type, 'minimal')
    
    def _generate_detailed_footer(self, document_type: str, order_data: Dict = None, user_data: Dict = None) -> str:
        """Generate detailed footer"""
        lines = []
        
        # Custom text
        custom_text = self.footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            lines.append(f"<p class='footer-custom'><strong>{custom_text}</strong></p>")
        
        # User info
        if self.footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and user_data:
            user_name = user_data.get('username', 'Staff')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"<p class='footer-user'>Processed by: {user_name} at {timestamp}</p>")
        
        # Receipt info
        if self.footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            receipt_lines = self._generate_receipt_info(order_data, detailed=True)
            lines.extend(receipt_lines)
        
        # Business info
        if self.footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            business_lines = self._generate_business_info(detailed=True)
            lines.extend(business_lines)
        
        # Additional terms
        lines.append("<hr class='footer-divider'>")
        lines.append("<p class='footer-terms'>This is a computer generated document. Goods once sold will not be taken back.</p>")
        lines.append("<p class='footer-jurisdiction'>All disputes are subject to local jurisdiction.</p>")
        
        return self._wrap_footer_html(lines, document_type, 'detailed')
    
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
            lines.append(f"<p class='footer-receipt'><strong>Receipt:</strong> {order_number}</p>")
            lines.append(f"<p class='footer-date'><strong>Date:</strong> {formatted_date}</p>")
        else:
            lines.append(f"<p class='footer-receipt'>Receipt #{order_number} - {formatted_date}</p>")
        
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
                lines.append(f"<p class='footer-business-name'><strong>{name}</strong></p>")
            if address:
                lines.append(f"<p class='footer-address'>{address}</p>")
            contact_info = []
            if phone:
                contact_info.append(f"Phone: {phone}")
            if email:
                contact_info.append(f"Email: {email}")
            if contact_info:
                lines.append(f"<p class='footer-contact'>{' | '.join(contact_info)}</p>")
            if gst:
                lines.append(f"<p class='footer-gst'>GST: {gst}</p>")
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
                lines.append(f"<p class='footer-business-compact'>{' | '.join(info_parts)}</p>")
        
        return lines
    
    def _generate_multiline_footer(self) -> List[str]:
        """Generate multiline footer text"""
        lines = []
        
        line1 = self.footer_settings.get('footer_line1', '')
        line2 = self.footer_settings.get('footer_line2', '')
        line3 = self.footer_settings.get('footer_line3', '')
        
        if line1:
            lines.append(f"<p class='footer-line1'>{line1}</p>")
        if line2:
            lines.append(f"<p class='footer-line2'>{line2}</p>")
        if line3:
            lines.append(f"<p class='footer-line3'>{line3}</p>")
        
        return lines
    
    def _wrap_footer_html(self, lines: List[str], document_type: str, style: str = 'default') -> str:
        """Wrap footer lines in HTML with appropriate styling"""
        if not lines:
            return ""
        
        alignment = self.footer_settings.get('footer_alignment', 'center')
        font_size = self.footer_settings.get('footer_font_size', '10')
        
        # Determine CSS classes
        css_classes = [f'footer-{document_type}', f'footer-{style}']
        css_classes.append(f'text-{alignment}')
        css_classes.append(f'font-size-{font_size}')
        
        # Add logo if enabled
        logo_html = ""
        if self.footer_settings.get('footer_show_logo', 'false').lower() == 'true':
            logo_path = self.footer_settings.get('footer_logo_path', '')
            if logo_path:
                logo_html = f'<div class="footer-logo"><img src="{logo_path}" alt="Company Logo" style="max-height: 50px;"></div>'
        
        # Build footer HTML
        footer_html = f"""
        <div class="footer {' '.join(css_classes)}">
            {logo_html}
            <div class="footer-content">
                {''.join(lines)}
            </div>
            <div class="footer-timestamp">
                <small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
        </div>
        """
        
        return footer_html
    
    def get_footer_css(self) -> str:
        """Get CSS styles for footer"""
        return """
        <style>
        .footer {
            border-top: 1px solid #ddd;
            padding: 20px 0;
            margin-top: 30px;
            text-align: center;
            font-size: 10px;
            color: #666;
        }
        .footer-logo {
            text-align: center;
            margin-bottom: 10px;
        }
        .footer-content p {
            margin: 5px 0;
        }
        .footer-custom {
            font-weight: bold;
            font-size: 12px;
            margin-bottom: 10px;
        }
        .footer-user {
            font-style: italic;
        }
        .footer-receipt {
            font-family: monospace;
        }
        .footer-business-name {
            font-weight: bold;
            font-size: 11px;
        }
        .footer-divider {
            border: none;
            border-top: 1px solid #eee;
            margin: 10px 0;
        }
        .footer-timestamp {
            margin-top: 15px;
            font-size: 9px;
            color: #999;
        }
        .footer-minimal {
            padding: 10px 0;
        }
        .footer-detailed {
            padding: 30px 0;
            border-top: 2px solid #ddd;
        }
        .text-left { text-align: left; }
        .text-center { text-align: center; }
        .text-right { text-align: right; }
        .font-size-8 { font-size: 8px; }
        .font-size-10 { font-size: 10px; }
        .font-size-12 { font-size: 12px; }
        .font-size-14 { font-size: 14px; }
        </style>
        """