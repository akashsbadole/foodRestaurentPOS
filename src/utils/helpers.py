import hashlib
import csv
from datetime import datetime
from io import StringIO
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def hash_password(password):
    """Hash password using MD5"""
    return hashlib.md5(password.encode()).hexdigest()

def format_currency(amount, currency_symbol="₹"):
    """Format amount as currency"""
    # Use ASCII-compatible currency symbol for console output
    try:
        # Test if the symbol can be encoded
        currency_symbol.encode('cp1252')
        return f"{currency_symbol}{amount:.2f}"
    except (UnicodeEncodeError, AttributeError):
        # Fallback to Rs. if currency symbol can't be encoded
        return f"Rs.{amount:.2f}"

def format_datetime(date_string, input_format='%Y-%m-%d %H:%M:%S', output_format='%d-%m-%Y %H:%M'):
    """Format datetime string"""
    try:
        date_obj = datetime.strptime(date_string, input_format)
        return date_obj.strftime(output_format)
    except ValueError:
        return date_string

def export_to_csv(data, headers, file_path):
    """Export data to CSV file"""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(data)
        return True
    except Exception as e:
        print(f"Error exporting to CSV: {e}")
        return False

def generate_timestamped_filename(base_name, extension="csv"):
    """Generate filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"

def export_report_to_csv(report_tree, report_type, file_path=None):
    """Enhanced CSV export for reports with automatic naming"""
    try:
        if not file_path:
            # Generate automatic filename
            base_name = f"{report_type.lower().replace(' ', '_')}_report"
            file_path = generate_timestamped_filename(base_name)
        
        # Get report data
        headers = [report_tree.heading(col)['text'] for col in report_tree['columns']]
        data = []
        for child in report_tree.get_children():
            data.append(report_tree.item(child)['values'])
        
        # Write to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header with metadata
            csvfile.write(f"# Report: {report_type}\n")
            csvfile.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            csvfile.write(f"# Total Records: {len(data)}\n\n")
            
            # Write data
            writer.writerow(headers)
            writer.writerows(data)
            
            # Write summary
            csvfile.write(f"\n# End of Report - {len(data)} records exported")
        
        return True, file_path
    except Exception as e:
        print(f"Error exporting report to CSV: {e}")
        return False, str(e)

def export_to_excel_format(data, headers, file_path):
    """Export data to Excel-compatible CSV format"""
    try:
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  # UTF-8 BOM for Excel
            writer = csv.writer(csvfile)
            
            # Add metadata
            writer.writerow(['Restaurant POS Report'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow([])
            
            # Write headers
            writer.writerow(headers)
            
            # Write data
            writer.writerows(data)
            
            # Add summary
            writer.writerow([])
            writer.writerow(['Total Records:', len(data)])
            
        return True
    except Exception as e:
        print(f"Error exporting to Excel format: {e}")
        return False

def create_export_options_dialog(parent, report_type="Report"):
    """Create export options dialog"""
    from tkinter import filedialog, messagebox
    
    dialog = tk.Toplevel(parent)
    dialog.title(f"Export {report_type}")
    dialog.geometry("400x300")
    dialog.resizable(False, False)
    
    # Make dialog modal
    dialog.transient(parent)
    dialog.grab_set()
    
    main_frame = ttk.Frame(dialog, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # File format selection
    format_frame = ttk.LabelFrame(main_frame, text="Export Format", padding=10)
    format_frame.pack(fill=tk.X, pady=(0, 10))
    
    format_var = tk.StringVar(value="CSV")
    ttk.Radiobutton(format_frame, text="CSV (Standard)", variable=format_var, 
                   value="CSV").pack(anchor=tk.W)
    ttk.Radiobutton(format_frame, text="CSV (Excel Compatible)", variable=format_var, 
                   value="Excel").pack(anchor=tk.W)
    
    # File name options
    name_frame = ttk.LabelFrame(main_frame, text="File Name", padding=10)
    name_frame.pack(fill=tk.X, pady=(0, 10))
    
    auto_name_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(name_frame, text="Auto-generate filename with timestamp", 
                   variable=auto_name_var).pack(anchor=tk.W)
    
    custom_name_var = tk.StringVar()
    ttk.Label(name_frame, text="Custom name:").pack(anchor=tk.W, pady=(10, 0))
    ttk.Entry(name_frame, textvariable=custom_name_var, width=40).pack(fill=tk.X)
    
    # Include metadata option
    meta_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(main_frame, text="Include metadata and summary", 
                   variable=meta_var).pack(anchor=tk.W, pady=(10, 0))
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(20, 0))
    
    def do_export():
        file_format = format_var.get()
        auto_name = auto_name_var.get()
        custom_name = custom_name_var.get().strip()
        include_meta = meta_var.get()
        
        # Determine file path
        if auto_name or not custom_name:
            base_name = report_type.lower().replace(' ', '_')
            filename = generate_timestamped_filename(base_name, "csv")
        else:
            filename = custom_name if custom_name.endswith('.csv') else f"{custom_name}.csv"
        
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if not file_path:
            return
        
        # Export with appropriate format
        success = False
        if include_meta:
            success, _ = export_report_to_csv(None, report_type, file_path)
        else:
            if file_format == "Excel":
                success = export_to_excel_format([], [], file_path)
            else:
                success = export_to_csv([], [], file_path)
        
        if success:
            messagebox.showinfo("Success", f"{report_type} exported to {file_path}")
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to export report")
    
    ttk.Button(button_frame, text="Export", command=do_export).pack(side=tk.RIGHT, padx=(0, 10))
    ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)
    
    return dialog

def generate_order_number():
    """Generate unique order number"""
    return "ORD" + datetime.now().strftime("%Y%m%d%H%M%S")

def generate_bill_content(restaurant_name, restaurant_address, order_details, items, subtotal, tax, discount, total):
    """Generate bill content as string"""
    bill_content = f"""
{restaurant_name}
{restaurant_address}
{'='*40}
BILL
{'='*40}
Order No: {order_details['order_number']}
Date: {order_details['created_at']}
Order Type: {order_details['order_type']}
"""
    
    if order_details['order_type'] == "Dine-in" and order_details.get('table_number'):
        bill_content += f"Table: {order_details['table_number']}\n"
    elif order_details['order_type'] == "Takeaway" and order_details.get('customer_name'):
        bill_content += f"Customer: {order_details['customer_name']}\n"
        if order_details.get('customer_mobile'):
            bill_content += f"Mobile: {order_details['customer_mobile']}\n"
    
    bill_content += f"""
{'='*40}
{'Item':<20} {'Qty':<5} {'Price':<10} {'Total':<10}
{'-'*50}
"""
    
    for item in items:
        name, quantity, price, item_total = item
        bill_content += f"{name:<20} {quantity:<5} ₹{price:<9.2f} ₹{item_total:<9.2f}\n"
    
    bill_content += f"""
{'-'*50}
Subtotal: ₹{subtotal:.2f}
Tax (5%): ₹{tax:.2f}
Discount: ₹{discount:.2f}
{'='*50}
Total: ₹{total:.2f}
{'='*50}
Thank you for dining with us!
"""
    
    return bill_content

def generate_kot_content(order_number, item_name, quantity, created_at):
    """Generate KOT content as string"""
    kot_content = f"""
{'='*30}
KITCHEN ORDER TICKET
{'='*30}
Order No: {order_number}
Time: {created_at}
{'-'*30}
Item: {item_name}
Quantity: {quantity}
{'='*30}
"""
    return kot_content

def validate_positive_number(value, field_name="Value"):
    """Validate that value is a positive number"""
    try:
        num = float(value)
        if num < 0:
            raise ValueError(f"{field_name} must be positive")
        return num
    except ValueError as e:
        raise ValueError(f"{field_name} must be a valid positive number")

def validate_positive_integer(value, field_name="Value"):
    """Validate that value is a positive integer"""
    try:
        num = int(value)
        if num < 0:
            raise ValueError(f"{field_name} must be positive")
        return num
    except ValueError as e:
        raise ValueError(f"{field_name} must be a valid positive integer")
