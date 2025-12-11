#!/usr/bin/env python3
"""
License Key Generator for POS MVP application
Comprehensive utility for generating cryptographically secure license keys
"""

import os
import sys
import json
import argparse
import secrets
import hashlib
import base64
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.license_crypto import LicenseCrypto
from src.utils.hardware_fingerprint import HardwareFingerprint
from src.models.license import License


class LicenseKeyGenerator:
    """
    Comprehensive license key generator with support for multiple license types
    and cryptographic security features
    """
    
    # License types
    TYPE_TRIAL = "trial"
    TYPE_STANDARD = "standard"
    TYPE_PROFESSIONAL = "professional"
    TYPE_ENTERPRISE = "enterprise"
    
    # Export formats
    FORMAT_JSON = "json"
    FORMAT_CSV = "csv"
    FORMAT_TEXT = "text"
    FORMAT_BINARY = "binary"
    
    def __init__(self, algorithm: str = "RSA"):
        """
        Initialize license key generator
        
        Args:
            algorithm: Cryptographic algorithm (RSA or ECC)
        """
        self.license_crypto = LicenseCrypto(algorithm)
        self.hardware_fingerprint = HardwareFingerprint()
        self.license = License()
        
        # License templates
        self.license_templates = {
            self.TYPE_TRIAL: {
                'maintenance_days': 30,
                'max_activations': 1,
                'offline_grace_period_days': 7,
                'features': License.FEATURES.get(self.TYPE_TRIAL, [])
            },
            self.TYPE_STANDARD: {
                'maintenance_days': 365,
                'max_activations': 3,
                'offline_grace_period_days': 30,
                'features': License.FEATURES.get(self.TYPE_STANDARD, [])
            },
            self.TYPE_PROFESSIONAL: {
                'maintenance_days': 365,
                'max_activations': 5,
                'offline_grace_period_days': 45,
                'features': License.FEATURES.get(self.TYPE_PROFESSIONAL, [])
            },
            self.TYPE_ENTERPRISE: {
                'maintenance_days': 365,
                'max_activations': 10,
                'offline_grace_period_days': 60,
                'features': License.FEATURES.get(self.TYPE_ENTERPRISE, [])
            }
        }
    
    def generate_license_key(self, license_type: str, customer_data: Dict[str, Any],
                          hardware_binding: bool = False, custom_features: List[str] = None,
                          expiry_days: int = None, activation_code: str = None) -> Dict[str, Any]:
        """
        Generate a single license key
        
        Args:
            license_type: Type of license to generate
            customer_data: Customer information
            hardware_binding: Whether to bind to hardware fingerprint
            custom_features: Custom feature list (overrides template)
            expiry_days: Custom expiry in days (overrides template)
            activation_code: Optional activation code
            
        Returns:
            Dictionary with generated license data
        """
        try:
            # Validate license type
            if license_type not in self.license_templates:
                raise ValueError(f"Invalid license type: {license_type}")
            
            # Get license template
            template = self.license_templates[license_type].copy()
            
            # Prepare license data
            license_data = {
                'license_id': self._generate_license_id(),
                'license_type': license_type,
                'customer_name': customer_data.get('name', ''),
                'customer_email': customer_data.get('email', ''),
                'customer_company': customer_data.get('company', ''),
                'customer_phone': customer_data.get('phone', ''),
                'max_activations': customer_data.get('max_activations', template['max_activations']),
                'offline_grace_period_days': customer_data.get('offline_grace_period_days', 
                                                             template['offline_grace_period_days']),
                'features': custom_features or template['features'],
                'machine_bindings': []
            }
            
            # Set expiry
            if expiry_days:
                license_data['maintenance_days'] = expiry_days
            else:
                license_data['maintenance_days'] = template['maintenance_days']
            
            # Add hardware binding if requested
            if hardware_binding:
                fingerprint_data = self.hardware_fingerprint.generate_fingerprint(
                    HardwareFingerprint.METHOD_ADVANCED
                )
                license_data['machine_bindings'] = [fingerprint_data.get('hash', '')]
            
            # Add activation code if provided
            if activation_code:
                license_data['activation_code'] = activation_code
            
            # Create license
            if not self.license.create_license(license_data):
                raise Exception("Failed to create license")
            
            # Generate license package
            license_package = {
                'license_key': self.license._license_key,
                'license_data': self.license.export_license_data(),
                'signature': self.license._signature,
                'validation_hash': self.license._validation_hash,
                'generation_info': {
                    'algorithm': self.license_crypto.algorithm,
                    'generated_at': datetime.now().isoformat(),
                    'generator_version': '1.0.0',
                    'hardware_binding': hardware_binding,
                    'activation_code': activation_code is not None
                }
            }
            
            return license_package
        except Exception as e:
            print(f"Error generating license key: {str(e)}")
            return {}
    
    def generate_batch_keys(self, license_type: str, customer_list: List[Dict[str, Any]],
                         hardware_binding: bool = False, custom_features: List[str] = None,
                         expiry_days: int = None, activation_code: str = None) -> List[Dict[str, Any]]:
        """
        Generate multiple license keys in batch
        
        Args:
            license_type: Type of license to generate
            customer_list: List of customer information dictionaries
            hardware_binding: Whether to bind to hardware fingerprint
            custom_features: Custom feature list (overrides template)
            expiry_days: Custom expiry in days (overrides template)
            activation_code: Optional activation code
            
        Returns:
            List of generated license packages
        """
        batch_licenses = []
        
        for i, customer_data in enumerate(customer_list):
            print(f"Generating license {i+1}/{len(customer_list)} for {customer_data.get('name', 'Unknown')}")
            
            license_package = self.generate_license_key(
                license_type, customer_data, hardware_binding, 
                custom_features, expiry_days, activation_code
            )
            
            if license_package:
                batch_licenses.append(license_package)
            else:
                print(f"Failed to generate license for {customer_data.get('name', 'Unknown')}")
        
        return batch_licenses
    
    def export_licenses(self, licenses: List[Dict[str, Any]], output_file: str, 
                       format_type: str = FORMAT_JSON) -> bool:
        """
        Export licenses to specified format
        
        Args:
            licenses: List of license packages to export
            output_file: Output file path
            format_type: Export format (json, csv, text, binary)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            if format_type == self.FORMAT_JSON:
                return self._export_json(licenses, output_file)
            elif format_type == self.FORMAT_CSV:
                return self._export_csv(licenses, output_file)
            elif format_type == self.FORMAT_TEXT:
                return self._export_text(licenses, output_file)
            elif format_type == self.FORMAT_BINARY:
                return self._export_binary(licenses, output_file)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
        except Exception as e:
            print(f"Error exporting licenses: {str(e)}")
            return False
    
    def _export_json(self, licenses: List[Dict[str, Any]], output_file: str) -> bool:
        """Export licenses to JSON format"""
        try:
            export_data = {
                'export_info': {
                    'total_licenses': len(licenses),
                    'exported_at': datetime.now().isoformat(),
                    'generator_version': '1.0.0',
                    'algorithm': self.license_crypto.algorithm
                },
                'licenses': licenses
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
            return False
    
    def _export_csv(self, licenses: List[Dict[str, Any]], output_file: str) -> bool:
        """Export licenses to CSV format"""
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                header = [
                    'License Key', 'License ID', 'Customer Name', 'Customer Email',
                    'License Type', 'Issued Date', 'Expiry Date', 'Features',
                    'Max Activations', 'Hardware Binding', 'Signature'
                ]
                writer.writerow(header)
                
                # Write license data
                for license_pkg in licenses:
                    license_data = license_pkg.get('license_data', {})
                    features_str = ';'.join(license_data.get('features', []))
                    hw_binding = 'Yes' if license_data.get('machine_bindings') else 'No'
                    
                    row = [
                        license_pkg.get('license_key', ''),
                        license_data.get('license_id', ''),
                        license_data.get('customer_name', ''),
                        license_data.get('customer_email', ''),
                        license_data.get('license_type', ''),
                        license_data.get('issued_date', ''),
                        license_data.get('expiry_date', ''),
                        features_str,
                        license_data.get('max_activations', ''),
                        hw_binding,
                        license_pkg.get('signature', '')
                    ]
                    writer.writerow(row)
            
            return True
        except Exception as e:
            print(f"Error exporting to CSV: {str(e)}")
            return False
    
    def _export_text(self, licenses: List[Dict[str, Any]], output_file: str) -> bool:
        """Export licenses to human-readable text format"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("POS MVP License Keys Export\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Licenses: {len(licenses)}\n")
                f.write(f"Exported At: {datetime.now().isoformat()}\n")
                f.write(f"Algorithm: {self.license_crypto.algorithm}\n\n")
                
                for i, license_pkg in enumerate(licenses, 1):
                    f.write(f"License #{i}\n")
                    f.write("-" * 30 + "\n")
                    
                    license_data = license_pkg.get('license_data', {})
                    
                    f.write(f"License Key: {license_pkg.get('license_key', '')}\n")
                    f.write(f"License ID: {license_data.get('license_id', '')}\n")
                    f.write(f"Customer: {license_data.get('customer_name', '')}\n")
                    f.write(f"Email: {license_data.get('customer_email', '')}\n")
                    f.write(f"Type: {license_data.get('license_type', '')}\n")
                    f.write(f"Issued: {license_data.get('issued_date', '')}\n")
                    f.write(f"Expires: {license_data.get('expiry_date', '')}\n")
                    f.write(f"Max Activations: {license_data.get('max_activations', '')}\n")
                    
                    features = license_data.get('features', [])
                    f.write(f"Features: {', '.join(features)}\n")
                    
                    hw_binding = license_data.get('machine_bindings')
                    f.write(f"Hardware Binding: {'Yes' if hw_binding else 'No'}\n")
                    
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error exporting to text: {str(e)}")
            return False
    
    def _export_binary(self, licenses: List[Dict[str, Any]], output_file: str) -> bool:
        """Export licenses to encrypted binary format"""
        try:
            # Convert to JSON first
            json_data = json.dumps(licenses, separators=(',', ':'))
            
            # Encrypt with license crypto
            encrypted_data, key = self.license_crypto.encrypt_data(json_data)
            
            # Create binary package
            binary_package = {
                'version': '1.0',
                'algorithm': self.license_crypto.algorithm,
                'license_count': len(licenses),
                'encrypted_data': encrypted_data,
                'encryption_key': key,
                'export_timestamp': datetime.now().isoformat()
            }
            
            # Write as JSON (could also write as raw binary)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(binary_package, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting to binary: {str(e)}")
            return False
    
    def _generate_license_id(self) -> str:
        """Generate a unique license ID"""
        import uuid
        return str(uuid.uuid4())
    
    def validate_license_package(self, license_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a generated license package
        
        Args:
            license_package: License package to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = {
                'valid': False,
                'errors': [],
                'warnings': []
            }
            
            # Check required fields
            required_fields = ['license_key', 'license_data', 'signature', 'validation_hash']
            for field in required_fields:
                if field not in license_package:
                    result['errors'].append(f"Missing required field: {field}")
            
            if result['errors']:
                return result
            
            # Validate license data structure
            license_data = license_package.get('license_data', {})
            required_data_fields = ['license_key', 'license_id', 'license_type', 'features']
            for field in required_data_fields:
                if field not in license_data:
                    result['errors'].append(f"Missing license data field: {field}")
            
            # Verify signature
            license_json = json.dumps(license_data, sort_keys=True)
            if not self.license_crypto.verify_signature(license_json, license_package.get('signature', '')):
                result['errors'].append("Invalid license signature")
            
            # Verify validation hash
            calculated_hash = hashlib.sha256(license_json.encode()).hexdigest()
            if calculated_hash != license_package.get('validation_hash', ''):
                result['errors'].append("Invalid validation hash")
            
            result['valid'] = len(result['errors']) == 0
            return result
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': []
            }
    
    def get_license_template_info(self, license_type: str) -> Dict[str, Any]:
        """Get information about a license template"""
        if license_type not in self.license_templates:
            return {}
        
        template = self.license_templates[license_type]
        return {
            'license_type': license_type,
            'maintenance_days': template['maintenance_days'],
            'max_activations': template['max_activations'],
            'offline_grace_period_days': template['offline_grace_period_days'],
            'features': template['features'],
            'feature_count': len(template['features'])
        }
    
    def list_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all license templates"""
        return {
            license_type: self.get_license_template_info(license_type)
            for license_type in self.license_templates
        }


def main():
    """Command-line interface for license key generator"""
    parser = argparse.ArgumentParser(description='POS MVP License Key Generator')
    parser.add_argument('--type', choices=['trial', 'standard', 'professional', 'enterprise'],
                       help='License type')
    parser.add_argument('--name', help='Customer name')
    parser.add_argument('--email', help='Customer email')
    parser.add_argument('--company', help='Customer company')
    parser.add_argument('--phone', help='Customer phone')
    parser.add_argument('--batch', help='Batch input file (JSON or CSV)')
    parser.add_argument('--output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'csv', 'text', 'binary'],
                       default='json', help='Output format')
    parser.add_argument('--algorithm', choices=['RSA', 'ECC'], default='RSA',
                       help='Cryptographic algorithm')
    parser.add_argument('--hardware-binding', action='store_true',
                       help='Bind license to hardware fingerprint')
    parser.add_argument('--expiry-days', type=int, help='Custom expiry in days')
    parser.add_argument('--max-activations', type=int, help='Maximum activations')
    parser.add_argument('--activation-code', help='Optional activation code')
    parser.add_argument('--custom-features', help='Custom features (comma-separated)')
    parser.add_argument('--list-templates', action='store_true',
                       help='List all license templates')
    parser.add_argument('--validate', help='Validate license package file')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = LicenseKeyGenerator(args.algorithm)
    
    # List templates
    if args.list_templates:
        templates = generator.list_all_templates()
        print("Available License Templates:")
        print("=" * 50)
        for license_type, info in templates.items():
            print(f"\n{license_type.upper()} License:")
            print(f"  Maintenance Days: {info['maintenance_days']}")
            print(f"  Max Activations: {info['max_activations']}")
            print(f"  Offline Grace Period: {info['offline_grace_period_days']} days")
            print(f"  Features: {info['feature_count']}")
            print(f"  Feature List: {', '.join(info['features'])}")
        return
    
    # Validate license package
    if args.validate:
        try:
            with open(args.validate, 'r', encoding='utf-8') as f:
                if args.validate.endswith('.json'):
                    license_package = json.load(f)
                else:
                    # Assume binary package
                    license_package = json.load(f)
            
            result = generator.validate_license_package(license_package)
            if result['valid']:
                print("License package is valid!")
            else:
                print("License package validation failed:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if result['warnings']:
                print("Warnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
        except Exception as e:
            print(f"Error validating license package: {str(e)}")
        return
    
    # Check if license type is provided for generation
    if not args.type:
        print("License type is required for license generation")
        return
    
    # Prepare customer data
    customer_data = {
        'name': args.name or '',
        'email': args.email or '',
        'company': args.company or '',
        'phone': args.phone or ''
    }
    
    if args.max_activations:
        customer_data['max_activations'] = args.max_activations
    
    # Parse custom features
    custom_features = None
    if args.custom_features:
        custom_features = [f.strip() for f in args.custom_features.split(',')]
    
    # Generate licenses
    licenses = []
    
    if args.batch:
        # Batch generation
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                if args.batch.endswith('.json'):
                    customer_list = json.load(f)
                elif args.batch.endswith('.csv'):
                    reader = csv.DictReader(f)
                    customer_list = list(reader)
                else:
                    raise ValueError("Unsupported batch file format. Use JSON or CSV.")
            
            licenses = generator.generate_batch_keys(
                args.type, customer_list, args.hardware_binding,
                custom_features, args.expiry_days, args.activation_code
            )
            
            print(f"Generated {len(licenses)} licenses from batch file")
        except Exception as e:
            print(f"Error processing batch file: {str(e)}")
            return
    else:
        # Single license generation
        if not args.name:
            print("Customer name is required for single license generation")
            return
        
        license_package = generator.generate_license_key(
            args.type, customer_data, args.hardware_binding,
            custom_features, args.expiry_days, args.activation_code
        )
        
        if license_package:
            licenses = [license_package]
            print(f"Generated license key: {license_package['license_key']}")
        else:
            print("Failed to generate license key")
            return
    
    # Export licenses
    if licenses:
        output_file = args.output or f"licenses_{args.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"
        
        if generator.export_licenses(licenses, output_file, args.format):
            print(f"Exported {len(licenses)} licenses to {output_file}")
        else:
            print("Failed to export licenses")


if __name__ == "__main__":
    main()