import tkinter as tk
from tkinter import ttk
from utils.constants import *

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
        """Show a message dialog"""
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
        return False
    
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
