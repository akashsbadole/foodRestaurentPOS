"""
License Activation Dialog for POS MVP application
Handles license activation with comprehensive UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from typing import Dict, Optional, Any, Callable

from src.ui.base_ui import BaseUI
from src.utils.constants import *
from src.utils.license_manager import LicenseManager
from src.utils.hardware_fingerprint import HardwareFingerprint


class LicenseActivationDialog(BaseUI):
    """
    License Activation Dialog for license activation
    Provides comprehensive UI for license activation with anti-cracking measures
    """
    
    def __init__(self, parent, app, license_manager: LicenseManager = None, on_success: Callable = None):
        """
        Initialize license activation dialog
        
        Args:
            parent: Parent window
            app: Application instance
            license_manager: License manager instance (optional, will be initialized if not provided)
            on_success: Callback function for successful activation
        """
        super().__init__(parent.root if hasattr(parent, 'root') else parent, app)
        self.parent = parent
        self.on_success = on_success
        
        # Initialize license manager if not provided
        if license_manager is None:
            from src.utils.license_manager import LicenseManager
            license_manager = LicenseManager()
        
        self.license_manager = license_manager
        self.hardware_fingerprint = HardwareFingerprint()
        
        # Dialog state
        self.dialog = None
        self.license_key_var = tk.StringVar()
        self.activation_code_var = tk.StringVar()
        self.online_var = tk.BooleanVar(value=True)
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar()
        
        # UI components
        self.license_key_entry = None
        self.activation_code_entry = None
        self.online_check = None
        self.activate_button = None
        self.cancel_button = None
        self.progress_bar = None
        self.status_label = None
        
        # Activation state
        self.is_activating = False
        self.activation_result = None
    
    def show_dialog(self) -> None:
        """Show license activation dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.parent.root if hasattr(self.parent, 'root') else self.parent)
            self.dialog.title("License Activation")
            self.dialog.geometry("600x500")
            self.dialog.resizable(False, False)
            self.dialog.transient(self.parent.root if hasattr(self.parent, 'root') else self.parent)
            self.dialog.grab_set()
            
            # Center dialog
            self._center_dialog()
            
            # Create UI
            self._create_ui()
            
            # Configure styles
            self.configure_styles()
            
            # Start dialog
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
            self.dialog.wait_window()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show activation dialog: {str(e)}")
    
    def _center_dialog(self) -> None:
        """Center dialog on parent window"""
        try:
            self.dialog.update_idletasks()
            
            # Get parent geometry
            if hasattr(self.parent, 'root'):
                parent_x = self.parent.root.winfo_x()
                parent_y = self.parent.root.winfo_y()
                parent_width = self.parent.root.winfo_width()
                parent_height = self.parent.root.winfo_height()
            else:
                parent_x = self.parent.winfo_x()
                parent_y = self.parent.winfo_y()
                parent_width = self.parent.winfo_width()
                parent_height = self.parent.winfo_height()
            
            # Get dialog geometry
            dialog_width = self.dialog.winfo_width()
            dialog_height = self.dialog.winfo_height()
            
            # Calculate center position
            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2
            
            # Set dialog position
            self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        except Exception as e:
            print(f"Error centering dialog: {str(e)}")
    
    def _create_ui(self) -> None:
        """Create dialog UI"""
        try:
            # Main container
            main_frame = self.create_modern_frame(self.dialog, padding=SPACING_L)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_XXL, pady=SPACING_XXL)
            
            # Title
            title_label = self.create_modern_label(
                main_frame, 
                "Activate Your License", 
                style="Title.TLabel"
            )
            title_label.pack(pady=(0, SPACING_L))
            
            # License Key section
            self._create_license_key_section(main_frame)
            
            # Activation Code section
            self._create_activation_code_section(main_frame)
            
            # Online Activation section
            self._create_online_section(main_frame)
            
            # Progress section
            self._create_progress_section(main_frame)
            
            # Status section
            self._create_status_section(main_frame)
            
            # Buttons
            self._create_button_section(main_frame)
            
            # Hardware info section
            self._create_hardware_info_section(main_frame)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create UI: {str(e)}")
    
    def _create_license_key_section(self, parent) -> None:
        """Create license key input section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "License Key", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # License key entry
            self.license_key_entry = self.create_modern_entry(
                section_frame, 
                font=(FONT_FAMILY_PRIMARY, 12)
            )
            self.license_key_entry.pack(fill=tk.X, pady=SPACING_S)
            self.license_key_entry.configure(textvariable=self.license_key_var)
            
            # Bind validation
            self.license_key_var.trace('w', self._validate_license_key)
            
            # Help text
            help_label = self.create_modern_label(
                section_frame, 
                "Enter your license key (format: XXXX-XXXX-XXXX-XXXX)", 
                style="Small.TLabel"
            )
            help_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        except Exception as e:
            print(f"Error creating license key section: {str(e)}")
    
    def _create_activation_code_section(self, parent) -> None:
        """Create activation code input section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "Activation Code (Optional)", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Activation code entry
            self.activation_code_entry = self.create_modern_entry(
                section_frame, 
                font=(FONT_FAMILY_PRIMARY, 12),
                show="*"
            )
            self.activation_code_entry.pack(fill=tk.X, pady=SPACING_S)
            self.activation_code_entry.configure(textvariable=self.activation_code_var)
            
            # Help text
            help_label = self.create_modern_label(
                section_frame, 
                "Enter activation code if provided with your license", 
                style="Small.TLabel"
            )
            help_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        except Exception as e:
            print(f"Error creating activation code section: {str(e)}")
    
    def _create_online_section(self, parent) -> None:
        """Create online activation section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Online activation checkbox
            self.online_check = ttk.Checkbutton(
                section_frame,
                text="Enable Online Activation (Recommended)",
                variable=self.online_var,
                style="Modern.TCheckbutton"
            )
            self.online_check.pack(anchor=tk.W, pady=SPACING_S)
            
            # Help text
            help_label = self.create_modern_label(
                section_frame, 
                "Online activation provides enhanced security and automatic updates", 
                style="Small.TLabel"
            )
            help_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        except Exception as e:
            print(f"Error creating online section: {str(e)}")
    
    def _create_progress_section(self, parent) -> None:
        """Create progress section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Progress bar
            self.progress_bar = ttk.Progressbar(
                section_frame,
                variable=self.progress_var,
                maximum=100,
                style="Modern.TProgressbar"
            )
            self.progress_bar.pack(fill=tk.X, pady=SPACING_S)
            
            # Initially hidden
            self.progress_bar.pack_forget()
        except Exception as e:
            print(f"Error creating progress section: {str(e)}")
    
    def _create_status_section(self, parent) -> None:
        """Create status section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Status label
            self.status_label = self.create_modern_label(
                section_frame, 
                "Ready to activate license", 
                style="Body.TLabel"
            )
            self.status_label.pack(anchor=tk.W, pady=SPACING_S)
            self.status_label.configure(textvariable=self.status_var)
        except Exception as e:
            print(f"Error creating status section: {str(e)}")
    
    def _create_button_section(self, parent) -> None:
        """Create button section"""
        try:
            # Button frame
            button_frame = self.create_modern_frame(parent, padding=SPACING_M)
            button_frame.pack(fill=tk.X, pady=SPACING_L)
            
            # Buttons
            buttons = [
                ("Activate", self._on_activate, "Success.TButton"),
                ("Cancel", self._on_cancel, "Secondary.TButton")
            ]
            
            self.create_button_group(button_frame, buttons, spacing=SPACING_M)
            
            # Store button references
            self.activate_button = button_frame.winfo_children()[0]
            self.cancel_button = button_frame.winfo_children()[1]
        except Exception as e:
            print(f"Error creating button section: {str(e)}")
    
    def _create_hardware_info_section(self, parent) -> None:
        """Create hardware information section"""
        try:
            # Section frame
            section_frame = self.create_modern_frame(parent, style="Panel.TFrame", padding=SPACING_M)
            section_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                section_frame, 
                "System Information", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Generate hardware fingerprint
            fingerprint_data = self.hardware_fingerprint.generate_fingerprint(
                HardwareFingerprint.METHOD_ADVANCED
            )
            
            # Display hardware info (non-sensitive)
            hardware_info = self.hardware_fingerprint.get_fingerprint_summary(fingerprint_data)
            
            # Create info labels
            info_text = f"""
            CPU: {hardware_info['components'].get('cpu', {}).get('name', 'Unknown')}
            Memory: {hardware_info['components'].get('memory', {}).get('capacity_gb', 'Unknown')} GB
            System: {hardware_info['components'].get('system', {}).get('platform', 'Unknown')}
            Fingerprint Method: {hardware_info['method']}
            """
            
            info_label = self.create_modern_label(
                section_frame, 
                info_text.strip(), 
                style="Small.TLabel",
                justify=tk.LEFT
            )
            info_label.pack(anchor=tk.W, pady=SPACING_S)
        except Exception as e:
            print(f"Error creating hardware info section: {str(e)}")
    
    def _validate_license_key(self, *args) -> None:
        """Validate license key format"""
        try:
            license_key = self.license_key_var.get().strip().upper()
            
            # Basic format validation (XXXX-XXXX-XXXX-XXXX)
            if len(license_key) == 19:
                parts = license_key.split('-')
                if len(parts) == 4 and all(len(part) == 4 for part in parts):
                    # Valid format
                    self.license_key_var.set(license_key)
                    return
            
            # Invalid format
            self.status_var.set("Invalid license key format (XXXX-XXXX-XXXX-XXXX)")
        except Exception as e:
            print(f"Error validating license key: {str(e)}")
    
    def _on_activate(self) -> None:
        """Handle activate button click"""
        try:
            if self.is_activating:
                return
            
            # Validate inputs
            license_key = self.license_key_var.get().strip()
            activation_code = self.activation_code_var.get().strip()
            online = self.online_var.get()
            
            if not license_key:
                messagebox.showerror("Error", "Please enter a license key")
                return
            
            # For trial activation, allow empty activation code
            if not activation_code and not license_key.lower().startswith('trial'):
                messagebox.showerror("Error", "Please enter an activation code")
                return
            
            # Start activation
            self._start_activation(license_key, activation_code, online)
        except Exception as e:
            messagebox.showerror("Error", f"Activation failed: {str(e)}")
    
    def _on_cancel(self) -> None:
        """Handle cancel button click"""
        try:
            if self.is_activating:
                if not messagebox.askyesno("Cancel Activation", 
                                       "Activation is in progress. Cancel anyway?"):
                    return
            
            self.dialog.destroy()
        except Exception as e:
            print(f"Error canceling activation: {str(e)}")
    
    def _start_activation(self, license_key: str, activation_code: str, online: bool) -> None:
        """Start license activation process"""
        try:
            self.is_activating = True
            self.status_var.set("Activating license...")
            self.progress_var.set(0)
            
            # Show progress bar
            self.progress_bar.pack(fill=tk.X, pady=SPACING_S, before=self.status_label.master)
            
            # Disable buttons
            self.activate_button.configure(state=tk.DISABLED)
            self.cancel_button.configure(state=tk.DISABLED)
            
            # Update progress
            self.dialog.update()
            self.progress_var.set(10)
            
            # Get hardware fingerprint
            fingerprint_data = self.hardware_fingerprint.generate_fingerprint(
                HardwareFingerprint.METHOD_ADVANCED
            )
            hardware_fingerprint = fingerprint_data.get('hash', '')
            
            # Update progress
            self.progress_var.set(30)
            self.status_var.set("Connecting to license server...")
            self.dialog.update()
            
            # Activate license
            activation_result = self.license_manager.activate_license(
                license_key, activation_code, online
            )
            
            # Update progress
            self.progress_var.set(70)
            self.status_var.set("Finalizing activation...")
            self.dialog.update()
            
            # Process result
            self._process_activation_result(activation_result)
            
            # Complete progress
            self.progress_var.set(100)
            self.dialog.update()
            
            # Re-enable buttons
            self.activate_button.configure(state=tk.NORMAL)
            self.cancel_button.configure(state=tk.NORMAL)
            
            self.is_activating = False
            
            # Handle result
            if activation_result['success']:
                self.status_var.set("License activated successfully!")
                
                # Show success dialog
                messagebox.showinfo("Success", activation_result['message'])
                
                # Call success callback
                if self.on_success:
                    self.on_success(activation_result)
                
                # Close dialog after delay
                self.dialog.after(2000, self.dialog.destroy)
            else:
                self.status_var.set(f"Activation failed: {activation_result['message']}")
                messagebox.showerror("Activation Failed", activation_result['message'])
        except Exception as e:
            self.is_activating = False
            self.status_var.set(f"Activation error: {str(e)}")
            messagebox.showerror("Error", f"Activation error: {str(e)}")
            
            # Re-enable buttons
            if self.activate_button:
                self.activate_button.configure(state=tk.NORMAL)
            if self.cancel_button:
                self.cancel_button.configure(state=tk.NORMAL)
    
    def _process_activation_result(self, result: Dict[str, Any]) -> None:
        """Process activation result"""
        try:
            self.activation_result = result
            
            # Log activation attempt
            if result.get('success'):
                print(f"License activated successfully: {result.get('license_info', {}).get('license_key')}")
            else:
                print(f"License activation failed: {result.get('message')}")
        except Exception as e:
            print(f"Error processing activation result: {str(e)}")
    
    def get_activation_result(self) -> Optional[Dict[str, Any]]:
        """Get last activation result"""
        return self.activation_result
    
    def reset_form(self) -> None:
        """Reset activation form"""
        try:
            self.license_key_var.set("")
            self.activation_code_var.set("")
            self.online_var.set(True)
            self.progress_var.set(0)
            self.status_var.set("Ready to activate license")
            self.is_activating = False
            self.activation_result = None
            
            # Hide progress bar
            if self.progress_bar:
                self.progress_bar.pack_forget()
            
            # Re-enable buttons
            if self.activate_button:
                self.activate_button.configure(state=tk.NORMAL)
            if self.cancel_button:
                self.cancel_button.configure(state=tk.NORMAL)
        except Exception as e:
            print(f"Error resetting form: {str(e)}")
    
    def set_license_key(self, license_key: str) -> None:
        """Set license key programmatically"""
        try:
            self.license_key_var.set(license_key)
            self._validate_license_key()
        except Exception as e:
            print(f"Error setting license key: {str(e)}")
    
    def set_activation_code(self, activation_code: str) -> None:
        """Set activation code programmatically"""
        try:
            self.activation_code_var.set(activation_code)
        except Exception as e:
            print(f"Error setting activation code: {str(e)}")
    
    def set_online_mode(self, online: bool) -> None:
        """Set online activation mode"""
        try:
            self.online_var.set(online)
        except Exception as e:
            print(f"Error setting online mode: {str(e)}")