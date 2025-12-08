import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .base_ui import BaseUI

class TablesScreen(BaseUI):
    """Tables management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup tables management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Table Management", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.app.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("Add Table", self.add_table),
            ("Edit Table", self.edit_table),
            ("Delete Table", self.delete_table),
            ("Reset All Tables", self.reset_all_tables)
        ])
        
        # Tables frame
        tables_frame = ttk.Frame(self.app.content_frame)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create table grid
        self.table_buttons_frame = ttk.Frame(tables_frame)
        self.table_buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load tables
        self.load_tables_grid()
    
    def load_tables_grid(self):
        """Load tables in grid view"""
        # Clear existing widgets
        for widget in self.table_buttons_frame.winfo_children():
            widget.destroy()
        
        # Get tables
        tables = self.app.table_model.get_all()
        
        # Create table buttons in grid
        rows = 3
        cols = 4
        
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            
            row = i // cols
            col = i % cols
            
            # Create frame for table
            table_frame = ttk.Frame(self.table_buttons_frame, relief=tk.RAISED, borderwidth=2)
            table_frame.grid(row=row, column=col, padx=10, pady=10, sticky=tk.W+tk.E)
            
            # Table number
            table_label = ttk.Label(table_frame, text=table_number, font=('Arial', 14, 'bold'))
            table_label.pack(pady=5)
            
            # Table capacity
            capacity_label = ttk.Label(table_frame, text=f"Capacity: {capacity}")
            capacity_label.pack()
            
            # Table status
            status_label = ttk.Label(table_frame, text=status)
            status_label.pack(pady=5)
            
            # Set color based on status
            if status == "Available":
                table_frame.configure(style="Available.TFrame")
                status_label.configure(foreground="green")
            else:  # Occupied
                table_frame.configure(style="Occupied.TFrame")
                status_label.configure(foreground="red")
            
            # Add click event to toggle status
            def toggle_status(event, tid=table_id, tnum=table_number):
                # Get current status
                tables = self.app.table_model.get_all()
                current_status = None
                for t in tables:
                    if t[0] == tid:
                        current_status = t[3]
                        break
                
                # Toggle status
                new_status = "Occupied" if current_status == "Available" else "Available"
                
                # Update status
                self.app.table_model.update_status(tid, new_status)
                
                # Reload tables
                self.load_tables_grid()
                
                # Show message
                self.show_message("Table Status", f"Table {tnum} status changed to {new_status}", "info")
            
            table_frame.bind("<Button-1>", toggle_status)
            table_label.bind("<Button-1>", toggle_status)
            capacity_label.bind("<Button-1>", toggle_status)
            status_label.bind("<Button-1>", toggle_status)
    
    def add_table(self):
        """Add a new table"""
        # Create add table window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add Table")
        add_window.geometry("300x200")
        
        # Create form
        form_frame = ttk.Frame(add_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table number
        ttk.Label(form_frame, text="Table Number:").grid(row=0, column=0, sticky=tk.W, pady=10)
        table_number_entry = ttk.Entry(form_frame, width=30)
        table_number_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Capacity
        ttk.Label(form_frame, text="Capacity:").grid(row=1, column=0, sticky=tk.W, pady=10)
        capacity_entry = ttk.Entry(form_frame, width=30)
        capacity_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        def save_table():
            table_number = table_number_entry.get().strip()
            capacity = capacity_entry.get().strip()
            
            if not table_number or not capacity:
                self.show_message("Warning", "Please fill in all fields", "warning")
                return
            
            try:
                capacity = int(capacity)
            except ValueError:
                self.show_message("Warning", "Capacity must be a number", "warning")
                return
            
            # Insert table
            success = self.app.table_model.add(table_number, capacity)
            
            if success:
                self.show_message("Success", "Table added successfully", "info")
                add_window.destroy()
                self.load_tables_grid()
            else:
                self.show_message("Error", "Table number already exists", "error")
        
        self.create_button_frame(buttons_frame, [
            ("Save", save_table),
            ("Cancel", add_window.destroy)
        ])
    
    def edit_table(self):
        """Edit selected table"""
        # Create select table window
        select_window = tk.Toplevel(self.app.root)
        select_window.title("Select Table to Edit")
        select_window.geometry("300x400")
        
        # Create form
        form_frame = ttk.Frame(select_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Select Table:").pack(anchor=tk.W, pady=5)
        
        # Table list
        table_listbox = tk.Listbox(form_frame, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load tables
        tables = self.app.table_model.get_all()
        
        table_data = {} # To store table info by index
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            table_listbox.insert(tk.END, f"{table_number} (Capacity: {capacity}, Status: {status})")
            table_data[i] = table

        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        def select_table_to_edit():
            selection = table_listbox.curselection()
            if not selection:
                self.show_message("Warning", "Please select a table", "warning")
                return
            
            index = selection[0]
            table_id, table_number, capacity, status = table_data[index]
            
            # Close select window
            select_window.destroy()
            
            # Create edit table window
            edit_window = tk.Toplevel(self.app.root)
            edit_window.title("Edit Table")
            edit_window.geometry("300x250")
            
            # Create form
            edit_form_frame = ttk.Frame(edit_window, padding="20")
            edit_form_frame.pack(fill=tk.BOTH, expand=True)
            
            # Table number
            ttk.Label(edit_form_frame, text="Table Number:").grid(row=0, column=0, sticky=tk.W, pady=10)
            table_number_entry = ttk.Entry(edit_form_frame, width=30)
            table_number_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10)
            table_number_entry.insert(0, table_number)
            
            # Capacity
            ttk.Label(edit_form_frame, text="Capacity:").grid(row=1, column=0, sticky=tk.W, pady=10)
            capacity_entry = ttk.Entry(edit_form_frame, width=30)
            capacity_entry.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10)
            capacity_entry.insert(0, str(capacity))
            
            # Status
            ttk.Label(edit_form_frame, text="Status:").grid(row=2, column=0, sticky=tk.W, pady=10)
            status_var = tk.StringVar(value=status)
            status_combo = ttk.Combobox(edit_form_frame, textvariable=status_var, values=["Available", "Occupied"], state="readonly", width=28)
            status_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=10)

            # Buttons
            edit_buttons_frame = ttk.Frame(edit_form_frame)
            edit_buttons_frame.grid(row=3, column=0, columnspan=2, pady=10)
            
            def update_table():
                new_table_number = table_number_entry.get().strip()
                new_capacity = capacity_entry.get().strip()
                new_status = status_var.get()
                
                if not new_table_number or not new_capacity:
                    self.show_message("Warning", "Please fill in all fields", "warning")
                    return
                
                try:
                    new_capacity = int(new_capacity)
                except ValueError:
                    self.show_message("Warning", "Capacity must be a number", "warning")
                    return
                
                # Update table
                success = self.app.table_model.update(table_id, new_table_number, new_capacity, new_status)
                
                if success:
                    self.show_message("Success", "Table updated successfully", "info")
                    edit_window.destroy()
                    self.load_tables_grid()
                else:
                    self.show_message("Error", "Table number already exists", "error")
            
            self.create_button_frame(edit_buttons_frame, [
                ("Update", update_table),
                ("Cancel", edit_window.destroy)
            ])

        self.create_button_frame(buttons_frame, [
            ("Edit", select_table_to_edit),
            ("Cancel", select_window.destroy)
        ])

    def delete_table(self):
        """Delete selected table"""
        # Create select table window
        select_window = tk.Toplevel(self.app.root)
        select_window.title("Select Table to Delete")
        select_window.geometry("300x400")
        
        # Create form
        form_frame = ttk.Frame(select_window, padding="20")
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(form_frame, text="Select Table:").pack(anchor=tk.W, pady=5)
        
        # Table list
        table_listbox = tk.Listbox(form_frame, height=10)
        table_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Load tables
        tables = self.app.table_model.get_all()
        
        table_data = {}
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            table_listbox.insert(tk.END, f"{table_number}")
            table_data[i] = {'id': table_id, 'name': table_number}

        # Buttons
        buttons_frame = ttk.Frame(form_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        def select_table_to_delete():
            selection = table_listbox.curselection()
            if not selection:
                self.show_message("Warning", "Please select a table", "warning")
                return
            
            index = selection[0]
            table_id = table_data[index]['id']
            table_name = table_data[index]['name']

            # Confirm deletion
            if self.show_message("Confirm Delete", f"Are you sure you want to delete {table_name}? This action cannot be undone.", "yesno"):
                # Delete table
                self.app.table_model.delete(table_id)
                
                self.show_message("Success", "Table deleted successfully", "info")
                select_window.destroy()
                self.load_tables_grid()

        self.create_button_frame(buttons_frame, [
            ("Delete", select_table_to_delete),
            ("Cancel", select_window.destroy)
        ])

    def reset_all_tables(self):
        """Reset status of all tables to Available"""
        if self.show_message("Confirm Reset", "Are you sure you want to reset all tables to 'Available'?", "yesno"):
            self.app.table_model.reset_all()
            self.show_message("Success", "All tables have been reset to 'Available'", "info")
            self.load_tables_grid()
