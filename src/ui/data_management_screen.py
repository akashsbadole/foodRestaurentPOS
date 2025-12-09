import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from datetime import datetime
from .base_ui import BaseUI
from src.utils.data_exporter import DataExporter
from src.utils.data_importer import DataImporter
from src.utils.helpers import format_datetime

class DataManagementScreen(BaseUI):
    """Data Management Screen for Export/Import operations"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        
        # Initialize data manager
        from src.managers.data_manager import get_data_manager
        self.data_manager = get_data_manager(app)
        
        # Initialize exporter and importer
        self.exporter = DataExporter(app, self.data_manager)
        self.importer = DataImporter(app, self.data_manager)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup data management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Data Management", 
                           font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.app.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Export tab
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="Export Data")
        self.setup_export_tab()
        
        # Import tab
        self.import_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.import_frame, text="Import Data")
        self.setup_import_tab()
        
        # Backup tab
        self.backup_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.backup_frame, text="Backup & Restore")
        self.setup_backup_tab()
    
    def setup_export_tab(self):
        """Setup export tab"""
        # Data summary frame
        summary_frame = ttk.LabelFrame(self.export_frame, text="Data Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Get data summary
        summary = self.exporter.get_export_summary()
        
        # Create summary labels
        summary_items = [
            ("Orders", summary.get('orders', 0)),
            ("Menu Items", summary.get('menu_items', 0)),
            ("Categories", summary.get('categories', 0)),
            ("Tables", summary.get('tables', 0)),
            ("Users", summary.get('users', 0)),
            ("Inventory Items", summary.get('inventory_items', 0))
        ]
        
        for i, (label, count) in enumerate(summary_items):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(summary_frame, text=f"{label}:").grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            ttk.Label(summary_frame, text=str(count), font=('Arial', 10, 'bold')).grid(
                row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Export options frame
        options_frame = ttk.LabelFrame(self.export_frame, text="Export Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Data type selection
        ttk.Label(options_frame, text="Data Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.export_type_var = tk.StringVar(value="all")
        export_type_combo = ttk.Combobox(options_frame, textvariable=self.export_type_var, 
                                     values=["all", "orders", "menu_items", "categories", 
                                            "tables", "users", "inventory", "settings"],
                                     state="readonly", width=20)
        export_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Format selection
        ttk.Label(options_frame, text="Format:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.export_format_var = tk.StringVar(value="json")
        export_format_combo = ttk.Combobox(options_frame, textvariable=self.export_format_var,
                                        values=["json", "csv", "excel"],
                                        state="readonly", width=15)
        export_format_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Include details checkbox
        self.include_details_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Include Details", 
                      variable=self.include_details_var).grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        
        # Date range frame
        date_frame = ttk.LabelFrame(self.export_frame, text="Date Range (Optional)", padding=10)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(date_frame, text="From:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.from_date_var = tk.StringVar()
        from_date_entry = ttk.Entry(date_frame, textvariable=self.from_date_var, width=15)
        from_date_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(date_frame, text="To:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.to_date_var = tk.StringVar()
        to_date_entry = ttk.Entry(date_frame, textvariable=self.to_date_var, width=15)
        to_date_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Export buttons
        buttons_frame = ttk.Frame(self.export_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Preview Export", 
                 command=self.preview_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Export Data", 
                 command=self.export_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Refresh Summary", 
                 command=self.refresh_summary).pack(side=tk.LEFT, padx=5)
    
    def setup_import_tab(self):
        """Setup import tab"""
        # File selection frame
        file_frame = ttk.LabelFrame(self.import_frame, text="Select File", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="File Path:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.import_file_var = tk.StringVar()
        self.import_file_entry = ttk.Entry(file_frame, textvariable=self.import_file_var, width=50)
        self.import_file_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        
        ttk.Button(file_frame, text="Browse", 
                 command=self.browse_import_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Import options frame
        options_frame = ttk.LabelFrame(self.import_frame, text="Import Options", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Import type
        ttk.Label(options_frame, text="Import Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.import_type_var = tk.StringVar(value="auto")
        import_type_combo = ttk.Combobox(options_frame, textvariable=self.import_type_var,
                                     values=["auto", "all", "orders", "menu_items", "categories",
                                            "tables", "users", "inventory", "settings"],
                                     state="readonly", width=20)
        import_type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Overwrite checkbox
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Overwrite Existing Data", 
                      variable=self.overwrite_var).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Validate only checkbox
        self.validate_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Validate Only (Don't Import)", 
                      variable=self.validate_only_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Import buttons
        buttons_frame = ttk.Frame(self.import_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Validate File", 
                 command=self.validate_import_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Import Data", 
                 command=self.import_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Clear", 
                 command=self.clear_import_fields).pack(side=tk.LEFT, padx=5)
    
    def setup_backup_tab(self):
        """Setup backup and restore tab"""
        # Backup section
        backup_frame = ttk.LabelFrame(self.backup_frame, text="Create Backup", padding=10)
        backup_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(backup_frame, text="Create a complete backup of all POS data").pack(anchor=tk.W, pady=5)
        
        backup_info = ttk.Frame(backup_frame)
        backup_info.pack(fill=tk.X, pady=5)
        
        ttk.Label(backup_info, text="Backup will include:").pack(anchor=tk.W)
        ttk.Label(backup_info, text="• All orders and order details").pack(anchor=tk.W, padx=20)
        ttk.Label(backup_info, text="• Menu items and categories").pack(anchor=tk.W, padx=20)
        ttk.Label(backup_info, text="• Tables and users").pack(anchor=tk.W, padx=20)
        ttk.Label(backup_info, text="• Settings and inventory").pack(anchor=tk.W, padx=20)
        
        # Restore section
        restore_frame = ttk.LabelFrame(self.backup_frame, text="Restore from Backup", padding=10)
        restore_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(restore_frame, text="⚠ Warning: Restore will overwrite existing data!").pack(
            anchor=tk.W, pady=5, foreground='red')
        
        ttk.Label(restore_frame, text="Backup File:").pack(anchor=tk.W, padx=5, pady=2)
        self.backup_file_var = tk.StringVar()
        self.backup_file_entry = ttk.Entry(restore_frame, textvariable=self.backup_file_var, width=50)
        self.backup_file_entry.pack(fill=tk.X, padx=5, pady=2)
        
        backup_buttons = ttk.Frame(restore_frame)
        backup_buttons.pack(fill=tk.X, pady=10)
        
        ttk.Button(backup_buttons, text="Browse Backup", 
                 command=self.browse_backup_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_buttons, text="Create Backup", 
                 command=self.create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_buttons, text="Restore Backup", 
                 command=self.restore_backup).pack(side=tk.LEFT, padx=5)
    
    def browse_import_file(self):
        """Browse for import file"""
        file_path = filedialog.askopenfilename(
            title="Select Import File",
            filetypes=[
                ("All Supported Files", "*.json;*.csv;*.xlsx;*.xls"),
                ("JSON Files", "*.json"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx;*.xls"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.import_file_var.set(file_path)
    
    def browse_backup_file(self):
        """Browse for backup file"""
        file_path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[
                ("JSON Backup Files", "*.json"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.backup_file_var.set(file_path)
    
    def preview_export(self):
        """Preview export data"""
        try:
            export_type = self.export_type_var.get()
            format_type = self.export_format_var.get()
            include_details = self.include_details_var.get()
            
            # Get preview data
            if export_type == 'all':
                data = self.exporter.export_all(include_details)
            else:
                data = self.exporter.EXPORT_TYPES[export_type](include_details)
            
            if not data:
                messagebox.showwarning("No Data", "No data found to export")
                return
            
            # Show preview dialog
            self.show_preview_dialog(data, export_type, format_type)
            
        except Exception as e:
            messagebox.showerror("Preview Error", f"Error generating preview: {e}")
    
    def show_preview_dialog(self, data: dict, export_type: str, format_type: str):
        """Show preview dialog"""
        preview_window = tk.Toplevel(self.app.root)
        preview_window.title(f"Export Preview - {export_type}")
        preview_window.geometry("600x400")
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(preview_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format preview data
        if format_type == 'json':
            import json
            preview_text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        else:
            preview_text = str(data)
        
        text_widget.insert(tk.END, preview_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(preview_window, text="Close", 
                 command=preview_window.destroy).pack(pady=5)
    
    def export_data(self):
        """Export data to file"""
        try:
            export_type = self.export_type_var.get()
            format_type = self.export_format_var.get()
            include_details = self.include_details_var.get()
            
            # Get default file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"pos_export_{export_type}_{timestamp}.{format_type}"
            
            # Get save path
            file_path = filedialog.asksaveasfilename(
                title="Save Export",
                defaultextension=f".{format_type}",
                filetypes=[
                    (f"{format_type.upper()} Files", f"*.{format_type}"),
                    ("All Files", "*.*")
                ],
                initialfile=default_name
            )
            
            if not file_path:
                return
            
            # Get date range if specified
            date_range = None
            if self.from_date_var.get() or self.to_date_var.get():
                date_range = {
                    'from_date': self.from_date_var.get(),
                    'to_date': self.to_date_var.get()
                }
            
            # Perform export
            success = self.exporter.export_data(
                export_type, format_type, file_path, include_details, date_range
            )
            
            if success:
                messagebox.showinfo("Export Success", 
                                 f"Data exported successfully to:\n{file_path}")
            else:
                messagebox.showerror("Export Failed", "Failed to export data")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error during export: {e}")
    
    def validate_import_file(self):
        """Validate import file without importing"""
        self.perform_import(validate_only=True)
    
    def import_data(self):
        """Import data from file"""
        if messagebox.askyesno("Confirm Import", 
                              "This will import data and may modify existing records.\nContinue?"):
            self.perform_import(validate_only=False)
    
    def perform_import(self, validate_only: bool):
        """Perform import with validation"""
        try:
            file_path = self.import_file_var.get()
            if not file_path:
                messagebox.showwarning("No File", "Please select a file to import")
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", f"File not found:\n{file_path}")
                return
            
            import_type = self.import_type_var.get()
            overwrite = self.overwrite_var.get()
            
            # Perform import
            result = self.importer.import_data(
                file_path, import_type, validate_only, overwrite
            )
            
            # Show result
            self.show_import_result(result, validate_only)
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error during import: {e}")
    
    def show_import_result(self, result: dict, validate_only: bool):
        """Show import result dialog"""
        result_window = tk.Toplevel(self.app.root)
        result_window.title("Import Result")
        result_window.geometry("500x400")
        
        # Create scrolled text for results
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Format result text
        if result.get('success', False):
            text_widget.insert(tk.END, "✅ SUCCESS\n\n", "success")
            action = "Validation" if validate_only else "Import"
            text_widget.insert(tk.END, f"{action} completed successfully!\n\n")
            
            if 'imported_count' in result:
                text_widget.insert(tk.END, f"Records processed: {result['imported_count']}\n")
            if 'total_imported' in result:
                text_widget.insert(tk.END, f"Total records: {result['total_imported']}\n")
            
            text_widget.insert(tk.END, f"\n{result.get('message', '')}\n")
        else:
            text_widget.insert(tk.END, "❌ FAILED\n\n", "error")
            text_widget.insert(tk.END, f"Error: {result.get('error', 'Unknown error')}\n\n")
            
            if 'validation_errors' in result:
                text_widget.insert(tk.END, "Validation Errors:\n")
                for error in result['validation_errors']:
                    text_widget.insert(tk.END, f"• {error}\n")
            
            if 'errors' in result:
                text_widget.insert(tk.END, "\nImport Errors:\n")
                for error in result['errors']:
                    text_widget.insert(tk.END, f"• {error}\n")
        
        # Configure text tags
        text_widget.tag_config("success", foreground="green")
        text_widget.tag_config("error", foreground="red")
        
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(result_window, text="Close", 
                 command=result_window.destroy).pack(pady=5)
    
    def clear_import_fields(self):
        """Clear import fields"""
        self.import_file_var.set("")
        self.import_type_var.set("auto")
        self.overwrite_var.set(False)
        self.validate_only_var.set(False)
    
    def refresh_summary(self):
        """Refresh data summary"""
        # Clear and recreate export tab to refresh summary
        self.export_frame.destroy()
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="Export Data")
        self.setup_export_tab()
    
    def create_backup(self):
        """Create complete backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"pos_backup_{timestamp}.json"
            
            file_path = filedialog.asksaveasfilename(
                title="Create Backup",
                defaultextension=".json",
                filetypes=[("JSON Backup Files", "*.json"), ("All Files", "*.*")],
                initialfile=default_name
            )
            
            if not file_path:
                return
            
            # Export all data
            success = self.exporter.export_data('all', 'json', file_path, True)
            
            if success:
                messagebox.showinfo("Backup Success", 
                                 f"Backup created successfully:\n{file_path}")
            else:
                messagebox.showerror("Backup Failed", "Failed to create backup")
                
        except Exception as e:
            messagebox.showerror("Backup Error", f"Error creating backup: {e}")
    
    def restore_backup(self):
        """Restore from backup"""
        try:
            file_path = self.backup_file_var.get()
            if not file_path:
                messagebox.showwarning("No File", "Please select a backup file")
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("File Not Found", f"Backup file not found:\n{file_path}")
                return
            
            # Confirm restore
            if not messagebox.askyesno("Confirm Restore", 
                                     "⚠ WARNING: This will overwrite ALL existing data!\n\n"
                                     "This action cannot be undone.\n\n"
                                     "Continue with restore?"):
                return
            
            # Perform restore
            result = self.importer.import_data(file_path, 'all', False, True)
            
            # Show result
            self.show_import_result(result, False)
            
            if result.get('success', False):
                messagebox.showinfo("Restore Success", 
                                 "Data restored successfully!\n"
                                 "Please restart the application to ensure all changes take effect.")
                
        except Exception as e:
            messagebox.showerror("Restore Error", f"Error during restore: {e}")
