"""
License Storage utility for POS MVP application
Handles fragmented storage of license data with anti-cracking measures
"""

import os
import json
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple

from src.models.license import License
from src.models.license_activation import LicenseActivation
from src.utils.encryption import get_encryption_manager
from src.utils.license_crypto import LicenseCrypto


class LicenseStorage:
    """
    License Storage utility for fragmented license data
    Implements secure storage with anti-cracking measures
    """
    
    # Storage locations
    LOCATION_REGISTRY = "registry"
    LOCATION_FILE = "file"
    LOCATION_ENVIRONMENT = "environment"
    LOCATION_MULTIPLE = "multiple"
    
    # Fragmentation methods
    FRAGMENTATION_SIMPLE = "simple"
    FRAGMENTATION_ADVANCED = "advanced"
    FRAGMENTATION_STEALTH = "stealth"
    
    # Storage paths
    STORAGE_DIR = os.path.join(os.path.expanduser("~"), ".posmvp_license")
    FRAGMENT_DIR = os.path.join(STORAGE_DIR, "fragments")
    BACKUP_DIR = os.path.join(STORAGE_DIR, "backups")
    
    # Fragment names
    FRAGMENT_PRIMARY = "primary"
    FRAGMENT_SECONDARY = "secondary"
    FRAGMENT_TERTIARY = "tertiary"
    FRAGMENT_BACKUP = "backup"
    
    # Fragment types
    TYPE_LICENSE_DATA = "license_data"
    TYPE_ACTIVATION_DATA = "activation_data"
    TYPE_SIGNATURE = "signature"
    TYPE_METADATA = "metadata"
    
    def __init__(self, storage_method: str = LOCATION_MULTIPLE, 
                 fragmentation_method: str = FRAGMENTATION_ADVANCED):
        """
        Initialize license storage
        
        Args:
            storage_method: Storage method to use
            fragmentation_method: Fragmentation method to use
        """
        self.storage_method = storage_method
        self.fragmentation_method = fragmentation_method
        self.encryption_manager = get_encryption_manager()
        self.license_crypto = LicenseCrypto()
        
        # Storage directories
        self._ensure_directories()
        
        # Fragment data
        self._fragments = {}
        self._fragment_keys = {}
        self._fragment_locations = {}
        
        # Initialize fragment keys
        self._init_fragment_keys()
        
        # Load existing fragments
        self._load_fragments()
    
    def _ensure_directories(self) -> None:
        """Ensure storage directories exist"""
        try:
            os.makedirs(self.STORAGE_DIR, exist_ok=True)
            os.makedirs(self.FRAGMENT_DIR, exist_ok=True)
            os.makedirs(self.BACKUP_DIR, exist_ok=True)
            
            # Set directory permissions (read/write for owner only)
            os.chmod(self.STORAGE_DIR, 0o700)
            os.chmod(self.FRAGMENT_DIR, 0o700)
            os.chmod(self.BACKUP_DIR, 0o700)
        except Exception as e:
            print(f"Error ensuring directories: {str(e)}")
    
    def _init_fragment_keys(self) -> None:
        """Initialize fragment keys for encryption"""
        try:
            # Generate or load fragment keys
            keys_file = os.path.join(self.STORAGE_DIR, "fragment_keys.json")
            
            if os.path.exists(keys_file):
                # Load existing keys
                with open(keys_file, 'r') as f:
                    self._fragment_keys = json.load(f)
            else:
                # Generate new keys
                self._fragment_keys = {
                    'primary_key': base64.b64encode(secrets.token_bytes(32)).decode(),
                    'secondary_key': base64.b64encode(secrets.token_bytes(32)).decode(),
                    'tertiary_key': base64.b64encode(secrets.token_bytes(32)).decode(),
                    'backup_key': base64.b64encode(secrets.token_bytes(32)).decode(),
                    'salt': base64.b64encode(secrets.token_bytes(16)).decode()
                }
                
                # Save keys
                with open(keys_file, 'w') as f:
                    json.dump(self._fragment_keys, f)
                
                # Set file permissions
                os.chmod(keys_file, 0o600)
        except Exception as e:
            print(f"Error initializing fragment keys: {str(e)}")
    
    def _get_fragment_key(self, fragment_name: str) -> bytes:
        """Get encryption key for fragment"""
        try:
            key_name = f"{fragment_name}_key"
            key_b64 = self._fragment_keys.get(key_name)
            
            if not key_b64:
                return None
            
            # Derive key with salt
            salt = base64.b64decode(self._fragment_keys['salt'])
            key_data = base64.b64decode(key_b64)
            
            # Use PBKDF2 to derive final key
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.backends import default_backend
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=10000,
                backend=default_backend()
            )
            
            return kdf.derive(key_data)
        except Exception as e:
            print(f"Error getting fragment key: {str(e)}")
            return None
    
    def _get_fragment_path(self, fragment_name: str, fragment_type: str) -> str:
        """Get file path for fragment"""
        try:
            # Generate fragment filename
            fragment_hash = hashlib.sha256(f"{fragment_name}_{fragment_type}".encode()).hexdigest()[:16]
            filename = f"fragment_{fragment_hash}.dat"
            
            # Determine location based on storage method
            if self.storage_method == self.LOCATION_FILE:
                return os.path.join(self.FRAGMENT_DIR, filename)
            elif self.storage_method == self.LOCATION_REGISTRY:
                # Use registry location (Windows only)
                if os.name == 'nt':
                    return f"SOFTWARE\\POSMVP\\License\\{fragment_hash}"
                else:
                    return os.path.join(self.FRAGMENT_DIR, filename)
            elif self.storage_method == self.LOCATION_ENVIRONMENT:
                # Use environment variable
                env_var = f"POSMVP_LICENSE_{fragment_hash.upper()}"
                return env_var
            elif self.storage_method == self.LOCATION_MULTIPLE:
                # Use multiple locations for redundancy
                locations = [
                    os.path.join(self.FRAGMENT_DIR, filename),
                    os.path.join(self.STORAGE_DIR, filename),
                    os.path.join(os.path.expanduser("~"), f".posmvp_{filename}")
                ]
                
                # Return first available location
                for location in locations:
                    try:
                        # Test if location is writable
                        test_file = location + ".test"
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                        return location
                    except:
                        continue
                
                # Fallback to primary location
                return os.path.join(self.FRAGMENT_DIR, filename)
            
            return os.path.join(self.FRAGMENT_DIR, filename)
        except Exception as e:
            print(f"Error getting fragment path: {str(e)}")
            return None
    
    def _store_fragment(self, fragment_name: str, fragment_type: str, data: Any) -> bool:
        """Store fragment data"""
        try:
            # Get fragment path
            fragment_path = self._get_fragment_path(fragment_name, fragment_type)
            
            if not fragment_path:
                return False
            
            # Get encryption key
            encryption_key = self._get_fragment_key(fragment_name)
            
            if not encryption_key:
                return False
            
            # Prepare fragment data
            fragment_data = {
                'name': fragment_name,
                'type': fragment_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            # Convert to JSON
            fragment_json = json.dumps(fragment_data, sort_keys=True)
            
            # Encrypt fragment data
            encrypted_data, key = self.license_crypto.encrypt_data(fragment_json)
            
            # Prepare storage data
            storage_data = {
                'encrypted_data': encrypted_data,
                'encryption_key': key,
                'checksum': hashlib.sha256(fragment_json.encode()).hexdigest(),
                'created_at': datetime.now().isoformat()
            }
            
            # Store based on path type
            if fragment_path.startswith("SOFTWARE\\"):
                # Store in registry (Windows)
                return self._store_in_registry(fragment_path, storage_data)
            elif fragment_path.startswith("POSMVP_LICENSE_"):
                # Store in environment variable
                return self._store_in_environment(fragment_path, storage_data)
            else:
                # Store in file
                return self._store_in_file(fragment_path, storage_data)
        except Exception as e:
            print(f"Error storing fragment: {str(e)}")
            return False
    
    def _store_in_file(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Store fragment data in file"""
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write data to file
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            # Set file permissions
            os.chmod(file_path, 0o600)
            
            # Store location info
            self._fragment_locations[file_path] = 'file'
            
            return True
        except Exception as e:
            print(f"Error storing in file: {str(e)}")
            return False
    
    def _store_in_registry(self, registry_path: str, data: Dict[str, Any]) -> bool:
        """Store fragment data in Windows registry"""
        try:
            if os.name != 'nt':
                return False
            
            import winreg
            
            # Parse registry path
            path_parts = registry_path.split('\\')
            if len(path_parts) < 3:
                return False
            
            # Open registry key
            key_path = '\\'.join(path_parts[2:])
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            # Store data
            data_json = json.dumps(data)
            winreg.SetValueEx(key, "LicenseFragment", 0, winreg.REG_SZ, data_json)
            
            # Close key
            winreg.CloseKey(key)
            
            # Store location info
            self._fragment_locations[registry_path] = 'registry'
            
            return True
        except Exception as e:
            print(f"Error storing in registry: {str(e)}")
            return False
    
    def _store_in_environment(self, env_var: str, data: Dict[str, Any]) -> bool:
        """Store fragment data in environment variable"""
        try:
            # Convert data to base64 to handle special characters
            data_json = json.dumps(data)
            data_b64 = base64.b64encode(data_json.encode()).decode()
            
            # Set environment variable
            os.environ[env_var] = data_b64
            
            # Store location info
            self._fragment_locations[env_var] = 'environment'
            
            return True
        except Exception as e:
            print(f"Error storing in environment: {str(e)}")
            return False
    
    def _load_fragment(self, fragment_name: str, fragment_type: str) -> Optional[Any]:
        """Load fragment data"""
        try:
            # Get fragment path
            fragment_path = self._get_fragment_path(fragment_name, fragment_type)
            
            if not fragment_path:
                return None
            
            # Load based on path type
            if fragment_path.startswith("SOFTWARE\\"):
                # Load from registry (Windows)
                storage_data = self._load_from_registry(fragment_path)
            elif fragment_path.startswith("POSMVP_LICENSE_"):
                # Load from environment variable
                storage_data = self._load_from_environment(fragment_path)
            else:
                # Load from file
                storage_data = self._load_from_file(fragment_path)
            
            if not storage_data:
                return None
            
            # Decrypt fragment data
            encrypted_data = storage_data.get('encrypted_data')
            encryption_key = storage_data.get('encryption_key')
            checksum = storage_data.get('checksum')
            
            if not encrypted_data or not encryption_key:
                return None
            
            # Decrypt data
            fragment_json = self.license_crypto.decrypt_data(encrypted_data, encryption_key)
            
            if not fragment_json:
                return None
            
            # Verify checksum
            calculated_checksum = hashlib.sha256(fragment_json.encode()).hexdigest()
            if calculated_checksum != checksum:
                print(f"Fragment checksum mismatch: {fragment_name}_{fragment_type}")
                return None
            
            # Parse fragment data
            fragment_data = json.loads(fragment_json)
            
            return fragment_data.get('data')
        except Exception as e:
            print(f"Error loading fragment: {str(e)}")
            return None
    
    def _load_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load fragment data from file"""
        try:
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading from file: {str(e)}")
            return None
    
    def _load_from_registry(self, registry_path: str) -> Optional[Dict[str, Any]]:
        """Load fragment data from Windows registry"""
        try:
            if os.name != 'nt':
                return None
            
            import winreg
            
            # Parse registry path
            path_parts = registry_path.split('\\')
            if len(path_parts) < 3:
                return None
            
            # Open registry key
            key_path = '\\'.join(path_parts[2:])
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
            except:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            
            # Read data
            try:
                data_json, _ = winreg.QueryValueEx(key, "LicenseFragment")
                fragment_data = json.loads(data_json)
            except:
                fragment_data = None
            
            # Close key
            winreg.CloseKey(key)
            
            return fragment_data
        except Exception as e:
            print(f"Error loading from registry: {str(e)}")
            return None
    
    def _load_from_environment(self, env_var: str) -> Optional[Dict[str, Any]]:
        """Load fragment data from environment variable"""
        try:
            data_b64 = os.environ.get(env_var)
            
            if not data_b64:
                return None
            
            # Decode from base64
            data_json = base64.b64decode(data_b64).decode()
            
            return json.loads(data_json)
        except Exception as e:
            print(f"Error loading from environment: {str(e)}")
            return None
    
    def _load_fragments(self) -> None:
        """Load all fragments"""
        try:
            # Define fragments to load
            fragments = [
                (self.FRAGMENT_PRIMARY, self.TYPE_LICENSE_DATA),
                (self.FRAGMENT_PRIMARY, self.TYPE_ACTIVATION_DATA),
                (self.FRAGMENT_SECONDARY, self.TYPE_LICENSE_DATA),
                (self.FRAGMENT_SECONDARY, self.TYPE_SIGNATURE),
                (self.FRAGMENT_TERTIARY, self.TYPE_METADATA),
                (self.FRAGMENT_BACKUP, self.TYPE_LICENSE_DATA)
            ]
            
            # Load each fragment
            for fragment_name, fragment_type in fragments:
                data = self._load_fragment(fragment_name, fragment_type)
                if data is not None:
                    fragment_key = f"{fragment_name}_{fragment_type}"
                    self._fragments[fragment_key] = data
        except Exception as e:
            print(f"Error loading fragments: {str(e)}")
    
    def store_license_fragments(self, license: License, activation: LicenseActivation) -> bool:
        """
        Store license and activation data as fragments
        
        Args:
            license: License instance
            activation: LicenseActivation instance
            
        Returns:
            True if fragments stored successfully, False otherwise
        """
        try:
            # Prepare license data
            license_data = {
                'license_key': license._license_key,
                'license_id': license._license_id,
                'customer_name': license._customer_name,
                'customer_email': license._customer_email,
                'license_type': license._license_type,
                'features': license._features,
                'issued_date': license._issued_date.isoformat() if license._issued_date else None,
                'expiry_date': license._expiry_date.isoformat() if license._expiry_date else None,
                'status': license._status,
                'signature': license._signature,
                'validation_hash': license._validation_hash
            }
            
            # Prepare activation data
            activation_data = {
                'activation_id': activation._activation_id,
                'license_key': activation._license_key,
                'license_id': activation._license_id,
                'activation_code': activation._activation_code,
                'activation_type': activation._activation_type,
                'hardware_fingerprint': activation._hardware_fingerprint,
                'activation_date': activation._activation_date.isoformat() if activation._activation_date else None,
                'last_validated': activation._last_validated.isoformat() if activation._last_validated else None,
                'validation_count': activation._validation_count,
                'status': activation._status,
                'activation_signature': activation._activation_signature
            }
            
            # Store fragments based on fragmentation method
            if self.fragmentation_method == self.FRAGMENTATION_SIMPLE:
                return self._store_simple_fragments(license_data, activation_data)
            elif self.fragmentation_method == self.FRAGMENTATION_ADVANCED:
                return self._store_advanced_fragments(license_data, activation_data)
            elif self.fragmentation_method == self.FRAGMENTATION_STEALTH:
                return self._store_stealth_fragments(license_data, activation_data)
            else:
                # Default to advanced
                return self._store_advanced_fragments(license_data, activation_data)
        except Exception as e:
            print(f"Error storing license fragments: {str(e)}")
            return False
    
    def _store_simple_fragments(self, license_data: Dict[str, Any], 
                              activation_data: Dict[str, Any]) -> bool:
        """Store fragments using simple fragmentation"""
        try:
            # Store primary fragments
            success = True
            
            # Store license data
            success &= self._store_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_LICENSE_DATA, 
                license_data
            )
            
            # Store activation data
            success &= self._store_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_ACTIVATION_DATA, 
                activation_data
            )
            
            return success
        except Exception as e:
            print(f"Error storing simple fragments: {str(e)}")
            return False
    
    def _store_advanced_fragments(self, license_data: Dict[str, Any], 
                               activation_data: Dict[str, Any]) -> bool:
        """Store fragments using advanced fragmentation"""
        try:
            success = True
            
            # Store primary fragments (main data)
            success &= self._store_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_LICENSE_DATA, 
                license_data
            )
            
            success &= self._store_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_ACTIVATION_DATA, 
                activation_data
            )
            
            # Store secondary fragments (signatures)
            success &= self._store_fragment(
                self.FRAGMENT_SECONDARY, 
                self.TYPE_SIGNATURE, 
                {
                    'license_signature': license_data.get('signature'),
                    'activation_signature': activation_data.get('activation_signature')
                }
            )
            
            # Store tertiary fragments (metadata)
            success &= self._store_fragment(
                self.FRAGMENT_TERTIARY, 
                self.TYPE_METADATA, 
                {
                    'license_type': license_data.get('license_type'),
                    'features': license_data.get('features'),
                    'validation_hash': license_data.get('validation_hash'),
                    'created_at': datetime.now().isoformat()
                }
            )
            
            # Store backup fragments (redundancy)
            success &= self._store_fragment(
                self.FRAGMENT_BACKUP, 
                self.TYPE_LICENSE_DATA, 
                license_data
            )
            
            return success
        except Exception as e:
            print(f"Error storing advanced fragments: {str(e)}")
            return False
    
    def _store_stealth_fragments(self, license_data: Dict[str, Any], 
                              activation_data: Dict[str, Any]) -> bool:
        """Store fragments using stealth fragmentation"""
        try:
            success = True
            
            # Split data into multiple fragments for obfuscation
            license_json = json.dumps(license_data, sort_keys=True)
            activation_json = json.dumps(activation_data, sort_keys=True)
            
            # Split license data into 3 parts
            license_parts = self._split_data(license_json, 3)
            activation_parts = self._split_data(activation_json, 3)
            
            # Store fragmented data
            for i, part in enumerate(license_parts):
                fragment_name = f"license_part_{i+1}"
                success &= self._store_fragment(
                    fragment_name, 
                    self.TYPE_LICENSE_DATA, 
                    part
                )
            
            for i, part in enumerate(activation_parts):
                fragment_name = f"activation_part_{i+1}"
                success &= self._store_fragment(
                    fragment_name, 
                    self.TYPE_ACTIVATION_DATA, 
                    part
                )
            
            # Store reconstruction metadata
            metadata = {
                'license_parts': len(license_parts),
                'activation_parts': len(activation_parts),
                'reconstruction_key': base64.b64encode(secrets.token_bytes(16)).decode(),
                'created_at': datetime.now().isoformat()
            }
            
            success &= self._store_fragment(
                self.FRAGMENT_TERTIARY, 
                self.TYPE_METADATA, 
                metadata
            )
            
            return success
        except Exception as e:
            print(f"Error storing stealth fragments: {str(e)}")
            return False
    
    def _split_data(self, data: str, parts: int) -> List[str]:
        """Split data into multiple parts"""
        try:
            if parts <= 1:
                return [data]
            
            data_bytes = data.encode('utf-8')
            part_size = len(data_bytes) // parts
            result = []
            
            for i in range(parts):
                start = i * part_size
                end = start + part_size if i < parts - 1 else len(data_bytes)
                part_data = data_bytes[start:end]
                result.append(base64.b64encode(part_data).decode())
            
            return result
        except Exception as e:
            print(f"Error splitting data: {str(e)}")
            return [data]
    
    def load_license_fragments(self, license: License, activation: LicenseActivation) -> bool:
        """
        Load license and activation data from fragments
        
        Args:
            license: License instance to populate
            activation: LicenseActivation instance to populate
            
        Returns:
            True if fragments loaded successfully, False otherwise
        """
        try:
            # Load fragments based on fragmentation method
            if self.fragmentation_method == self.FRAGMENTATION_SIMPLE:
                return self._load_simple_fragments(license, activation)
            elif self.fragmentation_method == self.FRAGMENTATION_ADVANCED:
                return self._load_advanced_fragments(license, activation)
            elif self.fragmentation_method == self.FRAGMENTATION_STEALTH:
                return self._load_stealth_fragments(license, activation)
            else:
                # Default to advanced
                return self._load_advanced_fragments(license, activation)
        except Exception as e:
            print(f"Error loading license fragments: {str(e)}")
            return False
    
    def _load_simple_fragments(self, license: License, activation: LicenseActivation) -> bool:
        """Load fragments using simple fragmentation"""
        try:
            # Load primary fragments
            license_data = self._load_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_LICENSE_DATA
            )
            
            activation_data = self._load_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_ACTIVATION_DATA
            )
            
            if not license_data or not activation_data:
                return False
            
            # Populate license instance
            self._populate_license_from_data(license, license_data)
            
            # Populate activation instance
            self._populate_activation_from_data(activation, activation_data)
            
            return True
        except Exception as e:
            print(f"Error loading simple fragments: {str(e)}")
            return False
    
    def _load_advanced_fragments(self, license: License, activation: LicenseActivation) -> bool:
        """Load fragments using advanced fragmentation"""
        try:
            # Load primary fragments
            license_data = self._load_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_LICENSE_DATA
            )
            
            activation_data = self._load_fragment(
                self.FRAGMENT_PRIMARY, 
                self.TYPE_ACTIVATION_DATA
            )
            
            if not license_data or not activation_data:
                # Try backup fragments
                license_data = self._load_fragment(
                    self.FRAGMENT_BACKUP, 
                    self.TYPE_LICENSE_DATA
                )
            
            if not license_data or not activation_data:
                return False
            
            # Load secondary fragments (signatures)
            signature_data = self._load_fragment(
                self.FRAGMENT_SECONDARY, 
                self.TYPE_SIGNATURE
            )
            
            # Load tertiary fragments (metadata)
            metadata = self._load_fragment(
                self.FRAGMENT_TERTIARY, 
                self.TYPE_METADATA
            )
            
            # Verify data integrity
            if signature_data and metadata:
                # Verify signatures match
                if (signature_data.get('license_signature') != license_data.get('signature') or
                    signature_data.get('activation_signature') != activation_data.get('activation_signature')):
                    print("Signature mismatch in fragments")
                    return False
            
            # Populate license instance
            self._populate_license_from_data(license, license_data)
            
            # Populate activation instance
            self._populate_activation_from_data(activation, activation_data)
            
            return True
        except Exception as e:
            print(f"Error loading advanced fragments: {str(e)}")
            return False
    
    def _load_stealth_fragments(self, license: License, activation: LicenseActivation) -> bool:
        """Load fragments using stealth fragmentation"""
        try:
            # Load metadata first
            metadata = self._load_fragment(
                self.FRAGMENT_TERTIARY, 
                self.TYPE_METADATA
            )
            
            if not metadata:
                return False
            
            # Load fragmented parts
            license_parts = []
            activation_parts = []
            
            for i in range(metadata.get('license_parts', 0)):
                fragment_name = f"license_part_{i+1}"
                part = self._load_fragment(fragment_name, self.TYPE_LICENSE_DATA)
                if part:
                    license_parts.append(part)
            
            for i in range(metadata.get('activation_parts', 0)):
                fragment_name = f"activation_part_{i+1}"
                part = self._load_fragment(fragment_name, self.TYPE_ACTIVATION_DATA)
                if part:
                    activation_parts.append(part)
            
            # Reconstruct data
            license_json = self._reconstruct_data(license_parts)
            activation_json = self._reconstruct_data(activation_parts)
            
            if not license_json or not activation_json:
                return False
            
            # Parse reconstructed data
            license_data = json.loads(license_json)
            activation_data = json.loads(activation_json)
            
            # Populate license instance
            self._populate_license_from_data(license, license_data)
            
            # Populate activation instance
            self._populate_activation_from_data(activation, activation_data)
            
            return True
        except Exception as e:
            print(f"Error loading stealth fragments: {str(e)}")
            return False
    
    def _reconstruct_data(self, parts: List[str]) -> str:
        """Reconstruct data from parts"""
        try:
            if not parts:
                return ""
            
            # Decode parts and concatenate
            data_bytes = b''
            for part in parts:
                part_bytes = base64.b64decode(part)
                data_bytes += part_bytes
            
            return data_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error reconstructing data: {str(e)}")
            return ""
    
    def _populate_license_from_data(self, license: License, data: Dict[str, Any]) -> None:
        """Populate license instance from data"""
        try:
            license._license_key = data.get('license_key')
            license._license_id = data.get('license_id')
            license._customer_name = data.get('customer_name')
            license._customer_email = data.get('customer_email')
            license._license_type = data.get('license_type')
            license._features = data.get('features', [])
            
            # Parse dates
            issued_date = data.get('issued_date')
            if issued_date:
                license._issued_date = datetime.fromisoformat(issued_date)
            
            expiry_date = data.get('expiry_date')
            if expiry_date:
                license._expiry_date = datetime.fromisoformat(expiry_date)
            
            license._status = data.get('status')
            license._signature = data.get('signature')
            license._validation_hash = data.get('validation_hash')
        except Exception as e:
            print(f"Error populating license from data: {str(e)}")
    
    def _populate_activation_from_data(self, activation: LicenseActivation, data: Dict[str, Any]) -> None:
        """Populate activation instance from data"""
        try:
            activation._activation_id = data.get('activation_id')
            activation._license_key = data.get('license_key')
            activation._license_id = data.get('license_id')
            activation._activation_code = data.get('activation_code')
            activation._activation_type = data.get('activation_type')
            activation._hardware_fingerprint = data.get('hardware_fingerprint')
            
            # Parse dates
            activation_date = data.get('activation_date')
            if activation_date:
                activation._activation_date = datetime.fromisoformat(activation_date)
            
            last_validated = data.get('last_validated')
            if last_validated:
                activation._last_validated = datetime.fromisoformat(last_validated)
            
            activation._validation_count = data.get('validation_count', 0)
            activation._status = data.get('status')
            activation._activation_signature = data.get('activation_signature')
        except Exception as e:
            print(f"Error populating activation from data: {str(e)}")
    
    def clear_license_fragments(self) -> bool:
        """Clear all license fragments"""
        try:
            success = True
            
            # Clear file fragments
            if os.path.exists(self.FRAGMENT_DIR):
                for file_name in os.listdir(self.FRAGMENT_DIR):
                    if file_name.startswith('fragment_'):
                        file_path = os.path.join(self.FRAGMENT_DIR, file_name)
                        try:
                            os.remove(file_path)
                        except:
                            pass
            
            # Clear registry fragments (Windows)
            if os.name == 'nt':
                try:
                    import winreg
                    # Delete registry keys
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\POSMVP\\License")
                except:
                    pass
            
            # Clear environment fragments
            env_vars = [key for key in os.environ.keys() if key.startswith('POSMVP_LICENSE_')]
            for env_var in env_vars:
                try:
                    del os.environ[env_var]
                except:
                    pass
            
            # Clear fragment cache
            self._fragments.clear()
            
            return success
        except Exception as e:
            print(f"Error clearing license fragments: {str(e)}")
            return False
    
    def backup_fragments(self) -> bool:
        """Create backup of license fragments"""
        try:
            # Create backup timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.BACKUP_DIR, f"backup_{timestamp}")
            
            # Create backup directory
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy fragments to backup
            if os.path.exists(self.FRAGMENT_DIR):
                import shutil
                for file_name in os.listdir(self.FRAGMENT_DIR):
                    if file_name.startswith('fragment_'):
                        src_path = os.path.join(self.FRAGMENT_DIR, file_name)
                        dst_path = os.path.join(backup_path, file_name)
                        shutil.copy2(src_path, dst_path)
            
            # Copy fragment keys
            keys_file = os.path.join(self.STORAGE_DIR, "fragment_keys.json")
            if os.path.exists(keys_file):
                import shutil
                shutil.copy2(keys_file, os.path.join(backup_path, "fragment_keys.json"))
            
            return True
        except Exception as e:
            print(f"Error backing up fragments: {str(e)}")
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage information"""
        try:
            return {
                'storage_method': self.storage_method,
                'fragmentation_method': self.fragmentation_method,
                'storage_dir': self.STORAGE_DIR,
                'fragment_dir': self.FRAGMENT_DIR,
                'backup_dir': self.BACKUP_DIR,
                'fragments_count': len(self._fragments),
                'fragment_locations': len(self._fragment_locations),
                'directories_exist': {
                    'storage': os.path.exists(self.STORAGE_DIR),
                    'fragments': os.path.exists(self.FRAGMENT_DIR),
                    'backup': os.path.exists(self.BACKUP_DIR)
                }
            }
        except Exception as e:
            print(f"Error getting storage info: {str(e)}")
            return {}