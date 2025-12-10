"""
Text Exporter for POS Application
Handles exporting orders to text format with fixed-width layout
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple


class TextExporter:
    """
    Text Exporter for generating ASCII-compatible order invoices
    
    This class handles the creation of text invoices for orders with proper formatting,
    including restaurant branding, order details, item tables, and payment information.
    The output is optimized for thermal printer compatibility and readability in any text editor.
    """
    
    def __init__(self, restaurant_info: Dict = None):
        """
        Initialize Text Exporter
        
        Args:
            restaurant_info: Dictionary containing restaurant details
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Default restaurant information
        self.restaurant_info = restaurant_info or {
            'name': 'Restaurant POS',
            'address': '123 Main Street, City, State 12345',
            'phone': '+1 234 567 8900',
            'email': 'info@restaurant.com',
            'gst_number': 'GSTIN1234567890'
        }
        
        # Text formatting settings
        self.line_width = 80  # Standard terminal width
        self.max_item_name_length = 40  # Max length for item names
        
        # Export directory
        self.export_dir = os.path.join(os.getcwd(), 'exports', 'orders', 'text')
        self._ensure_export_directory()
    
    def _ensure_export_directory(self):
        """Ensure the export directory exists"""
        try:
            os.makedirs(self.export_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create export directory: {e}")
            raise
    
    def export_order(self, order_data: Dict) -> Tuple[bool, str]:
        """
        Export a single order to text
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate filename
            order_number = order_data.get('order_number', 'UNKNOWN')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Order_{order_number}_{timestamp}.txt"
            filepath = os.path.join(self.export_dir, filename)
            
            # Generate text content
            content = self._generate_invoice_content(order_data)
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Text exported successfully: {filepath}")
            return True, filepath
            
        except Exception as e:
            error_msg = f"Error exporting order to text: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _generate_invoice_content(self, order_data: Dict) -> str:
        """Generate the complete invoice content"""
        lines = []
        
        # Header section
        lines.extend(self._add_header())
        
        # Order details section
        lines.extend(self._add_order_details(order_data))
        
        # Items table section
        lines.extend(self._add_items_table(order_data.get('items', [])))
        
        # Summary section
        lines.extend(self._add_summary(order_data))
        
        # Payment information section
        lines.extend(self._add_payment_info(order_data.get('payments', [])))
        
        # Footer section
        lines.extend(self._add_footer())
        
        return '\n'.join(lines)
    
    def _add_header(self) -> List[str]:
        """Add restaurant header to the invoice"""
        lines = []
        
        # Top border
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        
        # Restaurant name (centered)
        name_line = self._center_text(self.restaurant_info['name'])
        lines.append('│' + name_line + '│')
        
        # Restaurant address (centered)
        address_lines = self._wrap_text(self.restaurant_info['address'], self.line_width - 4)
        for address_line in address_lines:
            address_line = self._center_text(address_line)
            lines.append('│' + address_line + '│')
        
        # Contact information (centered)
        contact_info = f"Phone: {self.restaurant_info['phone']} | Email: {self.restaurant_info['email']}"
        if self.restaurant_info.get('gst_number'):
            contact_info += f" | GST: {self.restaurant_info['gst_number']}"
        
        contact_lines = self._wrap_text(contact_info, self.line_width - 4)
        for contact_line in contact_lines:
            contact_line = self._center_text(contact_line)
            lines.append('│' + contact_line + '│')
        
        # Separator
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        
        # Invoice title (centered, bold)
        title_line = self._center_text("*** TAX INVOICE ***")
        lines.append('│' + title_line + '│')
        
        # Bottom border
        lines.append('└' + '─' * (self.line_width - 2) + '┘')
        
        return lines
    
    def _add_order_details(self, order_data: Dict) -> List[str]:
        """Add order details section"""
        lines = []
        
        # Add some spacing
        lines.append('')
        
        # Order details header
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        lines.append('│' + self._pad_text('ORDER DETAILS', self.line_width - 2) + '│')
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        
        # Order information
        order_number = order_data.get('order_number', 'N/A')
        created_at = self._format_datetime(order_data.get('created_at'))
        order_type = order_data.get('order_type', 'N/A')
        status = order_data.get('status', 'N/A')
        
        lines.append('│' + self._pad_text(f"Order Number: {order_number}", self.line_width - 2) + '│')
        lines.append('│' + self._pad_text(f"Date/Time: {created_at}", self.line_width - 2) + '│')
        lines.append('│' + self._pad_text(f"Order Type: {order_type}", self.line_width - 2) + '│')
        lines.append('│' + self._pad_text(f"Status: {status}", self.line_width - 2) + '│')
        
        # Add table or customer information based on order type
        if order_type == 'Dine-in':
            table_number = order_data.get('table_number', 'N/A')
            lines.append('│' + self._pad_text(f"Table Number: {table_number}", self.line_width - 2) + '│')
        elif order_type == 'Takeaway':
            customer_name = order_data.get('customer_name', 'N/A')
            customer_mobile = order_data.get('customer_mobile', 'N/A')
            lines.append('│' + self._pad_text(f"Customer Name: {customer_name}", self.line_width - 2) + '│')
            lines.append('│' + self._pad_text(f"Mobile: {customer_mobile}", self.line_width - 2) + '│')
        
        lines.append('└' + '─' * (self.line_width - 2) + '┘')
        
        return lines
    
    def _add_items_table(self, items: List) -> List[str]:
        """Add items table to the invoice"""
        lines = []
        
        if not items:
            return lines
        
        # Add some spacing
        lines.append('')
        
        # Table header
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        
        # Column headers
        header_line = '│' + self._pad_text('Item Name', 40) + '│' + \
                     self._pad_text('Qty', 8) + '│' + \
                     self._pad_text('Price', 12) + '│' + \
                     self._pad_text('Total', 14) + '│'
        lines.append(header_line)
        lines.append('├' + '─' * 40 + '┼' + '─' * 8 + '┼' + '─' * 12 + '┼' + '─' * 14 + '┤')
        
        # Table data
        for item in items:
            # Handle both tuple and dict formats
            if isinstance(item, (list, tuple)):
                name, quantity, price, total = item
            elif isinstance(item, dict):
                name = item.get('name', 'Unknown Item')
                quantity = item.get('quantity', 0)
                price = item.get('price', 0)
                total = item.get('total', 0)
            else:
                continue
            
            # Handle long item names
            name_lines = self._wrap_text(name, 40)
            
            # First line with item details
            first_name_line = name_lines[0]
            item_line = '│' + self._pad_text(first_name_line, 40) + '│' + \
                        self._pad_text(str(quantity), 8) + '│' + \
                        self._pad_text(f"Rs.{price:.2f}", 12) + '│' + \
                        self._pad_text(f"Rs.{total:.2f}", 14) + '│'
            lines.append(item_line)
            
            # Additional lines for long item names
            for name_line in name_lines[1:]:
                continuation_line = '│' + self._pad_text(name_line, 40) + '│' + \
                                  self._pad_text('', 8) + '│' + \
                                  self._pad_text('', 12) + '│' + \
                                  self._pad_text('', 14) + '│'
                lines.append(continuation_line)
        
        lines.append('└' + '─' * 40 + '┴' + '─' * 8 + '┴' + '─' * 12 + '┴' + '─' * 14 + '┘')
        
        return lines
    
    def _add_summary(self, order_data: Dict) -> List[str]:
        """Add order summary section"""
        lines = []
        
        # Add some spacing
        lines.append('')
        
        # Calculate values
        subtotal = float(order_data.get('subtotal', 0))
        tax = float(order_data.get('tax', 0))
        discount = float(order_data.get('discount', 0))
        total = float(order_data.get('total', 0))
        tax_rate = order_data.get('tax_rate', 5)
        
        # Summary box
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        lines.append('│' + self._pad_text('ORDER SUMMARY', self.line_width - 2) + '│')
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        
        # Summary items (right-aligned)
        lines.append('│' + self._pad_text('', 50) + self._pad_text('Subtotal:', 15) + 
                    self._pad_text(f"Rs.{subtotal:.2f}", 13) + '│')
        lines.append('│' + self._pad_text('', 50) + self._pad_text(f'Tax ({tax_rate}%):', 15) + 
                    self._pad_text(f"Rs.{tax:.2f}", 13) + '│')
        lines.append('│' + self._pad_text('', 50) + self._pad_text('Discount:', 15) + 
                    self._pad_text(f"Rs.{discount:.2f}", 13) + '│')
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        lines.append('│' + self._pad_text('', 50) + self._pad_text('TOTAL:', 15, bold=True) + 
                    self._pad_text(f"Rs.{total:.2f}", 13, bold=True) + '│')
        lines.append('└' + '─' * (self.line_width - 2) + '┘')
        
        return lines
    
    def _add_payment_info(self, payments: List) -> List[str]:
        """Add payment information section"""
        lines = []
        
        if not payments:
            return lines
        
        # Add some spacing
        lines.append('')
        
        # Payment header
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        lines.append('│' + self._pad_text('PAYMENT INFORMATION', self.line_width - 2) + '│')
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        
        # Column headers
        header_line = '│' + self._pad_text('Payment Mode', 25) + '│' + \
                     self._pad_text('Amount', 20) + '│' + \
                     self._pad_text('Date/Time', 29) + '│'
        lines.append(header_line)
        lines.append('├' + '─' * 25 + '┼' + '─' * 20 + '┼' + '─' * 29 + '┤')
        
        # Payment data
        for payment in payments:
            # Handle both tuple and dict formats
            if isinstance(payment, (list, tuple)):
                mode, amount, date = payment
            elif isinstance(payment, dict):
                mode = payment.get('payment_mode', 'Unknown')
                amount = payment.get('amount', 0)
                date = payment.get('created_at', '')
            else:
                continue
            
            payment_line = '│' + self._pad_text(mode, 25) + '│' + \
                          self._pad_text(f"Rs.{float(amount):.2f}", 20) + '│' + \
                          self._pad_text(self._format_datetime(date), 29) + '│'
            lines.append(payment_line)
        
        lines.append('└' + '─' * 25 + '┴' + '─' * 20 + '┴' + '─' * 29 + '┘')
        
        return lines
    
    def _add_footer(self) -> List[str]:
        """Add footer section"""
        lines = []
        
        # Add some spacing
        lines.append('')
        
        # Thank you message
        lines.append('┌' + '─' * (self.line_width - 2) + '┐')
        thank_you_line = self._center_text('Thank you for your business!')
        lines.append('│' + thank_you_line + '│')
        visit_again_line = self._center_text('Please visit again!')
        lines.append('│' + visit_again_line + '│')
        lines.append('├' + '─' * (self.line_width - 2) + '┤')
        
        # Terms and conditions
        terms = [
            "This is a computer generated invoice.",
            "Goods once sold will not be taken back.",
            "All disputes are subject to local jurisdiction."
        ]
        
        for term in terms:
            term_lines = self._wrap_text(term, self.line_width - 4)
            for term_line in term_lines:
                term_line = self._center_text(term_line)
                lines.append('│' + term_line + '│')
        
        lines.append('└' + '─' * (self.line_width - 2) + '┘')
        
        return lines
    
    def _center_text(self, text: str) -> str:
        """Center text within the line width"""
        return text.center(self.line_width - 2)
    
    def _pad_text(self, text: str, width: int, bold: bool = False) -> str:
        """Pad text to specified width with optional bold formatting"""
        if bold:
            text = f"***{text}***"
        return text.ljust(width)[:width]
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within specified width"""
        if not text:
            return [""]
        
        words = text.split(' ')
        lines = []
        current_line = ''
        
        for word in words:
            if len(current_line + word) <= max_width:
                current_line += word + ' '
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + ' '
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines if lines else [""]
    
    def _format_datetime(self, date_str: str) -> str:
        """Format datetime string for display"""
        if not date_str:
            return ""
        
        try:
            # Try to parse the datetime string
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
    
    def export_orders_batch(self, orders_data: List[Dict]) -> Tuple[bool, str]:
        """
        Export multiple orders to text (batch export)
        
        Args:
            orders_data: List of order dictionaries
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            exported_files = []
            failed_orders = []
            
            for order_data in orders_data:
                success, result = self.export_order(order_data)
                if success:
                    exported_files.append(result)
                else:
                    failed_orders.append({
                        'order_number': order_data.get('order_number', 'Unknown'),
                        'error': result
                    })
            
            if failed_orders:
                error_msg = f"Failed to export {len(failed_orders)} orders. Successfully exported {len(exported_files)} orders."
                self.logger.error(error_msg)
                return False, error_msg
            
            success_msg = f"Successfully exported {len(exported_files)} orders to text."
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error in batch export: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_export_directory(self) -> str:
        """Get the export directory path"""
        return self.export_dir
    
    def set_restaurant_info(self, restaurant_info: Dict):
        """Update restaurant information"""
        self.restaurant_info.update(restaurant_info)
