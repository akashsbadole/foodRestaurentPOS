"""
Supermarket & Groceries service layer with comprehensive business logic
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from decimal import Decimal
from models import db
from models.supermarket_groceries import (
    FreshProduce, FreshProduceInventory, FreshProducePriceUpdate, FreshProduceQualityCheck,
    WeighingScaleIntegration, ComboOffer, ShelfLifeManagement, FreshCounter
)
from utils.feature_flag_manager import feature_manager


class SupermarketGroceriesService:
    """Service layer for supermarket and groceries operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a supermarket feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Fresh Produce Management Methods
    
    def create_fresh_produce(self, produce_data: Dict[str, Any], 
                           user_id: Optional[str] = None) -> Tuple[bool, Optional[FreshProduce], str]:
        """Create a new fresh produce item"""
        try:
            produce = FreshProduce(
                product_id=produce_data['product_id'],
                sku_base=produce_data['sku_base'],
                name=produce_data['name'],
                description=produce_data.get('description'),
                produce_category=produce_data.get('produce_category'),
                variety=produce_data.get('variety'),
                origin=produce_data.get('origin'),
                grade=produce_data.get('grade'),
                certification=produce_data.get('certification'),
                unit_price=Decimal(str(produce_data['unit_price'])),
                cost_price=Decimal(str(produce_data.get('cost_price', 0))),
                price_per_kg=Decimal(str(produce_data.get('price_per_kg', 0))),
                average_weight_per_unit=produce_data.get('average_weight_per_unit'),
                weight_variance=produce_data.get('weight_variance'),
                size_category=produce_data.get('size_category'),
                shelf_life_days=produce_data.get('shelf_life_days'),
                optimal_storage_temp=produce_data.get('optimal_storage_temp'),
                optimal_humidity=produce_data.get('optimal_humidity'),
                ripeness_indicators=produce_data.get('ripeness_indicators', {}),
                is_seasonal=produce_data.get('is_seasonal', False),
                peak_season_start=datetime.fromisoformat(produce_data['peak_season_start']).date() if produce_data.get('peak_season_start') else None,
                peak_season_end=datetime.fromisoformat(produce_data['peak_season_end']).date() if produce_data.get('peak_season_end') else None,
                off_season_available=produce_data.get('off_season_available', True),
                quality_score=produce_data.get('quality_score'),
                inspection_date=datetime.fromisoformat(produce_data['inspection_date']).date() if produce_data.get('inspection_date') else None,
                inspector_name=produce_data.get('inspector_name'),
                quality_notes=produce_data.get('quality_notes'),
                barcode=produce_data.get('barcode'),
                plu_code=produce_data.get('plu_code'),
                batch_number=produce_data.get('batch_number'),
                supplier_id=produce_data.get('supplier_id'),
                supplier_farm=produce_data.get('supplier_farm'),
                current_stock=produce_data.get('current_stock', 0),
                minimum_stock_level=produce_data.get('minimum_stock_level', 5),
                maximum_stock_level=produce_data.get('maximum_stock_level', 100),
                reorder_point=produce_data.get('reorder_point', 10),
                is_active=produce_data.get('is_active', True),
                is_on_promotion=produce_data.get('is_on_promotion', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(produce)
            db.session.commit()
            return True, produce, "Fresh produce created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating fresh produce: {e}")
            return False, None, str(e)
    
    def get_fresh_produce(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshProduce]:
        """Get fresh produce with optional filters"""
        try:
            query = FreshProduce.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'produce_category' in filters:
                    query = query.filter(FreshProduce.produce_category == filters['produce_category'])
                if 'variety' in filters:
                    query = query.filter(FreshProduce.variety.ilike(f"%{filters['variety']}%"))
                if 'origin' in filters:
                    query = query.filter(FreshProduce.origin.ilike(f"%{filters['origin']}%"))
                if 'grade' in filters:
                    query = query.filter(FreshProduce.grade == filters['grade'])
                if 'certification' in filters:
                    query = query.filter(FreshProduce.certification == filters['certification'])
                if 'is_seasonal' in filters:
                    query = query.filter(FreshProduce.is_seasonal == filters['is_seasonal'])
                if 'is_on_promotion' in filters:
                    query = query.filter(FreshProduce.is_on_promotion == filters['is_on_promotion'])
                if 'min_quality_score' in filters:
                    query = query.filter(FreshProduce.quality_score >= filters['min_quality_score'])
                if 'max_quality_score' in filters:
                    query = query.filter(FreshProduce.quality_score <= filters['max_quality_score'])
                if 'in_stock' in filters and filters['in_stock']:
                    query = query.filter(FreshProduce.current_stock > 0)
            
            return query.order_by(FreshProduce.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting fresh produce: {e}")
            return []
    
    def get_produce_by_sku(self, sku: str) -> Optional[FreshProduce]:
        """Get produce by SKU"""
        try:
            return FreshProduce.query.filter_by(
                sku_base=sku,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting produce by SKU: {e}")
            return None
    
    # Fresh Produce Inventory Methods
    
    def create_fresh_produce_inventory(self, inventory_data: Dict[str, Any], 
                                   user_id: Optional[str] = None) -> Tuple[bool, Optional[FreshProduceInventory], str]:
        """Create a new fresh produce inventory record"""
        try:
            # Verify produce exists
            produce = FreshProduce.query.filter_by(
                id=inventory_data['produce_id'],
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not produce:
                return False, None, "Produce not found"
            
            inventory = FreshProduceInventory(
                produce_id=inventory_data['produce_id'],
                batch_number=inventory_data.get('batch_number'),
                initial_quantity=int(inventory_data['initial_quantity']),
                current_quantity=int(inventory_data['current_quantity']),
                unit_of_measure=inventory_data.get('unit_of_measure', 'units'),
                received_date=datetime.fromisoformat(inventory_data['received_date']).date() if inventory_data.get('received_date') else date.today(),
                expiry_date=datetime.fromisoformat(inventory_data['expiry_date']).date() if inventory_data.get('expiry_date') else None,
                quality_grade=inventory_data.get('quality_grade'),
                quality_score=inventory_data.get('quality_score'),
                spoilage_percentage=inventory_data.get('spoilage_percentage', 0.0),
                storage_location=inventory_data.get('storage_location'),
                display_area=inventory_data.get('display_area'),
                storage_temperature=inventory_data.get('storage_temperature'),
                temperature_log=inventory_data.get('temperature_log', []),
                last_sale_date=datetime.fromisoformat(inventory_data['last_sale_date']).date() if inventory_data.get('last_sale_date') else None,
                last_waste_date=datetime.fromisoformat(inventory_data['last_waste_date']).date() if inventory_data.get('last_waste_date') else None,
                is_active=inventory_data.get('is_active', True),
                is_on_display=inventory_data.get('is_on_display', True),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(inventory)
            db.session.commit()
            return True, inventory, "Fresh produce inventory created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating fresh produce inventory: {e}")
            return False, None, str(e)
    
    def get_produce_inventory(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshProduceInventory]:
        """Get produce inventory with optional filters"""
        try:
            query = FreshProduceInventory.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'produce_id' in filters:
                    query = query.filter(FreshProduceInventory.produce_id == filters['produce_id'])
                if 'batch_number' in filters:
                    query = query.filter(FreshProduceInventory.batch_number == filters['batch_number'])
                if 'quality_grade' in filters:
                    query = query.filter(FreshProduceInventory.quality_grade == filters['quality_grade'])
                if 'storage_location' in filters:
                    query = query.filter(FreshProduceInventory.storage_location.ilike(f"%{filters['storage_location']}%"))
                if 'display_area' in filters:
                    query = query.filter(FreshProduceInventory.display_area.ilike(f"%{filters['display_area']}%"))
                if 'near_expiry' in filters and filters['near_expiry']:
                    # Filter for items expiring within 3 days
                    threshold_date = date.today() + timedelta(days=3)
                    query = query.filter(
                        FreshProduceInventory.expiry_date.isnot(None),
                        FreshProduceInventory.expiry_date <= threshold_date
                    )
                if 'low_stock' in filters and filters['low_stock']:
                    # Filter for items below minimum stock
                    query = query.filter(
                        FreshProduceInventory.current_quantity < FreshProduce.minimum_stock_level
                    )
            
            return query.order_by(FreshProduceInventory.received_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting produce inventory: {e}")
            return []
    
    # Price Update Methods
    
    def create_price_update(self, price_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[FreshProducePriceUpdate], str]:
        """Create a new price update record"""
        try:
            # Verify produce exists
            produce = FreshProduce.query.filter_by(
                id=price_data['produce_id'],
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not produce:
                return False, None, "Produce not found"
            
            # Calculate price change percentage
            old_price = Decimal(str(price_data.get('old_price', 0)))
            new_price = Decimal(str(price_data['new_price']))
            price_change_percentage = 0.0
            if old_price > 0:
                price_change_percentage = float(((new_price - old_price) / old_price) * 100)
            
            price_update = FreshProducePriceUpdate(
                produce_id=price_data['produce_id'],
                old_price=old_price,
                new_price=new_price,
                price_change_percentage=price_change_percentage,
                change_reason=price_data.get('change_reason'),
                supplier_price_change=price_data.get('supplier_price_change', False),
                effective_date=datetime.fromisoformat(price_data['effective_date']).date() if price_data.get('effective_date') else date.today(),
                approved_by=price_data.get('approved_by'),
                approval_date=datetime.fromisoformat(price_data['approval_date']).date() if price_data.get('approval_date') else None,
                market_price=Decimal(str(price_data.get('market_price', 0))),
                competitor_price=Decimal(str(price_data.get('competitor_price', 0))),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(price_update)
            
            # Update produce price
            produce.unit_price = new_price
            db.session.commit()
            return True, price_update, "Price update created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating price update: {e}")
            return False, None, str(e)
    
    def get_price_updates(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshProducePriceUpdate]:
        """Get price updates with optional filters"""
        try:
            query = FreshProducePriceUpdate.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'produce_id' in filters:
                    query = query.filter(FreshProducePriceUpdate.produce_id == filters['produce_id'])
                if 'change_reason' in filters:
                    query = query.filter(FreshProducePriceUpdate.change_reason == filters['change_reason'])
                if 'supplier_price_change' in filters:
                    query = query.filter(FreshProducePriceUpdate.supplier_price_change == filters['supplier_price_change'])
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date']).date()
                    query = query.filter(FreshProducePriceUpdate.effective_date >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date']).date()
                    query = query.filter(FreshProducePriceUpdate.effective_date <= end_date)
            
            return query.order_by(FreshProducePriceUpdate.effective_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting price updates: {e}")
            return []
    
    # Quality Check Methods
    
    def create_quality_check(self, quality_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[FreshProduceQualityCheck], str]:
        """Create a new quality check record"""
        try:
            # Verify produce exists
            produce = FreshProduce.query.filter_by(
                id=quality_data['produce_id'],
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not produce:
                return False, None, "Produce not found"
            
            quality_check = FreshProduceQualityCheck(
                produce_id=quality_data['produce_id'],
                batch_number=quality_data.get('batch_number'),
                check_date=datetime.fromisoformat(quality_data['check_date']).date() if quality_data.get('check_date') else date.today(),
                check_time=datetime.fromisoformat(quality_data['check_time']) if quality_data.get('check_time') else datetime.utcnow(),
                inspector_name=quality_data['inspector_name'],
                overall_quality_score=int(quality_data.get('overall_quality_score', 5)),
                appearance_score=int(quality_data.get('appearance_score', 5)),
                freshness_score=int(quality_data.get('freshness_score', 5)),
                size_consistency=int(quality_data.get('size_consistency', 5)),
                color_quality=quality_data.get('color_quality'),
                firmness=quality_data.get('firmness'),
                ripeness=quality_data.get('ripeness'),
                defects=quality_data.get('defects', []),
                temperature_fahrenheit=quality_data.get('temperature_fahrenheit'),
                humidity_percentage=quality_data.get('humidity_percentage'),
                weight_sample_size=int(quality_data.get('weight_sample_size', 10)),
                average_weight=quality_data.get('average_weight'),
                grade_assigned=quality_data.get('grade_assigned'),
                passed_inspection=quality_data.get('passed_inspection', True),
                rejection_reasons=quality_data.get('rejection_reasons', []),
                actions_required=quality_data.get('actions_required', []),
                follow_up_required=quality_data.get('follow_up_required', False),
                follow_up_date=datetime.fromisoformat(quality_data['follow_up_date']).date() if quality_data.get('follow_up_date') else None,
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(quality_check)
            
            # Update inventory quality score
            inventory = FreshProduceInventory.query.filter_by(
                produce_id=quality_data['produce_id'],
                batch_number=quality_data.get('batch_number'),
                tenant_id=self.tenant_id
            ).first()
            
            if inventory:
                inventory.current_quality_score = int(quality_data.get('overall_quality_score', 5))
                inventory.last_quality_check = quality_check.check_date
                db.session.commit()
            
            return True, quality_check, "Quality check created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating quality check: {e}")
            return False, None, str(e)
    
    def get_quality_checks(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshProduceQualityCheck]:
        """Get quality checks with optional filters"""
        try:
            query = FreshProduceQualityCheck.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'produce_id' in filters:
                    query = query.filter(FreshProduceQualityCheck.produce_id == filters['produce_id'])
                if 'batch_number' in filters:
                    query = query.filter(FreshProduceQualityCheck.batch_number == filters['batch_number'])
                if 'inspector_name' in filters:
                    query = query.filter(FreshProduceQualityCheck.inspector_name.ilike(f"%{filters['inspector_name']}%"))
                if 'grade_assigned' in filters:
                    query = query.filter(FreshProduceQualityCheck.grade_assigned == filters['grade_assigned'])
                if 'passed_inspection' in filters:
                    query = query.filter(FreshProduceQualityCheck.passed_inspection == filters['passed_inspection'])
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date']).date()
                    query = query.filter(FreshProduceQualityCheck.check_date >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date']).date()
                    query = query.filter(FreshProduceQualityCheck.check_date <= end_date)
            
            return query.order_by(FreshProduceQualityCheck.check_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting quality checks: {e}")
            return []
    
    # Weighing Scale Integration Methods
    
    def create_weighing_scale(self, scale_data: Dict[str, Any], 
                             user_id: Optional[str] = None) -> Tuple[bool, Optional[WeighingScaleIntegration], str]:
        """Create a new weighing scale integration"""
        try:
            scale = WeighingScaleIntegration(
                scale_id=scale_data['scale_id'],
                scale_name=scale_data['scale_name'],
                location=scale_data.get('location'),
                department=scale_data.get('department'),
                connection_type=scale_data['connection_type'],
                connection_parameters=scale_data.get('connection_parameters', {}),
                capacity_kg=scale_data.get('capacity_kg'),
                readability_g=scale_data.get('readability_g'),
                units_supported=scale_data.get('units_supported', []),
                tare_weight_g=scale_data.get('tare_weight_g', 0.0),
                auto_tare_enabled=scale_data.get('auto_tare_enabled', True),
                price_per_weight_enabled=scale_data.get('price_per_weight_enabled', True),
                last_calibration_date=datetime.fromisoformat(scale_data['last_calibration_date']).date() if scale_data.get('last_calibration_date') else None,
                calibration_frequency_days=scale_data.get('calibration_frequency_days', 7),
                next_calibration_date=datetime.fromisoformat(scale_data['next_calibration_date']).date() if scale_data.get('next_calibration_date') else None,
                calibration_certificate=scale_data.get('calibration_certificate'),
                is_active=scale_data.get('is_active', True),
                is_connected=scale_data.get('is_connected', False),
                last_connection_time=datetime.fromisoformat(scale_data['last_connection_time']) if scale_data.get('last_connection_time') else None,
                daily_weighings=scale_data.get('daily_weighings', 0),
                total_weight_kg=scale_data.get('total_weight_kg', 0.0),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(scale)
            db.session.commit()
            return True, scale, "Weighing scale created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating weighing scale: {e}")
            return False, None, str(e)
    
    def get_weighing_scales(self, filters: Optional[Dict[str, Any]] = None) -> List[WeighingScaleIntegration]:
        """Get weighing scales with optional filters"""
        try:
            query = WeighingScaleIntegration.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'location' in filters:
                    query = query.filter(WeighingScaleIntegration.location.ilike(f"%{filters['location']}%"))
                if 'department' in filters:
                    query = query.filter(WeighingScaleIntegration.department == filters['department'])
                if 'connection_type' in filters:
                    query = query.filter(WeighingScaleIntegration.connection_type == filters['connection_type'])
                if 'is_active' in filters:
                    query = query.filter(WeighingScaleIntegration.is_active == filters['is_active'])
                if 'is_connected' in filters:
                    query = query.filter(WeighingScaleIntegration.is_connected == filters['is_connected'])
                if 'calibration_due' in filters and filters['calibration_due']:
                    today = date.today()
                    query = query.filter(
                        WeighingScaleIntegration.next_calibration_date.isnot(None),
                        WeighingScaleIntegration.next_calibration_date <= today
                    )
            
            return query.order_by(WeighingScaleIntegration.scale_name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting weighing scales: {e}")
            return []
    
    # Combo Offer Methods
    
    def create_combo_offer(self, combo_data: Dict[str, Any], 
                        user_id: Optional[str] = None) -> Tuple[bool, Optional[ComboOffer], str]:
        """Create a new combo offer"""
        try:
            combo = ComboOffer(
                combo_code=combo_data['combo_code'],
                name=combo_data['name'],
                description=combo_data.get('description'),
                start_date=datetime.fromisoformat(combo_data['start_date']).date() if combo_data.get('start_date') else date.today(),
                end_date=datetime.fromisoformat(combo_data['end_date']).date() if combo_data.get('end_date') else None,
                is_active=combo_data.get('is_active', True),
                combo_type=combo_data['combo_type'],
                discount_type=combo_data.get('discount_type'),
                discount_value=Decimal(str(combo_data['discount_value'])),
                combo_price=Decimal(str(combo_data['combo_price'])),
                main_product_id=combo_data.get('main_product_id'),
                main_product_quantity=combo_data.get('main_product_quantity', 1),
                additional_products=combo_data.get('additional_products', []),
                minimum_purchase_quantity=combo_data.get('minimum_purchase_quantity', 1),
                maximum_per_customer=combo_data.get('maximum_per_customer'),
                applicable_categories=combo_data.get('applicable_categories', []),
                excluded_products=combo_data.get('excluded_products', []),
                display_name=combo_data.get('display_name'),
                image_url=combo_data.get('image_url'),
                promotional_text=combo_data.get('promotional_text'),
                usage_count=combo_data.get('usage_count', 0),
                revenue_generated=Decimal(str(combo_data.get('revenue_generated', 0))),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(combo)
            db.session.commit()
            return True, combo, "Combo offer created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating combo offer: {e}")
            return False, None, str(e)
    
    def get_combo_offers(self, filters: Optional[Dict[str, Any]] = None) -> List[ComboOffer]:
        """Get combo offers with optional filters"""
        try:
            query = ComboOffer.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'combo_type' in filters:
                    query = query.filter(ComboOffer.combo_type == filters['combo_type'])
                if 'discount_type' in filters:
                    query = query.filter(ComboOffer.discount_type == filters['discount_type'])
                if 'is_active' in filters:
                    query = query.filter(ComboOffer.is_active == filters['is_active'])
                if 'valid_only' in filters and filters['valid_only']:
                    today = date.today()
                    query = query.filter(
                        ComboOffer.is_active == True,
                        ComboOffer.start_date <= today,
                        (ComboOffer.end_date.is_(None) | (ComboOffer.end_date >= today))
                    )
                if 'applicable_categories' in filters:
                    categories = filters['applicable_categories']
                    if categories:
                        category_filter = ComboOffer.applicable_categories.contains(categories)
                        query = query.filter(category_filter)
            
            return query.order_by(ComboOffer.is_active.desc(), ComboOffer.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting combo offers: {e}")
            return []
    
    def use_combo_offer(self, combo_id: int) -> Tuple[bool, str]:
        """Use a combo offer and increment usage count"""
        try:
            combo = ComboOffer.query.filter_by(
                id=combo_id,
                tenant_id=self.tenant_id
            ).first()
            
            if not combo:
                return False, "Combo offer not found"
            
            if not combo.is_valid():
                return False, "Combo offer is not valid or expired"
            
            # Increment usage count
            combo.usage_count += 1
            
            # Check if maximum per customer reached (this would need customer tracking)
            # For simplicity, we're just incrementing total usage here
            
            db.session.commit()
            return True, "Combo offer used successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error using combo offer: {e}")
            return False, str(e)
    
    # Shelf Life Management Methods
    
    def create_shelf_life_management(self, shelf_data: Dict[str, Any], 
                                  user_id: Optional[str] = None) -> Tuple[bool, Optional[ShelfLifeManagement], str]:
        """Create a new shelf life management record"""
        try:
            shelf_life = ShelfLifeManagement(
                product_id=shelf_data['product_id'],
                batch_number=shelf_data.get('batch_number'),
                production_date=datetime.fromisoformat(shelf_data['production_date']).date() if shelf_data.get('production_date') else None,
                received_date=datetime.fromisoformat(shelf_data['received_date']).date() if shelf_data.get('received_date') else date.today(),
                expiry_date=datetime.fromisoformat(shelf_data['expiry_date']).date() if shelf_data.get('expiry_date') else None,
                optimal_until=datetime.fromisoformat(shelf_data['optimal_until']).date() if shelf_data.get('optimal_until') else None,
                good_until=datetime.fromisoformat(shelf_data['good_until']).date() if shelf_data.get('good_until') else None,
                sell_by_date=datetime.fromisoformat(shelf_data['sell_by_date']).date() if shelf_data.get('sell_by_date') else None,
                optimal_temperature=shelf_data.get('optimal_temperature'),
                optimal_humidity=shelf_data.get('optimal_humidity'),
                light_requirements=shelf_data.get('light_requirements'),
                quality_loss_rate=shelf_data.get('quality_loss_rate', 0.0),
                current_quality_score=shelf_data.get('current_quality_score', 10),
                discount_schedule=shelf_data.get('discount_schedule', []),
                mark_down_schedule=shelf_data.get('mark_down_schedule', []),
                disposal_method=shelf_data.get('disposal_method'),
                is_active=shelf_data.get('is_active', True),
                requires_action=shelf_data.get('requires_action', False),
                action_taken=shelf_data.get('action_taken'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(shelf_life)
            db.session.commit()
            return True, shelf_life, "Shelf life management created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating shelf life management: {e}")
            return False, None, str(e)
    
    def get_shelf_life_management(self, filters: Optional[Dict[str, Any]] = None) -> List[ShelfLifeManagement]:
        """Get shelf life management records with optional filters"""
        try:
            query = ShelfLifeManagement.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'product_id' in filters:
                    query = query.filter(ShelfLifeManagement.product_id == filters['product_id'])
                if 'batch_number' in filters:
                    query = query.filter(ShelfLifeManagement.batch_number == filters['batch_number'])
                if 'requires_action' in filters:
                    query = query.filter(ShelfLifeManagement.requires_action == filters['requires_action'])
                if 'action_taken' in filters:
                    query = query.filter(ShelfLifeManagement.action_taken.ilike(f"%{filters['action_taken']}%"))
                if 'disposal_method' in filters:
                    query = query.filter(ShelfLifeManagement.disposal_method == filters['disposal_method'])
                if 'near_expiry' in filters and filters['near_expiry']:
                    # Filter for items expiring within 3 days
                    threshold_date = date.today() + timedelta(days=3)
                    query = query.filter(
                        ShelfLifeManagement.sell_by_date.isnot(None),
                        ShelfLifeManagement.sell_by_date <= threshold_date
                    )
            
            return query.order_by(ShelfLifeManagement.sell_by_date.asc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting shelf life management: {e}")
            return []
    
    # Fresh Counter Methods
    
    def create_fresh_counter(self, counter_data: Dict[str, Any], 
                          user_id: Optional[str] = None) -> Tuple[bool, Optional[FreshCounter], str]:
        """Create a new fresh counter"""
        try:
            counter = FreshCounter(
                counter_id=counter_data['counter_id'],
                name=counter_data['name'],
                counter_type=counter_data['counter_type'],
                location=counter_data.get('location'),
                department=counter_data.get('department'),
                section=counter_data.get('section'),
                opening_time=counter_data.get('opening_time'),
                closing_time=counter_data.get('closing_time'),
                operating_days=counter_data.get('operating_days', []),
                manager_name=counter_data.get('manager_name'),
                staff_count=counter_data.get('staff_count', 1),
                required_skills=counter_data.get('required_skills', []),
                equipment_list=counter_data.get('equipment_list', []),
                weighing_scale_id=counter_data.get('weighing_scale_id'),
                service_time_minutes=counter_data.get('service_time_minutes', 5),
                queue_management_enabled=counter_data.get('queue_management_enabled', True),
                advance_ordering_enabled=counter_data.get('advance_ordering_enabled', True),
                daily_customers=counter_data.get('daily_customers', 0),
                average_transaction_value=Decimal(str(counter_data.get('average_transaction_value', 0))),
                customer_satisfaction_score=counter_data.get('customer_satisfaction_score'),
                is_active=counter_data.get('is_active', True),
                status=counter_data.get('status', 'Open'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(counter)
            db.session.commit()
            return True, counter, "Fresh counter created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating fresh counter: {e}")
            return False, None, str(e)
    
    def get_fresh_counters(self, filters: Optional[Dict[str, Any]] = None) -> List[FreshCounter]:
        """Get fresh counters with optional filters"""
        try:
            query = FreshCounter.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'counter_type' in filters:
                    query = query.filter(FreshCounter.counter_type == filters['counter_type'])
                if 'location' in filters:
                    query = query.filter(FreshCounter.location.ilike(f"%{filters['location']}%"))
                if 'department' in filters:
                    query = query.filter(FreshCounter.department == filters['department'])
                if 'section' in filters:
                    query = query.filter(FreshCounter.section == filters['section'])
                if 'is_active' in filters:
                    query = query.filter(FreshCounter.is_active == filters['is_active'])
                if 'status' in filters:
                    query = query.filter(FreshCounter.status == filters['status'])
            
            return query.order_by(FreshCounter.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting fresh counters: {e}")
            return []
    
    # Analytics and Reporting Methods
    
    def get_fresh_produce_analytics(self, start_date: Optional[date] = None, 
                                   end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get fresh produce analytics"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get all produce
            produce_list = FreshProduce.query.filter_by(
                tenant_id=self.tenant_id,
                is_active=True
            ).all()
            
            analytics = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_produce_items': len(produce_list),
                    'total_categories': len(set(p.produce_category for p in produce_list)),
                    'average_quality_score': sum(p.quality_score or 0 for p in produce_list) / len(produce_list) if produce_list else 0,
                    'seasonal_items': sum(1 for p in produce_list if p.is_seasonal),
                    'promotional_items': sum(1 for p in produce_list if p.is_on_promotion),
                    'total_stock_value': sum(p.current_stock * p.unit_price for p in produce_list)
                },
                'category_breakdown': {},
                'quality_distribution': {
                    'excellent': 0,
                    'good': 0,
                    'fair': 0,
                    'poor': 0
                },
                'origin_breakdown': {}
            }
            
            # Analyze by category
            for produce in produce_list:
                category = produce.produce_category or 'Unknown'
                if category not in analytics['category_breakdown']:
                    analytics['category_breakdown'][category] = {
                        'count': 0,
                        'total_value': 0.0
                    }
                
                analytics['category_breakdown'][category]['count'] += 1
                analytics['category_breakdown'][category]['total_value'] += float(produce.current_stock * produce.unit_price)
                
                # Analyze quality distribution
                quality_score = produce.quality_score or 5
                if quality_score >= 9:
                    analytics['quality_distribution']['excellent'] += 1
                elif quality_score >= 7:
                    analytics['quality_distribution']['good'] += 1
                elif quality_score >= 5:
                    analytics['quality_distribution']['fair'] += 1
                else:
                    analytics['quality_distribution']['poor'] += 1
                
                # Analyze origin breakdown
                origin = produce.origin or 'Unknown'
                if origin not in analytics['origin_breakdown']:
                    analytics['origin_breakdown'][origin] = 0
                
                analytics['origin_breakdown'][origin] += 1
            
            return analytics
            
        except Exception as e:
            current_app.logger.error(f"Error generating fresh produce analytics: {e}")
            return {}
    
    def get_inventory_turnover_report(self, start_date: Optional[date] = None, 
                                   end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get inventory turnover report"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get inventory records
            inventory_records = FreshProduceInventory.query.filter(
                FreshProduceInventory.tenant_id == self.tenant_id,
                FreshProduceInventory.received_date >= start_date,
                FreshProduceInventory.received_date <= end_date
            ).all()
            
            # Calculate turnover metrics
            total_received = sum(record.initial_quantity for record in inventory_records)
            total_waste = sum(
                record.initial_quantity * (record.spoilage_percentage / 100)
                for record in inventory_records
            )
            total_sold = total_received - total_waste
            
            # Calculate by category
            category_turnover = {}
            for record in inventory_records:
                if record.produce:
                    category = record.produce.produce_category or 'Unknown'
                    if category not in category_turnover:
                        category_turnover[category] = {
                            'received': 0,
                            'waste': 0,
                            'sold': 0,
                            'waste_percentage': 0.0
                        }
                    
                    category_turnover[category]['received'] += record.initial_quantity
                    waste_quantity = record.initial_quantity * (record.spoilage_percentage / 100)
                    category_turnover[category]['waste'] += waste_quantity
                    category_turnover[category]['sold'] += record.initial_quantity - waste_quantity
            
            # Calculate waste percentages
            for category, data in category_turnover.items():
                if data['received'] > 0:
                    data['waste_percentage'] = (data['waste'] / data['received']) * 100
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_received': total_received,
                    'total_waste': total_waste,
                    'total_sold': total_sold,
                    'overall_waste_percentage': (total_waste / total_received * 100) if total_received > 0 else 0
                },
                'category_breakdown': category_turnover
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating inventory turnover report: {e}")
            return {}


# Factory function for creating supermarket service instances
def create_supermarket_groceries_service(tenant_id: Optional[str] = None) -> SupermarketGroceriesService:
    """Create a supermarket & groceries service instance"""
    return SupermarketGroceriesService(tenant_id)