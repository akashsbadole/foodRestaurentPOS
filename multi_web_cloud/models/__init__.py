from flask_sqlalchemy import SQLAlchemy

# Create shared database instance
db = SQLAlchemy()

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .category import Category
from .menu_item import MenuItem
from .table import Table
from .order import Order, OrderItem
from .payment import Payment
from .settings import Settings
from .customer import Customer
from .loyalty import LoyaltyTier, LoyaltyProgram, PointsTransaction, Reward, RewardRedemption, CustomerFeedback, Referral
from .tenant import (
    Tenant, TenantSettings, SubscriptionPlan, TenantSubscription,
    TenantFeatureFlag, TenantUsage
)
from .feature_flag import (
    FeatureDefinition, FeatureDependency, FeatureConflict,
    RetailTypePreset, FeatureFlagAuditLog
)
from .feature_aware_model import FeatureAwareModel, model_registry

# Import new multi-retail models
from .product import Product, ProductCategory, ProductVariant, ProductAttribute, Attribute
from .inventory import InventoryTransaction, StockAdjustment, LowStockAlert, ReorderPoint
from .tracking import BatchLot, SerialNumber
from .supplier import Supplier, PurchaseOrder, PurchaseOrderItem, PurchaseReceipt
from .tax import TaxJurisdiction, TaxRate, TaxRule, TaxExemption
from .warehouse import Warehouse, WarehouseStock, StockTransfer
from .payment_enhanced import PaymentMethod, SplitPayment, EMIPayment, WalletPayment
from .cash_management import CashDrawer, DenominationCount, CashTransaction
from .customer_enhanced import CustomerGroup, CustomerCredit, CustomerNote, PurchaseHistory
from .returns import SalesReturn, ReturnItem, ProductExchange, ExchangeItem
from .order_enhanced import EnhancedOrder, EnhancedOrderItem, OrderStatusHistory, EnhancedPayment
from .barcode import Barcode, BarcodeScan, BarcodeLabel, BarcodePrintJob, BarcodePrintItem
from .reporting import ReportTemplate, ReportSchedule, ReportExecution, AnalyticsCache, DashboardConfig
from .business_intelligence import (
    BusinessMetric, MetricValue, SalesTarget, CustomerSegment,
    CustomerSegmentMember, ProductPerformance
)

# Import restaurant models
from .restaurant import (
    RestaurantTable, TableReservation, KitchenStation, RestaurantShift
)

# Import apparel & footwear models
from .apparel_footwear import (
    ApparelProduct, ApparelVariant, ApparelSizeMatrix,
    ApparelExchange, ApparelExchangeItem, ApparelInventoryTransaction
)

# Import books & office supplies models
from .books_office import (
    BookProduct, BookVariant, BookAuthor, BookPublisher, BookCategory,
    BookSpecialOrder, TextbookBuyback, OfficeSupplyProduct
)

# Import food & confectionery models
from .food_confectionery import (
    FoodProduct, FoodBatch, TemperatureLog, Recipe, RecipeItem,
    FoodWastage, WeighingScaleIntegration
)

# Import hypermarket & departmental store models
from .hypermarket_departmental import (
    Department, HypermarketProduct, ShoppingCartItem, AbandonedCart,
    DepartmentPromotion, DepartmentSales, SelfCheckout, QueueManagement
)

# Import supermarket & groceries models
from .supermarket_groceries import (
    FreshProduce, FreshProduceInventory, FreshProducePriceUpdate, FreshProduceQualityCheck,
    WeighingScaleIntegration as SupermarketWeighingScaleIntegration, ComboOffer,
    ShelfLifeManagement, FreshCounter
)

# Import specialized retail models
from .specialized_retail import (
    CustomProduct, CustomAttribute, CustomAttributeValue, ServiceBooking,
    RepairRecord, WarrantyClaim, RentalItem, ConsignmentItem
)

# Import payment & settlement models
from .payment_settlement import (
    PaymentMethod, WalletPayment, EMIPayment, DenominationCount,
    SplitPayment, SettlementRecord, SettlementItem, CashManagement
)

# Import discounts & promotions models
from .discounts_promotions import (
    CouponCode, CouponUsage, BOGOOffer, BOGOUsage, VolumeDiscount, VolumeDiscountUsage,
    TimeBasedDiscount, TimeDiscountUsage, CategoryDiscount, CategoryDiscountUsage,
    PromotionalPricing, PromotionalPricingUsage
)

# Import returns & exchanges models
from .returns_exchanges import (
    ReturnRequest, ReturnItem, ExchangeRequest, ExchangeItem, ReturnPolicy,
    ReturnWorkflow, ReturnAuditLog
)

# Import reporting & analytics models
from .reporting_analytics import (
    ReportTemplate, ReportInstance, SalesAnalytics, CustomerAnalytics, StaffPerformance,
    ABCAnalysis, HourlySales, ProfitLossAnalysis, DashboardWidget, AnalyticsCache
)

# Import multi-store & franchise models
from .multi_store_franchise import (
    Store, InventoryTransfer, ConsolidatedReport, FranchiseAgreement,
    RoyaltyPayment, StorePerformance, StoreInventory, StoreUser
)

# Import online integration models
from .online_integration import (
    OnlineOrder, ClickAndCollect, HomeDelivery, DeliveryPartner,
    ThirdPartyIntegration, OnlineOrderHistory, OnlineOrderReview,
    OnlineOrderAnalytics
)

def create_tables():
    """Create all database tables"""
    db.create_all()

# Export all models and database instance
__all__ = [
    'db', 'User', 'Category', 'MenuItem', 'Table', 'Order', 'OrderItem', 'Payment', 'Settings',
    'Customer', 'LoyaltyTier', 'LoyaltyProgram', 'PointsTransaction', 'Reward', 'RewardRedemption',
    'CustomerFeedback', 'Referral', 'create_tables', 'Tenant', 'TenantSettings', 'SubscriptionPlan',
    'TenantSubscription', 'TenantFeatureFlag', 'TenantUsage', 'FeatureDefinition', 'FeatureDependency',
    'FeatureConflict', 'RetailTypePreset', 'FeatureFlagAuditLog', 'FeatureAwareModel', 'model_registry',
    
    # New multi-retail models
    'Product', 'ProductCategory', 'ProductVariant', 'ProductAttribute', 'Attribute',
    'InventoryTransaction', 'StockAdjustment', 'LowStockAlert', 'ReorderPoint',
    'BatchLot', 'SerialNumber',
    'Supplier', 'PurchaseOrder', 'PurchaseOrderItem', 'PurchaseReceipt',
    'TaxJurisdiction', 'TaxRate', 'TaxRule', 'TaxExemption',
    'Warehouse', 'WarehouseStock', 'StockTransfer',
    'PaymentMethod', 'SplitPayment', 'EMIPayment', 'WalletPayment',
    'CashDrawer', 'DenominationCount', 'CashTransaction',
    'CustomerGroup', 'CustomerCredit', 'CustomerNote', 'PurchaseHistory',
    'SalesReturn', 'ReturnItem', 'ProductExchange', 'ExchangeItem',
    'EnhancedOrder', 'EnhancedOrderItem', 'OrderStatusHistory', 'EnhancedPayment',
    'Barcode', 'BarcodeScan', 'BarcodeLabel', 'BarcodePrintJob', 'BarcodePrintItem',
    'ReportTemplate', 'ReportSchedule', 'ReportExecution', 'AnalyticsCache', 'DashboardConfig',
    'BusinessMetric', 'MetricValue', 'SalesTarget', 'CustomerSegment',
    'CustomerSegmentMember', 'ProductPerformance',
    
    # Restaurant models
    'RestaurantTable', 'TableReservation', 'KitchenStation', 'RestaurantShift',
    
    # Apparel & Footwear models
    'ApparelProduct', 'ApparelVariant', 'ApparelSizeMatrix',
    'ApparelExchange', 'ApparelExchangeItem', 'ApparelInventoryTransaction',
    
    # Books & Office Supplies models
    'BookProduct', 'BookVariant', 'BookAuthor', 'BookPublisher', 'BookCategory',
    'BookSpecialOrder', 'TextbookBuyback', 'OfficeSupplyProduct',
    
    # Food & Confectionery models
    'FoodProduct', 'FoodBatch', 'TemperatureLog', 'Recipe', 'RecipeItem',
    'FoodWastage', 'WeighingScaleIntegration',
    
    # Hypermarket & Departmental Store models
    'Department', 'HypermarketProduct', 'ShoppingCartItem', 'AbandonedCart',
    'DepartmentPromotion', 'DepartmentSales', 'SelfCheckout', 'QueueManagement',
    
    # Supermarket & Groceries models
    'FreshProduce', 'FreshProduceInventory', 'FreshProducePriceUpdate', 'FreshProduceQualityCheck',
    'SupermarketWeighingScaleIntegration', 'ComboOffer', 'ShelfLifeManagement', 'FreshCounter',
    
    # Specialized Retail models
    'CustomProduct', 'CustomAttribute', 'CustomAttributeValue', 'ServiceBooking',
    'RepairRecord', 'WarrantyClaim', 'RentalItem', 'ConsignmentItem',
    
    # Discounts & Promotions models
    'CouponCode', 'CouponUsage', 'BOGOOffer', 'BOGOUsage', 'VolumeDiscount', 'VolumeDiscountUsage',
    'TimeBasedDiscount', 'TimeDiscountUsage', 'CategoryDiscount', 'CategoryDiscountUsage',
    'PromotionalPricing', 'PromotionalPricingUsage',
    
    # Returns & Exchanges models
    'ReturnRequest', 'ReturnItem', 'ExchangeRequest', 'ExchangeItem', 'ReturnPolicy',
    'ReturnWorkflow', 'ReturnAuditLog',
    
    # Reporting & Analytics models
    'ReportTemplate', 'ReportInstance', 'SalesAnalytics', 'CustomerAnalytics', 'StaffPerformance',
    'ABCAnalysis', 'HourlySales', 'ProfitLossAnalysis', 'DashboardWidget', 'AnalyticsCache',
    
    # Multi-Store & Franchise models
    'Store', 'InventoryTransfer', 'ConsolidatedReport', 'FranchiseAgreement',
    'RoyaltyPayment', 'StorePerformance', 'StoreInventory', 'StoreUser',
    
    # Online Integration models
    'OnlineOrder', 'ClickAndCollect', 'HomeDelivery', 'DeliveryPartner',
    'ThirdPartyIntegration', 'OnlineOrderHistory', 'OnlineOrderReview',
    'OnlineOrderAnalytics'
]