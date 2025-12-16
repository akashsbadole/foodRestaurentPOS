"""
Returns & Exchanges service layer for handling comprehensive return management,
exchange processing with variant matching, refund processing and store credit,
and return approval workflows.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload

from models import db
from models.returns_exchanges import (
    ReturnRequest, ReturnItem, ExchangeRequest, ExchangeItem, ReturnPolicy, 
    ReturnWorkflow, ReturnAuditLog, ReturnStatus, ReturnReason, RefundMethod, ExchangeStatus
)
from utils.tenant_query_manager import tenant_scoped, get_tenant_id


class ReturnsExchangesService:
    """Service class for returns and exchanges operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    # Return Request Management
    
    def get_return_requests(self, filters: Optional[Dict] = None) -> List[ReturnRequest]:
        """Get return requests with optional filters"""
        query = ReturnRequest.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'status' in filters:
                query = query.filter(ReturnRequest.status == filters['status'])
            if 'customer_id' in filters:
                query = query.filter(ReturnRequest.customer_id == filters['customer_id'])
            if 'return_reason' in filters:
                query = query.filter(ReturnRequest.return_reason == filters['return_reason'])
            if 'date_from' in filters:
                query = query.filter(ReturnRequest.return_date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(ReturnRequest.return_date <= filters['date_to'])
            if 'approved_by' in filters:
                query = query.filter(ReturnRequest.approved_by == filters['approved_by'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ReturnRequest.return_number.ilike(search_term),
                    ReturnRequest.customer_name.ilike(search_term),
                    ReturnRequest.customer_email.ilike(search_term)
                ))
        
        return query.order_by(desc(ReturnRequest.created_at)).all()
    
    def get_return_request_by_id(self, return_id: int) -> Optional[ReturnRequest]:
        """Get return request by ID with related data"""
        return ReturnRequest.query.options(
            joinedload(ReturnRequest.return_items),
            joinedload(ReturnRequest.customer),
            joinedload(ReturnRequest.original_order),
            joinedload(ReturnRequest.approver),
            joinedload(ReturnRequest.receiver),
            joinedload(ReturnRequest.processor)
        ).filter_by(id=return_id, tenant_id=self.tenant_id).first()
    
    def get_return_request_by_number(self, return_number: str) -> Optional[ReturnRequest]:
        """Get return request by return number"""
        return ReturnRequest.query.filter_by(
            return_number=return_number, 
            tenant_id=self.tenant_id
        ).first()
    
    def create_return_request(self, data: Dict) -> Tuple[bool, Optional[ReturnRequest], str]:
        """Create a new return request"""
        try:
            # Create return request
            return_request = ReturnRequest(
                tenant_id=self.tenant_id,
                return_number=data.get('return_number'),
                original_order_id=data['original_order_id'],
                customer_id=data['customer_id'],
                return_date=datetime.strptime(data['return_date'], '%Y-%m-%d').date() if data.get('return_date') else date.today(),
                status=ReturnStatus.REQUESTED,
                return_reason=data['return_reason'],
                return_reason_details=data.get('return_reason_details'),
                customer_name=data['customer_name'],
                customer_email=data.get('customer_email'),
                customer_phone=data.get('customer_phone'),
                notes=data.get('notes'),
                internal_notes=data.get('internal_notes'),
                customer_notes=data.get('customer_notes')
            )
            
            # Generate return number if not provided
            if not return_request.return_number:
                return_request.generate_return_number()
            
            db.session.add(return_request)
            db.session.flush()  # Get the ID
            
            # Add return items
            for item_data in data.get('return_items', []):
                return_item = ReturnItem(
                    tenant_id=self.tenant_id,
                    return_request_id=return_request.id,
                    product_id=item_data['product_id'],
                    product_name=item_data['product_name'],
                    product_sku=item_data.get('product_sku'),
                    variant_id=item_data.get('variant_id'),
                    variant_name=item_data.get('variant_name'),
                    variant_attributes=item_data.get('variant_attributes'),
                    original_order_item_id=item_data.get('original_order_item_id'),
                    original_quantity=item_data['original_quantity'],
                    original_unit_price=Decimal(str(item_data['original_unit_price'])),
                    original_total_price=Decimal(str(item_data['original_total_price'])),
                    return_quantity=item_data['return_quantity'],
                    return_reason=item_data.get('return_reason'),
                    return_condition=item_data.get('return_condition'),
                    condition_details=item_data.get('condition_details'),
                    unit_price=Decimal(str(item_data.get('unit_price', item_data['original_unit_price']))),
                    total_value=Decimal(str(item_data.get('total_value', 
                        item_data['return_quantity'] * float(item_data.get('unit_price', item_data['original_unit_price'])))),
                    deduction_amount=Decimal(str(item_data.get('deduction_amount', '0'))),
                    deduction_reason=item_data.get('deduction_reason'),
                    refundable_amount=Decimal(str(item_data.get('refundable_amount', 
                        item_data['return_quantity'] * float(item_data.get('unit_price', item_data['original_unit_price'])))),
                    restock_fee=Decimal(str(item_data.get('restock_fee', '0'))),
                    restock_fee_reason=item_data.get('restock_fee_reason'),
                    should_restock=item_data.get('should_restock', True),
                    item_notes=item_data.get('item_notes'),
                    customer_notes=item_data.get('customer_notes')
                )
                
                db.session.add(return_item)
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_request.id,
                action='created',
                action_details={'source': 'customer_request'},
                user_id=data.get('user_id')
            )
            
            db.session.commit()
            return True, return_request, "Return request created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating return request: {str(e)}"
    
    def approve_return_request(self, return_id: int, approver_id: int, approval_data: Dict) -> Tuple[bool, str]:
        """Approve a return request"""
        try:
            return_request = self.get_return_request_by_id(return_id)
            if not return_request:
                return False, "Return request not found"
            
            if return_request.status != ReturnStatus.REQUESTED:
                return False, f"Return request cannot be approved in current status: {return_request.status.value}"
            
            # Update return request
            return_request.status = ReturnStatus.APPROVED
            return_request.approved_by = approver_id
            return_request.approved_at = datetime.utcnow()
            return_request.internal_notes = approval_data.get('internal_notes', return_request.internal_notes)
            
            # Update refund method if provided
            if 'refund_method' in approval_data:
                return_request.refund_method = approval_data['refund_method']
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_id,
                action='approved',
                action_details=approval_data,
                user_id=approver_id
            )
            
            db.session.commit()
            return True, "Return request approved successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error approving return request: {str(e)}"
    
    def reject_return_request(self, return_id: int, approver_id: int, rejection_data: Dict) -> Tuple[bool, str]:
        """Reject a return request"""
        try:
            return_request = self.get_return_request_by_id(return_id)
            if not return_request:
                return False, "Return request not found"
            
            if return_request.status != ReturnStatus.REQUESTED:
                return False, f"Return request cannot be rejected in current status: {return_request.status.value}"
            
            # Update return request
            return_request.status = ReturnStatus.REJECTED
            return_request.approved_by = approver_id
            return_request.approved_at = datetime.utcnow()
            return_request.rejection_reason = rejection_data.get('rejection_reason')
            return_request.internal_notes = rejection_data.get('internal_notes', return_request.internal_notes)
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_id,
                action='rejected',
                action_details=rejection_data,
                user_id=approver_id
            )
            
            db.session.commit()
            return True, "Return request rejected successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error rejecting return request: {str(e)}"
    
    def receive_return_request(self, return_id: int, receiver_id: int, receive_data: Dict) -> Tuple[bool, str]:
        """Mark return request as received"""
        try:
            return_request = self.get_return_request_by_id(return_id)
            if not return_request:
                return False, "Return request not found"
            
            if return_request.status != ReturnStatus.APPROVED:
                return False, f"Return request cannot be received in current status: {return_request.status.value}"
            
            # Update return request
            return_request.status = ReturnStatus.RECEIVED
            return_request.received_by = receiver_id
            return_request.received_at = datetime.utcnow()
            
            # Update return items with actual condition and quantities
            for item_update in receive_data.get('items', []):
                item_id = item_update['item_id']
                return_item = next((item for item in return_request.return_items if item.id == item_id), None)
                
                if return_item:
                    return_item.return_condition = item_update.get('return_condition', return_item.return_condition)
                    return_item.condition_details = item_update.get('condition_details', return_item.condition_details)
                    return_item.return_quantity = item_update.get('actual_quantity', return_item.return_quantity)
                    return_item.deduction_amount = Decimal(str(item_update.get('deduction_amount', return_item.deduction_amount)))
                    return_item.deduction_reason = item_update.get('deduction_reason', return_item.deduction_reason)
                    return_item.refundable_amount = return_item.calculate_refundable_amount()
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_id,
                action='received',
                action_details=receive_data,
                user_id=receiver_id
            )
            
            db.session.commit()
            return True, "Return request received successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error receiving return request: {str(e)}"
    
    def process_return_request(self, return_id: int, processor_id: int, process_data: Dict) -> Tuple[bool, str]:
        """Process a return request and issue refund/store credit"""
        try:
            return_request = self.get_return_request_by_id(return_id)
            if not return_request:
                return False, "Return request not found"
            
            if return_request.status != ReturnStatus.RECEIVED:
                return False, f"Return request cannot be processed in current status: {return_request.status.value}"
            
            # Calculate total refund amount
            total_refund = sum(item.refundable_amount for item in return_request.return_items)
            return_request.total_refund_amount = total_refund
            return_request.refund_method = process_data.get('refund_method')
            
            # Process refund based on method
            refund_method = process_data.get('refund_method')
            if refund_method == RefundMethod.STORE_CREDIT:
                return_request.store_credit_issued = total_refund
                if process_data.get('store_credit_expiry_days'):
                    return_request.store_credit_expiry = date.today() + timedelta(days=process_data['store_credit_expiry_days'])
                return_request.store_credit_reference = process_data.get('store_credit_reference')
            
            # Update return request
            return_request.status = ReturnStatus.PROCESSING
            return_request.processed_by = processor_id
            return_request.processed_at = datetime.utcnow()
            
            # Restock items if applicable
            for item_update in process_data.get('restock_items', []):
                item_id = item_update['item_id']
                return_item = next((item for item in return_request.return_items if item.id == item_id), None)
                
                if return_item and return_item.should_restock:
                    return_item.restocked_quantity = item_update.get('restocked_quantity', return_item.return_quantity)
                    return_item.restocked_at = datetime.utcnow()
                    return_item.restocked_by = processor_id
                    
                    # Update inventory (this would need to be implemented based on inventory system)
                    # self._update_inventory_for_restock(return_item)
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_id,
                action='processed',
                action_details=process_data,
                user_id=processor_id
            )
            
            db.session.commit()
            return True, "Return request processed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing return request: {str(e)}"
    
    def complete_return_request(self, return_id: int, processor_id: int, completion_data: Dict) -> Tuple[bool, str]:
        """Complete a return request"""
        try:
            return_request = self.get_return_request_by_id(return_id)
            if not return_request:
                return False, "Return request not found"
            
            if return_request.status != ReturnStatus.PROCESSING:
                return False, f"Return request cannot be completed in current status: {return_request.status.value}"
            
            # Update return request
            return_request.status = ReturnStatus.COMPLETED
            return_request.refund_processed_at = datetime.utcnow()
            return_request.refund_transaction_id = completion_data.get('refund_transaction_id')
            
            # Create audit log
            self._create_audit_log(
                return_request_id=return_id,
                action='completed',
                action_details=completion_data,
                user_id=processor_id
            )
            
            db.session.commit()
            return True, "Return request completed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error completing return request: {str(e)}"
    
    # Exchange Request Management
    
    def get_exchange_requests(self, filters: Optional[Dict] = None) -> List[ExchangeRequest]:
        """Get exchange requests with optional filters"""
        query = ExchangeRequest.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'status' in filters:
                query = query.filter(ExchangeRequest.status == filters['status'])
            if 'customer_id' in filters:
                query = query.filter(ExchangeRequest.customer_id == filters['customer_id'])
            if 'return_request_id' in filters:
                query = query.filter(ExchangeRequest.return_request_id == filters['return_request_id'])
            if 'date_from' in filters:
                query = query.filter(ExchangeRequest.exchange_date >= filters['date_from'])
            if 'date_to' in filters:
                query = query.filter(ExchangeRequest.exchange_date <= filters['date_to'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ExchangeRequest.exchange_number.ilike(search_term),
                    ExchangeRequest.customer_name.ilike(search_term),
                    ExchangeRequest.customer_email.ilike(search_term)
                ))
        
        return query.order_by(desc(ExchangeRequest.created_at)).all()
    
    def get_exchange_request_by_id(self, exchange_id: int) -> Optional[ExchangeRequest]:
        """Get exchange request by ID with related data"""
        return ExchangeRequest.query.options(
            joinedload(ExchangeRequest.exchange_items),
            joinedload(ExchangeRequest.customer),
            joinedload(ExchangeRequest.original_order),
            joinedload(ExchangeRequest.approver),
            joinedload(ExchangeRequest.processor),
            joinedload(ExchangeRequest.shipper)
        ).filter_by(id=exchange_id, tenant_id=self.tenant_id).first()
    
    def create_exchange_request(self, data: Dict) -> Tuple[bool, Optional[ExchangeRequest], str]:
        """Create a new exchange request"""
        try:
            # Create exchange request
            exchange_request = ExchangeRequest(
                tenant_id=self.tenant_id,
                return_request_id=data.get('return_request_id'),
                exchange_number=data.get('exchange_number'),
                original_order_id=data['original_order_id'],
                customer_id=data['customer_id'],
                exchange_date=datetime.strptime(data['exchange_date'], '%Y-%m-%d').date() if data.get('exchange_date') else date.today(),
                status=ExchangeStatus.REQUESTED,
                exchange_reason=data['exchange_reason'],
                exchange_reason_details=data.get('exchange_reason_details'),
                notes=data.get('notes'),
                internal_notes=data.get('internal_notes'),
                customer_notes=data.get('customer_notes')
            )
            
            # Generate exchange number if not provided
            if not exchange_request.exchange_number:
                exchange_request.generate_exchange_number()
            
            db.session.add(exchange_request)
            db.session.flush()  # Get the ID
            
            # Add exchange items
            for item_data in data.get('exchange_items', []):
                exchange_item = ExchangeItem(
                    tenant_id=self.tenant_id,
                    exchange_request_id=exchange_request.id,
                    # Original item details
                    original_product_id=item_data['original_product_id'],
                    original_product_name=item_data['original_product_name'],
                    original_product_sku=item_data.get('original_product_sku'),
                    original_variant_id=item_data.get('original_variant_id'),
                    original_variant_name=item_data.get('original_variant_name'),
                    original_variant_attributes=item_data.get('original_variant_attributes'),
                    original_quantity=item_data['original_quantity'],
                    original_unit_price=Decimal(str(item_data['original_unit_price'])),
                    original_total_price=Decimal(str(item_data['original_total_price'])),
                    # Exchange item details
                    exchange_product_id=item_data['exchange_product_id'],
                    exchange_product_name=item_data['exchange_product_name'],
                    exchange_product_sku=item_data.get('exchange_product_sku'),
                    exchange_variant_id=item_data.get('exchange_variant_id'),
                    exchange_variant_name=item_data.get('exchange_variant_name'),
                    exchange_variant_attributes=item_data.get('exchange_variant_attributes'),
                    exchange_quantity=item_data['exchange_quantity'],
                    exchange_unit_price=Decimal(str(item_data['exchange_unit_price'])),
                    exchange_total_price=Decimal(str(item_data['exchange_total_price'])),
                    # Availability
                    original_available=item_data.get('original_available', True),
                    exchange_available=item_data.get('exchange_available', True),
                    exchange_stock_quantity=item_data.get('exchange_stock_quantity', 0),
                    exchange_reserved_quantity=item_data.get('exchange_reserved_quantity', 0),
                    # Additional information
                    exchange_reason=item_data.get('exchange_reason'),
                    item_notes=item_data.get('item_notes'),
                    customer_notes=item_data.get('customer_notes')
                )
                
                db.session.add(exchange_item)
            
            # Calculate price difference
            price_difference = exchange_request.calculate_price_difference()
            exchange_request.price_difference = price_difference
            
            if price_difference > 0:
                exchange_request.additional_payment_required = price_difference
            else:
                exchange_request.refund_amount = abs(price_difference)
            
            # Create audit log
            self._create_audit_log(
                exchange_request_id=exchange_request.id,
                action='created',
                action_details={'source': 'customer_request'},
                user_id=data.get('user_id')
            )
            
            db.session.commit()
            return True, exchange_request, "Exchange request created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating exchange request: {str(e)}"
    
    def approve_exchange_request(self, exchange_id: int, approver_id: int, approval_data: Dict) -> Tuple[bool, str]:
        """Approve an exchange request"""
        try:
            exchange_request = self.get_exchange_request_by_id(exchange_id)
            if not exchange_request:
                return False, "Exchange request not found"
            
            if exchange_request.status != ExchangeStatus.REQUESTED:
                return False, f"Exchange request cannot be approved in current status: {exchange_request.status.value}"
            
            # Update exchange request
            exchange_request.status = ExchangeStatus.APPROVED
            exchange_request.approved_by = approver_id
            exchange_request.approved_at = datetime.utcnow()
            exchange_request.internal_notes = approval_data.get('internal_notes', exchange_request.internal_notes)
            
            # Reserve exchange items in inventory
            for item in exchange_request.exchange_items:
                item.exchange_reserved_quantity = item.exchange_quantity
                # Update inventory reservation (this would need to be implemented based on inventory system)
                # self._reserve_inventory_for_exchange(item)
            
            # Create audit log
            self._create_audit_log(
                exchange_request_id=exchange_id,
                action='approved',
                action_details=approval_data,
                user_id=approver_id
            )
            
            db.session.commit()
            return True, "Exchange request approved successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error approving exchange request: {str(e)}"
    
    def process_exchange_request(self, exchange_id: int, processor_id: int, process_data: Dict) -> Tuple[bool, str]:
        """Process an exchange request"""
        try:
            exchange_request = self.get_exchange_request_by_id(exchange_id)
            if not exchange_request:
                return False, "Exchange request not found"
            
            if exchange_request.status != ExchangeStatus.APPROVED:
                return False, f"Exchange request cannot be processed in current status: {exchange_request.status.value}"
            
            # Update exchange request
            exchange_request.status = ExchangeStatus.PROCESSING
            exchange_request.processed_by = processor_id
            exchange_request.processed_at = datetime.utcnow()
            
            # Process payment if additional payment required
            if exchange_request.additional_payment_required > 0:
                payment_data = process_data.get('payment_data', {})
                # Process payment (this would need to be implemented based on payment system)
                # self._process_additional_payment(exchange_request, payment_data)
                exchange_request.payment_processed_at = datetime.utcnow()
            
            # Create audit log
            self._create_audit_log(
                exchange_request_id=exchange_id,
                action='processed',
                action_details=process_data,
                user_id=processor_id
            )
            
            db.session.commit()
            return True, "Exchange request processed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing exchange request: {str(e)}"
    
    def ship_exchange_request(self, exchange_id: int, shipper_id: int, shipping_data: Dict) -> Tuple[bool, str]:
        """Ship an exchange request"""
        try:
            exchange_request = self.get_exchange_request_by_id(exchange_id)
            if not exchange_request:
                return False, "Exchange request not found"
            
            if exchange_request.status != ExchangeStatus.PROCESSING:
                return False, f"Exchange request cannot be shipped in current status: {exchange_request.status.value}"
            
            # Update exchange request
            exchange_request.status = ExchangeStatus.SHIPPED
            exchange_request.shipped_by = shipper_id
            exchange_request.shipped_at = datetime.utcnow()
            exchange_request.tracking_number = shipping_data.get('tracking_number')
            exchange_request.shipping_carrier = shipping_data.get('shipping_carrier')
            
            # Update inventory
            for item in exchange_request.exchange_items:
                # Decrease inventory for exchange items
                # self._decrease_inventory_for_exchange(item)
                pass
            
            # Create audit log
            self._create_audit_log(
                exchange_request_id=exchange_id,
                action='shipped',
                action_details=shipping_data,
                user_id=shipper_id
            )
            
            db.session.commit()
            return True, "Exchange request shipped successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error shipping exchange request: {str(e)}"
    
    # Return Policy Management
    
    def get_return_policies(self, filters: Optional[Dict] = None) -> List[ReturnPolicy]:
        """Get return policies with optional filters"""
        query = ReturnPolicy.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(ReturnPolicy.is_active == filters['is_active'])
            if 'is_default' in filters:
                query = query.filter(ReturnPolicy.is_default == filters['is_default'])
            if 'policy_type' in filters:
                query = query.filter(ReturnPolicy.policy_type == filters['policy_type'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ReturnPolicy.name.ilike(search_term),
                    ReturnPolicy.description.ilike(search_term)
                ))
        
        return query.order_by(ReturnPolicy.is_default.desc(), ReturnPolicy.name).all()
    
    def get_return_policy_by_id(self, policy_id: int) -> Optional[ReturnPolicy]:
        """Get return policy by ID"""
        return ReturnPolicy.query.filter_by(id=policy_id, tenant_id=self.tenant_id).first()
    
    def get_default_return_policy(self) -> Optional[ReturnPolicy]:
        """Get the default return policy"""
        return ReturnPolicy.query.filter_by(
            is_default=True, 
            tenant_id=self.tenant_id
        ).first()
    
    def create_return_policy(self, data: Dict) -> Tuple[bool, Optional[ReturnPolicy], str]:
        """Create a new return policy"""
        try:
            # If this is set as default, unset other default policies
            if data.get('is_default', False):
                ReturnPolicy.query.filter_by(
                    tenant_id=self.tenant_id, 
                    is_default=True
                ).update({'is_default': False})
            
            policy = ReturnPolicy(
                tenant_id=self.tenant_id,
                name=data['name'],
                description=data.get('description'),
                policy_type=data['policy_type'],
                return_period_days=data.get('return_period_days', 30),
                exchange_period_days=data.get('exchange_period_days', 30),
                require_original_receipt=data.get('require_original_receipt', True),
                require_original_packaging=data.get('require_original_packaging', False),
                require_unused_condition=data.get('require_unused_condition', False),
                require_tags_attached=data.get('require_tags_attached', False),
                restocking_fee_percentage=Decimal(str(data.get('restocking_fee_percentage', '0'))),
                restocking_fee_fixed=Decimal(str(data.get('restocking_fee_fixed', '0'))),
                max_restocking_fee=Decimal(str(data.get('max_restocking_fee'))) if data.get('max_restocking_fee') else None,
                allowed_refund_methods=data.get('allowed_refund_methods'),
                default_refund_method=data.get('default_refund_method'),
                store_credit_expiry_days=data.get('store_credit_expiry_days'),
                applies_to_all_products=data.get('applies_to_all_products', True),
                product_ids=data.get('product_ids'),
                category_ids=data.get('category_ids'),
                excluded_product_ids=data.get('excluded_product_ids'),
                excluded_category_ids=data.get('excluded_category_ids'),
                holiday_return_extension=data.get('holiday_return_extension', 0),
                defective_item_policy=data.get('defective_item_policy'),
                damaged_item_policy=data.get('damaged_item_policy'),
                is_active=data.get('is_active', True),
                is_default=data.get('is_default', False),
                created_by=data.get('created_by')
            )
            
            db.session.add(policy)
            db.session.commit()
            return True, policy, "Return policy created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating return policy: {str(e)}"
    
    def get_applicable_return_policy(self, product_id: int, category_ids: List[int] = None) -> Optional[ReturnPolicy]:
        """Get the most applicable return policy for a product"""
        # Get all active policies for this tenant
        policies = ReturnPolicy.query.filter_by(
            tenant_id=self.tenant_id,
            is_active=True
        ).order_by(ReturnPolicy.is_default.desc()).all()
        
        for policy in policies:
            if policy.is_applicable_to_product(product_id, category_ids):
                return policy
        
        return None
    
    # Return Workflow Management
    
    def get_return_workflows(self, filters: Optional[Dict] = None) -> List[ReturnWorkflow]:
        """Get return workflows with optional filters"""
        query = ReturnWorkflow.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'is_active' in filters:
                query = query.filter(ReturnWorkflow.is_active == filters['is_active'])
            if 'is_default' in filters:
                query = query.filter(ReturnWorkflow.is_default == filters['is_default'])
            if 'workflow_type' in filters:
                query = query.filter(ReturnWorkflow.workflow_type == filters['workflow_type'])
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    ReturnWorkflow.name.ilike(search_term),
                    ReturnWorkflow.description.ilike(search_term)
                ))
        
        return query.order_by(ReturnWorkflow.is_default.desc(), ReturnWorkflow.name).all()
    
    def get_return_workflow_by_id(self, workflow_id: int) -> Optional[ReturnWorkflow]:
        """Get return workflow by ID"""
        return ReturnWorkflow.query.filter_by(id=workflow_id, tenant_id=self.tenant_id).first()
    
    def get_applicable_workflow(self, return_request: ReturnRequest) -> Optional[ReturnWorkflow]:
        """Get the most applicable workflow for a return request"""
        # Get all active workflows for this tenant
        workflows = ReturnWorkflow.query.filter_by(
            tenant_id=self.tenant_id,
            is_active=True
        ).order_by(ReturnWorkflow.is_default.desc()).all()
        
        for workflow in workflows:
            if workflow.is_triggered(return_request):
                return workflow
        
        return None
    
    # Analytics and Reporting
    
    def get_returns_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """Get returns analytics for a date range"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Return statistics
            return_stats = db.session.query(
                func.count(ReturnRequest.id).label('total_returns'),
                func.sum(ReturnRequest.total_refund_amount).label('total_refunded'),
                func.count(func.distinct(ReturnRequest.customer_id)).label('unique_customers')
            ).filter(
                ReturnRequest.tenant_id == self.tenant_id,
                ReturnRequest.return_date >= start_date,
                ReturnRequest.return_date <= end_date
            ).first()
            
            # Returns by reason
            reason_stats = db.session.query(
                ReturnRequest.return_reason,
                func.count(ReturnRequest.id).label('count'),
                func.sum(ReturnRequest.total_refund_amount).label('total_refund')
            ).filter(
                ReturnRequest.tenant_id == self.tenant_id,
                ReturnRequest.return_date >= start_date,
                ReturnRequest.return_date <= end_date
            ).group_by(ReturnRequest.return_reason).all()
            
            # Returns by status
            status_stats = db.session.query(
                ReturnRequest.status,
                func.count(ReturnRequest.id).label('count')
            ).filter(
                ReturnRequest.tenant_id == self.tenant_id,
                ReturnRequest.return_date >= start_date,
                ReturnRequest.return_date <= end_date
            ).group_by(ReturnRequest.status).all()
            
            # Exchange statistics
            exchange_stats = db.session.query(
                func.count(ExchangeRequest.id).label('total_exchanges'),
                func.sum(ExchangeRequest.price_difference).label('total_price_difference'),
                func.count(func.distinct(ExchangeRequest.customer_id)).label('unique_customers')
            ).filter(
                ExchangeRequest.tenant_id == self.tenant_id,
                ExchangeRequest.exchange_date >= start_date,
                ExchangeRequest.exchange_date <= end_date
            ).first()
            
            return {
                'returns': {
                    'total_returns': return_stats.total_returns or 0,
                    'total_refunded': float(return_stats.total_refunded or 0),
                    'unique_customers': return_stats.unique_customers or 0,
                    'by_reason': [
                        {
                            'reason': stat.return_reason.value,
                            'count': stat.count,
                            'total_refund': float(stat.total_refund or 0)
                        } for stat in reason_stats
                    ],
                    'by_status': [
                        {
                            'status': stat.status.value,
                            'count': stat.count
                        } for stat in status_stats
                    ]
                },
                'exchanges': {
                    'total_exchanges': exchange_stats.total_exchanges or 0,
                    'total_price_difference': float(exchange_stats.total_price_difference or 0),
                    'unique_customers': exchange_stats.unique_customers or 0
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {
                'error': f"Error generating returns analytics: {str(e)}",
                'returns': {},
                'exchanges': {}
            }
    
    # Helper Methods
    
    def _create_audit_log(self, return_request_id: Optional[int] = None, 
                         exchange_request_id: Optional[int] = None,
                         action: str = '', action_details: Dict = None, 
                         user_id: Optional[int] = None) -> None:
        """Create an audit log entry"""
        audit_log = ReturnAuditLog(
            tenant_id=self.tenant_id,
            return_request_id=return_request_id,
            exchange_request_id=exchange_request_id,
            action=action,
            action_details=action_details or {},
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(audit_log)
    
    def _generate_return_number(self) -> str:
        """Generate a unique return number"""
        prefix = "RTN"
        date_str = date.today().strftime("%Y%m%d")
        
        # Get count of returns for today
        today_count = ReturnRequest.query.filter(
            ReturnRequest.tenant_id == self.tenant_id,
            ReturnRequest.return_date == date.today()
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:04d}"
    
    def _generate_exchange_number(self) -> str:
        """Generate a unique exchange number"""
        prefix = "EXC"
        date_str = date.today().strftime("%Y%m%d")
        
        # Get count of exchanges for today
        today_count = ExchangeRequest.query.filter(
            ExchangeRequest.tenant_id == self.tenant_id,
            ExchangeRequest.exchange_date == date.today()
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:04d}"


# Factory function to create service instances
def create_returns_exchanges_service(tenant_id: str) -> ReturnsExchangesService:
    """Factory function to create a returns & exchanges service instance"""
    return ReturnsExchangesService(tenant_id)