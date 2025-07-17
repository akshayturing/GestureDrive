# test_gesture_detection.py

import unittest
import time
import math
import numpy as np
from unittest.mock import Mock, patch

class TestGestureDetection(unittest.TestCase):
    """Test cases for gesture detection logic."""
    
    def setUp(self):
        """Set up a mock PersistentGestureNavigator for testing."""
        # Import here to allow for patching
        from persistent_gesture_navigator import PersistentGestureNavigator
        
        # Create a mock camera
        self.mock_camera = Mock()
        self.mock_camera.hand_landmarks_data = None
        
        # Patch the DirectoryStateManager to avoid file system operations
        with patch('persistent_gesture_navigator.DirectoryStateManager') as MockStateManager:
            # Create an instance of the mock state manager
            self.mock_state_manager = MockStateManager.return_value
            
            # Configure mock state manager methods
            self.mock_state_manager.get_current_directory.return_value = Mock(
                exists=lambda: True,
                is_dir=lambda: True,
                iterdir=lambda: [],
                name="test_dir",
                parent=Mock(name="parent_dir")
            )
            self.mock_state_manager.get_selection_index.return_value = 0
            
            # Create the navigator with our mocks
            self.navigator = PersistentGestureNavigator(self.mock_camera)
            
            # Replace the real state manager with our mock
            self.navigator.state_manager = self.mock_state_manager
            
    def generate_landmark(self, x, y, z=0):
        """Generate a mock landmark with the given coordinates."""
        landmark = Mock()
        landmark.x = x
        landmark.y = y
        landmark.z = z
        return landmark
    
    def generate_gesture_path(self, points, start_time=None):
        """
        Generate a gesture path from a list of points.
        
        Args:
            points: List of (x, y, z) tuples
            start_time: Starting timestamp (defaults to current time)
        
        Returns:
            List of ((x, y, z), timestamp) tuples
        """
        if start_time is None:
            start_time = time.time()
            
        path = []
        for i, point in enumerate(points):
            # Each point is 0.05 seconds after the previous
            timestamp = start_time + (i * 0.05)
            path.append((point, timestamp))
            
        return path
    
    def test_is_hand_idle(self):
        """Test idle hand detection."""
        # Idle hand (minimal movement)
        idle_path = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.501, 0.499, 0), (0.502, 0.501, 0),
            (0.499, 0.502, 0), (0.5, 0.498, 0)
        ])
        
        result = self.navigator._is_hand_idle(idle_path)
        self.assertTrue(result, "Should detect idle hand with minimal movement")
        
        # Active hand (significant movement)
        active_path = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.55, 0.48, 0), (0.6, 0.45, 0),
            (0.65, 0.43, 0), (0.7, 0.4, 0)
        ])
        
        result = self.navigator._is_hand_idle(active_path)
        self.assertFalse(result, "Should not detect idle hand with significant movement")
    
    def test_has_deliberate_movement(self):
        """Test detection of deliberate movement."""
        # Consistent direction (right swipe)
        right_swipe = self.generate_gesture_path([
            (0.3, 0.5, 0), (0.35, 0.51, 0), (0.4, 0.49, 0),
            (0.45, 0.5, 0), (0.5, 0.51, 0), (0.55, 0.5, 0)
        ])
        
        result = self.navigator._has_deliberate_movement(right_swipe)
        self.assertTrue(result, "Should detect deliberate right swipe")
        
        # Random movement (no consistent direction)
        random_movement = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.55, 0.48, 0), (0.52, 0.55, 0),
            (0.48, 0.51, 0), (0.51, 0.47, 0)
        ])
        
        result = self.navigator._has_deliberate_movement(random_movement)
        self.assertFalse(result, "Should not detect deliberate movement in random pattern")
        
        # Slow movement (below velocity threshold)
        slow_movement = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.505, 0.5, 0), (0.51, 0.5, 0),
            (0.515, 0.5, 0), (0.52, 0.5, 0)
        ], time.time() - 1)  # Older timestamps to create slow movement
        
        result = self.navigator._has_deliberate_movement(slow_movement)
        self.assertFalse(result, "Should not detect deliberate movement when too slow")
    
    def test_recognize_gesture(self):
        """Test gesture recognition."""
        # Set up the navigator with some paths
        
        # Right swipe
        right_swipe = self.generate_gesture_path([
            (0.3, 0.5, 0), (0.4, 0.5, 0), (0.5, 0.5, 0), 
            (0.6, 0.5, 0), (0.7, 0.5, 0)
        ])
        self.navigator.gesture_path = right_swipe
        
        # Use the internal method to extract active movement
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=right_swipe):
            result = self.navigator._recognize_gesture()
            self.assertEqual(result, "swipe_right", "Should recognize right swipe")
        
        # Left swipe
        left_swipe = self.generate_gesture_path([
            (0.7, 0.5, 0), (0.6, 0.5, 0), (0.5, 0.5, 0), 
            (0.4, 0.5, 0), (0.3, 0.5, 0)
        ])
        self.navigator.gesture_path = left_swipe
        
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=left_swipe):
            result = self.navigator._recognize_gesture()
            self.assertEqual(result, "swipe_left", "Should recognize left swipe")
        
        # Down swipe
        down_swipe = self.generate_gesture_path([
            (0.5, 0.3, 0), (0.5, 0.4, 0), (0.5, 0.5, 0), 
            (0.5, 0.6, 0), (0.5, 0.7, 0)
        ])
        self.navigator.gesture_path = down_swipe
        
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=down_swipe):
            result = self.navigator._recognize_gesture()
            self.assertEqual(result, "swipe_down", "Should recognize down swipe")
        
        # Up swipe
        up_swipe = self.generate_gesture_path([
            (0.5, 0.7, 0), (0.5, 0.6, 0), (0.5, 0.5, 0), 
            (0.5, 0.4, 0), (0.5, 0.3, 0)
        ])
        self.navigator.gesture_path = up_swipe
        
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=up_swipe):
            result = self.navigator._recognize_gesture()
            self.assertEqual(result, "swipe_up", "Should recognize up swipe")
    
    def test_extract_active_movement(self):
        """Test extraction of active movement from a gesture path."""
        # Path with idle start, active middle, idle end
        full_path = self.generate_gesture_path([
            # Idle start
            (0.5, 0.5, 0), (0.501, 0.499, 0), (0.502, 0.501, 0),
            # Active middle (right swipe)
            (0.51, 0.5, 0), (0.55, 0.49, 0), (0.6, 0.5, 0), 
            (0.65, 0.51, 0), (0.7, 0.5, 0),
            # Idle end
            (0.701, 0.499, 0), (0.702, 0.501, 0), (0.7, 0.502, 0)
        ])
        
        active_path = self.navigator._extract_active_movement(full_path)
        
        # Check that the active part was extracted (should be the middle)
        self.assertLess(len(active_path), len(full_path), 
                        "Active path should be shorter than full path")
        self.assertGreater(len(active_path), 2, 
                          "Active path should contain multiple points")
        
        # Check first and last coords of active path
        first_pos, _ = active_path[0]
        last_pos, _ = active_path[-1]
        
        # First active point should be around the start of movement
        self.assertGreater(first_pos[0], 0.5)
        
        # Last active point should be around the end of movement
        self.assertGreater(last_pos[0], 0.65)
    
    def test_state_machine_transitions(self):
        """Test the gesture state machine transitions."""
        # Initialize with idle state
        self.navigator.gesture_state = self.navigator.GESTURE_STATE_IDLE
        
        # 1. From IDLE to POTENTIAL
        landmark = self.generate_landmark(0.5, 0.5)
        self.navigator.start_tracking_landmark(landmark)
        self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_POTENTIAL)
        
        # 2. From POTENTIAL to ACTIVE (with deliberate movement)
        with patch.object(self.navigator, '_has_deliberate_movement', return_value=True):
            with patch.object(self.navigator, '_is_hand_idle', return_value=False):
                for i in range(5):
                    # Move right
                    landmark = self.generate_landmark(0.5 + (i * 0.05), 0.5)
                    self.navigator.update_landmark_tracking(landmark)
                
                self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_ACTIVE)
        
        # 3. From ACTIVE to RECOGNIZED (when movement stops)
        with patch.object(self.navigator, '_is_hand_idle', return_value=True):
            with patch.object(self.navigator, '_recognize_gesture', return_value="swipe_right"):
                with patch.object(self.navigator, '_execute_gesture_action'):
                    # Hold still
                    for _ in range(self.navigator.required_idle_confirmations + 1):
                        landmark = self.generate_landmark(0.7, 0.5)
                        self.navigator.update_landmark_tracking(landmark)
                    
                    self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_RECOGNIZED)
        
        # 4. From RECOGNIZED back to IDLE (after cooldown)
        with patch.object(self.navigator, '_is_hand_idle', return_value=True):
            for _ in range(self.navigator.required_idle_confirmations + 1):
                landmark = self.generate_landmark(0.7, 0.5)
                self.navigator.update_landmark_tracking(landmark)
            
            self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
    
    def test_gesture_rejection(self):
        """Test that invalid gestures are properly rejected."""
        # Too few points
        self.navigator.gesture_path = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.51, 0.5, 0)  # Only 2 points
        ])
        
        result = self.navigator._recognize_gesture()
        self.assertIsNone(result, "Should reject gesture with too few points")
        
        # Too short distance
        self.navigator.gesture_path = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.51, 0.5, 0), (0.52, 0.5, 0), 
            (0.53, 0.5, 0), (0.54, 0.5, 0)  # Movement too small
        ])
        
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=self.navigator.gesture_path):
            result = self.navigator._recognize_gesture()
            self.assertIsNone(result, "Should reject gesture with insufficient distance")
        
        # Zigzag path (poor straightness)
        zigzag_path = self.generate_gesture_path([
            (0.5, 0.5, 0), (0.55, 0.55, 0), (0.6, 0.45, 0),
            (0.65, 0.55, 0), (0.7, 0.45, 0)
        ])
        
        with patch.object(self.navigator, '_extract_active_movement', 
                         return_value=zigzag_path):
            with patch.object(self.navigator, '_calculate_path_length', 
                             return_value=0.5):  # Make path length much longer than direct distance
                result = self.navigator._recognize_gesture()
                self.assertIsNone(result, "Should reject zigzag gesture with poor straightness")

# Run the tests
if __name__ == '__main__':
    unittest.main()
