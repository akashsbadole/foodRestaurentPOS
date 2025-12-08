import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime
from .base_ui import BaseUI
from ..utils.helpers import generate_kot_content

class KOTScreen(BaseUI):
    """Kitchen Order Ticket screen UI component"""
    
    def __init__(self, root, app):
        super().__init__(root, app)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup KOT management UI"""
        # Title
        title_label = ttk.Label(self.app.content_frame, text="Kitchen Order Tickets (KOT)", font=('Arial', 18, 'bold'))
        title_label.pack(pady=10)
        
        # Filter frame
        filter_frame = ttk.Frame(self.app.content_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT, padx=5)
        
        self.kot_filter_var = tk.StringVar(value="Pending")
        ttk.Radiobutton(filter_frame, text="Pending", variable=self.kot_filter_var, 
                       value="Pending", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Preparing", variable=self.kot_filter_var, 
                       value="Preparing", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Completed", variable=self.kot_filter_var, 
                       value="Completed", command=self.load_kot).pack(side=tk.LEFT, padx=5)
        
        # KOT tree
        kot_frame = ttk.Frame(self.app.content_frame)
        kot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.kot_tree, kot_scrollbar = self.create_treeview(
            kot_frame,
            ("order_number", "item", "quantity", "time", "status"),
            ("Order #", "Item", "Quantity", "Time", "Status"),
            (100, 200, 80, 120, 100)
        )
        self.kot_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.app.content_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_button_frame(buttons_frame, [
            ("Mark as Preparing", self.mark_kot_preparing),
            ("Mark as Completed", self.mark_kot_completed),
            ("Print KOT", self.print_kot),
            ("Refresh", self.load_kot)
        ])
        
        # Load KOT items
        self.load_kot()

    def load_kot(self):
        """Load KOT items"""
        status_filter = self.kot_filter_var.get()
        
        items = self.app.kot_model.get_items(status_filter)
        
        # Clear tree
        for item in self.kot_tree.get_children():
            self.kot_tree.delete(item)
        
        # Add items to tree
        for item in items:
            item_id, order_number, name, quantity, created_at, status = item
            
            # Format time
            time_obj = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            formatted_time = time_obj.strftime('%H:%M:%S')
            
            self.kot_tree.insert("", tk.END, values=(
                order_number,
                name,
                quantity,
                formatted_time,
                status
            ), tags=(item_id,))

    def mark_kot_preparing(self):
        """Mark selected KOT item as preparing"""
        selection = self.kot_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to update", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Update status
        self.app.kot_model.update_status(item_id, "Preparing")
        
        self.show_message("Success", "Item marked as 'Preparing'", "info")
        self.load_kot()

    def mark_kot_completed(self):
        """Mark selected KOT item as completed"""
        selection = self.kot_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to update", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Update status
        self.app.kot_model.update_status(item_id, "Completed")
        
        self.show_message("Success", "Item marked as 'Completed'", "info")
        self.load_kot()

    def print_kot(self):
        """Print selected KOT item"""
        selection = self.kot_tree.selection()
        if not selection:
            self.show_message("Warning", "Please select an item to print", "warning")
            return
        
        # Get item ID from tags
        item_id = int(self.kot_tree.item(selection[0])['tags'][0])
        
        # Get item details
        kot_details = self.app.kot_model.get_kot_details(item_id)
        if not kot_details:
            return
        
        order_number, name, quantity, created_at = kot_details
        
        # Create KOT content
        kot_content = generate_kot_content(order_number, name, quantity, created_at)
        
        # Save KOT to file
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"KOT_{order_number}_{name}.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(kot_content)
            self.show_message("KOT Saved", f"KOT saved to {file_path}", "info")
