# test_persistent_navigator.py

import unittest
import os
import shutil
import tempfile
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

class TestPersistentNavigator(unittest.TestCase):
    """Integration tests for the PersistentGestureNavigator."""
    
    def setUp(self):
        """Set up test environment with temporary directory structure."""
        # Create a temporary directory structure for testing
        self.temp_root = tempfile.mkdtemp(prefix="gesture_drive_test_")
        
        # Create a test directory structure
        self.test_dirs = {
            'main': self.temp_root,
            'dir1': os.path.join(self.temp_root, "dir1"),
            'dir2': os.path.join(self.temp_root, "dir2"),
            'subdir1': os.path.join(self.temp_root, "dir1", "subdir1"),
        }
        
        # Create the directories
        for dir_path in self.test_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
            
        # Create some test files
        self.test_files = {
            'file1': os.path.join(self.test_dirs['main'], "file1.txt"),
            'file2': os.path.join(self.test_dirs['dir1'], "file2.txt"),
            'file3': os.path.join(self.test_dirs['dir2'], "file3.txt"),
        }
        
        # Write some content to the files
        for file_path in self.test_files.values():
            with open(file_path, 'w') as f:
                f.write(f"Test content for {os.path.basename(file_path)}")
                
        # Create a test state file
        self.test_state_file = os.path.join(self.temp_root, "test_nav_state.json")
        
        # Create mock camera
        self.mock_camera = Mock()
        self.mock_camera.hand_landmarks_data = None
        
        # Import the navigator here to allow patching
        from persistent_gesture_navigator import PersistentGestureNavigator
        
        # Path DirectoryStateManager to use our test file and initial directory
        with patch('persistent_gesture_navigator.DirectoryStateManager') as MockManager:
            # Configure the mock manager
            self.mock_manager = Mock()
            self.mock_manager.get_current_directory.return_value = Path(self.test_dirs['main'])
            self.mock_manager.get_selection_index.return_value = 0
            
            # Make manager return our configured mock
            MockManager.return_value = self.mock_manager
            
            # Create the navigator with patched dependencies
            self.navigator = PersistentGestureNavigator(self.mock_camera)
            
    def tearDown(self):
        """Clean up the test environment."""
        # Clean up resources
        if hasattr(self, 'navigator'):
            self.navigator.shutdown()
        
        # Remove temporary directory
        try:
            shutil.rmtree(self.temp_root)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not remove temporary directory: {e}")
    
    def generate_landmark(self, x, y, z=0):
        """Generate a mock landmark with the given coordinates."""
        landmark = Mock()
        landmark.x = x
        landmark.y = y
        landmark.z = z
        return landmark
    
    def generate_hand_landmarks(self, main_landmark=None):
        """
        Generate mock hand landmarks.
        
        Args:
            main_landmark: Optional specific landmark for index finger (landmark 8)
        
        Returns:
            Mock hand landmarks object
        """
        landmarks = []
        
        # Create 21 landmarks for a hand
        for i in range(21):
            if i == 8 and main_landmark is not None:
                landmarks.append(main_landmark)
            else:
                # Default positions for other landmarks
                landmarks.append(self.generate_landmark(0.5, 0.5))
        
        hand_landmarks = Mock()
        hand_landmarks.landmark = landmarks
        return [hand_landmarks]
    
    def simulate_gesture(self, gesture_type, landmark_positions=None):
        """
        Simulate a complete gesture sequence.
        
        Args:
            gesture_type: Type of gesture to simulate ("left", "right", "up", "down")
            landmark_positions: Optional custom sequence of (x, y) positions
        """
        if landmark_positions is None:
            # Default landmark paths for each gesture type
            if gesture_type == "left":
                landmark_positions = [
                    (0.7, 0.5), (0.65, 0.5), (0.6, 0.5), 
                    (0.55, 0.5), (0.5, 0.5), (0.45, 0.5), (0.4, 0.5), (0.35, 0.5)
                ]
            elif gesture_type == "right":
                landmark_positions = [
                    (0.3, 0.5), (0.35, 0.5), (0.4, 0.5), 
                    (0.45, 0.5), (0.5, 0.5), (0.55, 0.5), (0.6, 0.5), (0.65, 0.5)
                ]
            elif gesture_type == "up":
                landmark_positions = [
                    (0.5, 0.7), (0.5, 0.65), (0.5, 0.6), 
                    (0.5, 0.55), (0.5, 0.5), (0.5, 0.45), (0.5, 0.4), (0.5, 0.35)
                ]
            elif gesture_type == "down":
                landmark_positions = [
                    (0.5, 0.3), (0.5, 0.35), (0.5, 0.4), 
                    (0.5, 0.45), (0.5, 0.5), (0.5, 0.55), (0.5, 0.6), (0.5, 0.65)
                ]
            else:
                raise ValueError(f"Unknown gesture type: {gesture_type}")
        
        # Start tracking
        landmark = self.generate_landmark(*landmark_positions[0])
        self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(landmark)
        
        # Force state to POTENTIAL to start
        with patch.object(self.navigator, '_is_hand_idle', return_value=False):
            with patch.object(self.navigator, '_has_deliberate_movement', return_value=False):
                self.navigator.update()
        
        # Simulate gesture movement - each position
        for pos in landmark_positions:
            landmark = self.generate_landmark(*pos)
            self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(landmark)
            
            # Force deliberate movement detection
            with patch.object(self.navigator, '_has_deliberate_movement', return_value=True):
                with patch.object(self.navigator, '_is_hand_idle', return_value=False):
                    self.navigator.update()
        
        # Make hand stationary to trigger recognition
        final_pos = landmark_positions[-1]
        landmark = self.generate_landmark(*final_pos)
        self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(landmark)
        
        # Force idle detection to trigger gesture recognition
        with patch.object(self.navigator, '_is_hand_idle', return_value=True):
            for _ in range(self.navigator.required_idle_confirmations + 1):
                self.navigator.update()
    
    def test_gesture_state_machine(self):
        """Test the complete gesture state machine flow."""
        # Initial state should be idle
        self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
        
        # 1. No hand landmarks - should stay idle
        self.mock_camera.hand_landmarks_data = None
        self.navigator.update()
        self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
        
        # 2. Hand appears - should move to POTENTIAL
        self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(
            self.generate_landmark(0.5, 0.5)
        )
        with patch.object(self.navigator, 'gesture_cooldown', 0):  # Bypass cooldown
            self.navigator.update()
            self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_POTENTIAL)
        
        # 3. Hand moves deliberately - should move to ACTIVE
        with patch.object(self.navigator, '_is_hand_idle', return_value=False):
            with patch.object(self.navigator, '_has_deliberate_movement', return_value=True):
                self.navigator.update()
                self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_ACTIVE)
        
        # 4. Hand becomes idle again - should try to recognize
        with patch.object(self.navigator, '_is_hand_idle', return_value=True):
            with patch.object(self.navigator, '_recognize_gesture', return_value="swipe_right"):
                with patch.object(self.navigator, '_execute_gesture_action'):
                    # Simulate required idle confirmations
                    for _ in range(self.navigator.required_idle_confirmations + 1):
                        self.navigator.update()
                    
                    self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_RECOGNIZED)
        
        # 5. After recognition, should eventually return to idle
        with patch.object(self.navigator, '_is_hand_idle', return_value=True):
            for _ in range(self.navigator.required_idle_confirmations + 1):
                self.navigator.update()
            
            self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
    
    @patch('persistent_gesture_navigator.PersistentGestureNavigator._recognize_gesture')
    @patch('persistent_gesture_navigator.PersistentGestureNavigator._execute_gesture_action')
    def test_gesture_navigation_commands(self, mock_execute, mock_recognize):
        """Test that each gesture triggers the correct navigation command."""
        # Configure gesture recognition for different gestures
        
        # 1. Right swipe - Enter selected directory
        mock_recognize.return_value = "swipe_right"
        self.simulate_gesture("right")
        mock_execute.assert_called_with("swipe_right")
        mock_execute.reset_mock()
        
        # 2. Left swipe - Back in history
        mock_recognize.return_value = "swipe_left"
        self.simulate_gesture("left")
        mock_execute.assert_called_with("swipe_left")
        mock_execute.reset_mock()
        
        # 3. Up swipe - Parent directory
        mock_recognize.return_value = "swipe_up"
        self.simulate_gesture("up")
        mock_execute.assert_called_with("swipe_up")
        mock_execute.reset_mock()
        
        # 4. Down swipe - Select next
        mock_recognize.return_value = "swipe_down"
        self.simulate_gesture("down")
        mock_execute.assert_called_with("swipe_down")
    
    def test_continue_tracking_after_recognized_gesture(self):
        """Test that navigator can recognize a new gesture after a successful one."""
        # Simulate a complete gesture cycle
        with patch.object(self.navigator, '_recognize_gesture', return_value="swipe_right"):
            with patch.object(self.navigator, '_execute_gesture_action'):
                self.simulate_gesture("right")
                
        # Verify state returned to idle
        self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
        
        # Simulate the start of a new gesture
        with patch.object(self.navigator, 'gesture_cooldown', 0):  # Bypass cooldown
            self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(
                self.generate_landmark(0.5, 0.5)
            )
            self.navigator.update()
            
            # Should be able to enter potential state again
            self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_POTENTIAL)
    
    def test_vertical_movement_detection(self):
        """Test continuous vertical movement detection for scrolling."""
        # Set up mock selection methods
        self.navigator.select_next = Mock()
        self.navigator.select_previous = Mock()
        
        # Set state to idle for vertical movement detection
        self.navigator.gesture_state = self.navigator.GESTURE_STATE_IDLE
        self.navigator.tracking_active = True
        
        # Create a gesture path with clear downward movement
        self.navigator.gesture_path = []
        start_time = time.time() - 0.25  # Start 0.25 seconds ago
        
        # Add points with timestamps 50ms apart
        for i in range(5):
            y = 0.5 + (i * 0.02)  # Move down
            self.navigator.gesture_path.append(((0.5, y, 0), start_time + (i * 0.05)))
        
        # Reset the last scroll time to allow scrolling
        self.navigator.last_scroll_time = 0
        
        # Call check_vertical_movement with a landmark at the bottom of the path
        landmark = self.generate_landmark(0.5, 0.6)
        self.navigator.check_vertical_movement(landmark)
        
        # Should have called select_next
        self.navigator.select_next.assert_called_once()
        self.navigator.select_previous.assert_not_called()
        
        # Reset mocks
        self.navigator.select_next.reset_mock()
        self.navigator.select_previous.reset_mock()
        
        # Test upward movement
        self.navigator.gesture_path = []
        for i in range(5):
            y = 0.5 - (i * 0.02)  # Move up
            self.navigator.gesture_path.append(((0.5, y, 0), start_time + (i * 0.05)))
        
        # Reset the last scroll time
        self.navigator.last_scroll_time = 0
        
        # Call check_vertical_movement with a landmark at the top of the path
        landmark = self.generate_landmark(0.5, 0.4)
        self.navigator.check_vertical_movement(landmark)
        
        # Should have called select_previous
        self.navigator.select_previous.assert_called_once()
        self.navigator.select_next.assert_not_called()
    
    def test_ui_elements(self):
        """Test that UI drawing includes all required elements."""
        import numpy as np
        import cv2
        
        # Create a test frame
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        
        # Set some state for UI display
        self.navigator.current_directory = Path(self.test_dirs['dir1'])
        self.navigator.current_items = [
            {'name': 'file1.txt', 'path': '/path/to/file1.txt', 'is_dir': False},
            {'name': 'subdir1', 'path': '/path/to/subdir1', 'is_dir': True},
        ]
        self.navigator.selected_index = 0
        self.navigator.status_message = "Test status message"
        self.navigator.tracking_active = True
        self.navigator.gesture_state = self.navigator.GESTURE_STATE_ACTIVE
        self.navigator.gesture_path = [
            ((0.3, 0.5, 0), time.time() - 0.2),
            ((0.4, 0.5, 0), time.time() - 0.15),
            ((0.5, 0.5, 0), time.time() - 0.1),
        ]
        
        # Draw UI
        result_frame = self.navigator.draw_ui(frame)
        
        # Very basic check - result should not be the same as input (should have drawings)
        self.assertFalse(np.array_equal(frame, result_frame))
        
        # More complex checking would require image analysis or mocking opencv functions
        # For basic test, just verify the frame was modified
        modified = False
        for i in range(frame.shape[0]):
            for j in range(frame.shape[1]):
                if not np.array_equal(frame[i, j], result_frame[i, j]):
                    modified = True
                    break
            if modified:
                break
                
        self.assertTrue(modified)
    
    @patch('persistent_gesture_navigator.PersistentGestureNavigator._is_hand_idle')
    @patch('persistent_gesture_navigator.PersistentGestureNavigator._has_deliberate_movement')
    @patch('persistent_gesture_navigator.PersistentGestureNavigator._recognize_gesture')
    def test_gesture_timeout(self, mock_recognize, mock_deliberate, mock_idle):
        """Test that potential gestures time out if not completed."""
        # Set up for a potential gesture that never becomes active
        mock_idle.return_value = False
        mock_deliberate.return_value = False
        mock_recognize.return_value = None
        
        # Create a gesture path
        landmark = self.generate_landmark(0.5, 0.5)
        self.mock_camera.hand_landmarks_data = self.generate_hand_landmarks(landmark)
        
        # Update to start gesture
        with patch.object(self.navigator, 'gesture_cooldown', 0):
            self.navigator.update()
            self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_POTENTIAL)
        
        # Manipulate the potential start time to simulate timeout
        self.navigator.potential_start_time = time.time() - (self.navigator.idle_potential_timeout + 1)
        
        # Update again - should timeout
        self.navigator.update()
        self.assertEqual(self.navigator.gesture_state, self.navigator.GESTURE_STATE_IDLE)
    
    @patch('persistent_gesture_navigator.time.time')
    def test_idle_detection_timing(self, mock_time):
        """Test the timing mechanism in idle detection."""
        # Set initial time
        start_time = 1000.0
        mock_time.return_value = start_time
        
        # Set up a gesture path with consistent movement
        self.navigator.gesture_path = [
            ((0.5, 0.5, 0), start_time - 0.5),
            ((0.55, 0.5, 0), start_time - 0.4),
            ((0.6, 0.5, 0), start_time - 0.3),
            ((0.65, 0.5, 0), start_time - 0.2),
            ((0.7, 0.5, 0), start_time - 0.1),
        ]
        
        # Hand should not be idle with this movement
        result = self.navigator._is_hand_idle(self.navigator.gesture_path)
        self.assertFalse(result)
        
        # Now add some smaller movements at the end to simulate stopping
        self.navigator.gesture_path.extend([
            ((0.701, 0.501, 0), start_time - 0.08),
            ((0.7, 0.499, 0), start_time - 0.06),
            ((0.702, 0.5, 0), start_time - 0.04),
            ((0.701, 0.501, 0), start_time - 0.02),
        ])
        
        # Only look at recent points (last 200ms)
        mock_time.return_value = start_time
        with patch.object(self.navigator, '_is_hand_idle', wraps=self.navigator._is_hand_idle) as wrapped_idle:
            result = wrapped_idle(self.navigator.gesture_path, time_window=0.2)
            
            # Should be considered idle since recent points (last 200ms) have minimal movement
            self.assertTrue(result)
        
        # Look at all points (last 1 second)
        mock_time.return_value = start_time
        with patch.object(self.navigator, '_is_hand_idle', wraps=self.navigator._is_hand_idle) as wrapped_idle:
            result = wrapped_idle(self.navigator.gesture_path, time_window=1.0)
            
            # Should not be idle since full path has significant movement
            self.assertFalse(result)

# Run the tests
if __name__ == '__main__':
    unittest.main()
