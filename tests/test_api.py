# tests/test_api.py
import pytest
import json
import os

def test_api_status(client):
    """Test the API status endpoint"""
    response = client.get('/api/status')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check required fields
    assert "status" in data
    assert "webcam_available" in data
    assert "gesture_system" in data
    
def test_api_directory(client):
    """Test directory information API"""
    response = client.get('/api/directory')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Check required fields
    assert "current_directory" in data
    assert "files" in data
    assert "selected_index" in data
    assert isinstance(data["files"], list)
    
def test_api_select(client, monkeypatch):
    """Test selection API endpoint"""
    # Since the real file system depends on state, we'll mock the controller's
    # select_next and select_previous methods
    
    # Create a mock response for select endpoints
    class MockResponse:
        @staticmethod
        def json():
            return {
                "success": True,
                "directory": {
                    "current_directory": "/test",
                    "files": ["file1.txt", "file2.txt", "file3.txt"],
                    "selected_index": 1
                }
            }
    
    # Patch the requests module's get method
    with monkeypatch.context() as m:
        # Use a mock for the select API calls
        m.setattr("urllib.request.urlopen", lambda url: MockResponse())
        
        # Test select next
        response = client.get('/api/select?action=next')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data
        
        # Test select previous
        response = client.get('/api/select?action=previous')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data
        
        # Test select with invalid action
        response = client.get('/api/select?action=invalid')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is False
        
def test_api_gestures(client, monkeypatch):
    """Test the gestures API endpoint"""
    # Mock camera's gesture attributes
    class MockCamera:
        def __init__(self):
            self.current_gesture = "point_up"
            self.current_motion = "swipe_left"
            self.current_selection_gesture = "pinch"
    
    # Patch the get_camera function
    with monkeypatch.context() as m:
        m.setattr("app.get_camera", lambda: MockCamera())
        
        response = client.get('/api/gestures')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["gesture"] == "point_up"
        assert data["motion"] == "swipe_left"
        assert data["selection_gesture"] == "pinch"

def test_api_hand_position(client, monkeypatch):
    """Test the hand position API endpoint"""
    # Mock camera with hand landmarks
    class MockLandmark:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z
    
    class MockHandLandmarks:
        def __init__(self):
            self.landmark = [MockLandmark(0.5, 0.5, 0) for _ in range(21)]
    
    class MockCamera:
        def __init__(self):
            self.hand_landmarks_data = [MockHandLandmarks()]
    
    # Patch the get_camera function
    with monkeypatch.context() as m:
        m.setattr("app.get_camera", lambda: MockCamera())
        
        response = client.get('/api/hand_position')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["visible"] is True
        assert data["x"] == 0.5
        assert data["y"] == 0.5
