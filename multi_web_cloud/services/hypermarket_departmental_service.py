"""
Hypermarket & Departmental Store service layer with comprehensive business logic
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from decimal import Decimal
from models import db
from models.hypermarket_departmental import (
    Department, HypermarketProduct, ShoppingCartItem, AbandonedCart, 
    DepartmentPromotion, DepartmentSales, SelfCheckout, QueueManagement
)
from utils.feature_flag_manager import feature_manager


class HypermarketDepartmentalService:
    """Service layer for hypermarket and departmental store operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a hypermarket feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Department Management Methods
    
    def create_department(self, department_data: Dict[str, Any], 
                      user_id: Optional[str] = None) -> Tuple[bool, Optional[Department], str]:
        """Create a new department"""
        try:
            department = Department(
                department_code=department_data['department_code'],
                name=department_data['name'],
                description=department_data.get('description'),
                parent_department_id=department_data.get('parent_department_id'),
                level=department_data.get('level', 1),
                sort_order=department_data.get('sort_order', 0),
                floor_number=department_data.get('floor_number'),
                section=department_data.get('section'),
                aisle_range=department_data.get('aisle_range'),
                manager_name=department_data.get('manager_name'),
                manager_contact=department_data.get('manager_contact'),
                assistant_manager=department_data.get('assistant_manager'),
                opening_time=department_data.get('opening_time'),
                closing_time=department_data.get('closing_time'),
                operating_days=department_data.get('operating_days', []),
                monthly_sales_target=Decimal(str(department_data.get('monthly_sales_target', 0))),
                monthly_footfall_target=department_data.get('monthly_footfall_target'),
                average_transaction_value_target=Decimal(str(department_data.get('average_transaction_value_target', 0))),
                is_active=department_data.get('is_active', True),
                is_seasonal=department_data.get('is_seasonal', False),
                season_start_date=datetime.fromisoformat(department_data['season_start_date']).date() if department_data.get('season_start_date') else None,
                season_end_date=datetime.fromisoformat(department_data['season_end_date']).date() if department_data.get('season_end_date') else None,
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(department)
            db.session.commit()
            return True, department, "Department created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating department: {e}")
            return False, None, str(e)
    
    def get_departments(self, filters: Optional[Dict[str, Any]] = None) -> List[Department]:
        """Get departments with optional filters"""
        try:
            query = Department.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'parent_department_id' in filters:
                    query = query.filter(Department.parent_department_id == filters['parent_department_id'])
                if 'level' in filters:
                    query = query.filter(Department.level == filters['level'])
                if 'floor_number' in filters:
                    query = query.filter(Department.floor_number == filters['floor_number'])
                if 'manager_name' in filters:
                    query = query.filter(Department.manager_name.ilike(f"%{filters['manager_name']}%"))
            
            return query.order_by(Department.sort_order, Department.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting departments: {e}")
            return []
    
    def get_department_hierarchy(self) -> List[Dict[str, Any]]:
        """Get department hierarchy structure"""
        try:
            # Get root departments (level 1)
            root_departments = Department.query.filter_by(
                tenant_id=self.tenant_id,
                parent_department_id=None,
                is_active=True
            ).order_by(Department.sort_order, Department.name).all()
            
            def build_tree(departments):
                tree = []
                for department in departments:
                    children = Department.query.filter_by(
                        parent_department_id=department.id,
                        is_active=True
                    ).order_by(Department.sort_order, Department.name).all()
                    
                    node = {
                        'department': department.to_dict(),
                        'children': build_tree(children)
                    }
                    tree.append(node)
                return tree
            
            return build_tree(root_departments)
            
        except Exception as e:
            current_app.logger.error(f"Error getting department hierarchy: {e}")
            return []
    
    # Product Management Methods
    
    def create_hypermarket_product(self, product_data: Dict[str, Any], 
                               user_id: Optional[str] = None) -> Tuple[bool, Optional[HypermarketProduct], str]:
        """Create a new hypermarket product"""
        try:
            product = HypermarketProduct(
                product_id=product_data['product_id'],
                sku_base=product_data['sku_base'],
                name=product_data['name'],
                description=product_data.get('description'),
                primary_department_id=product_data['primary_department_id'],
                secondary_departments=product_data.get('secondary_departments', []),
                categories=product_data.get('categories', []),
                tags=product_data.get('tags', []),
                unit_price=Decimal(str(product_data['unit_price'])),
                cost_price=Decimal(str(product_data.get('cost_price', 0))),
                wholesale_price=Decimal(str(product_data.get('wholesale_price', 0))),
                bulk_pricing_tiers=product_data.get('bulk_pricing_tiers', []),
                promotional_price=Decimal(str(product_data.get('promotional_price', 0))),
                promotional_start_date=datetime.fromisoformat(product_data['promotional_start_date']).date() if product_data.get('promotional_start_date') else None,
                promotional_end_date=datetime.fromisoformat(product_data['promotional_end_date']).date() if product_data.get('promotional_end_date') else None,
                current_stock=product_data.get('current_stock', 0),
                minimum_stock_level=product_data.get('minimum_stock_level', 5),
                maximum_stock_level=product_data.get('maximum_stock_level', 1000),
                reorder_point=product_data.get('reorder_point', 10),
                weight=product_data.get('weight'),
                dimensions=product_data.get('dimensions', {}),
                volume=product_data.get('volume'),
                package_type=product_data.get('package_type'),
                units_per_package=product_data.get('units_per_package'),
                package_quantity=product_data.get('package_quantity'),
                primary_supplier_id=product_data.get('primary_supplier_id'),
                supplier_sku=product_data.get('supplier_sku'),
                alternate_suppliers=product_data.get('alternate_suppliers', []),
                barcode=product_data.get('barcode'),
                upc=product_data.get('upc'),
                ean=product_data.get('ean'),
                is_active=product_data.get('is_active', True),
                is_perishable=product_data.get('is_perishable', False),
                is_fragile=product_data.get('is_fragile', False),
                is_hazardous=product_data.get('is_hazardous', False),
                is_age_restricted=product_data.get('is_age_restricted', False),
                minimum_age=product_data.get('minimum_age'),
                tax_category=product_data.get('tax_category'),
                tax_rate=Decimal(str(product_data.get('tax_rate', 0))),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(product)
            db.session.commit()
            return True, product, "Product created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating hypermarket product: {e}")
            return False, None, str(e)
    
    def get_hypermarket_products(self, filters: Optional[Dict[str, Any]] = None) -> List[HypermarketProduct]:
        """Get hypermarket products with optional filters"""
        try:
            query = HypermarketProduct.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'primary_department_id' in filters:
                    query = query.filter(HypermarketProduct.primary_department_id == filters['primary_department_id'])
                if 'categories' in filters:
                    # Filter for products that have any of the specified categories
                    categories = filters['categories']
                    if categories:
                        category_filter = HypermarketProduct.categories.contains(categories)
                        query = query.filter(category_filter)
                if 'tags' in filters:
                    # Filter for products that have any of the specified tags
                    tags = filters['tags']
                    if tags:
                        tag_filter = HypermarketProduct.tags.contains(tags)
                        query = query.filter(tag_filter)
                if 'is_perishable' in filters:
                    query = query.filter(HypermarketProduct.is_perishable == filters['is_perishable'])
                if 'is_age_restricted' in filters:
                    query = query.filter(HypermarketProduct.is_age_restricted == filters['is_age_restricted'])
                if 'min_price' in filters:
                    query = query.filter(HypermarketProduct.unit_price >= Decimal(str(filters['min_price'])))
                if 'max_price' in filters:
                    query = query.filter(HypermarketProduct.unit_price <= Decimal(str(filters['max_price'])))
                if 'in_stock' in filters and filters['in_stock']:
                    query = query.filter(HypermarketProduct.current_stock > 0)
            
            return query.order_by(HypermarketProduct.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting hypermarket products: {e}")
            return []
    
    def get_product_by_sku(self, sku: str) -> Optional[HypermarketProduct]:
        """Get a product by SKU"""
        try:
            return HypermarketProduct.query.filter_by(
                sku_base=sku,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting product by SKU: {e}")
            return None
    
    # Shopping Cart Management Methods
    
    def create_shopping_cart_item(self, cart_data: Dict[str, Any], 
                                user_id: Optional[str] = None) -> Tuple[bool, Optional[ShoppingCartItem], str]:
        """Create a new shopping cart item"""
        try:
            # Check if product exists
            product = HypermarketProduct.query.filter_by(
                id=cart_data['product_id'],
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not product:
                return False, None, "Product not found"
            
            cart_item = ShoppingCartItem(
                cart_id=cart_data['cart_id'],
                product_id=cart_data['product_id'],
                quantity=int(cart_data['quantity']),
                unit_price=product.get_effective_price(int(cart_data.get('quantity', 1))),
                customer_id=cart_data.get('customer_id'),
                session_id=cart_data.get('session_id'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            # Calculate total price
            cart_item.calculate_total_price()
            
            db.session.add(cart_item)
            db.session.commit()
            return True, cart_item, "Cart item added successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating shopping cart item: {e}")
            return False, None, str(e)
    
    def get_cart_items(self, cart_id: str) -> List[ShoppingCartItem]:
        """Get items in a shopping cart"""
        try:
            return ShoppingCartItem.query.filter_by(
                cart_id=cart_id,
                tenant_id=self.tenant_id,
                is_active=True
            ).order_by(ShoppingCartItem.added_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting cart items: {e}")
            return []
    
    def update_cart_item(self, item_id: int, quantity: int) -> Tuple[bool, str]:
        """Update cart item quantity"""
        try:
            item = ShoppingCartItem.query.filter_by(
                id=item_id,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not item:
                return False, "Cart item not found"
            
            item.quantity = quantity
            item.calculate_total_price()
            item.last_updated = datetime.utcnow()
            
            db.session.commit()
            return True, "Cart item updated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating cart item: {e}")
            return False, str(e)
    
    # Abandoned Cart Management Methods
    
    def create_abandoned_cart(self, cart_data: Dict[str, Any], 
                           user_id: Optional[str] = None) -> Tuple[bool, Optional[AbandonedCart], str]:
        """Create an abandoned cart record"""
        try:
            abandoned_cart = AbandonedCart(
                cart_id=cart_data['cart_id'],
                customer_id=cart_data.get('customer_id'),
                session_id=cart_data.get('session_id'),
                total_items=cart_data.get('total_items', 0),
                total_value=Decimal(str(cart_data.get('total_value', 0))),
                abandoned_at=datetime.fromisoformat(cart_data['abandoned_at']) if cart_data.get('abandoned_at') else datetime.utcnow(),
                abandonment_reason=cart_data.get('abandonment_reason'),
                abandonment_stage=cart_data.get('abandonment_stage'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(abandoned_cart)
            db.session.commit()
            return True, abandoned_cart, "Abandoned cart created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating abandoned cart: {e}")
            return False, None, str(e)
    
    def get_abandoned_carts(self, filters: Optional[Dict[str, Any]] = None) -> List[AbandonedCart]:
        """Get abandoned carts with optional filters"""
        try:
            query = AbandonedCart.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'customer_id' in filters:
                    query = query.filter(AbandonedCart.customer_id == filters['customer_id'])
                if 'recovery_status' in filters:
                    query = query.filter(AbandonedCart.recovery_status == filters['recovery_status'])
                if 'abandoned_after' in filters:
                    abandoned_after = datetime.fromisoformat(filters['abandoned_after'])
                    query = query.filter(AbandonedCart.abandoned_at >= abandoned_after)
                if 'abandoned_before' in filters:
                    abandoned_before = datetime.fromisoformat(filters['abandoned_before'])
                    query = query.filter(AbandonedCart.abandoned_at <= abandoned_before)
                if 'min_value' in filters:
                    query = query.filter(AbandonedCart.total_value >= Decimal(str(filters['min_value'])))
                if 'max_value' in filters:
                    query = query.filter(AbandonedCart.total_value <= Decimal(str(filters['max_value'])))
            
            return query.order_by(AbandonedCart.abandoned_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting abandoned carts: {e}")
            return []
    
    def process_cart_recovery(self, cart_id: str, recovery_type: str, 
                           user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Process cart recovery (email or SMS)"""
        try:
            cart = AbandonedCart.query.filter_by(
                cart_id=cart_id,
                tenant_id=self.tenant_id
            ).first()
            
            if not cart:
                return False, "Abandoned cart not found"
            
            now = datetime.utcnow()
            
            if recovery_type == 'email':
                cart.recovery_email_sent = True
                cart.recovery_email_sent_at = now
            elif recovery_type == 'sms':
                cart.recovery_sms_sent = True
                cart.recovery_sms_sent_at = now
            
            if cart.recovery_status == 'Not Attempted':
                cart.recovery_status = f"{recovery_type.title()} Sent"
            
            db.session.commit()
            return True, f"Cart recovery {recovery_type} processed successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing cart recovery: {e}")
            return False, str(e)
    
    # Department Promotion Methods
    
    def create_department_promotion(self, promotion_data: Dict[str, Any], 
                                user_id: Optional[str] = None) -> Tuple[bool, Optional[DepartmentPromotion], str]:
        """Create a new department promotion"""
        try:
            promotion = DepartmentPromotion(
                promotion_code=promotion_data['promotion_code'],
                name=promotion_data['name'],
                description=promotion_data.get('description'),
                department_id=promotion_data['department_id'],
                start_date=datetime.fromisoformat(promotion_data['start_date']).date(),
                end_date=datetime.fromisoformat(promotion_data['end_date']).date(),
                promotion_type=promotion_data['promotion_type'],
                discount_value=Decimal(str(promotion_data['discount_value'])),
                minimum_purchase=Decimal(str(promotion_data.get('minimum_purchase', 0))),
                maximum_discount=Decimal(str(promotion_data.get('maximum_discount', 0))),
                applicable_categories=promotion_data.get('applicable_categories', []),
                applicable_products=promotion_data.get('applicable_products', []),
                excluded_products=promotion_data.get('excluded_products', []),
                usage_limit=promotion_data.get('usage_limit'),
                usage_limit_per_customer=promotion_data.get('usage_limit_per_customer'),
                is_active=promotion_data.get('is_active', True),
                is_featured=promotion_data.get('is_featured', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(promotion)
            db.session.commit()
            return True, promotion, "Department promotion created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating department promotion: {e}")
            return False, None, str(e)
    
    def get_department_promotions(self, filters: Optional[Dict[str, Any]] = None) -> List[DepartmentPromotion]:
        """Get department promotions with optional filters"""
        try:
            query = DepartmentPromotion.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'department_id' in filters:
                    query = query.filter(DepartmentPromotion.department_id == filters['department_id'])
                if 'promotion_type' in filters:
                    query = query.filter(DepartmentPromotion.promotion_type == filters['promotion_type'])
                if 'is_active' in filters:
                    query = query.filter(DepartmentPromotion.is_active == filters['is_active'])
                if 'is_featured' in filters:
                    query = query.filter(DepartmentPromotion.is_featured == filters['is_featured'])
                if 'valid_only' in filters and filters['valid_only']:
                    today = date.today()
                    query = query.filter(
                        DepartmentPromotion.is_active == True,
                        DepartmentPromotion.start_date <= today,
                        DepartmentPromotion.end_date >= today
                    )
            
            return query.order_by(DepartmentPromotion.is_featured.desc(), DepartmentPromotion.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting department promotions: {e}")
            return []
    
    def use_promotion(self, promotion_id: int, customer_id: Optional[int] = None) -> Tuple[bool, str]:
        """Use a promotion and increment usage count"""
        try:
            promotion = DepartmentPromotion.query.filter_by(
                id=promotion_id,
                tenant_id=self.tenant_id
            ).first()
            
            if not promotion:
                return False, "Promotion not found"
            
            if not promotion.is_valid():
                return False, "Promotion is not valid or expired"
            
            # Check per-customer limit
            if customer_id and promotion.usage_limit_per_customer:
                # This would need additional tracking of usage per customer
                # For simplicity, we're just incrementing total usage here
                pass
            
            # Increment usage count
            promotion.current_usage_count += 1
            
            # Check if usage limit reached
            if promotion.usage_limit and promotion.current_usage_count >= promotion.usage_limit:
                promotion.is_active = False
            
            db.session.commit()
            return True, "Promotion used successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error using promotion: {e}")
            return False, str(e)
    
    # Department Sales Methods
    
    def create_department_sales(self, sales_data: Dict[str, Any], 
                            user_id: Optional[str] = None) -> Tuple[bool, Optional[DepartmentSales], str]:
        """Create department sales record"""
        try:
            sales = DepartmentSales(
                department_id=sales_data['department_id'],
                sales_date=datetime.fromisoformat(sales_data['sales_date']).date(),
                period_type=sales_data.get('period_type', 'Daily'),
                total_sales=Decimal(str(sales_data['total_sales'])),
                total_transactions=sales_data.get('total_transactions', 0),
                total_items_sold=sales_data.get('total_items_sold', 0),
                total_customers=sales_data.get('total_customers', 0),
                footfall_count=sales_data.get('footfall_count'),
                unique_products_sold=sales_data.get('unique_products_sold', 0),
                top_selling_products=sales_data.get('top_selling_products', []),
                staff_count=sales_data.get('staff_count'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            # Calculate derived metrics
            sales.calculate_derived_metrics()
            
            db.session.add(sales)
            db.session.commit()
            return True, sales, "Department sales record created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating department sales: {e}")
            return False, None, str(e)
    
    def get_department_sales(self, filters: Optional[Dict[str, Any]] = None) -> List[DepartmentSales]:
        """Get department sales with optional filters"""
        try:
            query = DepartmentSales.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'department_id' in filters:
                    query = query.filter(DepartmentSales.department_id == filters['department_id'])
                if 'period_type' in filters:
                    query = query.filter(DepartmentSales.period_type == filters['period_type'])
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date']).date()
                    query = query.filter(DepartmentSales.sales_date >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date']).date()
                    query = query.filter(DepartmentSales.sales_date <= end_date)
            
            return query.order_by(DepartmentSales.sales_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting department sales: {e}")
            return []
    
    # Self-Checkout Management Methods
    
    def create_self_checkout(self, checkout_data: Dict[str, Any], 
                          user_id: Optional[str] = None) -> Tuple[bool, Optional[SelfCheckout], str]:
        """Create a new self-checkout station"""
        try:
            checkout = SelfCheckout(
                checkout_id=checkout_data['checkout_id'],
                name=checkout_data['name'],
                model=checkout_data.get('model'),
                manufacturer=checkout_data.get('manufacturer'),
                location=checkout_data.get('location'),
                department_id=checkout_data.get('department_id'),
                is_active=checkout_data.get('is_active', True),
                is_online=checkout_data.get('is_online', False),
                status=checkout_data.get('status', 'Offline'),
                supports_cash=checkout_data.get('supports_cash', False),
                supports_card=checkout_data.get('supports_card', True),
                supports_mobile=checkout_data.get('supports_mobile', True),
                weight_limit_kg=checkout_data.get('weight_limit_kg'),
                total_transactions=checkout_data.get('total_transactions', 0),
                total_sales_amount=Decimal(str(checkout_data.get('total_sales_amount', 0))),
                average_transaction_time_seconds=checkout_data.get('average_transaction_time_seconds'),
                last_maintenance_date=datetime.fromisoformat(checkout_data['last_maintenance_date']).date() if checkout_data.get('last_maintenance_date') else None,
                next_maintenance_date=datetime.fromisoformat(checkout_data['next_maintenance_date']).date() if checkout_data.get('next_maintenance_date') else None,
                maintenance_interval_days=checkout_data.get('maintenance_interval_days', 30),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(checkout)
            db.session.commit()
            return True, checkout, "Self-checkout created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating self-checkout: {e}")
            return False, None, str(e)
    
    def get_self_checkouts(self, filters: Optional[Dict[str, Any]] = None) -> List[SelfCheckout]:
        """Get self-checkout stations with optional filters"""
        try:
            query = SelfCheckout.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'department_id' in filters:
                    query = query.filter(SelfCheckout.department_id == filters['department_id'])
                if 'location' in filters:
                    query = query.filter(SelfCheckout.location.ilike(f"%{filters['location']}%"))
                if 'is_active' in filters:
                    query = query.filter(SelfCheckout.is_active == filters['is_active'])
                if 'is_online' in filters:
                    query = query.filter(SelfCheckout.is_online == filters['is_online'])
                if 'status' in filters:
                    query = query.filter(SelfCheckout.status == filters['status'])
                if 'maintenance_due' in filters and filters['maintenance_due']:
                    today = date.today()
                    query = query.filter(
                        SelfCheckout.next_maintenance_date.isnot(None),
                        SelfCheckout.next_maintenance_date <= today
                    )
            
            return query.order_by(SelfCheckout.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting self-checkouts: {e}")
            return []
    
    def update_checkout_status(self, checkout_id: str, status: str, 
                          is_online: Optional[bool] = None) -> Tuple[bool, str]:
        """Update self-checkout status"""
        try:
            checkout = SelfCheckout.query.filter_by(
                checkout_id=checkout_id,
                tenant_id=self.tenant_id
            ).first()
            
            if not checkout:
                return False, "Self-checkout not found"
            
            checkout.status = status
            
            if is_online is not None:
                checkout.is_online = is_online
            
            db.session.commit()
            return True, "Checkout status updated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating checkout status: {e}")
            return False, str(e)
    
    # Queue Management Methods
    
    def create_queue(self, queue_data: Dict[str, Any], 
                   user_id: Optional[str] = None) -> Tuple[bool, Optional[QueueManagement], str]:
        """Create a new queue"""
        try:
            queue = QueueManagement(
                queue_id=queue_data['queue_id'],
                name=queue_data['name'],
                queue_type=queue_data['queue_type'],
                location=queue_data.get('location'),
                department_id=queue_data.get('department_id'),
                is_active=queue_data.get('is_active', True),
                current_length=queue_data.get('current_length', 0),
                average_wait_time_minutes=queue_data.get('average_wait_time_minutes', 0),
                maximum_capacity=queue_data.get('maximum_capacity'),
                service_points=queue_data.get('service_points', 1),
                average_service_time_minutes=queue_data.get('average_service_time_minutes'),
                total_customers_served_today=queue_data.get('total_customers_served_today', 0),
                average_service_time_today=queue_data.get('average_service_time_today'),
                peak_queue_length_today=queue_data.get('peak_queue_length_today', 0),
                current_staff_count=queue_data.get('current_staff_count', 0),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(queue)
            db.session.commit()
            return True, queue, "Queue created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating queue: {e}")
            return False, None, str(e)
    
    def get_queues(self, filters: Optional[Dict[str, Any]] = None) -> List[QueueManagement]:
        """Get queues with optional filters"""
        try:
            query = QueueManagement.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'department_id' in filters:
                    query = query.filter(QueueManagement.department_id == filters['department_id'])
                if 'queue_type' in filters:
                    query = query.filter(QueueManagement.queue_type == filters['queue_type'])
                if 'location' in filters:
                    query = query.filter(QueueManagement.location.ilike(f"%{filters['location']}%"))
                if 'is_active' in filters:
                    query = query.filter(QueueManagement.is_active == filters['is_active'])
            
            return query.order_by(QueueManagement.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting queues: {e}")
            return []
    
    def update_queue_status(self, queue_id: str, current_length: int, 
                          staff_count: Optional[int] = None) -> Tuple[bool, str]:
        """Update queue status"""
        try:
            queue = QueueManagement.query.filter_by(
                queue_id=queue_id,
                tenant_id=self.tenant_id
            ).first()
            
            if not queue:
                return False, "Queue not found"
            
            queue.current_length = current_length
            
            # Update peak length if needed
            if current_length > queue.peak_queue_length_today:
                queue.peak_queue_length_today = current_length
            
            if staff_count is not None:
                queue.current_staff_count = staff_count
            
            db.session.commit()
            return True, "Queue status updated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating queue status: {e}")
            return False, str(e)
    
    # Analytics and Reporting Methods
    
    def get_department_performance_report(self, start_date: Optional[date] = None, 
                                     end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get department performance report"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get all departments
            departments = Department.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).all()
            
            # Get sales data for each department
            performance_data = []
            total_sales = Decimal('0.00')
            total_transactions = 0
            
            for department in departments:
                sales_records = DepartmentSales.query.filter(
                    DepartmentSales.department_id == department.id,
                    DepartmentSales.sales_date >= start_date,
                    DepartmentSales.sales_date <= end_date
                ).all()
                
                # Aggregate sales data
                dept_total_sales = sum(record.total_sales for record in sales_records)
                dept_total_transactions = sum(record.total_transactions for record in sales_records)
                dept_total_items_sold = sum(record.total_items_sold for record in sales_records)
                dept_total_customers = sum(record.total_customers for record in sales_records)
                
                # Calculate averages
                avg_transaction_value = dept_total_sales / dept_total_transactions if dept_total_transactions > 0 else Decimal('0.00')
                
                # Get target achievement
                target_achievement = 0
                if department.monthly_sales_target and department.monthly_sales_target > 0:
                    # Calculate monthly average from the period
                    days_in_period = (end_date - start_date).days + 1
                    monthly_average = dept_total_sales * 30 / days_in_period
                    target_achievement = (monthly_average / department.monthly_sales_target * 100) if department.monthly_sales_target > 0 else 0
                
                performance_data.append({
                    'department': department.to_dict(),
                    'total_sales': float(dept_total_sales),
                    'total_transactions': dept_total_transactions,
                    'total_items_sold': dept_total_items_sold,
                    'total_customers': dept_total_customers,
                    'average_transaction_value': float(avg_transaction_value),
                    'target_achievement_percentage': round(target_achievement, 2)
                })
                
                total_sales += dept_total_sales
                total_transactions += dept_total_transactions
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_departments': len(departments),
                    'total_sales': float(total_sales),
                    'total_transactions': total_transactions,
                    'average_transaction_value': float(total_sales / total_transactions) if total_transactions > 0 else 0
                },
                'department_performance': performance_data
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating department performance report: {e}")
            return {}
    
    def get_cart_abandonment_analysis(self, start_date: Optional[date] = None, 
                                    end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get cart abandonment analysis"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get abandoned carts in date range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            abandoned_carts = AbandonedCart.query.filter(
                AbandonedCart.tenant_id == self.tenant_id,
                AbandonedCart.abandoned_at >= start_datetime,
                AbandonedCart.abandoned_at <= end_datetime
            ).all()
            
            # Analyze abandonment by reason
            abandonment_by_reason = {}
            abandonment_by_stage = {}
            total_carts = len(abandoned_carts)
            total_value = sum(cart.total_value or Decimal('0.00') for cart in abandoned_carts)
            recovered_carts = sum(1 for cart in abandoned_carts if cart.recovery_status == 'Recovered')
            
            for cart in abandoned_carts:
                # Group by reason
                reason = cart.abandonment_reason or 'Unknown'
                if reason not in abandonment_by_reason:
                    abandonment_by_reason[reason] = {
                        'count': 0,
                        'value': Decimal('0.00')
                    }
                
                abandonment_by_reason[reason]['count'] += 1
                abandonment_by_reason[reason]['value'] += cart.total_value or Decimal('0.00')
                
                # Group by stage
                stage = cart.abandonment_stage or 'Unknown'
                if stage not in abandonment_by_stage:
                    abandonment_by_stage[stage] = {
                        'count': 0,
                        'value': Decimal('0.00')
                    }
                
                abandonment_by_stage[stage]['count'] += 1
                abandonment_by_stage[stage]['value'] += cart.total_value or Decimal('0.00')
            
            # Convert Decimal to float for JSON serialization
            for reason_data in abandonment_by_reason.values():
                reason_data['value'] = float(reason_data['value'])
            
            for stage_data in abandonment_by_stage.values():
                stage_data['value'] = float(stage_data['value'])
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_abandoned_carts': total_carts,
                    'total_abandoned_value': float(total_value),
                    'recovered_carts': recovered_carts,
                    'recovery_rate': round((recovered_carts / total_carts * 100), 2) if total_carts > 0 else 0,
                    'average_cart_value': float(total_value / total_carts) if total_carts > 0 else 0
                },
                'abandonment_by_reason': abandonment_by_reason,
                'abandonment_by_stage': abandonment_by_stage
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating cart abandonment analysis: {e}")
            return {}


# Factory function for creating hypermarket service instances
def create_hypermarket_departmental_service(tenant_id: Optional[str] = None) -> HypermarketDepartmentalService:
    """Create a hypermarket & departmental store service instance"""
    return HypermarketDepartmentalService(tenant_id)