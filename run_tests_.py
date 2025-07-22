# run_tests.py
import unittest
import sys

# Import test modules
from test_gesture_signature_extractor import TestGestureSignatureExtractor
from test_gesture_recognition_engine import TestGestureRecognitionEngine
from test_gesture_signature_config_manager import TestGestureSignatureConfigManager
from test_gesture_serialization import TestGestureSerialization

def run_tests():
    """Run all gesture signature system tests"""
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestGestureSignatureExtractor))
    test_suite.addTest(unittest.makeSuite(TestGestureRecognitionEngine))
    test_suite.addTest(unittest.makeSuite(TestGestureSignatureConfigManager))
    test_suite.addTest(unittest.makeSuite(TestGestureSerialization))
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())