"""
License Transfer Dialog for POS MVP application
Handles license transfer between devices
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable, List

from src.ui.base_ui import BaseUI
from src.utils.constants import *
from src.utils.license_manager import LicenseManager
from src.models.license import License


class LicenseTransferDialog(BaseUI):
    """
    License Transfer Dialog for license transfer between devices
    Provides comprehensive UI for license deactivation and reactivation
    """
    
    def __init__(self, parent, app, license_manager: LicenseManager):
        """
        Initialize license transfer dialog
        
        Args:
            parent: Parent window
            app: Application instance
            license_manager: License manager instance
        """
        super().__init__(parent.root if hasattr(parent, 'root') else parent, app)
        self.parent = parent
        self.license_manager = license_manager
        
        # Dialog properties
        self.dialog = None
        self.result = None
        
        # UI components
        self.main_frame = None
        self.current_frame = None
        self.transfer_frame = None
        self.confirmation_frame = None
        
        # License data
        self.current_license = {}
        self.hardware_info = {}
        self.transfer_code = None
    
    def show_dialog(self) -> Dict[str, Any]:
        """
        Show the license transfer dialog
        
        Returns:
            Dialog result
        """
        try:
            # Create dialog
            self._create_dialog()
            
            # Load license information
            self._load_license_info()
            
            # Load hardware information
            self._load_hardware_info()
            
            # Update UI
            self._update_ui()
            
            # Show dialog
            self.dialog.wait_window()
            
            return self.result
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show dialog: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_dialog(self) -> None:
        """Create the license transfer dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.root)
            self.dialog.title("License Transfer")
            self.dialog.geometry("600x500")
            self.dialog.resizable(False, False)
            self.dialog.transient(self.root)
            self.dialog.grab_set()
            
            # Center dialog
            self._center_dialog()
            
            # Create main frame
            self.main_frame = self.create_modern_frame(self.dialog, padding=SPACING_M)
            self.main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_L, pady=SPACING_L)
            
            # Create UI sections
            self._create_header()
            self._create_current_license()
            self._create_transfer_options()
            self._create_confirmation()
            self._create_actions()
            
            # Configure styles
            self.configure_styles()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create dialog: {str(e)}")
    
    def _center_dialog(self) -> None:
        """Center the dialog on screen"""
        try:
            self.dialog.update_idletasks()
            width = self.dialog.winfo_width()
            height = self.dialog.winfo_height()
            x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
            self.dialog.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            print(f"Error centering dialog: {str(e)}")
    
    def _create_header(self) -> None:
        """Create dialog header"""
        try:
            # Header frame
            header_frame = self.create_modern_frame(self.main_frame, padding=SPACING_M)
            header_frame.pack(fill=tk.X, pady=(0, SPACING_M))
            
            # Title
            title_label = self.create_modern_label(
                header_frame, 
                "License Transfer", 
                style="Title.TLabel"
            )
            title_label.pack(anchor=tk.W)
            
            # Description
            desc_label = self.create_modern_label(
                header_frame, 
                "Transfer your license to a new device by deactivating the current installation", 
                style="Body.TLabel"
            )
            desc_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        except Exception as e:
            print(f"Error creating header: {str(e)}")
    
    def _create_current_license(self) -> None:
        """Create current license section"""
        try:
            # Current license frame
            self.current_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.current_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.current_frame, 
                "Current License Information", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # License info fields
            info_fields = [
                ("License Key:", "license_key"),
                ("License Type:", "license_type"),
                ("Status:", "status"),
                ("Activated On:", "activation_date"),
                ("Device ID:", "device_id")
            ]
            
            # Create info labels
            self.current_labels = {}
            for label_text, field_key in info_fields:
                field_frame = ttk.Frame(self.current_frame)
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
                
                self.current_labels[field_key] = value_label
        except Exception as e:
            print(f"Error creating current license section: {str(e)}")
    
    def _create_transfer_options(self) -> None:
        """Create transfer options section"""
        try:
            # Transfer frame
            self.transfer_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.transfer_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.transfer_frame, 
                "Transfer Options", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Transfer type
            type_frame = ttk.Frame(self.transfer_frame)
            type_frame.pack(fill=tk.X, pady=SPACING_S)
            
            type_label = self.create_modern_label(
                type_frame, 
                "Transfer Type:", 
                style="Body.TLabel",
                width=15
            )
            type_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.transfer_type_var = tk.StringVar(value="deactivate")
            types = [
                ("Deactivate Current Device", "deactivate"),
                ("Generate Transfer Code", "generate_code")
            ]
            
            for text, value in types:
                radio = self.create_modern_radiobutton(
                    type_frame, 
                    self.transfer_type_var, 
                    text, 
                    value
                )
                radio.pack(anchor=tk.W, pady=SPACING_XS)
            
            # Reason for transfer
            reason_frame = ttk.Frame(self.transfer_frame)
            reason_frame.pack(fill=tk.X, pady=SPACING_S)
            
            reason_label = self.create_modern_label(
                reason_frame, 
                "Reason:", 
                style="Body.TLabel",
                width=15
            )
            reason_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.reason_var = tk.StringVar()
            self.reason_entry = self.create_modern_entry(
                reason_frame,
                textvariable=self.reason_var
            )
            self.reason_entry.insert(0, "Reason for license transfer")
            self.reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Generate transfer code button
            self.generate_button = self.create_modern_button(
                self.transfer_frame, 
                "Generate Transfer Code", 
                self._on_generate_code,
                style="Secondary.TButton"
            )
            self.generate_button.pack(pady=SPACING_M)
            
            # Transfer code display
            code_frame = ttk.Frame(self.transfer_frame)
            code_frame.pack(fill=tk.X, pady=SPACING_S)
            
            code_label = self.create_modern_label(
                code_frame, 
                "Transfer Code:", 
                style="Body.TLabel",
                width=15
            )
            code_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.transfer_code_var = tk.StringVar()
            self.transfer_code_entry = self.create_modern_entry(
                code_frame,
                textvariable=self.transfer_code_var,
                state=tk.DISABLED
            )
            self.transfer_code_entry.insert(0, "Transfer code will appear here")
            self.transfer_code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Copy code button
            self.copy_button = self.create_modern_button(
                code_frame, 
                "Copy", 
                self._on_copy_code,
                style="Secondary.TButton"
            )
            self.copy_button.pack(side=tk.LEFT, padx=SPACING_S)
        except Exception as e:
            print(f"Error creating transfer options: {str(e)}")
    
    def _create_confirmation(self) -> None:
        """Create confirmation section"""
        try:
            # Confirmation frame
            self.confirmation_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.confirmation_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.confirmation_frame, 
                "Transfer Confirmation", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Warning message
            warning_label = self.create_modern_label(
                self.confirmation_frame, 
                "⚠️ Warning: License transfer will deactivate the current installation. "
                "You will need to reactivate the license on the new device using the transfer code.",
                style="Body.TLabel"
            )
            warning_label.pack(anchor=tk.W, pady=SPACING_S)
            
            # Confirmation checkbox
            self.confirm_var = tk.BooleanVar()
            confirm_check = self.create_modern_checkbutton(
                self.confirmation_frame, 
                self.confirm_var, 
                "I understand that the current installation will be deactivated"
            )
            confirm_check.pack(anchor=tk.W, pady=SPACING_S)
        except Exception as e:
            print(f"Error creating confirmation section: {str(e)}")
    
    def _create_actions(self) -> None:
        """Create action buttons"""
        try:
            # Actions frame
            actions_frame = ttk.Frame(self.main_frame)
            actions_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Buttons
            buttons = [
                ("Deactivate License", self._on_deactivate, "Danger.TButton"),
                ("Help", self._on_help, "Secondary.TButton"),
                ("Close", self._on_close, "Default.TButton")
            ]
            
            self.create_button_group(actions_frame, buttons, spacing=SPACING_M)
        except Exception as e:
            print(f"Error creating actions: {str(e)}")
    
    def _load_license_info(self) -> None:
        """Load current license information"""
        try:
            # Get current license
            status = self.license_manager.get_license_status()
            
            # Update current license info
            self.current_license = status.get('license_info', {})
        except Exception as e:
            print(f"Error loading license info: {str(e)}")
    
    def _load_hardware_info(self) -> None:
        """Load hardware information"""
        try:
            # Get hardware fingerprint
            hardware_fingerprint = self.license_manager.hardware_fingerprint
            if hardware_fingerprint:
                self.hardware_info = {
                    'fingerprint': hardware_fingerprint.get_fingerprint(),
                    'device_id': hardware_fingerprint.get_device_id()
                }
        except Exception as e:
            print(f"Error loading hardware info: {str(e)}")
    
    def _update_ui(self) -> None:
        """Update UI with license and hardware information"""
        try:
            # Update current license
            self._update_current_license()
            
            # Update transfer options
            self._update_transfer_options()
        except Exception as e:
            print(f"Error updating UI: {str(e)}")
    
    def _update_current_license(self) -> None:
        """Update current license display"""
        try:
            if not self.current_labels:
                return
            
            # Get license info
            license_key = self.current_license.get('license_key', 'Not Available')
            license_type = self.current_license.get('license_type', 'Unknown')
            status = self.current_license.get('status', 'Unknown')
            activation_date = self.current_license.get('activation_date')
            device_id = self.hardware_info.get('device_id', 'Not Available')
            
            # Update info fields
            self.current_labels['license_key'].configure(text=self._truncate_license_key(license_key))
            self.current_labels['license_type'].configure(text=license_type.title())
            self.current_labels['status'].configure(text=status.title())
            self.current_labels['activation_date'].configure(text=self._format_date(activation_date))
            self.current_labels['device_id'].configure(text=self._truncate_device_id(device_id))
        except Exception as e:
            print(f"Error updating current license: {str(e)}")
    
    def _update_transfer_options(self) -> None:
        """Update transfer options based on license status"""
        try:
            # Check if license is active
            license_active = self.current_license.get('status') == 'active'
            
            # Enable/disable transfer options
            state = tk.NORMAL if license_active else tk.DISABLED
            
            # Update UI elements
            self.reason_entry.configure(state=state)
            self.generate_button.configure(state=state)
            
            # Update transfer type selection
            if license_active:
                self.transfer_type_var.set("deactivate")
            else:
                self.transfer_type_var.set("generate_code")
        except Exception as e:
            print(f"Error updating transfer options: {str(e)}")
    
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
    
    def _truncate_license_key(self, license_key: str) -> str:
        """Truncate license key for display"""
        try:
            if not license_key or license_key == "Not Available":
                return license_key
            
            # Show first 8 and last 4 characters
            if len(license_key) > 12:
                return f"{license_key[:8]}...{license_key[-4:]}"
            
            return license_key
        except Exception as e:
            print(f"Error truncating license key: {str(e)}")
            return license_key
    
    def _truncate_device_id(self, device_id: str) -> str:
        """Truncate device ID for display"""
        try:
            if not device_id or device_id == "Not Available":
                return device_id
            
            # Show first 8 and last 4 characters
            if len(device_id) > 12:
                return f"{device_id[:8]}...{device_id[-4:]}"
            
            return device_id
        except Exception as e:
            print(f"Error truncating device ID: {str(e)}")
            return device_id
    
    def _on_generate_code(self) -> None:
        """Handle generate transfer code button click"""
        try:
            # Get reason
            reason = self.reason_var.get().strip()
            
            if not reason:
                messagebox.showerror("Error", "Please enter a reason for the transfer")
                return
            
            # Show progress
            self._show_progress("Generating transfer code...")
            
            # Generate transfer code
            result = self.license_manager.generate_transfer_code(reason)
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                self.transfer_code = result.get('transfer_code')
                self.transfer_code_var.set(self.transfer_code)
                self.transfer_code_entry.configure(state=tk.NORMAL)
                messagebox.showinfo("Success", "Transfer code generated successfully")
            else:
                messagebox.showerror("Generation Failed", f"Transfer code generation failed: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Error generating transfer code: {str(e)}")
    
    def _on_copy_code(self) -> None:
        """Handle copy code button click"""
        try:
            if not self.transfer_code:
                messagebox.showerror("Error", "No transfer code to copy")
                return
            
            # Copy to clipboard
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(self.transfer_code)
            
            messagebox.showinfo("Success", "Transfer code copied to clipboard")
        except Exception as e:
            messagebox.showerror("Error", f"Error copying transfer code: {str(e)}")
    
    def _on_deactivate(self) -> None:
        """Handle deactivate license button click"""
        try:
            # Check confirmation
            if not self.confirm_var.get():
                messagebox.showerror("Error", "Please confirm that you understand the transfer process")
                return
            
            # Confirm deactivation
            if not messagebox.askyesno("Confirm Deactivation", 
                                   "Are you sure you want to deactivate the license on this device?\n\nThis will make the current installation unusable until the license is reactivated on a new device."):
                return
            
            # Show progress
            self._show_progress("Deactivating license...")
            
            # Deactivate license
            result = self.license_manager.deactivate_license_for_transfer(
                reason=self.reason_var.get().strip()
            )
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                messagebox.showinfo("Success", "License deactivated successfully. Use the transfer code to activate on the new device.")
                self.result = {'success': True, 'action': 'deactivated', 'transfer_code': self.transfer_code}
                self.dialog.destroy()
            else:
                messagebox.showerror("Deactivation Failed", f"License deactivation failed: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Error deactivating license: {str(e)}")
    
    def _on_help(self) -> None:
        """Handle help button click"""
        try:
            help_text = """
License Transfer Help:

1. Generate Transfer Code:
   - Enter a reason for the transfer
   - Click 'Generate Transfer Code'
   - Copy the generated transfer code

2. Deactivate Current Device:
   - Confirm that you understand the transfer process
   - Click 'Deactivate License'
   - The current installation will be deactivated

3. Activate on New Device:
   - Install the application on the new device
   - Use the transfer code during activation
   - The license will be activated on the new device

Important Notes:
- The transfer code is valid for 24 hours
- Only one device can be active at a time
- Keep the transfer code secure
- Contact support if you encounter issues
            """
            
            messagebox.showinfo("Transfer Help", help_text)
        except Exception as e:
            messagebox.showerror("Error", f"Error showing help: {str(e)}")
    
    def _on_close(self) -> None:
        """Handle close button click"""
        try:
            self.result = {'success': True, 'action': 'close'}
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error closing dialog: {str(e)}")
    
    def _show_progress(self, message: str) -> None:
        """Show progress indicator"""
        try:
            # Create progress window
            self.progress_window = tk.Toplevel(self.dialog)
            self.progress_window.title("Processing")
            self.progress_window.geometry("300x100")
            self.progress_window.resizable(False, False)
            self.progress_window.transient(self.dialog)
            self.progress_window.grab_set()
            
            # Center progress window
            self.progress_window.update_idletasks()
            width = self.progress_window.winfo_width()
            height = self.progress_window.winfo_height()
            x = (self.progress_window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.progress_window.winfo_screenheight() // 2) - (height // 2)
            self.progress_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Create progress frame
            progress_frame = self.create_modern_frame(self.progress_window, padding=SPACING_M)
            progress_frame.pack(fill=tk.BOTH, expand=True)
            
            # Progress label
            progress_label = self.create_modern_label(
                progress_frame, 
                message, 
                style="Body.TLabel"
            )
            progress_label.pack(pady=SPACING_M)
            
            # Progress bar
            progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=SPACING_M)
            progress_bar.start(10)
        except Exception as e:
            print(f"Error showing progress: {str(e)}")
    
    def _hide_progress(self) -> None:
        """Hide progress indicator"""
        try:
            if hasattr(self, 'progress_window') and self.progress_window:
                self.progress_window.destroy()
                self.progress_window = None
        except Exception as e:
            print(f"Error hiding progress: {str(e)}")