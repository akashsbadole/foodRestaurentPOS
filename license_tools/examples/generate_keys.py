#!/usr/bin/env python3
"""
Example script for generating license keys
Demonstrates various key generation scenarios
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from license_key_generator import LicenseKeyGenerator


def generate_trial_license():
    """Generate a trial license"""
    print("Generating Trial License...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Trial Customer',
        'email': 'trial@example.com',
        'company': 'Trial Company',
        'phone': '+1234567890'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_TRIAL,
        customer_data,
        hardware_binding=True,
        expiry_days=30
    )
    
    if license_package:
        print(f"License Key: {license_package['license_key']}")
        print(f"License ID: {license_package['license_data']['license_id']}")
        print(f"Customer: {license_package['license_data']['customer_name']}")
        print(f"Type: {license_package['license_data']['license_type']}")
        print(f"Expires: {license_package['license_data']['expiry_date']}")
        print(f"Features: {', '.join(license_package['license_data']['features'])}")
        
        # Export to file
        output_file = f"trial_license_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generator.export_licenses([license_package], output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def generate_standard_license():
    """Generate a standard license"""
    print("Generating Standard License...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("RSA")
    
    customer_data = {
        'name': 'Standard Customer',
        'email': 'standard@example.com',
        'company': 'Standard Company',
        'phone': '+1234567890',
        'max_activations': 5
    }
    
    custom_features = [
        "orders.create", "orders.view", "orders.edit", "orders.delete",
        "menu.view", "menu.edit", "menu.create", "inventory.view", "inventory.edit",
        "reports.basic", "tables.manage", "users.create", "users.edit"
    ]
    
    license_package = generator.generate_license_key(
        generator.TYPE_STANDARD,
        customer_data,
        hardware_binding=False,
        custom_features=custom_features,
        expiry_days=365
    )
    
    if license_package:
        print(f"License Key: {license_package['license_key']}")
        print(f"License ID: {license_package['license_data']['license_id']}")
        print(f"Customer: {license_package['license_data']['customer_name']}")
        print(f"Type: {license_package['license_data']['license_type']}")
        print(f"Max Activations: {license_package['license_data']['max_activations']}")
        print(f"Expires: {license_package['license_data']['expiry_date']}")
        
        # Export to file
        output_file = f"standard_license_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generator.export_licenses([license_package], output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def generate_professional_license():
    """Generate a professional license"""
    print("Generating Professional License...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("ECC")
    
    customer_data = {
        'name': 'Professional Customer',
        'email': 'professional@example.com',
        'company': 'Professional Company',
        'phone': '+1234567890',
        'max_activations': 10,
        'offline_grace_period_days': 60
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_PROFESSIONAL,
        customer_data,
        hardware_binding=True,
        expiry_days=365,
        activation_code="PRO-2024-DEMO"
    )
    
    if license_package:
        print(f"License Key: {license_package['license_key']}")
        print(f"License ID: {license_package['license_data']['license_id']}")
        print(f"Customer: {license_package['license_data']['customer_name']}")
        print(f"Type: {license_package['license_data']['license_type']}")
        print(f"Algorithm: {license_package['generation_info']['algorithm']}")
        print(f"Hardware Binding: {license_package['generation_info']['hardware_binding']}")
        print(f"Activation Code: {license_package['generation_info']['activation_code']}")
        
        # Export to file
        output_file = f"professional_license_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generator.export_licenses([license_package], output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def generate_enterprise_license():
    """Generate an enterprise license"""
    print("Generating Enterprise License...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("ECC")
    
    customer_data = {
        'name': 'Enterprise Customer',
        'email': 'enterprise@example.com',
        'company': 'Enterprise Corporation',
        'phone': '+1234567890',
        'max_activations': 50,
        'offline_grace_period_days': 90
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_ENTERPRISE,
        customer_data,
        hardware_binding=True,
        expiry_days=365
    )
    
    if license_package:
        print(f"License Key: {license_package['license_key']}")
        print(f"License ID: {license_package['license_data']['license_id']}")
        print(f"Customer: {license_package['license_data']['customer_name']}")
        print(f"Company: {license_package['license_data'].get('customer_company', 'N/A')}")
        print(f"Type: {license_package['license_data']['license_type']}")
        print(f"Max Activations: {license_package['license_data']['max_activations']}")
        print(f"Features: {len(license_package['license_data']['features'])} features")
        
        # Export to file
        output_file = f"enterprise_license_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generator.export_licenses([license_package], output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def generate_batch_licenses():
    """Generate multiple licenses in batch"""
    print("Generating Batch Licenses...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Customer list
    customer_list = [
        {
            'name': 'Customer One',
            'email': 'customer1@example.com',
            'company': 'Company One',
            'phone': '+1234567890'
        },
        {
            'name': 'Customer Two',
            'email': 'customer2@example.com',
            'company': 'Company Two',
            'phone': '+1234567890'
        },
        {
            'name': 'Customer Three',
            'email': 'customer3@example.com',
            'company': 'Company Three',
            'phone': '+1234567890'
        }
    ]
    
    # Generate batch
    licenses = generator.generate_batch_keys(
        generator.TYPE_PROFESSIONAL,
        customer_list,
        hardware_binding=True,
        expiry_days=365
    )
    
    if licenses:
        print(f"Generated {len(licenses)} licenses:")
        for i, license_pkg in enumerate(licenses, 1):
            print(f"  {i}. {license_pkg['license_key']} - {license_pkg['license_data']['customer_name']}")
        
        # Export to different formats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON format
        json_file = f"batch_licenses_{timestamp}.json"
        generator.export_licenses(licenses, json_file, generator.FORMAT_JSON)
        print(f"Exported JSON to: {json_file}")
        
        # CSV format
        csv_file = f"batch_licenses_{timestamp}.csv"
        generator.export_licenses(licenses, csv_file, generator.FORMAT_CSV)
        print(f"Exported CSV to: {csv_file}")
        
        # Text format
        text_file = f"batch_licenses_{timestamp}.txt"
        generator.export_licenses(licenses, text_file, generator.FORMAT_TEXT)
        print(f"Exported text to: {text_file}")
    
    print()


def list_license_templates():
    """List all available license templates"""
    print("Available License Templates")
    print("=" * 50)
    
    generator = LicenseKeyGenerator("RSA")
    templates = generator.list_all_templates()
    
    for license_type, info in templates.items():
        print(f"\n{license_type.upper()} License:")
        print(f"  Maintenance Days: {info['maintenance_days']}")
        print(f"  Max Activations: {info['max_activations']}")
        print(f"  Offline Grace Period: {info['offline_grace_period_days']} days")
        print(f"  Features: {info['feature_count']}")
        print(f"  Feature List: {', '.join(info['features'])}")
    
    print()


def validate_generated_license():
    """Validate a generated license package"""
    print("Validating Generated License...")
    print("-" * 30)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Generate a test license
    customer_data = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'company': 'Test Company'
    }
    
    license_package = generator.generate_license_key(
        generator.TYPE_STANDARD,
        customer_data,
        hardware_binding=True
    )
    
    if license_package:
        print(f"Generated license: {license_package['license_key']}")
        
        # Validate the package
        validation_result = generator.validate_license_package(license_package)
        
        print(f"Validation Result: {'VALID' if validation_result['valid'] else 'INVALID'}")
        
        if validation_result['errors']:
            print("Errors:")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        if validation_result['warnings']:
            print("Warnings:")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
    
    print()


def main():
    """Main function demonstrating various license generation scenarios"""
    print("POS MVP License Key Generator Examples")
    print("=" * 50)
    print()
    
    # List templates
    list_license_templates()
    
    # Generate different license types
    generate_trial_license()
    generate_standard_license()
    generate_professional_license()
    generate_enterprise_license()
    
    # Generate batch licenses
    generate_batch_licenses()
    
    # Validate generated license
    validate_generated_license()
    
    print("All examples completed successfully!")


if __name__ == "__main__":
    main()