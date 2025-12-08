#!/usr/bin/env python3
"""
Test script to debug KOT screen button visibility issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import tkinter as tk
from app import RestaurantPOSApp

class MockUser:
    def __init__(self):
        self.username = "admin"
        self.role = "Admin"

def test_kot_screen():
    """Test KOT screen directly"""
    root = tk.Tk()
    root.title("KOT Screen Debug Test")
    root.geometry("1200x700")
    
    # Create app instance
    app = RestaurantPOSApp(root)
    
    # Mock login
    app.current_user = MockUser()
    
    # Create main app structure
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)
    
    # Create content area
    content_container = tk.Frame(main_container)
    content_container.pack(fill=tk.BOTH, expand=True)
    
    # Create content frame
    app.content_frame = tk.Frame(content_container)
    app.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    # Load settings
    app.load_settings()
    
    # Show KOT screen directly
    print("=== Creating KOT Screen ===")
    from src.ui.kot_screen import KOTScreen
    kot_screen = KOTScreen(root, app)
    
    print("=== KOT Screen Created ===")
    root.update()  # Force update to get widget info
    
    # Print widget hierarchy
    def print_widget_hierarchy(widget, level=0):
        indent = "  " * level
        try:
            widget_class = widget.winfo_class()
            widget_visible = widget.winfo_viewable()
            widget_width = widget.winfo_width()
            widget_height = widget.winfo_height()
            print(f"{indent}{widget_class} - Visible: {widget_visible}, Size: {widget_width}x{widget_height}")
        except:
            print(f"{indent}{type(widget).__name__} - Error getting info")
        
        for child in widget.winfo_children():
            print_widget_hierarchy(child, level + 1)
    
    print("\n=== Widget Hierarchy ===")
    print_widget_hierarchy(app.content_frame)
    
    root.mainloop()

if __name__ == "__main__":
    test_kot_screen()