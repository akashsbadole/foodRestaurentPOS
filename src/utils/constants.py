# Constants for Restaurant POS System

# Window dimensions
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 700

# Colors for status indicators
COLOR_AVAILABLE = "#ccffcc"  # Light green
COLOR_OCCUPIED = "#ffcccc"   # Light red
COLOR_LOW_STOCK = "#ffffcc"   # Light yellow
COLOR_OUT_OF_STOCK = "#ffcccc"  # Light red

# Default values
DEFAULT_TAX_RATE = 5.0
DEFAULT_CURRENCY_SYMBOL = "₹"
DEFAULT_RESTAURANT_NAME = "My Restaurant"
DEFAULT_RESTAURANT_ADDRESS = "123 Main Street, City"

# User roles
ROLE_ADMIN = "Admin"
ROLE_CASHIER = "Cashier"

# Order types
ORDER_TYPE_DINE_IN = "Dine-in"
ORDER_TYPE_TAKEAWAY = "Takeaway"

# Table statuses
TABLE_STATUS_AVAILABLE = "Available"
TABLE_STATUS_OCCUPIED = "Occupied"

# Order item statuses
STATUS_PENDING = "Pending"
STATUS_PREPARING = "Preparing"
STATUS_COMPLETED = "Completed"

# Payment modes
PAYMENT_CASH = "Cash"
PAYMENT_CARD = "Card"
PAYMENT_UPI = "UPI"

# Low stock threshold
LOW_STOCK_THRESHOLD = 10

# Grid layout for tables
TABLE_GRID_ROWS = 3
TABLE_GRID_COLS = 4

# Default capacity for tables
DEFAULT_TABLE_CAPACITY = 4

# Design System Colors (based on pos_design_system_specification.md)

# Primary Colors
COLOR_PRIMARY = "#3498db"        # Main actions, highlights, primary buttons
COLOR_PRIMARY_DARK = "#2c3e50"   # Headings, important text, navigation
COLOR_PRIMARY_LIGHT = "#2980b9"  # Hover state for primary elements

# Secondary Colors
COLOR_SECONDARY = "#7f8c8d"      # Secondary text, subtitles
COLOR_SECONDARY_LIGHT = "#95a5a6" # Disabled text, placeholders
COLOR_BACKGROUND_LIGHT = "#f0f0f0" # Main background
COLOR_CARD_WHITE = "#e6e6e6"     # Card backgrounds, content areas

# Dark Theme Colors (for dark mode UI components)
COLOR_BACKGROUND_DARK = "#2c3e50"    # Main dark background
COLOR_CARD_DARK = "#34495e"         # Dark card backgrounds
COLOR_SECONDARY_DARK = "#5d6d7e"    # Dark secondary elements

# Status Colors
COLOR_SUCCESS = "#27ae60"         # Successful operations, available tables
COLOR_SUCCESS_LIGHT = "#ccffcc"   # Background for success states
COLOR_WARNING = "#f39c12"         # Warnings, low stock
COLOR_WARNING_LIGHT = "#ffffcc"   # Background for warning states
COLOR_ERROR = "#e74c3c"           # Errors, out of stock
COLOR_ERROR_LIGHT = "#ffcccc"     # Background for error states
COLOR_INFO = "#3498db"            # Information messages

# Neutral Colors
COLOR_TEXT_PRIMARY = "#2c3e50"    # Main text content
COLOR_TEXT_SECONDARY = "#7f8c8d"  # Secondary text
COLOR_TEXT_DISABLED = "#bdc3c7"   # Disabled elements
COLOR_BORDER_LIGHT = "#ecf0f1"    # Light borders
COLOR_BORDER_MEDIUM = "#bdc3c7"   # Medium borders
COLOR_SHADOW = "#d0d0d0"          # Shadow effects

# Typography
FONT_FAMILY_PRIMARY = "Segoe UI"
FONT_FAMILY_FALLBACK = "Arial"

# Spacing (based on 8px grid)
SPACING_XS = 2     # Fine adjustments, tight spacing
SPACING_S = 3      # Small gaps, related elements
SPACING_M = 5     # Standard spacing, most common
SPACING_L = 10     # Section separation, breathing room
SPACING_XL = 20    # Major sections, screen divisions
SPACING_XXL = 25   # Screen margins, large divisions

# Border Radius
BORDER_RADIUS_SMALL = 2
BORDER_RADIUS_MEDIUM = 4
BORDER_RADIUS_LARGE = 6

# Printer constants
PRINTER_TYPE_THERMAL = "thermal"
PRINTER_TYPE_STANDARD = "standard"

# Paper size constants for thermal printers
PAPER_SIZE_MM58 = 58  # 58mm paper width
PAPER_SIZE_MM80 = 80  # 80mm paper width

# Default printer settings
DEFAULT_THERMAL_PRINTER = ""
DEFAULT_STANDARD_PRINTER = ""
DEFAULT_BILL_PRINTER_TYPE = "standard"
DEFAULT_KOT_PRINTER_TYPE = "thermal"
DEFAULT_BILL_PAPER_WIDTH = 58
DEFAULT_KOT_PAPER_WIDTH = 58
DEFAULT_AUTO_PRINT_BILL = False
DEFAULT_AUTO_PRINT_KOT = True

# PIL import status placeholder
PIL_AVAILABLE = None
PIL_VERSION = None
