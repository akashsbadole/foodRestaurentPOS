#!/usr/bin/env python3
"""
License Validator CLI for POS MVP application
Command-line tool for comprehensive license validation
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.license_validator import LicenseValidator
from src.utils.license_crypto import LicenseCrypto
from src.utils.hardware_fingerprint import HardwareFingerprint
from src.models.license import License


class LicenseValidatorCLI:
    """
    Command-line interface for license validation
    """
    
    # Validation modes
    MODE_ONLINE = "online"
    MODE_OFFLINE = "offline"
    MODE_HYBRID = "hybrid"
    
    # Validation levels
    LEVEL_BASIC = "basic"
    LEVEL_STANDARD = "standard"
    LEVEL_ADVANCED = "advanced"
    LEVEL_STEALTH = "stealth"
    
    def __init__(self, server_url: str = None, mode: str = MODE_HYBRID):
        """
        Initialize license validator CLI
        
        Args:
            server_url: License server URL
            mode: Validation mode (online/offline/hybrid)
        """
        self.validator = LicenseValidator(server_url, mode)
        self.license_crypto = LicenseCrypto()
        self.hardware_fingerprint = HardwareFingerprint()
        self.license = License()
    
    def validate_license_key(self, license_key: str, activation_id: str = None,
                           hardware_fingerprint: str = None, validation_level: str = LEVEL_ADVANCED,
                           online: bool = False, detailed: bool = False) -> Dict[str, Any]:
        """
        Validate a license key with comprehensive checks
        
        Args:
            license_key: License key to validate
            activation_id: Optional activation ID
            hardware_fingerprint: Optional hardware fingerprint
            validation_level: Validation level to perform
            online: Whether to perform online validation
            detailed: Whether to show detailed validation results
            
        Returns:
            Dictionary with validation result
        """
        try:
            result = {
                'license_key': license_key,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_level': validation_level,
                'validation_mode': 'online' if online else 'offline',
                'valid': False,
                'status': 'invalid',
                'message': '',
                'checks': {},
                'license_info': None,
                'warnings': [],
                'errors': []
            }
            
            # Generate hardware fingerprint if not provided
            if not hardware_fingerprint:
                fp_data = self.hardware_fingerprint.generate_fingerprint(
                    HardwareFingerprint.METHOD_ADVANCED
                )
                hardware_fingerprint = fp_data.get('hash', '')
            
            # Prepare validation data
            validation_data = {
                'validation_level': validation_level,
                'detailed_output': detailed,
                'client_info': {
                    'platform': os.name,
                    'python_version': sys.version,
                    'validator_version': '1.0.0'
                }
            }
            
            # Perform validation based on mode
            if online:
                validation_result = self.validator.validate_license_online(
                    license_key, activation_id, hardware_fingerprint, validation_data
                )
            else:
                validation_result = self.validator.validate_license_offline(
                    license_key, activation_id, hardware_fingerprint, validation_data
                )
            
            # Parse validation result
            result['valid'] = validation_result.get('success', False)
            result['status'] = validation_result.get('status', 'invalid')
            result['message'] = validation_result.get('message', '')
            
            # Add detailed checks if requested
            if detailed:
                result['checks'] = self._perform_detailed_checks(license_key, activation_id, hardware_fingerprint)
            
            # Add license info if available
            if result['valid']:
                license_info = self._extract_license_info(license_key)
                if license_info:
                    result['license_info'] = license_info
            
            # Add warnings and errors
            if not result['valid']:
                result['errors'].append(result['message'])
            
            # Add additional warnings
            if validation_result.get('grace_period_remaining'):
                grace_hours = validation_result['grace_period_remaining'] / 3600
                if grace_hours < 24:
                    result['warnings'].append(f"Offline grace period expires in {grace_hours:.1f} hours")
                elif grace_hours < 72:
                    result['warnings'].append(f"Offline grace period expires in {grace_hours/24:.1f} days")
            
            return result
        except Exception as e:
            return {
                'license_key': license_key,
                'validation_timestamp': datetime.now().isoformat(),
                'validation_level': validation_level,
                'validation_mode': 'online' if online else 'offline',
                'valid': False,
                'status': 'error',
                'message': f'Validation error: {str(e)}',
                'checks': {},
                'license_info': None,
                'warnings': [],
                'errors': [str(e)]
            }
    
    def _perform_detailed_checks(self, license_key: str, activation_id: str,
                              hardware_fingerprint: str) -> Dict[str, Any]:
        """Perform detailed validation checks"""
        checks = {
            'signature_verification': False,
            'integrity_check': False,
            'expiry_check': False,
            'hardware_binding_check': False,
            'blacklist_check': False,
            'activation_check': False,
            'feature_check': False
        }
        
        try:
            # Load license from database (if available)
            if self.license.load_from_database(license_key):
                # Check signature
                checks['signature_verification'] = self.license.verify_signature()
                
                # Check integrity
                checks['integrity_check'] = self.license.verify_integrity()
                
                # Check expiry
                checks['expiry_check'] = not self.license.is_expired()
                
                # Check hardware binding
                if self.license._machine_bindings:
                    checks['hardware_binding_check'] = hardware_fingerprint in self.license._machine_bindings
                else:
                    checks['hardware_binding_check'] = True  # No binding required
                
                # Check activation status
                checks['activation_check'] = self.license._status == self.license.STATUS_ACTIVE
                
                # Check features
                checks['feature_check'] = bool(self.license._features)
                
                # Check blacklist
                blacklist_result = self.validator.check_blacklist(license_key, hardware_fingerprint)
                checks['blacklist_check'] = not blacklist_result.get('blacklisted', False)
        except Exception as e:
            checks['error'] = str(e)
        
        return checks
    
    def _extract_license_info(self, license_key: str) -> Dict[str, Any]:
        """Extract license information"""
        try:
            if self.license.load_from_database(license_key):
                return self.license.get_license_info()
        except Exception:
            pass
        return None
    
    def check_blacklist(self, license_key: str = None, hardware_fingerprint: str = None) -> Dict[str, Any]:
        """Check if license or hardware is blacklisted"""
        try:
            if not hardware_fingerprint:
                fp_data = self.hardware_fingerprint.generate_fingerprint(
                    HardwareFingerprint.METHOD_ADVANCED
                )
                hardware_fingerprint = fp_data.get('hash', '')
            
            return self.validator.check_blacklist(license_key, hardware_fingerprint)
        except Exception as e:
            return {
                'success': False,
                'blacklisted': False,
                'message': f'Blacklist check error: {str(e)}',
                'blacklist_info': None
            }
    
    def send_heartbeat(self, license_key: str, activation_id: str,
                      usage_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send heartbeat to license server"""
        try:
            if not usage_data:
                usage_data = {
                    'app_version': '1.0.0',
                    'usage_hours': 0,
                    'features_used': [],
                    'system_info': {
                        'platform': os.name,
                        'python_version': sys.version
                    }
                }
            
            return self.validator.send_heartbeat(license_key, activation_id, usage_data)
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'message': f'Heartbeat error: {str(e)}'
            }
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validator status"""
        try:
            return self.validator.get_validation_status()
        except Exception as e:
            return {
                'error': f'Status check error: {str(e)}'
            }
    
    def validate_batch(self, license_keys: List[str], validation_level: str = LEVEL_STANDARD,
                     online: bool = False, detailed: bool = False) -> List[Dict[str, Any]]:
        """Validate multiple license keys in batch"""
        results = []
        
        for i, license_key in enumerate(license_keys):
            print(f"Validating license {i+1}/{len(license_keys)}: {license_key}")
            
            result = self.validate_license_key(
                license_key, None, None, validation_level, online, detailed
            )
            results.append(result)
        
        return results
    
    def export_validation_report(self, results: List[Dict[str, Any]], output_file: str,
                             format_type: str = 'json') -> bool:
        """Export validation results to report"""
        try:
            if format_type.lower() == 'json':
                report_data = {
                    'report_info': {
                        'total_licenses': len(results),
                        'valid_licenses': sum(1 for r in results if r['valid']),
                        'invalid_licenses': sum(1 for r in results if not r['valid']),
                        'generated_at': datetime.now().isoformat(),
                        'validator_version': '1.0.0'
                    },
                    'results': results
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            elif format_type.lower() == 'text':
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("License Validation Report\n")
                    f.write("=" * 50 + "\n\n")
                    
                    valid_count = sum(1 for r in results if r['valid'])
                    invalid_count = len(results) - valid_count
                    
                    f.write(f"Total Licenses: {len(results)}\n")
                    f.write(f"Valid Licenses: {valid_count}\n")
                    f.write(f"Invalid Licenses: {invalid_count}\n")
                    f.write(f"Generated At: {datetime.now().isoformat()}\n\n")
                    
                    for i, result in enumerate(results, 1):
                        f.write(f"License #{i}\n")
                        f.write("-" * 30 + "\n")
                        f.write(f"License Key: {result['license_key']}\n")
                        f.write(f"Status: {result['status']}\n")
                        f.write(f"Valid: {'Yes' if result['valid'] else 'No'}\n")
                        f.write(f"Message: {result['message']}\n")
                        
                        if result.get('warnings'):
                            f.write("Warnings:\n")
                            for warning in result['warnings']:
                                f.write(f"  - {warning}\n")
                        
                        if result.get('errors'):
                            f.write("Errors:\n")
                            for error in result['errors']:
                                f.write(f"  - {error}\n")
                        
                        f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error exporting validation report: {str(e)}")
            return False


def main():
    """Command-line interface for license validator"""
    parser = argparse.ArgumentParser(description='POS MVP License Validator CLI')
    parser.add_argument('license_key', nargs='?', help='License key to validate')
    parser.add_argument('--activation-id', help='Activation ID')
    parser.add_argument('--hardware-fingerprint', help='Hardware fingerprint')
    parser.add_argument('--server-url', help='License server URL')
    parser.add_argument('--mode', choices=['online', 'offline', 'hybrid'], default='hybrid',
                       help='Validation mode')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced', 'stealth'],
                       default='advanced', help='Validation level')
    parser.add_argument('--online', action='store_true', help='Perform online validation')
    parser.add_argument('--detailed', action='store_true', help='Show detailed validation results')
    parser.add_argument('--batch', help='Batch input file (JSON or text)')
    parser.add_argument('--output', help='Output file for validation report')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format for report')
    parser.add_argument('--blacklist-check', action='store_true', help='Check blacklist status')
    parser.add_argument('--heartbeat', action='store_true', help='Send heartbeat to server')
    parser.add_argument('--status', action='store_true', help='Get validator status')
    parser.add_argument('--usage-data', help='Usage data file for heartbeat (JSON)')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = LicenseValidatorCLI(args.server_url, args.mode)
    
    # Get validator status
    if args.status:
        status = validator.get_validation_status()
        print("Validator Status:")
        print("=" * 30)
        for key, value in status.items():
            print(f"{key}: {value}")
        return
    
    # Blacklist check
    if args.blacklist_check:
        if not args.license_key:
            print("License key is required for blacklist check")
            return
        
        result = validator.check_blacklist(args.license_key, args.hardware_fingerprint)
        print("Blacklist Check Result:")
        print("=" * 30)
        print(f"Blacklisted: {'Yes' if result.get('blacklisted') else 'No'}")
        print(f"Message: {result.get('message', '')}")
        
        if result.get('blacklist_info'):
            print("Blacklist Info:")
            for key, value in result['blacklist_info'].items():
                print(f"  {key}: {value}")
        return
    
    # Heartbeat
    if args.heartbeat:
        if not args.license_key or not args.activation_id:
            print("License key and activation ID are required for heartbeat")
            return
        
        usage_data = None
        if args.usage_data:
            try:
                with open(args.usage_data, 'r', encoding='utf-8') as f:
                    usage_data = json.load(f)
            except Exception as e:
                print(f"Error loading usage data: {str(e)}")
                return
        
        result = validator.send_heartbeat(args.license_key, args.activation_id, usage_data)
        print("Heartbeat Result:")
        print("=" * 30)
        print(f"Success: {'Yes' if result.get('success') else 'No'}")
        print(f"Status: {result.get('status', '')}")
        print(f"Message: {result.get('message', '')}")
        return
    
    # Batch validation
    if args.batch:
        try:
            with open(args.batch, 'r', encoding='utf-8') as f:
                if args.batch.endswith('.json'):
                    license_keys = json.load(f)
                else:
                    # Text file with one license key per line
                    license_keys = [line.strip() for line in f if line.strip()]
            
            results = validator.validate_batch(
                license_keys, args.level, args.online, args.detailed
            )
            
            # Print summary
            valid_count = sum(1 for r in results if r['valid'])
            invalid_count = len(results) - valid_count
            
            print(f"Batch Validation Complete:")
            print(f"Total: {len(results)}")
            print(f"Valid: {valid_count}")
            print(f"Invalid: {invalid_count}")
            
            # Export report if requested
            if args.output:
                if validator.export_validation_report(results, args.output, args.format):
                    print(f"Report exported to {args.output}")
                else:
                    print("Failed to export report")
            
            return
        except Exception as e:
            print(f"Error processing batch file: {str(e)}")
            return
    
    # Single license validation
    if not args.license_key:
        print("License key is required for validation")
        return
    
    result = validator.validate_license_key(
        args.license_key, args.activation_id, args.hardware_fingerprint,
        args.level, args.online, args.detailed
    )
    
    # Print validation result
    print("License Validation Result:")
    print("=" * 30)
    print(f"License Key: {result['license_key']}")
    print(f"Valid: {'Yes' if result['valid'] else 'No'}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    print(f"Validation Level: {result['validation_level']}")
    print(f"Validation Mode: {result['validation_mode']}")
    print(f"Timestamp: {result['validation_timestamp']}")
    
    # Print detailed checks if available
    if result.get('checks'):
        print("\nDetailed Checks:")
        for check_name, check_result in result['checks'].items():
            status = 'PASS' if check_result else 'FAIL'
            print(f"  {check_name}: {status}")
    
    # Print license info if available
    if result.get('license_info'):
        print("\nLicense Information:")
        license_info = result['license_info']
        print(f"  License ID: {license_info.get('license_id', '')}")
        print(f"  Customer: {license_info.get('customer_name', '')}")
        print(f"  Email: {license_info.get('customer_email', '')}")
        print(f"  Type: {license_info.get('license_type', '')}")
        print(f"  Issued: {license_info.get('issued_date', '')}")
        print(f"  Expires: {license_info.get('expiry_date', '')}")
        print(f"  Activations: {license_info.get('activation_count', 0)}/{license_info.get('max_activations', 0)}")
    
    # Print warnings
    if result.get('warnings'):
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    # Print errors
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()