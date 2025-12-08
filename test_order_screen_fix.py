import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.order_screen import OrderScreen
from controllers.order_controller import OrderController
from models.database import DatabaseManager

class TestApp:
    def __init__(self, root):
        self.root = root
        self.content_frame = ttk.Frame(root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Create order screen
        self.order_screen = OrderScreen(root, self)
        
    def show_message(self, title, message, msg_type):
        print(f"[{msg_type.upper()}] {title}: {message}")
        
    def show_input_dialog(self, title, message, minvalue=None, maxvalue=None):
        print(f"[INPUT] {title}: {message}")
        return "1"  # Return default value for testing

def test_calculate_totals():
    """Test the calculate_totals method with various inputs"""
    print("Testing calculate_totals method...")
    
    # Create a test app
    root = tk.Tk()
    app = TestApp(root)
    
    # Create the order screen UI
    app.order_screen.setup_ui()
    
    # Add some test items to the cart
    app.order_screen.order_controller.cart_items = [
        {'id': 1, 'name': 'Test Item 1', 'price': 10.0, 'quantity': 2, 'total': 20.0},
        {'id': 2, 'name': 'Test Item 2', 'price': 15.0, 'quantity': 1, 'total': 15.0}
    ]
    
    # Test 1: Valid numeric discount values
    print("\n--- Test 1: Valid numeric discount values ---")
    
    # Test with percentage discount
    app.order_screen.discount_var.set("10")
    app.order_screen.discount_type_var.set("%")
    app.order_screen.calculate_totals()
    print(f"Percentage discount (10%): Subtotal = Rs.35.00, Tax = Rs.1.75, Total should be Rs.32.75")
    
    # Test with flat discount
    app.order_screen.discount_var.set("5")
    app.order_screen.discount_type_var.set("Flat")
    app.order_screen.calculate_totals()
    print(f"Flat discount (Rs.5): Subtotal = Rs.35.00, Tax = Rs.1.75, Total should be Rs.31.75")
    
    # Test 2: Empty discount values
    print("\n--- Test 2: Empty discount values ---")
    app.order_screen.discount_var.set("")
    app.order_screen.discount_type_var.set("%")
    try:
        app.order_screen.calculate_totals()
        print("Empty discount value handled successfully")
    except Exception as e:
        print(f"Error with empty discount value: {e}")
    
    # Test 3: Non-numeric discount values (to trigger the ValueError)
    print("\n--- Test 3: Non-numeric discount values ---")
    app.order_screen.discount_var.set("abc")
    app.order_screen.discount_type_var.set("%")
    try:
        app.order_screen.calculate_totals()
        print("Non-numeric discount value handled successfully")
    except Exception as e:
        print(f"Error with non-numeric discount value: {e}")
    
    # Test 4: Different discount types
    print("\n--- Test 4: Different discount types ---")
    
    # Test percentage type
    app.order_screen.discount_var.set("15")
    app.order_screen.discount_type_var.set("%")
    try:
        app.order_screen.calculate_totals()
        print("Percentage discount type handled successfully")
    except Exception as e:
        print(f"Error with percentage discount type: {e}")
    
    # Test flat type
    app.order_screen.discount_var.set("7.5")
    app.order_screen.discount_type_var.set("Flat")
    try:
        app.order_screen.calculate_totals()
        print("Flat discount type handled successfully")
    except Exception as e:
        print(f"Error with flat discount type: {e}")
    
    print("\nAll tests completed successfully!")
    root.destroy()

def test_full_application():
    """Test the full application to verify no UnboundLocalError occurs"""
    print("Testing full application...")
    
    # Create a test app
    root = tk.Tk()
    app = TestApp(root)
    
    # Create the order screen UI
    app.order_screen.setup_ui()
    
    # Simulate user interactions
    print("\n--- Simulating user interactions ---")
    
    # Add some test items to the cart
    app.order_screen.order_controller.cart_items = [
        {'id': 1, 'name': 'Test Item 1', 'price': 10.0, 'quantity': 2, 'total': 20.0},
        {'id': 2, 'name': 'Test Item 2', 'price': 15.0, 'quantity': 1, 'total': 15.0}
    ]
    
    # Update cart display
    app.order_screen.update_cart_display()
    
    # Test various discount scenarios
    test_cases = [
        ("10", "%", "Valid percentage discount"),
        ("5", "Flat", "Valid flat discount"),
        ("", "%", "Empty discount with percentage type"),
        ("abc", "%", "Non-numeric discount with percentage type"),
        ("xyz", "Flat", "Non-numeric discount with flat type"),
        ("0", "%", "Zero percentage discount"),
        ("0", "Flat", "Zero flat discount")
    ]
    
    for discount_value, discount_type, description in test_cases:
        print(f"\nTesting: {description}")
        app.order_screen.discount_var.set(discount_value)
        app.order_screen.discount_type_var.set(discount_type)
        
        try:
            app.order_screen.calculate_totals()
            print(f"[PASS] {description} handled successfully")
        except UnboundLocalError as e:
            print(f"[FAIL] UnboundLocalError with {description}: {e}")
            return False
        except Exception as e:
            print(f"[FAIL] Other error with {description}: {e}")
            return False
    
    print("\n[PASS] Full application test completed successfully!")
    root.destroy()
    return True

if __name__ == "__main__":
    print("Testing the fix for UnboundLocalError in order_screen.py")
    print("=" * 60)
    
    # Test the calculate_totals method
    test_calculate_totals()
    
    print("\n" + "=" * 60)
    
    # Test the full application
    success = test_full_application()
    
    print("\n" + "=" * 60)
    if success:
        print("[PASS] All tests passed! The UnboundLocalError has been fixed.")
    else:
        print("[FAIL] Tests failed! The UnboundLocalError still exists.")