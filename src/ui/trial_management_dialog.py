"""
Trial Management Dialog for POS MVP application
Handles trial period management and activation
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable

from src.ui.base_ui import BaseUI
from src.utils.constants import *
from src.utils.license_manager import LicenseManager
from src.models.license import License


class TrialManagementDialog(BaseUI):
    """
    Trial Management Dialog for trial period management
    Provides comprehensive UI for trial activation and management
    """
    
    def __init__(self, parent, app, license_manager: LicenseManager):
        """
        Initialize trial management dialog
        
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
        self.info_frame = None
        self.activation_frame = None
        self.extension_frame = None
        
        # Trial data
        self.trial_info = {}
        self.activation_info = {}
    
    def show_dialog(self) -> Dict[str, Any]:
        """
        Show the trial management dialog
        
        Returns:
            Dialog result
        """
        try:
            # Create dialog
            self._create_dialog()
            
            # Load trial information
            self._load_trial_info()
            
            # Update UI
            self._update_ui()
            
            # Show dialog
            self.dialog.wait_window()
            
            return self.result
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show dialog: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_dialog(self) -> None:
        """Create the trial management dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.root)
            self.dialog.title("Trial Management")
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
            self._create_trial_info()
            self._create_activation_options()
            self._create_extension_options()
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
                "Trial Period Management", 
                style="Title.TLabel"
            )
            title_label.pack(anchor=tk.W)
            
            # Description
            desc_label = self.create_modern_label(
                header_frame, 
                "Manage your trial period and activate full features", 
                style="Body.TLabel"
            )
            desc_label.pack(anchor=tk.W, pady=(SPACING_S, 0))
        except Exception as e:
            print(f"Error creating header: {str(e)}")
    
    def _create_trial_info(self) -> None:
        """Create trial information section"""
        try:
            # Info frame
            self.info_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.info_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.info_frame, 
                "Trial Information", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Trial info fields
            info_fields = [
                ("Trial Status:", "trial_status"),
                ("Days Remaining:", "days_remaining"),
                ("Trial Started:", "trial_started"),
                ("Trial Expires:", "trial_expires"),
                ("Features Available:", "features_available")
            ]
            
            # Create info labels
            self.info_labels = {}
            for label_text, field_key in info_fields:
                field_frame = ttk.Frame(self.info_frame)
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
            print(f"Error creating trial info: {str(e)}")
    
    def _create_activation_options(self) -> None:
        """Create activation options section"""
        try:
            # Activation frame
            self.activation_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.activation_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.activation_frame, 
                "Activation Options", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # License key input
            key_frame = ttk.Frame(self.activation_frame)
            key_frame.pack(fill=tk.X, pady=SPACING_S)
            
            key_label = self.create_modern_label(
                key_frame, 
                "License Key:", 
                style="Body.TLabel",
                width=12
            )
            key_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.license_key_var = tk.StringVar()
            self.license_key_entry = self.create_modern_entry(
                key_frame,
                textvariable=self.license_key_var
            )
            self.license_key_entry.insert(0, "Enter your license key")
            self.license_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Activation code input
            code_frame = ttk.Frame(self.activation_frame)
            code_frame.pack(fill=tk.X, pady=SPACING_S)
            
            code_label = self.create_modern_label(
                code_frame, 
                "Activation Code:", 
                style="Body.TLabel",
                width=12
            )
            code_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.activation_code_var = tk.StringVar()
            self.activation_code_entry = self.create_modern_entry(
                code_frame,
                textvariable=self.activation_code_var
            )
            self.activation_code_entry.insert(0, "Enter your activation code")
            self.activation_code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Online activation option
            self.online_var = tk.BooleanVar(value=True)
            online_check = self.create_modern_checkbutton(
                self.activation_frame, 
                self.online_var, 
                "Online Activation (Recommended)"
            )
            online_check.pack(anchor=tk.W, pady=SPACING_S)
            
            # Activate button
            activate_button = self.create_modern_button(
                self.activation_frame, 
                "Activate License", 
                self._on_activate_license,
                style="Primary.TButton"
            )
            activate_button.pack(pady=SPACING_M)
        except Exception as e:
            print(f"Error creating activation options: {str(e)}")
    
    def _create_extension_options(self) -> None:
        """Create extension options section"""
        try:
            # Extension frame
            self.extension_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.extension_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.extension_frame, 
                "Trial Extension", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Extension info
            info_label = self.create_modern_label(
                self.extension_frame, 
                "Need more time to evaluate? Request a trial extension.", 
                style="Body.TLabel"
            )
            info_label.pack(anchor=tk.W, pady=SPACING_S)
            
            # Extension reason
            reason_frame = ttk.Frame(self.extension_frame)
            reason_frame.pack(fill=tk.X, pady=SPACING_S)
            
            reason_label = self.create_modern_label(
                reason_frame, 
                "Reason:", 
                style="Body.TLabel",
                width=12
            )
            reason_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.extension_reason_var = tk.StringVar()
            self.extension_reason_entry = self.create_modern_entry(
                reason_frame,
                textvariable=self.extension_reason_var
            )
            self.extension_reason_entry.insert(0, "Why do you need an extension?")
            self.extension_reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Request extension button
            request_button = self.create_modern_button(
                self.extension_frame, 
                "Request Extension", 
                self._on_request_extension,
                style="Secondary.TButton"
            )
            request_button.pack(pady=SPACING_M)
        except Exception as e:
            print(f"Error creating extension options: {str(e)}")
    
    def _create_actions(self) -> None:
        """Create action buttons"""
        try:
            # Actions frame
            actions_frame = ttk.Frame(self.main_frame)
            actions_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Buttons
            buttons = [
                ("Continue Trial", self._on_continue_trial, "Secondary.TButton"),
                ("Purchase License", self._on_purchase_license, "Success.TButton"),
                ("Close", self._on_close, "Default.TButton")
            ]
            
            self.create_button_group(actions_frame, buttons, spacing=SPACING_M)
        except Exception as e:
            print(f"Error creating actions: {str(e)}")
    
    def _load_trial_info(self) -> None:
        """Load trial information"""
        try:
            # Get trial status
            status = self.license_manager.get_trial_status()
            
            # Update trial info
            self.trial_info = status.get('trial_info', {})
            self.activation_info = status.get('activation_info', {})
        except Exception as e:
            print(f"Error loading trial info: {str(e)}")
    
    def _update_ui(self) -> None:
        """Update UI with trial information"""
        try:
            # Update trial info
            self._update_trial_info()
            
            # Update activation options
            self._update_activation_options()
            
            # Update extension options
            self._update_extension_options()
        except Exception as e:
            print(f"Error updating UI: {str(e)}")
    
    def _update_trial_info(self) -> None:
        """Update trial information display"""
        try:
            if not self.info_labels:
                return
            
            # Get trial info
            trial_status = self.trial_info.get('status', 'unknown')
            days_remaining = self.trial_info.get('days_remaining', 0)
            trial_started = self.trial_info.get('started_date')
            trial_expires = self.trial_info.get('expires_date')
            features = self.trial_info.get('features', [])
            
            # Update info fields
            self.info_labels['trial_status'].configure(text=trial_status.title())
            self.info_labels['days_remaining'].configure(text=f"{days_remaining} days")
            self.info_labels['trial_started'].configure(text=self._format_date(trial_started))
            self.info_labels['trial_expires'].configure(text=self._format_date(trial_expires))
            self.info_labels['features_available'].configure(text=f"{len(features)} features available")
        except Exception as e:
            print(f"Error updating trial info: {str(e)}")
    
    def _update_activation_options(self) -> None:
        """Update activation options based on trial status"""
        try:
            # Check if trial is active
            trial_active = self.trial_info.get('status') == 'active'
            
            # Enable/disable activation options
            state = tk.NORMAL if trial_active else tk.DISABLED
            self.license_key_entry.configure(state=state)
            self.activation_code_entry.configure(state=state)
            
            # Update activation frame visibility
            if trial_active:
                self.activation_frame.pack(fill=tk.X, pady=SPACING_M)
            else:
                self.activation_frame.pack_forget()
        except Exception as e:
            print(f"Error updating activation options: {str(e)}")
    
    def _update_extension_options(self) -> None:
        """Update extension options based on trial status"""
        try:
            # Check if trial is active
            trial_active = self.trial_info.get('status') == 'active'
            days_remaining = self.trial_info.get('days_remaining', 0)
            
            # Enable/disable extension options
            state = tk.NORMAL if trial_active and days_remaining <= 7 else tk.DISABLED
            self.extension_reason_entry.configure(state=state)
            
            # Update extension frame visibility
            if trial_active and days_remaining <= 7:
                self.extension_frame.pack(fill=tk.X, pady=SPACING_M)
            else:
                self.extension_frame.pack_forget()
        except Exception as e:
            print(f"Error updating extension options: {str(e)}")
    
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
    
    def _on_activate_license(self) -> None:
        """Handle activate license button click"""
        try:
            # Get input values
            license_key = self.license_key_var.get().strip()
            activation_code = self.activation_code_var.get().strip()
            online = self.online_var.get()
            
            # Validate input
            if not license_key:
                messagebox.showerror("Error", "Please enter a license key")
                return
            
            if not activation_code:
                messagebox.showerror("Error", "Please enter an activation code")
                return
            
            # Show progress
            self._show_progress("Activating license...")
            
            # Activate license
            result = self.license_manager.activate_license(
                license_key=license_key,
                activation_code=activation_code,
                online=online
            )
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                messagebox.showinfo("Success", "License activated successfully")
                self.result = {'success': True, 'action': 'activated'}
                self.dialog.destroy()
            else:
                messagebox.showerror("Activation Failed", f"License activation failed: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Activation error: {str(e)}")
    
    def _on_request_extension(self) -> None:
        """Handle request extension button click"""
        try:
            # Get reason
            reason = self.extension_reason_var.get().strip()
            
            # Validate input
            if not reason:
                messagebox.showerror("Error", "Please enter a reason for the extension")
                return
            
            # Show progress
            self._show_progress("Requesting extension...")
            
            # Request extension
            result = self.license_manager.request_trial_extension(reason)
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                messagebox.showinfo("Success", "Trial extension requested successfully")
                # Reload trial info
                self._load_trial_info()
                self._update_ui()
            else:
                messagebox.showerror("Extension Failed", f"Trial extension failed: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Extension error: {str(e)}")
    
    def _on_continue_trial(self) -> None:
        """Handle continue trial button click"""
        try:
            # Show progress
            self._show_progress("Creating trial license...")
            
            # Collect customer information for trial license
            customer_name = "Trial User"
            customer_email = "trial@example.com"
            
            # Try to get user information from the application if available
            if hasattr(self, 'app') and hasattr(self.app, 'current_user'):
                current_user = self.app.current_user
                if current_user and 'username' in current_user:
                    customer_name = current_user['username']
                    customer_email = f"{current_user['username']}@example.com"
            
            # Create trial license with customer information
            result = self.license_manager.create_trial_license(
                customer_name=customer_name,
                customer_email=customer_email
            )
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                messagebox.showinfo("Success", "Trial license created successfully")
                self.result = {'success': True, 'action': 'continue_trial'}
                self.dialog.destroy()
            else:
                messagebox.showerror("Trial Creation Failed", f"Failed to create trial license: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Error creating trial license: {str(e)}")
    
    def _on_purchase_license(self) -> None:
        """Handle purchase license button click"""
        try:
            # Open purchase URL
            import webbrowser
            webbrowser.open("https://example.com/purchase")
            
            messagebox.showinfo("Purchase", "Opening purchase page in your browser...")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening purchase page: {str(e)}")
    
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