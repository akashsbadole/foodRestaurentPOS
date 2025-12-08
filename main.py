#!/usr/bin/env python3
"""
Restaurant POS System - Main Entry Point
Refactored modular version of the POS system
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import RestaurantPOSApp
import tkinter as tk

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = RestaurantPOSApp(root)
    
    # Handle window closing
    def on_closing():
        if app.on_closing():
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
