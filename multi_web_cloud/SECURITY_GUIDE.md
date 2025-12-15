# Security Guide - Enhanced Flask POS Application

## 📋 Table of Contents

1. [Security Overview](#security-overview)
2. [Threat Landscape](#threat-landscape)
3. [Security Architecture](#security-architecture)
4. [Authentication & Authorization](#authentication--authorization)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Application Security](#application-security)
8. [Session Management Security](#session-management-security)
9. [Payment Security](#payment-security)
10. [Multi-Tenant Security](#multi-tenant-security)
11. [Security Monitoring](#security-monitoring)
12. [Compliance](#compliance)
13. [Security Best Practices](#security-best-practices)
14. [Incident Response](#incident-response)
15. [Security Testing](#security-testing)

---

## Security Overview

### Security Philosophy

The Enhanced Flask POS application follows a defense-in-depth security approach with multiple layers of protection:

- **Zero Trust Architecture**: Never trust, always verify
- **Principle of Least Privilege**: Minimum necessary access
- **Defense in Depth**: Multiple security layers
- **Security by Design**: Built-in security from ground up
- **Continuous Monitoring**: Real-time threat detection

### Security Goals

1. **Confidentiality**: Protect sensitive data from unauthorized access
2. **Integrity**: Ensure data accuracy and prevent tampering
3. **Availability**: Maintain system uptime and reliability
4. **Authentication**: Verify user identities securely
5. **Authorization**: Control access to resources appropriately
6. **Auditability**: Track and log all security events

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│  • Input Validation  • Business Logic Security        │
│  • Error Handling    • Secure Coding Practices        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Session Layer                         │
│  • Session Management  • CSRF Protection              │
│  • Token Security    • Timeout Management           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                  Authentication Layer                     │
│  • Multi-Factor Auth  • Password Policies           │
│  • Biometric Options  • Account Lockout              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                   Network Layer                           │
│  • TLS/SSL          • Firewall Rules               │
│  • Rate Limiting    • DDoS Protection             │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                    Data Layer                            │
│  • Encryption       • Access Controls               │
│  • Backup Security  • Data Retention                │
└─────────────────────────────────────────────────────────────┘
```

---

## Threat Landscape

### Common Threats

#### 1. Web Application Threats

- **SQL Injection**: Malicious SQL code injection
- **Cross-Site Scripting (XSS)**: Client-side script injection
- **Cross-Site Request Forgery (CSRF)**: Forced malicious requests
- **Authentication Bypass**: Unauthorized access attempts
- **Privilege Escalation**: Gaining elevated permissions

#### 2. Infrastructure Threats

- **DDoS Attacks**: Overwhelming system resources
- **Man-in-the-Middle**: Intercepting communications
- **DNS Spoofing**: Redirecting to malicious sites
- **Port Scanning**: Discovering system vulnerabilities

#### 3. Data Threats

- **Data Breaches**: Unauthorized data access
- **Data Exfiltration**: Stealing sensitive information
- **Ransomware**: Encrypting data for extortion
- **Insider Threats**: Malicious internal activities

#### 4. Business Logic Threats

- **Payment Fraud**: Manipulating payment processes
- **Loyalty Abuse**: Exploiting loyalty programs
- **Order Manipulation**: Altering order data
- **Inventory Theft**: Manipulating inventory records

### Risk Assessment

```python
# security/risk_assessment.py
class ThreatRiskAssessment:
    THREAT_LEVELS = {
        'critical': {'impact': 9, 'likelihood': 3},
        'high': {'impact': 7, 'likelihood': 5},
        'medium': {'impact': 5, 'likelihood': 7},
        'low': {'impact': 3, 'likelihood': 9}
    }
    
    def assess_risk(self, threat_type, context):
        """Assess risk level for specific threat"""
        base_risk = self.THREAT_LEVELS.get(threat_type, {'impact': 5, 'likelihood': 5})
        
        # Adjust based on context
        if context.get('has_authentication', False):
            base_risk['likelihood'] -= 1
        
        if context.get('has_encryption', False):
            base_risk['impact'] -= 1
        
        risk_score = base_risk['impact'] * base_risk['likelihood']
        
        return {
            'threat_type': threat_type,
            'risk_score': risk_score,
            'risk_level': self.calculate_risk_level(risk_score),
            'mitigations': self.get_mitigations(threat_type)
        }
    
    def calculate_risk_level(self, score):
        if score >= 40:
            return 'critical'
        elif score >= 25:
            return 'high'
        elif score >= 15:
            return 'medium'
        else:
            return 'low'
```

---

## Security Architecture

### Security Components

#### 1. Authentication System

```python
# security/authentication.py
class AuthenticationService:
    def __init__(self):
        self.password_policy = PasswordPolicy()
        self.mfa_service = MFAService()
        self.session_manager = SecureSessionManager()
    
    def authenticate_user(self, credentials):
        """Multi-factor authentication process"""
        username = credentials.get('username')
        password = credentials.get('password')
        mfa_token = credentials.get('mfa_token')
        
        # Step 1: Validate credentials
        user = self.validate_credentials(username, password)
        if not user:
            self.log_failed_attempt(username)
            return None
        
        # Step 2: Check MFA if enabled
        if user.mfa_enabled:
            if not self.mfa_service.verify_token(user.id, mfa_token):
                self.log_mfa_failure(user.id)
                return None
        
        # Step 3: Create secure session
        session_id = self.session_manager.create_session(user)
        
        return {
            'user_id': user.id,
            'session_id': session_id,
            'permissions': self.get_user_permissions(user)
        }
    
    def validate_credentials(self, username, password):
        """Secure credential validation"""
        # Rate limiting
        if self.is_rate_limited(username):
            raise AuthenticationError("Too many attempts")
        
        # User lookup
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        
        # Password verification with constant-time comparison
        if not self.verify_password(password, user.password_hash):
            return None
        
        # Account status check
        if user.status != 'active':
            return None
        
        return user
```

#### 2. Authorization System

```python
# security/authorization.py
class AuthorizationService:
    def __init__(self):
        self.permission_manager = PermissionManager()
        self.role_manager = RoleManager()
    
    def check_permission(self, user_id, resource, action):
        """Check if user has permission for action on resource"""
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Get user roles and permissions
        user_roles = self.role_manager.get_user_roles(user_id)
        user_permissions = self.permission_manager.get_role_permissions(user_roles)
        
        # Check specific permission
        required_permission = f"{resource}.{action}"
        
        return required_permission in user_permissions
    
    def check_tenant_access(self, user_id, tenant_id, resource_id=None):
        """Check tenant access with resource-level validation"""
        # Verify user belongs to tenant
        user_tenant = UserTenant.query.filter_by(
            user_id=user_id,
            tenant_id=tenant_id
        ).first()
        
        if not user_tenant:
            return False
        
        # If resource_id provided, check resource ownership
        if resource_id:
            resource = self.get_resource(resource_id)
            if resource and resource.tenant_id != tenant_id:
                return False
        
        return True
```

#### 3. Encryption Service

```python
# security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    def __init__(self):
        self.key = self._derive_key()
        self.cipher_suite = Fernet(self.key)
    
    def _derive_key(self):
        """Derive encryption key from master key"""
        password = current_app.config['ENCRYPTION_MASTER_KEY'].encode()
        salt = current_app.config['ENCRYPTION_SALT'].encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, data):
        """Encrypt sensitive data"""
        if isinstance(data, str):
            data = data.encode()
        
        encrypted_data = self.cipher_suite.encrypt(data)
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data):
        """Decrypt sensitive data"""
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode()
        
        encrypted_data = base64.urlsafe_b64decode(encrypted_data)
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    def encrypt_field(self, model_instance, field_name):
        """Encrypt model field"""
        plaintext = getattr(model_instance, field_name)
        if plaintext:
            encrypted = self.encrypt(plaintext)
            setattr(model_instance, f"{field_name}_encrypted", encrypted)
            setattr(model_instance, field_name, None)  # Clear plaintext
    
    def decrypt_field(self, model_instance, field_name):
        """Decrypt model field"""
        encrypted = getattr(model_instance, f"{field_name}_encrypted")
        if encrypted:
            decrypted = self.decrypt(encrypted)
            setattr(model_instance, field_name, decrypted)
```

---

## Authentication & Authorization

### Password Security

#### Password Policy

```python
# security/password_policy.py
class PasswordPolicy:
    def __init__(self):
        self.min_length = 12
        self.max_length = 128
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.forbidden_patterns = [
            'password', '123456', 'qwerty', 'admin',
            'welcome', 'login', 'user', 'test'
        ]
        self.forbidden_sequences = [
            '123', 'abc', 'qwe', 'asd', 'zxc'
        ]
    
    def validate_password(self, password):
        """Validate password against policy"""
        errors = []
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")
        
        if len(password) > self.max_length:
            errors.append(f"Password must not exceed {self.max_length} characters")
        
        # Character requirements
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        
        if self.require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append("Password must contain special characters")
        
        # Forbidden patterns
        password_lower = password.lower()
        for pattern in self.forbidden_patterns:
            if pattern in password_lower:
                errors.append(f"Password cannot contain common patterns like '{pattern}'")
        
        # Sequential characters
        for seq in self.forbidden_sequences:
            if seq in password_lower:
                errors.append(f"Password cannot contain sequential characters like '{seq}'")
        
        # Calculate strength
        strength = self.calculate_strength(password)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': strength,
            'score': self.calculate_score(password)
        }
    
    def calculate_strength(self, password):
        """Calculate password strength"""
        score = 0
        
        # Length bonus
        score += min(len(password) * 2, 20)
        
        # Character variety
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            score += 15
        
        # Entropy bonus
        entropy = self.calculate_entropy(password)
        score += min(entropy * 5, 25)
        
        if score < 30:
            return 'weak'
        elif score < 60:
            return 'medium'
        elif score < 80:
            return 'strong'
        else:
            return 'very_strong'
```

#### Multi-Factor Authentication

```python
# security/mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAService:
    def __init__(self):
        self.issuer = "Flask POS"
        self.app_name = "Restaurant POS"
    
    def generate_secret(self, user_id):
        """Generate MFA secret for user"""
        secret = pyotp.random_base32()
        
        # Store secret encrypted
        encrypted_secret = encryption_service.encrypt(secret)
        
        user_mfa = UserMFA(
            user_id=user_id,
            secret_encrypted=encrypted_secret,
            enabled=False,
            backup_codes=self.generate_backup_codes()
        )
        
        db.session.add(user_mfa)
        db.session.commit()
        
        return secret
    
    def generate_qr_code(self, user_id, secret):
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=f"{self.app_name}:{user_id}",
            issuer_name=self.issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, user_id, token):
        """Verify MFA token"""
        user_mfa = UserMFA.query.filter_by(user_id=user_id).first()
        if not user_mfa or not user_mfa.enabled:
            return False
        
        secret = encryption_service.decrypt(user_mfa.secret_encrypted)
        totp = pyotp.TOTP(secret)
        
        # Check current and adjacent time windows
        for i in range(-1, 2):  # -1, 0, +1
            if totp.verify(token, valid_window=i):
                return True
        
        return False
    
    def verify_backup_code(self, user_id, backup_code):
        """Verify backup code"""
        user_mfa = UserMFA.query.filter_by(user_id=user_id).first()
        if not user_mfa:
            return False
        
        backup_codes = json.loads(user_mfa.backup_codes)
        
        if backup_code in backup_codes:
            # Remove used backup code
            backup_codes.remove(backup_code)
            user_mfa.backup_codes = json.dumps(backup_codes)
            db.session.commit()
            return True
        
        return False
```

### Session Security

#### Secure Session Management

```python
# security/session_security.py
from flask import session
import uuid
import hashlib
import hmac

class SecureSessionManager:
    def __init__(self):
        self.session_timeout = 3600  # 1 hour
        self.max_concurrent_sessions = 3
        self.rotation_interval = 300  # 5 minutes
    
    def create_session(self, user):
        """Create secure session with multiple security layers"""
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session fingerprint
        fingerprint = self.generate_fingerprint()
        
        # Store session data
        session_data = {
            'session_id': session_id,
            'user_id': user.id,
            'tenant_id': user.tenant_id,
            'fingerprint': fingerprint,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'authenticated': True
        }
        
        # Encrypt session data
        encrypted_session = encryption_service.encrypt(json.dumps(session_data))
        
        # Store in secure cookie
        session['pos_session'] = encrypted_session
        session['csrf_token'] = self.generate_csrf_token()
        
        # Track session in database
        db_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            fingerprint=fingerprint,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=self.session_timeout)
        )
        
        db.session.add(db_session)
        db.session.commit()
        
        return session_id
    
    def validate_session(self):
        """Validate session security"""
        encrypted_session = session.get('pos_session')
        if not encrypted_session:
            return False
        
        try:
            session_data = json.loads(encryption_service.decrypt(encrypted_session))
        except Exception:
            return False
        
        # Check session expiration
        if datetime.utcnow() > session_data['expires_at']:
            return False
        
        # Verify fingerprint
        current_fingerprint = self.generate_fingerprint()
        if not hmac.compare_digest(session_data['fingerprint'], current_fingerprint):
            return False
        
        # Check IP address (optional)
        if session_data['ip_address'] != request.remote_addr:
            # Log suspicious activity
            self.log_suspicious_activity('IP address changed', session_data)
        
        # Update last activity
        self.update_session_activity(session_data['session_id'])
        
        return True
    
    def generate_fingerprint(self):
        """Generate browser fingerprint"""
        # Collect various browser characteristics
        user_agent = request.headers.get('User-Agent', '')
        accept_language = request.headers.get('Accept-Language', '')
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        # Create fingerprint
        fingerprint_data = f"{user_agent}:{accept_language}:{accept_encoding}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        return fingerprint
    
    def rotate_session(self):
        """Rotate session ID periodically"""
        if 'pos_session' in session:
            try:
                session_data = json.loads(encryption_service.decrypt(session['pos_session']))
                old_session_id = session_data['session_id']
                
                # Generate new session ID
                new_session_id = str(uuid.uuid4())
                session_data['session_id'] = new_session_id
                session_data['last_activity'] = datetime.utcnow()
                
                # Update database
                db_session = UserSession.query.filter_by(session_id=old_session_id).first()
                if db_session:
                    db_session.session_id = new_session_id
                    db.session.commit()
                
                # Update session cookie
                session['pos_session'] = encryption_service.encrypt(json.dumps(session_data))
                
            except Exception:
                # If rotation fails, invalidate session
                self.invalidate_session()
```

---

## Data Protection

### Encryption at Rest

#### Database Encryption

```python
# security/database_encryption.py
class DatabaseEncryption:
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.encrypted_fields = [
            'customer.phone',
            'customer.email',
            'user.password_hash',
            'payment.card_number',
            'payment.bank_account'
        ]
    
    def encrypt_sensitive_data(self, model_instance):
        """Encrypt sensitive fields before saving"""
        for field_path in self.encrypted_fields:
            model_name, field_name = field_path.split('.')
            
            if hasattr(model_instance, field_name):
                value = getattr(model_instance, field_name)
                if value:
                    encrypted_value = self.encryption_service.encrypt(value)
                    setattr(model_instance, f"{field_name}_encrypted", encrypted_value)
                    setattr(model_instance, field_name, None)  # Clear plaintext
    
    def decrypt_sensitive_data(self, model_instance):
        """Decrypt sensitive fields after loading"""
        for field_path in self.encrypted_fields:
            model_name, field_name = field_path.split('.')
            
            encrypted_field_name = f"{field_name}_encrypted"
            if hasattr(model_instance, encrypted_field_name):
                encrypted_value = getattr(model_instance, encrypted_field_name)
                if encrypted_value:
                    decrypted_value = self.encryption_service.decrypt(encrypted_value)
                    setattr(model_instance, field_name, decrypted_value)
    
    def setup_model_hooks(self, model_class):
        """Setup encryption hooks for model"""
        # Before insert/update
        @event.listens_for(model_class, 'before_insert')
        def encrypt_before_insert(mapper, connection, target):
            self.encrypt_sensitive_data(target)
        
        @event.listens_for(model_class, 'before_update')
        def encrypt_before_update(mapper, connection, target):
            self.encrypt_sensitive_data(target)
        
        # After load
        @event.listens_for(model_class, 'load')
        def decrypt_after_load(target, context):
            self.decrypt_sensitive_data(target)
```

#### File Encryption

```python
# security/file_encryption.py
from cryptography.fernet import Fernet
import os

class FileEncryption:
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Get or create file encryption key"""
        key_file = 'config/file_encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt_file(self, file_path):
        """Encrypt file at given path"""
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        encrypted_data = self.cipher.encrypt(file_data)
        
        encrypted_path = f"{file_path}.encrypted"
        with open(encrypted_path, 'wb') as f:
            f.write(encrypted_data)
        
        # Remove original file
        os.remove(file_path)
        
        return encrypted_path
    
    def decrypt_file(self, encrypted_file_path):
        """Decrypt file at given path"""
        with open(encrypted_file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        # Remove .encrypted extension
        original_path = encrypted_file_path[:-10]  # Remove '.encrypted'
        
        with open(original_path, 'wb') as f:
            f.write(decrypted_data)
        
        # Remove encrypted file
        os.remove(encrypted_file_path)
        
        return original_path
```

### Data Masking

#### PII Data Masking

```python
# security/data_masking.py
class DataMasking:
    @staticmethod
    def mask_email(email):
        """Mask email address"""
        if '@' not in email:
            return email
        
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone):
        """Mask phone number"""
        if len(phone) <= 4:
            return '*' * len(phone)
        
        return phone[:2] + '*' * (len(phone) - 4) + phone[-2:]
    
    @staticmethod
    def mask_card_number(card_number):
        """Mask credit card number"""
        if len(card_number) <= 4:
            return '*' * len(card_number)
        
        return '*' * (len(card_number) - 4) + card_number[-4:]
    
    @staticmethod
    def mask_pii(data, pii_types):
        """Mask PII data based on types"""
        masked_data = data.copy()
        
        for field, pii_type in pii_types.items():
            if field in masked_data:
                if pii_type == 'email':
                    masked_data[field] = DataMasking.mask_email(masked_data[field])
                elif pii_type == 'phone':
                    masked_data[field] = DataMasking.mask_phone(masked_data[field])
                elif pii_type == 'card':
                    masked_data[field] = DataMasking.mask_card_number(masked_data[field])
        
        return masked_data
```

---

## Network Security

### TLS/SSL Configuration

#### SSL/TLS Setup

```python
# security/ssl_config.py
class SSLConfiguration:
    @staticmethod
    def get_ssl_context():
        """Create secure SSL context"""
        context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        
        # Configure secure TLS version
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Configure cipher suites
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Configure options
        context.set_options(ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_COMPRESSION)
        
        return context
    
    @staticmethod
    def configure_flask_ssl(app):
        """Configure Flask for SSL"""
        app.config.update({
            'SSL_CONTEXT': SSLConfiguration.get_ssl_context(),
            'FORCE_HTTPS': True,
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax'
        })
```

#### HSTS Configuration

```python
# security/hsts.py
from flask import make_response

class HSTSManager:
    @staticmethod
    def add_hsts_headers(response):
        """Add HSTS headers to response"""
        hsts_header = 'max-age=31536000; includeSubDomains; preload'
        response.headers['Strict-Transport-Security'] = hsts_header
        return response

# Flask middleware
@app.after_request
def add_security_headers(response):
    response = HSTSManager.add_hsts_headers(response)
    return response
```

### Firewall Configuration

#### Application Firewall Rules

```python
# security/firewall.py
class ApplicationFirewall:
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union.*select',               # SQL Injection
            r'javascript:',                 # JavaScript injection
            r'\.\./',                      # Path traversal
            r'cmd\.exe',                   # Command injection
        ]
    
    def check_request(self):
        """Check request against firewall rules"""
        # IP blocking
        client_ip = request.remote_addr
        if client_ip in self.blocked_ips:
            abort(403)  # Forbidden
        
        # Pattern matching
        request_data = f"{request.url}{request.get_data(as_text=True)}"
        
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                self.log_suspicious_request(client_ip, pattern)
                self.block_ip_temporarily(client_ip)
                abort(403)
        
        # Rate limiting
        if self.is_rate_limited(client_ip):
            abort(429)  # Too Many Requests
    
    def block_ip_temporarily(self, ip_address):
        """Block IP address temporarily"""
        self.blocked_ips.add(ip_address)
        
        # Schedule unblock
        threading.Timer(300, self.unblock_ip, args=[ip_address]).start()
    
    def unblock_ip(self, ip_address):
        """Unblock IP address"""
        self.blocked_ips.discard(ip_address)
```

---

## Application Security

### Input Validation

#### Comprehensive Input Validation

```python
# security/input_validation.py
import re
from bleach import clean
from html import escape

class InputValidator:
    def __init__(self):
        self.validation_rules = {
            'email': {
                'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'max_length': 255,
                'required': True
            },
            'phone': {
                'pattern': r'^\+?[\d\s\-\(\)]{10,20}$',
                'max_length': 20,
                'required': False
            },
            'name': {
                'pattern': r'^[a-zA-Z\s\-\']{1,100}$',
                'max_length': 100,
                'required': True
            },
            'amount': {
                'pattern': r'^\d+(\.\d{1,2})?$',
                'min_value': 0,
                'max_value': 999999.99,
                'required': True
            },
            'gst_number': {
                'pattern': r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z?[A-Z0-9]{1}$',
                'max_length': 15,
                'required': False
            }
        }
    
    def validate_field(self, field_name, field_value):
        """Validate single field"""
        if field_name not in self.validation_rules:
            return {'valid': False, 'error': 'Unknown field type'}
        
        rules = self.validation_rules[field_name]
        
        # Required check
        if rules.get('required', False) and not field_value:
            return {'valid': False, 'error': f'{field_name} is required'}
        
        if not field_value and not rules.get('required', False):
            return {'valid': True}
        
        # Length check
        if 'max_length' in rules and len(field_value) > rules['max_length']:
            return {'valid': False, 'error': f'{field_name} exceeds maximum length'}
        
        # Pattern check
        if 'pattern' in rules:
            if not re.match(rules['pattern'], str(field_value)):
                return {'valid': False, 'error': f'{field_name} format is invalid'}
        
        # Value range check
        if 'min_value' in rules and float(field_value) < rules['min_value']:
            return {'valid': False, 'error': f'{field_name} is below minimum value'}
        
        if 'max_value' in rules and float(field_value) > rules['max_value']:
            return {'valid': False, 'error': f'{field_name} exceeds maximum value'}
        
        return {'valid': True}
    
    def sanitize_input(self, input_value, field_type='text'):
        """Sanitize input based on field type"""
        if field_type == 'html':
            # Allow safe HTML only
            return clean(input_value, tags=['b', 'i', 'u', 'strong', 'em'], strip=True)
        elif field_type == 'text':
            # Escape HTML entities
            return escape(input_value)
        elif field_type == 'numeric':
            # Allow only numeric characters
            return re.sub(r'[^\d.]', '', input_value)
        elif field_type == 'alphanumeric':
            # Allow only alphanumeric characters
            return re.sub(r'[^a-zA-Z0-9]', '', input_value)
        else:
            return input_value
```

#### CSRF Protection

```python
# security/csrf.py
import secrets
from flask import session, request
from functools import wraps

class CSRFProtection:
    @staticmethod
    def generate_token():
        """Generate CSRF token"""
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']
    
    @staticmethod
    def validate_token():
        """Validate CSRF token"""
        token = session.get('csrf_token')
        request_token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        
        if not token or not request_token:
            return False
        
        return secrets.compare_digest(token, request_token)
    
    @staticmethod
    def protect(f):
        """CSRF protection decorator"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                if not CSRFProtection.validate_token():
                    abort(403, description='CSRF token validation failed')
            return f(*args, **kwargs)
        return decorated_function

# Template helper function
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=CSRFProtection.generate_token)
```

### SQL Injection Prevention

#### Secure Database Queries

```python
# security/sql_injection.py
class SQLInjectionProtection:
    @staticmethod
    def execute_secure_query(query, params=None):
        """Execute query with parameter binding"""
        try:
            if params:
                result = db.session.execute(text(query), params)
            else:
                result = db.session.execute(text(query))
            return result
        except Exception as e:
            # Log suspicious activity
            security_logger.error(f"Suspicious SQL query: {query}")
            raise
    
    @staticmethod
    def validate_query(query):
        """Validate query for SQL injection patterns"""
        suspicious_patterns = [
            r'union\s+select',
            r'or\s+1\s*=\s*1',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'exec\s*\(',
            r'xp_cmdshell',
            r'sp_executesql'
        ]
        
        query_lower = query.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, query_lower):
                raise SecurityError("Potentially malicious SQL query detected")
        
        return True

# Model usage example
class SecureCustomer(db.Model):
    @classmethod
    def find_by_email(cls, email):
        """Secure customer lookup by email"""
        query = text("SELECT * FROM customers WHERE email = :email")
        return SQLInjectionProtection.execute_secure_query(query, {'email': email})
    
    @classmethod
    def find_with_conditions(cls, conditions):
        """Secure customer lookup with conditions"""
        # Build parameterized query
        where_clauses = []
        params = {}
        
        for i, (field, operator, value) in enumerate(conditions):
            param_name = f"param_{i}"
            where_clauses.append(f"{field} {operator} :{param_name}")
            params[param_name] = value
        
        query = text(f"SELECT * FROM customers WHERE {' AND '.join(where_clauses)}")
        return SQLInjectionProtection.execute_secure_query(query, params)
```

---

## Session Management Security

### Session Security Features

#### Advanced Session Management

```python
# security/advanced_session.py
class AdvancedSessionManager:
    def __init__(self):
        self.session_store = RedisStore()
        self.encryption_service = EncryptionService()
        self.security_config = SecurityConfig()
    
    def create_secure_session(self, user):
        """Create highly secure session"""
        # Generate session components
        session_id = secrets.token_urlsafe(32)
        session_key = secrets.token_bytes(32)
        
        # Create session data
        session_data = {
            'user_id': user.id,
            'tenant_id': user.tenant_id,
            'role': user.role,
            'permissions': self.get_user_permissions(user),
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'security_level': self.assess_security_level()
        }
        
        # Encrypt session data
        encrypted_data = self.encryption_service.encrypt(json.dumps(session_data))
        
        # Store session with metadata
        session_metadata = {
            'data': encrypted_data,
            'session_key': session_key.hex(),
            'ip_address': request.remote_addr,
            'user_agent_hash': hashlib.sha256(
                request.headers.get('User-Agent', '').encode()
            ).hexdigest(),
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=self.security_config.SESSION_TIMEOUT),
            'max_concurrent': self.security_config.MAX_CONCURRENT_SESSIONS
        }
        
        # Store in Redis with expiration
        self.session_store.setex(
            f"session:{session_id}",
            self.security_config.SESSION_TIMEOUT * 3600,
            json.dumps(session_metadata)
        )
        
        # Set secure cookie
        response = make_response()
        response.set_cookie(
            'pos_session',
            session_id,
            secure=True,
            httponly=True,
            samesite='Lax',
            max_age=self.security_config.SESSION_TIMEOUT * 3600
        )
        
        return response
    
    def validate_session_security(self, session_id):
        """Comprehensive session validation"""
        session_data = self.session_store.get(f"session:{session_id}")
        
        if not session_data:
            return False, "Session not found"
        
        try:
            metadata = json.loads(session_data)
            session_data = json.loads(self.encryption_service.decrypt(metadata['data']))
        except Exception:
            return False, "Invalid session format"
        
        # Check expiration
        if datetime.utcnow() > datetime.fromisoformat(metadata['expires_at']):
            self.invalidate_session(session_id)
            return False, "Session expired"
        
        # Check IP address consistency
        if metadata['ip_address'] != request.remote_addr:
            self.log_security_event("IP address changed", session_id)
            return False, "IP address mismatch"
        
        # Check user agent consistency
        current_ua_hash = hashlib.sha256(
            request.headers.get('User-Agent', '').encode()
        ).hexdigest()
        
        if metadata['user_agent_hash'] != current_ua_hash:
            self.log_security_event("User agent changed", session_id)
            return False, "User agent mismatch"
        
        # Check concurrent sessions
        concurrent_sessions = self.get_user_concurrent_sessions(session_data['user_id'])
        if len(concurrent_sessions) > metadata['max_concurrent']:
            self.log_security_event("Too many concurrent sessions", session_id)
            return False, "Concurrent session limit exceeded"
        
        # Update last activity
        self.update_session_activity(session_id)
        
        return True, session_data
    
    def rotate_session_id(self, session_id):
        """Rotate session ID for security"""
        old_session_data = self.session_store.get(f"session:{session_id}")
        
        if old_session_data:
            # Generate new session ID
            new_session_id = secrets.token_urlsafe(32)
            
            # Move session data to new ID
            self.session_store.setex(
                f"session:{new_session_id}",
                self.security_config.SESSION_TIMEOUT * 3600,
                old_session_data
            )
            
            # Delete old session
            self.session_store.delete(f"session:{session_id}")
            
            return new_session_id
        
        return None
```

### Session Analytics

#### Session Monitoring

```python
# security/session_monitoring.py
class SessionMonitor:
    def __init__(self):
        self.analytics_store = AnalyticsStore()
    
    def track_session_activity(self, session_id, activity_type, details=None):
        """Track session activity for security analysis"""
        session_data = self.get_session_data(session_id)
        
        if session_data:
            activity_record = {
                'session_id': session_id,
                'user_id': session_data['user_id'],
                'tenant_id': session_data['tenant_id'],
                'activity_type': activity_type,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'timestamp': datetime.utcnow(),
                'details': details or {}
            }
            
            self.analytics_store.record_activity(activity_record)
    
    def detect_anomalous_activity(self, user_id):
        """Detect anomalous session patterns"""
        user_sessions = self.analytics_store.get_user_sessions(user_id, hours=24)
        
        anomalies = []
        
        # Check for unusual login locations
        locations = set(session['ip_address'] for session in user_sessions)
        if len(locations) > 3:  # More than 3 locations in 24 hours
            anomalies.append({
                'type': 'multiple_locations',
                'severity': 'high',
                'description': f"User accessed from {len(locations)} different locations"
            })
        
        # Check for unusual time patterns
        login_times = [session['timestamp'].hour for session in user_sessions if session['activity_type'] == 'login']
        if login_times:
            unusual_hours = [hour for hour in login_times if hour < 6 or hour > 22]
            if len(unusual_hours) > len(login_times) * 0.5:
                anomalies.append({
                    'type': 'unusual_hours',
                    'severity': 'medium',
                    'description': "Multiple logins during unusual hours"
                })
        
        # Check for rapid session creation
        recent_sessions = [
            session for session in user_sessions 
            if session['timestamp'] > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if len(recent_sessions) > 5:
            anomalies.append({
                'type': 'rapid_sessions',
                'severity': 'high',
                'description': "Rapid session creation detected"
            })
        
        return anomalies
```

---

## Payment Security

### PCI DSS Compliance

#### Payment Data Protection

```python
# security/payment_security.py
class PaymentSecurityManager:
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.tokenization_service = TokenizationService()
        self.fraud_detector = FraudDetector()
    
    def process_payment(self, payment_data):
        """Secure payment processing with PCI DSS compliance"""
        # Validate payment data
        validation_result = self.validate_payment_data(payment_data)
        if not validation_result['valid']:
            return {'success': False, 'error': validation_result['error']}
        
        # Tokenize card data
        if payment_data.get('card_number'):
            tokenized_data = self.tokenization_service.tokenize_card(payment_data)
            payment_data['card_token'] = tokenized_data['token']
            del payment_data['card_number']
            del payment_data['cvv']
        
        # Fraud detection
        fraud_score = self.fraud_detector.assess_risk(payment_data)
        if fraud_score > 0.7:
            return {'success': False, 'error': 'High fraud risk detected'}
        
        # Process payment through secure gateway
        try:
            result = self.process_with_gateway(payment_data)
            
            # Store encrypted payment record
            payment_record = {
                'order_id': payment_data['order_id'],
                'amount': payment_data['amount'],
                'currency': payment_data['currency'],
                'payment_method': payment_data['payment_method'],
                'card_token': payment_data.get('card_token'),
                'fraud_score': fraud_score,
                'created_at': datetime.utcnow()
            }
            
            encrypted_record = self.encryption_service.encrypt(json.dumps(payment_record))
            self.store_payment_record(encrypted_record)
            
            return result
            
        except Exception as e:
            self.log_payment_error(payment_data, str(e))
            return {'success': False, 'error': 'Payment processing failed'}
    
    def validate_payment_data(self, payment_data):
        """Validate payment data for security"""
        errors = []
        
        # Amount validation
        amount = payment_data.get('amount', 0)
        if amount <= 0 or amount > 100000:  # Max ₹100,000
            errors.append("Invalid amount")
        
        # Card validation
        if 'card_number' in payment_data:
            card_number = payment_data['card_number'].replace(' ', '')
            if not re.match(r'^\d{13,19}$', card_number):
                errors.append("Invalid card number")
            
            # Luhn algorithm check
            if not self.validate_luhn(card_number):
                errors.append("Invalid card checksum")
        
        # Expiry validation
        if 'expiry_month' in payment_data and 'expiry_year' in payment_data:
            expiry_date = datetime(
                int(payment_data['expiry_year']),
                int(payment_data['expiry_month']),
                1
            )
            
            if expiry_date < datetime.utcnow():
                errors.append("Card has expired")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_luhn(self, card_number):
        """Validate card number using Luhn algorithm"""
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n = (n // 10) + (n % 10)
            total += n
        
        return total % 10 == 0
```

#### Tokenization Service

```python
# security/tokenization.py
class TokenizationService:
    def __init__(self):
        self.token_store = TokenStore()
        self.encryption_service = EncryptionService()
    
    def tokenize_card(self, card_data):
        """Tokenize card data"""
        # Generate random token
        token = f"tok_{secrets.token_urlsafe(24)}"
        
        # Encrypt sensitive data
        sensitive_data = {
            'card_number': card_data['card_number'],
            'expiry_month': card_data['expiry_month'],
            'expiry_year': card_data['expiry_year'],
            'cardholder_name': card_data.get('cardholder_name', ''),
            'billing_address': card_data.get('billing_address', {})
        }
        
        encrypted_data = self.encryption_service.encrypt(json.dumps(sensitive_data))
        
        # Store token mapping
        token_record = {
            'token': token,
            'encrypted_data': encrypted_data,
            'created_at': datetime.utcnow(),
            'last_used': datetime.utcnow(),
            'usage_count': 0
        }
        
        self.token_store.store_token(token_record)
        
        return {
            'token': token,
            'last4': card_data['card_number'][-4:],
            'brand': self.get_card_brand(card_data['card_number'])
        }
    
    def detokenize_card(self, token):
        """Retrieve card data from token"""
        token_record = self.token_store.get_token(token)
        
        if not token_record:
            return None
        
        # Update usage
        token_record['last_used'] = datetime.utcnow()
        token_record['usage_count'] += 1
        self.token_store.update_token(token_record)
        
        # Decrypt data
        try:
            decrypted_data = json.loads(self.encryption_service.decrypt(token_record['encrypted_data']))
            return decrypted_data
        except Exception:
            return None
    
    def get_card_brand(self, card_number):
        """Determine card brand from number"""
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith('5'):
            return 'Mastercard'
        elif card_number.startswith('3'):
            return 'American Express'
        elif card_number.startswith('6'):
            return 'Discover'
        elif card_number.startswith('65'):
            return 'RuPay'
        else:
            return 'Unknown'
```

---

## Multi-Tenant Security

### Tenant Isolation Security

#### Data Isolation Verification

```python
# security/tenant_isolation.py
class TenantIsolationSecurity:
    def __init__(self):
        self.audit_logger = AuditLogger()
    
    def verify_tenant_isolation(self, tenant_id, resource_id, resource_type):
        """Verify tenant isolation for resource access"""
        # Check if resource belongs to tenant
        resource = self.get_resource(resource_id, resource_type)
        
        if not resource:
            self.audit_logger.log_security_event(
                'resource_access_denied',
                f"Resource {resource_id} not found",
                tenant_id=tenant_id
            )
            return False
        
        if resource.tenant_id != tenant_id:
            self.audit_logger.log_security_event(
                'tenant_isolation_breach',
                f"Attempted access to resource {resource_id} from wrong tenant",
                tenant_id=tenant_id,
                resource_id=resource_id
            )
            return False
        
        return True
    
    def enforce_tenant_scoping(self, query, tenant_id):
        """Enforce tenant scoping on database queries"""
        # Add tenant filter to all queries
        if hasattr(query.column_mapper, 'c') and 'tenant_id' in query.column_mapper.c:
            query = query.filter(query.column_mapper.c.tenant_id == tenant_id)
        
        return query
    
    def audit_cross_tenant_access(self, user_id, from_tenant_id, to_tenant_id):
        """Audit cross-tenant access attempts"""
        self.audit_logger.log_security_event(
            'cross_tenant_access',
            f"User {user_id} attempted access from tenant {from_tenant_id} to {to_tenant_id}",
            user_id=user_id,
            from_tenant_id=from_tenant_id,
            to_tenant_id=to_tenant_id
        )
```

#### Tenant Security Policies

```python
# security/tenant_security_policies.py
class TenantSecurityPolicyManager:
    def __init__(self):
        self.policy_store = PolicyStore()
    
    def create_tenant_security_policy(self, tenant_id, policy_config):
        """Create security policy for tenant"""
        policy = {
            'tenant_id': tenant_id,
            'password_policy': {
                'min_length': policy_config.get('password_min_length', 12),
                'require_uppercase': policy_config.get('require_uppercase', True),
                'require_lowercase': policy_config.get('require_lowercase', True),
                'require_digits': policy_config.get('require_digits', True),
                'require_special': policy_config.get('require_special', True),
                'expiry_days': policy_config.get('password_expiry_days', 90)
            },
            'session_policy': {
                'timeout_minutes': policy_config.get('session_timeout', 60),
                'max_concurrent': policy_config.get('max_concurrent_sessions', 3),
                'require_mfa': policy_config.get('require_mfa', False)
            },
            'access_policy': {
                'ip_whitelist': policy_config.get('ip_whitelist', []),
                'ip_blacklist': policy_config.get('ip_blacklist', []),
                'time_restrictions': policy_config.get('time_restrictions', {}),
                'geo_restrictions': policy_config.get('geo_restrictions', [])
            },
            'audit_policy': {
                'log_all_access': policy_config.get('log_all_access', True),
                'log_failed_attempts': policy_config.get('log_failed_attempts', True),
                'retention_days': policy_config.get('audit_retention_days', 2555)
            }
        }
        
        self.policy_store.store_policy(tenant_id, policy)
        return policy
    
    def validate_tenant_access(self, tenant_id, user_id, access_context):
        """Validate access against tenant security policies"""
        policy = self.policy_store.get_policy(tenant_id)
        
        if not policy:
            return True  # No policy means allow access
        
        # Check IP restrictions
        if policy['access_policy']['ip_whitelist']:
            client_ip = access_context.get('ip_address')
            if client_ip not in policy['access_policy']['ip_whitelist']:
                return False
        
        if policy['access_policy']['ip_blacklist']:
            client_ip = access_context.get('ip_address')
            if client_ip in policy['access_policy']['ip_blacklist']:
                return False
        
        # Check time restrictions
        time_restrictions = policy['access_policy']['time_restrictions']
        if time_restrictions:
            current_time = datetime.utcnow().time()
            current_hour = current_time.hour
            
            if 'allowed_hours' in time_restrictions:
                if current_hour not in time_restrictions['allowed_hours']:
                    return False
        
        # Check geographical restrictions
        geo_restrictions = policy['access_policy']['geo_restrictions']
        if geo_restrictions:
            client_country = access_context.get('country')
            if client_country and client_country not in geo_restrictions:
                return False
        
        return True
```

---

## Security Monitoring

### Real-time Security Monitoring

#### Security Event Monitoring

```python
# security/monitoring.py
class SecurityMonitor:
    def __init__(self):
        self.event_queue = EventQueue()
        self.alert_manager = AlertManager()
        self.analytics_service = SecurityAnalyticsService()
    
    def monitor_security_events(self):
        """Monitor security events in real-time"""
        while True:
            try:
                # Get security events
                events = self.event_queue.get_events(batch_size=100)
                
                for event in events:
                    # Analyze event
                    analysis = self.analyze_security_event(event)
                    
                    # Check for threats
                    if analysis['threat_level'] >= 7:
                        self.alert_manager.send_alert(analysis)
                    
                    # Store for analytics
                    self.analytics_service.record_event(event, analysis)
                
                # Sleep before next batch
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                time.sleep(5)
    
    def analyze_security_event(self, event):
        """Analyze security event for threats"""
        analysis = {
            'event_id': event['id'],
            'event_type': event['type'],
            'threat_level': 0,
            'risk_score': 0,
            'indicators': []
        }
        
        # Analyze based on event type
        if event['type'] == 'failed_login':
            analysis = self.analyze_failed_login(event, analysis)
        elif event['type'] == 'suspicious_activity':
            analysis = self.analyze_suspicious_activity(event, analysis)
        elif event['type'] == 'data_access':
            analysis = self.analyze_data_access(event, analysis)
        elif event['type'] == 'payment_fraud':
            analysis = self.analyze_payment_fraud(event, analysis)
        
        return analysis
    
    def analyze_failed_login(self, event, analysis):
        """Analyze failed login events"""
        # Check for brute force
        recent_failures = self.get_recent_failures(
            event['ip_address'], 
            minutes=5
        )
        
        if len(recent_failures) >= 5:
            analysis['threat_level'] = 8
            analysis['risk_score'] = 85
            analysis['indicators'].append('brute_force_attack')
        
        # Check for credential stuffing
        if len(recent_failures) >= 10:
            analysis['threat_level'] = 9
            analysis['risk_score'] = 95
            analysis['indicators'].append('credential_stuffing')
        
        return analysis
```

#### Threat Detection

```python
# security/threat_detection.py
class ThreatDetector:
    def __init__(self):
        self.ml_models = self.load_ml_models()
        self.pattern_database = PatternDatabase()
    
    def detect_anomalies(self, user_behavior):
        """Detect anomalous user behavior"""
        anomalies = []
        
        # Behavioral analysis
        behavior_score = self.analyze_behavior_patterns(user_behavior)
        if behavior_score > 0.8:
            anomalies.append({
                'type': 'behavioral_anomaly',
                'score': behavior_score,
                'description': 'Unusual user behavior detected'
            })
        
        # Temporal analysis
        temporal_score = self.analyze_temporal_patterns(user_behavior)
        if temporal_score > 0.7:
            anomalies.append({
                'type': 'temporal_anomaly',
                'score': temporal_score,
                'description': 'Unusual access time pattern'
            })
        
        # Geographic analysis
        geo_score = self.analyze_geographic_patterns(user_behavior)
        if geo_score > 0.6:
            anomalies.append({
                'type': 'geographic_anomaly',
                'score': geo_score,
                'description': 'Unusual geographic access pattern'
            })
        
        return anomalies
    
    def analyze_behavior_patterns(self, user_behavior):
        """Analyze user behavior patterns using ML"""
        features = self.extract_behavior_features(user_behavior)
        
        # Use trained model to detect anomalies
        anomaly_score = self.ml_models['behavior_anomaly'].predict(features)
        
        return anomaly_score
    
    def extract_behavior_features(self, user_behavior):
        """Extract features for ML analysis"""
        features = {
            'login_frequency': user_behavior['login_count_per_day'],
            'avg_session_duration': user_behavior['avg_session_minutes'],
            'feature_usage': user_behavior['feature_usage_patterns'],
            'data_access_patterns': user_behavior['data_access_frequency'],
            'error_rate': user_behavior['error_rate'],
            'navigation_patterns': user_behavior['page_transition_patterns']
        }
        
        return features
```

---

## Compliance

### Regulatory Compliance

#### GDPR Compliance

```python
# compliance/gdpr.py
class GDPRCompliance:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.audit_logger = AuditLogger()
    
    def handle_data_subject_request(self, user_id, request_type):
        """Handle GDPR data subject requests"""
        if request_type == 'access':
            return self.provide_data_access(user_id)
        elif request_type == 'portability':
            return self.provide_data_portability(user_id)
        elif request_type == 'rectification':
            return self.handle_data_rectification(user_id)
        elif request_type == 'erasure':
            return self.handle_data_erasure(user_id)
        elif request_type == 'restriction':
            return self.handle_processing_restriction(user_id)
        elif request_type == 'objection':
            return self.handle_objection(user_id)
    
    def provide_data_access(self, user_id):
        """Provide access to personal data"""
        # Collect all personal data
        personal_data = {
            'user_profile': self.get_user_profile(user_id),
            'order_history': self.get_order_history(user_id),
            'payment_data': self.get_payment_data(user_id),
            'communication_history': self.get_communication_history(user_id),
            'analytics_data': self.get_analytics_data(user_id)
        }
        
        # Mask sensitive data as appropriate
        masked_data = self.mask_sensitive_data(personal_data)
        
        # Log access request
        self.audit_logger.log_gdpr_request(
            user_id=user_id,
            request_type='access',
            timestamp=datetime.utcnow()
        )
        
        return masked_data
    
    def handle_data_erasure(self, user_id):
        """Handle right to be forgotten"""
        try:
            # Anonymize user data instead of deletion for audit purposes
            self.anonymize_user_data(user_id)
            
            # Delete non-essential data
            self.delete_user_data(user_id)
            
            # Log erasure request
            self.audit_logger.log_gdpr_request(
                user_id=user_id,
                request_type='erasure',
                timestamp=datetime.utcnow()
            )
            
            return {'success': True, 'message': 'Data erased successfully'}
            
        except Exception as e:
            self.audit_logger.log_gdpr_error(user_id, str(e))
            return {'success': False, 'error': str(e)}
```

#### PCI DSS Compliance

```python
# compliance/pci_dss.py
class PCIDSSCompliance:
    def __init__(self):
        self.card_data_env = CardDataEnvironment()
        self.audit_logger = AuditLogger()
    
    def validate_pci_compliance(self):
        """Validate PCI DSS compliance"""
        compliance_checks = {
            'network_security': self.check_network_security(),
            'data_protection': self.check_data_protection(),
            'vulnerability_management': self.check_vulnerability_management(),
            'access_control': self.check_access_control(),
            'monitoring': self.check_monitoring(),
            'security_policy': self.check_security_policy()
        }
        
        overall_score = sum(checks['score'] for checks in compliance_checks.values()) / len(compliance_checks)
        
        return {
            'overall_score': overall_score,
            'compliant': overall_score >= 0.8,
            'checks': compliance_checks,
            'recommendations': self.get_pci_recommendations(compliance_checks)
        }
    
    def check_data_protection(self):
        """Check data protection requirements"""
        checks = {
            'encryption_at_rest': self.check_encryption_at_rest(),
            'encryption_in_transit': self.check_encryption_in_transit(),
            'tokenization': self.check_tokenization(),
            'access_control': self.check_access_control(),
            'key_management': self.check_key_management()
        }
        
        score = sum(1 for check in checks.values() if check['compliant']) / len(checks)
        
        return {
            'score': score,
            'compliant': score >= 0.8,
            'checks': checks
        }
    
    def check_encryption_at_rest(self):
        """Check encryption at rest"""
        # Verify card data is encrypted
        card_data_stored = self.card_data_env.get_stored_card_data()
        
        for data in card_data_stored:
            if not data['encrypted']:
                return {'compliant': False, 'issue': 'Unencrypted card data found'}
        
        return {'compliant': True}
```

---

## Security Best Practices

### Development Security

#### Secure Coding Practices

```python
# security/secure_coding.py
class SecureCodingGuidelines:
    @staticmethod
    def validate_input(input_data, validation_rules):
        """Always validate input data"""
        for field, rules in validation_rules.items():
            if field not in input_data:
                if rules.get('required', False):
                    raise ValidationError(f"Required field {field} missing")
                continue
            
            value = input_data[field]
            
            # Type validation
            if 'type' in rules:
                if not isinstance(value, rules['type']):
                    raise ValidationError(f"Field {field} has invalid type")
            
            # Length validation
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                raise ValidationError(f"Field {field} exceeds maximum length")
            
            # Pattern validation
            if 'pattern' in rules:
                if not re.match(rules['pattern'], str(value)):
                    raise ValidationError(f"Field {field} format is invalid")
        
        return True
    
    @staticmethod
    def prevent_sql_injection(query, params):
        """Use parameterized queries"""
        # Never concatenate user input into SQL queries
        # ✅ Good: Use parameter binding
        result = db.session.execute(text(query), params)
        
        # ❌ Bad: String concatenation
        # bad_query = f"SELECT * FROM users WHERE name = '{name}'"
        
        return result
    
    @staticmethod
    def prevent_xss(user_input):
        """Prevent XSS attacks"""
        # Always escape user input for HTML context
        from markupsafe import escape
        escaped_input = escape(user_input)
        
        # For rich content, use HTML sanitization
        from bleach import clean
        sanitized_input = clean(user_input, tags=['b', 'i', 'u', 'strong'], strip=True)
        
        return escaped_input
    
    @staticmethod
    def secure_file_upload(file):
        """Secure file upload handling"""
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError("File type not allowed")
        
        # Validate file size
        max_size = 5 * 1024 * 1024  # 5MB
        if file.content_length > max_size:
            raise ValidationError("File too large")
        
        # Generate secure filename
        import uuid
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        
        # Store file securely
        secure_path = os.path.join('uploads', filename)
        file.save(secure_path)
        
        return secure_path
```

### Operational Security

#### Security Operations

```python
# security/operations.py
class SecurityOperations:
    def __init__(self):
        self.backup_manager = BackupManager()
        self.patch_manager = PatchManager()
        self.audit_manager = AuditManager()
    
    def perform_security_backup(self):
        """Perform secure backup with encryption"""
        # Create backup
        backup_data = self.collect_backup_data()
        
        # Encrypt backup
        encrypted_backup = self.encryption_service.encrypt(json.dumps(backup_data))
        
        # Store with integrity check
        backup_file = {
            'data': encrypted_backup,
            'checksum': self.calculate_checksum(encrypted_backup),
            'timestamp': datetime.utcnow(),
            'version': '2.0.0'
        }
        
        backup_path = f"backups/secure_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.enc"
        
        with open(backup_path, 'wb') as f:
            f.write(json.dumps(backup_file).encode())
        
        # Verify backup integrity
        if self.verify_backup_integrity(backup_path):
            self.audit_manager.log_security_operation(
                'backup_created',
                {'backup_path': backup_path, 'size': len(encrypted_backup)}
            )
            return True
        
        return False
    
    def perform_security_patch(self, patch_info):
        """Apply security patches safely"""
        # Verify patch signature
        if not self.verify_patch_signature(patch_info):
            raise SecurityError("Invalid patch signature")
        
        # Create system backup before patching
        if not self.backup_manager.create_system_backup():
            raise SecurityError("Failed to create backup before patching")
        
        try:
            # Apply patch in maintenance mode
            self.enable_maintenance_mode()
            
            # Apply patch
            patch_result = self.patch_manager.apply_patch(patch_info)
            
            if patch_result['success']:
                # Verify system integrity
                if self.verify_system_integrity():
                    self.audit_manager.log_security_operation(
                        'patch_applied',
                        {'patch_version': patch_info['version'], 'success': True}
                    )
                    return True
                else:
                    # Rollback patch
                    self.patch_manager.rollback_patch(patch_info)
                    raise SecurityError("System integrity check failed after patch")
            else:
                raise SecurityError(f"Patch application failed: {patch_result['error']}")
                
        except Exception as e:
            # Rollback on any error
            self.patch_manager.rollback_patch(patch_info)
            raise e
        finally:
            self.disable_maintenance_mode()
```

---

## Incident Response

### Security Incident Response

#### Incident Management

```python
# security/incident_response.py
class IncidentResponseManager:
    def __init__(self):
        self.incident_store = IncidentStore()
        self.notification_service = NotificationService()
        self.forensics_service = ForensicsService()
    
    def handle_security_incident(self, incident_data):
        """Handle security incident according to response plan"""
        # Create incident record
        incident = {
            'id': str(uuid.uuid4()),
            'type': incident_data['type'],
            'severity': incident_data['severity'],
            'description': incident_data['description'],
            'affected_assets': incident_data.get('affected_assets', []),
            'timeline': [],
            'status': 'detected',
            'created_at': datetime.utcnow(),
            'assigned_to': None,
            'resolution': None
        }
        
        self.incident_store.create_incident(incident)
        
        # Initialize response based on severity
        if incident['severity'] in ['critical', 'high']:
            self.initiate_emergency_response(incident)
        else:
            self.initiate_standard_response(incident)
        
        return incident
    
    def initiate_emergency_response(self, incident):
        """Initiate emergency response for critical incidents"""
        # 1. Immediate containment
        self.contain_incident(incident)
        
        # 2. Notify stakeholders
        self.notify_stakeholders(incident, priority='urgent')
        
        # 3. Preserve evidence
        self.preserve_evidence(incident)
        
        # 4. Activate incident response team
        self.activate_response_team(incident)
        
        # 5. Document timeline
        self.add_timeline_event(incident, 'emergency_response_initiated')
    
    def contain_incident(self, incident):
        """Contain security incident"""
        containment_actions = []
        
        if incident['type'] == 'data_breach':
            # Isolate affected systems
            self.isolate_affected_systems(incident['affected_assets'])
            containment_actions.append('systems_isolated')
            
            # Block suspicious IPs
            self.block_suspicious_ips(incident)
            containment_actions.append('ips_blocked')
            
            # Force password resets
            self.force_password_resets(incident)
            containment_actions.append('password_resets_forced')
        
        elif incident['type'] == 'ransomware':
            # Disconnect affected systems
            self.disconnect_affected_systems(incident['affected_assets'])
            containment_actions.append('systems_disconnected')
            
            # Activate backup systems
            self.activate_backup_systems()
            containment_actions.append('backup_systems_activated')
        
        # Update incident with containment actions
        self.add_timeline_event(incident, 'containment_completed', {
            'actions': containment_actions
        })
```

---

## Security Testing

### Security Testing Framework

#### Automated Security Testing

```python
# security/testing.py
class SecurityTestingFramework:
    def __init__(self):
        self.test_results = []
        self.vulnerability_scanner = VulnerabilityScanner()
        self.penetration_tester = PenetrationTester()
    
    def run_security_tests(self, target_url):
        """Run comprehensive security tests"""
        test_suite = {
            'authentication_tests': self.test_authentication(target_url),
            'authorization_tests': self.test_authorization(target_url),
            'input_validation_tests': self.test_input_validation(target_url),
            'session_tests': self.test_session_security(target_url),
            'xss_tests': self.test_xss_vulnerabilities(target_url),
            'sql_injection_tests': self.test_sql_injection(target_url),
            'csrf_tests': self.test_csrf_protection(target_url),
            'security_headers_tests': self.test_security_headers(target_url),
            'encryption_tests': self.test_encryption(target_url)
        }
        
        # Analyze results
        vulnerabilities = self.analyze_test_results(test_suite)
        
        # Generate report
        report = self.generate_security_report(test_suite, vulnerabilities)
        
        return {
            'test_results': test_suite,
            'vulnerabilities': vulnerabilities,
            'report': report,
            'overall_score': self.calculate_security_score(test_suite)
        }
    
    def test_authentication(self, target_url):
        """Test authentication security"""
        tests = {
            'weak_passwords': self.test_weak_passwords(target_url),
            'brute_force': self.test_brute_force_protection(target_url),
            'account_lockout': self.test_account_lockout(target_url),
            'mfa_bypass': self.test_mfa_bypass(target_url),
            'session_fixation': self.test_session_fixation(target_url)
        }
        
        return tests
    
    def test_sql_injection(self, target_url):
        """Test for SQL injection vulnerabilities"""
        injection_payloads = [
            "' OR '1'='1",
            "' UNION SELECT NULL--",
            "'; DROP TABLE users--",
            "' OR 1=1--",
            "admin'--"
        ]
        
        results = {}
        
        for endpoint in ['/login', '/api/customers', '/api/orders']:
            for payload in injection_payloads:
                try:
                    response = requests.post(
                        f"{target_url}{endpoint}",
                        data={'username': payload, 'password': 'test'},
                        timeout=10
                    )
                    
                    # Check for SQL error messages
                    if any(error in response.text.lower() for error in [
                        'sql', 'mysql', 'postgresql', 'oracle', 'syntax error'
                    ]):
                        results[f"{endpoint}_{payload}"] = {
                            'vulnerable': True,
                            'payload': payload,
                            'response': response.text[:200]
                        }
                    else:
                        results[f"{endpoint}_{payload}"] = {
                            'vulnerable': False,
                            'payload': payload
                        }
                        
                except Exception as e:
                    results[f"{endpoint}_{payload}"] = {
                        'error': str(e),
                        'payload': payload
                    }
        
        return results
```

### Continuous Security Monitoring

#### Security Metrics

```python
# security/metrics.py
class SecurityMetrics:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_thresholds = {
            'failed_login_rate': 0.1,  # 10%
            'suspicious_activity_rate': 0.05,  # 5%
            'vulnerability_count': 0,  # Any vulnerabilities
            'security_incident_rate': 0.01  # 1%
        }
    
    def collect_security_metrics(self):
        """Collect and analyze security metrics"""
        metrics = {
            'authentication_metrics': self.get_authentication_metrics(),
            'authorization_metrics': self.get_authorization_metrics(),
            'vulnerability_metrics': self.get_vulnerability_metrics(),
            'incident_metrics': self.get_incident_metrics(),
            'compliance_metrics': self.get_compliance_metrics()
        }
        
        # Check for alerts
        alerts = self.check_metric_alerts(metrics)
        
        if alerts:
            self.send_security_alerts(alerts)
        
        return metrics
    
    def get_authentication_metrics(self):
        """Get authentication-related metrics"""
        time_period = datetime.utcnow() - timedelta(hours=24)
        
        total_logins = self.metrics_collector.count_events(
            'login_attempt', 
            time_period
        )
        
        failed_logins = self.metrics_collector.count_events(
            'failed_login', 
            time_period
        )
        
        unique_ips = self.metrics_collector.count_unique_ips(
            'login_attempt', 
            time_period
        )
        
        return {
            'total_login_attempts': total_logins,
            'failed_login_attempts': failed_logins,
            'success_rate': (total_logins - failed_logins) / total_logins if total_logins > 0 else 0,
            'failed_login_rate': failed_logins / total_logins if total_logins > 0 else 0,
            'unique_ip_addresses': unique_ips,
            'brute_force_attempts': self.detect_brute_force_patterns(time_period)
        }
```

---

**Version**: 2.0.0 Security Guide  
**Last Updated**: December 2024  
**Documentation**: Flask POS Security Team