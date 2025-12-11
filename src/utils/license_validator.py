"""
License Validator utility for POS MVP application
Handles online/offline validation with secure communication
"""

import os
import json
import time
import hashlib
import requests
import ssl
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple

from src.utils.license_crypto import LicenseCrypto
from src.utils.encryption import get_encryption_manager


class LicenseValidator:
    """
    License Validator for online/offline validation
    Implements secure communication with license server
    """
    
    # Validation endpoints
    ENDPOINT_VALIDATE = "/api/v1/validate"
    ENDPOINT_ACTIVATE = "/api/v1/activate"
    ENDPOINT_HEARTBEAT = "/api/v1/heartbeat"
    ENDPOINT_BLACKLIST = "/api/v1/blacklist"
    
    # Server URLs (would be configured in production)
    PRODUCTION_SERVER = "https://license.posmvp.com"
    STAGING_SERVER = "https://license-staging.posmvp.com"
    TEST_SERVER = "https://license-test.posmvp.com"
    
    # Validation modes
    MODE_ONLINE = "online"
    MODE_OFFLINE = "offline"
    MODE_HYBRID = "hybrid"
    
    # Response codes
    RESPONSE_SUCCESS = "success"
    RESPONSE_INVALID = "invalid"
    RESPONSE_EXPIRED = "expired"
    RESPONSE_REVOKED = "revoked"
    RESPONSE_BLACKLISTED = "blacklisted"
    RESPONSE_ERROR = "error"
    RESPONSE_RATE_LIMITED = "rate_limited"
    
    # HTTP status codes
    HTTP_OK = 200
    HTTP_UNAUTHORIZED = 401
    HTTP_FORBIDDEN = 403
    HTTP_NOT_FOUND = 404
    HTTP_RATE_LIMITED = 429
    HTTP_SERVER_ERROR = 500
    
    # Validation intervals (in seconds)
    ONLINE_INTERVAL = 86400  # 24 hours
    OFFLINE_GRACE = 259200  # 72 hours (3 days)
    HEARTBEAT_INTERVAL = 21600  # 6 hours
    
    def __init__(self, server_url: str = None, mode: str = MODE_HYBRID):
        """
        Initialize license validator
        
        Args:
            server_url: License server URL
            mode: Validation mode (online/offline/hybrid)
        """
        self.server_url = server_url or self.PRODUCTION_SERVER
        self.mode = mode
        self.encryption_manager = get_encryption_manager()
        self.license_crypto = LicenseCrypto()
        
        # SSL context for secure communication
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        
        # Request session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'POS-MVP-LicenseValidator/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Validation cache
        self._validation_cache = {}
        self._last_online_validation = None
        self._offline_grace_expires = None
        self._server_public_key = None
        
        # Load server public key
        self._load_server_public_key()
    
    def _load_server_public_key(self) -> None:
        """Load server public key for response verification"""
        try:
            # In production, this would be bundled with the application
            public_key_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'server_public_key.pem')
            
            if os.path.exists(public_key_file):
                with open(public_key_file, 'r') as f:
                    self._server_public_key = f.read()
            else:
                # For development, generate a test key
                self._server_public_key = self.license_crypto.get_public_key_pem()
        except Exception as e:
            print(f"Error loading server public key: {str(e)}")
            self._server_public_key = None
    
    def validate_license_online(self, license_key: str, activation_id: str,
                            hardware_fingerprint: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate license online with server
        
        Args:
            license_key: License key to validate
            activation_id: Activation ID
            hardware_fingerprint: Hardware fingerprint
            validation_data: Additional validation data
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': '',
                'server_data': None,
                'next_validation': None
            }
            
            # Prepare validation request
            request_data = {
                'license_key': license_key,
                'activation_id': activation_id,
                'hardware_fingerprint': hardware_fingerprint,
                'timestamp': datetime.now().isoformat(),
                'validation_data': validation_data or {}
            }
            
            # Add request signature
            request_json = json.dumps(request_data, sort_keys=True)
            request_signature = self.license_crypto.sign_data(request_json)
            request_data['signature'] = request_signature
            
            # Encrypt sensitive data
            encrypted_request = self._encrypt_request(request_data)
            
            # Send request to server
            url = f"{self.server_url}{self.ENDPOINT_VALIDATE}"
            response = self._send_request(url, encrypted_request)
            
            if not response:
                result['message'] = 'Failed to connect to license server.'
                return result
            
            # Process response
            if response['status_code'] == self.HTTP_OK:
                # Decrypt and verify response
                server_response = self._decrypt_response(response['data'])
                
                if not server_response:
                    result['message'] = 'Failed to decrypt server response.'
                    return result
                
                # Verify response signature
                if not self._verify_server_response(server_response):
                    result['message'] = 'Server response verification failed.'
                    return result
                
                # Process validation result
                validation_status = server_response.get('status', self.RESPONSE_ERROR)
                result['status'] = validation_status
                result['server_data'] = server_response.get('data', {})
                result['next_validation'] = server_response.get('next_validation')
                
                if validation_status == self.RESPONSE_SUCCESS:
                    result['success'] = True
                    result['message'] = 'License validation successful.'
                    self._last_online_validation = datetime.now()
                    self._offline_grace_expires = datetime.now() + timedelta(seconds=self.OFFLINE_GRACE)
                else:
                    result['message'] = self._get_status_message(validation_status, server_response)
            else:
                result['message'] = self._get_http_error_message(response['status_code'])
            
            return result
        except Exception as e:
            print(f"Error in online validation: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'Online validation error: {str(e)}',
                'server_data': None,
                'next_validation': None
            }
    
    def validate_license_offline(self, license_key: str, activation_id: str,
                             hardware_fingerprint: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate license offline with cached data
        
        Args:
            license_key: License key to validate
            activation_id: Activation ID
            hardware_fingerprint: Hardware fingerprint
            validation_data: Additional validation data
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': '',
                'grace_period_remaining': None
            }
            
            # Check if offline grace period has expired
            if self._offline_grace_expires and datetime.now() > self._offline_grace_expires:
                result['status'] = self.RESPONSE_ERROR
                result['message'] = 'Offline grace period expired. Online validation required.'
                return result
            
            # Check cache for recent validation
            cache_key = f"{license_key}_{activation_id}"
            if cache_key in self._validation_cache:
                cached_validation = self._validation_cache[cache_key]
                cache_time = cached_validation['timestamp']
                
                # Check if cache is still valid
                if datetime.now() - cache_time < timedelta(hours=1):
                    result['success'] = cached_validation['success']
                    result['status'] = cached_validation['status']
                    result['message'] = cached_validation['message']
                    
                    # Calculate grace period remaining
                    if self._offline_grace_expires:
                        grace_remaining = self._offline_grace_expires - datetime.now()
                        result['grace_period_remaining'] = int(grace_remaining.total_seconds())
                    
                    return result
            
            # Perform offline validation checks
            # This would involve checking local license data, signatures, etc.
            # For now, simulate offline validation
            
            # Simulate validation result
            offline_valid = True  # This would be determined by local checks
            
            if offline_valid:
                result['success'] = True
                result['status'] = self.RESPONSE_SUCCESS
                result['message'] = 'Offline validation successful.'
                
                # Cache validation result
                self._validation_cache[cache_key] = {
                    'success': True,
                    'status': self.RESPONSE_SUCCESS,
                    'message': 'Offline validation successful.',
                    'timestamp': datetime.now()
                }
                
                # Calculate grace period remaining
                if self._offline_grace_expires:
                    grace_remaining = self._offline_grace_expires - datetime.now()
                    result['grace_period_remaining'] = int(grace_remaining.total_seconds())
            else:
                result['status'] = self.RESPONSE_INVALID
                result['message'] = 'Offline validation failed.'
            
            return result
        except Exception as e:
            print(f"Error in offline validation: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'Offline validation error: {str(e)}',
                'grace_period_remaining': None
            }
    
    def validate_license_hybrid(self, license_key: str, activation_id: str,
                             hardware_fingerprint: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate license using hybrid approach (online with offline fallback)
        
        Args:
            license_key: License key to validate
            activation_id: Activation ID
            hardware_fingerprint: Hardware fingerprint
            validation_data: Additional validation data
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Try online validation first
            online_result = self.validate_license_online(
                license_key, activation_id, hardware_fingerprint, validation_data
            )
            
            if online_result['success']:
                return online_result
            
            # If online validation failed, try offline validation
            offline_result = self.validate_license_offline(
                license_key, activation_id, hardware_fingerprint, validation_data
            )
            
            # Add information about online failure
            if offline_result['success']:
                offline_result['message'] += ' (Online validation failed, using offline validation)'
                offline_result['online_failed'] = True
            else:
                offline_result['online_failed'] = True
            
            return offline_result
        except Exception as e:
            print(f"Error in hybrid validation: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'Hybrid validation error: {str(e)}',
                'online_failed': True
            }
    
    def activate_license_online(self, license_key: str, activation_code: str = None,
                           hardware_fingerprint: str = None, activation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Activate license online with server
        
        Args:
            license_key: License key to activate
            activation_code: Optional activation code
            hardware_fingerprint: Hardware fingerprint
            activation_data: Additional activation data
            
        Returns:
            Dictionary with activation result
        """
        try:
            result = {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': '',
                'license_data': None
            }
            
            # Prepare activation request
            request_data = {
                'license_key': license_key,
                'activation_code': activation_code,
                'hardware_fingerprint': hardware_fingerprint,
                'timestamp': datetime.now().isoformat(),
                'activation_data': activation_data or {}
            }
            
            # Add request signature
            request_json = json.dumps(request_data, sort_keys=True)
            request_signature = self.license_crypto.sign_data(request_json)
            request_data['signature'] = request_signature
            
            # Encrypt sensitive data
            encrypted_request = self._encrypt_request(request_data)
            
            # Send request to server
            url = f"{self.server_url}{self.ENDPOINT_ACTIVATE}"
            response = self._send_request(url, encrypted_request)
            
            if not response:
                result['message'] = 'Failed to connect to license server.'
                return result
            
            # Process response
            if response['status_code'] == self.HTTP_OK:
                # Decrypt and verify response
                server_response = self._decrypt_response(response['data'])
                
                if not server_response:
                    result['message'] = 'Failed to decrypt server response.'
                    return result
                
                # Verify response signature
                if not self._verify_server_response(server_response):
                    result['message'] = 'Server response verification failed.'
                    return result
                
                # Process activation result
                activation_status = server_response.get('status', self.RESPONSE_ERROR)
                result['status'] = activation_status
                result['license_data'] = server_response.get('data', {})
                
                if activation_status == self.RESPONSE_SUCCESS:
                    result['success'] = True
                    result['message'] = 'License activation successful.'
                else:
                    result['message'] = self._get_status_message(activation_status, server_response)
            else:
                result['message'] = self._get_http_error_message(response['status_code'])
            
            return result
        except Exception as e:
            print(f"Error in online activation: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'Online activation error: {str(e)}',
                'license_data': None
            }
    
    def send_heartbeat(self, license_key: str, activation_id: str,
                     usage_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Send heartbeat to license server
        
        Args:
            license_key: License key
            activation_id: Activation ID
            usage_data: Usage statistics
            
        Returns:
            Dictionary with heartbeat result
        """
        try:
            result = {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': ''
            }
            
            # Prepare heartbeat request
            request_data = {
                'license_key': license_key,
                'activation_id': activation_id,
                'timestamp': datetime.now().isoformat(),
                'usage_data': usage_data or {}
            }
            
            # Add request signature
            request_json = json.dumps(request_data, sort_keys=True)
            request_signature = self.license_crypto.sign_data(request_json)
            request_data['signature'] = request_signature
            
            # Encrypt sensitive data
            encrypted_request = self._encrypt_request(request_data)
            
            # Send request to server
            url = f"{self.server_url}{self.ENDPOINT_HEARTBEAT}"
            response = self._send_request(url, encrypted_request)
            
            if not response:
                result['message'] = 'Failed to connect to license server.'
                return result
            
            # Process response
            if response['status_code'] == self.HTTP_OK:
                # Decrypt and verify response
                server_response = self._decrypt_response(response['data'])
                
                if not server_response:
                    result['message'] = 'Failed to decrypt server response.'
                    return result
                
                # Verify response signature
                if not self._verify_server_response(server_response):
                    result['message'] = 'Server response verification failed.'
                    return result
                
                # Process heartbeat result
                heartbeat_status = server_response.get('status', self.RESPONSE_ERROR)
                result['status'] = heartbeat_status
                
                if heartbeat_status == self.RESPONSE_SUCCESS:
                    result['success'] = True
                    result['message'] = 'Heartbeat sent successfully.'
                else:
                    result['message'] = self._get_status_message(heartbeat_status, server_response)
            else:
                result['message'] = self._get_http_error_message(response['status_code'])
            
            return result
        except Exception as e:
            print(f"Error sending heartbeat: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'Heartbeat error: {str(e)}'
            }
    
    def check_blacklist(self, license_key: str = None, hardware_fingerprint: str = None) -> Dict[str, Any]:
        """
        Check if license or hardware is blacklisted
        
        Args:
            license_key: License key to check
            hardware_fingerprint: Hardware fingerprint to check
            
        Returns:
            Dictionary with blacklist check result
        """
        try:
            result = {
                'success': False,
                'blacklisted': False,
                'message': '',
                'blacklist_info': None
            }
            
            # Prepare blacklist request
            request_data = {
                'license_key': license_key,
                'hardware_fingerprint': hardware_fingerprint,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add request signature
            request_json = json.dumps(request_data, sort_keys=True)
            request_signature = self.license_crypto.sign_data(request_json)
            request_data['signature'] = request_signature
            
            # Encrypt sensitive data
            encrypted_request = self._encrypt_request(request_data)
            
            # Send request to server
            url = f"{self.server_url}{self.ENDPOINT_BLACKLIST}"
            response = self._send_request(url, encrypted_request)
            
            if not response:
                result['message'] = 'Failed to connect to license server.'
                return result
            
            # Process response
            if response['status_code'] == self.HTTP_OK:
                # Decrypt and verify response
                server_response = self._decrypt_response(response['data'])
                
                if not server_response:
                    result['message'] = 'Failed to decrypt server response.'
                    return result
                
                # Verify response signature
                if not self._verify_server_response(server_response):
                    result['message'] = 'Server response verification failed.'
                    return result
                
                # Process blacklist result
                blacklist_status = server_response.get('status', self.RESPONSE_ERROR)
                result['blacklisted'] = blacklist_status == self.RESPONSE_BLACKLISTED
                result['blacklist_info'] = server_response.get('data', {})
                
                if blacklist_status == self.RESPONSE_SUCCESS:
                    result['success'] = True
                    result['message'] = 'Not blacklisted.'
                elif blacklist_status == self.RESPONSE_BLACKLISTED:
                    result['success'] = True
                    result['message'] = 'License or hardware is blacklisted.'
                else:
                    result['message'] = self._get_status_message(blacklist_status, server_response)
            else:
                result['message'] = self._get_http_error_message(response['status_code'])
            
            return result
        except Exception as e:
            print(f"Error checking blacklist: {str(e)}")
            return {
                'success': False,
                'blacklisted': False,
                'message': f'Blacklist check error: {str(e)}',
                'blacklist_info': None
            }
    
    def _encrypt_request(self, request_data: Dict[str, Any]) -> str:
        """Encrypt request data for secure transmission"""
        try:
            # Convert to JSON
            request_json = json.dumps(request_data, sort_keys=True)
            
            # Encrypt with license crypto
            encrypted_data, key = self.license_crypto.encrypt_data(request_json)
            
            # Return encrypted data with key
            return json.dumps({
                'encrypted_data': encrypted_data,
                'encryption_key': key,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error encrypting request: {str(e)}")
            raise
    
    def _decrypt_response(self, encrypted_response: str) -> Dict[str, Any]:
        """Decrypt response data from server"""
        try:
            # Parse encrypted response
            response_data = json.loads(encrypted_response)
            
            # Extract encrypted data and key
            encrypted_data = response_data.get('encrypted_data')
            encryption_key = response_data.get('encryption_key')
            
            if not encrypted_data or not encryption_key:
                return None
            
            # Decrypt with license crypto
            decrypted_json = self.license_crypto.decrypt_data(encrypted_data, encryption_key)
            
            return json.loads(decrypted_json)
        except Exception as e:
            print(f"Error decrypting response: {str(e)}")
            return None
    
    def _verify_server_response(self, response_data: Dict[str, Any]) -> bool:
        """Verify server response signature"""
        try:
            if not self._server_public_key:
                # Skip verification if no public key
                return True
            
            # Extract signature
            signature = response_data.get('signature')
            if not signature:
                return False
            
            # Create response data for verification
            verify_data = {
                'status': response_data.get('status'),
                'data': response_data.get('data'),
                'timestamp': response_data.get('timestamp')
            }
            
            # Convert to JSON
            verify_json = json.dumps(verify_data, sort_keys=True)
            
            # Verify signature
            return self.license_crypto.verify_signature(verify_json, signature)
        except Exception as e:
            print(f"Error verifying server response: {str(e)}")
            return False
    
    def _send_request(self, url: str, data: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Send HTTP request to server"""
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=timeout,
                verify=self.ssl_context
            )
            
            return {
                'status_code': response.status_code,
                'data': response.text
            }
        except requests.exceptions.Timeout:
            print(f"Request timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error: {url}")
            return None
        except requests.exceptions.SSLError:
            print(f"SSL error: {url}")
            return None
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    def _get_status_message(self, status: str, response_data: Dict[str, Any]) -> str:
        """Get user-friendly message for status"""
        messages = {
            self.RESPONSE_SUCCESS: "Operation successful.",
            self.RESPONSE_INVALID: "Invalid license or activation data.",
            self.RESPONSE_EXPIRED: "License has expired.",
            self.RESPONSE_REVOKED: "License has been revoked.",
            self.RESPONSE_BLACKLISTED: "License is blacklisted.",
            self.RESPONSE_ERROR: "Server error occurred.",
            self.RESPONSE_RATE_LIMITED: "Too many requests. Please try again later."
        }
        
        # Get default message
        message = messages.get(status, "Unknown status.")
        
        # Add server message if available
        server_message = response_data.get('message')
        if server_message:
            message += f" Server message: {server_message}"
        
        return message
    
    def _get_http_error_message(self, status_code: int) -> str:
        """Get user-friendly message for HTTP error"""
        if status_code == self.HTTP_UNAUTHORIZED:
            return "Authentication failed."
        elif status_code == self.HTTP_FORBIDDEN:
            return "Access forbidden."
        elif status_code == self.HTTP_NOT_FOUND:
            return "Requested resource not found."
        elif status_code == self.HTTP_RATE_LIMITED:
            return "Too many requests. Please try again later."
        elif status_code >= self.HTTP_SERVER_ERROR:
            return "Server error. Please try again later."
        else:
            return f"HTTP error: {status_code}"
    
    def validate_license(self, license_key: str, activation_id: str,
                      hardware_fingerprint: str, validation_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate license using configured mode
        
        Args:
            license_key: License key to validate
            activation_id: Activation ID
            hardware_fingerprint: Hardware fingerprint
            validation_data: Additional validation data
            
        Returns:
            Dictionary with validation result
        """
        try:
            if self.mode == self.MODE_ONLINE:
                return self.validate_license_online(
                    license_key, activation_id, hardware_fingerprint, validation_data
                )
            elif self.mode == self.MODE_OFFLINE:
                return self.validate_license_offline(
                    license_key, activation_id, hardware_fingerprint, validation_data
                )
            elif self.mode == self.MODE_HYBRID:
                return self.validate_license_hybrid(
                    license_key, activation_id, hardware_fingerprint, validation_data
                )
            else:
                return {
                    'success': False,
                    'status': self.RESPONSE_ERROR,
                    'message': f'Invalid validation mode: {self.mode}'
                }
        except Exception as e:
            print(f"Error in license validation: {str(e)}")
            return {
                'success': False,
                'status': self.RESPONSE_ERROR,
                'message': f'License validation error: {str(e)}'
            }
    
    def set_server_url(self, server_url: str) -> None:
        """Set license server URL"""
        self.server_url = server_url
    
    def set_validation_mode(self, mode: str) -> bool:
        """Set validation mode"""
        if mode in [self.MODE_ONLINE, self.MODE_OFFLINE, self.MODE_HYBRID]:
            self.mode = mode
            return True
        return False
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status"""
        return {
            'mode': self.mode,
            'server_url': self.server_url,
            'last_online_validation': self._last_online_validation.isoformat() if self._last_online_validation else None,
            'offline_grace_expires': self._offline_grace_expires.isoformat() if self._offline_grace_expires else None,
            'cache_size': len(self._validation_cache),
            'server_public_key_loaded': self._server_public_key is not None
        }
    
    def clear_cache(self) -> None:
        """Clear validation cache"""
        self._validation_cache.clear()
    
    def is_online_validation_required(self) -> bool:
        """Check if online validation is required"""
        if not self._last_online_validation:
            return True
        
        time_since_validation = datetime.now() - self._last_online_validation
        return time_since_validation.total_seconds() > self.ONLINE_INTERVAL
    
    def is_offline_grace_expired(self) -> bool:
        """Check if offline grace period has expired"""
        if not self._offline_grace_expires:
            return False
        
        return datetime.now() > self._offline_grace_expires