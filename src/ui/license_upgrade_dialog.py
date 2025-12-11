"""
License Upgrade Dialog for POS MVP application
Handles license upgrade and feature enhancement
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable, List

from src.ui.base_ui import BaseUI
from src.utils.constants import *
from src.utils.license_manager import LicenseManager
from src.models.license import License


class LicenseUpgradeDialog(BaseUI):
    """
    License Upgrade Dialog for license upgrade and feature enhancement
    Provides comprehensive UI for license upgrade options and processing
    """
    
    def __init__(self, parent, app, license_manager: LicenseManager):
        """
        Initialize license upgrade dialog
        
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
        self.options_frame = None
        self.payment_frame = None
        self.confirmation_frame = None
        
        # License data
        self.current_license = {}
        self.available_upgrades = []
        self.selected_upgrade = None
        self.upgrade_details = {}
    
    def show_dialog(self) -> Dict[str, Any]:
        """
        Show the license upgrade dialog
        
        Returns:
            Dialog result
        """
        try:
            # Create dialog
            self._create_dialog()
            
            # Load license information
            self._load_license_info()
            
            # Load upgrade options
            self._load_upgrade_options()
            
            # Update UI
            self._update_ui()
            
            # Show dialog
            self.dialog.wait_window()
            
            return self.result
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show dialog: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_dialog(self) -> None:
        """Create the license upgrade dialog"""
        try:
            # Create dialog window
            self.dialog = tk.Toplevel(self.root)
            self.dialog.title("License Upgrade")
            self.dialog.geometry("700x600")
            self.dialog.resizable(True, True)
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
            self._create_upgrade_options()
            self._create_payment_section()
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
                "License Upgrade", 
                style="Title.TLabel"
            )
            title_label.pack(anchor=tk.W)
            
            # Description
            desc_label = self.create_modern_label(
                header_frame, 
                "Upgrade your license to access additional features and capabilities", 
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
                "Current License", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Current license info
            info_frame = ttk.Frame(self.current_frame)
            info_frame.pack(fill=tk.X, pady=SPACING_S)
            
            # License info fields
            self.current_labels = {}
            info_fields = [
                ("License Type:", "license_type"),
                ("Status:", "status"),
                ("Expiry Date:", "expiry_date"),
                ("Features:", "feature_count")
            ]
            
            for label_text, field_key in info_fields:
                field_frame = ttk.Frame(info_frame)
                field_frame.pack(fill=tk.X, pady=SPACING_S)
                
                # Label
                label = self.create_modern_label(
                    field_frame, 
                    label_text, 
                    style="Body.TLabel",
                    width=12
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
    
    def _create_upgrade_options(self) -> None:
        """Create upgrade options section"""
        try:
            # Options frame
            self.options_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.options_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.options_frame, 
                "Available Upgrades", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Upgrade options treeview
            columns = ("license_type", "features", "price", "duration")
            headings = ("License Type", "Features", "Price", "Duration")
            
            self.upgrade_tree = self.create_modern_treeview(
                self.options_frame, 
                columns, 
                headings,
                column_widths=[150, 200, 100, 100],
                select_mode="browse"
            )
            
            # Configure treeview
            self.upgrade_tree.pack(fill=tk.BOTH, expand=True, pady=SPACING_S)
            self.upgrade_tree.bind("<<TreeviewSelect>>", self._on_upgrade_select)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(self.options_frame, orient=tk.VERTICAL, command=self.upgrade_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.upgrade_tree.configure(yscrollcommand=scrollbar.set)
            
            # Upgrade details frame
            details_frame = self.create_modern_frame(self.options_frame, padding=SPACING_M)
            details_frame.pack(fill=tk.X, pady=SPACING_S)
            
            # Details title
            details_title = self.create_modern_label(
                details_frame, 
                "Upgrade Details", 
                style="SectionTitle.TLabel"
            )
            details_title.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Details text
            self.details_text = tk.Text(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
            self.details_text.pack(fill=tk.BOTH, expand=True)
            
            # Configure text widget
            self.details_text.tag_configure("title", font=("Arial", 10, "bold"))
            self.details_text.tag_configure("feature", font=("Arial", 9))
        except Exception as e:
            print(f"Error creating upgrade options: {str(e)}")
    
    def _create_payment_section(self) -> None:
        """Create payment section"""
        try:
            # Payment frame
            self.payment_frame = self.create_modern_frame(self.main_frame, style="Panel.TFrame", padding=SPACING_M)
            self.payment_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Section title
            title_label = self.create_modern_label(
                self.payment_frame, 
                "Payment Information", 
                style="SectionTitle.TLabel"
            )
            title_label.pack(anchor=tk.W, pady=(0, SPACING_S))
            
            # Payment method
            method_frame = ttk.Frame(self.payment_frame)
            method_frame.pack(fill=tk.X, pady=SPACING_S)
            
            method_label = self.create_modern_label(
                method_frame, 
                "Payment Method:", 
                style="Body.TLabel",
                width=12
            )
            method_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.payment_method_var = tk.StringVar(value="credit_card")
            methods = [
                ("Credit Card", "credit_card"),
                ("PayPal", "paypal"),
                ("Bank Transfer", "bank_transfer")
            ]
            
            for text, value in methods:
                radio = self.create_modern_radiobutton(
                    method_frame, 
                    self.payment_method_var, 
                    text, 
                    value
                )
                radio.pack(side=tk.LEFT, padx=SPACING_S)
            
            # Promotional code
            promo_frame = ttk.Frame(self.payment_frame)
            promo_frame.pack(fill=tk.X, pady=SPACING_S)
            
            promo_label = self.create_modern_label(
                promo_frame, 
                "Promo Code:", 
                style="Body.TLabel",
                width=12
            )
            promo_label.pack(side=tk.LEFT, padx=(0, SPACING_S))
            
            self.promo_code_var = tk.StringVar()
            self.promo_code_entry = self.create_modern_entry(
                promo_frame,
                textvariable=self.promo_code_var
            )
            self.promo_code_entry.insert(0, "Enter promotional code (optional)")
            self.promo_code_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Apply promo button
            apply_button = self.create_modern_button(
                promo_frame, 
                "Apply", 
                self._on_apply_promo,
                style="Secondary.TButton"
            )
            apply_button.pack(side=tk.LEFT, padx=SPACING_S)
        except Exception as e:
            print(f"Error creating payment section: {str(e)}")
    
    def _create_actions(self) -> None:
        """Create action buttons"""
        try:
            # Actions frame
            actions_frame = ttk.Frame(self.main_frame)
            actions_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Buttons
            buttons = [
                ("Upgrade License", self._on_upgrade_license, "Primary.TButton"),
                ("Purchase New License", self._on_purchase_new, "Success.TButton"),
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
    
    def _load_upgrade_options(self) -> None:
        """Load available upgrade options"""
        try:
            # Get available upgrades
            upgrades = self.license_manager.get_available_upgrades()
            
            # Update available upgrades
            self.available_upgrades = upgrades
        except Exception as e:
            print(f"Error loading upgrade options: {str(e)}")
    
    def _update_ui(self) -> None:
        """Update UI with license and upgrade information"""
        try:
            # Update current license
            self._update_current_license()
            
            # Update upgrade options
            self._update_upgrade_options()
        except Exception as e:
            print(f"Error updating UI: {str(e)}")
    
    def _update_current_license(self) -> None:
        """Update current license display"""
        try:
            if not self.current_labels:
                return
            
            # Get license info
            license_type = self.current_license.get('license_type', 'Unknown')
            status = self.current_license.get('status', 'Unknown')
            expiry_date = self.current_license.get('expiry_date')
            features = self.current_license.get('features', [])
            
            # Update info fields
            self.current_labels['license_type'].configure(text=license_type.title())
            self.current_labels['status'].configure(text=status.title())
            self.current_labels['expiry_date'].configure(text=self._format_date(expiry_date))
            self.current_labels['feature_count'].configure(text=f"{len(features)} features")
        except Exception as e:
            print(f"Error updating current license: {str(e)}")
    
    def _update_upgrade_options(self) -> None:
        """Update upgrade options display"""
        try:
            if not hasattr(self, 'upgrade_tree'):
                return
            
            # Clear existing items
            for item in self.upgrade_tree.get_children():
                self.upgrade_tree.delete(item)
            
            # Add upgrade options to tree
            for upgrade in self.available_upgrades:
                license_type = upgrade.get('license_type', 'Unknown')
                features = upgrade.get('features', [])
                price = upgrade.get('price', '0.00')
                duration = upgrade.get('duration', 'perpetual')
                
                self.upgrade_tree.insert("", tk.END, values=(
                    license_type.title(),
                    f"{len(features)} features",
                    f"${price}",
                    duration
                ), tags=(upgrade.get('id'),))
        except Exception as e:
            print(f"Error updating upgrade options: {str(e)}")
    
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
    
    def _on_upgrade_select(self, event) -> None:
        """Handle upgrade selection"""
        try:
            # Get selected item
            selection = self.upgrade_tree.selection()
            if not selection:
                return
            
            # Get upgrade ID
            item = self.upgrade_tree.item(selection[0])
            tags = item.get('tags', [])
            if not tags:
                return
            
            upgrade_id = tags[0]
            
            # Find upgrade details
            for upgrade in self.available_upgrades:
                if upgrade.get('id') == upgrade_id:
                    self.selected_upgrade = upgrade
                    self._show_upgrade_details(upgrade)
                    break
        except Exception as e:
            print(f"Error handling upgrade selection: {str(e)}")
    
    def _show_upgrade_details(self, upgrade: Dict[str, Any]) -> None:
        """Show upgrade details"""
        try:
            if not hasattr(self, 'details_text'):
                return
            
            # Clear details
            self.details_text.configure(state=tk.NORMAL)
            self.details_text.delete(1.0, tk.END)
            
            # Add upgrade details
            license_type = upgrade.get('license_type', 'Unknown')
            features = upgrade.get('features', [])
            price = upgrade.get('price', '0.00')
            duration = upgrade.get('duration', 'perpetual')
            description = upgrade.get('description', '')
            
            # Title
            self.details_text.insert(tk.END, f"{license_type.title()} License\n", "title")
            self.details_text.insert(tk.END, f"Price: ${price} ({duration})\n\n")
            
            # Description
            if description:
                self.details_text.insert(tk.END, f"{description}\n\n")
            
            # Features
            self.details_text.insert(tk.END, "Features:\n", "title")
            for feature in features:
                self.details_text.insert(tk.END, f"• {feature}\n", "feature")
            
            # Configure text
            self.details_text.configure(state=tk.DISABLED)
        except Exception as e:
            print(f"Error showing upgrade details: {str(e)}")
    
    def _on_apply_promo(self) -> None:
        """Handle apply promotional code button click"""
        try:
            # Get promo code
            promo_code = self.promo_code_var.get().strip()
            
            if not promo_code:
                messagebox.showerror("Error", "Please enter a promotional code")
                return
            
            # Validate promo code
            result = self.license_manager.validate_promo_code(promo_code)
            
            if result['valid']:
                discount = result.get('discount', 0)
                messagebox.showinfo("Success", f"Promotional code applied! Discount: {discount}%")
            else:
                messagebox.showerror("Invalid Code", "The promotional code is invalid or expired")
        except Exception as e:
            messagebox.showerror("Error", f"Error applying promo code: {str(e)}")
    
    def _on_upgrade_license(self) -> None:
        """Handle upgrade license button click"""
        try:
            # Check if upgrade is selected
            if not self.selected_upgrade:
                messagebox.showerror("Error", "Please select an upgrade option")
                return
            
            # Confirm upgrade
            license_type = self.selected_upgrade.get('license_type', 'Unknown')
            price = self.selected_upgrade.get('price', '0.00')
            
            if not messagebox.askyesno("Confirm Upgrade", 
                                   f"Are you sure you want to upgrade to {license_type.title()} for ${price}?"):
                return
            
            # Show progress
            self._show_progress("Processing upgrade...")
            
            # Process upgrade
            result = self.license_manager.upgrade_license(
                upgrade_id=self.selected_upgrade.get('id'),
                payment_method=self.payment_method_var.get(),
                promo_code=self.promo_code_var.get().strip() or None
            )
            
            # Hide progress
            self._hide_progress()
            
            if result['success']:
                messagebox.showinfo("Success", "License upgraded successfully")
                self.result = {'success': True, 'action': 'upgraded', 'upgrade': self.selected_upgrade}
                self.dialog.destroy()
            else:
                messagebox.showerror("Upgrade Failed", f"License upgrade failed: {result.get('message')}")
        except Exception as e:
            self._hide_progress()
            messagebox.showerror("Error", f"Upgrade error: {str(e)}")
    
    def _on_purchase_new(self) -> None:
        """Handle purchase new license button click"""
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