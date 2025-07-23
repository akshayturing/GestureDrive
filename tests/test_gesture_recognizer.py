# tests/test_gesture_recognizer.py
import pytest

def test_gesture_recognizer_initialization(gesture_recognizer):
    """Test gesture recognizer initialization"""
    assert gesture_recognizer.buffer_size == 3
    assert gesture_recognizer.current_gesture is None
    assert len(gesture_recognizer.gesture_buffer) == 0
    
def test_gesture_recognition(gesture_recognizer, mock_hand_landmarks):
    """Test basic gesture recognition"""
    # The mock landmarks are configured for "point_up"
    gesture = gesture_recognizer.recognize_gesture(mock_hand_landmarks[0])
    assert gesture == "point_up"
    
def test_gesture_buffer_smoothing(gesture_recognizer, mock_hand_landmarks):
    """Test gesture buffer smoothing over multiple frames"""
    # Mock hand landmarks for test
    hand = mock_hand_landmarks[0]
    
    # First update - add to buffer
    gesture_recognizer.update_gesture(hand)
    assert len(gesture_recognizer.gesture_buffer) == 1
    
    # Second update - add to buffer
    gesture_recognizer.update_gesture(hand)
    assert len(gesture_recognizer.gesture_buffer) == 2
    
    # Third update - buffer should be full, gesture should be recognized
    result = gesture_recognizer.update_gesture(hand)
    assert len(gesture_recognizer.gesture_buffer) == 3
    assert result == "point_up"
