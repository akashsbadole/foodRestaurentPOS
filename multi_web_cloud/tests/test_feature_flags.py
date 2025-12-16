"""
Comprehensive Feature Flag Testing Framework
Tests all aspects of the feature flag system including parsing, validation,
dependency resolution, conflict detection, and hierarchical precedence.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Import application and managers
from app import create_app
from config import Config
from utils.feature_flag_manager import FeatureFlagManager
from utils.environment_flag_parser import EnvironmentFlagParser
from utils.feature_validator import FeatureValidator
from utils.retail_type_manager import get_retail_type_manager
from utils.dynamic_model_loader import get_model_loader

# Import models
from models import db, FeatureDefinition, FeatureDependency, FeatureConflict, RetailTypePreset, TenantFeatureFlag


class TestFeatureFlagParsing(unittest.TestCase):
    """Test feature flag parsing and validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        # Create test app
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        # Create application context
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Initialize managers
        cls.parser = EnvironmentFlagParser()
        cls.validator = FeatureValidator()
        cls.feature_manager = FeatureFlagManager()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def test_environment_flag_parsing(self):
        """Test parsing of feature flags from environment"""
        print("\n=== Testing Environment Flag Parsing ===")
        
        # Test with mock environment
        test_env = {
            'FEATURE_SALES_PROCESSING': 'true',
            'FEATURE_TABLE_MANAGEMENT': 'false',
            'FEATURE_BARCODE_SCANNING': '1',
            'FEATURE_LOYALTY_PROGRAM': 'yes',
            'FEATURE_CRM': 'on',
            'FEATURE_AI_RECOMMENDATIONS': 'enabled',
            'FEATURE_EXPIRY_TRACKING': '0',
            'FEATURE_BATCH_TRACKING': 'disabled'
        }
        
        with patch.dict(os.environ, test_env):
            flags = self.parser.parse_environment_flags()
            
            # Test boolean conversion
            self.assertTrue(flags.get('FEATURE_SALES_PROCESSING', False), "Should convert 'true' to True")
            self.assertFalse(flags.get('FEATURE_TABLE_MANAGEMENT', True), "Should convert 'false' to False")
            self.assertTrue(flags.get('FEATURE_BARCODE_SCANNING', False), "Should convert '1' to True")
            self.assertTrue(flags.get('FEATURE_LOYALTY_PROGRAM', False), "Should convert 'yes' to True")
            self.assertTrue(flags.get('FEATURE_CRM', False), "Should convert 'on' to True")
            self.assertTrue(flags.get('FEATURE_AI_RECOMMENDATIONS', False), "Should convert 'enabled' to True")
            self.assertFalse(flags.get('FEATURE_EXPIRY_TRACKING', True), "Should convert '0' to False")
            self.assertFalse(flags.get('FEATURE_BATCH_TRACKING', True), "Should convert 'disabled' to False")
        
        print("✅ Environment flag parsing tests passed")
    
    def test_flag_validation(self):
        """Test feature flag validation against definitions"""
        print("\n=== Testing Flag Validation ===")
        
        # Test valid flags
        valid_flags = {
            'FEATURE_SALES_PROCESSING': True,
            'FEATURE_TABLE_MANAGEMENT': False,
            'FEATURE_BARCODE_SCANNING': True
        }
        
        validation_result = self.parser.validate_flag_values(valid_flags)
        self.assertTrue(validation_result.is_valid, "Valid flags should pass validation")
        
        # Test invalid flag values
        invalid_flags = {
            'FEATURE_SALES_PROCESSING': 'not_a_boolean',
            'FEATURE_BARCODE_SCANNING': 123.456  # Should be boolean
        }
        
        validation_result = self.parser.validate_flag_values(invalid_flags)
        self.assertFalse(validation_result.is_valid, "Invalid flags should fail validation")
        self.assertGreater(len(validation_result.errors), 0, "Should have validation errors")
        
        # Test unknown flags
        unknown_flags = {
            'FEATURE_UNKNOWN_FEATURE': True,
            'FEATURE_ANOTHER_UNKNOWN': False
        }
        
        validation_result = self.parser.validate_flag_values(unknown_flags)
        self.assertGreater(len(validation_result.warnings), 0, "Should warn about unknown features")
        
        print("✅ Flag validation tests passed")
    
    def test_flag_conflict_detection(self):
        """Test detection of conflicting feature flags"""
        print("\n=== Testing Flag Conflict Detection ===")
        
        # Test conflicting flags
        conflicting_flags = {
            'FEATURE_TABLE_MANAGEMENT': True,
            'FEATURE_QUICK_SALE': True,  # Should conflict with table management
            'FEATURE_ADVANCED_INVENTORY': True,
            'FEATURE_BASIC_INVENTORY': True  # Should conflict with advanced inventory
        }
        
        conflicts = self.parser.detect_flag_conflicts(conflicting_flags)
        self.assertGreater(len(conflicts), 0, "Should detect conflicts")
        
        # Check for specific conflicts
        conflict_messages = ' '.join(conflicts)
        self.assertIn('FEATURE_TABLE_MANAGEMENT', conflict_messages, "Should detect table management conflict")
        self.assertIn('FEATURE_QUICK_SALE', conflict_messages, "Should detect quick sale conflict")
        self.assertIn('FEATURE_ADVANCED_INVENTORY', conflict_messages, "Should detect advanced inventory conflict")
        self.assertIn('FEATURE_BASIC_INVENTORY', conflict_messages, "Should detect basic inventory conflict")
        
        print("✅ Flag conflict detection tests passed")
    
    def test_retail_type_compatibility(self):
        """Test retail type compatibility validation"""
        print("\n=== Testing Retail Type Compatibility ===")
        
        # Test restaurant-specific features
        restaurant_features = {
            'FEATURE_TABLE_MANAGEMENT': True,
            'FEATURE_KOT_PRINTING': True,
            'FEATURE_KITCHEN_DISPLAY': True
        }
        
        validation_result = self.validator.validate_feature_combination(list(restaurant_features.keys()), 'tenant1')
        self.assertTrue(validation_result['valid'], "Restaurant features should be compatible")
        
        # Test incompatible features for retail type
        incompatible_features = {
            'FEATURE_TABLE_MANAGEMENT': True,  # Restaurant only
            'FEATURE_SIZE_VARIANTS': True,    # Apparel only
            'FEATURE_WEIGHING_SCALE': True     # Grocery only
        }
        
        # Mock tenant retail type
        with patch.object(self.feature_manager, 'get_tenant_retail_type', return_value='restaurant'):
            validation_result = self.validator.validate_feature_combination(
                list(incompatible_features.keys()), 'tenant1'
            )
            
            # Should have warnings about incompatible features
            self.assertGreater(len(validation_result['warnings']), 0, 
                            "Should warn about incompatible features")
        
        print("✅ Retail type compatibility tests passed")


class TestFeatureDependencyResolution(unittest.TestCase):
    """Test feature dependency resolution and validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls.feature_manager = FeatureFlagManager()
        cls.feature_manager.initialize()
        
        # Create test dependencies
        cls._create_test_dependencies()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_dependencies(cls):
        """Create test feature dependencies"""
        # Create feature definitions
        features = [
            FeatureDefinition(
                name='FEATURE_SALES_PROCESSING',
                display_name='Sales Processing',
                description='Enable sales processing',
                category='core',
                default_value=True,
                is_required=True
            ),
            FeatureDefinition(
                name='FEATURE_CUSTOMER_MANAGEMENT',
                display_name='Customer Management',
                description='Enable customer management',
                category='core',
                default_value=False,
                is_required=False
            ),
            FeatureDefinition(
                name='FEATURE_LOYALTY_PROGRAM',
                display_name='Loyalty Program',
                description='Enable loyalty program',
                category='advanced',
                default_value=False,
                is_required=False
            ),
            FeatureDefinition(
                name='FEATURE_CRM',
                display_name='CRM',
                description='Enable CRM functionality',
                category='advanced',
                default_value=False,
                is_required=False
            )
        ]
        
        for feature in features:
            db.session.add(feature)
        
        # Create dependencies
        dependencies = [
            FeatureDependency(
                feature_name='FEATURE_LOYALTY_PROGRAM',
                depends_on_feature='FEATURE_CUSTOMER_MANAGEMENT',
                dependency_type='required',
                description='Loyalty program requires customer management'
            ),
            FeatureDependency(
                feature_name='FEATURE_CRM',
                depends_on_feature='FEATURE_CUSTOMER_MANAGEMENT',
                dependency_type='required',
                description='CRM requires customer management'
            ),
            FeatureDependency(
                feature_name='FEATURE_CRM',
                depends_on_feature='FEATURE_LOYALTY_PROGRAM',
                dependency_type='optional',
                description='CRM optionally works with loyalty program'
            )
        ]
        
        for dep in dependencies:
            db.session.add(dep)
        
        db.session.commit()
    
    def test_dependency_validation(self):
        """Test feature dependency validation"""
        print("\n=== Testing Dependency Validation ===")
        
        # Test valid feature combination
        valid_features = [
            'FEATURE_SALES_PROCESSING',
            'FEATURE_CUSTOMER_MANAGEMENT',
            'FEATURE_LOYALTY_PROGRAM'
        ]
        
        validation_result = self.feature_manager.validate_feature_combination(valid_features)
        self.assertTrue(validation_result['valid'], "Valid feature combination should pass")
        
        # Test missing dependencies
        invalid_features = [
            'FEATURE_SALES_PROCESSING',
            'FEATURE_LOYALTY_PROGRAM'  # Missing CUSTOMER_MANAGEMENT dependency
        ]
        
        validation_result = self.feature_manager.validate_feature_combination(invalid_features)
        self.assertFalse(validation_result['valid'], "Missing dependencies should fail validation")
        self.assertGreater(len(validation_result['errors']), 0, "Should have dependency errors")
        
        # Check error message
        error_messages = ' '.join(validation_result['errors'])
        self.assertIn('FEATURE_LOYALTY_PROGRAM', error_messages, "Should mention loyalty program")
        self.assertIn('FEATURE_CUSTOMER_MANAGEMENT', error_messages, "Should mention customer management")
        
        print("✅ Dependency validation tests passed")
    
    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies"""
        print("\n=== Testing Circular Dependency Detection ===")
        
        # Create circular dependency
        circular_dep = FeatureDependency(
            feature_name='FEATURE_CUSTOMER_MANAGEMENT',
            depends_on_feature='FEATURE_LOYALTY_PROGRAM',
            dependency_type='required',
            description='Circular dependency test'
        )
        db.session.add(circular_dep)
        db.session.commit()
        
        # Reload dependencies
        self.feature_manager.load_feature_definitions()
        
        # Check for circular dependencies
        circular_deps = self.feature_manager.validator.find_circular_dependencies()
        self.assertGreater(len(circular_deps), 0, "Should detect circular dependencies")
        
        # Clean up
        db.session.delete(circular_dep)
        db.session.commit()
        
        print("✅ Circular dependency detection tests passed")
    
    def test_dependency_resolution_order(self):
        """Test dependency resolution order"""
        print("\n=== Testing Dependency Resolution Order ===")
        
        # Enable features in wrong order
        with patch.object(self.feature_manager, 'enable_feature') as mock_enable:
            # Try to enable CRM (should enable dependencies first)
            success = self.feature_manager.enable_feature('FEATURE_CRM', 'test_tenant')
            
            # Check that dependencies were enabled first
            if success:
                # Verify enable was called for dependencies
                enable_calls = [call[0][0] for call in mock_enable.call_args_list]
                self.assertIn('FEATURE_CUSTOMER_MANAGEMENT', enable_calls, 
                           "Should enable customer management first")
        
        print("✅ Dependency resolution order tests passed")


class TestHierarchicalFeaturePrecedence(unittest.TestCase):
    """Test hierarchical feature precedence (Environment > Tenant > Runtime)"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls.feature_manager = FeatureFlagManager()
        cls.feature_manager.initialize()
        
        # Create test tenant and feature flags
        cls._create_test_tenant_and_flags()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    @classmethod
    def _create_test_tenant_and_flags(cls):
        """Create test tenant and feature flags"""
        # Create feature definition
        feature_def = FeatureDefinition(
            name='FEATURE_TEST_HIERARCHY',
            display_name='Test Hierarchy',
            description='Test feature for hierarchy',
            category='test',
            default_value=False
        )
        db.session.add(feature_def)
        
        # Create tenant feature flag
        tenant_flag = TenantFeatureFlag(
            tenant_id='test_tenant',
            feature_name='FEATURE_TEST_HIERARCHY',
            is_active=True,
            configuration={'test': 'value'}
        )
        db.session.add(tenant_flag)
        
        db.session.commit()
    
    def test_environment_precedence(self):
        """Test environment flag precedence"""
        print("\n=== Testing Environment Precedence ===")
        
        # Set environment flag
        with patch.dict(os.environ, {'FEATURE_TEST_HIERARCHY': 'true'}):
            # Reload environment flags
            self.feature_manager.load_environment_flags()
            
            # Check if environment flag takes precedence
            is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
            self.assertTrue(is_enabled, "Environment flag should take precedence")
        
        print("✅ Environment precedence tests passed")
    
    def test_tenant_precedence(self):
        """Test tenant flag precedence"""
        print("\n=== Testing Tenant Precedence ===")
        
        # Check if tenant flag is enabled
        is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
        self.assertTrue(is_enabled, "Tenant flag should be enabled")
        
        # Check for different tenant (should be default)
        is_enabled_other = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'other_tenant')
        self.assertFalse(is_enabled_other, "Other tenant should use default value")
        
        print("✅ Tenant precedence tests passed")
    
    def test_runtime_precedence(self):
        """Test runtime override precedence"""
        print("\n=== Testing Runtime Precedence ===")
        
        # Apply runtime override
        self.feature_manager.apply_runtime_override('FEATURE_TEST_HIERARCHY', False, 'test_tenant')
        
        # Check if runtime override takes precedence
        is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
        self.assertFalse(is_enabled, "Runtime override should take precedence")
        
        # Clear runtime override
        self.feature_manager.runtime_flags['test_tenant'].pop('FEATURE_TEST_HIERARCHY', None)
        
        # Check if tenant flag is back
        is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
        self.assertTrue(is_enabled, "Tenant flag should be restored after clearing runtime override")
        
        print("✅ Runtime precedence tests passed")
    
    def test_precedence_hierarchy(self):
        """Test complete precedence hierarchy"""
        print("\n=== Testing Complete Precedence Hierarchy ===")
        
        # 1. Set environment flag
        with patch.dict(os.environ, {'FEATURE_TEST_HIERARCHY': 'false'}):
            self.feature_manager.load_environment_flags()
            
            # 2. Set tenant flag (should override environment)
            tenant_flag = TenantFeatureFlag.query.filter_by(
                tenant_id='test_tenant',
                feature_name='FEATURE_TEST_HIERARCHY'
            ).first()
            tenant_flag.is_active = True
            db.session.commit()
            
            # 3. Apply runtime override (should override tenant)
            self.feature_manager.apply_runtime_override('FEATURE_TEST_HIERARCHY', True, 'test_tenant')
            
            # Check precedence
            is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
            self.assertTrue(is_enabled, "Runtime override should have highest precedence")
            
            # Clear runtime override
            self.feature_manager.runtime_flags['test_tenant'].pop('FEATURE_TEST_HIERARCHY', None)
            
            # Check tenant override of environment
            is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
            self.assertTrue(is_enabled, "Tenant flag should override environment")
            
            # Disable tenant flag
            tenant_flag.is_active = False
            db.session.commit()
            
            # Check environment fallback
            is_enabled = self.feature_manager.is_enabled('FEATURE_TEST_HIERARCHY', 'test_tenant')
            self.assertFalse(is_enabled, "Environment flag should be fallback")
        
        print("✅ Complete precedence hierarchy tests passed")


class TestDynamicModelLoading(unittest.TestCase):
    """Test dynamic model loading based on feature flags"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls.feature_manager = FeatureFlagManager()
        cls.feature_manager.initialize()
        
        cls.model_loader = get_model_loader(cls.feature_manager)
        cls.model_loader.initialize()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def test_conditional_model_loading(self):
        """Test conditional model loading based on features"""
        print("\n=== Testing Conditional Model Loading ===")
        
        # Test loading models for tenant with specific features
        with patch.object(cls.feature_manager, 'get_enabled_features', 
                       return_value={'FEATURE_TABLE_MANAGEMENT', 'FEATURE_SALES_PROCESSING'}):
            
            results = self.model_loader.load_models_for_tenant('test_tenant')
            
            self.assertIsInstance(results, dict, "Should return results dictionary")
            self.assertIn('loaded', results, "Should have loaded models")
            self.assertIn('skipped', results, "Should have skipped models")
            self.assertIn('failed', results, "Should have failed models")
            
            # Check that table-related models are loaded
            loaded_models = results['loaded']
            self.assertGreater(len(loaded_models), 0, "Should load some models")
        
        print("✅ Conditional model loading tests passed")
    
    def test_model_dependency_validation(self):
        """Test model dependency validation"""
        print("\n=== Testing Model Dependency Validation ===")
        
        # Test model dependency validation
        validation_results = self.model_loader.validate_model_dependencies('test_tenant')
        
        self.assertIsInstance(validation_results, dict, "Should return validation results")
        self.assertIn('valid', validation_results, "Should have validity status")
        self.assertIn('errors', validation_results, "Should have errors list")
        self.assertIn('warnings', validation_results, "Should have warnings list")
        self.assertIn('model_status', validation_results, "Should have model status")
        
        print("✅ Model dependency validation tests passed")
    
    def test_model_table_creation(self):
        """Test conditional table creation"""
        print("\n=== Testing Model Table Creation ===")
        
        # Test table creation for tenant
        with patch.object(cls.feature_manager, 'get_enabled_features',
                       return_value={'FEATURE_TABLE_MANAGEMENT'}):
            
            results = self.model_loader.create_model_tables('test_tenant')
            
            self.assertIsInstance(results, dict, "Should return results dictionary")
            # Table creation should succeed for enabled features
        
        print("✅ Model table creation tests passed")


class TestRetailTypeFeaturePresets(unittest.TestCase):
    """Test retail type feature presets"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_config = {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key'
        }
        
        cls.app = create_app('testing')
        cls.app.config.update(cls.test_config)
        
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        db.create_all()
        
        cls.feature_manager = FeatureFlagManager()
        cls.feature_manager.initialize()
        
        cls.retail_manager = get_retail_type_manager(cls.feature_manager)
        cls.retail_manager.initialize()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()
    
    def test_retail_type_preset_creation(self):
        """Test retail type preset creation"""
        print("\n=== Testing Retail Type Preset Creation ===")
        
        # Create preset for restaurant
        preset_features = {
            'FEATURE_SALES_PROCESSING': True,
            'FEATURE_TABLE_MANAGEMENT': True,
            'FEATURE_KOT_PRINTING': True,
            'FEATURE_BARCODE_SCANNING': False
        }
        
        result = self.retail_manager.create_retail_type_preset(
            'restaurant',
            'Test Restaurant Preset',
            preset_features,
            'Test preset for restaurant'
        )
        
        self.assertTrue(result['success'], "Preset creation should succeed")
        self.assertIn('preset_id', result, "Should return preset ID")
        
        print("✅ Retail type preset creation tests passed")
    
    def test_retail_type_preset_application(self):
        """Test applying retail type preset to tenant"""
        print("\n=== Testing Retail Type Preset Application ===")
        
        # Create preset first
        preset = RetailTypePreset(
            retail_type='restaurant',
            name='Test Restaurant Preset',
            description='Test preset',
            feature_flags={
                'FEATURE_SALES_PROCESSING': True,
                'FEATURE_TABLE_MANAGEMENT': True,
                'FEATURE_KOT_PRINTING': True
            }
        )
        db.session.add(preset)
        db.session.commit()
        
        # Apply preset to tenant
        result = self.retail_manager.apply_retail_type_preset('test_tenant', 'restaurant')
        
        self.assertTrue(result['success'], "Preset application should succeed")
        self.assertIn('applied_features', result, "Should list applied features")
        self.assertGreater(len(result['applied_features']), 0, "Should apply some features")
        
        print("✅ Retail type preset application tests passed")
    
    def test_retail_type_feature_validation(self):
        """Test retail type feature validation"""
        print("\n=== Testing Retail Type Feature Validation ===")
        
        # Test valid restaurant features
        restaurant_features = {
            'FEATURE_SALES_PROCESSING',
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_KOT_PRINTING',
            'FEATURE_KITCHEN_DISPLAY'
        }
        
        validation_result = self.retail_manager.validate_retail_type_features(
            'restaurant', restaurant_features
        )
        
        self.assertTrue(validation_result['valid'], "Restaurant features should be valid")
        
        # Test invalid features for retail type
        invalid_features = {
            'FEATURE_SALES_PROCESSING',
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_SIZE_VARIANTS'  # Not valid for restaurant
        }
        
        validation_result = self.retail_manager.validate_retail_type_features(
            'restaurant', invalid_features
        )
        
        self.assertFalse(validation_result['valid'], "Invalid features should fail validation")
        self.assertGreater(len(validation_result['missing_required']), 0, 
                        "Should have missing required features")
        
        print("✅ Retail type feature validation tests passed")


def run_feature_flag_tests():
    """Run all feature flag tests"""
    print("=" * 80)
    print("FEATURE FLAG TESTING FRAMEWORK")
    print("=" * 80)
    print("Testing feature flag parsing, validation, dependencies, and precedence\n")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFeatureFlagParsing,
        TestFeatureDependencyResolution,
        TestHierarchicalFeaturePrecedence,
        TestDynamicModelLoading,
        TestRetailTypeFeaturePresets
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*80}")
    print("FEATURE FLAG TEST RESULTS")
    print(f"{'='*80}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")
    
    print(f"\n{'='*80}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_feature_flag_tests()
    
    if success:
        print("\n✅ ALL FEATURE FLAG TESTS PASSED!")
        print("Feature flag system is working correctly")
        exit(0)
    else:
        print("\n❌ SOME FEATURE FLAG TESTS FAILED!")
        print("Review and fix feature flag issues")
        exit(1)