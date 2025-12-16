"""
Books & Office Supplies service layer with comprehensive business logic
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from models import db
from models.books_office import (
    BookProduct, BookVariant, BookAuthor, BookPublisher, BookCategory,
    BookSpecialOrder, TextbookBuyback, OfficeSupplyProduct
)
from utils.feature_flag_manager import feature_manager


class BooksOfficeService:
    """Service layer for books and office supplies operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a books feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Book Product Management Methods
    
    def create_book_product(self, product_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[BookProduct], str]:
        """Create a new book product with variants"""
        try:
            # Create base book product
            book_product = BookProduct(
                product_id=product_data['product_id'],
                sku_base=product_data['sku_base'],
                list_price=float(product_data['list_price']),
                book_type=product_data.get('book_type'),
                genre=product_data.get('genre'),
                subgenre=product_data.get('subgenre'),
                series=product_data.get('series'),
                series_number=product_data.get('series_number'),
                primary_author=product_data.get('primary_author'),
                additional_authors=product_data.get('additional_authors'),
                publisher=product_data.get('publisher'),
                imprint=product_data.get('imprint'),
                publication_date=datetime.fromisoformat(product_data['publication_date']).date() if product_data.get('publication_date') else None,
                edition=product_data.get('edition'),
                language=product_data.get('language'),
                format_type=product_data.get('format_type'),
                page_count=product_data.get('page_count'),
                dimensions=product_data.get('dimensions'),
                weight_oz=product_data.get('weight_oz'),
                cover_type=product_data.get('cover_type'),
                isbn_10=product_data.get('isbn_10'),
                isbn_13=product_data.get('isbn_13'),
                upc=product_data.get('upc'),
                ean=product_data.get('ean'),
                doi=product_data.get('doi'),
                grade_level=product_data.get('grade_level'),
                subject_area=product_data.get('subject_area'),
                curriculum_standard=product_data.get('curriculum_standard'),
                wholesale_price=product_data.get('wholesale_price'),
                cost_price=product_data.get('cost_price'),
                is_bestseller=product_data.get('is_bestseller', False),
                is_new_release=product_data.get('is_new_release', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(book_product)
            db.session.flush()  # Get the ID
            
            # Create variants if provided
            if 'variants' in product_data:
                for variant_data in product_data['variants']:
                    variant = BookVariant(
                        book_product_id=book_product.id,
                        sku=variant_data['sku'],
                        format_type=variant_data['format_type'],
                        condition=variant_data.get('condition'),
                        binding=variant_data.get('binding'),
                        stock=variant_data.get('stock', 0),
                        price_adjustment=variant_data.get('price_adjustment', 0.0),
                        cost_adjustment=variant_data.get('cost_adjustment', 0.0),
                        file_format=variant_data.get('file_format'),
                        file_size_mb=variant_data.get('file_size_mb'),
                        drm_type=variant_data.get('drm_type'),
                        download_limit_days=variant_data.get('download_limit_days'),
                        weight_oz=variant_data.get('weight_oz'),
                        requires_shipping=variant_data.get('requires_shipping', True),
                        tenant_id=self.tenant_id
                    )
                    db.session.add(variant)
            
            # Add categories if provided
            if self.is_feature_enabled('FEATURE_BOOK_CATEGORIES') and 'category_ids' in product_data:
                for category_id in product_data['category_ids']:
                    # Add book to category
                    db.session.execute(
                        "INSERT INTO book_product_categories (book_product_id, category_id) VALUES (:book_id, :category_id)",
                        {'book_id': book_product.id, 'category_id': category_id}
                    )
            
            db.session.commit()
            return True, book_product, "Book product created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating book product: {e}")
            return False, None, str(e)
    
    def get_book_products(self, filters: Optional[Dict[str, Any]] = None) -> List[BookProduct]:
        """Get book products with optional filters"""
        try:
            query = BookProduct.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'author' in filters:
                    query = query.filter(BookProduct.primary_author.ilike(f"%{filters['author']}%"))
                if 'publisher' in filters:
                    query = query.filter(BookProduct.publisher.ilike(f"%{filters['publisher']}%"))
                if 'genre' in filters:
                    query = query.filter(BookProduct.genre == filters['genre'])
                if 'book_type' in filters:
                    query = query.filter(BookProduct.book_type == filters['book_type'])
                if 'min_price' in filters:
                    query = query.filter(BookProduct.list_price >= float(filters['min_price']))
                if 'max_price' in filters:
                    query = query.filter(BookProduct.list_price <= float(filters['max_price']))
                if 'is_textbook' in filters:
                    query = query.filter(BookProduct.book_type.in_(['Textbook', 'Educational', 'Reference']))
                if 'is_bestseller' in filters:
                    query = query.filter(BookProduct.is_bestseller == True)
            
            return query.order_by(BookProduct.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting book products: {e}")
            return []
    
    def get_book_by_isbn(self, isbn: str) -> Optional[BookProduct]:
        """Get book by ISBN (10 or 13)"""
        try:
            return BookProduct.query.filter(
                db.or_(
                    BookProduct.isbn_10 == isbn,
                    BookProduct.isbn_13 == isbn
                ),
                BookProduct.tenant_id == self.tenant_id,
                BookProduct.is_active == True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting book by ISBN: {e}")
            return None
    
    def get_book_variants(self, book_product_id: int) -> List[BookVariant]:
        """Get all variants for a book product"""
        try:
            return BookVariant.query.filter_by(
                book_product_id=book_product_id,
                is_active=True
            ).order_by(BookVariant.format_type, BookVariant.condition).all()
        except Exception as e:
            current_app.logger.error(f"Error getting book variants: {e}")
            return []
    
    # Author Management Methods
    
    def create_author(self, author_data: Dict[str, Any], 
                   user_id: Optional[str] = None) -> Tuple[bool, Optional[BookAuthor], str]:
        """Create a new author"""
        try:
            author = BookAuthor(
                name=author_data['name'],
                bio=author_data.get('bio'),
                photo_url=author_data.get('photo_url'),
                website_url=author_data.get('website_url'),
                birth_date=datetime.fromisoformat(author_data['birth_date']).date() if author_data.get('birth_date') else None,
                nationality=author_data.get('nationality'),
                literary_genre=author_data.get('literary_genre'),
                awards=author_data.get('awards'),
                twitter_handle=author_data.get('twitter_handle'),
                instagram_handle=author_data.get('instagram_handle'),
                tenant_id=self.tenant_id
            )
            
            db.session.add(author)
            db.session.commit()
            return True, author, "Author created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating author: {e}")
            return False, None, str(e)
    
    def get_authors(self, search: Optional[str] = None) -> List[BookAuthor]:
        """Get authors with optional search"""
        try:
            query = BookAuthor.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if search:
                query = query.filter(BookAuthor.name.ilike(f"%{search}%"))
            
            return query.order_by(BookAuthor.name).all()
        except Exception as e:
            current_app.logger.error(f"Error getting authors: {e}")
            return []
    
    # Publisher Management Methods
    
    def create_publisher(self, publisher_data: Dict[str, Any], 
                      user_id: Optional[str] = None) -> Tuple[bool, Optional[BookPublisher], str]:
        """Create a new publisher"""
        try:
            publisher = BookPublisher(
                name=publisher_data['name'],
                imprint=publisher_data.get('imprint'),
                description=publisher_data.get('description'),
                logo_url=publisher_data.get('logo_url'),
                website_url=publisher_data.get('website_url'),
                founded_year=publisher_data.get('founded_year'),
                location=publisher_data.get('location'),
                distribution=publisher_data.get('distribution'),
                specialties=publisher_data.get('specialties'),
                contact_email=publisher_data.get('contact_email'),
                contact_phone=publisher_data.get('contact_phone'),
                tenant_id=self.tenant_id
            )
            
            db.session.add(publisher)
            db.session.commit()
            return True, publisher, "Publisher created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating publisher: {e}")
            return False, None, str(e)
    
    def get_publishers(self, search: Optional[str] = None) -> List[BookPublisher]:
        """Get publishers with optional search"""
        try:
            query = BookPublisher.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if search:
                query = query.filter(BookPublisher.name.ilike(f"%{search}%"))
            
            return query.order_by(BookPublisher.name).all()
        except Exception as e:
            current_app.logger.error(f"Error getting publishers: {e}")
            return []
    
    # Category Management Methods
    
    def create_category(self, category_data: Dict[str, Any], 
                     user_id: Optional[str] = None) -> Tuple[bool, Optional[BookCategory], str]:
        """Create a new book category"""
        try:
            category = BookCategory(
                name=category_data['name'],
                code=category_data['code'],
                parent_id=category_data.get('parent_id'),
                description=category_data.get('description'),
                level=category_data.get('level', 1),
                sort_order=category_data.get('sort_order', 0),
                age_group=category_data.get('age_group'),
                target_audience=category_data.get('target_audience'),
                educational_level=category_data.get('educational_level'),
                tenant_id=self.tenant_id
            )
            
            db.session.add(category)
            db.session.commit()
            return True, category, "Category created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating category: {e}")
            return False, None, str(e)
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """Get category tree structure"""
        try:
            # Get root categories (level 1)
            root_categories = BookCategory.query.filter_by(
                tenant_id=self.tenant_id,
                parent_id=None,
                is_active=True
            ).order_by(BookCategory.sort_order, BookCategory.name).all()
            
            def build_tree(categories):
                tree = []
                for category in categories:
                    children = BookCategory.query.filter_by(
                        parent_id=category.id,
                        is_active=True
                    ).order_by(BookCategory.sort_order, BookCategory.name).all()
                    
                    node = {
                        'category': category.to_dict(),
                        'children': build_tree(children)
                    }
                    tree.append(node)
                return tree
            
            return build_tree(root_categories)
            
        except Exception as e:
            current_app.logger.error(f"Error getting category tree: {e}")
            return []
    
    # Special Order Management Methods
    
    def create_special_order(self, order_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[BookSpecialOrder], str]:
        """Create a new special order"""
        try:
            # Generate unique order number
            order_number = f"SO{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            special_order = BookSpecialOrder(
                order_number=order_number,
                book_product_id=order_data['book_product_id'],
                customer_id=order_data['customer_id'],
                quantity=int(order_data['quantity']),
                format_preference=order_data.get('format_preference'),
                special_instructions=order_data.get('special_instructions'),
                urgency=order_data.get('urgency', 'Normal'),
                quoted_price=float(order_data['quoted_price']),
                deposit_required=order_data.get('deposit_required', False),
                deposit_amount=float(order_data.get('deposit_amount', 0.0)),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(special_order)
            db.session.commit()
            return True, special_order, "Special order created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating special order: {e}")
            return False, None, str(e)
    
    def get_customer_special_orders(self, customer_id: int, status: Optional[str] = None) -> List[BookSpecialOrder]:
        """Get special orders for a customer"""
        try:
            query = BookSpecialOrder.query.filter_by(
                customer_id=customer_id,
                tenant_id=self.tenant_id
            )
            
            if status:
                query = query.filter(BookSpecialOrder.status == status)
            
            return query.order_by(BookSpecialOrder.requested_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting customer special orders: {e}")
            return []
    
    def confirm_special_order(self, order_id: int, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Confirm a special order"""
        try:
            special_order = BookSpecialOrder.query.get(order_id)
            if not special_order:
                return False, "Special order not found"
            
            success = special_order.confirm(user_id)
            if success:
                return True, "Special order confirmed successfully"
            else:
                return False, "Failed to confirm special order"
                
        except Exception as e:
            current_app.logger.error(f"Error confirming special order: {e}")
            return False, str(e)
    
    # Textbook Buyback Methods
    
    def create_buyback(self, buyback_data: Dict[str, Any], 
                    user_id: Optional[str] = None) -> Tuple[bool, Optional[TextbookBuyback], str]:
        """Create a new textbook buyback"""
        try:
            # Generate unique buyback code
            buyback_code = f"BB{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            buyback = TextbookBuyback(
                buyback_code=buyback_code,
                book_product_id=buyback_data['book_product_id'],
                customer_id=buyback_data['customer_id'],
                original_purchase_date=datetime.fromisoformat(buyback_data['original_purchase_date']).date() if buyback_data.get('original_purchase_date') else None,
                original_purchase_price=float(buyback_data.get('original_purchase_price', 0.0)),
                original_receipt_number=buyback_data.get('original_receipt_number'),
                condition=buyback_data['condition'],
                condition_notes=buyback_data.get('condition_notes'),
                missing_items=buyback_data.get('missing_items'),
                damage_description=buyback_data.get('damage_description'),
                quoted_buyback_price=float(buyback_data['quoted_buyback_price']),
                tenant_id=self.tenant_id
            )
            
            db.session.add(buyback)
            db.session.commit()
            return True, buyback, "Buyback created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating buyback: {e}")
            return False, None, str(e)
    
    def get_customer_buybacks(self, customer_id: int, status: Optional[str] = None) -> List[TextbookBuyback]:
        """Get buybacks for a customer"""
        try:
            query = TextbookBuyback.query.filter_by(
                customer_id=customer_id,
                tenant_id=self.tenant_id
            )
            
            if status:
                query = query.filter(TextbookBuyback.status == status)
            
            return query.order_by(TextbookBuyback.submitted_at.desc()).all()
        except Exception as e:
            current_app.logger.error(f"Error getting customer buybacks: {e}")
            return []
    
    def approve_buyback(self, buyback_id: int, final_price: float, store_credit: float, 
                   cash_payout: float, user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Approve a buyback"""
        try:
            buyback = TextbookBuyback.query.get(buyback_id)
            if not buyback:
                return False, "Buyback not found"
            
            success = buyback.approve(
                final_price=final_price,
                store_credit=store_credit,
                cash_payout=cash_payout,
                user_id=user_id
            )
            
            if success:
                return True, "Buyback approved successfully"
            else:
                return False, "Failed to approve buyback"
                
        except Exception as e:
            current_app.logger.error(f"Error approving buyback: {e}")
            return False, str(e)
    
    # Office Supply Management Methods
    
    def create_office_supply(self, supply_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[OfficeSupplyProduct], str]:
        """Create a new office supply product"""
        try:
            import json
            
            office_supply = OfficeSupplyProduct(
                product_id=supply_data['product_id'],
                sku_base=supply_data['sku_base'],
                unit_price=float(supply_data['unit_price']),
                supply_type=supply_data.get('supply_type'),
                subcategory=supply_data.get('subcategory'),
                brand_line=supply_data.get('brand_line'),
                specifications=json.dumps(supply_data.get('specifications', {})),
                compatibility=supply_data.get('compatibility'),
                warranty_months=supply_data.get('warranty_months'),
                typical_use=supply_data.get('typical_use'),
                capacity_units=supply_data.get('capacity_units'),
                capacity_quantity=supply_data.get('capacity_quantity'),
                min_order_quantity=supply_data.get('min_order_quantity', 1),
                order_multiples=supply_data.get('order_multiples', 1),
                bulk_pricing_tiers=json.dumps(supply_data.get('bulk_pricing_tiers', [])),
                eco_friendly=supply_data.get('eco_friendly', False),
                recyclable=supply_data.get('recyclable', False),
                safety_certifications=json.dumps(supply_data.get('safety_certifications', [])),
                cost_price=supply_data.get('cost_price'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(office_supply)
            db.session.commit()
            return True, office_supply, "Office supply created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating office supply: {e}")
            return False, None, str(e)
    
    def get_office_supplies(self, filters: Optional[Dict[str, Any]] = None) -> List[OfficeSupplyProduct]:
        """Get office supplies with optional filters"""
        try:
            query = OfficeSupplyProduct.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'supply_type' in filters:
                    query = query.filter(OfficeSupplyProduct.supply_type == filters['supply_type'])
                if 'brand_line' in filters:
                    query = query.filter(OfficeSupplyProduct.brand_line.ilike(f"%{filters['brand_line']}%"))
                if 'eco_friendly' in filters:
                    query = query.filter(OfficeSupplyProduct.eco_friendly == True)
                if 'min_price' in filters:
                    query = query.filter(OfficeSupplyProduct.unit_price >= float(filters['min_price']))
                if 'max_price' in filters:
                    query = query.filter(OfficeSupplyProduct.unit_price <= float(filters['max_price']))
            
            return query.order_by(OfficeSupplyProduct.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting office supplies: {e}")
            return []
    
    # Analytics and Reporting Methods
    
    def get_book_sales_analytics(self, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get book sales analytics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get sales data for books
            sales_data = db.session.query(
                BookProduct.id,
                BookProduct.primary_author,
                BookProduct.publisher,
                BookProduct.genre,
                BookProduct.book_type,
                db.func.sum(BookVariant.stock).label('total_stock'),
                db.func.count(BookVariant.id).label('variant_count')
            ).join(BookVariant).filter(
                BookProduct.tenant_id == self.tenant_id,
                BookProduct.is_active == True,
                BookVariant.is_active == True
            ).group_by(BookProduct.id).all()
            
            # Get special orders data
            special_orders_data = db.session.query(
                BookProduct.id,
                db.func.count(BookSpecialOrder.id).label('special_order_count'),
                db.func.sum(BookSpecialOrder.quantity).label('total_quantity')
            ).join(BookSpecialOrder).filter(
                BookProduct.tenant_id == self.tenant_id,
                BookSpecialOrder.requested_at >= start_date,
                BookSpecialOrder.requested_at <= end_date
            ).group_by(BookProduct.id).all()
            
            # Get buyback data
            buyback_data = db.session.query(
                BookProduct.id,
                db.func.count(TextbookBuyback.id).label('buyback_count'),
                db.func.sum(TextbookBuyback.final_buyback_price).label('total_buyback_value')
            ).join(TextbookBuyback).filter(
                BookProduct.tenant_id == self.tenant_id,
                TextbookBuyback.submitted_at >= start_date,
                TextbookBuyback.submitted_at <= end_date
            ).group_by(BookProduct.id).all()
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'book_sales': [dict(row) for row in sales_data],
                'special_orders': [dict(row) for row in special_orders_data],
                'buyback_data': [dict(row) for row in buyback_data]
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting book sales analytics: {e}")
            return {}
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get inventory summary for books and office supplies"""
        try:
            # Book products summary
            total_books = BookProduct.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).count()
            
            book_variants = BookVariant.query.join(BookProduct).filter(
                BookProduct.tenant_id == self.tenant_id,
                BookVariant.is_active == True
            ).count()
            
            in_stock_books = BookVariant.query.join(BookProduct).filter(
                BookProduct.tenant_id == self.tenant_id,
                BookVariant.is_active == True,
                BookVariant.stock > 0
            ).count()
            
            # Office supplies summary
            total_supplies = OfficeSupplyProduct.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).count()
            
            in_stock_supplies = OfficeSupplyProduct.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True,
                stock__gt=0  # Assuming OfficeSupplyProduct has stock field
            ).count()
            
            # Category breakdown for books
            category_breakdown = db.session.query(
                BookCategory.name,
                db.func.count(BookProduct.id).label('product_count')
            ).join(book_product_categories).join(BookProduct).filter(
                BookProduct.tenant_id == self.tenant_id,
                BookProduct.is_active == True
            ).group_by(BookCategory.name).all()
            
            return {
                'books': {
                    'total_products': total_books,
                    'total_variants': book_variants,
                    'in_stock_variants': in_stock_books,
                    'stock_percentage': round((in_stock_books / book_variants * 100) if book_variants > 0 else 0, 2),
                    'category_breakdown': [dict(row) for row in category_breakdown]
                },
                'office_supplies': {
                    'total_products': total_supplies,
                    'in_stock_products': in_stock_supplies,
                    'stock_percentage': round((in_stock_supplies / total_supplies * 100) if total_supplies > 0 else 0, 2)
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting inventory summary: {e}")
            return {}


# Factory function for creating books service instances
def create_books_office_service(tenant_id: Optional[str] = None) -> BooksOfficeService:
    """Create a books & office supplies service instance"""
    return BooksOfficeService(tenant_id)