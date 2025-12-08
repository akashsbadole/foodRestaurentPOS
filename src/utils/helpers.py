import hashlib
import csv
from datetime import datetime
from io import StringIO

def hash_password(password):
    """Hash password using MD5"""
    return hashlib.md5(password.encode()).hexdigest()

def format_currency(amount, currency_symbol="₹"):
    """Format amount as currency"""
    return f"{currency_symbol}{amount:.2f}"

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
