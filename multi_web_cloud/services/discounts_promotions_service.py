"""
Discounts & Promotions service layer for handling coupon codes, BOGO offers,
volume and time-based discounts, category discounts, happy hours,
and promotional pricing engine.
"""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload
from models import db
from models.discounts_promotions import (
    CouponCode, CouponUsage, BOGOOffer, BOGOUsage, VolumeDiscount, VolumeDiscountUsage,
    TimeBasedDiscount, TimeDiscountUsage, CategoryDiscount, CategoryDiscountUsage,
    PromotionalPricing, PromotionalPricingUsage
)
from utils.tenant_query_manager import tenant_scoped, get_tenant_id


class DiscountsPromotionsService:
    """Service class for discounts and promotions operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    # Coupon Code Management
    
    def get_coupon_codes(self, filters: Optional[Dict] = None) -> List[CouponCode]:
        """Get coupon codes with optional filters"""
        query = CouponCode.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(CouponCode.is_active == filters['is_active'])
            if 'is_public' in filters:
                query = query.filter(CouponCode.is_public == filters['is_public'])
            if 'discount_type' in filters:
                query = query.filter(CouponCode.discount_type == filters['discount_type'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        CouponCode.valid_from <= now,
                        CouponCode.valid_until >= now
                    )
                )
            if 'expired' in filters and filters['expired']:
                query = query.filter(CouponCode.valid_until < datetime.utcnow())
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    CouponCode.name.ilike(search_term),
                    CouponCode.coupon_code.ilike(search_term),
                    CouponCode.description.ilike(search_term)
                ))
        
        return query.order_by(desc(CouponCode.created_at)).all()
    
    def get_coupon_code_by_id(self, coupon_id: int) -> Optional[CouponCode]:
        """Get coupon code by ID"""
        return CouponCode.query.options(
            joinedload(CouponCode.coupon_usages)
        ).filter_by(id=coupon_id, tenant_id=self.tenant_id).first()
    
    def get_coupon_code_by_code(self, coupon_code: str) -> Optional[CouponCode]:
        """Get coupon code by code"""
        return CouponCode.query.filter_by(
            coupon_code=coupon_code, 
            tenant_id=self.tenant_id
        ).first()
    
    def create_coupon_code(self, data: Dict) -> Tuple[bool, Optional[CouponCode], str]:
        """Create a new coupon code"""
        try:
            # Check if coupon code already exists
            existing = CouponCode.query.filter_by(
                coupon_code=data['coupon_code'], 
                tenant_id=self.tenant_id
            ).first()
            if existing:
                return False, None, f"Coupon code {data['coupon_code']} already exists"
            
            coupon = CouponCode(
                tenant_id=self.tenant_id,
                coupon_code=data['coupon_code'],
                name=data['name'],
                description=data.get('description'),
                discount_type=data['discount_type'],
                discount_value=Decimal(str(data['discount_value'])),
                minimum_order_amount=Decimal(str(data['minimum_order_amount'])) if data.get('minimum_order_amount') else None,
                maximum_discount_amount=Decimal(str(data['maximum_discount_amount'])) if data.get('maximum_discount_amount') else None,
                usage_limit=data.get('usage_limit'),
                usage_limit_per_customer=data.get('usage_limit_per_customer'),
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S') if data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),
                applies_to=data.get('applies_to'),
                exclude_items=data.get('exclude_items'),
                first_time_customers_only=data.get('first_time_customers_only', False),
                is_active=data.get('is_active', True),
                is_public=data.get('is_public', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(coupon)
            db.session.commit()
            return True, coupon, "Coupon code created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating coupon code: {str(e)}"
    
    def validate_coupon_code(self, coupon_code: str, customer_id: Optional[int] = None, order_amount: Optional[Decimal] = None) -> Tuple[bool, Optional[CouponCode], str]:
        """Validate a coupon code for use"""
        coupon = self.get_coupon_code_by_code(coupon_code)
        if not coupon:
            return False, None, "Invalid coupon code"
        
        if not coupon.is_valid:
            if coupon.is_expired:
                return False, None, "Coupon code has expired"
            else:
                return False, None, "Coupon code is not active"
        
        # Check usage limits
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return False, None, "Coupon code usage limit exceeded"
        
        if customer_id and coupon.usage_limit_per_customer:
            customer_usage = CouponUsage.query.filter_by(
                coupon_id=coupon.id,
                customer_id=customer_id
            ).count()
            
            if customer_usage >= coupon.usage_limit_per_customer:
                return False, None, "Customer usage limit exceeded for this coupon"
        
        # Check minimum order amount
        if order_amount and coupon.minimum_order_amount and order_amount < coupon.minimum_order_amount:
            return False, None, f"Minimum order amount of {coupon.minimum_order_amount} required"
        
        return True, coupon, "Coupon code is valid"
    
    def use_coupon_code(self, coupon_id: int, customer_id: int, order_id: int, order_amount: Decimal) -> Tuple[bool, Optional[CouponUsage], str]:
        """Use a coupon code and create usage record"""
        try:
            coupon = self.get_coupon_code_by_id(coupon_id)
            if not coupon:
                return False, None, "Coupon code not found"
            
            # Validate coupon again
            is_valid, _, message = self.validate_coupon_code(coupon.coupon_code, customer_id, order_amount)
            if not is_valid:
                return False, None, message
            
            # Calculate discount amount
            discount_amount = self._calculate_coupon_discount(coupon, order_amount)
            
            # Create usage record
            usage = CouponUsage(
                tenant_id=self.tenant_id,
                coupon_id=coupon.id,
                customer_id=customer_id,
                order_id=order_id,
                discount_amount=discount_amount,
                order_amount=order_amount
            )
            
            # Update coupon usage count
            coupon.used_count += 1
            coupon.updated_at = datetime.utcnow()
            
            db.session.add(usage)
            db.session.commit()
            return True, usage, "Coupon code used successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error using coupon code: {str(e)}"
    
    # BOGO Offer Management
    
    def get_bogo_offers(self, filters: Optional[Dict] = None) -> List[BOGOOffer]:
        """Get BOGO offers with optional filters"""
        query = BOGOOffer.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(BOGOOffer.is_active == filters['is_active'])
            if 'auto_apply' in filters:
                query = query.filter(BOGOOffer.auto_apply == filters['auto_apply'])
            if 'buy_type' in filters:
                query = query.filter(BOGOOffer.buy_type == filters['buy_type'])
            if 'get_type' in filters:
                query = query.filter(BOGOOffer.get_type == filters['get_type'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        BOGOOffer.valid_from <= now,
                        BOGOOffer.valid_until >= now
                    )
                )
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    BOGOOffer.name.ilike(search_term),
                    BOGOOffer.offer_code.ilike(search_term),
                    BOGOOffer.description.ilike(search_term)
                ))
        
        return query.order_by(desc(BOGOOffer.created_at)).all()
    
    def get_bogo_offer_by_id(self, offer_id: int) -> Optional[BOGOOffer]:
        """Get BOGO offer by ID"""
        return BOGOOffer.query.options(
            joinedload(BOGOOffer.bogo_usages)
        ).filter_by(id=offer_id, tenant_id=self.tenant_id).first()
    
    def create_bogo_offer(self, data: Dict) -> Tuple[bool, Optional[BOGOOffer], str]:
        """Create a new BOGO offer"""
        try:
            # Check if offer code already exists
            existing = BOGOOffer.query.filter_by(
                offer_code=data['offer_code'], 
                tenant_id=self.tenant_id
            ).first()
            if existing:
                return False, None, f"BOGO offer code {data['offer_code']} already exists"
            
            offer = BOGOOffer(
                tenant_id=self.tenant_id,
                offer_code=data['offer_code'],
                name=data['name'],
                description=data.get('description'),
                buy_quantity=data['buy_quantity'],
                get_quantity=data['get_quantity'],
                buy_type=data.get('buy_type'),
                get_type=data.get('get_type'),
                buy_products=data.get('buy_products'),
                buy_categories=data.get('buy_categories'),
                get_products=data.get('get_products'),
                get_categories=data.get('get_categories'),
                get_value_limit=Decimal(str(data['get_value_limit'])) if data.get('get_value_limit') else None,
                get_discount_type=data.get('get_discount_type'),
                get_discount_value=Decimal(str(data['get_discount_value'])) if data.get('get_discount_value') else None,
                usage_limit=data.get('usage_limit'),
                customer_usage_limit=data.get('customer_usage_limit'),
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S') if data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),
                valid_days=data.get('valid_days'),
                valid_hours_start=time.fromisoformat(data['valid_hours_start']) if data.get('valid_hours_start') else None,
                valid_hours_end=time.fromisoformat(data['valid_hours_end']) if data.get('valid_hours_end') else None,
                is_active=data.get('is_active', True),
                auto_apply=data.get('auto_apply', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(offer)
            db.session.commit()
            return True, offer, "BOGO offer created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating BOGO offer: {str(e)}"
    
    def validate_bogo_offer(self, offer_id: int, cart_items: List[Dict]) -> Tuple[bool, Optional[BOGOOffer], Dict]:
        """Validate BOGO offer against cart items"""
        offer = self.get_bogo_offer_by_id(offer_id)
        if not offer:
            return False, None, {}
        
        if not offer.is_valid:
            return False, None, {}
        
        # Check if cart meets buy requirements
        buy_items = []
        get_items = []
        
        for item in cart_items:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 0)
            
            # Check if item qualifies for buy
            if offer.buy_products and product_id in offer.buy_products:
                buy_items.append(item)
            elif offer.buy_categories and item.get('category_id') in offer.buy_categories:
                buy_items.append(item)
            elif offer.buy_type == 'specific':
                # Would need to check specific product logic
                pass
            
            # Check if item qualifies for get
            if offer.get_products and product_id in offer.get_products:
                get_items.append(item)
            elif offer.get_categories and item.get('category_id') in offer.get_categories:
                get_items.append(item)
        
        total_buy_quantity = sum(item.get('quantity', 0) for item in buy_items)
        
        if total_buy_quantity < offer.buy_quantity:
            return False, None, {}
        
        # Calculate how many free items customer gets
        free_quantity = (total_buy_quantity // offer.buy_quantity) * offer.get_quantity
        
        return True, offer, {
            'buy_items': buy_items,
            'get_items': get_items,
            'free_quantity': free_quantity,
            'offer_applies': True
        }
    
    def use_bogo_offer(self, offer_id: int, customer_id: int, order_id: int, buy_items: List[Dict], get_items: List[Dict]) -> Tuple[bool, Optional[BOGOUsage], str]:
        """Use a BOGO offer and create usage record"""
        try:
            offer = self.get_bogo_offer_by_id(offer_id)
            if not offer:
                return False, None, "BOGO offer not found"
            
            # Calculate total discount (value of free items)
            total_discount = Decimal('0')
            for item in get_items:
                price = Decimal(str(item.get('price', 0)))
                quantity = item.get('quantity', 0)
                total_discount += price * quantity
            
            # Create usage record
            usage = BOGOUsage(
                tenant_id=self.tenant_id,
                bogo_offer_id=offer.id,
                customer_id=customer_id,
                order_id=order_id,
                buy_items=buy_items,
                get_items=get_items,
                total_discount=total_discount
            )
            
            # Update offer usage count
            offer.used_count += 1
            offer.updated_at = datetime.utcnow()
            
            db.session.add(usage)
            db.session.commit()
            return True, usage, "BOGO offer used successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error using BOGO offer: {str(e)}"
    
    # Volume Discount Management
    
    def get_volume_discounts(self, filters: Optional[Dict] = None) -> List[VolumeDiscount]:
        """Get volume discounts with optional filters"""
        query = VolumeDiscount.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(VolumeDiscount.is_active == filters['is_active'])
            if 'auto_apply' in filters:
                query = query.filter(VolumeDiscount.auto_apply == filters['auto_apply'])
            if 'can_stack' in filters:
                query = query.filter(VolumeDiscount.can_stack == filters['can_stack'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        VolumeDiscount.valid_from <= now,
                        VolumeDiscount.valid_until >= now
                    )
                )
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    VolumeDiscount.name.ilike(search_term),
                    VolumeDiscount.description.ilike(search_term)
                ))
        
        return query.order_by(desc(VolumeDiscount.priority), desc(VolumeDiscount.created_at)).all()
    
    def get_volume_discount_by_id(self, discount_id: int) -> Optional[VolumeDiscount]:
        """Get volume discount by ID"""
        return VolumeDiscount.query.options(
            joinedload(VolumeDiscount.volume_discount_usages)
        ).filter_by(id=discount_id, tenant_id=self.tenant_id).first()
    
    def create_volume_discount(self, data: Dict) -> Tuple[bool, Optional[VolumeDiscount], str]:
        """Create a new volume discount"""
        try:
            discount = VolumeDiscount(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                discount_type=data['discount_type'],
                tiers=data['tiers'],
                applies_to=data.get('applies_to'),
                product_ids=data.get('product_ids'),
                category_ids=data.get('category_ids'),
                brand_ids=data.get('brand_ids'),
                based_on=data.get('based_on', 'quantity'),
                measurement_unit=data.get('measurement_unit'),
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S') if data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),
                priority=data.get('priority', 0),
                can_stack=data.get('can_stack', False),
                is_active=data.get('is_active', True),
                auto_apply=data.get('auto_apply', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(discount)
            db.session.commit()
            return True, discount, "Volume discount created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating volume discount: {str(e)}"
    
    def calculate_volume_discount(self, discount_id: int, quantity: Optional[int] = None, amount: Optional[Decimal] = None) -> Tuple[bool, Decimal, Dict]:
        """Calculate volume discount for given quantity/amount"""
        discount = self.get_volume_discount_by_id(discount_id)
        if not discount or not discount.is_valid:
            return False, Decimal('0'), {}
        
        discount_amount = discount.calculate_discount(quantity, amount)
        is_applicable = discount_amount > 0
        
        return is_applicable, discount_amount, {
            'discount_name': discount.name,
            'discount_type': discount.discount_type,
            'applied_tier': None  # Would need to find which tier was applied
        }
    
    # Time-based Discount Management
    
    def get_time_based_discounts(self, filters: Optional[Dict] = None) -> List[TimeBasedDiscount]:
        """Get time-based discounts with optional filters"""
        query = TimeBasedDiscount.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(TimeBasedDiscount.is_active == filters['is_active'])
            if 'auto_apply' in filters:
                query = query.filter(TimeBasedDiscount.auto_apply == filters['auto_apply'])
            if 'can_stack' in filters:
                query = query.filter(TimeBasedDiscount.can_stack == filters['can_stack'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        TimeBasedDiscount.valid_from <= now,
                        TimeBasedDiscount.valid_until >= now
                    )
                )
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    TimeBasedDiscount.name.ilike(search_term),
                    TimeBasedDiscount.description.ilike(search_term)
                ))
        
        return query.order_by(desc(TimeBasedDiscount.priority), desc(TimeBasedDiscount.created_at)).all()
    
    def get_time_based_discount_by_id(self, discount_id: int) -> Optional[TimeBasedDiscount]:
        """Get time-based discount by ID"""
        return TimeBasedDiscount.query.options(
            joinedload(TimeBasedDiscount.time_discount_usages)
        ).filter_by(id=discount_id, tenant_id=self.tenant_id).first()
    
    def create_time_based_discount(self, data: Dict) -> Tuple[bool, Optional[TimeBasedDiscount], str]:
        """Create a new time-based discount"""
        try:
            discount = TimeBasedDiscount(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                discount_type=data['discount_type'],
                discount_value=Decimal(str(data['discount_value'])),
                days_of_week=data.get('days_of_week'),
                start_time=time.fromisoformat(data['start_time']) if data.get('start_time') else None,
                end_time=time.fromisoformat(data['end_time']) if data.get('end_time') else None,
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d').date() if data.get('valid_from') else date.today(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d').date() if data.get('valid_until') else None,
                applies_to=data.get('applies_to'),
                product_ids=data.get('product_ids'),
                category_ids=data.get('category_ids'),
                minimum_order_amount=Decimal(str(data['minimum_order_amount'])) if data.get('minimum_order_amount') else None,
                priority=data.get('priority', 0),
                can_stack=data.get('can_stack', False),
                is_active=data.get('is_active', True),
                auto_apply=data.get('auto_apply', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(discount)
            db.session.commit()
            return True, discount, "Time-based discount created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating time-based discount: {str(e)}"
    
    def is_time_discount_active_now(self, discount_id: int) -> bool:
        """Check if time-based discount is active at current time"""
        discount = self.get_time_based_discount_by_id(discount_id)
        if not discount:
            return False
        
        return discount.is_active_now
    
    # Category Discount Management
    
    def get_category_discounts(self, filters: Optional[Dict] = None) -> List[CategoryDiscount]:
        """Get category discounts with optional filters"""
        query = CategoryDiscount.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(CategoryDiscount.is_active == filters['is_active'])
            if 'auto_apply' in filters:
                query = query.filter(CategoryDiscount.auto_apply == filters['auto_apply'])
            if 'can_stack' in filters:
                query = query.filter(CategoryDiscount.can_stack == filters['can_stack'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        CategoryDiscount.valid_from <= now,
                        CategoryDiscount.valid_until >= now
                    )
                )
            if 'category_id' in filters:
                query = query.filter(CategoryDiscount.category_ids.contains([filters['category_id']]))
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    CategoryDiscount.name.ilike(search_term),
                    CategoryDiscount.description.ilike(search_term)
                ))
        
        return query.order_by(desc(CategoryDiscount.priority), desc(CategoryDiscount.created_at)).all()
    
    def get_category_discount_by_id(self, discount_id: int) -> Optional[CategoryDiscount]:
        """Get category discount by ID"""
        return CategoryDiscount.query.options(
            joinedload(CategoryDiscount.category_discount_usages)
        ).filter_by(id=discount_id, tenant_id=self.tenant_id).first()
    
    def create_category_discount(self, data: Dict) -> Tuple[bool, Optional[CategoryDiscount], str]:
        """Create a new category discount"""
        try:
            discount = CategoryDiscount(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                discount_type=data['discount_type'],
                discount_value=Decimal(str(data['discount_value'])),
                category_ids=data['category_ids'],
                exclude_subcategories=data.get('exclude_subcategories', False),
                include_child_categories=data.get('include_child_categories', True),
                minimum_quantity=data.get('minimum_quantity'),
                minimum_amount=Decimal(str(data['minimum_amount'])) if data.get('minimum_amount') else None,
                maximum_discount_amount=Decimal(str(data['maximum_discount_amount'])) if data.get('maximum_discount_amount') else None,
                customer_groups=data.get('customer_groups'),
                first_purchase_only=data.get('first_purchase_only', False),
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S') if data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),
                priority=data.get('priority', 0),
                can_stack=data.get('can_stack', False),
                is_active=data.get('is_active', True),
                auto_apply=data.get('auto_apply', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(discount)
            db.session.commit()
            return True, discount, "Category discount created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating category discount: {str(e)}"
    
    # Promotional Pricing Management
    
    def get_promotional_pricing(self, filters: Optional[Dict] = None) -> List[PromotionalPricing]:
        """Get promotional pricing rules with optional filters"""
        query = PromotionalPricing.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(PromotionalPricing.is_active == filters['is_active'])
            if 'auto_apply' in filters:
                query = query.filter(PromotionalPricing.auto_apply == filters['auto_apply'])
            if 'is_exclusive' in filters:
                query = query.filter(PromotionalPricing.is_exclusive == filters['is_exclusive'])
            if 'valid_only' in filters and filters['valid_only']:
                now = datetime.utcnow()
                query = query.filter(
                    and_(
                        PromotionalPricing.valid_from <= now,
                        PromotionalPricing.valid_until >= now
                    )
                )
            if 'pricing_type' in filters:
                query = query.filter(PromotionalPricing.pricing_type == filters['pricing_type'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    PromotionalPricing.name.ilike(search_term),
                    PromotionalPricing.description.ilike(search_term)
                ))
        
        return query.order_by(desc(PromotionalPricing.priority), desc(PromotionalPricing.created_at)).all()
    
    def get_promotional_pricing_by_id(self, pricing_id: int) -> Optional[PromotionalPricing]:
        """Get promotional pricing by ID"""
        return PromotionalPricing.query.options(
            joinedload(PromotionalPricing.promotional_pricing_usages)
        ).filter_by(id=pricing_id, tenant_id=self.tenant_id).first()
    
    def create_promotional_pricing(self, data: Dict) -> Tuple[bool, Optional[PromotionalPricing], str]:
        """Create a new promotional pricing rule"""
        try:
            pricing = PromotionalPricing(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                pricing_type=data['pricing_type'],
                trigger_condition=data.get('trigger_condition'),
                product_ids=data.get('product_ids'),
                category_ids=data.get('category_ids'),
                brand_ids=data.get('brand_ids'),
                special_prices=data.get('special_prices'),
                discount_rules=data.get('discount_rules'),
                bundle_config=data.get('bundle_config'),
                valid_from=datetime.strptime(data['valid_from'], '%Y-%m-%d %H:%M:%S') if data.get('valid_from') else datetime.utcnow(),
                valid_until=datetime.strptime(data['valid_until'], '%Y-%m-%d %H:%M:%S'),
                usage_limit=data.get('usage_limit'),
                customer_usage_limit=data.get('customer_usage_limit'),
                priority=data.get('priority', 0),
                is_exclusive=data.get('is_exclusive', False),
                is_active=data.get('is_active', True),
                auto_apply=data.get('auto_apply', True),
                show_original_price=data.get('show_original_price', True),
                promo_label=data.get('promo_label'),
                created_by=data.get('created_by')
            )
            
            db.session.add(pricing)
            db.session.commit()
            return True, pricing, "Promotional pricing created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating promotional pricing: {str(e)}"
    
    def calculate_promotional_price(self, pricing_id: int, product_id: int, original_price: Decimal, quantity: int = 1, customer_id: Optional[int] = None) -> Tuple[bool, Decimal, Dict]:
        """Calculate promotional price for a product"""
        pricing = self.get_promotional_pricing_by_id(pricing_id)
        if not pricing or not pricing.is_valid:
            return False, original_price, {}
        
        # Check usage limits
        if customer_id and pricing.customer_usage_limit:
            customer_usage = PromotionalPricingUsage.query.filter_by(
                promotional_pricing_id=pricing.id,
                customer_id=customer_id
            ).count()
            
            if customer_usage >= pricing.customer_usage_limit:
                return False, original_price, {}
        
        promotional_price = pricing.calculate_price(product_id, original_price, quantity, customer_id)
        is_applicable = promotional_price != original_price
        
        return is_applicable, promotional_price, {
            'pricing_name': pricing.name,
            'promo_label': pricing.promo_label,
            'show_original_price': pricing.show_original_price
        }
    
    # Analytics and Reporting
    
    def get_discount_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """Get discount analytics for a date range"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Coupon analytics
            coupon_stats = db.session.query(
                func.count(CouponUsage.id).label('total_uses'),
                func.sum(CouponUsage.discount_amount).label('total_discount'),
                func.count(func.distinct(CouponUsage.customer_id)).label('unique_customers')
            ).filter(
                CouponUsage.tenant_id == self.tenant_id,
                CouponUsage.used_at >= start_date,
                CouponUsage.used_at <= end_date
            ).first()
            
            # BOGO analytics
            bogo_stats = db.session.query(
                func.count(BOGOUsage.id).label('total_uses'),
                func.sum(BOGOUsage.total_discount).label('total_discount'),
                func.count(func.distinct(BOGOUsage.customer_id)).label('unique_customers')
            ).filter(
                BOGOUsage.tenant_id == self.tenant_id,
                BOGOUsage.used_at >= start_date,
                BOGOUsage.used_at <= end_date
            ).first()
            
            # Volume discount analytics
            volume_stats = db.session.query(
                func.count(VolumeDiscountUsage.id).label('total_uses'),
                func.sum(VolumeDiscountUsage.discount_amount).label('total_discount'),
                func.count(func.distinct(VolumeDiscountUsage.customer_id)).label('unique_customers')
            ).filter(
                VolumeDiscountUsage.tenant_id == self.tenant_id,
                VolumeDiscountUsage.used_at >= start_date,
                VolumeDiscountUsage.used_at <= end_date
            ).first()
            
            # Time-based discount analytics
            time_stats = db.session.query(
                func.count(TimeDiscountUsage.id).label('total_uses'),
                func.sum(TimeDiscountUsage.discount_amount).label('total_discount'),
                func.count(func.distinct(TimeDiscountUsage.customer_id)).label('unique_customers')
            ).filter(
                TimeDiscountUsage.tenant_id == self.tenant_id,
                TimeDiscountUsage.used_at >= start_date,
                TimeDiscountUsage.used_at <= end_date
            ).first()
            
            # Category discount analytics
            category_stats = db.session.query(
                func.count(CategoryDiscountUsage.id).label('total_uses'),
                func.sum(CategoryDiscountUsage.discount_amount).label('total_discount'),
                func.count(func.distinct(CategoryDiscountUsage.customer_id)).label('unique_customers')
            ).filter(
                CategoryDiscountUsage.tenant_id == self.tenant_id,
                CategoryDiscountUsage.used_at >= start_date,
                CategoryDiscountUsage.used_at <= end_date
            ).first()
            
            # Promotional pricing analytics
            promo_stats = db.session.query(
                func.count(PromotionalPricingUsage.id).label('total_uses'),
                func.sum(PromotionalPricingUsage.discount_amount).label('total_discount'),
                func.count(func.distinct(PromotionalPricingUsage.customer_id)).label('unique_customers')
            ).filter(
                PromotionalPricingUsage.tenant_id == self.tenant_id,
                PromotionalPricingUsage.used_at >= start_date,
                PromotionalPricingUsage.used_at <= end_date
            ).first()
            
            return {
                'coupon_codes': {
                    'total_uses': coupon_stats.total_uses or 0,
                    'total_discount': float(coupon_stats.total_discount or 0),
                    'unique_customers': coupon_stats.unique_customers or 0
                },
                'bogo_offers': {
                    'total_uses': bogo_stats.total_uses or 0,
                    'total_discount': float(bogo_stats.total_discount or 0),
                    'unique_customers': bogo_stats.unique_customers or 0
                },
                'volume_discounts': {
                    'total_uses': volume_stats.total_uses or 0,
                    'total_discount': float(volume_stats.total_discount or 0),
                    'unique_customers': volume_stats.unique_customers or 0
                },
                'time_based_discounts': {
                    'total_uses': time_stats.total_uses or 0,
                    'total_discount': float(time_stats.total_discount or 0),
                    'unique_customers': time_stats.unique_customers or 0
                },
                'category_discounts': {
                    'total_uses': category_stats.total_uses or 0,
                    'total_discount': float(category_stats.total_discount or 0),
                    'unique_customers': category_stats.unique_customers or 0
                },
                'promotional_pricing': {
                    'total_uses': promo_stats.total_uses or 0,
                    'total_discount': float(promo_stats.total_discount or 0),
                    'unique_customers': promo_stats.unique_customers or 0
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {
                'error': f"Error generating discount analytics: {str(e)}",
                'coupon_codes': {},
                'bogo_offers': {},
                'volume_discounts': {},
                'time_based_discounts': {},
                'category_discounts': {},
                'promotional_pricing': {}
            }
    
    # Helper Methods
    
    def _calculate_coupon_discount(self, coupon: CouponCode, order_amount: Decimal) -> Decimal:
        """Calculate discount amount for a coupon"""
        if coupon.discount_type == 'percentage':
            return order_amount * (coupon.discount_value / Decimal('100'))
        elif coupon.discount_type == 'fixed_amount':
            return min(coupon.discount_value, order_amount)
        elif coupon.discount_type == 'buy_x_get_y':
            # This would need more complex logic based on the specific offer
            return Decimal('0')
        
        return Decimal('0')
    
    def _generate_coupon_code(self) -> str:
        """Generate a unique coupon code"""
        prefix = "CPN"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of coupons for today
        today_count = CouponCode.query.filter(
            CouponCode.tenant_id == self.tenant_id,
            CouponCode.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:04d}"
    
    def _generate_bogo_code(self) -> str:
        """Generate a unique BOGO offer code"""
        prefix = "BOGO"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of BOGO offers for today
        today_count = BOGOOffer.query.filter(
            BOGOOffer.tenant_id == self.tenant_id,
            BOGOOffer.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"


# Factory function to create service instances
def create_discounts_promotions_service(tenant_id: str) -> DiscountsPromotionsService:
    """Factory function to create a discounts & promotions service instance"""
    return DiscountsPromotionsService(tenant_id)