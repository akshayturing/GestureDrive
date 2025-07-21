# tests/test_selection_detector.py
import pytest
import time

def test_selection_detector_initialization(selection_detector):
    """Test selection detector initialization"""
    assert selection_detector.cooldown_period == 0.1
    assert len(selection_detector.position_history) == 0
    
def test_pinch_detection(selection_detector, mock_hand_landmarks):
    """Test pinch gesture detection"""
    # Modify mock landmarks for pinch detection
    mock_landmarks = mock_hand_landmarks
    
    # Set thumb and index finger close together for pinch
    mock_landmarks[0].landmark[4].x = 0.45  # Thumb tip 
    mock_landmarks[0].landmark[4].y = 0.45
    mock_landmarks[0].landmark[8].x = 0.46  # Index tip
    mock_landmarks[0].landmark[8].y = 0.46
    
    # Should detect a pinch
    result = selection_detector.update(mock_landmarks)
    assert result == "pinch"
    
def test_cooldown_period(selection_detector, mock_hand_landmarks):
    """Test that the cooldown period prevents rapid gesture detection"""
    # Configure for pinch
    mock_landmarks = mock_hand_landmarks
    mock_landmarks[0].landmark[4].x = 0.45
    mock_landmarks[0].landmark[4].y = 0.45
    mock_landmarks[0].landmark[8].x = 0.46
    mock_landmarks[0].landmark[8].y = 0.46
    
    # First detection should work
    result1 = selection_detector.update(mock_landmarks)
    assert result1 == "pinch"
    
    # Immediate second detection should respect cooldown
    result2 = selection_detector.update(mock_landmarks)
    assert result2 is None
    
    # After cooldown, should detect again
    time.sleep(0.15)  # Wait longer than cooldown period
    result3 = selection_detector.update(mock_landmarks)
    assert result3 == "pinch"