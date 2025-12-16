"""
Payment & Settlement service layer for handling enhanced payment methods, 
wallet payments, EMI options, denomination counting, cash management, 
split payments, and settlement processing.
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import joinedload, selectinload
from models import db
from models.payment_settlement import (
    PaymentMethod, WalletPayment, EMIPayment, DenominationCount,
    SplitPayment, SettlementRecord, SettlementItem, CashManagement
)
from utils.tenant_query_manager import tenant_scoped


class PaymentSettlementService:
    """Service class for payment and settlement operations"""
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
    
    # Payment Method Management
    
    def get_payment_methods(self, filters: Optional[Dict] = None) -> List[PaymentMethod]:
        """Get payment methods with optional filters"""
        query = PaymentMethod.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'method_type' in filters:
                query = query.filter(PaymentMethod.method_type == filters['method_type'])
            if 'is_active' in filters:
                query = query.filter(PaymentMethod.is_active == filters['is_active'])
            if 'is_default' in filters:
                query = query.filter(PaymentMethod.is_default == filters['is_default'])
            if 'requires_approval' in filters:
                query = query.filter(PaymentMethod.requires_approval == filters['requires_approval'])
            if 'allows_partial' in filters:
                query = query.filter(PaymentMethod.allows_partial == filters['allows_partial'])
            if 'settlement_cycle' in filters:
                query = query.filter(PaymentMethod.settlement_cycle == filters['settlement_cycle'])
        
        return query.order_by(PaymentMethod.display_order, PaymentMethod.method_name).all()
    
    def get_payment_method_by_id(self, method_id: int) -> Optional[PaymentMethod]:
        """Get payment method by ID"""
        return PaymentMethod.query.filter_by(id=method_id, tenant_id=self.tenant_id).first()
    
    def get_default_payment_method(self) -> Optional[PaymentMethod]:
        """Get default payment method"""
        return PaymentMethod.query.filter_by(
            tenant_id=self.tenant_id, 
            is_default=True, 
            is_active=True
        ).first()
    
    def create_payment_method(self, data: Dict) -> Tuple[bool, Optional[PaymentMethod], str]:
        """Create a new payment method"""
        try:
            # Check if method name already exists
            existing = PaymentMethod.query.filter_by(
                method_name=data['method_name'], 
                tenant_id=self.tenant_id
            ).first()
            if existing:
                return False, None, f"Payment method {data['method_name']} already exists"
            
            # If setting as default, unset other defaults
            if data.get('is_default', False):
                PaymentMethod.query.filter_by(
                    tenant_id=self.tenant_id, 
                    is_default=True
                ).update({'is_default': False})
            
            payment_method = PaymentMethod(
                tenant_id=self.tenant_id,
                method_name=data['method_name'],
                method_type=data['method_type'],
                display_name=data.get('display_name'),
                description=data.get('description'),
                is_active=data.get('is_active', True),
                is_default=data.get('is_default', False),
                requires_approval=data.get('requires_approval', False),
                allows_partial=data.get('allows_partial', True),
                max_transaction_amount=Decimal(str(data['max_transaction_amount'])) if data.get('max_transaction_amount') else None,
                min_transaction_amount=Decimal(str(data['min_transaction_amount'])) if data.get('min_transaction_amount') else None,
                transaction_fee_type=data.get('transaction_fee_type'),
                transaction_fee_amount=Decimal(str(data['transaction_fee_amount'])) if data.get('transaction_fee_amount') else None,
                transaction_fee_percentage=Decimal(str(data['transaction_fee_percentage'])) if data.get('transaction_fee_percentage') else None,
                settlement_cycle=data.get('settlement_cycle'),
                settlement_delay_days=data.get('settlement_delay_days', 0),
                auto_settle=data.get('auto_settle', True),
                provider_name=data.get('provider_name'),
                provider_config=data.get('provider_config'),
                supported_currencies=data.get('supported_currencies'),
                icon_url=data.get('icon_url'),
                button_color=data.get('button_color'),
                display_order=data.get('display_order', 0),
                show_on_receipt=data.get('show_on_receipt', True),
                created_by=data.get('created_by')
            )
            
            db.session.add(payment_method)
            db.session.commit()
            return True, payment_method, "Payment method created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating payment method: {str(e)}"
    
    def update_payment_method(self, method_id: int, data: Dict) -> Tuple[bool, Optional[PaymentMethod], str]:
        """Update an existing payment method"""
        try:
            payment_method = PaymentMethod.query.filter_by(id=method_id, tenant_id=self.tenant_id).first()
            if not payment_method:
                return False, None, "Payment method not found"
            
            # If setting as default, unset other defaults
            if data.get('is_default', False) and not payment_method.is_default:
                PaymentMethod.query.filter_by(
                    tenant_id=self.tenant_id, 
                    is_default=True
                ).update({'is_default': False})
            
            # Update fields
            for field, value in data.items():
                if hasattr(payment_method, field) and field not in ['id', 'tenant_id', 'created_at', 'created_by']:
                    if field in ['max_transaction_amount', 'min_transaction_amount', 'transaction_fee_amount', 'transaction_fee_percentage'] and value is not None:
                        setattr(payment_method, field, Decimal(str(value)))
                    else:
                        setattr(payment_method, field, value)
            
            payment_method.updated_at = datetime.utcnow()
            db.session.commit()
            return True, payment_method, "Payment method updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error updating payment method: {str(e)}"
    
    # Wallet Payment Management
    
    def get_wallet_payments(self, filters: Optional[Dict] = None) -> List[WalletPayment]:
        """Get wallet payments with optional filters"""
        query = WalletPayment.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'wallet_id' in filters:
                query = query.filter(WalletPayment.wallet_id == filters['wallet_id'])
            if 'customer_id' in filters:
                query = query.filter(WalletPayment.customer_id == filters['customer_id'])
            if 'payment_method_id' in filters:
                query = query.filter(WalletPayment.payment_method_id == filters['payment_method_id'])
            if 'transaction_type' in filters:
                query = query.filter(WalletPayment.transaction_type == filters['transaction_type'])
            if 'status' in filters:
                query = query.filter(WalletPayment.status == filters['status'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(WalletPayment.created_at >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                query = query.filter(WalletPayment.created_at <= end_date)
        
        return query.order_by(desc(WalletPayment.created_at)).all()
    
    def get_wallet_payment_by_id(self, payment_id: int) -> Optional[WalletPayment]:
        """Get wallet payment by ID"""
        return WalletPayment.query.options(
            joinedload(WalletPayment.customer),
            joinedload(WalletPayment.payment_method)
        ).filter_by(id=payment_id, tenant_id=self.tenant_id).first()
    
    def get_wallet_balance(self, wallet_id: str) -> Dict:
        """Get current wallet balance"""
        latest_transaction = WalletPayment.query.filter_by(
            wallet_id=wallet_id, 
            tenant_id=self.tenant_id,
            status='completed'
        ).order_by(desc(WalletPayment.created_at)).first()
        
        return {
            'wallet_id': wallet_id,
            'current_balance': float(latest_transaction.balance_after) if latest_transaction and latest_transaction.balance_after else 0,
            'last_updated': latest_transaction.created_at.isoformat() if latest_transaction else None
        }
    
    def create_wallet_payment(self, data: Dict) -> Tuple[bool, Optional[WalletPayment], str]:
        """Create a new wallet payment"""
        try:
            # Generate transaction ID
            transaction_id = self._generate_wallet_transaction_id()
            
            # Get current balance
            current_balance = 0
            if data['wallet_id']:
                balance_info = self.get_wallet_balance(data['wallet_id'])
                current_balance = balance_info['current_balance']
            
            # Calculate new balance
            amount = Decimal(str(data['amount']))
            transaction_type = data.get('transaction_type', 'payment')
            
            if transaction_type == 'payment':
                new_balance = current_balance - amount
            elif transaction_type == 'refund':
                new_balance = current_balance + amount
            elif transaction_type == 'topup':
                new_balance = current_balance + amount
            else:
                new_balance = current_balance
            
            wallet_payment = WalletPayment(
                tenant_id=self.tenant_id,
                wallet_id=data['wallet_id'],
                customer_id=data.get('customer_id'),
                payment_method_id=data.get('payment_method_id'),
                transaction_id=transaction_id,
                transaction_type=transaction_type,
                amount=amount,
                currency=data.get('currency', 'USD'),
                balance_before=Decimal(str(current_balance)),
                balance_after=new_balance,
                status=data.get('status', 'pending'),
                authorization_code=data.get('authorization_code'),
                reference_number=data.get('reference_number'),
                processed_at=datetime.strptime(data['processed_at'], '%Y-%m-%d %H:%M:%S') if data.get('processed_at') else None,
                failure_reason=data.get('failure_reason'),
                retry_count=data.get('retry_count', 0),
                created_by=data.get('created_by')
            )
            
            db.session.add(wallet_payment)
            db.session.commit()
            return True, wallet_payment, "Wallet payment created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating wallet payment: {str(e)}"
    
    def process_wallet_payment(self, payment_id: int, status: str, processed_at: Optional[datetime] = None, failure_reason: Optional[str] = None) -> Tuple[bool, str]:
        """Process a wallet payment (approve/reject)"""
        try:
            wallet_payment = WalletPayment.query.filter_by(id=payment_id, tenant_id=self.tenant_id).first()
            if not wallet_payment:
                return False, "Wallet payment not found"
            
            wallet_payment.status = status
            wallet_payment.processed_at = processed_at or datetime.utcnow()
            
            if status == 'failed' and failure_reason:
                wallet_payment.failure_reason = failure_reason
                wallet_payment.retry_count = (wallet_payment.retry_count or 0) + 1
            elif status == 'completed':
                # Update wallet balance if this was a pending transaction
                if wallet_payment.transaction_type in ['payment', 'refund', 'topup']:
                    # Update related wallet balances for all subsequent transactions
                    subsequent_payments = WalletPayment.query.filter(
                        WalletPayment.wallet_id == wallet_payment.wallet_id,
                        WalletPayment.created_at > wallet_payment.created_at,
                        WalletPayment.status == 'completed'
                    ).all()
                    
                    for payment in subsequent_payments:
                        payment.balance_after = wallet_payment.balance_after
                    db.session.bulk_save_objects(subsequent_payments)
            
            db.session.commit()
            return True, f"Wallet payment {status} successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing wallet payment: {str(e)}"
    
    # EMI Payment Management
    
    def get_emi_payments(self, filters: Optional[Dict] = None) -> List[EMIPayment]:
        """Get EMI payments with optional filters"""
        query = EMIPayment.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'emi_plan_id' in filters:
                query = query.filter(EMIPayment.emi_plan_id == filters['emi_plan_id'])
            if 'customer_id' in filters:
                query = query.filter(EMIPayment.customer_id == filters['customer_id'])
            if 'payment_method_id' in filters:
                query = query.filter(EMIPayment.payment_method_id == filters['payment_method_id'])
            if 'order_id' in filters:
                query = query.filter(EMIPayment.order_id == filters['order_id'])
            if 'status' in filters:
                query = query.filter(EMIPayment.status == filters['status'])
            if 'overdue' in filters and filters['overdue']:
                query = query.filter(
                    and_(
                        EMIPayment.due_date < date.today(),
                        EMIPayment.status.notin_(['paid', 'cancelled'])
                    )
                )
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(EMIPayment.due_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(EMIPayment.due_date <= end_date)
        
        return query.order_by(EMIPayment.due_date).all()
    
    def get_emi_payment_by_id(self, payment_id: int) -> Optional[EMIPayment]:
        """Get EMI payment by ID"""
        return EMIPayment.query.options(
            joinedload(EMIPayment.customer),
            joinedload(EMIPayment.payment_method),
            joinedload(EMIPayment.order)
        ).filter_by(id=payment_id, tenant_id=self.tenant_id).first()
    
    def create_emi_plan(self, data: Dict) -> Tuple[bool, List[EMIPayment], str]:
        """Create a new EMI plan with all installments"""
        try:
            # Generate EMI plan ID
            emi_plan_id = self._generate_emi_plan_id()
            
            # Calculate EMI details
            principal_amount = Decimal(str(data['principal_amount']))
            interest_rate = Decimal(str(data.get('interest_rate', 0)))
            tenure_months = int(data['tenure_months'])
            
            # Calculate monthly installment using simple interest
            total_interest = principal_amount * interest_rate / 100 * tenure_months / 12
            total_amount = principal_amount + total_interest
            monthly_installment = total_amount / tenure_months
            
            # Create installments
            installments = []
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            
            for month in range(1, tenure_months + 1):
                due_date = start_date.replace(day=1) + timedelta(days=32 * month)
                # Adjust to last day of month if needed
                while due_date.month != ((start_date.replace(day=1) + timedelta(days=32 * month)).month):
                    due_date -= timedelta(days=1)
                
                installment = EMIPayment(
                    tenant_id=self.tenant_id,
                    emi_plan_id=emi_plan_id,
                    customer_id=data.get('customer_id'),
                    payment_method_id=data.get('payment_method_id'),
                    order_id=data.get('order_id'),
                    principal_amount=principal_amount,
                    interest_rate=interest_rate,
                    tenure_months=tenure_months,
                    monthly_installment=monthly_installment,
                    total_interest=total_interest,
                    total_amount=total_amount,
                    installment_number=month,
                    due_date=due_date,
                    status='pending',
                    auto_debit_enabled=data.get('auto_debit_enabled', False),
                    created_by=data.get('created_by')
                )
                
                installments.append(installment)
            
            # Bulk insert
            db.session.add_all(installments)
            db.session.commit()
            return True, installments, f"EMI plan created with {tenure_months} installments"
            
        except Exception as e:
            db.session.rollback()
            return False, [], f"Error creating EMI plan: {str(e)}"
    
    def pay_emi_installment(self, payment_id: int, payment_data: Dict) -> Tuple[bool, str]:
        """Pay an EMI installment"""
        try:
            emi_payment = EMIPayment.query.filter_by(id=payment_id, tenant_id=self.tenant_id).first()
            if not emi_payment:
                return False, "EMI payment not found"
            
            if emi_payment.status == 'paid':
                return False, "EMI installment already paid"
            
            # Update payment details
            emi_payment.paid_amount = Decimal(str(payment_data['paid_amount']))
            emi_payment.paid_date = datetime.strptime(payment_data['paid_date'], '%Y-%m-%d').date()
            emi_payment.status = 'paid'
            emi_payment.transaction_id = payment_data.get('transaction_id')
            emi_payment.payment_reference = payment_data.get('payment_reference')
            
            # Calculate late fees if applicable
            if emi_payment.due_date < emi_payment.paid_date:
                days_late = (emi_payment.paid_date - emi_payment.due_date).days
                # Apply late fee calculation (could be configurable)
                late_fee_rate = Decimal('0.02')  # 2% of installment
                emi_payment.late_fee = emi_payment.monthly_installment * late_fee_rate * days_late / 30
            
            db.session.commit()
            return True, "EMI installment paid successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error paying EMI installment: {str(e)}"
    
    # Denomination Count Management
    
    def get_denomination_counts(self, filters: Optional[Dict] = None) -> List[DenominationCount]:
        """Get denomination counts with optional filters"""
        query = DenominationCount.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'cash_drawer_id' in filters:
                query = query.filter(DenominationCount.cash_drawer_id == filters['cash_drawer_id'])
            if 'user_id' in filters:
                query = query.filter(DenominationCount.user_id == filters['user_id'])
            if 'shift_id' in filters:
                query = query.filter(DenominationCount.shift_id == filters['shift_id'])
            if 'currency' in filters:
                query = query.filter(DenominationCount.currency == filters['currency'])
            if 'denomination_type' in filters:
                query = query.filter(DenominationCount.denomination_type == filters['denomination_type'])
            if 'count_type' in filters:
                query = query.filter(DenominationCount.count_type == filters['count_type'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(DenominationCount.count_time >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                query = query.filter(DenominationCount.count_time <= end_date)
        
        return query.order_by(DenominationCount.denomination_value.desc()).all()
    
    def create_denomination_count(self, data: Dict) -> Tuple[bool, Optional[DenominationCount], str]:
        """Create a new denomination count"""
        try:
            count = DenominationCount(
                tenant_id=self.tenant_id,
                cash_drawer_id=data.get('cash_drawer_id'),
                user_id=data.get('user_id'),
                shift_id=data.get('shift_id'),
                currency=data.get('currency', 'USD'),
                denomination_value=Decimal(str(data['denomination_value'])),
                denomination_type=data.get('denomination_type'),
                count=data['count'],
                total_value=Decimal(str(data['denomination_value'])) * int(data['count']),
                count_type=data.get('count_type', 'opening'),
                count_time=datetime.strptime(data['count_time'], '%Y-%m-%d %H:%M:%S') if data.get('count_time') else datetime.utcnow(),
                verified_by=data.get('verified_by'),
                verification_notes=data.get('verification_notes'),
                expected_count=data.get('expected_count'),
                created_by=data.get('created_by')
            )
            
            # Calculate variance if expected count provided
            count.calculate_variance()
            
            db.session.add(count)
            db.session.commit()
            return True, count, "Denomination count created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating denomination count: {str(e)}"
    
    def verify_denomination_count(self, count_id: int, verification_data: Dict) -> Tuple[bool, str]:
        """Verify a denomination count"""
        try:
            count = DenominationCount.query.filter_by(id=count_id, tenant_id=self.tenant_id).first()
            if not count:
                return False, "Denomination count not found"
            
            count.verified_by = verification_data.get('verified_by')
            count.verification_notes = verification_data.get('verification_notes')
            count.expected_count = verification_data.get('expected_count')
            
            # Recalculate variance
            count.calculate_variance()
            
            db.session.commit()
            return True, "Denomination count verified successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error verifying denomination count: {str(e)}"
    
    def calculate_total_by_currency(self, currency: str, count_type: Optional[str] = None) -> Dict:
        """Calculate total cash by currency and optionally by count type"""
        query = DenominationCount.query.filter_by(
            tenant_id=self.tenant_id,
            currency=currency
        )
        
        if count_type:
            query = query.filter(DenominationCount.count_type == count_type)
        
        results = query.with_entities(
            DenominationCount.denomination_value,
            func.sum(DenominationCount.count).label('total_count'),
            func.sum(DenominationCount.total_value).label('total_value')
        ).group_by(DenominationCount.denomination_value).all()
        
        return {
            'currency': currency,
            'count_type': count_type,
            'denominations': [
                {
                    'denomination_value': float(result.denomination_value),
                    'total_count': result.total_count or 0,
                    'total_value': float(result.total_value or 0)
                }
                for result in results
            ],
            'grand_total': sum(float(result.total_value or 0) for result in results)
        }
    
    # Split Payment Management
    
    def get_split_payments(self, filters: Optional[Dict] = None) -> List[SplitPayment]:
        """Get split payments with optional filters"""
        query = SplitPayment.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'order_id' in filters:
                query = query.filter(SplitPayment.order_id == filters['order_id'])
            if 'payment_method_id' in filters:
                query = query.filter(SplitPayment.payment_method_id == filters['payment_method_id'])
            if 'status' in filters:
                query = query.filter(SplitPayment.status == filters['status'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(SplitPayment.created_at >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                query = query.filter(SplitPayment.created_at <= end_date)
        
        return query.order_by(SplitPayment.order_id, SplitPayment.sequence_number).all()
    
    def create_split_payment(self, data: Dict) -> Tuple[bool, Optional[SplitPayment], str]:
        """Create a new split payment"""
        try:
            split_payment = SplitPayment(
                tenant_id=self.tenant_id,
                order_id=data['order_id'],
                payment_method_id=data['payment_method_id'],
                amount=Decimal(str(data['amount'])),
                currency=data.get('currency', 'USD'),
                sequence_number=data.get('sequence_number', 1),
                transaction_id=data.get('transaction_id'),
                authorization_code=data.get('authorization_code'),
                reference_number=data.get('reference_number'),
                status=data.get('status', 'pending'),
                processed_at=datetime.strptime(data['processed_at'], '%Y-%m-%d %H:%M:%S') if data.get('processed_at') else None,
                failure_reason=data.get('failure_reason'),
                created_by=data.get('created_by')
            )
            
            db.session.add(split_payment)
            db.session.commit()
            return True, split_payment, "Split payment created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating split payment: {str(e)}"
    
    def process_split_payment(self, payment_id: int, status: str, processed_at: Optional[datetime] = None, failure_reason: Optional[str] = None) -> Tuple[bool, str]:
        """Process a split payment"""
        try:
            split_payment = SplitPayment.query.filter_by(id=payment_id, tenant_id=self.tenant_id).first()
            if not split_payment:
                return False, "Split payment not found"
            
            split_payment.status = status
            split_payment.processed_at = processed_at or datetime.utcnow()
            
            if status == 'failed' and failure_reason:
                split_payment.failure_reason = failure_reason
            
            db.session.commit()
            return True, f"Split payment {status} successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error processing split payment: {str(e)}"
    
    # Settlement Management
    
    def get_settlement_records(self, filters: Optional[Dict] = None) -> List[SettlementRecord]:
        """Get settlement records with optional filters"""
        query = SettlementRecord.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'payment_method_id' in filters:
                query = query.filter(SettlementRecord.payment_method_id == filters['payment_method_id'])
            if 'status' in filters:
                query = query.filter(SettlementRecord.status == filters['status'])
            if 'reconciled' in filters:
                query = query.filter(SettlementRecord.reconciled == filters['reconciled'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                query = query.filter(SettlementRecord.settlement_start_date >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                query = query.filter(SettlementRecord.settlement_end_date <= end_date)
        
        return query.order_by(desc(SettlementRecord.settlement_date)).all()
    
    def create_settlement_record(self, data: Dict) -> Tuple[bool, Optional[SettlementRecord], str]:
        """Create a new settlement record"""
        try:
            # Generate settlement ID
            settlement_id = self._generate_settlement_id()
            
            settlement = SettlementRecord(
                tenant_id=self.tenant_id,
                settlement_id=settlement_id,
                payment_method_id=data['payment_method_id'],
                settlement_start_date=datetime.strptime(data['settlement_start_date'], '%Y-%m-%d').date(),
                settlement_end_date=datetime.strptime(data['settlement_end_date'], '%Y-%m-%d').date(),
                settlement_date=datetime.strptime(data['settlement_date'], '%Y-%m-%d %H:%M:%S'),
                transaction_count=data.get('transaction_count', 0),
                gross_amount=Decimal(str(data['gross_amount'])),
                total_fees=Decimal(str(data['total_fees'])),
                net_amount=Decimal(str(data['net_amount'])),
                successful_transactions=data.get('successful_transactions', 0),
                failed_transactions=data.get('failed_transactions', 0),
                refunded_transactions=data.get('refunded_transactions', 0),
                chargeback_transactions=data.get('chargeback_transactions', 0),
                currency=data.get('currency', 'USD'),
                exchange_rate=Decimal(str(data['exchange_rate'])) if data.get('exchange_rate') else None,
                processor_reference=data.get('processor_reference'),
                processor_response=data.get('processor_response'),
                batch_id=data.get('batch_id'),
                status=data.get('status', 'pending'),
                initiated_at=datetime.strptime(data['initiated_at'], '%Y-%m-%d %H:%M:%S') if data.get('initiated_at') else datetime.utcnow(),
                completed_at=datetime.strptime(data['completed_at'], '%Y-%m-%d %H:%M:%S') if data.get('completed_at') else None,
                failure_reason=data.get('failure_reason'),
                created_by=data.get('created_by')
            )
            
            db.session.add(settlement)
            db.session.commit()
            return True, settlement, "Settlement record created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating settlement record: {str(e)}"
    
    def reconcile_settlement(self, settlement_id: int, reconciliation_data: Dict) -> Tuple[bool, str]:
        """Reconcile a settlement record"""
        try:
            settlement = SettlementRecord.query.filter_by(id=settlement_id, tenant_id=self.tenant_id).first()
            if not settlement:
                return False, "Settlement record not found"
            
            settlement.reconciled = True
            settlement.reconciled_by = reconciliation_data.get('reconciled_by')
            settlement.reconciled_at = datetime.utcnow()
            settlement.reconciliation_notes = reconciliation_data.get('reconciliation_notes')
            
            db.session.commit()
            return True, "Settlement reconciled successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error reconciling settlement: {str(e)}"
    
    # Cash Management
    
    def get_cash_management_records(self, filters: Optional[Dict] = None) -> List[CashManagement]:
        """Get cash management records with optional filters"""
        query = CashManagement.query.filter_by(tenant_id=self.tenant_id)
        
        if filters:
            if 'cash_drawer_id' in filters:
                query = query.filter(CashManagement.cash_drawer_id == filters['cash_drawer_id'])
            if 'user_id' in filters:
                query = query.filter(CashManagement.user_id == filters['user_id'])
            if 'shift_id' in filters:
                query = query.filter(CashManagement.shift_id == filters['shift_id'])
            if 'status' in filters:
                query = query.filter(CashManagement.status == filters['status'])
            if 'session_type' in filters:
                query = query.filter(CashManagement.session_type == filters['session_type'])
            if 'start_date' in filters:
                start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d')
                query = query.filter(CashManagement.session_start >= start_date)
            if 'end_date' in filters:
                end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d')
                query = query.filter(CashManagement.session_start <= end_date)
        
        return query.order_by(desc(CashManagement.session_start)).all()
    
    def create_cash_management_session(self, data: Dict) -> Tuple[bool, Optional[CashManagement], str]:
        """Create a new cash management session"""
        try:
            session = CashManagement(
                tenant_id=self.tenant_id,
                cash_drawer_id=data['cash_drawer_id'],
                user_id=data['user_id'],
                shift_id=data.get('shift_id'),
                opening_balance=Decimal(str(data['opening_balance'])),
                cash_sales=Decimal(str(data.get('cash_sales', 0))),
                cash_received=Decimal(str(data.get('cash_received', 0))),
                cash_paid_out=Decimal(str(data.get('cash_paid_out', 0))),
                closing_balance=Decimal(str(data.get('closing_balance', 0))),
                session_start=datetime.strptime(data['session_start'], '%Y-%m-%d %H:%M:%S'),
                session_end=datetime.strptime(data['session_end'], '%Y-%m-%d %H:%M:%S') if data.get('session_end') else None,
                session_type=data.get('session_type', 'shift'),
                status=data.get('status', 'active'),
                created_by=data.get('created_by')
            )
            
            # Calculate expected closing balance
            session.expected_closing_balance = session.calculate_expected_closing_balance()
            
            # Calculate variance if closing balance provided
            if session.closing_balance:
                session.variance_amount = session.closing_balance - session.expected_closing_balance
            
            db.session.add(session)
            db.session.commit()
            return True, session, "Cash management session created successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating cash management session: {str(e)}"
    
    def close_cash_management_session(self, session_id: int, closing_data: Dict) -> Tuple[bool, str]:
        """Close a cash management session"""
        try:
            session = CashManagement.query.filter_by(id=session_id, tenant_id=self.tenant_id).first()
            if not session:
                return False, "Cash management session not found"
            
            session.cash_sales = Decimal(str(closing_data.get('cash_sales', session.cash_sales)))
            session.cash_received = Decimal(str(closing_data.get('cash_received', session.cash_received)))
            session.cash_paid_out = Decimal(str(closing_data.get('cash_paid_out', session.cash_paid_out)))
            session.closing_balance = Decimal(str(closing_data['closing_balance']))
            session.session_end = datetime.strptime(closing_data['session_end'], '%Y-%m-%d %H:%M:%S')
            session.status = 'closed'
            
            # Calculate expected closing balance and variance
            session.expected_closing_balance = session.calculate_expected_closing_balance()
            session.variance_amount = session.closing_balance - session.expected_closing_balance
            session.variance_reason = closing_data.get('variance_reason')
            
            db.session.commit()
            return True, "Cash management session closed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error closing cash management session: {str(e)}"
    
    # Analytics and Reporting
    
    def get_payment_analytics(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict:
        """Get payment analytics for a date range"""
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Payment method analytics
            payment_methods = db.session.query(
                PaymentMethod.method_type,
                func.count(SplitPayment.id).label('transaction_count'),
                func.sum(SplitPayment.amount).label('total_amount')
            ).join(
                SplitPayment, PaymentMethod.id == SplitPayment.payment_method_id
            ).filter(
                SplitPayment.tenant_id == self.tenant_id,
                SplitPayment.created_at >= start_date,
                SplitPayment.created_at <= end_date,
                SplitPayment.status == 'completed'
            ).group_by(PaymentMethod.method_type).all()
            
            # Wallet payment analytics
            wallet_stats = db.session.query(
                func.count(WalletPayment.id).label('total_transactions'),
                func.sum(WalletPayment.amount).label('total_amount'),
                func.count(func.nullif(WalletPayment.status, 'completed')).label('failed_transactions')
            ).filter(
                WalletPayment.tenant_id == self.tenant_id,
                WalletPayment.created_at >= start_date,
                WalletPayment.created_at <= end_date
            ).first()
            
            # EMI payment analytics
            emi_stats = db.session.query(
                func.count(EMIPayment.id).label('total_installments'),
                func.sum(EMIPayment.paid_amount).label('total_paid'),
                func.sum(EMIPayment.late_fee).label('total_late_fees'),
                func.count(func.nullif(EMIPayment.status, 'paid')).label('overdue_installments')
            ).filter(
                EMIPayment.tenant_id == self.tenant_id,
                EMIPayment.due_date >= start_date,
                EMIPayment.due_date <= end_date
            ).first()
            
            return {
                'payment_methods': [
                    {
                        'method_type': result.method_type,
                        'transaction_count': result.transaction_count or 0,
                        'total_amount': float(result.total_amount or 0)
                    }
                    for result in payment_methods
                ],
                'wallet_payments': {
                    'total_transactions': wallet_stats.total_transactions or 0,
                    'total_amount': float(wallet_stats.total_amount or 0),
                    'failed_transactions': wallet_stats.failed_transactions or 0
                },
                'emi_payments': {
                    'total_installments': emi_stats.total_installments or 0,
                    'total_paid': float(emi_stats.total_paid or 0),
                    'total_late_fees': float(emi_stats.total_late_fees or 0),
                    'overdue_installments': emi_stats.overdue_installments or 0
                },
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            return {
                'error': f"Error generating payment analytics: {str(e)}",
                'payment_methods': [],
                'wallet_payments': {},
                'emi_payments': {}
            }
    
    # Helper Methods
    
    def _generate_wallet_transaction_id(self) -> str:
        """Generate a unique wallet transaction ID"""
        prefix = "WLT"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of transactions for today
        today_count = WalletPayment.query.filter(
            WalletPayment.tenant_id == self.tenant_id,
            WalletPayment.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:04d}"
    
    def _generate_emi_plan_id(self) -> str:
        """Generate a unique EMI plan ID"""
        prefix = "EMI"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of EMI plans for today
        today_count = EMIPayment.query.filter(
            EMIPayment.tenant_id == self.tenant_id,
            EMIPayment.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).distinct(EMIPayment.emi_plan_id).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"
    
    def _generate_settlement_id(self) -> str:
        """Generate a unique settlement ID"""
        prefix = "STL"
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Get count of settlements for today
        today_count = SettlementRecord.query.filter(
            SettlementRecord.tenant_id == self.tenant_id,
            SettlementRecord.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        sequence = today_count + 1
        return f"{prefix}{date_str}{sequence:03d}"


# Factory function to create service instances
def create_payment_settlement_service(tenant_id: str) -> PaymentSettlementService:
    """Factory function to create a payment settlement service instance"""
    return PaymentSettlementService(tenant_id)