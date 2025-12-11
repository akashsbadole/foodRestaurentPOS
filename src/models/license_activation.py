"""
License Activation model for POS MVP application
Handles license activation with hardware binding and anti-cracking measures
"""

import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

from src.utils.encryption import get_encryption_manager
from src.utils.license_crypto import LicenseCrypto
from src.models.hardware_binding import HardwareBinding


class LicenseActivation:
    """
    License Activation model with hardware binding and secure activation process
    Implements strong anti-cracking measures with multiple validation layers
    """
    
    # Activation statuses
    STATUS_PENDING = "pending"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_REVOKED = "revoked"
    STATUS_SUSPENDED = "suspended"
    STATUS_FAILED = "failed"
    
    # Activation types
    TYPE_ONLINE = "online"
    TYPE_OFFLINE = "offline"
    TYPE_TRIAL = "trial"
    
    def __init__(self, db_manager=None):
        """Initialize license activation model"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        self.license_crypto = LicenseCrypto()
        self.hardware_binding = HardwareBinding()
        
        # Activation data
        self._activation_id = None
        self._license_key = None
        self._license_id = None
        self._activation_code = None
        self._activation_type = None
        self._hardware_fingerprint = None
        self._hardware_bindings = []
        self._activation_date = None
        self._last_validated = None
        self._expiry_date = None
        self._validation_count = 0
        self._max_validations = 100  # Maximum offline validations before online check required
        self._status = None
        self._activation_signature = None
        self._validation_hash = None
        self._machine_token = None
        self._server_response = None
        self._offline_grace_expires = None
        self._is_trial_activation = False
        self._trial_days_remaining = 0
        self._activation_metadata = {}
        
    def create_activation(self, license_key: str, license_id: str, activation_type: str = TYPE_ONLINE) -> bool:
        """
        Create a new license activation
        
        Args:
            license_key: License key to activate
            license_id: License ID
            activation_type: Type of activation (online/offline/trial)
            
        Returns:
            True if activation created successfully, False otherwise
        """
        try:
            # Generate activation ID
            self._activation_id = self._generate_activation_id()
            self._license_key = license_key
            self._license_id = license_id
            self._activation_type = activation_type
            self._activation_code = self._generate_activation_code()
            
            # Generate hardware fingerprint
            self._hardware_fingerprint = self.hardware_binding.get_fingerprint()
            self._hardware_bindings = [self._hardware_fingerprint]
            
            # Set activation date
            self._activation_date = datetime.now()
            self._last_validated = self._activation_date
            
            # Set expiry based on activation type
            if activation_type == self.TYPE_TRIAL:
                self._expiry_date = self._activation_date + timedelta(days=30)
                self._is_trial_activation = True
                self._trial_days_remaining = 30
            else:
                # Regular activation with offline grace period
                self._offline_grace_expires = self._activation_date + timedelta(days=30)
            
            self._status = self.STATUS_PENDING
            self._validation_count = 0
            
            # Generate machine token
            self._machine_token = self._generate_machine_token()
            
            # Generate activation signature
            self._generate_activation_signature()
            
            # Generate validation hash
            self._generate_validation_hash()
            
            return True
        except Exception as e:
            print(f"Error creating activation: {str(e)}")
            return False
    
    def _generate_activation_id(self) -> str:
        """Generate a unique activation ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_activation_code(self) -> str:
        """Generate a unique activation code"""
        import secrets
        
        # Generate random bytes
        random_bytes = secrets.token_bytes(16)
        
        # Create hash with timestamp
        timestamp = int(datetime.now().timestamp())
        combined = random_bytes + timestamp.to_bytes(8, 'big')
        
        # Generate activation code
        hash_obj = hashlib.sha256(combined)
        activation_code = base64.b32encode(hash_obj.digest()[:10]).decode('utf-8')
        
        # Format code (XXXX-XXXX-XXXX)
        formatted_code = f"{activation_code[:4]}-{activation_code[4:8]}-{activation_code[8:12]}"
        
        return formatted_code
    
    def _generate_machine_token(self) -> str:
        """Generate a machine-specific token"""
        import secrets
        
        # Combine hardware fingerprint with random data
        random_bytes = secrets.token_bytes(16)
        fingerprint_bytes = self._hardware_fingerprint.encode('utf-8')
        
        combined = random_bytes + fingerprint_bytes
        token_hash = hashlib.sha256(combined).hexdigest()
        
        return token_hash
    
    def _generate_activation_signature(self) -> None:
        """Generate cryptographic signature for activation"""
        activation_data = {
            'activation_id': self._activation_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'activation_code': self._activation_code,
            'activation_type': self._activation_type,
            'hardware_fingerprint': self._hardware_fingerprint,
            'hardware_bindings': self._hardware_bindings,
            'activation_date': self._activation_date.isoformat() if self._activation_date else None,
            'machine_token': self._machine_token,
            'status': self._status
        }
        
        # Convert to JSON string
        activation_json = json.dumps(activation_data, sort_keys=True)
        
        # Generate signature
        self._activation_signature = self.license_crypto.sign_data(activation_json)
    
    def _generate_validation_hash(self) -> None:
        """Generate validation hash for tamper detection"""
        validation_data = {
            'activation_id': self._activation_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'activation_type': self._activation_type,
            'hardware_fingerprint': self._hardware_fingerprint,
            'activation_date': self._activation_date.isoformat() if self._activation_date else None,
            'last_validated': self._last_validated.isoformat() if self._last_validated else None,
            'status': self._status,
            'activation_signature': self._activation_signature,
            'machine_token': self._machine_token
        }
        
        validation_json = json.dumps(validation_data, sort_keys=True)
        self._validation_hash = hashlib.sha256(validation_json.encode()).hexdigest()
    
    def verify_activation_signature(self) -> bool:
        """Verify the cryptographic signature of the activation"""
        try:
            activation_data = {
                'activation_id': self._activation_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'activation_code': self._activation_code,
                'activation_type': self._activation_type,
                'hardware_fingerprint': self._hardware_fingerprint,
                'hardware_bindings': self._hardware_bindings,
                'activation_date': self._activation_date.isoformat() if self._activation_date else None,
                'machine_token': self._machine_token,
                'status': self._status
            }
            
            activation_json = json.dumps(activation_data, sort_keys=True)
            return self.license_crypto.verify_signature(activation_json, self._activation_signature)
        except Exception as e:
            print(f"Error verifying activation signature: {str(e)}")
            return False
    
    def verify_integrity(self) -> bool:
        """Verify activation integrity using validation hash"""
        try:
            if not self._validation_hash:
                return False
            
            validation_data = {
                'activation_id': self._activation_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'activation_type': self._activation_type,
                'hardware_fingerprint': self._hardware_fingerprint,
                'activation_date': self._activation_date.isoformat() if self._activation_date else None,
                'last_validated': self._last_validated.isoformat() if self._last_validated else None,
                'status': self._status,
                'activation_signature': self._activation_signature,
                'machine_token': self._machine_token
            }
            
            validation_json = json.dumps(validation_data, sort_keys=True)
            calculated_hash = hashlib.sha256(validation_json.encode()).hexdigest()
            
            return calculated_hash == self._validation_hash
        except Exception as e:
            print(f"Error verifying activation integrity: {str(e)}")
            return False
    
    def is_valid_hardware(self) -> bool:
        """Check if current hardware matches activation"""
        try:
            current_fingerprint = self.hardware_binding.get_fingerprint()
            
            # Check if current fingerprint is in allowed bindings
            if current_fingerprint == self._hardware_fingerprint:
                return True
            
            # Check if current fingerprint is in additional bindings
            for binding in self._hardware_bindings:
                if self.hardware_binding.compare_fingerprints(current_fingerprint, binding):
                    return True
            
            return False
        except Exception as e:
            print(f"Error validating hardware: {str(e)}")
            return False
    
    def is_expired(self) -> bool:
        """Check if activation is expired"""
        if not self._expiry_date and not self._offline_grace_expires:
            return False
        
        now = datetime.now()
        
        # Check trial expiry
        if self._is_trial_activation and self._expiry_date:
            return now > self._expiry_date
        
        # Check offline grace period
        if self._offline_grace_expires:
            return now > self._offline_grace_expires
        
        return False
    
    def needs_online_validation(self) -> bool:
        """Check if activation needs online validation"""
        # Always need online validation for trial activations
        if self._is_trial_activation:
            return True
        
        # Check if validation count exceeded
        if self._validation_count >= self._max_validations:
            return True
        
        # Check if offline grace period expired
        if self._offline_grace_expires and datetime.now() > self._offline_grace_expires:
            return True
        
        return False
    
    def is_valid(self) -> bool:
        """Check if activation is valid"""
        # Check status
        if self._status != self.STATUS_ACTIVE:
            return False
        
        # Check expiry
        if self.is_expired():
            return False
        
        # Check hardware binding
        if not self.is_valid_hardware():
            return False
        
        # Verify signature
        if not self.verify_activation_signature():
            return False
        
        # Verify integrity
        if not self.verify_integrity():
            return False
        
        return True
    
    def validate_activation(self, force_online: bool = False) -> Dict[str, Any]:
        """
        Validate activation and return validation result
        
        Args:
            force_online: Force online validation even if not required
            
        Returns:
            Dictionary with validation result
        """
        result = {
            'valid': False,
            'needs_online': False,
            'message': '',
            'days_remaining': 0,
            'validation_count': self._validation_count
        }
        
        try:
            # Check if activation needs online validation
            if force_online or self.needs_online_validation():
                result['needs_online'] = True
                result['message'] = 'Online validation required'
                return result
            
            # Perform local validation
            if self.is_valid():
                # Update validation count and timestamp
                self._validation_count += 1
                self._last_validated = datetime.now()
                
                # Update trial days remaining
                if self._is_trial_activation and self._expiry_date:
                    days_remaining = (self._expiry_date - datetime.now()).days
                    self._trial_days_remaining = max(0, days_remaining)
                    result['days_remaining'] = self._trial_days_remaining
                
                result['valid'] = True
                result['message'] = 'Activation validated successfully'
                
                # Update validation hash
                self._generate_validation_hash()
            else:
                result['message'] = 'Activation validation failed'
                
        except Exception as e:
            result['message'] = f'Validation error: {str(e)}'
        
        return result
    
    def add_hardware_binding(self, hardware_fingerprint: str) -> bool:
        """
        Add additional hardware binding for license transfer
        
        Args:
            hardware_fingerprint: Hardware fingerprint to add
            
        Returns:
            True if binding added successfully, False otherwise
        """
        try:
            if hardware_fingerprint not in self._hardware_bindings:
                self._hardware_bindings.append(hardware_fingerprint)
                
                # Update activation signature
                self._generate_activation_signature()
                
                # Update validation hash
                self._generate_validation_hash()
                
                return True
            return False
        except Exception as e:
            print(f"Error adding hardware binding: {str(e)}")
            return False
    
    def activate(self) -> None:
        """Activate the license activation"""
        self._status = self.STATUS_ACTIVE
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def revoke(self) -> None:
        """Revoke the license activation"""
        self._status = self.STATUS_REVOKED
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def suspend(self) -> None:
        """Suspend the license activation"""
        self._status = self.STATUS_SUSPENDED
        self._generate_validation_hash()  # Update hash to reflect status change
    
    def get_activation_info(self) -> Dict[str, Any]:
        """Get activation information (non-sensitive data)"""
        return {
            'activation_id': self._activation_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'activation_code': self._activation_code,
            'activation_type': self._activation_type,
            'activation_date': self._activation_date.isoformat() if self._activation_date else None,
            'last_validated': self._last_validated.isoformat() if self._last_validated else None,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'status': self._status,
            'validation_count': self._validation_count,
            'max_validations': self._max_validations,
            'is_trial_activation': self._is_trial_activation,
            'trial_days_remaining': self._trial_days_remaining,
            'hardware_bindings_count': len(self._hardware_bindings)
        }
    
    def save_to_database(self) -> bool:
        """Save activation to database with encrypted fields"""
        if not self.db:
            return False
        
        try:
            # Encrypt sensitive fields
            encrypted_hardware_fingerprint = self.encryption_manager.encrypt(self._hardware_fingerprint) if self._hardware_fingerprint else None
            encrypted_hardware_bindings = self.encryption_manager.encrypt(json.dumps(self._hardware_bindings)) if self._hardware_bindings else None
            encrypted_machine_token = self.encryption_manager.encrypt(self._machine_token) if self._machine_token else None
            encrypted_server_response = self.encryption_manager.encrypt(json.dumps(self._server_response)) if self._server_response else None
            encrypted_activation_metadata = self.encryption_manager.encrypt(json.dumps(self._activation_metadata)) if self._activation_metadata else None
            
            # Convert dates to strings
            activation_date_str = self._activation_date.isoformat() if self._activation_date else None
            last_validated_str = self._last_validated.isoformat() if self._last_validated else None
            expiry_date_str = self._expiry_date.isoformat() if self._expiry_date else None
            offline_grace_expires_str = self._offline_grace_expires.isoformat() if self._offline_grace_expires else None
            
            query = """
            INSERT OR REPLACE INTO license_activations (
                activation_id, license_key, license_id, activation_code, activation_type,
                hardware_fingerprint, hardware_bindings, activation_date, last_validated,
                expiry_date, validation_count, max_validations, status, activation_signature,
                validation_hash, machine_token, server_response, offline_grace_expires,
                is_trial_activation, trial_days_remaining, activation_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                self._activation_id, self._license_key, self._license_id, self._activation_code,
                self._activation_type, encrypted_hardware_fingerprint, encrypted_hardware_bindings,
                activation_date_str, last_validated_str, expiry_date_str, self._validation_count,
                self._max_validations, self._status, self._activation_signature, self._validation_hash,
                encrypted_machine_token, encrypted_server_response, offline_grace_expires_str,
                self._is_trial_activation, self._trial_days_remaining, encrypted_activation_metadata
            )
            
            self.db.execute_query(query, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error saving activation to database: {str(e)}")
            return False
    
    def load_from_database(self, activation_id: str) -> bool:
        """Load activation from database using activation ID"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM license_activations WHERE activation_id = ?"
            self.db.execute_query(query, (activation_id,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._activation_id = result[1]
            self._license_key = result[2]
            self._license_id = result[3]
            self._activation_code = result[4]
            self._activation_type = result[5]
            self._hardware_fingerprint = self.encryption_manager.decrypt(result[6]) if result[6] else None
            self._hardware_bindings = json.loads(self.encryption_manager.decrypt(result[7])) if result[7] else []
            self._activation_date = datetime.fromisoformat(result[8]) if result[8] else None
            self._last_validated = datetime.fromisoformat(result[9]) if result[9] else None
            self._expiry_date = datetime.fromisoformat(result[10]) if result[10] else None
            self._validation_count = result[11]
            self._max_validations = result[12]
            self._status = result[13]
            self._activation_signature = result[14]
            self._validation_hash = result[15]
            self._machine_token = self.encryption_manager.decrypt(result[16]) if result[16] else None
            self._server_response = json.loads(self.encryption_manager.decrypt(result[17])) if result[17] else None
            self._offline_grace_expires = datetime.fromisoformat(result[18]) if result[18] else None
            self._is_trial_activation = bool(result[19])
            self._trial_days_remaining = result[20]
            self._activation_metadata = json.loads(self.encryption_manager.decrypt(result[21])) if result[21] else {}
            
            return True
        except Exception as e:
            print(f"Error loading activation from database: {str(e)}")
            return False
    
    def load_by_license_key(self, license_key: str) -> bool:
        """Load activation from database using license key"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM license_activations WHERE license_key = ?"
            self.db.execute_query(query, (license_key,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._activation_id = result[1]
            self._license_key = result[2]
            self._license_id = result[3]
            self._activation_code = result[4]
            self._activation_type = result[5]
            self._hardware_fingerprint = self.encryption_manager.decrypt(result[6]) if result[6] else None
            self._hardware_bindings = json.loads(self.encryption_manager.decrypt(result[7])) if result[7] else []
            self._activation_date = datetime.fromisoformat(result[8]) if result[8] else None
            self._last_validated = datetime.fromisoformat(result[9]) if result[9] else None
            self._expiry_date = datetime.fromisoformat(result[10]) if result[10] else None
            self._validation_count = result[11]
            self._max_validations = result[12]
            self._status = result[13]
            self._activation_signature = result[14]
            self._validation_hash = result[15]
            self._machine_token = self.encryption_manager.decrypt(result[16]) if result[16] else None
            self._server_response = json.loads(self.encryption_manager.decrypt(result[17])) if result[17] else None
            self._offline_grace_expires = datetime.fromisoformat(result[18]) if result[18] else None
            self._is_trial_activation = bool(result[19])
            self._trial_days_remaining = result[20]
            self._activation_metadata = json.loads(self.encryption_manager.decrypt(result[21])) if result[21] else {}
            
            return True
        except Exception as e:
            print(f"Error loading activation by license key: {str(e)}")
            return False
    
    def export_activation_data(self) -> Dict[str, Any]:
        """Export activation data for backup or transfer"""
        return {
            'activation_id': self._activation_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'activation_code': self._activation_code,
            'activation_type': self._activation_type,
            'hardware_fingerprint': self._hardware_fingerprint,
            'hardware_bindings': self._hardware_bindings,
            'activation_date': self._activation_date.isoformat() if self._activation_date else None,
            'last_validated': self._last_validated.isoformat() if self._last_validated else None,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'validation_count': self._validation_count,
            'max_validations': self._max_validations,
            'status': self._status,
            'activation_signature': self._activation_signature,
            'validation_hash': self._validation_hash,
            'machine_token': self._machine_token,
            'offline_grace_expires': self._offline_grace_expires.isoformat() if self._offline_grace_expires else None,
            'is_trial_activation': self._is_trial_activation,
            'trial_days_remaining': self._trial_days_remaining,
            'activation_metadata': self._activation_metadata
        }
    
    def import_activation_data(self, activation_data: Dict[str, Any]) -> bool:
        """Import activation data from backup or transfer"""
        try:
            self._activation_id = activation_data.get('activation_id')
            self._license_key = activation_data.get('license_key')
            self._license_id = activation_data.get('license_id')
            self._activation_code = activation_data.get('activation_code')
            self._activation_type = activation_data.get('activation_type')
            self._hardware_fingerprint = activation_data.get('hardware_fingerprint')
            self._hardware_bindings = activation_data.get('hardware_bindings', [])
            self._activation_date = datetime.fromisoformat(activation_data['activation_date']) if activation_data.get('activation_date') else None
            self._last_validated = datetime.fromisoformat(activation_data['last_validated']) if activation_data.get('last_validated') else None
            self._expiry_date = datetime.fromisoformat(activation_data['expiry_date']) if activation_data.get('expiry_date') else None
            self._validation_count = activation_data.get('validation_count', 0)
            self._max_validations = activation_data.get('max_validations', 100)
            self._status = activation_data.get('status', self.STATUS_PENDING)
            self._activation_signature = activation_data.get('activation_signature')
            self._validation_hash = activation_data.get('validation_hash')
            self._machine_token = activation_data.get('machine_token')
            self._offline_grace_expires = datetime.fromisoformat(activation_data['offline_grace_expires']) if activation_data.get('offline_grace_expires') else None
            self._is_trial_activation = activation_data.get('is_trial_activation', False)
            self._trial_days_remaining = activation_data.get('trial_days_remaining', 0)
            self._activation_metadata = activation_data.get('activation_metadata', {})
            
            # Verify imported activation
            return self.is_valid()
        except Exception as e:
            print(f"Error importing activation data: {str(e)}")
            return False