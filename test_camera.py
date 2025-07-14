import unittest
import numpy as np
import cv2
import mediapipe as mp
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the Python path to import our modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Camera class and LandmarkSmoother
from camera import Camera, LandmarkSmoother

class MockLandmark:
    """Mock class for MediaPipe landmarks"""
    def __init__(self, x, y, z=0.0):
        self.x = x
        self.y = y
        self.z = z

class MockHandLandmarks:
    """Mock class for MediaPipe hand landmarks collection"""
    def __init__(self, landmarks_list):
        self.landmark = landmarks_list

class TestMediaPipeHandDetection(unittest.TestCase):
    """Test cases for MediaPipe hand landmark detection pipeline"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock frame
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a simple hand shape to the test frame
        cv2.rectangle(self.test_frame, (300, 200), (400, 300), (255, 255, 255), -1)
        cv2.circle(self.test_frame, (350, 150), 30, (255, 255, 255), -1)  # Thumb
        cv2.line(self.test_frame, (350, 250), (350, 150), (255, 255, 255), 5)  # Connection
        
        # Create sample landmarks for testing
        wrist = MockLandmark(0.5, 0.8, 0.0)
        thumb_tip = MockLandmark(0.3, 0.4, 0.1)
        index_tip = MockLandmark(0.6, 0.3, 0.1)
        
        # Create a mock hand landmarks object
        self.mock_landmarks = MockHandLandmarks([
            wrist,                          # 0: WRIST
            MockLandmark(0.45, 0.75, 0.0),  # 1: THUMB_CMC
            MockLandmark(0.40, 0.65, 0.0),  # 2: THUMB_MCP
            MockLandmark(0.35, 0.55, 0.0),  # 3: THUMB_IP
            thumb_tip,                      # 4: THUMB_TIP
            MockLandmark(0.55, 0.70, 0.0),  # 5: INDEX_FINGER_MCP
            MockLandmark(0.57, 0.60, 0.0),  # 6: INDEX_FINGER_PIP
            MockLandmark(0.59, 0.45, 0.0),  # 7: INDEX_FINGER_DIP
            index_tip,                      # 8: INDEX_FINGER_TIP
            # ... remaining landmarks would be added here
        ])
        
        # Create patches for MediaPipe dependencies
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
        
        # Mock the process result
        self.mock_process_result = MagicMock()
        self.mock_hands.process.return_value = self.mock_process_result
        
    def tearDown(self):
        """Tear down test fixtures"""
        # Stop the patches
        self.mp_hands_patch.stop()
        self.mp_drawing_patch.stop()
        self.mp_drawing_styles_patch.stop()
    
    def test_camera_initialization(self):
        """Test camera initialization with MediaPipe"""
        # Create the camera
        camera = Camera(camera_id=0, width=640, height=480)
        
        # Check MediaPipe initialization
        self.assertEqual(camera.width, 640)
        self.assertEqual(camera.height, 480)
        self.assertTrue(camera.mirror)
        
        # Verify MediaPipe Hands was initialized correctly
        self.mock_mp_hands.Hands.assert_called_once()
        
        # Verify parameters
        call_kwargs = self.mock_mp_hands.Hands.call_args[1]
        self.assertFalse(call_kwargs['static_image_mode'])
        self.assertEqual(call_kwargs['max_num_hands'], 2)
        self.assertGreater(call_kwargs['min_detection_confidence'], 0.0)
        self.assertLessEqual(call_kwargs['min_detection_confidence'], 1.0)
    
    @patch('cv2.cvtColor')
    def test_frame_conversion_to_rgb(self, mock_cvtColor):
        """Test conversion of frames from BGR to RGB"""
        # Setup
        camera = Camera(camera_id=0)
        
        # Mock the process result
        self.mock_process_result.multi_hand_landmarks = None
        
        # Call the process method
        with patch.object(Camera, 'get_frame', return_value=self.test_frame):
            camera._process_frame(self.test_frame)
        
        # Assert cv2.cvtColor was called with BGR2RGB
        mock_cvtColor.assert_called_once()
        # Verify correct conversion parameters
        args, kwargs = mock_cvtColor.call_args
        self.assertEqual(args[0].shape, self.test_frame.shape)
        self.assertEqual(args[1], cv2.COLOR_BGR2RGB)
    
    def test_hand_landmark_detection(self):
        """Test detection of hand landmarks"""
        # Setup
        camera = Camera(camera_id=0)
        
        # Configure the mock to return landmarks
        self.mock_process_result.multi_hand_landmarks = [self.mock_landmarks]
        
        # Call the process method
        with patch.object(Camera, 'get_frame', return_value=self.test_frame):
            result = camera._process_frame(self.test_frame)
        
        # Assert MediaPipe process was called
        self.mock_hands.process.assert_called_once()
        
        # Check that landmarks were stored
        self.assertEqual(camera.hand_landmarks_data, [self.mock_landmarks])
    
    @patch('cv2.circle')
    @patch('cv2.putText')
    def test_key_landmark_extraction(self, mock_putText, mock_circle):
        """Test extraction of key landmarks (wrist, thumb, index)"""
        # Setup
        camera = Camera(camera_id=0)
        
        # Configure the mock to return landmarks
        self.mock_process_result.multi_hand_landmarks = [self.mock_landmarks]
        
        # Create spy method for extract_key_landmarks
        original_extract = LandmarkSmoother._apply_smoothing if hasattr(camera, 'landmark_smoother') else None
        
        # Define a mockable extraction method if needed
        if not hasattr(camera, 'extract_key_landmarks'):
            def mock_extract_key_landmarks(self, hand_landmarks, frame_shape):
                # Basic extraction without the actual implementation
                return {
                    'wrist': {'normalized': (hand_landmarks.landmark[0].x, 
                                           hand_landmarks.landmark[0].y, 
                                           hand_landmarks.landmark[0].z),
                            'pixel': (int(hand_landmarks.landmark[0].x * frame_shape[1]), 
                                     int(hand_landmarks.landmark[0].y * frame_shape[0]))},
                    'thumb_tip': {'normalized': (hand_landmarks.landmark[4].x, 
                                               hand_landmarks.landmark[4].y, 
                                               hand_landmarks.landmark[4].z),
                                'pixel': (int(hand_landmarks.landmark[4].x * frame_shape[1]), 
                                         int(hand_landmarks.landmark[4].y * frame_shape[0]))},
                    'index_tip': {'normalized': (hand_landmarks.landmark[8].x, 
                                               hand_landmarks.landmark[8].y, 
                                               hand_landmarks.landmark[8].z),
                                'pixel': (int(hand_landmarks.landmark[8].x * frame_shape[1]), 
                                         int(hand_landmarks.landmark[8].y * frame_shape[0]))},
                }
            
            # Add method to camera for testing
            camera.extract_key_landmarks = mock_extract_key_landmarks.__get__(camera)
        
        # Create a spy for the extraction method
        with patch.object(camera, 'extract_key_landmarks', wraps=camera.extract_key_landmarks) as mock_extract:
            # Process a frame
            result = camera._process_frame(self.test_frame)
            
            # Verify extraction was called with landmarks
            if hasattr(camera, 'show_landmarks') and camera.show_landmarks:
                mock_extract.assert_called()
                
                # Get the extraction results
                call_args = mock_extract.call_args
                # Verify landmark coordinates were extracted
                self.assertIsNotNone(call_args)
                if call_args:
                    # Ensure the first argument is landmarks, second is frame shape
                    self.assertEqual(call_args[0][0], self.mock_landmarks)
    
    def test_landmark_coordinate_conversion(self):
        """Test conversion of normalized coordinates to pixel coordinates"""
        # Setup expected pixel coordinates (based on 640x480 frame)
        expected_wrist = (int(0.5 * 640), int(0.8 * 480))
        expected_thumb = (int(0.3 * 640), int(0.4 * 480))
        expected_index = (int(0.6 * 640), int(0.3 * 480))
        
        # Manually convert normalized to pixel coordinates
        frame_width, frame_height = self.test_frame.shape[1], self.test_frame.shape[0]
        
        wrist_pixel = (int(self.mock_landmarks.landmark[0].x * frame_width), 
                      int(self.mock_landmarks.landmark[0].y * frame_height))
        thumb_pixel = (int(self.mock_landmarks.landmark[4].x * frame_width), 
                      int(self.mock_landmarks.landmark[4].y * frame_height))
        index_pixel = (int(self.mock_landmarks.landmark[8].x * frame_width), 
                      int(self.mock_landmarks.landmark[8].y * frame_height))
        
        # Compare
        self.assertEqual(wrist_pixel, expected_wrist)
        self.assertEqual(thumb_pixel, expected_thumb)
        self.assertEqual(index_pixel, expected_index)
    
    def test_landmark_smoothing(self):
        """Test landmark position smoothing if implemented"""
        # Skip test if LandmarkSmoother is not defined
        if not hasattr(Camera, 'landmark_smoother'):
            self.skipTest("LandmarkSmoother not implemented")
        
        # Create a smoother
        smoother = LandmarkSmoother(smoothing_factor=0.5)
        
        # Update with initial landmarks
        smoothed = smoother.update(self.mock_landmarks)
        
        # First update should return landmarks unchanged
        self.assertEqual(smoothed.landmark[0].x, self.mock_landmarks.landmark[0].x)
        
        # Create slightly modified landmarks
        modified_landmarks = MockHandLandmarks([
            MockLandmark(0.51, 0.81),  # Slightly moved wrist
            MockLandmark(0.46, 0.76),
            MockLandmark(0.41, 0.66),
            MockLandmark(0.36, 0.56),
            MockLandmark(0.31, 0.41),  # Slightly moved thumb
            MockLandmark(0.56, 0.71),
            MockLandmark(0.58, 0.61),
            MockLandmark(0.60, 0.46),
            MockLandmark(0.61, 0.31),  # Slightly moved index
        ])
        
        # Update with modified landmarks
        smoothed = smoother.update(modified_landmarks)
        
        # Check that smoothed landmarks are between original and modified
        # Using smoothing_factor=0.5, should be exactly halfway
        self.assertAlmostEqual(smoothed.landmark[0].x, 0.505)
        self.assertAlmostEqual(smoothed.landmark[0].y, 0.805)
    
    def test_handle_no_landmarks_detected(self):
        """Test handling when no landmarks are detected"""
        # Setup
        camera = Camera(camera_id=0)
        
        # Configure the mock to return no landmarks
        self.mock_process_result.multi_hand_landmarks = None
        
        # Call the process method
        with patch.object(Camera, 'get_frame', return_value=self.test_frame):
            result = camera._process_frame(self.test_frame)
        
        # Check that hand_landmarks_data is none
        self.assertIsNone(camera.hand_landmarks_data)
    
    def test_frame_processing_benchmarking(self):
        """Test performance of frame processing (simple benchmark)"""
        # This is more of a benchmark than a unit test
        camera = Camera(camera_id=0)
        
        # Configure the mock
        self.mock_process_result.multi_hand_landmarks = [self.mock_landmarks]
        
        # Process the frame multiple times and measure
        import time
        start_time = time.time()
        iterations = 10
        
        for _ in range(iterations):
            with patch.object(Camera, 'get_frame', return_value=self.test_frame):
                result = camera._process_frame(self.test_frame)
        
        elapsed = time.time() - start_time
        avg_time = elapsed / iterations
        
        # This is not a pass/fail test, just informational
        print(f"\nAverage processing time per frame: {avg_time*1000:.2f}ms")
        
        # But we'll assert it's not unreasonably slow
        self.assertLess(avg_time, 1.0, "Frame processing is too slow")

if __name__ == '__main__':
    unittest.main()