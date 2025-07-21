# tests/test_gesture_file_controller.py
import pytest
import os

def test_process_tap_gesture(file_controller, temp_test_directory):
    """Test processing tap gesture for file selection"""
    # First make sure we have a file selected
    file_controller.selected_index = 0  # Select first file
    
    # Process tap gesture
    result = file_controller.process_selection_gesture("tap")
    
    assert result["action"] == "select"
    assert "file" in result
    assert "path" in result
    assert "type" in result
    
def test_process_pinch_gesture_on_directory(file_controller, temp_test_directory):
    """Test processing pinch gesture to open a directory"""
    # Find test_dir index
    test_dir_index = file_controller.files_list.index("test_dir")
    file_controller.selected_index = test_dir_index
    
    # Process pinch gesture
    result = file_controller.process_selection_gesture("pinch")
    
    assert result["action"] == "navigate"
    assert "directory" in result
    assert result["directory"] == "test_dir"
    
    # Should now be in the test_dir
    assert os.path.basename(file_controller.current_directory) == "test_dir"
    
def test_process_pinch_gesture_on_file(file_controller, temp_test_directory):
    """Test processing pinch gesture to activate a file"""
    # Find text file index
    txt_file_index = file_controller.files_list.index("test.txt")
    file_controller.selected_index = txt_file_index
    
    # Process pinch gesture
    result = file_controller.process_selection_gesture("pinch")
    
    assert result["action"] == "activate"
    assert result["file"] == "test.txt"
    assert "path" in result
    assert result["type"] == "text"
    assert "extension" in result
    assert result["extension"] == "txt"
    
    # Preview data should be included
    assert "preview" in result