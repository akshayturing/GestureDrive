"""
test_gesture_tracking.py - Unit tests for the gesture tracking system

Tests the functionality of the HandLandmarkTracker class and its gesture filtering capabilities.
"""

import unittest
import time
import math
import numpy as np
from unittest.mock import Mock, patch
from collections import deque

from gesture_tracking import HandLandmarkTracker, HandState

class MockLandmark:
    """Mock implementation of MediaPipe landmark for testing"""
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class TestHandLandmarkTracker(unittest.TestCase):
    """Test cases for the HandLandmarkTracker class"""
    
    def setUp(self):
        """Set up test environment before each test"""
        # Create tracker with shorter durations for faster testing
        self.tracker = HandLandmarkTracker(
            buffer_size=5,
            min_gesture_duration_ms=100,  # Use shorter duration for tests
            motion_consistency_frames=3
        )
        
        # Create standard test hand landmarks
        self.create_test_landmarks()
    
    def create_test_landmarks(self):
        """Create test hand landmark data for various scenarios"""
        # Basic landmark set - palm facing camera, fingers extended
        self.valid_hand_landmarks = self._create_extended_hand_landmarks()
        
        # Fist landmark set - fingers curled
        self.fist_hand_landmarks = self._create_fist_landmarks()
        
        # Side-facing hand - fingers not pointing to camera
        self.side_hand_landmarks = self._create_side_hand_landmarks()
        
        # Create mock MediaPipe multi_hand_landmarks structure
        self.mock_multi_hand_landmarks = [Mock()]
        self.mock_multi_hand_landmarks[0].landmark = self.valid_hand_landmarks
    
    def _create_extended_hand_landmarks(self):
        """Create landmarks for hand with extended fingers pointing at camera"""
        landmarks = []
        
        # Wrist at origin
        landmarks.append(MockLandmark(0.5, 0.5, 0))
        
        # Thumb landmarks (1-4)
        landmarks.append(MockLandmark(0.45, 0.5, 0))
        landmarks.append(MockLandmark(0.4, 0.48, 0))
        landmarks.append(MockLandmark(0.35, 0.46, -0.02))
        landmarks.append(MockLandmark(0.3, 0.45, -0.05))
        
        # Index finger landmarks (5-8)
        landmarks.append(MockLandmark(0.45, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.45, 0.35, -0.3))  # PIP
        landmarks.append(MockLandmark(0.45, 0.3, -0.5))  # DIP
        landmarks.append(MockLandmark(0.45, 0.25, -0.7))  # Tip
        
        # Middle finger landmarks (9-12)
        landmarks.append(MockLandmark(0.5, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.35, -0.3))  # PIP
        landmarks.append(MockLandmark(0.5, 0.3, -0.5))  # DIP
        landmarks.append(MockLandmark(0.5, 0.25, -0.7))  # Tip
        
        # Ring finger landmarks (13-16)
        landmarks.append(MockLandmark(0.55, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.55, 0.35, -0.3))  # PIP
        landmarks.append(MockLandmark(0.55, 0.3, -0.5))  # DIP
        landmarks.append(MockLandmark(0.55, 0.25, -0.7))  # Tip
        
        # Pinky finger landmarks (17-20)
        landmarks.append(MockLandmark(0.6, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.6, 0.35, -0.3))  # PIP
        landmarks.append(MockLandmark(0.6, 0.3, -0.5))  # DIP
        landmarks.append(MockLandmark(0.6, 0.25, -0.7))  # Tip
        
        return landmarks
    
    def _create_fist_landmarks(self):
        """Create landmarks for a closed fist posture"""
        landmarks = []
        
        # Wrist at origin
        landmarks.append(MockLandmark(0.5, 0.5, 0))
        
        # Thumb landmarks (1-4) - tucked
        landmarks.append(MockLandmark(0.45, 0.5, 0))
        landmarks.append(MockLandmark(0.4, 0.48, 0))
        landmarks.append(MockLandmark(0.4, 0.45, 0.1))
        landmarks.append(MockLandmark(0.42, 0.43, 0.12))
        
        # Index finger landmarks (5-8) - curled
        landmarks.append(MockLandmark(0.45, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.45, 0.35, -0.1))  # PIP
        landmarks.append(MockLandmark(0.47, 0.38, 0.1))  # DIP (curled)
        landmarks.append(MockLandmark(0.48, 0.42, 0.15))  # Tip (curled)
        
        # Middle finger landmarks (9-12) - curled
        landmarks.append(MockLandmark(0.5, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.35, -0.1))  # PIP
        landmarks.append(MockLandmark(0.52, 0.38, 0.1))  # DIP (curled)
        landmarks.append(MockLandmark(0.53, 0.42, 0.15))  # Tip (curled)
        
        # Ring finger landmarks (13-16) - curled
        landmarks.append(MockLandmark(0.55, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.55, 0.35, -0.1))  # PIP
        landmarks.append(MockLandmark(0.57, 0.38, 0.1))  # DIP (curled)
        landmarks.append(MockLandmark(0.58, 0.42, 0.15))  # Tip (curled)
        
        # Pinky finger landmarks (17-20) - curled
        landmarks.append(MockLandmark(0.6, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.6, 0.35, -0.1))  # PIP
        landmarks.append(MockLandmark(0.62, 0.38, 0.1))  # DIP (curled)
        landmarks.append(MockLandmark(0.63, 0.42, 0.15))  # Tip (curled)
        
        return landmarks
    
    def _create_side_hand_landmarks(self):
        """Create landmarks for a hand facing to the side (not at camera)"""
        landmarks = []
        
        # Wrist at origin
        landmarks.append(MockLandmark(0.5, 0.5, 0))
        
        # Thumb landmarks (1-4)
        landmarks.append(MockLandmark(0.45, 0.5, 0))
        landmarks.append(MockLandmark(0.4, 0.48, 0))
        landmarks.append(MockLandmark(0.35, 0.46, 0))
        landmarks.append(MockLandmark(0.3, 0.45, 0))
        
        # Index finger landmarks (5-8) - pointing right
        landmarks.append(MockLandmark(0.45, 0.4, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.4, 0))  # PIP
        landmarks.append(MockLandmark(0.55, 0.4, 0))  # DIP
        landmarks.append(MockLandmark(0.6, 0.4, 0))  # Tip
        
        # Middle finger landmarks (9-12) - pointing right
        landmarks.append(MockLandmark(0.45, 0.45, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.45, 0))  # PIP
        landmarks.append(MockLandmark(0.55, 0.45, 0))  # DIP
        landmarks.append(MockLandmark(0.6, 0.45, 0))  # Tip
        
        # Ring finger landmarks (13-16) - pointing right
        landmarks.append(MockLandmark(0.45, 0.5, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.5, 0))  # PIP
        landmarks.append(MockLandmark(0.55, 0.5, 0))  # DIP
        landmarks.append(MockLandmark(0.6, 0.5, 0))  # Tip
        
        # Pinky finger landmarks (17-20) - pointing right
        landmarks.append(MockLandmark(0.45, 0.55, 0))  # MCP
        landmarks.append(MockLandmark(0.5, 0.55, 0))  # PIP
        landmarks.append(MockLandmark(0.55, 0.55, 0))  # DIP
        landmarks.append(MockLandmark(0.6, 0.55, 0))  # Tip
        
        return landmarks
    
    def _add_trajectory_data(self, hand_idx=0, landmark_idx=8, trajectory=None):
        """
        Add test trajectory data to the tracker.
        
        Args:
            hand_idx: Hand index
            landmark_idx: Landmark index
            trajectory: List of (x,y,z,t) tuples representing position and time
        """
        if trajectory is None:
            return
            
        hand_key = f"hand_{hand_idx}"
        landmark_key = f"landmark_{landmark_idx}"
        
        if hand_key not in self.tracker.landmark_history:
            self.tracker.landmark_history[hand_key] = {}
            
        if landmark_key not in self.tracker.landmark_history[hand_key]:
            self.tracker.landmark_history[hand_key][landmark_key] = deque(maxlen=self.tracker.buffer_size)
            
        # Add trajectory data
        for x, y, z, t in trajectory:
            self.tracker.landmark_history[hand_key][landmark_key].append({
                'x': x, 'y': y, 'z': z, 'timestamp': t
            })
    
    def _simulate_left_swipe(self, current_time=1.0):
        """Simulate a left swipe motion trajectory"""
        # Create motion from right to left over 0.5 seconds
        trajectory = [
            (0.7, 0.5, 0, current_time - 0.5),  # Start position
            (0.6, 0.5, 0, current_time - 0.4),
            (0.5, 0.5, 0, current_time - 0.3),
            (0.4, 0.5, 0, current_time - 0.2),
            (0.3, 0.5, 0, current_time - 0.1),
            (0.2, 0.5, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)
    
    def _simulate_right_swipe(self, current_time=1.0):
        """Simulate a right swipe motion trajectory"""
        # Create motion from left to right over 0.5 seconds
        trajectory = [
            (0.2, 0.5, 0, current_time - 0.5),  # Start position
            (0.3, 0.5, 0, current_time - 0.4),
            (0.4, 0.5, 0, current_time - 0.3),
            (0.5, 0.5, 0, current_time - 0.2),
            (0.6, 0.5, 0, current_time - 0.1),
            (0.7, 0.5, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)
    
    def _simulate_up_swipe(self, current_time=1.0):
        """Simulate an upward swipe motion trajectory"""
        # Create motion from bottom to top over 0.5 seconds 
        trajectory = [
            (0.5, 0.7, 0, current_time - 0.5),  # Start position
            (0.5, 0.6, 0, current_time - 0.4),
            (0.5, 0.5, 0, current_time - 0.3),
            (0.5, 0.4, 0, current_time - 0.2),
            (0.5, 0.3, 0, current_time - 0.1),
            (0.5, 0.2, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)

    def _simulate_down_swipe(self, current_time=1.0):
        """Simulate a downward swipe motion trajectory"""
        # Create motion from top to bottom over 0.5 seconds
        trajectory = [
            (0.5, 0.2, 0, current_time - 0.5),  # Start position
            (0.5, 0.3, 0, current_time - 0.4),
            (0.5, 0.4, 0, current_time - 0.3),
            (0.5, 0.5, 0, current_time - 0.2),
            (0.5, 0.6, 0, current_time - 0.1),
            (0.5, 0.7, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)
    
    def _simulate_erratic_motion(self, current_time=1.0):
        """Simulate an erratic, non-directional motion"""
        trajectory = [
            (0.5, 0.5, 0, current_time - 0.5),  # Start position
            (0.6, 0.4, 0, current_time - 0.4),
            (0.5, 0.6, 0, current_time - 0.3),
            (0.4, 0.5, 0, current_time - 0.2),
            (0.5, 0.4, 0, current_time - 0.1),
            (0.6, 0.5, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)
    
    def _simulate_idle_hand(self, current_time=1.0):
        """Simulate an idle hand with minimal movement"""
        trajectory = [
            (0.5, 0.5, 0, current_time - 0.5),  # Start position
            (0.505, 0.498, 0, current_time - 0.4),
            (0.503, 0.502, 0, current_time - 0.3),
            (0.498, 0.501, 0, current_time - 0.2),
            (0.5, 0.499, 0, current_time - 0.1),
            (0.502, 0.5, 0, current_time)         # End position
        ]
        self._add_trajectory_data(trajectory=trajectory)

    def _simulate_starting_motion(self, current_time=1.0):
        """Simulate a hand just starting to move to the left (transitional)"""
        trajectory = [
            (0.52, 0.5, 0, current_time - 0.5),  # Start with minimal movement
            (0.51, 0.5, 0, current_time - 0.4),
            (0.5, 0.5, 0, current_time - 0.3),
            (0.48, 0.5, 0, current_time - 0.2),  # Starting to move left
            (0.45, 0.5, 0, current_time - 0.1),  # Accelerating left
            (0.4, 0.5, 0, current_time)          # Moving left
        ]
        self._add_trajectory_data(trajectory=trajectory)
        
    # ---- Test Cases ----
        
    def test_add_landmarks(self):
        """Test that landmarks can be added to the tracker"""
        # Add mock landmarks
        self.tracker.add_landmarks(self.mock_multi_hand_landmarks)
        
        # Verify landmarks were added
        self.assertTrue("hand_0" in self.tracker.landmark_history)
        self.assertTrue("landmark_0" in self.tracker.landmark_history["hand_0"])
        self.assertEqual(len(self.tracker.landmark_history["hand_0"]["landmark_0"]), 1)
        
        # Verify landmark data
        landmark_data = self.tracker.landmark_history["hand_0"]["landmark_0"][0]
        self.assertEqual(landmark_data["x"], 0.5)
        self.assertEqual(landmark_data["y"], 0.5)
        self.assertEqual(landmark_data["z"], 0)
        self.assertTrue("timestamp" in landmark_data)
    
    # def test_calculate_velocity(self):
    #     """Test velocity calculation from landmarks"""
    #     # Add trajectory data for a left swipe
    #     current_time = 1.0
    #     self._simulate_left_swipe(current_time)
        
    #     # Calculate velocity
    #     velocities = self.tracker.calculate_velocity()
        
    #     # Verify velocities
    #     self.assertIsNotNone(velocities)
    #     self.assertEqual(len(velocities), 5)  # 6 positions -> 5 velocities
        
    #     # Verify velocity direction is negative in x (left swipe)
    #     for velocity in velocities:
    #         self.assertTrue(velocity["vx"] < 0)  # Moving left = negative x velocity
    #         self.assertAlmostEqual(velocity["vy"], 0, delta=0.01)  # No significant y movement
    
    def test_calculate_velocity(self):
        """Test velocity calculation from landmarks"""
        # Add trajectory data for a left swipe
        current_time = 1.0
        self._simulate_left_swipe(current_time)
        
        # Calculate velocity
        velocities = self.tracker.calculate_velocity()
        
        # Verify velocities
        self.assertIsNotNone(velocities)
        self.assertEqual(len(velocities), 5, f"Expected 5 velocity samples, got {len(velocities)}")
        
        # Verify velocity direction is negative in x (left swipe)
        for velocity in velocities:
            self.assertTrue(velocity["vx"] < 0)  # Moving left = negative x velocity
            self.assertAlmostEqual(velocity["vy"], 0, delta=0.01)  # No significant y movement
    def test_is_valid_hand_posture(self):
        """Test hand posture validation"""
        # Test with valid posture (extended fingers toward camera)
        validity = self.tracker.is_valid_hand_posture(self.valid_hand_landmarks)
        self.assertTrue(validity)
        
        # Test with fist posture (should be invalid)
        validity = self.tracker.is_valid_hand_posture(self.fist_hand_landmarks)
        self.assertFalse(validity)
        
        # Test with side-facing hand posture (should be invalid)
        validity = self.tracker.is_valid_hand_posture(self.side_hand_landmarks)
        self.assertFalse(validity)
    
    def test_determine_hand_state(self):
        """Test hand state classification"""
        # Test with idle hand
        current_time = 1.0
        self._simulate_idle_hand(current_time)
        velocities = self.tracker.calculate_velocity()
        state, avg_vel = self.tracker.determine_hand_state(velocities)
        self.assertEqual(state, HandState.IDLE)
        self.assertLess(avg_vel, self.tracker.idle_threshold)
        
        # Test with deliberate left swipe
        self._simulate_left_swipe(current_time)
        velocities = self.tracker.calculate_velocity()
        state, avg_vel = self.tracker.determine_hand_state(velocities)
        self.assertEqual(state, HandState.DELIBERATE)
        self.assertGreater(avg_vel, self.tracker.deliberate_threshold)
        
        # Test with transitioning/starting motion
        self._simulate_starting_motion(current_time)
        velocities = self.tracker.calculate_velocity()
        state, avg_vel = self.tracker.determine_hand_state(velocities)
        self.assertEqual(state, HandState.TRANSITIONING)
    
    # def test_is_motion_consistent(self):
    #     """Test motion consistency detection"""
    #     # Reset tracker's recent directions
    #     self.tracker.recent_directions.clear()
        
    #     # Add consistent leftward motion
    #     self.assertFalse(self.tracker.is_motion_consistent("swipe_left"))  # First call, not enough history
    #     self.tracker.recent_directions.append("swipe_left")
    #     self.assertFalse(self.tracker.is_motion_consistent("swipe_left"))  # Second call, still not enough
    #     self.tracker.recent_directions.append("swipe_left")
    #     self.assertTrue(self.tracker.is_motion_consistent("swipe_left"))  # Third call, now consistent
        
    #     # Test inconsistent motion
    #     self.tracker.recent_directions[-1] = "swipe_right"  # Change last direction
    #     self.assertFalse(self.tracker.is_motion_consistent("swipe_left"))  # No longer consistent
    
    def test_is_motion_consistent(self):
        """Test motion consistency detection"""
        # Reset tracker's recent directions
        self.tracker.recent_directions.clear()
        
        # Test with insufficient history
        self.assertFalse(self.tracker.is_motion_consistent("swipe_left"), 
                        "Should fail with no history")
        
        # Add one entry - still insufficient
        self.tracker.recent_directions.append("swipe_left")
        self.assertFalse(self.tracker.is_motion_consistent("swipe_left"), 
                        "Should fail with only 1 history entry")
        
        # Add second entry - now it has minimum required history (2)
        self.tracker.recent_directions.append("swipe_left")
        self.assertTrue(self.tracker.is_motion_consistent("swipe_left"), 
                        "Should pass with 2 consistent entries")
        
        # Test with inconsistent history
        self.tracker.recent_directions.clear()
        self.tracker.recent_directions.extend(["swipe_left", "swipe_right"])
        self.assertFalse(self.tracker.is_motion_consistent("swipe_left"), 
                        "Should fail with inconsistent history")
        
        # Test when current motion is not the most frequent
        self.tracker.recent_directions.clear()
        self.tracker.recent_directions.extend(["swipe_left", "swipe_left", "swipe_right"])
        self.assertFalse(self.tracker.is_motion_consistent("swipe_right"), 
                        "Should fail when current motion isn't most frequent")

    def test_detect_motion_gesture_valid_swipe(self):
        """Test detection of a valid swipe gesture"""
        # Simulate a deliberate left swipe with valid hand posture
        current_time = 1.0
        self._simulate_left_swipe(current_time)
        
        # First call with valid posture but duration not met
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        self.assertEqual(motion, "swipe_left")
        self.assertFalse(is_valid)  # Not valid yet (duration not met)
        
        # Second call after duration requirement is met
        # Track gesture for longer than min_gesture_duration
        self.tracker.current_motion_candidate = "swipe_left"
        self.tracker.motion_start_time = current_time - 0.2  # 200ms > 100ms requirement
        
        # Add motion consistency
        self.tracker.recent_directions.extend(["swipe_left", "swipe_left", "swipe_left"])
        
        # Call again
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        
        # Now the gesture should be valid
        self.assertEqual(motion, "swipe_left")
        self.assertTrue(is_valid)
    
    def test_detect_motion_gesture_invalid_posture(self):
        """Test rejection of gesture with invalid hand posture"""
        # Simulate a left swipe but with fist posture
        current_time = 1.0
        self._simulate_left_swipe(current_time)
        
        # Call with invalid posture
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.fist_hand_landmarks, 
            current_time=current_time
        )
        
        # Should reject due to invalid posture
        self.assertEqual(motion, "invalid_posture")
        self.assertFalse(is_valid)
    
    def test_detect_motion_gesture_erratic_movement(self):
        """Test rejection of erratic, non-directional movement"""
        # Simulate erratic movement
        current_time = 1.0
        self._simulate_erratic_motion(current_time)
        
        # Call with valid posture but erratic motion
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        
        # Should not recognize as a directional gesture
        self.assertIn(motion, ["transitioning", "unclear_direction"])
        self.assertFalse(is_valid)
    
    def test_detect_motion_gesture_all_directions(self):
        """Test detection of gestures in all directions"""
        current_time = 1.0
        
        # Test left swipe
        self._simulate_left_swipe(current_time)
        motion, _ = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        self.assertEqual(motion, "swipe_left")
        
        # Test right swipe
        self.tracker = HandLandmarkTracker(min_gesture_duration_ms=100)  # Reset tracker
        self._simulate_right_swipe(current_time)
        motion, _ = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        self.assertEqual(motion, "swipe_right")
        
        # Test up swipe
        self.tracker = HandLandmarkTracker(min_gesture_duration_ms=100)  # Reset tracker
        self._simulate_up_swipe(current_time)
        motion, _ = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        self.assertEqual(motion, "swipe_up")
        
        # Test down swipe
        self.tracker = HandLandmarkTracker(min_gesture_duration_ms=100)  # Reset tracker
        self._simulate_down_swipe(current_time)
        motion, _ = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        self.assertEqual(motion, "swipe_down")
    
    def test_idle_hand_detection(self):
        """Test that idle hands don't trigger gestures"""
        # Simulate an idle hand
        current_time = 1.0
        self._simulate_idle_hand(current_time)
        
        # Call with valid posture but idle motion
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        
        # Should identify as stationary
        self.assertEqual(motion, "stationary")
        self.assertFalse(is_valid)
        self.assertEqual(self.tracker.current_hand_state, HandState.IDLE)
    
    # def test_transitioning_hand_detection(self):
    #     """Test that transitioning hands are correctly identified"""
    #     # Simulate a hand starting to move
    #     current_time = 1.0
    #     self._simulate_starting_motion(current_time)
        
    #     # Call with valid posture and transitioning motion
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.valid_hand_landmarks, 
    #         current_time=current_time
    #     )
        
    #     # Should recognize as transitioning
    #     self.assertIn(self.tracker.current_hand_state.name, ["TRANSITIONING", "DELIBERATE"])
    #     # May be "transitioning" or might detect as "swipe_left" depending on threshold, 
    #     # but should not be validated
    #     self.assertFalse(is_valid)
    
    def test_transitioning_hand_detection(self):
        """Test that transitioning hands are correctly identified"""
        # Simulate a hand starting to move
        current_time = 1.0
        self._simulate_starting_motion(current_time)
        
        # Call with valid posture and transitioning motion
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks, 
            current_time=current_time
        )
        
        # Should specifically recognize as transitioning
        self.assertEqual(self.tracker.current_hand_state, HandState.TRANSITIONING,
                        f"Expected TRANSITIONING state, got {self.tracker.current_hand_state.name}")
        self.assertFalse(is_valid)
    def test_get_debug_info(self):
        """Test debug info collection"""
        # Set up some state
        self.tracker.current_motion_candidate = "swipe_left"
        self.tracker.debug_info["posture_valid"] = True
        self.tracker.debug_info["tracking_duration"] = 0.15
        
        # Get debug info
        debug_info = self.tracker.get_debug_info()
        
        # Verify expected keys exist
        expected_keys = [
            "current_candidate", "has_validated_motion", "validation_reason", 
            "tracking_duration", "posture_valid", "hand_state"
        ]
        for key in expected_keys:
            self.assertIn(key, debug_info)
        
        # Verify values
        self.assertEqual(debug_info["current_candidate"], "swipe_left")
        self.assertEqual(debug_info["tracking_duration"], 0.15)
        self.assertTrue(debug_info["posture_valid"])
    
    def test_reset_tracking(self):
        """Test tracking reset functionality"""
        # Set up some state
        self.tracker.current_motion_candidate = "swipe_left"
        self.tracker.motion_start_time = 1.0
        self.tracker.validated_motion = "swipe_left"
        self.tracker.recent_directions.extend(["swipe_left", "swipe_left"])
        self.tracker.recent_states.extend([HandState.DELIBERATE, HandState.DELIBERATE])
        
        # Reset tracking
        self.tracker.reset_tracking()
        
        # Verify state is reset
        self.assertIsNone(self.tracker.current_motion_candidate)
        self.assertEqual(self.tracker.motion_start_time, 0)
        self.assertIsNone(self.tracker.validated_motion)
        self.assertEqual(len(self.tracker.recent_directions), 0)
        self.assertEqual(len(self.tracker.recent_states), 0)

    # def test_end_to_end_gesture_filtering(self):
    #     """Test the complete gesture filtering pipeline with a realistic scenario"""
    #     # Start with tracker in a clean state
    #     self.tracker = HandLandmarkTracker(
    #         buffer_size=5,
    #         min_gesture_duration_ms=200,
    #         motion_consistency_frames=3
    #     )
        
    #     # 1. First simulate idle hand with valid posture
    #     current_time = 0.0
    #     self._simulate_idle_hand(current_time)
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.valid_hand_landmarks,
    #         current_time=current_time
    #     )
    #     self.assertEqual(motion, "stationary")
    #     self.assertFalse(is_valid)
        
    #     # 2. Now simulate the beginning of a left swipe (transitioning)
    #     current_time = 0.5
    #     self._simulate_starting_motion(current_time)
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.valid_hand_landmarks,
    #         current_time=current_time
    #     )
    #     # Since the hand is just starting to move, it should not validate
    #     self.assertFalse(is_valid)
        
    #     # 3. Now simulate a deliberate left swipe
    #     current_time = 1.0
    #     self._simulate_left_swipe(current_time)
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.valid_hand_landmarks,
    #         current_time=current_time
    #     )
    #     # First time detecting the swipe, should set the candidate but not validate yet
    #     self.assertEqual(motion, "swipe_left")
    #     self.assertFalse(is_valid)
        
    #     # 4. Continue the same gesture for long enough to meet duration requirement
    #     # The consistent sustained gesture should now validate
    #     self.tracker.current_motion_candidate = "swipe_left"
    #     self.tracker.motion_start_time = current_time - 0.3  # 300ms > 200ms requirement
    #     self.tracker.recent_directions.extend(["swipe_left", "swipe_left", "swipe_left"])
        
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.valid_hand_landmarks,
    #         current_time=current_time
    #     )
    #     # Now it should validate the gesture
    #     self.assertEqual(motion, "swipe_left")
    #     self.assertTrue(is_valid)
        
    #     # 5. Finally, test that changing to invalid posture rejects the gesture
    #     current_time = 1.5
    #     motion, is_valid = self.tracker.detect_motion_gesture(
    #         self.fist_hand_landmarks,
    #         current_time=current_time
    #     )
    #     # Should reject due to invalid posture
    #     self.assertEqual(motion, "invalid_posture")
    #     self.assertFalse(is_valid)
    def test_end_to_end_gesture_filtering(self):
        """Test the complete gesture filtering pipeline with a realistic scenario"""
        # Start with tracker in a clean state
        self.tracker = HandLandmarkTracker(
            buffer_size=5,
            min_gesture_duration_ms=200,
            motion_consistency_frames=3
        )
        
        # 1. First simulate idle hand with valid posture
        current_time = 0.0
        self._simulate_idle_hand(current_time)
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks,
            current_time=current_time
        )
        self.assertEqual(motion, "stationary")
        self.assertFalse(is_valid)
        
        # 2. Now simulate the beginning of a left swipe (transitioning)
        current_time = 0.5
        self._simulate_starting_motion(current_time)
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks,
            current_time=current_time
        )
        # Since the hand is just starting to move, it should not validate
        self.assertFalse(is_valid)
        
        # 3. Now simulate a more deliberate left swipe
        current_time = 1.0
        self._simulate_left_swipe(current_time)
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks,
            current_time=current_time
        )
        # First time detecting the swipe, should set the candidate but not validate yet
        self.assertEqual(motion, "swipe_left")
        self.assertFalse(is_valid)
        
        # 4. Continue the same gesture for long enough to meet duration requirement
        # But we need to ensure the hand state has been DELIBERATE long enough
        self.tracker.current_motion_candidate = "swipe_left"
        self.tracker.motion_start_time = current_time - 0.3  # 300ms > 200ms requirement
        self.tracker.recent_directions.extend(["swipe_left", "swipe_left", "swipe_left"])
        
        # Add sufficient DELIBERATE state history
        self.tracker.recent_states.extend([HandState.DELIBERATE, HandState.DELIBERATE, HandState.DELIBERATE])
        
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.valid_hand_landmarks,
            current_time=current_time
        )
        # Now it should validate the gesture
        self.assertEqual(motion, "swipe_left")
        self.assertTrue(is_valid, "Gesture should be validated when all criteria are met")
        
        # 5. Finally, test that changing to invalid posture rejects the gesture
        current_time = 1.5
        motion, is_valid = self.tracker.detect_motion_gesture(
            self.fist_hand_landmarks,
            current_time=current_time
        )
        # Should reject due to invalid posture
        self.assertEqual(motion, "invalid_posture")
        self.assertFalse(is_valid)

if __name__ == '__main__':
    unittest.main()