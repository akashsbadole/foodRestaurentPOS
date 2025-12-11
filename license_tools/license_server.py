#!/usr/bin/env python3
"""
License Server for POS MVP application
Simple license server for validation and management
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, g
from flask_cors import CORS

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.license_crypto import LicenseCrypto
from src.utils.hardware_fingerprint import HardwareFingerprint
from src.models.license import License


class LicenseServer:
    """
    Simple license server for validation and management
    """
    
    def __init__(self, database_path: str = "license_server.db", 
                 host: str = "0.0.0.0", port: int = 8080, debug: bool = False):
        """
        Initialize license server
        
        Args:
            database_path: Path to SQLite database
            host: Server host
            port: Server port
            debug: Enable debug mode
        """
        self.database_path = database_path
        self.host = host
        self.port = port
        self.debug = debug
        
        # Initialize components
        self.license_crypto = LicenseCrypto()
        self.hardware_fingerprint = HardwareFingerprint()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Configure app
        self.app.config['SECRET_KEY'] = os.urandom(24).hex()
        self.app.config['DATABASE'] = database_path
        
        # Register routes
        self._register_routes()
        
        # Initialize database
        self._init_database()
    
    def _register_routes(self):
        """Register Flask routes"""
        
        @self.app.route('/api/v1/validate', methods=['POST'])
        def validate_license():
            """Validate license endpoint"""
            try:
                # Get request data
                request_data = request.get_json()
                if not request_data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }), 400
                
                # Extract required fields
                license_key = request_data.get('license_key')
                activation_id = request_data.get('activation_id')
                hardware_fingerprint = request_data.get('hardware_fingerprint')
                
                if not license_key or not activation_id:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required fields: license_key, activation_id'
                    }), 400
                
                # Verify request signature
                if not self._verify_request_signature(request_data):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request signature'
                    }), 401
                
                # Perform validation
                validation_result = self._validate_license(
                    license_key, activation_id, hardware_fingerprint
                )
                
                # Sign response
                response_data = {
                    'status': validation_result['status'],
                    'data': validation_result.get('data', {}),
                    'timestamp': datetime.now().isoformat(),
                    'next_validation': validation_result.get('next_validation')
                }
                
                signed_response = self._sign_response(response_data)
                return jsonify(signed_response)
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Validation error: {str(e)}'
                }), 500
        
        @self.app.route('/api/v1/activate', methods=['POST'])
        def activate_license():
            """Activate license endpoint"""
            try:
                # Get request data
                request_data = request.get_json()
                if not request_data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }), 400
                
                # Extract required fields
                license_key = request_data.get('license_key')
                activation_code = request_data.get('activation_code')
                hardware_fingerprint = request_data.get('hardware_fingerprint')
                
                if not license_key or not hardware_fingerprint:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required fields: license_key, hardware_fingerprint'
                    }), 400
                
                # Verify request signature
                if not self._verify_request_signature(request_data):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request signature'
                    }), 401
                
                # Perform activation
                activation_result = self._activate_license(
                    license_key, activation_code, hardware_fingerprint
                )
                
                # Sign response
                response_data = {
                    'status': activation_result['status'],
                    'data': activation_result.get('data', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                signed_response = self._sign_response(response_data)
                return jsonify(signed_response)
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Activation error: {str(e)}'
                }), 500
        
        @self.app.route('/api/v1/heartbeat', methods=['POST'])
        def heartbeat():
            """Heartbeat endpoint"""
            try:
                # Get request data
                request_data = request.get_json()
                if not request_data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }), 400
                
                # Extract required fields
                license_key = request_data.get('license_key')
                activation_id = request_data.get('activation_id')
                
                if not license_key or not activation_id:
                    return jsonify({
                        'status': 'error',
                        'message': 'Missing required fields: license_key, activation_id'
                    }), 400
                
                # Verify request signature
                if not self._verify_request_signature(request_data):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request signature'
                    }), 401
                
                # Process heartbeat
                heartbeat_result = self._process_heartbeat(
                    license_key, activation_id, request_data.get('usage_data', {})
                )
                
                # Sign response
                response_data = {
                    'status': heartbeat_result['status'],
                    'data': heartbeat_result.get('data', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                signed_response = self._sign_response(response_data)
                return jsonify(signed_response)
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Heartbeat error: {str(e)}'
                }), 500
        
        @self.app.route('/api/v1/blacklist', methods=['POST'])
        def check_blacklist():
            """Check blacklist endpoint"""
            try:
                # Get request data
                request_data = request.get_json()
                if not request_data:
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request data'
                    }), 400
                
                # Extract fields
                license_key = request_data.get('license_key')
                hardware_fingerprint = request_data.get('hardware_fingerprint')
                
                if not license_key and not hardware_fingerprint:
                    return jsonify({
                        'status': 'error',
                        'message': 'At least one of license_key or hardware_fingerprint required'
                    }), 400
                
                # Verify request signature
                if not self._verify_request_signature(request_data):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid request signature'
                    }), 401
                
                # Check blacklist
                blacklist_result = self._check_blacklist(license_key, hardware_fingerprint)
                
                # Sign response
                response_data = {
                    'status': blacklist_result['status'],
                    'data': blacklist_result.get('data', {}),
                    'timestamp': datetime.now().isoformat()
                }
                
                signed_response = self._sign_response(response_data)
                return jsonify(signed_response)
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Blacklist check error: {str(e)}'
                }), 500
        
        @self.app.route('/api/v1/licenses', methods=['GET'])
        def list_licenses():
            """List licenses endpoint (admin only)"""
            try:
                # Check admin key
                admin_key = request.headers.get('X-Admin-Key')
                if not admin_key or admin_key != self._get_admin_key():
                    return jsonify({
                        'status': 'error',
                        'message': 'Unauthorized'
                    }), 401
                
                # Get query parameters
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 50))
                status = request.args.get('status')
                
                # List licenses
                licenses = self._list_licenses(page, per_page, status)
                
                return jsonify({
                    'status': 'success',
                    'data': licenses,
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'List licenses error: {str(e)}'
                }), 500
        
        @self.app.route('/api/v1/licenses/<license_key>/revoke', methods=['POST'])
        def revoke_license(license_key):
            """Revoke license endpoint (admin only)"""
            try:
                # Check admin key
                admin_key = request.headers.get('X-Admin-Key')
                if not admin_key or admin_key != self._get_admin_key():
                    return jsonify({
                        'status': 'error',
                        'message': 'Unauthorized'
                    }), 401
                
                # Revoke license
                revoke_result = self._revoke_license(license_key)
                
                return jsonify({
                    'status': revoke_result['status'],
                    'message': revoke_result.get('message', ''),
                    'timestamp': datetime.now().isoformat()
                })
            
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': f'Revoke license error: {str(e)}'
                }), 500
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Create licenses table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS licenses (
                        license_key TEXT PRIMARY KEY,
                        license_id TEXT UNIQUE NOT NULL,
                        customer_name TEXT,
                        customer_email TEXT,
                        license_type TEXT NOT NULL,
                        features TEXT,
                        issued_date TEXT NOT NULL,
                        expiry_date TEXT NOT NULL,
                        machine_bindings TEXT,
                        signature TEXT NOT NULL,
                        validation_hash TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        activation_count INTEGER DEFAULT 0,
                        max_activations INTEGER DEFAULT 3,
                        server_validation_token TEXT,
                        offline_grace_period_days INTEGER DEFAULT 30,
                        is_trial BOOLEAN DEFAULT 0,
                        trial_days_used INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create activations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activations (
                        activation_id TEXT PRIMARY KEY,
                        license_key TEXT NOT NULL,
                        hardware_fingerprint TEXT,
                        activation_type TEXT NOT NULL,
                        activated_at TEXT NOT NULL,
                        last_validated TEXT,
                        validation_count INTEGER DEFAULT 0,
                        offline_grace_expires TEXT,
                        server_response TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (license_key) REFERENCES licenses (license_key)
                    )
                ''')
                
                # Create blacklist table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blacklist (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        license_key TEXT,
                        hardware_fingerprint TEXT,
                        reason TEXT,
                        blacklisted_by TEXT,
                        blacklisted_at TEXT NOT NULL,
                        expires_at TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create usage_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usage_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        license_key TEXT NOT NULL,
                        activation_id TEXT NOT NULL,
                        usage_data TEXT,
                        logged_at TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses (license_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_licenses_status ON licenses (status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_activations_key ON activations (license_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklist_key ON blacklist (license_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_blacklist_hw ON blacklist (hardware_fingerprint)')
                
                conn.commit()
        except Exception as e:
            print(f"Error initializing database: {str(e)}")
            raise
    
    def _verify_request_signature(self, request_data: Dict[str, Any]) -> bool:
        """Verify request signature"""
        try:
            signature = request_data.pop('signature', None)
            if not signature:
                return False
            
            # Create verification data
            verify_data = {
                'license_key': request_data.get('license_key'),
                'activation_id': request_data.get('activation_id'),
                'hardware_fingerprint': request_data.get('hardware_fingerprint'),
                'timestamp': request_data.get('timestamp'),
                'validation_data': request_data.get('validation_data', {}),
                'activation_data': request_data.get('activation_data', {}),
                'usage_data': request_data.get('usage_data', {})
            }
            
            # Convert to JSON
            verify_json = json.dumps(verify_data, sort_keys=True)
            
            # Verify signature
            return self.license_crypto.verify_signature(verify_json, signature)
        except Exception as e:
            print(f"Error verifying request signature: {str(e)}")
            return False
    
    def _sign_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sign response data"""
        try:
            # Convert to JSON
            response_json = json.dumps(response_data, sort_keys=True)
            
            # Generate signature
            signature = self.license_crypto.sign_data(response_json)
            
            # Add signature to response
            response_data['signature'] = signature
            return response_data
        except Exception as e:
            print(f"Error signing response: {str(e)}")
            return response_data
    
    def _validate_license(self, license_key: str, activation_id: str,
                        hardware_fingerprint: str) -> Dict[str, Any]:
        """Validate license"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get license
                cursor.execute('''
                    SELECT * FROM licenses WHERE license_key = ?
                ''', (license_key,))
                license_row = cursor.fetchone()
                
                if not license_row:
                    return {
                        'status': 'invalid',
                        'message': 'License not found'
                    }
                
                # Check license status
                if license_row['status'] != 'active':
                    return {
                        'status': license_row['status'],
                        'message': f'License is {license_row["status"]}'
                    }
                
                # Check expiry
                expiry_date = datetime.fromisoformat(license_row['expiry_date'])
                if datetime.now() > expiry_date:
                    return {
                        'status': 'expired',
                        'message': 'License has expired'
                    }
                
                # Get activation
                cursor.execute('''
                    SELECT * FROM activations WHERE activation_id = ?
                ''', (activation_id,))
                activation_row = cursor.fetchone()
                
                if not activation_row:
                    return {
                        'status': 'invalid',
                        'message': 'Activation not found'
                    }
                
                # Check hardware binding
                machine_bindings = json.loads(license_row['machine_bindings'] or '[]')
                if machine_bindings and hardware_fingerprint not in machine_bindings:
                    return {
                        'status': 'invalid',
                        'message': 'Hardware fingerprint mismatch'
                    }
                
                # Check blacklist
                cursor.execute('''
                    SELECT * FROM blacklist 
                    WHERE (license_key = ? OR hardware_fingerprint = ?) 
                    AND is_active = 1 
                    AND (expires_at IS NULL OR expires_at > ?)
                ''', (license_key, hardware_fingerprint, datetime.now().isoformat()))
                blacklist_row = cursor.fetchone()
                
                if blacklist_row:
                    return {
                        'status': 'blacklisted',
                        'message': 'License is blacklisted'
                    }
                
                # Update activation validation
                cursor.execute('''
                    UPDATE activations 
                    SET last_validated = ?, validation_count = validation_count + 1
                    WHERE activation_id = ?
                ''', (datetime.now().isoformat(), activation_id))
                
                conn.commit()
                
                return {
                    'status': 'success',
                    'data': {
                        'license_type': license_row['license_type'],
                        'features': json.loads(license_row['features'] or '[]'),
                        'expiry_date': license_row['expiry_date'],
                        'next_validation': (datetime.now() + timedelta(hours=24)).isoformat()
                    }
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Validation error: {str(e)}'
            }
    
    def _activate_license(self, license_key: str, activation_code: str,
                        hardware_fingerprint: str) -> Dict[str, Any]:
        """Activate license"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get license
                cursor.execute('''
                    SELECT * FROM licenses WHERE license_key = ?
                ''', (license_key,))
                license_row = cursor.fetchone()
                
                if not license_row:
                    return {
                        'status': 'invalid',
                        'message': 'License not found'
                    }
                
                # Check license status
                if license_row['status'] != 'active':
                    return {
                        'status': license_row['status'],
                        'message': f'License is {license_row["status"]}'
                    }
                
                # Check expiry
                expiry_date = datetime.fromisoformat(license_row['expiry_date'])
                if datetime.now() > expiry_date:
                    return {
                        'status': 'expired',
                        'message': 'License has expired'
                    }
                
                # Check activation limit
                if license_row['activation_count'] >= license_row['max_activations']:
                    return {
                        'status': 'invalid',
                        'message': 'Maximum activation limit reached'
                    }
                
                # Check existing activations
                cursor.execute('''
                    SELECT COUNT(*) as count FROM activations WHERE license_key = ?
                ''', (license_key,))
                activation_count = cursor.fetchone()['count']
                
                if activation_count >= license_row['max_activations']:
                    return {
                        'status': 'invalid',
                        'message': 'Maximum activation limit reached'
                    }
                
                # Create activation
                activation_id = f"ACT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
                
                cursor.execute('''
                    INSERT INTO activations (
                        activation_id, license_key, hardware_fingerprint,
                        activation_type, activated_at
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    activation_id, license_key, hardware_fingerprint,
                    'online', datetime.now().isoformat()
                ))
                
                # Update license activation count
                cursor.execute('''
                    UPDATE licenses SET activation_count = activation_count + 1
                    WHERE license_key = ?
                ''', (license_key,))
                
                conn.commit()
                
                return {
                    'status': 'success',
                    'data': {
                        'activation_id': activation_id,
                        'license_type': license_row['license_type'],
                        'features': json.loads(license_row['features'] or '[]'),
                        'expiry_date': license_row['expiry_date']
                    }
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Activation error: {str(e)}'
            }
    
    def _process_heartbeat(self, license_key: str, activation_id: str,
                         usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process heartbeat"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Log usage data
                cursor.execute('''
                    INSERT INTO usage_logs (
                        license_key, activation_id, usage_data, logged_at
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    license_key, activation_id, json.dumps(usage_data),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
                return {
                    'status': 'success',
                    'data': {
                        'logged_at': datetime.now().isoformat()
                    }
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Heartbeat error: {str(e)}'
            }
    
    def _check_blacklist(self, license_key: str, hardware_fingerprint: str) -> Dict[str, Any]:
        """Check blacklist"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check blacklist
                cursor.execute('''
                    SELECT * FROM blacklist 
                    WHERE (license_key = ? OR hardware_fingerprint = ?) 
                    AND is_active = 1 
                    AND (expires_at IS NULL OR expires_at > ?)
                ''', (license_key, hardware_fingerprint, datetime.now().isoformat()))
                blacklist_row = cursor.fetchone()
                
                if blacklist_row:
                    return {
                        'status': 'blacklisted',
                        'data': {
                            'reason': blacklist_row['reason'],
                            'blacklisted_at': blacklist_row['blacklisted_at'],
                            'expires_at': blacklist_row['expires_at']
                        }
                    }
                
                return {
                    'status': 'success',
                    'data': {}
                }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Blacklist check error: {str(e)}'
            }
    
    def _list_licenses(self, page: int, per_page: int, status: str = None) -> Dict[str, Any]:
        """List licenses"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Build query
                query = 'SELECT * FROM licenses'
                params = []
                
                if status:
                    query += ' WHERE status = ?'
                    params.append(status)
                
                query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
                params.extend([per_page, (page - 1) * per_page])
                
                cursor.execute(query, params)
                licenses = cursor.fetchall()
                
                # Convert to list of dicts
                license_list = []
                for license_row in licenses:
                    license_dict = dict(license_row)
                    license_list.append(license_dict)
                
                # Get total count
                count_query = 'SELECT COUNT(*) as total FROM licenses'
                count_params = []
                
                if status:
                    count_query += ' WHERE status = ?'
                    count_params.append(status)
                
                cursor.execute(count_query, count_params)
                total = cursor.fetchone()['total']
                
                return {
                    'licenses': license_list,
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': total,
                        'pages': (total + per_page - 1) // per_page
                    }
                }
        except Exception as e:
            return {
                'error': f'List licenses error: {str(e)}'
            }
    
    def _revoke_license(self, license_key: str) -> Dict[str, Any]:
        """Revoke license"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.cursor()
                
                # Update license status
                cursor.execute('''
                    UPDATE licenses SET status = 'revoked', updated_at = ?
                    WHERE license_key = ?
                ''', (datetime.now().isoformat(), license_key))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    return {
                        'status': 'success',
                        'message': 'License revoked successfully'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'License not found'
                    }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Revoke license error: {str(e)}'
            }
    
    def _get_admin_key(self) -> str:
        """Get admin key from environment or generate one"""
        admin_key = os.environ.get('LICENSE_SERVER_ADMIN_KEY')
        if not admin_key:
            # Generate a default admin key (should be changed in production)
            admin_key = hashlib.sha256(b'posmvp_admin_2024').hexdigest()
        return admin_key
    
    def run(self):
        """Run the license server"""
        print(f"Starting license server on {self.host}:{self.port}")
        print(f"Database: {self.database_path}")
        print(f"Debug mode: {self.debug}")
        
        self.app.run(host=self.host, port=self.port, debug=self.debug)


def main():
    """Command-line interface for license server"""
    parser = argparse.ArgumentParser(description='POS MVP License Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--database', default='license_server.db', help='Database path')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize database and exit')
    
    args = parser.parse_args()
    
    # Initialize server
    server = LicenseServer(args.database, args.host, args.port, args.debug)
    
    # Initialize database and exit if requested
    if args.init_db:
        print("Database initialized successfully")
        return
    
    # Run server
    server.run()


if __name__ == "__main__":
    main()