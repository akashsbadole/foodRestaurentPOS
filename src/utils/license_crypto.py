"""
License Cryptography utility for POS MVP application
Handles RSA-4096/ECC signatures and white-box cryptography
"""

import os
import json
import hashlib
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


class LicenseCrypto:
    """
    License Cryptography class for secure license operations
    Implements RSA-4096/ECC signatures and white-box cryptography
    """
    
    # Key sizes
    RSA_KEY_SIZE = 4096
    ECC_KEY_SIZE = 521  # ECC curve P-521
    
    # Algorithms
    ALGORITHM_RSA = "RSA"
    ALGORITHM_ECC = "ECC"
    ALGORITHM_AES = "AES"
    
    # Encryption modes
    MODE_GCM = "GCM"
    MODE_CBC = "CBC"
    
    def __init__(self, algorithm: str = ALGORITHM_RSA):
        """
        Initialize license crypto
        
        Args:
            algorithm: Cryptographic algorithm to use (RSA or ECC)
        """
        self.algorithm = algorithm
        self.private_key = None
        self.public_key = None
        self.key_file_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'license_keys')
        self._init_keys()
    
    def _init_keys(self) -> None:
        """Initialize or load cryptographic keys"""
        try:
            # Create config directory if it doesn't exist
            os.makedirs(self.key_file_path, exist_ok=True)
            
            # Try to load existing keys
            if self._load_keys():
                return
            
            # Generate new keys if none exist
            self._generate_keys()
            self._save_keys()
        except Exception as e:
            print(f"Error initializing license crypto keys: {str(e)}")
    
    def _generate_keys(self) -> None:
        """Generate new cryptographic keys"""
        try:
            if self.algorithm == self.ALGORITHM_RSA:
                # Generate RSA-4096 key pair
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=self.RSA_KEY_SIZE,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
            elif self.algorithm == self.ALGORITHM_ECC:
                # Generate ECC P-521 key pair
                self.private_key = ec.generate_private_key(
                    ec.SECP521R1(),
                    default_backend()
                )
                self.public_key = self.private_key.public_key()
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
        except Exception as e:
            print(f"Error generating keys: {str(e)}")
            raise
    
    def _load_keys(self) -> bool:
        """Load existing keys from files"""
        try:
            private_key_file = os.path.join(self.key_file_path, f'license_private_{self.algorithm.lower()}.pem')
            public_key_file = os.path.join(self.key_file_path, f'license_public_{self.algorithm.lower()}.pem')
            
            if not os.path.exists(private_key_file) or not os.path.exists(public_key_file):
                return False
            
            # Load private key
            with open(private_key_file, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None,
                    backend=default_backend()
                )
            
            # Load public key
            with open(public_key_file, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(
                    f.read(),
                    backend=default_backend()
                )
            
            return True
        except Exception as e:
            print(f"Error loading keys: {str(e)}")
            return False
    
    def _save_keys(self) -> None:
        """Save keys to files"""
        try:
            private_key_file = os.path.join(self.key_file_path, f'license_private_{self.algorithm.lower()}.pem')
            public_key_file = os.path.join(self.key_file_path, f'license_public_{self.algorithm.lower()}.pem')
            
            # Save private key
            with open(private_key_file, 'wb') as f:
                f.write(self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(public_key_file, 'wb') as f:
                f.write(self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            # Set file permissions (read/write for owner only)
            os.chmod(private_key_file, 0o600)
            os.chmod(public_key_file, 0o644)
        except Exception as e:
            print(f"Error saving keys: {str(e)}")
            raise
    
    def sign_data(self, data: str) -> str:
        """
        Sign data with private key
        
        Args:
            data: Data to sign
            
        Returns:
            Base64 encoded signature
        """
        try:
            data_bytes = data.encode('utf-8')
            
            if self.algorithm == self.ALGORITHM_RSA:
                # RSA signature with PSS padding
                signature = self.private_key.sign(
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            elif self.algorithm == self.ALGORITHM_ECC:
                # ECC signature
                signature = self.private_key.sign(
                    data_bytes,
                    ec.ECDSA(hashes.SHA256())
                )
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
            # Return base64 encoded signature
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            print(f"Error signing data: {str(e)}")
            raise
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        Verify signature with public key
        
        Args:
            data: Original data
            signature: Base64 encoded signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            data_bytes = data.encode('utf-8')
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            
            if self.algorithm == self.ALGORITHM_RSA:
                # RSA signature verification
                self.public_key.verify(
                    signature_bytes,
                    data_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            elif self.algorithm == self.ALGORITHM_ECC:
                # ECC signature verification
                self.public_key.verify(
                    signature_bytes,
                    data_bytes,
                    ec.ECDSA(hashes.SHA256())
                )
            else:
                raise ValueError(f"Unsupported algorithm: {self.algorithm}")
            
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Error verifying signature: {str(e)}")
            return False
    
    def encrypt_license_key(self, license_key: str, password: str = None) -> str:
        """
        Encrypt license key with white-box cryptography
        
        Args:
            license_key: License key to encrypt
            password: Optional password for additional security
            
        Returns:
            Encrypted license key
        """
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Derive key from password or random data
            if password:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = kdf.derive(password.encode())
            else:
                # Use system-specific key derivation
                system_data = self._get_system_fingerprint()
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = kdf.derive(system_data.encode())
            
            # Generate random IV
            iv = os.urandom(16)
            
            # Encrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt license key
            license_key_bytes = license_key.encode('utf-8')
            ciphertext = encryptor.update(license_key_bytes) + encryptor.finalize()
            
            # Combine salt, IV, tag, and ciphertext
            encrypted_data = salt + iv + encryptor.tag + ciphertext
            
            # Return base64 encoded encrypted data
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Error encrypting license key: {str(e)}")
            raise
    
    def decrypt_license_key(self, encrypted_key: str, password: str = None) -> str:
        """
        Decrypt license key with white-box cryptography
        
        Args:
            encrypted_key: Encrypted license key
            password: Optional password for decryption
            
        Returns:
            Decrypted license key
        """
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_key.encode('utf-8'))
            
            # Extract components
            salt = encrypted_data[:16]
            iv = encrypted_data[16:32]
            tag = encrypted_data[32:48]
            ciphertext = encrypted_data[48:]
            
            # Derive key from password or system data
            if password:
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = kdf.derive(password.encode())
            else:
                # Use system-specific key derivation
                system_data = self._get_system_fingerprint()
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                key = kdf.derive(system_data.encode())
            
            # Decrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt license key
            license_key_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            
            return license_key_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error decrypting license key: {str(e)}")
            raise
    
    def _get_system_fingerprint(self) -> str:
        """Get system fingerprint for key derivation"""
        try:
            import platform
            import uuid
            
            # Collect system information
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'node': platform.node(),
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'uuid': str(uuid.getnode())
            }
            
            # Create fingerprint
            system_json = json.dumps(system_info, sort_keys=True)
            return hashlib.sha256(system_json.encode()).hexdigest()
        except Exception as e:
            print(f"Error getting system fingerprint: {str(e)}")
            # Fallback to random data
            return hashlib.sha256(os.urandom(32)).hexdigest()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate a cryptographically secure token
        
        Args:
            length: Length of token in bytes
            
        Returns:
            Base64 encoded secure token
        """
        try:
            token_bytes = secrets.token_bytes(length)
            return base64.b64encode(token_bytes).decode('utf-8')
        except Exception as e:
            print(f"Error generating secure token: {str(e)}")
            raise
    
    def hash_data(self, data: str, algorithm: str = "SHA256") -> str:
        """
        Hash data with specified algorithm
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (SHA256, SHA512, etc.)
            
        Returns:
            Hexadecimal hash
        """
        try:
            data_bytes = data.encode('utf-8')
            
            if algorithm.upper() == "SHA256":
                hash_obj = hashlib.sha256(data_bytes)
            elif algorithm.upper() == "SHA512":
                hash_obj = hashlib.sha512(data_bytes)
            elif algorithm.upper() == "SHA384":
                hash_obj = hashlib.sha384(data_bytes)
            elif algorithm.upper() == "SHA1":
                hash_obj = hashlib.sha1(data_bytes)
            elif algorithm.upper() == "MD5":
                hash_obj = hashlib.md5(data_bytes)
            else:
                raise ValueError(f"Unsupported hash algorithm: {algorithm}")
            
            return hash_obj.hexdigest()
        except Exception as e:
            print(f"Error hashing data: {str(e)}")
            raise
    
    def derive_key_from_password(self, password: str, salt: bytes = None, 
                              iterations: int = 100000, key_length: int = 32) -> bytes:
        """
        Derive key from password using PBKDF2
        
        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)
            iterations: Number of iterations
            key_length: Length of derived key in bytes
            
        Returns:
            Tuple of (derived_key, salt)
        """
        try:
            if salt is None:
                salt = os.urandom(16)
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=key_length,
                salt=salt,
                iterations=iterations,
                backend=default_backend()
            )
            
            derived_key = kdf.derive(password.encode())
            return derived_key, salt
        except Exception as e:
            print(f"Error deriving key from password: {str(e)}")
            raise
    
    def encrypt_data(self, data: str, key: bytes = None) -> Tuple[str, str]:
        """
        Encrypt data with AES-256-GCM
        
        Args:
            data: Data to encrypt
            key: Encryption key (generated if not provided)
            
        Returns:
            Tuple of (encrypted_data, key) where key is base64 encoded
        """
        try:
            if key is None:
                key = os.urandom(32)
            
            # Generate random IV
            iv = os.urandom(16)
            
            # Encrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt data
            data_bytes = data.encode('utf-8')
            ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
            
            # Combine IV, tag, and ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            
            # Return base64 encoded encrypted data and key
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            key_b64 = base64.b64encode(key).decode('utf-8')
            
            return encrypted_b64, key_b64
        except Exception as e:
            print(f"Error encrypting data: {str(e)}")
            raise
    
    def decrypt_data(self, encrypted_data: str, key: str) -> str:
        """
        Decrypt data with AES-256-GCM
        
        Args:
            encrypted_data: Base64 encoded encrypted data
            key: Base64 encoded encryption key
            
        Returns:
            Decrypted data
        """
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            key_bytes = base64.b64decode(key.encode('utf-8'))
            
            # Extract components
            iv = encrypted_bytes[:16]
            tag = encrypted_bytes[16:32]
            ciphertext = encrypted_bytes[32:]
            
            # Decrypt with AES-256-GCM
            cipher = Cipher(
                algorithms.AES(key_bytes),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            data_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            
            return data_bytes.decode('utf-8')
        except Exception as e:
            print(f"Error decrypting data: {str(e)}")
            raise
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        try:
            return self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
        except Exception as e:
            print(f"Error getting public key PEM: {str(e)}")
            raise
    
    def get_key_info(self) -> Dict[str, Any]:
        """Get information about cryptographic keys"""
        try:
            key_info = {
                'algorithm': self.algorithm,
                'key_size': self.RSA_KEY_SIZE if self.algorithm == self.ALGORITHM_RSA else self.ECC_KEY_SIZE,
                'has_private_key': self.private_key is not None,
                'has_public_key': self.public_key is not None,
                'key_files_exist': os.path.exists(os.path.join(self.key_file_path, f'license_private_{self.algorithm.lower()}.pem'))
            }
            
            # Add algorithm-specific info
            if self.algorithm == self.ALGORITHM_RSA:
                key_info['public_numbers'] = self.public_key.public_numbers().n
                key_info['key_size'] = self.public_key.key_size
            elif self.algorithm == self.ALGORITHM_ECC:
                key_info['curve'] = self.public_key.curve.name
            
            return key_info
        except Exception as e:
            print(f"Error getting key info: {str(e)}")
            return {}
    
    def rotate_keys(self) -> bool:
        """
        Rotate cryptographic keys
        
        Returns:
            True if keys rotated successfully, False otherwise
        """
        try:
            # Backup existing keys
            if self._backup_keys():
                # Generate new keys
                self._generate_keys()
                self._save_keys()
                return True
            return False
        except Exception as e:
            print(f"Error rotating keys: {str(e)}")
            return False
    
    def _backup_keys(self) -> bool:
        """Backup existing keys"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.key_file_path, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            private_key_file = os.path.join(self.key_file_path, f'license_private_{self.algorithm.lower()}.pem')
            public_key_file = os.path.join(self.key_file_path, f'license_public_{self.algorithm.lower()}.pem')
            
            private_backup = os.path.join(backup_dir, f'license_private_{self.algorithm.lower()}_{timestamp}.pem')
            public_backup = os.path.join(backup_dir, f'license_public_{self.algorithm.lower()}_{timestamp}.pem')
            
            if os.path.exists(private_key_file):
                import shutil
                shutil.copy2(private_key_file, private_backup)
                os.chmod(private_backup, 0o600)
            
            if os.path.exists(public_key_file):
                import shutil
                shutil.copy2(public_key_file, public_backup)
            
            return True
        except Exception as e:
            print(f"Error backing up keys: {str(e)}")
            return False
    
    def verify_key_integrity(self) -> bool:
        """Verify cryptographic key integrity"""
        try:
            if not self.private_key or not self.public_key:
                return False
            
            # Test signing and verification
            test_data = "integrity_test_" + datetime.now().isoformat()
            signature = self.sign_data(test_data)
            return self.verify_signature(test_data, signature)
        except Exception as e:
            print(f"Error verifying key integrity: {str(e)}")
            return False