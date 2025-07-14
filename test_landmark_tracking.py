import unittest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
import sys
import os
import math

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Camera and LandmarkSmoother
from camera import Camera, LandmarkSmoother

class MockLandmark:
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class MockHandLandmarks:
    def __init__(self, landmarks_list):
        self.landmark = landmarks_list

class TestLandmarkTracking(unittest.TestCase):
    """Test cases for landmark tracking and analysis"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock landmarks for a sequence of frames
        # Simulate a hand moving from left to right
        self.landmark_sequence = []
        
        # Generate 10 frames of hand movement
        for i in range(10):
            # Base position that moves right with each frame
            base_x = 0.3 + (i * 0.02)
            
            # Create landmarks for this frame
            wrist = MockLandmark(base_x, 0.8, 0.0)
            thumb_tip = MockLandmark(base_x - 0.1, 0.6, 0.1)
            index_tip = MockLandmark(base_x + 0.1, 0.5, 0.1)
            
            # Create a hand landmarks object
            landmarks = MockHandLandmarks([
                wrist,                            # 0: WRIST
                MockLandmark(base_x - 0.05, 0.75),  # 1: THUMB_CMC
                MockLandmark(base_x - 0.07, 0.70),  # 2: THUMB_MCP
                MockLandmark(base_x - 0.09, 0.65),  # 3: THUMB_IP
                thumb_tip,                        # 4: THUMB_TIP
                MockLandmark(base_x + 0.05, 0.70),  # 5: INDEX_FINGER_MCP
                MockLandmark(base_x + 0.07, 0.65),  # 6: INDEX_FINGER_PIP
                MockLandmark(base_x + 0.09, 0.55),  # 7: INDEX_FINGER_DIP
                index_tip,                        # 8: INDEX_FINGER_TIP
                # ... additional landmarks would be defined here
            ])
            
            self.landmark_sequence.append(landmarks)
        
        # Create patches
        self.mp_hands_patch = patch('mediapipe.solutions.hands')
        self.mp_drawing_patch = patch('mediapipe.solutions.drawing_utils')
        self.mp_drawing_styles_patch = patch('mediapipe.solutions.drawing_styles')
        
        # Start the patches
        self.mock_mp_hands = self.mp_hands_patch.start()
        self.mock_mp_drawing = self.mp_drawing_patch.start()
        self.mock_mp_drawing_styles = self.mp_drawing_styles_patch.start()
        
        # Setup the mock hands
        self.mock_hands = MagicMock()
        self.mock_mp_hands.Hands.return_value = self.mock_hands
    
    def tearDown(self):
        """Tear down test fixtures"""
        self.mp_hands_patch.stop()
        self.mp_drawing_patch.stop()
        self.mp_drawing_styles_patch.stop()
    
    def test_landmark_tracking_consistency(self):
        """Test if landmarks are tracked consistently across frames"""
        # Create a camera with smoother
        camera = Camera(camera_id=0)
        
        # Process each frame in sequence
        wrist_positions = []
        
        for landmarks in self.landmark_sequence:
            # Configure the mock to return these landmarks
            self.mock_hands.process.return_value.multi_hand_landmarks = [landmarks]
            
            # Process the frame
            frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Dummy frame
            processed = camera._process_frame(frame)
            
            # Extract wrist position for tracking
            if camera.hand_landmarks_data:
                wrist = camera.hand_landmarks_data[0].landmark[0]
                wrist_positions.append((wrist.x, wrist.y))
        
        # Check that positions change smoothly
        for i in range(1, len(wrist_positions)):
            dx = wrist_positions[i][0] - wrist_positions[i-1][0]
            dy = wrist_positions[i][1] - wrist_positions[i-1][1]
            
            # Change should be similar across frames
            expected_dx = 0.02  # From our test data
            self.assertAlmostEqual(dx, expected_dx, delta=0.01)
            
            # Y should remain relatively stable
            self.assertAlmostEqual(dy, 0.0, delta=0.01)
    
    def test_landmark_prediction_during_occlusion(self):
        """Test if landmarks can be predicted during brief occlusion"""
        # Skip if LandmarkSmoother is not implemented
        if not hasattr(Camera, 'landmark_smoother'):
            self.skipTest("LandmarkSmoother not implemented")
        
        # Create a smoother with low smoothing factor for more prediction
        smoother = LandmarkSmoother(smoothing_factor=0.3)
        
        # Process first few frames normally
        for i in range(3):
            smoothed = smoother.update(self.landmark_sequence[i])
        
        # Now simulate occlusion (None landmarks)
        predicted = smoother.update(None)
        
        # Check if prediction is available
        self.assertIsNotNone(predicted, "Should predict landmarks during brief occlusion")
        
        if predicted:
            # Position should be similar to last known position
            last_known_x = self.landmark_sequence[2].landmark[0].x
            predicted_x = predicted.landmark[0].x
            self.assertAlmostEqual(predicted_x, last_known_x, delta=0.05)
    
    def test_key_landmarks_extraction(self):
        """Test extraction of key landmarks from hand detection"""
        # Define extraction function if not in Camera class
        def extract_landmarks(landmarks, frame_shape):
            wrist = landmarks.landmark[0]
            thumb_tip = landmarks.landmark[4]
            index_tip = landmarks.landmark[8]
            
            height, width = frame_shape
            
            return {
                'wrist': (int(wrist.x * width), int(wrist.y * height)),
                'thumb_tip': (int(thumb_tip.x * width), int(thumb_tip.y * height)),
                'index_tip': (int(index_tip.x * width), int(index_tip.y * height))
            }
        
        # Test extraction with sample landmarks
        landmarks = self.landmark_sequence[0]
        frame_shape = (480, 640)
        
        extracted = extract_landmarks(landmarks, frame_shape)
        
        # Check that key points were extracted correctly
        self.assertIn('wrist', extracted)
        self.assertIn('thumb_tip', extracted)
        self.assertIn('index_tip', extracted)
        
        # Verify coordinates
        wrist_x, wrist_y = extracted['wrist']
        self.assertEqual(wrist_x, int(landmarks.landmark[0].x * 640))
        self.assertEqual(wrist_y, int(landmarks.landmark[0].y * 480))
    
    def test_distance_calculation(self):
        """Test distance calculation between landmarks"""
        # Define a distance function
        def calculate_distance(landmark1, landmark2):
            return math.sqrt(
                (landmark1.x - landmark2.x)**2 +
                (landmark1.y - landmark2.y)**2 +
                (landmark1.z - landmark2.z)**2
            )
        
        # Get landmarks from first frame
        landmarks = self.landmark_sequence[0].landmark
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        
        # Calculate distances
        dist_wrist_thumb = calculate_distance(wrist, thumb_tip)
        dist_wrist_index = calculate_distance(wrist, index_tip)
        dist_thumb_index = calculate_distance(thumb_tip, index_tip)
        
        # Verify distances are reasonable
        # These values depend on our test data coordinates
        expected_wrist_thumb = 0.25  # Approximate based on our coordinates
        self.assertAlmostEqual(dist_wrist_thumb, expected_wrist_thumb, delta=0.1)
    
    def test_landmark_velocity_calculation(self):
        """Test calculation of landmark velocity between frames"""
        # Process multiple frames to track motion
        positions = []
        timestamps = [i * 0.033 for i in range(len(self.landmark_sequence))]  # 30fps
        
        for i, landmarks in enumerate(self.landmark_sequence):
            # Extract wrist position
            wrist = landmarks.landmark[0]
            positions.append((wrist.x, wrist.y, timestamps[i]))
        
        # Calculate velocities
        velocities = []
        for i in range(1, len(positions)):
            dx = positions[i][0] - positions[i-1][0]
            dy = positions[i][1] - positions[i-1][1]
            dt = positions[i][2] - positions[i-1][2]
            
            velocity = math.sqrt(dx**2 + dy**2) / dt
            velocities.append(velocity)
        
        # Verify velocities are consistent (our test data moves at constant speed)
        avg_velocity = sum(velocities) / len(velocities)
        for v in velocities:
            self.assertAlmostEqual(v, avg_velocity, delta=0.1*avg_velocity)

if __name__ == '__main__':
    unittest.main()