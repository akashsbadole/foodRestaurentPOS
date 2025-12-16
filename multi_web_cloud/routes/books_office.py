"""
Books & Office Supplies routes with feature-aware implementation
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from utils.feature_flag_manager import feature_manager
from services.books_office_service import create_books_office_service
from utils.auth import require_auth
from utils.tenant import get_current_tenant_id
from models.books_office import (
    BookProduct, BookVariant, BookAuthor, BookPublisher, BookCategory,
    BookSpecialOrder, TextbookBuyback, OfficeSupplyProduct
)
from models import db
from datetime import datetime
import json

# Create blueprint
books_office_bp = Blueprint('books_office', __name__, url_prefix='/books-office')

def feature_required(feature_name):
    """Decorator to check if a feature is enabled"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tenant_id = get_current_tenant_id()
            if not feature_manager.is_enabled(feature_name, tenant_id):
                return jsonify({
                    'success': False,
                    'message': f'Feature {feature_name} is not enabled'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Book Product Routes

@books_office_bp.route('/api/books', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_books():
    """Get book products with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('author'):
            filters['author'] = request.args.get('author')
        if request.args.get('publisher'):
            filters['publisher'] = request.args.get('publisher')
        if request.args.get('genre'):
            filters['genre'] = request.args.get('genre')
        if request.args.get('book_type'):
            filters['book_type'] = request.args.get('book_type')
        if request.args.get('min_price'):
            filters['min_price'] = request.args.get('min_price')
        if request.args.get('max_price'):
            filters['max_price'] = request.args.get('max_price')
        if request.args.get('is_textbook'):
            filters['is_textbook'] = request.args.get('is_textbook').lower() == 'true'
        if request.args.get('is_bestseller'):
            filters['is_bestseller'] = request.args.get('is_bestseller').lower() == 'true'
        
        books = service.get_book_products(filters)
        return jsonify({
            'success': True,
            'data': [book.to_dict() for book in books],
            'count': len(books)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting books: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/books', methods=['POST'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def create_book():
    """Create a new book product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, book, message = service.create_book_product(data)
        if success:
            return jsonify({
                'success': True,
                'data': book.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating book: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/books/<int:book_id>', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_book(book_id):
    """Get a specific book product"""
    try:
        tenant_id = get_current_tenant_id()
        book = BookProduct.query.filter_by(
            id=book_id,
            tenant_id=tenant_id,
            is_active=True
        ).first()
        
        if not book:
            return jsonify({'success': False, 'message': 'Book not found'}), 404
        
        return jsonify({
            'success': True,
            'data': book.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting book: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/books/isbn/<isbn>', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_book_by_isbn(isbn):
    """Get a book by ISBN"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        book = service.get_book_by_isbn(isbn)
        if not book:
            return jsonify({'success': False, 'message': 'Book not found'}), 404
        
        return jsonify({
            'success': True,
            'data': book.to_dict()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting book by ISBN: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/books/<int:book_id>/variants', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_book_variants(book_id):
    """Get variants for a book product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        variants = service.get_book_variants(book_id)
        return jsonify({
            'success': True,
            'data': [variant.to_dict() for variant in variants],
            'count': len(variants)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting book variants: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Author Routes

@books_office_bp.route('/api/authors', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_authors():
    """Get authors with optional search"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        search = request.args.get('search')
        authors = service.get_authors(search)
        
        return jsonify({
            'success': True,
            'data': [author.to_dict() for author in authors],
            'count': len(authors)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting authors: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/authors', methods=['POST'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def create_author():
    """Create a new author"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, author, message = service.create_author(data)
        if success:
            return jsonify({
                'success': True,
                'data': author.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating author: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Publisher Routes

@books_office_bp.route('/api/publishers', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_publishers():
    """Get publishers with optional search"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        search = request.args.get('search')
        publishers = service.get_publishers(search)
        
        return jsonify({
            'success': True,
            'data': [publisher.to_dict() for publisher in publishers],
            'count': len(publishers)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting publishers: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/publishers', methods=['POST'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def create_publisher():
    """Create a new publisher"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, publisher, message = service.create_publisher(data)
        if success:
            return jsonify({
                'success': True,
                'data': publisher.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating publisher: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Category Routes

@books_office_bp.route('/api/categories', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_CATEGORIES')
def get_categories():
    """Get category tree"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        category_tree = service.get_category_tree()
        return jsonify({
            'success': True,
            'data': category_tree
        })
    except Exception as e:
        current_app.logger.error(f"Error getting categories: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/categories', methods=['POST'])
@require_auth
@feature_required('FEATURE_BOOK_CATEGORIES')
def create_category():
    """Create a new category"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, category, message = service.create_category(data)
        if success:
            return jsonify({
                'success': True,
                'data': category.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating category: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Special Order Routes

@books_office_bp.route('/api/special-orders', methods=['GET'])
@require_auth
@feature_required('FEATURE_SPECIAL_ORDERS')
def get_special_orders():
    """Get special orders for a customer"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        customer_id = request.args.get('customer_id', type=int)
        status = request.args.get('status')
        
        if not customer_id:
            return jsonify({'success': False, 'message': 'Customer ID is required'}), 400
        
        orders = service.get_customer_special_orders(customer_id, status)
        return jsonify({
            'success': True,
            'data': [order.to_dict() for order in orders],
            'count': len(orders)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting special orders: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/special-orders', methods=['POST'])
@require_auth
@feature_required('FEATURE_SPECIAL_ORDERS')
def create_special_order():
    """Create a new special order"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, order, message = service.create_special_order(data)
        if success:
            return jsonify({
                'success': True,
                'data': order.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating special order: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/special-orders/<int:order_id>/confirm', methods=['POST'])
@require_auth
@feature_required('FEATURE_SPECIAL_ORDERS')
def confirm_special_order(order_id):
    """Confirm a special order"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        success, message = service.confirm_special_order(order_id)
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error confirming special order: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Textbook Buyback Routes

@books_office_bp.route('/api/buybacks', methods=['GET'])
@require_auth
@feature_required('FEATURE_TEXTBOOK_BUYBACK')
def get_buybacks():
    """Get buybacks for a customer"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        customer_id = request.args.get('customer_id', type=int)
        status = request.args.get('status')
        
        if not customer_id:
            return jsonify({'success': False, 'message': 'Customer ID is required'}), 400
        
        buybacks = service.get_customer_buybacks(customer_id, status)
        return jsonify({
            'success': True,
            'data': [buyback.to_dict() for buyback in buybacks],
            'count': len(buybacks)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting buybacks: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/buybacks', methods=['POST'])
@require_auth
@feature_required('FEATURE_TEXTBOOK_BUYBACK')
def create_buyback():
    """Create a new buyback"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, buyback, message = service.create_buyback(data)
        if success:
            return jsonify({
                'success': True,
                'data': buyback.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating buyback: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/buybacks/<int:buyback_id>/approve', methods=['POST'])
@require_auth
@feature_required('FEATURE_TEXTBOOK_BUYBACK')
def approve_buyback(buyback_id):
    """Approve a buyback"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        final_price = float(data.get('final_price', 0))
        store_credit = float(data.get('store_credit', 0))
        cash_payout = float(data.get('cash_payout', 0))
        
        success, message = service.approve_buyback(
            buyback_id=buyback_id,
            final_price=final_price,
            store_credit=store_credit,
            cash_payout=cash_payout
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error approving buyback: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Office Supply Routes

@books_office_bp.route('/api/office-supplies', methods=['GET'])
@require_auth
@feature_required('FEATURE_OFFICE_SUPPLIES')
def get_office_supplies():
    """Get office supplies with optional filters"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        # Parse filters from query parameters
        filters = {}
        if request.args.get('supply_type'):
            filters['supply_type'] = request.args.get('supply_type')
        if request.args.get('brand_line'):
            filters['brand_line'] = request.args.get('brand_line')
        if request.args.get('eco_friendly'):
            filters['eco_friendly'] = request.args.get('eco_friendly').lower() == 'true'
        if request.args.get('min_price'):
            filters['min_price'] = request.args.get('min_price')
        if request.args.get('max_price'):
            filters['max_price'] = request.args.get('max_price')
        
        supplies = service.get_office_supplies(filters)
        return jsonify({
            'success': True,
            'data': [supply.to_dict() for supply in supplies],
            'count': len(supplies)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting office supplies: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/office-supplies', methods=['POST'])
@require_auth
@feature_required('FEATURE_OFFICE_SUPPLIES')
def create_office_supply():
    """Create a new office supply product"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        success, supply, message = service.create_office_supply(data)
        if success:
            return jsonify({
                'success': True,
                'data': supply.to_dict(),
                'message': message
            }), 201
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating office supply: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Analytics Routes

@books_office_bp.route('/api/analytics/sales', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_ANALYTICS')
def get_sales_analytics():
    """Get book sales analytics"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        # Parse date range from query parameters
        start_date = None
        end_date = None
        
        if request.args.get('start_date'):
            start_date = datetime.fromisoformat(request.args.get('start_date'))
        if request.args.get('end_date'):
            end_date = datetime.fromisoformat(request.args.get('end_date'))
        
        analytics = service.get_book_sales_analytics(start_date, end_date)
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        current_app.logger.error(f"Error getting sales analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@books_office_bp.route('/api/analytics/inventory', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_ANALYTICS')
def get_inventory_summary():
    """Get inventory summary"""
    try:
        tenant_id = get_current_tenant_id()
        service = create_books_office_service(tenant_id)
        
        summary = service.get_inventory_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        current_app.logger.error(f"Error getting inventory summary: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Configuration Routes

@books_office_bp.route('/api/config', methods=['GET'])
@require_auth
@feature_required('FEATURE_BOOK_MANAGEMENT')
def get_books_config():
    """Get books & office supplies configuration"""
    try:
        tenant_id = get_current_tenant_id()
        
        # Get configuration from feature flags
        config = {
            'features': {
                'book_management': feature_manager.is_enabled('FEATURE_BOOK_MANAGEMENT', tenant_id),
                'book_categories': feature_manager.is_enabled('FEATURE_BOOK_CATEGORIES', tenant_id),
                'special_orders': feature_manager.is_enabled('FEATURE_SPECIAL_ORDERS', tenant_id),
                'textbook_buyback': feature_manager.is_enabled('FEATURE_TEXTBOOK_BUYBACK', tenant_id),
                'office_supplies': feature_manager.is_enabled('FEATURE_OFFICE_SUPPLIES', tenant_id),
                'book_analytics': feature_manager.is_enabled('FEATURE_BOOK_ANALYTICS', tenant_id)
            },
            'settings': {
                'default_currency': 'USD',
                'tax_inclusive': False,
                'allow_special_orders': True,
                'require_deposit_for_special_orders': False,
                'default_deposit_percentage': 20,
                'buyback_enabled': True,
                'buyback_condition_required': True,
                'buyback_receipt_required': False,
                'office_supplies_enabled': True
            }
        }
        
        return jsonify({
            'success': True,
            'data': config
        })
    except Exception as e:
        current_app.logger.error(f"Error getting books config: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500