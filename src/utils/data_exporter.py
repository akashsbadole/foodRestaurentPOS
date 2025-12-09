"""
Data Exporter for POS Application
Handles exporting all POS data to various formats
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

class DataExporter:
    """Handles exporting POS data to various formats"""
    
    def __init__(self, app, data_manager):
        self.app = app
        self.data_manager = data_manager
        
        # Export file templates
        self.EXPORT_TYPES = {
            'orders': self.export_orders,
            'menu_items': self.export_menu_items,
            'categories': self.export_categories,
            'tables': self.export_tables,
            'users': self.export_users,
            'inventory': self.export_inventory,
            'settings': self.export_settings,
            'all': self.export_all
        }
        
        self.FORMATS = {
            'json': self._export_json,
            'csv': self._export_csv,
            'excel': self._export_excel
        }
    
    def export_data(self, export_type: str, format_type: str, file_path: str, 
                   include_details: bool = False, date_range: Dict = None) -> bool:
        """
        Export data to specified format
        
        Args:
            export_type: Type of data to export ('orders', 'menu_items', etc.)
            format_type: Export format ('json', 'csv', 'excel')
            file_path: Output file path
            include_details: Whether to include detailed information
            date_range: Date range filter for orders
            
        Returns:
            bool: Success status
        """
        try:
            if export_type not in self.EXPORT_TYPES:
                raise ValueError(f"Invalid export type: {export_type}")
            
            if format_type not in self.FORMATS:
                raise ValueError(f"Invalid format type: {format_type}")
            
            # Get data
            data = self.EXPORT_TYPES[export_type](include_details, date_range)
            
            if not data:
                raise ValueError(f"No data found for export type: {export_type}")
            
            # Add metadata
            export_metadata = {
                'export_type': export_type,
                'export_date': datetime.now().isoformat(),
                'export_format': format_type,
                'version': '1.0',
                'include_details': include_details,
                'date_range': date_range
            }
            
            # Create export data structure
            export_data = {
                'metadata': export_metadata,
                'data': data
            }
            
            # Export to specified format
            success = self.FORMATS[format_type](export_data, file_path)
            
            return success
            
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False
    
    def export_orders(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export orders data"""
        try:
            # Get orders with optional date filtering
            filter_value = "All"
            if date_range:
                # Apply date range filtering logic here
                pass
            
            orders = self.data_manager.get_orders(filter_value, "", force_refresh=True)
            orders_data = []
            
            for order in orders:
                order_data = {
                    'id': order['id'],
                    'order_number': order['order_number'],
                    'created_at': order['created_at'],
                    'order_type': order['order_type'],
                    'table_number': order['table_number'],
                    'total': order['total'],
                    'status': order['status'],
                    'customer_name': order['customer_name']
                }
                
                # Include detailed information if requested
                if include_details:
                    order_details = self.data_manager.get_order_details(order['id'])
                    if order_details:
                        order_data.update({
                            'subtotal': order_details['subtotal'],
                            'tax': order_details['tax'],
                            'discount': order_details['discount'],
                            'items': order_details['items'],
                            'payments': order_details['payments']
                        })
                
                orders_data.append(order_data)
            
            return {
                'orders': orders_data,
                'count': len(orders_data)
            }
            
        except Exception as e:
            print(f"Error exporting orders: {e}")
            return {}
    
    def export_menu_items(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export menu items data"""
        try:
            items = self.data_manager.get_menu_items("", "", force_refresh=True)
            categories = self.data_manager.get_categories(force_refresh=True)
            
            # Create category mapping
            category_map = {cat['id']: cat['name'] for cat in categories}
            
            items_data = []
            for item in items:
                item_data = {
                    'id': item['id'],
                    'name': item['name'],
                    'category_name': item['category_name'],
                    'price': item['price'],
                    'stock_quantity': item['stock_quantity']
                }
                
                items_data.append(item_data)
            
            return {
                'menu_items': items_data,
                'categories': categories,
                'count': len(items_data)
            }
            
        except Exception as e:
            print(f"Error exporting menu items: {e}")
            return {}
    
    def export_categories(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export categories data"""
        try:
            categories = self.data_manager.get_categories(force_refresh=True)
            
            return {
                'categories': categories,
                'count': len(categories)
            }
            
        except Exception as e:
            print(f"Error exporting categories: {e}")
            return {}
    
    def export_tables(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export tables data"""
        try:
            tables = self.data_manager.get_tables(force_refresh=True)
            
            return {
                'tables': tables,
                'count': len(tables)
            }
            
        except Exception as e:
            print(f"Error exporting tables: {e}")
            return {}
    
    def export_users(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export users data"""
        try:
            users = self.app.user_model.get_all()
            users_data = []
            
            for user in users:
                user_data = {
                    'username': user[0],
                    'role': user[1]
                }
                users_data.append(user_data)
            
            return {
                'users': users_data,
                'count': len(users_data)
            }
            
        except Exception as e:
            print(f"Error exporting users: {e}")
            return {}
    
    def export_inventory(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export inventory data"""
        try:
            items = self.data_manager.get_inventory_items("", "All", force_refresh=True)
            
            return {
                'inventory_items': items,
                'count': len(items)
            }
            
        except Exception as e:
            print(f"Error exporting inventory: {e}")
            return {}
    
    def export_settings(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export settings data"""
        try:
            settings = self.data_manager.get_settings(force_refresh=True)
            
            return {
                'settings': settings,
                'count': len(settings)
            }
            
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return {}
    
    def export_all(self, include_details: bool = False, date_range: Dict = None) -> Dict:
        """Export all data"""
        try:
            all_data = {}
            
            # Export all data types
            for export_type in ['orders', 'menu_items', 'categories', 'tables', 'users', 'inventory', 'settings']:
                data = self.EXPORT_TYPES[export_type](include_details, date_range)
                if data:
                    all_data[export_type] = data
            
            return all_data
            
        except Exception as e:
            print(f"Error exporting all data: {e}")
            return {}
    
    def _export_json(self, data: Dict, file_path: str) -> bool:
        """Export data to JSON format"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def _export_csv(self, data: Dict, file_path: str) -> bool:
        """Export data to CSV format"""
        try:
            export_type = data['metadata']['export_type']
            actual_data = data['data']
            
            if export_type == 'all':
                # For 'all' type, create multiple CSV files
                base_path = os.path.splitext(file_path)[0]
                for data_type, type_data in actual_data.items():
                    if isinstance(type_data, dict) and 'data' in type_data:
                        csv_file = f"{base_path}_{data_type}.csv"
                        self._write_csv_data(type_data['data'], csv_file)
                return True
            else:
                # Single data type
                return self._write_csv_data(actual_data, file_path)
                
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def _write_csv_data(self, data: Dict, file_path: str) -> bool:
        """Write data to CSV file"""
        try:
            # Extract the actual data list from the data dictionary
            if isinstance(data, dict):
                # Find the key that contains the actual data list
                data_list = None
                for key, value in data.items():
                    if isinstance(value, list):
                        data_list = value
                        break
                
                if data_list is None:
                    return False
            else:
                data_list = data
            
            if not data_list:
                return True  # Empty file is valid
            
            # Get headers from first item
            if isinstance(data_list[0], dict):
                fieldnames = data_list[0].keys()
            else:
                # Handle simple data structures
                fieldnames = ['value']
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in data_list:
                    if isinstance(item, dict):
                        writer.writerow(item)
                    else:
                        writer.writerow({'value': item})
            
            return True
            
        except Exception as e:
            print(f"Error writing CSV data: {e}")
            return False
    
    def _export_excel(self, data: Dict, file_path: str) -> bool:
        """Export data to Excel format"""
        try:
            export_type = data['metadata']['export_type']
            actual_data = data['data']
            
            wb = Workbook()
            
            # Remove default sheet
            wb.remove(wb.active)
            
            if export_type == 'all':
                # Create separate sheets for each data type
                for data_type, type_data in actual_data.items():
                    if isinstance(type_data, dict):
                        sheet_name = data_type.replace('_', ' ').title()
                        self._create_excel_sheet(wb, sheet_name, type_data)
            else:
                # Single data type
                sheet_name = export_type.replace('_', ' ').title()
                self._create_excel_sheet(wb, sheet_name, actual_data)
            
            # Save workbook
            wb.save(file_path)
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def _create_excel_sheet(self, workbook, sheet_name: str, data: Dict):
        """Create Excel sheet with data"""
        try:
            ws = workbook.create_sheet(title=sheet_name)
            
            # Extract actual data list
            if isinstance(data, dict):
                data_list = None
                for key, value in data.items():
                    if isinstance(value, list):
                        data_list = value
                        break
                
                if data_list is None:
                    return
            else:
                data_list = data
            
            if not data_list:
                return
            
            # Get headers
            if isinstance(data_list[0], dict):
                headers = list(data_list[0].keys())
            else:
                headers = ['Value']
            
            # Write headers with styling
            header_font = Font(bold=True)
            header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
            
            for col_idx, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_idx, value=header)
                cell.font = header_font
                cell.fill = header_fill
            
            # Write data
            for row_idx, item in enumerate(data_list, 2):
                if isinstance(item, dict):
                    for col_idx, header in enumerate(headers, 1):
                        ws.cell(row=row_idx, column=col_idx, value=item.get(header, ''))
                else:
                    ws.cell(row=row_idx, column=1, value=item)
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
                
        except Exception as e:
            print(f"Error creating Excel sheet: {e}")

    def get_export_summary(self) -> Dict:
        """Get summary of available data for export"""
        try:
            summary = {
                'orders': len(self.data_manager.get_orders(force_refresh=True)),
                'menu_items': len(self.data_manager.get_menu_items(force_refresh=True)),
                'categories': len(self.data_manager.get_categories(force_refresh=True)),
                'tables': len(self.data_manager.get_tables(force_refresh=True)),
                'users': len(self.app.user_model.get_all()),
                'inventory_items': len(self.data_manager.get_inventory_items(force_refresh=True)),
                'settings': len(self.data_manager.get_settings(force_refresh=True))
            }
            
            return summary
            
        except Exception as e:
            print(f"Error getting export summary: {e}")
            return {}
