# file_system_gesture_interface.py

from file_system_manager import FileSystemManager
from gesture_recognizer import GestureRecognizer
from typing import Dict, List, Any, Callable

class FileSystemGestureInterface:
    """
    Connects gesture recognition with file system navigation.
    Maps recognized gestures to appropriate file system operations.
    """
    
    def __init__(self, file_manager: FileSystemManager, gesture_recognizer: GestureRecognizer):
        """
        Initialize the gesture-to-file-system interface.
        
        Args:
            file_manager: The FileSystemManager instance to control
            gesture_recognizer: The GestureRecognizer instance to use
        """
        self.file_manager = file_manager
        self.gesture_recognizer = gesture_recognizer
        
        # Start directory monitoring
        self.file_manager.start_monitoring()
        
        # Selected item index for navigation
        self.selected_index = 0
        self.current_items = []
        
        # Last processed gesture to avoid duplicates
        self.last_gesture = None
        self.gesture_cooldown = 0.5  # seconds
        self.last_gesture_time = 0
        
        # Initialize directory listing
        self._update_directory_listing()
        
    def _update_directory_listing(self):
        """Update the current directory listing."""
        self.current_items = self.file_manager.list_directory()
        # Reset selection if out of bounds
        if self.selected_index >= len(self.current_items):
            self.selected_index = max(0, len(self.current_items) - 1)
    
    def process_gesture(self, gesture: str) -> Dict[str, Any]:
        """
        Process a gesture and execute corresponding file system operation.
        
        Args:
            gesture: The recognized gesture string
            
        Returns:
            Dictionary with operation result and current state
        """
        import time
        
        # Check for cooldown to avoid duplicate commands
        current_time = time.time()
        if gesture == self.last_gesture and current_time - self.last_gesture_time < self.gesture_cooldown:
            # Still in cooldown period, don't process this gesture
            return self._get_current_state()
            
        # Update timestamp and last gesture
        self.last_gesture = gesture
        self.last_gesture_time = current_time
        
        # Process the gesture
        result = False
        message = ""
        
        if gesture == "point_up":  # Navigate up in the item list
            self.selected_index = max(0, self.selected_index - 1)
            message = f"Selected item: {self.current_items[self.selected_index]['name'] if self.current_items else 'None'}"
            result = True
            
        elif gesture == "point_down":  # Navigate down in the item list
            self.selected_index = min(len(self.current_items) - 1 if self.current_items else 0, 
                                    self.selected_index + 1)
            message = f"Selected item: {self.current_items[self.selected_index]['name'] if self.current_items else 'None'}"
            result = True
            
        elif gesture == "point_left":  # Go to parent directory
            result = self.file_manager.navigate_up()
            if result:
                message = f"Navigated to: {self.file_manager.get_current_path()}"
                self._update_directory_listing()
            else:
                message = "Already at root directory"
                
        elif gesture == "point_right":  # Enter selected directory
            if self.current_items and self.selected_index < len(self.current_items):
                selected_item = self.current_items[self.selected_index]
                if selected_item['is_dir']:
                    result = self.file_manager.navigate_to(selected_item['path'])
                    if result:
                        message = f"Navigated to: {self.file_manager.get_current_path()}"
                        self._update_directory_listing()
                    else:
                        message = f"Failed to navigate to: {selected_item['name']}"
                else:
                    message = f"Selected file: {selected_item['name']} (Cannot navigate into files)"
            else:
                message = "No item selected"
                
        elif gesture == "open_palm":  # Refresh directory listing
            self._update_directory_listing()
            message = "Directory listing refreshed"
            result = True
            
        # Return current state and operation result
        return {
            **self._get_current_state(),
            'operation_result': result,
            'message': message
        }
    
    def _get_current_state(self) -> Dict[str, Any]:
        """Get the current state of the file system and interface."""
        current_path = self.file_manager.get_current_path()
        return {
            'current_directory': str(current_path),
            'parent_directory': str(current_path.parent),
            'items': self.current_items,
            'selected_index': self.selected_index,
            'selected_item': self.current_items[self.selected_index] if self.current_items and self.selected_index < len(self.current_items) else None,
            'item_count': len(self.current_items)
        }
        
    def cleanup(self):
        """Clean up resources."""
        self.file_manager.stop_monitoring()
