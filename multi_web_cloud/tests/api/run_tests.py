"""
Test runner for API endpoints
"""
import sys
import os
import pytest

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == "__main__":
    # Run all API tests
    test_files = [
        "test_validation_api.py",
        "test_session_api.py",
        "test_offline_api.py",
        "test_security_api.py",
        "test_payment_api.py",
        "test_dashboard_api.py",
        "test_config_api.py"
    ]
    
    # Run pytest with the test files
    exit_code = pytest.main([
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes",  # Colored output
        "-x",  # Stop on first failure
        *test_files
    ])
    
    sys.exit(exit_code)