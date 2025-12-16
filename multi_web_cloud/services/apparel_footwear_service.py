"""
Apparel & Footwear service layer with comprehensive business logic
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from models import db
from models.apparel_footwear import (
    ApparelProduct, ApparelVariant, ApparelSizeMatrix, 
    ApparelExchange, ApparelExchangeItem, ApparelInventoryTransaction
)
from utils.feature_flag_manager import feature_manager


class ApparelFootwearService:
    """Service layer for apparel and footwear operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if an apparel feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Product Management Methods
    
    def create_apparel_product(self, product_data: Dict[str, Any], 
                            user_id: Optional[str] = None) -> Tuple[bool, Optional[ApparelProduct], str]:
        """Create a new apparel product with variants"""
        try:
            # Create base apparel product
            apparel_product = ApparelProduct(
                product_id=product_data['product_id'],
                sku_base=product_data['sku_base'],
                base_price=float(product_data['base_price']),
                clothing_type=product_data.get('clothing_type'),
                footwear_type=product_data.get('footwear_type'),
                material=product_data.get('material'),
                fit_type=product_data.get('fit_type'),
                care_instructions=product_data.get('care_instructions'),
                style_name=product_data.get('style_name'),
                collection_name=product_data.get('collection_name'),
                season=product_data.get('season'),
                year=product_data.get('year'),
                brand_name=product_data.get('brand_name'),
                designer_name=product_data.get('designer_name'),
                brand_tier=product_data.get('brand_tier', 'Standard'),
                size_system=product_data.get('size_system', 'US'),
                size_range=product_data.get('size_range'),
                has_plus_sizes=product_data.get('has_plus_sizes', False),
                has_petite_sizes=product_data.get('has_petite_sizes', False),
                has_tall_sizes=product_data.get('has_tall_sizes', False),
                primary_color=product_data.get('primary_color'),
                secondary_color=product_data.get('secondary_color'),
                pattern_type=product_data.get('pattern_type'),
                gender=product_data.get('gender'),
                age_group=product_data.get('age_group'),
                cost_price=product_data.get('cost_price'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(apparel_product)
            db.session.flush()  # Get the ID
            
            # Create variants if provided
            if 'variants' in product_data:
                for variant_data in product_data['variants']:
                    variant = ApparelVariant(
                        apparel_product_id=apparel_product.id,
                        sku=variant_data['sku'],
                        size=variant_data['size'],
                        color=variant_data['color'],
                        color_code=variant_data.get('color_code'),
                        upc=variant_data.get('upc'),
                        ean=variant_data.get('ean'),
                        stock=variant_data.get('stock', 0),
                        price_adjustment=variant_data.get('price_adjustment', 0.0),
                        cost_adjustment=variant_data.get('cost_adjustment', 0.0),
                        weight=variant_data.get('weight'),
                        length=variant_data.get('length'),
                        width=variant_data.get('width'),
                        tenant_id=self.tenant_id
                    )
                    db.session.add(variant)
            
            # Create size matrix if provided
            if self.is_feature_enabled('FEATURE_SIZE_MATRIX') and 'size_matrix' in product_data:
                for size_data in product_data['size_matrix']:
                    size_entry = ApparelSizeMatrix(
                        apparel_product_id=apparel_product.id,
                        size_system=size_data['size_system'],
                        size_name=size_data['size_name'],
                        chest_measurement=size_data.get('chest_measurement'),
                        waist_measurement=size_data.get('waist_measurement'),
                        hip_measurement=size_data.get('hip_measurement'),
                        inseam_measurement=size_data.get('inseam_measurement'),
                        sleeve_length=size_data.get('sleeve_length'),
                        foot_length_cm=size_data.get('foot_length_cm'),
                        foot_width=size_data.get('foot_width'),
                        display_order=size_data.get('display_order', 0),
                        tenant_id=self.tenant_id
                    )
                    db.session.add(size_entry)
            
            db.session.commit()
            return True, apparel_product, "Apparel product created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating apparel product: {e}")
            return False, None, str(e)
    
    def get_apparel_products(self, filters: Optional[Dict[str, Any]] = None) -> List[ApparelProduct]:
        """Get apparel products with optional filters"""
        try:
            query = ApparelProduct.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'brand_name' in filters:
                    query = query.filter(ApparelProduct.brand_name.ilike(f"%{filters['brand_name']}%"))
                if 'season' in filters:
                    query = query.filter(ApparelProduct.season == filters['season'])
                if 'gender' in filters:
                    query = query.filter(ApparelProduct.gender == filters['gender'])
                if 'clothing_type' in filters:
                    query = query.filter(ApparelProduct.clothing_type.ilike(f"%{filters['clothing_type']}%"))
                if 'min_price' in filters:
                    query = query.filter(ApparelProduct.base_price >= float(filters['min_price']))
                if 'max_price' in filters:
                    query = query.filter(ApparelProduct.base_price <= float(filters['max_price']))
            
            return query.order_by(ApparelProduct.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting apparel products: {e}")
            return []
    
    def get_product_variants(self, apparel_product_id: int) -> List[ApparelVariant]:
        """Get all variants for an apparel product"""
        try:
            return ApparelVariant.query.filter_by(
                apparel_product_id=apparel_product_id,
                is_active=True
            ).order_by(ApparelVariant.color, ApparelVariant.size).all()
        except Exception as e:
            current_app.logger.error(f"Error getting product variants: {e}")
            return []
    
    def get_variant_by_sku(self, sku: str) -> Optional[ApparelVariant]:
        """Get variant by SKU"""
        try:
            return ApparelVariant.query.filter_by(
                sku=sku,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting variant by SKU: {e}")
            return None
    
    # Inventory Management Methods
    
    def adjust_variant_stock(self, variant_id: int, quantity: int, reason: str = 'Adjustment',
                          user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Adjust stock for a specific variant"""
        try:
            variant = ApparelVariant.query.get(variant_id)
            if not variant:
                return False, "Variant not found"
            
            old_stock = variant.stock
            new_stock = old_stock + quantity
            
            if new_stock < 0:
                return False, "Insufficient stock for adjustment"
            
            variant.stock = new_stock
            variant.updated_at = datetime.utcnow()
            
            # Create inventory transaction
            transaction = ApparelInventoryTransaction(
                variant_id=variant_id,
                quantity=quantity,
                old_stock=old_stock,
                new_stock=new_stock,
                transaction_type='Adjustment',
                reason=reason,
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            db.session.add(transaction)
            db.session.commit()
            
            return True, f"Stock adjusted from {old_stock} to {new_stock}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adjusting variant stock: {e}")
            return False, str(e)
    
    def get_low_stock_variants(self, threshold: int = 5) -> List[ApparelVariant]:
        """Get variants with low stock"""
        try:
            return ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True,
                ApparelVariant.stock <= threshold,
                ApparelVariant.stock > 0
            ).order_by(ApparelVariant.stock.asc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting low stock variants: {e}")
            return []
    
    def get_out_of_stock_variants(self) -> List[ApparelVariant]:
        """Get variants that are out of stock"""
        try:
            return ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True,
                ApparelVariant.stock <= 0
            ).order_by(ApparelVariant.updated_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting out of stock variants: {e}")
            return []
    
    # Exchange Management Methods
    
    def create_exchange(self, exchange_data: Dict[str, Any], 
                     user_id: Optional[str] = None) -> Tuple[bool, Optional[ApparelExchange], str]:
        """Create a new exchange request"""
        try:
            # Generate unique exchange code
            exchange_code = f"EXCH{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            exchange = ApparelExchange(
                exchange_code=exchange_code,
                apparel_product_id=exchange_data['apparel_product_id'],
                original_order_id=exchange_data['original_order_id'],
                customer_id=exchange_data['customer_id'],
                exchange_reason=exchange_data['exchange_reason'],
                exchange_type=exchange_data.get('exchange_type', 'Size'),
                original_size=exchange_data.get('original_size'),
                original_color=exchange_data.get('original_color'),
                new_size=exchange_data.get('new_size'),
                new_color=exchange_data.get('new_color'),
                customer_notes=exchange_data.get('customer_notes'),
                price_difference=exchange_data.get('price_difference', 0.0),
                refund_amount=exchange_data.get('refund_amount', 0.0),
                store_credit=exchange_data.get('store_credit', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(exchange)
            db.session.flush()  # Get the ID
            
            # Add exchange items if provided
            if 'items' in exchange_data:
                for item_data in exchange_data['items']:
                    exchange_item = ApparelExchangeItem(
                        exchange_id=exchange.id,
                        variant_id=item_data['variant_id'],
                        quantity=item_data.get('quantity', 1),
                        original_condition=item_data.get('original_condition'),
                        returned_condition=item_data.get('returned_condition'),
                        condition_notes=item_data.get('condition_notes'),
                        requires_alteration=item_data.get('requires_alteration', False),
                        alteration_type=item_data.get('alteration_type'),
                        alteration_cost=item_data.get('alteration_cost', 0.0),
                        alteration_notes=item_data.get('alteration_notes'),
                        tenant_id=self.tenant_id
                    )
                    db.session.add(exchange_item)
            
            db.session.commit()
            return True, exchange, "Exchange created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating exchange: {e}")
            return False, None, str(e)
    
    def get_customer_exchanges(self, customer_id: int, status: Optional[str] = None) -> List[ApparelExchange]:
        """Get exchanges for a customer"""
        try:
            query = ApparelExchange.query.filter_by(
                customer_id=customer_id,
                tenant_id=self.tenant_id
            )
            
            if status:
                query = query.filter(ApparelExchange.status == status)
            
            return query.order_by(ApparelExchange.requested_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting customer exchanges: {e}")
            return []
    
    def approve_exchange(self, exchange_id: int, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Approve an exchange request"""
        try:
            exchange = ApparelExchange.query.get(exchange_id)
            if not exchange:
                return False, "Exchange not found"
            
            if exchange.status != 'Pending':
                return False, f"Exchange cannot be approved in {exchange.status} status"
            
            success = exchange.approve(user_id)
            if success:
                return True, "Exchange approved successfully"
            else:
                return False, "Failed to approve exchange"
                
        except Exception as e:
            current_app.logger.error(f"Error approving exchange: {e}")
            return False, str(e)
    
    def complete_exchange(self, exchange_id: int, completion_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Complete an exchange"""
        try:
            exchange = ApparelExchange.query.get(exchange_id)
            if not exchange:
                return False, "Exchange not found"
            
            if exchange.status != 'Approved':
                return False, f"Exchange cannot be completed in {exchange.status} status"
            
            success = exchange.complete(
                new_size=completion_data.get('new_size'),
                new_color=completion_data.get('new_color')
            )
            
            if success:
                # Update stock for exchanged items
                for item in exchange.items:
                    if item.requires_alteration:
                        # Adjust stock for alteration (no stock change)
                        pass
                    else:
                        # Return original variant to stock
                        item.variant.adjust_stock(item.quantity, 'Exchange Return')
                        
                        # Deduct stock for new variant
                        new_variant = self.get_variant_by_size_color(
                            exchange.apparel_product_id,
                            completion_data.get('new_size'),
                            completion_data.get('new_color')
                        )
                        if new_variant:
                            new_variant.adjust_stock(-item.quantity, 'Exchange Issue')
                
                return True, "Exchange completed successfully"
            else:
                return False, "Failed to complete exchange"
                
        except Exception as e:
            current_app.logger.error(f"Error completing exchange: {e}")
            return False, str(e)
    
    # Size and Color Management Methods
    
    def get_variant_by_size_color(self, apparel_product_id: int, size: str, color: str) -> Optional[ApparelVariant]:
        """Get specific variant by size and color"""
        try:
            return ApparelVariant.query.filter_by(
                apparel_product_id=apparel_product_id,
                size=size,
                color=color,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting variant by size/color: {e}")
            return None
    
    def get_available_sizes_for_product(self, apparel_product_id: int) -> List[str]:
        """Get available sizes for a product"""
        try:
            variants = ApparelVariant.query.filter_by(
                apparel_product_id=apparel_product_id,
                is_active=True
            ).filter(ApparelVariant.stock > 0).all()
            
            sizes = list(set(v.size for v in variants))
            return sorted(sizes)
        except Exception as e:
            current_app.logger.error(f"Error getting available sizes: {e}")
            return []
    
    def get_available_colors_for_product(self, apparel_product_id: int, size: Optional[str] = None) -> List[str]:
        """Get available colors for a product (and optionally size)"""
        try:
            query = ApparelVariant.query.filter_by(
                apparel_product_id=apparel_product_id,
                is_active=True
            ).filter(ApparelVariant.stock > 0)
            
            if size:
                query = query.filter(ApparelVariant.size == size)
            
            variants = query.all()
            colors = list(set(v.color for v in variants))
            return sorted(colors)
        except Exception as e:
            current_app.logger.error(f"Error getting available colors: {e}")
            return []
    
    def get_size_matrix(self, apparel_product_id: int, size_system: Optional[str] = None) -> List[ApparelSizeMatrix]:
        """Get size matrix for a product"""
        try:
            query = ApparelSizeMatrix.query.filter_by(apparel_product_id=apparel_product_id)
            
            if size_system:
                query = query.filter(ApparelSizeMatrix.size_system == size_system)
            
            return query.order_by(ApparelSizeMatrix.display_order).all()
        except Exception as e:
            current_app.logger.error(f"Error getting size matrix: {e}")
            return []
    
    # Analytics and Reporting Methods
    
    def get_product_performance(self, start_date: Optional[datetime] = None, 
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get apparel product performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get sales data for apparel products
            sales_data = db.session.query(
                ApparelProduct.id,
                ApparelProduct.brand_name,
                ApparelProduct.season,
                db.func.sum(ApparelVariant.stock).label('total_stock'),
                db.func.count(ApparelVariant.id).label('variant_count')
            ).join(ApparelVariant).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelProduct.is_active == True,
                ApparelVariant.is_active == True
            ).group_by(ApparelProduct.id).all()
            
            # Get exchange data
            exchange_data = db.session.query(
                ApparelProduct.id,
                db.func.count(ApparelExchange.id).label('exchange_count')
            ).join(ApparelExchange).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelExchange.requested_at >= start_date,
                ApparelExchange.requested_at <= end_date
            ).group_by(ApparelProduct.id).all()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'product_sales': [dict(row) for row in sales_data],
                'exchange_data': [dict(row) for row in exchange_data]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting product performance: {e}")
            return {}
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary for apparel products"""
        try:
            # Total products and variants
            total_products = ApparelProduct.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).count()
            
            total_variants = ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True
            ).count()
            
            # Stock levels
            in_stock_variants = ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True,
                ApparelVariant.stock > 0
            ).count()
            
            low_stock_variants = ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True,
                ApparelVariant.stock <= 5,
                ApparelVariant.stock > 0
            ).count()
            
            out_of_stock_variants = ApparelVariant.query.join(ApparelProduct).filter(
                ApparelProduct.tenant_id == self.tenant_id,
                ApparelVariant.is_active == True,
                ApparelVariant.stock <= 0
            ).count()
            
            # Brand breakdown
            brand_breakdown = db.session.query(
                ApparelProduct.brand_name,
                db.func.count(ApparelProduct.id).label('product_count')
            ).filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).group_by(ApparelProduct.brand_name).all()
            
            return {
                'total_products': total_products,
                'total_variants': total_variants,
                'in_stock_variants': in_stock_variants,
                'low_stock_variants': low_stock_variants,
                'out_of_stock_variants': out_of_stock_variants,
                'stock_percentage': round((in_stock_variants / total_variants * 100) if total_variants > 0 else 0, 2),
                'brand_breakdown': [dict(row) for row in brand_breakdown]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting inventory summary: {e}")
            return {}


# Factory function for creating apparel service instances
def create_apparel_footwear_service(tenant_id: Optional[str] = None) -> ApparelFootwearService:
    """Create an apparel & footwear service instance"""
    return ApparelFootwearService(tenant_id)