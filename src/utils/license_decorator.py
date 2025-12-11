"""
License Decorator for POS MVP application
Provides decorators for license-based feature access control
"""

import functools
from typing import Callable, Any, Optional
import tkinter as tk
from tkinter import messagebox


def require_license_feature(feature: str, fallback_message: Optional[str] = None):
    """
    Decorator to require a specific license feature for a function
    
    Args:
        feature: Feature name required
        fallback_message: Optional custom message to show if feature not available
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            try:
                # Get app instance
                app = None
                if hasattr(self, 'app'):
                    app = self.app
                elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                    app = self.master.app
                elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                    app = self.root.app
                
                # Check feature access
                if app and hasattr(app, 'check_feature_access'):
                    if not app.check_feature_access(feature):
                        # Feature not available
                        message = fallback_message or f"This feature requires a license with '{feature}' access."
                        messagebox.showwarning("Feature Not Available", message)
                        return None
                
                # Call original function
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"Error in license decorator: {str(e)}")
                # Call original function on error
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def require_license_level(min_level: str, fallback_message: Optional[str] = None):
    """
    Decorator to require a minimum license level
    
    Args:
        min_level: Minimum license level required (trial, standard, professional, enterprise)
        fallback_message: Optional custom message to show if level not sufficient
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            try:
                # Get app instance
                app = None
                if hasattr(self, 'app'):
                    app = self.app
                elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                    app = self.master.app
                elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                    app = self.root.app
                
                # Check license level
                if app and hasattr(app, 'license_integration'):
                    license_info = app.license_integration.get_license_info()
                    license_type = license_info.get('license_type', 'trial')
                    
                    # Define license levels
                    license_levels = {
                        'trial': 0,
                        'standard': 1,
                        'professional': 2,
                        'enterprise': 3
                    }
                    
                    current_level = license_levels.get(license_type, 0)
                    required_level = license_levels.get(min_level, 0)
                    
                    if current_level < required_level:
                        # License level insufficient
                        message = fallback_message or f"This feature requires a {min_level} license or higher."
                        messagebox.showwarning("License Level Required", message)
                        return None
                
                # Call original function
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"Error in license level decorator: {str(e)}")
                # Call original function on error
                return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def license_feature_button(feature: str, button_text: str, command: Callable, 
                       parent: tk.Widget, **button_kwargs):
    """
    Create a button that is enabled/disabled based on license feature
    
    Args:
        feature: Feature name required
        button_text: Text to display on button
        command: Command to execute when button is clicked
        parent: Parent widget
        **button_kwargs: Additional arguments for button creation
        
    Returns:
        Created button widget
    """
    try:
        # Create button
        button = tk.Button(parent, text=button_text, command=command, **button_kwargs)
        
        # Get app instance
        app = None
        if hasattr(parent, 'app'):
            app = parent.app
        elif hasattr(parent, 'master') and hasattr(parent.master, 'app'):
            app = parent.master.app
        elif hasattr(parent, 'root') and hasattr(parent.root, 'app'):
            app = parent.root.app
        
        # Check feature access and enable/disable button
        if app and hasattr(app, 'check_feature_access'):
            if not app.check_feature_access(feature):
                button.config(state=tk.DISABLED)
        
        return button
    except Exception as e:
        print(f"Error creating license feature button: {str(e)}")
        # Create regular button on error
        return tk.Button(parent, text=button_text, command=command, **button_kwargs)


def license_feature_menuitem(feature: str, menu_text: str, command: Callable, 
                         menu: tk.Menu, **menuitem_kwargs):
    """
    Create a menu item that is enabled/disabled based on license feature
    
    Args:
        feature: Feature name required
        menu_text: Text to display on menu item
        command: Command to execute when menu item is clicked
        menu: Menu widget
        **menuitem_kwargs: Additional arguments for menu item creation
        
    Returns:
        Created menu item
    """
    try:
        # Get app instance
        app = None
        if hasattr(menu, 'app'):
            app = menu.app
        elif hasattr(menu, 'master') and hasattr(menu.master, 'app'):
            app = menu.master.app
        elif hasattr(menu, 'root') and hasattr(menu.root, 'app'):
            app = menu.root.app
        
        # Check feature access
        enabled = True
        if app and hasattr(app, 'check_feature_access'):
            enabled = app.check_feature_access(feature)
        
        # Create menu item
        menu.add_command(label=menu_text, command=command, state=tk.NORMAL if enabled else tk.DISABLED, **menuitem_kwargs)
        
        return menu
    except Exception as e:
        print(f"Error creating license feature menu item: {str(e)}")
        # Create regular menu item on error
        menu.add_command(label=menu_text, command=command, **menuitem_kwargs)
        return menu


def validate_license_on_action(func: Callable) -> Callable:
    """
    Decorator to validate license before executing an action
    
    Args:
        func: Function to wrap
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        try:
            # Get app instance
            app = None
            if hasattr(self, 'app'):
                app = self.app
            elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                app = self.master.app
            elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                app = self.root.app
            
            # Validate license
            if app and hasattr(app, 'license_integration'):
                # Check if license is valid
                license_info = app.license_integration.get_license_info()
                license_status = license_info.get('status', 'unknown')
                
                if license_status != 'active':
                    messagebox.showwarning("License Required", 
                                      "A valid license is required to perform this action. Please activate your license.")
                    return None
                
                # Check if trial has expired
                if app.license_integration.is_trial_expired():
                    messagebox.showwarning("Trial Expired", 
                                      "Your trial period has expired. Please upgrade to continue using this feature.")
                    return None
                
                # Periodic validation
                app.license_integration.validate_license_periodically()
            
            # Call original function
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"Error in license validation decorator: {str(e)}")
            # Call original function on error
            return func(self, *args, **kwargs)
    
    return wrapper


class LicenseFeatureMixin:
    """
    Mixin class for license feature access control
    Provides methods for checking license features in UI components
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._license_features_checked = set()
    
    def check_license_feature(self, feature: str, show_warning: bool = True) -> bool:
        """
        Check if a license feature is available
        
        Args:
            feature: Feature name to check
            show_warning: Whether to show warning if feature not available
            
        Returns:
            True if feature is available, False otherwise
        """
        try:
            # Get app instance
            app = None
            if hasattr(self, 'app'):
                app = self.app
            elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                app = self.master.app
            elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                app = self.root.app
            
            # Check feature access
            if app and hasattr(app, 'check_feature_access'):
                has_feature = app.check_feature_access(feature)
                
                # Show warning if needed
                if not has_feature and show_warning and feature not in self._license_features_checked:
                    messagebox.showwarning("Feature Not Available", 
                                      f"This feature requires a license with '{feature}' access.")
                    self._license_features_checked.add(feature)
                
                return has_feature
            
            return True  # Default to True if license system not available
        except Exception as e:
            print(f"Error checking license feature: {str(e)}")
            return True  # Default to True on error
    
    def get_license_info(self) -> dict:
        """
        Get current license information
        
        Returns:
            License information dictionary
        """
        try:
            # Get app instance
            app = None
            if hasattr(self, 'app'):
                app = self.app
            elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                app = self.master.app
            elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                app = self.root.app
            
            # Get license info
            if app and hasattr(app, 'license_integration'):
                return app.license_integration.get_license_info()
            
            return {}
        except Exception as e:
            print(f"Error getting license info: {str(e)}")
            return {}
    
    def is_trial_mode(self) -> bool:
        """
        Check if running in trial mode
        
        Returns:
            True if in trial mode, False otherwise
        """
        try:
            # Get app instance
            app = None
            if hasattr(self, 'app'):
                app = self.app
            elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                app = self.master.app
            elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                app = self.root.app
            
            # Check trial mode
            if app and hasattr(app, 'license_integration'):
                return app.license_integration.trial_mode
            
            return False
        except Exception as e:
            print(f"Error checking trial mode: {str(e)}")
            return False
    
    def get_trial_days_remaining(self) -> int:
        """
        Get number of days remaining in trial
        
        Returns:
            Number of days remaining, 0 if not in trial
        """
        try:
            # Get app instance
            app = None
            if hasattr(self, 'app'):
                app = self.app
            elif hasattr(self, 'master') and hasattr(self.master, 'app'):
                app = self.master.app
            elif hasattr(self, 'root') and hasattr(self.root, 'app'):
                app = self.root.app
            
            # Get trial info
            if app and hasattr(app, 'license_integration'):
                trial_info = app.license_integration.get_trial_info()
                return trial_info.get('days_remaining', 0)
            
            return 0
        except Exception as e:
            print(f"Error getting trial days remaining: {str(e)}")
            return 0