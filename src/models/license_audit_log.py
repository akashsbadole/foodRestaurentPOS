"""
License Audit Log model for POS MVP application
Handles tracking all license events with comprehensive logging
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List

from src.utils.encryption import get_encryption_manager


class LicenseAuditLog:
    """
    License Audit Log model for tracking all license events
    Implements comprehensive logging with tamper protection
    """
    
    # Event types
    EVENT_LICENSE_CREATED = "license_created"
    EVENT_LICENSE_ACTIVATED = "license_activated"
    EVENT_LICENSE_VALIDATED = "license_validated"
    EVENT_LICENSE_EXPIRED = "license_expired"
    EVENT_LICENSE_REVOKED = "license_revoked"
    EVENT_LICENSE_SUSPENDED = "license_suspended"
    EVENT_LICENSE_TRANSFERRED = "license_transferred"
    EVENT_LICENSE_UPGRADED = "license_upgraded"
    EVENT_LICENSE_RENEWED = "license_renewed"
    EVENT_ACTIVATION_FAILED = "activation_failed"
    EVENT_VALIDATION_FAILED = "validation_failed"
    EVENT_TAMPER_DETECTED = "tamper_detected"
    EVENT_OFFLINE_GRACE_EXPIRED = "offline_grace_expired"
    EVENT_ONLINE_VALIDATION_REQUIRED = "online_validation_required"
    EVENT_HARDWARE_CHANGED = "hardware_changed"
    EVENT_TRIAL_STARTED = "trial_started"
    EVENT_TRIAL_EXPIRED = "trial_expired"
    EVENT_BLACKLISTED = "blacklisted"
    EVENT_SECURITY_VIOLATION = "security_violation"
    
    # Event severity levels
    SEVERITY_INFO = "info"
    SEVERITY_WARNING = "warning"
    SEVERITY_ERROR = "error"
    SEVERITY_CRITICAL = "critical"
    
    # Event sources
    SOURCE_SYSTEM = "system"
    SOURCE_USER = "user"
    SOURCE_SERVER = "server"
    SOURCE_CLIENT = "client"
    
    def __init__(self, db_manager=None):
        """Initialize license audit log model"""
        self.db = db_manager
        self.encryption_manager = get_encryption_manager()
        
        # Audit log entry data
        self._log_id = None
        self._license_key = None
        self._license_id = None
        self._activation_id = None
        self._event_type = None
        self._event_severity = None
        self._event_source = None
        self._event_description = None
        self._event_data = {}
        self._timestamp = None
        self._ip_address = None
        self._user_agent = None
        self._hardware_fingerprint = None
        self._previous_state = {}
        self._new_state = {}
        self._success = None
        self._error_message = None
        self._event_hash = None
        self._signature = None
        self._is_tampered = False
        
    def log_event(self, license_key: str, event_type: str, event_data: Dict[str, Any] = None, 
                  severity: str = SEVERITY_INFO, source: str = SOURCE_SYSTEM) -> bool:
        """
        Log a license event
        
        Args:
            license_key: License key associated with the event
            event_type: Type of event
            event_data: Additional event data
            severity: Event severity level
            source: Event source
            
        Returns:
            True if event logged successfully, False otherwise
        """
        try:
            # Generate log ID
            self._log_id = self._generate_log_id()
            self._license_key = license_key
            self._event_type = event_type
            self._event_severity = severity
            self._event_source = source
            self._event_data = event_data or {}
            self._timestamp = datetime.now()
            
            # Extract additional data from event_data
            self._license_id = self._event_data.get('license_id')
            self._activation_id = self._event_data.get('activation_id')
            self._event_description = self._event_data.get('description', self._get_default_description(event_type))
            self._ip_address = self._event_data.get('ip_address')
            self._user_agent = self._event_data.get('user_agent')
            self._hardware_fingerprint = self._event_data.get('hardware_fingerprint')
            self._previous_state = self._event_data.get('previous_state', {})
            self._new_state = self._event_data.get('new_state', {})
            self._success = self._event_data.get('success', True)
            self._error_message = self._event_data.get('error_message')
            
            # Generate event hash
            self._generate_event_hash()
            
            # Generate signature
            self._generate_signature()
            
            # Save to database
            return self.save_to_database()
        except Exception as e:
            print(f"Error logging event: {str(e)}")
            return False
    
    def _generate_log_id(self) -> str:
        """Generate a unique log ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _get_default_description(self, event_type: str) -> str:
        """Get default description for event type"""
        descriptions = {
            self.EVENT_LICENSE_CREATED: "License created",
            self.EVENT_LICENSE_ACTIVATED: "License activated",
            self.EVENT_LICENSE_VALIDATED: "License validated",
            self.EVENT_LICENSE_EXPIRED: "License expired",
            self.EVENT_LICENSE_REVOKED: "License revoked",
            self.EVENT_LICENSE_SUSPENDED: "License suspended",
            self.EVENT_LICENSE_TRANSFERRED: "License transferred",
            self.EVENT_LICENSE_UPGRADED: "License upgraded",
            self.EVENT_LICENSE_RENEWED: "License renewed",
            self.EVENT_ACTIVATION_FAILED: "License activation failed",
            self.EVENT_VALIDATION_FAILED: "License validation failed",
            self.EVENT_TAMPER_DETECTED: "License tampering detected",
            self.EVENT_OFFLINE_GRACE_EXPIRED: "Offline grace period expired",
            self.EVENT_ONLINE_VALIDATION_REQUIRED: "Online validation required",
            self.EVENT_HARDWARE_CHANGED: "Hardware configuration changed",
            self.EVENT_TRIAL_STARTED: "Trial period started",
            self.EVENT_TRIAL_EXPIRED: "Trial period expired",
            self.EVENT_BLACKLISTED: "License blacklisted",
            self.EVENT_SECURITY_VIOLATION: "Security violation detected"
        }
        
        return descriptions.get(event_type, "Unknown license event")
    
    def _generate_event_hash(self) -> None:
        """Generate hash for event integrity"""
        try:
            event_data = {
                'log_id': self._log_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'activation_id': self._activation_id,
                'event_type': self._event_type,
                'event_severity': self._event_severity,
                'event_source': self._event_source,
                'event_description': self._event_description,
                'event_data': self._event_data,
                'timestamp': self._timestamp.isoformat(),
                'ip_address': self._ip_address,
                'user_agent': self._user_agent,
                'hardware_fingerprint': self._hardware_fingerprint,
                'previous_state': self._previous_state,
                'new_state': self._new_state,
                'success': self._success,
                'error_message': self._error_message
            }
            
            event_json = json.dumps(event_data, sort_keys=True)
            self._event_hash = hashlib.sha256(event_json.encode()).hexdigest()
        except Exception as e:
            print(f"Error generating event hash: {str(e)}")
    
    def _generate_signature(self) -> None:
        """Generate signature for event authentication"""
        try:
            from src.utils.license_crypto import LicenseCrypto
            license_crypto = LicenseCrypto()
            
            signature_data = {
                'log_id': self._log_id,
                'license_key': self._license_key,
                'event_type': self._event_type,
                'timestamp': self._timestamp.isoformat(),
                'event_hash': self._event_hash
            }
            
            signature_json = json.dumps(signature_data, sort_keys=True)
            self._signature = license_crypto.sign_data(signature_json)
        except Exception as e:
            print(f"Error generating signature: {str(e)}")
    
    def verify_event_integrity(self) -> bool:
        """Verify event integrity using hash and signature"""
        try:
            if not self._event_hash or not self._signature:
                return False
            
            # Recalculate event hash
            event_data = {
                'log_id': self._log_id,
                'license_key': self._license_key,
                'license_id': self._license_id,
                'activation_id': self._activation_id,
                'event_type': self._event_type,
                'event_severity': self._event_severity,
                'event_source': self._event_source,
                'event_description': self._event_description,
                'event_data': self._event_data,
                'timestamp': self._timestamp.isoformat(),
                'ip_address': self._ip_address,
                'user_agent': self._user_agent,
                'hardware_fingerprint': self._hardware_fingerprint,
                'previous_state': self._previous_state,
                'new_state': self._new_state,
                'success': self._success,
                'error_message': self._error_message
            }
            
            event_json = json.dumps(event_data, sort_keys=True)
            calculated_hash = hashlib.sha256(event_json.encode()).hexdigest()
            
            # Verify hash
            if calculated_hash != self._event_hash:
                return False
            
            # Verify signature
            from src.utils.license_crypto import LicenseCrypto
            license_crypto = LicenseCrypto()
            
            signature_data = {
                'log_id': self._log_id,
                'license_key': self._license_key,
                'event_type': self._event_type,
                'timestamp': self._timestamp.isoformat(),
                'event_hash': self._event_hash
            }
            
            signature_json = json.dumps(signature_data, sort_keys=True)
            return license_crypto.verify_signature(signature_json, self._signature)
        except Exception as e:
            print(f"Error verifying event integrity: {str(e)}")
            return False
    
    def save_to_database(self) -> bool:
        """Save audit log entry to database with encrypted fields"""
        if not self.db:
            return False
        
        try:
            # Encrypt sensitive fields
            encrypted_event_data = self.encryption_manager.encrypt(json.dumps(self._event_data)) if self._event_data else None
            encrypted_ip_address = self.encryption_manager.encrypt(self._ip_address) if self._ip_address else None
            encrypted_user_agent = self.encryption_manager.encrypt(self._user_agent) if self._user_agent else None
            encrypted_hardware_fingerprint = self.encryption_manager.encrypt(self._hardware_fingerprint) if self._hardware_fingerprint else None
            encrypted_previous_state = self.encryption_manager.encrypt(json.dumps(self._previous_state)) if self._previous_state else None
            encrypted_new_state = self.encryption_manager.encrypt(json.dumps(self._new_state)) if self._new_state else None
            encrypted_error_message = self.encryption_manager.encrypt(self._error_message) if self._error_message else None
            
            # Convert timestamp to string
            timestamp_str = self._timestamp.isoformat()
            
            query = """
            INSERT INTO license_audit_logs (
                log_id, license_key, license_id, activation_id, event_type, event_severity,
                event_source, event_description, event_data, timestamp, ip_address,
                user_agent, hardware_fingerprint, previous_state, new_state,
                success, error_message, event_hash, signature, is_tampered
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                self._log_id, self._license_key, self._license_id, self._activation_id,
                self._event_type, self._event_severity, self._event_source,
                self._event_description, encrypted_event_data, timestamp_str,
                encrypted_ip_address, encrypted_user_agent, encrypted_hardware_fingerprint,
                encrypted_previous_state, encrypted_new_state, self._success,
                encrypted_error_message, self._event_hash, self._signature, self._is_tampered
            )
            
            self.db.execute_query(query, params)
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error saving audit log to database: {str(e)}")
            return False
    
    def load_from_database(self, log_id: str) -> bool:
        """Load audit log entry from database using log ID"""
        if not self.db:
            return False
        
        try:
            query = "SELECT * FROM license_audit_logs WHERE log_id = ?"
            self.db.execute_query(query, (log_id,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            # Extract data from result
            self._log_id = result[1]
            self._license_key = result[2]
            self._license_id = result[3]
            self._activation_id = result[4]
            self._event_type = result[5]
            self._event_severity = result[6]
            self._event_source = result[7]
            self._event_description = result[8]
            self._event_data = json.loads(self.encryption_manager.decrypt(result[9])) if result[9] else {}
            self._timestamp = datetime.fromisoformat(result[10])
            self._ip_address = self.encryption_manager.decrypt(result[11]) if result[11] else None
            self._user_agent = self.encryption_manager.decrypt(result[12]) if result[12] else None
            self._hardware_fingerprint = self.encryption_manager.decrypt(result[13]) if result[13] else None
            self._previous_state = json.loads(self.encryption_manager.decrypt(result[14])) if result[14] else {}
            self._new_state = json.loads(self.encryption_manager.decrypt(result[15])) if result[15] else {}
            self._success = result[16]
            self._error_message = self.encryption_manager.decrypt(result[17]) if result[17] else None
            self._event_hash = result[18]
            self._signature = result[19]
            self._is_tampered = bool(result[20])
            
            return True
        except Exception as e:
            print(f"Error loading audit log from database: {str(e)}")
            return False
    
    def get_license_events(self, license_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all events for a specific license"""
        if not self.db:
            return []
        
        try:
            query = """
            SELECT log_id, event_type, event_severity, event_source, event_description,
                   timestamp, success, error_message
            FROM license_audit_logs
            WHERE license_key = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            
            self.db.execute_query(query, (license_key, limit))
            results = self.db.fetch_all()
            
            events = []
            for result in results:
                events.append({
                    'log_id': result[0],
                    'event_type': result[1],
                    'event_severity': result[2],
                    'event_source': result[3],
                    'event_description': result[4],
                    'timestamp': result[5],
                    'success': result[6],
                    'error_message': result[7]
                })
            
            return events
        except Exception as e:
            print(f"Error getting license events: {str(e)}")
            return []
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security-related events within specified hours"""
        if not self.db:
            return []
        
        try:
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(hours=hours)
            threshold_str = threshold_time.isoformat()
            
            # Security event types
            security_events = [
                self.EVENT_TAMPER_DETECTED,
                self.EVENT_VALIDATION_FAILED,
                self.EVENT_ACTIVATION_FAILED,
                self.EVENT_SECURITY_VIOLATION,
                self.EVENT_BLACKLISTED
            ]
            
            # Build query
            placeholders = ','.join(['?' for _ in security_events])
            query = f"""
            SELECT log_id, license_key, event_type, event_severity, event_description,
                   timestamp, ip_address, hardware_fingerprint
            FROM license_audit_logs
            WHERE event_type IN ({placeholders}) AND timestamp >= ?
            ORDER BY timestamp DESC
            """
            
            params = security_events + [threshold_str]
            self.db.execute_query(query, params)
            results = self.db.fetch_all()
            
            events = []
            for result in results:
                events.append({
                    'log_id': result[0],
                    'license_key': result[1],
                    'event_type': result[2],
                    'event_severity': result[3],
                    'event_description': result[4],
                    'timestamp': result[5],
                    'ip_address': self.encryption_manager.decrypt(result[6]) if result[6] else None,
                    'hardware_fingerprint': self.encryption_manager.decrypt(result[7]) if result[7] else None
                })
            
            return events
        except Exception as e:
            print(f"Error getting security events: {str(e)}")
            return []
    
    def get_failed_validations(self, license_key: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get failed validation events"""
        if not self.db:
            return []
        
        try:
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(hours=hours)
            threshold_str = threshold_time.isoformat()
            
            query = """
            SELECT log_id, license_key, event_type, event_description, timestamp,
                   error_message, ip_address, hardware_fingerprint
            FROM license_audit_logs
            WHERE event_type IN (?, ?) AND timestamp >= ?
            """
            
            params = [self.EVENT_VALIDATION_FAILED, self.EVENT_ACTIVATION_FAILED, threshold_str]
            
            if license_key:
                query += " AND license_key = ?"
                params.append(license_key)
            
            query += " ORDER BY timestamp DESC"
            
            self.db.execute_query(query, params)
            results = self.db.fetch_all()
            
            events = []
            for result in results:
                events.append({
                    'log_id': result[0],
                    'license_key': result[1],
                    'event_type': result[2],
                    'event_description': result[3],
                    'timestamp': result[4],
                    'error_message': self.encryption_manager.decrypt(result[5]) if result[5] else None,
                    'ip_address': self.encryption_manager.decrypt(result[6]) if result[6] else None,
                    'hardware_fingerprint': self.encryption_manager.decrypt(result[7]) if result[7] else None
                })
            
            return events
        except Exception as e:
            print(f"Error getting failed validations: {str(e)}")
            return []
    
    def get_event_statistics(self, license_key: str = None, days: int = 30) -> Dict[str, Any]:
        """Get event statistics for analysis"""
        if not self.db:
            return {}
        
        try:
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(days=days)
            threshold_str = threshold_time.isoformat()
            
            # Base query
            base_query = "SELECT event_type, COUNT(*) FROM license_audit_logs WHERE timestamp >= ?"
            params = [threshold_str]
            
            if license_key:
                base_query += " AND license_key = ?"
                params.append(license_key)
            
            base_query += " GROUP BY event_type"
            
            self.db.execute_query(base_query, params)
            results = self.db.fetch_all()
            
            # Count events by type
            event_counts = {}
            total_events = 0
            
            for result in results:
                event_type = result[0]
                count = result[1]
                event_counts[event_type] = count
                total_events += count
            
            # Count by severity
            severity_query = "SELECT event_severity, COUNT(*) FROM license_audit_logs WHERE timestamp >= ?"
            severity_params = [threshold_str]
            
            if license_key:
                severity_query += " AND license_key = ?"
                severity_params.append(license_key)
            
            severity_query += " GROUP BY event_severity"
            
            self.db.execute_query(severity_query, severity_params)
            severity_results = self.db.fetch_all()
            
            severity_counts = {}
            for result in severity_results:
                severity = result[0]
                count = result[1]
                severity_counts[severity] = count
            
            return {
                'total_events': total_events,
                'event_counts': event_counts,
                'severity_counts': severity_counts,
                'period_days': days,
                'license_key': license_key
            }
        except Exception as e:
            print(f"Error getting event statistics: {str(e)}")
            return {}
    
    def export_audit_data(self, license_key: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Export audit data for analysis or backup"""
        if not self.db:
            return []
        
        try:
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(days=days)
            threshold_str = threshold_time.isoformat()
            
            query = """
            SELECT log_id, license_key, license_id, activation_id, event_type,
                   event_severity, event_source, event_description, event_data,
                   timestamp, ip_address, user_agent, hardware_fingerprint,
                   previous_state, new_state, success, error_message,
                   event_hash, signature, is_tampered
            FROM license_audit_logs
            WHERE timestamp >= ?
            """
            
            params = [threshold_str]
            
            if license_key:
                query += " AND license_key = ?"
                params.append(license_key)
            
            query += " ORDER BY timestamp DESC"
            
            self.db.execute_query(query, params)
            results = self.db.fetch_all()
            
            export_data = []
            for result in results:
                export_data.append({
                    'log_id': result[0],
                    'license_key': result[1],
                    'license_id': result[2],
                    'activation_id': result[3],
                    'event_type': result[4],
                    'event_severity': result[5],
                    'event_source': result[6],
                    'event_description': result[7],
                    'event_data': json.loads(self.encryption_manager.decrypt(result[8])) if result[8] else {},
                    'timestamp': result[9],
                    'ip_address': self.encryption_manager.decrypt(result[10]) if result[10] else None,
                    'user_agent': self.encryption_manager.decrypt(result[11]) if result[11] else None,
                    'hardware_fingerprint': self.encryption_manager.decrypt(result[12]) if result[12] else None,
                    'previous_state': json.loads(self.encryption_manager.decrypt(result[13])) if result[13] else {},
                    'new_state': json.loads(self.encryption_manager.decrypt(result[14])) if result[14] else {},
                    'success': result[15],
                    'error_message': self.encryption_manager.decrypt(result[16]) if result[16] else None,
                    'event_hash': result[17],
                    'signature': result[18],
                    'is_tampered': bool(result[19])
                })
            
            return export_data
        except Exception as e:
            print(f"Error exporting audit data: {str(e)}")
            return []
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """Clean up old audit logs"""
        if not self.db:
            return 0
        
        try:
            # Calculate time threshold
            threshold_time = datetime.now() - timedelta(days=days)
            threshold_str = threshold_time.isoformat()
            
            # Delete old logs
            query = "DELETE FROM license_audit_logs WHERE timestamp < ?"
            self.db.execute_query(query, (threshold_str,))
            
            deleted_count = self.db.cursor.rowcount
            self.db.commit()
            
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up old logs: {str(e)}")
            return 0
    
    def get_log_info(self) -> Dict[str, Any]:
        """Get log information (non-sensitive data)"""
        return {
            'log_id': self._log_id,
            'license_key': self._license_key,
            'license_id': self._license_id,
            'activation_id': self._activation_id,
            'event_type': self._event_type,
            'event_severity': self._event_severity,
            'event_source': self._event_source,
            'event_description': self._event_description,
            'timestamp': self._timestamp.isoformat() if self._timestamp else None,
            'success': self._success,
            'is_tampered': self._is_tampered
        }