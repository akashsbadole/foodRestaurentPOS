"""
License Integration Module for POS MVP application
Handles integration of license system with existing application
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable

from src.utils.license_manager import LicenseManager
from src.ui.license_activation_dialog import LicenseActivationDialog
from src.ui.license_status_screen import LicenseStatusScreen
from src.ui.trial_management_dialog import TrialManagementDialog
from src.ui.license_upgrade_dialog import LicenseUpgradeDialog
from src.ui.license_transfer_dialog import LicenseTransferDialog
from src.migrations.add_license_tables import run_migration
from src.utils.event_dispatcher import event_dispatcher, EventType


class LicenseIntegration:
    """
    License Integration class for managing license system integration
    Handles license validation, UI integration, and feature access control
    """
    
    def __init__(self, app):
        """
        Initialize license integration
        
        Args:
            app: Application instance
        """
        self.app = app
        self.license_manager = None
        self.license_status = None
        self.is_licensed = False
        self.trial_mode = False
        self.feature_access = {}
        
        # Initialize license system
        self._initialize_license_system()
    
    def _initialize_license_system(self) -> None:
        """Initialize license system components"""
        try:
            # Run database migration if needed
            self._ensure_license_tables()
            
            # Initialize license manager
            self.license_manager = LicenseManager()
            
            # Check license status on startup
            self._check_license_on_startup()
            
            # Initialize feature access
            self._initialize_feature_access()
            
            print("License system initialized successfully")
        except Exception as e:
            print(f"Error initializing license system: {str(e)}")
            messagebox.showerror("License Error", f"Failed to initialize license system: {str(e)}")
    
    def _ensure_license_tables(self) -> None:
        """Ensure license tables exist in database"""
        try:
            # Check if license tables exist
            if not self._check_license_tables_exist():
                # Run migration to create license tables
                if run_migration():
                    print("License tables created successfully")
                else:
                    raise Exception("Failed to create license tables")
        except Exception as e:
            print(f"Error ensuring license tables: {str(e)}")
            raise
    
    def _check_license_tables_exist(self) -> bool:
        """Check if license tables exist in database"""
        try:
            # Get database connection
            conn = self.app.db.conn
            
            # Check if licenses table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='licenses'
            """)
            
            result = cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Error checking license tables: {str(e)}")
            return False
    
    def _check_license_on_startup(self) -> None:
        """Check license status on application startup"""
        try:
            # Get license status
            self.license_status = self.license_manager.get_license_status()
            
            # Check if license_status is None or empty
            if not self.license_status:
                print("No license status available")
                self.is_licensed = False
                self.trial_mode = False
                self._show_license_activation_dialog()
                return
            
            # Check if license is valid
            license_info = self.license_status.get('license_info', {})
            activation_info = self.license_status.get('activation_info', {})
            
            # Additional null checks for license_info and activation_info
            if not license_info:
                license_info = {}
            if not activation_info:
                activation_info = {}
            
            license_status = license_info.get('status', 'unknown')
            
            if license_status == 'active':
                self.is_licensed = True
                self.trial_mode = False
                print("Active license found")
                
                # Dispatch license activated event
                license_key = license_info.get('license_key', '')
                license_type = license_info.get('license_type', 'unknown')
                expiry_date = license_info.get('expiry_date', '')
                event_dispatcher.license_activated(license_key, license_type, expiry_date)
                
            elif license_status == 'trial':
                self.is_licensed = True
                self.trial_mode = True
                print("Trial license found")
                
                # Dispatch trial started event
                trial_info = activation_info.get('trial_info', {})
                if not trial_info:
                    trial_info = {}
                trial_days = trial_info.get('trial_days', 0)
                expiry_date = trial_info.get('expiry_date', '')
                event_dispatcher.trial_started(trial_days, expiry_date)
                
            else:
                self.is_licensed = False
                self.trial_mode = False
                print("No valid license found")
                
                # Show license activation dialog
                self._show_license_activation_dialog()
        except Exception as e:
            print(f"Error checking license on startup: {str(e)}")
            self.is_licensed = False
            self.trial_mode = False
            # Show license activation dialog even on error
            try:
                self._show_license_activation_dialog()
            except Exception as dialog_error:
                print(f"Error showing license activation dialog: {str(dialog_error)}")
    
    def _initialize_feature_access(self) -> None:
        """Initialize feature access based on license"""
        try:
            # Check if license_status is None or empty
            if not self.license_status:
                print("No license status available, using trial features")
                license_type = 'trial'
            else:
                # Get license type
                license_info = self.license_status.get('license_info', {})
                if not license_info:
                    license_info = {}
                license_type = license_info.get('license_type', 'trial')
            
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
            
            # Set feature access
            features = feature_access_map.get(license_type, [])
            for feature in features:
                self.feature_access[feature] = True
            
            print(f"Feature access initialized for {license_type} license")
        except Exception as e:
            print(f"Error initializing feature access: {str(e)}")
            # Set minimal trial features as fallback
            self.feature_access = {
                'basic_orders': True,
                'basic_inventory': True,
                'basic_reports': True,
                'customer_support': True,
                'data_export': True
            }
    
    def _show_license_activation_dialog(self) -> None:
        """Show license activation dialog"""
        try:
            # Check if trial is available
            if self._check_trial_available():
                # Show trial management dialog
                trial_dialog = TrialManagementDialog(self.app, self.app, self.license_manager)
                result = trial_dialog.show_dialog()
                
                if result.get('action') == 'continue_trial':
                    # Continue with trial
                    self.trial_mode = True
                    self.is_licensed = True
                    self._initialize_feature_access()
                elif result.get('action') == 'activated':
                    # License activated
                    self.is_licensed = True
                    self.trial_mode = False
                    self._initialize_feature_access()
                else:
                    # Exit application
                    self.app.root.quit()
            else:
                # Show license activation dialog
                activation_dialog = LicenseActivationDialog(self.app, self.app, self.license_manager)
                result = activation_dialog.show_dialog()
                
                if result.get('success'):
                    # License activated
                    self.is_licensed = True
                    self.trial_mode = False
                    self._initialize_feature_access()
                else:
                    # Exit application
                    self.app.root.quit()
        except Exception as e:
            print(f"Error showing license activation dialog: {str(e)}")
            messagebox.showerror("License Error", f"Failed to show license activation: {str(e)}")
            self.app.root.quit()
    
    def _check_trial_available(self) -> bool:
        """Check if trial is available"""
        try:
            # Check if trial has been used before
            trial_status = self.license_manager.get_trial_status()
            
            # Check if trial is active or can be started
            trial_info = trial_status.get('trial_info', {})
            trial_status_value = trial_info.get('status', 'unknown')
            
            return trial_status_value in ['available', 'active']
        except Exception as e:
            print(f"Error checking trial availability: {str(e)}")
            return False
    
    def check_feature_access(self, feature: str) -> bool:
        """
        Check if a feature is accessible
        
        Args:
            feature: Feature name to check
            
        Returns:
            True if feature is accessible, False otherwise
        """
        try:
            # Check if licensed
            if not self.is_licensed:
                return False
            
            # Check feature access
            if feature in self.feature_access:
                return self.feature_access[feature]
            
            # Check with license manager
            result = self.license_manager.check_feature_access(feature)
            return result.get('allowed', False)
        except Exception as e:
            print(f"Error checking feature access: {str(e)}")
            return False
    
    def validate_license_periodically(self) -> None:
        """Validate license periodically"""
        try:
            if not self.is_licensed:
                return
            
            # Validate license
            result = self.license_manager.validate_license(online=True)
            
            if result.get('status') != 'valid':
                # License validation failed
                self.is_licensed = False
                self.trial_mode = False
                
                # Dispatch license validation failed event
                license_key = result.get('license_key', '')
                error_message = result.get('error_message', 'License validation failed')
                event_dispatcher.license_validation_failed(license_key, error_message)
                
                # Show license activation dialog
                self._show_license_activation_dialog()
            else:
                # Update license status
                self.license_status = self.license_manager.get_license_status()
        except Exception as e:
            print(f"Error validating license periodically: {str(e)}")
    
    def show_license_status(self) -> None:
        """Show license status screen"""
        try:
            if not self.license_manager:
                messagebox.showerror("Error", "License system not initialized")
                return
            
            # Create license status screen
            license_status_screen = LicenseStatusScreen(self.app, self.app, self.license_manager)
            
            # Clear content frame
            self.app.clear_content_frame()
            
            # Show license status screen
            license_status_screen.show()
        except Exception as e:
            print(f"Error showing license status: {str(e)}")
            messagebox.showerror("Error", f"Failed to show license status: {str(e)}")
    
    def show_license_upgrade(self) -> None:
        """Show license upgrade dialog"""
        try:
            if not self.license_manager:
                messagebox.showerror("Error", "License system not initialized")
                return
            
            # Create license upgrade dialog
            upgrade_dialog = LicenseUpgradeDialog(self.app, self.app, self.license_manager)
            upgrade_dialog.show_dialog()
            
            # Refresh license status
            self._check_license_on_startup()
        except Exception as e:
            print(f"Error showing license upgrade: {str(e)}")
            messagebox.showerror("Error", f"Failed to show license upgrade: {str(e)}")
    
    def show_license_transfer(self) -> None:
        """Show license transfer dialog"""
        try:
            if not self.license_manager:
                messagebox.showerror("Error", "License system not initialized")
                return
            
            # Create license transfer dialog
            transfer_dialog = LicenseTransferDialog(self.app, self.app, self.license_manager)
            transfer_dialog.show_dialog()
            
            # Refresh license status
            self._check_license_on_startup()
        except Exception as e:
            print(f"Error showing license transfer: {str(e)}")
            messagebox.showerror("Error", f"Failed to show license transfer: {str(e)}")
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get current license information"""
        try:
            if not self.license_status:
                return {}
            
            return self.license_status.get('license_info', {})
        except Exception as e:
            print(f"Error getting license info: {str(e)}")
            return {}
    
    def get_trial_info(self) -> Dict[str, Any]:
        """Get current trial information"""
        try:
            if not self.trial_mode:
                return {}
            
            trial_status = self.license_manager.get_trial_status()
            return trial_status.get('trial_info', {})
        except Exception as e:
            print(f"Error getting trial info: {str(e)}")
            return {}
    
    def is_trial_expired(self) -> bool:
        """Check if trial has expired"""
        try:
            if not self.trial_mode:
                return False
            
            trial_info = self.get_trial_info()
            days_remaining = trial_info.get('days_remaining', 0)
            
            return days_remaining <= 0
        except Exception as e:
            print(f"Error checking trial expiration: {str(e)}")
            return True
    
    def get_license_status_text(self) -> str:
        """Get license status text for display"""
        try:
            if not self.is_licensed:
                return "No License"
            
            license_info = self.get_license_info()
            license_type = license_info.get('license_type', 'Unknown')
            status = license_info.get('status', 'Unknown')
            
            if self.trial_mode:
                trial_info = self.get_trial_info()
                days_remaining = trial_info.get('days_remaining', 0)
                return f"Trial ({days_remaining} days left)"
            
            return f"{license_type.title()} ({status.title()})"
        except Exception as e:
            print(f"Error getting license status text: {str(e)}")
            return "Unknown"
    
    def get_license_status(self) -> Dict[str, Any]:
        """
        Get current license status
        
        Returns:
            Dictionary containing license status information
        """
        try:
            if not self.license_status:
                # If no license status, try to get it
                self._check_license_on_startup()
            
            return self.license_status or {}
        except Exception as e:
            print(f"Error getting license status: {str(e)}")
            return {}
    
    def add_license_menu_items(self, sidebar) -> None:
        """Add license menu items to sidebar"""
        try:
            # Add license menu items
            license_items = [
                ("License Status", self.show_license_status),
                ("Upgrade License", self.show_license_upgrade),
                ("Transfer License", self.show_license_transfer)
            ]
            
            for text, command in license_items:
                button = tk.Button(sidebar, text=text, command=command, 
                                 bg='#f0f0f0', fg='black', relief=tk.RAISED, bd=1)
                button.pack(fill=tk.X, pady=2)
        except Exception as e:
            print(f"Error adding license menu items: {str(e)}")
    
    def add_license_status_to_top_bar(self, top_bar) -> None:
        """Add license status to top bar"""
        try:
            # Create license status frame
            license_frame = tk.Frame(top_bar)
            license_frame.pack(side=tk.RIGHT, padx=10)
            
            # License status label
            status_text = self.get_license_status_text()
            self.license_status_label = tk.Label(license_frame, text=status_text, 
                                               bg='lightblue', fg='black', 
                                               relief=tk.RAISED, bd=1, padx=5)
            self.license_status_label.pack(side=tk.LEFT, padx=5)
            
            # Refresh button
            refresh_button = tk.Button(license_frame, text="↻", command=self._refresh_license_status,
                                     bg='lightgray', fg='black', relief=tk.RAISED, bd=1)
            refresh_button.pack(side=tk.LEFT, padx=2)
        except Exception as e:
            print(f"Error adding license status to top bar: {str(e)}")
    
    def _refresh_license_status(self) -> None:
        """Refresh license status display"""
        try:
            # Check license status
            self._check_license_on_startup()
            
            # Update status label
            if hasattr(self, 'license_status_label'):
                status_text = self.get_license_status_text()
                self.license_status_label.config(text=status_text)
        except Exception as e:
            print(f"Error refreshing license status: {str(e)}")
    
    def restrict_ui_features(self) -> None:
        """Restrict UI features based on license"""
        try:
            # Check if licensed
            if not self.is_licensed:
                return
            
            # Get current license type
            license_info = self.get_license_info()
            current_license = license_info.get('license_type', 'trial')
            
            # Restrict features based on license
            if not self.check_feature_access('advanced_reports'):
                # Disable advanced reports
                if hasattr(self.app, 'gst_reports_button'):
                    self.app.gst_reports_button.config(state=tk.DISABLED)
                
                # Dispatch feature access denied event
                event_dispatcher.feature_access_denied('advanced_reports', current_license, 'professional')
            
            if not self.check_feature_access('multi_user'):
                # Disable multi-user features
                if hasattr(self.app, 'user_management_button'):
                    self.app.user_management_button.config(state=tk.DISABLED)
                
                # Dispatch feature access denied event
                event_dispatcher.feature_access_denied('multi_user', current_license, 'professional')
            
            if not self.check_feature_access('api_access'):
                # Disable API access
                if hasattr(self.app, 'api_settings_button'):
                    self.app.api_settings_button.config(state=tk.DISABLED)
                
                # Dispatch feature access denied event
                event_dispatcher.feature_access_denied('api_access', current_license, 'professional')
            
            if not self.check_feature_access('custom_themes'):
                # Disable custom themes
                if hasattr(self.app, 'theme_settings_button'):
                    self.app.theme_settings_button.config(state=tk.DISABLED)
                
                # Dispatch feature access denied event
                event_dispatcher.feature_access_denied('custom_themes', current_license, 'professional')
        except Exception as e:
            print(f"Error restricting UI features: {str(e)}")
    
    def cleanup(self) -> None:
        """Clean up license integration resources"""
        try:
            if self.license_manager:
                self.license_manager.cleanup()
        except Exception as e:
            print(f"Error cleaning up license integration: {str(e)}")