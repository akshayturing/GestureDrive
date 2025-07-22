# test_gesture_signature_config_manager.py
import unittest
import os
import json
import numpy as np
import shutil
from gesture_signature_config_manager import GestureSignatureConfigManager
from test_gesture_signatures_setup import TestSetup

class TestGestureSignatureConfigManager(unittest.TestCase):
    """Test case for the GestureSignatureConfigManager class"""
    
    @classmethod
    def setUpClass(cls):
        # Create temporary directories for testing
        cls.temp_dir = TestSetup.create_temp_dirs()
        
        # Create mock training session
        cls.training_data_path = TestSetup.create_mock_training_session(
            session_id="test_session",
            gesture_name="Circle Gesture",
            example_count=5,
            frames_per_example=10
        )
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directories
        TestSetup.cleanup_temp_dirs()
    
    def setUp(self):
        # Initialize the config manager
        self.config_manager = GestureSignatureConfigManager(
            config_dir=TestSetup.config_dir,
            model_dir=TestSetup.models_dir,
            training_dir=TestSetup.training_dir
        )
    
    def test_init(self):
        """Test initialization of GestureSignatureConfigManager"""
        self.assertIsNotNone(self.config_manager)
        self.assertEqual(self.config_manager.config_dir, TestSetup.config_dir)
        self.assertEqual(self.config_manager.model_dir, TestSetup.models_dir)
        self.assertEqual(self.config_manager.training_dir, TestSetup.training_dir)
        
        # Check that extractor and recognition engine were initialized
        self.assertIsNotNone(self.config_manager.extractor)
        self.assertIsNotNone(self.config_manager.recognition_engine)
    
    def test_extract_signature_from_session(self):
        """Test extracting signature from a training session"""
        # Extract signature
        signature = self.config_manager.extract_signature_from_session("test_session")
        
        # Check signature structure
        self.assertIsNotNone(signature)
        self.assertEqual(signature["gesture_name"], "Circle Gesture")
        self.assertIn("feature_vectors", signature)
        
        # Check that signature was cached
        self.assertIn("Circle Gesture", self.config_manager.signatures)
    
    def test_create_gesture_model(self):
        """Test creating a gesture model from a signature"""
        # Extract signature
        signature = self.config_manager.extract_signature_from_session("test_session")
        
        # Create model
        model = self.config_manager.create_gesture_model(signature)
        
        # Check model structure
        self.assertIsNotNone(model)
        self.assertEqual(model["gesture_name"], "Circle Gesture")
        self.assertIn("feature_vectors", model)
        
        # Check that model was saved to disk
        model_files = os.listdir(TestSetup.models_dir)
        self.assertGreaterEqual(len(model_files), 1)
    
    def test_create_gesture_config(self):
        """Test creating a gesture configuration from a model"""
        # Extract signature and create model
        signature = self.config_manager.extract_signature_from_session("test_session")
        model = self.config_manager.create_gesture_model(signature)
        
        # Create config
        config = self.config_manager.create_gesture_config(model)
        
        # Check config structure
        self.assertIsNotNone(config)
        self.assertEqual(config["gesture_name"], "Circle Gesture")
        self.assertEqual(config["type"], "custom")
        self.assertIn("recognition", config)
        self.assertIn("action", config)
        
        # Check that config was saved to disk
        config_files = os.listdir(TestSetup.config_dir)
        self.assertGreaterEqual(len(config_files), 1)
        
        # Check that config was stored in memory
        self.assertIn("Circle Gesture", self.config_manager.configs)
    
    def test_process_training_session(self):
        """Test processing a complete training session"""
        # Process the session
        result = self.config_manager.process_training_session("test_session")
        
        # Check result structure
        self.assertIsNotNone(result)
        self.assertTrue(result["success"])
        self.assertEqual(result["gesture_name"], "Circle Gesture")
        
        # Check that all steps were completed
        self.assertIn("signature_extraction", result["steps_completed"])
        self.assertIn("model_creation", result["steps_completed"])
        self.assertIn("config_creation", result["steps_completed"])
    
    def test_get_available_custom_gestures(self):
        """Test getting available custom gestures"""
        # Process a session to create a gesture
        self.config_manager.process_training_session("test_session")
        
        # Get available gestures
        gestures = self.config_manager.get_available_custom_gestures()
        
        # Check that our gesture is in the list
        self.assertGreaterEqual(len(gestures), 1)
        self.assertTrue(any(g["name"] == "Circle Gesture" for g in gestures))
    
    def test_delete_gesture(self):
        """Test deleting a custom gesture"""
        # Process a session to create a gesture
        self.config_manager.process_training_session("test_session")
        
        # Delete the gesture
        result = self.config_manager.delete_gesture("Circle Gesture")
        
        # Check result
        self.assertTrue(result)
        
        # Check that gesture was removed from memory
        self.assertNotIn("Circle Gesture", self.config_manager.configs)

if __name__ == '__main__':
    unittest.main()