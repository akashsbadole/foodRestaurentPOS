# Retail Module Templates

This directory contains comprehensive frontend templates for all retail modules in the multi-retail POS system.

## Directory Structure

```
retail/
├── base/                           # Base templates for retail modules
│   ├── retail_base.html            # Main base template for all retail types
│   ├── feature_aware_base.html     # Feature-aware base with adaptive rendering
│   └── mobile_base.html           # Mobile-optimized base template
├── restaurant/                      # Restaurant-specific templates
│   ├── dashboard.html
│   ├── tables/
│   ├── menu/
│   ├── reservations/
│   ├── kitchen/
│   └── pos/
├── apparel_footwear/               # Apparel & Footwear templates
│   ├── dashboard.html
│   ├── products/
│   ├── variants/
│   ├── exchanges/
│   └── pos/
├── books_office/                   # Books & Office Supplies templates
│   ├── dashboard.html
│   ├── products/
│   ├── authors/
│   ├── publishers/
│   ├── special_orders/
│   └── pos/
├── food_confectionery/            # Food & Confectionery templates
│   ├── dashboard.html
│   ├── products/
│   ├── batches/
│   ├── recipes/
│   ├── wastage/
│   └── pos/
├── supermarket_groceries/          # Supermarket & Groceries templates
│   ├── dashboard.html
│   ├── produce/
│   ├── weighing/
│   ├── quality/
│   └── pos/
├── hypermarket_departmental/       # Hypermarket & Departmental templates
│   ├── dashboard.html
│   ├── departments/
│   ├── products/
│   ├── promotions/
│   ├── self_checkout/
│   └── pos/
├── specialized_retail/            # Specialized Retail templates
│   ├── dashboard.html
│   ├── custom_products/
│   ├── services/
│   ├── repairs/
│   ├── warranty/
│   ├── rental/
│   ├── consignment/
│   └── pos/
└── multi_store_franchise/          # Multi-Store & Franchise templates
    ├── dashboard.html
    ├── stores/
    ├── transfers/
    ├── franchise/
    ├── reports/
    └── pos/
```

## Feature-Aware Rendering

All templates support feature-aware rendering based on:
- Retail type configuration
- Feature flags
- User permissions
- Tenant settings

## Mobile Optimization

All templates include mobile-responsive design with:
- Touch-optimized interfaces
- Adaptive layouts
- Progressive enhancement
- Offline support

## Template Inheritance

Templates use a hierarchical inheritance structure:
- `base.html` (main system base)
- `retail/base/retail_base.html` (retail-specific base)
- `retail/base/feature_aware_base.html` (feature-aware base)
- Module-specific templates

## Common Components

Reusable components are located in:
- `components/retail/` - Retail-specific components
- `components/common/` - Common UI components
- `components/mobile/` - Mobile-optimized components