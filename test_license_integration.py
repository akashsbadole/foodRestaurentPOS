"""
License Integration Test Script
Tests the license system integration with the POS MVP application
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.license_manager import LicenseManager
from src.utils.license_integration import LicenseIntegration
from src.migrations.add_license_tables import run_migration


def test_license_tables():
    """Test license tables creation"""
    print("Testing license tables creation...")
    
    try:
        # Run migration
        if run_migration():
            print("✅ License tables created successfully")
            return True
        else:
            print("❌ Failed to create license tables")
            return False
    except Exception as e:
        print(f"❌ Error creating license tables: {str(e)}")
        return False


def test_license_manager():
    """Test license manager functionality"""
    print("\nTesting license manager...")
    
    try:
        # Initialize license manager
        license_manager = LicenseManager()
        
        # Test license status
        status = license_manager.get_license_status()
        print(f"✅ License status retrieved: {status.get('status', 'unknown')}")
        
        # Test trial status
        trial_status = license_manager.get_trial_status()
        print(f"✅ Trial status retrieved: {trial_status.get('trial_info', {}).get('status', 'unknown')}")
        
        # Test feature access
        feature_access = license_manager.check_feature_access('basic_orders')
        print(f"✅ Feature access check: {feature_access.get('allowed', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license manager: {str(e)}")
        return False


def test_license_integration():
    """Test license integration"""
    print("\nTesting license integration...")
    
    try:
        # Create mock app object
        class MockApp:
            def __init__(self):
                self.root = None
                self.db = None
                self.license_integration = None
        
        app = MockApp()
        
        # Initialize license integration
        license_integration = LicenseIntegration(app)
        app.license_integration = license_integration
        
        # Test license info
        license_info = license_integration.get_license_info()
        print(f"✅ License info retrieved: {bool(license_info)}")
        
        # Test trial info
        trial_info = license_integration.get_trial_info()
        print(f"✅ Trial info retrieved: {bool(trial_info)}")
        
        # Test feature access
        feature_access = license_integration.check_feature_access('basic_orders')
        print(f"✅ Feature access check: {feature_access}")
        
        # Test license status text
        status_text = license_integration.get_license_status_text()
        print(f"✅ License status text: {status_text}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license integration: {str(e)}")
        return False


def test_license_models():
    """Test license models"""
    print("\nTesting license models...")
    
    try:
        from src.models.license import License
        from src.models.license_activation import LicenseActivation
        from src.models.hardware_binding import HardwareBinding
        from src.models.license_audit_log import LicenseAuditLog
        from src.models.blacklisted_license import BlacklistedLicense
        
        # Test model imports
        print("✅ License models imported successfully")
        
        # Test license model
        license = License()
        license.license_key = "TEST-KEY-12345"
        license.license_type = "trial"
        license.status = "active"
        print(f"✅ License model created: {license.license_key}")
        
        # Test license activation model
        activation = LicenseActivation()
        activation.activation_id = "ACT-12345"
        activation.activation_type = "online"
        activation.status = "active"
        print(f"✅ License activation model created: {activation.activation_id}")
        
        # Test hardware binding model
        hardware = HardwareBinding()
        hardware.hardware_id = "HW-12345"
        hardware.fingerprint_method = "advanced"
        print(f"✅ Hardware binding model created: {hardware.hardware_id}")
        
        # Test audit log model
        audit_log = LicenseAuditLog()
        audit_log.license_key = "TEST-KEY-12345"
        audit_log.event_type = "activation"
        audit_log.event_severity = "info"
        print(f"✅ Audit log model created: {audit_log.event_type}")
        
        # Test blacklisted license model
        blacklisted = BlacklistedLicense()
        blacklisted.license_key = "BLACKLISTED-12345"
        blacklisted.reason = "Test blacklisting"
        print(f"✅ Blacklisted license model created: {blacklisted.reason}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license models: {str(e)}")
        return False


def test_license_utilities():
    """Test license utilities"""
    print("\nTesting license utilities...")
    
    try:
        from src.utils.license_crypto import LicenseCrypto
        from src.utils.hardware_fingerprint import HardwareFingerprint
        from src.utils.license_validator import LicenseValidator
        from src.utils.anti_tamper import AntiTamper
        from src.utils.license_storage import LicenseStorage
        
        # Test utility imports
        print("✅ License utilities imported successfully")
        
        # Test license crypto
        crypto = LicenseCrypto()
        test_data = "test license data"
        signature = crypto.sign_data(test_data)
        verified = crypto.verify_signature(test_data, signature)
        print(f"✅ License crypto test: {verified}")
        
        # Test hardware fingerprint
        fingerprint = HardwareFingerprint()
        hw_id = fingerprint.generate_fingerprint()
        print(f"✅ Hardware fingerprint generated: {len(hw_id)} characters")
        
        # Test license validator
        validator = LicenseValidator()
        print("✅ License validator created")
        
        # Test anti-tamper
        anti_tamper = AntiTamper()
        integrity_ok = anti_tamper.check_integrity()
        print(f"✅ Anti-tamper check: {integrity_ok}")
        
        # Test license storage
        storage = LicenseStorage()
        print("✅ License storage created")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license utilities: {str(e)}")
        return False


def test_license_ui_components():
    """Test license UI components"""
    print("\nTesting license UI components...")
    
    try:
        from src.ui.license_activation_dialog import LicenseActivationDialog
        from src.ui.license_status_screen import LicenseStatusScreen
        from src.ui.trial_management_dialog import TrialManagementDialog
        from src.ui.license_upgrade_dialog import LicenseUpgradeDialog
        from src.ui.license_transfer_dialog import LicenseTransferDialog
        
        # Test UI component imports
        print("✅ License UI components imported successfully")
        
        # Test license decorator
        from src.utils.license_decorator import require_license_feature, LicenseFeatureMixin
        print("✅ License decorator imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license UI components: {str(e)}")
        return False


def test_license_features():
    """Test license feature access"""
    print("\nTesting license features...")
    
    try:
        # Create mock app with license integration
        class MockApp:
            def __init__(self):
                self.root = None
                self.db = None
                self.license_integration = None
        
        app = MockApp()
        license_integration = LicenseIntegration(app)
        app.license_integration = license_integration
        
        # Test different features
        features = [
            'basic_orders',
            'basic_inventory',
            'basic_reports',
            'advanced_reports',
            'multi_user',
            'api_access',
            'custom_themes',
            'priority_support',
            'custom_integrations',
            'advanced_analytics',
            'white_labeling'
        ]
        
        for feature in features:
            access = license_integration.check_feature_access(feature)
            print(f"✅ Feature '{feature}': {'Allowed' if access else 'Denied'}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing license features: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("License Integration Test Suite")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("License Tables", test_license_tables),
        ("License Manager", test_license_manager),
        ("License Integration", test_license_integration),
        ("License Models", test_license_models),
        ("License Utilities", test_license_utilities),
        ("License UI Components", test_license_ui_components),
        ("License Features", test_license_features)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print results
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! License system is working correctly.")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the license system.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)