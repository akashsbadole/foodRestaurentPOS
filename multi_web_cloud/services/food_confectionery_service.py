"""
Food & Confectionery service layer with comprehensive business logic
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from decimal import Decimal
from models import db
from models.food_confectionery import (
    FoodProduct, FoodBatch, TemperatureLog, Recipe, RecipeItem, 
    FoodWastage, WeighingScaleIntegration
)
from utils.feature_flag_manager import feature_manager


class FoodConfectioneryService:
    """Service layer for food and confectionery operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a food feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Food Product Management Methods
    
    def create_food_product(self, product_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[FoodProduct], str]:
        """Create a new food product"""
        try:
            food_product = FoodProduct(
                product_id=product_data['product_id'],
                sku_base=product_data['sku_base'],
                name=product_data['name'],
                description=product_data.get('description'),
                food_category=product_data.get('food_category'),
                subcategory=product_data.get('subcategory'),
                brand=product_data.get('brand'),
                flavor_variety=product_data.get('flavor_variety'),
                size_description=product_data.get('size_description'),
                unit_of_measure=product_data.get('unit_of_measure'),
                unit_price=Decimal(str(product_data['unit_price'])),
                cost_price=Decimal(str(product_data.get('cost_price', 0))),
                wholesale_price=Decimal(str(product_data.get('wholesale_price', 0))),
                shelf_life_days=product_data.get('shelf_life_days'),
                storage_temperature_min=product_data.get('storage_temperature_min'),
                storage_temperature_max=product_data.get('storage_temperature_max'),
                storage_requirements=product_data.get('storage_requirements'),
                handling_instructions=product_data.get('handling_instructions'),
                calories_per_serving=product_data.get('calories_per_serving'),
                serving_size=product_data.get('serving_size'),
                nutritional_info=product_data.get('nutritional_info', {}),
                allergens=product_data.get('allergens', []),
                dietary_restrictions=product_data.get('dietary_restrictions', []),
                certifications=product_data.get('certifications', []),
                net_weight=product_data.get('net_weight'),
                gross_weight=product_data.get('gross_weight'),
                package_dimensions=product_data.get('package_dimensions', {}),
                requires_batch_tracking=product_data.get('requires_batch_tracking', False),
                expiry_date_required=product_data.get('expiry_date_required', True),
                sell_by_days_before_expiry=product_data.get('sell_by_days_before_expiry', 3),
                temperature_sensitive=product_data.get('temperature_sensitive', False),
                cold_chain_required=product_data.get('cold_chain_required', False),
                is_prepared_item=product_data.get('is_prepared_item', False),
                recipe_id=product_data.get('recipe_id'),
                preparation_time_minutes=product_data.get('preparation_time_minutes'),
                cooking_instructions=product_data.get('cooking_instructions'),
                sold_by_weight=product_data.get('sold_by_weight', False),
                price_per_kg=Decimal(str(product_data.get('price_per_kg', 0))),
                tare_weight=product_data.get('tare_weight', 0.0),
                minimum_stock_level=product_data.get('minimum_stock_level', 5),
                maximum_stock_level=product_data.get('maximum_stock_level', 100),
                reorder_point=product_data.get('reorder_point', 10),
                primary_supplier_id=product_data.get('primary_supplier_id'),
                supplier_sku=product_data.get('supplier_sku'),
                barcode=product_data.get('barcode'),
                upc=product_data.get('upc'),
                ean=product_data.get('ean'),
                is_seasonal=product_data.get('is_seasonal', False),
                is_promotional=product_data.get('is_promotional', False),
                is_best_seller=product_data.get('is_best_seller', False),
                is_new_product=product_data.get('is_new_product', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(food_product)
            db.session.commit()
            return True, food_product, "Food product created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating food product: {e}")
            return False, None, str(e)
    
    def get_food_products(self, filters: Optional[Dict[str, Any]] = None) -> List[FoodProduct]:
        """Get food products with optional filters"""
        try:
            query = FoodProduct.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'food_category' in filters:
                    query = query.filter(FoodProduct.food_category == filters['food_category'])
                if 'brand' in filters:
                    query = query.filter(FoodProduct.brand.ilike(f"%{filters['brand']}%"))
                if 'temperature_sensitive' in filters:
                    query = query.filter(FoodProduct.temperature_sensitive == filters['temperature_sensitive'])
                if 'requires_batch_tracking' in filters:
                    query = query.filter(FoodProduct.requires_batch_tracking == filters['requires_batch_tracking'])
                if 'sold_by_weight' in filters:
                    query = query.filter(FoodProduct.sold_by_weight == filters['sold_by_weight'])
                if 'min_price' in filters:
                    query = query.filter(FoodProduct.unit_price >= Decimal(str(filters['min_price'])))
                if 'max_price' in filters:
                    query = query.filter(FoodProduct.unit_price <= Decimal(str(filters['max_price'])))
                if 'is_seasonal' in filters:
                    query = query.filter(FoodProduct.is_seasonal == filters['is_seasonal'])
            
            return query.order_by(FoodProduct.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting food products: {e}")
            return []
    
    def get_food_product_by_id(self, product_id: int) -> Optional[FoodProduct]:
        """Get a specific food product"""
        try:
            return FoodProduct.query.filter_by(
                id=product_id,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting food product: {e}")
            return None
    
    def get_food_product_by_sku(self, sku: str) -> Optional[FoodProduct]:
        """Get a food product by SKU"""
        try:
            return FoodProduct.query.filter_by(
                sku_base=sku,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting food product by SKU: {e}")
            return None
    
    # Batch Management Methods
    
    def create_food_batch(self, batch_data: Dict[str, Any], 
                         user_id: Optional[str] = None) -> Tuple[bool, Optional[FoodBatch], str]:
        """Create a new food batch"""
        try:
            # Verify product exists
            product = FoodProduct.query.filter_by(
                id=batch_data['product_id'],
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
            
            if not product:
                return False, None, "Product not found"
            
            food_batch = FoodBatch(
                batch_number=batch_data['batch_number'],
                product_id=batch_data['product_id'],
                production_date=datetime.fromisoformat(batch_data['production_date']).date() if batch_data.get('production_date') else None,
                expiry_date=datetime.fromisoformat(batch_data['expiry_date']).date() if batch_data.get('expiry_date') else None,
                received_date=datetime.fromisoformat(batch_data['received_date']).date() if batch_data.get('received_date') else date.today(),
                initial_quantity=int(batch_data['initial_quantity']),
                current_quantity=int(batch_data['current_quantity']),
                unit_cost=Decimal(str(batch_data.get('unit_cost', 0))),
                quality_grade=batch_data.get('quality_grade'),
                quality_notes=batch_data.get('quality_notes'),
                supplier_id=batch_data.get('supplier_id'),
                supplier_batch_number=batch_data.get('supplier_batch_number'),
                storage_location=batch_data.get('storage_location'),
                storage_temperature=batch_data.get('storage_temperature'),
                storage_humidity=batch_data.get('storage_humidity'),
                is_active=batch_data.get('is_active', True),
                is_quarantined=batch_data.get('is_quarantined', False),
                quarantine_reason=batch_data.get('quarantine_reason'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(food_batch)
            db.session.commit()
            return True, food_batch, "Food batch created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating food batch: {e}")
            return False, None, str(e)
    
    def get_product_batches(self, product_id: int, include_expired: bool = False) -> List[FoodBatch]:
        """Get batches for a product"""
        try:
            query = FoodBatch.query.filter_by(
                product_id=product_id,
                tenant_id=self.tenant_id,
                is_active=True
            )
            
            if not include_expired:
                # Filter out expired batches
                today = date.today()
                query = query.filter(
                    db.or_(
                        FoodBatch.expiry_date.is_(None),
                        FoodBatch.expiry_date > today
                    )
                )
            
            return query.order_by(FoodBatch.expiry_date.asc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting product batches: {e}")
            return []
    
    def get_expiring_batches(self, days_threshold: int = 7) -> List[FoodBatch]:
        """Get batches expiring within the threshold"""
        try:
            threshold_date = date.today() + timedelta(days=days_threshold)
            
            return FoodBatch.query.filter(
                FoodBatch.tenant_id == self.tenant_id,
                FoodBatch.is_active == True,
                FoodBatch.expiry_date.isnot(None),
                FoodBatch.expiry_date <= threshold_date,
                FoodBatch.current_quantity > 0
            ).order_by(FoodBatch.expiry_date.asc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting expiring batches: {e}")
            return []
    
    def get_expired_batches(self) -> List[FoodBatch]:
        """Get expired batches"""
        try:
            today = date.today()
            
            return FoodBatch.query.filter(
                FoodBatch.tenant_id == self.tenant_id,
                FoodBatch.is_active == True,
                FoodBatch.expiry_date.isnot(None),
                FoodBatch.expiry_date < today,
                FoodBatch.current_quantity > 0
            ).order_by(FoodBatch.expiry_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting expired batches: {e}")
            return []
    
    # Temperature Logging Methods
    
    def create_temperature_log(self, log_data: Dict[str, Any], 
                             user_id: Optional[str] = None) -> Tuple[bool, Optional[TemperatureLog], str]:
        """Create a new temperature log"""
        try:
            temperature_log = TemperatureLog(
                product_id=log_data['product_id'],
                batch_id=log_data.get('batch_id'),
                temperature_celsius=float(log_data['temperature_celsius']),
                target_temperature=log_data.get('target_temperature'),
                tolerance_plus=log_data.get('tolerance_plus', 2.0),
                tolerance_minus=log_data.get('tolerance_minus', 2.0),
                reading_time=datetime.fromisoformat(log_data['reading_time']) if log_data.get('reading_time') else datetime.utcnow(),
                reading_device_id=log_data.get('reading_device_id'),
                reading_location=log_data.get('reading_location'),
                recorded_by=log_data.get('recorded_by'),
                verified_by=log_data.get('verified_by'),
                verification_time=datetime.fromisoformat(log_data['verification_time']) if log_data.get('verification_time') else None,
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            # Check if temperature is within range
            temperature_log.is_within_range = temperature_log.check_temperature_range()
            temperature_log.requires_action = not temperature_log.is_within_range
            
            db.session.add(temperature_log)
            db.session.commit()
            return True, temperature_log, "Temperature log created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating temperature log: {e}")
            return False, None, str(e)
    
    def get_temperature_logs(self, filters: Optional[Dict[str, Any]] = None) -> List[TemperatureLog]:
        """Get temperature logs with optional filters"""
        try:
            query = TemperatureLog.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'product_id' in filters:
                    query = query.filter(TemperatureLog.product_id == filters['product_id'])
                if 'batch_id' in filters:
                    query = query.filter(TemperatureLog.batch_id == filters['batch_id'])
                if 'reading_location' in filters:
                    query = query.filter(TemperatureLog.reading_location == filters['reading_location'])
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date'])
                    query = query.filter(TemperatureLog.reading_time >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date'])
                    query = query.filter(TemperatureLog.reading_time <= end_date)
                if 'out_of_range_only' in filters and filters['out_of_range_only']:
                    query = query.filter(TemperatureLog.is_within_range == False)
            
            return query.order_by(TemperatureLog.reading_time.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting temperature logs: {e}")
            return []
    
    # Recipe Management Methods
    
    def create_recipe(self, recipe_data: Dict[str, Any], 
                     user_id: Optional[str] = None) -> Tuple[bool, Optional[Recipe], str]:
        """Create a new recipe"""
        try:
            recipe = Recipe(
                recipe_code=recipe_data['recipe_code'],
                name=recipe_data['name'],
                description=recipe_data.get('description'),
                category=recipe_data.get('category'),
                cuisine_type=recipe_data.get('cuisine_type'),
                preparation_time_minutes=recipe_data.get('preparation_time_minutes'),
                cooking_time_minutes=recipe_data.get('cooking_time_minutes'),
                total_time_minutes=recipe_data.get('total_time_minutes'),
                difficulty_level=recipe_data.get('difficulty_level'),
                yield_quantity=recipe_data.get('yield_quantity', 1),
                yield_unit=recipe_data.get('yield_unit'),
                serving_size=recipe_data.get('serving_size'),
                preparation_method=recipe_data.get('preparation_method'),
                cooking_instructions=recipe_data.get('cooking_instructions'),
                presentation_notes=recipe_data.get('presentation_notes'),
                calories_per_serving=recipe_data.get('calories_per_serving'),
                nutritional_info=recipe_data.get('nutritional_info', {}),
                allergens=recipe_data.get('allergens', []),
                is_active=recipe_data.get('is_active', True),
                is_standardized=recipe_data.get('is_standardized', False),
                version=recipe_data.get('version', '1.0'),
                last_revision_date=datetime.fromisoformat(recipe_data['last_revision_date']).date() if recipe_data.get('last_revision_date') else date.today(),
                revised_by=recipe_data.get('revised_by'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(recipe)
            db.session.flush()  # Get the ID
            
            # Create recipe items if provided
            if 'ingredients' in recipe_data:
                for ingredient_data in recipe_data['ingredients']:
                    recipe_item = RecipeItem(
                        recipe_id=recipe.id,
                        product_id=ingredient_data['product_id'],
                        quantity=ingredient_data['quantity'],
                        unit_of_measure=ingredient_data['unit_of_measure'],
                        preparation_method=ingredient_data.get('preparation_method'),
                        cooking_instruction=ingredient_data.get('cooking_instruction'),
                        can_be_substituted=ingredient_data.get('can_be_substituted', False),
                        substitution_options=ingredient_data.get('substitution_options', []),
                        quality_grade_required=ingredient_data.get('quality_grade_required'),
                        special_requirements=ingredient_data.get('special_requirements'),
                        tenant_id=self.tenant_id
                    )
                    db.session.add(recipe_item)
            
            # Calculate recipe cost
            recipe.calculate_cost()
            
            db.session.commit()
            return True, recipe, "Recipe created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating recipe: {e}")
            return False, None, str(e)
    
    def get_recipes(self, filters: Optional[Dict[str, Any]] = None) -> List[Recipe]:
        """Get recipes with optional filters"""
        try:
            query = Recipe.query.filter_by(tenant_id=self.tenant_id, is_active=True)
            
            if filters:
                if 'category' in filters:
                    query = query.filter(Recipe.category == filters['category'])
                if 'cuisine_type' in filters:
                    query = query.filter(Recipe.cuisine_type == filters['cuisine_type'])
                if 'difficulty_level' in filters:
                    query = query.filter(Recipe.difficulty_level == filters['difficulty_level'])
                if 'is_standardized' in filters:
                    query = query.filter(Recipe.is_standardized == filters['is_standardized'])
            
            return query.order_by(Recipe.name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting recipes: {e}")
            return []
    
    def get_recipe_by_code(self, recipe_code: str) -> Optional[Recipe]:
        """Get a recipe by code"""
        try:
            return Recipe.query.filter_by(
                recipe_code=recipe_code,
                tenant_id=self.tenant_id,
                is_active=True
            ).first()
        except Exception as e:
            current_app.logger.error(f"Error getting recipe by code: {e}")
            return None
    
    # Wastage Management Methods
    
    def create_wastage_record(self, wastage_data: Dict[str, Any], 
                             user_id: Optional[str] = None) -> Tuple[bool, Optional[FoodWastage], str]:
        """Create a new wastage record"""
        try:
            wastage = FoodWastage(
                product_id=wastage_data['product_id'],
                batch_id=wastage_data.get('batch_id'),
                wastage_date=datetime.fromisoformat(wastage_data['wastage_date']).date() if wastage_data.get('wastage_date') else date.today(),
                quantity=float(wastage_data['quantity']),
                unit_of_measure=wastage_data['unit_of_measure'],
                wastage_reason=wastage_data['wastage_reason'],
                wastage_category=wastage_data.get('wastage_category'),
                detailed_reason=wastage_data.get('detailed_reason'),
                unit_cost=Decimal(str(wastage_data.get('unit_cost', 0))),
                prevention_measures=wastage_data.get('prevention_measures'),
                is_preventable=wastage_data.get('is_preventable', True),
                reported_by=wastage_data.get('reported_by'),
                approved_by=wastage_data.get('approved_by'),
                is_documented=wastage_data.get('is_documented', False),
                is_analyzed=wastage_data.get('is_analyzed', False),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            # Calculate wastage cost
            wastage.calculate_cost()
            
            # Update batch quantity if batch is specified
            if wastage.batch_id:
                batch = FoodBatch.query.filter_by(
                    id=wastage.batch_id,
                    tenant_id=self.tenant_id
                ).first()
                
                if batch:
                    batch.current_quantity -= int(wastage.quantity)
                    if batch.current_quantity < 0:
                        batch.current_quantity = 0
            
            db.session.add(wastage)
            db.session.commit()
            return True, wastage, "Wastage record created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating wastage record: {e}")
            return False, None, str(e)
    
    def get_wastage_records(self, filters: Optional[Dict[str, Any]] = None) -> List[FoodWastage]:
        """Get wastage records with optional filters"""
        try:
            query = FoodWastage.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'product_id' in filters:
                    query = query.filter(FoodWastage.product_id == filters['product_id'])
                if 'batch_id' in filters:
                    query = query.filter(FoodWastage.batch_id == filters['batch_id'])
                if 'wastage_reason' in filters:
                    query = query.filter(FoodWastage.wastage_reason == filters['wastage_reason'])
                if 'wastage_category' in filters:
                    query = query.filter(FoodWastage.wastage_category == filters['wastage_category'])
                if 'start_date' in filters:
                    start_date = datetime.fromisoformat(filters['start_date']).date()
                    query = query.filter(FoodWastage.wastage_date >= start_date)
                if 'end_date' in filters:
                    end_date = datetime.fromisoformat(filters['end_date']).date()
                    query = query.filter(FoodWastage.wastage_date <= end_date)
            
            return query.order_by(FoodWastage.wastage_date.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting wastage records: {e}")
            return []
    
    # Weighing Scale Integration Methods
    
    def create_weighing_scale(self, scale_data: Dict[str, Any], 
                             user_id: Optional[str] = None) -> Tuple[bool, Optional[WeighingScaleIntegration], str]:
        """Create a new weighing scale integration"""
        try:
            weighing_scale = WeighingScaleIntegration(
                scale_id=scale_data['scale_id'],
                scale_name=scale_data['scale_name'],
                scale_model=scale_data.get('scale_model'),
                manufacturer=scale_data.get('manufacturer'),
                connection_type=scale_data['connection_type'],
                connection_parameters=scale_data.get('connection_parameters', {}),
                capacity_kg=scale_data.get('capacity_kg'),
                readability_g=scale_data.get('readability_g'),
                units_supported=scale_data.get('units_supported', []),
                last_calibration_date=datetime.fromisoformat(scale_data['last_calibration_date']).date() if scale_data.get('last_calibration_date') else None,
                calibration_frequency_days=scale_data.get('calibration_frequency_days', 30),
                next_calibration_date=datetime.fromisoformat(scale_data['next_calibration_date']).date() if scale_data.get('next_calibration_date') else None,
                calibration_certificate=scale_data.get('calibration_certificate'),
                is_active=scale_data.get('is_active', True),
                is_connected=scale_data.get('is_connected', False),
                last_connection_time=datetime.fromisoformat(scale_data['last_connection_time']) if scale_data.get('last_connection_time') else None,
                location=scale_data.get('location'),
                department=scale_data.get('department'),
                tenant_id=self.tenant_id,
                created_by=user_id
            )
            
            db.session.add(weighing_scale)
            db.session.commit()
            return True, weighing_scale, "Weighing scale created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating weighing scale: {e}")
            return False, None, str(e)
    
    def get_weighing_scales(self, filters: Optional[Dict[str, Any]] = None) -> List[WeighingScaleIntegration]:
        """Get weighing scales with optional filters"""
        try:
            query = WeighingScaleIntegration.query.filter_by(tenant_id=self.tenant_id)
            
            if filters:
                if 'connection_type' in filters:
                    query = query.filter(WeighingScaleIntegration.connection_type == filters['connection_type'])
                if 'location' in filters:
                    query = query.filter(WeighingScaleIntegration.location == filters['location'])
                if 'department' in filters:
                    query = query.filter(WeighingScaleIntegration.department == filters['department'])
                if 'is_active' in filters:
                    query = query.filter(WeighingScaleIntegration.is_active == filters['is_active'])
                if 'is_connected' in filters:
                    query = query.filter(WeighingScaleIntegration.is_connected == filters['is_connected'])
            
            return query.order_by(WeighingScaleIntegration.scale_name).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting weighing scales: {e}")
            return []
    
    # Analytics and Reporting Methods
    
    def get_expiry_report(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Get expiry report for products"""
        try:
            # Get products with expiry tracking
            products_with_expiry = FoodProduct.query.filter(
                FoodProduct.tenant_id == self.tenant_id,
                FoodProduct.is_active == True,
                FoodProduct.expiry_date_required == True
            ).all()
            
            expiry_report = []
            total_expired_value = Decimal('0.00')
            total_expiring_soon_value = Decimal('0.00')
            
            for product in products_with_expiry:
                expiry_status = product.get_expiry_status()
                
                if expiry_status['expired_quantity'] > 0 or expiry_status['expiring_soon_quantity'] > 0:
                    product_info = {
                        'product_id': product.id,
                        'product_name': product.name,
                        'sku': product.sku_base,
                        'category': product.food_category,
                        'expired_quantity': expiry_status['expired_quantity'],
                        'expiring_soon_quantity': expiry_status['expiring_soon_quantity'],
                        'unit_price': float(product.unit_price),
                        'expired_value': expiry_status['expired_quantity'] * float(product.unit_price),
                        'expiring_soon_value': expiry_status['expiring_soon_quantity'] * float(product.unit_price)
                    }
                    
                    expiry_report.append(product_info)
                    total_expired_value += Decimal(str(product_info['expired_value']))
                    total_expiring_soon_value += Decimal(str(product_info['expiring_soon_value']))
            
            return {
                'report_date': date.today().isoformat(),
                'days_ahead': days_ahead,
                'products_at_risk': expiry_report,
                'summary': {
                    'total_products_at_risk': len(expiry_report),
                    'total_expired_quantity': sum(p['expired_quantity'] for p in expiry_report),
                    'total_expiring_soon_quantity': sum(p['expiring_soon_quantity'] for p in expiry_report),
                    'total_expired_value': float(total_expired_value),
                    'total_expiring_soon_value': float(total_expiring_soon_value),
                    'total_financial_risk': float(total_expired_value + total_expiring_soon_value)
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating expiry report: {e}")
            return {}
    
    def get_wastage_analysis(self, start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get wastage analysis"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            # Get wastage records in date range
            wastage_records = FoodWastage.query.filter(
                FoodWastage.tenant_id == self.tenant_id,
                FoodWastage.wastage_date >= start_date,
                FoodWastage.wastage_date <= end_date
            ).all()
            
            # Group by reason
            wastage_by_reason = {}
            wastage_by_category = {}
            total_cost = Decimal('0.00')
            total_quantity = 0
            
            for record in wastage_records:
                # Group by reason
                reason = record.wastage_reason
                if reason not in wastage_by_reason:
                    wastage_by_reason[reason] = {
                        'quantity': 0,
                        'cost': Decimal('0.00'),
                        'count': 0
                    }
                
                wastage_by_reason[reason]['quantity'] += record.quantity
                wastage_by_reason[reason]['cost'] += record.total_cost or Decimal('0.00')
                wastage_by_reason[reason]['count'] += 1
                
                # Group by category
                category = record.wastage_category or 'Other'
                if category not in wastage_by_category:
                    wastage_by_category[category] = {
                        'quantity': 0,
                        'cost': Decimal('0.00'),
                        'count': 0
                    }
                
                wastage_by_category[category]['quantity'] += record.quantity
                wastage_by_category[category]['cost'] += record.total_cost or Decimal('0.00')
                wastage_by_category[category]['count'] += 1
                
                # Totals
                total_cost += record.total_cost or Decimal('0.00')
                total_quantity += record.quantity
            
            # Convert Decimal to float for JSON serialization
            for reason_data in wastage_by_reason.values():
                reason_data['cost'] = float(reason_data['cost'])
            
            for category_data in wastage_by_category.values():
                category_data['cost'] = float(category_data['cost'])
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_records': len(wastage_records),
                    'total_quantity': total_quantity,
                    'total_cost': float(total_cost)
                },
                'wastage_by_reason': wastage_by_reason,
                'wastage_by_category': wastage_by_category
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating wastage analysis: {e}")
            return {}
    
    def get_temperature_compliance_report(self, start_date: Optional[date] = None, 
                                        end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get temperature compliance report"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=7)
            if not end_date:
                end_date = date.today()
            
            # Get temperature logs in date range
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            temp_logs = TemperatureLog.query.filter(
                TemperatureLog.tenant_id == self.tenant_id,
                TemperatureLog.reading_time >= start_datetime,
                TemperatureLog.reading_time <= end_datetime
            ).all()
            
            # Analyze compliance
            total_readings = len(temp_logs)
            compliant_readings = sum(1 for log in temp_logs if log.is_within_range)
            non_compliant_readings = total_readings - compliant_readings
            
            compliance_percentage = (compliant_readings / total_readings * 100) if total_readings > 0 else 0
            
            # Group by location
            compliance_by_location = {}
            for log in temp_logs:
                location = log.reading_location or 'Unknown'
                if location not in compliance_by_location:
                    compliance_by_location[location] = {
                        'total': 0,
                        'compliant': 0,
                        'non_compliant': 0
                    }
                
                compliance_by_location[location]['total'] += 1
                if log.is_within_range:
                    compliance_by_location[location]['compliant'] += 1
                else:
                    compliance_by_location[location]['non_compliant'] += 1
            
            # Calculate percentages for each location
            for location_data in compliance_by_location.values():
                if location_data['total'] > 0:
                    location_data['compliance_percentage'] = (location_data['compliant'] / location_data['total'] * 100)
                else:
                    location_data['compliance_percentage'] = 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'summary': {
                    'total_readings': total_readings,
                    'compliant_readings': compliant_readings,
                    'non_compliant_readings': non_compliant_readings,
                    'compliance_percentage': round(compliance_percentage, 2)
                },
                'compliance_by_location': compliance_by_location
            }
            
        except Exception as e:
            current_app.logger.error(f"Error generating temperature compliance report: {e}")
            return {}


# Factory function for creating food service instances
def create_food_confectionery_service(tenant_id: Optional[str] = None) -> FoodConfectioneryService:
    """Create a food & confectionery service instance"""
    return FoodConfectioneryService(tenant_id)