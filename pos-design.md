I apologize for overlooking those specific details. You have a very specific workflow implemented (Status tracking, Tabs for multiple orders, Detailed Tax breakdowns, and specific Action buttons).

To make this **compact** without losing **any** functionality, we need to switch from a "Vertical Scroll" layout to a **"Dashboard" (Left/Right) layout**.

Here are the specific instructions for your editor to refactor this Tkinter app while keeping every single feature you showed.

### The New Layout Concept: "Split-Screen"

- **Top Bar:** User Profile & Order Tabs (Navigation).
- **Left Pane (60%):** Data Entry (Customer, Selection, Search, Status).
- **Right Pane (40%):** The "Receipt" (List, Totals, Actions).

---

### Instructions for the Editor

#### 1\. The Top Header & Tab System

- **Current Issue:** The "New Order" title takes up too much space, and the Tabs are in the middle of the screen.
- **Action:** Move the **Tabs** (`+ New Order` button and the blue `ORD...` tabs) to the very top left of the screen, aligned with the "User: admin" label.
- **Result:** This creates a web-browser-style navigation bar.
  - _Left:_ `[+ New Order] [ORD2025... x] [ORD2025... x]`
  - _Right:_ `User: Admin (Admin) [Logout]`

#### 2\. Left Panel: Inputs & Controls (The "Work" Area)

_Create a frame on the left side._

- **A. Customer Details (Compact Grid):**

  - Instead of one long row, make a 2x2 grid.
  - **Row 1:** `Order Type (Radio Buttons)` | `Table Dropdown`
  - **Row 2:** `Customer Name` | `Mobile Number`
  - _Note:_ Use LabelFrames (Group boxes) titled "Customer Info" to make it look organized.

- **B. Item Selection & Search:**

  - Merge the "Add Items" and "Search" rows.
  - **Row 1:** `Category Dropdown` (Width: 30%) | `Item Dropdown` (Width: 40%) | `Quantity Spinbox` (Width: 10%) | `Add Button` (Width: 20%).
  - **Row 2:** `Search Entry` (Fill width) | `Clear Button` | `Clear Order Button` (Move the "Clear Order" button from the far right to here so all inputs are together).

- **C. Order Status Workflow:**

  - You currently have text showing "Status: New, In Progress...".
  - **Action:** Turn this into a **Status Control Strip** at the bottom of the Left Panel.
  - Use clickable buttons or a progress bar visual:
    `[> New]  [> In Progress]  [> Ready]  [v Completed]`
  - Highlight the active status color (e.g., Orange for In Progress).

#### 3\. Right Panel: The Cart & Payment (The "Result" Area)

_Create a frame on the right side._

- **A. The Active Orders List (Treeview):**

  - This should take up the top 60% of the Right Panel.
  - Keep columns: Item, Quantity, Price, Total.
  - **Crucial:** Move the "Current: ORD... | Items: 0..." info strip immediately _below_ the Treeview.

- **B. Financial Breakdown (Bottom Right):**

  - **Current Issue:** The tax list takes up 6 lines of vertical space on the far left.
  - **Action:** Move this to the bottom of the Right Panel. Align the text to the right.
  - Format it like a receipt:
    ```text
    Subtotal:     Rs. 0.00
    CGST (2.5%):  Rs. 0.00
    SGST (2.5%):  Rs. 0.00
    Discount:   - Rs. 0.00
    ----------------------
    TOTAL:        Rs. 0.00  <-- Make this font Size 14 Bold
    ```

- **C. Action Buttons:**

  - Place the three main buttons (`Process Payment`, `Apply Discount`, `Export Order`) in a **horizontal row** at the very bottom of the Right Panel.
  - Make "Process Payment" the largest button (e.g., Green background).

---

### Visual Map for the Editor

You can copy and paste this text diagram to your editor to show exactly where every feature goes:

```text
================================================================================
[+ New Order] [ORD-ID-123 x] [ORD-ID-456 x]           User: Admin [Logout]
================================================================================
| LEFT PANEL (Inputs)                   | RIGHT PANEL (Receipt)                |
|                                       |                                      |
| [ Customer Info Frame ]               | [ Treeview - Items List ]            |
| Order Type: (o) Dine ( ) Takeaway     | | Item A   | 1 | 50  | 50 |        |
| Table: [ T2 v ]                       | | Item B   | 2 | 20  | 40 |        |
| Name: [___________] Mobile: [_______] | |          |   |     |    |        |
|                                       | |_______________________|        |
| [ Item Selection Frame ]              |                                      |
| [Category v] [Item Name v] [Qty] [ADD]| Info: Items: 3 | Status: New         |
| [ Search Items...        ] [ Clear ]  | ------------------------------------ |
|                                       |                                      |
| [ Status Control ]                    |           Subtotal:   100.00         |
| Status: (•) New ( ) In Progress       |           CGST 2.5%:    2.50         |
|         ( ) Ready ( ) Completed       |           SGST 2.5%:    2.50         |
|                                       |           Discount:     0.00         |
|                                       |           ------------------         |
|                                       |           TOTAL:      105.00         |
|                                       |                                      |
|                                       | [Discount] [Export] [PROCESS PAYMENT]|
================================================================================
```

### Why this is better for your Tkinter App:

1.  **No Scrolling:** Everything fits on one 1080p or 720p screen.
2.  **Logical Flow:** Work left (enter data), Look right (verify money).
3.  **Feature Retention:** All your taxes, status indicators, tabs, and export buttons are preserved, just organized into logical "zones".
