"""
Encryption utility module for POS system
Provides AES-256 encryption for sensitive data with enhanced security features
"""

import os
import base64
import json
import logging
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class EncryptionError(Exception):
    """Custom exception for encryption and decryption errors."""
    pass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configure logging
logger = logging.getLogger(__name__)

class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data using AES-256
    with enhanced security features including integrity checks and key rotation
    """
    
    def __init__(self, key_file_path=None):
        """
        Initialize the encryption manager
        
        Args:
            key_file_path: Path to the encryption key file. If None, uses default path.
        """
        self.key_file_path = key_file_path or os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption.key')
        self._key = None
        self._cipher_suite = None
        self._key_rotation_interval = 90  # days
        self._last_key_rotation = None
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption by loading or creating the encryption key"""
        try:
            self._load_or_create_key()
            self._cipher_suite = Fernet(self._key)
            self._check_key_rotation()
            logger.info("Encryption system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption system: {str(e)}")
            raise
    
    def _load_or_create_key(self):
        """
        Load existing encryption key or create a new one
        The key is derived from a master password using PBKDF2
        """
        # Ensure the config directory exists
        os.makedirs(os.path.dirname(self.key_file_path), exist_ok=True)
        
        # Check if key file exists
        if os.path.exists(self.key_file_path):
            try:
                with open(self.key_file_path, 'r') as key_file: # Changed 'rb' to 'r' for json.load
                    key_data = json.load(key_file)
                    # Derive the actual encryption key from the stored salt and master key
                    self._key = self._derive_key(
                        key_data['master_key'].encode(),
                        base64.b64decode(key_data['salt'].encode()) # Decode salt from base64
                    )
                    # Convert last_rotation to datetime object if it exists
                    last_rotation_str = key_data.get('last_rotation', None)
                    if last_rotation_str:
                        self._last_key_rotation = datetime.fromisoformat(last_rotation_str)
                    
                    logger.info("Encryption key loaded from file")
            except (json.JSONDecodeError, KeyError, base64.binascii.Error) as e:
                logger.error(f"Failed to load encryption key due to corruption or malformed data: {str(e)}. Regenerating key.")
                self._regenerate_key_on_failure() # Call the new regeneration method
            except Exception as e:
                logger.error(f"An unexpected error occurred while loading encryption key: {str(e)}")
                self._regenerate_key_on_failure() # Regenerate key for any unexpected errors too
        else:
            # Create new encryption key
            self._create_new_key()
    
    def _regenerate_key_on_failure(self):
        """
        Regenerate the encryption key if loading fails.
        This includes deleting the old file and creating a new one.
        """
        logger.warning("Attempting to regenerate encryption key due to load failure.")
        if os.path.exists(self.key_file_path):
            os.remove(self.key_file_path)
            logger.info(f"Removed corrupted key file: {self.key_file_path}")
        self._create_new_key()
        self._cipher_suite = Fernet(self._key) # Re-initialize cipher suite after new key creation
        logger.info("Encryption key regenerated successfully after previous failure.")

    def _create_new_key(self):
        """Create a new encryption key and save it"""
        try:
            # Generate a random salt
            salt = os.urandom(16)
            
            # Get master key from environment or create a random one
            master_key = os.environ.get('POS_ENCRYPTION_MASTER_KEY')
            if not master_key:
                # If no master key in environment, generate a random one
                master_key = base64.b64encode(os.urandom(32)).decode()
                logger.warning("No master key found in environment. Generated random key.")
                logger.warning("Store this master key securely: POS_ENCRYPTION_MASTER_KEY=" + master_key)
            
            # Derive the encryption key
            self._key = self._derive_key(master_key.encode(), salt)
            
            # Save the key data (not the actual key)
            key_data = {
                'master_key': master_key,
                'salt': base64.b64encode(salt).decode(),
                'created_at': datetime.utcnow().isoformat(),
                'last_rotation': datetime.utcnow().isoformat(),
                'version': '2.0'
            }
            
            with open(self.key_file_path, 'w') as key_file:
                json.dump(key_data, key_file)
            
            # Set file permissions (read/write for owner only)
            os.chmod(self.key_file_path, 0o600)
            
            self._last_key_rotation = datetime.utcnow().isoformat() # Store as ISO format string
            logger.info("New encryption key created and saved")
        except Exception as e:
            logger.error(f"Failed to create new encryption key: {str(e)}")
            raise # Re-raise only if key creation fails
    
    def _derive_key(self, master_key: bytes, salt: bytes) -> bytes:
        """
        Derive encryption key from master key using PBKDF2
        
        Args:
            master_key: The master key
            salt: Random salt for key derivation
            
        Returns:
            Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=100000,  # High iteration count for security
            backend=default_backend()
        )
        return base64.b64encode(kdf.derive(master_key))
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: The data to encrypt
            
        Returns:
            Base64 encoded encrypted data
        """
        if not data or data.strip() == "":
            return data  # Return empty/null data as-is
        
        try:
            # Convert to bytes if needed
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Encrypt the data
            encrypted_data = self._cipher_suite.encrypt(data_bytes)
            
            # Return as base64 string for storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            logger.debug(f"Data encrypted successfully (length: {len(data)})")
            return encrypted_b64
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data with enhanced error handling for malformed data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            
        Returns:
            Decrypted data as string
        """
        if not encrypted_data or encrypted_data.strip() == "":
            return encrypted_data  # Return empty/null data as-is
        
        # Add comprehensive logging to debug malformed data
        logger.debug(f"Attempting to decrypt data: '{encrypted_data}' (length: {len(encrypted_data)})")
        logger.debug(f"Data type: {type(encrypted_data)}")
        logger.debug(f"Data repr: {repr(encrypted_data)}")
        
        # Check if data looks like valid base64
        if len(encrypted_data) % 4 != 0:
            logger.warning(f"Invalid base64 length: {len(encrypted_data)} (should be multiple of 4)")
        
        # Check for common base64 characters
        import re
        if not re.match(r'^[A-Za-z0-9+/=]+$', encrypted_data):
            logger.warning(f"Invalid base64 characters detected in: {encrypted_data}")
        
        try:
            # Check if data is encrypted (base64 format)
            try:
                # Decode from base64
                logger.debug("Attempting base64 decode...")
                encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
                logger.debug(f"Base64 decode successful, got {len(encrypted_bytes)} bytes")
                
                # Decrypt the data
                logger.debug("Attempting decryption...")
                decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
                logger.debug(f"Decryption successful, got {len(decrypted_bytes)} bytes")
                
                # Convert back to string
                decrypted_data = decrypted_bytes.decode('utf-8')
                logger.debug(f"Data converted to string successfully: '{decrypted_data}' (length: {len(decrypted_data)})")
                
                return decrypted_data
            except (base64.binascii.Error, ValueError) as e:
                # Log error and raise custom exception for bad format or value
                logger.error(f"Decryption failed due to invalid format or value: {e}")
                logger.error(f"Problematic encrypted data: '{encrypted_data}' (length: {len(encrypted_data)})")
                raise EncryptionError(f"Decryption failed: Malformed encrypted data or incorrect padding. Details: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred during decryption: {e}")
                logger.error(f"Problematic encrypted data: '{encrypted_data}' (length: {len(encrypted_data)})")
                raise EncryptionError(f"Decryption failed unexpectedly. Details: {e}")
        except EncryptionError:
            # Re-raise EncryptionError without modification
            raise
        except Exception as e:
            # Handle any other exceptions
            logger.error(f"Unexpected error in decrypt method: {e}")
            logger.error(f"Problematic encrypted data: '{encrypted_data}' (length: {len(encrypted_data)})")
            raise EncryptionError(f"Decryption failed: {str(e)}")
    
    def safe_decrypt(self, encrypted_data: str, fallback_value: str = None) -> str:
        """
        Safely decrypt data with graceful error handling for malformed data
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            fallback_value: Value to return if decryption fails
            
        Returns:
            Decrypted data or fallback value if decryption fails
        """
        try:
            return self.decrypt(encrypted_data)
        except EncryptionError as e:
            logger.warning(f"Failed to decrypt data, using fallback: {e}")
            logger.warning(f"Problematic data: '{encrypted_data}' (length: {len(encrypted_data)})")
            return fallback_value or encrypted_data  # Return original data if no fallback provided
        except Exception as e:
            logger.error(f"Unexpected error during safe decryption: {e}")
            return fallback_value or encrypted_data
    
    def is_valid_encrypted_data(self, encrypted_data: str) -> bool:
        """
        Check if encrypted data appears to be valid
        
        Args:
            encrypted_data: The encrypted data to validate
            
        Returns:
            True if data appears valid, False otherwise
        """
        if not encrypted_data or encrypted_data.strip() == "":
            return False
        
        # Check length is multiple of 4 (base64 requirement)
        if len(encrypted_data) % 4 != 0:
            return False
        
        # Check for valid base64 characters
        import re
        if not re.match(r'^[A-Za-z0-9+/=]+$', encrypted_data):
            return False
        
        # Try to decode as base64
        try:
            base64.b64decode(encrypted_data.encode('utf-8'))
            return True
        except (base64.binascii.Error, ValueError):
            return False
    
    def repair_encrypted_data(self, encrypted_data: str) -> str:
        """
        Attempt to repair malformed encrypted data
        
        Args:
            encrypted_data: The potentially malformed encrypted data
            
        Returns:
            Repaired encrypted data or original if repair fails
        """
        if not encrypted_data or encrypted_data.strip() == "":
            return encrypted_data
        
        original_data = encrypted_data
        
        # Try common repair scenarios
        
        # 1. Fix padding issues (add missing padding characters)
        if len(encrypted_data) % 4 != 0:
            missing_padding = len(encrypted_data) % 4
            if missing_padding == 1:
                # Can't fix single character, likely corrupted
                logger.warning(f"Cannot repair encrypted data with single extra character: '{encrypted_data}'")
                return original_data
            
            # Add padding characters
            repaired = encrypted_data + '=' * (4 - missing_padding)
            logger.debug(f"Attempted padding repair: '{encrypted_data}' -> '{repaired}'")
            
            if self.is_valid_encrypted_data(repaired):
                logger.info(f"Successfully repaired encrypted data with padding fix")
                return repaired
        
        # 2. Try to fix common character substitutions
        char_substitutions = {
            # Common character mapping errors
            '0': 'O',  # zero to letter O
            '1': 'I',  # one to letter I
            '5': 'S',  # five to letter S
            '$': 'S',  # dollar sign to letter S
            '@': 'A',  # at sign to letter A
        }
        
        for old_char, new_char in char_substitutions.items():
            if old_char in encrypted_data:
                repaired = encrypted_data.replace(old_char, new_char)
                if repaired != encrypted_data and self.is_valid_encrypted_data(repaired):
                    logger.info(f"Successfully repaired encrypted data with character substitution: '{old_char}' -> '{new_char}'")
                    return repaired
        
        # 3. Try to remove invalid characters
        import re
        invalid_chars = re.compile(r'[^A-Za-z0-9+/=]')
        if invalid_chars.search(encrypted_data):
            repaired = invalid_chars.sub('', encrypted_data)
            if repaired != encrypted_data and self.is_valid_encrypted_data(repaired):
                logger.info(f"Successfully repaired encrypted data by removing invalid characters")
                return repaired
        
        # 4. Try base64 cleanup (remove extra whitespace, etc.)
        repaired = encrypted_data.strip()
        if repaired != encrypted_data and self.is_valid_encrypted_data(repaired):
            logger.info(f"Successfully repaired encrypted data by removing whitespace")
            return repaired
        
        # If no repair worked, return original
        logger.warning(f"Could not repair encrypted data: '{encrypted_data}'")
        return original_data
    
    def diagnose_encrypted_data(self, encrypted_data: str) -> dict:
        """
        Diagnose issues with encrypted data
        
        Args:
            encrypted_data: The encrypted data to diagnose
            
        Returns:
            Dictionary with diagnosis information
        """
        diagnosis = {
            'original_data': encrypted_data,
            'length': len(encrypted_data),
            'is_empty': not encrypted_data or encrypted_data.strip() == "",
            'is_valid_base64': self.is_valid_encrypted_data(encrypted_data),
            'issues': [],
            'suggestions': []
        }
        
        if diagnosis['is_empty']:
            diagnosis['issues'].append('Data is empty or whitespace only')
            diagnosis['suggestions'].append('Check if data should be empty or if this is missing data')
            return diagnosis
        
        # Check length issues
        if len(encrypted_data) % 4 != 0:
            diagnosis['issues'].append(f'Invalid length ({len(encrypted_data)}), should be multiple of 4')
            diagnosis['suggestions'].append('Data may be truncated or have padding issues')
        
        # Check for invalid characters
        import re
        if not re.match(r'^[A-Za-z0-9+/=]+$', encrypted_data):
            invalid_chars = re.findall(r'[^A-Za-z0-9+/=]', encrypted_data)
            diagnosis['issues'].append(f'Invalid characters detected: {set(invalid_chars)}')
            diagnosis['suggestions'].append('Data may be corrupted or not properly base64 encoded')
        
        # Check if it looks like unencrypted data
        if len(encrypted_data) < 50 and not diagnosis['is_valid_base64']:
            # Check if it looks like a name, phone number, or email
            if re.match(r'^[A-Za-z\s]+$', encrypted_data):
                diagnosis['suggestions'].append('Data appears to be an unencrypted name')
            elif re.match(r'^[\d\s\-+()]+$', encrypted_data):
                diagnosis['suggestions'].append('Data appears to be an unencrypted phone number')
            elif '@' in encrypted_data and '.' in encrypted_data:
                diagnosis['suggestions'].append('Data appears to be an unencrypted email address')
        
        return diagnosis
    
    def encrypt_field(self, field_value) -> str:
        """
        Encrypt a database field value
        
        Args:
            field_value: The field value to encrypt
            
        Returns:
            Encrypted field value
        """
        if field_value is None:
            return None
        
        return self.encrypt(str(field_value))
    
    def decrypt_field(self, encrypted_value) -> str:
        """
        Decrypt a database field value
        
        Args:
            encrypted_value: The encrypted field value
            
        Returns:
            Decrypted field value
        """
        if encrypted_value is None:
            return None
        
        return self.decrypt(str(encrypted_value))
    
    def _check_key_rotation(self):
        """Check if key rotation is needed and perform it"""
        if self._last_key_rotation and isinstance(self._last_key_rotation, datetime):
            if datetime.utcnow() - self._last_key_rotation > timedelta(days=self._key_rotation_interval):
                logger.info("Key rotation interval reached, performing automatic key rotation")
                self.rotate_key()
        elif isinstance(self._last_key_rotation, str): # Handle case where it's still a string after refactoring
            try:
                last_rotation_dt = datetime.fromisoformat(self._last_key_rotation)
                if datetime.utcnow() - last_rotation_dt > timedelta(days=self._key_rotation_interval):
                    logger.info("Key rotation interval reached, performing automatic key rotation (string parsing)")
                    self.rotate_key()
            except ValueError:
                logger.warning(f"Invalid last_key_rotation string format: {self._last_key_rotation}. Skipping rotation check.")
        elif self._last_key_rotation is None:
            logger.debug("Last key rotation not set, skipping rotation check.")
    
    def rotate_key(self, new_master_key: str = None):
        """
        Rotate encryption key
        
        Args:
            new_master_key: New master key. If None, generates a random one.
        """
        try:
            # Backup old key
            old_key = self._key
            
            # Create new key
            if new_master_key:
                os.environ['POS_ENCRYPTION_MASTER_KEY'] = new_master_key
            
            # Remove old key file to force creation of new one
            if os.path.exists(self.key_file_path):
                backup_path = self.key_file_path + '.backup'
                os.rename(self.key_file_path, backup_path)
                logger.info(f"Old key backed up to: {backup_path}")
            
            # Initialize new key
            self._init_encryption()
            
            logger.info("Encryption key rotated successfully")
            return True
        except Exception as e:
            logger.error(f"Key rotation failed: {str(e)}")
            # Restore old key if rotation failed
            self._key = old_key
            self._cipher_suite = Fernet(self._key)
            return False
    
    def encrypt_with_integrity(self, data: str) -> str:
        """
        Encrypt data with integrity check using HMAC
        
        Args:
            data: The data to encrypt
            
        Returns:
            Base64 encoded encrypted data with integrity check
        """
        if not data or data.strip() == "":
            return data
        
        try:
            # Encrypt the data
            encrypted_data = self.encrypt(data)
            
            # Create HMAC for integrity check
            hmac_obj = hmac.new(self._key, encrypted_data.encode(), hashlib.sha256)
            integrity_hash = hmac_obj.hexdigest()
            
            # Combine encrypted data and integrity hash
            combined_data = f"{encrypted_data}:{integrity_hash}"
            
            # Return as base64 string for storage
            combined_b64 = base64.b64encode(combined_data.encode()).decode('utf-8')
            
            logger.debug(f"Data encrypted with integrity check (length: {len(data)})")
            return combined_b64
        except Exception as e:
            logger.error(f"Encryption with integrity failed: {str(e)}")
            raise
    
    def decrypt_with_integrity(self, encrypted_data_with_integrity: str) -> str:
        """
        Decrypt data with integrity verification
        
        Args:
            encrypted_data_with_integrity: Base64 encoded encrypted data with integrity check
            
        Returns:
            Decrypted data as string
        """
        if not encrypted_data_with_integrity or encrypted_data_with_integrity.strip() == "":
            return encrypted_data_with_integrity
        
        try:
            # Decode from base64
            combined_data = base64.b64decode(encrypted_data_with_integrity.encode('utf-8')).decode()
            
            # Split encrypted data and integrity hash
            parts = combined_data.split(':')
            if len(parts) != 2:
                logger.warning("Invalid integrity check format, attempting standard decryption")
                return self.decrypt(encrypted_data_with_integrity)
            
            encrypted_data, received_hash = parts
            
            # Verify integrity
            hmac_obj = hmac.new(self._key, encrypted_data.encode(), hashlib.sha256)
            calculated_hash = hmac_obj.hexdigest()
            
            if not hmac.compare_digest(calculated_hash, received_hash):
                logger.error("Integrity check failed - data may be tampered with.")
                raise EncryptionError("Data integrity verification failed: Data may have been tampered with or is corrupted.")
            
            # Decrypt the data
            decrypted_data = self.decrypt(encrypted_data)
            
            logger.debug(f"Data decrypted with integrity verification (length: {len(decrypted_data)})")
            return decrypted_data
        except ValueError as e: # Catch the ValueError from self.decrypt or integrity check split
            logger.error(f"Decryption with integrity failed due to data format or integrity issue: {e}")
            raise EncryptionError(f"Decryption with integrity failed: Invalid data format or integrity compromised. Details: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during decryption with integrity: {e}")
            raise EncryptionError(f"Decryption with integrity failed unexpectedly. Details: {e}")
    
    def backup_key(self, backup_path: str = None) -> str:
        """
        Create a backup of the encryption key
        
        Args:
            backup_path: Path for backup file. If None, generates default path.
            
        Returns:
            Path to backup file
        """
        try:
            if not backup_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = self.key_file_path.replace('.key', f'_backup_{timestamp}.key')
            
            # Copy current key file to backup location
            import shutil
            shutil.copy2(self.key_file_path, backup_path)
            
            # Set secure permissions on backup
            os.chmod(backup_path, 0o600)
            
            logger.info(f"Encryption key backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Key backup failed: {str(e)}")
            raise
    
    def restore_key(self, backup_path: str) -> bool:
        """
        Restore encryption key from backup
        
        Args:
            backup_path: Path to backup key file
            
        Returns:
            True if restore successful, False otherwise
        """
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Backup current key before restoring
            current_backup = self.backup_key()
            
            # Copy backup to current key location
            import shutil
            shutil.copy2(backup_path, self.key_file_path)
            
            # Reinitialize encryption with restored key
            self._init_encryption()
            
            logger.info(f"Encryption key restored from: {backup_path}")
            logger.info(f"Previous key backed up to: {current_backup}")
            return True
        except Exception as e:
            logger.error(f"Key restore failed: {str(e)}")
            return False
    
    def get_key_info(self) -> dict:
        """
        Get information about current encryption key
        
        Returns:
            Dictionary with key information
        """
        info = {
            'key_file_exists': os.path.exists(self.key_file_path),
            'key_file_path': self.key_file_path,
            'algorithm': 'AES-256',
            'key_derivation': 'PBKDF2-HMAC-SHA256'
        }
        
        if os.path.exists(self.key_file_path):
            stat = os.stat(self.key_file_path)
            info.update({
                'key_file_size': stat.st_size,
                'key_file_modified': stat.st_mtime,
                'key_file_permissions': oct(stat.st_mode)[-3:]
            })
        
        return info


# Global encryption manager instance
_encryption_manager = None

def get_encryption_manager() -> EncryptionManager:
    """
    Get the global encryption manager instance
    
    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager

def encrypt_data(data: str) -> str:
    """
    Convenience function to encrypt data
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data
    """
    return get_encryption_manager().encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """
    Convenience function to decrypt data
    
    Args:
        encrypted_data: Encrypted data
        
    Returns:
        Decrypted data
    """
    return get_encryption_manager().decrypt(encrypted_data)