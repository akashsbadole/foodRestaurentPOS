"""
Service layer for Multi-Store & Franchise module handling multi-store inventory management,
store transfers, consolidated reporting, franchise management and royalty tracking.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, contains_eager

from models import db
from models.multi_store_franchise import (
    Store, InventoryTransfer, ConsolidatedReport, FranchiseAgreement,
    RoyaltyPayment, StorePerformance, StoreInventory, StoreUser,
    StoreType, TransferStatus, FranchiseStatus
)
from models.feature_flag import feature_flag_service


class MultiStoreFranchiseService:
    """Service class for multi-store and franchise operations"""
    
    def __init__(self):
        self.feature_service = feature_flag_service
    
    # Store Management
    
    def create_store(self, store_data: Dict[str, Any]) -> Tuple[Optional[Store], Optional[str]]:
        """Create a new store"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('multi_store_management', store_data.get('tenant_id')):
                return None, "Multi-store management feature is not enabled"
            
            # Check if store code already exists
            if Store.query.filter_by(store_code=store_data.get('store_code'), 
                                     tenant_id=store_data.get('tenant_id')).first():
                return None, "Store code already exists"
            
            # Create store
            store = Store(
                tenant_id=store_data.get('tenant_id'),
                store_code=store_data.get('store_code'),
                store_name=store_data.get('store_name'),
                store_type=StoreType(store_data.get('store_type')),
                address=store_data.get('address'),
                city=store_data.get('city'),
                state=store_data.get('state'),
                postal_code=store_data.get('postal_code'),
                country=store_data.get('country'),
                phone=store_data.get('phone'),
                email=store_data.get('email'),
                latitude=store_data.get('latitude'),
                longitude=store_data.get('longitude'),
                timezone=store_data.get('timezone'),
                manager_id=store_data.get('manager_id'),
                assistant_managers=store_data.get('assistant_managers', []),
                store_hours=store_data.get('store_hours', {}),
                holidays=store_data.get('holidays', []),
                features=store_data.get('features', []),
                departments=store_data.get('departments', []),
                payment_methods=store_data.get('payment_methods', []),
                inventory_tracking=store_data.get('inventory_tracking', True),
                auto_reorder=store_data.get('auto_reorder', False),
                reorder_point_days=store_data.get('reorder_point_days', 7),
                franchise_id=store_data.get('franchise_id'),
                franchise_agreement_date=store_data.get('franchise_agreement_date'),
                franchise_expiry_date=store_data.get('franchise_expiry_date'),
                royalty_rate=store_data.get('royalty_rate'),
                minimum_monthly_fee=store_data.get('minimum_monthly_fee'),
                is_active=store_data.get('is_active', True),
                is_headquarters=store_data.get('is_headquarters', False),
                opening_date=store_data.get('opening_date'),
                closing_date=store_data.get('closing_date'),
                notes=store_data.get('notes'),
                created_by=store_data.get('created_by')
            )
            
            db.session.add(store)
            db.session.commit()
            
            return store, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_store(self, store_id: int, tenant_id: str) -> Optional[Store]:
        """Get store by ID"""
        return Store.query.filter_by(id=store_id, tenant_id=tenant_id).first()
    
    def get_stores(self, tenant_id: str, include_inactive: bool = False) -> List[Store]:
        """Get all stores for a tenant"""
        query = Store.query.filter_by(tenant_id=tenant_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(Store.store_name).all()
    
    def update_store(self, store_id: int, store_data: Dict[str, Any]) -> Tuple[Optional[Store], Optional[str]]:
        """Update store information"""
        try:
            store = Store.query.filter_by(id=store_id, tenant_id=store_data.get('tenant_id')).first()
            if not store:
                return None, "Store not found"
            
            # Update fields
            if 'store_name' in store_data:
                store.store_name = store_data['store_name']
            if 'store_type' in store_data:
                store.store_type = StoreType(store_data['store_type'])
            if 'address' in store_data:
                store.address = store_data['address']
            if 'city' in store_data:
                store.city = store_data['city']
            if 'state' in store_data:
                store.state = store_data['state']
            if 'postal_code' in store_data:
                store.postal_code = store_data['postal_code']
            if 'country' in store_data:
                store.country = store_data['country']
            if 'phone' in store_data:
                store.phone = store_data['phone']
            if 'email' in store_data:
                store.email = store_data['email']
            if 'latitude' in store_data:
                store.latitude = store_data['latitude']
            if 'longitude' in store_data:
                store.longitude = store_data['longitude']
            if 'timezone' in store_data:
                store.timezone = store_data['timezone']
            if 'manager_id' in store_data:
                store.manager_id = store_data['manager_id']
            if 'assistant_managers' in store_data:
                store.assistant_managers = store_data['assistant_managers']
            if 'store_hours' in store_data:
                store.store_hours = store_data['store_hours']
            if 'holidays' in store_data:
                store.holidays = store_data['holidays']
            if 'features' in store_data:
                store.features = store_data['features']
            if 'departments' in store_data:
                store.departments = store_data['departments']
            if 'payment_methods' in store_data:
                store.payment_methods = store_data['payment_methods']
            if 'inventory_tracking' in store_data:
                store.inventory_tracking = store_data['inventory_tracking']
            if 'auto_reorder' in store_data:
                store.auto_reorder = store_data['auto_reorder']
            if 'reorder_point_days' in store_data:
                store.reorder_point_days = store_data['reorder_point_days']
            if 'franchise_id' in store_data:
                store.franchise_id = store_data['franchise_id']
            if 'franchise_agreement_date' in store_data:
                store.franchise_agreement_date = store_data['franchise_agreement_date']
            if 'franchise_expiry_date' in store_data:
                store.franchise_expiry_date = store_data['franchise_expiry_date']
            if 'royalty_rate' in store_data:
                store.royalty_rate = store_data['royalty_rate']
            if 'minimum_monthly_fee' in store_data:
                store.minimum_monthly_fee = store_data['minimum_monthly_fee']
            if 'is_active' in store_data:
                store.is_active = store_data['is_active']
            if 'is_headquarters' in store_data:
                store.is_headquarters = store_data['is_headquarters']
            if 'opening_date' in store_data:
                store.opening_date = store_data['opening_date']
            if 'closing_date' in store_data:
                store.closing_date = store_data['closing_date']
            if 'notes' in store_data:
                store.notes = store_data['notes']
            
            store.updated_at = datetime.utcnow()
            store.updated_by = store_data.get('updated_by')
            
            db.session.commit()
            return store, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def delete_store(self, store_id: int, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Delete a store"""
        try:
            store = Store.query.filter_by(id=store_id, tenant_id=tenant_id).first()
            if not store:
                return False, "Store not found"
            
            # Check if store has inventory or transfers
            if store.inventory_transfers_from or store.inventory_transfers_to:
                return False, "Cannot delete store with existing inventory transfers"
            
            db.session.delete(store)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Inventory Transfer Management
    
    def create_inventory_transfer(self, transfer_data: Dict[str, Any]) -> Tuple[Optional[InventoryTransfer], Optional[str]]:
        """Create a new inventory transfer"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('inventory_transfers', transfer_data.get('tenant_id')):
                return None, "Inventory transfers feature is not enabled"
            
            # Validate stores
            from_store = Store.query.filter_by(id=transfer_data.get('from_store_id'), 
                                              tenant_id=transfer_data.get('tenant_id')).first()
            to_store = Store.query.filter_by(id=transfer_data.get('to_store_id'), 
                                            tenant_id=transfer_data.get('tenant_id')).first()
            
            if not from_store or not to_store:
                return None, "Invalid store(s) specified"
            
            # Create transfer
            transfer = InventoryTransfer(
                tenant_id=transfer_data.get('tenant_id'),
                transfer_number=transfer_data.get('transfer_number'),
                from_store_id=transfer_data.get('from_store_id'),
                to_store_id=transfer_data.get('to_store_id'),
                transfer_date=transfer_data.get('transfer_date', date.today()),
                requested_by=transfer_data.get('requested_by'),
                status=TransferStatus(transfer_data.get('status', 'requested')),
                tracking_number=transfer_data.get('tracking_number'),
                shipping_carrier=transfer_data.get('shipping_carrier'),
                estimated_arrival=transfer_data.get('estimated_arrival'),
                transfer_items=transfer_data.get('transfer_items', []),
                total_items=transfer_data.get('total_items', 0),
                total_value=transfer_data.get('total_value', Decimal('0.00')),
                transfer_reason=transfer_data.get('transfer_reason'),
                priority=transfer_data.get('priority', 'normal'),
                notes=transfer_data.get('notes'),
                shipping_cost=transfer_data.get('shipping_cost', Decimal('0.00')),
                insurance_cost=transfer_data.get('insurance_cost', Decimal('0.00'))
            )
            
            # Generate transfer number if not provided
            if not transfer.transfer_number:
                transfer.generate_transfer_number()
            
            db.session.add(transfer)
            db.session.commit()
            
            return transfer, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_inventory_transfer(self, transfer_id: int, tenant_id: str) -> Optional[InventoryTransfer]:
        """Get inventory transfer by ID"""
        return InventoryTransfer.query.filter_by(id=transfer_id, tenant_id=tenant_id).first()
    
    def get_inventory_transfers(self, tenant_id: str, from_store_id: Optional[int] = None, 
                               to_store_id: Optional[int] = None, status: Optional[str] = None) -> List[InventoryTransfer]:
        """Get inventory transfers with filters"""
        query = InventoryTransfer.query.filter_by(tenant_id=tenant_id)
        
        if from_store_id:
            query = query.filter_by(from_store_id=from_store_id)
        if to_store_id:
            query = query.filter_by(to_store_id=to_store_id)
        if status:
            query = query.filter_by(status=TransferStatus(status))
        
        return query.order_by(desc(InventoryTransfer.created_at)).all()
    
    def update_inventory_transfer(self, transfer_id: int, transfer_data: Dict[str, Any]) -> Tuple[Optional[InventoryTransfer], Optional[str]]:
        """Update inventory transfer"""
        try:
            transfer = InventoryTransfer.query.filter_by(id=transfer_id, tenant_id=transfer_data.get('tenant_id')).first()
            if not transfer:
                return None, "Transfer not found"
            
            # Update fields
            if 'transfer_date' in transfer_data:
                transfer.transfer_date = transfer_data['transfer_date']
            if 'status' in transfer_data:
                transfer.status = TransferStatus(transfer_data['status'])
            if 'approved_by' in transfer_data:
                transfer.approved_by = transfer_data['approved_by']
            if 'shipped_by' in transfer_data:
                transfer.shipped_by = transfer_data['shipped_by']
            if 'received_by' in transfer_data:
                transfer.received_by = transfer_data['received_by']
            if 'tracking_number' in transfer_data:
                transfer.tracking_number = transfer_data['tracking_number']
            if 'shipping_carrier' in transfer_data:
                transfer.shipping_carrier = transfer_data['shipping_carrier']
            if 'estimated_arrival' in transfer_data:
                transfer.estimated_arrival = transfer_data['estimated_arrival']
            if 'actual_arrival' in transfer_data:
                transfer.actual_arrival = transfer_data['actual_arrival']
            if 'transfer_items' in transfer_data:
                transfer.transfer_items = transfer_data['transfer_items']
            if 'total_items' in transfer_data:
                transfer.total_items = transfer_data['total_items']
            if 'total_value' in transfer_data:
                transfer.total_value = transfer_data['total_value']
            if 'transfer_reason' in transfer_data:
                transfer.transfer_reason = transfer_data['transfer_reason']
            if 'priority' in transfer_data:
                transfer.priority = transfer_data['priority']
            if 'notes' in transfer_data:
                transfer.notes = transfer_data['notes']
            if 'shipping_cost' in transfer_data:
                transfer.shipping_cost = transfer_data['shipping_cost']
            if 'insurance_cost' in transfer_data:
                transfer.insurance_cost = transfer_data['insurance_cost']
            
            transfer.updated_at = datetime.utcnow()
            
            db.session.commit()
            return transfer, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def approve_transfer(self, transfer_id: int, approved_by: int, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Approve an inventory transfer"""
        try:
            transfer = InventoryTransfer.query.filter_by(id=transfer_id, tenant_id=tenant_id).first()
            if not transfer:
                return False, "Transfer not found"
            
            if transfer.status != TransferStatus.REQUESTED:
                return False, "Transfer must be in requested status to approve"
            
            transfer.status = TransferStatus.APPROVED
            transfer.approved_by = approved_by
            transfer.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    def receive_transfer(self, transfer_id: int, received_by: int, tenant_id: str, 
                        received_items: Optional[List[Dict]] = None) -> Tuple[bool, Optional[str]]:
        """Receive an inventory transfer"""
        try:
            transfer = InventoryTransfer.query.filter_by(id=transfer_id, tenant_id=tenant_id).first()
            if not transfer:
                return False, "Transfer not found"
            
            if transfer.status not in [TransferStatus.APPROVED, TransferStatus.IN_TRANSIT]:
                return False, "Transfer must be approved or in transit to receive"
            
            # Update transfer status
            if received_items and len(received_items) < len(transfer.transfer_items):
                transfer.status = TransferStatus.PARTIALLY_RECEIVED
            else:
                transfer.status = TransferStatus.RECEIVED
            
            transfer.received_by = received_by
            transfer.actual_arrival = date.today()
            transfer.updated_at = datetime.utcnow()
            
            # Update received items if provided
            if received_items:
                transfer.transfer_items = received_items
            
            # Update store inventory
            # This would typically involve inventory service integration
            # For now, we'll just mark the transfer as received
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Consolidated Reporting
    
    def create_consolidated_report(self, report_data: Dict[str, Any]) -> Tuple[Optional[ConsolidatedReport], Optional[str]]:
        """Create a new consolidated report"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('consolidated_reporting', report_data.get('tenant_id')):
                return None, "Consolidated reporting feature is not enabled"
            
            # Create report
            report = ConsolidatedReport(
                tenant_id=report_data.get('tenant_id'),
                report_name=report_data.get('report_name'),
                report_type=report_data.get('report_type'),
                report_period=report_data.get('report_period'),
                start_date=report_data.get('start_date'),
                end_date=report_data.get('end_date'),
                store_ids=report_data.get('store_ids', []),
                include_headquarters=report_data.get('include_headquarters', True),
                include_inactive_stores=report_data.get('include_inactive_stores', False),
                report_data=report_data.get('report_data', {}),
                summary_data=report_data.get('summary_data', {}),
                insights=report_data.get('insights', {}),
                generated_by=report_data.get('generated_by'),
                generation_time=report_data.get('generation_time'),
                file_path=report_data.get('file_path'),
                file_format=report_data.get('file_format'),
                file_size=report_data.get('file_size'),
                email_recipients=report_data.get('email_recipients', []),
                auto_distribute=report_data.get('auto_distribute', False),
                notes=report_data.get('notes')
            )
            
            db.session.add(report)
            db.session.commit()
            
            return report, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_consolidated_report(self, report_id: int, tenant_id: str) -> Optional[ConsolidatedReport]:
        """Get consolidated report by ID"""
        return ConsolidatedReport.query.filter_by(id=report_id, tenant_id=tenant_id).first()
    
    def get_consolidated_reports(self, tenant_id: str, report_type: Optional[str] = None, 
                                start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[ConsolidatedReport]:
        """Get consolidated reports with filters"""
        query = ConsolidatedReport.query.filter_by(tenant_id=tenant_id)
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        if start_date:
            query = query.filter(ConsolidatedReport.start_date >= start_date)
        if end_date:
            query = query.filter(ConsolidatedReport.end_date <= end_date)
        
        return query.order_by(desc(ConsolidatedReport.generated_at)).all()
    
    def generate_sales_consolidated_report(self, tenant_id: str, store_ids: List[int], 
                                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate consolidated sales report"""
        try:
            # This would typically query orders and aggregate by store
            # For now, we'll return a template structure
            
            stores = Store.query.filter(Store.id.in_(store_ids), Store.tenant_id == tenant_id).all()
            
            report_data = {
                'stores': [],
                'total_sales': 0,
                'total_orders': 0,
                'total_customers': 0,
                'average_order_value': 0
            }
            
            for store in stores:
                # In a real implementation, this would query actual sales data
                store_data = {
                    'store_id': store.id,
                    'store_name': store.store_name,
                    'sales': 0,
                    'orders': 0,
                    'customers': 0,
                    'average_order_value': 0
                }
                report_data['stores'].append(store_data)
            
            return report_data
        except SQLAlchemyError as e:
            return {'error': str(e)}
    
    # Franchise Management
    
    def create_franchise_agreement(self, agreement_data: Dict[str, Any]) -> Tuple[Optional[FranchiseAgreement], Optional[str]]:
        """Create a new franchise agreement"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('franchise_management', agreement_data.get('tenant_id')):
                return None, "Franchise management feature is not enabled"
            
            # Check if franchise ID already exists
            if FranchiseAgreement.query.filter_by(franchise_id=agreement_data.get('franchise_id'), 
                                                 tenant_id=agreement_data.get('tenant_id')).first():
                return None, "Franchise ID already exists"
            
            # Create agreement
            agreement = FranchiseAgreement(
                tenant_id=agreement_data.get('tenant_id'),
                franchise_id=agreement_data.get('franchise_id'),
                franchise_name=agreement_data.get('franchise_name'),
                legal_entity_name=agreement_data.get('legal_entity_name'),
                agreement_date=agreement_data.get('agreement_date'),
                start_date=agreement_data.get('start_date'),
                end_date=agreement_data.get('end_date'),
                initial_term_years=agreement_data.get('initial_term_years'),
                royalty_rate=agreement_data.get('royalty_rate'),
                royalty_type=agreement_data.get('royalty_type', 'revenue'),
                minimum_monthly_royalty=agreement_data.get('minimum_monthly_royalty', Decimal('0.00')),
                franchise_fee=agreement_data.get('franchise_fee'),
                marketing_fee=agreement_data.get('marketing_fee', Decimal('0.00')),
                training_fee=agreement_data.get('training_fee', Decimal('0.00')),
                territory_description=agreement_data.get('territory_description'),
                exclusive_territory=agreement_data.get('exclusive_territory', True),
                protected_radius=agreement_data.get('protected_radius'),
                protected_zip_codes=agreement_data.get('protected_zip_codes', []),
                minimum_investment=agreement_data.get('minimum_investment'),
                experience_requirements=agreement_data.get('experience_requirements', {}),
                training_requirements=agreement_data.get('training_requirements', {}),
                operational_standards=agreement_data.get('operational_standards', {}),
                reporting_requirements=agreement_data.get('reporting_requirements', {}),
                brand_guidelines=agreement_data.get('brand_guidelines', {}),
                marketing_materials_provided=agreement_data.get('marketing_materials_provided', False),
                local_marketing_allowed=agreement_data.get('local_marketing_allowed', False),
                status=FranchiseStatus(agreement_data.get('status', 'pending')),
                termination_date=agreement_data.get('termination_date'),
                termination_reason=agreement_data.get('termination_reason'),
                notes=agreement_data.get('notes'),
                created_by=agreement_data.get('created_by')
            )
            
            db.session.add(agreement)
            db.session.commit()
            
            return agreement, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_franchise_agreement(self, agreement_id: int, tenant_id: str) -> Optional[FranchiseAgreement]:
        """Get franchise agreement by ID"""
        return FranchiseAgreement.query.filter_by(id=agreement_id, tenant_id=tenant_id).first()
    
    def get_franchise_agreements(self, tenant_id: str, status: Optional[str] = None) -> List[FranchiseAgreement]:
        """Get franchise agreements with filters"""
        query = FranchiseAgreement.query.filter_by(tenant_id=tenant_id)
        
        if status:
            query = query.filter_by(status=FranchiseStatus(status))
        
        return query.order_by(desc(FranchiseAgreement.created_at)).all()
    
    def update_franchise_agreement(self, agreement_id: int, agreement_data: Dict[str, Any]) -> Tuple[Optional[FranchiseAgreement], Optional[str]]:
        """Update franchise agreement"""
        try:
            agreement = FranchiseAgreement.query.filter_by(id=agreement_id, tenant_id=agreement_data.get('tenant_id')).first()
            if not agreement:
                return None, "Agreement not found"
            
            # Update fields
            if 'franchise_name' in agreement_data:
                agreement.franchise_name = agreement_data['franchise_name']
            if 'legal_entity_name' in agreement_data:
                agreement.legal_entity_name = agreement_data['legal_entity_name']
            if 'agreement_date' in agreement_data:
                agreement.agreement_date = agreement_data['agreement_date']
            if 'start_date' in agreement_data:
                agreement.start_date = agreement_data['start_date']
            if 'end_date' in agreement_data:
                agreement.end_date = agreement_data['end_date']
            if 'initial_term_years' in agreement_data:
                agreement.initial_term_years = agreement_data['initial_term_years']
            if 'royalty_rate' in agreement_data:
                agreement.royalty_rate = agreement_data['royalty_rate']
            if 'royalty_type' in agreement_data:
                agreement.royalty_type = agreement_data['royalty_type']
            if 'minimum_monthly_royalty' in agreement_data:
                agreement.minimum_monthly_royalty = agreement_data['minimum_monthly_royalty']
            if 'franchise_fee' in agreement_data:
                agreement.franchise_fee = agreement_data['franchise_fee']
            if 'marketing_fee' in agreement_data:
                agreement.marketing_fee = agreement_data['marketing_fee']
            if 'training_fee' in agreement_data:
                agreement.training_fee = agreement_data['training_fee']
            if 'territory_description' in agreement_data:
                agreement.territory_description = agreement_data['territory_description']
            if 'exclusive_territory' in agreement_data:
                agreement.exclusive_territory = agreement_data['exclusive_territory']
            if 'protected_radius' in agreement_data:
                agreement.protected_radius = agreement_data['protected_radius']
            if 'protected_zip_codes' in agreement_data:
                agreement.protected_zip_codes = agreement_data['protected_zip_codes']
            if 'minimum_investment' in agreement_data:
                agreement.minimum_investment = agreement_data['minimum_investment']
            if 'experience_requirements' in agreement_data:
                agreement.experience_requirements = agreement_data['experience_requirements']
            if 'training_requirements' in agreement_data:
                agreement.training_requirements = agreement_data['training_requirements']
            if 'operational_standards' in agreement_data:
                agreement.operational_standards = agreement_data['operational_standards']
            if 'reporting_requirements' in agreement_data:
                agreement.reporting_requirements = agreement_data['reporting_requirements']
            if 'brand_guidelines' in agreement_data:
                agreement.brand_guidelines = agreement_data['brand_guidelines']
            if 'marketing_materials_provided' in agreement_data:
                agreement.marketing_materials_provided = agreement_data['marketing_materials_provided']
            if 'local_marketing_allowed' in agreement_data:
                agreement.local_marketing_allowed = agreement_data['local_marketing_allowed']
            if 'status' in agreement_data:
                agreement.status = FranchiseStatus(agreement_data['status'])
            if 'termination_date' in agreement_data:
                agreement.termination_date = agreement_data['termination_date']
            if 'termination_reason' in agreement_data:
                agreement.termination_reason = agreement_data['termination_reason']
            if 'notes' in agreement_data:
                agreement.notes = agreement_data['notes']
            
            agreement.updated_at = datetime.utcnow()
            agreement.updated_by = agreement_data.get('updated_by')
            
            db.session.commit()
            return agreement, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    # Royalty Payment Management
    
    def create_royalty_payment(self, payment_data: Dict[str, Any]) -> Tuple[Optional[RoyaltyPayment], Optional[str]]:
        """Create a new royalty payment"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('royalty_tracking', payment_data.get('tenant_id')):
                return None, "Royalty tracking feature is not enabled"
            
            # Calculate net revenue and royalty amount if not provided
            gross_revenue = payment_data.get('gross_revenue', Decimal('0.00'))
            deductible_expenses = payment_data.get('deductible_expenses', Decimal('0.00'))
            net_revenue = gross_revenue - deductible_expenses
            royalty_rate = payment_data.get('royalty_rate', Decimal('0.00'))
            royalty_amount = (net_revenue * royalty_rate) / Decimal('100')
            
            # Apply minimum monthly royalty if applicable
            minimum_monthly_royalty = payment_data.get('minimum_monthly_royalty', Decimal('0.00'))
            if royalty_amount < minimum_monthly_royalty:
                royalty_amount = minimum_monthly_royalty
            
            # Create payment
            payment = RoyaltyPayment(
                tenant_id=payment_data.get('tenant_id'),
                franchise_id=payment_data.get('franchise_id'),
                payment_period=payment_data.get('payment_period'),
                period_start=payment_data.get('period_start'),
                period_end=payment_data.get('period_end'),
                gross_revenue=gross_revenue,
                deductible_expenses=deductible_expenses,
                net_revenue=net_revenue,
                royalty_rate=royalty_rate,
                royalty_amount=royalty_amount,
                payment_date=payment_data.get('payment_date'),
                payment_method=payment_data.get('payment_method'),
                reference_number=payment_data.get('reference_number'),
                status=payment_data.get('status', 'pending'),
                due_date=payment_data.get('due_date'),
                notes=payment_data.get('notes'),
                created_by=payment_data.get('created_by')
            )
            
            db.session.add(payment)
            db.session.commit()
            
            return payment, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_royalty_payment(self, payment_id: int, tenant_id: str) -> Optional[RoyaltyPayment]:
        """Get royalty payment by ID"""
        return RoyaltyPayment.query.filter_by(id=payment_id, tenant_id=tenant_id).first()
    
    def get_royalty_payments(self, tenant_id: str, franchise_id: Optional[str] = None, 
                            status: Optional[str] = None) -> List[RoyaltyPayment]:
        """Get royalty payments with filters"""
        query = RoyaltyPayment.query.filter_by(tenant_id=tenant_id)
        
        if franchise_id:
            query = query.filter_by(franchise_id=franchise_id)
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(desc(RoyaltyPayment.period_start)).all()
    
    def calculate_monthly_royalty(self, tenant_id: str, franchise_id: str, 
                                period_start: date, period_end: date) -> Dict[str, Any]:
        """Calculate monthly royalty for a franchise"""
        try:
            # Get franchise agreement
            agreement = FranchiseAgreement.query.filter_by(
                franchise_id=franchise_id, 
                tenant_id=tenant_id,
                status=FranchiseStatus.ACTIVE
            ).first()
            
            if not agreement:
                return {'error': 'Active franchise agreement not found'}
            
            # Get stores for this franchise
            stores = Store.query.filter_by(
                franchise_id=franchise_id,
                tenant_id=tenant_id,
                is_active=True
            ).all()
            
            if not stores:
                return {'error': 'No active stores found for this franchise'}
            
            store_ids = [store.id for store in stores]
            
            # Calculate total revenue from stores (this would typically query actual sales data)
            # For now, we'll use placeholder values
            total_gross_revenue = Decimal('0.00')
            
            # Calculate royalty
            royalty_amount = (total_gross_revenue * agreement.royalty_rate) / Decimal('100')
            
            # Apply minimum monthly royalty
            if royalty_amount < agreement.minimum_monthly_royalty:
                royalty_amount = agreement.minimum_monthly_royalty
            
            return {
                'franchise_id': franchise_id,
                'period_start': period_start,
                'period_end': period_end,
                'total_gross_revenue': total_gross_revenue,
                'deductible_expenses': Decimal('0.00'),
                'net_revenue': total_gross_revenue,
                'royalty_rate': agreement.royalty_rate,
                'minimum_monthly_royalty': agreement.minimum_monthly_royalty,
                'calculated_royalty': royalty_amount,
                'store_count': len(stores)
            }
        except SQLAlchemyError as e:
            return {'error': str(e)}
    
    # Store Performance
    
    def create_store_performance(self, performance_data: Dict[str, Any]) -> Tuple[Optional[StorePerformance], Optional[str]]:
        """Create a new store performance record"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('store_performance_tracking', performance_data.get('tenant_id')):
                return None, "Store performance tracking feature is not enabled"
            
            # Extract date components
            performance_date = performance_data.get('date', date.today())
            month = performance_date.month
            quarter = (month - 1) // 3 + 1
            year = performance_date.year
            
            # Create performance record
            performance = StorePerformance(
                tenant_id=performance_data.get('tenant_id'),
                store_id=performance_data.get('store_id'),
                date=performance_date,
                month=month,
                quarter=quarter,
                year=year,
                total_sales=performance_data.get('total_sales', Decimal('0.00')),
                total_orders=performance_data.get('total_orders', 0),
                average_order_value=performance_data.get('average_order_value', Decimal('0.00')),
                items_per_order=performance_data.get('items_per_order', Decimal('0.00')),
                unique_customers=performance_data.get('unique_customers', 0),
                returning_customers=performance_data.get('returning_customers', 0),
                new_customers=performance_data.get('new_customers', 0),
                unique_products_sold=performance_data.get('unique_products_sold', 0),
                top_product_id=performance_data.get('top_product_id'),
                top_category_id=performance_data.get('top_category_id'),
                staff_count=performance_data.get('staff_count', 0),
                staff_hours_worked=performance_data.get('staff_hours_worked', Decimal('0.00')),
                sales_per_staff_hour=performance_data.get('sales_per_staff_hour', Decimal('0.00')),
                gross_profit=performance_data.get('gross_profit', Decimal('0.00')),
                net_profit=performance_data.get('net_profit', Decimal('0.00')),
                profit_margin=performance_data.get('profit_margin', Decimal('0.00')),
                inventory_turnover=performance_data.get('inventory_turnover', Decimal('0.00')),
                stockout_count=performance_data.get('stockout_count', 0),
                waste_percentage=performance_data.get('waste_percentage', Decimal('0.00')),
                metadata=performance_data.get('metadata', {})
            )
            
            db.session.add(performance)
            db.session.commit()
            
            return performance, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_store_performance(self, performance_id: int, tenant_id: str) -> Optional[StorePerformance]:
        """Get store performance by ID"""
        return StorePerformance.query.filter_by(id=performance_id, tenant_id=tenant_id).first()
    
    def get_store_performance_by_store(self, tenant_id: str, store_id: int, 
                                      start_date: Optional[date] = None, 
                                      end_date: Optional[date] = None) -> List[StorePerformance]:
        """Get store performance by store with date range"""
        query = StorePerformance.query.filter_by(tenant_id=tenant_id, store_id=store_id)
        
        if start_date:
            query = query.filter(StorePerformance.date >= start_date)
        if end_date:
            query = query.filter(StorePerformance.date <= end_date)
        
        return query.order_by(desc(StorePerformance.date)).all()
    
    def get_store_performance_comparison(self, tenant_id: str, store_ids: List[int], 
                                        start_date: date, end_date: date) -> Dict[str, Any]:
        """Compare performance across multiple stores"""
        try:
            query = StorePerformance.query.filter(
                StorePerformance.tenant_id == tenant_id,
                StorePerformance.store_id.in_(store_ids),
                StorePerformance.date >= start_date,
                StorePerformance.date <= end_date
            )
            
            performances = query.all()
            
            # Aggregate by store
            store_data = {}
            for performance in performances:
                store_id = performance.store_id
                if store_id not in store_data:
                    store_data[store_id] = {
                        'store_id': store_id,
                        'total_sales': Decimal('0.00'),
                        'total_orders': 0,
                        'total_customers': 0,
                        'average_order_value': Decimal('0.00'),
                        'gross_profit': Decimal('0.00'),
                        'net_profit': Decimal('0.00'),
                        'profit_margin': Decimal('0.00'),
                        'performance_count': 0
                    }
                
                data = store_data[store_id]
                data['total_sales'] += performance.total_sales
                data['total_orders'] += performance.total_orders
                data['total_customers'] += performance.unique_customers
                data['gross_profit'] += performance.gross_profit
                data['net_profit'] += performance.net_profit
                data['performance_count'] += 1
            
            # Calculate averages
            for store_id, data in store_data.items():
                if data['total_orders'] > 0:
                    data['average_order_value'] = data['total_sales'] / data['total_orders']
                
                if data['total_sales'] > 0:
                    data['profit_margin'] = (data['net_profit'] / data['total_sales']) * Decimal('100')
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'stores': list(store_data.values()),
                'total_stores': len(store_data)
            }
        except SQLAlchemyError as e:
            return {'error': str(e)}
    
    # Store Inventory
    
    def create_store_inventory(self, inventory_data: Dict[str, Any]) -> Tuple[Optional[StoreInventory], Optional[str]]:
        """Create a new store inventory record"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('store_inventory_tracking', inventory_data.get('tenant_id')):
                return None, "Store inventory tracking feature is not enabled"
            
            # Calculate available quantity
            quantity_on_hand = inventory_data.get('quantity_on_hand', 0)
            quantity_reserved = inventory_data.get('quantity_reserved', 0)
            quantity_available = quantity_on_hand - quantity_reserved
            
            # Calculate total values
            unit_cost = inventory_data.get('unit_cost', Decimal('0.00'))
            unit_price = inventory_data.get('unit_price', Decimal('0.00'))
            total_cost = quantity_on_hand * unit_cost
            total_value = quantity_on_hand * unit_price
            
            # Create inventory record
            inventory = StoreInventory(
                tenant_id=inventory_data.get('tenant_id'),
                store_id=inventory_data.get('store_id'),
                product_id=inventory_data.get('product_id'),
                variant_id=inventory_data.get('variant_id'),
                quantity_on_hand=quantity_on_hand,
                quantity_reserved=quantity_reserved,
                quantity_available=quantity_available,
                reorder_point=inventory_data.get('reorder_point', 0),
                reorder_quantity=inventory_data.get('reorder_quantity', 0),
                unit_cost=unit_cost,
                total_cost=total_cost,
                unit_price=unit_price,
                total_value=total_value,
                aisle=inventory_data.get('aisle'),
                shelf=inventory_data.get('shelf'),
                bin_location=inventory_data.get('bin_location'),
                last_counted=inventory_data.get('last_counted'),
                last_received=inventory_data.get('last_received'),
                last_sold=inventory_data.get('last_sold'),
                metadata=inventory_data.get('metadata', {})
            )
            
            db.session.add(inventory)
            db.session.commit()
            
            return inventory, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_store_inventory(self, inventory_id: int, tenant_id: str) -> Optional[StoreInventory]:
        """Get store inventory by ID"""
        return StoreInventory.query.filter_by(id=inventory_id, tenant_id=tenant_id).first()
    
    def get_store_inventory_by_store(self, tenant_id: str, store_id: int, 
                                     below_reorder_point: bool = False) -> List[StoreInventory]:
        """Get store inventory by store with optional filter for low stock"""
        query = StoreInventory.query.filter_by(tenant_id=tenant_id, store_id=store_id)
        
        if below_reorder_point:
            query = query.filter(StoreInventory.quantity_available <= StoreInventory.reorder_point)
        
        return query.order_by(StoreInventory.product_id).all()
    
    def update_store_inventory(self, inventory_id: int, inventory_data: Dict[str, Any]) -> Tuple[Optional[StoreInventory], Optional[str]]:
        """Update store inventory"""
        try:
            inventory = StoreInventory.query.filter_by(id=inventory_id, tenant_id=inventory_data.get('tenant_id')).first()
            if not inventory:
                return None, "Inventory record not found"
            
            # Update fields
            if 'quantity_on_hand' in inventory_data:
                inventory.quantity_on_hand = inventory_data['quantity_on_hand']
            if 'quantity_reserved' in inventory_data:
                inventory.quantity_reserved = inventory_data['quantity_reserved']
            if 'reorder_point' in inventory_data:
                inventory.reorder_point = inventory_data['reorder_point']
            if 'reorder_quantity' in inventory_data:
                inventory.reorder_quantity = inventory_data['reorder_quantity']
            if 'unit_cost' in inventory_data:
                inventory.unit_cost = inventory_data['unit_cost']
            if 'unit_price' in inventory_data:
                inventory.unit_price = inventory_data['unit_price']
            if 'aisle' in inventory_data:
                inventory.aisle = inventory_data['aisle']
            if 'shelf' in inventory_data:
                inventory.shelf = inventory_data['shelf']
            if 'bin_location' in inventory_data:
                inventory.bin_location = inventory_data['bin_location']
            if 'last_counted' in inventory_data:
                inventory.last_counted = inventory_data['last_counted']
            if 'last_received' in inventory_data:
                inventory.last_received = inventory_data['last_received']
            if 'last_sold' in inventory_data:
                inventory.last_sold = inventory_data['last_sold']
            if 'metadata' in inventory_data:
                inventory.metadata = inventory_data['metadata']
            
            # Recalculate derived fields
            inventory.quantity_available = inventory.quantity_on_hand - inventory.quantity_reserved
            inventory.total_cost = inventory.quantity_on_hand * inventory.unit_cost
            inventory.total_value = inventory.quantity_on_hand * inventory.unit_price
            
            inventory.updated_at = datetime.utcnow()
            
            db.session.commit()
            return inventory, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    # Store User Management
    
    def create_store_user(self, store_user_data: Dict[str, Any]) -> Tuple[Optional[StoreUser], Optional[str]]:
        """Create a new store user assignment"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('store_user_management', store_user_data.get('tenant_id')):
                return None, "Store user management feature is not enabled"
            
            # Check if assignment already exists
            existing = StoreUser.query.filter_by(
                store_id=store_user_data.get('store_id'),
                user_id=store_user_data.get('user_id'),
                tenant_id=store_user_data.get('tenant_id'),
                is_active=True
            ).first()
            
            if existing:
                return None, "User already assigned to this store"
            
            # Create assignment
            store_user = StoreUser(
                tenant_id=store_user_data.get('tenant_id'),
                store_id=store_user_data.get('store_id'),
                user_id=store_user_data.get('user_id'),
                role=store_user_data.get('role'),
                permissions=store_user_data.get('permissions', []),
                assigned_by=store_user_data.get('assigned_by'),
                is_active=store_user_data.get('is_active', True),
                notes=store_user_data.get('notes')
            )
            
            db.session.add(store_user)
            db.session.commit()
            
            return store_user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_store_user(self, store_user_id: int, tenant_id: str) -> Optional[StoreUser]:
        """Get store user by ID"""
        return StoreUser.query.filter_by(id=store_user_id, tenant_id=tenant_id).first()
    
    def get_store_users_by_store(self, tenant_id: str, store_id: int, 
                                active_only: bool = True) -> List[StoreUser]:
        """Get store users by store"""
        query = StoreUser.query.filter_by(tenant_id=tenant_id, store_id=store_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.all()
    
    def get_store_users_by_user(self, tenant_id: str, user_id: int, 
                               active_only: bool = True) -> List[StoreUser]:
        """Get store assignments by user"""
        query = StoreUser.query.filter_by(tenant_id=tenant_id, user_id=user_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.all()
    
    def terminate_store_user(self, store_user_id: int, tenant_id: str, 
                            termination_reason: str) -> Tuple[bool, Optional[str]]:
        """Terminate a store user assignment"""
        try:
            store_user = StoreUser.query.filter_by(id=store_user_id, tenant_id=tenant_id).first()
            if not store_user:
                return False, "Store user assignment not found"
            
            store_user.is_active = False
            store_user.terminated_at = datetime.utcnow()
            store_user.termination_reason = termination_reason
            store_user.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Analytics
    
    def get_multi_store_analytics(self, tenant_id: str, start_date: date, 
                                 end_date: date) -> Dict[str, Any]:
        """Get multi-store analytics for a date range"""
        try:
            # Get all stores
            stores = Store.query.filter_by(tenant_id=tenant_id, is_active=True).all()
            
            # Get performance data for all stores
            performances = StorePerformance.query.filter(
                StorePerformance.tenant_id == tenant_id,
                StorePerformance.date >= start_date,
                StorePerformance.date <= end_date
            ).all()
            
            # Aggregate data by store
            store_analytics = {}
            total_sales = Decimal('0.00')
            total_orders = 0
            total_customers = 0
            
            for performance in performances:
                store_id = performance.store_id
                if store_id not in store_analytics:
                    store_analytics[store_id] = {
                        'store_id': store_id,
                        'total_sales': Decimal('0.00'),
                        'total_orders': 0,
                        'unique_customers': 0,
                        'gross_profit': Decimal('0.00'),
                        'net_profit': Decimal('0.00'),
                        'performance_days': 0
                    }
                
                data = store_analytics[store_id]
                data['total_sales'] += performance.total_sales
                data['total_orders'] += performance.total_orders
                data['unique_customers'] += performance.unique_customers
                data['gross_profit'] += performance.gross_profit
                data['net_profit'] += performance.net_profit
                data['performance_days'] += 1
                
                total_sales += performance.total_sales
                total_orders += performance.total_orders
                total_customers += performance.unique_customers
            
            # Calculate averages and rankings
            for store_id, data in store_analytics.items():
                if data['total_orders'] > 0:
                    data['average_order_value'] = data['total_sales'] / data['total_orders']
                
                if data['total_sales'] > 0:
                    data['profit_margin'] = (data['net_profit'] / data['total_sales']) * Decimal('100')
                
                # Get store details
                store = next((s for s in stores if s.id == store_id), None)
                if store:
                    data['store_name'] = store.store_name
                    data['store_type'] = store.store_type.value
            
            # Sort stores by sales
            sorted_stores = sorted(store_analytics.values(), key=lambda x: x['total_sales'], reverse=True)
            
            # Add rankings
            for i, store_data in enumerate(sorted_stores):
                store_data['sales_rank'] = i + 1
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_stores': len(stores),
                    'total_sales': total_sales,
                    'total_orders': total_orders,
                    'total_customers': total_customers,
                    'average_sales_per_store': total_sales / len(stores) if stores else Decimal('0.00'),
                    'average_orders_per_store': total_orders / len(stores) if stores else 0
                },
                'stores': sorted_stores
            }
        except SQLAlchemyError as e:
            return {'error': str(e)}


# Create service instance
multi_store_franchise_service = MultiStoreFranchiseService()