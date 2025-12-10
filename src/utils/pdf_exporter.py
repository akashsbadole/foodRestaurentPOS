"""
PDF Exporter for POS Application
Handles exporting orders to PDF format with professional invoice layout
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
# ReportLab imports with error handling
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus.tableofcontents import TableOfContents
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ReportLab not available: {e}")
    REPORTLAB_AVAILABLE = False
    # Fallback imports for compatibility
    A4 = None
    colors = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    mm = None
    inch = None
    SimpleDocTemplate = None
    Table = None
    TableStyle = None
    Paragraph = None
    Spacer = None
    PageBreak = None
    TableOfContents = None
    TA_CENTER = None
    TA_LEFT = None
    TA_RIGHT = None
    canvas = None
    ImageReader = None


class PDFExporter:
    """
    PDF Exporter for generating professional order invoices
    
    This class handles the creation of PDF invoices for orders with proper formatting,
    including restaurant branding, order details, item tables, and payment information.
    """
    
    def __init__(self, restaurant_info: Dict = None, settings_manager=None):
        """
        Initialize PDF Exporter
        
        Args:
            restaurant_info: Dictionary containing restaurant details
            settings_manager: Settings manager for footer configuration
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
        
        # Settings manager for footer
        self.settings_manager = settings_manager
        
        # PDF settings
        self.page_size = A4
        self.margin = 20 * mm
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self._setup_custom_styles()
        
        # Export directory
        self.export_dir = os.path.join(os.getcwd(), 'exports', 'orders', 'pdf')
        self._ensure_export_directory()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles for the PDF"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Normal centered style
        self.centered_style = ParagraphStyle(
            'CenteredNormal',
            parent=self.styles['Normal'],
            alignment=TA_CENTER,
            fontSize=10
        )
        
        # Right aligned style
        self.right_style = ParagraphStyle(
            'RightNormal',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT,
            fontSize=10
        )
        
        # Bold style
        self.bold_style = ParagraphStyle(
            'BoldNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold'
        )
    
    def _ensure_export_directory(self):
        """Ensure the export directory exists"""
        try:
            os.makedirs(self.export_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Failed to create export directory: {e}")
            raise
    
    def export_order(self, order_data: Dict) -> Tuple[bool, str]:
        """
        Export a single order to PDF
        
        Args:
            order_data: Dictionary containing order information
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Generate filename
            order_number = order_data.get('order_number', 'UNKNOWN')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"Order_{order_number}_{timestamp}.pdf"
            filepath = os.path.join(self.export_dir, filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                filepath,
                pagesize=self.page_size,
                leftMargin=self.margin,
                rightMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Build PDF content
            story = []
            self._add_header(story)
            story.append(Spacer(1, 20))
            self._add_order_details(story, order_data)
            story.append(Spacer(1, 20))
            self._add_items_table(story, order_data.get('items', []))
            story.append(Spacer(1, 20))
            self._add_summary(story, order_data)
            story.append(Spacer(1, 20))
            self._add_payment_info(story, order_data.get('payments', []))
            story.append(Spacer(1, 30))
            self._add_footer(story, order_data)
            
            # Build PDF
            doc.build(story, onFirstPage=self._add_page_header_footer, onLaterPages=self._add_page_header_footer)
            
            self.logger.info(f"PDF exported successfully: {filepath}")
            return True, filepath
            
        except Exception as e:
            error_msg = f"Error exporting order to PDF: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _add_page_header_footer(self, canvas_obj, doc):
        """Add header and footer to each page"""
        canvas_obj.saveState()
        
        # Header
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(
            self.margin,
            doc.pagesize[1] - self.margin/2,
            f"{self.restaurant_info['name']} - Invoice"
        )
        
        # Footer
        canvas_obj.drawRightString(
            doc.pagesize[0] - self.margin,
            self.margin/2,
            f"Page {doc.page}"
        )
        
        canvas_obj.restoreState()
    
    def _add_header(self, story: List):
        """Add restaurant header to the PDF"""
        # Restaurant name
        story.append(Paragraph(self.restaurant_info['name'], self.title_style))
        
        # Restaurant address
        story.append(Paragraph(self.restaurant_info['address'], self.centered_style))
        
        # Contact information
        contact_info = f"Phone: {self.restaurant_info['phone']} | Email: {self.restaurant_info['email']}"
        if self.restaurant_info.get('gst_number'):
            contact_info += f" | GST: {self.restaurant_info['gst_number']}"
        story.append(Paragraph(contact_info, self.centered_style))
        
        # Invoice title
        story.append(Spacer(1, 10))
        story.append(Paragraph("TAX INVOICE", self.header_style))
    
    def _add_order_details(self, story: List, order_data: Dict):
        """Add order details section"""
        # Create order details table
        order_details = [
            ['Order Number:', order_data.get('order_number', ''), 'Date:', self._format_datetime(order_data.get('created_at'))],
            ['Order Type:', order_data.get('order_type', ''), 'Status:', order_data.get('status', '')]
        ]
        
        # Add table or customer information based on order type
        if order_data.get('order_type') == 'Dine-in':
            table_number = order_data.get('table_number', 'N/A')
            order_details.append(['Table Number:', table_number, '', ''])
        elif order_data.get('order_type') == 'Takeaway':
            customer_name = order_data.get('customer_name', 'N/A')
            customer_mobile = order_data.get('customer_mobile', 'N/A')
            order_details.append(['Customer Name:', customer_name, 'Mobile:', customer_mobile])
        
        # Create table
        table = Table(order_details, colWidths=[60*mm, 60*mm, 60*mm, 60*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
    
    def _add_items_table(self, story: List, items: List):
        """Add items table to the PDF"""
        if not items:
            return
        
        # Table headers
        headers = ['Item Name', 'Quantity', 'Price', 'Total']
        
        # Prepare table data
        table_data = [headers]
        
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
            
            table_data.append([
                name,
                str(quantity),
                f"₹{price:.2f}",
                f"₹{total:.2f}"
            ])
        
        # Create table
        table = Table(table_data, colWidths=[80*mm, 30*mm, 40*mm, 40*mm])
        table.setStyle(TableStyle([
            # Header styling
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        story.append(table)
    
    def _add_summary(self, story: List, order_data: Dict):
        """Add order summary section"""
        # Calculate values
        subtotal = float(order_data.get('subtotal', 0))
        tax = float(order_data.get('tax', 0))
        discount = float(order_data.get('discount', 0))
        total = float(order_data.get('total', 0))
        tax_rate = order_data.get('tax_rate', 5)
        
        # Create summary table
        summary_data = [
            ['Subtotal:', f"₹{subtotal:.2f}"],
            [f"Tax ({tax_rate}%):", f"₹{tax:.2f}"],
            ['Discount:', f"₹{discount:.2f}"],
            ['TOTAL:', f"₹{total:.2f}"]
        ]
        
        # Create table
        table = Table(summary_data, colWidths=[120*mm, 40*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-2, -1), 'Helvetica'),
            ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.darkblue),
            ('TEXTCOLOR', (-1, -1), (-1, -1), colors.darkblue),
            ('FONTSIZE', (-1, -1), (-1, -1), 14),
        ]))
        
        story.append(table)
    
    def _add_payment_info(self, story: List, payments: List):
        """Add payment information section"""
        if not payments:
            return
        
        story.append(Paragraph("Payment Information", self.bold_style))
        story.append(Spacer(1, 5))
        
        # Create payment table
        payment_data = [['Payment Mode', 'Amount', 'Date/Time']]
        
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
            
            payment_data.append([
                mode,
                f"₹{float(amount):.2f}",
                self._format_datetime(date)
            ])
        
        # Create table
        table = Table(payment_data, colWidths=[60*mm, 40*mm, 60*mm])
        table.setStyle(TableStyle([
            # Header styling
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            
            # Data styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(table)
    
    def _add_footer(self, story: List, order_data: Dict = None):
        """Add footer section"""
        if not self.settings_manager:
            # Use default footer if no settings manager
            self._add_default_footer(story)
            return
        
        # Get footer settings
        footer_settings = self.settings_manager.get_footer_settings()
        
        if not footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return
        
        # Generate footer based on template
        template = footer_settings.get('footer_template', 'default')
        
        story.append(Spacer(1, 20))
        
        if template == 'minimal':
            self._add_minimal_footer(story, footer_settings)
        elif template == 'detailed':
            self._add_detailed_footer(story, footer_settings, order_data)
        else:
            self._add_default_footer(story, footer_settings, order_data)
    
    def _add_default_footer(self, story: List, footer_settings: Dict = None, order_data: Dict = None):
        """Add default footer"""
        if not footer_settings:
            # Fallback to original default footer
            self._add_original_default_footer(story)
            return
        
        # Custom text
        custom_text = footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            story.append(Paragraph(custom_text, self.centered_style))
        
        # User info
        if footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and order_data:
            # For PDF, we'll use a generic user since we don't have user info in order_data
            story.append(Paragraph(f"Processed by POS System", self.centered_style))
        
        # Receipt info
        if footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            order_number = order_data.get('order_number', 'N/A')
            created_at = order_data.get('created_at', '')
            if created_at:
                formatted_date = self._format_datetime(created_at)
                story.append(Paragraph(f"Receipt #{order_number} - {formatted_date}", self.centered_style))
        
        # Business info
        if footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            business_info = []
            if self.restaurant_info.get('name'):
                business_info.append(self.restaurant_info['name'])
            if self.restaurant_info.get('phone'):
                business_info.append(self.restaurant_info['phone'])
            if self.restaurant_info.get('gst_number'):
                business_info.append(f"GST: {self.restaurant_info['gst_number']}")
            
            if business_info:
                story.append(Paragraph(" | ".join(business_info), self.centered_style))
        
        # Multiline footer
        if footer_settings.get('footer_multiline', 'false').lower() == 'true':
            lines = [
                footer_settings.get('footer_line1', ''),
                footer_settings.get('footer_line2', ''),
                footer_settings.get('footer_line3', '')
            ]
            for line in lines:
                if line:
                    story.append(Paragraph(line, self.centered_style))
        
        # Original default terms
        story.append(Spacer(1, 10))
        terms = [
            "This is a computer generated invoice.",
            "Goods once sold will not be taken back.",
            "All disputes are subject to local jurisdiction."
        ]
        
        for term in terms:
            story.append(Paragraph(term, self.centered_style))
    
    def _add_minimal_footer(self, story: List, footer_settings: Dict):
        """Add minimal footer"""
        custom_text = footer_settings.get('footer_custom_text', 'Thank you!')
        if custom_text:
            story.append(Paragraph(custom_text, self.centered_style))
    
    def _add_detailed_footer(self, story: List, footer_settings: Dict, order_data: Dict = None):
        """Add detailed footer"""
        # Custom text
        custom_text = footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            story.append(Paragraph(f"*** {custom_text} ***", self.centered_style))
        
        # User info
        if footer_settings.get('footer_show_user_name', 'true').lower() == 'true':
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            story.append(Paragraph(f"Processed by POS System at {timestamp}", self.centered_style))
        
        # Receipt info
        if footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and order_data:
            order_number = order_data.get('order_number', 'N/A')
            created_at = order_data.get('created_at', '')
            if created_at:
                formatted_date = self._format_datetime(created_at)
                story.append(Paragraph(f"Receipt: {order_number}", self.centered_style))
                story.append(Paragraph(f"Date: {formatted_date}", self.centered_style))
        
        # Business info
        if footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            if self.restaurant_info.get('name'):
                story.append(Paragraph(f"Business: {self.restaurant_info['name']}", self.centered_style))
            if self.restaurant_info.get('address'):
                story.append(Paragraph(f"Address: {self.restaurant_info['address']}", self.centered_style))
            if self.restaurant_info.get('phone'):
                story.append(Paragraph(f"Phone: {self.restaurant_info['phone']}", self.centered_style))
            if self.restaurant_info.get('gst_number'):
                story.append(Paragraph(f"GST: {self.restaurant_info['gst_number']}", self.centered_style))
        
        # Additional terms
        story.append(Spacer(1, 10))
        story.append(Paragraph("This is a computer generated document.", self.centered_style))
        story.append(Paragraph("Goods once sold will not be taken back.", self.centered_style))
        story.append(Paragraph("All disputes are subject to local jurisdiction.", self.centered_style))
    
    def _add_original_default_footer(self, story: List):
        """Add original default footer (fallback)"""
        story.append(Paragraph("Thank you for your business!", self.centered_style))
        story.append(Paragraph("Please visit again!", self.centered_style))
        
        # Terms and conditions
        story.append(Spacer(1, 10))
        terms = [
            "This is a computer generated invoice.",
            "Goods once sold will not be taken back.",
            "All disputes are subject to [City] jurisdiction."
        ]
        
        for term in terms:
            story.append(Paragraph(term, self.centered_style))
    
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
        Export multiple orders to PDF (batch export)
        
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
            
            success_msg = f"Successfully exported {len(exported_files)} orders to PDF."
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