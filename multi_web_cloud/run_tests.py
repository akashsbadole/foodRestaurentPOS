#!/usr/bin/env python3
"""
Test Runner Script for Multi-Retail POS System
Provides various test execution options and reporting.
"""

import os
import sys
import argparse
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path


class TestRunner:
    """Test runner for the multi-retail POS system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / 'tests'
        self.results_dir = self.project_root / 'test_results'
        self.coverage_dir = self.project_root / 'htmlcov'
        
        # Ensure results directory exists
        self.results_dir.mkdir(exist_ok=True)
        self.coverage_dir.mkdir(exist_ok=True)
    
    def run_command(self, command, description):
        """Run a command and return results"""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        result = subprocess.run(
            command,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"\nExecution time: {execution_time:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        
        return result, execution_time
    
    def run_unit_tests(self):
        """Run unit tests only"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-m', 'unit',
            '-v',
            '--tb=short',
            '--cov=models',
            '--cov=routes',
            '--cov=utils',
            '--cov=services',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=json:test_results/coverage_unit.json',
            '--junit-xml=test_results/unit_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "Unit Tests")
        
        # Save results
        self.save_test_result('unit_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_integration_tests(self):
        """Run integration tests only"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-m', 'integration',
            '-v',
            '--tb=short',
            '--junit-xml=test_results/integration_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "Integration Tests")
        
        # Save results
        self.save_test_result('integration_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_performance_tests(self):
        """Run performance tests only"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_performance.py',
            '-v',
            '--tb=short',
            '--junit-xml=test_results/performance_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "Performance Tests")
        
        # Save results
        self.save_test_result('performance_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_security_tests(self):
        """Run security tests only"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_security_comprehensive.py',
            '-v',
            '--tb=short',
            '--junit-xml=test_results/security_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "Security Tests")
        
        # Save results
        self.save_test_result('security_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_feature_flag_tests(self):
        """Run feature flag tests only"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/test_feature_flags.py',
            '-v',
            '--tb=short',
            '--junit-xml=test_results/feature_flag_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "Feature Flag Tests")
        
        # Save results
        self.save_test_result('feature_flag_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_retail_specific_tests(self, retail_type=None):
        """Run retail-type specific tests"""
        if retail_type:
            marker = retail_type.lower()
            command = [
                sys.executable, '-m', 'pytest',
                'tests/',
                '-m', marker,
                '-v',
                '--tb=short',
                '--junit-xml=test_results/retail_{retail_type}_tests.xml'
            ]
        else:
            # Run all retail-specific tests
            markers = ['restaurant', 'apparel', 'books', 'grocery']
            command = [
                sys.executable, '-m', 'pytest',
                'tests/',
                '-m', ' or '.join(markers),
                '-v',
                '--tb=short',
                '--junit-xml=test_results/retail_all_tests.xml'
            ]
        
        result, execution_time = self.run_command(
            command, 
            f"Retail-Specific Tests ({retail_type or 'All'})"
        )
        
        # Save results
        test_name = f'retail_{retail_type}_tests' if retail_type else 'retail_all_tests'
        self.save_test_result(test_name, result, execution_time)
        
        return result.returncode == 0
    
    def run_all_tests(self):
        """Run all tests"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-v',
            '--tb=short',
            '--cov=models',
            '--cov=routes',
            '--cov=utils',
            '--cov=services',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-report=json:test_results/coverage_all.json',
            '--junit-xml=test_results/all_tests.xml'
        ]
        
        result, execution_time = self.run_command(command, "All Tests")
        
        # Save results
        self.save_test_result('all_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_quick_tests(self):
        """Run quick tests (unit tests only, no coverage)"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-m', 'unit and not slow',
            '-v',
            '--tb=short',
            '--maxfail=5'
        ]
        
        result, execution_time = self.run_command(command, "Quick Tests")
        
        # Save results
        self.save_test_result('quick_tests', result, execution_time)
        
        return result.returncode == 0
    
    def run_ci_tests(self):
        """Run tests optimized for CI/CD"""
        command = [
            sys.executable, '-m', 'pytest',
            'tests/',
            '-v',
            '--tb=short',
            '--cov=models',
            '--cov=routes',
            '--cov=utils',
            '--cov=services',
            '--cov-report=xml:test_results/coverage.xml',
            '--cov-report=html:htmlcov',
            '--cov-fail-under=80',
            '--junit-xml=test_results/ci_tests.xml',
            '--maxfail=10'
        ]
        
        result, execution_time = self.run_command(command, "CI/CD Tests")
        
        # Save results
        self.save_test_result('ci_tests', result, execution_time)
        
        return result.returncode == 0
    
    def save_test_result(self, test_name, result, execution_time):
        """Save test results to JSON file"""
        results_file = self.results_dir / f'{test_name}_result.json'
        
        result_data = {
            'test_name': test_name,
            'timestamp': datetime.now().isoformat(),
            'return_code': result.returncode,
            'execution_time': execution_time,
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
        with open(results_file, 'w') as f:
            json.dump(result_data, f, indent=2)
    
    def generate_report(self):
        """Generate comprehensive test report"""
        report_file = self.results_dir / 'test_report.html'
        
        # Collect all result files
        result_files = list(self.results_dir.glob('*_result.json'))
        
        if not result_files:
            print("No test results found to generate report")
            return
        
        # Load all results
        all_results = []
        for result_file in result_files:
            with open(result_file, 'r') as f:
                all_results.append(json.load(f))
        
        # Generate HTML report
        html_content = self._generate_html_report(all_results)
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        print(f"\nTest report generated: {report_file}")
    
    def _generate_html_report(self, results):
        """Generate HTML report content"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Retail POS Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .test-result { margin: 10px 0; padding: 15px; border-radius: 5px; }
        .success { background-color: #d4edda; border: 1px solid #c3e6cb; }
        .failure { background-color: #f8d7da; border: 1px solid #f5c6cb; }
        .summary { display: flex; justify-content: space-between; margin: 20px 0; }
        .summary-item { text-align: center; padding: 15px; background-color: #e9ecef; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Multi-Retail POS Test Report</h1>
        <p>Generated on: {}</p>
    </div>
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # Summary section
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['success'])
        failed_tests = total_tests - passed_tests
        total_time = sum(r['execution_time'] for r in results)
        
        html += f"""
    <div class="summary">
        <div class="summary-item">
            <h3>{total_tests}</h3>
            <p>Total Tests</p>
        </div>
        <div class="summary-item">
            <h3>{passed_tests}</h3>
            <p>Passed</p>
        </div>
        <div class="summary-item">
            <h3>{failed_tests}</h3>
            <p>Failed</p>
        </div>
        <div class="summary-item">
            <h3>{total_time:.2f}s</h3>
            <p>Total Time</p>
        </div>
    </div>
"""
        
        # Results table
        html += """
    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Test Name</th>
            <th>Status</th>
            <th>Execution Time</th>
            <th>Return Code</th>
            <th>Timestamp</th>
        </tr>
"""
        
        for result in results:
            status_class = 'success' if result['success'] else 'failure'
            status_text = 'PASSED' if result['success'] else 'FAILED'
            
            html += f"""
        <tr class="{status_class}">
            <td>{result['test_name']}</td>
            <td>{status_text}</td>
            <td>{result['execution_time']:.2f}s</td>
            <td>{result['return_code']}</td>
            <td>{result['timestamp']}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        
        return html
    
    def clean_results(self):
        """Clean previous test results"""
        import shutil
        
        # Clean results directory
        if self.results_dir.exists():
            shutil.rmtree(self.results_dir)
            self.results_dir.mkdir(exist_ok=True)
        
        # Clean coverage directory
        if self.coverage_dir.exists():
            shutil.rmtree(self.coverage_dir)
            self.coverage_dir.mkdir(exist_ok=True)
        
        # Clean .coverage files
        for coverage_file in self.project_root.glob('.coverage*'):
            coverage_file.unlink()
        
        print("Previous test results cleaned")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test Runner for Multi-Retail POS System')
    
    # Test type options
    parser.add_argument(
        'test_type',
        choices=[
            'unit', 'integration', 'performance', 'security',
            'feature-flags', 'retail', 'all', 'quick', 'ci'
        ],
        help='Type of tests to run'
    )
    
    # Retail type option
    parser.add_argument(
        '--retail-type',
        choices=['restaurant', 'apparel', 'books', 'grocery'],
        help='Specific retail type to test (only with "retail" test type)'
    )
    
    # Other options
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean previous test results before running'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate HTML report after running tests'
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner()
    
    # Clean results if requested
    if args.clean:
        runner.clean_results()
    
    # Run tests based on type
    success = True
    
    try:
        if args.test_type == 'unit':
            success = runner.run_unit_tests()
        elif args.test_type == 'integration':
            success = runner.run_integration_tests()
        elif args.test_type == 'performance':
            success = runner.run_performance_tests()
        elif args.test_type == 'security':
            success = runner.run_security_tests()
        elif args.test_type == 'feature-flags':
            success = runner.run_feature_flag_tests()
        elif args.test_type == 'retail':
            success = runner.run_retail_specific_tests(args.retail_type)
        elif args.test_type == 'all':
            success = runner.run_all_tests()
        elif args.test_type == 'quick':
            success = runner.run_quick_tests()
        elif args.test_type == 'ci':
            success = runner.run_ci_tests()
        
        # Generate report if requested
        if args.report:
            runner.generate_report()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()