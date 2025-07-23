# tests/test_file_manager.py
import pytest
import os

def test_file_controller_initialization(file_controller, temp_test_directory):
    """Test file controller initialization"""
    assert file_controller.current_directory == temp_test_directory
    assert file_controller.base_directory == temp_test_directory
    assert len(file_controller.directory_history) > 0
    
def test_file_listing(file_controller, temp_test_directory):
    """Test file listing functionality"""
    # Get directory contents
    dir_info = file_controller.get_directory_info()
    
    # Should contain our test files and directories
    assert "test.txt" in dir_info["files"]
    assert "readme.md" in dir_info["files"]
    assert "test.jpg" in dir_info["files"]
    assert "test_dir" in dir_info["files"]
    assert "empty_dir" in dir_info["files"]
    
def test_file_navigation(file_controller, temp_test_directory):
    """Test directory navigation"""
    # Navigate to test_dir
    initial_files = file_controller.files_list.copy()
    
    # Find index of test_dir
    test_dir_index = file_controller.files_list.index("test_dir")
    
    # Select the directory
    file_controller.selected_index = test_dir_index
    
    # Navigate down into the directory
    result = file_controller.navigate_directory("down")
    assert result is True
    
    # Check if we're in the test_dir
    assert file_controller.current_directory == os.path.join(temp_test_directory, "test_dir")
    
    # Directory should contain nested.txt and nested folder
    assert "nested.txt" in file_controller.files_list
    assert "nested" in file_controller.files_list
    
    # Navigate back up
    result = file_controller.navigate_directory("up")
    assert result is True
    
    # Should be back in the original directory
    assert file_controller.current_directory == temp_test_directory
    assert set(file_controller.files_list) == set(initial_files)
    
def test_file_selection_navigation(file_controller):
    """Test navigating through files with selection"""
    # Get initial index
    initial_index = file_controller.selected_index
    
    # Select next item
    file_controller.select_next()
    assert file_controller.selected_index == initial_index + 1
    
    # Select previous item
    file_controller.select_previous()
    assert file_controller.selected_index == initial_index
    
    # Select previous at beginning should stay at beginning
    if initial_index == 0:
        file_controller.select_previous()
        assert file_controller.selected_index == 0

def test_file_type_detection(file_controller, temp_test_directory):
    """Test file type detection"""
    # Test text file
    txt_path = os.path.join(temp_test_directory, "test.txt")
    txt_type = file_controller.get_file_type(txt_path)
    assert txt_type["type"] == "text"
    assert txt_type["extension"] == "txt"
    
    # Test image file
    img_path = os.path.join(temp_test_directory, "test.jpg")
    img_type = file_controller.get_file_type(img_path)
    assert img_type["type"] == "image"
    assert img_type["extension"] == "jpg"
    
    # Test directory
    dir_path = os.path.join(temp_test_directory, "test_dir")
    dir_type = file_controller.get_file_type(dir_path)
    assert dir_type["type"] == "directory"
    
def test_file_preview(file_controller, temp_test_directory):
    """Test file preview functionality"""
    # Test text file preview
    txt_path = os.path.join(temp_test_directory, "test.txt")
    preview = file_controller.get_file_preview(txt_path)
    
    assert preview["status"] == "success"
    assert preview["type"] == "text"
    assert "This is a test file." in preview["content"]
    assert not preview["truncated"]
    
    # Test non-existent file
    bad_path = os.path.join(temp_test_directory, "nonexistent.txt")
    preview = file_controller.get_file_preview(bad_path)
    assert preview["status"] == "error"