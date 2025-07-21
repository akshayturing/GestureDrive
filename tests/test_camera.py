import pytest
import numpy as np
import cv2
import time

def test_camera_initialization(mock_camera):
    """Test camera initialization and properties"""
    assert mock_camera.is_running
    assert mock_camera.width == 640
    assert mock_camera.height == 480
    
    # Test frame shapes
    frame = mock_camera.get_frame()
    assert frame.shape == (480, 640, 3)
    
    # Test JPEG frame generation
    jpeg_frame = mock_camera.get_jpeg_frame()
    assert jpeg_frame is not None
    assert isinstance(jpeg_frame, bytes)
    
def test_camera_gesture_setting(mock_camera):
    """Test setting gestures in the camera"""
    # Initial values should be None
    assert mock_camera.current_gesture is None
    assert mock_camera.current_motion is None
    assert mock_camera.current_selection_gesture is None
    
    # Set mock gestures
    mock_camera.set_mock_gesture("point_up", "swipe_left", "pinch")
    
    # Check values were set
    assert mock_camera.current_gesture == "point_up"
    assert mock_camera.current_motion == "swipe_left"
    assert mock_camera.current_selection_gesture == "pinch"
    
def test_camera_stop(mock_camera):
    """Test camera stop function"""
    assert mock_camera.is_running
    mock_camera.stop()
    assert not mock_camera.is_running
