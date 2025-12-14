from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, DecimalField, SelectField, TextAreaField, EmailField, HiddenField, FileField, DateField, TimeField
from wtforms.validators import DataRequired, Length, ValidationError, Email, EqualTo, NumberRange, Regexp, Optional, URL
from models import User
import re
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64), Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Sign In')
    user = None
    
    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if not user:
            raise ValidationError('Username does not exist')
        self.user = user
    
    def validate_password(self, password):
        if self.user and not self.user.check_password(password.data):
            raise ValidationError('Password is incorrect')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(min=3, max=64),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = EmailField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, max=128),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]', 
               message='Password must contain at least 8 characters, one uppercase, one lowercase, one digit, and one special character')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('cashier', 'Cashier')], default='cashier')
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user:
            raise ValidationError('Username already exists')
    
    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Email already registered')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, max=128),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]', 
               message='Password must contain at least 8 characters, one uppercase, one lowercase, one digit, and one special character')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')

class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[
        DataRequired(), 
        Length(min=2, max=100),
        Regexp(r'^[a-zA-Z0-9\s&-]+$', message='Category name can only contain letters, numbers, spaces, ampersand, and hyphens')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')

class MenuItemForm(FlaskForm):
    name = StringField('Item Name', validators=[
        DataRequired(), 
        Length(min=2, max=100),
        Regexp(r'^[a-zA-Z0-9\s&()-]+$', message='Item name can only contain letters, numbers, spaces, and basic punctuation')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    price = DecimalField('Price', validators=[
        DataRequired(), 
        NumberRange(min=0.01, max=99999.99, message='Price must be between 0.01 and 99999.99')
    ], places=2)
    stock_quantity = IntegerField('Stock Quantity', validators=[
        DataRequired(), 
        NumberRange(min=0, max=99999, message='Stock quantity must be between 0 and 99999')
    ])
    min_stock_level = IntegerField('Minimum Stock Level', validators=[
        DataRequired(), 
        NumberRange(min=0, max=1000, message='Minimum stock level must be between 0 and 1000')
    ])
    unit = StringField('Unit', validators=[
        DataRequired(), 
        Length(min=1, max=20),
        Regexp(r'^[a-zA-Z]+$', message='Unit can only contain letters')
    ])
    is_active = BooleanField('Active', default=True)
    image = FileField('Image', validators=[Optional()])
    submit = SubmitField('Save Menu Item')

class TableForm(FlaskForm):
    table_number = StringField('Table Number', validators=[
        DataRequired(), 
        Length(min=1, max=20),
        Regexp(r'^[A-Za-z0-9-]+$', message='Table number can only contain letters, numbers, and hyphens')
    ])
    capacity = IntegerField('Capacity', validators=[
        DataRequired(), 
        NumberRange(min=1, max=20, message='Capacity must be between 1 and 20')
    ])
    location = StringField('Location', validators=[
        DataRequired(), 
        Length(min=2, max=100),
        Regexp(r'^[a-zA-Z0-9\s-]+$', message='Location can only contain letters, numbers, spaces, and hyphens')
    ])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Table')

class OrderForm(FlaskForm):
    customer_name = StringField('Customer Name', validators=[
        Optional(), 
        Length(max=100),
        Regexp(r'^[a-zA-Z\s]+$', message='Customer name can only contain letters and spaces')
    ])
    customer_mobile = StringField('Customer Mobile', validators=[
        Optional(), 
        Length(min=10, max=15),
        Regexp(r'^[0-9+]+$', message='Mobile number can only contain numbers and +')
    ])
    order_type = SelectField('Order Type', choices=[
        ('Dine-in', 'Dine-in'),
        ('Takeaway', 'Takeaway'),
        ('Delivery', 'Delivery')
    ], default='Dine-in')
    table_id = SelectField('Table', coerce=int, validators=[Optional()])
    special_instructions = TextAreaField('Special Instructions', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Order')

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
        ('Wallet', 'Wallet'),
        ('Razorpay', 'Razorpay')
    ], validators=[DataRequired()])
    amount_paid = DecimalField('Amount Paid', validators=[
        DataRequired(), 
        NumberRange(min=0.01, max=999999.99, message='Amount must be between 0.01 and 999999.99')
    ], places=2)
    discount_amount = DecimalField('Discount Amount', validators=[
        Optional(), 
        NumberRange(min=0, max=99999.99, message='Discount must be between 0 and 99999.99')
    ], places=2, default=0)
    reference_number = StringField('Reference Number', validators=[
        Optional(), 
        Length(max=100),
        Regexp(r'^[A-Za-z0-9-]+$', message='Reference number can only contain letters, numbers, and hyphens')
    ])
    razorpay_payment_id = HiddenField('Razorpay Payment ID')
    razorpay_order_id = HiddenField('Razorpay Order ID')
    razorpay_signature = HiddenField('Razorpay Signature')
    submit = SubmitField('Process Payment')

class SettingsForm(FlaskForm):
    restaurant_name = StringField('Restaurant Name', validators=[
        DataRequired(), 
        Length(min=2, max=100)
    ])
    restaurant_address = TextAreaField('Address', validators=[
        DataRequired(), 
        Length(min=10, max=500)
    ])
    restaurant_phone = StringField('Phone', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp(r'^[0-9+()\s-]+$', message='Phone number format is invalid')
    ])
    restaurant_email = EmailField('Email', validators=[DataRequired(), Email()])
    gst_number = StringField('GST Number', validators=[
        Optional(), 
        Length(min=15, max=15),
        Regexp(r'^[0-9A-Z]{15}$', message='GST number must be 15 characters alphanumeric')
    ])
    currency_symbol = StringField('Currency Symbol', validators=[
        DataRequired(), 
        Length(min=1, max=5)
    ], default='₹')
    decimal_places = IntegerField('Decimal Places', validators=[
        DataRequired(), 
        NumberRange(min=0, max=4, message='Decimal places must be between 0 and 4')
    ], default=2)
    order_prefix = StringField('Order Prefix', validators=[
        DataRequired(), 
        Length(min=2, max=10),
        Regexp(r'^[A-Z]+$', message='Order prefix must be uppercase letters only')
    ], default='ORD')
    submit = SubmitField('Save Settings')

class EmailConfigForm(FlaskForm):
    smtp_server = StringField('SMTP Server', validators=[
        DataRequired(), 
        Length(min=3, max=100)
    ])
    smtp_port = IntegerField('SMTP Port', validators=[
        DataRequired(), 
        NumberRange(min=1, max=65535, message='Port must be between 1 and 65535')
    ])
    use_tls = BooleanField('Use TLS')
    use_ssl = BooleanField('Use SSL')
    username = StringField('Username', validators=[DataRequired(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(max=100)])
    from_email = EmailField('From Email', validators=[DataRequired(), Email()])
    from_name = StringField('From Name', validators=[DataRequired(), Length(max=100)])
    test_email = EmailField('Test Email', validators=[Optional(), Email()])
    submit = SubmitField('Save Configuration')

class ReportForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('daily', 'Daily Sales'),
        ('monthly', 'Monthly Sales'),
        ('gstr1', 'GSTR-1'),
        ('gstr3b', 'GSTR-3B'),
        ('itemwise', 'Item-wise Sales'),
        ('categorywise', 'Category-wise Sales')
    ], validators=[DataRequired()])
    date_from = DateField('From Date', validators=[DataRequired()])
    date_to = DateField('To Date', validators=[DataRequired()])
    format = SelectField('Export Format', choices=[
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('excel', 'Excel')
    ], default='pdf')
    submit = SubmitField('Generate Report')
    
    def validate_date_to(self, date_to):
        if date_to.data and self.date_from.data:
            if date_to.data < self.date_from.data:
                raise ValidationError('End date must be after start date')

class SearchForm(FlaskForm):
    search_query = StringField('Search', validators=[Optional(), Length(max=100)])
    search_type = SelectField('Search Type', choices=[
        ('all', 'All'),
        ('order_number', 'Order Number'),
        ('customer_name', 'Customer Name'),
        ('customer_mobile', 'Customer Mobile'),
        ('table_number', 'Table Number')
    ], default='all')
    date_filter = DateField('Date Filter', validators=[Optional()])
    status_filter = SelectField('Status Filter', choices=[
        ('', 'All Status'),
        ('New', 'New'),
        ('In Progress', 'In Progress'),
        ('Ready', 'Ready'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ], default='')
    submit = SubmitField('Search')

class InventoryAdjustmentForm(FlaskForm):
    adjustment_type = SelectField('Adjustment Type', choices=[
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('set', 'Set Stock Level')
    ], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[
        DataRequired(), 
        NumberRange(min=0, max=99999, message='Quantity must be between 0 and 99999')
    ])
    reason = TextAreaField('Reason', validators=[DataRequired(), Length(min=5, max=500)])
    submit = SubmitField('Adjust Stock')

class BackupForm(FlaskForm):
    backup_type = SelectField('Backup Type', choices=[
        ('database', 'Database Only'),
        ('full', 'Full Backup'),
        ('settings', 'Settings Only')
    ], validators=[DataRequired()])
    include_files = BooleanField('Include Uploaded Files')
    email_backup = BooleanField('Email Backup')
    submit = SubmitField('Create Backup')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(), 
        Length(min=2, max=50),
        Regexp(r'^[a-zA-Z\s]+$', message='First name can only contain letters and spaces')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(), 
        Length(min=2, max=50),
        Regexp(r'^[a-zA-Z\s]+$', message='Last name can only contain letters and spaces')
    ])
    email = EmailField('Email', validators=[Optional(), Email(), Length(max=120)])
    phone = StringField('Phone', validators=[
        Optional(), 
        Length(min=10, max=20),
        Regexp(r'^[0-9+()\s-]+$', message='Phone number format is invalid')
    ])
    submit = SubmitField('Update Profile')

class CSRFTokenForm(FlaskForm):
    """Form for CSRF token validation in AJAX requests"""
    csrf_token = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Submit')

# Custom validators
def validate_future_date(form, field):
    """Validate that date is not in the future"""
    if field.data and field.data > datetime.now().date():
        raise ValidationError('Date cannot be in the future')

def validate_business_hours(form, field):
    """Validate business hours"""
    if field.data:
        try:
            time_obj = datetime.strptime(field.data, '%H:%M').time()
            if not (0 <= time_obj.hour <= 23 and 0 <= time_obj.minute <= 59):
                raise ValidationError('Invalid time format')
        except ValueError:
            raise ValidationError('Invalid time format')

def validate_positive_decimal(form, field):
    """Validate that decimal field is positive"""
    if field.data is not None and field.data <= 0:
        raise ValidationError('Value must be positive')

# Form validation utilities
class FormValidator:
    """Utility class for form validation"""
    
    @staticmethod
    def validate_json_data(data, required_fields):
        """Validate JSON data with required fields"""
        if not isinstance(data, dict):
            return False, "Invalid JSON data"
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "Validation passed"
    
    @staticmethod
    def sanitize_string(value, max_length=None, allowed_chars=None):
        """Sanitize string input"""
        if not isinstance(value, str):
            return ""
        
        # Remove potentially harmful characters
        value = re.sub(r'[<>"\']', '', value)
        
        # Limit length
        if max_length:
            value = value[:max_length]
        
        # Filter allowed characters
        if allowed_chars:
            value = ''.join(char for char in value if char in allowed_chars)
        
        return value.strip()
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions=None, max_size_mb=None):
        """Validate file upload"""
        if not file:
            return True, "No file provided"
        
        # Check file extension
        if allowed_extensions:
            filename = file.filename.lower()
            if not any(filename.endswith(ext.lower()) for ext in allowed_extensions):
                return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check file size
        if max_size_mb:
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > max_size_mb * 1024 * 1024:
                return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
        
        return True, "File validation passed"

# Custom field validators
class CustomValidators:
    """Custom field validators for specific use cases"""
    
    @staticmethod
    def validate_order_number(form, field):
        """Validate order number format"""
        pattern = r'^[A-Z]{2,}\d{8,}$'
        if not re.match(pattern, field.data):
            raise ValidationError('Invalid order number format')
    
    @staticmethod
    def validate_phone_number(form, field):
        """Validate phone number format"""
        pattern = r'^[+]?[\d\s\-\(\)]{10,}$'
        if not re.match(pattern, field.data):
            raise ValidationError('Invalid phone number format')
    
    @staticmethod
    def validate_password_strength(form, field):
        """Validate password strength"""
        password = field.data
        
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')
    
    @staticmethod
    def validate_gst_number(form, field):
        """Validate GST number format"""
        if field.data:
            pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$'
            if not re.match(pattern, field.data):
                raise ValidationError('Invalid GST number format')