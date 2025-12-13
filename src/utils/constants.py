# Constants for Restaurant POS System

# Database
DATABASE_PATH = "restaurant_pos.db"

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

# Design System Colors (Google Material Design inspired)

# Primary Colors (Google Blue)
COLOR_PRIMARY = "#1a73e8"        # Google Blue - Main actions, highlights, primary buttons
COLOR_PRIMARY_DARK = "#1557b0"   # Darker blue - Headings, important text, navigation
COLOR_PRIMARY_LIGHT = "#4285f4"  # Lighter blue - Hover state for primary elements

# Secondary Colors (Google Grey)
COLOR_SECONDARY = "#5f6368"      # Google grey - Secondary text, subtitles
COLOR_SECONDARY_LIGHT = "#80868b" # Light grey - Disabled text, placeholders
COLOR_BACKGROUND_LIGHT = "#f8f9fa" # Google light background - Main background
COLOR_CARD_WHITE = "#ffffff"     # Pure white - Card backgrounds, content areas

# Dark Theme Colors
COLOR_BACKGROUND_DARK = "#202124"    # Google dark background
COLOR_CARD_DARK = "#292a2d"         # Dark card backgrounds
COLOR_SECONDARY_DARK = "#3c4043"    # Dark secondary elements

# Status Colors (Google Material colors)
COLOR_SUCCESS = "#1e8e3e"         # Google Green - Successful operations, available tables
COLOR_SUCCESS_LIGHT = "#e8f5e9"   # Light green background for success states
COLOR_WARNING = "#f9ab00"         # Google Yellow - Warnings, low stock
COLOR_WARNING_LIGHT = "#fff9c4"   # Light yellow background for warning states
COLOR_ERROR = "#d93025"           # Google Red - Errors, out of stock
COLOR_ERROR_LIGHT = "#ffebee"     # Light red background for error states
COLOR_INFO = "#1a73e8"            # Google Blue - Information messages

# Neutral Colors
COLOR_TEXT_PRIMARY = "#202124"    # Google dark grey - Main text content
COLOR_TEXT_SECONDARY = "#5f6368"  # Google medium grey - Secondary text
COLOR_TEXT_DISABLED = "#9aa0a6"   # Google light grey - Disabled elements
COLOR_BORDER_LIGHT = "#e8eaed"    # Google border light - Light borders
COLOR_BORDER_MEDIUM = "#dadce0"   # Google border medium - Medium borders
COLOR_SHADOW = "rgba(60, 64, 67, 0.3)"  # Google shadow - Shadow effects

# Accent Colors (additional Google colors)
COLOR_ACCENT_RED = "#ea4335"      # Google Red
COLOR_ACCENT_YELLOW = "#fbbc04"   # Google Yellow
COLOR_ACCENT_GREEN = "#34a853"    # Google Green
COLOR_ACCENT_BLUE = "#4285f4"     # Google Blue

# Background variations
COLOR_BACKGROUND_GREY = "#f1f3f4" # Subtle grey background
COLOR_HOVER = "#282828"           # Hover state background
COLOR_PRESSED = "#295ba6"         # Pressed state background
COLOR_SELECTED = "#505050"        # Selected state background (light blue)

# Typography
FONT_FAMILY_PRIMARY = "Roboto"    # Google's primary font
FONT_FAMILY_FALLBACK = "Segoe UI, Arial, sans-serif"

# Font Sizes
FONT_SIZE_SMALL = 11
FONT_SIZE_BODY = 13
FONT_SIZE_MEDIUM = 14
FONT_SIZE_LARGE = 16
FONT_SIZE_XLARGE = 20
FONT_SIZE_HEADING = 24

# Left Panel Enhanced Font Sizes
LEFT_PANEL_HEADER = 18           # For section titles (Customer Info, Add Items, Order Status)
LEFT_PANEL_MEDIUM = 16           # For control labels and combo boxes  
LEFT_PANEL_LARGE = 14            # For button text and important info
LEFT_PANEL_REGULAR = 13          # For standard text
LEFT_PANEL_SMALL = 12            # For minor details and placeholders

# Font Weights
FONT_WEIGHT_REGULAR = "normal"
FONT_WEIGHT_MEDIUM = "bold"
FONT_WEIGHT_BOLD = "bold"

# Spacing (based on 8px grid)
SPACING_XS = 2     # Fine adjustments, tight spacing
SPACING_S = 3      # Small gaps, related elements
SPACING_M = 5     # Standard spacing, most common
SPACING_L = 10     # Section separation, breathing room
SPACING_XL = 20    # Major sections, screen divisions
SPACING_XXL = 25   # Screen margins, large divisions

# Border Radius (Google Material Design)
BORDER_RADIUS_SMALL = 4
BORDER_RADIUS_MEDIUM = 8
BORDER_RADIUS_LARGE = 12
BORDER_RADIUS_XLARGE = 16

# Elevation/Shadow levels (Google Material Design)
SHADOW_LEVEL_1 = "0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15)"
SHADOW_LEVEL_2 = "0 1px 2px 0 rgba(60,64,67,0.3), 0 2px 6px 2px rgba(60,64,67,0.15)"
SHADOW_LEVEL_3 = "0 4px 8px 3px rgba(60,64,67,0.15), 0 1px 3px rgba(60,64,67,0.3)"
SHADOW_LEVEL_4 = "0 8px 12px 6px rgba(60,64,67,0.15), 0 4px 4px rgba(60,64,67,0.3)"

# Button styles
BUTTON_PRIMARY_BG = COLOR_PRIMARY
BUTTON_PRIMARY_FG = "#ffffff"
BUTTON_PRIMARY_HOVER = COLOR_PRIMARY_DARK
BUTTON_SECONDARY_BG = "#ffffff"
BUTTON_SECONDARY_FG = COLOR_PRIMARY
BUTTON_SECONDARY_HOVER = COLOR_HOVER
BUTTON_SECONDARY_BORDER = COLOR_BORDER_MEDIUM

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

# Support System Constants

# Support ticket statuses
TICKET_STATUS_OPEN = "Open"
TICKET_STATUS_IN_PROGRESS = "In Progress"
TICKET_STATUS_RESOLVED = "Resolved"
TICKET_STATUS_CLOSED = "Closed"

# Support ticket priorities
PRIORITY_LOW = "Low"
PRIORITY_MEDIUM = "Medium"
PRIORITY_HIGH = "High"
PRIORITY_CRITICAL = "Critical"

# Support ticket categories
TICKET_CATEGORY_GENERAL = "General"
TICKET_CATEGORY_TECHNICAL = "Technical"
TICKET_CATEGORY_BILLING = "Billing"
TICKET_CATEGORY_FEATURE = "Feature Request"
TICKET_CATEGORY_BUG = "Bug Report"

# Bug report severity
SEVERITY_LOW = "Low"
SEVERITY_MEDIUM = "Medium"
SEVERITY_HIGH = "High"
SEVERITY_CRITICAL = "Critical"

# Bug report status
BUG_STATUS_NEW = "New"
BUG_STATUS_ASSIGNED = "Assigned"
BUG_STATUS_IN_PROGRESS = "In Progress"
BUG_STATUS_FIXED = "Fixed"
BUG_STATUS_VERIFIED = "Verified"
BUG_STATUS_CLOSED = "Closed"

# Contact form types
CONTACT_TYPE_GENERAL = "General Inquiry"
CONTACT_TYPE_SUPPORT = "Support Request"
CONTACT_TYPE_FEEDBACK = "Feedback"
CONTACT_TYPE_COMPLAINT = "Complaint"

# Support user roles
SUPPORT_ROLE_USER = "User"
SUPPORT_ROLE_STAFF = "Support Staff"
SUPPORT_ROLE_ADMIN = "Support Admin"

# Attachment types
ATTACHMENT_TYPE_SCREENSHOT = "Screenshot"
ATTACHMENT_TYPE_LOG = "Log File"
ATTACHMENT_TYPE_DOCUMENT = "Document"
ATTACHMENT_TYPE_IMAGE = "Image"
ATTACHMENT_TYPE_OTHER = "Other"

# Support system settings
SUPPORT_EMAIL_NOTIFICATIONS = "support_email_notifications"
SUPPORT_AUTO_ASSIGN_TICKETS = "support_auto_assign_tickets"
SUPPORT_DEFAULT_PRIORITY = "support_default_priority"
SUPPORT_MAX_ATTACHMENT_SIZE = "support_max_attachment_size_mb"
SUPPORT_ALLOWED_FILE_TYPES = "support_allowed_file_types"

# PIL import status placeholder
PIL_AVAILABLE = None
PIL_VERSION = None
