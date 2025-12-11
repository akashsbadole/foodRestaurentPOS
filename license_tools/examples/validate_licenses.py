#!/usr/bin/env python3
"""
Example script for validating licenses
Demonstrates various validation scenarios
"""

import os
import sys
import json
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from license_validator_cli import LicenseValidatorCLI
from license_key_generator import LicenseKeyGenerator


def validate_single_license():
    """Validate a single license"""
    print("Validating Single License...")
    print("-" * 30)
    
    # Generate a test license first
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'company': 'Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_PROFESSIONAL,
        customer_data,
        hardware_binding=True
    )
    
    if not license_package:
        print("Failed to generate test license")
        return
    
    license_key = license_package['license_key']
    print(f"Generated test license: {license_key}")
    
    # Validate the license
    validator = LicenseValidatorCLI(mode="offline")
    
    result = validator.validate_license_key(
        license_key,
        activation_id="ACT_TEST_001",
        validation_level="advanced",
        online=False,
        detailed=True
    )
    
    print(f"Validation Result: {'VALID' if result['valid'] else 'INVALID'}")
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result.get('checks'):
        print("Detailed Checks:")
        for check_name, check_result in result['checks'].items():
            status = 'PASS' if check_result else 'FAIL'
            print(f"  {check_name}: {status}")
    
    if result.get('license_info'):
        license_info = result['license_info']
        print("License Information:")
        print(f"  Customer: {license_info.get('customer_name', '')}")
        print(f"  Type: {license_info.get('license_type', '')}")
        print(f"  Expires: {license_info.get('expiry_date', '')}")
    
    if result.get('warnings'):
        print("Warnings:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    print()


def validate_batch_licenses():
    """Validate multiple licenses in batch"""
    print("Validating Batch Licenses...")
    print("-" * 30)
    
    # Generate test licenses
    generator = LicenseKeyGenerator("RSA")
    
    customer_list = [
        {
            'name': 'Customer One',
            'email': 'customer1@example.com',
            'company': 'Company One'
        },
        {
            'name': 'Customer Two',
            'email': 'customer2@example.com',
            'company': 'Company Two'
        },
        {
            'name': 'Customer Three',
            'email': 'customer3@example.com',
            'company': 'Company Three'
        }
    ]
    
    licenses = generator.generate_batch_keys(
        generator.TYPE_STANDARD,
        customer_list,
        hardware_binding=False
    )
    
    if not licenses:
        print("Failed to generate test licenses")
        return
    
    license_keys = [pkg['license_key'] for pkg in licenses]
    print(f"Generated {len(license_keys)} test licenses")
    
    # Validate in batch
    validator = LicenseValidatorCLI(mode="offline")
    
    results = validator.validate_batch(
        license_keys,
        validation_level="standard",
        online=False,
        detailed=False
    )
    
    # Print results
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    
    print(f"Validation Results:")
    print(f"  Total: {len(results)}")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {invalid_count}")
    
    print("\nIndividual Results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['license_key'][:16]}... - {result['status'].upper()}")
    
    # Export report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"validation_report_{timestamp}.json"
    
    if validator.export_validation_report(results, report_file, 'json'):
        print(f"\nReport exported to: {report_file}")
    
    print()


def check_blacklist_status():
    """Check blacklist status"""
    print("Checking Blacklist Status...")
    print("-" * 30)
    
    # Generate a test license
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Blacklist Test Customer',
        'email': 'blacklist@example.com',
        'company': 'Blacklist Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_TRIAL,
        customer_data
    )
    
    if not license_package:
        print("Failed to generate test license")
        return
    
    license_key = license_package['license_key']
    print(f"Generated test license: {license_key}")
    
    # Check blacklist status
    validator = LicenseValidatorCLI(mode="offline")
    
    result = validator.check_blacklist(license_key)
    
    print("Blacklist Check Result:")
    print(f"  Blacklisted: {'Yes' if result.get('blacklisted') else 'No'}")
    print(f"  Message: {result.get('message', '')}")
    
    if result.get('blacklist_info'):
        print("  Blacklist Info:")
        for key, value in result['blacklist_info'].items():
            print(f"    {key}: {value}")
    
    print()


def send_heartbeat_test():
    """Test heartbeat functionality"""
    print("Testing Heartbeat...")
    print("-" * 30)
    
    # Generate a test license
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Heartbeat Test Customer',
        'email': 'heartbeat@example.com',
        'company': 'Heartbeat Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_PROFESSIONAL,
        customer_data
    )
    
    if not license_package:
        print("Failed to generate test license")
        return
    
    license_key = license_package['license_key']
    activation_id = "ACT_HEARTBEAT_001"
    
    print(f"Generated test license: {license_key}")
    
    # Test heartbeat
    validator = LicenseValidatorCLI(mode="offline")
    
    usage_data = {
        'app_version': '1.0.0',
        'usage_hours': 24,
        'features_used': ['orders.create', 'reports.basic'],
        'system_info': {
            'platform': os.name,
            'python_version': sys.version
        }
    }
    
    result = validator.send_heartbeat(license_key, activation_id, usage_data)
    
    print("Heartbeat Result:")
    print(f"  Success: {'Yes' if result.get('success') else 'No'}")
    print(f"  Status: {result.get('status', '')}")
    print(f"  Message: {result.get('message', '')}")
    
    print()


def test_validation_levels():
    """Test different validation levels"""
    print("Testing Validation Levels...")
    print("-" * 30)
    
    # Generate a test license
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Validation Levels Test',
        'email': 'validation@example.com',
        'company': 'Validation Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_ENTERPRISE,
        customer_data,
        hardware_binding=True
    )
    
    if not license_package:
        print("Failed to generate test license")
        return
    
    license_key = license_package['license_key']
    print(f"Generated test license: {license_key}")
    
    # Test different validation levels
    validator = LicenseValidatorCLI(mode="offline")
    
    validation_levels = ["basic", "standard", "advanced", "stealth"]
    
    for level in validation_levels:
        print(f"\nTesting {level.upper()} validation:")
        
        result = validator.validate_license_key(
            license_key,
            activation_id=f"ACT_{level.upper()}_001",
            validation_level=level,
            online=False,
            detailed=True
        )
        
        print(f"  Result: {'VALID' if result['valid'] else 'INVALID'}")
        print(f"  Status: {result['status']}")
        
        if result.get('checks'):
            failed_checks = [name for name, passed in result['checks'].items() if not passed]
            if failed_checks:
                print(f"  Failed Checks: {', '.join(failed_checks)}")
            else:
                print("  All checks passed")
    
    print()


def test_validation_modes():
    """Test different validation modes"""
    print("Testing Validation Modes...")
    print("-" * 30)
    
    # Generate a test license
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Validation Modes Test',
        'email': 'modes@example.com',
        'company': 'Modes Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_PROFESSIONAL,
        customer_data
    )
    
    if not license_package:
        print("Failed to generate test license")
        return
    
    license_key = license_package['license_key']
    print(f"Generated test license: {license_key}")
    
    # Test different validation modes
    modes = ["offline", "hybrid"]
    
    for mode in modes:
        print(f"\nTesting {mode.upper()} validation:")
        
        validator = LicenseValidatorCLI(mode=mode)
        
        result = validator.validate_license_key(
            license_key,
            activation_id=f"ACT_{mode.upper()}_001",
            validation_level="standard",
            online=(mode == "online"),
            detailed=False
        )
        
        print(f"  Result: {'VALID' if result['valid'] else 'INVALID'}")
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
        
        if result.get('warnings'):
            for warning in result['warnings']:
                print(f"  Warning: {warning}")
    
    print()


def get_validator_status():
    """Get validator status information"""
    print("Getting Validator Status...")
    print("-" * 30)
    
    validator = LicenseValidatorCLI(mode="hybrid")
    
    status = validator.get_validation_status()
    
    print("Validator Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print()


def simulate_real_world_scenario():
    """Simulate a real-world license validation scenario"""
    print("Simulating Real-World Scenario...")
    print("-" * 30)
    
    # Generate a license for a real customer
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Acme Restaurant',
        'email': 'contact@acmerestaurant.com',
        'company': 'Acme Restaurant LLC',
        'phone': '+1-555-0123',
        'max_activations': 3,
        'offline_grace_period_days': 30
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_PROFESSIONAL,
        customer_data,
        hardware_binding=True,
        expiry_days=365
    )
    
    if not license_package:
        print("Failed to generate customer license")
        return
    
    license_key = license_package['license_key']
    print(f"Generated license for Acme Restaurant: {license_key}")
    
    # Simulate license activation and validation over time
    validator = LicenseValidatorCLI(mode="hybrid")
    
    # Initial activation
    print("\n1. Initial Activation:")
    result = validator.validate_license_key(
        license_key,
        activation_id="ACT_ACME_001",
        validation_level="advanced",
        online=True,
        detailed=True
    )
    
    print(f"   Status: {result['status']}")
    print(f"   Valid: {result['valid']}")
    
    # Regular usage validation (offline)
    print("\n2. Regular Usage Validation (Offline):")
    for day in range(1, 8):  # Simulate 7 days of usage
        print(f"   Day {day}: ", end="")
        
        result = validator.validate_license_key(
            license_key,
            activation_id="ACT_ACME_001",
            validation_level="standard",
            online=False,
            detailed=False
        )
        
        if result['valid']:
            print("Valid [OK]")
        else:
            print(f"Invalid [FAIL] ({result['status']})")
            break
        
        # Simulate time passing
        time.sleep(0.1)  # Small delay for demonstration
    
    # Periodic online validation
    print("\n3. Periodic Online Validation:")
    result = validator.validate_license_key(
        license_key,
        activation_id="ACT_ACME_001",
        validation_level="advanced",
        online=True,
        detailed=True
    )
    
    print(f"   Status: {result['status']}")
    print(f"   Valid: {result['valid']}")
    
    # Send heartbeat
    print("\n4. Sending Heartbeat:")
    usage_data = {
        'app_version': '1.0.0',
        'usage_hours': 168,  # 1 week
        'features_used': [
            'orders.create', 'orders.view', 'orders.edit',
            'menu.view', 'menu.edit', 'inventory.view',
            'reports.basic', 'tables.manage'
        ],
        'system_info': {
            'platform': os.name,
            'python_version': sys.version
        }
    }
    
    heartbeat_result = validator.send_heartbeat(license_key, "ACT_ACME_001", usage_data)
    print(f"   Success: {heartbeat_result.get('success', False)}")
    
    print()


def main():
    """Main function demonstrating various validation scenarios"""
    print("POS MVP License Validator Examples")
    print("=" * 50)
    print()
    
    # Run all validation examples
    validate_single_license()
    validate_batch_licenses()
    check_blacklist_status()
    send_heartbeat_test()
    test_validation_levels()
    test_validation_modes()
    get_validator_status()
    simulate_real_world_scenario()
    
    print("All validation examples completed successfully!")


if __name__ == "__main__":
    main()