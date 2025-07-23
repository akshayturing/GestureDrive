# test_gesture_serialization.py
import unittest
import os
import json
import numpy as np
from gesture_signature_config_manager import GestureSignatureConfigManager
from test_gesture_signatures_setup import TestSetup

class TestGestureSerialization(unittest.TestCase):
    """Test case for gesture serialization and deserialization"""
    
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
        
        # Create mock serialized gesture
        cls.serialized_gesture = TestSetup.create_mock_serialized_gesture("Circle Gesture")
        cls.serialized_path = os.path.join(TestSetup.models_dir, "serialized_circle.json")
        
        with open(cls.serialized_path, 'w') as f:
            json.dump(cls.serialized_gesture, f, indent=2)
        
        # Create a test collection
        cls.gesture2 = TestSetup.create_mock_serialized_gesture("Swipe Right")
        cls.collection = {
            "schemaVersion": "1.0",
            "metadata": {
                "collectionName": "Test Collection",
                "created": "2025-07-22T13:00:00Z",
                "author": "Test User",
                "description": "A collection of test gestures",
                "gestures": [
                    {
                        "name": "Circle Gesture",
                        "description": "A circular gesture",
                        "created": "2025-07-22T12:00:00Z"
                    },
                    {
                        "name": "Swipe Right",
                        "description": "A swipe right gesture",
                        "created": "2025-07-22T12:30:00Z"
                    }
                ]
            },
            "gestures": [
                cls.serialized_gesture,
                cls.gesture2
            ]
        }
        
        cls.collection_path = os.path.join(TestSetup.models_dir, "test_collection.json")
        
        with open(cls.collection_path, 'w') as f:
            json.dump(cls.collection, f, indent=2)
    
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
        
        # Extract a signature for testing
        self.signature = self.config_manager.extract_signature_from_session("test_session")
        self.model = self.config_manager.create_gesture_model(self.signature)
    
    def test_serialize_gesture_signature(self):
        """Test serializing a gesture signature"""
        # Serialize the signature
        serialized = self.config_manager.serialize_gesture_signature(self.signature, self.model)
        
        # Check serialized structure
        self.assertIsNotNone(serialized)
        self.assertEqual(serialized["schemaVersion"], "1.0")
        self.assertEqual(serialized["metadata"]["gestureName"], "Circle Gesture")
        
        # Check that signature data was properly serialized
        self.assertIn("signature", serialized)
        self.assertIn("trajectoryFeatures", serialized["signature"])
        self.assertIn("velocityFeatures", serialized["signature"])
        
        # Check recognition parameters
        self.assertIn("recognitionParams", serialized)
        self.assertIn("similarityThreshold", serialized["recognitionParams"])
        
        # Check action mapping
        self.assertIn("actionMapping", serialized)
        self.assertIn("defaultAction", serialized["actionMapping"])
    
    def test_deserialize_gesture_signature(self):
        """Test deserializing a gesture signature"""
        # Deserialize from the test file
        signature, model = self.config_manager.deserialize_gesture_signature(self.serialized_gesture)
        
        # Check deserialized signature
        self.assertIsNotNone(signature)
        self.assertEqual(signature["gesture_name"], "Circle Gesture")
        self.assertIn("feature_vectors", signature)
        
        # Check deserialized model
        self.assertIsNotNone(model)
        self.assertEqual(model["gesture_name"], "Circle Gesture")
        self.assertIn("recognition_params", model)
    
    def test_save_load_signature_json(self):
        """Test saving and loading a gesture signature JSON"""
        # Save the signature
        filepath = self.config_manager.save_signature_json(self.signature, self.model)
        
        # Check that file was created
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        
        # Load the signature
        loaded_sig, loaded_model = self.config_manager.load_signature_json(filepath)
        
        # Check loaded data
        self.assertIsNotNone(loaded_sig)
        self.assertEqual(loaded_sig["gesture_name"], "Circle Gesture")
        self.assertIsNotNone(loaded_model)
        self.assertEqual(loaded_model["gesture_name"], "Circle Gesture")
    
    def test_save_gesture_collection(self):
        """Test saving a gesture collection"""
        # Save a collection with two gestures
        collection_path = self.config_manager.save_gesture_collection(
            ["Circle Gesture", "Swipe Right"],
            "Test Collection",
            "A test collection of gestures"
        )
        
        # Check that file was created
        self.assertIsNotNone(collection_path)
        self.assertTrue(os.path.exists(collection_path))
        
        # Check file content
        with open(collection_path, 'r') as f:
            collection = json.load(f)
        
        # Verify collection structure
        self.assertEqual(collection["metadata"]["collectionName"], "Test Collection")
        self.assertEqual(len(collection["gestures"]), 1)  # May only have Circle Gesture
    
    def test_load_gesture_collection(self):
        """Test loading a gesture collection"""
        # Load the test collection
        result = self.config_manager.load_gesture_collection(self.collection_path)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["imported_count"], 2)
        self.assertEqual(len(result["imported_gestures"]), 2)
        
        # Check that gestures were added to the config manager
        self.assertIn("Circle Gesture", self.config_manager.configs)
        self.assertIn("Swipe Right", self.config_manager.configs)

if __name__ == '__main__':
    unittest.main()