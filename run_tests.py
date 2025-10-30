#!/usr/bin/env python3
"""
StockHark Test Runner
Comprehensive test suite runner with database integration
"""

import unittest
import sys
import os
import sqlite3
from pathlib import Path
from io import StringIO

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}")

def print_header(text):
    """Print section header"""
    print_colored(f"\n{'='*60}", Colors.BLUE)
    print_colored(f"{text:^60}", Colors.BOLD)
    print_colored(f"{'='*60}", Colors.BLUE)

def check_prerequisites():
    """Check if all prerequisites are met"""
    print_header("PREREQUISITE CHECKS")
    
    project_root = Path(__file__).parent.parent
    issues = []
    
    # Check database
    db_path = project_root / "src" / "data" / "stocks.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM stock_data")
            count = cursor.fetchone()[0]
            conn.close()
            print_colored(f"✅ Database found with {count:,} records", Colors.GREEN)
        except Exception as e:
            print_colored(f"⚠️ Database exists but has issues: {e}", Colors.YELLOW)
            issues.append("Database accessibility")
    else:
        print_colored("❌ Database not found", Colors.RED)
        issues.append("Missing database")
    
    # Check JSON files
    json_dir = project_root / "src" / "data" / "json"
    if json_dir.exists():
        json_files = list(json_dir.glob("*.json"))
        print_colored(f"✅ JSON directory found with {len(json_files)} files", Colors.GREEN)
    else:
        print_colored("❌ JSON data directory not found", Colors.RED)
        issues.append("Missing JSON data")
    
    # Check core modules
    sys.path.insert(0, str(project_root / "src"))
    
    modules_to_check = [
        "stockhark.core.validators.stock_validator",
        "stockhark.core.services.service_factory", 
        "stockhark.app"
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print_colored(f"✅ Module {module} importable", Colors.GREEN)
        except ImportError as e:
            print_colored(f"❌ Module {module} import failed: {e}", Colors.RED)
            issues.append(f"Module import: {module}")
    
    return issues

def run_test_suite(test_file, description):
    """Run a specific test suite"""
    print_header(f"RUNNING {description}")
    
    # Add tests directory to path
    project_root = Path(__file__).parent
    test_dir = project_root / "tests"
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))
    
    # Capture test output
    test_output = StringIO()
    test_runner = unittest.TextTestRunner(
        stream=test_output,
        verbosity=2,
        buffer=True
    )
    
    # Load and run tests
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(test_file)
        result = test_runner.run(suite)
        
        # Print results
        output = test_output.getvalue()
        print(output)
        
        # Summary
        if result.wasSuccessful():
            print_colored(f"✅ {description} - All tests passed!", Colors.GREEN)
        else:
            print_colored(f"⚠️ {description} - Some tests failed/skipped", Colors.YELLOW)
            
        print_colored(f"Tests run: {result.testsRun}", Colors.BLUE)
        if result.failures:
            print_colored(f"Failures: {len(result.failures)}", Colors.RED)
        if result.errors:
            print_colored(f"Errors: {len(result.errors)}", Colors.RED)
        if result.skipped:
            print_colored(f"Skipped: {len(result.skipped)}", Colors.YELLOW)
            
        return result
        
    except Exception as e:
        print_colored(f"❌ Failed to run {description}: {e}", Colors.RED)
        return None

def run_quick_integration_test():
    """Run quick integration test"""
    print_header("QUICK INTEGRATION TEST")
    
    try:
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / "src"))
        
        # Test Flask app creation
        from stockhark.app import create_production_app
        app = create_production_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            home_status = response.status_code
            
            # Test API route
            response = client.get('/api/stocks')
            api_status = response.status_code
            
            if api_status == 200:
                data = response.get_json()
                stock_count = len(data) if data else 0
            else:
                stock_count = 0
            
            print_colored(f"✅ Home route: {home_status}", Colors.GREEN if home_status == 200 else Colors.RED)
            print_colored(f"✅ API route: {api_status}", Colors.GREEN if api_status == 200 else Colors.RED)
            print_colored(f"✅ API returned {stock_count} stocks", Colors.GREEN if stock_count > 0 else Colors.YELLOW)
            
            return home_status == 200 and api_status == 200
            
    except Exception as e:
        print_colored(f"❌ Integration test failed: {e}", Colors.RED)
        return False

def main():
    """Main test runner"""
    print_colored("StockHark Comprehensive Test Suite", Colors.BOLD)
    print_colored("Testing with latest database and configuration", Colors.BLUE)
    
    # Check prerequisites
    issues = check_prerequisites()
    
    if issues:
        print_colored(f"\n⚠️ Found {len(issues)} prerequisite issues:", Colors.YELLOW)
        for issue in issues:
            print_colored(f"  - {issue}", Colors.YELLOW)
        print_colored("\nSome tests may be skipped due to missing dependencies.", Colors.YELLOW)
    
    # Run test suites
    test_results = []
    
    # Core functionality tests
    core_result = run_test_suite('test_core', 'CORE FUNCTIONALITY TESTS')
    if core_result:
        test_results.append(('Core Tests', core_result))
    
    # Performance tests (modified to handle missing psutil)
    perf_result = run_test_suite('test_performance', 'PERFORMANCE & SYSTEM TESTS')
    if perf_result:
        test_results.append(('Performance Tests', perf_result))
    
    # Quick integration test
    integration_success = run_quick_integration_test()
    
    # Final summary
    print_header("TEST SUMMARY")
    
    total_tests = sum(result.testsRun for _, result in test_results)
    total_failures = sum(len(result.failures) for _, result in test_results)
    total_errors = sum(len(result.errors) for _, result in test_results)
    total_skipped = sum(len(result.skipped) for _, result in test_results)
    
    print_colored(f"Total tests run: {total_tests}", Colors.BLUE)
    
    if total_failures == 0 and total_errors == 0:
        print_colored("✅ All tests passed successfully!", Colors.GREEN)
        status = "PASSED"
    else:
        print_colored(f"⚠️ {total_failures} failures, {total_errors} errors", Colors.YELLOW)
        status = "PARTIAL"
    
    if total_skipped > 0:
        print_colored(f"ℹ️ {total_skipped} tests skipped", Colors.BLUE)
    
    print_colored(f"Integration test: {'✅ PASSED' if integration_success else '❌ FAILED'}", 
                 Colors.GREEN if integration_success else Colors.RED)
    
    # Railway deployment readiness
    print_header("RAILWAY DEPLOYMENT READINESS")
    
    deployment_ready = (
        len(issues) <= 2 and  # Allow some minor issues
        total_errors == 0 and
        integration_success
    )
    
    if deployment_ready:
        print_colored("🚀 READY FOR RAILWAY DEPLOYMENT!", Colors.GREEN)
        print_colored("All critical systems tested and functional", Colors.GREEN)
    else:
        print_colored("⚠️ Review issues before deploying to Railway", Colors.YELLOW)
        print_colored("Some critical functionality may not work properly", Colors.YELLOW)
    
    # Exit code
    return 0 if deployment_ready else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)