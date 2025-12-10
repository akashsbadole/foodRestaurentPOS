"""
Data Importer for POS Application
Handles importing POS data from various formats with validation
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from openpyxl import load_workbook

class DataImporter:
    """Handles importing POS data from various formats with validation"""
    
    def __init__(self, app, data_manager):
        self.app = app
        self.data_manager = data_manager
        self.import_log = []
        
        # Import handlers
        self.IMPORT_TYPES = {
            'orders': self.import_orders,
            'menu_items': self.import_menu_items,
            'categories': self.import_categories,
            'tables': self.import_tables,
            'users': self.import_users,
            'inventory': self.import_inventory,
            'settings': self.import_settings,
            'all': self.import_all
        }
        
        self.FORMATS = {
            'json': self._import_json,
            'csv': self._import_csv,
            'excel': self._import_excel
        }
    
    def import_data(self, file_path: str, import_type: str = 'auto', 
                   validate_only: bool = False, overwrite: bool = False) -> Dict:
        """
        Import data from file
        
        Args:
            file_path: Path to import file
            import_type: Type of data to import ('auto', 'orders', 'menu_items', etc.)
            validate_only: Only validate data without importing
            overwrite: Overwrite existing data
            
        Returns:
            Dict: Import result with status and details
        """
        try:
            self.import_log = []
            
            # Determine file format
            file_format = self._detect_file_format(file_path)
            if not file_format:
                return {
                    'success': False,
                    'error': 'Unsupported file format',
                    'details': self.import_log
                }
            
            # Read data from file
            raw_data = self._read_file(file_path, file_format)
            if not raw_data:
                return {
                    'success': False,
                    'error': 'Failed to read file or file is empty',
                    'details': self.import_log
                }
            
            # Determine import type
            if import_type == 'auto':
                import_type = self._detect_import_type(raw_data)
                if not import_type:
                    return {
                        'success': False,
                        'error': 'Could not determine import type',
                        'details': self.import_log
                    }
            
            # Validate import type
            if import_type not in self.IMPORT_TYPES:
                return {
                    'success': False,
                    'error': f'Invalid import type: {import_type}',
                    'details': self.import_log
                }
            
            # Extract and validate data
            import_data = self._extract_import_data(raw_data, import_type, file_format)
            if not import_data:
                return {
                    'success': False,
                    'error': 'Failed to extract valid data',
                    'details': self.import_log
                }
            
            # Validate data
            validation_result = self._validate_import_data(import_data, import_type)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Data validation failed',
                    'validation_errors': validation_result['errors'],
                    'details': self.import_log
                }
            
            if validate_only:
                return {
                    'success': True,
                    'message': 'Data validation passed',
                    'validation_result': validation_result,
                    'details': self.import_log
                }
            
            # Perform import
            import_result = self.IMPORT_TYPES[import_type](import_data, overwrite)
            
            # Refresh caches after successful import
            if import_result.get('success', False):
                self.data_manager.refresh_all_data()
            
            return import_result
            
        except Exception as e:
            self.import_log.append(f"Import error: {str(e)}")
            return {
                'success': False,
                'error': f'Import failed: {str(e)}',
                'details': self.import_log
            }
    
    def _detect_file_format(self, file_path: str) -> Optional[str]:
        """Detect file format from file extension"""
        _, ext = os.path.splitext(file_path.lower())
        
        format_map = {
            '.json': 'json',
            '.csv': 'csv',
            '.xlsx': 'excel',
            '.xls': 'excel'
        }
        
        return format_map.get(ext)
    
    def _detect_import_type(self, data: Dict) -> Optional[str]:
        """Auto-detect import type from data structure"""
        if not isinstance(data, dict):
            return None
        
        # Check for specific keys
        if 'metadata' in data and 'data' in data:
            # Structured export format
            data_content = data['data']
            if isinstance(data_content, dict):
                for import_type in ['orders', 'menu_items', 'categories', 'tables', 'users', 'inventory', 'settings']:
                    if import_type in data_content:
                        return import_type
                return 'all'
        
        # Check for direct data lists
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                # Try to determine type from first item
                first_item = value[0]
                if isinstance(first_item, dict):
                    if 'order_number' in first_item:
                        return 'orders'
                    elif 'price' in first_item and 'category_name' in first_item:
                        return 'menu_items'
                    elif 'table_number' in first_item:
                        return 'tables'
                    elif 'username' in first_item and 'role' in first_item:
                        return 'users'
                    elif 'stock_quantity' in first_item:
                        return 'inventory'
                    elif 'name' in first_item and len(first_item) <= 2:
                        return 'categories'
        
        return None
    
    def _read_file(self, file_path: str, file_format: str) -> Optional[Dict]:
        """Read file based on format"""
        try:
            if file_format not in self.FORMATS:
                return None
            
            return self.FORMATS[file_format](file_path)
            
        except Exception as e:
            self.import_log.append(f"Error reading file: {str(e)}")
            return None
    
    def _import_json(self, file_path: str) -> Optional[Dict]:
        """Import JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.import_log.append(f"JSON import error: {str(e)}")
            return None
    
    def _import_csv(self, file_path: str) -> Optional[Dict]:
        """Import CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                
                # Auto-detect type from CSV headers
                if data:
                    headers = data[0].keys()
                    if 'order_number' in headers:
                        return {'orders': data}
                    elif 'price' in headers and 'category_name' in headers:
                        return {'menu_items': data}
                    elif 'table_number' in headers:
                        return {'tables': data}
                    elif 'username' in headers:
                        return {'users': data}
                    elif 'stock_quantity' in headers:
                        return {'inventory': data}
                    elif 'name' in headers and len(headers) <= 2:
                        return {'categories': data}
                
                return None
                
        except Exception as e:
            self.import_log.append(f"CSV import error: {str(e)}")
            return None
    
    def _import_excel(self, file_path: str) -> Optional[Dict]:
        """Import Excel file"""
        try:
            wb = load_workbook(file_path, read_only=True)
            data = {}
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                data_list = []
                
                # Get headers
                headers = []
                for cell in ws[1]:
                    if cell.value:
                        headers.append(str(cell.value))
                
                # Read data rows
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if any(cell is not None for cell in row):
                        row_data = {}
                        for i, value in enumerate(row):
                            if i < len(headers):
                                row_data[headers[i]] = value
                        data_list.append(row_data)
                
                if data_list:
                    # Convert sheet name to data type
                    sheet_key = sheet_name.lower().replace(' ', '_')
                    data[sheet_key] = data_list
            
            return data if data else None
            
        except Exception as e:
            self.import_log.append(f"Excel import error: {str(e)}")
            return None
    
    def _extract_import_data(self, raw_data: Dict, import_type: str, file_format: str) -> Optional[Dict]:
        """Extract and normalize import data"""
        try:
            if 'metadata' in raw_data and 'data' in raw_data:
                # Structured export format
                data_content = raw_data['data']
                if import_type == 'all':
                    return data_content
                elif import_type in data_content:
                    return data_content[import_type]
                else:
                    return None
            else:
                # Direct data format
                if import_type == 'all':
                    return raw_data
                elif import_type in raw_data:
                    return {import_type: raw_data[import_type]}
                else:
                    return raw_data
                    
        except Exception as e:
            self.import_log.append(f"Data extraction error: {str(e)}")
            return None
    
    def _validate_import_data(self, data: Dict, import_type: str) -> Dict:
        """Validate import data"""
        try:
            errors = []
            warnings = []
            
            # Get data list
            data_list = None
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        data_list = value
                        break
            elif isinstance(data, list):
                data_list = data
            
            if not data_list:
                errors.append("No data found to import")
                return {'valid': False, 'errors': errors, 'warnings': warnings}
            
            # Type-specific validation
            if import_type == 'orders':
                self._validate_orders(data_list, errors, warnings)
            elif import_type == 'menu_items':
                self._validate_menu_items(data_list, errors, warnings)
            elif import_type == 'categories':
                self._validate_categories(data_list, errors, warnings)
            elif import_type == 'tables':
                self._validate_tables(data_list, errors, warnings)
            elif import_type == 'users':
                self._validate_users(data_list, errors, warnings)
            elif import_type == 'inventory':
                self._validate_inventory(data_list, errors, warnings)
            elif import_type == 'settings':
                self._validate_settings(data_list, errors, warnings)
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'record_count': len(data_list)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def _validate_orders(self, orders: List[Dict], errors: List, warnings: List):
        """Validate orders data"""
        for i, order in enumerate(orders):
            row_num = i + 1
            
            if not order.get('order_number'):
                errors.append(f"Row {row_num}: Order number is required")
            
            if not order.get('total'):
                errors.append(f"Row {row_num}: Order total is required")
            
            if order.get('order_type') not in ['Dine-in', 'Takeaway']:
                warnings.append(f"Row {row_num}: Invalid order type")
    
    def _validate_menu_items(self, items: List[Dict], errors: List, warnings: List):
        """Validate menu items data"""
        for i, item in enumerate(items):
            row_num = i + 1
            
            if not item.get('name'):
                errors.append(f"Row {row_num}: Item name is required")
            
            if not item.get('price') or float(item.get('price', 0)) < 0:
                errors.append(f"Row {row_num}: Valid price is required")
            
            if not item.get('category_name'):
                warnings.append(f"Row {row_num}: Category name is recommended")
    
    def _validate_categories(self, categories: List[Dict], errors: List, warnings: List):
        """Validate categories data"""
        for i, category in enumerate(categories):
            row_num = i + 1
            
            if not category.get('name'):
                errors.append(f"Row {row_num}: Category name is required")
    
    def _validate_tables(self, tables: List[Dict], errors: List, warnings: List):
        """Validate tables data"""
        for i, table in enumerate(tables):
            row_num = i + 1
            
            if not table.get('table_number'):
                errors.append(f"Row {row_num}: Table number is required")
            
            if table.get('capacity') and int(table.get('capacity', 0)) <= 0:
                errors.append(f"Row {row_num}: Valid capacity is required")
    
    def _validate_users(self, users: List[Dict], errors: List, warnings: List):
        """Validate users data"""
        for i, user in enumerate(users):
            row_num = i + 1
            
            if not user.get('username'):
                errors.append(f"Row {row_num}: Username is required")
            
            if not user.get('role') or user.get('role') not in ['Admin', 'Cashier']:
                errors.append(f"Row {row_num}: Valid role is required")
    
    def _validate_inventory(self, items: List[Dict], errors: List, warnings: List):
        """Validate inventory data"""
        for i, item in enumerate(items):
            row_num = i + 1
            
            if not item.get('name'):
                errors.append(f"Row {row_num}: Item name is required")
            
            stock_qty = item.get('stock_quantity')
            if stock_qty is None or int(stock_qty) < 0:
                errors.append(f"Row {row_num}: Valid stock quantity is required")
    
    def _validate_settings(self, settings: List[Dict], errors: List, warnings: List):
        """Validate settings data"""
        pass  # Settings validation would depend on specific setting requirements
    
    # Import methods for different data types
    def import_orders(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import orders data"""
        try:
            orders = data.get('orders', [])
            imported_count = 0
            errors = []
            
            for order_data in orders:
                try:
                    # Check if order already exists
                    if not overwrite:
                        existing_orders = self.app.order_model.get_orders("", order_data.get('order_number', ''))
                        if existing_orders:
                            errors.append(f"Order {order_data.get('order_number')} already exists")
                            continue
                    
                    # Create order using dictionary format
                    order_dict = {
                        'order_number': order_data.get('order_number', ''),
                        'table_id': order_data.get('table_id'),
                        'customer_name': order_data.get('customer_name', ''),
                        'customer_mobile': order_data.get('customer_mobile', ''),
                        'order_type': order_data.get('order_type', 'Dine-in'),
                        'subtotal': order_data.get('subtotal', 0),
                        'tax': order_data.get('tax', 0),
                        'discount': order_data.get('discount', 0),
                        'total': order_data.get('total', 0)
                    }
                    order_id = self.app.order_model.create(order_dict)
                    
                    if order_id:
                        imported_count += 1
                        # Import items if present
                        if 'items' in order_data:
                            for item in order_data['items']:
                                self.app.order_model.add_item(
                                    order_id,
                                    item.get('menu_item_id'),
                                    item.get('quantity', 1),
                                    item.get('price', 0),
                                    item.get('total', 0)
                                )
                    else:
                        errors.append(f"Failed to create order {order_data.get('order_number')}")
                        
                except Exception as e:
                    errors.append(f"Error importing order: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} orders"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Orders import failed: {str(e)}"
            }
    
    def import_menu_items(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import menu items data"""
        try:
            items = data.get('menu_items', [])
            categories = data.get('categories', [])
            imported_count = 0
            errors = []
            
            # Import categories first
            category_map = {}
            for category in categories:
                try:
                    if not overwrite:
                        existing_categories = self.app.category_model.get_all()
                        if any(cat[1] == category['name'] for cat in existing_categories):
                            category_map[category['name']] = next(cat[0] for cat in existing_categories if cat[1] == category['name'])
                            continue
                    
                    category_id = self.app.category_model.add(category['name'])
                    if category_id:
                        category_map[category['name']] = category_id
                        imported_count += 1
                    else:
                        errors.append(f"Failed to create category {category['name']}")
                except Exception as e:
                    errors.append(f"Error importing category: {str(e)}")
            
            # Import menu items
            for item in items:
                try:
                    category_name = item.get('category_name', '')
                    category_id = category_map.get(category_name)
                    
                    if not category_id:
                        errors.append(f"Category not found for item {item.get('name')}")
                        continue
                    
                    success = self.app.menu_item_model.add(
                        item.get('name', ''),
                        item.get('price', 0),
                        category_id,
                        item.get('stock_quantity', 0),
                        item.get('image_path', '')
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Failed to create menu item {item.get('name')}")
                        
                except Exception as e:
                    errors.append(f"Error importing menu item: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} menu items"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Menu items import failed: {str(e)}"
            }
    
    def import_categories(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import categories data"""
        try:
            categories = data.get('categories', [])
            imported_count = 0
            errors = []
            
            for category in categories:
                try:
                    if not overwrite:
                        existing_categories = self.app.category_model.get_all()
                        if any(cat[1] == category['name'] for cat in existing_categories):
                            errors.append(f"Category {category['name']} already exists")
                            continue
                    
                    success = self.app.category_model.add(category['name'])
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Failed to create category {category['name']}")
                        
                except Exception as e:
                    errors.append(f"Error importing category: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} categories"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Categories import failed: {str(e)}"
            }
    
    def import_tables(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import tables data"""
        try:
            tables = data.get('tables', [])
            imported_count = 0
            errors = []
            
            for table in tables:
                try:
                    if not overwrite:
                        existing_tables = self.app.table_model.get_all()
                        if any(t[1] == table['table_number'] for t in existing_tables):
                            errors.append(f"Table {table['table_number']} already exists")
                            continue
                    
                    success = self.app.table_model.add(
                        table.get('table_number', ''),
                        table.get('capacity', 4)
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Failed to create table {table.get('table_number')}")
                        
                except Exception as e:
                    errors.append(f"Error importing table: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} tables"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Tables import failed: {str(e)}"
            }
    
    def import_users(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import users data"""
        try:
            users = data.get('users', [])
            imported_count = 0
            errors = []
            
            for user in users:
                try:
                    if not overwrite:
                        existing_users = self.app.user_model.get_all()
                        if any(u[0] == user['username'] for u in existing_users):
                            errors.append(f"User {user['username']} already exists")
                            continue
                    
                    # Default password for imported users
                    success = self.app.user_model.add(
                        user.get('username', ''),
                        'password123',  # Default password
                        user.get('role', 'Cashier')
                    )
                    
                    if success:
                        imported_count += 1
                    else:
                        errors.append(f"Failed to create user {user.get('username')}")
                        
                except Exception as e:
                    errors.append(f"Error importing user: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} users"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Users import failed: {str(e)}"
            }
    
    def import_inventory(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import inventory data"""
        try:
            items = data.get('inventory_items', [])
            imported_count = 0
            errors = []
            
            for item in items:
                try:
                    # Find existing menu item
                    menu_items = self.app.menu_item_model.get_all(item.get('name', ''))
                    if menu_items:
                        menu_item_id = menu_items[0][0]
                        
                        # Update stock
                        self.app.menu_item_model.update_stock(
                            menu_item_id,
                            item.get('stock_quantity', 0)
                        )
                        imported_count += 1
                    else:
                        errors.append(f"Menu item not found: {item.get('name')}")
                        
                except Exception as e:
                    errors.append(f"Error updating inventory: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Updated {imported_count} inventory items"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Inventory import failed: {str(e)}"
            }
    
    def import_settings(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import settings data"""
        try:
            settings = data.get('settings', {})
            imported_count = 0
            errors = []
            
            for key, value in settings.items():
                try:
                    self.app.settings_model.update(key, value)
                    imported_count += 1
                except Exception as e:
                    errors.append(f"Error importing setting {key}: {str(e)}")
            
            return {
                'success': imported_count > 0,
                'imported_count': imported_count,
                'errors': errors,
                'message': f"Imported {imported_count} settings"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Settings import failed: {str(e)}"
            }
    
    def import_all(self, data: Dict, overwrite: bool = False) -> Dict:
        """Import all data types"""
        try:
            results = {}
            total_imported = 0
            all_errors = []
            
            # Import in dependency order
            import_order = ['categories', 'menu_items', 'tables', 'users', 'orders', 'inventory', 'settings']
            
            for data_type in import_order:
                if data_type in data:
                    result = self.IMPORT_TYPES[data_type](data[data_type], overwrite)
                    results[data_type] = result
                    
                    if result.get('success', False):
                        total_imported += result.get('imported_count', 0)
                    
                    if result.get('errors'):
                        all_errors.extend(result.get('errors', []))
            
            return {
                'success': total_imported > 0,
                'total_imported': total_imported,
                'results': results,
                'errors': all_errors,
                'message': f"Import completed. Total items imported: {total_imported}"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Import all failed: {str(e)}"
            }
