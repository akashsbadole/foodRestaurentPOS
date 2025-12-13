"""
Fixed LicenseManager module with proper error handling and database integration
"""

import os
import json
import hashlib
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from src.models.database import DatabaseManager
from src.models.license import License
from src.models.license_activation import LicenseActivation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/license_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LicenseManager:
    """
    Fixed License Management System with proper error handling and database integration
    """
    
    def __init__(self):
        """Initialize the license manager with database connection"""
        self.db = DatabaseManager()
        self.license_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'license_keys')
        os.makedirs(self.license_dir, exist_ok=True)
        self.private_key_path = os.path.join(self.license_dir, 'license_private_rsa.pem')
        self.public_key_path = os.path.join(self.license_dir, 'license_public_rsa.pem')
        
        # Initialize RSA keys
        self._initialize_keys()
        
        logger.info("LicenseManager initialized successfully")
    
    def _initialize_keys(self):
        """Initialize RSA keys for license signing and verification"""
        try:
            if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
                # Load existing keys
                with open(self.private_key_path, 'rb') as f:
                    self.private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
                
                with open(self.public_key_path, 'rb') as f:
                    self.public_key = serialization.load_pem_public_key(
                        f.read()
                    )
                logger.info("Existing RSA keys loaded successfully")
            else:
                # Generate new keys
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                self.public_key = self.private_key.public_key()
                
                # Save keys
                with open(self.private_key_path, 'wb') as f:
                    f.write(self.private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                
                with open(self.public_key_path, 'wb') as f:
                    f.write(self.public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
                logger.info("New RSA keys generated and saved")
        except Exception as e:
            logger.error(f"Failed to initialize RSA keys: {e}")
            raise
    
    def generate_license_key(self, customer_info: Dict, license_type: str = "trial", 
                           features: Dict = None, expiry_days: int = 30) -> str:
        """
        Generate a new license key with proper error handling
        """
        try:
            license_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
            
            license_data = {
                "license_id": license_id,
                "customer_info": customer_info,
                "license_type": license_type,
                "features": features or {},
                "created_at": created_at,
                "expiry_date": expiry_date,
                "version": "1.0"
            }
            
            # Create license signature
            license_json = json.dumps(license_data, sort_keys=True)
            signature = self.private_key.sign(
                license_json.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Create license key
            license_key = {
                "data": license_data,
                "signature": signature.hex()
            }
            
            logger.info(f"Generated {license_type} license key for customer: {customer_info.get('name', 'Unknown')}")
            return json.dumps(license_key)
            
        except Exception as e:
            logger.error(f"Failed to generate license key: {e}")
            raise
    
    def verify_license_key(self, license_key: str) -> Tuple[bool, Dict]:
        """
        Verify a license key with proper error handling
        """
        try:
            license_obj = json.loads(license_key)
            license_data = license_obj["data"]
            signature = bytes.fromhex(license_obj["signature"])
            
            # Verify signature
            license_json = json.dumps(license_data, sort_keys=True)
            self.public_key.verify(
                signature,
                license_json.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Check expiry
            expiry_date = datetime.fromisoformat(license_data["expiry_date"])
            if datetime.now() > expiry_date:
                logger.warning(f"License {license_data['license_id']} has expired")
                return False, {"error": "License has expired"}
            
            logger.info(f"License {license_data['license_id']} verified successfully")
            return True, license_data
            
        except Exception as e:
            logger.error(f"Failed to verify license key: {e}")
            return False, {"error": str(e)}
    
    def create_trial_license(self, customer_name: str = None, customer_email: str = None,
                           business_name: str = None) -> Dict:
        """
        Create a trial license with proper database integration
        
        Args:
            customer_name: Customer name (optional, will use default if not provided)
            customer_email: Customer email (optional, will use default if not provided)
            business_name: Business name (optional)
            
        Returns:
            Dictionary with trial license creation result
        """
        try:
            # Use default values if customer_name and customer_email are not provided
            if not customer_name:
                customer_name = "Trial User"
            if not customer_email:
                customer_email = "trial@example.com"
                
            # Generate trial license key
            customer_info = {
                "name": customer_name,
                "email": customer_email,
                "business_name": business_name or customer_name
            }
            
            trial_features = {
                "max_users": 3,
                "max_terminals": 1,
                "modules": ["orders", "menu", "reports"],
                "support_level": "basic"
            }
            
            license_key = self.generate_license_key(
                customer_info=customer_info,
                license_type="trial",
                features=trial_features,
                expiry_days=30
            )
            
            # Parse license data
            license_obj = json.loads(license_key)
            license_data = license_obj["data"]
            signature = license_obj.get("signature", "")
            
            # Save to database using direct SQL with proper connection handling
            conn = None
            cursor = None
            
            try:
                # Get a fresh database connection
                conn = self.db.get_session()
                if not conn:
                    raise Exception("Failed to get database connection")
                    
                cursor = conn.cursor()
                
                # Insert license record
                cursor.execute("""
                    INSERT INTO licenses (
                        license_id, customer_name, customer_email, business_name,
                        license_type, features, license_key, created_at, issued_date, expires_at, is_active, signature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    license_data["license_id"],
                    customer_name,
                    customer_email,
                    business_name or customer_name,
                    "trial",
                    json.dumps(trial_features),
                    license_key,
                    datetime.now(),
                    datetime.now(),
                    datetime.fromisoformat(license_data["expiry_date"]),
                    True,
                    signature
                ))
                
                # Create license activation record
                cursor.execute("""
                    INSERT INTO license_activations (
                        license_id, activation_id, activation_token, hardware_fingerprint,
                        activation_date, expiry_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    license_data["license_id"],
                    str(uuid.uuid4()),
                    str(uuid.uuid4()),
                    "",
                    datetime.now(),
                    datetime.fromisoformat(license_data["expiry_date"]),
                    "active"
                ))
                
                conn.commit()
                
                logger.info(f"Trial license created and saved to database: {license_data['license_id']}")
                
                return {
                    "success": True,
                    "license_id": license_data["license_id"],
                    "license_key": license_key,
                    "customer_info": customer_info,
                    "features": trial_features,
                    "expires_at": license_data["expiry_date"],
                    "message": "Trial license created successfully"
                }
                
            except Exception as db_error:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                logger.error(f"Failed to save trial license to database: {db_error}")
                return {
                    "success": False,
                    "error": f"Database error: {str(db_error)}"
                }
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Failed to create trial license: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def activate_license(self, license_key: str, hardware_fingerprint: str) -> Dict:
        """
        Activate a license with proper error handling
        """
        try:
            # Verify license key
            is_valid, license_data = self.verify_license_key(license_key)
            if not is_valid:
                return {
                    "success": False,
                    "error": license_data.get("error", "Invalid license key")
                }
            
            license_id = license_data["license_id"]
            
            # Check if license already exists in database
            session = self.db.get_session()
            try:
                license_record = session.query(License).filter_by(license_id=license_id).first()
                
                if not license_record:
                    # Create license record if it doesn't exist
                    customer_info = license_data.get("customer_info", {})
                    license_record = License(
                        license_id=license_id,
                        customer_name=customer_info.get("name", "Unknown"),
                        customer_email=customer_info.get("email", ""),
                        business_name=customer_info.get("business_name", "Unknown"),
                        license_type=license_data.get("license_type", "unknown"),
                        features=json.dumps(license_data.get("features", {})),
                        license_key=license_key,
                        created_at=datetime.fromisoformat(license_data["created_at"]),
                        expires_at=datetime.fromisoformat(license_data["expiry_date"]),
                        is_active=True
                    )
                    session.add(license_record)
                    session.flush()
                
                # Check for existing activation
                existing_activation = session.query(LicenseActivation).filter_by(
                    license_id=license_id,
                    hardware_fingerprint=hardware_fingerprint
                ).first()
                
                if existing_activation:
                    if existing_activation.is_active:
                        return {
                            "success": True,
                            "message": "License already activated on this hardware",
                            "activation_token": existing_activation.activation_token
                        }
                    else:
                        # Reactivate existing activation
                        existing_activation.is_active = True
                        existing_activation.activated_at = datetime.now()
                        session.commit()
                        return {
                            "success": True,
                            "message": "License reactivated successfully",
                            "activation_token": existing_activation.activation_token
                        }
                
                # Create new activation
                activation_token = str(uuid.uuid4())
                activation_record = LicenseActivation(
                    license_id=license_id,
                    activation_token=activation_token,
                    hardware_fingerprint=hardware_fingerprint,
                    activated_at=datetime.now(),
                    expires_at=datetime.fromisoformat(license_data["expiry_date"]),
                    is_active=True
                )
                
                session.add(activation_record)
                session.commit()
                
                logger.info(f"License {license_id} activated successfully")
                return {
                    "success": True,
                    "message": "License activated successfully",
                    "activation_token": activation_token
                }
                
            except Exception as db_error:
                session.rollback()
                logger.error(f"Failed to activate license in database: {db_error}")
                return {
                    "success": False,
                    "error": f"Database error: {str(db_error)}"
                }
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to activate license: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def validate_license(self, license_key: str, hardware_fingerprint: str) -> Dict:
        """
        Validate a license with proper error handling
        """
        conn = None
        cursor = None
        
        try:
            # First verify the license key
            is_valid, license_data = self.verify_license_key(license_key)
            if not is_valid:
                return {
                    "valid": False,
                    "error": license_data.get("error", "Invalid license key")
                }
            
            license_id = license_data["license_id"]
            
            # Check database for activation
            conn = self.db.get_session()
            if not conn:
                logger.error("Failed to get database connection for license validation")
                return {
                    "valid": False,
                    "error": "Database connection failed"
                }
                
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT activation_token, hardware_fingerprint, activated_at, expires_at, is_active
                    FROM license_activations
                    WHERE license_id = ? AND hardware_fingerprint = ? AND is_active = 1
                    LIMIT 1
                """, (license_id, hardware_fingerprint))
                
                activation_row = cursor.fetchone()
                
                if not activation_row:
                    return {
                        "valid": False,
                        "error": "License not activated for this hardware"
                    }
                
                # Check if activation has expired
                expires_at = activation_row[3]
                if expires_at and datetime.now() > expires_at:
                    return {
                        "valid": False,
                        "error": "License activation has expired"
                    }
                
                # Get license record
                cursor.execute("""
                    SELECT license_id, customer_name, customer_email, business_name,
                           license_type, features, created_at, expires_at, is_active
                    FROM licenses
                    WHERE license_id = ? AND is_active = 1
                    LIMIT 1
                """, (license_id,))
                
                license_row = cursor.fetchone()
                
                if not license_row:
                    return {
                        "valid": False,
                        "error": "License not found or inactive"
                    }
                
                logger.info(f"License {license_id} validated successfully")
                return {
                    "valid": True,
                    "license_data": license_data,
                    "features": json.loads(license_row[5]) if license_row[5] else {},
                    "expires_at": license_row[7]
                }
                
            except Exception as db_error:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                logger.error(f"Failed to validate license in database: {db_error}")
                return {
                    "valid": False,
                    "error": f"Database error: {str(db_error)}"
                }
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Failed to validate license: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_license_info(self, license_id: str) -> Dict:
        """
        Get license information from database
        """
        try:
            conn = self.db.get_session()
            cursor = conn.cursor()
            
            try:
                # Get license record
                cursor.execute("""
                    SELECT license_id, customer_name, customer_email, business_name,
                           license_type, features, created_at, expires_at, is_active
                    FROM licenses
                    WHERE license_id = ?
                """, (license_id,))
                
                license_row = cursor.fetchone()
                
                if not license_row:
                    return {"success": False, "error": "License not found"}
                
                # Get activation records
                cursor.execute("""
                    SELECT activation_token, hardware_fingerprint, activated_at, expires_at, is_active
                    FROM license_activations
                    WHERE license_id = ?
                """, (license_id,))
                
                activation_rows = cursor.fetchall()
                
                return {
                    "success": True,
                    "license": {
                        "license_id": license_row[0],
                        "customer_name": license_row[1],
                        "customer_email": license_row[2],
                        "business_name": license_row[3],
                        "license_type": license_row[4],
                        "features": json.loads(license_row[5]) if license_row[5] else {},
                        "created_at": license_row[6],
                        "expires_at": license_row[7],
                        "is_active": bool(license_row[8])
                    },
                    "activations": [
                        {
                            "activation_token": act[0],
                            "hardware_fingerprint": act[1],
                            "activated_at": act[2],
                            "expires_at": act[3],
                            "is_active": bool(act[4])
                        }
                        for act in activation_rows
                    ]
                }
                
            except Exception as db_error:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                logger.error(f"Failed to get license info from database: {db_error}")
                return {"success": False, "error": f"Database error: {str(db_error)}"}
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Failed to get license info: {e}")
            return {"success": False, "error": str(e)}
    
    def deactivate_license(self, license_id: str, hardware_fingerprint: str = None) -> Dict:
        """
        Deactivate a license
        """
        try:
            session = self.db.get_session()
            try:
                query = session.query(LicenseActivation).filter_by(license_id=license_id)
                
                if hardware_fingerprint:
                    query = query.filter_by(hardware_fingerprint=hardware_fingerprint)
                
                activations = query.all()
                
                if not activations:
                    return {"success": False, "error": "No activations found"}
                
                for activation in activations:
                    activation.is_active = False
                
                session.commit()
                
                logger.info(f"License {license_id} deactivated successfully")
                return {"success": True, "message": "License deactivated successfully"}
                
            except Exception as db_error:
                session.rollback()
                logger.error(f"Failed to deactivate license in database: {db_error}")
                return {"success": False, "error": f"Database error: {str(db_error)}"}
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Failed to deactivate license: {e}")
            return {"success": False, "error": str(e)}
    
    # Methods to maintain compatibility with existing code
    def get_license_status(self) -> Dict[str, Any]:
        """Get current license status"""
        conn = None
        cursor = None
        
        try:
            # Try to get any active license
            conn = self.db.get_session()
            if not conn:
                logger.error("Failed to get database connection")
                return {
                    'status': 'error',
                    'message': 'Database connection failed',
                    'license_info': None,
                    'activation_info': None
                }
                
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT license_id, customer_name, customer_email, business_name,
                           license_type, features, created_at, expires_at, is_active
                    FROM licenses
                    WHERE is_active = 1
                    LIMIT 1
                """)
                
                license_row = cursor.fetchone()
                
                if not license_row:
                    return {
                        'status': 'not_activated',
                        'message': 'No license activated.',
                        'license_info': None,
                        'activation_info': None
                    }
                
                # Get activation
                cursor.execute("""
                    SELECT activation_token, hardware_fingerprint, activation_date, expiry_date, status
                    FROM license_activations
                    WHERE license_id = ?
                    LIMIT 1
                """, (license_row[0],))
                
                activation_row = cursor.fetchone()
                
                if not activation_row:
                    return {
                        'status': 'inactive',
                        'message': 'License found but not activated.',
                        'license_info': {
                            'license_id': license_row[0],
                            'customer_name': license_row[1],
                            'customer_email': license_row[2],
                            'business_name': license_row[3],
                            'license_type': license_row[4],
                            'features': json.loads(license_row[5]) if license_row[5] else {},
                            'created_at': license_row[6],
                            'expires_at': license_row[7],
                            'is_active': bool(license_row[8])
                        },
                        'activation_info': None
                    }
                
                # Check if expired
                expires_at = activation_row[3]
                if expires_at and datetime.now() > expires_at:
                    return {
                        'status': 'expired',
                        'message': 'License has expired.',
                        'license_info': {
                            'license_id': license_row[0],
                            'customer_name': license_row[1],
                            'customer_email': license_row[2],
                            'business_name': license_row[3],
                            'license_type': license_row[4],
                            'features': json.loads(license_row[5]) if license_row[5] else {},
                            'created_at': license_row[6],
                            'expires_at': license_row[7],
                            'is_active': bool(license_row[8])
                        },
                        'activation_info': {
                            'activation_token': activation_row[0],
                            'hardware_fingerprint': activation_row[1],
                            'activated_at': activation_row[2],
                            'expires_at': activation_row[3],
                            'is_active': bool(activation_row[4])
                        }
                    }
                
                return {
                    'status': 'active',
                    'message': 'License is active.',
                    'license_info': {
                        'license_id': license_row[0],
                        'customer_name': license_row[1],
                        'customer_email': license_row[2],
                        'business_name': license_row[3],
                        'license_type': license_row[4],
                        'features': json.loads(license_row[5]) if license_row[5] else {},
                        'created_at': license_row[6],
                        'expires_at': license_row[7],
                        'is_active': bool(license_row[8])
                    },
                    'activation_info': {
                        'activation_token': activation_row[0],
                        'hardware_fingerprint': activation_row[1],
                        'activated_at': activation_row[2],
                        'expires_at': activation_row[3],
                        'is_active': bool(activation_row[4])
                    }
                }
                
            except Exception as e:
                logger.error(f"Error getting license status: {e}")
                return {
                    'status': 'error',
                    'message': f'Error getting license status: {str(e)}',
                    'license_info': None,
                    'activation_info': None
                }
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                
        except Exception as e:
            logger.error(f"Error getting license status: {e}")
            return {
                'status': 'error',
                'message': f'Error getting license status: {str(e)}',
                'license_info': None,
                'activation_info': None
            }
    
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
            try:
                license_status = self.get_license_status()
                
                # Check if license_status is valid
                if not license_status or not isinstance(license_status, dict):
                    logger.warning("Invalid license status returned, using defaults")
                    license_status = {}
                
                if license_status.get('status') == 'active':
                    # Get license info
                    license_info = license_status.get('license_info', {})
                    activation_info = license_status.get('activation_info', {})
                    
                    # Check if it's a trial license
                    if license_info and license_info.get('license_type') == 'trial':
                        # Calculate days remaining
                        started_date = activation_info.get('activated_at')
                        expires_date = activation_info.get('expires_at')
                        
                        if expires_date:
                            try:
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
                            except (ValueError, TypeError) as date_error:
                                logger.error(f"Error parsing expiry date: {date_error}")
                                result['trial_info']['status'] = 'error'
                                result['trial_info']['days_remaining'] = 0
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
            except Exception as e:
                logger.error(f"Error getting trial status: {e}")
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
            
            return result
        except Exception as e:
            logger.error(f"Error getting trial status: {e}")
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
    
    def check_feature_access(self, feature: str) -> Dict[str, Any]:
        """Check if a feature is available"""
        try:
            result = {
                'allowed': False,
                'reason': '',
                'license_type': None
            }
            
            # Get license status
            license_status = self.get_license_status()
            
            if license_status.get('status') != 'active':
                result['reason'] = 'No active license found.'
                return result
            
            # Get license info
            license_info = license_status.get('license_info', {})
            if not license_info:
                result['reason'] = 'No license information available.'
                return result
            
            # Check feature access based on license type
            license_type = license_info.get('license_type', 'trial')
            result['license_type'] = license_type
            
            # Define feature access based on license type
            feature_access_map = {
                'trial': [
                    'basic_orders', 'basic_inventory', 'basic_reports',
                    'customer_support', 'data_export'
                ],
                'standard': [
                    'basic_orders', 'basic_inventory', 'basic_reports',
                    'customer_support', 'data_export', 'advanced_orders',
                    'advanced_inventory'
                ],
                'professional': [
                    'basic_orders', 'basic_inventory', 'basic_reports',
                    'customer_support', 'data_export', 'advanced_orders',
                    'advanced_inventory', 'advanced_reports', 'multi_user',
                    'api_access', 'custom_themes'
                ],
                'enterprise': [
                    'basic_orders', 'basic_inventory', 'basic_reports',
                    'customer_support', 'data_export', 'advanced_orders',
                    'advanced_inventory', 'advanced_reports', 'multi_user',
                    'api_access', 'custom_themes', 'priority_support',
                    'custom_integrations', 'advanced_analytics', 'white_labeling'
                ]
            }
            
            # Check if feature is available for this license type
            allowed_features = feature_access_map.get(license_type, [])
            if feature in allowed_features:
                result['allowed'] = True
            else:
                result['reason'] = f'Feature "{feature}" not available in {license_type} license.'
            
            return result
        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return {
                'allowed': False,
                'reason': f'Error checking feature access: {str(e)}',
                'license_type': None
            }
    
    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self.db:
                self.db.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")