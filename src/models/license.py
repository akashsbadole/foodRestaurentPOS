"""
License model for POS MVP application
Handles license data with encrypted fields and cryptographic signatures
"""

import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

from src.utils.encryption import get_encryption_manager
from src.utils.license_crypto import LicenseCrypto


class License:
    """
    License model with encrypted fields and cryptographic signatures
    Implements strong anti-cracking measures with multiple validation layers
    """
    
    # License types
    TYPE_TRIAL = "trial"
    TYPE_STANDARD = "standard"
    TYPE_PROFESSIONAL = "professional"
    TYPE_ENTERPRISE = "enterprise"
    
    # License statuses
    STATUS_ACTIVE = "active"
    STATUS_SUSPENDED = "suspended"
    STATUS_EXPIRED = "expired"
    STATUS_REVOKED = "revoked"
    
    # Feature flags for different license types
    FEATURES = {
        TYPE_TRIAL: [
            "orders.create", "orders.view", "orders.edit",
            "menu.view", "menu.edit", "inventory.view",
            "reports.basic", "tables.manage"
        ],
        TYPE_STANDARD: [
            "orders.create", "orders.view", "orders.edit", "orders.delete",
            "menu.view", "menu.edit", "menu.create", "inventory.view", "inventory.edit",
            "reports.basic", "tables.manage", "users.create", "users.edit"
        ],
        TYPE_PROFESSIONAL: [
            "orders.create", "orders.view", "orders.edit", "orders.delete",
            "menu.view", "menu.edit", "menu.create", "menu.delete", "inventory.view", 
            "inventory.edit", "inventory.manage", "reports.basic", "reports.advanced",
            "tables.manage", "users.create", "users.edit", "users.manage",
            "export.data", "import.data", "backup.create", "backup.restore"
        ],
        TYPE_ENTERPRISE: [
            "orders.create", "orders.view", "orders.edit", "orders.delete",
            "menu.view", "menu.edit", "menu.create", "menu.delete", "inventory.view", 
            "inventory.edit", "inventory.manage", "reports.basic", "reports.advanced",
            "reports.custom", "tables.manage", "users.create", "users.edit", "users.manage",
            "export.data", "import.data", "backup.create", "backup.restore",
            "api.access", "multi_branch", "advanced_analytics", "priority_support"
        ]
    }
    
    def __init__(self, db_manager=None):
        """Initialize license model"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        self.license_crypto = LicenseCrypto()
        
        # License data (encrypted fields)
        self._license_key = None
        self._license_id = None
        self._customer_name = None
        self._customer_email = None
        self._license_type = None
        self._features = None
        self._issued_date = None
        self._expiry_date = None
        self._machine_bindings = None
        self._signature = None
        self._status = None
        self._validation_hash = None
        self._last_validated = None
        self._activation_count = 0
        self._max_activations = 3
        self._server_validation_token = None
        self._offline_grace_period_days = 30
        self._is_trial = False
        self._trial_days_used = 0
        
    def create_license(self, license_data: Dict[str, Any]) -> bool:
        """
        Create a new license with cryptographic signature
        
        Args:
            license_data: Dictionary containing license information
            
        Returns:
            True if license created successfully, False otherwise
        """
        try:
            # Extract license data
            self._license_key = self._generate_license_key()
            self._license_id = license_data.get('license_id', self._generate_license_id())
            self._customer_name = license_data.get('customer_name', '')
            self._customer_email = license_data.get('customer_email', '')
            self._license_type = license_data.get('license_type', self.TYPE_TRIAL)
            self._features = license_data.get('features', self.FEATURES.get(self._license_type, []))
            self._issued_date = datetime.now()
            
            # Set expiry based on license type
            if self._license_type == self.TYPE_TRIAL:
                self._expiry_date = self._issued_date + timedelta(days=30)
                self._is_trial = True
            else:
                # Perpetual licenses with maintenance expiry
                maintenance_days = license_data.get('maintenance_days', 365)
                self._expiry_date = self._issued_date + timedelta(days=maintenance_days)
            
            self._machine_bindings = license_data.get('machine_bindings', [])
            self._status = self.STATUS_ACTIVE
            self._activation_count = 0
            self._max_activations = license_data.get('max_activations', 3)
            self._offline_grace_period_days = license_data.get('offline_grace_period_days', 30)
            
            # Generate cryptographic signature
            self._generate_signature()
            
            # Generate validation hash
            self._generate_validation_hash()
            
            return True
        except Exception as e:
            print(f"Error creating license: {str(e)}")
            return False
    
    def _generate_license_key(self) -> str:
        """Generate a unique license key"""
        import uuid
        import secrets
        
        # Generate base key
        base_key = str(uuid.uuid4()).replace('-', '').upper()
        
        # Add entropy
        random_bytes = secrets.token_bytes(8)
        entropy_hash = hashlib.sha256(random_bytes).hexdigest()[:8].upper()
        
        # Format license key (XXXX-XXXX-XXXX-XXXX)
        license_key = f"{base_key[:4]}-{base_key[4:8]}-{base_key[8:12]}-{entropy_hash}"
        
        return license_key
    
    def _generate_license_id(self) -> str:
        """Generate a unique license ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_signature(self) -> None:
        """Generate cryptographic signature for license"""
        license_data = {
            'license_key': self._license_key,
            'license_id': self._license_id,
            'customer_name': self._customer_name,
            'customer_email': self._customer_email,
            'license_type': self._license_type,
            'features': sorted(self._features),  # Sort for consistent signature
            'issued_date': self._issued_date.isoformat() if self._issued_date else None,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'machine_bindings': self._machine_bindings,
            'max_activations': self._max_activations,
            'offline_grace_period_days': self._offline_grace_period_days
        }
        
        # Convert to JSON string
        license_json = json.dumps(license_data, sort_keys=True)
        
        # Generate signature
        self._signature = self.license_crypto.sign_data(license_json)
    
    def _generate_validation_hash(self) -> None:
        """Generate validation hash for tamper detection"""
        validation_data = {
            'license_key': self._license_key,
            'license_id': self._license_id,
            'license_type': self._license_type,
            'features': sorted(self._features),
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'status': self._status,
            'signature': self._signature
        }
        
        validation_json = json.dumps(validation_data, sort_keys=True)
        self._validation_hash = hashlib.sha256(validation_json.encode()).hexdigest()
    
    def verify_signature(self) -> bool:
        """Verify the cryptographic signature of the license"""
        try:
            license_data = {
                'license_key': self._license_key,
                'license_id': self._license_id,
                'customer_name': self._customer_name,
                'customer_email': self._customer_email,
                'license_type': self._license_type,
                'features': sorted(self._features) if self._features else [],
                'issued_date': self._issued_date.isoformat() if self._issued_date else None,
                'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
                'machine_bindings': self._machine_bindings,
                'max_activations': self._max_activations,
                'offline_grace_period_days': self._offline_grace_period_days
            }
            
            license_json = json.dumps(license_data, sort_keys=True)
            return self.license_crypto.verify_signature(license_json, self._signature)
        except Exception as e:
            print(f"Error verifying signature: {str(e)}")
            return False
    
    def verify_integrity(self) -> bool:
        """Verify license integrity using validation hash"""
        try:
            if not self._validation_hash:
                return False
            
            validation_data = {
                'license_key': self._license_key,
                'license_id': self._license_id,
                'license_type': self._license_type,
                'features': sorted(self._features) if self._features else [],
                'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
                'status': self._status,
                'signature': self._signature
            }
            
            validation_json = json.dumps(validation_data, sort_keys=True)
            calculated_hash = hashlib.sha256(validation_json.encode()).hexdigest()
            
            return calculated_hash == self._validation_hash
        except Exception as e:
            print(f"Error verifying integrity: {str(e)}")
            return False
    
    def is_expired(self) -> bool:
        """Check if license is expired"""
        if not self._expiry_date:
            return False
        
        # Check if trial license has expired
        if self._is_trial:
            days_used = (datetime.now() - self._issued_date).days if self._issued_date else 0
            return days_used >= 30
        
        # Check perpetual license maintenance expiry
        return datetime.now() > self._expiry_date
    
    def is_valid(self) -> bool:
        """Check if license is valid"""
        # Check status
        if self._status != self.STATUS_ACTIVE:
            return False
        
        # Check expiry
        if self.is_expired():
            return False
        
        # Verify signature
        if not self.verify_signature():
            return False
        
        # Verify integrity
        if not self.verify_integrity():
            return False
        
        return True
    
    def has_feature(self, feature: str) -> bool:
        """Check if license has a specific feature"""
        if not self._features:
            return False
        return feature in self._features
    
    def get_features(self) -> List[str]:
        """Get list of features for this license"""
        return self._features.copy() if self._features else []
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get license information (non-sensitive data)"""
        return {
            'license_key': self._license_key,
            'license_id': self._license_id,
            'customer_name': self._customer_name,
            'customer_email': self._customer_email,
            'license_type': self._license_type,
            'features': self._features,
            'issued_date': self._issued_date.isoformat() if self._issued_date else None,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'status': self._status,
            'is_trial': self._is_trial,
            'activation_count': self._activation_count,
            'max_activations': self._max_activations,
            'last_validated': self._last_validated.isoformat() if self._last_validated else None
        }
    
    def save_to_database(self) -> bool:
        """Save license to database with encrypted fields"""
        if not self.db:
            return False
        
        try:
            # Encrypt sensitive fields
            encrypted_customer_name = self.encryption_manager.encrypt(self._customer_name) if self._customer_name else None
            encrypted_customer_email = self.encryption_manager.encrypt(self._customer_email) if self._customer_email else None
            encrypted_features = self.encryption_manager.encrypt(json.dumps(self._features)) if self._features else None
            encrypted_machine_bindings = self.encryption_manager.encrypt(json.dumps(self._machine_bindings)) if self._machine_bindings else None
            
            # Convert dates to strings
            issued_date_str = self._issued_date.isoformat() if self._issued_date else None
            expiry_date_str = self._expiry_date.isoformat() if self._expiry_date else None
            last_validated_str = self._last_validated.isoformat() if self._last_validated else None
            
            query = """
            INSERT OR REPLACE INTO licenses (
                license_key, license_id, customer_name, customer_email, license_type,
                features, issued_date, expiry_date, machine_bindings, signature,
                validation_hash, status, last_validated, activation_count,
                max_activations, server_validation_token, offline_grace_period_days,
                is_trial, trial_days_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                self._license_key, self._license_id, encrypted_customer_name, encrypted_customer_email,
                self._license_type, encrypted_features, issued_date_str, expiry_date_str,
                encrypted_machine_bindings, self._signature, self._validation_hash,
                self._status, last_validated_str, self._activation_count, self._max_activations,
                self._server_validation_token, self._offline_grace_period_days,
                self._is_trial, self._trial_days_used
            )
            
            self.db.execute_query(query, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error saving license to database: {str(e)}")
            return False
    
    def load_from_database(self, license_key: str) -> bool:
        """Load license from database using license key"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM licenses WHERE license_key = ?"
            self.db.execute_query(query, (license_key,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._license_key = result[1]
            self._license_id = result[2]
            self._customer_name = self.encryption_manager.decrypt(result[3]) if result[3] else None
            self._customer_email = self.encryption_manager.decrypt(result[4]) if result[4] else None
            self._license_type = result[5]
            self._features = json.loads(self.encryption_manager.decrypt(result[6])) if result[6] else []
            self._issued_date = datetime.fromisoformat(result[7]) if result[7] else None
            self._expiry_date = datetime.fromisoformat(result[8]) if result[8] else None
            self._machine_bindings = json.loads(self.encryption_manager.decrypt(result[9])) if result[9] else []
            self._signature = result[10]
            self._validation_hash = result[11]
            self._status = result[12]
            self._last_validated = datetime.fromisoformat(result[13]) if result[13] else None
            self._activation_count = result[14]
            self._max_activations = result[15]
            self._server_validation_token = result[16]
            self._offline_grace_period_days = result[17]
            self._is_trial = bool(result[18])
            self._trial_days_used = result[19]
            
            return True
        except Exception as e:
            print(f"Error loading license from database: {str(e)}")
            return False
    
    def update_validation_timestamp(self) -> None:
        """Update the last validated timestamp"""
        self._last_validated = datetime.now()
        if self._is_trial:
            self._trial_days_used = (datetime.now() - self._issued_date).days if self._issued_date else 0
    
    def increment_activation_count(self) -> bool:
        """Increment activation count and check if limit exceeded"""
        if self._activation_count >= self._max_activations:
            return False
        
        self._activation_count += 1
        return True
    
    def revoke(self) -> None:
        """Revoke the license"""
        self._status = self.STATUS_REVOKED
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def suspend(self) -> None:
        """Suspend the license"""
        self._status = self.STATUS_SUSPENDED
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def activate(self) -> None:
        """Activate the license"""
        self._status = self.STATUS_ACTIVE
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def export_license_data(self) -> Dict[str, Any]:
        """Export license data for backup or transfer"""
        return {
            'license_key': self._license_key,
            'license_id': self._license_id,
            'customer_name': self._customer_name,
            'customer_email': self._customer_email,
            'license_type': self._license_type,
            'features': self._features,
            'issued_date': self._issued_date.isoformat() if self._issued_date else None,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'machine_bindings': self._machine_bindings,
            'signature': self._signature,
            'validation_hash': self._validation_hash,
            'status': self._status,
            'activation_count': self._activation_count,
            'max_activations': self._max_activations,
            'offline_grace_period_days': self._offline_grace_period_days,
            'is_trial': self._is_trial,
            'trial_days_used': self._trial_days_used
        }
    
    def import_license_data(self, license_data: Dict[str, Any]) -> bool:
        """Import license data from backup or transfer"""
        try:
            self._license_key = license_data.get('license_key')
            self._license_id = license_data.get('license_id')
            self._customer_name = license_data.get('customer_name')
            self._customer_email = license_data.get('customer_email')
            self._license_type = license_data.get('license_type')
            self._features = license_data.get('features', [])
            self._issued_date = datetime.fromisoformat(license_data['issued_date']) if license_data.get('issued_date') else None
            self._expiry_date = datetime.fromisoformat(license_data['expiry_date']) if license_data.get('expiry_date') else None
            self._machine_bindings = license_data.get('machine_bindings', [])
            self._signature = license_data.get('signature')
            self._validation_hash = license_data.get('validation_hash')
            self._status = license_data.get('status', self.STATUS_ACTIVE)
            self._activation_count = license_data.get('activation_count', 0)
            self._max_activations = license_data.get('max_activations', 3)
            self._offline_grace_period_days = license_data.get('offline_grace_period_days', 30)
            self._is_trial = license_data.get('is_trial', False)
            self._trial_days_used = license_data.get('trial_days_used', 0)
            
            # Verify imported license
            return self.is_valid()
        except Exception as e:
            print(f"Error importing license data: {str(e)}")
            return False