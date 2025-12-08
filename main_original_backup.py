#!/usr/bin/env python3
"""
Restaurant POS System - Main Entry Point
Refactored modular version
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import main

if __name__ == "__main__":
    main()
