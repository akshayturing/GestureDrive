import os
import time

class GestureFileController:
    """Controls file operations using gesture input"""
    
    def __init__(self, base_directory=None):
        self.base_directory = base_directory or os.path.expanduser("~")
        self.current_directory = self.base_directory
        self.directory_history = [self.base_directory]
        self.history_position = 0
        self.files_list = []
        self.selected_index = -1
        self.update_files_list()
        
    def update_files_list(self):
        """Update the list of files in the current directory"""
        try:
            entries = os.listdir(self.current_directory)
            # Sort directories first, then files
            dirs = [e for e in entries if os.path.isdir(os.path.join(self.current_directory, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(self.current_directory, e))]
            
            # Sort each group alphabetically
            dirs.sort()
            files.sort()
            
            # Combine the lists with directories first
            self.files_list = dirs + files
            
            # Reset selection
            if self.files_list:
                self.selected_index = 0
            else:
                self.selected_index = -1
                
            return True
        except (PermissionError, FileNotFoundError) as e:
            print(f"Error accessing directory: {e}")
            return False
    
    def navigate_directory(self, direction):
        """
        Navigate directory structure based on direction
        direction: "up" (parent), "down" (enter selected), "back", "forward"
        """
        if direction == "up":
            # Go to parent directory
            parent = os.path.dirname(self.current_directory)
            if os.path.exists(parent) and parent != self.current_directory:
                self.current_directory = parent
                self._add_to_history(self.current_directory)
                return self.update_files_list()
                
        elif direction == "down" and self.selected_index >= 0:
            # Enter selected directory
            selected = self.files_list[self.selected_index]
            path = os.path.join(self.current_directory, selected)
            
            if os.path.isdir(path) and os.path.exists(path):
                self.current_directory = path
                self._add_to_history(self.current_directory)
                return self.update_files_list()
                
        elif direction == "back" and self.history_position > 0:
            # Go back in history
            self.history_position -= 1
            self.current_directory = self.directory_history[self.history_position]
            return self.update_files_list()
            
        elif direction == "forward" and self.history_position < len(self.directory_history) - 1:
            # Go forward in history
            self.history_position += 1
            self.current_directory = self.directory_history[self.history_position]
            return self.update_files_list()
            
        return False
    
    def _add_to_history(self, directory):
        """Add directory to navigation history"""
        # If we went back and then navigated, trim the forward history
        if self.history_position < len(self.directory_history) - 1:
            self.directory_history = self.directory_history[:self.history_position + 1]
            
        # Don't add if it's the same as current
        if self.directory_history and self.directory_history[-1] == directory:
            return
            
        self.directory_history.append(directory)
        self.history_position = len(self.directory_history) - 1
    
    def select_next(self):
        """Select the next item in the file list"""
        if not self.files_list:
            return False
            
        self.selected_index = min(self.selected_index + 1, len(self.files_list) - 1)
        return True
    
    def select_previous(self):
        """Select the previous item in the file list"""
        if not self.files_list:
            return False
            
        self.selected_index = max(self.selected_index - 1, 0)
        return True
    
    def get_selected_file(self):
        """Get the currently selected file's name and path"""
        if not self.files_list or self.selected_index < 0:
            return None, None
            
        filename = self.files_list[self.selected_index]
        filepath = os.path.join(self.current_directory, filename)
        return filename, filepath
    
    def process_selection_gesture(self, gesture):
        """
        Process file selection gestures
        gesture: "tap" (select) or "pinch" (activate)
        Returns: action taken and relevant information
        """
        if not self.files_list or self.selected_index < 0:
            return {"action": "none", "reason": "no_selection"}
        
        filename, filepath = self.get_selected_file()
        
        if gesture == "tap":
            # Tap just confirms selection - already handled by index
            return {
                "action": "select", 
                "file": filename,
                "path": filepath,
                "type": "directory" if os.path.isdir(filepath) else "file"
            }
            
        elif gesture == "pinch":
            # Pinch activates the selected item
            if os.path.isdir(filepath):
                # If directory, enter it
                success = self.navigate_directory("down")
                return {
                    "action": "navigate" if success else "error",
                    "directory": filename,
                    "path": filepath
                }
            else:
                # If file, trigger file action (could be open, preview, etc.)
                return {
                    "action": "activate",
                    "file": filename,
                    "path": filepath,
                    "extension": os.path.splitext(filename)[1].lower()[1:]
                }
        
        return {"action": "none", "reason": "invalid_gesture"}
    
    def get_directory_info(self):
        """Get current directory information"""
        return {
            "current_directory": self.current_directory,
            "parent_directory": os.path.dirname(self.current_directory),
            "files": self.files_list,
            "selected_index": self.selected_index,
            "can_go_up": self.current_directory != self.base_directory,
            "can_go_back": self.history_position > 0,
            "can_go_forward": self.history_position < len(self.directory_history) - 1
        }