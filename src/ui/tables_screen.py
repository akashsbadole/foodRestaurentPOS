import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from .base_ui import BaseUI
from utils.constants import *

class TablesScreen(BaseUI):
    """Tables management screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        # Configure modern styles
        self.configure_styles()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup tables management UI with modern design"""
        # Set main background - use style configuration for ttk.Frame
        try:
            self.app.content_frame.configure(background=COLOR_BACKGROUND_LIGHT)
        except tk.TclError:
            # If it's a ttk.Frame, use style configuration
            style = ttk.Style()
            style.configure("TablesScreen.TFrame", background=COLOR_BACKGROUND_LIGHT)
            self.app.content_frame.configure(style="TablesScreen.TFrame")
        
        # Main container with padding
        main_container = self.create_modern_frame(
            self.app.content_frame, 
            style="Card.TFrame", 
            padding=SPACING_L
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Title section
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, SPACING_L))
        
        title_label = self.create_modern_label(
            title_frame, 
            "Table Management", 
            style="Title.TLabel"
        )
        title_label.pack(side=tk.LEFT)
        
        # Subtitle
        subtitle_label = self.create_modern_label(
            title_frame, 
            "Manage restaurant tables and track their status", 
            style="Small.TLabel"
        )
        subtitle_label.pack(side=tk.LEFT, padx=(SPACING_S, 0))
        
        # Action buttons section
        self.create_button_group(main_container, [
            ("Add Table", self.add_table, "Success.TButton"),
            ("Edit Table", self.edit_table, "Primary.TButton"),
            ("Delete Table", self.delete_table, "Danger.TButton"),
            ("Reset All Tables", self.reset_all_tables, "Secondary.TButton")
        ])
        
        # Separator
        self.create_separator(main_container, orient=tk.HORIZONTAL, padding=SPACING_M)
        
        # Tables grid container with scrollable area
        tables_container = self.create_modern_frame(
            main_container, 
            style="Card.TFrame", 
            padding=SPACING_M
        )
        tables_container.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame for tables
        canvas = tk.Canvas(tables_container, background=COLOR_BACKGROUND_LIGHT, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tables_container, orient="vertical", command=canvas.yview)
        self.table_buttons_frame = ttk.Frame(canvas, style="Card.TFrame")
        
        self.table_buttons_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.table_buttons_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configure table card styles
        self._configure_table_card_styles()
        
        # Load tables
        self.load_tables_grid()
    
    def _configure_table_card_styles(self):
        """Configure specific styles for table cards"""
        style = ttk.Style()
        
        # Table card styles for different statuses
        style.configure("TableCard.Available.TFrame",
                       background=COLOR_SUCCESS_LIGHT,
                       borderwidth=2,
                       relief='solid',
                       bordercolor=COLOR_SUCCESS)
        
        style.configure("TableCard.Occupied.TFrame",
                       background=COLOR_ERROR_LIGHT,
                       borderwidth=2,
                       relief='solid',
                       bordercolor=COLOR_ERROR)
        
        style.configure("TableCard.Reserved.TFrame",
                       background=COLOR_WARNING_LIGHT,
                       borderwidth=2,
                       relief='solid',
                       bordercolor=COLOR_WARNING)
        
        # Table number label style
        style.configure("TableNumber.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_PRIMARY_DARK,
                       font=(FONT_FAMILY_PRIMARY, 20, 'bold'))
        
        # Table capacity label style
        style.configure("TableCapacity.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       font=(FONT_FAMILY_PRIMARY, 12, 'medium'))
        
        # Table status label style
        style.configure("TableStatus.TLabel",
                       font=(FONT_FAMILY_PRIMARY, 11, 'bold'))
        
        style.configure("TableStatus.Available.TLabel",
                       background=COLOR_SUCCESS_LIGHT,
                       foreground=COLOR_SUCCESS,
                       font=(FONT_FAMILY_PRIMARY, 11, 'bold'))
        
        style.configure("TableStatus.Occupied.TLabel",
                       background=COLOR_ERROR_LIGHT,
                       foreground=COLOR_ERROR,
                       font=(FONT_FAMILY_PRIMARY, 11, 'bold'))
        
        style.configure("TableStatus.Reserved.TLabel",
                       background=COLOR_WARNING_LIGHT,
                       foreground=COLOR_WARNING,
                       font=(FONT_FAMILY_PRIMARY, 11, 'bold'))
    
    def load_tables_grid(self):
        """Load tables in modern grid view with card-based design"""
        # Clear existing widgets
        for widget in self.table_buttons_frame.winfo_children():
            widget.destroy()
        
        # Get tables
        tables = self.app.table_model.get_all()
        
        if not tables:
            # Show empty state
            empty_frame = ttk.Frame(self.table_buttons_frame, style="Card.TFrame")
            empty_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_XXL)
            
            empty_label = self.create_modern_label(
                empty_frame,
                "No tables found. Click 'Add Table' to create your first table.",
                style="Body.TLabel"
            )
            empty_label.pack()
            return
        
        # Create table cards in responsive grid
        cols = 4  # Default columns
        card_size = 180  # Card size in pixels
        spacing = SPACING_M
        
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            
            row = i // cols
            col = i % cols
            
            # Create modern table card
            table_card = self._create_table_card(
                self.table_buttons_frame,
                table_id,
                table_number,
                capacity,
                status
            )
            
            # Grid layout with proper spacing
            table_card.grid(
                row=row, 
                column=col, 
                padx=spacing, 
                pady=spacing, 
                sticky=tk.W+tk.E+tk.N+tk.S
            )
        
        # Configure grid weights for responsiveness
        for col in range(cols):
            self.table_buttons_frame.columnconfigure(col, weight=1, minsize=card_size)
        
        for row in range((len(tables) + cols - 1) // cols):
            self.table_buttons_frame.rowconfigure(row, weight=1)
    
    def _create_table_card(self, parent, table_id, table_number, capacity, status):
        """Create a modern table card with enhanced visual design"""
        # Determine status style
        status_style = status.capitalize() if status in ["Available", "Occupied", "Reserved"] else "Available"
        
        # Main card container with shadow effect
        card_frame = ttk.Frame(parent, style=f"TableCard.{status_style}.TFrame")
        
        # Inner white content area
        content_frame = ttk.Frame(card_frame, style="Card.TFrame", padding=SPACING_M)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_XS, pady=SPACING_XS)
        
        # Table number (prominent)
        number_label = self.create_modern_label(
            content_frame,
            f"Table {table_number}",
            style="TableNumber.TLabel"
        )
        number_label.pack(pady=(0, SPACING_S))
        
        # Capacity information
        capacity_frame = ttk.Frame(content_frame, style="Card.TFrame")
        capacity_frame.pack(fill=tk.X, pady=(SPACING_XS, SPACING_S))
        
        capacity_icon = self.create_modern_label(
            capacity_frame,
            "👥",
            style="Body.TLabel"
        )
        capacity_icon.pack(side=tk.LEFT)
        
        capacity_label = self.create_modern_label(
            capacity_frame,
            f"Capacity: {capacity}",
            style="TableCapacity.TLabel"
        )
        capacity_label.pack(side=tk.LEFT, padx=(SPACING_XS, 0))
        
        # Status indicator with visual styling
        status_frame = ttk.Frame(content_frame, style=f"TableCard.{status_style}.TFrame")
        status_frame.pack(fill=tk.X, pady=(SPACING_S, 0))
        
        status_label = self.create_modern_label(
            status_frame,
            f"● {status}",
            style=f"TableStatus.{status_style}.TLabel"
        )
        status_label.pack(pady=SPACING_XS)
        
        # Add click event to toggle status with visual feedback
        def toggle_status(event, tid=table_id, tnum=table_number):
            # Get current status
            tables = self.app.table_model.get_all()
            current_status = None
            for t in tables:
                if t[0] == tid:
                    current_status = t[3]
                    break
            
            # Toggle status
            if current_status == "Available":
                new_status = "Occupied"
            elif current_status == "Occupied":
                new_status = "Reserved"
            else:
                new_status = "Available"
            
            # Update status
            self.app.table_model.update_status(tid, new_status)
            
            # Reload tables with animation effect
            self.load_tables_grid()
            
            # Show modern success message
            self.show_message("Table Status Updated", f"Table {tnum} status changed to {new_status}", "info")
        
        # Bind click events to all card elements
        for widget in [card_frame, content_frame, number_label, capacity_frame, status_frame]:
            widget.bind("<Button-1>", toggle_status)
            widget.bind("<Enter>", lambda e, w=card_frame: self._on_card_enter(e, w))
            widget.bind("<Leave>", lambda e, w=card_frame: self._on_card_leave(e, w))
        
        return card_frame
    
    def _on_card_enter(self, event, widget):
        """Handle card hover enter effect"""
        # Add visual feedback on hover
        widget.configure(relief='raised', borderwidth=3)
    
    def _on_card_leave(self, event, widget):
        """Handle card hover leave effect"""
        # Reset visual feedback
        widget.configure(relief='solid', borderwidth=2)
    
    def add_table(self):
        """Add a new table with modern dialog"""
        # Create modern add table window
        add_window = tk.Toplevel(self.app.root)
        add_window.title("Add New Table")
        add_window.geometry("400x300")
        add_window.configure(background=COLOR_BACKGROUND_LIGHT)
        add_window.resizable(False, False)
        
        # Center the window
        add_window.transient(self.app.root)
        add_window.grab_set()
        
        # Main container
        main_frame = self.create_modern_frame(
            add_window, 
            style="Card.TFrame", 
            padding=SPACING_L
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            main_frame,
            "Add New Table",
            style="SectionTitle.TLabel"
        )
        title_label.pack(pady=(0, SPACING_L))
        
        # Form fields
        form_frame = ttk.Frame(main_frame, style="Card.TFrame")
        form_frame.pack(fill=tk.X, pady=SPACING_M)
        
        # Table number field
        table_number_entry = self.create_form_field(
            form_frame,
            "Table Number:",
            entry_type="entry",
            style="Modern.TEntry",
            width=30
        )
        
        # Capacity field
        capacity_entry = self.create_form_field(
            form_frame,
            "Capacity:",
            entry_type="entry",
            style="Modern.TEntry",
            width=30
        )
        
        # Status field
        status_var = tk.StringVar(value="Available")
        status_combo = self.create_form_field(
            form_frame,
            "Status:",
            entry_type="combobox",
            textvariable=status_var,
            values=["Available", "Occupied", "Reserved"],
            style="Modern.TCombobox",
            width=28,
            state="readonly"
        )
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=SPACING_L)
        
        def save_table():
            table_number = table_number_entry.get().strip()
            capacity = capacity_entry.get().strip()
            status = status_var.get()
            
            if not table_number or not capacity:
                self.show_message("Validation Error", "Please fill in all required fields", "warning")
                return
            
            try:
                capacity = int(capacity)
                if capacity <= 0:
                    raise ValueError("Capacity must be positive")
            except ValueError:
                self.show_message("Validation Error", "Capacity must be a positive number", "warning")
                return
            
            # Insert table
            success = self.app.table_model.add(table_number, capacity)
            
            if success:
                self.show_message("Success", f"Table '{table_number}' added successfully", "info")
                add_window.destroy()
                self.load_tables_grid()
            else:
                self.show_message("Error", "Table number already exists", "error")
        
        def cancel_add():
            add_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Save Table", save_table, "Success.TButton"),
            ("Cancel", cancel_add, "Secondary.TButton")
        ])
        
        # Focus on first field
        table_number_entry.focus_set()
        add_window.bind("<Return>", lambda e: save_table())
        add_window.bind("<Escape>", lambda e: cancel_add())
    
    def edit_table(self):
        """Edit selected table with modern dialog"""
        # Create modern select table window
        select_window = tk.Toplevel(self.app.root)
        select_window.title("Select Table to Edit")
        select_window.geometry("450x500")
        select_window.configure(background=COLOR_BACKGROUND_LIGHT)
        select_window.resizable(False, False)
        
        # Center the window
        select_window.transient(self.app.root)
        select_window.grab_set()
        
        # Main container
        main_frame = self.create_modern_frame(
            select_window, 
            style="Card.TFrame", 
            padding=SPACING_L
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Title
        title_label = self.create_modern_label(
            main_frame,
            "Select Table to Edit",
            style="SectionTitle.TLabel"
        )
        title_label.pack(pady=(0, SPACING_M))
        
        # Table list with modern styling
        list_frame = self.create_modern_frame(
            main_frame, 
            style="Card.TFrame", 
            padding=SPACING_S
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
        
        # Create modern listbox with scrollbar
        table_listbox = tk.Listbox(
            list_frame,
            font=(FONT_FAMILY_PRIMARY, 11),
            background=COLOR_CARD_WHITE,
            foreground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_PRIMARY_LIGHT,
            selectforeground=COLOR_CARD_WHITE,
            borderwidth=1,
            relief='solid',
            highlightthickness=0,
            height=12
        )
        
        # Add scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=table_listbox.yview)
        table_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load tables
        tables = self.app.table_model.get_all()
        table_data = {}
        
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            display_text = f"Table {table_number} (Capacity: {capacity}, Status: {status})"
            table_listbox.insert(tk.END, display_text)
            table_data[i] = table
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=SPACING_M)
        
        def select_table_to_edit():
            selection = table_listbox.curselection()
            if not selection:
                self.show_message("Selection Required", "Please select a table to edit", "warning")
                return
            
            index = selection[0]
            table_id, table_number, capacity, status = table_data[index]
            
            # Close select window
            select_window.destroy()
            
            # Create modern edit table window
            edit_window = tk.Toplevel(self.app.root)
            edit_window.title("Edit Table")
            edit_window.geometry("400x350")
            edit_window.configure(background=COLOR_BACKGROUND_LIGHT)
            edit_window.resizable(False, False)
            
            # Center the window
            edit_window.transient(self.app.root)
            edit_window.grab_set()
            
            # Main container
            edit_main_frame = self.create_modern_frame(
                edit_window, 
                style="Card.TFrame", 
                padding=SPACING_L
            )
            edit_main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
            
            # Title
            edit_title_label = self.create_modern_label(
                edit_main_frame,
                f"Edit Table {table_number}",
                style="SectionTitle.TLabel"
            )
            edit_title_label.pack(pady=(0, SPACING_L))
            
            # Form fields
            edit_form_frame = ttk.Frame(edit_main_frame, style="Card.TFrame")
            edit_form_frame.pack(fill=tk.X, pady=SPACING_M)
            
            # Table number field
            edit_table_number_entry = self.create_form_field(
                edit_form_frame,
                "Table Number:",
                entry_type="entry",
                style="Modern.TEntry",
                width=30
            )
            edit_table_number_entry.insert(0, table_number)
            
            # Capacity field
            edit_capacity_entry = self.create_form_field(
                edit_form_frame,
                "Capacity:",
                entry_type="entry",
                style="Modern.TEntry",
                width=30
            )
            edit_capacity_entry.insert(0, str(capacity))
            
            # Status field
            edit_status_var = tk.StringVar(value=status)
            edit_status_combo = self.create_form_field(
                edit_form_frame,
                "Status:",
                entry_type="combobox",
                textvariable=edit_status_var,
                values=["Available", "Occupied", "Reserved"],
                style="Modern.TCombobox",
                width=28,
                state="readonly"
            )
            
            # Buttons
            edit_button_frame = ttk.Frame(edit_main_frame, style="Card.TFrame")
            edit_button_frame.pack(fill=tk.X, pady=SPACING_L)
            
            def update_table():
                new_table_number = edit_table_number_entry.get().strip()
                new_capacity = edit_capacity_entry.get().strip()
                new_status = edit_status_var.get()
                
                if not new_table_number or not new_capacity:
                    self.show_message("Validation Error", "Please fill in all required fields", "warning")
                    return
                
                try:
                    new_capacity = int(new_capacity)
                    if new_capacity <= 0:
                        raise ValueError("Capacity must be positive")
                except ValueError:
                    self.show_message("Validation Error", "Capacity must be a positive number", "warning")
                    return
                
                # Update table
                success = self.app.table_model.update(table_id, new_table_number, new_capacity, new_status)
                
                if success:
                    self.show_message("Success", f"Table '{new_table_number}' updated successfully", "info")
                    edit_window.destroy()
                    self.load_tables_grid()
                else:
                    self.show_message("Error", "Table number already exists", "error")
            
            def cancel_edit():
                edit_window.destroy()
            
            self.create_button_group(edit_button_frame, [
                ("Update Table", update_table, "Primary.TButton"),
                ("Cancel", cancel_edit, "Secondary.TButton")
            ])
            
            # Focus on first field
            edit_table_number_entry.focus_set()
            edit_window.bind("<Return>", lambda e: update_table())
            edit_window.bind("<Escape>", lambda e: cancel_edit())
        
        def cancel_select():
            select_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Edit Selected", select_table_to_edit, "Primary.TButton"),
            ("Cancel", cancel_select, "Secondary.TButton")
        ])
        
        # Focus on listbox
        table_listbox.focus_set()
        table_listbox.bind("<Double-Button-1>", lambda e: select_table_to_edit())
        select_window.bind("<Escape>", lambda e: cancel_select())
    
    def delete_table(self):
        """Delete selected table with modern dialog"""
        # Create modern select table window
        select_window = tk.Toplevel(self.app.root)
        select_window.title("Select Table to Delete")
        select_window.geometry("450x500")
        select_window.configure(background=COLOR_BACKGROUND_LIGHT)
        select_window.resizable(False, False)
        
        # Center the window
        select_window.transient(self.app.root)
        select_window.grab_set()
        
        # Main container
        main_frame = self.create_modern_frame(
            select_window, 
            style="Card.TFrame", 
            padding=SPACING_L
        )
        main_frame.pack(fill=tk.BOTH, expand=True, padx=SPACING_M, pady=SPACING_M)
        
        # Title with warning
        title_label = self.create_modern_label(
            main_frame,
            "Select Table to Delete",
            style="SectionTitle.TLabel"
        )
        title_label.pack(pady=(0, SPACING_S))
        
        warning_label = self.create_modern_label(
            main_frame,
            "⚠️ This action cannot be undone",
            style="Small.TLabel"
        )
        warning_label.pack(pady=(0, SPACING_M))
        
        # Table list with modern styling
        list_frame = self.create_modern_frame(
            main_frame, 
            style="Card.TFrame", 
            padding=SPACING_S
        )
        list_frame.pack(fill=tk.BOTH, expand=True, pady=SPACING_M)
        
        # Create modern listbox with scrollbar
        table_listbox = tk.Listbox(
            list_frame,
            font=(FONT_FAMILY_PRIMARY, 11),
            background=COLOR_CARD_WHITE,
            foreground=COLOR_TEXT_PRIMARY,
            selectbackground=COLOR_ERROR_LIGHT,
            selectforeground=COLOR_ERROR,
            borderwidth=1,
            relief='solid',
            highlightthickness=0,
            height=12
        )
        
        # Add scrollbar
        list_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=table_listbox.yview)
        table_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        table_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load tables
        tables = self.app.table_model.get_all()
        table_data = {}
        
        for i, table in enumerate(tables):
            table_id, table_number, capacity, status = table
            display_text = f"Table {table_number} (Capacity: {capacity})"
            table_listbox.insert(tk.END, display_text)
            table_data[i] = {'id': table_id, 'name': table_number}
        
        # Buttons
        button_frame = ttk.Frame(main_frame, style="Card.TFrame")
        button_frame.pack(fill=tk.X, pady=SPACING_M)
        
        def select_table_to_delete():
            selection = table_listbox.curselection()
            if not selection:
                self.show_message("Selection Required", "Please select a table to delete", "warning")
                return
            
            index = selection[0]
            table_id = table_data[index]['id']
            table_name = table_data[index]['name']
            
            # Confirm deletion with modern dialog
            if self.show_message("Confirm Delete", 
                                f"Are you sure you want to delete Table {table_name}?\n\nThis action cannot be undone.", 
                                "yesno"):
                # Delete table
                self.app.table_model.delete(table_id)
                
                self.show_message("Success", f"Table {table_name} deleted successfully", "info")
                select_window.destroy()
                self.load_tables_grid()
        
        def cancel_delete():
            select_window.destroy()
        
        self.create_button_group(button_frame, [
            ("Delete Selected", select_table_to_delete, "Danger.TButton"),
            ("Cancel", cancel_delete, "Secondary.TButton")
        ])
        
        # Focus on listbox
        table_listbox.focus_set()
        table_listbox.bind("<Double-Button-1>", lambda e: select_table_to_delete())
        select_window.bind("<Escape>", lambda e: cancel_delete())
    
    def reset_all_tables(self):
        """Reset status of all tables to Available with modern confirmation"""
        if self.show_message("Reset All Tables", 
                            "Are you sure you want to reset all tables to 'Available' status?\n\nThis will change the status of all tables in the system.", 
                            "yesno"):
            self.app.table_model.reset_all()
            self.show_message("Success", "All tables have been reset to 'Available' status", "info")
            self.load_tables_grid()