import tkinter as tk
from tkinter import ttk
from src.utils.constants import *

class BaseUI:
    """Base class for UI components"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.db = app.db
        
    def clear_frame(self, frame):
        """Clear all widgets from a frame"""
        for widget in frame.winfo_children():
            widget.destroy()
    
    def create_status_bar(self, parent):
        """Create a status bar at the bottom of the window"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        
        # Keyboard shortcut indicator
        shortcut_indicator = ttk.Label(status_frame, text="Press F1 for shortcuts", relief=tk.SUNKEN)
        shortcut_indicator.pack(side=tk.RIGHT, padx=2, pady=2)
        
        return status_bar, shortcut_indicator, status_bar
    
    def create_treeview(self, parent, columns, headings, column_widths=None):
        """Create a standardized treeview with scrollbar"""
        # Create treeview
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        # Set headings
        for i, heading in enumerate(headings):
            tree.heading(columns[i], text=heading)
            if column_widths and i < len(column_widths):
                tree.column(columns[i], width=column_widths[i])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        return tree, scrollbar
    
    def create_form_entry(self, parent, label_text, row, column, width=30, show=""):
        """Create a form entry with label"""
        ttk.Label(parent, text=label_text).grid(row=row, column=column, sticky=tk.W, pady=5)
        entry = ttk.Entry(parent, width=width, show=show)
        entry.grid(row=row, column=column+1, sticky=tk.W+tk.E, pady=5)
        return entry
    
    def create_form_combo(self, parent, label_text, values, row, column, width=28):
        """Create a form combobox with label"""
        ttk.Label(parent, text=label_text).grid(row=row, column=column, sticky=tk.W, pady=5)
        var = tk.StringVar()
        combo = ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=width)
        combo.grid(row=row, column=column+1, sticky=tk.W+tk.E, pady=5)
        return combo, var
    
    def create_button_frame(self, parent, buttons):
        """Create a frame with buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command).pack(side=tk.LEFT, padx=5)
        
        return button_frame
    
    def show_message(self, title, message, message_type="info"):
        """Show a message dialog with automatic error logging"""
        try:
            # Log error messages automatically
            if message_type == "error":
                self._log_error(title, message)
            elif message_type == "warning":
                self._log_warning(title, message)
            
            # Show the message dialog
            if message_type == "info":
                from tkinter import messagebox
                messagebox.showinfo(title, message)
            elif message_type == "warning":
                from tkinter import messagebox
                messagebox.showwarning(title, message)
            elif message_type == "error":
                from tkinter import messagebox
                messagebox.showerror(title, message)
            elif message_type == "yesno":
                from tkinter import messagebox
                return messagebox.askyesno(title, message)
        except Exception as e:
            # Fallback logging if the main app is not available
            print(f"Error in show_message: {str(e)}")
        return False
    
    def _log_error(self, title, message):
        """Log error to bug logger"""
        try:
            if hasattr(self.app, 'log_error'):
                # Get current screen name for context
                screen_name = self.__class__.__name__
                error_context = f"Screen: {screen_name}, Title: {title}"
                self.app.log_error(f"{message}\n\nContext: {error_context}", "high")
        except Exception as e:
            print(f"Failed to log error: {str(e)}")
    
    def _log_warning(self, title, message):
        """Log warning to bug logger"""
        try:
            if hasattr(self.app, 'log_error'):
                # Get current screen name for context
                screen_name = self.__class__.__name__
                warning_context = f"Screen: {screen_name}, Title: {title}"
                self.app.log_error(f"WARNING: {message}\n\nContext: {warning_context}", "medium")
        except Exception as e:
            print(f"Failed to log warning: {str(e)}")
    
    def handle_exception(self, exception, context=""):
        """Handle and log exceptions with context"""
        try:
            import traceback
            error_details = f"Exception: {str(exception)}\n\nTraceback:\n{traceback.format_exc()}"
            if context:
                error_details = f"Context: {context}\n\n{error_details}"
            
            # Get current screen name for additional context
            screen_name = self.__class__.__name__
            error_details = f"Screen: {screen_name}\n\n{error_details}"
            
            if hasattr(self.app, 'log_error'):
                self.app.log_error(error_details, "high")
            else:
                print(error_details)
            
            # Show user-friendly error message
            self.show_message("Error", f"An unexpected error occurred: {str(exception)}", "error")
        except Exception as e:
            print(f"Failed to handle exception: {str(e)}")
            print(f"Original exception: {str(exception)}")
    
    def show_input_dialog(self, title, prompt, initialvalue="", minvalue=None, maxvalue=None):
        """Show an input dialog"""
        from tkinter import simpledialog
        if minvalue is not None and maxvalue is not None:
            return simpledialog.askinteger(title, prompt, initialvalue=initialvalue, 
                                     minvalue=minvalue, maxvalue=maxvalue)
        else:
            return simpledialog.askstring(title, prompt, initialvalue=initialvalue)
    
    def show_file_dialog(self, title, filetypes, defaultextension="", mode="save", initialfile=""):
        """Show file dialog"""
        from tkinter import filedialog
        if mode == "save":
            return filedialog.asksaveasfilename(
                defaultextension=defaultextension,
                filetypes=filetypes,
                initialfile=initialfile,
                title=title
            )
        else:  # open
            return filedialog.askopenfilename(
                filetypes=filetypes,
                title=title
            )
    
    def configure_styles(self):
        """Configure custom styles for ttk widgets"""
        style = ttk.Style()
        
        # Configure available table style
        style.configure("Available.TFrame", background=COLOR_AVAILABLE)
        style.configure("Occupied.TFrame", background=COLOR_OCCUPIED)
        
        # Configure treeview tags for inventory
        style.configure("Treeview", font=('Arial', 9))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        # Configure modern styles based on design system
        self._configure_modern_styles(style)
    
    def _configure_modern_styles(self, style):
        """Configure modern styling based on design system"""
        
        # Modern Button Styles
        style.configure("Primary.TButton",
                       background=COLOR_PRIMARY,
                       foreground=COLOR_CARD_WHITE,
                       borderwidth=0,
                       focuscolor='none',
                       font=(FONT_FAMILY_PRIMARY, 12, 'bold'),
                       padding=(12, 8))
        style.map("Primary.TButton",
                 background=[('active', COLOR_PRIMARY_LIGHT),
                           ('pressed', COLOR_PRIMARY_DARK)])
        
        style.configure("Secondary.TButton",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_PRIMARY,
                       borderwidth=1,
                       focuscolor='none',
                       font=(FONT_FAMILY_PRIMARY, 12, 'bold'),
                       padding=(12, 8))
        style.map("Secondary.TButton",
                 background=[('active', COLOR_PRIMARY),
                           ('pressed', COLOR_PRIMARY_DARK)],
                 foreground=[('active', COLOR_CARD_WHITE),
                           ('pressed', COLOR_CARD_WHITE)])
        
        style.configure("Success.TButton",
                       background=COLOR_SUCCESS,
                       foreground=COLOR_CARD_WHITE,
                       borderwidth=0,
                       focuscolor='none',
                       font=(FONT_FAMILY_PRIMARY, 12, 'bold'),
                       padding=(12, 8))
        style.map("Success.TButton",
                 background=[('active', '#229954'),
                           ('pressed', '#1e8449')])
        
        style.configure("Danger.TButton",
                       background=COLOR_ERROR,
                       foreground=COLOR_CARD_WHITE,
                       borderwidth=0,
                       focuscolor='none',
                       font=(FONT_FAMILY_PRIMARY, 12, 'bold'),
                       padding=(12, 8))
        style.map("Danger.TButton",
                 background=[('active', '#c0392b'),
                           ('pressed', '#a93226')])
        
        # Modern Frame Styles
        style.configure("Card.TFrame",
                       background=COLOR_CARD_WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_LIGHT)
        
        style.configure("Panel.TFrame",
                       background=COLOR_CARD_WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_MEDIUM)
        
        # Modern Label Styles
        style.configure("Title.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_PRIMARY_DARK,
                       font=(FONT_FAMILY_PRIMARY, 24, 'bold'))
        
        style.configure("SectionTitle.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_PRIMARY_DARK,
                       font=(FONT_FAMILY_PRIMARY, 18, 'bold'))
        
        style.configure("CardTitle.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_PRIMARY_DARK,
                       font=(FONT_FAMILY_PRIMARY, 16, 'bold'))
        
        style.configure("Subtitle.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       font=(FONT_FAMILY_PRIMARY, 14, 'medium'))
        
        style.configure("Body.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_PRIMARY,
                       font=(FONT_FAMILY_PRIMARY, 12, 'normal'))
        
        style.configure("Small.TLabel",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_SECONDARY,
                       font=(FONT_FAMILY_PRIMARY, 10, 'normal'))
        
        # Modern Entry Styles
        style.configure("Modern.TEntry",
                       fieldbackground=COLOR_CARD_WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_MEDIUM,
                       font=(FONT_FAMILY_PRIMARY, 12))
        style.map("Modern.TEntry",
                 bordercolor=[('focus', COLOR_PRIMARY),
                            ('!focus', COLOR_BORDER_MEDIUM)],
                 borderwidth=[('focus', 2),
                            ('!focus', 1)])
        
        # Modern Combobox Styles
        style.configure("Modern.TCombobox",
                       fieldbackground=COLOR_CARD_WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_MEDIUM,
                       font=(FONT_FAMILY_PRIMARY, 12))
        style.map("Modern.TCombobox",
                 bordercolor=[('focus', COLOR_PRIMARY),
                            ('!focus', COLOR_BORDER_MEDIUM)],
                 borderwidth=[('focus', 2),
                            ('!focus', 1)])
        
        # Modern Treeview Styles
        style.configure("Modern.Treeview",
                       background=COLOR_CARD_WHITE,
                       foreground=COLOR_TEXT_PRIMARY,
                       fieldbackground=COLOR_CARD_WHITE,
                       borderwidth=1,
                       relief='solid',
                       bordercolor=COLOR_BORDER_LIGHT,
                       font=(FONT_FAMILY_PRIMARY, 11))
        
        style.configure("Modern.Treeview.Heading",
                       background=COLOR_BACKGROUND_LIGHT,
                       foreground=COLOR_PRIMARY_DARK,
                       font=(FONT_FAMILY_PRIMARY, 10, 'bold'))
        
        style.map("Modern.Treeview",
                 background=[('selected', COLOR_PRIMARY_LIGHT)],
                 foreground=[('selected', COLOR_CARD_WHITE)])
        
        # Table Card Shadow Effect
        style.configure("Shadow.TFrame",
                       background=COLOR_SHADOW,
                       borderwidth=0,
                       relief='flat')
    
    def create_modern_frame(self, parent, style="Card.TFrame", padding=SPACING_M):
        """Create a modern styled frame"""
        frame = ttk.Frame(parent, style=style, padding=padding)
        return frame
    
    def create_modern_button(self, parent, text, command, style="Primary.TButton", width=None):
        """Create a modern styled button"""
        button = ttk.Button(parent, text=text, command=command, style=style)
        if width:
            button.configure(width=width)
        return button
    
    def create_modern_label(self, parent, text, style="Body.TLabel", **kwargs):
        """Create a modern styled label"""
        label = ttk.Label(parent, text=text, style=style, **kwargs)
        return label
    
    def create_modern_entry(self, parent, style="Modern.TEntry", **kwargs):
        """Create a modern styled entry"""
        entry = ttk.Entry(parent, style=style, **kwargs)
        return entry
    
    def create_modern_combobox(self, parent, textvariable, values, style="Modern.TCombobox", **kwargs):
        """Create a modern styled combobox"""
        combo = ttk.Combobox(parent, textvariable=textvariable, values=values, style=style, **kwargs)
        return combo
    
    def create_modern_checkbutton(self, parent, variable, text, **kwargs):
        """Create a modern styled checkbutton"""
        checkbutton = ttk.Checkbutton(parent, variable=variable, text=text, **kwargs)
        return checkbutton
    
    def create_modern_radiobutton(self, parent, variable, text, value, **kwargs):
        """Create a modern styled radiobutton"""
        radiobutton = ttk.Radiobutton(parent, variable=variable, text=text, value=value, **kwargs)
        return radiobutton
    
    def create_modern_treeview(self, parent, columns, headings, column_widths=None, style="Modern.Treeview"):
        """Create a modern styled treeview with scrollbar"""
        # Create treeview
        tree = ttk.Treeview(parent, columns=columns, show="headings", style=style)
        
        # Set headings
        for i, heading in enumerate(headings):
            tree.heading(columns[i], text=heading)
            if column_widths and i < len(column_widths):
                tree.column(columns[i], width=column_widths[i])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        return tree, scrollbar
    
    def create_button_group(self, parent, buttons, spacing=SPACING_S):
        """Create a group of modern styled buttons with proper spacing"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=SPACING_M)
        
        for i, (text, command, style) in enumerate(buttons):
            button = self.create_modern_button(button_frame, text, command, style)
            button.pack(side=tk.LEFT, padx=(0 if i == 0 else spacing, 0))
        
        return button_frame
    
    def create_form_field(self, parent, label_text, entry_type="entry", **kwargs):
        """Create a modern form field with label"""
        # Create a container frame for the form field
        field_frame = ttk.Frame(parent)
        field_frame.pack(fill=tk.X, pady=SPACING_S)
        
        # Label
        label = self.create_modern_label(field_frame, label_text, style="Body.TLabel")
        label.pack(anchor=tk.W, padx=(SPACING_M, SPACING_S))
        
        # Entry widget
        if entry_type == "entry":
            field = self.create_modern_entry(field_frame, **kwargs)
        elif entry_type == "combobox":
            field = self.create_modern_combobox(field_frame, **kwargs)
        elif entry_type == "checkbutton":
            # Handle checkbutton case
            field = None  # No field to pack for checkbutton
            # Create checkbutton directly with label
            checkbutton = ttk.Checkbutton(field_frame, **kwargs)
            checkbutton.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
            return checkbutton
        else:
            # Default to entry for unknown types
            field = self.create_modern_entry(field_frame, **kwargs)
        
        field.pack(fill=tk.X, padx=(SPACING_M, SPACING_M))
        
        return field
    
    def create_separator(self, parent, orient=tk.HORIZONTAL, padding=SPACING_M):
        """Create a visual separator"""
        separator = ttk.Separator(parent, orient=orient)
        if orient == tk.HORIZONTAL:
            separator.pack(fill=tk.X, pady=padding)
        else:
            separator.pack(fill=tk.Y, padx=padding)
        return separator
