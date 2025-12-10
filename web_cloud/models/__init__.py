from flask_sqlalchemy import SQLAlchemy

# Create shared database instance
db = SQLAlchemy()

from .user import User
from .category import Category
from .menu_item import MenuItem
from .table import Table
from .order import Order, OrderItem
from .payment import Payment
from .settings import Settings

__all__ = ['db', 'User', 'Category', 'MenuItem', 'Table', 'Order', 'OrderItem', 'Payment', 'Settings']
