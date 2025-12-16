"""
Specialized Retail service layer for handling custom attributes, service booking, 
repair and warranty tracking, and rental and consignment management.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload
from models import db
from models.specialized_retail import (
    CustomProduct, CustomAttribute, CustomAttributeValue, ServiceBooking,
    RepairRecord, WarrantyClaim, RentalItem, ConsignmentItem
)
from utils.tenant_query_manager import tenant_scoped


class SpecializedRetailService:
    """Service class for specialized retail operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    # Custom Product Management
    
    def get_custom_products(self, filters: Optional[Dict] = None) -> List[CustomProduct]:
        """Get custom products with optional filters"""
        query = CustomProduct.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'category' in filters:
                query = query.filter(CustomProduct.category == filters['category'])
            if 'specialized_category' in filters:
                query = query.filter(CustomProduct.specialized_category == filters['specialized_category'])
            if 'brand' in filters:
                query = query.filter(CustomProduct.brand == filters['brand'])
            if 'is_active' in filters:
                query = query.filter(CustomProduct.is_active == filters['is_active'])
            if 'is_featured' in filters:
                query = query.filter(CustomProduct.is_featured == filters['is_featured'])
            if 'is_on_sale' in filters:
                query = query.filter(CustomProduct.is_on_sale == filters['is_on_sale'])
            if 'min_price' in filters:
                query = query.filter(CustomProduct.selling_price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(CustomProduct.selling_price <= filters['max_price'])
            if 'low_stock' in filters and filters['low_stock']:
                query = query.filter(CustomProduct.quantity <= CustomProduct.reorder_level)
            if 'search' in filters:
                search_term = f"%{filters['search']}%"
                query = query.filter(or_(
                    CustomProduct.name.ilike(search_term),
                    CustomProduct.description.ilike(search_term),
                    CustomProduct.product_code.ilike(search_term),
                    CustomProduct.sku.ilike(search_term)
                ))
        
        return query.order_by(CustomProduct.name).all()
    
    def get_custom_product_by_id(self, product_id: int) -> Optional[CustomProduct]:
        """Get custom product by ID with all related data"""
        return CustomProduct.query.options(
            joinedload(CustomProduct.custom_attributes_values).joinedload(CustomAttributeValue.attribute),
            joinedload(CustomProduct.service_bookings),
            joinedload(CustomProduct.repair_records),
            joinedload(CustomProduct.warranty_claims),
            joinedload(CustomProduct.rental_items),
            joinedload(CustomProduct.consignment_items)
        ).filter_by(id=product_id, tenant_id=self.tenant_id).first()
    
    def get_custom_product_by_sku(self, sku: str) -> Optional[CustomProduct]:
        """Get custom product by SKU"""
        return CustomProduct.query.filter_by(sku=sku, tenant_id=self.tenant_id).first()
    
    def create_custom_product(self, data: Dict) -> Tuple[bool, Optional[CustomProduct], str]:
        """Create a new custom product"""
        try:
            # Check if product code already exists
            existing = CustomProduct.query.filter_by(
                product_code=data['product_code'], 
                tenant_id=self.tenant_id
            ).first()
            if existing:
                return False, None, f"Product code {data['product_code']} already exists"
            
            # Create product
            product = CustomProduct(
                tenant_id=self.tenant_id,
                product_code=data['product_code'],
                name=data['name'],
                description=data.get('description'),
                category=data.get('category'),
                specialized_category=data.get('specialized_category'),
                brand=data.get('brand'),
                model=data.get('model'),
                sku=data.get('sku'),
                cost_price=Decimal(str(data.get('cost_price', 0))),
                selling_price=Decimal(str(data.get('selling_price', 0))),
                market_price=Decimal(str(data.get('market_price', 0))),
                quantity=data.get('quantity', 0),
                min_quantity=data.get('min_quantity', 0),
                max_quantity=data.get('max_quantity'),
                reorder_level=data.get('reorder_level', 0),
                custom_attributes=data.get('custom_attributes'),
                technical_specifications=data.get('technical_specifications'),
                dimensions=data.get('dimensions'),
                material_specifications=data.get('material_specifications'),
                serial_number_required=data.get('serial_number_required', False),
                warranty_period_months=data.get('warranty_period_months'),
                warranty_terms=data.get('warranty_terms'),
                care_instructions=data.get('care_instructions'),
                usage_instructions=data.get('usage_instructions'),
                safety_warnings=data.get('safety_warnings'),
                service_required=data.get('service_required', False),
                service_interval_months=data.get('service_interval_months'),
                last_service_date=datetime.strptime(data['last_service_date'], '%Y-%m-%d').date() if data.get('last_service_date') else None,
                next_service_date=datetime.strptime(data['next_service_date'], '%Y-%m-%d').date() if data.get('next_service_date') else None,
                is_active=data.get('is_active', True),
                is_featured=data.get('is_featured', False),
                is_new_arrival=data.get('is_new_arrival', False),
                is_on_sale=data.get('is_on_sale', False),
                is_discontinued=data.get('is_discontinued', False),
                created_by=data.get('created_by')
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Process custom attribute values if provided
            if 'attribute_values' in data:
                for attr_data in data['attribute_values']:
                    attribute_value = CustomAttributeValue(
                        tenant_id=self.tenant_id,
                        product_id=product.id,
                        attribute_id=attr_data['attribute_id'],
                        text_value=attr_data.get('text_value'),
                        number_value=Decimal(str(attr_data['number_value'])) if attr_data.get('number_value') else None,
                        date_value=datetime.strptime(attr_data['date_value'], '%Y-%m-%d').date() if attr_data.get('date_value') else None,
                        boolean_value=attr_data.get('boolean_value'),
                        selected_options=attr_data.get('selected_options')
                    )
                    db.session.add(attribute_value)
            
            db.session.commit()
            return True, product, "Custom product created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating custom product: {str(e)}"
    
    def update_custom_product(self, product_id: int, data: Dict) -> Tuple[bool, Optional[CustomProduct], str]:
        """Update an existing custom product"""
        try:
            product = CustomProduct.query.filter_by(id=product_id, tenant_id=self.tenant_id).first()
            if not product:
                return False, None, "Product not found"
            
            # Update fields
            for field, value in data.items():
                if field == 'attribute_values':
                    continue  # Handle separately
                elif hasattr(product, field) and field not in ['id', 'tenant_id', 'created_at', 'created_by']:
                    if field in ['cost_price', 'selling_price', 'market_price'] and value is not None:
                        setattr(product, field, Decimal(str(value)))
                    elif field in ['last_service_date', 'next_service_date'] and value:
                        setattr(product, field, datetime.strptime(value, '%Y-%m-%d').date())
                    else:
                        setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            
            # Update custom attribute values if provided
            if 'attribute_values' in data:
                # Remove existing attribute values
                CustomAttributeValue.query.filter_by(product_id=product_id).delete()
                
                # Add new attribute values
                for attr_data in data['attribute_values']:
                    attribute_value = CustomAttributeValue(
                        tenant_id=self.tenant_id,
                        product_id=product_id,
                        attribute_id=attr_data['attribute_id'],
                        text_value=attr_data.get('text_value'),
                        number_value=Decimal(str(attr_data['number_value'])) if attr_data.get('number_value') else None,
                        date_value=datetime.strptime(attr_data['date_value'], '%Y-%m-%d').date() if attr_data.get('date_value') else None,
                        boolean_value=attr_data.get('boolean_value'),
                        selected_options=attr_data.get('selected_options')
                    )
                    db.session.add(attribute_value)
            
            db.session.commit()
            return True, product, "Custom product updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error updating custom product: {str(e)}"
    
    def delete_custom_product(self, product_id: int) -> Tuple[bool, str]:
        """Delete a custom product"""
        try:
            product = CustomProduct.query.filter_by(id=product_id, tenant_id=self.tenant_id).first()
            if not product:
                return False, "Product not found"
            
            # Check if product has any active rentals or consignments
            active_rentals = RentalItem.query.filter_by(
                product_id=product_id, 
                tenant_id=self.tenant_id,
                status='active'
            ).count()
            
            active_consignments = ConsignmentItem.query.filter_by(
                product_id=product_id,
                tenant_id=self.tenant_id,
                status='on_display'
            ).count()
            
            if active_rentals > 0 or active_consignments > 0:
                return False, "Cannot delete product with active rentals or consignments"
            
            db.session.delete(product)
            db.session.commit()
            return True, "Custom product deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting custom product: {str(e)}"
    
    # Custom Attribute Management
    
    def get_custom_attributes(self, filters: Optional[Dict] = None) -> List[CustomAttribute]:
        """Get custom attributes with optional filters"""
        query = CustomAttribute.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'category' in filters:
                query = query.filter(CustomAttribute.category == filters['category'])
            if 'attribute_type' in filters:
                query = query.filter(CustomAttribute.attribute_type == filters['attribute_type'])
            if 'is_active' in filters:
                query = query.filter(CustomAttribute.is_active == filters['is_active'])
            if 'show_in_filters' in filters:
                query = query.filter(CustomAttribute.show_in_filters == filters['show_in_filters'])
        
        return query.order_by(CustomAttribute.display_order, CustomAttribute.display_name).all()
    
    def get_custom_attribute_by_id(self, attribute_id: int) -> Optional[CustomAttribute]:
        """Get custom attribute by ID"""
        return CustomAttribute.query.filter_by(id=attribute_id, tenant_id=self.tenant_id).first()
    
    def create_custom_attribute(self, data: Dict) -> Tuple[bool, Optional[CustomAttribute], str]:
        """Create a new custom attribute"""
        try:
            # Check if attribute name already exists
            existing = CustomAttribute.query.filter_by(
                attribute_name=data['attribute_name'], 
                tenant_id=self.tenant_id
            ).first()
            if existing:
                return False, None, f"Attribute name {data['attribute_name']} already exists"
            
            attribute = CustomAttribute(
                tenant_id=self.tenant_id,
                attribute_name=data['attribute_name'],
                display_name=data['display_name'],
                attribute_type=data['attribute_type'],
                data_type=data.get('data_type'),
                description=data.get('description'),
                is_required=data.get('is_required', False),
                is_unique=data.get('is_unique', False),
                min_value=Decimal(str(data['min_value'])) if data.get('min_value') else None,
                max_value=Decimal(str(data['max_value'])) if data.get('max_value') else None,
                min_length=data.get('min_length'),
                max_length=data.get('max_length'),
                default_value=data.get('default_value'),
                options=data.get('options'),
                category=data.get('category'),
                applies_to_categories=data.get('applies_to_categories'),
                applies_to_brands=data.get('applies_to_brands'),
                display_order=data.get('display_order', 0),
                show_in_list=data.get('show_in_list', True),
                show_in_detail=data.get('show_in_detail', True),
                show_in_filters=data.get('show_in_filters', False),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(attribute)
            db.session.commit()
            return True, attribute, "Custom attribute created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating custom attribute: {str(e)}"
    
    def update_custom_attribute(self, attribute_id: int, data: Dict) -> Tuple[bool, Optional[CustomAttribute], str]:
        """Update an existing custom attribute"""
        try:
            attribute = CustomAttribute.query.filter_by(id=attribute_id, tenant_id=self.tenant_id).first()
            if not attribute:
                return False, None, "Attribute not found"
            
            # Update fields
            for field, value in data.items():
                if hasattr(attribute, field) and field not in ['id', 'tenant_id', 'created_at']:
                    if field in ['min_value', 'max_value'] and value is not None:
                        setattr(attribute, field, Decimal(str(value)))
                    else:
                        setattr(attribute, field, value)
            
            attribute.updated_at = datetime.utcnow()
            db.session.commit()
            return True, attribute, "Custom attribute updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error updating custom attribute: {str(e)}"
    
    # Service Booking Management
    
    def get_service_bookings(self, filters: Optional[Dict] = None) -> List[ServiceBooking]:
        """Get service bookings with optional filters"""
        query = ServiceBooking.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'product_id' in filters:
                query = query.filter(ServiceBooking.product_id == filters['product_id'])
            if 'customer_id' in filters:
                query = query.filter(ServiceBooking.customer_id == filters['customer_id'])
            if 'service_type' in filters:
                query = query.filter(ServiceBooking.service_type == filters['service_type'])
            if 'status' in filters:
                query = query.filter(ServiceBooking.status == filters['status'])
            if 'technician_id' in filters:
                query = query.filter(ServiceBooking.technician_id == filters['technician_id'])
            if 'service_location' in filters:
                query = query.filter(ServiceBooking.service_location == filters['service_location'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(ServiceBooking.scheduled_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(ServiceBooking.scheduled_date <= end_date)
            if 'overdue' in filters and filters['overdue']:
                query = query.filter(
                    and_(
                        ServiceBooking.scheduled_date < date.today(),
                        ServiceBooking.status == 'scheduled'
                    )
                )
        
        return query.order_by(desc(ServiceBooking.scheduled_date)).all()
    
    def get_service_booking_by_id(self, booking_id: int) -> Optional[ServiceBooking]:
        """Get service booking by ID with all related data"""
        return ServiceBooking.query.options(
            joinedload(ServiceBooking.product),
            joinedload(ServiceBooking.customer),
            joinedload(ServiceBooking.technician),
            joinedload(ServiceBooking.invoice)
        ).filter_by(id=booking_id, tenant_id=self.tenant_id).first()
    
    def create_service_booking(self, data: Dict) -> Tuple[bool, Optional[ServiceBooking], str]:
        """Create a new service booking"""
        try:
            # Generate booking number
            booking_number = self._generate_booking_number()
            
            booking = ServiceBooking(
                tenant_id=self.tenant_id,
                booking_number=booking_number,
                product_id=data.get('product_id'),
                customer_id=data.get('customer_id'),
                service_type=data['service_type'],
                service_description=data.get('service_description'),
                priority=data.get('priority', 'normal'),
                preferred_date=datetime.strptime(data['preferred_date'], '%Y-%m-%d').date() if data.get('preferred_date') else None,
                preferred_time=data.get('preferred_time'),
                scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date() if data.get('scheduled_date') else None,
                scheduled_time=data.get('scheduled_time'),
                duration_hours=Decimal(str(data['duration_hours'])) if data.get('duration_hours') else None,
                service_location=data.get('service_location'),
                service_address=data.get('service_address'),
                contact_person=data.get('contact_person'),
                contact_phone=data.get('contact_phone'),
                technician_id=data.get('technician_id'),
                technician_notes=data.get('technician_notes'),
                status=data.get('status', 'scheduled'),
                estimated_cost=Decimal(str(data['estimated_cost'])) if data.get('estimated_cost') else None,
                actual_cost=Decimal(str(data['actual_cost'])) if data.get('actual_cost') else None,
                labor_cost=Decimal(str(data['labor_cost'])) if data.get('labor_cost') else None,
                parts_cost=Decimal(str(data['parts_cost'])) if data.get('parts_cost') else None,
                is_billable=data.get('is_billable', True),
                invoice_id=data.get('invoice_id'),
                created_by=data.get('created_by')
            )
            
            db.session.add(booking)
            db.session.commit()
            return True, booking, "Service booking created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating service booking: {str(e)}"
    
    def update_service_booking(self, booking_id: int, data: Dict) -> Tuple[bool, Optional[ServiceBooking], str]:
        """Update an existing service booking"""
        try:
            booking = ServiceBooking.query.filter_by(id=booking_id, tenant_id=self.tenant_id).first()
            if not booking:
                return False, None, "Service booking not found"
            
            # Update fields
            for field, value in data.items():
                if hasattr(booking, field) and field not in ['id', 'tenant_id', 'booking_number', 'created_at', 'created_by']:
                    if field in ['preferred_date', 'scheduled_date'] and value:
                        setattr(booking, field, datetime.strptime(value, '%Y-%m-%d').date())
                    elif field in ['duration_hours', 'estimated_cost', 'actual_cost', 'labor_cost', 'parts_cost'] and value is not None:
                        setattr(booking, field, Decimal(str(value)))
                    elif field == 'completion_date' and value:
                        setattr(booking, field, datetime.strptime(value, '%Y-%m-%d %H:%M:%S'))
                    else:
                        setattr(booking, field, value)
            
            booking.updated_at = datetime.utcnow()
            db.session.commit()
            return True, booking, "Service booking updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error updating service booking: {str(e)}"
    
    # Repair Record Management
    
    def get_repair_records(self, filters: Optional[Dict] = None) -> List[RepairRecord]:
        """Get repair records with optional filters"""
        query = RepairRecord.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'product_id' in filters:
                query = query.filter(RepairRecord.product_id == filters['product_id'])
            if 'customer_id' in filters:
                query = query.filter(RepairRecord.customer_id == filters['customer_id'])
            if 'repair_type' in filters:
                query = query.filter(RepairRecord.repair_type == filters['repair_type'])
            if 'status' in filters:
                query = query.filter(RepairRecord.status == filters['status'])
            if 'technician_id' in filters:
                query = query.filter(RepairRecord.technician_id == filters['technician_id'])
            if 'is_warranty_repair' in filters:
                query = query.filter(RepairRecord.is_warranty_repair == filters['is_warranty_repair'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(RepairRecord.received_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                query = query.filter(RepairRecord.received_date <= end_date)
            if 'overdue' in filters and filters['overdue']:
                query = query.filter(
                    and_(
                        RepairRecord.estimated_completion_date < datetime.utcnow(),
                        RepairRecord.status.in_(['pending', 'in_progress'])
                    )
                )
        
        return query.order_by(desc(RepairRecord.received_date)).all()
    
    def get_repair_record_by_id(self, repair_id: int) -> Optional[RepairRecord]:
        """Get repair record by ID with all related data"""
        return RepairRecord.query.options(
            joinedload(RepairRecord.product),
            joinedload(RepairRecord.customer),
            joinedload(RepairRecord.technician),
            joinedload(RepairRecord.quality_checker),
            joinedload(RepairRecord.warranty_claim),
            joinedload(RepairRecord.invoice)
        ).filter_by(id=repair_id, tenant_id=self.tenant_id).first()
    
    def create_repair_record(self, data: Dict) -> Tuple[bool, Optional[RepairRecord], str]:
        """Create a new repair record"""
        try:
            # Generate repair number
            repair_number = self._generate_repair_number()
            
            repair = RepairRecord(
                tenant_id=self.tenant_id,
                repair_number=repair_number,
                product_id=data.get('product_id'),
                customer_id=data.get('customer_id'),
                repair_type=data['repair_type'],
                problem_description=data.get('problem_description'),
                diagnosis=data.get('diagnosis'),
                repair_actions=data.get('repair_actions'),
                parts_replaced=data.get('parts_replaced'),
                status=data.get('status', 'pending'),
                priority=data.get('priority', 'normal'),
                technician_id=data.get('technician_id'),
                technician_notes=data.get('technician_notes'),
                estimated_completion_date=datetime.strptime(data['estimated_completion_date'], '%Y-%m-%d %H:%M:%S') if data.get('estimated_completion_date') else None,
                diagnostic_fee=Decimal(str(data['diagnostic_fee'])) if data.get('diagnostic_fee') else None,
                labor_cost=Decimal(str(data['labor_cost'])) if data.get('labor_cost') else None,
                parts_cost=Decimal(str(data['parts_cost'])) if data.get('parts_cost') else None,
                total_cost=Decimal(str(data['total_cost'])) if data.get('total_cost') else None,
                is_warranty_repair=data.get('is_warranty_repair', False),
                warranty_claim_id=data.get('warranty_claim_id'),
                invoice_id=data.get('invoice_id'),
                customer_notified=data.get('customer_notified', False),
                customer_approval=data.get('customer_approval'),
                customer_notes=data.get('customer_notes'),
                quality_check_passed=data.get('quality_check_passed'),
                quality_check_notes=data.get('quality_check_notes'),
                quality_check_by=data.get('quality_check_by'),
                created_by=data.get('created_by')
            )
            
            db.session.add(repair)
            db.session.commit()
            return True, repair, "Repair record created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating repair record: {str(e)}"
    
    # Warranty Claim Management
    
    def get_warranty_claims(self, filters: Optional[Dict] = None) -> List[WarrantyClaim]:
        """Get warranty claims with optional filters"""
        query = WarrantyClaim.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'product_id' in filters:
                query = query.filter(WarrantyClaim.product_id == filters['product_id'])
            if 'customer_id' in filters:
                query = query.filter(WarrantyClaim.customer_id == filters['customer_id'])
            if 'claim_type' in filters:
                query = query.filter(WarrantyClaim.claim_type == filters['claim_type'])
            if 'claim_status' in filters:
                query = query.filter(WarrantyClaim.claim_status == filters['claim_status'])
            if 'warranty_valid' in filters:
                query = query.filter(WarrantyClaim.warranty_valid == filters['warranty_valid'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(WarrantyClaim.claim_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(WarrantyClaim.claim_date <= end_date)
        
        return query.order_by(desc(WarrantyClaim.submission_date)).all()
    
    def get_warranty_claim_by_id(self, claim_id: int) -> Optional[WarrantyClaim]:
        """Get warranty claim by ID with all related data"""
        return WarrantyClaim.query.options(
            joinedload(WarrantyClaim.product),
            joinedload(WarrantyClaim.replacement_product),
            joinedload(WarrantyClaim.customer),
            joinedload(WarrantyClaim.assessor),
            joinedload(WarrantyClaim.decision_maker),
            joinedload(WarrantyClaim.repair_records)
        ).filter_by(id=claim_id, tenant_id=self.tenant_id).first()
    
    def create_warranty_claim(self, data: Dict) -> Tuple[bool, Optional[WarrantyClaim], str]:
        """Create a new warranty claim"""
        try:
            # Generate claim number
            claim_number = self._generate_claim_number()
            
            claim = WarrantyClaim(
                tenant_id=self.tenant_id,
                claim_number=claim_number,
                product_id=data.get('product_id'),
                customer_id=data.get('customer_id'),
                purchase_date=datetime.strptime(data['purchase_date'], '%Y-%m-%d').date() if data.get('purchase_date') else None,
                purchase_invoice=data.get('purchase_invoice'),
                serial_number=data.get('serial_number'),
                claim_type=data['claim_type'],
                issue_description=data.get('issue_description'),
                claim_date=datetime.strptime(data['claim_date'], '%Y-%m-%d').date() if data.get('claim_date') else date.today(),
                warranty_valid=data.get('warranty_valid'),
                warranty_expiry_date=datetime.strptime(data['warranty_expiry_date'], '%Y-%m-%d').date() if data.get('warranty_expiry_date') else None,
                warranty_terms_violated=data.get('warranty_terms_violated', False),
                violation_reason=data.get('violation_reason'),
                assessment_notes=data.get('assessment_notes'),
                assessment_by=data.get('assessment_by'),
                assessment_date=datetime.strptime(data['assessment_date'], '%Y-%m-%d %H:%M:%S') if data.get('assessment_date') else None,
                claim_status=data.get('claim_status', 'pending'),
                decision_date=datetime.strptime(data['decision_date'], '%Y-%m-%d').date() if data.get('decision_date') else None,
                decision_by=data.get('decision_by'),
                decision_notes=data.get('decision_notes'),
                resolution_type=data.get('resolution_type'),
                resolution_details=data.get('resolution_details'),
                replacement_product_id=data.get('replacement_product_id'),
                refund_amount=Decimal(str(data['refund_amount'])) if data.get('refund_amount') else None,
                repair_cost=Decimal(str(data['repair_cost'])) if data.get('repair_cost') else None,
                customer_notified=data.get('customer_notified', False),
                customer_response=data.get('customer_response'),
                customer_satisfaction=data.get('customer_satisfaction'),
                processing_start_date=datetime.strptime(data['processing_start_date'], '%Y-%m-%d %H:%M:%S') if data.get('processing_start_date') else None,
                completion_date=datetime.strptime(data['completion_date'], '%Y-%m-%d %H:%M:%S') if data.get('completion_date') else None,
                created_by=data.get('created_by')
            )
            
            db.session.add(claim)
            db.session.commit()
            return True, claim, "Warranty claim created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating warranty claim: {str(e)}"
    
    # Rental Item Management
    
    def get_rental_items(self, filters: Optional[Dict] = None) -> List[RentalItem]:
        """Get rental items with optional filters"""
        query = RentalItem.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'product_id' in filters:
                query = query.filter(RentalItem.product_id == filters['product_id'])
            if 'customer_id' in filters:
                query = query.filter(RentalItem.customer_id == filters['customer_id'])
            if 'status' in filters:
                query = query.filter(RentalItem.status == filters['status'])
            if 'payment_status' in filters:
                query = query.filter(RentalItem.payment_status == filters['payment_status'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(RentalItem.rental_start_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(RentalItem.rental_end_date <= end_date)
            if 'overdue' in filters and filters['overdue']:
                query = query.filter(
                    and_(
                        RentalItem.rental_end_date < date.today(),
                        RentalItem.status == 'active'
                    )
                )
        
        return query.order_by(desc(RentalItem.rental_start_date)).all()
    
    def get_rental_item_by_id(self, rental_id: int) -> Optional[RentalItem]:
        """Get rental item by ID with all related data"""
        return RentalItem.query.options(
            joinedload(RentalItem.product),
            joinedload(RentalItem.customer),
            joinedload(RentalItem.creator)
        ).filter_by(id=rental_id, tenant_id=self.tenant_id).first()
    
    def create_rental_item(self, data: Dict) -> Tuple[bool, Optional[RentalItem], str]:
        """Create a new rental item"""
        try:
            # Generate rental number
            rental_number = self._generate_rental_number()
            
            rental = RentalItem(
                tenant_id=self.tenant_id,
                rental_number=rental_number,
                product_id=data.get('product_id'),
                customer_id=data.get('customer_id'),
                rental_start_date=datetime.strptime(data['rental_start_date'], '%Y-%m-%d').date(),
                rental_end_date=datetime.strptime(data['rental_end_date'], '%Y-%m-%d').date(),
                daily_rate=Decimal(str(data['daily_rate'])) if data.get('daily_rate') else None,
                weekly_rate=Decimal(str(data['weekly_rate'])) if data.get('weekly_rate') else None,
                monthly_rate=Decimal(str(data['monthly_rate'])) if data.get('monthly_rate') else None,
                deposit_amount=Decimal(str(data['deposit_amount'])) if data.get('deposit_amount') else None,
                total_rental_cost=Decimal(str(data['total_rental_cost'])) if data.get('total_rental_cost') else None,
                insurance_required=data.get('insurance_required', False),
                insurance_cost=Decimal(str(data['insurance_cost'])) if data.get('insurance_cost') else None,
                damage_waiver=data.get('damage_waiver', False),
                liability_limit=Decimal(str(data['liability_limit'])) if data.get('liability_limit') else None,
                serial_number=data.get('serial_number'),
                condition_on_rental=data.get('condition_on_rental'),
                condition_on_return=data.get('condition_on_return'),
                damage_notes=data.get('damage_notes'),
                damage_charges=Decimal(str(data['damage_charges'])) if data.get('damage_charges') else None,
                status=data.get('status', 'reserved'),
                payment_status=data.get('payment_status', 'pending'),
                extension_allowed=data.get('extension_allowed', True),
                extension_rate=Decimal(str(data['extension_rate'])) if data.get('extension_rate') else None,
                current_extension_end_date=datetime.strptime(data['current_extension_end_date'], '%Y-%m-%d').date() if data.get('current_extension_end_date') else None,
                late_fee_per_day=Decimal(str(data['late_fee_per_day'])) if data.get('late_fee_per_day') else None,
                grace_period_days=data.get('grace_period_days', 0),
                created_by=data.get('created_by')
            )
            
            db.session.add(rental)
            db.session.commit()
            return True, rental, "Rental item created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating rental item: {str(e)}"
    
    # Consignment Item Management
    
    def get_consignment_items(self, filters: Optional[Dict] = None) -> List[ConsignmentItem]:
        """Get consignment items with optional filters"""
        query = ConsignmentItem.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'product_id' in filters:
                query = query.filter(ConsignmentItem.product_id == filters['product_id'])
            if 'consignor_id' in filters:
                query = query.filter(ConsignmentItem.consignor_id == filters['consignor_id'])
            if 'status' in filters:
                query = query.filter(ConsignmentItem.status == filters['status'])
            if 'payment_status' in filters:
                query = query.filter(ConsignmentItem.payment_status == filters['payment_status'])
            if 'item_condition' in filters:
                query = query.filter(ConsignmentItem.item_condition == filters['item_condition'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(ConsignmentItem.consignment_start_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(ConsignmentItem.consignment_start_date <= end_date)
            if 'expired' in filters and filters['expired']:
                query = query.filter(
                    and_(
                        ConsignmentItem.consignment_end_date < date.today(),
                        ConsignmentItem.status != 'sold'
                    )
                )
        
        return query.order_by(desc(ConsignmentItem.consignment_start_date)).all()
    
    def get_consignment_item_by_id(self, consignment_id: int) -> Optional[ConsignmentItem]:
        """Get consignment item by ID with all related data"""
        return ConsignmentItem.query.options(
            joinedload(ConsignmentItem.product),
            joinedload(ConsignmentItem.consignor),
            joinedload(ConsignmentItem.creator)
        ).filter_by(id=consignment_id, tenant_id=self.tenant_id).first()
    
    def create_consignment_item(self, data: Dict) -> Tuple[bool, Optional[ConsignmentItem], str]:
        """Create a new consignment item"""
        try:
            # Generate consignment number
            consignment_number = self._generate_consignment_number()
            
            consignment = ConsignmentItem(
                tenant_id=self.tenant_id,
                consignment_number=consignment_number,
                product_id=data.get('product_id'),
                consignor_id=data.get('consignor_id'),
                consignment_start_date=datetime.strptime(data['consignment_start_date'], '%Y-%m-%d').date(),
                consignment_end_date=datetime.strptime(data['consignment_end_date'], '%Y-%m-%d').date() if data.get('consignment_end_date') else None,
                actual_sale_date=datetime.strptime(data['actual_sale_date'], '%Y-%m-%d').date() if data.get('actual_sale_date') else None,
                asking_price=Decimal(str(data['asking_price'])) if data.get('asking_price') else None,
                minimum_acceptable_price=Decimal(str(data['minimum_acceptable_price'])) if data.get('minimum_acceptable_price') else None,
                actual_sale_price=Decimal(str(data['actual_sale_price'])) if data.get('actual_sale_price') else None,
                commission_rate=Decimal(str(data['commission_rate'])) if data.get('commission_rate') else None,
                commission_amount=Decimal(str(data['commission_amount'])) if data.get('commission_amount') else None,
                flat_fee=Decimal(str(data['flat_fee'])) if data.get('flat_fee') else None,
                commission_type=data.get('commission_type', 'percentage'),
                payment_status=data.get('payment_status', 'pending'),
                payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d').date() if data.get('payment_date') else None,
                payment_amount=Decimal(str(data['payment_amount'])) if data.get('payment_amount') else None,
                payment_method=data.get('payment_method'),
                payment_reference=data.get('payment_reference'),
                item_condition=data.get('item_condition'),
                condition_notes=data.get('condition_notes'),
                authenticity_verified=data.get('authenticity_verified', False),
                appraisal_value=Decimal(str(data['appraisal_value'])) if data.get('appraisal_value') else None,
                appraisal_date=datetime.strptime(data['appraisal_date'], '%Y-%m-%d').date() if data.get('appraisal_date') else None,
                appraiser_notes=data.get('appraiser_notes'),
                display_location=data.get('display_location'),
                featured_item=data.get('featured_item', False),
                marketing_notes=data.get('marketing_notes'),
                photo_urls=data.get('photo_urls'),
                status=data.get('status', 'received'),
                contract_terms=data.get('contract_terms'),
                auto_price_reduction=data.get('auto_price_reduction', False),
                price_reduction_schedule=data.get('price_reduction_schedule'),
                return_unsold_items=data.get('return_unsold_items', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(consignment)
            db.session.commit()
            return True, consignment, "Consignment item created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating consignment item: {str(e)}"
    
    # Analytics and Reporting
    
    def get_specialized_retail_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """Get analytics for specialized retail operations"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Service booking analytics
            service_bookings = ServiceBooking.query.filter(
                ServiceBooking.tenant_id == self.tenant_id,
                ServiceBooking.scheduled_date >= start_date,
                ServiceBooking.scheduled_date <= end_date
            ).all()
            
            service_analytics = {
                'total_bookings': len(service_bookings),
                'completed_bookings': len([b for b in service_bookings if b.status == 'completed']),
                'pending_bookings': len([b for b in service_bookings if b.status == 'scheduled']),
                'overdue_bookings': len([b for b in service_bookings if b.is_overdue]),
                'total_revenue': sum(float(b.actual_cost or 0) for b in service_bookings if b.actual_cost),
                'average_booking_value': 0
            }
            
            if service_analytics['completed_bookings'] > 0:
                service_analytics['average_booking_value'] = service_analytics['total_revenue'] / service_analytics['completed_bookings']
            
            # Repair record analytics
            repair_records = RepairRecord.query.filter(
                RepairRecord.tenant_id == self.tenant_id,
                RepairRecord.received_date >= start_date,
                RepairRecord.received_date <= end_date
            ).all()
            
            repair_analytics = {
                'total_repairs': len(repair_records),
                'completed_repairs': len([r for r in repair_records if r.status == 'completed']),
                'warranty_repairs': len([r for r in repair_records if r.is_warranty_repair]),
                'paid_repairs': len([r for r in repair_records if not r.is_warranty_repair]),
                'total_repair_cost': sum(float(r.total_cost or 0) for r in repair_records if r.total_cost),
                'average_repair_cost': 0
            }
            
            if repair_analytics['completed_repairs'] > 0:
                repair_analytics['average_repair_cost'] = repair_analytics['total_repair_cost'] / repair_analytics['completed_repairs']
            
            # Warranty claim analytics
            warranty_claims = WarrantyClaim.query.filter(
                WarrantyClaim.tenant_id == self.tenant_id,
                WarrantyClaim.claim_date >= start_date,
                WarrantyClaim.claim_date <= end_date
            ).all()
            
            warranty_analytics = {
                'total_claims': len(warranty_claims),
                'approved_claims': len([c for c in warranty_claims if c.claim_status == 'approved']),
                'rejected_claims': len([c for c in warranty_claims if c.claim_status == 'rejected']),
                'pending_claims': len([c for c in warranty_claims if c.claim_status == 'pending']),
                'total_claim_value': sum(float(c.refund_amount or 0) + float(c.repair_cost or 0) for c in warranty_claims),
                'average_processing_days': 0
            }
            
            completed_claims = [c for c in warranty_claims if c.completion_date]
            if completed_claims:
                total_days = sum(c.processing_days for c in completed_claims)
                warranty_analytics['average_processing_days'] = total_days / len(completed_claims)
            
            # Rental item analytics
            rental_items = RentalItem.query.filter(
                RentalItem.tenant_id == self.tenant_id,
                RentalItem.rental_start_date >= start_date,
                RentalItem.rental_start_date <= end_date
            ).all()
            
            rental_analytics = {
                'total_rentals': len(rental_items),
                'active_rentals': len([r for r in rental_items if r.status == 'active']),
                'overdue_rentals': len([r for r in rental_items if r.is_overdue]),
                'total_rental_revenue': sum(float(r.total_rental_cost or 0) for r in rental_items if r.total_rental_cost),
                'total_deposit_amount': sum(float(r.deposit_amount or 0) for r in rental_items if r.deposit_amount),
                'total_late_fees': sum(float(r.late_fees) for r in rental_items if r.late_fees > 0),
                'average_rental_duration': 0
            }
            
            if rental_analytics['total_rentals'] > 0:
                total_days = sum(r.rental_days for r in rental_items)
                rental_analytics['average_rental_duration'] = total_days / rental_analytics['total_rentals']
            
            # Consignment item analytics
            consignment_items = ConsignmentItem.query.filter(
                ConsignmentItem.tenant_id == self.tenant_id,
                ConsignmentItem.consignment_start_date >= start_date,
                ConsignmentItem.consignment_start_date <= end_date
            ).all()
            
            consignment_analytics = {
                'total_consignments': len(consignment_items),
                'sold_items': len([c for c in consignment_items if c.status == 'sold']),
                'active_consignments': len([c for c in consignment_items if c.status == 'on_display']),
                'expired_consignments': len([c for c in consignment_items if c.is_expired]),
                'total_sales_value': sum(float(c.actual_sale_price or 0) for c in consignment_items if c.actual_sale_price),
                'total_commission_earned': sum(c.calculate_commission for c in consignment_items if c.actual_sale_price),
                'total_consignor_payouts': sum(float(c.payment_amount or 0) for c in consignment_items if c.payment_amount),
                'average_days_to_sell': 0
            }
            
            sold_items = [c for c in consignment_items if c.status == 'sold' and c.actual_sale_date]
            if sold_items:
                total_days = sum(c.days_on_consignment for c in sold_items)
                consignment_analytics['average_days_to_sell'] = total_days / len(sold_items)
            
            return {
                'service_analytics': service_analytics,
                'repair_analytics': repair_analytics,
                'warranty_analytics': warranty_analytics,
                'rental_analytics': rental_analytics,
                'consignment_analytics': consignment_analytics,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {
                'error': f"Error generating specialized retail analytics: {str(e)}",
                'service_analytics': {},
                'repair_analytics': {},
                'warranty_analytics': {},
                'rental_analytics': {},
                'consignment_analytics': {}
            }
    
    # Helper Methods
    
    def _generate_booking_number(self) -> str:
        """Generate a unique booking number"""
        prefix = "BK"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get the count of bookings for today
        today_count = ServiceBooking.query.filter(
            ServiceBooking.tenant_id == self.tenant_id,
            ServiceBooking.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"
    
    def _generate_repair_number(self) -> str:
        """Generate a unique repair number"""
        prefix = "RP"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get the count of repairs for today
        today_count = RepairRecord.query.filter(
            RepairRecord.tenant_id == self.tenant_id,
            RepairRecord.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"
    
    def _generate_claim_number(self) -> str:
        """Generate a unique claim number"""
        prefix = "WC"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get the count of claims for today
        today_count = WarrantyClaim.query.filter(
            WarrantyClaim.tenant_id == self.tenant_id,
            WarrantyClaim.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"
    
    def _generate_rental_number(self) -> str:
        """Generate a unique rental number"""
        prefix = "RT"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get the count of rentals for today
        today_count = RentalItem.query.filter(
            RentalItem.tenant_id == self.tenant_id,
            RentalItem.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"
    
    def _generate_consignment_number(self) -> str:
        """Generate a unique consignment number"""
        prefix = "CS"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get the count of consignments for today
        today_count = ConsignmentItem.query.filter(
            ConsignmentItem.tenant_id == self.tenant_id,
            ConsignmentItem.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"


# Factory function to create service instances
def create_specialized_retail_service(tenant_id: str) -> SpecializedRetailService:
    """Factory function to create a specialized retail service instance"""
    return SpecializedRetailService(tenant_id)