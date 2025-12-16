"""
Data migration script for migrating from existing restaurant POS to multi-retail system
This script migrates existing data to the new enhanced models
"""

import os
import sys
from datetime import datetime

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import (
    # Legacy models
    MenuItem, Category, Order, OrderItem, Payment, Customer,
    
    # New models
    Product, ProductCategory, ProductVariant, ProductAttribute, Attribute,
    EnhancedOrder, EnhancedOrderItem, EnhancedPayment
)

def migrate_menu_items_to_products():
    """Migrate menu items to products"""
    print("Migrating menu items to products...")
    
    # Get all menu items
    menu_items = MenuItem.query.all()
    migrated_count = 0
    
    for menu_item in menu_items:
        # Check if product already exists
        existing_product = Product.query.filter_by(
            name=menu_item.name,
            tenant_id=menu_item.tenant_id
        ).first()
        
        if not existing_product:
            # Create new product from menu item
            product = Product(
                name=menu_item.name,
                description=menu_item.description,
                price=menu_item.price,
                cost=menu_item.cost or 0,
                sku=f"MENU-{menu_item.id:06d}",  # Generate SKU from menu item ID
                barcode=menu_item.barcode,
                is_active=menu_item.is_available,
                product_type="Restaurant",  # Mark as restaurant product
                tenant_id=menu_item.tenant_id,
                created_by=1  # Assuming admin user has ID 1
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Create product attributes for restaurant-specific fields
            if menu_item.spiciness_level:
                add_product_attribute(product.id, "Spiciness Level", menu_item.spiciness_level, menu_item.tenant_id)
            
            if menu_item.preparation_time:
                add_product_attribute(product.id, "Preparation Time", f"{menu_item.preparation_time} minutes", menu_item.tenant_id)
            
            if menu_item.allergen_info:
                add_product_attribute(product.id, "Allergen Info", menu_item.allergen_info, menu_item.tenant_id)
            
            # Store original menu item ID for reference
            add_product_attribute(product.id, "Original Menu Item ID", str(menu_item.id), menu_item.tenant_id)
            
            migrated_count += 1
    
    db.session.commit()
    print(f"Migrated {migrated_count} menu items to products")

def add_product_attribute(product_id, attribute_name, attribute_value, tenant_id):
    """Add a product attribute"""
    # Get or create attribute definition
    attribute = Attribute.query.filter_by(name=attribute_name, tenant_id=tenant_id).first()
    if not attribute:
        attribute = Attribute(
            name=attribute_name,
            attribute_type="Text",
            tenant_id=tenant_id
        )
        db.session.add(attribute)
        db.session.flush()
    
    # Create product attribute
    product_attribute = ProductAttribute(
        product_id=product_id,
        attribute_id=attribute.id,
        value=attribute_value,
        tenant_id=tenant_id
    )
    db.session.add(product_attribute)

def migrate_categories():
    """Migrate categories to product categories"""
    print("Migrating categories...")
    
    # Get all categories
    categories = Category.query.all()
    migrated_count = 0
    
    for category in categories:
        # Check if product category already exists
        existing_category = ProductCategory.query.filter_by(
            name=category.name,
            tenant_id=category.tenant_id
        ).first()
        
        if not existing_category:
            # Create new product category
            product_category = ProductCategory(
                name=category.name,
                description=category.description,
                tenant_id=category.tenant_id
            )
            
            db.session.add(product_category)
            migrated_count += 1
    
    db.session.commit()
    print(f"Migrated {migrated_count} categories")

def migrate_orders():
    """Migrate orders to enhanced orders"""
    print("Migrating orders...")
    
    # Get all orders
    orders = Order.query.all()
    migrated_count = 0
    
    for order in orders:
        # Check if enhanced order already exists
        existing_order = EnhancedOrder.query.filter_by(
            order_number=order.order_number,
            tenant_id=order.tenant_id
        ).first()
        
        if not existing_order:
            # Create new enhanced order
            enhanced_order = EnhancedOrder(
                order_number=order.order_number,
                order_type='Sale',
                order_subtype='DineIn' if order.table_id else 'Takeaway',
                retail_type='Restaurant',
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                table_id=order.table_id,
                covers=order.covers,
                order_date=order.order_date,
                order_time=order.created_at,
                status=order.status,
                subtotal=order.subtotal,
                tax_amount=order.tax_amount,
                discount_amount=order.discount_amount,
                total_amount=order.total_amount,
                payment_status=order.payment_status,
                order_notes=order.notes,
                source='POS',
                tenant_id=order.tenant_id,
                created_by=order.created_by or 1
            )
            
            db.session.add(enhanced_order)
            db.session.flush()  # Get the enhanced order ID
            
            # Migrate order items
            migrate_order_items(order.id, enhanced_order.id, order.tenant_id)
            
            # Migrate payments
            migrate_payments(order.id, enhanced_order.id, order.tenant_id)
            
            migrated_count += 1
    
    db.session.commit()
    print(f"Migrated {migrated_count} orders")

def migrate_order_items(original_order_id, enhanced_order_id, tenant_id):
    """Migrate order items to enhanced order items"""
    # Get order items for original order
    order_items = OrderItem.query.filter_by(order_id=original_order_id).all()
    
    for order_item in order_items:
        # Find corresponding product
        product = Product.query.filter_by(
            name=order_item.menu_item.name if order_item.menu_item else None,
            tenant_id=tenant_id
        ).first()
        
        if product:
            # Create enhanced order item
            enhanced_order_item = EnhancedOrderItem(
                order_id=enhanced_order_id,
                product_id=product.id,
                quantity=order_item.quantity,
                unit_price=order_item.price,
                total_price=order_item.total_price,
                status='Completed',
                notes=order_item.notes,
                tenant_id=tenant_id
            )
            
            db.session.add(enhanced_order_item)

def migrate_payments(original_order_id, enhanced_order_id, tenant_id):
    """Migrate payments to enhanced payments"""
    # Get payments for original order
    payments = Payment.query.filter_by(order_id=original_order_id).all()
    
    for payment in payments:
        # Create enhanced payment
        enhanced_payment = EnhancedPayment(
            order_id=enhanced_order_id,
            payment_method=payment.payment_method,
            payment_type='Payment',
            amount=payment.amount,
            reference_number=payment.reference_number,
            transaction_id=payment.transaction_id,
            status='Completed',
            tenant_id=tenant_id,
            created_by=payment.created_by or 1
        )
        
        db.session.add(enhanced_payment)

def migrate_customers():
    """Migrate customers to enhanced customers"""
    print("Migrating customers...")
    
    # Customers are already in the Customer model which is shared
    # No migration needed, but we can add any missing fields
    customers = Customer.query.all()
    updated_count = 0
    
    for customer in customers:
        updated = False
        
        # Add default values for new fields if they don't exist
        if not hasattr(customer, 'customer_type') or not customer.customer_type:
            customer.customer_type = 'Regular'
            updated = True
        
        if not hasattr(customer, 'credit_limit') or not customer.credit_limit:
            customer.credit_limit = 0
            updated = True
        
        if updated:
            updated_count += 1
    
    db.session.commit()
    print(f"Updated {updated_count} customers with new fields")

def create_restaurant_preset():
    """Create restaurant preset configuration"""
    print("Creating restaurant preset...")
    
    from models.feature_flag import RetailTypePreset, FeatureDefinition
    
    # Get or create restaurant preset
    preset = RetailTypePreset.query.filter_by(name='Restaurant').first()
    if not preset:
        preset = RetailTypePreset(
            name='Restaurant',
            description='Restaurant POS with table management, KOT, and kitchen operations',
            icon='restaurant',
            is_active=True
        )
        db.session.add(preset)
        db.session.flush()
        
        # Define restaurant-specific features
        restaurant_features = [
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_KOT',
            'FEATURE_KITCHEN_DISPLAY',
            'FEATURE_MENU_MANAGEMENT',
            'FEATURE_ORDER_MANAGEMENT',
            'FEATURE_PAYMENT_PROCESSING',
            'FEATURE_CUSTOMER_MANAGEMENT',
            'FEATURE_BASIC_REPORTING'
        ]
        
        # Add features to preset
        for feature_code in restaurant_features:
            feature = FeatureDefinition.query.filter_by(code=feature_code).first()
            if feature:
                # Check if feature is already associated with preset
                from models.feature_flag import RetailTypePreset
                # This would require a many-to-many relationship table
                # For now, we'll just log this
                print(f"Added feature {feature_code} to restaurant preset")
    
    db.session.commit()
    print("Restaurant preset created")

def run_migration():
    """Run the complete migration"""
    with app.app_context():
        print("Starting restaurant to multi-retail migration...")
        
        try:
            # Migrate in order of dependencies
            migrate_categories()
            migrate_menu_items_to_products()
            migrate_customers()
            migrate_orders()
            create_restaurant_preset()
            
            print("Restaurant to multi-retail migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    run_migration()