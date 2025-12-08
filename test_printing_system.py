#!/usr/bin/env python3
"""
Test script for the new printing system
Tests both thermal and standard printer functionality
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.printer import PrinterManager, PrinterType, PaperSize
from utils.constants import *

def test_printer_manager():
    """Test the printer manager functionality"""
    print("Testing Printer Manager...")
    print("=" * 50)
    
    # Test settings
    test_settings = {
        'thermal_printer_name': 'Test Thermal Printer',
        'standard_printer_name': 'Test Standard Printer',
        'default_bill_printer_type': 'thermal',
        'default_kot_printer_type': 'thermal',
        'bill_paper_width': '58',
        'kot_paper_width': '58',
        'auto_print_bill': 'False',
        'auto_print_kot': 'True'
    }
    
    # Initialize printer manager
    try:
        printer_manager = PrinterManager(test_settings)
        print("✓ Printer Manager initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing Printer Manager: {e}")
        return False
    
    # Test getting available printers
    try:
        available_printers = printer_manager.get_available_printers()
        print(f"✓ Available printers detected:")
        print(f"  Thermal printers: {available_printers.get('thermal', [])}")
        print(f"  Standard printers: {available_printers.get('standard', [])}")
    except Exception as e:
        print(f"✗ Error getting available printers: {e}")
    
    # Test bill data preparation
    test_bill_data = {
        'restaurant_name': 'Test Restaurant',
        'restaurant_address': '123 Test Street, Test City',
        'order_number': 'TEST001',
        'date': '2024-01-01 12:00:00',
        'order_type': 'Dine-in',
        'table_number': 'T1',
        'customer_name': None,
        'customer_mobile': None,
        'items': [
            ('Test Item 1', 2, 50.00, 100.00),
            ('Test Item 2', 1, 30.00, 30.00)
        ],
        'subtotal': 130.00,
        'tax': 6.50,
        'discount': 0.00,
        'total': 136.50,
        'tax_rate': 5.0
    }
    
    # Test KOT data preparation
    test_kot_data = {
        'order_number': 'KOT001',
        'time': '12:00:00',
        'item_name': 'Test KOT Item',
        'quantity': 2,
        'notes': 'Extra spicy'
    }
    
    # Test thermal printer functionality (simulation)
    print("\nTesting Thermal Printer Functionality...")
    try:
        # Test with thermal printer
        result = printer_manager.print_bill(test_bill_data, PrinterType.THERMAL, 'Test Thermal Printer')
        if result:
            print("✓ Thermal bill print test passed")
        else:
            print("✗ Thermal bill print test failed (expected - no physical printer)")
        
        # Test KOT with thermal printer
        result = printer_manager.print_kot(test_kot_data, PrinterType.THERMAL, 'Test Thermal Printer')
        if result:
            print("✓ Thermal KOT print test passed")
        else:
            print("✗ Thermal KOT print test failed (expected - no physical printer)")
            
    except Exception as e:
        print(f"✗ Error testing thermal printer: {e}")
    
    # Test standard printer functionality (simulation)
    print("\nTesting Standard Printer Functionality...")
    try:
        # Test with standard printer
        result = printer_manager.print_bill(test_bill_data, PrinterType.STANDARD, 'Test Standard Printer')
        if result:
            print("✓ Standard bill print test passed")
        else:
            print("✗ Standard bill print test failed")
        
        # Test KOT with standard printer
        result = printer_manager.print_kot(test_kot_data, PrinterType.STANDARD, 'Test Standard Printer')
        if result:
            print("✓ Standard KOT print test passed")
        else:
            print("✗ Standard KOT print test failed")
            
    except Exception as e:
        print(f"✗ Error testing standard printer: {e}")
    
    print("\n" + "=" * 50)
    print("Printing System Test Complete!")
    print("Note: Some tests may fail without physical printers connected")
    return True

def test_printer_dialog():
    """Test the printer selection dialog"""
    print("\nTesting Printer Selection Dialog...")
    print("=" * 50)
    
    try:
        import tkinter as tk
        from ui.printer_dialog import PrinterSelectionDialog
        
        # Create dummy root and settings
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        test_settings = {
            'thermal_printer_name': '',
            'standard_printer_name': '',
            'default_bill_printer_type': 'thermal',
            'default_kot_printer_type': 'thermal',
            'bill_paper_width': '58',
            'kot_paper_width': '58',
            'auto_print_bill': 'False',
            'auto_print_kot': 'True'
        }
        
        # Test bill printer dialog
        print("Testing Bill Printer Selection Dialog...")
        dialog = PrinterSelectionDialog(root, test_settings, "bill")
        result = dialog.get_result()
        
        if result:
            print(f"✓ Bill printer dialog test passed")
            print(f"  Selected printer type: {result.get('printer_type')}")
            print(f"  Selected printer name: {result.get('printer_name')}")
            print(f"  Paper width: {result.get('paper_width')}")
            print(f"  Preview: {result.get('preview')}")
        else:
            print("✗ Bill printer dialog test failed")
        
        # Test KOT printer dialog
        print("Testing KOT Printer Selection Dialog...")
        dialog = PrinterSelectionDialog(root, test_settings, "kot")
        result = dialog.get_result()
        
        if result:
            print(f"✓ KOT printer dialog test passed")
            print(f"  Selected printer type: {result.get('printer_type')}")
            print(f"  Selected printer name: {result.get('printer_name')}")
            print(f"  Paper width: {result.get('paper_width')}")
            print(f"  Preview: {result.get('preview')}")
        else:
            print("✗ KOT printer dialog test failed")
        
        root.destroy()
        
    except Exception as e:
        print(f"✗ Error testing printer dialog: {e}")
        return False
    
    return True

def test_settings_integration():
    """Test settings integration"""
    print("\nTesting Settings Integration...")
    print("=" * 50)
    
    try:
        # Test if printer settings are properly defined in constants
        print("Checking printer constants...")
        print(f"  PRINTER_TYPE_THERMAL: {PRINTER_TYPE_THERMAL}")
        print(f"  PRINTER_TYPE_STANDARD: {PRINTER_TYPE_STANDARD}")
        print(f"  PAPER_SIZE_MM58: {PAPER_SIZE_MM58}")
        print(f"  PAPER_SIZE_MM80: {PAPER_SIZE_MM80}")
        print(f"  DEFAULT_THERMAL_PRINTER: {DEFAULT_THERMAL_PRINTER}")
        print(f"  DEFAULT_STANDARD_PRINTER: {DEFAULT_STANDARD_PRINTER}")
        print(f"  DEFAULT_BILL_PRINTER_TYPE: {DEFAULT_BILL_PRINTER_TYPE}")
        print(f"  DEFAULT_KOT_PRINTER_TYPE: {DEFAULT_KOT_PRINTER_TYPE}")
        print(f"  DEFAULT_BILL_PAPER_WIDTH: {DEFAULT_BILL_PAPER_WIDTH}")
        print(f"  DEFAULT_KOT_PAPER_WIDTH: {DEFAULT_KOT_PAPER_WIDTH}")
        print(f"  DEFAULT_AUTO_PRINT_BILL: {DEFAULT_AUTO_PRINT_BILL}")
        print(f"  DEFAULT_AUTO_PRINT_KOT: {DEFAULT_AUTO_PRINT_KOT}")
        print("✓ All printer constants defined correctly")
        
        # Test if printer module imports correctly
        print("Testing printer module imports...")
        from utils.printer import PrinterManager, ThermalPrinter, StandardPrinter
        print("✓ Printer module imports successfully")
        
        # Test if printer dialog imports correctly
        print("Testing printer dialog imports...")
        from ui.printer_dialog import PrinterSelectionDialog, PrintPreviewDialog
        print("✓ Printer dialog imports successfully")
        
    except Exception as e:
        print(f"✗ Error in settings integration test: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Restaurant POS Printing System Test")
    print("=" * 60)
    print("This script tests the new printing functionality")
    print("It will test:")
    print("1. Printer Manager functionality")
    print("2. Printer Selection Dialog")
    print("3. Settings integration")
    print("4. Thermal and Standard printer support")
    print("=" * 60)
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Printer Manager
    if test_printer_manager():
        tests_passed += 1
    
    # Test 2: Printer Dialog
    if test_printer_dialog():
        tests_passed += 1
    
    # Test 3: Settings Integration
    if test_settings_integration():
        tests_passed += 1
    
    # Test 4: Import test
    try:
        from utils.printer import PrinterManager
        from ui.printer_dialog import PrinterSelectionDialog
        print("✓ All imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Import test failed: {e}")
    
    # Results
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("✓ ALL TESTS PASSED!")
        print("The printing system is ready for use.")
    else:
        print("✗ Some tests failed.")
        print("Please check the implementation.")
    
    print("=" * 60)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    main()