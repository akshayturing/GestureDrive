# test_directory_state_manager.py

import unittest
import os
import shutil
import tempfile
import time
import json
from pathlib import Path
from core.directory_state_manager import DirectoryStateManager

class TestDirectoryStateManager(unittest.TestCase):
    """Test cases for the directory state manager component."""
    
    def setUp(self):
        """Set up the test environment with a temporary directory structure."""
        # Create a temporary directory structure for testing
        self.temp_root = tempfile.mkdtemp(prefix="gesture_drive_test_")
        
        # Create a test directory structure
        self.test_dirs = {
            'main': self.temp_root,
            'dir1': os.path.join(self.temp_root, "dir1"),
            'dir2': os.path.join(self.temp_root, "dir2"),
            'subdir1': os.path.join(self.temp_root, "dir1", "subdir1"),
            'empty_dir': os.path.join(self.temp_root, "empty_dir")
        }
        
        # Create the directories
        for dir_path in self.test_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
            
        # Create some test files
        self.test_files = {
            'file1': os.path.join(self.test_dirs['main'], "file1.txt"),
            'file2': os.path.join(self.test_dirs['dir1'], "file2.txt"),
            'hidden': os.path.join(self.test_dirs['main'], ".hidden_file"),
        }
        
        # Write some content to the files
        for file_path in self.test_files.values():
            with open(file_path, 'w') as f:
                f.write(f"Test content for {os.path.basename(file_path)}")
                
        # Create a test state file
        self.test_state_file = os.path.join(self.temp_root, "test_state.json")
        
        # Initialize the state manager with the test file
        self.state_manager = DirectoryStateManager(
            state_file=self.test_state_file,
            auto_save=False  # Disable auto-save for testing
        )
        
    def tearDown(self):
        """Clean up the test environment."""
        self.state_manager.shutdown()
        
        # Remove the temporary directory structure
        try:
            shutil.rmtree(self.temp_root)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not remove temporary directory: {e}")
    
    def test_initial_state(self):
        """Test the initial state of the manager."""
        # Verify that the state file was created
        self.assertTrue(os.path.exists(self.test_state_file))
        
        # Verify that the current directory is valid
        current_dir = self.state_manager.get_current_directory()
        self.assertTrue(current_dir.exists())
        self.assertTrue(current_dir.is_dir())
    
    def test_change_directory(self):
        """Test changing directories."""
        # Change to dir1
        result = self.state_manager.change_directory(self.test_dirs['dir1'])
        self.assertTrue(result)
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir1'])
        
        # Change to dir2
        result = self.state_manager.change_directory(self.test_dirs['dir2'])
        self.assertTrue(result)
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir2'])
        
        # Try to change to a non-existent directory
        result = self.state_manager.change_directory(os.path.join(self.temp_root, "nonexistent"))
        self.assertFalse(result)
        # Current directory should remain unchanged
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir2'])
    
    def test_navigate_history(self):
        """Test navigation history."""
        # Navigate to a sequence of directories
        self.state_manager.change_directory(self.test_dirs['dir1'])
        self.state_manager.change_directory(self.test_dirs['subdir1'])
        self.state_manager.change_directory(self.test_dirs['dir2'])
        
        # Current directory should be dir2
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir2'])
        
        # Navigate backward twice
        self.assertTrue(self.state_manager.navigate_history(forward=False))
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['subdir1'])
        
        self.assertTrue(self.state_manager.navigate_history(forward=False))
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir1'])
        
        # Navigate forward
        self.assertTrue(self.state_manager.navigate_history(forward=True))
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['subdir1'])
        
        # Try to navigate backward past the beginning of history
        initial_count = len(self.state_manager.get_history())
        for _ in range(initial_count + 1):
            res = self.state_manager.navigate_history(forward=False)
            if not res:
                break
                
        # Trying to go back further should fail
        self.assertFalse(self.state_manager.navigate_history(forward=False))
    
    def test_navigate_up(self):
        """Test navigating up to parent directory."""
        # Navigate to a subdirectory
        self.state_manager.change_directory(self.test_dirs['dir1'])
        self.state_manager.change_directory(self.test_dirs['subdir1'])
        
        # Navigate up
        self.assertTrue(self.state_manager.navigate_up())
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir1'])
        
        # Navigate up again
        self.assertTrue(self.state_manager.navigate_up())
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['main'])
        
        # At the temp root, if that is the root of the file system, navigate_up might fail
        # This depends on the OS and permissions, so we'll just check the result is boolean
        result = self.state_manager.navigate_up()
        self.assertIsInstance(result, bool)
    
    def test_selection_index(self):
        """Test saving and retrieving selection indices."""
        # Set selection index for a directory
        self.state_manager.set_selection_index(2, self.test_dirs['dir1'])
        
        # Get selection index for same directory
        index = self.state_manager.get_selection_index(self.test_dirs['dir1'])
        self.assertEqual(index, 2)
        
        # Change directory and set a different index
        self.state_manager.change_directory(self.test_dirs['dir2'])
        self.state_manager.set_selection_index(3)
        
        # Verify the index is correctly saved
        index = self.state_manager.get_selection_index()
        self.assertEqual(index, 3)
        
        # Navigation should preserve distinct indices per directory
        self.state_manager.change_directory(self.test_dirs['dir1'])
        index = self.state_manager.get_selection_index()
        self.assertEqual(index, 2)
        
        # Default index for a new directory should be 0
        index = self.state_manager.get_selection_index(self.test_dirs['empty_dir'])
        self.assertEqual(index, 0)
    
    def test_state_persistence(self):
        """Test that state persists after shutdown and restart."""
        # Set up a known state
        self.state_manager.change_directory(self.test_dirs['dir1'])
        self.state_manager.set_selection_index(2)
        self.state_manager.add_favorite("test_favorite", self.test_dirs['dir2'])
        
        # Save state and shutdown
        self.state_manager.save_now()
        self.state_manager.shutdown()
        
        # Create new instance with the same state file
        new_manager = DirectoryStateManager(
            state_file=self.test_state_file,
            auto_save=False
        )
        
        # Verify state was loaded correctly
        self.assertEqual(str(new_manager.get_current_directory()), self.test_dirs['dir1'])
        self.assertEqual(new_manager.get_selection_index(), 2)
        favorites = new_manager.get_favorites()
        self.assertIn("test_favorite", favorites)
        self.assertEqual(favorites["test_favorite"], self.test_dirs['dir2'])
        
        # Clean up
        new_manager.shutdown()
    
    def test_invalid_directory_recovery(self):
        """Test recovery from invalid directories."""
        # Set up a directory that will be deleted
        temp_dir = os.path.join(self.temp_root, "temp_to_delete")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Navigate to the directory
        self.state_manager.change_directory(temp_dir)
        self.assertEqual(str(self.state_manager.get_current_directory()), temp_dir)
        
        # Save state and shutdown
        self.state_manager.save_now()
        self.state_manager.shutdown()
        
        # Delete the directory
        shutil.rmtree(temp_dir)
        
        # Create new instance with the same state file
        new_manager = DirectoryStateManager(
            state_file=self.test_state_file,
            auto_save=False
        )
        
        # Verify recovery - should be in a valid directory
        current_dir = new_manager.get_current_directory()
        self.assertTrue(current_dir.exists())
        self.assertTrue(current_dir.is_dir())
        
        # Clean up
        new_manager.shutdown()
    
    def test_favorites(self):
        """Test favorite directory management."""
        # Add favorites
        self.state_manager.add_favorite("main", self.test_dirs['main'])
        self.state_manager.add_favorite("dir1", self.test_dirs['dir1'])
        
        # Get favorites
        favorites = self.state_manager.get_favorites()
        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites["main"], self.test_dirs['main'])
        self.assertEqual(favorites["dir1"], self.test_dirs['dir1'])
        
        # Navigate to a favorite
        self.state_manager.change_directory(self.test_dirs['dir2'])
        self.assertTrue(self.state_manager.navigate_to_favorite("dir1"))
        self.assertEqual(str(self.state_manager.get_current_directory()), self.test_dirs['dir1'])
        
        # Remove a favorite
        self.assertTrue(self.state_manager.remove_favorite("main"))
        favorites = self.state_manager.get_favorites()
        self.assertEqual(len(favorites), 1)
        self.assertNotIn("main", favorites)
        
        # Try to navigate to a removed favorite
        self.assertFalse(self.state_manager.navigate_to_favorite("main"))
        
        # Try to remove a non-existent favorite
        self.assertFalse(self.state_manager.remove_favorite("nonexistent"))

# Run the tests
if __name__ == '__main__':
    unittest.main()