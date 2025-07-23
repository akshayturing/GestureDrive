# tests/test_explorer_integration.py
import pytest
import json

def test_explorer_page_loads(client):
    """Test that the explorer page loads successfully"""
    response = client.get('/explorer')
    assert response.status_code == 200
    
    # Check for key HTML elements in the response
    html = response.data.decode('utf-8')
    assert '<div class="explorer-container">' in html
    assert '<div class="camera-feed">' in html
    assert '<div class="file-panel">' in html
    assert '<div class="gesture-instructions">' in html
    
def test_start_gesture_processor(client):
    """Test the start_gesture_processor endpoint"""
    response = client.get('/start_gesture_processor')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "status" in data
    assert data["status"] in ["started", "already_running"]

def test_file_preview_api_text(client, temp_test_directory, monkeypatch):
    """Test the file preview API for text files"""
    # Mock the file controller to return our test directory
    class MockController:
        def get_file_preview(self, path):
            return {
                "status": "success",
                "type": "text",
                "content": "This is a test file.\nIt has multiple lines.",
                "truncated": False
            }
    
    # Patch the file_controller in app.py
    with monkeypatch.context() as m:
        m.setattr("app.file_controller", MockController())
        
        response = client.get(f'/api/file/preview?path={temp_test_directory}/test.txt')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "success"
        assert data["type"] == "text"
        assert "content" in data
        assert "truncated" in data
        
def test_file_preview_api_image(client, temp_test_directory, monkeypatch):
    """Test the file preview API for image files"""
    # Mock the file controller to return our test directory
    class MockController:
        def get_file_preview(self, path):
            return {
                "status": "success",
                "type": "image",
                "image_type": "jpeg",
                "file_path": f"{temp_test_directory}/test.jpg",
                "size": 2048
            }
    
    # Patch the file_controller in app.py
    with monkeypatch.context() as m:
        m.setattr("app.file_controller", MockController())
        
        response = client.get(f'/api/file/preview?path={temp_test_directory}/test.jpg')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["status"] == "success"
        assert data["type"] == "image"
        assert "file_path" in data
        assert "size" in data