"""
Service layer for Online Integration module handling online order processing, click-and-collect functionality,
home delivery management, and third-party integration framework.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, contains_eager

from models import db
from models.online_integration import (
    OnlineOrder, ClickAndCollect, HomeDelivery, DeliveryPartner,
    ThirdPartyIntegration, OnlineOrderHistory, OnlineOrderReview,
    OnlineOrderAnalytics, OnlineOrderStatus, DeliveryType, ThirdPartyPlatform
)
from models.feature_flag import feature_flag_service


class OnlineIntegrationService:
    """Service class for online integration operations"""
    
    def __init__(self):
        self.feature_service = feature_flag_service
    
    # Online Order Management
    
    def create_online_order(self, order_data: Dict[str, Any]) -> Tuple[Optional[OnlineOrder], Optional[str]]:
        """Create a new online order"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('online_orders', order_data.get('tenant_id')):
                return None, "Online orders feature is not enabled"
            
            # Create order
            order = OnlineOrder(
                tenant_id=order_data.get('tenant_id'),
                platform_order_id=order_data.get('platform_order_id'),
                platform=ThirdPartyPlatform(order_data.get('platform', 'none')),
                customer_id=order_data.get('customer_id'),
                customer_name=order_data.get('customer_name'),
                customer_email=order_data.get('customer_email'),
                customer_phone=order_data.get('customer_phone'),
                delivery_type=DeliveryType(order_data.get('delivery_type')),
                delivery_address=order_data.get('delivery_address'),
                delivery_instructions=order_data.get('delivery_instructions'),
                preferred_delivery_time=order_data.get('preferred_delivery_time'),
                delivery_time_slot=order_data.get('delivery_time_slot'),
                store_id=order_data.get('store_id'),
                pickup_store=order_data.get('pickup_store'),
                order_items=order_data.get('order_items', []),
                subtotal=order_data.get('subtotal'),
                tax_amount=order_data.get('tax_amount', Decimal('0.00')),
                delivery_fee=order_data.get('delivery_fee', Decimal('0.00')),
                platform_fee=order_data.get('platform_fee', Decimal('0.00')),
                discount_amount=order_data.get('discount_amount', Decimal('0.00')),
                tip_amount=order_data.get('tip_amount', Decimal('0.00')),
                total_amount=order_data.get('total_amount'),
                payment_status=order_data.get('payment_status', 'pending'),
                payment_method=order_data.get('payment_method'),
                payment_reference=order_data.get('payment_reference'),
                notes=order_data.get('notes'),
                customer_notes=order_data.get('customer_notes'),
                platform_notes=order_data.get('platform_notes'),
                created_by=order_data.get('created_by')
            )
            
            # Generate order number
            order.generate_order_number()
            
            db.session.add(order)
            db.session.commit()
            
            # Create order history
            self.create_order_history(
                order.id, None, OnlineOrderStatus.PENDING,
                order_data.get('created_by'), "Order created"
            )
            
            return order, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_online_order(self, order_id: int, tenant_id: str) -> Optional[OnlineOrder]:
        """Get online order by ID"""
        return OnlineOrder.query.filter_by(id=order_id, tenant_id=tenant_id).first()
    
    def get_online_orders(self, tenant_id: str, status: Optional[str] = None, 
                         platform: Optional[str] = None, store_id: Optional[int] = None,
                         start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[OnlineOrder]:
        """Get online orders with filters"""
        query = OnlineOrder.query.filter_by(tenant_id=tenant_id)
        
        if status:
            query = query.filter_by(status=OnlineOrderStatus(status))
        if platform:
            query = query.filter_by(platform=ThirdPartyPlatform(platform))
        if store_id:
            query = query.filter_by(store_id=store_id)
        if start_date:
            query = query.filter(OnlineOrder.created_at >= start_date)
        if end_date:
            query = query.filter(OnlineOrder.created_at <= end_date)
        
        return query.order_by(desc(OnlineOrder.created_at)).all()
    
    def update_online_order(self, order_id: int, order_data: Dict[str, Any]) -> Tuple[Optional[OnlineOrder], Optional[str]]:
        """Update online order"""
        try:
            order = OnlineOrder.query.filter_by(id=order_id, tenant_id=order_data.get('tenant_id')).first()
            if not order:
                return None, "Order not found"
            
            previous_status = order.status
            
            # Update fields
            if 'customer_name' in order_data:
                order.customer_name = order_data['customer_name']
            if 'customer_email' in order_data:
                order.customer_email = order_data['customer_email']
            if 'customer_phone' in order_data:
                order.customer_phone = order_data['customer_phone']
            if 'delivery_type' in order_data:
                order.delivery_type = DeliveryType(order_data['delivery_type'])
            if 'delivery_address' in order_data:
                order.delivery_address = order_data['delivery_address']
            if 'delivery_instructions' in order_data:
                order.delivery_instructions = order_data['delivery_instructions']
            if 'preferred_delivery_time' in order_data:
                order.preferred_delivery_time = order_data['preferred_delivery_time']
            if 'delivery_time_slot' in order_data:
                order.delivery_time_slot = order_data['delivery_time_slot']
            if 'order_items' in order_data:
                order.order_items = order_data['order_items']
            if 'subtotal' in order_data:
                order.subtotal = order_data['subtotal']
            if 'tax_amount' in order_data:
                order.tax_amount = order_data['tax_amount']
            if 'delivery_fee' in order_data:
                order.delivery_fee = order_data['delivery_fee']
            if 'platform_fee' in order_data:
                order.platform_fee = order_data['platform_fee']
            if 'discount_amount' in order_data:
                order.discount_amount = order_data['discount_amount']
            if 'tip_amount' in order_data:
                order.tip_amount = order_data['tip_amount']
            if 'total_amount' in order_data:
                order.total_amount = order_data['total_amount']
            if 'payment_status' in order_data:
                order.payment_status = order_data['payment_status']
            if 'payment_method' in order_data:
                order.payment_method = order_data['payment_method']
            if 'payment_reference' in order_data:
                order.payment_reference = order_data['payment_reference']
            if 'status' in order_data:
                order.status = OnlineOrderStatus(order_data['status'])
            if 'assigned_to' in order_data:
                order.assigned_to = order_data['assigned_to']
            if 'delivery_assigned_to' in order_data:
                order.delivery_assigned_to = order_data['delivery_assigned_to']
            if 'notes' in order_data:
                order.notes = order_data['notes']
            if 'customer_notes' in order_data:
                order.customer_notes = order_data['customer_notes']
            if 'platform_notes' in order_data:
                order.platform_notes = order_data['platform_notes']
            
            order.updated_at = datetime.utcnow()
            order.updated_by = order_data.get('updated_by')
            
            # Update status timestamps
            if 'status' in order_data:
                new_status = OnlineOrderStatus(order_data['status'])
                if new_status == OnlineOrderStatus.CONFIRMED and not order.confirmed_at:
                    order.confirmed_at = datetime.utcnow()
                elif new_status == OnlineOrderStatus.PROCESSING and not order.processing_started_at:
                    order.processing_started_at = datetime.utcnow()
                elif new_status == OnlineOrderStatus.READY_FOR_PICKUP and not order.ready_for_pickup_at:
                    order.ready_for_pickup_at = datetime.utcnow()
                elif new_status == OnlineOrderStatus.OUT_FOR_DELIVERY and not order.out_for_delivery_at:
                    order.out_for_delivery_at = datetime.utcnow()
                elif new_status == OnlineOrderStatus.DELIVERED and not order.delivered_at:
                    order.delivered_at = datetime.utcnow()
                elif new_status == OnlineOrderStatus.CANCELLED and not order.cancelled_at:
                    order.cancelled_at = datetime.utcnow()
                    order.cancellation_reason = order_data.get('cancellation_reason')
            
            db.session.commit()
            
            # Create order history if status changed
            if 'status' in order_data and previous_status != order.status:
                self.create_order_history(
                    order.id, previous_status, order.status,
                    order_data.get('updated_by'), order_data.get('status_reason')
                )
            
            return order, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def confirm_online_order(self, order_id: int, confirmed_by: int, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Confirm an online order"""
        try:
            order = OnlineOrder.query.filter_by(id=order_id, tenant_id=tenant_id).first()
            if not order:
                return False, "Order not found"
            
            if order.status != OnlineOrderStatus.PENDING:
                return False, "Order must be in pending status to confirm"
            
            order.status = OnlineOrderStatus.CONFIRMED
            order.confirmed_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create order history
            self.create_order_history(
                order.id, OnlineOrderStatus.PENDING, OnlineOrderStatus.CONFIRMED,
                confirmed_by, "Order confirmed"
            )
            
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    def cancel_online_order(self, order_id: int, cancelled_by: int, tenant_id: str, 
                          cancellation_reason: str) -> Tuple[bool, Optional[str]]:
        """Cancel an online order"""
        try:
            order = OnlineOrder.query.filter_by(id=order_id, tenant_id=tenant_id).first()
            if not order:
                return False, "Order not found"
            
            if order.status in [OnlineOrderStatus.DELIVERED, OnlineOrderStatus.CANCELLED]:
                return False, "Cannot cancel delivered or already cancelled order"
            
            previous_status = order.status
            order.status = OnlineOrderStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            order.cancellation_reason = cancellation_reason
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create order history
            self.create_order_history(
                order.id, previous_status, OnlineOrderStatus.CANCELLED,
                cancelled_by, cancellation_reason
            )
            
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    def create_order_history(self, order_id: int, previous_status: Optional[OnlineOrderStatus], 
                           new_status: OnlineOrderStatus, changed_by: Optional[int], 
                           change_reason: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Create order history record"""
        try:
            history = OnlineOrderHistory(
                tenant_id=OnlineOrder.query.get(order_id).tenant_id,
                online_order_id=order_id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            db.session.add(history)
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Click and Collect Management
    
    def create_click_and_collect(self, collect_data: Dict[str, Any]) -> Tuple[Optional[ClickAndCollect], Optional[str]]:
        """Create a new click and collect record"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('click_and_collect', collect_data.get('tenant_id')):
                return None, "Click and collect feature is not enabled"
            
            # Create click and collect
            collect = ClickAndCollect(
                tenant_id=collect_data.get('tenant_id'),
                online_order_id=collect_data.get('online_order_id'),
                pickup_instructions=collect_data.get('pickup_instructions'),
                pickup_area=collect_data.get('pickup_area'),
                preferred_pickup_time=collect_data.get('preferred_pickup_time'),
                scheduled_pickup_time=collect_data.get('scheduled_pickup_time'),
                pickup_time_slot=collect_data.get('pickup_time_slot'),
                pickup_customer_name=collect_data.get('pickup_customer_name'),
                pickup_customer_phone=collect_data.get('pickup_customer_phone'),
                pickup_customer_email=collect_data.get('pickup_customer_email'),
                pickup_vehicle_details=collect_data.get('pickup_vehicle_details'),
                notes=collect_data.get('notes')
            )
            
            # Generate pickup code
            collect.generate_pickup_code()
            
            db.session.add(collect)
            db.session.commit()
            
            return collect, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_click_and_collect(self, collect_id: int, tenant_id: str) -> Optional[ClickAndCollect]:
        """Get click and collect by ID"""
        return ClickAndCollect.query.filter_by(id=collect_id, tenant_id=tenant_id).first()
    
    def get_click_and_collect_by_order(self, order_id: int, tenant_id: str) -> Optional[ClickAndCollect]:
        """Get click and collect by order ID"""
        return ClickAndCollect.query.filter_by(online_order_id=order_id, tenant_id=tenant_id).first()
    
    def update_click_and_collect(self, collect_id: int, collect_data: Dict[str, Any]) -> Tuple[Optional[ClickAndCollect], Optional[str]]:
        """Update click and collect"""
        try:
            collect = ClickAndCollect.query.filter_by(id=collect_id, tenant_id=collect_data.get('tenant_id')).first()
            if not collect:
                return None, "Click and collect record not found"
            
            # Update fields
            if 'pickup_instructions' in collect_data:
                collect.pickup_instructions = collect_data['pickup_instructions']
            if 'pickup_area' in collect_data:
                collect.pickup_area = collect_data['pickup_area']
            if 'preferred_pickup_time' in collect_data:
                collect.preferred_pickup_time = collect_data['preferred_pickup_time']
            if 'scheduled_pickup_time' in collect_data:
                collect.scheduled_pickup_time = collect_data['scheduled_pickup_time']
            if 'pickup_time_slot' in collect_data:
                collect.pickup_time_slot = collect_data['pickup_time_slot']
            if 'pickup_customer_name' in collect_data:
                collect.pickup_customer_name = collect_data['pickup_customer_name']
            if 'pickup_customer_phone' in collect_data:
                collect.pickup_customer_phone = collect_data['pickup_customer_phone']
            if 'pickup_customer_email' in collect_data:
                collect.pickup_customer_email = collect_data['pickup_customer_email']
            if 'pickup_vehicle_details' in collect_data:
                collect.pickup_vehicle_details = collect_data['pickup_vehicle_details']
            if 'is_ready' in collect_data:
                collect.is_ready = collect_data['is_ready']
            if 'is_picked_up' in collect_data:
                collect.is_picked_up = collect_data['is_picked_up']
                if collect_data['is_picked_up'] and not collect.actual_pickup_time:
                    collect.actual_pickup_time = datetime.utcnow()
            if 'prepared_by' in collect_data:
                collect.prepared_by = collect_data['prepared_by']
            if 'handed_over_by' in collect_data:
                collect.handed_over_by = collect_data['handed_over_by']
            if 'notes' in collect_data:
                collect.notes = collect_data['notes']
            
            collect.updated_at = datetime.utcnow()
            
            db.session.commit()
            return collect, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def mark_ready_for_pickup(self, collect_id: int, prepared_by: int, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Mark click and collect as ready for pickup"""
        try:
            collect = ClickAndCollect.query.filter_by(id=collect_id, tenant_id=tenant_id).first()
            if not collect:
                return False, "Click and collect record not found"
            
            collect.is_ready = True
            collect.prepared_by = prepared_by
            collect.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    def complete_pickup(self, collect_id: int, handed_over_by: int, tenant_id: str) -> Tuple[bool, Optional[str]]:
        """Complete click and collect pickup"""
        try:
            collect = ClickAndCollect.query.filter_by(id=collect_id, tenant_id=tenant_id).first()
            if not collect:
                return False, "Click and collect record not found"
            
            if not collect.is_ready:
                return False, "Order must be ready for pickup first"
            
            collect.is_picked_up = True
            collect.handed_over_by = handed_over_by
            collect.actual_pickup_time = datetime.utcnow()
            collect.updated_at = datetime.utcnow()
            
            # Update order status
            order = collect.online_order
            order.status = OnlineOrderStatus.DELIVERED
            order.delivered_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Home Delivery Management
    
    def create_home_delivery(self, delivery_data: Dict[str, Any]) -> Tuple[Optional[HomeDelivery], Optional[str]]:
        """Create a new home delivery record"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('home_delivery', delivery_data.get('tenant_id')):
                return None, "Home delivery feature is not enabled"
            
            # Create home delivery
            delivery = HomeDelivery(
                tenant_id=delivery_data.get('tenant_id'),
                online_order_id=delivery_data.get('online_order_id'),
                delivery_address=delivery_data.get('delivery_address'),
                delivery_latitude=delivery_data.get('delivery_latitude'),
                delivery_longitude=delivery_data.get('delivery_longitude'),
                delivery_instructions=delivery_data.get('delivery_instructions'),
                landmark=delivery_data.get('landmark'),
                preferred_delivery_time=delivery_data.get('preferred_delivery_time'),
                scheduled_delivery_time=delivery_data.get('scheduled_delivery_time'),
                delivery_time_slot=delivery_data.get('delivery_time_slot'),
                delivery_partner_id=delivery_data.get('delivery_partner_id'),
                delivery_partner_name=delivery_data.get('delivery_partner_name'),
                delivery_partner_phone=delivery_data.get('delivery_partner_phone'),
                delivery_partner_vehicle=delivery_data.get('delivery_partner_vehicle'),
                tracking_number=delivery_data.get('tracking_number'),
                tracking_url=delivery_data.get('tracking_url'),
                estimated_delivery_time=delivery_data.get('estimated_delivery_time'),
                delivery_distance=delivery_data.get('delivery_distance'),
                delivery_duration=delivery_data.get('delivery_duration'),
                notes=delivery_data.get('notes'),
                delivery_notes=delivery_data.get('delivery_notes')
            )
            
            db.session.add(delivery)
            db.session.commit()
            
            return delivery, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_home_delivery(self, delivery_id: int, tenant_id: str) -> Optional[HomeDelivery]:
        """Get home delivery by ID"""
        return HomeDelivery.query.filter_by(id=delivery_id, tenant_id=tenant_id).first()
    
    def get_home_delivery_by_order(self, order_id: int, tenant_id: str) -> Optional[HomeDelivery]:
        """Get home delivery by order ID"""
        return HomeDelivery.query.filter_by(online_order_id=order_id, tenant_id=tenant_id).first()
    
    def update_home_delivery(self, delivery_id: int, delivery_data: Dict[str, Any]) -> Tuple[Optional[HomeDelivery], Optional[str]]:
        """Update home delivery"""
        try:
            delivery = HomeDelivery.query.filter_by(id=delivery_id, tenant_id=delivery_data.get('tenant_id')).first()
            if not delivery:
                return None, "Home delivery record not found"
            
            # Update fields
            if 'delivery_address' in delivery_data:
                delivery.delivery_address = delivery_data['delivery_address']
            if 'delivery_latitude' in delivery_data:
                delivery.delivery_latitude = delivery_data['delivery_latitude']
            if 'delivery_longitude' in delivery_data:
                delivery.delivery_longitude = delivery_data['delivery_longitude']
            if 'delivery_instructions' in delivery_data:
                delivery.delivery_instructions = delivery_data['delivery_instructions']
            if 'landmark' in delivery_data:
                delivery.landmark = delivery_data['landmark']
            if 'preferred_delivery_time' in delivery_data:
                delivery.preferred_delivery_time = delivery_data['preferred_delivery_time']
            if 'scheduled_delivery_time' in delivery_data:
                delivery.scheduled_delivery_time = delivery_data['scheduled_delivery_time']
            if 'delivery_time_slot' in delivery_data:
                delivery.delivery_time_slot = delivery_data['delivery_time_slot']
            if 'delivery_partner_id' in delivery_data:
                delivery.delivery_partner_id = delivery_data['delivery_partner_id']
            if 'delivery_partner_name' in delivery_data:
                delivery.delivery_partner_name = delivery_data['delivery_partner_name']
            if 'delivery_partner_phone' in delivery_data:
                delivery.delivery_partner_phone = delivery_data['delivery_partner_phone']
            if 'delivery_partner_vehicle' in delivery_data:
                delivery.delivery_partner_vehicle = delivery_data['delivery_partner_vehicle']
            if 'tracking_number' in delivery_data:
                delivery.tracking_number = delivery_data['tracking_number']
            if 'tracking_url' in delivery_data:
                delivery.tracking_url = delivery_data['tracking_url']
            if 'estimated_delivery_time' in delivery_data:
                delivery.estimated_delivery_time = delivery_data['estimated_delivery_time']
            if 'delivery_distance' in delivery_data:
                delivery.delivery_distance = delivery_data['delivery_distance']
            if 'delivery_duration' in delivery_data:
                delivery.delivery_duration = delivery_data['delivery_duration']
            if 'is_ready_for_delivery' in delivery_data:
                delivery.is_ready_for_delivery = delivery_data['is_ready_for_delivery']
            if 'is_out_for_delivery' in delivery_data:
                delivery.is_out_for_delivery = delivery_data['is_out_for_delivery']
            if 'is_delivered' in delivery_data:
                delivery.is_delivered = delivery_data['is_delivered']
                if delivery_data['is_delivered'] and not delivery.actual_delivery_time:
                    delivery.actual_delivery_time = datetime.utcnow()
            if 'delivery_photo_url' in delivery_data:
                delivery.delivery_photo_url = delivery_data['delivery_photo_url']
            if 'delivery_signature' in delivery_data:
                delivery.delivery_signature = delivery_data['delivery_signature']
            if 'recipient_name' in delivery_data:
                delivery.recipient_name = delivery_data['recipient_name']
            if 'recipient_phone' in delivery_data:
                delivery.recipient_phone = delivery_data['recipient_phone']
            if 'packed_by' in delivery_data:
                delivery.packed_by = delivery_data['packed_by']
            if 'dispatched_by' in delivery_data:
                delivery.dispatched_by = delivery_data['dispatched_by']
            if 'notes' in delivery_data:
                delivery.notes = delivery_data['notes']
            if 'delivery_notes' in delivery_data:
                delivery.delivery_notes = delivery_data['delivery_notes']
            
            delivery.updated_at = datetime.utcnow()
            
            db.session.commit()
            return delivery, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def dispatch_delivery(self, delivery_id: int, dispatched_by: int, tenant_id: str, 
                        delivery_partner_id: int) -> Tuple[bool, Optional[str]]:
        """Dispatch home delivery"""
        try:
            delivery = HomeDelivery.query.filter_by(id=delivery_id, tenant_id=tenant_id).first()
            if not delivery:
                return False, "Home delivery record not found"
            
            if not delivery.is_ready_for_delivery:
                return False, "Delivery must be ready for dispatch"
            
            delivery.is_out_for_delivery = True
            delivery.dispatched_by = dispatched_by
            delivery.delivery_partner_id = delivery_partner_id
            delivery.updated_at = datetime.utcnow()
            
            # Update order status
            order = delivery.online_order
            order.status = OnlineOrderStatus.OUT_FOR_DELIVERY
            order.out_for_delivery_at = datetime.utcnow()
            order.delivery_assigned_to = delivery_partner_id
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    def complete_delivery(self, delivery_id: int, tenant_id: str, 
                        delivery_proof: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
        """Complete home delivery"""
        try:
            delivery = HomeDelivery.query.filter_by(id=delivery_id, tenant_id=tenant_id).first()
            if not delivery:
                return False, "Home delivery record not found"
            
            if not delivery.is_out_for_delivery:
                return False, "Delivery must be out for delivery first"
            
            delivery.is_delivered = True
            delivery.actual_delivery_time = datetime.utcnow()
            
            if delivery_proof:
                if 'delivery_photo_url' in delivery_proof:
                    delivery.delivery_photo_url = delivery_proof['delivery_photo_url']
                if 'delivery_signature' in delivery_proof:
                    delivery.delivery_signature = delivery_proof['delivery_signature']
                if 'recipient_name' in delivery_proof:
                    delivery.recipient_name = delivery_proof['recipient_name']
                if 'recipient_phone' in delivery_proof:
                    delivery.recipient_phone = delivery_proof['recipient_phone']
            
            delivery.updated_at = datetime.utcnow()
            
            # Update order status
            order = delivery.online_order
            order.status = OnlineOrderStatus.DELIVERED
            order.delivered_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            db.session.commit()
            return True, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, str(e)
    
    # Delivery Partner Management
    
    def create_delivery_partner(self, partner_data: Dict[str, Any]) -> Tuple[Optional[DeliveryPartner], Optional[str]]:
        """Create a new delivery partner"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('delivery_partners', partner_data.get('tenant_id')):
                return None, "Delivery partners feature is not enabled"
            
            # Check if partner code already exists
            if DeliveryPartner.query.filter_by(partner_code=partner_data.get('partner_code'), 
                                          tenant_id=partner_data.get('tenant_id')).first():
                return None, "Partner code already exists"
            
            # Create partner
            partner = DeliveryPartner(
                tenant_id=partner_data.get('tenant_id'),
                partner_name=partner_data.get('partner_name'),
                partner_code=partner_data.get('partner_code'),
                contact_person=partner_data.get('contact_person'),
                contact_phone=partner_data.get('contact_phone'),
                contact_email=partner_data.get('contact_email'),
                service_areas=partner_data.get('service_areas', []),
                delivery_radius=partner_data.get('delivery_radius'),
                average_delivery_time=partner_data.get('average_delivery_time'),
                base_delivery_fee=partner_data.get('base_delivery_fee', Decimal('0.00')),
                fee_per_km=partner_data.get('fee_per_km', Decimal('0.00')),
                fee_per_minute=partner_data.get('fee_per_minute', Decimal('0.00')),
                minimum_order_value=partner_data.get('minimum_order_value', Decimal('0.00')),
                api_endpoint=partner_data.get('api_endpoint'),
                api_key=partner_data.get('api_key'),
                webhook_url=partner_data.get('webhook_url'),
                integration_type=partner_data.get('integration_type'),
                is_active=partner_data.get('is_active', True),
                is_available=partner_data.get('is_available', True),
                notes=partner_data.get('notes'),
                created_by=partner_data.get('created_by')
            )
            
            db.session.add(partner)
            db.session.commit()
            
            return partner, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_delivery_partner(self, partner_id: int, tenant_id: str) -> Optional[DeliveryPartner]:
        """Get delivery partner by ID"""
        return DeliveryPartner.query.filter_by(id=partner_id, tenant_id=tenant_id).first()
    
    def get_delivery_partners(self, tenant_id: str, active_only: bool = True) -> List[DeliveryPartner]:
        """Get all delivery partners for a tenant"""
        query = DeliveryPartner.query.filter_by(tenant_id=tenant_id)
        
        if active_only:
            query = query.filter_by(is_active=True, is_available=True)
        
        return query.order_by(DeliveryPartner.partner_name).all()
    
    def update_delivery_partner(self, partner_id: int, partner_data: Dict[str, Any]) -> Tuple[Optional[DeliveryPartner], Optional[str]]:
        """Update delivery partner"""
        try:
            partner = DeliveryPartner.query.filter_by(id=partner_id, tenant_id=partner_data.get('tenant_id')).first()
            if not partner:
                return None, "Delivery partner not found"
            
            # Update fields
            if 'partner_name' in partner_data:
                partner.partner_name = partner_data['partner_name']
            if 'contact_person' in partner_data:
                partner.contact_person = partner_data['contact_person']
            if 'contact_phone' in partner_data:
                partner.contact_phone = partner_data['contact_phone']
            if 'contact_email' in partner_data:
                partner.contact_email = partner_data['contact_email']
            if 'service_areas' in partner_data:
                partner.service_areas = partner_data['service_areas']
            if 'delivery_radius' in partner_data:
                partner.delivery_radius = partner_data['delivery_radius']
            if 'average_delivery_time' in partner_data:
                partner.average_delivery_time = partner_data['average_delivery_time']
            if 'base_delivery_fee' in partner_data:
                partner.base_delivery_fee = partner_data['base_delivery_fee']
            if 'fee_per_km' in partner_data:
                partner.fee_per_km = partner_data['fee_per_km']
            if 'fee_per_minute' in partner_data:
                partner.fee_per_minute = partner_data['fee_per_minute']
            if 'minimum_order_value' in partner_data:
                partner.minimum_order_value = partner_data['minimum_order_value']
            if 'api_endpoint' in partner_data:
                partner.api_endpoint = partner_data['api_endpoint']
            if 'api_key' in partner_data:
                partner.api_key = partner_data['api_key']
            if 'webhook_url' in partner_data:
                partner.webhook_url = partner_data['webhook_url']
            if 'integration_type' in partner_data:
                partner.integration_type = partner_data['integration_type']
            if 'is_active' in partner_data:
                partner.is_active = partner_data['is_active']
            if 'is_available' in partner_data:
                partner.is_available = partner_data['is_available']
            if 'notes' in partner_data:
                partner.notes = partner_data['notes']
            
            partner.updated_at = datetime.utcnow()
            partner.updated_by = partner_data.get('updated_by')
            
            db.session.commit()
            return partner, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    # Third-Party Integration Management
    
    def create_third_party_integration(self, integration_data: Dict[str, Any]) -> Tuple[Optional[ThirdPartyIntegration], Optional[str]]:
        """Create a new third-party integration"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('third_party_integration', integration_data.get('tenant_id')):
                return None, "Third-party integration feature is not enabled"
            
            # Check if integration code already exists
            if ThirdPartyIntegration.query.filter_by(integration_code=integration_data.get('integration_code'), 
                                                 tenant_id=integration_data.get('tenant_id')).first():
                return None, "Integration code already exists"
            
            # Create integration
            integration = ThirdPartyIntegration(
                tenant_id=integration_data.get('tenant_id'),
                platform=ThirdPartyPlatform(integration_data.get('platform')),
                integration_name=integration_data.get('integration_name'),
                integration_code=integration_data.get('integration_code'),
                api_endpoint=integration_data.get('api_endpoint'),
                api_key=integration_data.get('api_key'),
                api_secret=integration_data.get('api_secret'),
                webhook_url=integration_data.get('webhook_url'),
                webhook_secret=integration_data.get('webhook_secret'),
                store_mapping=integration_data.get('store_mapping', {}),
                category_mapping=integration_data.get('category_mapping', {}),
                product_mapping=integration_data.get('product_mapping', {}),
                auto_sync_orders=integration_data.get('auto_sync_orders', True),
                auto_sync_menu=integration_data.get('auto_sync_menu', True),
                auto_update_inventory=integration_data.get('auto_update_inventory', True),
                sync_frequency=integration_data.get('sync_frequency', 5),
                auto_accept_orders=integration_data.get('auto_accept_orders', False),
                auto_cancel_time=integration_data.get('auto_cancel_time'),
                preparation_time_buffer=integration_data.get('preparation_time_buffer', 15),
                commission_rate=integration_data.get('commission_rate'),
                fixed_fee=integration_data.get('fixed_fee', Decimal('0.00')),
                payment_gateway_fee=integration_data.get('payment_gateway_fee', Decimal('0.00')),
                is_active=integration_data.get('is_active', True),
                is_connected=integration_data.get('is_connected', False),
                notes=integration_data.get('notes'),
                created_by=integration_data.get('created_by')
            )
            
            db.session.add(integration)
            db.session.commit()
            
            return integration, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_third_party_integration(self, integration_id: int, tenant_id: str) -> Optional[ThirdPartyIntegration]:
        """Get third-party integration by ID"""
        return ThirdPartyIntegration.query.filter_by(id=integration_id, tenant_id=tenant_id).first()
    
    def get_third_party_integrations(self, tenant_id: str, platform: Optional[str] = None, 
                                   active_only: bool = True) -> List[ThirdPartyIntegration]:
        """Get third-party integrations with filters"""
        query = ThirdPartyIntegration.query.filter_by(tenant_id=tenant_id)
        
        if platform:
            query = query.filter_by(platform=ThirdPartyPlatform(platform))
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(ThirdPartyIntegration.integration_name).all()
    
    def update_third_party_integration(self, integration_id: int, integration_data: Dict[str, Any]) -> Tuple[Optional[ThirdPartyIntegration], Optional[str]]:
        """Update third-party integration"""
        try:
            integration = ThirdPartyIntegration.query.filter_by(id=integration_id, tenant_id=integration_data.get('tenant_id')).first()
            if not integration:
                return None, "Integration not found"
            
            # Update fields
            if 'integration_name' in integration_data:
                integration.integration_name = integration_data['integration_name']
            if 'api_endpoint' in integration_data:
                integration.api_endpoint = integration_data['api_endpoint']
            if 'api_key' in integration_data:
                integration.api_key = integration_data['api_key']
            if 'api_secret' in integration_data:
                integration.api_secret = integration_data['api_secret']
            if 'webhook_url' in integration_data:
                integration.webhook_url = integration_data['webhook_url']
            if 'webhook_secret' in integration_data:
                integration.webhook_secret = integration_data['webhook_secret']
            if 'store_mapping' in integration_data:
                integration.store_mapping = integration_data['store_mapping']
            if 'category_mapping' in integration_data:
                integration.category_mapping = integration_data['category_mapping']
            if 'product_mapping' in integration_data:
                integration.product_mapping = integration_data['product_mapping']
            if 'auto_sync_orders' in integration_data:
                integration.auto_sync_orders = integration_data['auto_sync_orders']
            if 'auto_sync_menu' in integration_data:
                integration.auto_sync_menu = integration_data['auto_sync_menu']
            if 'auto_update_inventory' in integration_data:
                integration.auto_update_inventory = integration_data['auto_update_inventory']
            if 'sync_frequency' in integration_data:
                integration.sync_frequency = integration_data['sync_frequency']
            if 'auto_accept_orders' in integration_data:
                integration.auto_accept_orders = integration_data['auto_accept_orders']
            if 'auto_cancel_time' in integration_data:
                integration.auto_cancel_time = integration_data['auto_cancel_time']
            if 'preparation_time_buffer' in integration_data:
                integration.preparation_time_buffer = integration_data['preparation_time_buffer']
            if 'commission_rate' in integration_data:
                integration.commission_rate = integration_data['commission_rate']
            if 'fixed_fee' in integration_data:
                integration.fixed_fee = integration_data['fixed_fee']
            if 'payment_gateway_fee' in integration_data:
                integration.payment_gateway_fee = integration_data['payment_gateway_fee']
            if 'is_active' in integration_data:
                integration.is_active = integration_data['is_active']
            if 'is_connected' in integration_data:
                integration.is_connected = integration_data['is_connected']
            if 'notes' in integration_data:
                integration.notes = integration_data['notes']
            
            integration.updated_at = datetime.utcnow()
            integration.updated_by = integration_data.get('updated_by')
            
            db.session.commit()
            return integration, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    # Online Order Review Management
    
    def create_online_order_review(self, review_data: Dict[str, Any]) -> Tuple[Optional[OnlineOrderReview], Optional[str]]:
        """Create a new online order review"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('order_reviews', review_data.get('tenant_id')):
                return None, "Order reviews feature is not enabled"
            
            # Create review
            review = OnlineOrderReview(
                tenant_id=review_data.get('tenant_id'),
                online_order_id=review_data.get('online_order_id'),
                rating=review_data.get('rating'),
                review_title=review_data.get('review_title'),
                review_text=review_data.get('review_text'),
                food_quality_rating=review_data.get('food_quality_rating'),
                delivery_time_rating=review_data.get('delivery_time_rating'),
                packaging_rating=review_data.get('packaging_rating'),
                customer_service_rating=review_data.get('customer_service_rating'),
                review_source=review_data.get('review_source')
            )
            
            db.session.add(review)
            db.session.commit()
            
            return review, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_online_order_review(self, review_id: int, tenant_id: str) -> Optional[OnlineOrderReview]:
        """Get online order review by ID"""
        return OnlineOrderReview.query.filter_by(id=review_id, tenant_id=tenant_id).first()
    
    def get_online_order_reviews(self, tenant_id: str, approved_only: bool = False, 
                               featured_only: bool = False) -> List[OnlineOrderReview]:
        """Get online order reviews with filters"""
        query = OnlineOrderReview.query.filter_by(tenant_id=tenant_id)
        
        if approved_only:
            query = query.filter_by(is_approved=True)
        if featured_only:
            query = query.filter_by(is_featured=True)
        
        return query.order_by(desc(OnlineOrderReview.created_at)).all()
    
    def update_online_order_review(self, review_id: int, review_data: Dict[str, Any]) -> Tuple[Optional[OnlineOrderReview], Optional[str]]:
        """Update online order review"""
        try:
            review = OnlineOrderReview.query.filter_by(id=review_id, tenant_id=review_data.get('tenant_id')).first()
            if not review:
                return None, "Review not found"
            
            # Update fields
            if 'is_approved' in review_data:
                review.is_approved = review_data['is_approved']
            if 'is_featured' in review_data:
                review.is_featured = review_data['is_featured']
            if 'staff_response' in review_data:
                review.staff_response = review_data['staff_response']
            
            review.updated_at = datetime.utcnow()
            
            db.session.commit()
            return review, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    # Online Order Analytics
    
    def create_online_order_analytics(self, analytics_data: Dict[str, Any]) -> Tuple[Optional[OnlineOrderAnalytics], Optional[str]]:
        """Create online order analytics record"""
        try:
            # Check if feature is enabled
            if not self.feature_service.is_feature_enabled('online_analytics', analytics_data.get('tenant_id')):
                return None, "Online analytics feature is not enabled"
            
            # Extract date components
            analytics_date = analytics_data.get('date', date.today())
            month = analytics_date.month
            quarter = (month - 1) // 3 + 1
            year = analytics_date.year
            
            # Create analytics
            analytics = OnlineOrderAnalytics(
                tenant_id=analytics_data.get('tenant_id'),
                date=analytics_date,
                month=month,
                quarter=quarter,
                year=year,
                total_orders=analytics_data.get('total_orders', 0),
                pending_orders=analytics_data.get('pending_orders', 0),
                confirmed_orders=analytics_data.get('confirmed_orders', 0),
                delivered_orders=analytics_data.get('delivered_orders', 0),
                cancelled_orders=analytics_data.get('cancelled_orders', 0),
                platform_breakdown=analytics_data.get('platform_breakdown', {}),
                delivery_type_breakdown=analytics_data.get('delivery_type_breakdown', {}),
                total_revenue=analytics_data.get('total_revenue', Decimal('0.00')),
                average_order_value=analytics_data.get('average_order_value', Decimal('0.00')),
                delivery_fee_revenue=analytics_data.get('delivery_fee_revenue', Decimal('0.00')),
                platform_fee_total=analytics_data.get('platform_fee_total', Decimal('0.00')),
                average_preparation_time=analytics_data.get('average_preparation_time'),
                average_delivery_time=analytics_data.get('average_delivery_time'),
                average_fulfillment_time=analytics_data.get('average_fulfillment_time'),
                unique_customers=analytics_data.get('unique_customers', 0),
                returning_customers=analytics_data.get('returning_customers', 0),
                customer_satisfaction_score=analytics_data.get('customer_satisfaction_score'),
                metadata=analytics_data.get('metadata', {})
            )
            
            db.session.add(analytics)
            db.session.commit()
            
            return analytics, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, str(e)
    
    def get_online_order_analytics(self, analytics_id: int, tenant_id: str) -> Optional[OnlineOrderAnalytics]:
        """Get online order analytics by ID"""
        return OnlineOrderAnalytics.query.filter_by(id=analytics_id, tenant_id=tenant_id).first()
    
    def get_online_order_analytics_by_date_range(self, tenant_id: str, start_date: date, 
                                              end_date: date) -> List[OnlineOrderAnalytics]:
        """Get online order analytics by date range"""
        return OnlineOrderAnalytics.query.filter(
            OnlineOrderAnalytics.tenant_id == tenant_id,
            OnlineOrderAnalytics.date >= start_date,
            OnlineOrderAnalytics.date <= end_date
        ).order_by(desc(OnlineOrderAnalytics.date)).all()
    
    def generate_online_order_analytics(self, tenant_id: str, analytics_date: date) -> Dict[str, Any]:
        """Generate online order analytics for a specific date"""
        try:
            # Get orders for the date
            orders = OnlineOrder.query.filter(
                OnlineOrder.tenant_id == tenant_id,
                func.date(OnlineOrder.created_at) == analytics_date
            ).all()
            
            # Calculate metrics
            total_orders = len(orders)
            pending_orders = len([o for o in orders if o.status == OnlineOrderStatus.PENDING])
            confirmed_orders = len([o for o in orders if o.status == OnlineOrderStatus.CONFIRMED])
            delivered_orders = len([o for o in orders if o.status == OnlineOrderStatus.DELIVERED])
            cancelled_orders = len([o for o in orders if o.status == OnlineOrderStatus.CANCELLED])
            
            # Platform breakdown
            platform_breakdown = {}
            for order in orders:
                platform = order.platform.value
                platform_breakdown[platform] = platform_breakdown.get(platform, 0) + 1
            
            # Delivery type breakdown
            delivery_type_breakdown = {}
            for order in orders:
                delivery_type = order.delivery_type.value
                delivery_type_breakdown[delivery_type] = delivery_type_breakdown.get(delivery_type, 0) + 1
            
            # Financial metrics
            total_revenue = sum([order.total_amount for order in orders if order.status == OnlineOrderStatus.DELIVERED])
            average_order_value = total_revenue / delivered_orders if delivered_orders > 0 else Decimal('0.00')
            delivery_fee_revenue = sum([order.delivery_fee for order in orders if order.status == OnlineOrderStatus.DELIVERED])
            platform_fee_total = sum([order.platform_fee for order in orders if order.status == OnlineOrderStatus.DELIVERED])
            
            # Time metrics (placeholder calculations)
            average_preparation_time = 15  # Placeholder
            average_delivery_time = 30  # Placeholder
            average_fulfillment_time = average_preparation_time + average_delivery_time
            
            # Customer metrics
            unique_customers = len(set([order.customer_phone for order in orders]))
            returning_customers = 0  # Placeholder
            
            # Customer satisfaction score (placeholder)
            customer_satisfaction_score = Decimal('4.5')  # Placeholder
            
            return {
                'tenant_id': tenant_id,
                'date': analytics_date,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'confirmed_orders': confirmed_orders,
                'delivered_orders': delivered_orders,
                'cancelled_orders': cancelled_orders,
                'platform_breakdown': platform_breakdown,
                'delivery_type_breakdown': delivery_type_breakdown,
                'total_revenue': total_revenue,
                'average_order_value': average_order_value,
                'delivery_fee_revenue': delivery_fee_revenue,
                'platform_fee_total': platform_fee_total,
                'average_preparation_time': average_preparation_time,
                'average_delivery_time': average_delivery_time,
                'average_fulfillment_time': average_fulfillment_time,
                'unique_customers': unique_customers,
                'returning_customers': returning_customers,
                'customer_satisfaction_score': customer_satisfaction_score
            }
        except SQLAlchemyError as e:
            return {'error': str(e)}


# Create service instance
online_integration_service = OnlineIntegrationService()