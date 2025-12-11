"""
Add License Tables Migration
Creates database tables for the license system
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional

from src.utils.constants import DATABASE_PATH
from src.utils.encryption import EncryptionManager


class AddLicenseTables:
    """
    Migration to add license system tables to the database
    Creates tables for licenses, activations, hardware bindings, audit logs, and blacklisted licenses
    """
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize migration
        
        Args:
            db_path: Path to the database file
        """
        self.db_path = db_path
        self.encryption_manager = EncryptionManager()
    
    def run_migration(self) -> bool:
        """
        Run the migration to add license tables
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create license tables
            self._create_license_tables(cursor)
            
            # Create indexes
            self._create_indexes(cursor)
            
            # Create triggers
            self._create_triggers(cursor)
            
            # Commit changes
            conn.commit()
            
            # Close connection
            conn.close()
            
            print("License tables migration completed successfully")
            return True
        except Exception as e:
            print(f"Error running license tables migration: {str(e)}")
            return False
    
    def _create_license_tables(self, cursor: sqlite3.Cursor) -> None:
        """Create license system tables"""
        try:
            # Create licenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT UNIQUE NOT NULL,
                    license_type TEXT NOT NULL,
                    customer_name TEXT,
                    customer_email TEXT,
                    issued_date TEXT NOT NULL,
                    expiry_date TEXT,
                    status TEXT NOT NULL DEFAULT 'inactive',
                    features TEXT,
                    max_activations INTEGER DEFAULT 1,
                    current_activations INTEGER DEFAULT 0,
                    signature TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create license_activations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_id INTEGER NOT NULL,
                    activation_id TEXT UNIQUE NOT NULL,
                    activation_type TEXT NOT NULL DEFAULT 'online',
                    activation_date TEXT NOT NULL,
                    last_validated TEXT,
                    validation_count INTEGER DEFAULT 0,
                    hardware_fingerprint TEXT NOT NULL,
                    activation_code TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    machine_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (license_id) REFERENCES licenses (id) ON DELETE CASCADE
                )
            ''')
            
            # Create hardware_bindings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hardware_bindings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activation_id INTEGER NOT NULL,
                    hardware_id TEXT UNIQUE NOT NULL,
                    cpu_id TEXT,
                    motherboard_id TEXT,
                    disk_id TEXT,
                    mac_addresses TEXT,
                    system_uuid TEXT,
                    bios_serial TEXT,
                    fingerprint_method TEXT DEFAULT 'advanced',
                    fingerprint_hash TEXT NOT NULL,
                    binding_strength TEXT DEFAULT 'strong',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (activation_id) REFERENCES license_activations (id) ON DELETE CASCADE
                )
            ''')
            
            # Create license_audit_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT NOT NULL,
                    activation_id TEXT,
                    event_type TEXT NOT NULL,
                    event_severity TEXT DEFAULT 'info',
                    event_description TEXT,
                    event_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    integrity_hash TEXT
                )
            ''')
            
            # Create blacklisted_licenses table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklisted_licenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_key TEXT UNIQUE NOT NULL,
                    reason TEXT NOT NULL,
                    blacklisted_by TEXT,
                    blacklist_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    is_permanent INTEGER DEFAULT 0,
                    expiry_date TEXT,
                    integrity_hash TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create license_fragments table for fragmented storage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_fragments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_id INTEGER NOT NULL,
                    fragment_name TEXT NOT NULL,
                    fragment_data TEXT NOT NULL,
                    fragment_hash TEXT NOT NULL,
                    storage_location TEXT NOT NULL,
                    encryption_method TEXT DEFAULT 'aes256',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (license_id) REFERENCES licenses (id) ON DELETE CASCADE
                )
            ''')
            
            # Create license_heartbeat table for periodic validation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_heartbeat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_id INTEGER NOT NULL,
                    activation_id INTEGER NOT NULL,
                    last_heartbeat TEXT DEFAULT CURRENT_TIMESTAMP,
                    heartbeat_interval INTEGER DEFAULT 86400,
                    next_heartbeat TEXT,
                    validation_status TEXT DEFAULT 'valid',
                    server_response TEXT,
                    missed_heartbeats INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (license_id) REFERENCES licenses (id) ON DELETE CASCADE,
                    FOREIGN KEY (activation_id) REFERENCES license_activations (id) ON DELETE CASCADE
                )
            ''')
            
            # Create license_features table for feature-based access control
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    license_type TEXT NOT NULL,
                    feature_name TEXT NOT NULL,
                    feature_category TEXT,
                    is_enabled INTEGER DEFAULT 1,
                    feature_description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(license_type, feature_name)
                )
            ''')
            
            # Create license_servers table for server configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_name TEXT NOT NULL,
                    server_url TEXT NOT NULL,
                    server_key TEXT,
                    is_primary INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    timeout INTEGER DEFAULT 30,
                    retry_count INTEGER DEFAULT 3,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create license_settings table for system configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS license_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'string',
                    description TEXT,
                    is_encrypted INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            print(f"Error creating license tables: {str(e)}")
            raise
    
    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Create indexes for license tables"""
        try:
            # Licenses table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses (license_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_type ON licenses (license_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_expiry ON licenses (expiry_date)')
            
            # License activations table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activations_license_id ON license_activations (license_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activations_id ON license_activations (activation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activations_status ON license_activations (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activations_fingerprint ON license_activations (hardware_fingerprint)')
            
            # Hardware bindings table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bindings_activation_id ON hardware_bindings (activation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bindings_hardware_id ON hardware_bindings (hardware_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_bindings_hash ON hardware_bindings (fingerprint_hash)')
            
            # Audit logs table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_license_key ON license_audit_logs (license_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_activation_id ON license_audit_logs (activation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_event_type ON license_audit_logs (event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON license_audit_logs (timestamp)')
            
            # Blacklisted licenses table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklisted_key ON blacklisted_licenses (license_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklisted_date ON blacklisted_licenses (blacklist_date)')
            
            # License fragments table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fragments_license_id ON license_fragments (license_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fragments_name ON license_fragments (fragment_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fragments_hash ON license_fragments (fragment_hash)')
            
            # License heartbeat table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_heartbeat_license_id ON license_heartbeat (license_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_heartbeat_activation_id ON license_heartbeat (activation_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_heartbeat_next ON license_heartbeat (next_heartbeat)')
            
            # License features table indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_license_type ON license_features (license_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_name ON license_features (feature_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_features_enabled ON license_features (is_enabled)')
        except Exception as e:
            print(f"Error creating license table indexes: {str(e)}")
            raise
    
    def _create_triggers(self, cursor: sqlite3.Cursor) -> None:
        """Create triggers for license tables"""
        try:
            # Trigger to update updated_at timestamp for licenses
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_licenses_timestamp
                AFTER UPDATE ON licenses
                FOR EACH ROW
                BEGIN
                    UPDATE licenses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_activations
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_activations_timestamp
                AFTER UPDATE ON license_activations
                FOR EACH ROW
                BEGIN
                    UPDATE license_activations SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for hardware_bindings
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_hardware_bindings_timestamp
                AFTER UPDATE ON hardware_bindings
                FOR EACH ROW
                BEGIN
                    UPDATE hardware_bindings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for blacklisted_licenses
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_blacklisted_licenses_timestamp
                AFTER UPDATE ON blacklisted_licenses
                FOR EACH ROW
                BEGIN
                    UPDATE blacklisted_licenses SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_fragments
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_fragments_timestamp
                AFTER UPDATE ON license_fragments
                FOR EACH ROW
                BEGIN
                    UPDATE license_fragments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_heartbeat
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_heartbeat_timestamp
                AFTER UPDATE ON license_heartbeat
                FOR EACH ROW
                BEGIN
                    UPDATE license_heartbeat SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_features
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_features_timestamp
                AFTER UPDATE ON license_features
                FOR EACH ROW
                BEGIN
                    UPDATE license_features SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_servers
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_servers_timestamp
                AFTER UPDATE ON license_servers
                FOR EACH ROW
                BEGIN
                    UPDATE license_servers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to update updated_at timestamp for license_settings
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_license_settings_timestamp
                AFTER UPDATE ON license_settings
                FOR EACH ROW
                BEGIN
                    UPDATE license_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            # Trigger to maintain current_activations count
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_current_activations
                AFTER INSERT ON license_activations
                FOR EACH ROW
                BEGIN
                    UPDATE licenses 
                    SET current_activations = (
                        SELECT COUNT(*) FROM license_activations 
                        WHERE license_id = NEW.license_id AND status = 'active'
                    )
                    WHERE id = NEW.license_id;
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_current_activations_delete
                AFTER UPDATE ON license_activations
                FOR EACH ROW
                WHEN OLD.status != NEW.status
                BEGIN
                    UPDATE licenses 
                    SET current_activations = (
                        SELECT COUNT(*) FROM license_activations 
                        WHERE license_id = NEW.license_id AND status = 'active'
                    )
                    WHERE id = NEW.license_id;
                END
            ''')
        except Exception as e:
            print(f"Error creating license table triggers: {str(e)}")
            raise
    
    def insert_default_data(self) -> bool:
        """
        Insert default data for license system
        
        Returns:
            True if insertion successful, False otherwise
        """
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert default license features
            self._insert_default_features(cursor)
            
            # Insert default license servers
            self._insert_default_servers(cursor)
            
            # Insert default license settings
            self._insert_default_settings(cursor)
            
            # Commit changes
            conn.commit()
            
            # Close connection
            conn.close()
            
            print("Default license data inserted successfully")
            return True
        except Exception as e:
            print(f"Error inserting default license data: {str(e)}")
            return False
    
    def _insert_default_features(self, cursor: sqlite3.Cursor) -> None:
        """Insert default license features"""
        try:
            # Trial license features
            trial_features = [
                ('trial', 'basic_orders', 'orders', 1, 'Basic order management'),
                ('trial', 'basic_inventory', 'inventory', 1, 'Basic inventory tracking'),
                ('trial', 'basic_reports', 'reports', 1, 'Basic reporting'),
                ('trial', 'customer_support', 'support', 1, 'Customer support access'),
                ('trial', 'data_export', 'export', 1, 'Data export functionality')
            ]
            
            # Standard license features
            standard_features = [
                ('standard', 'basic_orders', 'orders', 1, 'Basic order management'),
                ('standard', 'basic_inventory', 'inventory', 1, 'Basic inventory tracking'),
                ('standard', 'basic_reports', 'reports', 1, 'Basic reporting'),
                ('standard', 'customer_support', 'support', 1, 'Customer support access'),
                ('standard', 'data_export', 'export', 1, 'Data export functionality'),
                ('standard', 'advanced_orders', 'orders', 1, 'Advanced order management'),
                ('standard', 'advanced_inventory', 'inventory', 1, 'Advanced inventory tracking')
            ]
            
            # Professional license features
            professional_features = [
                ('professional', 'basic_orders', 'orders', 1, 'Basic order management'),
                ('professional', 'basic_inventory', 'inventory', 1, 'Basic inventory tracking'),
                ('professional', 'basic_reports', 'reports', 1, 'Basic reporting'),
                ('professional', 'customer_support', 'support', 1, 'Customer support access'),
                ('professional', 'data_export', 'export', 1, 'Data export functionality'),
                ('professional', 'advanced_orders', 'orders', 1, 'Advanced order management'),
                ('professional', 'advanced_inventory', 'inventory', 1, 'Advanced inventory tracking'),
                ('professional', 'advanced_reports', 'reports', 1, 'Advanced reporting'),
                ('professional', 'multi_user', 'users', 1, 'Multi-user support'),
                ('professional', 'api_access', 'api', 1, 'API access'),
                ('professional', 'custom_themes', 'ui', 1, 'Custom themes')
            ]
            
            # Enterprise license features
            enterprise_features = [
                ('enterprise', 'basic_orders', 'orders', 1, 'Basic order management'),
                ('enterprise', 'basic_inventory', 'inventory', 1, 'Basic inventory tracking'),
                ('enterprise', 'basic_reports', 'reports', 1, 'Basic reporting'),
                ('enterprise', 'customer_support', 'support', 1, 'Customer support access'),
                ('enterprise', 'data_export', 'export', 1, 'Data export functionality'),
                ('enterprise', 'advanced_orders', 'orders', 1, 'Advanced order management'),
                ('enterprise', 'advanced_inventory', 'inventory', 1, 'Advanced inventory tracking'),
                ('enterprise', 'advanced_reports', 'reports', 1, 'Advanced reporting'),
                ('enterprise', 'multi_user', 'users', 1, 'Multi-user support'),
                ('enterprise', 'api_access', 'api', 1, 'API access'),
                ('enterprise', 'custom_themes', 'ui', 1, 'Custom themes'),
                ('enterprise', 'priority_support', 'support', 1, 'Priority support'),
                ('enterprise', 'custom_integrations', 'integrations', 1, 'Custom integrations'),
                ('enterprise', 'advanced_analytics', 'analytics', 1, 'Advanced analytics'),
                ('enterprise', 'white_labeling', 'branding', 1, 'White labeling')
            ]
            
            # Insert all features
            all_features = trial_features + standard_features + professional_features + enterprise_features
            
            for feature in all_features:
                cursor.execute('''
                    INSERT OR IGNORE INTO license_features 
                    (license_type, feature_name, feature_category, is_enabled, feature_description)
                    VALUES (?, ?, ?, ?, ?)
                ''', feature)
        except Exception as e:
            print(f"Error inserting default license features: {str(e)}")
            raise
    
    def _insert_default_servers(self, cursor: sqlite3.Cursor) -> None:
        """Insert default license servers"""
        try:
            # Default license servers
            servers = [
                ('Primary Server', 'https://license.example.com/api', None, 1, 1, 30, 3),
                ('Backup Server', 'https://backup-license.example.com/api', None, 0, 1, 30, 3)
            ]
            
            for server in servers:
                cursor.execute('''
                    INSERT OR IGNORE INTO license_servers 
                    (server_name, server_url, server_key, is_primary, is_active, timeout, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', server)
        except Exception as e:
            print(f"Error inserting default license servers: {str(e)}")
            raise
    
    def _insert_default_settings(self, cursor: sqlite3.Cursor) -> None:
        """Insert default license settings"""
        try:
            # Default license settings
            settings = [
                ('trial_duration_days', '30', 'integer', 'Duration of trial period in days', 0),
                ('max_activations_per_license', '1', 'integer', 'Maximum number of activations per license', 0),
                ('heartbeat_interval_seconds', '86400', 'integer', 'Heartbeat interval in seconds', 0),
                ('offline_grace_period_days', '7', 'integer', 'Offline grace period in days', 0),
                ('max_failed_heartbeats', '3', 'integer', 'Maximum failed heartbeats before deactivation', 0),
                ('enable_hardware_binding', 'true', 'boolean', 'Enable hardware binding', 0),
                ('enable_fragmented_storage', 'true', 'boolean', 'Enable fragmented license storage', 0),
                ('enable_anti_tamper', 'true', 'boolean', 'Enable anti-tampering protection', 0),
                ('license_server_timeout', '30', 'integer', 'License server timeout in seconds', 0),
                ('license_server_retry_count', '3', 'integer', 'License server retry count', 0),
                ('encryption_algorithm', 'AES-256-GCM', 'string', 'Encryption algorithm for license data', 0),
                ('signature_algorithm', 'RSA-4096', 'string', 'Signature algorithm for license verification', 0),
                ('hardware_fingerprint_method', 'advanced', 'string', 'Hardware fingerprint method', 0),
                ('enable_debug_logging', 'false', 'boolean', 'Enable debug logging for license system', 0),
                ('license_validation_level', 'strict', 'string', 'License validation level', 0)
            ]
            
            for setting in settings:
                cursor.execute('''
                    INSERT OR IGNORE INTO license_settings 
                    (setting_key, setting_value, setting_type, description, is_encrypted)
                    VALUES (?, ?, ?, ?, ?)
                ''', setting)
        except Exception as e:
            print(f"Error inserting default license settings: {str(e)}")
            raise


def run_migration() -> bool:
    """
    Run the license tables migration
    
    Returns:
        True if migration successful, False otherwise
    """
    try:
        migration = AddLicenseTables()
        
        # Run migration
        if not migration.run_migration():
            return False
        
        # Insert default data
        if not migration.insert_default_data():
            return False
        
        return True
    except Exception as e:
        print(f"Error running license tables migration: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_migration()
    if success:
        print("License tables migration completed successfully")
    else:
        print("License tables migration failed")