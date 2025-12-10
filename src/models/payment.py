"""
Payment model for handling payment information with enhanced encryption
"""

from src.utils.encryption import get_encryption_manager

class Payment:
    """Payment model with encrypted sensitive data and integrity checks"""
    
    def __init__(self, db):
        self.db = db
        self.encryption_manager = get_encryption_manager()
    
    def add_payment(self, order_id, payment_mode, amount, payment_details=None):
        """
        Add payment record with encrypted sensitive information
        
        Args:
            order_id: Order ID
            payment_mode: Payment method (Cash, Card, UPI, Wallet, Credit)
            amount: Payment amount
            payment_details: Dictionary containing payment-specific details
                - For Card: card_number, expiry, card_holder
                - For UPI: upi_id
                - For Wallet: wallet_number
                - For Credit: customer_name
        """
        try:
            # Encrypt sensitive payment details with integrity checks
            encrypted_details = {}
            if payment_details:
                if payment_mode == "Card":
                    if 'card_number' in payment_details:
                        encrypted_details['card_number'] = self.encryption_manager.encrypt_with_integrity(payment_details['card_number'])
                    if 'expiry' in payment_details:
                        encrypted_details['expiry'] = self.encryption_manager.encrypt_with_integrity(payment_details['expiry'])
                    if 'card_holder' in payment_details:
                        encrypted_details['card_holder'] = self.encryption_manager.encrypt_with_integrity(payment_details['card_holder'])
                
                elif payment_mode == "UPI":
                    if 'upi_id' in payment_details:
                        encrypted_details['upi_id'] = self.encryption_manager.encrypt_with_integrity(payment_details['upi_id'])
                
                elif payment_mode == "Wallet":
                    if 'wallet_number' in payment_details:
                        encrypted_details['wallet_number'] = self.encryption_manager.encrypt_with_integrity(payment_details['wallet_number'])
                
                elif payment_mode == "Credit":
                    if 'customer_name' in payment_details:
                        encrypted_details['customer_name'] = self.encryption_manager.encrypt_with_integrity(payment_details['customer_name'])
            
            # Store encrypted details as JSON
            import json
            encrypted_json = json.dumps(encrypted_details) if encrypted_details else None
            
            query = """
            INSERT INTO payments (order_id, payment_mode, amount, payment_details)
            VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (order_id, payment_mode, amount, encrypted_json))
            self.db.commit()
            
            return self.db.lastrowid()
        except Exception as e:
            print(f"Error adding payment: {e}")
            self.db.rollback()
            return None
    
    def get_payment_details(self, payment_id):
        """
        Get payment details with decrypted sensitive information
        
        Args:
            payment_id: Payment ID
            
        Returns:
            Dictionary with payment details
        """
        try:
            query = """
            SELECT id, order_id, payment_mode, amount, payment_details, created_at
            FROM payments
            WHERE id = ?
            """
            
            self.db.execute_query(query, (payment_id,))
            result = self.db.fetch_one()
            
            if not result:
                return None
            
            payment_id, order_id, payment_mode, amount, encrypted_details, created_at = result
            
            # Decrypt payment details
            decrypted_details = {}
            if encrypted_details:
                import json
                try:
                    encrypted_dict = json.loads(encrypted_details)
                    
                    if payment_mode == "Card":
                        if 'card_number' in encrypted_dict:
                            decrypted_details['card_number'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['card_number'])
                        if 'expiry' in encrypted_dict:
                            decrypted_details['expiry'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['expiry'])
                        if 'card_holder' in encrypted_dict:
                            decrypted_details['card_holder'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['card_holder'])
                    
                    elif payment_mode == "UPI":
                        if 'upi_id' in encrypted_dict:
                            decrypted_details['upi_id'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['upi_id'])
                    
                    elif payment_mode == "Wallet":
                        if 'wallet_number' in encrypted_dict:
                            decrypted_details['wallet_number'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['wallet_number'])
                    
                    elif payment_mode == "Credit":
                        if 'customer_name' in encrypted_dict:
                            decrypted_details['customer_name'] = self.encryption_manager.decrypt_with_integrity(encrypted_dict['customer_name'])
                
                except json.JSONDecodeError:
                    print(f"Error decoding payment details for payment ID {payment_id}")
            
            return {
                'id': payment_id,
                'order_id': order_id,
                'payment_mode': payment_mode,
                'amount': amount,
                'payment_details': decrypted_details,
                'created_at': created_at
            }
        except Exception as e:
            print(f"Error getting payment details: {e}")
            return None
    
    def get_order_payments(self, order_id):
        """
        Get all payments for an order with decrypted details
        
        Args:
            order_id: Order ID
            
        Returns:
            List of payment dictionaries
        """
        try:
            query = """
            SELECT id FROM payments
            WHERE order_id = ?
            ORDER BY created_at
            """
            
            self.db.execute_query(query, (order_id,))
            payment_ids = [row[0] for row in self.db.fetch_all()]
            
            payments = []
            for payment_id in payment_ids:
                payment = self.get_payment_details(payment_id)
                if payment:
                    payments.append(payment)
            
            return payments
        except Exception as e:
            print(f"Error getting order payments: {e}")
            return []
    
    def update_payment_details(self, payment_id, payment_details):
        """
        Update payment details with encryption
        
        Args:
            payment_id: Payment ID
            payment_details: New payment details dictionary
        """
        try:
            # Get current payment to determine payment mode
            query = "SELECT payment_mode FROM payments WHERE id = ?"
            self.db.execute_query(query, (payment_id,))
            result = self.db.fetch_one()
            
            if not result:
                return False
            
            payment_mode = result[0]
            
            # Encrypt new details with integrity checks
            encrypted_details = {}
            if payment_mode == "Card":
                if 'card_number' in payment_details:
                    encrypted_details['card_number'] = self.encryption_manager.encrypt_with_integrity(payment_details['card_number'])
                if 'expiry' in payment_details:
                    encrypted_details['expiry'] = self.encryption_manager.encrypt_with_integrity(payment_details['expiry'])
                if 'card_holder' in payment_details:
                    encrypted_details['card_holder'] = self.encryption_manager.encrypt_with_integrity(payment_details['card_holder'])
            
            elif payment_mode == "UPI":
                if 'upi_id' in payment_details:
                    encrypted_details['upi_id'] = self.encryption_manager.encrypt_with_integrity(payment_details['upi_id'])
            
            elif payment_mode == "Wallet":
                if 'wallet_number' in payment_details:
                    encrypted_details['wallet_number'] = self.encryption_manager.encrypt_with_integrity(payment_details['wallet_number'])
            
            elif payment_mode == "Credit":
                if 'customer_name' in payment_details:
                    encrypted_details['customer_name'] = self.encryption_manager.encrypt_with_integrity(payment_details['customer_name'])
            
            # Update with encrypted JSON
            import json
            encrypted_json = json.dumps(encrypted_details) if encrypted_details else None
            
            query = "UPDATE payments SET payment_details = ? WHERE id = ?"
            self.db.execute_query(query, (encrypted_json, payment_id))
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"Error updating payment details: {e}")
            self.db.rollback()
            return False
    
    def delete_payment(self, payment_id):
        """
        Delete a payment record
        
        Args:
            payment_id: Payment ID
        """
        try:
            query = "DELETE FROM payments WHERE id = ?"
            self.db.execute_query(query, (payment_id,))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error deleting payment: {e}")
            self.db.rollback()
            return False
    
    def verify_encrypted_payments(self):
        """
        Utility method to verify all payment details are encrypted
        
        Returns:
            True if all payments appear to be properly encrypted
        """
        try:
            query = "SELECT id, payment_mode, payment_details FROM payments WHERE payment_details IS NOT NULL"
            self.db.execute_query(query)
            payments = self.db.fetch_all()
            
            unencrypted_count = 0
            for payment_id, payment_mode, payment_details in payments:
                if not payment_details:
                    continue
                
                try:
                    import json
                    details_dict = json.loads(payment_details)
                    
                    # Check if sensitive fields are encrypted
                    if payment_mode == "Card" and 'card_number' in details_dict:
                        card_number = details_dict['card_number']
                        # Try to decrypt with integrity, if it equals original, it's likely unencrypted
                        try:
                            decrypted = self.encryption_manager.decrypt_with_integrity(card_number)
                            if card_number == decrypted:
                                unencrypted_count += 1
                                print(f"Payment ID {payment_id} has unencrypted card number")
                        except:
                            # If integrity decryption fails, try standard decryption
                            decrypted = self.encryption_manager.decrypt_field(card_number)
                            if card_number == decrypted:
                                unencrypted_count += 1
                                print(f"Payment ID {payment_id} has unencrypted card number")
                    
                    elif payment_mode == "UPI" and 'upi_id' in details_dict:
                        upi_id = details_dict['upi_id']
                        try:
                            decrypted = self.encryption_manager.decrypt_with_integrity(upi_id)
                            if upi_id == decrypted:
                                unencrypted_count += 1
                                print(f"Payment ID {payment_id} has unencrypted UPI ID")
                        except:
                            # If integrity decryption fails, try standard decryption
                            decrypted = self.encryption_manager.decrypt_field(upi_id)
                            if upi_id == decrypted:
                                unencrypted_count += 1
                                print(f"Payment ID {payment_id} has unencrypted UPI ID")
                
                except json.JSONDecodeError:
                    print(f"Payment ID {payment_id} has invalid JSON in payment_details")
                    unencrypted_count += 1
            
            if unencrypted_count > 0:
                print(f"Found {unencrypted_count} payments with potentially unencrypted details")
            else:
                print("All payment details appear to be properly encrypted")
            
            return unencrypted_count == 0
        except Exception as e:
            print(f"Error verifying encrypted payments: {e}")
            return False