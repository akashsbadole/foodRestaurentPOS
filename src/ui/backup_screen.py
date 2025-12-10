"""
Advanced Backup Management Screen
Provides comprehensive backup management interface with scheduling,
configuration, and monitoring capabilities
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict, List, Any
import threading
import os

from .base_ui import BaseUI
from src.utils.backup_manager import BackupManager, BackupConfig

class BackupScreen(BaseUI):
    """Advanced backup management screen"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.app = app
        
        # Initialize backup manager
        self.backup_manager = BackupManager(app)
        
        # UI components
        self.backup_list = None
        self.status_label = None
        self.progress_var = None
        self.progress_bar = None
        
        self.setup_ui()
        
        # Refresh backup list
        self.refresh_backup_list()
        self.refresh_statistics()
    
    def setup_ui(self):
        """Setup backup management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Backup Management", 
                           font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.app.content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Backup Operations tab
        self.operations_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.operations_frame, text="Operations")
        self.setup_operations_tab()
        
        # Configuration tab
        self.config_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configuration")
        self.setup_configuration_tab()
        
        # Schedule tab
        self.schedule_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.schedule_frame, text="Schedule")
        self.setup_schedule_tab()
        
        # Restore tab
        self.restore_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.restore_frame, text="Restore")
        self.setup_restore_tab()
    
    def setup_operations_tab(self):
        """Setup backup operations tab"""
        # Statistics frame
        stats_frame = ttk.LabelFrame(self.operations_frame, text="Backup Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_labels = {}
        stats_items = [
            ("Total Backups:", "total_backups"),
            ("Successful:", "successful_backups"),
            ("Failed:", "failed_backups"),
            ("Success Rate:", "success_rate"),
            ("Last Backup:", "last_backup"),
            ("Storage Used:", "total_storage_mb")
        ]
        
        for i, (label, key) in enumerate(stats_items):
            row = i // 3
            col = (i % 3) * 2
            
            ttk.Label(stats_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            self.stats_labels[key] = ttk.Label(stats_frame, text="--", font=('Arial', 10, 'bold'))
            self.stats_labels[key].grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Quick actions frame
        actions_frame = ttk.LabelFrame(self.operations_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create backup section
        create_frame = ttk.Frame(actions_frame)
        create_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(create_frame, text="Create Full Backup", 
                 command=self.create_full_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(create_frame, text="Create Custom Backup", 
                 command=self.create_custom_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(create_frame, text="Verify Backups", 
                 command=self.verify_all_backups).pack(side=tk.LEFT, padx=5)
        
        # Management section
        manage_frame = ttk.Frame(actions_frame)
        manage_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(manage_frame, text="Clean Old Backups", 
                 command=self.clean_old_backups).pack(side=tk.LEFT, padx=5)
        ttk.Button(manage_frame, text="Export Backup List", 
                 command=self.export_backup_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(manage_frame, text="Refresh", 
                 command=self.refresh_backup_list).pack(side=tk.LEFT, padx=5)
        
        # Backup list frame
        list_frame = ttk.LabelFrame(self.operations_frame, text="Backup History", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create treeview for backup list
        columns = ("backup_id", "filename", "type", "created_at", "size_mb", "status")
        headers = ("ID", "Filename", "Type", "Created", "Size (MB)", "Status")
        
        self.backup_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col, header in zip(columns, headers):
            self.backup_list.heading(col, text=header)
            self.backup_list.column(col, width=120)
        
        # Scrollbar for backup list
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_list.yview)
        self.backup_list.configure(yscrollcommand=scrollbar.set)
        
        self.backup_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click for backup details
        self.backup_list.bind("<Double-Button-1>", self.show_backup_details)
        
        # Backup actions frame
        backup_actions_frame = ttk.Frame(list_frame)
        backup_actions_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(backup_actions_frame, text="Delete Selected", 
                 command=self.delete_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_actions_frame, text="Restore Selected", 
                 command=self.restore_selected_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(backup_actions_frame, text="Download Selected", 
                 command=self.download_selected_backup).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        progress_frame = ttk.Frame(self.operations_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                      maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
    
    def setup_configuration_tab(self):
        """Setup backup configuration tab"""
        # Create scrollable frame
        canvas = tk.Canvas(self.config_frame)
        scrollbar = ttk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Basic settings frame
        basic_frame = ttk.LabelFrame(scrollable_frame, text="Basic Settings", padding=10)
        basic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Backup location
        ttk.Label(basic_frame, text="Backup Location:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.backup_location_var = tk.StringVar(value=self.backup_manager.config.backup_location)
        location_entry = ttk.Entry(basic_frame, textvariable=self.backup_location_var, width=50)
        location_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(basic_frame, text="Browse", command=self.browse_backup_location).grid(
            row=0, column=2, padx=5, pady=5)
        
        # Auto backup enabled
        self.auto_backup_var = tk.BooleanVar(value=self.backup_manager.config.auto_backup_enabled)
        ttk.Checkbutton(basic_frame, text="Enable Automatic Backups", 
                       variable=self.auto_backup_var).grid(row=1, column=0, columnspan=2, 
                                                       sticky=tk.W, padx=5, pady=5)
        
        # Backup frequency
        ttk.Label(basic_frame, text="Backup Frequency:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.frequency_var = tk.StringVar(value=self.backup_manager.config.backup_frequency)
        frequency_combo = ttk.Combobox(basic_frame, textvariable=self.frequency_var,
                                     values=["hourly", "daily", "weekly"], state="readonly", width=15)
        frequency_combo.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Retention days
        ttk.Label(basic_frame, text="Keep Backups (days):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.retention_var = tk.IntVar(value=self.backup_manager.config.backup_retention_days)
        ttk.Spinbox(basic_frame, from_=1, to=365, textvariable=self.retention_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Data types frame
        data_frame = ttk.LabelFrame(scrollable_frame, text="Data Types to Backup", padding=10)
        data_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Checkboxes for data types
        self.include_vars = {}
        data_types = [
            ("Orders", "include_orders", self.backup_manager.config.include_orders),
            ("Menu Items", "include_menu_items", self.backup_manager.config.include_menu_items),
            ("Categories", "include_categories", self.backup_manager.config.include_categories),
            ("Tables", "include_tables", self.backup_manager.config.include_tables),
            ("Users", "include_users", self.backup_manager.config.include_users),
            ("Settings", "include_settings", self.backup_manager.config.include_settings),
            ("Inventory", "include_inventory", self.backup_manager.config.include_inventory)
        ]
        
        for i, (label, key, value) in enumerate(data_types):
            row = i // 2
            col = (i % 2) * 2
            
            var = tk.BooleanVar(value=value)
            self.include_vars[key] = var
            ttk.Checkbutton(data_frame, text=label, variable=var).grid(
                row=row, column=col, sticky=tk.W, padx=5, pady=2)
        
        # Advanced options frame
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="Advanced Options", padding=10)
        advanced_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Checkboxes for advanced options
        self.compress_var = tk.BooleanVar(value=self.backup_manager.config.compress_backups)
        ttk.Checkbutton(advanced_frame, text="Compress Backups (.gz)", 
                       variable=self.compress_var).grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.encrypt_var = tk.BooleanVar(value=self.backup_manager.config.encrypt_backups)
        ttk.Checkbutton(advanced_frame, text="Encrypt Backups", 
                       variable=self.encrypt_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        self.verify_var = tk.BooleanVar(value=self.backup_manager.config.verify_backups)
        ttk.Checkbutton(advanced_frame, text="Verify Backup Integrity", 
                       variable=self.verify_var).grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        
        self.incremental_var = tk.BooleanVar(value=self.backup_manager.config.incremental_backups)
        ttk.Checkbutton(advanced_frame, text="Incremental Backups", 
                       variable=self.incremental_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Save configuration button
        save_frame = ttk.Frame(scrollable_frame)
        save_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(save_frame, text="Save Configuration", 
                 command=self.save_configuration).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="Reset to Defaults", 
                 command=self.reset_configuration).pack(side=tk.LEFT, padx=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_schedule_tab(self):
        """Setup backup schedule tab"""
        # Schedule status frame
        status_frame = ttk.LabelFrame(self.schedule_frame, text="Schedule Status", padding=10)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(status_frame, text="Automatic Backup Status:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.schedule_status_var = tk.StringVar(value="Unknown")
        ttk.Label(status_frame, textvariable=self.schedule_status_var, 
                 font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Next Scheduled Backup:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.next_backup_var = tk.StringVar(value="Not scheduled")
        ttk.Label(status_frame, textvariable=self.next_backup_var, 
                 font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Schedule controls frame
        controls_frame = ttk.LabelFrame(self.schedule_frame, text="Schedule Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Start Scheduler", 
                 command=self.start_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Stop Scheduler", 
                 command=self.stop_scheduler).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Run Backup Now", 
                 command=self.run_scheduled_backup).pack(side=tk.LEFT, padx=5)
        
        # Schedule preview frame
        preview_frame = ttk.LabelFrame(self.schedule_frame, text="Schedule Preview", padding=10)
        preview_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.schedule_text = tk.Text(preview_frame, height=10, width=70, wrap=tk.WORD)
        schedule_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.schedule_text.yview)
        self.schedule_text.configure(yscrollcommand=schedule_scrollbar.set)
        
        self.schedule_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        schedule_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Update schedule status
        self.update_schedule_status()
    
    def setup_restore_tab(self):
        """Setup backup restore tab"""
        # Restore from file frame
        file_frame = ttk.LabelFrame(self.restore_frame, text="Restore from Backup File", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="Backup File:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.restore_file_var = tk.StringVar()
        restore_file_entry = ttk.Entry(file_frame, textvariable=self.restore_file_var, width=50)
        restore_file_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_restore_file).grid(
            row=0, column=2, padx=5, pady=5)
        
        # Restore options
        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_frame, text="Overwrite Existing Data", 
                       variable=self.overwrite_var).grid(row=1, column=0, columnspan=2, 
                                                   sticky=tk.W, padx=5, pady=5)
        
        # Warning label
        ttk.Label(file_frame, text="⚠ Warning: Restore will overwrite existing data!", 
                 foreground='red').grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Restore button
        ttk.Button(file_frame, text="Restore Backup", command=self.restore_backup).grid(
            row=3, column=1, padx=5, pady=10)
        
        # Restore from list frame
        list_frame = ttk.LabelFrame(self.restore_frame, text="Restore from Backup List", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for restore list
        restore_columns = ("backup_id", "created_at", "type", "size_mb")
        restore_headers = ("ID", "Created", "Type", "Size (MB)")
        
        self.restore_list = ttk.Treeview(list_frame, columns=restore_columns, show="headings", height=8)
        
        for col, header in zip(restore_columns, restore_headers):
            self.restore_list.heading(col, text=header)
            self.restore_list.column(col, width=120)
        
        # Scrollbar for restore list
        restore_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.restore_list.yview)
        self.restore_list.configure(yscrollcommand=restore_scrollbar.set)
        
        self.restore_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        restore_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Restore from list button
        ttk.Button(list_frame, text="Restore Selected from List", 
                 command=self.restore_from_list).pack(pady=5)
        
        # Refresh restore list
        self.refresh_restore_list()
    
    def create_full_backup(self):
        """Create a full backup"""
        self.update_status("Creating full backup...", 0)
        
        def run_backup():
            try:
                success, message = self.backup_manager.create_backup("full")
                
                if success:
                    self.update_status("Full backup created successfully", 100)
                    self.refresh_backup_list()
                    self.refresh_statistics()
                    messagebox.showinfo("Success", f"Full backup created:\n{message}")
                else:
                    self.update_status(f"Backup failed: {message}", 0)
                    messagebox.showerror("Error", f"Failed to create backup:\n{message}")
            
            except Exception as e:
                self.update_status(f"Backup error: {str(e)}", 0)
                messagebox.showerror("Error", f"Backup error:\n{str(e)}")
        
        # Run in background thread
        threading.Thread(target=run_backup, daemon=True).start()
    
    def create_custom_backup(self):
        """Create a custom backup with user input"""
        dialog = CustomBackupDialog(self.app.root)
        backup_name = dialog.get_result()
        
        if backup_name:
            self.update_status(f"Creating custom backup: {backup_name}...", 0)
            
            def run_backup():
                try:
                    success, message = self.backup_manager.create_backup("custom", backup_name)
                    
                    if success:
                        self.update_status("Custom backup created successfully", 100)
                        self.refresh_backup_list()
                        self.refresh_statistics()
                        messagebox.showinfo("Success", f"Custom backup created:\n{message}")
                    else:
                        self.update_status(f"Backup failed: {message}", 0)
                        messagebox.showerror("Error", f"Failed to create backup:\n{message}")
                
                except Exception as e:
                    self.update_status(f"Backup error: {str(e)}", 0)
                    messagebox.showerror("Error", f"Backup error:\n{str(e)}")
            
            threading.Thread(target=run_backup, daemon=True).start()
    
    def verify_all_backups(self):
        """Verify all backup files"""
        self.update_status("Verifying backups...", 0)
        
        def run_verification():
            try:
                backups = self.backup_manager.get_backup_list()
                verified_count = 0
                failed_count = 0
                
                total_backups = len(backups)
                for i, backup in enumerate(backups):
                    backup_path = os.path.join(self.backup_manager.config.backup_location, backup['filename'])
                    
                    if os.path.exists(backup_path):
                        success = self.backup_manager.verify_backup(
                            os.path.join(self.backup_manager.config.backup_location, backup['filename']),
                            backup['checksum']
                        )
                        
                        if success:
                            verified_count += 1
                        else:
                            failed_count += 1
                    
                    progress = int((i + 1) / total_backups * 100)
                    self.update_status(f"Verifying backup {i+1}/{total_backups}...", progress)
                
                message = f"Verification complete:\nVerified: {verified_count}\nFailed: {failed_count}"
                self.update_status("Backup verification complete", 100)
                messagebox.showinfo("Verification Complete", message)
            
            except Exception as e:
                self.update_status(f"Verification error: {str(e)}", 0)
                messagebox.showerror("Error", f"Verification error:\n{str(e)}")
        
        threading.Thread(target=run_verification, daemon=True).start()
    
    def clean_old_backups(self):
        """Clean old backup files"""
        if messagebox.askyesno("Confirm Cleanup", 
                              "This will delete old backup files based on retention policy.\nContinue?"):
            try:
                self.backup_manager.clean_old_backups()
                self.refresh_backup_list()
                self.refresh_statistics()
                messagebox.showinfo("Success", "Old backups cleaned up successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Cleanup error:\n{str(e)}")
    
    def delete_selected_backup(self):
        """Delete selected backup"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to delete")
            return
        
        backup_id = self.backup_list.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete backup {backup_id}?"):
            try:
                success, message = self.backup_manager.delete_backup(backup_id)
                
                if success:
                    self.refresh_backup_list()
                    self.refresh_statistics()
                    messagebox.showinfo("Success", message)
                else:
                    messagebox.showerror("Error", message)
            
            except Exception as e:
                messagebox.showerror("Error", f"Delete error:\n{str(e)}")
    
    def restore_selected_backup(self):
        """Restore selected backup"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore")
            return
        
        backup_info = self.backup_list.item(selection[0])['values']
        backup_filename = backup_info[1]
        backup_path = os.path.join(self.backup_manager.config.backup_location, backup_filename)
        
        self.perform_restore(backup_path)
    
    def download_selected_backup(self):
        """Download selected backup to external location"""
        selection = self.backup_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to download")
            return
        
        backup_info = self.backup_list.item(selection[0])['values']
        backup_filename = backup_info[1]
        source_path = os.path.join(self.backup_manager.config.backup_location, backup_filename)
        
        destination = filedialog.asksaveasfilename(
            title="Download Backup",
            initialfile=backup_filename,
            filetypes=[("All Files", "*.*")]
        )
        
        if destination:
            try:
                import shutil
                shutil.copy2(source_path, destination)
                messagebox.showinfo("Success", f"Backup downloaded to:\n{destination}")
            except Exception as e:
                messagebox.showerror("Error", f"Download error:\n{str(e)}")
    
    def show_backup_details(self, event):
        """Show detailed information about selected backup"""
        selection = self.backup_list.selection()
        if not selection:
            return
        
        backup_info = self.backup_list.item(selection[0])['values']
        backup_id = backup_info[0]
        
        # Find backup details
        backup_details = None
        for backup in self.backup_manager.backup_history:
            if backup.backup_id == backup_id:
                backup_details = backup
                break
        
        if backup_details:
            BackupDetailsDialog(self.app.root, backup_details)
    
    def browse_backup_location(self):
        """Browse for backup location"""
        location = filedialog.askdirectory(title="Select Backup Location")
        if location:
            self.backup_location_var.set(location)
    
    def save_configuration(self):
        """Save backup configuration"""
        try:
            # Create new config
            config = BackupConfig(
                backup_location=self.backup_location_var.get(),
                auto_backup_enabled=self.auto_backup_var.get(),
                backup_frequency=self.frequency_var.get(),
                backup_retention_days=self.retention_var.get(),
                include_orders=self.include_vars['include_orders'].get(),
                include_menu_items=self.include_vars['include_menu_items'].get(),
                include_categories=self.include_vars['include_categories'].get(),
                include_tables=self.include_vars['include_tables'].get(),
                include_users=self.include_vars['include_users'].get(),
                include_settings=self.include_vars['include_settings'].get(),
                include_inventory=self.include_vars['include_inventory'].get(),
                compress_backups=self.compress_var.get(),
                encrypt_backups=self.encrypt_var.get(),
                verify_backups=self.verify_var.get(),
                incremental_backups=self.incremental_var.get()
            )
            
            # Save configuration
            success = self.backup_manager.save_config(config)
            
            if success:
                messagebox.showinfo("Success", "Configuration saved successfully")
                
                # Restart scheduler if settings changed
                if self.backup_manager.config.auto_backup_enabled != config.auto_backup_enabled or \
                   self.backup_manager.config.backup_frequency != config.backup_frequency:
                    self.backup_manager.stop_scheduler()
                    if config.auto_backup_enabled:
                        self.backup_manager.start_scheduler()
                
                self.update_schedule_status()
            else:
                messagebox.showerror("Error", "Failed to save configuration")
        
        except Exception as e:
            messagebox.showerror("Error", f"Configuration error:\n{str(e)}")
    
    def reset_configuration(self):
        """Reset configuration to defaults"""
        if messagebox.askyesno("Confirm Reset", "Reset configuration to default values?"):
            try:
                default_config = BackupConfig()
                success = self.backup_manager.save_config(default_config)
                
                if success:
                    messagebox.showinfo("Success", "Configuration reset to defaults")
                    # Refresh UI
                    self.backup_manager = BackupManager(self.app)
                    self.setup_configuration_tab()
                    self.update_schedule_status()
                else:
                    messagebox.showerror("Error", "Failed to reset configuration")
            
            except Exception as e:
                messagebox.showerror("Error", f"Reset error:\n{str(e)}")
    
    def start_scheduler(self):
        """Start backup scheduler"""
        try:
            self.backup_manager.start_scheduler()
            self.update_schedule_status()
            messagebox.showinfo("Success", "Backup scheduler started")
        except Exception as e:
            messagebox.showerror("Error", f"Scheduler start error:\n{str(e)}")
    
    def stop_scheduler(self):
        """Stop backup scheduler"""
        try:
            self.backup_manager.stop_scheduler()
            self.update_schedule_status()
            messagebox.showinfo("Success", "Backup scheduler stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Scheduler stop error:\n{str(e)}")
    
    def run_scheduled_backup(self):
        """Run scheduled backup immediately"""
        try:
            self.backup_manager.scheduled_backup()
            self.refresh_backup_list()
            self.refresh_statistics()
            messagebox.showinfo("Success", "Scheduled backup executed")
        except Exception as e:
            messagebox.showerror("Error", f"Scheduled backup error:\n{str(e)}")
    
    def update_schedule_status(self):
        """Update schedule status display"""
        try:
            if self.backup_manager.scheduler_running:
                self.schedule_status_var.set("Running")
                
                # Calculate next backup time
                frequency = self.backup_manager.config.backup_frequency
                now = datetime.now()
                
                if frequency == "hourly":
                    next_backup = now + timedelta(hours=1)
                elif frequency == "daily":
                    next_backup = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    if next_backup <= now:
                        next_backup += timedelta(days=1)
                elif frequency == "weekly":
                    next_backup = now.replace(hour=2, minute=0, second=0, microsecond=0)
                    days_ahead = 6 - now.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7
                    next_backup += timedelta(days=days_ahead)
                else:
                    next_backup = None
                
                if next_backup:
                    self.next_backup_var.set(next_backup.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    self.next_backup_var.set("Not scheduled")
            else:
                self.schedule_status_var.set("Stopped")
                self.next_backup_var.set("Not scheduled")
            
            # Update schedule preview
            self.update_schedule_preview()
        
        except Exception as e:
            print(f"Error updating schedule status: {e}")
    
    def update_schedule_preview(self):
        """Update schedule preview text"""
        try:
            frequency = self.backup_manager.config.backup_frequency
            retention = self.backup_manager.config.backup_retention_days
            
            schedule_text = f"Backup Schedule Configuration:\n\n"
            schedule_text += f"Frequency: {frequency.capitalize()}\n"
            schedule_text += f"Retention Period: {retention} days\n"
            schedule_text += f"Auto Backup: {'Enabled' if self.backup_manager.config.auto_backup_enabled else 'Disabled'}\n\n"
            
            if frequency == "hourly":
                schedule_text += "Backups will be created every hour.\n"
                schedule_text += f"Approximately {24 * retention} backups will be kept.\n"
            elif frequency == "daily":
                schedule_text += "Backups will be created daily at 2:00 AM.\n"
                schedule_text += f"Approximately {retention} backups will be kept.\n"
            elif frequency == "weekly":
                schedule_text += "Backups will be created weekly on Sunday at 2:00 AM.\n"
                schedule_text += f"Approximately {retention // 7} backups will be kept.\n"
            
            schedule_text += f"\nOld backups will be automatically deleted after {retention} days."
            
            self.schedule_text.delete(1.0, tk.END)
            self.schedule_text.insert(1.0, schedule_text)
        
        except Exception as e:
            print(f"Error updating schedule preview: {e}")
    
    def browse_restore_file(self):
        """Browse for backup file to restore"""
        file_path = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[
                ("JSON Backup Files", "*.json"),
                ("Compressed Backups", "*.json.gz"),
                ("Encrypted Backups", "*.enc"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self.restore_file_var.set(file_path)
    
    def restore_backup(self):
        """Restore backup from file path"""
        file_path = self.restore_file_var.get()
        if not file_path:
            messagebox.showwarning("No File", "Please select a backup file to restore")
            return
        
        self.perform_restore(file_path)
    
    def restore_from_list(self):
        """Restore selected backup from list"""
        selection = self.restore_list.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a backup to restore")
            return
        
        backup_info = self.restore_list.item(selection[0])['values']
        backup_id = backup_info[0]
        
        # Find backup filename
        backup_filename = None
        for backup in self.backup_manager.backup_history:
            if backup.backup_id == backup_id:
                backup_filename = backup.filename
                break
        
        if backup_filename:
            backup_path = os.path.join(self.backup_manager.config.backup_location, backup_filename)
            self.perform_restore(backup_path)
    
    def perform_restore(self, backup_path: str):
        """Perform restore operation"""
        overwrite = self.overwrite_var.get()
        
        if not overwrite:
            if not messagebox.askyesno("Confirm Restore", 
                                      "This will overwrite existing data.\nContinue?"):
                return
        
        self.update_status("Restoring backup...", 0)
        
        def run_restore():
            try:
                success, message = self.backup_manager.restore_backup(backup_path, overwrite)
                
                if success:
                    self.update_status("Restore completed successfully", 100)
                    messagebox.showinfo("Success", f"Backup restored successfully:\n{message}")
                else:
                    self.update_status(f"Restore failed: {message}", 0)
                    messagebox.showerror("Error", f"Failed to restore backup:\n{message}")
            
            except Exception as e:
                self.update_status(f"Restore error: {str(e)}", 0)
                messagebox.showerror("Error", f"Restore error:\n{str(e)}")
        
        threading.Thread(target=run_restore, daemon=True).start()
    
    def refresh_backup_list(self):
        """Refresh backup list display"""
        try:
            # Clear existing items
            for item in self.backup_list.get_children():
                self.backup_list.delete(item)
            
            # Get backup list
            backups = self.backup_manager.get_backup_list()
            
            # Add backups to treeview
            for backup in backups:
                self.backup_list.insert("", tk.END, values=(
                    backup['backup_id'],
                    backup['filename'],
                    backup['backup_type'],
                    backup['created_at'],
                    backup['file_size_mb'],
                    backup['status']
                ))
        
        except Exception as e:
            print(f"Error refreshing backup list: {e}")
    
    def refresh_restore_list(self):
        """Refresh restore list display"""
        try:
            # Clear existing items
            for item in self.restore_list.get_children():
                self.restore_list.delete(item)
            
            # Get backup list
            backups = self.backup_manager.get_backup_list()
            
            # Add backups to restore treeview
            for backup in backups:
                self.restore_list.insert("", tk.END, values=(
                    backup['backup_id'],
                    backup['created_at'],
                    backup['backup_type'],
                    backup['file_size_mb']
                ))
        
        except Exception as e:
            print(f"Error refreshing restore list: {e}")
    
    def refresh_statistics(self):
        """Refresh backup statistics display"""
        try:
            stats = self.backup_manager.get_backup_statistics()
            
            for key, label in self.stats_labels.items():
                if key in stats:
                    if key == 'success_rate':
                        label.config(text=f"{stats[key]}%")
                    elif key == 'total_storage_mb':
                        label.config(text=f"{stats[key]} MB")
                    else:
                        label.config(text=str(stats[key]))
                else:
                    label.config(text="--")
        
        except Exception as e:
            print(f"Error refreshing statistics: {e}")
    
    def export_backup_list(self):
        """Export backup list to file"""
        try:
            backups = self.backup_manager.get_backup_list()
            
            if not backups:
                messagebox.showwarning("No Data", "No backups to export")
                return
            
            # Choose save location
            filename = f"backup_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path = filedialog.asksaveasfilename(
                title="Export Backup List",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
                initialfile=filename
            )
            
            if file_path:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if backups:
                        writer = csv.DictWriter(f, fieldnames=backups[0].keys())
                        writer.writeheader()
                        writer.writerows(backups)
                
                messagebox.showinfo("Success", f"Backup list exported to:\n{file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Export error:\n{str(e)}")
    
    def update_status(self, message: str, progress: int):
        """Update status label and progress bar"""
        if self.status_label:
            self.status_label.config(text=message)
        if self.progress_bar:
            self.progress_var.set(progress)


class CustomBackupDialog:
    """Dialog for creating custom backup"""
    
    def __init__(self, parent):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Custom Backup")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup custom backup dialog UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Backup name
        ttk.Label(main_frame, text="Backup Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.backup_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.backup_name_var, width=30).grid(
            row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.description_var, width=30).grid(
            row=1, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Info label
        info_label = ttk.Label(main_frame, 
                           text="The backup will include a timestamp automatically.",
                           font=('Arial', 9), foreground='gray')
        info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Create", command=self.create_backup).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
    
    def create_backup(self):
        """Create custom backup"""
        backup_name = self.backup_name_var.get().strip()
        
        if not backup_name:
            messagebox.showerror("Error", "Please enter a backup name")
            return
        
        self.result = backup_name
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel dialog"""
        self.dialog.destroy()
    
    def get_result(self):
        """Get dialog result"""
        self.dialog.wait_window()
        return self.result


class BackupDetailsDialog:
    """Dialog for showing backup details"""
    
    def __init__(self, parent, backup_info):
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Backup Details")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.setup_ui(backup_info)
    
    def setup_ui(self, backup_info):
        """Setup backup details dialog UI"""
        # Create scrollable frame
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Backup information
        info_frame = ttk.LabelFrame(scrollable_frame, text="Backup Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Display backup details
        details = [
            ("Backup ID:", backup_info.backup_id),
            ("Filename:", backup_info.filename),
            ("Type:", backup_info.backup_type),
            ("Created At:", backup_info.created_at.strftime('%Y-%m-%d %H:%M:%S')),
            ("File Size:", f"{backup_info.file_size / (1024*1024):.2f} MB"),
            ("Compressed:", "Yes" if backup_info.compressed else "No"),
            ("Encrypted:", "Yes" if backup_info.encrypted else "No"),
            ("Status:", backup_info.status),
            ("Checksum:", backup_info.checksum[:16] + "..." if len(backup_info.checksum) > 16 else backup_info.checksum)
        ]
        
        for i, (label, value) in enumerate(details):
            ttk.Label(info_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(info_frame, text=str(value), font=('Arial', 10, 'bold')).grid(
                row=i, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Includes frame
        includes_frame = ttk.LabelFrame(scrollable_frame, text="Data Included", padding=10)
        includes_frame.pack(fill=tk.X, padx=10, pady=5)
        
        for i, item in enumerate(backup_info.includes):
            ttk.Label(includes_frame, text=f"• {item.capitalize()}").pack(anchor=tk.W, pady=2)
        
        # Close button
        ttk.Button(scrollable_frame, text="Close", command=self.dialog.destroy).pack(pady=10)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
