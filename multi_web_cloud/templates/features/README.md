# Feature-Specific Templates

This directory contains comprehensive feature-specific templates for all 19 feature categories of the multi-retail POS system.

## Directory Structure

```
features/
├── universal_core/           # Universal Core Features (12 features)
├── billing_taxation/         # Billing & Taxation (9 features)
├── inventory_management/      # Inventory Management (11 features)
├── customer_features/        # Customer Features (9 features)
├── apparel_footwear/         # Apparel & Footwear Specific (8 features)
├── books_office/             # Books & Office Supplies (5 features)
├── food_confectionery/       # Food & Confectionery (7 features)
├── hypermarket_departmental/ # Hypermarket & Departmental Store (7 features)
├── specialized_retail/      # Specialized Retail (6 features)
├── supermarket_groceries/    # Supermarket & Groceries (6 features)
├── payment_settlement/       # Payment & Settlement (10 features)
├── discounts_promotions/      # Discounts & Promotions (8 features)
├── returns_exchanges/        # Returns & Exchanges (7 features)
├── reporting_analytics/      # Reporting & Analytics (12 features)
├── user_management/          # User Management & Security (11 features)
├── hardware_integration/      # Hardware Integration (8 features)
├── multi_store_franchise/    # Multi-Store & Franchise (5 features)
├── online_integration/       # Online Integration (5 features)
└── additional_features/      # Additional Features (7 features)
```

## Template Types

Each feature category contains the following template types:

1. **Main Interface** - Primary user interface for the feature
2. **List/View** - Data listing and viewing templates
3. **Create/Edit Form** - Data entry and editing forms
4. **Settings/Configuration** - Feature configuration templates
5. **Reports/Analytics** - Feature-specific reporting (if applicable)

## Feature Flag Integration

All templates use the feature flag system for conditional rendering:

```html
{% if feature_manager.is_enabled('FEATURE_NAME', tenant_id) %}
    <!-- Feature-specific content -->
{% endif %}
```

## Usage

Templates are automatically loaded based on enabled features for each tenant. The system uses the feature flag manager to determine which templates to render and which functionality to expose.

## Template Components

All templates extend the base feature-aware template and include:

- Feature-aware navigation
- Conditional rendering based on feature flags
- Retail type specific styling
- Responsive design for mobile/tablet/desktop
- Accessibility features
- Performance optimizations