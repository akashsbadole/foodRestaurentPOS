"""
Printer utility module for Restaurant POS System
Handles both thermal printer and standard printer functionality
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import tkinter as tk
from tkinter import messagebox

# Try to import printer libraries
try:
    import win32print
    import win32ui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("Warning: win32print not available. Standard printer support will be limited.")

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False
    print("Warning: pyusb not available. USB thermal printer detection will be limited.")

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not available. Serial thermal printer support will be limited.")


class PrinterType:
    """Printer type constants"""
    THERMAL = "thermal"
    STANDARD = "standard"


class PaperSize:
    """Paper size constants for thermal printers"""
    MM58 = 58  # 58mm paper width
    MM80 = 80  # 80mm paper width


class ESCPOS:
    """ESC/POS command constants for thermal printers"""
    # Initialize
    INIT = b'\x1B\x40'
    
    # Text formatting
    ALIGN_LEFT = b'\x1B\x61\x00'
    ALIGN_CENTER = b'\x1B\x61\x01'
    ALIGN_RIGHT = b'\x1B\x61\x02'
    
    # Font styles
    FONT_NORMAL = b'\x1B\x21\x00'
    FONT_BOLD = b'\x1B\x21\x08'
    FONT_DOUBLE_HEIGHT = b'\x1B\x21\x10'
    FONT_DOUBLE_WIDTH = b'\x1B\x21\x20'
    FONT_DOUBLE_BOTH = b'\x1B\x21\x30'
    
    # Line spacing
    LINE_SPACING_DEFAULT = b'\x1B\x32'
    LINE_SPACING_24 = b'\x1B\x33\x18'
    
    # Paper cut
    PAPER_CUT = b'\x1D\x56\x00'
    PARTIAL_CUT = b'\x1D\x56\x01'
    
    # Feed commands
    FEED_LINE = b'\x0A'
    FEED_3_LINES = b'\x0A\x0A\x0A'
    FEED_5_LINES = b'\x0A\x0A\x0A\x0A\x0A'


class ThermalPrinter:
    """Thermal printer implementation using ESC/POS commands"""
    
    def __init__(self, printer_name: str = None, paper_width: int = PaperSize.MM58, settings_manager=None):
        self.printer_name = printer_name
        self.paper_width = paper_width
        self.max_chars_per_line = 32 if paper_width == PaperSize.MM58 else 48
        self.settings_manager = settings_manager
        
    def _format_text(self, text: str, align: str = 'left', style: str = 'normal') -> bytes:
        """Format text with alignment and style"""
        result = b''
        
        # Set alignment
        if align == 'center':
            result += ESCPOS.ALIGN_CENTER
        elif align == 'right':
            result += ESCPOS.ALIGN_RIGHT
        else:
            result += ESCPOS.ALIGN_LEFT
            
        # Set style
        if style == 'bold':
            result += ESCPOS.FONT_BOLD
        elif style == 'double_height':
            result += ESCPOS.FONT_DOUBLE_HEIGHT
        elif style == 'double_width':
            result += ESCPOS.FONT_DOUBLE_WIDTH
        elif style == 'double_both':
            result += ESCPOS.FONT_DOUBLE_BOTH
        else:
            result += ESCPOS.FONT_NORMAL
            
        # Add text
        result += text.encode('utf-8')
        
        # Reset style
        result += ESCPOS.FONT_NORMAL
        result += ESCPOS.ALIGN_LEFT
        
        return result
    
    def _wrap_text(self, text: str, max_chars: int = None) -> List[str]:
        """Wrap text to fit within max characters per line"""
        if max_chars is None:
            max_chars = self.max_chars_per_line
            
        words = text.split(' ')
        lines = []
        current_line = ''
        
        for word in words:
            if len(current_line + word) <= max_chars:
                current_line += word + ' '
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + ' '
                
        if current_line:
            lines.append(current_line.strip())
            
        return lines
    
    def _create_separator(self, char: str = '-') -> bytes:
        """Create a separator line"""
        return (char * self.max_chars_per_line + '\n').encode('utf-8')
    
    def print_bill(self, bill_data: Dict) -> bool:
        """Print a bill using ESC/POS commands"""
        try:
            # Start print job
            buffer = ESCPOS.INIT
            
            # Restaurant header (centered, bold)
            buffer += self._format_text(bill_data.get('restaurant_name', ''), 'center', 'bold')
            buffer += ESCPOS.FEED_LINE
            buffer += self._format_text(bill_data.get('restaurant_address', ''), 'center')
            buffer += ESCPOS.FEED_LINE
            
            # Bill title
            buffer += self._create_separator('=')
            buffer += self._format_text('BILL', 'center', 'bold')
            buffer += self._create_separator('=')
            buffer += ESCPOS.FEED_LINE
            
            # Order details
            buffer += self._format_text(f"Order No: {bill_data.get('order_number', '')}")
            buffer += self._format_text(f"Date: {bill_data.get('date', '')}")
            buffer += self._format_text(f"Type: {bill_data.get('order_type', '')}")
            
            if bill_data.get('order_type') == 'Dine-in' and bill_data.get('table_number'):
                buffer += self._format_text(f"Table: {bill_data.get('table_number', '')}")
            elif bill_data.get('order_type') == 'Takeaway' and bill_data.get('customer_name'):
                buffer += self._format_text(f"Customer: {bill_data.get('customer_name', '')}")
                if bill_data.get('customer_mobile'):
                    buffer += self._format_text(f"Mobile: {bill_data.get('customer_mobile', '')}")
            
            buffer += ESCPOS.FEED_LINE
            buffer += self._create_separator('-')
            
            # Items header
            items_header = f"{'Item':<{self.max_chars_per_line-20}} {'Qty':<5} {'Price':<10} {'Total':<10}"
            buffer += self._format_text(items_header, 'left', 'bold')
            buffer += self._create_separator('-')
            
            # Items
            for item in bill_data.get('items', []):
                name, quantity, price, total = item
                # Wrap item name if too long
                name_lines = self._wrap_text(name, self.max_chars_per_line - 20)
                buffer += self._format_text(name_lines[0])
                
                if len(name_lines) > 1:
                    for line in name_lines[1:]:
                        buffer += self._format_text(line)
                
                item_line = f"{'':{self.max_chars_per_line-20}} {quantity:<5} {price:<9.2f} {total:<9.2f}"
                buffer += self._format_text(item_line)
            
            buffer += self._create_separator('-')
            
            # Totals
            buffer += self._format_text(f"Subtotal: {bill_data.get('subtotal', 0):.2f}")
            buffer += self._format_text(f"Tax ({bill_data.get('tax_rate', 5)}%): {bill_data.get('tax', 0):.2f}")
            buffer += self._format_text(f"Discount: {bill_data.get('discount', 0):.2f}")
            buffer += self._create_separator('=')
            buffer += self._format_text(f"Total: {bill_data.get('total', 0):.2f}", 'left', 'bold')
            buffer += self._create_separator('=')
            
            # Footer
            buffer += self._add_footer_to_print(bill_data)
            
            # Cut paper
            buffer += ESCPOS.PAPER_CUT
            
            # Send to printer
            return self._send_to_printer(buffer)
            
        except Exception as e:
            print(f"Error printing bill: {e}")
            return False
    
    def print_kot(self, kot_data: Dict) -> bool:
        """Print a KOT using ESC/POS commands"""
        try:
            # Start print job
            buffer = ESCPOS.INIT
            
            # KOT header (centered, bold)
            buffer += self._format_text('KITCHEN ORDER TICKET', 'center', 'bold')
            buffer += self._create_separator('=')
            buffer += ESCPOS.FEED_LINE
            
            # Order details
            buffer += self._format_text(f"Order No: {kot_data.get('order_number', '')}")
            buffer += self._format_text(f"Time: {kot_data.get('time', '')}")
            buffer += ESCPOS.FEED_LINE
            buffer += self._create_separator('-')
            
            # Item details
            buffer += self._format_text(f"Item: {kot_data.get('item_name', '')}", 'left', 'bold')
            buffer += self._format_text(f"Quantity: {kot_data.get('quantity', '')}")
            buffer += ESCPOS.FEED_LINE
            
            # Additional notes if any
            if kot_data.get('notes'):
                buffer += self._create_separator('-')
                buffer += self._format_text("Notes:", 'left', 'bold')
                buffer += self._format_text(kot_data.get('notes'))
            
            buffer += self._create_separator('=')
            buffer += ESCPOS.FEED_3_LINES
            
            # Cut paper
            buffer += ESCPOS.PARTIAL_CUT
            
            # Send to printer
            return self._send_to_printer(buffer)
            
        except Exception as e:
            print(f"Error printing KOT: {e}")
            return False
    
    def _send_to_printer(self, buffer: bytes) -> bool:
        """Send buffer to thermal printer"""
        try:
            if self.printer_name and WIN32_AVAILABLE:
                # Windows printer
                hprinter = win32print.OpenPrinter(self.printer_name)
                try:
                    p = win32print.StartDocPrinter(hprinter, 1, ("Bill", None, "RAW"))
                    try:
                        win32print.WritePrinter(hprinter, buffer)
                        win32print.EndDocPrinter(hprinter)
                        return True
                    finally:
                        win32print.ClosePrinter(hprinter)
                except:
                    win32print.ClosePrinter(hprinter)
                    return False
            else:
                # Try to detect and use USB/Serial thermal printer
                return self._detect_and_print_usb(buffer)
                
        except Exception as e:
            print(f"Error sending to printer: {e}")
            return False
    
    def _detect_and_print_usb(self, buffer: bytes) -> bool:
        """Detect and print to USB thermal printer"""
        try:
            if USB_AVAILABLE:
                # Common thermal printer vendor/product IDs
                thermal_printers = [
                    (0x04b8, 0x0202),  # Epson TM-T20
                    (0x04b8, 0x0e15),  # Epson TM-T88
                    (0x1cb0, 0x0003),  # P3 RONGTA
                ]
                
                for vid, pid in thermal_printers:
                    device = usb.core.find(idVendor=vid, idProduct=pid)
                    if device:
                        try:
                            if device.is_kernel_driver_active(0):
                                device.detach_kernel_driver(0)
                            
                            device.set_configuration()
                            endpoint = device[0][(0,0)][0]
                            device.write(endpoint.bEndpointAddress, buffer, 1000)
                            return True
                        except:
                            pass
            
            # Fallback to serial port
            if SERIAL_AVAILABLE:
                ports = ['COM1', 'COM2', 'COM3', 'COM4', 'COM5']
                for port in ports:
                    try:
                        ser = serial.Serial(port, 9600, timeout=1)
                        ser.write(buffer)
                        ser.close()
                        return True
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error in USB/Serial detection: {e}")
            
        return False


class StandardPrinter:
    """Standard printer implementation using system print dialog"""
    
    def __init__(self, printer_name: str = None):
        self.printer_name = printer_name
    
    def print_bill(self, bill_data: Dict) -> bool:
        """Print a bill using standard printer"""
        try:
            # Create temporary file with bill content
            content = self._format_bill_content(bill_data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_file = f.name
            
            # Print using system command
            if sys.platform == 'win32':
                cmd = f'notepad /p "{temp_file}"'
                if self.printer_name:
                    cmd = f'print /D:"{self.printer_name}" "{temp_file}"'
            else:
                cmd = f'lpr "{temp_file}"'
                if self.printer_name:
                    cmd = f'lpr -P {self.printer_name} "{temp_file}"'
            
            result = subprocess.run(cmd, shell=True, capture_output=True)
            
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error printing with standard printer: {e}")
            return False
    
    def print_kot(self, kot_data: Dict) -> bool:
        """Print a KOT using standard printer"""
        try:
            # Create temporary file with KOT content
            content = self._format_kot_content(kot_data)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(content)
                temp_file = f.name
            
            # Print using system command
            if sys.platform == 'win32':
                cmd = f'notepad /p "{temp_file}"'
                if self.printer_name:
                    cmd = f'print /D:"{self.printer_name}" "{temp_file}"'
            else:
                cmd = f'lpr "{temp_file}"'
                if self.printer_name:
                    cmd = f'lpr -P {self.printer_name} "{temp_file}"'
            
            result = subprocess.run(cmd, shell=True, capture_output=True)
            
            # Clean up
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Error printing KOT with standard printer: {e}")
            return False
    
    def _format_bill_content(self, bill_data: Dict) -> str:
        """Format bill content for standard printer"""
        content = f"""
{bill_data.get('restaurant_name', '').center(50)}
{bill_data.get('restaurant_address', '').center(50)}
{'=' * 50}
{'BILL':^50}
{'=' * 50}
Order No: {bill_data.get('order_number', '')}
Date: {bill_data.get('date', '')}
Order Type: {bill_data.get('order_type', '')}
"""
        
        if bill_data.get('order_type') == 'Dine-in' and bill_data.get('table_number'):
            content += f"Table: {bill_data.get('table_number', '')}\n"
        elif bill_data.get('order_type') == 'Takeaway' and bill_data.get('customer_name'):
            content += f"Customer: {bill_data.get('customer_name', '')}\n"
            if bill_data.get('customer_mobile'):
                content += f"Mobile: {bill_data.get('customer_mobile', '')}\n"
        
        content += f"""
{'=' * 50}
{'Item':<20} {'Qty':<5} {'Price':<10} {'Total':<10}
{'-' * 50}
"""
        
        for item in bill_data.get('items', []):
            name, quantity, price, total = item
            content += f"{name:<20} {quantity:<5} {price:<9.2f} {total:<9.2f}\n"
        
        content += f"""
{'-' * 50}
Subtotal: {bill_data.get('subtotal', 0):.2f}
Tax ({bill_data.get('tax_rate', 5)}%): {bill_data.get('tax', 0):.2f}
Discount: {bill_data.get('discount', 0):.2f}
{'=' * 50}
Total: {bill_data.get('total', 0):.2f}
{'=' * 50}
Thank you for dining with us!
"""
        
        return content
    
    def _format_kot_content(self, kot_data: Dict) -> str:
        """Format KOT content for standard printer"""
        content = f"""
{'KITCHEN ORDER TICKET':^40}
{'=' * 40}
Order No: {kot_data.get('order_number', '')}
Time: {kot_data.get('time', '')}
{'-' * 40}
Item: {kot_data.get('item_name', '')}
Quantity: {kot_data.get('quantity', '')}
"""
        
        if kot_data.get('notes'):
            content += f"""
{'-' * 40}
Notes:
{kot_data.get('notes')}
"""
        
        content += f"{'=' * 40}\n"
        
        return content


class PrinterManager:
    """Main printer management class"""
    
    def __init__(self, settings: Dict = None):
        self.settings = settings or {}
        self.thermal_printer = None
        self.standard_printer = None
        
        # Initialize printers
        self._initialize_printers()
    
    def _initialize_printers(self):
        """Initialize printer instances"""
        thermal_name = self.settings.get('thermal_printer_name')
        standard_name = self.settings.get('standard_printer_name')
        
        if thermal_name:
            paper_width = int(self.settings.get('bill_paper_width', PaperSize.MM58))
            self.thermal_printer = ThermalPrinter(thermal_name, paper_width)
        
        if standard_name:
            self.standard_printer = StandardPrinter(standard_name)
    
    def get_available_printers(self) -> Dict[str, List[str]]:
        """Get list of available printers"""
        printers = {
            'thermal': [],
            'standard': []
        }
        
        # Get standard printers
        if WIN32_AVAILABLE:
            try:
                printer_list = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
                for printer in printer_list:
                    printer_name = printer[2]  # Printer name is at index 2
                    printers['standard'].append(printer_name)
                    
                    # Check if it might be a thermal printer
                    if any(keyword in printer_name.lower() for keyword in ['thermal', 'pos', 'receipt', 'ticket']):
                        printers['thermal'].append(printer_name)
            except Exception as e:
                print(f"Error enumerating printers: {e}")
        
        # Add common thermal printer names for USB detection
        if USB_AVAILABLE:
            common_thermal = [
                'EPSON TM-T20',
                'EPSON TM-T88',
                'P3 RONGTA',
                'Custom TG2460',
                'POS-58',
                'POS-80'
            ]
            for printer in common_thermal:
                if printer not in printers['thermal']:
                    printers['thermal'].append(printer)
        
        return printers
    
    def print_bill(self, bill_data: Dict, printer_type: str = None, printer_name: str = None) -> bool:
        """Print bill using specified printer"""
        try:
            # Determine printer type
            if not printer_type:
                printer_type = self.settings.get('default_bill_printer', PrinterType.STANDARD)
            
            # Use specified printer or default
            if printer_type == PrinterType.THERMAL:
                printer = self.thermal_printer
                if printer_name:
                    paper_width = int(self.settings.get('bill_paper_width', PaperSize.MM58))
                    printer = ThermalPrinter(printer_name, paper_width)
                
                if printer:
                    return printer.print_bill(bill_data)
            else:
                printer = self.standard_printer
                if printer_name:
                    printer = StandardPrinter(printer_name)
                
                if printer:
                    return printer.print_bill(bill_data)
            
            return False
            
        except Exception as e:
            print(f"Error in print_bill: {e}")
            return False
    
    def print_kot(self, kot_data: Dict, printer_type: str = None, printer_name: str = None) -> bool:
        """Print KOT using specified printer"""
        try:
            # Determine printer type
            if not printer_type:
                printer_type = self.settings.get('default_kot_printer', PrinterType.THERMAL)
            
            # Use specified printer or default
            if printer_type == PrinterType.THERMAL:
                printer = self.thermal_printer
                if printer_name:
                    paper_width = int(self.settings.get('kot_paper_width', PaperSize.MM58))
                    printer = ThermalPrinter(printer_name, paper_width)
                
                if printer:
                    return printer.print_kot(kot_data)
            else:
                printer = self.standard_printer
                if printer_name:
                    printer = StandardPrinter(printer_name)
                
                if printer:
                    return printer.print_kot(kot_data)
            
            return False
            
        except Exception as e:
            print(f"Error in print_kot: {e}")
            return False
    
    def test_printer(self, printer_type: str, printer_name: str) -> bool:
        """Test printer connection"""
        try:
            if printer_type == PrinterType.THERMAL:
                paper_width = int(self.settings.get('bill_paper_width', PaperSize.MM58))
                printer = ThermalPrinter(printer_name, paper_width)
                
                # Simple test print
                test_data = {
                    'restaurant_name': 'Test Restaurant',
                    'order_number': 'TEST001',
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_type': 'Test',
                    'items': [('Test Item', 1, 10.00, 10.00)],
                    'subtotal': 10.00,
                    'tax': 0.50,
                    'discount': 0.00,
                    'total': 10.50,
                    'tax_rate': 5
                }
                return printer.print_bill(test_data)
            else:
                printer = StandardPrinter(printer_name)
                test_data = {
                    'restaurant_name': 'Test Restaurant',
                    'order_number': 'TEST001',
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'order_type': 'Test',
                    'items': [('Test Item', 1, 10.00, 10.00)],
                    'subtotal': 10.00,
                    'tax': 0.50,
                    'discount': 0.00,
                    'total': 10.50,
                    'tax_rate': 5
                }
                return printer.print_bill(test_data)
                
        except Exception as e:
            print(f"Error testing printer: {e}")
            return False
    
    def _add_footer_to_print(self, bill_data: Dict) -> bytes:
        """Add footer to print buffer"""
        buffer = ESCPOS.FEED_LINE
        
        if not self.settings_manager:
            # Use default footer if no settings manager
            buffer += self._format_text("Thank you for dining with us!", 'center')
            buffer += ESCPOS.FEED_3_LINES
            return buffer
        
        # Get footer settings
        footer_settings = self.settings_manager.get_footer_settings()
        
        if not footer_settings.get('footer_enabled', 'true').lower() == 'true':
            return buffer
        
        # Generate footer based on template
        template = footer_settings.get('footer_template', 'default')
        
        if template == 'minimal':
            buffer += self._add_minimal_footer_print(footer_settings)
        elif template == 'detailed':
            buffer += self._add_detailed_footer_print(footer_settings, bill_data)
        else:
            buffer += self._add_default_footer_print(footer_settings, bill_data)
        
        return buffer
    
    def _add_default_footer_print(self, footer_settings: Dict, bill_data: Dict) -> bytes:
        """Add default footer to print buffer"""
        buffer = b''
        
        # Custom text
        custom_text = footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            buffer += self._format_text(custom_text, 'center')
            buffer += ESCPOS.FEED_LINE
        
        # User info
        if footer_settings.get('footer_show_user_name', 'true').lower() == 'true' and bill_data:
            # For printing, we'll use a generic user since we don't have user info in bill_data
            buffer += self._format_text("Processed by POS System", 'center')
            buffer += ESCPOS.FEED_LINE
        
        # Receipt info
        if footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and bill_data:
            order_number = bill_data.get('order_number', 'N/A')
            date = bill_data.get('date', '')
            if order_number and date:
                buffer += self._format_text(f"Receipt #{order_number} - {date}", 'center')
                buffer += ESCPOS.FEED_LINE
        
        # Business info
        if footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            # Get business info from bill_data or use defaults
            name = bill_data.get('restaurant_name', '')
            phone = bill_data.get('restaurant_phone', '')
            
            info_parts = []
            if name:
                info_parts.append(name)
            if phone:
                info_parts.append(phone)
            
            if info_parts:
                buffer += self._format_text(" | ".join(info_parts), 'center')
                buffer += ESCPOS.FEED_LINE
        
        # Multiline footer
        if footer_settings.get('footer_multiline', 'false').lower() == 'true':
            lines = [
                footer_settings.get('footer_line1', ''),
                footer_settings.get('footer_line2', ''),
                footer_settings.get('footer_line3', '')
            ]
            for line in lines:
                if line:
                    buffer += self._format_text(line, 'center')
                    buffer += ESCPOS.FEED_LINE
        
        buffer += ESCPOS.FEED_3_LINES
        return buffer
    
    def _add_minimal_footer_print(self, footer_settings: Dict) -> bytes:
        """Add minimal footer to print buffer"""
        buffer = b''
        custom_text = footer_settings.get('footer_custom_text', 'Thank you!')
        if custom_text:
            buffer += self._format_text(custom_text, 'center')
            buffer += ESCPOS.FEED_LINE
            buffer += ESCPOS.FEED_2_LINES
        return buffer
    
    def _add_detailed_footer_print(self, footer_settings: Dict, bill_data: Dict) -> bytes:
        """Add detailed footer to print buffer"""
        buffer = b''
        
        # Custom text
        custom_text = footer_settings.get('footer_custom_text', 'Thank you for your business!')
        if custom_text:
            buffer += self._create_separator('=')
            buffer += self._format_text(f"*** {custom_text} ***", 'center', 'bold')
            buffer += self._create_separator('=')
            buffer += ESCPOS.FEED_LINE
        
        # User info
        if footer_settings.get('footer_show_user_name', 'true').lower() == 'true':
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            buffer += self._format_text(f"Processed by POS System at {timestamp}", 'center')
            buffer += ESCPOS.FEED_LINE
        
        # Receipt info
        if footer_settings.get('footer_show_receipt_info', 'true').lower() == 'true' and bill_data:
            order_number = bill_data.get('order_number', 'N/A')
            date = bill_data.get('date', '')
            if order_number:
                buffer += self._format_text(f"Receipt: {order_number}", 'center')
            if date:
                buffer += self._format_text(f"Date: {date}", 'center')
            buffer += ESCPOS.FEED_LINE
        
        # Business info
        if footer_settings.get('footer_show_business_info', 'true').lower() == 'true':
            name = bill_data.get('restaurant_name', '')
            address = bill_data.get('restaurant_address', '')
            phone = bill_data.get('restaurant_phone', '')
            
            if name:
                buffer += self._format_text(f"Business: {name}", 'center')
            if address:
                buffer += self._format_text(f"Address: {address}", 'center')
            if phone:
                buffer += self._format_text(f"Phone: {phone}", 'center')
            buffer += ESCPOS.FEED_LINE
        
        # Additional terms
        buffer += self._create_separator('-')
        buffer += self._format_text("This is a computer generated document.", 'center')
        buffer += ESCPOS.FEED_LINE
        buffer += self._format_text("Goods once sold will not be taken back.", 'center')
        buffer += ESCPOS.FEED_LINE
        buffer += self._format_text("All disputes are subject to local jurisdiction.", 'center')
        buffer += ESCPOS.FEED_LINE
        
        buffer += self._create_separator('=')
        buffer += ESCPOS.FEED_3_LINES
        return buffer