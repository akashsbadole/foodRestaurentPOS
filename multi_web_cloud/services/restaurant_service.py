"""
Restaurant service layer with comprehensive business logic for restaurant operations
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from flask import current_app
from models import db, Table, Order, OrderItem, MenuItem, Category
from utils.feature_flag_manager import feature_manager


class RestaurantService:
    """Service layer for restaurant-specific operations"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        self.tenant_id = tenant_id
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a restaurant feature is enabled"""
        return feature_manager.is_enabled(feature_name, self.tenant_id)
    
    # Table Management Methods
    
    def get_available_tables(self, capacity: Optional[int] = None, location: Optional[str] = None) -> List[Table]:
        """Get available tables with optional filters"""
        query = Table.query.filter_by(is_active=True, status='Available')
        
        if capacity:
            query = query.filter(Table.capacity >= capacity)
        
        if location:
            query = query.filter(Table.location.ilike(f'%{location}%'))
        
        return query.order_by(Table.capacity, Table.table_number).all()
    
    def get_table_by_number(self, table_number: str) -> Optional[Table]:
        """Get table by number"""
        return Table.query.filter_by(table_number=table_number, is_active=True).first()
    
    def create_table(self, table_number: str, capacity: int, location: Optional[str] = None, 
                     description: Optional[str] = None) -> Tuple[bool, Optional[Table], str]:
        """Create a new table"""
        try:
            # Check if table number already exists
            if Table.query.filter_by(table_number=table_number).first():
                return False, None, "Table number already exists"
            
            table = Table(
                table_number=table_number,
                capacity=capacity,
                location=location,
                description=description
            )
            db.session.add(table)
            db.session.commit()
            
            return True, table, "Table created successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating table: {e}")
            return False, None, str(e)
    
    def update_table_status(self, table_id: int, new_status: str, 
                           user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Update table status with validation"""
        try:
            valid_statuses = ['Available', 'Occupied', 'Reserved', 'Maintenance']
            if new_status not in valid_statuses:
                return False, "Invalid status"
            
            table = Table.query.get(table_id)
            if not table:
                return False, "Table not found"
            
            old_status = table.status
            table.status = new_status
            table.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Log status change if audit feature is enabled
            if self.is_feature_enabled('FEATURE_AUDIT_LOG'):
                self._log_table_status_change(table, old_status, new_status, user_id)
            
            return True, f"Table status updated from {old_status} to {new_status}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating table status: {e}")
            return False, str(e)
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """Get comprehensive table statistics"""
        try:
            total_tables = Table.query.filter_by(is_active=True).count()
            
            status_counts = db.session.query(
                Table.status,
                db.func.count(Table.id)
            ).filter_by(is_active=True).group_by(Table.status).all()
            
            status_summary = dict(status_counts)
            
            # Calculate occupancy rate
            occupied_count = status_summary.get('Occupied', 0)
            occupancy_rate = (occupied_count / total_tables * 100) if total_tables > 0 else 0
            
            # Get capacity utilization
            occupied_tables = Table.query.filter_by(is_active=True, status='Occupied').all()
            total_capacity = sum(table.capacity for table in Table.query.filter_by(is_active=True).all())
            used_capacity = sum(table.capacity for table in occupied_tables)
            capacity_utilization = (used_capacity / total_capacity * 100) if total_capacity > 0 else 0
            
            return {
                'total_tables': total_tables,
                'status_summary': status_summary,
                'occupancy_rate': round(occupancy_rate, 2),
                'capacity_utilization': round(capacity_utilization, 2),
                'available_tables': status_summary.get('Available', 0),
                'occupied_tables': occupied_count,
                'reserved_tables': status_summary.get('Reserved', 0),
                'maintenance_tables': status_summary.get('Maintenance', 0)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting table statistics: {e}")
            return {}
    
    def suggest_tables(self, party_size: int, preferred_location: Optional[str] = None) -> List[Table]:
        """Suggest best tables for a party size"""
        try:
            # Get tables that can accommodate the party
            suitable_tables = Table.query.filter(
                Table.is_active == True,
                Table.status == 'Available',
                Table.capacity >= party_size
            )
            
            if preferred_location:
                suitable_tables = suitable_tables.filter(
                    Table.location.ilike(f'%{preferred_location}%')
                )
            
            suitable_tables = suitable_tables.order_by(Table.capacity.asc()).all()
            
            # Score tables based on fit (prefer tables that aren't oversized)
            scored_tables = []
            for table in suitable_tables:
                # Calculate efficiency score (lower is better)
                excess_capacity = table.capacity - party_size
                efficiency_score = excess_capacity if excess_capacity >= 0 else float('inf')
                
                scored_tables.append({
                    'table': table,
                    'score': efficiency_score,
                    'efficiency': 'Perfect' if excess_capacity == 0 else 'Good' if excess_capacity <= 2 else 'Large'
                })
            
            # Sort by efficiency score
            scored_tables.sort(key=lambda x: x['score'])
            
            return [item['table'] for item in scored_tables[:5]]  # Return top 5 suggestions
            
        except Exception as e:
            current_app.logger.error(f"Error suggesting tables: {e}")
            return []
    
    # KOT (Kitchen Order Ticket) Management Methods
    
    def get_active_kot_orders(self, station: Optional[str] = None) -> List[Order]:
        """Get active KOT orders with optional station filter"""
        try:
            query = Order.query.filter(
                Order.status.in_(['New', 'In Progress', 'Ready'])
            )
            
            # Filter by kitchen station if feature is enabled
            if station and self.is_feature_enabled('FEATURE_KITCHEN_STATIONS'):
                query = query.join(OrderItem).join(MenuItem).filter(
                    MenuItem.kitchen_station == station
                ).distinct()
            
            return query.order_by(Order.created_at.desc()).all()
            
        except Exception as e:
            current_app.logger.error(f"Error getting active KOT orders: {e}")
            return []
    
    def get_kot_order_details(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed KOT order information"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return None
            
            items = db.session.query(OrderItem, MenuItem).join(
                MenuItem, OrderItem.menu_item_id == MenuItem.id
            ).filter(OrderItem.order_id == order_id).all()
            
            # Group items by kitchen station if feature is enabled
            if self.is_feature_enabled('FEATURE_KITCHEN_STATIONS'):
                station_groups = {}
                for order_item, menu_item in items:
                    station = menu_item.kitchen_station or 'Main'
                    if station not in station_groups:
                        station_groups[station] = []
                    station_groups[station].append({
                        'order_item': order_item,
                        'menu_item': menu_item
                    })
            else:
                station_groups = {'Main': [{'order_item': oi, 'menu_item': mi} for oi, mi in items]}
            
            # Calculate order age and urgency
            order_age = datetime.utcnow() - order.created_at
            age_minutes = int(order_age.total_seconds() / 60)
            
            urgency = 'normal'
            if age_minutes > 20:
                urgency = 'high'
            elif age_minutes > 10:
                urgency = 'medium'
            
            return {
                'order': order,
                'items': items,
                'station_groups': station_groups,
                'age_minutes': age_minutes,
                'urgency': urgency,
                'table_number': order.table.table_number if order.table else None
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting KOT order details: {e}")
            return None
    
    def update_kot_item_status(self, item_id: int, status: str, 
                              user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Update KOT item status with validation"""
        try:
            valid_statuses = ['Pending', 'In Progress', 'Ready', 'Completed', 'Cancelled']
            if status not in valid_statuses:
                return False, "Invalid status"
            
            order_item = OrderItem.query.get(item_id)
            if not order_item:
                return False, "Order item not found"
            
            old_status = order_item.status
            order_item.status = status
            db.session.commit()
            
            # Log status change if audit feature is enabled
            if self.is_feature_enabled('FEATURE_AUDIT_LOG'):
                self._log_kot_item_status_change(order_item, old_status, status, user_id)
            
            # Check if all items in the order are ready/completed
            self._update_order_status_based_on_items(order_item.order_id)
            
            return True, f"Item status updated to {status}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating KOT item status: {e}")
            return False, str(e)
    
    def bulk_update_kot_items(self, item_ids: List[int], status: str, 
                             user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Bulk update multiple KOT items"""
        try:
            valid_statuses = ['Pending', 'In Progress', 'Ready', 'Completed', 'Cancelled']
            if status not in valid_statuses:
                return False, "Invalid status"
            
            updated_count = 0
            order_ids = set()
            
            for item_id in item_ids:
                order_item = OrderItem.query.get(item_id)
                if order_item:
                    old_status = order_item.status
                    order_item.status = status
                    updated_count += 1
                    order_ids.add(order_item.order_id)
                    
                    # Log status change if audit feature is enabled
                    if self.is_feature_enabled('FEATURE_AUDIT_LOG'):
                        self._log_kot_item_status_change(order_item, old_status, status, user_id)
            
            db.session.commit()
            
            # Update order statuses based on item changes
            for order_id in order_ids:
                self._update_order_status_based_on_items(order_id)
            
            return True, f"{updated_count} items updated to {status}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error bulk updating KOT items: {e}")
            return False, str(e)
    
    def get_kitchen_performance_metrics(self, start_date: Optional[datetime] = None, 
                                       end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get kitchen performance metrics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Get completed orders in the period
            completed_orders = Order.query.filter(
                Order.status == 'Completed',
                Order.created_at >= start_date,
                Order.created_at <= end_date
            ).all()
            
            # Calculate average preparation time
            total_prep_time = timedelta()
            order_count = 0
            
            for order in completed_orders:
                items = OrderItem.query.filter_by(order_id=order.id).all()
                for item in items:
                    if item.completed_at and item.created_at:
                        prep_time = item.completed_at - item.created_at
                        total_prep_time += prep_time
                        order_count += 1
            
            avg_prep_time = (total_prep_time / order_count).total_seconds() / 60 if order_count > 0 else 0
            
            # Get item status distribution
            status_counts = db.session.query(
                OrderItem.status,
                db.func.count(OrderItem.id)
            ).join(Order).filter(
                Order.created_at >= start_date,
                Order.created_at <= end_date
            ).group_by(OrderItem.status).all()
            
            status_summary = dict(status_counts)
            
            # Calculate kitchen efficiency
            total_items = sum(status_summary.values())
            completed_items = status_summary.get('Completed', 0)
            efficiency = (completed_items / total_items * 100) if total_items > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_orders': len(completed_orders),
                'total_items': total_items,
                'average_prep_time_minutes': round(avg_prep_time, 2),
                'efficiency_percentage': round(efficiency, 2),
                'status_distribution': status_summary,
                'completed_items': completed_items
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting kitchen performance metrics: {e}")
            return {}
    
    # Restaurant Configuration Methods
    
    def get_restaurant_config(self) -> Dict[str, Any]:
        """Get restaurant-specific configuration"""
        try:
            from models.settings import Settings
            
            settings = Settings.get_all_as_dict()
            
            config = {
                'table_management': {
                    'auto_assign_tables': settings.get('AUTO_ASSIGN_TABLES', False),
                    'allow_table_merging': settings.get('ALLOW_TABLE_MERGING', False),
                    'table_reservation_minutes': settings.get('TABLE_RESERVATION_MINUTES', 30)
                },
                'kot_settings': {
                    'auto_print_kot': settings.get('AUTO_PRINT_KOT', True),
                    'kot_duplicate_copies': settings.get('KOT_DUPLICATE_COPIES', 1),
                    'show_item_modifications': settings.get('SHOW_ITEM_MODIFICATIONS', True),
                    'kitchen_display_refresh_seconds': settings.get('KITCHEN_DISPLAY_REFRESH', 30)
                },
                'order_management': {
                    'auto_complete_ready_orders': settings.get('AUTO_COMPLETE_READY_ORDERS', False),
                    'allow_order_modifications': settings.get('ALLOW_ORDER_MODIFICATIONS', True),
                    'require_order_confirmation': settings.get('REQUIRE_ORDER_CONFIRMATION', False)
                }
            }
            
            # Add feature-specific configuration
            if self.is_feature_enabled('FEATURE_KITCHEN_STATIONS'):
                config['kitchen_stations'] = self._get_kitchen_stations()
            
            if self.is_feature_enabled('FEATURE_TABLE_RESERVATIONS'):
                config['reservations'] = self._get_reservation_config()
            
            return config
            
        except Exception as e:
            current_app.logger.error(f"Error getting restaurant config: {e}")
            return {}
    
    def update_restaurant_config(self, config_updates: Dict[str, Any], 
                                user_id: Optional[str] = None) -> Tuple[bool, str]:
        """Update restaurant configuration"""
        try:
            from models.settings import Settings
            
            for section, settings in config_updates.items():
                for key, value in settings.items():
                    Settings.set(key, value)
            
            # Log configuration change if audit feature is enabled
            if self.is_feature_enabled('FEATURE_AUDIT_LOG'):
                self._log_config_change(config_updates, user_id)
            
            return True, "Restaurant configuration updated successfully"
            
        except Exception as e:
            current_app.logger.error(f"Error updating restaurant config: {e}")
            return False, str(e)
    
    # Private Helper Methods
    
    def _log_table_status_change(self, table: Table, old_status: str, new_status: str, 
                                user_id: Optional[str] = None):
        """Log table status change for audit"""
        try:
            from models.feature_flag import FeatureFlagAuditLog
            
            audit_log = FeatureFlagAuditLog(
                tenant_id=self.tenant_id or 'default',
                feature_name='TABLE_STATUS_CHANGE',
                action='updated',
                old_value={'table_id': table.id, 'old_status': old_status},
                new_value={'table_id': table.id, 'new_status': new_status},
                changed_by=user_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error logging table status change: {e}")
    
    def _log_kot_item_status_change(self, order_item: OrderItem, old_status: str, 
                                  new_status: str, user_id: Optional[str] = None):
        """Log KOT item status change for audit"""
        try:
            from models.feature_flag import FeatureFlagAuditLog
            
            audit_log = FeatureFlagAuditLog(
                tenant_id=self.tenant_id or 'default',
                feature_name='KOT_ITEM_STATUS_CHANGE',
                action='updated',
                old_value={
                    'order_item_id': order_item.id,
                    'order_id': order_item.order_id,
                    'old_status': old_status
                },
                new_value={
                    'order_item_id': order_item.id,
                    'order_id': order_item.order_id,
                    'new_status': new_status
                },
                changed_by=user_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error logging KOT item status change: {e}")
    
    def _log_config_change(self, config_updates: Dict[str, Any], user_id: Optional[str] = None):
        """Log configuration change for audit"""
        try:
            from models.feature_flag import FeatureFlagAuditLog
            
            audit_log = FeatureFlagAuditLog(
                tenant_id=self.tenant_id or 'default',
                feature_name='RESTAURANT_CONFIG_CHANGE',
                action='updated',
                old_value={},
                new_value=config_updates,
                changed_by=user_id
            )
            db.session.add(audit_log)
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error logging config change: {e}")
    
    def _update_order_status_based_on_items(self, order_id: int):
        """Update order status based on item statuses"""
        try:
            order = Order.query.get(order_id)
            if not order:
                return
            
            items = OrderItem.query.filter_by(order_id=order_id).all()
            
            if not items:
                return
            
            # Count items by status
            status_counts = {}
            for item in items:
                status_counts[item.status] = status_counts.get(item.status, 0) + 1
            
            # Determine order status based on item statuses
            if status_counts.get('Completed', 0) == len(items):
                order.status = 'Ready'
            elif status_counts.get('In Progress', 0) > 0:
                order.status = 'In Progress'
            elif status_counts.get('Cancelled', 0) == len(items):
                order.status = 'Cancelled'
            
            db.session.commit()
            
        except Exception as e:
            current_app.logger.error(f"Error updating order status: {e}")
    
    def _get_kitchen_stations(self) -> List[Dict[str, Any]]:
        """Get kitchen stations configuration"""
        try:
            stations = db.session.query(
                MenuItem.kitchen_station,
                db.func.count(MenuItem.id)
            ).filter(
                MenuItem.kitchen_station.isnot(None),
                MenuItem.kitchen_station != ''
            ).group_by(MenuItem.kitchen_station).all()
            
            return [
                {
                    'name': station,
                    'item_count': count,
                    'display_name': station.replace('_', ' ').title()
                }
                for station, count in stations
            ]
            
        except Exception as e:
            current_app.logger.error(f"Error getting kitchen stations: {e}")
            return []
    
    def _get_reservation_config(self) -> Dict[str, Any]:
        """Get reservation configuration"""
        try:
            from models.settings import Settings
            
            return {
                'advance_booking_days': Settings.get('RESERVATION_ADVANCE_DAYS', 30),
                'min_reservation_duration': Settings.get('MIN_RESERVATION_DURATION', 30),
                'max_reservation_duration': Settings.get('MAX_RESERVATION_DURATION', 240),
                'require_deposit': Settings.get('RESERVATION_REQUIRE_DEPOSIT', False),
                'deposit_amount': Settings.get('RESERVATION_DEPOSIT_AMOUNT', 0),
                'auto_cancel_minutes': Settings.get('RESERVATION_AUTO_CANCEL_MINUTES', 15)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting reservation config: {e}")
            return {}


# Factory function for creating restaurant service instances
def create_restaurant_service(tenant_id: Optional[str] = None) -> RestaurantService:
    """Create a restaurant service instance"""
    return RestaurantService(tenant_id)