"""
License Manager utility for POS MVP application
Handles multi-layered license validation with anti-cracking measures
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple

from src.models.license import License
from src.models.license_activation import LicenseActivation
from src.models.hardware_binding import HardwareBinding
from src.models.blacklisted_license import BlacklistedLicense
from src.models.license_audit_log import LicenseAuditLog
from src.utils.license_crypto import LicenseCrypto
from src.utils.hardware_fingerprint import HardwareFingerprint
from src.utils.license_storage import LicenseStorage
from src.utils.anti_tamper import AntiTamper
from src.utils.encryption import get_encryption_manager


class LicenseManager:
    """
    License Manager for multi-layered license validation
    Implements comprehensive anti-cracking measures
    """
    
    # Validation levels
    VALIDATION_BASIC = "basic"
    VALIDATION_STANDARD = "standard"
    VALIDATION_ADVANCED = "advanced"
    VALIDATION_STEALTH = "stealth"
    
    # Validation results
    RESULT_VALID = "valid"
    RESULT_INVALID = "invalid"
    RESULT_EXPIRED = "expired"
    RESULT_REVOKED = "revoked"
    RESULT_BLACKLISTED = "blacklisted"
    RESULT_TAMPERED = "tampered"
    RESULT_OFFLINE_GRACE = "offline_grace"
    RESULT_ONLINE_REQUIRED = "online_required"
    
    # Validation intervals (in hours)
    ONLINE_VALIDATION_INTERVAL = 24
    OFFLINE_GRACE_PERIOD = 72  # 3 days
    HEARTBEAT_INTERVAL = 6  # 6 hours
    
    def __init__(self, db_manager=None):
        """Initialize license manager"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        self.license_crypto = LicenseCrypto()
        self.hardware_fingerprint = HardwareFingerprint()
        self.license_storage = LicenseStorage()
        self.anti_tamper = AntiTamper()
        
        # License instances
        self._license = License(db_manager)
        self._activation = LicenseActivation(db_manager)
        self._hardware_binding = HardwareBinding(db_manager)
        self._blacklisted_license = BlacklistedLicense(db_manager)
        self._audit_log = LicenseAuditLog(db_manager)
        
        # Validation state
        self._validation_cache = {}
        self._last_validation = None
        self._validation_level = self.VALIDATION_ADVANCED
        self._validation_thread = None
        self._validation_lock = threading.Lock()
        
        # Initialize anti-tamper
        self._init_anti_tamper()
        
        # Start background validation thread
        self._start_validation_thread()
    
    def _init_anti_tamper(self) -> None:
        """Initialize anti-tamper protection"""
        try:
            # Calculate code integrity hash
            self.anti_tamper.calculate_integrity_hash()
            
            # Set up tamper detection
            self.anti_tamper.setup_tamper_detection()
        except Exception as e:
            print(f"Error initializing anti-tamper: {str(e)}")
    
    def _start_validation_thread(self) -> None:
        """Start background validation thread"""
        try:
            if self._validation_thread is None or not self._validation_thread.is_alive():
                self._validation_thread = threading.Thread(
                    target=self._validation_worker,
                    daemon=True
                )
                self._validation_thread.start()
        except Exception as e:
            print(f"Error starting validation thread: {str(e)}")
    
    def _validation_worker(self) -> None:
        """Background validation worker thread"""
        while True:
            try:
                # Sleep for heartbeat interval
                time.sleep(self.HEARTBEAT_INTERVAL * 3600)
                
                # Perform periodic validation
                with self._validation_lock:
                    if self._is_license_loaded():
                        self._perform_periodic_validation()
            except Exception as e:
                print(f"Error in validation worker: {str(e)}")
    
    def _is_license_loaded(self) -> bool:
        """Check if license is loaded"""
        return (self._license._license_key is not None and 
                self._activation._activation_id is not None)
    
    def _perform_periodic_validation(self) -> None:
        """Perform periodic license validation"""
        try:
            # Check if online validation is needed
            if self._needs_online_validation():
                result = self.validate_license(online=True)
                if result['status'] != self.RESULT_VALID:
                    # Log validation failure
                    self._log_validation_event(result)
            else:
                # Perform offline validation
                result = self.validate_license(online=False)
                if result['status'] != self.RESULT_VALID:
                    # Log validation failure
                    self._log_validation_event(result)
        except Exception as e:
            print(f"Error performing periodic validation: {str(e)}")
    
    def _needs_online_validation(self) -> bool:
        """Check if online validation is needed"""
        try:
            if not self._last_validation:
                return True
            
            # Check if online validation interval has passed
            time_since_validation = datetime.now() - self._last_validation
            return time_since_validation.total_seconds() > self.ONLINE_VALIDATION_INTERVAL * 3600
        except Exception as e:
            print(f"Error checking online validation need: {str(e)}")
            return True
    
    def _log_validation_event(self, result: Dict[str, Any]) -> None:
        """Log validation event"""
        try:
            event_data = {
                'license_id': self._license._license_id,
                'activation_id': self._activation._activation_id,
                'description': f"License validation: {result['status']}",
                'previous_state': {'last_validation': self._last_validation.isoformat() if self._last_validation else None},
                'new_state': {'validation_status': result['status']},
                'success': result['status'] == self.RESULT_VALID,
                'error_message': result.get('message'),
                'hardware_fingerprint': self.hardware_fingerprint.get_fingerprint()
            }
            
            event_type = LicenseAuditLog.EVENT_LICENSE_VALIDATED
            if result['status'] == self.RESULT_INVALID:
                event_type = LicenseAuditLog.EVENT_VALIDATION_FAILED
            elif result['status'] == self.RESULT_TAMPERED:
                event_type = LicenseAuditLog.EVENT_TAMPER_DETECTED
            
            self._audit_log.log_event(
                self._license._license_key,
                event_type,
                event_data,
                LicenseAuditLog.SEVERITY_ERROR if result['status'] != self.RESULT_VALID else LicenseAuditLog.SEVERITY_INFO
            )
        except Exception as e:
            print(f"Error logging validation event: {str(e)}")
    
    def activate_license(self, license_key: str, activation_code: str = None,
                       online: bool = True) -> Dict[str, Any]:
        """
        Activate a license
        
        Args:
            license_key: License key to activate
            activation_code: Optional activation code
            online: Whether to perform online activation
            
        Returns:
            Dictionary with activation result
        """
        try:
            result = {
                'success': False,
                'status': self.RESULT_INVALID,
                'message': '',
                'license_info': None,
                'activation_info': None
            }
            
            # Check for tampering
            if self.anti_tamper.is_tampered():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Code tampering detected. License activation failed.'
                self._audit_log.log_event(
                    license_key,
                    LicenseAuditLog.EVENT_TAMPER_DETECTED,
                    {'message': 'Tampering detected during license activation'},
                    LicenseAuditLog.SEVERITY_CRITICAL
                )
                return result
            
            # Check if license is blacklisted
            if self._blacklisted_license.load_by_license_key(license_key):
                if self._blacklisted_license.is_blacklisted(license_key):
                    result['status'] = self.RESULT_BLACKLISTED
                    result['message'] = 'License is blacklisted and cannot be activated.'
                    self._audit_log.log_event(
                        license_key,
                        LicenseAuditLog.EVENT_BLACKLISTED,
                        {'message': 'Attempted to activate blacklisted license'},
                        LicenseAuditLog.SEVERITY_ERROR
                    )
                    return result
            
            # Load license
            if not self._license.load_from_database(license_key):
                # License not found in database, try online activation
                if online:
                    online_result = self._online_activation(license_key, activation_code)
                    if not online_result['success']:
                        result['message'] = online_result['message']
                        return result
                    
                    # Load license after online activation
                    if not self._license.load_from_database(license_key):
                        result['message'] = 'Failed to load license after online activation.'
                        return result
                else:
                    result['message'] = 'License not found and offline activation not available.'
                    return result
            
            # Check if license is valid
            if not self._license.is_valid():
                if self._license.is_expired():
                    result['status'] = self.RESULT_EXPIRED
                    result['message'] = 'License has expired.'
                else:
                    result['status'] = self.RESULT_REVOKED
                    result['message'] = 'License has been revoked.'
                return result
            
            # Create activation
            activation_type = LicenseActivation.TYPE_ONLINE if online else LicenseActivation.TYPE_OFFLINE
            if not self._activation.create_activation(license_key, self._license._license_id, activation_type):
                result['message'] = 'Failed to create license activation.'
                return result
            
            # Generate hardware fingerprint
            fingerprint_data = self.hardware_fingerprint.generate_fingerprint(
                HardwareFingerprint.METHOD_ADVANCED
            )
            fingerprint_hash = fingerprint_data.get('hash')
            
            # Save hardware binding
            if not self._hardware_binding.generate_fingerprint(HardwareBinding.METHOD_ADVANCED):
                result['message'] = 'Failed to generate hardware binding.'
                return result
            
            # Save activation to database
            if not self._activation.save_to_database():
                result['message'] = 'Failed to save activation to database.'
                return result
            
            # Save hardware binding to database
            if not self._hardware_binding.save_to_database():
                result['message'] = 'Failed to save hardware binding to database.'
                return result
            
            # Store license fragments
            if not self.license_storage.store_license_fragments(self._license, self._activation):
                result['message'] = 'Failed to store license fragments.'
                return result
            
            # Update license activation count
            if not self._license.increment_activation_count():
                result['message'] = 'Maximum activation limit reached.'
                return result
            
            # Save updated license
            if not self._license.save_to_database():
                result['message'] = 'Failed to save updated license.'
                return result
            
            # Log successful activation
            self._audit_log.log_event(
                license_key,
                LicenseAuditLog.EVENT_LICENSE_ACTIVATED,
                {
                    'license_id': self._license._license_id,
                    'activation_id': self._activation._activation_id,
                    'activation_type': activation_type,
                    'hardware_fingerprint': fingerprint_hash,
                    'description': 'License activated successfully'
                },
                LicenseAuditLog.SEVERITY_INFO
            )
            
            result['success'] = True
            result['status'] = self.RESULT_VALID
            result['message'] = 'License activated successfully.'
            result['license_info'] = self._license.get_license_info()
            result['activation_info'] = self._activation.get_activation_info()
            
            # Update last validation time
            self._last_validation = datetime.now()
            
            return result
        except Exception as e:
            print(f"Error activating license: {str(e)}")
            return {
                'success': False,
                'status': self.RESULT_INVALID,
                'message': f'License activation error: {str(e)}',
                'license_info': None,
                'activation_info': None
            }
    
    def _online_activation(self, license_key: str, activation_code: str = None) -> Dict[str, Any]:
        """
        Perform online license activation
        
        Args:
            license_key: License key to activate
            activation_code: Optional activation code
            
        Returns:
            Dictionary with online activation result
        """
        try:
            # This would connect to the license server
            # For now, simulate online activation
            
            result = {
                'success': False,
                'message': ''
            }
            
            # Simulate server validation
            if len(license_key) < 20:
                result['message'] = 'Invalid license key format.'
                return result
            
            # Create license data (simulated server response)
            license_data = {
                'license_key': license_key,
                'license_id': self._license._generate_license_id(),
                'customer_name': 'Test Customer',
                'customer_email': 'test@example.com',
                'license_type': License.TYPE_PROFESSIONAL,
                'features': License.FEATURES[License.TYPE_PROFESSIONAL],
                'maintenance_days': 365,
                'max_activations': 3,
                'offline_grace_period_days': 30
            }
            
            # Create license
            if not self._license.create_license(license_data):
                result['message'] = 'Failed to create license from server response.'
                return result
            
            # Save license to database
            if not self._license.save_to_database():
                result['message'] = 'Failed to save license to database.'
                return result
            
            result['success'] = True
            result['message'] = 'Online activation successful.'
            
            return result
        except Exception as e:
            print(f"Error in online activation: {str(e)}")
            return {
                'success': False,
                'message': f'Online activation error: {str(e)}'
            }
    
    def validate_license(self, online: bool = False, force: bool = False) -> Dict[str, Any]:
        """
        Validate license with multi-layered checks
        
        Args:
            online: Whether to perform online validation
            force: Whether to force validation
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = {
                'status': self.RESULT_INVALID,
                'message': '',
                'license_info': None,
                'validation_level': self._validation_level,
                'timestamp': datetime.now().isoformat()
            }
            
            # Check cache first
            if not force:
                cache_key = f"validation_{online}"
                if cache_key in self._validation_cache:
                    cached_result = self._validation_cache[cache_key]
                    # Check if cache is still valid
                    cache_time = datetime.fromisoformat(cached_result['timestamp'])
                    if datetime.now() - cache_time < timedelta(minutes=5):
                        return cached_result
            
            # Check for tampering
            if self.anti_tamper.is_tampered():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Code tampering detected. License validation failed.'
                self._audit_log.log_event(
                    self._license._license_key or 'unknown',
                    LicenseAuditLog.EVENT_TAMPER_DETECTED,
                    {'message': 'Tampering detected during license validation'},
                    LicenseAuditLog.SEVERITY_CRITICAL
                )
                return result
            
            # Load license fragments if not loaded
            if not self._is_license_loaded():
                if not self.license_storage.load_license_fragments(self._license, self._activation):
                    result['message'] = 'No valid license found.'
                    return result
            
            # Check if license is blacklisted
            if self._blacklisted_license.load_by_license_key(self._license._license_key):
                if self._blacklisted_license.is_blacklisted(self._license._license_key):
                    result['status'] = self.RESULT_BLACKLISTED
                    result['message'] = 'License is blacklisted.'
                    return result
            
            # Perform validation based on level
            if self._validation_level == self.VALIDATION_BASIC:
                validation_result = self._validate_basic()
            elif self._validation_level == self.VALIDATION_STANDARD:
                validation_result = self._validate_standard()
            elif self._validation_level == self.VALIDATION_ADVANCED:
                validation_result = self._validate_advanced()
            elif self._validation_level == self.VALIDATION_STEALTH:
                validation_result = self._validate_stealth()
            else:
                validation_result = self._validate_advanced()
            
            # Update result with validation result
            result.update(validation_result)
            
            # Perform online validation if requested
            if online and result['status'] == self.RESULT_VALID:
                online_result = self._validate_online()
                if online_result['status'] != self.RESULT_VALID:
                    result.update(online_result)
            
            # Update license and activation timestamps
            if result['status'] == self.RESULT_VALID:
                self._license.update_validation_timestamp()
                self._activation.validate_activation()
                self._license.save_to_database()
                self._activation.save_to_database()
                
                # Update last validation time
                self._last_validation = datetime.now()
            
            # Cache result
            self._validation_cache[f"validation_{online}"] = result
            
            return result
        except Exception as e:
            print(f"Error validating license: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'License validation error: {str(e)}',
                'license_info': None,
                'validation_level': self._validation_level,
                'timestamp': datetime.now().isoformat()
            }
    
    def _validate_basic(self) -> Dict[str, Any]:
        """Perform basic license validation"""
        try:
            result = {
                'status': self.RESULT_VALID,
                'message': 'Basic validation passed.'
            }
            
            # Check license validity
            if not self._license.is_valid():
                if self._license.is_expired():
                    result['status'] = self.RESULT_EXPIRED
                    result['message'] = 'License has expired.'
                else:
                    result['status'] = self.RESULT_REVOKED
                    result['message'] = 'License has been revoked.'
                return result
            
            # Check activation validity
            if not self._activation.is_valid():
                result['status'] = self.RESULT_INVALID
                result['message'] = 'License activation is invalid.'
                return result
            
            return result
        except Exception as e:
            print(f"Error in basic validation: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'Basic validation error: {str(e)}'
            }
    
    def _validate_standard(self) -> Dict[str, Any]:
        """Perform standard license validation"""
        try:
            # Start with basic validation
            result = self._validate_basic()
            if result['status'] != self.RESULT_VALID:
                return result
            
            # Check hardware binding
            if not self._activation.is_valid_hardware():
                result['status'] = self.RESULT_INVALID
                result['message'] = 'Hardware binding validation failed.'
                return result
            
            # Check license signature
            if not self._license.verify_signature():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'License signature verification failed.'
                return result
            
            result['message'] = 'Standard validation passed.'
            return result
        except Exception as e:
            print(f"Error in standard validation: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'Standard validation error: {str(e)}'
            }
    
    def _validate_advanced(self) -> Dict[str, Any]:
        """Perform advanced license validation"""
        try:
            # Start with standard validation
            result = self._validate_standard()
            if result['status'] != self.RESULT_VALID:
                return result
            
            # Check license integrity
            if not self._license.verify_integrity():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'License integrity verification failed.'
                return result
            
            # Check activation signature
            if not self._activation.verify_activation_signature():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Activation signature verification failed.'
                return result
            
            # Check hardware binding integrity
            if not self._hardware_binding.verify_binding():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Hardware binding integrity verification failed.'
                return result
            
            # Check anti-tamper hash
            if not self._hardware_binding.verify_anti_tamper():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Anti-tamper verification failed.'
                return result
            
            # Check if online validation is needed
            if self._activation.needs_online_validation():
                result['status'] = self.RESULT_ONLINE_REQUIRED
                result['message'] = 'Online validation required.'
                return result
            
            result['message'] = 'Advanced validation passed.'
            return result
        except Exception as e:
            print(f"Error in advanced validation: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'Advanced validation error: {str(e)}'
            }
    
    def _validate_stealth(self) -> Dict[str, Any]:
        """Perform stealth license validation"""
        try:
            # Start with advanced validation
            result = self._validate_advanced()
            if result['status'] != self.RESULT_VALID:
                return result
            
            # Additional stealth checks
            # Check for debugging
            if self.anti_tamper.is_debugger_attached():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Debugger detected. License validation failed.'
                return result
            
            # Check for virtualization
            if self.anti_tamper.is_virtual_environment():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Virtual environment detected. License validation failed.'
                return result
            
            # Check for code injection
            if self.anti_tamper.is_code_injected():
                result['status'] = self.RESULT_TAMPERED
                result['message'] = 'Code injection detected. License validation failed.'
                return result
            
            result['message'] = 'Stealth validation passed.'
            return result
        except Exception as e:
            print(f"Error in stealth validation: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'Stealth validation error: {str(e)}'
            }
    
    def _validate_online(self) -> Dict[str, Any]:
        """Perform online license validation"""
        try:
            result = {
                'status': self.RESULT_VALID,
                'message': 'Online validation passed.'
            }
            
            # This would connect to the license server
            # For now, simulate online validation
            
            # Simulate server check
            if not self._license._license_key or len(self._license._license_key) < 20:
                result['status'] = self.RESULT_INVALID
                result['message'] = 'Invalid license key for online validation.'
                return result
            
            # Check if license is still valid on server
            # Simulate server response
            server_valid = True  # This would be determined by the server
            
            if not server_valid:
                result['status'] = self.RESULT_REVOKED
                result['message'] = 'License revoked by server.'
                return result
            
            # Update server validation token
            self._activation._server_response = {
                'validated_at': datetime.now().isoformat(),
                'server_status': 'valid',
                'next_validation': (datetime.now() + timedelta(hours=self.ONLINE_VALIDATION_INTERVAL)).isoformat()
            }
            
            # Reset validation count
            self._activation._validation_count = 0
            
            # Extend offline grace period
            self._activation._offline_grace_expires = datetime.now() + timedelta(days=3)
            
            result['message'] = 'Online validation successful.'
            return result
        except Exception as e:
            print(f"Error in online validation: {str(e)}")
            return {
                'status': self.RESULT_INVALID,
                'message': f'Online validation error: {str(e)}'
            }
    
    def deactivate_license(self) -> Dict[str, Any]:
        """Deactivate current license"""
        try:
            result = {
                'success': False,
                'message': ''
            }
            
            if not self._is_license_loaded():
                result['message'] = 'No license to deactivate.'
                return result
            
            # Log deactivation
            self._audit_log.log_event(
                self._license._license_key,
                LicenseAuditLog.EVENT_LICENSE_REVOKED,
                {
                    'license_id': self._license._license_id,
                    'activation_id': self._activation._activation_id,
                    'description': 'License deactivated by user'
                },
                LicenseAuditLog.SEVERITY_INFO
            )
            
            # Deactivate activation
            self._activation.revoke()
            self._activation.save_to_database()
            
            # Clear license fragments
            self.license_storage.clear_license_fragments()
            
            # Clear validation cache
            self._validation_cache.clear()
            
            # Reset license instances
            self._license = License(self.db)
            self._activation = LicenseActivation(self.db)
            
            result['success'] = True
            result['message'] = 'License deactivated successfully.'
            
            return result
        except Exception as e:
            print(f"Error deactivating license: {str(e)}")
            return {
                'success': False,
                'message': f'License deactivation error: {str(e)}'
            }
    
    def get_license_status(self) -> Dict[str, Any]:
        """Get current license status"""
        try:
            if not self._is_license_loaded():
                return {
                    'status': 'not_activated',
                    'message': 'No license activated.',
                    'license_info': None,
                    'activation_info': None
                }
            
            # Perform quick validation
            validation_result = self.validate_license(online=False)
            
            return {
                'status': validation_result['status'],
                'message': validation_result['message'],
                'license_info': self._license.get_license_info(),
                'activation_info': self._activation.get_activation_info(),
                'last_validation': self._last_validation.isoformat() if self._last_validation else None,
                'validation_level': self._validation_level
            }
        except Exception as e:
            print(f"Error getting license status: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error getting license status: {str(e)}',
                'license_info': None,
                'activation_info': None
            }
    
    def check_feature_access(self, feature: str) -> Dict[str, Any]:
        """Check if a feature is available"""
        try:
            result = {
                'allowed': False,
                'reason': '',
                'license_type': None
            }
            
            if not self._is_license_loaded():
                result['reason'] = 'No license activated.'
                return result
            
            # Validate license first
            validation_result = self.validate_license(online=False)
            if validation_result['status'] != self.RESULT_VALID:
                result['reason'] = validation_result['message']
                return result
            
            # Check feature access
            if self._license.has_feature(feature):
                result['allowed'] = True
                result['license_type'] = self._license._license_type
            else:
                result['reason'] = f'Feature "{feature}" not available in {self._license._license_type} license.'
                result['license_type'] = self._license._license_type
            
            return result
        except Exception as e:
            print(f"Error checking feature access: {str(e)}")
            return {
                'allowed': False,
                'reason': f'Error checking feature access: {str(e)}',
                'license_type': None
            }
    
    def set_validation_level(self, level: str) -> bool:
        """Set license validation level"""
        try:
            if level in [self.VALIDATION_BASIC, self.VALIDATION_STANDARD, 
                        self.VALIDATION_ADVANCED, self.VALIDATION_STEALTH]:
                self._validation_level = level
                # Clear validation cache to force revalidation
                self._validation_cache.clear()
                return True
            return False
        except Exception as e:
            print(f"Error setting validation level: {str(e)}")
            return False
    
    def get_audit_logs(self, license_key: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get license audit logs"""
        try:
            if license_key:
                return self._audit_log.get_license_events(license_key, limit=100)
            else:
                # Get security events
                return self._audit_log.get_security_events(hours=days*24)
        except Exception as e:
            print(f"Error getting audit logs: {str(e)}")
            return []
    
    def get_trial_status(self) -> Dict[str, Any]:
        """
        Get current trial status
        
        Returns:
            Dictionary with trial status information
        """
        try:
            result = {
                'trial_info': {
                    'status': 'available',
                    'days_remaining': 0,
                    'started_date': None,
                    'expires_date': None,
                    'features': []
                },
                'activation_info': {
                    'trial_activated': False,
                    'activation_id': None
                }
            }
            
            # Check if license is loaded
            if self._is_license_loaded():
                # Get license info
                license_info = self._license.get_license_info()
                activation_info = self._activation.get_activation_info()
                
                # Check if it's a trial license
                if license_info and license_info.get('license_type') == 'trial':
                    # Calculate days remaining
                    started_date = activation_info.get('created_at')
                    expires_date = activation_info.get('expires_at')
                    
                    if expires_date:
                        expires = datetime.fromisoformat(expires_date.replace('Z', '+00:00'))
                        days_remaining = (expires - datetime.now()).days
                        if days_remaining < 0:
                            days_remaining = 0
                        
                        result['trial_info'] = {
                            'status': 'active' if days_remaining > 0 else 'expired',
                            'days_remaining': days_remaining,
                            'started_date': started_date,
                            'expires_date': expires_date,
                            'features': license_info.get('features', [])
                        }
                        
                        result['activation_info'] = {
                            'trial_activated': True,
                            'activation_id': activation_info.get('id')
                        }
                    else:
                        result['trial_info']['status'] = 'active'
                else:
                    # Trial not activated, check if available
                    result['trial_info']['status'] = 'available'
                    result['trial_info']['days_remaining'] = 30  # Default 30-day trial
                    result['trial_info']['features'] = [
                        'basic_orders', 'basic_inventory', 'basic_reports',
                        'customer_support', 'data_export'
                    ]
            else:
                # No license, trial is available
                result['trial_info']['status'] = 'available'
                result['trial_info']['days_remaining'] = 30  # Default 30-day trial
                result['trial_info']['features'] = [
                    'basic_orders', 'basic_inventory', 'basic_reports',
                    'customer_support', 'data_export'
                ]
            
            return result
        except Exception as e:
            print(f"Error getting trial status: {str(e)}")
            return {
                'trial_info': {
                    'status': 'error',
                    'days_remaining': 0,
                    'started_date': None,
                    'expires_date': None,
                    'features': []
                },
                'activation_info': {
                    'trial_activated': False,
                    'activation_id': None
                }
            }
    
    def request_trial_extension(self, reason: str) -> Dict[str, Any]:
        """
        Request a trial extension
        
        Args:
            reason: Reason for extension request
            
        Returns:
            Dictionary with extension request result
        """
        try:
            result = {
                'success': False,
                'message': '',
                'extension_days': 0
            }
            
            # Simulate extension request
            # In a real implementation, this would contact the license server
            if len(reason) < 10:
                result['message'] = 'Please provide a detailed reason for the extension request.'
                return result
            
            # Grant 7-day extension
            extension_days = 7
            
            # Update trial expiration if active
            if self._is_license_loaded():
                activation_info = self._activation.get_activation_info()
                if activation_info and activation_info.get('expires_at'):
                    current_expires = datetime.fromisoformat(activation_info['expires_at'].replace('Z', '+00:00'))
                    new_expires = current_expires + timedelta(days=extension_days)
                    
                    # Update activation
                    self._activation._expires_at = new_expires.isoformat()
                    self._activation.save_to_database()
                    
                    # Log extension
                    self._audit_log.log_event(
                        self._license._license_key or 'trial',
                        LicenseAuditLog.EVENT_LICENSE_VALIDATED,
                        {
                            'description': f'Trial extended by {extension_days} days',
                            'reason': reason,
                            'previous_expires': activation_info['expires_at'],
                            'new_expires': new_expires.isoformat()
                        },
                        LicenseAuditLog.SEVERITY_INFO
                    )
                    
                    result['success'] = True
                    result['message'] = f'Trial extended by {extension_days} days.'
                    result['extension_days'] = extension_days
                else:
                    result['message'] = 'No active trial found to extend.'
            else:
                result['message'] = 'No active trial found to extend.'
            
            return result
        except Exception as e:
            print(f"Error requesting trial extension: {str(e)}")
            return {
                'success': False,
                'message': f'Error requesting trial extension: {str(e)}',
                'extension_days': 0
            }
    
    def cleanup(self) -> None:
        """Cleanup license manager resources"""
        try:
            # Stop validation thread
            if self._validation_thread and self._validation_thread.is_alive():
                # Thread will stop on next iteration
                pass
            
            # Clear caches
            self._validation_cache.clear()
            self.hardware_fingerprint.clear_cache()
            
            # Cleanup old audit logs
            self._audit_log.cleanup_old_logs(days=365)
            
            # Cleanup expired blacklists
            self._blacklisted_license.cleanup_expired_blacklists()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")