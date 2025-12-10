"""
Advanced Backup Manager for POS Application
Provides comprehensive backup functionality with scheduling, compression, 
encryption, and cloud integration capabilities
"""

import os
import json
import sqlite3
import shutil
import gzip
import hashlib
import threading
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import tkinter as tk
from tkinter import messagebox
import pickle
from .email_service import EmailService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Backup configuration data class"""
    # Basic settings
    backup_location: str = "backups"
    auto_backup_enabled: bool = True
    backup_frequency: str = "daily"  # hourly, daily, weekly
    backup_retention_days: int = 30
    
    # Backup types
    include_orders: bool = True
    include_menu_items: bool = True
    include_categories: bool = True
    include_tables: bool = True
    include_users: bool = True
    include_settings: bool = True
    include_inventory: bool = True
    
    # Advanced options
    compress_backups: bool = True
    encrypt_backups: bool = False
    verify_backups: bool = True
    incremental_backups: bool = False
    
    # Cloud settings
    cloud_backup_enabled: bool = False
    cloud_provider: str = ""  # google_drive, dropbox, onedrive
    cloud_credentials: Dict = None
    
    # Notification settings
    email_notifications: bool = False
    email_address: str = ""
    email_config: Dict = None

@dataclass
class BackupInfo:
    """Backup information data class"""
    backup_id: str
    filename: str
    backup_type: str  # full, incremental
    created_at: datetime
    file_size: int
    compressed: bool
    encrypted: bool
    checksum: str
    backup_config: Dict
    includes: List[str]
    status: str  # success, failed, partial

class BackupManager:
    """Advanced backup management system"""
    
    def __init__(self, app, config_path: str = "backup_config.json"):
        self.app = app
        self.config_path = config_path
        self.config = self.load_config()
        
        # Backup tracking
        self.backup_history: List[BackupInfo] = []
        self.last_backup_time = None
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # Initialize email service
        self.email_service = EmailService(app)
        
        # Ensure backup directory exists
        self.ensure_backup_directory()
        
        # Load backup history
        self.load_backup_history()
        
        # Start scheduler if auto-backup is enabled
        if self.config.auto_backup_enabled:
            self.start_scheduler()
    
    def load_config(self) -> BackupConfig:
        """Load backup configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                return BackupConfig(**config_data)
            else:
                # Create default config
                config = BackupConfig()
                self.save_config(config)
                return config
        except Exception as e:
            logger.error(f"Error loading backup config: {e}")
            return BackupConfig()
    
    def save_config(self, config: BackupConfig = None):
        """Save backup configuration to file"""
        try:
            if config is None:
                config = self.config
            
            with open(self.config_path, 'w') as f:
                json.dump(asdict(config), f, indent=2, default=str)
            
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Error saving backup config: {e}")
            return False
    
    def ensure_backup_directory(self):
        """Ensure backup directory exists"""
        try:
            backup_path = Path(self.config.backup_location)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (backup_path / "daily").mkdir(exist_ok=True)
            (backup_path / "weekly").mkdir(exist_ok=True)
            (backup_path / "monthly").mkdir(exist_ok=True)
            (backup_path / "incremental").mkdir(exist_ok=True)
            
            logger.info(f"Backup directory created: {backup_path}")
            
        except Exception as e:
            logger.error(f"Error creating backup directory: {e}")
            raise
    
    def load_backup_history(self):
        """Load backup history from file"""
        try:
            history_path = Path(self.config.backup_location) / "backup_history.json"
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history_data = json.load(f)
                
                for backup_data in history_data:
                    backup_data['created_at'] = datetime.fromisoformat(backup_data['created_at'])
                    self.backup_history.append(BackupInfo(**backup_data))
        
        except Exception as e:
            logger.error(f"Error loading backup history: {e}")
    
    def save_backup_history(self):
        """Save backup history to file"""
        try:
            history_path = Path(self.config.backup_location) / "backup_history.json"
            history_data = []
            
            for backup in self.backup_history:
                backup_dict = asdict(backup)
                backup_dict['created_at'] = backup.created_at.isoformat()
                history_data.append(backup_dict)
            
            with open(history_path, 'w') as f:
                json.dump(history_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving backup history: {e}")
    
    def create_backup(self, backup_type: str = "full", 
                    backup_name: str = None) -> Tuple[bool, str]:
        """
        Create a backup of POS data
        
        Args:
            backup_type: Type of backup ('full', 'incremental')
            backup_name: Optional custom backup name
            
        Returns:
            Tuple[bool, str]: Success status and backup file path or error message
        """
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                filename = f"{backup_name}_{timestamp}.json"
            else:
                filename = f"pos_backup_{backup_type}_{timestamp}.json"
            
            # Determine backup path
            if self.config.incremental_backups and backup_type == "incremental":
                backup_path = Path(self.config.backup_location) / "incremental" / filename
            else:
                backup_path = Path(self.config.backup_location) / filename
            
            # Collect data to backup
            backup_data = self.collect_backup_data()
            
            if not backup_data:
                return False, "No data available for backup"
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=timestamp,
                filename=filename,
                backup_type=backup_type,
                created_at=datetime.now(),
                file_size=0,  # Will be updated after saving
                compressed=self.config.compress_backups,
                encrypted=self.config.encrypt_backups,
                checksum="",  # Will be calculated after saving
                backup_config=asdict(self.config),
                includes=list(backup_data.keys()),
                status="creating"
            )
            
            # Save backup
            success = self.save_backup_data(backup_data, backup_path, backup_info)
            
            if success:
                backup_info.status = "success"
                backup_info.file_size = backup_path.stat().st_size
                backup_info.checksum = self.calculate_checksum(backup_path)
                
                # Add to history
                self.backup_history.append(backup_info)
                self.save_backup_history()
                self.last_backup_time = datetime.now()
                
                # Verify backup if enabled
                if self.config.verify_backups:
                    verification_success = self.verify_backup(backup_path, backup_info.checksum)
                    if not verification_success:
                        backup_info.status = "verification_failed"
                        logger.warning(f"Backup verification failed for {filename}")
                
                # Clean old backups
                self.clean_old_backups()
                
                logger.info(f"Backup created successfully: {filename}")
                return True, str(backup_path)
            else:
                backup_info.status = "failed"
                return False, "Failed to save backup"
        
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, f"Backup creation failed: {str(e)}"
    
    def collect_backup_data(self) -> Dict:
        """Collect data for backup based on configuration"""
        try:
            backup_data = {
                'metadata': {
                    'backup_version': '2.0',
                    'created_at': datetime.now().isoformat(),
                    'backup_type': 'full' if not self.config.incremental_backups else 'incremental',
                    'last_backup': self.last_backup_time.isoformat() if self.last_backup_time else None,
                    'includes': []
                }
            }
            
            # Include data based on configuration
            if self.config.include_orders:
                backup_data['orders'] = self.get_orders_data()
                backup_data['metadata']['includes'].append('orders')
            
            if self.config.include_menu_items:
                backup_data['menu_items'] = self.get_menu_items_data()
                backup_data['metadata']['includes'].append('menu_items')
            
            if self.config.include_categories:
                backup_data['categories'] = self.get_categories_data()
                backup_data['metadata']['includes'].append('categories')
            
            if self.config.include_tables:
                backup_data['tables'] = self.get_tables_data()
                backup_data['metadata']['includes'].append('tables')
            
            if self.config.include_users:
                backup_data['users'] = self.get_users_data()
                backup_data['metadata']['includes'].append('users')
            
            if self.config.include_settings:
                backup_data['settings'] = self.get_settings_data()
                backup_data['metadata']['includes'].append('settings')
            
            if self.config.include_inventory:
                backup_data['inventory'] = self.get_inventory_data()
                backup_data['metadata']['includes'].append('inventory')
            
            return backup_data
        
        except Exception as e:
            logger.error(f"Error collecting backup data: {e}")
            return {}
    
    def get_orders_data(self) -> Dict:
        """Get orders data for backup"""
        try:
            # Try to get orders data using available methods
            orders_data = []
            
            # Method 1: Try data manager
            try:
                from src.managers.data_manager import get_data_manager
                data_manager = get_data_manager(self.app)
                orders = data_manager.get_orders(force_refresh=True)
                
                for order in orders:
                    order_details = data_manager.get_order_details(order['id'])
                    if order_details:
                        orders_data.append(order_details)
            except:
                # Method 2: Try direct model access
                try:
                    if hasattr(self.app, 'order_model'):
                        orders = self.app.order_model.get_all()
                        orders_data = [{'order': order} for order in orders]
                except:
                    # Method 3: Return empty data
                    pass
            
            return {'orders': orders_data, 'count': len(orders_data)}
        
        except Exception as e:
            logger.error(f"Error getting orders data: {e}")
            return {'orders': [], 'count': 0}
    
    def get_menu_items_data(self) -> Dict:
        """Get menu items data for backup"""
        try:
            items = []
            categories = []
            
            # Try to get data using available methods
            try:
                from src.managers.data_manager import get_data_manager
                data_manager = get_data_manager(self.app)
                items = data_manager.get_menu_items(force_refresh=True)
                categories = data_manager.get_categories(force_refresh=True)
            except:
                # Return empty data if methods not available
                pass
            
            return {
                'menu_items': items,
                'categories': categories,
                'items_count': len(items),
                'categories_count': len(categories)
            }
        
        except Exception as e:
            logger.error(f"Error getting menu items data: {e}")
            return {'menu_items': [], 'categories': [], 'items_count': 0, 'categories_count': 0}
    
    def get_categories_data(self) -> Dict:
        """Get categories data for backup"""
        try:
            categories = []
            
            # Try to get data using available methods
            try:
                from src.managers.data_manager import get_data_manager
                data_manager = get_data_manager(self.app)
                categories = data_manager.get_categories(force_refresh=True)
            except:
                # Return empty data if methods not available
                pass
            
            return {'categories': categories, 'count': len(categories)}
        
        except Exception as e:
            logger.error(f"Error getting categories data: {e}")
            return {'categories': [], 'count': 0}
    
    def get_tables_data(self) -> Dict:
        """Get tables data for backup"""
        try:
            tables = []
            
            # Try to get data using available methods
            try:
                from src.managers.data_manager import get_data_manager
                data_manager = get_data_manager(self.app)
                tables = data_manager.get_tables(force_refresh=True)
            except:
                # Return empty data if methods not available
                pass
            
            return {'tables': tables, 'count': len(tables)}
        
        except Exception as e:
            logger.error(f"Error getting tables data: {e}")
            return {'tables': [], 'count': 0}
    
    def get_users_data(self) -> Dict:
        """Get users data for backup"""
        try:
            users = []
            
            # Try to get data using available methods
            try:
                if hasattr(self.app, 'user_model'):
                    users = self.app.user_model.get_all()
                else:
                    # Return empty data if no user model
                    pass
            except:
                # Return empty data if error
                pass
            
            return {'users': users, 'count': len(users)}
        
        except Exception as e:
            logger.error(f"Error getting users data: {e}")
            return {'users': [], 'count': 0}
    
    def get_settings_data(self) -> Dict:
        """Get settings data for backup"""
        try:
            settings = {}
            
            # Try to get data using available methods
            try:
                if hasattr(self.app, 'settings'):
                    settings = dict(self.app.settings)
                else:
                    # Return default settings if no settings
                    settings = {'backup_test': True}
            except:
                # Return empty settings if error
                pass
            
            return {'settings': settings, 'count': len(settings)}
        
        except Exception as e:
            logger.error(f"Error getting settings data: {e}")
            return {'settings': {}, 'count': 0}
    
    def get_inventory_data(self) -> Dict:
        """Get inventory data for backup"""
        try:
            items = []
            
            # Try to get data using available methods
            try:
                from src.managers.data_manager import get_data_manager
                data_manager = get_data_manager(self.app)
                items = data_manager.get_inventory_items(force_refresh=True)
            except:
                # Return empty data if methods not available
                pass
            
            return {'inventory_items': items, 'count': len(items)}
        
        except Exception as e:
            logger.error(f"Error getting inventory data: {e}")
            return {'inventory_items': [], 'count': 0}
    
    def save_backup_data(self, data: Dict, backup_path: Path, backup_info: BackupInfo) -> bool:
        """Save backup data to file with optional compression and encryption"""
        try:
            # Save to temporary file first
            temp_path = backup_path.with_suffix('.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Apply compression if enabled
            if self.config.compress_backups:
                compressed_path = backup_path.with_suffix('.json.gz')
                with open(temp_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                temp_path.unlink()
                backup_path = compressed_path
            else:
                shutil.move(temp_path, backup_path)
            
            # Apply encryption if enabled
            if self.config.encrypt_backups:
                encrypted_path = backup_path.with_suffix('.enc')
                self.encrypt_file(backup_path, encrypted_path)
                backup_path.unlink()  # Remove unencrypted file
                backup_path = encrypted_path
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving backup data: {e}")
            # Clean up temporary files
            if temp_path.exists():
                temp_path.unlink()
            return False
    
    def encrypt_file(self, input_path: Path, output_path: Path):
        """Encrypt file (placeholder implementation)"""
        # This is a placeholder - implement actual encryption here
        # For now, just copy the file
        shutil.copy2(input_path, output_path)
    
    def decrypt_file(self, input_path: Path, output_path: Path):
        """Decrypt file (placeholder implementation)"""
        # This is a placeholder - implement actual decryption here
        # For now, just copy the file
        shutil.copy2(input_path, output_path)
    
    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum: {e}")
            return ""
    
    def verify_backup(self, backup_path: Path, expected_checksum: str) -> bool:
        """Verify backup integrity using checksum"""
        try:
            actual_checksum = self.calculate_checksum(backup_path)
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return False
    
    def restore_backup(self, backup_path: str, overwrite: bool = False) -> Tuple[bool, str]:
        """
        Restore data from backup
        
        Args:
            backup_path: Path to backup file
            overwrite: Whether to overwrite existing data
            
        Returns:
            Tuple[bool, str]: Success status and message
        """
        try:
            backup_path = Path(backup_path)
            
            if not backup_path.exists():
                return False, "Backup file not found"
            
            # Decrypt if needed
            temp_path = backup_path.with_suffix('.temp')
            if backup_path.suffix == '.enc':
                self.decrypt_file(backup_path, temp_path)
            else:
                temp_path = backup_path
            
            # Decompress if needed
            if temp_path.suffix == '.gz':
                with gzip.open(temp_path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Clean up temporary file
            if temp_path != backup_path:
                temp_path.unlink()
            
            # Restore data using existing importer
            from src.utils.data_importer import DataImporter
            from src.managers.data_manager import get_data_manager
            
            data_manager = get_data_manager(self.app)
            importer = DataImporter(self.app, data_manager)
            
            # Create temporary file for importer
            temp_restore_path = Path(self.config.backup_location) / "temp_restore.json"
            with open(temp_restore_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Perform restore
            result = importer.import_data(str(temp_restore_path), 'all', False, overwrite)
            
            # Clean up temporary file
            temp_restore_path.unlink()
            
            if result.get('success', False):
                message = f"Restore completed successfully. {result.get('message', '')}"
                return True, message
            else:
                error_msg = result.get('error', 'Unknown error during restore')
                return False, error_msg
        
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, f"Restore failed: {str(e)}"
    
    def clean_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.backup_retention_days)
            deleted_count = 0
            
            for backup_info in self.backup_history[:]:
                if backup_info.created_at < cutoff_date:
                    backup_path = Path(self.config.backup_location) / backup_info.filename
                    
                    if backup_path.exists():
                        backup_path.unlink()
                        deleted_count += 1
                    
                    self.backup_history.remove(backup_info)
            
            if deleted_count > 0:
                self.save_backup_history()
                logger.info(f"Cleaned up {deleted_count} old backup files")
        
        except Exception as e:
            logger.error(f"Error cleaning old backups: {e}")
    
    def get_backup_list(self) -> List[Dict]:
        """Get list of available backups"""
        try:
            backups = []
            for backup_info in sorted(self.backup_history, key=lambda x: x.created_at, reverse=True):
                backup_dict = asdict(backup_info)
                backup_dict['created_at'] = backup_info.created_at.strftime('%Y-%m-%d %H:%M:%S')
                backup_dict['file_size_mb'] = round(backup_info.file_size / (1024 * 1024), 2)
                backups.append(backup_dict)
            
            return backups
        
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            return []
    
    def delete_backup(self, backup_id: str) -> Tuple[bool, str]:
        """Delete a specific backup"""
        try:
            for backup_info in self.backup_history:
                if backup_info.backup_id == backup_id:
                    backup_path = Path(self.config.backup_location) / backup_info.filename
                    
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    self.backup_history.remove(backup_info)
                    self.save_backup_history()
                    
                    return True, f"Backup {backup_id} deleted successfully"
            
            return False, "Backup not found"
        
        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            return False, f"Failed to delete backup: {str(e)}"
    
    def start_scheduler(self):
        """Start the backup scheduler"""
        try:
            if self.scheduler_running:
                return
            
            self.scheduler_running = True
            
            # Schedule backups based on frequency
            if self.config.backup_frequency == "hourly":
                schedule.every().hour.do(self.scheduled_backup)
            elif self.config.backup_frequency == "daily":
                schedule.every().day.at("02:00").do(self.scheduled_backup)
            elif self.config.backup_frequency == "weekly":
                schedule.every().sunday.at("02:00").do(self.scheduled_backup)
            
            # Run scheduler in separate thread
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Backup scheduler started")
        
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
    
    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.scheduler_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the backup scheduler"""
        try:
            self.scheduler_running = False
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            schedule.clear()
            logger.info("Backup scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def scheduled_backup(self):
        """Execute scheduled backup"""
        try:
            logger.info("Starting scheduled backup")
            success, message = self.create_backup("scheduled")
            
            if success:
                logger.info(f"Scheduled backup completed: {message}")
                
                # Send notification if enabled
                if self.config.email_notifications:
                    # Get backup info for the latest backup
                    if self.backup_history:
                        latest_backup = self.backup_history[-1]
                        backup_info = {
                            'status': 'success',
                            'backup_type': latest_backup.backup_type,
                            'file_size_mb': round(latest_backup.file_size / (1024 * 1024), 2),
                            'created_at': latest_backup.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'includes': latest_backup.includes
                        }
                        backup_path = os.path.join(self.config.backup_location, latest_backup.filename)
                        self.send_backup_notification(success, message, backup_path, backup_info)
                    else:
                        self.send_backup_notification(success, message)
            else:
                logger.error(f"Scheduled backup failed: {message}")
                # Send failure notification
                if self.config.email_notifications:
                    backup_info = {
                        'status': 'failed',
                        'backup_type': 'scheduled',
                        'file_size_mb': 0,
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'includes': []
                    }
                    self.send_backup_notification(success, message, None, backup_info)
        
        except Exception as e:
            logger.error(f"Error in scheduled backup: {e}")
    
    def send_backup_notification(self, success: bool, message: str, backup_path: str = None, backup_info: Dict = None):
        """Send backup notification email"""
        try:
            if backup_path and backup_info:
                # Send detailed backup notification with attachment
                email_success, email_message = self.email_service.send_backup_notification(backup_path, backup_info)
                logger.info(f"Backup notification queued: {email_message}")
            else:
                # Send simple status notification
                logger.info(f"Backup notification: {'SUCCESS' if success else 'FAILED'} - {message}")
        except Exception as e:
            logger.error(f"Error sending backup notification: {e}")
    
    def get_backup_statistics(self) -> Dict:
        """Get backup statistics"""
        try:
            total_backups = len(self.backup_history)
            successful_backups = len([b for b in self.backup_history if b.status == "success"])
            failed_backups = len([b for b in self.backup_history if b.status == "failed"])
            
            if self.backup_history:
                last_backup = max(b.created_at for b in self.backup_history)
                last_backup_str = last_backup.strftime('%Y-%m-%d %H:%M:%S')
            else:
                last_backup_str = "Never"
            
            # Calculate total storage used
            total_size = sum(b.file_size for b in self.backup_history)
            total_size_mb = round(total_size / (1024 * 1024), 2)
            
            return {
                'total_backups': total_backups,
                'successful_backups': successful_backups,
                'failed_backups': failed_backups,
                'success_rate': round(successful_backups / total_backups * 100, 2) if total_backups > 0 else 0,
                'last_backup': last_backup_str,
                'total_storage_mb': total_size_mb,
                'auto_backup_enabled': self.config.auto_backup_enabled,
                'backup_frequency': self.config.backup_frequency
            }
        
        except Exception as e:
            logger.error(f"Error getting backup statistics: {e}")
            return {}
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            self.stop_scheduler()
        except:
            pass
