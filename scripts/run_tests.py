# run_tests.py

import unittest
import sys

def run_all_tests():
    """Run all unit tests."""
    # Get all test modules
    test_modules = [
        'test_directory_state_manager',
        'test_gesture_detection',
        'test_persistent_navigator'
    ]
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests from each module
    for test_module in test_modules:
        try:
            # Import the module
            module = __import__(test_module)
            
            # Add tests from the module
            module_tests = loader.loadTestsFromModule(module)
            suite.addTest(module_tests)
            
            print(f"Added tests from {test_module}")
            
        except ImportError as e:
            print(f"Could not import test module {test_module}: {e}")
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test success
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_all_tests())