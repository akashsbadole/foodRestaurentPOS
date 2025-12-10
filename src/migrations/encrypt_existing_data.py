"""
Database migration script to encrypt existing sensitive data for Tkinter desktop version
Run this script once after implementing encryption to encrypt all existing sensitive data
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add parent directory to path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.encryption import get_encryption_manager
from src.utils.key_manager import get_key_manager
from src.models.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataEncryptionMigrator:
    """Handles migration of existing data to encrypted format"""
    
    def __init__(self, db_path):
        """
        Initialize migrator
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.db = Database(db_path)
        self.encryption_manager = get_encryption_manager()
        self.key_manager = get_key_manager()
    
    def migrate_all_data(self):
        """Migrate all sensitive data to encrypted format"""
        logger.info("Starting data encryption migration...")
        
        try:
            # Verify key integrity before migration
            if not self.key_manager.verify_key_integrity():
                logger.error("Key integrity verification failed. Aborting migration.")
                return False
            
            # Create backup before migration
            backup_path = self.key_manager.create_key_backup("before_migration_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            logger.info(f"Key backed up to: {backup_path}")
            
            # Migrate users table
            self._migrate_users()
            
            # Migrate orders table
            self._migrate_orders()
            
            # Migrate payments table
            self._migrate_payments()
            
            logger.info("Data encryption migration completed successfully!")
            
            # Create migration record
            self._create_migration_record()
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.db.rollback()
            return False
    
    def _migrate_users(self):
        """Migrate user passwords to encrypted format"""
        logger.info("Migrating users table...")
        
        try:
            # Get all users
            self.db.execute_query("SELECT id, username, password, role FROM users")
            users = self.db.fetch_all()
            
            migrated_count = 0
            for user_id, username, password, role in users:
                try:
                    # Check if password is already encrypted
                    if password and not password.startswith('gAAAA'):
                        # Encrypt password
                        encrypted_password = self.encryption_manager.encrypt_field(password)
                        
                        # Update record
                        self.db.execute_query(
                            "UPDATE users SET password = ? WHERE id = ?",
                            (encrypted_password, user_id)
                        )
                        
                        migrated_count += 1
                        logger.debug(f"Encrypted password for user: {username}")
                
                except Exception as e:
                    logger.warning(f"Failed to migrate user {username}: {str(e)}")
            
            self.db.commit()
            logger.info(f"Users migration completed: {migrated_count} passwords encrypted")
            
        except Exception as e:
            logger.error(f"Users migration failed: {str(e)}")
            raise
    
    def _migrate_orders(self):
        """Migrate order customer information to encrypted format"""
        logger.info("Migrating orders table...")
        
        try:
            # Get all orders with customer information
            self.db.execute_query("""
                SELECT id, order_number, customer_name, customer_mobile 
                FROM orders 
                WHERE customer_name IS NOT NULL OR customer_mobile IS NOT NULL
            """)
            orders = self.db.fetch_all()
            
            migrated_count = 0
            for order_id, order_number, customer_name, customer_mobile in orders:
                try:
                    updates = []
                    params = []
                    
                    # Check and encrypt customer name
                    if customer_name and not customer_name.startswith('gAAAA'):
                        encrypted_name = self.encryption_manager.encrypt_field(customer_name)
                        updates.append("customer_name = ?")
                        params.append(encrypted_name)
                        logger.debug(f"Encrypted customer name for order: {order_number}")
                    
                    # Check and encrypt customer mobile
                    if customer_mobile and not customer_mobile.startswith('gAAAA'):
                        encrypted_mobile = self.encryption_manager.encrypt_field(customer_mobile)
                        updates.append("customer_mobile = ?")
                        params.append(encrypted_mobile)
                        logger.debug(f"Encrypted customer mobile for order: {order_number}")
                    
                    # Update if there are changes
                    if updates:
                        params.append(order_id)
                        update_query = f"UPDATE orders SET {', '.join(updates)} WHERE id = ?"
                        self.db.execute_query(update_query, tuple(params))
                        migrated_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to migrate order {order_number}: {str(e)}")
            
            self.db.commit()
            logger.info(f"Orders migration completed: {migrated_count} orders updated")
            
        except Exception as e:
            logger.error(f"Orders migration failed: {str(e)}")
            raise
    
    def _migrate_payments(self):
        """Migrate payment details to encrypted format"""
        logger.info("Migrating payments table...")
        
        try:
            # Get all payments with details
            self.db.execute_query("""
                SELECT id, order_id, payment_mode, payment_details 
                FROM payments 
                WHERE payment_details IS NOT NULL
            """)
            payments = self.db.fetch_all()
            
            migrated_count = 0
            for payment_id, order_id, payment_mode, payment_details in payments:
                try:
                    # Check if payment details are already encrypted
                    if payment_details and not payment_details.startswith('gAAAA'):
                        # Parse payment details if they're in JSON format
                        try:
                            details_dict = json.loads(payment_details) if isinstance(payment_details, str) else payment_details
                            
                            # Encrypt sensitive fields based on payment mode
                            if payment_mode == "Card":
                                if 'card_number' in details_dict:
                                    details_dict['card_number'] = self.encryption_manager.encrypt_with_integrity(details_dict['card_number'])
                                if 'expiry' in details_dict:
                                    details_dict['expiry'] = self.encryption_manager.encrypt_with_integrity(details_dict['expiry'])
                                if 'card_holder' in details_dict:
                                    details_dict['card_holder'] = self.encryption_manager.encrypt_with_integrity(details_dict['card_holder'])
                            
                            elif payment_mode == "UPI":
                                if 'upi_id' in details_dict:
                                    details_dict['upi_id'] = self.encryption_manager.encrypt_with_integrity(details_dict['upi_id'])
                            
                            elif payment_mode == "Wallet":
                                if 'wallet_number' in details_dict:
                                    details_dict['wallet_number'] = self.encryption_manager.encrypt_with_integrity(details_dict['wallet_number'])
                            
                            elif payment_mode == "Credit":
                                if 'customer_name' in details_dict:
                                    details_dict['customer_name'] = self.encryption_manager.encrypt_with_integrity(details_dict['customer_name'])
                            
                            # Convert back to JSON
                            encrypted_details = json.dumps(details_dict)
                            
                        except (json.JSONDecodeError, TypeError):
                            # If not JSON, encrypt as plain text
                            encrypted_details = self.encryption_manager.encrypt_with_integrity(payment_details)
                        
                        # Update record
                        self.db.execute_query(
                            "UPDATE payments SET payment_details = ? WHERE id = ?",
                            (encrypted_details, payment_id)
                        )
                        
                        migrated_count += 1
                        logger.debug(f"Encrypted payment details for payment ID: {payment_id}")
                
                except Exception as e:
                    logger.warning(f"Failed to migrate payment {payment_id}: {str(e)}")
            
            self.db.commit()
            logger.info(f"Payments migration completed: {migrated_count} payments updated")
            
        except Exception as e:
            logger.error(f"Payments migration failed: {str(e)}")
            raise
    
    def _create_migration_record(self):
        """Create a record of this migration"""
        try:
            migration_record = {
                'migration_type': 'encryption',
                'version': '2.0',
                'timestamp': datetime.utcnow().isoformat(),
                'description': 'Migrated existing sensitive data to encrypted format'
            }
            
            # Store in settings table
            self.db.execute_query(
                "INSERT INTO settings (key, value, description) VALUES (?, ?, ?)",
                (
                    'encryption_migration_v2',
                    json.dumps(migration_record),
                    'Encryption migration record'
                )
            )
            self.db.commit()
            
            logger.info("Migration record created")
            
        except Exception as e:
            logger.warning(f"Failed to create migration record: {str(e)}")
    
    def verify_migration(self):
        """Verify that migration was successful"""
        logger.info("Verifying encryption migration...")
        
        try:
            issues = []
            
            # Verify users
            self.db.execute_query("SELECT username, password FROM users WHERE password IS NOT NULL")
            users = self.db.fetch_all()
            
            for username, password in users:
                if password and not password.startswith('gAAAA'):
                    issues.append(f"Unencrypted password for user: {username}")
            
            # Verify orders
            self.db.execute_query("""
                SELECT order_number, customer_name, customer_mobile 
                FROM orders 
                WHERE customer_name IS NOT NULL OR customer_mobile IS NOT NULL
            """)
            orders = self.db.fetch_all()
            
            for order_number, customer_name, customer_mobile in orders:
                if customer_name and not customer_name.startswith('gAAAA'):
                    issues.append(f"Unencrypted customer name for order: {order_number}")
                if customer_mobile and not customer_mobile.startswith('gAAAA'):
                    issues.append(f"Unencrypted customer mobile for order: {order_number}")
            
            # Verify payments
            self.db.execute_query("""
                SELECT id, payment_mode, payment_details 
                FROM payments 
                WHERE payment_details IS NOT NULL
            """)
            payments = self.db.fetch_all()
            
            for payment_id, payment_mode, payment_details in payments:
                if payment_details and not payment_details.startswith('gAAAA'):
                    issues.append(f"Unencrypted payment details for payment ID: {payment_id}")
            
            if issues:
                logger.warning(f"Migration verification found {len(issues)} issues:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
                return False
            else:
                logger.info("Migration verification completed successfully!")
                return True
                
        except Exception as e:
            logger.error(f"Migration verification failed: {str(e)}")
            return False

def main():
    """Main migration function"""
    # Default database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'restaurant_pos.db')
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Create migrator and run migration
    migrator = DataEncryptionMigrator(db_path)
    
    if len(sys.argv) > 2 and sys.argv[2] == "--verify":
        success = migrator.verify_migration()
    else:
        success = migrator.migrate_all_data()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)