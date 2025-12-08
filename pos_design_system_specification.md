# POS Application Design System Specification

## Overview

This design system provides a comprehensive guide for creating a consistent, modern, and professional user interface across all internal screens of the Restaurant POS application. The design builds upon the modernized login screen's styling principles and extends them throughout the application.

## 1. Color Palette

### Primary Colors
Based on the established login screen theme:

- **Primary Blue**: `#3498db` (Main actions, highlights, primary buttons)
- **Primary Dark**: `#2c3e50` (Headings, important text, navigation)
- **Primary Light**: `#2980b9` (Hover state for primary elements)

### Secondary Colors
- **Secondary Gray**: `#7f8c8d` (Secondary text, subtitles)
- **Secondary Light**: `#95a5a6` (Disabled text, placeholders)
- **Background Light**: `#f0f0f0` (Main background)
- **Card White**: `#ffffff` (Card backgrounds, content areas)

### Status Colors
- **Success**: `#27ae60` (Successful operations, available tables)
- **Success Light**: `#ccffcc` (Background for success states)
- **Warning**: `#f39c12` (Warnings, low stock)
- **Warning Light**: `#ffffcc` (Background for warning states)
- **Error**: `#e74c3c` (Errors, out of stock)
- **Error Light**: `#ffcccc` (Background for error states)
- **Info**: `#3498db` (Information messages)

### Neutral Colors
- **Text Primary**: `#2c3e50` (Main text content)
- **Text Secondary**: `#7f8c8d` (Secondary text)
- **Text Disabled**: `#bdc3c7` (Disabled elements)
- **Border Light**: `#ecf0f1` (Light borders)
- **Border Medium**: `#bdc3c7` (Medium borders)
- **Shadow**: `#d0d0d0` (Shadow effects)

## 2. Typography System

### Font Families
- **Primary Font**: `Segoe UI` (Primary interface text)
- **Fallback Font**: `Arial` (System fallback)
- **Monospace Font**: `Consolas` (Code, technical data)

### Font Sizes and Weights

#### Headings
- **H1 - Screen Title**: 24px, Bold (Screens like "Dashboard", "Menu Management")
- **H2 - Section Title**: 18px, Bold (Section headers like "Order Details")
- **H3 - Card Title**: 16px, Semi-Bold (Card titles, widget headers)
- **H4 - Subtitle**: 14px, Medium (Subsections, secondary titles)

#### Body Text
- **Body Large**: 14px, Regular (Primary content, descriptions)
- **Body Normal**: 12px, Regular (Standard text, labels)
- **Body Small**: 10px, Regular (Helper text, captions)

#### Special Text
- **Button Text**: 12px, Semi-Bold
- **Navigation Text**: 12px, Medium
- **Status Text**: 11px, Medium
- **Data Display**: 12px, Regular (Numbers, values)

### Text Hierarchy and Contrast
- **Primary Text**: `#2c3e50` on light backgrounds
- **Secondary Text**: `#7f8c8d` on light backgrounds
- **White Text**: `#ffffff` on dark/colored backgrounds
- **Disabled Text**: `#bdc3c7` on any background
- **Minimum Contrast Ratio**: 4.5:1 for accessibility

## 3. Spacing and Layout Guidelines

### Standard Spacing Scale
- **XS**: 4px (Fine adjustments, tight spacing)
- **S**: 8px (Small gaps, related elements)
- **M**: 16px (Standard spacing, most common)
- **L**: 24px (Section separation, breathing room)
- **XL**: 32px (Major sections, screen divisions)
- **XXL**: 48px (Screen margins, large divisions)

### Component Spacing
- **Button Padding**: 12px horizontal, 8px vertical
- **Card Padding**: 20px all around
- **Form Field Padding**: 10px horizontal, 8px vertical
- **Table Cell Padding**: 8px horizontal, 6px vertical
- **Navigation Item Spacing**: 5px vertical

### Layout Grid System
- **Base Unit**: 8px grid for consistent alignment
- **Column System**: 12-column flexible grid
- **Container Max Width**: 1200px for optimal readability
- **Sidebar Width**: 200px fixed
- **Content Area**: Flexible, minimum 800px

### Responsive Breakpoints
- **Small**: < 768px (Mobile/tablet)
- **Medium**: 768px - 1024px (Tablet)
- **Large**: > 1024px (Desktop)

## 4. Component Design Specifications

### 4.1 Buttons

#### Primary Button
- **Background**: `#3498db`
- **Text**: `#ffffff`, 12px, Semi-Bold
- **Border**: None
- **Padding**: 12px 20px
- **Border Radius**: 4px
- **Hover**: `#2980b9`
- **Active**: `#2472a4`
- **Shadow**: Subtle shadow on hover

#### Secondary Button
- **Background**: `#ffffff`
- **Text**: `#3498db`, 12px, Semi-Bold
- **Border**: 1px solid `#3498db`
- **Padding**: 12px 20px
- **Border Radius**: 4px
- **Hover**: Background `#3498db`, Text `#ffffff`

#### Danger Button
- **Background**: `#e74c3c`
- **Text**: `#ffffff`, 12px, Semi-Bold
- **Border**: None
- **Padding**: 12px 20px
- **Border Radius**: 4px
- **Hover**: `#c0392b`

#### Success Button
- **Background**: `#27ae60`
- **Text**: `#ffffff`, 12px, Semi-Bold
- **Border**: None
- **Padding**: 12px 20px
- **Border Radius**: 4px
- **Hover**: `#229954`

### 4.2 Form Fields

#### Text Entry Fields
- **Background**: `#ffffff`
- **Border**: 1px solid `#bdc3c7`
- **Border Radius**: 4px
- **Padding**: 10px 12px
- **Font**: 12px, Regular
- **Focus Border**: 2px solid `#3498db`
- **Placeholder Text**: `#bdc3c7`

#### Dropdown/Combobox
- **Background**: `#ffffff`
- **Border**: 1px solid `#bdc3c7`
- **Border Radius**: 4px
- **Padding**: 10px 12px
- **Font**: 12px, Regular
- **Arrow**: `#7f8c8d`

#### Radio Buttons & Checkboxes
- **Size**: 16px
- **Selected Color**: `#3498db`
- **Label Spacing**: 8px from control
- **Font**: 12px, Regular

### 4.3 Cards and Containers

#### Standard Card
- **Background**: `#ffffff`
- **Border**: 1px solid `#ecf0f1`
- **Border Radius**: 6px
- **Shadow**: Subtle shadow (2px 2px 8px `#d0d0d0`)
- **Padding**: 20px
- **Margin**: 10px

#### Dashboard Stat Card
- **Background**: `#ffffff`
- **Border**: 1px solid `#ecf0f1`
- **Border Radius**: 8px
- **Shadow**: Subtle shadow
- **Padding**: 24px
- **Accent Border**: 4px solid `#3498db` on top
- **Value Font**: 20px, Bold
- **Label Font**: 12px, Medium, `#7f8c8d`

#### Table Card
- **Background**: `#ffffff`
- **Border**: 1px solid `#ecf0f1`
- **Border Radius**: 6px
- **Shadow**: Subtle shadow
- **Padding**: 16px
- **Header Background**: `#f8f9fa`

### 4.4 Navigation Elements

#### Sidebar Navigation
- **Background**: `#f8f9fa`
- **Button Background**: Transparent
- **Button Text**: `#2c3e50`, 12px, Medium
- **Button Hover**: Background `#e9ecef`
- **Button Active**: Background `#3498db`, Text `#ffffff`
- **Button Padding**: 12px 16px
- **Button Margin**: 0 0 5px 0

#### Top Bar
- **Background**: `#ffffff`
- **Border Bottom**: 1px solid `#ecf0f1`
- **Height**: 60px
- **Restaurant Name**: 18px, Bold, `#2c3e50`
- **User Info**: 12px, Regular, `#7f8c8d`

### 4.5 Tables and Treeviews

#### Header Row
- **Background**: `#f8f9fa`
- **Text**: `#2c3e50`, 10px, Bold
- **Border**: 1px solid `#dee2e6`
- **Padding**: 10px 8px

#### Data Row
- **Background**: `#ffffff`
- **Text**: `#2c3e50`, 10px, Regular
- **Border**: 1px solid `#dee2e6`
- **Padding**: 8px
- **Hover**: Background `#f8f9fa`
- **Selected**: Background `#e3f2fd`

### 4.6 Status Indicators

#### Status Badges
- **Success**: Background `#d4edda`, Text `#155724`
- **Warning**: Background `#fff3cd`, Text `#856404`
- **Error**: Background `#f8d7da`, Text `#721c24`
- **Info**: Background `#d1ecf1`, Text `#0c5460`
- **Border Radius**: 12px
- **Padding**: 4px 8px
- **Font**: 10px, Medium

## 5. Visual Feedback Patterns

### 5.1 Hover Effects
- **Buttons**: Darken background by 10%
- **Cards**: Slight shadow increase
- **Table Rows**: Background change to `#f8f9fa`
- **Navigation**: Background change to `#e9ecef`
- **Links**: Color change to `#2980b9`

### 5.2 Active States
- **Buttons**: Darken background by 20%
- **Navigation**: Background `#3498db`, text `#ffffff`
- **Tabs**: Bottom border 3px solid `#3498db`

### 5.3 Loading Indicators
- **Spinner**: 16px rotating circle, `#3498db`
- **Progress Bar**: Background `#ecf0f1`, Fill `#3498db`
- **Loading Overlay**: Semi-transparent `#ffffff` with spinner

### 5.4 Success/Error Feedback
- **Success Messages**: Green background, icon, auto-dismiss after 3 seconds
- **Error Messages**: Red background, icon, requires user dismissal
- **Warning Messages**: Yellow background, icon, auto-dismiss after 5 seconds
- **Info Messages**: Blue background, icon, auto-dismiss after 4 seconds

## 6. Screen-Specific Design Recommendations

### 6.1 Dashboard Screen
- **Layout**: 4-column grid for stat cards
- **Stat Cards**: Large numbers (20px, Bold), clear labels, trend indicators
- **Recent Orders**: Compact table with time formatting
- **Quick Actions**: Large, colorful buttons with icons
- **Visual Hierarchy**: Emphasize today's sales and order count

### 6.2 Order Screen
- **Layout**: Two-panel design (menu items left, cart right)
- **Menu Items**: Clear categorization, search prominent
- **Cart**: Prominent total, clear itemization
- **Payment Options**: Large, distinct buttons for each payment type
- **Order Summary**: Highlighted box with clear breakdown

### 6.3 Menu Management Screen
- **Layout**: Split view (items left, categories right)
- **Item Cards**: Image preview, clear pricing, stock status
- **Category Management**: Simple list with add/edit/delete
- **Search/Filter**: Prominent search bar, category filters
- **Form Dialogs**: Clean, focused layouts with validation

### 6.4 Tables Screen
- **Layout**: Grid view of table cards
- **Table Cards**: Visual status indicators (green/red)
- **Status Colors**: Green for available, red for occupied
- **Interactive Elements**: Click to toggle status
- **Capacity Display**: Clear and prominent

### 6.5 KOT Screen
- **Layout**: Tabbed interface for different statuses
- **Status Filters**: Clear visual separation
- **Time Display**: Prominent and formatted
- **Action Buttons**: Contextual based on status
- **Priority Indicators**: Visual cues for urgent orders

### 6.6 Reports Screen
- **Layout**: Controls top, data display below
- **Date Pickers**: Clear calendar interface
- **Export Options**: Multiple format options
- **Data Visualization**: Clean tables with proper formatting
- **Summary Cards**: Key metrics highlighted

### 6.7 Inventory Screen
- **Layout**: Search/filter top, table below
- **Stock Status**: Color-coded indicators
- **Low Stock Warnings**: Prominent visual alerts
- **Update Actions**: Quick access buttons
- **Category Organization**: Clear grouping

### 6.8 Settings Screen
- **Layout**: Tabbed interface for different setting types
- **Form Groups**: Logical grouping with clear labels
- **Save Actions**: Prominent save button
- **Validation**: Real-time feedback
- **User Management**: Simple table with action buttons

## 7. Implementation Guidelines

### 7.1 CSS Class Structure
```
.pos-btn-primary     /* Primary buttons */
.pos-btn-secondary   /* Secondary buttons */
.pos-card           /* Standard cards */
.pos-card-stat      /* Dashboard stat cards */
.pos-form-field     /* Form inputs */
.pos-table-header   /* Table headers */
.pos-status-success /* Success status */
.pos-status-error   /* Error status */
```

### 7.2 Component Naming Convention
- Use BEM methodology for CSS classes
- Prefix all classes with `pos-` to avoid conflicts
- Use semantic names that describe purpose, not appearance

### 7.3 Accessibility Guidelines
- All interactive elements must have keyboard access
- Minimum contrast ratio of 4.5:1 for text
- Focus indicators visible on all interactive elements
- ARIA labels for screen readers
- Alt text for all meaningful images

### 7.4 Performance Considerations
- Limit use of shadows and gradients for better performance
- Optimize images and icons for fast loading
- Use CSS transitions instead of JavaScript animations where possible
- Implement lazy loading for large data sets

## 8. Design Tokens

### 8.1 Color Tokens
```css
--color-primary: #3498db;
--color-primary-dark: #2c3e50;
--color-primary-light: #2980b9;
--color-secondary: #7f8c8d;
--color-success: #27ae60;
--color-warning: #f39c12;
--color-error: #e74c3c;
--color-background: #f0f0f0;
--color-card: #ffffff;
--color-text-primary: #2c3e50;
--color-text-secondary: #7f8c8d;
```

### 8.2 Typography Tokens
```css
--font-family-primary: 'Segoe UI', Arial, sans-serif;
--font-size-h1: 24px;
--font-size-h2: 18px;
--font-size-h3: 16px;
--font-size-body: 12px;
--font-weight-bold: 700;
--font-weight-medium: 500;
--font-weight-regular: 400;
```

### 8.3 Spacing Tokens
```css
--spacing-xs: 4px;
--spacing-s: 8px;
--spacing-m: 16px;
--spacing-l: 24px;
--spacing-xl: 32px;
--spacing-xxl: 48px;
```

### 8.4 Border Radius Tokens
```css
--radius-small: 4px;
--radius-medium: 6px;
--radius-large: 8px;
--radius-round: 50%;
```

## 9. Animation and Transitions

### 9.1 Duration
- **Fast**: 150ms (hover states)
- **Normal**: 250ms (panel transitions)
- **Slow**: 350ms (modal dialogs)

### 9.2 Easing
- **Ease-in-out**: Most transitions
- **Ease-out**: Dropdown menus
- **Ease-in**: Tooltips

### 9.3 Common Animations
- **Fade In**: Opacity 0 to 1
- **Slide Down**: Height 0 to auto
- **Scale In**: Transform scale 0.9 to 1
- **Button Press**: Scale 0.95 to 1

## 10. Testing and Validation

### 10.1 Cross-Browser Compatibility
- Chrome (latest)
- Firefox (latest)
- Edge (latest)
- Safari (latest)

### 10.2 Screen Resolution Testing
- 1920x1080 (Desktop)
- 1366x768 (Laptop)
- 768x1024 (Tablet)
- 375x667 (Mobile)

### 10.3 Accessibility Testing
- Keyboard navigation
- Screen reader compatibility
- Color contrast validation
- Focus management

## Conclusion

This design system provides a comprehensive foundation for creating a consistent, modern, and user-friendly interface across all POS application screens. By following these guidelines, developers can ensure that the application maintains a cohesive visual identity while providing an excellent user experience.

The system is designed to be:
- **Consistent**: Unified visual language across all screens
- **Scalable**: Easy to extend and maintain
- **Accessible**: Usable by people with diverse abilities
- **Professional**: Modern business-appropriate appearance
- **Efficient**: Streamlined development process

Regular updates and refinements should be made based on user feedback and evolving design trends to ensure the system remains current and effective.