#!/usr/bin/env python3
"""
Example script for batch license generation
Demonstrates large-scale license generation workflows
"""

import os
import sys
import json
import csv
import random
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from license_key_generator import LicenseKeyGenerator


def generate_customer_data(count: int) -> list:
    """Generate sample customer data for batch testing"""
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 
                   'James', 'Mary', 'William', 'Patricia', 'Richard', 'Jennifer', 'Charles']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson']
    
    companies = ['Restaurant Corp', 'Food Service Inc', 'Dining Solutions LLC', 'Cafe Group',
                'Bistro Holdings', 'Eatery Partners', 'Kitchen Systems', 'FoodTech Solutions',
                'Restaurant Management Co', 'Culinary Services', 'Hospitality Group', 'Food & Beverage Inc']
    
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'company.com', 'restaurant.com',
                'email.com', 'mail.com', 'business.com']
    
    customers = []
    
    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        company = random.choice(companies)
        
        customer = {
            'name': f"{first_name} {last_name}",
            'email': f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}",
            'company': company,
            'phone': f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'max_activations': random.choice([1, 3, 5, 10]),
            'offline_grace_period_days': random.choice([7, 15, 30, 45, 60])
        }
        
        customers.append(customer)
    
    return customers


def batch_generate_trial_licenses(count: int = 10):
    """Generate multiple trial licenses"""
    print(f"Generating {count} Trial Licenses...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Generate customer data
    customers = generate_customer_data(count)
    
    # Generate licenses
    licenses = generator.generate_batch_keys(
        generator.TYPE_TRIAL,
        customers,
        hardware_binding=True,
        expiry_days=30
    )
    
    if licenses:
        print(f"Successfully generated {len(licenses)} trial licenses")
        
        # Export to different formats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON format
        json_file = f"batch_trial_{timestamp}.json"
        generator.export_licenses(licenses, json_file, generator.FORMAT_JSON)
        print(f"Exported JSON to: {json_file}")
        
        # CSV format
        csv_file = f"batch_trial_{timestamp}.csv"
        generator.export_licenses(licenses, csv_file, generator.FORMAT_CSV)
        print(f"Exported CSV to: {csv_file}")
        
        # Text format
        text_file = f"batch_trial_{timestamp}.txt"
        generator.export_licenses(licenses, text_file, generator.FORMAT_TEXT)
        print(f"Exported text to: {text_file}")
    
    print()


def batch_generate_standard_licenses(count: int = 15):
    """Generate multiple standard licenses"""
    print(f"Generating {count} Standard Licenses...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Generate customer data
    customers = generate_customer_data(count)
    
    # Generate licenses
    licenses = generator.generate_batch_keys(
        generator.TYPE_STANDARD,
        customers,
        hardware_binding=False,
        expiry_days=365
    )
    
    if licenses:
        print(f"Successfully generated {len(licenses)} standard licenses")
        
        # Export to different formats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON format
        json_file = f"batch_standard_{timestamp}.json"
        generator.export_licenses(licenses, json_file, generator.FORMAT_JSON)
        print(f"Exported JSON to: {json_file}")
        
        # CSV format
        csv_file = f"batch_standard_{timestamp}.csv"
        generator.export_licenses(licenses, csv_file, generator.FORMAT_CSV)
        print(f"Exported CSV to: {csv_file}")
        
        # Binary format (encrypted)
        binary_file = f"batch_standard_{timestamp}.bin"
        generator.export_licenses(licenses, binary_file, generator.FORMAT_BINARY)
        print(f"Exported encrypted binary to: {binary_file}")
    
    print()


def batch_generate_mixed_licenses():
    """Generate mixed license types"""
    print("Generating Mixed License Types...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Define license distribution
    license_distribution = [
        (generator.TYPE_TRIAL, 5, True),
        (generator.TYPE_STANDARD, 10, False),
        (generator.TYPE_PROFESSIONAL, 8, True),
        (generator.TYPE_ENTERPRISE, 3, True)
    ]
    
    all_licenses = []
    
    for license_type, count, hardware_binding in license_distribution:
        print(f"Generating {count} {license_type} licenses...")
        
        customers = generate_customer_data(count)
        
        licenses = generator.generate_batch_keys(
            license_type,
            customers,
            hardware_binding=hardware_binding,
            expiry_days=365 if license_type != generator.TYPE_TRIAL else 30
        )
        
        all_licenses.extend(licenses)
        print(f"  Generated {len(licenses)} {license_type} licenses")
    
    print(f"\nTotal licenses generated: {len(all_licenses)}")
    
    # Export all licenses
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON format
    json_file = f"batch_mixed_{timestamp}.json"
    generator.export_licenses(all_licenses, json_file, generator.FORMAT_JSON)
    print(f"Exported JSON to: {json_file}")
    
    # CSV format
    csv_file = f"batch_mixed_{timestamp}.csv"
    generator.export_licenses(all_licenses, csv_file, generator.FORMAT_CSV)
    print(f"Exported CSV to: {csv_file}")
    
    print()


def batch_from_csv_file():
    """Generate licenses from CSV file input"""
    print("Generating Licenses from CSV File...")
    print("-" * 40)
    
    # Create sample CSV file
    csv_file = "sample_customers.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['name', 'email', 'company', 'phone', 'max_activations', 'offline_grace_period_days'])
        
        # Write sample data
        writer.writerow(['Alice Johnson', 'alice@restaurant.com', 'Alice\'s Cafe', '+1-555-0101', 3, 30])
        writer.writerow(['Bob Smith', 'bob@dining.com', 'Bob\'s Bistro', '+1-555-0102', 5, 45])
        writer.writerow(['Carol Williams', 'carol@eatery.com', 'Carol\'s Kitchen', '+1-555-0103', 1, 15])
        writer.writerow(['David Brown', 'david@food.com', 'David\'s Diner', '+1-555-0104', 10, 60])
        writer.writerow(['Eva Davis', 'eva@cafe.com', 'Eva\'s Eatery', '+1-555-0105', 3, 30])
    
    print(f"Created sample CSV file: {csv_file}")
    
    # Read CSV and generate licenses
    generator = LicenseKeyGenerator("ECC")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        customer_list = list(reader)
    
    print(f"Read {len(customer_list)} customers from CSV")
    
    # Generate professional licenses for all customers
    licenses = generator.generate_batch_keys(
        generator.TYPE_PROFESSIONAL,
        customer_list,
        hardware_binding=True,
        expiry_days=365
    )
    
    if licenses:
        print(f"Successfully generated {len(licenses)} professional licenses")
        
        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"batch_from_csv_{timestamp}.json"
        generator.export_licenses(licenses, output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def batch_from_json_file():
    """Generate licenses from JSON file input"""
    print("Generating Licenses from JSON File...")
    print("-" * 40)
    
    # Create sample JSON file
    json_file = "sample_customers.json"
    
    customer_data = {
        "customers": [
            {
                "name": "Frank Miller",
                "email": "frank@restaurant.com",
                "company": "Frank's Fine Dining",
                "phone": "+1-555-0201",
                "max_activations": 5,
                "offline_grace_period_days": 45
            },
            {
                "name": "Grace Wilson",
                "email": "grace@cafe.com",
                "company": "Grace's Garden Cafe",
                "phone": "+1-555-0202",
                "max_activations": 3,
                "offline_grace_period_days": 30
            },
            {
                "name": "Henry Taylor",
                "email": "henry@bistro.com",
                "company": "Henry's Bistro & Bar",
                "phone": "+1-555-0203",
                "max_activations": 10,
                "offline_grace_period_days": 60
            }
        ]
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(customer_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created sample JSON file: {json_file}")
    
    # Read JSON and generate licenses
    generator = LicenseKeyGenerator("ECC")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        customer_list = data['customers']
    
    print(f"Read {len(customer_list)} customers from JSON")
    
    # Generate enterprise licenses for all customers
    licenses = generator.generate_batch_keys(
        generator.TYPE_ENTERPRISE,
        customer_list,
        hardware_binding=True,
        expiry_days=365
    )
    
    if licenses:
        print(f"Successfully generated {len(licenses)} enterprise licenses")
        
        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"batch_from_json_{timestamp}.json"
        generator.export_licenses(licenses, output_file, generator.FORMAT_JSON)
        print(f"Exported to: {output_file}")
    
    print()


def batch_with_custom_features():
    """Generate licenses with custom features"""
    print("Generating Licenses with Custom Features...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Define custom feature sets
    custom_feature_sets = [
        {
            "name": "Basic POS",
            "features": [
                "orders.create", "orders.view", "orders.edit",
                "menu.view", "menu.edit", "inventory.view",
                "reports.basic", "tables.manage"
            ]
        },
        {
            "name": "Advanced POS",
            "features": [
                "orders.create", "orders.view", "orders.edit", "orders.delete",
                "menu.view", "menu.edit", "menu.create", "menu.delete",
                "inventory.view", "inventory.edit", "inventory.manage",
                "reports.basic", "reports.advanced", "tables.manage",
                "users.create", "users.edit", "users.manage"
            ]
        },
        {
            "name": "Full Featured",
            "features": [
                "orders.create", "orders.view", "orders.edit", "orders.delete",
                "menu.view", "menu.edit", "menu.create", "menu.delete",
                "inventory.view", "inventory.edit", "inventory.manage",
                "reports.basic", "reports.advanced", "reports.custom",
                "tables.manage", "users.create", "users.edit", "users.manage",
                "export.data", "import.data", "backup.create", "backup.restore",
                "api.access", "multi_branch", "advanced_analytics", "priority_support"
            ]
        }
    ]
    
    all_licenses = []
    
    for feature_set in custom_feature_sets:
        print(f"Generating licenses with {feature_set['name']} features...")
        
        customers = generate_customer_data(3)  # 3 customers per feature set
        
        licenses = generator.generate_batch_keys(
            generator.TYPE_PROFESSIONAL,
            customers,
            hardware_binding=True,
            custom_features=feature_set['features'],
            expiry_days=365
        )
        
        all_licenses.extend(licenses)
        print(f"  Generated {len(licenses)} licenses with {len(feature_set['features'])} features")
    
    print(f"\nTotal licenses generated: {len(all_licenses)}")
    
    # Export all licenses
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"batch_custom_features_{timestamp}.json"
    generator.export_licenses(all_licenses, output_file, generator.FORMAT_JSON)
    print(f"Exported to: {output_file}")
    
    print()


def batch_performance_test():
    """Performance test for batch generation"""
    print("Batch Generation Performance Test...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("RSA")
    
    # Test different batch sizes
    batch_sizes = [10, 50, 100, 200]
    
    for size in batch_sizes:
        print(f"Testing batch size: {size}")
        
        customers = generate_customer_data(size)
        
        start_time = datetime.now()
        
        licenses = generator.generate_batch_keys(
            generator.TYPE_STANDARD,
            customers,
            hardware_binding=False,
            expiry_days=365
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"  Generated: {len(licenses)} licenses")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Rate: {len(licenses)/duration:.2f} licenses/second")
        
        # Clean up generated licenses to save memory
        del licenses
        
        print()
    
    print("Performance test completed!")


def generate_large_scale_batch():
    """Generate a large batch of licenses"""
    print("Large-Scale Batch Generation...")
    print("-" * 40)
    
    generator = LicenseKeyGenerator("ECC")  # Use ECC for better performance
    
    batch_size = 500
    print(f"Generating {batch_size} licenses (this may take a moment)...")
    
    customers = generate_customer_data(batch_size)
    
    start_time = datetime.now()
    
    licenses = generator.generate_batch_keys(
        generator.TYPE_PROFESSIONAL,
        customers,
        hardware_binding=True,
        expiry_days=365
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if licenses:
        print(f"Successfully generated {len(licenses)} licenses")
        print(f"Generation time: {duration:.2f} seconds")
        print(f"Generation rate: {len(licenses)/duration:.2f} licenses/second")
        
        # Export to JSON (compressed)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"large_batch_{timestamp}.json"
        generator.export_licenses(licenses, output_file, generator.FORMAT_JSON)
        
        # Get file size
        file_size = os.path.getsize(output_file)
        print(f"Exported to: {output_file}")
        print(f"File size: {file_size/1024:.2f} KB")
    
    print()


def main():
    """Main function demonstrating batch generation scenarios"""
    print("POS MVP Batch License Generation Examples")
    print("=" * 60)
    print()
    
    # Run all batch generation examples
    batch_generate_trial_licenses(10)
    batch_generate_standard_licenses(15)
    batch_generate_mixed_licenses()
    batch_from_csv_file()
    batch_from_json_file()
    batch_with_custom_features()
    batch_performance_test()
    generate_large_scale_batch()
    
    print("All batch generation examples completed successfully!")


if __name__ == "__main__":
    main()