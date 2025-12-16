"""
Dynamic Form System with Conditional Fields
Creates adaptive forms based on retail type and enabled features
"""

from typing import Dict, List, Optional, Any, Set, Union
from flask import request, current_app
from werkzeug.datastructures import MultiDict
from utils.feature_flag_manager import feature_manager
from utils.retail_type_manager import get_retail_type_manager


class DynamicFormField:
    """
    Represents a dynamic form field with conditional rendering
    """
    
    def __init__(self, field_id: str, field_type: str, **kwargs):
        self.field_id = field_id
        self.field_type = field_type
        self.label = kwargs.get('label', field_id.title())
        self.placeholder = kwargs.get('placeholder', '')
        self.required = kwargs.get('required', False)
        self.default_value = kwargs.get('default', '')
        self.options = kwargs.get('options', [])
        self.validation_rules = kwargs.get('validation', {})
        self.required_features = kwargs.get('required_features', [])
        self.excluded_features = kwargs.get('excluded_features', [])
        self.retail_types = kwargs.get('retail_types', [])
        self.depends_on = kwargs.get('depends_on', {})
        self.affects = kwargs.get('affects', [])
        self.css_classes = kwargs.get('css_classes', [])
        self.attributes = kwargs.get('attributes', {})
        self.help_text = kwargs.get('help_text', '')
        self.group = kwargs.get('group', 'default')
        self.order = kwargs.get('order', 100)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert field to dictionary"""
        return {
            'id': self.field_id,
            'type': self.field_type,
            'label': self.label,
            'placeholder': self.placeholder,
            'required': self.required,
            'default': self.default_value,
            'options': self.options,
            'validation': self.validation_rules,
            'required_features': self.required_features,
            'excluded_features': self.excluded_features,
            'retail_types': self.retail_types,
            'depends_on': self.depends_on,
            'affects': self.affects,
            'css_classes': self.css_classes,
            'attributes': self.attributes,
            'help_text': self.help_text,
            'group': self.group,
            'order': self.order
        }


class DynamicForm:
    """
    Represents a dynamic form with conditional fields
    """
    
    def __init__(self, form_id: str, **kwargs):
        self.form_id = form_id
        self.title = kwargs.get('title', form_id.title())
        self.description = kwargs.get('description', '')
        self.action = kwargs.get('action', '')
        self.method = kwargs.get('method', 'POST')
        self.css_classes = kwargs.get('css_classes', ['dynamic-form'])
        self.attributes = kwargs.get('attributes', {})
        self.retail_types = kwargs.get('retail_types', [])
        self.required_features = kwargs.get('required_features', [])
        self.excluded_features = kwargs.get('excluded_features', [])
        self.fields = {}
        self.field_groups = {}
        self.validation_rules = kwargs.get('validation', {})
        self.submit_text = kwargs.get('submit_text', 'Submit')
        self.reset_text = kwargs.get('reset_text', 'Reset')
        self.show_reset = kwargs.get('show_reset', True)
    
    def add_field(self, field: DynamicFormField):
        """Add a field to the form"""
        self.fields[field.field_id] = field
        
        # Add to field group
        if field.group not in self.field_groups:
            self.field_groups[field.group] = []
        self.field_groups[field.group].append(field)
    
    def get_field(self, field_id: str) -> Optional[DynamicFormField]:
        """Get field by ID"""
        return self.fields.get(field_id)
    
    def remove_field(self, field_id: str):
        """Remove field from form"""
        if field_id in self.fields:
            field = self.fields[field_id]
            del self.fields[field_id]
            
            # Remove from field groups
            if field.group in self.field_groups:
                self.field_groups[field.group] = [
                    f for f in self.field_groups[field.group] 
                    if f.field_id != field_id
                ]
    
    def to_dict(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Convert form to dictionary with filtered fields"""
        if tenant_id is None:
            tenant_id = self._get_tenant_id()
        
        retail_type = feature_manager.get_tenant_retail_type(tenant_id) if tenant_id else 'restaurant'
        enabled_features = feature_manager.get_enabled_features(tenant_id) if tenant_id else set()
        
        # Filter fields based on conditions
        filtered_fields = self._filter_fields(retail_type, enabled_features)
        
        # Organize fields by groups
        grouped_fields = {}
        for field in filtered_fields:
            if field.group not in grouped_fields:
                grouped_fields[field.group] = []
            grouped_fields[field.group].append(field)
        
        # Sort fields within groups
        for group in grouped_fields:
            grouped_fields[group].sort(key=lambda x: x.order)
        
        return {
            'id': self.form_id,
            'title': self.title,
            'description': self.description,
            'action': self.action,
            'method': self.method,
            'css_classes': self.css_classes,
            'attributes': self.attributes,
            'retail_type': retail_type,
            'enabled_features': list(enabled_features),
            'field_groups': grouped_fields,
            'validation_rules': self.validation_rules,
            'submit_text': self.submit_text,
            'reset_text': self.reset_text,
            'show_reset': self.show_reset
        }
    
    def _get_tenant_id(self):
        """Get current tenant ID"""
        try:
            from utils.tenant_query_manager import get_current_tenant_id
            return get_current_tenant_id()
        except:
            return None
    
    def _filter_fields(self, retail_type: str, enabled_features: Set[str]) -> List[DynamicFormField]:
        """Filter fields based on retail type and features"""
        filtered_fields = []
        
        for field in self.fields.values():
            # Check retail type compatibility
            if field.retail_types and retail_type not in field.retail_types:
                continue
            
            # Check required features
            if field.required_features:
                if not all(feature in enabled_features for feature in field.required_features):
                    continue
            
            # Check excluded features
            if field.excluded_features:
                if any(feature in enabled_features for feature in field.excluded_features):
                    continue
            
            filtered_fields.append(field)
        
        return filtered_fields


class DynamicFormManager:
    """
    Manages dynamic forms with conditional rendering
    """
    
    def __init__(self, feature_manager=None):
        self.feature_manager = feature_manager
        self.forms = {}
        self.field_types = {}
        self.validation_rules = {}
        self._initialized = False
    
    def initialize(self):
        """Initialize form manager"""
        if self._initialized:
            return
        
        self._load_field_types()
        self._load_validation_rules()
        self._load_default_forms()
        self._initialized = True
    
    def _load_field_types(self):
        """Load available field types"""
        self.field_types = {
            'text': {
                'template': 'forms/fields/text.html',
                'default_validation': {'max_length': 255}
            },
            'email': {
                'template': 'forms/fields/email.html',
                'default_validation': {'max_length': 255, 'email': True}
            },
            'password': {
                'template': 'forms/fields/password.html',
                'default_validation': {'min_length': 8}
            },
            'number': {
                'template': 'forms/fields/number.html',
                'default_validation': {'numeric': True}
            },
            'tel': {
                'template': 'forms/fields/tel.html',
                'default_validation': {'phone': True}
            },
            'date': {
                'template': 'forms/fields/date.html',
                'default_validation': {'date': True}
            },
            'datetime': {
                'template': 'forms/fields/datetime.html',
                'default_validation': {'datetime': True}
            },
            'time': {
                'template': 'forms/fields/time.html',
                'default_validation': {'time': True}
            },
            'select': {
                'template': 'forms/fields/select.html',
                'default_validation': {}
            },
            'multiselect': {
                'template': 'forms/fields/multiselect.html',
                'default_validation': {}
            },
            'radio': {
                'template': 'forms/fields/radio.html',
                'default_validation': {}
            },
            'checkbox': {
                'template': 'forms/fields/checkbox.html',
                'default_validation': {}
            },
            'textarea': {
                'template': 'forms/fields/textarea.html',
                'default_validation': {'max_length': 1000}
            },
            'file': {
                'template': 'forms/fields/file.html',
                'default_validation': {'file': True}
            },
            'image': {
                'template': 'forms/fields/image.html',
                'default_validation': {'image': True}
            },
            'range': {
                'template': 'forms/fields/range.html',
                'default_validation': {'numeric': True}
            },
            'color': {
                'template': 'forms/fields/color.html',
                'default_validation': {'color': True}
            },
            'hidden': {
                'template': 'forms/fields/hidden.html',
                'default_validation': {}
            },
            'barcode_scanner': {
                'template': 'forms/fields/barcode_scanner.html',
                'default_validation': {},
                'required_features': ['FEATURE_BARCODE_SCANNING']
            },
            'weighing_scale': {
                'template': 'forms/fields/weighing_scale.html',
                'default_validation': {'numeric': True},
                'required_features': ['FEATURE_WEIGHING_SCALE']
            },
            'product_search': {
                'template': 'forms/fields/product_search.html',
                'default_validation': {},
                'required_features': ['FEATURE_PRODUCT_CATALOG']
            },
            'customer_search': {
                'template': 'forms/fields/customer_search.html',
                'default_validation': {},
                'required_features': ['FEATURE_CUSTOMER_MANAGEMENT']
            },
            'table_selector': {
                'template': 'forms/fields/table_selector.html',
                'default_validation': {},
                'required_features': ['FEATURE_TABLE_MANAGEMENT'],
                'retail_types': ['restaurant']
            },
            'size_variant': {
                'template': 'forms/fields/size_variant.html',
                'default_validation': {},
                'required_features': ['FEATURE_SIZE_VARIANTS'],
                'retail_types': ['apparel']
            },
            'color_variant': {
                'template': 'forms/fields/color_variant.html',
                'default_validation': {},
                'required_features': ['FEATURE_COLOR_VARIANTS'],
                'retail_types': ['apparel']
            }
        }
    
    def _load_validation_rules(self):
        """Load validation rules"""
        self.validation_rules = {
            'required': {
                'message': 'This field is required',
                'rule': 'value != ""'
            },
            'email': {
                'message': 'Please enter a valid email address',
                'rule': 'email_regex.test(value)'
            },
            'numeric': {
                'message': 'Please enter a valid number',
                'rule': '!isNaN(value) && value.trim() !== ""'
            },
            'phone': {
                'message': 'Please enter a valid phone number',
                'rule': 'phone_regex.test(value)'
            },
            'min_length': {
                'message': 'Minimum length is {min} characters',
                'rule': 'value.length >= min'
            },
            'max_length': {
                'message': 'Maximum length is {max} characters',
                'rule': 'value.length <= max'
            },
            'min_value': {
                'message': 'Minimum value is {min}',
                'rule': 'parseFloat(value) >= min'
            },
            'max_value': {
                'message': 'Maximum value is {max}',
                'rule': 'parseFloat(value) <= max'
            },
            'date': {
                'message': 'Please enter a valid date',
                'rule': '!isNaN(Date.parse(value))'
            },
            'datetime': {
                'message': 'Please enter a valid date and time',
                'rule': '!isNaN(Date.parse(value))'
            },
            'time': {
                'message': 'Please enter a valid time',
                'rule': 'time_regex.test(value)'
            },
            'file': {
                'message': 'Please select a valid file',
                'rule': 'value instanceof File'
            },
            'image': {
                'message': 'Please select a valid image file',
                'rule': 'value instanceof File && image_types.includes(value.type)'
            },
            'color': {
                'message': 'Please enter a valid color',
                'rule': 'color_regex.test(value)'
            }
        }
    
    def _load_default_forms(self):
        """Load default form configurations"""
        # Order form
        order_form = DynamicForm(
            'order_form',
            title='Create Order',
            required_features=['FEATURE_SALES_PROCESSING']
        )
        
        order_form.add_field(DynamicFormField(
            'customer_name',
            'text',
            label='Customer Name',
            placeholder='Enter customer name',
            required_features=['FEATURE_CUSTOMER_MANAGEMENT']
        ))
        
        order_form.add_field(DynamicFormField(
            'customer_phone',
            'tel',
            label='Phone Number',
            placeholder='Enter phone number',
            required_features=['FEATURE_CUSTOMER_MANAGEMENT']
        ))
        
        order_form.add_field(DynamicFormField(
            'table_id',
            'table_selector',
            label='Table',
            required=True,
            retail_types=['restaurant'],
            required_features=['FEATURE_TABLE_MANAGEMENT']
        ))
        
        order_form.add_field(DynamicFormField(
            'order_type',
            'select',
            label='Order Type',
            required=True,
            options=[
                {'value': 'dine_in', 'label': 'Dine In'},
                {'value': 'takeaway', 'label': 'Takeaway'},
                {'value': 'delivery', 'label': 'Delivery'}
            ],
            retail_types=['restaurant']
        ))
        
        order_form.add_field(DynamicFormField(
            'barcode',
            'barcode_scanner',
            label='Product Barcode',
            placeholder='Scan or enter barcode',
            required_features=['FEATURE_BARCODE_SCANNING']
        ))
        
        order_form.add_field(DynamicFormField(
            'weight',
            'weighing_scale',
            label='Weight (kg)',
            placeholder='Enter weight',
            required_features=['FEATURE_WEIGHING_SCALE'],
            retail_types=['grocery']
        ))
        
        order_form.add_field(DynamicFormField(
            'notes',
            'textarea',
            label='Order Notes',
            placeholder='Enter any special instructions'
        ))
        
        self.forms['order_form'] = order_form
        
        # Product form
        product_form = DynamicForm(
            'product_form',
            title='Product Management',
            required_features=['FEATURE_PRODUCT_CATALOG']
        )
        
        product_form.add_field(DynamicFormField(
            'name',
            'text',
            label='Product Name',
            placeholder='Enter product name',
            required=True
        ))
        
        product_form.add_field(DynamicFormField(
            'category',
            'select',
            label='Category',
            required=True,
            options=[
                {'value': 'food', 'label': 'Food'},
                {'value': 'beverage', 'label': 'Beverage'},
                {'value': 'apparel', 'label': 'Apparel'},
                {'value': 'grocery', 'label': 'Grocery'}
            ]
        ))
        
        product_form.add_field(DynamicFormField(
            'price',
            'number',
            label='Price',
            placeholder='0.00',
            required=True,
            validation_rules={'min_value': 0}
        ))
        
        product_form.add_field(DynamicFormField(
            'size',
            'size_variant',
            label='Size',
            required_features=['FEATURE_SIZE_VARIANTS'],
            retail_types=['apparel']
        ))
        
        product_form.add_field(DynamicFormField(
            'color',
            'color_variant',
            label='Color',
            required_features=['FEATURE_COLOR_VARIANTS'],
            retail_types=['apparel']
        ))
        
        product_form.add_field(DynamicFormField(
            'barcode',
            'text',
            label='Barcode',
            placeholder='Enter barcode',
            required_features=['FEATURE_BARCODE_SCANNING']
        ))
        
        product_form.add_field(DynamicFormField(
            'expiry_date',
            'date',
            label='Expiry Date',
            required_features=['FEATURE_EXPIRY_TRACKING'],
            retail_types=['grocery']
        ))
        
        product_form.add_field(DynamicFormField(
            'image',
            'image',
            label='Product Image'
        ))
        
        self.forms['product_form'] = product_form
        
        # Customer form
        customer_form = DynamicForm(
            'customer_form',
            title='Customer Management',
            required_features=['FEATURE_CUSTOMER_MANAGEMENT']
        )
        
        customer_form.add_field(DynamicFormField(
            'name',
            'text',
            label='Full Name',
            placeholder='Enter full name',
            required=True
        ))
        
        customer_form.add_field(DynamicFormField(
            'email',
            'email',
            label='Email Address',
            placeholder='Enter email address'
        ))
        
        customer_form.add_field(DynamicFormField(
            'phone',
            'tel',
            label='Phone Number',
            placeholder='Enter phone number',
            required=True
        ))
        
        customer_form.add_field(DynamicFormField(
            'address',
            'textarea',
            label='Address',
            placeholder='Enter address'
        ))
        
        customer_form.add_field(DynamicFormField(
            'loyalty_member',
            'checkbox',
            label='Loyalty Program Member',
            required_features=['FEATURE_LOYALTY_PROGRAM']
        ))
        
        self.forms['customer_form'] = customer_form
    
    def get_form(self, form_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get form configuration"""
        if not self._initialized:
            self.initialize()
        
        if form_id in self.forms:
            return self.forms[form_id].to_dict(tenant_id)
        
        return None
    
    def create_form(self, form_id: str, **kwargs) -> DynamicForm:
        """Create a new dynamic form"""
        form = DynamicForm(form_id, **kwargs)
        self.forms[form_id] = form
        return form
    
    def register_form(self, form: DynamicForm):
        """Register a form"""
        self.forms[form.form_id] = form
    
    def validate_form_data(self, form_id: str, form_data: MultiDict, 
                         tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate form data"""
        if not self._initialized:
            self.initialize()
        
        form_config = self.get_form(form_id, tenant_id)
        if not form_config:
            return {'valid': False, 'errors': {'form': 'Form not found'}}
        
        errors = {}
        valid = True
        
        # Validate each field
        for group_name, fields in form_config['field_groups'].items():
            for field in fields:
                field_value = form_data.get(field.field_id, '')
                field_errors = self._validate_field(field, field_value)
                
                if field_errors:
                    errors[field.field_id] = field_errors
                    valid = False
        
        return {
            'valid': valid,
            'errors': errors,
            'cleaned_data': self._clean_form_data(form_config, form_data)
        }
    
    def _validate_field(self, field: DynamicFormField, value: str) -> List[str]:
        """Validate a single field"""
        errors = []
        
        # Check if required
        if field.required and not value.strip():
            errors.append('This field is required')
        
        # Skip validation if field is empty and not required
        if not value.strip() and not field.required:
            return errors
        
        # Apply validation rules
        for rule_name, rule_config in field.validation_rules.items():
            if rule_name in self.validation_rules:
                rule = self.validation_rules[rule_name]
                
                # Simple validation (in real implementation, this would be more sophisticated)
                if rule_name == 'min_length' and len(value) < rule_config:
                    errors.append(f"Minimum length is {rule_config} characters")
                elif rule_name == 'max_length' and len(value) > rule_config:
                    errors.append(f"Maximum length is {rule_config} characters")
                elif rule_name == 'min_value' and float(value) < rule_config:
                    errors.append(f"Minimum value is {rule_config}")
                elif rule_name == 'max_value' and float(value) > rule_config:
                    errors.append(f"Maximum value is {rule_config}")
        
        return errors
    
    def _clean_form_data(self, form_config: Dict[str, Any], form_data: MultiDict) -> Dict[str, Any]:
        """Clean and process form data"""
        cleaned_data = {}
        
        for group_name, fields in form_config['field_groups'].items():
            for field in fields:
                field_value = form_data.get(field.field_id, '')
                
                # Apply field-specific cleaning
                if field.field_type == 'number':
                    try:
                        cleaned_data[field.field_id] = float(field_value)
                    except ValueError:
                        cleaned_data[field.field_id] = 0.0
                elif field.field_type == 'checkbox':
                    cleaned_data[field.field_id] = bool(field_value)
                elif field.field_type == 'multiselect':
                    cleaned_data[field.field_id] = form_data.getlist(field.field_id)
                else:
                    cleaned_data[field.field_id] = field_value.strip()
        
        return cleaned_data
    
    def get_field_type_config(self, field_type: str) -> Dict[str, Any]:
        """Get field type configuration"""
        return self.field_types.get(field_type, {})
    
    def register_field_type(self, field_type: str, config: Dict[str, Any]):
        """Register a new field type"""
        self.field_types[field_type] = config


# Global form manager instance
form_manager = None


def get_form_manager(feature_manager=None) -> DynamicFormManager:
    """Get or create global form manager instance"""
    global form_manager
    if form_manager is None:
        form_manager = DynamicFormManager(feature_manager)
    return form_manager