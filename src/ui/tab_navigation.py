import tkinter as tk
from tkinter import ttk, messagebox
from src.utils.constants import *

class TabNavigation:
    """Modern browser-style tab navigation component for POS system"""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.tabs = {}  # {tab_id: tab_info}
        self.active_tab_id = None
        self.setup_ui()
    
    def setup_ui(self):
        """Create modern tab navigation UI"""
        # Main tab container with frame for styling
        self.tab_container = ttk.Frame(self.parent, style="TabContainer.TFrame")
        self.tab_container.pack(fill=tk.X, side=tk.TOP, pady=(10, 5))
        
        # Configure tab styling
        self.configure_tab_styles()
        
        # Create tabs
        self.create_main_tabs()
    
    def configure_tab_styles(self):
        """Configure modern tab styling using constants"""
        style = ttk.Style()
        
        # Inactive tab style
        style.configure("TabNav.TButton",
                       font=(FONT_FAMILY_PRIMARY, 10, 'normal'),
                       padding=(12, 6),
                       relief='flat',
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       borderwidth=0,
                       focuscolor='none')
        
        # Active tab style
        style.configure("ActiveTabNav.TButton",
                       font=(FONT_FAMILY_PRIMARY, 10, 'bold'),
                       padding=(12, 6),
                       relief='solid',
                       background=COLOR_PRIMARY_LIGHT,
                       foreground=COLOR_PRIMARY_DARK,
                       borderwidth=1,
                       bordercolor=COLOR_PRIMARY,
                       focuscolor='none')
        
        # Tab container style
        style.configure("TabContainer.TFrame",
                       background=COLOR_BACKGROUND_LIGHT,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_LIGHT)
        
        # Hover effect for tabs
        style.configure("TabNav.Hover.TButton",
                       font=(FONT_FAMILY_PRIMARY, 10, 'normal'),
                       padding=(12, 6),
                       relief='flat',
                       background=COLOR_HOVER,
                       foreground=COLOR_TEXT_PRIMARY,
                       borderwidth=0,
                       focuscolor='none')
        
        # Add button style
        style.configure("AddTab.TButton",
                       font=(FONT_FAMILY_PRIMARY, 10, 'normal'),
                       padding=(8, 4),
                       relief='flat',
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       borderwidth=1,
                       bordercolor=COLOR_BORDER_LIGHT,
                       focuscolor='none')
        
        style.map("TabNav.TButton",
                 background=[('active', COLOR_HOVER)],
                 foreground=[('active', COLOR_TEXT_PRIMARY)])
        
        style.map("AddTab.TButton",
                 background=[('active', COLOR_HOVER)],
                 foreground=[('active', COLOR_PRIMARY)])
    
    def create_main_tabs(self):
        """Create main navigation tabs"""
        # Define tabs with their properties
        main_tabs = [
            {
                'id': 'dashboard',
                'text': 'Dashboard',
                'icon': '📊',
                'command': lambda: self.app.show_dashboard(),
                'priority': 1,
                'always_visible': True
            },
            {
                'id': 'new_order',
                'text': 'New Order',
                'icon': '📝',
                'command': lambda: self.app.show_new_order(),
                'priority': 2,
                'always_visible': True
            },
            {
                'id': 'orders',
                'text': 'Orders',
                'icon': '📋',
                'command': lambda: self.app.show_orders(),
                'priority': 3,
                'always_visible': True
            },
            {
                'id': 'menu',
                'text': 'Menu',
                'icon': '🍽️',
                'command': lambda: self.app.show_menu(),
                'priority': 4,
                'always_visible': True
            },
            {
                'id': 'tables',
                'text': 'Tables',
                'icon': '🪑',
                'command': lambda: self.app.show_tables(),
                'priority': 5,
                'always_visible': True
            },
            {
                'id': 'inventory',
                'text': 'Inventory',
                'icon': '📦',
                'command': lambda: self.app.show_inventory(),
                'priority': 6,
                'always_visible': False
            },
            {
                'id': 'reports',
                'text': 'Reports',
                'icon': '📈',
                'command': lambda: self.app.show_reports(),
                'priority': 7,
                'always_visible': False
            },
            {
                'id': 'support',
                'text': 'Support',
                'icon': '🆘',
                'command': lambda: self.app.show_support_screen(),
                'priority': 8,
                'always_visible': False
            }
        ]
        
        # Admin-only tabs
        if self.app.current_user and self.app.current_user.get('role') == ROLE_ADMIN:
            admin_tabs = [
                {
                    'id': 'data_management',
                    'text': 'Data Mgmt',
                    'icon': '💾',
                    'command': lambda: self.app.show_data_management(),
                    'priority': 9,
                    'always_visible': False
                },
                {
                    'id': 'settings',
                    'text': 'Settings',
                    'icon': '⚙️',
                    'command': lambda: self.app.show_settings(),
                    'priority': 10,
                    'always_visible': False
                }
            ]
            main_tabs.extend(admin_tabs)
        
        # Sort by priority and create tabs
        main_tabs.sort(key=lambda x: x['priority'])
        
        # Create tabs
        for tab_info in main_tabs:
            if self._should_show_tab(tab_info):
                self.create_tab(tab_info)
        
        # Add more button
        self.create_more_button()
    
    def _should_show_tab(self, tab_info):
        """Determine if a tab should be shown based on visibility settings"""
        # For now, show all tabs that are always visible
        # This can be extended for role-based access control
        return tab_info['always_visible'] or True  # Temporary: show all tabs
    
    def create_tab(self, tab_info):
        """Create a single tab button"""
        tab_id = tab_info['id']
        tab_text = f"{tab_info['icon']} {tab_info['text']}"
        
        # Create tab button
        tab_button = ttk.Button(
            self.tab_container,
            text=tab_text,
            command=tab_info['command'],
            style="TabNav.TButton"
        )
        
        # Add hover effects
        tab_button.bind('<Enter>', lambda e: self._on_tab_enter(e, tab_button))
        tab_button.bind('<Leave>', lambda e: self._on_tab_leave(e, tab_button))
        
        # Add right-click context menu
        tab_button.bind('<Button-3>', lambda e: self._show_tab_context_menu(e, tab_info))
        
        # Pack the tab
        tab_button.pack(side=tk.LEFT, padx=(2, 1), fill=tk.X, expand=True)
        
        # Store tab info
        self.tabs[tab_id] = {
            'button': tab_button,
            'info': tab_info,
            'container': self.tab_container
        }
        
        return tab_button
    
    def create_more_button(self):
        """Create the 'More' dropdown button for additional tabs"""
        self.more_button = ttk.Button(
            self.tab_container,
            text="⋮ More",
            command=self._show_more_menu,
            style="AddTab.TButton"
        )
        self.more_button.pack(side=tk.RIGHT, padx=(10, 2))
        
        # Create more menu (initially hidden)
        self.more_menu = tk.Menu(self.tab_container, tearoff=0)
        
        # Populate more menu with tabs that aren't shown
        more_tabs = []
        for tab_id, tab_data in self.tabs.items():
            if tab_id not in ['dashboard', 'new_order', 'orders', 'menu', 'tables']:
                tab_info = tab_data['info']
                more_tabs.append(tab_info)
        
        # Sort by priority
        more_tabs.sort(key=lambda x: x['priority'])
        
        # Add menu items
        for tab_info in more_tabs:
            self.more_menu.add_command(
                label=f"{tab_info['icon']} {tab_info['text']}",
                command=tab_info['command']
            )
    
    def _show_more_menu(self):
        """Show the more dropdown menu"""
        try:
            x = self.more_button.winfo_rootx()
            y = self.more_button.winfo_rooty() + self.more_button.winfo_height()
            self.more_menu.post(x, y)
        except Exception as e:
            print(f"Error showing more menu: {e}")
    
    def _on_tab_enter(self, event, tab_button):
        """Handle tab hover enter"""
        if tab_button.cget('style') == 'TabNav.TButton':
            tab_button.configure(style="TabNav.Hover.TButton")
    
    def _on_tab_leave(self, event, tab_button):
        """Handle tab hover leave"""
        if tab_button.cget('style') == 'TabNav.Hover.TButton':
            tab_button.configure(style="TabNav.TButton")
    
    def _show_tab_context_menu(self, event, tab_info):
        """Show context menu for a tab"""
        try:
            context_menu = tk.Menu(self.tab_container, tearoff=0)
            
            context_menu.add_command(
                label=f"Switch to {tab_info['text']}",
                command=tab_info['command']
            )
            
            # Add separator
            context_menu.add_separator()
            
            context_menu.add_command(
                label="Close Tab",
                command=lambda: self.close_tab(tab_info['id'])
            )
            
            # Show menu at cursor position
            x = event.x_root
            y = event.y_root
            context_menu.post(x, y)
            
        except Exception as e:
            print(f"Error showing context menu: {e}")
    
    def set_active_tab(self, tab_id):
        """Set the active tab and update styling"""
        # Clear previous active tab styling
        if self.active_tab_id and self.active_tab_id in self.tabs:
            old_tab = self.tabs[self.active_tab_id]
            old_tab['button'].configure(style="TabNav.TButton")
        
        # Set new active tab styling
        if tab_id and tab_id in self.tabs:
            new_tab = self.tabs[tab_id]
            new_tab['button'].configure(style="ActiveTabNav.TButton")
            self.active_tab_id = tab_id
        else:
            self.active_tab_id = None
    
    def close_tab(self, tab_id):
        """Close a tab and update the UI"""
        if tab_id in self.tabs:
            tab_data = self.tabs[tab_id]
            
            # Remove the button
            tab_data['button'].destroy()
            
            # Remove from tabs dictionary
            del self.tabs[tab_id]
            
            # If closing the active tab, switch to another tab
            if self.active_tab_id == tab_id:
                # Find another tab to activate
                if self.tabs:
                    first_tab_id = list(self.tabs.keys())[0]
                    self.set_active_tab(first_tab_id)
                    # Trigger the command for the first tab
                    if first_tab_id in self.tabs:
                        self.tabs[first_tab_id]['info']['command']()
                else:
                    self.active_tab_id = None
    
    def get_active_tab_id(self):
        """Get the ID of the currently active tab"""
        return self.active_tab_id
    
    def add_tab(self, tab_id, tab_info):
        """Add a new tab dynamically"""
        if tab_id not in self.tabs:
            self.create_tab(tab_info)
            # Update more menu if needed
            self._update_more_menu()
    
    def remove_tab(self, tab_id):
        """Remove a tab dynamically"""
        if tab_id in self.tabs:
            self.close_tab(tab_id)
            self._update_more_menu()
    
    def _update_more_menu(self):
        """Update the more menu based on visible tabs"""
        # Clear existing menu items
        self.more_menu.delete(0, tk.END)
        
        # Rebuild menu with tabs that aren't visible
        # For now, just show static content
        # This can be enhanced later
        hidden_tabs = []
        for tab_id, tab_data in self.tabs.items():
            if tab_id not in ['dashboard', 'new_order', 'orders', 'menu', 'tables']:
                hidden_tabs.append(tab_data['info'])
        
        # Add menu items
        for tab_info in hidden_tabs:
            self.more_menu.add_command(
                label=f"{tab_info['icon']} {tab_info['text']}",
                command=tab_info['command']
            )
    
    def refresh_tabs(self):
        """Refresh tab display (e.g., after user role changes)"""
        # Clear existing tabs
        for tab_data in self.tabs.values():
            tab_data['button'].destroy()
        self.tabs.clear()
        
        # Recreate tabs
        self.create_main_tabs()
        
        # Reset active tab
        self.set_active_tab(None)
    
    def cleanup(self):
        """Clean up resources when component is destroyed"""
        # Destroy all tab buttons
        for tab_data in self.tabs.values():
            if tab_data['button'].winfo_exists():
                tab_data['button'].destroy()
        
        # Destroy more button and menu
        if hasattr(self, 'more_button') and self.more_button.winfo_exists():
            self.more_button.destroy()
        
        if hasattr(self, 'more_menu'):
            self.more_menu.destroy()
        
        self.tabs.clear()
