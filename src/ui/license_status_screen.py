"""
License Status Screen for POS MVP application
Handles license status display and management
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable

from src.ui.base_ui import BaseUI
from src.utils.constants import *
from src.utils.license_manager import LicenseManager
from src.models.license import License


class LicenseStatusScreen(BaseUI):
    """
    License Status Screen for license status and management
    Provides comprehensive UI for license information and operations
    """
    
    def __init__(self, parent, app, license_manager: LicenseManager):
        """
        Initialize license status screen
        
        Args:
            parent: Parent window
            app: Application instance
            license_manager: License manager instance
        """
        super().__init__(parent.root if hasattr(parent, 'root') else parent, app)
        self.parent = parent
        self.license_manager = license_manager
        
        # UI components
        self.main_frame = None
        self.info_frame = None
        self.status_frame = None
        self.features_frame = None
        self.actions_frame = None
        self.validation_frame = None
        
        # License data
        self.license_info = {}
        self.activation_info = {}
        self.validation_status = {}
        
        # Create UI
        self._create_ui()
        
        # Load license status
        self._refresh_license_status()
    
    def _create_ui(self) -> None:
        """Create the license status UI"""
        try:
            # Main container
            self.main_frame = self.create_modern_frame(self.root, padding=SPACING_M)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
            
            # Title
            title_label = self.create_modern_label(
                self.main_frame, 
                "License Status", 
                style="Title.TLabel"
            )
            title_label.pack(pady=(0, SPACING_L))
            
            # Create notebook for tabs
            notebook = ttk.Notebook(self.main_frame)
            notebook.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
            
            # Create tabs
            self._create_info_tab(notebook)
            self._create_status_tab(notebook)
            self._create_features_tab(notebook)
            self._create_actions_tab(notebook)
            self._create_validation_tab(notebook)
            
            # Configure styles
            self.configure_styles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create UI: {str(e)}")
    
    def _create_info_tab(self, parent) -> None:
        """Create license information tab"""
        try:
            # Tab frame
            self.info_frame = self.create_modern_frame(parent, padding=SPACING_L)
            parent.add(self.info_frame, text="License Information")
            
            # License info section
            self._create_license_info_section(self.info_frame)
            
            # Activation info section
            self._create_activation_info_section(self.info_frame)
        except Exception as e:
            print(f"Error creating info tab: {str(e)}")
    
    def _create_license_info_section(self, parent) -> None:
        """Create license information section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "License Details", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # License info fields
            info_fields = [
                ("License Key:", "license_key"),
                ("License Type:", "license_type"),
                ("Customer Name:", "customer_name"),
                ("Customer Email:", "customer_email"),
                ("Issued Date:", "issued_date"),
                ("Expiry Date:", "expiry_date"),
                ("Status:", "status")
            ]
            
            # Create info labels
            self.info_labels = {}
            for label_text, field_key in info_fields:
                field_frame = ttk.Frame(section_frame)
                field_frame.pack(fill=tk.X, pady=SPACING_S)
                
                # Label
                label = self.create_modern_label(
                    field_frame, 
                    label_text, 
                    style="Body.TLabel",
                    width=15
                )
                label.pack(side=tk.LEFT, padx=(0, SPACING_S))
                
                # Value label
                value_label = self.create_modern_label(
                    field_frame, 
                    "Loading...", 
                    style="Body.TLabel"
                )
                value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.info_labels[field_key] = value_label
        except Exception as e:
            print(f"Error creating license info section: {str(e)}")
    
    def _create_activation_info_section(self, parent) -> None:
        """Create activation information section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Activation Details", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Activation info fields
            info_fields = [
                ("Activation ID:", "activation_id"),
                ("Activation Type:", "activation_type"),
                ("Activation Date:", "activation_date"),
                ("Last Validated:", "last_validated"),
                ("Validation Count:", "validation_count"),
                ("Hardware Binding:", "hardware_fingerprint")
            ]
            
            # Create info labels
            self.activation_labels = {}
            for label_text, field_key in info_fields:
                field_frame = ttk.Frame(section_frame)
                field_frame.pack(fill=tk.X, pady=SPACING_S)
                
                # Label
                label = self.create_modern_label(
                    field_frame, 
                    label_text, 
                    style="Body.TLabel",
                    width=15
                )
                label.pack(side=tk.LEFT, padx=(0, SPACING_S))
                
                # Value label
                value_label = self.create_modern_label(
                    field_frame, 
                    "Loading...", 
                    style="Body.TLabel"
                )
                value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.activation_labels[field_key] = value_label
        except Exception as e:
            print(f"Error creating activation info section: {str(e)}")
    
    def _create_status_tab(self, parent) -> None:
        """Create license status tab"""
        try:
            # Tab frame
            self.status_frame = self.create_modern_frame(parent, padding=SPACING_L)
            parent.add(self.status_frame, text="License Status")
            
            # Status display
            self._create_status_display(self.status_frame)
            
            # Validation status
            self._create_validation_status(self.status_frame)
        except Exception as e:
            print(f"Error creating status tab: {str(e)}")
    
    def _create_status_display(self, parent) -> None:
        """Create status display section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_L)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Current Status", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Status indicator frame
            status_frame = ttk.Frame(section_frame)
            status_frame.pack(fill=tk.X, pady=SPACING_L)
            
            # Status icon
            self.status_icon = tk.Canvas(status_frame, width=50, height=50, bg=COLOR_CARD_WHITE)
            self.status_icon.pack(side=tk.LEFT, padx=(0, SPACING_M))
            
            # Status text
            self.status_text = self.create_modern_label(
                status_frame, 
                "Checking...", 
                style="Body.TLabel"
            )
            self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Draw initial status icon
            self._draw_status_icon("checking")
        except Exception as e:
            print(f"Error creating status display: {str(e)}")
    
    def _create_validation_status(self, parent) -> None:
        """Create validation status section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Validation Information", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Validation info
            self.validation_info_label = self.create_modern_label(
                section_frame, 
                "Loading validation information...", 
                style="Body.TLabel"
            )
            self.validation_info_label.pack(fill=tk.X, pady=SPACING_S)
        except Exception as e:
            print(f"Error creating validation status: {str(e)}")
    
    def _create_features_tab(self, parent) -> None:
        """Create license features tab"""
        try:
            # Tab frame
            self.features_frame = self.create_modern_frame(parent, padding=SPACING_L)
            parent.add(self.features_frame, text="License Features")
            
            # Features list
            self._create_features_list(self.features_frame)
        except Exception as e:
            print(f"Error creating features tab: {str(e)}")
    
    def _create_features_list(self, parent) -> None:
        """Create features list section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Available Features", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Features treeview
            columns = ("feature", "status")
            headings = ("Feature", "Status")
            
            self.features_tree = self.create_modern_treeview(
                section_frame, 
                columns, 
                headings,
                column_widths=[300, 100]
            )
            
            # Configure treeview
            self.features_tree.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(section_frame, orient=tk.VERTICAL, command=self.features_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.features_tree.configure(yscrollcommand=scrollbar.set)
        except Exception as e:
            print(f"Error creating features list: {str(e)}")
    
    def _create_actions_tab(self, parent) -> None:
        """Create license actions tab"""
        try:
            # Tab frame
            self.actions_frame = self.create_modern_frame(parent, padding=SPACING_L)
            parent.add(self.actions_frame, text="License Actions")
            
            # Action buttons
            self._create_action_buttons(self.actions_frame)
        except Exception as e:
            print(f"Error creating actions tab: {str(e)}")
    
    def _create_action_buttons(self, parent) -> None:
        """Create action buttons section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_L)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "License Actions", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Action buttons
            buttons = [
                ("Refresh Status", self._on_refresh_status, "Primary.TButton"),
                ("Validate License", self._on_validate_license, "Success.TButton"),
                ("Deactivate License", self._on_deactivate_license, "Danger.TButton"),
                ("Transfer License", self._on_transfer_license, "Secondary.TButton"),
                ("Upgrade License", self._on_upgrade_license, "Secondary.TButton")
            ]
            
            self.create_button_group(section_frame, buttons, spacing=SPACING_M)
        except Exception as e:
            print(f"Error creating action buttons: {str(e)}")
    
    def _create_validation_tab(self, parent) -> None:
        """Create validation tab"""
        try:
            # Tab frame
            self.validation_frame = self.create_modern_frame(parent, padding=SPACING_L)
            parent.add(self.validation_frame, text="Validation History")
            
            # Validation history
            self._create_validation_history(self.validation_frame)
        except Exception as e:
            print(f"Error creating validation tab: {str(e)}")
    
    def _create_validation_history(self, parent) -> None:
        """Create validation history section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Recent Validation Events", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Validation history treeview
            columns = ("timestamp", "event_type", "status", "message")
            headings = ("Time", "Event Type", "Status", "Message")
            
            self.validation_tree = self.create_modern_treeview(
                section_frame, 
                columns, 
                headings,
                column_widths=[150, 150, 100, 300]
            )
            
            # Configure treeview
            self.validation_tree.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(section_frame, orient=tk.VERTICAL, command=self.validation_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.validation_tree.configure(yscrollcommand=scrollbar.set)
            
            # Load validation history
            self._load_validation_history()
        except Exception as e:
            print(f"Error creating validation history: {str(e)}")
    
    def _draw_status_icon(self, status: str) -> None:
        """Draw status icon"""
        try:
            # Clear canvas
            self.status_icon.delete("all")
            
            # Draw icon based on status
            if status == "valid":
                # Green checkmark
                self.status_icon.create_oval(10, 10, 40, 40, fill=COLOR_SUCCESS, outline=COLOR_SUCCESS)
                self.status_icon.create_line(15, 20, 25, 30, fill=COLOR_CARD_WHITE, width=3)
                self.status_icon.create_line(25, 30, 35, 20, fill=COLOR_CARD_WHITE, width=3)
                self.status_icon.create_line(20, 25, 30, 25, fill=COLOR_CARD_WHITE, width=3)
            elif status == "expired":
                # Orange warning
                self.status_icon.create_oval(10, 10, 40, 40, fill=COLOR_WARNING, outline=COLOR_WARNING)
                self.status_icon.create_text(25, 25, text="!", font=("Arial", 20, "bold"), fill=COLOR_CARD_WHITE)
            elif status == "invalid" or status == "revoked":
                # Red X
                self.status_icon.create_oval(10, 10, 40, 40, fill=COLOR_ERROR, outline=COLOR_ERROR)
                self.status_icon.create_line(15, 20, 35, 30, fill=COLOR_CARD_WHITE, width=3)
                self.status_icon.create_line(35, 20, 15, 30, fill=COLOR_CARD_WHITE, width=3)
            elif status == "checking":
                # Blue loading
                self.status_icon.create_oval(10, 10, 40, 40, fill=COLOR_INFO, outline=COLOR_INFO)
                self.status_icon.create_arc(15, 15, 20, 20, 0, 270, fill=COLOR_CARD_WHITE, width=3)
            else:
                # Gray question mark
                self.status_icon.create_oval(10, 10, 40, 40, fill=COLOR_TEXT_SECONDARY, outline=COLOR_TEXT_SECONDARY)
                self.status_icon.create_text(25, 25, text="?", font=("Arial", 20, "bold"), fill=COLOR_CARD_WHITE)
        except Exception as e:
            print(f"Error drawing status icon: {str(e)}")
    
    def _refresh_license_status(self) -> None:
        """Refresh license status"""
        try:
            # Get license status
            status = self.license_manager.get_license_status()
            
            # Update license info
            self.license_info = status.get('license_info', {})
            self.activation_info = status.get('activation_info', {})
            self.validation_status = status
            
            # Update UI
            self._update_license_info()
            self._update_activation_info()
            self._update_status_display()
            self._update_features_list()
            self._update_validation_info()
        except Exception as e:
            print(f"Error refreshing license status: {str(e)}")
    
    def _update_license_info(self) -> None:
        """Update license information display"""
        try:
            if not self.info_labels:
                return
            
            # Update license info fields
            field_mappings = {
                'license_key': self.license_info.get('license_key', 'Not Available'),
                'license_type': self.license_info.get('license_type', 'Not Available'),
                'customer_name': self.license_info.get('customer_name', 'Not Available'),
                'customer_email': self.license_info.get('customer_email', 'Not Available'),
                'issued_date': self._format_date(self.license_info.get('issued_date')),
                'expiry_date': self._format_date(self.license_info.get('expiry_date')),
                'status': self.license_info.get('status', 'Unknown')
            }
            
            for field_key, value in field_mappings.items():
                if field_key in self.info_labels:
                    self.info_labels[field_key].configure(text=value)
        except Exception as e:
            print(f"Error updating license info: {str(e)}")
    
    def _update_activation_info(self) -> None:
        """Update activation information display"""
        try:
            if not self.activation_labels:
                return
            
            # Update activation info fields
            field_mappings = {
                'activation_id': self.activation_info.get('activation_id', 'Not Available'),
                'activation_type': self.activation_info.get('activation_type', 'Not Available'),
                'activation_date': self._format_date(self.activation_info.get('activation_date')),
                'last_validated': self._format_date(self.activation_info.get('last_validated')),
                'validation_count': str(self.activation_info.get('validation_count', 0)),
                'hardware_fingerprint': self._truncate_fingerprint(self.activation_info.get('hardware_fingerprint', 'Not Available'))
            }
            
            for field_key, value in field_mappings.items():
                if field_key in self.activation_labels:
                    self.activation_labels[field_key].configure(text=value)
        except Exception as e:
            print(f"Error updating activation info: {str(e)}")
    
    def _update_status_display(self) -> None:
        """Update status display"""
        try:
            if not self.status_text or not self.status_icon:
                return
            
            # Get status
            status = self.validation_status.get('status', 'unknown')
            
            # Update status text
            status_messages = {
                'valid': 'License is valid and active',
                'expired': 'License has expired',
                'invalid': 'License is invalid',
                'revoked': 'License has been revoked',
                'blacklisted': 'License is blacklisted',
                'tampered': 'License tampering detected',
                'not_activated': 'No license activated',
                'unknown': 'License status unknown'
            }
            
            message = status_messages.get(status, 'Unknown license status')
            self.status_text.configure(text=message)
            
            # Update status icon
            self._draw_status_icon(status)
        except Exception as e:
            print(f"Error updating status display: {str(e)}")
    
    def _update_features_list(self) -> None:
        """Update features list"""
        try:
            if not hasattr(self, 'features_tree'):
                return
            
            # Clear existing items
            for item in self.features_tree.get_children():
                self.features_tree.delete(item)
            
            # Get features
            features = self.license_info.get('features', [])
            
            # Add features to tree
            for feature in features:
                # Check if feature is available
                feature_check = self.license_manager.check_feature_access(feature)
                status = "Available" if feature_check.get('allowed') else "Not Available"
                
                self.features_tree.insert("", tk.END, values=(feature, status))
        except Exception as e:
            print(f"Error updating features list: {str(e)}")
    
    def _update_validation_info(self) -> None:
        """Update validation information"""
        try:
            if not self.validation_info_label:
                return
            
            # Create validation info text
            info_text = f"""
            Validation Level: {self.validation_status.get('validation_level', 'Unknown')}
            Last Validation: {self._format_date(self.validation_status.get('last_validation'))}
            Server URL: {self.license_manager.server_url if hasattr(self.license_manager, 'server_url') else 'Not Configured'}
            """
            
            self.validation_info_label.configure(text=info_text.strip())
        except Exception as e:
            print(f"Error updating validation info: {str(e)}")
    
    def _load_validation_history(self) -> None:
        """Load validation history"""
        try:
            if not hasattr(self, 'validation_tree'):
                return
            
            # Clear existing items
            for item in self.validation_tree.get_children():
                self.validation_tree.delete(item)
            
            # Get validation logs
            logs = self.license_manager.get_audit_logs(days=30)
            
            # Add logs to tree
            for log in logs[:50]:  # Limit to 50 most recent
                timestamp = self._format_date(log.get('timestamp'))
                event_type = log.get('event_type', 'Unknown')
                status = log.get('event_severity', 'Unknown')
                message = log.get('event_description', 'No message')
                
                self.validation_tree.insert("", tk.END, values=(timestamp, event_type, status, message))
        except Exception as e:
            print(f"Error loading validation history: {str(e)}")
    
    def _format_date(self, date_string: str) -> str:
        """Format date string for display"""
        try:
            if not date_string:
                return "Not Available"
            
            # Parse date
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            
            # Format for display
            return date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(f"Error formatting date: {str(e)}")
            return date_string
    
    def _truncate_fingerprint(self, fingerprint: str) -> str:
        """Truncate fingerprint for display"""
        try:
            if not fingerprint or fingerprint == "Not Available":
                return fingerprint
            
            # Show first 8 and last 4 characters
            if len(fingerprint) > 12:
                return f"{fingerprint[:8]}...{fingerprint[-4:]}"
            
            return fingerprint
        except Exception as e:
            print(f"Error truncating fingerprint: {str(e)}")
            return fingerprint
    
    def _on_refresh_status(self) -> None:
        """Handle refresh status button click"""
        try:
            self._refresh_license_status()
            messagebox.showinfo("Refresh", "License status refreshed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh status: {str(e)}")
    
    def _on_validate_license(self) -> None:
        """Handle validate license button click"""
        try:
            # Perform validation
            result = self.license_manager.validate_license(online=True)
            
            if result['status'] == 'valid':
                messagebox.showinfo("Validation", "License validation successful")
            else:
                messagebox.showerror("Validation Failed", f"License validation failed: {result.get('message')}")
            
            # Refresh status
            self._refresh_license_status()
        except Exception as e:
            messagebox.showerror("Error", f"Validation error: {str(e)}")
    
    def _on_deactivate_license(self) -> None:
        """Handle deactivate license button click"""
        try:
            # Confirm deactivation
            if not messagebox.askyesno("Deactivate License", 
                                   "Are you sure you want to deactivate the license?\n\nThis will make the application unusable until a new license is activated."):
                return
            
            # Deactivate license
            result = self.license_manager.deactivate_license()
            
            if result['success']:
                messagebox.showinfo("Deactivation", "License deactivated successfully")
                # Refresh status
                self._refresh_license_status()
            else:
                messagebox.showerror("Deactivation Failed", f"License deactivation failed: {result.get('message')}")
        except Exception as e:
            messagebox.showerror("Error", f"Deactivation error: {str(e)}")
    
    def _on_transfer_license(self) -> None:
        """Handle transfer license button click"""
        try:
            # Show transfer dialog
            from src.ui.license_transfer_dialog import LicenseTransferDialog
            transfer_dialog = LicenseTransferDialog(self, self.app, self.license_manager)
            transfer_dialog.show_dialog()
            
            # Refresh status after transfer
            self._refresh_license_status()
        except Exception as e:
            messagebox.showerror("Error", f"Transfer error: {str(e)}")
    
    def _on_upgrade_license(self) -> None:
        """Handle upgrade license button click"""
        try:
            # Show upgrade dialog
            from src.ui.license_upgrade_dialog import LicenseUpgradeDialog
            upgrade_dialog = LicenseUpgradeDialog(self, self.app, self.license_manager)
            upgrade_dialog.show_dialog()
            
            # Refresh status after upgrade
            self._refresh_license_status()
        except Exception as e:
            messagebox.showerror("Error", f"Upgrade error: {str(e)}")
    
    def refresh_status(self) -> None:
        """Public method to refresh status"""
        self._refresh_license_status()
    
    def get_license_info(self) -> Dict[str, Any]:
        """Get current license information"""
        return self.license_info
    
    def get_activation_info(self) -> Dict[str, Any]:
        """Get current activation information"""
        return self.activation_info
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status"""
        return self.validation_status