#!/usr/bin/env python3
"""
Test runner for semantic analyzer tests.
Runs both unit tests and integration tests for the semantic analyzer.
"""

import unittest
import sys
import os

def run_all_tests():
    """Run all semantic analyzer tests"""
    print("Running Semantic Analyzer Test Suite")
    print("=" * 50)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add unit tests
    try:
        unit_tests = loader.loadTestsFromName('test_semantic_analyzer')
        suite.addTests(unit_tests)
        print("(+) Loaded unit tests")
    except Exception as e:
        print(f"(-) Failed to load unit tests: {e}")
        return False
    
    # Add integration tests
    try:
        integration_tests = loader.loadTestsFromName('test_integration_semantica')
        suite.addTests(integration_tests)
        print("(+) Loaded integration tests")
    except Exception as e:
        print(f"(-) Failed to load integration tests: {e}")
        return False
    
    print(f"Total tests loaded: {suite.countTestCases()}")
    print("-" * 50)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_unit_tests_only():
    """Run only unit tests"""
    print("Running Unit Tests Only")
    print("=" * 30)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_semantic_analyzer')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

def run_integration_tests_only():
    """Run only integration tests"""
    print("Running Integration Tests Only")
    print("=" * 35)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_integration_semantica')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    # Check if TestSemantica.txt exists
    if not os.path.exists('TestSemantica.txt'):
        print("Warning: TestSemantica.txt not found. Integration tests may fail.")
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'unit':
            success = run_unit_tests_only()
        elif sys.argv[1] == 'integration':
            success = run_integration_tests_only()
        elif sys.argv[1] == 'all':
            success = run_all_tests()
        else:
            print("Usage: python run_semantic_tests.py [unit|integration|all]")
            print("  unit        - Run only unit tests")
            print("  integration - Run only integration tests") 
            print("  all         - Run all tests (default)")
            sys.exit(1)
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)