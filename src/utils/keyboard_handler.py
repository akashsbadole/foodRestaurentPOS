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
        self.root.unbind('<Alt-d>')
        self.root.unbind('<Alt-D>')
        self.root.unbind('<Alt-n>')
        self.root.unbind('<Alt-N>')
        self.root.unbind('<Alt-o>')
        self.root.unbind('<Alt-O>')
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
        
        # Global shortcuts (Alt+key combinations)
        self.root.bind('<Alt-d>', lambda e: (self.app.show_dashboard(), self.show_keyboard_feedback("Dashboard")))
        self.root.bind('<Alt-D>', lambda e: (self.app.show_dashboard(), self.show_keyboard_feedback("Dashboard")))
        self.root.bind('<Alt-n>', lambda e: (self.app.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-N>', lambda e: (self.app.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('<Alt-o>', lambda e: (self.app.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('<Alt-O>', lambda e: (self.app.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('<Alt-m>', lambda e: (self.app.show_menu(), self.show_keyboard_feedback("Menu Management")))
        self.root.bind('<Alt-M>', lambda e: (self.app.show_menu(), self.show_keyboard_feedback("Menu Management")))
        self.root.bind('<Alt-t>', lambda e: (self.app.show_tables(), self.show_keyboard_feedback("Table Management")))
        self.root.bind('<Alt-T>', lambda e: (self.app.show_tables(), self.show_keyboard_feedback("Table Management")))
        self.root.bind('<Alt-i>', lambda e: (self.app.show_inventory(), self.show_keyboard_feedback("Inventory")))
        self.root.bind('<Alt-I>', lambda e: (self.app.show_inventory(), self.show_keyboard_feedback("Inventory")))
        self.root.bind('<Alt-k>', lambda e: (self.app.show_kot(), self.show_keyboard_feedback("KOT")))
        self.root.bind('<Alt-K>', lambda e: (self.app.show_kot(), self.show_keyboard_feedback("KOT")))
        self.root.bind('<Alt-r>', lambda e: (self.app.show_reports(), self.show_keyboard_feedback("Reports")))
        self.root.bind('<Alt-R>', lambda e: (self.app.show_reports(), self.show_keyboard_feedback("Reports")))
        
        # Settings shortcut (Admin only)
        if self.app.current_user and self.app.current_user['role'] == 'Admin':
            self.root.bind('<Alt-s>', lambda e: (self.app.show_settings(), self.show_keyboard_feedback("Settings")))
            self.root.bind('<Alt-S>', lambda e: (self.app.show_settings(), self.show_keyboard_feedback("Settings")))
        
        # Logout shortcut
        self.root.bind('<Alt-l>', lambda e: (self.app.logout(), self.show_keyboard_feedback("Logout")))
        self.root.bind('<Alt-L>', lambda e: (self.app.logout(), self.show_keyboard_feedback("Logout")))
        
        # Help shortcut
        self.root.bind('<F1>', lambda e: (self.show_keyboard_shortcuts_help(), self.show_keyboard_feedback("Help")))
    
    def setup_dashboard_shortcuts(self):
        """Set up dashboard numeric key shortcuts"""
        # Clear any existing bindings
        self.root.unbind('1')
        self.root.unbind('2')
        self.root.unbind('3')
        
        # Dashboard shortcuts (numeric keys)
        self.root.bind('1', lambda e: (self.app.show_new_order(), self.show_keyboard_feedback("New Order")))
        self.root.bind('2', lambda e: (self.app.show_orders(), self.show_keyboard_feedback("Orders")))
        self.root.bind('3', lambda e: (self.app.show_menu(), self.show_keyboard_feedback("Menu Management")))
    
    def setup_order_screen_shortcuts(self):
        """Set up order screen specific shortcuts"""
        # Clear any existing bindings
        self.root.unbind('<F1>')
        self.root.unbind('<F2>')
        self.root.unbind('<F3>')
        self.root.unbind('<F4>')
        self.root.unbind('<F5>')
        self.root.unbind('<Control-Return>')
        
        # Order screen shortcuts
        self.root.bind('<F1>', lambda e: (self.app.add_to_cart(), self.show_keyboard_feedback("Add to Cart")))
        self.root.bind('<F2>', lambda e: (self.app.update_cart_quantity(), self.show_keyboard_feedback("Update Quantity")))
        self.root.bind('<F3>', lambda e: (self.app.remove_from_cart(), self.show_keyboard_feedback("Remove from Cart")))
        self.root.bind('<F4>', lambda e: (self.app.clear_cart(), self.show_keyboard_feedback("Clear Cart")))
        self.root.bind('<F5>', lambda e: (self.app.load_menu_items(), self.show_keyboard_feedback("Refresh Menu")))
        self.root.bind('<Control-Return>', lambda e: (self.app.process_payment("Cash"), self.show_keyboard_feedback("Process Payment")))
    
    def enhance_treeview_navigation(self, treeview):
        """Enhance treeview with better keyboard navigation"""
        def on_tree_key_press(event):
            if event.keysym == 'Return':
                # Trigger default action based on current screen
                self.handle_treeview_enter_key(treeview)
            elif event.keysym == 'Delete':
                # Trigger delete action if applicable
                self.handle_treeview_delete_key(treeview)
        
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
        elif hasattr(self.app, 'inventory_tree') and treeview == self.app.inventory_tree:
            self.app.update_stock()
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
        """Setup improved form navigation with Enter and Escape keys"""
        def on_form_key_press(event):
            if event.keysym == 'Return':
                # Find the next widget to focus
                widget = event.widget
                next_widget = parent_frame.tk_focusNext().focus_get()
                if next_widget:
                    next_widget.focus()
                    self.show_keyboard_feedback("Next Field")
                else:
                    # If no next widget, try to submit form
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
        ALT + D: Dashboard
        ALT + N: New Order
        ALT + O: Orders
        ALT + M: Menu Management
        ALT + T: Table Management
        ALT + I: Inventory
        ALT + K: KOT (Kitchen Order Tickets)
        ALT + R: Reports
        ALT + S: Settings (Admin only)
        ALT + L: Logout
        F1: Show this help dialog
        """
        
        global_label = ttk.Label(global_frame, text=global_text, justify=tk.LEFT)
        global_label.pack(anchor=tk.W)
        
        # Dashboard shortcuts tab
        dashboard_frame = ttk.Frame(notebook, padding="10")
        notebook.add(dashboard_frame, text="Dashboard")
        
        dashboard_text = """
        1: New Order
        2: View Orders
        3: Menu Management
        """
        
        dashboard_label = ttk.Label(dashboard_frame, text=dashboard_text, justify=tk.LEFT)
        dashboard_label.pack(anchor=tk.W)
        
        # Order screen shortcuts tab
        order_frame = ttk.Frame(notebook, padding="10")
        notebook.add(order_frame, text="Order Screen")
        
        order_text = """
        F1: Add to Cart
        F2: Update Quantity
        F3: Remove from Cart
        F4: Clear Cart
        F5: Refresh Menu
        Ctrl + Enter: Process Payment (Cash)
        """
        
        order_label = ttk.Label(order_frame, text=order_text, justify=tk.LEFT)
        order_label.pack(anchor=tk.W)
        
        # Treeview navigation tab
        treeview_frame = ttk.Frame(notebook, padding="10")
        notebook.add(treeview_frame, text="Treeview Navigation")
        
        treeview_text = """
        Enter: Trigger default action (view details, edit, etc.)
        Delete: Delete selected item where applicable
        Arrow Keys: Navigate between items
        Tab: Move between fields/sections
        """
        
        treeview_label = ttk.Label(treeview_frame, text=treeview_text, justify=tk.LEFT)
        treeview_label.pack(anchor=tk.W)
        
        # Form navigation tab
        form_frame = ttk.Frame(notebook, padding="10")
        notebook.add(form_frame, text="Form Navigation")
        
        form_text = """
        Enter: Move to next field or submit form
        Escape: Cancel dialog/close window
        Tab: Move between form fields
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
