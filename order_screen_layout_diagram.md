# Order Screen Layout Diagram with Exact Positioning

## Visual Layout Map

```
================================================================================
[+ New Order] [ORD2025...001 x] [ORD2025...002 x]      User: Admin [Logout]
================================================================================
| LEFT PANEL (60%)                              | RIGHT PANEL (40%)          |
|                                              |                            |
| ┌────────────────────────────────────────────┐ | ┌────────────────────────┐ |
| │ Customer Info                              │ │ │ Active Orders          │ │
| │ Order Type: (o) Dine ( ) Takeaway        │ │ │ Item Name    | Qty... │ │
| │ Table: [ T2 ▼ ]                           │ │ │ Burger      | 2     │ │
| │ Name: [_______________]                    │ │ │ Fries       | 1     │ │
| │ Mobile: [___________]                     │ │ │ Coke        | 2     │ │
| └────────────────────────────────────────────┘ │ └────────────────────────┘ │
|                                              | Info: Items: 3 | Status: New |
| ┌────────────────────────────────────────────┐ | ---------------------------- |
| │ Add Items                                  │ │                            |
| │ [Category ▼] [Item Name ▼] [Qty] [ADD]   │ │           Subtotal:   100.00 |
| │ [ Search Items...        ] [Clear]         │ │           CGST 2.5%:    2.50 |
| └────────────────────────────────────────────┘ │           SGST 2.5%:    2.50 |
|                                              │           Discount:     0.00 |
| ┌────────────────────────────────────────────┐ │           ------------------ |
| │ Order Status                               │ │           TOTAL:      105.00 |
| │ [• New] [ In Progress] [ Ready] [Completed]│ │                            |
| └────────────────────────────────────────────┘ │ [Discount] [Export] [PAYMENT] |
|                                              │ └────────────────────────┘ |
================================================================================
```

## Exact Positioning Specifications

### Screen Dimensions
- **Minimum Resolution**: 1280×720 pixels
- **Optimal Resolution**: 1920×1080 pixels
- **Header Height**: 60 pixels (fixed)
- **Available Height**: 660 pixels (720p) or 1020 pixels (1080p)

### Component Dimensions (1280×720 baseline)

#### Top Header (60px height)
```
x: 0, y: 0
width: 1280px, height: 60px
├── Tab Container (left-aligned)
│   ├── x: 10px, y: 15px
│   ├── width: auto, height: 30px
│   └── Contains: [+ New Order] [Order Tabs]
└── User Profile (right-aligned)
    ├── x: 1100px, y: 15px
    ├── width: 170px, height: 30px
    └── Contains: [User: Admin] [Logout]
```

#### Main Content Area (y: 60px to 720px)
```
x: 0, y: 60px
width: 1280px, height: 660px
├── Left Panel (60% width)
│   ├── x: 0px, y: 60px
│   ├── width: 768px, height: 660px
│   └── padding: 10px
└── Right Panel (40% width)
    ├── x: 768px, y: 60px
    ├── width: 512px, height: 660px
    └── padding: 10px
```

### Left Panel Components (768px width, 660px height)

#### Customer Info Frame
```
x: 10px, y: 70px
width: 748px, height: 120px
├── 2×2 Grid Layout
│   ├── Row 0: Order Type | Table
│   │   ├── Order Type: x: 20px, y: 90px, width: 200px
│   │   └── Table: x: 400px, y: 90px, width: 150px
│   └── Row 1: Name | Mobile
│       ├── Name: x: 20px, y: 130px, width: 300px
│       └── Mobile: x: 400px, y: 130px, width: 200px
```

#### Item Selection Frame
```
x: 10px, y: 200px
width: 748px, height: 100px
├── Row 0: Controls
│   ├── Category: x: 20px, y: 220px, width: 150px (30%)
│   ├── Item: x: 180px, y: 220px, width: 300px (40%)
│   ├── Quantity: x: 490px, y: 220px, width: 80px (10%)
│   └── Add: x: 580px, y: 220px, width: 100px (20%)
└── Row 1: Search & Actions
    ├── Search: x: 20px, y: 260px, width: 500px
    ├── Clear: x: 530px, y: 260px, width: 80px
    └── Clear Order: x: 620px, y: 260px, width: 100px
```

#### Status Control Strip
```
x: 10px, y: 310px
width: 748px, height: 60px
├── Status Buttons (4 equal buttons)
│   ├── New: x: 50px, y: 330px, width: 150px
│   ├── In Progress: x: 220px, y: 330px, width: 150px
│   ├── Ready: x: 390px, y: 330px, width: 150px
│   └── Completed: x: 560px, y: 330px, width: 150px
```

### Right Panel Components (512px width, 660px height)

#### Active Orders Frame (60% of right panel height = 396px)
```
x: 778px, y: 70px
width: 492px, height: 396px
├── Treeview
│   ├── x: 788px, y: 90px
│   ├── width: 472px, height: 320px
│   └── Columns: Item(200px), Qty(60px), Price(80px), Total(80px)
└── Info Strip
    ├── x: 788px, y: 420px
    ├── width: 472px, height: 30px
    └── Text: "Items: 3 | Status: New"
```

#### Financial Breakdown Frame (30% of right panel height = 198px)
```
x: 778px, y: 476px
width: 492px, height: 198px
├── Right-aligned labels
│   ├── Subtotal: x: 1100px, y: 496px
│   ├── CGST: x: 1100px, y: 516px
│   ├── SGST: x: 1100px, y: 536px
│   ├── Discount: x: 1100px, y: 556px
│   ├── Separator: x: 900px, y: 576px (width: 200px)
│   └── Total: x: 1100px, y: 596px (bold, larger font)
```

#### Action Buttons Frame (10% of right panel height = 66px)
```
x: 778px, y: 674px
width: 492px, height: 66px
├── Three buttons in horizontal row
│   ├── Discount: x: 800px, y: 694px, width: 120px
│   ├── Export: x: 940px, y: 694px, width: 120px
│   └── Process Payment: x: 1080px, y: 694px, width: 160px (emphasized)
```

## Responsive Scaling

### 1920×1080 Scaling (1.5x)
```
- Header Height: 60px (fixed)
- Left Panel: 1152px width (60% of 1920px)
- Right Panel: 768px width (40% of 1920px)
- Component Heights: Scale proportionally
- Font Sizes: Scale by 1.1x for better readability
```

### 1400×900 Scaling (1.09x)
```
- Header Height: 60px (fixed)
- Left Panel: 840px width (60% of 1400px)
- Right Panel: 560px width (40% of 1400px)
- Component Heights: Adjust to fit 840px available height
- Font Sizes: Standard scale (1.0x)
```

## Component Spacing Guidelines

### Margins
- **Outer Margin**: 10px from screen edges
- **Component Margin**: 10px between major components
- **Internal Padding**: 5px within components

### Button Sizing
- **Standard Button**: Minimum 80px width, 25px height
- **Large Button**: 120-160px width, 30px height
- **Small Button**: 60px width, 20px height

### Input Field Sizing
- **Text Entry**: Minimum 150px width, 20px height
- **Dropdown**: Minimum 120px width, 20px height
- **Spinbox**: 60px width, 20px height

## Color Scheme

### Background Colors
- **Main Background**: #ffffff (white)
- **Panel Background**: #f8f8f8 (light gray)
- **Header Background**: #e1e1e1 (medium gray)
- **Frame Background**: #ffffff (white)

### Text Colors
- **Primary Text**: #000000 (black)
- **Secondary Text**: #666666 (dark gray)
- **Status Text**: Color-coded by status
- **Link Text**: #0078d7 (blue)

### Button Colors
- **Standard Button**: #f0f0f0 (light gray) with #333333 text
- **Active Button**: #0078d7 (blue) with white text
- **Success Button**: #28a745 (green) with white text
- **Warning Button**: #ffc107 (yellow) with black text

### Status Colors
- **New**: #808080 (gray)
- **In Progress**: #FFA500 (orange)
- **Ready**: #008000 (green)
- **Completed**: #0000FF (blue)

## Typography

### Font Families
- **Primary Font**: Arial, sans-serif
- **Monospace Font**: Consolas, monospace (for codes/IDs)

### Font Sizes
- **Header Text**: 16pt, bold
- **Section Titles**: 12pt, bold
- **Standard Text**: 10pt, regular
- **Small Text**: 9pt, regular
- **Button Text**: 9pt, regular
- **Total Amount**: 14pt, bold

### Font Weights
- **Bold**: For headers, totals, active elements
- **Regular**: For standard text and labels
- **Light**: For secondary information

## Interactive Elements

### Hover States
- **Buttons**: Slightly darker background on hover
- **Tabs**: Highlight on hover with underline effect
- **Clickable Labels**: Cursor changes to pointer

### Active States
- **Selected Tab**: Different background color, bold text
- **Active Status Button**: Different background color, bold text
- **Focused Input**: Highlighted border

### Disabled States
- **Buttons**: Grayed out, no hover effect
- **Input Fields**: Grayed background, no interaction
- **Tabs**: Reduced opacity, no click interaction

## Animation and Transitions

### Tab Switching
- **Duration**: 200ms smooth transition
- **Effect**: Fade in/out for content
- **Indicator**: Sliding underline for active tab

### Status Updates
- **Duration**: 150ms color transition
- **Effect**: Smooth color change for status indicators
- **Notification**: Brief flash for status changes

### Button Interactions
- **Duration**: 100ms hover effect
- **Effect**: Smooth color transition
- **Feedback**: Subtle scale effect on click

This exact positioning specification ensures consistent layout across different screen sizes while maintaining the professional appearance and usability requirements outlined in the design document.