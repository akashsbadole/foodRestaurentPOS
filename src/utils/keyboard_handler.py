import tkinter as tk
from tkinter import ttk

class KeyboardHandler:
    """Handle keyboard shortcuts for the application"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        
    def setup_global_keyboard_shortcuts(self):
        """Set up global keyboard shortcuts for the application"""
        # Clear any existing bindings
        self.root.unbind('<Alt-n>')
        self.root.unbind('<Alt-N>')
        self.root.unbind('<Alt-o>')
        self.root.unbind('<Alt-O>')
        self.root.unbind('<Alt-d>')
        self.root.unbind('<Alt-D>')
        self.root.unbind('<Alt-m>')
        self.root.unbind('<Alt-M>')
        self.root.unbind('<Alt-t>')
        self.root.unbind('<Alt-T>')
        self.root.unbind('<Alt-i>')
        self.root.unbind('<Alt-I>')
        self.root.unbind('<Alt-k>')
        self.root.unbind('<Alt-K>')
        self.root.unbind('<Alt-r>')
        self.root.unbind('<Alt-R>')
        self.root.unbind('<Alt-s>')
        self.root.unbind('<Alt-S>')
        self.root.unbind('<Alt-l>')
        self.root.unbind('<Alt-L>')
        self.root.unbind('<F1>')
        
        # Essential global shortcuts only
        self.root.bind('<Alt-n>', lambda e: (self.app.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-N>', lambda e: (self.app.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-o>', lambda e: (self.app.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('<Alt-O>', lambda e: (self.app.show_orders(), self.show_keyboard_feedback("Orders")))
        
        # Help shortcut
        self.root.bind('<F1>', lambda e: (self.show_keyboard_shortcuts_help(), self.show_keyboard_feedback("Help")))
    
    def setup_dashboard_shortcuts(self):
        """Set up dashboard numeric key shortcuts - DISABLED"""
        # Clear any existing bindings
        self.root.unbind('1')
        self.root.unbind('2')
        self.root.unbind('3')
        
        # Dashboard numeric shortcuts removed - only mouse interaction allowed
        pass
    
    def setup_order_screen_shortcuts(self):
        """Set up order screen specific shortcuts - DISABLED"""
        # Clear any existing bindings
        self.root.unbind('<F1>')
        self.root.unbind('<F2>')
        self.root.unbind('<F3>')
        self.root.unbind('<F4>')
        self.root.unbind('<F5>')
        self.root.unbind('<Control-Return>')
        
        # Order screen shortcuts removed - only mouse interaction allowed
        # Enter key functionality is preserved through treeview and form navigation
        pass
    
    def enhance_treeview_navigation(self, treeview):
        """Enhance treeview with limited keyboard navigation - Enter key only"""
        def on_tree_key_press(event):
            if event.keysym == 'Return':
                # Trigger default action based on current screen
                self.handle_treeview_enter_key(treeview)
            # Delete key functionality removed
        
        treeview.bind('<KeyRelease>', on_tree_key_press)
    
    def handle_treeview_enter_key(self, treeview):
        """Handle Enter key press on treeview"""
        selection = treeview.selection()
        if not selection:
            return
        
        # Determine current screen and trigger appropriate action
        if hasattr(self.app, 'orders_tree') and treeview == self.app.orders_tree:
            self.app.view_order_details()
            self.show_keyboard_feedback("View Order Details")
        elif hasattr(self.app, 'menu_items_tree') and treeview == self.app.menu_items_tree:
            self.app.edit_menu_item()
            self.show_keyboard_feedback("Edit Menu Item")
        elif hasattr(self.app, 'categories_tree') and treeview == self.app.categories_tree:
            self.app.edit_category()
            self.show_keyboard_feedback("Edit Category")
        elif (hasattr(self.app, 'current_screen') and
              hasattr(self.app.current_screen, 'inventory_tree') and
              treeview == self.app.current_screen.inventory_tree):
            # Check if current screen is inventory screen and has update_stock method
            if hasattr(self.app.current_screen, 'update_stock'):
                self.app.current_screen.update_stock()
                self.show_keyboard_feedback("Update Stock")
        elif hasattr(self.app, 'kot_tree') and treeview == self.app.kot_tree:
            # Toggle between statuses
            if self.app.kot_filter_var.get() == "Pending":
                self.app.mark_kot_preparing()
                self.show_keyboard_feedback("Mark as Preparing")
            else:
                self.app.mark_kot_completed()
                self.show_keyboard_feedback("Mark as Completed")
    
    def handle_treeview_delete_key(self, treeview):
        """Handle Delete key press on treeview"""
        selection = treeview.selection()
        if not selection:
            return
        
        # Determine current screen and trigger appropriate delete action
        if hasattr(self.app, 'menu_items_tree') and treeview == self.app.menu_items_tree:
            self.app.delete_menu_item()
            self.show_keyboard_feedback("Delete Menu Item")
        elif hasattr(self.app, 'categories_tree') and treeview == self.app.categories_tree:
            self.app.delete_category()
            self.show_keyboard_feedback("Delete Category")
    
    def setup_form_navigation(self, parent_frame):
        """Setup basic form navigation with Enter and Escape keys only"""
        def on_form_key_press(event):
            if event.keysym == 'Return':
                # Try to submit form directly (no field navigation)
                self.try_submit_form(parent_frame)
                self.show_keyboard_feedback("Submit Form")
            elif event.keysym == 'Escape':
                # Try to cancel/close dialog
                self.try_cancel_dialog(parent_frame)
                self.show_keyboard_feedback("Cancel Dialog")
        
        # Bind to all entry widgets in the form
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Entry):
                widget.bind('<KeyRelease>', on_form_key_press)
    
    def try_submit_form(self, parent_frame):
        """Try to submit the current form"""
        # Look for a save/submit button in the parent frame
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        button_text = child.cget('text').lower()
                        if 'save' in button_text or 'submit' in button_text or 'login' in button_text:
                            child.invoke()
                            return
    
    def try_cancel_dialog(self, parent_frame):
        """Try to cancel/close the current dialog"""
        # Look for a cancel button in the parent frame
        for widget in parent_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        button_text = child.cget('text').lower()
                        if 'cancel' in button_text:
                            child.invoke()
                            return
        
        # If no cancel button found, try to close the window
        try:
            parent_frame.winfo_toplevel().destroy()
        except:
            pass
    
    def show_keyboard_shortcuts_help(self):
        """Show keyboard shortcuts help dialog"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Keyboard Shortcuts Help")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        # Create notebook for different sections
        notebook = ttk.Notebook(help_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Global shortcuts tab
        global_frame = ttk.Frame(notebook, padding="10")
        notebook.add(global_frame, text="Global Shortcuts")
        
        global_text = """
        ALT + N: New Order
        ALT + O: Orders List
        F1: Show this help dialog
        
        Note: Most keyboard shortcuts have been removed to simplify the interface.
        Only essential shortcuts are preserved for navigation.
        """
        
        global_label = ttk.Label(global_frame, text=global_text, justify=tk.LEFT)
        global_label.pack(anchor=tk.W)
        
        # Dashboard shortcuts tab
        dashboard_frame = ttk.Frame(notebook, padding="10")
        notebook.add(dashboard_frame, text="Dashboard")
        
        dashboard_text = """
        No keyboard shortcuts available on dashboard.
        Please use the mouse to navigate.
        """
        
        dashboard_label = ttk.Label(dashboard_frame, text=dashboard_text, justify=tk.LEFT)
        dashboard_label.pack(anchor=tk.W)
        
        # Order screen shortcuts tab
        order_frame = ttk.Frame(notebook, padding="10")
        notebook.add(order_frame, text="Order Screen")
        
        order_text = """
        No keyboard shortcuts available on order screen.
        Please use the mouse to interact with the order form.
        Enter key can be used for form submission.
        """
        
        order_label = ttk.Label(order_frame, text=order_text, justify=tk.LEFT)
        order_label.pack(anchor=tk.W)
        
        # Treeview navigation tab
        treeview_frame = ttk.Frame(notebook, padding="10")
        notebook.add(treeview_frame, text="Treeview Navigation")
        
        treeview_text = """
        Enter: Trigger default action (view details, edit, etc.)
        
        Note: Navigation and delete shortcuts have been removed.
        Please use the mouse for most interactions.
        """
        
        treeview_label = ttk.Label(treeview_frame, text=treeview_text, justify=tk.LEFT)
        treeview_label.pack(anchor=tk.W)
        
        # Form navigation tab
        form_frame = ttk.Frame(notebook, padding="10")
        notebook.add(form_frame, text="Form Navigation")
        
        form_text = """
        Enter: Submit form
        Escape: Cancel dialog/close window
        
        Note: Field navigation shortcuts have been removed.
        Please use the mouse or Tab key to move between fields.
        """
        
        form_label = ttk.Label(form_frame, text=form_text, justify=tk.LEFT)
        form_label.pack(anchor=tk.W)
        
        # Close button
        close_button = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_button.pack(pady=10)
        
        # Center the window
        help_window.transient(self.root)
        help_window.grab_set()
    
    def show_keyboard_feedback(self, action):
        """Show visual feedback for keyboard shortcut action"""
        if hasattr(self.app, 'status_bar') and self.app.status_bar:
            try:
                # Update status bar with action
                self.app.status_bar.config(text=f"Keyboard shortcut: {action}")
                # Schedule clearing the status after 2 seconds
                self.root.after(2000, lambda: self.safe_update_status_bar("Ready"))
            except tk.TclError:
                # Status bar widget may have been destroyed
                pass
    
    def safe_update_status_bar(self, text):
        """Safely update status bar, handling case where widget might be destroyed"""
        try:
            if hasattr(self.app, 'status_bar') and self.app.status_bar:
                self.app.status_bar.config(text=text)
        except tk.TclError:
            # Status bar widget may have been destroyed
            pass
