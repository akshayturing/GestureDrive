# test_gesture_signature_extractor.py
import unittest
import os
import json
import numpy as np
from gesture_signature_extractor import GestureSignatureExtractor
from test_gesture_signatures_setup import TestSetup

class TestGestureSignatureExtractor(unittest.TestCase):
    """Test case for the GestureSignatureExtractor class"""
    
    @classmethod
    def setUpClass(cls):
        # Create temporary directories for testing
        cls.temp_dir = TestSetup.create_temp_dirs()
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directories
        TestSetup.cleanup_temp_dirs()
    
    def setUp(self):
        # Initialize the extractor
        self.extractor = GestureSignatureExtractor(
            signature_cache_dir=TestSetup.cache_dir
        )
        
        # Create a mock training session
        self.training_data_path = TestSetup.create_mock_training_session(
            session_id="test_session",
            gesture_name="Circle Gesture",
            example_count=3,
            frames_per_example=10
        )
    
    def test_init(self):
        """Test initialization of GestureSignatureExtractor"""
        self.assertIsNotNone(self.extractor)
        self.assertEqual(self.extractor.signature_cache_dir, TestSetup.cache_dir)
        self.assertEqual(self.extractor.normalization_method, "minmax")
        self.assertEqual(len(self.extractor.key_landmarks), 6)  # Default key landmarks
        
        # Test with custom parameters
        custom_extractor = GestureSignatureExtractor(
            normalization_method="zscore",
            resample_length=20,
            key_landmarks=[0, 4, 8],
            feature_weights={
                "trajectory": 0.6,
                "velocity": 0.3,
                "acceleration": 0.05,
                "hand_shape": 0.05
            },
            signature_cache_dir=TestSetup.cache_dir
        )
        
        self.assertEqual(custom_extractor.normalization_method, "zscore")
        self.assertEqual(custom_extractor.resample_length, 20)
        self.assertEqual(len(custom_extractor.key_landmarks), 3)
        self.assertEqual(custom_extractor.feature_weights["trajectory"], 0.6)
    
    def test_normalize_trajectory(self):
        """Test trajectory normalization"""
        # Create test trajectory
        trajectory = np.array([
            [0.1, 0.2, 0.3],
            [0.2, 0.4, 0.6],
            [0.3, 0.6, 0.9]
        ])
        
        # Test minmax normalization
        self.extractor.normalization_method = "minmax"
        normalized = self.extractor._normalize_trajectory(trajectory)
        
        # Check that values are normalized to 0-1 range
        self.assertAlmostEqual(np.min(normalized[:, 0]), 0.0, places=5)
        self.assertAlmostEqual(np.max(normalized[:, 0]), 1.0, places=5)
        self.assertAlmostEqual(np.min(normalized[:, 1]), 0.0, places=5)
        self.assertAlmostEqual(np.max(normalized[:, 1]), 1.0, places=5)
        
        # Test zscore normalization
        self.extractor.normalization_method = "zscore"
        normalized = self.extractor._normalize_trajectory(trajectory)
        
        # Check that mean is approximately 0 and std is approximately 1
        self.assertAlmostEqual(np.mean(normalized[:, 0]), 0.0, places=5)
        self.assertAlmostEqual(np.std(normalized[:, 0]), 1.0, places=5)
    
    def test_resample_trajectory(self):
        """Test trajectory resampling"""
        # Create test trajectory with 10 points
        trajectory = np.zeros((10, 3))
        for i in range(10):
            trajectory[i] = [i/9, i/9, 0]
        
        # Test resampling to 5 points
        self.extractor.resample_length = 5
        resampled = self.extractor._resample_trajectory(trajectory)
        
        # Check dimensions
        self.assertEqual(resampled.shape, (5, 3))
        
        # Check that it maintains the pattern (linear interpolation)
        np.testing.assert_allclose(resampled[0], [0, 0, 0], atol=1e-5)
        np.testing.assert_allclose(resampled[-1], [1, 1, 0], atol=1e-5)
    
    def test_extract_signature_from_landmarks(self):
        """Test extracting signature from landmarks"""
        # Create mock landmarks
        landmarks_sequence, timestamps = TestSetup.create_mock_landmarks("circle", 20)
        
        # Extract signature
        signature = self.extractor._extract_signature_from_landmarks(
            landmarks_sequence, timestamps, "test_example"
        )
        
        # Check signature structure
        self.assertEqual(signature["example_id"], "test_example")
        self.assertEqual(signature["frame_count"], 20)
        
        # Check that trajectories were extracted
        self.assertIn("trajectories", signature)
        self.assertIn("landmark_0", signature["trajectories"])
        
        # Check feature vectors
        self.assertIn("feature_vectors", signature)
        self.assertIn("trajectory_features", signature["feature_vectors"])
        self.assertIn("velocity_features", signature["feature_vectors"])
    
    def test_extract_signature_from_session(self):
        """Test extracting signature from a training session"""
        # Extract signature
        signature = self.extractor.extract_signature_from_session(self.training_data_path)
        
        # Check signature structure
        self.assertIsNotNone(signature)
        self.assertEqual(signature["gesture_name"], "Circle Gesture")
        
        # Check example signatures
        self.assertIn("example_signatures", signature)
        self.assertEqual(len(signature["example_signatures"]), 3)
        
        # Check combined feature vectors
        self.assertIn("feature_vectors", signature)
        
        # Check that pattern clusters were created
        self.assertIn("pattern_clusters", signature)
    
    def test_compare_signatures(self):
        """Test comparing two signatures"""
        # Create two similar signatures
        signature1 = TestSetup.create_mock_signature("Circle Gesture")
        signature2 = TestSetup.create_mock_signature("Circle Gesture")
        
        # Compare signatures
        result = self.extractor.compare_signatures(signature1, signature2)
        
        # Check result structure
        self.assertIn("overall_similarity", result)
        self.assertIn("feature_similarities", result)
        self.assertIn("is_match", result)
        self.assertIn("confidence", result)
        
        # Signatures should be very similar
        self.assertGreater(result["overall_similarity"], 0.9)
        self.assertTrue(result["is_match"])
        
        # Now create a different signature
        signature3 = TestSetup.create_mock_signature("Swipe Gesture")
        # Modify the features to be different
        for landmark in signature3["feature_vectors"]["trajectory_features"]:
            if isinstance(signature3["feature_vectors"]["trajectory_features"][landmark], dict):
                for key in signature3["feature_vectors"]["trajectory_features"][landmark]:
                    # Make the feature values significantly different
                    signature3["feature_vectors"]["trajectory_features"][landmark][key] *= 3
        
        # Compare different signatures
        result = self.extractor.compare_signatures(signature1, signature3)
        
        # Signatures should be different
        self.assertLess(result["overall_similarity"], signature1["similarity_threshold"])
        self.assertFalse(result["is_match"])
    
    def test_build_gesture_model(self):
        """Test building a gesture model from a signature"""
        # Create mock signature
        signature = TestSetup.create_mock_signature("Circle Gesture")
        
        # Build model
        model = self.extractor.build_gesture_model(signature)
        
        # Check model structure
        self.assertEqual(model["gesture_name"], "Circle Gesture")
        self.assertIn("feature_vectors", model)
        self.assertIn("pattern_clusters", model)
        self.assertIn("recognition_params", model)
        
        # Check that the model was stored in memory
        self.assertIn("Circle Gesture", self.extractor.gesture_models)
    
    def test_save_and_load_gesture_model(self):
        """Test saving and loading a gesture model"""
        # Create mock model
        model = TestSetup.create_mock_model("Circle Gesture")
        
        # Save model
        model_path = self.extractor.save_gesture_model(
            model, output_dir=TestSetup.models_dir
        )
        
        # Check that file was created
        self.assertTrue(os.path.exists(model_path))
        
        # Load model
        loaded_model = self.extractor.load_gesture_model(model_path)
        
        # Check that model was loaded correctly
        self.assertEqual(loaded_model["gesture_name"], "Circle Gesture")
        self.assertIn("feature_vectors", loaded_model)
        
        # Check that model was stored in memory
        self.assertIn("Circle Gesture", self.extractor.gesture_models)

if __name__ == '__main__':
    unittest.main()
