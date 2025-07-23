# test_gesture_recognition_engine.py
import unittest
import os
import json
import numpy as np
import pickle
import cv2
from gesture_recognition_engine import GestureRecognitionEngine
from test_gesture_signatures_setup import TestSetup

class TestGestureRecognitionEngine(unittest.TestCase):
    """Test case for the GestureRecognitionEngine class"""
    
    @classmethod
    def setUpClass(cls):
        # Create temporary directories for testing
        cls.temp_dir = TestSetup.create_temp_dirs()
        
        # Create a test model
        cls.model = TestSetup.create_mock_model("Circle Gesture")
        cls.model_path = os.path.join(TestSetup.models_dir, "gesture_model_circle_gesture.json")
        
        with open(cls.model_path, 'w') as f:
            json.dump(cls.model, f, indent=2)
            
        # Create second test model for swipe
        cls.swipe_model = TestSetup.create_mock_model("Swipe Right")
        cls.swipe_model_path = os.path.join(TestSetup.models_dir, "gesture_model_swipe_right.json")
        
        with open(cls.swipe_model_path, 'w') as f:
            json.dump(cls.swipe_model, f, indent=2)
    
    @classmethod
    def tearDownClass(cls):
        # Clean up temporary directories
        TestSetup.cleanup_temp_dirs()
    
    def setUp(self):
        # Initialize the recognition engine
        self.engine = GestureRecognitionEngine(
            model_dir=TestSetup.models_dir,
            confidence_threshold=0.7,
            temporal_window=20,
            cooldown_frames=5
        )
    
    def test_init(self):
        """Test initialization of GestureRecognitionEngine"""
        self.assertIsNotNone(self.engine)
        self.assertEqual(self.engine.model_dir, TestSetup.models_dir)
        self.assertEqual(self.engine.confidence_threshold, 0.7)
        self.assertEqual(self.engine.temporal_window, 20)
        
        # Check that models were loaded
        self.assertIn("Circle Gesture", self.engine.gesture_models)
        self.assertIn("Swipe Right", self.engine.gesture_models)
    
    def test_add_remove_model(self):
        """Test adding and removing models"""
        # Create a new model
        model = TestSetup.create_mock_model("Test Gesture")
        
        # Add to engine
        result = self.engine.add_model(model)
        self.assertTrue(result)
        self.assertIn("Test Gesture", self.engine.gesture_models)
        
        # Remove from engine
        result = self.engine.remove_model("Test Gesture")
        self.assertTrue(result)
        self.assertNotIn("Test Gesture", self.engine.gesture_models)
        
        # Try to remove non-existent model
        result = self.engine.remove_model("Nonexistent Gesture")
        self.assertFalse(result)
    
    def test_process_landmarks_circle(self):
        """Test processing landmarks for circle gesture recognition"""
        # Create circle gesture landmarks
        landmarks_sequence, timestamps = TestSetup.create_mock_landmarks("circle", 20)
        
        # Process each frame
        for i in range(len(landmarks_sequence)):
            result = self.engine.process_landmarks(landmarks_sequence[i], timestamps[i])
            
            # Check result structure
            self.assertIn("timestamp", result)
            self.assertIn("history_frames", result)
            
            # Early frames shouldn't have enough history for recognition
            if i < 5:
                self.assertFalse(result.get("recognized", False))
            
            # Later frames should recognize the circle gesture
            if i >= 15:  # Allow some frames for recognition to stabilize
                if result.get("recognized", False):
                    self.assertEqual(result["gesture_name"], "Circle Gesture")
        
        # Check final state
        self.assertEqual(len(self.engine.landmark_history), self.engine.temporal_window)
    
    def test_process_landmarks_swipe(self):
        """Test processing landmarks for swipe gesture recognition"""
        # Create swipe gesture landmarks
        landmarks_sequence, timestamps = TestSetup.create_mock_landmarks("swipe_right", 20)
        
        # Process each frame
        for i in range(len(landmarks_sequence)):
            result = self.engine.process_landmarks(landmarks_sequence[i], timestamps[i])
            
            # Later frames should recognize the swipe gesture
            if i >= 15:  # Allow some frames for recognition to stabilize
                if result.get("recognized", False):
                    self.assertEqual(result["gesture_name"], "Swipe Right")
    
    def test_cooldown(self):
        """Test gesture recognition cooldown"""
        # Create gesture landmarks
        landmarks_sequence, timestamps = TestSetup.create_mock_landmarks("circle", 30)
        
        # Process until we get a recognition
        recognized_frame = -1
        for i in range(20):
            result = self.engine.process_landmarks(landmarks_sequence[i], timestamps[i])
            if result.get("recognized", False):
                recognized_frame = i
                break
        
        # Check that we got a recognition
        self.assertGreater(recognized_frame, 0)
        
        # The next few frames should be in cooldown
        for i in range(recognized_frame + 1, recognized_frame + self.engine.cooldown_frames):
            result = self.engine.process_landmarks(landmarks_sequence[i], timestamps[i])
            self.assertFalse(result.get("recognized", False))
            if "message" in result:
                self.assertIn("cooldown", result["message"].lower())
    
    def test_process_frame(self):
        """Test processing video frames"""
        # Create a simple test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create mock hand landmarks
        landmarks = {
            "landmarks": [[0.5, 0.5, 0.0], [0.6, 0.6, 0.0]]
        }
        
        # Process frame
        processed_frame, result = self.engine.process_frame(frame, landmarks, draw_result=True)
        
        # Check that result was returned
        self.assertIsNotNone(result)
        
        # Check that frame was modified (text was added)
        self.assertFalse(np.array_equal(frame, processed_frame))
    
    def test_clear_history(self):
        """Test clearing the landmark history"""
        # Add some landmarks to history
        landmarks, timestamps = TestSetup.create_mock_landmarks("circle", 10)
        for i in range(len(landmarks)):
            self.engine.process_landmarks(landmarks[i], timestamps[i])
        
        # Check that history has data
        self.assertGreater(len(self.engine.landmark_history), 0)
        
        # Clear history
        self.engine.clear_history()
        
        # Check that history is empty
        self.assertEqual(len(self.engine.landmark_history), 0)
        self.assertEqual(len(self.engine.timestamp_history), 0)
        self.assertIsNone(self.engine.current_gesture)
        self.assertEqual(self.engine.current_confidence, 0.0)

if __name__ == '__main__':
    unittest.main()