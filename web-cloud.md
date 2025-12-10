Excellent! Now I have the complete design specification from pos-design.md. This gives me the exact UI layout and workflow requirements. Let me finalize my comprehensive plan for the Flask web application with the specific split-screen design.

## Final Flask Web Application Plan with Split-Screen Design

Based on the pos-design.md, I'll implement a **split-screen dashboard layout** that perfectly matches the requirements:

### UI Layout Structure (Split-Screen Design)

**Top Header Bar:**

```
[+ New Order] [ORD-ID-123 x] [ORD-ID-456 x]           User: Admin [Logout]
```

**Main Content Area (Split-Screen):**

```
================================================================================
| LEFT PANEL (60%) - Work Area         | RIGHT PANEL (40%) - Receipt Area    |
|                                       |                                      |
| [ Customer Info Frame ]               | [ Treeview - Items List ]            |
| Order Type: (o) Dine ( ) Takeaway     | | Item A   | 1 | 50  | 50 |        |
| Table: [ T2 v ]                       | | Item B   | 2 | 20  | 40 |        |
| Name: [___________] Mobile: [_______] | |_______________________|        |
|                                       |                                      |
| [ Item Selection Frame ]              | Info: Items: 3 | Status: New         |
| [Category v] [Item Name v] [Qty] [ADD]| ------------------------------------ |
| [ Search Items...        ] [ Clear ]  |                                      |
|                                       |           Subtotal:   100.00         |
| [ Status Control ]                    |           CGST 2.5%:    2.50         |
| Status: (•) New ( ) In Progress       |           SGST 2.5%:    2.50         |
|         ( ) Ready ( ) Completed       |           Discount:     0.00         |
|                                       |           ------------------         |
|                                       |           TOTAL:      105.00         |
|                                       |                                      |
|                                       | [Discount] [Export] [PROCESS PAYMENT]|
================================================================================
```

### Key Implementation Features:

**1. Multi-Order Tab System**

- Browser-style tabs at the top
- Each tab maintains independent order state
- Real-time tab switching without page reload
- Auto-save draft orders

**2. Split-Screen Responsive Design**

- Left panel (60%): Input controls and work area
- Right panel (40%): Receipt and payment area
- Mobile-responsive: Stacks vertically on small screens

**3. Real-Time Features**

- Live cart updates with HTMX
- Real-time status tracking
- Instant tax calculations
- KOT updates without refresh

**4. GST Compliance**

- Precise CGST (2.5%) and SGST (2.5%) calculations
- GST invoice format
- GSTR-1 export capability
- Tax breakdown display

### Technical Implementation Plan:

**Frontend Architecture:**

```javascript
// Alpine.js for multi-order state management
Alpine.data("posApp", () => ({
  activeOrders: {}, // Multiple order tabs
  currentOrderId: null, // Active tab
  cart: {}, // Cart items per order
  gst: {}, // GST calculations
  status: {}, // Order status tracking
}));
```

**Backend API Endpoints:**

```python
# HTMX endpoints for real-time updates
/api/orders/new          # Create new order tab
/api/orders/:id/items    # Add/update items
/api/orders/:id/gst      # Calculate GST
/api/orders/:id/status   # Update status
/api/kot/pending         # Get pending KOT items
```

**Responsive CSS Strategy:**

```css
/* Desktop: Split-screen */
@media (min-width: 1024px) {
  .left-panel {
    width: 60%;
  }
  .right-panel {
    width: 40%;
  }
}

/* Tablet: Compact split */
@media (min-width: 768px) and (max-width: 1023px) {
  .left-panel {
    width: 55%;
  }
  .right-panel {
    width: 45%;
  }
}

/* Mobile: Stacked */
@media (max-width: 767px) {
  .left-panel,
  .right-panel {
    width: 100%;
  }
}
```

### Enhanced Project Structure:

```
web_cloud/
├── app.py
├── config.py
├── requirements.txt
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── category.py
│   ├── menu_item.py
│   ├── table.py
│   ├── order.py              # With GST fields
│   ├── order_item.py
│   ├── payment.py
│   └── settings.py
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── dashboard.py
│   ├── orders.py             # Multi-order management
│   ├── menu.py
│   ├── tables.py
│   ├── inventory.py
│   ├── kot.py
│   ├── reports.py
│   ├── gst.py
│   └── api.py                # HTMX endpoints
├── templates/
│   ├── base.html
│   ├── auth/
│   │   └── login.html
│   ├── dashboard/
│   │   └── index.html
│   ├── orders/
│   │   ├── new.html         # Split-screen main order page
│   │   ├── tabs.html        # Tab navigation component
│   │   ├── left_panel.html  # Work area
│   │   ├── right_panel.html # Receipt area
│   │   └── details.html
│   ├── menu/
│   ├── tables/
│   ├── inventory/
│   ├── kot/
│   ├── reports/
│   │   ├── sales.html
│   │   ├── gst.html
│   │   └── gstr1.html
│   └── partials/
│       ├── order_tab.html
│       ├── customer_info.html
│       ├── item_selection.html
│       ├── status_control.html
│       ├── cart_items.html
│       ├── gst_breakdown.html
│       └── kot_items.html
├── static/
│   ├── css/
│   │   ├── bootstrap.min.css
│   │   └── pos.css          # Split-screen layout
│   └── js/
│       ├── alpine.min.js
│       ├── htmx.min.js
│       ├── pos.js           # Multi-order state
│       ├── tabs.js          # Tab management
│       ├── gst.js           # GST calculations
│       └── cart.js          # Cart operations
└── utils/
    ├── __init__.py
    ├── database.py
    ├── helpers.py
    ├── validators.py
    └── gst_calculator.py
```

### Implementation Phases:

**Phase 1: Foundation**

- Flask setup with split-screen template
- Authentication system
- Base responsive layout

**Phase 2: Multi-Order System**

- Tab navigation with Alpine.js
- Order state management
- Session persistence

**Phase 3: Split-Screen Interface**

- Left panel: Customer info, item selection, status control
- Right panel: Cart display, GST breakdown, payment actions
- Real-time updates with HTMX

**Phase 4: Menu & GST Integration**

- Menu management with search
- GST calculation engine
- Tax-compliant invoicing

**Phase 5: Advanced Features**

- KOT system with real-time updates
- GST reports (Daily/Monthly/GSTR-1)
- Export functionality

**Phase 6: Mobile Optimization**

- Responsive split-screen design
- Touch-friendly interactions
- Performance optimization

The result will be a modern, web-based POS system that perfectly replicates the desktop functionality while adding web benefits like accessibility from any device, real-time updates, and enhanced mobile support.

Are you ready for me to proceed with implementing this split-screen Flask POS application with all the specified features?
