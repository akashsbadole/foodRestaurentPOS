from datetime import datetime
from decimal import Decimal
from . import db
from .feature_aware_model import FeatureAwareModel

class TaxJurisdiction(FeatureAwareModel):
    """Tax jurisdiction model for different tax regions"""
    __tablename__ = 'tax_jurisdictions'
    
    # Feature requirements
    required_features = ['FEATURE_GST_COMPLIANCE', 'FEATURE_VAT_SUPPORT']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    country = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # Tax system type
    tax_system = db.Column(db.String(20), default='GST')  # GST, VAT, Sales Tax, None
    
    # Registration numbers
    gstin = db.Column(db.String(20), nullable=True)  # GST Identification Number
    vat_number = db.Column(db.String(30), nullable=True)
    tax_id = db.Column(db.String(30), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tax_rates = db.relationship('TaxRate', backref='jurisdiction', lazy=True)
    
    def __init__(self, name, code, country, tax_system='GST', state=None,
                 city=None, gstin=None, vat_number=None, tax_id=None,
                 is_active=True, is_default=False, tenant_id=None):
        self.name = name
        self.code = code
        self.country = country
        self.tax_system = tax_system
        self.state = state
        self.city = city
        self.gstin = gstin
        self.vat_number = vat_number
        self.tax_id = tax_id
        self.is_active = is_active
        self.is_default = is_default
        self.tenant_id = tenant_id
    
    def to_dict(self):
        """Convert tax jurisdiction to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'country': self.country,
            'state': self.state,
            'city': self.city,
            'tax_system': self.tax_system,
            'gstin': self.gstin,
            'vat_number': self.vat_number,
            'tax_id': self.tax_id,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_default(tenant_id=None):
        """Get default tax jurisdiction"""
        query = TaxJurisdiction.query.filter_by(is_default=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_active(tenant_id=None):
        """Get all active tax jurisdictions"""
        query = TaxJurisdiction.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(TaxJurisdiction.name).all()
    
    def __repr__(self):
        return f'<TaxJurisdiction {self.name} ({self.code})>'


class TaxRate(FeatureAwareModel):
    """Tax rate model for different tax types"""
    __tablename__ = 'tax_rates'
    
    # Feature requirements
    required_features = ['FEATURE_GST_COMPLIANCE', 'FEATURE_VAT_SUPPORT']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Tax type and classification
    tax_type = db.Column(db.String(20), nullable=False)  # CGST, SGST, IGST, VAT, Service Tax, etc.
    tax_category = db.Column(db.String(50), nullable=True)  # Goods, Services, Both
    
    # Tax rates
    rate_percentage = db.Column(db.Numeric(5, 2), nullable=False)
    cess_rate = db.Column(db.Numeric(5, 2), default=0)  # Additional cess
    surcharge_rate = db.Column(db.Numeric(5, 2), default=0)  # Surcharge
    
    # Applicability
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('tax_jurisdictions.id'), nullable=True)
    hsn_code_from = db.Column(db.String(10), nullable=True)  # HSN code range
    hsn_code_to = db.Column(db.String(10), nullable=True)
    sac_code_from = db.Column(db.String(10), nullable=True)  # SAC code range
    sac_code_to = db.Column(db.String(10), nullable=True)
    
    # Effective dates
    effective_from = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    effective_to = db.Column(db.Date, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='tax_rates')
    
    def __init__(self, name, code, tax_type, rate_percentage, tax_category=None,
                 cess_rate=0, surcharge_rate=0, jurisdiction_id=None,
                 hsn_code_from=None, hsn_code_to=None, sac_code_from=None,
                 sac_code_to=None, effective_from=None, effective_to=None,
                 is_active=True, is_default=False, tenant_id=None):
        self.name = name
        self.code = code
        self.tax_type = tax_type
        self.tax_category = tax_category
        self.rate_percentage = Decimal(str(rate_percentage))
        self.cess_rate = Decimal(str(cess_rate))
        self.surcharge_rate = Decimal(str(surcharge_rate))
        self.jurisdiction_id = jurisdiction_id
        self.hsn_code_from = hsn_code_from
        self.hsn_code_to = hsn_code_to
        self.sac_code_from = sac_code_from
        self.sac_code_to = sac_code_to
        self.effective_from = effective_from or datetime.utcnow().date()
        self.effective_to = effective_to
        self.is_active = is_active
        self.is_default = is_default
        self.tenant_id = tenant_id
    
    @property
    def total_rate(self):
        """Get total tax rate including cess and surcharge"""
        return self.rate_percentage + self.cess_rate + self.surcharge_rate
    
    @property
    def is_effective(self):
        """Check if tax rate is currently effective"""
        today = datetime.utcnow().date()
        if self.effective_from and today < self.effective_from:
            return False
        if self.effective_to and today > self.effective_to:
            return False
        return True
    
    def is_applicable_to_hsn(self, hsn_code):
        """Check if tax rate applies to HSN code"""
        if not hsn_code or not self.hsn_code_from:
            return True
        
        if self.hsn_code_to:
            return self.hsn_code_from <= hsn_code <= self.hsn_code_to
        else:
            return hsn_code.startswith(self.hsn_code_from)
    
    def is_applicable_to_sac(self, sac_code):
        """Check if tax rate applies to SAC code"""
        if not sac_code or not self.sac_code_from:
            return True
        
        if self.sac_code_to:
            return self.sac_code_from <= sac_code <= self.sac_code_to
        else:
            return sac_code.startswith(self.sac_code_from)
    
    def calculate_tax(self, taxable_amount):
        """Calculate tax amount for given taxable amount"""
        if not self.is_effective or not self.is_active:
            return Decimal('0')
        
        tax_amount = taxable_amount * (self.rate_percentage / Decimal('100'))
        cess_amount = taxable_amount * (self.cess_rate / Decimal('100'))
        surcharge_amount = taxable_amount * (self.surcharge_rate / Decimal('100'))
        
        return {
            'tax_amount': tax_amount,
            'cess_amount': cess_amount,
            'surcharge_amount': surcharge_amount,
            'total_amount': tax_amount + cess_amount + surcharge_amount
        }
    
    def to_dict(self):
        """Convert tax rate to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'tax_type': self.tax_type,
            'tax_category': self.tax_category,
            'rate_percentage': float(self.rate_percentage),
            'cess_rate': float(self.cess_rate),
            'surcharge_rate': float(self.surcharge_rate),
            'total_rate': float(self.total_rate),
            'jurisdiction_id': self.jurisdiction_id,
            'jurisdiction_name': self.jurisdiction.name if self.jurisdiction else None,
            'hsn_code_from': self.hsn_code_from,
            'hsn_code_to': self.hsn_code_to,
            'sac_code_from': self.sac_code_from,
            'sac_code_to': self.sac_code_to,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'is_effective': self.is_effective,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_active_rates(tenant_id=None):
        """Get all active tax rates"""
        query = TaxRate.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(TaxRate.name).all()
    
    @staticmethod
    def get_by_code(code, tenant_id=None):
        """Get tax rate by code"""
        query = TaxRate.query.filter_by(code=code)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    @staticmethod
    def get_default_rate(tenant_id=None):
        """Get default tax rate"""
        query = TaxRate.query.filter_by(is_default=True, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.first()
    
    def __repr__(self):
        return f'<TaxRate {self.name} ({self.total_rate}%)>'


class TaxRule(FeatureAwareModel):
    """Tax rule model for complex tax calculations"""
    __tablename__ = 'tax_rules'
    
    # Feature requirements
    required_features = ['FEATURE_GST_COMPLIANCE', 'FEATURE_VAT_SUPPORT']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Rule conditions
    customer_type = db.Column(db.String(20), nullable=True)  # B2B, B2C, Export, etc.
    product_category = db.Column(db.String(50), nullable=True)
    product_type = db.Column(db.String(50), nullable=True)
    price_range_from = db.Column(db.Numeric(12, 2), nullable=True)
    price_range_to = db.Column(db.Numeric(12, 2), nullable=True)
    quantity_from = db.Column(db.Integer, nullable=True)
    quantity_to = db.Column(db.Integer, nullable=True)
    
    # Location conditions
    source_state = db.Column(db.String(100), nullable=True)
    destination_state = db.Column(db.String(100), nullable=True)
    is_inter_state = db.Column(db.Boolean, nullable=True)
    
    # Tax configuration
    tax_components = db.Column(db.Text, nullable=False)  # JSON array of tax rate IDs
    tax_calculation_method = db.Column(db.String(20), default='inclusive')  # inclusive, exclusive
    
    # Priority and status
    priority = db.Column(db.Integer, default=0)  # Higher priority rules are applied first
    is_active = db.Column(db.Boolean, default=True)
    
    # Effective dates
    effective_from = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    effective_to = db.Column(db.Date, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_tax_rules')
    
    def __init__(self, name, tax_components, description=None, customer_type=None,
                 product_category=None, product_type=None, price_range_from=None,
                 price_range_to=None, quantity_from=None, quantity_to=None,
                 source_state=None, destination_state=None, is_inter_state=None,
                 tax_calculation_method='inclusive', priority=0, is_active=True,
                 effective_from=None, effective_to=None, tenant_id=None, created_by=None):
        self.name = name
        self.description = description
        self.customer_type = customer_type
        self.product_category = product_category
        self.product_type = product_type
        self.price_range_from = Decimal(str(price_range_from)) if price_range_from else None
        self.price_range_to = Decimal(str(price_range_to)) if price_range_to else None
        self.quantity_from = quantity_from
        self.quantity_to = quantity_to
        self.source_state = source_state
        self.destination_state = destination_state
        self.is_inter_state = is_inter_state
        self.tax_components = tax_components
        self.tax_calculation_method = tax_calculation_method
        self.priority = priority
        self.is_active = is_active
        self.effective_from = effective_from or datetime.utcnow().date()
        self.effective_to = effective_to
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    def get_tax_components(self):
        """Get tax components as list"""
        import json
        try:
            return json.loads(self.tax_components)
        except:
            return []
    
    def is_applicable(self, customer=None, product=None, price=None, quantity=None,
                     source_location=None, destination_location=None):
        """Check if tax rule is applicable to given conditions"""
        if not self.is_active or not self.is_effective:
            return False
        
        # Check customer type
        if self.customer_type and customer:
            # This would need customer type logic
            pass
        
        # Check product category
        if self.product_category and product:
            if product.category and product.category.name != self.product_category:
                return False
        
        # Check product type
        if self.product_type and product:
            if product.product_type != self.product_type:
                return False
        
        # Check price range
        if price is not None:
            if self.price_range_from and price < self.price_range_from:
                return False
            if self.price_range_to and price > self.price_range_to:
                return False
        
        # Check quantity range
        if quantity is not None:
            if self.quantity_from and quantity < self.quantity_from:
                return False
            if self.quantity_to and quantity > self.quantity_to:
                return False
        
        # Check location conditions
        if self.is_inter_state is not None and source_location and destination_location:
            is_inter = source_location != destination_location
            if is_inter != self.is_inter_state:
                return False
        
        return True
    
    @property
    def is_effective(self):
        """Check if tax rule is currently effective"""
        today = datetime.utcnow().date()
        if self.effective_from and today < self.effective_from:
            return False
        if self.effective_to and today > self.effective_to:
            return False
        return True
    
    def calculate_tax(self, taxable_amount):
        """Calculate tax based on rule components"""
        if not self.is_effective or not self.is_active:
            return {'total_tax': Decimal('0'), 'components': []}
        
        components = self.get_tax_components()
        total_tax = Decimal('0')
        tax_details = []
        
        for component_id in components:
            tax_rate = TaxRate.query.get(component_id)
            if tax_rate and tax_rate.is_active and tax_rate.is_effective:
                tax_calc = tax_rate.calculate_tax(taxable_amount)
                total_tax += tax_calc['total_amount']
                tax_details.append({
                    'tax_rate_id': tax_rate.id,
                    'tax_name': tax_rate.name,
                    'tax_type': tax_rate.tax_type,
                    'rate': float(tax_rate.total_rate),
                    'amount': float(tax_calc['total_amount'])
                })
        
        return {
            'total_tax': total_tax,
            'components': tax_details,
            'calculation_method': self.tax_calculation_method
        }
    
    def to_dict(self):
        """Convert tax rule to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'customer_type': self.customer_type,
            'product_category': self.product_category,
            'product_type': self.product_type,
            'price_range_from': float(self.price_range_from) if self.price_range_from else None,
            'price_range_to': float(self.price_range_to) if self.price_range_to else None,
            'quantity_from': self.quantity_from,
            'quantity_to': self.quantity_to,
            'source_state': self.source_state,
            'destination_state': self.destination_state,
            'is_inter_state': self.is_inter_state,
            'tax_components': self.get_tax_components(),
            'tax_calculation_method': self.tax_calculation_method,
            'priority': self.priority,
            'is_active': self.is_active,
            'is_effective': self.is_effective,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_applicable_rules(customer=None, product=None, price=None, quantity=None,
                          source_location=None, destination_location=None, tenant_id=None):
        """Get applicable tax rules for given conditions"""
        query = TaxRule.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        all_rules = query.order_by(TaxRule.priority.desc()).all()
        applicable_rules = []
        
        for rule in all_rules:
            if rule.is_applicable(customer, product, price, quantity,
                              source_location, destination_location):
                applicable_rules.append(rule)
        
        return applicable_rules
    
    @staticmethod
    def get_active_rules(tenant_id=None):
        """Get all active tax rules"""
        query = TaxRule.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(TaxRule.priority.desc(), TaxRule.name).all()
    
    def __repr__(self):
        return f'<TaxRule {self.name} (Priority: {self.priority})>'


class TaxExemption(FeatureAwareModel):
    """Tax exemption model for tax-exempt customers and products"""
    __tablename__ = 'tax_exemptions'
    
    # Feature requirements
    required_features = ['FEATURE_TAX_EXEMPTIONS']
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    exemption_type = db.Column(db.String(20), nullable=False)  # customer, product, service
    
    # Customer exemption
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_group_id = db.Column(db.Integer, db.ForeignKey('customer_groups.id'), nullable=True)
    
    # Product exemption
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'), nullable=True)
    
    # Service exemption
    service_type = db.Column(db.String(50), nullable=True)
    
    # Exemption details
    exemption_reason = db.Column(db.String(100), nullable=False)
    exemption_certificate = db.Column(db.String(100), nullable=True)  # Certificate number
    certificate_valid_from = db.Column(db.Date, nullable=True)
    certificate_valid_to = db.Column(db.Date, nullable=True)
    
    # Tax types exempted
    exempted_tax_types = db.Column(db.Text, nullable=True)  # JSON array of tax types
    
    # Status and dates
    is_active = db.Column(db.Boolean, default=True)
    effective_from = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    effective_to = db.Column(db.Date, nullable=True)
    
    # Multi-tenancy and timestamps
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    customer = db.relationship('Customer', backref='tax_exemptions')
    customer_group = db.relationship('CustomerGroup', backref='tax_exemptions')
    product = db.relationship('Product', backref='tax_exemptions')
    product_category = db.relationship('ProductCategory', backref='tax_exemptions')
    creator = db.relationship('User', backref='created_tax_exemptions')
    
    def __init__(self, name, exemption_type, exemption_reason, customer_id=None,
                 customer_group_id=None, product_id=None, product_category_id=None,
                 service_type=None, exemption_certificate=None, certificate_valid_from=None,
                 certificate_valid_to=None, exempted_tax_types=None, is_active=True,
                 effective_from=None, effective_to=None, tenant_id=None, created_by=None):
        self.name = name
        self.exemption_type = exemption_type
        self.exemption_reason = exemption_reason
        self.customer_id = customer_id
        self.customer_group_id = customer_group_id
        self.product_id = product_id
        self.product_category_id = product_category_id
        self.service_type = service_type
        self.exemption_certificate = exemption_certificate
        self.certificate_valid_from = certificate_valid_from
        self.certificate_valid_to = certificate_valid_to
        self.exempted_tax_types = exempted_tax_types
        self.is_active = is_active
        self.effective_from = effective_from or datetime.utcnow().date()
        self.effective_to = effective_to
        self.tenant_id = tenant_id
        self.created_by = created_by
    
    def get_exempted_tax_types(self):
        """Get exempted tax types as list"""
        import json
        try:
            return json.loads(self.exempted_tax_types) if self.exempted_tax_types else []
        except:
            return []
    
    @property
    def is_certificate_valid(self):
        """Check if exemption certificate is valid"""
        if not self.certificate_valid_from or not self.certificate_valid_to:
            return True  # No date restrictions
        
        today = datetime.utcnow().date()
        return self.certificate_valid_from <= today <= self.certificate_valid_to
    
    @property
    def is_effective(self):
        """Check if exemption is currently effective"""
        if not self.is_active:
            return False
        
        today = datetime.utcnow().date()
        if self.effective_from and today < self.effective_from:
            return False
        if self.effective_to and today > self.effective_to:
            return False
        
        return self.is_certificate_valid
    
    def is_applicable(self, customer=None, product=None, service_type=None):
        """Check if exemption is applicable"""
        if not self.is_effective:
            return False
        
        # Check customer exemption
        if self.exemption_type == 'customer' and customer:
            if self.customer_id and customer.id != self.customer_id:
                return False
            if self.customer_group_id and customer.customer_group_id != self.customer_group_id:
                return False
        
        # Check product exemption
        if self.exemption_type == 'product' and product:
            if self.product_id and product.id != self.product_id:
                return False
            if self.product_category_id and product.category_id != self.product_category_id:
                return False
        
        # Check service exemption
        if self.exemption_type == 'service' and service_type:
            if self.service_type and service_type != self.service_type:
                return False
        
        return True
    
    def to_dict(self):
        """Convert tax exemption to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'exemption_type': self.exemption_type,
            'exemption_reason': self.exemption_reason,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name_decrypted if self.customer else None,
            'customer_group_id': self.customer_group_id,
            'customer_group_name': self.customer_group.name if self.customer_group else None,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_category_id': self.product_category_id,
            'product_category_name': self.product_category.name if self.product_category else None,
            'service_type': self.service_type,
            'exemption_certificate': self.exemption_certificate,
            'certificate_valid_from': self.certificate_valid_from.isoformat() if self.certificate_valid_from else None,
            'certificate_valid_to': self.certificate_valid_to.isoformat() if self.certificate_valid_to else None,
            'exempted_tax_types': self.get_exempted_tax_types(),
            'is_active': self.is_active,
            'is_certificate_valid': self.is_certificate_valid,
            'is_effective': self.is_effective,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @staticmethod
    def get_applicable_exemptions(customer=None, product=None, service_type=None, tenant_id=None):
        """Get applicable tax exemptions"""
        query = TaxExemption.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        
        all_exemptions = query.all()
        applicable_exemptions = []
        
        for exemption in all_exemptions:
            if exemption.is_applicable(customer, product, service_type):
                applicable_exemptions.append(exemption)
        
        return applicable_exemptions
    
    @staticmethod
    def get_active_exemptions(tenant_id=None):
        """Get all active tax exemptions"""
        query = TaxExemption.query.filter_by(is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.order_by(TaxExemption.name).all()
    
    def __repr__(self):
        return f'<TaxExemption {self.name} ({self.exemption_type})>'