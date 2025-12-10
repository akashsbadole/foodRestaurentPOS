# PDF Exporter Documentation

## Overview

The PDF Exporter is a utility class for generating professional PDF invoices for orders in the POS system. It uses the ReportLab library to create well-formatted A4 PDF documents with restaurant branding, order details, item tables, and payment information.

## Features

- Professional A4 PDF invoice generation
- Restaurant branding with customizable information
- Support for both dine-in and takeaway orders
- Detailed item tables with proper formatting
- Order summary with tax, discount, and total calculations
- Payment information display
- Automatic file naming with order number and timestamp
- Batch export support for multiple orders
- Comprehensive error handling and logging
- Type hints and documentation

## Installation Requirements

The PDF Exporter requires the following library (already included in requirements.txt):

```
reportlab>=3.6.0
```

## Basic Usage

### Importing the Class

```python
from src.utils.pdf_exporter import PDFExporter
```

### Creating an Instance

```python
# With default restaurant information
exporter = PDFExporter()

# With custom restaurant information
restaurant_info = {
    'name': 'My Restaurant',
    'address': '123 Main Street, City, State 12345',
    'phone': '+91 98765 43210',
    'email': 'info@myrestaurant.com',
    'gst_number': 'GSTIN1234567890'
}
exporter = PDFExporter(restaurant_info)
```

### Exporting a Single Order

```python
# Prepare order data
order_data = {
    'order_number': 'ORD20231209001',
    'created_at': '2023-12-09 15:30:00',
    'order_type': 'Dine-in',
    'table_number': 'T05',
    'status': 'Completed',
    'subtotal': 450.00,
    'tax': 22.50,
    'tax_rate': 5,
    'discount': 20.00,
    'total': 452.50,
    'items': [
        ('Chicken Biryani', 2, 180.00, 360.00),
        ('Veg Pulao', 1, 120.00, 120.00),
        ('Cold Drink', 2, 25.00, 50.00)
    ],
    'payments': [
        ('Cash', 452.50, '2023-12-09 15:30:00')
    ]
}

# Export to PDF
success, result = exporter.export_order(order_data)

if success:
    print(f"PDF exported successfully: {result}")
else:
    print(f"Export failed: {result}")
```

### Batch Exporting Multiple Orders

```python
# Prepare multiple orders
orders_data = [
    {
        'order_number': 'ORD20231209002',
        'order_type': 'Takeaway',
        'customer_name': 'John Doe',
        'customer_mobile': '+91 98765 43210',
        # ... other order fields
    },
    {
        'order_number': 'ORD20231209003',
        'order_type': 'Dine-in',
        'table_number': 'T02',
        # ... other order fields
    }
]

# Export all orders
success, result = exporter.export_orders_batch(orders_data)

if success:
    print(f"Batch export successful: {result}")
else:
    print(f"Batch export failed: {result}")
```

## Order Data Structure

### Required Fields

- `order_number` (str): Unique order identifier
- `created_at` (str): Order creation timestamp
- `order_type` (str): Either 'Dine-in' or 'Takeaway'
- `status` (str): Order status (e.g., 'Completed', 'Pending')
- `subtotal` (float): Subtotal amount
- `tax` (float): Tax amount
- `total` (float): Total amount
- `items` (list): List of order items
- `payments` (list): List of payment records

### Optional Fields

- `table_number` (str): Table number for dine-in orders
- `customer_name` (str): Customer name for takeaway orders
- `customer_mobile` (str): Customer mobile for takeaway orders
- `tax_rate` (float): Tax rate percentage (default: 5)
- `discount` (float): Discount amount (default: 0)

### Items Format

Items can be provided as tuples or dictionaries:

```python
# Tuple format
items = [
    ('Item Name', quantity, price, total),
    # Example: ('Chicken Biryani', 2, 180.00, 360.00)
]

# Dictionary format
items = [
    {
        'name': 'Item Name',
        'quantity': 2,
        'price': 180.00,
        'total': 360.00
    }
]
```

### Payments Format

Payments can be provided as tuples or dictionaries:

```python
# Tuple format
payments = [
    ('Payment Mode', amount, timestamp),
    # Example: ('Cash', 452.50, '2023-12-09 15:30:00')
]

# Dictionary format
payments = [
    {
        'payment_mode': 'Cash',
        'amount': 452.50,
        'created_at': '2023-12-09 15:30:00'
    }
]
```

## File Naming Convention

PDF files are automatically named using the following pattern:

```
Order_{order_number}_{timestamp}.pdf
```

Example: `Order_ORD20231209001_20231209_153000.pdf`

## Export Directory

PDF files are saved to: `./exports/orders/pdf/`

The directory is automatically created if it doesn't exist.

## Integration with Existing POS System

### Using with Order Model

```python
from models.order import Order
from models.database import Database
from utils.pdf_exporter import PDFExporter

# Get order from database
db = Database('restaurant_pos.db')
order_model = Order(db)
order_details = order_model.get_details(order_id)

# Extract and format data for PDF export
order = order_details['order']
items = order_details['items']
payments = order_details['payments']

# Create PDF data structure
pdf_order_data = {
    'order_number': order[0],
    'created_at': order[9],
    'order_type': order[4],
    'status': order[9],
    'subtotal': float(order[5]),
    'tax': float(order[6]),
    'discount': float(order[7]),
    'total': float(order[8]),
    'items': items,
    'payments': payments
}

# Add type-specific information
if order[4] == 'Dine-in':
    # Get table number
    table_id = order[1]
    if table_id:
        db.execute_query("SELECT table_number FROM tables WHERE id = ?", (table_id,))
        table_result = db.fetch_one()
        if table_result:
            pdf_order_data['table_number'] = table_result[0]
elif order[4] == 'Takeaway':
    pdf_order_data['customer_name'] = order[2]
    pdf_order_data['customer_mobile'] = order[3]

# Export to PDF
exporter = PDFExporter(restaurant_info)
success, result = exporter.export_order(pdf_order_data)
```

## Error Handling

The PDF Exporter includes comprehensive error handling:

```python
success, result = exporter.export_order(order_data)

if success:
    # Success: result contains the file path
    print(f"PDF exported to: {result}")
else:
    # Error: result contains the error message
    print(f"Export failed: {result}")
```

## Logging

The PDF Exporter uses Python's logging module for error tracking:

```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Exporter will automatically log errors and success messages
exporter = PDFExporter()
```

## Customization Options

### Restaurant Information

Update restaurant information at runtime:

```python
exporter.set_restaurant_info({
    'name': 'New Restaurant Name',
    'address': 'New Address',
    'phone': 'New Phone',
    'email': 'New Email',
    'gst_number': 'New GST Number'
})
```

### PDF Styling

The PDF Exporter uses ReportLab's styling system. Custom styles can be modified by editing the `_setup_custom_styles` method in the class.

## Testing

Run the test script to verify functionality:

```bash
python test_pdf_exporter.py
```

The test script includes:
- Directory structure verification
- Single order export
- Takeaway order export
- Batch export testing

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure ReportLab is installed (`pip install reportlab`)
2. **Permission Error**: Check write permissions for the export directory
3. **File Already Exists**: The exporter uses timestamps to avoid conflicts
4. **Missing Data**: Verify all required fields are present in order data

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

exporter = PDFExporter()
```

## Performance Considerations

- Batch export processes orders sequentially to avoid memory issues
- PDF generation is CPU-intensive; consider background processing for large batches
- File I/O operations are buffered for better performance

## Future Enhancements

Potential future improvements:
- Digital signature support
- Multi-language support
- Custom templates
- Email integration
- Cloud storage integration
- Barcode/QR code generation