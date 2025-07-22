import unittest
import numpy as np
import cv2
import time
import threading
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Camera class
from core.camera import Camera

@unittest.skipIf(not cv2.VideoCapture(0).isOpened(), "No camera available for testing")
class TestCameraIntegration(unittest.TestCase):
    """Integration tests for Camera module with actual hardware"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.camera = Camera(camera_id=0, width=320, height=240)  # Lower resolution for speed
    
    def tearDown(self):
        """Tear down test fixtures"""
        if hasattr(self, 'camera') and self.camera.is_running:
            self.camera.stop()
    
    def test_camera_start_stop(self):
        """Test camera startup and shutdown"""
        # Start camera
        self.camera.start()
        self.assertTrue(self.camera.is_running)
        self.assertIsNotNone(self.camera.thread)
        
        # Let it run briefly
        time.sleep(1.0)
        
        # Stop camera
        self.camera.stop()
        self.assertFalse(self.camera.is_running)
        self.assertIsNone(self.camera.thread)
    
    def test_get_frame(self):
        """Test frame retrieval"""
        # Start camera
        self.camera.start()
        time.sleep(1.0)  # Give it time to initialize
        
        # Get a frame
        frame = self.camera.get_frame(processed=False)
        
        # Verify frame properties
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[0], 240)  # Height
        self.assertEqual(frame.shape[1], 320)  # Width
        self.assertEqual(frame.shape[2], 3)    # Channels
        
        # Check that frame is not all zeros (actual camera data)
        self.assertGreater(np.mean(frame), 1.0)
    
    @unittest.skipIf(True, "Long running test - run manually")
    def test_landmark_detection_with_real_hand(self):
        """Test hand landmark detection with a real hand (interactive)"""
        # This test requires a human to place their hand in front of the camera
        self.camera.start()
        
        print("\nPlease place your hand in front of the camera...")
        print("Test will run for 5 seconds")
        
        start_time = time.time()
        detection_results = []
        
        # Run for 5 seconds
        while time.time() - start_time < 5.0:
            # Get processed frame
            frame = self.camera.get_frame(processed=True)
            
            # Display the frame
            cv2.imshow('Hand Detection Test', frame)
            cv2.waitKey(1)
            
            # Record if landmarks were detected
            detection_results.append(self.camera.hand_landmarks_data is not None)
            
            time.sleep(0.1)
        
        cv2.destroyAllWindows()
        
        # Check if landmarks were detected at least once
        self.assertTrue(any(detection_results), 
                       "No hand landmarks detected. Make sure a hand was visible.")

if __name__ == '__main__':
    unittest.main()