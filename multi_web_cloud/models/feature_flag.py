"""
Enhanced feature flag models for multi-retail POS system
"""

from datetime import datetime
import uuid
from . import db


class FeatureDefinition(db.Model):
    """Feature definition metadata"""
    __tablename__ = 'feature_definitions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  # core, retail_type, advanced, etc.
    feature_type = db.Column(db.Enum('boolean', 'string', 'numeric', 'json', name='feature_type'), default='boolean')
    default_value = db.Column(db.Boolean, default=False)
    is_required = db.Column(db.Boolean, default=False)
    is_experimental = db.Column(db.Boolean, default=False)
    
    # Retail type restrictions
    supported_retail_types = db.Column(db.JSON, nullable=True)  # List of retail types that support this feature
    required_retail_types = db.Column(db.JSON, nullable=True)  # Retail types that require this feature
    
    # Version and deprecation
    version = db.Column(db.String(20), default='1.0.0')
    deprecated = db.Column(db.Boolean, default=False)
    deprecation_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dependencies = db.relationship('FeatureDependency', foreign_keys='FeatureDependency.feature_name', 
                                backref='feature_definition', lazy=True, cascade='all, delete-orphan')
    dependents = db.relationship('FeatureDependency', foreign_keys='FeatureDependency.depends_on_feature',
                               backref='dependent_feature', lazy=True, cascade='all, delete-orphan')
    conflicts = db.relationship('FeatureConflict', backref='feature_definition', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name, display_name, description, category, **kwargs):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.category = category
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert feature definition to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'feature_type': self.feature_type,
            'default_value': self.default_value,
            'is_required': self.is_required,
            'is_experimental': self.is_experimental,
            'supported_retail_types': self.supported_retail_types,
            'required_retail_types': self.required_retail_types,
            'version': self.version,
            'deprecated': self.deprecated,
            'deprecation_message': self.deprecation_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def is_supported_by_retail_type(self, retail_type):
        """Check if feature is supported by retail type"""
        if not self.supported_retail_types:
            return True  # Feature supports all retail types if not specified
        return retail_type in self.supported_retail_types
    
    def is_required_by_retail_type(self, retail_type):
        """Check if feature is required by retail type"""
        if not self.required_retail_types:
            return False  # Feature is not required by any retail type if not specified
        return retail_type in self.required_retail_types
    
    def __repr__(self):
        return f'<FeatureDefinition {self.name}>'


class FeatureDependency(db.Model):
    """Feature dependency relationships"""
    __tablename__ = 'feature_dependencies'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_name = db.Column(db.String(100), db.ForeignKey('feature_definitions.name'), nullable=False)
    depends_on_feature = db.Column(db.String(100), db.ForeignKey('feature_definitions.name'), nullable=False)
    dependency_type = db.Column(db.Enum('required', 'optional', 'conflicts', name='dependency_type'), default='required')
    condition = db.Column(db.String(200), nullable=True)  # Conditional logic
    description = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, feature_name, depends_on_feature, dependency_type='required', **kwargs):
        self.feature_name = feature_name
        self.depends_on_feature = depends_on_feature
        self.dependency_type = dependency_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert dependency to dictionary"""
        return {
            'id': self.id,
            'feature_name': self.feature_name,
            'depends_on_feature': self.depends_on_feature,
            'dependency_type': self.dependency_type,
            'condition': self.condition,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<FeatureDependency {self.feature_name} -> {self.depends_on_feature}>'


class FeatureConflict(db.Model):
    """Feature conflict definitions"""
    __tablename__ = 'feature_conflicts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_1 = db.Column(db.String(100), db.ForeignKey('feature_definitions.name'), nullable=False)
    feature_2 = db.Column(db.String(100), db.ForeignKey('feature_definitions.name'), nullable=False)
    conflict_type = db.Column(db.String(50), nullable=False)
    resolution_strategy = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, feature_1, feature_2, conflict_type, **kwargs):
        self.feature_1 = feature_1
        self.feature_2 = feature_2
        self.conflict_type = conflict_type
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert conflict to dictionary"""
        return {
            'id': self.id,
            'feature_1': self.feature_1,
            'feature_2': self.feature_2,
            'conflict_type': self.conflict_type,
            'resolution_strategy': self.resolution_strategy,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<FeatureConflict {self.feature_1} <-> {self.feature_2}>'


class RetailTypePreset(db.Model):
    """Retail-type specific feature presets"""
    __tablename__ = 'retail_type_presets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    retail_type = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    feature_flags = db.Column(db.JSON, nullable=False)  # Feature configuration
    is_active = db.Column(db.Boolean, default=True)
    
    # Preset metadata
    version = db.Column(db.String(20), default='1.0.0')
    author = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.JSON, nullable=True)  # Tags for categorization
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, retail_type, name, feature_flags, **kwargs):
        self.retail_type = retail_type
        self.name = name
        self.feature_flags = feature_flags
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert preset to dictionary"""
        return {
            'id': self.id,
            'retail_type': self.retail_type,
            'name': self.name,
            'description': self.description,
            'feature_flags': self.feature_flags,
            'is_active': self.is_active,
            'version': self.version,
            'author': self.author,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_enabled_features(self):
        """Get list of enabled features in this preset"""
        return [feature for feature, enabled in self.feature_flags.items() if enabled]
    
    def get_disabled_features(self):
        """Get list of disabled features in this preset"""
        return [feature for feature, enabled in self.feature_flags.items() if not enabled]
    
    def is_feature_enabled(self, feature_name):
        """Check if a feature is enabled in this preset"""
        return self.feature_flags.get(feature_name, False)
    
    def __repr__(self):
        return f'<RetailTypePreset {self.name} for {self.retail_type}>'


class FeatureFlagAuditLog(db.Model):
    """Audit log for feature flag changes"""
    __tablename__ = 'feature_flag_audit_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(20), nullable=False)  # created, updated, deleted, enabled, disabled
    old_value = db.Column(db.JSON, nullable=True)
    new_value = db.Column(db.JSON, nullable=True)
    changed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tenant = db.relationship('Tenant', backref='feature_audit_logs')
    user = db.relationship('User', backref='feature_audit_logs')
    
    def __init__(self, tenant_id, feature_name, action, changed_by, **kwargs):
        self.tenant_id = tenant_id
        self.feature_name = feature_name
        self.action = action
        self.changed_by = changed_by
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'feature_name': self.feature_name,
            'action': self.action,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_by': self.changed_by,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def __repr__(self):
        return f'<FeatureFlagAuditLog {self.action} on {self.feature_name} for {self.tenant_id}>'