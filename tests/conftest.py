import os
import pytest
import tempfile
import shutil
import cv2
import numpy as np
from flask import Flask
from datetime import datetime

from camera import Camera
from gesture_recognizer import GestureRecognizer
from gesture_detector import SelectionGestureDetector
from gesture_file_controller import GestureFileController
from app import app as flask_app

@pytest.fixture
def app():
    """Create a Flask application for testing"""
    app = flask_app
    app.config.update({
        "TESTING": True,
    })
    
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application"""
    return app.test_client()

@pytest.fixture
def temp_test_directory():
    """Create a temporary directory with test files for file system tests"""
    temp_dir = tempfile.mkdtemp()
    
    # Create some test files and directories
    os.mkdir(os.path.join(temp_dir, "test_dir"))
    os.mkdir(os.path.join(temp_dir, "empty_dir"))
    
    # Create text file
    with open(os.path.join(temp_dir, "test.txt"), "w") as f:
        f.write("This is a test file.\nIt has multiple lines.\n")
        
    # Create markdown file
    with open(os.path.join(temp_dir, "readme.md"), "w") as f:
        f.write("# Test Markdown\n\nThis is a test markdown file.")
    
    # Create dummy image file
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.imwrite(os.path.join(temp_dir, "test.jpg"), img)
    
    # Create nested files
    os.mkdir(os.path.join(temp_dir, "test_dir", "nested"))
    with open(os.path.join(temp_dir, "test_dir", "nested.txt"), "w") as f:
        f.write("Nested file content")
    
    yield temp_dir
    
    # Clean up after test
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_camera():
    """Create a mock camera for testing gesture recognition"""
    class MockCamera(Camera):
        def __init__(self):
            # Skip parent init to avoid actual camera operations
            self.is_running = True
            self.camera_id = -1
            self.width = 640
            self.height = 480
            self.fps = 30
            self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
            self.processed_frame = self.frame.copy()
            self.hand_landmarks_data = None
            self.current_gesture = None
            self.current_motion = None
            self.current_selection_gesture = None
            self.lock = None  # No threading lock needed for tests
        
        def start(self):
            self.is_running = True
            return True
            
        def stop(self):
            self.is_running = False
            return True
            
        def get_frame(self, processed=True):
            return self.processed_frame if processed else self.frame
            
        def get_jpeg_frame(self, processed=True):
            frame = self.processed_frame if processed else self.frame
            _, jpeg = cv2.imencode('.jpg', frame)
            return jpeg.tobytes()
            
        def set_mock_gesture(self, gesture=None, motion=None, selection_gesture=None):
            """Set mock gesture data for testing"""
            self.current_gesture = gesture
            self.current_motion = motion
            self.current_selection_gesture = selection_gesture
            
        def set_mock_hand_landmarks(self, landmarks=None):
            """Set mock hand landmarks for testing"""
            self.hand_landmarks_data = landmarks
    
    return MockCamera()

@pytest.fixture
def file_controller(temp_test_directory):
    """Create a file controller instance for testing"""
    controller = GestureFileController(base_directory=temp_test_directory)
    return controller

@pytest.fixture
def gesture_recognizer():
    """Create a gesture recognizer instance for testing"""
    return GestureRecognizer(buffer_size=3)

@pytest.fixture
def selection_detector():
    """Create a selection gesture detector instance for testing"""
    return SelectionGestureDetector(cooldown_period=0.1)

@pytest.fixture
def mock_hand_landmarks():
    """Create mock hand landmarks for testing gesture recognition"""
    # Simple mock of MediaPipe's hand landmarks output
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z
    
    class MockHandLandmarks:
        def __init__(self):
            self.landmark = [MockLandmark(0.5, 0.5, 0) for _ in range(21)]
    
    landmarks = MockHandLandmarks()
    
    # Position for a pointing up gesture
    landmarks.landmark[8].y = 0.3  # Index finger tip up
    landmarks.landmark[7].y = 0.4  # Index finger middle joint
    landmarks.landmark[6].y = 0.5  # Index finger base joint
    
    return [landmarks]