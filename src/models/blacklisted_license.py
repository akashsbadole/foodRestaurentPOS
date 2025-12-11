"""
Blacklisted License model for POS MVP application
Handles revoked and blacklisted licenses with security tracking
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

from src.utils.encryption import get_encryption_manager


class BlacklistedLicense:
    """
    Blacklisted License model for managing revoked licenses
    Implements comprehensive tracking of blacklisted licenses
    """
    
    # Blacklist reasons
    REASON_FRAUD = "fraud"
    REASON_CHARGEBACK = "chargeback"
    REASON_VIOLATION = "violation"
    REASON_EXPIRED = "expired"
    REASON_REFUNDED = "refunded"
    REASON_SECURITY = "security"
    REASON_ABUSE = "abuse"
    REASON_PIRACY = "piracy"
    REASON_MANUAL = "manual"
    REASON_SYSTEM = "system"
    
    # Blacklist severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    def __init__(self, db_manager=None):
        """Initialize blacklisted license model"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        
        # Blacklisted license data
        self._blacklist_id = None
        self._license_key = None
        self._license_id = None
        self._customer_name = None
        self._customer_email = None
        self._blacklist_reason = None
        self._blacklist_severity = None
        self._blacklisted_date = None
        self._blacklisted_by = None
        self._notes = None
        self._ip_addresses = []
        self._hardware_fingerprints = []
        self._activation_ids = []
        self._is_permanent = False
        self._expiry_date = None
        self._notification_sent = False
        self._appeal_status = None
        self._appeal_date = None
        self._appeal_notes = None
        self._blacklist_hash = None
        self._signature = None
        self._is_active = True
        
    def blacklist_license(self, license_key: str, license_id: str, reason: str, 
                        severity: str = SEVERITY_MEDIUM, blacklisted_by: str = "system",
                        notes: str = None, is_permanent: bool = False,
                        expiry_date: datetime = None, customer_name: str = None,
                        customer_email: str = None) -> bool:
        """
        Add a license to the blacklist
        
        Args:
            license_key: License key to blacklist
            license_id: License ID
            reason: Reason for blacklisting
            severity: Severity level
            blacklisted_by: Who blacklisted the license
            notes: Additional notes
            is_permanent: Whether blacklist is permanent
            expiry_date: Expiry date for temporary blacklist
            customer_name: Customer name
            customer_email: Customer email
            
        Returns:
            True if license blacklisted successfully, False otherwise
        """
        try:
            # Generate blacklist ID
            self._blacklist_id = self._generate_blacklist_id()
            self._license_key = license_key
            self._license_id = license_id
            self._blacklist_reason = reason
            self._blacklist_severity = severity
            self._blacklisted_date = datetime.now()
            self._blacklisted_by = blacklisted_by
            self._notes = notes
            self._is_permanent = is_permanent
            self._expiry_date = expiry_date
            self._customer_name = customer_name
            self._customer_email = customer_email
            self._appeal_status = "none"
            self._is_active = True
            
            # Generate blacklist hash
            self._generate_blacklist_hash()
            
            # Generate signature
            self._generate_signature()
            
            return True
        except Exception as e:
            print(f"Error blacklisting license: {str(e)}")
            return False
    
    def _generate_blacklist_id(self) -> str:
        """Generate a unique blacklist ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_blacklist_hash(self) -> None:
        """Generate hash for blacklist integrity"""
        try:
            blacklist_data = {
                'blacklist_id': self._blacklist_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'blacklist_reason': self._blacklist_reason,
                'blacklist_severity': self._blacklist_severity,
                'blacklisted_date': self._blacklisted_date.isoformat() if self._blacklisted_date else None,
                'blacklisted_by': self._blacklisted_by,
                'is_permanent': self._is_permanent,
                'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None
            }
            
            blacklist_json = json.dumps(blacklist_data, sort_keys=True)
            self._blacklist_hash = hashlib.sha256(blacklist_json.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating blacklist hash: {str(e)}")
    
    def _generate_signature(self) -> None:
        """Generate signature for blacklist authentication"""
        try:
            from src.utils.license_crypto import LicenseCrypto
            license_crypto = LicenseCrypto()
            
            signature_data = {
                'blacklist_id': self._blacklist_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'blacklist_hash': self._blacklist_hash,
                'blacklisted_date': self._blacklisted_date.isoformat() if self._blacklisted_date else None
            }
            
            signature_json = json.dumps(signature_data, sort_keys=True)
            self._signature = license_crypto.sign_data(signature_json)
        except Exception as e:
            print(f"Error generating signature: {str(e)}")
    
    def add_ip_address(self, ip_address: str) -> None:
        """Add IP address to blacklist record"""
        if ip_address and ip_address not in self._ip_addresses:
            self._ip_addresses.append(ip_address)
    
    def add_hardware_fingerprint(self, fingerprint: str) -> None:
        """Add hardware fingerprint to blacklist record"""
        if fingerprint and fingerprint not in self._hardware_fingerprints:
            self._hardware_fingerprints.append(fingerprint)
    
    def add_activation_id(self, activation_id: str) -> None:
        """Add activation ID to blacklist record"""
        if activation_id and activation_id not in self._activation_ids:
            self._activation_ids.append(activation_id)
    
    def is_blacklisted(self, license_key: str = None, ip_address: str = None,
                      hardware_fingerprint: str = None, activation_id: str = None) -> bool:
        """
        Check if a license, IP, or hardware fingerprint is blacklisted
        
        Args:
            license_key: License key to check
            ip_address: IP address to check
            hardware_fingerprint: Hardware fingerprint to check
            activation_id: Activation ID to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            # Check if blacklist is active
            if not self._is_active:
                return False
            
            # Check if temporary blacklist has expired
            if not self._is_permanent and self._expiry_date and datetime.now() > self._expiry_date:
                return False
            
            # Check license key
            if license_key and license_key == self._license_key:
                return True
            
            # Check IP address
            if ip_address and ip_address in self._ip_addresses:
                return True
            
            # Check hardware fingerprint
            if hardware_fingerprint and hardware_fingerprint in self._hardware_fingerprints:
                return True
            
            # Check activation ID
            if activation_id and activation_id in self._activation_ids:
                return True
            
            return False
        except Exception as e:
            print(f"Error checking blacklist status: {str(e)}")
            return False
    
    def verify_blacklist_integrity(self) -> bool:
        """Verify blacklist integrity using hash and signature"""
        try:
            if not self._blacklist_hash or not self._signature:
                return False
            
            # Recalculate blacklist hash
            blacklist_data = {
                'blacklist_id': self._blacklist_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'blacklist_reason': self._blacklist_reason,
                'blacklist_severity': self._blacklist_severity,
                'blacklisted_date': self._blacklisted_date.isoformat() if self._blacklisted_date else None,
                'blacklisted_by': self._blacklisted_by,
                'is_permanent': self._is_permanent,
                'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None
            }
            
            blacklist_json = json.dumps(blacklist_data, sort_keys=True)
            calculated_hash = hashlib.sha256(blacklist_json.encode()).hexdigest()
            
            # Verify hash
            if calculated_hash != self._blacklist_hash:
                return False
            
            # Verify signature
            from src.utils.license_crypto import LicenseCrypto
            license_crypto = LicenseCrypto()
            
            signature_data = {
                'blacklist_id': self._blacklist_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'blacklist_hash': self._blacklist_hash,
                'blacklisted_date': self._blacklisted_date.isoformat() if self._blacklisted_date else None
            }
            
            signature_json = json.dumps(signature_data, sort_keys=True)
            return license_crypto.verify_signature(signature_json, self._signature)
        except Exception as e:
            print(f"Error verifying blacklist integrity: {str(e)}")
            return False
    
    def update_appeal(self, appeal_status: str, appeal_notes: str = None) -> None:
        """Update appeal status"""
        self._appeal_status = appeal_status
        self._appeal_date = datetime.now()
        self._appeal_notes = appeal_notes
        
        # Regenerate hash and signature
        self._generate_blacklist_hash()
        self._generate_signature()
    
    def deactivate(self) -> None:
        """Deactivate blacklist entry"""
        self._is_active = False
        
        # Regenerate hash and signature
        self._generate_blacklist_hash()
        self._generate_signature()
    
    def reactivate(self) -> None:
        """Reactivate blacklist entry"""
        self._is_active = True
        
        # Regenerate hash and signature
        self._generate_blacklist_hash()
        self._generate_signature()
    
    def extend_expiry(self, days: int) -> None:
        """Extend expiry date for temporary blacklist"""
        if not self._is_permanent:
            if self._expiry_date:
                self._expiry_date = self._expiry_date + timedelta(days=days)
            else:
                self._expiry_date = datetime.now() + timedelta(days=days)
            
            # Regenerate hash and signature
            self._generate_blacklist_hash()
            self._generate_signature()
    
    def get_blacklist_info(self) -> Dict[str, Any]:
        """Get blacklist information (non-sensitive data)"""
        return {
            'blacklist_id': self._blacklist_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'customer_name': self._customer_name,
            'customer_email': self._customer_email,
            'blacklist_reason': self._blacklist_reason,
            'blacklist_severity': self._blacklist_severity,
            'blacklisted_date': self._blacklisted_date.isoformat() if self._blacklisted_date else None,
            'blacklisted_by': self._blacklisted_by,
            'is_permanent': self._is_permanent,
            'expiry_date': self._expiry_date.isoformat() if self._expiry_date else None,
            'appeal_status': self._appeal_status,
            'appeal_date': self._appeal_date.isoformat() if self._appeal_date else None,
            'is_active': self._is_active,
            'ip_addresses_count': len(self._ip_addresses),
            'hardware_fingerprints_count': len(self._hardware_fingerprints),
            'activation_ids_count': len(self._activation_ids)
        }
    
    def save_to_database(self) -> bool:
        """Save blacklist entry to database with encrypted fields"""
        if not self.db:
            return False
        
        try:
            # Encrypt sensitive fields
            encrypted_customer_name = self.encryption_manager.encrypt(self._customer_name) if self._customer_name else None
            encrypted_customer_email = self.encryption_manager.encrypt(self._customer_email) if self._customer_email else None
            encrypted_notes = self.encryption_manager.encrypt(self._notes) if self._notes else None
            encrypted_ip_addresses = self.encryption_manager.encrypt(json.dumps(self._ip_addresses)) if self._ip_addresses else None
            encrypted_hardware_fingerprints = self.encryption_manager.encrypt(json.dumps(self._hardware_fingerprints)) if self._hardware_fingerprints else None
            encrypted_activation_ids = self.encryption_manager.encrypt(json.dumps(self._activation_ids)) if self._activation_ids else None
            encrypted_appeal_notes = self.encryption_manager.encrypt(self._appeal_notes) if self._appeal_notes else None
            
            # Convert dates to strings
            blacklisted_date_str = self._blacklisted_date.isoformat() if self._blacklisted_date else None
            expiry_date_str = self._expiry_date.isoformat() if self._expiry_date else None
            appeal_date_str = self._appeal_date.isoformat() if self._appeal_date else None
            
            query = """
            INSERT OR REPLACE INTO blacklisted_licenses (
                blacklist_id, license_key, license_id, customer_name, customer_email,
                blacklist_reason, blacklist_severity, blacklisted_date, blacklisted_by,
                notes, ip_addresses, hardware_fingerprints, activation_ids,
                is_permanent, expiry_date, notification_sent, appeal_status,
                appeal_date, appeal_notes, blacklist_hash, signature, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                self._blacklist_id, self._license_key, self._license_id, encrypted_customer_name,
                encrypted_customer_email, self._blacklist_reason, self._blacklist_severity,
                blacklisted_date_str, self._blacklisted_by, encrypted_notes,
                encrypted_ip_addresses, encrypted_hardware_fingerprints, encrypted_activation_ids,
                self._is_permanent, expiry_date_str, self._notification_sent,
                self._appeal_status, appeal_date_str, encrypted_appeal_notes,
                self._blacklist_hash, self._signature, self._is_active
            )
            
            self.db.execute_query(query, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error saving blacklist to database: {str(e)}")
            return False
    
    def load_from_database(self, blacklist_id: str) -> bool:
        """Load blacklist entry from database using blacklist ID"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM blacklisted_licenses WHERE blacklist_id = ?"
            self.db.execute_query(query, (blacklist_id,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._blacklist_id = result[1]
            self._license_key = result[2]
            self._license_id = result[3]
            self._customer_name = self.encryption_manager.decrypt(result[4]) if result[4] else None
            self._customer_email = self.encryption_manager.decrypt(result[5]) if result[5] else None
            self._blacklist_reason = result[6]
            self._blacklist_severity = result[7]
            self._blacklisted_date = datetime.fromisoformat(result[8]) if result[8] else None
            self._blacklisted_by = result[9]
            self._notes = self.encryption_manager.decrypt(result[10]) if result[10] else None
            self._ip_addresses = json.loads(self.encryption_manager.decrypt(result[11])) if result[11] else []
            self._hardware_fingerprints = json.loads(self.encryption_manager.decrypt(result[12])) if result[12] else []
            self._activation_ids = json.loads(self.encryption_manager.decrypt(result[13])) if result[13] else []
            self._is_permanent = bool(result[14])
            self._expiry_date = datetime.fromisoformat(result[15]) if result[15] else None
            self._notification_sent = bool(result[16])
            self._appeal_status = result[17]
            self._appeal_date = datetime.fromisoformat(result[18]) if result[18] else None
            self._appeal_notes = self.encryption_manager.decrypt(result[19]) if result[19] else None
            self._blacklist_hash = result[20]
            self._signature = result[21]
            self._is_active = bool(result[22])
            
            return True
        except Exception as e:
            print(f"Error loading blacklist from database: {str(e)}")
            return False
    
    def load_by_license_key(self, license_key: str) -> bool:
        """Load blacklist entry from database using license key"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM blacklisted_licenses WHERE license_key = ?"
            self.db.execute_query(query, (license_key,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._blacklist_id = result[1]
            self._license_key = result[2]
            self._license_id = result[3]
            self._customer_name = self.encryption_manager.decrypt(result[4]) if result[4] else None
            self._customer_email = self.encryption_manager.decrypt(result[5]) if result[5] else None
            self._blacklist_reason = result[6]
            self._blacklist_severity = result[7]
            self._blacklisted_date = datetime.fromisoformat(result[8]) if result[8] else None
            self._blacklisted_by = result[9]
            self._notes = self.encryption_manager.decrypt(result[10]) if result[10] else None
            self._ip_addresses = json.loads(self.encryption_manager.decrypt(result[11])) if result[11] else []
            self._hardware_fingerprints = json.loads(self.encryption_manager.decrypt(result[12])) if result[12] else []
            self._activation_ids = json.loads(self.encryption_manager.decrypt(result[13])) if result[13] else []
            self._is_permanent = bool(result[14])
            self._expiry_date = datetime.fromisoformat(result[15]) if result[15] else None
            self._notification_sent = bool(result[16])
            self._appeal_status = result[17]
            self._appeal_date = datetime.fromisoformat(result[18]) if result[18] else None
            self._appeal_notes = self.encryption_manager.decrypt(result[19]) if result[19] else None
            self._blacklist_hash = result[20]
            self._signature = result[21]
            self._is_active = bool(result[22])
            
            return True
        except Exception as e:
            print(f"Error loading blacklist by license key: {str(e)}")
            return False
    
    def get_blacklisted_licenses(self, active_only: bool = True, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of blacklisted licenses"""
        if not self.db:
            return []
        
        try:
            query = """
            SELECT blacklist_id, license_key, license_id, blacklist_reason, blacklist_severity,
                   blacklisted_date, is_permanent, expiry_date, appeal_status, is_active
            FROM blacklisted_licenses
            """
            
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
                # Also check if temporary blacklist has expired
                query += " AND (is_permanent = 1 OR expiry_date IS NULL OR expiry_date > ?)"
                params.append(datetime.now().isoformat())
            
            query += " ORDER BY blacklisted_date DESC LIMIT ?"
            params.append(limit)
            
            self.db.execute_query(query, params)
            results = self.db.fetch_all()
            
            blacklisted = []
            for result in results:
                blacklisted.append({
                    'blacklist_id': result[0],
                    'license_key': result[1],
                    'license_id': result[2],
                    'blacklist_reason': result[3],
                    'blacklist_severity': result[4],
                    'blacklisted_date': result[5],
                    'is_permanent': bool(result[6]),
                    'expiry_date': result[7],
                    'appeal_status': result[8],
                    'is_active': bool(result[9])
                })
            
            return blacklisted
        except Exception as e:
            print(f"Error getting blacklisted licenses: {str(e)}")
            return []
    
    def cleanup_expired_blacklists(self) -> int:
        """Clean up expired blacklist entries"""
        if not self.db:
            return 0
        
        try:
            query = """
            DELETE FROM blacklisted_licenses
            WHERE is_permanent = 0 AND expiry_date IS NOT NULL AND expiry_date < ?
            """
            
            self.db.execute_query(query, (datetime.now().isoformat(),))
            deleted_count = self.db.cursor.rowcount
            self.db.commit()
            
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up expired blacklists: {str(e)}")
            return 0
    
    def export_blacklist_data(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Export blacklist data for analysis or backup"""
        if not self.db:
            return []
        
        try:
            query = """
            SELECT blacklist_id, license_key, license_id, customer_name, customer_email,
                   blacklist_reason, blacklist_severity, blacklisted_date, blacklisted_by,
                   notes, ip_addresses, hardware_fingerprints, activation_ids,
                   is_permanent, expiry_date, notification_sent, appeal_status,
                   appeal_date, appeal_notes, blacklist_hash, signature, is_active
            FROM blacklisted_licenses
            """
            
            params = []
            
            if active_only:
                query += " WHERE is_active = 1"
                query += " AND (is_permanent = 1 OR expiry_date IS NULL OR expiry_date > ?)"
                params.append(datetime.now().isoformat())
            
            query += " ORDER BY blacklisted_date DESC"
            
            self.db.execute_query(query, params)
            results = self.db.fetch_all()
            
            export_data = []
            for result in results:
                export_data.append({
                    'blacklist_id': result[0],
                    'license_key': result[1],
                    'license_id': result[2],
                    'customer_name': self.encryption_manager.decrypt(result[3]) if result[3] else None,
                    'customer_email': self.encryption_manager.decrypt(result[4]) if result[4] else None,
                    'blacklist_reason': result[5],
                    'blacklist_severity': result[6],
                    'blacklisted_date': result[7],
                    'blacklisted_by': result[8],
                    'notes': self.encryption_manager.decrypt(result[9]) if result[9] else None,
                    'ip_addresses': json.loads(self.encryption_manager.decrypt(result[10])) if result[10] else [],
                    'hardware_fingerprints': json.loads(self.encryption_manager.decrypt(result[11])) if result[11] else [],
                    'activation_ids': json.loads(self.encryption_manager.decrypt(result[12])) if result[12] else [],
                    'is_permanent': bool(result[13]),
                    'expiry_date': result[14],
                    'notification_sent': bool(result[15]),
                    'appeal_status': result[16],
                    'appeal_date': result[17],
                    'appeal_notes': self.encryption_manager.decrypt(result[18]) if result[18] else None,
                    'blacklist_hash': result[19],
                    'signature': result[20],
                    'is_active': bool(result[21])
                })
            
            return export_data
        except Exception as e:
            print(f"Error exporting blacklist data: {str(e)}")
            return []