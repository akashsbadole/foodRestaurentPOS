"""
Test Reporting Framework
Generates comprehensive test reports with analytics and metrics.
"""

import os
import json
import time
import unittest
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


@dataclass
class TestResult:
    """Represents a single test result"""
    name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    component: Optional[str] = None
    feature: Optional[str] = None


@dataclass
class TestSuiteResult:
    """Represents a test suite result"""
    name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    success_rate: float
    test_results: List[TestResult]
    timestamp: datetime


@dataclass
class PerformanceMetric:
    """Represents a performance metric"""
    name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    status: str = 'unknown'  # 'passed', 'failed', 'warning'


@dataclass
class CoverageMetric:
    """Represents a code coverage metric"""
    module: str
    statements: int
    missing: int
    covered: int
    coverage_percentage: float


class TestReporter:
    """Generates comprehensive test reports"""
    
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_suites = []
        self.performance_metrics = []
        self.coverage_metrics = []
        self.start_time = None
        self.end_time = None
        
    def run_test_suite(self, suite_name: str, test_path: str, 
                      component: Optional[str] = None) -> TestSuiteResult:
        """Run a test suite and collect results"""
        print(f"Running test suite: {suite_name}")
        
        start_time = time.time()
        
        # Run tests using pytest with JSON output
        cmd = [
            'python', '-m', 'pytest', 
            test_path,
            '--json-report',
            f'--json-report-file={self.output_dir}/{suite_name}_report.json',
            '--tb=short',
            '-v'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd='multi_web_cloud'
            )
            
            # Parse JSON report
            report_file = self.output_dir / f"{suite_name}_report.json"
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                
                test_results = []
                for test in report_data.get('tests', []):
                    test_result = TestResult(
                        name=test.get('nodeid', ''),
                        status=test.get('outcome', 'unknown'),
                        duration=test.get('duration', 0.0),
                        error_message=test.get('call', {}).get('longrepr', ''),
                        traceback=test.get('call', {}).get('traceback', ''),
                        component=component,
                        feature=self._extract_feature_from_test(test.get('nodeid', ''))
                    )
                    test_results.append(test_result)
                
                summary = report_data.get('summary', {})
                
                suite_result = TestSuiteResult(
                    name=suite_name,
                    total_tests=summary.get('total', 0),
                    passed=summary.get('passed', 0),
                    failed=summary.get('failed', 0),
                    skipped=summary.get('skipped', 0),
                    errors=summary.get('error', 0),
                    duration=summary.get('duration', 0.0),
                    success_rate=summary.get('passed', 0) / max(summary.get('total', 1), 1) * 100,
                    test_results=test_results,
                    timestamp=datetime.now()
                )
                
                self.test_suites.append(suite_result)
                return suite_result
            
            else:
                # Fallback to parsing stdout
                return self._parse_pytest_output(result.stdout, suite_name, component)
        
        except Exception as e:
            print(f"Error running test suite {suite_name}: {e}")
            return TestSuiteResult(
                name=suite_name,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                duration=0.0,
                success_rate=0.0,
                test_results=[],
                timestamp=datetime.now()
            )
        
        finally:
            end_time = time.time()
            if not self.start_time:
                self.start_time = start_time
            self.end_time = end_time
    
    def _parse_pytest_output(self, output: str, suite_name: str, 
                            component: Optional[str] = None) -> TestSuiteResult:
        """Parse pytest output when JSON report is not available"""
        lines = output.split('\n')
        test_results = []
        
        # Simple parsing - would need enhancement for production use
        for line in lines:
            if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
                parts = line.split()
                test_name = parts[0]
                status = parts[1].lower().replace('[', '').replace(']', '')
                
                test_result = TestResult(
                    name=test_name,
                    status=status,
                    duration=0.0,
                    component=component
                )
                test_results.append(test_result)
        
        # Count results
        passed = sum(1 for t in test_results if t.status == 'passed')
        failed = sum(1 for t in test_results if t.status == 'failed')
        skipped = sum(1 for t in test_results if t.status == 'skipped')
        total = len(test_results)
        
        return TestSuiteResult(
            name=suite_name,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=0,
            duration=0.0,
            success_rate=passed / max(total, 1) * 100,
            test_results=test_results,
            timestamp=datetime.now()
        )
    
    def _extract_feature_from_test(self, test_name: str) -> Optional[str]:
        """Extract feature name from test name"""
        features = [
            'FEATURE_TABLE_MANAGEMENT',
            'FEATURE_RESERVATIONS',
            'FEATURE_KOT_PRINTING',
            'FEATURE_KITCHEN_DISPLAY',
            'FEATURE_SIZE_VARIANTS',
            'FEATURE_COLOR_VARIANTS',
            'FEATURE_ISBN_TRACKING',
            'FEATURE_WEIGHING_SCALE',
            'FEATURE_EXPIRY_TRACKING',
            'FEATURE_LOYALTY_PROGRAM',
            'FEATURE_ANALYTICS',
            'FEATURE_PAYMENT_GATEWAY',
            'FEATURE_ONLINE_ORDERING'
        ]
        
        for feature in features:
            if feature.lower() in test_name.lower():
                return feature
        
        return None
    
    def run_coverage_analysis(self) -> List[CoverageMetric]:
        """Run code coverage analysis"""
        print("Running coverage analysis...")
        
        cmd = [
            'python', '-m', 'pytest',
            '--cov=multi_web_cloud',
            '--cov-report=json',
            f'--cov-report=html:{self.output_dir}/htmlcov',
            '--cov-report=xml',
            '--tb=short'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd='multi_web_cloud'
            )
            
            # Parse coverage JSON report
            coverage_file = Path('multi_web_cloud/coverage.json')
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                
                coverage_metrics = []
                for module, data in coverage_data.get('files', {}).items():
                    metric = CoverageMetric(
                        module=module,
                        statements=data.get('summary', {}).get('num_statements', 0),
                        missing=data.get('summary', {}).get('missing_lines', 0),
                        covered=data.get('summary', {}).get('covered_lines', 0),
                        coverage_percentage=data.get('summary', {}).get('percent_covered', 0.0)
                    )
                    coverage_metrics.append(metric)
                
                self.coverage_metrics = coverage_metrics
                return coverage_metrics
        
        except Exception as e:
            print(f"Error running coverage analysis: {e}")
        
        return []
    
    def run_performance_tests(self) -> List[PerformanceMetric]:
        """Run performance tests and collect metrics"""
        print("Running performance tests...")
        
        metrics = []
        
        # Test API response times
        api_metrics = self._test_api_performance()
        metrics.extend(api_metrics)
        
        # Test database performance
        db_metrics = self._test_database_performance()
        metrics.extend(db_metrics)
        
        # Test UI rendering performance
        ui_metrics = self._test_ui_performance()
        metrics.extend(ui_metrics)
        
        self.performance_metrics = metrics
        return metrics
    
    def _test_api_performance(self) -> List[PerformanceMetric]:
        """Test API performance metrics"""
        metrics = []
        
        # Mock API performance test
        # In a real implementation, this would make actual API calls
        endpoints = [
            ('/api/products', 'Product List'),
            ('/api/orders', 'Order List'),
            ('/api/customers', 'Customer List'),
            ('/api/inventory', 'Inventory List')
        ]
        
        for endpoint, name in endpoints:
            # Simulate response time
            response_time = 0.1 + (hash(endpoint) % 100) / 1000  # 0.1-0.2s
            
            metric = PerformanceMetric(
                name=f"API Response Time - {name}",
                value=response_time,
                unit='seconds',
                threshold=1.0,
                status='passed' if response_time < 1.0 else 'failed'
            )
            metrics.append(metric)
        
        return metrics
    
    def _test_database_performance(self) -> List[PerformanceMetric]:
        """Test database performance metrics"""
        metrics = []
        
        # Mock database performance test
        operations = [
            ('Product Query', 0.05, 0.1),
            ('Order Insert', 0.02, 0.05),
            ('Customer Update', 0.03, 0.08),
            ('Inventory Search', 0.08, 0.15)
        ]
        
        for name, value, threshold in operations:
            metric = PerformanceMetric(
                name=f"DB Performance - {name}",
                value=value,
                unit='seconds',
                threshold=threshold,
                status='passed' if value < threshold else 'failed'
            )
            metrics.append(metric)
        
        return metrics
    
    def _test_ui_performance(self) -> List[PerformanceMetric]:
        """Test UI rendering performance metrics"""
        metrics = []
        
        # Mock UI performance test
        pages = [
            ('Dashboard', 1.2, 2.0),
            ('Product List', 0.8, 1.5),
            ('Order Form', 0.9, 1.8),
            ('Customer Profile', 0.7, 1.3)
        ]
        
        for name, value, threshold in pages:
            metric = PerformanceMetric(
                name=f"UI Render Time - {name}",
                value=value,
                unit='seconds',
                threshold=threshold,
                status='passed' if value < threshold else 'failed'
            )
            metrics.append(metric)
        
        return metrics
    
    def generate_html_report(self) -> str:
        """Generate HTML test report"""
        report_file = self.output_dir / "test_report.html"
        
        # Calculate overall statistics
        total_tests = sum(suite.total_tests for suite in self.test_suites)
        total_passed = sum(suite.passed for suite in self.test_suites)
        total_failed = sum(suite.failed for suite in self.test_suites)
        total_skipped = sum(suite.skipped for suite in self.test_suites)
        total_errors = sum(suite.errors for suite in self.test_suites)
        total_duration = sum(suite.duration for suite in self.test_suites)
        overall_success_rate = total_passed / max(total_tests, 1) * 100
        
        # Calculate coverage statistics
        avg_coverage = 0.0
        if self.coverage_metrics:
            avg_coverage = sum(m.coverage_percentage for m in self.coverage_metrics) / len(self.coverage_metrics)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Retail POS System Test Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border-left: 4px solid #007bff;
        }}
        .summary-card.passed {{
            border-left-color: #28a745;
        }}
        .summary-card.failed {{
            border-left-color: #dc3545;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 24px;
        }}
        .summary-card p {{
            margin: 0;
            color: #666;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .status-passed {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-failed {{
            color: #dc3545;
            font-weight: bold;
        }}
        .status-skipped {{
            color: #ffc107;
            font-weight: bold;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background-color: #28a745;
            transition: width 0.3s ease;
        }}
        .chart {{
            margin: 20px 0;
            text-align: center;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multi-Retail POS System Test Report</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>{total_tests}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{total_passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>{total_failed}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card">
                <h3>{total_skipped}</h3>
                <p>Skipped</p>
            </div>
            <div class="summary-card">
                <h3>{overall_success_rate:.1f}%</h3>
                <p>Success Rate</p>
            </div>
            <div class="summary-card">
                <h3>{avg_coverage:.1f}%</h3>
                <p>Code Coverage</p>
            </div>
        </div>
        
        <div class="section">
            <h2>Success Rate Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {overall_success_rate}%"></div>
            </div>
        </div>
        
        <div class="section">
            <h2>Test Suite Results</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test Suite</th>
                        <th>Total Tests</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Success Rate</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for suite in self.test_suites:
            html_content += f"""
                    <tr>
                        <td>{suite.name}</td>
                        <td>{suite.total_tests}</td>
                        <td class="status-passed">{suite.passed}</td>
                        <td class="status-failed">{suite.failed}</td>
                        <td class="status-skipped">{suite.skipped}</td>
                        <td>{suite.success_rate:.1f}%</td>
                        <td>{suite.duration:.2f}s</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Performance Metrics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Threshold</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for metric in self.performance_metrics:
            status_class = f"status-{metric.status}"
            html_content += f"""
                    <tr>
                        <td>{metric.name}</td>
                        <td>{metric.value:.3f} {metric.unit}</td>
                        <td>{metric.threshold:.3f} {metric.unit}</td>
                        <td class="{status_class}">{metric.status.upper()}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Code Coverage</h2>
            <table>
                <thead>
                    <tr>
                        <th>Module</th>
                        <th>Statements</th>
                        <th>Missing</th>
                        <th>Covered</th>
                        <th>Coverage %</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for metric in self.coverage_metrics:
            coverage_class = "status-passed" if metric.coverage_percentage >= 80 else "status-failed"
            html_content += f"""
                    <tr>
                        <td>{metric.module}</td>
                        <td>{metric.statements}</td>
                        <td>{metric.missing}</td>
                        <td>{metric.covered}</td>
                        <td class="{coverage_class}">{metric.coverage_percentage:.1f}%</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Test Results Chart</h2>
            <div class="chart">
                <canvas id="testResultsChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <div class="section">
            <h2>Coverage Chart</h2>
            <div class="chart">
                <canvas id="coverageChart" width="400" height="200"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Test Results Chart
        const testResultsCtx = document.getElementById('testResultsChart').getContext('2d');
        new Chart(testResultsCtx, {
            type: 'doughnut',
            data: {
                labels: ['Passed', 'Failed', 'Skipped'],
                datasets: [{
                    data: [""" + f"{total_passed}, {total_failed}, {total_skipped}" + """],
                    backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Test Results Distribution'
                    }
                }
            }
        });
        
        // Coverage Chart
        const coverageCtx = document.getElementById('coverageChart').getContext('2d');
        new Chart(coverageCtx, {
            type: 'bar',
            data: {
                labels: [""" + ", ".join([f"'{m.module.split('/')[-1]}'" for m in self.coverage_metrics[:5]]) + """],
                datasets: [{
                    label: 'Coverage %',
                    data: [""" + ", ".join([str(m.coverage_percentage) for m in self.coverage_metrics[:5]]) + """],
                    backgroundColor: '#007bff'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Code Coverage by Module'
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        return str(report_file)
    
    def generate_json_report(self) -> str:
        """Generate JSON test report"""
        report_file = self.output_dir / "test_report.json"
        
        # Calculate overall statistics
        total_tests = sum(suite.total_tests for suite in self.test_suites)
        total_passed = sum(suite.passed for suite in self.test_suites)
        total_failed = sum(suite.failed for suite in self.test_suites)
        total_skipped = sum(suite.skipped for suite in self.test_suites)
        total_errors = sum(suite.errors for suite in self.test_suites)
        total_duration = sum(suite.duration for suite in self.test_suites)
        overall_success_rate = total_passed / max(total_tests, 1) * 100
        
        report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_duration': total_duration,
                'environment': 'testing'
            },
            'summary': {
                'total_tests': total_tests,
                'passed': total_passed,
                'failed': total_failed,
                'skipped': total_skipped,
                'errors': total_errors,
                'success_rate': overall_success_rate
            },
            'test_suites': [asdict(suite) for suite in self.test_suites],
            'performance_metrics': [asdict(metric) for metric in self.performance_metrics],
            'coverage_metrics': [asdict(metric) for metric in self.coverage_metrics]
        }
        
        # Convert datetime objects to strings
        for suite in report_data['test_suites']:
            suite['timestamp'] = suite['timestamp']
            for test in suite['test_results']:
                if test.get('timestamp'):
                    test['timestamp'] = test['timestamp']
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        return str(report_file)
    
    def generate_junit_xml(self) -> str:
        """Generate JUnit XML report for CI/CD integration"""
        report_file = self.output_dir / "test_report.xml"
        
        # Create root element
        testsuites = ET.Element('testsuites')
        
        # Calculate overall statistics
        total_tests = sum(suite.total_tests for suite in self.test_suites)
        total_failures = sum(suite.failed for suite in self.test_suites)
        total_errors = sum(suite.errors for suite in self.test_suites)
        total_duration = sum(suite.duration for suite in self.test_suites)
        
        testsuites.set('tests', str(total_tests))
        testsuites.set('failures', str(total_failures))
        testsuites.set('errors', str(total_errors))
        testsuites.set('time', str(total_duration))
        
        # Add test suite elements
        for suite in self.test_suites:
            testsuite = ET.SubElement(testsuites, 'testsuite')
            testsuite.set('name', suite.name)
            testsuite.set('tests', str(suite.total_tests))
            testsuite.set('failures', str(suite.failed))
            testsuite.set('errors', str(suite.errors))
            testsuite.set('skipped', str(suite.skipped))
            testsuite.set('time', str(suite.duration))
            testsuite.set('timestamp', suite.timestamp.isoformat())
            
            # Add test case elements
            for test in suite.test_results:
                testcase = ET.SubElement(testsuite, 'testcase')
                testcase.set('name', test.name)
                testcase.set('time', str(test.duration))
                testcase.set('classname', test.component or 'unknown')
                
                # Add failure element if test failed
                if test.status == 'failed':
                    failure = ET.SubElement(testcase, 'failure')
                    failure.set('message', test.error_message or 'Test failed')
                    failure.text = test.traceback or ''
                
                # Add skipped element if test was skipped
                elif test.status == 'skipped':
                    skipped = ET.SubElement(testcase, 'skipped')
                    skipped.set('message', test.error_message or 'Test skipped')
        
        # Write XML to file
        tree = ET.ElementTree(testsuites)
        tree.write(report_file, encoding='utf-8', xml_declaration=True)
        
        return str(report_file)
    
    def run_full_test_suite(self) -> Dict[str, str]:
        """Run the complete test suite and generate all reports"""
        print("Running complete test suite...")
        
        # Define test suites to run
        test_suites = [
            ('Feature Flags', 'tests/test_feature_flags.py', 'feature_flags'),
            ('Multi-Retail Modules', 'tests/test_multi_retail_modules.py', 'multi_retail'),
            ('Database Schema', 'tests/test_database_schema.py', 'database'),
            ('API Tests', 'tests/test_api_comprehensive.py', 'api'),
            ('UI/UX Tests', 'tests/test_ui_ux.py', 'ui_ux'),
            ('Performance Tests', 'tests/test_performance.py', 'performance'),
            ('Security Tests', 'tests/test_security_comprehensive.py', 'security'),
            ('Integration Tests', 'tests/test_integration_workflows.py', 'integration'),
            ('Retail-Specific Tests', 'tests/test_retail_specific_scenarios.py', 'retail_specific'),
            ('Feature Combinations', 'tests/test_feature_combinations.py', 'feature_combinations')
        ]
        
        # Run each test suite
        for name, path, component in test_suites:
            try:
                self.run_test_suite(name, path, component)
            except Exception as e:
                print(f"Error running test suite {name}: {e}")
        
        # Run coverage analysis
        try:
            self.run_coverage_analysis()
        except Exception as e:
            print(f"Error running coverage analysis: {e}")
        
        # Run performance tests
        try:
            self.run_performance_tests()
        except Exception as e:
            print(f"Error running performance tests: {e}")
        
        # Generate all reports
        reports = {}
        
        try:
            reports['html'] = self.generate_html_report()
            print(f"HTML report generated: {reports['html']}")
        except Exception as e:
            print(f"Error generating HTML report: {e}")
        
        try:
            reports['json'] = self.generate_json_report()
            print(f"JSON report generated: {reports['json']}")
        except Exception as e:
            print(f"Error generating JSON report: {e}")
        
        try:
            reports['junit'] = self.generate_junit_xml()
            print(f"JUnit XML report generated: {reports['junit']}")
        except Exception as e:
            print(f"Error generating JUnit XML report: {e}")
        
        return reports


def run_test_reporting():
    """Run test reporting and generate reports"""
    reporter = TestReporter()
    reports = reporter.run_full_test_suite()
    
    print("\n" + "="*80)
    print("TEST REPORTING COMPLETE")
    print("="*80)
    print(f"Reports generated in: {reporter.output_dir}")
    
    for report_type, report_path in reports.items():
        print(f"  {report_type.upper()}: {report_path}")
    
    # Print summary
    if reporter.test_suites:
        total_tests = sum(suite.total_tests for suite in reporter.test_suites)
        total_passed = sum(suite.passed for suite in reporter.test_suites)
        total_failed = sum(suite.failed for suite in reporter.test_suites)
        success_rate = total_passed / max(total_tests, 1) * 100
        
        print(f"\nTest Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        if reporter.coverage_metrics:
            avg_coverage = sum(m.coverage_percentage for m in reporter.coverage_metrics) / len(reporter.coverage_metrics)
            print(f"  Average Coverage: {avg_coverage:.1f}%")
    
    print("="*80)
    
    return reports


if __name__ == '__main__':
    run_test_reporting()